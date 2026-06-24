import { useCallback, useEffect, useRef, useState } from "react";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

const apiKey = import.meta.env.VITE_RAILMIND_API_KEY?.trim();

function buildAuthenticatedWebSocketUrl(url: string) {
  if (!apiKey) {
    return url;
  }

  const websocketUrl = new URL(url);
  websocketUrl.searchParams.set("api_key", apiKey);
  return websocketUrl.toString();
}

export function useWebSocket<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const retryCount = useRef(0);
  const isUnmounted = useRef(false);

  const clearReconnect = useCallback(() => {
    if (reconnectTimeout.current !== null) {
      window.clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
  }, []);

  const closeSocket = useCallback(() => {
    const socket = socketRef.current;
    if (socket) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      socket.onerror = null;
      socket.close();
      socketRef.current = null;
    }
  }, []);

  const scheduleReconnect = useCallback((connectFn: () => void) => {
    if (isUnmounted.current) {
      return;
    }

    if (retryCount.current >= 5) {
      setError("Unable to connect to real-time updates after several attempts.");
      setStatus("error");
      return;
    }

    const delay = Math.min(30000, 1000 * 2 ** retryCount.current);
    retryCount.current += 1;
    reconnectTimeout.current = window.setTimeout(() => {
      reconnectTimeout.current = null;
      if (!isUnmounted.current) {
        connectFn();
      }
    }, delay);
  }, []);

  const connect = useCallback(() => {
    if (typeof window === "undefined" || isUnmounted.current) {
      return;
    }

    clearReconnect();
    closeSocket();
    setStatus("connecting");
    setError(null);

    const socket = new WebSocket(buildAuthenticatedWebSocketUrl(url));
    socketRef.current = socket;

    socket.onopen = () => {
      if (isUnmounted.current) {
        socket.close();
        return;
      }

      retryCount.current = 0;
      setError(null);
      setStatus("connected");
    };

    socket.onmessage = (event) => {
      if (isUnmounted.current) {
        return;
      }
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
      } catch (error) {
        console.warn("useWebSocket: failed to parse message", error);
      }
    };

    socket.onclose = (event) => {
      socketRef.current = null;
      if (isUnmounted.current) {
        setStatus("disconnected");
        return;
      }

      if (event.code === 1008) {
        const reason = event.reason || "WebSocket connection rejected by server origin policy.";
        setError(reason);
        setStatus("error");
        return;
      }

      if (retryCount.current >= 5) {
        setError("Unable to connect to real-time updates after several attempts.");
        setStatus("error");
        return;
      }

      setStatus("disconnected");
      scheduleReconnect(connect);
    };

    socket.onerror = (event) => {
      console.error("useWebSocket: socket error", event);
      setError("WebSocket error occurred while connecting to real-time updates.");
      setStatus("error");
      socket.close();
    };
  }, [clearReconnect, closeSocket, scheduleReconnect, url]);

  useEffect(() => {
    isUnmounted.current = false;
    connect();

    return () => {
      isUnmounted.current = true;
      clearReconnect();
      closeSocket();
      setStatus("disconnected");
    };
  }, [connect, clearReconnect, closeSocket]);

  const reconnect = useCallback(() => {
    if (isUnmounted.current) {
      return;
    }
    clearReconnect();
    closeSocket();
    setStatus("connecting");
    setError(null);
    connect();
  }, [clearReconnect, closeSocket, connect]);

  return { data, status, error, reconnect } as const;
}
