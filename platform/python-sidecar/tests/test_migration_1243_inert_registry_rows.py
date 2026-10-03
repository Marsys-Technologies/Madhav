"""Pravāha B (steward M20261003T020844-29ec) — migration 1243 against a REAL PostgreSQL.

The orchestrator's writer-gap pre-flight (`runner._check_writer_registry_gaps`, enforce by default) fails every build run when any
@register()'d writer has no `asset_registry` row with has_writer = true. Production has no row for `ka_gochara_v4_41_candidate`
(registered on main) and the a53 train would add the same hazard for `ka_gochara_v5`. Migration 1243 stages the two INERT rows.

Proven here, on a disposable database whose `asset_registry` has production's exact column list, defaults, CHECK constraints, primary key
and its AFTER UPDATE trigger (the trigger's function is a stub that RAISES, so any UPDATE the migration issued would fail the test):
  (a) the REAL `_check_writer_registry_gaps` — run against every writer main registers — reports exactly the one gap before the
      migration and none after it; with `ka_gochara_v5` also registered (the train) it still reports none;
  (b) a registry row whose writer is NOT yet registered is not a gap (the check goes registry→database only);
  (c) the planner / cockpit predicates the codebase actually uses select neither row, and the same-target co-writer test
      (runner.py:359-365) is unchanged for an active asset sharing `kala_gochara_windows`;
  (d) nothing else changes: every other row is byte-identical; a second application changes nothing; a pre-existing wrong row,
      a dependent asset or a row with has_writer = false make the migration FAIL LOUDLY and roll back whole.
The database is created and dropped by the test (needs GOCHARA_A51_TEST_DATABASE_URL pointing at a disposable server).
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

PG = os.environ.get("GOCHARA_A51_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not PG, reason="needs GOCHARA_A51_TEST_DATABASE_URL (a disposable PostgreSQL server; the test creates and drops its own database)")

MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "1243_ka_gochara_inert_registry_rows.sql"
V41, V5 = "ka_gochara_v4_41_candidate", "ka_gochara_v5"

# production's asset_registry, as read from the catalog (columns, defaults, NOT NULLs, CHECKs, PK, the one trigger)
DDL = """
CREATE TABLE asset_registry (
  asset_id text NOT NULL, layer text NOT NULL, sort_order integer NOT NULL, sanskrit_name text NOT NULL, english_name text NOT NULL,
  english_description text NOT NULL, storage_type text NOT NULL, target_table text, count_sql text, size_sql text, target_floor integer,
  expected_volume_formula text, expected_volume_inputs jsonb, volume_explanation text, depends_on text[] DEFAULT ARRAY[]::text[],
  scope text NOT NULL, is_active boolean DEFAULT true, estimated_seconds integer, created_at timestamptz DEFAULT now(), clear_tables text[],
  asset_type text NOT NULL DEFAULT 'data', layer_name text, layer_index text, provides_apis jsonb, health_probe jsonb,
  catalog_status text NOT NULL DEFAULT 'DRAFT', rebuild_on_probe_fail boolean NOT NULL DEFAULT false, integrity_check_sql text,
  has_substeps boolean NOT NULL DEFAULT false, asset_kind text NOT NULL DEFAULT 'data', service_health text, last_invoked_at timestamptz,
  last_selftest_at timestamptz, selftest_detail jsonb, has_writer boolean NOT NULL DEFAULT false, writer_timeout_seconds integer NOT NULL DEFAULT 600,
  domain text, rung text, superseded_by text, data_disposition text, natural_key_partition text, dead_flag boolean,
  CONSTRAINT asset_registry_pkey PRIMARY KEY (asset_id),
  CONSTRAINT asset_registry_asset_kind_check CHECK (asset_kind = ANY (ARRAY['data','service','artifact'])),
  CONSTRAINT asset_registry_asset_type_check CHECK (asset_type = ANY (ARRAY['data','service'])),
  CONSTRAINT asset_registry_catalog_status_check CHECK (catalog_status = ANY (ARRAY['CURRENT','DRAFT','RETIRED'])),
  CONSTRAINT asset_registry_layer_check CHECK (layer = ANY (ARRAY['brahmagyan','ganita','bodha','kala','phala','mimamsa'])),
  CONSTRAINT asset_registry_scope_check CHECK (scope = ANY (ARRAY['global','per_chart'])),
  CONSTRAINT asset_registry_storage_type_check CHECK (storage_type = ANY (ARRAY['postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only','service'])),
  CONSTRAINT asset_registry_dead_flag_not_retired CHECK (dead_flag IS NOT TRUE OR (catalog_status <> 'RETIRED' AND is_active IS NOT FALSE))
);
CREATE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'an UPDATE fired on asset_registry'; END $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table
  ON asset_registry FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""


def _row(asset_id: str, **kw):
    d = dict(layer="kala", sort_order=1, sanskrit_name="x", english_name="x", english_description="x", storage_type="postgres_table", scope="per_chart",
             is_active=True, has_writer=True, depends_on=[], target_table=None, catalog_status="CURRENT")
    d.update(kw)
    return asset_id, d


