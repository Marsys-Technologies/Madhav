"""
tests/test_migration_862_kala_darshana_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 862 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_kala_darshana`
(target_floor 750 was already a genuine achieved-count floor; only the
derivation was undocumented).

`ka_kala_darshana` is a top-N-of-qualifying asset — the same shape as
ka_bhavishya_lekha (migration 857), simpler: LEAST(750, count of
kala_convergence rows for this chart), no additional filter.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed) that independently re-derive the eligible-pool count from
kala_convergence directly, not trusted from the migration's own claim.
"""
from __future__ import annotations

import json
import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "862_nirmana_l3_w3_kala_darshana_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 862 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_862_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_kala_darshana'" in updates[0]


def test_migration_862_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_862_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_862_cap_and_observed_are_consistent():
    sql = _read_migration()
    assert "'cap', 750" in sql
    assert "'eligible_convergence_rows', 14868" in sql
    assert "'served_rows', 750" in sql
    assert min(750, 14868) == 750


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
def test_migration_862_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves LEAST(750, live
    kala_convergence row count) matches what the asset's own live count_sql
    produces for the canonical chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_kala_darshana'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_kala_darshana not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        # Independently re-derive the eligible pool — not trusted from the migration's
        # own recorded number, re-queried from kala_convergence directly.
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_convergence WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            eligible_row = cur.fetchone()
        if eligible_row is None:
            pytest.skip("kala_convergence has no rows for the canonical chart in this environment")
        live_eligible = eligible_row["n"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_darshana WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            served_row = cur.fetchone()
        if served_row is None or served_row["n"] == 0:
            pytest.skip("kala_darshana has no rows for the canonical chart in this environment")
        live_served = served_row["n"]

        assert live_served == min(750, live_eligible), (
            f"live served count {live_served} != LEAST(750, live eligible {live_eligible})"
        )
        assert live_served == row["target_floor"]
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_862_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_kala_darshana'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_kala_darshana not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_kala_darshana'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
