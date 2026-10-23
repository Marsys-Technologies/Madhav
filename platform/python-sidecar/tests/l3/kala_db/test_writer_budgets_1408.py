"""SR-VEDHA-WRITER-BUDGET: migration 1408 raises asset_registry.writer_timeout_seconds of ka_vedha_gochara from 120 to 600, and every audited K9 /
century-path writer budget is held against its recorded measured wall.

Real SQL on the guarded disposable cluster, registry replayed from the real baseline DDL (same recipe as test_j3c_cap_1395.py). Nothing is
golden-captured: the expected values come from the audit data file (writer_budget_audit_1408.json, each row citing its measurement source) and from
the migration / seed texts.

Claims, one oracle each:
  (a) on the registry as production holds it (vedha at 120) the migration sets 600, touches no other column and no other row, stales nothing;
  (b) re-running it changes nothing (idempotent, the row is not even rewritten), and it refuses an absent row or any value other than 120 / 600;
  (c) the seed declares the value explicitly and equals what the migration writes (seed / migration drift);
  (d) after the migration no audited writer with a recorded measurement is below 2 x that measurement, the registry reads exactly what the audit
      says it should, and writers without a measurement are untouched (NOT_MEASURED -> unchanged).

The migration file is placed by the cockpit (migration numbers 13xx-19xx are not written by builder jobs). It is looked up at
platform/migrations/1408_ka_vedha_gochara_writer_timeout_600.sql, or at $WRITER_BUDGET_1408_SQL; if neither exists the tests FAIL, never skip.
$WRITER_BUDGET_1408_SEED points the seed oracle at another copy of the seed file (used to prove a planted revert fails).
"""
import json
import os
import re
from pathlib import Path

import psycopg
import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
PLATFORM = REPO / "platform"
M1408 = Path(os.environ.get("WRITER_BUDGET_1408_SQL") or PLATFORM / "migrations/1408_ka_vedha_gochara_writer_timeout_600.sql")
SEED = Path(os.environ.get("WRITER_BUDGET_1408_SEED") or PLATFORM / "scripts/seed/asset_registry_seed.ts")
AUDIT = json.loads((HERE / "writer_budget_audit_1408.json").read_text())
TARGET = "ka_vedha_gochara"
REQUIRED_AUDITED = {"ka_vedha_gochara", "ka_yojaka", "ka_gochara_resonance", "ka_gochara", "ka_sangam", "ka_vighnakara", "ka_gochara_v5", "ka_dasha_kala"}
BASELINE = [
    "supabase/migrations/167_asset_registry.sql", "supabase/migrations/202_asset_registry_service_support.sql",
    "supabase/migrations/223_orchestrator_rebuild_probe_dag.sql", "supabase/migrations/242_l3_service_asset_type.sql",
    "supabase/migrations/342_asset_registry_writer_flags.sql", "supabase/migrations/417_asset_registry_writer_timeout_seconds.sql",
    "migrations/590_nirmana_m0_catalogue_contract_columns.sql", "migrations/591_nirmana_m0_partition_and_dead_flag_columns.sql",
]
WRITERS = {w["asset_id"]: w for w in AUDIT["writers"]}


def _migration_sql() -> str:
    assert M1408.exists(), f"migration 1408 is not placed at {M1408} (the cockpit places it; or set WRITER_BUDGET_1408_SQL)"
    return M1408.read_text()


def _migration_value() -> int:
    """The value 1408 writes, read from its executable SET line (comment lines start with '--' and never match)."""
    return int(re.search(r"^\s+SET writer_timeout_seconds = (\d+)\s*$", _migration_sql(), re.M).group(1))


@pytest.fixture(scope="module")
def registry_dsn(isolated_kala_db_dsn):
    """Registry as production holds it: baseline DDL, the real migration-596 invalidation trigger, one row per audited writer at its recorded budget."""
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        for f in BASELINE:
            conn.execute((PLATFORM / f).read_text())
        conn.execute("""CREATE TABLE asset_freshness (
            asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE, scope_key text NOT NULL, partition_key text NOT NULL,
            freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')), reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
            receipt_version text NOT NULL, observed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (asset_id, scope_key, partition_key))""")
        m596 = (PLATFORM / "supabase/migrations/596_nirmana_provenance_receipts.sql").read_text()
        end = "EXECUTE FUNCTION nirmana_invalidate_registry_receipts();"
        conn.execute(m596[m596.index("CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()"):m596.index(end) + len(end)])
        rows = [(w["asset_id"], w["registry_before_s"]) for w in AUDIT["writers"] if w["registry_before_s"] is not None]
        rows += [(f"b1408_neighbour_{i}", t) for i, t in enumerate([120, 600, 10800])]      # a wrong WHERE on the value alone would catch these
        for i, (asset_id, budget) in enumerate(rows):
            conn.execute(
                "INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active,"
                " depends_on, writer_timeout_seconds, has_writer, asset_type, layer_name, layer_index, catalog_status, asset_kind)"
                " VALUES (%s,'kala',%s,'n','n','d','postgres_table','per_chart',true,'{}',%s,true,'data','Kala',3,'DRAFT','data')",
                (asset_id, 900 + i, budget))
        conn.execute("INSERT INTO asset_freshness (asset_id, scope_key, partition_key, freshness_state, receipt_version) VALUES (%s,'k','p','fresh','v')", (TARGET,))
    return isolated_kala_db_dsn


