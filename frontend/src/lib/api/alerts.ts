import { apiFetch } from "./client";
import { Alert, AlertStatus, cctvImages, RiskLevel } from "@/lib/mock-data";

export interface BackendAlert {
  id?: number;
  person_id: string;
  camera_id: string;
  platform: string;
  incident_type: string;
  risk_score: number;
  risk_level: string;
  status: string;
  timestamp: string;
  /** Operator assigned to this alert (may be null if unassigned) */
  operator_assigned?: string | null;
}

export type ApiAlert = Alert & { backendId: number };

function normalizeRiskLevel(value: string): RiskLevel {
  const lower = value.toLowerCase();
  if (lower.includes("high")) return "high";
  if (lower.includes("suspicious")) return "suspicious";
  if (lower.includes("medium")) return "medium";
  return "low";
}

function getDisplayCameraId(cameraId: string): string {
  const match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-](\d+))/i);
  const number = match ? Number(match[1] ?? match[2]) : NaN;
  return Number.isFinite(number) && number > 0 ? `CCTV-${number}` : cameraId;
}

function normalizeStatus(value?: string | null): AlertStatus {
  const lower = String(value ?? "active").toLowerCase();
  if (lower === "acknowledged") return "acknowledged";
  if (lower === "resolved") return "resolved";
  return "active";
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true });
}

function formatDate(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

function getImageForCamera(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cctvImages[index % cctvImages.length] ?? cctvImages[0];
}

export function mapBackendAlert(alert: BackendAlert): ApiAlert {
  const displayCameraId = getDisplayCameraId(alert.camera_id || "CCTV-1");
  const roundedRiskScore = Math.round(alert.risk_score);
  const clampedRiskScore = Math.min(100, Math.max(0, roundedRiskScore));

  const alertId =
    alert.id !== undefined && alert.id !== null
      ? alert.id
      : Math.floor(Math.random() * 1000000) + 10000;

  return {
    backendId: alertId,
    id: `ALT-${String(alertId).padStart(3, "0")}`,
    cctv: displayCameraId,
    platform: alert.platform,
    type: alert.incident_type,
    riskScore: clampedRiskScore,
    riskLevel: normalizeRiskLevel(alert.risk_level),
    time: formatTime(alert.timestamp),
    date: formatDate(alert.timestamp),
    status: normalizeStatus(alert.status),
    description: `${alert.incident_type} on ${alert.platform}`,
    image: getImageForCamera(alert.camera_id),
    operator_assigned: alert.operator_assigned ?? null,
  };
}

export async function getAlerts(): Promise<ApiAlert[]> {
  const alerts = await apiFetch<BackendAlert[]>("/alerts");
  return (Array.isArray(alerts) ? alerts : []).map(mapBackendAlert);
}

export async function acknowledgeAlert(id: number, operatorId?: string | null): Promise<ApiAlert> {
  const trimmedOperatorId = operatorId?.trim();
  const query = trimmedOperatorId
    ? `?operator_id=${encodeURIComponent(trimmedOperatorId)}`
    : "";
  const alert = await apiFetch<BackendAlert>(`/alerts/${id}/acknowledge${query}`, {
    method: "PATCH",
  });
  return mapBackendAlert(alert);
}

export async function resolveAlert(id: number): Promise<ApiAlert> {
  const alert = await apiFetch<BackendAlert>(`/alerts/${id}/resolve`, { method: "PATCH" });
  return mapBackendAlert(alert);
}

export async function assignAlert(id: number, assignee: string): Promise<ApiAlert> {
  const alert = await apiFetch<BackendAlert>(`/alerts/${id}/assign`, {
    method: "PATCH",
    body: JSON.stringify({ assignee }),
  });
  return mapBackendAlert(alert);
}
