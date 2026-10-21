"""K8 registry edge (SR-K8-EDGE-1403): migration 1403 adds bg_dignity_reference to ka_gochara_v5.depends_on.

Real SQL on the guarded disposable cluster. The registry is replayed from the real migrations over the baseline DDL (the real 1243 insert, 1304,
1395 and the real K8-REG 1392 over a stub row for every seed asset), together with the REAL migration-596 receipt/freshness tables and trigger, so the
row under test is the row production holds after 1392, never a hand-built stand-in. Nothing is golden-captured: expected values come from the migration texts.

The migration file is placed under platform/migrations/ by the cockpit; until then KALA_MIGRATION_1403 may name it.

Claims, one oracle each:
  (a) 1403 changes depends_on of ka_gochara_v5 to the 1392 array + bg_dignity_reference and NO other column and NO other registry row;
  (b) 1403 refuses, changing nothing, on any other prior array, an absent row, a missing/inactive/non-global producer and a cycle;
  (c) a re-run writes nothing (a freshness row restored by a governed build is not staled again);
  (d) SERVING EFFECT (surrogate condition, madhav-44): on a prod-shaped DB the ONLY rows that change are the ka_gochara_v5 asset_freshness rows (fresh -> stale,
      registry_changed) and the one registry row: every other table is byte-identical, the real dependency gate (asset_runner.deps_unsatisfied) answers the same for
      every (chart, asset), and the only downstream-closure change is that ka_gochara_v5 joins the closure of bg_dignity_reference;
  (e) the 28-column row fingerprint chain 1395 -> 1392 -> 1403 differs only in depends_on.
"""
import os
import re
import json
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

REPO = Path(__file__).resolve().parents[5]
PLATFORM = REPO / "platform"
SEED = PLATFORM / "scripts/seed/asset_registry_seed.ts"
M1243 = PLATFORM / "migrations/1243_ka_gochara_inert_registry_rows.sql"
M1304 = PLATFORM / "migrations/1304_ka_gochara_v5_registry_row_small_test.sql"
M1395 = PLATFORM / "migrations/1395_ka_gochara_v5_writer_timeout_72000.sql"
M1392 = PLATFORM / "migrations/1392_k8_registry_truth.sql"
M596 = PLATFORM / "supabase/migrations/596_nirmana_provenance_receipts.sql"
TARGET = "ka_gochara_v5"
PRODUCER = "bg_dignity_reference"
BASELINE = [
    "supabase/migrations/167_asset_registry.sql", "supabase/migrations/202_asset_registry_service_support.sql",
    "supabase/migrations/223_orchestrator_rebuild_probe_dag.sql", "supabase/migrations/242_l3_service_asset_type.sql",
    "supabase/migrations/342_asset_registry_writer_flags.sql", "supabase/migrations/417_asset_registry_writer_timeout_seconds.sql",
    "migrations/590_nirmana_m0_catalogue_contract_columns.sql", "migrations/591_nirmana_m0_partition_and_dead_flag_columns.sql",
]
FINGERPRINT_SQL = """md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql,
  target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name,
  layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text)"""
CHART_A = "00000000-0000-4000-8000-0000000000a1"   # stands in for the canonical chart (the only chart the v5 small test may run on)
CHART_B = "00000000-0000-4000-8000-0000000000b2"
SERVED_GENERATION = "candidate:served-head"


def m1403_path() -> Path:
    named = os.environ.get("KALA_MIGRATION_1403")
    if named:
        return Path(named)
    found = sorted((PLATFORM / "migrations").glob("1403_*.sql"))
    assert len(found) == 1, f"exactly one 1403 migration expected under platform/migrations/ (or KALA_MIGRATION_1403), found {[p.name for p in found]}"
    return found[0]


def m1403_text() -> str:
    return m1403_path().read_text()


def m1403_edge() -> dict:
    return json.loads(re.search(r"\$k8_edge\$(.*?)\$k8_edge\$", m1403_text(), re.S)[1])


def seed_ids() -> list[str]:
    return re.findall(r"^    asset_id: '([^']+)'", SEED.read_text(), re.M)


