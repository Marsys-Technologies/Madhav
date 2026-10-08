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
OK = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])


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
    assert [ac.CRITERION_REGISTRY[c]["revision"] for c in CRITS] == [3, 2, 4, 3]      # Build.registered 3: SS N-203 (the writer_sibling form); Idem.pattern 4: SS 2026-10-05 update-only (R5 moved it to 3); Build.exercised 3: SS R-c (legacy attempts vs the registry definition) moved it once more after R5
    for c in CRITS:
        assert "has_writer: false" in ac.CRITERION_REGISTRY[c]["applicability"], c


# ───────────────────────── the pure measurement ─────────────────────────

@pytest.mark.parametrize("fn", [lambda d: ac._measure_contract("bg_x", [], False, d), lambda d: ac._measure_idem("bg_x", [], "upsert", False, (), d)])
def test_contract_and_idem_carry_the_three_facts(fn):
    r = fn(True)
    assert r["v"] == NA and r["cause"] == "no-writer-registry-agrees" and r["no_writer"] == OK, r
    r = fn(False)
    assert r["v"] == NA and r["no_writer"] == dict(declared=False, registry_has_writer=False, register_files=0, register_mentions=[]) and "NOT declared" in r["measured"], r


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
@pytest.mark.parametrize("mut", ["no_block", "not_declared", "registry_true", "files_found", "files_missing_key", "declared_string", "block_not_dict", "mentions_present", "mentions_missing"])
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
    elif mut == "mentions_present":
        blk["register_mentions"] = ["writers/x.py"]
    elif mut == "mentions_missing":
        del blk["register_mentions"]
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


CENSUS_FILES = {"L0": "193639", "L1": "194909", "L2": "195251", "L3": "195534", "L4": "195644", "L5": "195749"}


def _all_layers():
    out = {}
    for L, ts in CENSUS_FILES.items():
        p = REPO / "00_ARCHITECTURE/control/census" / f"asset_census_2026-10-04T{ts}+0530.json"
        for a in json.loads(p.read_text(encoding="utf-8"))[L]["assets"]:
            out[(L, a["asset_id"])] = a
    return out


# The saved no-writer N/A cells across ALL SIX layers, and what N-150 R5 does to each (intended, stated moves; review fix MED):
RELEASED = {("L0", a, c) for a in NO_WRITER_L0 for c in ("Build.registered", "Build.contract", "Idem.pattern")} | {("L0", "bg_gochara_citation_resolution", "Build.exercised"),
                                                                                                                    ("L0", "bg_sarvatobhadra_grid", "Build.exercised")}
MOVED_TO_NO_DETECTOR = {("L0", "bg_nakshatra_medical", "Build.exercised"), ("L0", "bg_transit_engine", "Build.exercised"),       # an @register exists: the fact register_files == 0 is false
                        ("L5", "lel_events", "Build.registered"), ("L5", "lel_events", "Build.contract"), ("L5", "lel_events", "Idem.pattern"),      # registry-writerless, NOT declared
                        ("L5", "lel_events", "Build.exercised")}                                                                                   # (honest, conservative: no has_writer false is declared for it)


def test_every_saved_no_writer_n_a_across_all_layers_is_either_released_or_a_stated_move_to_no_detector():
    census, decl = _all_layers(), ac.load_asset_declarations()
    seen, released, moved = set(), set(), set()
    for (L, a), rec in census.items():
        for c in CRITS:
            m = rec["measurements"].get(c)
            if m and m["v"] == NA and m.get("cause") in ac.NO_WRITER_CAUSES[c]:
                assert rec["has_writer"] is False, (L, a, c)
                seen.add((L, a, c))
                declared = (decl.get(a) or {}).get("has_writer") is False
                blk = dict(declared=declared, registry_has_writer=False, register_files=1 if a in REGISTERED_BUT_FALSE else 0, register_mentions=[])
                v = _cell(c, dict(m, no_writer=blk))["v"]
                (released if v == NA else moved).add((L, a, c))
                assert v in (NA, NO_DET)
    assert released == RELEASED
    assert moved == MOVED_TO_NO_DETECTOR
    assert seen == RELEASED | MOVED_TO_NO_DETECTOR            # nothing else moves: the complete list across L0-L5


