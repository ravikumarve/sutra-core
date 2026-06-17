export default function OrdersPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-titanium">Orders</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Order analytics and history
        </p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-5 max-md:grid-cols-1">
        {[
          { label: "Today", value: "24", change: "+3 vs yesterday" },
          { label: "This Week", value: "187", change: "+12% vs last week" },
          { label: "Avg. Order Value", value: "₹675", change: "+5.2% vs last month" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-bg-surface border border-border-dim rounded-xl p-6"
          >
            <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
              {stat.label}
            </div>
            <div className="text-2xl font-bold text-text-main font-mono mb-1">{stat.value}</div>
            <div className="text-xs text-text-muted font-light">{stat.change}</div>
          </div>
        ))}
      </div>

      {/* Placeholder for full order table */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
        <div className="text-3xl mb-3">⊞</div>
        <p className="text-text-muted text-sm font-light">
          Full order management with filtering, search, and export will be built here.
        </p>
      </div>
    </div>
  );
}
