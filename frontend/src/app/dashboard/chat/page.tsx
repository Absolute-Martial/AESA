'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { SEND_CHAT_MESSAGE } from '@/lib/graphql/mutations';

export default function ChatPage() {
  const router = useRouter();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);

  const [send, { loading, error }] = useMutation(SEND_CHAT_MESSAGE);

  const navItems = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: false },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: true },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: false },
  ];

  const transcript = useMemo(() => messages, [messages]);

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
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <h1 className="text-2xl font-display font-semibold text-text-main">Chat</h1>

        <div className="rounded-2xl border border-sand-200 bg-white p-4 h-[520px] overflow-y-auto">
          {transcript.length === 0 ? (
            <div className="text-text-muted">Ask the assistant to optimize your schedule, create blocks, or manage tasks.</div>
          ) : (
            <div className="space-y-3">
              {transcript.map((m, idx) => (
                <div key={idx} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                  <div className={`inline-block rounded-2xl px-4 py-2 ${m.role === 'user' ? 'bg-primary text-white' : 'bg-sand-100 text-text-main'}`}>
                    {m.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && <div className="text-red-600 text-sm">{error.message}</div>}

        <form
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            const text = input.trim();
            if (!text) return;

            setMessages((prev) => [...prev, { role: 'user', content: text }]);
            setInput('');

            const res = await send({ variables: { message: text } });
            const reply = res.data?.sendChatMessage?.message || '(no response)';
            setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 rounded-xl border border-sand-200 p-3"
            placeholder="Type a message…"
          />
          <Button type="submit" disabled={loading}>
            Send
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
}
