import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Negotiation, NegotiationStatus } from '../../../types/api'

type NegotiationCardProps = {
  negotiation: Negotiation
}

const statusStyles: Record<
  NegotiationStatus,
  { label: string; className: string; dotClassName: string }
> = {
  negotiating: {
    label: 'Negotiating',
    className: 'bg-orange-50 text-orange-700',
    dotClassName: 'bg-orange-500',
  },
  waiting: {
    label: 'Waiting',
    className: 'bg-blue-50 text-blue-700',
    dotClassName: 'bg-blue-500',
  },
  completed: {
    label: 'Completed',
    className: 'bg-emerald-50 text-emerald-700',
    dotClassName: 'bg-emerald-500',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'bg-slate-100 text-slate-700',
    dotClassName: 'bg-slate-500',
  },
}

export function NegotiationCard({ negotiation }: NegotiationCardProps) {
  const {
    id,
    supplier,
    product,
    status,
    originalQuote,
    currentOffer,
    savings,
    stage,
    progress,
    updatedAt,
  } = negotiation

  const statusStyle = statusStyles[status]

  return (
    <article className="rounded-xl border border-border bg-card p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-semibold text-foreground">{supplier}</h3>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyle.className}`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${statusStyle.dotClassName}`}
              />
              {statusStyle.label}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{product}</p>
        </div>

        <p className="shrink-0 text-xs text-muted-foreground">{updatedAt}</p>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-muted-foreground">Original quote</p>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {originalQuote}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Current offer</p>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {currentOffer}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Est. savings</p>
          <p className="mt-1 text-sm font-semibold text-success">{savings}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Stage</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{stage}</p>
        </div>
      </div>

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium text-foreground">{progress}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Link
          to={`/app/negotiations/${id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground no-underline transition-colors hover:bg-secondary"
        >
          View details
          <ArrowRight size={14} />
        </Link>
      </div>
    </article>
  )
}
