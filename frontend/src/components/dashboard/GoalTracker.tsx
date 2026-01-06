'use client';

import React, { useState } from 'react';
import { Icon, Button, Card, Input } from '@/components/common';
import type { Goal } from '@/lib/types';

export interface GoalTrackerProps {
  /** List of goals */
  goals: Goal[];
  /** Callback when goal is created */
  onCreateGoal?: (goal: Omit<Goal, 'id' | 'currentValue' | 'status'>) => void;
  /** Callback when goal progress is updated */
  onUpdateProgress?: (goalId: string, progress: number) => void;
  /** Callback when goal is deleted */
  onDeleteGoal?: (goalId: string) => void;
  /** API endpoint for goals */
  apiEndpoint?: string;
  /** Show create button */
  showCreateButton?: boolean;
}

/**
 * Calculate progress percentage
 */
function calculateProgress(goal: Goal): number {
  if (!goal.targetValue || goal.targetValue === 0) return 0;
  return Math.min(100, (goal.currentValue / goal.targetValue) * 100);
}

/**
 * Format deadline to relative string
 */
function formatDeadline(deadline?: Date): string {
  if (!deadline) return '';
  
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diffDays = Math.ceil((deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return 'Overdue';
  if (diffDays === 0) return 'Due today';
  if (diffDays === 1) return 'Due tomorrow';
  if (diffDays < 7) return `${diffDays} days left`;
  if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks left`;
  return `${Math.ceil(diffDays / 30)} months left`;
}

/**
 * GoalTracker - Component for tracking study goals with progress bars
 * Requirements: 16.1
 */
export function GoalTracker({
  goals,
  onCreateGoal,
  onUpdateProgress,
  onDeleteGoal,
  apiEndpoint = '/api/goals',
  showCreateButton = true,
}: GoalTrackerProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGoalId, setEditingGoalId] = useState<string | null>(null);

  const activeGoals = goals.filter((g) => g.status === 'active');
  const completedGoals = goals.filter((g) => g.status === 'completed');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-display font-semibold text-text-main flex items-center gap-2">
          <Icon name="flag" size={20} className="text-primary" />
          Study Goals
        </h3>
        {showCreateButton && (
          <Button
            variant="ghost"
            size="sm"
            icon="add"
            onClick={() => setIsModalOpen(true)}
          >
            Add Goal
          </Button>
        )}
      </div>

      {/* Active Goals */}
      {activeGoals.length > 0 ? (
        <div className="space-y-3">
          {activeGoals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onUpdateProgress={onUpdateProgress}
              onDelete={onDeleteGoal}
              isEditing={editingGoalId === goal.id}
              onEditToggle={() => setEditingGoalId(
                editingGoalId === goal.id ? null : goal.id
              )}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-text-muted">
          <Icon name="flag" size={32} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">No active goals</p>
          <p className="text-xs mt-1">Create a goal to track your progress</p>
        </div>
      )}

      {/* Completed Goals Summary */}
      {completedGoals.length > 0 && (
        <div className="pt-4 border-t border-sand-200">
          <p className="text-sm text-text-muted flex items-center gap-2">
            <Icon name="check_circle" size={16} className="text-primary" />
            {completedGoals.length} goal{completedGoals.length > 1 ? 's' : ''} completed
          </p>
        </div>
      )}

      {/* Create Goal Modal */}
      {isModalOpen && (
        <GoalCreationModal
          onClose={() => setIsModalOpen(false)}
          onCreate={(goal) => {
            onCreateGoal?.(goal);
            setIsModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

/**
 * Individual Goal Card
 */
interface GoalCardProps {
  goal: Goal;
  onUpdateProgress?: (goalId: string, progress: number) => void;
  onDelete?: (goalId: string) => void;
  isEditing: boolean;
  onEditToggle: () => void;
}

function GoalCard({
  goal,
  onUpdateProgress,
  onDelete,
  isEditing,
  onEditToggle,
}: GoalCardProps) {
  const progress = calculateProgress(goal);
  const deadlineText = formatDeadline(goal.deadline);
  const isOverdue = deadlineText === 'Overdue';

  return (
    <Card variant="default" padding="md" className="group">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h4 className="font-medium text-text-main text-sm">{goal.title}</h4>
          {goal.description && (
            <p className="text-xs text-text-muted mt-0.5 line-clamp-1">
              {goal.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onEditToggle}
            className="p-1 hover:bg-sand-100 rounded text-text-muted hover:text-text-main transition-colors"
          >
            <Icon name="edit" size={14} />
          </button>
          <button
            onClick={() => onDelete?.(goal.id)}
            className="p-1 hover:bg-red-50 rounded text-text-muted hover:text-red-500 transition-colors"
          >
            <Icon name="delete" size={14} />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-2">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-text-muted">
            {goal.currentValue} / {goal.targetValue} {goal.unit}
          </span>
          <span className={`font-medium ${progress >= 100 ? 'text-primary' : 'text-text-main'}`}>
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-2 bg-sand-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              progress >= 100 ? 'bg-primary' : 'bg-primary/70'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Deadline */}
      {deadlineText && (
        <p className={`text-xs ${isOverdue ? 'text-red-500' : 'text-text-muted'}`}>
          {deadlineText}
        </p>
      )}

      {/* Quick Update (when editing) */}
      {isEditing && (
        <div className="mt-3 pt-3 border-t border-sand-200">
          <QuickProgressUpdate
            currentValue={goal.currentValue}
            targetValue={goal.targetValue || 100}
            unit={goal.unit}
            onUpdate={(value) => onUpdateProgress?.(goal.id, value)}
          />
        </div>
      )}
    </Card>
  );
}

/**
 * Quick Progress Update Component
 */
interface QuickProgressUpdateProps {
  currentValue: number;
  targetValue: number;
  unit?: string;
  onUpdate: (value: number) => void;
}

function QuickProgressUpdate({
  currentValue,
  targetValue,
  unit,
  onUpdate,
}: QuickProgressUpdateProps) {
  const [value, setValue] = useState(currentValue.toString());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      onUpdate(numValue);
    }
  };

  const quickIncrements = [1, 5, 10];

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="flex gap-2">
        <input
          type="number"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="flex-1 px-3 py-1.5 text-sm bg-sand-100 border border-sand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20"
          min={0}
          max={targetValue}
        />
        <Button type="submit" variant="primary" size="sm">
          Update
        </Button>
      </div>
      <div className="flex gap-1">
        {quickIncrements.map((inc) => (
          <button
            key={inc}
            type="button"
            onClick={() => {
              const newValue = Math.min(currentValue + inc, targetValue);
              setValue(newValue.toString());
              onUpdate(newValue);
            }}
            className="px-2 py-1 text-xs bg-sand-100 hover:bg-sand-200 rounded transition-colors"
          >
            +{inc} {unit}
          </button>
        ))}
      </div>
    </form>
  );
}

/**
 * Goal Creation Modal
 */
interface GoalCreationModalProps {
  onClose: () => void;
  onCreate: (goal: Omit<Goal, 'id' | 'currentValue' | 'status'>) => void;
}

function GoalCreationModal({ onClose, onCreate }: GoalCreationModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [targetValue, setTargetValue] = useState('');
  const [unit, setUnit] = useState('hours');
  const [deadline, setDeadline] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    onCreate({
      title: title.trim(),
      description: description.trim() || undefined,
      targetValue: targetValue ? parseFloat(targetValue) : undefined,
      unit: unit || undefined,
      deadline: deadline ? new Date(deadline) : undefined,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-light rounded-2xl shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-sand-200">
          <h3 className="font-display font-semibold text-lg text-text-main">
            Create New Goal
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-sand-100 rounded-lg transition-colors"
          >
            <Icon name="close" size={20} className="text-text-muted" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <Input
            label="Goal Title"
            placeholder="e.g., Complete 20 hours of study"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            fullWidth
          />

          <Input
            label="Description (optional)"
            placeholder="Add more details..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Target Value"
              type="number"
              placeholder="20"
              value={targetValue}
              onChange={(e) => setTargetValue(e.target.value)}
              min={1}
            />
            <div>
              <label className="block text-sm font-medium text-text-main mb-1.5">
                Unit
              </label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full px-4 py-3 bg-surface-light border border-sand-200 rounded-xl text-sm text-text-main focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="hours">hours</option>
                <option value="chapters">chapters</option>
                <option value="problems">problems</option>
                <option value="pages">pages</option>
                <option value="sessions">sessions</option>
              </select>
            </div>
          </div>

          <Input
            label="Deadline (optional)"
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            fullWidth
          />

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              disabled={!title.trim()}
            >
              Create Goal
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * GoalTrackerCompact - Compact version showing summary only
 */
export interface GoalTrackerCompactProps {
  goals: Goal[];
  onClick?: () => void;
}

export function GoalTrackerCompact({ goals, onClick }: GoalTrackerCompactProps) {
  const activeGoals = goals.filter((g) => g.status === 'active');
  const totalProgress = activeGoals.length > 0
    ? activeGoals.reduce((sum, g) => sum + calculateProgress(g), 0) / activeGoals.length
    : 0;

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 px-3 py-2 bg-sand-100 hover:bg-sand-200 rounded-lg transition-colors"
    >
      <Icon name="flag" size={18} className="text-primary" />
      <div className="text-left">
        <p className="text-xs text-text-muted">{activeGoals.length} active goals</p>
        <p className="text-sm font-medium text-text-main">
          {Math.round(totalProgress)}% avg progress
        </p>
      </div>
    </button>
  );
}
