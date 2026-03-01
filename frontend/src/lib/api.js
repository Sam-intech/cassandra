const DEFAULT_API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return DEFAULT_API.replace(/\/$/, "");
}

export function getWebsocketUrl() {
  const base = getApiBaseUrl();
  if (base.startsWith("https://")) {
    return base.replace("https://", "wss://") + "/ws";
  }
  return base.replace("http://", "ws://") + "/ws";
}

export async function fetchJson(path, options = {}) {
  const url = `${getApiBaseUrl()}${path}`;
  const response = await fetch(url, {
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