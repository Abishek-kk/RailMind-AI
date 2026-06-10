import { useCallback, useEffect, useRef, useState } from "react";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>("connecting");
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

  const scheduleReconnect = useCallback(
    (connectFn: () => void) => {
      if (isUnmounted.current || retryCount.current >= 5) {
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
    },
    [],
  );

  const connect = useCallback(() => {
    if (typeof window === "undefined" || isUnmounted.current) {
      return;
    }

    clearReconnect();
    closeSocket();
    setStatus("connecting");

    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      if (isUnmounted.current) {
        socket.close();
        return;
      }

      retryCount.current = 0;
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

    socket.onclose = () => {
      socketRef.current = null;
      if (isUnmounted.current) {
        setStatus("disconnected");
        return;
      }
      setStatus("disconnected");
      scheduleReconnect(connect);
    };

    socket.onerror = (event) => {
      console.error("useWebSocket: socket error", event);
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

  return { data, status } as const;
}
