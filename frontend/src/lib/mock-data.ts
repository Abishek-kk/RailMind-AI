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
  x: number; // percent
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
  /** Optional operator assigned to this alert, as returned by the backend */
  operator_assigned?: string | null;
}

import p1 from "@/assets/cctv-platform.jpg";
import p2 from "@/assets/cctv-platform2.jpg";
import p3 from "@/assets/cctv-platform3.jpg";
import p4 from "@/assets/cctv-platform4.jpg";

export const cctvImages = [p1, p2, p3, p4, p1];

export const CCTV_OPTIONS = [
  { id: "all", label: "All CCTV Feeds" },
  { id: "CCTV-1", label: "CCTV-1 (Platform 1)" },
  { id: "CCTV-2", label: "CCTV-2 (Platform 2)" },
  { id: "CCTV-3", label: "CCTV-3 (Platform 3)" },
  { id: "CCTV-4", label: "CCTV-4 (Platform 4)" },
  { id: "CCTV-5", label: "CCTV-5 (Platform 5)" },
];

export function getLiveFeeds(): CCTVFeed[] {
  return [
    {
      id: "CCTV-1",
      platform: "Platform 1",
      image: p1,
      status: "online",
      peopleDetected: 6,
      alertType: "Suicide Risk",
      riskScore: 91,
      riskLevel: "high",
      boxes: [
        { id: 11, x: 36, y: 38, w: 9, h: 28, level: "low" },
        { id: 12, x: 22, y: 46, w: 9, h: 30, level: "low" },
        { id: 15, x: 48, y: 40, w: 9, h: 28, level: "low" },
        { id: 16, x: 60, y: 44, w: 9, h: 30, level: "low" },
        { id: 7, x: 42, y: 50, w: 12, h: 36, level: "high" },
      ],
    },
    {
      id: "CCTV-2",
      platform: "Platform 2",
      image: p2,
      status: "online",
      peopleDetected: 5,
      alertType: "Loitering Detected",
      riskScore: 62,
      riskLevel: "medium",
      boxes: [
        { id: 9, x: 38, y: 44, w: 10, h: 30, level: "medium" },
        { id: 21, x: 22, y: 48, w: 10, h: 30, level: "low" },
        { id: 22, x: 70, y: 48, w: 10, h: 30, level: "low" },
      ],
    },
    {
      id: "CCTV-3",
      platform: "Platform 3",
      image: p3,
      status: "online",
      peopleDetected: 8,
      alertType: "Pickpocketing Risk",
      riskScore: 86,
      riskLevel: "suspicious",
      boxes: [
        { id: 24, x: 38, y: 50, w: 14, h: 34, level: "suspicious" },
        { id: 27, x: 50, y: 36, w: 9, h: 26, level: "low" },
        { id: 28, x: 62, y: 48, w: 9, h: 30, level: "low" },
        { id: 31, x: 20, y: 50, w: 9, h: 32, level: "low" },
        { id: 33, x: 70, y: 38, w: 9, h: 26, level: "low" },
      ],
    },
    {
      id: "CCTV-4",
      platform: "Platform 4",
      image: p4,
      status: "online",
      peopleDetected: 4,
      alertType: "Security Threat",
      riskScore: 90,
      riskLevel: "high",
      boxes: [
        { id: 38, x: 70, y: 44, w: 10, h: 32, level: "high" },
        { id: 41, x: 40, y: 46, w: 9, h: 30, level: "low" },
        { id: 44, x: 52, y: 46, w: 9, h: 30, level: "low" },
        { id: 45, x: 62, y: 42, w: 9, h: 28, level: "low" },
      ],
    },
  ];
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
