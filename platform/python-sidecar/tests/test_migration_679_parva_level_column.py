"""
tests/test_migration_679_parva_level_column.py — L3 Kāla, F-PARVA-1:
migration 679 adds `kala_jivana_parva.parva_level` (1=MD, 2=AD, 3=PD) — the discriminator
that lets a consumer tell which biographical-chapter level a row is without string-parsing
`source_citation`. Backfills existing rows deterministically from their own
`source_citation` value, sets the column NOT NULL with a CHECK(1,2,3), and adds a real
natural key `(chart_id, source_citation, start_year)` alongside the existing
loop-counter `(chart_id, parva_index)` unique index (kept, not removed).

The natural key is NOT the finding's first-proposed `(chart_id, parva_level,
dasha_planet, start_year)` — that combination was dry-run tested against real production
data and genuinely collided (an MD-boundary antardaśā transition where the outgoing and
incoming lord happen to share a lord+year). `(chart_id, source_citation, start_year)` was
verified live to have zero duplicate groups across all three canonical charts.

Same two-layer convention as migrations 675-678 this session:

  1. DB-free (static): the migration's structure — ADD COLUMN, the backfill CASE
     expression, NOT NULL + CHECK, and the new UNIQUE INDEX — all present and correctly
     shaped; no destructive statement (no DROP of the existing unique index or any column).

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear reason if
     unreachable): runs the ACTUAL migration file against the real `kala_jivana_parva`
     table inside a transaction that is ALWAYS rolled back — never commits, matching this
     session's established "dry-run + ROLLBACK only, never apply-for-real ahead of merge"
     discipline. Proves: idempotent, backfill correctness against real source_citation
     values, and the new CHECK/UNIQUE constraints are genuinely enforced (not just
     documentation-compatible).
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "679_nirmana_l3_f_parva_1_level_column.sql"
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 679 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_679_adds_parva_level_column():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert re.search(
        r"ALTER TABLE\s+kala_jivana_parva\s+ADD COLUMN\s+IF NOT EXISTS\s+parva_level\s+SMALLINT",
        code_only,
    ), "expected an idempotent ADD COLUMN IF NOT EXISTS parva_level SMALLINT"


def test_migration_679_backfill_matches_the_source_citation_rule_the_finding_names():
    """F-PARVA-1's own text names the exact string-parsing rule a reader has to use today
    (':PD=' -> level 3, ':AD=' -> level 2, else MD/level 1) — the migration's backfill
    must implement exactly that rule, in that priority order (PD checked before AD, since
    a PD citation also contains ':MD=' but never matters if PD is checked first)."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"UPDATE\s+kala_jivana_parva\s+SET\s+parva_level\s*=\s*CASE(.*?)END", code_only, re.S)
    assert m, "could not find the backfill UPDATE ... SET parva_level = CASE ... END"
    case_body = m.group(1)
    pd_idx = case_body.find(":PD=")
    ad_idx = case_body.find(":AD=")
    assert pd_idx != -1 and ad_idx != -1, "backfill CASE must test both :PD= and :AD="
    assert pd_idx < ad_idx, "the :PD= branch must be tested BEFORE :AD= (a PD citation also contains :MD=)"
    assert re.search(r":PD=%'\s*THEN\s*3", case_body)
    assert re.search(r":AD=%'\s*THEN\s*2", case_body)
    assert re.search(r"ELSE\s*1", case_body)


def test_migration_679_sets_not_null_and_check_constraint():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert re.search(r"ALTER COLUMN\s+parva_level\s+SET NOT NULL", code_only)
    assert re.search(
        r"ADD CONSTRAINT\s+kala_jivana_parva_parva_level_check\s+CHECK\s*\(\s*parva_level\s+IN\s*\(\s*1\s*,\s*2\s*,\s*3\s*\)\s*\)",
        code_only,
    )


def test_migration_679_adds_natural_key_without_dropping_the_existing_index():
    """The fix is ADDITIVE — a real natural key alongside the existing
    (chart_id, parva_index) unique index, not a replacement. No DROP INDEX / DROP
    CONSTRAINT touching the pre-existing idx_kala_jivana_parva_chart_index."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert "idx_kala_jivana_parva_chart_index" not in code_only, (
        "must not touch the existing (chart_id, parva_index) unique index"
    )
    # NOT (chart_id, parva_level, dasha_planet, start_year) — that combination was
    # dry-run tested live and genuinely collided (see the migration's own header comment).
    assert re.search(
        r"CREATE UNIQUE INDEX\s+IF NOT EXISTS\s+idx_kala_jivana_parva_natural_key\s+"
        r"ON\s+kala_jivana_parva\s*\(\s*chart_id\s*,\s*source_citation\s*,\s*start_year\s*\)",
        code_only,
    )


def test_migration_679_no_destructive_statement():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert "DROP TABLE" not in code_only.upper()
    assert "DROP COLUMN" not in code_only.upper()


def test_migration_679_no_self_transaction_wrapper():
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
def test_migration_679_backfills_existing_rows_correctly_live():
    """Runs the actual migration against the real kala_jivana_parva table inside a
    transaction that is ALWAYS rolled back. Proves every pre-existing row gets a
    parva_level matching its own source_citation, and no row is left NULL."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM kala_jivana_parva")
            total_before = cur.fetchone()["n"]
            if total_before == 0:
                pytest.skip("kala_jivana_parva is empty in this environment — nothing to backfill")

            cur.execute(sql)

            cur.execute("SELECT count(*) AS n FROM kala_jivana_parva WHERE parva_level IS NULL")
            assert cur.fetchone()["n"] == 0, "every row must have a non-NULL parva_level after the migration"

            cur.execute(
                "SELECT count(*) AS n FROM kala_jivana_parva "
                "WHERE (source_citation LIKE '%:PD=%' AND parva_level != 3) "
                "   OR (source_citation NOT LIKE '%:PD=%' AND source_citation LIKE '%:AD=%' AND parva_level != 2) "
                "   OR (source_citation NOT LIKE '%:PD=%' AND source_citation NOT LIKE '%:AD=%' AND parva_level != 1)"
            )
            assert cur.fetchone()["n"] == 0, "every row's parva_level must match its own source_citation exactly"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_679_is_idempotent_live():
    """Running the migration twice inside one transaction produces the identical
    per-row parva_level values the second time. Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM kala_jivana_parva")
            if cur.fetchone()["n"] == 0:
                pytest.skip("kala_jivana_parva is empty in this environment")

            cur.execute(sql)
            cur.execute(
                "SELECT chart_id, parva_index, parva_level FROM kala_jivana_parva ORDER BY chart_id, parva_index"
            )
            first_pass = cur.fetchall()

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT chart_id, parva_index, parva_level FROM kala_jivana_parva ORDER BY chart_id, parva_index"
            )
            second_pass = cur.fetchall()

        assert first_pass == second_pass, "migration is not idempotent"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_679_check_constraint_genuinely_rejects_invalid_level_live():
    """Proves the CHECK constraint is real enforcement, not just documentation — an
    attempted INSERT with parva_level=4 must fail."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            with pytest.raises(Exception):
                cur.execute(
                    "INSERT INTO kala_jivana_parva "
                    "(chart_id, parva_index, parva_level, start_year, dasha_planet, "
                    " dominant_signal_class, parva_quality, source_citation) "
                    "SELECT chart_id, 32000, 4, start_year, dasha_planet, "
                    "       dominant_signal_class, parva_quality, 'test:invalid_level' "
                    "FROM kala_jivana_parva LIMIT 1"
                )
    finally:
        conn.rollback()
        conn.close()
