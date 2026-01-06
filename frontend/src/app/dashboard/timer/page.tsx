'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { GET_TIMER_STATUS, GET_SUBJECTS } from '@/lib/graphql/queries';
import { START_TIMER, STOP_TIMER } from '@/lib/graphql/mutations';

export default function TimerPage() {
  const router = useRouter();

  const { data: statusData, loading: statusLoading, error: statusError, refetch } = useQuery(GET_TIMER_STATUS);
  const { data: subjectsData } = useQuery(GET_SUBJECTS);

  const [startTimer, { loading: startLoading, error: startError }] = useMutation(START_TIMER, {
    onCompleted: () => refetch(),
  });
  const [stopTimer, { loading: stopLoading, error: stopError }] = useMutation(STOP_TIMER, {
    onCompleted: () => refetch(),
  });

  const navItems = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'subjects', label: 'Subjects', icon: 'menu_book', href: '/dashboard/subjects', isActive: false },
    { id: 'timetable', label: 'Timetable', icon: 'calendar_month', href: '/dashboard/timetable', isActive: false },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: true },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: false },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: false },
  ];

  const status = statusData?.timerStatus;

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
      <div className="p-6 max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl font-display font-semibold text-text-main">Timer</h1>

        {statusLoading && <div className="text-text-muted">Loading…</div>}
        {statusError && <div className="text-red-600">Failed to load: {statusError.message}</div>}

        {!statusLoading && status && (
          <div className="rounded-2xl border border-sand-200 bg-white p-4">
            <div className="text-sm text-text-muted">Status</div>
            <div className="text-lg font-semibold text-text-main">
              {status.isRunning ? 'Running' : 'Stopped'}
            </div>
            {status.isRunning && (
              <div className="text-sm text-text-muted mt-1">
                Elapsed: {status.elapsedMinutes} min
              </div>
            )}

            <div className="mt-4 flex gap-3">
              {!status.isRunning ? (
                <Button
                  disabled={startLoading}
                  onClick={() => {
                    const firstSubject = subjectsData?.subjects?.[0]?.id;
                    startTimer({ variables: { subjectId: firstSubject || null } });
                  }}
                >
                  Start
                </Button>
              ) : (
                <Button disabled={stopLoading} onClick={() => stopTimer()}>
                  Stop
                </Button>
              )}
            </div>

            {(startError || stopError) && (
              <div className="text-red-600 text-sm mt-2">{(startError || stopError)?.message}</div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
