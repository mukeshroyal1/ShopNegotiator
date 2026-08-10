from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("negotiations/", views.NegotiationListView.as_view(), name="negotiations"),
    path(
        "negotiations/<uuid:negotiation_id>/",
        views.NegotiationDetailView.as_view(),
        name="negotiation-detail",
    ),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("suppliers/", views.SupplierListView.as_view(), name="suppliers"),
    path(
        "purchase-orders/",
        views.PurchaseOrderListView.as_view(),
        name="purchase-orders",
    ),
]
