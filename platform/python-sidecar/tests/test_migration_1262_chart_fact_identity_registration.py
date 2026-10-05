"""Migration 1262 (Suvarna, S-L2 blocker B5): register the Fact Identity Index as asset `ga_fact_identity` and
GRANT SELECT ON chart_fact_identity TO data_plane_builder.

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per available
major version (15 = production, 17). Nothing here touches any real database. The cluster is built the way production is shaped
(catalog read as the reader role 2026-10-03):
  * schema public is owned by data_plane_schema_owner, PUBLIC has no access, the migration role `amjis_app` has USAGE without CREATE;
  * chart_facts is owned by data_plane_l1_owner (builder arwd, amjis_app r, ...), chart_fact_identity and asset_registry and
    build_runs are owned by amjis_app, with production's ACL on chart_fact_identity (the builder has NO privilege), asset_registry
    carries production's exact column list / CHECKs / PK and its AFTER UPDATE receipt-invalidation trigger (a stub that RAISES, so any
    UPDATE the migration issued would fail the test);
  * the migration is applied AS amjis_app in ONE transaction (BEGIN; sql; COMMIT), like platform/scripts/migrate.ts.

Each scenario returns a list of VIOLATIONS; the real file must produce none. What they prove:
  apply_once        the builder cannot SELECT before (InsufficientPrivilege, then InFailedSqlTransaction) and can after; it holds SELECT and
                    NO other privilege (effective + column level), cannot write; the relacl diff over ALL relations is exactly
                    `data_plane_builder=r/amjis_app` on chart_fact_identity; the registry row is present exactly once with the intended
                    shape; every other registry row is byte-identical; the receipt-invalidation trigger did not fire; lock_timeout does
                    not leak past COMMIT.
  idempotent        a second apply changes nothing (one registry row, same ACL, same other rows) and reports the grant no-op.
  count_sql         evaluates (as written, `$1`, via PREPARE) against a two-chart fixture: per-chart counts, 0 for an unknown chart.
  integrity         the integrity SQL is TRUE on the consistent fixture and FALSE on each crafted defect: empty index, orphan (FK dropped),
                    wrong chart, wrong build, stale subject, stale key; TRUE again after repair; it runs as amjis_app AND as the builder.
  guards            active build run (planned / running / paused) refuses; completed / failed / stopped do not; missing role / table;
                    a non-owner executor refuses with the owner message BEFORE any write; the WARN-only non-owner GRANT is caught by the
                    post-check even with that guard removed.
  divergent_row     a pre-existing wrong registry row makes the migration fail and roll back whole (no grant either).
Mutation tests then rewrite the real SQL (grant removed / to PUBLIC / ALL, post-check and read-back neutered, guards removed, DO UPDATE,
unscoped count_sql, each integrity clause dropped, writer/active flags flipped, lock_timeout removed ...) and require EVERY mutant to
produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL with the production-shaped role structure; it does not read
production. The detector semantics of the integrity SQL are proven on crafted fixtures only; the Python-side corrected G-IDX check
(rows == parsed, gap == 0, reason set) is NOT reproduced here (see the migration header). `REQUIRE_PG_BINARIES=1` turns a missing
binary from a skip into a failure.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import errors as pgerr

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1262_chart_fact_identity_asset_registration.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

ASSET_ID = "ga_fact_identity"
BUILDER_ENTRY = "data_plane_builder=r/amjis_app"
EXTRA_PRIVS = ["INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]
CHART_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CHART_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
BUILD_A = "a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1"
BUILD_B = "b2b2b2b2-b2b2-4b2b-8b2b-b2b2b2b2b2b2"
UNKNOWN_CHART = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
N_IDENT_A, N_IDENT_B, N_FACTS_PER_CHART = 4, 3, 6  # identity rows < facts: identity-free facts have no row

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", "/tmp")  # must be SHORT (unix socket path limit)
VERSIONS = ["15", "17"]

# --------------------------------------------------------------------------- production shape (read from the catalog)
ROLES = [
    ("amjis_app", "LOGIN NOINHERIT"),
    ("data_plane_builder", "LOGIN NOINHERIT"),
    ("data_plane_migrator", "LOGIN NOINHERIT"),
    ("data_plane_verifier", "LOGIN NOINHERIT"),
    ("suvarna_reader", "LOGIN NOINHERIT"),
    ("retrieval_census_ro", "LOGIN INHERIT"),
    ("nirmana_campaign_control_writer", "LOGIN NOINHERIT"),
    ("nirmana_evidence_ingress_writer", "LOGIN NOINHERIT"),
    ("data_plane_l1_owner", "NOLOGIN NOINHERIT"),
    ("data_plane_l2_owner", "NOLOGIN NOINHERIT"),
    ("data_plane_schema_owner", "NOLOGIN NOINHERIT"),
    ("role_orchestrator", "NOLOGIN INHERIT"),
    ("role_jobs", "NOLOGIN INHERIT"),
    ("role_sidecar", "NOLOGIN INHERIT"),
    ("role_web_serve", "NOLOGIN INHERIT"),
    ("utkarsha_builder", "NOLOGIN INHERIT"),
    ("outsider", "LOGIN NOINHERIT"),  # a non-owner executor with no privilege on the index or the registry
    ("registry_writer", "LOGIN NOINHERIT"),  # a non-owner executor that CAN insert registry rows (reaches the GRANT, which then only WARNs)
]

CHART_FACTS_DDL = """
CREATE TABLE public.chart_facts (
  fact_id text NOT NULL PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL,
  fact_category text NOT NULL, fact_subject text NOT NULL, fact_key text NOT NULL, fact_value_text text, fact_value_num numeric,
  fact_value_jsonb jsonb, unit text, citation_ref text NOT NULL, citation_human text NOT NULL, source_calculation text NOT NULL,
  verification_pass_status text NOT NULL, engine_version text NOT NULL, salience_formula_ver text, computed_at timestamptz NOT NULL,
  tolerance_arcsec double precision, near_sign_boundary_flag boolean DEFAULT false, near_nakshatra_boundary_flag boolean DEFAULT false,
  vargottama_flag_at_point boolean DEFAULT false, formula_provenance_text text, cross_ayanamsha_divergence_arcsec double precision DEFAULT 0.0,
  formula_id text)
