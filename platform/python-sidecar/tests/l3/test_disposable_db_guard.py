"""C24 — one test per DSN form for the ONE shared disposable-database guard
(tests/l3/_disposable_db_guard.py, steward M20261002T154223-e3e1): the
legitimate loopback forms are ACCEPTED and every dangerous form is REFUSED —
URI multi-host (libpq failover past the first host, the Suvarṇa finding),
keyword/value DSNs, host=/hostaddr= in the query string, pg_service, libpq
environment overrides (PGHOST / PGHOSTADDR / PGSERVICE / PGSERVICEFILE), and a
wrong dbname. All string-level tests are pure (no connection). The
post-connect check runs only when the C7 CI Postgres DSN is present.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _disposable_db_guard import (  # noqa: E402
    RefusedError,
    assert_disposable_connection,
    validate_disposable_dsn,
)

DB = "c7_builder_role_test"
C7_DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")
EMPTY_ENV: dict = {}


def _accept(dsn, name=DB, env=EMPTY_ENV):
    return validate_disposable_dsn(dsn, name, env=env)


def _refuse(dsn, name=DB, env=EMPTY_ENV):
    with pytest.raises(RefusedError):
        validate_disposable_dsn(dsn, name, env=env)


# ── acceptance: the legitimate forms ─────────────────────────────────────────

def test_uri_single_loopback_host_accepted():
    info = _accept(f"postgresql://u:p@localhost:5432/{DB}")
    assert info["dbname"] == DB and info["host"] == "localhost"


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "[::1]", "localhost"])
def test_every_loopback_spelling_accepted(host):
    _accept(f"postgresql://u:p@{host}:5432/{DB}")


def test_keyword_value_dsn_accepted():
    _accept(f"host=localhost port=5432 dbname={DB} user=u")


def test_query_string_loopback_hostaddr_accepted():
    _accept(f"postgresql://u:p@localhost/{DB}?hostaddr=127.0.0.1")


def test_expected_dbname_none_is_host_discipline_only():
    # the wp10 fixture's form: any dbname, loopback everywhere
    _accept("postgresql://postgres:postgres@localhost:5432/postgres", name=None)


# ── refusal: every dangerous form ────────────────────────────────────────────

def test_uri_multi_host_refused():
    """The Suvarṇa finding: urlparse().hostname sees only the FIRST host; libpq
    can fail over to the second. Refused on the comma in the netloc."""
    _refuse(f"postgresql://u:p@localhost:5432,db.prod.example.com:5432/{DB}")


def test_keyword_value_multi_host_refused():
    _refuse(f"host=localhost,db.prod.example.com dbname={DB}")


def test_query_string_host_override_refused():
    _refuse(f"postgresql://u:p@localhost:5432/{DB}?host=db.prod.example.com")


def test_query_string_non_loopback_hostaddr_refused():
    _refuse(f"postgresql://u:p@localhost/{DB}?hostaddr=10.0.0.5")


def test_remote_single_host_refused():
    _refuse(f"postgresql://u:p@db.prod.example.com:5432/{DB}")


def test_pg_service_in_dsn_refused():
    _refuse(f"service=myservice dbname={DB}")


@pytest.mark.parametrize("var", ["PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_libpq_environment_override_refused(var):
    _refuse(f"postgresql://u:p@localhost:5432/{DB}", env={var: "anything"})


def test_empty_environment_override_treated_as_unset():
    _accept(f"postgresql://u:p@localhost:5432/{DB}", env={"PGHOST": "  "})


def test_wrong_dbname_refused():
    _refuse("postgresql://u:p@localhost:5432/production")


def test_unparseable_dsn_refused():
    _refuse("not a dsn at all :::")


# ── post-connect proof (needs the CI Postgres / a local disposable) ──────────

@pytest.mark.skipif(not C7_DSN, reason="C7_BUILDER_ROLE_TEST_DATABASE_URL not set")
def test_post_connect_check_on_the_real_disposable():
    psycopg = pytest.importorskip("psycopg")
    validate_disposable_dsn(C7_DSN, DB)
    with psycopg.connect(C7_DSN) as conn:
        assert_disposable_connection(conn, DB)  # must not raise
        with pytest.raises(RefusedError):
            assert_disposable_connection(conn, "some_other_database")
