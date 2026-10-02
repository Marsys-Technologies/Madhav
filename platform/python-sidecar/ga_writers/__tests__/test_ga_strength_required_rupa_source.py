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
  5. a missing L1 required fact floors the classical-graha composite row (honest null);
     the nodes (no classical minimum) floor with the named reason
     `no_classical_required_value_for_node` — no invented normaliser (SS ruling 2026-10-02);
  6. a FAILED SELECT raises (it is not a missing fact); floor reasons/text name every cause;
  7. ga_strength has no silent 5.0 default (`required_rupa_for` raises; mutation-tested).
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


def test_nodes_composite_rows_are_honest_nulls_with_a_named_reason():
    # SS ruling 2026-10-02 (CLAUDE.md N.7 item 6): Rahu/Ketu have NO classical required
    # minimum; the invented flat 5.0 normaliser is gone. One floored bphs_weighted row per
    # house, value NULL, tier 'floored', reason named; no simple_multiplication or
    # cross_formula_divergence row is emitted for a floored (graha, house).
    conn = _ChartFactsFakeConn(
        {"SUN": 8.0, "MOON": 6.0, "RAH_MEAN": 2.5},
        _required_rows_from_writer(strength_w.SHADBALA_REQUIRED),
    )
    rows = _composite(conn)
    rahu = [r for r in rows if r["fact_subject"].startswith("RAH_MEAN_IN_HOUSE_")]
    assert len(rahu) == 12                                   # 12 houses x ONE floored row
    assert {r["fact_key"] for r in rahu} == {"bphs_weighted"}
    for r in rahu:
        assert r["fact_value_num"] is None
        assert r["verification_pass_status"] == "floored"
        assert r["fact_value_jsonb"] == {
            "floored": True, "reason": "no_classical_required_value_for_node"}
        assert "no classical required shadbala value exists for the nodes" in r["citation_human"]
        assert "5.0" not in r["citation_human"]
    assert structural_w.NODE_NO_CLASSICAL_REQUIRED_REASON == "no_classical_required_value_for_node"


def test_the_invented_node_normaliser_is_gone():
    assert not hasattr(structural_w, "_NODE_LEGACY_COMPOSITE_REQUIRED")
    src = open(structural_w.__file__, encoding="utf-8").read()
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
    assert "_NODE_LEGACY_COMPOSITE_REQUIRED" not in code


def test_node_floor_also_names_a_missing_ga3_input():
    conn = _ChartFactsFakeConn(
        {"SUN": 8.0, "MOON": 6.0},   # no RAH_MEAN rupa
        _required_rows_from_writer(strength_w.SHADBALA_REQUIRED),
    )
    rows = _composite(conn)
    rahu = [r for r in rows if r["fact_subject"].startswith("RAH_MEAN_IN_HOUSE_")]
    assert len(rahu) == 12
    assert all(r["fact_value_jsonb"]["reason"] ==
               "no_classical_required_value_for_node+missing_ga3_shadbala_or_bhava_bala_fact"
               for r in rahu)


def test_classical_grahas_are_not_floored_when_all_inputs_exist():
    conn = _ChartFactsFakeConn(
        {"SUN": 8.0, "MOON": 6.0, "RAH_MEAN": 2.5},
        _required_rows_from_writer(strength_w.SHADBALA_REQUIRED),
    )
    rows = _composite(conn)
    for subj in ("SUN", "MOON"):
        own = [r for r in rows if r["fact_subject"].startswith(f"{subj}_IN_HOUSE_")]
        assert len(own) == 36                                 # 12 houses x 3 keys
        assert all(r["fact_value_jsonb"] is None or not r["fact_value_jsonb"].get("floored")
                   for r in own)


# ── 6. a FAILED read raises; only a genuinely missing fact floors (review LOW-1) ──────

class _RaisingConn:
    """A connection whose SELECT fails (e.g. a dropped connection, a permission error)."""

    def cursor(self, *a, row_factory=None, **k):
        return _RaisingCursor()


class _RaisingCursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        raise RuntimeError("simulated failed SELECT")

    def fetchall(self):  # pragma: no cover - never reached
        return []


def test_failed_required_rupa_select_propagates_not_floors():
    with pytest.raises(RuntimeError, match="simulated failed SELECT"):
        structural_w._load_required_rupa_map(_RaisingConn(), "chart-x")


def test_failed_shadbala_bhava_select_propagates_not_floors():
    with pytest.raises(RuntimeError, match="simulated failed SELECT"):
        structural_w._load_shadbala_and_bhava_fact_ids(
            _RaisingConn(), "chart-x", "lahiri_chitrapaksha")


def test_composite_build_propagates_a_failed_select_instead_of_flooring_seven_grahas():
    with pytest.raises(RuntimeError, match="simulated failed SELECT"):
        _composite(_RaisingConn())


def test_a_genuinely_missing_fact_is_an_empty_map_not_an_error():
    conn = _ChartFactsFakeConn({}, [])
    assert structural_w._load_required_rupa_map(conn, "chart-x") == {}


# ── 7. floor reason and citation text name the ACTUAL missing input(s) (review LOW-2) ──

def _sun_floor_rows(rupa, required_rows):
    conn = _ChartFactsFakeConn(rupa, required_rows)
    rows = _composite(conn)
    return [r for r in rows if r["fact_subject"].startswith("SUN_IN_HOUSE_")]


def _all_but_sun_required():
    return [r for r in _required_rows_from_writer(strength_w.SHADBALA_REQUIRED)
            if r["subject"] != "SUN"]


