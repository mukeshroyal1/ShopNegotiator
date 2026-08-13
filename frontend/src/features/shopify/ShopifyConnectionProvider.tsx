import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { getShopifyStatus, type ShopifyStatus } from '../../api/client'
import { useAuth } from '../auth/AuthProvider'

const STATUS_TIMEOUT_MS = 4000
const STORAGE_PREFIX = 'bargainlabs.shopifyStatus:'

type CachedShopify = {
  connected: boolean
  shop: ShopifyStatus['shop']
  webhooks?: ShopifyStatus['webhooks']
}

type ShopifyConnectionValue = {
  connected: boolean
  shop: ShopifyStatus['shop']
  webhooks: ShopifyStatus['webhooks'] | undefined
  /** True only while the first network check is in flight and we have no cache. */
  initialLoading: boolean
  refresh: () => Promise<void>
}

const ShopifyConnectionContext = createContext<ShopifyConnectionValue | null>(null)

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

function storageKey(userId: string) {
  return `${STORAGE_PREFIX}${userId}`
}

function readCache(userId: string): CachedShopify | null {
  try {
    const raw = sessionStorage.getItem(storageKey(userId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as CachedShopify
    if (typeof parsed?.connected !== 'boolean') return null
    return parsed
  } catch {
    return null
  }
}

function writeCache(userId: string, value: CachedShopify) {
  try {
    sessionStorage.setItem(storageKey(userId), JSON.stringify(value))
  } catch {
    /* ignore quota / private mode */
  }
}

export function ShopifyConnectionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const userId = user?.id ?? null
  const knownConnectedRef = useRef(false)

  const [connected, setConnected] = useState(false)
  const [shop, setShop] = useState<ShopifyStatus['shop']>(null)
  const [webhooks, setWebhooks] = useState<ShopifyStatus['webhooks'] | undefined>(
    undefined,
  )
  const [initialLoading, setInitialLoading] = useState(Boolean(userId))

  const applyStatus = useCallback((status: ShopifyStatus, uid: string) => {
    setConnected(status.connected)
    setShop(status.shop)
    setWebhooks(status.webhooks)
    knownConnectedRef.current = status.connected
    writeCache(uid, {
      connected: status.connected,
      shop: status.shop,
      webhooks: status.webhooks,
    })
  }, [])

  const refresh = useCallback(async () => {
    if (!userId) return
    try {
      const status = await withTimeout(getShopifyStatus(), STATUS_TIMEOUT_MS)
      applyStatus(status, userId)
    } catch {
      // Soft-fail: keep last known connected; only force disconnect if never confirmed.
      if (!knownConnectedRef.current) {
        setConnected(false)
        setShop(null)
        setWebhooks(undefined)
      }
    } finally {
      setInitialLoading(false)
    }
  }, [applyStatus, userId])

  useEffect(() => {
    if (!userId) {
      knownConnectedRef.current = false
      setConnected(false)
      setShop(null)
      setWebhooks(undefined)
      setInitialLoading(false)
      return
    }

    // OAuth callback lands on /app?shopify=connected — ignore a stale "not connected" cache.
    const oauthJustConnected =
      typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).get('shopify') === 'connected'

    const cached = oauthJustConnected ? null : readCache(userId)
    if (cached) {
      setConnected(cached.connected)
      setShop(cached.shop)
      setWebhooks(cached.webhooks)
      knownConnectedRef.current = cached.connected
      setInitialLoading(false)
    } else {
      if (oauthJustConnected) {
        knownConnectedRef.current = true
        setConnected(true)
      }
      setInitialLoading(!oauthJustConnected)
    }

    void refresh()
  }, [userId, refresh])

  const value = useMemo<ShopifyConnectionValue>(
    () => ({
      connected,
      shop,
      webhooks,
      initialLoading,
      refresh,
    }),
    [connected, shop, webhooks, initialLoading, refresh],
  )

  return (
    <ShopifyConnectionContext.Provider value={value}>
      {children}
    </ShopifyConnectionContext.Provider>
  )
}

export function useShopifyConnection() {
  const ctx = useContext(ShopifyConnectionContext)
  if (!ctx) {
    throw new Error('useShopifyConnection must be used within ShopifyConnectionProvider')
  }
  return ctx
}
