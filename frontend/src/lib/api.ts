/**
 * SUTRA Dashboard API Client
 * Typed client for the FastAPI backend with JWT token injection
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────

export interface KpiMetric {
  value: number;
  change?: string;
  trend?: "up" | "down";
  period?: string;
  customers_with_debt?: number;
  total_skus?: number;
}

export interface RecentOrder {
  id: string;
  order_number: string;
  customer_name: string;
  total_amount: number;
  status: string;
  created_at: string | null;
}

export interface LowStockItem {
  sku: string;
  name: string;
  remaining: number;
  threshold: number;
  unit: string;
}

export interface TopMover {
  sku: string;
  name: string;
  total_sold: number;
  total_revenue: number;
}

export interface DashboardKpiData {
  kpi: {
    total_orders: KpiMetric;
    revenue_mtd: KpiMetric;
    udhaar_outstanding: KpiMetric;
    low_stock_count: KpiMetric;
  };
  recent_orders: RecentOrder[];
  low_stock_items: LowStockItem[];
  top_movers: TopMover[];
}

interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  timestamp?: string;
}

// ── Token Management ─────────────────────────────────────────────────────────

const TOKEN_COOKIE = "sutra_token";

function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${TOKEN_COOKIE}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function setToken(token: string, expiresInDays = 7): void {
  const expires = new Date(Date.now() + expiresInDays * 86400000).toUTCString();
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; expires=${expires}; path=/; SameSite=Lax`;
}

export function clearToken(): void {
  document.cookie = `${TOKEN_COOKIE}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

// ── HTTP Client ──────────────────────────────────────────────────────────────

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  const json: ApiResponse<T> = await res.json();

  if (!res.ok) {
    throw new Error(json.message || `Request failed: ${res.status}`);
  }

  return json.data as T;
}

// ── Auth API ─────────────────────────────────────────────────────────────────

export interface LoginPayload {
  phone_number: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const json: ApiResponse<TokenResponse> = await res.json();

  if (!res.ok) {
    throw new Error((json as any).detail || json.message || "Login failed");
  }

  if (!json.data) throw new Error("Empty response");

  // Store token
  setToken(json.data.access_token, 7);

  return json.data;
}

// ── Dashboard API ────────────────────────────────────────────────────────────

export async function fetchDashboardKpi(
  tenantId: string,
  days = 30,
): Promise<DashboardKpiData> {
  return request<DashboardKpiData>(
    `/api/v1/dashboard/kpi?tenant_id=${encodeURIComponent(tenantId)}&days=${days}`,
  );
}

// ── Inventory API ─────────────────────────────────────────────────────────────

export interface InventoryItem {
  id: string;
  tenant_id: string;
  sku: string;
  name: string;
  description: string | null;
  category: string | null;
  hsn_code: string | null;
  unit: string;
  purchase_price: number;
  selling_price: number;
  gst_rate: number;
  quantity: number;
  min_stock_level: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface InventoryListData {
  items: InventoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface InventoryCreatePayload {
  sku: string;
  name: string;
  description?: string;
  category?: string;
  hsn_code?: string;
  unit: string;
  purchase_price: number;
  selling_price: number;
  gst_rate?: number;
  quantity?: number;
  min_stock_level?: number;
}

export interface InventoryUpdatePayload {
  sku?: string;
  name?: string;
  description?: string;
  category?: string;
  hsn_code?: string;
  unit?: string;
  purchase_price?: number;
  selling_price?: number;
  gst_rate?: number;
  quantity?: number;
  min_stock_level?: number;
  is_active?: boolean;
}

export interface StockAdjustPayload {
  quantity_change: number;
  reason?: string;
}

export async function fetchInventory(params?: {
  category?: string;
  low_stock_only?: boolean;
  search?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}): Promise<InventoryListData> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set("category", params.category);
  if (params?.low_stock_only) searchParams.set("low_stock_only", "true");
  if (params?.search) searchParams.set("search", params.search);
  if (params?.is_active !== undefined) searchParams.set("is_active", String(params.is_active));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  return request<InventoryListData>(`/api/v1/inventory/${qs ? `?${qs}` : ""}`);
}

export async function fetchInventoryItem(itemId: string): Promise<{ item: InventoryItem }> {
  return request<{ item: InventoryItem }>(`/api/v1/inventory/${itemId}`);
}

export async function createInventoryItem(
  payload: InventoryCreatePayload,
): Promise<{ item: InventoryItem }> {
  return request<{ item: InventoryItem }>("/api/v1/inventory/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateInventoryItem(
  itemId: string,
  payload: InventoryUpdatePayload,
): Promise<{ item: InventoryItem }> {
  return request<{ item: InventoryItem }>(`/api/v1/inventory/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteInventoryItem(
  itemId: string,
): Promise<{ item_id: string }> {
  return request<{ item_id: string }>(`/api/v1/inventory/${itemId}`, {
    method: "DELETE",
  });
}

export async function adjustStock(
  itemId: string,
  payload: StockAdjustPayload,
): Promise<{ item: InventoryItem; previous_quantity: number; quantity_change: number }> {
  return request<{ item: InventoryItem; previous_quantity: number; quantity_change: number }>(
    `/api/v1/inventory/${itemId}/stock`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export async function fetchInventoryCategories(): Promise<{ categories: string[] }> {
  return request<{ categories: string[] }>("/api/v1/inventory/categories");
}

// ── Customers API ────────────────────────────────────────────────────────────

export interface Customer {
  id: string;
  tenant_id: string;
  phone_number: string;
  name: string | null;
  address: string | null;
  credit_limit: number;
  current_balance: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  total_orders?: number;
}

export interface CustomerListData {
  items: Customer[];
  total: number;
  limit: number;
  offset: number;
}

export interface CustomerCreatePayload {
  phone_number: string;
  name?: string;
  address?: string;
  credit_limit?: number;
}

export interface CustomerUpdatePayload {
  phone_number?: string;
  name?: string;
  address?: string;
  credit_limit?: number;
  current_balance?: number;
  is_active?: boolean;
}

export interface LedgerEntry {
  id: string;
  transaction_type: string;
  amount: number;
  balance_after: number;
  description: string | null;
  reference_number: string | null;
  source: string;
  created_at: string | null;
}

export interface LedgerData {
  entries: LedgerEntry[];
  total: number;
  limit: number;
  offset: number;
}

export async function fetchCustomers(params?: {
  search?: string;
  has_balance?: boolean;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}): Promise<CustomerListData> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set("search", params.search);
  if (params?.has_balance !== undefined) searchParams.set("has_balance", String(params.has_balance));
  if (params?.is_active !== undefined) searchParams.set("is_active", String(params.is_active));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  return request<CustomerListData>(`/api/v1/customers/${qs ? `?${qs}` : ""}`);
}

export async function fetchCustomer(customerId: string): Promise<{ customer: Customer }> {
  return request<{ customer: Customer }>(`/api/v1/customers/${customerId}`);
}

export async function createCustomer(
  payload: CustomerCreatePayload,
): Promise<{ customer: Customer }> {
  return request<{ customer: Customer }>("/api/v1/customers/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomer(
  customerId: string,
  payload: CustomerUpdatePayload,
): Promise<{ customer: Customer }> {
  return request<{ customer: Customer }>(`/api/v1/customers/${customerId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomer(customerId: string): Promise<{ customer_id: string }> {
  return request<{ customer_id: string }>(`/api/v1/customers/${customerId}`, {
    method: "DELETE",
  });
}

export async function fetchCustomerLedger(
  customerId: string,
  params?: { limit?: number; offset?: number },
): Promise<LedgerData> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  return request<LedgerData>(`/api/v1/customers/${customerId}/ledger${qs ? `?${qs}` : ""}`);
}
