import type { LucideIcon } from 'lucide-react'
import {
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
    subtitle: 'Manual supplier contacts for voice negotiations.',
  },
  [`${APP_BASE}/negotiations`]: {
    title: 'Negotiations',
    subtitle: 'Track active and completed supplier calls.',
  },
  [`${APP_BASE}/purchase-orders`]: {
    title: 'Purchase Orders',
    subtitle: 'Procurement POs and Shopify store orders.',
  },
  [`${APP_BASE}/settings`]: {
    title: 'Settings',
    subtitle: 'Shopify connection, scopes, and inventory locations.',
  },
}
