"""Migration 1304 (Pravāha C41-P2): UPDATE ONLY the asset_registry row ka_gochara_v5 into the
steward-dispatched SMALL TEST shape (has_substeps=true, writer_timeout_seconds=28800,
depends_on=[ga_positions,ga_dashas], the ka_gochara_eval_window truth counter, target_floor=0,
estimated_seconds=NULL), leaving is_active=false and every other row untouched.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at
the end), once per available major version (15 and 17). Nothing here touches any real database.
The migration is applied as the table owner inside one transaction, the way
platform/scripts/migrate.ts does (BEGIN; <sql>; COMMIT).

What it proves:
  * apply_twice        from the 1243 v5 shape (has_substeps=false, timeout 600, depends_on {},
                       the kala_gochara_windows counter): after ONE apply every new value has
                       landed, is_active is still false and the control row is byte-identical;
                       a SECOND apply still updates exactly that one row to the same values
                       (ROW_COUNT=1, the xmin nothing-else-touched check passes) — idempotent;
  * row_absent         with no ka_gochara_v5 row the migration RAISES its own 1304 exception
                       (ROW_COUNT 0) and rolls back;
  * assertion_fires    a mutant writing the WRONG depends_on must RAISE the migration's own
                       landed-shape exception — the post-check is load-bearing.
"""
from __future__ import annotations

import re
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import psycopg
import pytest

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1304_ka_gochara_v5_registry_row_small_test.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")
VERSIONS = ["15", "17"]

DDL = """
CREATE TABLE public.asset_registry (
    asset_id text PRIMARY KEY,
    is_active boolean NOT NULL,
    has_writer boolean NOT NULL,
    has_substeps boolean NOT NULL,
    writer_timeout_seconds int,
    depends_on text[] NOT NULL,
    count_sql text,
    target_table text,
    size_sql text,
    target_floor int,
    estimated_seconds int,
    asset_kind text NOT NULL DEFAULT 'data',
    asset_type text NOT NULL DEFAULT 'data',
    health_probe text,
    integrity_check_sql text,
    rebuild_on_probe_fail boolean NOT NULL DEFAULT false
)
"""

# The v5 row exactly as migration 1243 lands it (the pre-1304 shape).
V5_1243 = dict(
    is_active=False, has_writer=True, has_substeps=False, writer_timeout_seconds=600,
    depends_on=[], target_table="kala_gochara_windows",
    count_sql="SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='5.0'",
    size_sql="SELECT pg_total_relation_size('kala_gochara_windows')",
    target_floor=0, estimated_seconds=None,
)
# The shape migration 1304 must land (kept in sync with the v_count_sql/v_size_sql constants).
V5_1304 = dict(
    is_active=False, has_writer=True, has_substeps=True, writer_timeout_seconds=28800,
    depends_on=["ga_positions", "ga_dashas"], target_table="ka_gochara_eval_window",
    count_sql="SELECT COUNT(*) FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation='5.0'",
    size_sql="SELECT pg_total_relation_size('ka_gochara_eval_window')",
    target_floor=0, estimated_seconds=None,
)
CONTROL = dict(
    is_active=True, has_writer=True, has_substeps=True, writer_timeout_seconds=3600,
    depends_on=["ga_positions"], target_table="some_other_table",
    count_sql="SELECT COUNT(*) FROM some_other_table WHERE chart_id=$1",
    size_sql="SELECT pg_total_relation_size('some_other_table')",
    target_floor=5, estimated_seconds=42,
)

