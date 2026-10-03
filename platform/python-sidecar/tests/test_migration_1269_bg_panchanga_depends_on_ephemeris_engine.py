"""Migration 1269 (Suvarna Track I, TI-L0-29): bg_panchanga.depends_on {} -> {bg_ephemeris_engine} (SS Q16).

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per
available major version (15 and 17). Nothing here touches any real database. The cluster is built the way production
is shaped (P2 rule of the W1 privilege audit): the routine migration runner `amjis_app` is a NOSUPERUSER NOINHERIT
LOGIN role that holds USAGE but NOT CREATE on schema public (owned by `data_plane_schema_owner`); it owns the real
asset_registry / asset_freshness / _migrations_applied DDL (copied from a pg_dump of production) with the real
`nirmana_registry_receipt_invalidation` trigger and function, loaded with the FULL live 129-row registry graph
(tests/fixtures/registry_graph_pre_1269.json, read 2026-10-03). The migration is applied AS amjis_app inside one
transaction the way platform/scripts/migrate.ts does (BEGIN; <sql>; tracker INSERT; COMMIT).

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once    exactly one cell changes (bg_panchanga.depends_on); the trigger stales ONLY bg_panchanga (reason
                  registry_changed appended to the existing one); the whole 129-asset graph stays acyclic with
                  bg_ephemeris_engine < bg_panchanga < ga_panchanga in topological order; the REAL
                  asset_runner.deps_unsatisfied does not block bg_panchanga (engine lit) nor ga_panchanga (its service
                  dependency bg_panchanga is stale but a service's data-freshness receipt is ignored); the REAL
                  compute_downstream_closure of bg_ephemeris_engine grows by exactly bg_panchanga + its dependents.
  * gate_effective  negative control: with the engine in state 'error' the gate DOES block bg_panchanga (the edge is real).
  * idempotent    a second run changes nothing and does not re-fire the trigger.
  * guards        a drifted bg_panchanga (other deps, writer, kind, table, inactive), a missing / inactive /
                  non-service engine, or an edge that would close a cycle refuses and rolls back.
  * absent        a missing bg_panchanga row is skipped with a NOTICE.
  * silent_noop   a BEFORE UPDATE trigger that swallows the UPDATE makes the migration fail loudly.
Mutation tests then rewrite the real SQL and require every mutant to produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL 15/17 with the production-shaped role structure and
the production registry DDL; it does not read production, does not run the inspector or a real build (the in-flight
run hazard and the Nirmana frozen-manifest effect are documented in the migration header, not exercised here), and
`REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

TAG = "m1269"
_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1269_bg_panchanga_depends_on_ephemeris_engine.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

# ---- production-shaped DDL, copied from the S_L1 privilege-audit mirror (pg_dump of production, schema only) ----
REGISTRY_DDL = r"""
CREATE TABLE public.asset_registry (
    asset_id text NOT NULL,
    layer text NOT NULL,
    sort_order integer NOT NULL,
    sanskrit_name text NOT NULL,
    english_name text NOT NULL,
    english_description text NOT NULL,
    storage_type text NOT NULL,
    target_table text,
    count_sql text,
    size_sql text,
    target_floor integer,
    expected_volume_formula text,
    expected_volume_inputs jsonb,
    volume_explanation text,
    depends_on text[] DEFAULT ARRAY[]::text[],
    scope text NOT NULL,
    is_active boolean DEFAULT true,
    estimated_seconds integer,
    created_at timestamp with time zone DEFAULT now(),
    clear_tables text[],
    asset_type text DEFAULT 'data'::text NOT NULL,
    layer_name text,
    layer_index text,
    provides_apis jsonb,
    health_probe jsonb,
    catalog_status text DEFAULT 'DRAFT'::text NOT NULL,
    rebuild_on_probe_fail boolean DEFAULT false NOT NULL,
    integrity_check_sql text,
    has_substeps boolean DEFAULT false NOT NULL,
    asset_kind text DEFAULT 'data'::text NOT NULL,
    service_health text,
    last_invoked_at timestamp with time zone,
    last_selftest_at timestamp with time zone,
    selftest_detail jsonb,
    has_writer boolean DEFAULT false NOT NULL,
    writer_timeout_seconds integer DEFAULT 600 NOT NULL,
    domain text,
    rung text,
    superseded_by text,
    data_disposition text,
    natural_key_partition text,
    dead_flag boolean,
    CONSTRAINT asset_registry_asset_kind_check CHECK ((asset_kind = ANY (ARRAY['data'::text, 'service'::text, 'artifact'::text]))),
    CONSTRAINT asset_registry_asset_type_check CHECK ((asset_type = ANY (ARRAY['data'::text, 'service'::text]))),
    CONSTRAINT asset_registry_catalog_status_check CHECK ((catalog_status = ANY (ARRAY['CURRENT'::text, 'DRAFT'::text, 'RETIRED'::text]))),
    CONSTRAINT asset_registry_data_disposition_check CHECK (((data_disposition IS NULL) OR (data_disposition = ANY (ARRAY['RETAINED_AS_CAPITAL'::text, 'SUPERSEDED_IN_PLACE'::text, 'DROPPABLE'::text])))),
    CONSTRAINT asset_registry_dead_flag_not_retired CHECK (((dead_flag IS NOT TRUE) OR ((catalog_status <> 'RETIRED'::text) AND (is_active IS NOT FALSE)))),
    CONSTRAINT asset_registry_domain_check CHECK (((domain IS NULL) OR (domain = ANY (ARRAY['shared'::text, 'chart'::text])))),
    CONSTRAINT asset_registry_layer_check CHECK ((layer = ANY (ARRAY['brahmagyan'::text, 'ganita'::text, 'bodha'::text, 'kala'::text, 'phala'::text, 'mimamsa'::text]))),
    CONSTRAINT asset_registry_natural_key_partition_needs_table CHECK (((natural_key_partition IS NULL) OR (target_table IS NOT NULL))),
    CONSTRAINT asset_registry_natural_key_partition_nonblank CHECK (((natural_key_partition IS NULL) OR (btrim(natural_key_partition) <> ''::text))),
    CONSTRAINT asset_registry_rung_check CHECK (((rung IS NULL) OR (rung = ANY (ARRAY['R0'::text, 'R1'::text, 'R2'::text, 'R3'::text, 'R4'::text, 'R5'::text])))),
    CONSTRAINT asset_registry_scope_check CHECK ((scope = ANY (ARRAY['global'::text, 'per_chart'::text]))),
    CONSTRAINT asset_registry_service_health_check CHECK ((service_health = ANY (ARRAY['healthy'::text, 'degraded'::text, 'unhealthy'::text, 'unknown'::text]))),
    CONSTRAINT asset_registry_storage_type_check CHECK ((storage_type = ANY (ARRAY['postgres_table'::text, 'pgvector'::text, 'postgres_view'::text, 'gcs_jsonl'::text, 'bigquery'::text, 'tool_only'::text, 'service'::text]))),
    CONSTRAINT asset_registry_superseded_by_not_self CHECK (((superseded_by IS NULL) OR (superseded_by <> asset_id)))
);

