"""The live dump fixtures preserve socket/host parameters when choosing a database."""
import pytest
import psycopg
from psycopg.conninfo import conninfo_to_dict

from . import test_dump_extract_pg as live


@pytest.mark.parametrize("fixture", [live.conn, live.fresh])
@pytest.mark.parametrize("admin_dsn", [
    "postgresql://postgres:postgres@localhost:5432/postgres",
    "postgresql://postgres:postgres@/postgres?host=/var/run/postgresql",
])
def test_dump_fixtures_preserve_the_connection_parameters(monkeypatch, fixture, admin_dsn):
    opened = []

    class Connection:
        def __init__(self, dsn):
            self.params = conninfo_to_dict(dsn)

        def execute(self, sql):
            return self

        def fetchone(self):
            return self.params["dbname"], None if self.params["host"].startswith("/") else "127.0.0.1"

        def close(self):
            pass

    def connect(dsn, **kwargs):
        connection = Connection(dsn)
        opened.append(connection.params)
        return connection

    monkeypatch.setattr(live, "ADMIN", admin_dsn)
    monkeypatch.setattr(psycopg, "connect", connect)
    generator = fixture.__wrapped__()
    try:
        next(generator)
        admin, test = opened
        assert test["dbname"].startswith("ge_")
        assert {k: v for k, v in test.items() if k != "dbname"} == {
            k: v for k, v in admin.items() if k != "dbname"
        }
    finally:
        generator.close()
