'use client';

import { useState, useCallback, useEffect } from 'react';
import { useWebSocket, type WebSocketStatus } from './useWebSocket';
import type { Notification } from '@/lib/types';

// API URL from environment or default
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws/notifications';

export interface UseNotificationsOptions {
  /** Enable WebSocket connection */
  enabled?: boolean;
  /** Callback when new notification received */
  onNotification?: (notification: Notification) => void;
}

export interface UseNotificationsReturn {
  /** List of notifications */
  notifications: Notification[];
  /** Unread notification count */
  unreadCount: number;
  /** WebSocket connection status */
  connectionStatus: WebSocketStatus;
  /** Mark notification as read */
  markAsRead: (id: string) => void;
  /** Mark all notifications as read */
  markAllAsRead: () => void;
  /** Clear all notifications */
  clearAll: () => void;
  /** Add notification manually (for testing) */
  addNotification: (notification: Notification) => void;
}

export function useNotifications({
  enabled = true,
  onNotification,
}: UseNotificationsOptions = {}): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const handleMessage = useCallback((data: unknown) => {
    // Parse notification from WebSocket message
    const notification = parseNotification(data);
    if (notification) {
      setNotifications((prev) => [notification, ...prev]);
      onNotification?.(notification);
    }
  }, [onNotification]);

  const { status: connectionStatus } = useWebSocket({
    url: WS_URL,
    reconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    onMessage: handleMessage,
    onOpen: () => {
      console.log('[Notifications] WebSocket connected');
    },
    onClose: () => {
      console.log('[Notifications] WebSocket disconnected');
    },
    onError: (error) => {
      console.error('[Notifications] WebSocket error:', error);
    },
  });

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const addNotification = useCallback((notification: Notification) => {
    setNotifications((prev) => [notification, ...prev]);
    onNotification?.(notification);
  }, [onNotification]);

  return {
    notifications,
    unreadCount,
    connectionStatus,
    markAsRead,
    markAllAsRead,
    clearAll,
    addNotification,
  };
}

/**
 * Parse notification from WebSocket message
 */
function parseNotification(data: unknown): Notification | null {
  if (!data || typeof data !== 'object') return null;

  const obj = data as Record<string, unknown>;
  
  // Check if it's a notification message
  if (obj.type === 'notification' && obj.payload) {
    const payload = obj.payload as Record<string, unknown>;
    return {
      id: String(payload.id || Date.now()),
      type: (payload.type as Notification['type']) || 'suggestion',
      title: String(payload.title || ''),
      message: payload.message ? String(payload.message) : undefined,
      isRead: Boolean(payload.isRead),
      createdAt: payload.createdAt ? new Date(String(payload.createdAt)) : new Date(),
    };
  }

  // Direct notification object
  if (obj.id && obj.title) {
    return {
      id: String(obj.id),
      type: (obj.type as Notification['type']) || 'suggestion',
      title: String(obj.title),
      message: obj.message ? String(obj.message) : undefined,
      isRead: Boolean(obj.isRead),
      createdAt: obj.createdAt ? new Date(String(obj.createdAt)) : new Date(),
    };
  }

  return null;
}
