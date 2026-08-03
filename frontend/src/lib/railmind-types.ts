import p1 from "@/assets/cctv-platform.jpg";
import p2 from "@/assets/cctv-platform2.jpg";
import p3 from "@/assets/cctv-platform3.jpg";
import p4 from "@/assets/cctv-platform4.jpg";

export type RiskLevel = "high" | "medium" | "low" | "suspicious";
export type AlertStatus = "active" | "acknowledged" | "resolved";

export interface CCTVFeed {
  id: string;
  platform: string;
  image: string;
  streamUrl?: string;
  status: "online" | "offline";
  peopleDetected: number;
  alertType?: string;
  riskScore?: number;
  riskLevel?: RiskLevel;
  boxes: BoundingBox[];
}

export interface BoundingBox {
  id: number;
  x: number;
  y: number;
  w: number;
  h: number;
  level: RiskLevel;
}

export interface Alert {
  id: string;
  cctv: string;
  platform: string;
  type: string;
  riskScore: number;
  riskLevel: RiskLevel;
  time: string;
  date: string;
  status: AlertStatus;
  description: string;
  image: string;
  operator_assigned?: string | null;
  reasoning_mode?: string | null;
}

const cameraImages = [p1, p2, p3, p4];

export function getCameraImage(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cameraImages[index % cameraImages.length] ?? cameraImages[0];
}

export const riskColor = (level: RiskLevel | string) => {
  switch (level) {
    case "high":
    case "very-high":
      return "#ef4444";
    case "medium":
      return "#f97316";
    case "suspicious":
      return "#a855f7";
    case "low":
    default:
      return "#22c55e";
  }
};
