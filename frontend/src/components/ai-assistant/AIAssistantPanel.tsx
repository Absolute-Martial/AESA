'use client';

import React, { useState } from 'react';
import { Icon } from '../common/Icon';
import { Button } from '../common/Button';

export interface AIAssistantPanelProps {
  /** Whether the panel starts collapsed */
  defaultCollapsed?: boolean;
  /** Callback when panel is toggled */
  onToggle?: (isCollapsed: boolean) => void;
  /** Children content to render inside the panel */
  children?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * AIAssistantPanel - Collapsible panel for AI assistant interface
 * Features glass-panel effect and smooth expand/collapse animation
 */
export function AIAssistantPanel({
  defaultCollapsed = false,
  onToggle,
  children,
  className = '',
}: AIAssistantPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const handleToggle = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onToggle?.(newState);
  };

  return (
    <div
      className={`
        relative flex flex-col
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-14' : 'w-[380px]'}
        ${className}
      `.trim()}
    >
      {/* Toggle Button - Always visible */}
      <button
        onClick={handleToggle}
        className={`
          absolute top-4 z-10
          flex items-center justify-center
          w-10 h-10
          bg-primary text-white
          rounded-full
          shadow-lg shadow-primary/30
          hover:bg-primary-600
          transition-all duration-300
          ${isCollapsed ? 'left-2' : '-left-5'}
        `}
        aria-label={isCollapsed ? 'Expand AI Assistant' : 'Collapse AI Assistant'}
        aria-expanded={!isCollapsed}
      >
        <Icon 
          name={isCollapsed ? 'smart_toy' : 'chevron_right'} 
          size={20} 
        />
      </button>

      {/* Panel Container */}
      <div
        className={`
          h-full
          bg-white/80 dark:bg-gray-900/80
          backdrop-blur-[12px]
          shadow-glass
          border border-sand-200/50
          rounded-2xl
          overflow-hidden
          transition-all duration-300
          ${isCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}
        `}
      >
        {/* Panel Header */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-sand-200/50">
          <div className="flex items-center justify-center w-8 h-8 bg-primary/10 rounded-lg">
            <Icon name="smart_toy" size={18} className="text-primary" />
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-semibold text-text-main">AESA Assistant</h2>
            <p className="text-xs text-text-muted">Your study companion</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon="more_horiz"
            aria-label="More options"
          />
        </div>

        {/* Panel Content */}
        <div className="flex-1 flex flex-col h-[calc(100%-64px)] overflow-hidden">
          {children}
        </div>
      </div>

      {/* Collapsed State Indicator */}
      {isCollapsed && (
        <div className="flex flex-col items-center pt-16 gap-4">
          <div className="w-1 h-8 bg-primary/20 rounded-full" />
          <span className="text-xs text-text-muted writing-mode-vertical transform rotate-180" style={{ writingMode: 'vertical-rl' }}>
            AI Assistant
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * AIAssistantPanelSection - Section wrapper for panel content
 */
export interface AIAssistantPanelSectionProps {
  /** Section title */
  title?: string;
  /** Children content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export function AIAssistantPanelSection({
  title,
  children,
  className = '',
}: AIAssistantPanelSectionProps) {
  return (
    <div className={`px-4 py-3 ${className}`}>
      {title && (
        <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