ALTER TABLE ONLY public.asset_registry ADD CONSTRAINT asset_registry_pkey PRIMARY KEY (asset_id);
ALTER TABLE ONLY public.asset_registry ADD CONSTRAINT asset_registry_superseded_by_fkey
    FOREIGN KEY (superseded_by) REFERENCES public.asset_registry(asset_id) ON DELETE RESTRICT;
CREATE TABLE public.asset_freshness (
    asset_id text NOT NULL,
    chart_id uuid,
    scope_key text GENERATED ALWAYS AS (COALESCE((chart_id)::text, '__global__'::text)) STORED NOT NULL,
    partition_key text NOT NULL,
    freshness_state text NOT NULL,
    reasons jsonb DEFAULT '[]'::jsonb NOT NULL,
    receipt_version text NOT NULL,
    observed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT asset_freshness_freshness_state_check CHECK ((freshness_state = ANY (ARRAY['fresh'::text, 'stale'::text, 'unknown'::text]))),
    CONSTRAINT asset_freshness_partition_key_check CHECK ((btrim(partition_key) <> ''::text)),
    CONSTRAINT asset_freshness_reasons_check CHECK ((jsonb_typeof(reasons) = 'array'::text))
);

ALTER TABLE ONLY public.asset_freshness ADD CONSTRAINT asset_freshness_pkey PRIMARY KEY (asset_id, scope_key, partition_key);
ALTER TABLE ONLY public.asset_freshness ADD CONSTRAINT asset_freshness_asset_id_fkey
    FOREIGN KEY (asset_id) REFERENCES public.asset_registry(asset_id) ON DELETE CASCADE;
