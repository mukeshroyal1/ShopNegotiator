import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getNegotiations } from '../api/client'
import { NegotiationCard } from '../features/dashboard/components/NegotiationCard'
import { useRealtimeRefetch } from '../hooks/useRealtimeRefetch'
import type { Negotiation } from '../types/api'

export function NegotiationsPage() {
  const [threads, setThreads] = useState<Negotiation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await getNegotiations()
      setThreads(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load negotiations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useRealtimeRefetch(
    useMemo(() => [{ table: 'negotiations' }], []),
    load,
  )

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          All supplier threads your AI is managing.
        </p>
        <Link
          to="/app"
          className="text-sm font-medium text-primary no-underline hover:text-primary/80"
        >
          ← Dashboard
        </Link>
      </div>

      {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {!loading && !error && threads.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-card p-8 text-sm text-muted-foreground">
          No negotiations yet for this account.
        </div>
      )}

      {!loading && !error && threads.length > 0 && (
        <div className="space-y-4">
          {threads.map((negotiation) => (
            <NegotiationCard key={negotiation.id} negotiation={negotiation} />
          ))}
        </div>
      )}
    </div>
  )
}
