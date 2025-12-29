"""
Gap detection and classification for schedule optimization.

This module identifies available time periods between scheduled activities
and classifies them by duration for appropriate task assignment.

Requirements: 9.3 (Gap identification)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class GapType(str, Enum):
    """Classification of available time gaps."""

    MICRO = "micro"  # < 30 minutes - quick review tasks
    STANDARD = "standard"  # 30-60 minutes - practice problems
    DEEP_WORK = "deep_work"  # > 60 minutes (90+ ideal) - conceptual learning


# Gap duration thresholds in minutes
MICRO_GAP_MAX = 30
STANDARD_GAP_MAX = 60
DEEP_WORK_MIN = 60
DEEP_WORK_IDEAL = 90


@dataclass
class Gap:
    """Represents an available time gap in the schedule."""

    start_time: datetime
    end_time: datetime
    gap_type: GapType
    suggested_task_type: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate gap duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def is_deep_work_opportunity(self) -> bool:
        """Check if this gap is suitable for deep work (90+ minutes)."""
        return self.duration_minutes >= DEEP_WORK_IDEAL

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "type": self.gap_type.value,
            "suggested_task_type": self.suggested_task_type,
            "is_deep_work_opportunity": self.is_deep_work_opportunity,
        }


def classify_gap(duration_minutes: int) -> GapType:
    """
    Classify a gap by its duration.

    Args:
        duration_minutes: Gap duration in minutes

    Returns:
        GapType classification
    """
    if duration_minutes < MICRO_GAP_MAX:
        return GapType.MICRO
    elif duration_minutes <= STANDARD_GAP_MAX:
        return GapType.STANDARD
    else:
        return GapType.DEEP_WORK


def suggest_task_type_for_gap(gap_type: GapType) -> str:
    """
    Suggest appropriate task type for a gap.

    Args:
        gap_type: Type of gap

    Returns:
        Suggested task type string
    """
    suggestions = {
        GapType.MICRO: "revision",  # Quick review tasks
        GapType.STANDARD: "practice",  # Practice problems
        GapType.DEEP_WORK: "study",  # Conceptual learning
    }
    return suggestions.get(gap_type, "study")


@dataclass
class TimeBlock:
    """Represents a scheduled time block for gap detection."""

    start_time: datetime
    end_time: datetime
    is_fixed: bool = False
    block_type: str = ""


def find_gaps(
    blocks: list[TimeBlock],
    day_start: datetime,
    day_end: datetime,
    min_gap_minutes: int = 15,
) -> list[Gap]:
    """
    Find all gaps between scheduled blocks within a day.

    Args:
        blocks: List of scheduled time blocks
        day_start: Start of the active day (e.g., wake time)
        day_end: End of the active day (e.g., sleep time)
        min_gap_minutes: Minimum gap duration to consider

    Returns:
        List of identified gaps sorted by start time
    """
    if not blocks:
        # Entire day is a gap
        duration = int((day_end - day_start).total_seconds() / 60)
        if duration >= min_gap_minutes:
            gap_type = classify_gap(duration)
            return [
                Gap(
                    start_time=day_start,
                    end_time=day_end,
                    gap_type=gap_type,
                    suggested_task_type=suggest_task_type_for_gap(gap_type),
                )
            ]
        return []

    # Sort blocks by start time
    sorted_blocks = sorted(blocks, key=lambda b: b.start_time)

    gaps: list[Gap] = []

    # Check gap before first block
    if sorted_blocks[0].start_time > day_start:
        gap_start = day_start
        gap_end = sorted_blocks[0].start_time
        duration = int((gap_end - gap_start).total_seconds() / 60)

        if duration >= min_gap_minutes:
            gap_type = classify_gap(duration)
            gaps.append(
                Gap(
                    start_time=gap_start,
                    end_time=gap_end,
                    gap_type=gap_type,
                    suggested_task_type=suggest_task_type_for_gap(gap_type),
                )
            )

    # Check gaps between blocks
    for i in range(len(sorted_blocks) - 1):
        current_block = sorted_blocks[i]
        next_block = sorted_blocks[i + 1]

        gap_start = current_block.end_time
        gap_end = next_block.start_time

        if gap_end > gap_start:
            duration = int((gap_end - gap_start).total_seconds() / 60)

            if duration >= min_gap_minutes:
                gap_type = classify_gap(duration)
                gaps.append(
                    Gap(
                        start_time=gap_start,
                        end_time=gap_end,
                        gap_type=gap_type,
                        suggested_task_type=suggest_task_type_for_gap(gap_type),
                    )
                )

    # Check gap after last block
    if sorted_blocks[-1].end_time < day_end:
        gap_start = sorted_blocks[-1].end_time
        gap_end = day_end
        duration = int((gap_end - gap_start).total_seconds() / 60)

        if duration >= min_gap_minutes:
            gap_type = classify_gap(duration)
            gaps.append(
                Gap(
                    start_time=gap_start,
                    end_time=gap_end,
                    gap_type=gap_type,
                    suggested_task_type=suggest_task_type_for_gap(gap_type),
                )
            )

    return gaps


def find_deep_work_slots(
    blocks: list[TimeBlock],
    day_start: datetime,
    day_end: datetime,
    min_duration_minutes: int = DEEP_WORK_IDEAL,
) -> list[Gap]:
    """
    Find available deep work slots (90+ minutes by default).

    Args:
        blocks: List of scheduled time blocks
        day_start: Start of the active day
        day_end: End of the active day
        min_duration_minutes: Minimum duration for deep work

    Returns:
        List of gaps suitable for deep work
    """
    all_gaps = find_gaps(blocks, day_start, day_end)
    return [gap for gap in all_gaps if gap.duration_minutes >= min_duration_minutes]


def merge_overlapping_blocks(blocks: list[TimeBlock]) -> list[TimeBlock]:
    """
    Merge overlapping time blocks into single blocks.

    Args:
        blocks: List of potentially overlapping blocks

    Returns:
        List of non-overlapping blocks
    """
    if not blocks:
        return []

    # Sort by start time
    sorted_blocks = sorted(blocks, key=lambda b: b.start_time)

    merged: list[TimeBlock] = [sorted_blocks[0]]

    for block in sorted_blocks[1:]:
        last = merged[-1]

        # Check if blocks overlap or are adjacent
        if block.start_time <= last.end_time:
            # Extend the last block if needed
            if block.end_time > last.end_time:
                merged[-1] = TimeBlock(
                    start_time=last.start_time,
                    end_time=block.end_time,
                    is_fixed=last.is_fixed or block.is_fixed,
                    block_type=last.block_type,
                )
        else:
            merged.append(block)

    return merged
