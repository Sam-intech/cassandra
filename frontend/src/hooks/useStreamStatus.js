import { useCallback, useEffect, useState } from "react";
import { fetchJson } from "../lib/api";

export function useStreamStatus(intervalMs = 5000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const data = await fetchJson("/stream/status");
      setStatus(data);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to fetch stream status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs, refresh]);

  return { status, loading, error, refresh };
}
