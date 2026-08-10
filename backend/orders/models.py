import uuid

from django.db import models

from negotiation.models import Negotiation
from quotes.models import Quote


class PurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.DO_NOTHING,
        db_column="quote_id",
        null=True,
        blank=True,
        related_name="purchase_orders",
    )
    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.DO_NOTHING,
        db_column="negotiation_id",
        null=True,
        blank=True,
        related_name="purchase_orders",
    )
    status = models.TextField(default="draft")
    total_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    currency = models.TextField(default="USD")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "purchase_orders"
