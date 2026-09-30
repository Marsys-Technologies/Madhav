"""ASTRA_REVIEW_A5_4 P1-5 — the ACTUAL L1 kakṣyā boundary seam (FABLE #19 /
T0-10) repaired in both readers and both consumers.

ga_strength_writer.py writes fact_subject 'KAKSHYA_{n}' (n = 1..8) with
start_deg/end_deg as WITHIN-SIGN offsets — 24 facts per (chart × ayanāṃśa),
chart-independent. The readers expected '{planet}.{index}' with absolute
degrees: "Supplying all 24 actual L1 boundary facts to the context reader
returned zero boundaries" (the reviewer's probe). The consumers then searched
the raw offsets as if they were absolute Aries longitudes.

Covered here, on the producer's exact shape and in a NON-Aries sign:
  (a) both readers return 8 boundaries from the 24 producer facts;
  (b) the consumers add the target sign's base — Scorpio cell 2 is
      [213.75°, 217.5°), Jupiter (30°/8 = 3.75°; "cell two is [3.75°, 7.5°),
      Jupiter" — the reviewer's arithmetic);
  (c) retrograde crossings enter the cell BELOW the boundary (boundary 0 ⇒
      cell 7 of the previous sign); an unknown direction is disclosed;
  (d) contributor reads are pinned to an ayanāṃśa and refuse row-order picks
      on conflicting duplicates.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.gochara_grammar import primitives as P
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_v3 import engine as engine_module
from services.gochara_v3.context import (
    _fetch_bindu_contributor_rows, _fetch_kakshya_boundaries)
from services.gochara_v3.engine import _kakshya_cell_crossing_from_context

from .test_n22_kakshya_bindu_interim import _make_context

KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]
_BASE_JD = 2461042.0


def _producer_facts(ayanamshas=("lahiri_chitrapaksha",)):
    """The 24 facts exactly as ga_strength_writer.py emits them (per
    ayanāṃśa: the rows are stored per chart × ayanāṃśa, identical values)."""
    rows = []
    for _ay in ayanamshas:
        for k in range(8):
            subj = f"KAKSHYA_{k + 1}"
            rows.append((subj, "lord", KAKSHYA_LORDS[k], None))
            rows.append((subj, "start_deg", None, round(k * 3.75, 4)))
            rows.append((subj, "end_deg", None, round((k + 1) * 3.75, 4)))
    return rows


class _Conn:
    autocommit = True

    def __init__(self, rows):
        self._rows = rows
        self.params = []

    def execute(self, sql, params=None):
        self.params.append(params)
        rows = self._rows

        class _C:
            def fetchall(self_inner):
                return rows
        return _C()


# ── (a) both readers ────────────────────────────────────────────────────────

def test_context_reader_returns_eight_boundaries_from_producer_facts():
    rows = _fetch_kakshya_boundaries(_Conn(_producer_facts()), "chart-1")
    assert len(rows) == 8  # the reviewer's probe returned zero
    assert {r.planet for r in rows} == {"*"} and all(r.sign_relative for r in rows)
    assert [r.kakshya_index for r in rows] == list(range(8))
    assert [r.lord for r in rows] == KAKSHYA_LORDS
    assert rows[1].start_deg == 3.75 and rows[1].end_deg == 7.5 and rows[1].lord == "Jupiter"


def test_context_reader_collapses_per_ayanamsha_duplicates_and_drops_conflicts():
    two = _producer_facts(("lahiri_chitrapaksha", "raman"))
    assert len(_fetch_kakshya_boundaries(_Conn(two), "chart-1")) == 8
    conflicting = _producer_facts() + [("KAKSHYA_2", "lord", "Mars", None)]
    rows = _fetch_kakshya_boundaries(_Conn(conflicting), "chart-1")
    assert [r.kakshya_index for r in rows] == [0, 2, 3, 4, 5, 6, 7]  # KAKSHYA_2 dropped


def test_context_reader_still_accepts_legacy_per_planet_shape():
    rows = _fetch_kakshya_boundaries(_Conn([
        ("Jupiter.0", "start_deg", None, 10.0), ("Jupiter.0", "lord", "Saturn", None)]),
        "chart-1")
    assert len(rows) == 1 and rows[0].planet == "Jupiter" and rows[0].sign_relative is False


def test_primitives_reader_returns_eight_boundaries_for_any_planet():
    P._KAKSHYA_BOUNDARIES_CACHE.clear()
    conn = _Conn(_producer_facts())
    for planet in ("Saturn", "Moon"):
        rows = P._fetch_kakshya_boundaries(conn, "chart-2", planet)
        assert len(rows) == 8
        assert all(r["sign_relative"] and r["planet_scope"] == "*" for r in rows)
        assert rows[1]["lord"] == "Jupiter" and rows[1]["start_deg"] == 3.75
    P._KAKSHYA_BOUNDARIES_CACHE.clear()


def test_subject_parser_shapes():
    assert P.parse_kakshya_boundary_subject("KAKSHYA_1") == (0, True, "*")
    assert P.parse_kakshya_boundary_subject("KAKSHYA_8") == (7, True, "*")
    assert P.parse_kakshya_boundary_subject("KAKSHYA_9") is None
    assert P.parse_kakshya_boundary_subject("Jupiter.3") == (3, False, "Jupiter")
    assert P.parse_kakshya_boundary_subject("Jupiter.3", "Saturn") is None
    assert P.parse_kakshya_boundary_subject("garbage") is None


# ── (b) consumers add the sign base — Scorpio ───────────────────────────────

def _target(sign):
    return ResonanceTarget(chart_id="c", event_class="marriage", target_type="bhava",
                           target_ref="7", weight=1.0, target_sign=sign,
                           uncited_extension=True)


def _event(jd, speed=None):
    ev = MagicMock()
    ev.event_jd = jd
    ev.event_datetime_ist = "2026-01-01T12:00:00+05:30"
    if speed is not None:
        ev.speed_at_event_dps = speed
    return ev


def test_engine_consumer_searches_scorpio_offsets_not_aries():
    l1 = _fetch_kakshya_boundaries(_Conn(_producer_facts()), "chart-1")
    ctx = _make_context(kakshya_boundaries=tuple(l1))
    with patch("services.gochara_v3.engine.find_aspect_events",
               return_value=[_event(_BASE_JD + 1.0)]) as mock_find:
        sentences = _kakshya_cell_crossing_from_context(
            MagicMock(), ctx, _target("Scorpio"), _BASE_JD, _BASE_JD + 30.0,
            planets=["Saturn"])
    searched = sorted(call.args[2] for call in mock_find.call_args_list)
    assert searched == [210.0 + k * 3.75 for k in range(8)]  # NOT 0, 3.75, …
    assert len(sentences) == 8
    by_b = {s.detail["boundary_deg"]: s.detail for s in sentences}
    cell2 = by_b[213.75]
    assert cell2["kakshya_index"] == 1 and cell2["kakshya_lord"] == "Jupiter"
    assert cell2["entered_sign_number"] == 8 and cell2["direction"] == "unknown"
    assert all(s.detail["source"] == "chart_facts.ashtakavarga_kakshya_boundary"
               for s in sentences)
    assert all(s.uncited_extension is False for s in sentences)


def test_primitives_consumer_searches_scorpio_offsets_not_aries():
    P._KAKSHYA_BOUNDARIES_CACHE.clear()
    conn = _Conn(_producer_facts())
    with patch("services.gochara_grammar.primitives.find_aspect_events",
               return_value=[_event(_BASE_JD + 1.0)]) as mock_find:
        sentences = P.kakshya_cell_crossing(
            MagicMock(), "chart-3", _target("Scorpio"), _BASE_JD, _BASE_JD + 30.0,
            conn=conn, planets=["Saturn"])
    P._KAKSHYA_BOUNDARIES_CACHE.clear()
    searched = sorted(call.args[2] for call in mock_find.call_args_list)
    assert searched == [210.0 + k * 3.75 for k in range(8)]
    d = {s.detail["boundary_deg"]: s.detail for s in sentences}[213.75]
    assert d["kakshya_index"] == 1 and d["kakshya_lord"] == "Jupiter"
    assert sentences[0].uncited_extension is False


# ── (c) retrograde cell selection ───────────────────────────────────────────

def test_cell_entered_by_direction():
    assert P.kakshya_cell_entered(0.1, 2, 8) == ("direct", 2, 8)
    assert P.kakshya_cell_entered(-0.1, 2, 8) == ("retrograde", 1, 8)
    assert P.kakshya_cell_entered(-0.1, 0, 8) == ("retrograde", 7, 7)   # previous sign
    assert P.kakshya_cell_entered(-0.1, 0, 1) == ("retrograde", 7, 12)  # Aries → Pisces
    assert P.kakshya_cell_entered(None, 2, 8) == ("unknown", 2, 8)
    assert P.kakshya_cell_entered(MagicMock(), 2, 8)[0] == "unknown"


def test_engine_retrograde_crossing_enters_the_cell_below_and_keys_its_donor(monkeypatch):
    monkeypatch.setattr(engine_module, "_KAKSHYA_BINDU_INTERIM_ENABLED", True)
    from services.gochara_v3.context import BinduContributorRow
    l1 = _fetch_kakshya_boundaries(_Conn(_producer_facts()), "chart-1")
    ctx = _make_context(
        kakshya_boundaries=tuple(l1),
        bindu_contributor_rows=(
            BinduContributorRow(graha="SAT", contributor="JUP", sign_number=8, bindus=1.0),
            BinduContributorRow(graha="SAT", contributor="MAR", sign_number=8, bindus=0.0),
            BinduContributorRow(graha="SAT", contributor="LAGNA", sign_number=7, bindus=1.0),
        ))

    def _events(swe, planet, b, aspects, orb, s, e):
        if b == 217.5:                  # boundary 2 (Mars's cell starts here)
            return [_event(_BASE_JD + 1.0, speed=-0.05)]   # retrograde
        if b == 210.0:                  # boundary 0 (sign start)
            return [_event(_BASE_JD + 2.0, speed=-0.05)]
        return []

    with patch("services.gochara_v3.engine.find_aspect_events", side_effect=_events):
        sentences = _kakshya_cell_crossing_from_context(
            MagicMock(), ctx, _target("Scorpio"), _BASE_JD, _BASE_JD + 30.0,
            planets=["Saturn"])
    by_b = {s.detail["boundary_deg"]: s.detail for s in sentences}
    d = by_b[217.5]
    assert d["direction"] == "retrograde" and d["kakshya_index_entered"] == 1
    assert d["kakshya_lord"] == "Jupiter" and d["donor_row_key"] == "SAT-CONTRIBUTOR_JUP-SIGN_8"
    assert d["donor_bindu"] == 1 and d["qualification_grain"] == "kakshya"
    # mutation: the direct convention would have keyed Mars (mark 0 ⇒ unqualified)
    assert d["donor_row_key"] != "SAT-CONTRIBUTOR_MAR-SIGN_8"
    d0 = by_b[210.0]
    assert d0["kakshya_index_entered"] == 7 and d0["entered_sign_number"] == 7
    assert d0["donor_row_key"] == "SAT-CONTRIBUTOR_LAGNA-SIGN_7" and d0["donor_bindu"] == 1


# ── (d) contributor reads: ayanāṃśa pin + conflict policy ───────────────────

def test_contributor_rows_read_is_ayanamsha_pinned_and_conflict_safe():
    conn = _Conn([("SAT-CONTRIBUTOR_JUP-SIGN_8", 1.0),
                  ("SAT-CONTRIBUTOR_JUP-SIGN_8", 1.0),   # identical duplicate
                  ("SAT-CONTRIBUTOR_MAR-SIGN_8", 1.0),
                  ("SAT-CONTRIBUTOR_MAR-SIGN_8", 0.0)])  # conflict
    rows = _fetch_bindu_contributor_rows(conn, "chart-1", "raman")
    assert conn.params[0][1] == "raman"
    assert [(r.contributor, r.bindus) for r in rows] == [("JUP", 1.0)]


def test_donor_bindu_read_is_ayanamsha_pinned_and_refuses_conflicts():
    conn = _Conn([(1.0,), (0.0,)])
    assert P._fetch_kakshya_donor_bindu(conn, "c", "Saturn", "Jupiter", 8) is None
    assert conn.params[0][1] == "lahiri_chitrapaksha"
    conn2 = _Conn([(1.0,), (1.0,)])
    assert P._fetch_kakshya_donor_bindu(conn2, "c", "Saturn", "Jupiter", 8,
                                         ayanamsha_id="raman") == 1.0
    assert conn2.params[0][1] == "raman"
    d = P.kakshya_donor_bindu_detail(_Conn([(1.0,), (0.0,)]), "c", "Saturn", 8, 1)
    assert d["donor_bindu_state"] == "unavailable" and d["donor_bindu"] is None
