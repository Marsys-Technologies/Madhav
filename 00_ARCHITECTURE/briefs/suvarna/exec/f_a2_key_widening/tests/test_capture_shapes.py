"""The 18-shape capture probe through the REAL capture path (real open_l1_data_plane_generation, guard and capture triggers, as role
data_plane_builder), before and after the apply, with the typed projection read back.

Cases A-K and the seven verification tiers are the 18 shapes; L (a second value-bearing shape in an owned category) and N (all-null, not
floored) extend them; M (a category the asset does not own) must be refused by the ownership guard before AND after: that is the guard's job,
not this patch's."""
from __future__ import annotations

import pytest

import conftest as cf
import shapes


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


FAIL_BEFORE = {"D num+jsonb (aspect_tajik shape)", "E num+text+jsonb (lord_in_house shape)", "F text+jsonb (contradiction_pair shape)",
               "G num=0 + jsonb (zero)", "H all-null floored (sensitive-lane shape)",
               "L UNOWNED category karaka_web_per_varga (text+jsonb)", "N all-null, not floored (single)"}
GUARD_REFUSED = "M UNOWNED category graha_position (num only)"


def key_of(name):
    return f"k{[c['name'] for c in shapes.cases()].index(name)}"


def test_before_the_apply_exactly_the_multi_value_and_all_null_shapes_abort_the_capture(cluster, db):
    res, rows = shapes.run_shapes(cluster, db)
    failed = {n for n, (ok, _) in res.items() if not ok}
    assert failed == FAIL_BEFORE | {GUARD_REFUSED}
    for n in FAIL_BEFORE:
        assert "CheckViolation" in res[n][1] and "l1_data_plane_fact_snapshots_check" in res[n][1], res[n]
    assert "cannot mutate chart_facts category" in res[GUARD_REFUSED][1]


def test_after_the_apply_all_18_shapes_pass_and_the_guard_still_refuses_the_unowned_category(runner, cluster, db):
    code, r = runner.run("apply")
    assert code == 0, r["details"]
    res, rows = shapes.run_shapes(cluster, db)
    first18 = [c["name"] for c in shapes.cases()][:18]
    assert all(res[n][0] for n in first18), {n: res[n] for n in first18 if not res[n][0]}
    assert [n for n, (ok, _) in res.items() if not ok] == [GUARD_REFUSED]


def test_the_typed_projection_keeps_one_value_by_the_precedence_and_records_the_companions(runner, cluster, db):
    runner.run("apply")
    res, rows = shapes.run_shapes(cluster, db)
    k = key_of
    # D: num + jsonb -> num kept, jsonb dropped and named
    r = rows[k("D num+jsonb (aspect_tajik shape)")]
    assert (float(r["value_num"]), r["value_text"], r["value_jsonb"]) == (93.4861, None, None)
    assert r["grain_jsonb"]["typed_value_column"] == "fact_value_num" and r["grain_jsonb"]["companion_value_columns"] == ["fact_value_jsonb"]
    # E: num + text + jsonb -> num kept (precedence), text and jsonb named in that order
    r = rows[k("E num+text+jsonb (lord_in_house shape)")]
    assert (float(r["value_num"]), r["value_text"], r["value_jsonb"]) == (3.0, None, None)
    assert r["grain_jsonb"]["typed_value_column"] == "fact_value_num"
    assert r["grain_jsonb"]["companion_value_columns"] == ["fact_value_text", "fact_value_jsonb"]
    # F: text + jsonb -> text kept (text before jsonb)
    r = rows[k("F text+jsonb (contradiction_pair shape)")]
    assert (r["value_num"], r["value_text"], r["value_jsonb"]) == (None, "pair", None)
    assert r["grain_jsonb"]["typed_value_column"] == "fact_value_text" and r["grain_jsonb"]["companion_value_columns"] == ["fact_value_jsonb"]
    # G: zero with detail: still 'zero', num kept
    r = rows[k("G num=0 + jsonb (zero)")]
    assert r["missingness_state"] == "zero" and float(r["value_num"]) == 0 and r["grain_jsonb"]["typed_value_column"] == "fact_value_num"
    # a single typed value: untouched, NO marker in grain_jsonb (grain_jsonb is exactly what it was)
    for n, want in (("A num only", ("1.5", None, None)), ("B text only", (None, "x", None)), ("C jsonb only", (None, None, {"a": 1}))):
        r = rows[k(n)]
        assert (None if r["value_num"] is None else str(r["value_num"]), r["value_text"], r["value_jsonb"]) == want
        assert set(r["grain_jsonb"]) == {"source_table", "row_identity", "fact_category", "fact_subject", "fact_key"}, n
    # the FULL row stays in the row snapshot: every typed column as written
    full = rows[k("E num+text+jsonb (lord_in_house shape)")]["source_row_jsonb"]
    assert float(full["fact_value_num"]) == 3.0 and full["fact_value_text"] == "kendra" and full["fact_value_jsonb"] == {"h": 3}
    full = rows[k("D num+jsonb (aspect_tajik shape)")]["source_row_jsonb"]
    assert full["fact_value_jsonb"] == {"orb_deg": 93.4861}


def test_an_all_null_row_is_floored_or_unavailable_never_present(runner, cluster, db):
    runner.run("apply")
    res, rows = shapes.run_shapes(cluster, db)
    r = rows[key_of("H all-null floored (sensitive-lane shape)")]
    assert (r["missingness_state"], r["row_state"]) == ("floored", "floored") and r["missingness_reason"]
    assert (r["value_num"], r["value_text"], r["value_jsonb"]) == (None, None, None)
    r = rows[key_of("N all-null, not floored (single)")]
    assert (r["missingness_state"], r["row_state"]) == ("unavailable", "unavailable") and r["missingness_reason"]
    # a producer row that declares its own state keeps it; a floored-by-jsonb row is unchanged by H2
    assert rows[key_of("J jsonb {state:floored}+num")]["missingness_state"] == "floored"


def test_after_the_rollback_the_old_shapes_fail_again(runner, cluster, db):
    assert runner.run("apply")[0] == 0 and runner.run("rollback")[0] == 0
    res, rows = shapes.run_shapes(cluster, db)
    assert {n for n, (ok, _) in res.items() if not ok} == FAIL_BEFORE | {GUARD_REFUSED}
