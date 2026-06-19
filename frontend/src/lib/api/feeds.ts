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
function resolveStreamUrl(streamUrl: string | undefined): string | undefined {
  if (!streamUrl) return undefined;
  // Already an absolute URL — return as-is.
  if (streamUrl.startsWith("http://") || streamUrl.startsWith("https://")) {
    return streamUrl;
  }

  // Derive the backend origin from VITE_API_BASE_URL env var, or fall back to
  // the default backend address used in development.
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
  const baseToUse = apiBase.startsWith("/") && typeof window !== "undefined"
    ? `${window.location.origin}${apiBase}`
    : apiBase;

  if (apiBase.startsWith("/")) {
    console.warn(
      "VITE_API_BASE_URL is set to a relative path. Video stream URLs need the backend origin (e.g. http://localhost:8000/api)."
    );
  }

  const encodedPath = streamUrl
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");

  try {
    return new URL(streamUrl, baseToUse).href;
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
