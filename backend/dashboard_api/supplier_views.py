from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db_schema import suppliers_milestone1_ready
from inventory.models import InventoryAlert, Product
from negotiation.models import Activity, Message, Negotiation
from suppliers.models import Supplier


def serialize_supplier(s: Supplier) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "contactName": s.contact_name or "",
        "phone": s.phone or "",
        "email": s.email,
        "defaultMoq": s.default_moq,
        "lastUnitPrice": float(s.last_unit_price) if s.last_unit_price else None,
        "currency": s.currency or "USD",
        "notes": s.notes or "",
        "createdAt": s.created_at.isoformat(),
        "updatedAt": s.updated_at.isoformat(),
    }


def serialize_inventory_alert(alert: InventoryAlert) -> dict:
    product_name = "Unknown product"
    sku = ""
    if alert.product_id:
        row = (
            Product.objects.filter(id=alert.product_id)
            .values_list("name", "sku")
            .first()
        )
        if row:
            product_name, sku = row[0], row[1] or ""

    return {
        "id": str(alert.id),
        "productId": str(alert.product_id),
        "productName": product_name,
        "sku": sku,
        "currentStock": alert.current_stock,
        "threshold": alert.threshold,
        "status": alert.status,
        "createdAt": alert.created_at.isoformat(),
        "updatedAt": alert.updated_at.isoformat(),
    }


class SupplierListCreateView(APIView):
    def get(self, request):
        if not suppliers_milestone1_ready():
            return Response(
                {
                    "detail": (
                        "Database needs Milestone 1 migration. "
                        "Run backend/db/milestone1_suppliers_alerts.sql in Supabase."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        rows = Supplier.objects.filter(user_id=request.user.id).order_by("name")
        return Response([serialize_supplier(s) for s in rows])

    def post(self, request):
        if not suppliers_milestone1_ready():
            return Response(
                {
                    "detail": (
                        "Database needs Milestone 1 migration. "
                        "Run backend/db/milestone1_suppliers_alerts.sql in Supabase."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        name = (request.data.get("name") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        if not name:
            return Response({"detail": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not phone:
            return Response({"detail": "Phone is required."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        supplier = Supplier.objects.create(
            user_id=request.user.id,
            name=name,
            contact_name=(request.data.get("contactName") or "").strip(),
            phone=phone,
            email=(request.data.get("email") or "").strip() or None,
            default_moq=int(request.data.get("defaultMoq") or 1),
            last_unit_price=_parse_price(request.data.get("lastUnitPrice")),
            currency=(request.data.get("currency") or "USD").strip() or "USD",
            notes=(request.data.get("notes") or "").strip(),
            created_at=now,
            updated_at=now,
        )
        return Response(serialize_supplier(supplier), status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    def patch(self, request, supplier_id):
        try:
            supplier = Supplier.objects.get(id=supplier_id, user_id=request.user.id)
        except Supplier.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if "name" in request.data:
            name = (request.data.get("name") or "").strip()
            if not name:
                return Response({"detail": "Name cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            supplier.name = name
        if "phone" in request.data:
            phone = (request.data.get("phone") or "").strip()
            if not phone:
                return Response({"detail": "Phone cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            supplier.phone = phone
        if "contactName" in request.data:
            supplier.contact_name = (request.data.get("contactName") or "").strip()
        if "email" in request.data:
            supplier.email = (request.data.get("email") or "").strip() or None
        if "defaultMoq" in request.data:
            supplier.default_moq = int(request.data.get("defaultMoq") or 1)
        if "lastUnitPrice" in request.data:
            supplier.last_unit_price = _parse_price(request.data.get("lastUnitPrice"))
        if "currency" in request.data:
            supplier.currency = (request.data.get("currency") or "USD").strip() or "USD"
        if "notes" in request.data:
            supplier.notes = (request.data.get("notes") or "").strip()

        supplier.updated_at = timezone.now()
        supplier.save()
        return Response(serialize_supplier(supplier))

    def delete(self, request, supplier_id):
        deleted, _ = Supplier.objects.filter(
            id=supplier_id, user_id=request.user.id
        ).delete()
        if not deleted:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InventoryAlertListView(APIView):
    def get(self, request):
        status_filter = (request.query_params.get("status") or "open").strip()
        qs = InventoryAlert.objects.filter(user_id=request.user.id)
        if status_filter != "all":
            qs = qs.filter(status=status_filter)
        rows = qs.order_by("-created_at")
        return Response([serialize_inventory_alert(a) for a in rows])


class StartNegotiationView(APIView):
    def post(self, request):
        if not suppliers_milestone1_ready():
            return Response(
                {
                    "detail": (
                        "Database needs Milestone 1 migration. "
                        "Run backend/db/milestone1_suppliers_alerts.sql in Supabase."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        alert_id = request.data.get("alertId")
        supplier_id = request.data.get("supplierId")
        if not alert_id or not supplier_id:
            return Response(
                {"detail": "alertId and supplierId are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            alert = InventoryAlert.objects.get(id=alert_id, user_id=request.user.id)
        except InventoryAlert.DoesNotExist:
            return Response({"detail": "Alert not found."}, status=status.HTTP_404_NOT_FOUND)

        product = (
            Product.objects.filter(id=alert.product_id).only("name").first()
            if alert.product_id
            else None
        )

        if alert.status not in ("open",):
            return Response(
                {"detail": f"Alert is already {alert.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            supplier = Supplier.objects.get(id=supplier_id, user_id=request.user.id)
        except Supplier.DoesNotExist:
            return Response({"detail": "Supplier not found."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        negotiation = Negotiation.objects.create(
            user_id=request.user.id,
            product_id=alert.product_id,
            supplier_id=supplier.id,
            alert_id=alert.id,
            status="waiting",
            stage="Ready to call",
            progress=0,
            currency=supplier.currency or "USD",
            created_at=now,
            updated_at=now,
        )

        Message.objects.create(
            user_id=request.user.id,
            negotiation_id=negotiation.id,
            role="system",
            body=(
                f"Negotiation queued for {product.name if product else 'product'} "
                f"with {supplier.name}. Voice call will start in a later milestone."
            ),
            created_at=now,
        )

        alert.status = "negotiating"
        alert.updated_at = now
        alert.save(update_fields=["status", "updated_at"])

        Activity.objects.create(
            user_id=request.user.id,
            kind="handshake",
            text=(
                f"Started negotiation for {product.name if product else 'product'} "
                f"with {supplier.name}"
            ),
            created_at=now,
        )

        return Response(
            {
                "id": str(negotiation.id),
                "status": negotiation.status,
                "stage": negotiation.stage,
                "product": product.name if product else "Unknown product",
                "supplier": supplier.name,
            },
            status=status.HTTP_201_CREATED,
        )


def _parse_price(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
