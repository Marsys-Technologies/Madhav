"""Real CDLM SQL/digest qualification on an explicitly opted-in scratch database.

Run with MADHAV_CDLM_TEST_DSN pointing to test_cdlm in scratch.noindex. No
production connection or private chart inputs are used by this fixture.
"""
from __future__ import annotations

import json
import os
import re
from itertools import permutations
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from psycopg.rows import dict_row

from pipeline.orchestrator.output_digest import _validate_spec, compute_output_digest
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bo_cdlm_summary import BoCdlmSummaryWriter, CANONICAL_AYAS

PLATFORM = Path(__file__).resolve().parents[3]
MIGRATION = PLATFORM / "supabase/migrations/1416_bo_cdlm_summary_three_table_receipts.sql"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
TABLES = ("bodha_cdlm_chart_summary", "bodha_cdlm_domain_rollups", "bodha_cdlm_pattern_clusters")


def _new_spec():
    match = re.search(r"VALUES\s*\(\s*'bo_cdlm_summary',\s*'([a-f0-9]{64})',\s*'(\{.*?\})'::jsonb", MIGRATION.read_text(), re.S)
    assert match, "forward migration must carry the reviewed spec"
    sha, raw = match.groups()
    spec = json.loads(raw)
    _validate_spec("bo_cdlm_summary", spec, sha)
    return sha, spec


def test_full_receipt_declares_all_three_tables_and_preserves_execution_exclusions():
    _, spec = _new_spec()
    assert [c["relation"] for c in spec["components"]] == list(TABLES)
    for component in spec["components"]:
        assert component["where_equals"] == {"chart_id": CHART}
        assert {"chart_id", "ayanamsha_id", "snapshot_type"} <= set(component["key_columns"])
        assert not {"summary_id", "rollup_id", "pattern_id", "build_id", "computed_at"} & set(component["value_columns"])


@pytest.fixture(params=[1, 5], ids=["applied-358-floor", "disclosed-358-source-replay"])
def db(request):
    dsn = os.environ.get("MADHAV_CDLM_TEST_DSN")
    if not dsn:
        pytest.skip("requires explicitly opted-in scratch PostgreSQL")
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        assert conn.info.dbname == "test_cdlm"
        directory = conn.execute("SHOW data_directory").fetchone()["data_directory"]
        assert directory.startswith("/Users/Dev/scratch.noindex/codex/madhav/")
        conn.execute("CREATE TABLE asset_registry (asset_id text PRIMARY KEY, natural_key_partition text, target_floor bigint, count_sql text)")
        conn.execute("INSERT INTO asset_registry VALUES ('bo_cdlm_summary', NULL, 1, 'SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1')")
        conn.execute("UPDATE asset_registry SET target_floor=%s", [request.param])
        # Use the actual source DDL, including UUID array types and NOT NULLs.
        ddl = (PLATFORM / "migrations/325_l2_bodha_enriched_schema.sql").read_text()
        for table in ("bodha_cdlm_cells", *TABLES):
            match = re.search(rf"CREATE TABLE {table} \(.*?\n\);", ddl, re.S)
            assert match
            conn.execute(match.group())
        digest_ddl = (PLATFORM / "supabase/migrations/598_nirmana_output_digest_specs.sql").read_text()
        conn.execute(digest_ddl.split("ALTER TABLE asset_provenance_receipts", 1)[0])
        conn.execute((PLATFORM / "migrations/986_nirmana_l2_bo_cdlm_summary_output_digest_spec.sql").read_text())
        conn.execute((PLATFORM / "migrations/987_nirmana_l2_bo_cdlm_summary_natural_key_partition.sql").read_text())
        conn.execute((PLATFORM / "migrations/1297_bo_cdlm_summary_count_sql_three_tables.sql").read_text())
        # Install the actual invalidation function and trigger from 596, using
        # only the small registry/freshness schema needed by this fixture.
        for column in ("depends_on", "health_probe", "integrity_check_sql", "asset_kind", "asset_type", "scope", "has_writer", "is_active", "target_table"):
            conn.execute(f"ALTER TABLE asset_registry ADD COLUMN {column} text")
        conn.execute("CREATE TABLE asset_freshness (asset_id text, freshness_state text, reasons jsonb, observed_at timestamptz)")
        conn.execute("INSERT INTO asset_freshness VALUES ('bo_cdlm_summary','fresh','[]',now())")
        invalidation = (PLATFORM / "supabase/migrations/596_nirmana_provenance_receipts.sql").read_text()
        start = invalidation.index("CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()")
        end = invalidation.index("CREATE OR REPLACE FUNCTION nirmana_invalidate_chart_receipts()")
        conn.execute(invalidation[start:end])
        yield conn
        # Fixtures, forward changes and outputs remain caller-transaction-owned.
        conn.rollback()


