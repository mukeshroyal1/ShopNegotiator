import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Phone, Plus, Trash2, UserRound } from 'lucide-react'
import {
  createSupplier,
  deleteSupplier,
  getSuppliers,
  updateSupplier,
} from '../api/client'
import type { Supplier, SupplierInput } from '../types/api'

const emptyForm: SupplierInput = {
  name: '',
  contactName: '',
  phone: '',
  email: '',
  defaultMoq: 1,
  lastUnitPrice: null,
  currency: 'USD',
  notes: '',
}

export function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<SupplierInput>(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      const rows = await getSuppliers()
      setSuppliers(rows)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suppliers')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  function openCreate() {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  function openEdit(supplier: Supplier) {
    setEditingId(supplier.id)
    setForm({
      name: supplier.name,
      contactName: supplier.contactName,
      phone: supplier.phone,
      email: supplier.email,
      defaultMoq: supplier.defaultMoq,
      lastUnitPrice: supplier.lastUnitPrice,
      currency: supplier.currency,
      notes: supplier.notes,
    })
    setShowForm(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (editingId) {
        await updateSupplier(editingId, form)
      } else {
        await createSupplier(form)
      }
      setShowForm(false)
      setForm(emptyForm)
      setEditingId(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save supplier')
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('Delete this supplier?')) return
    setBusy(true)
    setError(null)
    try {
      await deleteSupplier(id)
      if (editingId === id) {
        setShowForm(false)
        setEditingId(null)
      }
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete supplier')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">
            Add suppliers manually — phone number is required for voice negotiations.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          <Plus size={16} />
          Add supplier
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-border bg-card p-6 shadow-soft"
        >
          <h2 className="text-base font-semibold text-foreground">
            {editingId ? 'Edit supplier' : 'New supplier'}
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="text-muted-foreground">Company / name *</span>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted-foreground">Contact name</span>
              <input
                value={form.contactName ?? ''}
                onChange={(e) => setForm({ ...form, contactName: e.target.value })}
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted-foreground">Phone (E.164) *</span>
              <input
                required
                placeholder="+14155551234"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted-foreground">Email</span>
              <input
                type="email"
                value={form.email ?? ''}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted-foreground">Default MOQ</span>
              <input
                type="number"
                min={1}
                value={form.defaultMoq ?? 1}
                onChange={(e) =>
                  setForm({ ...form, defaultMoq: Number(e.target.value) || 1 })
                }
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted-foreground">Last unit price</span>
              <input
                type="number"
                step="0.01"
                min={0}
                value={form.lastUnitPrice ?? ''}
                onChange={(e) =>
                  setForm({
                    ...form,
                    lastUnitPrice: e.target.value ? Number(e.target.value) : null,
                  })
                }
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
            <label className="block text-sm sm:col-span-2">
              <span className="text-muted-foreground">Notes</span>
              <textarea
                rows={3}
                value={form.notes ?? ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="mt-1 w-full rounded-lg border border-input bg-background px-3 py-2"
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
            >
              {busy ? 'Saving…' : editingId ? 'Save changes' : 'Create supplier'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false)
                setEditingId(null)
              }}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-muted-foreground">Loading suppliers…</p>}

      {!loading && suppliers.length === 0 && !showForm && (
        <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center">
          <UserRound className="mx-auto text-muted-foreground" size={28} />
          <p className="mt-3 text-sm font-medium text-foreground">No suppliers yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Add yourself as a supplier with your phone number to test call negotiations later.
          </p>
        </div>
      )}

      {!loading && suppliers.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-soft">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-secondary/50 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Supplier</th>
                <th className="px-4 py-3 font-medium">Phone</th>
                <th className="px-4 py-3 font-medium">MOQ</th>
                <th className="px-4 py-3 font-medium">Last price</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((supplier) => (
                <tr key={supplier.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <p className="font-medium text-foreground">{supplier.name}</p>
                    {supplier.contactName && (
                      <p className="text-xs text-muted-foreground">{supplier.contactName}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 font-mono text-xs">
                      <Phone size={12} />
                      {supplier.phone}
                    </span>
                  </td>
                  <td className="px-4 py-3 tabular-nums">{supplier.defaultMoq}</td>
                  <td className="px-4 py-3 tabular-nums">
                    {supplier.lastUnitPrice != null
                      ? `${supplier.currency} ${supplier.lastUnitPrice.toFixed(2)}`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(supplier)}
                        className="text-sm font-medium text-primary"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(supplier.id)}
                        disabled={busy}
                        className="inline-flex items-center gap-1 text-sm text-destructive"
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
