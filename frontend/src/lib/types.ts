/**
 * Core TypeScript types for AESA Frontend
 */

export type TaskType =
  | 'university'
  | 'study'
  | 'revision'
  | 'practice'
  | 'assignment'
  | 'lab_work'
  | 'deep_work'
  | 'break'
  | 'free_time'
  | 'sleep'
  | 'wake_routine'
  | 'breakfast'
  | 'lunch'
  | 'dinner';

export type TaskPriority =
  | 'OVERDUE'
  | 'DUE_TODAY'
  | 'EXAM_PREP'
  | 'URGENT_LAB'
  | 'REVISION_DUE'
  | 'ASSIGNMENT'
  | 'REGULAR_STUDY'
  | 'FREE_TIME';

export type TaskStatus = 'pending' | 'in_progress' | 'completed';

export type ColumnType = 'morning' | 'afternoon' | 'evening' | 'backlog';

export interface Subject {
  id: string;
  code: string;
  name: string;
  color?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  taskType: TaskType;
  durationMinutes: number;
  priority: number;
  deadline?: Date;
  isCompleted: boolean;
  subjectId?: string;
  subject?: Subject;
  status: TaskStatus;
}

export interface TimeBlock {
  id: string;
  title: string;
  blockType: TaskType;
  startTime: Date;
  endTime: Date;
  isFixed: boolean;
  task?: Task;
  metadata?: Record<string, unknown>;
}

export interface Gap {
  startTime: Date;
  endTime: Date;
  durationMinutes: number;
  type: 'micro' | 'standard' | 'deep_work';
  suggestedTaskType?: TaskType;
}

export interface DayStats {
  focusTimeMinutes: number;
  deepWorkMinutes: number;
  tasksCompleted: number;
  energyLevel: number;
}

export interface DaySchedule {
  date: Date;
  blocks: TimeBlock[];
  gaps: Gap[];
  stats: DayStats;
}

export interface Goal {
  id: string;
  title: string;
  description?: string;
  targetValue?: number;
  currentValue: number;
  unit?: string;
  deadline?: Date;
  status: 'active' | 'completed' | 'abandoned';
}

export interface TimerStatus {
  isRunning: boolean;
  subjectId?: string;
  startedAt?: Date;
  elapsedMinutes: number;
}

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  suggestions?: Suggestion[];
}

export interface Suggestion {
  text: string;
  actionLabel: string;
  action: () => void;
}

export interface Notification {
  id: string;
  type: 'reminder' | 'suggestion' | 'achievement' | 'warning' | 'motivation';
  title: string;
  message?: string;
  isRead: boolean;
  createdAt: Date;
}
