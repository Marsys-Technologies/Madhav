"""SR-K9-ADMITTED-ZERO: migration 1409 sets asset_registry.target_floor of ka_sangam (14868) and ka_vighnakara (536) to the achieved count 0 (CLAUDE.md N.4).

Real SQL on the guarded disposable cluster, registry replayed from the real baseline DDL and the real migration-596 invalidation trigger (same recipe as
test_writer_budgets_1408.py). Nothing is golden-captured: the prior values are the production floors named in migrations 856 / 866, the target 0 is the ruling.

Claims, one oracle each:
  (a) on the registry as production holds it the migration sets BOTH floors to 0, touches no other column and no other row;
  (b) the trigger effect is exactly what the migration header states: the freshness rows of those two assets (only) turn stale with reason 'registry_changed';
  (c) a replay changes nothing (the rows are not even rewritten, so the trigger does not fire again); an already-landed row is left alone;
  (d) it refuses an absent row and any value other than the expected prior / 0;
  (e) the seed declares target_floor 0 for both assets (seed / migration drift);
  (f) the migration is data-only: no DDL, no destructive statement.
"""
import os
import re
from pathlib import Path

import psycopg
import pytest

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parents[4] / "platform"
M1409 = Path(os.environ.get("K9_FLOORS_1409_SQL") or PLATFORM / "migrations/1409_k9_floors_achieved_zero.sql")
SEED = Path(os.environ.get("K9_FLOORS_1409_SEED") or PLATFORM / "scripts/seed/asset_registry_seed.ts")
PRIOR = {"ka_sangam": 14868, "ka_vighnakara": 536}
BASELINE = [
    "supabase/migrations/167_asset_registry.sql", "supabase/migrations/202_asset_registry_service_support.sql",
    "supabase/migrations/223_orchestrator_rebuild_probe_dag.sql", "supabase/migrations/242_l3_service_asset_type.sql",
    "supabase/migrations/342_asset_registry_writer_flags.sql", "supabase/migrations/417_asset_registry_writer_timeout_seconds.sql",
    "migrations/590_nirmana_m0_catalogue_contract_columns.sql", "migrations/591_nirmana_m0_partition_and_dead_flag_columns.sql",
]


def _migration_sql() -> str:
    assert M1409.exists(), f"migration 1409 is not placed at {M1409}"
    return M1409.read_text()


@pytest.fixture(scope="module")
def registry_dsn(isolated_kala_db_dsn):
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
        rows = list(PRIOR.items()) + [("k9_neighbour_floor", 14868), ("k9_neighbour_zero", 0), ("k9_neighbour_536", 536)]   # a WHERE on the value alone would catch these
        for i, (asset_id, floor) in enumerate(rows):
            conn.execute(
                "INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active,"
                " depends_on, target_floor, has_writer, asset_type, layer_name, layer_index, catalog_status, asset_kind)"
                " VALUES (%s,'kala',%s,'n','n','d','postgres_table','per_chart',true,'{}',%s,true,'data','Kala',3,'DRAFT','data')",
                (asset_id, 900 + i, floor))
            conn.execute("INSERT INTO asset_freshness (asset_id, scope_key, partition_key, freshness_state, receipt_version) VALUES (%s,'k','p','fresh','v')", (asset_id,))
    return isolated_kala_db_dsn


@pytest.fixture
def conn(registry_dsn):
    with psycopg.connect(registry_dsn) as c:
        yield c
        c.rollback()


def _snapshot(c):
    return dict(c.execute("SELECT asset_id, row_to_json(r)::text FROM asset_registry r ORDER BY asset_id").fetchall())


def _floor(c, asset_id):
    return c.execute("SELECT target_floor FROM asset_registry WHERE asset_id = %s", (asset_id,)).fetchone()[0]


def _ctids(c):
    return c.execute("SELECT asset_id, ctid::text FROM asset_registry WHERE asset_id = ANY(%s) ORDER BY asset_id", (list(PRIOR),)).fetchall()


def _freshness(c):
    return dict(c.execute("SELECT asset_id, freshness_state FROM asset_freshness ORDER BY asset_id").fetchall())


def test_precondition_is_the_production_rows(conn):
    assert {a: _floor(conn, a) for a in PRIOR} == PRIOR


def test_a_migration_sets_both_floors_to_zero_and_changes_nothing_else(conn):
    before = _snapshot(conn)
    conn.execute(_migration_sql())
    assert {a: _floor(conn, a) for a in PRIOR} == {"ka_sangam": 0, "ka_vighnakara": 0}
    after = _snapshot(conn)
    for asset, prior in PRIOR.items():
        assert after[asset] == before[asset].replace(f'"target_floor":{prior}', '"target_floor":0')
    others = {k for k in before if k not in PRIOR}
    assert {k: after[k] for k in others} == {k: before[k] for k in others}


