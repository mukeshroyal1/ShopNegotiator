import { TrendingDown, TrendingUp } from 'lucide-react'
import type { Stat } from '../types'

type StatCardProps = {
  stat: Stat
}

const iconStyles: Record<string, string> = {
  'active-negotiations': 'bg-blue-50 text-blue-600',
  'total-savings': 'bg-emerald-50 text-emerald-600',
  'suppliers-engaged': 'bg-indigo-50 text-indigo-600',
  'avg-discount': 'bg-orange-50 text-orange-600',
}

export function StatCard({ stat }: StatCardProps) {
  const { label, value, trend, trendUp, icon: Icon, id } = stat
  const iconClass = iconStyles[id] ?? 'bg-secondary text-primary'

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconClass}`}
        >
          <Icon size={18} />
        </div>
      </div>

      <p className="mt-3 text-3xl font-bold tracking-tight text-foreground">
        {value}
      </p>

      <div
        className={`mt-2 flex items-center gap-1 text-sm ${
          trendUp ? 'text-success' : 'text-destructive'
        }`}
      >
        {trendUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        <span>{trend}</span>
      </div>
    </div>
  )
}
