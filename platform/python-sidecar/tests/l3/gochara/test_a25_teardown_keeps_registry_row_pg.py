"""Pravāha C27 — teardown keeps the permanent asset_registry row (DB regression).

Codex's reproduction on PR #2996: with migration 1243's inert
ka_gochara_v4_41_candidate row in place, the OLD teardown deleted it, and the
orchestrator's writer-gap preflight (runner.py:159–205, enforce) then reported
[] → ['ka_gochara_v4_41_candidate'] — failing EVERY build run on every chart.

This test executes, against REAL disposable PostgreSQL (never a fake):
  1. the inert row seeded via the dispatch script's OWN REGISTRY_INSERT (the
     exact row migration 1243 lands; the insert is idempotent);
  2. dispatch.main() — stages the run, flips/restores is_active in one
     transaction;
  3. teardown() — deletes the run bookkeeping and '4.1' candidate rows, KEEPS
     the registry row and restores is_active = false (verified by the script's
     own _validate_registry_row inside the same transaction);
  4. a REDEPLOY (dispatch.main() again): the registry INSERT is ON-CONFLICT
     skipped because the row survived teardown;
  5. runner._check_writer_registry_gaps reports NO gap for this asset, and
     the row is present and inert.

NOT_RUN (skip with reason) when the pinned disposable cluster is unreachable —
never a fallback to any other DSN, per the WP10/A2.5 convention.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import psycopg
import psycopg.rows
import pytest

SIDECAR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(SIDECAR.parent / "scripts"))
sys.path.insert(0, str(SIDECAR / "tests" / "l3"))

from _disposable_db_guard import (  # noqa: E402
    assert_disposable_connection,
    validate_disposable_dsn,
)

ASSET_ID = "ka_gochara_v4_41_candidate"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

ADMIN_DSN = os.environ.get(
    "GOCHARA_A25_ADMIN_DSN", "postgresql://wp6:local@localhost:55434/postgres"
)
EXPECTED_CLUSTER_ID = os.environ.get(
    "GOCHARA_A25_DISPOSABLE_CLUSTER_ID", "7691638507951775319"
)

STUB_DDL = """
DROP TABLE IF EXISTS build_run_assets CASCADE;
DROP TABLE IF EXISTS build_runs CASCADE;
DROP TABLE IF EXISTS asset_throughput CASCADE;
DROP TABLE IF EXISTS kala_gochara_authority CASCADE;
DROP TABLE IF EXISTS kala_gochara_publication CASCADE;
DROP TABLE IF EXISTS kala_gochara_coverage CASCADE;
DROP TABLE IF EXISTS kala_gochara_contacts CASCADE;
DROP TABLE IF EXISTS kala_gochara_windows CASCADE;
DROP TABLE IF EXISTS asset_registry CASCADE;
CREATE TABLE asset_registry (
  asset_id TEXT PRIMARY KEY,
  layer TEXT, sort_order INT,
  sanskrit_name TEXT, english_name TEXT, english_description TEXT,
  storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
  target_floor INT, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
  has_substeps BOOLEAN, writer_timeout_seconds INT,
  layer_name TEXT, layer_index TEXT, catalog_status TEXT, asset_kind TEXT,
  depends_on TEXT[], natural_key_partition TEXT
);
CREATE TABLE asset_throughput (
  chart_id UUID, asset_id TEXT NOT NULL, state TEXT,
  rows_written BIGINT, last_error TEXT
);
CREATE UNIQUE INDEX asset_throughput_chart_asset_key
  ON asset_throughput (chart_id, asset_id) WHERE chart_id IS NOT NULL;
