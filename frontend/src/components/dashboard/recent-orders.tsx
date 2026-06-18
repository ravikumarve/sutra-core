"use client";

import type { RecentOrder } from "@/lib/api";

interface Props {
  orders: RecentOrder[];
  loading: boolean;
}

const statusStyles: Record<string, string> = {
  confirmed: "bg-emerald-dim text-emerald border-emerald/20",
  delivered: "bg-emerald-dim text-emerald border-emerald/20",
  processing: "bg-[rgba(0,240,255,0.08)] text-cyan-400 border-cyan-400/20",
  pending: "bg-[rgba(245,158,11,0.08)] text-amber-400 border-amber-400/20",
  cancelled: "bg-[rgba(239,68,68,0.08)] text-red-400 border-red-400/20",
};

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function Skeleton() {
  return (
    <div className="space-y-3 p-6">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-10 bg-bg-panel rounded animate-pulse" />
      ))}
    </div>
  );
}

export function RecentOrders({ orders, loading }: Props) {
  return (
    <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
      <div className="px-6 py-5 border-b border-border-dim flex items-center justify-between">
        <h3 className="text-base font-semibold text-text-main">Recent Orders</h3>
        <a href="/dashboard/orders" className="text-xs font-mono text-emerald hover:underline">
          View all →
        </a>
      </div>

      {loading ? (
        <Skeleton />
      ) : orders.length === 0 ? (
        <div className="px-6 py-10 text-center text-text-muted text-sm">
          No orders yet. Orders will appear here once customers start placing them via WhatsApp.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-dim">
                <th className="text-left px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                  Order
                </th>
                <th className="text-left px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                  Customer
                </th>
                <th className="text-right px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                  Amount
                </th>
                <th className="text-right px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr
                  key={order.id}
                  className="border-b border-border-dim last:border-b-0 hover:bg-bg-panel/50 transition-colors"
                >
                  <td className="px-6 py-4 font-mono text-text-main text-xs">
                    {order.order_number}
                  </td>
                  <td className="px-6 py-4 text-text-main">{order.customer_name}</td>
                  <td className="px-6 py-4 text-right font-mono text-text-main text-sm">
                    {formatCurrency(order.total_amount)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-full text-[0.65rem] font-mono font-medium border ${
                        statusStyles[order.status] || "bg-text-muted/10 text-text-muted"
                      }`}
                    >
                      {order.status}
                    </span>
                    <div className="text-[0.6rem] text-text-faint mt-0.5">
                      {timeAgo(order.created_at)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
