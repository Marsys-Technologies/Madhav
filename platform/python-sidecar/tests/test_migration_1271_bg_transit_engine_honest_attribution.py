"""Migration 1271 (Suvarna Track I, WAVE-1): bg_transit_engine honest attribution - the refuted 'BPHS Ch.22' citation is
replaced on the nine rows (8 x UNSOURCED, jupiter PARTLY SOURCED), the two integrity digests that cover the citation
column are re-sealed (bg_transit_engine AND bg_transit_rules, whose check embeds the engine digest), the registry
description is corrected and the table/columns are commented. NO NUMERIC VALUE IS CHANGED.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per
available major version (15 and 17). Nothing here touches any real database. The cluster is built the way production
is shaped (P2 rule of the W1 privilege audit): the routine migration runner `amjis_app` is a NOSUPERUSER NOINHERIT
LOGIN role that holds USAGE but NOT CREATE on schema public (owned by `data_plane_schema_owner`); it owns the real
asset_registry / asset_freshness DDL with the real trigger, and bg_transit_engine / bg_transit_rules / bg_transit_moorti
loaded with the audited PRODUCTION rows (tests/fixtures/transit_tables_pre_1271.json, read 2026-10-03) together with the
UNMODIFIED production integrity_check_sql texts, so every pinned md5 guard is exercised for real. The migration is
applied AS amjis_app inside one transaction the way platform/scripts/migrate.ts does.

What it proves (each scenario returns a list of VIOLATIONS; the real file must produce none):
  * apply_once    the fixture reproduces the production digest e2dafc84... and both stored checks read true BEFORE;
                  after: numbers byte-identical, citations equal the writer module's constants, rules/moorti rows
                  untouched, registry changes are exactly the three audited cells, each integrity text differs from the
                  audited one by ONE digest literal and BOTH read true when executed, only bg_transit_rules goes stale
                  and the REAL deps_unsatisfied now reads 'bg_transit_rules(receipt:stale)' for its six dependents (the
                  documented serving effect), comments carry the measured identity gaps recomputed from the rows, no
                  relation/ACL change. LOCKSTEP: module BG_TRANSIT_ENGINE == the rows the migration wrote, and after a
                  writer-style rebuild from the module the re-sealed checks still read true.
  * idempotent    a second run changes nothing and does not re-fire the trigger.
  * guards        a changed value, a changed citation, an extra row, a changed check text (either), a changed description,
                  or a half-applied table-new/registry-old state refuses with the migration's message, changing nothing.
  * empty/missing an empty table is skipped with a NOTICE (fresh bootstrap); a missing engine registry row refuses.
  * silent_noop   a BEFORE UPDATE trigger that swallows the UPDATE (on the table, on the registry) fails loudly.
  * text          the migration carries the module's citation strings byte for byte; the numbers in the module are the
                  audited production numbers.
Mutation tests then rewrite the real SQL and require every mutant to produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL 15/17 with the production-shaped role structure and
the production registry DDL; it does not read production, does not run the inspector or the real writer (the writer is
modelled by loading the module rows), and
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

TAG = "m1271"
_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1271_bg_transit_engine_honest_attribution.sql"
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
from brahmagyan import l0_transit as module  # noqa: E402  (the writer's seed module, edited in lockstep)

FX = json.loads((Path(__file__).resolve().parent / "fixtures" / "transit_tables_pre_1271.json").read_text(encoding="utf-8"))
ENGINE = FX["tables"]["engine"]
RULES = FX["tables"]["rules"]
MOORTI = FX["tables"]["moorti"]
REG = FX["registry"]
OLD_HASH = "e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b"
OLD_CIT = "BPHS Ch.22 (Graha Gati — Planetary Motion)"
DEPENDENTS = ["ka_moorti_nirnaya", "ka_gochara", "ka_sangam", "ka_yojaka", "ka_vedha_gochara", "ka_gochara_resonance"]
HASH_SQL = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,"
            "sign_residence_days,classical_citation)::text, E'\\n' ORDER BY graha COLLATE \"C\"),''),'UTF8')),'hex') FROM bg_transit_engine")
DDL = """
CREATE TABLE public.bg_transit_engine (id serial PRIMARY KEY, graha text NOT NULL UNIQUE, avg_daily_motion_deg double precision NOT NULL,
    zodiac_period_days double precision NOT NULL, sign_residence_days double precision NOT NULL, classical_citation text NOT NULL);