CREATE TABLE public._migrations_applied (
    id integer NOT NULL,
    filename text NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL,
    sha256 text NOT NULL,
    sql_identity text
);

ALTER TABLE ONLY public._migrations_applied ADD CONSTRAINT _migrations_applied_filename_key UNIQUE (filename);
CREATE SEQUENCE public._migrations_applied_id_seq OWNED BY public._migrations_applied.id;
ALTER TABLE ONLY public._migrations_applied ALTER COLUMN id SET DEFAULT nextval('public._migrations_applied_id_seq');
CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'registry_changed' THEN reasons
           ELSE reasons || '["registry_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$function$;
CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table ON public.asset_registry FOR EACH ROW WHEN ((old.* IS DISTINCT FROM new.*)) EXECUTE FUNCTION public.nirmana_invalidate_registry_receipts();
"""

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
    """A disposable PostgreSQL cluster (unix socket only). Production-shaped roles: the routine migration runner
    `amjis_app` is a NOSUPERUSER NOINHERIT LOGIN role with NO CREATE on schema public (USAGE only); schema public is
    owned by `data_plane_schema_owner`. Every object a migration touches is owned by amjis_app, like production."""

    def __init__(self, version: str, bindir: Path):
        self.version, self.bindir = version, bindir
        self.data = tempfile.mkdtemp(prefix=f"{TAG}pg{version}_")
        self.sock = tempfile.mkdtemp(prefix="p", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self._n = 0
        self._base: str | None = None
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
                "CREATE ROLE data_plane_schema_owner NOLOGIN NOINHERIT",
                "CREATE ROLE amjis_app LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB",
                "CREATE ROLE suvarna_reader LOGIN NOINHERIT NOSUPERUSER",
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
    """A fresh production-shaped database inside the disposable cluster, with the real asset_registry /
    asset_freshness / _migrations_applied DDL, the real invalidation trigger and function, all owned by amjis_app."""

    def __init__(self, cl: Cluster, ddl: str = REGISTRY_DDL):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        # the production-shaped base database is built ONCE per cluster and cloned (CREATE DATABASE ... TEMPLATE)
        if cl._base is None:
            cl._base = "base_tpl"
            with cl.connect("postgres", "postgres", autocommit=True) as c:
                c.execute(f"CREATE DATABASE {cl._base} TEMPLATE template0")
            with cl.connect(cl._base, "postgres", autocommit=True) as c:
                c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
                c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
                c.execute("GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner")
                c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, suvarna_reader")
                c.execute(ddl)
                self._own_everything(c)
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} TEMPLATE {cl._base}")

    def _own_everything(self, c: psycopg.Connection) -> None:
        for (rel,) in c.execute(
                "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r','S')"
        ).fetchall():
            c.execute(f'ALTER TABLE public."{rel}" OWNER TO amjis_app' if _is_table(c, rel)
                      else f'ALTER SEQUENCE public."{rel}" OWNER TO amjis_app')
        c.execute("ALTER FUNCTION public.nirmana_invalidate_registry_receipts() OWNER TO amjis_app")
        c.execute("REVOKE ALL ON FUNCTION public.nirmana_invalidate_registry_receipts() FROM PUBLIC")

    def admin(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "postgres", autocommit=True)

    def app(self, autocommit: bool = False) -> psycopg.Connection:
        return self.cl.connect(self.db, "amjis_app", autocommit=autocommit)

    def _conn(self) -> psycopg.Connection:
        """One shared superuser autocommit connection for fixture writes (opening one per row is the slow path)."""
        if getattr(self, "_c", None) is None or self._c.closed:
            self._c = self.cl.connect(self.db, "postgres", autocommit=True)
        return self._c

    def run(self, stmt: str, params=None) -> None:
        """Fixture DML/DDL as the superuser (the app role cannot CREATE in schema public, like production)."""
        self._conn().execute(stmt, params)

    def rows(self, stmt: str, params=None) -> list[tuple]:
        with self.admin() as c:
            return c.execute(stmt, params).fetchall()

    def add_asset(self, asset_id: str, **cols) -> None:
        base = dict(layer="brahmagyan", sort_order=1, sanskrit_name=asset_id, english_name=asset_id,
                    english_description=asset_id, storage_type="postgres_table", scope="global",
                    catalog_status="CURRENT", asset_type="data", asset_kind="data", is_active=True,
                    has_writer=False, depends_on=[], target_table=None, count_sql=None, target_floor=None,
                    integrity_check_sql=None)
        base.update(cols)
        base["asset_id"] = asset_id
        names = list(base)
        self._conn().execute(f"INSERT INTO public.asset_registry ({', '.join(names)}) VALUES ({', '.join(['%s'] * len(names))})",
                             [base[n] for n in names])

    def add_fresh(self, asset_id: str, state: str = "fresh", reasons: str = "[]") -> None:
        self._conn().execute("INSERT INTO public.asset_freshness (asset_id, partition_key, freshness_state, reasons, receipt_version, observed_at) "
                             "VALUES (%s, '__whole_asset__', %s, %s::jsonb, 'v1', '2026-01-01T00:00:00Z')",
                             (asset_id, state, reasons))

    def apply(self, sql: str, name: str = "mig.sql", notices: list[str] | None = None, track: bool = True):
        """Apply `sql` as amjis_app in ONE transaction (BEGIN; sql; tracker INSERT; COMMIT), like migrate.ts.
        Raises on failure (after rolling back)."""
        conn = self.app()
        try:
            if notices is not None:
                conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
            conn.execute(sql)
            if track:
                conn.execute("INSERT INTO public._migrations_applied (filename, sha256, sql_identity) VALUES (%s, %s, %s)",
                             (name, "0" * 64, "x"))
            conn.commit()
            return conn.execute("SHOW lock_timeout").fetchone()[0]
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def snapshot(self, table: str, key: str) -> dict:
        with self.admin() as c:
            cur = c.execute(f"SELECT * FROM public.{table} ORDER BY {key}")
            cols = [d.name for d in cur.description]
            return {r[cols.index(key)]: dict(zip(cols, r)) for r in cur.fetchall()}

    def drop(self) -> None:
        if getattr(self, "_c", None) is not None and not self._c.closed:
            self._c.close()
        with self.cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


def _is_table(c: psycopg.Connection, rel: str) -> bool:
    return c.execute("SELECT relkind = 'r' FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relname = %s",
                     (rel,)).fetchone()[0]


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001 - scenarios report any failure as data
        return exc


def _msg(exc: BaseException | None) -> str:
    return "" if exc is None else str(exc).splitlines()[0]


def changed_columns(before: dict, after: dict) -> dict[str, set[str]]:
    """{asset_id: {columns whose value differs}} for rows present in both snapshots."""
    out: dict[str, set[str]] = {}
    for k in before:
        if k in after:
            diff = {c for c in before[k] if before[k][c] != after[k].get(c)}
            if diff:
                out[k] = diff
    return out


def mutate(sql: str, old: str, new: str) -> str:
    """Return `sql` with exactly-one `old` replaced by `new` (a mutant that does not apply is a test bug)."""
    assert sql.count(old) == 1, f"mutation anchor not unique/present: {old!r} x{sql.count(old)}"
    return sql.replace(old, new)


# ---------------------------------------------------------------------------------------------- fixture data
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.orchestrator import asset_runner as ar  # noqa: E402  (the REAL gate and closure functions)

GRAPH = json.loads((Path(__file__).resolve().parent / "fixtures" / "registry_graph_pre_1269.json").read_text())["assets"]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
THROUGHPUT_DDL = """
CREATE TABLE public.asset_throughput (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id), chart_id uuid,
                                      state text NOT NULL, last_built_at timestamptz);
