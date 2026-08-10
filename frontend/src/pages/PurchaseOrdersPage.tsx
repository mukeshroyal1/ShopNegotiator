import { useEffect, useState } from 'react'
import { getPurchaseOrders, getShopifyOrders } from '../api/client'
import type { PurchaseOrder, ShopifyOrder } from '../types/api'

export function PurchaseOrdersPage() {
  const [pos, setPos] = useState<PurchaseOrder[]>([])
  const [orders, setOrders] = useState<ShopifyOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ordersWarning, setOrdersWarning] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [purchaseOrders, shopifyResult] = await Promise.all([
          getPurchaseOrders(),
          getShopifyOrders()
            .then((rows) => ({ orders: rows, warning: null as string | null }))
            .catch((err: unknown) => ({
              orders: [] as ShopifyOrder[],
              warning:
                err instanceof Error
                  ? err.message
                  : 'Could not load Shopify orders',
            })),
        ])
        if (cancelled) return
        setPos(purchaseOrders)
        setOrders(shopifyResult.orders)
        setOrdersWarning(shopifyResult.warning)
        setError(null)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load orders')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-8 p-6 md:p-8">
      {loading && <p className="text-sm text-muted-foreground">Loading orders…</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {!loading && (
        <>
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-foreground">Procurement purchase orders</h2>
            <p className="text-sm text-muted-foreground">
              Orders created from approved supplier quotes in Bargain Labs.
            </p>
            {pos.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-card p-6 text-sm text-muted-foreground">
                No purchase orders yet.
              </div>
            ) : (
              <div className="overflow-hidden rounded-xl border border-border bg-card shadow-soft">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-border bg-secondary/50 text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">ID</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium text-right">Total</th>
                      <th className="px-4 py-3 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pos.map((po) => (
                      <tr key={po.id} className="border-b border-border last:border-0">
                        <td className="px-4 py-3 font-mono text-xs">{po.id.slice(0, 8)}</td>
                        <td className="px-4 py-3 capitalize">{po.status}</td>
                        <td className="px-4 py-3 text-right tabular-nums">
                          {po.currency} {po.totalAmount.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {new Date(po.createdAt).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-foreground">Shopify store orders</h2>
            <p className="text-sm text-muted-foreground">
              Live orders from your connected store (read_orders).
            </p>
            {ordersWarning && (
              <div className="rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-foreground">
                Shopify orders unavailable: {ordersWarning}. If you just added
                read_orders, reconnect in Settings. Development apps may also need
                Protected customer data access in the Partner Dashboard.
              </div>
            )}
            {!ordersWarning && orders.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-card p-6 text-sm text-muted-foreground">
                No Shopify orders found.
              </div>
            ) : orders.length > 0 ? (
              <div className="overflow-hidden rounded-xl border border-border bg-card shadow-soft">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-border bg-secondary/50 text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Order</th>
                      <th className="px-4 py-3 font-medium">Payment</th>
                      <th className="px-4 py-3 font-medium">Fulfillment</th>
                      <th className="px-4 py-3 font-medium text-right">Items</th>
                      <th className="px-4 py-3 font-medium text-right">Total</th>
                      <th className="px-4 py-3 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id} className="border-b border-border last:border-0">
                        <td className="px-4 py-3 font-medium">{order.name}</td>
                        <td className="px-4 py-3 capitalize text-muted-foreground">
                          {order.financialStatus || '—'}
                        </td>
                        <td className="px-4 py-3 capitalize text-muted-foreground">
                          {order.fulfillmentStatus || 'unfulfilled'}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums">{order.itemCount}</td>
                        <td className="px-4 py-3 text-right tabular-nums">
                          {order.currency} {order.totalPrice}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {order.createdAt
                            ? new Date(order.createdAt).toLocaleString()
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        </>
      )}
    </div>
  )
}
