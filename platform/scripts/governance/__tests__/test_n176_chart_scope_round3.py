"""test_n176_chart_scope_round3.py: the round-3 re-check of the measured-chart scope.

HIGH      a chart-bound count_sql was read as GLOBAL when it was not the bare `chart_id = $1` (`WHERE chart_id = $1::uuid`, ga_yoga's registry seed): every read of the asset saw all charts. A table is global only
          when its count_sql tail has NO `$1` and NO `chart_id` reference at all; any other tail keeps the chart scope. (`_chart_pinned`, which decides whether a COUNT is exact, also accepts the casts and quoting now.)
MED-HIGH  a shared table with two produced_tables filters was scoped to the FIRST only: all declared filters are ORed.
MED       a scoped table with ZERO rows for the chart is not judged (a closure over no rows is not 'holds'): label, prose_none, Vocab and Ldgr reads read NO_DETECTOR; a verified zero_row_convention lifts the guard.
LOW       unknown columns => the read is not made (NO_DETECTOR with the cause); the json branch of the vocabulary probe is scoped (two-chart test); the code compiles on Python 3.11 (no nested same-quote
          f-string, no backslash or newline in an f-string expression).
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
CHART = ac.CHART_ID
OTHER = "11111111-2222-3333-4444-555555555555"
T = "n176r3_t"
COLS = ["id", "chart_id", "node_type", "label", "doc", "citation"]
TYPES = {"id": "integer", "chart_id": "uuid", "node_type": "text", "label": "text", "doc": "jsonb", "citation": "text"}


def _q(s):
    return "'" + s.replace("'", "''") + "'"


@pytest.fixture
def table(disposable_pg, monkeypatch):
    """`put(rows)`: rows are (chart, node_type, label, doc_dict|None, citation|None)."""
    point_psql_at(disposable_pg, monkeypatch)
    ac.set_read_scope(None)

    def put(rows):
        ac.psql(f"DROP TABLE IF EXISTS {T}")
        ac.psql(f"CREATE TABLE {T} (id int, chart_id uuid, node_type text, label text, doc jsonb, citation text)")
        for i, (chart, nt, label, doc, cit) in enumerate(rows):
            ac.psql(f"INSERT INTO {T} VALUES ({i}, '{chart}', {_q(nt)}, {_q(label)}, {('NULL' if doc is None else _q(json.dumps(doc)) + '::jsonb')}, {'NULL' if cit is None else _q(cit)})")
    yield put
    ac.set_read_scope(None)
    ac.psql(f"DROP TABLE IF EXISTS {T}")


# ───────────────────────── HIGH: any chart reference keeps the chart scope ─────────────────────────

CHART_BOUND = ["SELECT COUNT(*) FROM ga_yoga_firings WHERE chart_id = $1::uuid", "SELECT count(*) FROM ga_yoga_firings WHERE chart_id::text = $1",
               'SELECT count(*) FROM ga_yoga_firings WHERE "chart_id" = $1', "SELECT count(*) FROM ga_yoga_firings f WHERE f.chart_id = $1::uuid AND f.x > 0",
               "SELECT count(*) FROM ga_yoga_firings WHERE chart_id = $1", "SELECT count(*) FROM ga_yoga_firings WHERE $1::uuid = chart_id", "select count(*) from ga_yoga_firings where CHART_ID = $1",
               "SELECT count(*) FROM ga_yoga_firings WHERE chart_id = $1 OR kind = 'x'", "SELECT count(*) FROM ga_yoga_firings WHERE kind = 'x'  /* chart_id handled elsewhere */"]
GLOBAL = ["SELECT count(*) FROM ga_yoga_firings", "SELECT count(*) FROM ga_yoga_firings WHERE kind = 'x'", "SELECT COUNT(*) FROM ga_yoga_firings WHERE tier IN ('a','b')"]


@pytest.mark.parametrize("count_sql", CHART_BOUND[:-1])
def test_a_count_sql_that_mentions_the_chart_in_any_form_keeps_the_chart_scope(count_sql):
    sc = ac.read_scopes(["ga_yoga_firings"], dict(count_sql=count_sql), {"ga_yoga_firings": ["id", "chart_id", "kind"]}, set(), {}, CHART)
    assert sc["ga_yoga_firings"]["where"] == f"(\"chart_id\" = '{CHART}')" and sc["ga_yoga_firings"]["label"] == f"chart {CHART[:8]}", count_sql


@pytest.mark.parametrize("count_sql", GLOBAL)
def test_a_count_sql_with_no_chart_reference_at_all_is_global_and_says_so(count_sql):
    sc = ac.read_scopes(["ga_yoga_firings"], dict(count_sql=count_sql), {"ga_yoga_firings": ["id", "chart_id", "kind"]}, set(), {}, CHART)
    assert sc["ga_yoga_firings"] == dict(where=None, label="whole table (global: the registry count_sql carries no $1 and no chart_id reference)")


def test_the_chart_pin_matcher_accepts_casts_and_quoting_and_still_refuses_what_it_did():
    for tail in (" WHERE chart_id = $1::uuid", " WHERE chart_id::text = $1", ' WHERE "chart_id" = $1', " WHERE c.chart_id = $1::uuid AND x = 1", " WHERE (chart_id = $1::uuid)"):
        assert ac._chart_pinned(tail), tail
    for tail in (" WHERE chart_id = $10", " WHERE a = 1 OR chart_id = $1::uuid", " WHERE chart_id <> $1", " WHERE other_chart_id = $1"):
        assert not ac._chart_pinned(tail), tail
    assert ac._tail_mentions_chart(" WHERE x = $1") and ac._tail_mentions_chart(' WHERE "Chart_Id" IS NOT NULL') and not ac._tail_mentions_chart(" WHERE kind = 'x'")


# ───────────────────────── MED-HIGH: every declared produced filter, ORed ─────────────────────────

def _decl(*filters):
    return {"kind": "data", "produced_tables": [dict(table=T, filter=dict(column="node_type", equals=f), why="the writer's own row set") for f in filters]}


def test_the_scopes_or_every_declared_filter_and_the_label_counts_them():
    two = ac.vocab_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T}"), {}, {T}, _decl("arudha", "special_lagna"), CHART)
    assert two[T]["where"] == "(\"node_type\"::text = 'arudha') OR (\"node_type\"::text = 'special_lagna')" and "2 filters, ORed" in two[T]["label"] and "node_type = 'special_lagna'" in two[T]["label"]
    one = ac.vocab_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T}"), {}, {T}, _decl("arudha"), CHART)
    assert one[T]["where"] == "(\"node_type\"::text = 'arudha')" and "1 filter, ORed" in one[T]["label"]
    full = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, {T}, _decl("arudha", "special_lagna"), CHART)
    assert full[T]["where"].startswith(f"(\"chart_id\" = '{CHART}') AND ((\"node_type\"::text = 'arudha') OR (") and full[T]["label"].startswith(f"chart {CHART[:8]}; the asset's declared produced rows (2 filters")
    # an unfiltered declared entry for the table is the whole table: no restriction from the declaration (the count_sql predicate decides)
    mixed = {"kind": "data", "produced_tables": [dict(table=T, filter=dict(column="node_type", equals="arudha"), why="x"), dict(table=T, why="the rest of the table")]}
    assert "declared produced rows" not in ac.vocab_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T}"), {}, {T}, mixed, CHART)[T]["label"]


def test_REAL_SQL_rows_only_under_the_second_filter_are_read(table):
    """bo_karanajala declares bodha_cgm_nodes twice (node_type arudha and special_lagna): the second filter's rows were never read."""
    table([(CHART, "arudha", "Sun", None, "BPHS 1.1"), (CHART, "arudha", "Moon", None, "BPHS 1.1"), (CHART, "special_lagna", "MARS", None, "BPHS 1.1"), (CHART, "other_asset", "SATURN", None, "BPHS 1.1")])
    types = dict(TYPES)
    own = {T: (list(types), types)}
    sc = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, {T}, _decl("arudha", "special_lagna"), CHART)
    rec = ac.vocab_value_detect(own, scopes=sc)
    assert rec["v"] == FAIL and "'MARS'" in rec["measured"] and "SATURN" not in rec["measured"]               # the special_lagna row is read; the other asset's SATURN is not
    only_first = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, {T}, _decl("arudha"), CHART)
    assert ac.vocab_value_detect(own, scopes=only_first)["v"] == PASS                                          # (what the first-filter-only scope used to give)


