"""
tests/test_migration_860_service_assets_expected_volume.py — L3 Kāla, F-L3-4
slice: migration 860 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for all four of L3's
`asset_kind='service'` assets (`ka_dasha_kala`, `ka_graha_sancara`,
`ka_muhurta_seva`, `ka_tulana`) in ONE migration, unlike migrations 852-859
which each covered one data-writer asset — these four share an identical,
verified-live reason: no per-chart table to count in the first place.

Same convention: DB-free static guards + a no-self-transaction-wrapper check,
plus `@pytest.mark.integration` live tests (rolled back, never committed)
that independently re-verify the asset_kind/target_table/count_sql claims
from asset_registry itself, not trusted from the migration's own text.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "860_nirmana_l3_w3_service_assets_expected_volume.sql"
)

_SERVICE_ASSET_IDS = ("ka_dasha_kala", "ka_graha_sancara", "ka_muhurta_seva", "ka_tulana")


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 860 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_860_updates_exactly_the_four_service_assets():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    for asset_id in _SERVICE_ASSET_IDS:
        assert f"'{asset_id}'" in updates[0]
    assert "IN (" in updates[0], "must scope via WHERE asset_id IN (...), not a bare UPDATE"


def test_migration_860_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_860_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_860_does_not_touch_target_floor():
    """This migration is scoped to the three volume-documentation fields
    only — target_floor's NULL-vs-0 inconsistency across these four assets
    was checked against asset_runner.py and confirmed not to matter (they
    take the probe-based completion path), and is deliberately left alone."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    update_stmt = re.search(r"UPDATE asset_registry\s+SET(.*?)WHERE", code_only, re.S).group(1)
    assert "target_floor" not in update_stmt


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
def test_migration_860_all_four_are_genuinely_service_kind_with_no_table_live():
    """Independently re-verifies the migration's own premise against live
    asset_registry — not trusted from the migration text: all four assets
    are asset_kind='service' with no target_table/count_sql."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT asset_id, asset_kind, target_table, count_sql, health_probe IS NOT NULL AS has_probe "
                "FROM asset_registry WHERE asset_id = ANY(%s)",
                (list(_SERVICE_ASSET_IDS),),
            )
            rows = {r["asset_id"]: r for r in cur.fetchall()}
        if len(rows) < len(_SERVICE_ASSET_IDS):
            pytest.skip("not all four service assets present in asset_registry in this environment")
        for asset_id in _SERVICE_ASSET_IDS:
            r = rows[asset_id]
            assert r["asset_kind"] == "service", f"{asset_id}: expected asset_kind='service', got {r['asset_kind']!r}"
            assert r["target_table"] is None, f"{asset_id}: expected NULL target_table"
            assert r["count_sql"] is None, f"{asset_id}: expected NULL count_sql"
            assert r["has_probe"] is True, f"{asset_id}: expected a health_probe to already be present"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_860_sets_volume_fields_for_all_four_live():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves all four assets
    receive the N/A documentation, not just some of them."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT asset_id, expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = ANY(%s)",
                (list(_SERVICE_ASSET_IDS),),
            )
            rows = {r["asset_id"]: r for r in cur.fetchall()}
        if len(rows) < len(_SERVICE_ASSET_IDS):
            pytest.skip("not all four service assets present in asset_registry in this environment")
        for asset_id in _SERVICE_ASSET_IDS:
            r = rows[asset_id]
            assert r["expected_volume_formula"] is not None, f"{asset_id}: formula still NULL after migration"
            assert r["expected_volume_formula"].startswith("N/A")
            assert r["volume_explanation"] is not None
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_860_is_idempotent_live():
    """Running the migration twice inside one transaction produces byte-
    identical stored values the second time (the IS NULL guard makes the
    second application a no-op). Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT asset_id, expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = ANY(%s) ORDER BY asset_id",
                (list(_SERVICE_ASSET_IDS),),
            )
            first_pass = cur.fetchall()
            if not first_pass:
                pytest.skip("none of the four service assets present in asset_registry in this environment")

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT asset_id, expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = ANY(%s) ORDER BY asset_id",
                (list(_SERVICE_ASSET_IDS),),
            )
            second_pass = cur.fetchall()

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
