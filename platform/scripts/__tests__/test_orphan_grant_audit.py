"""C51 — tests for platform/scripts/orphan-grant-audit.sh.

The runner is a READ-ONLY audit: every NOLOGIN role with no members that holds
INSERT/UPDATE/DELETE/TRUNCATE on any table in schema public, as TSV evidence. Semantics are
tested against a REAL disposable cluster (fixture roles/grants, runner invoked with the real
pinned SQL file); the preflight refusals (tampered SQL file, writable session) are tested with
a stubbed psql, and the no-DSN guarantee is asserted from the stub's argv log.
"""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/orphan-grant-audit.sh"
SQL_FILE = REPO / "platform/scripts/readbacks/orphan_dml_grant_audit.sql"
PIN = hashlib.sha256(SQL_FILE.read_bytes()).hexdigest()

sys.path.insert(0, str(REPO / "platform/scripts/governance/__tests__"))
try:
    from _disposable_pg import disposable_pg, point_psql_at  # noqa: F401  (fixture import)
except Exception:  # pragma: no cover
    @pytest.fixture(scope="session")
    def disposable_pg():
        pytest.skip("the _disposable_pg helper is unavailable")

    def point_psql_at(cl, monkeypatch):  # noqa: ARG001
        pytest.skip("the _disposable_pg helper is unavailable")


@pytest.fixture(scope="session", autouse=True)
def _c_locale():
    old = os.environ.get("LC_ALL")
    os.environ["LC_ALL"] = "C"
    yield
    if old is None:
        os.environ.pop("LC_ALL", None)
    else:
        os.environ["LC_ALL"] = old


SETUP = """
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'c51_orphan_a') THEN
    CREATE ROLE c51_orphan_a NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'c51_orphan_b') THEN
    CREATE ROLE c51_orphan_b NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'c51_group') THEN
    CREATE ROLE c51_group NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'c51_holder') THEN
    CREATE ROLE c51_holder NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'c51_member') THEN
    CREATE ROLE c51_member LOGIN; END IF;
END $$;
DROP TABLE IF EXISTS public.c51_audit_t1;
DROP TABLE IF EXISTS public.c51_audit_t2;
DROP TABLE IF EXISTS public.c51_audit_t3;
CREATE TABLE public.c51_audit_t1 (id int);
CREATE TABLE public.c51_audit_t2 (id int);
CREATE TABLE public.c51_audit_t3 (id int);
-- orphan_a: NOLOGIN, no members, INSERT+DELETE on t1 -> LISTED
GRANT INSERT, DELETE ON public.c51_audit_t1 TO c51_orphan_a;
-- orphan_b: NOLOGIN, no members, TRUNCATE on t2 -> LISTED
GRANT TRUNCATE ON public.c51_audit_t2 TO c51_orphan_b;
-- group: NOLOGIN but HAS a member -> excluded even with DML
GRANT INSERT ON public.c51_audit_t1 TO c51_group;
GRANT c51_group TO c51_member;
-- holder: NOLOGIN, no members, SELECT only -> excluded
GRANT SELECT ON public.c51_audit_t3 TO c51_holder;
"""


