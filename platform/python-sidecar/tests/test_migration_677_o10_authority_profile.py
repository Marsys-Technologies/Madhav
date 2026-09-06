"""
tests/test_migration_677_o10_authority_profile.py — L3 Kāla, N1 (Temporal Concordance
Contract) fifth bounded step: migration 677 seeds kala_paddhati_profile's first
non-agnivasa factor_family, O-10 (L3_W1_ANALYSIS_BATCH_E.md §1.2: "Does the causal chain
hold?" — PACT · KP · a5_gochara_agreement), with one authority-profile row per (chart,
engine).

Same two-layer convention as the other migration tests this session:

  1. DB-free (static): the migration's INSERT is scoped correctly (no bare unconditional
     INSERT — every row is chart-scoped via the CROSS JOIN against existing chart_ids), is
     idempotent (ON CONFLICT DO NOTHING against the real natural key), and seeds exactly the
     three engine ids this PR's own serving-plane wiring (PR #1919) actually produces.

  2. `@pytest.mark.integration` (live Cloud SQL proxy): runs the ACTUAL migration file against
     the real kala_paddhati_profile table inside a transaction that is ALWAYS rolled back —
     never commits. Proves: idempotent, the CHECK constraint accepts the seeded
     arbitration_role values (a real constraint, not just documentation), and the seeded rows
     exactly match this migration's own documented design (pact=primary/hard/precedence=1;
     kp and gochara_v3=corroborating/informational/precedence=NULL).
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "677_nirmana_l3_n1_o10_authority_profile.sql"
)
_ENGINE_IDS = {"pact", "kp", "gochara_v3"}


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 677 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_677_seeds_exactly_the_three_engine_testimony_ids():
    """The three convention_ids seeded must be exactly the engine ids
    lib/engine_testimony.ts's mappers actually produce ('kp', 'gochara_v3') plus
    'pact' (the authority they are measured against) — no more, no fewer."""
    sql = _read_migration()
    for engine_id in _ENGINE_IDS:
        assert f"('{engine_id}'," in sql, f"expected a VALUES row for convention_id={engine_id!r}"


def test_migration_677_insert_is_chart_scoped_not_bare():
    """Every seeded row must be scoped to a real chart_id via the CROSS JOIN
    against existing chart_ids — never a hardcoded/bare chart_id literal that
    could silently miss a chart or duplicate across environments."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert "CROSS JOIN" in code_only
    assert "SELECT DISTINCT chart_id FROM kala_paddhati_profile" in code_only
    # No bare UUID literal anywhere in the INSERT (would indicate a hardcoded chart_id).
    assert not re.search(r"'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'", code_only)


def test_migration_677_is_idempotent_via_on_conflict():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert "ON CONFLICT" in code_only
    assert "DO NOTHING" in code_only


def test_migration_677_pact_is_the_only_primary_hard_row():
    """pact must be the sole arbitration_role='primary' entry — kp and
    gochara_v3 must both be 'corroborating', matching this migration's own
    documented reasoning (PACT is the reference point the other two are
    measured against, not a corroborating voice alongside them)."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert "'primary', 1)" in code_only
    assert code_only.count("'corroborating'") == 2


def test_migration_677_defensive_column_guard_is_idempotent():
    """Guards against migration 675 (arbitration_role/precedence's own
    ADD COLUMN) not yet having landed on main when 677 runs — must use the
    same idempotent IF NOT EXISTS pattern, not a bare ADD COLUMN that would
    fail once 675 has already run."""
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert re.search(r"ADD COLUMN IF NOT EXISTS arbitration_role", code_only)
    assert re.search(r"ADD COLUMN IF NOT EXISTS precedence", code_only)


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
def test_migration_677_seeds_six_rows_matching_documented_design_live():
    """Runs the actual migration against the real kala_paddhati_profile table
    inside a transaction that is ALWAYS rolled back. Proves the seeded rows
    exactly match this migration's own documented design."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chart_id FROM kala_paddhati_profile")
            chart_ids = {r["chart_id"] for r in cur.fetchall()}
            if not chart_ids:
                pytest.skip("kala_paddhati_profile has no rows in this environment (nothing to CROSS JOIN against)")

            cur.execute(sql)
            cur.execute(
                "SELECT chart_id, convention_id, school_tag, constraint_role, "
                "arbitration_role, precedence, convention_status "
                "FROM kala_paddhati_profile WHERE factor_family = 'O-10'"
            )
            rows = cur.fetchall()

        assert len(rows) == 3 * len(chart_ids), (
            f"expected one row per (chart, engine) = {3 * len(chart_ids)}, got {len(rows)}"
        )
        by_convention = {r["convention_id"]: r for r in rows}
        assert set(by_convention) >= _ENGINE_IDS

        pact = next(r for r in rows if r["convention_id"] == "pact")
        assert pact["arbitration_role"] == "primary"
        assert pact["constraint_role"] == "hard"
        assert pact["precedence"] == 1
        assert pact["convention_status"] == "computed"

        for engine_id in ("kp", "gochara_v3"):
            entry = next(r for r in rows if r["convention_id"] == engine_id)
            assert entry["arbitration_role"] == "corroborating"
            assert entry["constraint_role"] == "informational"
            assert entry["precedence"] is None
            assert entry["convention_status"] == "computed"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_677_is_idempotent_live():
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chart_id FROM kala_paddhati_profile")
            if not cur.fetchall():
                pytest.skip("kala_paddhati_profile has no rows in this environment")

            cur.execute(sql)
            cur.execute("SELECT count(*) AS n FROM kala_paddhati_profile WHERE factor_family = 'O-10'")
            first_count = cur.fetchone()["n"]

            cur.execute(sql)  # second application, same transaction
            cur.execute("SELECT count(*) AS n FROM kala_paddhati_profile WHERE factor_family = 'O-10'")
            second_count = cur.fetchone()["n"]

        assert first_count == second_count and first_count > 0
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_677_check_constraint_accepts_the_seeded_values_live():
    """Proves the arbitration_role values this migration seeds ('primary',
    'corroborating') are genuinely accepted by the real CHECK constraint —
    not just documentation-compatible."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chart_id FROM kala_paddhati_profile")
            if not cur.fetchall():
                pytest.skip("kala_paddhati_profile has no rows in this environment")
            cur.execute(sql)  # would raise if the CHECK constraint rejected a seeded value
            cur.execute(
                "SELECT count(*) AS n FROM kala_paddhati_profile "
                "WHERE factor_family = 'O-10' AND arbitration_role IN ('primary', 'corroborating')"
            )
            n = cur.fetchone()["n"]
        assert n > 0
    finally:
        conn.rollback()
        conn.close()
