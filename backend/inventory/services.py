from __future__ import annotations

from uuid import UUID

from django.utils import timezone

from inventory.models import InventoryAlert, Product
from negotiation.models import Activity

OPEN_ALERT_STATUSES = ("open", "negotiating")


def sync_inventory_alert_for_product(product: Product) -> InventoryAlert | None:
    """Create, update, or resolve alerts when stock crosses the threshold."""
    now = timezone.now()
    user_id = product.user_id
    low = product.current_stock <= product.threshold

    open_alert = (
        InventoryAlert.objects.filter(
            user_id=user_id,
            product_id=product.id,
            status__in=OPEN_ALERT_STATUSES,
        )
        .order_by("-created_at")
        .first()
    )

    if low:
        if open_alert:
            open_alert.current_stock = product.current_stock
            open_alert.threshold = product.threshold
            open_alert.updated_at = now
            open_alert.save(
                update_fields=["current_stock", "threshold", "updated_at"]
            )
            return open_alert

        alert = InventoryAlert.objects.create(
            user_id=user_id,
            product_id=product.id,
            current_stock=product.current_stock,
            threshold=product.threshold,
            status="open",
            created_at=now,
            updated_at=now,
        )
        try:
            Activity.objects.create(
                user_id=user_id,
                kind="alert",
                text=(
                    f"Low stock: {product.name} "
                    f"({product.current_stock} left, threshold {product.threshold})"
                ),
                created_at=now,
            )
        except Exception:  # noqa: BLE001
            pass
        return alert

    if open_alert and open_alert.status == "open":
        open_alert.status = "resolved"
        open_alert.updated_at = now
        open_alert.save(update_fields=["status", "updated_at"])

    return None


def sync_inventory_alerts_for_user(user_id: UUID) -> int:
    """Reconcile alerts for every product belonging to the user."""
    touched = 0
    for product in Product.objects.filter(user_id=user_id):
        if sync_inventory_alert_for_product(product):
            touched += 1
    return touched
