import { gql } from '@apollo/client';
import { TASK_FIELDS, TIME_BLOCK_FIELDS, GOAL_FIELDS } from './queries';

// ============ TASK MUTATIONS ============

export const CREATE_TASK = gql`
  mutation CreateTask($input: CreateTaskInput!) {
    createTask(input: $input) {
      ...TaskFields
    }
  }
  ${TASK_FIELDS}
`;

export const UPDATE_TASK = gql`
  mutation UpdateTask($id: ID!, $input: UpdateTaskInput!) {
    updateTask(id: $id, input: $input) {
      ...TaskFields
    }
  }
  ${TASK_FIELDS}
`;

export const DELETE_TASK = gql`
  mutation DeleteTask($id: ID!) {
    deleteTask(id: $id)
  }
`;

// ============ TIME BLOCK MUTATIONS ============

export const CREATE_TIME_BLOCK = gql`
  mutation CreateTimeBlock($input: CreateTimeBlockInput!) {
    createTimeBlock(input: $input) {
      ...TimeBlockFields
    }
  }
  ${TIME_BLOCK_FIELDS}
`;

export const MOVE_TIME_BLOCK = gql`
  mutation MoveTimeBlock($id: ID!, $newStart: DateTime!) {
    moveTimeBlock(id: $id, newStart: $newStart) {
      ...TimeBlockFields
    }
  }
  ${TIME_BLOCK_FIELDS}
`;

export const DELETE_TIME_BLOCK = gql`
  mutation DeleteTimeBlock($id: ID!) {
    deleteTimeBlock(id: $id)
  }
`;

// ============ TIMER MUTATIONS ============

export const START_TIMER = gql`
  mutation StartTimer($subjectId: ID) {
    startTimer(subjectId: $subjectId) {
      isRunning
      subjectId
      startedAt
      elapsedMinutes
    }
  }
`;

export const STOP_TIMER = gql`
  mutation StopTimer {
    stopTimer {
      id
      subjectId
      startedAt
      endedAt
      durationMinutes
      isDeepWork
    }
  }
`;

// ============ GOAL MUTATIONS ============

export const CREATE_GOAL = gql`
  mutation CreateGoal($input: CreateGoalInput!) {
    createGoal(input: $input) {
      ...GoalFields
    }
  }
  ${GOAL_FIELDS}
`;

export const UPDATE_GOAL_PROGRESS = gql`
  mutation UpdateGoalProgress($id: ID!, $progress: Float!) {
    updateGoalProgress(id: $id, progress: $progress) {
      ...GoalFields
    }
  }
  ${GOAL_FIELDS}
`;

// ============ CHAT MUTATIONS ============

export const SEND_CHAT_MESSAGE = gql`
  mutation SendChatMessage($message: String!) {
    sendChatMessage(message: $message) {
      message
      suggestions
      toolCalls
    }
  }
`;

// ============ ASSISTANT SETTINGS MUTATIONS ============

export const UPDATE_ASSISTANT_SETTINGS = gql`
  mutation UpdateAssistantSettings($input: UpdateAssistantSettingsInput!) {
    updateAssistantSettings(input: $input) {
      baseUrl
      model
    }
  }
`;

// ============ SUBJECT MUTATIONS ============

export const CREATE_SUBJECT = gql`
  mutation CreateSubject($input: CreateSubjectInput!) {
    createSubject(input: $input) {
      id
      code
      name
      color
      createdAt
    }
  }
`;

export const UPDATE_SUBJECT = gql`
  mutation UpdateSubject($id: ID!, $input: UpdateSubjectInput!) {
    updateSubject(id: $id, input: $input) {
      id
      code
      name
      color
      createdAt
    }
  }
`;

export const DELETE_SUBJECT = gql`
  mutation DeleteSubject($id: ID!) {
    deleteSubject(id: $id)
  }
`;


// ============ NOTIFICATION MUTATIONS ============

export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($id: ID!) {
    markNotificationRead(id: $id) {
      id
      isRead
    }
  }
`;

export const MARK_ALL_NOTIFICATIONS_READ = gql`
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead
  }
`;
