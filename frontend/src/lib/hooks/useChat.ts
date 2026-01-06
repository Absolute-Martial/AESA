'use client';

import { useState, useCallback } from 'react';
import type { Message, Suggestion } from '@/lib/types';

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface UseChatOptions {
  /** API endpoint for chat */
  endpoint?: string;
  /** Initial messages */
  initialMessages?: Message[];
  /** Callback when a new message is received */
  onMessage?: (message: Message) => void;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
}

export interface UseChatReturn {
  /** Current chat messages */
  messages: Message[];
  /** Whether a message is being sent/processed */
  isLoading: boolean;
  /** Current error message */
  error: string | null;
  /** Send a message to the AI */
  sendMessage: (content: string) => Promise<void>;
  /** Clear all messages */
  clearMessages: () => void;
  /** Clear error state */
  clearError: () => void;
  /** Add a message manually (e.g., for suggestions) */
  addMessage: (message: Message) => void;
}

/**
 * Generate a unique message ID
 */
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * useChat - Custom hook for managing chat state and API communication
 * Connects to the /api/chat endpoint for AI responses
 */
export function useChat({
  endpoint = '/api/chat',
  initialMessages = [],
  onMessage,
  onError,
}: UseChatOptions = {}): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
    onMessage?.(message);
  }, [onMessage]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Create user message
    const userMessage: Message = {
      id: generateMessageId(),
      content: content.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    // Add user message to state
    addMessage(userMessage);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: content }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Request failed with status ${response.status}`);
      }

      const data = await response.json();

      // Create AI response message
      const aiMessage: Message = {
        id: generateMessageId(),
        content: data.response || data.message || 'I received your message.',
        isUser: false,
        timestamp: new Date(),
        suggestions: parseSuggestions(data.suggestions),
      };

      addMessage(aiMessage);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));

      // Add error message from AI
      const errorAiMessage: Message = {
        id: generateMessageId(),
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        isUser: false,
        timestamp: new Date(),
      };
      addMessage(errorAiMessage);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint, addMessage, onError]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    clearError,
    addMessage,
  };
}

/**
 * Parse suggestions from API response
 */
function parseSuggestions(suggestions?: unknown[]): Suggestion[] | undefined {
  if (!Array.isArray(suggestions)) return undefined;

  return suggestions
    .filter((s): s is { text: string; actionLabel: string } => 
      typeof s === 'object' && 
      s !== null && 
      'text' in s && 
      'actionLabel' in s
    )
    .map((s) => ({
      text: s.text,
      actionLabel: s.actionLabel,
      action: () => {
        // Default action - can be overridden by consumer
        console.log('Suggestion action:', s.actionLabel);
      },
    }));
}
