'use client';

import React from 'react';
import { Icon } from '../common/Icon';
import { Button } from '../common/Button';
import type { Suggestion } from '@/lib/types';

export interface SuggestionCardProps {
  /** Suggestion data */
  suggestion: Suggestion;
  /** Whether the action is loading */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SuggestionCard - Displays an AI suggestion with an actionable button
 * Used in the AI Assistant panel to show proactive recommendations
 */
export function SuggestionCard({
  suggestion,
  loading = false,
  className = '',
}: SuggestionCardProps) {
  const { text, actionLabel, action } = suggestion;

  return (
    <div
      className={`
        bg-gradient-to-br from-primary/5 to-primary/10
        border border-primary/20
        rounded-xl
        p-4
        ${className}
      `.trim()}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
          <Icon name="lightbulb" size={14} className="text-primary" />
        </div>
        <span className="text-xs font-semibold text-primary uppercase tracking-wider">
          AESA Suggestion
        </span>
      </div>

      {/* Suggestion Text */}
      <p className="text-sm text-text-main leading-relaxed mb-3">
        {text}
      </p>

      {/* Action Button */}
      <Button
        variant="primary"
        size="sm"
        onClick={action}
        loading={loading}
        icon="add"
        className="w-full"
      >
        {actionLabel}
      </Button>
    </div>
  );
}

/**
 * SuggestionCardList - Container for multiple suggestion cards
 */
export interface SuggestionCardListProps {
  /** Array of suggestions to display */
  suggestions: Suggestion[];
  /** Loading states for each suggestion (by index) */
  loadingStates?: Record<number, boolean>;
  /** Additional CSS classes */
  className?: string;
}

export function SuggestionCardList({
  suggestions,
  loadingStates = {},
  className = '',
}: SuggestionCardListProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {suggestions.map((suggestion, index) => (
        <SuggestionCard
          key={index}
          suggestion={suggestion}
          loading={loadingStates[index]}
        />
      ))}
    </div>
  );
}

/**
 * QuickAction - Smaller inline action button for quick suggestions
 */
export interface QuickActionProps {
  /** Action label */
  label: string;
  /** Icon name */
  icon?: string;
  /** Click handler */
  onClick: () => void;
  /** Whether the action is loading */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function QuickAction({
  label,
  icon = 'add',
  onClick,
  loading = false,
  className = '',
}: QuickActionProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`
        inline-flex items-center gap-1.5
        px-3 py-1.5
        bg-white
        border border-sand-200
        rounded-full
        text-xs font-medium text-text-main
        hover:bg-sand-50 hover:border-primary/30
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `.trim()}
    >
      {loading ? (
        <Icon name="progress_activity" size={14} className="animate-spin" />
      ) : (
        <Icon name={icon} size={14} className="text-primary" />
      )}
      {label}
    </button>
  );
}

/**
 * QuickActionGroup - Group of quick action buttons
 */
export interface QuickActionGroupProps {
  /** Array of quick actions */
  actions: Array<{
    label: string;
    icon?: string;
    onClick: () => void;
  }>;
  /** Additional CSS classes */
  className?: string;
}

export function QuickActionGroup({ actions, className = '' }: QuickActionGroupProps) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {actions.map((action, index) => (
        <QuickAction
          key={index}
          label={action.label}
          icon={action.icon}
          onClick={action.onClick}
        />
      ))}
    </div>
  );
}

/**
 * SuggestionCardSkeleton - Loading state for SuggestionCard
 */
export function SuggestionCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`
        bg-sand-50
        border border-sand-200
        rounded-xl
        p-4
        ${className}
      `}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-6 h-6 bg-sand-200 rounded-full animate-pulse" />
        <div className="w-24 h-3 bg-sand-200 rounded animate-pulse" />
      </div>
      <div className="space-y-2 mb-3">
        <div className="w-full h-3 bg-sand-200 rounded animate-pulse" />
        <div className="w-3/4 h-3 bg-sand-200 rounded animate-pulse" />
      </div>
      <div className="w-full h-8 bg-sand-200 rounded-xl animate-pulse" />
    </div>
  );
}
