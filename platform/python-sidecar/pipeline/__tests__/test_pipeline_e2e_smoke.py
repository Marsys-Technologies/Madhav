"""
E2E smoke test for the 5-ayanamsha build pipeline.

Requires a live DB connection (amjis via Cloud SQL proxy on 127.0.0.1:5433).
Creates a test build row, runs the full pipeline with stub writers, verifies
all pipeline mechanics end-to-end, and cleans up on exit.

Skip behaviour: all tests in this module are skipped automatically if the DB
is unreachable (e.g. in CI without the proxy).  No test should fail simply
because the DB is absent — it should skip.

Native chart used as test subject:
  Abhisek Mohanty · 1984-02-05 · 10:43 IST · Bhubaneswar
  chart_id = 362f9f17-95a5-490b-a5a7-027d3e0efda0 (canonical L1 subject)
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest

# ── DSN ───────────────────────────────────────────────────────────────────────
# Prefer an explicit env-var override; fall back to the production proxy DSN.
_DEFAULT_DSN = (
    "postgresql://amjis_app:aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
    "@127.0.0.1:5433/amjis"
)
DSN = os.environ.get("DB_URL", _DEFAULT_DSN)

# ── DB availability probe ─────────────────────────────────────────────────────


def _db_available() -> bool:
    """Return True iff a psycopg2 connection to DSN can be opened."""
    try:
        import psycopg2  # type: ignore[import]

        conn = psycopg2.connect(DSN)
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_available()

# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def conn():
    """
    Open a psycopg2 connection for one test function.
    autocommit=False so each test controls its own commit/rollback.
    Connection is closed (not rolled back globally) after the test; individual
    test methods call conn.commit() when they want changes to persist within
    their own transaction window.
    """
    import psycopg2  # type: ignore[import]

    c = psycopg2.connect(DSN)
    c.autocommit = False
    yield c
    try:
        c.rollback()
    except Exception:
        pass
    c.close()


@pytest.fixture(scope="function")
def test_build_id(conn):
    """
    Insert a test builds row and yield (build_id, chart_id).

    Cleanup: DELETE build_steps, build_notifications, builds rows that were
    inserted by this fixture, regardless of whether the test passed or failed.

    Skips automatically when no charts row is available in the DB.
    """
    # Resolve the native chart_id (or any chart if the native is missing).
    NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
    with conn.cursor() as cur:
        cur.execute(
            "SELECT chart_id FROM charts WHERE chart_id = %s LIMIT 1",
            (NATIVE_CHART_ID,),
        )
        row = cur.fetchone()
        if not row:
            # Fall back to any chart in the DB
            cur.execute("SELECT chart_id FROM charts LIMIT 1")
            row = cur.fetchone()

    if not row:
        pytest.skip("No charts rows in DB — create a chart first")

    chart_id = str(row[0])
    build_id = str(uuid.uuid4())

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO builds (
                build_id, chart_id, triggered_by_uid, triggered_by_role,
                engine_version, ayanamshas, status, queued_at
            )
            VALUES (
                %s, %s, 'smoke_test_uid', 'super_admin',
                'natal_engine/0.2.0-jh-parity',
                '["lahiri","true_chitra","kp","raman","surya_siddhanta"]'::jsonb,
                'queued', NOW()
            )
            """,
            (build_id, chart_id),
        )
    conn.commit()

    yield build_id, chart_id

    # ── Cleanup (always runs) ─────────────────────────────────────────────────
    # ON DELETE CASCADE handles build_steps + build_notifications automatically,
    # but we delete explicitly to be clear about what is being torn down.
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM build_steps WHERE build_id = %s",
                (build_id,),
            )
            cur.execute(
                "DELETE FROM build_notifications WHERE build_id = %s",
                (build_id,),
            )
            cur.execute(
                "DELETE FROM builds WHERE build_id = %s",
                (build_id,),
            )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


