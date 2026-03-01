import { useCallback, useEffect, useState } from "react";
import { fetchJson } from "../lib/api";

export function useIntelligenceBrief(intervalMs = 10000) {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const payload = await fetchJson("/agent/brief");
      setBrief(payload.brief || null);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to fetch intelligence brief.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs, refresh]);

  return { brief, loading, error, refresh, setBrief };
}
