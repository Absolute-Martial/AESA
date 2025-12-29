"""
Smart planning tools for the AI agent.

These tools provide intelligent planning capabilities including
backward planning from deadlines, spaced repetition scheduling,
and deep work slot identification.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from langchain_core.tools import tool

from app.models.time_block import TimeBlock
from app.scheduler.service import SchedulerService
from app.scheduler.gaps import GapType
from app.tools.schedule_tools import get_tool_context

logger = logging.getLogger(__name__)


# Spaced repetition intervals in days (based on forgetting curve)
SPACED_REPETITION_INTERVALS = [1, 3, 7, 14, 30]


@tool
async def backward_plan(
    goal: str,
    deadline: str,
    estimated_hours: float,
) -> dict[str, Any]:
    """
    Create a backward plan from a deadline.

    This tool calculates the available days until the deadline,
    finds available gaps, and distributes work with increasing
    intensity as the deadline approaches.

    Args:
        goal: What needs to be accomplished (e.g., "Complete Chapter 5 of Calculus")
        deadline: Deadline in YYYY-MM-DD format (e.g., "2025-01-15")
        estimated_hours: Total hours needed to complete the goal

    Returns:
        Plan with distributed time blocks leading up to deadline
    """
    user_id, db = get_tool_context()

    try:
        # Parse deadline
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate days available
        days_available = (deadline_date - today).days

        if days_available <= 0:
            return {
                "success": False,
                "error": "Deadline has already passed or is today",
            }

        # Convert hours to minutes
        total_minutes = int(estimated_hours * 60)

        # Get schedule service
        service = SchedulerService(db)

        # Find available gaps for each day
        available_slots = []
        for day_offset in range(days_available):
            date = today + timedelta(days=day_offset)
            schedule = await service.get_day_schedule(UUID(user_id), date)

            # Collect deep work and standard gaps
            for gap in schedule.gaps:
                if gap.gap_type in [GapType.DEEP_WORK, GapType.STANDARD]:
                    available_slots.append(
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "start_time": gap.start_time.isoformat(),
                            "duration_minutes": gap.duration_minutes,
                            "day_offset": day_offset,
                        }
                    )

        if not available_slots:
            return {
                "success": False,
                "error": "No available time slots found before deadline",
            }

        # Calculate total available minutes
        total_available = sum(s["duration_minutes"] for s in available_slots)

        if total_available < total_minutes:
            return {
                "success": False,
                "error": f"Not enough time available. Need {estimated_hours}h but only {total_available / 60:.1f}h available",
                "available_hours": total_available / 60,
            }

        # Distribute work with increasing intensity near deadline
        # Use a simple algorithm: allocate more time to later days
        planned_blocks = []
        remaining_minutes = total_minutes

        # Sort slots by date (later dates first for intensity)
        sorted_slots = sorted(
            available_slots, key=lambda x: x["day_offset"], reverse=True
        )

        for slot in sorted_slots:
            if remaining_minutes <= 0:
                break

            # Allocate time (up to slot duration or remaining)
            allocate = min(
                int(slot["duration_minutes"] * 0.8),  # Use 80% of slot
                remaining_minutes,
                90,  # Max 90 minutes per block
            )

            if allocate >= 30:  # Minimum 30 minutes
                planned_blocks.append(
                    {
                        "date": slot["date"],
                        "start_time": slot["start_time"],
                        "duration_minutes": allocate,
                        "title": f"{goal} - Session",
                    }
                )
                remaining_minutes -= allocate

        # Sort by date for presentation
        planned_blocks.sort(key=lambda x: x["date"])

        return {
            "success": True,
            "goal": goal,
            "deadline": deadline,
            "days_available": days_available,
            "total_hours_needed": estimated_hours,
            "total_hours_planned": (total_minutes - remaining_minutes) / 60,
            "planned_blocks": planned_blocks,
            "message": f"Created {len(planned_blocks)} study sessions for '{goal}'",
        }

    except Exception as e:
        logger.error(f"Failed to create backward plan: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def schedule_chapter_revision(
    subject_code: str,
    chapter_name: str,
    completion_date: str,
) -> dict[str, Any]:
    """
    Schedule spaced repetition for a completed chapter.

    This tool creates revision blocks at optimal intervals based on
    the forgetting curve: 1, 3, 7, 14, and 30 days after completion.

    Args:
        subject_code: Subject code (e.g., "MATH101")
        chapter_name: Name of the chapter (e.g., "Integration Techniques")
        completion_date: When the chapter was completed in YYYY-MM-DD format

    Returns:
        Scheduled revision blocks at spaced intervals
    """
    user_id, db = get_tool_context()

    try:
        # Parse completion date
        completed = datetime.strptime(completion_date, "%Y-%m-%d")

        # Get schedule service
        service = SchedulerService(db)

        # Schedule revisions at each interval
        scheduled_revisions = []

        for interval in SPACED_REPETITION_INTERVALS:
            revision_date = completed + timedelta(days=interval)

            # Skip if date is in the past
            if revision_date.date() < datetime.now().date():
                continue

            # Find a suitable gap on that day
            schedule = await service.get_day_schedule(UUID(user_id), revision_date)

            # Look for a standard or micro gap (revision is usually quick)
            suitable_gap = None
            for gap in schedule.gaps:
                if gap.duration_minutes >= 20:  # At least 20 minutes for revision
                    suitable_gap = gap
                    break

            if suitable_gap:
                # Create the revision block
                revision_title = (
                    f"Review: {subject_code} - {chapter_name} (Day {interval})"
                )
                duration = min(
                    30, suitable_gap.duration_minutes
                )  # 30 min max for revision

                time_block = TimeBlock(
                    user_id=UUID(user_id),
                    title=revision_title,
                    block_type="revision",
                    start_time=suitable_gap.start_time,
                    end_time=suitable_gap.start_time + timedelta(minutes=duration),
                    is_fixed=False,
                )

                db.add(time_block)

                scheduled_revisions.append(
                    {
                        "date": revision_date.strftime("%Y-%m-%d"),
                        "interval_days": interval,
                        "start_time": suitable_gap.start_time.isoformat(),
                        "duration_minutes": duration,
                        "title": revision_title,
                    }
                )

        await db.flush()

        return {
            "success": True,
            "subject_code": subject_code,
            "chapter_name": chapter_name,
            "completion_date": completion_date,
            "revisions_scheduled": len(scheduled_revisions),
            "revision_blocks": scheduled_revisions,
            "message": f"Scheduled {len(scheduled_revisions)} revision sessions using spaced repetition",
        }

    except Exception as e:
        logger.error(f"Failed to schedule chapter revision: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def schedule_event_prep(
    event_name: str,
    event_date: str,
    prep_hours: float,
    event_type: str = "exam",
) -> dict[str, Any]:
    """
    Schedule preparation blocks for an upcoming event.

    This tool automatically creates study blocks leading up to
    an exam, test, or other important event.

    Args:
        event_name: Name of the event (e.g., "Calculus Midterm")
        event_date: Date of the event in YYYY-MM-DD format
        prep_hours: Total hours of preparation needed
        event_type: Type of event - "exam", "test", "quiz", "presentation"

    Returns:
        Scheduled preparation blocks
    """
    user_id, db = get_tool_context()

    try:
        # Parse event date
        event = datetime.strptime(event_date, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        days_until = (event - today).days

        if days_until <= 0:
            return {
                "success": False,
                "error": "Event date has already passed or is today",
            }

        # Determine prep strategy based on event type
        if event_type == "exam":
            # Start earlier, more intensive
            start_days_before = min(days_until, 7)
        elif event_type == "test":
            start_days_before = min(days_until, 5)
        elif event_type == "quiz":
            start_days_before = min(days_until, 3)
        else:
            start_days_before = min(days_until, 4)

        # Get schedule service
        service = SchedulerService(db)

        # Find available slots
        total_minutes = int(prep_hours * 60)
        scheduled_blocks = []
        remaining_minutes = total_minutes

        for day_offset in range(start_days_before):
            if remaining_minutes <= 0:
                break

            date = event - timedelta(days=day_offset + 1)
            schedule = await service.get_day_schedule(UUID(user_id), date)

            # Prioritize deep work slots for exam prep
            for gap in schedule.gaps:
                if remaining_minutes <= 0:
                    break

                if gap.gap_type == GapType.DEEP_WORK or gap.duration_minutes >= 45:
                    # Allocate time
                    allocate = min(
                        gap.duration_minutes - 15,  # Leave buffer
                        remaining_minutes,
                        90,  # Max 90 minutes
                    )

                    if allocate >= 30:
                        prep_title = f"Prep: {event_name} ({event_type.title()})"

                        time_block = TimeBlock(
                            user_id=UUID(user_id),
                            title=prep_title,
                            block_type="study",
                            start_time=gap.start_time,
                            end_time=gap.start_time + timedelta(minutes=allocate),
                            is_fixed=False,
                        )

                        db.add(time_block)

                        scheduled_blocks.append(
                            {
                                "date": date.strftime("%Y-%m-%d"),
                                "days_before_event": day_offset + 1,
                                "start_time": gap.start_time.isoformat(),
                                "duration_minutes": allocate,
                                "title": prep_title,
                            }
                        )

                        remaining_minutes -= allocate

        await db.flush()

        hours_scheduled = (total_minutes - remaining_minutes) / 60

        return {
            "success": True,
            "event_name": event_name,
            "event_date": event_date,
            "event_type": event_type,
            "hours_requested": prep_hours,
            "hours_scheduled": hours_scheduled,
            "blocks_created": len(scheduled_blocks),
            "scheduled_blocks": scheduled_blocks,
            "message": f"Scheduled {hours_scheduled:.1f}h of prep for {event_name}",
        }

    except Exception as e:
        logger.error(f"Failed to schedule event prep: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def allocate_free_time(
    target_date: str,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """
    Intelligently allocate free/relaxation time.

    This tool finds a suitable gap and creates a free time block
    for relaxation, helping maintain work-life balance.

    Args:
        target_date: Date to allocate free time in YYYY-MM-DD format
        duration_minutes: Desired free time duration (default: 30)

    Returns:
        Allocated free time block details
    """
    user_id, db = get_tool_context()

    try:
        # Parse date
        date = datetime.strptime(target_date, "%Y-%m-%d")

        # Get schedule
        service = SchedulerService(db)
        schedule = await service.get_day_schedule(UUID(user_id), date)

        # Find a suitable gap (prefer afternoon/evening for free time)
        suitable_gap = None

        # Sort gaps by start time, prefer later in the day
        sorted_gaps = sorted(schedule.gaps, key=lambda g: g.start_time, reverse=True)

        for gap in sorted_gaps:
            if gap.duration_minutes >= duration_minutes:
                suitable_gap = gap
                break

        if not suitable_gap:
            return {
                "success": False,
                "error": f"No gap of at least {duration_minutes} minutes found on {target_date}",
            }

        # Create free time block
        time_block = TimeBlock(
            user_id=UUID(user_id),
            title="Free Time - Relax & Recharge",
            block_type="free_time",
            start_time=suitable_gap.start_time,
            end_time=suitable_gap.start_time + timedelta(minutes=duration_minutes),
            is_fixed=False,
        )

        db.add(time_block)
        await db.flush()
        await db.refresh(time_block)

        return {
            "success": True,
            "id": str(time_block.id),
            "date": target_date,
            "start_time": time_block.start_time.isoformat(),
            "end_time": time_block.end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "message": f"Allocated {duration_minutes} minutes of free time",
        }

    except Exception as e:
        logger.error(f"Failed to allocate free time: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def find_deep_work_slots(
    target_date: str,
    min_duration_minutes: int = 90,
) -> dict[str, Any]:
    """
    Find available deep work slots (90+ minutes).

    This tool identifies time blocks suitable for deep, focused work
    that requires sustained concentration.

    Args:
        target_date: Date to search in YYYY-MM-DD format
        min_duration_minutes: Minimum slot duration (default: 90)

    Returns:
        List of available deep work time slots
    """
    user_id, db = get_tool_context()

    try:
        # Parse date
        date = datetime.strptime(target_date, "%Y-%m-%d")

        # Get schedule
        service = SchedulerService(db)
        deep_work_gaps = await service.find_deep_work_opportunities(
            UUID(user_id),
            date,
            min_duration_minutes,
        )

        slots = []
        for gap in deep_work_gaps:
            slots.append(
                {
                    "start_time": gap.start_time.isoformat(),
                    "end_time": gap.end_time.isoformat(),
                    "duration_minutes": gap.duration_minutes,
                    "is_ideal": gap.duration_minutes >= 90,
                }
            )

        return {
            "success": True,
            "date": target_date,
            "min_duration_minutes": min_duration_minutes,
            "slots_found": len(slots),
            "slots": slots,
            "total_deep_work_minutes": sum(s["duration_minutes"] for s in slots),
            "message": f"Found {len(slots)} deep work slots on {target_date}",
        }

    except Exception as e:
        logger.error(f"Failed to find deep work slots: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Export all planning tools
PLANNING_TOOLS = [
    backward_plan,
    schedule_chapter_revision,
    schedule_event_prep,
    allocate_free_time,
    find_deep_work_slots,
]
