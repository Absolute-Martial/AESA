'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { GET_NOTIFICATIONS } from '@/lib/graphql/queries';

export default function NotificationsPage() {
  const router = useRouter();
  const { data, loading, error } = useQuery(GET_NOTIFICATIONS, { variables: { unreadOnly: false } });

  const navItems = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
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
      <div className="p-6 max-w-4xl mx-auto">
        <h1 className="text-2xl font-display font-semibold text-text-main mb-4">Notifications</h1>

        {loading && <div className="text-text-muted">Loading…</div>}
        {error && <div className="text-red-600">Failed to load: {error.message}</div>}

        {!loading && !error && (
          <div className="space-y-2">
            {(data?.notifications || []).length === 0 && <div className="text-text-muted">No notifications.</div>}
            {(data?.notifications || []).map((n: any) => (
              <div key={n.id} className="rounded-2xl border border-sand-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-semibold text-text-main">{n.title}</div>
                    {n.message && <div className="text-sm text-text-muted mt-1">{n.message}</div>}
                    <div className="text-xs text-text-muted mt-2">
                      {n.notificationType} • {new Date(n.createdAt).toLocaleString()}
                    </div>
                  </div>
                  <div className={`text-xs px-2 py-1 rounded-lg ${n.isRead ? 'bg-sand-100 text-text-muted' : 'bg-primary/10 text-primary'}`}>
                    {n.isRead ? 'Read' : 'Unread'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
