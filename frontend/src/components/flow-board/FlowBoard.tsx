'use client';

import React from 'react';
import { Column, COLUMN_CONFIG } from './Column';
import { FlowBoardHeader } from './FlowBoardHeader';
import type { Task, DayStats, ColumnType } from '@/lib/types';

export interface FlowBoardProps {
  /** Current date */
  date: Date;
  /** Daily statistics */
  stats?: DayStats;
  /** Tasks organized by column */
  tasksByColumn: Record<ColumnType, Task[]>;
  /** Active task ID (currently in progress) */
  activeTaskId?: string;
  /** Callback when a task is moved between columns */
  onTaskMove?: (taskId: string, targetColumn: ColumnType) => void;
  /** Callback when add task is clicked for a column */
  onAddTask?: (column: ColumnType) => void;
  /** Render function for task cards */
  renderTaskCard: (task: Task, isActive: boolean) => React.ReactNode;
}

const COLUMN_ORDER: ColumnType[] = ['morning', 'afternoon', 'evening', 'backlog'];

/**
 * FlowBoard - Main Kanban-style board for daily task management
 */
export function FlowBoard({
  date,
  stats,
  tasksByColumn,
  activeTaskId,
  onTaskMove,
  onAddTask,
  renderTaskCard,
}: FlowBoardProps) {
  return (
    <main className="flex-1 h-full flex flex-col p-6 overflow-x-hidden">
      {/* Header with date and stats */}
      <FlowBoardHeader date={date} stats={stats} />

      {/* Columns Container */}
      <div className="flex-1 grid grid-cols-1 gap-6 pb-4 xl:grid-cols-2">
        {COLUMN_ORDER.map((columnId) => {
          const config = COLUMN_CONFIG[columnId];
          const tasks = tasksByColumn[columnId] || [];

          return (
            <Column
              key={columnId}
              id={columnId}
              title={config.title}
              timeRange={config.timeRange}
              tasks={tasks}
              onAddTask={() => onAddTask?.(columnId)}
            >
              {tasks.map((task) => (
                <React.Fragment key={task.id}>
                  {renderTaskCard(task, task.id === activeTaskId)}
                </React.Fragment>
              ))}
            </Column>
          );
        })}
      </div>
    </main>
  );
}
