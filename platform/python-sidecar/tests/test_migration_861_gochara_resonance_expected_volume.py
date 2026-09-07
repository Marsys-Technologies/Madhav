"""
tests/test_migration_861_gochara_resonance_expected_volume.py — L3 Kāla,
F-L3-4 slice: migration 861 populates `asset_registry.expected_volume_formula`
/ `expected_volume_inputs` / `volume_explanation` for `ka_gochara_resonance`
(target_floor 762 was already a genuine achieved-count floor; only the
derivation was undocumented).

Scoped strictly to volume documentation — this asset's W4 dispatch remains
correctly HELD per D-CND-26 (true closure includes unfrozen L1 ancestors),
and its `depends_on` remains untouched (campaign-wide immutable per
D-CND-09). This test file asserts the migration does not touch either.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed).
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
    _REPO_ROOT, "platform", "migrations", "861_nirmana_l3_w3_gochara_resonance_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

_OBSERVED_BY_TYPE = {
    "yoga_constituent": 220, "sensitive_degree": 176, "mechanism_node": 93,
    "arudha": 68, "bhava": 68, "lord": 49, "dasha_lord_portfolio": 44, "karaka": 44,
}


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 861 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_861_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_gochara_resonance'" in updates[0]


def test_migration_861_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_861_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_861_does_not_touch_depends_on_or_probe_fields():
    """This asset's W4 dispatch is correctly HELD (D-CND-26) and depends_on
    is campaign-wide immutable (D-CND-09) — this migration must not assign
    either, only the three volume-documentation fields. Checks only the
    top-level assigned column names (start-of-line `col_name =`), not the
    full SET-clause text, since the assigned string VALUES legitimately
    mention "target_floor" in prose (e.g. "matches target_floor exactly")."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    update_stmt = re.search(r"UPDATE asset_registry\s+SET(.*?)WHERE", code_only, re.S).group(1)
    assigned_columns = re.findall(r"^\s*(\w+)\s*=", update_stmt, re.M)
    assert assigned_columns == ["expected_volume_formula", "expected_volume_inputs", "volume_explanation"]


def test_migration_861_observed_counts_sum_to_target_floor():
    sql = _read_migration()
    for name, n in _OBSERVED_BY_TYPE.items():
        assert f"'{name}', {n}" in sql
    assert "'total', 762" in sql
    assert sum(_OBSERVED_BY_TYPE.values()) == 762


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
def test_migration_861_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    per-target_type breakdown sums to the live count_sql result for the
    canonical chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor, depends_on FROM asset_registry WHERE asset_id = 'ka_gochara_resonance'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_gochara_resonance not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None
        assert row["depends_on"] == ["bg_transit_rules"], "depends_on must remain untouched by this migration"

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM gochara_resonance_map WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("gochara_resonance_map has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_861_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_gochara_resonance'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_gochara_resonance not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_gochara_resonance'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
