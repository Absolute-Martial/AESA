"""
Property-based tests for task priority system.

**Property 9: Overdue Priority Elevation**
**Property 10: Priority Sort Order**
**Validates: Requirements 4.3, 4.4**
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock
import uuid

from app.scheduler.priority import (
    PriorityLevel,
    calculate_priority,
    is_task_overdue,
    should_elevate_priority,
    get_elevated_priority,
    sort_tasks_by_priority,
    compare_task_priority,
)
from app.models import Task


# Helper to create mock tasks
def create_mock_task(
    priority: int,
    deadline: datetime = None,
    is_completed: bool = False,
) -> Task:
    """Create a mock Task object for testing."""
    task = MagicMock(spec=Task)
    task.id = uuid.uuid4()
    task.priority = priority
    task.deadline = deadline
    task.is_completed = is_completed
    
    # Implement effective_priority property
    def get_effective_priority():
        if deadline and not is_completed and datetime.utcnow() > deadline:
            return PriorityLevel.OVERDUE
        return priority
    
    task.effective_priority = property(lambda self: get_effective_priority())
    # For mock, we need to set it directly
    type(task).effective_priority = property(lambda self: get_effective_priority())
    
    return task


class TestOverduePriorityElevation:
    """
    Property 9: Overdue Priority Elevation
    
    Feature: aesa-core-scheduling, Property 9: Overdue Priority Elevation
    Validates: Requirements 4.3
    
    For any task whose deadline has passed, the task's priority SHALL be
    automatically elevated to OVERDUE (100).
    """
    
    @given(st.integers(min_value=1, max_value=365))
    @settings(max_examples=100)
    def test_past_deadline_is_overdue(self, days_past: int):
        """
        For any deadline in the past, is_task_overdue should return True.
        """
        past_deadline = datetime.utcnow() - timedelta(days=days_past)
        assert is_task_overdue(past_deadline) is True
    
    @given(st.integers(min_value=1, max_value=365))
    @settings(max_examples=100)
    def test_future_deadline_not_overdue(self, days_future: int):
        """
        For any deadline in the future, is_task_overdue should return False.
        """
        future_deadline = datetime.utcnow() + timedelta(days=days_future)
        assert is_task_overdue(future_deadline) is False
    
    @settings(max_examples=100)
    @given(st.integers(min_value=0, max_value=99))
    def test_overdue_task_should_elevate(self, current_priority: int):
        """
        For any task with priority < 100 and past deadline, should_elevate_priority
        should return True.
        """
        past_deadline = datetime.utcnow() - timedelta(days=1)
        assert should_elevate_priority(current_priority, past_deadline) is True
    
    @given(st.integers(min_value=1, max_value=365))
    @settings(max_examples=100)
    def test_elevated_priority_is_overdue(self, days_past: int):
        """
        For any past deadline, get_elevated_priority should return OVERDUE (100).
        """
        past_deadline = datetime.utcnow() - timedelta(days=days_past)
        elevated = get_elevated_priority(past_deadline)
        assert elevated == PriorityLevel.OVERDUE
    
    @given(st.integers(min_value=0, max_value=99))
    @settings(max_examples=100)
    def test_calculate_priority_returns_overdue_for_past_deadline(
        self, _: int
    ):
        """
        For any task type with past deadline, calculate_priority should return OVERDUE.
        """
        past_deadline = datetime.utcnow() - timedelta(days=1)
        
        task_types = ["study", "assignment", "revision", "practice", "lab_work"]
        for task_type in task_types:
            priority = calculate_priority(task_type, deadline=past_deadline)
            assert priority == PriorityLevel.OVERDUE, (
                f"Task type {task_type} with past deadline should have "
                f"priority OVERDUE (100), got {priority}"
            )


class TestPrioritySortOrder:
    """
    Property 10: Priority Sort Order
    
    Feature: aesa-core-scheduling, Property 10: Priority Sort Order
    Validates: Requirements 4.4
    
    For any list of pending tasks returned by the API, the list SHALL be
    sorted by priority in descending order.
    """
    
    @given(st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=0,
        max_size=20,
    ))
    @settings(max_examples=100)
    def test_sorted_tasks_are_in_descending_order(self, priorities: list[int]):
        """
        For any list of tasks, sort_tasks_by_priority should return them
        in descending priority order.
        """
        # Create mock tasks with given priorities
        tasks = []
        for priority in priorities:
            task = MagicMock(spec=Task)
            task.priority = priority
            task.deadline = None
            task.is_completed = False
            # Set effective_priority to match priority (no deadline = no elevation)
            task.effective_priority = priority
            tasks.append(task)
        
        sorted_tasks = sort_tasks_by_priority(tasks)
        
        # Check descending order
        for i in range(len(sorted_tasks) - 1):
            assert sorted_tasks[i].effective_priority >= sorted_tasks[i + 1].effective_priority
    
    @given(st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=2,
        max_size=20,
    ))
    @settings(max_examples=100)
    def test_compare_task_priority_is_consistent(self, priorities: list[int]):
        """
        For any two tasks, compare_task_priority should be consistent with sort order.
        """
        tasks = []
        for priority in priorities:
            task = MagicMock(spec=Task)
            task.priority = priority
            task.effective_priority = priority
            tasks.append(task)
        
        # Compare all pairs
        for i in range(len(tasks)):
            for j in range(len(tasks)):
                comparison = compare_task_priority(tasks[i], tasks[j])
                
                if tasks[i].effective_priority > tasks[j].effective_priority:
                    assert comparison < 0, "Higher priority task should compare as less"
                elif tasks[i].effective_priority < tasks[j].effective_priority:
                    assert comparison > 0, "Lower priority task should compare as greater"
                else:
                    assert comparison == 0, "Equal priority tasks should compare as equal"
    
    @given(st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=20,
    ))
    @settings(max_examples=100)
    def test_highest_priority_is_first(self, priorities: list[int]):
        """
        For any list of tasks, the first task after sorting should have
        the highest priority.
        """
        tasks = []
        for priority in priorities:
            task = MagicMock(spec=Task)
            task.priority = priority
            task.effective_priority = priority
            tasks.append(task)
        
        sorted_tasks = sort_tasks_by_priority(tasks)
        max_priority = max(priorities)
        
        assert sorted_tasks[0].effective_priority == max_priority
    
    @given(st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=20,
    ))
    @settings(max_examples=100)
    def test_lowest_priority_is_last(self, priorities: list[int]):
        """
        For any list of tasks, the last task after sorting should have
        the lowest priority.
        """
        tasks = []
        for priority in priorities:
            task = MagicMock(spec=Task)
            task.priority = priority
            task.effective_priority = priority
            tasks.append(task)
        
        sorted_tasks = sort_tasks_by_priority(tasks)
        min_priority = min(priorities)
        
        assert sorted_tasks[-1].effective_priority == min_priority


class TestDueTodayPriority:
    """
    Additional tests for due-today priority elevation.
    """
    
    @given(st.integers(min_value=0, max_value=89))
    @settings(max_examples=100)
    def test_due_today_elevates_to_due_today_priority(self, current_priority: int):
        """
        For any task due today with priority < DUE_TODAY, should_elevate_priority
        should return True.
        """
        # Create a deadline for today
        now = datetime.utcnow()
        today_deadline = now.replace(hour=23, minute=59, second=59)
        
        # Only elevate if deadline is today and priority is below DUE_TODAY
        if current_priority < PriorityLevel.DUE_TODAY:
            assert should_elevate_priority(current_priority, today_deadline) is True
    
    @settings(max_examples=100)
    @given(st.integers(min_value=0, max_value=23))
    def test_due_today_returns_due_today_priority(self, hour: int):
        """
        For any deadline today, get_elevated_priority should return DUE_TODAY.
        """
        now = datetime.utcnow()
        today_deadline = now.replace(hour=hour, minute=30, second=0)
        
        # Only if deadline hasn't passed
        if today_deadline > now:
            elevated = get_elevated_priority(today_deadline)
            assert elevated == PriorityLevel.DUE_TODAY
