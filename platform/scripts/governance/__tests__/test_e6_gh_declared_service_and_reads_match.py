"""test_e6_gh_declared_service_and_reads_match.py — E6 work-list items (g) and (h) (N-22 proposal v1.2.3, section 5).

(g) `Build.target`: a DECLARED service satisfies check 3 (T4:274: "a `target_table` set, **or** service / multi-table
    declared explicitly") as a PASS BY DECLARATION. No measurement stands behind it (nothing tests the declaration), and
    the verdict text and record say so (CLAUDE.md N.8). "Declared" = the asset-declarations file says `kind: service`
    AND the registry `asset_kind` is also `service`; where they disagree the current reading stands (N/A, cause-keyed).

(h) `Build.dag`: the reads-match detector (T4:275, check 4: "the declared edges match what the asset actually reads").
    What the writer code SELECTs (FROM / JOIN, followed through first-party delegation) against the asset's declared
    `depends_on` edges: a read of another asset's produced table with no declared edge is a FAIL naming the missing edge;
    "reads nothing undeclared" is a PASS only when the parse is demonstrably complete, else NO_DETECTOR (never a PASS by
    absence of a parse, N.8). Resolvability (unknown depends_on ids) is unchanged and still a FAIL.

Offline: the `_stub_layer` harness of E6 packet (a) plus a python-sidecar tree on disk (W2-3). No database.
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
import test_e6_a_na_causes as pa  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

NA = "N/A"
_HDR = w3._HDR


# ═════════════════════════════════ (g) Build.target: PASS by declaration ═════════════════════════════════

def _decl(kind, **extra):
    return {"kind": kind, "carriage": None, "prose_fields": None, "terminal_by_construction": None,
            "cross_asset_writes": None, "read_evidence": None, "read_table": None, "read_kind": None,
            "evidence": None, **extra}


def _target(monkeypatch, tmp_path, row, declared):
    """Build.target record for one registry row under a declarations mapping {asset_id: entry}."""
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: dict(declared))
    return pa._m(monkeypatch, tmp_path, {row["asset_id"]: row})[row["asset_id"]]["Build.target"]


@pytest.mark.parametrize("has_writer", [True, False])
def test_g_a_declared_service_with_no_table_reads_pass_by_declaration(monkeypatch, tmp_path, has_writer):
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="service", has_writer=has_writer),
                  {"svc": _decl("service")})
    assert rec["v"] == ac.PASS, rec
    assert rec.get("basis") == "declaration", rec
    assert "cause" not in rec, "a PASS carries no N/A cause"
    txt = rec["measured"]
    assert "PASS by declaration" in txt and "T4:274" in txt, txt
    assert "no measurement" in txt, "the verdict must say nothing measured it"
    assert "cannot fail" in txt or "no fail path" in txt, "the verdict must say the detector has no fail path"


def test_g_the_declaration_alone_is_not_enough_a_registry_disagreement_keeps_the_current_reading(monkeypatch, tmp_path):
    # registry says service, the file says data: current code = cause-keyed N/A (NO_DETECTOR at the rollup)
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="service", has_writer=True), {"svc": _decl("data")})
    assert rec["v"] == NA and rec["cause"] == "service-no-target-table", rec
    # registry says service, the file says nothing about it (absent / null kind)
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="service", has_writer=True), {})
    assert rec["v"] == NA and rec["cause"] == "service-no-target-table", rec
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="service", has_writer=True), {"svc": _decl(None)})
    assert rec["v"] == NA and rec["cause"] == "service-no-target-table", rec
    # registry says data + no writer, the file says service: the registry fact decides, the N/A stands
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="data", has_writer=False), {"svc": _decl("service")})
    assert rec["v"] == NA and rec["cause"] == "no-writer-no-target-table", rec
    # registry says data + writer + no table: the table-less grading (R53) is untouched by a service declaration
    monkeypatch.setattr(ac, "target_owners", lambda: {})
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="data", has_writer=True,
                                                     count_sql="SELECT count(*) FROM orphan_t"), {"svc": _decl("service")})
    assert rec["v"] == ac.FAIL and "declaration is missing" in rec["measured"], rec
    # registry `artifact` is not compared with the file's service
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="artifact", has_writer=False), {"svc": _decl("service")})
    assert rec["v"] == NA, rec


def test_g_other_kinds_are_never_a_declared_service(monkeypatch, tmp_path):
    for kind in ("view", "static", "rider", "probe", "user_data"):
        rec = _target(monkeypatch, tmp_path, pa._reg_row("x", asset_kind="service", has_writer=True), {"x": _decl(kind)})
        assert rec["v"] == NA, (kind, rec)


def test_g_a_target_table_still_reads_pass_on_the_table_not_on_the_declaration(monkeypatch, tmp_path):
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", target_table="t_svc", asset_kind="service", has_writer=True),
                  {"svc": _decl("service")})
    assert rec["v"] == ac.PASS and rec["measured"] == "target_table=t_svc" and "basis" not in rec, rec


def test_g_an_unreadable_declarations_file_keeps_the_current_reading(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise ac.DeclarationsError("cannot read the declarations file")
    monkeypatch.setattr(ac, "load_asset_declarations", boom)
    m = pa._m(monkeypatch, tmp_path, {"svc": pa._reg_row("svc", asset_kind="service", has_writer=True)})
    assert m["svc"]["Build.target"]["v"] == NA, m["svc"]["Build.target"]


def test_g_the_rollup_reports_the_pass_as_declared_not_measured():
    rec = dict(v=ac.PASS, measured="x", basis="declaration")
    c = ac._check_contribution("Build.target", "L3", rec, None)
    assert c["v"] == ac.PASS and c["state"] == "MEASURED", c
    assert "declar" in c["reason"] and c["reason"] != "measured", c
    assert ac._check_contribution("Build.target", "L3", dict(v=ac.PASS, measured="x"), None)["reason"] == "measured"


SIX = ("bg_ephemeris_engine", "bg_panchanga", "ka_dasha_kala", "ka_graha_sancara", "ka_muhurta_seva", "ka_tulana")


@pytest.mark.parametrize("aid", SIX)
def test_g_the_six_census_visible_services_move_with_the_real_declarations_file(monkeypatch, tmp_path, aid):
    decl = ac.load_asset_declarations()
    assert decl[aid]["kind"] == "service"
    wr = not aid.startswith("bg_")
    rec = pa._m(monkeypatch, tmp_path, {aid: pa._reg_row(aid, asset_kind="service", has_writer=wr)})[aid]["Build.target"]
    assert rec["v"] == ac.PASS and rec["basis"] == "declaration", rec


@pytest.mark.parametrize("aid", ("mi_abhilekha", "mi_seva"))
def test_g_the_two_services_with_a_table_are_unchanged(monkeypatch, tmp_path, aid):
    rec = pa._m(monkeypatch, tmp_path, {aid: pa._reg_row(aid, target_table="t", asset_kind="service", has_writer=True)})[aid]["Build.target"]
    assert rec == dict(v=ac.PASS, measured="target_table=t"), rec


# ═════════════════════════════════ (h) the SQL relation reader ═════════════════════════════════

def rel(sql):
    return ac.sql_relations(sql)


def test_h_from_join_and_comma_lists():
    t, d = rel("SELECT a.x FROM alpha a JOIN beta AS b ON b.id = a.id LEFT JOIN public.gamma g ON true, delta WHERE 1=1")
    assert t == ["alpha", "beta", "gamma", "delta"] and d == []


def test_h_quoted_schema_and_case_are_normalised_and_foreign_schemas_are_not_asset_tables():
    t, d = rel('SELECT 1 FROM "Public"."Alpha" JOIN pg_temp.beta USING (id) JOIN information_schema.tables t2 ON true')
    assert t == ["alpha"] and d == []


def test_h_functions_subqueries_values_are_not_relations_but_their_inner_reads_are():
    t, d = rel("SELECT * FROM (SELECT z FROM inner_t) s, unnest(ARRAY[1,2]) u(n), jsonb_array_elements(s.j) e, "
               "generate_series(1,3) g, (VALUES (1),(2)) v(x), real_t WHERE true")
    assert sorted(t) == ["inner_t", "real_t"] and d == []


def test_h_ctes_are_not_relations():
    t, d = rel("WITH RECURSIVE dep AS (SELECT a FROM asset_registry UNION SELECT b FROM dep JOIN real_t ON true), "
               "other(x) AS MATERIALIZED (SELECT 1 FROM third_t) SELECT * FROM dep, other")
    assert sorted(t) == ["asset_registry", "real_t", "third_t"] and d == []


def test_h_non_relation_froms_are_ignored():
    t, d = rel("SELECT EXTRACT(year FROM col), SUBSTRING(s FROM 2), TRIM(BOTH 'x' FROM y), a IS DISTINCT FROM b, "
               "'text from nowhere', 1 -- from a_comment\n /* from block_comment */ FROM real_t")
    assert t == ["real_t"] and d == []


def test_h_a_delete_target_is_a_write_not_a_read_but_update_from_and_insert_select_are_reads():
    t, d = rel("DELETE FROM written_t WHERE id IN (SELECT id FROM read_t)")
    assert t == ["read_t"]
    t, d = rel("UPDATE upd_t SET a = s.a FROM src_t s WHERE upd_t.id = s.id")
    assert t == ["src_t"]
    t, d = rel("INSERT INTO ins_t (a) SELECT a FROM src_t")
    assert t == ["src_t"]


def test_h_dynamic_tables_are_reported_never_guessed():
    for sql in ("SELECT 1 FROM {?} WHERE x", "SELECT 1 FROM %s", "SELECT 1 FROM {table}", "SELECT 1 FROM ",
                "SELECT 1 FROM a JOIN {?} ON true", "SELECT * FROM a, {?}"):
        t, d = rel(sql)
        assert d, sql
    t, d = rel("SELECT 1 FROM {?} WHERE x")
    assert t == []


def test_h_lowercase_sql_and_multiline():
    t, d = rel("select a\n  from\n   first_t f\n  join\n   second_t s on s.id = f.id")
    assert t == ["first_t", "second_t"]


# ═════════════════════════════ (h) the reads scan over a writer tree ═════════════════════════════

def _side(monkeypatch, tmp_path, body, extra=None):
    files = {"pipeline/orchestrator/writers/ka_up.py": _HDR + body}
    files.update(extra or {})
    return w3._sidecar(monkeypatch, tmp_path, files)


def test_h_scan_finds_the_reads_of_the_registered_class_with_file_and_line(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        ctx.db_conn.execute("SELECT x FROM bg_up WHERE chart_id = %s", (1,))\n'
          '        ctx.db_conn.execute("INSERT INTO kala_up (x) VALUES (1)")\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_up"], s
    (rel_, line, via), = s["reads"]["bg_up"]
    assert rel_ == "ka_up.py" and line == 5 and via == ""
    assert s["incomplete"] == [], s


def test_h_scan_follows_first_party_delegation_and_names_the_chain(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          'from helpers.loader import load_rows\n'
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        load_rows(ctx.db_conn)\n',
          {"helpers/__init__.py": "", "helpers/loader.py":
           'def load_rows(conn):\n    return conn.execute("SELECT x FROM bg_deep").fetchall()\n'})
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_deep"] and s["reads"]["bg_deep"][0][0] == "helpers/loader.py", s
    assert "ka_up.py" in s["reads"]["bg_deep"][0][2], "the delegation chain is named"
    assert s["incomplete"] == [], s


def test_h_scan_reads_only_the_registered_class_not_a_sibling_asset_in_the_same_module(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        ctx.db_conn.execute("SELECT 1 FROM mine_t")\n'
          '@register("ka_other")\nclass KaOther(WriterBase):\n    def run(self, ctx):\n        ctx.db_conn.execute("SELECT 1 FROM theirs_t")\n')
    assert list(ac.reads_scan("ka_up", ["ka_up.py"])["reads"]) == ["mine_t"]


def test_h_scan_marks_a_dynamic_table_incomplete_with_its_location(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx, table):\n'
          '        ctx.db_conn.execute(f"SELECT 1 FROM {table} WHERE true")\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] and "ka_up.py:5" in s["incomplete"][0] and "dynamic" in s["incomplete"][0], s


def test_h_scan_resolves_a_table_from_a_module_constant_or_loop_sequence(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          'SRC = "bg_const"\n'
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        ctx.db_conn.execute(f"SELECT 1 FROM {SRC}")\n'
          '        for t in ("bg_a", "bg_b"):\n            ctx.db_conn.execute(f"SELECT 1 FROM {t}")\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert sorted(s["reads"]) == ["bg_a", "bg_b", "bg_const"] and s["incomplete"] == [], s


def test_h_scan_marks_a_non_literal_execute_argument_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        sql = build_sql(ctx)\n        ctx.db_conn.execute(sql)\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] and "ka_up.py:6" in s["incomplete"][0], s


def test_h_scan_follows_a_parameter_forwarded_sql_to_its_literal_callers(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          'def _q(conn, sql):\n    return conn.execute(sql).fetchall()\n'
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        _q(ctx.db_conn, "SELECT 1 FROM bg_fwd")\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_fwd"] and s["incomplete"] == [], s


def test_h_scan_a_parameter_forwarded_sql_with_a_non_literal_caller_is_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          'def _q(conn, sql):\n    return conn.execute(sql).fetchall()\n'
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        _q(ctx.db_conn, pick(ctx))\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_h_scan_a_parameter_forwarded_sql_with_no_caller_in_scope_is_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          'class Base:\n    pass\n'
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        self._go(ctx.db_conn, ctx.config["sql"])\n'
          '    def _go(self, conn, sql):\n        conn.execute(sql)\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_h_scan_a_class_constant_sql_is_resolved(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    _SQL = "SELECT 1 FROM bg_cls"\n'
          '    def run(self, ctx):\n        ctx.db_conn.execute(self._SQL)\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_cls"] and s["incomplete"] == [], s


def test_h_scan_sql_one_hop_past_the_frontier_makes_the_parse_incomplete(monkeypatch, tmp_path):
    extra = {}
    for i in range(1, 5):
        if i < 4:
            extra[f"m{i}.py"] = f"from m{i + 1} import f{i + 1}\ndef f{i}(c):\n    return f{i + 1}(c)\n"
        else:
            extra[f"m{i}.py"] = 'def f4(c):\n    return c.execute("SELECT 1 FROM bg_far")\n'
    _side(monkeypatch, tmp_path,
          'from m1 import f1\n@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        f1(ctx.db_conn)\n', extra)
    far = ac.reads_scan("ka_up", ["ka_up.py"])
    assert "bg_far" not in far["reads"], "m4's read is hop 4: beyond the scan"
    assert far["incomplete"] and any("hop" in r for r in far["incomplete"]), far
    # the same read inside the hop limit is found and the parse is complete
    _side(monkeypatch, tmp_path / "b",
          'from m1 import f1\n@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        f1(ctx.db_conn)\n',
          {"m1.py": 'def f1(c):\n    return c.execute("SELECT 1 FROM bg_near")\n'})
    near = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(near["reads"]) == ["bg_near"] and near["incomplete"] == []


def test_h_scan_a_writer_with_no_registered_class_is_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'class Plain:\n    def run(self):\n        pass\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] and "no class registered" in s["incomplete"][0], s


def test_h_scan_prose_that_mentions_from_is_not_sql(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        raise ValueError("cannot read rows from the upstream table")\n'
          '        log("copy from {?} to")\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["reads"] == {} and s["incomplete"] == [], s


# ═════════════════════════════ (h) Build.dag in measure() ═════════════════════════════

WRITER_READING = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
                  '        ctx.db_conn.execute("SELECT x FROM up_t WHERE chart_id = %s", (1,))\n')
WRITER_SILENT = '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        return 1\n'


def _dag(monkeypatch, tmp_path, body, depends_on=(), owners=None, graph=None, extra_rows=None, extra_files=None,
         has_writer=True, registered=True):
    _side(monkeypatch, tmp_path, body, extra_files)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=has_writer, count_sql="SELECT count(*) FROM kala_up",
                                depends_on=depends_on),
           "bg_up": pa._reg_row("bg_up", "up_t", has_writer=True), "bg_other": pa._reg_row("bg_other", "other_t", has_writer=True)}
    reg.update(extra_rows or {})
    pa._stub_layer(monkeypatch, tmp_path, reg, registered=({"ka_up": ["ka_up.py"]} if registered else {}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners",
                        lambda: dict(owners if owners is not None else {"up_t": ["bg_up"], "kala_up": ["ka_up"]}), raising=False)
    if graph is not None:
        monkeypatch.setattr(ac, "dependency_graph", lambda: dict(graph))
    c = ac.measure("L0")
    return next(a for a in c["assets"] if a["asset_id"] == "ka_up")["measurements"]["Build.dag"]


def test_h_an_undeclared_read_of_another_assets_table_is_a_fail_naming_the_missing_edge(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_READING, depends_on=(), owners={"up_t": ["bg_up"]})
    assert rec["v"] == ac.FAIL, rec
    assert "missing depends_on edge" in rec["measured"] and "ka_up -> bg_up" in rec["measured"], rec
    assert "up_t" in rec["measured"] and "ka_up.py:5" in rec["measured"], rec
    assert rec["missing_edges"] == [dict(asset="ka_up", needs="bg_up", table="up_t", file="ka_up.py", line=5,
                                         via="", transitive_via=[], kind="missing_edge", cycle_tested=True)], rec


def test_h_a_read_of_the_table_of_an_asset_registered_on_the_same_writer_class_needs_no_edge(monkeypatch, tmp_path):
    # bg_transit_engine and bg_transit_rules are one class registered twice: one writer, not a dependency
    body = WRITER_READING.replace('@register("ka_up")', '@register("bg_up")\n@register("ka_up")')
    rec = _dag(monkeypatch, tmp_path, body, owners={"up_t": ["bg_up"]})
    assert rec["v"] == ac.PASS, rec
    assert ac.reads_scan("ka_up", ["ka_up.py"])["co_registered"] == ["bg_up"]


def test_h_a_declared_edge_makes_the_read_covered_and_the_parse_complete_passes(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_READING, depends_on=("bg_up",), owners={"up_t": ["bg_up"]})
    assert rec["v"] == ac.PASS, rec
    assert rec["measured"].startswith("1 declared edge(s); exists: "), rec
    assert "missing_edges" not in rec


def test_h_reading_your_own_table_needs_no_edge(monkeypatch, tmp_path):
    body = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
            '        ctx.db_conn.execute("SELECT count(*) FROM kala_up")\n')
    rec = _dag(monkeypatch, tmp_path, body, owners={"kala_up": ["ka_up"]})
    assert rec["v"] == ac.PASS, rec


def test_h_a_table_no_asset_produces_needs_no_edge(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_READING, owners={"something_else": ["bg_up"]})
    assert rec["v"] == ac.PASS, rec


def test_h_a_shared_table_is_covered_by_any_of_its_producers_and_otherwise_names_all_of_them(monkeypatch, tmp_path):
    shared = {"up_t": ["bg_other", "bg_up"]}
    assert _dag(monkeypatch, tmp_path, WRITER_READING, depends_on=("bg_other",), owners=shared)["v"] == ac.PASS
    rec = _dag(monkeypatch, tmp_path / "x", WRITER_READING, depends_on=(), owners=shared)
    assert rec["v"] == ac.FAIL and "bg_other" in rec["measured"] and "bg_up" in rec["measured"], rec


def test_h_only_a_direct_edge_counts_a_transitive_ancestor_is_named_but_still_fails(monkeypatch, tmp_path):
    rows = {"mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("bg_up",))}
    rec = _dag(monkeypatch, tmp_path, WRITER_READING, depends_on=("mid",), owners={"up_t": ["bg_up"]},
               graph={"ka_up": ["mid"], "mid": ["bg_up"], "bg_up": [], "bg_other": []}, extra_rows=rows)
    assert rec["v"] == ac.FAIL, rec
    assert rec["missing_edges"][0]["transitive_via"] == ["mid"], rec
    assert "transitively" in rec["measured"], rec


def test_h_an_incomplete_parse_with_no_undeclared_read_is_no_detector_never_pass(monkeypatch, tmp_path):
    body = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx, table):\n'
            '        ctx.db_conn.execute(f"SELECT 1 FROM {table}")\n')
    rec = _dag(monkeypatch, tmp_path, body)
    assert rec["v"] == ac.NO_DET, rec
    assert "not established" in rec["measured"] and "ka_up.py:5" in rec["measured"], rec


def test_h_an_undeclared_read_is_a_fail_even_when_the_parse_is_incomplete(monkeypatch, tmp_path):
    body = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx, table):\n'
            '        ctx.db_conn.execute("SELECT x FROM up_tbl")\n        ctx.db_conn.execute(f"SELECT 1 FROM {table}")\n')
    rec = _dag(monkeypatch, tmp_path, body, owners={"up_tbl": ["bg_up"]})
    assert rec["v"] == ac.FAIL and "ka_up -> bg_up" in rec["measured"], rec


def test_h_a_complete_parse_that_reads_nothing_upstream_passes_and_says_what_it_scanned(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_SILENT)
    assert rec["v"] == ac.PASS and "0 read(s)" in rec["measured"] and "static scan" in rec["measured"], rec


def test_h_an_unresolvable_depends_on_is_still_a_fail_as_before(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_SILENT, depends_on=("bg_ghost",))
    assert rec["v"] == ac.FAIL and "unknown or inactive" in rec["measured"] and "bg_ghost" in rec["measured"], rec


def test_h_a_writerless_asset_with_no_declared_edges_passes_and_with_declared_edges_is_no_detector(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_SILENT, has_writer=False, registered=False)
    assert rec["v"] == ac.PASS and "no writer" in rec["measured"], rec
    rec = _dag(monkeypatch, tmp_path / "e", WRITER_SILENT, depends_on=("bg_up",), has_writer=False, registered=False)
    assert rec["v"] == ac.NO_DET and "no writer" in rec["measured"], rec


def test_h_a_writer_the_registry_claims_but_no_file_is_found_is_no_detector(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, WRITER_SILENT, has_writer=True, registered=False)
    assert rec["v"] == ac.NO_DET, rec


def test_h_unreadable_ownership_is_errored_not_pass(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, WRITER_READING)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up")}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})

    def boom():
        raise ac.Unknown("relation gone")
    monkeypatch.setattr(ac, "produced_table_owners", boom, raising=False)
    rec = ac.measure("L0")["assets"][0]["measurements"]["Build.dag"]
    assert rec["v"] == ac.ERRORED and "ownership" in rec["measured"], rec


def test_h_a_scan_that_raises_degrades_only_this_check_to_errored(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, WRITER_SILENT)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up")}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners", lambda: {}, raising=False)
    monkeypatch.setattr(ac, "reads_scan", lambda *a, **k: (_ for _ in ()).throw(ac.Unknown("unparseable")))
    a = ac.measure("L0")["assets"][0]["measurements"]
    assert a["Build.dag"]["v"] == ac.ERRORED and "unparseable" in a["Build.dag"]["measured"], a["Build.dag"]
    assert a["Build.registered"]["v"] != ac.ERRORED, "the layer and the other checks are untouched"


def test_h_the_ownership_map_is_read_once_per_measure_and_only_when_a_read_needs_it(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, WRITER_READING)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up"),
           "ka_two": pa._reg_row("ka_two", "kala_two", has_writer=True, count_sql="SELECT count(*) FROM kala_two")}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"], "ka_two": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    calls = []
    monkeypatch.setattr(ac, "produced_table_owners", lambda: calls.append(1) or {"bg_up": ["bg_x"]}, raising=False)
    ac.measure("L0")
    assert len(calls) <= 1, calls


def test_h_produced_table_owners_unions_target_and_count_sql_tables():
    rows = [("a", "t_a", "SELECT count(*) FROM t_a"), ("m", None, "SELECT (SELECT count(*) FROM t_1) + (SELECT count(*) FROM t_2)"),
            ("b", "t_a", ""), ("v", "vw_v", "SELECT count(*) FROM vw_v WHERE chart_id=$1")]
    got = ac.build_table_owners(rows)
    assert got == {"t_a": ["a", "b"], "t_1": ["m"], "t_2": ["m"], "vw_v": ["v"]}, got


def test_h_an_asset_with_no_writer_produces_nothing_a_build_waits_for_so_its_table_is_never_a_missing_edge():
    # an edge to a writer-less asset could never reach `lit` (T4 check 9): a permanent DEP-ASSERT trap
    got = ac.build_table_owners([("lel_events", "life_events", "SELECT count(*) FROM life_events", False),
                                 ("w", "t_w", "", True)])
    assert got == {"t_w": ["w"]}, got


def test_h_a_read_of_a_writerless_assets_table_needs_no_edge(monkeypatch, tmp_path):
    body = WRITER_READING.replace("up_t", "life_events")
    rec = _dag(monkeypatch, tmp_path, body, owners=ac.build_table_owners([("lel_events", "life_events", "", False)]))
    assert rec["v"] == ac.PASS, rec


# ───────── tests added after the first mutation run (survivors) ─────────

def test_g_a_kind_outside_the_declared_enum_is_not_a_declared_service(monkeypatch, tmp_path):
    rec = _target(monkeypatch, tmp_path, pa._reg_row("svc", asset_kind="service", has_writer=True), {"svc": _decl("bogus")})
    assert rec["v"] == NA, rec
    assert ac._declared_kind({"x": _decl("bogus")}, "x") is None and ac._declared_kind({"x": _decl("service")}, "x") == "service"


def test_h_a_placeholder_right_after_a_relation_may_hide_a_join_and_is_reported():
    for sql in ("SELECT 1 FROM a {?} WHERE x", "SELECT 1 FROM a x %s"):
        t, d = ac.sql_relations(sql)
        assert d and "placeholder" in d[0], (sql, d)
    assert ac.sql_relations("SELECT 1 FROM a x WHERE x = %s")[1] == []


def test_h_scan_a_name_that_is_not_a_parameter_a_local_literal_or_a_module_constant_is_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
          '        for sql in load_statements():\n            ctx.db_conn.execute(sql)\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_h_scan_a_forwarding_function_nobody_in_scope_calls_is_incomplete(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path,
          '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        return 1\n'
          '    def _go(self, conn, sql):\n        conn.execute(sql)\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] and "ka_up.py:7" in s["incomplete"][0], s


def test_h_a_partition_writer_that_shares_the_table_and_an_own_count_table_need_no_edge(monkeypatch, tmp_path):
    # shared: ka_up is itself one of the table's producers (ga_strength -> chart_facts)
    rec = _dag(monkeypatch, tmp_path, WRITER_READING, owners={"up_t": ["bg_other", "ka_up"]})
    assert rec["v"] == ac.PASS, rec
    # own: the table is named by this asset's own count_sql even if the ownership map credits someone else
    body = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
            '        ctx.db_conn.execute("SELECT count(*) FROM kala_up")\n')
    rec = _dag(monkeypatch, tmp_path / "own", body, owners={"kala_up": ["bg_other"]})
    assert rec["v"] == ac.PASS, rec


# ═════════════════════════════ registry revision and fingerprint ═════════════════════════════

def test_the_criteria_whose_behaviour_changed_carry_a_bumped_revision():
    assert ac.CRITERION_REGISTRY["Build.target"]["revision"] == 2
    assert ac.CRITERION_REGISTRY["Build.dag"]["revision"] == 2
    assert ac.CRITERION_REGISTRY["Idem.pattern"]["revision"] == 3        # 3: N-150 R5 (pin 26) re-worded and bumped it
    assert ac.REGISTRY_REVISION >= 6     # 7: E6 item (f) bumped it (NA_CAUSES only); 9 declares the approved rules
