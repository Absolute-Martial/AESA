"""
Property-based tests for GraphQL schema conformance.

**Property 18: GraphQL Schema Conformance**
**Validates: Requirements 23.3, 23.4, 23.5**

For any GraphQL query against the schema, the response data structure SHALL
conform to the declared return types—no null values where non-nullable declared,
correct field types.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Any, Optional

from hypothesis import given, strategies as st, settings, assume
import pytest

from app.graphql.schema import schema
from app.graphql.types import (
    Task,
    TimeBlock,
    DaySchedule,
    Subject,
    Goal,
    Notification,
    TimerStatus,
    StudyAnalytics,
    StudySession,
    ChatResponse,
    Gap,
    DayStats,
    TimetableEntry,
    TaskFilter,
    CreateTaskInput,
    UpdateTaskInput,
    CreateTimeBlockInput,
    CreateGoalInput,
    AnalyticsPeriod,
    GoalStatusEnum,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating valid task types
task_type_strategy = st.sampled_from([
    "university", "study", "revision", "practice", "assignment",
    "lab_work", "deep_work", "break", "free_time", "sleep",
    "wake_routine", "breakfast", "lunch", "dinner"
])

# Strategy for generating valid goal statuses
goal_status_strategy = st.sampled_from(["active", "completed", "abandoned"])

# Strategy for generating valid analytics periods
analytics_period_strategy = st.sampled_from([
    AnalyticsPeriod.TODAY,
    AnalyticsPeriod.WEEK,
    AnalyticsPeriod.MONTH,
])

# Strategy for generating non-empty titles
title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())

# Strategy for generating valid durations (5-480 minutes)
duration_strategy = st.integers(min_value=5, max_value=480)

# Strategy for generating valid priorities (0-100)
priority_strategy = st.integers(min_value=0, max_value=100)

# Strategy for generating valid dates as ISO strings
date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2030, 12, 31)
).map(lambda d: d.isoformat())


def execute_sync(query: str, variable_values: dict = None):
    """Execute a GraphQL query synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            schema.execute(query, variable_values=variable_values)
        )
        return result
    finally:
        loop.close()


