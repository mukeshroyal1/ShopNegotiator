from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.parse import unquote, urlencode
from uuid import UUID

import requests
from django.conf import settings
from django.utils import timezone

from inventory.models import Product
from negotiation.models import Activity
from shopify.models import ShopifyShop


def normalize_shop_domain(shop: str) -> str:
    value = (shop or "").strip().lower()
    value = value.replace("https://", "").replace("http://", "").strip("/")
    if value.endswith(".myshopify.com"):
        return value
    # allow bare store name
    if "." not in value and value:
        return f"{value}.myshopify.com"
    raise ValueError("Shop must be like your-store.myshopify.com")


def _sign_state(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{sig}"


def _verify_state(state: str) -> dict[str, Any]:
    state = unquote(state or "")
    try:
        body, sig = state.rsplit(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid OAuth state") from exc

    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise ValueError("Invalid OAuth state signature")

    pad = "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(body + pad).decode())
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("OAuth state expired")
    return payload


def build_authorize_url(*, user_id: UUID, shop: str) -> str:
    shop_domain = normalize_shop_domain(shop)
    state = _sign_state(
        {
            "uid": str(user_id),
            "shop": shop_domain,
            "nonce": secrets.token_urlsafe(12),
            "exp": int(time.time()) + 600,
        }
    )
    params = {
        "client_id": settings.SHOPIFY_API_KEY,
        "scope": settings.SHOPIFY_SCOPES,
        "redirect_uri": settings.SHOPIFY_REDIRECT_URI,
        "state": state,
    }
    return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"


def exchange_code_for_token(*, shop: str, code: str) -> dict[str, Any]:
    shop_domain = normalize_shop_domain(shop)
    url = f"https://{shop_domain}/admin/oauth/access_token"
    response = requests.post(
        url,
        data={
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(
            f"Shopify token exchange failed ({response.status_code}): {response.text[:200]}"
        )
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError(f"Shopify token exchange failed: {data}")
    return data


def save_shop_connection(*, user_id: UUID, shop: str, token_payload: dict[str, Any]) -> ShopifyShop:
    shop_domain = normalize_shop_domain(shop)
    now = timezone.now()
    existing = ShopifyShop.objects.filter(user_id=user_id).first()
    if existing:
        existing.shop_domain = shop_domain
        existing.access_token = token_payload["access_token"]
        existing.scope = token_payload.get("scope", "")
        existing.is_active = True
        existing.updated_at = now
        existing.save(
            update_fields=["shop_domain", "access_token", "scope", "is_active", "updated_at"]
        )
        return existing

    # If this shop was connected to another user, take it over (re-install).
    other = ShopifyShop.objects.filter(shop_domain=shop_domain).first()
    if other:
        other.user_id = user_id
        other.access_token = token_payload["access_token"]
        other.scope = token_payload.get("scope", "")
        other.is_active = True
        other.updated_at = now
        other.save(
            update_fields=["user_id", "access_token", "scope", "is_active", "updated_at"]
        )
        return other

    return ShopifyShop.objects.create(
        user_id=user_id,
        shop_domain=shop_domain,
        access_token=token_payload["access_token"],
        scope=token_payload.get("scope", ""),
        is_active=True,
        installed_at=now,
        updated_at=now,
    )


def shopify_get(shop: ShopifyShop, path: str, params: dict | None = None) -> dict[str, Any]:
    version = settings.SHOPIFY_API_VERSION
    url = f"https://{shop.shop_domain}/admin/api/{version}{path}"
    response = requests.get(
        url,
        params=params or {},
        headers={
            "X-Shopify-Access-Token": shop.access_token,
            "Content-Type": "application/json",
        },
        timeout=45,
    )
    response.raise_for_status()
    return response.json()


def fetch_locations(shop: ShopifyShop) -> list[dict[str, Any]]:
    data = shopify_get(shop, "/locations.json")
    return list(data.get("locations") or [])


def fetch_orders(shop: ShopifyShop, *, limit: int = 50) -> list[dict[str, Any]]:
    data = shopify_get(
        shop,
        "/orders.json",
        {"status": "any", "limit": min(limit, 250)},
    )
    return list(data.get("orders") or [])


def sync_products_from_shopify(
    shop: ShopifyShop, *, record_activity: bool = True
) -> int:
    """Pull products + inventory into the user's products table. Returns count upserted."""
    user_id = shop.user_id
    count = 0
    page_info = None
    seen_keys: set[str] = set()

    while True:
        params: dict[str, Any] = {"limit": 50}
        if page_info:
            params = {"limit": 50, "page_info": page_info}
        else:
            params["fields"] = "id,title,variants"

        version = settings.SHOPIFY_API_VERSION
        url = f"https://{shop.shop_domain}/admin/api/{version}/products.json"
        response = requests.get(
            url,
            params=params,
            headers={"X-Shopify-Access-Token": shop.access_token},
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        products = payload.get("products", [])

        now = timezone.now()
        for product in products:
            title = product.get("title") or "Untitled"
            product_id = str(product.get("id"))
            for variant in product.get("variants") or []:
                sku = (variant.get("sku") or "").strip() or f"shopify-{variant.get('id')}"
                stock = int(variant.get("inventory_quantity") or 0)
                shopify_variant_key = f"{product_id}:{variant.get('id')}"
                seen_keys.add(shopify_variant_key)
                name = title
                if variant.get("title") and variant.get("title") != "Default Title":
                    name = f"{title} — {variant['title']}"

                existing = Product.objects.filter(user_id=user_id, sku=sku).first()
                if existing:
                    existing.name = name
                    existing.current_stock = stock
                    existing.shopify_product_id = shopify_variant_key
                    existing.updated_at = now
                    if existing.threshold <= 0:
                        existing.threshold = 25
                    existing.save(
                        update_fields=[
                            "name",
                            "current_stock",
                            "shopify_product_id",
                            "threshold",
                            "updated_at",
                        ]
                    )
                else:
                    Product.objects.create(
                        user_id=user_id,
                        name=name,
                        sku=sku,
                        current_stock=stock,
                        threshold=25,
                        shopify_product_id=shopify_variant_key,
                        created_at=now,
                        updated_at=now,
                    )
                count += 1

        link = response.headers.get("Link", "")
        if 'rel="next"' in link:
            next_part = [p for p in link.split(",") if 'rel="next"' in p]
            if not next_part:
                break
            start = next_part[0].find("page_info=")
            end = next_part[0].find(">", start)
            page_info = next_part[0][start + len("page_info=") : end]
        else:
            break

    # Drop Shopify rows that no longer exist in the store.
    stale = Product.objects.filter(user_id=user_id).exclude(
        shopify_product_id__isnull=True
    ).exclude(shopify_product_id="")
    if seen_keys:
        stale = stale.exclude(shopify_product_id__in=seen_keys)
    stale.delete()

    shop.updated_at = timezone.now()
    shop.save(update_fields=["updated_at"])

    if record_activity:
        try:
            Activity.objects.create(
                user_id=user_id,
                kind="package",
                text=f"Synced {count} products from {shop.shop_domain}",
                created_at=timezone.now(),
            )
        except Exception:  # noqa: BLE001
            pass

    try:
        from inventory.services import sync_inventory_alerts_for_user

        sync_inventory_alerts_for_user(user_id)
    except Exception:  # noqa: BLE001
        pass

    return count


WEBHOOK_TOPICS = (
    "products/create",
    "products/update",
    "products/delete",
    "inventory_levels/update",
)


def webhook_callback_url() -> str | None:
    base = (getattr(settings, "SHOPIFY_APP_URL", None) or "").rstrip("/")
    if not base:
        # Derive from redirect URI host when it's publicly reachable.
        redirect = (settings.SHOPIFY_REDIRECT_URI or "").rstrip("/")
        if redirect.startswith("https://") and "localhost" not in redirect:
            base = redirect.rsplit("/api/shopify/", 1)[0]
    if not base or "localhost" in base or "127.0.0.1" in base:
        return None
    return f"{base}/api/shopify/webhooks/"


def register_webhooks(shop: ShopifyShop) -> None:
    address = webhook_callback_url()
    if not address:
        return

    version = settings.SHOPIFY_API_VERSION
    list_url = f"https://{shop.shop_domain}/admin/api/{version}/webhooks.json"
    headers = {"X-Shopify-Access-Token": shop.access_token}

    existing: list[dict[str, Any]] = []
    try:
        listed = requests.get(list_url, headers=headers, timeout=30)
        listed.raise_for_status()
        existing = list(listed.json().get("webhooks") or [])
    except Exception:  # noqa: BLE001
        existing = []

    for topic in WEBHOOK_TOPICS:
        already = next(
            (
                w
                for w in existing
                if w.get("topic") == topic and w.get("address") == address
            ),
            None,
        )
        if already:
            continue
        requests.post(
            list_url,
            headers={**headers, "Content-Type": "application/json"},
            json={"webhook": {"topic": topic, "address": address, "format": "json"}},
            timeout=30,
        ).raise_for_status()


def verify_shopify_webhook(*, body: bytes, hmac_header: str) -> bool:
    digest = hmac.new(
        settings.SHOPIFY_API_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    computed = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed, hmac_header or "")


def complete_oauth(*, state: str, shop: str, code: str) -> ShopifyShop:
    payload = _verify_state(state)
    expected_shop = payload.get("shop")
    shop_domain = normalize_shop_domain(shop)
    if expected_shop and expected_shop != shop_domain:
        raise ValueError("Shop mismatch in OAuth state")

    user_id = UUID(str(payload["uid"]))
    token_payload = exchange_code_for_token(shop=shop_domain, code=code)
    shop_row = save_shop_connection(
        user_id=user_id, shop=shop_domain, token_payload=token_payload
    )

    try:
        Activity.objects.create(
            user_id=user_id,
            kind="system",
            text=f"Connected Shopify store {shop_domain}",
            created_at=timezone.now(),
        )
    except Exception:  # noqa: BLE001
        pass

    try:
        sync_products_from_shopify(shop_row, record_activity=True)
    except Exception:  # noqa: BLE001
        pass

    try:
        register_webhooks(shop_row)
    except Exception:  # noqa: BLE001
        pass

    return shop_row
