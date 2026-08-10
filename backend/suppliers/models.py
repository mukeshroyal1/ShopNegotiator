import uuid

from django.db import models


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    name = models.TextField()
    email = models.EmailField(null=True, blank=True)
    alibaba_listing_id = models.TextField(null=True, blank=True)
    notes = models.TextField(default="")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "suppliers"
