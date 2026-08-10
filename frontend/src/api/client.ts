import { supabase } from '../lib/supabase'
import type {
  DashboardPayload,
  Negotiation,
  Product,
  PurchaseOrder,
  ShopifyLocation,
  ShopifyOrder,
  Supplier,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

async function getAccessToken(): Promise<string> {
  const { data, error } = await supabase.auth.getSession()
  if (error) throw error
  const token = data.session?.access_token
  if (!token) {
    throw new Error('Not signed in')
  }
  return token
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken()
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = body.detail
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

export function getDashboard(): Promise<DashboardPayload> {
  return request<DashboardPayload>('/dashboard/')
}

export function getNegotiations(): Promise<Negotiation[]> {
  return request<Negotiation[]>('/negotiations/')
}

export function getNegotiation(id: string): Promise<Negotiation> {
  return request<Negotiation>(`/negotiations/${id}/`)
}

export function getProducts(): Promise<Product[]> {
  return request<Product[]>('/products/')
}

export function getSuppliers(): Promise<Supplier[]> {
  return request<Supplier[]>('/suppliers/')
}

export function getPurchaseOrders(): Promise<PurchaseOrder[]> {
  return request<PurchaseOrder[]>('/purchase-orders/')
}

export type ShopifyStatus = {
  connected: boolean
  shop: { domain: string; scope: string; installedAt: string } | null
  webhooks?: { address: string | null; configured: boolean }
}

export function getShopifyStatus(): Promise<ShopifyStatus> {
  return request<ShopifyStatus>('/shopify/status/')
}

export function startShopifyConnect(
  shop: string,
): Promise<{ authorizeUrl: string; shop: string }> {
  return request<{ authorizeUrl: string; shop: string }>('/shopify/connect/', {
    method: 'POST',
    body: JSON.stringify({ shop }),
  })
}

export function syncShopifyProducts(): Promise<{
  ok: boolean
  productsSynced: number
}> {
  return request<{ ok: boolean; productsSynced: number }>('/shopify/sync/', {
    method: 'POST',
  })
}

export function getShopifyLocations(): Promise<ShopifyLocation[]> {
  return request<ShopifyLocation[]>('/shopify/locations/')
}

export function getShopifyOrders(): Promise<ShopifyOrder[]> {
  return request<ShopifyOrder[]>('/shopify/orders/')
}

export function registerShopifyWebhooks(): Promise<{
  ok: boolean
  address: string
  topics: string[]
}> {
  return request('/shopify/webhooks/register/', { method: 'POST' })
}
