"""
Property-based tests for subject code validation.

**Property 14: Subject Code Validation**
**Validates: Requirements 9.5**

For any string matching the pattern [A-Z]{4}[0-9]{3}, the system SHALL accept
it as a valid subject code. For any string not matching this pattern, the
system SHALL reject it with a validation error.
"""

import string
from hypothesis import given, strategies as st, settings

from app.models.subject import validate_subject_code, SUBJECT_CODE_PATTERN


# Strategy for generating valid subject codes
@st.composite
def valid_subject_code_strategy(draw):
    """Generate a valid subject code: 4 uppercase letters + 3 digits."""
    letters = draw(st.text(
        alphabet=string.ascii_uppercase,
        min_size=4,
        max_size=4,
    ))
    digits = draw(st.text(
        alphabet=string.digits,
        min_size=3,
        max_size=3,
    ))
    return letters + digits


# Strategy for generating invalid subject codes
@st.composite
def invalid_subject_code_strategy(draw):
    """Generate an invalid subject code."""
    # Choose a type of invalid code
    invalid_type = draw(st.sampled_from([
        "too_short",
        "too_long",
        "lowercase_letters",
        "wrong_format",
        "letters_in_digits",
        "digits_in_letters",
        "empty",
        "special_chars",
    ]))
    
    if invalid_type == "too_short":
        # Less than 7 characters
        return draw(st.text(
            alphabet=string.ascii_uppercase + string.digits,
            min_size=1,
            max_size=6,
        ))
    elif invalid_type == "too_long":
        # More than 7 characters
        return draw(st.text(
            alphabet=string.ascii_uppercase + string.digits,
            min_size=8,
            max_size=15,
        ))
    elif invalid_type == "lowercase_letters":
        # Lowercase letters in first 4 positions
        letters = draw(st.text(
            alphabet=string.ascii_lowercase,
            min_size=4,
            max_size=4,
        ))
        digits = draw(st.text(
            alphabet=string.digits,
            min_size=3,
            max_size=3,
        ))
        return letters + digits
    elif invalid_type == "wrong_format":
        # Digits first, then letters
        digits = draw(st.text(
            alphabet=string.digits,
            min_size=3,
            max_size=3,
        ))
        letters = draw(st.text(
            alphabet=string.ascii_uppercase,
            min_size=4,
            max_size=4,
        ))
        return digits + letters
    elif invalid_type == "letters_in_digits":
        # Letters in the digit positions
        letters1 = draw(st.text(
            alphabet=string.ascii_uppercase,
            min_size=4,
            max_size=4,
        ))
        letters2 = draw(st.text(
            alphabet=string.ascii_uppercase,
            min_size=3,
            max_size=3,
        ))
        return letters1 + letters2
    elif invalid_type == "digits_in_letters":
        # Digits in the letter positions
        digits1 = draw(st.text(
            alphabet=string.digits,
            min_size=4,
            max_size=4,
        ))
        digits2 = draw(st.text(
            alphabet=string.digits,
            min_size=3,
            max_size=3,
        ))
        return digits1 + digits2
    elif invalid_type == "empty":
        return ""
    else:  # special_chars
        # Include special characters
        special = draw(st.text(
            alphabet="!@#$%^&*()_+-=[]{}|;':\",./<>?",
            min_size=1,
            max_size=3,
        ))
        letters = draw(st.text(
            alphabet=string.ascii_uppercase,
            min_size=2,
            max_size=4,
        ))
        return special + letters


class TestSubjectCodeValidation:
    """
    Property 14: Subject Code Validation
    
    Feature: aesa-core-scheduling, Property 14: Subject Code Validation
    Validates: Requirements 9.5
    """
    
    @given(valid_subject_code_strategy())
    @settings(max_examples=100)
    def test_valid_codes_are_accepted(self, code: str):
        """
        For any string matching [A-Z]{4}[0-9]{3}, validate_subject_code
        should return True.
        """
        assert validate_subject_code(code) is True, (
            f"Valid subject code '{code}' was rejected"
        )
    
    @given(invalid_subject_code_strategy())
    @settings(max_examples=100)
    def test_invalid_codes_are_rejected(self, code: str):
        """
        For any string not matching [A-Z]{4}[0-9]{3}, validate_subject_code
        should return False.
        """
        # Skip if the random generation accidentally created a valid code
        if SUBJECT_CODE_PATTERN.match(code):
            return
        
        assert validate_subject_code(code) is False, (
            f"Invalid subject code '{code}' was accepted"
        )
    
    @given(st.text(min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_validation_matches_regex(self, code: str):
        """
        For any string, validate_subject_code should return the same result
        as the regex pattern match.
        """
        expected = bool(SUBJECT_CODE_PATTERN.match(code))
        actual = validate_subject_code(code)
        
        assert actual == expected, (
            f"Validation mismatch for '{code}': "
            f"expected {expected}, got {actual}"
        )
    
    @given(
        st.text(alphabet=string.ascii_uppercase, min_size=4, max_size=4),
        st.text(alphabet=string.digits, min_size=3, max_size=3),
    )
    @settings(max_examples=100)
    def test_exact_format_is_valid(self, letters: str, digits: str):
        """
        For any combination of exactly 4 uppercase letters and 3 digits,
        the code should be valid.
        """
        code = letters + digits
        assert validate_subject_code(code) is True
    
    @given(st.text(alphabet=string.ascii_lowercase, min_size=4, max_size=4))
    @settings(max_examples=100)
    def test_lowercase_letters_are_invalid(self, letters: str):
        """
        For any code with lowercase letters, validation should fail.
        """
        code = letters + "123"
        assert validate_subject_code(code) is False
    
    @given(st.integers(min_value=0, max_value=999))
    @settings(max_examples=100)
    def test_specific_valid_codes(self, num: int):
        """
        Test specific valid codes like MATH101, PHYS102, etc.
        """
        # Generate codes like MATH001, MATH002, ..., MATH999
        code = f"MATH{num:03d}"
        assert validate_subject_code(code) is True
    
    def test_example_valid_codes(self):
        """Test specific example valid codes from requirements."""
        valid_codes = [
            "MATH101",
            "PHYS102",
            "COMP201",
            "ELEC301",
            "CHEM100",
            "ENGR999",
            "ABCD000",
            "ZZZZ999",
        ]
        
        for code in valid_codes:
            assert validate_subject_code(code) is True, (
                f"Expected valid code '{code}' was rejected"
            )
    
    def test_example_invalid_codes(self):
        """Test specific example invalid codes."""
        invalid_codes = [
            "MATH10",      # Too short
            "MATH1001",    # Too long
            "math101",     # Lowercase
            "101MATH",     # Wrong order
            "MATHABC",     # Letters instead of digits
            "1234567",     # All digits
            "ABCDEFG",     # All letters
            "",            # Empty
            "MAT101",      # Only 3 letters
            "MATH01",      # Only 2 digits
            "MATH 101",    # Space
            "MATH-101",    # Hyphen
        ]
        
        for code in invalid_codes:
            assert validate_subject_code(code) is False, (
                f"Expected invalid code '{code}' was accepted"
            )
