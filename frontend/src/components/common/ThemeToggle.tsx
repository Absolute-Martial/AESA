'use client';

import React from 'react';
import { useTheme } from '@/lib/contexts';
import { Icon } from './Icon';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className = '', showLabel = false }: ThemeToggleProps) {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {showLabel && (
        <span className="text-sm text-text-muted dark:text-gray-400">Theme:</span>
      )}
      
      {/* Simple toggle button */}
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg bg-sand-100 dark:bg-gray-800 hover:bg-sand-200 dark:hover:bg-gray-700 transition-colors"
        aria-label={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
        title={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
      >
        <Icon
          name={resolvedTheme === 'light' ? 'dark_mode' : 'light_mode'}
          className="text-text-main dark:text-gray-200"
          size={20}
        />
      </button>

      {/* Theme selector dropdown (optional, for more control) */}
      {showLabel && (
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
          className="text-sm px-2 py-1 rounded-md border border-sand-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-text-main dark:text-gray-200"
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System</option>
        </select>
      )}
    </div>
  );
}
