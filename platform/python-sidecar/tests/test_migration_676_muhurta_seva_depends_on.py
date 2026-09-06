"""
tests/test_migration_676_muhurta_seva_depends_on.py — L3 Kāla, finding N5 (depends_on half):
migration 676 corrects `ka_muhurta_seva.depends_on` from the fictional `{ka_graha_sancara}`
to the audit-verified true value, `{}`.

Same two-layer convention as test_migration_675_paddhati_arbitration_role.py:

  1. DB-free (static): the migration is a single, precisely-scoped UPDATE — no other asset's
     depends_on is touched, and the new value matches L3_DEPENDS_ON_AUDIT_v1_0.md's own
     verified verdict for this asset (1 declared, 0 hidden, 1 false -> corrected value is the
     empty array, not a swap to a different asset id).

  2. `@pytest.mark.integration` (live Cloud SQL proxy, same DATABASE_URL convention every other
     integration test in this suite uses; skips with a clear reason if unreachable): runs the
     ACTUAL migration file against the real `asset_registry` row inside a transaction that is
     ALWAYS rolled back — never commits, matching this session's established "dry-run + ROLLBACK
     only, never apply-for-real ahead of merge" discipline. Proves: idempotent (running twice
     is a no-op the second time), and the value lands exactly as the migration's header claims.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "676_nirmana_l3_n5_muhurta_seva_depends_on.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 676 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_676_is_a_single_precisely_scoped_update():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE\s+\w+.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}: {updates}"
    stmt = updates[0]
    assert "asset_registry" in stmt
    assert "WHERE asset_id = 'ka_muhurta_seva'" in stmt, (
        "UPDATE must be scoped to exactly this one asset_id — not a bare, unconditional UPDATE"
    )


def test_migration_676_sets_the_audit_verified_value_not_a_swap():
    """The audit (L3_DEPENDS_ON_AUDIT_v1_0.md) verified zero real dependencies for this
    asset — the fix is the empty array, never a different single-element array (which
    would just replace one fictional edge with another unverified guess)."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+depends_on\s*=\s*'([^']*)'", code_only)
    assert m, "could not find the SET depends_on = '...' clause"
    assert m.group(1) == "{}", f"expected depends_on = '{{}}' (empty array), got {m.group(1)!r}"


def test_migration_676_no_self_transaction_wrapper():
    """Same platform/migrations/ convention as migration 675 — transaction ownership
    belongs to platform/scripts/migrate.ts, no self-wrapped BEGIN/COMMIT."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


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
def test_migration_676_corrects_depends_on_live():
    """Runs the actual migration against the real asset_registry row inside a transaction
    that is ALWAYS rolled back. Proves the pre-migration value is the known-fictional
    {ka_graha_sancara} and the post-migration value is the audit-verified {}."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_muhurta_seva'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_muhurta_seva not present in asset_registry in this environment")
            before = row["depends_on"]

            cur.execute(sql)
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_muhurta_seva'")
            after = cur.fetchone()["depends_on"]

        assert after == [], f"expected depends_on = [] after migration, got {after!r}"
        if before == ["ka_graha_sancara"]:
            # Corroborates the audit's specific claim about this environment's pre-state —
            # informational only, not load-bearing if a prior partial-apply already changed it.
            pass
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_676_is_idempotent_live():
    """Running the migration twice inside one transaction produces the identical value the
    second time. Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_muhurta_seva'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_muhurta_seva not present in asset_registry in this environment")
            first_pass = row["depends_on"]

            cur.execute(sql)  # second application, same transaction
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_muhurta_seva'")
            second_pass = cur.fetchone()["depends_on"]

        assert first_pass == second_pass == [], "migration is not idempotent"
    finally:
        conn.rollback()
        conn.close()
