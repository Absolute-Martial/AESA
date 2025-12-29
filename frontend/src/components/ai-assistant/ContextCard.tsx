'use client';

import React from 'react';
import { Icon } from '../common/Icon';
import { Badge, Tag } from '../common/Badge';
import type { Task, TaskType } from '@/lib/types';

export interface ContextCardProps {
  /** Currently active task */
  activeTask: Task | null;
  /** Relevant tags/context for the current session */
  tags?: string[];
  /** Additional CSS classes */
  className?: string;
}

/**
 * Map task types to icon names
 */
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
 * Format duration in minutes to readable string
 */
function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/**
 * ContextCard - Displays current active task details and relevant tags
 * Shows in the AI Assistant panel to provide context awareness
 */
export function ContextCard({ activeTask, tags = [], className = '' }: ContextCardProps) {
  if (!activeTask) {
    return (
      <div className={`bg-sand-50 rounded-xl p-4 ${className}`}>
        <div className="flex items-center gap-2 mb-2">
          <Icon name="info" size={16} className="text-text-muted" />
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            Current Context
          </span>
        </div>
        <p className="text-sm text-text-muted">
          No active task. Start a task to see context here.
        </p>
      </div>
    );
  }

  const taskIcon = TASK_TYPE_ICONS[activeTask.taskType] || 'task_alt';

  return (
    <div className={`bg-sand-50 rounded-xl p-4 ${className}`}>
      {/* Section Header */}
      <div className="flex items-center gap-2 mb-3">
        <Icon name="info" size={16} className="text-text-muted" />
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          Current Context
        </span>
      </div>

      {/* Active Task Card */}
      <div className="bg-white rounded-lg p-3 border border-sand-200/50 shadow-sm">
        <div className="flex items-start gap-3">
          {/* Task Icon */}
          <div className="flex-shrink-0 w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Icon name={taskIcon} size={20} className="text-primary" />
          </div>

          {/* Task Details */}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-text-main truncate">
              {activeTask.title}
            </h4>
            
            <div className="flex items-center gap-2 mt-1">
              {/* Subject Badge */}
              {activeTask.subject && (
                <Badge variant="primary" size="sm">
                  {activeTask.subject.code}
                </Badge>
              )}
              
              {/* Duration */}
              <span className="text-xs text-text-muted flex items-center gap-1">
                <Icon name="schedule" size={12} />
                {formatDuration(activeTask.durationMinutes)}
              </span>
            </div>

            {/* Description if available */}
            {activeTask.description && (
              <p className="text-xs text-text-muted mt-2 line-clamp-2">
                {activeTask.description}
              </p>
            )}
          </div>

          {/* Status Indicator */}
          <div className="flex-shrink-0">
            {activeTask.status === 'in_progress' && (
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            )}
          </div>
        </div>
      </div>

      {/* Tags Section */}
      {tags.length > 0 && (
        <div className="mt-3">
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag, index) => (
              <Tag key={index}>{tag}</Tag>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * ContextCardSkeleton - Loading state for ContextCard
 */
export function ContextCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-sand-50 rounded-xl p-4 ${className}`}>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-4 h-4 bg-sand-200 rounded animate-pulse" />
        <div className="w-24 h-3 bg-sand-200 rounded animate-pulse" />
      </div>
      
      <div className="bg-white rounded-lg p-3 border border-sand-200/50">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-sand-200 rounded-lg animate-pulse" />
          <div className="flex-1">
            <div className="w-32 h-4 bg-sand-200 rounded animate-pulse mb-2" />
            <div className="w-20 h-3 bg-sand-200 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