# ───────────────────────── MED: an empty scoped read is vacuous ─────────────────────────

LC = [dict(column="label", values=["Sun", "Moon"], why="reviewed", evidence="platform/scripts/governance/asset_census.py:1")]
PN = dict(why="w" * 20, closed_columns=[dict(column="label", values=["Sun", "Moon"], why="a closed label set")])
SRC = dict(why="a reviewed reason", evidence="platform/scripts/governance/asset_census.py:1", level="row", columns=[dict(column="citation", kinds=["K1"])], citation_state="sourced")


def _scoped(convention=False):
    sc = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, set(), {}, CHART)
    ac.mark_empty_scopes(sc, convention_holds=convention)
    ac.set_read_scope(sc)
    return sc


def test_REAL_SQL_a_table_with_no_rows_for_the_chart_is_not_judged_by_any_read(table, monkeypatch):
    table([(OTHER, "a", "Sun", {"k": "v"}, "BPHS 1.1")] * 3)                                                    # rows exist, but none for the measured chart
    sc = _scoped()
    assert sc[T].get("empty") is True and "NO ROWS in this scope" in sc[T]["label"] and "vacuous" in sc[T]["block"]
    # label
    got = ac.label_read(T, "label", ["Sun", "Moon"])
    assert got == dict(blocked=sc[T]["block"])
    rec = ac.grade_label_columns(LC, {"label": got})
    assert rec["v"] == NO_DET and "were not read" in rec["measured"] and rec["v"] not in (PASS, NA)           # (an empty fetched list used to grade PASS)
    # prose_none closure
    narrow = {T: (["id", "label"], {"id": "integer", "label": "text"}, None)}
    out = ac.prose_none_fetch_outside(narrow, T, PN)
    assert out[(T, "label")]["unread"] == sc[T]["block"]
    decl = {"prose_fields": [], "evidence": {"prose_fields": "platform/scripts/governance/asset_census.py:1"}, "prose_none": PN}
    graded = ac.grade_prose_none("x", decl, narrow, T, out, written={T: {"label"}})
    assert all(graded[c]["v"] == NO_DET and "the closure was not read" in graded[c]["measured"] for c in ac.NARR_CHECKS + ac.NULL_CHECKS)
    # vocabulary
    own = {T: (COLS, dict(TYPES))}
    vrec = ac.vocab_value_detect(own, scopes=sc)
    assert vrec["v"] == NO_DET and vrec["v"] != NA and "NO rows" in vrec["measured"]
    # Ldgr (exact and existence), the residual, the legacy reading
    for est in (None, ac.LDGR_CHEAP_MIN_ROWS):                                                                 # the exact read and the existence read
        monkeypatch.setattr(ac, "source_estimate_rows", lambda t, e=est: e)
        assert ac.source_declared_check("x", SRC, T, COLS, rows=0, keys=[["id"]])["Ldgr.source_presence"]["v"] == NO_DET
    residual = dict(SRC, citation_state="unsourced", residual=ac.UNSOURCED_DECLARED)
    assert ac.source_declared_check("x", residual, T, COLS, rows=0, keys=[["id"]])["Ldgr.source_presence"]["v"] == NO_DET
    assert ac.depth_census(T, COLS)["note"] == "table empty"


