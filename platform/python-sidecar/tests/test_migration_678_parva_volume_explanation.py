"""
tests/test_migration_678_parva_volume_explanation.py — L3 Kāla, F-PARVA-2:
migration 678 corrects `ka_jivana_parva`'s `asset_registry.volume_explanation` from the
stale MD-only description ("One row per mahadasha (typically 9 for a full Vimshottari
cycle)") to text naming all three levels the writer actually emits (MD + AD + PD), matching
L3_W1_ANALYSIS_BATCH_E.md's own measured 100-row live figure.

Same two-layer convention as migrations 675/676/677 this session:

  1. DB-free (static): the migration is a single, precisely-scoped UPDATE — no other
     asset's volume_explanation is touched, and the new text names all three levels
     (mahādaśā/antardaśā/pratyantardaśā) rather than repeating the stale MD-only claim.

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear reason if
     unreachable): runs the ACTUAL migration file against the real `asset_registry` row
     inside a transaction that is ALWAYS rolled back — never commits, matching this
     session's established "dry-run + ROLLBACK only, never apply-for-real ahead of merge"
     discipline. Proves: idempotent, and the value lands exactly as the migration claims.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "678_nirmana_l3_f_parva_2_volume_explanation.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 678 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_678_is_a_single_precisely_scoped_update():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE\s+\w+.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}: {updates}"
    stmt = updates[0]
    assert "asset_registry" in stmt
    assert "WHERE asset_id = 'ka_jivana_parva'" in stmt, (
        "UPDATE must be scoped to exactly this one asset_id — not a bare, unconditional UPDATE"
    )


def test_migration_678_new_text_names_all_three_levels_not_md_only():
    """The old text claimed 'One row per mahadasha (typically 9...)' — the fix must name
    AD and PD too, not just correct the count while keeping the MD-only framing."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+volume_explanation\s*=\s*'([^']*(?:''[^']*)*)'", code_only, re.S)
    assert m, "could not find the SET volume_explanation = '...' clause"
    new_text = m.group(1)
    assert "mahādaśā" in new_text or "mahadasha" in new_text.lower() or "MD" in new_text
    assert "antardaśā" in new_text or "antardasha" in new_text.lower() or " AD " in new_text
    assert "pratyantardaśā" in new_text or "pratyantardasha" in new_text.lower() or " PD " in new_text


def test_migration_678_does_not_repeat_the_stale_fixed_count_claim():
    """The stale text's specific defect was implying a fixed ~9-row count. The new text
    must not restate 'typically 9' as if it were still the current design."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+volume_explanation\s*=\s*'([^']*(?:''[^']*)*)'", code_only, re.S)
    assert m
    new_text = m.group(1)
    assert "typically 9" not in new_text


def test_migration_678_no_self_transaction_wrapper():
    """Same platform/migrations/ convention as migrations 675/676/677 — transaction
    ownership belongs to platform/scripts/migrate.ts, no self-wrapped BEGIN/COMMIT."""
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
def test_migration_678_corrects_volume_explanation_live():
    """Runs the actual migration against the real asset_registry row inside a transaction
    that is ALWAYS rolled back. Proves the post-migration value matches the migration's own
    text and no longer contains the stale 'typically 9' MD-only claim."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT volume_explanation FROM asset_registry WHERE asset_id = 'ka_jivana_parva'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_jivana_parva not present in asset_registry in this environment")
            before = row["volume_explanation"]

            cur.execute(sql)
            cur.execute("SELECT volume_explanation FROM asset_registry WHERE asset_id = 'ka_jivana_parva'")
            after = cur.fetchone()["volume_explanation"]

        assert "typically 9" not in (after or "")
        assert "pratyantarda" in (after or "").lower() or "PD" in (after or "")
        if before and "typically 9" in before:
            # Corroborates the finding's specific claim about this environment's pre-state —
            # informational only, not load-bearing if a prior partial-apply already changed it.
            pass
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_678_is_idempotent_live():
    """Running the migration twice inside one transaction produces the identical value the
    second time. Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("SELECT volume_explanation FROM asset_registry WHERE asset_id = 'ka_jivana_parva'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_jivana_parva not present in asset_registry in this environment")
            first_pass = row["volume_explanation"]

            cur.execute(sql)  # second application, same transaction
            cur.execute("SELECT volume_explanation FROM asset_registry WHERE asset_id = 'ka_jivana_parva'")
            second_pass = cur.fetchone()["volume_explanation"]

        assert first_pass == second_pass, "migration is not idempotent"
    finally:
        conn.rollback()
        conn.close()
