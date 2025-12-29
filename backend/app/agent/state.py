"""
Agent state management for LangGraph.

This module defines the state structure used by the LangGraph agent
for managing conversation context and tool execution.

Requirements: 6.1, 6.2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Sequence

from langchain_core.messages import BaseMessage


@dataclass
class AgentContext:
    """Context information for the agent."""

    current_task_id: Optional[str] = None
    current_task_title: Optional[str] = None
    active_subject: Optional[str] = None
    today_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    preferences: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_task_id": self.current_task_id,
            "current_task_title": self.current_task_title,
            "active_subject": self.active_subject,
            "today_date": self.today_date,
            "preferences": self.preferences,
        }


@dataclass
class AgentState:
    """
    State for the LangGraph agent.

    This state is passed between nodes in the agent graph and
    maintains conversation history and context.
    """

    messages: Sequence[BaseMessage] = field(default_factory=list)
    user_id: str = ""
    context: AgentContext = field(default_factory=AgentContext)
    tool_calls_made: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "messages": [m.dict() for m in self.messages],
            "user_id": self.user_id,
            "context": self.context.to_dict(),
            "tool_calls_made": self.tool_calls_made,
            "error": self.error,
        }
