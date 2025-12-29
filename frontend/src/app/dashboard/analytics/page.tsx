'use client';

import React, { useState } from 'react';
import { 
  StudyAnalytics, 
  DashboardHeader, 
  DashboardLayout,
  type AnalyticsPeriod,
  type StudyAnalyticsData,
} from '@/components/dashboard';
import { Button, Icon } from '@/components/common';

// Mock data for demonstration
const mockAnalyticsData: StudyAnalyticsData = {
  totalStudyMinutes: 285,
  deepWorkMinutes: 120,
  tasksCompleted: 8,
  streakDays: 5,
  timeBySubject: [
    {
      subject: { id: 's1', code: 'COMP401', name: 'Machine Learning', color: '#6366f1' },
      minutes: 90,
    },
    {
      subject: { id: 's2', code: 'MATH201', name: 'Linear Algebra', color: '#f59e0b' },
      minutes: 75,
    },
    {
      subject: { id: 's3', code: 'PHYS102', name: 'Physics', color: '#ef4444' },
      minutes: 60,
    },
    {
      subject: { id: 's4', code: 'COMP201', name: 'Data Structures', color: '#8b5cf6' },
      minutes: 45,
    },
    {
      subject: { id: 's5', code: 'MATH101', name: 'Calculus', color: '#10b981' },
      minutes: 15,
    },
  ],
  dailyData: [
    { date: '2025-12-23', studyMinutes: 180, deepWorkMinutes: 90 },
    { date: '2025-12-24', studyMinutes: 240, deepWorkMinutes: 120 },
    { date: '2025-12-25', studyMinutes: 120, deepWorkMinutes: 60 },
    { date: '2025-12-26', studyMinutes: 300, deepWorkMinutes: 150 },
    { date: '2025-12-27', studyMinutes: 210, deepWorkMinutes: 90 },
    { date: '2025-12-28', studyMinutes: 270, deepWorkMinutes: 120 },
    { date: '2025-12-29', studyMinutes: 285, deepWorkMinutes: 120 },
  ],
};

const navItems = [
  { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
  { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
  { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
  { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: true },
];

/**
 * Analytics Page - Study statistics and charts
 * Requirements: 17.1, 17.4
 */
export default function AnalyticsPage() {
  const [period, setPeriod] = useState<AnalyticsPeriod>('week');

  const handleNavClick = (id: string) => {
    console.log('Navigate to:', id);
    // Would use router.push
  };

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={navItems}
          onNavClick={handleNavClick}
          actions={
            <>
              <Button variant="ghost" icon="notifications" size="sm" />
              <Button variant="ghost" icon="settings" size="sm" />
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Icon name="person" size={18} className="text-primary" />
              </div>
            </>
          }
        />
      }
    >
      <div className="p-6 max-w-4xl mx-auto">
        <StudyAnalytics
          data={mockAnalyticsData}
          period={period}
          onPeriodChange={setPeriod}
        />
      </div>
    </DashboardLayout>
  );
}
