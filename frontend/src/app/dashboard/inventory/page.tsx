export default function InventoryPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-titanium">Inventory</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Stock levels and product analytics
        </p>
      </div>

      <div className="grid grid-cols-3 gap-5 max-md:grid-cols-1">
        {[
          { label: "Total SKUs", value: "342", change: "active products" },
          { label: "Low Stock", value: "3", change: "needs attention" },
          { label: "Out of Stock", value: "0", change: "all stocked" },
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

      <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
        <div className="text-3xl mb-3">⊟</div>
        <p className="text-text-muted text-sm font-light">
          Full inventory dashboard with stock movements, reorder points, and product catalog will be built here.
        </p>
      </div>
    </div>
  );
}
