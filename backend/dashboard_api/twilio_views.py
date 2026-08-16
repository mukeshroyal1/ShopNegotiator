from __future__ import annotations

import hmac
from decimal import Decimal
from urllib.parse import quote
from xml.sax.saxutils import escape

import requests
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.agent_auth import IsAgentService
from inventory.models import InventoryAlert
from negotiation.models import Activity, Message, Negotiation
from quotes.models import Quote
from suppliers.models import Supplier


def _webhook_token() -> str:
    return (
        (getattr(settings, "TWILIO_WEBHOOK_SECRET", None) or "").strip()
        or (getattr(settings, "AGENT_SERVICE_SECRET", None) or "").strip()
    )


def _token_ok(request) -> bool:
    expected = _webhook_token()
    if not expected:
        return False
    provided = (
        request.query_params.get("token")
        or request.META.get("HTTP_X_AGENT_SECRET")
        or ""
    )
    return bool(provided) and hmac.compare_digest(provided, expected)


def _public_base() -> str:
    base = (getattr(settings, "TWILIO_WEBHOOK_BASE_URL", None) or "").rstrip("/")
    if not base:
        base = (getattr(settings, "SHOPIFY_APP_URL", None) or "").rstrip("/")
    return base


def _twiml(body: str) -> HttpResponse:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'
    return HttpResponse(xml, content_type="text/xml")


def _say_gather(say_text: str, gather_action: str, *, finish: bool = False) -> HttpResponse:
    safe = escape(say_text)
    if finish:
        return _twiml(f"<Say>{safe}</Say><Hangup/>")
    action = escape(gather_action)
    return _twiml(
        f"<Say>{safe}</Say>"
        f'<Gather input="speech" speechTimeout="auto" timeout="6" action="{action}" method="POST">'
        f"</Gather>"
        f"<Say>I did not catch that. Goodbye.</Say><Hangup/>"
    )


def _agent_unavailable() -> HttpResponse:
    return _say_gather(
        "Sorry, our negotiation agent is unavailable right now. Please try again later. Goodbye.",
        "",
        finish=True,
    )


def _append_message(n: Negotiation, role: str, body: str) -> None:
    body = (body or "").strip()
    if not body or role not in ("agent", "supplier", "system"):
        return
    last = (
        Message.objects.filter(negotiation_id=n.id).order_by("-created_at").first()
    )
    if last and last.role == role and last.body == body:
        return
    now = timezone.now()
    Message.objects.create(
        user_id=n.user_id,
        negotiation_id=n.id,
        role=role,
        body=body,
        created_at=now,
    )
    n.updated_at = now
    n.save(update_fields=["updated_at"])


def _agent_turn(
    n: Negotiation,
    *,
    speech: str | None = None,
    round_no: int = 1,
    is_opening: bool = False,
) -> dict | None:
    """Ask the agent LLM for the next spoken line."""
    agent_url = (getattr(settings, "AGENT_SERVICE_URL", None) or "").rstrip("/")
    agent_secret = (getattr(settings, "AGENT_SERVICE_SECRET", None) or "").strip()
    if not agent_url or not agent_secret:
        return None
    try:
        response = requests.post(
            f"{agent_url}/turns/next",
            json={
                "negotiationId": str(n.id),
                "speech": speech,
                "round": round_no,
                "isOpening": is_opening,
            },
            headers={
                "Content-Type": "application/json",
                "X-Agent-Secret": agent_secret,
            },
            timeout=28,
        )
    except requests.RequestException:
        return None
    if not response.ok:
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    say = str(body.get("say") or "").strip()
    if not say:
        return None
    return body


def _apply_llm_turn(
    n: Negotiation,
    turn: dict,
    *,
    round_no: int,
    base: str,
    token: str,
) -> HttpResponse:
    say = str(turn.get("say") or "").strip()
    action = str(turn.get("action") or "listen").strip().lower()
    stage = str(turn.get("stage") or "").strip()
    heard = turn.get("heardPrice")
    agreed = turn.get("agreedPrice")

    if heard is not None and n.original_quote is None:
        try:
            n.original_quote = Decimal(str(heard))
            n.save(update_fields=["original_quote"])
        except Exception:  # noqa: BLE001
            pass

    _append_message(n, "agent", say)

    if action == "accept" and agreed is not None:
        try:
            price = Decimal(str(agreed))
        except Exception:  # noqa: BLE001
            price = None
        if price is not None:
            _complete_deal(n, price)
            return _say_gather(say, "", finish=True)

    if action == "end":
        n.status = "waiting"
        n.stage = stage or "Call ended"
        n.progress = max(n.progress or 0, 80)
        n.updated_at = timezone.now()
        n.save(update_fields=["status", "stage", "progress", "updated_at"])
        return _say_gather(say, "", finish=True)

    if agreed is not None:
        try:
            n.current_offer = Decimal(str(agreed))
        except Exception:  # noqa: BLE001
            pass
    n.stage = stage or "On a call"
    n.progress = max(n.progress or 0, 55)
    n.updated_at = timezone.now()
    fields = ["stage", "progress", "updated_at"]
    if n.current_offer is not None:
        fields.append("current_offer")
    n.save(update_fields=fields)
    next_round = round_no + 1
    gather = f"{base}/api/twilio/gather/{n.id}/?token={token}&round={next_round}"
    return _say_gather(say, gather)


