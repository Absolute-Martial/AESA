"""
Property-based tests for gap identification.

**Property 13: Gap Identification Completeness**
**Validates: Requirements 9.3**

For any daily timeline with scheduled blocks, all time periods between blocks
(and before first/after last block within active hours) SHALL be identified
as gaps with correct duration and type classification.
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck

from app.scheduler.gaps import (
    TimeBlock,
    Gap,
    GapType,
    find_gaps,
    classify_gap,
    merge_overlapping_blocks,
    MICRO_GAP_MAX,
    STANDARD_GAP_MAX,
    DEEP_WORK_MIN,
)


# Fixed day boundaries for testing
TEST_DAY_START = datetime(2025, 12, 29, 7, 0, 0)
TEST_DAY_END = datetime(2025, 12, 29, 23, 0, 0)


class TestGapIdentificationCompleteness:
    """
    Property 13: Gap Identification Completeness
    
    Feature: aesa-core-scheduling, Property 13: Gap Identification Completeness
    Validates: Requirements 9.3
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
    def test_gaps_cover_all_unscheduled_time(self, block_specs: list[tuple[int, int]]):
        """
        For any set of blocks, gaps should cover all unscheduled time.
        
        The total time covered by blocks + gaps should equal the active day duration.
        """
        day_start = TEST_DAY_START
        day_end = TEST_DAY_END
        total_day_minutes = int((day_end - day_start).total_seconds() / 60)
        
        # Create blocks from specs
        blocks = []
        for start_offset, duration in block_specs:
            # Ensure block fits within day
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
        
        # Merge overlapping blocks
        merged_blocks = merge_overlapping_blocks(blocks)
        
        # Find gaps with no minimum filter for exact coverage
        gaps = find_gaps(merged_blocks, day_start, day_end, min_gap_minutes=0)
        
        # Calculate total time covered by blocks
        block_minutes = sum(
            int((b.end_time - b.start_time).total_seconds() / 60)
            for b in merged_blocks
        )
        
        # Calculate total time covered by gaps
        gap_minutes = sum(g.duration_minutes for g in gaps)
        
        # Total should equal day duration
        assert block_minutes + gap_minutes == total_day_minutes
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),
            st.integers(min_value=15, max_value=120),
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_gaps_do_not_overlap_with_blocks(self, block_specs: list[tuple[int, int]]):
        """
        For any set of blocks, no gap should overlap with any block.
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
        
        # Check no gap overlaps with any block
        for gap in gaps:
            for block in merged_blocks:
                # Gap and block should not overlap
                overlaps = (
                    gap.start_time < block.end_time and
                    gap.end_time > block.start_time
                )
                assert not overlaps, (
                    f"Gap {gap.start_time}-{gap.end_time} overlaps with "
                    f"block {block.start_time}-{block.end_time}"
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
    def test_gaps_are_sorted_by_start_time(self, block_specs: list[tuple[int, int]]):
        """
        For any set of blocks, gaps should be returned sorted by start time.
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
        
        # Check gaps are sorted
        for i in range(len(gaps) - 1):
            assert gaps[i].start_time <= gaps[i + 1].start_time
    
    @given(st.integers(min_value=1, max_value=500))
    @settings(max_examples=100)
    def test_gap_classification_is_correct(self, duration_minutes: int):
        """
        For any gap duration, classification should match the defined thresholds.
        """
        gap_type = classify_gap(duration_minutes)
        
        if duration_minutes < MICRO_GAP_MAX:
            assert gap_type == GapType.MICRO
        elif duration_minutes <= STANDARD_GAP_MAX:
            assert gap_type == GapType.STANDARD
        else:
            assert gap_type == GapType.DEEP_WORK
    
    @given(st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=900),
            st.integers(min_value=15, max_value=120),
        ),
        min_size=0,
        max_size=5,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_gaps_have_correct_type_classification(self, block_specs: list[tuple[int, int]]):
        """
        For any set of blocks, each gap should have correct type based on duration.
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
        
        for gap in gaps:
            expected_type = classify_gap(gap.duration_minutes)
            assert gap.gap_type == expected_type, (
                f"Gap with duration {gap.duration_minutes} has type {gap.gap_type}, "
                f"expected {expected_type}"
            )
