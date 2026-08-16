from __future__ import annotations

from typing import Any

from app.django_client import DjangoClient
from app.llm import LlmError, chat_json
from app.ml_client import fetch_fair_price
from app.prompts import SYSTEM_PROMPT, build_user_prompt


def next_turn(
    negotiation_id: str,
    *,
    speech: str | None = None,
    round_no: int = 1,
    is_opening: bool = False,
) -> dict[str, Any]:
    client = DjangoClient()
    context = client.get_context(negotiation_id)
    # Prefer ML fair price when the service is up; use heard/original ask if present
    ask = _float_or_none(context.get("originalQuote"))
    ml_fair = fetch_fair_price(context, supplier_ask=ask)
    user_prompt = build_user_prompt(
        context=context,
        speech=speech,
        round_no=round_no,
        is_opening=is_opening,
        ml_fair=ml_fair,
    )
    try:
        raw = chat_json(system=SYSTEM_PROMPT, user=user_prompt)
    except LlmError:
        raise

    say = str(raw.get("say") or "").strip()
    if not say:
        raise LlmError("Model returned empty say text")

    action = str(raw.get("action") or "listen").strip().lower()
    if action not in ("listen", "accept", "end"):
        action = "listen"

    agreed = _float_or_none(raw.get("agreedPrice"))
    heard = _float_or_none(raw.get("heardPrice"))
    stage = str(raw.get("stage") or "").strip() or (
        "On a call"
        if action == "listen"
        else ("Completed (call)" if action == "accept" else "Call ended")
    )

    # Soft guardrails: opening must keep listening; accept needs a price.
    if is_opening:
        action = "listen"
        agreed = None
    if action == "accept" and agreed is None:
        agreed = heard or _float_or_none(context.get("currentOffer"))
        if agreed is None:
            action = "listen"
            if "price" not in say.lower():
                say = f"{say} What unit price can you do?"

    return {
        "say": say,
        "action": action,
        "agreedPrice": agreed,
        "heardPrice": heard,
        "stage": stage,
        "currency": context.get("currency")
        or (context.get("supplier") or {}).get("currency")
        or "USD",
    }


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
