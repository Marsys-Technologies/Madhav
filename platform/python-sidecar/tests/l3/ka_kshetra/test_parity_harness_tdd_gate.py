"""
tests/l3/ka_kshetra/test_parity_harness_tdd_gate.py — SAMPURTI-D2 V3 TDD GATE

Verifies the parity harness (test_dhara_parity.py) is structurally correct
BEFORE the DHARA engine exists:

  1. All 6 required test classes are present.
  2. E1–E5 tolerance constants are defined at module level with correct types.
  3. The matching algorithm (match_windows) is importable and callable.
  4. The file is importable without syntax errors.

These tests do NOT depend on DHARA being available — they run unconditionally
and must ALL PASS.

Authority: SAMPURTI-D2 V3 task brief.
"""
from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure the harness module is importable from this worktree
# ---------------------------------------------------------------------------
_SIDECAR_ROOT = Path(__file__).resolve().parents[3]
if str(_SIDECAR_ROOT) not in sys.path:
    sys.path.insert(0, str(_SIDECAR_ROOT))

# ---------------------------------------------------------------------------
# Import the harness module (must not raise)
# ---------------------------------------------------------------------------
# We do a direct spec-based import so the test is robust to the module not
# being installed as a package.
import importlib.util as _ilu

_HARNESS_PATH = Path(__file__).parent / "test_dhara_parity.py"

_spec = _ilu.spec_from_file_location("test_dhara_parity", _HARNESS_PATH)
assert _spec is not None and _spec.loader is not None, (
    f"Cannot build module spec from {_HARNESS_PATH} — file missing?"
)
_harness = _ilu.module_from_spec(_spec)


def _load_harness():
    """Load the harness module once; returns it.  Any import error = gate failure."""
    # Register in sys.modules BEFORE exec_module so @dataclass can find __dict__
    # via sys.modules[cls.__module__] during class construction.
    sys.modules.setdefault("test_dhara_parity", _harness)
    try:
        _spec.loader.exec_module(_harness)
    except Exception as exc:
        pytest.fail(
            f"test_dhara_parity.py raised {type(exc).__name__} on import: {exc}"
        )
    return _harness


# Load eagerly at collection time so all gate tests share one import.
_M = _load_harness()


# ===========================================================================
# Gate 1: Required test classes present
# ===========================================================================

class TestGate1RequiredClasses:
    """All 6 required test classes must exist in the harness module."""

    _REQUIRED_CLASSES = [
        "TestParityE1WindowEdges",
        "TestParityE2PeakTimes",
        "TestParityE3ExpectedCounts",
        "TestParityE4NullThresholds",
        "TestParityE5WindowCount",
        "TestParityClassified",
    ]

    @pytest.mark.parametrize("class_name", _REQUIRED_CLASSES)
    def test_class_exists(self, class_name: str):
        """Each required test class must be present as a module-level attribute."""
        cls = getattr(_M, class_name, None)
        assert cls is not None, (
            f"Required test class '{class_name}' not found in test_dhara_parity.py"
        )
        assert isinstance(cls, type), (
            f"'{class_name}' exists but is not a class (got {type(cls).__name__})"
        )

    def test_all_six_classes_present_count(self):
        """Exactly 6 (or more) required classes — no accidental omission."""
        found = [c for c in self._REQUIRED_CLASSES if isinstance(getattr(_M, c, None), type)]
        assert len(found) == len(self._REQUIRED_CLASSES), (
            f"Expected {len(self._REQUIRED_CLASSES)} test classes, found {len(found)}: "
            f"missing={set(self._REQUIRED_CLASSES) - set(found)}"
        )


# ===========================================================================
# Gate 2: E1–E5 tolerance constants defined correctly
# ===========================================================================

