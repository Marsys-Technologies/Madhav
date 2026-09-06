"""
tests/test_migration_811_dasha_kala_proxy_probe.py — L3 Kāla, F-L3-15 fourth
and final slice: migration 811 populates `asset_registry.health_probe` for
`ka_dasha_kala`.

Ruled D-CND-34 (#2071): unlike the other three L3 service probes,
`ka_dasha_kala` cannot get a DB-free probe of the same architecture —
`KaDashaKalaService.query()` reads `chart_dashas` through `db_conn`, and the
authenticated `nirmana_probe.py` route this dispatches through has zero DB
infrastructure by design (adding one would expand that route's security
surface, a risk-acceptance call outside a session's own authority).

Ruling: Option (B), a DB-free PROXY check — importability + the 7-system
constant-set identity, nothing DB-backed. Required condition: every check
must disclose this narrow scope, never imply live-DB correctness (§N.8).

Same two-layer convention as the other three probes' migration tests:

  1. DB-free (static): the migration is a single UPDATE scoped to
     `asset_id = 'ka_dasha_kala'`, no self-transaction wrapper, and the
     JSONB literal's keys match exactly what
     `service_probes._validated_dasha_kala_probe_config` requires.

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear
     reason if unreachable): runs the ACTUAL migration file against the real
     `asset_registry` table inside a transaction that is ALWAYS rolled back —
     never commits. Proves the stored contract round-trips through the real
     probe dispatcher to GREEN, AND that the result's checks carry the
     required scope-disclosure field (not just that it returns GREEN).
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "811_nirmana_l3_w3_dasha_kala_proxy_probe.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 811 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_811_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_dasha_kala'" in updates[0]


def test_migration_811_sets_the_expected_probe_type():
    sql = _read_migration()
    assert '"probe_type": "dasha_kala_proxy_integrity"' in sql


def test_migration_811_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_811_declares_exactly_the_seven_systems():
    """The registry-owned `expected_systems` list must match the module's own
    documented 7-system set exactly — not a superset or subset — since this
    is the whole point of the check (catch drift, not just presence)."""
    sql = _read_migration()
    m = re.search(r"\$hp\$(.*?)\$hp\$", sql, re.S)
    assert m, "expected a $hp$ ... $hp$ dollar-quoted JSONB literal"
    import json
    contract = json.loads(m.group(1))
    assert set(contract["expected_systems"]) == {
        "vimshottari", "yogini", "ashtottari", "chara_karaka",
        "naisargika", "mudda", "kalachakra",
    }


def test_migration_811_contract_matches_the_probe_module_field_names():
    """The JSONB literal's keys must be exactly what
    service_probes._validated_dasha_kala_probe_config requires — a typo here
    would pass this migration's own SQL syntax check yet fail the probe
    closed at dispatch time with 'missing required fields'."""
    from pipeline.orchestrator import service_probes as sp

    sql = _read_migration()
    m = re.search(r"\$hp\$(.*?)\$hp\$", sql, re.S)
    assert m, "expected a $hp$ ... $hp$ dollar-quoted JSONB literal"
    import json
    contract = json.loads(m.group(1))
    # Round-trips through the real validator without raising.
    sp._validated_dasha_kala_probe_config(contract)


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
def test_migration_811_sets_health_probe_and_drives_a_real_green_live():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the stored
    contract round-trips through the real probe dispatcher to GREEN, AND
    that every reported check carries the required scope-disclosure field —
    the ruling's own required condition, not just a passing status."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_dasha_kala'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_dasha_kala not present in asset_registry in this environment"
        assert row["health_probe"] is not None

        from pipeline.orchestrator import service_probes as sp

        result = sp.run_health_probe("ka_dasha_kala", row["health_probe"])
        assert result["status"] == "GREEN", f"got {result['status']}: {result['message']}"
        for check in result["checks"]:
            assert "scope" in check, f"check {check['check']!r} missing required scope disclosure"
            assert "PROXY" in check["scope"], f"check {check['check']!r} scope does not disclose proxy-only coverage"
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_811_is_idempotent_live():
    """Running the migration twice inside one transaction produces a byte-
    identical stored contract the second time. Rolled back at the end; never
    persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_dasha_kala'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_dasha_kala not present in asset_registry in this environment")
            first_pass = row["health_probe"]

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_dasha_kala'"
            )
            second_pass = cur.fetchone()["health_probe"]

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored contract"
    finally:
        conn.rollback()
        conn.close()
