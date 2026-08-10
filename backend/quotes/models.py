import uuid

from django.db import models

from negotiation.models import Negotiation
from suppliers.models import Supplier


class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.DO_NOTHING,
        db_column="negotiation_id",
        related_name="quotes",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.DO_NOTHING,
        db_column="supplier_id",
        null=True,
        blank=True,
        related_name="quotes",
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.TextField(default="USD")
    moq = models.IntegerField(default=1)
    lead_time_days = models.IntegerField(default=0)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "quotes"
