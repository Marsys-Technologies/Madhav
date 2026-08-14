"""
test_w42_negative_control.py -- unit tests for the W4.2 negative-control harness.

All tests are DB-free. Curve-builder dependencies are satisfied with toy
fixture data (a small in-memory set of DashaPeriods and LelEvents) so no
real cache files or live connectors are needed.

I3 HONESTY PRINCIPLE (documented here per task spec):
    Admission requires "does not degrade + classically cited" -- NOT
    statistical significance; this harness simply establishes what random
    chance looks like, not a p-value gate.
"""
from __future__ import annotations

import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Make kala_admission importable
sys.path.insert(0, str(Path(__file__).parents[2]))

from kala_admission.curve import DashaPeriod  # noqa: E402
from kala_admission.lel import LelEvent, TEST_SPLIT_BOUNDARY  # noqa: E402
from kala_admission.w42_negative_control import (  # noqa: E402
    BOUNDS_START,
    N_SHUFFLES,
    SHUFFLE_SEED,
    _SHUFFLE_UPPER,
    _date_range_days,
    compute_noise_floor,
    shuffle_event_dates,
    run_one_shuffle,
    build_negative_control_report,
    NoiseFloor,
)
from kala_admission.currents import CurrentsConfig  # noqa: E402


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _toy_periods() -> list[DashaPeriod]:
    """Small dasha-period set covering 1984-02-05..2022-06-01 at a single level."""
    # One broad MD covering the whole train window -- intensity_at will always
    # find a running lord (Jupiter), giving non-zero v1 intensity for any
    # significator set that includes Jupiter.
    return [
        DashaPeriod(1, "Jupiter", date(1984, 1, 1), date(2023, 1, 1)),
        DashaPeriod(2, "Venus", date(1984, 1, 1), date(2023, 1, 1)),
        DashaPeriod(3, "Saturn", date(1984, 1, 1), date(2023, 1, 1)),
    ]


def _toy_events(n: int = 5) -> list[LelEvent]:
    """N synthetic TRAIN events spread across the train window."""
    events = []
    for i in range(n):
        # Space events roughly 5 years apart starting from 1985
        d = date(1985 + i * 5, 6, 15)
        assert d < TEST_SPLIT_BOUNDARY, "fixture must not produce TEST dates"
        events.append(
            LelEvent(
                event_id=f"fixture-event-{i:03d}",
                event_date=d,
                category="finance",
                domain="wealth",
                description="synthetic fixture event",
            )
        )
    return events


def _toy_lord_capability() -> dict:
    """Minimal lord_capability dict (no warning scores -- clean lords)."""
    return {
        "Jupiter": {"warning_score": 0},
        "Venus": {"warning_score": 0},
        "Saturn": {"warning_score": 0},
    }


# ── Test 1: shuffle produces same number of events ────────────────────────────

def test_shuffle_preserves_event_count():
    """After shuffling, the returned list must have exactly the same length
    as the input -- no events are added or dropped."""
    events = _toy_events(7)
    rng = random.Random(42)
    shuffled = shuffle_event_dates(events, rng)
    assert len(shuffled) == len(events)


def test_shuffle_preserves_event_ids_and_categories():
    """Event identity (event_id, category) must be unchanged by the shuffle;
    only dates may differ."""
    events = _toy_events(5)
    rng = random.Random(42)
    shuffled = shuffle_event_dates(events, rng)
    for orig, shuf in zip(events, shuffled):
        assert shuf.event_id == orig.event_id
        assert shuf.category == orig.category
        assert shuf.domain == orig.domain


# ── Test 2: shuffled dates are within bounds ──────────────────────────────────

def test_shuffled_dates_within_train_bounds():
    """Every shuffled date must satisfy:
        BOUNDS_START <= date <= _SHUFFLE_UPPER < TEST_SPLIT_BOUNDARY

    _toy_events(5) gives 5 events safely within the TRAIN window; we run
    10 shuffle rounds for a total of 50 date assertions.
    """
    events = _toy_events(5)  # 5 events max -- dates stay within TRAIN range
    rng = random.Random(99)
    for _ in range(10):  # 10 shuffle rounds, 5 events each = 50 date checks
        shuffled = shuffle_event_dates(events, rng)
        for e in shuffled:
            assert e.event_date >= BOUNDS_START, f"{e.event_date} before BOUNDS_START"
            assert e.event_date <= _SHUFFLE_UPPER, f"{e.event_date} after _SHUFFLE_UPPER"
            assert e.event_date < TEST_SPLIT_BOUNDARY, f"{e.event_date} >= TEST_SPLIT_BOUNDARY"


def test_shuffle_upper_is_before_test_split():
    """Sanity check: _SHUFFLE_UPPER must be strictly < TEST_SPLIT_BOUNDARY."""
    assert _SHUFFLE_UPPER < TEST_SPLIT_BOUNDARY


# ── Test 3: noise floor computation (mean/std of known array) ─────────────────

def test_noise_floor_computation_known_values():
    """compute_noise_floor on a known dataset must match manually verified stats."""
    # Simple dataset: [0.0, 0.25, 0.5, 0.75, 1.0]
    data = [0.0, 0.25, 0.5, 0.75, 1.0]
    n = len(data)
    expected_mean = sum(data) / n  # = 0.5
    expected_variance = sum((x - expected_mean) ** 2 for x in data) / n
    expected_std = math.sqrt(expected_variance)  # = sqrt(0.125) ≈ 0.35355...

    nf = compute_noise_floor(data)

    assert abs(nf.mean - expected_mean) < 1e-5, f"mean mismatch: {nf.mean} vs {expected_mean}"
    assert abs(nf.std - expected_std) < 1e-5, f"std mismatch: {nf.std} vs {expected_std}"


