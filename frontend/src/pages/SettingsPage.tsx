import { useEffect, useState, type FormEvent } from 'react'
import {
  getShopifyLocations,
  getShopifyStatus,
  registerShopifyWebhooks,
  startShopifyConnect,
  type ShopifyStatus,
} from '../api/client'
import type { ShopifyLocation } from '../types/api'

export function SettingsPage() {
  const [status, setStatus] = useState<ShopifyStatus | null>(null)
  const [locations, setLocations] = useState<ShopifyLocation[]>([])
  const [shopInput, setShopInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const shopify = await getShopifyStatus()
        if (cancelled) return
        setStatus(shopify)
        setShopInput(shopify.shop?.domain?.replace('.myshopify.com', '') ?? '')
        if (shopify.connected) {
          const locs = await getShopifyLocations().catch(() => [])
          if (!cancelled) setLocations(locs)
        }
        setError(null)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load settings')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleReconnect(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const shop = shopInput.trim() || status?.shop?.domain || ''
      const { authorizeUrl } = await startShopifyConnect(shop)
      window.location.assign(authorizeUrl)
    } catch (err) {
      setBusy(false)
      setError(err instanceof Error ? err.message : 'Could not start reconnect')
    }
  }

  async function handleRegisterWebhooks() {
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const result = await registerShopifyWebhooks()
      setMessage(`Live sync enabled → ${result.address}`)
      const shopify = await getShopifyStatus()
      setStatus(shopify)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not enable webhooks')
    } finally {
      setBusy(false)
    }
  }

  const scopes = (status?.shop?.scope || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  return (
    <div className="space-y-6 p-6 md:p-8">
      {loading && <p className="text-sm text-muted-foreground">Loading settings…</p>}
      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-xl border border-border bg-card px-4 py-3 text-sm text-foreground">
          {message}
        </div>
      )}

      {!loading && (
        <>
          <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
            <h2 className="text-base font-semibold text-foreground">Shopify connection</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Product and inventory changes push from Shopify via webhooks. Reconnect only
              to update scopes or switch stores.
            </p>

            {status?.connected && status.shop ? (
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">Store</dt>
                  <dd className="font-medium text-foreground">{status.shop.domain}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Installed</dt>
                  <dd className="font-medium text-foreground">
                    {new Date(status.shop.installedAt).toLocaleString()}
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-muted-foreground">Live sync (webhooks)</dt>
                  <dd className="font-medium text-foreground">
                    {status.webhooks?.configured
                      ? status.webhooks.address
                      : 'Not configured on server (set SHOPIFY_APP_URL)'}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">No store connected.</p>
            )}

            {scopes.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Granted scopes
                </p>
                <ul className="mt-2 flex flex-wrap gap-2">
                  {scopes.map((scope) => (
                    <li
                      key={scope}
                      className="rounded-md bg-secondary px-2 py-1 font-mono text-xs text-secondary-foreground"
                    >
                      {scope}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <form onSubmit={handleReconnect} className="mt-6 flex flex-wrap items-end gap-3">
              <label className="block min-w-[220px] flex-1 text-sm">
                <span className="text-muted-foreground">Store name</span>
                <input
                  value={shopInput}
                  onChange={(e) => setShopInput(e.target.value)}
                  placeholder="your-store"
                  className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-foreground"
                />
              </label>
              <button
                type="submit"
                disabled={busy}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
              >
                {busy ? 'Working…' : 'Reconnect Shopify'}
              </button>
              {status?.connected && (
                <button
                  type="button"
                  onClick={() => void handleRegisterWebhooks()}
                  disabled={busy}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground disabled:opacity-60"
                >
                  Enable live sync
                </button>
              )}
            </form>
          </section>

          <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
            <h2 className="text-base font-semibold text-foreground">Inventory locations</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              From Shopify (read_locations).
            </p>
            {locations.length === 0 ? (
              <p className="mt-4 text-sm text-muted-foreground">
                No locations loaded. Reconnect if this scope was just added.
              </p>
            ) : (
              <ul className="mt-4 divide-y divide-border">
                {locations.map((loc) => (
                  <li key={loc.id} className="flex items-start justify-between gap-4 py-3 text-sm">
                    <div>
                      <p className="font-medium text-foreground">{loc.name}</p>
                      <p className="text-muted-foreground">
                        {[loc.address1, loc.city, loc.province, loc.country]
                          .filter(Boolean)
                          .join(', ') || 'No address'}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {loc.active ? 'Active' : 'Inactive'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}
