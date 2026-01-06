'use client';

import React, { useState } from 'react';
import { FlowBoard } from '@/components/flow-board';
import { AIAssistant } from '@/components/ai-assistant';
import { TaskCard, ActiveTaskCard } from '@/components/flow-board';
import { Icon, ThemeToggle, NotificationCenter } from '@/components/common';
import type { Task, DayStats, ColumnType } from '@/lib/types';

export interface TodayDashboardProps {
  /** Tasks organized by column */
  tasksByColumn: Record<ColumnType, Task[]>;
  /** Daily statistics */
  stats?: DayStats;
  /** Active task ID */
  activeTaskId?: string;
  /** Context tags for AI assistant */
  contextTags?: string[];
  /** Callback when task is moved */
  onTaskMove?: (taskId: string, targetColumn: ColumnType) => void;
  /** Callback when add task is clicked */
  onAddTask?: (column: ColumnType) => void;
  /** Callback when task is clicked */
  onTaskClick?: (task: Task) => void;
  /** Callback when continue is clicked on active task */
  onContinueTask?: (task: Task) => void;
  /** Callback when pause is clicked on active task */
  onPauseTask?: (task: Task) => void;
  /** Callback when edit is clicked on active task */
  onEditTask?: (task: Task) => void;
}

/**
 * TodayDashboard - Main dashboard combining Flow Board and AI Assistant
 * Requirements: 13.1
 */
export function TodayDashboard({
  tasksByColumn,
  stats,
  activeTaskId,
  contextTags = [],
  onTaskMove,
  onAddTask,
  onTaskClick,
  onContinueTask,
  onPauseTask,
  onEditTask,
}: TodayDashboardProps) {
  const [isAiPanelCollapsed, setIsAiPanelCollapsed] = useState(false);
  
  // Find active task from all columns
  const activeTask = activeTaskId
    ? Object.values(tasksByColumn)
        .flat()
        .find((task) => task.id === activeTaskId)
    : undefined;

  // Calculate progress for active task (mock - would come from timer)
  const activeTaskProgress = 45; // percentage
  const activeTaskRemainingMinutes = 23;

  const renderTaskCard = (task: Task, isActive: boolean) => {
    if (isActive && activeTask) {
      return (
        <ActiveTaskCard
          task={activeTask}
          progress={activeTaskProgress}
          remainingMinutes={activeTaskRemainingMinutes}
          onContinue={() => onContinueTask?.(activeTask)}
          onPause={() => onPauseTask?.(activeTask)}
          onEdit={() => onEditTask?.(activeTask)}
        />
      );
    }

    return (
      <TaskCard
        task={task}
        onClick={() => onTaskClick?.(task)}
      />
    );
  };

  return (
    <div className="flex min-h-screen bg-sand-100 dark:bg-gray-900 transition-colors overflow-x-hidden">
      <div className="flex-1">
        <FlowBoard
          date={new Date()}
          stats={stats}
          tasksByColumn={tasksByColumn}
          activeTaskId={activeTaskId}
          onTaskMove={onTaskMove}
          onAddTask={onAddTask}
          renderTaskCard={renderTaskCard}
        />

        <div className="border-t border-sand-200 dark:border-gray-700">
          <AIAssistant
            activeTask={activeTask}
            contextTags={contextTags}
            defaultCollapsed={isAiPanelCollapsed}
            onToggle={setIsAiPanelCollapsed}
            className="h-[520px]"
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Navigation Header for the dashboard
 */
export interface DashboardHeaderProps {
  /** Current page title */
  title?: string;
  /** User name for greeting */
  userName?: string;
  /** Navigation items */
  navItems?: Array<{
    id: string;
    label: string;
    icon: string;
    href: string;
    isActive?: boolean;
  }>;
  /** Callback when nav item is clicked */
  onNavClick?: (id: string) => void;
  /** Right side actions */
  actions?: React.ReactNode;
}

export function DashboardHeader({
  title = "Today's Flow",
  userName,
  navItems = [],
  onNavClick,
  actions,
}: DashboardHeaderProps) {
  const greeting = getGreeting();

  return (
    <header className="h-16 bg-surface-light dark:bg-gray-800 border-b border-sand-200 dark:border-gray-700 px-6 flex items-center justify-between transition-colors">
      {/* Left - Logo and Nav */}
      <div className="flex items-center gap-8">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Icon name="auto_awesome" size={18} className="text-white" />
          </div>
          <span className="font-display font-bold text-lg text-text-main dark:text-gray-100">AESA</span>
        </div>

        {/* Navigation */}
        {navItems.length > 0 && (
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onNavClick?.(item.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                  transition-colors
                  ${item.isActive 
                    ? 'bg-primary/10 text-primary' 
                    : 'text-text-muted dark:text-gray-400 hover:bg-sand-100 dark:hover:bg-gray-700 hover:text-text-main dark:hover:text-gray-200'
                  }
                `}
              >
                <Icon name={item.icon} size={18} />
                {item.label}
              </button>
            ))}
          </nav>
        )}
      </div>

      {/* Center - Title/Greeting */}
      <div className="absolute left-1/2 -translate-x-1/2">
        {userName && (
          <p className="text-sm text-text-muted dark:text-gray-400">
            {greeting}, <span className="font-medium text-text-main dark:text-gray-100">{userName}</span>
          </p>
        )}
      </div>

      {/* Right - Actions */}
      <div className="flex items-center gap-3">
        <NotificationCenter />
        <ThemeToggle />
        {actions}
      </div>
    </header>
  );
}

/**
 * Get time-based greeting
 */
function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Full page layout with header and dashboard
 */
export interface DashboardLayoutProps {
  children: React.ReactNode;
  header?: React.ReactNode;
}

export function DashboardLayout({ children, header }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-sand-100 dark:bg-gray-900 flex flex-col transition-colors">
      {header}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
