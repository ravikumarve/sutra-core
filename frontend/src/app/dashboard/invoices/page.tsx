"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchOrders,
  fetchOrder,
  type Order,
  type OrderListData,
} from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

function statusBadge(status: string): { label: string; color: string } {
  switch (status) {
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

// ── Component ────────────────────────────────────────────────────────────────

export default function InvoicesPage() {
  const [data, setData] = useState<OrderListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("delivered");
  const [detailOrder, setDetailOrder] = useState<Order | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 100 };
      if (statusFilter) params.status = statusFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const result = await fetchOrders(params);
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalInvoices = data?.total ?? 0;
  const totalAmount = data?.items.reduce((s, o) => s + o.total_amount, 0) ?? 0;

  async function openDetail(orderId: string) {
    setDetailLoading(true);
    try {
      const result = await fetchOrder(orderId);
      setDetailOrder(result.order);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setDetailLoading(false);
    }
  }

  function handlePrint() {
    window.print();
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-titanium">Invoices</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          GST-compliant invoices for completed orders
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-5 max-md:grid-cols-1">
        {[
          { label: "Invoices", value: String(totalInvoices), sub: "In selected period" },
          { label: "Total Billed", value: formatCurrency(totalAmount), sub: "Sum of invoice amounts" },
          { label: "Avg Invoice", value: totalInvoices > 0 ? formatCurrency(totalAmount / totalInvoices) : "₹0", sub: "Average order value" },
        ].map((stat) => (
          <div key={stat.label} className="bg-bg-surface border border-border-dim rounded-xl p-5">
            <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
              {stat.label}
            </div>
            <div className="text-2xl font-bold text-text-main font-mono mb-1">{stat.value}</div>
            <div className="text-xs text-text-muted font-light">{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
        >
          <option value="delivered">Delivered</option>
          <option value="confirmed">Confirmed</option>
          <option value="">All Statuses</option>
        </select>

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
          placeholder="From"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
          placeholder="To"
        />
      </div>

      {/* Invoice Table */}
      {loading ? (
        <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
          <p className="text-text-muted text-sm">Loading invoices...</p>
        </div>
      ) : error ? (
        <div className="bg-bg-surface border border-red-500/20 rounded-xl p-12 text-center">
          <p className="text-red-400 text-sm">{error}</p>
          <button onClick={loadData} className="mt-3 text-emerald-400 text-sm hover:underline">Retry</button>
        </div>
      ) : (
        <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dim">
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase">Invoice #</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase">Customer</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase">Date</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase">Amount</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase">GST</th>
                  <th className="text-center px-5 py-3 font-mono text-xs text-text-faint uppercase">Status</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase">Action</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-text-muted text-sm">
                      No invoices found for the selected period.
                    </td>
                  </tr>
                ) : (
                  data?.items.map((order) => {
                    const sb = statusBadge(order.status);
                    return (
                      <tr key={order.id} className="border-b border-border-dim/50 hover:bg-bg-void/50 transition-colors">
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs text-emerald-400">{order.order_number}</span>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="text-text-main font-medium">{order.customer_name || "Walk-in"}</div>
                        </td>
                        <td className="px-5 py-3.5 text-xs text-text-muted">
                          {order.created_at
                            ? new Date(order.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
                            : "—"}
                        </td>
                        <td className="px-5 py-3.5 text-right font-mono text-text-main">{formatCurrency(order.total_amount)}</td>
                        <td className="px-5 py-3.5 text-right font-mono text-text-muted">{formatCurrency(order.total_gst)}</td>
                        <td className="px-5 py-3.5 text-center">
                          <span className={`inline-block px-2 py-1 rounded-lg text-xs font-mono border ${sb.color}`}>
                            {sb.label}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <button
                            onClick={() => openDetail(order.id)}
                            className="px-3 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-emerald-400 hover:border-emerald-500/30 transition-colors"
                          >
                            View Invoice
                          </button>
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

      {/* Invoice Detail Modal (print-friendly) */}
      {detailOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm print:bg-white print:text-black">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto print:shadow-none print:border-none print:max-h-none print:rounded-none print:p-4">
            {/* Invoice Header */}
            <div className="flex items-start justify-between mb-8 print:mb-4">
              <div>
                <h2 className="text-xl font-bold text-titanium print:text-black">SUTRA Core</h2>
                <p className="text-xs text-text-muted print:text-gray-600 mt-0.5">GST Invoice</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold font-mono text-titanium print:text-black">{detailOrder.order_number}</div>
                <div className="text-xs text-text-muted print:text-gray-600 mt-0.5">
                  {detailOrder.created_at
                    ? new Date(detailOrder.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit", month: "short", year: "numeric",
                      })
                    : ""}
                </div>
              </div>
            </div>

            {/* Bill To */}
            <div className="mb-6 print:mb-3">
              <h3 className="text-xs font-mono text-text-faint uppercase tracking-wider mb-1 print:text-gray-500">Bill To</h3>
              <p className="text-sm text-text-main font-medium print:text-black">
                {detailOrder.customer_name || "Walk-in Customer"}
              </p>
              {detailOrder.customer_phone && (
                <p className="text-xs text-text-muted font-mono print:text-gray-600">{detailOrder.customer_phone}</p>
              )}
            </div>

            {/* Line Items */}
            {detailOrder.items && (
              <table className="w-full text-sm mb-6 print:mb-3">
                <thead>
                  <tr className="border-b border-border-dim print:border-gray-300">
                    <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">#</th>
                    <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">Product</th>
                    <th className="text-center px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">Qty</th>
                    <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">Rate</th>
                    <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">GST</th>
                    <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase print:text-gray-500">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {detailOrder.items.map((item, idx) => (
                    <tr key={item.id} className="border-b border-border-dim/50 print:border-gray-200">
                      <td className="px-3 py-2 text-xs text-text-muted print:text-gray-500">{idx + 1}</td>
                      <td className="px-3 py-2">
                        <div className="text-text-main text-sm print:text-black">{item.product_name || "—"}</div>
                        <div className="text-xs text-text-faint font-mono print:text-gray-400">{item.sku}</div>
                      </td>
                      <td className="px-3 py-2 text-center font-mono text-text-main print:text-black">{item.quantity}</td>
                      <td className="px-3 py-2 text-right font-mono text-text-main print:text-black">{formatCurrency(item.unit_price)}</td>
                      <td className="px-3 py-2 text-right font-mono text-text-muted print:text-gray-600">{item.gst_rate}%</td>
                      <td className="px-3 py-2 text-right font-mono text-text-main print:text-black">{formatCurrency(item.total_amount)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-border-dim print:border-gray-300">
                    <td colSpan={5} className="px-3 py-2 text-right font-mono text-sm text-text-muted print:text-gray-600">Subtotal</td>
                    <td className="px-3 py-2 text-right font-mono text-text-main print:text-black">
                      {formatCurrency(detailOrder.total_amount - detailOrder.total_gst)}
                    </td>
                  </tr>
                  <tr>
                    <td colSpan={5} className="px-3 py-2 text-right font-mono text-sm text-text-muted print:text-gray-600">GST</td>
                    <td className="px-3 py-2 text-right font-mono text-text-muted print:text-gray-600">+{formatCurrency(detailOrder.total_gst)}</td>
                  </tr>
                  {detailOrder.discount_amount > 0 && (
                    <tr>
                      <td colSpan={5} className="px-3 py-2 text-right font-mono text-sm text-text-muted print:text-gray-600">Discount</td>
                      <td className="px-3 py-2 text-right font-mono text-red-400 print:text-red-600">-{formatCurrency(detailOrder.discount_amount)}</td>
                    </tr>
                  )}
                  <tr className="border-t-2 border-emerald-500/30 print:border-gray-800">
                    <td colSpan={5} className="px-3 py-3 text-right font-mono text-sm font-bold text-emerald-400 print:text-black">
                      Total (incl. GST)
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-emerald-400 print:text-black">
                      {formatCurrency(detailOrder.total_amount)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            )}

            {/* Payment Info */}
            <div className="grid grid-cols-2 gap-6 text-sm mb-6 print:mb-3 print:text-xs">
              <div>
                <span className="text-text-faint print:text-gray-500">Payment Method:</span>
                <span className="ml-2 text-text-main capitalize print:text-black">{detailOrder.payment_method}</span>
              </div>
              <div>
                <span className="text-text-faint print:text-gray-500">Payment Status:</span>
                <span className="ml-2 text-text-main capitalize print:text-black">{detailOrder.payment_status}</span>
              </div>
            </div>

            {detailOrder.notes && (
              <div className="mb-6">
                <p className="text-sm text-text-muted italic print:text-gray-600">"{detailOrder.notes}"</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 print:hidden">
              <button
                onClick={handlePrint}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                🖨 Print
              </button>
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
    </div>
  );
}
