import { apiFetch } from "./client";
import type { IncidentTrendItem } from "./dashboard";

export interface LstmPerformance {
  total_predictions: number;
  avg_confidence: number;
  false_positive_rate: number;
  false_positive_count: number;
  per_class_counts: Record<string, number>;
}

export interface FalsePositiveRateAlert {
  id: number;
  platform: string;
  fp_rate: number;
  alerted_at?: string | null;
}

export async function getAnalyticsSummary(days = 7): Promise<IncidentTrendItem[]> {
  return apiFetch<IncidentTrendItem[]>(`/analytics/summary?days=${days}`);
}

export async function getAnalyticsTrend(days = 7): Promise<IncidentTrendItem[]> {
  return apiFetch<IncidentTrendItem[]>(`/analytics/trend?days=${days}`);
}

export async function getLstmPerformance(): Promise<LstmPerformance> {
  return apiFetch<LstmPerformance>("/analytics/lstm-performance");
}

export async function getFalsePositiveRateAlerts(): Promise<FalsePositiveRateAlert[]> {
  return apiFetch<FalsePositiveRateAlert[]>("/analytics/fp-rate-alerts");
}
