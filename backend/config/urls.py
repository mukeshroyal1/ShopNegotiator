from django.urls import include, path

urlpatterns = [
    path("api/", include("dashboard_api.urls")),
    path("api/shopify/", include("shopify.urls")),
]
