"""
test_bg_sarvatobhadra_grid_throughput — G4a SAMPŪRTI L0b

ROOT CAUSE VERIFIED (R16 — every status claim cites the exact query):

  bg_sarvatobhadra_grid was registered in migration 529 (applied 2026-08-02,
  _migrations_applied id=389) with has_writer=false and target_floor=0.
  The table exists and has 0 rows — as designed per ADJUDICATION-11 Part 2
  (migration 529 comment: "DELIBERATELY EMPTY. An empty school-keyed table
  honestly states that SBC grid variants exist and none is currently held/
  selected, rather than seating one tradition's grid as an unqualified L0
  fact (a B.1 layer violation).").

  The global_runner (pipeline/orchestrator/global_runner.py) returns "deferred"
  (line 158) for assets with no registered writer, and NEVER calls
  _upsert_asset_throughput_global() in that code path — so bg_sarvatobhadra_grid
  has NO asset_throughput row at all (verified:
    SELECT state FROM asset_throughput WHERE asset_id='bg_sarvatobhadra_grid'
      AND chart_id IS NULL  → 0 rows).

  This makes the asset invisible to the cockpit/stats route even though its
  designed state (0 rows, no writer, deliberately empty) is correct by intent.
  The fix is to upsert a sentinel asset_throughput row with state='lit' and
  rows_written=0, matching the bg_panchanga precedent for a data-only global
  asset whose designed state is zero rows (bg_panchanga: state='lit',
  rows_written=0, verified live).

TDD SEQUENCE:
  1. This test is written FIRST (before migration 553) — it fails on a live DB
     because the asset_throughput row is absent.
  2. Migration 553_bg_sarvatobhadra_grid_throughput_sentinel.sql is applied.
  3. This test then passes.

CONTENT ROWS DELIBERATELY ABSENT (B.10 / B.1 compliance):
  The bg_sarvatobhadra_grid table remains at 0 rows. The SBC grid geometry
  varies by Jyotish tradition; no single school has been source-verified in
  the repo corpus. Inserting SBC vedha-pair rows without native approval and
  a verified source text would be a B.1 violation (structural_prior-masquerading-
  as-fact) and a B.10 violation (fabricated classical data). The sentinel row
  ONLY repairs monitoring visibility; it does not populate the grid.

  Activation path (zero code change required — per migration 529 comment):
  A future native-approved, source-verified school's grid activates automatically
  when rows land in bg_sarvatobhadra_grid under a school_tag.
"""
from __future__ import annotations

