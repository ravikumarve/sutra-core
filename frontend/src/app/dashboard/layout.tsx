import type { Metadata } from "next";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardHeader } from "@/components/dashboard/header";

export const metadata: Metadata = {
  title: "Dashboard | SUTRA Core",
  description: "Analytics dashboard for SUTRA Core headless ERP",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-dvh flex bg-bg-void">
      {/* Ambient background */}
      <div className="fixed inset-0 z-0">
        <div className="dot-matrix-overlay" />
        <div className="ambient-core" />
      </div>

      {/* Sidebar */}
      <DashboardSidebar />

      {/* Main content area */}
      <div className="relative z-10 flex-1 flex flex-col ml-64 max-lg:ml-0">
        <DashboardHeader />
        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
