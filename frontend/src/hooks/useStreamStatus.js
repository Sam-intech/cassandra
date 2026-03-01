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