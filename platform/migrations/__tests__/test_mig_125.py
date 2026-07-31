"""
Migration 125 verification tests: build_steps table
MARSYS-JIS Multi-Ayanamsha Build Orchestrator
"""
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
    "step_id",
    "build_id",
    "ayanamsha_id",
    "category",
    "status",
    "started_at",
    "completed_at",
    "error_msg",
    "row_count",
    "duration_ms",
    "created_at",
}

VALID_STATUSES = ["queued", "running", "complete", "failed", "skipped"]


@pytest.fixture(scope="module")
def conn():
    connection = psycopg2.connect(**DB_PARAMS)
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture(scope="module")
def sample_build_id(conn):
    """Fetch a real chart_id from charts, insert a builds row, return its build_id."""
    with conn.cursor() as cur:
        cur.execute("SELECT chart_id FROM charts LIMIT 1")
        row = cur.fetchone()
    if row is None:
        pytest.skip("No rows in charts table — FK prerequisite not met")
    chart_id = row[0]
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
            VALUES (%s, %s, %s, %s)
            RETURNING build_id
            """,
            (chart_id, "test_mig125_uid", "super_admin", "queued"),
        )
        build_id = cur.fetchone()[0]
    conn.commit()
    yield build_id
    # Cleanup: deleting the build cascades to any build_steps rows inserted during tests
    with conn.cursor() as cur:
        cur.execute("DELETE FROM builds WHERE build_id = %s", (build_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# T01 — table exists
# ---------------------------------------------------------------------------
def test_build_steps_table_exists(conn):
    """build_steps table must exist in public schema."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'build_steps'
            """
        )
        count = cur.fetchone()[0]
    assert count == 1, "build_steps table not found in public schema"


# ---------------------------------------------------------------------------
# T02 — all expected columns present
# ---------------------------------------------------------------------------
def test_build_steps_columns(conn):
    """All expected columns must be present on the build_steps table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'build_steps'
            """
        )
        actual = {row[0] for row in cur.fetchall()}
    missing = EXPECTED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"


# ---------------------------------------------------------------------------
# T03 — primary key on step_id
# ---------------------------------------------------------------------------
def test_build_steps_primary_key(conn):
    """step_id must be the primary key."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kc.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kc
              ON tc.constraint_name = kc.constraint_name
             AND tc.table_schema = kc.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name = 'build_steps'
              AND tc.constraint_type = 'PRIMARY KEY'
            """
        )
        pk_cols = [row[0] for row in cur.fetchall()]
    assert pk_cols == ["step_id"], f"Unexpected primary key columns: {pk_cols}"


# ---------------------------------------------------------------------------
# T04 — FK violation: invalid build_id raises IntegrityError
# ---------------------------------------------------------------------------
def test_invalid_build_id_fk_violation(conn):
    """Inserting a build_step with a non-existent build_id must raise FK violation."""
    bogus_build_id = str(uuid.uuid4())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category)
                VALUES (%s, %s, %s)
                """,
                (bogus_build_id, "lahiri", "planets"),
            )
        conn.rollback()
        pytest.fail("Expected ForeignKeyViolation but no error was raised")
    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()


# ---------------------------------------------------------------------------
# T05 — default status is 'queued'
# ---------------------------------------------------------------------------
def test_default_status_is_queued(conn, sample_build_id):
    """Omitting status on insert should default to 'queued'."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category)
                VALUES (%s, %s, %s)
                RETURNING status
                """,
                (sample_build_id, "lahiri", "planets"),
            )
            status = cur.fetchone()[0]
        assert status == "queued", f"Expected default status 'queued', got '{status}'"
    finally:
        conn.rollback()


# ---------------------------------------------------------------------------
# T06 — all valid statuses accepted
# ---------------------------------------------------------------------------
def test_valid_statuses_accepted(conn, sample_build_id):
    """Each valid status string must insert without constraint error."""
    inserted = []
    try:
        with conn.cursor() as cur:
            for status in VALID_STATUSES:
                cur.execute(
                    """
                    INSERT INTO build_steps (build_id, ayanamsha_id, category, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING step_id
                    """,
                    (sample_build_id, "lahiri", "planets", status),
                )
                inserted.append(cur.fetchone()[0])
        assert len(inserted) == len(VALID_STATUSES), "Not all valid statuses inserted"
    finally:
        conn.rollback()


