from __future__ import annotations

from decimal import Decimal
from typing import Iterable
from uuid import UUID

from inventory.models import Product
from negotiation.models import Negotiation
from suppliers.models import Supplier


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
    from django.utils import timezone

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


def _name_map(model, ids: Iterable[UUID | None]) -> dict[UUID, str]:
    clean = {i for i in ids if i}
    if not clean:
        return {}
    return {
        row_id: name
        for row_id, name in model.objects.filter(id__in=clean).values_list("id", "name")
    }


def negotiation_name_maps(
    negotiations: Iterable[Negotiation],
) -> tuple[dict[UUID, str], dict[UUID, str]]:
    rows = list(negotiations)
    supplier_names = _name_map(Supplier, (n.supplier_id for n in rows))
    product_names = _name_map(Product, (n.product_id for n in rows))
    return supplier_names, product_names


def serialize_negotiation(
    n: Negotiation,
    *,
    supplier_names: dict[UUID, str] | None = None,
    product_names: dict[UUID, str] | None = None,
) -> dict:
    if supplier_names is None or product_names is None:
        supplier_names, product_names = negotiation_name_maps([n])

    currency = n.currency or "USD"
    savings = None
    if n.savings_pct is not None:
        savings = _pct(n.savings_pct)
    elif n.original_quote and n.current_offer and n.original_quote > 0:
        savings = _pct(
            ((n.original_quote - n.current_offer) / n.original_quote) * Decimal(100)
        )

    supplier_label = "Unknown supplier"
    if n.supplier_id:
        supplier_label = supplier_names.get(n.supplier_id, "Unknown supplier")

    product_label = "Unknown product"
    if n.product_id:
        product_label = product_names.get(n.product_id, "Unknown product")

    return {
        "id": str(n.id),
        "supplier": supplier_label,
        "product": product_label,
        "status": n.status,
        "originalQuote": _money(n.original_quote, currency),
        "currentOffer": _money(n.current_offer, currency),
        "savings": savings or "—",
        "stage": n.stage,
        "progress": n.progress,
        "updatedAt": _relative_time(n.updated_at),
    }


def supplier_name_map(ids: Iterable[UUID | None]) -> dict[UUID, str]:
    return _name_map(Supplier, ids)
