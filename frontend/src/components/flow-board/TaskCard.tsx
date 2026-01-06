'use client';

import React from 'react';
import { Icon } from '../common';
import type { Task, TaskType } from '@/lib/types';

export interface TaskCardProps {
  /** Task data */
  task: Task;
  /** Whether this task is currently active */
  isActive?: boolean;
  /** Whether the task is completed */
  isCompleted?: boolean;
  /** Callback when card is clicked */
  onClick?: () => void;
  /** Callback when edit is clicked */
  onEdit?: () => void;
  /** Callback when drag starts */
  onDragStart?: (e: React.DragEvent) => void;
  /** Callback when drag ends */
  onDragEnd?: (e: React.DragEvent) => void;
}

/** Map task types to Material Symbols icon names */
const TASK_TYPE_ICONS: Record<TaskType, string> = {
  university: 'school',
  study: 'menu_book',
  revision: 'history_edu',
  practice: 'edit_note',
  assignment: 'assignment',
  lab_work: 'science',
  deep_work: 'psychology',
  break: 'coffee',
  free_time: 'self_improvement',
  sleep: 'bedtime',
  wake_routine: 'alarm',
  breakfast: 'restaurant',
  lunch: 'restaurant',
  dinner: 'restaurant',
};

/**
 * Format duration in minutes to human-readable string
 */
function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * TaskCard - Individual task card for the Flow Board
 */
export function TaskCard({
  task,
  isActive = false,
  isCompleted = false,
  onClick,
  onEdit,
  onDragStart,
  onDragEnd,
}: TaskCardProps) {
  const iconName = TASK_TYPE_ICONS[task.taskType] || 'task';
  const duration = formatDuration(task.durationMinutes);
  
  // Completed tasks have reduced opacity and grayscale
  const completedStyles = isCompleted
    ? 'opacity-60 grayscale hover:grayscale-0 hover:opacity-100'
    : '';
  
  // Base card styles
  const baseStyles = `
    kanban-card 
    bg-surface-light/60 
    border border-transparent 
    hover:border-sand-200 
    p-5 rounded-2xl 
    transition-all
    cursor-grab
    active:cursor-grabbing
  `;
  
  return (
    <div
      className={`${baseStyles} ${completedStyles}`}
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`Task: ${task.title}`}
    >
      <div className="flex justify-between items-center">
        {/* Left side: Icon and task info */}
        <div className="flex gap-3 items-center">
          {/* Task Type Icon */}
          <div className="bg-sand p-2 rounded-lg text-text-muted">
            <Icon name={iconName} size={20} />
          </div>
          
          {/* Task Details */}
          <div>
            <h3 className="text-lg font-display font-medium text-text-main">
              {task.title}
            </h3>
            <p className="text-sm text-text-muted">
              {duration} duration
              {task.subject && ` • ${task.subject.code}`}
            </p>
          </div>
        </div>
        
        {/* Right side: Drag handle */}
        <span className="text-sand-300 hover:text-text-muted transition-colors">
          <Icon name="drag_indicator" size={20} />
        </span>
      </div>
      
      {/* Status indicator for completed tasks */}
      {isCompleted && (
        <div className="mt-2 flex items-center gap-1 text-text-muted text-sm">
          <Icon name="check_circle" size={16} filled />
          <span>Completed</span>
        </div>
      )}
    </div>
  );
}

/**
 * CompactTaskCard - Smaller version for breaks and quick tasks
 */
export interface CompactTaskCardProps {
  /** Task data */
  task: Task;
  /** Callback when drag starts */
  onDragStart?: (e: React.DragEvent) => void;
  /** Callback when drag ends */
  onDragEnd?: (e: React.DragEvent) => void;
}

export function CompactTaskCard({
  task,
  onDragStart,
  onDragEnd,
}: CompactTaskCardProps) {
  const iconName = TASK_TYPE_ICONS[task.taskType] || 'task';
  const duration = formatDuration(task.durationMinutes);
  
  return (
    <div
      className="kanban-card flex items-center bg-sand/50 border border-transparent px-4 py-2 rounded-2xl transition-all hover:bg-sand/80 cursor-grab active:cursor-grabbing"
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <div className="flex items-center gap-3">
        <Icon name={iconName} size={18} className="text-text-muted" />
        <span className="text-sm text-text-main font-medium">
          {task.title} ({duration})
        </span>
      </div>
      <span className="text-sand-300 ml-auto">
        <Icon name="drag_indicator" size={18} />
      </span>
    </div>
  );
}