# ---------------------------------------------------------------------------
# T07 — invalid status rejected (CHECK constraint)
# ---------------------------------------------------------------------------
def test_invalid_status_rejected(conn, sample_build_id):
    """An invalid status must raise a CheckViolation."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category, status)
                VALUES (%s, %s, %s, %s)
                """,
                (sample_build_id, "lahiri", "planets", "pending"),
            )
        conn.rollback()
        pytest.fail("Expected CheckViolation for invalid status, but no error was raised")
    except psycopg2.errors.CheckViolation:
        conn.rollback()


# ---------------------------------------------------------------------------
# T08 — ayanamsha_id is NOT NULL
# ---------------------------------------------------------------------------
def test_ayanamsha_id_not_null(conn, sample_build_id):
    """Inserting NULL ayanamsha_id must raise NotNullViolation."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category)
                VALUES (%s, NULL, %s)
                """,
                (sample_build_id, "planets"),
            )
        conn.rollback()
        pytest.fail("Expected NotNullViolation for NULL ayanamsha_id")
    except psycopg2.errors.NotNullViolation:
        conn.rollback()


# ---------------------------------------------------------------------------
# T09 — category is NOT NULL
# ---------------------------------------------------------------------------
def test_category_not_null(conn, sample_build_id):
    """Inserting NULL category must raise NotNullViolation."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category)
                VALUES (%s, %s, NULL)
                """,
                (sample_build_id, "lahiri"),
            )
        conn.rollback()
        pytest.fail("Expected NotNullViolation for NULL category")
    except psycopg2.errors.NotNullViolation:
        conn.rollback()


# ---------------------------------------------------------------------------
# T10 — indexes exist (pg_indexes)
# ---------------------------------------------------------------------------
def test_indexes_exist(conn):
    """All three expected indexes must be present on build_steps."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'build_steps'
            """
        )
        indexes = {row[0] for row in cur.fetchall()}
    assert "build_steps_build_idx" in indexes, "build_steps_build_idx missing"
    assert "build_steps_status_idx" in indexes, "build_steps_status_idx missing"
    assert "build_steps_category_idx" in indexes, "build_steps_category_idx missing"


# ---------------------------------------------------------------------------
# T11 — partial status index covers only queued/running
# ---------------------------------------------------------------------------
def test_partial_status_index_predicate(conn):
    """build_steps_status_idx must be a partial index with the expected WHERE predicate."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'build_steps'
              AND indexname = 'build_steps_status_idx'
            """
        )
        row = cur.fetchone()
    assert row is not None, "build_steps_status_idx not found"
    indexdef = row[0].lower()
    assert "where" in indexdef, "build_steps_status_idx is not a partial index"
    assert "queued" in indexdef, "'queued' not in partial index predicate"
    assert "running" in indexdef, "'running' not in partial index predicate"


# ---------------------------------------------------------------------------
# T12 — FK CASCADE: deleting a build removes its steps
# ---------------------------------------------------------------------------
def test_fk_cascade_delete(conn):
    """Deleting a build must cascade-delete its build_steps."""
    with conn.cursor() as cur:
        # need a real chart_id
        cur.execute("SELECT chart_id FROM charts LIMIT 1")
        chart_row = cur.fetchone()
    if chart_row is None:
        pytest.skip("No rows in charts table")
    chart_id = chart_row[0]

    try:
        with conn.cursor() as cur:
            # Insert a throwaway build
            cur.execute(
                """
                INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
                VALUES (%s, %s, %s, %s)
                RETURNING build_id
                """,
                (chart_id, "cascade_test_uid", "super_admin", "queued"),
            )
            temp_build_id = cur.fetchone()[0]

            # Insert a step under it
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category)
                VALUES (%s, %s, %s)
                RETURNING step_id
                """,
                (temp_build_id, "kp", "houses"),
            )
            step_id = cur.fetchone()[0]

            # Delete the build
            cur.execute("DELETE FROM builds WHERE build_id = %s", (temp_build_id,))

            # Confirm the step is gone
            cur.execute(
                "SELECT COUNT(*) FROM build_steps WHERE step_id = %s", (step_id,)
            )
            count = cur.fetchone()[0]

        assert count == 0, "build_steps row not deleted by CASCADE"
    finally:
        conn.rollback()
