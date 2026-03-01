const DEFAULT_API = "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API).replace(/\/$/, "");
}

function normalizeBase(base) {
  return base ? base.replace(/\/+$/, "") : "";
}

function addLocalDevCandidates(candidates) {
  const localBases = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
  ];
  for (const base of localBases) {
    candidates.add(normalizeBase(base));
  }
}

function getApiCandidates() {
  const configured = normalizeBase(getApiBaseUrl());
  const candidates = new Set([configured]);

  try {
    const parsed = new URL(configured);
    const origin = normalizeBase(parsed.origin);
    candidates.add(origin);

    const segments = parsed.pathname.split("/").filter(Boolean);
    let pathPrefix = "";
    for (const segment of segments) {
      pathPrefix += `/${segment}`;
      candidates.add(normalizeBase(`${origin}${pathPrefix}`));
    }
  } catch {
    // Keep configured base URL only.
  }

  if (typeof window !== "undefined") {
    candidates.add(normalizeBase(window.location.origin));
    candidates.add("");
  }

  addLocalDevCandidates(candidates);

  const expanded = new Set();
  for (const candidate of candidates) {
    if (!candidate) {
      expanded.add(candidate);
      continue;
    }
    expanded.add(candidate);
    if (candidate.includes("127.0.0.1")) {
      expanded.add(candidate.replace("127.0.0.1", "localhost"));
    } else if (candidate.includes("localhost")) {
      expanded.add(candidate.replace("localhost", "127.0.0.1"));
    }
  }

  return [...expanded];
}

function getPathCandidates(path) {
  if (!path.startsWith("/")) {
    return [path];
  }

  const candidates = [path];
  if (!path.startsWith("/api/") && path !== "/api") {
    candidates.push(`/api${path}`);
  }
  return candidates;
}

function toWebsocketUrl(base, path) {
  if (!base) return path;
  if (base.startsWith("https://")) return `${base.replace("https://", "wss://")}${path}`;
  if (base.startsWith("http://")) return `${base.replace("http://", "ws://")}${path}`;
  return `${base}${path}`;
}

export function getWebsocketCandidates() {
  const candidates = new Set();
  const wsPaths = getPathCandidates("/ws");

  for (const baseUrl of getApiCandidates()) {
    for (const wsPath of wsPaths) {
      candidates.add(toWebsocketUrl(baseUrl, wsPath));
    }
  }

  return [...candidates];
}

export function getWebsocketUrl() {
  return getWebsocketCandidates()[0];
}

export async function fetchJson(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const shouldSetJsonContentType = method !== "GET" && method !== "HEAD";
  const baseHeaders = shouldSetJsonContentType ? { "Content-Type": "application/json" } : {};

  let lastError = null;

  for (const baseUrl of getApiCandidates()) {
    for (const pathCandidate of getPathCandidates(path)) {
      try {
        const url = `${baseUrl}${pathCandidate}`;
        const response = await fetch(url, {
          headers: {
            ...baseHeaders,
            ...(options.headers || {}),
          },
          ...options,
        });

        if (!response.ok) {
          const raw = await response.text();
          let message = raw;
          try {
            const parsed = JSON.parse(raw);
            message = parsed.detail || parsed.error || raw;
          } catch {
            // Keep raw text fallback
          }
          const error = new Error(message || `Request failed (${response.status})`);
          error.status = response.status;
          throw error;
        }

        return await response.json();
      } catch (error) {
        lastError = error;
      }
    }
  }

  throw lastError || new Error("Failed to fetch");
}

export async function fetchJsonAny(paths, options = {}) {
  let lastError = null;
  for (const path of paths) {
    try {
      return await fetchJson(path, options);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("Failed to fetch");
}
