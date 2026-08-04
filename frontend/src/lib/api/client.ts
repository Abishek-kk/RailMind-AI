const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
let hasWarnedAboutPublicApiKey = false;

function shouldWarnAboutApiKey(apiKey: string): boolean {
  if (!import.meta.env.DEV) return false;
  if (hasWarnedAboutPublicApiKey) return false;

  const normalizedKey = apiKey.toLowerCase();
  return (
    !normalizedKey.includes("change-this") &&
    !normalizedKey.includes("dev") &&
    !normalizedKey.includes("test")
  );
}

export function getApiKey(): string | undefined {
  if (typeof window !== "undefined") {
    const runtimeKey = (window as Window & { __RAILMIND_API_KEY?: string }).__RAILMIND_API_KEY;
    if (typeof runtimeKey === "string") {
      const trimmedRuntimeKey = runtimeKey.trim();
      if (trimmedRuntimeKey) return trimmedRuntimeKey;
    }
  }

  // VITE_RAILMIND_API_KEY is bundled into client-side JavaScript by Vite.
  // It is only safe for local/dev demos. Production deployments should proxy
  // authenticated requests through a backend-for-frontend that attaches the API
  // key server-side instead of shipping it to the browser.
  const buildTimeKey = import.meta.env.VITE_RAILMIND_API_KEY?.trim();
  if (buildTimeKey) {
    if (shouldWarnAboutApiKey(buildTimeKey)) {
      hasWarnedAboutPublicApiKey = true;
      console.warn(
        "RailMind: VITE_RAILMIND_API_KEY appears to be a non-placeholder value. Remember this key is publicly visible in the browser bundle — see SECURITY.md.",
      );
    }
    return buildTimeKey;
  }

  return undefined;
}

function buildUrl(path: string) {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export function apiHeaders(headers?: HeadersInit) {
  const merged = new Headers(headers);
  const apiKey = getApiKey();
  if (apiKey && !merged.has("X-API-Key")) {
    merged.set("X-API-Key", apiKey);
  }
  return merged;
}

export async function apiFetch<T = unknown>(path: string, options: RequestInit = {}) {
  const headers = apiHeaders(options.headers);
  const hasBody = options.body !== undefined && options.body !== null;
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!headers.has("Content-Type") && hasBody && !isFormData) {
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

  if (response.status === 204) {
    return null as T;
  }

  const text = await response.text();
  if (!text || !text.trim()) {
    return null as T;
  }

  return JSON.parse(text) as T;
}
