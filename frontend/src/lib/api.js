const DEFAULT_API = "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API).replace(/\/$/, "");
}

export function getWebsocketUrl() {
  const apiBase = getApiBaseUrl();
  if (apiBase.startsWith("https://")) {
    return `${apiBase.replace("https://", "wss://")}/ws`;
  }
  return `${apiBase.replace("http://", "ws://")}/ws`;
}

export async function fetchJson(path, options = {}) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed (${response.status})`);
  }

  return response.json();
}
