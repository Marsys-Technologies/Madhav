"""The disposable-database guard every A5.3 fixture uses (steward M…154825). Every hostile DSN form is refused WITHOUT a connection."""
from __future__ import annotations

import pytest

from ._disposable_db_guard import UnsafeAdminDSN, assert_loopback_server, check_admin_dsn

CLEAN = {}


@pytest.mark.parametrize("dsn", [
    "postgresql://wp6:local@localhost:55434/postgres",
    "postgresql://u:p@127.0.0.1:5432/postgres",
    "postgresql://u:p@[::1]:5432/postgres",
    "postgresql://u@127.0.0.2/postgres",
    "postgresql://u@/postgres?host=/var/run/postgresql",
    "host=localhost port=55434 user=u dbname=postgres",
    "host=/tmp user=u dbname=postgres",
    "host=db.prod.example.com hostaddr=127.0.0.1 user=u dbname=postgres",     # hostaddr is what libpq dials; the name is a label
])
def test_the_clean_loopback_forms_pass(dsn):
    # (hostaddr loopback + a non-loopback host LABEL is refused below: both are checked, since either can be used)
    if "db.prod.example.com" in dsn:
        with pytest.raises(UnsafeAdminDSN):
            check_admin_dsn(dsn, CLEAN)
    else:
        assert check_admin_dsn(dsn, CLEAN)


@pytest.mark.parametrize("dsn,why", [
    ("postgresql://u:p@localhost:5432,db.prod.example.com:5432/x", "comma in the netloc (first-host-only urlparse passes this)"),
    ("postgresql://u:p@localhost,db.prod.example.com/x", "comma, no ports"),
    ("postgresql://u:p@localhost:5432,127.0.0.1:5432/x", "comma even between two loopbacks: failover is still failover"),
    ("postgresql://u@/x?host=localhost,db.prod.example.com", "comma in a query-string host"),
    ("postgresql://u@localhost/x?hostaddr=127.0.0.1,10.0.0.5", "comma in hostaddr"),
    ("host=localhost,db.prod.example.com user=u dbname=x", "keyword form multi-host"),
    ("postgresql://u:p@db.prod.example.com:5432/x", "remote host"),
    ("postgresql://u:p@localhost.evil.example.com/x", "a hostname that merely starts with localhost"),
    ("postgresql://localhost@db.prod.example.com/x", "localhost as the USER, remote as the host"),
    ("postgresql://u@localhost/x?host=db.prod.example.com", "a query host overriding the authority"),
    ("postgresql://u@localhost/x?hostaddr=10.0.0.5", "a non-loopback hostaddr"),
    ("host=db.prod.example.com user=u dbname=x", "keyword form remote"),
    ("service=prod user=u dbname=x", "service="),
    ("host=localhost service=prod dbname=x", "service= beside a loopback host"),
    ("postgresql://u@localhost/x?servicefile=/tmp/pg_service.conf", "servicefile="),
    ("postgresql:///x", "no explicit host at all (the environment would decide)"),
    ("user=u dbname=x", "keyword form, no host"),
    ("postgresql://u@[::2]/x", "an IPv6 address that is not loopback"),
    ("postgresql://u@192.168.0.10/x", "a private-network address"),
    ("", "empty"),
])
def test_every_hostile_dsn_form_is_refused_without_connecting(dsn, why):
    with pytest.raises(UnsafeAdminDSN):
        check_admin_dsn(dsn, CLEAN)


@pytest.mark.parametrize("var", ["PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_the_environment_overrides_are_refused_even_with_a_clean_dsn(var):
    with pytest.raises(UnsafeAdminDSN, match=var):
        check_admin_dsn("postgresql://u:p@localhost:55434/postgres", {var: "anything"})


def test_the_process_environment_is_what_the_default_checks(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.prod.example.com")
    with pytest.raises(UnsafeAdminDSN, match="PGHOST"):
        check_admin_dsn("postgresql://u:p@localhost:55434/postgres")


class _Conn:
    def __init__(self, addr):
        self.addr = addr

    def execute(self, sql):
        class _R:
            def fetchone(s):
                return (self.addr,)
        return _R()


def test_the_connected_servers_address_must_be_loopback_or_a_unix_socket():
    assert assert_loopback_server(_Conn(None)) == "unix-socket"
    assert assert_loopback_server(_Conn("127.0.0.1")) == "127.0.0.1"
    assert assert_loopback_server(_Conn("::1")) == "::1"
    for remote in ("10.1.2.3", "203.0.113.9", "2001:db8::1"):
        with pytest.raises(UnsafeAdminDSN, match="not loopback"):
            assert_loopback_server(_Conn(remote))


def test_every_a53_fixture_that_creates_or_drops_goes_through_the_guard():
    """No admin fixture of the A5.3 suites connects with a bare `psycopg.connect(ADMIN_DSN…)` any more."""
    import re
    from pathlib import Path
    here = Path(__file__).parent
    offenders = []
    for p in sorted(here.glob("test_*.py")):
        if p.name == Path(__file__).name:
            continue
        text = p.read_text()
        if re.search(r"psycopg\.connect\(\s*(ADMIN_DSN|MAINT_DSN)\b", text):
            offenders.append(p.name)
    assert not offenders, offenders
