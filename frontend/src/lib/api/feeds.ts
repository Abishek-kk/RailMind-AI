// frontend/src/lib/api/feeds.ts
import { apiFetch } from "./client";

export interface Feed {
  platform: any;
  id: string;
  name: string;
  status: "active" | "processing" | "error" | "offline";
  stream_url?: string;
  track_count?: number;
  error_message?: string;
  // Additional fields from backend if any
}

/**
 * Fetch all feeds from the backend.
 */
export async function getFeeds(): Promise<Feed[]> {
  const response = (await apiFetch("/feeds")) as Response;
  return response.json() as Promise<Feed[]>;
}

/**
 * Create a new live stream feed (immediately active).
 */
export async function createFeed(payload: { id: string; name: string; source_url: string }): Promise<Feed> {
  const response = (await apiFetch("/feeds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })) as Response;
  return response.json() as Promise<Feed>;
}

/**
 * Upload a video file for processing. The backend starts processing asynchronously
 * and returns immediately with status "processing".
 */
export async function uploadVideo(
  file: File,
  feedId?: string,
  name?: string,
): Promise<{ id: string; status: "processing" | "active" | "error"; msg: string }> {
  const formData = new FormData();
  formData.append("file", file);
  if (feedId) formData.append("feed_id", feedId);
  if (name) formData.append("name", name);

  const response = (await apiFetch("/feeds/upload", {
    method: "POST",
    body: formData,
  })) as Response;
  return response.json() as Promise<{ id: string; status: "processing" | "active" | "error"; msg: string }>;
}

/**
 * Delete an existing feed.
 */
export async function deleteFeed(feedId: string): Promise<{ status: string; feed_id: string }> {
  const response = (await apiFetch(`/feeds/${feedId}`, { method: "DELETE" })) as Response;
  return response.json() as Promise<{ status: string; feed_id: string }>;
}

/**
 * Poll the status of a specific feed (e.g., while it is processing).
 */
export async function getFeedStatus(feedId: string): Promise<{
  id: string;
  status: "processing" | "active" | "error" | "offline";
  error_message?: string;
  stream_url?: string;
  track_count?: number;
}> {
  const response = (await apiFetch(`/feeds/${feedId}/status`)) as Response;
  return response.json() as Promise<{
    id: string;
    status: "processing" | "active" | "error" | "offline";
    error_message?: string;
    stream_url?: string;
    track_count?: number;
  }>;
}