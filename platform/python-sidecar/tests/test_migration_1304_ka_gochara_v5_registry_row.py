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
                       landed-shape exception — the post-check is load-bearing;
  * prior_state_guard  (Astra review of PR 3101, blocker 1) the row is locked and validated before
                       the write: ONLY the 1243 shape or the exact 1304 shape is accepted; one altered
                       prior value per assigned field, a different scope, a probe / integrity statement
                       / rebuild flag, a half-migrated row — each refuses BY FIELD NAME and changes nothing;
  * health_probe       (blocker 2) must be NULL: an empty string is refused, never preserved or normalised;
  * freshness_trigger  the REAL migration-596 trigger (extracted from its file) marks THIS asset's
                       asset_freshness rows stale on the first apply and nobody else's; a re-run changes
                       nothing and does not fire it;
  * lock               the row lock is taken under the migration's lock_timeout (a held lock fails it fast).
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
    scope text NOT NULL DEFAULT 'per_chart',
    natural_key_partition text,
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

# asset_freshness as migration 596 defines it (the columns the trigger function writes), with the REAL function + trigger text lifted from 596's own file.
FRESHNESS_DDL = """
CREATE TABLE public.asset_freshness (
    asset_id text NOT NULL REFERENCES public.asset_registry(asset_id) ON DELETE CASCADE,
    scope_key text NOT NULL,
    partition_key text NOT NULL,
    freshness_state text NOT NULL CHECK (freshness_state IN ('fresh', 'stale', 'unknown')),
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
    receipt_version text NOT NULL,
    observed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (asset_id, scope_key, partition_key)
)
"""
_M596 = (_REPO / "platform" / "supabase" / "migrations" / "596_nirmana_provenance_receipts.sql").read_text(encoding="utf-8")
TRIGGER_596 = _M596[_M596.index("CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts()"):
                    _M596.index("EXECUTE FUNCTION nirmana_invalidate_registry_receipts();") + len("EXECUTE FUNCTION nirmana_invalidate_registry_receipts();")]

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
            c.execute(FRESHNESS_DDL)
            c.execute(TRIGGER_596)
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


def _set(env, sql, *params):
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute(sql, params)


def _refused(env, before, *needles):
    """The migration refuses (the guard's own 1304 message, every needle in it) and the v5 row is exactly as it was: nothing changed."""
    with pytest.raises(Exception, match="1304: refusing to overwrite the ka_gochara_v5 row") as ei:
        env.apply(REAL_SQL)
    for n in needles:
        assert n in str(ei.value), (n, str(ei.value))
    assert env.row("ka_gochara_v5") == before


@pytest.mark.parametrize("column, value", [
    ("rebuild_on_probe_fail", True), ("integrity_check_sql", "SELECT true"), ("integrity_check_sql", ""),
    ("health_probe", "probe"), ("health_probe", ""), ("asset_kind", "service"), ("asset_type", "service"),
    ("scope", "global"), ("has_writer", False), ("is_active", True),
], ids=lambda v: repr(v))
def test_a_row_with_unexpected_routing_or_scope_is_refused_by_name_and_nothing_changes(env, column, value):
    """Astra blockers 1+2 / Codex round 4 D2: the routing fields and scope are CHECKED before the write (never assigned); an empty health_probe is
    refused too (the dispatch reads '' as None, the teardown does not): NULL or nothing."""
    _set(env, f"UPDATE public.asset_registry SET {column} = %s WHERE asset_id = 'ka_gochara_v5'", value)
    _refused(env, env.row("ka_gochara_v5"), f"shared shape: [{column}]")
    with env.cl.connect(env.db, autocommit=True) as c:        # the routing column itself is byte-for-byte what the operator left
        assert c.execute(f"SELECT {column} FROM public.asset_registry WHERE asset_id = 'ka_gochara_v5'").fetchone()[0] == value


ASSIGNED = [
    ("has_substeps", "has_substeps", "1243"), ("writer_timeout_seconds", "writer_timeout_seconds", "1243"), ("depends_on", "depends_on", "1243"),
    ("count_sql", "count_sql", "1243"), ("target_table", "target_table", "1243"), ("size_sql", "size_sql", "1243"),
    ("target_floor", "target_floor", "shared"), ("estimated_seconds", "estimated_seconds", "shared"),
]
ALTERED = {"has_substeps": True, "writer_timeout_seconds": 7200, "depends_on": ["ga_positions"], "count_sql": "SELECT 1", "target_table": "some_table",
           "size_sql": "SELECT 2", "target_floor": 5, "estimated_seconds": 90}


