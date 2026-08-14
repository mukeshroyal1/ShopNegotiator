from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db_schema import suppliers_milestone1_ready
from dashboard_api.negotiation_helpers import (
    negotiation_name_maps,
    serialize_negotiation,
    supplier_name_map,
)
from negotiation.models import Activity, Negotiation
from orders.models import PurchaseOrder
from quotes.models import Quote


def _relative_time(dt) -> str:
    if not dt:
        return ""
    now = timezone.now()
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    return f"{days}d ago"


class DashboardView(APIView):
    def get(self, request):
        user_id = request.user.id
        month_ago = timezone.now() - timedelta(days=30)

        active_qs = Negotiation.objects.filter(
            user_id=user_id, status__in=["negotiating", "waiting"]
        )
        active_count = active_qs.count()

        completed_month = Negotiation.objects.filter(
            user_id=user_id, status="completed", updated_at__gte=month_ago
        )
        money_saved = Decimal("0")
        for n in completed_month:
            if n.original_quote and n.current_offer:
                money_saved += max(n.original_quote - n.current_offer, Decimal("0"))

        suppliers_contacted = (
            Negotiation.objects.filter(user_id=user_id, supplier_id__isnull=False)
            .values("supplier_id")
            .distinct()
            .count()
        )

        avg_savings = Negotiation.objects.filter(
            user_id=user_id, savings_pct__isnull=False
        ).aggregate(avg=Avg("savings_pct"))["avg"]

        negotiation_rows = list(
            Negotiation.objects.filter(user_id=user_id).order_by("-updated_at")[:10]
        )
        supplier_names, product_names = negotiation_name_maps(negotiation_rows)
        negotiations = [
            serialize_negotiation(
                n, supplier_names=supplier_names, product_names=product_names
            )
            for n in negotiation_rows
        ]

        activities = [
            {
                "id": str(a.id),
                "text": a.text,
                "time": _relative_time(a.created_at),
                "kind": a.kind,
            }
            for a in Activity.objects.filter(user_id=user_id).order_by("-created_at")[
                :20
            ]
        ]

        return Response(
            {
                "stats": {
                    "activeNegotiations": active_count,
                    "moneySavedThisMonth": float(money_saved),
                    "suppliersContacted": suppliers_contacted,
                    "averageSavings": float(avg_savings or 0),
                },
                "negotiations": negotiations,
                "activities": activities,
            }
        )


class NegotiationListView(APIView):
    def get(self, request):
        user_id = request.user.id
        rows = list(
            Negotiation.objects.filter(user_id=user_id).order_by("-updated_at")
        )
        supplier_names, product_names = negotiation_name_maps(rows)
        return Response(
            [
                serialize_negotiation(
                    n, supplier_names=supplier_names, product_names=product_names
                )
                for n in rows
            ]
        )


class NegotiationDetailView(APIView):
    def get(self, request, negotiation_id):
        user_id = request.user.id
        try:
            n = Negotiation.objects.get(id=negotiation_id, user_id=user_id)
        except Negotiation.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        supplier_names, product_names = negotiation_name_maps([n])
        payload = serialize_negotiation(
            n, supplier_names=supplier_names, product_names=product_names
        )
        payload["messages"] = [
            {
                "id": str(m.id),
                "role": m.role,
                "body": m.body,
                "createdAt": m.created_at.isoformat(),
            }
            for m in n.messages.order_by("created_at")
        ]
        quote_rows = list(
            Quote.objects.filter(negotiation=n, user_id=user_id).only(
                "id",
                "supplier_id",
                "unit_price",
                "currency",
                "moq",
                "lead_time_days",
                "is_selected",
            )
        )
        quote_supplier_names = supplier_name_map(q.supplier_id for q in quote_rows)
        payload["quotes"] = [
            {
                "id": str(q.id),
                "supplierName": quote_supplier_names.get(q.supplier_id, "Supplier")
                if q.supplier_id
                else "Supplier",
                "unitPrice": float(q.unit_price),
                "currency": q.currency,
                "moq": q.moq,
                "leadTimeDays": q.lead_time_days,
                "isSelected": q.is_selected,
            }
            for q in quote_rows
        ]
        return Response(payload)


class ProductListView(APIView):
    def get(self, request):
        from inventory.models import Product

        # DB-only read path. Catalog freshness comes from Shopify webhooks
        # (and optional Settings sync) — never block list GET on Admin API I/O.
        rows = Product.objects.filter(user_id=request.user.id).order_by("name")
        return Response(
            [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "sku": p.sku,
                    "currentStock": p.current_stock,
                    "threshold": p.threshold,
                    "shopifyProductId": p.shopify_product_id,
                    "lowStock": p.current_stock <= p.threshold,
                }
                for p in rows
            ]
        )


class PurchaseOrderListView(APIView):
    def get(self, request):
        rows = PurchaseOrder.objects.filter(user_id=request.user.id).order_by(
            "-created_at"
        )
        return Response(
            [
                {
                    "id": str(po.id),
                    "status": po.status,
                    "totalAmount": float(po.total_amount or 0),
                    "currency": po.currency,
                    "createdAt": po.created_at.isoformat(),
                }
                for po in rows
            ]
        )


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        import os

        from django.conf import settings as dj_settings

        # Presence only — never return secret values.
        env_present = {
            key: bool((os.getenv(key) or "").strip())
            for key in (
                "DATABASE_URL",
                "DJANGO_SECRET_KEY",
                "DJANGO_ALLOWED_HOSTS",
                "SUPABASE_URL",
                "SUPABASE_JWT_SECRET",
                "SHOPIFY_API_KEY",
                "SHOPIFY_API_SECRET",
                "SHOPIFY_APP_URL",
                "FRONTEND_URL",
                "CORS_ALLOWED_ORIGINS",
            )
        }
        return Response(
            {
                "ok": True,
                "service": "bargainlabs-api",
                "envPresent": env_present,
                "allowedHostsCount": len(dj_settings.ALLOWED_HOSTS),
                "schemaMilestone1": suppliers_milestone1_ready(),
            }
        )
