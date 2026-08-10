import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { getShopifyStatus } from '../../api/client'

const STATUS_TIMEOUT_MS = 4000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = window.setTimeout(
      () => reject(new Error('Shopify status check timed out')),
      ms,
    )
    promise
      .then((value) => {
        window.clearTimeout(timer)
        resolve(value)
      })
      .catch((error: unknown) => {
        window.clearTimeout(timer)
        reject(error)
      })
  })
}

/**
 * After auth, users must finish Shopify onboarding before the dashboard.
 * The connect page always renders immediately (no blocking spinner).
 */
export function ShopifyRequiredRoute() {
  const location = useLocation()
  const isConnectPage = location.pathname.startsWith('/app/connect-shopify')
  const [loading, setLoading] = useState(!isConnectPage)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const status = await withTimeout(getShopifyStatus(), STATUS_TIMEOUT_MS)
        if (!cancelled) setConnected(status.connected)
      } catch {
        if (!cancelled) setConnected(false)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [location.pathname, location.search])

  if (isConnectPage) {
    if (!loading && connected) {
      return <Navigate to="/app" replace />
    }
    return <Outlet />
  }

  if (loading) {
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
