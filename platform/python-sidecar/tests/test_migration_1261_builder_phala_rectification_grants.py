"""Migration 1261 (Suvarna, SS ruling N-99, Q-L4-04): GRANT SELECT, INSERT, DELETE on phala_rectification and
phala_rectification_best to `data_plane_builder`, nothing wider. HELD: own draft PR, merges only after S-L1 and only on
SS's review.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end). Nothing here
touches any real database. The cluster is built the way production is shaped: a LOGIN role `amjis_app` OWNS schema public and
every table; the build identity `data_plane_builder` is a non-superuser, NOINHERIT LOGIN role holding only USAGE on schema
public (and, like production, SELECT on `charts` is NOT given to it in the fixture, to prove the FK checks need nothing of
the builder); the migration is applied as the owner inside one transaction, the way platform/scripts/migrate.ts does.

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once         before: the builder's writer statements FAIL (InsufficientPrivilege); after: the writer's exact
                       statement sequence (DELETE best, DELETE rect, INSERT rect RETURNING id, INSERT best with FKs) WORKS as the
                       builder; UPDATE / TRUNCATE / REFERENCES / TRIGGER stay denied; effective privileges are exactly
                       SELECT+INSERT+DELETE on both tables; the relacl diff over all relations is exactly two entries
                       `data_plane_builder=ard/amjis_app` (grantor amjis_app); sibling tables and a control table untouched;
                       lock_timeout is transaction-local; no sequence was needed or touched.
  * idempotent         a second apply changes nothing and reports six no-ops.
  * partial            a privilege already held is skipped.
  * guards             missing role, missing table, not-an-ordinary-table, and a migration user that is not the owner
                       (a GRANT by it would be a silent no-op) all refuse with the migration's own message and grant nothing.
  * refuses_extra      a pre-existing extra privilege (table-level UPDATE, column-level UPDATE, via PUBLIC, via an inherited
                       role) makes the migration fail and roll back.
  * lock_timeout       a blocked GRANT fails fast with lock_not_available instead of hanging.
Mutation tests then rewrite the real SQL (each guard neutered, an extra privilege, a dropped privilege, a dropped table,
grant to PUBLIC, post-check neutered, lock_timeout removed or made session-wide) and require every mutant to be caught.

HONEST LIMITS: stock PostgreSQL with the production-shaped role structure; it does not read production and does not prove the
writer's other reads (life_events is NOT granted by this migration; see its header). `REQUIRE_PG_BINARIES=1` turns a missing
binary from a skip into a failure.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1261_builder_phala_rectification_dml_grants.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")
CODE = "\n".join(l for l in REAL_SQL.splitlines() if not l.lstrip().startswith("--"))
FLAT = re.sub(r"\s+", " ", re.sub(r"^--", " ", REAL_SQL, flags=re.M))

TABLES = ["phala_rectification", "phala_rectification_best"]
SIBLINGS = ["phala_anchors", "phala_phaladesa", "control_table", "charts"]
GRANTED = ["SELECT", "INSERT", "DELETE"]
DENIED = ["UPDATE", "TRUNCATE", "REFERENCES", "TRIGGER"]
ENTRY = "data_plane_builder=ard/amjis_app"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


# -- static --------------------------------------------------------------------------

def test_static_one_table_list_one_privilege_list_exactly_the_ruled_set():
    t = re.findall(r"tables text\[\] := ARRAY\[(.*?)\];", CODE, re.S)
    p = re.findall(r"privs text\[\] := ARRAY\[(.*?)\];", CODE, re.S)
    assert len(t) == 1 and len(p) == 1
    assert re.findall(r"'([a-z_]+)'", t[0]) == TABLES
    assert re.findall(r"'([A-Z]+)'", p[0]) == GRANTED
    for name in TABLES:
        assert CODE.count(f"'{name}'") == 1, "table names appear only in the list"


def test_static_grants_only_no_ddl_no_data_no_revoke_no_grant_option_no_sequence_no_public():
    assert CODE.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert CODE.count("EXECUTE format('GRANT") == 1 and "GRANT %s ON TABLE %s TO data_plane_builder" in CODE
    assert not re.search(r"\bREVOKE\b|WITH GRANT OPTION|SECURITY DEFINER|\bINSERT INTO\b|\bUPDATE\s+\w+\s+SET|\bDELETE FROM\b|\bSEQUENCE\b", CODE, re.I)
    assert not re.search(r"^\s*(CREATE|ALTER|DROP|TRUNCATE)\b", CODE, re.I | re.M)
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", CODE, re.M)
    assert not re.search(r"TO (PUBLIC|role_)", CODE)
    for held_out in ("life_events", "chart_fact_identity", "role_sidecar"):
        assert held_out not in CODE


def test_static_guards_and_postchecks_present():
    for needle in ("rolname = 'data_plane_builder'", "1261: role data_plane_builder does not exist", "does not exist",
                   "kind NOT IN ('r', 'p')", "pg_has_role(current_user, owner, 'USAGE')", "a silent no-op",
                   "has_table_privilege('data_plane_builder', rel, p)", "has_any_column_privilege('data_plane_builder', rel, x)",
                   "ARRAY['UPDATE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']", "holds more than SELECT, INSERT, DELETE", "lacks % on"):
        assert needle in CODE, needle


def test_static_header_states_the_facts():
    for needle in ("HELD", "AFTER S-L1", "on SS's review", "WHAT THE WRITER ACTUALLY NEEDS", "RETURNING id", "SEQUENCES: none",
                   "gen_random_uuid()", "WHO ISSUES THE GRANT", "amjis_app", "data_plane_builder=ard/amjis_app", "SIDE EFFECTS TO DECIDE",
                   "Migration 1073", "Strategy 6.2", "ka_kshetra", "uncertainty.py:185-191", "NOT SUFFICIENT BY ITSELF", "life_events",
                   "InFailedSqlTransaction", "SERVING EFFECT AT APPLY: none", "nirmana_registry_receipt_invalidation", "POST-CHECK",
                   "NOINHERIT", "MAINTAIN", "LOCK TIMEOUT", "NOT DONE HERE", "never REVOKE", "VERIFICATION AFTER APPLY",
                   "Q-L4-04", "TI-L4-44", "retrieval_census_ro", "nirmana_evidence_ingress_writer", "UPDATE on phala_phaladesa"):
        assert needle in FLAT, f"header no longer states: {needle}"


def test_static_number_and_name():
    assert MIGRATION.name.startswith("1261_") and len(list(MIGRATION.parent.glob("1261_*.sql"))) == 1


# -- live ----------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


class Cluster:
    def __init__(self, bindir: Path):
        self.bindir = bindir
        self.data = tempfile.mkdtemp(prefix="m1261pg_")
        self.sock = tempfile.mkdtemp(prefix="p61", dir="/tmp")  # must be SHORT (unix socket path limit)
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self._n = 0
        self.started = False

    def _run(self, exe: str, *args: str) -> None:
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=120, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self, psycopg) -> None:
        self.psycopg = psycopg
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        opts = (f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                "-c fsync=off -c max_connections=40 -c shared_buffers=16MB")
        self._run("pg_ctl", "-D", self.data, "-o", opts, "-w", "-t", "60", "-l", os.path.join(self.data, "server.log"), "start")
        self.started = True
        with self.connect("postgres", "postgres", autocommit=True) as c:
            for stmt in ("CREATE ROLE amjis_app LOGIN", "CREATE ROLE data_plane_builder LOGIN NOINHERIT",
                         "CREATE ROLE role_orchestrator NOLOGIN", "CREATE ROLE role_web_serve NOLOGIN",
                         "CREATE ROLE extra_path NOLOGIN", "CREATE ROLE other_owner LOGIN", "CREATE ROLE blocker_role NOLOGIN"):
                c.execute(stmt)

    def stop(self) -> None:
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db: str, user: str, autocommit: bool = False):
        return self.psycopg.connect(host=self.sock, port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10)


@pytest.fixture(scope="module")
def cluster():
    psycopg = pytest.importorskip("psycopg")
    bindir = _find_pg_bin()
    if bindir is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("PostgreSQL binaries not found and REQUIRE_PG_BINARIES=1")
        pytest.skip("PostgreSQL binaries not found")
    cl = Cluster(bindir)
    try:
        cl.start(psycopg)
        yield cl
    finally:
        cl.stop()


# Production-shaped DDL (constraint and default shapes read from production 2026-10-03; columns reduced to what the writer names).
_DDL = """
CREATE TABLE public.charts (id uuid PRIMARY KEY);
CREATE TABLE public.phala_rectification (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id uuid NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
    candidate_birth_utc timestamptz, offset_minutes int, ayanamsha_id text, lagna_sign text, lagna_longitude_deg float8,
    lagna_degree_in_sign float8, lel_fit_score float8, lel_events_matched int, lel_events_tested int,
    lagna_stable boolean DEFAULT true, scored_at timestamptz DEFAULT now());
