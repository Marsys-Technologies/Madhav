"""test_e5_7_build_completion_produced_set.py: Build.completion revision 4, the DECLARED produced-table set (N-150).

An asset that declares `produced_tables` is compared against that declared set instead of its count_sql: each declared table is counted read-only (chart-scoped where it
carries chart_id, a declared filter as AND "column" = 'value'), a declared table the writer scan shows is only UPDATEd is excluded, PASS needs rows_written = the SUM, a
different sum FAILs, an undeclared extra table the writer writes FAILs, an unread writer scope caps PASS at PARTIAL. A declaration, never a tolerance: with none the asset
reads exactly as before. Real fixture: the committed rev-25 L1 census, where ga_dashas reads FAIL (rows_written 483,856 against count_sql 483,855, the 1 being the
dasha_scope_cap sentinel fact in chart_facts). Offline: psql / scalar / the writer scan are faked; no database.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_n99_build_completion_integrity as n99  # noqa: E402  (the offline measure() harness)

REPO = HERE.parents[3]
L1_FILE = REPO / "00_ARCHITECTURE" / "control" / "census" / "asset_census_2026-10-04T194909+0530.json"
L2_FILE = REPO / "00_ARCHITECTURE" / "control" / "census" / "asset_census_2026-10-04T195251+0530.json"
CHART = ac.CHART_ID
DASHA = [dict(table="chart_dashas"), dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"))]
DASHA_COUNTS = {"chart_dashas": 483855, "chart_facts": 1}


class World:
    """Fakes the three reads the clause makes and records every SQL string it sends."""

    def __init__(self, counts, scoped=("chart_dashas", "chart_facts"), written=(), update_only=(), complete=True):
        self.counts, self.scoped, self.sql = dict(counts), set(scoped), []
        self.written, self.update_only, self.complete = list(written), list(update_only), complete

    def psql(self, sql, *a, **k):
        if "information_schema.columns" not in sql:
            return []                                                              # any other read of the (stubbed) measure() path
        self.sql.append(sql)
        return [[t] for t in self.scoped if f"'{t}'" in sql]

    def scalar(self, sql, *a, **k):
        m = re.search(r'^SELECT count\(\*\)::text FROM "(\w+)"', sql)
        if m is None:
            return None
        self.sql.append(sql)
        t = m.group(1)
        return None if self.counts.get(t) is None else str(self.counts[t])

    def scan(self, aid, files):
        return dict(written=self.written, update_only=self.update_only, complete=self.complete)


def run(monkeypatch, tmp_path, world, *, writer_files=True, aid="ga_dashas", decl=DASHA, rw="483856", live=483855, count_sql="SELECT count(*) FROM chart_dashas WHERE chart_id = $1"):
    reg = {aid: dict(n99._reg_row(aid), target_table="chart_dashas", count_sql=count_sql, has_integrity=False, target_floor="1")}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=live, rec=dict(n99._REC, rows_written=rw))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {CHART: dict(n99._REC, rows_written=rw)}})      # a chart-scoped count_sql reads the chart-scoped build record
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {aid: dict(kind="data", **({"produced_tables": decl} if decl else {}))})
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {aid: [f"{aid}.py"]} if writer_files else {})
    monkeypatch.setattr(ac, "idem_scan", lambda *x, **k: ("PASS", ["stub"]))          # a recognised writer file would otherwise start the real scans
    monkeypatch.setattr(ac, "contract_scan", lambda *x, **k: ("PASS", []))
    monkeypatch.setattr(ac, "psql", world.psql)
    monkeypatch.setattr(ac, "scalar", world.scalar)
    monkeypatch.setattr(ac, "produced_set_written", world.scan)
    return n99._cell(ac.measure("L1"), aid)


# ───────────────────────── the real fixture: today's ga_dashas FAIL ─────────────────────────

def test_real_rev25_ga_dashas_reads_fail_on_the_one_row_gap():
    d = json.loads(L1_FILE.read_text(encoding="utf-8"))
    a = next(x for x in d["L1"]["assets"] if x["asset_id"] == "ga_dashas")
    m = a["measurements"]["Build.completion"]
    assert m["v"] == "FAIL" and "rows_written=483856 disagrees with live=483855" in m["measured"] and a["live_rows"] == 483855


def test_declared_set_explains_the_gap_and_passes(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS, written=["chart_dashas", "chart_facts"])
    c = run(monkeypatch, tmp_path, w)
    assert c["v"] == ac.PASS, c
    assert "chart_dashas=483855 + chart_facts[fact_category=dasha_scope_cap]=1 = 483856" in c["measured"]
    assert c["produced_set"]["extra"] == [] and [p["rows"] for p in c["produced_set"]["parts"]] == [483855, 1]


def test_a_different_sum_fails(monkeypatch, tmp_path):
    w = World({"chart_dashas": 483855, "chart_facts": 0}, written=["chart_dashas", "chart_facts"])
    c = run(monkeypatch, tmp_path, w)
    assert c["v"] == ac.FAIL and "rows_written=483856 disagrees with live=483855" in c["measured"] and "declared produced-table set" in c["measured"], c


def test_every_declared_table_is_counted_even_when_the_sum_is_zero(monkeypatch, tmp_path):
    w = World({"chart_dashas": 0, "chart_facts": 0}, written=["chart_dashas"])
    c = run(monkeypatch, tmp_path, w, rw="0", live=0)
    assert c["v"] == ac.FAIL and "empty: live=0" in c["measured"]              # the non-emptiness rule still applies over the declared set
    counted = [s for s in w.sql if s.startswith("SELECT count(*)")]
    assert len(counted) == 2


def test_no_declaration_reads_exactly_as_before(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS)
    c = run(monkeypatch, tmp_path, w, decl=None)
    assert c["v"] == ac.FAIL and "rows_written=483856 disagrees with live=483855 (count_sql over the target table" in c["measured"] and "produced_set" not in c
    assert w.sql == []                                                           # nothing was read for the clause


def test_a_declaration_is_not_a_tolerance_the_sum_must_equal_rows_written(monkeypatch, tmp_path):
    w = World({"chart_dashas": 483855, "chart_facts": 1}, written=["chart_dashas", "chart_facts"])
    assert run(monkeypatch, tmp_path, w, rw="483857")["v"] == ac.FAIL
    assert run(monkeypatch, tmp_path, w, rw="483855")["v"] == ac.FAIL


# ───────────────────────── the writer scan: extras, UPDATE-only, unread scope ─────────────────────────

def test_an_undeclared_extra_table_the_writer_writes_fails(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS, written=["chart_dashas", "chart_facts", "chart_divisionals"])
    c = run(monkeypatch, tmp_path, w)
    assert c["v"] == ac.FAIL and "chart_divisionals" in c["measured"] and "undeclared extra table" in c["measured"]
    assert c["produced_set"]["extra"] == ["chart_divisionals"]


def test_a_table_only_updated_and_undeclared_is_also_an_extra(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS, written=["chart_dashas", "chart_facts"], update_only=["chart_vichara"])
    assert run(monkeypatch, tmp_path, w)["v"] == ac.FAIL


def test_an_unread_writer_scope_caps_a_pass_at_partial(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS, written=["chart_dashas", "chart_facts"], complete=False)
    c = run(monkeypatch, tmp_path, w)
    assert c["v"] == ac.PARTIAL and "not proven" in c["measured"]


def test_no_recognised_writer_file_means_nothing_was_scanned_so_a_pass_is_capped(monkeypatch, tmp_path):
    w = World(DASHA_COUNTS)
    c = run(monkeypatch, tmp_path, w, writer_files=False)
    assert c["v"] == ac.PARTIAL and "not proven" in c["measured"]


def test_the_bookkeeping_tables_are_never_extras():
    assert {"asset_throughput", "build_runs", "build_run_assets"} <= ac.BOOKKEEPING_TABLES


KARANAJALA = [dict(table="bodha_cgm_edges"), dict(table="bodha_contradictions"), dict(table="bodha_cgm_nodes", why="the writer updates the centrality columns of the node rows bo_bimba inserts")]


def test_a_declared_update_only_table_is_excluded_from_the_sum(monkeypatch, tmp_path):
    w = World({"bodha_cgm_edges": 849, "bodha_contradictions": 10, "bodha_cgm_nodes": 385}, scoped=(),
              written=["bodha_cgm_edges", "bodha_contradictions"], update_only=["bodha_cgm_nodes"])
    c = run(monkeypatch, tmp_path, w, aid="bo_karanajala", decl=KARANAJALA, rw="859", live=849)
    assert c["v"] == ac.PASS and "bodha_cgm_edges=849 + bodha_contradictions=10 = 859" in c["measured"] and "declared UPDATE-only, not counted: bodha_cgm_nodes" in c["measured"], c
    assert c["produced_set"]["excluded"] == ["bodha_cgm_nodes"]
    assert any('"bodha_cgm_nodes"' in s for s in w.sql)                          # still read: every declared table is checked


def test_update_only_is_not_assumed_when_the_scan_is_incomplete(monkeypatch, tmp_path):
    w = World({"bodha_cgm_edges": 849, "bodha_contradictions": 10, "bodha_cgm_nodes": 385}, scoped=(),
              written=["bodha_cgm_edges", "bodha_contradictions"], update_only=["bodha_cgm_nodes"], complete=False)
    c = run(monkeypatch, tmp_path, w, aid="bo_karanajala", decl=KARANAJALA, rw="859", live=849)
    assert c["v"] == ac.FAIL and "= 1244" in c["measured"]


@pytest.mark.parametrize("aid,tables", [("bo_cdlm_summary", ["bodha_cdlm_chart_summary", "bodha_cdlm_domain_rollups", "bodha_cdlm_pattern_clusters"]),
                                        ("bo_cgm_motifs", ["bodha_cgm_motifs", "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary"]),
                                        ("bo_sangati", ["bodha_cdlm_cells", "bodha_convergence", "bodha_triangulation"]),
                                        ("bo_upaya", ["bodha_rm_resonances", "bodha_rm_remedy_prescriptions", "bodha_rm_chart_summary", "bodha_rm_dosha_remedy_bundles", "bodha_rm_pattern_remedies"]),
                                        ("ga_prashna", ["ga_prashna_lagna", "ga_prashna_judgment"])])
def test_multi_table_writers_compare_against_the_sum_of_every_declared_table(monkeypatch, tmp_path, aid, tables):
    counts = {t: i + 2 for i, t in enumerate(tables)}
    total = sum(counts.values())
    w = World(counts, scoped=tables, written=tables)
    c = run(monkeypatch, tmp_path, w, aid=aid, decl=[dict(table=t) for t in tables], rw=str(total), live=counts[tables[0]])
    assert c["v"] == ac.PASS and f"= {total}" in c["measured"] and len(c["produced_set"]["parts"]) == len(tables), c
    bad = run(monkeypatch, tmp_path, w, aid=aid, decl=[dict(table=t) for t in tables], rw=str(total - 1), live=counts[tables[0]])
    assert bad["v"] == ac.FAIL


def test_the_committed_census_names_these_multi_table_writers():
    """The real rev-25 census: these assets' count_sql tables are the tables a declaration names (ga_prashna 2, bo_sangati 2 of 3, bo_upaya 2 of 5 under count_sql today)."""
    d = json.loads(L2_FILE.read_text(encoding="utf-8"))
    by = {a["asset_id"]: a["count_sql_tables"] for a in d["L2"]["assets"]}
    assert by["bo_sangati"] == ["bodha_cdlm_cells", "bodha_triangulation"] and by["bo_upaya"] == ["bodha_rm_resonances", "bodha_rm_remedy_prescriptions"]
    assert by["bo_cdlm_summary"] == ["bodha_cdlm_chart_summary"]            # count_sql sees one of the three (migration 1297 widens it)


