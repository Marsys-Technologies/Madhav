"""Disposable local Postgres (initdb into a temp dir on its own port; never the project database) + executor loader.

The executor connects as `adm` = a non-superuser CREATEROLE role (stands in for Cloud SQL's `postgres` admin and exercises the
transient GRANT/REVOKE of amjis_app and data_plane_schema_owner; valid on PostgreSQL <= 15, where CREATEROLE may grant any
non-superuser role). On PostgreSQL >= 16 CREATEROLE alone cannot: run with NODEIDX_TEST_ADMIN=postgres there (superuser).
Set PG_BIN to a bin directory to test another major version. Skips (loudly) when the binaries are absent.
"""
import importlib.util
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
REPO = EXEC_DIR.parents[5]
MIG = REPO / "platform" / "migrations" / "1227_ephemeris_daily_node_series_unique_index.sql"
ADMIN_USER = os.environ.get("NODEIDX_TEST_ADMIN", "adm")


def _bin(name):
    pb = os.environ.get("PG_BIN")
    if pb and os.path.exists(os.path.join(pb, name)):
        return os.path.join(pb, name)
    found = shutil.which(name)
    if found:
        return found
    import glob
    for cand in [f"/opt/homebrew/bin/{name}"] + sorted(glob.glob(f"/usr/lib/postgresql/*/bin/{name}"), reverse=True):
        if os.path.exists(cand):
            return cand
    return None


INITDB, PG_CTL = _bin("initdb"), _bin("pg_ctl")
HAVE_PG = bool(INITDB and PG_CTL) and not (hasattr(os, "geteuid") and os.geteuid() == 0)

ROLES_SQL = """
CREATE ROLE amjis_app NOLOGIN;
CREATE ROLE data_plane_schema_owner NOLOGIN;
CREATE ROLE adm LOGIN CREATEROLE;
CREATE ROLE other_writer LOGIN;
"""
LIVE_DDL = (REPO / "platform" / "python-sidecar" / "tests" / "test_ephemeris_node_index_1227_sql.py").read_text()
LIVE_DDL = LIVE_DDL.split('LIVE_DDL = """', 1)[1].split('"""', 1)[0]
TOPOLOGY = """
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO amjis_app, other_writer;
ALTER TABLE public.ephemeris_daily OWNER TO amjis_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ephemeris_daily TO other_writer;
"""
SEED = """
INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode, epoch_convention)
SELECT DATE '2000-01-01' + n, b.body, (n * 1.5 + b.i)::numeric,
       CASE WHEN b.body IN ('Rahu', 'Ketu') THEN 'true' END, 'noon_ut'
FROM generate_series(0, 29) n,
     (VALUES ('Sun',0),('Moon',1),('Mars',2),('Mercury',3),('Jupiter',4),('Venus',5),('Saturn',6),('Rahu',7),('Ketu',8)) b(body, i);
"""


def load_exec():
    spec = importlib.util.spec_from_file_location("node_index_exec", EXEC_DIR / "node_index_exec.py")
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

    def image(self, db):
        """Everything the executor must leave unchanged, plus the index catalog."""
        with self.conn(db, autocommit=True) as c:
            cur = c.cursor()
            out = {}
            cur.execute("SELECT count(*), coalesce(bit_xor(hashtextextended(t::text,0)),0) FROM public.ephemeris_daily t")
            out["data"] = cur.fetchone()
            cur.execute("SELECT relname, relacl::text, pg_get_userbyid(relowner) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' ORDER BY 1")
            out["rel"] = cur.fetchall()
            cur.execute("SELECT nspname, pg_get_userbyid(nspowner), nspacl::text FROM pg_namespace WHERE nspname='public'")
            out["nsp"] = cur.fetchall()
            cur.execute("SELECT r.rolname, m.rolname FROM pg_auth_members am JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member WHERE r.rolname !~ '^pg_' ORDER BY 1,2")
            out["mem"] = cur.fetchall()
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename='ephemeris_daily' ORDER BY 1")
            out["idx"] = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT conname FROM pg_constraint WHERE conrelid='public.ephemeris_daily'::regclass ORDER BY 1")
            out["con"] = [r[0] for r in cur.fetchall()]
            return out


@pytest.fixture(scope="session")
def cluster():
    if not HAVE_PG:
        pytest.skip("no local Postgres binaries (or running as root): D6 executor tests NOT RUN")
    d = tempfile.mkdtemp(prefix="pgnodeidx_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o", f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d} -c fsync=off",
                    "-l", d + "/log", "-w", "start"], check=True, capture_output=True)
    cl = Cluster(port)
    try:
        cl.su("postgres", ROLES_SQL)
        cl.su("postgres", "CREATE DATABASE tmpl")
        with cl.conn("tmpl", autocommit=True) as c:
            c.execute(LIVE_DDL)
            c.execute(SEED)
            c.execute(TOPOLOGY)
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


@pytest.fixture(autouse=True)
def evidence_env(monkeypatch, tmp_path):
    """The executor writes under the real evidence root unless this test-only variable is set."""
    monkeypatch.setenv("NODEIDX_TEST_EVIDENCE_ROOT", str(tmp_path / "ev"))
    monkeypatch.delenv("NODEIDX_TEST_MIGRATION_FILE", raising=False)


class Runner:
    def __init__(self, cluster, mod, db, tmp_path):
        self.cl, self.m, self.db, self.tmp = cluster, mod, db, tmp_path

    def execute(self, argv):
        return self.m.execute(self.m.parse_args(argv), lambda: self.cl.conn(self.db, user=ADMIN_USER))

    def dry(self):
        return self.execute(["--dry-run"])

    def apply(self, **over):
        code, rep = self.dry()
        plan = over.get("plan") or self.m.plan_hash()
        ev = over.get("evidence") or rep.get("evidence_digest", "0" * 64)
        return self.execute(["--apply", "--expect-plan", plan, "--expect-evidence", ev])


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return Runner(cluster, mod, db, tmp_path)
