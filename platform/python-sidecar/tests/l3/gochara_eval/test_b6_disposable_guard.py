"""The disposable-database guard refuses multi-host DSNs, query-string host overrides, default hosts, service files and environment overrides."""
import pytest

from ._disposable_guard import NotDisposable, assert_disposable_dsn

BAD = [
    "postgresql://u:p@localhost:5432,db.prod.example.com:5432/x",
    "postgresql://u:p@db.prod.example.com:5432,localhost:5432/x",
    "postgresql://u@localhost:5432/x?host=db.prod.example.com",
    "postgresql://u@localhost:5432/x?hostaddr=10.0.0.5",
    "postgresql://u@localhost:5432/x?hostaddr=127.0.0.1,10.0.0.5",
    "postgresql://u@/x",
    "postgresql:///x?host=db.prod.example.com",
    "host=localhost,db.prod.example.com port=5432,5432 dbname=x",
    "host=localhost dbname=x service=prod",
    "host=db.prod.example.com dbname=x",
    "",
]
GOOD = ["postgresql://u@127.0.0.1:54361/postgres", "postgresql://u@localhost:5432/x", "host=127.0.0.1 port=5432 dbname=x", "postgresql://u@[::1]:5432/x"]


@pytest.mark.parametrize("dsn", BAD)
def test_refuses(dsn, monkeypatch):
    for k in ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(NotDisposable):
        assert_disposable_dsn(dsn)


@pytest.mark.parametrize("dsn", GOOD)
def test_accepts_an_explicit_loopback_single_host(dsn, monkeypatch):
    for k in ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        monkeypatch.delenv(k, raising=False)
    assert assert_disposable_dsn(dsn)["host"] in ("127.0.0.1", "localhost", "::1")


@pytest.mark.parametrize("var", ["PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_refuses_an_environment_override(var, monkeypatch):
    monkeypatch.setenv(var, "db.prod.example.com")
    with pytest.raises(NotDisposable, match=var):
        assert_disposable_dsn("postgresql://u@127.0.0.1:5432/x")


def test_requires_the_exact_database_name_when_asked(monkeypatch):
    for k in ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        monkeypatch.delenv(k, raising=False)
    assert_disposable_dsn("postgresql://u@127.0.0.1:5432/postgres", dbname="postgres")
    with pytest.raises(NotDisposable, match="expected"):
        assert_disposable_dsn("postgresql://u@127.0.0.1:5432/other", dbname="postgres")
