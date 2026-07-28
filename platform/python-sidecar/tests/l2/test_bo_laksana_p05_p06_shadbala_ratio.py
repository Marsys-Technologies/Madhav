"""
Tests for bo_laksana._build_strength_lookup — ŚUDDHA-VĀCA P0-5 / P0-6 fix
(SUDDHA_VACA_FIX_LEDGER_v1_0.md, lane:bo-laksana).

P0-5 (D1_MISSELECT): the SELECT filtered ONLY on
fact_category='graha_shadbala_total' — no fact_key pin, no ORDER BY. Under
that category, chart_facts carries TWO fact_key variants scoped to the SAME
(chart_id, ayanamsha_id, fact_subject) for every classical graha:
  - fact_key='rupa'  — raw achieved shadbala (scale ~4.6-8.5)
  - fact_key='ratio' — L1-computed achieved/required (scale ~0.8-1.7)
(a THIRD fact_key='required_rupa' row also exists but is stored under
ayanamsha_id='INVARIANT', so it never matches the ayanamsha_id=%s filter.)
With no fact_key pin and no ORDER BY, the dict-building loop keeps whichever
row the DB returns LAST for a given graha — non-deterministic across
otherwise-identical builds/replans.

P0-6 (D3_HARDCODED_DRIFT): whichever row won, its value was normalized by a
flat `raw / 1.0` constant instead of that graha's own L1 `required_rupa`
fact — a wrapper-local constant standing in for an L1-derived per-graha
value (forbidden per CLAUDE.md §N.5, "L1 is the authority over L2+
derivations").

Fix: pin fact_key='ratio' (ga_strength_writer / L1 already computes
`achieved_total / required_rupa` per graha — see
`ga_writers/ga_strength_writer.py::_build_shadbala_rows`, CR-18 — and stores
it under this same fact_category, ayanamsha-scoped) with a deterministic
ORDER BY. This mirrors the sibling `_fetch_shadbala` in bo_upaya.py, which
already reads this exact fact_key='ratio' row for the identical purpose.

Golden fixture (brief §5 C.8) — independently re-derived against the live
canonical chart 482012f1-710e-4a25-994a-93821f5871aa / lahiri_chitrapaksha
via `mcp__postgres__query` on 2026-07-28:

    SELECT fact_subject, fact_key, fact_value_num FROM chart_facts
    WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category='graha_shadbala_total' AND ayanamsha_id='lahiri_chitrapaksha';

  Graha    ratio     required  actual(rupa)  grade
  SUN      1.694     5.0       8.47          strong
  SAT      1.566     5.0       7.83          strong
  JUP      1.200     6.5       7.80          strong
  MER      1.078571  7.0       7.55          strong
  MAR      1.114     5.0       5.57          strong
  MOON     0.941667  6.0       5.65          weak
  VEN      0.843636  5.5       4.64          weak

confirmed against the live DB — no divergence from the brief's table.
"""
from __future__ import annotations

import random
import re
from typing import Any

import pytest

from pipeline.orchestrator.writers.bo_laksana import _build_strength_lookup

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri_chitrapaksha"

GOLDEN_RATIO = {
    "SUN": 1.694,
    "SAT": 1.566,
    "JUP": 1.200,
    "MER": 7.55 / 7.0,
    "MAR": 1.114,
    "MOON": 5.65 / 6.0,
    "VEN": 4.64 / 5.5,
}
GOLDEN_REQUIRED = {"SUN": 5.0, "SAT": 5.0, "JUP": 6.5, "MER": 7.0, "MAR": 5.0, "MOON": 6.0, "VEN": 5.5}
GOLDEN_RUPA = {"SUN": 8.47, "SAT": 7.83, "JUP": 7.8, "MER": 7.55, "MAR": 5.57, "MOON": 5.65, "VEN": 4.64}
GOLDEN_GRADE = {  # ratio >= 1.0 => strong (at/above classical minimum)
    "SUN": "strong", "SAT": "strong", "JUP": "strong", "MER": "strong",
    "MAR": "strong", "MOON": "weak", "VEN": "weak",
}


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def fetchall(self):
        return [dict(r) for r in self._rows]


class _FakeChartFactsConn:
    """Simulates the graha_shadbala_total slice of chart_facts closely enough
    to catch the P0-5 defect at the query level (not just the Python loop):

    - a `fact_key='...'` literal embedded in the SQL text (real code embeds
      it as a literal, not a bind param, exactly like the existing
      `fact_category='graha_shadbala_total'` literal) is honored as a filter;
    - rows are returned in INSERTION order when the SQL has no ORDER BY
      clause — the worst case a real unordered SELECT could produce — and in
      deterministic (fact_subject, fact_id) order when it does.
    """

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def execute(self, sql: str, params: list):
        chart_id, ayanamsha_id = params
        out = [
            r for r in self._rows
            if r["chart_id"] == chart_id
            and r["ayanamsha_id"] == ayanamsha_id
            and r["fact_category"] == "graha_shadbala_total"
        ]
        m = re.search(r"fact_key\s*=\s*'([^']+)'", sql)
        if m:
            out = [r for r in out if r["fact_key"] == m.group(1)]
        if "ORDER BY" in sql.upper():
            out = sorted(out, key=lambda r: (r["fact_subject"], r["fact_id"]))
        return _FakeCursor(out)


