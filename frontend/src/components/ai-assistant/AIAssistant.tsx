'use client';

import React from 'react';
import { AIAssistantPanel, AIAssistantPanelSection } from './AIAssistantPanel';
import { ChatMessageList, TypingIndicator } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ContextCard } from './ContextCard';
import { SuggestionCardList } from './SuggestionCard';
import { useChat } from '@/lib/hooks/useChat';
import type { Task, Suggestion } from '@/lib/types';

export interface AIAssistantProps {
  /** Currently active task for context */
  activeTask?: Task | null;
  /** Context tags */
  contextTags?: string[];
  /** Initial suggestions to display */
  initialSuggestions?: Suggestion[];
  /** Whether the panel starts collapsed */
  defaultCollapsed?: boolean;
  /** Callback when panel is toggled */
  onToggle?: (isCollapsed: boolean) => void;
  /** API endpoint for chat */
  chatEndpoint?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * AIAssistant - Complete AI Assistant panel with chat, context, and suggestions
 * Combines all AI assistant sub-components into a cohesive interface
 */
export function AIAssistant({
  activeTask = null,
  contextTags = [],
  initialSuggestions = [],
  defaultCollapsed = false,
  onToggle,
  chatEndpoint = '/api/chat',
  className = '',
}: AIAssistantProps) {
  const {
    messages,
    isLoading,
    sendMessage,
  } = useChat({ endpoint: chatEndpoint });

  // Extract suggestions from the latest AI message
  const latestAiMessage = [...messages].reverse().find((m) => !m.isUser);
  const currentSuggestions = latestAiMessage?.suggestions || initialSuggestions;

  return (
    <AIAssistantPanel
      defaultCollapsed={defaultCollapsed}
      onToggle={onToggle}
      className={className}
    >
      {/* Context Section */}
      <AIAssistantPanelSection className="border-b border-sand-200/50">
        <ContextCard
          activeTask={activeTask}
          tags={contextTags}
        />
      </AIAssistantPanelSection>

      {/* Suggestions Section (if any) */}
      {currentSuggestions.length > 0 && (
        <AIAssistantPanelSection 
          title="Suggestions"
          className="border-b border-sand-200/50"
        >
          <SuggestionCardList suggestions={currentSuggestions} />
        </AIAssistantPanelSection>
      )}

      {/* Chat Messages */}
      <ChatMessageList messages={messages} />

      {/* Typing Indicator */}
      {isLoading && (
        <div className="px-4 pb-2">
          <TypingIndicator />
        </div>
      )}

      {/* Chat Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
        placeholder={isLoading ? 'AESA is thinking...' : 'Ask AESA anything...'}
      />
    </AIAssistantPanel>
  );
}

/**
 * AIAssistantMinimal - Simplified version without context card
 * Useful for standalone chat interfaces
 */
export interface AIAssistantMinimalProps {
  /** Whether the panel starts collapsed */
  defaultCollapsed?: boolean;
  /** Callback when panel is toggled */
  onToggle?: (isCollapsed: boolean) => void;
  /** API endpoint for chat */
  chatEndpoint?: string;
  /** Additional CSS classes */
  className?: string;
}

export function AIAssistantMinimal({
  defaultCollapsed = false,
  onToggle,
  chatEndpoint = '/api/chat',
  className = '',
}: AIAssistantMinimalProps) {
  const {
    messages,
    isLoading,
    sendMessage,
  } = useChat({ endpoint: chatEndpoint });

  return (
    <AIAssistantPanel
      defaultCollapsed={defaultCollapsed}
      onToggle={onToggle}
      className={className}
    >
      {/* Chat Messages */}
      <ChatMessageList messages={messages} />

      {/* Typing Indicator */}
      {isLoading && (
        <div className="px-4 pb-2">
          <TypingIndicator />
        </div>
      )}

      {/* Chat Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
        placeholder={isLoading ? 'AESA is thinking...' : 'Ask AESA anything...'}
      />
    </AIAssistantPanel>
  );
}
