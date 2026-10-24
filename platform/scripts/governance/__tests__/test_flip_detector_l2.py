"""test_flip_detector_l2.py -- offline tests for the L2 (Bodha) extension of platform/scripts/governance/flip_detector.py (opt-in behind --l2).

The extension is ADD-ONLY: without --l2 every output (snapshot JSON, compare report JSON, summary text, exit codes, hook-validation messages, the SQL sent
to the reader) must be byte-identical to the pre-L2 tool. That is proven here by a differential test against a vendored copy of the pre-L2 file
(fixtures/flip_detector/l2/flip_detector_baseline_v2_3.py.txt, sha256 pinned = origin/main cabb8186...), on the golden fixtures, on the 23 real hooks and on
randomized states. The L2 behaviour itself is proven per registry table on synthetic before/after states, plus an end-to-end run through a fake FLIP_READER.

No database, no network, no credentials. test_flip_detector_l2_mutations.py proves these tests go red when the new code is mutated.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
import os
import pathlib
import random
import re
import stat
import sys
import tempfile
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV_DIR = HERE.parent
FIX = HERE / "fixtures" / "flip_detector"
L2FIX = FIX / "l2"
REAL_HOOKS = FIX / "hooks_real"
BASELINE = L2FIX / "flip_detector_baseline_v2_3.py.txt"
BASELINE_SHA = "cabb8186868a5757707110b18b37baec321d137364a4a8db18be8129e58e624e"
GOLDEN_L2 = L2FIX / "golden_flip_detector_l2_expected.json"

_TOOL = pathlib.Path(os.environ.get("FLIP_DETECTOR_TOOL_UNDER_TEST") or (GOV_DIR / "flip_detector.py"))
_spec = importlib.util.spec_from_file_location("flip_detector_l2_under_test", _TOOL)
F = importlib.util.module_from_spec(_spec)
sys.modules["flip_detector_l2_under_test"] = F
_spec.loader.exec_module(F)

OLD = types.ModuleType("flip_detector_baseline_v2_3")
OLD.__file__ = str(GOV_DIR / "flip_detector.py")
exec(compile(BASELINE.read_text(), str(BASELINE), "exec"), OLD.__dict__)

NATIVE = F.NATIVE
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

L2_29 = ["bodha_anomalies", "bodha_cdlm_cells", "bodha_cdlm_chart_summary", "bodha_cdlm_domain_rollups", "bodha_cdlm_pattern_clusters", "bodha_cgm_chart_topology_summary",
         "bodha_cgm_edges", "bodha_cgm_motifs", "bodha_cgm_nodes", "bodha_cgm_paths", "bodha_cgm_sub_graphs", "bodha_chart_gestalt", "bodha_contradictions", "bodha_convergence",
         "bodha_discoveries", "bodha_grounding_matches", "bodha_mechanisms", "bodha_msr_signals", "bodha_pratijna", "bodha_question_lenses", "bodha_rm_chart_summary",
         "bodha_rm_dasha_windowed_prescriptions", "bodha_rm_dosha_remedy_bundles", "bodha_rm_pattern_remedies", "bodha_rm_remedy_prescriptions", "bodha_rm_resonances",
         "bodha_signal_embeddings", "bodha_triangulation", "synthesis_quality_scorecard"]
MUST_HAVE = {"bodha_msr_signals", "bodha_signal_embeddings", "bodha_cgm_nodes", "bodha_cgm_edges", "bodha_cgm_paths", "bodha_cdlm_cells", "bodha_rm_resonances",
             "bodha_mechanisms", "synthesis_quality_scorecard", "bodha_rm_remedy_prescriptions"}
NOT_MUST = [t for t in L2_29 if t not in MUST_HAVE]


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    def tripwire(sql, retries=4):
        raise AssertionError("flip_detector L2 test reached the database layer: " + sql[:80])
    monkeypatch.setattr(F, "q", tripwire)
    monkeypatch.setattr(OLD, "q", tripwire)


# ----------------------------------------------------------------------------------------------- fixtures
def l1_state():
    """A small L1 state on a non-native chart (no anchors). chart_dashas / panchanga_daily are not read in these runs."""
    return {"chart_facts": [["lahiri_chitrapaksha", "graha_position", "SUN", "sign", "Capricorn", "", "single"]],
            "divisionals": [["lahiri_chitrapaksha", "D9", "Sun", "varga_position", "sign", "Leo", "", "Leo"]]}


def uid(n):
    return f"{n:08x}-0000-4000-8000-{n:012x}"


def rows_for(t, n=3, dup=2):
    """n distinct semantic keys + one key shared by `dup` rows (an occurrence list). Row = [aya, category, subject, key, text, num, tier]."""
    cat = cat_of(t)
    rows = [["lahiri_chitrapaksha", cat, f"subj{i}", f"key{i}", f"id={uid(i)}|v=a|cites=abc{i}", "0.5,1.5", "two_pass_verified"] for i in range(n)]
    rows += [["lahiri_chitrapaksha", cat, "dupsubj", "dupkey", f"id={uid(100 + j)}|v=a", "0.25", "single"] for j in range(dup)]
    return rows


def st_with(l2):
    s = l1_state()
    s["l2"] = copy.deepcopy(l2)
    return s


def mut(state, fn):
    s = copy.deepcopy(state)
    fn(s)
    return s


def hook(lane, entries, **kw):
    h = {"lane": lane, "ruling": lane, "pr": "#1", "description": "test hook", "may_change": entries}
    h.update(kw)
    return h


def l2entry(t, change_types=None, **kw):
    e = {"table": t, "categories": [cat_of(t)]}
    if change_types is not None:
        e["change_types"] = list(change_types)
    e.update(kw)
    return e


def loaded(tmp_path, *hooks_):
    d = pathlib.Path(tempfile.mkdtemp(dir=tmp_path))  # a fresh folder per call: hook sets never leak into each other
    for h in hooks_:
        (d / f"{h['lane']}.json").write_text(json.dumps(h))
    hs, errs = F.load_hooks(str(d))
    assert not errs, errs
    return hs


def run2(snap, cur, hooks_=(), tables=None, requested=True, **kw):
    """compare_states for the L2 tests: non-native chart, no dashas / daily, no standing registry noise unless asked."""
    tables = tuple(tables if tables is not None else (snap.get("l2") or {}))
    kw.setdefault("standing_not_checked", ())
    return F.compare_states(snap, cur, list(hooks_), OTHER, have_dash=False, have_daily=False, l2_tables=tables, l2_requested=requested, **kw)


def cat_of(t):
    return "cat_" + t[-6:]


def kinds(rep, table=None):
    return sorted(c["change"] for c in rep["changes"] if table is None or c["table"] == table)


def counts(rep):
    return {k: v for k, v in rep["failure_counts"].items() if v}


# ----------------------------------------------------------------------------------------------- the registry
def test_registry_is_the_29_l2_tables_of_the_data_plane_manifest():
    assert sorted(F.L2_TABLES) == L2_29 and len(F.L2_TABLES) == 29


def test_registry_must_have_rows_flags_are_the_documented_ten():
    assert {t for t, s in F.L2_TABLES.items() if s["must_have_rows"]} == MUST_HAVE


def test_hook_tables_are_additive():
    assert F.HOOK_TABLES[:5] == F.LEGACY_HOOK_TABLES == ("chart_facts", "chart_divisionals", "chart_dashas", "panchanga_daily", "l1_tajik_varsha_year_lords")
    assert set(F.HOOK_TABLES) == set(F.LEGACY_HOOK_TABLES) | set(L2_29)
    assert F.TABLES == OLD.TABLES and F.UNCOMPARED_TABLES == OLD.UNCOMPARED_TABLES and F.TOOL_VERSION == OLD.TOOL_VERSION == "2.3"


def split_select_list(sql):
    """Top-level comma split of the select list of one SELECT (quote and parenthesis aware)."""
    assert sql.count(" from ") == 1
    body = sql[len("select "):sql.index(" from ")]
    out, depth, q, cur = [], 0, False, ""
    for ch in body:
        if ch == "'":
            q = not q
        if not q:
            depth += ch == "("
            depth -= ch == ")"
            if ch == "," and depth == 0:
                out.append(cur.strip())
                cur = ""
                continue
        cur += ch
    out.append(cur.strip())
    return out


@pytest.mark.parametrize("t", L2_29)
def test_every_table_spec_is_one_read_only_select_of_seven_columns_filtered_by_chart(t):
    sql = F.l2_select_sql(t, NATIVE)
    F._select_only(sql)  # the detector's own single-SELECT guard
    items = split_select_list(sql)
    s = F.L2_TABLES[t]
    assert len(items) == 7, items
    assert f"t.chart_id='{NATIVE}'" in sql and sql.lstrip().lower().startswith("select ")
    assert ";" not in sql
    # the 7 columns are, in order, ayanamsha / category / subject / key / text / num / tier
    assert s["category"] in items[1] and s["subject"] in items[2] and s["key"] in items[3]
    assert "'id='" in items[4] and s["ident"] in items[4]
    for c in s["score"]:
        assert c in items[5]
    assert s["tier"] in items[6] and s["aya"] in items[0]


@pytest.mark.parametrize("t", L2_29)
def test_generated_identity_is_never_in_the_semantic_key(t):
    s = F.L2_TABLES[t]
    ident = s["ident"]
    assert ident.startswith("t.") and ident not in s["category"] + s["subject"] + s["key"] + s["aya"]
    items = split_select_list(F.l2_select_sql(t, NATIVE))
    assert ident not in items[1] + items[2] + items[3] and ident in items[4]


def test_spec_sql_refuses_a_bad_chart_id_and_the_phantom():
    for bad in ("not-a-uuid", "362f9f17-0000-0000-0000-000000000000", "x'; drop table t; --"):
        with pytest.raises(ValueError):
            F.l2_select_sql("bodha_msr_signals", bad)


def test_the_msr_key_names_the_documented_columns():
    sql = F.l2_select_sql("bodha_msr_signals", NATIVE)
    for needle in ("t.signal_type_class", "t.signal_type_id", "t.varga_id", "fact_subject", "fact_key", "t.ayanamsha_id", "t.signal_id"):
        assert needle in sql


# ----------------------------------------------------------------------------------------------- per-table before / after
@pytest.mark.parametrize("t", L2_29)
def test_appeared_disappeared_value_occurrence_and_tier_are_detected_per_table(t, tmp_path):
    R = rows_for(t)
    before = st_with({t: R})
    h = loaded(tmp_path, hook("lane_a", [l2entry(t)]))

    def appeared(s):
        s["l2"][t].append(["lahiri_chitrapaksha", cat_of(t), "newsubj", "newkey", f"id={uid(900)}|v=a", "1", "single"])

    def disappeared(s):
        s["l2"][t].pop(0)

    def moved_identity(s):
        s["l2"][t][1][4] = f"id={uid(777)}|v=a|cites=abc1"

    def content_changed(s):
        s["l2"][t][1][4] = f"id={uid(1)}|v=a|cites=CHANGED"

    def occurrence(s):
        s["l2"][t].pop()  # one of the two rows that share the key

    def tier(s):
        s["l2"][t][0][6] = "classical_match"

    for fn, want in ((appeared, ["appeared"]), (disappeared, ["disappeared"]), (moved_identity, ["value"]), (content_changed, ["value"]),
                     (occurrence, ["occurrence_count"]), (tier, ["tier"])):
        rep = run2(before, mut(before, fn), h)
        assert kinds(rep, t) == want, (fn.__name__, rep["changes"])
        assert rep["changes_total"] == 1 and counts(rep) == {}, (fn.__name__, counts(rep))
        assert rep["changes"][0]["lanes"] == ["lane_a"]


@pytest.mark.parametrize("t", L2_29)
def test_a_moved_identity_is_one_value_change_not_an_appeared_plus_disappeared_pair(t):
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(4, f"id={uid(555)}|v=a|cites=abc0"))
    rep = run2(before, after)
    c = rep["changes"]
    assert [x["change"] for x in c] == ["value"] and c[0]["before"][0].startswith(f"id={uid(0)}") and c[0]["after"][0].startswith(f"id={uid(555)}")
    assert c[0]["category"] == cat_of(t) and c[0]["fact_key"] == "key0"


def test_occurrence_count_reports_the_totals_not_what_was_left_after_the_identical_rows_cancel():
    t = "bodha_msr_signals"
    before = st_with({t: rows_for(t, dup=4)})
    after = mut(before, lambda s: s["l2"][t].pop())
    rep = run2(before, after)
    oc = [c for c in rep["changes"] if c["change"] == "occurrence_count"]
    assert len(oc) == 1 and (oc[0]["before"], oc[0]["after"]) == (4, 3) and rep["changes_total"] == 1


def test_one_moved_identity_in_a_large_duplicate_group_is_one_change_not_a_cascade():
    t = "bodha_discoveries"
    cat = cat_of(t)
    grp = [["lahiri_chitrapaksha", cat, "s", "k", f"id={uid(i)}|v=a", "0.1", ""] for i in range(1, 40)]
    before = st_with({t: grp})
    after = mut(before, lambda s: s["l2"][t].__setitem__(5, ["lahiri_chitrapaksha", cat, "s", "k", f"id={uid(5000)}|v=a", "0.1", ""]))
    rep = run2(before, after)
    assert kinds(rep) == ["value"], rep["changes"]  # positional pairing alone would have produced many


def test_row_order_from_the_database_does_not_matter():
    t = "bodha_cgm_edges"
    r = rows_for(t, n=6)
    a = st_with({t: r})
    b = st_with({t: list(reversed(r))})
    assert run2(a, b)["changes_total"] == 0


# ----------------------------------------------------------------------------------------------- continuous scores
@pytest.mark.parametrize("t", L2_29)
def test_a_continuous_score_change_is_not_a_class_change(t):
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(5, "0.9000001,1.5"))
    rep = run2(before, after, hooks_=[], standing_not_checked=())
    assert rep["changes_total"] == 0 and counts(rep) == {}
    st = rep["continuous_l2"][t]
    assert st["changed"] == 1 and st["to_null"] == 0 and st["max_abs_delta"] > 0.39
    assert {"l2.unread_columns", "l2.generation_ledger"} <= {x["id"] for x in rep["not_checked"]} and rep["verdict"] == "NOT_CHECKED"  # never a pass


def test_a_score_beyond_float_noise_and_an_integral_score_are_continuous_too():
    t = "bodha_cgm_nodes"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(5, "1,1.5"))  # 0.5 -> 1: the L1 rule would call an integral value a class value
    rep = run2(before, after)
    assert rep["changes_total"] == 0 and rep["continuous_l2"][t]["changed"] == 1


def test_a_score_within_float_noise_is_not_even_counted_as_changed():
    t = "bodha_cgm_nodes"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(5, "0.50000000000001,1.5"))
    assert run2(before, after)["continuous_l2"][t]["changed"] == 0


def test_a_score_that_becomes_null_is_a_value_change_like_the_l1_continuous_values():
    t = "bodha_msr_signals"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(5, ",1.5"))
    rep = run2(before, after)
    assert kinds(rep) == ["value"] and rep["changes"][0]["note"] == "score_lost" and rep["continuous_l2"][t]["to_null"] == 1


def test_a_score_that_appears_where_it_was_null_is_not_a_change():
    t = "bodha_msr_signals"
    before = st_with({t: mut(st_with({t: rows_for(t)}), lambda s: s["l2"][t][0].__setitem__(5, ",1.5"))["l2"][t]})
    after = st_with({t: rows_for(t)})
    rep = run2(before, after)
    assert rep["changes_total"] == 0 and rep["continuous_l2"][t]["changed"] == 1


# ----------------------------------------------------------------------------------------------- attribution
def test_an_undeclared_l2_change_is_undeclared_change(tmp_path):
    t = "bodha_cgm_nodes"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(4, f"id={uid(9)}|v=a"))
    rep = run2(before, after, [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and rep["verdict"] == "FAIL"
    assert rep["failures"]["UNDECLARED_CHANGE"][0]["table"] == t and F.exit_code(rep) == 2


def test_a_hook_on_another_table_or_category_does_not_declare_the_change(tmp_path):
    t = "bodha_cgm_nodes"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(4, f"id={uid(9)}|v=a"))
    wrong_table = hook("w1", [l2entry("bodha_cgm_edges")])
    wrong_cat = hook("w2", [{"table": t, "categories": ["some_other_category"]}])
    rep = run2(before, after, loaded(tmp_path, wrong_cat), tables=(t,))
    assert counts(rep) == {"UNDECLARED_CHANGE": 1, "DECLARED_BUT_ABSENT": 1}
    rep = run2(before, after, loaded(tmp_path, wrong_table, wrong_cat), tables=(t,))
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 1


def test_kind_mismatch_on_an_l2_table(tmp_path):
    t = "bodha_cgm_edges"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][0].__setitem__(4, f"id={uid(9)}|v=a"))
    rep = run2(before, after, loaded(tmp_path, hook("tieronly", [l2entry(t, ["tier"])])))
    assert counts(rep) == {"KIND_MISMATCH": 1, "DECLARED_BUT_ABSENT": 1}


def test_expected_count_exact_is_judged_for_an_l2_entry_and_off_by_one_is_expectation_mismatch(tmp_path):
    t = "bodha_cgm_edges"
    before = st_with({t: rows_for(t)})

    def two_moves(s):
        s["l2"][t][0][4] = f"id={uid(8)}|v=a"
        s["l2"][t][1][4] = f"id={uid(9)}|v=a"
    after = mut(before, two_moves)
    ok = run2(before, after, loaded(tmp_path, hook("exact2", [l2entry(t, ["value"], expected_count={"exact": 2})])))
    assert counts(ok) == {} and ok["expectations"] == [{"lane": "exact2", "entry": 0, "expected": {"exact": 2}, "observed": 2, "ok": True}]
    for bad in ({"exact": 1}, {"exact": 3}, {"min": 3, "max": 5}, {"max": 1}):
        rep = run2(before, after, loaded(tmp_path, hook("exact2", [l2entry(t, ["value"], expected_count=bad)])))
        assert counts(rep) == {"EXPECTATION_MISMATCH": 1}, bad
        assert rep["verdict"] == "FAIL"


def test_declared_but_absent_and_optional_on_an_l2_entry(tmp_path):
    t = "bodha_rm_resonances"
    same = st_with({t: rows_for(t)})
    assert counts(run2(same, same, loaded(tmp_path, hook("ghost", [l2entry(t)])))) == {"DECLARED_BUT_ABSENT": 1}
    rep = run2(same, same, loaded(tmp_path, hook("ghost", [l2entry(t, optional=True)])))
    assert counts(rep) == {} and any("OPTIONAL_ABSENT" in w for w in rep["warnings"])


def test_fact_key_and_ayanamsha_narrowing_apply_to_l2_entries(tmp_path):
    t = "bodha_msr_signals"
    before = st_with({t: rows_for(t)})
    after = mut(before, lambda s: s["l2"][t][1].__setitem__(4, f"id={uid(9)}|v=a"))  # key1
    narrow_ok = hook("n1", [l2entry(t, fact_keys=["key1"], ayanamsha_ids=["lahiri_chitrapaksha"])])
    narrow_no = hook("n2", [l2entry(t, fact_keys=["key2"], optional=True)])
    assert counts(run2(before, after, loaded(tmp_path, narrow_ok))) == {}
    assert counts(run2(before, after, loaded(tmp_path, narrow_no))) == {"UNDECLARED_CHANGE": 1}


def test_a_hook_may_name_an_l2_table_and_validates():
    h = hook("x", [{"table": "bodha_msr_signals", "categories": ["yoga"], "change_types": ["value", "tier", "occurrence_count"]}])
    assert F.validate_hook(h, "x.json") == []
    h["may_change"][0]["table"] = "bodha_not_a_table"
    errs = F.validate_hook(h, "x.json")
    assert errs and OLD.validate_hook(h, "x.json") == errs  # the message is byte-identical to the pre-L2 tool


# ----------------------------------------------------------------------------------------------- NOT CHECKED paths
def test_hook_entry_on_an_l2_table_in_a_run_without_l2_is_not_checked_never_absent_never_passing(tmp_path):
    t = "bodha_msr_signals"
    h = loaded(tmp_path, hook("l2lane", [l2entry(t), l2entry("bodha_cgm_edges", optional=True)]))
    rep = F.compare_states(l1_state(), l1_state(), h, OTHER, have_dash=False, have_daily=False, standing_not_checked=())
    assert rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 0 and rep["warnings"] == []
    rows = {x["id"]: x for x in rep["not_checked"]}
    assert rows["l2lane[0]"]["table"] == t and "not compared" in rows["l2lane[0]"]["reason"] and "--l2" in rows["l2lane[0]"]["reason"]
    assert "l2lane[1]" in rows and rep["verdict"] == "NOT_CHECKED" and F.exit_code(rep) == 4
    assert "l2.not_compared" not in rows and "l2" not in rep["compared"]


def test_with_l2_compared_the_same_entry_is_judged_like_any_other(tmp_path):
    t = "bodha_msr_signals"
    h = loaded(tmp_path, hook("l2lane", [l2entry(t)]))
    same = st_with({t: rows_for(t)})
    rep = run2(same, same, h)
    assert rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 1 and not any(x["id"] == "l2lane[0]" for x in rep["not_checked"])


def test_an_entry_on_an_l2_table_outside_the_compared_subset_is_not_checked(tmp_path):
    h = loaded(tmp_path, hook("l2lane", [l2entry("bodha_cgm_edges")]))
    same = st_with({"bodha_msr_signals": rows_for("bodha_msr_signals")})
    rep = run2(same, same, h, tables=("bodha_msr_signals",))
    assert rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 0 and any(x["id"] == "l2lane[0]" for x in rep["not_checked"])


def test_l2_not_compared_row_only_when_l2_was_requested_and_a_section_is_missing(tmp_path):
    h = loaded(tmp_path, hook("l2lane", [l2entry("bodha_cgm_edges", optional=True)]))
    plain = F.compare_states(l1_state(), l1_state(), h, OTHER, have_dash=False, have_daily=False, standing_not_checked=())
    assert not any(x["id"] == "l2.not_compared" for x in plain["not_checked"])
    req = F.compare_states(l1_state(), l1_state(), h, OTHER, have_dash=False, have_daily=False, standing_not_checked=(), l2_requested=True,
                           not_compared={"l2": "L2 tables not compared in this run: x missing from the snapshot's l2 section"})
    row = next(x for x in req["not_checked"] if x["id"] == "l2.not_compared")
    assert row["status"] == "NOT CHECKED" and "snapshot's l2 section" in row["reason"] and row["declared_by_lanes"] == ["l2lane"]
    assert req["verdict"] == "NOT_CHECKED"
    ok = run2(st_with({"bodha_msr_signals": rows_for("bodha_msr_signals")}), st_with({"bodha_msr_signals": rows_for("bodha_msr_signals")}))
    assert not any(x["id"] == "l2.not_compared" for x in ok["not_checked"])


def test_standing_l2_notes_only_when_l2_is_compared_and_the_stale_l1_era_rows_are_dropped_then():
    t = "bodha_msr_signals"
    s = st_with({t: rows_for(t)})
    on = F.compare_states(s, s, [], OTHER, have_dash=False, have_daily=False, l2_tables=(t,), l2_requested=True)
    ids_on = {x["id"] for x in on["not_checked"]}
    assert {"l2.unread_columns", "l2.generation_ledger"} <= ids_on and "bodha_msr_signals" not in ids_on and "bodha_rm_resonances" in ids_on
    off = F.compare_states(l1_state(), l1_state(), [], OTHER, have_dash=False, have_daily=False)
    ids_off = {x["id"] for x in off["not_checked"]}
    assert not {"l2.unread_columns", "l2.generation_ledger"} & ids_off and {"bodha_msr_signals", "bodha_rm_resonances"} <= ids_off
    assert on["l2_unread"][t] and on["l2_extension_version"] == F.L2_EXTENSION_VERSION


# ----------------------------------------------------------------------------------------------- EMPTY_READ
@pytest.mark.parametrize("t", sorted(MUST_HAVE))
def test_empty_read_applies_to_must_have_rows_tables(t):
    full = st_with({t: rows_for(t)})
    empty = st_with({t: []})
    for a, b in ((full, empty), (empty, full), (empty, empty)):
        rep = run2(a, b)
        assert rep["failure_counts"]["EMPTY_READ"] >= 1 and rep["verdict"] == "FAIL", t


@pytest.mark.parametrize("t", NOT_MUST)
def test_empty_read_does_not_apply_to_a_table_that_is_legitimately_empty(t):
    full = st_with({t: rows_for(t)})
    empty = st_with({t: []})
    for a, b in ((empty, empty), (full, empty), (empty, full)):
        rep = run2(a, b)
        assert rep["failure_counts"]["EMPTY_READ"] == 0, t
    assert kinds(run2(empty, full)) == ["appeared"] * 4 and kinds(run2(full, empty)) == ["disappeared"] * 4


def test_empty_l2_helper_ignores_tables_outside_the_registry_and_the_compared_subset():
    st = {"l2": {"bodha_msr_signals": [], "bodha_cgm_edges": [], "not_a_table": []}}
    assert F.empty_l2_tables(st) == ["bodha_msr_signals", "bodha_cgm_edges"]
    assert F.empty_l2_tables(st, ("bodha_cgm_edges",)) == ["bodha_cgm_edges"]
    assert F.empty_l2_tables({"chart_facts": []}) == []


# ----------------------------------------------------------------------------------------------- no L2 in the report unless asked
def test_the_report_carries_no_l2_key_unless_l2_was_requested_or_compared():
    rep = F.compare_states(l1_state(), l1_state(), [], OTHER, have_dash=False, have_daily=False)
    assert set(rep) == set(OLD.compare_states(l1_state(), l1_state(), [], OTHER, have_dash=False, have_daily=False)) and "l2_extension_version" not in rep
    assert rep["compared"] == {"chart_facts": True, "chart_divisionals": True, "chart_dashas": False, "panchanga_daily": False}


def test_an_l2_section_in_the_snapshot_is_ignored_when_l2_is_not_requested():
    t = "bodha_msr_signals"
    a, b = st_with({t: rows_for(t)}), st_with({t: rows_for(t, n=1)})
    plain = F.compare_states(a, b, [], OTHER, have_dash=False, have_daily=False)
    assert plain["changes_total"] == 0 and "l2" not in plain["compared"]
    assert json.dumps(plain, sort_keys=True) == json.dumps(OLD.compare_states(a, b, [], OTHER, have_dash=False, have_daily=False), sort_keys=True)


def test_l2_changes_follow_the_l1_changes_in_the_report_so_the_l1_order_is_unchanged():
    t = "bodha_msr_signals"
    s = st_with({t: rows_for(t)})
    s2 = mut(s, lambda x: (x["l2"][t][0].__setitem__(4, f"id={uid(9)}|v=a"), x["chart_facts"][0].__setitem__(4, "Aries")))
    rep = run2(s, s2)
    assert [c["table"] for c in rep["changes"]] == ["chart_facts", t]


def test_summary_text_prints_the_l2_lines_only_in_an_l2_run():
    t = "bodha_cgm_nodes"
    s = st_with({t: rows_for(t)})
    s2 = mut(s, lambda x: x["l2"][t][0].__setitem__(5, "0.9,1.5"))
    on = "\n".join(F.render_summary(run2(s, s2)))
    assert "l2 (Bodha) tables compared: 1 of 29" in on and f"continuous (l2 {t}): compared 8 changed 1" in on
    off = "\n".join(F.render_summary(F.compare_states(l1_state(), l1_state(), [], OTHER, have_dash=False, have_daily=False)))
    assert "l2" not in off.replace("_l2", "")


# ----------------------------------------------------------------------------------------------- ADD-ONLY: differential against the pre-L2 file
def test_the_vendored_baseline_is_the_pre_l2_main_file():
    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == BASELINE_SHA


def _sibling():
    """The existing golden fixtures (test_flip_detector.py helpers), loaded without running its tests."""
    sp = importlib.util.spec_from_file_location("flip_detector_sibling_for_l2", HERE / "test_flip_detector.py")
    m = importlib.util.module_from_spec(sp)
    old_env = os.environ.get("FLIP_DETECTOR_TOOL_UNDER_TEST")
    os.environ["FLIP_DETECTOR_TOOL_UNDER_TEST"] = str(_TOOL)
    try:
        sp.loader.exec_module(m)
    finally:
        if old_env is None:
            os.environ.pop("FLIP_DETECTOR_TOOL_UNDER_TEST", None)
        else:
            os.environ["FLIP_DETECTOR_TOOL_UNDER_TEST"] = old_env
    return m


def same_report(old, new):
    assert json.dumps(old, sort_keys=True) == json.dumps(new, sort_keys=True)
    assert OLD.exit_code(old) == F.exit_code(new) and OLD.exit_code(old, True) == F.exit_code(new, True)
    assert OLD.render_summary(old) == F.render_summary(new) and OLD.render_summary(old, True) == F.render_summary(new, True)


def test_differential_golden_fixtures_and_all_23_real_hooks_are_identical_without_l2(tmp_path):
    sib = _sibling()
    old_hooks, e1 = OLD.load_hooks(str(REAL_HOOKS))
    new_hooks, e2 = F.load_hooks(str(REAL_HOOKS))
    assert e1 == e2 == [] and old_hooks == new_hooks and len(new_hooks) == 23
    cases = {"unchanged": (sib.base_state(), sib.base_state()), "golden": (sib.golden_before(), sib.golden_after())}

    def noisy(s):
        sib.change_mar_pada(s)
        sib.shift_vimshottari(s)
    cases["noisy"] = (sib.golden_before(), sib.mutate(sib.golden_after(), noisy))
    for name, (a, b) in cases.items():
        for chart in (NATIVE, OTHER):
            for dash, daily in ((True, True), (False, True), (True, False), (False, False)):
                kw = dict(have_dash=dash, have_daily=daily)
                old = OLD.compare_states(copy.deepcopy(a), copy.deepcopy(b), old_hooks, chart, **kw)
                new = F.compare_states(copy.deepcopy(a), copy.deepcopy(b), new_hooks, chart, **kw)
                same_report(old, new)
                assert "l2" not in new["compared"]


def test_differential_the_golden_file_still_pins_the_pre_l2_reports(tmp_path):
    """The existing golden file is untouched; the pre-L2 tool and this tool produce the same summaries for its cases."""
    sib = _sibling()
    want = json.loads((FIX / "golden_flip_detector_expected.json").read_text())
    got = sib.golden_cases(tmp_path)
    assert got == want


def _random_state(rng):
    cats = ["graha_position", "argala_natal_matrix", "graha_shadbala_total", "special_lagna", "kp_cuspal_significators", "graha_gandanta", "karaka_roles", "sade_sati"]
    keys = ["sign", "pada", "net", "total", "is_gandanta", "house_d1", "ratio"]
    facts = []
    for ay in F.AYANS[:3] + ("INVARIANT",):
        for _ in range(rng.randint(4, 14)):
            cat, key = rng.choice(cats), rng.choice(keys)
            kind = rng.choice(("txt", "int", "cont", "none"))
            t, n = ("", "")
            if kind == "txt":
                t = rng.choice(["Aries", "Taurus", "false", "true", "2026-01-01T00:00:00+00:00"])
            elif kind == "int":
                n = str(rng.randint(1, 12))
            elif kind == "cont":
                n = f"{rng.uniform(0, 500):.6f}"
            facts.append([ay, cat, f"S{rng.randint(0, 4)}", key, t, n, rng.choice(["single", "two_pass_verified", "classical_match"])])
    divs = [["lahiri_chitrapaksha", f"D{rng.randint(2, 12)}", rng.choice(["Sun", "Moon"]), "varga_position", "sign", rng.choice(["Leo", "Aries"]), "", "Leo"] for _ in range(rng.randint(1, 5))]
    dashas = [["lahiri_chitrapaksha", rng.choice(["vimshottari", "yogini"]), 1, f"/L{i}", f"19{70 + i}-01-01T00:00:00+00:00", f"19{71 + i}-01-01T00:00:00+00:00"] for i in range(rng.randint(1, 4))]
    daily = [[f"2026-07-{d:02d}", "5", "shukla", "5", "9", "Ashlesha", "3", "6", "7", "Panchami", "Guruvara", "Priti", "Taitila"] for d in range(1, rng.randint(2, 5))]
    return {"chart_facts": facts, "divisionals": divs, "dashas": dashas, "daily": daily}


def _random_mutation(rng, s):
    s = copy.deepcopy(s)
    for _ in range(rng.randint(0, 4)):
        op = rng.choice(("val", "tier", "drop", "add", "dup", "cont", "dash", "daily"))
        f = s["chart_facts"]
        if op == "val" and f:
            r = rng.choice(f)
            r[4], r[5] = ("Gemini", "") if r[4] else ("", str(rng.randint(1, 12)))
        elif op == "tier" and f:
            rng.choice(f)[6] = rng.choice(["single", "two_pass_verified", "classical_match"])
        elif op == "drop" and f:
            f.pop(rng.randrange(len(f)))
        elif op == "add":
            f.append(["lahiri_chitrapaksha", rng.choice(["graha_position", "new_cat"]), "S9", "sign", "Virgo", "", "single"])
        elif op == "dup" and f:
            f.append(list(rng.choice(f)))
        elif op == "cont" and f:
            r = rng.choice(f)
            if r[5] and "." in r[5]:
                r[5] = f"{float(r[5]) + 1.5:.6f}"
        elif op == "dash" and s["dashas"]:
            r = rng.choice(s["dashas"])
            r[4] = "1970-01-09T00:00:00+00:00"
        elif op == "daily" and s["daily"]:
            rng.choice(s["daily"])[1] = "6"
    return s


def test_differential_randomized_states_and_hook_subsets_are_identical_without_l2(tmp_path):
    rng = random.Random(20261003)
    hooks_all, _ = OLD.load_hooks(str(REAL_HOOKS))
    for i in range(300):
        a = _random_state(rng)
        b = _random_mutation(rng, a)
        hs = rng.sample(hooks_all, rng.randint(0, 8))
        chart = rng.choice([NATIVE, OTHER])
        kw = dict(have_dash=rng.random() < 0.7, have_daily=rng.random() < 0.7, hook_errors=rng.choice([(), ("HOOK ERROR x",)]))
        if rng.random() < 0.2:
            kw["standing_not_checked"] = ()
        old = OLD.compare_states(copy.deepcopy(a), copy.deepcopy(b), copy.deepcopy(hs), chart, **kw)
        new = F.compare_states(copy.deepcopy(a), copy.deepcopy(b), copy.deepcopy(hs), chart, **kw)
        same_report(old, new)


def test_differential_hook_validation_messages_are_identical(tmp_path):
    bad = [hook("x", [{"table": "chart_nope", "categories": ["a"]}]), hook("y", [{"table": "chart_facts", "categories": ["a"], "change_types": ["bogus"]}]),
           hook("z", []), hook("w", [{"table": "chart_dashas", "kind": "dasha_shift"}]), {"lane": "q"}, hook("v", [{"table": "chart_facts", "categories": ["a*"]}])]
    for h in bad:
        assert OLD.validate_hook(copy.deepcopy(h), "f.json") == F.validate_hook(copy.deepcopy(h), "f.json")
    d = tmp_path / "hk"
    d.mkdir()
    for h in bad[:3]:
        (d / f"{h['lane']}.json").write_text(json.dumps(h))
    assert OLD.load_hooks(str(d), ["x", "nolane"]) == F.load_hooks(str(d), ["x", "nolane"])


# --- CLI level: stdout, report file, snapshot content and the SQL sent to the reader
FAKE_READER = r"""#!__PY__
import sys, os, json, re
script = sys.argv[1]
d = os.environ["FAKE_DIR"]
with open(d + "/calls.log", "a") as lg:
    lg.write(json.dumps({"pgoptions": os.environ.get("PGOPTIONS", ""), "script": script}) + chr(10))
