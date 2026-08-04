import { apiFetch } from "./client";

export interface TrainingRun {
  id: number;
  triggered_by: string;
  status: string;
  model_type: string;
  epochs: number;
  batch_size: number;
  synthetic_sample_count: number;
  real_sample_count: number;
  final_train_loss?: number | null;
  final_val_loss?: number | null;
  final_train_accuracy?: number | null;
  final_val_accuracy?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  error_message?: string | null;
  model_saved_path?: string | null;
  is_production_ready: boolean;
}

export interface TrainingSystemStatus {
  system_status: string;
  training_runs: {
    pending: number;
    running: number;
    completed: number;
    failed: number;
    total: number;
  };
  latest_successful_run?: {
    id: number | null;
    completed_at?: string | null;
    is_production_ready: boolean;
  } | null;
}

export interface TrainingTriggerResponse {
  run_id: number;
  status: string;
  message: string;
}

export async function getTrainingStatus(): Promise<TrainingSystemStatus> {
  return apiFetch<TrainingSystemStatus>("/training/status");
}

export async function getLatestTrainingRun(): Promise<TrainingRun | null> {
  return apiFetch<TrainingRun | null>("/training/latest");
}

export async function getTrainingRuns(limit = 10): Promise<TrainingRun[]> {
  return apiFetch<TrainingRun[]>(`/training/runs?limit=${limit}`);
}

export async function triggerTraining(payload = { model_type: "all", epochs: 30, batch_size: 32 }) {
  return apiFetch<TrainingTriggerResponse>("/training/trigger", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