def _row(graha: str, fact_key: str, value: float, fact_id: str, ayanamsha: str = AYANAMSHA) -> dict:
    return {
        "chart_id": CHART_ID,
        "ayanamsha_id": ayanamsha,
        "fact_category": "graha_shadbala_total",
        "fact_subject": graha,
        "fact_key": fact_key,
        "fact_value_num": value,
        "fact_id": fact_id,
    }


def _golden_fixture_rows(shuffle_seed: "int | None" = None) -> list[dict]:
    """Realistic row set: 'rupa' + 'ratio' per classical graha, plus the
    INVARIANT 'required_rupa' row (out of ayanamsha-filter scope), exactly
    matching the live L1 schema confirmed above.
    """
    rows = []
    for i, graha in enumerate(GOLDEN_RATIO):
        rupa_row = _row(graha, "rupa", GOLDEN_RUPA[graha], fact_id=f"{graha}-rupa")
        ratio_row = _row(graha, "ratio", GOLDEN_RATIO[graha], fact_id=f"{graha}-ratio")
        req_row = _row(graha, "required_rupa", GOLDEN_REQUIRED[graha], fact_id=f"{graha}-req",
                        ayanamsha="INVARIANT")
        # Deliberately alternate insertion order per graha: this is what
        # makes the pre-fix "whichever row lands last" bug land on a
        # DIFFERENT fact_key for different grahas — the concrete shape of
        # the non-determinism P0-5 describes, not just a theoretical risk.
        if i % 2 == 0:
            rows += [ratio_row, rupa_row, req_row]
        else:
            rows += [rupa_row, ratio_row, req_row]
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(rows)
    return rows


def test_strength_lookup_matches_golden_ratio_table():
    """_build_strength_lookup must return the L1-computed ratio (actual/required),
    not a raw-rupa/1.0 restatement (P0-6)."""
    conn = _FakeChartFactsConn(_golden_fixture_rows())
    lookup = _build_strength_lookup(conn, CHART_ID, AYANAMSHA)

    for graha, expected_ratio in GOLDEN_RATIO.items():
        assert graha in lookup, f"{graha} missing from strength lookup"
        assert lookup[graha] == pytest.approx(expected_ratio, abs=1e-4), (
            f"{graha}: expected ratio {expected_ratio:.6f}, got {lookup[graha]!r} "
            f"(P0-6: still normalizing by flat /1.0 instead of the L1 ratio/required_rupa fact?)"
        )


def test_strength_lookup_grades_match_golden_table():
    conn = _FakeChartFactsConn(_golden_fixture_rows())
    lookup = _build_strength_lookup(conn, CHART_ID, AYANAMSHA)

    for graha, expected_grade in GOLDEN_GRADE.items():
        grade = "strong" if lookup[graha] >= 1.0 else "weak"
        assert grade == expected_grade, (
            f"{graha}: expected grade {expected_grade}, got {grade} (value={lookup[graha]!r})"
        )

    # Relative ordering: Sun is the single strongest graha, Venus the weakest
    # (golden table). Under the P0-6 bug every graha whose 'rupa' row won
    # gets clamped flat to 2.0 (raw rupas 4.64-8.47 all exceed the 2.0
    # ceiling), destroying this discrimination.
    assert max(lookup, key=lookup.get) == "SUN"
    assert min(lookup, key=lookup.get) == "VEN"


def test_strength_lookup_deterministic_regardless_of_row_order():
    """P0-5: result must be identical across differently-ordered/shuffled row sets."""
    baseline = _build_strength_lookup(_FakeChartFactsConn(_golden_fixture_rows()), CHART_ID, AYANAMSHA)
    assert baseline, "sanity: baseline lookup must not be empty"
    for seed in range(8):
        shuffled = _build_strength_lookup(
            _FakeChartFactsConn(_golden_fixture_rows(shuffle_seed=seed)), CHART_ID, AYANAMSHA
        )
        assert shuffled == baseline, f"non-deterministic result at shuffle seed={seed}: {shuffled} != {baseline}"


def test_nodes_have_no_classical_ratio_and_are_absent_not_defaulted():
    """Rahu/Ketu carry no classical shadbala requirement (ga_strength_writer's
    classical_grahas list excludes them) and so emit no 'ratio' row. Post-fix
    they are simply absent from the lookup — callers already default missing
    grahas to a neutral 1.0 (mirrors bo_upaya.py's documented fallback) —
    rather than being present with a fabricated/misscaled value.
    """
    rows = _golden_fixture_rows()
    rows.append(_row("RAH_MEAN", "rupa", 0.375, fact_id="rah-rupa"))
    rows.append(_row("KET_MEAN", "rupa", 0.625, fact_id="ket-rupa"))
    conn = _FakeChartFactsConn(rows)
    lookup = _build_strength_lookup(conn, CHART_ID, AYANAMSHA)

    assert "RAH_MEAN" not in lookup
    assert "KET_MEAN" not in lookup
