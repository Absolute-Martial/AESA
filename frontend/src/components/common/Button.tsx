'use client';

import React from 'react';
import { Icon } from './Icon';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'icon';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button style variant */
  variant?: ButtonVariant;
  /** Button size */
  size?: ButtonSize;
  /** Icon name to display (Material Symbols) */
  icon?: string;
  /** Position of icon relative to text */
  iconPosition?: 'left' | 'right';
  /** Whether button is in loading state */
  loading?: boolean;
  /** Full width button */
  fullWidth?: boolean;
  /** Children content */
  children?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: `
    bg-primary text-white 
    hover:bg-[#16a03d] 
    shadow-lg shadow-primary/20
    font-bold tracking-wide
  `,
  secondary: `
    bg-sand text-text-main 
    hover:bg-sand-200
    font-medium
  `,
  ghost: `
    bg-transparent text-text-muted 
    hover:bg-black/5 hover:text-text-main
    font-medium
  `,
  icon: `
    bg-sand text-text-main 
    hover:bg-sand-200
    p-0
  `,
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
};

const iconSizeStyles: Record<ButtonSize, string> = {
  sm: 'size-8',
  md: 'size-10',
  lg: 'size-12',
};

/**
 * Button component with multiple variants and sizes
 */
export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  fullWidth = false,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const isIconOnly = variant === 'icon';
  
  const baseStyles = `
    inline-flex items-center justify-center
    rounded-xl
    transition-colors
    cursor-pointer
    disabled:opacity-50 disabled:cursor-not-allowed
  `;
  
  const sizeClass = isIconOnly ? iconSizeStyles[size] : sizeStyles[size];
  const widthClass = fullWidth ? 'w-full' : '';
  
  const iconSize = size === 'sm' ? 16 : size === 'md' ? 18 : 20;
  
  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeClass}
        ${widthClass}
        ${className}
      `.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="animate-spin">
          <Icon name="progress_activity" size={iconSize} />
        </span>
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <Icon name={icon} size={iconSize} />
          )}
          {children}
          {icon && iconPosition === 'right' && (
            <Icon name={icon} size={iconSize} />
          )}
        </>
      )}
    </button>
  );
}
