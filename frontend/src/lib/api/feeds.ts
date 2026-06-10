import { apiFetch } from "./client";
import { cctvImages, type CCTVFeed } from "@/lib/mock-data";

interface BackendFeed {
  id: string;
  name: string;
  status: string;
  fps: number;
}

function getDisplayFeedId(cameraId: string, index: number) {
  const match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-](\d+))/i);
  const number = match ? Number(match[1] ?? match[2]) : NaN;
  if (!Number.isFinite(number) || number <= 0) {
    return `CCTV-${index + 1}`;
  }
  return `CCTV-${number}`;
}

function getImageForFeed(cameraId: string) {
  const match = cameraId.match(/\d+/);
  const index = match ? Number(match[0]) - 1 : 0;
  return cctvImages[index % cctvImages.length] ?? cctvImages[0];
}

export async function getFeeds(): Promise<CCTVFeed[]> {
  const feeds = await apiFetch<BackendFeed[]>('/feeds');
  return (Array.isArray(feeds) ? feeds : []).map((feed, index) => ({
    id: getDisplayFeedId(feed.id, index),
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
  url: string;
}): Promise<{ id: string; status: string; msg: string }> {
  return apiFetch("/feeds", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
