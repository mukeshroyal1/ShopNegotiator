from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


def fetch_fair_price(context: dict[str, Any], *, supplier_ask: float | None = None) -> dict[str, Any] | None:
    """Call local ML /predict. Returns None if unset/unreachable."""
    base = (settings.ml_service_url or "").rstrip("/")
    if not base:
        return None

    product = context.get("product") or {}
    supplier = context.get("supplier") or {}
    last = supplier.get("lastUnitPrice")
    qty = float(product.get("reorderQty") or supplier.get("defaultMoq") or 100)
    if last is None and supplier_ask is None:
        return None

    last_f = float(last) if last is not None else float(supplier_ask or 0)
    ask_f = float(supplier_ask) if supplier_ask is not None else last_f * 1.12
    if last_f <= 0 or ask_f <= 0:
        return None

    # Hoodie-model defaults until product metadata carries tier/region
    body = {
        "quantity": qty,
        "moq": float(supplier.get("defaultMoq") or max(12, int(qty * 0.1))),
        "weightOz": 8.5,
        "leadTimeDays": 14,
        "daysSinceLastBuy": 60,
        "lastUnitPrice": last_f,
        "supplierAsk": ask_f,
        "skuTier": "mid",
        "supplierTier": "standard",
        "region": "US",
        "currency": context.get("currency")
        or supplier.get("currency")
        or "USD",
    }
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.post(f"{base}/predict", json=body)
        if response.status_code >= 400:
            return None
        data = response.json()
        if "fairPrice" not in data:
            return None
        return data
    except Exception:  # noqa: BLE001
        return None
