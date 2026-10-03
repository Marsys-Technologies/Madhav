"""Migration 1270 (Suvarna Track I, TI-L0-30): bg_cohort.count_sql scoped to the primary table
(SELECT COUNT(*) FROM bg_synthetic_cohort) and target_floor 110000 -> 10000 (SS Q19).

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per
available major version (15 and 17). Nothing here touches any real database. The cluster is built the way production
is shaped (P2 rule of the W1 privilege audit): the routine migration runner `amjis_app` is a NOSUPERUSER NOINHERIT
LOGIN role that holds USAGE but NOT CREATE on schema public (owned by `data_plane_schema_owner`); it owns the real
asset_registry / asset_freshness / _migrations_applied DDL (copied from a pg_dump of production) with the real
`nirmana_registry_receipt_invalidation` trigger and function. The migration is applied AS amjis_app inside one
transaction the way platform/scripts/migrate.ts does (BEGIN; <sql>; tracker INSERT; COMMIT).

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once    exactly two cells change (bg_cohort.count_sql, target_floor); the multi-table declaration
                  (natural_key_partition), the explanation, the integrity check and the deps are untouched; the
                  trigger stales ONLY bg_cohort; the stored count_sql runs and returns the primary-table count (3 on
                  the fixture, where the old sum returned 33); and the DOCUMENTED SERVING EFFECT holds: the REAL
                  asset_runner.deps_unsatisfied now reads 'bg_cohort(receipt:stale)' for the dependent ka_kshetra
                  (it read [] before).
  * idempotent    a second run changes nothing and does not re-fire the trigger.
  * guards        a drifted floor, any change to count_sql (incl. a half-applied scoped-but-old-floor state, or a
                  count of the child table), or a drifted target_table refuses and rolls back.
  * absent        a missing bg_cohort row is skipped with a NOTICE.
  * silent_noop   a BEFORE UPDATE trigger that swallows the UPDATE makes the migration fail loudly.
Mutation tests then rewrite the real SQL and require every mutant to produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL 15/17 with the production-shaped role structure and
the production registry DDL; it does not read production, does not run the inspector, does not rebuild bg_cohort
(so clearing the stale receipt is not exercised), and
`REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import hashlib
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

TAG = "m1270"
_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1270_bg_cohort_count_scope.sql"
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
from pipeline.orchestrator import asset_runner as ar  # noqa: E402  (the REAL dispatch gate)

OLD_COUNT_SQL = ("SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count")
NEW_COUNT_SQL = "SELECT COUNT(*) FROM bg_synthetic_cohort"
NKP = "bg_synthetic_cohort.synthetic_id; bg_synthetic_cohort_md.(synthetic_id,md_index)"
EXPLANATION = ("10,000 deterministic synthetic birth charts + 100,000 Vimshottari mahadasha age-chain rows from fixed RNG seed "
               "20260729 and the pinned Swiss Ephemeris corpus.")
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
DDL = """
CREATE TABLE public.bg_synthetic_cohort (synthetic_id integer PRIMARY KEY);
CREATE TABLE public.bg_synthetic_cohort_md (synthetic_id integer NOT NULL, md_index integer NOT NULL, PRIMARY KEY (synthetic_id, md_index));
CREATE TABLE public.asset_throughput (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id), chart_id uuid,
                                      state text NOT NULL, last_built_at timestamptz);
