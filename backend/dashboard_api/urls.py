from django.urls import path

from . import internal_views, supplier_views, twilio_views, views

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
        "negotiations/<uuid:negotiation_id>/call/",
        internal_views.NegotiationCallView.as_view(),
        name="negotiation-call",
    ),
    path(
        "negotiations/<uuid:negotiation_id>/dry-run/",
        internal_views.NegotiationDryRunView.as_view(),
        name="negotiation-dry-run",
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
    path(
        "twilio/voice/<uuid:negotiation_id>/",
        twilio_views.TwilioVoiceView.as_view(),
        name="twilio-voice",
    ),
    path(
        "twilio/gather/<uuid:negotiation_id>/",
        twilio_views.TwilioGatherView.as_view(),
        name="twilio-gather",
    ),
    path(
        "twilio/status/<uuid:negotiation_id>/",
        twilio_views.TwilioStatusView.as_view(),
        name="twilio-status",
    ),
    path(
        "internal/negotiations/<uuid:negotiation_id>/context/",
        internal_views.InternalNegotiationContextView.as_view(),
        name="internal-negotiation-context",
    ),
    path(
        "internal/negotiations/<uuid:negotiation_id>/messages/",
        internal_views.InternalNegotiationMessageView.as_view(),
        name="internal-negotiation-messages",
    ),
    path(
        "internal/negotiations/<uuid:negotiation_id>/quotes/",
        internal_views.InternalNegotiationQuoteView.as_view(),
        name="internal-negotiation-quotes",
    ),
    path(
        "internal/negotiations/<uuid:negotiation_id>/twilio-call/",
        twilio_views.InternalTwilioCallView.as_view(),
        name="internal-twilio-call",
    ),
    path(
        "internal/negotiations/<uuid:negotiation_id>/",
        internal_views.InternalNegotiationPatchView.as_view(),
        name="internal-negotiation-patch",
    ),
]
