"""
Property-based tests for error response well-formedness.

**Property 11: Error Response Well-Formedness**
**Validates: Requirements 5.4, 19.1, 19.2, 19.3**

For any API error condition, the response SHALL contain a valid error code,
human-readable message, and optional suggestion—never an empty or malformed response.
"""

from hypothesis import given, strategies as st, settings, assume
import re

from app.api.errors import (
    ErrorCode,
    ErrorResponse,
    ErrorDetail,
    APIError,
    create_error_response,
    handle_scheduler_error,
    ERROR_SUGGESTIONS,
    ERROR_STATUS_MAP,
)
from app.scheduler.bridge import SchedulerError, SchedulerErrorCode


# Strategy for generating error codes
error_code_strategy = st.sampled_from(list(ErrorCode))

# Strategy for generating scheduler error codes
scheduler_error_code_strategy = st.sampled_from(list(SchedulerErrorCode))

# Strategy for generating non-empty messages
message_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())


class TestErrorResponseWellFormedness:
    """
    Property 11: Error Response Well-Formedness
    
    Feature: aesa-core-scheduling, Property 11: Error Response Well-Formedness
    Validates: Requirements 5.4, 19.1, 19.2, 19.3
    """
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_create_error_response_has_valid_code(
        self, code: ErrorCode, message: str
    ):
        """
        For any error, the response should contain a valid error code.
        """
        response = create_error_response(code, message)
        
        # Response should have success=False
        assert response["success"] is False
        
        # Response should have error object
        assert "error" in response
        
        # Error should have code
        assert "code" in response["error"]
        assert response["error"]["code"] is not None
        assert len(response["error"]["code"]) > 0
        
        # Code should match the pattern EXXX
        assert re.match(r"E\d{3}", response["error"]["code"]), (
            f"Error code should match pattern EXXX, got {response['error']['code']}"
        )
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_create_error_response_has_message(
        self, code: ErrorCode, message: str
    ):
        """
        For any error, the response should contain a human-readable message.
        """
        response = create_error_response(code, message)
        
        # Error should have message
        assert "message" in response["error"]
        assert response["error"]["message"] is not None
        assert len(response["error"]["message"]) > 0
        assert isinstance(response["error"]["message"], str)
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_create_error_response_never_empty(
        self, code: ErrorCode, message: str
    ):
        """
        For any error, the response should never be empty or malformed.
        """
        response = create_error_response(code, message)
        
        # Response should not be empty
        assert response is not None
        assert len(response) > 0
        
        # Response should be a dict
        assert isinstance(response, dict)
        
        # Required fields should exist
        assert "success" in response
        assert "error" in response
        assert isinstance(response["error"], dict)
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_api_error_to_response_well_formed(
        self, code: ErrorCode, message: str
    ):
        """
        For any APIError, to_response() should produce a well-formed response.
        """
        error = APIError(code=code, message=message)
        response = error.to_response()
        
        # Should be ErrorResponse type
        assert isinstance(response, ErrorResponse)
        
        # Should have success=False
        assert response.success is False
        
        # Should have error detail
        assert response.error is not None
        assert isinstance(response.error, ErrorDetail)
        
        # Error detail should have required fields
        assert response.error.code is not None
        assert response.error.message is not None
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_api_error_to_dict_well_formed(
        self, code: ErrorCode, message: str
    ):
        """
        For any APIError, to_dict() should produce a well-formed dict.
        """
        error = APIError(code=code, message=message)
        response_dict = error.to_dict()
        
        # Should be a dict
        assert isinstance(response_dict, dict)
        
        # Should have required structure
        assert "success" in response_dict
        assert response_dict["success"] is False
        assert "error" in response_dict
        assert "code" in response_dict["error"]
        assert "message" in response_dict["error"]
    
    @given(scheduler_error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_handle_scheduler_error_well_formed(
        self, code: SchedulerErrorCode, message: str
    ):
        """
        For any SchedulerError, handle_scheduler_error should produce
        a well-formed response.
        """
        scheduler_error = SchedulerError(
            code=code,
            message=message,
        )
        
        response = handle_scheduler_error(scheduler_error)
        
        # Should be a dict
        assert isinstance(response, dict)
        
        # Should have required structure
        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        
        # Code should be valid
        assert re.match(r"E\d{3}", response["error"]["code"])
    
    @given(error_code_strategy)
    @settings(max_examples=100)
    def test_error_code_has_status_mapping(self, code: ErrorCode):
        """
        For any error code, there should be a corresponding HTTP status.
        """
        assert code in ERROR_STATUS_MAP, (
            f"Error code {code} should have a status mapping"
        )
        
        status = ERROR_STATUS_MAP[code]
        assert isinstance(status, int)
        assert 400 <= status <= 599, (
            f"HTTP status should be 4xx or 5xx, got {status}"
        )
    
    @given(
        error_code_strategy,
        message_strategy,
        st.text(max_size=200),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=5),
    )
    @settings(max_examples=100)
    def test_error_response_with_optional_fields(
        self,
        code: ErrorCode,
        message: str,
        suggestion: str,
        context: dict,
    ):
        """
        For any error with optional fields, the response should still be well-formed.
        """
        response = create_error_response(
            code=code,
            message=message,
            suggestion=suggestion if suggestion.strip() else None,
            context=context if context else None,
        )
        
        # Required fields should exist
        assert response["success"] is False
        assert response["error"]["code"] is not None
        assert response["error"]["message"] is not None
        
        # Optional fields should be present (may be None)
        assert "suggestion" in response["error"]
        assert "context" in response["error"]
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_error_response_message_preserved(
        self, code: ErrorCode, message: str
    ):
        """
        For any error, the original message should be preserved in the response.
        """
        response = create_error_response(code, message)
        
        assert response["error"]["message"] == message
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_api_error_status_code_valid(
        self, code: ErrorCode, message: str
    ):
        """
        For any APIError, the status_code should be a valid HTTP error status.
        """
        error = APIError(code=code, message=message)
        
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code <= 599


class TestErrorSuggestions:
    """
    Tests for error suggestions being provided appropriately.
    """
    
    @given(error_code_strategy, message_strategy)
    @settings(max_examples=100)
    def test_common_errors_have_suggestions(
        self, code: ErrorCode, message: str
    ):
        """
        For common error codes, a default suggestion should be provided.
        """
        response = create_error_response(code, message)
        
        # If the code has a default suggestion, it should be included
        if code in ERROR_SUGGESTIONS:
            assert response["error"]["suggestion"] is not None
            assert len(response["error"]["suggestion"]) > 0
    
    @given(message_strategy, st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_custom_suggestion_overrides_default(
        self, message: str, custom_suggestion: str
    ):
        """
        For any error, a custom suggestion should override the default.
        """
        assume(custom_suggestion.strip())
        
        code = ErrorCode.NO_VALID_PLACEMENT  # Has a default suggestion
        response = create_error_response(
            code=code,
            message=message,
            suggestion=custom_suggestion,
        )
        
        assert response["error"]["suggestion"] == custom_suggestion
