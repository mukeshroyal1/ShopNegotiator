import { useEffect, useState } from 'react'
import { getDashboard } from '../../api/client'
import type { Activity, DashboardStats, Negotiation } from '../../types/api'
import { ActiveNegotiations } from './components/ActiveNegotiations'
import { HeroBanner } from './components/HeroBanner'
import { RecentActivity } from './components/RecentActivity'
import { StatsGrid } from './components/StatsGrid'
import { buildStatCards } from './stats'

const emptyStats: DashboardStats = {
  activeNegotiations: 0,
  moneySavedThisMonth: 0,
  suppliersContacted: 0,
  averageSavings: 0,
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(emptyStats)
  const [negotiations, setNegotiations] = useState<Negotiation[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const data = await getDashboard()
        if (cancelled) return
        setStats(data.stats)
        setNegotiations(data.negotiations)
        setActivities(data.activities)
        setError(null)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load dashboard')
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

  return (
    <div className="space-y-6 p-6 md:p-8">
      <HeroBanner />

      {loading && (
        <p className="text-sm text-muted-foreground">Loading your workspace…</p>
      )}

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <StatsGrid stats={buildStatCards(stats)} />

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ActiveNegotiations negotiations={negotiations} />
            </div>
            <RecentActivity activities={activities} />
          </div>
        </>
      )}
    </div>
  )
}
