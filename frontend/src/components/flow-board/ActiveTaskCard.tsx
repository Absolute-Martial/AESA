'use client';

import React from 'react';
import { Icon, Button, Badge } from '../common';
import type { Task, TaskType } from '@/lib/types';

export interface ActiveTaskCardProps {
  /** Task data */
  task: Task;
  /** Progress percentage (0-100) */
  progress: number;
  /** Remaining time in minutes */
  remainingMinutes: number;
  /** Current time range string (e.g., "11:15 AM - 01:00 PM") */
  timeRange?: string;
  /** Callback when continue/play is clicked */
  onContinue: () => void;
  /** Callback when pause is clicked */
  onPause: () => void;
  /** Callback when edit is clicked */
  onEdit: () => void;
  /** Whether the timer is currently running */
  isRunning?: boolean;
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
 * Format minutes to human-readable string
 */
function formatRemainingTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m remaining`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) return `${hours}h remaining`;
  return `${hours}h ${mins}m remaining`;
}

/**
 * ActiveTaskCard - Expanded card for the currently active task with timer controls
 */
export function ActiveTaskCard({
  task,
  progress,
  remainingMinutes,
  timeRange,
  onContinue,
  onPause,
  onEdit,
  isRunning = true,
}: ActiveTaskCardProps) {
  const iconName = TASK_TYPE_ICONS[task.taskType] || 'task';
  
  return (
    <div className="kanban-card relative bg-surface-light border border-primary/20 p-5 rounded-2xl shadow-soft">
      {/* Glow effect behind the card */}
      <div className="absolute inset-0 bg-primary/5 rounded-3xl blur-xl -z-10 translate-y-2" />
      
      {/* Header: Icon, Title, Time, Status Badge */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex gap-4">
          {/* Task Type Icon */}
          <div className="bg-primary/10 p-3 rounded-xl text-primary">
            <Icon name={iconName} size={24} filled />
          </div>
          
          {/* Task Details */}
          <div>
            <h3 className="text-xl font-display font-bold text-text-main">
              {task.title}
            </h3>
            {timeRange && (
              <p className="text-primary font-medium text-sm mt-1">
                {timeRange}
              </p>
            )}
          </div>
        </div>
        
        {/* Status Badge */}
        <Badge variant="primary">
          In Progress
        </Badge>
      </div>
      
      {/* Progress Section */}
      <div className="flex flex-col gap-2 mb-6 bg-sand/30 p-4 rounded-xl">
        <div className="flex gap-6 justify-between items-end">
          <p className="text-text-main text-sm font-medium leading-normal">
            Session Progress
          </p>
          <div className="text-right">
            <p className="text-text-main text-sm font-bold leading-normal">
              {Math.round(progress)}%
            </p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="rounded-full bg-sand-200 h-2 w-full overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
        
        {/* Remaining Time */}
        <p className="text-primary text-xs font-medium leading-normal mt-1">
          {formatRemainingTime(remainingMinutes)}
        </p>
      </div>
      
      {/* Action Buttons */}
      <div className="flex gap-3">
        {/* Continue/Play Button */}
        <Button
          variant="primary"
          size="lg"
          icon={isRunning ? 'play_circle' : 'play_circle'}
          onClick={onContinue}
          className="flex-1 shadow-lg shadow-primary/20"
        >
          {isRunning ? 'Continue Focus' : 'Start Focus'}
        </Button>
        
        {/* Pause Button */}
        <Button
          variant="icon"
          size="lg"
          onClick={onPause}
          aria-label="Pause"
        >
          <Icon name="pause" size={20} />
        </Button>
        
        {/* Edit Button */}
        <Button
          variant="icon"
          size="lg"
          onClick={onEdit}
          aria-label="Edit task"
        >
          <Icon name="edit" size={20} />
        </Button>
      </div>
    </div>
  );
}
