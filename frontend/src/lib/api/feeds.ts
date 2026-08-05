import { apiFetch, apiHeaders } from "./client";
import { cctvImages, type CCTVFeed } from "@/lib/mock-data";

interface BackendFeed {
  id: string;
  name: string;
  status: string;
  fps: number;
  source_url?: string;
  stream_url?: string;
}

function getImageForFeed(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cctvImages[index % cctvImages.length] ?? cctvImages[0];
}

/**
 * The backend stores stream_url as a relative path (e.g. "/uploads/video.mp4").
 * StaticFiles are served directly by FastAPI at its root (port 8000), NOT under
 * the /api prefix. We must prepend the backend origin so the browser's <video>
 * element can actually fetch the file.
 */
export function resolveStreamUrl(streamUrl: string | undefined): string | undefined {
  if (!streamUrl) return undefined;
  if (streamUrl.startsWith("http://") || streamUrl.startsWith("https://")) return streamUrl;

  // Get the backend base URL — must be an absolute URL (http://host:port) in production
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "/api";

  try {
    // Build an absolute URL using the API base as the reference origin
    const baseUrl = new URL(apiBase);
    const backendOrigin = baseUrl.origin;
    const normalizedPath = streamUrl.startsWith("/") ? streamUrl : `/${streamUrl}`;
    return backendOrigin + normalizedPath;
  } catch {
    // VITE_API_BASE_URL is a relative path — fall back to current window origin
    // This only works in dev (where the Vite proxy forwards /uploads to the backend)
    if (typeof window !== "undefined") {
      const normalizedPath = streamUrl.startsWith("/") ? streamUrl : `/${streamUrl}`;
      return window.location.origin + normalizedPath;
    }
    return streamUrl;
  }
}

export async function getFeeds(): Promise<CCTVFeed[]> {
  const feeds = await apiFetch<BackendFeed[]>("/feeds");
  if (!Array.isArray(feeds) || feeds.length === 0) {
    return [];
  }

  return feeds.map((feed) => ({
    id: feed.id,
    platform: feed.name,
    image: getImageForFeed(feed.id),
    streamUrl: resolveStreamUrl(feed.stream_url),
    status: feed.status === "active" ? "online" : "offline",
    peopleDetected: 0,
    boxes: [],
  }));
}

export async function createFeed(payload: {
  id: string;
  name: string;
  source_url: string;
}): Promise<{ id: string; status: string; msg: string }> {
  return apiFetch("/feeds", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// frontend/src/lib/api/feeds.ts
export async function uploadVideo(
  file: File,
  feedId?: string,
  name?: string,
): Promise<{ id: string; status: "processing" | "active" | "error"; msg: string }> {
  const formData = new FormData();
  formData.append("file", file);
  if (feedId) formData.append("feed_id", feedId);
  if (name) formData.append("name", name);

  const response = await apiFetch("/feeds/upload", {
    method: "POST",
    body: formData,
  });
  return response.json();
}

export async function deleteFeed(id: string): Promise<void> {
  const url = (import.meta.env.VITE_API_BASE_URL ?? "/api") + `/feeds/${encodeURIComponent(id)}`;
  const resp = await fetch(url, { method: "DELETE", headers: apiHeaders() });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Delete failed: ${resp.status} ${text}`);
  }
}
