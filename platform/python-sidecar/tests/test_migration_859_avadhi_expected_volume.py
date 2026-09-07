"""
tests/test_migration_859_avadhi_expected_volume.py — L3 Kāla, F-L3-4 slice:
migration 859 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_avadhi` (target_floor
1169 was already a genuine achieved-count floor; only the derivation was
undocumented).

This migration also surfaces (without fixing) a real gap: of the 7 dasha
systems `ka_avadhi`'s own `_DASHA_SYSTEMS` declares, only 6 have an exact
`system_id` match in live `chart_dashas` — `chara` has none (`chart_dashas`
instead carries `chara_karaka`, a related but distinct Jaimini concept). This
file's live test independently re-confirms that exact-match count from
`chart_dashas` itself, not from the migration's own claim.

Same convention as the rest of this batch: DB-free static guards + a
no-self-transaction-wrapper check, plus `@pytest.mark.integration` live tests
(rolled back, never committed).
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
    _REPO_ROOT, "platform", "migrations", "859_nirmana_l3_w3_avadhi_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

_DECLARED_SYSTEMS = ("vimshottari", "yogini", "ashtottari", "chara", "naisargika", "mudda", "kalachakra")

_OBSERVED_BY_SYSTEM = {
    "vimshottari": 117, "yogini": 308, "ashtottari": 104, "naisargika": 70, "mudda": 480, "kalachakra": 90,
}


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 859 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_859_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_avadhi'" in updates[0]


def test_migration_859_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_859_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_859_documents_the_chara_gap_without_resolving_it():
    sql = _read_migration()
    assert "'chara_karaka'" in sql
    assert "'chara'" in sql
    assert "unresolved_gap" in sql
    # must not claim resolution — no "fixed", "resolved", or "bug in ka_avadhi confirmed" language
    assert "NOT resolved by this migration" in sql


def test_migration_859_observed_counts_sum_to_target_floor():
    sql = _read_migration()
    for name, n in _OBSERVED_BY_SYSTEM.items():
        assert f"'{name}', {n}" in sql
    assert "'total', 1169" in sql
    assert sum(_OBSERVED_BY_SYSTEM.values()) == 1169


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
def test_migration_859_exact_match_count_is_six_of_seven_live():
    """Independently re-derives the claim this migration makes: exactly 6 of
    the 7 declared _DASHA_SYSTEMS names have a live chart_dashas system_id
    match for the canonical chart — not trusted from the migration's own
    text, re-queried from chart_dashas directly."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT system_id FROM chart_dashas WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_system_ids = {r["system_id"] for r in cur.fetchall()}
        if not live_system_ids:
            pytest.skip("chart_dashas has no rows for the canonical chart in this environment")
        matching = [s for s in _DECLARED_SYSTEMS if s in live_system_ids]
        assert set(matching) == {"vimshottari", "yogini", "ashtottari", "naisargika", "mudda", "kalachakra"}
        assert "chara" not in live_system_ids
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_859_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    per-system breakdown sums to the live count_sql result for the canonical
    chart today — not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_avadhi'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_avadhi not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]
        assert recorded_total == sum(v for k, v in observed.items() if k != "total")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_avadhi WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_avadhi has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_859_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_avadhi'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_avadhi not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_avadhi'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
