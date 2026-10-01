"""S-L1 (Suvarna): the classical required (minimum) shadbala — single source of truth.

Source: BPHS ch.27 śl.32-33 (R. Santhanam trans.; corpus chunk bphs_pg0286_c01 and
00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt):
"390, 360, 300, 420, 390, 330 and 300 Virupas are the Shadbala Pindas needed for the
Sun etc. (upto Saturn) to be considered strong"; the translator's note gives the same in
rupas (Sun 6.5, Moon 6.0, Mars 5.0, Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0).
Independently corroborated by Phaladīpikā IV.22-23 (chunk phaladeepika_pg0079_c01) and by
Pravāha's sad_bala_sufficient v1.0 thresholds (PR #2869).

The Sun was stored as 5.0 before this fix. This module pins:
  1. the seven classical values (golden, from the source — fails if any differs);
  2. the emitted `graha_shadbala_total|required_rupa` rows and the derived `ratio`;
  3. the Sun's ratio old vs new from stored achieved totals (fixture, not live);
  4. ga_structural carries NO shadow copy: it READS the L1 fact, and follows a mutation
     of ga_strength_writer.SHADBALA_REQUIRED (CLAUDE.md §N.5 / §N.7 item 3);
  5. a missing L1 required fact floors the classical-graha composite row (honest null),
     and the nodes keep their pre-existing (named) legacy default.
"""
from __future__ import annotations

import re

import pytest

from ga_writers import ga_strength_writer as strength_w
from ga_writers import ga_structural_writer as structural_w

# BPHS ch.27 śl.32-33, verbatim figures. Moon's virupa glyph is OCR-degraded in the verse
# line ("3*0") and Mercury's too ("42C"); both are fixed by the translator's explicit rupa
# note (6.0 / 7.0) and by Phaladīpikā IV.22 (6 / 7 rupas).
SOURCE_VIRUPA = {"Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420,
                 "Jupiter": 390, "Venus": 330, "Saturn": 300}
SOURCE_RUPA_NOTE = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
                    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
SUBJECT = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
           "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT"}


# ── 1. golden: all seven values from the source ──────────────────────────────

@pytest.mark.parametrize("graha", sorted(SOURCE_RUPA_NOTE))
def test_required_rupa_matches_bphs_ch27_for_every_graha(graha):
    assert strength_w.SHADBALA_REQUIRED[graha] == SOURCE_RUPA_NOTE[graha]


@pytest.mark.parametrize("graha", sorted(SOURCE_VIRUPA))
def test_required_rupa_is_virupa_over_sixty(graha):
    assert strength_w.SHADBALA_REQUIRED_VIRUPA[graha] == SOURCE_VIRUPA[graha]
    assert strength_w.SHADBALA_REQUIRED[graha] == SOURCE_VIRUPA[graha] / 60


def test_table_has_exactly_the_seven_classical_grahas():
    assert set(strength_w.SHADBALA_REQUIRED) == set(SOURCE_RUPA_NOTE)


def test_sun_is_six_and_a_half_not_five():
    assert strength_w.SHADBALA_REQUIRED["Sun"] == 6.5


# ── 2. emitted rows ──────────────────────────────────────────────────────────

def _shadbala_rows(totals: dict[str, float]):
    shadbala = {
        g: {"sthana": 1.0, "dig": 1.0, "kala": 1.0, "cheshta": 1.0,
            "naisargika": 1.0, "drik": 1.0, "total": totals[g]}
        for g in totals
    }
    empty = {g: {} for g in shadbala}
    return strength_w._build_shadbala_rows(
        shadbala, empty, empty, "chart-x", "build-x", "lahiri_chitrapaksha",
        "2026-10-02T00:00:00Z", "eng/1.0", "single_pass",
    )


def test_emitted_required_rupa_rows_are_the_source_values_under_invariant():
    rows = _shadbala_rows({g: 6.0 for g in SOURCE_RUPA_NOTE})
    req = {r["fact_subject"]: r for r in rows
           if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "required_rupa"}
    assert set(req) == set(SUBJECT.values())
    for graha, subj in SUBJECT.items():
        assert req[subj]["fact_value_num"] == SOURCE_RUPA_NOTE[graha]
        assert req[subj]["ayanamsha_id"] == "INVARIANT"
        assert req[subj]["unit"] == "rupa"


