from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.django_client import DjangoClient
from app.graph import NegotiationState, load_context


def initiate_call(state: NegotiationState) -> dict[str, Any]:
    client = DjangoClient()
    nid = state["negotiation_id"]
    if state.get("error"):
        return {}

    phone = (state["supplier"].get("phone") or "").replace(" ", "")
    try:
        result = client.start_twilio_call(nid)
    except Exception as exc:  # noqa: BLE001
        detail = str(exc)
        client.add_message(nid, "system", detail)
        client.patch_negotiation(
            nid,
            {
                "status": "waiting",
                "stage": "Call failed",
                "progress": 0,
                "activity": f"Voice call failed: {detail}",
            },
        )
        return {"error": detail, "outcome": "failed", "stage": "Call failed"}

    call_id = result.get("callId") or ""
    return {
        "outcome": "pending",
        "stage": result.get("stage") or "Ringing",
        "call_id": call_id,
        "error": None,
    }


def build_call_graph():
    graph = StateGraph(NegotiationState)
    graph.add_node("load_context", load_context)
    graph.add_node("initiate_call", initiate_call)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "initiate_call")
    graph.add_edge("initiate_call", END)
    return graph.compile()


call_graph = build_call_graph()