"""


def seed(env: Env, engine_state: str = "lit") -> None:
    env.run(THROUGHPUT_DDL)
    env.run("ALTER TABLE public.asset_throughput OWNER TO amjis_app")
    for aid, row in GRAPH.items():
        kw = dict(depends_on=row["depends_on"], is_active=row["is_active"], asset_kind=row["asset_kind"], has_writer=row["has_writer"])
        if row["asset_kind"] == "service":
            kw.update(storage_type="service", asset_type="service")
        elif aid != "bg_panchanga":
            kw.update(target_table=aid)
        env.add_asset(aid, **kw)
    env.add_fresh("bg_panchanga", "unknown", '["output_digest_spec_unavailable"]')
    env.add_fresh("bg_ephemeris_engine", "stale", '["output_digest_spec_unavailable", "registry_changed"]')
    env.add_fresh("ga_panchanga")
    env.add_fresh("ga_positions")
    env.add_fresh("bg_cohort")
    with env.admin() as c:
        for aid, st, ch in (("bg_ephemeris_engine", engine_state, None), ("bg_panchanga", "lit", None), ("bg_cohort", "lit", None),
                            ("ga_positions", "lit", CHART), ("ga_panchanga", "lit", CHART)):
            c.execute("INSERT INTO public.asset_throughput (asset_id, chart_id, state, last_built_at) VALUES (%s, %s, %s, '2026-08-27T06:09:30Z')",
                      (aid, ch, st))


def _precondition(env: Env) -> None:
    with env.admin() as c:
        assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
        assert c.execute("SELECT rolsuper FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
        assert c.execute("SELECT rolinherit FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
    conn = env.app()
    try:
        assert isinstance(_try(lambda: conn.execute("CREATE TABLE public.zz_should_fail (x int)")), psycopg.errors.InsufficientPrivilege)
    finally:
        conn.close()
    assert GRAPH["bg_panchanga"]["depends_on"] == [] and GRAPH["bg_ephemeris_engine"]["depends_on"] == []
    assert GRAPH["bg_cohort"]["depends_on"] == ["bg_ephemeris_engine"]  # the precedent edge
    assert GRAPH["ga_panchanga"]["depends_on"] == ["ga_positions", "bg_panchanga"]


def _graph(env: Env) -> dict[str, list[str]]:
    return {a: list(d or []) for a, d in env.rows("SELECT asset_id, depends_on FROM public.asset_registry")}


def _topo(graph: dict[str, list[str]]) -> list[str] | None:
    """Kahn's algorithm over the declared edges; None when a cycle exists."""
    indeg = {a: 0 for a in graph}
    for a, deps in graph.items():
        for d in deps:
            if d in graph:
                indeg[a] += 1
    queue = sorted(a for a, n in indeg.items() if n == 0)
    order: list[str] = []
    while queue:
        a = queue.pop(0)
        order.append(a)
        for b, deps in sorted(graph.items()):
            if a in deps:
                indeg[b] -= 1
                if indeg[b] == 0:
                    queue.append(b)
    return order if len(order) == len(graph) else None


