-- Milestone 1: manual suppliers + inventory alerts
-- Run once in Supabase SQL Editor after schema.sql

-- Suppliers: phone-first contact fields (drop unused Alibaba column)
alter table public.suppliers add column if not exists contact_name text not null default '';
alter table public.suppliers add column if not exists phone text not null default '';
alter table public.suppliers add column if not exists default_moq integer not null default 1;
alter table public.suppliers add column if not exists last_unit_price numeric(12, 2);
alter table public.suppliers add column if not exists currency text not null default 'USD';

alter table public.suppliers drop column if exists alibaba_listing_id;

-- Inventory alert statuses for the call workflow
alter table public.inventory_alerts drop constraint if exists inventory_alerts_status_check;
alter table public.inventory_alerts
  add constraint inventory_alerts_status_check
  check (status in ('open', 'negotiating', 'resolved', 'failed'));

-- Realtime for suppliers + alerts (safe to re-run)
do $$
begin
  begin
    alter publication supabase_realtime add table public.suppliers;
  exception when duplicate_object then null;
  end;
  begin
    alter publication supabase_realtime add table public.inventory_alerts;
  exception when duplicate_object then null;
  end;
end $$;
