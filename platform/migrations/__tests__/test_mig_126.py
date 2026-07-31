"""
Migration 126 verification tests: engine_versions + build_engine_versions tables
MARSYS-JIS Multi-Ayanamsha Build Orchestrator [BUILD-ORCH-B-03]
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

EXPECTED_EV_COLUMNS = {
    "version_id",
    "engine_name",
    "version_str",
    "git_sha",
    "swisseph_ver",
    "created_at",
}

EXPECTED_BEV_COLUMNS = {
    "build_id",
    "version_id",
}

# A real chart_id that exists in the DB (needed for builds FK)
FIXTURE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"


def _insert_build(cur):
    """Insert a minimal builds row and return its build_id."""
    cur.execute(
        """
        INSERT INTO builds (chart_id, triggered_by_uid, triggered_by_role, status)
        VALUES (%s, 'test-uid', 'super_admin', 'queued')
        RETURNING build_id
        """,
        (FIXTURE_CHART_ID,),
    )
    return cur.fetchone()[0]


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


# ── 1. engine_versions table exists ──────────────────────────────────────────
def test_engine_versions_table_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass('public.engine_versions')::text"
        )
        assert cur.fetchone()[0] == "engine_versions"


# ── 2. build_engine_versions table exists ────────────────────────────────────
def test_build_engine_versions_table_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass('public.build_engine_versions')::text"
        )
        assert cur.fetchone()[0] == "build_engine_versions"


# ── 3. engine_versions has expected columns ───────────────────────────────────
def test_engine_versions_columns(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'engine_versions'
            """
        )
        cols = {row[0] for row in cur.fetchall()}
    assert EXPECTED_EV_COLUMNS <= cols


# ── 4. build_engine_versions has expected columns ────────────────────────────
def test_build_engine_versions_columns(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'build_engine_versions'
            """
        )
        cols = {row[0] for row in cur.fetchall()}
    assert EXPECTED_BEV_COLUMNS <= cols


# ── 5. UNIQUE constraint on (engine_name, version_str) ───────────────────────
def test_engine_versions_unique_constraint(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str)
            VALUES ('swisseph', '2.10.03-test-unique')
            """
        )
        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute(
                """
                INSERT INTO engine_versions (engine_name, version_str)
                VALUES ('swisseph', '2.10.03-test-unique')
                """
            )


# ── 6. git_sha is nullable ────────────────────────────────────────────────────
def test_engine_versions_git_sha_nullable(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str, git_sha)
            VALUES ('pyjhora', '1.0.0-test-nullable', NULL)
            RETURNING git_sha
            """
        )
        result = cur.fetchone()
    assert result[0] is None


# ── 7. swisseph_ver is nullable ───────────────────────────────────────────────
def test_engine_versions_swisseph_ver_nullable(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str, swisseph_ver)
            VALUES ('pyjhora', '1.0.1-test-swver-null', NULL)
            RETURNING swisseph_ver
            """
        )
        result = cur.fetchone()
    assert result[0] is None


# ── 8. Insert + query round-trip for engine_versions ─────────────────────────
def test_engine_versions_insert_roundtrip(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str, git_sha, swisseph_ver)
            VALUES ('swisseph', '2.10.03-rt', 'abc1234def5678', '2.10.03')
            RETURNING *
            """
        )
        row = cur.fetchone()
    assert row["engine_name"] == "swisseph"
    assert row["version_str"] == "2.10.03-rt"
    assert row["git_sha"] == "abc1234def5678"
    assert row["swisseph_ver"] == "2.10.03"
    assert row["version_id"] is not None
    assert row["created_at"] is not None


# ── 9. build_engine_versions composite PK prevents duplicate rows ─────────────
def test_build_engine_versions_composite_pk(conn):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)

        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str)
            VALUES ('swisseph', '2.10.03-pk-test')
            RETURNING version_id
            """
        )
        version_id = cur.fetchone()[0]

        # First link succeeds
        cur.execute(
            """
            INSERT INTO build_engine_versions (build_id, version_id)
            VALUES (%s, %s)
            """,
            (build_id, version_id),
        )

        # Duplicate raises UniqueViolation (PK conflict)
        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute(
                """
                INSERT INTO build_engine_versions (build_id, version_id)
                VALUES (%s, %s)
                """,
                (build_id, version_id),
            )


# ── 10. FK cascade: deleting a build cascades to build_engine_versions ────────
def test_build_engine_versions_fk_cascade_on_build_delete(conn):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)

        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str)
            VALUES ('swisseph', '2.10.03-cascade-test')
            RETURNING version_id
            """
        )
        version_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO build_engine_versions (build_id, version_id)
            VALUES (%s, %s)
            """,
            (build_id, version_id),
        )

        # Delete the build — should cascade
        cur.execute("DELETE FROM builds WHERE build_id = %s", (build_id,))

        # The bev row must be gone
        cur.execute(
            "SELECT COUNT(*) FROM build_engine_versions WHERE build_id = %s",
            (build_id,),
        )
        assert cur.fetchone()[0] == 0


# ── 11. Index bev_version_idx exists ─────────────────────────────────────────
def test_bev_version_idx_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename  = 'build_engine_versions'
              AND indexname  = 'bev_version_idx'
            """
        )
        assert cur.fetchone() is not None, "Index bev_version_idx not found"


# ── 12. FK to engine_versions enforced (bogus version_id raises) ─────────────
def test_build_engine_versions_fk_to_engine_versions(conn):
    with conn.cursor() as cur:
        build_id = _insert_build(cur)

        bogus_version_id = str(uuid.uuid4())
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            cur.execute(
                """
                INSERT INTO build_engine_versions (build_id, version_id)
                VALUES (%s, %s)
                """,
                (build_id, bogus_version_id),
            )


# ── 13. created_at defaults to NOW() ─────────────────────────────────────────
def test_engine_versions_created_at_default(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO engine_versions (engine_name, version_str)
            VALUES ('pyjhora', '1.2.3-ts-default')
            RETURNING created_at
            """
        )
        created_at = cur.fetchone()[0]
    assert created_at is not None
