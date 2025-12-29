'use client';

import React from 'react';

export interface SkeletonProps {
  /** Width of the skeleton */
  width?: string | number;
  /** Height of the skeleton */
  height?: string | number;
  /** Border radius variant */
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  /** Additional CSS classes */
  className?: string;
}

const variantStyles: Record<string, string> = {
  text: 'rounded',
  circular: 'rounded-full',
  rectangular: 'rounded-none',
  rounded: 'rounded-xl',
};

/**
 * Skeleton loading placeholder component
 */
export function Skeleton({
  width,
  height,
  variant = 'text',
  className = '',
}: SkeletonProps) {
  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      className={`
        animate-pulse 
        bg-sand-200 dark:bg-gray-700
        ${variantStyles[variant]}
        ${className}
      `.trim()}
      style={style}
    />
  );
}

/**
 * Skeleton for a task card
 */
export function TaskCardSkeleton() {
  return (
    <div className="bg-surface-light/60 border border-sand-200 p-5 rounded-2xl">
      <div className="flex justify-between items-center">
        <div className="flex gap-3 items-center">
          <Skeleton variant="rounded" width={40} height={40} />
          <div>
            <Skeleton width={150} height={20} className="mb-2" />
            <Skeleton width={80} height={14} />
          </div>
        </div>
        <Skeleton width={24} height={24} />
      </div>
    </div>
  );
}

/**
 * Skeleton for an active task card
 */
export function ActiveTaskCardSkeleton() {
  return (
    <div className="bg-surface-light border border-primary/20 p-5 rounded-2xl shadow-soft">
      <div className="flex justify-between items-start mb-4">
        <div className="flex gap-4">
          <Skeleton variant="rounded" width={48} height={48} />
          <div>
            <Skeleton width={180} height={24} className="mb-2" />
            <Skeleton width={120} height={16} />
          </div>
        </div>
        <Skeleton variant="rounded" width={90} height={24} />
      </div>
      
      <div className="bg-sand/30 p-4 rounded-xl mb-6">
        <div className="flex justify-between mb-2">
          <Skeleton width={100} height={14} />
          <Skeleton width={30} height={14} />
        </div>
        <Skeleton variant="rounded" width="100%" height={8} />
        <Skeleton width={80} height={12} className="mt-2" />
      </div>
      
      <div className="flex gap-3">
        <Skeleton variant="rounded" width="100%" height={48} className="flex-1" />
        <Skeleton variant="rounded" width={48} height={48} />
        <Skeleton variant="rounded" width={48} height={48} />
      </div>
    </div>
  );
}

/**
 * Skeleton for a column
 */
export function ColumnSkeleton() {
  return (
    <div className="min-w-[320px] bg-sand-50 border border-sand-200 rounded-3xl p-6 flex flex-col gap-4 shadow-soft">
      <div className="flex justify-between items-center mb-2">
        <Skeleton width={160} height={24} />
        <Skeleton variant="circular" width={24} height={24} />
      </div>
      <Skeleton width={120} height={14} />
      
      <div className="flex-1 flex flex-col gap-4">
        <TaskCardSkeleton />
        <TaskCardSkeleton />
      </div>
    </div>
  );
}

/**
 * Skeleton for the flow board
 */
export function FlowBoardSkeleton() {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      <ColumnSkeleton />
      <ColumnSkeleton />
      <ColumnSkeleton />
      <ColumnSkeleton />
    </div>
  );
}
