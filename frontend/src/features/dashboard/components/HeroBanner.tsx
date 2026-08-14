export function HeroBanner() {
  return (
    <section className="rounded-2xl border border-border bg-gradient-to-br from-blue-50/80 via-card to-card p-6 md:p-8">
      <div className="max-w-2xl">
        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Shopify connected
        </div>

        <h2 className="mt-4 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          Procurement dashboard
        </h2>

        <p className="mt-2 text-sm text-muted-foreground md:text-base">
          Monitor low-stock alerts, manage supplier contacts, and track negotiations
          from one place.
        </p>
      </div>
    </section>
  )
}
