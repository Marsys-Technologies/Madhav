"""
tests/test_migration_730_vighnakara_depends_on.py — L3 Kāla, F-VIGHNA-5:
migration 730 corrects `ka_vighnakara.depends_on` from `{ka_sangam, ka_gochara,
ka_muhurta_seva, ga_positions}` (one fictional edge, two undeclared real reads) to
`{ka_sangam, ka_muhurta_seva, ga_positions, bg_dignity_reference, ka_yojaka}` — verified
against the writer's own SQL/imports, not assumed from the analysis batch alone.

First migration in L3's new 730-739 range (the Conductor's ruling on #1942, after the
670-679 range was fully consumed).

Same two-layer convention as migrations 675-679 this session:

  1. DB-free (static): the migration is a single, precisely-scoped UPDATE — the fictional
     `ka_gochara` edge is gone, the two undeclared reads are present, the three genuinely
     real edges are untouched.

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
    _REPO_ROOT, "platform", "migrations", "730_nirmana_l3_f_vighna_5_depends_on.sql"
)
_WRITER_PATH = os.path.join(
    _REPO_ROOT, "platform", "python-sidecar", "pipeline", "orchestrator", "writers",
    "ka_vighnakara.py",
)


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 730 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_730_is_a_single_precisely_scoped_update():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE\s+\w+.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}: {updates}"
    stmt = updates[0]
    assert "asset_registry" in stmt
    assert "WHERE asset_id = 'ka_vighnakara'" in stmt, (
        "UPDATE must be scoped to exactly this one asset_id — not a bare, unconditional UPDATE"
    )


def test_migration_730_removes_the_fictional_ka_gochara_edge():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+depends_on\s*=\s*'([^']*)'", code_only)
    assert m, "could not find the SET depends_on = '...' clause"
    new_value = m.group(1)
    assert "ka_gochara" not in new_value, "ka_gochara is a fictional edge — must be removed"


def test_migration_730_adds_both_undeclared_real_reads():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+depends_on\s*=\s*'([^']*)'", code_only)
    assert m
    new_value = m.group(1)
    assert "bg_dignity_reference" in new_value, "bg_combustion_orbs is written by bg_dignity_reference"
    assert "ka_yojaka" in new_value, "kala_activation_predicates is ka_yojaka's own output"


def test_migration_730_keeps_the_three_genuinely_real_edges():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    m = re.search(r"SET\s+depends_on\s*=\s*'([^']*)'", code_only)
    assert m
    new_value = m.group(1)
    for real_edge in ("ka_sangam", "ka_muhurta_seva", "ga_positions"):
        assert real_edge in new_value, f"{real_edge} is a verified real read — must stay"


def test_writer_genuinely_does_not_reference_ka_gochara_service():
    """Static proof (not just the migration's own comment) that ka_gochara is unread:
    the writer never references KaGocharaService or any kala_gochara table."""
    if not os.path.exists(_WRITER_PATH):
        pytest.skip(f"writer not found at {_WRITER_PATH}")
    with open(_WRITER_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "KaGocharaService" not in content
    assert "kala_gochara" not in content


def test_migration_730_no_self_transaction_wrapper():
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
def test_migration_730_corrects_depends_on_live():
    """Runs the actual migration against the real asset_registry row inside a transaction
    that is ALWAYS rolled back. Proves the post-migration value matches the migration's
    own claim exactly."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_vighnakara not present in asset_registry in this environment")

            cur.execute(sql)
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
            after = set(cur.fetchone()["depends_on"])

        assert after == {"ka_sangam", "ka_muhurta_seva", "ga_positions", "bg_dignity_reference", "ka_yojaka"}
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_730_is_idempotent_live():
    """Running the migration twice inside one transaction produces the identical value the
    second time. Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_vighnakara not present in asset_registry in this environment")

            cur.execute(sql)
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
            first_pass = cur.fetchone()["depends_on"]

            cur.execute(sql)  # second application, same transaction
            cur.execute("SELECT depends_on FROM asset_registry WHERE asset_id = 'ka_vighnakara'")
            second_pass = cur.fetchone()["depends_on"]

        assert first_pass == second_pass, "migration is not idempotent"
    finally:
        conn.rollback()
        conn.close()