def place_twilio_call(*, negotiation: Negotiation, to_number: str) -> str:
    sid = (getattr(settings, "TWILIO_ACCOUNT_SID", None) or "").strip()
    token = (getattr(settings, "TWILIO_AUTH_TOKEN", None) or "").strip()
    from_number = (getattr(settings, "TWILIO_FROM_NUMBER", None) or "").strip()
    base = _public_base()
    webhook_secret = _webhook_token()

    if not sid or not token or not from_number:
        raise RuntimeError(
            "Twilio is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
            "and TWILIO_FROM_NUMBER."
        )
    if not base or "localhost" in base or "127.0.0.1" in base:
        raise RuntimeError(
            "TWILIO_WEBHOOK_BASE_URL must be a public HTTPS origin (ngrok or your "
            "deployed API). Twilio cannot reach localhost."
        )
    if not to_number.startswith("+"):
        raise RuntimeError("Supplier phone must be E.164 (example: +14155551234).")

    nid = str(negotiation.id)
    voice_url = (
        f"{base}/api/twilio/voice/{nid}/"
        f"?token={quote(webhook_secret, safe='')}"
    )
    status_url = (
        f"{base}/api/twilio/status/{nid}/"
        f"?token={quote(webhook_secret, safe='')}"
    )

    response = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
        auth=(sid, token),
        data={
            "To": to_number,
            "From": from_number,
            "Url": voice_url,
            "Method": "POST",
            "StatusCallback": status_url,
            "StatusCallbackMethod": "POST",
            "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
        },
        timeout=30,
    )
    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("message") or detail
        except ValueError:
            pass
        raise RuntimeError(f"Twilio call failed: {detail}")

    return str(response.json().get("sid") or "")


class InternalTwilioCallView(APIView):
    """Agent asks Django to place the outbound Twilio call."""

    authentication_classes: list = []
    permission_classes = [IsAgentService]

    def post(self, request, negotiation_id):
        try:
            n = Negotiation.objects.get(id=negotiation_id)
        except Negotiation.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        supplier = (
            Supplier.objects.filter(id=n.supplier_id).first() if n.supplier_id else None
        )
        phone = (supplier.phone if supplier else "") or ""
        phone = phone.replace(" ", "")
        try:
            call_sid = place_twilio_call(negotiation=n, to_number=phone)
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        now = timezone.now()
        _append_message(n, "system", f"Calling {phone} via Twilio (call {call_sid}).")
        n.status = "negotiating"
        n.stage = "Ringing"
        n.progress = 25
        n.updated_at = now
        n.save(update_fields=["status", "stage", "progress", "updated_at"])
        Activity.objects.create(
            user_id=n.user_id,
            kind="handshake",
            text=f"Outbound Twilio call started to {supplier.name if supplier else phone}.",
            created_at=now,
        )
        return Response({"ok": True, "callId": call_sid, "stage": "Ringing"})


