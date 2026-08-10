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

## 3. Deploy on Vercel (frontend + API together)

Vercel **Services** can host both apps on one project/domain.

1. Ensure root `vercel.json` is present (defines `frontend` + `backend` services).
2. Import the GitHub repo → Application Preset: **Services** → Root Directory: `./`
3. Click **Refresh** after the file is on `main`, then **Deploy**.
4. Set env vars (see below). Use your Vercel URL, e.g. `https://bargain-labs.vercel.app`:

**Frontend**

| Variable | Value |
|----------|-------|
| `VITE_SUPABASE_URL` | Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |
| `VITE_API_BASE` | `https://bargain-labs.vercel.app/api` |

**Backend**

| Variable | Value |
|----------|-------|
| `DJANGO_SECRET_KEY` | Generated secret |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `bargain-labs.vercel.app,.vercel.app` |
| `DATABASE_URL` | Supabase session pooler URI |
| `SUPABASE_URL` / `SUPABASE_JWT_SECRET` | From Supabase |
| `CORS_ALLOWED_ORIGINS` | `https://bargain-labs.vercel.app` |
| `FRONTEND_URL` | `https://bargain-labs.vercel.app` |
| `SHOPIFY_API_KEY` / `SHOPIFY_API_SECRET` | Partner app |
| `SHOPIFY_SCOPES` | (same as `.env.example`) |
| `SHOPIFY_APP_URL` | `https://bargain-labs.vercel.app` |
| `SHOPIFY_REDIRECT_URI` | `https://bargain-labs.vercel.app/api/shopify/callback/` |

5. Shopify Partner app → App URL + Allowed redirection URL = those values.
6. After deploy, **Reconnect Shopify** in Settings so webhooks register.

### Alternative: frontend on Vercel, API on Render

Use `render.yaml` if you prefer a dedicated always-on API. See older notes in git history / Render dashboard.

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
