# Bargain Labs — fair-price ML (Milestone 4)

Synthetic **blank hoodie** wholesale quotes + a local FastAPI `/predict` service.

## What to copy from SageMaker Studio

From your Studio notebook / file browser, download these into **`ml/model/`** on your Mac:

| File | Required | Where it came from |
|------|----------|-------------------|
| `model.joblib` | **Yes** | Saved by local training cell (`joblib.dump(model, "model/model.joblib")`) |
| `feature_columns.json` | **Yes** | Same training cell / `processed/feature_columns.json` |
| `model.tar.gz` | Optional | Packed archive; extract if you only have this |

Final layout:

```text
ml/model/
  model.joblib
  feature_columns.json
```

If you only have `model.tar.gz`:

```bash
cd ml/model
tar -xzf model.tar.gz
# ensure model.joblib + feature_columns.json are directly under ml/model/
```

You can also download from S3 if you uploaded them:

`s3://argainlabs-ml-mukesh/hoodie-fair-price/model/model.tar.gz`

## Run the API

On macOS, XGBoost needs OpenMP once:

```bash
brew install libomp
```

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

Check:

```bash
curl http://127.0.0.1:8090/health
```

Expect `"modelReady": true` once the two files are in `ml/model/`.

Predict:

```bash
curl -s http://127.0.0.1:8090/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "quantity": 200,
    "moq": 50,
    "weightOz": 8.5,
    "leadTimeDays": 14,
    "daysSinceLastBuy": 60,
    "lastUnitPrice": 16.0,
    "supplierAsk": 19.5,
    "skuTier": "mid",
    "supplierTier": "standard",
    "region": "US"
  }'
```

## Wire to the voice agent

In `agent/.env`:

```text
ML_SERVICE_URL=http://127.0.0.1:8090
```

Restart the agent. Each turn will call `/predict` and inject the fair price into the LLM brief.

## Data

| File | Description |
|------|-------------|
| `data/hoodie_quotes.csv` | 10,000 synthetic quote/fill rows |
| `generate_hoodie_data.py` | Regenerates the CSV |

```bash
python3 generate_hoodie_data.py
```