class TwilioVoiceView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, negotiation_id):
        if not _token_ok(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            n = Negotiation.objects.get(id=negotiation_id)
        except (Negotiation.DoesNotExist, ValueError):
            return _twiml("<Say>Sorry, this negotiation was not found.</Say><Hangup/>")

        n.status = "negotiating"
        n.stage = "On a call"
        n.progress = max(n.progress or 0, 50)
        n.updated_at = timezone.now()
        n.save(update_fields=["status", "stage", "progress", "updated_at"])

        base = _public_base()
        token = quote(_webhook_token(), safe="")
        turn = _agent_turn(n, is_opening=True, round_no=1)
        if not turn:
            _append_message(
                n,
                "system",
                "Agent LLM unavailable for opening turn (check OPENAI_API_KEY / agent service).",
            )
            return _agent_unavailable()
        return _apply_llm_turn(n, turn, round_no=1, base=base, token=token)


class TwilioGatherView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, negotiation_id):
        if not _token_ok(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            n = Negotiation.objects.get(id=negotiation_id)
        except (Negotiation.DoesNotExist, ValueError):
            return _twiml("<Say>Goodbye.</Say><Hangup/>")

        speech = (
            request.data.get("SpeechResult")
            or request.POST.get("SpeechResult")
            or ""
        ).strip()
        round_no = int(request.query_params.get("round") or 1)
        base = _public_base()
        token = quote(_webhook_token(), safe="")

        if speech:
            _append_message(n, "supplier", speech)

        if round_no >= 6:
            turn = _agent_turn(
                n,
                speech=speech or "We should wrap up.",
                round_no=round_no,
                is_opening=False,
            )
            if turn:
                turn = {**turn, "action": "end"}
                return _apply_llm_turn(n, turn, round_no=round_no, base=base, token=token)
            _append_message(n, "system", "Call ended after max turns.")
            n.status = "waiting"
            n.stage = "Call ended"
            n.progress = 80
            n.updated_at = timezone.now()
            n.save(update_fields=["status", "stage", "progress", "updated_at"])
            return _agent_unavailable()

        turn = _agent_turn(n, speech=speech, round_no=round_no, is_opening=False)
        if not turn:
            _append_message(
                n,
                "system",
                "Agent LLM unavailable mid-call (check OPENAI_API_KEY / agent service).",
            )
            return _agent_unavailable()
        return _apply_llm_turn(n, turn, round_no=round_no, base=base, token=token)


class TwilioStatusView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request, negotiation_id):
        if not _token_ok(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            n = Negotiation.objects.get(id=negotiation_id)
        except (Negotiation.DoesNotExist, ValueError):
            return Response({"ok": True})

        if n.status == "completed":
            return Response({"ok": True})

        call_status = (
            request.data.get("CallStatus") or request.POST.get("CallStatus") or ""
        ).lower()
        mapping = {
            "queued": ("negotiating", "Queued", 15),
            "ringing": ("negotiating", "Ringing", 25),
            "in-progress": ("negotiating", "On a call", 50),
            "answered": ("negotiating", "On a call", 50),
            "completed": None,
            "busy": ("waiting", "No answer", 0),
            "no-answer": ("waiting", "No answer", 0),
            "failed": ("waiting", "Call failed", 0),
            "canceled": ("waiting", "Call ended", 0),
        }
        if call_status == "completed":
            if n.status != "completed":
                n.status = "waiting"
                n.stage = "Call ended"
                n.progress = max(n.progress or 0, 80)
                n.updated_at = timezone.now()
                n.save(update_fields=["status", "stage", "progress", "updated_at"])
            return Response({"ok": True})

        mapped = mapping.get(call_status)
        if not mapped:
            return Response({"ok": True})
        status_value, stage, progress = mapped
        n.status = status_value
        n.stage = stage
        n.progress = max(n.progress or 0, progress)
        n.updated_at = timezone.now()
        n.save(update_fields=["status", "stage", "progress", "updated_at"])
        if stage in ("No answer", "Call failed"):
            _append_message(n, "system", f"Twilio call status: {call_status}.")
        return Response({"ok": True})


def _complete_deal(n: Negotiation, unit_price: Decimal) -> None:
    now = timezone.now()
    Quote.objects.create(
        user_id=n.user_id,
        negotiation_id=n.id,
        supplier_id=n.supplier_id,
        unit_price=unit_price,
        currency=n.currency or "USD",
        moq=1,
        lead_time_days=14,
        is_selected=True,
        created_at=now,
    )
    n.current_offer = unit_price
    if n.original_quote and n.original_quote > 0 and unit_price < n.original_quote:
        n.savings_pct = (
            (n.original_quote - unit_price) / n.original_quote * Decimal(100)
        ).quantize(Decimal("0.1"))
    n.status = "completed"
    n.stage = "Completed (call)"
    n.progress = 100
    n.updated_at = now
    n.save(
        update_fields=[
            "current_offer",
            "savings_pct",
            "status",
            "stage",
            "progress",
            "updated_at",
        ]
    )
    if n.alert_id:
        InventoryAlert.objects.filter(id=n.alert_id).update(
            status="resolved", updated_at=now
        )
    Activity.objects.create(
        user_id=n.user_id,
        kind="handshake",
        text="Voice negotiation completed via Twilio.",
        created_at=now,
    )