st = json.load(open(d + "/state.json"))["charts"]
for sql in [x.strip() for x in script.split(";" + chr(10)) if x.strip()]:
    flat = re.sub(r"\s+", " ", sql)
    if flat.upper().startswith("BEGIN") or flat.upper() == "COMMIT":
        continue
    m = re.match(r"^select '(@@END:[a-z_]+@@)'$", flat)
    if m:
        print(m.group(1)); continue
    if "current_setting('transaction_read_only')" in flat:
        print("on" if "default_transaction_read_only=on" in os.environ.get("PGOPTIONS", "") else "off"); continue
    if flat.startswith("select current_user"):
        print("fake_reader"); continue
    cid = (re.search(r"chart_id='([^']*)'", flat) or [None, None])[1]
    c = st.get(cid, {})
    m = re.search(r"\bfrom ([a-z_]+) t\b", flat)
    if m and m.group(1) in (c.get("l2") or {}):
        rows = c["l2"][m.group(1)]
    elif m and m.group(1) not in ("chart_facts", "chart_divisionals", "chart_dashas", "panchanga_daily"):
        rows = []
    else:
        tbl = re.search(r"from (chart_facts|chart_divisionals|chart_dashas|panchanga_daily)", flat).group(1)
        if tbl == "chart_facts": rows = c.get("chart_facts", [])
        elif tbl == "chart_divisionals": rows = c.get("divisionals", [])
        elif tbl == "chart_dashas": rows = [[r[0], r[1], r[2], r[3].split("/")[-1], "", "", "", r[4], r[5], "id%d" % i, ""] for i, r in enumerate(c.get("dashas", []))]
        else: rows = next(iter(st.values())).get("daily", [])
    for r in rows:
        print("\t".join(str(x) for x in r))