def _gate(env: Env, asset_id: str, chart: str | None) -> list[str]:
    """The REAL asset_runner.deps_unsatisfied, run against the fixture."""
    with env.cl.connect(env.db, "postgres") as c:
        cur = c.cursor(row_factory=dict_row)
        return ar.deps_unsatisfied(cur, chart, asset_id)


def _closure(env: Env, asset_id: str) -> set[str]:
    with env.cl.connect(env.db, "postgres") as c:
        return set(ar.compute_downstream_closure(c.cursor(row_factory=dict_row), asset_id))


# ---------------------------------------------------------------------------------------------- scenarios
def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        _precondition(env)
        before = env.snapshot("asset_registry", "asset_id")
        fresh_before = env.snapshot("asset_freshness", "asset_id")
        closure_before = _closure(env, "bg_ephemeris_engine")
        notices: list[str] = []
        try:
            lock_after = env.apply(sql, "1269.sql", notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply as amjis_app failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after = env.snapshot("asset_registry", "asset_id")
        if after["bg_panchanga"]["depends_on"] != ["bg_ephemeris_engine"]:
            v.append(f"bg_panchanga.depends_on is {after['bg_panchanga']['depends_on']}")
        if changed_columns(before, after) != {"bg_panchanga": {"depends_on"}}:
            v.append(f"changed cells are not exactly bg_panchanga.depends_on: {changed_columns(before, after)}")
        fresh_after = env.snapshot("asset_freshness", "asset_id")
        f = fresh_after["bg_panchanga"]
        if f["freshness_state"] != "stale" or list(f["reasons"]) != ["output_digest_spec_unavailable", "registry_changed"]:
            v.append(f"bg_panchanga freshness is {f['freshness_state']} {f['reasons']}")
        for other in ("ga_panchanga", "ga_positions", "bg_cohort", "bg_ephemeris_engine"):
            if fresh_after[other] != fresh_before[other]:
                v.append(f"the freshness row of {other} changed (only bg_panchanga may go stale)")
        order = _topo(_graph(env))
        if order is None:
            v.append("the registry graph has a cycle after the migration")
        else:
            if not order.index("bg_ephemeris_engine") < order.index("bg_panchanga") < order.index("ga_panchanga"):
                v.append("topological order does not place bg_ephemeris_engine < bg_panchanga < ga_panchanga")
        # the real dispatch gate
        if _gate(env, "bg_panchanga", None) != []:
            v.append(f"bg_panchanga is blocked by its new dependency: {_gate(env, 'bg_panchanga', None)}")
        if _gate(env, "ga_panchanga", CHART) != []:
            v.append(f"ga_panchanga is newly blocked: {_gate(env, 'ga_panchanga', CHART)}")
        closure_after = _closure(env, "bg_ephemeris_engine")
        added = closure_after - closure_before
        expected_added = ({"bg_panchanga"} | _closure(env, "bg_panchanga")) - closure_before
        if closure_before - closure_after:
            v.append("the downstream closure of bg_ephemeris_engine lost members")
        if added != expected_added:
            v.append(f"closure grew by {sorted(added)}, expected exactly bg_panchanga + its dependents not already downstream: {sorted(expected_added)}")
        if env.rows("SELECT count(*) FROM public._migrations_applied WHERE filename = '1269.sql'")[0][0] != 1:
            v.append("tracker row missing")
        return v
    finally:
        env.drop()


def sc_gate_is_effective(cl: Cluster, sql: str) -> list[str]:
    """Negative control: the edge is a REAL gate. With the engine in state error the dependent is blocked."""
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env, engine_state="error")
        env.apply(sql, "1269.sql")
        got = _gate(env, "bg_panchanga", None)
        if got != ["bg_ephemeris_engine(error)"]:
            v.append(f"gate did not block bg_panchanga on an errored engine: {got}")
        return v
    finally:
        env.drop()


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.apply(sql, "1269.sql")
        snap, fresh = env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id")
        notices: list[str] = []
        try:
            env.apply(sql, "1269_again.sql", notices, track=False)
        except Exception as exc:  # noqa: BLE001
            return [f"second run failed: {_msg(exc)}"]
        if env.snapshot("asset_registry", "asset_id") != snap or env.snapshot("asset_freshness", "asset_id") != fresh:
            v.append("a second run changed something / re-fired the trigger")
        if not any("already depends on bg_ephemeris_engine" in n for n in notices):
            v.append(f"second run did not report the existing edge: {notices}")
        return v
    finally:
        env.drop()


