#!/usr/bin/env python3
"""
w42_negative_control.py -- W4.2 negative-control harness for the D-3 ADMIT
kernel-admission scoring harness.

I3 HONESTY PRINCIPLE (small-N honesty):
    Admission requires "does not degrade + classically cited" -- NOT
    statistical significance. This harness simply establishes what random
    chance looks like, not a p-value gate. The noise floor is diagnostic
    evidence, not a pass/fail bar: a real score that barely clears the
    floor is weak evidence; one that clears it by a large margin is
    stronger. Both are informative; neither replaces classical judgment.

WHAT THIS HARNESS DOES:
    Takes the same scoring machinery (curve builder, percentile threshold,
    PROXIMITY_DAYS) used by the real D-3 ADMIT loop (run_admission.py) but
    feeds it SHUFFLED event dates instead of the real ones. Event identities
    (event_id, category, significators) are held fixed; only the calendar
    dates are reassigned uniformly at random within the TRAIN period
    (BOUNDS_START .. TEST_SPLIT_BOUNDARY exclusive). Running N_SHUFFLES=1000
    iterations yields a hit_rate distribution whose mean + 2*std is the
    noise floor.

TEST-SPLIT ENFORCEMENT:
    - Shuffled dates are constrained to BOUNDS_START..TEST_SPLIT_BOUNDARY-1.
    - Real event loading uses lel.py's load_train_events() with its built-in
      SealedTestSplitViolation circuit breaker -- TEST events can never enter
      this harness.
    - No event >= 2020-01-01 is ever scored.

REPRODUCIBILITY:
    random.seed(SHUFFLE_SEED) is called before every use of the RNG so
    results are deterministic per seed value.
"""
from __future__ import annotations

import json
import math
import random
import sys
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# Make kala_admission importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from kala_admission.checks import run_blind_battery_curve  # noqa: E402
from kala_admission.currents import CurrentsConfig, make_candidate_curve_builder  # noqa: E402
from kala_admission.dasha_periods import load_dasha_lord_capability, load_dasha_periods  # noqa: E402
from kala_admission.dates import parse_date  # noqa: E402
from kala_admission.lel import TEST_SPLIT_BOUNDARY, LelEvent, load_train_events, partition_scorable  # noqa: E402
from kala_admission.mechanisms import significators_for_category  # noqa: E402

# ── Constants (match run_admission.py exactly) ──────────────────────────────
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BOUNDS_START: date = parse_date("1984-02-05")
BOUNDS_END: date = parse_date("2022-06-01")

# Upper boundary for shuffled dates: exclusive of TEST split (< 2020-01-01).
# We use TEST_SPLIT_BOUNDARY-1day so every shuffled date is strictly TRAIN.
_SHUFFLE_UPPER: date = TEST_SPLIT_BOUNDARY - timedelta(days=1)

N_SHUFFLES: int = 1000
SHUFFLE_SEED: int = 42

# ── Helpers ──────────────────────────────────────────────────────────────────

def _date_range_days(start: date, end: date) -> int:
    """Number of days in [start, end] inclusive."""
    return (end - start).days + 1


def _random_date_in_train(rng: random.Random) -> date:
    """Sample a uniformly random date in [BOUNDS_START, _SHUFFLE_UPPER]."""
    n = _date_range_days(BOUNDS_START, _SHUFFLE_UPPER)
    offset = rng.randint(0, n - 1)
    return BOUNDS_START + timedelta(days=offset)