CREATE TABLE build_runs (
  id UUID PRIMARY KEY, chart_id UUID, scope TEXT, scope_target TEXT,
  action TEXT, state TEXT, plan JSONB, plan_manifest JSONB,
  plan_manifest_digest TEXT, triggered_by TEXT
);
CREATE TABLE build_run_assets (
  run_id UUID, asset_id TEXT, position INT, state TEXT
);
CREATE TABLE kala_gochara_windows (
  id BIGSERIAL PRIMARY KEY, chart_id UUID, generation TEXT
);
CREATE TABLE kala_gochara_contacts (
  contact_id TEXT PRIMARY KEY, chart_id UUID, generation TEXT
);
CREATE TABLE kala_gochara_coverage (
  id BIGSERIAL PRIMARY KEY, chart_id UUID, generation TEXT
);
CREATE TABLE kala_gochara_publication (
  manifest_id UUID PRIMARY KEY, chart_id UUID, generation TEXT, status TEXT
);
CREATE TABLE kala_gochara_authority (
  chart_id UUID PRIMARY KEY, authoritative_generation TEXT
);
"""


@pytest.fixture()
def disposable_dsn():
    """A brand-new throwaway database on the pinned disposable cluster —
    created for the test, dropped afterwards. Skips (NOT_RUN) unless the
    cluster IS the pinned disposable one."""
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable cluster unreachable ({exc})")
    actual = admin.execute(
        "SELECT system_identifier FROM pg_control_system()").fetchone()[0]
    if str(actual) != EXPECTED_CLUSTER_ID:
        admin.close()
        pytest.skip(
            "NOT_RUN: cluster system_identifier "
            f"{actual} is not the pinned disposable cluster — refusing to "
            "run any setup against an unrecognised cluster")
    dbname = f"a25td_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{dbname}"')
    parts = psycopg.conninfo.conninfo_to_dict(ADMIN_DSN)
    parts["dbname"] = dbname
    dsn = psycopg.conninfo.make_conninfo(**parts)
    admin.close()
    # C24: the shared guard vets the DSN string and the landed session before
    # ANY destructive statement (the fixture DROPs its stub tables).
    validate_disposable_dsn(dsn, dbname)
    probe = psycopg.connect(dsn)
    try:
        assert_disposable_connection(probe, dbname)
    finally:
        probe.close()
    yield dsn
    admin = psycopg.connect(ADMIN_DSN, autocommit=True)
    admin.execute(f'DROP DATABASE IF EXISTS "{dbname}" WITH (FORCE)')
    admin.close()


def _run_dispatch_module(disposable_dsn, monkeypatch):
    """Import the dispatch script pointed at the disposable DB (DATABASE_URL
    set BEFORE import so the module's .env.local setdefault cannot win)."""
    monkeypatch.setenv("DATABASE_URL", disposable_dsn)
    import importlib
    import dispatch_a25_v41_candidate_job as dispatch
    importlib.reload(dispatch)
    return dispatch


def test_teardown_keeps_the_permanent_registry_row_no_writer_gap(
        disposable_dsn, monkeypatch):
    """Codex's C27 regression, end to end on real PostgreSQL:
    1243-shaped inert row → dispatch → teardown → redeploy (registry insert
    skipped, row already present) → writer-gap check does NOT list the asset
    and the row is present + inert."""
    dispatch = _run_dispatch_module(disposable_dsn, monkeypatch)

    # (0) minimal schema the dispatch/teardown/writer-gap paths touch
    setup = psycopg.connect(disposable_dsn, autocommit=True)
    setup.execute(STUB_DDL)
    setup.close()

    # (1) the permanent inert row, as migration 1243 lands it (the script's
    # own idempotent insert — never a re-implementation of the rule)
    conn = psycopg.connect(disposable_dsn, row_factory=psycopg.rows.dict_row)
    conn.execute(dispatch.REGISTRY_INSERT)
    conn.commit()

    # (2) dispatch stages a run; (3) teardown removes it but KEEPS the row
    dispatch.main()
    conn.rollback()  # drop the test connection's snapshot before verifying
    row = conn.execute(
        "SELECT is_active, has_writer FROM asset_registry WHERE asset_id = %s",
        (ASSET_ID,)).fetchone()
    assert row is not None and row["is_active"] is False
    # teardown is fail-closed against ACTIVE execution — the run must be
    # finished before teardown, exactly as in the real steward flow
    conn.execute(
        "UPDATE build_runs SET state = 'complete' WHERE triggered_by = %s",
        (dispatch.TRIGGERED_BY,))
    conn.commit()
    dispatch.teardown()

    # (4) redeploy: the registry INSERT is ON-CONFLICT-skipped — the row
    # survived teardown, so staging works off the permanent row
    dispatch.main()
    conn.rollback()

    # (5) the writer-gap preflight reports NO gap for this asset, and the
    # row is present, inert and writer-flagged
    from pipeline.orchestrator.runner import _check_writer_registry_gaps
    with conn.cursor() as cur:
        gaps = _check_writer_registry_gaps(cur)
    assert ASSET_ID not in gaps
    row = conn.execute(
        "SELECT is_active, has_writer, has_substeps, writer_timeout_seconds,"
        " scope, depends_on FROM asset_registry WHERE asset_id = %s",
        (ASSET_ID,)).fetchone()
    assert row is not None, "teardown deleted the permanent registry row"
    assert row["is_active"] is False
    assert row["has_writer"] is True
    # and teardown left no '4.1' bookkeeping behind for the FIRST run
    assert conn.execute(
        "SELECT count(*) FROM build_runs WHERE triggered_by = %s",
        (dispatch.TRIGGERED_BY,)).fetchone()["count"] == 1  # the redeploy's
    conn.close()
