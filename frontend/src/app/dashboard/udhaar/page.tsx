export default function UdhaarPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-titanium">Udhaar / Credit</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Customer credit tracking and aging analysis
        </p>
      </div>

      <div className="grid grid-cols-3 gap-5 max-md:grid-cols-1">
        {[
          { label: "Total Outstanding", value: "₹2,31,800", change: "across 12 customers" },
          { label: "30+ Days Aging", value: "₹42,500", change: "3 accounts overdue" },
          { label: "Avg. Credit Limit", value: "₹35,000", change: "per customer" },
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
        <div className="text-3xl mb-3">⟐</div>
        <p className="text-text-muted text-sm font-light">
          Credit aging report, payment reminders, and customer credit limit management will be built here.
        </p>
      </div>
    </div>
  );
}
