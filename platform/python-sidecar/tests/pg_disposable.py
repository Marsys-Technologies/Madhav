"""A disposable local Postgres for migration tests (initdb into a temp dir; never the project database).

Used by test_argala_migration_1219_sql.py and test_argala_migration_1221_sql.py (kept byte-identical in the two PRs
that add it). Finds the server binaries via $PG_BIN, PATH, Homebrew and /usr/lib/postgresql/*/bin (newest first); skips
loudly (see PG_SKIP_REASON) when they are absent or when running as root (initdb refuses root). Import the `pg`
fixture into a test module with: from tests.pg_disposable import pg  # noqa: F401
"""
from __future__ import annotations

import glob
import os
import pathlib
import re
import shutil
import socket
import subprocess
import tempfile
import uuid

import pytest


def _version_key(path: str) -> tuple[int, ...]:
    """/usr/lib/postgresql/16/bin -> (16,); numeric, so 17 sorts above 9 and 16 (a plain string sort would not)."""
    ver = os.path.basename(os.path.dirname(path))
    return tuple(int(x) for x in re.findall(r"\d+", ver)) or (0,)


def _find_pg_bin() -> pathlib.Path | None:
    """The first directory holding initdb, pg_ctl AND psql: $PG_BIN, then PATH, then Homebrew, then
    /usr/lib/postgresql/*/bin newest first (the Debian/Ubuntu layout, where the server binaries are NOT on PATH,
    as on the GitHub-hosted ubuntu runner). Same lookup order as the other migration tests' _find_pg_bin."""
    cands: list[pathlib.Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(pathlib.Path(os.environ["PG_BIN"]))
    on_path = shutil.which("initdb")
    if on_path:
        cands.append(pathlib.Path(on_path).resolve().parent)
    cands.append(pathlib.Path("/opt/homebrew/bin"))
    cands += [pathlib.Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), key=_version_key, reverse=True)]
    for c in cands:
        if all((c / n).exists() for n in ("initdb", "pg_ctl", "psql")):
            return c
    return None


PG_BIN_DIR = _find_pg_bin()
INITDB, PG_CTL, PSQL = ((str(PG_BIN_DIR / n) for n in ("initdb", "pg_ctl", "psql")) if PG_BIN_DIR else (None, None, None))
# initdb refuses to run as root (a root CI step or container): skip with a loud reason rather than fail.
_IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
if not PG_BIN_DIR:
    PG_SKIP_REASON = ("no PostgreSQL server binaries (initdb, pg_ctl, psql) found: looked in $PG_BIN, PATH, /opt/homebrew/bin, "
                      "/usr/lib/postgresql/*/bin; set PG_BIN to pin a directory")
elif _IS_ROOT:
    PG_SKIP_REASON = "running as root: initdb refuses root, so the disposable cluster cannot start; run as an unprivileged user"
else:
    PG_SKIP_REASON = ""
HAVE_PG = not PG_SKIP_REASON
requires_pg = pytest.mark.skipif(not HAVE_PG, reason="DB-backed migration test NOT RUN: " + PG_SKIP_REASON)


@pytest.fixture(scope="module")
def pg():
    if not HAVE_PG:
        pytest.skip("DB-backed migration test NOT RUN: " + PG_SKIP_REASON)
    d = tempfile.mkdtemp(prefix="pgdisp_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    r = subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"initdb failed (rc {r.returncode}) with {INITDB}: {r.stderr.strip()[-800:]}")
    r = subprocess.run([PG_CTL, "-D", d + "/data", "-o",
                        f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d} -c fsync=off",
                        "-l", d + "/log", "-w", "start"], capture_output=True, text=True)
    if r.returncode != 0:
        log = pathlib.Path(d, "log").read_text(errors="replace")[-800:] if pathlib.Path(d, "log").exists() else ""
        raise RuntimeError(f"pg_ctl start failed (rc {r.returncode}): {r.stderr.strip()[-400:]} | log: {log}")
    try:
        yield port
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


def psql(port: int, db: str, sql: str | None = None, file: pathlib.Path | None = None, single_transaction: bool = False):
    cmd = [PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", db,
           "-v", "ON_ERROR_STOP=1"]
    if single_transaction:          # the migrate.ts shape: one transaction, rolled back whole on any error
        cmd.append("--single-transaction")
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
