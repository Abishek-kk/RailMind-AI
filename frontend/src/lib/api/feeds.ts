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
 * Fetch all feeds from the backend, with stream_url resolved to an
 * absolute URL (backend returns relative paths like "/processed/...",
 * which need the API base URL prepended -- see resolveStreamUrl below).
 */
export async function getFeeds(): Promise<Feed[]> {
  const feeds = await apiFetch<Feed[]>("/feeds");
  if (!Array.isArray(feeds)) return [];
  return feeds.map((feed) => ({
    ...feed,
    stream_url: resolveStreamUrl(feed.stream_url),
  }));
}

/**
 * Create a new live stream feed (immediately active).
 */
export async function createFeed(payload: { id: string; name: string; source_url: string }): Promise<Feed> {
  return apiFetch<Feed>("/feeds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Upload a video file for processing. The backend starts processing asynchronously
 * and returns immediately with status "processing".
 */
export async function uploadVideo(
  file: File,
  feedId?: string,
  name?: string,
): Promise<{
  feed_id: string; id: string; status: "processing" | "active" | "error"; msg: string 
}> {
  const formData = new FormData();
  formData.append("file", file);
  if (feedId) formData.append("feed_id", feedId);
  if (name) formData.append("name", name);

  return apiFetch<{ id: string; status: "processing" | "active" | "error"; msg: string }>(
    "/feeds/upload",
    {
      method: "POST",
      body: formData,
    },
  );
}

/**
 * Delete an existing feed.
 */
export async function deleteFeed(feedId: string): Promise<{ status: string; feed_id: string }> {
  return apiFetch<{ status: string; feed_id: string }>(`/feeds/${feedId}`, { method: "DELETE" });
}

/**
 * Return the current feed state from the backend feed list. This project does not
 * expose a dedicated /feeds/{id}/status endpoint, so we reconstruct that status
 * using the canonical feed list.
 */
export async function getFeedStatus(feedId: string): Promise<{
  id: string;
  status: "processing" | "active" | "error" | "offline";
  error_message?: string;
  stream_url?: string;
  track_count?: number;
}> {
  const feeds = await getFeeds();
  const existing = feeds.find((feed) => feed.id === feedId);

  if (!existing) {
    throw new Error(`Feed ${feedId} not found`);
  }

  return {
    id: existing.id,
    status: existing.status,
    error_message: existing.error_message,
    stream_url: existing.stream_url,
    track_count: existing.track_count,
  };
}

/**
 * Resolve a stream URL to an absolute URL.
 * If the path is already a fully-qualified http(s) URL, return it as-is.
 * Otherwise (including root-relative paths like "/processed/..." returned by
 * the backend), prepend the configured API base URL -- a leading "/" is
 * relative to the FastAPI backend's origin, not the Vite dev server's.
 */
export function resolveStreamUrl(path: string | undefined): string {
  if (!path) return "";

  const normalizedPath = path.replace(/\\/g, "/");

  if (
    normalizedPath.startsWith("http://") ||
    normalizedPath.startsWith("https://")
  ) {
    return normalizedPath;
  }


  const baseUrl = import.meta.env.VITE_API_URL || "";
  return `${baseUrl.replace(/\/+$/, "")}/${normalizedPath.replace(/^\/+/, "")}`;
}