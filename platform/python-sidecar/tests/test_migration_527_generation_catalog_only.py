"""
tests/test_migration_527_generation_catalog_only.py — ṢAḌ-DARŚANA lane
w2g-generation-schema, ADJUDICATION-6 additive schema (migration 527).

TWO INDEPENDENT PROOF LAYERS, same convention as
tests/test_cr131_gochara_db_reachability.py (DB-free static guard +
`@pytest.mark.integration` live guard, excluded by the mandated
`-m "not integration"` CI invocation):

  1. DB-free (static): the migration file itself is additive-only — no
     UPDATE/DELETE against `kala_gochara_windows`, uses `ADD COLUMN IF NOT
     EXISTS` / `CREATE TABLE IF NOT EXISTS`, and the new authority table is
     seeded with nothing (no INSERT). Regression guard against a future edit
     silently turning this into a data-mutating migration.

  2. `@pytest.mark.integration` (live Cloud SQL proxy, 127.0.0.1:5433, same
     `DATABASE_URL` convention every other integration test in this suite
     uses — skips with a clear reason if unreachable, never fabricates a
     result): proves, against the REAL PostgreSQL server this repo runs on,
     that `ALTER TABLE ... ADD COLUMN x TEXT NOT NULL DEFAULT 'v1'` is a
     catalog-only operation in PG11+ — no pre-existing row's heap tuple is
     rewritten. This is demonstrated on a throwaway `CREATE TEMP TABLE`
     (session-local, auto-dropped on disconnect, zero shared-state risk),
     NEVER against the production `kala_gochara_windows` table itself —
     the untouchable-data rail means this suite proves the general
     PostgreSQL claim on a structurally-representative stand-in rather than
     experimenting on the real 16,692-row table. The proof: capture each
     pre-existing row's system column `xmin` (the ID of the transaction that
     last wrote that row's current heap version — advances IFF the row is
     rewritten) before the ALTER, run the exact migration-527 ALTER
     statement, then assert every pre-existing row's `xmin` is byte-for-byte
     unchanged and its new column reads back the DEFAULT for every row with
     no explicit UPDATE ever issued.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "supabase", "migrations", "527_kala_gochara_generation_authority.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 527 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_527_adds_generation_column_additively():
    sql = _read_migration()
    assert re.search(
        r"ALTER TABLE kala_gochara_windows\s+ADD COLUMN IF NOT EXISTS generation TEXT NOT NULL DEFAULT 'v1'",
        sql,
    ), "migration 527 must add kala_gochara_windows.generation via ADD COLUMN IF NOT EXISTS ... DEFAULT 'v1'"


def test_migration_527_creates_authority_table_additively():
    sql = _read_migration()
    assert "CREATE TABLE IF NOT EXISTS kala_gochara_authority" in sql, (
        "migration 527 must create kala_gochara_authority as a new, additive table"
    )
    assert "authoritative_generation TEXT NOT NULL DEFAULT 'v1'" in sql, (
        "kala_gochara_authority.authoritative_generation must default to 'v1' — "
        "the absent-row-means-v1 reading-path contract depends on this default "
        "matching the column-level default even though the real contract is the "
        "COALESCE-on-absent-row pattern, not this column default"
    )


def test_migration_527_never_updates_or_deletes_kala_gochara_windows_rows():
    """The untouchable-data rail (brief §7 / ADJUDICATION-6): v1 rows are never
    updated or deleted, in this migration or ever. A regression here (someone
    later adding a backfill UPDATE) is exactly the class of change this test
    exists to catch before it ships."""
    sql = _read_migration()
    # Strip comments (this migration's prose extensively discusses "UPDATE"/
    # "DELETE" as concepts it is NOT doing) before scanning for real statements.
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bUPDATE\s+kala_gochara_windows\b", code_only, re.IGNORECASE), (
        "migration 527 must never UPDATE kala_gochara_windows — untouchable-data rail"
    )
    assert not re.search(r"\bDELETE\s+FROM\s+kala_gochara_windows\b", code_only, re.IGNORECASE), (
        "migration 527 must never DELETE FROM kala_gochara_windows — untouchable-data rail"
    )
    assert not re.search(r"\bINSERT\s+INTO\s+kala_gochara_authority\b", code_only, re.IGNORECASE), (
        "migration 527 must seed NOTHING into kala_gochara_authority — an absent row "
        "means 'v1' authoritative BY DEFINITION, per ADJUDICATION-6's reading-path contract"
    )


def test_migration_527_is_idempotent_on_every_ddl_statement():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    for stmt_kind, guard in [
        ("ALTER TABLE kala_gochara_windows ADD COLUMN", r"ADD COLUMN IF NOT EXISTS generation"),
        ("CREATE TABLE kala_gochara_authority", r"CREATE TABLE IF NOT EXISTS kala_gochara_authority"),
        ("CREATE INDEX on (chart_id, generation)", r"CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_chart_generation"),
    ]:
        assert re.search(guard, code_only), f"{stmt_kind} must be idempotent (IF NOT EXISTS)"


def test_migration_527_wrapped_in_a_single_transaction():
    sql = _read_migration()
    # BEGIN...COMMIT exactly once each, in the applied (non-comment) SQL.
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert len(re.findall(r"\bBEGIN\s*;", code_only)) == 1
    assert len(re.findall(r"\bCOMMIT\s*;", code_only)) == 1


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
def test_add_column_with_default_is_catalog_only_no_xmin_change():
    """The load-bearing claim in migration 527's header comment, proven live
    against the real PostgreSQL server this repo runs on (not asserted from
    documentation alone). Uses a throwaway CREATE TEMP TABLE — never the real
    kala_gochara_windows table — so this test carries zero risk to production
    data regardless of environment."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TEMP TABLE t527_catalog_only_probe "
                "(id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, source TEXT NOT NULL DEFAULT 'live')"
            )
            cur.executemany(
                "INSERT INTO t527_catalog_only_probe (chart_id) VALUES (%s)",
                [("482012f1-710e-4a25-994a-93821f5871aa",)] * 25,
            )
            cur.execute("SELECT id, xmin::text AS xmin_before FROM t527_catalog_only_probe ORDER BY id")
            before = {r["id"]: r["xmin_before"] for r in cur.fetchall()}
            assert len(before) == 25

            # The EXACT statement shape migration 527 issues against
            # kala_gochara_windows, run here against the throwaway stand-in.
            cur.execute(
                "ALTER TABLE t527_catalog_only_probe "
                "ADD COLUMN IF NOT EXISTS generation TEXT NOT NULL DEFAULT 'v1'"
            )

            cur.execute(
                "SELECT id, xmin::text AS xmin_after, generation FROM t527_catalog_only_probe ORDER BY id"
            )
            after = cur.fetchall()
            assert len(after) == 25, "ADD COLUMN must not change row count"
            for r in after:
                assert r["xmin_after"] == before[r["id"]], (
                    f"row id={r['id']} xmin changed ({before[r['id']]} -> {r['xmin_after']}) -- "
                    "ADD COLUMN ... DEFAULT rewrote the heap; the catalog-only claim is FALSE "
                    "on this PostgreSQL server/version"
                )
                assert r["generation"] == "v1", (
                    f"row id={r['id']} did not read back the DEFAULT 'v1' with no explicit UPDATE issued"
                )
        conn.rollback()  # never persists so much as the temp table beyond this session
    finally:
        conn.close()


@pytest.mark.integration
def test_live_kala_gochara_windows_source_still_single_valued_live():
    """Read-only corroboration of PR #1006's finding this lane is fixing:
    `source` is single-valued 'live' on every row, so it cannot be
    repurposed as a generation discriminator without mutating existing rows
    — exactly why migration 527 adds a NEW column instead. Never asserts
    anything about `generation` here (whether the migration has been applied
    in this environment is orthogonal to this specific, narrow claim)."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT source FROM kala_gochara_windows")
            values = {r["source"] for r in cur.fetchall()}
        if not values:
            pytest.skip("kala_gochara_windows has zero rows in this environment")
        assert values == {"live"}, (
            f"source is no longer single-valued 'live' ({values}) -- re-check whether "
            "this PR's premise (source cannot be repurposed) still holds"
        )
    finally:
        conn.close()