CREATE TABLE public.bg_transit_rules (id integer PRIMARY KEY, rule_type text NOT NULL, graha text NOT NULL, primary_house integer NOT NULL,
    vedha_house integer, phala text NOT NULL, classical_citation text NOT NULL, rule_notes text,
    CONSTRAINT bg_transit_rules_primary_house_check CHECK (primary_house >= 1 AND primary_house <= 12),
    CONSTRAINT bg_transit_rules_rule_type_check CHECK (rule_type = ANY (ARRAY['favourable','unfavourable','vedha','double_transit'])),
    CONSTRAINT bg_transit_rules_vedha_house_check CHECK (vedha_house >= 1 AND vedha_house <= 12),
    CONSTRAINT bg_transit_rules_graha_type_house_unique UNIQUE (graha, rule_type, primary_house));
CREATE TABLE public.bg_transit_moorti (nakshatra_offset integer PRIMARY KEY, moorti_name text NOT NULL, quality_tier integer NOT NULL,
    phala_brief text NOT NULL, classical_citation text NOT NULL, rule_notes text,
    CONSTRAINT bg_transit_moorti_moorti_name_check CHECK (moorti_name = ANY (ARRAY['swarna','rajata','tamra','loha'])),
    CONSTRAINT bg_transit_moorti_nakshatra_offset_check CHECK (nakshatra_offset >= 1 AND nakshatra_offset <= 27),
    CONSTRAINT bg_transit_moorti_quality_tier_check CHECK (quality_tier >= 1 AND quality_tier <= 4));
CREATE TABLE public.asset_throughput (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id), chart_id uuid,
                                      state text NOT NULL, last_built_at timestamptz);
