from __future__ import annotations

import logging
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shopify.models import ShopifyShop
from shopify.services import (
    WEBHOOK_TOPICS,
    build_authorize_url,
    complete_oauth,
    fetch_locations,
    fetch_orders,
    normalize_shop_domain,
    register_webhooks,
    sync_products_from_shopify,
    verify_shopify_webhook,
    webhook_callback_url,
)

logger = logging.getLogger(__name__)


class ShopifyStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            shop = (
                ShopifyShop.objects.filter(user_id=request.user.id, is_active=True)
                .order_by("-updated_at")
                .first()
            )
        except Exception:  # noqa: BLE001
            logger.exception("shopify status query failed")
            return Response(
                {"connected": False, "shop": None, "warning": "status_unavailable"},
                status=status.HTTP_200_OK,
            )
        if not shop:
            return Response({"connected": False, "shop": None})
        return Response(
            {
                "connected": True,
                "shop": {
                    "domain": shop.shop_domain,
                    "scope": shop.scope,
                    "installedAt": shop.installed_at.isoformat(),
                },
                "webhooks": {
                    "address": webhook_callback_url(),
                    "configured": bool(webhook_callback_url()),
                },
            }
        )


class ShopifyConnectView(APIView):
    """Return the Shopify OAuth authorize URL for the given shop domain."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        shop = request.data.get("shop") or ""
        try:
            shop_domain = normalize_shop_domain(shop)
            authorize_url = build_authorize_url(
                user_id=request.user.id, shop=shop_domain
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.SHOPIFY_API_KEY or not settings.SHOPIFY_API_SECRET:
            return Response(
                {"detail": "Shopify app credentials are not configured on the server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"authorizeUrl": authorize_url, "shop": shop_domain})


class ShopifyCallbackView(APIView):
    """Browser redirect target from Shopify — no Bearer token available."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        frontend = settings.FRONTEND_URL.rstrip("/")
        error = request.query_params.get("error")
        if error:
            return HttpResponseRedirect(
                f"{frontend}/app/connect-shopify?error={quote(error)}"
            )

        shop = request.query_params.get("shop", "")
        code = request.query_params.get("code", "")
        state = request.query_params.get("state", "")
        if not shop or not code or not state:
            return HttpResponseRedirect(
                f"{frontend}/app/connect-shopify?error=missing_params"
            )

        try:
            complete_oauth(state=state, shop=shop, code=code)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Shopify OAuth callback failed")
            detail = quote(str(exc)[:180])
            return HttpResponseRedirect(
                f"{frontend}/app/connect-shopify?error=oauth_failed&detail={detail}"
            )

        return HttpResponseRedirect(f"{frontend}/app?shopify=connected")


class ShopifyRegisterWebhooksView(APIView):
    """Register product/inventory webhooks for the current shop (needs SHOPIFY_APP_URL)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        address = webhook_callback_url()
        if not address:
            return Response(
                {
                    "detail": (
                        "SHOPIFY_APP_URL is not set to a public HTTPS origin on the server."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        shop = ShopifyShop.objects.filter(
            user_id=request.user.id, is_active=True
        ).first()
        if not shop:
            return Response(
                {"detail": "No Shopify store connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            register_webhooks(shop)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Webhook registration failed")
            return Response(
                {"detail": f"Could not register webhooks: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"ok": True, "address": address, "topics": list(WEBHOOK_TOPICS)})


class ShopifySyncView(APIView):
    """Internal/manual fallback. Prefer webhooks + auto-refresh on product reads."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        shop = ShopifyShop.objects.filter(
            user_id=request.user.id, is_active=True
        ).first()
        if not shop:
            return Response(
                {"detail": "No Shopify store connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            count = sync_products_from_shopify(shop, record_activity=False)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Shopify product sync failed")
            return Response(
                {"detail": f"Sync failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"ok": True, "productsSynced": count})


class ShopifyWebhookView(APIView):
    """Shopify → app push updates for products/inventory."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        hmac_header = request.META.get("HTTP_X_SHOPIFY_HMAC_SHA256", "")
        raw = request.body
        if not verify_shopify_webhook(body=raw, hmac_header=hmac_header):
            return Response({"detail": "Invalid HMAC"}, status=status.HTTP_401_UNAUTHORIZED)

        shop_domain = request.META.get("HTTP_X_SHOPIFY_SHOP_DOMAIN", "")
        topic = request.META.get("HTTP_X_SHOPIFY_TOPIC", "")
        try:
            shop_domain = normalize_shop_domain(shop_domain)
        except ValueError:
            return Response({"detail": "Invalid shop"}, status=status.HTTP_400_BAD_REQUEST)

        shop = ShopifyShop.objects.filter(
            shop_domain=shop_domain, is_active=True
        ).first()
        if not shop:
            return Response({"ok": True, "ignored": True})

        try:
            if topic == "products/delete":
                payload = request.data if isinstance(request.data, dict) else {}
                product_id = str(payload.get("id") or "")
                if product_id:
                    from inventory.models import Product

                    Product.objects.filter(
                        user_id=shop.user_id,
                        shopify_product_id__startswith=f"{product_id}:",
                    ).delete()
                    shop.updated_at = timezone.now()
                    shop.save(update_fields=["updated_at"])
            else:
                sync_products_from_shopify(shop, record_activity=False)
        except Exception:  # noqa: BLE001
            logger.exception("Shopify webhook handling failed topic=%s shop=%s", topic, shop_domain)
            return Response({"detail": "Webhook processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"ok": True})


class ShopifyLocationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = ShopifyShop.objects.filter(
            user_id=request.user.id, is_active=True
        ).first()
        if not shop:
            return Response(
                {"detail": "No Shopify store connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            locations = fetch_locations(shop)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Shopify locations fetch failed")
            return Response(
                {"detail": f"Could not load locations: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            [
                {
                    "id": str(loc.get("id")),
                    "name": loc.get("name") or "Location",
                    "active": bool(loc.get("active", True)),
                    "address1": loc.get("address1") or "",
                    "city": loc.get("city") or "",
                    "province": loc.get("province") or "",
                    "country": loc.get("country") or "",
                }
                for loc in locations
            ]
        )


class ShopifyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = ShopifyShop.objects.filter(
            user_id=request.user.id, is_active=True
        ).first()
        if not shop:
            return Response(
                {"detail": "No Shopify store connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            orders = fetch_orders(shop)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Shopify orders fetch failed")
            detail = str(exc)
            response = getattr(exc, "response", None)
            if response is not None and getattr(response, "status_code", None) == 403:
                detail = (
                    "Shopify denied orders access (403). Reconnect to grant read_orders, "
                    "and enable Protected customer data for your app if required."
                )
            return Response(
                {"detail": detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            [
                {
                    "id": str(order.get("id")),
                    "name": order.get("name") or f"#{order.get('order_number')}",
                    "financialStatus": order.get("financial_status") or "",
                    "fulfillmentStatus": order.get("fulfillment_status") or "unfulfilled",
                    "totalPrice": order.get("total_price") or "0",
                    "currency": order.get("currency") or "USD",
                    "createdAt": order.get("created_at") or "",
                    "itemCount": len(order.get("line_items") or []),
                }
                for order in orders
            ]
        )
