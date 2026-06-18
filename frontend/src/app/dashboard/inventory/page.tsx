"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchInventory,
  createInventoryItem,
  updateInventoryItem,
  deleteInventoryItem,
  adjustStock,
  fetchInventoryCategories,
  type InventoryItem,
  type InventoryListData,
} from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

interface FormState {
  sku: string;
  name: string;
  description: string;
  category: string;
  unit: string;
  purchase_price: string;
  selling_price: string;
  gst_rate: string;
  quantity: string;
  min_stock_level: string;
}

const EMPTY_FORM: FormState = {
  sku: "",
  name: "",
  description: "",
  category: "",
  unit: "pieces",
  purchase_price: "",
  selling_price: "",
  gst_rate: "12",
  quantity: "0",
  min_stock_level: "10",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}

function stockStatus(item: InventoryItem): "ok" | "low" | "out" {
  if (item.quantity <= 0) return "out";
  if (item.quantity < item.min_stock_level) return "low";
  return "ok";
}

function statusColor(status: "ok" | "low" | "out"): string {
  switch (status) {
    case "out": return "text-red-400 bg-red-500/10 border-red-500/20";
    case "low": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "ok": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  }
}

function statusLabel(status: "ok" | "low" | "out"): string {
  switch (status) {
    case "out": return "Out of Stock";
    case "low": return "Low Stock";
    case "ok": return "In Stock";
  }
}

