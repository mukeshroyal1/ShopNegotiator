-- Run in Supabase SQL Editor (once) — Shopify store connections

create table if not exists public.shopify_shops (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  shop_domain text not null,
  access_token text not null,
  scope text not null default '',
  is_active boolean not null default true,
  installed_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint shopify_shops_user_id_unique unique (user_id),
  constraint shopify_shops_shop_domain_unique unique (shop_domain)
);

create index if not exists shopify_shops_user_id_idx on public.shopify_shops (user_id);

drop trigger if exists shopify_shops_set_updated_at on public.shopify_shops;
create trigger shopify_shops_set_updated_at
  before update on public.shopify_shops
  for each row execute function public.set_updated_at();

alter table public.shopify_shops enable row level security;

drop policy if exists "shopify_shops_select_own" on public.shopify_shops;
create policy "shopify_shops_select_own" on public.shopify_shops
  for select using (auth.uid() = user_id);

-- Inserts/updates go through the Django backend (service role / DB user), not the anon key.
drop policy if exists "shopify_shops_no_client_writes" on public.shopify_shops;
-- No insert/update/delete policies for authenticated clients — backend only.
