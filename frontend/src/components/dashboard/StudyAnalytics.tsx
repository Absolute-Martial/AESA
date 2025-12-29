'use client';

import React, { useState, useMemo } from 'react';
import { Icon, Button, Card } from '@/components/common';
import type { Subject } from '@/lib/types';

export type AnalyticsPeriod = 'today' | 'week' | 'month';

export interface StudyAnalyticsData {
  /** Total study time in minutes */
  totalStudyMinutes: number;
  /** Deep work time in minutes */
  deepWorkMinutes: number;
  /** Number of tasks completed */
  tasksCompleted: number;
  /** Current streak in days */
  streakDays: number;
  /** Study time by subject */
  timeBySubject: Array<{
    subject: Subject;
    minutes: number;
  }>;
  /** Daily breakdown (for charts) */
  dailyData?: Array<{
    date: string;
    studyMinutes: number;
    deepWorkMinutes: number;
  }>;
}

export interface StudyAnalyticsProps {
  /** Analytics data */
  data: StudyAnalyticsData;
  /** Current period */
  period: AnalyticsPeriod;
  /** Callback when period changes */
  onPeriodChange?: (period: AnalyticsPeriod) => void;
  /** Loading state */
  isLoading?: boolean;
}

/**
 * Format minutes to human-readable string
 */
function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * StudyAnalytics - Dashboard component for study statistics and charts
 * Requirements: 17.1, 17.4
 */
export function StudyAnalytics({
  data,
  period,
  onPeriodChange,
  isLoading = false,
}: StudyAnalyticsProps) {
  const periodLabels: Record<AnalyticsPeriod, string> = {
    today: 'Today',
    week: 'This Week',
    month: 'This Month',
  };

  // Calculate max for bar chart scaling
  const maxSubjectMinutes = useMemo(() => {
    return Math.max(...data.timeBySubject.map((s) => s.minutes), 1);
  }, [data.timeBySubject]);

  if (isLoading) {
    return <StudyAnalyticsSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header with Period Selector */}
      <div className="flex items-center justify-between">
        <h3 className="font-display font-semibold text-lg text-text-main flex items-center gap-2">
          <Icon name="analytics" size={22} className="text-primary" />
          Study Analytics
        </h3>
        <PeriodSelector
          value={period}
          onChange={onPeriodChange}
        />
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          icon="schedule"
          label="Total Study"
          value={formatDuration(data.totalStudyMinutes)}
          color="primary"
        />
        <MetricCard
          icon="psychology"
          label="Deep Work"
          value={formatDuration(data.deepWorkMinutes)}
          color="purple"
        />
        <MetricCard
          icon="task_alt"
          label="Tasks Done"
          value={data.tasksCompleted.toString()}
          color="green"
        />
        <MetricCard
          icon="local_fire_department"
          label="Streak"
          value={`${data.streakDays} days`}
          color="orange"
        />
      </div>

      {/* Time by Subject Chart */}
      <Card variant="elevated" padding="lg">
        <h4 className="font-display font-semibold text-text-main mb-4">
          Time by Subject
        </h4>
        {data.timeBySubject.length > 0 ? (
          <div className="space-y-3">
            {data.timeBySubject
              .sort((a, b) => b.minutes - a.minutes)
              .map(({ subject, minutes }) => (
                <SubjectBar
                  key={subject.id}
                  subject={subject}
                  minutes={minutes}
                  maxMinutes={maxSubjectMinutes}
                />
              ))}
          </div>
        ) : (
          <div className="text-center py-8 text-text-muted">
            <Icon name="bar_chart" size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No study data for this period</p>
          </div>
        )}
      </Card>

      {/* Daily Activity Chart (if available) */}
      {data.dailyData && data.dailyData.length > 0 && (
        <Card variant="elevated" padding="lg">
          <h4 className="font-display font-semibold text-text-main mb-4">
            Daily Activity
          </h4>
          <DailyActivityChart data={data.dailyData} />
        </Card>
      )}

      {/* Study Distribution Pie Chart */}
      {data.timeBySubject.length > 0 && (
        <Card variant="elevated" padding="lg">
          <h4 className="font-display font-semibold text-text-main mb-4">
            Study Distribution
          </h4>
          <StudyDistributionChart subjects={data.timeBySubject} />
        </Card>
      )}
    </div>
  );
}

