import { apiFetch, apiHeaders } from "./client";
import { getCameraImage, type CCTVFeed } from "@/lib/railmind-types";

interface BackendFeed {
  id: string;
  name: string;
  status: string;
  fps: number;
  source_url?: string;
  stream_url?: string;
}

/**
 * The backend stores stream_url as a relative path (e.g. "/uploads/video.mp4").
 * StaticFiles are served directly by FastAPI at its root (port 8000), NOT under
 * the /api prefix. We must prepend the backend origin so the browser's <video>
 * element can actually fetch the file.
 */
export function resolveStreamUrl(
  streamUrl: string | undefined,
  apiBase: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"
): string | undefined {
  if (!streamUrl) return undefined;
  if (streamUrl.startsWith("http://") || streamUrl.startsWith("https://")) {
    return streamUrl;
  }

  const normalizedApiBase = apiBase?.trim() || "http://localhost:8000/api";
  const baseToUse = normalizedApiBase.startsWith("/") && typeof window !== "undefined"
    ? `${window.location.origin}${normalizedApiBase}`
    : normalizedApiBase;

  const encodedPath = streamUrl
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");

  try {
    return new URL(encodedPath, baseToUse).href;
  } catch {
    try {
      const origin = new URL(baseToUse).origin;
      return streamUrl.startsWith("/") ? `${origin}${encodedPath}` : `${origin}/${encodedPath}`;
    } catch {
      return streamUrl;
    }
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
    image: getCameraImage(feed.id),
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

export async function uploadVideo(file: File, feed_id?: string, name?: string) {
  const form = new FormData();
  form.append("file", file, file.name);
  if (feed_id) form.append("feed_id", feed_id);
  if (name) form.append("name", name);

  const url = (import.meta.env.VITE_API_BASE_URL ?? "/api") + "/feeds/upload";
  const resp = await fetch(url, {
    method: "POST",
    headers: apiHeaders(),
    body: form,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Upload failed: ${resp.status} ${text}`);
  }
  return await resp.json();
}

export async function deleteFeed(id: string): Promise<void> {
  const url = (import.meta.env.VITE_API_BASE_URL ?? "/api") + `/feeds/${encodeURIComponent(id)}`;
  const resp = await fetch(url, { method: "DELETE", headers: apiHeaders() });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Delete failed: ${resp.status} ${text}`);
  }
}
