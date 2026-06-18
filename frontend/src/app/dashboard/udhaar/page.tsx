"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  fetchCustomerLedger,
  fetchDashboardKpi,
  type Customer,
  type CustomerListData,
  type LedgerEntry,
} from "@/lib/api";
import { getKpiCards } from "@/lib/hooks";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function UdhaarPage() {
  // Data state
  const [data, setData] = useState<CustomerListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpiData, setKpiData] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [balanceFilter, setBalanceFilter] = useState<string>("all");

  // Create/Edit modal
  const [showForm, setShowForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [formPhone, setFormPhone] = useState("");
  const [formName, setFormName] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formCreditLimit, setFormCreditLimit] = useState("");
  const [saving, setSaving] = useState(false);

  // Detail view (for ledger)
  const [detailCustomer, setDetailCustomer] = useState<Customer | null>(null);
  const [ledgerEntries, setLedgerEntries] = useState<LedgerEntry[]>([]);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  // Delete confirmation
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  // ── Data Load ──

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 200 };
      if (search) params.search = search;
      if (balanceFilter === "debt") params.has_balance = true;
      else if (balanceFilter === "clear") params.has_balance = false;

      const result = await fetchCustomers(params);
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, balanceFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load KPI for stats
  useEffect(() => {
    // Try to get tenant_id from cookie for KPI fetch
    const match = document.cookie.match(/sutra_token=([^;]+)/);
    if (!match) return;
    try {
      const payload = JSON.parse(atob(match[1].split(".")[1]));
      const tenantId = payload.tenant_id;
      if (tenantId) {
        fetchDashboardKpi(tenantId, 30)
          .then((d) => setKpiData(d))
          .catch(() => {});
      }
    } catch {
      // Ignore parse errors — KPI is optional
    }
  }, []);

  // ── Stats ──
  const totalCustomers = data?.total ?? 0;
  const totalBalance =
    data?.items ? data.items.reduce((s, c) => s + c.current_balance, 0) : 0;
  const debtCustomers = data?.items ? data.items.filter((c) => c.current_balance > 0).length : 0;
  const avgCreditLimit =
    totalCustomers > 0 && data?.items
      ? data.items.reduce((s, c) => s + c.credit_limit, 0) / totalCustomers
      : 0;

  // Udhaar-specific KPI from dashboard if available
  const udhaarKpi = kpiData?.kpi?.udhaar_outstanding;

  // ── Form handlers ──

  function openCreate() {
    setEditingCustomer(null);
    setFormPhone("");
    setFormName("");
    setFormAddress("");
    setFormCreditLimit("");
    setShowForm(true);
  }

  function openEdit(c: Customer) {
    setEditingCustomer(c);
    setFormPhone(c.phone_number);
    setFormName(c.name || "");
    setFormAddress(c.address || "");
    setFormCreditLimit(String(c.credit_limit));
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const payload: any = {
        phone_number: formPhone,
        name: formName || undefined,
        address: formAddress || undefined,
        credit_limit: parseFloat(formCreditLimit || "0"),
      };

      if (editingCustomer) {
        await updateCustomer(editingCustomer.id, payload);
      } else {
        await createCustomer(payload);
      }

      setShowForm(false);
      await loadData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteCustomer(id);
      setConfirmDelete(null);
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function openLedger(c: Customer) {
    setDetailCustomer(c);
    setLedgerLoading(true);
    try {
      const result = await fetchCustomerLedger(c.id, { limit: 50 });
      setLedgerEntries(result.entries);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLedgerLoading(false);
    }
  }

  // ── Render ──

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-titanium">Udhaar / Credit</h1>
          <p className="text-text-muted text-sm font-light mt-1">
            Customer credit tracking and ledger management
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-xl transition-colors"
        >
          + Add Customer
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-5 max-md:grid-cols-2 max-sm:grid-cols-1">
        {[
          { label: "Total Customers", value: String(totalCustomers), sub: "Registered customers" },
          {
            label: "Udhaar Outstanding",
            value: formatCurrency(udhaarKpi?.value ?? totalBalance),
            sub: `${udhaarKpi?.customers_with_debt ?? debtCustomers} customers with balance`,
            warn: (udhaarKpi?.value ?? totalBalance) > 0,
          },
          {
            label: "Avg Credit Limit",
            value: formatCurrency(avgCreditLimit),
            sub: "Per customer limit",
          },
          {
            label: "Total Credit Limit",
            value: formatCurrency(data?.items ? data.items.reduce((s, c) => s + c.credit_limit, 0) : 0),
            sub: "Combined customer limits",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className={`bg-bg-surface border rounded-xl p-5 ${
              stat.warn ? "border-amber-500/30" : "border-border-dim"
            }`}
          >
            <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
              {stat.label}
            </div>
            <div
              className={`text-2xl font-bold font-mono mb-1 ${
                stat.warn ? "text-amber-400" : "text-text-main"
              }`}
            >
              {stat.value}
            </div>
            <div className="text-xs text-text-muted font-light">{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Search + Filter */}
      <div className="flex gap-4 items-center max-sm:flex-col">
        <div className="relative flex-1 max-w-md">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-faint text-sm">⊖</span>
          <input
            type="text"
            placeholder="Search by name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main placeholder:text-text-faint focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
        <select
          value={balanceFilter}
          onChange={(e) => setBalanceFilter(e.target.value)}
          className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
        >
          <option value="all">All Customers</option>
          <option value="debt">Has Balance</option>
          <option value="clear">Zero Balance</option>
        </select>
      </div>

      {/* Customer Table */}
      {loading ? (
        <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
          <p className="text-text-muted text-sm">Loading customers...</p>
        </div>
      ) : error ? (
        <div className="bg-bg-surface border border-red-500/20 rounded-xl p-12 text-center">
          <p className="text-red-400 text-sm">{error}</p>
          <button onClick={loadData} className="mt-3 text-emerald-400 text-sm hover:underline">
            Retry
          </button>
        </div>
      ) : (
        <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dim">
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Name</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Phone</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Orders</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Balance</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Limit</th>
                  <th className="text-center px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Status</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-text-muted text-sm">
                      No customers found. Click &quot;Add Customer&quot; to register one.
                    </td>
                  </tr>
                ) : (
                  data?.items.map((customer) => (
                    <tr
                      key={customer.id}
                      className="border-b border-border-dim/50 hover:bg-bg-void/50 transition-colors"
                    >
                      <td className="px-5 py-3.5">
                        <div className="text-text-main font-medium">
                          {customer.name || "—"}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="font-mono text-xs text-text-muted">
                          {customer.phone_number}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right font-mono text-text-main">
                        {customer.total_orders ?? 0}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <span
                          className={`font-mono ${
                            customer.current_balance > 0
                              ? "text-amber-400"
                              : "text-emerald-400"
                          }`}
                        >
                          {formatCurrency(customer.current_balance)}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right font-mono text-text-muted">
                        {formatCurrency(customer.credit_limit)}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-lg text-xs font-mono border ${
                            customer.is_active
                              ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                              : "text-text-faint bg-bg-void border-border-dim"
                          }`}
                        >
                          {customer.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openLedger(customer)}
                            className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-emerald-400 hover:border-emerald-500/30 transition-colors"
                          >
                            Ledger
                          </button>
                          <button
                            onClick={() => openEdit(customer)}
                            className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-titanium hover:border-titanium/30 transition-colors"
                          >
                            ✎ Edit
                          </button>
                          <button
                            onClick={() => setConfirmDelete(customer.id)}
                            className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-red-400 hover:border-red-500/30 transition-colors"
                          >
                            ✕
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-lg mx-4">
            <h2 className="text-lg font-bold text-titanium mb-1">
              {editingCustomer ? "Edit Customer" : "Add Customer"}
            </h2>
            <p className="text-text-muted text-xs mb-6 font-light">
              {editingCustomer
                ? `Editing: ${editingCustomer.name || editingCustomer.phone_number}`
                : "Register a new customer for credit tracking"}
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Phone Number *</label>
                <input
                  value={formPhone}
                  onChange={(e) => setFormPhone(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="+919876543210"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Name</label>
                <input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="Customer name (optional)"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Credit Limit (₹)</label>
                <input
                  type="number"
                  value={formCreditLimit}
                  onChange={(e) => setFormCreditLimit(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="e.g. 50000"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Address</label>
                <textarea
                  value={formAddress}
                  onChange={(e) => setFormAddress(e.target.value)}
                  rows={2}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50 resize-none"
                  placeholder="Optional address"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => setShowForm(false)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formPhone}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
              >
                {saving ? "Saving..." : editingCustomer ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ledger Detail Modal */}
      {detailCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-2xl mx-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-titanium">{detailCustomer.name || "Customer"}</h2>
                <p className="text-text-muted text-xs font-mono mt-1">{detailCustomer.phone_number}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold font-mono text-amber-400">
                  {formatCurrency(detailCustomer.current_balance)}
                </div>
                <div className="text-xs text-text-faint">Outstanding</div>
              </div>
            </div>

            {detailCustomer.address && (
              <p className="text-sm text-text-muted mb-4">{detailCustomer.address}</p>
            )}

            <h3 className="text-sm font-mono text-text-faint uppercase tracking-wider mb-3">Credit Ledger</h3>

            {ledgerLoading ? (
              <p className="text-text-muted text-sm py-4">Loading ledger...</p>
            ) : ledgerEntries.length === 0 ? (
              <p className="text-text-muted text-sm py-4">No ledger entries found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-dim">
                      <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase">Date</th>
                      <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase">Type</th>
                      <th className="text-left px-3 py-2 font-mono text-xs text-text-faint uppercase">Description</th>
                      <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase">Amount</th>
                      <th className="text-right px-3 py-2 font-mono text-xs text-text-faint uppercase">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ledgerEntries.map((entry) => (
                      <tr key={entry.id} className="border-b border-border-dim/50">
                        <td className="px-3 py-2.5 text-xs text-text-muted font-mono">
                          {entry.created_at ? new Date(entry.created_at).toLocaleDateString("en-IN") : "—"}
                        </td>
                        <td className="px-3 py-2.5">
                          <span className="text-xs font-mono capitalize text-text-main">{entry.transaction_type}</span>
                        </td>
                        <td className="px-3 py-2.5 text-xs text-text-muted">
                          {entry.description || "—"}
                        </td>
                        <td className={`px-3 py-2.5 text-right font-mono text-sm ${
                          entry.amount >= 0 ? "text-emerald-400" : "text-red-400"
                        }`}>
                          {entry.amount >= 0 ? "+" : ""}{formatCurrency(entry.amount)}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono text-sm text-text-main">
                          {formatCurrency(entry.balance_after)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-end mt-6">
              <button
                onClick={() => setDetailCustomer(null)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-sm mx-4 text-center">
            <div className="text-3xl mb-3 text-red-400">⚠</div>
            <h2 className="text-lg font-bold text-titanium mb-2">Deactivate Customer?</h2>
            <p className="text-text-muted text-sm mb-6">
              This will deactivate the customer. Historical ledger data will be preserved.
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="px-5 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-medium rounded-xl transition-colors"
              >
                Deactivate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
