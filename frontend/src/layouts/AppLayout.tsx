import { Outlet, useLocation } from 'react-router-dom'
import { APP_BASE, PAGE_META } from '../config/navigation'
import { Header } from '../components/layout/Header'
import { Sidebar } from '../components/layout/Sidebar'

export function AppLayout() {
  const { pathname } = useLocation()
  const meta =
    PAGE_META[pathname] ??
    Object.entries(PAGE_META)
      .filter(([path]) => path !== APP_BASE)
      .sort((a, b) => b[0].length - a[0].length)
      .find(([path]) => pathname.startsWith(path))?.[1] ?? {
      title: 'Bargain Labs',
      subtitle: 'AI Procurement',
    }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="shrink-0 border-b border-border bg-card/80 px-6 py-4 md:px-8">
          <Header title={meta.title} subtitle={meta.subtitle} />
        </div>
        <main className="min-h-0 flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
