# This test runs as part of the standard pytest suite: pytest platform/python-sidecar/
"""
CI guard: NATIVE_BIRTH contamination class.

Tests that:
1. resolve_birth_params() correctly implements the 3-way guard.
2. No writer file contains the vulnerable 'birth_params or NATIVE_BIRTH' silent-fallback pattern.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # tests/ → python-sidecar/ → platform/ → project root

import pytest

from pipeline.orchestrator.birth_params import (
    CANONICAL_CHART_ID,
    resolve_birth_params,
)

_NON_NATIVE = "00000000-0000-0000-0000-000000000001"
_VALID_PARAMS = {
    "datetime_iso": "1990-01-01T12:00:00",
    "latitude_deg": 20.0,
    "longitude_deg": 85.0,
    "tz_offset_hours": 5.5,
    "place_name": "Test",
    "subject_label": "Test Chart",
}


# ---------------------------------------------------------------------------
# resolve_birth_params() unit tests
# ---------------------------------------------------------------------------


def test_resolve_native_none_returns_none():
    """Native chart + None birth_params → None (writer uses its NATIVE_BIRTH constant)."""
    assert resolve_birth_params(CANONICAL_CHART_ID, None) is None


def test_resolve_native_empty_dict_returns_none():
    """Native chart + empty dict → None (same signal)."""
    assert resolve_birth_params(CANONICAL_CHART_ID, {}) is None


def test_resolve_non_native_valid_params_passthrough():
    """Non-native chart + valid dict → returns the dict unchanged."""
    result = resolve_birth_params(_NON_NATIVE, _VALID_PARAMS)
    assert result is _VALID_PARAMS


def test_resolve_non_native_none_raises():
    """Non-native chart + None → ValueError (no silent fallback)."""
    with pytest.raises(ValueError, match="refusing NATIVE_BIRTH fallback"):
        resolve_birth_params(_NON_NATIVE, None)


def test_resolve_non_native_empty_dict_raises():
    """Non-native chart + empty dict → ValueError (no silent fallback)."""
    with pytest.raises(ValueError, match="refusing NATIVE_BIRTH fallback"):
        resolve_birth_params(_NON_NATIVE, {})


# ---------------------------------------------------------------------------
# Grep-based structural guard
# ---------------------------------------------------------------------------


def test_no_raw_native_birth_fallback():
    """Ensure no writer uses `= birth_params or NATIVE_BIRTH` (silent fallback assignment)."""
    # Pattern matches the vulnerable assignment form (e.g. `bp = birth_params or NATIVE_BIRTH`)
    # but NOT comments or docstrings that mention the pattern by name.
    result = subprocess.run(
        [
            "grep",
            "-rn",
            "= birth_params or NATIVE_BIRTH",
            str(_PROJECT_ROOT / "platform" / "python-sidecar"),
            "--include=*.py",
            "--exclude-dir=venv",
            "--exclude-dir=__pycache__",
            "--exclude=test_contamination_guard.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )
    assert result.stdout == "", (
        f"Found VULNERABLE assignment 'birth_params or NATIVE_BIRTH' in:\n{result.stdout}\n"
        "Use resolve_birth_params() instead."
    )
