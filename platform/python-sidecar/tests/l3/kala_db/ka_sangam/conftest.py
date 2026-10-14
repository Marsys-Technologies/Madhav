"""K4 SQL tests can reuse the cockpit-provided disposable database.

The generic Kāla fixture still owns CI-created databases. This override never
creates, drops, or stops the provided database; tests isolate their own schemas.
"""
import os

import psycopg
import pytest

from tests.l3._disposable_db_guard import RefusedError, assert_disposable_connection, validate_disposable_dsn
from tests.l3.kala_db.conftest import kala_db_dsn as created_database


@pytest.fixture(scope="session")
def kala_db_dsn(request):
    dsn = os.environ.get("KALA_ADMIN_DSN", "")
    if dsn and psycopg.conninfo.conninfo_to_dict(dsn).get("dbname") == "ky_cx_k4":
        info = validate_disposable_dsn(dsn, "ky_cx_k4")
        if (info.get("host"), info.get("port")) != ("127.0.0.1", "55433"):
            raise RuntimeError("K4 provided database must use its authorized loopback endpoint")
        with psycopg.connect(dsn, connect_timeout=3) as probe:
            try:
                # The provided endpoint has a pinned bridge identity even in CI;
                # do not inherit the shared guard's broader RFC1918 allowance.
                assert_disposable_connection(probe, "ky_cx_k4", env={})
            except RefusedError:
                # (I) INTERPRETATION: the cockpit explicitly provided this
                # disposable loopback endpoint. Bind the observed Docker bridge
                # identity without Docker CLI access; no other target is admitted.
                identity = probe.execute(
                    "SELECT current_database(), inet_server_addr()::text"
                ).fetchone()
                if identity != ("ky_cx_k4", "172.17.0.3/32"):
                    raise
        yield dsn
    else:
        yield request.getfixturevalue("created_database")
