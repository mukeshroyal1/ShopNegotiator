import { Navigate, Outlet, useLocation } from 'react-router-dom'
import {
  ShopifyConnectionProvider,
  useShopifyConnection,
} from './ShopifyConnectionProvider'

/**
 * After auth, users must finish Shopify onboarding before the dashboard.
 * Status is loaded once per session via ShopifyConnectionProvider — not on every route.
 */
export function ShopifyRequiredRoute() {
  const location = useLocation()
  const isConnectPage = location.pathname.startsWith('/app/connect-shopify')
  const { connected, initialLoading } = useShopifyConnection()

  if (isConnectPage) {
    // Only bounce away once we know they're connected (cached or fresh).
    if (!initialLoading && connected) {
      return <Navigate to="/app" replace />
    }
    return <Outlet />
  }

  // Block only the first check when we have no cache yet.
  if (initialLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        Loading your workspace…
      </div>
    )
  }

  if (!connected) {
    return <Navigate to="/app/connect-shopify" replace />
  }

  return <Outlet />
}

/** Stable route layout: connection context + gate (survives sidebar navigations). */
export function ShopifyGateLayout() {
  return (
    <ShopifyConnectionProvider>
      <ShopifyRequiredRoute />
    </ShopifyConnectionProvider>
  )
}