def shuffle_event_dates(events: list[LelEvent], rng: random.Random) -> list[LelEvent]:
    """Return a new list with the same events but dates randomly permuted.

    Strategy: sample a fresh random date from the TRAIN period for every
    event (rather than permuting the existing dates) so the shuffled
    distribution is uniform over the whole train window rather than
    constrained to the actual event-date set. Both strategies are valid
    negative controls; uniform sampling makes the noise-floor estimate
    more conservative (it does not benefit from any clustering the real
    dates might have).

    Every returned LelEvent has event_date strictly < TEST_SPLIT_BOUNDARY.
    """
    out: list[LelEvent] = []
    for e in events:
        new_date = _random_date_in_train(rng)
        assert new_date < TEST_SPLIT_BOUNDARY, "shuffle must never produce a TEST date"
        out.append(
            LelEvent(
                event_id=e.event_id,
                event_date=new_date,
                category=e.category,
                domain=e.domain,
                description=e.description,
            )
        )
    return out


# ── Noise floor statistics ────────────────────────────────────────────────────

@dataclass
class NoiseFloor:
    mean: float
    std: float
    ci_2sigma_low: float
    ci_2sigma_high: float
    p95: float
    p99: float


def compute_noise_floor(hit_rates: list[float]) -> NoiseFloor:
    """Compute descriptive statistics for the shuffle hit_rate distribution.

    CI is the symmetric 2-sigma interval [mean - 2*std, mean + 2*std].
    The noise_floor_upper_bound used by the comparison is mean + 2*std.
    """
    n = len(hit_rates)
    if n == 0:
        return NoiseFloor(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    mean = sum(hit_rates) / n
    variance = sum((r - mean) ** 2 for r in hit_rates) / n
    std = math.sqrt(variance)
    sorted_rates = sorted(hit_rates)

    def _percentile(p: float) -> float:
        # nearest-rank, consistent with curve.py's percentile_threshold
        idx = min(n - 1, max(0, math.ceil(p * n) - 1))
        return sorted_rates[idx]

    return NoiseFloor(
        mean=round(mean, 6),
        std=round(std, 6),
        ci_2sigma_low=round(mean - 2 * std, 6),
        ci_2sigma_high=round(mean + 2 * std, 6),
        p95=round(_percentile(0.95), 6),
        p99=round(_percentile(0.99), 6),
    )


# ── Core: run one shuffle iteration ──────────────────────────────────────────

def _build_curve_factory(periods, lord_capability, config: CurrentsConfig):
    """Returns a per-event-id curve-builder closure matching checks.CurveBuilder."""
    def build_curve_for_event(event_id: str, category: str):
        sig = significators_for_category(category)
        return make_candidate_curve_builder(periods, sig, lord_capability, config)
    return build_curve_for_event


def run_one_shuffle(
    scorable_events: list[LelEvent],
    periods,
    lord_capability,
    config: CurrentsConfig,
    rng: random.Random,
) -> float:
    """Shuffle event dates, score the shuffled set, return the hit_rate."""
    shuffled = shuffle_event_dates(scorable_events, rng)

    # Build (event_id, shuffled_date) pairs; resolve significators per event
    # by wiring through the per-event curve builder required by run_blind_battery_curve.
    events_for_scoring: list[tuple[str, date]] = [
        (e.event_id, e.event_date) for e in shuffled
    ]

    # build_curve_for_event needs to look up category by event_id.
    # Build a lookup from the SHUFFLED list (dates changed; categories unchanged).
    category_by_id: dict[str, str] = {e.event_id: e.category for e in shuffled}

    def build_curve_for_event(event_id: str):
        cat = category_by_id[event_id]
        sig = significators_for_category(cat)
        return make_candidate_curve_builder(periods, sig, lord_capability, config)

    result = run_blind_battery_curve(
        build_curve_for_event=build_curve_for_event,
        events=events_for_scoring,
        bounds_start=BOUNDS_START,
        bounds_end=BOUNDS_END,
        percentile=2.0 / 3.0,  # top-tercile, matching run_admission.py
    )
    return result.hit_rate


# ── Real score (Stage 0 v1 baseline only, matching W4.2 spec) ────────────────

def run_real_score(
    scorable_events: list[LelEvent],
    periods,
    lord_capability,
) -> dict:
    """Run the v1-baseline curve (Stage 0, no PERMISSION/TRIGGER) against
    the real event dates. Returns hit_rate/hit_count/scored_count.

    The Stage 0 config matches run_admission.py exactly:
        CurrentsConfig(permission_admitted=False, trigger_admitted=False)
    """
    config = CurrentsConfig(permission_admitted=False, trigger_admitted=False)

    events_for_scoring: list[tuple[str, date]] = [
        (e.event_id, e.event_date) for e in scorable_events
    ]
    category_by_id: dict[str, str] = {e.event_id: e.category for e in scorable_events}

    def build_curve_for_event(event_id: str):
        cat = category_by_id[event_id]
        sig = significators_for_category(cat)
        return make_candidate_curve_builder(periods, sig, lord_capability, config)

    result = run_blind_battery_curve(
        build_curve_for_event=build_curve_for_event,
        events=events_for_scoring,
        bounds_start=BOUNDS_START,
        bounds_end=BOUNDS_END,
        percentile=2.0 / 3.0,
    )
    return {
        "hit_rate": round(result.hit_rate, 6),
        "hit_count": result.hit_count,
        "scored_count": result.scored_count,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def build_negative_control_report(
    n_shuffles: int = N_SHUFFLES,
    seed: int = SHUFFLE_SEED,
) -> dict:
    """Full negative-control run. Loads TRAIN events, runs N_SHUFFLES date
    shuffles against the v1-baseline curve, computes noise floor, and
    compares against the real v1-baseline score.

    Returns the complete JSON-serialisable report dict.
    """
    # ── Load TRAIN data (SealedTestSplitViolation raised if contaminated) ──
    all_events = load_train_events()
    for e in all_events:
        assert e.event_date < TEST_SPLIT_BOUNDARY, "unreachable -- load_train_events() already enforces this"

    scorable_events, excluded = partition_scorable(all_events)

    # ── Load dasha substrate (deterministic L1 facts, no test split) ──
    periods = load_dasha_periods()
    lord_capability = load_dasha_lord_capability()["lords"]

    # ── Stage 0 config: v1 baseline only ──
    config = CurrentsConfig(permission_admitted=False, trigger_admitted=False)

    # ── Shuffle loop ──
    rng = random.Random(seed)
    shuffle_hit_rates: list[float] = []
    for _ in range(n_shuffles):
        hr = run_one_shuffle(scorable_events, periods, lord_capability, config, rng)
        shuffle_hit_rates.append(round(hr, 6))

    noise_floor = compute_noise_floor(shuffle_hit_rates)

    # ── Real score ──
    real_score = run_real_score(scorable_events, periods, lord_capability)

    # ── Comparison ──
    floor_upper = noise_floor.mean + 2 * noise_floor.std
    margin = real_score["hit_rate"] - floor_upper

    return {
        "harness": "w42_negative_control",
        "wave": "W4.2",
        "chart_id": CHART_ID,
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "bounds_start": BOUNDS_START.isoformat(),
        "bounds_end": BOUNDS_END.isoformat(),
        "shuffle_upper_bound": _SHUFFLE_UPPER.isoformat(),
        "n_shuffles": n_shuffles,
        "shuffle_seed": seed,
        "train_events_total": len(all_events),
        "train_events_scorable": len(scorable_events),
        "train_events_excluded": len(excluded),
        "curve_config": "v1_baseline_only (permission_admitted=False, trigger_admitted=False)",
        "percentile_threshold": "top_tercile (2/3)",
        "proximity_days": 45,
        "shuffle_hit_rates": shuffle_hit_rates,
        "noise_floor": asdict(noise_floor),
        "real_score": real_score,
        "noise_floor_upper_bound": round(floor_upper, 6),
        "exceeds_noise_floor": real_score["hit_rate"] > floor_upper,
        "margin_above_floor": round(margin, 6),
    }


def main() -> None:
    report = build_negative_control_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
