-- ShopNegotiator schema for Supabase Postgres
-- Run in Supabase SQL Editor (once). All tenant data is scoped by user_id + RLS.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Profiles (1:1 with auth.users)
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  full_name text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Products
-- ---------------------------------------------------------------------------
create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  sku text not null default '',
  current_stock integer not null default 0,
  threshold integer not null default 0,
  shopify_product_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, sku)
);

create index if not exists products_user_id_idx on public.products (user_id);

-- ---------------------------------------------------------------------------
-- Suppliers
-- ---------------------------------------------------------------------------
create table if not exists public.suppliers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  email text,
  alibaba_listing_id text,
  notes text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists suppliers_user_id_idx on public.suppliers (user_id);

-- ---------------------------------------------------------------------------
-- Inventory alerts
-- ---------------------------------------------------------------------------
create table if not exists public.inventory_alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  product_id uuid not null references public.products (id) on delete cascade,
  current_stock integer not null,
  threshold integer not null,
  status text not null default 'open'
    check (status in ('open', 'searching', 'negotiating', 'resolved')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists inventory_alerts_user_id_idx on public.inventory_alerts (user_id);

-- ---------------------------------------------------------------------------
-- Negotiations
-- ---------------------------------------------------------------------------
create table if not exists public.negotiations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  product_id uuid references public.products (id) on delete set null,
  supplier_id uuid references public.suppliers (id) on delete set null,
  alert_id uuid references public.inventory_alerts (id) on delete set null,
  status text not null default 'negotiating'
    check (status in ('negotiating', 'waiting', 'completed', 'cancelled')),
  stage text not null default 'Opening',
  progress integer not null default 0 check (progress >= 0 and progress <= 100),
  original_quote numeric(12, 2),
  current_offer numeric(12, 2),
  currency text not null default 'USD',
  savings_pct numeric(6, 2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists negotiations_user_id_idx on public.negotiations (user_id);
create index if not exists negotiations_status_idx on public.negotiations (user_id, status);

-- ---------------------------------------------------------------------------
-- Messages
-- ---------------------------------------------------------------------------
create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  negotiation_id uuid not null references public.negotiations (id) on delete cascade,
  role text not null check (role in ('agent', 'supplier', 'system')),
  body text not null,
  created_at timestamptz not null default now()
);

create index if not exists messages_negotiation_id_idx on public.messages (negotiation_id);

-- ---------------------------------------------------------------------------
-- Quotes
-- ---------------------------------------------------------------------------
create table if not exists public.quotes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  negotiation_id uuid not null references public.negotiations (id) on delete cascade,
  supplier_id uuid references public.suppliers (id) on delete set null,
  unit_price numeric(12, 2) not null,
  currency text not null default 'USD',
  moq integer not null default 1,
  lead_time_days integer not null default 0,
  is_selected boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists quotes_negotiation_id_idx on public.quotes (negotiation_id);

-- ---------------------------------------------------------------------------
-- Purchase orders
-- ---------------------------------------------------------------------------
create table if not exists public.purchase_orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  quote_id uuid references public.quotes (id) on delete set null,
  negotiation_id uuid references public.negotiations (id) on delete set null,
  status text not null default 'draft'
    check (status in ('draft', 'approved', 'ordered', 'cancelled')),
  total_amount numeric(14, 2),
  currency text not null default 'USD',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists purchase_orders_user_id_idx on public.purchase_orders (user_id);

-- ---------------------------------------------------------------------------
-- Activity feed
-- ---------------------------------------------------------------------------
create table if not exists public.activities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  kind text not null default 'system',
  text text not null,
  created_at timestamptz not null default now()
);

create index if not exists activities_user_id_idx on public.activities (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Auto-create profile on signup
-- ---------------------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', '')
  )
  on conflict (id) do update
    set email = excluded.email,
        full_name = coalesce(nullif(excluded.full_name, ''), public.profiles.full_name),
        updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- updated_at helper
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at
  before update on public.products
  for each row execute function public.set_updated_at();

drop trigger if exists suppliers_set_updated_at on public.suppliers;
create trigger suppliers_set_updated_at
  before update on public.suppliers
  for each row execute function public.set_updated_at();

drop trigger if exists inventory_alerts_set_updated_at on public.inventory_alerts;
create trigger inventory_alerts_set_updated_at
  before update on public.inventory_alerts
  for each row execute function public.set_updated_at();

drop trigger if exists negotiations_set_updated_at on public.negotiations;
create trigger negotiations_set_updated_at
  before update on public.negotiations
  for each row execute function public.set_updated_at();

drop trigger if exists purchase_orders_set_updated_at on public.purchase_orders;
create trigger purchase_orders_set_updated_at
  before update on public.purchase_orders
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security (each user only sees their rows)
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.products enable row level security;
alter table public.suppliers enable row level security;
alter table public.inventory_alerts enable row level security;
alter table public.negotiations enable row level security;
alter table public.messages enable row level security;
alter table public.quotes enable row level security;
alter table public.purchase_orders enable row level security;
alter table public.activities enable row level security;

-- Profiles
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- Generic owner policies
drop policy if exists "products_all_own" on public.products;
create policy "products_all_own" on public.products
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "suppliers_all_own" on public.suppliers;
create policy "suppliers_all_own" on public.suppliers
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "inventory_alerts_all_own" on public.inventory_alerts;
create policy "inventory_alerts_all_own" on public.inventory_alerts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "negotiations_all_own" on public.negotiations;
create policy "negotiations_all_own" on public.negotiations
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "messages_all_own" on public.messages;
create policy "messages_all_own" on public.messages
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "quotes_all_own" on public.quotes;
create policy "quotes_all_own" on public.quotes
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "purchase_orders_all_own" on public.purchase_orders;
create policy "purchase_orders_all_own" on public.purchase_orders
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "activities_all_own" on public.activities;
create policy "activities_all_own" on public.activities
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Live UI updates: also run db/realtime.sql to add tables to supabase_realtime.
