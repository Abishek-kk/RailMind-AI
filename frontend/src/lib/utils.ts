import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function parseCameraId(cameraId: string): string {
  const match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-](\d+))/i);
  const number = match ? Number(match[1] ?? match[2]) : NaN;
  if (Number.isFinite(number) && number > 0) {
    return `CCTV-${number}`;
  }

  const fallback = cameraId.match(/\d+/);
  return fallback ? `CCTV-${Number(fallback[0])}` : cameraId;
}