DRIFTS = [
    ("panchanga_other_dep", "UPDATE public.asset_registry SET depends_on = ARRAY['ga_positions'] WHERE asset_id = 'bg_panchanga'", "refusing to overwrite"),
    ("panchanga_has_writer", "UPDATE public.asset_registry SET has_writer = true WHERE asset_id = 'bg_panchanga'", "drifted from the audited state"),
    ("panchanga_asset_kind", "UPDATE public.asset_registry SET asset_kind = 'data' WHERE asset_id = 'bg_panchanga'", "drifted from the audited state"),
    ("panchanga_target_table", "UPDATE public.asset_registry SET target_table = 'x' WHERE asset_id = 'bg_panchanga'", "drifted from the audited state"),
    ("panchanga_inactive", "UPDATE public.asset_registry SET is_active = false WHERE asset_id = 'bg_panchanga'", "drifted from the audited state"),
    ("engine_inactive", "UPDATE public.asset_registry SET is_active = false WHERE asset_id = 'bg_ephemeris_engine'", "dependency trap"),
    ("engine_not_service", "UPDATE public.asset_registry SET asset_kind = 'data' WHERE asset_id = 'bg_ephemeris_engine'", "dependency trap"),
    ("engine_missing", "DELETE FROM public.asset_throughput WHERE asset_id = 'bg_ephemeris_engine'; "
                       "DELETE FROM public.asset_registry WHERE asset_id = 'bg_ephemeris_engine'", "dependency trap"),
    ("would_close_a_cycle", "UPDATE public.asset_registry SET depends_on = ARRAY['bg_panchanga'] WHERE asset_id = 'bg_ephemeris_engine'", "cycle"),
]


