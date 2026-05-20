"""
conftest.py — pytest fixtures for panchang_engine tests.
"""
import pytest
from datetime import date


@pytest.fixture
def bhubaneswar():
    """Standard Bhubaneswar location fixture."""
    return {
        "lat": 20.27,
        "lon": 85.84,
        "tz_offset": 330,  # IST +05:30
        "name": "Bhubaneswar, Odisha, India",
    }


@pytest.fixture
def reference_date():
    """Reference date: 2026-05-19 (today — known Drik anchor)."""
    return date(2026, 5, 19)


@pytest.fixture
def j2000():
    """Julian Day for J2000 (2000-01-01 12:00 TT)."""
    return 2451545.0
