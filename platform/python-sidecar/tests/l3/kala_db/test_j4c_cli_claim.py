"""Execute the production CLI prepare lease SQL against guarded Postgres.

The TypeScript suite covers resolution and transaction ordering. This oracle
executes the actual statement so a broken WHERE cannot pass behind a fake pool.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import threading

import psycopg
import pytest

REPOSITORY = Path(__file__).resolve().parents[5] / "platform/src/lib/ai-console/repository.ts"


def _claim(conn):
    source = REPOSITORY.read_text()
    statement = re.search(r"const claimed = await query\(`(.*?)`, \[cliId, PREPARE_CLI_REVALIDATION_INTERVAL_MINUTES\]\)",
                          source, re.S)
    assert statement, "production claim statement could not be located"
    sql = statement.group(1).replace("$1", "%s").replace("$2", "%s")
    return conn.execute(sql, ("claude_code", 15)).fetchall()


@pytest.fixture()
def lease_db(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS ai_cli_installations")
        conn.execute("CREATE TABLE ai_cli_installations(cli_id TEXT PRIMARY KEY, validation_state TEXT, last_checked_at TIMESTAMPTZ)")
        conn.execute("INSERT INTO ai_cli_installations VALUES ('claude_code','unreachable',NULL)")
    return isolated_kala_db_dsn


def test_simultaneous_prepares_claim_one_interval_across_connections(lease_db):
    barrier = threading.Barrier(2)

    def attempt():
        with psycopg.connect(lease_db, autocommit=True) as conn:
            barrier.wait(timeout=10)
            return len(_claim(conn))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        assert sorted(f.result(timeout=15) for f in futures) == [0, 1]
    with psycopg.connect(lease_db, autocommit=True) as conn:
        assert _claim(conn) == []  # a thrown probe still consumed the interval
        conn.execute("UPDATE ai_cli_installations SET last_checked_at=clock_timestamp()-interval '16 minutes'")
        assert len(_claim(conn)) == 1


@pytest.mark.parametrize("state", ["reachable", "not_installed", "auth_unavailable", "validating"])
def test_terminal_or_inflight_installation_is_not_claimed(lease_db, state):
    with psycopg.connect(lease_db, autocommit=True) as conn:
        conn.execute("UPDATE ai_cli_installations SET validation_state=%s", (state,))
        assert _claim(conn) == []
