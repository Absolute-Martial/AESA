'use client';

import React, { useState } from 'react';
import { 
  TodayDashboard, 
  DashboardHeader, 
  DashboardLayout 
} from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import type { Task, DayStats, ColumnType } from '@/lib/types';

// Mock data for demonstration
const mockStats: DayStats = {
  focusTimeMinutes: 185,
  deepWorkMinutes: 90,
  tasksCompleted: 4,
  energyLevel: 72,
};

const mockTasks: Record<ColumnType, Task[]> = {
  morning: [
    {
      id: '1',
      title: 'Study Neural Networks',
      taskType: 'deep_work',
      durationMinutes: 90,
      priority: 85,
      isCompleted: false,
      status: 'in_progress',
      subject: { id: 's1', code: 'COMP401', name: 'Machine Learning', color: '#6366f1' },
    },
    {
      id: '2',
      title: 'Review Linear Algebra',
      taskType: 'revision',
      durationMinutes: 45,
      priority: 65,
      isCompleted: true,
      status: 'completed',
      subject: { id: 's2', code: 'MATH201', name: 'Linear Algebra', color: '#f59e0b' },
    },
  ],
  afternoon: [
    {
      id: '3',
      title: 'Practice Problems - Calculus',
      taskType: 'practice',
      durationMinutes: 60,
      priority: 50,
      isCompleted: false,
      status: 'pending',
      subject: { id: 's3', code: 'MATH101', name: 'Calculus', color: '#10b981' },
    },
    {
      id: '4',
      title: 'Lab Report - Physics',
      taskType: 'assignment',
      durationMinutes: 120,
      priority: 75,
      deadline: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      isCompleted: false,
      status: 'pending',
      subject: { id: 's4', code: 'PHYS102', name: 'Physics', color: '#ef4444' },
    },
  ],
  evening: [
    {
      id: '5',
      title: 'Read Chapter 5 - Data Structures',
      taskType: 'study',
      durationMinutes: 45,
      priority: 50,
      isCompleted: false,
      status: 'pending',
      subject: { id: 's5', code: 'COMP201', name: 'Data Structures', color: '#8b5cf6' },
    },
  ],
  backlog: [
    {
      id: '6',
      title: 'Prepare for Quiz',
      taskType: 'revision',
      durationMinutes: 30,
      priority: 40,
      isCompleted: false,
      status: 'pending',
    },
    {
      id: '7',
      title: 'Watch Lecture Recording',
      taskType: 'study',
      durationMinutes: 60,
      priority: 30,
      isCompleted: false,
      status: 'pending',
    },
  ],
};

const navItems = [
  { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: true },
  { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
  { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
  { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
];

/**
 * Dashboard Page - Main entry point for the Today view
 * Requirements: 13.1
 */
export default function DashboardPage() {
  const [tasksByColumn, setTasksByColumn] = useState(mockTasks);
  const [activeTaskId, setActiveTaskId] = useState<string | undefined>('1');

  const handleTaskMove = (taskId: string, targetColumn: ColumnType) => {
    // Find and move task between columns
    const newTasksByColumn = { ...tasksByColumn };
    let movedTask: Task | undefined;

    // Remove from current column
    for (const column of Object.keys(newTasksByColumn) as ColumnType[]) {
      const index = newTasksByColumn[column].findIndex((t) => t.id === taskId);
      if (index !== -1) {
        [movedTask] = newTasksByColumn[column].splice(index, 1);
        break;
      }
    }

    // Add to target column
    if (movedTask) {
      newTasksByColumn[targetColumn] = [...newTasksByColumn[targetColumn], movedTask];
      setTasksByColumn(newTasksByColumn);
    }
  };

  const handleAddTask = (column: ColumnType) => {
    console.log('Add task to column:', column);
    // Would open a modal or navigate to task creation
  };

  const handleTaskClick = (task: Task) => {
    console.log('Task clicked:', task);
    // Would open task details or start task
  };

  const handleContinueTask = (task: Task) => {
    console.log('Continue task:', task);
    setActiveTaskId(task.id);
  };

  const handlePauseTask = (task: Task) => {
    console.log('Pause task:', task);
    setActiveTaskId(undefined);
  };

  const handleEditTask = (task: Task) => {
    console.log('Edit task:', task);
    // Would open edit modal
  };

  const handleNavClick = (id: string) => {
    console.log('Navigate to:', id);
    // Would use router.push
  };

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={navItems}
          onNavClick={handleNavClick}
          actions={
            <>
              <Button variant="ghost" icon="notifications" size="sm" />
              <Button variant="ghost" icon="settings" size="sm" />
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Icon name="person" size={18} className="text-primary" />
              </div>
            </>
          }
        />
      }
    >
      <TodayDashboard
        tasksByColumn={tasksByColumn}
        stats={mockStats}
        activeTaskId={activeTaskId}
        contextTags={['COMP401', 'Deep Work', 'Morning Session']}
        onTaskMove={handleTaskMove}
        onAddTask={handleAddTask}
        onTaskClick={handleTaskClick}
        onContinueTask={handleContinueTask}
        onPauseTask={handlePauseTask}
        onEditTask={handleEditTask}
      />
    </DashboardLayout>
  );
}
