import uuid

from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    name = models.TextField()
    sku = models.TextField(default="")
    current_stock = models.IntegerField(default=0)
    threshold = models.IntegerField(default=0)
    shopify_product_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "products"


class InventoryAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column="product_id",
        related_name="alerts",
    )
    current_stock = models.IntegerField()
    threshold = models.IntegerField()
    status = models.TextField(default="open")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "inventory_alerts"
