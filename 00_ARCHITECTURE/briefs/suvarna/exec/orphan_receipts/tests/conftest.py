"""Disposable local Postgres (initdb into a temp dir on its own port; never the project database) + executor loader.

Pattern copied from tests/pg_disposable.py on suvarna/land/TI-argala-l1-001. Skips when the binaries are absent.
Set PG_BIN to a bin directory (e.g. /opt/homebrew/opt/postgresql@17/bin) to test against another major version.
"""
import importlib.util
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid

import psycopg
import pytest

HERE = pathlib.Path(__file__).resolve().parent
EXEC_DIR = HERE.parent
sys.path.insert(0, str(HERE))
import fixture_schema as fx  # noqa: E402


def _bin(name):
    pb = os.environ.get("PG_BIN")
    if pb and os.path.exists(os.path.join(pb, name)):
        return os.path.join(pb, name)
    return shutil.which(name) or (f"/opt/homebrew/bin/{name}" if os.path.exists(f"/opt/homebrew/bin/{name}") else None)


# The executor connects as this role. Default `adm` = non-superuser CREATEROLE (stands in for Cloud SQL's postgres admin and
# exercises the transient GRANT/REVOKE of amjis_app; valid on PostgreSQL <= 15, where CREATEROLE may grant any non-superuser
# role). On PostgreSQL >= 16 CREATEROLE alone cannot, so run with ORPH_TEST_ADMIN=postgres there (superuser: no GRANT needed).
ADMIN_USER = os.environ.get("ORPH_TEST_ADMIN", "adm")
INITDB, PG_CTL, PSQL = _bin("initdb"), _bin("pg_ctl"), _bin("psql")
HAVE_PG = bool(INITDB and PG_CTL and PSQL)


def load_exec():
    spec = importlib.util.spec_from_file_location("orphan_receipts_exec", EXEC_DIR / "orphan_receipts_exec.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Cluster:
    def __init__(self, port):
        self.port = port

    def conn(self, db, user="postgres", autocommit=False):
        return psycopg.connect(host="127.0.0.1", port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10)

    def su(self, db, sql, params=None):
        with self.conn(db, autocommit=True) as c:
            cur = c.cursor()
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else None

    def new_db(self):
        name = "t" + uuid.uuid4().hex[:10]
        self.su("postgres", f"CREATE DATABASE {name} TEMPLATE tmpl")
        return name

    def psql_file(self, db, path):
        return subprocess.run([PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(self.port), "-U", "postgres", "-d", db,
                               "-v", "ON_ERROR_STOP=1", "-f", str(path)], capture_output=True, text=True)

    def image(self, db):
        """Byte-level image of the DB: md5 of every row of every table, plus the ACL/RLS/policy/membership catalogs."""
        out = {}
        with self.conn(db, autocommit=True) as c:
            cur = c.cursor()
            for t in ("charts", "asset_registry", "asset_output_digest_specs", "build_runs", "build_run_assets",
                      "asset_provenance_receipts", "asset_freshness"):
                cur.execute(f"SELECT coalesce(md5(string_agg(x::text, '|' ORDER BY x::text)), 'empty'), count(*) FROM public.{t} x")
                out[t] = cur.fetchone()
            cur.execute("SELECT relname, relacl::text, pg_get_userbyid(relowner), relrowsecurity, relforcerowsecurity FROM pg_class "
                        "JOIN pg_namespace n ON n.oid=relnamespace WHERE n.nspname='public' AND relkind='r' ORDER BY 1")
            out["rel"] = cur.fetchall()
            cur.execute("SELECT c.relname, p.polname FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid ORDER BY 1,2")
            out["pol"] = cur.fetchall()
            cur.execute("SELECT r.rolname, m.rolname, am.admin_option FROM pg_auth_members am JOIN pg_roles r ON r.oid=am.roleid "
                        "JOIN pg_roles m ON m.oid=am.member WHERE r.rolname !~ '^pg_' ORDER BY 1,2")
            out["mem"] = cur.fetchall()
        return out


@pytest.fixture(scope="session")
def cluster():
    if not HAVE_PG:
        pytest.skip("no local Postgres binaries")
    d = tempfile.mkdtemp(prefix="pgorph_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o", f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d}",
                    "-l", d + "/log", "-w", "start"], check=True, capture_output=True)
    cl = Cluster(port)
    try:
        cl.su("postgres", fx.ROLES_SQL)
        cl.su("postgres", "CREATE DATABASE tmpl")
        with cl.conn("tmpl", autocommit=True) as c:
            c.execute(fx.SCHEMA_SQL)
        with cl.conn("tmpl") as c:
            fx.seed_world(c.cursor())
            c.commit()
        yield cl
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="session")
def mod():
    return load_exec()


@pytest.fixture()
def db(cluster):
    return cluster.new_db()


class Runner:
    """Runs the executor's execute() against one fixture DB as the non-superuser admin `adm`."""

    def __init__(self, cluster, mod, db, tmp_path):
        self.cl, self.m, self.db, self.tmp = cluster, mod, db, tmp_path
        self.ev = str(tmp_path / "ev")

    def args(self, mode, asset="ga_positions", chart=fx.CANON, min_after=fx.MIN_AFTER, expect_plan=None, expect_evidence=None):
        a = ["--asset", asset, "--chart", chart]
        a += ["--dry-run"] if mode == "dry" else ["--apply", "--expect-plan", expect_plan or self.m.plan_hash(asset, chart)]
        if min_after is not None:
            a += ["--min-build-after", min_after]
        if expect_evidence:
            a += ["--expect-evidence", expect_evidence]
        return self.m.parse_args(a)

    def run(self, mode, evidence_root=None, **kw):
        args = self.args(mode, **kw)
        return self.m.execute(args, lambda: self.cl.conn(self.db, user=ADMIN_USER), evidence_root=evidence_root or self.ev)


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return Runner(cluster, mod, db, tmp_path)
