"""
Migration 127 verification tests: build_notifications SSE event log table
MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-04]
"""
import json
import os
import uuid
import pytest
import psycopg2
import psycopg2.extras


DB_PARAMS = {
    "host": "127.0.0.1",
    "port": 5433,
    "user": "amjis_app",
    "password": os.environ.get("PGPASSWORD", ""),
    "dbname": "amjis",
}

EXPECTED_COLUMNS = {
    "notif_id",
    "build_id",
    "event_type",
    "payload",
    "created_at",
    "delivered_at",
    "subscriber_id",
}

VALID_EVENT_TYPES = [
    "build_queued",
    "build_started",
    "step_started",
    "step_complete",
    "step_failed",
    "build_complete",
    "build_failed",
    "build_cancelled",
]

# A real chart_id that exists in the DB (needed for builds FK)
FIXTURE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"


def _insert_build(conn_or_cur):
    """Insert a minimal builds row and return its build_id.

    Accepts either a connection (opens a plain cursor internally) or a cursor.
    Always reads the result via integer index so it works regardless of
    cursor_factory on the caller's cursor.
    """
    # If passed a cursor, get its connection; otherwise use directly.
    conn = getattr(conn_or_cur, "connection", conn_or_cur)
    with conn.cursor() as plain_cur:
        plain_cur.execute(
            """
            INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
            VALUES (%s, 'test-uid-127', 'super_admin', 'queued')
            RETURNING build_id
            """,
            (FIXTURE_CHART_ID,),
        )
        return plain_cur.fetchone()[0]


def _insert_notification(conn_or_cur, build_id, event_type="build_queued", **kwargs):
    """Insert a minimal build_notifications row and return its notif_id.

    Uses a plain cursor internally so integer-index access always works,
    regardless of cursor_factory on the caller's cursor.
    """
    payload = kwargs.get("payload", "{}")
    subscriber_id = kwargs.get("subscriber_id", None)
    conn = getattr(conn_or_cur, "connection", conn_or_cur)
    with conn.cursor() as plain_cur:
        plain_cur.execute(
            """
            INSERT INTO build_notifications (build_id, event_type, payload, subscriber_id)
            VALUES (%s, %s, %s::jsonb, %s)
            RETURNING notif_id
            """,
            (build_id, event_type, payload, subscriber_id),
        )
        return plain_cur.fetchone()[0]


@pytest.fixture(scope="module")
def conn():
    c = psycopg2.connect(**DB_PARAMS)
    c.autocommit = False
    yield c
    c.rollback()
    c.close()


@pytest.fixture(autouse=True)
def rollback_after(conn):
    """Roll back each test's writes so tests are independent."""
    yield
    conn.rollback()


