// frontend/src/lib/mock-data.ts

export type RiskLevel = "low" | "medium" | "high" | "suspicious";

export type AlertStatus = "active" | "acknowledged" | "resolved";

export type HandlingLevel = "normal" | "medium" | "high";

export interface BoundingBox {
  id: number;
  level: RiskLevel;
  x: number; // percentage (0-100)
  y: number; // percentage (0-100)
  w: number; // percentage (0-100)
  h: number; // percentage (0-100)
}

export interface CCTVFeed {
  id: string;
  name: string;
  platform: string;
  status: "active" | "processing" | "error" | "offline";
  streamUrl?: string;
  image?: string;
  peopleDetected?: number;
  alertType?: string;
  riskScore?: number;
  riskLevel?: RiskLevel;
  error_message?: string;
  track_count?: number; // number of tracked people from pipeline
}

export interface Alert {
  id: string;
  cctv: string;
  platform: string;
  type: string;
  riskLevel: RiskLevel;
  riskScore: number;
  time: string;
  date: string;
  status: AlertStatus;
  handlingLevel: HandlingLevel;
  image: string;
  description: string;
  operator_assigned?: string | null;
  reasoning_mode?: "llm" | "rule_based";
  reasoning?: {
    mode: "llm" | "rule_based";
    summary: string;
    evidence: { signal: string; value: string | number | boolean; meaning: string }[];
    limitations: string;
  };
  videoUrl?: string;
}

/**
 * Returns the appropriate color for a given risk level.
 */
export function riskColor(level: RiskLevel | "very-high" | string): string {
  if (level === "high" || level === "very-high") return "#ff2d55";
  if (level === "medium") return "#ff9f0a";
  if (level === "suspicious") return "#b026ff";
  return "#00e676";
}

/**
 * Placeholder images for CCTV feeds (used when no real image is available).
 */
export const cctvImages = [];
