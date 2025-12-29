"""
Property-based tests for analytics aggregation.

**Property 16: Analytics Aggregation Consistency**
**Validates: Requirements 17.2, 17.3**

For any analytics period (day, week, month), the total_study_time SHALL equal
the sum of all individual session durations within that period.
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
import uuid

from app.models.study import StudySession
from app.scheduler.analytics import (
    aggregate_sessions,
    StudyAnalytics,
    AnalyticsPeriod,
)


# Strategy for generating valid session durations (1-480 minutes)
duration_strategy = st.integers(min_value=1, max_value=480)

# Strategy for generating a list of session durations
durations_list_strategy = st.lists(
    duration_strategy,
    min_size=0,
    max_size=50,
)


def create_mock_session(
    duration_minutes: int,
    is_deep_work: bool = None,
    subject_id: uuid.UUID = None,
) -> StudySession:
    """
    Create a mock StudySession for testing.
    
    Args:
        duration_minutes: Session duration in minutes
        is_deep_work: Override deep work flag (auto-calculated if None)
        subject_id: Optional subject ID
        
    Returns:
        StudySession instance
    """
    started_at = datetime(2025, 1, 1, 10, 0, 0)
    ended_at = started_at + timedelta(minutes=duration_minutes)
    
    session = StudySession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subject_id=subject_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_minutes=duration_minutes,
        is_deep_work=is_deep_work if is_deep_work is not None else (duration_minutes >= 90),
    )
    
    return session


class TestAnalyticsAggregationConsistency:
    """
    Property 16: Analytics Aggregation Consistency
    
    Feature: aesa-core-scheduling, Property 16: Analytics Aggregation Consistency
    Validates: Requirements 17.2, 17.3
    """
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_total_study_time_equals_sum_of_sessions(self, durations: list[int]):
        """
        For any list of sessions, total_study_minutes should equal
        the sum of all individual session durations.
        
        Property 16: total_study_time = sum of all session durations
        """
        # Create sessions from durations
        sessions = [create_mock_session(d) for d in durations]
        
        # Aggregate
        analytics = aggregate_sessions(sessions)
        
        # Verify: total equals sum of individual durations
        expected_total = sum(durations)
        assert analytics.total_study_minutes == expected_total, (
            f"Total study minutes should be {expected_total}, "
            f"got {analytics.total_study_minutes}"
        )
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_deep_work_minutes_equals_sum_of_deep_work_sessions(self, durations: list[int]):
        """
        For any list of sessions, deep_work_minutes should equal
        the sum of durations for sessions >= 90 minutes.
        """
        # Create sessions from durations
        sessions = [create_mock_session(d) for d in durations]
        
        # Aggregate
        analytics = aggregate_sessions(sessions)
        
        # Verify: deep work equals sum of sessions >= 90 minutes
        expected_deep_work = sum(d for d in durations if d >= 90)
        assert analytics.deep_work_minutes == expected_deep_work, (
            f"Deep work minutes should be {expected_deep_work}, "
            f"got {analytics.deep_work_minutes}"
        )
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_sessions_count_equals_list_length(self, durations: list[int]):
        """
        For any list of sessions, sessions_count should equal
        the number of sessions.
        """
        sessions = [create_mock_session(d) for d in durations]
        
        analytics = aggregate_sessions(sessions)
        
        assert analytics.sessions_count == len(durations), (
            f"Sessions count should be {len(durations)}, "
            f"got {analytics.sessions_count}"
        )
    
    @given(st.lists(st.tuples(duration_strategy, st.booleans()), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_subjects_studied_counts_unique_subjects(
        self, session_data: list[tuple[int, bool]]
    ):
        """
        For any list of sessions with subjects, subjects_studied should
        equal the count of unique subject IDs.
        """
        # Create sessions with or without subjects
        sessions = []
        subject_ids = set()
        
        for duration, has_subject in session_data:
            subject_id = uuid.uuid4() if has_subject else None
            if subject_id:
                subject_ids.add(subject_id)
            sessions.append(create_mock_session(duration, subject_id=subject_id))
        
        analytics = aggregate_sessions(sessions)
        
        assert analytics.subjects_studied == len(subject_ids), (
            f"Subjects studied should be {len(subject_ids)}, "
            f"got {analytics.subjects_studied}"
        )
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_average_session_calculated_correctly(self, durations: list[int]):
        """
        For any non-empty list of sessions, average_session_minutes should
        equal total_study_minutes / sessions_count.
        """
        assume(len(durations) > 0)  # Skip empty lists
        
        sessions = [create_mock_session(d) for d in durations]
        
        analytics = aggregate_sessions(sessions)
        
        expected_avg = round(sum(durations) / len(durations), 1)
        assert analytics.average_session_minutes == expected_avg, (
            f"Average session should be {expected_avg}, "
            f"got {analytics.average_session_minutes}"
        )
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_longest_session_is_maximum(self, durations: list[int]):
        """
        For any list of sessions, longest_session_minutes should
        equal the maximum duration.
        """
        sessions = [create_mock_session(d) for d in durations]
        
        analytics = aggregate_sessions(sessions)
        
        expected_longest = max(durations) if durations else 0
        assert analytics.longest_session_minutes == expected_longest, (
            f"Longest session should be {expected_longest}, "
            f"got {analytics.longest_session_minutes}"
        )
    
    @settings(max_examples=100)
    @given(st.data())
    def test_empty_sessions_returns_zero_analytics(self, data):
        """
        For an empty list of sessions, all analytics should be zero.
        """
        analytics = aggregate_sessions([])
        
        assert analytics.total_study_minutes == 0
        assert analytics.deep_work_minutes == 0
        assert analytics.sessions_count == 0
        assert analytics.subjects_studied == 0
        assert analytics.average_session_minutes == 0.0
        assert analytics.longest_session_minutes == 0
    
    @given(durations_list_strategy)
    @settings(max_examples=100)
    def test_deep_work_percentage_calculated_correctly(self, durations: list[int]):
        """
        For any list of sessions, deep_work_percentage should equal
        (deep_work_minutes / total_study_minutes) * 100.
        """
        assume(len(durations) > 0)  # Skip empty lists
        
        sessions = [create_mock_session(d) for d in durations]
        
        analytics = aggregate_sessions(sessions)
        
        total = sum(durations)
        deep_work = sum(d for d in durations if d >= 90)
        
        if total == 0:
            expected_pct = 0.0
        else:
            expected_pct = round((deep_work / total) * 100, 1)
        
        assert analytics.deep_work_percentage == expected_pct, (
            f"Deep work percentage should be {expected_pct}, "
            f"got {analytics.deep_work_percentage}"
        )


class TestAnalyticsPeriod:
    """Tests for AnalyticsPeriod helper class."""
    
    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    @settings(max_examples=100)
    def test_today_period_starts_at_midnight(self, reference_date: datetime):
        """
        For any reference date, 'today' period should start at midnight.
        """
        period_start = AnalyticsPeriod.get_period_start("today", reference_date)
        
        assert period_start.hour == 0
        assert period_start.minute == 0
        assert period_start.second == 0
        assert period_start.microsecond == 0
        assert period_start.date() == reference_date.date()
    
    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    @settings(max_examples=100)
    def test_week_period_starts_on_monday(self, reference_date: datetime):
        """
        For any reference date, 'week' period should start on Monday.
        """
        period_start = AnalyticsPeriod.get_period_start("week", reference_date)
        
        # Monday is weekday 0
        assert period_start.weekday() == 0
        assert period_start.hour == 0
        assert period_start.minute == 0
    
    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    @settings(max_examples=100)
    def test_month_period_starts_on_first_day(self, reference_date: datetime):
        """
        For any reference date, 'month' period should start on day 1.
        """
        period_start = AnalyticsPeriod.get_period_start("month", reference_date)
        
        assert period_start.day == 1
        assert period_start.month == reference_date.month
        assert period_start.year == reference_date.year
        assert period_start.hour == 0
        assert period_start.minute == 0
    
    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    @settings(max_examples=100)
    def test_period_start_before_or_equal_reference(self, reference_date: datetime):
        """
        For any period, the start should be before or equal to the reference date.
        """
        for period in ["today", "week", "month"]:
            period_start = AnalyticsPeriod.get_period_start(period, reference_date)
            assert period_start <= reference_date, (
                f"Period start {period_start} should be <= reference {reference_date}"
            )


class TestStudyAnalyticsProperties:
    """Tests for StudyAnalytics class properties."""
    
    @given(st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_total_study_hours_conversion(self, total_minutes: int):
        """
        For any total_study_minutes, total_study_hours should equal
        total_study_minutes / 60 rounded to 2 decimal places.
        """
        analytics = StudyAnalytics(total_study_minutes=total_minutes)
        
        expected_hours = round(total_minutes / 60, 2)
        assert analytics.total_study_hours == expected_hours, (
            f"Total hours should be {expected_hours}, got {analytics.total_study_hours}"
        )
    
    @given(st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_deep_work_hours_conversion(self, deep_work_minutes: int):
        """
        For any deep_work_minutes, deep_work_hours should equal
        deep_work_minutes / 60 rounded to 2 decimal places.
        """
        analytics = StudyAnalytics(deep_work_minutes=deep_work_minutes)
        
        expected_hours = round(deep_work_minutes / 60, 2)
        assert analytics.deep_work_hours == expected_hours, (
            f"Deep work hours should be {expected_hours}, got {analytics.deep_work_hours}"
        )
    
    @given(
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_to_dict_contains_all_fields(self, total: int, deep_work: int):
        """
        For any analytics, to_dict should contain all expected fields.
        """
        analytics = StudyAnalytics(
            total_study_minutes=total,
            deep_work_minutes=deep_work,
        )
        
        result = analytics.to_dict()
        
        expected_keys = {
            "total_study_minutes",
            "deep_work_minutes",
            "sessions_count",
            "subjects_studied",
            "average_session_minutes",
            "longest_session_minutes",
            "streak_days",
            "tasks_completed",
            "total_study_hours",
            "deep_work_hours",
            "deep_work_percentage",
        }
        
        assert set(result.keys()) == expected_keys, (
            f"Missing keys: {expected_keys - set(result.keys())}"
        )
