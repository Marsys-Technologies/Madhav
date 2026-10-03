"""Migration 1267 (Suvarna Track I, TI-L0-08): the registry side of the rider relation - a nullable self-referencing
column asset_registry.producer_asset_id (FK + not-self CHECK), set for bg_nakshatra_medical and bg_sign_medical
(-> bg_medical_mappings) and bg_transit_engine (-> bg_transit_rules).

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per
available major version (15 and 17). Nothing here touches any real database. The cluster is built the way production
is shaped (P2 rule of the W1 privilege audit): the routine migration runner `amjis_app` is a NOSUPERUSER NOINHERIT
LOGIN role that holds USAGE but NOT CREATE on schema public (owned by `data_plane_schema_owner`); it owns the real
asset_registry / asset_freshness / _migrations_applied DDL (copied from a pg_dump of production) with the real
`nirmana_registry_receipt_invalidation` trigger and function. The migration is applied AS amjis_app inside one
transaction the way platform/scripts/migrate.ts does (BEGIN; <sql>; tracker INSERT; COMMIT).

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once    the column exists (nullable text), the FK (ON DELETE RESTRICT) and the not-self CHECK are enforced, the
                  three riders declare exactly their audited producer and no other cell of any row changed; NO
                  relation/ACL changed and no schema object was created; the registry trigger did NOT fire (no
                  freshness row changed); the reader role sees the column through its existing table grant; the tracker
                  row is written; lock_timeout is transaction-local.
  * idempotent    a second run changes nothing and reports the column and the three relations as already present.
  * partial       a database where the column, the constraints and one relation already exist converges the rest.
  * guards        a missing / inactive / writer-less / non-data producer, a drifted rider identity, or a rider that
                  already declares a DIFFERENT producer refuses with the migration's own message and rolls everything
                  back (the column does not exist afterwards).
  * absent        a rider row that does not exist is skipped with a NOTICE, the others still apply.
  * silent_noop   a BEFORE UPDATE trigger that swallows the UPDATE makes the migration fail loudly.
Mutation tests then rewrite the real SQL and require every mutant to produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL 15/17 with the production-shaped role structure and
the production registry DDL; it does not read production, does not run the inspector (nothing reads the new column yet; the
inspector reading it is Track E's path and not part of this file), and
`REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import psycopg
import pytest

TAG = "m1267"
_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1267_asset_registry_rider_producer_relation.sql"
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
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
            c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
            c.execute("GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner")
            c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, suvarna_reader")
            c.execute(ddl)
            self._own_everything(c)

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

    def run(self, stmt: str, params=None) -> None:
        """Fixture DML/DDL as the superuser (the app role cannot CREATE in schema public, like production)."""
        with self.admin() as c:
            c.execute(stmt, params)

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
        with self.admin() as c:
            c.execute(f"INSERT INTO public.asset_registry ({', '.join(names)}) VALUES ({', '.join(['%s'] * len(names))})",
                      [base[n] for n in names])

    def add_fresh(self, asset_id: str, state: str = "fresh", reasons: str = "[]") -> None:
        with self.admin() as c:
            c.execute("INSERT INTO public.asset_freshness (asset_id, partition_key, freshness_state, reasons, receipt_version, observed_at) "
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
RIDERS = {"bg_nakshatra_medical": "bg_medical_mappings", "bg_sign_medical": "bg_medical_mappings",
          "bg_transit_engine": "bg_transit_rules"}


def seed(env: Env) -> None:
    for prod in ("bg_medical_mappings", "bg_transit_rules"):
        env.add_asset(prod, target_table=prod, count_sql=f"SELECT COUNT(*) FROM {prod}", target_floor=10, has_writer=True)
    env.add_asset("bg_nakshatra_medical", target_table="bg_nakshatra_medical", target_floor=27)
    env.add_asset("bg_sign_medical", target_table="bg_sign_medical", target_floor=12, has_writer=True)
    env.add_asset("bg_transit_engine", target_table="bg_transit_engine", target_floor=9)
    env.add_asset("bg_parihara_rules", target_table="bg_parihara_rules", target_floor=449, has_writer=True)
    env.add_fresh("bg_parihara_rules")
    env.add_fresh("bg_transit_rules")
    env.run("GRANT SELECT ON public.asset_registry TO suvarna_reader")


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


def _strip(snap: dict) -> dict:
    return {k: {c: v for c, v in row.items() if c != "producer_asset_id"} for k, row in snap.items()}


def _relations(env: Env) -> list[tuple]:
    return env.rows("SELECT relname, relkind::text, pg_get_userbyid(relowner), coalesce(relacl::text, '') FROM pg_class "
                    "WHERE relnamespace = 'public'::regnamespace ORDER BY relname")


def _column_present(env: Env) -> bool:
    return env.rows("SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' "
                    "AND table_name = 'asset_registry' AND column_name = 'producer_asset_id'")[0][0] == 1


# ---------------------------------------------------------------------------------------------- scenarios
def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        _precondition(env)
        before = env.snapshot("asset_registry", "asset_id")
        fresh_before = env.snapshot("asset_freshness", "asset_id")
        rels_before = _relations(env)
        notices: list[str] = []
        try:
            lock_after = env.apply(sql, "1267.sql", notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply as amjis_app failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after = env.snapshot("asset_registry", "asset_id")
        if not _column_present(env):
            return v + ["producer_asset_id column missing"]
        col = env.rows("SELECT data_type, is_nullable FROM information_schema.columns WHERE table_name = 'asset_registry' "
                       "AND column_name = 'producer_asset_id'")[0]
        if tuple(col) != ("text", "YES"):
            v.append(f"column is {col}, expected ('text','YES')")
        declared = {k: r["producer_asset_id"] for k, r in after.items() if r["producer_asset_id"] is not None}
        if declared != RIDERS:
            v.append(f"declared relations are {declared}, expected {RIDERS}")
        if _strip(after) != _strip(before):
            v.append("a cell other than producer_asset_id changed in asset_registry")
        if env.snapshot("asset_freshness", "asset_id") != fresh_before:
            v.append("the registry trigger fired / freshness changed")
        if _relations(env) != rels_before:
            v.append("a relation, owner or ACL changed (a schema object was created or granted)")
        fk = env.rows("SELECT confdeltype::text, pg_get_constraintdef(oid) FROM pg_constraint "
                      "WHERE conname = 'asset_registry_producer_asset_id_fkey'")
        if not fk or fk[0][0] != "r" or "REFERENCES asset_registry(asset_id)" not in fk[0][1]:
            v.append(f"FK missing or not ON DELETE RESTRICT: {fk}")
        if not env.rows("SELECT 1 FROM pg_constraint WHERE conname = 'asset_registry_producer_not_self'"):
            v.append("not-self CHECK missing")
        if env.rows("SELECT count(*) FROM public._migrations_applied WHERE filename = '1267.sql'")[0][0] != 1:
            v.append("tracker row missing")
        # the constraints are ENFORCED (each in its own rolled-back transaction)
        for label, stmt, exc_t in (
            ("FK to a missing asset", "UPDATE public.asset_registry SET producer_asset_id = 'no_such_asset' WHERE asset_id = 'bg_parihara_rules'",
             psycopg.errors.ForeignKeyViolation),
            ("self-reference", "UPDATE public.asset_registry SET producer_asset_id = asset_id WHERE asset_id = 'bg_parihara_rules'",
             psycopg.errors.CheckViolation),
            ("deleting a referenced producer", "DELETE FROM public.asset_registry WHERE asset_id = 'bg_medical_mappings'",
             psycopg.errors.ForeignKeyViolation),
        ):
            conn = env.app()
            try:
                exc = _try(lambda: conn.execute(stmt))
                if not isinstance(exc, exc_t):
                    v.append(f"{label} was not refused ({type(exc).__name__ if exc else 'accepted'})")
            finally:
                conn.rollback()
                conn.close()
        # the reader keeps working through its existing table grant
        with env.cl.connect(env.db, "suvarna_reader") as rc:
            got = rc.execute("SELECT producer_asset_id FROM public.asset_registry WHERE asset_id = 'bg_transit_engine'").fetchone()
            if got != ("bg_transit_rules",):
                v.append(f"reader cannot read the new column: {got}")
        return v
    finally:
        env.drop()


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.apply(sql, "1267.sql")
        snap, fresh, rels = env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id"), _relations(env)
        notices: list[str] = []
        try:
            env.apply(sql, "1267_again.sql", notices, track=False)
        except Exception as exc:  # noqa: BLE001
            return [f"second run failed: {_msg(exc)}"]
        if (env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id"), _relations(env)) != (snap, fresh, rels):
            v.append("a second run changed something")
        if sum("already declares producer" in n for n in notices) != 3:
            v.append(f"second run did not report three existing relations: {notices}")
        return v
    finally:
        env.drop()


def sc_partial(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.run("ALTER TABLE public.asset_registry ADD COLUMN producer_asset_id text")
        env.run("ALTER TABLE public.asset_registry ADD CONSTRAINT asset_registry_producer_asset_id_fkey "
                "FOREIGN KEY (producer_asset_id) REFERENCES public.asset_registry(asset_id) ON DELETE RESTRICT")
        env.run("UPDATE public.asset_registry SET producer_asset_id = 'bg_medical_mappings' WHERE asset_id = 'bg_sign_medical'")
        try:
            env.apply(sql, "1267.sql")
        except Exception as exc:  # noqa: BLE001
            return [f"partial-state run failed: {_msg(exc)}"]
        declared = {r[0]: r[1] for r in env.rows("SELECT asset_id, producer_asset_id FROM public.asset_registry WHERE producer_asset_id IS NOT NULL")}
        if declared != RIDERS:
            v.append(f"partial state did not converge to the audited relations: {declared}")
        if not env.rows("SELECT 1 FROM pg_constraint WHERE conname = 'asset_registry_producer_not_self'"):
            v.append("the missing not-self CHECK was not added on convergence")
        return v
    finally:
        env.drop()


DRIFTS = [
    ("producer_missing", "DELETE FROM public.asset_registry WHERE asset_id = 'bg_medical_mappings'", "missing, inactive"),
    ("producer_inactive", "UPDATE public.asset_registry SET is_active = false WHERE asset_id = 'bg_transit_rules'", "missing, inactive"),
    ("producer_no_writer", "UPDATE public.asset_registry SET has_writer = false WHERE asset_id = 'bg_transit_rules'", "missing, inactive"),
    ("producer_service", "UPDATE public.asset_registry SET asset_kind = 'service' WHERE asset_id = 'bg_medical_mappings'", "missing, inactive"),
    ("rider_target_table", "UPDATE public.asset_registry SET target_table = 'x' WHERE asset_id = 'bg_sign_medical'", "drifted from the audited state"),
    ("rider_asset_kind", "UPDATE public.asset_registry SET asset_kind = 'artifact' WHERE asset_id = 'bg_transit_engine'", "drifted from the audited state"),
    ("other_producer_declared",
     "ALTER TABLE public.asset_registry ADD COLUMN producer_asset_id text; "
     "UPDATE public.asset_registry SET producer_asset_id = 'bg_transit_rules' WHERE asset_id = 'bg_nakshatra_medical'",
     "refusing to overwrite"),
]


def sc_guards(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for name, drift, needle in DRIFTS:
        env = Env(cl)
        try:
            seed(env)
            env.run(drift)
            had_column = _column_present(env)
            before = env.snapshot("asset_registry", "asset_id")
            exc = _try(lambda: env.apply(sql, "1267.sql"))
            if exc is None:
                v.append(f"drift {name}: the migration did not refuse")
            elif needle not in str(exc):
                v.append(f"drift {name}: refused with the wrong message: {_msg(exc)}")
            if _column_present(env) != had_column:
                v.append(f"drift {name}: the column state changed although the migration refused (DDL not rolled back)")
            if env.snapshot("asset_registry", "asset_id") != before:
                v.append(f"drift {name}: registry changed although the migration refused")
            if env.rows("SELECT count(*) FROM public._migrations_applied")[0][0] != 0:
                v.append(f"drift {name}: tracker row written for a refused migration")
        finally:
            env.drop()
    return v


def sc_absent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for gone in RIDERS:
        env = Env(cl)
        try:
            seed(env)
            env.run("DELETE FROM public.asset_registry WHERE asset_id = %s", (gone,))
            notices: list[str] = []
            try:
                env.apply(sql, "1267.sql", notices)
            except Exception as exc:  # noqa: BLE001
                v.append(f"absent {gone} made the migration fail: {_msg(exc)}")
                continue
            if not any(f"rider {gone} is not in asset_registry" in n for n in notices):
                v.append(f"absent {gone} was skipped silently (no NOTICE)")
            declared = {r[0] for r in env.rows("SELECT asset_id FROM public.asset_registry WHERE producer_asset_id IS NOT NULL")}
            if declared != set(RIDERS) - {gone}:
                v.append(f"absent {gone}: the other riders were not declared: {declared}")
        finally:
            env.drop()
    return v


def sc_silent_noop(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.run("CREATE FUNCTION public.zz_swallow() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
        env.run("CREATE TRIGGER zz_swallow BEFORE UPDATE ON public.asset_registry FOR EACH ROW EXECUTE FUNCTION public.zz_swallow()")
        exc = _try(lambda: env.apply(sql, "1267.sql"))
        if exc is None:
            v.append("a swallowed UPDATE let the migration pass silently")
        return v
    finally:
        env.drop()


SCENARIOS = [sc_apply_once, sc_idempotent, sc_partial, sc_guards, sc_absent, sc_silent_noop]


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
    ("FK replaced by a trivial CHECK",
     ("            ADD CONSTRAINT asset_registry_producer_asset_id_fkey\n            FOREIGN KEY (producer_asset_id) REFERENCES asset_registry(asset_id) ON DELETE RESTRICT;",
      "            ADD CONSTRAINT asset_registry_producer_asset_id_fkey\n            CHECK (true);")),
    ("FK made ON DELETE CASCADE", ("ON DELETE RESTRICT;", "ON DELETE CASCADE;")),
    ("not-self CHECK weakened", ("CHECK (producer_asset_id IS NULL OR producer_asset_id <> asset_id);", "CHECK (producer_asset_id IS NULL OR producer_asset_id <> 'zzz');")),
    ("producer has_writer guard removed", (" OR p_writer IS DISTINCT FROM true THEN", " THEN")),
    ("producer is_active guard removed", ("OR p_active IS DISTINCT FROM true OR", "OR")),
    ("producer asset_kind guard removed", (" OR p_kind IS DISTINCT FROM 'data'", "")),
    ("overwrite of a different producer allowed",
     ("            RAISE EXCEPTION '1267: rider % already declares producer % (audited: %); refusing to overwrite',",
      "            RAISE NOTICE '1267: rider % already declares producer % (audited: %); refusing to overwrite',")),
    ("transit engine given the medical producer", ("WHEN 'bg_transit_engine' THEN 'bg_transit_rules' ELSE 'bg_medical_mappings' END;\n\n        SELECT",
                                                    "WHEN 'bg_transit_engine' THEN 'bg_medical_mappings' ELSE 'bg_medical_mappings' END;\n\n        SELECT")),
    ("bg_sign_medical dropped from the riders", ("ARRAY['bg_nakshatra_medical', 'bg_sign_medical', 'bg_transit_engine'] LOOP", "ARRAY['bg_nakshatra_medical', 'bg_transit_engine'] LOOP")),
    ("rider identity guard removed", ("IF v_kind IS DISTINCT FROM 'data' OR v_target IS DISTINCT FROM v_rider THEN", "IF false THEN")),
    ("ADD COLUMN not idempotent", ("ADD COLUMN IF NOT EXISTS producer_asset_id text;", "ADD COLUMN producer_asset_id text;")),
    ("constraint existence check removed (FK)",
     ("    IF NOT EXISTS (SELECT 1 FROM pg_constraint\n                    WHERE conrelid = 'public.asset_registry'::regclass AND conname = 'asset_registry_producer_asset_id_fkey') THEN",
      "    IF true THEN")),
    ("lock_timeout session-wide", ("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '5s';")),
    ("also touches a trigger column (has_writer)", ("    -- Post-check: re-read the catalog",
                                                      "    UPDATE asset_registry SET has_writer = true WHERE asset_id = 'bg_nakshatra_medical';\n    -- Post-check: re-read the catalog")),
    ("an unrelated asset also declared a producer", ("    -- Post-check: re-read the catalog",
                                                       "    UPDATE asset_registry SET producer_asset_id = 'bg_transit_rules' WHERE asset_id = 'bg_parihara_rules';\n    -- Post-check: re-read the catalog")),
    ("row-count check and post-check removed", None),
]


def _build_mutant(spec) -> str:
    if spec is None:
        s = REAL_SQL
        s = s.replace("            GET DIAGNOSTICS v_rows = ROW_COUNT;\n            IF v_rows <> 1 THEN\n                RAISE EXCEPTION '1267: setting producer_asset_id of % touched % rows, expected 1', v_rider, v_rows;\n            END IF;\n", "")
        assert "v_rows <> 1" not in s
        i = s.index("    -- Post-check: re-read the catalog")
        j = s.index("END\n$m1267$;")
        return s[:i] + s[j:]
    return mutate(REAL_SQL, *spec)


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
