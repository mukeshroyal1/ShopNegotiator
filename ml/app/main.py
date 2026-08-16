from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.predict import ModelNotReady, artifacts_ready, predict_fair_price

app = FastAPI(title="Bargain Labs fair-price ML", version="0.1.0")


class PredictRequest(BaseModel):
    quantity: float = Field(..., gt=0)
    moq: float = Field(1, gt=0)
    weight_oz: float = Field(8.5, alias="weightOz", gt=0)
    lead_time_days: float = Field(14, alias="leadTimeDays", ge=0)
    days_since_last_buy: float = Field(60, alias="daysSinceLastBuy", ge=0)
    last_unit_price: float = Field(..., alias="lastUnitPrice", gt=0)
    supplier_ask: float = Field(..., alias="supplierAsk", gt=0)
    sku_tier: Literal["basic", "mid", "premium"] = Field("mid", alias="skuTier")
    supplier_tier: Literal["budget", "standard", "premium"] = Field(
        "standard", alias="supplierTier"
    )
    region: Literal["US", "CN", "MX"] = Field("US")
    currency: str = "USD"

    model_config = {"populate_by_name": True}


@app.get("/health")
def health() -> dict:
    ready = artifacts_ready()
    return {
        "ok": True,
        "service": "bargainlabs-fair-price",
        "modelReady": ready,
    }


@app.post("/predict")
def predict(body: PredictRequest) -> dict:
    try:
        return predict_fair_price(body.model_dump(by_alias=True))
    except ModelNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
