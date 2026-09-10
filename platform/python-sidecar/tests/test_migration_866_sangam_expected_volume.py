"""
tests/test_migration_866_sangam_expected_volume.py — L3 Kāla, F-L3-4 slice:
migration 866 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_sangam` (target_floor
14868 was already a genuine achieved-count floor; only the derivation was
undocumented).

This closes a two-cycle investigation (see L3_STATE.md heartbeat/Held-items
history). The unreconciled ~2.3x gap between a naive Mode-D estimate and the
live total had two real causes, both verified by running the actual
production code rather than approximating further:

  1. Mode D (`mode_d_av_bindhu`) fires only for a substep whose sole
     predicate is NOT signature_class SUBSYSTEM (SUBSYSTEM predicates route
     to Mode C with a `continue` before the Mode D block). Only 25 of this
     chart's 60 lifetime substeps qualify.
  2. `_derive_birth_year` reads MIN(chart_dashas.start_date) at level_n=1 —
     the theoretical pre-birth balance-of-dasha start (1950), not the
     native's real 1984 birth — so Mode D's lifetime horizon is actually
     [1950-01-01, 2050-12-31].

25 qualifying substeps x 478 real ingress-search windows (computed via
pipeline.transit_search.find_ingress_events directly against live
ephemeris) = 11950, exactly matching the live mode='D' row count. The
remaining 2918 rows (Modes A/B/C) are honestly left undecomposed as
per-predicate-alignment-dependent.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed) that independently re-derive the qualifying-substep count and
the mode/tier breakdown from source tables directly.
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
    _REPO_ROOT, "platform", "migrations", "866_nirmana_l3_w3_sangam_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 866 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_866_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_sangam'" in updates[0]


def test_migration_866_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_866_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_866_mode_d_arithmetic_is_exact():
    sql = _read_migration()
    assert "'qualifying_lifetime_substeps', 25" in sql
    assert "'windows_per_qualifying_substep', 478" in sql
    assert "'mode_d_total', 11950" in sql
    assert 25 * 478 == 11950


def test_migration_866_total_reconciles():
    sql = _read_migration()
    assert "'modes_abc_total', 2918" in sql
    assert "'total', 14868" in sql
    assert 11950 + 2918 == 14868


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
def test_migration_866_qualifying_substep_count_matches_live_data():
    """Independently re-derives the 25-of-60 qualifying-substep claim from
    kala_convergence/kala_activation_predicates directly — not trusted from
    the migration's own recorded numbers."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(DISTINCT signal_id) AS n FROM kala_convergence "
                "WHERE chart_id = %s AND horizon_tier = 'lifetime'",
                (_CANONICAL_CHART_ID,),
            )
            total_substeps = cur.fetchone()
            cur.execute(
                "SELECT COUNT(DISTINCT signal_id) AS n FROM kala_convergence "
                "WHERE chart_id = %s AND horizon_tier = 'lifetime' AND mode = 'D'",
                (_CANONICAL_CHART_ID,),
            )
            qualifying = cur.fetchone()
        if total_substeps is None or total_substeps["n"] == 0:
            pytest.skip("kala_convergence has no lifetime-tier rows for the canonical chart in this environment")
        assert total_substeps["n"] == 60
        assert qualifying["n"] == 25

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.signature_class, COUNT(DISTINCT kc.signal_id) AS n
                FROM kala_convergence kc
                JOIN kala_activation_predicates p
                  ON p.signal_id = kc.signal_id AND p.chart_id = kc.chart_id
                WHERE kc.chart_id = %s AND kc.horizon_tier = 'lifetime' AND kc.mode = 'D'
                GROUP BY p.signature_class
                """,
                (_CANONICAL_CHART_ID,),
            )
            by_class = {r["signature_class"]: r["n"] for r in cur.fetchall()}
        assert by_class == {
            "CLASSIFY_RESIDUAL": 5, "DIGNITY": 5, "DISPOSITOR_RELATIONAL": 5,
            "DOSHA": 5, "YOGA": 5,
        }
        assert "SUBSYSTEM" not in by_class
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_866_mode_tier_breakdown_matches_live_data():
    """Independently re-derives the full mode/tier breakdown from
    kala_convergence directly."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT horizon_tier, mode, COUNT(*) AS n FROM kala_convergence "
                "WHERE chart_id = %s GROUP BY horizon_tier, mode",
                (_CANONICAL_CHART_ID,),
            )
            rows = {(r["horizon_tier"], r["mode"]): r["n"] for r in cur.fetchall()}
        if not rows:
            pytest.skip("kala_convergence has no rows for the canonical chart in this environment")
        assert rows == {
            ("near", "A"): 484, ("near", "B"): 361, ("near", "C"): 119,
            ("lifetime", "A"): 644, ("lifetime", "B"): 505, ("lifetime", "C"): 805,
            ("lifetime", "D"): 11950,
        }
        assert sum(rows.values()) == 14868
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_866_sets_volume_fields_and_matches_live_count_sql():
    """Runs the actual migration file against the real asset_registry table
    inside a transaction that is ALWAYS rolled back. Proves the recorded
    total matches the live count_sql result for the canonical chart today —
    not a stale or invented number."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation, "
                "target_floor FROM asset_registry WHERE asset_id = 'ka_sangam'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_sangam not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]
        assert recorded_total == observed["mode_d_total"] + observed["modes_abc_total"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_convergence WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_convergence has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_866_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_sangam'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_sangam not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_sangam'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
