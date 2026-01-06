'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Icon } from './Icon';
import { Badge } from './Badge';
import { useNotifications } from '@/lib/hooks/useNotifications';
import type { Notification } from '@/lib/types';

export interface NotificationCenterProps {
  className?: string;
}

const notificationIcons: Record<Notification['type'], string> = {
  reminder: 'alarm',
  suggestion: 'lightbulb',
  achievement: 'emoji_events',
  warning: 'warning',
  motivation: 'favorite',
};

const notificationColors: Record<Notification['type'], string> = {
  reminder: 'text-blue-500',
  suggestion: 'text-primary',
  achievement: 'text-yellow-500',
  warning: 'text-orange-500',
  motivation: 'text-pink-500',
};

export function NotificationCenter({ className = '' }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const {
    notifications,
    unreadCount,
    connectionStatus,
    markAsRead,
    markAllAsRead,
    clearAll,
  } = useNotifications();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg bg-sand-100 dark:bg-gray-800 hover:bg-sand-200 dark:hover:bg-gray-700 transition-colors"
        aria-label="Notifications"
      >
        <Icon
          name="notifications"
          className="text-text-main dark:text-gray-200"
          size={20}
        />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-medium rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}

        {/* Connection Status Indicator */}
        <span
          className={`absolute bottom-1 right-1 w-2 h-2 rounded-full ${
            connectionStatus === 'connected'
              ? 'bg-green-500'
              : connectionStatus === 'connecting'
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-gray-400'
          }`}
          title={`WebSocket: ${connectionStatus}`}
        />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-sand-200 dark:border-gray-700 overflow-hidden z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-sand-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-medium text-text-main dark:text-gray-100">
              Notifications
            </h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-primary hover:text-primary-600"
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={clearAll}
                  className="text-xs text-text-muted dark:text-gray-400 hover:text-text-main dark:hover:text-gray-200"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto scrollbar-thin">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-text-muted dark:text-gray-400">
                <Icon name="notifications_off" size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No notifications yet</p>
              </div>
            ) : (
              <ul>
                {notifications.map((notification: Notification) => (
                  <li
                    key={notification.id}
                    onClick={() => markAsRead(notification.id)}
                    className={`
                      px-4 py-3 border-b border-sand-100 dark:border-gray-700 last:border-0
                      cursor-pointer hover:bg-sand-50 dark:hover:bg-gray-750 transition-colors
                      ${!notification.isRead ? 'bg-primary/5 dark:bg-primary/10' : ''}
                    `}
                  >
                    <div className="flex gap-3">
                      {/* Icon */}
                      <div className={`flex-shrink-0 ${notificationColors[notification.type]}`}>
                        <Icon name={notificationIcons[notification.type]} size={20} />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className={`text-sm font-medium ${!notification.isRead ? 'text-text-main dark:text-gray-100' : 'text-text-muted dark:text-gray-400'}`}>
                            {notification.title}
                          </p>
                          {!notification.isRead && (
                            <span className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-1.5" />
                          )}
                        </div>
                        {notification.message && (
                          <p className="text-xs text-text-muted dark:text-gray-400 mt-0.5 line-clamp-2">
                            {notification.message}
                          </p>
                        )}
                        <p className="text-xs text-text-light dark:text-gray-500 mt-1">
                          {formatTime(notification.createdAt)}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
