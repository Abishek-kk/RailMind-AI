const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

function buildUrl(path: string) {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export async function apiFetch<T = unknown>(path: string, options: RequestInit = {}) {
  const response = await fetch(buildUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText} \n${body}`);
  }

  return (await response.json()) as T;
}
