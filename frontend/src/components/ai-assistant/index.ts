// AI Assistant Components

// Main composite component
export { AIAssistant, AIAssistantMinimal } from './AIAssistant';
export type { AIAssistantProps, AIAssistantMinimalProps } from './AIAssistant';

// Panel container
export { AIAssistantPanel, AIAssistantPanelSection } from './AIAssistantPanel';
export type { AIAssistantPanelProps, AIAssistantPanelSectionProps } from './AIAssistantPanel';

// Chat components
export { ChatMessage, ChatMessageList, TypingIndicator } from './ChatMessage';
export type { ChatMessageProps, ChatMessageListProps } from './ChatMessage';

// Chat input
export { ChatInput, ChatInputWithState } from './ChatInput';
export type { ChatInputProps, ChatInputWithStateProps } from './ChatInput';

// Context card
export { ContextCard, ContextCardSkeleton } from './ContextCard';
export type { ContextCardProps } from './ContextCard';

// Suggestion components
export { 
  SuggestionCard, 
  SuggestionCardList, 
  SuggestionCardSkeleton,
  QuickAction,
  QuickActionGroup,
} from './SuggestionCard';
export type { 
  SuggestionCardProps, 
  SuggestionCardListProps,
  QuickActionProps,
  QuickActionGroupProps,
} from './SuggestionCard';
