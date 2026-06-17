interface KPICardProps {
  title: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  subtitle: string;
  icon: string;
}

export function KPICard({ title, value, change, trend, subtitle, icon }: KPICardProps) {
  const trendColors = {
    up: "text-emerald",
    down: "text-red-400",
    neutral: "text-text-muted",
  };

  return (
    <div className="bg-bg-surface border border-border-dim rounded-xl p-6 transition-all duration-300 hover:border-border-glow hover:-translate-y-0.5 hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
      <div className="flex items-start justify-between mb-4">
        <span className="text-xs font-mono text-text-faint uppercase tracking-wider">
          {title}
        </span>
        <span className="text-emerald text-lg">{icon}</span>
      </div>

      <div className="text-[2rem] font-bold text-text-main tracking-tight mb-1 font-mono">
        {value}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span
          className={`text-xs font-medium font-mono ${
            trend === "up"
              ? "text-emerald"
              : trend === "down"
                ? "text-red-400"
                : "text-text-muted"
          }`}
        >
          {change}
        </span>
        <span className="text-xs text-text-muted font-light">{subtitle}</span>
      </div>

      {/* Micro sparkline bar */}
      <div className="h-1 w-full bg-bg-panel rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            trend === "up"
              ? "bg-emerald"
              : trend === "down"
                ? "bg-red-400/60"
                : "bg-text-muted/30"
          }`}
          style={{ width: trend === "up" ? "72%" : trend === "down" ? "34%" : "50%" }}
        />
      </div>
    </div>
  );
}
