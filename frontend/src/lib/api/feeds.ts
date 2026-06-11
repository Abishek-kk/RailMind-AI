import { apiFetch } from "./client";
import { cctvImages, type CCTVFeed } from "@/lib/mock-data";

interface BackendFeed {
  id: string;
  name: string;
  status: string;
  fps: number;
}

function getImageForFeed(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cctvImages[index % cctvImages.length] ?? cctvImages[0];
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
  const resp = await fetch(url, { method: "DELETE" });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Delete failed: ${resp.status} ${text}`);
  }
}