def test_noise_floor_single_value():
    """A single-value list should produce std=0 and both CI bounds = the value."""
    nf = compute_noise_floor([0.6])
    assert nf.mean == 0.6
    assert nf.std == 0.0
    assert nf.ci_2sigma_low == 0.6
    assert nf.ci_2sigma_high == 0.6


def test_noise_floor_empty():
    """Empty list should not raise; returns zeros."""
    nf = compute_noise_floor([])
    assert nf.mean == 0.0
    assert nf.std == 0.0


# ── Test 4: CI calculation is correct (known data) ───────────────────────────

def test_ci_is_symmetric_two_sigma():
    """ci_2sigma_low = mean - 2*std and ci_2sigma_high = mean + 2*std."""
    data = [0.1 * i for i in range(11)]  # 0.0, 0.1, ..., 1.0
    nf = compute_noise_floor(data)
    expected_low = nf.mean - 2 * nf.std
    expected_high = nf.mean + 2 * nf.std
    assert abs(nf.ci_2sigma_low - expected_low) < 1e-5
    assert abs(nf.ci_2sigma_high - expected_high) < 1e-5


def test_p95_is_above_p50_for_non_constant_data():
    """p95 must be >= mean for a non-constant distribution."""
    data = [float(i) / 100.0 for i in range(100)]
    nf = compute_noise_floor(data)
    assert nf.p95 >= nf.mean


def test_p99_gte_p95():
    """p99 must be >= p95 for any dataset."""
    data = [float(i) / 100.0 for i in range(100)]
    nf = compute_noise_floor(data)
    assert nf.p99 >= nf.p95


# ── Test 5: report JSON has required fields ───────────────────────────────────

def test_report_has_required_fields():
    """The report dict must contain every key specified in the W4.2 task spec."""
    required_keys = [
        "harness",
        "wave",
        "n_shuffles",
        "shuffle_hit_rates",
        "noise_floor",
        "real_score",
        "exceeds_noise_floor",
        "margin_above_floor",
    ]
    required_noise_floor_keys = [
        "mean",
        "std",
        "ci_2sigma_low",
        "ci_2sigma_high",
        "p95",
        "p99",
    ]
    required_real_score_keys = [
        "hit_rate",
        "hit_count",
        "scored_count",
    ]

    # Run with a very small n_shuffles so the test finishes quickly
    report = build_negative_control_report(n_shuffles=10, seed=42)

    for k in required_keys:
        assert k in report, f"missing top-level key: {k!r}"

    for k in required_noise_floor_keys:
        assert k in report["noise_floor"], f"missing noise_floor key: {k!r}"

    for k in required_real_score_keys:
        assert k in report["real_score"], f"missing real_score key: {k!r}"

    assert report["harness"] == "w42_negative_control"
    assert report["wave"] == "W4.2"
    assert report["n_shuffles"] == 10
    assert len(report["shuffle_hit_rates"]) == 10
    assert isinstance(report["exceeds_noise_floor"], bool)
    assert isinstance(report["margin_above_floor"], float)


def test_report_hit_rate_in_unit_interval():
    """All hit_rates (real and shuffled) must be in [0.0, 1.0]."""
    report = build_negative_control_report(n_shuffles=5, seed=7)
    for hr in report["shuffle_hit_rates"]:
        assert 0.0 <= hr <= 1.0, f"shuffle hit_rate out of bounds: {hr}"
    assert 0.0 <= report["real_score"]["hit_rate"] <= 1.0


def test_report_margin_consistent_with_components():
    """margin_above_floor must equal real_score.hit_rate - noise_floor_upper_bound."""
    report = build_negative_control_report(n_shuffles=5, seed=13)
    nf = report["noise_floor"]
    upper_bound = nf["mean"] + 2 * nf["std"]
    expected_margin = report["real_score"]["hit_rate"] - upper_bound
    assert abs(report["margin_above_floor"] - expected_margin) < 1e-4, (
        f"margin inconsistency: {report['margin_above_floor']} vs {expected_margin}"
    )


def test_shuffle_is_deterministic_per_seed():
    """Two runs with the same seed must produce identical shuffle_hit_rates."""
    r1 = build_negative_control_report(n_shuffles=10, seed=42)
    r2 = build_negative_control_report(n_shuffles=10, seed=42)
    assert r1["shuffle_hit_rates"] == r2["shuffle_hit_rates"]


def test_different_seeds_produce_different_distributions():
    """Different seeds should produce different shuffle_hit_rates lists
    (with overwhelming probability for any non-trivial event set)."""
    r1 = build_negative_control_report(n_shuffles=20, seed=1)
    r2 = build_negative_control_report(n_shuffles=20, seed=9999)
    # If all hit rates are identical under both seeds the scoring surface is
    # degenerate (constant output) -- a useful signal but not expected.
    # We just assert the lists are not byte-identical, which is the minimal bar.
    assert r1["shuffle_hit_rates"] != r2["shuffle_hit_rates"], (
        "hit_rates were identical under two different seeds -- this suggests "
        "the scoring surface is constant, which should be investigated"
    )