# ── Test class ────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available — skipping E2E smoke")
class TestPipelineE2ESmoke:
    """
    Six DB-integrated test cases covering the full 5-ayanamsha pipeline lifecycle.

    Test isolation: each test that needs to run the full pipeline calls
    create_build_steps() + run_build() itself.  Tests that only verify initial
    state rely solely on the fixture-inserted builds row.
    """

    # ── TC-1: build row created at 'queued' status ────────────────────────────

    def test_build_row_created_at_queued(self, conn, test_build_id):
        """
        TC-1: The fixture must have inserted a builds row with status='queued'.

        Verifies that the test harness itself is wired correctly before any
        pipeline code runs.
        """
        build_id, _chart_id = test_build_id
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM builds WHERE build_id = %s",
                (build_id,),
            )
            row = cur.fetchone()
        assert row is not None, "builds row not found after fixture insert"
        assert row[0] == "queued", f"expected status='queued', got '{row[0]}'"

    # ── TC-2: create_build_steps seeds 70 rows (14 assets × 5 ayanamshas) ────

    def test_create_build_steps_seeds_correct_row_count(self, conn, test_build_id):
        """
        TC-2: create_build_steps() must insert exactly 14 × 5 = 70 build_steps rows.

        14 assets in DAG_ORDER × 5 entries in CANONICAL_AYANAMSHAS = 70 slots.
        """
        from pipeline.build_chart import CANONICAL_AYANAMSHAS, create_build_steps

        build_id, _chart_id = test_build_id
        inserted = create_build_steps(conn, build_id, CANONICAL_AYANAMSHAS)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM build_steps WHERE build_id = %s",
                (build_id,),
            )
            db_count = cur.fetchone()[0]

        assert inserted == 70, f"create_build_steps() returned {inserted}, expected 70"
        assert db_count == 70, f"DB count is {db_count}, expected 70"

    # ── TC-3: check_cancellation returns False for a 'queued' build ──────────

    def test_check_cancellation_false_for_queued(self, conn, test_build_id):
        """
        TC-3: check_cancellation() must return False when builds.status = 'queued'.

        Sanity-checks the live DB path (not the mocked path in the unit tests).
        """
        from pipeline.build_chart import check_cancellation

        build_id, _chart_id = test_build_id
        result = check_cancellation(conn, build_id)
        assert result is False, (
            f"check_cancellation returned {result!r} for a queued build; expected False"
        )

    # ── TC-4: check_cancellation returns True after status set to 'cancelling' ─

    def test_cancellation_polling_detects_cancelling(self, conn, test_build_id):
        """
        TC-4: check_cancellation() must return True when builds.status = 'cancelling'.

        Exercises the live DB cancellation-polling path end-to-end.
        """
        from pipeline.build_chart import check_cancellation

        build_id, _chart_id = test_build_id

        # Flip the status to 'cancelling'
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE builds SET status = 'cancelling' WHERE build_id = %s",
                (build_id,),
            )
        conn.commit()

        assert check_cancellation(conn, build_id) is True, (
            "check_cancellation should return True after status set to 'cancelling'"
        )

        # Reset so other tests (if sharing state) won't be confused
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE builds SET status = 'queued' WHERE build_id = %s",
                (build_id,),
            )
        conn.commit()

    # ── TC-5: full pipeline runs to 'complete' with stub writers ─────────────

    def test_full_pipeline_runs_to_complete(self, conn, test_build_id):
        """
        TC-5: run_build() must return True and set builds.status = 'complete'.

        Uses stub writers (natal_engine not installed in test env) — all asset
        steps return 0 rows_written, which is correct for the stub path.
        """
        from pipeline.build_chart import (
            CANONICAL_AYANAMSHAS,
            create_build_steps,
            run_build,
        )

        build_id, chart_id = test_build_id
        create_build_steps(conn, build_id, CANONICAL_AYANAMSHAS)

        result = asyncio.run(run_build(build_id, chart_id, conn))

        assert result is True, (
            f"run_build returned {result!r}; expected True for a full stub run"
        )

        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM builds WHERE build_id = %s",
                (build_id,),
            )
            row = cur.fetchone()

        assert row is not None, "builds row disappeared after run_build"
        assert row[0] == "complete", (
            f"builds.status is '{row[0]}' after successful run; expected 'complete'"
        )

    # ── TC-6: all 70 build_steps marked 'complete' after successful run ───────

    def test_all_build_steps_complete_after_run(self, conn, test_build_id):
        """
        TC-6: After run_build() succeeds, all 70 build_steps rows must have
        status = 'complete'.

        This verifies that the DAG loop iterated all 14 assets and correctly
        updated every ayanamsha slot (5 per asset) to 'complete'.
        """
        from pipeline.build_chart import (
            CANONICAL_AYANAMSHAS,
            create_build_steps,
            run_build,
        )

        build_id, chart_id = test_build_id
        create_build_steps(conn, build_id, CANONICAL_AYANAMSHAS)
        asyncio.run(run_build(build_id, chart_id, conn))

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM build_steps WHERE build_id = %s",
                (build_id,),
            )
            total = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM build_steps "
                "WHERE build_id = %s AND status = 'complete'",
                (build_id,),
            )
            complete_count = cur.fetchone()[0]

        assert total == 70, f"Expected 70 total build_steps rows, got {total}"
        assert complete_count == 70, (
            f"Expected 70 'complete' rows, got {complete_count} "
            f"(total={total})"
        )

    # ── TC-7: build_notifications emitted (build_started + build_complete) ────

    def test_build_notifications_emitted(self, conn, test_build_id):
        """
        TC-7: run_build() must emit at least build_started + build_complete
        notifications (via emit_event).

        Verifies the SSE/notification pipeline is wired into the build loop.
        """
        from pipeline.build_chart import (
            CANONICAL_AYANAMSHAS,
            create_build_steps,
            run_build,
        )

        build_id, chart_id = test_build_id
        create_build_steps(conn, build_id, CANONICAL_AYANAMSHAS)
        asyncio.run(run_build(build_id, chart_id, conn))

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*), array_agg(DISTINCT event_type ORDER BY event_type) "
                "FROM build_notifications WHERE build_id = %s",
                (build_id,),
            )
            row = cur.fetchone()

        notif_count, event_types = row
        assert notif_count > 0, (
            "No build_notifications rows found — emit_event is not writing to DB"
        )

        event_types_set = set(event_types or [])
        assert "build_started" in event_types_set, (
            f"'build_started' event missing from notifications; found: {event_types_set}"
        )
        assert "build_complete" in event_types_set, (
            f"'build_complete' event missing from notifications; found: {event_types_set}"
        )
