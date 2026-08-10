import uuid

from django.db import models

from inventory.models import InventoryAlert, Product
from suppliers.models import Supplier


class Negotiation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column="product_id",
        null=True,
        blank=True,
        related_name="negotiations",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.DO_NOTHING,
        db_column="supplier_id",
        null=True,
        blank=True,
        related_name="negotiations",
    )
    alert = models.ForeignKey(
        InventoryAlert,
        on_delete=models.DO_NOTHING,
        db_column="alert_id",
        null=True,
        blank=True,
        related_name="negotiations",
    )
    status = models.TextField(default="negotiating")
    stage = models.TextField(default="Opening")
    progress = models.IntegerField(default=0)
    original_quote = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    current_offer = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    currency = models.TextField(default="USD")
    savings_pct = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "negotiations"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.DO_NOTHING,
        db_column="negotiation_id",
        related_name="messages",
    )
    role = models.TextField()
    body = models.TextField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "messages"


class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    kind = models.TextField(default="system")
    text = models.TextField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "activities"
