import { useCallback, useEffect, useRef, useState } from "react";

export function useWebSocket<T>(url: string, reconnectDelay = 2000) {
  const [latestMessage, setLatestMessage] = useState<T | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const shouldReconnect = useRef(true);

  const cleanup = useCallback(() => {
    shouldReconnect.current = false;
    if (reconnectTimeout.current) {
      window.clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    cleanup();
    shouldReconnect.current = true;

    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setLatestMessage(parsed);
      } catch (error) {
        console.warn("useWebSocket: failed to parse message", error);
      }
    });

    socket.addEventListener("close", () => {
      if (!shouldReconnect.current) {
        return;
      }
      reconnectTimeout.current = window.setTimeout(connect, reconnectDelay);
    });

    socket.addEventListener("error", () => {
      socket.close();
    });
  }, [cleanup, reconnectDelay, url]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  return latestMessage;
}