"""


def test_audited_literal_matches_the_pin():
    assert hashlib.md5(OLD_COUNT_SQL.encode()).hexdigest() == "d8f9f0bfe7b996e5fd829bc3f5347632"


def seed(env: Env) -> None:
    env.run(DDL)
    for t in ("bg_synthetic_cohort", "bg_synthetic_cohort_md", "asset_throughput"):
        env.run(f"ALTER TABLE public.{t} OWNER TO amjis_app")
    env.run("INSERT INTO public.bg_synthetic_cohort SELECT g FROM generate_series(1, 3) g")
    env.run("INSERT INTO public.bg_synthetic_cohort_md SELECT g, m FROM generate_series(1, 3) g, generate_series(1, 10) m")
    env.add_asset("bg_ephemeris_engine", storage_type="service", asset_type="service", asset_kind="service")
    env.add_asset("bg_cohort", target_table="bg_synthetic_cohort", count_sql=OLD_COUNT_SQL, target_floor=110000, has_writer=True,
                  depends_on=["bg_ephemeris_engine"], natural_key_partition=NKP, volume_explanation=EXPLANATION,
                  size_sql="SELECT pg_total_relation_size('bg_synthetic_cohort')",
                  integrity_check_sql="SELECT (SELECT count(*) = 3 FROM bg_synthetic_cohort)")
    env.add_asset("ka_kshetra", layer="kala", target_table="kala_kshetra", has_writer=True, depends_on=["bg_cohort"])
    env.add_asset("bg_parihara_rules", target_table="bg_parihara_rules", target_floor=449, has_writer=True)
    for a in ("bg_cohort", "bg_parihara_rules"):
        env.add_fresh(a)
    with env.admin() as c:
        for a, st, ch in (("bg_ephemeris_engine", "lit", None), ("bg_cohort", "lit", None)):
            c.execute("INSERT INTO public.asset_throughput (asset_id, chart_id, state, last_built_at) VALUES (%s, %s, %s, '2026-09-07T06:32:44Z')", (a, ch, st))


def _precondition(env: Env) -> None:
    with env.admin() as c:
        assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
        assert c.execute("SELECT rolsuper FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
        assert c.execute("SELECT rolinherit FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
        # the OLD count is the two-table sum (33 on this fixture), as the cockpit would run it
        assert c.execute(OLD_COUNT_SQL).fetchone()[0] == 33
    conn = env.app()
    try:
        assert isinstance(_try(lambda: conn.execute("CREATE TABLE public.zz_should_fail (x int)")), psycopg.errors.InsufficientPrivilege)
    finally:
        conn.close()


def _gate(env: Env, asset_id: str) -> list[str]:
    """The REAL asset_runner.deps_unsatisfied against the fixture."""
    with env.cl.connect(env.db, "postgres") as c:
        return ar.deps_unsatisfied(c.cursor(row_factory=dict_row), None, asset_id)


# ---------------------------------------------------------------------------------------------- scenarios
def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        _precondition(env)
        if _gate(env, "ka_kshetra") != []:
            return ["fixture: ka_kshetra is blocked before the migration"]
        before = env.snapshot("asset_registry", "asset_id")
        fresh_before = env.snapshot("asset_freshness", "asset_id")
        notices: list[str] = []
        try:
            lock_after = env.apply(sql, "1270.sql", notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply as amjis_app failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after = env.snapshot("asset_registry", "asset_id")
        row = after["bg_cohort"]
        if row["count_sql"] != NEW_COUNT_SQL or row["target_floor"] != 10000:
            v.append(f"bg_cohort is {row['count_sql']!r} / {row['target_floor']}, expected the scoped pair")
        if changed_columns(before, after) != {"bg_cohort": {"count_sql", "target_floor"}}:
            v.append(f"changed cells are not exactly bg_cohort.count_sql + target_floor: {changed_columns(before, after)}")
        if (row["natural_key_partition"], row["volume_explanation"], row["integrity_check_sql"], row["depends_on"]) != \
                (NKP, EXPLANATION, before["bg_cohort"]["integrity_check_sql"], ["bg_ephemeris_engine"]):
            v.append("multi-table declaration / explanation / integrity check / deps of bg_cohort changed")
        fresh_after = env.snapshot("asset_freshness", "asset_id")
        f = fresh_after["bg_cohort"]
        if f["freshness_state"] != "stale" or list(f["reasons"]) != ["registry_changed"]:
            v.append(f"bg_cohort freshness is {f['freshness_state']} {f['reasons']}")
        if fresh_after["bg_parihara_rules"] != fresh_before["bg_parihara_rules"]:
            v.append("an unrelated asset's freshness changed (only bg_cohort may go stale)")
        if set(fresh_after) != set(fresh_before):
            v.append("freshness rows were created or removed")
        # the stored count_sql runs and counts the PRIMARY table only
        with env.admin() as c:
            if c.execute(row["count_sql"]).fetchone()[0] != 3:
                v.append("the scoped count_sql does not return the primary-table count")
        # DOCUMENTED SERVING EFFECT: the dependent ka_kshetra is blocked until bg_cohort is re-receipted
        if _gate(env, "ka_kshetra") != ["bg_cohort(receipt:stale)"]:
            v.append(f"expected the documented gate effect on ka_kshetra, got {_gate(env, 'ka_kshetra')}")
        if env.rows("SELECT count(*) FROM public._migrations_applied WHERE filename = '1270.sql'")[0][0] != 1:
            v.append("tracker row missing")
        return v
    finally:
        env.drop()


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.apply(sql, "1270.sql")
        snap, fresh = env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id")
        notices: list[str] = []
        try:
            env.apply(sql, "1270_again.sql", notices, track=False)
        except Exception as exc:  # noqa: BLE001
            return [f"second run failed: {_msg(exc)}"]
        if env.snapshot("asset_registry", "asset_id") != snap or env.snapshot("asset_freshness", "asset_id") != fresh:
            v.append("a second run changed something / re-fired the trigger")
        if not any("already scoped" in n for n in notices):
            v.append(f"second run did not report the existing scope: {notices}")
        return v
    finally:
        env.drop()


DRIFTS = [
    ("floor_109999", "UPDATE public.asset_registry SET target_floor = 109999 WHERE asset_id = 'bg_cohort'"),
    ("floor_null", "UPDATE public.asset_registry SET target_floor = NULL WHERE asset_id = 'bg_cohort'"),
    ("count_sql_whitespace", "UPDATE public.asset_registry SET count_sql = count_sql || ' ' WHERE asset_id = 'bg_cohort'"),
    ("count_sql_scoped_but_old_floor", "UPDATE public.asset_registry SET count_sql = 'SELECT COUNT(*) FROM bg_synthetic_cohort' WHERE asset_id = 'bg_cohort'"),
    ("count_sql_other", "UPDATE public.asset_registry SET count_sql = 'SELECT COUNT(*) FROM bg_synthetic_cohort_md' WHERE asset_id = 'bg_cohort'"),
    ("target_table", "UPDATE public.asset_registry SET target_table = 'x' WHERE asset_id = 'bg_cohort'"),
]


def sc_guards(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for name, drift in DRIFTS:
        env = Env(cl)
        try:
            seed(env)
            env.run(drift)
            before = env.snapshot("asset_registry", "asset_id")
            fresh = env.snapshot("asset_freshness", "asset_id")
            exc = _try(lambda: env.apply(sql, "1270.sql"))
            if exc is None:
                v.append(f"drift {name}: the migration did not refuse")
            elif "drifted from the audited state" not in str(exc):
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
        env.run("DELETE FROM public.asset_throughput WHERE asset_id = 'bg_cohort'")
        env.run("DELETE FROM public.asset_registry WHERE asset_id = 'bg_cohort'")  # asset_freshness cascades
        notices: list[str] = []
        try:
            env.apply(sql, "1270.sql", notices)
        except Exception as exc:  # noqa: BLE001
            return [f"an absent bg_cohort made the migration fail: {_msg(exc)}"]
        if not any("bg_cohort is not in asset_registry" in n for n in notices):
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
        exc = _try(lambda: env.apply(sql, "1270.sql"))
        if exc is None:
            v.append("a swallowed UPDATE let the migration pass silently")
        return v
    finally:
        env.drop()


SCENARIOS = [sc_apply_once, sc_idempotent, sc_guards, sc_absent, sc_silent_noop]


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
    ("floor 10001", ("target_floor = 10000\n     WHERE", "target_floor = 10001\n     WHERE")),
    ("count scoped to the child table", ("new_count_sql constant text := 'SELECT COUNT(*) FROM bg_synthetic_cohort';", "new_count_sql constant text := 'SELECT COUNT(*) FROM bg_synthetic_cohort_md';")),
    ("floor left unchanged", ("SET count_sql = new_count_sql, target_floor = 10000", "SET count_sql = new_count_sql")),
    ("count_sql left unchanged", ("SET count_sql = new_count_sql, target_floor = 10000", "SET target_floor = 10000")),
    ("audited literal altered", ("(SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count';\n    new_count_sql", "(SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS cnt';\n    new_count_sql")),
    ("drift guard removed", ("IF v_sql IS DISTINCT FROM old_count_sql OR v_floor IS DISTINCT FROM 110000 THEN", "IF false THEN")),
    ("floor guard removed", ("IF v_sql IS DISTINCT FROM old_count_sql OR v_floor IS DISTINCT FROM 110000 THEN", "IF v_sql IS DISTINCT FROM old_count_sql THEN")),
    ("count_sql guard removed", ("IF v_sql IS DISTINCT FROM old_count_sql OR v_floor IS DISTINCT FROM 110000 THEN", "IF v_floor IS DISTINCT FROM 110000 THEN")),
    ("target_table guard removed", ("IF v_target IS DISTINCT FROM 'bg_synthetic_cohort' THEN", "IF false THEN")),
    ("already-scoped skip removed", ("    IF v_sql = new_count_sql AND v_floor = 10000 THEN\n        RAISE NOTICE '1270: bg_cohort count_sql / target_floor are already scoped; skipped';\n        RETURN;\n    END IF;\n", "")),
    ("absent row raises instead of skipping", ("RAISE NOTICE '1270: bg_cohort is not in asset_registry; skipped';\n        RETURN;", "RAISE EXCEPTION '1270: absent';")),
    ("lock_timeout session-wide", ("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '5s';")),
    ("also rewrites the multi-table declaration", ("    -- Post-check: re-read both cells", "    UPDATE asset_registry SET natural_key_partition = 'bg_synthetic_cohort.synthetic_id' WHERE asset_id = 'bg_cohort';\n    -- Post-check: re-read both cells")),
    ("also edits another asset", ("    -- Post-check: re-read both cells", "    UPDATE asset_registry SET target_floor = 1 WHERE asset_id = 'bg_parihara_rules';\n    -- Post-check: re-read both cells")),
    ("row-count check and post-check removed", None),
]


def _build_mutant(spec) -> str:
    s = REAL_SQL
    if spec is None:
        s = s.replace("    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 1 THEN\n        RAISE EXCEPTION '1270: bg_cohort update touched % rows, expected 1', v_rows;\n    END IF;\n", "")
        assert "v_rows <> 1" not in s
        i = s.index("    -- Post-check: re-read both cells")
        j = s.index("END\n$m1270$;")
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
