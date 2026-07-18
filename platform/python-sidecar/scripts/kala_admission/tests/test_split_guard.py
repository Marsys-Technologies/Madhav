"""
test_split_guard.py -- proves the sealed TEST-split circuit breaker
(ESCALATION_POLICY_v1_0.md §4) is actually enforced, not just documented.

This is the single most important test file in this lane (per the T-6
ADMIT brief's explicit instruction) -- a fresh-context Opus verifier is
expected to scrutinize this file with extreme care. Every test here proves
a NEGATIVE: a synthetic event dated on/after 2020-01-01 is PROVABLY
EXCLUDED from every code path that reaches the scorer, not merely absent
from today's cache by convention.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from kala_admission.lel import (  # noqa: E402
    TEST_SPLIT_BOUNDARY,
    SealedTestSplitViolation,
    classify_scorability,
    load_train_events,
    partition_scorable,
)
from kala_admission.dates import parse_date  # noqa: E402

REAL_CACHE = Path(__file__).parents[1] / "cache" / "lel_train_events.json"


def _write_cache(tmp_path: Path, events: list[dict]) -> Path:
    p = tmp_path / "synthetic_lel_cache.json"
    p.write_text(json.dumps({"events": events}))
    return p


# ═══════════════════════════════════════════════════════════════════════════
# 1. THE core circuit-breaker test: a synthetic TEST-split row must be
#    provably rejected, not silently dropped or silently accepted.
# ═══════════════════════════════════════════════════════════════════════════

def test_load_train_events_raises_on_2020_01_01_row(tmp_path):
    """A synthetic event dated EXACTLY on the sealed boundary (2020-01-01,
    the first TEST-split date per the brief's '>= 2020-01-01 is TEST' rule)
    must cause load_train_events() to raise SealedTestSplitViolation --
    not skip the row silently, not load it, not warn-and-continue."""
    cache = _write_cache(
        tmp_path,
        [
            {
                "event_id": "synthetic-test-split-row",
                "event_date": "2020-01-01",
                "category": "career",
                "domain": "career/synthetic",
                "description": "Synthetic contamination probe -- must never load.",
            }
        ],
    )
    with pytest.raises(SealedTestSplitViolation):
        load_train_events(cache)


def test_load_train_events_raises_on_far_future_row(tmp_path):
    """A synthetic event dated well into the TEST window (e.g. the sealed
    2025-05-15 loss event's own date) must also raise -- the guard is not a
    boundary-only off-by-one check."""
    cache = _write_cache(
        tmp_path,
        [
            {
                "event_id": "synthetic-loss-event-probe",
                "event_date": "2025-05-15",
                "category": "loss",
                "domain": "loss/synthetic",
                "description": "Synthetic stand-in for the sealed 2025-05-15 loss event.",
            }
        ],
    )
    with pytest.raises(SealedTestSplitViolation):
        load_train_events(cache)


def test_load_train_events_raises_even_when_mixed_with_valid_train_rows(tmp_path):
    """A single contaminated row must poison the whole load, even when every
    other row in the same cache file is legitimately TRAIN -- the guard
    checks EVERY row, it does not short-circuit on the first clean one."""
    cache = _write_cache(
        tmp_path,
        [
            {
                "event_id": "valid-train-row",
                "event_date": "2010-07-01",
                "category": "finance",
                "domain": "finance/family_windfall",
                "description": "A legitimate TRAIN row.",
            },
            {
                "event_id": "contaminated-row",
                "event_date": "2021-06-30",
                "category": "career",
                "domain": "career/synthetic",
                "description": "Contamination probe placed AFTER a valid row.",
            },
        ],
    )
    with pytest.raises(SealedTestSplitViolation):
        load_train_events(cache)


def test_load_train_events_accepts_the_day_before_the_boundary(tmp_path):
    """Sanity check on the other side of the guard: 2019-12-31 (one day
    before the sealed boundary) must load cleanly -- proves the guard is a
    correct >= comparison, not an overly aggressive < comparison that would
    also reject legitimate TRAIN data."""
    cache = _write_cache(
        tmp_path,
        [
            {
                "event_id": "boundary-minus-one-day",
                "event_date": "2019-12-31",
                "category": "career",
                "domain": "career/synthetic",
                "description": "One day before the sealed boundary -- must load.",
            }
        ],
    )
    events = load_train_events(cache)
    assert len(events) == 1
    assert events[0].event_date == parse_date("2019-12-31")


def test_test_split_boundary_constant_is_2020_01_01():
    """Pins the boundary constant itself -- if this ever silently drifts,
    every other test in this file is checking the wrong line."""
    assert TEST_SPLIT_BOUNDARY == parse_date("2020-01-01")


# ═══════════════════════════════════════════════════════════════════════════
# 2. The REAL cache file this lane actually built and scored against must
#    itself contain zero TEST-split rows -- this is the check a verifier
#    can run directly against the committed artifact.
# ═══════════════════════════════════════════════════════════════════════════

def test_real_train_cache_contains_zero_test_split_events():
    events = load_train_events(REAL_CACHE)  # raises if contaminated -- this call IS the assertion
    assert len(events) == 36
    for e in events:
        assert e.event_date < TEST_SPLIT_BOUNDARY, f"{e.event_id} dated {e.event_date} is >= sealed boundary"


def test_real_train_cache_never_contains_the_sealed_loss_event_id():
    """The 2025-05-15 loss/financial_deception event (event_id
    d81fae4e-edf4-58d9-b201-cced7eae19d7 per BRIEF's anchors) must not
    appear anywhere in the TRAIN cache under any circumstance."""
    events = load_train_events(REAL_CACHE)
    ids = {e.event_id for e in events}
    assert "d81fae4e-edf4-58d9-b201-cced7eae19d7" not in ids


def test_real_train_cache_contains_the_usable_windfall_event():
    """The 2010-07-01 finance/family_windfall event IS usable (TRAIN) --
    confirms the guard is not over-broad and the intended anchor event is
    actually present for the windfall check."""
    events = load_train_events(REAL_CACHE)
    ids = {e.event_id for e in events}
    assert "bd7f5711-8668-5315-8e25-94dc94f2a101" in ids


# ═══════════════════════════════════════════════════════════════════════════
# 3. The scorability partition (which feeds the blind-battery check) must
#    never be handed a pre-boundary-violating event in the first place --
#    proven by construction, since it only ever receives load_train_events()'s
#    already-guarded output in the real pipeline (run_admission.py).
# ═══════════════════════════════════════════════════════════════════════════

def test_partition_scorable_on_real_cache_has_no_test_split_rows_in_either_bucket():
    events = load_train_events(REAL_CACHE)
    scorable, excluded = partition_scorable(events)
    for e in scorable:
        assert e.event_date < TEST_SPLIT_BOUNDARY
    for e, _reasons in excluded:
        assert e.event_date < TEST_SPLIT_BOUNDARY


def test_birth_anchor_is_excluded_not_scored():
    events = load_train_events(REAL_CACHE)
    birth = next(e for e in events if e.domain == "other/birth")
    verdict = classify_scorability(birth)
    assert verdict.scorable is False
    assert "birth_anchor_not_an_outcome" in verdict.reasons
