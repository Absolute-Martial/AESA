'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Icon, Button } from '@/components/common';
import type { Subject, TimerStatus } from '@/lib/types';

export interface StudyTimerProps {
  /** Available subjects for selection */
  subjects: Subject[];
  /** Initial timer status */
  initialStatus?: TimerStatus;
  /** Callback when timer starts */
  onStart?: (subjectId?: string) => void;
  /** Callback when timer stops */
  onStop?: () => void;
  /** API endpoint for timer operations */
  apiEndpoint?: string;
  /** Compact mode for header display */
  compact?: boolean;
}

/**
 * Format seconds to HH:MM:SS or MM:SS
 */
function formatTime(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const pad = (n: number) => n.toString().padStart(2, '0');

  if (hours > 0) {
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }
  return `${pad(minutes)}:${pad(seconds)}`;
}

/**
 * StudyTimer - Timer component for tracking study sessions
 * Requirements: 15.1
 */
export function StudyTimer({
  subjects,
  initialStatus,
  onStart,
  onStop,
  apiEndpoint = '/api/timer',
  compact = false,
}: StudyTimerProps) {
  const [isRunning, setIsRunning] = useState(initialStatus?.isRunning ?? false);
  const [elapsedSeconds, setElapsedSeconds] = useState(
    (initialStatus?.elapsedMinutes ?? 0) * 60
  );
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | undefined>(
    initialStatus?.subjectId
  );
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Timer tick effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isRunning) {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning]);

  // Start timer
  const handleStart = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiEndpoint}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subjectCode: selectedSubjectId }),
      });

      if (response.ok) {
        setIsRunning(true);
        onStart?.(selectedSubjectId);
      }
    } catch (error) {
      console.error('Failed to start timer:', error);
      // Start locally even if API fails
      setIsRunning(true);
      onStart?.(selectedSubjectId);
    } finally {
      setIsLoading(false);
    }
  }, [apiEndpoint, selectedSubjectId, onStart]);

  // Stop timer
  const handleStop = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiEndpoint}/stop`, {
        method: 'POST',
      });

      if (response.ok) {
        setIsRunning(false);
        setElapsedSeconds(0);
        onStop?.();
      }
    } catch (error) {
      console.error('Failed to stop timer:', error);
      // Stop locally even if API fails
      setIsRunning(false);
      setElapsedSeconds(0);
      onStop?.();
    } finally {
      setIsLoading(false);
    }
  }, [apiEndpoint, onStop]);

  // Get selected subject
  const selectedSubject = subjects.find((s) => s.id === selectedSubjectId);

  // Compact mode for header
  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {/* Timer Display */}
        <div className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg
          ${isRunning ? 'bg-primary/10 text-primary' : 'bg-sand-100 text-text-muted'}
        `}>
          <Icon name={isRunning ? 'timer' : 'timer_off'} size={16} />
          <span className="font-mono font-medium text-sm">
            {formatTime(elapsedSeconds)}
          </span>
        </div>

        {/* Subject Badge */}
        {selectedSubject && isRunning && (
          <span 
            className="px-2 py-1 rounded text-xs font-medium"
            style={{ 
              backgroundColor: `${selectedSubject.color}20`,
              color: selectedSubject.color 
            }}
          >
            {selectedSubject.code}
          </span>
        )}

        {/* Quick Controls */}
        {isRunning ? (
          <Button
            variant="ghost"
            size="sm"
            icon="stop"
            onClick={handleStop}
            loading={isLoading}
          />
        ) : (
          <Button
            variant="ghost"
            size="sm"
            icon="play_arrow"
            onClick={handleStart}
            loading={isLoading}
          />
        )}
      </div>
    );
  }

  // Full mode
  return (
    <div className="bg-surface-light rounded-2xl border border-sand-200 p-4 shadow-soft">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display font-semibold text-text-main flex items-center gap-2">
          <Icon name="timer" size={20} className="text-primary" />
          Study Timer
        </h3>
        {isRunning && (
          <span className="flex items-center gap-1 text-xs text-primary font-medium">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            Recording
          </span>
        )}
      </div>

      {/* Timer Display */}
      <div className="text-center mb-4">
        <div className={`
          text-4xl font-mono font-bold tracking-wider
          ${isRunning ? 'text-primary' : 'text-text-main'}
        `}>
          {formatTime(elapsedSeconds)}
        </div>
        {selectedSubject && (
          <p className="text-sm text-text-muted mt-1">
            Studying <span className="font-medium" style={{ color: selectedSubject.color }}>
              {selectedSubject.name}
            </span>
          </p>
        )}
      </div>

      {/* Subject Selection Dropdown */}
      {!isRunning && (
        <div className="relative mb-4">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full flex items-center justify-between px-4 py-3 bg-sand-100 rounded-xl text-sm text-text-main hover:bg-sand-200 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Icon name="school" size={18} className="text-text-muted" />
              {selectedSubject ? (
                <span className="flex items-center gap-2">
                  <span 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: selectedSubject.color }}
                  />
                  {selectedSubject.name}
                </span>
              ) : (
                <span className="text-text-muted">Select subject (optional)</span>
              )}
            </span>
            <Icon 
              name={isDropdownOpen ? 'expand_less' : 'expand_more'} 
              size={18} 
              className="text-text-muted"
            />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-surface-light rounded-xl border border-sand-200 shadow-lg z-10 overflow-hidden">
              <button
                onClick={() => {
                  setSelectedSubjectId(undefined);
                  setIsDropdownOpen(false);
                }}
                className="w-full px-4 py-2.5 text-left text-sm text-text-muted hover:bg-sand-100 transition-colors"
              >
                No subject
              </button>
              {subjects.map((subject) => (
                <button
                  key={subject.id}
                  onClick={() => {
                    setSelectedSubjectId(subject.id);
                    setIsDropdownOpen(false);
                  }}
                  className="w-full px-4 py-2.5 text-left text-sm text-text-main hover:bg-sand-100 transition-colors flex items-center gap-2"
                >
                  <span 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: subject.color }}
                  />
                  <span>{subject.code}</span>
                  <span className="text-text-muted">- {subject.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Controls */}
      <div className="flex gap-3">
        {isRunning ? (
          <>
            <Button
              variant="secondary"
              size="lg"
              icon="pause"
              onClick={() => setIsRunning(false)}
              className="flex-1"
            >
              Pause
            </Button>
            <Button
              variant="primary"
              size="lg"
              icon="stop"
              onClick={handleStop}
              loading={isLoading}
              className="flex-1"
            >
              Stop
            </Button>
          </>
        ) : (
          <Button
            variant="primary"
            size="lg"
            icon="play_arrow"
            onClick={handleStart}
            loading={isLoading}
            fullWidth
          >
            {elapsedSeconds > 0 ? 'Resume' : 'Start Session'}
          </Button>
        )}
      </div>

      {/* Deep Work Indicator */}
      {elapsedSeconds >= 90 * 60 && (
        <div className="mt-4 p-3 bg-primary/10 rounded-xl flex items-center gap-2">
          <Icon name="psychology" size={20} className="text-primary" />
          <span className="text-sm text-primary font-medium">
            Deep Work Session! 🎉
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * StudyTimerCompact - Compact version for header integration
 */
export function StudyTimerCompact(props: Omit<StudyTimerProps, 'compact'>) {
  return <StudyTimer {...props} compact />;
}
