"""test_formgap_decl_static.py: the FORM-GAP declarations of the three static / view assets are TRUE on the REAL DDL (and, for the seeded table, the REAL migration data) (SS N-191).

  * bg_sarvatobhadra_grid: created deliberately empty by migration 529, no writer. `static_read zero_rows`: one live EXISTS stands in for the observed write; a row is a FAIL.
  * bo_samvada: the view vw_chart_digest; its writer runs no DDL / DML. `static_read closed_read`: the view's four closed columns are read live in place of the write.
  * bg_gochara_citation_resolution: created AND seeded by migration 565 (executed whole here), no writer. `static_read closed_read`.
The COMMITTED declarations (asset_declarations.json) are used as they are; every claim has a mutation that must turn the reading red.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, NA, FAIL, NO_DET, CELLS  # noqa: E402
from test_formgap_static_read import view, _seed_view, _view_sql, VIEW_SRC_TABLES  # noqa: E402,F401  (the real view + real source DDL fixture)

DECLS = ac.load_asset_declarations()


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


# ═════════════════════════════════════════ bg_sarvatobhadra_grid ═════════════════════════════════════════
SG = "bg_sarvatobhadra_grid"


def test_sarvatobhadra_declaration_is_the_checked_zero_rows_form():
    e = DECLS[SG]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["kind"] == "static" and e["has_writer"] is False
    assert e["prose_none"]["static_read"]["mode"] == "zero_rows" and e["prose_none"]["closed_columns"] == []


def test_sarvatobhadra_facts_the_declaration_rests_on_no_insert_anywhere_and_migration_529_seeds_nothing():
    """The 'no writer, no INSERT' premise is checked on the source tree: no tracked code or migration inserts into the table, and migration 529 inserts only its registry catalogue row."""
    sql = (fs.SMIG / "529_bg_sarvatobhadra_grid.sql").read_text(encoding="utf-8")
    inserts = re.findall(r"(?im)^\s*INSERT\s+INTO\s+(\S+)", sql)
    assert inserts == ["asset_registry"] and "No rows are inserted by this migration." in sql                  # the one INSERT is the registry catalogue row, never a grid row
    out = subprocess.run(["git", "grep", "-il", "-E", "insert[[:space:]]+into[[:space:]]+(public\\.)?bg_sarvatobhadra_grid", "--", "*.py", "*.ts", "*.tsx", "*.sql", "*.sh"],
                         cwd=fs.REPO, capture_output=True, text=True, timeout=120).stdout.split()
    hits = [p for p in out if "__tests__" not in p and "/tests/" not in p]
    assert hits == [], hits
    reg = (fs.REPO / "platform/scripts/seed/asset_registry_seed.ts").read_text(encoding="utf-8").splitlines()
    window = "\n".join(reg[950:962]).lower()
    assert "migration 529" in window and "deliberately empty" in window and "no wri" in window


@pytest.fixture()
def sg(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, SG)
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "529_bg_sarvatobhadra_grid.sql", SG))
    yield pg
    fs.drop_tables(pg, SG)


def _m_sg(pg, monkeypatch, decl=None, registry=None):
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: [])
    return fs.measure(SG, pg, monkeypatch, [], SG, [SG], decl or _own(SG), registry=dict({"has_writer": False}, **(registry or {})))


def test_REAL_DDL_the_committed_declaration_reads_na_on_all_six_on_the_empty_table(sg, monkeypatch):
    got = _m_sg(sg, monkeypatch)
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["static_read"]["rows"] == {SG: 0}


def test_REAL_DDL_MUTATION_one_row_turns_the_committed_declaration_red(sg, monkeypatch):
    fs.psql(sg, f"INSERT INTO {SG} (school_tag, cell_index, cell_kind, cell_value, table_version) VALUES ('x', 1, 'vedha_pair', 'a sentence', 'v1')")
    got = _m_sg(sg, monkeypatch)
    assert got["Narr.agree"]["v"] == FAIL and "declared empty by design" in got["Narr.agree"]["measured"]


def test_REAL_DDL_MUTATION_a_registry_row_that_says_the_asset_has_a_writer_withdraws_the_release(sg, monkeypatch):
    got = _m_sg(sg, monkeypatch, registry=dict(has_writer=True))
    assert all(got[c]["v"] == NO_DET for c in CELLS)


# ═════════════════════════════════════════ bo_samvada ═════════════════════════════════════════

def _m_bo(pg, monkeypatch, decl=None, scope=None):
    scope = {"vw_chart_digest": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")} if scope is None else scope
    return fs.measure("bo_samvada", pg, monkeypatch, ac.registered_ids("")["bo_samvada"], "vw_chart_digest", ["vw_chart_digest"], decl or _own("bo_samvada"), scope=scope, registry=dict(has_writer=True))


def test_bo_samvada_declaration_adds_only_the_closed_read_to_the_checked_form():
    e = DECLS["bo_samvada"]
    assert ac.prose_none_problem(e) is None and e["kind"] == "view" and e["prose_none"]["static_read"]["mode"] == "closed_read"
    assert [c["column"] for c in e["prose_none"]["closed_columns"]] == ["ayanamsha_id", "weakest_graha", "top_priority_class", "top_convergence_domains"]


def test_bo_samvada_writer_runs_no_ddl_or_dml_the_premise_of_the_form():
    import ast
    src = (fs.REPO / "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    executes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("execute", "executemany", "copy")]
    assert executes == []                                                                   # nothing in the writer module executes a statement
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "_CREATE_VIEW_CLEAN" not in {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}, names
    assert "rows_inserted=0" in src.replace(" ", "")


def test_REAL_VIEW_the_committed_declaration_reads_na_on_all_six(view, monkeypatch):
    _seed_view(view)
    got = _m_bo(view, monkeypatch)
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["static_read"]["mode"] == "closed_read"


def test_REAL_VIEW_MUTATION_without_static_read_the_asset_is_back_to_no_detector(view, monkeypatch):
    _seed_view(view)
    d = _own("bo_samvada")
    del d["prose_none"]["static_read"]
    got = _m_bo(view, monkeypatch, d)
    assert all(got[c]["v"] == NO_DET for c in CELLS)


def test_REAL_VIEW_MUTATION_a_label_outside_the_declared_vocabulary_is_a_FAIL(view, monkeypatch):
    _seed_view(view)
    fs.psql(view, f"UPDATE bodha_rm_resonances SET remedy_priority_class = 'urgent' WHERE chart_id = '{CHART_A}'")
    assert _m_bo(view, monkeypatch)["Narr.agree"]["v"] == FAIL


def test_REAL_VIEW_MUTATION_a_kind_that_is_not_view_or_static_withdraws_the_release(view, monkeypatch):
    _seed_view(view)
    d = _own("bo_samvada")
    d["kind"] = "data"
    assert all(_m_bo(view, monkeypatch, d)[c]["v"] == NO_DET for c in CELLS)


# ═════════════════════════════════════════ bg_gochara_citation_resolution ═════════════════════════════════════════
GC = "bg_gochara_citation_resolution"


def test_gochara_declaration_is_the_closed_read_form_on_a_static_asset():
    e = DECLS[GC]
    assert ac.prose_none_problem(e) is None and e["kind"] == "static" and e["has_writer"] is False and e["prose_none"]["static_read"]["mode"] == "closed_read"


@pytest.fixture()
def gc(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, GC)
    # the real migration text up to its asset_registry catalogue row (this database has no asset_registry): the DDL and every seed row, unedited
    text = (fs.SMIG / "565_bg_gochara_citation_resolution.sql").read_text(encoding="utf-8")
    cut = text.index("-- ── asset_registry seed")
    sql_file = pathlib.Path(tempfile.mkdtemp(prefix="formgap565_")) / "565_head.sql"
    sql_file.write_text(text[:cut] + "COMMIT;\n", encoding="utf-8")
    fs.psql(pg, path=sql_file)
    yield pg
    fs.drop_tables(pg, GC)


def _m_gc(pg, monkeypatch, decl=None, registry=None):
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: [])
    return fs.measure(GC, pg, monkeypatch, [], GC, [GC], decl or _own(GC), registry=dict({"has_writer": False}, **(registry or {})))


def test_REAL_MIGRATION_565_seeds_rows_and_the_committed_declaration_reads_na_on_all_six(gc, monkeypatch):
    assert int(fs.psql(gc, f"SELECT count(*) FROM {GC}").strip()) > 0
    got = _m_gc(gc, monkeypatch)
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["static_read"]["mode"] == "closed_read"


def test_REAL_MIGRATION_565_MUTATION_without_static_read_it_is_no_detector(gc, monkeypatch):
    d = _own(GC)
    del d["prose_none"]["static_read"]
    assert all(_m_gc(gc, monkeypatch, d)[c]["v"] == NO_DET for c in CELLS)


def test_REAL_MIGRATION_565_MUTATION_a_writer_flag_in_the_registry_withdraws_the_release(gc, monkeypatch):
    got = _m_gc(gc, monkeypatch, registry=dict(has_writer=True))
    assert all(got[c]["v"] == NO_DET for c in CELLS)
