'use client';

import React, { forwardRef } from 'react';
import { Icon } from './Icon';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Label text */
  label?: string;
  /** Error message */
  error?: string;
  /** Helper text */
  helperText?: string;
  /** Icon name to display on the left */
  leftIcon?: string;
  /** Icon name to display on the right */
  rightIcon?: string;
  /** Click handler for right icon */
  onRightIconClick?: () => void;
  /** Full width input */
  fullWidth?: boolean;
}

/**
 * Input component with label, icons, and error states
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      onRightIconClick,
      fullWidth = false,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    
    const baseInputStyles = `
      w-full py-3 
      bg-surface-light 
      border border-sand-200
      rounded-xl 
      text-sm text-text-main
      placeholder:text-text-muted
      focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
      shadow-sm
      transition-colors
    `;
    
    const paddingStyles = `
      ${leftIcon ? 'pl-10' : 'pl-4'}
      ${rightIcon ? 'pr-10' : 'pr-4'}
    `;
    
    const errorStyles = error
      ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500'
      : '';
    
    const widthClass = fullWidth ? 'w-full' : '';
    
    return (
      <div className={`${widthClass} ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-text-main mb-1.5"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
              <Icon name={leftIcon} size={18} />
            </span>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className={`
              ${baseInputStyles}
              ${paddingStyles}
              ${errorStyles}
            `.trim()}
            {...props}
          />
          
          {rightIcon && (
            <button
              type="button"
              onClick={onRightIconClick}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
            >
              <Icon name={rightIcon} size={18} filled />
            </button>
          )}
        </div>
        
        {error && (
          <p className="mt-1.5 text-xs text-red-500">{error}</p>
        )}
        
        {helperText && !error && (
          <p className="mt-1.5 text-xs text-text-muted">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
