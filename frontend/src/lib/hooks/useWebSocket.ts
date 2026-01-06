'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseWebSocketOptions {
  /** WebSocket URL */
  url: string;
  /** Auto-reconnect on disconnect */
  reconnect?: boolean;
  /** Reconnect interval in ms */
  reconnectInterval?: number;
  /** Max reconnect attempts */
  maxReconnectAttempts?: number;
  /** Callback when message received */
  onMessage?: (data: unknown) => void;
  /** Callback when connection opens */
  onOpen?: () => void;
  /** Callback when connection closes */
  onClose?: () => void;
  /** Callback when error occurs */
  onError?: (error: Event) => void;
}

export interface UseWebSocketReturn {
  /** Current connection status */
  status: WebSocketStatus;
  /** Send message through WebSocket */
  send: (data: unknown) => void;
  /** Manually connect */
  connect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
  /** Last received message */
  lastMessage: unknown | null;
}

export function useWebSocket({
  url,
  reconnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  onMessage,
  onOpen,
  onClose,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(reconnect);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setStatus('connecting');
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessage?.(data);
        } catch {
          // If not JSON, pass raw data
          setLastMessage(event.data);
          onMessage?.(event.data);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        onClose?.();

        // Attempt reconnect if enabled
        if (shouldReconnectRef.current && 
            reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setStatus('error');
        onError?.(error);
      };
    } catch (error) {
      setStatus('error');
      console.error('[WebSocket] Connection error:', error);
    }
  }, [url, maxReconnectAttempts, reconnectInterval, onMessage, onOpen, onClose, onError]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setStatus('disconnected');
  }, [clearReconnectTimeout]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      wsRef.current.send(message);
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    shouldReconnectRef.current = reconnect;
    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]); // Only reconnect if URL changes - intentionally omitting connect/disconnect to avoid infinite loops

  return {
    status,
    send,
    connect,
    disconnect,
    lastMessage,
  };
}
