"""
tests/test_migration_675_paddhati_arbitration_role.py — L3 Kāla, N1 (Temporal
Concordance Contract) second bounded step: migration 675 adds
`arbitration_role`/`precedence` to `kala_paddhati_profile` and backfills the
six existing rows, correcting F-CONC-2 (rows 7/8's constraint_role='hard'
contradicting their own provenance prose).

Same two-layer convention as test_migration_527_generation_catalog_only.py:

  1. DB-free (static): the migration is additive-only on schema (`ADD COLUMN
     IF NOT EXISTS`), the CHECK constraint carries the exact five-value
     vocabulary the W1 evidence base names, and the backfill UPDATEs are
     scoped by convention_id/version/convention_status — never a bare
     unconditional UPDATE that could silently repoint every row identically
     if the table grows new conventions later.

  2. `@pytest.mark.integration` (live Cloud SQL proxy, same DATABASE_URL
     convention every other integration test in this suite uses; skips with
     a clear reason if unreachable): runs the ACTUAL migration file against
     the real `kala_paddhati_profile` table inside a transaction that is
     ALWAYS rolled back — never commits, matching this session's established
     "dry-run + ROLLBACK only, never apply-for-real ahead of merge"
     discipline. Proves: idempotent (running twice is a no-op the second
     time), the CHECK constraint genuinely rejects an invalid value, and the
     F-CONC-2 fix lands on exactly the rows the migration's header claims.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "675_nirmana_l3_n1_paddhati_arbitration_role.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 675 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_675_adds_columns_additively():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert re.search(r"ADD COLUMN IF NOT EXISTS arbitration_role", code_only)
    assert re.search(r"ADD COLUMN IF NOT EXISTS precedence", code_only)
    # No DROP COLUMN / DROP TABLE anywhere — purely additive.
    assert "DROP COLUMN" not in code_only
    assert "DROP TABLE" not in code_only


def test_migration_675_check_constraint_has_the_five_value_vocabulary():
    sql = _read_migration()
    m = re.search(r"CHECK\s*\(arbitration_role IS NULL OR arbitration_role = ANY \(ARRAY\[(.*?)\]\)\)", sql, re.S)
    assert m, "arbitration_role CHECK constraint not found in the expected shape"
    values = {v.strip().strip("'").rstrip("::text").strip("'") for v in m.group(1).split(",")}
    values = {v.split("'")[1] if "'" in v else v.strip() for v in m.group(1).split(",")}
    assert values == {"gate", "primary", "corroborating", "informational", "declared_silent"}


def test_migration_675_check_constraint_is_dropped_before_recreated():
    """DROP CONSTRAINT IF EXISTS before ADD CONSTRAINT is the idempotency
    pattern for a named CHECK constraint (ADD COLUMN IF NOT EXISTS alone
    does not make a same-named constraint re-add idempotent)."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert re.search(r"DROP CONSTRAINT IF EXISTS kala_paddhati_profile_arbitration_role_check", code_only)
    assert re.search(r"ADD CONSTRAINT kala_paddhati_profile_arbitration_role_check", code_only)


def test_migration_675_backfill_updates_are_scoped_not_unconditional():
    """Every UPDATE must filter on convention_id (+ version/convention_status
    where needed) — never a bare UPDATE kala_paddhati_profile SET ... with no
    WHERE, which would silently repoint every row (including future,
    non-agnivasa rows this migration was never analysed against) to the same
    arbitration_role."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE kala_paddhati_profile\s+SET.*?;", code_only, re.S)
    assert len(updates) == 3, f"expected exactly 3 backfill UPDATEs, found {len(updates)}"
    for stmt in updates:
        assert "WHERE" in stmt, f"UPDATE with no WHERE clause: {stmt!r}"
        assert "convention_id" in stmt, f"UPDATE not scoped by convention_id: {stmt!r}"


def test_migration_675_no_self_transaction_wrapper():
    """This migration lives in platform/migrations/ (the L3 670-679 range),
    whose established convention (migration 670's own header) is that
    transaction ownership belongs to platform/scripts/migrate.ts — unlike
    platform/supabase/migrations/527's self-wrapped BEGIN/COMMIT, a
    different pipeline with a different convention."""
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
def test_migration_675_backfills_correctly_and_fixes_f_conc_2():
    """Runs the actual migration file against the real kala_paddhati_profile
    table inside a transaction that is ALWAYS rolled back. Proves the exact
    backfill this migration's header claims, including the F-CONC-2 fix
    (rows 7/8 get arbitration_role='informational', not 'gate' — correcting
    the contradiction with their own constraint_role='hard')."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT id, convention_id, version, convention_status, "
                "constraint_role, arbitration_role, precedence "
                "FROM kala_paddhati_profile ORDER BY id"
            )
            rows = {r["id"]: r for r in cur.fetchall()}
        if not rows:
            pytest.skip("kala_paddhati_profile has no rows in this environment")

        for rid in (1, 3):
            if rid in rows:
                assert rows[rid]["arbitration_role"] == "gate"
                assert rows[rid]["precedence"] == 1

        for rid in (2, 4):
            if rid in rows:
                assert rows[rid]["convention_status"] == "declared_not_computed"
                assert rows[rid]["arbitration_role"] == "declared_silent"
                assert rows[rid]["precedence"] is None

        for rid in (7, 8):
            if rid in rows:
                # F-CONC-2: constraint_role says 'hard' but arbitration_role
                # must say the true, precise thing — informational, never a gate.
                assert rows[rid]["constraint_role"] == "hard"
                assert rows[rid]["arbitration_role"] == "informational"
                assert rows[rid]["precedence"] == 2
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_675_is_idempotent_live():
    """Running the migration twice inside one transaction produces byte-
    identical backfilled values the second time — no duplicate-constraint
    error, no value drift. Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("SELECT id, arbitration_role, precedence FROM kala_paddhati_profile ORDER BY id")
            first_pass = {r["id"]: (r["arbitration_role"], r["precedence"]) for r in cur.fetchall()}

            cur.execute(sql)  # second application, same transaction
            cur.execute("SELECT id, arbitration_role, precedence FROM kala_paddhati_profile ORDER BY id")
            second_pass = {r["id"]: (r["arbitration_role"], r["precedence"]) for r in cur.fetchall()}

        assert first_pass == second_pass, "migration is not idempotent — second pass changed values"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_675_check_constraint_rejects_invalid_value_live():
    """Proves the CHECK constraint is a real, enforced gate — not decorative
    — by attempting an invalid value and asserting PostgreSQL itself refuses
    it. Rolled back at the end; never persists (and the invalid UPDATE
    itself never commits even transiently, since the whole block aborts on
    the expected error before any COMMIT is reached)."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            with pytest.raises(Exception, match="kala_paddhati_profile_arbitration_role_check"):
                cur.execute(
                    "UPDATE kala_paddhati_profile SET arbitration_role = 'not_a_real_role' "
                    "WHERE id = (SELECT id FROM kala_paddhati_profile LIMIT 1)"
                )
    finally:
        conn.rollback()
        conn.close()
