"""test_formgap_decl_static.py: the FORM-GAP declarations of the three static / view assets are TRUE on the REAL DDL (and, for the seeded table, the REAL migration data) (SS N-191).

  * bg_sarvatobhadra_grid (RETIRED by migration 1360; its declaration was dropped from asset_declarations.json at declarations rev28b, and no other committed declaration uses `zero_rows`): the checked zero-rows FORM is still exercised, on SG_DECL, a synthetic declaration built in this file in the exact shape of the dropped one, against the REAL migration-529 DDL. `static_read zero_rows`: one live EXISTS stands in for the observed write; a row is a FAIL.
  * bo_samvada: the view vw_chart_digest; its writer runs no DDL / DML. `static_read closed_read`: the view's four closed columns are read live in place of the write.
  * bg_gochara_citation_resolution: created AND seeded by migration 565 (executed whole here), no writer. Review fix HIGH 1: it declares NO static_read (its transcription / identifier columns are exemptions no read verifies), so it reads NO_DETECTOR; a forged closed_read declaration is refused.
The COMMITTED declarations (asset_declarations.json) are used as they are (except the retired grid's, which is the synthetic SG_DECL); every claim has a mutation that must turn the reading red.
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


def _own_sg():
    return json.loads(json.dumps(SG_DECL))


# ═════════════════════════════════════════ bg_sarvatobhadra_grid ═════════════════════════════════════════
SG = "bg_sarvatobhadra_grid"
# The declaration dropped at rev28b, reproduced verbatim in shape (git: 093094add^:platform/scripts/governance/asset_declarations.json), so the checked zero-rows form keeps its coverage.
SG_DECL = {
    "kind": "static", "has_writer": False, "carriage": {"served_surface": None}, "prose_fields": [], "terminal_by_construction": None,
    "cross_asset_writes": None, "read_evidence": None, "read_table": None, "read_kind": None,
    "evidence": {
        "kind": "migration supabase/529 creates it deliberately empty (ADJUDICATION-11); seed only; has_writer=false and no @register (census writer_files empty); T0 execution_obligation static_acceptance/empty_acceptance; registry asset_kind reads data",
        "carriage": "served_surface null (unknown): the only evidence is a provenance LABEL; Dens.served N/A.",
        "prose_fields": "stores nothing: the table is created DELIBERATELY EMPTY by migration 529 (platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql, line 65: ADJUDICATION-11: no school-keyed grid is source-verified), no writer exists and the only reader is a SELECT. The three open text columns of the schema (cell_value, source_text_id, source_citation) can hold no prose while the table holds no row; a row would contradict this declaration.",
    },
    "source": {"na": "not_built", "why": "the sarvatobhadra grid table exists but no writer builds it and it holds no rows, so the asset is declared not built and reads as a failure of the build", "evidence": "platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql:1"},
    "evidence_kind": "writer",
    "prose_none": {
        "why": "the table is empty by design and no writer exists, so it holds no text at all; the live read of the table decides, and a single row contradicts the declaration",
        "closed_columns": [],
        "static_read": {"mode": "zero_rows", "why": "no writer fills this table (registry has_writer false, no @register, no INSERT anywhere in the repository) and migration 529 inserts no row, so one live read of the table (it holds no row) stands in for the write the prose check needs",
                        "evidence": "platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql:65"},
    },
}


def test_sarvatobhadra_declaration_is_the_checked_zero_rows_form():
    e = _own_sg()
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
    return fs.measure(SG, pg, monkeypatch, [], SG, [SG], decl or _own_sg(), registry=dict({"has_writer": False}, **(registry or {})))


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


def test_gochara_declares_no_static_read_because_nothing_reads_its_transcription_columns():
    e = DECLS[GC]
    assert ac.prose_none_problem(e) is None and e["kind"] == "static" and e["has_writer"] is False and "static_read" not in e["prose_none"]


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


def test_REAL_MIGRATION_565_seeds_rows_and_the_asset_honestly_reads_no_detector(gc, monkeypatch):
    assert int(fs.psql(gc, f"SELECT count(*) FROM {GC}").strip()) > 0
    got = _m_gc(gc, monkeypatch)
    assert all(got[c]["v"] == NO_DET for c in CELLS)


_FORGED_SR = dict(mode="closed_read", why="the table is seeded by migration 565 and no writer builds it, so a live read stands in for the write",
                  evidence="platform/supabase/migrations/565_bg_gochara_citation_resolution.sql:77")


def test_FORGERY_a_closed_read_declaration_added_beside_the_transcription_columns_is_refused_by_the_validator():
    d = _own(GC)
    d["prose_none"]["static_read"] = dict(_FORGED_SR)
    bad = ac.prose_none_problem(d)
    assert bad and "closed_read cannot stand beside" in bad


def test_FORGERY_a_closed_read_that_got_past_the_validator_still_reads_no_detector_never_na(gc, monkeypatch):
    """The grader refuses on its own: the validator is bypassed, the transcription / identifier columns are exemptions nothing reads."""
    d = _own(GC)
    d["prose_none"]["static_read"] = dict(_FORGED_SR)
    monkeypatch.setattr(ac, "formgap_prose_none_problem", lambda entry, pn: None)
    monkeypatch.setattr(ac, "prose_none_problem", lambda entry: None)
    got = _m_gc(gc, monkeypatch, d)
    assert all(got[c]["v"] == NO_DET for c in CELLS), {c: got[c]["v"] for c in CELLS}
    assert "exempt by declaration alone" in got["Narr.agree"]["measured"]
