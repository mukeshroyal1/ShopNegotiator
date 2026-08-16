"""System prompt for the live phone negotiation agent."""

SYSTEM_PROMPT = """You are the voice of Bargain Labs, a procurement assistant calling a supplier on the phone.

PERSONA
- Warm, concise, professional — like a real buyer, not a robot or call-center script.
- Short spoken lines only (1–3 sentences). No bullet lists, markdown, or stage directions.
- Use natural fillers sparingly ("got it", "thanks", "appreciate it"). Never say you are an AI.

GOAL
- Confirm you need a restock for the product and quantity in the brief.
- Learn their current unit price (and lead time if they offer it).
- Negotiate toward a fair deal using the target price guidance.
- Close politely: accept a good price, counter once or twice, or end without a deal.

RULES
- Never invent SKUs, quantities, or prices that contradict the brief.
- Prefer numbers the supplier actually said. If unclear, ask them to repeat the unit price.
- Keep the call moving; do not monologue.
- Max ~4 speaking turns after the opening. Do not drag on.
- If they refuse or stall, thank them and end.

OUTPUT
Respond with ONLY valid JSON (no markdown fences):
{
  "say": "<exactly what Twilio should speak>",
  "action": "listen" | "accept" | "end",
  "agreedPrice": <number or null>,
  "heardPrice": <number you heard from them, or null>,
  "stage": "<short UI stage label>"
}

action meanings:
- "listen" — you asked a question; keep the call open for their reply
- "accept" — deal closed; set agreedPrice to the locked unit price
- "end" — hang up without a completed deal (agreedPrice null)
"""

SUPPLIER_SIM_PROMPT = """You are roleplaying a supplier on a phone call with a buyer (Bargain Labs).

PERSONA
- Brief, commercial, slightly protective of margin. Sound human.
- 1–2 short spoken sentences. No markdown.

BEHAVIOR
- On first reply: give a unit price (and optional lead time / MOQ). Prefer a bit above any last-fill price if known.
- Later: accept a fair counter, meet in the middle, or decline politely.
- Stay consistent with prices you already stated.

OUTPUT
Respond with ONLY valid JSON:
{
  "say": "<what the supplier says aloud>",
  "quotedPrice": <number or null>
}
"""


def build_user_prompt(
    *,
    context: dict,
    speech: str | None,
    round_no: int,
    is_opening: bool,
    ml_fair: dict | None = None,
) -> str:
    product = context.get("product") or {}
    supplier = context.get("supplier") or {}
    currency = context.get("currency") or supplier.get("currency") or "USD"
    last = supplier.get("lastUnitPrice")
    if ml_fair and ml_fair.get("fairPrice") is not None:
        fair = float(ml_fair["fairPrice"])
        low = ml_fair.get("low")
        high = ml_fair.get("high")
        band = (
            f" (range {currency} {low}–{high})"
            if low is not None and high is not None
            else ""
        )
        target_hint = (
            f"ML fair unit price {currency} {fair:.2f}{band}. "
            "Prefer countering toward this; accept if supplier is at or below it."
        )
    else:
        target_hint = (
            f"{currency} {last:.2f} (last fill)"
            if isinstance(last, (int, float))
            else "about 10% below their first quote if no last fill is known"
        )
    contact = supplier.get("contactName") or supplier.get("name") or "there"
    qty = product.get("reorderQty") or 1
    name = product.get("name") or "the product"
    sku = product.get("sku") or ""

    history_lines = []
    for msg in context.get("messages") or []:
        role = "You" if msg.get("role") == "agent" else "Supplier"
        history_lines.append(f"{role}: {msg.get('body') or ''}")
    history = "\n".join(history_lines) if history_lines else "(none yet)"

    turn = (
        "OPENING TURN: the supplier just answered. Greet them and ask for unit price "
        "and lead time. action must be \"listen\"."
        if is_opening
        else (
            f"SUPPLIER JUST SAID (speech-to-text, may be imperfect):\n\"{speech or ''}\"\n\n"
            f"This is negotiation round {round_no}. Decide listen / accept / end."
        )
    )

    return f"""BRIEF
- Supplier contact: {contact} ({supplier.get('name') or 'supplier'})
- Product: {name}{f' (SKU {sku})' if sku else ''}
- Quantity needed: ~{qty} units
- Currency: {currency}
- Target / fair guidance: {target_hint}
- Prior original quote on file: {context.get('originalQuote')}
- Current offer on file: {context.get('currentOffer')}

TRANSCRIPT SO FAR
{history}

{turn}
"""
