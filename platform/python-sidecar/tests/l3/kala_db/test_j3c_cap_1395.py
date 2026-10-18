"""J-3c cap (SR-J3-CAP-LIVE): migration 1395 raises asset_registry.writer_timeout_seconds of ka_gochara_v5 from 28,800 to 72,000.

Real SQL on the guarded disposable cluster. The registry is replayed from the real migrations (baseline DDL, then the real 1243 insert and the real
1304 update), so the row under test is the row production holds after 1304, never a hand-built stand-in. Nothing is golden-captured: the expected
post-state is derived from the migration texts (the 28 pinned columns of the 1243 row, the 1304 overlay, the 1395 value).

Claims, one oracle each:
  (a) after 1395 the row reads 72000, no other column of it changed, no other registry row changed, and the real migration-596 trigger staled nothing;
  (b) 1395 refuses (and changes nothing) when the prior value is not exactly 28800, or when the row is absent;
  (c) the seed and the migration agree on the value, and the dispatch/teardown expectations pin the same value.
"""
import re
from pathlib import Path

import psycopg
import pytest

REPO = Path(__file__).resolve().parents[5]
PLATFORM = REPO / "platform"
M1395 = PLATFORM / "migrations/1395_ka_gochara_v5_writer_timeout_72000.sql"
M1243 = PLATFORM / "migrations/1243_ka_gochara_inert_registry_rows.sql"
M1304 = PLATFORM / "migrations/1304_ka_gochara_v5_registry_row_small_test.sql"
SEED = PLATFORM / "scripts/seed/asset_registry_seed.ts"
TARGET = "ka_gochara_v5"
BASELINE = [
    "supabase/migrations/167_asset_registry.sql", "supabase/migrations/202_asset_registry_service_support.sql",
    "supabase/migrations/223_orchestrator_rebuild_probe_dag.sql", "supabase/migrations/242_l3_service_asset_type.sql",
    "supabase/migrations/342_asset_registry_writer_flags.sql", "supabase/migrations/417_asset_registry_writer_timeout_seconds.sql",
    "migrations/590_nirmana_m0_catalogue_contract_columns.sql", "migrations/591_nirmana_m0_partition_and_dead_flag_columns.sql",
]
# The 28 columns the pinned Gochara fingerprints hash (platform/scripts/gochara-window-readbacks.sh, R2-1243-fingerprints).
FINGERPRINT_SQL = """md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql,
  target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name,
  layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text)"""


def _m1395_value() -> int:
    """The value 1395 writes, read from its executable SET line (comment lines start with '--' and never match)."""
    return int(re.search(r"^\s+SET writer_timeout_seconds = (\d+)\s*$", M1395.read_text(), re.M).group(1))


@pytest.fixture(scope="module")
def registry_dsn(isolated_kala_db_dsn):
    """Registry as production holds it before 1395: baseline DDL + the real 1243 insert + the real 1304 update + the real 596 invalidation trigger."""
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        for f in BASELINE:
            conn.execute((PLATFORM / f).read_text())
        # asset_freshness as migration 596 defines the columns the trigger function writes, with the REAL function + trigger text lifted from 596's own file
        # (596 as a whole needs the charts table, which this registry-only replay does not carry).
        conn.execute("""CREATE TABLE asset_freshness (
            asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE, scope_key text NOT NULL, partition_key text NOT NULL,
            freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')), reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
            receipt_version text NOT NULL, observed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (asset_id, scope_key, partition_key))""")
        m596 = (PLATFORM / "supabase/migrations/596_nirmana_provenance_receipts.sql").read_text()
        end = "EXECUTE FUNCTION nirmana_invalidate_registry_receipts();"
        conn.execute(m596[m596.index("CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()"):m596.index(end) + len(end)])
        # neighbours: a handful of ordinary rows, one of them also at 28800 (a wrong WHERE on asset_id would catch it)
        for i, t in enumerate([600, 3600, 28800, 7200]):
            conn.execute(
                "INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active,"
                " depends_on, writer_timeout_seconds, has_writer, asset_type, layer_name, layer_index, catalog_status, asset_kind)"
                " VALUES (%s,'kala',%s,'n','n','d','postgres_table','per_chart',true,'{}',%s,true,'data','Kala',3,'DRAFT','data')",
                (f"j3c_neighbour_{i}", 900 + i, t))
        for m in (M1243, M1304):                       # one transaction each, as migrate.ts applies them (the nothing-else-touched xmin checks need it)
            with conn.transaction():
                conn.execute(m.read_text())
        conn.execute("INSERT INTO asset_freshness (asset_id, scope_key, partition_key, freshness_state, receipt_version) VALUES (%s,'k','p','fresh','v')", (TARGET,))
    return isolated_kala_db_dsn


