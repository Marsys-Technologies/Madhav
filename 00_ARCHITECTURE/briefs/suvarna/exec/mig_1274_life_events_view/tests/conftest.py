"""Disposable local PostgreSQL (initdb into a short temp dir on its own port; never the project database) holding a MIRROR of production's
relevant state: the production roles (reused verbatim from the W1 privilege audit: roles.sql), the production schema-public owner and ACL
(schema_acl.sql, verbatim), life_events with production's columns, ACL, policies, G1c accessor and amjis_app's default ACL, and SYNTHETIC rows
for three charts (two with events, one without).

PROCESS RULE: the cluster is started by this fixture, its postmaster PID is read from postmaster.pid and RECORDED, it is stopped ONLY by
signalling that recorded PID (SIGINT = fast shutdown), and its directory is deleted. Nothing else is signalled. The socket directory is a short
path under /tmp (a Unix socket path is limited to 104 bytes); the cluster listens on 127.0.0.1 only, on a free port.

Set PG_BIN to a bin directory (e.g. /opt/homebrew/opt/postgresql@17/bin) to test another major version. The executor connects as `postgres_mimic`
(non-superuser CREATEROLE, no table privilege, no USAGE on schema public: Cloud SQL's `postgres` as read live; valid on PostgreSQL <= 15). The executor
refuses a superuser, so the plan is PostgreSQL 15 only; other majors are exercised only to show the refusal.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import psycopg
import pytest

HERE = pathlib.Path(__file__).resolve().parent
EXEC_DIR = HERE.parent
REPO = EXEC_DIR.parents[4]
SCHEMA = HERE / "schema"
ADMIN_USER = os.environ.get("M1274_TEST_ADMIN", "postgres_mimic")
CHART_A = "aaaaaaaa-1111-4222-8333-00000000000a"
CHART_B = "bbbbbbbb-1111-4222-8333-00000000000b"
CHART_C = "cccccccc-1111-4222-8333-00000000000c"       # a chart with no events


def _bin(name):
    pb = os.environ.get("PG_BIN") or "/opt/homebrew/opt/postgresql@15/bin"
    p = os.path.join(pb, name)
    return p if os.path.exists(p) else shutil.which(name)


INITDB, POSTGRES, PSQL = _bin("initdb"), _bin("postgres"), _bin("psql")
HAVE_PG = bool(INITDB and POSTGRES and PSQL)


def load_exec(name="mig_1274_exec"):
    spec = importlib.util.spec_from_file_location(name, EXEC_DIR / "mig_1274_life_events_view_exec.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


class Cluster:
    def __init__(self, port, root, pid, major):
        self.port, self.root, self.pid, self.major = port, root, pid, major

    def conn(self, db, user="postgres", autocommit=False):
        return psycopg.connect(host="127.0.0.1", port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10)

    def su(self, db, sql, params=None, user="postgres"):
        with self.conn(db, user=user, autocommit=True) as c:
            cur = c.cursor()
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else None

    def psql_file(self, db, path, user="postgres", preamble=""):
        sql = preamble + pathlib.Path(path).read_text()
        r = subprocess.run([PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(self.port), "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1"],
                           input=sql, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"psql {path} failed: {r.stderr[-800:]}")
        return r

    def new_db(self):
        name = "t" + uuid.uuid4().hex[:10]
        self.su("postgres", f"CREATE DATABASE {name} TEMPLATE tmpl")
        return name


@pytest.fixture(scope="session")
def cluster():
    if not HAVE_PG:
        pytest.skip("no local PostgreSQL binaries (set PG_BIN)")
    root = tempfile.mkdtemp(prefix="omit_m1274_", dir="/tmp")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", root + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], check=True, capture_output=True)
    log = open(root + "/log", "wb")
    proc = subprocess.Popen([POSTGRES, "-D", root + "/data", "-p", str(port), "-c", "listen_addresses=127.0.0.1", "-c", f"unix_socket_directories={root}",
                             "-c", "fsync=off", "-c", "full_page_writes=off", "-c", "max_connections=60"], stdout=log, stderr=log)
    pid = proc.pid                                              # the RECORDED PID: the only process this fixture will ever signal
    try:
        for _ in range(100):
            try:
                psycopg.connect(host="127.0.0.1", port=port, dbname="postgres", user="postgres", connect_timeout=2).close()
                break
            except psycopg.OperationalError:
                time.sleep(0.2)
        else:
            raise RuntimeError("disposable PostgreSQL did not start")
        major = int(subprocess.run([PSQL, "-X", "-A", "-t", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", "postgres", "-c",
                                    "SHOW server_version_num"], capture_output=True, text=True).stdout.strip()) // 10000
        cl = Cluster(port, root, pid, major)
        cl.su("postgres", (SCHEMA / "00_roles.sql").read_text())
        cl.su("postgres", "CREATE DATABASE tmpl")
        cl.su("tmpl", "CREATE EXTENSION pgcrypto")
        cl.psql_file("tmpl", SCHEMA / "01_schema_acl.sql")
        cl.psql_file("tmpl", SCHEMA / "02_life_events.sql")
        yield cl
    finally:
        try:
            os.kill(pid, signal.SIGINT)                         # fast shutdown of OUR postmaster, by the recorded PID
            proc.wait(timeout=60)
        except Exception:
            try:
                os.kill(pid, signal.SIGQUIT)
                proc.wait(timeout=30)
            except Exception:
                pass
        log.close()
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture(scope="session")
def mod():
    m = load_exec()

    def boom(*a, **k):
        raise AssertionError("a test reached the Secret Manager: tests inject a disposable connection and never fetch a credential")
    m.secret = boom
    return m


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("M1274_TEST_EVIDENCE_ROOT", str(tmp_path / "ev"))


@pytest.fixture()
def db(cluster):
    """A fresh disposable database cloned from the mirror template."""
    return cluster.new_db()


class Runner:
    """Runs execute() against one disposable DB as the administrator role. `apply`/`rollback` first perform the matching dry run in the same
    state and pass its evidence digest (as an operator would)."""

    def __init__(self, cluster, mod, db, tmp_path):
        self.cl, self.m, self.db, self.tmp = cluster, mod, db, tmp_path

    def args(self, mode, expect_plan=None, expect_evidence=None):
        a = ["--" + mode, "--expect-plan", expect_plan or self.m.plan_hash()]
        if expect_evidence:
            a += ["--expect-evidence", expect_evidence]
        return self.m.parse_args(a)

    def execute(self, args, user=None):
        return self.m.execute(args, lambda: self.cl.conn(self.db, user=user or ADMIN_USER))

    def run(self, mode, expect_evidence=None, expect_plan=None, user=None):
        if mode in ("apply", "rollback") and not expect_evidence:
            dry = "dry-run" if mode == "apply" else "rollback-dry-run"
            _, d = self.execute(self.args(dry, expect_plan=expect_plan), user=user)
            expect_evidence = d.get("evidence_digest") or "0" * 64
        return self.execute(self.args(mode, expect_plan=expect_plan, expect_evidence=expect_evidence), user=user)

    # ------------------------------------------------------------------------------------------------ state images (read as the superuser)
    def state(self):
        with self.cl.conn(self.db, autocommit=True) as c:
            cur = c.cursor()
            out = {}
            for k, q in {
                "schema_acl": "SELECT nspacl::text FROM pg_namespace WHERE nspname='public'",
                "schema_owner": "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'",
                "table_acl": "SELECT relacl::text FROM pg_class WHERE oid='public.life_events'::regclass",
                "view": "SELECT (SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND relname='life_events_chart_scoped')",
                "memberships": "SELECT string_agg(r.rolname||'>'||m.rolname, ',' ORDER BY r.rolname, m.rolname) FROM pg_auth_members am "
                               "JOIN pg_roles r ON r.oid=am.member JOIN pg_roles m ON m.oid=am.roleid",
                "col_acl": "SELECT string_agg(attname||':'||attacl::text, ',' ORDER BY attname) FROM pg_attribute WHERE attrelid='public.life_events'::regclass AND attacl IS NOT NULL",
                "rows": "SELECT count(*) FROM public.life_events",
                "row_digest": "SELECT md5(string_agg(t::text, '|' ORDER BY id)) FROM public.life_events t",
                "fn": "SELECT md5(pg_get_functiondef('public.app_chart_context()'::regprocedure))",
                "default_acl": "SELECT string_agg(defaclacl::text, ',') FROM pg_default_acl",
                "other_objects": "SELECT string_agg(relname||':'||relkind::text, ',' ORDER BY relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                                 "WHERE n.nspname='public' AND relkind IN ('r','v','S','m','f','p')",
            }.items():
                cur.execute(q)
                out[k] = cur.fetchone()[0]
            return out


@pytest.fixture()
def runner(cluster, mod, db, tmp_path, monkeypatch):
    # the executor refuses any connection but production's (database amjis, administrator postgres, PostgreSQL 15); the disposable stand-ins are named here
    monkeypatch.setattr(mod, "EXPECTED_DATABASE", db)
    monkeypatch.setattr(mod, "EXPECTED_ADMIN", ADMIN_USER)
    monkeypatch.setattr(mod, "EXPECTED_MAJOR", cluster.major)
    return Runner(cluster, mod, db, tmp_path)

# --- no test may launch a real cloud command (2026-10-05 incident): installed at conftest import, see platform/scripts/governance/no_real_cloud_guard.py ---
import pathlib as _pl
import sys as _sys
for _p in _pl.Path(__file__).resolve().parents:
    for _cand in (_p / "scripts" / "governance", _p / "platform" / "scripts" / "governance"):
        if (_cand / "no_real_cloud_pytest.py").exists():
            _sys.path.insert(0, str(_cand))
            break
    else:
        continue
    break
from no_real_cloud_pytest import *  # noqa: E402,F401,F403  (an ImportError here must stay loud: no silent disabling)
