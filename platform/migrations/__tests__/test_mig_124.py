"""
Migration 124 verification tests: builds table
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
    "build_id",
    "chart_id",
    "triggered_by_uid",
    "triggered_by_role",
    "engine_version",
    "ayanamshas",
    "salience_formula_ver",
    "status",
    "queued_at",
    "started_at",
    "finished_at",
    "cancelled_at",
    "failed_at",
    "error_summary",
    "log_gcs_uri",
    "asset_artifacts_uri",
    "cloud_run_job_exec",
}

VALID_STATUSES = ["queued", "running", "complete", "failed", "cancelled", "cancelling"]


@pytest.fixture(scope="module")
def conn():
    connection = psycopg2.connect(**DB_PARAMS)
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture(scope="module")
def sample_chart_id(conn):
    """Fetch a real chart_id from the charts table to satisfy the FK."""
    with conn.cursor() as cur:
        cur.execute("SELECT chart_id FROM charts LIMIT 1")
        row = cur.fetchone()
    if row is None:
        pytest.skip("No rows in charts table — FK prerequisite not met")
    return row[0]


def test_builds_table_exists(conn):
    """builds table must exist in public schema."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'builds'
            """
        )
        count = cur.fetchone()[0]
    assert count == 1, "builds table not found in public schema"


def test_builds_staging_table_exists(conn):
    """builds_staging mirror table must exist."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'builds_staging'
            """
        )
        count = cur.fetchone()[0]
    assert count == 1, "builds_staging table not found in public schema"


def test_builds_columns(conn):
    """All expected columns must be present on the builds table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'builds'
            """
        )
        actual = {row[0] for row in cur.fetchall()}
    missing = EXPECTED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"


def test_builds_primary_key(conn):
    """build_id must be the primary key."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kc.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kc
              ON tc.constraint_name = kc.constraint_name
             AND tc.table_schema = kc.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name = 'builds'
              AND tc.constraint_type = 'PRIMARY KEY'
            """
        )
        pk_cols = [row[0] for row in cur.fetchall()]
    assert pk_cols == ["build_id"], f"Unexpected primary key columns: {pk_cols}"


def test_valid_status_insert(conn, sample_chart_id):
    """Rows with each valid status must insert without constraint error."""
    inserted_ids = []
    try:
        with conn.cursor() as cur:
            for status in VALID_STATUSES:
                cur.execute(
                    """
                    INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING build_id
                    """,
                    (sample_chart_id, "test_uid", "super_admin", status),
                )
                inserted_ids.append(cur.fetchone()[0])
        assert len(inserted_ids) == len(VALID_STATUSES), "Not all valid statuses inserted"
    finally:
        conn.rollback()


def test_invalid_status_rejected(conn, sample_chart_id):
    """A row with an invalid status must raise an IntegrityError."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
                VALUES (%s, %s, %s, %s)
                """,
                (sample_chart_id, "test_uid", "super_admin", "invalid_status"),
            )
        conn.rollback()
        pytest.fail("Expected IntegrityError for invalid status, but no error was raised")
    except psycopg2.errors.CheckViolation:
        conn.rollback()  # clean up after constraint violation


def test_invalid_role_rejected(conn, sample_chart_id):
    """A row with an invalid triggered_by_role must raise an IntegrityError."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
                VALUES (%s, %s, %s, %s)
                """,
                (sample_chart_id, "test_uid", "admin", "queued"),
            )
        conn.rollback()
        pytest.fail("Expected IntegrityError for invalid role, but no error was raised")
    except psycopg2.errors.CheckViolation:
        conn.rollback()


def test_ayanamshas_default(conn, sample_chart_id):
    """ayanamshas column must default to the 5-element JSONB array."""
    expected = ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
                VALUES (%s, %s, %s, %s)
                RETURNING ayanamshas
                """,
                (sample_chart_id, "test_uid", "super_admin", "queued"),
            )
            ayanamshas = cur.fetchone()[0]
        assert ayanamshas == expected, f"Unexpected default ayanamshas: {ayanamshas}"
    finally:
        conn.rollback()


def test_fk_cascade_exists(conn):
    """Foreign key from builds.chart_id → charts.chart_id with CASCADE must exist."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rc.delete_rule
            FROM information_schema.referential_constraints rc
            JOIN information_schema.table_constraints tc
              ON rc.constraint_name = tc.constraint_name
             AND rc.constraint_schema = tc.constraint_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name = 'builds'
              AND tc.constraint_type = 'FOREIGN KEY'
            """
        )
        rows = cur.fetchall()
    assert rows, "No foreign key found on builds table"
    delete_rules = [r[0] for r in rows]
    assert "CASCADE" in delete_rules, f"CASCADE not found in FK delete rules: {delete_rules}"


def test_indexes_exist(conn):
    """Both expected indexes must be present on the builds table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'builds'
            """
        )
        indexes = {row[0] for row in cur.fetchall()}
    assert "builds_chart_idx" in indexes, "builds_chart_idx index missing"
    assert "builds_status_idx" in indexes, "builds_status_idx index missing"
