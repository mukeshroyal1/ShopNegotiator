from __future__ import annotations

from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.agent_auth import IsAgentService
from inventory.models import InventoryAlert, Product
from negotiation.models import Activity, Message, Negotiation
from quotes.models import Quote
from suppliers.models import Supplier


def _negotiation_or_404(negotiation_id) -> Negotiation | Response:
    try:
        return Negotiation.objects.get(id=negotiation_id)
    except Negotiation.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


def serialize_context(n: Negotiation) -> dict:
    product = (
        Product.objects.filter(id=n.product_id).first() if n.product_id else None
    )
    supplier = (
        Supplier.objects.filter(id=n.supplier_id).first() if n.supplier_id else None
    )
    alert = InventoryAlert.objects.filter(id=n.alert_id).first() if n.alert_id else None

    reorder_qty = 0
    if product:
        reorder_qty = max(product.threshold * 2 - product.current_stock, product.threshold, 1)

    messages = list(
        Message.objects.filter(negotiation_id=n.id)
        .order_by("created_at")
        .values("role", "body", "created_at")[:40]
    )

    return {
        "id": str(n.id),
        "userId": str(n.user_id),
        "status": n.status,
        "stage": n.stage,
        "progress": n.progress,
        "currency": n.currency or "USD",
        "originalQuote": float(n.original_quote) if n.original_quote is not None else None,
        "currentOffer": float(n.current_offer) if n.current_offer is not None else None,
        "product": None
        if not product
        else {
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "currentStock": product.current_stock,
            "threshold": product.threshold,
            "reorderQty": reorder_qty,
        },
        "supplier": None
        if not supplier
        else {
            "id": str(supplier.id),
            "name": supplier.name,
            "contactName": supplier.contact_name or "",
            "phone": supplier.phone or "",
            "defaultMoq": supplier.default_moq,
            "lastUnitPrice": float(supplier.last_unit_price)
            if supplier.last_unit_price is not None
            else None,
            "currency": supplier.currency or "USD",
        },
        "alert": None
        if not alert
        else {
            "id": str(alert.id),
            "currentStock": alert.current_stock,
            "threshold": alert.threshold,
            "status": alert.status,
        },
        "messages": [
            {
                "role": m["role"],
                "body": m["body"],
            }
            for m in messages
            if m["role"] in ("agent", "supplier")
        ],
    }


class InternalNegotiationContextView(APIView):
    authentication_classes: list = []
    permission_classes = [IsAgentService]

    def get(self, request, negotiation_id):
        n = _negotiation_or_404(negotiation_id)
        if isinstance(n, Response):
            return n
        return Response(serialize_context(n))


