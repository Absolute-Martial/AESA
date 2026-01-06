'use client';

import React, { useMemo } from 'react';
import { Card } from '@/components/common/Card';

export interface TimetableBlock {
  id: string;
  title: string;
  blockType: string;
  startTime: string; // ISO
  endTime: string; // ISO
  isFixed: boolean;
}

export interface DayTimetableProps {
  dateLabel: string;
  blocks: TimetableBlock[];
  onSelectBlock?: (blockId: string) => void;
  selectedBlockId?: string;
  startHour?: number; // default 6
  endHour?: number; // default 24
}

function minutesSinceStartOfDay(iso: string): number {
  const d = new Date(iso);
  return d.getHours() * 60 + d.getMinutes();
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function DayTimetable({
  dateLabel,
  blocks,
  onSelectBlock,
  selectedBlockId,
  startHour = 6,
  endHour = 24,
}: DayTimetableProps) {
  const rangeStart = startHour * 60;
  const rangeEnd = endHour * 60;
  const rangeMinutes = rangeEnd - rangeStart;

  const positioned = useMemo(() => {
    return blocks
      .map((b) => {
        const start = Math.max(rangeStart, minutesSinceStartOfDay(b.startTime));
        const end = Math.min(rangeEnd, minutesSinceStartOfDay(b.endTime));
        const topPct = ((start - rangeStart) / rangeMinutes) * 100;
        const heightPct = Math.max(1, ((end - start) / rangeMinutes) * 100);
        return { ...b, topPct, heightPct, start, end };
      })
      .filter((b) => b.end > b.start)
      .sort((a, b) => a.start - b.start);
  }, [blocks, rangeStart, rangeEnd, rangeMinutes]);

  const hours = useMemo(() => {
    const out: number[] = [];
    for (let h = startHour; h <= endHour; h += 1) out.push(h);
    return out;
  }, [startHour, endHour]);

  return (
    <Card variant="elevated" padding="md" className="overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm text-text-muted">Timetable</div>
          <div className="text-lg font-display font-semibold text-text-main">{dateLabel}</div>
        </div>
        <div className="text-xs text-text-muted">{startHour}:00 – {endHour}:00</div>
      </div>

      <div className="grid grid-cols-[64px_1fr] gap-3">
        {/* Hour labels */}
        <div className="relative">
          {hours.map((h) => (
            <div key={h} className="h-16 text-xs text-text-muted flex items-start justify-end pr-2">
              {String(h).padStart(2, '0')}:00
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div className="relative overflow-hidden rounded-2xl border border-sand-200 bg-sand-50">
          <div className="relative h-[calc(16*64px)]">
            {/* grid lines */}
            {hours.map((h) => (
              <div
                key={h}
                className="absolute left-0 right-0 border-t border-sand-200/70"
                style={{ top: `${((h * 60 - rangeStart) / rangeMinutes) * 100}%` }}
              />
            ))}

            {/* blocks */}
            {positioned.map((b) => {
              const selected = b.id === selectedBlockId;
              return (
                <button
                  key={b.id}
                  type="button"
                  onClick={() => onSelectBlock?.(b.id)}
                  className={`absolute left-3 right-3 rounded-xl text-left p-3 transition border
                    ${b.isFixed ? 'bg-primary/10 border-primary/20' : 'bg-white border-sand-200'}
                    ${selected ? 'ring-2 ring-primary' : 'hover:shadow-soft'}
                  `}
                  style={{ top: `${b.topPct}%`, height: `${b.heightPct}%` }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-text-main truncate">{b.title}</div>
                      <div className="text-xs text-text-muted truncate">{b.blockType}</div>
                    </div>
                    <div className="text-xs text-text-muted whitespace-nowrap">
                      {formatTime(b.startTime)} – {formatTime(b.endTime)}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}
