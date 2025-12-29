'use client';

import React, { useState, useCallback } from 'react';
import { DraggableColumn } from './DraggableColumn';
import { FlowBoardHeader } from './FlowBoardHeader';
import { TaskCard, CompactTaskCard } from './TaskCard';
import { ActiveTaskCard } from './ActiveTaskCard';
import { COLUMN_CONFIG } from './Column';
import { useDragAndDrop } from '@/lib/hooks';
import type { Task, DayStats, ColumnType } from '@/lib/types';

export interface DraggableFlowBoardProps {
  /** Current date */
  date: Date;
  /** Daily statistics */
  stats?: DayStats;
  /** Initial tasks organized by column */
  initialTasksByColumn: Record<ColumnType, Task[]>;
  /** Active task ID (currently in progress) */
  activeTaskId?: string;
  /** Active task progress (0-100) */
  activeTaskProgress?: number;
  /** Active task remaining minutes */
  activeTaskRemainingMinutes?: number;
  /** Active task time range string */
  activeTaskTimeRange?: string;
  /** Whether the active task timer is running */
  isTimerRunning?: boolean;
  /** Callback when a task is moved between columns (API call) */
  onTaskMove: (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => Promise<void>;
  /** Callback when add task is clicked for a column */
  onAddTask?: (column: ColumnType) => void;
  /** Callback when continue is clicked on active task */
  onContinue?: () => void;
  /** Callback when pause is clicked on active task */
  onPause?: () => void;
  /** Callback when edit is clicked on a task */
  onEditTask?: (taskId: string) => void;
}

const COLUMN_ORDER: ColumnType[] = ['morning', 'afternoon', 'evening', 'backlog'];

/**
 * DraggableFlowBoard - Flow Board with full drag-and-drop support
 */
export function DraggableFlowBoard({
  date,
  stats,
  initialTasksByColumn,
  activeTaskId,
  activeTaskProgress = 0,
  activeTaskRemainingMinutes = 0,
  activeTaskTimeRange,
  isTimerRunning = false,
  onTaskMove,
  onAddTask,
  onContinue,
  onPause,
  onEditTask,
}: DraggableFlowBoardProps) {
  // Local state for optimistic updates
  const [tasksByColumn, setTasksByColumn] = useState(initialTasksByColumn);

  // Optimistic update handler
  const handleOptimisticUpdate = useCallback(
    (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => {
      setTasksByColumn((prev) => {
        const sourceTasks = [...(prev[sourceColumn] || [])];
        const targetTasks = [...(prev[targetColumn] || [])];
        
        // Find and remove task from source
        const taskIndex = sourceTasks.findIndex((t) => t.id === taskId);
        if (taskIndex === -1) return prev;
        
        const [task] = sourceTasks.splice(taskIndex, 1);
        
        // Add task to target
        targetTasks.push(task);
        
        return {
          ...prev,
          [sourceColumn]: sourceTasks,
          [targetColumn]: targetTasks,
        };
      });
    },
    []
  );

  // Revert optimistic update on error
  const handleRevertUpdate = useCallback(
    (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => {
      // Revert by moving back (source and target are swapped)
      handleOptimisticUpdate(taskId, sourceColumn, targetColumn);
    },
    [handleOptimisticUpdate]
  );

  // Initialize drag-and-drop hook
  const {
    dragState,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    isDropTarget,
  } = useDragAndDrop({
    onTaskMove,
    onOptimisticUpdate: handleOptimisticUpdate,
    onRevertUpdate: handleRevertUpdate,
  });

  // Render a task card based on its state
  const renderTaskCard = (task: Task, columnId: ColumnType) => {
    const isActive = task.id === activeTaskId;
    const isCompleted = task.isCompleted;
    const isCompact = task.taskType === 'break' || task.durationMinutes <= 15;

    if (isActive) {
      return (
        <ActiveTaskCard
          key={task.id}
          task={task}
          progress={activeTaskProgress}
          remainingMinutes={activeTaskRemainingMinutes}
          timeRange={activeTaskTimeRange}
          isRunning={isTimerRunning}
          onContinue={onContinue || (() => {})}
          onPause={onPause || (() => {})}
          onEdit={() => onEditTask?.(task.id)}
        />
      );
    }

    if (isCompact) {
      return (
        <CompactTaskCard
          key={task.id}
          task={task}
          onDragStart={handleDragStart(task.id, columnId)}
          onDragEnd={handleDragEnd}
        />
      );
    }

    return (
      <TaskCard
        key={task.id}
        task={task}
        isCompleted={isCompleted}
        onDragStart={handleDragStart(task.id, columnId)}
        onDragEnd={handleDragEnd}
        onEdit={() => onEditTask?.(task.id)}
      />
    );
  };

  return (
    <main className="flex-1 h-full flex flex-col p-6 overflow-x-auto scroll-smooth snap-x scroll-p-6">
      {/* Header with date and stats */}
      <FlowBoardHeader date={date} stats={stats} />
      
      {/* Columns Container */}
      <div className="flex-1 flex gap-6 pb-4 overflow-x-auto scroll-smooth">
        {COLUMN_ORDER.map((columnId) => {
          const config = COLUMN_CONFIG[columnId];
          const tasks = tasksByColumn[columnId] || [];
          
          return (
            <DraggableColumn
              key={columnId}
              id={columnId}
              title={config.title}
              timeRange={config.timeRange}
              tasks={tasks}
              isDropTarget={isDropTarget(columnId)}
              onAddTask={() => onAddTask?.(columnId)}
              onDragOver={handleDragOver(columnId)}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop(columnId)}
            >
              {tasks.map((task) => renderTaskCard(task, columnId))}
            </DraggableColumn>
          );
        })}
      </div>
    </main>
  );
}