import os

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL not set — live DB test skipped",
)
class TestBgSarvatobhadraGridThroughput:
    """
    Live-DB guard: after migration 553, bg_sarvatobhadra_grid must have a
    sentinel asset_throughput row with state='lit', confirming it is monitored
    as a correctly-empty-by-design global asset.

    Run with: DATABASE_URL=<url> pytest tests/test_bg_sarvatobhadra_grid_throughput.py -v
    """

    def _conn(self):
        import psycopg
        import psycopg.rows
        return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)

    # ── Test 1: asset_registry sanity (must pass before and after migration) ──

    def test_asset_registry_row_exists_and_is_correct(self):
        """
        Exact query:
          SELECT asset_id, has_writer, target_floor, scope, is_active
          FROM asset_registry
          WHERE asset_id = 'bg_sarvatobhadra_grid';
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT asset_id, has_writer, target_floor, scope, is_active
                    FROM asset_registry
                    WHERE asset_id = 'bg_sarvatobhadra_grid'
                    """
                )
                row = cur.fetchone()
        assert row is not None, "bg_sarvatobhadra_grid missing from asset_registry"
        assert row["has_writer"] is False, (
            f"bg_sarvatobhadra_grid has_writer should be False (deliberately "
            f"empty, data-only); got {row['has_writer']}"
        )
        assert row["target_floor"] == 0, (
            f"bg_sarvatobhadra_grid target_floor should be 0; got {row['target_floor']}"
        )
        assert row["scope"] == "global", (
            f"bg_sarvatobhadra_grid scope should be 'global'; got {row['scope']}"
        )
        assert row["is_active"] is True, (
            f"bg_sarvatobhadra_grid should be is_active=True; got {row['is_active']}"
        )

    # ── Test 2: content table row count (must be 0, by design) ───────────────

    def test_content_table_has_zero_rows_by_design(self):
        """
        Exact query: SELECT COUNT(*) AS n FROM bg_sarvatobhadra_grid;

        Zero rows is CORRECT per ADJUDICATION-11 Part 2 / migration 529
        (deliberately empty). This test asserts the design intent, not a defect.
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM bg_sarvatobhadra_grid")
                row = cur.fetchone()
        assert row["n"] == 0, (
            f"bg_sarvatobhadra_grid should have 0 rows (deliberately empty "
            f"per ADJUDICATION-11); got {row['n']}. "
            f"If rows were added, verify native approval + source citation per B.1/B.10."
        )

    # ── Test 3: throughput sentinel row (FAILS before migration 553, passes after) ──

    def test_asset_throughput_sentinel_row_is_lit(self):
        """
        Exact query:
          SELECT state, rows_written, chart_id
          FROM asset_throughput
          WHERE asset_id = 'bg_sarvatobhadra_grid' AND chart_id IS NULL;

        BEFORE migration 553: 0 rows → this test FAILS.
        AFTER migration 553: 1 row with state='lit', rows_written=0 → PASSES.

        Root cause documented above: global_runner returns 'deferred' for
        has_writer=false assets without calling _upsert_asset_throughput_global(),
        leaving no throughput row. Migration 553 upserts the sentinel directly,
        matching the bg_panchanga precedent.
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT state, rows_written, chart_id
                    FROM asset_throughput
                    WHERE asset_id = 'bg_sarvatobhadra_grid'
                      AND chart_id IS NULL
                    """
                )
                row = cur.fetchone()

        assert row is not None, (
            "bg_sarvatobhadra_grid has no asset_throughput row (chart_id IS NULL). "
            "Migration 553_bg_sarvatobhadra_grid_throughput_sentinel.sql must be "
            "applied to register the monitoring sentinel. "
            "Root cause: global_runner._run_asset_writer() returns 'deferred' for "
            "has_writer=false assets without upserting asset_throughput, leaving "
            "this global asset invisible to the cockpit/stats route."
        )
        assert row["state"] == "lit", (
            f"bg_sarvatobhadra_grid throughput sentinel should have state='lit'; "
            f"got {row['state']!r}. "
            f"Zero rows is correct (deliberately empty by ADJUDICATION-11 design); "
            f"state='lit' signals 'monitoring-visible, intentionally empty'."
        )
        assert row["rows_written"] == 0, (
            f"bg_sarvatobhadra_grid throughput sentinel rows_written should be 0 "
            f"(deliberately empty by design); got {row['rows_written']}"
        )
        assert row["chart_id"] is None, (
            f"bg_sarvatobhadra_grid is a global (chart_id IS NULL) asset; "
            f"sentinel row should have chart_id=NULL, got {row['chart_id']}"
        )

    # ── Test 4: count_sql matches actual row count ─────────────────────────────

    def test_count_sql_returns_zero(self):
        """
        Exact query: SELECT COUNT(*) FROM bg_sarvatobhadra_grid
        (this is the asset_registry.count_sql value for this asset).

        Cockpit truth principle (§N.4): count_sql must return the real count.
        With 0 rows by design, count_sql must return 0.
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM bg_sarvatobhadra_grid")
                row = cur.fetchone()
        assert row["n"] == 0, (
            f"count_sql 'SELECT COUNT(*) FROM bg_sarvatobhadra_grid' returned {row['n']}; "
            f"expected 0 (deliberately empty by design)."
        )
