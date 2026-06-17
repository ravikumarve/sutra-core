import Link from "next/link";

const navItems = [
  { label: "Overview", href: "/dashboard", icon: "◈" },
  { label: "Orders", href: "/dashboard/orders", icon: "⊞" },
  { label: "Inventory", href: "/dashboard/inventory", icon: "⊟" },
  { label: "Udhaar", href: "/dashboard/udhaar", icon: "⟐" },
  { label: "Invoices", href: "/dashboard/invoices", icon: "⊡" },
  { label: "Settings", href: "/dashboard/settings", icon: "⚙" },
];

export function DashboardSidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 z-20 bg-bg-surface border-r border-border-dim flex flex-col max-lg:hidden">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-border-dim">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 text-lg font-bold text-text-main no-underline"
        >
          <div className="w-3.5 h-3.5 border-2 border-emerald rounded-full shadow-[0_0_10px_var(--emerald-dim)]" />
          SUTRA Core
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 px-4 py-2.5 text-sm text-text-muted rounded-lg no-underline transition-all duration-200 hover:bg-bg-panel hover:text-text-main"
          >
            <span className="text-emerald text-base w-5 text-center">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-5 border-t border-border-dim">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-bg-panel border border-border-dim flex items-center justify-center text-xs font-mono text-text-muted">
            A
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text-main truncate">Admin User</p>
            <p className="text-xs text-text-muted truncate">
              admin@sutra.local
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
