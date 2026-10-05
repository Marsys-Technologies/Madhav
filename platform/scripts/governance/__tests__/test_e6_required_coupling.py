"""test_e6_required_coupling.py -- the NARR-GUARD required-coupling pin (E6.1 follow-up, item 2).

The hole: NARR-GUARD (pin 16, N-94) binds bg_phaladeepika_latta's `prose_fields []` to Carr.D1 through TWO declarations, a `prose_coupling` and the D1 transcription
`carriage` it rests on. Deleting ONE of them is refused (`prose_empty_d1_problem` / `prose_coupling_problem`). Deleting BOTH leaves a bare `prose_fields []` on an asset with no
carriage, the shape bg_yogas / bg_doshas / bg_ontology / bo_laksana_rerank legitimately declare, and the Narr N/A silently falls back to the plain R03 rule: a cheaper state reached
by deleting two declarations, with no Carr.D1 behind it.

The pin: `asset_census.PROSE_COUPLING_REQUIRED` names the assets whose N/A is ONLY ever the coupled one. For them `prose_fields []` without a `prose_coupling` is refused by the
validator, read NO_DETECTOR by the measure-time glue, flagged `declared_prose_coupling_missing` for the rollup / gap ledger / certificate writer, and refused by the E6.3 reader
(`asset_elevation_tracker._e63_narr_coupling_ok`), which keeps a parity-pinned copy of the table.

Part 1 the table and the validator. Part 2 the measure-time glue. Part 3 the rollup and the ledger. Part 4 the E6.3 reader. Part 5 nothing moves (six saved censuses, fingerprint).
Every guard has a mutation test: with the table emptied the double deletion reads N/A again, so the detector can fail."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_narr_guard as ng  # noqa: E402
import test_e6_s1_elevation_reader as rd  # noqa: E402
from test_e6_s1_elevation_reader import real_registry  # noqa: E402,F401  (its autouse fixture: the reader tests' real registry)
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture the imported narr-guard tests use)

AID, ENTRY, NARR = ng.AID, ng.ENTRY, ng.NARR
PASS, NO_DET, NA = ac.PASS, ac.NO_DET, ac.NA
T = ng.T
BOTH_GONE = ("prose_coupling", "carriage")          # the double deletion


def _without(*keys, entry=ENTRY):
    return {k: v for k, v in entry.items() if k not in keys}


def _plain_na():
    """The measured record of a bare `prose_fields []` asset: what the writer-side glue emits for a plain R03 asset (no coupling block)."""
    return {c: dict(ac._na("prose_fields [] declared and no write to a column the declarations treat as narration", "no-prose")) for c in NARR}


# ───────────────────────── Part 1: the table and the validator ─────────────────────────

def test_the_table_names_exactly_the_latta_and_the_reader_holds_the_same_copy():
    assert set(ac.PROSE_COUPLING_REQUIRED) == {"bg_phaladeepika_latta"} == {AID}
    assert all(isinstance(v, str) and "N-94" in v for v in ac.PROSE_COUPLING_REQUIRED.values())
    assert T.E63_NARR_COUPLING_REQUIRED == frozenset(ac.PROSE_COUPLING_REQUIRED)         # two copies, one truth: a table that drifts from the reader's fails here


def test_the_committed_latta_entry_carries_its_coupling_so_the_pin_is_silent():
    assert ac.prose_coupling_required_problem(AID, ENTRY) is None
    assert ac.prose_coupling_required_problem(AID, ac.load_asset_declarations()[AID]) is None
    assert ac.validate_declarations(ng.DECL)                                               # the real file still validates as-is
    assert "declared_prose_coupling_missing" not in ac.declared_facts(ac.load_asset_declarations(), AID)


@pytest.mark.parametrize("entry", [None, {}, {"prose_fields": []}, {"prose_coupling": None}, {"prose_coupling": "carriage_d1"}, {"prose_coupling": []}, "x", 7])
def test_a_required_asset_without_a_prose_coupling_object_is_a_problem_in_every_shape(entry):
    why = ac.prose_coupling_required_problem(AID, entry)
    assert why and AID in why and "requires a prose_coupling to carriage_d1" in why and "N-94" in why


def test_an_asset_outside_the_table_is_never_a_problem():
    for a in ("bg_yogas", "bg_doshas", "bg_ontology", "bo_laksana_rerank", "bg_phaladeepika_latta_x", "", None, 3):
        for entry in (None, {}, {"prose_fields": []}, ENTRY):
            assert ac.prose_coupling_required_problem(a, entry) is None, (a, entry)


def test_the_double_deletion_is_refused_by_the_validator():
    with pytest.raises(ac.DeclarationsError, match="prose_coupling is missing.*bg_phaladeepika_latta requires a prose_coupling to carriage_d1"):
        ac.validate_declarations(ng._doc(lambda e: [e.pop(k) for k in BOTH_GONE]))
    # the full text names why: deleting the coupling together with the carriage must not make the asset cheaper
    with pytest.raises(ac.DeclarationsError, match="must not make the asset cheaper"):
        ac.validate_declarations(ng._doc(lambda e: [e.pop(k) for k in BOTH_GONE]))


@pytest.mark.parametrize("drop, match", [
    (("prose_coupling",), "needs a `prose_coupling` to carriage_d1"),                      # the carriage kept: the earlier (F1) guard, unchanged
    (("carriage",), "must declare a carriage check|declares a carriage|carriage check of nature"),   # the coupling kept: prose_coupling_problem, unchanged
])
def test_each_single_deletion_is_still_refused_by_its_own_guard(drop, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(ng._doc(lambda e: [e.pop(k) for k in drop]))


def test_the_pin_does_not_refuse_a_required_asset_that_declares_real_prose_or_nothing():
    """The pin only forbids the CHEAPER state (`prose_fields []` with no coupling). Declaring the prose columns the writer composes (a measured Narr, strictly harder) or leaving
    prose_fields undeclared (every check NO_DETECTOR) is not what it guards."""
    def real_prose(e):
        for k in BOTH_GONE:
            e.pop(k)
        e["prose_fields"] = ["effect_description"]
    ac.validate_declarations(ng._doc(real_prose, AID))
    def undeclared(e):
        for k in BOTH_GONE:
            e.pop(k)
        e.update(prose_fields=None, evidence_kind=None, evidence=dict(e["evidence"], prose_fields=None))
    ac.validate_declarations(ng._doc(undeclared, AID))


def test_MUTATION_without_the_table_the_validator_accepts_the_double_deletion(monkeypatch):
    doc = ng._doc(lambda e: [e.pop(k) for k in BOTH_GONE])
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(doc)
    monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
    assert ac.validate_declarations(doc)                                                    # the bare `prose_fields []` is the plain R03 shape: it takes the table to refuse it


# ───────────────────────── Part 2: the measure-time glue ─────────────────────────

def _checks(entry, aid=AID):
    return ac.prose_checks(aid, entry, ng._ctx())


def test_the_double_deletion_reads_no_detector_at_measure_time_never_na():
    out = _checks(_without(*BOTH_GONE))
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert out[c]["v"] == NO_DET and "requires a prose_coupling to carriage_d1" in out[c]["measured"] and AID in out[c]["measured"], c
        assert "cause" not in out[c]


def test_the_measure_time_glue_is_unchanged_where_the_coupling_is_declared_and_for_every_other_empty_asset():
    out = _checks(ENTRY)
    assert all(out[c]["v"] == NA and "prose_coupling" in out[c] for c in NARR)
    for a in ng.CONVERTED:      # no grandfather: a bare [] (the checked prose_none stripped) reads NO_DETECTOR on every Narr check
        ent = {k: v for k, v in ac.load_asset_declarations()[a].items() if k != "prose_none"}
        got = ac.prose_checks(a, ent, dict(table="t", own={"t": (["a"], {"a": "text"}, {})}, tests=(), vocabulary=set(), counts=None, paths=[], written={"t": {"a"}}))
        assert all(got[c]["v"] == NO_DET and "prose_none" in got[c]["measured"] for c in NARR), a
    # the hypothetical double deletion of an asset that is NOT required reads the plain N/A it always did
    out = ac.prose_checks("bo_laksana_rerank", _without(*BOTH_GONE), ng._ctx())
    assert all(out[c]["v"] == NO_DET and "prose_none" in out[c]["measured"] for c in NARR)       # N-150 R1: no bare-[] N/A is reachable for any asset


def test_MUTATION_without_the_table_the_double_deletion_reads_plain_na_at_measure_time(monkeypatch):
    assert _checks(_without(*BOTH_GONE))[NARR[0]]["v"] == NO_DET
    monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
    out = _checks(_without(*BOTH_GONE))
    assert all(out[c]["v"] == NO_DET and "prose_none" in out[c]["measured"] for c in NARR)       # N-150 R1: the cheaper state (a bare [] N/A) is no longer reachable at all for a non-enumerated asset


# ───────────────────────── Part 3: the rollup, the gap ledger ─────────────────────────

def _decl_with(entry):
    return {AID: entry} if entry is not None else {}


def test_declared_facts_flag_the_missing_coupling_for_a_required_asset_in_every_shape():
    for entry in (_without(*BOTH_GONE), _without("prose_coupling"), {}, None):
        facts = ac.declared_facts(_decl_with(entry), AID)
        assert facts.get("declared_prose_coupling_missing") is True, entry
    assert "declared_prose_coupling_missing" not in ac.declared_facts(_decl_with(ENTRY), AID)
    assert "declared_prose_coupling_missing" not in ac.declared_facts(_decl_with(_without(*BOTH_GONE, entry=ENTRY)), "bg_yogas")     # another asset: nothing
    assert ac.declared_facts({"bg_yogas": _without(*BOTH_GONE)}, "bg_yogas").get("declared_prose_coupling_missing") is None


def test_the_rollup_reads_no_detector_for_a_plain_narr_na_of_a_required_asset():
    """The record the rollup is handed is the bare R03 N/A (what an old census, or the measure-time glue under a double-deleted declaration of an older tool, holds); the facts, read
    from the declaration independently, are what bind it."""
    ms = _plain_na()
    facts = ac.declared_facts(_decl_with(_without(*BOTH_GONE)), AID)
    cell = ac.rollup_asset("L0", ms, facts)["Narr"]
    assert cell["v"] == NO_DET
    for chk in cell["checks"]:
        assert chk["v"] == NO_DET and "the asset declares prose_fields [] with a D1 transcription carriage but no prose_coupling" in chk["reason"]
    # the same record for an asset the pin does not name is no release either: no grandfather remains (N-150 R1), the plain unchecked N/A reads NO_DETECTOR
    assert ac.rollup_asset("L0", ms, ac.declared_facts({"bo_laksana_rerank": _without(*BOTH_GONE)}, "bo_laksana_rerank"))["Narr"]["v"] == NO_DET
    assert ac.rollup_asset("L0", ms, {})["Narr"]["v"] == NO_DET                              # N-150 R1: a plain N/A with no facts is no release


def test_the_rollup_with_the_coupling_present_is_unchanged():
    decl = ac.load_asset_declarations()
    facts = ac.declared_facts(decl, AID)
    assert ng._narr(ng._ms(ng._d1()), facts)[0]["v"] == NA                                  # D1 PASS + coupled block: the N/A stands, as before the pin
    assert ng._narr(ng._ms(ng._d1(rows=ng._one_word_off())), facts)[0]["v"] == NO_DET


def test_MUTATION_without_the_table_the_rollup_reads_the_double_deletion_as_na(monkeypatch):
    ms = _plain_na()
    assert ac.rollup_asset("L0", ms, ac.declared_facts(_decl_with(_without(*BOTH_GONE)), AID))["Narr"]["v"] == NO_DET
    monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
    assert ac.rollup_asset("L0", ms, ac.declared_facts(_decl_with(_without(*BOTH_GONE)), AID))["Narr"]["v"] == NO_DET       # N-150 R1: not even the mutation reaches N/A (latta is no enumerated legacy asset)


def test_the_gap_ledger_releases_no_narr_row_for_the_double_deletion(monkeypatch):
    facts = ac.declared_facts(_decl_with(_without(*BOTH_GONE)), AID)
    ms = _plain_na()
    for c in NARR:
        assert ac._na_released(c, ms[c], ms, "L0", facts) is False, c
    ok = ng._ms(ng._d1())
    good = ac.declared_facts(_decl_with(ENTRY), AID)
    assert all(ac._na_released(c, ok[c], ok, "L0", good) is True for c in NARR)           # the coupled N/A with its D1 PASS is still released
    monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
    facts_off = ac.declared_facts(_decl_with(_without(*BOTH_GONE)), AID)
    assert all(ac._na_released(c, ms[c], ms, "L0", facts_off) is False for c in NARR)      # N-150 R1: still not released with the pin removed (a plain record of a non-legacy asset)


def test_the_gap_ledger_facts_of_a_required_asset_stay_strict_when_the_declarations_file_is_unreadable(monkeypatch):
    """LOW-2: `_emit_facts` used to return None for EVERY asset when the declarations file could not be read, so the ledger's only guard was the record's own coupling block. A
    required asset now reads `declared_prose_coupling_missing` (asset-keyed); every other asset still reads None."""
    def boom():
        raise ac.DeclarationsError("unreadable")
    monkeypatch.setattr(ac, "load_asset_declarations", boom)
    latta, other = dict(asset_id=AID, measurements={}), dict(asset_id="bg_yogas", measurements={})
    assert ac._emit_facts(latta, {}) == {"declared_prose_coupling_missing": True} and ac._emit_facts(other, {}) is None and ac._emit_facts("x", {}) is None
    ms = _plain_na()                                          # a plain N/A record (its block dropped): not released for the latta, released for any other asset
    assert all(ac._na_released(c, ms[c], ms, "L0", ac._emit_facts(latta, {})) is False for c in NARR)
    assert all(ac._na_released(c, ms[c], ms, "L0", ac._emit_facts(other, {})) is False for c in NARR)     # N-150 R1: with no readable declaration a plain N/A is released for no asset
    monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
    assert all(ac._na_released(c, ms[c], ms, "L0", ac._emit_facts(latta, {})) is False for c in NARR)


# ───────────────────────── Part 4: the E6.3 reader ─────────────────────────

def test_the_reader_refuses_the_double_deletion_at_the_ref_in_every_census_shape(tmp_path):
    bare = _without(*BOTH_GONE)
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}
    assert ng.satisfied_narr(ng.nworld(tmp_path / "plain", plain, entry=bare)) == [False]                        # a census that records a plain N/A
    assert ng.satisfied_narr(ng.nworld(tmp_path / "full", ng._full(ng._d1()), entry=bare)) == [False]            # the full record and a D1 PASS: the declaration at the ref is what is wrong
    assert ng.satisfied_narr(ng.nworld(tmp_path / "nocensus", plain, entry=bare, text="{}")) == [False]
    assert ng.satisfied_narr(ng.nworld(tmp_path / "coupled", ng._full(ng._d1()))) == [True]                      # the committed entry still counts


def _rec(asset):
    return {"asset": asset, "layer": "L0", "criterion": "Narr.agree", "verdict": "N/A"}


def test_the_reader_fails_closed_when_a_required_asset_has_no_declaration_at_the_ref(monkeypatch):
    """The reader helper called directly (the world fixtures also fail on the declaration-sha binding, which would hide this branch): no entry at the ref for a REQUIRED asset is
    refused; for any other asset it is the old `True` (the declared rule alone decides, nothing to couple)."""
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, asset: None)
    assert T._e63_narr_coupling_ok("repo", "sha", _rec(AID), "census-src") is False
    assert T._e63_narr_coupling_ok("repo", "sha", _rec("bg_yogas"), "census-src") is True
    assert T._e63_narr_coupling_ok("repo", "sha", _rec("bg_phaladeepika_latta_x"), "census-src") is True


def test_MUTATION_a_reader_that_returns_true_for_an_absent_declaration_would_count_the_required_asset(monkeypatch):
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, asset: None)
    assert T._e63_narr_coupling_ok("repo", "sha", _rec(AID), "") is False
    monkeypatch.setattr(T, "E63_NARR_COUPLING_REQUIRED", frozenset())               # what `return not required` becomes if the branch is removed: the old `return True`
    assert T._e63_narr_coupling_ok("repo", "sha", _rec(AID), "") is True            # so the False above is earned by the REQUIRED branch, nothing else


def test_the_reader_refuses_a_required_asset_with_a_declaration_that_lacks_the_coupling(monkeypatch):
    """The entry exists but has neither word: the branch that decides to ASK the ref census (the `required` clause of the trigger): without it the reader would return True here."""
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, asset: _without(*BOTH_GONE))
    monkeypatch.setattr(T, "_e63_null_census_record", lambda repo, sha, rec: None)    # no census to ask: a coupled / required asset fails closed
    assert T._e63_narr_coupling_ok("repo", "sha", _rec(AID), "") is False
    assert T._e63_narr_coupling_ok("repo", "sha", _rec("bg_yogas"), "") is True       # an asset outside the table with the same shape is not asked at all
    monkeypatch.setattr(T, "E63_NARR_COUPLING_REQUIRED", frozenset())
    assert T._e63_narr_coupling_ok("repo", "sha", _rec(AID), "") is True              # mutation: without the table the trigger is skipped and the cheaper state counts


def bare_entry():
    return _without(*BOTH_GONE)


def test_the_reader_leaves_an_asset_outside_the_table_alone(tmp_path):
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}
    nocar = {"prose_fields": [], "evidence": ENTRY["evidence"]}
    for a in ("bg_yogas", "bg_doshas"):
        assert ng.satisfied_narr(ng.nworld(tmp_path / a, plain, entry=nocar, asset=a), asset=a) == [True], a


def test_MUTATION_the_reader_copy_of_the_table_is_what_stops_a_ref_census_that_predates_the_pin(tmp_path, monkeypatch):
    """A ref whose census does not hold the required table reads the double deletion as a plain N/A. The reader's own copy of the table is then the only thing that refuses it:
    emptied, the same world is counted; with the copy, it is not (fail closed)."""
    old = rd.CENSUS_TEXT.replace('    "bg_phaladeepika_latta": "N-94: its effect', '    "bg_phaladeepika_latta_not_the_pin": "N-94: its effect')
    assert old != rd.CENSUS_TEXT
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}
    bare = bare_entry()
    assert ng.satisfied_narr(ng.nworld(tmp_path / "with_copy", plain, entry=bare, census_src=old)) == [False]
    monkeypatch.setattr(T, "E63_NARR_COUPLING_REQUIRED", frozenset())
    T._E63_NARR_CACHE.clear()
    assert ng.satisfied_narr(ng.nworld(tmp_path / "no_copy", plain, entry=bare, census_src=old)) == [True]            # the cheaper state, counted: the copy is load-bearing


def test_MUTATION_a_drifted_reader_copy_stops_asking_the_census_and_the_cheaper_state_counts(tmp_path, monkeypatch):
    """The reader asks the ref's census about an asset only when ITS copy of the table names it (it holds no rule of its own). Empty the copy and a REAL world with the double
    deletion (the current census, a bare `prose_fields []` declaration, a plain N/A record) is counted: that is the failure the parity assertion of the first test exists to catch,
    shown as behaviour instead of as an inequality."""
    plain = {c: dict(v=NA, measured="x", cause="no-prose") for c in NARR}
    assert ng.satisfied_narr(ng.nworld(tmp_path / "with_copy", plain, entry=bare_entry())) == [False]
    monkeypatch.setattr(T, "E63_NARR_COUPLING_REQUIRED", frozenset())
    T._E63_NARR_CACHE.clear()
    assert ng.satisfied_narr(ng.nworld(tmp_path / "drifted_copy", plain, entry=bare_entry())) == [True]
    assert T.E63_NARR_COUPLING_REQUIRED != frozenset(ac.PROSE_COUPLING_REQUIRED)       # ... and the parity pin sees exactly this drift


# ───────────────────────── Part 5: nothing moves ─────────────────────────

SAVED = ng.SAVED


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_on_the_six_saved_censuses_the_pin_moves_no_cell_and_no_check(monkeypatch):
    """Re-roll every saved census (census_fresh/1e5781a, read only) with the pin on, with it off, and against the saved verdicts: 1143 cells, zero move, checks included."""
    decl = ac.load_asset_declarations()
    saved_all, on, off, n = {}, {}, {}, 0
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved_all[L] = d["rollup"]["layers"][L]
        on[L] = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        monkeypatch.setattr(ac, "PROSE_COUPLING_REQUIRED", {})
        off[L] = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        monkeypatch.undo()
    moved = []
    for L, cells in on.items():
        for aid, gates in cells.items():
            for g, c in gates.items():
                n += 1
                if c["v"] != saved_all[L][aid][g]["v"]:
                    moved.append(("saved", aid, g, saved_all[L][aid][g]["v"], c["v"]))
    assert n == 1143 and sorted(moved) == [("saved", a, "Narr", "N/A", "NO_DETECTOR") for a in ng.CONVERTED]      # E5.7: the three converted assets read NO_DETECTOR on a saved census until re-measured with the checked prose_none (a saved unchecked N/A is no release)
    assert on == off                                                                          # verdicts AND per-check readings identical with the pin removed: it decides nothing where the coupling is declared


def test_the_registry_revision_and_fingerprint_are_untouched():
    import test_e6_1_p1_registry_rollup as pin
    assert ac.registry_fingerprint() == pin.PINNED_FINGERPRINTS[ac.REGISTRY_REVISION]                  # the coupling pin adds nothing to the fingerprint: the CURRENT revision's pin still reproduces (never a hard-coded revision)
    assert not hasattr(ac, "PROSE_COUPLING_REQUIRED_IN_FINGERPRINT") and "PROSE_COUPLING_REQUIRED" not in json.dumps(ac.NA_CAUSES)