# ── 1. Table exists ───────────────────────────────────────────────────────────
def test_table_exists(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.build_notifications')::text")
        assert cur.fetchone()[0] == "build_notifications"


# ── 2. All expected columns are present ──────────────────────────────────────
def test_all_columns_present(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'build_notifications'
            """
        )
        cols = {row[0] for row in cur.fetchall()}
    assert EXPECTED_COLUMNS <= cols, f"Missing columns: {EXPECTED_COLUMNS - cols}"


# ── 3. All 8 valid event_type values are accepted ────────────────────────────
@pytest.mark.parametrize("event_type", VALID_EVENT_TYPES)
def test_valid_event_types_accepted(conn, event_type):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)
        notif_id = _insert_notification(cur, build_id, event_type=event_type)
        assert notif_id is not None


# ── 4. Invalid event_type raises CheckViolation ───────────────────────────────
def test_invalid_event_type_raises_check_violation(conn):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute(
                """
                INSERT INTO build_notifications (build_id, event_type)
                VALUES (%s, 'invalid_event')
                """,
                (build_id,),
            )


# ── 5. delivered_at is nullable ──────────────────────────────────────────────
def test_delivered_at_is_nullable(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        build_id = _insert_build(cur)
        cur.execute(
            """
            INSERT INTO build_notifications (build_id, event_type)
            VALUES (%s, 'build_queued')
            RETURNING delivered_at
            """,
            (build_id,),
        )
        row = cur.fetchone()
    assert row["delivered_at"] is None


# ── 6. subscriber_id is nullable ─────────────────────────────────────────────
def test_subscriber_id_is_nullable(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        build_id = _insert_build(cur)
        cur.execute(
            """
            INSERT INTO build_notifications (build_id, event_type)
            VALUES (%s, 'build_started')
            RETURNING subscriber_id
            """,
            (build_id,),
        )
        row = cur.fetchone()
    assert row["subscriber_id"] is None


# ── 7. payload JSONB defaults to '{}' ────────────────────────────────────────
def test_payload_jsonb_default(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        build_id = _insert_build(cur)
        cur.execute(
            """
            INSERT INTO build_notifications (build_id, event_type)
            VALUES (%s, 'step_started')
            RETURNING payload
            """,
            (build_id,),
        )
        row = cur.fetchone()
    assert row["payload"] == {}


# ── 8. FK cascade: deleting the build removes notifications ──────────────────
def test_fk_cascade_on_build_delete(conn):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)
        _insert_notification(cur, build_id, event_type="build_queued")
        _insert_notification(cur, build_id, event_type="build_started")

        # Verify rows exist before delete
        cur.execute(
            "SELECT COUNT(*) FROM build_notifications WHERE build_id = %s",
            (build_id,),
        )
        assert cur.fetchone()[0] == 2

        # Delete the parent build — cascade must propagate
        cur.execute("DELETE FROM builds WHERE build_id = %s", (build_id,))

        cur.execute(
            "SELECT COUNT(*) FROM build_notifications WHERE build_id = %s",
            (build_id,),
        )
        assert cur.fetchone()[0] == 0, "Cascade delete failed — notifications still present"


# ── 9. Partial undelivered index is present ───────────────────────────────────
def test_undelivered_partial_index_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename  = 'build_notifications'
              AND indexname  = 'build_notif_undelivered_idx'
            """
        )
        assert cur.fetchone() is not None, "Partial index build_notif_undelivered_idx not found"


# ── 10. build_notif_build_idx (composite) is present ─────────────────────────
def test_build_notif_build_idx_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename  = 'build_notifications'
              AND indexname  = 'build_notif_build_idx'
            """
        )
        assert cur.fetchone() is not None, "Index build_notif_build_idx not found"


# ── 11. Insert + query round-trip with JSONB payload ─────────────────────────
def test_insert_query_roundtrip_with_jsonb_payload(conn):
    sample_payload = {"step": "lahiri", "progress": 42, "details": {"rows": 1000}}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        build_id = _insert_build(cur)
        cur.execute(
            """
            INSERT INTO build_notifications (
                build_id, event_type, payload, subscriber_id
            )
            VALUES (%s, 'step_complete', %s::jsonb, 'client-abc-123')
            RETURNING *
            """,
            (build_id, json.dumps(sample_payload)),
        )
        row = cur.fetchone()

    assert row["build_id"] == build_id
    assert row["event_type"] == "step_complete"
    assert row["payload"] == sample_payload
    assert row["subscriber_id"] == "client-abc-123"
    assert row["notif_id"] is not None
    assert row["created_at"] is not None
    assert row["delivered_at"] is None


# ── 12. delivered_at can be set (marking delivery) ───────────────────────────
def test_delivered_at_can_be_set(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        build_id = _insert_build(cur)
        notif_id = _insert_notification(cur, build_id, event_type="build_complete")

        cur.execute(
            """
            UPDATE build_notifications
               SET delivered_at = NOW()
             WHERE notif_id = %s
            RETURNING delivered_at
            """,
            (notif_id,),
        )
        row = cur.fetchone()
    assert row["delivered_at"] is not None


# ── 13. FK to builds enforced (bogus build_id raises ForeignKeyViolation) ─────
def test_fk_to_builds_enforced(conn):
    with conn.cursor() as cur:
        bogus_build_id = str(uuid.uuid4())
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            cur.execute(
                """
                INSERT INTO build_notifications (build_id, event_type)
                VALUES (%s, 'build_queued')
                """,
                (bogus_build_id,),
            )
