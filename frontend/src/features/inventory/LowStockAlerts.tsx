import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  getInventoryAlerts,
  getSuppliers,
  startNegotiation,
} from '../../api/client'
import { useRealtimeRefetch } from '../../hooks/useRealtimeRefetch'
import type { InventoryAlert, Supplier } from '../../types/api'

type LowStockAlertsProps = {
  compact?: boolean
}

export function LowStockAlerts({ compact = false }: LowStockAlertsProps) {
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState<InventoryAlert[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyAlertId, setBusyAlertId] = useState<string | null>(null)
  const [selectedSupplier, setSelectedSupplier] = useState<Record<string, string>>({})

  const load = useCallback(async () => {
    try {
      const [alertRows, supplierRows] = await Promise.all([
        getInventoryAlerts('open'),
        getSuppliers(),
      ])
      setAlerts(alertRows)
      setSuppliers(supplierRows)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useRealtimeRefetch(
    useMemo(() => [{ table: 'inventory_alerts' }, { table: 'products' }], []),
    load,
  )

  async function handleStart(alert: InventoryAlert) {
    const supplierId = selectedSupplier[alert.id] ?? suppliers[0]?.id
    if (!supplierId) {
      setError('Add a supplier with a phone number before starting a negotiation.')
      return
    }

    setBusyAlertId(alert.id)
    setError(null)
    try {
      const result = await startNegotiation(alert.id, supplierId)
      navigate(`/app/negotiations/${result.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start negotiation')
    } finally {
      setBusyAlertId(null)
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-muted-foreground">
        {compact ? 'Loading alerts…' : 'Loading low-stock alerts…'}
      </p>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card p-6 text-sm text-muted-foreground">
        No open low-stock alerts. When Shopify inventory drops below threshold, alerts
        appear here automatically.
      </div>
    )
  }

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-base font-semibold text-foreground">Low-stock alerts</h2>
        <p className="text-sm text-muted-foreground">
          Pick a supplier and click Start negotiation. Then call the supplier or
          simulate with the LLM on the thread.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
          {suppliers.length === 0 && (
            <>
              {' '}
              <Link to="/app/suppliers" className="font-medium underline">
                Add a supplier
              </Link>
            </>
          )}
        </div>
      )}

      <ul className="space-y-3">
        {alerts.map((alert) => (
          <li
            key={alert.id}
            className="rounded-xl border border-border bg-card p-4 shadow-soft"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-medium text-foreground">{alert.productName}</p>
                <p className="text-xs text-muted-foreground">
                  SKU {alert.sku || '—'} · {alert.currentStock} in stock · threshold{' '}
                  {alert.threshold}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={selectedSupplier[alert.id] ?? suppliers[0]?.id ?? ''}
                  onChange={(e) =>
                    setSelectedSupplier((prev) => ({
                      ...prev,
                      [alert.id]: e.target.value,
                    }))
                  }
                  disabled={suppliers.length === 0 || busyAlertId === alert.id}
                  className="rounded-lg border border-input bg-background px-3 py-2 text-sm"
                >
                  {suppliers.length === 0 ? (
                    <option value="">No suppliers</option>
                  ) : (
                    suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.phone})
                      </option>
                    ))
                  )}
                </select>

                <button
                  type="button"
                  onClick={() => void handleStart(alert)}
                  disabled={suppliers.length === 0 || busyAlertId === alert.id}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
                >
                  {busyAlertId === alert.id ? 'Starting…' : 'Start negotiation'}
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