def _inputs(conn, order):
    conn.execute("DELETE FROM bodha_cdlm_cells")
    partners = ("health", "residence", "travel", "wealth")
    for aya_index, aya in enumerate(CANONICAL_AYAS):
        for index in order:
            conn.execute("""INSERT INTO bodha_cdlm_cells
              (cell_id,chart_id,ayanamsha_id,build_id,snapshot_type,domain_row,domain_col,
               shared_signal_count,shared_factor_count,unique_signals_row_domain,
               unique_signals_col_domain,shared_signal_salience_sum,positive_contribution,
               negative_contribution,net_linkage_strength,computed_linkage_strength,
               linkage_formula_version,contradicting_signal_pairs_count,
               cross_domain_contradiction_flag,asymmetric_linkage_flag,asymmetry_score,
               domain_relationship_class,shared_signal_ids_array,msr_salience_version_used,
               verification_pass_status,citation_ref,citation_human,computed_at,engine_version)
              VALUES (%s,%s,%s,%s,'static_natal','career',%s,
                1,0,0,0,1,1,0,1,1,'toy-v1',0,false,false,0,%s,%s,
                'toy-v1','unverified','open-toy','open toy cells',now(),'toy-v1')""",
              (UUID(int=100 + aya_index * 4 + index), CHART, aya, UUID(int=1),
               partners[index], "inverse" if index == 3 else "positive_strong",
               [UUID(int=200 + index)]))


def _run(conn, build):
    return BoCdlmSummaryWriter().run(ContextSpec(
        asset_id="bo_cdlm_summary", build_id=str(UUID(int=build)),
        db_conn=conn, config={"chart_id": CHART},
    ))


def _digest(conn):
    with conn.cursor() as cur:
        return compute_output_digest(cur, asset_id="bo_cdlm_summary")


def test_real_writer_is_order_invariant_idempotent_and_all_siblings_are_hashed(db):
    old_floor = db.execute("SELECT target_floor FROM asset_registry").fetchone()["target_floor"]
    db.execute(MIGRATION.read_text())
    # Forward declarations must be replay-safe without rewriting historical specs.
    db.execute(MIGRATION.read_text())
    history = db.execute("SELECT spec_sha256,retired_at FROM asset_output_digest_specs ORDER BY reviewed_at,spec_sha256").fetchall()
    assert len(history) == 2
    assert sum(row["retired_at"] is None for row in history) == 1
    assert db.execute("SELECT target_floor FROM asset_registry").fetchone()["target_floor"] == old_floor
    freshness = db.execute("SELECT freshness_state,reasons FROM asset_freshness").fetchone()
    assert freshness == {"freshness_state": "stale", "reasons": ["registry_changed"]}
    baseline = None
    for build, order in enumerate(permutations(range(4)), start=10):
        _inputs(db, order)
        result = _run(db, build)
        assert result.rows_inserted == 40  # 5 summaries + 25 domains + 10 classes
        assert [db.execute(f"SELECT count(*) n FROM {table}").fetchone()["n"] for table in TABLES] == [5, 25, 10]
        summary = db.execute("SELECT * FROM bodha_cdlm_chart_summary ORDER BY ayanamsha_id LIMIT 1").fetchone()
        assert summary["total_chart_linkage"] == 4
        assert summary["dominant_3_domains_array"] == ["career", "health", "residence"]
        assert summary["pattern_cluster_markers_jsonb"]["strongest_pair"] == {"domain_a": "career", "domain_b": "health", "strength": 1.0}
        rollup = db.execute("SELECT * FROM bodha_cdlm_domain_rollups WHERE domain='career' ORDER BY ayanamsha_id LIMIT 1").fetchone()
        assert rollup["top_3_linked_domains_jsonb"] == [{"domain": d, "strength": 1.0} for d in ("health", "residence", "travel")]
        digest = _digest(db)
        assert digest[0] is not None
        baseline = baseline or digest
        assert digest == baseline
    for table, field in zip(TABLES, ("total_chart_linkage", "total_inbound_linkage", "cluster_strength_total")):
        db.execute("SAVEPOINT mutation")
        db.execute(f"UPDATE {table} SET {field}={field}+1")
        assert _digest(db) != baseline, f"receipt omitted {table}"
        db.execute("ROLLBACK TO SAVEPOINT mutation")
        assert _digest(db) == baseline
    db.execute("SAVEPOINT failed_writer")
    db.execute("""CREATE FUNCTION reject_rollup() RETURNS trigger LANGUAGE plpgsql AS
      $$ BEGIN RAISE EXCEPTION 'intentional fixture failure'; END $$""")
    db.execute("CREATE TRIGGER reject_rollup BEFORE INSERT ON bodha_cdlm_domain_rollups FOR EACH ROW EXECUTE FUNCTION reject_rollup()")
    with pytest.raises(psycopg.errors.RaiseException, match="intentional fixture failure"):
        _run(db, 99)
    db.execute("ROLLBACK TO SAVEPOINT failed_writer")
    assert _digest(db) == baseline  # all deletes/partial writes rolled back together


@pytest.mark.parametrize("drift", [
    "UPDATE asset_registry SET target_floor=7",
    "UPDATE asset_registry SET count_sql='SELECT 0'",
    "UPDATE asset_registry SET natural_key_partition='unreviewed'",
    "UPDATE asset_output_digest_specs SET spec_sha256=repeat('0',64)",
])
def test_unreviewed_baseline_refuses_without_retiring_history(db, drift):
    db.execute(drift)
    before = db.execute("SELECT * FROM asset_output_digest_specs").fetchall()
    with pytest.raises(psycopg.errors.RaiseException):
        with db.transaction():
            db.execute(MIGRATION.read_text())
    assert db.execute("SELECT * FROM asset_output_digest_specs").fetchall() == before
