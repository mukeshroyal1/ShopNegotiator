import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import {
  ProtectedRoute,
  PublicOnlyRoute,
} from './features/auth/ProtectedRoute'
import { SignInPage } from './features/auth/SignInPage'
import { SignUpPage } from './features/auth/SignUpPage'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { HomePage } from './features/marketing/HomePage'
import { ConnectShopifyPage } from './features/shopify/ConnectShopifyPage'
import { ShopifyGateLayout } from './features/shopify/ShopifyRequiredRoute'
import { AppLayout } from './layouts/AppLayout'
import { NegotiationDetail } from './pages/NegotiationDetail'
import { NegotiationsPage } from './pages/NegotiationsPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { ProductsPage } from './pages/ProductsPage'
import { PurchaseOrdersPage } from './pages/PurchaseOrdersPage'
import { SettingsPage } from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />

        <Route element={<PublicOnlyRoute />}>
          <Route path="/signin" element={<SignInPage />} />
          <Route path="/signup" element={<SignUpPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<ShopifyGateLayout />}>
            <Route path="/app/connect-shopify" element={<ConnectShopifyPage />} />

            <Route path="/app" element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route
                path="suppliers"
                element={
                  <PlaceholderPage
                    title="Suppliers"
                    description="Alibaba and preferred supplier profiles will live here."
                  />
                }
              />
              <Route path="negotiations" element={<NegotiationsPage />} />
              <Route path="negotiations/:id" element={<NegotiationDetail />} />
              <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
              <Route
                path="analytics"
                element={
                  <PlaceholderPage
                    title="Analytics"
                    description="Savings and negotiation performance charts will live here."
                  />
                }
              />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
