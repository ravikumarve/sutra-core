"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchOrders,
  fetchOrder,
  createOrder,
  updateOrder,
  deleteOrder,
  fetchInventory,
  fetchCustomers,
  type Order,
  type OrderListData,
  type InventoryItem,
  type Customer,
} from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

function statusBadge(status: string): { label: string; color: string } {
  switch (status) {
    case "pending":
      return { label: "Pending", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" };
    case "confirmed":
      return { label: "Confirmed", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" };
    case "delivered":
      return { label: "Delivered", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" };
    case "cancelled":
      return { label: "Cancelled", color: "text-red-400 bg-red-500/10 border-red-500/20" };
    default:
      return { label: status, color: "text-text-muted bg-bg-void border-border-dim" };
  }
}

function paymentBadge(payment_status: string): { label: string; color: string } {
  switch (payment_status) {
    case "paid":
      return { label: "Paid", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" };
    case "pending":
      return { label: "Pending", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" };
    case "partial":
      return { label: "Partial", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" };
    default:
      return { label: payment_status, color: "text-text-muted bg-bg-void border-border-dim" };
  }
}

// ── Component ────────────────────────────────────────────────────────────────

export default function OrdersPage() {
  const [data, setData] = useState<OrderListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Create modal
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formCustomerId, setFormCustomerId] = useState("");
  const [formPaymentMethod, setFormPaymentMethod] = useState("cash");
  const [formIsCredit, setFormIsCredit] = useState(false);
  const [formNotes, setFormNotes] = useState("");
  const [formItems, setFormItems] = useState<{ inventory_id: string; quantity: string }[]>([]);
  const [inventoryList, setInventoryList] = useState<InventoryItem[]>([]);
  const [customerList, setCustomerList] = useState<Customer[]>([]);

  // Detail modal
  const [detailOrder, setDetailOrder] = useState<Order | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Cancel confirmation
  const [confirmCancel, setConfirmCancel] = useState<string | null>(null);

  // ── Data loading ──

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 100 };
      if (search) params.search = search;
      if (statusFilter) {
        if (statusFilter === "paid" || statusFilter === "pending" || statusFilter === "partial") {
          params.payment_status = statusFilter;
        } else {
          params.status = statusFilter;
        }
      }

      const result = await fetchOrders(params);
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Form helpers ──

  function openCreate() {
    setFormCustomerId("");
    setFormPaymentMethod("cash");
    setFormIsCredit(false);
    setFormNotes("");
    setFormItems([]);
    setShowForm(true);

    // Load inventory and customers for select dropdowns
    fetchInventory({ is_active: true, limit: 500 }).then((r) => setInventoryList(r.items)).catch(() => {});
    fetchCustomers({ is_active: true, limit: 500 }).then((r) => setCustomerList(r.items)).catch(() => {});
  }

  function addFormItem() {
    setFormItems([...formItems, { inventory_id: "", quantity: "1" }]);
  }

  function removeFormItem(idx: number) {
    setFormItems(formItems.filter((_, i) => i !== idx));
  }

  function updateFormItem(idx: number, field: "inventory_id" | "quantity", value: string) {
    const items = [...formItems];
    items[idx] = { ...items[idx], [field]: value };
    setFormItems(items);
  }

  async function handleCreate() {
    if (formItems.length === 0 || formItems.some((i) => !i.inventory_id)) {
      alert("Please add at least one item with a product selected");
      return;
    }

    setSaving(true);
    try {
      await createOrder({
        customer_id: formCustomerId || undefined,
        payment_method: formPaymentMethod,
        is_credit: formIsCredit,
        notes: formNotes || undefined,
        source: "manual",
        items: formItems.map((i) => ({
          inventory_id: i.inventory_id,
          quantity: parseInt(i.quantity || "1"),
        })),
      });

      setShowForm(false);
      await loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel(orderId: string) {
    try {
      await deleteOrder(orderId);
      setConfirmCancel(null);
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleStatusChange(orderId: string, newStatus: string) {
    try {
      await updateOrder(orderId, { status: newStatus });
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function openDetail(orderId: string) {
    setDetailLoading(true);
    setDetailOrder(null);
    try {
      const result = await fetchOrder(orderId);
      setDetailOrder(result.order);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setDetailLoading(false);
    }
  }

  // ── Stats from data ──
  const totalOrders = data?.total ?? 0;
  const totalRevenue = data?.items.reduce((s, o) => s + o.total_amount, 0) ?? 0;
  const pendingOrders = data?.items.filter((o) => o.status === "pending").length ?? 0;
  const deliveredOrders = data?.items.filter((o) => o.status === "delivered").length ?? 0;

  // ── Render ──

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-titanium">Orders</h1>
          <p className="text-text-muted text-sm font-light mt-1">
            Order management, tracking, and fulfillment
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-xl transition-colors"
        >
          + New Order
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-5 max-md:grid-cols-2 max-sm:grid-cols-1">
        {[
          { label: "Total Orders", value: String(totalOrders), sub: "All time" },
          { label: "Revenue", value: formatCurrency(totalRevenue), sub: "Total order value" },
          { label: "Pending", value: String(pendingOrders), sub: "Awaiting fulfillment", warn: pendingOrders > 0 },
          { label: "Delivered", value: String(deliveredOrders), sub: "Completed orders" },
        ].map((stat) => (
          <div
            key={stat.label}
            className={`bg-bg-surface border rounded-xl p-5 ${
              stat.warn ? "border-amber-500/30" : "border-border-dim"
            }`}
          >
            <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
              {stat.label}
            </div>
            <div
              className={`text-2xl font-bold font-mono mb-1 ${
                stat.warn ? "text-amber-400" : "text-text-main"
              }`}
            >
              {stat.value}
            </div>
            <div className="text-xs text-text-muted font-light">{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Search + Filter */}
      <div className="flex gap-4 items-center max-sm:flex-col">
        <div className="relative flex-1 max-w-md">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-faint text-sm">⊖</span>
          <input
            type="text"
            placeholder="Search by order number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main placeholder:text-text-faint focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
        >
          <option value="">All Orders</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
        </select>
      </div>

      {/* Orders Table */}
      {loading ? (
        <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
          <p className="text-text-muted text-sm">Loading orders...</p>
        </div>
      ) : error ? (
        <div className="bg-bg-surface border border-red-500/20 rounded-xl p-12 text-center">
          <p className="text-red-400 text-sm">{error}</p>
          <button onClick={loadData} className="mt-3 text-emerald-400 text-sm hover:underline">
            Retry
          </button>
        </div>
      ) : (
        <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dim">
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Order #</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Customer</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Date</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Amount</th>
                  <th className="text-center px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Status</th>
                  <th className="text-center px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Payment</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-text-muted text-sm">
                      No orders found. Click &quot;New Order&quot; to create one.
                    </td>
                  </tr>
                ) : (
                  data?.items.map((order) => {
                    const sb = statusBadge(order.status);
                    const pb = paymentBadge(order.payment_status);
                    return (
                      <tr
                        key={order.id}
                        className="border-b border-border-dim/50 hover:bg-bg-void/50 transition-colors"
                      >
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs text-emerald-400">
                            {order.order_number}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="text-text-main font-medium">
                            {order.customer_name || "Walk-in"}
                          </div>
                          {order.customer_phone && (
                            <div className="text-xs text-text-muted font-mono">
                              {order.customer_phone}
                            </div>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-xs text-text-muted">
                          {order.created_at
                            ? new Date(order.created_at).toLocaleDateString("en-IN", {
                                day: "2-digit",
                                month: "short",
                              })
                            : "—"}
                        </td>
                        <td className="px-5 py-3.5 text-right font-mono text-text-main">
                          {formatCurrency(order.total_amount)}
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          <span
                            className={`inline-block px-2 py-1 rounded-lg text-xs font-mono border ${sb.color}`}
                          >
                            {sb.label}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          <span
                            className={`inline-block px-2 py-1 rounded-lg text-xs font-mono border ${pb.color}`}
                          >
                            {pb.label}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => openDetail(order.id)}
                              className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-emerald-400 hover:border-emerald-500/30 transition-colors"
                            >
                              View
                            </button>
                            {order.status === "pending" && (
                              <>
                                <button
                                  onClick={() => handleStatusChange(order.id, "confirmed")}
                                  className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-blue-400 hover:border-blue-500/30 transition-colors"
                                >
                                  Confirm
                                </button>
                                <button
                                  onClick={() => handleStatusChange(order.id, "delivered")}
                                  className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-emerald-400 hover:border-emerald-500/30 transition-colors"
                                >
                                  Deliver
                                </button>
                              </>
                            )}
                            {order.status !== "cancelled" && (
                              <button
                                onClick={() => setConfirmCancel(order.id)}
                                className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-red-400 hover:border-red-500/30 transition-colors"
                              >
                                ✕
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Order Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-titanium mb-1">New Order</h2>
            <p className="text-text-muted text-xs mb-6 font-light">Create a manual order</p>

            {/* Customer & Payment */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Customer</label>
                <select
                  value={formCustomerId}
                  onChange={(e) => setFormCustomerId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="">Walk-in Customer</option>
                  {customerList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name || c.phone_number}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Payment Method</label>
                <select
                  value={formPaymentMethod}
                  onChange={(e) => setFormPaymentMethod(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="cash">Cash</option>
                  <option value="upi">UPI</option>
                  <option value="credit">Credit / Udhaar</option>
                  <option value="card">Card</option>
                  <option value="bank_transfer">Bank Transfer</option>
                </select>
              </div>

              <div className="flex items-center gap-3 mt-2">
                <input
                  type="checkbox"
                  id="is_credit"
                  checked={formIsCredit}
                  onChange={(e) => setFormIsCredit(e.target.checked)}
                  className="rounded bg-bg-void border-border-dim"
                />
                <label htmlFor="is_credit" className="text-sm text-text-muted">
                  Mark as Credit (Udhaar)
                </label>
              </div>
            </div>

            {/* Order Items */}
            <h3 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-3">Items</h3>

            {formItems.map((item, idx) => (
              <div key={idx} className="flex gap-3 items-end mb-3">
                <div className="flex-1">
                  <label className="block text-xs text-text-faint mb-1">Product</label>
                  <select
                    value={item.inventory_id}
                    onChange={(e) => updateFormItem(idx, "inventory_id", e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Select product...</option>
                    {inventoryList
                      .filter((inv) => inv.quantity > 0)
                      .map((inv) => (
                        <option key={inv.id} value={inv.id}>
                          {inv.name} ({inv.sku}) — {formatCurrency(inv.selling_price)}/{inv.unit} — Stock: {inv.quantity}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="w-24">
                  <label className="block text-xs text-text-faint mb-1">Qty</label>
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) => updateFormItem(idx, "quantity", e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
                <button
                  onClick={() => removeFormItem(idx)}
                  className="px-3 py-2.5 text-text-muted hover:text-red-400 transition-colors mb-0"
                >
                  ✕
                </button>
              </div>
            ))}

            <button
              onClick={addFormItem}
              className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors mb-4"
            >
              + Add item
            </button>

            {/* Notes */}
            <div className="mt-4">
              <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Notes</label>
              <textarea
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50 resize-none"
                placeholder="Optional order notes"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => setShowForm(false)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={saving || formItems.length === 0}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
              >
                {saving ? "Creating..." : "Create Order"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {detailOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-2xl mx-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-titanium">{detailOrder.order_number}</h2>
                <p className="text-text-muted text-xs mt-1">
                  {detailOrder.customer_name || "Walk-in"}
                  {detailOrder.customer_phone && ` • ${detailOrder.customer_phone}`}
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold font-mono text-text-main">
                  {formatCurrency(detailOrder.total_amount)}
                </div>
                <div className="text-xs text-text-faint">
                  {detailOrder.created_at
                    ? new Date(detailOrder.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </div>
              </div>
            </div>

            {/* Status badges */}
            <div className="flex gap-3 mb-6">
              <span
                className={`inline-block px-3 py-1.5 rounded-lg text-xs font-mono border ${statusBadge(detailOrder.status).color}`}
              >
                {statusBadge(detailOrder.status).label}
              </span>
              <span
                className={`inline-block px-3 py-1.5 rounded-lg text-xs font-mono border ${paymentBadge(detailOrder.payment_status).color}`}
              >
                {paymentBadge(detailOrder.payment_status).label}
              </span>
              <span className="inline-block px-3 py-1.5 rounded-lg text-xs font-mono border text-text-muted bg-bg-void border-border-dim capitalize">
                {detailOrder.payment_method}
              </span>
              {detailOrder.source !== "manual" && (
                <span className="inline-block px-3 py-1.5 rounded-lg text-xs font-mono border text-text-muted bg-bg-void border-border-dim">
                  {detailOrder.source}
                </span>
              )}
            </div>

            {/* Items table */}
            {detailOrder.items && detailOrder.items.length > 0 && (
              <>
                <h3 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-3">Items</h3>
                <table className="w-full text-sm mb-6">
                  <thead>
                    <tr className="border-b border-border-dim">
                      <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase">Product</th>
                      <th className="text-center px-3 py-2 font-mono text-xs text-text-faint uppercase">Qty</th>
                      <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase">Rate</th>
                      <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase">GST</th>
                      <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailOrder.items.map((item) => (
                      <tr key={item.id} className="border-b border-border-dim/50">
                        <td className="px-3 py-2.5">
                          <div className="text-text-main text-sm">{item.product_name || "—"}</div>
                          <div className="text-xs text-text-faint font-mono">{item.sku}</div>
                        </td>
                        <td className="px-3 py-2.5 text-center font-mono">{item.quantity}</td>
                        <td className="px-3 py-2.5 text-right font-mono">{formatCurrency(item.unit_price)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-text-muted">{item.gst_rate}%</td>
                        <td className="px-3 py-2.5 text-right font-mono">{formatCurrency(item.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-border-dim">
                      <td colSpan={4} className="px-3 py-2.5 text-right font-mono text-sm text-text-muted">Subtotal</td>
                      <td className="px-3 py-2.5 text-right font-mono">
                        {formatCurrency(detailOrder.total_amount - detailOrder.total_gst)}
                      </td>
                    </tr>
                    <tr>
                      <td colSpan={4} className="px-3 py-2.5 text-right font-mono text-sm text-text-muted">GST</td>
                      <td className="px-3 py-2.5 text-right font-mono">+{formatCurrency(detailOrder.total_gst)}</td>
                    </tr>
                    {detailOrder.discount_amount > 0 && (
                      <tr>
                        <td colSpan={4} className="px-3 py-2.5 text-right font-mono text-sm text-text-muted">Discount</td>
                        <td className="px-3 py-2.5 text-right font-mono text-red-400">-{formatCurrency(detailOrder.discount_amount)}</td>
                      </tr>
                    )}
                    <tr className="border-t-2 border-emerald-500/30">
                      <td colSpan={4} className="px-3 py-2.5 text-right font-mono text-sm text-emerald-400 font-bold">Total</td>
                      <td className="px-3 py-2.5 text-right font-mono text-emerald-400 font-bold">
                        {formatCurrency(detailOrder.total_amount)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </>
            )}

            {detailOrder.notes && (
              <div className="mb-6">
                <h3 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-2">Notes</h3>
                <p className="text-sm text-text-muted bg-bg-void rounded-xl p-4 border border-border-dim">
                  {detailOrder.notes}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-3">
              {detailOrder.status === "pending" && (
                <>
                  <button
                    onClick={() => {
                      handleStatusChange(detailOrder.id, "confirmed");
                      setDetailOrder(null);
                    }}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors"
                  >
                    Confirm Order
                  </button>
                  <button
                    onClick={() => {
                      handleStatusChange(detailOrder.id, "delivered");
                      setDetailOrder(null);
                    }}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-xl transition-colors"
                  >
                    Mark Delivered
                  </button>
                </>
              )}
              <button
                onClick={() => setDetailOrder(null)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Confirmation */}
      {confirmCancel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-sm mx-4 text-center">
            <div className="text-3xl mb-3 text-red-400">⚠</div>
            <h2 className="text-lg font-bold text-titanium mb-2">Cancel Order?</h2>
            <p className="text-text-muted text-sm mb-6">
              This will restore inventory and reverse any credit balances.
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => setConfirmCancel(null)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Keep
              </button>
              <button
                onClick={() => handleCancel(confirmCancel)}
                className="px-5 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-medium rounded-xl transition-colors"
              >
                Cancel Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
