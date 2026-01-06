'use client';

import React from 'react';
import { Icon, Button } from '../common';
import type { Task, ColumnType } from '@/lib/types';

export interface DraggableColumnProps {
  /** Column identifier */
  id: ColumnType;
  /** Column title */
  title: string;
  /** Time range description */
  timeRange: string;
  /** Tasks in this column */
  tasks: Task[];
  /** Whether this column is a drop target */
  isDropTarget?: boolean;
  /** Callback when add task button is clicked */
  onAddTask?: () => void;
  /** Callback when more options is clicked */
  onMoreOptions?: () => void;
  /** Handler for drag over event */
  onDragOver?: (e: React.DragEvent) => void;
  /** Handler for drag leave event */
  onDragLeave?: (e: React.DragEvent) => void;
  /** Handler for drop event */
  onDrop?: (e: React.DragEvent) => void;
  /** Children (task cards) */
  children?: React.ReactNode;
}

/**
 * DraggableColumn - Kanban column with drag-and-drop support
 */
export function DraggableColumn({
  id,
  title,
  timeRange,
  tasks,
  isDropTarget = false,
  onAddTask,
  onMoreOptions,
  onDragOver,
  onDragLeave,
  onDrop,
  children,
}: DraggableColumnProps) {
  // Visual feedback when column is a drop target
  const dropTargetStyles = isDropTarget
    ? 'ring-2 ring-primary ring-offset-2 bg-primary/5'
    : '';

  return (
    <div
      className={`
        kanban-column 
        min-w-[320px] flex-shrink-0 
        bg-sand-50 border border-sand-200 
        rounded-3xl p-6 
        flex flex-col gap-4 
        shadow-soft 
        scroll-snap-align-start
        transition-all duration-200
        ${dropTargetStyles}
      `}
      data-column-id={id}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
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
      <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2 scrollbar-thin min-h-[100px]">
        {children}
        
        {/* Drop zone indicator when empty and being dragged over */}
        {isDropTarget && React.Children.count(children) === 0 && (
          <div className="flex-1 flex items-center justify-center border-2 border-dashed border-primary/30 rounded-xl p-4">
            <p className="text-primary/60 text-sm font-medium">Drop task here</p>
          </div>
        )}
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
