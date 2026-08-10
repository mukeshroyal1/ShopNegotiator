type PlaceholderPageProps = {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="p-6 md:p-8">
      <div className="rounded-xl border border-border bg-card p-8 shadow-soft">
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
