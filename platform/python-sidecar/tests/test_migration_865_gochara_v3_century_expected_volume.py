"""
tests/test_migration_865_gochara_v3_century_expected_volume.py — L3 Kāla,
F-L3-4 slice: migration 865 populates `asset_registry.expected_volume_formula`
/ `expected_volume_inputs` / `volume_explanation` for
`ka_gochara_v3_century_materialize` (target_floor 914 was already a genuine
achieved-count floor; only the derivation was undocumented).

This asset was deferred in several preceding cycles as too complex for one
bounded unit (2480-line writer, peak-anchored era/month/day hierarchy). This
migration is the result of separating the ROW-COUNT shape (tractable) from
the intensity-scoring internals (not touched, not needed for volume
documentation): 18 of 27 event classes serve a flat, one-row-per-
threshold-crossing-interval production; the other 9 additionally get up to 3
peak-anchored month rows and 3 day rows per era window
(MAX_PEAKS_PER_ERA_WINDOW).

A first draft of this migration wrongly generalised the flat tier to a
uniform "10 rows per class" from an incomplete query truncated by a terminal
page limit — self-caught by re-running the FULL, untruncated breakdown before
committing. This test file's live checks independently re-derive the full
per-(event_class, resolution) breakdown from kala_gochara_windows_v2 itself,
not trusted from the migration's own recorded numbers, specifically to catch
a repeat of that class of error.

Same convention: DB-free static guards + a no-self-transaction-wrapper check,
plus `@pytest.mark.integration` live tests (rolled back, never committed).
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
    _REPO_ROOT, "platform", "migrations", "865_nirmana_l3_w3_gochara_v3_century_expected_volume.sql"
)

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 865 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_865_updates_exactly_one_asset():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    updates = re.findall(r"UPDATE asset_registry\s+SET.*?;", code_only, re.S)
    assert len(updates) == 1, f"expected exactly 1 UPDATE, found {len(updates)}"
    assert "WHERE asset_id = 'ka_gochara_v3_century_materialize'" in updates[0]


def test_migration_865_no_self_transaction_wrapper():
    sql = _read_migration()
    code_only = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


def test_migration_865_is_guarded_by_null_check():
    sql = _read_migration()
    assert "expected_volume_formula IS NULL" in sql


def test_migration_865_observed_breakdown_sums_to_target_floor():
    sql = _read_migration()
    assert "'flat_rows', 290" in sql
    assert "'hierarchy_era_rows', 90" in sql
    assert "'hierarchy_month_rows', 267" in sql
    assert "'hierarchy_day_rows', 267" in sql
    assert "'total', 914" in sql
    assert 290 + 90 + 267 + 267 == 914


def test_migration_865_does_not_claim_flat_tier_is_uniform():
    """Guards against a repeat of this migration's own self-caught first-
    draft error (generalising the flat tier to a uniform 10 rows/class from
    a truncated query)."""
    sql = _read_migration()
    assert "10-40 rows per class" in sql or "10 to 40 rows per class" in sql
    assert "genuinely class- and chart-specific" in sql


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
def test_migration_865_full_breakdown_matches_live_data():
    """Independently re-derives the COMPLETE per-(event_class, resolution)
    breakdown from kala_gochara_windows_v2 directly — not trusted from the
    migration's own recorded numbers, and NOT limited/truncated (the exact
    mistake a first draft of this migration made by trusting a paged
    terminal query)."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_class, resolution, COUNT(*) AS n
                FROM kala_gochara_windows_v2
                WHERE chart_id = %s AND generation LIKE 'g3_%%'
                GROUP BY event_class, resolution
                """,
                (_CANONICAL_CHART_ID,),
            )
            rows = cur.fetchall()
        if not rows:
            pytest.skip("kala_gochara_windows_v2 has no generation='g3_%' rows for the canonical chart in this environment")

        by_class: dict[str, dict] = {}
        for r in rows:
            by_class.setdefault(r["event_class"], {})[r["resolution"] or "FLAT"] = r["n"]

        assert len(by_class) == 27, f"expected 27 event classes, got {len(by_class)}"

        flat_total = 0
        era_total = month_total = day_total = 0
        hierarchy_classes = 0
        for cls, tiers in by_class.items():
            if set(tiers.keys()) == {"FLAT"}:
                flat_total += tiers["FLAT"]
            else:
                assert set(tiers.keys()) == {"era", "month", "day"}, f"{cls}: unexpected tier set {tiers.keys()}"
                hierarchy_classes += 1
                era_total += tiers["era"]
                month_total += tiers["month"]
                day_total += tiers["day"]

        assert flat_total == 290
        assert hierarchy_classes == 9
        assert era_total == 90
        assert month_total == 267
        assert day_total == 267
        assert flat_total + era_total + month_total + day_total == 914
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_865_sets_volume_fields_and_matches_live_count_sql():
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
                "target_floor FROM asset_registry WHERE asset_id = 'ka_gochara_v3_century_materialize'"
            )
            row = cur.fetchone()
        assert row is not None, "ka_gochara_v3_century_materialize not present in asset_registry in this environment"
        assert row["expected_volume_formula"] is not None
        assert row["volume_explanation"] is not None

        inputs = row["expected_volume_inputs"]
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        observed = inputs["observed_2026_09_07"][_CANONICAL_CHART_ID]
        recorded_total = observed["total"]
        assert recorded_total == (
            observed["flat_rows"] + observed["hierarchy_era_rows"]
            + observed["hierarchy_month_rows"] + observed["hierarchy_day_rows"]
        )

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM kala_gochara_windows_v2 WHERE chart_id = %s AND generation LIKE 'g3_%%'",
                (_CANONICAL_CHART_ID,),
            )
            live_row = cur.fetchone()
        if live_row is None or live_row["n"] == 0:
            pytest.skip("kala_gochara_windows_v2 has no generation='g3_%' rows for the canonical chart in this environment")

        assert recorded_total == live_row["n"] == row["target_floor"], (
            f"recorded observed total {recorded_total} != live count {live_row['n']} "
            f"or != target_floor {row['target_floor']}"
        )
    finally:
        conn.rollback()  # NEVER persists — dry-run only, matches this session's discipline
        conn.close()


@pytest.mark.integration
def test_migration_865_is_idempotent_live():
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
                "FROM asset_registry WHERE asset_id = 'ka_gochara_v3_century_materialize'"
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip("ka_gochara_v3_century_materialize not present in asset_registry in this environment")
            first_pass = (row["expected_volume_formula"], row["expected_volume_inputs"], row["volume_explanation"])

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT expected_volume_formula, expected_volume_inputs, volume_explanation "
                "FROM asset_registry WHERE asset_id = 'ka_gochara_v3_century_materialize'"
            )
            row2 = cur.fetchone()
            second_pass = (row2["expected_volume_formula"], row2["expected_volume_inputs"], row2["volume_explanation"])

        assert first_pass == second_pass, "migration is not idempotent — second pass changed the stored values"
    finally:
        conn.rollback()
        conn.close()
