import { riskColor, type RiskLevel } from "@/lib/railmind-types";

export function RiskBadge({ level, label }: { level: RiskLevel | "very-high"; label?: string }) {
  const c = riskColor(level);
  const text =
    label ??
    (level === "high"
      ? "HIGH RISK"
      : level === "very-high"
        ? "VERY HIGH"
        : level === "medium"
          ? "MEDIUM RISK"
          : level === "suspicious"
            ? "HIGH RISK"
            : "SAFE");
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wide"
      style={{ backgroundColor: `${c}22`, color: c, border: `1px solid ${c}44` }}
    >
      {text}
    </span>
  );
}

export function ScorePill({ score, level }: { score: number; level: RiskLevel }) {
  const c = riskColor(level);
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold tabular-nums"
      style={{ backgroundColor: `${c}1f`, color: c, border: `1px solid ${c}33` }}
    >
      {score}%
    </span>
  );
}
