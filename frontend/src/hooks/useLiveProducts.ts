import { useCallback, useEffect, useState } from 'react'
import type { RealtimePostgresChangesPayload } from '@supabase/supabase-js'
import { getProducts } from '../api/client'
import { useAuth } from '../features/auth/AuthProvider'
import { supabase } from '../lib/supabase'
import type { Product } from '../types/api'

type ProductRow = {
  id: string
  name: string
  sku: string
  current_stock: number
  threshold: number
  shopify_product_id?: string | null
}

function mapRow(row: ProductRow): Product {
  return {
    id: row.id,
    name: row.name,
    sku: row.sku ?? '',
    currentStock: row.current_stock,
    threshold: row.threshold,
    shopifyProductId: row.shopify_product_id ?? null,
    lowStock: row.current_stock <= row.threshold,
  }
}

function sortProducts(list: Product[]): Product[] {
  return [...list].sort((a, b) => a.name.localeCompare(b.name))
}

/**
 * Products list: initial API load + live Postgres patches (Shopify webhooks → DB → UI).
 */
export function useLiveProducts() {
  const { user } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await getProducts()
      setProducts(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load products')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    void (async () => {
      try {
        const data = await getProducts()
        if (!cancelled) {
          setProducts(data)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load products')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!user?.id) return

    const channel = supabase
      .channel(`products-live:${user.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'products',
          filter: `user_id=eq.${user.id}`,
        },
        (payload: RealtimePostgresChangesPayload<ProductRow>) => {
          setProducts((prev) => {
            if (payload.eventType === 'DELETE') {
              const id = (payload.old as ProductRow | null)?.id
              if (!id) return prev
              return prev.filter((p) => p.id !== id)
            }

            const row = payload.new as ProductRow | null
            if (!row?.id) return prev
            const next = mapRow(row)
            const idx = prev.findIndex((p) => p.id === next.id)
            if (idx === -1) return sortProducts([...prev, next])
            const copy = [...prev]
            copy[idx] = next
            return sortProducts(copy)
          })
          setError(null)
          setLoading(false)
        },
      )
      .subscribe()

    return () => {
      void supabase.removeChannel(channel)
    }
  }, [user?.id])

  return { products, loading, error, reload: load }
}
