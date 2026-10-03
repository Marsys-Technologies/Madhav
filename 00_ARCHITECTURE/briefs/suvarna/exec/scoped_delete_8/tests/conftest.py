"""Disposable local PostgreSQL (initdb into a short temp dir on its own port; never the project database) holding a MIRROR of production's relevant state: the
production roles (reused verbatim from the W1 privilege audit: roles.sql), the production schema-public owner and ACL (schema_acl.sql, verbatim), phala_pramana
and the objects the executor reads (columns, constraints, indexes, owners and ACLs as read from the catalog), and SYNTHETIC rows: the 8 target rows carry
production's ids / non-private values (so their fingerprint equals the pinned production one) and PRIVMARK-... markers in every private column.

PROCESS RULE: the cluster is started by this fixture, its postmaster PID is read from the Popen handle and RECORDED, it is stopped ONLY by signalling that
recorded PID (SIGINT = fast shutdown), and its directory is deleted. Nothing else is signalled. The socket directory is a short path under /tmp (a Unix
socket path is limited to 104 bytes); the cluster listens on 127.0.0.1 only, on a free port.

Set PG_BIN to a bin directory (e.g. /opt/homebrew/opt/postgresql@17/bin) to test another major version. The executor connects as `postgres_mimic` (non-superuser
CREATEROLE, no table privilege, no USAGE on schema public: Cloud SQL's `postgres` as read live; valid on PostgreSQL <= 15).
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
ADMIN_USER = "postgres_mimic"
CHART = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
OTHER_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
PROD_SHADOW_ACL = ("{amjis_app=arwdDxt/amjis_app,retrieval_census_ro=r/amjis_app,role_web_serve=r/amjis_app,role_orchestrator=arwd/amjis_app,"
                   "role_jobs=r/amjis_app,role_sidecar=r/amjis_app,suvarna_reader=r/amjis_app}")
PROD_PHALA_PRAMANA_ACL = ("{amjis_app=arwdDxt/amjis_app,retrieval_census_ro=r/amjis_app,role_web_serve=r/amjis_app,role_orchestrator=arwd/amjis_app,"
                          "role_jobs=r/amjis_app,role_sidecar=r/amjis_app,nirmana_evidence_ingress_writer=r/amjis_app,suvarna_reader=r/amjis_app,"
                          "data_plane_builder=ard/amjis_app}")


def _bin(name):
    pb = os.environ.get("PG_BIN") or "/opt/homebrew/opt/postgresql@15/bin"
    p = os.path.join(pb, name)
    return p if os.path.exists(p) else shutil.which(name)


INITDB, POSTGRES, PSQL = _bin("initdb"), _bin("postgres"), _bin("psql")
HAVE_PG = bool(INITDB and POSTGRES and PSQL)


def load_exec(name="sd8_exec"):
    spec = importlib.util.spec_from_file_location(name, EXEC_DIR / "scoped_delete_8_exec.py")
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
    root = tempfile.mkdtemp(prefix="omit_sd8_", dir="/tmp")
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
        cl.psql_file("tmpl", SCHEMA / "01_schema_acl.sql")
        cl.psql_file("tmpl", SCHEMA / "02_tables.sql")
        cl.psql_file("tmpl", SCHEMA / "03_seed.sql")
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
    monkeypatch.setenv("SD8_TEST_EVIDENCE_ROOT", str(tmp_path / "ev"))


@pytest.fixture()
def db(cluster):
    """A fresh disposable database cloned from the mirror template."""
    return cluster.new_db()


class Runner:
    """Runs execute() against one disposable DB as the administrator role. `apply` first performs the matching dry run in the same state and passes its evidence
    digest (as an operator would). The module's EXPECTED_DATABASE / EXPECTED_ADMIN are pointed at the disposable database / administrator role by the fixture
    (a test that wants production's real constants resets them)."""

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
        if mode == "apply" and not expect_evidence:
            _, d = self.execute(self.args("dry-run", expect_plan=expect_plan), user=user)
            expect_evidence = d.get("evidence_digest") or "0" * 64
        return self.execute(self.args(mode, expect_plan=expect_plan, expect_evidence=expect_evidence), user=user)

    # ------------------------------------------------------------------------------------------------ state images (read as the superuser)
    def su(self, sql, params=None):
        return self.cl.su(self.db, sql, params)

    def state(self):
        with self.cl.conn(self.db, autocommit=True) as c:
            cur = c.cursor()
            out = {}
            for k, q in {
                "schema_acl": "SELECT nspacl::text FROM pg_namespace WHERE nspname='public'",
                "schema_owner": "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'",
                "table_acls": "SELECT string_agg(relname||'='||COALESCE(relacl::text,'NULL')||'='||pg_get_userbyid(relowner), E'\\n' ORDER BY relname) FROM pg_class c "
                              "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND relkind='r'",
                "memberships": "SELECT string_agg(r.rolname||'>'||m.rolname, ',' ORDER BY r.rolname, m.rolname) FROM pg_auth_members am "
                               "JOIN pg_roles r ON r.oid=am.member JOIN pg_roles m ON m.oid=am.roleid",
                "constraints": "SELECT md5(string_agg(conrelid::regclass::text||conname||pg_get_constraintdef(oid), ',' ORDER BY conrelid::regclass::text, conname)) FROM pg_constraint "
                               "WHERE connamespace='public'::regnamespace",
                "triggers": "SELECT string_agg(tgname, ',' ORDER BY tgname) FROM pg_trigger WHERE NOT tgisinternal",
                "objects": "SELECT string_agg(relname||':'||relkind::text, ',' ORDER BY relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                           "WHERE n.nspname='public' AND relkind IN ('r','v','S','m','f','p')",
                "pramana_rows": "SELECT md5(string_agg(t::text, '|' ORDER BY pramana_id)) FROM public.phala_pramana t",
                "pramana_n": "SELECT count(*) FROM public.phala_pramana",
                "by_chart": "SELECT string_agg(chart_id::text||':'||n::text, ',' ORDER BY chart_id) FROM (SELECT chart_id, count(*) n FROM public.phala_pramana GROUP BY 1) s",
                "anchors": "SELECT md5(string_agg(t::text, '|' ORDER BY anchor_id)) FROM public.phala_anchors t",
                "others": "SELECT md5(concat_ws('|', (SELECT md5(string_agg(t::text, '|' ORDER BY id)) FROM public.build_runs t), "
                          "(SELECT md5(string_agg(t::text, '|' ORDER BY id)) FROM public.mimamsa_predictions t), "
                          "(SELECT md5(string_agg(t::text, '|' ORDER BY id)) FROM public.mimamsa_fact_adjustment t)))",
                "shadow_rows": "SELECT md5(string_agg(t::text, '|' ORDER BY pramana_id)) FROM public.phala_pramana__ssv_20260728b t",
                "shadow_n": "SELECT count(*) FROM public.phala_pramana__ssv_20260728b",
                "shadow_by_chart": "SELECT string_agg(chart_id::text||':'||n::text, ',' ORDER BY chart_id) FROM (SELECT chart_id, count(*) n FROM public.phala_pramana__ssv_20260728b GROUP BY 1) s",
            }.items():
                cur.execute(q)
                out[k] = cur.fetchone()[0]
            return out


@pytest.fixture()
def runner(cluster, mod, db, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "EXPECTED_DATABASE", db)
    monkeypatch.setattr(mod, "EXPECTED_ADMIN", ADMIN_USER)
    return Runner(cluster, mod, db, tmp_path)