def test_a_verified_zero_row_convention_lifts_the_guard(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: "f")
    sc = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, set(), {}, CHART)
    assert "block" not in ac.mark_empty_scopes(dict(sc), convention_holds=True)[T]
    assert ac.mark_empty_scopes(dict(sc))[T]["empty"] is True


def test_the_empty_probe_marks_only_scoped_tables_and_a_failed_probe_marks_nothing(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda q: (seen.append(q), "t")[1])
    sc = {"a": dict(where="\"chart_id\" = 'X'", label="chart X"), "b": dict(where=None, label="whole table (global)")}
    ac.mark_empty_scopes(sc)
    assert len(seen) == 1 and "FROM \"a\"" in seen[0] and "block" not in sc["a"] and "block" not in sc["b"]
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(ac.Unknown("ERROR:  canceling statement due to statement timeout")))
    ac.mark_empty_scopes(sc)
    assert "block" not in sc["a"]


def test_a_non_empty_scope_is_judged_as_before(table):
    table([(CHART, "a", "Sun", None, "BPHS 1.1"), (OTHER, "a", "MARS", None, None)])
    sc = _scoped()
    assert "block" not in sc[T] and ac.label_read(T, "label", ["Sun", "Moon"]) == ["Sun"]
    assert ac.grade_label_columns(LC, {"label": ["Sun"]})["v"] == PASS


# ───────────────────────── LOW-1: unknown columns => not read ─────────────────────────

@pytest.mark.parametrize("cols", [None, [], ()])
def test_a_table_whose_columns_could_not_be_read_is_not_scoped_as_global_it_is_not_read(cols):
    sc = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: cols}, set(), {}, CHART)
    assert sc[T]["where"] is None and "columns not read" in sc[T]["label"] and "cannot be scoped" in sc[T]["block"]
    ac.set_read_scope(sc)
    try:
        assert ac.label_read(T, "label", ["a"]) == dict(blocked=sc[T]["block"])
        assert "cannot be scoped" in ac.prose_none_fetch_outside({T: (COLS, TYPES, None)}, T, PN)[(T, "label")]["unread"]
        assert ac.vocab_value_detect({T: (COLS, dict(TYPES))}, scopes=sc)["v"] == NO_DET
    finally:
        ac.set_read_scope(None)


# ───────────────────────── LOW-2: the json branch of the vocabulary probe is scoped ─────────────────────────

