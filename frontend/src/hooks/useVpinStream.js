import { useEffect, useMemo, useRef, useState } from "react";
import { getWebsocketUrl } from "../lib/api";

const MAX_POINTS = 200;

function normalizePoint(point) {
  return {
    timestamp: point.timestamp,
    vpin: Number(point.vpin),
    alert_level: point.alert_level,
    trade_count: point.trade_count,
    latest_price: point.latest_price,
  };
}

export function useVpinStream() {
  const [livePoints, setLivePoints] = useState([]);
  const [latestUpdate, setLatestUpdate] = useState(null);
  const [latestBrief, setLatestBrief] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState("");
  const socketRef = useRef(null);
  const retryRef = useRef(null);
  const wsCandidateIndexRef = useRef(0);

  useEffect(() => {
    let isClosed = false;
    const wsUrl = getWebsocketUrl();

    if (!wsUrl) {
      setConnectionError("No websocket URL available.");
      return () => {};
    }

    const connect = () => {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setConnectionError("");
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === "history") {
            const normalized = (message.data || [])
              .map(normalizePoint)
              .filter((point) => !Number.isNaN(point.vpin));
            setLivePoints(normalized.slice(-MAX_POINTS));
            if (normalized.length > 0) {
              setLatestUpdate(normalized[normalized.length - 1]);
            }
            return;
          }

          if (message.type === "vpin_update") {
            const point = normalizePoint(message.data);
            if (Number.isNaN(point.vpin)) return;
            setLivePoints((prev) => [...prev.slice(-(MAX_POINTS - 1)), point]);
            setLatestUpdate(point);
            return;
          }

          if (message.type === "intelligence_brief") {
            setLatestBrief(message.data || null);
            return;
          }

          if (message.type === "system_reset") {
            setLivePoints([]);
            setLatestUpdate(null);
            setLatestBrief(null);
          }
        } catch {
          setConnectionError("Received malformed websocket payload.");
        }
      };

      socket.onerror = () => {
        setConnectionError("Websocket connection error.");
      };

      socket.onclose = () => {
        setIsConnected(false);
        if (!isClosed) {
          wsCandidateIndexRef.current += 1;
          retryRef.current = window.setTimeout(connect, 2000);
        }
      };
    };

    connect();

    return () => {
      isClosed = true;
      if (retryRef.current) {
        window.clearTimeout(retryRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const currentVpin = useMemo(() => {
    if (!latestUpdate) return null;
    return latestUpdate.vpin;
  }, [latestUpdate]);

  const clearStreamData = () => {
    setLivePoints([]);
    setLatestUpdate(null);
    setLatestBrief(null);
  };

  return {
    livePoints,
    latestUpdate,
    latestBrief,
    currentVpin,
    isConnected,
    connectionError,
    clearStreamData,
  };
}