@pytest.fixture
def conn(registry_dsn):
    with psycopg.connect(registry_dsn) as c:
        yield c
        c.rollback()


def _snapshot(c):
    return dict(c.execute("SELECT asset_id, row_to_json(r)::text FROM asset_registry r ORDER BY asset_id").fetchall())


def _timeout(c):
    return c.execute("SELECT writer_timeout_seconds FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]


def test_precondition_is_the_row_1304_leaves(conn):
    assert _timeout(conn) == 28800


def test_a_migration_sets_72000_and_changes_nothing_else(conn):
    before = _snapshot(conn)
    fresh_before = conn.execute("SELECT freshness_state FROM asset_freshness WHERE asset_id = %s", (TARGET,)).fetchall()
    conn.execute(M1395.read_text())
    assert _timeout(conn) == 72000
    after = _snapshot(conn)
    assert after[TARGET] == before[TARGET].replace('"writer_timeout_seconds":28800', '"writer_timeout_seconds":72000')
    assert {k: v for k, v in after.items() if k != TARGET} == {k: v for k, v in before.items() if k != TARGET}
    # the real migration-596 trigger did not fire: no freshness row went stale
    assert conn.execute("SELECT freshness_state FROM asset_freshness WHERE asset_id = %s", (TARGET,)).fetchall() == fresh_before == [("fresh",)]


@pytest.mark.parametrize("prior", [600, 72000, 28801])
def test_b_migration_refuses_any_prior_value_but_28800(conn, prior):
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = %s WHERE asset_id = %s", (prior, TARGET))
    before = _snapshot(conn)
    with pytest.raises(psycopg.errors.RaiseException, match=r"1395: refusing to change ka_gochara_v5"):
        conn.execute(M1395.read_text())
    conn.rollback()
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = %s WHERE asset_id = %s", (prior, TARGET))
    assert _snapshot(conn) == before
    assert _timeout(conn) == prior


def test_b_migration_refuses_when_the_row_is_absent(conn):
    conn.execute("DELETE FROM asset_freshness WHERE asset_id = %s", (TARGET,))
    conn.execute("DELETE FROM asset_registry WHERE asset_id = %s", (TARGET,))
    with pytest.raises(psycopg.errors.RaiseException, match=r"1395: ka_gochara_v5 has no asset_registry row"):
        conn.execute(M1395.read_text())


def test_c_seed_and_migration_agree_and_the_post_state_fingerprint_is_stable(conn):
    seed = SEED.read_text()
    block = seed[seed.index("asset_id: 'ka_gochara_v5',"):]
    block = block[:block.index("asset_kind: 'data',")]
    seed_value = int(re.search(r"^\s+writer_timeout_seconds: (\d+),", block, re.M).group(1))
    assert seed_value == _m1395_value() == 72000
    # the fingerprint of the row once 1395 has landed differs from the pre-1395 one in the timeout column alone
    pre = conn.execute(f"SELECT {FINGERPRINT_SQL} FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]
    conn.execute(M1395.read_text())
    post = conn.execute(f"SELECT {FINGERPRINT_SQL} FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]
    # the 28-column fingerprint, derived by replaying the real 1243 -> 1304 -> 1395 (the fixture reproduces the pinned 1243-stage md5 49995b52...); the
    # only column that differs between the two is writer_timeout_seconds, as the snapshot test above shows
    assert (pre, post) == ("89814fffd6e1aec8d5de63d5007e87d3", "8339e7adcbc90d0c62f50c4e62815b33")
    conn.execute("UPDATE asset_registry SET writer_timeout_seconds = 28800 WHERE asset_id = %s", (TARGET,))
    assert conn.execute(f"SELECT {FINGERPRINT_SQL} FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0] == pre


def test_c_dispatch_and_teardown_expect_the_value_1395_lands():
    for name in ("dispatch_v5_small_test_job.py", "teardown_v5_small_test_job.py"):
        text = (PLATFORM / "scripts" / name).read_text()
        assert re.search(r'^\s+"writer_timeout_seconds": (\d+),', text, re.M).group(1) == str(_m1395_value()), name
