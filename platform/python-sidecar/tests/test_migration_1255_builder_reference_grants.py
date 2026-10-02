"""Migration 1255 (Suvarna): GRANT SELECT on six L0 reference tables to `data_plane_builder`.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once
per available major version (15 and 17). Nothing here touches any real database. The cluster is built the way
production is shaped: a LOGIN role `amjis_app` OWNS schema public and every table; the build identity
`data_plane_builder` is a non-superuser, NOINHERIT LOGIN role holding only USAGE on schema public; the migration is
applied as the owner inside one transaction, the way platform/scripts/migrate.ts does (BEGIN; <sql>; COMMIT).

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once         the builder's reads FAIL before (InsufficientPrivilege, then InFailedSqlTransaction: the
                       swallowed-error abort the migration exists to prevent) and WORK after; the builder holds
                       SELECT and NO other privilege on all six, by every path; the relacl diff is exactly six
                       `data_plane_builder=r/amjis_app` entries; the held-out tables (bg_prashna_significators,
                       yoga_family_members), prashna_charts, a materialized view and a control table are untouched;
                       lock_timeout is transaction-local (back to 0 after COMMIT).
  * idempotent         a second apply changes nothing and reports six no-ops.
  * guard_missing_table / guard_missing_role / guard_not_a_table   refuse, with the migration's own message.
  * refuses_extra      a pre-existing extra privilege (table-level, column-level, via PUBLIC, via role membership)
                       makes the migration fail and roll back.
  * lock_timeout       a blocked GRANT fails fast with lock_not_available instead of hanging.
Mutation tests then rewrite the real SQL (guard neutered, wrong role, extra privilege, a table dropped from the
list, post-check neutered, grant to PUBLIC, lock_timeout removed or made session-wide) and require every mutant to
produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL 15/17 with the production-shaped role structure;
it does not read production, does not prove the writers' reads (that is the data-plane rehearsal), and the
`REQUIRE_PG_BINARIES=1` environment variable turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import psycopg
import pytest
from psycopg import errors as pgerr

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1255_builder_reference_tables_select_grants.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

SIX = [
    "reference_nakshatra",
    "reference_nakshatra_pada",
    "bg_shashtiamsha_deities",
    "bg_graha_naisargika_friendship",
    "bg_motion_state_thresholds",
    "brahma_vichara_constants",
]
HELD_OUT = ["bg_prashna_significators", "yoga_family_members"]
OTHER_TABLES = ["prashna_charts", "control_table"]
ALL_TABLES = SIX + HELD_OUT + OTHER_TABLES
EXTRA_PRIVS = ["INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]
BUILDER_ENTRY = "data_plane_builder=r/amjis_app"

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")  # must be SHORT (unix socket path limit)
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
        self.data = tempfile.mkdtemp(prefix=f"m1255pg{version}_")
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
            for stmt in (
                "CREATE ROLE amjis_app LOGIN",
                "CREATE ROLE data_plane_builder LOGIN NOINHERIT",
                "CREATE ROLE role_web_serve NOLOGIN",
                "CREATE ROLE extra_path NOLOGIN",
                "CREATE ROLE wrong_role NOLOGIN",
                "CREATE ROLE blocker_role NOLOGIN",
            ):
                c.execute(stmt)

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
    """A fresh production-shaped database inside the disposable cluster."""

    def __init__(self, cl: Cluster):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} OWNER amjis_app TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            c.execute("ALTER SCHEMA public OWNER TO amjis_app")
            c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
            c.execute("GRANT USAGE ON SCHEMA public TO data_plane_builder")
        with cl.connect(self.db, "amjis_app", autocommit=True) as c:
            for t in ALL_TABLES:
                c.execute(f"CREATE TABLE public.{t} (id int PRIMARY KEY, val text)")
                c.execute(f"INSERT INTO public.{t} VALUES (1, 'x')")
                c.execute(f"GRANT SELECT ON public.{t} TO role_web_serve")
            c.execute("CREATE MATERIALIZED VIEW public.mv_control AS SELECT * FROM public.control_table")

    def owner(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "amjis_app")

    def admin(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "postgres", autocommit=True)

    def builder(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "data_plane_builder")

    def acls(self) -> dict[str, list[str]]:
        with self.admin() as c:
            rows = c.execute(
                "SELECT relname, coalesce(relacl::text[], ARRAY[]::text[]) FROM pg_class "
                "WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r','m','v','p')").fetchall()
        return {r[0]: sorted(r[1]) for r in rows}

    def apply(self, sql: str, notices: list[str] | None = None, session_sql: str | None = None):
        """Apply `sql` as the owner in ONE transaction (BEGIN; sql; COMMIT), like migrate.ts. Raises on failure
        (after rolling back). Returns lock_timeout as seen right after COMMIT."""
        conn = self.owner()
        try:
            if notices is not None:
                conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
            if session_sql:
                conn.execute(session_sql)
                conn.commit()
            conn.execute(sql)
            conn.commit()
            return conn.execute("SHOW lock_timeout").fetchone()[0]
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def drop(self) -> None:
        with self.cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


def _privs(env: Env, table: str) -> dict[str, bool]:
    """Effective privileges of the builder on `table`, by every path (direct, PUBLIC, inherited; column-level)."""
    out: dict[str, bool] = {}
    with env.admin() as c:
        rel = f"public.{table}"
        out["SELECT"] = c.execute("SELECT has_table_privilege('data_plane_builder', %s, 'SELECT')", (rel,)).fetchone()[0]
        for p in EXTRA_PRIVS:
            q = "SELECT has_table_privilege('data_plane_builder', %s, %s)"
            v = c.execute(q, (rel, p)).fetchone()[0]
            if p in ("INSERT", "UPDATE", "REFERENCES"):
                v = v or c.execute("SELECT has_any_column_privilege('data_plane_builder', %s, %s)", (rel, p)).fetchone()[0]
            out[p] = v
    return out


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001 - scenarios report any failure as data
        return exc


def _msg(exc: BaseException | None) -> str:
    return "" if exc is None else str(exc)


# --------------------------------------------------------------------------------------------- scenarios

def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        before = env.acls()
        # Precondition (not a mutant-detectable property): the problem the migration solves is real.
        b = env.builder()
        try:
            with pytest.raises(pgerr.InsufficientPrivilege):
                b.execute("SELECT count(*) FROM public.reference_nakshatra")
            with pytest.raises(pgerr.InFailedSqlTransaction):
                b.execute("SELECT 1")
        finally:
            b.close()
        for t in SIX:
            assert _privs(env, t)["SELECT"] is False, f"precondition: builder already reads {t}"

        notices: list[str] = []
        try:
            lock_after = env.apply(sql, notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply failed: {_msg(exc).splitlines()[0]}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after = env.acls()
        for t in SIX:
            p = _privs(env, t)
            if not p["SELECT"]:
                v.append(f"builder lacks SELECT on {t}")
            extra = [k for k in EXTRA_PRIVS if p[k]]
            if extra:
                v.append(f"builder holds extra privilege on {t}: {extra}")
            if sorted(set(before[t]) | {BUILDER_ENTRY}) != after[t]:
                v.append(f"relacl of {t} is not 'before + builder=r': {after[t]}")
        for t in HELD_OUT + OTHER_TABLES + ["mv_control"]:
            if before[t] != after[t]:
                v.append(f"out-of-scope relation {t} was touched: {after[t]}")
        if any(e.startswith("=") for t in SIX for e in after[t]):
            v.append("a PUBLIC grant appeared on a target table")
        b = env.builder()
        try:
            for t in SIX:
                if _try(lambda t=t: (b.execute(f"SELECT count(*) FROM public.{t}"), b.rollback())) is not None:
                    v.append(f"builder cannot read {t} after apply")
                    b.rollback()
            if not isinstance(_try(lambda: b.execute("INSERT INTO public.reference_nakshatra VALUES (2,'y')")),
                              pgerr.InsufficientPrivilege):
                v.append("builder can write reference_nakshatra")
        finally:
            b.close()
        return v
    finally:
        env.drop()


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    env = Env(cl)
    try:
        try:
            env.apply(sql)
            mid = env.acls()
            notices: list[str] = []
            env.apply(sql, notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply failed: {_msg(exc).splitlines()[0]}"]
        v = []
        if env.acls() != mid:
            v.append("second apply changed an ACL")
        noops = [n for n in notices if "already holds SELECT" in n]
        if len(noops) != len(SIX):
            v.append(f"expected {len(SIX)} no-op notices on re-run, got {len(noops)}")
        return v
    finally:
        env.drop()


def sc_guard_missing_table(cl: Cluster, sql: str) -> list[str]:
    v = []
    for t in SIX:
        env = Env(cl)
        try:
            with env.admin() as c:
                c.execute(f"DROP TABLE public.{t}")
            before = env.acls()
            exc = _try(lambda: env.apply(sql))
            if exc is None:
                v.append(f"missing {t}: migration did not refuse")
            elif f"1255: public.{t} does not exist" not in _msg(exc):
                v.append(f"missing {t}: refused with the wrong message: {_msg(exc).splitlines()[0]}")
            if env.acls() != before:
                v.append(f"missing {t}: ACLs changed despite the refusal")
        finally:
            env.drop()
    return v


def sc_guard_not_a_table(cl: Cluster, sql: str) -> list[str]:
    env = Env(cl)
    try:
        with env.admin() as c:
            c.execute("DROP TABLE public.brahma_vichara_constants")
            c.execute("CREATE VIEW public.brahma_vichara_constants AS SELECT 1 AS id")
            c.execute("ALTER VIEW public.brahma_vichara_constants OWNER TO amjis_app")
        exc = _try(lambda: env.apply(sql))
        if exc is None:
            return ["a view in the list was granted instead of refused"]
        if "is not an ordinary table" not in _msg(exc):
            return [f"view refused with the wrong message: {_msg(exc).splitlines()[0]}"]
        return []
    finally:
        env.drop()


def sc_guard_missing_role(cl: Cluster, sql: str) -> list[str]:
    env = Env(cl)
    with env.admin() as c:
        c.execute("ALTER ROLE data_plane_builder RENAME TO data_plane_builder_gone")
    try:
        exc = _try(lambda: env.apply(sql))
        if exc is None:
            return ["missing role: migration did not refuse"]
        if "1255: role data_plane_builder does not exist" not in _msg(exc):
            return [f"missing role: refused with the wrong message: {_msg(exc).splitlines()[0]}"]
        return []
    finally:
        with env.admin() as c:
            c.execute("ALTER ROLE data_plane_builder_gone RENAME TO data_plane_builder")
        env.drop()


EXTRA_CASES = {
    "table-level INSERT": ("GRANT INSERT ON public.reference_nakshatra TO data_plane_builder", "INSERT"),
    "table-level TRUNCATE": ("GRANT TRUNCATE ON public.bg_motion_state_thresholds TO data_plane_builder", "TRUNCATE"),
    "column-level UPDATE": ("GRANT UPDATE (val) ON public.bg_shashtiamsha_deities TO data_plane_builder", "UPDATE"),
    "column-level REFERENCES": ("GRANT REFERENCES (id) ON public.brahma_vichara_constants TO data_plane_builder",
                                "REFERENCES"),
    "via PUBLIC (DELETE)": ("GRANT DELETE ON public.reference_nakshatra_pada TO PUBLIC", "DELETE"),
    "via role membership (TRIGGER)": (None, "TRIGGER"),
}


def sc_refuses_extra(cl: Cluster, sql: str) -> list[str]:
    v = []
    for label, (stmt, priv) in EXTRA_CASES.items():
        env = Env(cl)
        member = stmt is None
        try:
            with env.admin() as c:
                if member:
                    c.execute("ALTER ROLE data_plane_builder INHERIT")
                    c.execute("GRANT TRIGGER ON public.bg_graha_naisargika_friendship TO extra_path")
                    c.execute("GRANT extra_path TO data_plane_builder")
                else:
                    c.execute(stmt)
            before = env.acls()
            exc = _try(lambda: env.apply(sql))
            if exc is None:
                v.append(f"{label}: migration did not refuse")
            elif "holds more than SELECT" not in _msg(exc) or priv not in _msg(exc):
                v.append(f"{label}: refused with the wrong message: {_msg(exc).splitlines()[0]}")
            if env.acls() != before:
                v.append(f"{label}: ACLs changed despite the refusal (no rollback)")
        finally:
            if member:
                with env.admin() as c:
                    c.execute("REVOKE extra_path FROM data_plane_builder")
                    c.execute("ALTER ROLE data_plane_builder NOINHERIT")
            env.drop()
    return v


def sc_lock_timeout(cl: Cluster, sql: str) -> list[str]:
    """Another transaction holds an uncommitted ACL change on the same pg_class row: our GRANT must wait, then
    fail with lock_not_available at ~5s (not hang). The 9s statement_timeout is only a net so a mutant that
    lost the lock_timeout fails this scenario instead of hanging the suite."""
    env = Env(cl)
    blocker = env.cl.connect(env.db, "amjis_app")
    try:
        blocker.execute("GRANT SELECT ON public.bg_motion_state_thresholds TO blocker_role")  # held, uncommitted
        t0 = time.monotonic()
        exc = _try(lambda: env.apply(sql, session_sql="SET statement_timeout = '9s'"))
        dt = time.monotonic() - t0
        if exc is None:
            return ["the grant did not wait for the blocker (expected lock_not_available)"]
        if not isinstance(exc, pgerr.LockNotAvailable):
            return [f"expected lock_not_available, got {type(exc).__name__} after {dt:.1f}s"]
        if not 4.0 <= dt <= 8.0:
            return [f"lock timeout fired after {dt:.1f}s, expected about 5s"]
        return []
    finally:
        blocker.rollback()
        blocker.close()
        env.drop()


FAST = [sc_apply_once, sc_idempotent, sc_guard_missing_table, sc_guard_not_a_table, sc_guard_missing_role,
        sc_refuses_extra]
ALL = FAST + [sc_lock_timeout]


def run(cl: Cluster, sql: str, scenarios) -> list[str]:
    out: list[str] = []
    for sc in scenarios:
        out += [f"{sc.__name__}: {x}" for x in sc(cl, sql)]
    return out


# --------------------------------------------------------------------------------------------- real file

@pytest.mark.parametrize("scenario", ALL, ids=lambda s: s.__name__)
def test_real_migration_has_no_violations(cluster, scenario):
    assert scenario(cluster, REAL_SQL) == []


def test_real_migration_file_shape():
    code = "\n".join(l for l in REAL_SQL.splitlines() if not l.strip().startswith("--"))
    assert code.lstrip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", code, re.M | re.I)
    assert not re.search(r"\bREVOKE\b|WITH GRANT OPTION|SECURITY DEFINER", code, re.I)
    assert "SERVING EFFECT AT APPLY: none (no registry/freshness/trigger touched)" in REAL_SQL
    assert "never REVOKE" in REAL_SQL


# --------------------------------------------------------------------------------------------- mutations

def _sub(pattern: str, repl: str, flags: int = 0):
    def f(sql: str) -> str:
        return re.sub(pattern, repl, sql, count=1, flags=flags)
    return f


def _drop_table(name: str):
    def f(sql: str) -> str:
        m = re.search(r"tables text\[\] := ARRAY\[(.*?)\];", sql, re.S)
        names = re.findall(r"'([a-z_]+)'", m.group(1))
        assert name in names
        body = ",\n        ".join(f"'{n}'" for n in names if n != name)
        return sql[:m.start(1)] + "\n        " + body + "\n    " + sql[m.end(1):]
    return f


MUTANTS = {
    "guard neutered: missing table": (_sub(r"IF rel IS NULL THEN", "IF false THEN"), FAST),
    "guard neutered: not an ordinary table": (_sub(r"IF kind NOT IN \('r', 'p'\) THEN", "IF false THEN"), FAST),
    "guard neutered: missing role": (_sub(r"IF NOT EXISTS \(SELECT 1 FROM pg_roles[^)]*\) THEN", "IF false THEN"), FAST),
    "grant to the wrong role": (_sub(r"TO data_plane_builder'", "TO wrong_role'"), FAST),
    "grant to PUBLIC": (_sub(r"TO data_plane_builder'", "TO PUBLIC'"), FAST),
    "extra privilege granted (INSERT)": (_sub(r"GRANT SELECT ON TABLE", "GRANT SELECT, INSERT ON TABLE"), FAST),
    "extra privilege granted (ALL)": (_sub(r"GRANT SELECT ON TABLE", "GRANT ALL ON TABLE"), FAST),
    "post-check neutered (extra privilege)": (_sub(r"IF extra IS NOT NULL THEN", "IF false THEN"), FAST),
    "post-check neutered (SELECT) + wrong role": (
        lambda s: _sub(r"TO data_plane_builder'", "TO wrong_role'")(
            _sub(r"IF NOT has_table_privilege\('data_plane_builder', rel, 'SELECT'\) THEN", "IF false THEN")(s)),
        FAST),
    "lock_timeout removed": (_sub(r"^SET LOCAL lock_timeout = '5s';", "", re.M), [sc_lock_timeout]),
    "lock_timeout made session-wide (SET, not SET LOCAL)": (_sub(r"^SET LOCAL lock_timeout", "SET lock_timeout", re.M),
                                                            [sc_apply_once]),
}
for _t in SIX:
    MUTANTS[f"table dropped from the list: {_t}"] = (_drop_table(_t), [sc_apply_once])


@pytest.mark.parametrize("name", list(MUTANTS))
def test_every_mutant_is_caught(cluster, name):
    mutate, scenarios = MUTANTS[name]
    mutated = mutate(REAL_SQL)
    assert mutated != REAL_SQL, "the mutation did not change the file (a no-op mutant proves nothing)"
    violations = run(cluster, mutated, scenarios)
    assert violations, f"MUTANT SURVIVED: {name}"