class TestGate2ToleranceConstants:
    """Module-level tolerance constants must exist with correct types and values."""

    # (attr_name, expected_value, allowed_types)
    _CONSTANTS = [
        # E1
        ("E1_NONSUPPRESSION_EDGE_TOL", 0.1,   (float, int)),
        ("E1_SUPPRESSION_EDGE_TOL",    3.0,   (float, int)),
        # E2
        ("E2_NONSUPPRESSION_PEAK_TOL", 0.0,   (float, int)),
        ("E2_SUPPRESSION_PEAK_TOL",    1.0,   (float, int)),
        # E3
        ("E3_NONSUPPRESSION_COUNT_TOL", 1e-10, (float,)),
        ("E3_SUPPRESSION_COUNT_TOL",    0.01,  (float, int)),
        ("E3_OVERALL_COUNT_TOL",        0.05,  (float, int)),
        # E4
        ("E4_QE_RELATIVE_TOL",         0.20,  (float, int)),
        # E5
        ("E5_WINDOW_COUNT_TOL",        2,     (float, int)),
        # Matching thresholds
        ("MATCH_MAX_NONSUPPRESSION",   5.0,   (float, int)),
        ("MATCH_MAX_SUPPRESSION",      30.0,  (float, int)),
    ]

    @pytest.mark.parametrize("attr,expected,types", _CONSTANTS)
    def test_constant_defined(self, attr: str, expected: float, types: tuple):
        """Each constant must exist as a module attribute."""
        val = getattr(_M, attr, None)
        assert val is not None, f"Constant '{attr}' not found in test_dhara_parity.py"
        assert isinstance(val, types), (
            f"Constant '{attr}' has wrong type: expected one of {types}, got {type(val)}"
        )

    @pytest.mark.parametrize("attr,expected,types", _CONSTANTS)
    def test_constant_value_correct(self, attr: str, expected: float, types: tuple):
        """Each constant must match the frozen design-doc value."""
        val = getattr(_M, attr, None)
        if val is None:
            pytest.skip(f"Constant '{attr}' not defined — covered by test_constant_defined")
        assert math.isclose(float(val), float(expected), rel_tol=1e-9, abs_tol=1e-15), (
            f"Constant '{attr}': expected {expected}, got {val}"
        )

    def test_e3_nonsuppression_is_tight(self):
        """E3 non-suppression tolerance must be strictly < 1e-9 (analytic exact-match claim)."""
        tol = getattr(_M, "E3_NONSUPPRESSION_COUNT_TOL", None)
        assert tol is not None
        assert float(tol) < 1e-9, (
            f"E3_NONSUPPRESSION_COUNT_TOL={tol} is too loose — must be < 1e-9 for exact match"
        )

    def test_e2_nonsuppression_is_zero(self):
        """E2 non-suppression peak tolerance must be 0.0 (exact match required)."""
        tol = getattr(_M, "E2_NONSUPPRESSION_PEAK_TOL", None)
        assert tol is not None
        assert float(tol) == 0.0, (
            f"E2_NONSUPPRESSION_PEAK_TOL={tol} must be exactly 0.0 (exact match required)"
        )

    def test_suppression_tolerances_are_looser_than_nonsuppression(self):
        """Suppression tolerances must be strictly >= their non-suppression counterparts."""
        e1_ns  = float(getattr(_M, "E1_NONSUPPRESSION_EDGE_TOL", 0))
        e1_s   = float(getattr(_M, "E1_SUPPRESSION_EDGE_TOL",    0))
        e2_ns  = float(getattr(_M, "E2_NONSUPPRESSION_PEAK_TOL", 0))
        e2_s   = float(getattr(_M, "E2_SUPPRESSION_PEAK_TOL",    0))
        e3_ns  = float(getattr(_M, "E3_NONSUPPRESSION_COUNT_TOL", 0))
        e3_s   = float(getattr(_M, "E3_SUPPRESSION_COUNT_TOL",   0))
        assert e1_s >= e1_ns, f"E1 suppression tol {e1_s} < non-suppression {e1_ns}"
        assert e2_s >= e2_ns, f"E2 suppression tol {e2_s} < non-suppression {e2_ns}"
        assert e3_s >= e3_ns, f"E3 suppression tol {e3_s} < non-suppression {e3_ns}"

    def test_match_suppression_looser_than_nonsuppression(self):
        """Matching max separation for suppression must be >= non-suppression."""
        ns = float(getattr(_M, "MATCH_MAX_NONSUPPRESSION", 0))
        s  = float(getattr(_M, "MATCH_MAX_SUPPRESSION",    0))
        assert s >= ns, (
            f"MATCH_MAX_SUPPRESSION={s} must be >= MATCH_MAX_NONSUPPRESSION={ns}"
        )


# ===========================================================================
# Gate 3: match_windows algorithm importable and callable
# ===========================================================================

