"""
tests/test_migration_845_tulana_health_probe.py — L3 Kāla, F-L3-15 third
slice: migration 845 populates `asset_registry.health_probe` for `ka_tulana`.

RENUMBERED THREE TIMES 764→810→842→845 (across three cycles): 764 collided
with L2's own 760-779 range; 810 was independently claimed by L1's own
already-merged 810_..._houcompstrength.sql; 842 was independently claimed by
L1's own already-merged 842_..._bhava_bala_backfill.sql — all three caught
by `scripts/ci/migration_number_guard.ts`'s E2 check. Fixed each time by
renumbering upward, each time skipping the guard's own suggestion when a
sibling open L3 PR had already claimed it in the same cycle, since this
migration had never been applied anywhere.

Corrects a scoping error made in this migration's own F-L3-15 predecessor
(#2065's PR description, for `ka_muhurta_seva`): `ka_tulana` was described
there as needing live DB access alongside `ka_dasha_kala`. It does not —
`KaTulanaService.rank_windows()`/`.compare()` are pure ranking logic over
already-computed `WindowInput` records, no `db_conn` anywhere in the class.

Same two-layer convention as test_migration_676_muhurta_seva_health_probe.py:

  1. DB-free (static): the migration is a single UPDATE scoped to
     `asset_id = 'ka_tulana'`, no self-transaction wrapper, and the JSONB
     literal's keys match exactly what `service_probes._validated_tulana_
     probe_config` requires.

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear
     reason if unreachable): runs the ACTUAL migration file against the real
     `asset_registry` table inside a transaction that is ALWAYS rolled back —
     never commits. Proves the stored contract round-trips through the real
     probe dispatcher to GREEN — the end-to-end path a probe_accepted
     submission actually exercises.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "845_nirmana_l3_w3_tulana_health_probe.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 845 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_810_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_tulana'" in updates[0]


def test_migration_810_sets_the_expected_probe_type():
    sql = _read_migration()
    assert '"probe_type": "tulana_ranking_forensic"' in sql


def test_migration_810_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_810_contract_matches_the_probe_module_field_names():
    """The JSONB literal's keys must be exactly what
    service_probes._validated_tulana_probe_config requires — a typo here
    would pass this migration's own SQL syntax check yet fail the probe
    closed at dispatch time with 'missing required fields'."""
    from pipeline.orchestrator import service_probes as sp

    sql = _read_migration()
    m = re.search(r"\$hp\$(.*?)\$hp\$", sql, re.S)
    assert m, "expected a $hp$ ... $hp$ dollar-quoted JSONB literal"
    import json
    contract = json.loads(m.group(1))
    assert contract.keys() >= sp._TULANA_REQUIRED_FIELDS
    # Round-trips through the real validator without raising.
    sp._validated_tulana_probe_config(contract)


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
def test_migration_810_sets_health_probe_and_drives_a_real_green_live():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the stored
    contract round-trips through the real probe dispatcher to GREEN."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_tulana'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_tulana not present in asset_registry in this environment"
        assert row["health_probe"] is not None

        from pipeline.orchestrator import service_probes as sp

        result = sp.run_health_probe("ka_tulana", row["health_probe"])
        assert result["status"] == "GREEN", f"got {result['status']}: {result['message']}"
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_810_is_idempotent_live():
    """Running the migration twice inside one transaction produces a byte-
    identical stored contract the second time. Rolled back at the end; never
    persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_tulana'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_tulana not present in asset_registry in this environment")
            first_pass = row["health_probe"]

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_tulana'"
            )
            second_pass = cur.fetchone()["health_probe"]

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored contract"
    finally:
        conn.rollback()
        conn.close()