CREATE TABLE public.phala_rectification_best (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id uuid NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
    best_candidate_id uuid REFERENCES public.phala_rectification(id),
    offset_minutes int, auto_action text DEFAULT 'stage_for_review' CHECK (auto_action = 'stage_for_review'),
    scored_at timestamptz DEFAULT now(), native_adopted boolean DEFAULT false);
CREATE TABLE public.phala_anchors (id int PRIMARY KEY, val text);
CREATE TABLE public.phala_phaladesa (id int PRIMARY KEY, val text);
CREATE TABLE public.control_table (id int PRIMARY KEY, val text);
"""
_TABLES_ALL = TABLES + SIBLINGS


class Env:
    """A fresh production-shaped database inside the disposable cluster."""

    def __init__(self, cl: Cluster, *, skip_ddl: bool = False):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} OWNER amjis_app TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            c.execute("ALTER SCHEMA public OWNER TO amjis_app")
            c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
            c.execute("GRANT USAGE ON SCHEMA public TO data_plane_builder, other_owner")
        if not skip_ddl:
            with cl.connect(self.db, "amjis_app", autocommit=True) as c:
                c.execute(_DDL)
                for t in _TABLES_ALL:
                    c.execute(f"GRANT SELECT ON public.{t} TO role_web_serve")
                for t in TABLES:
                    c.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON public.{t} TO role_orchestrator")
                c.execute(f"INSERT INTO public.charts VALUES ('{CHART}')")

    def owner(self):
        return self.cl.connect(self.db, "amjis_app")

    def admin(self):
        return self.cl.connect(self.db, "postgres", autocommit=True)

    def builder(self):
        return self.cl.connect(self.db, "data_plane_builder")

    def acls(self) -> dict[str, list[str]]:
        with self.admin() as c:
            rows = c.execute("SELECT relname, coalesce(relacl::text[], ARRAY[]::text[]) FROM pg_class WHERE relnamespace = 'public'::regnamespace "
                             "AND relkind IN ('r','m','v','p','S')").fetchall()
        return {r[0]: sorted(r[1]) for r in rows}

    def apply(self, sql: str, notices: list[str] | None = None, user: str = "amjis_app", session_sql: str | None = None):
        """Apply `sql` as `user` in ONE transaction (BEGIN; sql; COMMIT) like migrate.ts. Returns lock_timeout right after COMMIT."""
        conn = self.cl.connect(self.db, user)
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


def _privs(env: Env, table: str, role: str = "data_plane_builder") -> dict[str, bool]:
    """Effective privileges of `role` on `table` (direct, PUBLIC, inherited; column-level UPDATE/REFERENCES)."""
    out: dict[str, bool] = {}
    with env.admin() as c:
        rel = f"public.{table}"
        for p in GRANTED + DENIED:
            v = c.execute("SELECT has_table_privilege(%s, %s, %s)", (role, rel, p)).fetchone()[0]
            if p in ("UPDATE", "REFERENCES"):
                v = v or c.execute("SELECT has_any_column_privilege(%s, %s, %s)", (role, rel, p)).fetchone()[0]
            out[p] = v
    return out


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001
        return exc


def _msg(exc) -> str:
    return "" if exc is None else str(exc).splitlines()[0]


def _writer_sequence(env: Env) -> list[str]:
    """The ph_rectification writer's exact statement sequence on the two tables, run as the builder in one transaction and
    rolled back. Returns violations."""
    v: list[str] = []
    b = env.builder()
    try:
        b.execute("DELETE FROM phala_rectification_best WHERE chart_id = %s", (CHART,))
        b.execute("DELETE FROM phala_rectification WHERE chart_id = %s", (CHART,))
        rid = b.execute("INSERT INTO phala_rectification (chart_id, candidate_birth_utc, offset_minutes, ayanamsha_id, lagna_sign, "
                        "lagna_longitude_deg, lagna_degree_in_sign, lel_fit_score, lel_events_matched, lel_events_tested, lagna_stable) "
                        "VALUES (%s, now(), 0, 'lahiri', 'Aries', 1.0, 1.0, 0.0, 0, 0, true) RETURNING id", (CHART,)).fetchone()[0]
        b.execute("INSERT INTO phala_rectification_best (chart_id, best_candidate_id, offset_minutes, auto_action) VALUES (%s, %s, 0, 'stage_for_review')",
                  (CHART, rid))
        b.execute("SELECT count(*) FROM phala_rectification WHERE chart_id = %s", (CHART,)).fetchone()
    except Exception as exc:  # noqa: BLE001
        v.append(f"writer sequence failed as the builder: {_msg(exc)}")
    finally:
        b.rollback()
        b.close()
    return v


# -- scenarios (each returns a list of violations) ------------------------------------------

def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        before = env.acls()
        pre = _writer_sequence(env)
        assert pre and "InsufficientPrivilege" in pre[0] or "permission denied" in pre[0], f"precondition: the builder already works ({pre})"
        for t in TABLES:
            assert not any(_privs(env, t).values()), f"precondition: builder already holds a privilege on {t}"
        notices: list[str] = []
        try:
            lock_after = env.apply(sql, notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after = env.acls()
        for t in TABLES:
            p = _privs(env, t)
            for g in GRANTED:
                if not p[g]:
                    v.append(f"builder lacks {g} on {t}")
            extra = [k for k in DENIED if p[k]]
            if extra:
                v.append(f"builder holds extra privilege on {t}: {extra}")
            if sorted(set(before[t]) | {ENTRY}) != after[t]:
                v.append(f"relacl of {t} is not 'before + {ENTRY}': {after[t]}")
        for t in SIBLINGS:
            if before[t] != after[t]:
                v.append(f"out-of-scope relation {t} was touched: {after[t]}")
        added = sorted(f"{t}:{e}" for t in after for e in set(after[t]) - set(before.get(t, [])))
        if added != sorted(f"{t}:{ENTRY}" for t in TABLES):
            v.append(f"ACL diff over all relations is not exactly the two builder entries: {added}")
        if any(e.startswith("=") for t in TABLES for e in after[t]):
            v.append("a PUBLIC grant appeared on a target table")
        v += _writer_sequence(env)
        b = env.builder()
        try:
            for stmt in ("UPDATE phala_rectification SET lel_events_tested = 1", "TRUNCATE phala_rectification",
                         "UPDATE phala_rectification_best SET offset_minutes = 1", "TRUNCATE phala_rectification_best"):
                exc = _try(lambda stmt=stmt: b.execute(stmt))
                b.rollback()
                if "permission denied" not in _msg(exc):
                    v.append(f"builder is not denied: {stmt} ({_msg(exc) or 'succeeded'})")
            for t in SIBLINGS:
                if not isinstance(_try(lambda t=t: b.execute(f"SELECT 1 FROM public.{t}")), Exception):
                    v.append(f"builder can read out-of-scope table {t}")
                b.rollback()
        finally:
            b.close()
        seqs = env.acls()
        if [k for k in seqs if k.endswith("_seq")]:
            v.append("a sequence appeared")
    finally:
        env.drop()
    return v


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    env = Env(cl)
    try:
        env.apply(sql)
        snap = env.acls()
        notices: list[str] = []
        try:
            env.apply(sql, notices)
        except Exception as exc:  # noqa: BLE001
            return [f"re-run failed: {_msg(exc)}"]
        v: list[str] = []
        if env.acls() != snap:
            v.append("a re-run changed an ACL")
        if sum("already holds" in n for n in notices) != 6:
            v.append(f"expected six no-op notices, got {notices}")
        return v
    finally:
        env.drop()


def sc_partial(cl: Cluster, sql: str) -> list[str]:
    env = Env(cl)
    try:
        with env.owner() as c:
            c.execute("GRANT SELECT ON public.phala_rectification TO data_plane_builder")
            c.commit()
        notices: list[str] = []
        env.apply(sql, notices)
        v = [f"builder lacks {g} on {t}" for t in TABLES for g, ok in _privs(env, t).items() if g in GRANTED and not ok]
        if sum("already holds SELECT on public.phala_rectification;" in n for n in notices) != 1:
            v.append(f"the held SELECT was not skipped: {notices}")
        return v
    finally:
        env.drop()


def sc_guards(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    # missing role (cluster-wide role renamed for the duration, always restored)
    env = Env(cl)
    try:
        with env.admin() as c:
            c.execute("ALTER ROLE data_plane_builder RENAME TO data_plane_builder_x")
        try:
            exc = _try(lambda: env.apply(sql))
        finally:
            with env.admin() as c:
                c.execute("ALTER ROLE data_plane_builder_x RENAME TO data_plane_builder")
        if "1261: role data_plane_builder does not exist" not in _msg(exc):
            v.append(f"missing role not refused by the migration's own guard: {_msg(exc)}")
    finally:
        env.drop()
    # missing table
    env = Env(cl)
    try:
        with env.owner() as c:
            c.execute("DROP TABLE public.phala_rectification_best")
            c.commit()
        before = env.acls()
        exc = _try(lambda: env.apply(sql))
        if "1261: public.phala_rectification_best does not exist" not in _msg(exc):
            v.append(f"missing table not refused by the migration's own guard: {_msg(exc)}")
        if env.acls() != before:
            v.append("a refused migration granted something (missing table)")
    finally:
        env.drop()
    # not an ordinary table
    env = Env(cl)
    try:
        with env.owner() as c:
            c.execute("DROP TABLE public.phala_rectification_best")
            c.execute("CREATE VIEW public.phala_rectification_best AS SELECT 1 AS id")
            c.commit()
        before = env.acls()
        exc = _try(lambda: env.apply(sql))
        if "is not an ordinary table" not in _msg(exc):
            v.append(f"a view was not refused: {_msg(exc)}")
        if env.acls() != before:
            v.append("a refused migration granted something (not a table)")
    finally:
        env.drop()
    # migration user is not the owner
    env = Env(cl)
    try:
        with env.admin() as c:
            c.execute("GRANT CREATE, USAGE ON SCHEMA public TO other_owner")
        before = env.acls()
        exc = _try(lambda: env.apply(sql, user="other_owner"))
        if "neither the owner" not in _msg(exc):
            v.append(f"a non-owner migration user was not refused by the owner guard: {_msg(exc)}")
        if env.acls() != before:
            v.append("a refused migration granted something (non-owner)")
    finally:
        env.drop()
    return v


def sc_refuses_extra(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    cases = {
        "table-level UPDATE": "GRANT UPDATE ON public.phala_rectification TO data_plane_builder",
        "column-level UPDATE": "GRANT UPDATE (offset_minutes) ON public.phala_rectification_best TO data_plane_builder",
        "via PUBLIC": "GRANT TRUNCATE ON public.phala_rectification TO PUBLIC",
        "via inherited role": "GRANT UPDATE ON public.phala_rectification_best TO extra_path; ALTER ROLE data_plane_builder INHERIT; GRANT extra_path TO data_plane_builder",
        "column-level REFERENCES": "GRANT REFERENCES (id) ON public.phala_rectification TO data_plane_builder",
    }
    for name, setup in cases.items():
        env = Env(cl)
        try:
            with env.admin() as c:
                for stmt in setup.split(";"):
                    c.execute(stmt)
            before = env.acls()
            exc = _try(lambda: env.apply(sql))
            if "holds more than SELECT, INSERT, DELETE" not in _msg(exc):
                v.append(f"{name}: not refused by the post-check ({_msg(exc) or 'applied'})")
            if env.acls() != before:
                v.append(f"{name}: a refused migration left a grant behind")
        finally:
            with env.admin() as c:
                c.execute("ALTER ROLE data_plane_builder NOINHERIT")
                c.execute("REVOKE extra_path FROM data_plane_builder")
            env.drop()
    return v


def sc_lock_timeout(cl: Cluster, sql: str) -> list[str]:
    """Another transaction holds an uncommitted ACL change on the same pg_class row: our GRANT must wait, then fail with
    lock_not_available at ~5s (not hang). The 9s statement_timeout is only a net so a mutant that lost the lock_timeout
    fails this scenario instead of hanging the suite."""
    env = Env(cl)
    blocker = env.cl.connect(env.db, "amjis_app")
    try:
        blocker.execute("GRANT SELECT ON public.phala_rectification TO blocker_role")  # held, uncommitted
        t0 = time.monotonic()
        exc = _try(lambda: env.apply(sql, session_sql="SET statement_timeout = '9s'"))
        dt = time.monotonic() - t0
        if exc is None:
            return ["the grant did not wait for the blocker (expected lock_not_available)"]
        if "lock timeout" not in _msg(exc).lower():
            return [f"expected a lock timeout, got: {_msg(exc)} after {dt:.1f}s"]
        if not 4.0 <= dt <= 8.0:
            return [f"lock timeout fired after {dt:.1f}s, expected about 5s"]
        return []
    finally:
        blocker.rollback()
        blocker.close()
        env.drop()


SCENARIOS = {"apply_once": sc_apply_once, "idempotent": sc_idempotent, "partial": sc_partial, "guards": sc_guards,
             "refuses_extra": sc_refuses_extra, "lock_timeout": sc_lock_timeout}


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_real_file_has_no_violations(cluster, name):
    assert SCENARIOS[name](cluster, REAL_SQL) == []


def test_precondition_ph_rectification_cannot_run_as_the_builder_before_the_grant(cluster):
    env = Env(cluster)
    try:
        v = _writer_sequence(env)
        assert v and "permission denied" in v[0]
    finally:
        env.drop()


# -- mutation proof --------------------------------------------------------------------------

def _mut(sql: str, a: str, b: str) -> str:
    assert a in sql, f"mutation pattern is stale: {a[:60]}"
    return sql.replace(a, b, 1)


MUTANTS = {
    "role_guard_removed": (lambda s: _mut(s, "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN", "IF false THEN"), "guards"),
    "table_exists_guard_removed": (lambda s: _mut(s, "IF rel IS NULL THEN", "IF false THEN"), "guards"),
    "relkind_guard_removed": (lambda s: _mut(s, "IF kind NOT IN ('r', 'p') THEN", "IF false THEN"), "guards"),
    "owner_guard_removed": (lambda s: _mut(s, "IF NOT pg_has_role(current_user, owner, 'USAGE') THEN", "IF false THEN"), "guards"),
    "update_privilege_added": (lambda s: _mut(s, "ARRAY['SELECT', 'INSERT', 'DELETE'];", "ARRAY['SELECT', 'INSERT', 'DELETE', 'UPDATE'];"), "apply_once"),
    "delete_privilege_dropped": (lambda s: _mut(s, "ARRAY['SELECT', 'INSERT', 'DELETE'];", "ARRAY['SELECT', 'INSERT'];"), "apply_once"),
    "select_privilege_dropped": (lambda s: _mut(s, "ARRAY['SELECT', 'INSERT', 'DELETE'];", "ARRAY['INSERT', 'DELETE'];"), "apply_once"),
    "second_table_dropped": (lambda s: _mut(s, "        'phala_rectification',\n        'phala_rectification_best'", "        'phala_rectification'"), "apply_once"),
    "grant_to_public": (lambda s: _mut(s, "TO data_plane_builder', p, rel)", "TO PUBLIC', p, rel)"), "apply_once"),
    "post_extra_check_neutered": (lambda s: _mut(s, "IF extra IS NOT NULL THEN", "IF false THEN"), "refuses_extra"),
    "post_extra_column_level_dropped": (lambda s: _mut(s, "OR (x IN ('UPDATE', 'REFERENCES') AND has_any_column_privilege('data_plane_builder', rel, x))", ""), "refuses_extra"),
    "skip_check_removed_regrants": (lambda s: _mut(s, "IF has_table_privilege('data_plane_builder', rel, p) THEN\n                RAISE NOTICE", "IF false THEN\n                RAISE NOTICE"), "idempotent"),
    "lock_timeout_removed": (lambda s: _mut(s, "SET LOCAL lock_timeout = '5s';", ""), "lock_timeout"),
    "lock_timeout_session_wide": (lambda s: _mut(s, "SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';"), "lock_timeout"),
}


def test_mutants_are_real_mutations():
    for name, (fn, _) in MUTANTS.items():
        assert fn(REAL_SQL) != REAL_SQL, name


@pytest.mark.parametrize("name", list(MUTANTS))
def test_every_mutant_is_caught(cluster, name):
    fn, scenario = MUTANTS[name]
    v = SCENARIOS[scenario](cluster, fn(REAL_SQL))
    assert v, f"mutant {name} was NOT caught by scenario {scenario}"