def _insert(conn, asset_id, d):
    cols = ["asset_id"] + list(d)
    conn.execute(f"INSERT INTO asset_registry ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", [asset_id] + list(d.values()))


def _all_rows_but_the_two(conn):
    return conn.execute("SELECT t::text FROM asset_registry t WHERE asset_id NOT IN (%s, %s) ORDER BY asset_id", (V41, V5)).fetchall()


@pytest.fixture(scope="module")
def dsn():
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    base = conninfo_to_dict(PG)
    admin = psycopg.connect(make_conninfo(**{**base, "dbname": "postgres"}), autocommit=True)
    name = f"reg1243_{uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        yield make_conninfo(**{**base, "dbname": name})
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


@pytest.fixture()
def world(dsn):
    """A fresh asset_registry holding a row (has_writer = true) for EVERY writer main registers except the two, plus an ACTIVE co-writer of
    kala_gochara_windows. Yields the autocommit connection and the registered-writer id set."""
    import psycopg
    from pipeline.orchestrator.runner import _WRITER_SUBASSET_IDS
    registered = _production_writer_ids()
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("DROP TABLE IF EXISTS asset_registry CASCADE; DROP FUNCTION IF EXISTS nirmana_invalidate_registry_receipts() CASCADE")
    conn.execute(DDL)
    others = sorted(set(registered) - _WRITER_SUBASSET_IDS - {V41, V5, "ka_gochara"})
    assert len(others) > 100, "the writer discovery probe found too few writers"
    for aid in others:
        _insert(conn, aid, _row(aid)[1])
    _insert(conn, "ka_gochara", _row("ka_gochara", target_table="kala_gochara_windows")[1])
    yield conn, set(registered)
    conn.close()


