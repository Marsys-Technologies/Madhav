"""The CI job proves that it can execute SQL against its own disposable DB."""
import os

import psycopg
import pytest

from tests.l3._disposable_db_guard import RefusedError
from .conftest import _assert_kala_disposable_connection


def test_disposable_database_is_live(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        assert conn.execute("SELECT 2 + 3").fetchone() == (5,)


def test_connected_database_identity_mismatch_is_refused(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        with pytest.raises(RefusedError):
            _assert_kala_disposable_connection(conn, "wrong_database", kala_db_dsn)


def test_a53_admin_guard_accepts_the_same_verified_disposable_cluster(kala_db_dsn):
    from tests.l3.gochara._disposable_db_guard import guarded_admin_connect

    # Reuse the endpoint already verified by the fixture, never an ambient DSN.
    with guarded_admin_connect(os.environ["KALA_ADMIN_DSN"], connect_timeout=3) as conn:
        assert conn.execute("SELECT current_database()").fetchone() == ("postgres",)
