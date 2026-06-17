const alerts = [
  { sku: "SILK_RED", item: "Silk Saree (Red)", remaining: 12, threshold: 20, unit: "pieces" },
  { sku: "PVC_1INCH", item: "PVC Pipe 1inch", remaining: 45, threshold: 50, unit: "pieces" },
  { sku: "BAS_RICE_25", item: "Basmati Rice 25kg", remaining: 3, threshold: 10, unit: "bags" },
];

const topItems = [
  { sku: "COT_BLUE_M", item: "Cotton Fabric (Blue)", sold: 340, revenue: "₹1,02,000", change: "+12%" },
  { sku: "SILK_RED", item: "Silk Saree (Red)", sold: 280, revenue: "₹6,97,200", change: "+8%" },
  { sku: "LED_12W", item: "LED Bulb 12W", sold: 195, revenue: "₹87,750", change: "+23%" },
];

export function InventoryAlerts() {
  return (
    <div className="space-y-6">
      {/* Low stock alerts */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h3 className="text-base font-semibold text-text-main mb-4 flex items-center gap-2">
          <span className="text-amber-400">⚠</span>
          Low Stock Alerts
        </h3>

        <div className="space-y-3">
          {alerts.map((a) => {
            const pct = Math.round((a.remaining / a.threshold) * 100);
            const isCritical = a.remaining < a.threshold * 0.5;

            return (
              <div key={a.sku}>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div>
                    <span className="font-mono text-text-faint">{a.sku}</span>
                    <span className="text-text-muted ml-2">{a.item}</span>
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

        <a
          href="/dashboard/inventory"
          className="block text-center text-xs font-mono text-emerald mt-4 pt-4 border-t border-border-dim hover:underline"
        >
          Manage Inventory →
        </a>
      </div>

      {/* Top selling items */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h3 className="text-base font-semibold text-text-main mb-4">Top Movers</h3>

        <div className="space-y-3">
          {topItems.map((item) => (
            <div
              key={item.sku}
              className="flex items-center justify-between py-2.5 border-b border-border-dim last:border-b-0"
            >
              <div>
                <span className="font-mono text-xs text-text-faint">{item.sku}</span>
                <p className="text-sm text-text-muted">{item.item}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm text-text-main">{item.sold} units</p>
                <p className="text-xs text-emerald">{item.change}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
