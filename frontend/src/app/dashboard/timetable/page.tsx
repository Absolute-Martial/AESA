'use client';

import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@apollo/client';

import { DashboardHeader, DashboardLayout } from '@/components/dashboard';
import { Button, Icon } from '@/components/common';
import { GET_SUBJECTS } from '@/lib/graphql/queries';

// Temporarily inline GraphQL documents until we add them to lib/graphql/queries.ts & mutations.ts
import { gql } from '@apollo/client';

const GET_TIMETABLE_SLOTS = gql`
  query GetTimetableSlots($dayOfWeek: Int, $subjectId: ID) {
    timetableSlots(dayOfWeek: $dayOfWeek, subjectId: $subjectId) {
      id
      dayOfWeek
      startTime
      endTime
      room
      classType
      subjectId
      subject {
        id
        code
        name
        color
      }
    }
  }
`;

const CREATE_TIMETABLE_SLOT = gql`
  mutation CreateTimetableSlot($input: CreateTimetableSlotInput!) {
    createTimetableSlot(input: $input) {
      id
      dayOfWeek
      startTime
      endTime
      room
      classType
      subjectId
      subject {
        id
        code
        name
        color
      }
    }
  }
`;

const UPDATE_TIMETABLE_SLOT = gql`
  mutation UpdateTimetableSlot($id: ID!, $input: UpdateTimetableSlotInput!) {
    updateTimetableSlot(id: $id, input: $input) {
      id
      dayOfWeek
      startTime
      endTime
      room
      classType
      subjectId
      subject {
        id
        code
        name
        color
      }
    }
  }
`;

const DELETE_TIMETABLE_SLOT = gql`
  mutation DeleteTimetableSlot($id: ID!) {
    deleteTimetableSlot(id: $id)
  }
`;

const IMPORT_TIMETABLE_CSV = gql`
  mutation ImportTimetableCsv($input: ImportTimetableCsvInput!) {
    importTimetableCsv(input: $input) {
      createdCount
      skippedCount
      errors
    }
  }
`;

type NavId = 'today' | 'week' | 'tasks' | 'subjects' | 'timetable' | 'goals' | 'timer' | 'analytics' | 'chat' | 'settings';

const DAYS: Array<{ label: string; value: number }> = [
  { label: 'Sun', value: 0 },
  { label: 'Mon', value: 1 },
  { label: 'Tue', value: 2 },
  { label: 'Wed', value: 3 },
  { label: 'Thu', value: 4 },
  { label: 'Fri', value: 5 },
  { label: 'Sat', value: 6 },
];

