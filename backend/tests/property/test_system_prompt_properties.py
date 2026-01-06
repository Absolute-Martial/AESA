"""
Property-based tests for system prompt inclusion.

**Property 12: System Prompt Inclusion**
**Validates: Requirements 6.5, 18.4**

For any user with stored memories or guidelines, the dynamically built
system prompt SHALL include all active guidelines and relevant memories.
"""

from hypothesis import given, strategies as st, settings, HealthCheck, assume

from app.agent.prompt_builder import (
    build_system_prompt_sync,
    format_memories,
    format_guidelines,
    check_prompt_includes_memories,
    check_prompt_includes_guidelines,
    BASE_SYSTEM_PROMPT,
)
from app.agent.state import AgentContext


# Strategy for valid memory keys
memory_key_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
    min_size=3,
    max_size=30,
).filter(lambda x: x[0].isalpha() and "__" not in x)

# Strategy for memory values (printable text without special markdown)
memory_value_strategy = st.text(
    alphabet=st.sampled_from(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-"
    ),
    min_size=5,
    max_size=100,
).filter(lambda x: x.strip())

# Strategy for guideline text
guideline_strategy = st.text(
    alphabet=st.sampled_from(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-"
    ),
    min_size=10,
    max_size=150,
).filter(lambda x: x.strip())