// ── Component ────────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const [data, setData] = useState<InventoryListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [stockAdjust, setStockAdjust] = useState<{ id: string; name: string } | null>(null);
  const [stockQty, setStockQty] = useState("");
  const [stockReason, setStockReason] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchInventory({
        search: search || undefined,
        category: categoryFilter || undefined,
        limit: 200,
      });
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, categoryFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    fetchInventoryCategories()
      .then((r) => setCategories(r.categories))
      .catch(() => {});
  }, []);

  // ── Stats ──
  const totalSkus = data?.total ?? 0;
  const lowStockItems = data?.items.filter((i) => stockStatus(i) === "low") ?? [];
  const outOfStockItems = data?.items.filter((i) => stockStatus(i) === "out") ?? [];
  const totalValue =
    data?.items.reduce((sum, i) => sum + i.selling_price * i.quantity, 0) ?? 0;

  // ── Form handlers ──
  function openCreate() {
    setEditingItem(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  }

  function openEdit(item: InventoryItem) {
    setEditingItem(item);
    setForm({
      sku: item.sku,
      name: item.name,
      description: item.description || "",
      category: item.category || "",
      unit: item.unit,
      purchase_price: String(item.purchase_price),
      selling_price: String(item.selling_price),
      gst_rate: String(item.gst_rate),
      quantity: String(item.quantity),
      min_stock_level: String(item.min_stock_level),
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        sku: form.sku,
        name: form.name,
        description: form.description || undefined,
        category: form.category || undefined,
        unit: form.unit,
        purchase_price: parseFloat(form.purchase_price),
        selling_price: parseFloat(form.selling_price),
        gst_rate: parseFloat(form.gst_rate || "0"),
        quantity: parseInt(form.quantity || "0"),
        min_stock_level: parseInt(form.min_stock_level || "10"),
      };

      if (editingItem) {
        await updateInventoryItem(editingItem.id, payload);
      } else {
        await createInventoryItem(payload);
      }

      setShowForm(false);
      await loadData();
      // Refresh categories
      fetchInventoryCategories()
        .then((r) => setCategories(r.categories))
        .catch(() => {});
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteInventoryItem(id);
      setConfirmDelete(null);
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleStockAdjust() {
    if (!stockAdjust) return;
    try {
      await adjustStock(stockAdjust.id, {
        quantity_change: parseInt(stockQty || "0"),
        reason: stockReason || undefined,
      });
      setStockAdjust(null);
      setStockQty("");
      setStockReason("");
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-titanium">Inventory</h1>
          <p className="text-text-muted text-sm font-light mt-1">
            Manage stock levels, products, and reorder points
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-xl transition-colors"
        >
          + Add Product
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-5 max-md:grid-cols-2 max-sm:grid-cols-1">
        {[
          { label: "Total SKUs", value: String(totalSkus), sub: "Registered products" },
          {
            label: "Low Stock",
            value: String(lowStockItems.length),
            sub: "Below reorder threshold",
            warn: lowStockItems.length > 0,
          },
          {
            label: "Out of Stock",
            value: String(outOfStockItems.length),
            sub: "Zero quantity items",
            danger: outOfStockItems.length > 0,
          },
          { label: "Stock Value", value: formatCurrency(totalValue), sub: "At selling price" },
        ].map((stat) => (
          <div
            key={stat.label}
            className={`bg-bg-surface border rounded-xl p-5 ${
              stat.danger
                ? "border-red-500/30"
                : stat.warn
                  ? "border-amber-500/30"
                  : "border-border-dim"
            }`}
          >
            <div className="text-xs font-mono text-text-faint uppercase tracking-wider mb-2">
              {stat.label}
            </div>
            <div
              className={`text-2xl font-bold font-mono mb-1 ${
                stat.danger ? "text-red-400" : stat.warn ? "text-amber-400" : "text-text-main"
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
            placeholder="Search by name or SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main placeholder:text-text-faint focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
        {categories.length > 0 && (
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2.5 bg-bg-surface border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        )}
      </div>

      {/* Inventory Table */}
      {loading ? (
        <div className="bg-bg-surface border border-border-dim rounded-xl p-12 text-center">
          <p className="text-text-muted text-sm">Loading inventory...</p>
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
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">SKU</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Name</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Category</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Price</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Stock</th>
                  <th className="text-center px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Status</th>
                  <th className="text-right px-5 py-3 font-mono text-xs text-text-faint uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-text-muted text-sm">
                      No products found. Click &quot;Add Product&quot; to create one.
                    </td>
                  </tr>
                ) : (
                  data?.items.map((item) => {
                    const status = stockStatus(item);
                    return (
                      <tr key={item.id} className="border-b border-border-dim/50 hover:bg-bg-void/50 transition-colors">
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs text-text-faint">{item.sku}</span>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="text-text-main font-medium">{item.name}</div>
                          {item.description && (
                            <div className="text-xs text-text-muted mt-0.5 line-clamp-1">{item.description}</div>
                          )}
                        </td>
                        <td className="px-5 py-3.5">
                          {item.category ? (
                            <span className="text-xs text-text-muted">{item.category}</span>
                          ) : (
                            <span className="text-xs text-text-faint">—</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="font-mono text-text-main">{formatCurrency(item.selling_price)}</div>
                          <div className="text-xs text-text-faint font-mono">/{item.unit}</div>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <span className="font-mono text-text-main">{item.quantity}</span>
                          <span className="text-xs text-text-faint ml-1">{item.unit}</span>
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          <span
                            className={`inline-block px-2.5 py-1 rounded-lg text-xs font-mono border ${statusColor(status)}`}
                          >
                            {statusLabel(status)}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => setStockAdjust({ id: item.id, name: item.name })}
                              className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-emerald-400 hover:border-emerald-500/30 transition-colors"
                              title="Adjust Stock"
                            >
                              ± Stock
                            </button>
                            <button
                              onClick={() => openEdit(item)}
                              className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-titanium hover:border-titanium/30 transition-colors"
                              title="Edit"
                            >
                              ✎ Edit
                            </button>
                            <button
                              onClick={() => setConfirmDelete(item.id)}
                              className="px-2.5 py-1.5 bg-bg-void border border-border-dim rounded-lg text-xs text-text-muted hover:text-red-400 hover:border-red-500/30 transition-colors"
                              title="Delete"
                            >
                              ✕
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-titanium mb-1">
              {editingItem ? "Edit Product" : "Add Product"}
            </h2>
            <p className="text-text-muted text-xs mb-6 font-light">
              {editingItem ? `Editing: ${editingItem.sku}` : "Create a new inventory item"}
            </p>

            <div className="grid grid-cols-2 gap-4">
              {/* SKU */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">SKU *</label>
                <input
                  value={form.sku}
                  onChange={(e) => setForm({ ...form, sku: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="e.g. SILK_RED"
                />
              </div>

              {/* Name */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Name *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="Product name"
                />
              </div>

              {/* Category */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Category</label>
                <input
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                  placeholder="e.g. textiles, hardware"
                />
              </div>

              {/* Unit */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Unit *</label>
                <select
                  value={form.unit}
                  onChange={(e) => setForm({ ...form, unit: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="pieces">Pieces</option>
                  <option value="kg">Kilograms</option>
                  <option value="meter">Meters</option>
                  <option value="bags">Bags</option>
                  <option value="liters">Liters</option>
                  <option value="dozen">Dozen</option>
                  <option value="boxes">Boxes</option>
                </select>
              </div>

              {/* Purchase Price */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Purchase Price (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.purchase_price}
                  onChange={(e) => setForm({ ...form, purchase_price: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* Selling Price */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Selling Price (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.selling_price}
                  onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* GST Rate */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">GST Rate (%)</label>
                <input
                  type="number"
                  step="0.25"
                  value={form.gst_rate}
                  onChange={(e) => setForm({ ...form, gst_rate: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* Quantity */}
              <div className="col-span-2 sm:col-span-1">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Quantity *</label>
                <input
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* Min Stock */}
              <div className="col-span-2">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Min Stock Level (Reorder at)</label>
                <input
                  type="number"
                  value={form.min_stock_level}
                  onChange={(e) => setForm({ ...form, min_stock_level: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* Description */}
              <div className="col-span-2">
                <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                  className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50 resize-none"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-8">
              <button
                onClick={() => setShowForm(false)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.sku || !form.name || !form.selling_price}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
              >
                {saving ? "Saving..." : editingItem ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Adjust Modal */}
      {stockAdjust && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-sm mx-4">
            <h2 className="text-lg font-bold text-titanium mb-1">Adjust Stock</h2>
            <p className="text-text-muted text-xs mb-6 font-light">{stockAdjust.name}</p>

            <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">
              Quantity Change <span className="text-text-muted normal-case">(positive to add, negative to remove)</span>
            </label>
            <input
              type="number"
              value={stockQty}
              onChange={(e) => setStockQty(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50 mb-4"
              placeholder="e.g. 10 or -5"
            />

            <label className="block text-xs font-mono text-text-faint uppercase tracking-wider mb-1.5">Reason</label>
            <input
              value={stockReason}
              onChange={(e) => setStockReason(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-main focus:outline-none focus:border-emerald-500/50 mb-6"
              placeholder="e.g. Received from supplier"
            />

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setStockAdjust(null)}
                className="px-5 py-2.5 bg-bg-void border border-border-dim rounded-xl text-sm text-text-muted hover:text-text-main transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStockAdjust}
                disabled={!stockQty}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-bg-surface border border-border-dim rounded-2xl p-8 w-full max-w-sm mx-4 text-center">
            <div className="text-3xl mb-3 text-red-400">⚠</div>
            <h2 className="text-lg font-bold text-titanium mb-2">Delete Product?</h2>
            <p className="text-text-muted text-sm mb-6">
              This will deactivate the product. Historical data will be preserved.
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
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
