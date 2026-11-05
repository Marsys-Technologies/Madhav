"""Real-PostgreSQL support for the L0 data-wave tests (TI-l0data-* PRs).

Env-gated, like FORMULA_CONSTANTS_TEST_DATABASE_URL in test_l0_formula_constants.py:
L0D_TEST_CONNINFO must be a libpq conninfo string for a DISPOSABLE local database whose
name ends in `_test`. Without it the real-PG tests skip (CI has no such database); with
it they run for real. The helper never touches anything but a throwaway database it creates
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
    """Yield a dict_row connection to a FRESH throwaway database (`l0d_<hex>_test`, created
    from the admin conninfo and dropped on exit) in whose `public` schema `ddl` has been run.
    A whole database, not a schema, because several L0 writers probe
    `information_schema ... table_schema='public'` and would test a different path otherwise.
    The connection is NOT autocommit: tests that want to model "caller owns the transaction"
    get exactly that. The name guard (`_test` suffix) is checked on the admin conninfo AND on
    the database actually created."""
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    from psycopg.rows import dict_row

    info = os.environ[ENV]
    admin_name = conninfo_to_dict(info).get("dbname", "")
    assert admin_name.endswith("_test"), f"refusing to run: database name {admin_name!r} must end with _test"
    name = "l0d_" + uuid.uuid4().hex[:12] + "_test"
    assert name.endswith("_test")
    admin = psycopg.connect(info, autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
        conn = psycopg.connect(make_conninfo(info, dbname=name), row_factory=dict_row)
        try:
            conn.execute(ddl)
            conn.commit()
            yield conn
        finally:
            conn.close()
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()
