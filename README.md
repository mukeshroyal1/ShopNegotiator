# Bargain Labs (ShopNego)

AI procurement: Shopify inventory → low-stock alerts → supplier phone negotiation
(Twilio + LLM agent) with an optional ML fair-price model.

## Architecture

| Piece | Path | Local port |
|-------|------|------------|
| Frontend | `frontend/` | 5173 |
| Django API | `backend/` | 8000 |
| LangGraph agent | `agent/` | 8080 |
| Fair-price ML API | `ml/` | 8090 |

Shopify webhooks need a public HTTPS API URL (ngrok locally, or your deployed host).

## Local development

```bash
# API
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver 8000

# Agent (needs OPENAI_API_KEY)
cd agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080

# Fair-price ML (put model.joblib + feature_columns.json in ml/model/)
cd ml && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# macOS: brew install libomp
uvicorn app.main:app --reload --port 8090

# Web
cd frontend && npm install && npm run dev
```

For local Twilio voice + Shopify webhooks, run `ngrok http 8000` and set
`TWILIO_WEBHOOK_BASE_URL` / `SHOPIFY_APP_URL` to the ngrok HTTPS origin.

See `agent/README.md`, `ml/README.md`, and `backend/README.md` for env details.

## Deploy

Frontend + Django can deploy together via root `vercel.json` (Vercel Services).
Agent and ML stay local (or your own host) until you deploy them separately.

## License

Private / all rights reserved unless otherwise noted.
