import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { BrandMark } from '../../components/BrandMark'
import { useAuth } from '../auth/AuthProvider'

export function HomePage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <BrandMark to="/" size="md" />

          <div className="flex items-center gap-2 sm:gap-3">
            {user ? (
              <Link
                to="/app"
                className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground no-underline transition-colors hover:bg-primary/90"
              >
                Open app
                <ArrowRight size={16} />
              </Link>
            ) : (
              <>
                <Link
                  to="/signin"
                  className="inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-medium text-foreground no-underline transition-colors hover:bg-secondary"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground no-underline transition-colors hover:bg-primary/90"
                >
                  Sign up
                  <ArrowRight size={16} />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-border">
          <div
            className="absolute inset-0 bg-gradient-to-br from-primary/12 via-background to-background"
            aria-hidden="true"
          />
          <div className="relative mx-auto flex max-w-6xl flex-col px-6 py-20 md:py-28">
            <BrandMark size="lg" />
            <h1 className="mt-6 max-w-3xl text-4xl font-bold tracking-tight text-foreground md:text-5xl">
              AI that calls suppliers when your store runs low
            </h1>
            <p className="mt-4 max-w-2xl text-base text-muted-foreground md:text-lg">
              Connect Shopify, add supplier contacts, and let your agent negotiate
              by phone — with fair-price guidance from your own ML model.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              {user ? (
                <Link
                  to="/app"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground no-underline transition-colors hover:bg-primary/90"
                >
                  Go to dashboard
                  <ArrowRight size={16} />
                </Link>
              ) : (
                <>
                  <Link
                    to="/signup"
                    className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground no-underline transition-colors hover:bg-primary/90"
                  >
                    Get started
                    <ArrowRight size={16} />
                  </Link>
                  <Link
                    to="/signin"
                    className="inline-flex h-11 items-center justify-center rounded-xl border border-border bg-card px-5 text-sm font-medium text-foreground no-underline transition-colors hover:bg-secondary"
                  >
                    Sign in
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-6 px-6 py-16 md:grid-cols-3">
          {[
            {
              title: 'Spot low stock early',
              body: 'Shopify webhooks keep inventory in sync and open alerts when stock hits your threshold.',
            },
            {
              title: 'Call suppliers',
              body: 'Add supplier phone numbers manually. Your agent will negotiate on a real phone call.',
            },
            {
              title: 'Track every thread',
              body: 'Review transcripts, quotes, and outcomes in one workspace.',
            },
          ].map((item) => (
            <article
              key={item.title}
              className="rounded-2xl border border-border bg-card p-6 shadow-soft"
            >
              <h2 className="text-lg font-semibold text-foreground">{item.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {item.body}
              </p>
            </article>
          ))}
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-6 text-sm text-muted-foreground">
          <BrandMark to="/" size="sm" />
          <span>AI procurement for modern merchants</span>
        </div>
      </footer>
    </div>
  )
}
