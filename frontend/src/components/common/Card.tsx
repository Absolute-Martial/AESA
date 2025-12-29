'use client';

import React from 'react';

export type CardVariant = 'default' | 'elevated' | 'outlined' | 'glass' | 'active';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Card style variant */
  variant?: CardVariant;
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Whether the card is interactive (hoverable) */
  interactive?: boolean;
  /** Children content */
  children: React.ReactNode;
}

const variantStyles: Record<CardVariant, string> = {
  default: `
    bg-surface-light/60 
    border border-transparent 
    hover:border-sand-200
  `,
  elevated: `
    bg-surface-light 
    border border-sand-200 
    shadow-soft
  `,
  outlined: `
    bg-transparent 
    border border-sand-200
  `,
  glass: `
    bg-white/80 dark:bg-gray-900/80 
    backdrop-blur-[12px] 
    shadow-glass 
    border border-sand-200/50
  `,
  active: `
    bg-surface-light 
    border border-primary/20 
    shadow-soft
    relative
  `,
};

const paddingStyles: Record<string, string> = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-5',
};

/**
 * Card component for containing content
 */
export function Card({
  variant = 'default',
  padding = 'md',
  interactive = false,
  children,
  className = '',
  ...props
}: CardProps) {
  const baseStyles = 'rounded-2xl transition-all';
  const interactiveStyles = interactive ? 'cursor-pointer' : '';
  
  return (
    <div
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${paddingStyles[padding]}
        ${interactiveStyles}
        ${className}
      `.trim()}
      {...props}
    >
      {variant === 'active' && (
        <div className="absolute inset-0 bg-primary/5 rounded-3xl blur-xl -z-10 translate-y-2" />
      )}
      {children}
    </div>
  );
}

/**
 * Card Header component
 */
export interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, action, className = '' }: CardHeaderProps) {
  return (
    <div className={`flex justify-between items-start mb-4 ${className}`}>
      <div>
        <h3 className="text-lg font-display font-semibold text-text-main">{title}</h3>
        {subtitle && (
          <p className="text-sm text-text-muted mt-0.5">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

/**
 * Card Content component
 */
export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
  return <div className={className}>{children}</div>;
}

/**
 * Card Footer component
 */
export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function CardFooter({ children, className = '' }: CardFooterProps) {
  return (
    <div className={`mt-4 flex gap-3 ${className}`}>
      {children}
    </div>
  );
}
