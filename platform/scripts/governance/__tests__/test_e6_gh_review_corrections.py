"""test_e6_gh_review_corrections.py — corrections to E6 items (g)/(h) after the independent review of b24e580cc.

(1) back-reads: a read of a DOWNSTREAM asset's product (declaring the missing edge would close a cycle in the
    registry graph) is still a FAIL, but it is not a "missing depends_on edge": it carries its own kind and text, and
    the cycle test is computed from the declared graph plus the candidate edge, never hard-coded;
(2) Build.dag states exactly what it checked: every depends_on id is an ACTIVE registry asset (every layer, not only the
    layer's prefix), the asset is on no dependency cycle (reported), and the reads-match clause; a clause that cannot be
    measured from the data is NO_DETECTOR, never a silent PASS;
(3) `transitive_only` flag on the record and in the rollup reason;
(4) incomplete parse: PARTIAL when at least one read resolved and every resolved read is covered, NO_DETECTOR when
    nothing resolved (default pending SS);
(5) false negatives closed (a `--` inside a string literal, a non-literal SQL argument to a read_sql/exec_sql-style
    call, USING / MERGE USING relations);
(7) mutants the review found alive;
(8) the declaration basis travels into the Build.target gate cell.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as pa  # noqa: E402
import test_e6_gh_declared_service_and_reads_match as g  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

_HDR = w3._HDR


def _writer(*lines):
    return ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
            + "".join(f"        {ln}\n" for ln in lines))


READ = 'ctx.db_conn.execute("SELECT x FROM down_t")'


# ═════════════════════════ (1) back-reads: an edge would close a cycle ═════════════════════════

def _down_rows():
    return {"down": pa._reg_row("down", "down_t", has_writer=True), "mid": pa._reg_row("mid", "mid_t", has_writer=True)}


def test_a_read_of_a_downstream_assets_product_is_a_back_read_not_a_missing_edge(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _writer(READ), owners={"down_t": ["down"]}, extra_rows=_down_rows(),
                 graph={"ka_up": [], "down": ["ka_up"], "mid": [], "bg_up": [], "bg_other": []})
    assert rec["v"] == ac.FAIL, rec
    txt = rec["measured"]
    assert "back-read" in txt and "would create a cycle" in txt and "down_t" in txt and "ka_up.py:5" in txt, txt
    assert "missing depends_on edge" not in txt, "declaring this edge would close a cycle: it is not a missing edge"
    f, = rec["missing_edges"]
    assert f["kind"] == "back_read" and f["needs"] == "down" and f["cycle_path"] == ["down", "ka_up"], rec
    assert not rec.get("transitive_only")


def test_the_cycle_test_follows_transitive_depends_on_chains(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _writer(READ), owners={"down_t": ["down"]}, extra_rows=_down_rows(),
                 graph={"ka_up": [], "down": ["mid"], "mid": ["ka_up"], "bg_up": [], "bg_other": []})
    f, = rec["missing_edges"]
    assert f["kind"] == "back_read" and f["cycle_path"] == ["down", "mid", "ka_up"], rec


def test_the_same_read_is_a_missing_edge_when_the_graph_would_stay_acyclic(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _writer(READ), owners={"down_t": ["down"]}, extra_rows=_down_rows(),
                 graph={"ka_up": [], "down": [], "mid": [], "bg_up": [], "bg_other": []})
    f, = rec["missing_edges"]
    assert f["kind"] == "missing_edge" and "missing depends_on edge" in rec["measured"] and "back-read" not in rec["measured"], rec


def test_a_shared_table_names_only_the_producers_an_edge_to_which_would_stay_acyclic(monkeypatch, tmp_path):
    rows = _down_rows()
    rec = g._dag(monkeypatch, tmp_path, _writer(READ), owners={"down_t": ["down", "mid"]}, extra_rows=rows,
                 graph={"ka_up": [], "down": ["ka_up"], "mid": [], "bg_up": [], "bg_other": []})
    f, = rec["missing_edges"]
    assert f["kind"] == "missing_edge" and f["needs"] == "mid", rec


def test_a_back_read_and_a_missing_edge_are_both_reported_with_their_own_text(monkeypatch, tmp_path):
    body = _writer(READ, 'ctx.db_conn.execute("SELECT 1 FROM mid_t")')
    rec = g._dag(monkeypatch, tmp_path, body, owners={"down_t": ["down"], "mid_t": ["mid"]}, extra_rows=_down_rows(),
                 graph={"ka_up": [], "down": ["ka_up"], "mid": [], "bg_up": [], "bg_other": []})
    kinds = sorted(f["kind"] for f in rec["missing_edges"])
    assert kinds == ["back_read", "missing_edge"], rec
    assert "back-read" in rec["measured"] and "missing depends_on edge" in rec["measured"], rec


# ═════════════════════════ (2) Build.dag states what it checked ═════════════════════════

def test_an_unknown_dependency_in_another_layer_fails(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("zz_missing",))
    assert rec["v"] == ac.FAIL and "zz_missing" in rec["measured"] and "unknown or inactive" in rec["measured"], rec


def test_a_dependency_on_an_inactive_asset_fails_it_is_not_in_the_active_registry(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("bg_retired",),
                 graph={"ka_up": [], "bg_up": [], "bg_other": []})
    assert rec["v"] == ac.FAIL and "bg_retired" in rec["measured"], rec


def test_a_cross_layer_dependency_that_exists_passes_the_existence_clause(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("ga_other",),
                 graph={"ka_up": [], "bg_up": [], "bg_other": [], "ga_other": []})
    assert rec["v"] == ac.PASS, rec


def test_a_dependency_cycle_through_the_asset_is_a_fail_and_the_cycle_is_reported(monkeypatch, tmp_path):
    rows = {"mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("ka_up",))}
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("mid",), extra_rows=rows,
                 graph={"ka_up": ["mid"], "mid": ["ka_up"], "bg_up": [], "bg_other": []})
    assert rec["v"] == ac.FAIL and "cycle: ka_up -> mid -> ka_up" in rec["measured"], rec


def test_a_self_dependency_is_a_cycle(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("ka_up",),
                 graph={"ka_up": ["ka_up"], "bg_up": [], "bg_other": []})
    assert rec["v"] == ac.FAIL and "cycle: ka_up -> ka_up" in rec["measured"], rec


def test_a_cycle_that_does_not_pass_through_the_asset_is_not_its_failure(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT,
                 graph={"ka_up": [], "bg_up": ["bg_other"], "bg_other": ["bg_up"]})
    assert rec["v"] == ac.PASS, rec


def test_the_pass_text_states_exactly_what_was_checked(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT, depends_on=("bg_up",))
    txt = rec["measured"]
    assert rec["v"] == ac.PASS, rec
    assert "1 declared edge(s)" in txt and "active registry assets (every layer)" in txt, txt
    assert "no dependency cycle" in txt and "reads-match:" in txt and "views and DB functions are not followed" in txt, txt


def test_an_unreadable_registry_graph_makes_the_unmeasurable_clauses_no_detector_never_pass(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, g.WRITER_SILENT)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up",
                                depends_on=("ga_other",))}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners", lambda: {}, raising=False)

    def boom():
        raise ac.Unknown("graph read failed")
    monkeypatch.setattr(ac, "dependency_graph", boom)
    rec = ac.measure("L3")["assets"][0]["measurements"]["Build.dag"]
    assert rec["v"] == ac.NO_DET, rec
    assert "ga_other" in rec["measured"] and "cycle" in rec["measured"] and "not measured" in rec["measured"], rec
    # with only same-layer ids the existence clause is still decidable from the layer registry; the cycle clause is not
    reg["ka_up"] = pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up")
    rec = ac.measure("L3")["assets"][0]["measurements"]["Build.dag"]
    assert rec["v"] == ac.NO_DET and "cycle" in rec["measured"] and "not measured" in rec["measured"], rec


def test_an_unknown_dependency_is_still_a_fail_when_the_graph_is_unreadable_for_a_same_layer_prefix(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, g.WRITER_SILENT)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up",
                                depends_on=("ka_ghost",))}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners", lambda: {}, raising=False)
    monkeypatch.setattr(ac, "dependency_graph", lambda: (_ for _ in ()).throw(ac.Unknown("x")))
    rec = ac.measure("L3")["assets"][0]["measurements"]["Build.dag"]
    assert rec["v"] == ac.FAIL and "ka_ghost" in rec["measured"], rec


# ═════════════════════════ (3) transitive_only ═════════════════════════

def test_transitive_only_is_flagged_on_the_record_and_in_the_rollup_reason(monkeypatch, tmp_path):
    rows = {"mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("bg_up",))}
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_READING, depends_on=("mid",), owners={"up_t": ["bg_up"]},
                 graph={"ka_up": ["mid"], "mid": ["bg_up"], "bg_up": [], "bg_other": []}, extra_rows=rows)
    assert rec["v"] == ac.FAIL and rec["transitive_only"] is True, rec
    c = ac._check_contribution("Build.dag", "L3", rec, None)
    assert c["v"] == ac.FAIL and "transitive" in c["reason"], c
    rec2 = g._dag(monkeypatch, tmp_path / "n", g.WRITER_READING, owners={"up_t": ["bg_up"]})
    assert rec2["v"] == ac.FAIL and rec2["transitive_only"] is False, rec2
    assert "transitive" not in ac._check_contribution("Build.dag", "L3", rec2, None)["reason"]


def test_a_passing_or_unrelated_record_carries_no_transitive_only_flag(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, g.WRITER_SILENT)
    assert "transitive_only" not in rec


# ═════════════════════════ (4) incomplete parse: PARTIAL vs NO_DETECTOR (default pending SS) ═════════════════════════

DYN = 'ctx.db_conn.execute(f"SELECT 1 FROM {table}")'


def test_an_incomplete_parse_with_resolved_covered_reads_is_partial_naming_the_reason(monkeypatch, tmp_path):
    body = _writer('ctx.db_conn.execute("SELECT x FROM up_t")', DYN).replace("def run(self, ctx)", "def run(self, ctx, table)")
    rec = g._dag(monkeypatch, tmp_path, body, depends_on=("bg_up",), owners={"up_t": ["bg_up"]})
    assert rec["v"] == ac.PARTIAL, rec
    assert "1 resolved read(s)" in rec["measured"] and "ka_up.py:6" in rec["measured"] and "dynamic" in rec["measured"], rec


def test_an_incomplete_parse_with_nothing_resolved_stays_no_detector(monkeypatch, tmp_path):
    body = _writer(DYN).replace("def run(self, ctx)", "def run(self, ctx, table)")
    rec = g._dag(monkeypatch, tmp_path, body)
    assert rec["v"] == ac.NO_DET, rec


def test_an_incomplete_parse_with_an_undeclared_read_is_still_a_fail(monkeypatch, tmp_path):
    body = _writer('ctx.db_conn.execute("SELECT x FROM up_t")', DYN).replace("def run(self, ctx)", "def run(self, ctx, table)")
    rec = g._dag(monkeypatch, tmp_path, body, owners={"up_t": ["bg_up"]})
    assert rec["v"] == ac.FAIL, rec


def test_a_local_pass_through_query_wrapper_passed_to_a_helper_is_traced(monkeypatch, tmp_path):
    body = ('from helpers.arcs import build_arcs\n'
            '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
            '        def query(sql, params=None):\n            return ctx.db_conn.execute(sql, params or []).fetchall()\n'
            '        build_arcs(query)\n')
    s = g._side(monkeypatch, tmp_path, body, {"helpers/__init__.py": "", "helpers/arcs.py":
                'def build_arcs(query):\n    return query("SELECT x FROM bg_arcs")\n'})
    scan = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(scan["reads"]) == ["bg_arcs"] and scan["incomplete"] == [], scan


# ═════════════════════════ (5) false negatives ═════════════════════════

def test_a_double_dash_inside_a_string_literal_is_not_a_comment():
    assert ac.sql_relations("SELECT '--' AS c FROM t")[0] == ["t"]
    assert ac.sql_relations("SELECT 'a--b', x FROM t JOIN u ON u.id = t.id")[0] == ["t", "u"]


def test_an_apostrophe_inside_a_comment_does_not_swallow_the_sql():
    assert ac.sql_relations("-- don't read this\nSELECT 1 FROM t")[0] == ["t"]
    assert ac.sql_relations("/* it's a block */ SELECT 1 FROM t")[0] == ["t"]
    assert ac.sql_relations("SELECT 1 FROM t -- from not_a_table")[0] == ["t"]


@pytest.mark.parametrize("call", ["pd.read_sql(sql, conn)", "pd.read_sql_query(build(ctx), conn)", "helper.exec_sql(conn, stmt)",
                                  "db.execute_sql(make(ctx))", "run_query(conn, q)"])
def test_a_non_literal_sql_argument_to_a_read_sql_style_call_makes_the_parse_incomplete(monkeypatch, tmp_path, call):
    g._side(monkeypatch, tmp_path, _writer("sql = compute(ctx)", "stmt = q = compute(ctx)", call))
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"], (call, s)


def test_a_literal_sql_argument_to_a_read_sql_style_call_is_read_and_complete(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, _writer('pd.read_sql("SELECT x FROM bg_lit", ctx.db_conn)'))
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_lit"] and s["incomplete"] == [], s


def test_using_relations_are_reads_on_the_read_side():
    assert ac.sql_relations("DELETE FROM written_t USING src_t s WHERE written_t.id = s.id")[0] == ["src_t"]
    assert ac.sql_relations("DELETE FROM written_t USING a, b WHERE true")[0] == ["a", "b"]
    assert ac.sql_relations("MERGE INTO tgt_t t USING src_t s ON t.id = s.id WHEN MATCHED THEN DELETE")[0] == ["src_t"]
    assert ac.sql_relations("MERGE INTO tgt_t USING (SELECT id FROM inner_t) s ON true")[0] == ["inner_t"]


def test_join_using_a_column_list_is_not_a_relation():
    assert ac.sql_relations("SELECT 1 FROM a JOIN b USING (id, kind)")[0] == ["a", "b"]


# ═════════════════════════ (7) survivors of the review's mutation run ═════════════════════════

def test_the_cited_location_is_the_first_in_file_order_not_the_last(monkeypatch, tmp_path):
    body = _writer('ctx.db_conn.execute("SELECT x FROM up_t")', 'ctx.db_conn.execute("SELECT y FROM up_t")')
    rec = g._dag(monkeypatch, tmp_path, body, owners={"up_t": ["bg_up"]})
    assert rec["missing_edges"][0]["line"] == 5 and "ka_up.py:5" in rec["measured"] and "ka_up.py:6" not in rec["measured"], rec


def test_the_pass_text_counts_the_covered_reads(monkeypatch, tmp_path):
    body = _writer('ctx.db_conn.execute("SELECT x FROM up_t")', 'ctx.db_conn.execute("SELECT y FROM other_t")')
    rec = g._dag(monkeypatch, tmp_path, body, depends_on=("bg_up", "bg_other"),
                 owners={"up_t": ["bg_up"], "other_t": ["bg_other"]})
    assert rec["v"] == ac.PASS and "reads-match: 2 read(s) of other assets' tables" in rec["measured"], rec


def test_executemany_is_an_execute_call_for_the_literal_trace(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, _writer("ctx.db_conn.executemany(build(ctx), [])"))
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_a_conditional_of_two_literals_is_traced_one_with_a_non_literal_branch_is_not(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, _writer('sql = "SELECT 1 FROM bg_a" if ctx.flag else "SELECT 1 FROM bg_b"',
                                           "ctx.db_conn.execute(sql)"))
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert sorted(s["reads"]) == ["bg_a", "bg_b"] and s["incomplete"] == [], s
    g._side(monkeypatch, tmp_path / "b", _writer('sql = "SELECT 1 FROM bg_a" if ctx.flag else compute(ctx)',
                                                 "ctx.db_conn.execute(sql)"))
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_a_long_incomplete_list_shows_the_first_three_reasons_and_counts_the_rest(monkeypatch, tmp_path):
    lines = [f'ctx.db_conn.execute(f"SELECT 1 FROM {{t{i}}}")' for i in range(5)]
    rec = g._dag(monkeypatch, tmp_path, _writer(*lines))
    assert rec["v"] == ac.NO_DET, rec
    txt = rec["measured"]
    for ln in (5, 6, 7):
        assert f"ka_up.py:{ln}:" in txt, txt
    assert "ka_up.py:8:" not in txt and "+2 more" in txt, txt


# ═════════════════════════ (8) the declaration basis reaches the Build gate cell ═════════════════════════

def test_the_build_gate_cell_carries_the_declaration_basis_of_its_target_check():
    rec = dict(v=ac.PASS, measured="x", basis="declaration")
    cell = ac.rollup_asset("L3", {"Build.target": rec})["Build"]
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.target")
    assert chk["basis"] == "declaration" and "declar" in chk["reason"], chk
    assert cell["declared_checks"] == ["Build.target"], cell
    plain = ac.rollup_asset("L3", {"Build.target": dict(v=ac.PASS, measured="x")})["Build"]
    assert "declared_checks" not in plain and "basis" not in next(c for c in plain["checks"] if c["criterion"] == "Build.target")


# ═════════════════════════ relative imports, imported constants, third-party re-exports ═════════════════════════

def test_a_relative_import_inside_a_package_resolves_against_that_package(monkeypatch, tmp_path):
    body = ('from services.pkg import build\n'
            '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        build(ctx.db_conn)\n')
    g._side(monkeypatch, tmp_path, body, {
        "services/__init__.py": "", "services/pkg/__init__.py": "from .arcs import build\n",
        "services/pkg/arcs.py": 'def build(conn):\n    return conn.execute("SELECT 1 FROM bg_rel")\n'})
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_rel"] and s["incomplete"] == [], s
    # ONE resolver: Idem.pattern's delegation scope resolves the same relative imports (no per-detector split)
    assert [u["rel"] for u in ac._delegation_scope("ka_up", ["ka_up.py"], hops=3)[0]] == ["ka_up.py", "services/pkg/arcs.py"]


def test_an_imported_sql_constant_is_read_and_traced(monkeypatch, tmp_path):
    body = ('from helpers.sql import READ_SQL\n'
            '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        ctx.db_conn.execute(READ_SQL)\n')
    g._side(monkeypatch, tmp_path, body, {"helpers/__init__.py": "", "helpers/sql.py": 'READ_SQL = "SELECT 1 FROM bg_const_t"\n'})
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_const_t"] and s["incomplete"] == [], s


def test_a_third_party_module_re_exported_by_a_shim_is_not_our_sql(monkeypatch, tmp_path):
    body = ('from shim import drik\n'
            '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        return drik.sun(1)\n')
    g._side(monkeypatch, tmp_path, body, {"shim.py": "from jhora.panchanga import drik\n"})
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [], s


# ═════════════════════════ final review: survivors, transitive_only with a back-read, unreadable graph, USING ═════════════════════════

def _many(monkeypatch, tmp_path, body, owners, graph, deps=(), extra_rows=None):
    return g._dag(monkeypatch, tmp_path, body, depends_on=deps, owners=owners, graph=graph, extra_rows=extra_rows)


def test_transitive_only_needs_EVERY_missing_edge_to_be_transitive(monkeypatch, tmp_path):
    body = _writer('ctx.db_conn.execute("SELECT 1 FROM up_t")', 'ctx.db_conn.execute("SELECT 1 FROM other_t")')
    rows = {"mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("bg_up",))}
    rec = _many(monkeypatch, tmp_path, body, {"up_t": ["bg_up"], "other_t": ["bg_other"]},
                {"ka_up": ["mid"], "mid": ["bg_up"], "bg_up": [], "bg_other": []}, deps=("mid",), extra_rows=rows)
    assert sorted(f["transitive_via"] for f in rec["missing_edges"]) == [[], ["mid"]], rec
    assert rec["transitive_only"] is False, rec


def test_a_back_read_present_means_transitive_only_is_false_and_the_rollup_reason_does_not_claim_it(monkeypatch, tmp_path):
    body = _writer(READ, 'ctx.db_conn.execute("SELECT 1 FROM up_t")')
    rows = {**_down_rows(), "mid2": pa._reg_row("mid2", "mid2_t", has_writer=True, depends_on=("bg_up",))}
    rec = _many(monkeypatch, tmp_path, body, {"down_t": ["down"], "up_t": ["bg_up"]},
                {"ka_up": ["mid2"], "mid2": ["bg_up"], "down": ["ka_up"], "mid": [], "bg_up": [], "bg_other": []},
                deps=("mid2",), extra_rows=rows)
    kinds = sorted(f["kind"] for f in rec["missing_edges"])
    assert kinds == ["back_read", "missing_edge"] and rec["transitive_only"] is False, rec
    assert "transitive" not in ac._check_contribution("Build.dag", "L3", rec, None)["reason"]


def test_the_cycle_path_is_the_first_producers_chain(monkeypatch, tmp_path):
    rows = {"down_a": pa._reg_row("down_a", "da_t", has_writer=True), "down_b": pa._reg_row("down_b", "db_t", has_writer=True),
            "mid": pa._reg_row("mid", "mid_t", has_writer=True)}
    rec = _many(monkeypatch, tmp_path, _writer(READ), {"down_t": ["down_a", "down_b"]},
                {"ka_up": [], "down_a": ["ka_up"], "down_b": ["mid"], "mid": ["ka_up"], "bg_up": [], "bg_other": []},
                extra_rows=rows)
    f, = rec["missing_edges"]
    assert f["kind"] == "back_read" and f["needs"] == "down_a | down_b" and f["cycle_path"] == ["down_a", "ka_up"], f


def test_transitive_via_considers_only_the_producers_an_edge_to_which_would_stay_acyclic(monkeypatch, tmp_path):
    # a graph that is already cyclic: ka_up -> x -> down -> ka_up. `down` is not a viable producer; `mid2` is.
    rows = {"x": pa._reg_row("x", "x_t", has_writer=True), "down": pa._reg_row("down", "down_t", has_writer=True),
            "mid2": pa._reg_row("mid2", "mid2_t", has_writer=True)}
    rec = _many(monkeypatch, tmp_path, _writer(READ), {"down_t": ["down", "mid2"]},
                {"ka_up": ["x"], "x": ["down"], "down": ["ka_up"], "mid2": [], "bg_up": [], "bg_other": []}, deps=("x",), extra_rows=rows)
    f, = rec["missing_edges"]
    assert f["kind"] == "missing_edge" and f["needs"] == "mid2" and f["transitive_via"] == [], f


def test_the_assets_own_depends_on_overrides_a_stale_graph_entry(monkeypatch, tmp_path):
    # the registry graph says ka_up has no edges; the asset's own row says mid, and mid depends on ka_up: a cycle
    rows = {"mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("ka_up",))}
    rec = _many(monkeypatch, tmp_path, g.WRITER_SILENT, None, {"ka_up": [], "mid": ["ka_up"], "bg_up": [], "bg_other": []},
                deps=("mid",), extra_rows=rows)
    assert rec["v"] == ac.FAIL and "cycle: ka_up -> mid -> ka_up" in rec["measured"], rec


def _unreadable_graph(monkeypatch, tmp_path, body, deps=(), owners=None):
    g._side(monkeypatch, tmp_path, body)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up", depends_on=deps),
           "down": pa._reg_row("down", "down_t", has_writer=True)}
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners", lambda: dict(owners or {}), raising=False)
    monkeypatch.setattr(ac, "dependency_graph", lambda: (_ for _ in ()).throw(ac.Unknown("graph read failed")))
    return ac.measure("L3")["assets"][0]["measurements"]["Build.dag"]


def test_an_unreadable_graph_says_the_cross_layer_ids_were_not_checked(monkeypatch, tmp_path):
    rec = _unreadable_graph(monkeypatch, tmp_path, g.WRITER_SILENT, deps=("ga_other",))
    assert "exists: cross-layer id(s) ['ga_other'] not checked" in rec["measured"], rec


def test_an_unreadable_graph_keeps_missing_edge_but_says_the_cycle_test_did_not_run(monkeypatch, tmp_path):
    rec = _unreadable_graph(monkeypatch, tmp_path, _writer(READ), owners={"down_t": ["down"]})
    assert rec["v"] == ac.FAIL, rec
    f, = rec["missing_edges"]
    assert f["kind"] == "missing_edge" and f["cycle_tested"] is False, f
    assert "cycle test did not run" in rec["measured"], rec
    ok = _unreadable_graph(monkeypatch, tmp_path / "ok", g.WRITER_SILENT)
    assert "cycle_tested" not in ok


def test_a_readable_graph_marks_findings_cycle_tested(monkeypatch, tmp_path):
    rec = _many(monkeypatch, tmp_path, _writer(READ), {"down_t": ["down"]}, {"ka_up": [], "down": [], "mid": [], "bg_up": [], "bg_other": []},
                extra_rows=_down_rows())
    assert rec["missing_edges"][0]["cycle_tested"] is True and "cycle test did not run" not in rec["measured"], rec


def test_every_positional_argument_of_a_read_sql_style_call_is_considered(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, _writer('helper.exec_sql(ctx.db_conn, "SELECT x FROM bg_second")'))
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_second"] and s["incomplete"] == [], s


def test_a_keyword_sql_argument_counts_too(monkeypatch, tmp_path):
    g._side(monkeypatch, tmp_path, _writer('pd.read_sql(con=ctx.db_conn, sql="SELECT x FROM bg_kw")'))
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [], s


def test_a_level_two_relative_import_resolves_against_the_grandparent_package(monkeypatch, tmp_path):
    body = ('from services.pkg.sub import go\n'
            '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        go(ctx.db_conn)\n')
    g._side(monkeypatch, tmp_path, body, {
        "services/__init__.py": "", "services/pkg/__init__.py": "", "services/pkg/sub/__init__.py": "",
        "services/pkg/sub/m.py": "", "services/pkg/helper.py": 'def f(conn):\n    return conn.execute("SELECT 1 FROM bg_l2")\n'})
    (tmp_path / "python-sidecar/services/pkg/sub/__init__.py").write_text("from ..helper import f as go\n")
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert list(s["reads"]) == ["bg_l2"] and s["incomplete"] == [], s


def test_a_constant_beyond_the_hop_limit_is_not_read_but_makes_the_parse_incomplete(monkeypatch, tmp_path):
    extra = {"m1.py": "from m2 import f2\ndef f1(c):\n    return f2(c)\n",
             "m2.py": "from m3 import f3\ndef f2(c):\n    return f3(c)\n",
             "m3.py": "from consts import FAR_SQL\ndef f3(c):\n    return c.execute(FAR_SQL)\n",
             "consts.py": 'FAR_SQL = "SELECT 1 FROM bg_far_const"\n'}
    g._side(monkeypatch, tmp_path, 'from m1 import f1\n@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        f1(ctx.db_conn)\n', extra)
    far = ac.reads_scan("ka_up", ["ka_up.py"], hops=3)
    assert "bg_far_const" not in far["reads"], far
    assert far["incomplete"] and any("hop" in r for r in far["incomplete"]), far
    near = ac.reads_scan("ka_up", ["ka_up.py"], hops=4)
    assert list(near["reads"]) == ["bg_far_const"] and near["incomplete"] == [], near


def test_the_frontier_follows_relative_imports_too(monkeypatch, tmp_path):
    extra = {"services/__init__.py": "", "services/p/__init__.py": "from .m1 import f1\n",
             "services/p/m1.py": "from .m2 import f2\ndef f1(c):\n    return f2(c)\n",
             "services/p/m2.py": "from .m3 import f3\ndef f2(c):\n    return f3(c)\n",
             "services/p/m3.py": "from .m4 import f4\ndef f3(c):\n    return f4(c)\n",
             "services/p/m4.py": 'def f4(c):\n    return c.execute("SELECT 1 FROM bg_far_rel")\n'}
    g._side(monkeypatch, tmp_path, 'from services.p import f1\n@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n        f1(ctx.db_conn)\n', extra)
    s = ac.reads_scan("ka_up", ["ka_up.py"], hops=3)
    assert "bg_far_rel" not in s["reads"] and s["incomplete"] and "services/p/m4.py" in s["incomplete"][0], s


@pytest.mark.parametrize("sql", ["ALTER TABLE t ALTER COLUMN c TYPE bigint USING c::bigint",
                                 "EXECUTE stmt USING p1, p2",
                                 "CREATE INDEX i ON t USING gin (c)"])
def test_using_that_is_not_a_relation_clause_yields_no_relation(sql):
    assert ac.sql_relations(sql) == ([], [])


def test_using_inside_a_later_statement_is_not_confused_with_an_earlier_delete():
    assert ac.sql_relations("DELETE FROM a WHERE true; ALTER TABLE t ALTER COLUMN c TYPE int USING c::int")[0] == []
    assert ac.sql_relations("DELETE FROM a USING b WHERE a.id = b.id; SELECT 1 FROM z")[0] == ["b", "z"]
