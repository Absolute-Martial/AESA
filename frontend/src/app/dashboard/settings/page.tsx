'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { UPDATE_ASSISTANT_SETTINGS } from '@/lib/graphql/mutations';

const STORAGE_KEYS = {
  assistantBaseUrl: 'aesa.assistant.baseUrl',
  assistantModel: 'aesa.assistant.model',
};

export default function SettingsPage() {
  const router = useRouter();

  const [baseUrl, setBaseUrl] = useState('http://localhost:3000/v1');
  const [model, setModel] = useState('');

  const [updateAssistantSettings, { loading: saving, error: saveError }] = useMutation(UPDATE_ASSISTANT_SETTINGS);

  useEffect(() => {
    const savedBaseUrl = localStorage.getItem(STORAGE_KEYS.assistantBaseUrl);
    const savedModel = localStorage.getItem(STORAGE_KEYS.assistantModel);
    if (savedBaseUrl) setBaseUrl(savedBaseUrl);
    if (savedModel) setModel(savedModel);
  }, []);

  const navItems = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'subjects', label: 'Subjects', icon: 'menu_book', href: '/dashboard/subjects', isActive: false },
    { id: 'timetable', label: 'Timetable', icon: 'calendar_month', href: '/dashboard/timetable', isActive: false },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: false },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: false },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: true },
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
      <div className="p-6 max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl font-display font-semibold text-text-main">Settings</h1>

        <div className="rounded-2xl border border-sand-200 bg-white p-4 space-y-3">
          {saveError && <div className="text-red-600 text-sm">{saveError.message}</div>}
          <div>
            <div className="text-sm font-semibold text-text-main">Assistant base URL</div>
            <div className="text-xs text-text-muted">OpenAI-compatible endpoint base (e.g. http://localhost:3000/v1)</div>
            <input
              className="mt-2 w-full rounded-xl border border-sand-200 p-3"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>

          <div>
            <div className="text-sm font-semibold text-text-main">Assistant model</div>
            <div className="text-xs text-text-muted">Model name returned by /v1/models</div>
            <input
              className="mt-2 w-full rounded-xl border border-sand-200 p-3"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gpt-4o-mini"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              disabled={saving}
              onClick={async () => {
                const nextBaseUrl = baseUrl.trim();
                const nextModel = model.trim();

                localStorage.setItem(STORAGE_KEYS.assistantBaseUrl, nextBaseUrl);
                localStorage.setItem(STORAGE_KEYS.assistantModel, nextModel);

                await updateAssistantSettings({
                  variables: { input: { baseUrl: nextBaseUrl || null, model: nextModel || null } },
                });
              }}
            >
              Save
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                localStorage.removeItem(STORAGE_KEYS.assistantBaseUrl);
                localStorage.removeItem(STORAGE_KEYS.assistantModel);
                setBaseUrl('http://localhost:3000/v1');
                setModel('');
              }}
            >
              Reset
            </Button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
