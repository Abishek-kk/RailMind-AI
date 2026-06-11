import { ArrowDown, ArrowUp, type LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  change?: number;
  dir?: "up" | "down";
  sublabel?: string;
}

export function StatCard({
  label,
  value,
  icon: Icon,
  iconColor = "#6366f1",
  iconBg = "rgba(99,102,241,0.15)",
  change,
  dir,
  sublabel,
}: StatCardProps) {
  const positive = dir === "up";
  return (
    <div className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/40">
      <div className="flex items-start gap-3">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
          style={{ backgroundColor: iconBg }}
        >
          <Icon className="h-6 w-6" style={{ color: iconColor }} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          <div className="mt-0.5 text-2xl font-bold leading-tight">{value}</div>
          {sublabel && <div className="text-[11px] text-muted-foreground">{sublabel}</div>}
          {typeof change === "number" && (
            <div className="mt-1 flex items-center gap-1 text-xs">
              {positive ? (
                <ArrowUp className="h-3 w-3 text-[#22c55e]" />
              ) : (
                <ArrowDown className="h-3 w-3 text-[#ef4444]" />
              )}
              <span className={positive ? "text-[#22c55e]" : "text-[#ef4444]"}>{change}%</span>
              <span className="text-muted-foreground">from yesterday</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