"""

# migration 552, verbatim column list
IDENTITY_DDL = """
CREATE TABLE public.chart_fact_identity (
  fact_id TEXT PRIMARY KEY REFERENCES public.chart_facts(fact_id) ON DELETE CASCADE,
  chart_id UUID NOT NULL, entity_kind TEXT NOT NULL, graha_code TEXT NULL, graha_code_secondary TEXT NULL,
  house_num SMALLINT NULL CHECK (house_num BETWEEN 1 AND 12), house_num_secondary SMALLINT NULL CHECK (house_num_secondary BETWEEN 1 AND 12),
  varga_id TEXT NULL, sign_num SMALLINT NULL CHECK (sign_num BETWEEN 1 AND 12), parse_rule TEXT NOT NULL, parsed_from TEXT NOT NULL,
  build_id UUID NULL, computed_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX chart_fact_identity_chart_id_idx ON public.chart_fact_identity (chart_id)
"""

ASSET_REGISTRY_DDL = """
CREATE TABLE public.asset_registry (
  asset_id text NOT NULL, layer text NOT NULL, sort_order integer NOT NULL, sanskrit_name text NOT NULL, english_name text NOT NULL,
  english_description text NOT NULL, storage_type text NOT NULL, target_table text, count_sql text, size_sql text, target_floor integer,
  expected_volume_formula text, expected_volume_inputs jsonb, volume_explanation text, depends_on text[] DEFAULT ARRAY[]::text[],
  scope text NOT NULL, is_active boolean DEFAULT true, estimated_seconds integer, created_at timestamptz DEFAULT now(), clear_tables text[],
  asset_type text NOT NULL DEFAULT 'data', layer_name text, layer_index text, provides_apis jsonb, health_probe jsonb,
  catalog_status text NOT NULL DEFAULT 'DRAFT', rebuild_on_probe_fail boolean NOT NULL DEFAULT false, integrity_check_sql text,
  has_substeps boolean NOT NULL DEFAULT false, asset_kind text NOT NULL DEFAULT 'data', service_health text, last_invoked_at timestamptz,
  last_selftest_at timestamptz, selftest_detail jsonb, has_writer boolean NOT NULL DEFAULT false, writer_timeout_seconds integer NOT NULL DEFAULT 600,
  domain text, rung text, superseded_by text, data_disposition text, natural_key_partition text, dead_flag boolean,
  CONSTRAINT asset_registry_pkey PRIMARY KEY (asset_id),
  CONSTRAINT asset_registry_asset_kind_check CHECK (asset_kind = ANY (ARRAY['data','service','artifact'])),
  CONSTRAINT asset_registry_asset_type_check CHECK (asset_type = ANY (ARRAY['data','service'])),
  CONSTRAINT asset_registry_catalog_status_check CHECK (catalog_status = ANY (ARRAY['CURRENT','DRAFT','RETIRED'])),
  CONSTRAINT asset_registry_domain_check CHECK (domain IS NULL OR domain = ANY (ARRAY['shared','chart'])),
  CONSTRAINT asset_registry_layer_check CHECK (layer = ANY (ARRAY['brahmagyan','ganita','bodha','kala','phala','mimamsa'])),
  CONSTRAINT asset_registry_rung_check CHECK (rung IS NULL OR rung = ANY (ARRAY['R0','R1','R2','R3','R4','R5'])),
  CONSTRAINT asset_registry_scope_check CHECK (scope = ANY (ARRAY['global','per_chart'])),
  CONSTRAINT asset_registry_storage_type_check CHECK (storage_type = ANY (ARRAY['postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only','service'])),
  CONSTRAINT asset_registry_dead_flag_not_retired CHECK (dead_flag IS NOT TRUE OR (catalog_status <> 'RETIRED' AND is_active IS NOT FALSE)));
CREATE FUNCTION public.nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'an UPDATE fired on asset_registry'; END $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table
  ON public.asset_registry FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*) EXECUTE FUNCTION public.nirmana_invalidate_registry_receipts()
"""

BUILD_RUNS_DDL = """
CREATE TABLE public.build_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, scope text NOT NULL DEFAULT 'asset', scope_target text, action text NOT NULL DEFAULT 'build',
  state text NOT NULL, created_at timestamptz DEFAULT now(),
  CONSTRAINT build_runs_state_check CHECK (state = ANY (ARRAY['planned','running','paused','completed','stopped','failed'])))
"""

ACL_SQL = """
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner;
GRANT USAGE ON SCHEMA public TO data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve,
  suvarna_reader, outsider, registry_writer, data_plane_l1_owner, data_plane_l2_owner;
ALTER TABLE public.chart_facts OWNER TO data_plane_l1_owner;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.chart_facts TO data_plane_builder;
GRANT SELECT ON public.chart_facts TO amjis_app, data_plane_verifier, data_plane_migrator, data_plane_l2_owner, suvarna_reader, outsider, registry_writer;
ALTER TABLE public.chart_fact_identity OWNER TO amjis_app;
GRANT SELECT ON public.chart_fact_identity TO retrieval_census_ro, role_web_serve, role_jobs, role_sidecar, suvarna_reader;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.chart_fact_identity TO role_orchestrator;
GRANT SELECT ON public.chart_fact_identity TO registry_writer;  -- some privilege, no grant option: a GRANT by it only WARNs
ALTER TABLE public.asset_registry OWNER TO amjis_app;
GRANT SELECT ON public.asset_registry TO retrieval_census_ro, role_web_serve, role_jobs, role_sidecar, nirmana_evidence_ingress_writer,
  nirmana_campaign_control_writer, data_plane_l1_owner, data_plane_l2_owner, data_plane_builder, suvarna_reader;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.asset_registry TO role_orchestrator;