@pytest.mark.parametrize("column, _label, shape", ASSIGNED, ids=[a[0] for a in ASSIGNED])
def test_an_altered_prior_value_of_any_assigned_column_is_refused_by_name_and_nothing_changes(env, column, _label, shape):
    """Astra blocker 1: the migration used to UPDATE by asset_id alone. Starting from the 1243 shape, ONE altered prior value of an assigned column
    (a value that is neither 1243's nor 1304's) must refuse naming that column, leaving the row as the operator left it."""
    _set(env, f"UPDATE public.asset_registry SET {column} = %s WHERE asset_id = 'ka_gochara_v5'", ALTERED[column])
    where = "shared shape" if shape == "shared" else "1243 shape"
    _refused(env, env.row("ka_gochara_v5"), f"{where}: [{column}]")


@pytest.mark.parametrize("column", [a[0] for a in ASSIGNED if a[2] == "1243"])
def test_an_altered_value_on_a_row_already_in_the_1304_shape_is_refused_too(env, column):
    """The re-run is accepted only for the EXACT 1304 shape: one altered column on top of it refuses naming that column in the 1304 comparison."""
    env.apply(REAL_SQL)
    altered = False if column == "has_substeps" else ALTERED[column]            # True is already the 1304 value
    _set(env, f"UPDATE public.asset_registry SET {column} = %s WHERE asset_id = 'ka_gochara_v5'", altered)
    _refused(env, env.row("ka_gochara_v5"), f"1304 shape: [{column}]")


def test_a_half_migrated_row_is_refused_it_is_neither_shape(env):
    """The timeout already moved to 28800 but nothing else: not the 1243 shape, not the 1304 shape — an operator's partial edit. Refused, untouched."""
    _set(env, "UPDATE public.asset_registry SET writer_timeout_seconds = 28800 WHERE asset_id = 'ka_gochara_v5'")
    _refused(env, env.row("ka_gochara_v5"), "from the 1243 shape: [writer_timeout_seconds]", "from the 1304 shape: [has_substeps")


def test_the_unvalidated_state_other_assets_and_the_control_row_stay_untouched_on_a_refusal(env):
    control_before = env.row("control_asset")
    _set(env, "UPDATE public.asset_registry SET scope = 'global' WHERE asset_id = 'ka_gochara_v5'")
    _refused(env, env.row("ka_gochara_v5"), "scope")
    assert env.row("control_asset") == control_before


def test_a_rerun_on_the_exact_1304_shape_is_accepted_and_changes_nothing(env):
    env.apply(REAL_SQL)
    once = env.row("ka_gochara_v5")
    assert once == V5_1304
    env.apply(REAL_SQL)
    assert env.row("ka_gochara_v5") == once


def test_the_1243_shape_is_accepted_and_the_routing_fields_stay_null(env):
    """health_probe and integrity_check_sql are NULL before and after (1243 inserted NULL; the migration assigns neither), rebuild false, kind/type data."""
    env.apply(REAL_SQL)
    with env.cl.connect(env.db, autocommit=True) as c:
        got = c.execute("SELECT health_probe, integrity_check_sql, rebuild_on_probe_fail, asset_kind, asset_type, scope FROM public.asset_registry "
                        "WHERE asset_id = 'ka_gochara_v5'").fetchone()
    assert got == (None, None, False, "data", "data", "per_chart")


def test_the_migration_assigns_no_routing_column_nor_scope():
    """Static: the UPDATE's SET list names none of the checked-not-written columns."""
    update = REAL_SQL[REAL_SQL.index("UPDATE asset_registry"):REAL_SQL.index("WHERE asset_id = 'ka_gochara_v5'")]
    for col in ("scope", "is_active", "has_writer", "asset_kind", "asset_type", "health_probe", "integrity_check_sql", "rebuild_on_probe_fail"):
        assert not re.search(rf"\b{col}\s*=", update), col
    assert not re.search(r"integrity_check_sql\s*=\s*'", REAL_SQL.replace("--", "\n--")), "no assignment-shaped literal (the N-99 static scan refuses a blank one)"