def test_floor_text_names_only_the_missing_l1_required_fact_when_that_is_the_reason():
    sun = _sun_floor_rows({"SUN": 5.74, "MOON": 6.0, "RAH_MEAN": 1.0}, _all_but_sun_required())
    assert len(sun) == 12
    for r in sun:
        assert r["fact_value_jsonb"]["reason"] == "missing_l1_required_rupa_fact"
        assert "missing the L1 required_rupa fact" in r["citation_human"]
        assert "GA3" not in r["citation_human"]          # the old text blamed GA3 shadbala/bhava_bala


def test_floor_text_names_only_the_missing_ga3_fact_when_that_is_the_reason():
    required = _required_rows_from_writer(strength_w.SHADBALA_REQUIRED)
    sun = _sun_floor_rows({"MOON": 6.0, "RAH_MEAN": 1.0}, required)   # Sun's achieved rupa absent
    assert len(sun) == 12
    for r in sun:
        assert r["fact_value_jsonb"]["reason"] == "missing_ga3_shadbala_or_bhava_bala_fact"
        assert "missing the GA3 shadbala fact" in r["citation_human"]
        assert "required_rupa" not in r["citation_human"]


def test_floor_reason_and_text_name_both_when_both_inputs_are_missing():
    sun = _sun_floor_rows({"MOON": 6.0, "RAH_MEAN": 1.0}, _all_but_sun_required())
    assert len(sun) == 12
    for r in sun:
        assert r["fact_value_jsonb"]["reason"] == (
            "missing_l1_required_rupa_fact+missing_ga3_shadbala_or_bhava_bala_fact")
        assert "missing the L1 required_rupa fact and the GA3 shadbala fact" in r["citation_human"]


def test_composite_floor_detail_names_every_missing_input_and_refuses_an_empty_floor():
    f = structural_w._composite_floor_detail
    assert f(required_missing=False, shadbala_missing=False, bhava_missing=True) == (
        "missing_ga3_shadbala_or_bhava_bala_fact", "missing the GA3 bhava_bala fact")
    assert f(required_missing=True, shadbala_missing=True, bhava_missing=True) == (
        "missing_l1_required_rupa_fact+missing_ga3_shadbala_or_bhava_bala_fact",
        "missing the L1 required_rupa fact and the GA3 shadbala fact and the GA3 bhava_bala fact")
    with pytest.raises(ValueError):
        f(required_missing=False, shadbala_missing=False, bhava_missing=False)


# ── 8. ga_strength: no silent 5.0 default (SS (b)); the citation reads the right table row ──

def _raises_for_a_graha_outside_the_table(fn) -> bool:
    try:
        fn("Rahu")
    except ValueError:
        return True
    except Exception:  # any other exception is not the contracted failure
        return False
    return False


def test_required_rupa_for_raises_for_anything_outside_the_seven():
    for bad in ("Rahu", "Ketu", "SUN", "sun", "Lagna", ""):
        with pytest.raises(ValueError, match="no classical required shadbala"):
            strength_w.required_rupa_for(bad)
    for g, v in SOURCE_RUPA_NOTE.items():
        assert strength_w.required_rupa_for(g) == v


def test_mutation_reintroducing_the_default_is_caught():
    """The raise-check has teeth: the real function passes it, a mutant that silently
    defaults to 5.0 (the removed `.get(graha, 5.0)`) fails it."""
    assert _raises_for_a_graha_outside_the_table(strength_w.required_rupa_for)
    mutant = lambda g: strength_w.SHADBALA_REQUIRED.get(g, 5.0)  # noqa: E731
    assert not _raises_for_a_graha_outside_the_table(mutant)


def test_ga_strength_source_has_no_defaulting_lookup_of_the_required_table():
    src = open(strength_w.__file__, encoding="utf-8").read()
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())  # comments stripped
    assert not re.search(r"SHADBALA_REQUIRED\s*\.get\s*\(", code)


@pytest.mark.parametrize("graha", sorted(SOURCE_RUPA_NOTE))
def test_total_rupa_citation_states_the_graha_own_required_value(graha):
    # Before: `graha` was the display string ('SUN'), a miss against the Title-case table, so
    # the silent default made EVERY classical graha read "vs required 5.00 rupa" (Moon read
    # "surplus 0.65 vs required 5.00" beside a ratio row saying below-minimum).
    text = strength_w._citation_human_strength(
        "graha_shadbala_total", SUBJECT[graha], "rupa", 5.65, "lahiri_chitrapaksha")
    assert f"vs required {SOURCE_RUPA_NOTE[graha]:.2f} rupa" in text


def test_total_rupa_citation_for_nodes_states_no_classical_minimum():
    for subj in ("RAH_MEAN", "KET_MEAN"):
        text = strength_w._citation_human_strength(
            "graha_shadbala_total", subj, "rupa", 0.375, "lahiri_chitrapaksha")
        assert "no classical required minimum exists for the nodes" in text
        assert "vs required" not in text


def test_total_rupa_citation_for_an_unknown_subject_raises():
    with pytest.raises(ValueError):
        strength_w._citation_human_strength(
            "graha_shadbala_total", "NOT_A_GRAHA", "rupa", 1.0, "lahiri_chitrapaksha")


def test_emitted_total_rupa_rows_carry_the_graha_own_required_in_their_citation():
    totals = {g: 6.0 for g in SOURCE_RUPA_NOTE}
    rows = _shadbala_rows(totals)
    cit = {r["fact_subject"]: r["citation_human"] for r in rows
           if r["fact_category"] == "graha_shadbala_total" and r["fact_key"] == "rupa"}
    assert "vs required 6.50 rupa" in cit["SUN"]
    assert "vs required 7.00 rupa" in cit["MER"]
