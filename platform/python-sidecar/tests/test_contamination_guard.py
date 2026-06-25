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

# Each entry is (label, grep_flag, pattern, description).
# grep_flag is either "-En" (extended regex) or "-Fn" (fixed string).
# Files excluded from scanning:
#   - test_contamination_guard.py : this file (contains patterns as string literals)
#   - birth_params.py             : the SOLUTION module; legitimately references NATIVE_BIRTH
#                                   in the guard implementation itself.
# Test files (tests/) are scanned because a test helper that hard-codes NATIVE_BIRTH
# as a default parameter is itself a contamination vector.
#
# Pattern coverage (Wave 2 extended guard):
#
#   Group 1 — or-fallback assignments:
#     `= birth_params or NATIVE_*`   e.g. bp = birth_params or NATIVE_BIRTH
#     `= bp or NATIVE_*`             shorter alias form
#
#   Group 2 — ternary / if-else forms:
#     `birth_params if birth_params else NATIVE_*`
#     `bp if bp else NATIVE_*`
#
#   Group 3 — dict.get() with NATIVE_BIRTH as the default argument (2nd positional arg):
#     `.get('birth_params', NATIVE_BIRTH)` / `.get("birth_params", NATIVE_BIRTH)`
#     Excludes comment-only matches (pattern requires the comma before NATIVE_BIRTH,
#     so a trailing comment mentioning NATIVE_BIRTH without the comma is not caught).
#
#   Group 4 — function signature defaults (CANONICAL_CHART_ID hardcoded):
#     `def ... chart_id ... = CANONICAL_CHART_ID`
#     Excludes equality comparisons (`==`) — those are safe native-routing guards.
#
#   Group 5 — generic fallback to NATIVE_BIRTH in any assignment or return:
#     `(= | return) ... or NATIVE_BIRTH`
#     Catches any remaining form not already covered by groups 1/2/3.

_SIDECAR_DIR = _PROJECT_ROOT / "platform" / "python-sidecar"

_GREP_COMMON_ARGS = [
    "--include=*.py",
    "--exclude-dir=venv",
    "--exclude-dir=__pycache__",
    "--exclude=test_contamination_guard.py",
    "--exclude=birth_params.py",
]

# (label, use_extended_regex, pattern, remediation_hint)
VULNERABLE_PATTERNS = [
    (
        "or-fallback assignment",
        True,
        r"= (birth_params|bp) or NATIVE_",
        "Replace `bp = birth_params or NATIVE_BIRTH` with `resolve_birth_params(chart_id, birth_params)`.",
    ),
    (
        "ternary native fallback",
        True,
        r"(birth_params|bp) if (birth_params|bp) else NATIVE_",
        "Replace ternary fallback to NATIVE_* with resolve_birth_params().",
    ),
    (
        "dict.get native default",
        True,
        r"\.get\(['\"]birth_params['\"],\s*NATIVE_BIRTH",
        "Never pass NATIVE_BIRTH as a .get() default; use resolve_birth_params() instead.",
    ),
    (
        "chart_id default param = CANONICAL_CHART_ID",
        True,
        r"def .+chart_id.+=\s*CANONICAL_CHART_ID",
        "Function signature defaults to CANONICAL_CHART_ID hard-wire native routing; "
        "require callers to pass chart_id explicitly.",
    ),
    (
        "generic or NATIVE_BIRTH",
        True,
        r"(=|return).*or NATIVE_BIRTH",
        "Any `or NATIVE_BIRTH` fallback in an assignment or return is a silent native contamination. "
        "Use resolve_birth_params() instead.",
    ),
]


def _run_grep(use_extended: bool, pattern: str) -> subprocess.CompletedProcess:
    flag = "-Ern" if use_extended else "-Frn"
    return subprocess.run(
        ["grep", flag, pattern, str(_SIDECAR_DIR)] + _GREP_COMMON_ARGS,
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )


def test_no_raw_native_birth_fallback():
    """
    CI guard: NATIVE_BIRTH contamination class — extended Wave 2 pattern set.

    Scans all .py files under platform/python-sidecar/ (excluding venv, __pycache__,
    this test file, and birth_params.py which is the approved implementation).

    Covered shapes:
      Group 1 — or-fallback assignments  (= birth_params|bp or NATIVE_*)
      Group 2 — ternary fallbacks        (X if X else NATIVE_*)
      Group 3 — dict.get() defaults      (.get('birth_params', NATIVE_BIRTH))
      Group 4 — signature defaults       (def f(chart_id = CANONICAL_CHART_ID))
      Group 5 — generic or NATIVE_BIRTH  ((=|return).*or NATIVE_BIRTH)

    Every hit is a bug requiring remediation via resolve_birth_params() or an
    explicit chart_id argument — never a silent fallback to native birth data.
    """
    failures: list[str] = []

    for label, use_extended, pattern, hint in VULNERABLE_PATTERNS:
        result = _run_grep(use_extended, pattern)
        if result.stdout.strip():
            failures.append(
                f"\n[{label}] pattern: {pattern!r}\n"
                f"  Hint: {hint}\n"
                f"  Matches:\n"
                + "\n".join(f"    {line}" for line in result.stdout.strip().splitlines())
            )

    assert not failures, (
        "Found VULNERABLE NATIVE_BIRTH / CANONICAL_CHART_ID contamination patterns.\n"
        "Each site below must use resolve_birth_params() or accept chart_id explicitly:\n"
        + "\n".join(failures)
    )
