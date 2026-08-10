import type { Stat } from '../types'
import { StatCard } from './StatCard'

type StatsGridProps = {
  stats: Stat[]
}

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <StatCard key={stat.id} stat={stat} />
      ))}
    </div>
  )
}
