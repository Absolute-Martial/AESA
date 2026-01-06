'use client';

import { useState, useCallback, useRef } from 'react';
import type { ColumnType } from '../types';

export interface DragState {
  /** ID of the task being dragged */
  draggedTaskId: string | null;
  /** Source column of the dragged task */
  sourceColumn: ColumnType | null;
  /** Target column being hovered over */
  targetColumn: ColumnType | null;
  /** Whether a drag operation is in progress */
  isDragging: boolean;
}

export interface UseDragAndDropOptions {
  /** Callback when a task is dropped in a new column */
  onTaskMove: (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => Promise<void>;
  /** Callback for optimistic update (before API call) */
  onOptimisticUpdate?: (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => void;
  /** Callback to revert optimistic update on error */
  onRevertUpdate?: (taskId: string, sourceColumn: ColumnType, targetColumn: ColumnType) => void;
}

export interface UseDragAndDropReturn {
  /** Current drag state */
  dragState: DragState;
  /** Handler for drag start event */
  handleDragStart: (taskId: string, sourceColumn: ColumnType) => (e: React.DragEvent) => void;
  /** Handler for drag end event */
  handleDragEnd: () => void;
  /** Handler for drag over event (on columns) */
  handleDragOver: (column: ColumnType) => (e: React.DragEvent) => void;
  /** Handler for drag leave event (on columns) */
  handleDragLeave: () => void;
  /** Handler for drop event (on columns) */
  handleDrop: (targetColumn: ColumnType) => (e: React.DragEvent) => void;
  /** Check if a column is the current drop target */
  isDropTarget: (column: ColumnType) => boolean;
}

/**
 * Custom hook for drag-and-drop functionality between columns
 */
export function useDragAndDrop({
  onTaskMove,
  onOptimisticUpdate,
  onRevertUpdate,
}: UseDragAndDropOptions): UseDragAndDropReturn {
  const [dragState, setDragState] = useState<DragState>({
    draggedTaskId: null,
    sourceColumn: null,
    targetColumn: null,
    isDragging: false,
  });
  
  // Track if we're currently processing a drop to prevent double-drops
  const isProcessingRef = useRef(false);

  /**
   * Handle drag start - store the task ID and source column
   */
  const handleDragStart = useCallback(
    (taskId: string, sourceColumn: ColumnType) => (e: React.DragEvent) => {
      // Set drag data for native drag-and-drop
      e.dataTransfer.setData('text/plain', taskId);
      e.dataTransfer.effectAllowed = 'move';
      
      setDragState({
        draggedTaskId: taskId,
        sourceColumn,
        targetColumn: null,
        isDragging: true,
      });
    },
    []
  );

  /**
   * Handle drag end - reset drag state
   */
  const handleDragEnd = useCallback(() => {
    setDragState({
      draggedTaskId: null,
      sourceColumn: null,
      targetColumn: null,
      isDragging: false,
    });
  }, []);

  /**
   * Handle drag over - update target column for visual feedback
   */
  const handleDragOver = useCallback(
    (column: ColumnType) => (e: React.DragEvent) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      
      setDragState((prev) => ({
        ...prev,
        targetColumn: column,
      }));
    },
    []
  );

  /**
   * Handle drag leave - clear target column
   */
  const handleDragLeave = useCallback(() => {
    setDragState((prev) => ({
      ...prev,
      targetColumn: null,
    }));
  }, []);

  /**
   * Handle drop - move task to new column
   */
  const handleDrop = useCallback(
    (targetColumn: ColumnType) => async (e: React.DragEvent) => {
      e.preventDefault();
      
      // Prevent double-processing
      if (isProcessingRef.current) return;
      
      const { draggedTaskId, sourceColumn } = dragState;
      
      // Validate we have all required data
      if (!draggedTaskId || !sourceColumn) {
        handleDragEnd();
        return;
      }
      
      // Don't do anything if dropped in the same column
      if (sourceColumn === targetColumn) {
        handleDragEnd();
        return;
      }
      
      isProcessingRef.current = true;
      
      try {
        // Apply optimistic update immediately
        onOptimisticUpdate?.(draggedTaskId, sourceColumn, targetColumn);
        
        // Call the API to persist the change
        await onTaskMove(draggedTaskId, sourceColumn, targetColumn);
      } catch (error) {
        // Revert optimistic update on error
        onRevertUpdate?.(draggedTaskId, targetColumn, sourceColumn);
        console.error('Failed to move task:', error);
      } finally {
        isProcessingRef.current = false;
        handleDragEnd();
      }
    },
    [dragState, onTaskMove, onOptimisticUpdate, onRevertUpdate, handleDragEnd]
  );

  /**
   * Check if a column is the current drop target
   */
  const isDropTarget = useCallback(
    (column: ColumnType) => {
      return dragState.isDragging && dragState.targetColumn === column;
    },
    [dragState.isDragging, dragState.targetColumn]
  );

  return {
    dragState,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    isDropTarget,
  };
}
