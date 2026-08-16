from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
MODEL_PATH = MODEL_DIR / "model.joblib"
FEATURES_PATH = MODEL_DIR / "feature_columns.json"


class ModelNotReady(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_artifacts() -> tuple[Any, list[str]]:
    if not MODEL_PATH.exists() or not FEATURES_PATH.exists():
        raise ModelNotReady(
            f"Missing model files. Put model.joblib and feature_columns.json in {MODEL_DIR}"
        )
    model = joblib.load(MODEL_PATH)
    feature_columns = json.loads(FEATURES_PATH.read_text())
    if not isinstance(feature_columns, list) or not feature_columns:
        raise ModelNotReady("feature_columns.json must be a non-empty JSON list")
    return model, feature_columns


def artifacts_ready() -> bool:
    return MODEL_PATH.exists() and FEATURES_PATH.exists()


def build_feature_row(
    *,
    quantity: float,
    moq: float,
    weight_oz: float,
    lead_time_days: float,
    days_since_last_buy: float,
    last_unit_price: float,
    supplier_ask: float,
    sku_tier: str,
    supplier_tier: str,
    region: str,
    feature_columns: list[str],
) -> list[float]:
    raw = pd.DataFrame(
        [
            {
                "weight_oz": weight_oz,
                "quantity": quantity,
                "moq": moq,
                "lead_time_days": lead_time_days,
                "days_since_last_buy": days_since_last_buy,
                "last_unit_price": last_unit_price,
                "supplier_ask": supplier_ask,
                "sku_tier": sku_tier,
                "supplier_tier": supplier_tier,
                "region": region,
            }
        ]
    )
    raw = pd.get_dummies(
        raw, columns=["sku_tier", "supplier_tier", "region"], drop_first=True
    )
    raw = raw.reindex(columns=feature_columns, fill_value=0.0)
    return [float(x) for x in raw.iloc[0].tolist()]


def predict_fair_price(payload: dict[str, Any]) -> dict[str, Any]:
    model, feature_columns = load_artifacts()
    features = build_feature_row(
        quantity=float(payload["quantity"]),
        moq=float(payload["moq"]),
        weight_oz=float(payload["weightOz"]),
        lead_time_days=float(payload["leadTimeDays"]),
        days_since_last_buy=float(payload["daysSinceLastBuy"]),
        last_unit_price=float(payload["lastUnitPrice"]),
        supplier_ask=float(payload["supplierAsk"]),
        sku_tier=str(payload["skuTier"]),
        supplier_tier=str(payload["supplierTier"]),
        region=str(payload["region"]),
        feature_columns=feature_columns,
    )
    pred = float(model.predict([features])[0])
    # Simple uncertainty band for the agent brief
    low = round(pred * 0.97, 2)
    high = round(pred * 1.03, 2)
    return {
        "fairPrice": round(pred, 2),
        "low": low,
        "high": high,
        "currency": payload.get("currency") or "USD",
        "category": "hoodie",
    }
