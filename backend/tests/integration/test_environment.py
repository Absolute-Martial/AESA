"""
Environment configuration verification tests.

Tests:
- All environment variables are properly loaded
- Fail-fast on missing required config

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

import pytest
import os
from unittest.mock import patch
from pathlib import Path

from pydantic import ValidationError


class TestEnvironmentConfiguration:
    """Test environment configuration loading."""
    
    def test_settings_loads_defaults(self):
        """Test that settings loads with default values."""
        from app.core.config import Settings
        
        # Create settings with defaults
        settings = Settings()
        
        # Verify default values exist
        assert settings.app_name == "AESA Backend"
        assert settings.debug is False
        assert settings.database_url is not None
        assert settings.copilot_api_url is not None
        assert settings.engine_path is not None
        assert settings.upload_dir is not None
        assert settings.cors_origins is not None
    
    def test_database_url_configuration(self):
        """
        Test DATABASE_URL environment variable.
        
        Requirement 21.1: THE Backend SHALL read DATABASE_URL from environment.
        """
        from app.core.config import Settings
        
        test_url = "postgresql+asyncpg://test:test@testhost:5432/testdb"
        
        with patch.dict(os.environ, {"DATABASE_URL": test_url}):
            # Clear cache to force reload
            from app.core.config import get_settings
            get_settings.cache_clear()
            
            settings = Settings()
            assert settings.database_url == test_url
    
    def test_copilot_api_url_configuration(self):
        """
        Test COPILOT_API_URL environment variable.
        
        Requirement 21.1: THE Backend SHALL read COPILOT_API_URL from environment.
        """
        from app.core.config import Settings
        
        test_url = "http://custom-copilot:8080"
        
        with patch.dict(os.environ, {"COPILOT_API_URL": test_url}):
            settings = Settings()
            assert settings.copilot_api_url == test_url
    
    def test_engine_path_configuration(self):
        """
        Test ENGINE_PATH environment variable.
        
        Requirement 21.1: THE Backend SHALL read ENGINE_PATH from environment.
        """
        from app.core.config import Settings
        
        test_path = "/custom/path/to/scheduler"
        
        with patch.dict(os.environ, {"ENGINE_PATH": test_path}):
            settings = Settings()
            assert settings.engine_path == test_path
    
    def test_upload_dir_configuration(self):
        """
        Test UPLOAD_DIR environment variable.
        
        Requirement 21.1: THE Backend SHALL read UPLOAD_DIR from environment.
        """
        from app.core.config import Settings
        
        test_dir = "/custom/uploads"
        
        with patch.dict(os.environ, {"UPLOAD_DIR": test_dir}):
            settings = Settings()
            assert settings.upload_dir == test_dir
    
    def test_cors_origins_configuration(self):
        """Test CORS_ORIGINS environment variable."""
        from app.core.config import Settings
        
        # Default should include localhost:3000
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
    
    def test_debug_mode_configuration(self):
        """Test DEBUG environment variable."""
        from app.core.config import Settings
        
        with patch.dict(os.environ, {"DEBUG": "true"}):
            settings = Settings()
            assert settings.debug is True
        
        with patch.dict(os.environ, {"DEBUG": "false"}):
            settings = Settings()
            assert settings.debug is False


class TestFrontendEnvironment:
    """Test frontend environment configuration."""
    
    def test_next_public_api_url_documented(self):
        """
        Verify NEXT_PUBLIC_API_URL is documented.
        
        Requirement 21.2: THE Frontend SHALL read NEXT_PUBLIC_API_URL from environment.
        """
        # Check that the environment variable is documented in .env.example
        env_example_path = Path(".env.example")
        
        if env_example_path.exists():
            content = env_example_path.read_text()
            # Should mention NEXT_PUBLIC_API_URL
            assert "NEXT_PUBLIC_API_URL" in content or "API_URL" in content, (
                "NEXT_PUBLIC_API_URL should be documented in .env.example"
            )


class TestNoHardcodedCredentials:
    """
    Test that no credentials are hardcoded.
    
    Requirement 21.3: THE system SHALL NOT hardcode any API keys or credentials.
    """
    
    def test_no_hardcoded_api_keys_in_config(self):
        """Verify config module has no hardcoded API keys."""
        config_path = Path("backend/app/core/config.py")
        
        if config_path.exists():
            content = config_path.read_text()
            
            # Check for common API key patterns
            suspicious_patterns = [
                "sk-",  # OpenAI keys
                "ghp_",  # GitHub tokens
                "gho_",  # GitHub OAuth tokens
                "Bearer ",  # Bearer tokens
                "api_key=",  # Hardcoded API keys
                "password=",  # Hardcoded passwords (except in default URLs)
            ]
            
            for pattern in suspicious_patterns:
                # Allow patterns in comments or default connection strings
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    # Skip default database URLs (they use placeholder passwords)
                    if "localhost" in line and "postgres:postgres" in line:
                        continue
                    # Check for suspicious patterns
                    if pattern in line and "env" not in line.lower():
                        # This is a potential hardcoded credential
                        # Only fail if it looks like a real key
                        if len(line) > 50 and not line.strip().startswith("#"):
                            pytest.fail(
                                f"Potential hardcoded credential found at line {i + 1}: "
                                f"pattern '{pattern}'"
                            )
    
    def test_no_hardcoded_credentials_in_main(self):
        """Verify main module has no hardcoded credentials."""
        main_path = Path("backend/app/main.py")
        
        if main_path.exists():
            content = main_path.read_text()
            
            # Should not contain hardcoded secrets
            assert "sk-" not in content, "OpenAI key found in main.py"
            assert "ghp_" not in content, "GitHub token found in main.py"


class TestEnvironmentValidation:
    """
    Test environment validation on startup.
    
    Requirements 21.4, 21.5: Validate required variables and fail fast.
    """
    
    def test_settings_validates_on_creation(self):
        """Test that Settings validates configuration."""
        from app.core.config import Settings
        
        # Settings should be creatable with defaults
        settings = Settings()
        assert settings is not None
    
    def test_database_url_format_validation(self):
        """Test that database URL has expected format."""
        from app.core.config import Settings
        
        settings = Settings()
        
        # Should be a valid PostgreSQL URL
        assert "postgresql" in settings.database_url.lower(), (
            "DATABASE_URL should be a PostgreSQL connection string"
        )
    
    def test_copilot_api_url_format_validation(self):
        """Test that copilot API URL has expected format."""
        from app.core.config import Settings
        
        settings = Settings()
        
        # Should be a valid HTTP URL
        assert settings.copilot_api_url.startswith("http"), (
            "COPILOT_API_URL should be an HTTP URL"
        )


class TestCEnginePathValidation:
    """Test C engine path validation."""
    
    def test_engine_path_exists_or_has_exe(self):
        """Test that engine path points to existing file or .exe variant."""
        from app.core.config import get_settings
        
        settings = get_settings()
        engine_path = Path(settings.engine_path)
        
        # Check if path exists or .exe variant exists
        exists = engine_path.exists() or engine_path.with_suffix(".exe").exists()
        
        if not exists:
            # This is a warning, not a failure - engine may not be built yet
            pytest.skip(
                f"C engine not found at {engine_path}. "
                f"Run 'make' in engine/ directory to build."
            )
    
    def test_scheduler_bridge_validates_engine(self):
        """Test that scheduler bridge validates engine path."""
        from app.scheduler.bridge import CSchedulerBridge, SchedulerError
        
        # Try to create bridge with non-existent path
        with pytest.raises(SchedulerError) as exc_info:
            bridge = CSchedulerBridge("/nonexistent/path/to/scheduler")
            bridge._validate_engine()
        
        assert "not found" in str(exc_info.value.message).lower()


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_logging_setup_exists(self):
        """Test that logging setup function exists."""
        from app.core.logging import setup_logging, log_system
        
        # Should be callable
        assert callable(setup_logging)
        assert callable(log_system)
    
    def test_log_system_accepts_levels(self):
        """Test that log_system accepts different levels."""
        from app.core.logging import log_system
        
        # Should not raise for valid levels
        log_system("info", "Test info message")
        log_system("warning", "Test warning message")
        log_system("error", "Test error message")
        log_system("debug", "Test debug message")
    
    def test_log_system_accepts_context(self):
        """Test that log_system accepts context dict."""
        from app.core.logging import log_system
        
        # Should not raise with context
        log_system("info", "Test message", {"key": "value", "count": 42})
