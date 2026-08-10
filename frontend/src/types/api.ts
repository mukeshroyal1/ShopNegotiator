export type NegotiationStatus = 'negotiating' | 'waiting' | 'completed' | 'cancelled'

export type DashboardStats = {
  activeNegotiations: number
  moneySavedThisMonth: number
  suppliersContacted: number
  averageSavings: number
}

export type Negotiation = {
  id: string
  supplier: string
  product: string
  status: NegotiationStatus
  originalQuote: string
  currentOffer: string
  savings: string
  stage: string
  progress: number
  updatedAt: string
  messages?: Message[]
  quotes?: Quote[]
}

export type Message = {
  id: string
  role: 'agent' | 'supplier' | 'system'
  body: string
  createdAt: string
}

export type Quote = {
  id: string
  supplierName: string
  unitPrice: number
  currency: string
  moq: number
  leadTimeDays: number
  isSelected: boolean
}

export type Activity = {
  id: string
  text: string
  time: string
  kind: string
}

export type DashboardPayload = {
  stats: DashboardStats
  negotiations: Negotiation[]
  activities: Activity[]
}

export type Product = {
  id: string
  name: string
  sku: string
  currentStock: number
  threshold: number
  shopifyProductId?: string | null
  lowStock?: boolean
}

export type Supplier = {
  id: string
  name: string
  email: string | null
  alibabaListingId: string | null
}

export type PurchaseOrder = {
  id: string
  status: string
  totalAmount: number
  currency: string
  createdAt: string
}

export type ShopifyOrder = {
  id: string
  name: string
  financialStatus: string
  fulfillmentStatus: string
  totalPrice: string
  currency: string
  createdAt: string
  itemCount: number
}

export type ShopifyLocation = {
  id: string
  name: string
  active: boolean
  address1: string
  city: string
  province: string
  country: string
}
