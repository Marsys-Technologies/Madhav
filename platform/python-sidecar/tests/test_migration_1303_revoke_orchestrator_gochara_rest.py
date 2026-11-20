"""Migration 1303 (Pravāha C40): REVOKE role_orchestrator's INSERT/UPDATE/DELETE (table- and
column-level) on the five remaining legacy Gochara tables, and USAGE/UPDATE on their OWNED id
sequences where granted; NOTICE no-op for a missing table or an absent role; raising post-checks.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at
the end), once per available major version (15 and 17). Nothing here touches any real database.
The cluster is shaped like production: a LOGIN role `amjis_app` OWNS schema public and the tables;
the migration is applied as the owner inside one transaction, the way platform/scripts/migrate.ts
does (BEGIN; <sql>; COMMIT).

What it proves:
  * apply_twice        with role_orchestrator holding table-level INSERT/UPDATE/DELETE on all five
                       tables, a column-level grant, SELECT, and USAGE/UPDATE on the two serial
                       sequences: after ONE apply no effective write path remains on any table or
                       sequence, SELECT everywhere and the control role's grants survive, and a
                       SECOND apply is a clean no-op;
  * role_absent        where pg_roles has no role_orchestrator the whole migration is a NOTICE no-op;
  * table_absent       a missing legacy table is a NOTICE no-op (skipped), the rest still revokes;
  * assertion_fires    a mutant with the REVOKE statements stripped must RAISE the migration's own
                       1303 exception and roll back — the post-check is load-bearing.
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
MIGRATION = _REPO / "platform" / "migrations" / "1303_revoke_role_orchestrator_gochara_rest.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")
VERSIONS = ["15", "17"]

TABLES = (
    "kala_gochara_authority",
    "kala_gochara_v2_build_state",
    "kala_gochara_windows__ssv_20260728c",
    "kala_gochara_windows_archive_20260805",
    "kala_gochara_windows_v2",
)
SERIAL_TABLES = ("kala_gochara_authority", "kala_gochara_windows_v2")
SEQUENCES = tuple(f"{t}_id_seq" for t in SERIAL_TABLES)


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
        self.data = tempfile.mkdtemp(prefix=f"m1303pg{version}_")
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
    """A fresh database with the five legacy-shaped tables owned by amjis_app (two of them serial,
    so two owned id sequences exist). `with_role` seeds role_orchestrator (dormant: NOLOGIN, no
    memberships) holding table-level INSERT/UPDATE/DELETE on all five, a column-level UPDATE/INSERT,
    SELECT on all five, and USAGE/UPDATE/SELECT on the two sequences; a control role holds ALL."""

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
            for t in TABLES:
                id_col = "id serial PRIMARY KEY" if t in SERIAL_TABLES else "id int PRIMARY KEY"
                c.execute(f"CREATE TABLE public.{t} ({id_col}, val text, note text)")
            for t in TABLES:
                c.execute(f"GRANT ALL ON public.{t} TO control_role")
            if with_role:
                for t in TABLES:
                    c.execute(f"GRANT INSERT, UPDATE, DELETE ON public.{t} TO role_orchestrator")
                    c.execute(f"GRANT SELECT ON public.{t} TO role_orchestrator")
                c.execute("GRANT UPDATE (note), INSERT (note) ON public.kala_gochara_authority TO role_orchestrator")
                for s in SEQUENCES:
                    c.execute(f"GRANT USAGE, UPDATE, SELECT ON SEQUENCE public.{s} TO role_orchestrator")

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
        out: dict[str, bool] = {}
        with self.cl.connect(self.db, "postgres", autocommit=True) as c:
            for t in TABLES:
                row = c.execute(
                    f"SELECT has_table_privilege('role_orchestrator', 'public.{t}', 'INSERT'),"
                    f"       has_table_privilege('role_orchestrator', 'public.{t}', 'UPDATE'),"
                    f"       has_table_privilege('role_orchestrator', 'public.{t}', 'DELETE'),"
                    f"       has_any_column_privilege('role_orchestrator', 'public.{t}', 'UPDATE'),"
                    f"       has_table_privilege('role_orchestrator', 'public.{t}', 'SELECT')"
                ).fetchone()
                for key, val in zip(("insert", "update", "delete", "col_update", "select"), row):
                    out[f"{t}.{key}"] = val
            for s in SEQUENCES:
                row = c.execute(
                    f"SELECT has_sequence_privilege('role_orchestrator', 'public.{s}', 'USAGE'),"
                    f"       has_sequence_privilege('role_orchestrator', 'public.{s}', 'UPDATE'),"
                    f"       has_sequence_privilege('role_orchestrator', 'public.{s}', 'SELECT')"
                ).fetchone()
                for key, val in zip(("usage", "update", "select"), row):
                    out[f"{s}.{key}"] = val
            out["ctrl.update"] = c.execute(
                "SELECT has_table_privilege('control_role', 'public.kala_gochara_windows_v2', 'UPDATE')"
            ).fetchone()[0]
        return out

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
    assert all(before[f"{t}.insert"] and before[f"{t}.update"] and before[f"{t}.delete"]
               for t in TABLES)
    assert all(before[f"{s}.usage"] and before[f"{s}.update"] for s in SEQUENCES)
    env.apply(REAL_SQL)
    after = env.privs()
    for t in TABLES:
        assert after[f"{t}.insert"] is False
        assert after[f"{t}.update"] is False
        assert after[f"{t}.delete"] is False
        assert after[f"{t}.col_update"] is False
        assert after[f"{t}.select"] is True          # only the WRITE privileges go
    for s in SEQUENCES:
        assert after[f"{s}.usage"] is False
        assert after[f"{s}.update"] is False
        assert after[f"{s}.select"] is True
    assert after["ctrl.update"] is True
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
                "SELECT has_table_privilege('control_role', 'public.kala_gochara_windows_v2', 'DELETE')"
            ).fetchone()[0] is True
    finally:
        e.drop()


def test_a_missing_table_is_a_notice_noop_and_the_rest_still_revokes(cluster):
    e = Env(cluster, with_role=True)
    try:
        with e.cl.connect(e.db, "amjis_app", autocommit=True) as c:
            c.execute("DROP TABLE public.kala_gochara_windows_archive_20260805")
        notices: list[str] = []
        e.apply(REAL_SQL, notices=notices)
        assert any("public.kala_gochara_windows_archive_20260805 does not exist; skipping it" in n
                   for n in notices)
        with e.cl.connect(e.db, "postgres", autocommit=True) as c:
            assert c.execute(
                "SELECT has_table_privilege('role_orchestrator', 'public.kala_gochara_windows_v2', 'UPDATE')"
            ).fetchone()[0] is False
    finally:
        e.drop()


def test_assertion_fires_when_the_revokes_are_stripped(env):
    mutant = re.sub(r"EXECUTE (?:format\()?[^;]*REVOKE[^;]*;", "", REAL_SQL)
    code = "\n".join(l for l in mutant.splitlines() if not l.strip().startswith("--"))
    assert "REVOKE" not in code
    with pytest.raises(Exception, match="1303: role_orchestrator still holds"):
        env.apply(mutant)
    assert env.privs()["kala_gochara_authority.update"] is True    # rolled back: nothing was revoked
