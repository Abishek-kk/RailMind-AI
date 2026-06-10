export type RiskLevel = "high" | "medium" | "low" | "suspicious";
export type AlertStatus = "active" | "acknowledged" | "resolved";

export interface CCTVFeed {
  id: string;
  platform: string;
  image: string;
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

function rand(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

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

const TYPES = [
  "Suicide Risk Detected",
  "Pickpocketing Risk",
  "Loitering Detected",
  "Normal Activity",
  "Security Threat",
] as const;

function typeToLevel(t: string): RiskLevel {
  if (t.includes("Suicide") || t.includes("Security")) return "high";
  if (t.includes("Pickpocketing")) return "suspicious";
  if (t.includes("Loitering")) return "medium";
  return "low";
}

export function generateAlerts(count = 28): Alert[] {
  const alerts: Alert[] = [];
  for (let i = 0; i < count; i++) {
    const type = TYPES[i % TYPES.length];
    const cctvNum = (i % 5) + 1;
    const level = typeToLevel(type);
    const baseScore =
      level === "high" ? 85 + (i % 10) :
      level === "suspicious" ? 70 + (i % 15) :
      level === "medium" ? 55 + (i % 15) :
      10 + (i % 15);
    const minute = 45 - i;
    const status: AlertStatus = type === "Normal Activity" ? "resolved" : "active";
    alerts.push({
      id: `ALT-2025-0526-${String(i + 1).padStart(3, "0")}`,
      cctv: `CCTV-${cctvNum}`,
      platform: `Platform ${cctvNum}`,
      type,
      riskScore: baseScore,
      riskLevel: level,
      time: `10:${String(Math.max(0, minute)).padStart(2, "0")}:${String(28 - (i % 30)).padStart(2, "0")} AM`,
      date: "18 May 2025",
      status,
      description:
        level === "high"
          ? "Person standing near platform edge for extended time with risky behavior."
          : level === "suspicious"
          ? "Suspicious hand movement detected in crowded area near other passengers."
          : level === "medium"
          ? "Individual loitering in restricted zone beyond expected dwell time."
          : "Normal passenger movement detected. No threat identified.",
      image: cctvImages[(cctvNum - 1) % cctvImages.length],
    });
  }
  // Make some explicitly resolved
  alerts[3].status = "resolved";
  alerts[6].status = "resolved";
  return alerts;
}

export function getDashboardStats() {
  return {
    totalIncidents: { value: 45, change: 12, dir: "up" },
    activeAlerts: { value: 8, change: 33, dir: "up" },
    suicideRisk: { value: 12, change: 20, dir: "up" },
    pickpocketingRisk: { value: 18, change: 15, dir: "up" },
    securityThreats: { value: 15, change: 25, dir: "up" },
  };
}

export function getAlertStats() {
  return {
    total: { value: 28, change: 18, dir: "up" },
    high: { value: 8, change: 33, dir: "up" },
    medium: { value: 13, change: 8, dir: "up" },
    low: { value: 7, change: 12, dir: "down" },
    resolved: { value: 15, change: 25, dir: "up" },
  };
}

export function getIncidentsByCCTV() {
  return [
    { name: "CCTV-1", value: 12, color: "#6366f1" },
    { name: "CCTV-2", value: 15, color: "#ef4444" },
    { name: "CCTV-3", value: 8, color: "#f97316" },
    { name: "CCTV-4", value: 6, color: "#22c55e" },
    { name: "CCTV-5", value: 4, color: "#3b82f6" },
  ];
}

export function getIncidentTrend() {
  const days = ["12 May", "13 May", "14 May", "15 May", "16 May", "17 May", "18 May"];
  return days.map((d, i) => ({
    date: d,
    total: 25 + Math.round(rand(i + 1) * 25),
    suicide: 15 + Math.round(rand(i + 2) * 10),
    pickpocket: 8 + Math.round(rand(i + 3) * 8),
    security: 4 + Math.round(rand(i + 4) * 6),
  }));
}

export function getRiskDistribution() {
  return [
    { name: "Suicide Risk", value: 12, color: "#ef4444" },
    { name: "Pickpocketing Risk", value: 18, color: "#f97316" },
    { name: "Security Threat", value: 15, color: "#6366f1" },
  ];
}

export function getPeakHours() {
  const data = [];
  for (let h = 0; h < 24; h++) {
    const base = Math.exp(-Math.pow((h - 13) / 4, 2)) * 22;
    data.push({ hour: `${String(h).padStart(2, "0")}:00`, incidents: Math.round(base + rand(h) * 3) });
  }
  return data;
}

export function getCCTVSummary() {
  return [
    { id: "CCTV-1", location: "Platform 1", status: "online", incidents: 12, alerts: 2, last: "10:45:17 AM", risk: "medium" },
    { id: "CCTV-2", location: "Platform 2", status: "online", incidents: 15, alerts: 3, last: "10:45:28 AM", risk: "high" },
    { id: "CCTV-3", location: "Platform 3", status: "online", incidents: 8, alerts: 2, last: "10:45:21 AM", risk: "medium" },
    { id: "CCTV-4", location: "Platform 4", status: "online", incidents: 6, alerts: 1, last: "10:45:10 AM", risk: "low" },
    { id: "CCTV-5", location: "Platform 5", status: "online", incidents: 4, alerts: 0, last: "10:44:55 AM", risk: "low" },
  ] as const;
}

export function getPlatformHeatmap() {
  return [
    { name: "Platform 1", risk: "High Risk", level: "high" as const },
    { name: "Platform 2", risk: "Very High Risk", level: "very-high" as const },
    { name: "Platform 3", risk: "Medium Risk", level: "medium" as const },
    { name: "Platform 4", risk: "Low Risk", level: "low" as const },
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