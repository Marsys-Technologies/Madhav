"""W2G — per-chart materialization layer tests (ṢAḌ-DARŚANA lane G, item 19).

TDD-first: written before `pipeline/orchestrator/writers/ka_gochara_v2_materialize.py`
(named `ka_gochara_sweep_v2.py` in the original PR #1081 authoring; renamed in
the lane G REWORK per the native ruling 2026-08-06 -- this module
(`materialize.py`) itself is unchanged by the rework, since it never touches
`kala_gochara_windows` or any table at all).
Everything here is offline and deterministic -- synthetic arcs with
analytically-known crossings (same technique as `test_w2g_arc_substrate.py`),
fixture `ResonanceTarget` rows, and injected fakes for the v1 grammar calls
(`compute_lambda_e_fn`, `fetch_temporal_shape_fn`, `gather_active_sentences_fn`)
so the CANDIDATE-DISCOVERY + ROW-ASSEMBLY logic under test is isolated from a
real DB or the full PROMISE/PERMISSION/suppression pipeline -- that pipeline is
v1's own, already tested in `test_ka_gochara_sweep.py` / the gochara_intensity
suite, and reused HERE unchanged (see materialize.py's module docstring).

Real `swisseph` is used for JD<->calendar-date conversion (pure ephemeris
arithmetic, no DB, same convention as `test_ka_gochara_sweep.py`).

WHAT IS UNDER TEST:
  1. `progressive_horizon` — design amendment 3's ±3y honest attestation.
  2. `resolve_target_degrees` — exact-degree-only extraction, bhava excluded.
  3. `candidate_point_jds` — the arc-substrate join: exact contacts, horizon
     filtering, de-duplication.
  4. `materialize_event_class` — the full per-class join+score assembly:
     honest-empty on no targets, honest-skip on non-point shapes, honest
     filtering of sub-threshold (inactive) candidates, and the exact row
     shape a `kala_gochara_windows` insert needs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest
import swisseph as swe

from services.gochara_grammar.models import ResonanceTarget
from services.w2g import build_arcs
from services.w2g.solver import InMemoryArcSource
from services.w2g.materialize import (
    CANDIDATE_NET_ORB_DEG,
    GENERATION_V2,
    HORIZON_STATUS_FULL,
    HORIZON_STATUS_PROGRESSIVE,
    PEAK_BASIS_V2,
    PROGRESSIVE_HORIZON_YEARS,
    candidate_point_jds,
    full_century_horizon,
    materialize_event_class,
    progressive_horizon,
    resolve_target_degrees,
)

JD0 = 2_451_545.0  # J2000.0 noon UT


# ── 1. progressive_horizon ─────────────────────────────────────────────────


def test_progressive_horizon_is_plus_minus_three_years_by_default():
    today = date(2026, 8, 6)
    h = progressive_horizon(today)
    assert h.start_date == date(2023, 8, 6)
    assert h.end_date == date(2029, 8, 6)
    assert h.status == HORIZON_STATUS_PROGRESSIVE
    assert PROGRESSIVE_HORIZON_YEARS == 3


def test_progressive_horizon_is_deterministic_not_wall_clock():
    """No internal date.today() call -- same `today` in, same result out,
    always. A hidden wall-clock read would make this test flaky/non-repro."""
    today = date(2020, 2, 29)  # leap day, deliberately awkward
    h1 = progressive_horizon(today)
    h2 = progressive_horizon(today)
    assert h1 == h2


def test_full_century_horizon_is_honestly_labelled_full():
    h = full_century_horizon(date(1900, 1, 1), date(2150, 12, 31))
    assert h.status == HORIZON_STATUS_FULL
    assert h.status != HORIZON_STATUS_PROGRESSIVE


# ── 2. resolve_target_degrees ──────────────────────────────────────────────


def _target(target_ref: str, longitude: float | None, target_type: str = "karaka") -> ResonanceTarget:
    return ResonanceTarget(
        chart_id="c1", event_class="marriage", target_type=target_type,
        target_ref=target_ref, weight=1.0, classical_citation="cite",
        target_longitude_deg=longitude,
    )


def test_resolve_target_degrees_excludes_unresolved_bhava_targets():
    targets = [
        _target("Venus", 123.45),
        _target("7", None, target_type="bhava"),  # sign-only, no exact degree
        _target("Jupiter", 400.0),  # unnormalized input, must wrap to [0,360)
    ]
    degs = resolve_target_degrees(targets)
    assert degs == [123.45, 40.0]


def test_resolve_target_degrees_honest_empty_when_nothing_resolved():
    assert resolve_target_degrees([_target("7", None, target_type="bhava")]) == []


# ── 3. candidate_point_jds ──────────────────────────────────────────────────


def _direct_arcs(body: str, n_days: int, deg_per_day: float, lon0: float = 0.0):
    jds = [JD0 + float(i) for i in range(n_days)]
    lons = [(lon0 + deg_per_day * i) % 360.0 for i in range(n_days)]
    return build_arcs(body, jds, lons)


def test_candidate_point_jds_finds_the_analytic_crossing():
    # Saturn-labelled synthetic arc: 0deg/day=0 -> 1deg/day for 400 days, so it
    # reaches 250.0deg at exactly t=250 (JD0+250), well inside the horizon.
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    found = candidate_point_jds(
        source, [250.0], horizon_start_jd=JD0, horizon_end_jd=JD0 + 399,
        bodies=["Saturn"], orb_deg=0.01,
    )
    assert len(found) == 1
    assert found[0] == pytest.approx(JD0 + 250.0, abs=1e-2)


def test_candidate_point_jds_filters_outside_horizon():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    # The crossing at t=250 is EXCLUDED by a horizon that ends at t=100.
    found = candidate_point_jds(
        source, [250.0], horizon_start_jd=JD0, horizon_end_jd=JD0 + 100,
        bodies=["Saturn"], orb_deg=0.01,
    )
    assert found == []


def test_candidate_point_jds_deduplicates_shared_target_degree():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    # Two distinct target degrees that are bit-identical after rounding must
    # not produce two rows for the same physical instant.
    found = candidate_point_jds(
        source, [250.0, 250.0], horizon_start_jd=JD0, horizon_end_jd=JD0 + 399,
        bodies=["Saturn"], orb_deg=0.01,
    )
    assert len(found) == 1


def test_candidate_point_jds_honest_empty_with_no_target_degrees():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    assert candidate_point_jds(source, [], horizon_start_jd=JD0, horizon_end_jd=JD0 + 399) == []


def test_candidate_net_orb_matches_documented_widest_v1_orb():
    assert CANDIDATE_NET_ORB_DEG == 8.0


# ── 4. materialize_event_class ──────────────────────────────────────────────


@dataclass
class _FakeIntensityResult:
    raw_lambda: float
    signed_lambda: float
    valence: str
    is_adverse: bool
    permission_detail: dict
    suppression_detail: dict
    calibration_state: str = "structural_prior"
    source: str = "live"


def _fake_scorer(active_jds: set[float], **_ignored_kwargs):
    """Builds a `compute_lambda_e_fn` double: active at the given rounded JDs,
    inactive (raw_lambda == 0.0) everywhere else -- so the "filter inactive
    candidates" behavior under test is driven by a real branch, not a
    tautology."""

    def _score(swe_, conn, chart_id, event_class, t_jd, **kwargs):
        active = round(t_jd, 3) in active_jds
        return _FakeIntensityResult(
            raw_lambda=1.5 if active else 0.0,
            signed_lambda=1.5 if active else 0.0,
            valence="gain",
            is_adverse=False,
            permission_detail={"systems": ["dasha_fixture"], "calibration_state": "structural_prior"},
            suppression_detail={"suppressed": False},
        )

    return _score


def test_materialize_event_class_honest_empty_when_no_resonance_targets():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    result = materialize_event_class(
        swe, conn=None, chart_id="c1", event_class="marriage", arc_source=source,
        horizon_start_jd=JD0, horizon_end_jd=JD0 + 399, bodies=["Saturn"],
        fetch_resonance_targets=lambda *a, **k: [],
    )
    assert result.rows == []
    assert result.contacts_evaluated == 0
    assert result.skipped_reason is not None and "no gochara_resonance_map targets" in result.skipped_reason


def test_materialize_event_class_skips_non_point_shapes_honestly():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    targets = [_target("Saturn", 250.0)]
    result = materialize_event_class(
        swe, conn=None, chart_id="c1", event_class="major_gain", arc_source=source,
        horizon_start_jd=JD0, horizon_end_jd=JD0 + 399, bodies=["Saturn"],
        fetch_resonance_targets=lambda *a, **k: targets,
        fetch_temporal_shape_fn=lambda *a, **k: "interval",
    )
    assert result.rows == []
    assert result.contacts_evaluated == 0
    assert "interval" in result.skipped_reason
    assert "deferred" in result.skipped_reason


def test_materialize_event_class_serves_only_active_candidates():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    # Two natal targets -> two candidate crossings (t=100, t=250). Only the
    # t=250 candidate is "active" per the fake scorer -- the honest-inactive
    # one (t=100) must be filtered, not served as a zero-intensity row.
    targets = [_target("Saturn", 100.0), _target("Venus", 250.0)]
    active_at = {round(JD0 + 250.0, 3)}
    result = materialize_event_class(
        swe, conn=None, chart_id="c1", event_class="marriage", arc_source=source,
        horizon_start_jd=JD0, horizon_end_jd=JD0 + 399, bodies=["Saturn"],
        fetch_resonance_targets=lambda *a, **k: targets,
        fetch_dasha_periods=lambda *a, **k: [],
        compute_lambda_e_fn=_fake_scorer(active_at),
        gather_active_sentences_fn=lambda *a, **k: [{"primitive": "fixture"}],
        fetch_temporal_shape_fn=lambda *a, **k: "point",
    )
    assert result.contacts_evaluated == 2, "both candidates must be EVALUATED"
    assert len(result.rows) == 1, "only the genuinely active one must be SERVED"
    row = result.rows[0]
    assert row["peak_date"] == date(2000, 9, 7)  # JD0+250 in IST calendar terms
    assert row["window_start"] == row["window_end"] == row["peak_date"]
    assert row["event_class"] == "marriage"
    assert row["temporal_shape"] == "point"
    assert row["milestone_id"] is None
    assert row["is_irreversibility_milestone"] is False
    assert row["peak_basis"] == PEAK_BASIS_V2
    assert row["signed_intensity"] == pytest.approx(1.5)
    assert row["raw_intensity"] == pytest.approx(1.5)
    assert row["valence"] == "gain"
    assert row["is_adverse"] is False
    assert row["contributing_systems"] == ["dasha_fixture"]
    assert row["suppression_state"] == {"suppressed": False}
    assert row["calibration_state"] == "structural_prior"
    assert row["active_sentences"] == [{"primitive": "fixture"}]


def test_materialize_event_class_honest_empty_when_all_candidates_inactive():
    arcs = _direct_arcs("Saturn", 400, 1.0, lon0=0.0)
    source = InMemoryArcSource({"Saturn": arcs})
    targets = [_target("Saturn", 250.0)]
    result = materialize_event_class(
        swe, conn=None, chart_id="c1", event_class="marriage", arc_source=source,
        horizon_start_jd=JD0, horizon_end_jd=JD0 + 399, bodies=["Saturn"],
        fetch_resonance_targets=lambda *a, **k: targets,
        fetch_dasha_periods=lambda *a, **k: [],
        compute_lambda_e_fn=_fake_scorer(active_jds=set()),  # nothing ever active
        fetch_temporal_shape_fn=lambda *a, **k: "point",
    )
    assert result.contacts_evaluated == 1
    assert result.rows == []


def test_generation_stamp_is_2_0():
    assert GENERATION_V2 == "2.0"
