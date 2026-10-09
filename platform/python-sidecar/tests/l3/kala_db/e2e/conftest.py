"""Real lane DB locally; isolated throwaway Postgres in CI. No persistent rows."""
import os
from pathlib import Path

import psycopg
import pytest

from tests.l3.kala_db.conftest import _assert_kala_disposable_connection
from tests.l3.kala_db.idempotency.conftest import _disposable_test_dsn

REPO = Path(__file__).resolve().parents[6]


@pytest.fixture
def conn():
    if os.environ.get("KALA_REQUIRE_DB") != "1":
        pytest.skip("K0a slice requires the dedicated disposable PostgreSQL job")
    dsn = _disposable_test_dsn()
    if os.environ.get("KY_LANE"):
        dsn = psycopg.conninfo.make_conninfo(dsn, dbname="ky_" + os.environ["KY_LANE"])
    with psycopg.connect(dsn) as connection:
        name = connection.execute("SELECT current_database()").fetchone()[0]
        _assert_kala_disposable_connection(connection, name, dsn)
        connection.execute(Path(__file__).with_name("legacy_schema.sql").read_text())
        manifest = (REPO / "platform/migrations/1330_kala_layer_manifest_candidates.sql").read_text()
        # Only table contracts are needed: no verifier grants/role operations.
        manifest = manifest[:manifest.index("-- A separately dispatched verifier")]
        connection.execute(manifest.replace("public.", "pg_temp.").replace("CREATE TABLE", "CREATE TEMP TABLE"))
        candidate_migration = REPO / "platform/migrations/1338_kala_assertion_vertical_slice.sql"
        if candidate_migration.exists():
            connection.execute(candidate_migration.read_text().replace("public.", "pg_temp."))
        yield connection
        connection.rollback()
