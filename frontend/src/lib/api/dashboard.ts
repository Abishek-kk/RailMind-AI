import { apiFetch } from "./client";
import { cctvImages, type RiskLevel } from "@/lib/mock-data";

export interface DashboardStats {
  total_incidents: number;
  active_alerts: number;
  security_threats: number;
  suicide_mitigations: number;
  theft_preventions: number;
  system_status: string;
}

export interface IncidentsByCCTVItem {
  camera_id: string;
  incidents: number;
}

export interface IncidentTrendItem {
  date: string;
  "Suicide Risk": number;
  Pickpocketing: number;
  Loitering: number;
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
  id: number;
  camera_id: string;
  platform: string;
  incident_type: string;
  risk_score: number;
  risk_level: string;
  status: string;
  timestamp: string;
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

function mapIncidentToAlert(incident: IncidentRead): DashboardAlert {
  return {
    id: `INC-${String(incident.id).padStart(3, "0")}`,
    cctv: incident.camera_id,
    platform: incident.platform || incident.camera_id,
    type: incident.incident_type,
    riskLevel: normalizeRiskLevel(incident.risk_level),
    time: formatTime(incident.timestamp),
    status: incident.status,
    image: getImageForCamera(incident.camera_id),
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
    "Suicide Risk Detection": "#ef4444",
    "Pickpocketing Actions": "#f97316",
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
  const incidents = await apiFetch<IncidentRead[]>("/incidents?status=active&limit=4");
  return incidents.map(mapIncidentToAlert);
}
