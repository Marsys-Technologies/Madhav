"""Conftest for tests/l2/ — provides db_conn fixture, skips when DATABASE_URL absent."""
import os
import pytest

try:
    import psycopg
    import psycopg.rows
    _PSYCOPG_AVAILABLE = True
except ImportError:
    _PSYCOPG_AVAILABLE = False


@pytest.fixture(scope="module")
def db_conn():
    """Real DB connection for l2 integration tests. Skips when DATABASE_URL is not set."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping live-DB test")
    if not _PSYCOPG_AVAILABLE:
        pytest.skip("psycopg not installed")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()