class InternalNegotiationMessageView(APIView):
    authentication_classes: list = []
    permission_classes = [IsAgentService]

    def post(self, request, negotiation_id):
        n = _negotiation_or_404(negotiation_id)
        if isinstance(n, Response):
            return n

        role = (request.data.get("role") or "").strip()
        body = (request.data.get("body") or "").strip()
        if role not in ("agent", "supplier", "system"):
            return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)
        if not body:
            return Response({"detail": "body is required."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        message = Message.objects.create(
            user_id=n.user_id,
            negotiation_id=n.id,
            role=role,
            body=body,
            created_at=now,
        )
        n.updated_at = now
        n.save(update_fields=["updated_at"])
        return Response(
            {"id": str(message.id), "role": message.role, "body": message.body},
            status=status.HTTP_201_CREATED,
        )


class InternalNegotiationQuoteView(APIView):
    authentication_classes: list = []
    permission_classes = [IsAgentService]

    def post(self, request, negotiation_id):
        n = _negotiation_or_404(negotiation_id)
        if isinstance(n, Response):
            return n

        try:
            unit_price = Decimal(str(request.data.get("unitPrice")))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"detail": "unitPrice is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        quote = Quote.objects.create(
            user_id=n.user_id,
            negotiation_id=n.id,
            supplier_id=n.supplier_id,
            unit_price=unit_price,
            currency=(request.data.get("currency") or n.currency or "USD"),
            moq=int(request.data.get("moq") or 1),
            lead_time_days=int(request.data.get("leadTimeDays") or 0),
            is_selected=bool(request.data.get("isSelected", True)),
            created_at=now,
        )
        n.updated_at = now
        n.save(update_fields=["updated_at"])
        return Response(
            {"id": str(quote.id), "unitPrice": float(quote.unit_price)},
            status=status.HTTP_201_CREATED,
        )


class InternalNegotiationPatchView(APIView):
    authentication_classes: list = []
    permission_classes = [IsAgentService]

    def patch(self, request, negotiation_id):
        n = _negotiation_or_404(negotiation_id)
        if isinstance(n, Response):
            return n

        now = timezone.now()
        fields = ["updated_at"]
        if "status" in request.data:
            n.status = request.data["status"]
            fields.append("status")
        if "stage" in request.data:
            n.stage = request.data["stage"]
            fields.append("stage")
        if "progress" in request.data:
            n.progress = int(request.data["progress"])
            fields.append("progress")
        if "originalQuote" in request.data:
            n.original_quote = _decimal_or_none(request.data.get("originalQuote"))
            fields.append("original_quote")
        if "currentOffer" in request.data:
            n.current_offer = _decimal_or_none(request.data.get("currentOffer"))
            fields.append("current_offer")
        if "savingsPct" in request.data:
            n.savings_pct = _decimal_or_none(request.data.get("savingsPct"))
            fields.append("savings_pct")

        n.updated_at = now
        n.save(update_fields=fields)

        if request.data.get("resolveAlert") and n.alert_id:
            InventoryAlert.objects.filter(id=n.alert_id).update(
                status="resolved", updated_at=now
            )

        if request.data.get("activity"):
            Activity.objects.create(
                user_id=n.user_id,
                kind="handshake",
                text=str(request.data["activity"]),
                created_at=now,
            )

        return Response({"ok": True, "status": n.status, "stage": n.stage})


class NegotiationDryRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, negotiation_id):
        return _forward_to_agent(
            request,
            negotiation_id,
            path="/runs/start",
            stage="Dry run",
        )


class NegotiationCallView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, negotiation_id):
        return _forward_to_agent(
            request,
            negotiation_id,
            path="/runs/call",
            stage="Starting call",
            timeout=30,
        )


def _forward_to_agent(
    request,
    negotiation_id,
    *,
    path: str,
    stage: str,
    timeout: int = 45,
):
    agent_url = (getattr(settings, "AGENT_SERVICE_URL", None) or "").rstrip("/")
    agent_secret = (getattr(settings, "AGENT_SERVICE_SECRET", None) or "").strip()
    if not agent_url or not agent_secret:
        return Response(
            {
                "detail": (
                    "Agent service is not configured. Set AGENT_SERVICE_URL and "
                    "AGENT_SERVICE_SECRET, then run the agent locally "
                    "(see agent/README.md)."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        n = Negotiation.objects.get(id=negotiation_id, user_id=request.user.id)
    except Negotiation.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if n.status not in ("waiting", "negotiating"):
        return Response(
            {"detail": f"Cannot run a {n.status} negotiation."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    n.status = "negotiating"
    n.stage = stage
    n.progress = 10
    n.updated_at = now
    n.save(update_fields=["status", "stage", "progress", "updated_at"])

    try:
        response = requests.post(
            f"{agent_url}{path}",
            json={"negotiationId": str(n.id)},
            headers={
                "Content-Type": "application/json",
                "X-Agent-Secret": agent_secret,
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return Response(
            {"detail": f"Could not reach agent service: {exc}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if not response.ok:
        detail = "Agent run failed."
        try:
            body = response.json()
            if isinstance(body, dict) and body.get("detail"):
                detail = str(body["detail"])
        except ValueError:
            pass
        return Response({"detail": detail}, status=status.HTTP_502_BAD_GATEWAY)

    payload = {}
    try:
        payload = response.json()
    except ValueError:
        payload = {"ok": True}

    return Response(
        {
            "ok": True,
            "id": str(n.id),
            "outcome": payload.get("outcome"),
            "stage": payload.get("stage"),
            "callId": payload.get("callId"),
        },
        status=status.HTTP_202_ACCEPTED,
    )


def _decimal_or_none(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
