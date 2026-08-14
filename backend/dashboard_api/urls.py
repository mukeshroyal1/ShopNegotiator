from django.urls import path

from . import supplier_views, views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("negotiations/", views.NegotiationListView.as_view(), name="negotiations"),
    path(
        "negotiations/start/",
        supplier_views.StartNegotiationView.as_view(),
        name="negotiations-start",
    ),
    path(
        "negotiations/<uuid:negotiation_id>/",
        views.NegotiationDetailView.as_view(),
        name="negotiation-detail",
    ),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("suppliers/", supplier_views.SupplierListCreateView.as_view(), name="suppliers"),
    path(
        "suppliers/<uuid:supplier_id>/",
        supplier_views.SupplierDetailView.as_view(),
        name="supplier-detail",
    ),
    path(
        "inventory-alerts/",
        supplier_views.InventoryAlertListView.as_view(),
        name="inventory-alerts",
    ),
    path(
        "purchase-orders/",
        views.PurchaseOrderListView.as_view(),
        name="purchase-orders",
    ),
]
