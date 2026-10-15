"""test_n150_r2_lint_not_applicable.py: SS N-150 R2 (REGISTRY_REVISION 26, Narr.lint revision 4).

"The narration lints are not applicable to this asset" (no chart_facts fact_category selection in the writer scope, no raw-token narrative column) reads N/A (cause
lint-not-applicable, rule `Narr.lint#measured:lint-not-applicable`, decision N-150 R2) ONLY when the asset DECLARES `lint_none` {why, evidence} AND the lint scan's own surface test
agrees (a scanned writer file, applied == []). Never on the declaration alone: a contradicted declaration reads NO_DETECTOR, an undeclared asset keeps today's NO_DETECTOR.

The nine real cells (committed censuses 2026-10-04: L0 bg_compendium_index, bg_remedies; L1 ga_positions, ga_sensitive, ga_strength; L2 bo_anveshana, bo_cdlm_summary, bo_cgm_motifs,
bo_sangati) are reproduced by the pure scan over the real writer scope (no database).

Run: python -m pytest platform/scripts/governance/__tests__/test_n150_r2_lint_not_applicable.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NA, NO_DET = ac.NA, ac.NO_DET
REPO = HERE.parents[3]
EV = "platform/scripts/governance/asset_census.py:1"
LN = dict(why="the writer selects no chart_facts by fact_category and writes no raw-token narrative column", evidence=EV)
NINE = {"L0": ("bg_compendium_index", "bg_remedies"), "L1": ("ga_positions", "ga_sensitive", "ga_strength"),
        "L2": ("bo_anveshana", "bo_cdlm_summary", "bo_cgm_motifs", "bo_sangati")}
E57_L2_LINT_NONE = ("bo_cgm_paths", "bo_samskara", "bo_chart_gestalt", "bo_grounding", "bo_pramana_mapa")     # E5.7 L2 fill: lint_none declared (the scan agrees); not in the rev-25 committed census
E57_LINT_NONE = {"L0": ("bg_vedha_malefic_scale", "bg_rules")}     # SS 2026-10-05: lint_none declared (the scan agrees); not in the rev-25 committed census. bg_rules: lint_none added by the N-431 declarations walk (R1, reworded SS N-457), the scan agrees
CENSUS = {"L0": "193639", "L1": "194909", "L2": "195251"}
GOOD_SQL = "def f(c):\n    return c.execute(\"SELECT fact_value_text FROM chart_facts WHERE fact_category = 'x' AND fact_key = 'k' ORDER BY fact_id LIMIT 1\")\n"


def _w(tmp_path, body, name="w.py"):
    p = tmp_path / name
    p.write_text(body)
    return p


# ───────────────────────── the scan (pure) ─────────────────────────

def test_declared_and_the_scan_agrees_reads_na_with_the_block(tmp_path):
    r = ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x + 1\n")], ["citation_human"], LN)
    assert r["v"] == NA and r["cause"] == "lint-not-applicable" and r["applied"] == [], r
    assert r["lint_none"] == dict(why=LN["why"], evidence=EV, scope_files=1, applied=[], beyond=[])
    assert "N-150 R2" in r["measured"]


def test_undeclared_keeps_the_old_no_detector(tmp_path):
    r = ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x + 1\n")], ["citation_human"])
    assert r["v"] == NO_DET and "not applicable" in r["measured"] and "cause" not in r


@pytest.mark.parametrize("body,cols,surface", [(GOOD_SQL, ["citation_human"], "fact-category-pin"),
                                               ("def f(x):\n    return x\n", ["signal_headline_text"], "raw-token")])
def test_a_declaration_the_scan_contradicts_reads_no_detector_never_na_never_pass(tmp_path, body, cols, surface):
    r = ac.narr_lint_scan([_w(tmp_path, body)], cols, LN)
    assert r["v"] == NO_DET and surface in r["measured"] and "contradicted" in r["measured"] and r["applied"] == [surface], r


def test_a_real_violation_stays_a_fail_whatever_is_declared(tmp_path):
    bad = _w(tmp_path, "def f(c):\n    return c.execute(\"SELECT fact_value_text FROM chart_facts WHERE fact_category = 'x'\")\n")
    r = ac.narr_lint_scan([bad], ["citation_human"], LN)
    assert r["v"] == ac.FAIL, r


def test_no_file_in_scope_is_no_detector_even_when_declared():
    assert ac.narr_lint_scan([], ["citation_human"], LN)["v"] == NO_DET


# ───────────────────────── the rollup refuses the declaration alone ─────────────────────────

def _cell(meas):
    return ac._check_contribution("Narr.lint", "L1", meas, None)


def test_the_rule_and_the_cause_are_declared_with_the_decision_n150_r2():
    assert "lint-not-applicable" in ac.NA_CAUSES["Narr.lint"]
    assert "N-150 R2" in ac.NA_RULE_DECISIONS["Narr.lint#measured:lint-not-applicable"]
    ac.validate_na_rule_decisions()
    assert ac.CRITERION_REGISTRY["Narr.lint"]["revision"] == 7 and "lint_none" in ac.CRITERION_REGISTRY["Narr.lint"]["applicability"]


def test_the_rollup_releases_a_record_carrying_the_scan_agreement(tmp_path):
    rec = ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x\n")], ["citation_human"], LN)
    c = _cell(rec)
    assert c["v"] == NA and c["rule_id"] == "Narr.lint#measured:lint-not-applicable" and "N-150 R2" in c["decision"], c
    assert ac._na_released("Narr.lint", rec)


@pytest.mark.parametrize("mut", ["drop_block", "scope_zero", "applied_nonempty_block", "applied_nonempty_record", "block_not_dict", "no_why", "beyond_nonempty", "beyond_missing"])
def test_the_rollup_never_releases_the_declaration_alone(tmp_path, mut):
    rec = json.loads(json.dumps(ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x\n")], ["citation_human"], LN)))
    if mut == "drop_block":
        del rec["lint_none"]
    elif mut == "scope_zero":
        rec["lint_none"]["scope_files"] = 0
    elif mut == "applied_nonempty_block":
        rec["lint_none"]["applied"] = ["raw-token"]
    elif mut == "applied_nonempty_record":
        rec["applied"] = ["fact-category-pin"]
    elif mut == "block_not_dict":
        rec["lint_none"] = True
    elif mut == "beyond_nonempty":
        rec["lint_none"]["beyond"] = ["x.py -> y.py"]
    elif mut == "beyond_missing":
        del rec["lint_none"]["beyond"]
    else:
        del rec["lint_none"]["why"]
    c = _cell(rec)
    assert c["v"] == NO_DET and "scan" in c["reason"], c
    assert not ac._na_released("Narr.lint", rec)


# ───────────────────────── the declaration ─────────────────────────

def _e(**over):
    d = dict(LN)
    d.update(over)
    return {"lint_none": d}


def test_a_sound_declaration_and_the_validator_hook():
    assert ac.lint_none_problem(_e()) is None and ac.lint_none_problem({}) is None
    assert "lint_none" in ac._DECL_ENTRY_KEYS


@pytest.mark.parametrize("over", [dict(why="short"), dict(why="a reason with three plain words only"), dict(evidence="unverified:i looked somewhere"),
                                  dict(evidence="platform/nope.py:1"), dict(evidence="platform/scripts/governance/asset_census.py"),
                                  dict(evidence="platform/scripts/governance/asset_census.py:99999999"), dict(extra=1)])
def test_an_unsound_declaration_is_refused(over):
    assert ac.lint_none_problem(_e(**over))
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_x": dict(kind="data", **_e(**over))}))


def test_a_bare_value_is_refused():
    for v in (True, "yes", [LN]):
        assert ac.lint_none_problem({"lint_none": v})


# ───────────────────────── the nine real cells (pure scan over the real writer scope) ─────────────────────────

@pytest.fixture(scope="module")
def real():
    decl, reg = ac.load_asset_declarations(), ac.registered_ids("")
    out = {}
    for L, ids in [*NINE.items(), ("L2", E57_L2_LINT_NONE), *E57_LINT_NONE.items()]:
        for a in ids:
            units, _ = ac._delegation_scope(a, reg[a])
            paths = [u["path"] for u in units]
            cols = [ac.parse_prose_field(e)[0] for e in (decl[a].get("prose_fields") or [])]
            out[a] = (L, paths, cols)
    return out


def test_the_committed_census_has_exactly_these_nine_lint_not_applicable_cells():
    got = []
    for L, ts in CENSUS.items():
        d = json.loads((REPO / "00_ARCHITECTURE/control/census" / f"asset_census_2026-10-04T{ts}+0530.json").read_text(encoding="utf-8"))[L]
        got += [a["asset_id"] for a in d["assets"] if "not applicable" in a["measurements"].get("Narr.lint", {}).get("measured", "")]
    assert sorted(got) == sorted(x for ids in NINE.values() for x in ids)


@pytest.mark.parametrize("aid", [a for ids in NINE.values() for a in ids])
def test_each_real_cell_reads_no_detector_undeclared_and_na_declared(real, aid):
    L, paths, cols = real[aid]
    assert paths
    und = ac.narr_lint_scan(paths, cols)
    assert und["v"] == NO_DET and und["applied"] == [] and "not applicable" in und["measured"], und
    dec = ac.narr_lint_scan(paths, cols, LN)
    assert dec["v"] == NA and dec["cause"] == "lint-not-applicable" and dec["lint_none"]["scope_files"] == len(paths), dec
    layer = L
    c = ac._check_contribution("Narr.lint", layer, dec, None)
    assert c["v"] == NA and c["decision"].startswith("N-150 R2")


# ───────────────────────── the committed declarations ─────────────────────────

def test_exactly_the_nine_cells_declare_lint_none_and_the_scan_agrees_for_each(real):
    decl = ac.load_asset_declarations()
    assert sorted(a for a, e in decl.items() if e.get("lint_none") is not None) == sorted(real)
    for aid, (L, paths, cols) in real.items():
        ln = decl[aid]["lint_none"]
        assert ac.lint_none_problem(decl[aid]) is None, aid
        rec = ac.narr_lint_scan(paths, cols, ln)
        assert rec["v"] == NA and rec["cause"] == "lint-not-applicable" and rec["applied"] == [], (aid, rec)
        assert ac._check_contribution("Narr.lint", L, rec, None)["v"] == NA


# ───────────────────────── review fix LOW-1: a cut delegation chain is not agreement ─────────────────────────

def test_a_cut_delegation_chain_reads_no_detector_never_na(tmp_path):
    r = ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x\n")], ["citation_human"], LN, beyond=["w.py -> verification_vocab.py (write SQL beyond the hop limit)"])
    assert r["v"] == NO_DET and "hop limit" in r["measured"] and "cause" not in r, r


def test_an_empty_beyond_is_the_agreement(tmp_path):
    assert ac.narr_lint_scan([_w(tmp_path, "def f(x):\n    return x\n")], ["citation_human"], LN, beyond=[])["v"] == NA


def test_the_criterion_text_states_the_deeper_scan_and_the_single_expression_limit():
    t = ac.CRITERION_REGISTRY["Narr.lint"]["applicability"]
    assert "PRODUCED_SET_HOPS" in t and "single-expression only" in t


def test_the_single_expression_limit_is_real(tmp_path):
    """A chart_facts / fact_category query split across statements is not seen by the surface test (disclosed): the scan reads applied == []."""
    split = _w(tmp_path, "def f(c):\n    sql = 'SELECT v FROM chart_facts'\n    sql += \" WHERE fact_category = 'x'\"\n    return c.execute(sql)\n", "split.py")
    assert ac._fact_category_surface(split.read_text()) is False


def test_the_nine_committed_declarations_still_agree_at_six_hops(real):
    decl = ac.load_asset_declarations()
    reg = ac.registered_ids("")
    for aid, (L, paths, cols) in real.items():
        units, beyond = ac._delegation_scope(aid, reg[aid], hops=ac.PRODUCED_SET_HOPS)
        rec = ac.narr_lint_scan([u["path"] for u in units], cols, decl[aid]["lint_none"], beyond)
        assert rec["v"] == NA and rec["lint_none"]["beyond"] == [], (aid, rec["measured"])
