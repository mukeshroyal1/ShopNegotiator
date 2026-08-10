import uuid

from django.db import models


class ShopifyShop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)
    shop_domain = models.TextField(unique=True)
    access_token = models.TextField()
    scope = models.TextField(default="")
    is_active = models.BooleanField(default=True)
    installed_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "shopify_shops"
