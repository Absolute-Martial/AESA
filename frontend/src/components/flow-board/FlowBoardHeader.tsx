'use client';

import React from 'react';
import type { DayStats } from '@/lib/types';

export interface FlowBoardHeaderProps {
  /** Current date */
  date: Date;
  /** Daily statistics */
  stats?: DayStats;
}

/**
 * Format date for display
 */
function formatDate(date: Date): string {
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  };
  return date.toLocaleDateString('en-US', options);
}

/**
 * Format minutes to hours and minutes string
 */
function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * Header component for the Flow Board showing date and daily stats
 */
export function FlowBoardHeader({ date, stats }: FlowBoardHeaderProps) {
  const formattedDate = formatDate(date);
  
  return (
    <div className="flex items-end justify-between mb-8 flex-shrink-0">
      {/* Date and Title */}
      <div>
        <p className="text-primary font-display text-sm font-medium mb-1 uppercase tracking-wider">
          {formattedDate}
        </p>
        <h2 className="text-text-main text-4xl font-display font-bold tracking-tight">
          Today&apos;s Flow Board
        </h2>
      </div>
      
      {/* Daily Stats */}
      {stats && (
        <div className="hidden md:flex gap-6">
          <div className="flex flex-col items-end">
            <span className="text-2xl font-display font-bold text-text-main">
              {formatDuration(stats.focusTimeMinutes)}
            </span>
            <span className="text-xs text-text-muted font-medium">Focus Time</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-2xl font-display font-bold text-text-main">
              {stats.energyLevel}%
            </span>
            <span className="text-xs text-text-muted font-medium">Energy Level</span>
          </div>
        </div>
      )}
    </div>
  );
}
