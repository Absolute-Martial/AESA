'use client';

import React from 'react';

export type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps {
  /** Badge content */
  children: React.ReactNode;
  /** Badge style variant */
  variant?: BadgeVariant;
  /** Badge size */
  size?: BadgeSize;
  /** Additional CSS classes */
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-sand-200 text-text-muted',
  primary: 'bg-primary/10 text-primary',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  error: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-[10px]',
  md: 'px-3 py-1 text-xs',
};

/**
 * Badge component for status indicators and labels
 */
export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center
        rounded-full
        font-bold uppercase tracking-wide
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `.trim()}
    >
      {children}
    </span>
  );
}

/**
 * Tag component for categorization (similar to badge but with border)
 */
export interface TagProps {
  /** Tag content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export function Tag({ children, className = '' }: TagProps) {
  return (
    <span
      className={`
        inline-flex items-center
        px-2 py-1
        text-[10px]
        bg-white
        border border-sand-200
        rounded
        text-text-muted
        ${className}
      `.trim()}
    >
      {children}
    </span>
  );
}
