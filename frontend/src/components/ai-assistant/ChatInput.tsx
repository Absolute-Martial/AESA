'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Icon } from '../common/Icon';

export interface ChatInputProps {
  /** Callback when message is sent */
  onSend: (message: string) => void;
  /** Whether the input is disabled (e.g., while AI is responding) */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ChatInput - Input field with send button for chat messages
 * Supports Enter to send and Shift+Enter for new lines
 */
export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask AESA anything...',
  className = '',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  }, [message, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  };

  const canSend = message.trim().length > 0 && !disabled;

  return (
    <div className={`border-t border-sand-200/50 p-4 ${className}`}>
      <div className="flex items-end gap-2">
        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={`
              w-full
              py-3 px-4
              bg-sand-50
              border border-sand-200
              rounded-xl
              text-sm text-text-main
              placeholder:text-text-muted
              focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
              resize-none
              transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          className={`
            flex-shrink-0
            flex items-center justify-center
            w-11 h-11
            rounded-xl
            transition-all
            ${canSend
              ? 'bg-primary text-white hover:bg-primary-600 shadow-lg shadow-primary/20'
              : 'bg-sand-100 text-text-muted cursor-not-allowed'
            }
          `}
          aria-label="Send message"
        >
          <Icon name="send" size={20} filled={canSend} />
        </button>
      </div>

      {/* Helper Text */}
      <p className="text-[10px] text-text-muted mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}

/**
 * ChatInputWithState - ChatInput with built-in loading/error state management
 */
export interface ChatInputWithStateProps {
  /** Async function to send message to API */
  onSendMessage: (message: string) => Promise<void>;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
}

export function ChatInputWithState({
  onSendMessage,
  placeholder,
  className = '',
}: ChatInputWithStateProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (message: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await onSendMessage(message);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={className}>
      {error && (
        <div className="px-4 pb-2">
          <div className="flex items-center gap-2 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">
            <Icon name="error" size={14} />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto hover:text-red-700"
            >
              <Icon name="close" size={14} />
            </button>
          </div>
        </div>
      )}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading}
        placeholder={isLoading ? 'AESA is thinking...' : placeholder}
      />
    </div>
  );
}
