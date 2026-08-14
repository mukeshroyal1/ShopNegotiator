import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDashboard } from '../../api/client'
import { useRealtimeRefetch } from '../../hooks/useRealtimeRefetch'
import type { Activity, DashboardStats, Negotiation } from '../../types/api'
import { ActiveNegotiations } from './components/ActiveNegotiations'
import { HeroBanner } from './components/HeroBanner'
import { RecentActivity } from './components/RecentActivity'
import { StatsGrid } from './components/StatsGrid'
import { buildStatCards } from './stats'
import { LowStockAlerts } from '../inventory/LowStockAlerts'

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

  const load = useCallback(async () => {
    try {
      const data = await getDashboard()
      setStats(data.stats)
      setNegotiations(data.negotiations)
      setActivities(data.activities)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useRealtimeRefetch(
    useMemo(
      () => [
        { table: 'activities' },
        { table: 'negotiations' },
        { table: 'products' },
        { table: 'inventory_alerts' },
      ],
      [],
    ),
    load,
  )

  return (
    <div className="space-y-6 p-6 md:p-8">
      <HeroBanner />

      {loading && (
        <p className="text-sm text-muted-foreground">Loading dashboard…</p>
      )}

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <StatsGrid stats={buildStatCards(stats)} />

          <LowStockAlerts />

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
