from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.django_client import DjangoClient
from app.llm import LlmError, chat_json
from app.prompts import SUPPLIER_SIM_PROMPT
from app.turn import next_turn


class NegotiationState(TypedDict, total=False):
    negotiation_id: str
    user_id: str
    product: dict[str, Any]
    supplier: dict[str, Any]
    currency: str
    reorder_qty: int
    original_ask: float | None
    supplier_quote: float | None
    agent_offer: float | None
    round: int
    stage: str
    outcome: Literal["pending", "accepted", "failed"]
    error: str | None


def _money(value: float, currency: str) -> str:
    return f"{currency} {value:.2f}"


def load_context(state: NegotiationState) -> dict[str, Any]:
    client = DjangoClient()
    ctx = client.get_context(state["negotiation_id"])
    product = ctx.get("product") or {}
    supplier = ctx.get("supplier") or {}
    if not product or not supplier:
        return {
            "error": "Negotiation is missing product or supplier context.",
            "outcome": "failed",
            "stage": "Failed",
        }

    client.patch_negotiation(
        state["negotiation_id"],
        {"status": "negotiating", "stage": "Opening", "progress": 20},
    )
    return {
        "user_id": ctx["userId"],
        "product": product,
        "supplier": supplier,
        "currency": ctx.get("currency") or supplier.get("currency") or "USD",
        "reorder_qty": int(product.get("reorderQty") or supplier.get("defaultMoq") or 1),
        "round": 0,
        "outcome": "pending",
        "stage": "Opening",
        "error": None,
    }


def _simulate_supplier(nid: str, context: dict[str, Any]) -> tuple[str, float | None]:
    product = context.get("product") or {}
    supplier = context.get("supplier") or {}
    currency = context.get("currency") or supplier.get("currency") or "USD"
    history = "\n".join(
        f"{'Buyer' if m.get('role') == 'agent' else 'You'}: {m.get('body')}"
        for m in (context.get("messages") or [])
        if m.get("role") in ("agent", "supplier")
    ) or "(call just started)"
    last = supplier.get("lastUnitPrice")
    user = f"""CONTEXT
- Your company: {supplier.get('name') or 'Supplier'}
- Product: {product.get('name') or 'item'} (SKU {product.get('sku') or 'n/a'})
- Buyer wants ~{product.get('reorderQty') or 1} units
- Currency: {currency}
- Your last fill to them: {last if last is not None else 'unknown'}
- Default MOQ: {supplier.get('defaultMoq') or 1}

TRANSCRIPT
{history}

Reply as the supplier on the phone.
"""
    raw = chat_json(system=SUPPLIER_SIM_PROMPT, user=user)
    say = str(raw.get("say") or "").strip()
    if not say:
        raise LlmError("Supplier sim returned empty say")
    quoted = raw.get("quotedPrice")
    try:
        price = float(quoted) if quoted is not None else None
    except (TypeError, ValueError):
        price = None
    return say, price


