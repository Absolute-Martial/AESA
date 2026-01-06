'use client';

import React from 'react';
import { Icon, Button } from '../common';
import type { Task, ColumnType } from '@/lib/types';

export interface ColumnProps {
  /** Column identifier */
  id: ColumnType;
  /** Column title */
  title: string;
  /** Time range description */
  timeRange: string;
  /** Tasks in this column */
  tasks: Task[];
  /** Callback when add task button is clicked */
  onAddTask?: () => void;
  /** Callback when more options is clicked */
  onMoreOptions?: () => void;
  /** Children (task cards) */
  children?: React.ReactNode;
}

/**
 * Kanban column component for the Flow Board
 */
export function Column({
  id,
  title,
  timeRange,
  tasks,
  onAddTask,
  onMoreOptions,
  children,
}: ColumnProps) {
  return (
    <div
      className="kanban-column w-full min-w-0 bg-sand-50 border border-sand-200 rounded-3xl p-6 flex flex-col gap-4 shadow-soft"
      data-column-id={id}
    >
      {/* Column Header */}
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-xl font-display font-bold text-text-main">{title}</h3>
        <button
          onClick={onMoreOptions}
          className="text-text-muted hover:text-text-main transition-colors"
          aria-label="More options"
        >
          <Icon name="more_horiz" size={20} />
        </button>
      </div>
      
      {/* Time Range */}
      <p className="text-sm text-text-muted">{timeRange}</p>
      
      {/* Task Cards Container */}
      <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2 scrollbar-thin">
        {children}
      </div>
      
      {/* Add Task Button */}
      <Button
        variant="ghost"
        fullWidth
        icon="add_circle"
        onClick={onAddTask}
        className="py-3 rounded-xl bg-sand/50 text-text-muted hover:bg-sand hover:text-text-main"
      >
        Add Task
      </Button>
    </div>
  );
}

/** Column configuration for the Flow Board */
export const COLUMN_CONFIG: Record<ColumnType, { title: string; timeRange: string }> = {
  morning: {
    title: 'Morning Deep Work',
    timeRange: '9:00 AM - 12:00 PM',
  },
  afternoon: {
    title: 'Afternoon Tasks',
    timeRange: '12:00 PM - 5:00 PM',
  },
  evening: {
    title: 'Evening Wind-down',
    timeRange: '5:00 PM - 8:00 PM',
  },
  backlog: {
    title: 'Upcoming / Backlog',
    timeRange: 'Tasks for later or next day',
  },
};
