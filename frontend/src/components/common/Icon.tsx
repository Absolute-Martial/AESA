'use client';

import React from 'react';

export interface IconProps {
  /** Material Symbols icon name */
  name: string;
  /** Size in pixels */
  size?: number;
  /** Whether to use filled variant */
  filled?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Click handler */
  onClick?: () => void;
}

/**
 * Icon component using Material Symbols Outlined
 * @see https://fonts.google.com/icons
 */
export function Icon({
  name,
  size = 24,
  filled = false,
  className = '',
  onClick,
}: IconProps) {
  const baseClasses = 'material-symbols-outlined select-none';
  const fillClass = filled ? 'fill' : '';
  
  return (
    <span
      className={`${baseClasses} ${fillClass} ${className}`}
      style={{ fontSize: size }}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {name}
    </span>
  );
}

/** Common icon names used throughout the app */
export const IconNames = {
  // Navigation
  flowBoard: 'view_kanban',
  calendar: 'calendar_today',
  analytics: 'bar_chart',
  knowledge: 'menu_book',
  settings: 'settings',
  
  // Actions
  add: 'add',
  addCircle: 'add_circle',
  edit: 'edit',
  delete: 'delete',
  more: 'more_horiz',
  send: 'send',
  play: 'play_circle',
  pause: 'pause',
  drag: 'drag_indicator',
  
  // Task types
  deepWork: 'psychology',
  study: 'menu_book',
  revision: 'history_edu',
  practice: 'edit_note',
  assignment: 'assignment',
  labWork: 'science',
  break: 'coffee',
  freeTime: 'self_improvement',
  meal: 'restaurant',
  meeting: 'group_work',
  
  // Status
  completed: 'check_circle',
  inProgress: 'pending',
  
  // AI Assistant
  ai: 'smart_toy',
  lightbulb: 'lightbulb',
  suggestion: 'psychology_alt',
  
  // Misc
  spa: 'spa',
  book: 'book',
  meditation: 'self_improvement',
  palette: 'palette',
  model: 'model_training',
  arrowBack: 'arrow_back_ios_new',
  arrowForward: 'arrow_forward_ios',
} as const;

export type IconName = keyof typeof IconNames;
