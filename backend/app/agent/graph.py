"""
LangGraph agent graph definition.

This module creates the LangGraph agent with state management,
tool calling, and conversation flow.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.6
"""

import logging
from typing import Any, Callable, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.llm import get_llm_client, check_llm_availability, get_fallback_message
from app.agent.state import AgentContext

logger = logging.getLogger(__name__)


def create_agent_node(tools: list[BaseTool], *, llm_base_url: str | None = None, llm_model: str | None = None) -> Callable:
    """
    Create the agent node that processes messages and decides on tool calls.

    Args:
        tools: List of available tools

    Returns:
        Agent node function
    """
    llm = get_llm_client(base_url=llm_base_url, model=llm_model)
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: dict[str, Any]) -> dict[str, Any]:
        """
        Process messages and generate response or tool calls.

        Args:
            state: Current agent state

        Returns:
            Updated state with new messages
        """
        messages = state.get("messages", [])

        try:
            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            # Return fallback message
            fallback = get_fallback_message("")
            return {
                "messages": [AIMessage(content=fallback)],
                "error": str(e),
            }

    return agent_node


def should_continue(state: dict[str, Any]) -> Literal["tools", "end"]:
    """
    Determine if the agent should continue to tools or end.

    Args:
        state: Current agent state

    Returns:
        "tools" if tool calls pending, "end" otherwise
    """
    messages = state.get("messages", [])

    if not messages:
        return "end"

    last_message = messages[-1]

    # Check if there's an error
    if state.get("error"):
        return "end"

    # Check if the last message has tool calls
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "end"


def create_agent_graph(tools: list[BaseTool], *, llm_base_url: str | None = None, llm_model: str | None = None) -> StateGraph:
    """
    Create the LangGraph agent with tools.

    Args:
        tools: List of tools available to the agent

    Returns:
        Compiled StateGraph
    """
    # Create the graph with state schema
    graph = StateGraph(dict)

    # Create nodes
    agent_node = create_agent_node(tools, llm_base_url=llm_base_url, llm_model=llm_model)
    tool_node = ToolNode(tools)

    # Add nodes to graph
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edges
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # Tools always go back to agent
    graph.add_edge("tools", "agent")

    return graph.compile()


class AESAAgent:
    """
    AESA AI Agent using LangGraph.

    This agent handles natural language interactions and tool calling
    for schedule management and smart planning.
    """

    def __init__(self, tools: list[BaseTool], *, llm_base_url: str | None = None, llm_model: str | None = None):
        """
        Initialize the agent with tools.

        Args:
            tools: List of tools available to the agent
        """
        self.tools = tools
        self.graph = create_agent_graph(tools, llm_base_url=llm_base_url, llm_model=llm_model)

    async def process_message(
        self,
        message: str,
        user_id: str,
        context: AgentContext | None = None,
        history: list[BaseMessage] | None = None,
    ) -> dict[str, Any]:
        """
        Process a user message and return the response.

        Args:
            message: User's message
            user_id: User UUID string
            context: Optional agent context
            history: Optional conversation history

        Returns:
            Response dictionary with content and metadata
        """
        # Check LLM availability first
        is_available = await check_llm_availability()
        if not is_available:
            return {
                "content": get_fallback_message(message),
                "tool_calls": [],
                "error": "LLM service unavailable",
            }

        # Build initial state
        messages = list(history) if history else []
        messages.append(HumanMessage(content=message))

        initial_state = {
            "messages": messages,
            "user_id": user_id,
            "context": context.to_dict() if context else {},
            "tool_calls_made": [],
            "error": None,
        }

        try:
            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            # Extract the final response
            final_messages = result.get("messages", [])

            # Find the last AI message
            response_content = ""
            tool_calls = []

            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    response_content = msg.content
                    tool_calls = msg.tool_calls if hasattr(msg, "tool_calls") else []
                    break

            return {
                "content": response_content,
                "tool_calls": tool_calls,
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return {
                "content": get_fallback_message(message),
                "tool_calls": [],
                "error": str(e),
            }