/**
 * Period Selector Component
 */
interface PeriodSelectorProps {
  value: AnalyticsPeriod;
  onChange?: (period: AnalyticsPeriod) => void;
}

function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  const periods: AnalyticsPeriod[] = ['today', 'week', 'month'];
  const labels: Record<AnalyticsPeriod, string> = {
    today: 'Today',
    week: 'Week',
    month: 'Month',
  };

  return (
    <div className="flex bg-sand-100 rounded-lg p-1">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => onChange?.(period)}
          className={`
            px-3 py-1.5 text-sm font-medium rounded-md transition-colors
            ${value === period
              ? 'bg-surface-light text-text-main shadow-sm'
              : 'text-text-muted hover:text-text-main'
            }
          `}
        >
          {labels[period]}
        </button>
      ))}
    </div>
  );
}

/**
 * Metric Card Component
 */
interface MetricCardProps {
  icon: string;
  label: string;
  value: string;
  color: 'primary' | 'purple' | 'green' | 'orange';
}

const colorClasses: Record<MetricCardProps['color'], { bg: string; text: string }> = {
  primary: { bg: 'bg-primary/10', text: 'text-primary' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
  green: { bg: 'bg-green-100', text: 'text-green-600' },
  orange: { bg: 'bg-orange-100', text: 'text-orange-600' },
};

function MetricCard({ icon, label, value, color }: MetricCardProps) {
  const colors = colorClasses[color];

  return (
    <Card variant="default" padding="md">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors.bg}`}>
          <Icon name={icon} size={20} className={colors.text} />
        </div>
        <div>
          <p className="text-xs text-text-muted">{label}</p>
          <p className="text-lg font-display font-bold text-text-main">{value}</p>
        </div>
      </div>
    </Card>
  );
}

/**
 * Subject Bar Component (horizontal bar chart)
 */
interface SubjectBarProps {
  subject: Subject;
  minutes: number;
  maxMinutes: number;
}

function SubjectBar({ subject, minutes, maxMinutes }: SubjectBarProps) {
  const percentage = (minutes / maxMinutes) * 100;

  return (
    <div className="flex items-center gap-3">
      {/* Subject Label */}
      <div className="w-24 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: subject.color || '#6b7280' }}
          />
          <span className="text-sm font-medium text-text-main truncate">
            {subject.code}
          </span>
        </div>
      </div>

      {/* Bar */}
      <div className="flex-1 h-6 bg-sand-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percentage}%`,
            backgroundColor: subject.color || '#6b7280',
          }}
        />
      </div>

      {/* Duration */}
      <span className="w-16 text-right text-sm text-text-muted">
        {formatDuration(minutes)}
      </span>
    </div>
  );
}

/**
 * Daily Activity Chart (simple bar chart)
 */
interface DailyActivityChartProps {
  data: Array<{
    date: string;
    studyMinutes: number;
    deepWorkMinutes: number;
  }>;
}

