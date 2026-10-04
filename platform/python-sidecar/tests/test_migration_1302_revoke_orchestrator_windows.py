"""Migration 1302 (Pravāha C39): REVOKE role_orchestrator's UPDATE/DELETE/INSERT (table- and column-level)
on public.kala_gochara_windows, no-op where the role is absent, with a raising post-check.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the
end), once per available major version (15 and 17). Nothing here touches any real database. The cluster
is shaped like production: a LOGIN role `amjis_app` OWNS schema public and the table; the migration is
applied as the owner inside one transaction, the way platform/scripts/migrate.ts does (BEGIN; <sql>; COMMIT).

What it proves:
  * apply_twice        with role_orchestrator holding table-level UPDATE+DELETE AND a column-level UPDATE:
                       after ONE apply the role has no effective UPDATE/DELETE path (table or column), its
                       SELECT and every other role's privileges are untouched, and a SECOND apply is a clean
                       no-op (same end state, no error);
  * role_absent        where pg_roles has no role_orchestrator the whole migration is a NOTICE no-op;
  * assertion_fires    a mutant with the REVOKE statements stripped must RAISE the migration's own 1302
                       exception and roll back (the privileges survive) — the post-check is load-bearing;
  * only_writes        role_orchestrator's SELECT on the table and an unrelated role's ALL grant survive.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import psycopg
import pytest

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1302_revoke_role_orchestrator_windows_dml.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")
VERSIONS = ["15", "17"]


def _bindir(version: str) -> Path | None:
    for cand in (
        os.environ.get(f"PG{version}_BIN"),
        f"/opt/homebrew/opt/postgresql@{version}/bin",
        f"/usr/local/opt/postgresql@{version}/bin",
        f"/usr/lib/postgresql/{version}/bin",
    ):
        if cand and (Path(cand) / "initdb").exists():
            return Path(cand)
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Cluster:
    def __init__(self, version: str, bindir: Path):
        self.version, self.bindir = version, bindir
        self.data = tempfile.mkdtemp(prefix=f"m1302pg{version}_")
        self.sock = tempfile.mkdtemp(prefix="p", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self._n = 0
        self.started = False

    def _run(self, exe: str, *args: str, timeout: int = 120) -> None:
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self) -> None:
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        opts = (f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                "-c fsync=off -c max_connections=40 -c shared_buffers=16MB")
        self._run("pg_ctl", "-D", self.data, "-o", opts, "-w", "-t", "60", "-l",
                  os.path.join(self.data, "server.log"), "start")
        self.started = True
        with self.connect("postgres", "postgres", autocommit=True) as c:
            c.execute("CREATE ROLE amjis_app LOGIN")

    def stop(self) -> None:
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db: str, user: str, autocommit: bool = False) -> psycopg.Connection:
        return psycopg.connect(host=self.sock, port=self.port, dbname=db, user=user, autocommit=autocommit,
                               connect_timeout=10)


@pytest.fixture(scope="module", params=VERSIONS)
def cluster(request):
    version = request.param
    bindir = _bindir(version)
    if bindir is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail(f"PostgreSQL {version} binaries not found and REQUIRE_PG_BINARIES=1")
        pytest.skip(f"PostgreSQL {version} binaries not found")
    cl = Cluster(version, bindir)
    try:
        cl.start()
        yield cl
    finally:
        cl.stop()


class Env:
    """A fresh database with public.kala_gochara_windows owned by amjis_app. `with_role` seeds
    role_orchestrator (dormant: NOLOGIN, no memberships) holding table-level UPDATE+DELETE, a
    column-level UPDATE and a SELECT; a control role holds ALL."""

    def __init__(self, cl: Cluster, with_role: bool = True):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} OWNER amjis_app TEMPLATE template0")
            for role in (["role_orchestrator"] if with_role else []) + ["control_role"]:
                c.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}')"
                          f" THEN CREATE ROLE {role} NOLOGIN; END IF; END $$")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            c.execute("ALTER SCHEMA public OWNER TO amjis_app")
        with cl.connect(self.db, "amjis_app", autocommit=True) as c:
            c.execute("CREATE TABLE public.kala_gochara_windows (id int PRIMARY KEY, val text, note text)")
            c.execute("INSERT INTO public.kala_gochara_windows VALUES (1, 'x', 'y')")
            c.execute("GRANT ALL ON public.kala_gochara_windows TO control_role")
            if with_role:
                c.execute("GRANT UPDATE, DELETE, INSERT ON public.kala_gochara_windows TO role_orchestrator")
                c.execute("GRANT UPDATE (note), INSERT (note) ON public.kala_gochara_windows TO role_orchestrator")
                c.execute("GRANT SELECT ON public.kala_gochara_windows TO role_orchestrator")

    def apply(self, sql: str, notices: list[str] | None = None):
        conn = self.cl.connect(self.db, "amjis_app")
        try:
            if notices is not None:
                conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
            conn.execute(sql)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def privs(self) -> dict[str, bool]:
        with self.cl.connect(self.db, "postgres", autocommit=True) as c:
            row = c.execute(
                "SELECT has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE'),"
                "       has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'DELETE'),"
                "       has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'UPDATE'),"
                "       has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'SELECT'),"
                "       has_table_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT'),"
                "       has_any_column_privilege('role_orchestrator', 'public.kala_gochara_windows', 'INSERT'),"
                "       has_table_privilege('control_role', 'public.kala_gochara_windows', 'UPDATE'),"
                "       has_table_privilege('control_role', 'public.kala_gochara_windows', 'DELETE')"
            ).fetchone()
        keys = ("orch_update", "orch_delete", "orch_col_update", "orch_select", "orch_insert", "orch_col_insert", "ctrl_update", "ctrl_delete")
        return dict(zip(keys, row))

    def drop(self) -> None:
        with self.cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


@pytest.fixture()
def env(cluster):
    e = Env(cluster, with_role=True)
    try:
        yield e
    finally:
        e.drop()


def test_apply_twice_revokes_every_write_path_and_keeps_the_rest(env):
    before = env.privs()
    assert before == {"orch_update": True, "orch_delete": True, "orch_col_update": True,
                      "orch_select": True, "orch_insert": True, "orch_col_insert": True,
                      "ctrl_update": True, "ctrl_delete": True}
    env.apply(REAL_SQL)
    after = env.privs()
    assert after["orch_update"] is False
    assert after["orch_delete"] is False
    assert after["orch_col_update"] is False
    assert after["orch_insert"] is False
    assert after["orch_col_insert"] is False
    assert after["orch_select"] is True          # only the WRITE privileges go
    assert after["ctrl_update"] is True and after["ctrl_delete"] is True
    # a SECOND apply is a clean no-op: same end state, no error
    env.apply(REAL_SQL)
    assert env.privs() == after


def test_role_absent_is_a_notice_noop(cluster):
    with cluster.connect("postgres", "postgres", autocommit=True) as c:
        c.execute("DROP ROLE IF EXISTS role_orchestrator")   # roles are cluster-wide; make it genuinely absent
    e = Env(cluster, with_role=False)
    try:
        notices: list[str] = []
        e.apply(REAL_SQL, notices=notices)
        assert any("role_orchestrator does not exist; no-op" in n for n in notices)
        with e.cl.connect(e.db, "postgres", autocommit=True) as c:
            assert c.execute(
                "SELECT has_table_privilege('control_role', 'public.kala_gochara_windows', 'DELETE')"
            ).fetchone()[0] is True
    finally:
        e.drop()


def test_assertion_fires_when_the_revokes_are_stripped(env):
    mutant = re.sub(r"EXECUTE (?:format\()?[^;]*REVOKE[^;]*;", "", REAL_SQL)
    code = "\n".join(l for l in mutant.splitlines() if not l.strip().startswith("--"))
    assert "REVOKE" not in code
    with pytest.raises(Exception, match="1302: role_orchestrator still holds a write privilege"):
        env.apply(mutant)
    assert env.privs()["orch_update"] is True    # rolled back: nothing was revoked
