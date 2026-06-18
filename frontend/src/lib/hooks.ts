/**
 * SUTRA Dashboard React Hooks
 * Data fetching hooks with loading/error states
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchDashboardKpi,
  type DashboardKpiData,
} from "@/lib/api";

// ── Generic Fetch Hook ───────────────────────────────────────────────────────

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const execute = useCallback(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));

    fetcher()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err: Error) => {
        if (!cancelled)
          setState({ data: null, loading: false, error: err.message });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    const cleanup = execute();
    return cleanup;
  }, [execute]);

  return { ...state, refetch: execute };
}

// ── Dashboard Hooks ──────────────────────────────────────────────────────────

export function useDashboardKPI(tenantId: string) {
  return useAsync(() => fetchDashboardKpi(tenantId, 30), [tenantId]);
}

export function useDashboardKPIWithRange(tenantId: string, days: number) {
  return useAsync(() => fetchDashboardKpi(tenantId, days), [tenantId, days]);
}

// ── Helper: Derive KPI card props from data ──────────────────────────────────

export interface KpiCardProps {
  label: string;
  value: string;
  subtitle: string;
  trend: "up" | "down" | "neutral";
  change: string;
}

export function getKpiCards(data: DashboardKpiData | null): KpiCardProps[] {
  if (!data) return [];

  const kpi = data.kpi;

  return [
    {
      label: "Total Orders",
      value: kpi.total_orders.value.toLocaleString(),
      subtitle: kpi.total_orders.period
        ? `Last ${kpi.total_orders.period.replace("last_", "").replace("_days", " days")}`
        : "Current period",
      trend: kpi.total_orders.trend || "neutral",
      change: kpi.total_orders.change || "0%",
    },
    {
      label: "Revenue MTD",
      value: `₹${kpi.revenue_mtd.value.toLocaleString("en-IN")}`,
      subtitle: "Month to date revenue",
      trend: kpi.revenue_mtd.trend || "neutral",
      change: kpi.revenue_mtd.change || "0%",
    },
    {
      label: "Udhaar Outstanding",
      value: `₹${kpi.udhaar_outstanding.value.toLocaleString("en-IN")}`,
      subtitle: `${kpi.udhaar_outstanding.customers_with_debt ?? 0} customers with balance`,
      trend: kpi.udhaar_outstanding.value > 0 ? "down" : "neutral",
      change: "Outstanding",
    },
    {
      label: "Low Stock Items",
      value: kpi.low_stock_count.value.toLocaleString(),
      subtitle: `of ${kpi.low_stock_count.total_skus ?? 0} total SKUs`,
      trend: kpi.low_stock_count.value > 0 ? "down" : "up",
      change: kpi.low_stock_count.value > 0 ? "Restock needed" : "All stocked",
    },
  ];
}
