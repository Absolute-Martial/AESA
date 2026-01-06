'use client';

import React, { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { GET_WEEK_SCHEDULE } from '@/lib/graphql/queries';

export default function WeekPage() {
  const router = useRouter();
  const startDate = useMemo(() => {
    const d = new Date();
    const iso = d.toISOString().slice(0, 10);
    return iso;
  }, []);

  const { data, loading, error } = useQuery(GET_WEEK_SCHEDULE, { variables: { startDate } });

  const navItems = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: true },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'subjects', label: 'Subjects', icon: 'menu_book', href: '/dashboard/subjects', isActive: false },
    { id: 'timetable', label: 'Timetable', icon: 'calendar_month', href: '/dashboard/timetable', isActive: false },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: false },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: false },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: false },
  ];

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={navItems}
          onNavClick={(id) => {
            const item = navItems.find((n) => n.id === id);
            if (item) router.push(item.href);
          }}
          actions={
            <>
              <Button variant="ghost" icon="notifications" size="sm" onClick={() => router.push('/dashboard/notifications')} />
              <Button variant="ghost" icon="settings" size="sm" onClick={() => router.push('/dashboard/settings')} />
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Icon name="person" size={18} className="text-primary" />
              </div>
            </>
          }
        />
      }
    >
      <div className="p-6 max-w-5xl mx-auto">
        <h1 className="text-2xl font-display font-semibold text-text-main mb-4">Week</h1>
        {loading && <div className="text-text-muted">Loading…</div>}
        {error && <div className="text-red-600">Failed to load: {error.message}</div>}
        {!loading && !error && (
          <div className="space-y-3">
            {(data?.weekSchedule || []).map((day: any) => (
              <div key={day.scheduleDate} className="rounded-2xl border border-sand-200 bg-white p-4">
                <div className="font-semibold text-text-main">{day.scheduleDate}</div>
                <div className="text-xs text-text-muted">
                  Blocks: {day.blocks?.length || 0} • Classes: {day.classes?.length || 0} • Deep work: {day.stats?.deepWorkMinutes || 0} min
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
