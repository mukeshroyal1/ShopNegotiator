import { useEffect, useMemo, useRef } from 'react'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { useAuth } from '../features/auth/AuthProvider'
import { supabase } from '../lib/supabase'

export type RealtimeTableSpec = {
  table: string
  /** Extra Realtime filter; defaults to `user_id=eq.<auth user>`. */
  filter?: string
}

/**
 * Re-run `refetch` when Postgres rows change (via Supabase Realtime).
 * Debounced so bulk webhook syncs don't hammer the API.
 */
export function useRealtimeRefetch(
  tables: RealtimeTableSpec[],
  refetch: () => void | Promise<void>,
  options?: { debounceMs?: number; enabled?: boolean },
) {
  const { user } = useAuth()
  const debounceMs = options?.debounceMs ?? 400
  const enabled = options?.enabled ?? true
  const refetchRef = useRef(refetch)
  refetchRef.current = refetch

  const tablesKey = useMemo(
    () =>
      tables
        .map((t) => `${t.table}:${t.filter ?? ''}`)
        .sort()
        .join('|'),
    [tables],
  )

  useEffect(() => {
    if (!enabled || !user?.id || tables.length === 0) return

    let timer: number | undefined
    const schedule = () => {
      window.clearTimeout(timer)
      timer = window.setTimeout(() => {
        void refetchRef.current()
      }, debounceMs)
    }

    const channelName = `live-refetch:${user.id}:${tablesKey}`
    let channel: RealtimeChannel = supabase.channel(channelName)

    for (const spec of tables) {
      const filter = spec.filter ?? `user_id=eq.${user.id}`
      channel = channel.on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: spec.table,
          filter,
        },
        () => {
          schedule()
        },
      )
    }

    channel.subscribe()

    return () => {
      window.clearTimeout(timer)
      void supabase.removeChannel(channel)
    }
    // tablesKey captures tables contents; tables.length is redundant with empty check
    // eslint-disable-next-line react-hooks/exhaustive-deps -- tablesKey is the stable fingerprint
  }, [user?.id, enabled, debounceMs, tablesKey])
}
