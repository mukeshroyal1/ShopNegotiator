import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
/** Classic anon JWT, or newer publishable key from the Supabase dashboard. */
const supabaseKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseKey)

export function createClient() {
  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      'Missing Supabase env. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (or VITE_SUPABASE_PUBLISHABLE_KEY) in frontend/.env',
    )
  }

  return createBrowserClient(supabaseUrl, supabaseKey)
}

/** Shared browser client for the SPA. */
export const supabase = isSupabaseConfigured
  ? createClient()
  : createBrowserClient(
      'https://placeholder.supabase.co',
      'placeholder-key',
    )

if (!isSupabaseConfigured) {
  console.warn(
    'Supabase env vars missing. Copy .env.example to .env and add your project URL + anon/publishable key.',
  )
}