def build_registry(dsn: str) -> None:
    """Baseline DDL + real 596 + a stub row per seed asset + the real 1243, 1304, 1395, 1392 (one transaction each, as migrate.ts applies them)."""
    with psycopg.connect(dsn, autocommit=True) as conn:
        for f in BASELINE:
            conn.execute((PLATFORM / f).read_text())
        conn.execute("""ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS data_disposition text, ADD COLUMN IF NOT EXISTS superseded_by text,
                        ADD COLUMN IF NOT EXISTS clear_tables text[], ADD COLUMN IF NOT EXISTS integrity_check_sql text""")
        # 596 needs charts and build_runs (FKs) and the charts columns its second trigger watches; the tables below are minimal stand-ins for those two only.
        conn.execute("""CREATE TABLE charts (id uuid PRIMARY KEY, birth_date date, birth_time time, birth_lat float, birth_lng float, birth_place text,
                        timezone_id text, name text, subject_name text, preferred_name text)""")
        conn.execute("CREATE TABLE build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid REFERENCES charts(id), state text)")
        conn.execute(M596.read_text())
        # every seed asset except the two rows 1243 inserts gets a stub; ka_* rows are corrected by the real 1392, the rest are plain neighbours
        for n, aid in enumerate(seed_ids()):
            if aid in (TARGET, "ka_gochara_v4_41_candidate"):
                continue
            conn.execute(
                "INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active,"
                " depends_on, writer_timeout_seconds, has_writer, asset_type, layer_name, layer_index, catalog_status, asset_kind)"
                " VALUES (%s,'kala',%s,'n','n','d','postgres_table',%s,true,'{}',600,true,'data','Kala',3,'DRAFT','data')",
                (aid, 1000 + n, "global" if aid.startswith("bg_") else "per_chart"))
        for m in (M1243, M1304, M1395, M1392):
            with conn.transaction():
                conn.execute(m.read_text())
        conn.execute("CREATE TABLE asset_throughput (asset_id text NOT NULL, chart_id uuid, state text NOT NULL, last_built_at timestamptz DEFAULT now())")
        # stand-ins for the served gochara head and generation rows: 1403 has no write path to them, the whole-table comparison proves it
        conn.execute("CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text NOT NULL)")
        conn.execute("CREATE TABLE ka_gochara_eval_window (chart_id uuid NOT NULL, generation text NOT NULL, payload jsonb)")


def populate(conn, v5_charts: list[str]) -> None:
    """Every registry asset is built (lit, proven receipt, fresh) for two charts (global assets once); v5 only on the charts named."""
    conn.execute("INSERT INTO charts (id, name) VALUES (%s,'A'),(%s,'B')", (CHART_A, CHART_B))
    for aid, scope in conn.execute("SELECT asset_id, scope FROM asset_registry ORDER BY asset_id").fetchall():
        charts = [None] if scope == "global" else [CHART_A, CHART_B]
        if aid == TARGET:
            charts = v5_charts
        for chart in charts:
            conn.execute("INSERT INTO asset_throughput (asset_id, chart_id, state) VALUES (%s,%s,'lit')", (aid, chart))
            conn.execute("INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state)"
                         " VALUES (%s,%s,'p','v1','proven')", (aid, chart))
            conn.execute("INSERT INTO asset_freshness (asset_id, chart_id, partition_key, freshness_state, receipt_version) VALUES (%s,%s,'p','fresh','v1')",
                         (aid, chart))
    for chart in (CHART_A, CHART_B):
        conn.execute("INSERT INTO kala_layer_head VALUES (%s,%s)", (chart, SERVED_GENERATION))
        conn.execute("INSERT INTO ka_gochara_eval_window VALUES (%s,%s,'{\"served\":true}'),(%s,'5.0','{\"candidate\":true}')", (chart, SERVED_GENERATION, chart))
        conn.execute("INSERT INTO build_runs (chart_id, state) VALUES (%s,'complete')", (chart,))


@pytest.fixture(scope="module")
def registry_dsn(isolated_kala_db_dsn):
    build_registry(isolated_kala_db_dsn)
    return isolated_kala_db_dsn


@pytest.fixture
def conn(registry_dsn):
    with psycopg.connect(registry_dsn) as c:
        yield c
        c.rollback()