class TestSystemPromptInclusion:
    """
    Property 12: System Prompt Inclusion
    
    Feature: aesa-core-scheduling, Property 12: System Prompt Inclusion
    Validates: Requirements 6.5, 18.4
    """
    
    @given(
        memories=st.lists(
            st.fixed_dictionaries({
                "key": memory_key_strategy,
                "value": memory_value_strategy,
            }),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_includes_all_memories(self, memories: list[dict[str, str]]):
        """
        For any set of memories, the system prompt should include all of them.
        
        This tests that no memories are lost during prompt construction.
        """
        # Build prompt with memories
        prompt = build_system_prompt_sync(
            memories=memories,
            guidelines=[],
            context=None,
        )
        
        # Check all memories are included
        assert check_prompt_includes_memories(prompt, memories), (
            f"Prompt missing some memories. Memories: {memories}"
        )
    
    @given(
        guidelines=st.lists(
            guideline_strategy,
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_includes_all_guidelines(self, guidelines: list[str]):
        """
        For any set of guidelines, the system prompt should include all of them.
        
        This tests that no guidelines are lost during prompt construction.
        """
        # Build prompt with guidelines
        prompt = build_system_prompt_sync(
            memories=[],
            guidelines=guidelines,
            context=None,
        )
        
        # Check all guidelines are included
        assert check_prompt_includes_guidelines(prompt, guidelines), (
            f"Prompt missing some guidelines. Guidelines: {guidelines}"
        )
    
    @given(
        memories=st.lists(
            st.fixed_dictionaries({
                "key": memory_key_strategy,
                "value": memory_value_strategy,
            }),
            min_size=1,
            max_size=3,
        ),
        guidelines=st.lists(
            guideline_strategy,
            min_size=1,
            max_size=3,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_includes_both_memories_and_guidelines(
        self,
        memories: list[dict[str, str]],
        guidelines: list[str],
    ):
        """
        For any combination of memories and guidelines, the prompt should include all.
        
        This tests that memories and guidelines don't interfere with each other.
        """
        # Build prompt with both
        prompt = build_system_prompt_sync(
            memories=memories,
            guidelines=guidelines,
            context=None,
        )
        
        # Check all memories are included
        assert check_prompt_includes_memories(prompt, memories), (
            "Prompt missing some memories when combined with guidelines"
        )
        
        # Check all guidelines are included
        assert check_prompt_includes_guidelines(prompt, guidelines), (
            "Prompt missing some guidelines when combined with memories"
        )
    
    @given(
        memories=st.lists(
            st.fixed_dictionaries({
                "key": memory_key_strategy,
                "value": memory_value_strategy,
            }),
            min_size=0,
            max_size=3,
        ),
        guidelines=st.lists(
            guideline_strategy,
            min_size=0,
            max_size=3,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_always_includes_base_content(
        self,
        memories: list[dict[str, str]],
        guidelines: list[str],
    ):
        """
        For any input, the prompt should always include base content.
        
        The base system prompt with AESA identity should always be present.
        """
        prompt = build_system_prompt_sync(
            memories=memories,
            guidelines=guidelines,
            context=None,
        )
        
        # Check base content is present
        assert "AESA" in prompt, "Prompt missing AESA identity"
        assert "AI Engineering Study Assistant" in prompt, "Prompt missing full name"
        assert "Your Capabilities" in prompt, "Prompt missing capabilities section"
        assert "Important Guidelines" in prompt, "Prompt missing guidelines section"
    
    @given(
        task_title=st.text(min_size=5, max_size=50).filter(lambda x: x.strip()),
        subject=st.text(
            alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            min_size=7,
            max_size=7,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_includes_context_when_provided(
        self,
        task_title: str,
        subject: str,
    ):
        """
        When context is provided, the prompt should include context information.
        """
        context = AgentContext(
            current_task_title=task_title,
            active_subject=subject,
        )
        
        prompt = build_system_prompt_sync(
            memories=[],
            guidelines=[],
            context=context,
        )
        
        # Check context is included
        assert task_title in prompt, "Prompt missing current task title"
        assert subject in prompt, "Prompt missing active subject"
    
    @given(
        key=memory_key_strategy,
        value=memory_value_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_formatting_preserves_content(self, key: str, value: str):
        """
        Memory formatting should preserve both key and value.
        """
        memories = [{"key": key, "value": value}]
        formatted = format_memories(memories)
        
        assert key in formatted, f"Formatted memories missing key: {key}"
        assert value in formatted, f"Formatted memories missing value: {value}"
    
    @given(
        guideline=guideline_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_guideline_formatting_preserves_content(self, guideline: str):
        """
        Guideline formatting should preserve the guideline text.
        """
        guidelines = [guideline]
        formatted = format_guidelines(guidelines)
        
        assert guideline in formatted, f"Formatted guidelines missing: {guideline}"
    
    @given(
        memories=st.lists(
            st.fixed_dictionaries({
                "key": memory_key_strategy,
                "value": memory_value_strategy,
            }),
            min_size=2,
            max_size=5,
            unique_by=lambda x: x["key"],  # Unique keys
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_memories_all_included(self, memories: list[dict[str, str]]):
        """
        When multiple memories exist, all should be included in the prompt.
        """
        prompt = build_system_prompt_sync(
            memories=memories,
            guidelines=[],
            context=None,
        )
        
        # Each memory should be present
        for memory in memories:
            assert memory["key"] in prompt, f"Missing memory key: {memory['key']}"
            assert memory["value"] in prompt, f"Missing memory value: {memory['value']}"
    
    @given(
        guidelines=st.lists(
            guideline_strategy,
            min_size=2,
            max_size=5,
            unique=True,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_guidelines_all_included(self, guidelines: list[str]):
        """
        When multiple guidelines exist, all should be included in the prompt.
        """
        prompt = build_system_prompt_sync(
            memories=[],
            guidelines=guidelines,
            context=None,
        )
        
        # Each guideline should be present
        for guideline in guidelines:
            assert guideline in prompt, f"Missing guideline: {guideline}"


class TestPromptStructure:
    """
    Additional tests for prompt structure and ordering.
    """
    
    @given(
        memories=st.lists(
            st.fixed_dictionaries({
                "key": memory_key_strategy,
                "value": memory_value_strategy,
            }),
            min_size=1,
            max_size=3,
        ),
        guidelines=st.lists(
            guideline_strategy,
            min_size=1,
            max_size=3,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_sections_are_properly_ordered(
        self,
        memories: list[dict[str, str]],
        guidelines: list[str],
    ):
        """
        Prompt sections should appear in a logical order.
        
        Base content should come before memories and guidelines.
        """
        prompt = build_system_prompt_sync(
            memories=memories,
            guidelines=guidelines,
            context=None,
        )
        
        # Find positions of key sections
        base_pos = prompt.find("Your Capabilities")
        memories_pos = prompt.find("User Memories")
        guidelines_pos = prompt.find("User Guidelines")
        
        # Base should come first
        assert base_pos < memories_pos, "Base content should come before memories"
        assert base_pos < guidelines_pos, "Base content should come before guidelines"
    
    def test_empty_memories_and_guidelines_produces_valid_prompt(self):
        """
        Even with no memories or guidelines, the prompt should be valid.
        """
        prompt = build_system_prompt_sync(
            memories=[],
            guidelines=[],
            context=None,
        )
        
        # Should still have base content
        assert "AESA" in prompt
        assert len(prompt) > 100  # Should have substantial content
