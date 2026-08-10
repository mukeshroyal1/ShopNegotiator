import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  Boxes,
  ClipboardList,
  Handshake,
  LayoutDashboard,
  Settings,
  Users,
} from 'lucide-react'

export type NavItem = {
  label: string
  to: string
  icon: LucideIcon
  matchPrefix?: string
}

export const APP_BASE = '/app'

export const WORKSPACE_NAV: NavItem[] = [
  { label: 'Dashboard', to: APP_BASE, icon: LayoutDashboard },
  {
    label: 'Products',
    to: `${APP_BASE}/products`,
    icon: Boxes,
    matchPrefix: `${APP_BASE}/products`,
  },
  {
    label: 'Suppliers',
    to: `${APP_BASE}/suppliers`,
    icon: Users,
    matchPrefix: `${APP_BASE}/suppliers`,
  },
  {
    label: 'Negotiations',
    to: `${APP_BASE}/negotiations`,
    icon: Handshake,
    matchPrefix: `${APP_BASE}/negotiations`,
  },
  {
    label: 'Purchase Orders',
    to: `${APP_BASE}/purchase-orders`,
    icon: ClipboardList,
    matchPrefix: `${APP_BASE}/purchase-orders`,
  },
  {
    label: 'Analytics',
    to: `${APP_BASE}/analytics`,
    icon: BarChart3,
    matchPrefix: `${APP_BASE}/analytics`,
  },
]

export const ACCOUNT_NAV: NavItem[] = [
  {
    label: 'Settings',
    to: `${APP_BASE}/settings`,
    icon: Settings,
    matchPrefix: `${APP_BASE}/settings`,
  },
]

export const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  [APP_BASE]: {
    title: 'Dashboard',
    subtitle: 'Overview of your AI procurement activity.',
  },
  [`${APP_BASE}/products`]: {
    title: 'Products',
    subtitle: 'Shopify catalog, inventory levels, and low-stock targets.',
  },
  [`${APP_BASE}/suppliers`]: {
    title: 'Suppliers',
    subtitle: 'Browse and manage your supplier network.',
  },
  [`${APP_BASE}/negotiations`]: {
    title: 'Negotiations',
    subtitle: 'Track active and completed AI negotiations.',
  },
  [`${APP_BASE}/purchase-orders`]: {
    title: 'Purchase Orders',
    subtitle: 'Procurement POs and Shopify store orders.',
  },
  [`${APP_BASE}/analytics`]: {
    title: 'Analytics',
    subtitle: 'Insights into savings, outcomes, and performance.',
  },
  [`${APP_BASE}/settings`]: {
    title: 'Settings',
    subtitle: 'Shopify connection, scopes, and inventory locations.',
  },
}
