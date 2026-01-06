"""
AI tools for the AESA agent.

This module exports all tools available to the LangGraph agent
for schedule management, smart planning, and memory operations.

Requirements: 7.1-7.6, 8.1-8.5, 18.1-18.5
"""

from app.tools.schedule_tools import (
    SCHEDULE_TOOLS,
    create_time_block,
    move_time_block,
    delete_time_block,
    get_optimized_schedule,
    get_weekly_timeline,
    reschedule_all,
    set_tool_context,
    get_tool_context,
)

from app.tools.planning_tools import (
    PLANNING_TOOLS,
    backward_plan,
    schedule_chapter_revision,
    schedule_event_prep,
    allocate_free_time,
    find_deep_work_slots,
)

from app.tools.memory_tools import (
    MEMORY_TOOLS,
    save_memory,
    get_memory,
    forget_memory,
    add_guideline,
    list_guidelines,
    deactivate_guideline,
    get_all_memories,
    get_active_guidelines,
)


# All tools combined
ALL_TOOLS = SCHEDULE_TOOLS + PLANNING_TOOLS + MEMORY_TOOLS


__all__ = [
    # Tool collections
    "ALL_TOOLS",
    "SCHEDULE_TOOLS",
    "PLANNING_TOOLS",
    "MEMORY_TOOLS",
    # Schedule tools
    "create_time_block",
    "move_time_block",
    "delete_time_block",
    "get_optimized_schedule",
    "get_weekly_timeline",
    "reschedule_all",
    # Planning tools
    "backward_plan",
    "schedule_chapter_revision",
    "schedule_event_prep",
    "allocate_free_time",
    "find_deep_work_slots",
    # Memory tools
    "save_memory",
    "get_memory",
    "forget_memory",
    "add_guideline",
    "list_guidelines",
    "deactivate_guideline",
    "get_all_memories",
    "get_active_guidelines",
    # Context management
    "set_tool_context",
    "get_tool_context",
]
