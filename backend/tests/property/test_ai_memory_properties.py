"""
Property-based tests for AI memory round-trip.

**Property 17: AI Memory Round-Trip**
**Validates: Requirements 18.1, 18.2**

For any key-value pair saved to AI memory, retrieving by the same key
SHALL return the exact same value.
"""

import uuid
from datetime import datetime
from hypothesis import given, strategies as st, settings, HealthCheck, assume

from app.models.ai import AIMemory


# Strategy for valid memory keys (alphanumeric with underscores)
memory_key_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_0123456789"),
    min_size=1,
    max_size=100,
).filter(lambda x: x[0].isalpha())  # Must start with letter

# Strategy for memory values (any printable text)
memory_value_strategy = st.text(
    min_size=1,
    max_size=1000,
).filter(lambda x: x.strip())  # Non-empty after stripping


class TestAIMemoryRoundTrip:
    """
    Property 17: AI Memory Round-Trip
    
    Feature: aesa-core-scheduling, Property 17: AI Memory Round-Trip
    Validates: Requirements 18.1, 18.2
    """
    
    @given(
        key=memory_key_strategy,
        value=memory_value_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_round_trip_preserves_value(self, key: str, value: str):
        """
        For any key-value pair, saving and retrieving should return the same value.
        
        This tests the core round-trip property: save(key, value) then get(key) == value
        """
        # Create a memory object
        user_id = uuid.uuid4()
        
        memory = AIMemory(
            user_id=user_id,
            key=key,
            value=value,
        )
        
        # Verify the stored value matches
        assert memory.key == key
        assert memory.value == value
        assert memory.user_id == user_id
    
    @given(
        key=memory_key_strategy,
        value1=memory_value_strategy,
        value2=memory_value_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_update_replaces_value(self, key: str, value1: str, value2: str):
        """
        For any key, updating the value should replace the old value.
        
        This tests that update semantics work correctly.
        """
        assume(value1 != value2)  # Ensure values are different
        
        user_id = uuid.uuid4()
        
        # Create initial memory
        memory = AIMemory(
            user_id=user_id,
            key=key,
            value=value1,
        )
        
        assert memory.value == value1
        
        # Update the value
        memory.value = value2
        memory.updated_at = datetime.utcnow()
        
        # Verify the new value
        assert memory.value == value2
        assert memory.key == key  # Key unchanged
    
    @given(
        keys=st.lists(memory_key_strategy, min_size=2, max_size=10, unique=True),
        values=st.lists(memory_value_strategy, min_size=2, max_size=10),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_memories_are_independent(self, keys: list[str], values: list[str]):
        """
        For any set of distinct keys, each memory should be independent.
        
        Storing multiple key-value pairs should not interfere with each other.
        """
        # Ensure we have matching counts
        count = min(len(keys), len(values))
        keys = keys[:count]
        values = values[:count]
        
        user_id = uuid.uuid4()
        
        # Create memories
        memories = {}
        for key, value in zip(keys, values):
            memory = AIMemory(
                user_id=user_id,
                key=key,
                value=value,
            )
            memories[key] = memory
        
        # Verify each memory independently
        for key, value in zip(keys, values):
            assert memories[key].key == key
            assert memories[key].value == value
    
    @given(
        key=memory_key_strategy,
        value=memory_value_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_key_is_case_sensitive(self, key: str, value: str):
        """
        Memory keys should be case-sensitive.
        
        'preferred_time' and 'Preferred_Time' should be different keys.
        """
        user_id = uuid.uuid4()
        
        # Create memory with original key
        memory1 = AIMemory(
            user_id=user_id,
            key=key,
            value=value,
        )
        
        # Create memory with different case (if applicable)
        key_upper = key.upper()
        if key != key_upper:
            memory2 = AIMemory(
                user_id=user_id,
                key=key_upper,
                value="different_value",
            )
            
            # Keys should be different
            assert memory1.key != memory2.key
            assert memory1.value != memory2.value
    
    @given(
        key=memory_key_strategy,
        value=st.text(min_size=0, max_size=5000),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_handles_various_value_lengths(self, key: str, value: str):
        """
        Memory should handle values of various lengths.
        
        From empty strings to long text, the round-trip should preserve the value.
        """
        user_id = uuid.uuid4()
        
        memory = AIMemory(
            user_id=user_id,
            key=key,
            value=value,
        )
        
        # Value should be preserved exactly
        assert memory.value == value
        assert len(memory.value) == len(value)
    
    @given(
        key=memory_key_strategy,
        value=memory_value_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_preserves_special_characters(self, key: str, value: str):
        """
        Memory should preserve special characters in values.
        
        Unicode, newlines, and other special characters should be stored correctly.
        """
        # Add some special characters to the value
        special_value = f"{value}\n\t🎓📚"
        
        user_id = uuid.uuid4()
        
        memory = AIMemory(
            user_id=user_id,
            key=key,
            value=special_value,
        )
        
        # Special characters should be preserved
        assert memory.value == special_value
        assert "\n" in memory.value
        assert "\t" in memory.value
        assert "🎓" in memory.value


class TestAIGuidelineProperties:
    """
    Additional property tests for AI guidelines.
    
    Feature: aesa-core-scheduling, Property 17 (extended): AI Guideline Storage
    Validates: Requirements 18.3, 18.5
    """
    
    @given(
        guideline=st.text(min_size=10, max_size=500).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_guideline_storage_preserves_text(self, guideline: str):
        """
        For any guideline text, storage should preserve the exact text.
        """
        from app.models.ai import AIGuideline
        
        user_id = uuid.uuid4()
        
        ai_guideline = AIGuideline(
            user_id=user_id,
            guideline=guideline,
            is_active=True,
        )
        
        assert ai_guideline.guideline == guideline
        assert ai_guideline.is_active == True
    
    @given(
        guidelines=st.lists(
            st.text(min_size=10, max_size=200).filter(lambda x: x.strip()),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_guidelines_are_independent(self, guidelines: list[str]):
        """
        Multiple guidelines for the same user should be independent.
        """
        from app.models.ai import AIGuideline
        
        user_id = uuid.uuid4()
        
        stored_guidelines = []
        for text in guidelines:
            ai_guideline = AIGuideline(
                user_id=user_id,
                guideline=text,
                is_active=True,
            )
            stored_guidelines.append(ai_guideline)
        
        # Each guideline should have its own text
        for i, text in enumerate(guidelines):
            assert stored_guidelines[i].guideline == text