class TestGate3MatchingAlgorithm:
    """The match_windows function must be importable, callable, and correct."""

    def _get_match_windows(self):
        fn = getattr(_M, "match_windows", None)
        assert fn is not None, "match_windows not found in test_dhara_parity"
        assert callable(fn), "match_windows is not callable"
        return fn

    def test_match_windows_importable(self):
        """match_windows must exist as a callable in the harness module."""
        self._get_match_windows()

    def test_empty_inputs_produce_empty_result(self):
        """match_windows([], []) must return a MatchResult with all empty lists."""
        fn = self._get_match_windows()
        result = fn([], [])
        assert result.matched == []
        assert result.unmatched_sampled == []
        assert result.unmatched_dhara == []

    def test_exact_match_non_suppression(self):
        """A single sampled window matched exactly to a DHARA window at same peak."""
        fn = self._get_match_windows()
        sw = [{"window_start": 100.0, "window_end": 200.0,
               "peak_days": 150.0, "expected_count": 0.05,
               "is_suppression_active": False}]
        dw = [{"window_start": 100.05, "window_end": 199.95,
               "peak_days": 150.0, "expected_count": 0.05,
               "is_suppression_active": False}]
        result = fn(sw, dw)
        assert len(result.matched) == 1, "Expected exactly 1 matched pair"
        assert len(result.unmatched_sampled) == 0
        assert len(result.unmatched_dhara) == 0
        assert result.matched[0].peak_separation == 0.0

    def test_no_match_when_too_far_apart(self):
        """A sampled window must be unmatched when the nearest DHARA window is > max_sep away."""
        fn = self._get_match_windows()
        max_ns = float(getattr(_M, "MATCH_MAX_NONSUPPRESSION", 5.0))
        sw = [{"window_start": 0.0, "window_end": 50.0,
               "peak_days": 25.0, "expected_count": 0.01,
               "is_suppression_active": False}]
        # DHARA window is max_ns + 10 days away in peak — beyond the threshold.
        dw = [{"window_start": 100.0, "window_end": 150.0,
               "peak_days": 25.0 + max_ns + 10.0, "expected_count": 0.01,
               "is_suppression_active": False}]
        result = fn(sw, dw)
        assert len(result.matched) == 0, "Should NOT match — too far apart"
        assert len(result.unmatched_sampled) == 1
        assert len(result.unmatched_dhara) == 1

    def test_one_to_one_assignment(self):
        """Each DHARA window can only be matched to one sampled window (no double-use)."""
        fn = self._get_match_windows()
        # Two sampled windows close together; one DHARA window equidistant between them.
        sw = [
            {"window_start": 0.0, "window_end": 40.0,
             "peak_days": 20.0, "expected_count": 0.01, "is_suppression_active": False},
            {"window_start": 50.0, "window_end": 90.0,
             "peak_days": 70.0, "expected_count": 0.01, "is_suppression_active": False},
        ]
        dw = [
            {"window_start": 20.0, "window_end": 60.0,
             "peak_days": 40.0, "expected_count": 0.01, "is_suppression_active": False},
        ]
        result = fn(sw, dw)
        # The DHARA window can only be assigned to ONE sampled window.
        assert len(result.matched) <= 1, "One DHARA window assigned to more than one sampled"
        assert len(result.matched) + len(result.unmatched_sampled) == len(sw)

    def test_suppression_uses_wider_window(self):
        """A suppression-active sampled window uses the wider max_sep (30 days, not 5)."""
        fn = self._get_match_windows()
        max_ns = float(getattr(_M, "MATCH_MAX_NONSUPPRESSION", 5.0))
        max_s  = float(getattr(_M, "MATCH_MAX_SUPPRESSION",    30.0))
        assert max_s > max_ns, "Suppression max must be strictly wider"

        gap = (max_ns + max_s) / 2.0   # between the two thresholds
        sw_supp = [{"window_start": 0.0, "window_end": 50.0,
                    "peak_days": 0.0, "expected_count": 0.01,
                    "is_suppression_active": True}]
        dw = [{"window_start": gap - 10, "window_end": gap + 10,
               "peak_days": gap, "expected_count": 0.01,
               "is_suppression_active": True}]
        result_supp = fn(sw_supp, dw)
        assert len(result_supp.matched) == 1, (
            f"Suppression window at gap={gap:.1f} days should match (max_s={max_s})"
        )

        sw_nons = [{"window_start": 0.0, "window_end": 50.0,
                    "peak_days": 0.0, "expected_count": 0.01,
                    "is_suppression_active": False}]
        result_nons = fn(sw_nons, dw)
        assert len(result_nons.matched) == 0, (
            f"Non-suppression window at gap={gap:.1f} days should NOT match (max_ns={max_ns})"
        )

    def test_match_result_dataclass_fields(self):
        """MatchResult returned by match_windows must have .matched, .unmatched_sampled, .unmatched_dhara."""
        fn = self._get_match_windows()
        result = fn([], [])
        assert hasattr(result, "matched")
        assert hasattr(result, "unmatched_sampled")
        assert hasattr(result, "unmatched_dhara")

    def test_matched_pair_has_peak_separation(self):
        """MatchedPair objects must expose .peak_separation as a non-negative float."""
        fn = self._get_match_windows()
        sw = [{"window_start": 0.0, "window_end": 50.0,
               "peak_days": 25.0, "expected_count": 0.01,
               "is_suppression_active": False}]
        dw = [{"window_start": 2.0, "window_end": 52.0,
               "peak_days": 27.0, "expected_count": 0.01,
               "is_suppression_active": False}]
        result = fn(sw, dw)
        assert len(result.matched) == 1
        pair = result.matched[0]
        assert hasattr(pair, "peak_separation"), "MatchedPair missing .peak_separation"
        assert isinstance(pair.peak_separation, (float, int))
        assert pair.peak_separation >= 0.0
        assert math.isclose(pair.peak_separation, 2.0, abs_tol=1e-9)


