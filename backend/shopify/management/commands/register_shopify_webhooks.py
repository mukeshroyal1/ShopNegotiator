from django.core.management.base import BaseCommand

from shopify.models import ShopifyShop
from shopify.services import register_webhooks, webhook_callback_url


class Command(BaseCommand):
    help = "Register Shopify product/inventory webhooks for all active shops."

    def handle(self, *args, **options):
        address = webhook_callback_url()
        if not address:
            self.stderr.write(
                "SHOPIFY_APP_URL is not set to a public HTTPS origin; cannot register webhooks."
            )
            return

        self.stdout.write(f"Webhook address: {address}")
        shops = ShopifyShop.objects.filter(is_active=True)
        if not shops.exists():
            self.stdout.write("No active shops.")
            return

        for shop in shops:
            try:
                register_webhooks(shop)
                self.stdout.write(self.style.SUCCESS(f"Registered for {shop.shop_domain}"))
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"Failed for {shop.shop_domain}: {exc}")
