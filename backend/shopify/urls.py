from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.ShopifyStatusView.as_view(), name="shopify-status"),
    path("connect/", views.ShopifyConnectView.as_view(), name="shopify-connect"),
    path("callback/", views.ShopifyCallbackView.as_view(), name="shopify-callback"),
    path("sync/", views.ShopifySyncView.as_view(), name="shopify-sync"),
    path("webhooks/", views.ShopifyWebhookView.as_view(), name="shopify-webhooks"),
    path("locations/", views.ShopifyLocationsView.as_view(), name="shopify-locations"),
    path("orders/", views.ShopifyOrdersView.as_view(), name="shopify-orders"),
]