@pytest.fixture
def conn(registry_dsn):
    with psycopg.connect(registry_dsn) as c:
        yield c
        c.rollback()


def _snapshot(c):
    return dict(c.execute("SELECT asset_id, row_to_json(r)::text FROM asset_registry r ORDER BY asset_id").fetchall())


def _timeout(c, asset_id=TARGET):
    return c.execute("SELECT writer_timeout_seconds FROM asset_registry WHERE asset_id = %s", (asset_id,)).fetchone()[0]


def _ctid(c):
    return c.execute("SELECT ctid::text FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]


def test_precondition_is_the_production_row(conn):
    assert _timeout(conn) == 120


def test_a_migration_sets_600_and_changes_nothing_else(conn):
    before = _snapshot(conn)
    conn.execute(_migration_sql())
    assert _timeout(conn) == 600
    after = _snapshot(conn)
    assert after[TARGET] == before[TARGET].replace('"writer_timeout_seconds":120', '"writer_timeout_seconds":600')
    assert {k: v for k, v in after.items() if k != TARGET} == {k: v for k, v in before.items() if k != TARGET}
    assert conn.execute("SELECT freshness_state FROM asset_freshness WHERE asset_id = %s", (TARGET,)).fetchall() == [("fresh",)]


def test_b_rerun_is_idempotent_and_writes_nothing(conn):
    conn.execute(_migration_sql())
    before, ctid = _snapshot(conn), _ctid(conn)
    conn.execute(_migration_sql())                       # second application: the row already reads 600
    assert _snapshot(conn) == before
    assert _ctid(conn) == ctid                           # the tuple was not rewritten (an UPDATE would have moved it)


def test_b_row_already_at_the_seed_value_is_left_alone(conn):
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = 600 WHERE asset_id = %s", (TARGET,))
    before, ctid = _snapshot(conn), _ctid(conn)
    conn.execute(_migration_sql())
    assert (_snapshot(conn), _ctid(conn)) == (before, ctid)


@pytest.mark.parametrize("prior", [300, 601, 10800])      # the column is NOT NULL, so NULL cannot occur on a real row
def test_b_migration_refuses_any_other_prior_value(conn, prior):
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = %s WHERE asset_id = %s", (prior, TARGET))
    before = _snapshot(conn)
    with pytest.raises(psycopg.errors.RaiseException, match=r"1408: refusing to change ka_vedha_gochara"):
        conn.execute(_migration_sql())
    conn.rollback()
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = %s WHERE asset_id = %s", (prior, TARGET))
    assert _snapshot(conn) == before


def test_b_migration_refuses_when_the_row_is_absent(conn):
    conn.execute("DELETE FROM asset_freshness WHERE asset_id = %s", (TARGET,))
    conn.execute("DELETE FROM asset_registry WHERE asset_id = %s", (TARGET,))
    with pytest.raises(psycopg.errors.RaiseException, match=r"1408: ka_vedha_gochara has no asset_registry row"):
        conn.execute(_migration_sql())


def test_c_seed_declares_the_value_the_migration_writes():
    seed = SEED.read_text()
    block = seed[seed.index(f"asset_id: '{TARGET}',"):]
    block = block[:block.index("\n  },")]
    declared = re.search(r"^\s+writer_timeout_seconds: (\d+),", block, re.M)
    assert declared is not None, "the seed must declare ka_vedha_gochara's budget explicitly (the implicit default is not a pin)"
    assert int(declared.group(1)) == _migration_value() == WRITERS[TARGET]["registry_after_s"] == 600


def test_d_audit_covers_every_required_writer_and_its_arithmetic_is_honest():
    assert set(WRITERS) == REQUIRED_AUDITED
    for w in WRITERS.values():
        if w["measured_wall_s"] is None:
            assert w["kind"] == "NOT_MEASURED" and w["two_x_s"] is None, w["asset_id"]
            assert w["registry_after_s"] == w["registry_before_s"], f"{w['asset_id']}: no measurement, so the budget must be left alone"
        else:
            assert w["two_x_s"] == pytest.approx(2 * w["measured_wall_s"], abs=0.01), w["asset_id"]
            if w.get("observations_s"):
                assert w["measured_wall_s"] == max(w["observations_s"]), w["asset_id"]


def test_d_no_audited_writer_is_below_twice_its_measured_wall_after_the_migration(conn):
    conn.execute(_migration_sql())
    for w in WRITERS.values():
        if w["registry_before_s"] is None:
            continue                                               # production value recorded in no source; nothing to read
        budget = _timeout(conn, w["asset_id"])
        assert budget == w["registry_after_s"], f"{w['asset_id']}: registry reads {budget}, audit says {w['registry_after_s']}"
        if w["measured_wall_s"] is not None:
            assert budget >= 2 * w["measured_wall_s"], f"{w['asset_id']}: budget {budget} s < 2 x measured {w['measured_wall_s']} s"