def _psql(env, sql):
    p = subprocess.run(["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr


def _run_audit(env, tmp_path, name="out"):
    out = tmp_path / name
    proc = subprocess.run([str(SCRIPT), "--out", str(out), "--sql-file", str(SQL_FILE)],
                          capture_output=True, text=True, env=env, cwd=REPO)
    return proc, out


def test_lists_exactly_the_orphan_roles(disposable_pg, monkeypatch, tmp_path):
    point_psql_at(disposable_pg, monkeypatch)
    env = dict(os.environ)
    _psql(env, SETUP)
    try:
        proc, out = _run_audit(env, tmp_path)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        rows = [l.split("\t") for l in (out / "orphan_dml_grants.tsv").read_text().splitlines()]
        got = {(r[0], r[1], r[4]) for r in rows}
        assert ("c51_orphan_a", "c51_audit_t1", "DELETE,INSERT") in got
        assert ("c51_orphan_b", "c51_audit_t2", "TRUNCATE") in got
        assert not any(r[0] in ("c51_group", "c51_holder") for r in rows)
        # table owner and grantor columns are populated
        assert all(r[2] and r[3] for r in rows)
        assert "PASS AUDIT-complete" in proc.stdout
    finally:
        _psql(env, "DROP TABLE IF EXISTS public.c51_audit_t1, public.c51_audit_t2,"
                   " public.c51_audit_t3;")


def test_an_empty_audit_is_a_clean_pass(disposable_pg, monkeypatch, tmp_path):
    point_psql_at(disposable_pg, monkeypatch)
    env = dict(os.environ)
    _psql(env, SETUP)      # then take every fixture grant back
    _psql(env, "REVOKE INSERT, DELETE ON public.c51_audit_t1 FROM c51_orphan_a;"
               " REVOKE TRUNCATE ON public.c51_audit_t2 FROM c51_orphan_b;"
               " REVOKE INSERT ON public.c51_audit_t1 FROM c51_group;")
    try:
        proc, out = _run_audit(env, tmp_path, name="out2")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        rows = (out / "orphan_dml_grants.tsv").read_text()
        # the cluster is session-shared: only OUR fixture roles must be gone
        assert "c51_orphan" not in rows and "c51_group" not in rows and "c51_holder" not in rows
        assert "PASS AUDIT-complete" in proc.stdout
    finally:
        _psql(env, "DROP TABLE IF EXISTS public.c51_audit_t1, public.c51_audit_t2,"
                   " public.c51_audit_t3;")


# ── preflight refusals (stubbed psql) ───────────────────────────────────────

STUB = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
with open(os.environ["PSQL_ARGV_LOG"], "a") as f:
    f.write("\\t".join(args) + "\\n")
    f.write("PGOPTIONS=" + os.environ.get("PGOPTIONS", "") + "\\n")
sql = ""
for i, a in enumerate(args):
    if a == "-c" and i + 1 < len(args):
        sql = args[i + 1]
    if a == "-f" and i + 1 < len(args):
        sql = open(args[i + 1]).read()
if "SHOW transaction_read_only" in sql and "default" not in sql:
    print(os.environ.get("STUB_RO", "on")); sys.exit(0)
if "SHOW default_transaction_read_only" in sql:
    print("on"); sys.exit(0)
if "current_user" in sql or "current_database" in sql:
    print("x"); sys.exit(0)
sys.exit(0)
"""


def _stub_env(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    stub = bindir / "psql"
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    argv_log = tmp_path / "argv.log"
    argv_log.touch()
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    env["PSQL_ARGV_LOG"] = str(argv_log)
    for k in [k for k in env if k.startswith("PG")]:
        env.pop(k)
    return env, argv_log


def test_a_tampered_sql_file_is_never_executed(tmp_path):
    env, argv_log = _stub_env(tmp_path)
    tampered = tmp_path / "tampered.sql"
    tampered.write_text(SQL_FILE.read_text() + "-- tampered\n")
    proc = subprocess.run([str(SCRIPT), "--out", str(tmp_path / "o"), "--sql-file", str(tampered)],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 1 and "sha256" in proc.stderr
    assert not argv_log.read_text().strip()            # psql was never even called


def test_a_writable_session_is_refused_and_no_dsn_is_used(tmp_path):
    env, argv_log = _stub_env(tmp_path)
    env["STUB_RO"] = "off"
    proc = subprocess.run([str(SCRIPT), "--out", str(tmp_path / "o"), "--sql-file", str(SQL_FILE)],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 2 and "not read-only" in proc.stderr
    log = argv_log.read_text()
    assert "-d" not in log and "--dbname" not in log and "postgresql://" not in log
    assert "default_transaction_read_only=on" in log   # still forced through the environment
