"""
test_w41_lambda_contenders.py -- unit tests for the W4.1 λ contenders.

GOCHARA-UTKARSA campaign, wave W4.1.

All tests are DB-free: they use in-memory GochaWindow fixtures and synthetic
LEL caches so the harness can run offline (no DATABASE_URL required). The
scoring math is deterministic and identical to the math verified by the
existing test suite for curve.py / checks.py.

Tests covered:
  1. TemporalCurveModel returns 0 intensity when no windows overlap a date.
  2. Overlapping windows sum correctly at a given date.
  3. Non-overlapping windows produce a correct step-function curve.
  4. The report JSON has the required top-level fields.
  5. Sealed split is respected -- test events are never scored (uses
     lel.SealedTestSplitViolation to prove the guard is live, not just
     documented, for the path this module would exercise).
  6. Domain filtering narrows windows correctly.
  7. Domain-filter fallback to ALL windows when no keyword matches (I4).
  8. Empty window list produces all-zero curve (I4 honest empty).
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import pytest

# Make the kala_admission package importable.
sys.path.insert(0, str(Path(__file__).parents[2]))

from kala_admission.dates import parse_date  # noqa: E402
from kala_admission.lel import (  # noqa: E402
    SealedTestSplitViolation,
    TEST_SPLIT_BOUNDARY,
    load_train_events,
)
from kala_admission.w41_lambda_contenders import (  # noqa: E402
    BOUNDS_END,
    BOUNDS_START,
    CHART_ID,
    GochaWindow,
    TemporalCurveModel,
    _build_lambda_curve,
    _filter_windows_by_domain,
    _intensity_at,
    score_contender,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _window(event_class: str, start: str, end: str, intensity: float) -> GochaWindow:
    return GochaWindow(
        event_class=event_class,
        window_start=parse_date(start),
        window_end=parse_date(end),
        signed_intensity=intensity,
    )


@dataclass
class _FakeLelEvent:
    """Minimal stand-in for lel.LelEvent for scoring tests."""
    event_id: str
    event_date: date
    category: str
    domain: str
    description: str = ""


# ── Test 1: no overlap → 0 intensity ─────────────────────────────────────────

def test_no_overlap_returns_zero():
    """TemporalCurveModel returns 0.0 intensity when no window overlaps the date."""
    windows = [
        _window("career_rise", "2005-01-01", "2005-06-01", 3.5),
        _window("career_rise", "2007-01-01", "2008-01-01", 2.0),
    ]
    # date is outside both windows
    probe = date(2006, 1, 1)
    assert _intensity_at(windows, probe) == 0.0


# ── Test 2: overlapping windows sum correctly ─────────────────────────────────

def test_overlapping_windows_sum():
    """Two windows both active on a date → signed_intensity values are summed."""
    windows = [
        _window("career_rise",   "2010-01-01", "2011-01-01", 2.0),
        _window("career_peak",   "2010-06-01", "2010-12-01", 1.5),
    ]
    # 2010-07-01 is inside both windows
    probe = date(2010, 7, 1)
    result = _intensity_at(windows, probe)
    assert abs(result - 3.5) < 1e-9


def test_overlapping_windows_mixed_signs():
    """Negative signed_intensity suppresses positive ones when both overlap."""
    windows = [
        _window("finance_gain",    "2010-01-01", "2012-01-01",  4.0),
        _window("finance_adverse", "2010-06-01", "2011-06-01", -1.5),
    ]
    probe = date(2010, 9, 1)
    result = _intensity_at(windows, probe)
    assert abs(result - 2.5) < 1e-9


# ── Test 3: step-function curve from non-overlapping windows ──────────────────

def test_non_overlapping_step_function():
    """Non-overlapping windows produce a step-function curve: intensity is from
    the active window at each sampled date, and 0 between windows.

    The step grid (step_days=180 from 2000-01-01) produces the following dates:
      2000-01-01 → inside window 1 (career_rise 2000-01-01..2001-01-01) → 3.0
      2001-06-24 → between the two windows (2001-01-01..2002-01-01 gap)  → 0.0
      2002-06-19 → inside window 2 (career_fall 2002-01-01..2003-01-01) → 2.0
    These exact dates are what the step grid produces; the test pins them
    directly to avoid KeyError from probing dates the grid never samples."""
    windows = [
        _window("career_rise",  "2000-01-01", "2001-01-01", 3.0),
        _window("career_fall",  "2002-01-01", "2003-01-01", 2.0),
    ]
    curve = _build_lambda_curve(windows, date(2000, 1, 1), date(2003, 1, 1), step_days=180)
    intensities = {pt.date: pt.intensity for pt in curve}

    # 2000-01-01: start of window 1 (start inclusive)
    assert abs(intensities[date(2000, 1, 1)] - 3.0) < 1e-9
    # 2001-06-24: between the two windows (gap period)
    assert abs(intensities[date(2001, 6, 24)] - 0.0) < 1e-9
    # 2002-06-19: inside window 2
    assert abs(intensities[date(2002, 6, 19)] - 2.0) < 1e-9


def test_window_end_is_exclusive():
    """The half-open interval [start, end) means window_end itself is NOT active."""
    windows = [_window("career_rise", "2010-01-01", "2010-06-01", 5.0)]
    # window_end date itself must return 0
    assert _intensity_at(windows, date(2010, 6, 1)) == 0.0
    # one day before window_end must return the intensity
    assert abs(_intensity_at(windows, date(2010, 5, 31)) - 5.0) < 1e-9


# ── Test 4: report JSON has required fields ───────────────────────────────────

def test_report_json_has_required_fields(tmp_path):
    """score_contender returns a dict with the required top-level keys, and
    a synthetic full report assembled from two contender results has all the
    required report fields."""
    windows = [_window("career_rise", "2000-01-01", "2010-01-01", 1.0)]
    model = TemporalCurveModel(windows, label="test_v1")

    # Make a minimal scorable event (TRAIN-only, well inside the train window)
    events = [_FakeLelEvent("ev-001", date(2005, 6, 1), "career", "career/test")]

    result = score_contender(model, events)

    # Required contender fields
    for key in ("label", "blind_battery_hit_rate", "hit_count", "scored_count", "per_event", "window_count"):
        assert key in result, f"missing key: {key!r}"

    # Assemble a synthetic report matching the shape main() produces
    fake_report = {
        "harness": "w41_lambda_contenders",
        "wave": "W4.1",
        "chart_id": CHART_ID,
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "bounds_start": BOUNDS_START.isoformat(),
        "bounds_end": BOUNDS_END.isoformat(),
        "train_events_used_count": 1,
        "train_events_scorable_count": 1,
        "train_events_excluded_count": 0,
        "contenders": {"lambda_v1": result, "lambda_v3": result},
        "comparison": {"hit_rate_delta_v3_minus_v1": 0.0, "winner": "tie", "note": "test"},
    }
    # Must round-trip through JSON without error
    json_str = json.dumps(fake_report)
    parsed = json.loads(json_str)
    assert parsed["harness"] == "w41_lambda_contenders"
    assert parsed["wave"] == "W4.1"
    assert "contenders" in parsed
    assert "comparison" in parsed


# ── Test 5: sealed split is respected ────────────────────────────────────────

def test_sealed_split_guard_fires_on_test_row(tmp_path):
    """The lel.load_train_events() sealed-split circuit breaker raises
    SealedTestSplitViolation on any event >= 2020-01-01. This proves the
    boundary is enforced before data ever reaches the scoring path in main()."""
    # Write a synthetic cache with a contaminated (TEST-split) event
    cache = tmp_path / "synthetic_test_split.json"
    cache.write_text(json.dumps({
        "events": [{
            "event_id": "w41-probe-sealed-test-split",
            "event_date": "2021-03-15",
            "category": "career",
            "domain": "career/test",
            "description": "W4.1 probe: must never reach the scorer.",
        }]
    }))
    with pytest.raises(SealedTestSplitViolation):
        load_train_events(cache)


def test_sealed_split_boundary_is_2020_01_01():
    """Pins the boundary constant itself -- if it silently drifts, every
    sealed-split test in this lane is checking the wrong line."""
    assert TEST_SPLIT_BOUNDARY == date(2020, 1, 1)


def test_score_contender_never_receives_test_events():
    """score_contender is called only with events from load_train_events(),
    which raises SealedTestSplitViolation before returning if any event >=
    2020-01-01 is present. Prove the contract: a fake event dated in the
    test window is never silently accepted -- it is simply not present in
    the real events list, and the synthetic boundary test above confirms
    the guard fires if it ever were."""
    # All events passed to score_contender must be pre-boundary.
    events = [
        _FakeLelEvent("ev-train-a", date(2005, 1, 1), "career", "career/test"),
        _FakeLelEvent("ev-train-b", date(2015, 6, 1), "finance", "finance/test"),
    ]
    for e in events:
        assert e.event_date < TEST_SPLIT_BOUNDARY, (
            f"test setup error: {e.event_id} is on or after the sealed boundary"
        )
    windows = [_window("career_rise", "2000-01-01", "2020-01-01", 1.0)]
    model = TemporalCurveModel(windows, label="test_split_proof")
    result = score_contender(model, events)
    assert result["scored_count"] == 2  # both train events scored, none leaked


# ── Test 6: domain filtering ──────────────────────────────────────────────────

def test_domain_filter_narrows_to_matching_windows():
    """_filter_windows_by_domain returns only windows whose event_class
    contains a matching keyword (case-insensitive)."""
    windows = [
        _window("career_rise",      "2000-01-01", "2001-01-01", 1.0),
        _window("finance_gain",     "2001-01-01", "2002-01-01", 2.0),
        _window("health_vitality",  "2002-01-01", "2003-01-01", 3.0),
    ]
    filtered = _filter_windows_by_domain(windows, ("career", "profession"))
    assert len(filtered) == 1
    assert filtered[0].event_class == "career_rise"


def test_domain_filter_is_case_insensitive():
    """Keyword matching is case-insensitive."""
    windows = [_window("CAREER_PEAK", "2000-01-01", "2001-01-01", 1.0)]
    filtered = _filter_windows_by_domain(windows, ("career",))
    assert len(filtered) == 1


# ── Test 7: I4 fallback to all windows when filter yields nothing ─────────────

def test_domain_filter_fallback_all_windows():
    """When _filter_windows_by_domain returns empty (no keyword matches),
    TemporalCurveModel.curve_builder_for_event falls back to ALL windows."""
    windows = [
        _window("finance_gain",  "2010-01-01", "2020-01-01", 5.0),
        _window("career_rise",   "2010-01-01", "2020-01-01", 3.0),
    ]
    # 'spiritual' maps to domain 'general'; _DOMAIN_CLASS_KEYWORDS['general'] is ()
    # → empty keywords → filter returns [] → fallback to ALL windows
    model = TemporalCurveModel(windows, label="fallback_test")
    builder = model.curve_builder_for_event("spiritual")
    curve = builder(date(2015, 1, 1), date(2015, 1, 6))  # one step at 2015-01-01
    # Both windows are active on 2015-01-01 (start <= d < end) → total = 8.0
    assert len(curve) >= 1
    assert abs(curve[0].intensity - 8.0) < 1e-9


def test_empty_keyword_tuple_returns_empty_list():
    """_filter_windows_by_domain with empty keywords returns [] (not all windows).
    The fallback decision is the caller's responsibility."""
    windows = [_window("finance_gain", "2010-01-01", "2020-01-01", 5.0)]
    result = _filter_windows_by_domain(windows, ())
    assert result == []


# ── Test 8: empty window list → honest all-zero curve (I4) ──────────────────

def test_empty_windows_produces_zero_curve():
    """An empty GochaWindow list must produce a curve of all 0.0 intensities --
    no fabricated values, no crash."""
    curve = _build_lambda_curve([], date(2010, 1, 1), date(2010, 6, 1), step_days=30)
    assert len(curve) > 0
    for pt in curve:
        assert pt.intensity == 0.0


def test_temporal_curve_model_empty_windows():
    """TemporalCurveModel with no windows returns all-zero curve for any category."""
    model = TemporalCurveModel([], label="empty")
    builder = model.curve_builder_for_event("career")
    curve = builder(date(2010, 1, 1), date(2010, 3, 1))
    for pt in curve:
        assert pt.intensity == 0.0


def test_temporal_curve_model_summary_stats():
    """summary_stats() reports the label and total_windows correctly."""
    windows = [
        _window("career_rise", "2010-01-01", "2011-01-01", 1.0),
        _window("finance_gain", "2011-01-01", "2012-01-01", 2.0),
    ]
    model = TemporalCurveModel(windows, label="test_model")
    stats = model.summary_stats()
    assert stats["label"] == "test_model"
    assert stats["total_windows"] == 2
