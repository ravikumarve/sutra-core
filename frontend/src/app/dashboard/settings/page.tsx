"use client";

import { useState, useEffect } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

interface UserInfo {
  user_id: string;
  tenant_id: string;
  phone_number: string;
  role: string;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Decode JWT from cookie
    const match = document.cookie.match(/sutra_token=([^;]+)/);
    if (!match) return;
    try {
      const payload = JSON.parse(atob(match[1].split(".")[1]));
      setUser({
        user_id: payload.user_id || "—",
        tenant_id: payload.tenant_id || "—",
        phone_number: payload.phone_number || "—",
        role: payload.role || "—",
      });
    } catch {
      // Ignore parse errors
    }
  }, []);

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-titanium">Settings</h1>
        <p className="text-text-muted text-sm font-light mt-1">
          Account and integration configuration
        </p>
      </div>

      {/* Profile */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h2 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-4">Profile</h2>
        {user ? (
          <div className="space-y-3">
            {[
              { label: "User ID", value: user.user_id },
              { label: "Tenant ID", value: user.tenant_id },
              { label: "Phone", value: user.phone_number },
              { label: "Role", value: user.role },
            ].map((field) => (
              <div key={field.label} className="flex items-center justify-between py-2 border-b border-border-dim/50 last:border-0">
                <span className="text-sm text-text-muted">{field.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-main font-mono">{field.value}</span>
                  <button
                    onClick={() => copyToClipboard(field.value)}
                    className="text-xs text-text-faint hover:text-emerald-400 transition-colors"
                  >
                    {copied ? "✓" : "⊡"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-text-muted">Not logged in</p>
        )}
      </div>

      {/* Integrations */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h2 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-4">Integrations</h2>
        <div className="space-y-4">
          {[
            { name: "WhatsApp Business API", status: "Not Configured", desc: "Connect your Meta WhatsApp Business Account for automated order processing", color: "text-amber-400" },
            { name: "Razorpay", status: "Coming Soon", desc: "Accept payments via UPI, cards, and net banking", color: "text-text-faint" },
            { name: "GST Portal", status: "Coming Soon", desc: "Auto-file GST returns and generate e-invoices", color: "text-text-faint" },
            { name: "Email Notifications", status: "Coming Soon", desc: "Send invoices and order confirmations via email", color: "text-text-faint" },
          ].map((integration) => (
            <div key={integration.name} className="flex items-center justify-between py-3 border-b border-border-dim/50 last:border-0">
              <div>
                <div className="text-sm text-text-main font-medium">{integration.name}</div>
                <div className="text-xs text-text-muted mt-0.5">{integration.desc}</div>
              </div>
              <span className={`text-xs font-mono px-2.5 py-1 rounded-lg border ${integration.color} ${integration.color.includes("text-amber") ? "bg-amber-500/10 border-amber-500/20" : "bg-bg-void border-border-dim"}`}>
                {integration.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* App Info */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-6">
        <h2 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-4">Application Info</h2>
        <div className="space-y-3">
          {[
            { label: "Version", value: "1.0.0" },
            { label: "Frontend", value: "Next.js 16.2.9" },
            { label: "Backend", value: "FastAPI + Python 3.12" },
            { label: "Database", value: "PostgreSQL 15 (dev: SQLite)" },
            { label: "Design", value: "LP6 — Abyssal Tech" },
          ].map((info) => (
            <div key={info.label} className="flex items-center justify-between py-2 border-b border-border-dim/50 last:border-0">
              <span className="text-sm text-text-muted">{info.label}</span>
              <span className="text-sm text-text-main font-mono">{info.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-bg-surface border border-red-500/20 rounded-xl p-6">
        <h2 className="text-sm font-mono text-red-400 uppercase tracking-wider mb-4">Danger Zone</h2>
        <p className="text-sm text-text-muted mb-4">
          Irreversible actions. These cannot be undone.
        </p>
        <button
          disabled
          className="px-5 py-2.5 bg-red-600/50 text-white/50 text-sm font-medium rounded-xl cursor-not-allowed"
          title="Coming soon"
        >
          Delete Account
        </button>
      </div>
    </div>
  );
}
