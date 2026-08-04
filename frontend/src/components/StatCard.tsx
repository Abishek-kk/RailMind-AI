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
  iconColor = "#00e5ff",
  iconBg = "rgba(0,229,255,0.15)",
  change,
  dir,
  sublabel,
}: StatCardProps) {
  const positive = dir === "up";
  return (
    <div className="hud-panel rounded-xl bg-card p-4">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
      <div className="flex items-start gap-3">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
          style={{
            backgroundColor: iconBg,
            boxShadow: `0 0 10px ${iconColor}22`,
            border: `1px solid ${iconColor}33`,
          }}
        >
          <Icon className="h-6 w-6" style={{ color: iconColor }} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          <div className="mt-0.5 text-2xl font-bold leading-tight font-mono">{value}</div>
          {sublabel && <div className="text-[11px] text-muted-foreground">{sublabel}</div>}
          {typeof change === "number" && (
            <div className="mt-1 flex items-center gap-1 text-xs">
              {positive ? (
                <ArrowUp className="h-3 w-3 text-[#00e676]" />
              ) : (
                <ArrowDown className="h-3 w-3 text-[#ff2d55]" />
              )}
              <span className={positive ? "text-[#00e676]" : "text-[#ff2d55]"}>{change}%</span>
              <span className="text-muted-foreground">from yesterday</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
