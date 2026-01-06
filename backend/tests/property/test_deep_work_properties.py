"""
Property-based tests for deep work block detection.

**Property 7: Deep Work Block Detection**
**Validates: Requirements 3.5, 15.3**

For any timeline with a contiguous gap of 90 or more minutes, that gap SHALL
be flagged as a deep_work opportunity in the gap analysis.
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck

from app.scheduler.gaps import (
    TimeBlock,
    Gap,
    GapType,
    find_gaps,
    find_deep_work_slots,
    merge_overlapping_blocks,
    DEEP_WORK_IDEAL,
)


# Fixed day boundaries for testing
TEST_DAY_START = datetime(2025, 12, 29, 7, 0, 0)
TEST_DAY_END = datetime(2025, 12, 29, 23, 0, 0)


class TestDeepWorkBlockDetection:
    """
    Property 7: Deep Work Block Detection
    
    Feature: aesa-core-scheduling, Property 7: Deep Work Block Detection
    Validates: Requirements 3.5, 15.3
    """
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),  # start offset in minutes
            st.integers(min_value=15, max_value=120),  # duration in minutes
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_gaps_90_plus_minutes_are_deep_work(self, block_specs: list[tuple[int, int]]):
        """
        For any gap of 90+ minutes, it should be classified as deep_work.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        total_day_minutes = int((day_end - day_start).total_seconds() / 60)
        
        # Create blocks from specs
        blocks = []
        for start_offset, duration in block_specs:
            if start_offset + duration > total_day_minutes:
                continue
            
            start_time = day_start + timedelta(minutes=start_offset)
            end_time = start_time + timedelta(minutes=duration)
            
            blocks.append(TimeBlock(
                start_time=start_time,
                end_time=end_time,
                is_fixed=True,
                block_type="university",
            ))
        
        merged_blocks = merge_overlapping_blocks(blocks)
        gaps = find_gaps(merged_blocks, day_start, day_end)
        
        # Check all gaps >= 90 minutes are classified as deep_work
        for gap in gaps:
            if gap.duration_minutes >= DEEP_WORK_IDEAL:
                assert gap.is_deep_work_opportunity, (
                    f"Gap with duration {gap.duration_minutes} should be "
                    f"flagged as deep work opportunity"
                )
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),
            st.integers(min_value=15, max_value=120),
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_find_deep_work_slots_returns_only_qualifying_gaps(
        self, block_specs: list[tuple[int, int]]
    ):
        """
        find_deep_work_slots should return only gaps >= min_duration_minutes.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        total_day_minutes = int((day_end - day_start).total_seconds() / 60)
        
        blocks = []
        for start_offset, duration in block_specs:
            if start_offset + duration > total_day_minutes:
                continue
            
            start_time = day_start + timedelta(minutes=start_offset)
            end_time = start_time + timedelta(minutes=duration)
            
            blocks.append(TimeBlock(
                start_time=start_time,
                end_time=end_time,
                is_fixed=True,
                block_type="university",
            ))
        
        merged_blocks = merge_overlapping_blocks(blocks)
        
        # Get deep work slots with default threshold (90 min)
        deep_work_slots = find_deep_work_slots(
            merged_blocks, day_start, day_end, min_duration_minutes=DEEP_WORK_IDEAL
        )
        
        # All returned slots should be >= 90 minutes
        for slot in deep_work_slots:
            assert slot.duration_minutes >= DEEP_WORK_IDEAL, (
                f"Deep work slot has duration {slot.duration_minutes}, "
                f"expected >= {DEEP_WORK_IDEAL}"
            )
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),
            st.integers(min_value=15, max_value=120),
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_deep_work_slots_are_subset_of_all_gaps(
        self, block_specs: list[tuple[int, int]]
    ):
        """
        Deep work slots should be a subset of all gaps.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        total_day_minutes = int((day_end - day_start).total_seconds() / 60)
        
        blocks = []
        for start_offset, duration in block_specs:
            if start_offset + duration > total_day_minutes:
                continue
            
            start_time = day_start + timedelta(minutes=start_offset)
            end_time = start_time + timedelta(minutes=duration)
            
            blocks.append(TimeBlock(
                start_time=start_time,
                end_time=end_time,
                is_fixed=True,
                block_type="university",
            ))
        
        merged_blocks = merge_overlapping_blocks(blocks)
        
        all_gaps = find_gaps(merged_blocks, day_start, day_end)
        deep_work_slots = find_deep_work_slots(
            merged_blocks, day_start, day_end, min_duration_minutes=DEEP_WORK_IDEAL
        )
        
        # Every deep work slot should be in all_gaps
        all_gap_times = {(g.start_time, g.end_time) for g in all_gaps}
        for slot in deep_work_slots:
            assert (slot.start_time, slot.end_time) in all_gap_times, (
                f"Deep work slot {slot.start_time}-{slot.end_time} "
                f"not found in all gaps"
            )
    
    @given(st.integers(min_value=60, max_value=120))
    @settings(max_examples=100)
    def test_custom_deep_work_threshold(self, threshold: int):
        """
        find_deep_work_slots should respect custom min_duration_minutes.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        
        # Create a single block leaving a known gap
        block_duration = 60
        block = TimeBlock(
            start_time=day_start + timedelta(minutes=120),
            end_time=day_start + timedelta(minutes=120 + block_duration),
            is_fixed=True,
            block_type="university",
        )
        
        deep_work_slots = find_deep_work_slots(
            [block], day_start, day_end, min_duration_minutes=threshold
        )
        
        # All returned slots should be >= threshold
        for slot in deep_work_slots:
            assert slot.duration_minutes >= threshold
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),
            st.integers(min_value=15, max_value=120),
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_gaps_under_90_minutes_not_deep_work_opportunity(
        self, block_specs: list[tuple[int, int]]
    ):
        """
        Gaps under 90 minutes should not be flagged as deep work opportunities.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        total_day_minutes = int((day_end - day_start).total_seconds() / 60)
        
        blocks = []
        for start_offset, duration in block_specs:
            if start_offset + duration > total_day_minutes:
                continue
            
            start_time = day_start + timedelta(minutes=start_offset)
            end_time = start_time + timedelta(minutes=duration)
            
            blocks.append(TimeBlock(
                start_time=start_time,
                end_time=end_time,
                is_fixed=True,
                block_type="university",
            ))
        
        merged_blocks = merge_overlapping_blocks(blocks)
        gaps = find_gaps(merged_blocks, day_start, day_end)
        
        # Check gaps < 90 minutes are NOT flagged as deep work opportunity
        for gap in gaps:
            if gap.duration_minutes < DEEP_WORK_IDEAL:
                assert not gap.is_deep_work_opportunity, (
                    f"Gap with duration {gap.duration_minutes} should NOT be "
                    f"flagged as deep work opportunity"
                )