"""


def l1_full():
    """Native chart with the anchors, dashas and daily rows (the CLI path reads all four L1 tables)."""
    f = []
    for ay in F.AYANS:
        f += [[ay, "graha_position", "SUN", "sign", "Capricorn", "", "single"], [ay, "graha_position", "MOON", "nakshatra", "Purva Bhadrapada", "", "single"],
              [ay, "graha_position", "LAGNA", "sign", "Aries", "", "single"]]
    for cat, subj, val in (("panchanga_tithi", "TITHI_BIRTH", "Shukla Tritiya"), ("panchanga_vara", "VARA_BIRTH", "Ravivara"), ("panchanga_yoga", "YOGA_BIRTH", "Shiva"),
                           ("panchanga_karana", "KARANA_BIRTH", "Garaja")):
        f.append(["INVARIANT", cat, subj, "name", val, "", "single"])
    return {"chart_facts": f, "divisionals": [["lahiri_chitrapaksha", "D9", "Sun", "varga_position", "sign", "Leo", "", "Leo"]],
            "dashas": [["lahiri_chitrapaksha", "vimshottari", 1, "/Jupiter", "1975-08-18T21:50:23+00:00", "1991-08-18T21:50:23+00:00"]],
            "daily": [["2026-07-09", "5", "shukla", "5", "9", "Ashlesha", "3", "6", "7", "Panchami", "Guruvara", "Priti", "Taitila"]]}


def l2_full():
    return {t: rows_for(t) for t in L2_29}


def fake_reader(tmp_path, monkeypatch, charts, tag="r"):
    d = tmp_path / f"fakereader_{tag}"
    d.mkdir(exist_ok=True)
    stub = d / "reader.py"
    stub.write_text(FAKE_READER.replace("__PY__", sys.executable))
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    (d / "state.json").write_text(json.dumps({"charts": charts}))
    monkeypatch.setattr(F.time, "sleep", lambda *_: None)
    monkeypatch.setattr(OLD.time, "sleep", lambda *_: None)
    monkeypatch.setenv("FLIP_READER", str(stub))
    monkeypatch.setenv("FAKE_DIR", str(d))
    monkeypatch.delenv("PGOPTIONS", raising=False)
    monkeypatch.delenv("FLIP_SNAPSHOT_DIR", raising=False)

    def calls():
        p = d / "calls.log"
        return [json.loads(ln) for ln in p.read_text().splitlines()] if p.exists() else []
    return calls


def write_snap(tmp_path, name, state, chart=NATIVE, meta_extra=None):
    st = copy.deepcopy(state)
    st["meta"] = {"tool": "flip_detector.py", "chart_id": chart, "taken_at_utc": "2026-10-02T00:00:00+00:00"}
    st["meta"].update(meta_extra or {})
    p = tmp_path / name
    with gzip.open(p, "wt") as f:
        json.dump(st, f)
    (tmp_path / (name + ".sha256")).write_text(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {name}\n")
    return p


def test_differential_cli_snapshot_and_compare_without_l2_are_byte_identical(tmp_path, monkeypatch, capsys):
    charts = {NATIVE: l1_full()}
    calls = fake_reader(tmp_path, monkeypatch, charts, "diff")
    outs = {}
    for label, mod in (("old", OLD), ("new", F)):
        o = tmp_path / label
        o.mkdir()
        snap = o / "s.json.gz"
        assert mod.main(["--snapshot", "native", "--out", str(snap)]) == 0
        cap = capsys.readouterr().out
        got = json.load(gzip.open(snap, "rt"))
        got["meta"].pop("taken_at_utc")
        out_json = o / "rep.json"
        hooks = REAL_HOOKS
        code = mod.main(["--compare", str(snap), "--hooks-dir", str(hooks), "--out", str(out_json), "--allow-not-checked"])
        sql_calls = [c["script"] for c in calls()]
        cap2 = capsys.readouterr().out.replace(str(o), "<dir>")
        rep = json.loads(out_json.read_text())
        rep["meta"].pop("compared_at_utc")
        rep["meta"]["snapshot"] = rep["meta"]["snapshot"].replace(str(o), "<dir>")
        rep["meta"]["snapshot_meta"].pop("taken_at_utc")
        outs[label] = (got, re.sub(r"taken:.*|snapshot:.*|sha256:.*", "", cap), code, cap2, rep, sql_calls)
        (tmp_path / "fakereader_diff" / "calls.log").unlink()
        capsys.readouterr()
    assert outs["old"][:5] == outs["new"][:5]
    assert outs["old"][5] == outs["new"][5] and len(outs["new"][5]) == 2  # the SQL sent to the reader is byte-identical (snapshot read + compare read)
    assert "l2" not in outs["new"][0] and "l2" not in outs["new"][0]["meta"] and "l2" not in outs["new"][4]["compared"]


# ----------------------------------------------------------------------------------------------- end to end with the fake FLIP_READER
def test_e2e_snapshot_with_l2_reads_everything_in_one_read_only_transaction(tmp_path, monkeypatch, capsys):
    charts = {NATIVE: dict(l1_full(), l2=l2_full()), OTHER: dict(l1_full(), l2={t: rows_for(t, n=1) for t in L2_29})}
    calls = fake_reader(tmp_path, monkeypatch, charts, "e2e1")
    out = tmp_path / "s.json.gz"
    assert F.main(["--snapshot", "native", "--l2", "--out", str(out)]) == 0
    c = calls()
    assert len(c) == 1, "ONE psql session for L1 and L2 together"
    stmts = [x.strip() for x in c[0]["script"].split(";\n") if x.strip()]
    assert stmts[0] == "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" and stmts[-1] == "COMMIT"
    inner = [re.sub(r"\s+", " ", x) for x in stmts[1:-1]]
    assert all(x.lower().startswith("select") for x in inner)
    l2_sql = [x for x in inner if re.search(r"\bfrom (bodha_|synthesis_)", x)]
    assert len(l2_sql) == 29 and all(f"chart_id='{NATIVE}'" in x for x in l2_sql)
    assert "default_transaction_read_only=on" in c[0]["pgoptions"]
    snap = json.load(gzip.open(out, "rt"))
    assert sorted(snap["l2"]) == L2_29 and snap["l2"]["bodha_msr_signals"] == rows_for("bodha_msr_signals")
    m = snap["meta"]
    assert m["l2"] is True and m["l2_extension_version"] == F.L2_EXTENSION_VERSION and sorted(m["l2_tables"]) == L2_29
    assert m["l2_counts"]["bodha_msr_signals"] == 5 and m["counts"]["chart_facts"] == len(l1_full()["chart_facts"]) and "l2" not in m["counts"]
    assert m["tool_version"] == "2.3" and "l2:" in capsys.readouterr().out
    # sha256 sidecar and atomic write behave as before
    side = (tmp_path / "s.json.gz.sha256").read_text().split()
    assert side[0] == hashlib.sha256(out.read_bytes()).hexdigest() and F.verify_sidecar(str(out))[0] == "ok"
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith("s.json.gz")) == ["s.json.gz", "s.json.gz.sha256"]
    assert F.main(["--snapshot", "native", "--l2", "--out", str(out)]) == F.EXIT_REFUSED  # a baseline is never overwritten


def test_e2e_l2_tables_subset(tmp_path, monkeypatch):
    fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2_full())}, "e2e2")
    out = tmp_path / "s.json.gz"
    assert F.main(["--snapshot", "native", "--l2", "--l2-tables", "bodha_cgm_edges,bodha_cgm_nodes", "--out", str(out)]) == 0
    assert sorted(json.load(gzip.open(out, "rt"))["l2"]) == ["bodha_cgm_edges", "bodha_cgm_nodes"]
    with pytest.raises(SystemExit):
        F.main(["--snapshot", "native", "--l2", "--l2-tables", "bodha_nope", "--out", str(tmp_path / "x.json.gz")])
    with pytest.raises(SystemExit):
        F.main(["--snapshot", "native", "--l2-tables", "bodha_cgm_edges", "--out", str(tmp_path / "y.json.gz")])
    with pytest.raises(SystemExit):
        F.main(["--validate-hooks", "--l2"])


def test_e2e_snapshot_of_an_empty_must_have_l2_table_is_refused_and_writes_nothing(tmp_path, monkeypatch, capsys):
    l2 = l2_full()
    l2["bodha_msr_signals"] = []
    fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2)}, "e2e3")
    out = tmp_path / "s.json.gz"
    assert F.main(["--snapshot", "native", "--l2", "--out", str(out)]) == F.EXIT_READ_ERROR
    assert "EMPTY READ" in capsys.readouterr().err and list(tmp_path.glob("s.json.gz*")) == []
    l2 = l2_full()
    l2["bodha_pratijna"] = []  # legitimately empty: accepted
    fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2)}, "e2e3b")
    assert F.main(["--snapshot", "native", "--l2", "--out", str(out)]) == 0


def hooks_dir_for(tmp_path, *hs, name="l2hooks"):
    d = tmp_path / name
    d.mkdir(exist_ok=True)
    for h in hs:
        (d / f"{h['lane']}.json").write_text(json.dumps(h))
    return d


def test_e2e_compare_live_with_l2_attributes_and_judges_an_l2_hook(tmp_path, monkeypatch, capsys):
    before = dict(l1_full(), l2=l2_full())
    after_l2 = l2_full()
    after_l2["bodha_cgm_edges"][0][4] = f"id={uid(4242)}|v=a|cites=abc0"
    after_l2["bodha_cgm_edges"].append(["lahiri_chitrapaksha", cat_of("bodha_cgm_edges"), "x", "y", f"id={uid(77)}", "1", "single"])
    after_l2["bodha_msr_signals"][0][5] = "9.5,1.5"  # a score only
    fake_reader(tmp_path, monkeypatch, {NATIVE: before}, "snap")
    snap = tmp_path / "pre.json.gz"
    assert F.main(["--snapshot", "native", "--l2", "--out", str(snap)]) == 0
    capsys.readouterr()
    fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=after_l2)}, "cur")
    hd = hooks_dir_for(tmp_path, hook("edges", [l2entry("bodha_cgm_edges", ["value"], expected_count={"exact": 1}), l2entry("bodha_cgm_edges", ["appeared"], expected_count={"exact": 1})]))
    out = tmp_path / "rep.json"
    code = F.main(["--compare", str(snap), "--l2", "--hooks-dir", str(hd), "--out", str(out), "--allow-not-checked"])
    text = capsys.readouterr().out
    rep = json.loads(out.read_text())
    assert code == 0 and rep["verdict"] == "NOT_CHECKED" and rep["changes_total"] == 2 and rep["unattributed"] == 0
    assert sorted(rep["compared"]["l2"]) == L2_29 and rep["meta"]["flags"]["l2"] is True and "continuous (l2 bodha_msr_signals): compared" in text
    assert rep["continuous_l2"]["bodha_msr_signals"]["changed"] == 1
    # the same compare WITHOUT --l2 ignores the L2 section and judges the L2 hook NOT CHECKED
    out2 = tmp_path / "rep2.json"
    code2 = F.main(["--compare", str(snap), "--hooks-dir", str(hd), "--out", str(out2), "--allow-not-checked"])
    rep2 = json.loads(out2.read_text())
    capsys.readouterr()
    assert code2 == 0 and rep2["changes_total"] == 0 and "l2" not in rep2["compared"] and {"edges[0]", "edges[1]"} <= {x["id"] for x in rep2["not_checked"]}
    # an off-by-one expected_count on the L2 table fails the wave
    hd2 = hooks_dir_for(tmp_path, hook("edges", [l2entry("bodha_cgm_edges", ["value"], expected_count={"exact": 2}), l2entry("bodha_cgm_edges", ["appeared"])]), name="l2hooks2")
    out3 = tmp_path / "rep3.json"
    assert F.main(["--compare", str(snap), "--l2", "--hooks-dir", str(hd2), "--out", str(out3), "--allow-not-checked"]) == F.EXIT_FAIL
    assert json.loads(out3.read_text())["failure_counts"]["EXPECTATION_MISMATCH"] == 1
    capsys.readouterr()


def test_e2e_compare_reads_only_the_tables_the_snapshot_carries_and_says_so(tmp_path, monkeypatch, capsys):
    only = {t: rows_for(t) for t in ("bodha_cgm_edges", "bodha_cgm_nodes")}
    snap = write_snap(tmp_path, "pre.json.gz", dict(l1_full(), l2=only), meta_extra={"l2": True})
    calls = fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2_full())}, "partial")
    hd = hooks_dir_for(tmp_path, hook("m", [l2entry("bodha_msr_signals", optional=True)]))
    out = tmp_path / "rep.json"
    F.main(["--compare", str(snap), "--l2", "--hooks-dir", str(hd), "--out", str(out), "--allow-not-checked"])
    rep = json.loads(out.read_text())
    capsys.readouterr()
    assert sorted(rep["compared"]["l2"]) == ["bodha_cgm_edges", "bodha_cgm_nodes"]
    row = next(x for x in rep["not_checked"] if x["id"] == "l2.not_compared")
    assert "bodha_msr_signals missing from the snapshot's l2 section" in row["reason"] and row["declared_by_lanes"] == ["m"]
    assert "l2" in rep["meta"]["skipped_sections"]
    script = calls()[-1]["script"]
    assert "from bodha_msr_signals" not in script and "from bodha_cgm_edges" in script


def test_e2e_compare_against_offline_needs_both_sides_and_never_reads_the_database(tmp_path, monkeypatch, capsys):
    a = write_snap(tmp_path, "a.json.gz", dict(l1_full(), l2=l2_full()))
    b_l2 = l2_full()
    del b_l2["bodha_pratijna"]
    b = write_snap(tmp_path, "b.json.gz", dict(l1_full(), l2=b_l2))
    hd = hooks_dir_for(tmp_path, hook("m", [l2entry("bodha_pratijna", optional=True)]))
    out = tmp_path / "rep.json"
    monkeypatch.delenv("FLIP_READER", raising=False)
    F.main(["--compare", str(a), "--against", str(b), "--l2", "--hooks-dir", str(hd), "--out", str(out), "--allow-not-checked"])
    rep = json.loads(out.read_text())
    capsys.readouterr()
    assert "bodha_pratijna" not in rep["compared"]["l2"] and len(rep["compared"]["l2"]) == 28
    row = next(x for x in rep["not_checked"] if x["id"] == "l2.not_compared")
    assert "bodha_pratijna missing from the --against snapshot's l2 section" in row["reason"]
    # a snapshot without any l2 section while --l2 is asked
    c = write_snap(tmp_path, "c.json.gz", l1_full())
    F.main(["--compare", str(c), "--against", str(c), "--l2", "--hooks-dir", str(hd), "--out", str(out), "--allow-not-checked"])
    rep = json.loads(out.read_text())
    capsys.readouterr()
    assert rep["compared"]["l2"] == [] and any(x["id"] == "l2.not_compared" for x in rep["not_checked"]) and rep["verdict"] == "NOT_CHECKED"
    assert "l2 (Bodha) tables compared: 0 of 29" in "\n".join(F.render_summary(rep))


def test_e2e_compare_other_chart_filters_by_chart_and_l2_read_failure_is_a_read_error_report(tmp_path, monkeypatch, capsys):
    snap = write_snap(tmp_path, "pre.json.gz", dict(l1_full(), l2=l2_full()), chart=OTHER)
    calls = fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2_full()), OTHER: dict(l1_full(), l2={t: [] for t in L2_29})}, "filter")
    hd = hooks_dir_for(tmp_path, hook("m", [l2entry("bodha_msr_signals", optional=True)]))
    out = tmp_path / "rep.json"
    code = F.main(["--compare", str(snap), "--l2", "--hooks-dir", str(hd), "--out", str(out), "--allow-not-checked"])
    rep = json.loads(out.read_text())
    capsys.readouterr()
    # the other chart has no L2 rows: its must-have tables are EMPTY_READ, and no row of the native chart leaked in
    assert code == F.EXIT_FAIL and rep["failure_counts"]["EMPTY_READ"] == len(MUST_HAVE)
    assert all(f"chart_id='{OTHER}'" in x for x in calls()[-1]["script"].split(";\n") if re.search(r"from (bodha_|synthesis_)", x))
    # a reader that fails is a READ_ERROR report with exit 5
    monkeypatch.setenv("FLIP_READER", "/nonexistent/reader")
    out2 = tmp_path / "rep2.json"
    assert F.main(["--compare", str(snap), "--l2", "--hooks-dir", str(hd), "--out", str(out2)]) == F.EXIT_READ_ERROR
    assert json.loads(out2.read_text())["verdict"] == "READ_ERROR"
    capsys.readouterr()


def test_e2e_a_reader_that_prints_only_the_last_result_set_is_an_incomplete_l2_read(tmp_path, monkeypatch):
    fake_reader(tmp_path, monkeypatch, {NATIVE: dict(l1_full(), l2=l2_full())}, "short")
    d = tmp_path / "fakereader_short"
    stub = d / "reader.py"
    stub.write_text(stub.read_text().replace("print(m.group(1)); continue", "continue"))
    with pytest.raises(F.ReadError, match="incomplete read"):
        F.read_state(NATIVE, l2=["bodha_msr_signals"])


def test_read_state_rejects_a_table_outside_the_registry(tmp_path, monkeypatch):
    fake_reader(tmp_path, monkeypatch, {NATIVE: l1_full()}, "bad")
    with pytest.raises(ValueError):
        F.read_state(NATIVE, l2=["chart_facts"])


def test_read_state_without_l2_sends_exactly_the_pre_l2_script(tmp_path, monkeypatch):
    calls = fake_reader(tmp_path, monkeypatch, {NATIVE: l1_full()}, "same")
    F.read_state(NATIVE)
    OLD.read_state(NATIVE)
    c = calls()
    assert len(c) == 2 and c[0]["script"] == c[1]["script"] and "bodha" not in c[0]["script"]


def test_main_help_documents_the_new_flags():
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf), pytest.raises(SystemExit):
        F.main(["--help"])
    assert "--l2" in buf.getvalue() and "--l2-tables" in buf.getvalue()


# ----------------------------------------------------------------------------------------------- golden for the L2 cases (new file; the existing golden is untouched)
def l2_golden_cases():
    t1, t2, t3 = "bodha_msr_signals", "bodha_cgm_edges", "bodha_pratijna"
    before = st_with({t1: rows_for(t1), t2: rows_for(t2), t3: rows_for(t3)})

    def after_fn(s):
        s["l2"][t1][0][4] = f"id={uid(31)}|v=a|cites=abc0"          # identity move: value
        s["l2"][t1][1][5] = "9.5,1.5"                              # score only: not a change
        s["l2"][t2].pop(0)                                         # disappeared
        s["l2"][t2][-1][6] = "classical_match"                     # tier (the dup group member)
        s["l2"][t3].append(["lahiri_chitrapaksha", cat_of(t3), "new", "new", f"id={uid(32)}", "1", ""])  # appeared
    after = mut(before, after_fn)
    h = [hook("a", [l2entry(t1, ["value"], expected_count={"exact": 1}), l2entry(t2, optional=True)]), hook("b", [l2entry(t3, ["appeared"])])]
    out = {}
    for name, hooks_ in (("declared", h), ("undeclared", [])):
        rep = F.compare_states(before, after, copy.deepcopy(hooks_), OTHER, have_dash=False, have_daily=False, l2_tables=(t1, t2, t3), l2_requested=True)
        out[name] = {"verdict": rep["verdict"], "failure_counts": rep["failure_counts"], "changes_total": rep["changes_total"],
                     "by": rep["by_table_category_change_lane"], "not_checked": [x["id"] for x in rep["not_checked"]],
                     "continuous_l2": rep["continuous_l2"], "exit": F.exit_code(rep, True)}
    return out


def test_golden_l2_cases():
    got = l2_golden_cases()
    if os.environ.get("FLIP_DETECTOR_REGEN_GOLDEN") == "1":
        GOLDEN_L2.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n")
    assert got == json.loads(GOLDEN_L2.read_text())


def test_golden_l2_semantics_read_by_a_human():
    got = l2_golden_cases()
    assert got["declared"]["failure_counts"]["UNDECLARED_CHANGE"] == 0 and got["undeclared"]["failure_counts"]["UNDECLARED_CHANGE"] == 4
    assert got["declared"]["changes_total"] == 4 and got["declared"]["verdict"] == "NOT_CHECKED"
    assert got["undeclared"]["verdict"] == "FAIL" and got["undeclared"]["exit"] == 2
    assert got["declared"]["continuous_l2"]["bodha_msr_signals"]["changed"] == 1
