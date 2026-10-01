"""A disposable local Postgres for migration tests (initdb into a temp dir; never the project database).

Used by test_argala_1219_migration_static.py and test_argala_1221_integrity_a29.py. Skips when the binaries are
absent. Import the `pg` fixture into a test module with: from tests.pg_disposable import pg  # noqa: F401
"""
from __future__ import annotations

import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import uuid

import pytest


def _bin(name: str) -> str | None:
    return shutil.which(name) or (f"/opt/homebrew/bin/{name}" if os.path.exists(f"/opt/homebrew/bin/{name}") else None)


INITDB, PG_CTL, PSQL = _bin("initdb"), _bin("pg_ctl"), _bin("psql")
HAVE_PG = bool(INITDB and PG_CTL and PSQL)
requires_pg = pytest.mark.skipif(not HAVE_PG, reason="no local Postgres binaries")


@pytest.fixture(scope="module")
def pg():
    if not HAVE_PG:
        pytest.skip("no local Postgres binaries")
    d = tempfile.mkdtemp(prefix="pgdisp_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"],
                   check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o",
                    f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d}",
                    "-l", d + "/log", "-w", "start"], check=True, capture_output=True)
    try:
        yield port
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


def psql(port: int, db: str, sql: str | None = None, file: pathlib.Path | None = None):
    cmd = [PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", db,
           "-v", "ON_ERROR_STOP=1"]
    cmd += ["-f", str(file)] if file else ["-c", sql]
    return subprocess.run(cmd, capture_output=True, text=True)


def q(port: int, db: str, sql: str) -> str:
    r = psql(port, db, sql)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def new_db(port: int) -> str:
    db = "t" + uuid.uuid4().hex[:10]
    assert psql(port, "postgres", f"CREATE DATABASE {db}").returncode == 0
    return db
