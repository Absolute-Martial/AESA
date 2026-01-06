import { gql } from '@apollo/client';

// Fragment for common task fields
export const TASK_FIELDS = gql`
  fragment TaskFields on Task {
    id
    title
    description
    taskType
    durationMinutes
    priority
    deadline
    isCompleted
    subjectId
    subject {
      id
      code
      name
      color
    }
  }
`;

// Fragment for time block fields
export const TIME_BLOCK_FIELDS = gql`
  fragment TimeBlockFields on TimeBlock {
    id
    title
    blockType
    startTime
    endTime
    isFixed
    task {
      ...TaskFields
    }
    metadata
  }
  ${TASK_FIELDS}
`;

// Fragment for goal fields
export const GOAL_FIELDS = gql`
  fragment GoalFields on Goal {
    id
    title
    description
    targetValue
    currentValue
    unit
    deadline
    status
  }
`;

// Fragment for notification fields
export const NOTIFICATION_FIELDS = gql`
  fragment NotificationFields on Notification {
    id
    notificationType
    title
    message
    isRead
    scheduledFor
    createdAt
  }
`;

// ============ QUERIES ============

// Get today's schedule
export const GET_TODAY_SCHEDULE = gql`
  query GetTodaySchedule {
    todaySchedule {
      scheduleDate
      blocks {
        ...TimeBlockFields
      }
      classes {
        subjectCode
        subjectName
        classType
        startTime
        endTime
        room
      }
      stats {
        totalStudyMinutes
        deepWorkMinutes
        hasDeepWorkOpportunity
        gapCount
        tasksCompleted
        energyLevel
      }
    }
  }
  ${TIME_BLOCK_FIELDS}
`;

// Get week schedule
export const GET_WEEK_SCHEDULE = gql`
  query GetWeekSchedule($startDate: String!) {
    weekSchedule(startDate: $startDate) {
      scheduleDate
      blocks {
        ...TimeBlockFields
      }
      classes {
        subjectCode
        subjectName
        classType
        startTime
        endTime
        room
      }
      stats {
        totalStudyMinutes
        deepWorkMinutes
        hasDeepWorkOpportunity
        gapCount
        tasksCompleted
        energyLevel
      }
    }
  }
  ${TIME_BLOCK_FIELDS}
`;

// Get tasks with optional filter
export const GET_TASKS = gql`
  query GetTasks($filter: TaskFilter) {
    tasks(filter: $filter) {
      ...TaskFields
    }
  }
  ${TASK_FIELDS}
`;

// Get single task
export const GET_TASK = gql`
  query GetTask($id: ID!) {
    task(id: $id) {
      ...TaskFields
    }
  }
  ${TASK_FIELDS}
`;

// Get subjects
export const GET_SUBJECTS = gql`
  query GetSubjects {
    subjects {
      id
      code
      name
      color
    }
  }
`;

// Get goals
export const GET_GOALS = gql`
  query GetGoals($status: GoalStatusEnum) {
    goals(status: $status) {
      ...GoalFields
    }
  }
  ${GOAL_FIELDS}
`;

// Get analytics
export const GET_ANALYTICS = gql`
  query GetAnalytics($period: AnalyticsPeriod!) {
    analytics(period: $period) {
      totalStudyMinutes
      deepWorkMinutes
      subjectsStudied
      streakDays
      dailyStats {
        date
        studyMinutes
        deepWorkMinutes
        tasksCompleted
      }
      subjectBreakdown {
        subjectId
        subjectCode
        subjectName
        totalMinutes
        percentage
      }
    }
  }
`;

// Get notifications
export const GET_NOTIFICATIONS = gql`
  query GetNotifications($unreadOnly: Boolean) {
    notifications(unreadOnly: $unreadOnly) {
      ...NotificationFields
    }
  }
  ${NOTIFICATION_FIELDS}
`;

// Get timer status
export const GET_TIMER_STATUS = gql`
  query GetTimerStatus {
    timerStatus {
      isRunning
      subjectId
      startedAt
      elapsedMinutes
    }
  }
`;
