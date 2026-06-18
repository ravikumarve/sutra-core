"use client";

import { useDashboardKPI, getKpiCards } from "@/lib/hooks";
import { KPICard } from "@/components/dashboard/kpi-card";
import { RecentOrders } from "@/components/dashboard/recent-orders";
import { InventoryAlerts } from "@/components/dashboard/inventory-alerts";

/** Decode JWT payload from the sutra_token cookie to get tenant_id */
function getTenantIdFromToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)sutra_token=([^;]+)/);
  if (!match) return null;
  try {
    const payload = JSON.parse(atob(match[1].split(".")[1]));
    return payload.tenant_id || null;
  } catch {
    return null;
  }
}

export default function DashboardOverview() {
  const tenantId = getTenantIdFromToken() || "";
  const { data, loading, error } = useDashboardKPI(tenantId);
  const kpiCards = getKpiCards(data);

  const cardIcons = ["📦", "₹", "⟐", "⚠"];

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-400 text-lg font-mono mb-2">⚠ Connection Error</p>
          <p className="text-text-muted text-sm">{error}</p>
          <p className="text-text-faint text-xs mt-4">
            Make sure the backend server is running at{" "}
            <code className="text-emerald">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-titanium">Dashboard Overview</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          {loading
            ? "Loading analytics..."
            : data
              ? `Real-time analytics for your SUTRA Core instance`
              : "No data available yet"}
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-4 gap-5 max-xl:grid-cols-2 max-md:grid-cols-1">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="bg-bg-surface border border-border-dim rounded-xl p-6 animate-pulse"
              >
                <div className="h-3 w-20 bg-bg-panel rounded mb-4" />
                <div className="h-8 w-32 bg-bg-panel rounded mb-2" />
                <div className="h-3 w-24 bg-bg-panel rounded" />
              </div>
            ))
          : kpiCards.map((card, i) => (
              <KPICard
                key={card.label}
                title={card.label}
                value={card.value}
                change={card.change}
                trend={card.trend}
                subtitle={card.subtitle}
                icon={cardIcons[i] || ""}
              />
            ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-[1.5fr_1fr] gap-6 max-lg:grid-cols-1">
        <RecentOrders
          orders={data?.recent_orders ?? []}
          loading={loading}
        />
        <InventoryAlerts
          lowStockItems={data?.low_stock_items ?? []}
          topMovers={data?.top_movers ?? []}
          loading={loading}
        />
      </div>
    </div>
  );
}