function DailyActivityChart({ data }: DailyActivityChartProps) {
  const maxMinutes = Math.max(...data.map((d) => d.studyMinutes), 1);

  return (
    <div className="flex items-end gap-2 h-40">
      {data.map((day, index) => {
        const studyHeight = (day.studyMinutes / maxMinutes) * 100;
        const deepWorkHeight = (day.deepWorkMinutes / maxMinutes) * 100;
        const dayLabel = new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' });

        return (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            {/* Bars */}
            <div className="w-full flex-1 flex flex-col justify-end">
              <div className="relative w-full">
                {/* Study time bar */}
                <div
                  className="w-full bg-primary/30 rounded-t transition-all duration-500"
                  style={{ height: `${studyHeight}%`, minHeight: day.studyMinutes > 0 ? '4px' : '0' }}
                />
                {/* Deep work overlay */}
                <div
                  className="absolute bottom-0 w-full bg-primary rounded-t transition-all duration-500"
                  style={{ height: `${deepWorkHeight}%`, minHeight: day.deepWorkMinutes > 0 ? '4px' : '0' }}
                />
              </div>
            </div>
            {/* Day label */}
            <span className="text-xs text-text-muted">{dayLabel}</span>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Study Distribution Chart (simple pie/donut visualization)
 */
interface StudyDistributionChartProps {
  subjects: Array<{
    subject: Subject;
    minutes: number;
  }>;
}

function StudyDistributionChart({ subjects }: StudyDistributionChartProps) {
  const total = subjects.reduce((sum, s) => sum + s.minutes, 0);

  // Calculate segments for the donut chart
  let currentAngle = 0;
  const segments = subjects.map(({ subject, minutes }) => {
    const percentage = (minutes / total) * 100;
    const angle = (minutes / total) * 360;
    const segment = {
      subject,
      minutes,
      percentage,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
    };
    currentAngle += angle;
    return segment;
  });

  return (
    <div className="flex items-center gap-8">
      {/* Simple Donut Chart using CSS */}
      <div className="relative w-32 h-32 flex-shrink-0">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          {segments.map((segment, index) => {
            const radius = 40;
            const circumference = 2 * Math.PI * radius;
            const strokeDasharray = (segment.percentage / 100) * circumference;
            const strokeDashoffset = segments
              .slice(0, index)
              .reduce((sum, s) => sum + (s.percentage / 100) * circumference, 0);

            return (
              <circle
                key={segment.subject.id}
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                stroke={segment.subject.color || '#6b7280'}
                strokeWidth="20"
                strokeDasharray={`${strokeDasharray} ${circumference}`}
                strokeDashoffset={-strokeDashoffset}
                className="transition-all duration-500"
              />
            );
          })}
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-bold text-text-main">{formatDuration(total)}</p>
            <p className="text-xs text-text-muted">Total</p>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1 space-y-2">
        {segments.map(({ subject, minutes, percentage }) => (
          <div key={subject.id} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: subject.color || '#6b7280' }}
              />
              <span className="text-sm text-text-main">{subject.name}</span>
            </div>
            <span className="text-sm text-text-muted">
              {Math.round(percentage)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Loading Skeleton
 */
function StudyAnalyticsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-6 w-40 bg-sand-200 rounded" />
        <div className="h-8 w-32 bg-sand-200 rounded-lg" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-sand-200 rounded-2xl" />
        ))}
      </div>
      <div className="h-48 bg-sand-200 rounded-2xl" />
    </div>
  );
}

/**
 * StudyAnalyticsCompact - Compact version for sidebar/header
 */
export interface StudyAnalyticsCompactProps {
  totalMinutes: number;
  deepWorkMinutes: number;
  onClick?: () => void;
}

export function StudyAnalyticsCompact({
  totalMinutes,
  deepWorkMinutes,
  onClick,
}: StudyAnalyticsCompactProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 px-3 py-2 bg-sand-100 hover:bg-sand-200 rounded-lg transition-colors"
    >
      <Icon name="analytics" size={18} className="text-primary" />
      <div className="text-left">
        <p className="text-xs text-text-muted">Today&apos;s Study</p>
        <p className="text-sm font-medium text-text-main">
          {formatDuration(totalMinutes)}
          {deepWorkMinutes > 0 && (
            <span className="text-primary ml-1">
              ({formatDuration(deepWorkMinutes)} deep)
            </span>
          )}
        </p>
      </div>
    </button>
  );
}