def depends_on(c) -> list[str]:
    return c.execute("SELECT depends_on FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]


def registry_snapshot(c) -> dict:
    return dict(c.execute("SELECT asset_id, row_to_json(r)::text FROM asset_registry r ORDER BY asset_id").fetchall())


def table_hashes(c) -> dict[str, str]:
    """md5 over every row of every public base table (row text, sorted): any write anywhere shows."""
    tables = [r[0] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1")]
    return {t: c.execute(f"SELECT md5(coalesce(string_agg(x::text, E'\\n' ORDER BY x::text), '')) FROM {t} x").fetchone()[0] for t in tables}


def freshness_rows(c) -> dict:
    return {(a, ch, p): (s, json.dumps(r)) for a, ch, p, s, r in c.execute(
        "SELECT asset_id, chart_id::text, partition_key, freshness_state, reasons FROM asset_freshness")}


def test_precondition_is_the_row_1392_leaves(conn):
    edge = m1403_edge()
    assert depends_on(conn) == edge["from"] == ["ga_positions", "ga_dashas", "bg_transit_rules"]


def test_a_migration_adds_the_one_producer_and_changes_nothing_else(conn):
    edge = m1403_edge()
    before = registry_snapshot(conn)
    conn.execute(m1403_text())
    after = registry_snapshot(conn)
    assert depends_on(conn) == edge["to"] == edge["from"] + [PRODUCER]
    changed = {k for k in after if after[k] != before[k]}
    assert changed == {TARGET}
    b, a = json.loads(before[TARGET]), json.loads(after[TARGET])
    assert {k: v for k, v in a.items() if k != "depends_on"} == {k: v for k, v in b.items() if k != "depends_on"}


@pytest.mark.parametrize("setup,message", [
    ("UPDATE asset_registry SET depends_on = '{ga_positions,ga_dashas}' WHERE asset_id = 'ka_gochara_v5'", r"1403: refusing to change ka_gochara_v5"),
    ("UPDATE asset_registry SET depends_on = '{ga_dashas,ga_positions,bg_transit_rules}' WHERE asset_id = 'ka_gochara_v5'", r"1403: refusing to change ka_gochara_v5"),
    ("UPDATE asset_registry SET depends_on = '{ga_positions,ga_dashas,bg_transit_rules,bg_ephemeris}' WHERE asset_id = 'ka_gochara_v5'", r"1403: refusing to change ka_gochara_v5"),
    ("DELETE FROM asset_freshness WHERE asset_id = 'ka_gochara_v5'; DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_v5'", r"1403: ka_gochara_v5 has no asset_registry row"),
    ("UPDATE asset_registry SET is_active = false WHERE asset_id = 'bg_dignity_reference'", r"1403: refusing: producer bg_dignity_reference is missing, inactive"),
    ("UPDATE asset_registry SET scope = 'per_chart' WHERE asset_id = 'bg_dignity_reference'", r"1403: refusing: producer bg_dignity_reference is missing, inactive"),
    ("DELETE FROM asset_freshness WHERE asset_id = 'bg_dignity_reference'; DELETE FROM asset_registry WHERE asset_id = 'bg_dignity_reference'", r"1403: refusing: producer bg_dignity_reference is missing"),
    ("UPDATE asset_registry SET depends_on = '{ka_gochara_v5}' WHERE asset_id = 'bg_dignity_reference'", r"would close a cycle"),
    ("UPDATE asset_registry SET depends_on = '{bo_x}' WHERE asset_id = 'bg_dignity_reference'; "
     "INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope, is_active, depends_on, has_writer, asset_type, layer_name, layer_index, catalog_status, asset_kind)"
     " VALUES ('bo_x','kala',1,'n','n','d','postgres_table','global',true,'{ka_gochara_v5}',true,'data','Kala',3,'DRAFT','data')", r"would close a cycle"),
])
def test_b_migration_refuses_and_changes_nothing(conn, setup, message):
    for statement in setup.split("; "):
        conn.execute(statement)
    before, hashes = registry_snapshot(conn), table_hashes(conn)
    with pytest.raises(psycopg.errors.RaiseException, match=message):
        with conn.transaction():          # a savepoint: the refusal rolls back to the prepared state, which must be untouched
            conn.execute(m1403_text())
    assert registry_snapshot(conn) == before and table_hashes(conn) == hashes


def test_c_a_rerun_writes_nothing(conn):
    populate(conn, [CHART_A])
    conn.execute(m1403_text())
    # a governed ka_gochara_v5 build restores 'fresh' ...
    conn.execute("UPDATE asset_freshness SET freshness_state = 'fresh', reasons = '[]'::jsonb WHERE asset_id = %s", (TARGET,))
    xmin_before = conn.execute("SELECT xmin::text FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]
    snapshot = registry_snapshot(conn)
    conn.execute(m1403_text())             # ... and applying 1403 again must not stale it a second time
    assert conn.execute("SELECT freshness_state FROM asset_freshness WHERE asset_id = %s", (TARGET,)).fetchall() == [("fresh",)]
    assert conn.execute("SELECT xmin::text FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0] == xmin_before
    assert registry_snapshot(conn) == snapshot


@pytest.mark.parametrize("v5_charts", [[CHART_A], [CHART_A, CHART_B]], ids=["pinned_chart_only", "worst_case_every_chart"])
def test_d_serving_effect_only_the_v5_freshness_rows_move(conn, v5_charts):
    from pipeline.orchestrator.asset_runner import compute_downstream_closure, deps_unsatisfied
    populate(conn, v5_charts)
    cur = conn.cursor(row_factory=dict_row)
    gate = lambda: {(a, ch): deps_unsatisfied(cur, ch, a) for a, ch in conn.execute(
        "SELECT asset_id, chart_id::text FROM asset_throughput").fetchall()}
    fresh_before, hashes_before, gate_before = freshness_rows(conn), table_hashes(conn), gate()
    closure_before = compute_downstream_closure(cur, PRODUCER)
    conn.execute(m1403_text())
    fresh_after, hashes_after, gate_after = freshness_rows(conn), table_hashes(conn), gate()
    closure_after = compute_downstream_closure(cur, PRODUCER)
    # (chart, asset, generation=partition) rows whose freshness reads differently: exactly the v5 rows, fresh -> stale with registry_changed
    moved = {k for k in fresh_after if fresh_after[k] != fresh_before[k]}
    assert moved == {(TARGET, c, "p") for c in v5_charts}
    assert all(fresh_before[k][0] == "fresh" and fresh_after[k] == ("stale", '["registry_changed"]') for k in moved)
    # every table except the two the trigger/UPDATE own is byte-identical: receipts, throughput, served head, generation rows, runs, charts, every other registry row
    changed_tables = {t for t in hashes_after if hashes_after[t] != hashes_before[t]}
    assert changed_tables == {"asset_registry", "asset_freshness"}
    # the real hard dependency gate answers identically for every (asset, chart); v5's new upstream is lit and fresh
    assert gate_after == gate_before
    # downstream closure of the new upstream: v5 joins it, nothing leaves
    assert set(closure_after) == set(closure_before) | {TARGET}
    assert TARGET not in closure_before


def test_e_fingerprint_chain_differs_only_in_depends_on(conn):
    fp = lambda: conn.execute(f"SELECT {FINGERPRINT_SQL} FROM asset_registry WHERE asset_id = %s", (TARGET,)).fetchone()[0]
    after_1392 = fp()
    # the pre-1392 depends_on (the 1304 pair) restores the stage the 1395 header pins: the fixture reproduces 8339e7ad... from the real 1243 -> 1304 -> 1395 -> 1392
    conn.execute("UPDATE asset_registry SET depends_on = '{ga_positions,ga_dashas}' WHERE asset_id = %s", (TARGET,))
    after_1395 = fp()
    conn.execute("UPDATE asset_registry SET depends_on = %s WHERE asset_id = %s", (m1403_edge()["from"], TARGET))
    conn.execute(m1403_text())
    after_1403 = fp()
    assert (after_1395, after_1392, after_1403) == ("8339e7adcbc90d0c62f50c4e62815b33", "4806fad946bdc9b90f378e138278478c", "97b54242cb98bce22e0300654ba4b660")