# ── 3. the Sun's ratio, old vs new, from stored achieved totals (fixtures) ───
# Achieved Sun rupa as stored in chart_facts (graha_shadbala_total|rupa, lahiri_chitrapaksha),
# read 2026-10-02: native 482012f1 = 8.47, Abhinandan 1c826d5a = 7.2, cb73cd3d = 5.74.
STORED_SUN_ACHIEVED = {"482012f1": 8.47, "1c826d5a": 7.2, "cb73cd3d": 5.74}
# (old stored ratio at required 5.0, new ratio at required 6.5)
SUN_RATIO_OLD_NEW = {
    "482012f1": (1.694, 8.47 / 6.5),   # 1.3031 — still at/above the minimum
    "1c826d5a": (1.44, 7.2 / 6.5),     # 1.1077 — still at/above
    "cb73cd3d": (1.148, 5.74 / 6.5),   # 0.8831 — flips from "at/above" to BELOW the minimum
}


@pytest.mark.parametrize("chart", sorted(STORED_SUN_ACHIEVED))
def test_sun_ratio_old_vs_new_from_stored_achieved_totals(chart):
    achieved = STORED_SUN_ACHIEVED[chart]
    old_ratio, new_ratio = SUN_RATIO_OLD_NEW[chart]
    assert achieved / 5.0 == pytest.approx(old_ratio, abs=1e-9)  # what was stored
    totals = {g: 6.0 for g in SOURCE_RUPA_NOTE}
    totals["Sun"] = achieved
    rows = _shadbala_rows(totals)
    ratio = {r["fact_subject"]: r["fact_value_num"] for r in rows
             if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "ratio"}
    assert ratio["SUN"] == pytest.approx(new_ratio, abs=1e-12)
    assert ratio["SUN"] != pytest.approx(old_ratio, abs=1e-6)
    # the six non-Sun ratios are unchanged by the fix
    assert ratio["MOON"] == pytest.approx(6.0 / 6.0)
    assert ratio["MER"] == pytest.approx(6.0 / 7.0)


def test_cb73_sun_flips_below_classical_minimum():
    old, new = SUN_RATIO_OLD_NEW["cb73cd3d"]
    assert old >= 1.0 > new


# ── 4. ga_structural has no shadow copy; it follows the ga_strength table ────

def test_ga_structural_no_longer_carries_its_own_required_table():
    assert not hasattr(structural_w, "_COMPOSITE_SHADBALA_REQUIRED")
    src = open(structural_w.__file__, encoding="utf-8").read()
    # (the old name may still be MENTIONED in a docstring explaining the removal; it must
    # not be ASSIGNED or referenced in code)
    assert not re.search(r"^\s*_COMPOSITE_SHADBALA_REQUIRED\b\s*[:=]", src, re.M)
    assert not re.search(r"_COMPOSITE_SHADBALA_REQUIRED\s*\.get", src)
    # no per-graha literal required table re-introduced (e.g. '"Sun": 5.0, "Moon": 6.0')
    assert not re.search(r'"Sun"\s*:\s*[56]\.[05]\s*,\s*"Moon"\s*:\s*6\.0', src)


class _ChartFactsFakeConn:
    """Serves graha_shadbala_total rows keyed on the SQL's literal fact_key / ayanamsha
    predicates, so the pinned INVARIANT query is actually exercised."""

    def __init__(self, rupa: dict[str, float], required_rows: list[dict]):
        self._rupa = rupa
        self._required = required_rows
        self.queries: list[str] = []

    def cursor(self, *a, row_factory=None, **k):
        return _FakeCursor(self)


class _FakeCursor:
    def __init__(self, conn):
        self._c = conn
        self._out: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._c.queries.append(sql)
        if "house_bhava_bala_total" in sql:
            self._out = [(f"HOUSE_{h}", 5.0, f"fid-bb-{h}") for h in range(1, 13)]
        elif "'required_rupa'" in sql:
            assert "ayanamsha_id = 'INVARIANT'" in sql, "required_rupa read must be INVARIANT-scoped"
            assert "ORDER BY" in sql, "required_rupa read must carry a total ORDER BY"
            self._out = [(r["subject"], r["value"], r["fact_id"]) for r in self._c._required]
        elif "'rupa'" in sql:
            self._out = [(s, v, f"fid-rupa-{s}") for s, v in self._c._rupa.items()]
        else:
            self._out = []

    def fetchall(self):
        return list(self._out)


_CHART_OUTPUT = {
    "grahas": [
        {"name": "Sun", "house": 10, "dignity_status": "neutral"},
        {"name": "Moon", "house": 1, "dignity_status": "neutral"},
        {"name": "Rahu", "house": 2, "dignity_status": "neutral"},
    ]
}