def test_b_trigger_effect_is_the_stated_one(conn):
    conn.execute(_migration_sql())
    state = _freshness(conn)
    assert state["ka_sangam"] == state["ka_vighnakara"] == "stale"
    assert all(v == "fresh" for k, v in state.items() if k not in PRIOR), "the trigger must stale no other asset"
    reasons = conn.execute("SELECT reasons::text FROM asset_freshness WHERE asset_id = 'ka_sangam'").fetchone()[0]
    assert "registry_changed" in reasons


def test_c_rerun_is_idempotent_and_writes_nothing(conn):
    conn.execute(_migration_sql())
    before, ctids = _snapshot(conn), _ctids(conn)
    conn.execute("UPDATE asset_freshness SET freshness_state = 'fresh'")      # a re-fired trigger would stale these again
    conn.execute(_migration_sql())
    assert _snapshot(conn) == before and _ctids(conn) == ctids                 # the tuples were not rewritten
    assert set(_freshness(conn).values()) == {"fresh"}


def test_c_one_row_already_landed_is_left_alone_and_the_other_still_moves(conn):
    conn.execute("UPDATE asset_registry SET target_floor = 0 WHERE asset_id = 'ka_sangam'")
    sangam_ctid = dict(_ctids(conn))["ka_sangam"]
    conn.execute(_migration_sql())
    assert _floor(conn, "ka_vighnakara") == 0 and dict(_ctids(conn))["ka_sangam"] == sangam_ctid


@pytest.mark.parametrize("asset,prior", [("ka_sangam", 536), ("ka_sangam", 1), ("ka_vighnakara", 14868), ("ka_vighnakara", 537)])
def test_d_migration_refuses_any_other_prior_value(conn, asset, prior):
    conn.execute("UPDATE asset_registry SET target_floor = %s WHERE asset_id = %s", (prior, asset))
    before = _snapshot(conn)
    with pytest.raises(psycopg.errors.RaiseException, match=rf"1409: refusing to change {asset}"):
        conn.execute(_migration_sql())
    conn.rollback()
    conn.execute("UPDATE asset_registry SET target_floor = %s WHERE asset_id = %s", (prior, asset))
    assert _snapshot(conn) == before


def test_d_migration_refuses_a_null_floor(conn):
    conn.execute("UPDATE asset_registry SET target_floor = NULL WHERE asset_id = 'ka_vighnakara'")
    with pytest.raises(psycopg.errors.RaiseException, match=r"1409: refusing to change ka_vighnakara: target_floor is NULL"):
        conn.execute(_migration_sql())


def test_d_migration_refuses_when_a_row_is_absent(conn):
    conn.execute("DELETE FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
    with pytest.raises(psycopg.errors.RaiseException, match=r"1409: ka_vighnakara has no asset_registry row"):
        conn.execute(_migration_sql())


def test_e_seed_declares_zero_for_both_assets():
    seed = SEED.read_text()
    for asset in PRIOR:
        block = seed[seed.index(f"asset_id: '{asset}',"):]
        block = block[:block.index("\n  },")]
        declared = re.search(r"^\s+target_floor: (\w+),", block, re.M)
        assert declared is not None and declared.group(1) == "0", f"{asset}: the seed must declare target_floor 0 (migration 1409)"


def test_f_migration_is_data_only_with_no_destructive_statement():
    code = "\n".join(line for line in _migration_sql().splitlines() if not line.strip().startswith("--"))
    assert not re.search(r"\b(CREATE|ALTER|DROP|TRUNCATE|DELETE\s+FROM|INSERT\s+INTO|GRANT|REVOKE)\b", code, re.I)
    assert len(re.findall(r"\bUPDATE\s+asset_registry\b", code)) == 1 and "SET target_floor = 0" in code


def test_g_post_apply_verification_readback(conn, capsys):
    """The migration header's post-apply verification, run for real (shown with -s): both floors 0, active, writer present; stale freshness; replay is a no-op."""
    conn.execute(_migration_sql())
    rows = conn.execute("SELECT asset_id, target_floor, is_active, has_writer FROM asset_registry WHERE asset_id IN ('ka_sangam','ka_vighnakara') ORDER BY asset_id").fetchall()
    print("POST-APPLY asset_registry:", rows, "| asset_freshness:", _freshness(conn))
    assert rows == [("ka_sangam", 0, True, True), ("ka_vighnakara", 0, True, True)]
    conn.execute(_migration_sql())                                            # replay inside the same transaction: NOTICE path, nothing raised
    assert [r[1] for r in conn.execute("SELECT asset_id, target_floor FROM asset_registry WHERE asset_id IN ('ka_sangam','ka_vighnakara') ORDER BY asset_id").fetchall()] == [0, 0]
