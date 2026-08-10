import { ACCOUNT_NAV, WORKSPACE_NAV } from '../../config/navigation'
import { UserProfile } from '../shared/UserProfile'
import { Logo } from './Logo'
import { SidebarItem } from './SidebarItem'

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <Logo />

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-2">
        <div className="space-y-1">
          <p className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
            Workspace
          </p>
          {WORKSPACE_NAV.map((item) => (
            <SidebarItem key={item.to} {...item} />
          ))}
        </div>

        <div className="space-y-1">
          <p className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
            Account
          </p>
          {ACCOUNT_NAV.map((item) => (
            <SidebarItem key={item.to} {...item} />
          ))}
        </div>
      </nav>

      <UserProfile />
    </aside>
  )
}
