"""TI-L0-20 (SS Q7 / Q21): dispatchable writers for the two static L0 assets that had none.

bg_gochara_citation_resolution (R9, 14 rows) - re-seeded from git by delete-then-insert.
bg_sarvatobhadra_grid (ADJUDICATION-11, 0 rows by ruling) - asserts the ruled empty state.

Proves
  static    the 14 seed rows equal the production rows read 2026-10-03 (fixture) and obey the
            table's honest-gap rules; both writers are registered with the frozen contract;
  real PG   (env-gated) the writer turns a damaged table (stray row, edited row, missing row)
            back into exactly the 14 rows, and the migration-631 integrity digest - extracted
            from the real migration file and evaluated inside PostgreSQL - reads TRUE; a rerun
            is a no-op. The grid writer empties the table and NEVER deletes a row (confirmed or staged, N-46).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from brahmagyan import l0_gochara_citation_resolution as G
from pipeline.orchestrator.writers import ContextSpec, get_writer
from pipeline.orchestrator.writers.bg_gochara_citation_resolution import GocharaCitationResolutionWriter
from pipeline.orchestrator.writers.bg_sarvatobhadra_grid import SarvatobhadraGridWriter
from tests._l0d_pg import requires_pg, scratch_schema

LIVE = json.loads((Path(__file__).parent / "fixtures" / "gochara_citation_resolution_live.json").read_text(encoding="utf-8"))
MIG_631 = Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "631_nirmana_l0_gochara_citation_chunk_repair.sql"


def ctx(asset_id, conn=None, dry_run=False):
    return ContextSpec(asset_id=asset_id, build_id="b", db_conn=conn, dry_run=dry_run)


# ── static ───────────────────────────────────────────────────────────────────

def test_seed_rows_equal_the_production_rows_exactly():
    assert G.ROWS == LIVE and len(G.ROWS) == 14


def test_seed_obeys_the_honest_gap_rules():
    assert len({(r["citation_string"], r["chunk_id"]) for r in G.ROWS}) == 14          # PK
    assert len({r["constant_name"] for r in G.ROWS}) == 14
    assert sum(r["status"] == "resolved" for r in G.ROWS) == 1
    for r in G.ROWS:
        if r["status"] == "unresolved":
            assert r["chunk_id"].startswith("CORPUS_GAP:"), r["constant_name"]    # no invented chunk
    assert [r["chunk_id"] for r in G.ROWS if r["status"] == "resolved"] == ["phaladeepika_pg0353_c01"]


def test_both_writers_are_registered_under_the_frozen_contract_only_when_the_gate_is_on(monkeypatch):
    """Registry-first ordering (review L0C H-1): the writers are unreachable until ORCHESTRATOR_L0_STATIC_WRITERS is on."""
    import importlib
    from pipeline.orchestrator import writers as W
    from pipeline.orchestrator.writers import _l0_static_gate as gate
    from pipeline.orchestrator.writers import bg_gochara_citation_resolution as m1, bg_sarvatobhadra_grid as m2

    ids = ("bg_gochara_citation_resolution", "bg_sarvatobhadra_grid")
    for i in ids:
        W._REGISTRY.pop(i, None)
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    importlib.reload(m1); importlib.reload(m2)
    assert not gate.enabled() and all(get_writer(i) is None for i in ids), "gate OFF: not registered, the writer-gap pre-flight sees nothing new"
    for i in ids:
        W._REGISTRY.pop(i, None)
    monkeypatch.setenv(gate.ENV_VAR, "1")
    importlib.reload(m1); importlib.reload(m2)
    assert gate.enabled()
    assert get_writer("bg_gochara_citation_resolution") is m1.GocharaCitationResolutionWriter
    assert get_writer("bg_sarvatobhadra_grid") is m2.SarvatobhadraGridWriter
    for cls in (m1.GocharaCitationResolutionWriter, m2.SarvatobhadraGridWriter):
        src = Path(__import__(cls.__module__, fromlist=["x"]).__file__).read_text(encoding="utf-8")
        code = "\n".join(l for l in src.splitlines() if not l.strip().startswith(("#", '"""')))
        assert ".commit(" not in code and ".close(" not in code and "INSERT INTO asset_throughput" not in code
    # leave the process-wide registry as the default (gate off) found it
    for i in ids:
        W._REGISTRY.pop(i, None)
    monkeypatch.delenv(gate.ENV_VAR, raising=False)
    importlib.reload(m1); importlib.reload(m2)


@pytest.mark.parametrize("raw,on", [("1", True), ("true", True), ("YES", True), ("on", True), ("", False), ("0", False), ("no", False), ("off", False)])
def test_gate_values(monkeypatch, raw, on):
    from pipeline.orchestrator.writers import _l0_static_gate as gate
    monkeypatch.setenv(gate.ENV_VAR, raw)
    assert gate.enabled() is on


def test_dry_runs_touch_nothing():
    assert G.seed_gochara_citation_resolution(None, dry_run=True) == {"bg_gochara_citation_resolution": 14, "deleted": 0}
    assert GocharaCitationResolutionWriter().run(ctx("bg_gochara_citation_resolution", dry_run=True)).rows_inserted == 14
    assert SarvatobhadraGridWriter().run(ctx("bg_sarvatobhadra_grid", dry_run=True)).rows_inserted == 0