"""


def test_fixture_is_the_audited_pre_state():
    assert len(ENGINE) == 9 and len(RULES) == 76 and len(MOORTI) == 27
    assert {r["classical_citation"] for r in ENGINE} == {OLD_CIT}
    for a, md5 in (("bg_transit_engine", "9c1b1f5b6792fc4643d689e5124fa554"), ("bg_transit_rules", "a3ded694827457ffaf640d24ff1e4057")):
        assert hashlib.md5(REG[a]["integrity_check_sql"].encode()).hexdigest() == md5
    assert hashlib.md5(REG["bg_transit_engine"]["english_description"].encode()).hexdigest() == "3ffe36c1c59b3bfac653fd198ce3cf46"
    assert REG["bg_transit_engine"]["integrity_check_sql"].count(OLD_HASH) == 1 and REG["bg_transit_rules"]["integrity_check_sql"].count(OLD_HASH) == 1


def seed(env: Env, rules_state: str = "fresh") -> None:
    env.run(DDL)
    for t in ("bg_transit_engine", "bg_transit_rules", "bg_transit_moorti", "asset_throughput"):
        env.run(f"ALTER TABLE public.{t} OWNER TO amjis_app")
        env.run(f"GRANT SELECT ON public.{t} TO suvarna_reader")
    c = env._conn()
    for r in ENGINE:
        c.execute("INSERT INTO public.bg_transit_engine (graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation) "
                  "VALUES (%s, %s, %s, %s, %s)", (r["graha"], r["avg_daily_motion_deg"], r["zodiac_period_days"], r["sign_residence_days"], r["classical_citation"]))
    for r in RULES:
        c.execute("INSERT INTO public.bg_transit_rules (id, rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes) "
                  "VALUES (%(id)s, %(rule_type)s, %(graha)s, %(primary_house)s, %(vedha_house)s, %(phala)s, %(classical_citation)s, %(rule_notes)s)", r)
    for r in MOORTI:
        c.execute("INSERT INTO public.bg_transit_moorti VALUES (%(nakshatra_offset)s, %(moorti_name)s, %(quality_tier)s, %(phala_brief)s, %(classical_citation)s, %(rule_notes)s)", r)
    for a in ("bg_transit_engine", "bg_transit_rules"):
        env.add_asset(a, target_table=a, target_floor=9 if a.endswith("engine") else 76, has_writer=True,
                      count_sql=f"SELECT COUNT(*) FROM {a}", integrity_check_sql=REG[a]["integrity_check_sql"],
                      english_description=REG[a]["english_description"])
    for d in DEPENDENTS:
        env.add_asset(d, layer="kala", target_table=d, has_writer=True, depends_on=["bg_transit_rules"])
    env.add_fresh("bg_transit_rules", rules_state)
    c.execute("INSERT INTO public.asset_throughput (asset_id, chart_id, state, last_built_at) VALUES ('bg_transit_rules', NULL, 'lit', '2026-10-01T21:26:00Z')")


def _precondition(env: Env) -> None:
    with env.admin() as c:
        assert c.execute("SELECT has_schema_privilege('amjis_app', 'public', 'CREATE')").fetchone()[0] is False
        assert c.execute("SELECT rolsuper FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
        assert c.execute("SELECT rolinherit FROM pg_roles WHERE rolname = 'amjis_app'").fetchone()[0] is False
        assert c.execute(HASH_SQL).fetchone()[0] == OLD_HASH  # the fixture reproduces the production digest exactly
        for a in ("bg_transit_engine", "bg_transit_rules"):
            assert c.execute(REG[a]["integrity_check_sql"]).fetchone()[0] is True, f"{a}: the audited check is not true on the fixture"
    conn = env.app()
    try:
        assert isinstance(_try(lambda: conn.execute("CREATE TABLE public.zz_should_fail (x int)")), psycopg.errors.InsufficientPrivilege)
    finally:
        conn.close()


def _gate(env: Env, asset_id: str) -> list[str]:
    with env.cl.connect(env.db, "postgres") as c:
        return ar.deps_unsatisfied(c.cursor(row_factory=dict_row), None, asset_id)


def _checks(env: Env) -> dict[str, bool]:
    with env.admin() as c:
        return {a: c.execute(t).fetchone()[0] for a, t in env.rows("SELECT asset_id, integrity_check_sql FROM public.asset_registry "
                                                                    "WHERE asset_id IN ('bg_transit_engine','bg_transit_rules')")}


def _identity_line(g, m, p, r) -> str:
    dm, dr = 360 / p, p / 12
    return f"{g} {abs(m):g} vs {dm:.4f} ({(abs(m) - dm) / dm * 100:+.1f}%), {r:g} vs {dr:.2f} ({(r - dr) / dr * 100:+.1f}%)"


def _engine_rows(env: Env) -> list[tuple]:
    return env.rows("SELECT graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation FROM public.bg_transit_engine ORDER BY graha")


# ---------------------------------------------------------------------------------------------- scenarios
def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        _precondition(env)
        for d in DEPENDENTS:
            if _gate(env, d) != []:
                return [f"fixture: {d} is blocked before the migration"]
        before_engine = _engine_rows(env)
        before_rules, before_moorti = env.snapshot("bg_transit_rules", "id"), env.snapshot("bg_transit_moorti", "nakshatra_offset")
        reg_before, fresh_before = env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id")
        rels_before = env.rows("SELECT relname, relkind::text, pg_get_userbyid(relowner), coalesce(relacl::text,'') FROM pg_class WHERE relnamespace='public'::regnamespace ORDER BY 1")
        try:
            lock_after = env.apply(sql, "1271.sql")
        except Exception as exc:  # noqa: BLE001
            return [f"apply as amjis_app failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        after_engine = _engine_rows(env)
        if [r[:4] for r in after_engine] != [r[:4] for r in before_engine]:
            v.append("a NUMERIC value of bg_transit_engine changed (this migration changes citations only)")
        for r in after_engine:
            want = module.TRANSIT_ENGINE_CITATION_JUPITER if r[0] == "jupiter" else module.TRANSIT_ENGINE_CITATION_UNSOURCED
            if r[4] != want:
                v.append(f"{r[0]}: citation is not the module constant")
        if any("BPHS Ch.22" in r[4] and not r[4].startswith(("UNSOURCED", "PARTLY SOURCED")) for r in after_engine):
            v.append("a row still carries the refuted citation as its attribution")
        if not all(r[4].startswith("UNSOURCED") for r in after_engine if r[0] != "jupiter") or not [r for r in after_engine if r[0] == "jupiter"][0][4].startswith("PARTLY SOURCED"):
            v.append("attribution markers wrong (8 x UNSOURCED, jupiter PARTLY SOURCED)")
        if env.snapshot("bg_transit_rules", "id") != before_rules or env.snapshot("bg_transit_moorti", "nakshatra_offset") != before_moorti:
            v.append("bg_transit_rules / bg_transit_moorti rows changed")
        reg_after = env.snapshot("asset_registry", "asset_id")
        want_changed = {"bg_transit_engine": {"integrity_check_sql", "english_description"}, "bg_transit_rules": {"integrity_check_sql"}}
        if changed_columns(reg_before, reg_after) != want_changed:
            v.append(f"registry cells changed: {changed_columns(reg_before, reg_after)}, expected {want_changed}")
        new_hash = env.rows(HASH_SQL)[0][0]
        for a in ("bg_transit_engine", "bg_transit_rules"):
            t = reg_after[a]["integrity_check_sql"]
            if t.count(new_hash) != 1 or OLD_HASH in t:
                v.append(f"{a}: integrity_check_sql does not carry exactly the new digest")
            if t.replace(new_hash, OLD_HASH) != REG[a]["integrity_check_sql"]:
                v.append(f"{a}: integrity_check_sql differs from the audited text by more than the one digest literal")
        if _checks(env) != {"bg_transit_engine": True, "bg_transit_rules": True}:
            v.append(f"the re-sealed integrity checks do not both read true: {_checks(env)}")
        if "Source: BPHS Ch.22" in reg_after["bg_transit_engine"]["english_description"] or "refuted" not in reg_after["bg_transit_engine"]["english_description"]:
            v.append("registry english_description still claims BPHS Ch.22 / does not say it is refuted")
        f_after = env.snapshot("asset_freshness", "asset_id")
        if f_after["bg_transit_rules"]["freshness_state"] != "stale" or list(f_after["bg_transit_rules"]["reasons"]) != ["registry_changed"]:
            v.append(f"bg_transit_rules freshness is {f_after['bg_transit_rules']}")
        if set(f_after) != set(fresh_before):
            v.append("freshness rows were created/removed (bg_transit_engine has none; only bg_transit_rules may go stale)")
        for d in DEPENDENTS:  # DOCUMENTED SERVING EFFECT
            if _gate(env, d) != ["bg_transit_rules(receipt:stale)"]:
                v.append(f"expected the documented gate effect on {d}, got {_gate(env, d)}")
        # metadata
        tc = env.rows("SELECT obj_description('public.bg_transit_engine'::regclass, 'pg_class')")[0][0] or ""
        for g, m, p, r in [(x["graha"], x["avg_daily_motion_deg"], x["zodiac_period_days"], x["sign_residence_days"]) for x in ENGINE]:
            if _identity_line(g, m, p, r) not in tc:
                v.append(f"table comment lacks the measured identity line for {g}: {_identity_line(g, m, p, r)}")
        for needle in ("MODERN MEAN", "NOT corpus-sourced", "NOT corrected", "yavana_jataka PG900:C1", "not an ephemeris", "1 deg 23 min"):
            if needle not in tc:
                v.append(f"table comment lacks {needle!r}")
        cols = {r[0] for r in env.rows("SELECT a.attname FROM pg_attribute a WHERE a.attrelid = 'public.bg_transit_engine'::regclass AND a.attnum > 0 "
                                       "AND col_description(a.attrelid, a.attnum) IS NOT NULL")}
        if cols != {"avg_daily_motion_deg", "zodiac_period_days", "sign_residence_days", "classical_citation"}:
            v.append(f"column comments on {sorted(cols)}")
        rels_after = env.rows("SELECT relname, relkind::text, pg_get_userbyid(relowner), coalesce(relacl::text,'') FROM pg_class WHERE relnamespace='public'::regnamespace ORDER BY 1")
        if rels_after != rels_before:
            v.append("a relation, owner or ACL in schema public changed")
        # LOCKSTEP: the writer module (this PR) equals what the migration wrote, and a writer rebuild keeps the re-sealed check true
        mod_rows = sorted((r["graha"], r["avg_daily_motion_deg"], r["zodiac_period_days"], r["sign_residence_days"], r["classical_citation"]) for r in module.BG_TRANSIT_ENGINE)
        if mod_rows != after_engine:
            v.append("module BG_TRANSIT_ENGINE != the rows the migration wrote (lockstep broken)")
        env.run("DELETE FROM public.bg_transit_engine")
        for r in module.BG_TRANSIT_ENGINE:
            env.run("INSERT INTO public.bg_transit_engine (graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation) VALUES (%s,%s,%s,%s,%s)",
                    (r["graha"], r["avg_daily_motion_deg"], r["zodiac_period_days"], r["sign_residence_days"], r["classical_citation"]))
        if _checks(env) != {"bg_transit_engine": True, "bg_transit_rules": True}:
            v.append("a writer rebuild from the module rows does not keep the re-sealed checks true")
        if env.rows("SELECT count(*) FROM public._migrations_applied WHERE filename = '1271.sql'")[0][0] != 1:
            v.append("tracker row missing")
        return v
    finally:
        env.drop()


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.apply(sql, "1271.sql")
        snap = (_engine_rows(env), env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id"))
        notices: list[str] = []
        try:
            env.apply(sql, "1271_again.sql", notices, track=False)
        except Exception as exc:  # noqa: BLE001
            return [f"second run failed: {_msg(exc)}"]
        if (_engine_rows(env), env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id")) != snap:
            v.append("a second run changed something / re-fired the trigger")
        if not any("already at the new state" in n for n in notices):
            v.append(f"second run did not report the existing state: {notices}")
        return v
    finally:
        env.drop()


def _tweak_value(e: Env): e.run("UPDATE public.bg_transit_engine SET sign_residence_days = 15 WHERE graha = 'mercury'")
def _tweak_citation(e: Env): e.run("UPDATE public.bg_transit_engine SET classical_citation = 'BPHS Ch.22' WHERE graha = 'sun'")
def _extra_row(e: Env): e.run("INSERT INTO public.bg_transit_engine (graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation) VALUES ('pluto', 1, 1, 1, 'x')")
def _engine_check_changed(e: Env): e.run("UPDATE public.asset_registry SET integrity_check_sql = integrity_check_sql || ' ' WHERE asset_id = 'bg_transit_engine'")
def _rules_check_changed(e: Env): e.run("UPDATE public.asset_registry SET integrity_check_sql = integrity_check_sql || ' ' WHERE asset_id = 'bg_transit_rules'")
def _description_changed(e: Env): e.run("UPDATE public.asset_registry SET english_description = english_description || '!' WHERE asset_id = 'bg_transit_engine'")
def _table_new_registry_old(e: Env):
    for r in ENGINE:
        e.run("UPDATE public.bg_transit_engine SET classical_citation = %s WHERE graha = %s",
              (module.TRANSIT_ENGINE_CITATION_JUPITER if r["graha"] == "jupiter" else module.TRANSIT_ENGINE_CITATION_UNSOURCED, r["graha"]))
def _rules_row_changed(e: Env): e.run("UPDATE public.bg_transit_rules SET phala = phala || '!' WHERE id = (SELECT min(id) FROM public.bg_transit_rules)")


DRIFTS = [("engine_value_changed", _tweak_value), ("engine_citation_changed", _tweak_citation), ("engine_extra_row", _extra_row),
          ("engine_check_changed", _engine_check_changed), ("rules_check_changed", _rules_check_changed),
          ("description_changed", _description_changed), ("table_new_registry_old", _table_new_registry_old)]


def sc_guards(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for name, drift in DRIFTS:
        env = Env(cl)
        try:
            seed(env)
            drift(env)
            before = (_engine_rows(env), env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id"))
            exc = _try(lambda: env.apply(sql, "1271.sql"))
            if exc is None:
                v.append(f"drift {name}: the migration did not refuse")
            elif "drifted from the audited state" not in str(exc):
                v.append(f"drift {name}: refused with the wrong message: {_msg(exc)}")
            if (_engine_rows(env), env.snapshot("asset_registry", "asset_id"), env.snapshot("asset_freshness", "asset_id")) != before:
                v.append(f"drift {name}: state changed although the migration refused")
            if env.rows("SELECT count(*) FROM public._migrations_applied")[0][0] != 0:
                v.append(f"drift {name}: tracker row written for a refused migration")
            if env.rows("SELECT obj_description('public.bg_transit_engine'::regclass, 'pg_class')")[0][0] is not None:
                v.append(f"drift {name}: the table comment was written although the migration refused")
        finally:
            env.drop()
    return v


def sc_empty_and_registry_missing(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        seed(env)
        env.run("DELETE FROM public.bg_transit_engine")
        notices: list[str] = []
        before = env.snapshot("asset_registry", "asset_id")
        try:
            env.apply(sql, "1271.sql", notices)
        except Exception as exc:  # noqa: BLE001
            v.append(f"an empty bg_transit_engine made the migration fail: {_msg(exc)}")
        else:
            if not any("is empty" in n for n in notices):
                v.append("empty table was skipped silently (no NOTICE)")
            if env.snapshot("asset_registry", "asset_id") != before:
                v.append("the registry changed although the table was empty")
    finally:
        env.drop()
    env = Env(cl)
    try:
        seed(env)
        env.run("UPDATE public.asset_registry SET depends_on = '{}' WHERE 'bg_transit_engine' = ANY(depends_on)")
        env.run("DELETE FROM public.asset_registry WHERE asset_id = 'bg_transit_engine'")
        exc = _try(lambda: env.apply(sql, "1271.sql"))
        if exc is None or "bg_transit_engine is not in asset_registry" not in str(exc):
            v.append(f"a missing engine registry row did not refuse: {_msg(exc)}")
    finally:
        env.drop()
    return v


def sc_silent_noop(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for table in ("bg_transit_engine", "asset_registry"):
        env = Env(cl)
        try:
            seed(env)
            env.run("CREATE FUNCTION public.zz_swallow() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
            env.run(f"CREATE TRIGGER zz_swallow BEFORE UPDATE ON public.{table} FOR EACH ROW EXECUTE FUNCTION public.zz_swallow()")
            exc = _try(lambda: env.apply(sql, "1271.sql"))
            if exc is None:
                v.append(f"a swallowed UPDATE on {table} let the migration pass silently")
        finally:
            env.drop()
    return v


SCENARIOS = [sc_apply_once, sc_idempotent, sc_guards, sc_empty_and_registry_missing, sc_silent_noop]


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


def test_migration_text_carries_exactly_the_module_constants():
    """The citations in the migration are byte-equal to the writer module's (lockstep), independent of any database."""
    assert module.TRANSIT_ENGINE_CITATION_UNSOURCED in REAL_SQL and module.TRANSIT_ENGINE_CITATION_JUPITER in REAL_SQL
    assert module.BPHS_CH29 and not hasattr(module, "BPHS_CH22"), "the refuted BPHS_CH22 constant must be gone from the seed module"
    assert all(r["classical_citation"] in (module.TRANSIT_ENGINE_CITATION_UNSOURCED, module.TRANSIT_ENGINE_CITATION_JUPITER) for r in module.BG_TRANSIT_ENGINE)
    # the numbers in the module are exactly the audited production numbers (this change must not move one)
    prod = sorted((r["graha"], r["avg_daily_motion_deg"], r["zodiac_period_days"], r["sign_residence_days"]) for r in ENGINE)
    assert sorted((r["graha"], r["avg_daily_motion_deg"], r["zodiac_period_days"], r["sign_residence_days"]) for r in module.BG_TRANSIT_ENGINE) == prod