GRANT UPDATE ON public.asset_registry TO utkarsha_builder;
GRANT SELECT,INSERT ON public.asset_registry TO registry_writer;
ALTER TABLE public.build_runs OWNER TO amjis_app;
GRANT SELECT ON public.build_runs TO outsider, suvarna_reader, registry_writer
"""


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
        self.data = tempfile.mkdtemp(prefix=f"m1262pg{version}_")
        self.sock = tempfile.mkdtemp(prefix="q", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self._n = 0
        self.started = False
        self.pid: int | None = None

    def _run(self, exe: str, *args: str, timeout: int = 120) -> None:
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self) -> None:
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        opts = (f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                "-c fsync=off -c max_connections=40 -c shared_buffers=16MB")
        self._run("pg_ctl", "-D", self.data, "-o", opts, "-w", "-t", "60", "-l", os.path.join(self.data, "server.log"), "start")
        self.started = True
        try:
            self.pid = int(Path(self.data, "postmaster.pid").read_text().splitlines()[0])
        except Exception:  # noqa: BLE001 - informational only
            self.pid = None
        with self.connect("postgres", "postgres", autocommit=True) as c:
            for name, attrs in ROLES:
                c.execute(f"CREATE ROLE {name} {attrs} NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS")
            c.execute("GRANT data_plane_l1_owner TO data_plane_migrator")

    def stop(self) -> None:
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db: str, user: str, autocommit: bool = False) -> psycopg.Connection:
        return psycopg.connect(host=self.sock, port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10)


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


def _fact_id(chart: str, i: int) -> str:
    return f"f-{chart[:4]}-{i}"


class Env:
    """A fresh production-shaped database inside the disposable cluster, with a two-chart fixture."""

    def __init__(self, cl: Cluster, *, with_identity_rows: bool = True):
        self.cl = cl
        cl._n += 1
        self.db = f"t{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} OWNER amjis_app TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            for ddl in (CHART_FACTS_DDL, IDENTITY_DDL, ASSET_REGISTRY_DDL, BUILD_RUNS_DDL):
                c.execute(ddl)
            for chart, build, n_ident in ((CHART_A, BUILD_A, N_IDENT_A), (CHART_B, BUILD_B, N_IDENT_B)):
                for i in range(N_FACTS_PER_CHART):
                    c.execute(
                        "INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key,"
                        " citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at)"
                        " VALUES (%s,%s,'lahiri',%s,'graha_position',%s,%s,'c','c','s','two_pass_verified','e',now())",
                        (_fact_id(chart, i), chart, build, f"GRAHA{i}", "house_d1"))
                    if with_identity_rows and i < n_ident:
                        c.execute(
                            "INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, graha_code, house_num, parse_rule, parsed_from, build_id)"
                            " VALUES (%s,%s,'graha_in_house','SUN',1,'bare_graha_subject',%s,%s)",
                            (_fact_id(chart, i), chart, f"fact_subject='GRAHA{i}';fact_key='house_d1'", build))
            # a few unrelated registry rows: they must come out of the migration byte-identical
            for aid, layer in (("ga_positions", "ganita"), ("ga_vargas", "ganita"), ("bo_laksana", "bodha")):
                c.execute("INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,"
                          " storage_type, scope, has_writer) VALUES (%s,%s,1,'x','x','x','postgres_table','per_chart',true)", (aid, layer))
            c.execute(ACL_SQL)
            # the pre-state every scenario relies on: the builder holds nothing on the index (production, W1_PRIVILEGE_AUDIT)
            assert c.execute("SELECT has_table_privilege('data_plane_builder','public.chart_fact_identity','SELECT')").fetchone()[0] is False

    # ---- connections
    def as_(self, user: str) -> psycopg.Connection:
        return self.cl.connect(self.db, user)

    def admin(self) -> psycopg.Connection:
        return self.cl.connect(self.db, "postgres", autocommit=True)

    # ---- observation
    def acls(self) -> dict[str, list[str]]:
        with self.admin() as c:
            rows = c.execute("SELECT relname, coalesce(relacl::text[], ARRAY[]::text[]) FROM pg_class "
                             "WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r','m','v','p')").fetchall()
        return {r[0]: sorted(r[1]) for r in rows}

    def other_rows(self) -> list[str]:
        with self.admin() as c:
            return [r[0] for r in c.execute("SELECT t::text FROM public.asset_registry t WHERE asset_id <> %s ORDER BY asset_id", (ASSET_ID,)).fetchall()]

    def registry_row(self) -> dict | None:
        with self.admin() as c:
            cur = c.execute("SELECT * FROM public.asset_registry WHERE asset_id = %s", (ASSET_ID,))
            row = cur.fetchone()
            if row is None:
                return None
            return dict(zip([d.name for d in cur.description], row))

    def n_registry_rows(self) -> int:
        with self.admin() as c:
            return c.execute("SELECT count(*) FROM public.asset_registry WHERE asset_id = %s", (ASSET_ID,)).fetchone()[0]

    def privs(self, role: str = "data_plane_builder") -> dict[str, bool]:
        """Effective privileges of `role` on the index (direct, PUBLIC, inherited; column-level). Not covered: NOINHERIT-membership paths, PG17 MAINTAIN."""
        out: dict[str, bool] = {}
        with self.admin() as c:
            rel = "public.chart_fact_identity"
            out["SELECT"] = c.execute("SELECT has_table_privilege(%s, %s, 'SELECT')", (role, rel)).fetchone()[0]
            for p in EXTRA_PRIVS:
                v = c.execute("SELECT has_table_privilege(%s, %s, %s)", (role, rel, p)).fetchone()[0]
                if p in ("INSERT", "UPDATE", "REFERENCES"):
                    v = v or c.execute("SELECT has_any_column_privilege(%s, %s, %s)", (role, rel, p)).fetchone()[0]
                out[p] = v
        return out

    # ---- action
    def apply(self, sql: str, role: str = "amjis_app", notices: list[str] | None = None, session_sql: str | None = None) -> str:
        """Apply `sql` as `role` in ONE transaction (BEGIN; sql; COMMIT), like migrate.ts. Raises after rolling back. Returns lock_timeout after COMMIT."""
        conn = self.as_(role)
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

    def run_sql(self, stmt: str, params=None):
        with self.admin() as c:
            return c.execute(stmt, params).fetchall() if stmt.lstrip().upper().startswith("SELECT") else c.execute(stmt, params)

    def drop(self) -> None:
        with self.cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001 - scenarios report any failure as data
        return exc


def _msg(exc: BaseException | None) -> str:
    return "" if exc is None else str(exc).splitlines()[0]


def _read_stored_sqls(env: Env) -> tuple[str, str]:
    row = env.registry_row()
    assert row is not None
    return row["count_sql"], row["integrity_check_sql"]


def _eval_count(env: Env, count_sql: str, chart: str, role: str = "amjis_app") -> int:
    conn = env.as_(role)
    try:
        conn.execute(f"PREPARE q_count(uuid) AS {count_sql}")
        n = conn.execute(f"EXECUTE q_count('{chart}'::uuid)").fetchone()[0]  # chart is one of this file's own UUID constants
        conn.rollback()
        return n
    finally:
        conn.close()


def _eval_integrity(env: Env, integrity_sql: str, role: str = "amjis_app") -> bool | None:
    conn = env.as_(role)
    try:
        val = conn.execute(integrity_sql).fetchone()[0]
        conn.rollback()
        return val
    finally:
        conn.close()


# --------------------------------------------------------------------------------------------- scenarios

def sc_apply_once(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        before_acl, before_rows = env.acls(), env.other_rows()
        # Precondition (not mutant-detectable): the problem the migration solves is real.
        b = env.as_("data_plane_builder")
        try:
            with pytest.raises(pgerr.InsufficientPrivilege):
                b.execute("SELECT count(*) FROM public.chart_fact_identity")
            with pytest.raises(pgerr.InFailedSqlTransaction):
                b.execute("SELECT 1")
        finally:
            b.close()
        assert env.n_registry_rows() == 0, "precondition: the registry row already exists"
        assert not any(env.privs().values()), "precondition: builder already holds a privilege on the index"

        notices: list[str] = []
        try:
            lock_after = env.apply(sql, notices=notices)
        except Exception as exc:  # noqa: BLE001
            return [f"apply failed: {_msg(exc)}"]
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after!r}")
        p = env.privs()
        if not p["SELECT"]:
            v.append("builder lacks SELECT on chart_fact_identity")
        extra = [k for k in EXTRA_PRIVS if p[k]]
        if extra:
            v.append(f"builder holds extra privilege: {extra}")
        after_acl = env.acls()
        added = sorted(f"{t}:{e}" for t in after_acl for e in set(after_acl[t]) - set(before_acl.get(t, [])))
        removed = sorted(f"{t}:{e}" for t in before_acl for e in set(before_acl[t]) - set(after_acl.get(t, [])))
        if added != [f"chart_fact_identity:{BUILDER_ENTRY}"] or removed:
            v.append(f"ACL diff over all relations is not exactly the one builder entry: added={added} removed={removed}")
        if any(e.startswith("=") for e in after_acl["chart_fact_identity"]):
            v.append("a PUBLIC grant appeared on chart_fact_identity")
        if env.n_registry_rows() != 1:
            v.append(f"registry rows for {ASSET_ID}: {env.n_registry_rows()}")
        row = env.registry_row() or {}
        want = dict(layer="ganita", target_table="chart_fact_identity", scope="per_chart", is_active=True, has_writer=False, has_substeps=False,
                    asset_type="data", asset_kind="data", storage_type="postgres_table", catalog_status="CURRENT", layer_name="Gaṇita",
                    layer_index="L1", domain="chart", rung="R1", target_floor=0, sort_order=52, depends_on=[], natural_key_partition=None, clear_tables=None)
        for k, val in want.items():
            if row.get(k) != val:
                v.append(f"registry {k} = {row.get(k)!r}, expected {val!r}")
        if not row.get("count_sql") or "$1" not in row["count_sql"] or "chart_id" not in row["count_sql"]:
            v.append("count_sql is not chart-scoped with $1")
        if not row.get("integrity_check_sql"):
            v.append("integrity_check_sql missing")
        if env.other_rows() != before_rows:
            v.append("another asset_registry row changed")
        # the builder can read, cannot write
        b = env.as_("data_plane_builder")
        try:
            if _try(lambda: (b.execute("SELECT count(*) FROM public.chart_fact_identity").fetchone(), b.rollback())) is not None:
                v.append("builder cannot read the index after apply")
                b.rollback()
            for dml in ("INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, parse_rule, parsed_from) VALUES ('zz', %s, 'k', 'r', 'p')",
                        "UPDATE public.chart_fact_identity SET entity_kind = 'x'", "DELETE FROM public.chart_fact_identity"):
                exc = _try(lambda d=dml: b.execute(d, (CHART_A,) if "%s" in d else None))
                b.rollback()
                if not isinstance(exc, pgerr.InsufficientPrivilege):
                    v.append(f"builder write was not refused: {dml.split()[0]} -> {_msg(exc)!r}")
        finally:
            b.close()
        # nobody else gained or lost anything on the index
        for r in ("retrieval_census_ro", "role_web_serve", "role_jobs", "role_sidecar", "suvarna_reader", "outsider", "data_plane_verifier"):
            pr = env.privs(r)
            if r == "outsider" and any(pr.values()):
                v.append(f"outsider gained a privilege: {pr}")
    finally:
        env.drop()
    return v


def sc_idempotent(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        env.apply(sql)
        acl1, rows1, reg1 = env.acls(), env.other_rows(), env.registry_row()
        notices: list[str] = []
        try:
            env.apply(sql, notices=notices)
            env.apply(sql)
        except Exception as exc:  # noqa: BLE001
            return [f"re-apply failed: {_msg(exc)}"]
        if env.acls() != acl1:
            v.append("ACLs changed on re-apply")
        if env.other_rows() != rows1:
            v.append("other registry rows changed on re-apply")
        if env.n_registry_rows() != 1 or env.registry_row() != reg1:
            v.append("the registry row changed or duplicated on re-apply")
        if not any("already holds SELECT" in n for n in notices):
            v.append(f"re-apply did not report the grant as a no-op: {notices}")
    finally:
        env.drop()
    return v


def sc_count_sql(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        env.apply(sql)
        count_sql, _ = _read_stored_sqls(env)
        for chart, want in ((CHART_A, N_IDENT_A), (CHART_B, N_IDENT_B), (UNKNOWN_CHART, 0)):
            got = _eval_count(env, count_sql, chart)
            if got != want:
                v.append(f"count_sql({chart[:4]}) = {got}, expected {want}")
        # adding a row for chart B moves B only
        env.run_sql("INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, parse_rule, parsed_from, build_id) VALUES (%s,%s,'graha','r','p',%s)",
                    (_fact_id(CHART_B, 5), CHART_B, BUILD_B))
        if _eval_count(env, count_sql, CHART_B) != N_IDENT_B + 1 or _eval_count(env, count_sql, CHART_A) != N_IDENT_A:
            v.append("count_sql is not partitioned by chart_id")
        # the builder can run it after the grant (the stats route / census read it with the app role; the builder is the new reader)
        if _eval_count(env, count_sql, CHART_A, "data_plane_builder") != N_IDENT_A:
            v.append("count_sql does not evaluate as the builder")
    finally:
        env.drop()
    return v


DEFECTS = [
    # name, SQL that creates the defect (admin), SQL that repairs it
    ("wrong_chart", f"UPDATE public.chart_fact_identity SET chart_id = '{CHART_B}' WHERE fact_id = '{_fact_id(CHART_A, 0)}'",
     f"UPDATE public.chart_fact_identity SET chart_id = '{CHART_A}' WHERE fact_id = '{_fact_id(CHART_A, 0)}'"),
    ("wrong_build", f"UPDATE public.chart_fact_identity SET build_id = '{BUILD_B}' WHERE fact_id = '{_fact_id(CHART_A, 1)}'",
     f"UPDATE public.chart_fact_identity SET build_id = '{BUILD_A}' WHERE fact_id = '{_fact_id(CHART_A, 1)}'"),
    ("null_build", f"UPDATE public.chart_fact_identity SET build_id = NULL WHERE fact_id = '{_fact_id(CHART_A, 1)}'",
     f"UPDATE public.chart_fact_identity SET build_id = '{BUILD_A}' WHERE fact_id = '{_fact_id(CHART_A, 1)}'"),
    ("stale_subject", f"UPDATE public.chart_facts SET fact_subject = 'RENAMED' WHERE fact_id = '{_fact_id(CHART_A, 2)}'",
     f"UPDATE public.chart_facts SET fact_subject = 'GRAHA2' WHERE fact_id = '{_fact_id(CHART_A, 2)}'"),
    ("stale_key", f"UPDATE public.chart_facts SET fact_key = 'sign_d9' WHERE fact_id = '{_fact_id(CHART_B, 1)}'",
     f"UPDATE public.chart_facts SET fact_key = 'house_d1' WHERE fact_id = '{_fact_id(CHART_B, 1)}'"),
]


def sc_integrity(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    env = Env(cl)
    try:
        env.apply(sql)
        _, isql = _read_stored_sqls(env)
        for role in ("amjis_app", "data_plane_builder"):
            got = _eval_integrity(env, isql, role)
            if got is not True:
                v.append(f"integrity on the consistent fixture as {role} = {got!r}, expected True")
        for name, break_sql, repair_sql in DEFECTS:
            env.run_sql(break_sql)
            got = _eval_integrity(env, isql)
            if got is not False:
                v.append(f"integrity with defect {name} = {got!r}, expected False")
            env.run_sql(repair_sql)
            if _eval_integrity(env, isql) is not True:
                v.append(f"integrity did not return to True after repairing {name}")
        # orphan: only reachable when the FK is absent / NOT VALID (the LEFT JOIN clause keeps the claim honest)
        env.run_sql("ALTER TABLE public.chart_fact_identity DROP CONSTRAINT chart_fact_identity_fact_id_fkey")
        # build_id NULL on the orphan: otherwise the build clause (NULL fact side) would flag it and mask a missing orphan clause
        env.run_sql(f"UPDATE public.chart_fact_identity SET build_id = NULL WHERE fact_id = '{_fact_id(CHART_A, 3)}'")
        env.run_sql(f"DELETE FROM public.chart_facts WHERE fact_id = '{_fact_id(CHART_A, 3)}'")
        if _eval_integrity(env, isql) is not False:
            v.append("integrity with an orphan identity row (no fact) is not False")
        env.run_sql(f"DELETE FROM public.chart_fact_identity WHERE fact_id = '{_fact_id(CHART_A, 3)}'")
        if _eval_integrity(env, isql) is not True:
            v.append("integrity did not return to True after removing the orphan")
        # an unrelated, perfectly consistent chart-B row does not disturb it; and an identity-free fact (no row) is NOT a defect
        env.run_sql(f"UPDATE public.chart_facts SET fact_subject = 'IDENTITY_FREE_LABEL' WHERE fact_id = '{_fact_id(CHART_B, 5)}'")
        if _eval_integrity(env, isql) is not True:
            v.append("a fact with no identity row (identity-free) made the integrity SQL false")
        # empty index: a vacuous NOT EXISTS must not read as green
        env.run_sql("DELETE FROM public.chart_fact_identity")
        if _eval_integrity(env, isql) is not False:
            v.append("integrity on an EMPTY index is not False (vacuous green)")
    finally:
        env.drop()
    return v


def sc_integrity_honest_limit(cl: Cluster, sql: str) -> list[str]:
    """The SQL does NOT attest completeness (documented limit): an index that covers only one of six facts, all consistent, reads True.
    This pins the honest scope of the claim: if someone widens the SQL to claim completeness it must do so deliberately."""
    v: list[str] = []
    env = Env(cl)
    try:
        env.apply(sql)
        _, isql = _read_stored_sqls(env)
        env.run_sql(f"DELETE FROM public.chart_fact_identity WHERE fact_id <> '{_fact_id(CHART_A, 0)}'")
        if _eval_integrity(env, isql) is not True:
            v.append("a consistent but INCOMPLETE index no longer reads True: the claim was widened (update the migration header and this pin together)")
    finally:
        env.drop()
    return v


def sc_guard_active_builds(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for state in ("planned", "running", "paused"):
        env = Env(cl)
        try:
            env.run_sql("INSERT INTO public.build_runs (state) VALUES (%s)", (state,))
            exc = _try(lambda: env.apply(sql))
            if exc is None or "build run(s) are active" not in _msg(exc):
                v.append(f"active build run ({state}) did not refuse with the guard message: {_msg(exc)!r}")
            if env.n_registry_rows() != 0 or env.privs()["SELECT"]:
                v.append(f"refusal for {state} did not roll back whole")
        finally:
            env.drop()
    env = Env(cl)
    try:
        for state in ("completed", "stopped", "failed"):
            env.run_sql("INSERT INTO public.build_runs (state) VALUES (%s)", (state,))
        exc = _try(lambda: env.apply(sql))
        if exc is not None:
            v.append(f"terminal build runs wrongly blocked the migration: {_msg(exc)}")
    finally:
        env.drop()
    return v


def sc_guard_missing(cl: Cluster, sql: str) -> list[str]:
    v: list[str] = []
    for what, ddl, needle in (
        ("role", "DROP OWNED BY data_plane_builder; DROP ROLE data_plane_builder", "role data_plane_builder does not exist"),
        ("table", "DROP TABLE public.chart_fact_identity", "public.chart_fact_identity does not exist"),
        ("not_a_table", "DROP TABLE public.build_runs; CREATE VIEW public.build_runs AS SELECT 'completed'::text AS state", "is not an ordinary table"),
    ):
        env = Env(cl)
        try:
            env.run_sql(ddl)
            exc = _try(lambda: env.apply(sql))
            if exc is None or needle not in _msg(exc):
                v.append(f"guard_{what}: expected {needle!r}, got {_msg(exc)!r}")
            if env.n_registry_rows() != 0:
                v.append(f"guard_{what}: registry row survived the refusal")
        finally:
            env.drop()
            if what == "role":  # roles are cluster-wide: put it back for the next scenario
                with cl.connect("postgres", "postgres", autocommit=True) as c:
                    c.execute("CREATE ROLE data_plane_builder LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS")
    return v


def sc_guard_non_owner(cl: Cluster, sql: str) -> list[str]:
    """An executor that cannot act as the owner must be refused BEFORE any write, with the owner message."""
    v: list[str] = []
    env = Env(cl)
    try:
        exc = _try(lambda: env.apply(sql, role="outsider"))
        if exc is None or "cannot act as the owner" not in _msg(exc):
            v.append(f"non-owner executor not refused by the owner guard: {_msg(exc)!r}")
        if env.n_registry_rows() != 0 or env.privs()["SELECT"]:
            v.append("non-owner refusal left something behind")
    finally:
        env.drop()
    return v


OWNER_GUARD = "IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN"


def sc_warn_only_grant_is_caught(cl: Cluster, sql: str) -> list[str]:
    """The P2 rule: a WARN-only GRANT counts as failure. PostgreSQL only WARNs when a non-owner GRANTs; show that, then show that the migration
    fails anyway when the owner guard is out of the way (the post-check), so a green apply can never mean 'nothing was granted'."""
    v: list[str] = []
    env = Env(cl)
    try:
        notices: list[str] = []
        conn = env.as_("registry_writer")
        try:
            conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
            conn.execute("GRANT SELECT ON TABLE public.chart_fact_identity TO data_plane_builder")
            conn.commit()
        finally:
            conn.close()
        if not any("no privileges were granted" in n for n in notices):
            v.append(f"PostgreSQL no longer WARNs on a non-owner GRANT: {notices}")
        if env.privs()["SELECT"]:
            v.append("a non-owner GRANT unexpectedly took effect")
        # owner guard neutered; the executor can insert the registry row but is not the owner: the GRANT only WARNs
        unguarded = sql.replace(OWNER_GUARD, "IF false THEN")
        exc = _try(lambda: env.apply(unguarded, role="registry_writer"))
        if exc is None:
            v.append("a WARN-only GRANT (non-owner executor, owner guard removed) left the migration GREEN")
        elif "lacks SELECT on public.chart_fact_identity after the grant" not in _msg(exc):
            v.append(f"the post-check did not catch the WARN-only GRANT: {_msg(exc)!r}")
        if env.privs()["SELECT"] or env.n_registry_rows() != 0:
            v.append("the WARN-only GRANT attempt left something behind")
    finally:
        env.drop()
    return v


def sc_lock_timeout(cl: Cluster, sql: str) -> list[str]:
    """Another transaction holds an uncommitted ACL change on the same pg_class row: our GRANT must wait, then fail with lock_not_available at
    ~5s (not hang). The 12s statement_timeout is only a net so a mutant that lost the lock_timeout fails this scenario instead of hanging."""
    env = Env(cl)
    blocker = env.as_("amjis_app")
    try:
        blocker.execute("GRANT SELECT ON public.chart_fact_identity TO retrieval_census_ro")  # held, uncommitted (already granted: a no-op ACL rewrite)
        blocker.execute("REVOKE SELECT ON public.chart_fact_identity FROM retrieval_census_ro")  # rewrites the pg_class row: the lock we need
        t0 = time.monotonic()
        exc = _try(lambda: env.apply(sql, session_sql="SET statement_timeout = '12s'"))
        dt = time.monotonic() - t0
        if exc is None:
            return ["the grant did not wait for the blocker (expected lock_not_available)"]
        if not isinstance(exc, pgerr.LockNotAvailable):
            return [f"expected lock_not_available, got {type(exc).__name__} after {dt:.1f}s"]
        if not 4.0 <= dt <= 9.0:
            return [f"lock timeout fired after {dt:.1f}s, expected about 5s"]
        return []
    finally:
        blocker.rollback()
        blocker.close()
        env.drop()


def sc_divergent_row(cl: Cluster, sql: str) -> list[str]:
    """A PRE-EXISTING ga_fact_identity row that differs from the intended shape is never silently accepted: the migration fails and rolls back whole."""
    v: list[str] = []
    base = dict(count_sql="SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1", integrity_check_sql="SELECT true", has_writer=False, is_active=True,
                scope="per_chart", target_table="chart_fact_identity")
    cases = {
        "count_sql": dict(count_sql="SELECT count(*) FROM chart_fact_identity"),
        "has_writer": dict(has_writer=True),
        "integrity": dict(),  # 'SELECT true' differs from the migration's text by construction
        "inactive": dict(is_active=False),
        "scope": dict(scope="global"),
        "target": dict(target_table="chart_facts"),
    }
    for what, over in cases.items():
        env = Env(cl)
        try:
            d = {**base, **over}
            env.run_sql("INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type,"
                        " scope, target_table, count_sql, integrity_check_sql, catalog_status, has_writer, is_active)"
                        " VALUES ('ga_fact_identity','ganita',52,'x','x','x','postgres_table',%s,%s,%s,%s,'CURRENT',%s,%s)",
                        (d["scope"], d["target_table"], d["count_sql"], d["integrity_check_sql"], d["has_writer"], d["is_active"]))
            exc = _try(lambda: env.apply(sql))
            if exc is None or "differs from the intended shape" not in _msg(exc):
                v.append(f"divergent pre-existing row ({what}) not refused: {_msg(exc)!r}")
            if env.privs()["SELECT"]:
                v.append(f"divergent row ({what}): the grant was not rolled back")
        finally:
            env.drop()
    return v


FAST = [sc_apply_once, sc_idempotent, sc_count_sql, sc_integrity, sc_integrity_honest_limit, sc_guard_active_builds, sc_guard_missing,
        sc_guard_non_owner, sc_warn_only_grant_is_caught, sc_divergent_row]
SCENARIOS = FAST + [sc_lock_timeout]  # the 5 s scenario last: a mutant already killed by a fast scenario never pays for it


def first_violations(cl: Cluster, sql: str, scenarios=None) -> dict[str, list[str]]:
    """Run scenarios in order and stop at the first one that reports a violation (used for mutants: one kill is enough)."""
    out: dict[str, list[str]] = {}
    for sc in (scenarios or SCENARIOS):
        try:
            res = sc(cl, sql)
        except AssertionError:  # a PRECONDITION failure is a test bug, not a mutant kill
            raise
        except Exception as exc:  # noqa: BLE001
            res = [f"scenario crashed: {type(exc).__name__}: {_msg(exc)}"]
        if res:
            out[sc.__name__] = res
            break
    return out


# --------------------------------------------------------------------------------------------- the real file

@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.__name__)
def test_real_migration_has_no_violations(cluster, scenario):
    violations = scenario(cluster, REAL_SQL)
    assert violations == [], "\n".join(violations)


# --------------------------------------------------------------------------------------------- mutation proofs

def _once(old: str, new: str):
    def mut(sql: str) -> str:
        assert sql.count(old) == 1, f"mutation anchor not unique/present ({sql.count(old)}): {old[:70]!r}"
        return sql.replace(old, new)
    return mut


GRANT_STMT = "EXECUTE format('GRANT SELECT ON TABLE %s TO data_plane_builder', rel);"
NOT_LOCK = "SET LOCAL lock_timeout = '5s';"

MUTANTS_EXTRA_ROW = _once(
    "    ON CONFLICT (asset_id) DO NOTHING;",
    "    ON CONFLICT (asset_id) DO NOTHING;\n    INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, scope)"
    " VALUES ('ga_extra', 'ganita', 99, 'x', 'x', 'x', 'postgres_table', 'per_chart') ON CONFLICT DO NOTHING;")

MUTANTS = {
    # ---- the grant
    "grant_removed": _once(GRANT_STMT, "NULL;"),
    "grant_to_public": _once("TO data_plane_builder', rel);", "TO PUBLIC', rel);"),
    "grant_all": _once("GRANT SELECT ON TABLE %s TO data_plane_builder", "GRANT ALL ON TABLE %s TO data_plane_builder"),
    "grant_select_insert": _once("GRANT SELECT ON TABLE %s TO data_plane_builder", "GRANT SELECT, INSERT ON TABLE %s TO data_plane_builder"),
    "grant_wrong_role": _once("GRANT SELECT ON TABLE %s TO data_plane_builder", "GRANT SELECT ON TABLE %s TO data_plane_verifier"),
    "grant_with_grant_option": _once("TO data_plane_builder', rel);", "TO data_plane_builder WITH GRANT OPTION', rel);"),
    "grant_skipped_always": _once("IF has_table_privilege('data_plane_builder', rel, 'SELECT') THEN\n        RAISE NOTICE", "IF true THEN\n        RAISE NOTICE"),
    # ---- the post-checks: each is only observable when the thing it guards is ALSO broken, so each is paired with its fault
    "postcheck_select_neutered_with_grant_removed": lambda s: _once("IF NOT has_table_privilege('data_plane_builder', rel, 'SELECT') THEN", "IF false THEN")(
        _once(GRANT_STMT, "NULL;")(s)),
    "postcheck_extra_neutered_with_grant_all": lambda s: _once("IF extra IS NOT NULL THEN", "IF false THEN")(
        _once("GRANT SELECT ON TABLE %s TO data_plane_builder", "GRANT ALL ON TABLE %s TO data_plane_builder")(s)),
    "postcheck_column_level_dropped_with_column_grant": lambda s: _once(
        "OR (p IN ('INSERT', 'UPDATE', 'REFERENCES')\n            AND has_any_column_privilege('data_plane_builder', rel, p))", "")(
        _once(GRANT_STMT, GRANT_STMT + "\n        EXECUTE 'GRANT UPDATE (entity_kind) ON TABLE public.chart_fact_identity TO data_plane_builder';")(s)),
    "readback_neutered_with_has_writer_true": lambda s: _once("IF n_rows <> 1 THEN", "IF false THEN")(
        _once("        false,\n        'data',\n        false,\n        'chart',", "        false,\n        'data',\n        true,\n        'chart',")(s)),
    "xmin_check_neutered_with_extra_row": lambda s: _once("IF n_other <> 0 THEN", "IF false THEN")(MUTANTS_EXTRA_ROW(s)),
    "owner_guard_and_postcheck_removed": lambda s: _once("IF NOT has_table_privilege('data_plane_builder', rel, 'SELECT') THEN", "IF false THEN")(
        _once("IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN", "IF false THEN")(s)),
    # ---- guards
    "guard_active_builds_removed": _once("IF n_active <> 0 THEN", "IF false THEN"),
    "guard_active_builds_running_only": _once("state IN ('planned', 'running', 'paused')", "state = 'running'"),
    "guard_owner_removed": _once("IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN", "IF false THEN"),
    "guard_role_removed": _once("IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN", "IF false THEN"),
    "guard_table_removed": _once("IF rel IS NULL THEN", "IF false THEN"),
    "guard_relkind_removed": _once("IF kind NOT IN ('r', 'p') THEN", "IF false THEN"),
    "lock_timeout_removed": _once(NOT_LOCK, "SELECT 1;"),
    "lock_timeout_session_wide": _once(NOT_LOCK, "SET lock_timeout = '5s';"),
    # ---- the registry row
    "do_update_on_conflict": _once("ON CONFLICT (asset_id) DO NOTHING;", "ON CONFLICT (asset_id) DO UPDATE SET target_floor = 1;"),
    "has_writer_true": _once("        false,\n        'data',\n        false,\n        'chart',", "        false,\n        'data',\n        true,\n        'chart',"),
    "inactive": _once("        'per_chart',\n        true,\n        'data',", "        'per_chart',\n        false,\n        'data',"),
    "scope_global": _once("        'per_chart',\n        true,\n        'data',", "        'global',\n        true,\n        'data',"),
    "count_sql_unscoped": _once("v_count_sql     constant text := 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1';",
                                "v_count_sql     constant text := 'SELECT count(*) FROM chart_fact_identity';"),
    "count_sql_wrong_table": _once("'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1'", "'SELECT count(*) FROM chart_facts WHERE chart_id = $1'"),
    "extra_registry_row": MUTANTS_EXTRA_ROW,
    "wrong_layer": _once("        'ganita',\n        52,", "        'bodha',\n        52,"),
    # ---- the integrity claim: each clause is load-bearing
    "integrity_nonvacuity_dropped": _once("'SELECT EXISTS (SELECT 1 FROM public.chart_fact_identity) '\n        'AND NOT EXISTS ('", "'SELECT NOT EXISTS ('"),
    "integrity_orphan_dropped": _once("'WHERE f.fact_id IS NULL '\n        'OR f.chart_id <> i.chart_id '", "'WHERE f.chart_id <> i.chart_id '"),
    "integrity_inner_join": _once("'LEFT JOIN public.chart_facts f", "'JOIN public.chart_facts f"),
    "integrity_chart_dropped": _once("'OR f.chart_id <> i.chart_id '\n", ""),
    "integrity_build_dropped": _once("'OR i.build_id IS DISTINCT FROM f.build_id '\n", ""),
    "integrity_build_plain_neq": _once("i.build_id IS DISTINCT FROM f.build_id", "i.build_id <> f.build_id"),
    "integrity_subject_dropped": _once("'OR strpos(i.parsed_from, f.fact_subject) = 0 '\n", ""),
    "integrity_key_dropped": _once("'OR strpos(i.parsed_from, f.fact_key) = 0'\n", "'OR false'\n"),
    "integrity_always_true": _once("') AS integrity_passed'", "') OR true AS integrity_passed'"),
    "integrity_completeness_claim_added": _once("'SELECT EXISTS (SELECT 1 FROM public.chart_fact_identity) '",
                                                "'SELECT (SELECT count(*) FROM public.chart_fact_identity) = (SELECT count(*) FROM public.chart_facts) '"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_mutant_is_killed(cluster, name):
    mutated = MUTANTS[name](REAL_SQL)
    assert mutated != REAL_SQL
    killed_by = first_violations(cluster, mutated)
    assert killed_by, f"mutant {name} SURVIVED: every scenario reported zero violations"
