# This test runs as part of the standard pytest suite: pytest platform/python-sidecar/
"""
CI guard: NATIVE_BIRTH contamination class.

Tests that:
1. resolve_birth_params() raises for ANY chart (native included) with falsy params.
2. No writer file contains vulnerable NATIVE_BIRTH fallback patterns (bare assignment,
   or-fallback, ternary, dict.get default, unconditional spread, etc.).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # tests/ → python-sidecar/ → platform/ → project root

import pytest

from pipeline.orchestrator.birth_params import (
    resolve_birth_params,
)

# Canonical native chart ID — used only in this test fixture.
_NATIVE = "482012f1-710e-4a25-994a-93821f5871aa"
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
# resolve_birth_params() unit tests (B1 elimination — native has no special case)
# ---------------------------------------------------------------------------


def test_resolve_native_none_raises():
    """B1: native chart + None birth_params → ValueError (no NATIVE_BIRTH fallback for anyone)."""
    with pytest.raises(ValueError):
        resolve_birth_params(_NATIVE, None)


def test_resolve_native_empty_dict_raises():
    """B1: native chart + empty dict → ValueError (same rule as any other chart)."""
    with pytest.raises(ValueError):
        resolve_birth_params(_NATIVE, {})


def test_resolve_native_valid_params_passthrough():
    """Native chart + valid dict → returns the dict unchanged (DB-sourced params work normally)."""
    result = resolve_birth_params(_NATIVE, _VALID_PARAMS)
    assert result is _VALID_PARAMS


def test_resolve_non_native_valid_params_passthrough():
    """Non-native chart + valid dict → returns the dict unchanged."""
    result = resolve_birth_params(_NON_NATIVE, _VALID_PARAMS)
    assert result is _VALID_PARAMS


def test_resolve_non_native_none_raises():
    """Non-native chart + None → ValueError (no silent fallback)."""
    with pytest.raises(ValueError):
        resolve_birth_params(_NON_NATIVE, None)


def test_resolve_non_native_empty_dict_raises():
    """Non-native chart + empty dict → ValueError (no silent fallback)."""
    with pytest.raises(ValueError):
        resolve_birth_params(_NON_NATIVE, {})


# ---------------------------------------------------------------------------
# Grep-based structural guard
# ---------------------------------------------------------------------------

# Each entry is (label, grep_flag, pattern, description).
# grep_flag is either "-En" (extended regex) or "-Fn" (fixed string).
# Files excluded from scanning:
#   - test_contamination_guard.py : this file (contains patterns as string literals)
#   - birth_params.py             : the solution module; may mention NATIVE_BIRTH in comments
#                                   (not in executable code after B1 elimination).
# Test files (tests/) are scanned because a test helper that hard-codes NATIVE_BIRTH
# as a default parameter is itself a contamination vector.
#
# Pattern coverage (Wave 2 extended guard + Wave 2 carryover + Group 9 B1 elimination):
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
#
#   Group 6 — local-alias native birth fallback in .get() default or or-expression:
#     `.get("datetime_iso") or BIRTH_IST`
#     `.get("latitude_deg", BIRTH_LAT)` / `.get("longitude_deg", BIRTH_LON)`
#     Matches only when BIRTH_* appears as a .get() default or after `or`.
#     Does NOT match legitimate positional args like panchanga_instant(..., BIRTH_LAT, ...).
#     These patterns let native constants silently leak into non-native builds.
#
#   Group 7 — unconditional NATIVE_BIRTH spread:
#     `{**NATIVE_BIRTH}` — spreads the native birth dict without chart_id routing.
#
#   Group 8 — hardcoded native birth year 1984 as NULL-guard fallback:
#     `else 1984` or `return 1984` — silently substitutes native birth year.
#
#   Group 9 — bare NATIVE_BIRTH reference (B1 elimination, added this PR):
#     Any bare occurrence of the token `NATIVE_BIRTH` in writer / pipeline code.
#     After B1 elimination, the constant must not exist in any executable writer code.

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
    # Group 6 — local-alias native birth fallback in .get() default or or-expression
    # Matches patterns like:
    #   .get("key", BIRTH_LAT)  / .get("key", BIRTH_LON)  / .get("key") or BIRTH_IST
    # Does NOT match positional-argument calls like panchanga_instant(..., BIRTH_LAT, ...)
    # because those use BIRTH_LAT without .get() context and the pattern requires
    # the `or` keyword or the `.get(` prefix on the same line.
    (
        "local-alias native birth fallback (BIRTH_IST/LAT/LON in .get or or-expr)",
        True,
        r"(\.get\([^)]*,\s*BIRTH_(LAT|LON|IST)|or BIRTH_(IST|LAT|LON))",
        "Replace local-alias native-birth fallback with resolve_birth_params().",
    ),
    # Group 7 — unconditional native birth spread
    (
        "unconditional NATIVE_BIRTH spread",
        True,
        r"\{\*\*NATIVE_BIRTH\}",
        "Unconditional {**NATIVE_BIRTH} spread ignores chart_id routing; use resolve_birth_params() instead.",
    ),
    # Group 8 — hardcoded native birth year as NULL-guard fallback
    # Catches: `else 1984` or `return 1984` used as a fallback when upstream data is None.
    # Shape found in Wave 4 (ka_jivana_parva line 44): `start_y = start_dt.year if start_dt else 1984`
    # silently substitutes the native birth year for non-native charts with NULL dasha rows.
    # Does NOT catch comparison operators (>= 1984, <= 1984) or tuple unpacking (Y, M, D = 1984, 2, 5).
    (
        "hardcoded native birth year as NULL-guard fallback (else/return 1984)",
        True,
        r"(else\s+1984\b|return\s+1984\b)",
        "Replace hardcoded native birth year 1984 with None/unknown; "
        "never silently substitute native birth year for non-native charts.",
    ),
    # Group 9 — bare NATIVE_BIRTH (exact token, not NATIVE_BIRTH_DATE/_IST/_NAKSHATRA etc.)
    # After B1 elimination, NATIVE_BIRTH (the birth-params constant) must not appear
    # in any ga_* writer, orchestrator shim, or rebuild script as executable code.
    # The L0 brahmagyan/ files use NATIVE_BIRTH_DATE, NATIVE_BIRTH_IST etc. which are
    # different variables (date/string scalars) — those are excluded via the negative
    # lookahead (match NATIVE_BIRTH not followed by _ or alphanumeric continuation).
    (
        "bare NATIVE_BIRTH dict constant in writer code (B1 elimination)",
        True,
        r"NATIVE_BIRTH(?!_[A-Z])",
        "NATIVE_BIRTH dict constant must not appear in ga_* writers, orchestrator shims, "
        "or rebuild scripts. Every chart (native included) must use fetch_birth_params() / "
        "resolve_birth_params(). Remove the constant definition and all assignment uses.",
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
    CI guard: NATIVE_BIRTH contamination class — extended Wave 2 + carryover + Group 9 B1.

    Scans all .py files under platform/python-sidecar/ (excluding venv, __pycache__,
    this test file, and birth_params.py which may mention NATIVE_BIRTH in comments only).

    Covered shapes:
      Group 1 — or-fallback assignments  (= birth_params|bp or NATIVE_*)
      Group 2 — ternary fallbacks        (X if X else NATIVE_*)
      Group 3 — dict.get() defaults      (.get('birth_params', NATIVE_BIRTH))
      Group 4 — signature defaults       (def f(chart_id = CANONICAL_CHART_ID))
      Group 5 — generic or NATIVE_BIRTH  ((=|return).*or NATIVE_BIRTH)
      Group 6 — local-alias BIRTH_IST/LAT/LON fallbacks (dict.get with native constants)
      Group 7 — unconditional {**NATIVE_BIRTH} spread (ignores chart_id routing)
      Group 8 — hardcoded native birth year 1984 as NULL-guard fallback (else/or/= 1984)
      Group 9 — bare NATIVE_BIRTH token in writer code (B1 elimination — zero tolerance)

    Every hit is a bug requiring remediation via resolve_birth_params() /
    fetch_birth_params() — never a silent fallback to native birth data.
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
        "Each site below must use fetch_birth_params() / resolve_birth_params() — "
        "no hardcoded native-birth fallback anywhere in the stack (Groups 1-9):\n"
        + "\n".join(failures)
    )