def _required_rows_from_writer(table: dict[str, float]):
    """Feed the stored `required_rupa` rows exactly as ga_strength_writer would emit them
    (value taken from the writer's table — the single source of truth)."""
    return [{"subject": SUBJECT[g], "value": v, "fact_id": f"fid-req-{SUBJECT[g]}"}
            for g, v in table.items()]


def _composite(conn):
    return structural_w._build_composite_strength_rows(
        conn, _CHART_OUTPUT, "chart-x", "build-x", "lahiri_chitrapaksha",
        "2026-10-02T00:00:00Z", "eng/1.0",
    )


def _sun_h1_bphs(rows):
    (row,) = [r for r in rows
              if r["fact_subject"] == "SUN_IN_HOUSE_1" and r["fact_key"] == "bphs_weighted"]
    return row


def test_composite_reads_the_l1_required_fact_not_a_local_constant():
    # Sun achieved 5.74 (cb73cd3d-like): ratio = 5.74/6.5 = 0.8831 under the corrected table.
    conn = _ChartFactsFakeConn(
        {"SUN": 5.74, "MOON": 6.0, "RAH_MEAN": 1.0},
        _required_rows_from_writer(strength_w.SHADBALA_REQUIRED),
    )
    row = _sun_h1_bphs(_composite(conn))
    assert "shadbala_ratio=0.8831" in row["citation_human"]
    # the L1 required fact is cited in the derivation ledger (B.3) next to the achieved fact
    assert "fid-req-SUN" in row["constituent_facts_array"]
    assert "fid-rupa-SUN" in row["constituent_facts_array"]


def test_mutating_the_ga_strength_table_moves_ga_structural(monkeypatch):
    """Mutation test: change the SINGLE table in ga_strength_writer, regenerate the L1
    rows it would store, and ga_structural's composite follows — proving there is no
    second copy that could disagree."""
    achieved = {"SUN": 5.74, "MOON": 6.0, "RAH_MEAN": 1.0}

    def sun_ratio_text():
        conn = _ChartFactsFakeConn(
            achieved, _required_rows_from_writer(strength_w.SHADBALA_REQUIRED))
        return _sun_h1_bphs(_composite(conn))["citation_human"]

    baseline = sun_ratio_text()
    assert "shadbala_ratio=0.8831" in baseline          # 5.74 / 6.5
    monkeypatch.setitem(strength_w.SHADBALA_REQUIRED, "Sun", 5.0)  # the OLD, wrong value
    assert "shadbala_ratio=1.0000" in sun_ratio_text()  # min(1, 5.74/5.0)
    monkeypatch.setitem(strength_w.SHADBALA_REQUIRED, "Sun", 8.0)
    assert "shadbala_ratio=0.7175" in sun_ratio_text()  # 5.74 / 8.0


def test_missing_l1_required_for_a_classical_graha_floors_the_row_honestly():
    # Sun's required fact absent; Moon's present. No substituted default (§N.7 item 6).
    conn = _ChartFactsFakeConn(
        {"SUN": 5.74, "MOON": 6.0, "RAH_MEAN": 1.0},
        [r for r in _required_rows_from_writer(strength_w.SHADBALA_REQUIRED)
         if r["subject"] != "SUN"],
    )
    rows = _composite(conn)
    sun = [r for r in rows if r["fact_subject"].startswith("SUN_IN_HOUSE_")]
    assert len(sun) == 12 and all(r["fact_value_num"] is None for r in sun)
    assert all(r["fact_value_jsonb"]["floored"] is True for r in sun)
    assert all(r["fact_value_jsonb"]["reason"] == "missing_l1_required_rupa_fact" for r in sun)
    moon = [r for r in rows if r["fact_subject"].startswith("MOON_IN_HOUSE_")]
    assert all(r["fact_value_num"] is not None for r in moon if r["fact_key"] == "bphs_weighted")


def test_nodes_keep_their_named_legacy_default_and_are_unaffected():
    conn = _ChartFactsFakeConn(
        {"SUN": 8.0, "MOON": 6.0, "RAH_MEAN": 2.5},
        _required_rows_from_writer(strength_w.SHADBALA_REQUIRED),
    )
    rows = _composite(conn)
    rahu = [r for r in rows if r["fact_subject"].startswith("RAH_MEAN_IN_HOUSE_")]
    assert len(rahu) == 36  # 12 houses x 3 keys — not floored
    assert structural_w._NODE_LEGACY_COMPOSITE_REQUIRED == 5.0
    assert any("shadbala_ratio=0.5000" in r["citation_human"] for r in rahu)  # 2.5 / 5.0
