# ShopNegotiator Frontend

React + TypeScript + Vite + Tailwind + Supabase Auth.

## Setup

```bash
cp .env.example .env
# Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY from Supabase → Project Settings → API
npm install
npm run dev
```

> This app is a Vite SPA, not Next.js. Use `VITE_` env vars (not `NEXT_PUBLIC_`).  
> Skip Next.js-only files from the Supabase wizard (`middleware.ts`, `utils/supabase/server.ts`).

## Routes

- `/` — marketing homepage
- `/signin`, `/signup` — Supabase auth
- `/app/*` — protected webapp (requires session)
