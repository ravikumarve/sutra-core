"use client";

import { useState } from "react";
import Link from "next/link";

const navItems = [
  { label: "Overview", href: "/dashboard", icon: "◈" },
  { label: "Orders", href: "/dashboard/orders", icon: "⊞" },
  { label: "Inventory", href: "/dashboard/inventory", icon: "⊟" },
  { label: "Udhaar", href: "/dashboard/udhaar", icon: "⟐" },
  { label: "Invoices", href: "/dashboard/invoices", icon: "⊡" },
  { label: "Settings", href: "/dashboard/settings", icon: "⚙" },
];

export function DashboardHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 bg-bg-surface/80 backdrop-blur-xl border-b border-border-dim">
      <div className="flex items-center justify-between px-8 py-4 max-lg:px-5">
        {/* Mobile menu toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="hidden max-lg:flex items-center justify-center w-10 h-10 rounded-lg border border-border-dim text-text-muted hover:text-text-main hover:bg-bg-panel transition-colors"
          aria-label="Toggle menu"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>

        {/* Page title area (slot for dynamic breadcrumb) */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs text-text-muted font-mono hover:text-emerald transition-colors"
          >
            ← Back to Site
          </Link>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Status indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-dim border border-emerald/20 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald animate-pulse" />
            <span className="font-mono text-[0.65rem] text-emerald uppercase tracking-wider">
              System Nominal
            </span>
          </div>

          {/* User avatar (desktop) */}
          <div className="w-9 h-9 rounded-full bg-bg-panel border border-border-dim flex items-center justify-center text-sm font-mono text-text-muted max-lg:hidden">
            A
          </div>
        </div>
      </div>

      {/* Mobile nav drawer */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-border-dim bg-bg-surface">
          <nav className="px-3 py-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-sm text-text-muted rounded-lg no-underline transition-all duration-200 hover:bg-bg-panel hover:text-text-main"
              >
                <span className="text-emerald text-base w-5 text-center">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
