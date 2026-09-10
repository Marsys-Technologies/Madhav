"""
tests/test_migration_858_jivana_parva_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 858 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_jivana_parva`
(target_floor 100 was already a genuine achieved-count floor; only the
derivation was undocumented).

`ka_jivana_parva` is a three-level (MD/AD/PD) birth- and time-clipped sum,
NOT a top-N cap like ka_bhavishya_lekha's coincidentally-identical 100
(migration 857). The migration also corrects a stale inline comment in the
writer itself (claims ~9 PD rows; the actual filter returns only the single
PD spanning build time) — this file asserts that correction is present and
independently re-verifies the PD filter's real behavior live.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed).
"""
from __future__ import annotations

import json
import os
import re
from datetime import date

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "858_nirmana_l3_w3_jivana_parva_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 858 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_858_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_jivana_parva'" in updates[0]


def test_migration_858_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_858_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_858_documents_the_stale_pd_comment_correction():
    sql = _read_migration()
    assert "stale" in sql.lower()
    assert "'md', 10" in sql
    assert "'ad', 89" in sql
    assert "'pd', 1" in sql
    assert "'total', 100" in sql
    assert 10 + 89 + 1 == 100


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
def test_migration_858_pd_filter_returns_at_most_one_row_live():
    """Independently re-verifies the claim this migration makes about the
    writer's REAL behavior (not its stale comment): the level_n=3 query,
    filtered to spans covering as_of_date, returns at most one row for the
    canonical chart today — not the ~9 the writer's own inline comment
    claims."""
    conn = _live_conn_or_skip()
    today = date.today()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM chart_dashas
                WHERE chart_id = %s AND level_n = 3
                  AND system_id = 'vimshottari' AND ayanamsha_id = 'lahiri_chitrapaksha'
                  AND start_date <= %s AND end_date >= %s
                """,
                (_CANONICAL_CHART_ID, today, today),
            )
            row = cur.fetchone()
        if row is None:
            pytest.skip("chart_dashas has no level_n=3 rows for the canonical chart in this environment")
        assert row["n"] <= 1, f"expected at most 1 PD row spanning today, got {row['n']}"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_858_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    per-level breakdown sums to the live count_sql result for the canonical
    chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_jivana_parva'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_jivana_parva not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]
        assert recorded_total == observed["md"] + observed["ad"] + observed["pd"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_jivana_parva WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_jivana_parva has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_858_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_jivana_parva'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_jivana_parva not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_jivana_parva'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
