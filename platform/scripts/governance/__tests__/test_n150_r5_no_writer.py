"""test_n150_r5_no_writer.py: SS N-150 R5 (REGISTRY_REVISION 26; Build.registered / Build.contract / Build.exercised revision 2, Idem.pattern revision 3).

A no-writer asset reads N/A for Build.registered, Build.contract, Build.exercised and Idem.pattern ONLY when ALL THREE agree: the asset's declaration says `has_writer: false`, the registry row says
has_writer false, and the @register scan found no writer file. The record carries them as `no_writer` {declared, registry_has_writer, register_files}; the rollup and the ledger release refuse a record
without (true, false, 0). A registry-only no-writer asset (no declaration) keeps reading NO_DETECTOR. A writer that IS registered (bg_nakshatra_medical, bg_transit_engine: registry false, @register found)
keeps its FAIL.

The real cells: the four L0 no-writer assets of the committed census (2026-10-04T193639: bg_ephemeris_engine, bg_gochara_citation_resolution, bg_panchanga, bg_sarvatobhadra_grid) carry the N/A
records with the no-writer causes; the pure helpers reproduce them and the rollup releases them only with the three facts.

Run: python -m pytest platform/scripts/governance/__tests__/test_n150_r5_no_writer.py -v
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NA, NO_DET = ac.NA, ac.NO_DET
REPO = HERE.parents[3]
L0_CENSUS = REPO / "00_ARCHITECTURE/control/census/asset_census_2026-10-04T193639+0530.json"
NO_WRITER_L0 = ("bg_ephemeris_engine", "bg_gochara_citation_resolution", "bg_panchanga", "bg_sarvatobhadra_grid")
REGISTERED_BUT_FALSE = ("bg_nakshatra_medical", "bg_transit_engine")
CRITS = ("Build.registered", "Build.contract", "Idem.pattern", "Build.exercised")
OK = dict(declared=True, registry_has_writer=False, register_files=0)


def _rec(crit, block=OK, cause=None):
    cause = cause or ("never-run-no-writer" if crit == "Build.exercised" else "no-writer-registry-agrees")
    r = ac._na("no writer", cause)
    if block is not None:
        r["no_writer"] = copy.deepcopy(block)
    return r


def _cell(crit, rec):
    return ac._check_contribution(crit, "L0", rec, None)


# ───────────────────────── the rules, the causes, the revisions ─────────────────────────

def test_the_five_rules_are_declared_with_the_decision_n150_r5():
    for rid in ("Build.registered#measured:no-writer-registry-agrees", "Build.contract#measured:no-writer-registry-agrees", "Idem.pattern#measured:no-writer-registry-agrees",
                "Build.exercised#measured:never-run-no-writer", "Build.exercised#measured:never-executed-no-writer"):
        assert "N-150 R5" in ac.NA_RULE_DECISIONS[rid], rid
    ac.validate_na_rule_decisions()


def test_each_touched_criterion_revision_moved_once_and_says_the_declaration_keyed_reading():
    assert [ac.CRITERION_REGISTRY[c]["revision"] for c in CRITS] == [2, 2, 3, 2]
    for c in CRITS:
        assert "has_writer: false" in ac.CRITERION_REGISTRY[c]["applicability"], c


# ───────────────────────── the pure measurement ─────────────────────────

@pytest.mark.parametrize("fn", [lambda d: ac._measure_contract("bg_x", [], False, d), lambda d: ac._measure_idem("bg_x", [], "upsert", False, (), d)])
def test_contract_and_idem_carry_the_three_facts(fn):
    r = fn(True)
    assert r["v"] == NA and r["cause"] == "no-writer-registry-agrees" and r["no_writer"] == OK, r
    r = fn(False)
    assert r["v"] == NA and r["no_writer"] == dict(declared=False, registry_has_writer=False, register_files=0) and "NOT declared" in r["measured"], r


@pytest.mark.parametrize("fn", [lambda: ac._measure_contract("bg_x", [], True, True), lambda: ac._measure_idem("bg_x", [], "upsert", True, (), True)])
def test_a_registry_that_says_a_writer_exists_is_never_an_na_whatever_is_declared(fn):
    r = fn()
    assert r["v"] == NO_DET and "no_writer" not in r and "cause" not in r, r


# ───────────────────────── the rollup and the ledger release ─────────────────────────

@pytest.mark.parametrize("crit", CRITS)
def test_the_rollup_releases_a_record_with_all_three_facts(crit):
    rec = _rec(crit)
    c = _cell(crit, rec)
    assert c["v"] == NA and "N-150 R5" in c["decision"], c
    assert ac._na_released(crit, rec)
    if crit == "Build.exercised":
        c2 = _cell(crit, _rec(crit, cause="never-executed-no-writer"))
        assert c2["v"] == NA and "N-150 R5" in c2["decision"]


@pytest.mark.parametrize("crit", CRITS)
@pytest.mark.parametrize("mut", ["no_block", "not_declared", "registry_true", "files_found", "files_missing_key", "declared_string", "block_not_dict"])
def test_the_rollup_never_releases_without_the_declaration_and_the_two_agreeing_facts(crit, mut):
    blk = copy.deepcopy(OK)
    if mut == "no_block":
        blk = None
    elif mut == "not_declared":
        blk["declared"] = False
    elif mut == "registry_true":
        blk["registry_has_writer"] = True
    elif mut == "files_found":
        blk["register_files"] = 1
    elif mut == "files_missing_key":
        del blk["register_files"]
    elif mut == "declared_string":
        blk["declared"] = "true"
    else:
        blk = True
    rec = _rec(crit, blk)
    c = _cell(crit, rec)
    assert c["v"] == NO_DET and "has_writer: false" in c["reason"], c
    assert not ac._na_released(crit, rec)


# ───────────────────────── the declaration ─────────────────────────

def test_only_false_is_a_declaration():
    assert ac.has_writer_problem({}) is None and ac.has_writer_problem({"has_writer": None}) is None and ac.has_writer_problem({"has_writer": False}) is None
    assert "has_writer" in ac._DECL_ENTRY_KEYS
    for v in (True, 0, "false", [False], {}):
        assert ac.has_writer_problem({"has_writer": v}), v
        with pytest.raises(ac.DeclarationsError):
            ac.validate_declarations(dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_x": dict(kind="data", has_writer=v)}))
    ac.validate_declarations(dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_x": dict(kind="data", has_writer=False)}))


# ───────────────────────── the real L0 cells ─────────────────────────

@pytest.fixture(scope="module")
def l0():
    return {a["asset_id"]: a for a in json.loads(L0_CENSUS.read_text(encoding="utf-8"))["L0"]["assets"]}


def test_the_committed_census_has_the_four_no_writer_assets_with_n_a_records(l0):
    for a in NO_WRITER_L0:
        assert l0[a]["has_writer"] is False
        for c in ("Build.registered", "Build.contract", "Idem.pattern"):
            assert l0[a]["measurements"][c]["v"] == NA and l0[a]["measurements"][c]["cause"] == "no-writer-registry-agrees", (a, c)
    assert {a for a in l0 if l0[a]["measurements"].get("Build.exercised", {}).get("cause") in ("never-run-no-writer", "never-executed-no-writer")} >= {"bg_gochara_citation_resolution", "bg_sarvatobhadra_grid"}


def test_without_the_block_those_saved_records_read_no_detector_and_with_it_na(l0):
    for a in NO_WRITER_L0:
        for c in ("Build.registered", "Build.contract", "Idem.pattern"):
            saved = l0[a]["measurements"][c]
            assert _cell(c, saved)["v"] == NO_DET, (a, c)                 # the census predates the declaration-keyed release
            assert _cell(c, dict(saved, no_writer=OK))["v"] == NA, (a, c)


def test_the_two_registered_writers_the_registry_calls_writerless_keep_their_fail(l0):
    for a in REGISTERED_BUT_FALSE:
        assert l0[a]["has_writer"] is False and l0[a]["measurements"]["Build.registered"]["v"] == "FAIL", a


def test_every_saved_no_writer_n_a_is_a_registry_writerless_asset_and_only_the_four_can_be_released(l0):
    """Build.exercised reads N/A for six registry-writerless assets; two of them (bg_nakshatra_medical, bg_transit_engine) HAVE an @register, so the fact `register_files == 0` is false for them
    and no declaration can release the cell (their Build.registered is already FAIL)."""
    seen = set()
    for a, rec in l0.items():
        for c in CRITS:
            m = rec["measurements"].get(c)
            if m and m["v"] == NA and m.get("cause") in ac.NO_WRITER_CAUSES[c]:
                assert rec["has_writer"] is False, (a, c)
                seen.add(a)
                if a in REGISTERED_BUT_FALSE:
                    assert _cell(c, dict(m, no_writer=dict(declared=True, registry_has_writer=False, register_files=1)))["v"] == NO_DET
    assert seen == set(NO_WRITER_L0) | set(REGISTERED_BUT_FALSE)
