import { KPICard } from "@/components/dashboard/kpi-card";
import { RecentOrders } from "@/components/dashboard/recent-orders";
import { InventoryAlerts } from "@/components/dashboard/inventory-alerts";

export default function DashboardOverview() {
  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-titanium">Dashboard Overview</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Real-time analytics for your SUTRA Core instance
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-4 gap-5 max-xl:grid-cols-2 max-md:grid-cols-1">
        <KPICard
          title="Total Orders"
          value="1,247"
          change="+12.3%"
          trend="up"
          subtitle="vs last month"
          icon="📦"
        />
        <KPICard
          title="Revenue (MTD)"
          value="₹8,42,500"
          change="+18.7%"
          trend="up"
          subtitle="vs last month"
          icon="₹"
        />
        <KPICard
          title="Udhaar Outstanding"
          value="₹2,31,800"
          change="+5.2%"
          trend="up"
          subtitle="30+ days aging"
          icon="⟐"
        />
        <KPICard
          title="Low Stock Items"
          value="3"
          change="-2"
          trend="down"
          subtitle="needs restock"
          icon="⚠"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-[1.5fr_1fr] gap-6 max-lg:grid-cols-1">
        {/* Recent Orders Table */}
        <RecentOrders />

        {/* Inventory Alerts + Top Movers */}
        <InventoryAlerts />
      </div>
    </div>
  );
}
