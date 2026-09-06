"""
tests/test_migration_863_kalasutra_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 863 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_kalasutra`
(target_floor 335403 was already a genuine achieved-count floor; only the
derivation was undocumented).

`ka_kalasutra` emits one row per (predicate, matched in-life dasha period)
per CR-109 — NOT one collapsed row per predicate. For the canonical chart
this bimodally splits: 9347 predicates resolve to 1 row, 40757 resolve to
8 rows, summing to 335403.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed) that independently re-derive the bimodal breakdown from
kala_activation/kala_activation_predicates directly, not trusted from the
migration's own recorded numbers.
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
    _REPO_ROOT, "platform", "migrations", "863_nirmana_l3_w3_kalasutra_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 863 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_863_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_kalasutra'" in updates[0]


def test_migration_863_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_863_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_863_bimodal_breakdown_is_internally_consistent():
    sql = _read_migration()
    assert "'total_predicates', 50104" in sql
    assert "'predicates_with_1_row', 9347" in sql
    assert "'predicates_with_8_rows', 40757" in sql
    assert "'total_activation_rows', 335403" in sql
    assert 9347 + 40757 == 50104
    assert 9347 * 1 + 40757 * 8 == 335403


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
def test_migration_863_bimodal_breakdown_matches_live_data():
    """Independently re-derives the per-predicate row-count distribution
    from kala_activation directly — not trusted from the migration's own
    recorded numbers."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT periods_per_predicate, COUNT(*) AS num_predicates FROM (
                    SELECT signal_id, COUNT(*) AS periods_per_predicate
                    FROM kala_activation
                    WHERE chart_id = %s
                    GROUP BY signal_id
                ) t
                GROUP BY periods_per_predicate
                ORDER BY periods_per_predicate
                """,
                (_CANONICAL_CHART_ID,),
            )
            rows = {r["periods_per_predicate"]: r["num_predicates"] for r in cur.fetchall()}
        if not rows:
            pytest.skip("kala_activation has no rows for the canonical chart in this environment")
        assert rows == {1: 9347, 8: 40757}, f"live distribution changed: {rows}"

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_activation_predicates WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            pred_row = cur.fetchone()
        assert pred_row["n"] == 50104
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_863_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    total matches the live count_sql result for the canonical chart today —
    not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_kalasutra'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_kalasutra not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total_activation_rows"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_activation WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_activation has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_863_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_kalasutra'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_kalasutra not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_kalasutra'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
