import { useCallback, useEffect, useState } from "react";
import { fetchJson } from "../lib/api";

export function useStreamStatus(intervalMs = 5000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

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

  const setStreaming = useCallback(
    async (shouldStream) => {
      setActionLoading(true);
      setActionError("");
      try {
        await fetchJson(shouldStream ? "/stream/start" : "/stream/stop", {
          method: "POST",
        });
        await refresh();
        return true;
      } catch (err) {
        setActionError(err.message || "Failed to update stream state.");
        return false;
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  const resetSystem = useCallback(
    async (startStream = true) => {
      setActionLoading(true);
      setActionError("");
      try {
        await fetchJson(`/system/reset?start_stream=${startStream}`, {
          method: "POST",
        });
        await refresh();
        return true;
      } catch (err) {
        setActionError(err.message || "Failed to reset system.");
        return false;
      } finally {
        setActionLoading(false);
      }
    },
    [refresh]
  );

  return {
    status,
    loading,
    error,
    refresh,
    setStreaming,
    resetSystem,
    actionLoading,
    actionError,
  };
}