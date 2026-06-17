export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-titanium">Settings</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Tenant configuration and account management
        </p>
      </div>

      {/* Profile */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-8">
        <h2 className="text-lg font-semibold text-text-main mb-6">Profile</h2>
        <div className="grid grid-cols-2 gap-6 max-md:grid-cols-1">
          {[
            { label: "Name", value: "Admin User" },
            { label: "Email", value: "admin@sutra.local" },
            { label: "Tenant ID", value: "sharma_textiles_01" },
            { label: "Plan", value: "Growth (₹1,499/mo)" },
          ].map((field) => (
            <div key={field.label}>
              <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-1">
                {field.label}
              </div>
              <div className="text-sm text-text-main bg-bg-void border border-border-dim rounded-lg px-4 py-2.5">
                {field.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Integration status */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-8">
        <h2 className="text-lg font-semibold text-text-main mb-6">Integrations</h2>
        <div className="space-y-4">
          {[
            { name: "WhatsApp Cloud API", status: "Connected", color: "text-emerald" },
            { name: "PostgreSQL Database", status: "Connected", color: "text-emerald" },
            { name: "Redis Streams", status: "Connected", color: "text-emerald" },
            { name: "Gumroad Payments", status: "Configured", color: "text-amber-400" },
          ].map((int) => (
            <div
              key={int.name}
              className="flex items-center justify-between py-3 border-b border-border-dim last:border-b-0"
            >
              <span className="text-sm text-text-main">{int.name}</span>
              <span className={`text-xs font-mono ${int.color}`}>● {int.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