# ── real PostgreSQL ──────────────────────────────────────────────────────────

CITATION_DDL = """
CREATE TABLE classical_text_chunks (chunk_id text PRIMARY KEY, text_id text, verse_ref text);
INSERT INTO classical_text_chunks VALUES ('phaladeepika_pg0353_c01','phaladeepika','PG353:C1');
CREATE TABLE bg_gochara_citation_resolution (
  citation_string text NOT NULL, chunk_id text NOT NULL, text_id text NOT NULL, verse_ref text NOT NULL,
  status text NOT NULL DEFAULT 'resolved' CHECK (status IN ('resolved','unresolved')),
  source_citation text NOT NULL, constant_name text, note text, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bg_gochara_citation_resolution_pk PRIMARY KEY (citation_string, chunk_id));
"""
GRID_DDL = """
CREATE TABLE bg_sarvatobhadra_grid (
  id bigserial PRIMARY KEY, school_tag text NOT NULL, cell_index integer NOT NULL,
  cell_kind text NOT NULL CHECK (cell_kind IN ('nakshatra_position','vedha_pair')), cell_value text NOT NULL,
  source_text_id text, source_citation text, table_version text NOT NULL, native_confirmed boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bg_sarvatobhadra_grid_natural_key UNIQUE (school_tag, cell_kind, cell_index, table_version));
"""


def sealed_check_sql() -> str:
    s = MIG_631.read_text(encoding="utf-8")
    m = re.search(r"citation_check constant text := \$check\$(.*?)\$check\$;", s, re.S)
    assert m, "could not extract the sealed integrity check from migration 631"
    return m.group(1).strip()


def rows(conn):
    cols = "citation_string,chunk_id,text_id,verse_ref,status,source_citation,constant_name,note"
    return [dict(r) for r in conn.execute(f"SELECT {cols} FROM bg_gochara_citation_resolution ORDER BY citation_string COLLATE \"C\", chunk_id COLLATE \"C\"")]


@requires_pg
def test_real_citation_writer_restores_exactly_the_14_sealed_rows_from_a_damaged_table():
    with scratch_schema(CITATION_DDL) as conn:
        for r in G.ROWS:        # production state
            conn.execute("INSERT INTO bg_gochara_citation_resolution(citation_string,chunk_id,text_id,verse_ref,status,source_citation,constant_name,note) "
                         "VALUES (%(citation_string)s,%(chunk_id)s,%(text_id)s,%(verse_ref)s,%(status)s,%(source_citation)s,%(constant_name)s,%(note)s)", r)
        conn.commit()
        assert list(conn.execute(sealed_check_sql()).fetchone().values())[0] is True
        # damage: stray row + edited row + missing row
        conn.execute("INSERT INTO bg_gochara_citation_resolution VALUES ('zz stray','CORPUS_GAP:zz','bphs','CH1','unresolved','x','ZZ',NULL)")
        conn.execute("UPDATE bg_gochara_citation_resolution SET verse_ref='TAMPERED' WHERE constant_name='GOCHARA_PHALA_BPHS_29'")
        conn.execute("DELETE FROM bg_gochara_citation_resolution WHERE constant_name='SADE_SATI_BPHS_71'")
        conn.commit()
        assert not list(conn.execute(sealed_check_sql()).fetchone().values())[0]
        r = GocharaCitationResolutionWriter().run(ctx("bg_gochara_citation_resolution", conn))
        conn.commit()
        assert r.rows_inserted == 14
        assert rows(conn) == LIVE
        assert list(conn.execute(sealed_check_sql()).fetchone().values())[0] is True
        snap = rows(conn)
        GocharaCitationResolutionWriter().run(ctx("bg_gochara_citation_resolution", conn))
        conn.commit()
        assert rows(conn) == snap


@requires_pg
def test_real_grid_writer_reports_the_state_and_deletes_nothing_native_confirmed_or_staged():
    with scratch_schema(GRID_DDL) as conn:
        r = SarvatobhadraGridWriter().run(ctx("bg_sarvatobhadra_grid", conn))
        conn.commit()
        assert r.rows_inserted == 0 and "0 row(s)" in r.notes and "NOT in the ruled empty state" not in r.notes
        conn.execute("INSERT INTO bg_sarvatobhadra_grid(school_tag,cell_index,cell_kind,cell_value,table_version,native_confirmed) "
                     "VALUES ('s1',1,'vedha_pair','a','v1',false),('s1',2,'vedha_pair','b','v1',false),('s2',1,'vedha_pair','c','v1',true)")
        conn.commit()
        before = [dict(x) for x in conn.execute("SELECT * FROM bg_sarvatobhadra_grid ORDER BY id")]
        r = SarvatobhadraGridWriter().run(ctx("bg_sarvatobhadra_grid", conn))
        conn.commit()
        assert [dict(x) for x in conn.execute("SELECT * FROM bg_sarvatobhadra_grid ORDER BY id")] == before, \
            "N-46: confirmed AND staged rows are never touched (review L0C LOW: staged rows used to be deleted on every rebuild)"
        assert "3 row(s)" in r.notes and "1 native-confirmed, 2 staged" in r.notes and "NOT in the ruled empty state" in r.notes
        assert r.rows_inserted == 0
