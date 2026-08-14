-- Enable Supabase Realtime for tables the webapp should live-update.
-- Run once in the Supabase SQL Editor (Dashboard → SQL).
-- Safe to re-run.

do $$
begin
  -- products: Shopify webhook catalog / inventory sync
  begin
    alter publication supabase_realtime add table public.products;
  exception
    when duplicate_object then null;
  end;

  -- dashboard activity feed
  begin
    alter publication supabase_realtime add table public.activities;
  exception
    when duplicate_object then null;
  end;

  -- negotiations list / detail
  begin
    alter publication supabase_realtime add table public.negotiations;
  exception
    when duplicate_object then null;
  end;

  begin
    alter publication supabase_realtime add table public.messages;
  exception
    when duplicate_object then null;
  end;

  begin
    alter publication supabase_realtime add table public.quotes;
  exception
    when duplicate_object then null;
  end;

  begin
    alter publication supabase_realtime add table public.purchase_orders;
  exception
    when duplicate_object then null;
  end;

  begin
    alter publication supabase_realtime add table public.suppliers;
  exception
    when duplicate_object then null;
  end;

  begin
    alter publication supabase_realtime add table public.inventory_alerts;
  exception
    when duplicate_object then null;
  end;
end $$;