def _freshness(env):
    with env.cl.connect(env.db, autocommit=True) as c:
        return c.execute("SELECT asset_id, scope_key, partition_key, freshness_state, reasons, receipt_version, observed_at FROM public.asset_freshness "
                         "ORDER BY asset_id, scope_key, partition_key").fetchall()


def _seed_fresh(env):
    with env.cl.connect(env.db, autocommit=True) as c:
        for aid, scope_key, part in (("ka_gochara_v5", "chart-a", "p1"), ("ka_gochara_v5", "__global__", "p2"), ("control_asset", "chart-a", "p1")):
            c.execute("INSERT INTO public.asset_freshness (asset_id, scope_key, partition_key, freshness_state, receipt_version, observed_at) "
                      "VALUES (%s, %s, %s, 'fresh', 'v1', '2026-01-01T00:00:00Z')", (aid, scope_key, part))


def test_the_596_trigger_marks_only_this_assets_freshness_rows_stale_and_a_rerun_does_not_fire_it(env):
    """Follow-up (a): the header used to say 'no other table'. depends_on / target_floor / target_table sit in migration 596's UPDATE OF list, so the
    first apply fires the invalidation for THIS asset (every scope/partition row of ka_gochara_v5) and no other asset's rows; a re-run (no value
    changes: OLD IS NOT DISTINCT FROM NEW) fires nothing."""
    _seed_fresh(env)
    before = {(r[0], r[1], r[2]): r for r in _freshness(env)}
    env.apply(REAL_SQL)
    after = {(r[0], r[1], r[2]): r for r in _freshness(env)}
    assert set(after) == set(before)
    for key, row in after.items():
        if key[0] == "ka_gochara_v5":
            assert row[3] == "stale" and "registry_changed" in row[4], key
            assert row[6] > before[key][6], key                         # observed_at moved
        else:
            assert row == before[key], key                              # the control asset's row is byte-identical
    # restore fresh, re-run: nothing fires, nothing moves
    with env.cl.connect(env.db, autocommit=True) as c:
        c.execute("UPDATE public.asset_freshness SET freshness_state = 'fresh', reasons = '[]'::jsonb WHERE asset_id = 'ka_gochara_v5'")
    mid = _freshness(env)
    env.apply(REAL_SQL)
    assert _freshness(env) == mid


def test_a_refused_migration_does_not_fire_the_trigger(env):
    _seed_fresh(env)
    before = _freshness(env)
    _set(env, "UPDATE public.asset_registry SET scope = 'global' WHERE asset_id = 'ka_gochara_v5'")
    mid = _freshness(env)                                              # the operator's own edit may itself have fired the trigger (scope is in its list)
    with pytest.raises(Exception, match="1304: refusing to overwrite"):
        env.apply(REAL_SQL)
    assert _freshness(env) == mid
    assert before is not None


def test_the_row_lock_is_taken_under_the_lock_timeout(env):
    """The guard's SELECT ... FOR UPDATE waits at most the migration's 5s lock_timeout: a transaction holding the row fails the migration fast, not hang it."""
    import time
    holder = env.cl.connect(env.db)
    try:
        # FOR KEY SHARE blocks a row-lock request FOR UPDATE but NOT a plain non-key UPDATE: only the guard's FOR UPDATE can collide with it
        holder.execute("SELECT 1 FROM public.asset_registry WHERE asset_id = 'ka_gochara_v5' FOR KEY SHARE")
        t0 = time.monotonic()
        with pytest.raises(Exception, match="lock timeout"):
            env.apply(REAL_SQL)
        assert time.monotonic() - t0 < 15
    finally:
        holder.rollback()
        holder.close()
    assert env.row("ka_gochara_v5") == V5_1243


def test_the_scope_is_rechecked_after_the_write(env):
    """Scope is checked before (the guard) AND after (the landed-shape check): a mutant that also assigned scope must be refused by the post-check."""
    mutant = REAL_SQL.replace("         estimated_seconds = NULL\n   WHERE", "         estimated_seconds = NULL, scope = 'global'\n   WHERE")
    assert mutant != REAL_SQL
    with pytest.raises(Exception, match="1304: the ka_gochara_v5 row did not land in the expected small-test shape"):
        env.apply(mutant)
    assert env.row("ka_gochara_v5") == V5_1243