MUTANTS = [
    ("new digest literal wrong", ("new_hash   constant text := 'e5c09a11", "new_hash   constant text := 'f5c09a11")),
    ("old digest literal wrong", ("old_hash   constant text := 'e2dafc84", "old_hash   constant text := 'f2dafc84")),
    ("jupiter not special-cased", ("CASE WHEN graha = 'jupiter' THEN cit_jupiter ELSE cit_unsourced END", "cit_unsourced")),
    ("a numeric value also changed", ("SET classical_citation = CASE WHEN graha = 'jupiter' THEN cit_jupiter ELSE cit_unsourced END",
                                      "SET avg_daily_motion_deg = CASE WHEN graha = 'mercury' THEN 4.0923 ELSE avg_daily_motion_deg END,\n           classical_citation = CASE WHEN graha = 'jupiter' THEN cit_jupiter ELSE cit_unsourced END")),
    ("rules check not re-sealed", ("    UPDATE asset_registry\n       SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash)\n     WHERE asset_id = 'bg_transit_rules' AND md5(integrity_check_sql) = rules_sql_md5;\n    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 1 THEN\n        RAISE EXCEPTION '1271: bg_transit_rules registry update touched % rows, expected 1', v_rows;\n    END IF;\n", "")),
    ("engine check not re-sealed", ("SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash), english_description = new_desc", "SET english_description = new_desc")),
    ("description not updated", ("SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash), english_description = new_desc", "SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash)")),
    ("engine check md5 guard removed", ("OR md5(v_engine_sql) IS DISTINCT FROM engine_sql_md5 OR md5(v_rules_sql) IS DISTINCT FROM rules_sql_md5", "OR md5(v_rules_sql) IS DISTINCT FROM rules_sql_md5")),
    ("rules check md5 guard removed", ("OR md5(v_engine_sql) IS DISTINCT FROM engine_sql_md5 OR md5(v_rules_sql) IS DISTINCT FROM rules_sql_md5", "OR md5(v_engine_sql) IS DISTINCT FROM engine_sql_md5")),
    ("description md5 guard removed", ("       OR md5(v_desc) IS DISTINCT FROM old_desc_md5\n", "")),
    ("table digest guard removed", ("IF v_hash IS DISTINCT FROM old_hash\n       OR md5(v_engine_sql)", "IF false\n       OR md5(v_engine_sql)")),
    ("empty-table skip removed", ("    IF v_n = 0 THEN\n        RAISE NOTICE '1271: bg_transit_engine is empty (fresh bootstrap, rows come from the writer); skipped';\n        RETURN;\n    END IF;\n", "")),
    ("already-applied skip removed", ("       AND strpos(v_rules_sql, new_hash) > 0 AND strpos(v_rules_sql, old_hash) = 0 THEN\n        RAISE NOTICE '1271: bg_transit_engine citations and digests are already at the new state; skipped';\n        RETURN;\n    END IF;\n", "       AND false THEN\n        RETURN;\n    END IF;\n")),
    ("registry-missing guard removed", ("    IF NOT FOUND THEN\n        RAISE EXCEPTION '1271: bg_transit_engine is not in asset_registry; refusing (registry contract unknown)';\n    END IF;\n", "")),
    ("em dash chr(8212) wrong", ("chr(8212)", "chr(8211)")),
    ("table comment removed", ("COMMENT ON TABLE bg_transit_engine IS", "SELECT 1 /* COMMENT ON TABLE bg_transit_engine IS")),
    ("lock_timeout session-wide", ("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '5s';")),
    ("also edits a rules row", ("    -- 2. re-seal both integrity checks", "    UPDATE bg_transit_rules SET phala = phala || '!' WHERE id = (SELECT min(id) FROM bg_transit_rules);\n    -- 2. re-seal both integrity checks")),
    ("row-count and post-checks removed", None),
]


def _build_mutant(spec) -> str:
    s = REAL_SQL
    if spec is None:
        for pat in ("    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 9 THEN\n        RAISE EXCEPTION '1271: citation update touched % rows, expected 9', v_rows;\n    END IF;\n",
                    "    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 1 THEN\n        RAISE EXCEPTION '1271: bg_transit_engine registry update touched % rows, expected 1', v_rows;\n    END IF;\n",
                    "    GET DIAGNOSTICS v_rows = ROW_COUNT;\n    IF v_rows <> 1 THEN\n        RAISE EXCEPTION '1271: bg_transit_rules registry update touched % rows, expected 1', v_rows;\n    END IF;\n"):
            assert pat in s
            s = s.replace(pat, "")
        i = s.index("    -- Post-check: the two re-sealed checks themselves must read true")
        j = s.index("END\n$m1271$;")
        return s[:i] + s[j:]
    if spec[0].startswith("COMMENT ON TABLE"):
        # neuter the whole table-comment statement (it spans one long dollar-quoted literal)
        i = s.index("COMMENT ON TABLE bg_transit_engine IS $c$")
        j = s.index("$c$;", i + 45) + 4
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
