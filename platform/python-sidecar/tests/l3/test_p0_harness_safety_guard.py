"""Track I-8 (SS ruling): the destructive P0 DB tests must REFUSE a non-disposable database.

`test_bhavishya_p0_empty_generation_db._reset` and `test_ka_kshetra_p0_planning_readonly` DELETE the
canonical chart's rows from `kala_*` / `phala_anchors`. Before this guard their only protection was the
default DSN; pointing `KALA_P0_HARNESS_DSN` at production would have deleted real rows. The guard (in
`_p0_harness.py`) follows the B2 test's `isSafeTestDbUrl` pattern: parse the target, require a LOCAL host
and a disposable database name, refuse (raise, never skip) otherwise; and a runtime twin checks the
server's own `current_database()` before any DELETE.

DB-free: no connection is made. The fake connection records every statement so the tests can prove that
a refusal happens BEFORE any DELETE is issued.
"""
from __future__ import annotations

import pytest

from tests.l3 import _p0_harness as h

SAFE = [
    "postgresql://kxuser@/kala_harness?host=/tmp/kp0&port=59510",            # the shipped default
    "postgresql://postgres@127.0.0.1:55432/kala_harness",
    "postgresql://postgres:pw@localhost:5432/kala_p0_harness",
    "postgresql://postgres@[::1]:5432/downstream_dependents_test",
    "postgresql://u@127.0.0.1/madhav_test",
    "postgresql://u@/kala_scratch?host=/var/run/postgresql",
    "host=/tmp/kp0 port=59510 dbname=kala_harness user=kxuser",
    "host=localhost dbname=bhavishya_disposable",
]
UNSAFE = [
    "postgresql://u@127.0.0.1:5432/madhav_prod",
    "postgresql://u@127.0.0.1:5432/amjis",
    "postgresql://u@127.0.0.1:5432/madhav",
    "postgresql://u@127.0.0.1:5432/postgres",
    "postgresql://u@127.0.0.1:5432/madhav_prod_test",                       # prod token even with _test
    "postgresql://u@127.0.0.1:5432/amjis_test",
    "postgresql://u@prod-db.example.com:5432/kala_harness",                  # right name, remote host
    "postgresql://u@10.0.0.5:5432/kala_harness",
    "postgresql://u@localhost.evil.example.com:5432/kala_harness",           # contains a loopback name
    "postgresql://u@127.0.0.1:5432/postgres?application_name=kala_harness",  # name only in the query
    "postgresql://u@127.0.0.1:5432/postgres?dbname=madhav_prod",
    "postgresql://u@/kala_harness?host=prod-db.example.com",                 # remote host via query
    "postgresql://u@127.0.0.1:5432/kala_harness?hostaddr=10.1.2.3",
    "postgresql://u@127.0.0.1:5432/kala_harness_prod",
    "postgresql://u@127.0.0.1:5432/kala_harness_backup",                      # near-miss names stay refused
    "postgresql://u@127.0.0.1:5432/orders_test_old",
    "postgresql://u@127.0.0.1:5432/x/kala_harness",
    "postgresql://u@127.0.0.1:5432/kala_harness/",
    "host=db.internal dbname=kala_harness",
    "host=127.0.0.1 dbname=madhav_prod",
    "service=prod_alias",                                                    # service files can redirect to a remote host
    "service=prod dbname=kala_harness host=/tmp/kp0",                        # even alongside safe-looking fields
    "postgresql://u@127.0.0.1:5432/kala_harness?service=prod",
    "postgresql:///kala_harness?service=prod&host=/tmp/kp0",
    "not a dsn kala_harness",
    "postgresql://u@[::1/kala_harness",                                      # unparseable
    "",
]


@pytest.mark.parametrize("dsn", SAFE)
def test_accepts_disposable_local_databases(dsn):
    assert h.is_safe_harness_dsn(dsn) is True
    h.assert_safe_harness_dsn(dsn)  # does not raise


@pytest.mark.parametrize("dsn", UNSAFE)
def test_refuses_production_looking_or_remote_targets(dsn):
    assert h.is_safe_harness_dsn(dsn) is False
    with pytest.raises(h.HarnessSafetyError):
        h.assert_safe_harness_dsn(dsn)


def test_the_shipped_default_dsn_is_itself_safe():
    assert h.is_safe_harness_dsn("postgresql://kxuser@/kala_harness?host=/tmp/kp0&port=59510")


def test_connect_refuses_before_any_connection_is_attempted(monkeypatch):
    for bad in ("postgresql://u@127.0.0.1:5432/madhav_prod", "postgresql://u@db.example.com/amjis"):
        monkeypatch.setattr(h, "HARNESS_DSN", bad)
        # a raise, NOT a pytest skip: a skipped destructive suite would hide the misconfiguration
        try:
            h.connect()
        except h.HarnessSafetyError:
            continue
        except BaseException as exc:  # incl. pytest's Skipped
            pytest.fail(f"connect() must raise HarnessSafetyError for {bad!r}, got {type(exc).__name__}")
        pytest.fail(f"connect() accepted {bad!r}")


class _FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append(sql)

    def fetchone(self):
        return {"d": self.conn.dbname}


class _FakeConn:
    def __init__(self, dbname):
        self.dbname = dbname
        self.executed: list[str] = []
        self.commits = 0

    def cursor(self, *a, **k):
        return _FakeCursor(self)

    def commit(self):
        self.commits += 1


@pytest.mark.parametrize("name", ["madhav_prod", "amjis", "madhav", "postgres", "amjis_test", "kala_harness_prod"])
def test_runtime_guard_refuses_a_production_database_name(name):
    with pytest.raises(h.HarnessSafetyError):
        h.assert_disposable_connection(_FakeConn(name))


@pytest.mark.parametrize("name", ["kala_harness", "kala_p0_harness", "madhav_test", "x_scratch", "y_disposable"])
def test_runtime_guard_accepts_disposable_names(name):
    h.assert_disposable_connection(_FakeConn(name))


def test_bhavishya_reset_refuses_prod_before_issuing_any_delete():
    from tests.l3 import test_bhavishya_p0_empty_generation_db as t

    prod = _FakeConn("madhav_prod")
    with pytest.raises(h.HarnessSafetyError):
        t._reset(prod)
    assert not any("DELETE" in s.upper() for s in prod.executed)
    assert prod.commits == 0

    ok = _FakeConn("kala_harness")
    t._reset(ok)
    assert sum("DELETE FROM" in s for s in ok.executed) == 4 and ok.commits == 1


def test_kshetra_fixture_source_calls_the_guard():
    import inspect
    from tests.l3 import test_ka_kshetra_p0_planning_readonly as t

    assert "assert_disposable_connection(c)" in inspect.getsource(t)