COLS = ("is_active", "has_writer", "has_substeps", "writer_timeout_seconds", "depends_on",
        "count_sql", "target_table", "size_sql", "target_floor", "estimated_seconds")


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
        self.data = tempfile.mkdtemp(prefix=f"m1304pg{version}_")
        self.sock = tempfile.mkdtemp(prefix="p", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self._n = 0
        self.started = False

    def _run(self, exe: str, *args: str, timeout: int = 120) -> None:
        env = dict(os.environ, LC_ALL="C")  # postmaster refuses the host's multithreaded locale
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=timeout, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self) -> None:
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        opts = (f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                "-c fsync=off -c max_connections=40 -c shared_buffers=16MB")
        self._run("pg_ctl", "-D", self.data, "-o", opts, "-w", "-t", "60", "-l",
                  os.path.join(self.data, "server.log"), "start")
        self.started = True

    def stop(self) -> None:
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db: str, autocommit: bool = False) -> psycopg.Connection:
        return psycopg.connect(host=self.sock, port=self.port, dbname=db, user="postgres",
                               autocommit=autocommit, connect_timeout=10)


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
    """A fresh database with a minimal asset_registry: the ka_gochara_v5 row in its 1243 shape
    (unless with_v5=False) plus one control row the migration must never touch."""

    def __init__(self, cl: Cluster, with_v5: bool = True):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} TEMPLATE template0")
        with cl.connect(self.db, autocommit=True) as c:
            c.execute(DDL)
            self._insert(c, "control_asset", CONTROL)
            if with_v5:
                self._insert(c, "ka_gochara_v5", V5_1243)

    @staticmethod
    def _insert(c, asset_id: str, row: dict) -> None:
        c.execute(
            f"INSERT INTO public.asset_registry (asset_id, {', '.join(COLS)}) "
            f"VALUES (%s, {', '.join(['%s'] * len(COLS))})",
            (asset_id, *[row[k] for k in COLS]),
        )

    def row(self, asset_id: str) -> dict:
        with self.cl.connect(self.db, autocommit=True) as c:
            r = c.execute(
                f"SELECT {', '.join(COLS)} FROM public.asset_registry WHERE asset_id = %s",
                (asset_id,),
            ).fetchone()
        assert r is not None, asset_id
        return dict(zip(COLS, r))

    def apply(self, sql: str) -> None:
        conn = self.cl.connect(self.db)
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def drop(self) -> None:
        with self.cl.connect("postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


@pytest.fixture()
def env(cluster):
    e = Env(cluster)
    try:
        yield e
    finally:
        e.drop()


def test_apply_twice_lands_the_small_test_shape_and_touches_nothing_else(env):
    assert env.row("ka_gochara_v5") == V5_1243
    control_before = env.row("control_asset")
    env.apply(REAL_SQL)
    assert env.row("ka_gochara_v5") == V5_1304
    assert env.row("control_asset") == control_before
    # a SECOND apply: the UPDATE still matches exactly that one row (ROW_COUNT=1),
    # writes the same values, and both post-checks pass — a clean no-op end state.
    env.apply(REAL_SQL)
    assert env.row("ka_gochara_v5") == V5_1304
    assert env.row("control_asset") == control_before


def test_a_missing_v5_row_raises_and_rolls_back(cluster):
    e = Env(cluster, with_v5=False)
    try:
        with pytest.raises(Exception, match="1304: expected to update exactly one asset_registry row"):
            e.apply(REAL_SQL)
        assert e.row("control_asset") == CONTROL          # rolled back: nothing landed
        with e.cl.connect(e.db, autocommit=True) as c:
            assert c.execute("SELECT count(*) FROM public.asset_registry").fetchone()[0] == 1
    finally:
        e.drop()


def test_assertion_fires_when_the_landed_shape_is_wrong(env):
    mutant = REAL_SQL.replace(
        "depends_on = ARRAY['ga_positions','ga_dashas']::text[],",
        "depends_on = ARRAY['ga_positions']::text[],",
    )
    assert mutant != REAL_SQL
    with pytest.raises(Exception, match="1304: the ka_gochara_v5 row did not land in the expected small-test shape"):
        env.apply(mutant)
    assert env.row("ka_gochara_v5") == V5_1243            # rolled back: the 1243 shape survives


@pytest.mark.parametrize("column, value", [
    ("rebuild_on_probe_fail", True), ("integrity_check_sql", "SELECT true"), ("health_probe", "probe"),
    ("asset_kind", "service"), ("asset_type", "service"),
], ids=lambda v: str(v))
def test_a_row_with_non_data_routing_is_refused_by_the_landed_shape_check(env, column, value):
    """Codex round 4 D2 / steward DB4: the routing fields the runner reads are CHECKED by the migration (never written); a row an operator left
    with a probe, an integrity check, rebuild_on_probe_fail or service routing must not be declared ready."""
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute(f"UPDATE public.asset_registry SET {column} = %s WHERE asset_id = 'ka_gochara_v5'", (value,))
    with pytest.raises(Exception, match="1304: the ka_gochara_v5 row did not land in the expected small-test shape"):
        env.apply(REAL_SQL)
    assert env.row("ka_gochara_v5") == V5_1243                              # rolled back


def test_an_empty_string_probe_reads_as_null_and_does_not_block_the_deploy(env):
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute("UPDATE public.asset_registry SET health_probe = '' WHERE asset_id = 'ka_gochara_v5'")
    env.apply(REAL_SQL)
    assert env.row("ka_gochara_v5") == V5_1304


def test_an_empty_string_integrity_statement_is_refused_it_must_be_null_and_the_migration_never_assigns_it(env):
    """Steward CHAIN-3101-RULING-FINAL: integrity_check_sql must be NULL for the row (NULL is skipped on the run path); the migration neither assigns nor tolerates a blank."""
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute("UPDATE public.asset_registry SET integrity_check_sql = '' WHERE asset_id = 'ka_gochara_v5'")
    with pytest.raises(Exception, match="1304: the ka_gochara_v5 row did not land in the expected small-test shape"):
        env.apply(REAL_SQL)
    assert not re.search(r"integrity_check_sql\s*=\s*'", REAL_SQL.replace("--", "\n--")), "no assignment-shaped literal (the N-99 static scan refuses a blank one)"


def test_the_migration_never_writes_the_routing_fields(env):
    """CHECKED, NOT WRITTEN: the apply leaves a harmless difference such as an empty-string health_probe byte-for-byte as it was."""
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute("UPDATE public.asset_registry SET health_probe = '' WHERE asset_id = 'ka_gochara_v5'")
    env.apply(REAL_SQL)
    with env.cl.connect(env.db, autocommit=True) as c:
        assert c.execute("SELECT health_probe FROM public.asset_registry WHERE asset_id = 'ka_gochara_v5'").fetchone()[0] == ""
