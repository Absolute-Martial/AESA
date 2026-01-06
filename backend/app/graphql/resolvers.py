"""GraphQL resolvers for AESA."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from app.api.chat import ChatRequest
from app.core.database import get_db
from app.graphql.assistant_settings_types import AssistantSettings, UpdateAssistantSettingsInput
from app.graphql.types import (
    AnalyticsPeriod,
    ChatResponse,
    CreateGoalInput,
    CreateSubjectInput,
    CreateTaskInput,
    CreateTimeBlockInput,
    UpdateTaskInput,
    DaySchedule,
    DayStats,
    Goal,
    GoalStatusEnum,
    Notification,
    StudyAnalytics,
    StudySession,
    Subject,
    Task,
    TaskFilter,
    TimeBlock,
    TimerStatus,
    TimetableEntry,
    TimetableSlot,
    CreateTimetableSlotInput,
    UpdateTimetableSlotInput,
    TimetableCsvRowInput,
    ImportTimetableCsvInput,
    ImportTimetableResult,
    UpdateSubjectInput,
)
from app.models import AssistantSettings as AssistantSettingsModel
from app.models import Notification as NotificationModel
from app.models import Subject as SubjectModel
from app.models import Task as TaskModel
from app.models import TimeBlock as TimeBlockModel
from app.models import User
from app.models.timetable import KUTimetable
from app.models.study import StudyGoal as GoalModel, ActiveTimer as ActiveTimerModel, StudySession as StudySessionModel
from app.scheduler.service import SchedulerService


# ==========================================================================
# Context helpers
# ==========================================================================


def _get_db_from_context(info: Info) -> AsyncSession:
    db = info.context.get("db")
    if db is None:
        raise RuntimeError("GraphQL context missing db session")
    return db


def _get_user_from_context(info: Info) -> User:
    user = info.context.get("user")
    if user is None:
        raise RuntimeError("GraphQL context missing user")
    return user


async def _get_or_create_default_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(email="dev@example.com", name="Development User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _uuid_to_id(value: UUID) -> strawberry.ID:
    return strawberry.ID(str(value))


def _id_to_uuid(value: strawberry.ID) -> UUID:
    return UUID(str(value))


def _to_gql_subject(subject: SubjectModel) -> Subject:
    return Subject(
        id=_uuid_to_id(subject.id),
        code=subject.code,
        name=subject.name,
        color=getattr(subject, "color", None),
        created_at=getattr(subject, "created_at", None),
    )


def _to_gql_task(task: TaskModel, subject: SubjectModel | None = None) -> Task:
    subj = _to_gql_subject(subject) if subject else None
    return Task(
        id=_uuid_to_id(task.id),
        title=task.title,
        description=getattr(task, "description", None),
        task_type=task.task_type,
        duration_minutes=task.duration_minutes,
        priority=int(getattr(task, "effective_priority", task.priority)),
        deadline=getattr(task, "deadline", None),
        is_completed=bool(task.is_completed),
        completed_at=getattr(task, "completed_at", None),
        subject_id=_uuid_to_id(task.subject_id) if getattr(task, "subject_id", None) else None,
        subject=subj,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _to_gql_time_block(block: Any) -> TimeBlock:
    # SchedulerService returns internal blocks without DB ids. Provide deterministic IDs.
    stable_id = f"{block.start_time.isoformat()}-{block.end_time.isoformat()}-{block.block_type}"
    return TimeBlock(
        id=strawberry.ID(stable_id),
        title=getattr(block, "title", block.block_type),
        block_type=block.block_type,
        start_time=block.start_time,
        end_time=block.end_time,
        is_fixed=bool(getattr(block, "is_fixed", False)),
        task_id=None,
        task=None,
        metadata=None,
        duration_minutes=int((block.end_time - block.start_time).total_seconds() // 60),
    )


def _to_gql_day_stats(schedule: Any) -> DayStats:
    return DayStats(
        total_study_minutes=int(getattr(schedule, "total_study_minutes", 0)),
        deep_work_minutes=int(getattr(schedule, "deep_work_minutes", 0)),
        has_deep_work_opportunity=bool(getattr(schedule, "has_deep_work_opportunity", False)),
        gap_count=len(getattr(schedule, "gaps", []) or []),
        tasks_completed=0,
        energy_level=50,
    )


def _format_hhmm(value: Any) -> str:
    s = str(value)
    # Normalize "HH:MM:SS" -> "HH:MM" for UI consistency
    if len(s) >= 5:
        return s[:5]
    return s


def _to_gql_timetable_slot(slot: KUTimetable, subject: SubjectModel | None = None) -> TimetableSlot:
    subj = _to_gql_subject(subject) if subject else None
    return TimetableSlot(
        id=_uuid_to_id(slot.id),
        subject_id=_uuid_to_id(slot.subject_id),
        subject=subj,
        day_of_week=int(slot.day_of_week),
        start_time=_format_hhmm(slot.start_time),
        end_time=_format_hhmm(slot.end_time),
        room=getattr(slot, "room", None),
        class_type=str(slot.class_type),
    )


def _create_empty_day_schedule(target_date: date) -> DaySchedule:
    return DaySchedule(
        schedule_date=target_date.isoformat(),
        blocks=[],
        gaps=[],
        classes=[],
        stats=DayStats(
            total_study_minutes=0,
            deep_work_minutes=0,
            has_deep_work_opportunity=False,
            gap_count=0,
            tasks_completed=0,
            energy_level=50,
        ),
    )


# ============================================================================
# Query Resolvers
# ============================================================================


@strawberry.type(description="GraphQL Query type with all available queries")
class Query:
    """GraphQL Query type with all available queries."""

    @strawberry.field(description="Get today's schedule with blocks, gaps, and stats")
    async def today_schedule(self, info: Info) -> DaySchedule:
        """Get the schedule for today."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        service = SchedulerService(db)
        today_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        schedule = await service.get_day_schedule(user.id, today_dt)

        return DaySchedule(
            schedule_date=schedule.date.date().isoformat(),
            blocks=[_to_gql_time_block(b) for b in schedule.blocks],
            gaps=[],
            classes=[
                TimetableEntry(
                    subject_code=c.subject_code,
                    subject_name=c.subject_name,
                    class_type=c.class_type.value,
                    start_time=_format_hhmm(c.start_time),
                    end_time=_format_hhmm(c.end_time),
                    room=c.room,
                )
                for c in schedule.classes
            ],
            stats=_to_gql_day_stats(schedule),
        )

    @strawberry.field(description="Get schedule for a week starting from a date")
    async def week_schedule(
        self,
        info: Info,
        start_date: str,
    ) -> list[DaySchedule]:
        """Get the schedule for a week."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        service = SchedulerService(db)
        start = date.fromisoformat(start_date)
        start_dt = datetime.combine(start, datetime.min.time())
        schedules = await service.get_week_schedule(user.id, start_dt)

        days: list[DaySchedule] = []
        for s in schedules:
            days.append(
                DaySchedule(
                    schedule_date=s.date.date().isoformat(),
                    blocks=[_to_gql_time_block(b) for b in s.blocks],
                    gaps=[],
                    classes=[
                        TimetableEntry(
                            subject_code=c.subject_code,
                            subject_name=c.subject_name,
                            class_type=c.class_type.value,
                            start_time=_format_hhmm(c.start_time),
                            end_time=_format_hhmm(c.end_time),
                            room=c.room,
                        )
                        for c in s.classes
                    ],
                    stats=_to_gql_day_stats(s),
                )
            )

        return days

    @strawberry.field(description="Get all tasks with optional filtering")
    async def tasks(
        self,
        info: Info,
        filter: Optional[TaskFilter] = None,
    ) -> list[Task]:
        """Get tasks with optional filtering."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        query = select(TaskModel).where(TaskModel.user_id == user.id)

        if filter is not None:
            if filter.task_type is not None:
                query = query.where(TaskModel.task_type == filter.task_type)
            if filter.is_completed is not None:
                query = query.where(TaskModel.is_completed == filter.is_completed)
            if filter.subject_id is not None:
                query = query.where(TaskModel.subject_id == _id_to_uuid(filter.subject_id))
            if filter.priority_min is not None:
                query = query.where(TaskModel.priority >= filter.priority_min)
            if filter.priority_max is not None:
                query = query.where(TaskModel.priority <= filter.priority_max)

        result = await db.execute(query.order_by(TaskModel.created_at.desc()))
        tasks = result.scalars().all()

        subject_ids = {t.subject_id for t in tasks if t.subject_id}
        subjects_by_id: dict[UUID, SubjectModel] = {}
        if subject_ids:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id.in_(subject_ids)))
            for s in sres.scalars().all():
                subjects_by_id[s.id] = s

        return [_to_gql_task(t, subjects_by_id.get(t.subject_id)) for t in tasks]

    @strawberry.field(description="Get a single task by ID")
    async def task(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> Optional[Task]:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        task_id = _id_to_uuid(id)
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
        task = result.scalar_one_or_none()
        if task is None:
            return None

        subject = None
        if task.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == task.subject_id))
            subject = sres.scalar_one_or_none()

        return _to_gql_task(task, subject)

    @strawberry.field(description="Get all subjects")
    async def subjects(self, info: Info) -> list[Subject]:
        """Get all subjects for the user."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        result = await db.execute(
            select(SubjectModel).where(SubjectModel.user_id == user.id).order_by(SubjectModel.code.asc())
        )
        subjects = result.scalars().all()
        return [_to_gql_subject(s) for s in subjects]

    @strawberry.field(description="Get single subject")
    async def subject(self, info: Info, id: strawberry.ID) -> Optional[Subject]:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject_id = _id_to_uuid(id)
        result = await db.execute(
            select(SubjectModel).where(SubjectModel.id == subject_id, SubjectModel.user_id == user.id)
        )
        subject = result.scalar_one_or_none()
        return _to_gql_subject(subject) if subject else None

    @strawberry.field(description="List timetable slots")
    async def timetable_slots(
        self,
        info: Info,
        day_of_week: Optional[int] = None,
        subject_id: Optional[strawberry.ID] = None,
    ) -> list[TimetableSlot]:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        stmt = (
            select(KUTimetable, SubjectModel)
            .join(SubjectModel, KUTimetable.subject_id == SubjectModel.id)
            .where(KUTimetable.user_id == user.id)
        )

        if day_of_week is not None:
            stmt = stmt.where(KUTimetable.day_of_week == int(day_of_week))

        if subject_id is not None:
            stmt = stmt.where(KUTimetable.subject_id == _id_to_uuid(subject_id))

        stmt = stmt.order_by(KUTimetable.day_of_week.asc(), KUTimetable.start_time.asc())

        result = await db.execute(stmt)
        rows = result.all()
        return [_to_gql_timetable_slot(slot=row[0], subject=row[1]) for row in rows]

    @strawberry.field(description="Get a single timetable slot")
    async def timetable_slot(self, info: Info, id: strawberry.ID) -> Optional[TimetableSlot]:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        slot_id = _id_to_uuid(id)
        result = await db.execute(
            select(KUTimetable, SubjectModel)
            .join(SubjectModel, KUTimetable.subject_id == SubjectModel.id)
            .where(KUTimetable.id == slot_id, KUTimetable.user_id == user.id)
        )
        row = result.first()
        if row is None:
            return None
        return _to_gql_timetable_slot(slot=row[0], subject=row[1])

    @strawberry.field(description="Get goals with optional status filter")
    async def goals(
        self,
        info: Info,
        status: Optional[GoalStatusEnum] = None,
    ) -> list[Goal]:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        query = select(GoalModel).where(GoalModel.user_id == user.id)
        if status is not None:
            query = query.where(GoalModel.status == status.value)

        result = await db.execute(query.order_by(GoalModel.created_at.desc()))
        goals = result.scalars().all()

        return [
            Goal(
                id=_uuid_to_id(g.id),
                title=g.title,
                description=g.description,
                target_value=g.target_value,
                current_value=g.current_value,
                unit=g.unit,
                deadline=g.deadline.isoformat() if g.deadline else None,
                status=g.status,
                progress_percent=g.progress_percent,
                category_id=_uuid_to_id(g.category_id) if g.category_id else None,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
            for g in goals
        ]

    @strawberry.field(description="Get study analytics for a period")
    async def analytics(
        self,
        info: Info,
        period: AnalyticsPeriod,
    ) -> StudyAnalytics:
        """Get study analytics for the specified period."""
        return StudyAnalytics(
            period=period.value,
            total_study_minutes=0,
            deep_work_minutes=0,
            sessions_count=0,
            subjects_studied=0,
            average_session_minutes=0.0,
            longest_session_minutes=0,
            streak_days=0,
        )

    @strawberry.field(description="Get notifications with optional unread filter")
    async def notifications(
        self,
        info: Info,
        unread_only: Optional[bool] = False,
    ) -> list[Notification]:
        """Get notifications for the user."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        query = select(NotificationModel).where(NotificationModel.user_id == user.id)
        if unread_only:
            query = query.where(NotificationModel.is_read.is_(False))

        result = await db.execute(query.order_by(NotificationModel.created_at.desc()))
        notifications = result.scalars().all()

        return [
            Notification(
                id=_uuid_to_id(n.id),
                notification_type=n.type,
                title=n.title,
                message=n.message,
                is_read=n.is_read,
                scheduled_for=n.scheduled_for,
                created_at=n.created_at,
            )
            for n in notifications
        ]

    @strawberry.field(description="Get assistant settings")
    async def assistant_settings(self, info: Info) -> AssistantSettings:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        result = await db.execute(select(AssistantSettingsModel).where(AssistantSettingsModel.user_id == user.id))
        settings = result.scalar_one_or_none()
        if settings is None:
            return AssistantSettings(base_url=None, model=None)

        return AssistantSettings(base_url=settings.base_url, model=settings.model)

    @strawberry.field(description="Get current timer status")
    async def timer_status(self, info: Info) -> Optional[TimerStatus]:
        """Get the current timer status."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        result = await db.execute(select(ActiveTimerModel).where(ActiveTimerModel.user_id == user.id))
        timer = result.scalar_one_or_none()
        if timer is None:
            return TimerStatus(
                is_running=False,
                subject_id=None,
                subject=None,
                started_at=None,
                elapsed_minutes=0,
            )

        subject = None
        if timer.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == timer.subject_id))
            sm = sres.scalar_one_or_none()
            if sm is not None:
                subject = _to_gql_subject(sm)

        return TimerStatus(
            is_running=True,
            subject_id=_uuid_to_id(timer.subject_id) if timer.subject_id else None,
            subject=subject,
            started_at=timer.started_at,
            elapsed_minutes=timer.elapsed_minutes,
        )


# ============================================================================
# Mutation Resolvers
# ============================================================================


@strawberry.type(description="GraphQL Mutation type with all available mutations")
class Mutation:
    """GraphQL Mutation type with all available mutations."""

    @strawberry.mutation(description="Update assistant settings")
    async def update_assistant_settings(
        self,
        info: Info,
        input: UpdateAssistantSettingsInput,
    ) -> AssistantSettings:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        result = await db.execute(select(AssistantSettingsModel).where(AssistantSettingsModel.user_id == user.id))
        settings = result.scalar_one_or_none()

        if settings is None:
            settings = AssistantSettingsModel(user_id=user.id)
            db.add(settings)

        if input.base_url is not None:
            settings.base_url = input.base_url
        if input.model is not None:
            settings.model = input.model

        db.add(settings)
        await db.flush()
        await db.refresh(settings)

        return AssistantSettings(base_url=settings.base_url, model=settings.model)

    @strawberry.mutation(description="Create a new subject")
    async def create_subject(self, info: Info, input: CreateSubjectInput) -> Subject:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject = SubjectModel(
            user_id=user.id,
            code=input.code,
            name=input.name,
            color=input.color,
        )
        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return _to_gql_subject(subject)

    @strawberry.mutation(description="Update a subject")
    async def update_subject(self, info: Info, id: strawberry.ID, input: UpdateSubjectInput) -> Subject:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject_id = _id_to_uuid(id)
        result = await db.execute(
            select(SubjectModel).where(SubjectModel.id == subject_id, SubjectModel.user_id == user.id)
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            raise ValueError("Subject not found")

        if input.code is not None:
            subject.code = input.code
        if input.name is not None:
            subject.name = input.name
        if input.color is not None:
            subject.color = input.color

        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return _to_gql_subject(subject)

    @strawberry.mutation(description="Delete a subject")
    async def delete_subject(self, info: Info, id: strawberry.ID) -> bool:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject_id = _id_to_uuid(id)
        result = await db.execute(
            select(SubjectModel).where(SubjectModel.id == subject_id, SubjectModel.user_id == user.id)
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            return False

        await db.delete(subject)
        await db.flush()
        return True

    @strawberry.mutation(description="Create a timetable slot")
    async def create_timetable_slot(self, info: Info, input: CreateTimetableSlotInput) -> TimetableSlot:
        from datetime import time as _time
        from app.models.enums import ClassType

        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject_uuid = _id_to_uuid(input.subject_id)
        sres = await db.execute(select(SubjectModel).where(SubjectModel.id == subject_uuid, SubjectModel.user_id == user.id))
        subject = sres.scalar_one_or_none()
        if subject is None:
            raise ValueError("Subject not found")

        if input.day_of_week < 0 or input.day_of_week > 6:
            raise ValueError("day_of_week must be between 0 and 6")

        start_t = _time.fromisoformat(input.start_time)
        end_t = _time.fromisoformat(input.end_time)
        if start_t >= end_t:
            raise ValueError("start_time must be before end_time")

        if input.class_type not in {ClassType.LECTURE.value, ClassType.LAB.value}:
            raise ValueError("class_type must be lecture or lab")

        slot = KUTimetable(
            user_id=user.id,
            subject_id=subject_uuid,
            day_of_week=int(input.day_of_week),
            start_time=start_t,
            end_time=end_t,
            room=input.room,
            class_type=input.class_type,
        )
        db.add(slot)
        await db.flush()
        await db.refresh(slot)

        return _to_gql_timetable_slot(slot, subject)

    @strawberry.mutation(description="Update a timetable slot")
    async def update_timetable_slot(
        self,
        info: Info,
        id: strawberry.ID,
        input: UpdateTimetableSlotInput,
    ) -> TimetableSlot:
        from datetime import time as _time
        from app.models.enums import ClassType

        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        slot_id = _id_to_uuid(id)
        result = await db.execute(select(KUTimetable).where(KUTimetable.id == slot_id, KUTimetable.user_id == user.id))
        slot = result.scalar_one_or_none()
        if slot is None:
            raise ValueError("Timetable slot not found")

        subject = None
        if input.subject_id is not None:
            subject_uuid = _id_to_uuid(input.subject_id)
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == subject_uuid, SubjectModel.user_id == user.id))
            subject = sres.scalar_one_or_none()
            if subject is None:
                raise ValueError("Subject not found")
            slot.subject_id = subject_uuid

        if input.day_of_week is not None:
            if input.day_of_week < 0 or input.day_of_week > 6:
                raise ValueError("day_of_week must be between 0 and 6")
            slot.day_of_week = int(input.day_of_week)

        if input.start_time is not None:
            slot.start_time = _time.fromisoformat(input.start_time)

        if input.end_time is not None:
            slot.end_time = _time.fromisoformat(input.end_time)

        if slot.start_time >= slot.end_time:
            raise ValueError("start_time must be before end_time")

        if input.room is not None:
            slot.room = input.room

        if input.class_type is not None:
            if input.class_type not in {ClassType.LECTURE.value, ClassType.LAB.value}:
                raise ValueError("class_type must be lecture or lab")
            slot.class_type = input.class_type

        db.add(slot)
        await db.flush()
        await db.refresh(slot)

        if subject is None:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == slot.subject_id))
            subject = sres.scalar_one_or_none()

        return _to_gql_timetable_slot(slot, subject)

    @strawberry.mutation(description="Delete a timetable slot")
    async def delete_timetable_slot(self, info: Info, id: strawberry.ID) -> bool:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        slot_id = _id_to_uuid(id)
        result = await db.execute(select(KUTimetable).where(KUTimetable.id == slot_id, KUTimetable.user_id == user.id))
        slot = result.scalar_one_or_none()
        if slot is None:
            return False

        await db.delete(slot)
        await db.flush()
        return True

    @strawberry.mutation(description="Import timetable rows from parsed CSV")
    async def import_timetable_csv(self, info: Info, input: ImportTimetableCsvInput) -> ImportTimetableResult:
        from datetime import time as _time
        from app.models.enums import ClassType

        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        mode = (input.mode or "REPLACE").upper()
        if mode not in {"REPLACE", "MERGE"}:
            raise ValueError("mode must be REPLACE or MERGE")

        # Map subject_code -> SubjectModel for the user
        sres = await db.execute(select(SubjectModel).where(SubjectModel.user_id == user.id))
        subjects = sres.scalars().all()
        by_code = {s.code.upper(): s for s in subjects}

        if mode == "REPLACE":
            # Delete all existing timetable slots for user
            existing = await db.execute(select(KUTimetable).where(KUTimetable.user_id == user.id))
            for slot in existing.scalars().all():
                await db.delete(slot)
            await db.flush()

        created = 0
        skipped = 0
        errors: list[str] = []

        for idx, row in enumerate(input.rows):
            try:
                code = row.subject_code.strip().upper()
                subj = by_code.get(code)
                if subj is None:
                    raise ValueError(f"Unknown subject_code: {code}")

                if row.day_of_week < 0 or row.day_of_week > 6:
                    raise ValueError("day_of_week must be between 0 and 6")

                start_t = _time.fromisoformat(row.start_time)
                end_t = _time.fromisoformat(row.end_time)
                if start_t >= end_t:
                    raise ValueError("start_time must be before end_time")

                class_type = (row.class_type or ClassType.LECTURE.value).strip().lower()
                if class_type not in {ClassType.LECTURE.value, ClassType.LAB.value}:
                    raise ValueError("class_type must be lecture or lab")

                slot = KUTimetable(
                    user_id=user.id,
                    subject_id=subj.id,
                    day_of_week=int(row.day_of_week),
                    start_time=start_t,
                    end_time=end_t,
                    room=(row.room.strip() if row.room else None),
                    class_type=class_type,
                )
                db.add(slot)
                created += 1
            except Exception as e:
                skipped += 1
                errors.append(f"row {idx + 1}: {e}")

        await db.flush()
        return ImportTimetableResult(created_count=created, skipped_count=skipped, errors=errors)

    @strawberry.mutation(description="Create a new task")
    async def create_task(
        self,
        info: Info,
        input: CreateTaskInput,
    ) -> Task:
        """Create a new task."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        subject_uuid = _id_to_uuid(input.subject_id) if input.subject_id else None
        if subject_uuid:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == subject_uuid, SubjectModel.user_id == user.id))
            if sres.scalar_one_or_none() is None:
                raise ValueError("Subject not found")

        task = TaskModel(
            user_id=user.id,
            title=input.title,
            description=input.description,
            task_type=input.task_type,
            duration_minutes=input.duration_minutes,
            priority=input.priority or 50,
            deadline=input.deadline,
            subject_id=subject_uuid,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        subject = None
        if task.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == task.subject_id))
            subject = sres.scalar_one_or_none()

        return _to_gql_task(task, subject)

    @strawberry.mutation(description="Update an existing task")
    async def update_task(
        self,
        info: Info,
        id: strawberry.ID,
        input: UpdateTaskInput,
    ) -> Task:
        """Update an existing task."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        task_id = _id_to_uuid(id)
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
        task = result.scalar_one_or_none()
        if task is None:
            raise ValueError("Task not found")

        if input.title is not None:
            task.title = input.title
        if input.description is not None:
            task.description = input.description
        if input.task_type is not None:
            task.task_type = input.task_type
        if input.duration_minutes is not None:
            task.duration_minutes = input.duration_minutes
        if input.priority is not None:
            task.priority = input.priority
        if input.deadline is not None:
            task.deadline = input.deadline
        if input.subject_id is not None:
            subject_uuid = _id_to_uuid(input.subject_id)
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == subject_uuid, SubjectModel.user_id == user.id))
            if sres.scalar_one_or_none() is None:
                raise ValueError("Subject not found")
            task.subject_id = subject_uuid

        if input.is_completed is not None:
            if input.is_completed:
                task.mark_completed()
            else:
                task.is_completed = False
                task.completed_at = None

        db.add(task)
        await db.flush()
        await db.refresh(task)

        subject = None
        if task.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == task.subject_id))
            subject = sres.scalar_one_or_none()

        return _to_gql_task(task, subject)

    @strawberry.mutation(description="Delete a task")
    async def delete_task(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> bool:
        """Delete a task by ID."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        task_id = _id_to_uuid(id)
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
        task = result.scalar_one_or_none()
        if task is None:
            return False

        await db.delete(task)
        await db.flush()
        return True

    @strawberry.mutation(description="Create a new time block")
    async def create_time_block(
        self,
        info: Info,
        input: CreateTimeBlockInput,
    ) -> TimeBlock:
        """Create a new time block."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        block = TimeBlockModel(
            user_id=user.id,
            title=input.title,
            block_type=input.block_type,
            start_time=input.start_time,
            end_time=input.end_time,
            is_fixed=input.is_fixed,
            task_id=_id_to_uuid(input.task_id) if input.task_id else None,
            block_metadata=None,
        )
        db.add(block)
        await db.flush()
        await db.refresh(block)

        return TimeBlock(
            id=_uuid_to_id(block.id),
            title=block.title,
            block_type=block.block_type,
            start_time=block.start_time,
            end_time=block.end_time,
            is_fixed=block.is_fixed,
            task_id=_uuid_to_id(block.task_id) if block.task_id else None,
            task=None,
            metadata=block.block_metadata,
            duration_minutes=block.duration_minutes,
        )

    @strawberry.mutation(description="Move a time block to a new start time")
    async def move_time_block(
        self,
        info: Info,
        id: strawberry.ID,
        new_start: datetime,
    ) -> TimeBlock:
        """Move a time block to a new start time."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        block_id = _id_to_uuid(id)
        result = await db.execute(
            select(TimeBlockModel).where(
                TimeBlockModel.id == block_id,
                TimeBlockModel.user_id == user.id,
            )
        )
        block = result.scalar_one_or_none()
        if block is None:
            raise ValueError("Time block not found")
        if block.is_fixed:
            raise ValueError("Cannot modify fixed time blocks")

        duration_minutes = int((block.end_time - block.start_time).total_seconds() // 60)
        new_end = new_start + timedelta(minutes=duration_minutes)

        # naive overlap check against other user blocks
        result = await db.execute(
            select(TimeBlockModel)
            .where(TimeBlockModel.user_id == user.id)
            .where(TimeBlockModel.id != block_id)
            .where(TimeBlockModel.start_time < new_end)
            .where(TimeBlockModel.end_time > new_start)
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError(f"New time range overlaps with: {existing.title}")

        block.start_time = new_start
        block.end_time = new_end
        db.add(block)
        await db.flush()
        await db.refresh(block)

        return TimeBlock(
            id=_uuid_to_id(block.id),
            title=block.title,
            block_type=block.block_type,
            start_time=block.start_time,
            end_time=block.end_time,
            is_fixed=block.is_fixed,
            task_id=_uuid_to_id(block.task_id) if block.task_id else None,
            task=None,
            metadata=block.block_metadata,
            duration_minutes=block.duration_minutes,
        )

    @strawberry.mutation(description="Delete a time block")
    async def delete_time_block(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> bool:
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        block_id = _id_to_uuid(id)
        result = await db.execute(
            select(TimeBlockModel).where(
                TimeBlockModel.id == block_id,
                TimeBlockModel.user_id == user.id,
            )
        )
        block = result.scalar_one_or_none()
        if block is None:
            return False
        if block.is_fixed:
            raise ValueError("Cannot delete fixed time blocks")

        await db.delete(block)
        await db.flush()
        return True

    @strawberry.mutation(description="Start the study timer")
    async def start_timer(
        self,
        info: Info,
        subject_id: Optional[strawberry.ID] = None,
    ) -> TimerStatus:
        """Start the study timer."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        # ensure no existing timer
        result = await db.execute(select(ActiveTimerModel).where(ActiveTimerModel.user_id == user.id))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise ValueError("Timer already running")

        subject_uuid = _id_to_uuid(subject_id) if subject_id else None
        if subject_uuid is not None:
            # validate ownership
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == subject_uuid, SubjectModel.user_id == user.id))
            if sres.scalar_one_or_none() is None:
                raise ValueError("Subject not found")

        timer = ActiveTimerModel(
            user_id=user.id,
            subject_id=subject_uuid,
            started_at=datetime.utcnow(),
        )
        db.add(timer)
        await db.flush()
        await db.refresh(timer)

        subject = None
        if timer.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == timer.subject_id))
            sm = sres.scalar_one_or_none()
            if sm is not None:
                subject = _to_gql_subject(sm)

        return TimerStatus(
            is_running=True,
            subject_id=_uuid_to_id(timer.subject_id) if timer.subject_id else None,
            subject=subject,
            started_at=timer.started_at,
            elapsed_minutes=0,
        )

    @strawberry.mutation(description="Stop the study timer")
    async def stop_timer(self, info: Info) -> StudySession:
        """Stop the study timer and create a session."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        result = await db.execute(select(ActiveTimerModel).where(ActiveTimerModel.user_id == user.id))
        timer = result.scalar_one_or_none()
        if timer is None:
            raise ValueError("No timer running")

        session = StudySessionModel(
            user_id=user.id,
            subject_id=timer.subject_id,
            started_at=timer.started_at,
            notes=None,
        )
        session.stop()

        db.add(session)
        await db.delete(timer)
        await db.flush()
        await db.refresh(session)

        subject = None
        if session.subject_id:
            sres = await db.execute(select(SubjectModel).where(SubjectModel.id == session.subject_id))
            sm = sres.scalar_one_or_none()
            if sm is not None:
                subject = _to_gql_subject(sm)

        return StudySession(
            id=_uuid_to_id(session.id),
            subject_id=_uuid_to_id(session.subject_id) if session.subject_id else None,
            subject=subject,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_minutes=session.duration_minutes,
            is_deep_work=session.is_deep_work,
            notes=session.notes,
        )

    @strawberry.mutation(description="Create a new goal")
    async def create_goal(
        self,
        info: Info,
        input: CreateGoalInput,
    ) -> Goal:
        """Create a new goal."""
        now = datetime.utcnow()
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        goal = GoalModel(
            user_id=user.id,
            title=input.title,
            description=input.description,
            target_value=input.target_value,
            current_value=0.0,
            unit=input.unit,
            deadline=date.fromisoformat(input.deadline) if input.deadline else None,
            status=GoalStatusEnum.ACTIVE.value,
            category_id=_id_to_uuid(input.category_id) if input.category_id else None,
        )
        db.add(goal)
        await db.flush()
        await db.refresh(goal)

        return Goal(
            id=_uuid_to_id(goal.id),
            title=goal.title,
            description=goal.description,
            target_value=goal.target_value,
            current_value=goal.current_value,
            unit=goal.unit,
            deadline=goal.deadline.isoformat() if goal.deadline else None,
            status=goal.status,
            progress_percent=goal.progress_percent,
            category_id=_uuid_to_id(goal.category_id) if goal.category_id else None,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

    @strawberry.mutation(description="Update goal progress")
    async def update_goal_progress(
        self,
        info: Info,
        id: strawberry.ID,
        progress: float,
    ) -> Goal:
        """Update the progress of a goal."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        goal_id = _id_to_uuid(id)
        result = await db.execute(select(GoalModel).where(GoalModel.id == goal_id, GoalModel.user_id == user.id))
        goal = result.scalar_one_or_none()
        if goal is None:
            raise ValueError("Goal not found")

        goal.update_progress(progress)
        db.add(goal)
        await db.flush()
        await db.refresh(goal)

        return Goal(
            id=_uuid_to_id(goal.id),
            title=goal.title,
            description=goal.description,
            target_value=goal.target_value,
            current_value=goal.current_value,
            unit=goal.unit,
            deadline=goal.deadline.isoformat() if goal.deadline else None,
            status=goal.status,
            progress_percent=goal.progress_percent,
            category_id=_uuid_to_id(goal.category_id) if goal.category_id else None,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

    @strawberry.mutation(description="Send a message to the AI assistant")
    async def send_chat_message(
        self,
        info: Info,
        message: str,
    ) -> ChatResponse:
        """Send a message to the AI assistant."""
        db = _get_db_from_context(info)
        user = _get_user_from_context(info)

        # Call the existing REST handler logic directly to avoid duplicating agent wiring.
        from app.api.chat import send_chat_message as chat_handler

        req = ChatRequest(message=message, user_id=str(user.id))
        resp = await chat_handler(req, db)

        return ChatResponse(
            message=resp.content,
            suggestions=[],
            tool_calls=[tc.name for tc in (resp.tool_calls or [])],
        )
