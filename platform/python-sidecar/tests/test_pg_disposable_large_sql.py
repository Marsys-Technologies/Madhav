"""tests/pg_disposable.psql must accept a generated statement larger than one Linux argv string (128 KiB, MAX_ARG_STRLEN).

CI (Linux) failed test_argala_migration_1221_sql.py with `OSError: [Errno 7] Argument list too long: '.../psql'` because the
helper passed the whole SQL as `psql -c <sql>`. Above 100 000 bytes the helper now feeds the SQL as a file in one transaction.
"""
from __future__ import annotations

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, pg, psql, q, requires_pg  # noqa: F401


@requires_pg
def test_a_statement_over_the_linux_argv_string_cap_runs_and_returns_its_result(pg):
    db = new_db(pg)
    big = "SELECT length('" + ("x" * 300_000) + "');"
    assert len(big.encode()) > 131_072
    assert q(pg, db, big) == "300000"


@requires_pg
def test_the_large_statement_path_is_one_transaction_that_rolls_back_whole_on_error(pg):
    db = new_db(pg)
    q(pg, db, "CREATE TABLE t_big (v text);")
    pad = "x" * 150_000
    sql = f"INSERT INTO t_big VALUES ('{pad}'); SELECT 1/0;"
    r = psql(pg, db, sql)
    assert r.returncode != 0
    assert q(pg, db, "SELECT count(*) FROM t_big;") == "0"
