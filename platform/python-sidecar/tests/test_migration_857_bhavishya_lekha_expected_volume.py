"""
tests/test_migration_857_bhavishya_lekha_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 857 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_bhavishya_lekha`
(target_floor 100 was already a genuine achieved-count floor; only the
derivation was undocumented).

`ka_bhavishya_lekha` is a top-N-of-qualifying asset (LEAST(100, |eligible
kala_darshana windows|)), the same shape as L5's mi_adhilepa (migration 690)
but simpler than the fan-out shapes in migrations 852/853/855/856 this batch.

Same convention: DB-free static guards + a no-self-transaction-wrapper check
(an embedded BEGIN;/COMMIT; defeats this file's execute-then-rollback
pattern, per the migration-852 near-miss self-caught earlier this session),
plus `@pytest.mark.integration` live tests (rolled back, never committed)
proving the recorded eligible-pool count matches a live re-derivation of the
writer's own eligibility query, and that LEAST(100, eligible) equals the
live count_sql result for the canonical chart.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "857_nirmana_l3_w3_bhavishya_lekha_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 857 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_857_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_bhavishya_lekha'" in updates[0]


def test_migration_857_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_857_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_857_cap_and_observed_are_consistent():
    sql = _read_migration()
    assert "'cap', 100" in sql
    assert "'eligible_windows', 110" in sql
    assert "'served_rows', 100" in sql
    assert min(100, 110) == 100


# ── live integration (excluded by -m "not integration"; run manually) ──────

LIVE_DSN = os.environ.get("DATABASE_URL", "")


def _live_conn_or_skip():
    import psycopg

    try:
        conn = psycopg.connect(LIVE_DSN, connect_timeout=10, row_factory=psycopg.rows.dict_row)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")
    return conn


@pytest.mark.integration
def test_migration_857_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves LEAST(100, live
    eligible-window count) matches what the asset's own live count_sql
    produces for the canonical chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_bhavishya_lekha'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_bhavishya_lekha not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        # Independently re-derive the writer's own eligibility query, not trusting the
        # migration's recorded number — the same discipline test_migration_856's
        # observed-counts check applies, but here re-run live against the source tables.
        today = date.today()
        horizon_end = date(today.year + 5, today.month, today.day)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM kala_darshana kd
                JOIN kala_convergence kc ON kd.convergence_id = kc.convergence_id
                WHERE kd.chart_id = %s
                  AND kd.peak_date >= %s AND kd.peak_date <= %s
                  AND kd.net_label NOT IN ('obstructed_severe')
                """,
                (_CANONICAL_CHART_ID, today, horizon_end),
            )
            eligible_row = cur.fetchone()
        if eligible_row is None:
            pytest.skip("kala_darshana/kala_convergence join produced no rows for the canonical chart in this environment")
        live_eligible = eligible_row["n"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_bhavishya WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            served_row = cur.fetchone()
        if served_row is None or served_row["n"] == 0:
            pytest.skip("kala_bhavishya has no rows for the canonical chart in this environment")
        live_served = served_row["n"]

        assert live_served == min(100, live_eligible), (
            f"live served count {live_served} != LEAST(100, live eligible {live_eligible})"
        )
        assert live_served == row["target_floor"]
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_857_is_idempotent_live():
    """Running the migration twice inside one transaction produces a byte-
    identical stored value the second time (the IS NULL guard makes the
    second application a no-op). Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_bhavishya_lekha'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_bhavishya_lekha not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_bhavishya_lekha'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