def sc_guards(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for name, drift, needle in DRIFTS:
        env = Env(cl)
        try:
            seed(env)
            env.run(drift)
            before = env.snapshot("asset_registry", "asset_id")
            fresh = env.snapshot("asset_freshness", "asset_id")
            exc = _try(lambda: env.apply(sql, "1269.sql"))
            if exc is None:
                v.append(f"drift {name}: the migration did not refuse")
            elif needle not in str(exc):
                v.append(f"drift {name}: refused with the wrong message: {_msg(exc)}")
            if env.snapshot("asset_registry", "asset_id") != before or env.snapshot("asset_freshness", "asset_id") != fresh:
                v.append(f"drift {name}: state changed although the migration refused")
            if env.rows("SELECT count(*) FROM public._migrations_applied")[0][0] != 0:
                v.append(f"drift {name}: tracker row written for a refused migration")
        finally:
            env.drop()
    return v


def sc_absent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.run("DELETE FROM public.asset_throughput WHERE asset_id = 'bg_panchanga'")
        env.run("DELETE FROM public.asset_registry WHERE asset_id = 'bg_panchanga'")  # asset_freshness cascades
        notices: list[str] = []
        try:
            env.apply(sql, "1269.sql", notices)
        except Exception as exc:  # noqa: BLE001
            return [f"an absent bg_panchanga made the migration fail: {_msg(exc)}"]
        if not any("bg_panchanga is not in asset_registry" in n for n in notices):
            v.append("absent row was skipped silently (no NOTICE)")
        return v
    finally:
        env.drop()


def sc_silent_noop(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.run("CREATE FUNCTION public.zz_swallow() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
        env.run("CREATE TRIGGER zz_swallow BEFORE UPDATE ON public.asset_registry FOR EACH ROW EXECUTE FUNCTION public.zz_swallow()")
        exc = _try(lambda: env.apply(sql, "1269.sql"))
        if exc is None:
            v.append("a swallowed UPDATE let the migration pass silently")
        return v
    finally:
        env.drop()


SCENARIOS = [sc_apply_once, sc_gate_is_effective, sc_idempotent, sc_guards, sc_absent, sc_silent_noop]


def all_violations(cl: Cluster, sql: str) -> list[str]:
    out: list[str] = []
    for sc in SCENARIOS:
        try:
            out += [f"{sc.__name__}: {x}" for x in sc(cl, sql)]
        except Exception as exc:  # noqa: BLE001 - a scenario that cannot even run is itself a violation
            out.append(f"{sc.__name__}: scenario crashed: {_msg(exc)}")
    return out


def test_real_migration_has_no_violations(cluster):
    assert all_violations(cluster, REAL_SQL) == []


MUTANTS = [
    ("wrong dependency (bg_ephemeris)", ("SET depends_on = ARRAY['bg_ephemeris_engine']::text[]", "SET depends_on = ARRAY['bg_ephemeris']::text[]")),
    ("edge to a data asset", ("SET depends_on = ARRAY['bg_ephemeris_engine']::text[]", "SET depends_on = ARRAY['bg_ephemeris_engine', 'ga_positions']::text[]")),
    ("panchanga identity guard removed", ("IF v_active IS DISTINCT FROM true OR v_kind IS DISTINCT FROM 'service'\n       OR v_writer IS DISTINCT FROM false OR v_target IS NOT NULL THEN", "IF false THEN")),
    ("panchanga has_writer guard removed", ("\n       OR v_writer IS DISTINCT FROM false OR v_target IS NOT NULL THEN", "\n       OR v_target IS NOT NULL THEN")),
    ("engine guard removed", ("IF NOT FOUND OR e_active IS DISTINCT FROM true OR e_kind IS DISTINCT FROM 'service' THEN", "IF false THEN")),
    ("engine service guard removed", (" OR e_kind IS DISTINCT FROM 'service' THEN", " THEN")),
    ("overwrite of other deps allowed", ("    IF v_deps IS DISTINCT FROM '{}'::text[] THEN\n        RAISE EXCEPTION", "    IF false THEN\n        RAISE EXCEPTION")),
    ("already-present skip removed", ("    IF v_deps = ARRAY['bg_ephemeris_engine']::text[] THEN\n        RAISE NOTICE '1269: bg_panchanga already depends on bg_ephemeris_engine; skipped';\n        RETURN;\n    END IF;\n", "")),
    ("both cycle checks removed", None),
    ("absent row raises instead of skipping", ("RAISE NOTICE '1269: bg_panchanga is not in asset_registry; skipped';\n        RETURN;", "RAISE EXCEPTION '1269: absent';")),
    ("lock_timeout session-wide", ("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '5s';")),
    ("also edits another asset's depends_on", ("    -- Post-check: re-read the cell", "    UPDATE asset_registry SET depends_on = depends_on || ARRAY['bg_ephemeris_engine'] WHERE asset_id = 'bg_class_priors';\n    -- Post-check: re-read the cell")),
    ("row-count check and post-check removed", "noop"),
]


def _build_mutant(spec) -> str:
    s = REAL_SQL
    if spec is None:  # the pre-update reachability guard AND the post-update cycle walk
        i = s.index("    -- no cycle: bg_panchanga must not be reachable from bg_ephemeris_engine")
        j = s.index("    UPDATE asset_registry SET depends_on = ARRAY['bg_ephemeris_engine']::text[]")
        s = s[:i] + s[j:]
        i = s.index("    IF EXISTS (\n        WITH RECURSIVE reach(asset_id) AS (\n            SELECT d FROM asset_registry a")
        j = s.index("END\n$m1269$;")
        return s[:i] + s[j:]
    if spec == "noop":
        s = s.replace("    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 1 THEN\n        RAISE EXCEPTION '1269: bg_panchanga depends_on update touched % rows, expected 1', v_rows;\n    END IF;\n", "")
        assert "v_rows <> 1" not in s
        i = s.index("    -- Post-check: re-read the cell")
        j = s.index("END\n$m1269$;")
        return s[:i] + s[j:]
    return mutate(s, *spec)


@pytest.mark.parametrize("name,spec", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_every_mutant_is_killed(cluster, name, spec):
    mutant = _build_mutant(spec)
    assert mutant != REAL_SQL
    viol = all_violations(cluster, mutant)
    assert viol != [], f"mutant survived: {name}"
    # a mutant that merely breaks the SQL (a scenario crash) proves nothing: require a detected behavioural violation
    assert any("scenario crashed" not in x for x in viol), f"mutant only crashed the harness: {name}: {viol[:2]}"
    log = os.environ.get("MUTATION_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(f"PG{cluster.version} | {name} | KILLED by {len(viol)} violation(s); first: {viol[0][:160]}\n")
