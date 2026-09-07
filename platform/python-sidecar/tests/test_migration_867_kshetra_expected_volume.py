"""
tests/test_migration_867_kshetra_expected_volume.py — L3 Kāla, F-L3-4 slice:
migration 867 populates `asset_registry.expected_volume_formula` /
`expected_volume_inputs` / `volume_explanation` for `ka_kshetra` (target_floor
8,599,775 was already a genuine achieved-count floor; only the derivation
was undocumented). This is the LAST of the 20 originally-NULL L3 assets.

`ka_kshetra` (14,000+ line, 25-file numerical pipeline) turned out to have a
tractable row-count shape despite its scoring complexity: 25 discovered
event classes x 343991 breakpoint-derived segments each, class-invariant
(identical count for every one of the 25 classes) and with
refinement_depth=0 for every row (no adaptive subdivision ever fired). The
internal knot-density mechanics behind 343991 are honestly left
undecomposed.

Same convention: DB-free static guards + a no-self-transaction-wrapper
check, plus `@pytest.mark.integration` live tests (rolled back, never
committed) that independently re-derive the per-class uniformity and
refinement_depth claim from kala_field directly, not trusted from the
migration's own recorded numbers.
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
    _REPO_ROOT, "platform", "migrations", "867_nirmana_l3_w3_kshetra_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 867 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_867_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_kshetra'" in updates[0]


def test_migration_867_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_867_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_867_multiplication_is_exact():
    sql = _read_migration()
    assert "'event_classes', 25" in sql
    assert "'segments_per_class', 343991" in sql
    assert "'total', 8599775" in sql
    assert 25 * 343991 == 8599775


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
def test_migration_867_per_class_uniformity_and_refinement_depth_live():
    """Independently re-verifies the migration's central claims against
    kala_field directly, not trusted from the migration's own recorded
    numbers: every discovered event class has exactly the same segment
    count, and refinement_depth is 0 everywhere."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT event_class, COUNT(*) AS n, MIN(refinement_depth) AS min_d, "
                "MAX(refinement_depth) AS max_d FROM kala_field "
                "WHERE chart_id = %s GROUP BY event_class",
                (_CANONICAL_CHART_ID,),
            )
            rows = cur.fetchall()
        if not rows:
            pytest.skip("kala_field has no rows for the canonical chart in this environment")

        assert len(rows) == 25, f"expected 25 event classes, got {len(rows)}"
        counts = {r["n"] for r in rows}
        assert counts == {343991}, f"expected uniform 343991 per class, got {counts}"
        for r in rows:
            assert r["min_d"] == 0 and r["max_d"] == 0, f"{r['event_class']}: refinement_depth not uniformly 0"
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_867_sets_volume_fields_and_matches_live_count_sql():
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
                "target_floor FROM asset_registry WHERE asset_id = 'ka_kshetra'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_kshetra not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]
        assert recorded_total == observed["event_classes"] * observed["segments_per_class"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_field WHERE chart_id = %s",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_field has no rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_867_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_kshetra'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_kshetra not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_kshetra'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
