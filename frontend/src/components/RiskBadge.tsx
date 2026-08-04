import { riskColor, type RiskLevel } from "@/lib/mock-data";

function getGlowShadow(level: RiskLevel | "very-high" | string) {
  switch (level) {
    case "high":
    case "very-high":
      return "0 0 14px rgba(255, 45, 85, 0.45)";
    case "medium":
      return "0 0 12px rgba(255, 159, 10, 0.4)";
    case "suspicious":
      return "0 0 12px rgba(176, 38, 255, 0.35)";
    case "low":
    default:
      return "0 0 4px rgba(0, 230, 118, 0.15)";
  }
}

export function RiskBadge({
  level,
  label,
}: {
  level: RiskLevel | "very-high" | string;
  label?: string;
}) {
  const c = riskColor(level);
  const normalizedLevel = String(level ?? "low").toLowerCase();
  const text =
    label ??
    (normalizedLevel === "high"
      ? "HIGH RISK"
      : normalizedLevel === "very-high"
        ? "VERY HIGH"
        : normalizedLevel === "medium"
          ? "MEDIUM RISK"
          : normalizedLevel === "suspicious"
            ? "SUSPICIOUS"
            : "SAFE");
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wide"
      style={{
        backgroundColor: `${c}22`,
        color: c,
        border: `1px solid ${c}44`,
        boxShadow: getGlowShadow(level),
      }}
    >
      {text}
    </span>
  );
}

export function ScorePill({ score, level }: { score: number; level: RiskLevel }) {
  const c = riskColor(level);
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold font-mono tabular-nums"
      style={{
        backgroundColor: `${c}1f`,
        color: c,
        border: `1px solid ${c}33`,
        boxShadow: getGlowShadow(level),
      }}
    >
      {score}%
    </span>
  );
}