def test_lel_events_is_not_declared_has_writer_false():
    assert (ac.load_asset_declarations().get("lel_events") or {}).get("has_writer") is None


# ───────────────────────── review fixes: prefix-independent lookup, register( call mentions ─────────────────────────

def test_the_per_asset_register_lookup_is_prefix_independent(tmp_path, monkeypatch):
    """`registered_ids('')` sees an id that lacks the layer prefix (lel_events under L5's `mi_`): measure() reads the per-asset files from it."""
    w = tmp_path / "w"
    w.mkdir()
    (w / "lel_writer.py").write_text("from x import register\n@register('lel_events')\nclass W:\n    pass\n")
    monkeypatch.setattr(ac, "WRITERS", w)
    monkeypatch.setattr(ac, "_writer_files", lambda: [w / "lel_writer.py"])
    monkeypatch.setattr(ac, "_writer_modules", lambda: [("lel_writer.py", w / "lel_writer.py")])
    assert ac.registered_ids("mi_").get("lel_events") is None            # the layer-prefix filter hides it
    assert ac.registered_ids("").get("lel_events") == ["lel_writer.py"]  # the prefix-independent lookup finds it


def _mods(monkeypatch, tmp_path, src):
    f = tmp_path / "m.py"
    f.write_text(src)
    monkeypatch.setattr(ac, "_writer_modules", lambda: [("m.py", f)])
    ac._PARSED.clear()


@pytest.mark.parametrize("src", [
    "register('bg_x')(Cls)\n",                                         # register(x)(Cls)
    "import mod\n@mod.register('bg_x')\nclass C: pass\n",            # @mod.register
    "ASSET = 'bg_x'\nregister(ASSET)(Cls)\n",                          # a module constant
    "from other import ASSET_ID\nregister(ASSET_ID)(Cls)\n",           # an imported constant: unreadable, so it may be this asset
    "register(prefix + 'x')(Cls)\n",                                    # a computed id
])
def test_a_register_call_the_decorator_scan_cannot_see_is_named(monkeypatch, tmp_path, src):
    _mods(monkeypatch, tmp_path, src)
    assert ac.register_call_mentions("bg_x") == ["m.py"], src


@pytest.mark.parametrize("src", ["@register('bg_y')\nclass C: pass\n", "ASSET = 'bg_y'\n@register(ASSET)\nclass C: pass\n", "def f():\n    return 1\n"])
def test_an_unrelated_or_resolved_register_call_is_not_a_mention(monkeypatch, tmp_path, src):
    _mods(monkeypatch, tmp_path, src)
    assert ac.register_call_mentions("bg_x") == []


def test_the_real_discovery_set_has_no_register_call_mention_of_the_four_declared_assets():
    for a in NO_WRITER_L0:
        assert ac.register_call_mentions(a) == [], a


def test_a_mention_defeats_the_no_writer_release_end_to_end(monkeypatch, tmp_path):
    _mods(monkeypatch, tmp_path, "from other import ASSET_ID\nregister(ASSET_ID)(Cls)\n")
    rec = ac._measure_contract("bg_x", [], False, True)
    assert rec["v"] == NA and rec["no_writer"]["register_mentions"] == ["m.py"]
    assert _cell("Build.contract", rec)["v"] == NO_DET and "no `register(` call" in _cell("Build.contract", rec)["reason"]


# ───────────────────────── the committed declarations ─────────────────────────

def test_the_four_l0_no_writer_assets_declare_has_writer_false_and_nothing_else_does(l0):
    decl = ac.load_asset_declarations()
    assert sorted(a for a, e in decl.items() if e.get("has_writer") is False) == sorted(NO_WRITER_L0)
    for a in NO_WRITER_L0:
        assert l0[a]["has_writer"] is False and l0[a]["measurements"]["Build.registered"]["cause"] == "no-writer-registry-agrees"   # the registry row agrees
    for a in REGISTERED_BUT_FALSE:
        assert decl[a].get("has_writer") is None          # an @register exists: the declaration would be false
