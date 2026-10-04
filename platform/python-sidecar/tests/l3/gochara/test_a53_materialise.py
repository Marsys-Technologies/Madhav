"""A5.3 interval_sweep (1/N) — contact materialisation, pure core
(materialise.py; no DB, no ephemeris — position_at is a piecewise-linear
fake consistent with the fixture crossings).

What this file proves:

  (a) residence spans derive from ordered boundary crossings with ONE
      midpoint probe per interval: direct passage, retrograde re-entry
      across the SAME boundary (equal consecutive levels — never guessed),
      and the 0° seam;
  (b) horizon truncation is KEPT as a span (t_exact NULL at a truncated
      ingress, solver_method 'clipped_truncated') — never absence
      (Tier-0-G truncated_contacts_kept); no position_at ⇒ no spans
      (unknown, never fabricated);
  (c) occurrence ordinals are full-domain and append-only stable (R3
      amendment 1); contact_id binds via substrate identity bytes, never a
      rounded t_exact;
  (d) record minting: one record per occurrence, uuid8 over the canonical
      natural key (E7); natal facts mint one record, contact_id NULL.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import evaluator as ev  # noqa: E402
from services.gochara_kernel import materialise as mat  # noqa: E402

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY = timedelta(days=1)
HORIZON = (T0, T0 + 400 * DAY)

CHART = {
    "lagna_deg": 12.43,
    "natal": {
        "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
        "Jupiter": 148.87, "Venus": 265.39, "Saturn": 356.74,
        "Rahu": 21.34, "Ketu": 201.34,
    },
}


def _cross(days: float, level: float) -> mat.BoundaryCrossing:
    return mat.BoundaryCrossing(t=T0 + days * DAY, level_deg=level)


def _piecewise(points: list[tuple[float, float]]):
    """position_at from (day, λ) knots, linear between them (deg/day)."""
    def position_at(t: datetime) -> float:
        d = (t - T0) / DAY
        for (d0, l0), (d1, l1) in zip(points, points[1:]):
            if d0 <= d <= d1:
                return l0 + (l1 - l0) * (d - d0) / (d1 - d0)
        return points[-1][1] if d > points[-1][0] else points[0][1]
    return position_at


# AM-2: span targets are the ABSOLUTE sign numeral (1 = Meṣa). An independent,
# spelled-out table — the tests must not derive their expectations from the
# production helper they are checking.
SIGN_NUM = {"aries": 1, "taurus": 2, "gemini": 3, "cancer": 4, "leo": 5,
            "virgo": 6, "libra": 7, "scorpio": 8, "sagittarius": 9,
            "capricorn": 10, "aquarius": 11, "pisces": 12}


def _p5_edge(sign: str, agent: str = "saturn") -> ev.RecordEdge:
    edges = [e for e in ev.enumerate_edges("marriage", "P5", CHART)
             if e.agent == agent
             and e.obj.canonical_target == f"span:{SIGN_NUM[sign]}"]
    assert len(edges) == 1
    return edges[0]


# ── (a) span derivation ───────────────────────────────────────────────────────


def test_direct_passage_spans():
    # λ = 15° + 1°/day: crosses 30° at day 15, 60° at day 45, then parks
    # just inside Gemini (the fake must not cross unlisted boundaries)
    crossings = [_cross(15, 30.0), _cross(45, 60.0)]
    pos = _piecewise([(0, 15.0), (45, 60.0), (46, 60.5), (400, 60.5)])
    spans = mat.residence_spans(crossings, horizon=HORIZON, position_at=pos)
    assert [(s.sign, s.truncated) for s in spans] == [
        ("Aries", True), ("Taurus", False), ("Gemini", True)]
    lead, mid, tail = spans
    assert lead.t_exact is None and lead.t_in == T0 and lead.t_out == T0 + 15 * DAY
    assert mid.t_exact == T0 + 15 * DAY and mid.t_out == T0 + 45 * DAY
    assert tail.t_exact == T0 + 45 * DAY and tail.t_out is None


def test_retrograde_reentry_same_boundary_multiple_spans():
    # Taurus at h_start; retrograde down across 30° (day 15) into Aries,
    # direct back up across 30° (day 45), on across 60° (day 75)
    crossings = [_cross(15, 30.0), _cross(45, 30.0), _cross(75, 60.0)]
    pos = _piecewise([(0, 45.0), (30, 15.0), (60, 45.0), (75, 60.0),
                      (76, 60.5), (400, 60.5)])
    spans = mat.residence_spans(crossings, horizon=HORIZON, position_at=pos)
    assert [(s.sign, s.truncated) for s in spans] == [
        ("Taurus", True), ("Aries", False), ("Taurus", False),
        ("Gemini", True)]
    taurus = [s for s in spans if s.sign == "Taurus"]
    assert len(taurus) == 2                       # re-entry: MULTIPLE spans
    assert all(s.t_exact is not None for s in taurus[1:])


def test_zero_degree_seam_spans():
    # λ = 350° + 1°/day: crosses the 0° seam at day 10, 30° at day 40
    crossings = [_cross(10, 0.0), _cross(40, 30.0)]
    pos = _piecewise([(0, 350.0), (400, 750.0)])
    spans = mat.residence_spans(crossings, horizon=HORIZON, position_at=pos)
    assert [s.sign for s in spans] == ["Pisces", "Aries", "Taurus"]


# ── (b) truncation honesty ────────────────────────────────────────────────────


def test_truncated_span_solver_method_and_null_t_exact():
    pos = _piecewise([(0, 15.0), (400, 415.0)])
    spans = mat.residence_spans([_cross(100, 30.0)], horizon=HORIZON,
                                position_at=pos)
    lead, tail = spans
    assert lead.sign == "Aries" and lead.t_exact is None
    assert lead.solver_method == "clipped_truncated"
    assert tail.sign == "Taurus" and tail.t_out is None
    assert tail.t_exact == T0 + 100 * DAY  # the ingress instant is real


def test_no_position_at_emits_nothing():
    spans = mat.residence_spans([_cross(10, 30.0), _cross(40, 60.0)],
                                horizon=HORIZON, position_at=None)
    assert spans == []


# ── (c) ordinals & identity ───────────────────────────────────────────────────


def test_ordinals_full_domain_and_append_only():
    spans = [
        mat.ResidenceSpan("Taurus", T0 + 10 * DAY, T0 + 40 * DAY,
                          T0 + 10 * DAY, False),
        mat.ResidenceSpan("Taurus", T0 + 100 * DAY, T0 + 130 * DAY,
                          T0 + 100 * DAY, False),
    ]
    edge = _p5_edge("taurus")
    contacts = mat.spans_for_object(spans, edge.obj)
    assert [c.occurrence_ordinal for c in contacts] == [1, 2]
    later = spans + [mat.ResidenceSpan("Taurus", T0 + 200 * DAY,
                                       T0 + 230 * DAY, T0 + 200 * DAY, False)]
    contacts2 = mat.spans_for_object(later, edge.obj)
    assert [c.contact_id for c in contacts2[:2]] == [c.contact_id for c in contacts]
    assert contacts2[2].occurrence_ordinal == 3


def test_truncated_spans_order_by_clipped_start():
    spans = [
        mat.ResidenceSpan("Taurus", T0, T0 + 10 * DAY, None, True),
        mat.ResidenceSpan("Taurus", T0 + 50 * DAY, T0 + 80 * DAY,
                          T0 + 50 * DAY, False),
    ]
    edge = _p5_edge("taurus")
    contacts = mat.spans_for_object(spans, edge.obj)
    assert [c.t_exact for c in contacts] == [None, T0 + 50 * DAY]


# ── (d) record minting ────────────────────────────────────────────────────────


def test_mint_transit_records_one_per_occurrence():
    spans = [
        mat.ResidenceSpan("Aries", T0, T0 + 10 * DAY, None, True),
        mat.ResidenceSpan("Taurus", T0 + 10 * DAY, T0 + 40 * DAY,
                          T0 + 10 * DAY, False),
        mat.ResidenceSpan("Taurus", T0 + 90 * DAY, T0 + 120 * DAY,
                          T0 + 90 * DAY, False),
    ]
    edge = _p5_edge("taurus")
    recs = mat.mint_transit_records(edge, spans, chart_id="c",
                                    generation="5.0", prerequisites=[])
    assert len(recs) == 2
    for r in recs:
        assert r["natural_key"]["contact_id"] == str(r["contact"].contact_id)
        assert r["record_id"].version == 8
        assert r["record_id"] == ev.record_uuid(r["natural_key"])
        assert r["span"].sign == "Taurus"
    assert recs[0]["span"].t_in == T0 + 10 * DAY
    assert recs[1]["span"].t_in == T0 + 90 * DAY
    assert recs[0]["record_id"] != recs[1]["record_id"]


def test_mint_transit_records_refuses_non_residence():
    edge = _p5_edge("taurus")
    bad = ev.RecordEdge(**{**edge.__dict__, "relation": "conjunction"})
    with pytest.raises(AssertionError):
        mat.mint_transit_records(bad, [], chart_id="c", generation="5.0",
                                 prerequisites=[])


def test_mint_natal_record_contact_null():
    edge = next(e for e in ev.enumerate_edges("marriage", "P1", CHART)
                if not e.transit)
    r = mat.mint_natal_record(edge, chart_id="c", generation="5.0",
                              prerequisites=[])
    assert r["natural_key"]["contact_id"] is None
    assert r["record_id"].version == 8