# ───────────────────────── the reads ─────────────────────────

def test_the_reads_are_read_only_selects_scoped_to_the_chart_and_the_declared_slice(monkeypatch):
    w = World(DASHA_COUNTS)
    monkeypatch.setattr(ac, "psql", w.psql)
    monkeypatch.setattr(ac, "scalar", w.scalar)
    got = ac.produced_set_counts(DASHA, CHART)
    assert [(t, n) for t, _f, n in got] == [("chart_dashas", 483855), ("chart_facts", 1)]
    sqls = [s for s in w.sql if "FROM \"" in s]
    assert sqls[0] == f"SELECT count(*)::text FROM \"chart_dashas\" WHERE chart_id = '{CHART}'"
    assert sqls[1] == f"SELECT count(*)::text FROM \"chart_facts\" WHERE chart_id = '{CHART}' AND \"fact_category\" = 'dasha_scope_cap'"
    assert all(s.lstrip().upper().startswith("SELECT") for s in w.sql)


def test_a_global_table_is_counted_whole_and_a_quote_is_escaped(monkeypatch):
    w = World({"bg_x": 7}, scoped=())
    monkeypatch.setattr(ac, "psql", w.psql)
    monkeypatch.setattr(ac, "scalar", w.scalar)
    ac.produced_set_counts([dict(table="bg_x", filter=dict(column="kind", equals="it's"))], CHART)
    assert w.sql[-1] == "SELECT count(*)::text FROM \"bg_x\" WHERE \"kind\" = 'it''s'"


