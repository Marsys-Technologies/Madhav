"""test_n176_chart_scope.py: every live DATA read judges the MEASURED chart's rows (SS, interim census 42e96d491, bo_chart_gestalt).

bo_chart_gestalt's Narr.agree FAIL (`headline_epistemic_jsonb.$.fragility_class` holds 'multi_ayanamsha_tested') was read by `label_distinct_sql`: `SELECT DISTINCT ... FROM <WHOLE table>`, no chart filter. The five rows of the
measured chart (rebuilt 2026-10-06) do not hold that value; OTHER charts' older rows (built by earlier code) do, so the cell judged data that is not the measured chart's. The same whole-table scope applied to the prose_none
closure reads, the Ldgr source reads (exact and existence), the Vocab.alias value reads, Complete.depth, the declared alias read and the Vocab.identity probes.

`read_scopes` names, per owned table, the predicate (`"chart_id" = '<census chart>'` on a table that carries a chart_id column and whose registry count_sql is chart-bound or unreadable; the asset's own rows too on a
table shared with other assets; whole table, said so, for a global table), `set_read_scope` installs it, every data-reading builder applies it in BOTH its exact and its bounded / existence form, and the cell records
which scope it read (`read_scope`). A two-chart fixture on a DISPOSABLE PostgreSQL: the measured chart clean and another chart dirty reads the measured chart's verdict, and the reverse.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_n99_build_completion_integrity as n99  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
CHART = ac.CHART_ID
OTHER = "11111111-2222-3333-4444-555555555555"
T = "n176cs_t"
COLS = ["id", "chart_id", "label", "doc", "citation"]
TYPES = {"id": "integer", "chart_id": "uuid", "label": "text", "doc": "jsonb", "citation": "text"}
R = dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1")


@pytest.fixture
def two_charts(disposable_pg, monkeypatch):
    """A table of two charts; `put(measured_rows, other_rows)` fills it. Rows are (label, fragility_class, citation)."""
    point_psql_at(disposable_pg, monkeypatch)
    ac.set_read_scope(None)

    def put(measured, other):
        ac.psql(f"DROP TABLE IF EXISTS {T}")
        ac.psql(f"CREATE TABLE {T} (id int, chart_id uuid, label text, doc jsonb, citation text)")
        i = 0
        for chart, rows in ((CHART, measured), (OTHER, other)):
            for label, frag, cit in rows:
                i += 1
                ac.psql(f"INSERT INTO {T} VALUES ({i}, '{chart}', {_q(label)}, {_q(json.dumps({'fragility_class': frag}))}::jsonb, {'NULL' if cit is None else _q(cit)})")
    yield put
    ac.set_read_scope(None)
    ac.psql(f"DROP TABLE IF EXISTS {T}")


def _q(s):
    return "'" + s.replace("'", "''") + "'"


def scope(shared=(), decl=None):
    sc = ac.read_scopes([T], R, {T: COLS}, set(shared), decl or {}, CHART)
    ac.set_read_scope(sc)
    return sc


CLEAN = [("Sun", "single_ayanamsha", "BPHS 1.1")] * 3
DIRTY = [("MARS", "multi_ayanamsha_tested", None)] * 3          # a stray label, an out-of-vocabulary value, a row lacking a source, a planet-name spelling


# ───────────────────────── the scope itself ─────────────────────────

def test_read_scopes_names_the_chart_global_and_shared_cases_and_refuses_a_phantom_chart():
    sc = ac.read_scopes([T], R, {T: COLS}, set(), {}, CHART)
    assert sc[T]["where"] == f"(\"chart_id\" = '{CHART}')" and sc[T]["label"] == f"chart {CHART[:8]}"
    glob = ac.read_scopes(["bg_x"], dict(count_sql="SELECT count(*) FROM bg_x"), {"bg_x": ["id", "label"]}, set(), {}, CHART)
    assert glob["bg_x"] == dict(where=None, label="whole table (global: no chart_id column)")
    declared_global = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T}"), {T: COLS}, set(), {}, CHART)         # a chart_id column, but the registry count_sql is not chart-bound
    assert declared_global[T] == dict(where=None, label="whole table (global: the registry count_sql carries no $1 and no chart_id reference)")
    unreadable = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} a JOIN x ON true"), {T: COLS}, set(), {}, CHART)
    assert unreadable[T]["where"] == f"(\"chart_id\" = '{CHART}')"                                                         # unreadable: keeps the chart scope
    shared = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1 AND label IN ('a','b')"), {T: COLS}, {T}, {}, CHART)
    assert shared[T]["where"] == f"(\"chart_id\" = '{CHART}') AND (chart_id = '{CHART}' AND label IN ('a','b'))" and "registry count_sql predicate" in shared[T]["label"] and shared[T]["label"].startswith(f"chart {CHART[:8]}")
    decl = {"produced_tables": [dict(table=T, filter=dict(column="label", equals="Sun"), why="the writer's own row set")]}
    produced = ac.read_scopes([T], R, {T: COLS}, {T}, dict(decl, kind="data"), CHART)
    assert "\"label\"::text = 'Sun'" in produced[T]["where"] and "declared produced rows" in produced[T]["label"]
    with pytest.raises(ac.Unknown, match="phantom"):
        ac.read_scopes([T], R, {T: COLS}, set(), {}, "362f9f17-0000-0000-0000-000000000000")
    with pytest.raises(ac.Unknown, match="not a uuid"):
        ac.read_scopes([T], R, {T: COLS}, set(), {}, "x'; drop table t; --")


def test_the_builders_are_byte_for_byte_unchanged_without_a_scope_and_apply_it_with_one():
    ac.set_read_scope(None)
    plain = [ac.label_distinct_sql("t", "label"), ac.label_stray_sql("t", "label", ["a"]), ac.prose_none_outside_sql("t", "c", "text", dict(column="c", values=["a"]), None),
             ac.prose_none_existence_sql("t", "c", "text", dict(column="c", values=["a"]), None), ac.source_presence_sql("t", "(p)", ["id"], None), ac.ldgr_legacy_count_sql("t", "c", "text"),
             ac.unsourced_declared_sql("t", "(p)", "c", None, ["id"], None)]
    assert not any("chart_id" in q for q in plain)
    ac.set_read_scope({"t": dict(where="\"chart_id\" = 'X'", label="x")})
    try:
        scoped = [ac.label_distinct_sql("t", "label"), ac.label_stray_sql("t", "label", ["a"]), ac.prose_none_outside_sql("t", "c", "text", dict(column="c", values=["a"]), None),
                  ac.prose_none_existence_sql("t", "c", "text", dict(column="c", values=["a"]), None), ac.source_presence_sql("t", "(p)", ["id"], None), ac.ldgr_legacy_count_sql("t", "c", "text"),
                  ac.unsourced_declared_sql("t", "(p)", "c", None, ["id"], None)]
        assert all("\"chart_id\" = 'X'" in q for q in scoped)
        assert "chart_id" not in ac.label_distinct_sql("other_table", "label")                          # a table without an entry is untouched
    finally:
        ac.set_read_scope(None)


# ───────────────────────── Narr.agree: the label check (the bo_chart_gestalt defect) ─────────────────────────

LC = [dict(column="doc.$.fragility_class", values=["single_ayanamsha", "cross_checked"], why="reviewed", evidence="platform/scripts/governance/asset_census.py:1")]


def _label_verdict():
    fetched = {"doc.$.fragility_class": ac.label_read(T, "doc.$.fragility_class", LC[0]["values"])}
    return ac.grade_label_columns(LC, fetched), fetched


def test_REAL_SQL_an_other_charts_older_label_no_longer_fails_the_measured_chart(two_charts):
    two_charts(CLEAN, DIRTY)                                                                           # the measured chart clean, another chart holds 'multi_ayanamsha_tested'
    ac.set_read_scope(None)
    whole, _ = _label_verdict()
    assert whole["v"] == FAIL and "multi_ayanamsha_tested" in whole["measured"]                        # the defect: the whole-table read FAILs the cell on another chart's rows
    scope()
    rec, fetched = _label_verdict()
    assert rec["v"] == PASS and fetched["doc.$.fragility_class"] == ["single_ayanamsha"]               # the measured chart's verdict


def test_REAL_SQL_a_stray_label_in_the_measured_chart_still_fails(two_charts):
    two_charts([("Sun", "multi_ayanamsha_tested", "BPHS 1.1")], CLEAN)
    scope()
    rec, _ = _label_verdict()
    assert rec["v"] == FAIL and "multi_ayanamsha_tested" in rec["measured"]


def test_REAL_SQL_the_bounded_stray_read_is_scoped_too(two_charts):
    two_charts(CLEAN, DIRTY)
    scope()
    assert ac.label_fetch_stray(T, "doc.$.fragility_class", LC[0]["values"])["stray"] == []
    two_charts([("Sun", "multi_ayanamsha_tested", "BPHS 1.1")], CLEAN)
    scope()
    assert ac.label_fetch_stray(T, "doc.$.fragility_class", LC[0]["values"])["stray"] == ["multi_ayanamsha_tested"]


# ───────────────────────── Narr / Null: the prose_none closure (exact and existence) ─────────────────────────

def _closure(estimate):
    pn = dict(why="w" * 20, closed_columns=[dict(column="label", values=["Sun", "Moon"], why="a closed label set"), dict(column="doc", values=None, no_string_leaves=False, json_leaf_patterns=[dict(path="$.fragility_class", values=["single_ayanamsha"])], why="a closed leaf")])
    tables = {T: (COLS, TYPES, None)}
    return ac.prose_none_fetch_outside(tables, T, pn)


@pytest.mark.parametrize("big", [False, True])
def test_REAL_SQL_the_closure_reads_the_measured_charts_rows_in_both_forms(two_charts, monkeypatch, big):
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: (ac.LDGR_CHEAP_MIN_ROWS if big else None))     # big: the bounded existence read; small: the exact count
    two_charts(CLEAN, DIRTY)
    scope()
    got = _closure(big)
    clean = {k: (v["violating"] if isinstance(v, dict) else v) for k, v in got.items()}
    assert clean == {(T, "label"): (False if big else 0), (T, "doc"): (False if big else 0)}, got           # another chart's stray MARS / leaf is not this chart's
    two_charts([("MARS", "multi_ayanamsha_tested", None)] * 2, CLEAN)
    scope()
    dirty = {k: (v["violating"] if isinstance(v, dict) else v) for k, v in _closure(big).items()}
    assert dirty == {(T, "label"): (True if big else 2), (T, "doc"): (True if big else 2)}, dirty             # the reverse: stray only in the measured chart
    ac.set_read_scope(None)
    whole = {k: (v["violating"] if isinstance(v, dict) else v) for k, v in _closure(big).items()}
    assert all(whole.values())                                                                         # (and the unscoped read would have judged the clean chart by another's rows)


# ───────────────────────── Ldgr: the exact and the existence reads of a declared source, the legacy reading ─────────────────────────

SRC = dict(why="a reviewed reason", evidence="platform/scripts/governance/asset_census.py:1", level="row", columns=[dict(column="citation", kinds=["K1"])], citation_state="sourced")


@pytest.mark.parametrize("big", [False, True])
def test_REAL_SQL_the_declared_source_reads_the_measured_chart_in_both_forms(two_charts, monkeypatch, big):
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: (ac.LDGR_CHEAP_MIN_ROWS if big else None))
    two_charts(CLEAN, DIRTY)                                                                           # the other chart's rows LACK a source
    scope()
    rec = ac.source_declared_check("x", SRC, T, COLS, rows=3, keys=[["id"]])["Ldgr.source_presence"]
    assert rec["v"] == PASS, rec["measured"]
    ac.set_read_scope(None)
    assert ac.source_declared_check("x", SRC, T, COLS, rows=6, keys=[["id"]])["Ldgr.source_presence"]["v"] == PARTIAL      # whole table: the other chart's rows made it PARTIAL
    two_charts([("Sun", "single_ayanamsha", None)] * 2 + CLEAN, CLEAN)                                 # a lacking row only in the measured chart
    scope()
    assert ac.source_declared_check("x", SRC, T, COLS, rows=5, keys=[["id"]])["Ldgr.source_presence"]["v"] == PARTIAL


def test_REAL_SQL_the_legacy_citation_reading_and_the_old_ldgr_source_form_are_scoped(two_charts):
    two_charts(CLEAN, DIRTY)
    scope()
    assert ac.ldgr_legacy_presence(T, "citation", 3)["v"] == PASS
    stats = ac.ldgr_fetch_source_stats(T, "citation", ["id"], "text")
    assert stats["rows"] == 3 and stats["lacking"] == 0
    ac.set_read_scope(None)
    assert ac.ldgr_legacy_presence(T, "citation", 6)["v"] == PARTIAL and ac.ldgr_fetch_source_stats(T, "citation", ["id"], "text")["lacking"] == 3


def test_REAL_SQL_the_unsourced_declared_residual_is_judged_on_the_measured_chart(two_charts):
    src = dict(SRC, citation_state="unsourced", residual=ac.UNSOURCED_DECLARED, columns=[dict(column="citation", kinds=["K1"])])
    two_charts([("Sun", "x", None)] * 2, CLEAN)                                                        # measured chart: no row carries a source; the OTHER chart's rows do
    scope()
    assert ac.source_declared_check("x", src, T, COLS, rows=2, keys=[["id"]])["Ldgr.source_presence"]["v"] == NA
    ac.set_read_scope(None)
    assert ac.source_declared_check("x", src, T, COLS, rows=5, keys=[["id"]])["Ldgr.source_presence"]["v"] != NA      # whole table: the other chart's sources refuse the label


# ───────────────────────── Vocab.alias: the value reads ─────────────────────────

def test_REAL_SQL_a_planet_name_spelling_in_another_chart_does_not_fail_the_measured_chart_and_the_reverse(two_charts):
    own = {T: (COLS, dict(TYPES))}
    two_charts(CLEAN, [("MARS", "x", "y")] * 3)
    sc = scope()
    cache = {}
    assert ac.vocab_value_detect(own, cache=cache, scopes=sc)["v"] == PASS
    rec_whole = ac.vocab_value_detect(own, cache=cache)
    assert rec_whole["v"] == FAIL                                                                      # the unscoped read; its own cache key (no collision with the scoped one)
    assert len({k[-1] for k in cache if k[0] == "sample"}) == 2
    two_charts([("MARS", "x", "y")], CLEAN)
    sc = scope()
    rec = ac.vocab_value_detect(own, scopes=sc)
    assert rec["v"] == FAIL and rec["vocab_values"]["scopes"] == {T: f"chart {CHART[:8]}"}


def test_REAL_SQL_a_probe_and_the_na_read_the_measured_charts_rows(two_charts, monkeypatch):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 3)
    own = {T: (COLS, dict(TYPES))}
    two_charts([("plain filler", "plain", "plain")] * 8, [("Sun", "x", "y")] * 8)                      # no vocabulary in the measured chart, a lot in the other
    sc = scope()
    rec = ac.vocab_value_detect(own, scopes=sc)
    assert rec["v"] == NA and rec["vocab_values"]["probed_columns"] and rec["vocab_values"]["scopes"] == {T: f"chart {CHART[:8]}"}
    assert ac.vocab_value_detect(own)["v"] != NA                                                       # unscoped it would not be N/A (judging the other chart)


# ───────────────────────── Complete.depth and the identity probes ─────────────────────────

def test_REAL_SQL_depth_alias_and_identity_reads_are_the_measured_charts(two_charts):
    two_charts(CLEAN, DIRTY[:1])
    scope()
    d = ac.depth_census(T, COLS)
    assert d["rows"] == 3 and "citation" in d["full"]                                                  # citation is populated on all 3 measured rows (the other chart's row has NULL)
    ac.set_read_scope(None)
    d2 = ac.depth_census(T, COLS)
    assert d2["rows"] == 4 and "citation" not in d2["full"]
    scope()
    assert ac.scalar(f"SELECT EXISTS(SELECT 1 FROM {T}{ac._where_scope(T)} GROUP BY label HAVING count(*) > 1)::text") == "true"
    two_charts([("Sun", "a", "b")], [("Sun", "a", "b")] * 3)
    scope()
    assert ac.scalar(f"SELECT EXISTS(SELECT 1 FROM {T}{ac._where_scope(T)} GROUP BY label HAVING count(*) > 1)::text") == "false"           # the other chart's duplicates are not this chart's


# ───────────────────────── measure(): the scope is set per asset, stamped, and cleared ─────────────────────────

@pytest.mark.parametrize("rows_exist", [True, False])
def test_measure_sets_the_scope_per_asset_stamps_every_data_record_and_clears_it(monkeypatch, tmp_path, rows_exist):
    aid = "ga_x"
    reg = {aid: dict(n99._reg_row(aid, has_integrity=False), target_table="ga_t", count_sql="SELECT count(*) FROM ga_t WHERE chart_id = $1")}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=5)
    cols = ["id", "chart_id", "label"]
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"ga_t"}, cols={"ga_t": cols}, keys={"ga_t": [["id"]]}, views=set(), types={"ga_t": {"id": "integer", "chart_id": "uuid", "label": "text"}}, defaults={"ga_t": {}},
                                                       types_error=None, udts={}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {aid: dict(kind="data")})
    sql_seen = []

    def fake_psql(sql, sep="\x1f", timeout=None):
        sql_seen.append(sql)
        if sql.startswith('SELECT EXISTS(SELECT 1 FROM "ga_t" WHERE'):                                      # the empty-scope probe
            return [["t" if rows_exist else "f"]]
        if "SELECT jsonb_build_object('label'," in sql and sql.startswith("WITH lex AS"):
            return [[json.dumps(dict(label=dict(rows=2, values=["Sun", "Moon"], emb=[])))]]
        if "format_type(a.atttypid" in sql:
            return [["text"]]
        if "IS NOT NULL" in sql:
            return [["5"]]
        if "EXISTS" in sql:
            return [["f"]]
        return []
    monkeypatch.setattr(ac, "psql", fake_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (fake_psql(sql) or [[None]])[0][0])
    got = {a["asset_id"]: a["measurements"] for a in ac.measure("L1")["assets"]}[aid]
    if not rows_exist:                                                                                 # no rows for the measured chart: the vocabulary is not read, the cell is NO_DETECTOR, the stamp says why
        assert got["Vocab.alias"]["read_scope"] == {"ga_t": f"chart {CHART[:8]}; NO ROWS in this scope"} and got["Vocab.alias"]["v"] == NO_DET
        assert not [q for q in sql_seen if q.startswith("WITH lex AS")]
    else:
        assert got["Vocab.alias"]["read_scope"] == {"ga_t": f"chart {CHART[:8]}"} and got["Vocab.alias"]["v"] == PASS
        vocab_sql = [q for q in sql_seen if q.startswith("WITH lex AS")]
        assert vocab_sql and all(f"\"chart_id\" = '{CHART}'" in q for q in vocab_sql)
    assert ac._READ_SCOPE == {}                                                                        # cleared: no scope leaks past the asset (or the run)


def test_every_data_reading_criterion_is_in_the_stamp_list_and_a_record_without_scopes_is_untouched():
    assert {"Narr.agree", "Null.blank_rows", "Ldgr.source_presence", "Vocab.alias", "Vocab.identity", "Complete.depth"} <= set(ac.READ_SCOPE_CRITERIA)
    m = {"Vocab.alias": dict(v=PASS, measured="x"), "Build.dag": dict(v=PASS, measured="y")}
    ac.stamp_read_scope(m, {})
    assert m == {"Vocab.alias": dict(v=PASS, measured="x"), "Build.dag": dict(v=PASS, measured="y")}
    ac.stamp_read_scope(m, {"t": dict(where=None, label="whole table (global: no chart_id column)")})
    assert m["Vocab.alias"]["read_scope"] == {"t": "whole table (global: no chart_id column)"} and "read_scope" not in m["Build.dag"]


def test_REAL_SQL_the_identity_probes_are_behaviourally_scoped(two_charts):
    """`identity_duplicates` / `identity_has_rows` (what measure() calls for Vocab.identity) read the measured chart: the other chart's duplicates are not this chart's, and the reverse."""
    two_charts([("Sun", "a", "b"), ("Moon", "a", "b")], [("Sun", "a", "b")] * 3)                         # measured chart: unique labels; the other chart repeats a label
    scope()
    assert ac.identity_duplicates(T, "label") == (False, "0 duplicate(s)")
    ac.set_read_scope(None)
    assert ac.identity_duplicates(T, "label")[0] is True                                                # whole table: the other chart's duplicates would FAIL the cell
    two_charts([("Sun", "a", "b")] * 3, [("Sun", "a", "b"), ("Moon", "a", "b")])                        # the reverse: duplicates only in the measured chart
    scope()
    assert ac.identity_duplicates(T, "label") == (True, "2 duplicate(s) in 1 duplicate group(s)")
    assert ac.identity_has_rows(T) is True
    two_charts([], [("Sun", "a", "b")])                                                                 # no rows for the measured chart
    scope()
    assert ac.identity_has_rows(T) is False
    ac.set_read_scope(None)
    assert ac.identity_has_rows(T) is True
