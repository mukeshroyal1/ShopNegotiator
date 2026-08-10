# ShopNegotiator Django API

## 1. Apply the Postgres schema (Supabase)

1. Open Supabase → SQL Editor
2. Paste and run `db/schema.sql`
3. This creates per-user tables + Row Level Security

## 2. Configure env

```bash
cp .env.example .env
```

Fill in:

- `DATABASE_URL` — Supabase → Project Settings → Database → URI
- `SUPABASE_JWT_SECRET` — Project Settings → API → JWT Secret
- `SUPABASE_URL` — your project URL

## 3. Run the API

```bash
source .venv/bin/activate
python manage.py runserver 8000
```

Auth: send the Supabase access token:

```
Authorization: Bearer <access_token>
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health/` | Public health check |
| GET | `/api/dashboard/` | Stats + negotiations + activities |
| GET | `/api/negotiations/` | Negotiation list |
| GET | `/api/negotiations/:id/` | Detail + messages + quotes |
| GET | `/api/products/` | User products |
| GET | `/api/suppliers/` | User suppliers |
| GET | `/api/purchase-orders/` | User POs |
