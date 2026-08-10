import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Negotiation } from '../../../types/api'
import { NegotiationCard } from './NegotiationCard'

type ActiveNegotiationsProps = {
  negotiations: Negotiation[]
}

export function ActiveNegotiations({ negotiations }: ActiveNegotiationsProps) {
  const active = negotiations.filter((n) =>
    n.status === 'negotiating' || n.status === 'waiting',
  )

  return (
    <section>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            Active Negotiations
          </h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Live deals your AI is working on right now
          </p>
        </div>

        <Link
          to="/app/negotiations"
          className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-primary no-underline transition-colors hover:text-primary/80"
        >
          View all
          <ArrowRight size={14} />
        </Link>
      </div>

      {active.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-6 text-sm text-muted-foreground">
          No active negotiations yet. When the agent starts talking to suppliers,
          they will appear here.
        </div>
      ) : (
        <div className="space-y-4">
          {active.map((negotiation) => (
            <NegotiationCard key={negotiation.id} negotiation={negotiation} />
          ))}
        </div>
      )}
    </section>
  )
}
