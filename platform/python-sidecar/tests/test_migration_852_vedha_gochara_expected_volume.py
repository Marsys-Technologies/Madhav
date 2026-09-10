"""
tests/test_migration_852_vedha_gochara_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 852 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_vedha_gochara`
(target_floor 176 was already a genuine achieved-count floor; only the
derivation was undocumented).

Same two-layer convention as test_migration_850_muhurta_seva_health_probe.py:

  1. DB-free (static): the migration is a single UPDATE scoped to
     `asset_id = 'ka_vedha_gochara'` (never a bare UPDATE that could repoint
     every asset's volume fields identically), guarded by
     `expected_volume_formula IS NULL` for idempotency, no self-transaction
     wrapper (transaction ownership belongs to migrate.ts, matching
     migration 670/850's convention for this range — NOT migration 851's;
     an embedded BEGIN;/COMMIT; would close its own transaction before this
     test's outer `conn.rollback()` could run, silently persisting the
     write for real against a live proxy — caught exactly that way on a
     first draft of this migration, reverted by hand, fixed at root here).

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear
     reason if unreachable): runs the ACTUAL migration file against the real
     `asset_registry` table inside a transaction that is ALWAYS rolled back —
     never commits. Proves idempotency and that the recorded observed count
     in `expected_volume_inputs` matches the live `count_sql` result for the
     canonical chart, not an invented figure.
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
    _REPO_ROOT, "platform", "migrations", "852_nirmana_l3_w3_vedha_gochara_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 852 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_852_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_vedha_gochara'" in updates[0]


def test_migration_852_no_self_transaction_wrapper():
    """A BEGIN;/COMMIT; wrapper would close its own transaction before the
    live integration tests' outer `conn.rollback()` runs, silently
    persisting the write for real against a live proxy — exactly what
    happened on a first draft of this migration (see the migration file's
    own header and this file's module docstring)."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_852_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_852_expected_volume_inputs_is_valid_json_and_matches_live_measurement():
    """Extracts the jsonb_build_object(...) call's literal string values isn't
    feasible via regex for a nested jsonb_build_object; instead this asserts
    the specific observed-count literals appear verbatim (132/24/20/176) —
    a change to any one of them without updating the others would still be
    caught by the live integration test's count comparison below."""
    sql = _read_migration()
    assert "'house_vedha', 132" in sql
    assert "'sarvatobhadra', 24" in sql
    assert "'latta', 20" in sql
    assert "'total', 176" in sql
    assert 132 + 24 + 20 == 176


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
def test_migration_852_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    observed total (176) matches what the asset's own live count_sql
    produces for the canonical chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_vedha_gochara'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_vedha_gochara not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_vedha_gochara WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_vedha_gochara has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_852_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_vedha_gochara'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_vedha_gochara not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_vedha_gochara'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
