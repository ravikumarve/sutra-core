"use client";

import type { LowStockItem, TopMover } from "@/lib/api";

interface Props {
  lowStockItems: LowStockItem[];
  topMovers: TopMover[];
  loading: boolean;
}

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

function SkeletonRows({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3 p-6">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-10 bg-bg-panel rounded animate-pulse" />
      ))}
    </div>
  );
}

export function InventoryAlerts({ lowStockItems, topMovers, loading }: Props) {
  return (
    <div className="space-y-6">
      {/* Low stock alerts */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h3 className="text-base font-semibold text-text-main mb-4 flex items-center gap-2">
          <span className="text-amber-400">⚠</span>
          Low Stock Alerts
        </h3>

        {loading ? (
          <SkeletonRows count={3} />
        ) : lowStockItems.length === 0 ? (
          <div className="text-center text-text-muted text-sm py-6">
            All items are above minimum stock levels ✓
          </div>
        ) : (
          <div className="space-y-3">
            {lowStockItems.map((a) => {
              const pct = Math.round((a.remaining / a.threshold) * 100);
              const isCritical = a.remaining < a.threshold * 0.5;

              return (
                <div key={a.sku}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div>
                      <span className="font-mono text-text-faint">{a.sku}</span>
                      <span className="text-text-muted ml-2">{a.name}</span>
                    </div>
                    <span className={isCritical ? "text-red-400 font-mono" : "text-amber-400 font-mono"}>
                      {a.remaining} / {a.threshold} {a.unit}
                    </span>
                  </div>
                  <div className="h-1.5 bg-bg-panel rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        isCritical ? "bg-red-400" : "bg-amber-400"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <a
          href="/dashboard/inventory"
          className="block text-center text-xs font-mono text-emerald mt-4 pt-4 border-t border-border-dim hover:underline"
        >
          Manage Inventory →
        </a>
      </div>

      {/* Top selling items */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h3 className="text-base font-semibold text-text-main mb-4">Top Movers (90 days)</h3>

        {loading ? (
          <SkeletonRows count={3} />
        ) : topMovers.length === 0 ? (
          <div className="text-center text-text-muted text-sm py-6">
            No sales data yet for this period.
          </div>
        ) : (
          <div className="space-y-3">
            {topMovers.map((item) => (
              <div
                key={item.sku}
                className="flex items-center justify-between py-2.5 border-b border-border-dim last:border-b-0"
              >
                <div>
                  <span className="font-mono text-xs text-text-faint">{item.sku}</span>
                  <p className="text-sm text-text-muted">{item.name}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm text-text-main">{item.total_sold} units</p>
                  {item.total_revenue > 0 && (
                    <p className="text-xs text-emerald">{formatCurrency(item.total_revenue)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
