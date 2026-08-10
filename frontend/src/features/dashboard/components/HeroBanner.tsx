import { ArrowRight } from 'lucide-react'

export function HeroBanner() {
  return (
    <section className="flex flex-col gap-6 rounded-2xl border border-border bg-gradient-to-br from-blue-50/80 via-card to-card p-6 md:flex-row md:items-center md:justify-between md:p-8">
      <div className="max-w-2xl">
        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          AI is actively negotiating
        </div>

        <h2 className="mt-4 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          AI Procurement Dashboard
        </h2>

        <p className="mt-2 text-sm text-muted-foreground md:text-base">
          Monitor supplier negotiations, track savings, and manage procurement
          from one place.
        </p>
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-3">
        <button
          type="button"
          className="inline-flex h-10 items-center justify-center rounded-xl border border-border bg-card px-4 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
        >
          Export report
        </button>

        <button
          type="button"
          className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          New negotiation
          <ArrowRight size={16} />
        </button>
      </div>
    </section>
  )
}