def test_REAL_SQL_the_json_probe_and_its_oversized_check_read_the_measured_charts_rows(table, monkeypatch):
    monkeypatch.setattr(ac, "VOCAB_JSON_SAMPLE_ROWS", 2)
    monkeypatch.setattr(ac, "VOCAB_JSON_MAX_BYTES", 200)
    small = {"k": "plain words"}
    big = {"k": "x" * 400}                                                                                      # an OVERSIZED document, in the OTHER chart only
    rows = [(CHART, "a", "n", small, None)] * 5 + [(OTHER, "a", "n", {"g": "Sun"}, None)] * 3 + [(OTHER, "a", "n", big, None)]
    table(rows)
    own = {T: (COLS, dict(TYPES))}
    sc = ac.read_scopes([T], dict(count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1"), {T: COLS}, set(), {}, CHART)
    scoped = ac.vocab_value_detect(own, scopes=sc)
    assert scoped["v"] == NA and "doc" in " ".join(scoped["vocab_values"]["probed_columns"])                      # the probe reached the end of the MEASURED chart's rows: no term, no oversized row there
    probe = ac.vocab_probe_sql(T, "doc", "json", sc[T]["where"])
    assert probe.count(sc[T]["where"]) == 2                                                                      # the leaf CTE and the `oversized` EXISTS both carry the scope
    unscoped = ac.vocab_value_detect(own)
    assert unscoped["v"] != NA                                                                                   # the other chart's `Sun` / oversized row would have been judged
    raw = ac.scalar(ac.vocab_probe_sql(T, "doc", "json", sc[T]["where"]))
    assert json.loads(raw)["oversized"] is False and json.loads(ac.scalar(ac.vocab_probe_sql(T, "doc", "json")))["oversized"] is True


# ───────────────────────── LOW-4: the code compiles on Python 3.11 ─────────────────────────

def nested_fstring_problems(path):
    """f-strings that only Python 3.12+ accepts: an expression part holding the string's own quote, a backslash, or (in a single-quoted f-string) a newline."""
    src = pathlib.Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src, feature_version=(3, 11))
    lines = src.splitlines(keepends=True)
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln))

    def pos(l, c):
        return offs[l - 1] + len(lines[l - 1].encode()[:c].decode())
    bad, inner = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) and id(node) not in inner:
            seg = src[pos(node.lineno, node.col_offset):pos(node.end_lineno, node.end_col_offset)]
            m = re.match(r'[rRbBuUfF]*("""|\'\'\'|"|\')', seg)
            if not m:
                continue
            q = m.group(1)
            for fv in ast.walk(node):
                if isinstance(fv, ast.JoinedStr) and fv is not node:
                    inner.add(id(fv))
                if isinstance(fv, ast.FormattedValue):
                    e = src[pos(fv.value.lineno, fv.value.col_offset):pos(fv.value.end_lineno, fv.value.end_col_offset)]
                    if q in e or "\\" in e or ("\n" in e and len(q) == 1):
                        bad.append((node.lineno, e[:60]))
                        break
    return bad


def test_the_scanner_catches_what_python_3_11_rejects(tmp_path):
    p = tmp_path / "x.py"
    p.write_text("a = 1\nb = f'{\",\".join(\"x\")}'\nc = f'{a}'\nd = f'{ \"a\" + f\"{a}\" }'\n", encoding="utf-8")
    assert nested_fstring_problems(p) == []                                  # a DIFFERENT quote inside an f-string is fine on 3.11
    q = tmp_path / "y.py"
    q.write_text("a = 1\nb = f'{\"x\" if a else f\'y\'}'\n", encoding="utf-8")
    assert [l for l, _ in nested_fstring_problems(q)] == [2]                 # the SAME quote nested: 3.12+ only
    r = tmp_path / "z.py"
    r.write_text("a = 1\nb = f'{\"\\\\n\".join([])}'\n", encoding="utf-8")
    assert [l for l, _ in nested_fstring_problems(r)] == [2]                 # a backslash inside the expression: 3.12+ only


@pytest.mark.parametrize("name", ["asset_census.py", "census_postprocess.py", "__tests__/test_n176_vocab_values.py", "__tests__/test_n176_vocab_values_review.py", "__tests__/test_n176_vocab_values_round2.py",
                                  "__tests__/test_n176_chart_scope.py", "__tests__/test_n176_chart_scope_round3.py", "__tests__/test_n176_prose_none_existence.py", "__tests__/test_n177_unsourced_declared.py",
                                  "__tests__/test_n178_completion_latest_attempt.py"])
def test_no_f_string_needs_python_3_12(name):
    assert nested_fstring_problems(HERE.parent / name) == [], name
