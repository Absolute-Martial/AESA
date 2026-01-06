"""Pytest configuration and fixtures for AESA backend tests."""

import pytest
from datetime import datetime, time, timedelta


@pytest.fixture
def sample_date() -> datetime:
    """Provide a sample date for testing."""
    return datetime(2025, 12, 29, 0, 0, 0)


@pytest.fixture
def day_start(sample_date: datetime) -> datetime:
    """Provide a typical day start time (7:00 AM)."""
    return sample_date.replace(hour=7, minute=0)


@pytest.fixture
def day_end(sample_date: datetime) -> datetime:
    """Provide a typical day end time (11:00 PM)."""
    return sample_date.replace(hour=23, minute=0)