def run_llm_dry_run(state: NegotiationState) -> dict[str, Any]:
    client = DjangoClient()
    nid = state["negotiation_id"]
    if state.get("error"):
        return {"outcome": "failed"}

    try:
        opening = next_turn(nid, is_opening=True, round_no=1)
        client.add_message(nid, "agent", opening["say"])
        client.patch_negotiation(
            nid,
            {"stage": opening.get("stage") or "Waiting for quote", "progress": 40},
        )

        original_ask: float | None = None
        agent_offer: float | None = None
        outcome: Literal["pending", "accepted", "failed"] = "pending"
        stage = opening.get("stage") or "On a call"
        currency = opening.get("currency") or state.get("currency") or "USD"

        for round_no in range(1, 5):
            ctx = client.get_context(nid)
            supplier_line, quoted = _simulate_supplier(nid, ctx)
            client.add_message(nid, "supplier", supplier_line)
            if quoted is not None and original_ask is None:
                original_ask = quoted
                client.patch_negotiation(nid, {"originalQuote": quoted})

            turn = next_turn(
                nid,
                speech=supplier_line,
                round_no=round_no,
                is_opening=False,
            )
            client.add_message(nid, "agent", turn["say"])
            stage = turn.get("stage") or stage
            action = turn.get("action") or "listen"
            heard = turn.get("heardPrice")
            agreed = turn.get("agreedPrice")
            if heard is not None and original_ask is None:
                original_ask = float(heard)
                client.patch_negotiation(nid, {"originalQuote": original_ask})

            if action == "accept" and agreed is not None:
                agent_offer = float(agreed)
                outcome = "accepted"
                client.patch_negotiation(
                    nid,
                    {
                        "stage": stage,
                        "progress": 90,
                        "currentOffer": agent_offer,
                    },
                )
                break

            if action == "end":
                outcome = "failed"
                client.patch_negotiation(
                    nid,
                    {"status": "waiting", "stage": stage or "Call ended", "progress": 80},
                )
                break

            if agreed is not None:
                agent_offer = float(agreed)
                client.patch_negotiation(
                    nid,
                    {
                        "stage": stage,
                        "progress": 55 + round_no * 10,
                        "currentOffer": agent_offer,
                    },
                )
            else:
                client.patch_negotiation(
                    nid,
                    {"stage": stage, "progress": 55 + round_no * 10},
                )
        else:
            outcome = "failed"
            stage = "Call ended"

        return {
            "original_ask": original_ask,
            "agent_offer": agent_offer,
            "supplier_quote": original_ask,
            "outcome": outcome if outcome != "pending" else "failed",
            "stage": stage,
            "currency": currency,
            "error": None,
        }
    except LlmError as exc:
        return {
            "error": str(exc),
            "outcome": "failed",
            "stage": "Failed",
        }


def finalize(state: NegotiationState) -> dict[str, Any]:
    client = DjangoClient()
    nid = state["negotiation_id"]
    if state.get("error") or state.get("outcome") == "failed":
        detail = state.get("error") or "Dry-run ended without a deal."
        client.add_message(nid, "system", detail)
        client.patch_negotiation(
            nid,
            {
                "status": "waiting" if not state.get("error") else "cancelled",
                "stage": state.get("stage") or "Failed",
                "progress": 0 if state.get("error") else 80,
                "activity": detail,
            },
        )
        return {"outcome": "failed"}

    price = float(state.get("agent_offer") or state.get("supplier_quote") or 0)
    if not price:
        client.add_message(nid, "system", "Dry-run finished with no agreed price.")
        client.patch_negotiation(
            nid,
            {"status": "waiting", "stage": "Call ended", "progress": 80},
        )
        return {"outcome": "failed", "stage": "Call ended"}

    original_ask = float(state.get("original_ask") or price)
    savings_pct = 0.0
    if price and original_ask and original_ask > price:
        savings_pct = round(((original_ask - price) / original_ask) * 100, 1)
    currency = state.get("currency") or "USD"
    client.add_quote(
        nid,
        unit_price=price,
        currency=currency,
        moq=int(state["supplier"].get("defaultMoq") or 1),
        lead_time_days=14,
    )
    product_name = state["product"].get("name") or "product"
    supplier_name = state["supplier"].get("name") or "supplier"
    client.add_message(
        nid,
        "system",
        f"Dry-run complete. Agreed {_money(price, currency)} with {supplier_name}.",
    )
    client.patch_negotiation(
        nid,
        {
            "status": "completed",
            "stage": "Completed (dry run)",
            "progress": 100,
            "currentOffer": price,
            "savingsPct": savings_pct,
            "resolveAlert": True,
            "activity": f"Dry-run negotiation completed for {product_name} with {supplier_name}.",
        },
    )
    return {"outcome": "accepted", "stage": "Completed (dry run)"}


def _route_after_load(state: NegotiationState) -> str:
    if state.get("error"):
        return "finalize"
    return "run_llm_dry_run"


def build_graph():
    graph = StateGraph(NegotiationState)
    graph.add_node("load_context", load_context)
    graph.add_node("run_llm_dry_run", run_llm_dry_run)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "load_context")
    graph.add_conditional_edges(
        "load_context",
        _route_after_load,
        {"run_llm_dry_run": "run_llm_dry_run", "finalize": "finalize"},
    )
    graph.add_edge("run_llm_dry_run", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


agent_graph = build_graph()
