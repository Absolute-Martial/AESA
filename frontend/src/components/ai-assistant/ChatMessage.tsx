'use client';

import React from 'react';
import { Icon } from '../common/Icon';
import type { Message } from '@/lib/types';

export interface ChatMessageProps {
  /** Message data */
  message: Message;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Format timestamp to readable time string
 */
function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/**
 * ChatMessage - Individual message bubble for AI and user messages
 * Styled differently based on sender (AI vs user)
 */
export function ChatMessage({ message, className = '' }: ChatMessageProps) {
  const { content, isUser, timestamp } = message;

  return (
    <div
      className={`
        flex gap-3
        ${isUser ? 'flex-row-reverse' : 'flex-row'}
        ${className}
      `.trim()}
    >
      {/* Avatar */}
      <ChatAvatar isUser={isUser} />

      {/* Message Content */}
      <div
        className={`
          flex flex-col gap-1
          max-w-[75%]
          ${isUser ? 'items-end' : 'items-start'}
        `}
      >
        {/* Message Bubble */}
        <div
          className={`
            px-4 py-3
            rounded-2xl
            text-sm leading-relaxed
            ${isUser
              ? 'bg-primary text-white rounded-br-md'
              : 'bg-sand-100 text-text-main rounded-bl-md'
            }
          `}
        >
          {content}
        </div>

        {/* Timestamp */}
        <span className="text-[10px] text-text-muted px-1">
          {formatTime(timestamp)}
        </span>
      </div>
    </div>
  );
}

/**
 * ChatAvatar - Avatar component for chat messages
 */
interface ChatAvatarProps {
  isUser: boolean;
  className?: string;
}

function ChatAvatar({ isUser, className = '' }: ChatAvatarProps) {
  return (
    <div
      className={`
        flex-shrink-0
        flex items-center justify-center
        w-8 h-8
        rounded-full
        ${isUser
          ? 'bg-sand-200 text-text-main'
          : 'bg-primary/10 text-primary'
        }
        ${className}
      `.trim()}
    >
      <Icon 
        name={isUser ? 'person' : 'smart_toy'} 
        size={16} 
      />
    </div>
  );
}

/**
 * ChatMessageList - Container for chat messages with scroll behavior
 */
export interface ChatMessageListProps {
  /** Array of messages to display */
  messages: Message[];
  /** Additional CSS classes */
  className?: string;
}

export function ChatMessageList({ messages, className = '' }: ChatMessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div
      className={`
        flex-1 
        overflow-y-auto 
        scrollbar-thin
        px-4 py-4
        space-y-4
        ${className}
      `.trim()}
    >
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

/**
 * EmptyState - Shown when there are no messages
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-8">
      <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-3">
        <Icon name="smart_toy" size={24} className="text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-text-main mb-1">
        Hi! I&apos;m AESA
      </h3>
      <p className="text-xs text-text-muted max-w-[200px]">
        Your AI study assistant. Ask me to help schedule tasks, plan revisions, or optimize your day.
      </p>
    </div>
  );
}

/**
 * TypingIndicator - Shows when AI is typing
 */
export function TypingIndicator({ className = '' }: { className?: string }) {
  return (
    <div className={`flex gap-3 ${className}`}>
      <ChatAvatar isUser={false} />
      <div className="bg-sand-100 rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-text-muted/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-text-muted/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-text-muted/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