class TestGraphQLSchemaConformance:
    """
    Property 18: GraphQL Schema Conformance
    
    Feature: aesa-core-scheduling, Property 18: GraphQL Schema Conformance
    Validates: Requirements 23.3, 23.4, 23.5
    """
    
    @given(analytics_period_strategy)
    @settings(max_examples=100)
    def test_analytics_query_returns_correct_types(self, period: AnalyticsPeriod):
        """
        For any analytics period, the query should return correctly typed fields.
        """
        query = """
            query TestAnalytics($period: AnalyticsPeriod!) {
                analytics(period: $period) {
                    period
                    totalStudyMinutes
                    deepWorkMinutes
                    sessionsCount
                    subjectsStudied
                    averageSessionMinutes
                    longestSessionMinutes
                    streakDays
                }
            }
        """
        
        result = execute_sync(
            query,
            variable_values={"period": period.value.upper()}
        )
        
        # Should not have errors
        assert result.errors is None, f"Query errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "analytics" in result.data
        
        analytics = result.data["analytics"]
        
        # All non-nullable fields should be present and correct type
        assert analytics["period"] is not None
        assert isinstance(analytics["period"], str)
        
        assert analytics["totalStudyMinutes"] is not None
        assert isinstance(analytics["totalStudyMinutes"], int)
        
        assert analytics["deepWorkMinutes"] is not None
        assert isinstance(analytics["deepWorkMinutes"], int)
        
        assert analytics["sessionsCount"] is not None
        assert isinstance(analytics["sessionsCount"], int)
        
        assert analytics["subjectsStudied"] is not None
        assert isinstance(analytics["subjectsStudied"], int)
        
        assert analytics["averageSessionMinutes"] is not None
        assert isinstance(analytics["averageSessionMinutes"], (int, float))
        
        assert analytics["longestSessionMinutes"] is not None
        assert isinstance(analytics["longestSessionMinutes"], int)
        
        assert analytics["streakDays"] is not None
        assert isinstance(analytics["streakDays"], int)
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_today_schedule_query_returns_correct_structure(self, _):
        """
        For todaySchedule query, the response should have correct structure.
        """
        query = """
            query TestTodaySchedule {
                todaySchedule {
                    scheduleDate
                    blocks {
                        id
                        title
                        blockType
                        startTime
                        endTime
                        isFixed
                        durationMinutes
                    }
                    gaps {
                        startTime
                        endTime
                        durationMinutes
                        gapType
                        isDeepWorkOpportunity
                    }
                    stats {
                        totalStudyMinutes
                        deepWorkMinutes
                        hasDeepWorkOpportunity
                        gapCount
                        tasksCompleted
                        energyLevel
                    }
                }
            }
        """
        
        result = execute_sync(query)
        
        # Should not have errors
        assert result.errors is None, f"Query errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "todaySchedule" in result.data
        
        schedule = result.data["todaySchedule"]
        
        # Non-nullable fields should be present
        assert schedule["scheduleDate"] is not None
        assert isinstance(schedule["scheduleDate"], str)
        
        assert schedule["blocks"] is not None
        assert isinstance(schedule["blocks"], list)
        
        assert schedule["gaps"] is not None
        assert isinstance(schedule["gaps"], list)
        
        assert schedule["stats"] is not None
        assert isinstance(schedule["stats"], dict)
        
        # Stats should have correct structure
        stats = schedule["stats"]
        assert stats["totalStudyMinutes"] is not None
        assert stats["deepWorkMinutes"] is not None
        assert stats["hasDeepWorkOpportunity"] is not None
        assert stats["gapCount"] is not None
        assert stats["tasksCompleted"] is not None
        assert stats["energyLevel"] is not None
    
    @given(date_strategy)
    @settings(max_examples=100)
    def test_week_schedule_query_returns_seven_days(self, start_date: str):
        """
        For any start date, weekSchedule should return exactly 7 days.
        """
        query = """
            query TestWeekSchedule($startDate: String!) {
                weekSchedule(startDate: $startDate) {
                    scheduleDate
                    blocks {
                        id
                        title
                    }
                    stats {
                        totalStudyMinutes
                    }
                }
            }
        """
        
        result = execute_sync(
            query,
            variable_values={"startDate": start_date}
        )
        
        # Should not have errors
        assert result.errors is None, f"Query errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "weekSchedule" in result.data
        
        week = result.data["weekSchedule"]
        
        # Should have exactly 7 days
        assert len(week) == 7
        
        # Each day should have correct structure
        for day in week:
            assert day["scheduleDate"] is not None
            assert isinstance(day["scheduleDate"], str)
            assert day["blocks"] is not None
            assert isinstance(day["blocks"], list)
            assert day["stats"] is not None
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_timer_status_query_returns_correct_types(self, _):
        """
        For timerStatus query, the response should have correct types.
        """
        query = """
            query TestTimerStatus {
                timerStatus {
                    isRunning
                    subjectId
                    startedAt
                    elapsedMinutes
                }
            }
        """
        
        result = execute_sync(query)
        
        # Should not have errors
        assert result.errors is None, f"Query errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "timerStatus" in result.data
        
        timer = result.data["timerStatus"]
        
        if timer is not None:
            # Non-nullable fields should be correct type
            assert isinstance(timer["isRunning"], bool)
            assert isinstance(timer["elapsedMinutes"], int)
    
    @given(title_strategy, duration_strategy, priority_strategy, task_type_strategy)
    @settings(max_examples=100)
    def test_create_task_mutation_returns_correct_types(
        self, title: str, duration: int, priority: int, task_type: str
    ):
        """
        For any valid input, createTask mutation should return correctly typed Task.
        """
        assume(title.strip())
        
        mutation = """
            mutation TestCreateTask($input: CreateTaskInput!) {
                createTask(input: $input) {
                    id
                    title
                    description
                    taskType
                    durationMinutes
                    priority
                    isCompleted
                    createdAt
                    updatedAt
                }
            }
        """
        
        result = execute_sync(
            mutation,
            variable_values={
                "input": {
                    "title": title,
                    "durationMinutes": duration,
                    "priority": priority,
                    "taskType": task_type,
                }
            }
        )
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "createTask" in result.data
        
        task = result.data["createTask"]
        
        # Non-nullable fields should be present and correct type
        assert task["id"] is not None
        assert isinstance(task["id"], str)
        
        assert task["title"] is not None
        assert isinstance(task["title"], str)
        assert task["title"] == title
        
        assert task["taskType"] is not None
        assert isinstance(task["taskType"], str)
        
        assert task["durationMinutes"] is not None
        assert isinstance(task["durationMinutes"], int)
        assert task["durationMinutes"] == duration
        
        assert task["priority"] is not None
        assert isinstance(task["priority"], int)
        
        assert task["isCompleted"] is not None
        assert isinstance(task["isCompleted"], bool)
        
        assert task["createdAt"] is not None
        assert task["updatedAt"] is not None
    
    @given(title_strategy)
    @settings(max_examples=100)
    def test_create_goal_mutation_returns_correct_types(self, title: str):
        """
        For any valid input, createGoal mutation should return correctly typed Goal.
        """
        assume(title.strip())
        
        mutation = """
            mutation TestCreateGoal($input: CreateGoalInput!) {
                createGoal(input: $input) {
                    id
                    title
                    description
                    targetValue
                    currentValue
                    unit
                    deadline
                    status
                    progressPercent
                    createdAt
                    updatedAt
                }
            }
        """
        
        result = execute_sync(
            mutation,
            variable_values={
                "input": {
                    "title": title,
                    "targetValue": 100.0,
                    "unit": "hours",
                }
            }
        )
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "createGoal" in result.data
        
        goal = result.data["createGoal"]
        
        # Non-nullable fields should be present and correct type
        assert goal["id"] is not None
        assert isinstance(goal["id"], str)
        
        assert goal["title"] is not None
        assert isinstance(goal["title"], str)
        assert goal["title"] == title
        
        assert goal["currentValue"] is not None
        assert isinstance(goal["currentValue"], (int, float))
        
        assert goal["status"] is not None
        assert isinstance(goal["status"], str)
        
        assert goal["progressPercent"] is not None
        assert isinstance(goal["progressPercent"], (int, float))
        
        assert goal["createdAt"] is not None
        assert goal["updatedAt"] is not None
    
    @given(st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    def test_send_chat_message_mutation_returns_correct_types(self, message: str):
        """
        For any message, sendChatMessage should return correctly typed ChatResponse.
        """
        mutation = """
            mutation TestSendChat($message: String!) {
                sendChatMessage(message: $message) {
                    message
                    suggestions
                    toolCalls
                }
            }
        """
        
        result = execute_sync(
            mutation,
            variable_values={"message": message}
        )
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "sendChatMessage" in result.data
        
        response = result.data["sendChatMessage"]
        
        # Non-nullable fields should be present and correct type
        assert response["message"] is not None
        assert isinstance(response["message"], str)
        
        assert response["suggestions"] is not None
        assert isinstance(response["suggestions"], list)
        
        assert response["toolCalls"] is not None
        assert isinstance(response["toolCalls"], list)
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_start_timer_mutation_returns_correct_types(self, _):
        """
        For startTimer mutation, the response should have correct types.
        """
        mutation = """
            mutation TestStartTimer {
                startTimer {
                    isRunning
                    subjectId
                    startedAt
                    elapsedMinutes
                }
            }
        """
        
        result = execute_sync(mutation)
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "startTimer" in result.data
        
        timer = result.data["startTimer"]
        
        # Non-nullable fields should be correct type
        assert timer["isRunning"] is not None
        assert isinstance(timer["isRunning"], bool)
        assert timer["isRunning"] is True
        
        assert timer["elapsedMinutes"] is not None
        assert isinstance(timer["elapsedMinutes"], int)
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_stop_timer_mutation_returns_correct_types(self, _):
        """
        For stopTimer mutation, the response should have correct types.
        """
        mutation = """
            mutation TestStopTimer {
                stopTimer {
                    id
                    startedAt
                    endedAt
                    durationMinutes
                    isDeepWork
                }
            }
        """
        
        result = execute_sync(mutation)
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "stopTimer" in result.data
        
        session = result.data["stopTimer"]
        
        # Non-nullable fields should be correct type
        assert session["id"] is not None
        assert isinstance(session["id"], str)
        
        assert session["startedAt"] is not None
        
        assert session["isDeepWork"] is not None
        assert isinstance(session["isDeepWork"], bool)
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_delete_task_mutation_returns_boolean(self, _):
        """
        For deleteTask mutation, the response should be a boolean.
        """
        mutation = """
            mutation TestDeleteTask($id: ID!) {
                deleteTask(id: $id)
            }
        """
        
        result = execute_sync(
            mutation,
            variable_values={"id": "test-task-id"}
        )
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "deleteTask" in result.data
        
        # Should be a boolean
        assert isinstance(result.data["deleteTask"], bool)
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_delete_time_block_mutation_returns_boolean(self, _):
        """
        For deleteTimeBlock mutation, the response should be a boolean.
        """
        mutation = """
            mutation TestDeleteTimeBlock($id: ID!) {
                deleteTimeBlock(id: $id)
            }
        """
        
        result = execute_sync(
            mutation,
            variable_values={"id": "test-block-id"}
        )
        
        # Should not have errors
        assert result.errors is None, f"Mutation errors: {result.errors}"
        
        # Should have data
        assert result.data is not None
        assert "deleteTimeBlock" in result.data
        
        # Should be a boolean
        assert isinstance(result.data["deleteTimeBlock"], bool)


class TestGraphQLSchemaIntrospection:
    """
    Tests for GraphQL schema introspection to verify schema structure.
    """
    
    @settings(max_examples=10)
    @given(st.just(None))
    def test_schema_has_required_query_fields(self, _):
        """
        The schema should have all required query fields.
        """
        query = """
            query IntrospectQueries {
                __schema {
                    queryType {
                        fields {
                            name
                        }
                    }
                }
            }
        """
        
        result = execute_sync(query)
        
        assert result.errors is None
        assert result.data is not None
        
        fields = result.data["__schema"]["queryType"]["fields"]
        field_names = {f["name"] for f in fields}
        
        required_queries = {
            "todaySchedule",
            "weekSchedule",
            "tasks",
            "task",
            "subjects",
            "goals",
            "analytics",
            "notifications",
            "timerStatus",
        }
        
        for query_name in required_queries:
            assert query_name in field_names, f"Missing query: {query_name}"
    
    @settings(max_examples=10)
    @given(st.just(None))
    def test_schema_has_required_mutation_fields(self, _):
        """
        The schema should have all required mutation fields.
        """
        query = """
            query IntrospectMutations {
                __schema {
                    mutationType {
                        fields {
                            name
                        }
                    }
                }
            }
        """
        
        result = execute_sync(query)
        
        assert result.errors is None
        assert result.data is not None
        
        fields = result.data["__schema"]["mutationType"]["fields"]
        field_names = {f["name"] for f in fields}
        
        required_mutations = {
            "createTask",
            "updateTask",
            "deleteTask",
            "createTimeBlock",
            "moveTimeBlock",
            "deleteTimeBlock",
            "startTimer",
            "stopTimer",
            "createGoal",
            "updateGoalProgress",
            "sendChatMessage",
        }
        
        for mutation_name in required_mutations:
            assert mutation_name in field_names, f"Missing mutation: {mutation_name}"
    
    @settings(max_examples=10)
    @given(st.just(None))
    def test_schema_has_required_types(self, _):
        """
        The schema should have all required types.
        """
        query = """
            query IntrospectTypes {
                __schema {
                    types {
                        name
                        kind
                    }
                }
            }
        """
        
        result = execute_sync(query)
        
        assert result.errors is None
        assert result.data is not None
        
        types = result.data["__schema"]["types"]
        type_names = {t["name"] for t in types}
        
        required_types = {
            "Task",
            "TimeBlock",
            "DaySchedule",
            "Subject",
            "Goal",
            "Notification",
            "TimerStatus",
            "StudyAnalytics",
            "StudySession",
            "ChatResponse",
            "Gap",
            "DayStats",
            "TimetableEntry",
        }
        
        for type_name in required_types:
            assert type_name in type_names, f"Missing type: {type_name}"
