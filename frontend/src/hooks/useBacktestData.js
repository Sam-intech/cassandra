import { useEffect, useState } from "react";
import { fetchJson } from "../lib/api";

export function useBacktestData() {
  const [data, setData] = useState([]);
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      try {
        const payload = await fetchJson("/backtest/ftx");
        if (ignore) return;

        if (payload.error) {
          const searchedPaths = Array.isArray(payload.searched_paths)
            ? ` Searched: ${payload.searched_paths.join(", ")}`
            : "";
          setError(`${payload.error}${searchedPaths}`);
          return;
        }

        const normalized = (payload.data || []).map((row) => ({
          ...row,
          vpin: Number(row.vpin),
          timestamp: row.timestamp,
        }));

        setData(normalized);
        setEvents(payload.events || []);
        setSummary(payload.summary || null);
      } catch (err) {
        if (!ignore) {
          setError(err.message || "Failed to load backtest data.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      ignore = true;
    };
  }, []);

  return { data, events, summary, loading, error };
}
