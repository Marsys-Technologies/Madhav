"""Disposable PostgreSQL fixture and earned-signal rules for Kāla DB tests."""
from __future__ import annotations

import os
import ipaddress
import json
import subprocess
import uuid

import psycopg
import pytest

from tests.l3._disposable_db_guard import (
    RefusedError,
    assert_disposable_connection,
    validate_disposable_dsn,
)


def _assert_kala_disposable_connection(conn, name: str, dsn: str) -> None:
    """Accept CI's shared guard or the validated, lane-owned local Docker server."""
    try:
        assert_disposable_connection(conn, name)
        return
    except RefusedError as original:
        # Local Docker publishes 127.0.0.1, but Postgres reports 172.17.x.x.
        # Bind that address to the specific campaign container before any SQL
        # that creates or removes a database. Every other refusal stays fatal.
        info = psycopg.conninfo.conninfo_to_dict(dsn)
        if info.get("host") != "127.0.0.1" or info.get("port") != os.environ.get("KY_PG_PORT", "55433"):
            raise original
        try:
            inspected = subprocess.run(
                ["docker", "inspect", "ky-pg"],
                check=True, capture_output=True, text=True, timeout=5,
            )
            container = json.loads(inspected.stdout)[0]
            bindings = container["NetworkSettings"]["Ports"]["5432/tcp"]
            addresses = {
                network["IPAddress"]
                for network in container["NetworkSettings"]["Networks"].values()
            }
            dbname, server_addr = conn.execute(
                "SELECT current_database(), inet_server_addr()::text"
            ).fetchone()
            server_ip = ipaddress.ip_interface(server_addr).ip
            accepted = (
                container["State"]["Running"]
                and container["Config"]["Image"] == "pgvector/pgvector:pg16"
                and container["Config"]["Labels"].get("campaign") == "kalayantra"
                and {tuple((b["HostIp"], b["HostPort"])) for b in bindings}
                == {("127.0.0.1", info["port"])}
                and dbname == name
                and str(server_ip) in addresses
            )
        except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError):
            raise original
        if not accepted:
            raise original


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """A skipped test cannot count as a green DB job when DB proof is required."""
    if os.environ.get("KALA_REQUIRE_DB") != "1":
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None and reporter.stats.get("skipped"):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(scope="session")
def kala_db_dsn() -> str:
    admin_dsn = os.environ.get("KALA_ADMIN_DSN")
    if not admin_dsn:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail("KALA_REQUIRE_DB=1 but KALA_ADMIN_DSN is absent")
        pytest.skip("NOT_RUN: KALA_ADMIN_DSN is absent")
    validate_disposable_dsn(admin_dsn, "postgres")
    try:
        admin = psycopg.connect(admin_dsn, autocommit=True, connect_timeout=3)
    except psycopg.Error as exc:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail(f"KALA_REQUIRE_DB=1 but disposable Postgres is unreachable: {exc}")
        pytest.skip(f"NOT_RUN: disposable Postgres is unreachable: {exc}")
    name = f"kala_ci_{uuid.uuid4().hex}"
    created = False
    try:
        _assert_kala_disposable_connection(admin, "postgres", admin_dsn)
        admin.execute(f'CREATE DATABASE "{name}"')
        created = True
        db_dsn = psycopg.conninfo.make_conninfo(admin_dsn, dbname=name)
        validate_disposable_dsn(db_dsn, name)
        with psycopg.connect(db_dsn, connect_timeout=3) as probe:
            _assert_kala_disposable_connection(probe, name, db_dsn)
        yield db_dsn
    finally:
        # Never issue cleanup SQL if the connection guard refused the server.
        if created:
            admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", (name,))
            admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.close()