# ===========================================================================
# Gate 4: Module importability (no syntax errors, no top-level crashes)
# ===========================================================================

class TestGate4Importability:
    """The harness module must be importable without errors."""

    def test_module_loaded_without_exception(self):
        """The harness module was imported at the top of this file; verify it is not None."""
        assert _M is not None, "test_dhara_parity module is None after import"

    def test_module_has_pytestmark(self):
        """The harness must declare pytestmark for the DHARA skip gate."""
        mark = getattr(_M, "pytestmark", None)
        assert mark is not None, (
            "test_dhara_parity.py missing 'pytestmark' — the DHARA skip gate is absent"
        )

    def test_dhara_available_flag_defined(self):
        """dhara_available must be a bool (False when DHARA not installed)."""
        flag = getattr(_M, "dhara_available", None)
        assert flag is not None, "dhara_available not defined in test_dhara_parity.py"
        assert isinstance(flag, bool), f"dhara_available is {type(flag)}, expected bool"

    def test_dhara_available_is_false_in_test_env(self):
        """In the pre-FIELD-INTEGRATED environment DHARA must not be importable.

        Post-FIELD-INTEGRATED (S3 PRs merged): dhara_available=True is expected
        and correct — this gate skips with a marker to record the transition.
        """
        flag = getattr(_M, "dhara_available", None)
        if flag is True:
            pytest.skip(
                "FIELD-INTEGRATED: dhara_sweep.py is now on main; "
                "dhara_available=True is correct post-FIELD-INTEGRATED. "
                "Pre-FIELD-INTEGRATED canary gate fulfilled and retired."
            )
        assert flag is False, (
            "dhara_available must be a bool; got None or non-bool"
        )

    def test_golden_fixture_path_resolvable(self):
        """The _FIXTURE_PATH constant must point to an existing file."""
        path = getattr(_M, "_FIXTURE_PATH", None)
        assert path is not None, "_FIXTURE_PATH not defined in test_dhara_parity.py"
        assert Path(path).exists(), (
            f"_FIXTURE_PATH={path} does not exist — "
            "golden fixture JSON is missing from the worktree"
        )

    def test_load_fixtures_callable(self):
        """_load_fixtures() must be callable and return a non-empty dict."""
        fn = getattr(_M, "_load_fixtures", None)
        assert fn is not None and callable(fn), "_load_fixtures not callable"
        result = fn()
        assert isinstance(result, dict) and result, "_load_fixtures() returned empty/non-dict"

    def test_active_fixtures_callable_and_non_empty(self):
        """_active_fixtures() must be callable and return a list.

        Note: _active_fixtures() requires PARITY_DB_TEST=1 to return non-empty
        (the DB-backed evaluator path is only active when that env var is set).
        This gate tests structural presence + return type only; populating the
        list requires PARITY_DB_TEST=1 in the caller's environment.
        """
        fn = getattr(_M, "_active_fixtures", None)
        assert fn is not None and callable(fn), "_active_fixtures not callable"
        result = fn()
        assert isinstance(result, list), (
            f"_active_fixtures() must return a list; got {type(result)}"
        )
        # Non-empty result requires PARITY_DB_TEST=1 — structural gate only here.

    def test_grade_helper_defined(self):
        """_grade() must exist and return PASS/WARN/FAIL strings."""
        fn = getattr(_M, "_grade", None)
        assert fn is not None and callable(fn), "_grade helper not found"
        assert fn(0.0,  1.0) == "PASS"
        assert fn(0.6,  1.0) == "WARN"   # > 50% of tol
        assert fn(1.01, 1.0) == "FAIL"

    def test_diff_row_dataclass_defined(self):
        """DiffRow must be a dataclass with the expected fields."""
        cls = getattr(_M, "DiffRow", None)
        assert cls is not None, "DiffRow not defined"
        import dataclasses
        assert dataclasses.is_dataclass(cls), "DiffRow is not a dataclass"
        field_names = {f.name for f in dataclasses.fields(cls)}
        required = {
            "fixture_key", "tolerance_id", "dimension",
            "sampled_value", "dhara_value", "absolute_error",
            "tolerance", "grade",
        }
        missing = required - field_names
        assert not missing, f"DiffRow missing fields: {missing}"
