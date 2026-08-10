import {
  Building2,
  DollarSign,
  MessageSquare,
  Percent,
  type LucideIcon,
} from 'lucide-react'
import type { DashboardStats } from '../../types/api'

export type StatCardModel = {
  id: string
  label: string
  value: string
  trend: string
  trendUp: boolean
  icon: LucideIcon
}

export function buildStatCards(stats: DashboardStats): StatCardModel[] {
  return [
    {
      id: 'active-negotiations',
      label: 'AI Negotiations Active',
      value: String(stats.activeNegotiations),
      trend: 'Live for your account',
      trendUp: true,
      icon: MessageSquare,
    },
    {
      id: 'total-savings',
      label: 'Money Saved This Month',
      value: `$${stats.moneySavedThisMonth.toLocaleString(undefined, {
        maximumFractionDigits: 0,
      })}`,
      trend: 'Completed deals this month',
      trendUp: stats.moneySavedThisMonth >= 0,
      icon: DollarSign,
    },
    {
      id: 'suppliers-engaged',
      label: 'Suppliers Contacted',
      value: String(stats.suppliersContacted),
      trend: 'Across your negotiations',
      trendUp: true,
      icon: Building2,
    },
    {
      id: 'avg-discount',
      label: 'Average Savings',
      value: `${stats.averageSavings.toFixed(1)}%`,
      trend: 'On tracked quotes',
      trendUp: stats.averageSavings >= 0,
      icon: Percent,
    },
  ]
}
