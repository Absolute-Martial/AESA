'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client';

import {
  DashboardHeader,
  DashboardLayout,
} from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { DayTimetable, type TimetableBlock } from '@/components/timetable/DayTimetable';
import { GET_TODAY_SCHEDULE, GET_TASKS } from '@/lib/graphql/queries';

type NavId = 'today' | 'week' | 'tasks' | 'subjects' | 'timetable' | 'goals' | 'timer' | 'analytics' | 'chat' | 'settings';


/**
 * Dashboard Page - Main entry point for the Today view
 * Requirements: 13.1
 */
export default function DashboardPage() {
  const router = useRouter();

  const [selectedBlockId, setSelectedBlockId] = useState<string | undefined>(undefined);

  const { data: scheduleData, loading: scheduleLoading, error: scheduleError } = useQuery(GET_TODAY_SCHEDULE);
  const { data: tasksData } = useQuery(GET_TASKS, { variables: { filter: { isCompleted: false } } });

  const blocks: TimetableBlock[] = useMemo(() => {
    const sched = scheduleData?.todaySchedule;
    const dayBlocks = (sched?.blocks || []).map((b: any) => ({
      id: String(b.id),
      title: b.title,
      blockType: b.blockType,
      startTime: b.startTime,
      endTime: b.endTime,
      isFixed: Boolean(b.isFixed),
    }));

    // Add timetable classes into the same timeline
    const classes = (sched?.classes || []).map((c: any) => {
      const day = sched?.scheduleDate;
      const startTime = new Date(`${day}T${c.startTime}:00`).toISOString();
      const endTime = new Date(`${day}T${c.endTime}:00`).toISOString();
      return {
        id: `class-${c.subjectCode}-${c.startTime}-${c.endTime}`,
        title: `${c.subjectCode} ${c.classType}`,
        blockType: 'class',
        startTime,
        endTime,
        isFixed: true,
      };
    });

    return [...dayBlocks, ...classes].sort((a, b) => a.startTime.localeCompare(b.startTime));
  }, [scheduleData]);

  const nav: Array<{ id: NavId; label: string; icon: any; href: string; isActive: boolean }> = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: true },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'subjects', label: 'Subjects', icon: 'menu_book', href: '/dashboard/subjects', isActive: false },
    { id: 'timetable', label: 'Timetable', icon: 'calendar_month', href: '/dashboard/timetable', isActive: false },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: false },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: false },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: false },
  ];

  const handleNavClick = (id: string) => {
    const item = nav.find((n) => n.id === (id as NavId));
    if (item) router.push(item.href);
  };

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={nav}
          onNavClick={handleNavClick}
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
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {scheduleLoading && <div className="text-text-muted">Loading timetable…</div>}
        {scheduleError && <div className="text-red-600">Failed to load timetable: {scheduleError.message}</div>}

        {!scheduleLoading && !scheduleError && (
          <DayTimetable
            dateLabel={scheduleData?.todaySchedule?.scheduleDate || new Date().toISOString().slice(0, 10)}
            blocks={blocks}
            selectedBlockId={selectedBlockId}
            onSelectBlock={setSelectedBlockId}
          />
        )}

        <div>
          <div className="text-sm text-text-muted mb-2">Pending tasks</div>
          <ul className="space-y-2">
            {(tasksData?.tasks || []).slice(0, 8).map((t: any) => (
              <li key={t.id} className="rounded-xl border border-sand-200 bg-white p-3">
                <div className="font-semibold text-text-main">{t.title}</div>
                <div className="text-xs text-text-muted">{t.taskType} • {t.durationMinutes} min</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
