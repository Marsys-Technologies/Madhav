"""Real-PostgreSQL support for the L0 data-wave tests (TI-l0data-* PRs).

Env-gated, like FORMULA_CONSTANTS_TEST_DATABASE_URL in test_l0_formula_constants.py:
L0D_TEST_CONNINFO must be a libpq conninfo string for a DISPOSABLE local database whose
name ends in `_test`. Without it the real-PG tests skip (CI has no such database); with
it they run for real. The helper never touches anything but a throwaway schema it creates
and drops itself, so even a mistaken conninfo cannot reach a table that was not created
by the test.

Row factory is dict_row on purpose: the L0 writers read `cur.fetchone()["..."]` /
dict-shaped rows because the orchestrator's connection (pipeline.orchestrator.db.connect)
uses dict_row; a plain-tuple connection would test a different code path.
"""
from __future__ import annotations

import contextlib
import os
import uuid

import pytest

ENV = "L0D_TEST_CONNINFO"


def pg_available() -> bool:
    return bool(os.environ.get(ENV))


requires_pg = pytest.mark.skipif(not pg_available(), reason=f"{ENV} not configured (disposable PG not available)")


@contextlib.contextmanager
def scratch_schema(ddl: str):
    """Yield a dict_row connection whose search_path is a fresh throwaway schema in which
    `ddl` has been executed. The schema is dropped on exit. The connection is NOT
    autocommit: tests that want to model "caller owns the transaction" get exactly that."""
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    from psycopg.rows import dict_row

    info = os.environ[ENV]
    dbname = conninfo_to_dict(info).get("dbname", "")
    assert dbname.endswith("_test"), f"refusing to run: database name {dbname!r} must end with _test"
    schema = "l0d_" + uuid.uuid4().hex[:12]
    admin = psycopg.connect(info, autocommit=True)
    try:
        admin.execute(f'CREATE SCHEMA "{schema}"')
        conn = psycopg.connect(info, row_factory=dict_row, options=f"-c search_path={schema}")
        try:
            conn.execute(ddl)
            conn.commit()
            yield conn
        finally:
            conn.close()
    finally:
        admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        admin.close()
