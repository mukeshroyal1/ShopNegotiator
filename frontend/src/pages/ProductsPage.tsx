import { useMemo } from 'react'
import { AlertTriangle, Package } from 'lucide-react'
import { LowStockAlerts } from '../features/inventory/LowStockAlerts'
import { useLiveProducts } from '../hooks/useLiveProducts'

export function ProductsPage() {
  const { products, loading, error } = useLiveProducts()

  const lowStockCount = useMemo(
    () => products.filter((p) => p.lowStock ?? p.currentStock <= p.threshold).length,
    [products],
  )

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div>
        <p className="text-sm text-muted-foreground">
          Live catalog from your Shopify store — updates here as inventory changes.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {loading
            ? 'Loading…'
            : `${products.length} variants${
                lowStockCount > 0 ? ` · ${lowStockCount} at or below threshold` : ''
              }`}
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && lowStockCount > 0 && <LowStockAlerts compact />}

      {loading && (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-soft">
          <div className="animate-pulse space-y-0">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="border-b border-border px-4 py-4 last:border-0">
                <div className="h-4 w-2/5 rounded bg-secondary" />
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && products.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center">
          <Package className="mx-auto text-muted-foreground" size={28} />
          <p className="mt-3 text-sm font-medium text-foreground">No products yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Add products in Shopify — they’ll show up here automatically.
          </p>
        </div>
      )}

      {!loading && products.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-soft">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-secondary/50 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Product</th>
                <th className="px-4 py-3 font-medium">SKU</th>
                <th className="px-4 py-3 font-medium text-right">Stock</th>
                <th className="px-4 py-3 font-medium text-right">Threshold</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => {
                const low = product.lowStock ?? product.currentStock <= product.threshold
                return (
                  <tr
                    key={product.id}
                    className="border-b border-border last:border-0 hover:bg-secondary/30"
                  >
                    <td className="px-4 py-3 font-medium text-foreground">{product.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      {product.sku || '—'}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-foreground">
                      {product.currentStock}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
                      {product.threshold}
                    </td>
                    <td className="px-4 py-3">
                      {low ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-warning/15 px-2 py-0.5 text-xs font-medium text-warning-foreground">
                          <AlertTriangle size={12} />
                          Low stock
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">OK</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
