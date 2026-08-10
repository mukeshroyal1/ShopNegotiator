from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from negotiation.models import Activity, Negotiation
from orders.models import PurchaseOrder
from quotes.models import Quote


def _money(value: Decimal | None, currency: str = "USD") -> str:
    if value is None:
        return f"{currency} 0.00"
    return f"{currency} {value:.2f}"


def _pct(value: Decimal | None) -> str:
    if value is None:
        return "0%"
    return f"{value:.1f}%"


def _relative_time(dt) -> str:
    if not dt:
        return ""
    now = timezone.now()
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    return f"{days}d ago"


def serialize_negotiation(n: Negotiation) -> dict:
    currency = n.currency or "USD"
    savings = None
    if n.savings_pct is not None:
        savings = _pct(n.savings_pct)
    elif n.original_quote and n.current_offer and n.original_quote > 0:
        savings = _pct(
            ((n.original_quote - n.current_offer) / n.original_quote) * Decimal(100)
        )

    return {
        "id": str(n.id),
        "supplier": n.supplier.name if n.supplier_id else "Unknown supplier",
        "product": n.product.name if n.product_id else "Unknown product",
        "status": n.status,
        "originalQuote": _money(n.original_quote, currency),
        "currentOffer": _money(n.current_offer, currency),
        "savings": savings or "—",
        "stage": n.stage,
        "progress": n.progress,
        "updatedAt": _relative_time(n.updated_at),
    }


class DashboardView(APIView):
    def get(self, request):
        user_id = request.user.id
        month_ago = timezone.now() - timedelta(days=30)

        active_qs = Negotiation.objects.filter(
            user_id=user_id, status__in=["negotiating", "waiting"]
        )
        active_count = active_qs.count()

        completed_month = Negotiation.objects.filter(
            user_id=user_id, status="completed", updated_at__gte=month_ago
        )
        money_saved = Decimal("0")
        for n in completed_month:
            if n.original_quote and n.current_offer:
                money_saved += max(n.original_quote - n.current_offer, Decimal("0"))

        suppliers_contacted = (
            Negotiation.objects.filter(user_id=user_id, supplier_id__isnull=False)
            .values("supplier_id")
            .distinct()
            .count()
        )

        avg_savings = Negotiation.objects.filter(
            user_id=user_id, savings_pct__isnull=False
        ).aggregate(avg=Avg("savings_pct"))["avg"]

        negotiations = [
            serialize_negotiation(n)
            for n in Negotiation.objects.filter(user_id=user_id)
            .select_related("product", "supplier")
            .order_by("-updated_at")[:10]
        ]

        activities = [
            {
                "id": str(a.id),
                "text": a.text,
                "time": _relative_time(a.created_at),
                "kind": a.kind,
            }
            for a in Activity.objects.filter(user_id=user_id).order_by("-created_at")[
                :20
            ]
        ]

        return Response(
            {
                "stats": {
                    "activeNegotiations": active_count,
                    "moneySavedThisMonth": float(money_saved),
                    "suppliersContacted": suppliers_contacted,
                    "averageSavings": float(avg_savings or 0),
                },
                "negotiations": negotiations,
                "activities": activities,
            }
        )


class NegotiationListView(APIView):
    def get(self, request):
        user_id = request.user.id
        rows = (
            Negotiation.objects.filter(user_id=user_id)
            .select_related("product", "supplier")
            .order_by("-updated_at")
        )
        return Response([serialize_negotiation(n) for n in rows])


class NegotiationDetailView(APIView):
    def get(self, request, negotiation_id):
        user_id = request.user.id
        try:
            n = Negotiation.objects.select_related("product", "supplier").get(
                id=negotiation_id, user_id=user_id
            )
        except Negotiation.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        payload = serialize_negotiation(n)
        payload["messages"] = [
            {
                "id": str(m.id),
                "role": m.role,
                "body": m.body,
                "createdAt": m.created_at.isoformat(),
            }
            for m in n.messages.order_by("created_at")
        ]
        payload["quotes"] = [
            {
                "id": str(q.id),
                "supplierName": q.supplier.name if q.supplier_id else "Supplier",
                "unitPrice": float(q.unit_price),
                "currency": q.currency,
                "moq": q.moq,
                "leadTimeDays": q.lead_time_days,
                "isSelected": q.is_selected,
            }
            for q in Quote.objects.filter(negotiation=n, user_id=user_id).select_related(
                "supplier"
            )
        ]
        return Response(payload)


class ProductListView(APIView):
    def get(self, request):
        from inventory.models import Product
        from shopify.models import ShopifyShop
        from shopify.services import ensure_shop_catalog_fresh

        shop = ShopifyShop.objects.filter(
            user_id=request.user.id, is_active=True
        ).first()
        if shop:
            try:
                ensure_shop_catalog_fresh(shop)
            except Exception:  # noqa: BLE001
                # Still return last known catalog if Shopify is briefly unavailable.
                pass

        rows = Product.objects.filter(user_id=request.user.id).order_by("name")
        return Response(
            [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "sku": p.sku,
                    "currentStock": p.current_stock,
                    "threshold": p.threshold,
                    "shopifyProductId": p.shopify_product_id,
                    "lowStock": p.current_stock <= p.threshold,
                }
                for p in rows
            ]
        )


class SupplierListView(APIView):
    def get(self, request):
        from suppliers.models import Supplier

        rows = Supplier.objects.filter(user_id=request.user.id).order_by("name")
        return Response(
            [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "email": s.email,
                    "alibabaListingId": s.alibaba_listing_id,
                }
                for s in rows
            ]
        )


class PurchaseOrderListView(APIView):
    def get(self, request):
        rows = PurchaseOrder.objects.filter(user_id=request.user.id).order_by(
            "-created_at"
        )
        return Response(
            [
                {
                    "id": str(po.id),
                    "status": po.status,
                    "totalAmount": float(po.total_amount or 0),
                    "currency": po.currency,
                    "createdAt": po.created_at.isoformat(),
                }
                for po in rows
            ]
        )


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"ok": True, "service": "bargainlabs-api"})
