from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.graph import agent_graph
from app.graph_voice import call_graph
from app.llm import LlmError
from app.turn import next_turn

app = FastAPI(title="Bargain Labs agent", version="0.4.0")


class StartRunRequest(BaseModel):
    negotiation_id: str = Field(alias="negotiationId")

    model_config = {"populate_by_name": True}


class TurnRequest(BaseModel):
    negotiation_id: str = Field(alias="negotiationId")
    speech: str | None = None
    round: int = 1
    is_opening: bool = Field(default=False, alias="isOpening")

    model_config = {"populate_by_name": True}


def _check_secret(x_agent_secret: str | None) -> None:
    if not x_agent_secret or x_agent_secret != settings.agent_service_secret:
        raise HTTPException(status_code=401, detail="Invalid agent secret")


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "bargainlabs-agent",
        "voice": "twilio",
        "llmConfigured": bool((settings.openai_api_key or "").strip()),
        "model": settings.openai_model,
    }


@app.post("/runs/start")
def start_run(
    payload: StartRunRequest,
    x_agent_secret: str | None = Header(default=None),
) -> dict:
    _check_secret(x_agent_secret)
    result = agent_graph.invoke({"negotiation_id": payload.negotiation_id})
    return {
        "ok": result.get("outcome") != "failed",
        "outcome": result.get("outcome"),
        "stage": result.get("stage"),
        "error": result.get("error"),
    }


@app.post("/runs/call")
def start_call(
    payload: StartRunRequest,
    x_agent_secret: str | None = Header(default=None),
) -> dict:
    _check_secret(x_agent_secret)
    result = call_graph.invoke({"negotiation_id": payload.negotiation_id})
    error = result.get("error")
    if error:
        raise HTTPException(status_code=502, detail=str(error))
    return {
        "ok": True,
        "outcome": result.get("outcome"),
        "stage": result.get("stage"),
        "callId": result.get("call_id"),
    }


@app.post("/turns/next")
def turns_next(
    payload: TurnRequest,
    x_agent_secret: str | None = Header(default=None),
) -> dict:
    _check_secret(x_agent_secret)
    try:
        result = next_turn(
            payload.negotiation_id,
            speech=payload.speech,
            round_no=payload.round,
            is_opening=payload.is_opening,
        )
    except LlmError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, **result}
