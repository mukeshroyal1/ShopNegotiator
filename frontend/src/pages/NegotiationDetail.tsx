import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Phone } from 'lucide-react'
import {
  getNegotiation,
  runNegotiationDryRun,
  startNegotiationCall,
} from '../api/client'
import { NegotiationCard } from '../features/dashboard/components/NegotiationCard'
import { useRealtimeRefetch } from '../hooks/useRealtimeRefetch'
import type { Negotiation } from '../types/api'

const LIVE_STAGES = new Set(['Starting call', 'Queued', 'Ringing', 'On a call'])

export function NegotiationDetail() {
  const { id } = useParams<{ id: string }>()
  const [negotiation, setNegotiation] = useState<Negotiation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [calling, setCalling] = useState(false)

  const load = useCallback(async () => {
    if (!id) return
    try {
      const data = await getNegotiation(id)
      setNegotiation(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load negotiation')
      setNegotiation(null)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const liveTables = useMemo(
    () =>
      id
        ? [
            { table: 'negotiations', filter: `id=eq.${id}` },
            { table: 'messages', filter: `negotiation_id=eq.${id}` },
            { table: 'quotes', filter: `negotiation_id=eq.${id}` },
          ]
        : [],
    [id],
  )

  useRealtimeRefetch(liveTables, load, { enabled: Boolean(id) })

  const live = Boolean(negotiation && LIVE_STAGES.has(negotiation.stage))
  const canAct =
    Boolean(id) &&
    negotiation &&
    (negotiation.status === 'waiting' || negotiation.status === 'negotiating') &&
    !live

  async function handleDryRun() {
    if (!id) return
    setRunning(true)
    setError(null)
    try {
      await runNegotiationDryRun(id)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dry-run failed')
    } finally {
      setRunning(false)
    }
  }

  async function handleCall() {
    if (!id) return
    setCalling(true)
    setError(null)
    try {
      await startNegotiationCall(id)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start call')
    } finally {
      setCalling(false)
    }
  }

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/app/negotiations"
          className="inline-block text-sm font-medium text-muted-foreground no-underline hover:text-primary"
        >
          ← All negotiations
        </Link>
        {canAct && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleCall()}
              disabled={calling || running}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
            >
              <Phone size={16} />
              {calling ? 'Dialing…' : 'Call supplier'}
            </button>
            <button
              type="button"
              onClick={() => void handleDryRun()}
              disabled={running || calling}
              className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium disabled:opacity-60"
            >
              {running ? 'Simulating…' : 'Simulate with LLM'}
            </button>
          </div>
        )}
      </div>

      {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {live && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {negotiation?.stage === 'On a call'
            ? 'Call in progress — transcript updates below as you talk.'
            : `${negotiation?.stage}… your phone should ring shortly.`}
        </div>
      )}

      {!loading && !negotiation && (
        <div className="rounded-xl border border-border bg-card p-8 shadow-soft">
          <p className="text-sm text-muted-foreground">Negotiation not found.</p>
        </div>
      )}

      {negotiation && (
        <div className="space-y-6">
          <NegotiationCard negotiation={negotiation} />

          {negotiation.messages && negotiation.messages.length > 0 && (
            <section className="rounded-xl border border-border bg-card p-5 shadow-soft">
              <h2 className="mb-4 text-lg font-semibold text-foreground">Thread</h2>
              <ul className="space-y-3">
                {negotiation.messages.map((message) => (
                  <li
                    key={message.id}
                    className="rounded-lg border border-border px-4 py-3"
                  >
                    <div className="mb-1 flex justify-between gap-3 text-xs text-muted-foreground">
                      <span className="font-semibold uppercase">{message.role}</span>
                      <time>{new Date(message.createdAt).toLocaleString()}</time>
                    </div>
                    <p className="text-sm text-foreground">{message.body}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {negotiation.quotes && negotiation.quotes.length > 0 && (
            <section className="rounded-xl border border-border bg-card p-5 shadow-soft">
              <h2 className="mb-4 text-lg font-semibold text-foreground">Quotes</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-muted-foreground">
                    <tr>
                      <th className="pb-2 font-medium">Supplier</th>
                      <th className="pb-2 font-medium">Unit price</th>
                      <th className="pb-2 font-medium">MOQ</th>
                      <th className="pb-2 font-medium">Lead time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {negotiation.quotes.map((quote) => (
                      <tr key={quote.id} className="border-t border-border">
                        <td className="py-3 font-medium">{quote.supplierName}</td>
                        <td className="py-3">
                          {quote.currency} {quote.unitPrice.toFixed(2)}
                        </td>
                        <td className="py-3">{quote.moq}</td>
                        <td className="py-3">{quote.leadTimeDays} days</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
