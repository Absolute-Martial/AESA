"""
Timeline REST API endpoints.

Implements:
- GET /api/timeline/today - Today's timeline
- GET /api/timeline/{date} - Timeline for specific date
- POST /api/timeline/blocks - Create time block
- PATCH /api/timeline/blocks/{id} - Move/update time block
- DELETE /api/timeline/blocks/{id} - Delete time block

Requirements: 5.1
"""

from datetime import datetime, date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, TimeBlock
from app.scheduler.service import SchedulerService
from app.api.schemas import (
    TimelineResponse,
    TimeBlockSchema,
    TimeBlockResponse,
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    GapSchema,
)
from app.api.schedule import get_current_user

router = APIRouter(prefix="/timeline", tags=["timeline"])


def _time_block_to_schema(block: TimeBlock) -> TimeBlockSchema:
    """Convert TimeBlock model to schema."""
    return TimeBlockSchema(
        id=block.id,
        title=block.title,
        block_type=block.block_type,
        start_time=block.start_time,
        end_time=block.end_time,
        is_fixed=block.is_fixed,
        task_id=block.task_id,
        metadata=block.block_metadata,
    )


@router.get("/today", response_model=TimelineResponse)
async def get_today_timeline(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimelineResponse:
    """
    Get today's timeline with all blocks and gaps.

    Returns the optimized daily timeline including:
    - All scheduled time blocks
    - Available gaps for scheduling
    """
    service = SchedulerService(db)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    schedule = await service.get_day_schedule(user.id, today)

    # Also get user-created time blocks from database
    tomorrow = (
        today + datetime.timedelta(days=1)
        if hasattr(datetime, "timedelta")
        else today.replace(day=today.day + 1)
    )
    from datetime import timedelta

    tomorrow = today + timedelta(days=1)

    result = await db.execute(
        select(TimeBlock)
        .where(
            and_(
                TimeBlock.user_id == user.id,
                TimeBlock.start_time >= today,
                TimeBlock.start_time < tomorrow,
            )
        )
        .order_by(TimeBlock.start_time)
    )
    user_blocks = result.scalars().all()

    # Combine system blocks with user blocks
    all_blocks = [
        TimeBlockSchema(
            title=getattr(b, "title", b.block_type),
            block_type=b.block_type,
            start_time=b.start_time,
            end_time=b.end_time,
            is_fixed=b.is_fixed,
        )
        for b in schedule.blocks
    ]

    # Add user-created blocks
    for block in user_blocks:
        all_blocks.append(_time_block_to_schema(block))

    # Sort by start time
    all_blocks.sort(key=lambda b: b.start_time)

    return TimelineResponse(
        success=True,
        date=today.date(),
        blocks=all_blocks,
        gaps=[
            GapSchema(
                start_time=g.start_time,
                end_time=g.end_time,
                duration_minutes=g.duration_minutes,
                gap_type=g.gap_type.value,
                suggested_task_type=g.suggested_task_type,
                is_deep_work_opportunity=g.is_deep_work_opportunity,
            )
            for g in schedule.gaps
        ],
    )


@router.get("/{target_date}", response_model=TimelineResponse)
async def get_timeline_by_date(
    target_date: date = Path(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimelineResponse:
    """
    Get timeline for a specific date.

    Returns the timeline for the specified date including
    all blocks and available gaps.
    """
    from datetime import timedelta

    service = SchedulerService(db)
    target_dt = datetime.combine(target_date, datetime.min.time())

    schedule = await service.get_day_schedule(user.id, target_dt)

    # Get user-created time blocks
    next_day = target_dt + timedelta(days=1)

    result = await db.execute(
        select(TimeBlock)
        .where(
            and_(
                TimeBlock.user_id == user.id,
                TimeBlock.start_time >= target_dt,
                TimeBlock.start_time < next_day,
            )
        )
        .order_by(TimeBlock.start_time)
    )
    user_blocks = result.scalars().all()

    # Combine blocks
    all_blocks = [
        TimeBlockSchema(
            title=getattr(b, "title", b.block_type),
            block_type=b.block_type,
            start_time=b.start_time,
            end_time=b.end_time,
            is_fixed=b.is_fixed,
        )
        for b in schedule.blocks
    ]

    for block in user_blocks:
        all_blocks.append(_time_block_to_schema(block))

    all_blocks.sort(key=lambda b: b.start_time)

    return TimelineResponse(
        success=True,
        date=target_date,
        blocks=all_blocks,
        gaps=[
            GapSchema(
                start_time=g.start_time,
                end_time=g.end_time,
                duration_minutes=g.duration_minutes,
                gap_type=g.gap_type.value,
                suggested_task_type=g.suggested_task_type,
                is_deep_work_opportunity=g.is_deep_work_opportunity,
            )
            for g in schedule.gaps
        ],
    )


@router.post("/blocks", response_model=TimeBlockResponse)
async def create_time_block(
    request: CreateTimeBlockRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimeBlockResponse:
    """
    Create a new time block in the schedule.

    Creates a scheduled activity block with the specified
    time range and properties.
    """
    # Validate time range
    if request.end_time <= request.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time",
        )

    # Check for overlapping blocks
    result = await db.execute(
        select(TimeBlock).where(
            and_(
                TimeBlock.user_id == user.id,
                TimeBlock.start_time < request.end_time,
                TimeBlock.end_time > request.start_time,
            )
        )
    )
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Time block overlaps with existing block: {existing.title}",
        )

    # Create the block
    block = TimeBlock(
        user_id=user.id,
        title=request.title,
        block_type=request.block_type,
        start_time=request.start_time,
        end_time=request.end_time,
        is_fixed=request.is_fixed,
        task_id=request.task_id,
        block_metadata=request.metadata,
    )

    db.add(block)
    await db.commit()
    await db.refresh(block)

    return TimeBlockResponse(
        success=True,
        block=_time_block_to_schema(block),
    )


@router.patch("/blocks/{block_id}", response_model=TimeBlockResponse)
async def update_time_block(
    block_id: UUID = Path(..., description="Time block ID"),
    request: UpdateTimeBlockRequest = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimeBlockResponse:
    """
    Update or move a time block.

    Updates the specified time block's properties or moves it
    to a new time slot.
    """
    # Get the block
    result = await db.execute(
        select(TimeBlock).where(
            and_(
                TimeBlock.id == block_id,
                TimeBlock.user_id == user.id,
            )
        )
    )
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(
            status_code=404,
            detail="Time block not found",
        )

    if block.is_fixed:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify fixed time blocks",
        )

    # Update fields
    if request:
        update_data = request.model_dump(exclude_unset=True)

        # Validate time range if both times are being updated
        new_start = update_data.get("start_time", block.start_time)
        new_end = update_data.get("end_time", block.end_time)

        if new_end <= new_start:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time",
            )

        # Check for overlaps with other blocks
        if "start_time" in update_data or "end_time" in update_data:
            result = await db.execute(
                select(TimeBlock).where(
                    and_(
                        TimeBlock.user_id == user.id,
                        TimeBlock.id != block_id,
                        TimeBlock.start_time < new_end,
                        TimeBlock.end_time > new_start,
                    )
                )
            )
            existing = result.scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"New time range overlaps with: {existing.title}",
                )

        for field, value in update_data.items():
            if value is not None:
                if field == "metadata":
                    setattr(block, "block_metadata", value)
                else:
                    setattr(block, field, value)

    await db.commit()
    await db.refresh(block)

    return TimeBlockResponse(
        success=True,
        block=_time_block_to_schema(block),
    )


@router.delete("/blocks/{block_id}")
async def delete_time_block(
    block_id: UUID = Path(..., description="Time block ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Delete a time block from the schedule.

    Removes the specified time block. Fixed blocks cannot be deleted.
    """
    # Get the block
    result = await db.execute(
        select(TimeBlock).where(
            and_(
                TimeBlock.id == block_id,
                TimeBlock.user_id == user.id,
            )
        )
    )
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(
            status_code=404,
            detail="Time block not found",
        )

    if block.is_fixed:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete fixed time blocks",
        )

    await db.delete(block)
    await db.commit()

    return {"success": True, "message": "Time block deleted"}
