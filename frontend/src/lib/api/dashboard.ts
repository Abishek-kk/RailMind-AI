import { apiFetch } from "./client";
import { resolveStreamUrl } from "@/lib/api/feeds";
import { cctvImages, type RiskLevel } from "@/lib/mock-data";

export interface DashboardStats {
  total_incidents: number;
  active_alerts: number;
  track_zone_intrusions: number;
  loitering_trespass: number;
  general_anomalies: number;
  system_status: string;
}

export interface IncidentsByCCTVItem {
  camera_id: string;
  incidents: number;
}

export interface IncidentTrendItem {
  date: string;
  "Track Zone Intrusion": number;
  "Loitering / Trespass": number;
  "General Anomalies": number;
}

export interface RiskDistributionItem {
  name: string;
  value: number;
  color: string;
}

export interface PeakHourItem {
  hour: string;
  incidents: number;
}

export interface HeatmapPoint {
  platform: string;
  zone: string;
  intensity: number;
}

export interface CCTVSummaryRow {
  camera_id: string;
  location: string;
  status: string;
  total_incidents: number;
  active_alerts: number;
  current_risk_level: string;
  last_incident?: string;
}

export interface IncidentRead {
  id: string;
  camera_id: string;
  platform?: string;
  incident_type: string;
  risk_score: number;
  risk_level: string;
  status: string;
  timestamp: string;
}

export interface AlertRead extends IncidentRead {
  image_url?: string | null;
  video_snippet_url?: string | null;
}

export interface DashboardAlert {
  id: string;
  cctv: string;
  platform: string;
  type: string;
  riskLevel: RiskLevel;
  time: string;
  status: string;
  image: string;
}

function normalizeRiskLevel(value: string): RiskLevel {
  const lower = value.toLowerCase();
  if (lower.includes("critical")) return "high";
  if (lower.includes("high")) return "high";
  if (lower.includes("suspicious")) return "suspicious";
  if (lower.includes("medium")) return "medium";
  return "low";
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true });
}

function getImageForCamera(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cctvImages[index % cctvImages.length] ?? cctvImages[0];
}

function mapIncidentToAlert(incident: IncidentRead | AlertRead): DashboardAlert {
  // Enforce incident type → risk level mapping
  let riskLevel: RiskLevel = "low";
  const incidentType = incident.incident_type || "";

  if (incidentType === "Normal Activity") {
    riskLevel = incident.risk_score < 40 ? "low" : "medium";
  } else if (
    incidentType === "Suspicious Following" ||
    incidentType === "Pickpocketing" ||
    incidentType === "Loitering"
  ) {
    riskLevel = "medium";
  } else if (
    incidentType === "Incident Risk" ||
    incidentType === "Track Intrusion" ||
    incidentType === "Security Threat"
  ) {
    riskLevel = "high";
  } else {
    // Default: use the backend's risk level for unknown types
    riskLevel = normalizeRiskLevel(incident.risk_level);
  }

  const imageUrl = "image_url" in incident ? incident.image_url : undefined;

  return {
    id: `INC-${String(incident.id).padStart(3, "0")}`,
    cctv: incident.camera_id,
    platform: incident.platform || incident.camera_id,
    type: incident.incident_type,
    riskLevel,
    time: formatTime(incident.timestamp),
    status: incident.status,
    image: resolveStreamUrl(imageUrl ?? undefined) || getImageForCamera(incident.camera_id),
  };
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiFetch<DashboardStats>("/dashboard/stats");
}

export async function getIncidentsByCCTV(): Promise<IncidentsByCCTVItem[]> {
  return apiFetch<IncidentsByCCTVItem[]>("/dashboard/incidents-by-cctv");
}

export async function getIncidentTrend(days = 7): Promise<IncidentTrendItem[]> {
  return apiFetch<IncidentTrendItem[]>(`/dashboard/trend?days=${days}`);
}

function mapRiskDistributionColor(item: Omit<RiskDistributionItem, "color">): RiskDistributionItem {
  const colorMap: Record<string, string> = {
    "Track Zone Intrusion": "#ef4444",
    "Loitering / Trespass": "#3b82f6",
    "General Anomalies": "#a855f7",
  };

  return {
    ...item,
    color: colorMap[item.name] ?? "#64748b",
  };
}

export async function getRiskDistribution(): Promise<RiskDistributionItem[]> {
  const distribution = await apiFetch<Omit<RiskDistributionItem, "color">[]>(
    "/dashboard/risk-distribution",
  );
  return distribution.map(mapRiskDistributionColor);
}

export async function getPeakHours(): Promise<PeakHourItem[]> {
  return apiFetch<PeakHourItem[]>("/dashboard/peak-hours");
}

export async function getPlatformHeatmap(): Promise<HeatmapPoint[]> {
  return apiFetch<HeatmapPoint[]>("/dashboard/heatmap");
}

export async function getCCTVSummary(): Promise<CCTVSummaryRow[]> {
  return apiFetch<CCTVSummaryRow[]>("/dashboard/cctv-summary");
}

export async function getRecentIncidents(): Promise<DashboardAlert[]> {
  const alerts = await apiFetch<AlertRead[]>("/alerts");
  return (Array.isArray(alerts) ? alerts : [])
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 4)
    .map(mapIncidentToAlert);
}
