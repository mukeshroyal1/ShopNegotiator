# Bargain Labs (ShopNego)

AI procurement workspace: connect Shopify, sync inventory, negotiate supplier quotes.

## Architecture

| Piece | Host | Why |
|-------|------|-----|
| **Frontend** (`frontend/`) | **Vercel** | Vite + React static app |
| **API** (`backend/`) | **Render** (or Railway) | Django must be publicly reachable for **Shopify OAuth + webhooks** |

Shopify cannot send webhooks to `localhost`. The webhook endpoint is:

`POST https://<YOUR_API_HOST>/api/shopify/webhooks/`

## 1. Push & GitHub

Already intended to live in this repo. Clone after create:

```bash
git clone https://github.com/<you>/BargainLabs.git
```

## 2. Deploy API on Render (webhooks)

1. [Render](https://render.com) → New → Blueprint → select this repo (`render.yaml`).
2. Set env vars (see `backend/.env.example`):

| Variable | Example |
|----------|---------|
| `DJANGO_ALLOWED_HOSTS` | `bargainlabs-api.onrender.com` |
| `DATABASE_URL` | Supabase **Session pooler** URI (`aws-1-…` if that’s your cluster) |
| `SUPABASE_URL` / `SUPABASE_JWT_SECRET` | From Supabase project settings |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
| `FRONTEND_URL` | `https://your-app.vercel.app` |
| `SHOPIFY_API_KEY` / `SHOPIFY_API_SECRET` | Shopify Partner app |
| `SHOPIFY_APP_URL` | `https://bargainlabs-api.onrender.com` |
| `SHOPIFY_REDIRECT_URI` | `https://bargainlabs-api.onrender.com/api/shopify/callback/` |

3. In **Shopify Partner → App → URLs**:
   - App URL: your Vercel URL
   - Allowed redirection URL(s): the `SHOPIFY_REDIRECT_URI` above

4. After the API is live, **Reconnect Shopify** in Settings once so webhooks register (`products/*`, `inventory_levels/update`).

## 3. Deploy frontend on Vercel

1. [Vercel](https://vercel.com) → Import this GitHub repo.
2. **Root Directory:** `frontend`
3. Framework: Vite (uses `frontend/vercel.json`)
4. Environment variables:

| Variable | Value |
|----------|-------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |
| `VITE_API_BASE` | `https://bargainlabs-api.onrender.com/api` |

## Local development

```bash
# API
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill values
python manage.py runserver 8000

# Web
cd frontend && npm install && npm run dev
```

For **local** webhooks, run [ngrok](https://ngrok.com) against port 8000 and set `SHOPIFY_APP_URL` + `SHOPIFY_REDIRECT_URI` to the ngrok HTTPS origin, then reconnect the shop.

## License

Private / all rights reserved unless otherwise noted.
