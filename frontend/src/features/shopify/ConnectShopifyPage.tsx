import { useEffect, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, Link2, Store } from 'lucide-react'
import { BrandMark } from '../../components/BrandMark'
import { startShopifyConnect } from '../../api/client'
import { useAuth } from '../auth/AuthProvider'

const ERROR_MESSAGES: Record<string, string> = {
  missing_params: 'Shopify did not return the expected OAuth parameters.',
  oauth_failed: 'Could not complete Shopify authorization. Try again.',
  access_denied: 'Shopify connection was denied.',
}

export function ConnectShopifyPage() {
  const { user, signOut } = useAuth()
  const [params] = useSearchParams()
  const [shop, setShop] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const code = params.get('error')
    const detail = params.get('detail')
    if (code) {
      const base = ERROR_MESSAGES[code] ?? `Shopify error: ${code}`
      setError(detail ? `${base} (${detail})` : base)
    }
  }, [params])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const { authorizeUrl } = await startShopifyConnect(shop.trim())
      window.location.assign(authorizeUrl)
    } catch (err) {
      setSubmitting(false)
      setError(err instanceof Error ? err.message : 'Failed to start Shopify connect')
    }
  }

  const email = user?.email ?? 'your account'

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/80">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-6 py-4">
          <BrandMark to="/" size="md" />
          <button
            type="button"
            onClick={() => void signOut()}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-10 md:py-14">
        <p className="text-sm font-medium text-primary">Onboarding</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
          Connect your Shopify store
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
          Signed in as <span className="font-medium text-foreground">{email}</span>.
          Link a store so we can sync products and inventory before opening your
          dashboard.
        </p>

        <ol className="mt-8 grid gap-3 sm:grid-cols-3">
          {[
            {
              icon: Store,
              title: 'Enter store',
              body: 'Use your myshopify.com domain',
            },
            {
              icon: Link2,
              title: 'Approve access',
              body: 'Install Bargain Labs in Shopify',
            },
            {
              icon: CheckCircle2,
              title: 'Sync catalog',
              body: 'Products & stock pull in automatically',
            },
          ].map((step) => (
            <li
              key={step.title}
              className="rounded-xl border border-border bg-card p-4 shadow-soft"
            >
              <step.icon className="text-primary" size={18} />
              <p className="mt-3 text-sm font-semibold text-foreground">{step.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">{step.body}</p>
            </li>
          ))}
        </ol>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-4 rounded-2xl border border-border bg-card p-6 shadow-soft md:p-8"
        >
          <div>
            <label
              htmlFor="shop"
              className="mb-1.5 block text-sm font-medium text-foreground"
            >
              Shopify store domain
            </label>
            <input
              id="shop"
              type="text"
              required
              autoFocus
              placeholder="your-store.myshopify.com"
              value={shop}
              onChange={(event) => setShop(event.target.value)}
              className="h-11 w-full rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/30"
            />
            <p className="mt-1.5 text-xs text-muted-foreground">
              Find this in Shopify Admin → Settings → Domains (ends with
              .myshopify.com).
            </p>
          </div>

          {error && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-primary text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60 sm:w-auto sm:px-6"
          >
            {submitting ? 'Redirecting to Shopify…' : 'Connect store & continue'}
          </button>
        </form>
      </main>
    </div>
  )
}
