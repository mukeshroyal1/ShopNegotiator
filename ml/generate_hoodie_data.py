"""Generate synthetic blank-hoodie wholesale quotes for the fair-price model.

Uses only the Python standard library so it runs without a venv.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "hoodie_quotes.csv"
N = 10_000
SEED = 42

TIER_BASE = {"basic": 14.0, "mid": 22.0, "premium": 32.0}
SUPPLIER_MULT = {"budget": 0.90, "standard": 1.00, "premium": 1.12}
WEIGHT_OZ = {"basic": 7.0, "mid": 8.5, "premium": 10.0}

COLUMNS = [
    "category",
    "sku_tier",
    "weight_oz",
    "supplier_tier",
    "region",
    "quantity",
    "moq",
    "lead_time_days",
    "days_since_last_buy",
    "last_unit_price",
    "supplier_ask",
    "fair_unit_price",
]


def _choice(rng: random.Random, options: list[str], weights: list[float]) -> str:
    return rng.choices(options, weights=weights, k=1)[0]


def generate(n: int = N, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []

    for _ in range(n):
        sku_tier = _choice(rng, ["basic", "mid", "premium"], [0.45, 0.40, 0.15])
        supplier_tier = _choice(
            rng, ["budget", "standard", "premium"], [0.30, 0.50, 0.20]
        )
        quantity = rng.randint(25, 2000)
        moq = max(12, min(200, int(quantity * rng.uniform(0.05, 0.25))))
        lead_time_days = rng.randint(7, 45)
        days_since_last_buy = rng.randint(14, 365)
        region = _choice(rng, ["US", "CN", "MX"], [0.35, 0.50, 0.15])

        base = TIER_BASE[sku_tier]
        supp = SUPPLIER_MULT[supplier_tier]
        weight = WEIGHT_OZ[sku_tier]

        qty_discount = 1.0 - min(0.18, math.log1p(quantity) / 55.0)
        region_mult = 0.92 if region == "CN" else (0.96 if region == "MX" else 1.05)
        lead_mult = 1.0 + (lead_time_days - 21) * 0.001

        fair = base * supp * qty_discount * region_mult * lead_mult
        fair += rng.gauss(0, 0.04 * fair)
        fair = round(min(55.0, max(8.0, fair)), 2)

        last_unit_price = round(fair * rng.uniform(0.95, 1.08), 2)
        supplier_ask = round(fair * rng.uniform(1.05, 1.28), 2)

        rows.append(
            {
                "category": "hoodie",
                "sku_tier": sku_tier,
                "weight_oz": weight,
                "supplier_tier": supplier_tier,
                "region": region,
                "quantity": quantity,
                "moq": moq,
                "lead_time_days": lead_time_days,
                "days_since_last_buy": days_since_last_buy,
                "last_unit_price": last_unit_price,
                "supplier_ask": supplier_ask,
                "fair_unit_price": fair,
            }
        )

    return rows


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = generate()
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    fairs = [r["fair_unit_price"] for r in rows]
    print(f"Wrote {OUT} ({len(rows)} rows)")
    print("Sample:")
    for row in rows[:5]:
        print(
            f"  {row['sku_tier']:7} qty={row['quantity']:4} "
            f"last={row['last_unit_price']:6.2f} ask={row['supplier_ask']:6.2f} "
            f"fair={row['fair_unit_price']:6.2f}"
        )
    print(
        f"fair_unit_price: min={min(fairs):.2f} "
        f"mean={statistics.mean(fairs):.2f} max={max(fairs):.2f}"
    )


if __name__ == "__main__":
    main()
