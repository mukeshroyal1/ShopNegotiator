import uuid

from django.db import models


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    name = models.TextField()
    contact_name = models.TextField(default="")
    phone = models.TextField(default="")
    email = models.EmailField(null=True, blank=True)
    default_moq = models.IntegerField(default=1)
    last_unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    currency = models.TextField(default="USD")
    notes = models.TextField(default="")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "suppliers"