@pytest.mark.parametrize("decl,chart", [([dict(table="a; DROP TABLE x")], CHART), ([dict(table="ok", filter=dict(column="c; x", equals="v"))], CHART),
                                        ([dict(table="ok")], "362f9f17-0000-0000-0000-000000000000"), ([dict(table="ok")], "not-a-uuid")])
def test_malformed_names_and_unusable_charts_are_refused_before_any_count(monkeypatch, decl, chart):
    w = World({"ok": 1})
    monkeypatch.setattr(ac, "psql", w.psql)
    monkeypatch.setattr(ac, "scalar", w.scalar)
    with pytest.raises(ac.Unknown):
        ac.produced_set_counts(decl, chart)
    assert not [s for s in w.sql if s.startswith("SELECT count")]


def test_an_unreadable_declared_table_reads_errored_never_pass(monkeypatch, tmp_path):
    w = World({"chart_dashas": 483855, "chart_facts": None}, written=["chart_dashas", "chart_facts"])
    c = run(monkeypatch, tmp_path, w)
    assert c["v"] == ac.ERRORED and "could not be counted" in c["measured"]


def test_the_criterion_is_revision_4_and_says_the_set_is_not_a_tolerance():
    e = ac.CRITERION_REGISTRY["Build.completion"]
    assert e["revision"] == 4 and "produced_tables" in e["applicability"] and "not a tolerance" in e["applicability"]
