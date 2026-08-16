# Bargain Labs negotiation agent

LangGraph service. Django is the system of record. Dialogue comes from OpenAI
(`agent/app/prompts.py`) — there is no scripted conversation fallback.

## Setup

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload --port 8080
```

`agent/.env`:

```
DJANGO_API_URL=http://127.0.0.1:8000/api
AGENT_SERVICE_SECRET=dev-agent-secret-change-me
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

`backend/.env` must include matching:

```
AGENT_SERVICE_URL=http://127.0.0.1:8080
AGENT_SERVICE_SECRET=dev-agent-secret-change-me
```

`GET http://127.0.0.1:8080/health` should show `"llmConfigured": true`.

## Dry-run (LLM simulation)

On a negotiation, click **Simulate with LLM**. The agent roleplays buyer + supplier
turns via OpenAI and writes the transcript + quote.

## Real Twilio call

1. Twilio credentials on **Django** (`TWILIO_*` in `backend/.env`).
2. `TWILIO_WEBHOOK_BASE_URL` = public HTTPS (ngrok → Django `:8000`).
3. Supplier phone E.164 (`+1…`). Trial accounts: verified numbers only.
4. **Call supplier** → Twilio → Django → `POST /turns/next` on the agent for each spoken line.

Edit persona/rules in `agent/app/prompts.py`.

## Fair-price ML (Milestone 4)

Run the local predictor:

```bash
cd ml
# put model.joblib + feature_columns.json in ml/model/ (from SageMaker Studio)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

In `agent/.env`:

```
ML_SERVICE_URL=http://127.0.0.1:8090
```
