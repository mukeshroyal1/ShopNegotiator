import { NavLink, useLocation } from 'react-router-dom'
import { APP_BASE, type NavItem } from '../../config/navigation'

type SidebarItemProps = NavItem

function isActivePath(pathname: string, to: string, matchPrefix?: string) {
  if (to === APP_BASE) return pathname === APP_BASE
  const prefix = matchPrefix ?? to
  return pathname === prefix || pathname.startsWith(`${prefix}/`)
}

export function SidebarItem({ icon: Icon, label, to, matchPrefix }: SidebarItemProps) {
  const { pathname } = useLocation()
  const active = isActivePath(pathname, to, matchPrefix)

  return (
    <NavLink
      to={to}
      end={to === APP_BASE}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
        active
          ? 'border border-sidebar-primary bg-blue-50 text-sidebar-primary'
          : 'border border-transparent text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </NavLink>
  )
}
