const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const apiKey = import.meta.env.VITE_RAILMIND_API_KEY?.trim();

function buildUrl(path: string) {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export function apiHeaders(headers?: HeadersInit) {
  const merged = new Headers(headers);
  if (apiKey && !merged.has("X-API-Key")) {
    merged.set("X-API-Key", apiKey);
  }
  return merged;
}

export async function apiFetch<T = unknown>(path: string, options: RequestInit = {}) {
  const headers = apiHeaders(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    headers: {
      ...Object.fromEntries(headers.entries()),
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }

  return (await response.json()) as T;
}