export default function TimetablePage() {
  const router = useRouter();

  const navItems: Array<{ id: NavId; label: string; icon: any; href: string; isActive: boolean }> = [
    { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
    { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
    { id: 'tasks', label: 'Tasks', icon: 'check_circle', href: '/dashboard/tasks', isActive: false },
    { id: 'subjects', label: 'Subjects', icon: 'menu_book', href: '/dashboard/subjects', isActive: false },
    { id: 'timetable', label: 'Timetable', icon: 'calendar_month', href: '/dashboard/timetable', isActive: true },
    { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: false },
    { id: 'timer', label: 'Timer', icon: 'timer', href: '/dashboard/timer', isActive: false },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
    { id: 'chat', label: 'Chat', icon: 'chat', href: '/dashboard/chat', isActive: false },
    { id: 'settings', label: 'Settings', icon: 'settings', href: '/dashboard/settings', isActive: false },
  ];

  const [selectedDay, setSelectedDay] = useState<number>(() => {
    const jsDay = new Date().getDay();
    // JS getDay(): 0=Sun..6=Sat matches backend convention
    return jsDay;
  });

  const { data: subjectsData } = useQuery(GET_SUBJECTS);
  const {
    data: slotsData,
    loading: slotsLoading,
    error: slotsError,
    refetch: refetchSlots,
  } = useQuery(GET_TIMETABLE_SLOTS, { variables: { dayOfWeek: selectedDay } });

  const [createSlot, { loading: creating, error: createError }] = useMutation(CREATE_TIMETABLE_SLOT, {
    onCompleted: () => refetchSlots(),
  });
  const [updateSlot, { loading: updating, error: updateError }] = useMutation(UPDATE_TIMETABLE_SLOT, {
    onCompleted: () => refetchSlots(),
  });
  const [deleteSlot, { loading: deleting, error: deleteError }] = useMutation(DELETE_TIMETABLE_SLOT, {
    onCompleted: () => refetchSlots(),
  });
  const [importCsv, { loading: importing, error: importError, data: importData }] = useMutation(IMPORT_TIMETABLE_CSV, {
    onCompleted: () => refetchSlots(),
  });

  const subjects = useMemo(() => subjectsData?.subjects || [], [subjectsData]);
  const slots = useMemo(() => slotsData?.timetableSlots || [], [slotsData]);

  const [subjectId, setSubjectId] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('09:00');
  const [endTime, setEndTime] = useState<string>('10:00');
  const [room, setRoom] = useState<string>('');
  const [classType, setClassType] = useState<'lecture' | 'lab'>('lecture');

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editSubjectId, setEditSubjectId] = useState<string>('');
  const [editStartTime, setEditStartTime] = useState<string>('');
  const [editEndTime, setEditEndTime] = useState<string>('');
  const [editRoom, setEditRoom] = useState<string>('');
  const [editClassType, setEditClassType] = useState<'lecture' | 'lab'>('lecture');

  const [csvRows, setCsvRows] = useState<Array<{ subjectCode: string; dayOfWeek: number; startTime: string; endTime: string; room?: string; classType?: string }>>([]);
  const [csvErrors, setCsvErrors] = useState<string[]>([]);

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={navItems}
          onNavClick={(id) => {
            const item = navItems.find((n) => n.id === (id as NavId));
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
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-display font-semibold text-text-main">Timetable</h1>
          <Button variant="ghost" disabled={slotsLoading} onClick={() => refetchSlots()}>
            Refresh
          </Button>
        </div>

        {(createError || updateError || deleteError || importError) && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {(createError || updateError || deleteError || importError)?.message}
          </div>
        )}

        <div className="rounded-2xl border border-sand-200 bg-white p-4 space-y-3">
          <div className="text-sm font-semibold text-text-main">Day</div>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((d) => (
              <Button
                key={d.value}
                size="sm"
                variant={selectedDay === d.value ? 'primary' : 'ghost'}
                onClick={() => setSelectedDay(d.value)}
              >
                {d.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-sand-200 bg-white p-4 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-text-main">CSV import</div>
              <div className="text-xs text-text-muted">Columns: subject_code, day_of_week(0-6), start_time(HH:MM), end_time(HH:MM), room, class_type(lecture|lab)</div>
            </div>
            <Button
              disabled={importing || csvRows.length === 0}
              onClick={async () => {
                await importCsv({
                  variables: {
                    input: {
                      mode: 'REPLACE',
                      rows: csvRows.map((r) => ({
                        subjectCode: r.subjectCode,
                        dayOfWeek: r.dayOfWeek,
                        startTime: r.startTime,
                        endTime: r.endTime,
                        room: r.room || null,
                        classType: r.classType || null,
                      })),
                    },
                  },
                });
              }}
            >
              Import (Replace)
            </Button>
          </div>

          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const reader = new FileReader();
              reader.onload = () => {
                const text = String(reader.result || '');
                const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
                if (lines.length === 0) {
                  setCsvRows([]);
                  setCsvErrors(['Empty CSV']);
                  return;
                }

                const header = lines[0].split(',').map((h) => h.trim().toLowerCase());
                const idx = (name: string) => header.indexOf(name);

                const req = ['subject_code', 'day_of_week', 'start_time', 'end_time'];
                const missing = req.filter((c) => idx(c) === -1);
                if (missing.length) {
                  setCsvRows([]);
                  setCsvErrors([`Missing columns: ${missing.join(', ')}`]);
                  return;
                }

                const rows: Array<{ subjectCode: string; dayOfWeek: number; startTime: string; endTime: string; room?: string; classType?: string }> = [];
                const errs: string[] = [];

                for (let i = 1; i < lines.length; i++) {
                  const cols = lines[i].split(',').map((c) => c.trim());
                  const get = (col: string) => cols[idx(col)] || '';

                  const subjectCode = get('subject_code').toUpperCase();
                  const dayStr = get('day_of_week');
                  const startTime = get('start_time');
                  const endTime = get('end_time');
                  const room = idx('room') !== -1 ? get('room') : '';
                  const classType = idx('class_type') !== -1 ? get('class_type').toLowerCase() : '';

                  const dayOfWeek = Number(dayStr);

                  if (!subjectCode) errs.push(`row ${i}: subject_code empty`);
                  if (!Number.isInteger(dayOfWeek) || dayOfWeek < 0 || dayOfWeek > 6) errs.push(`row ${i}: invalid day_of_week`);
                  if (!/^\d{2}:\d{2}$/.test(startTime)) errs.push(`row ${i}: invalid start_time (HH:MM)`);
                  if (!/^\d{2}:\d{2}$/.test(endTime)) errs.push(`row ${i}: invalid end_time (HH:MM)`);
                  if (classType && classType !== 'lecture' && classType !== 'lab') errs.push(`row ${i}: invalid class_type`);

                  rows.push({ subjectCode, dayOfWeek, startTime, endTime, room: room || undefined, classType: classType || undefined });
                }

                setCsvRows(rows);
                setCsvErrors(errs);
              };
              reader.readAsText(file);
            }}
          />

          {csvErrors.length > 0 && (
            <div className="text-sm text-red-600">
              <div className="font-semibold">CSV issues</div>
              <ul className="list-disc ml-5">
                {csvErrors.slice(0, 8).map((e, idx) => (
                  <li key={idx}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {importData?.importTimetableCsv && (
            <div className="text-sm text-text-muted">
              Imported: {importData.importTimetableCsv.createdCount} created, {importData.importTimetableCsv.skippedCount} skipped
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-sand-200 bg-white p-4 space-y-3">
          <div className="text-sm font-semibold text-text-main">Add class</div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <select
              className="rounded-xl border border-sand-200 p-3"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
            >
              <option value="">Select subject</option>
              {subjects.map((s: any) => (
                <option key={s.id} value={s.id}>
                  {s.code} — {s.name}
                </option>
              ))}
            </select>

            <input className="rounded-xl border border-sand-200 p-3" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
            <input className="rounded-xl border border-sand-200 p-3" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />

            <input className="rounded-xl border border-sand-200 p-3" value={room} onChange={(e) => setRoom(e.target.value)} placeholder="Room (optional)" />

            <select
              className="rounded-xl border border-sand-200 p-3"
              value={classType}
              onChange={(e) => setClassType(e.target.value as any)}
            >
              <option value="lecture">Lecture</option>
              <option value="lab">Lab</option>
            </select>
          </div>

          <div>
            <Button
              disabled={creating}
              onClick={async () => {
                if (!subjectId) return;
                await createSlot({
                  variables: {
                    input: {
                      subjectId,
                      dayOfWeek: selectedDay,
                      startTime,
                      endTime,
                      room: room.trim() || null,
                      classType,
                    },
                  },
                });
                setRoom('');
              }}
            >
              Add
            </Button>
          </div>
        </div>

        <div className="rounded-2xl border border-sand-200 bg-white p-4">
          <div className="text-sm font-semibold text-text-main mb-3">Classes</div>

          {slotsLoading && <div className="text-text-muted">Loading…</div>}
          {slotsError && <div className="text-red-600">Failed to load: {slotsError.message}</div>}

          {!slotsLoading && !slotsError && slots.length === 0 && (
            <div className="text-sm text-text-muted">No classes for this day.</div>
          )}

          {!slotsLoading && !slotsError && slots.length > 0 && (
            <div className="space-y-2">
              {slots.map((slot: any) => {
                const isEditing = editingId === slot.id;
                const label = slot.subject?.code ? `${slot.subject.code} ${slot.classType}` : slot.classType;
                return (
                  <div key={slot.id} className="rounded-xl border border-sand-200 p-3">
                    {!isEditing ? (
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-semibold text-text-main truncate">{label}</div>
                          <div className="text-xs text-text-muted">
                            {slot.startTime}–{slot.endTime}
                            {slot.room ? ` • ${slot.room}` : ''}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setEditingId(slot.id);
                              setEditSubjectId(slot.subjectId);
                              setEditStartTime(slot.startTime);
                              setEditEndTime(slot.endTime);
                              setEditRoom(slot.room || '');
                              setEditClassType(slot.classType);
                            }}
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={deleting}
                            onClick={async () => {
                              if (!confirm('Delete this class?')) return;
                              await deleteSlot({ variables: { id: slot.id } });
                            }}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                          <select
                            className="rounded-xl border border-sand-200 p-3"
                            value={editSubjectId}
                            onChange={(e) => setEditSubjectId(e.target.value)}
                          >
                            {subjects.map((s: any) => (
                              <option key={s.id} value={s.id}>
                                {s.code} — {s.name}
                              </option>
                            ))}
                          </select>

                          <input className="rounded-xl border border-sand-200 p-3" type="time" value={editStartTime} onChange={(e) => setEditStartTime(e.target.value)} />
                          <input className="rounded-xl border border-sand-200 p-3" type="time" value={editEndTime} onChange={(e) => setEditEndTime(e.target.value)} />
                          <input className="rounded-xl border border-sand-200 p-3" value={editRoom} onChange={(e) => setEditRoom(e.target.value)} placeholder="Room (optional)" />

                          <select
                            className="rounded-xl border border-sand-200 p-3"
                            value={editClassType}
                            onChange={(e) => setEditClassType(e.target.value as any)}
                          >
                            <option value="lecture">Lecture</option>
                            <option value="lab">Lab</option>
                          </select>
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            disabled={updating}
                            onClick={async () => {
                              await updateSlot({
                                variables: {
                                  id: slot.id,
                                  input: {
                                    subjectId: editSubjectId,
                                    dayOfWeek: selectedDay,
                                    startTime: editStartTime,
                                    endTime: editEndTime,
                                    room: editRoom.trim() || null,
                                    classType: editClassType,
                                  },
                                },
                              });
                              setEditingId(null);
                            }}
                          >
                            Save
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