def _production_writer_ids() -> frozenset[str]:
    """Every id main registers, discovered in a FRESH interpreter (the same probe test_has_writer_completeness uses) so this test never
    leaves writers registered in the pytest process."""
    import json, subprocess, sys
    sentinel = "__MADHAV_WRITER_IDS__="
    probe = f"import json\nfrom pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all\ndiscover_all()\nprint({sentinel!r} + json.dumps(sorted(WRITER_REGISTRY)))"
    done = subprocess.run([sys.executable, "-c", probe], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
    line = next(l for l in reversed(done.stdout.splitlines()) if l.startswith(sentinel))
    return frozenset(json.loads(line[len(sentinel):]))


def _gaps(conn, registry):
    from psycopg.rows import dict_row
    from pipeline.orchestrator import runner
    import pipeline.orchestrator.writers as W
    real = dict(W.WRITER_REGISTRY)
    W.WRITER_REGISTRY.clear(); W.WRITER_REGISTRY.update({k: object for k in registry})
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            return runner._check_writer_registry_gaps(cur)         # the REAL check, over the real registered ids
    finally:
        W.WRITER_REGISTRY.clear(); W.WRITER_REGISTRY.update(real)


def _apply(conn):
    with conn.transaction():
        conn.execute(MIGRATION.read_text(encoding="utf-8"))


def test_a_the_real_gap_check_reports_the_one_gap_before_and_none_after(world):
    conn, registered = world
    # the guard is proven in ENFORCE mode: that is the code's default, so the mode in force is "enforce" unless the environment overrides it
    from pipeline.orchestrator import runner
    if not os.environ.get("ORCHESTRATOR_WRITER_GAP_CHECK"):
        assert runner._WRITER_GAP_MODE == "enforce"
    assert V41 in registered, "ka_gochara_v4_41_candidate must be a registered writer on this tree"
    # before: the production defect, reproduced with the real check — on main exactly [V41]; on the a53 tree both inert writers are registered
    assert _gaps(conn, registered) == sorted({V41, V5} & registered)
    _apply(conn)
    assert _gaps(conn, registered) == []
    # the train: ka_gochara_v5 registered as well — still no gap, because 1243 also staged its row
    assert _gaps(conn, registered | {V5}) == []
    # and without the migration the train WOULD have failed every run
    conn.execute("DELETE FROM asset_registry WHERE asset_id IN (%s, %s)", (V41, V5))
    assert _gaps(conn, registered | {V5}) == sorted([V41, V5])


def test_b_a_row_whose_writer_is_not_registered_is_not_a_gap(world):
    conn, registered = world
    _apply(conn)
    assert _gaps(conn, registered - {V5}) == []                 # the V5 row exists, no V5 writer registered: nothing flagged


def test_c_planners_and_cockpit_predicates_select_neither_row_and_cowriter_test_is_unchanged(world):
    conn, _ = world
    cowriters = """SELECT ar.asset_id, EXISTS (SELECT 1 FROM asset_registry peer WHERE peer.target_table = ar.target_table AND ar.target_table IS NOT NULL
                    AND peer.asset_id <> ar.asset_id AND peer.is_active = true AND peer.has_writer = true) AS has_cowriters
                   FROM asset_registry ar WHERE ar.asset_id = 'ka_gochara'"""
    before = conn.execute(cowriters).fetchall()
    _apply(conn)
    preds = {
        "runPreparation.ts:183 (is_active)": "SELECT asset_id FROM asset_registry WHERE is_active = true",
        "recalibrationEnqueue.ts:141 (is_active AND has_writer)": "SELECT asset_id FROM asset_registry WHERE is_active = true AND has_writer = true",
        "cockpit plan/route.ts:50 (has_writer AND is_active)": "SELECT asset_id FROM asset_registry WHERE has_writer = true AND is_active = true",
        "cockpit stats/route.ts:301 (is_active)": "SELECT asset_id FROM asset_registry WHERE is_active = true",
        "runner.py:871 full registry (is_active)": "SELECT asset_id FROM asset_registry WHERE is_active = true",
        "dag_edge_guard.py:101 (is_active)": "SELECT asset_id FROM asset_registry WHERE is_active = true",
    }
    for name, sql in preds.items():
        got = {r[0] for r in conn.execute(sql).fetchall()}
        assert V41 not in got and V5 not in got, name
    assert conn.execute(cowriters).fetchall() == before          # an active asset on the same target table does not gain a co-writer
    assert conn.execute("SELECT count(*) FROM asset_registry WHERE depends_on && ARRAY[%s, %s]::text[]", (V41, V5)).fetchone()[0] == 0


def test_d_the_two_rows_are_inert_nothing_else_changes_and_a_second_application_changes_nothing(world):
    conn, _ = world
    other_before = _all_rows_but_the_two(conn)
    _apply(conn)                                                 # the stub UPDATE trigger would have raised on any UPDATE
    assert _all_rows_but_the_two(conn) == other_before
    rows = conn.execute("SELECT asset_id, is_active, has_writer, depends_on, scope, layer, layer_name, layer_index, catalog_status, asset_type, asset_kind, "
                        "has_substeps, writer_timeout_seconds, target_table, target_floor, estimated_seconds, count_sql FROM asset_registry WHERE asset_id IN (%s, %s) ORDER BY 1", (V41, V5)).fetchall()
    assert [r[0] for r in rows] == [V41, V5]
    for r in rows:
        assert (r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[13], r[14], r[15]) == \
               (False, True, [], "per_chart", "kala", "Kāla", "L3", "CURRENT", "data", "data", "kala_gochara_windows", 0, None)
    assert rows[0][11:13] == (True, 7200) and rows[1][11:13] == (False, 600)
    assert rows[0][16].endswith("generation='4.1'") and rows[1][16].endswith("generation='5.0'")
    snap = conn.execute("SELECT t::text FROM asset_registry t WHERE asset_id IN (%s, %s) ORDER BY asset_id", (V41, V5)).fetchall()
    _apply(conn)                                                 # idempotent: DO NOTHING, post-checks still pass, no UPDATE
    assert conn.execute("SELECT t::text FROM asset_registry t WHERE asset_id IN (%s, %s) ORDER BY asset_id", (V41, V5)).fetchall() == snap
    assert _all_rows_but_the_two(conn) == other_before


@pytest.mark.parametrize("setup, message", [
    ("INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active, has_writer) "
     "VALUES ('ka_gochara_v4_41_candidate','kala',1,'x','x','x','postgres_table','per_chart',true,true)", "found 1 matching row"),          # pre-existing but ACTIVE
    ("INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active, has_writer) "
     "VALUES ('ka_gochara_v5','kala',1,'x','x','x','postgres_table','per_chart',false,false)", "found 1 matching row"),                  # pre-existing, has_writer = false
    ("INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, depends_on) "
     "VALUES ('ka_x_dependent','kala',1,'x','x','x','postgres_table','per_chart',ARRAY['ka_gochara_v5'])", "1 asset(s) depend on the inert rows"),   # a dependent asset exists
])
def test_d_a_wrong_pre_existing_row_or_a_dependent_makes_the_migration_fail_loudly_and_roll_back_whole(world, setup, message):
    conn, _ = world
    conn.execute(setup)
    other_before = _all_rows_but_the_two(conn)
    existing = conn.execute("SELECT asset_id FROM asset_registry WHERE asset_id IN (%s, %s) ORDER BY 1", (V41, V5)).fetchall()
    import psycopg
    with pytest.raises(psycopg.errors.RaiseException) as e:
        _apply(conn)
    assert "1243:" in str(e.value) and message in str(e.value)
    # whole rollback: the rows that were missing were NOT left behind, nothing else moved
    assert conn.execute("SELECT asset_id FROM asset_registry WHERE asset_id IN (%s, %s) ORDER BY 1", (V41, V5)).fetchall() == existing
    assert _all_rows_but_the_two(conn) == other_before
