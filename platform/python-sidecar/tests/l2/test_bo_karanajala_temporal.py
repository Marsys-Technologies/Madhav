"""WP-2.3-temporal — active_dasha_periods_jsonb overlay on graha-resting CGM edges.

Covers the temporal overlay bo_karanajala now writes onto lordship / occupancy /
bhava_aspect / yoga_member edges. The periods are sourced from L1 chart_dashas
(here: hand-built DashaPeriod fixtures shaped exactly like load_dasha_timeline's
output) and resolved through the merged WP-2.1 resolver — NO hand-rolled dates.

Asserts (per the lane's acceptance criteria):
  1. an edge whose graha HAS a birth-forward dasha period gets a NON-EMPTY
     active_dasha_periods_jsonb whose ISO dates match the fixture input;
  2. an edge whose graha has NO eligible period gets [] (honest empty);
  3. every emitted date is birth-forward (no pre-birth window — the WP-2.1
     regression class): a straddling period is clipped to birth, a wholly
     pre-birth period is dropped;
  4. the graha↔bhava / yoga_member builders serialize the overlay as JSON and
     keep constituent_fact_ids_array intact (§N.5).
"""
from __future__ import annotations

import json
import uuid
from datetime import date

import pytest

from services.ka_temporal import DashaPeriod
from pipeline.orchestrator.writers.bo_karanajala import (
    _dasha_periods_for_graha,
    _build_dasha_periods_by_graha,
    _graha_bhava_edge,
    _membership_edge,
    KNOWN_GRAHAS,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = str(uuid.uuid4())
AYA      = "lahiri_chitrapaksha"
NOW      = "2026-07-13T00:00:00+00:00"
BIRTH    = date(1984, 2, 5)  # native's birth date (§B)


def _timeline() -> list[DashaPeriod]:
    """chart_dashas-shaped fixture: Saturn has three periods (a wholly pre-birth
    MD that must be dropped, a birth-straddling AD that must be clipped, and a
    clean birth-forward MD); Jupiter has one birth-forward MD. Mars/Moon absent."""
    return [
        DashaPeriod(lord="Saturn",  level_n=1, start=date(1955, 1, 1), end=date(1974, 1, 1)),   # pre-birth → drop
        DashaPeriod(lord="Saturn",  level_n=2, start=date(1983, 1, 1), end=date(1985, 1, 1)),   # straddles birth → clip
        DashaPeriod(lord="Saturn",  level_n=1, start=date(2000, 1, 1), end=date(2019, 1, 1)),   # birth-forward
        DashaPeriod(lord="Jupiter", level_n=1, start=date(2019, 1, 1), end=date(2035, 1, 1)),   # birth-forward
    ]


# ── 1. graha WITH birth-forward periods → non-empty, ISO dates match fixture ──

def test_periods_present_for_graha_with_birthforward_dasha():
    periods = _dasha_periods_for_graha("Saturn", _timeline(), BIRTH)
    assert periods, "Saturn has birth-forward periods → must be non-empty"
    # Every entry is a real chart_dashas-sourced period (no provenance stubs).
    assert all(p["source"] == "chart_dashas" for p in periods)
    assert all(p["graha"] == "Saturn" for p in periods)
    # The clean birth-forward MD's dates match the fixture verbatim.
    md = [p for p in periods if p["start"] == "2000-01-01"]
    assert len(md) == 1
    assert md[0]["end"] == "2019-01-01"
    assert md[0]["level"] == "mahadasha"


# ── 2. graha with NO eligible period → honest [] ──────────────────────────────

def test_empty_for_graha_with_no_period():
    # Mars is absent from the timeline entirely.
    assert _dasha_periods_for_graha("Mars", _timeline(), BIRTH) == []
    # A graha whose only period is wholly pre-birth also yields [].
    pre_birth_only = [DashaPeriod(lord="Rahu", level_n=1,
                                  start=date(1950, 1, 1), end=date(1968, 1, 1))]
    assert _dasha_periods_for_graha("Rahu", pre_birth_only, BIRTH) == []


# ── 3. birth-forward guarantee: no ISO date precedes birth ────────────────────

def test_birth_forward_no_pre_birth_windows():
    periods = _dasha_periods_for_graha("Saturn", _timeline(), BIRTH)
    for p in periods:
        assert p["start"] >= BIRTH.isoformat(), f"pre-birth start leaked: {p}"
    # The wholly pre-birth MD (1955–1974) must NOT appear.
    assert not any(p["end"] == "1974-01-01" for p in periods)
    # The straddling AD (1983–1985) is kept but clipped to birth.
    straddler = [p for p in periods if p["end"] == "1985-01-01"]
    assert len(straddler) == 1
    assert straddler[0]["start"] == BIRTH.isoformat()
    assert straddler[0].get("clipped_to_birth") is True


def test_unknown_graha_returns_empty():
    assert _dasha_periods_for_graha("NotAGraha", _timeline(), BIRTH) == []


# ── 4. builders serialize the overlay + keep the fact ledger intact ───────────

def test_build_dasha_periods_by_graha_covers_all_grahas():
    m = _build_dasha_periods_by_graha(_timeline(), BIRTH)
    assert set(m.keys()) == set(KNOWN_GRAHAS)
    assert m["Saturn"], "Saturn populated"
    assert m["Mars"] == [], "Mars honest empty"


def test_graha_bhava_edge_serializes_periods_and_keeps_fact_ids():
    periods = _dasha_periods_for_graha("Saturn", _timeline(), BIRTH)
    edge = _graha_bhava_edge(
        "occupancy", CHART_ID, AYA, BUILD_ID,
        "graha-node", "bhava-node", "Saturn", 7, ["fact-1"], NOW, periods,
    )
    stored = json.loads(edge["active_dasha_periods_jsonb"])
    assert stored == periods and stored, "non-empty JSON array of resolved periods"
    # §N.5: constituent fact ledger intact.
    assert edge["constituent_fact_ids_array"] == ["fact-1"]
    assert edge["edge_type"] == "occupancy"


def test_graha_bhava_edge_empty_is_honest_empty_array():
    edge = _graha_bhava_edge(
        "lordship", CHART_ID, AYA, BUILD_ID,
        "graha-node", "bhava-node", "Mars", 3, ["fact-2"], NOW, [],
    )
    assert edge["active_dasha_periods_jsonb"] == "[]"  # not NULL, not fabricated


def test_graha_bhava_edge_default_arg_is_empty_array():
    # Backward-compatible default (no dasha_periods passed) → '[]', never NULL.
    edge = _graha_bhava_edge(
        "bhava_aspect", CHART_ID, AYA, BUILD_ID,
        "graha-node", "bhava-node", "Venus", 10, ["fact-3"], NOW,
    )
    assert edge["active_dasha_periods_jsonb"] == "[]"


def test_membership_edge_graha_member_carries_periods():
    periods = _dasha_periods_for_graha("Jupiter", _timeline(), BIRTH)
    edge = _membership_edge(
        CHART_ID, AYA, BUILD_ID, "yoga-node", "graha-node",
        "yoga", "gajakesari", "graha", "Jupiter", ["fact-9"], NOW, periods,
    )
    stored = json.loads(edge["active_dasha_periods_jsonb"])
    assert stored == periods and stored
    assert edge["edge_type"] == "yoga_member"
    assert edge["constituent_fact_ids_array"] == ["fact-9"]


def test_membership_edge_bhava_member_is_empty_array():
    edge = _membership_edge(
        CHART_ID, AYA, BUILD_ID, "yoga-node", "bhava-node",
        "yoga", "gajakesari", "bhava", "5", [], NOW, [],
    )
    assert edge["active_dasha_periods_jsonb"] == "[]"
