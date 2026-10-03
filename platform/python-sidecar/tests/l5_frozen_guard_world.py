"""Shared fixture for the 1265 tests (not a test module): a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, trust
auth, no TCP, stopped by its own pid file, directories removed) holding a MIRROR of production's roles, owners and ACLs, the four L5 tables as read
live (suvarna_reader, 2026-10-03), the repo functions/triggers that sit beside the guards, the consent tables, and the administrator `adm`
(Cloud SQL's postgres as read live: CREATEROLE, NOT a superuser, no table privilege, NO USAGE on schema public; valid on PostgreSQL <= 15).

Set PG_BIN to pin a bin directory (default: Homebrew postgresql@15, production is 15.18). On PostgreSQL >= 16 CREATEROLE alone cannot grant a role it
does not administer, so the executor-route tests skip there (the guard behaviour tests run on any version).
"""
from __future__ import annotations

import glob
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
PKG = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "l5_frozen_guard_1265"
SQL_DIR = PKG / "sql"
FORWARD = SQL_DIR / "1265_l5_frozen_row_guards.sql"
ROLLBACK = SQL_DIR / "1265_l5_frozen_row_guards.ROLLBACK.sql"
MIGRATIONS = [REPO / "platform" / "migrations", REPO / "platform" / "supabase" / "migrations"]

CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
CHART_C = "11111111-2222-4333-8444-555555555555"
RUN_1 = "aaaaaaaa-0000-4000-8000-000000000001"
RUN_2 = "aaaaaaaa-0000-4000-8000-000000000002"
COMMIT = "0123456789abcdef0123456789abcdef01234567"

ROLES = [  # name, LOGIN, INHERIT (production attributes, read 2026-10-03; none is a superuser or BYPASSRLS)
    ("amjis_app", True, False), ("amjis_inquiry_serve", True, True), ("data_plane_builder", True, False),
    ("data_plane_l1_owner", False, False), ("data_plane_l2_owner", False, False), ("data_plane_migrator", True, False),
    ("data_plane_schema_owner", False, False), ("data_plane_verifier", True, False), ("nirmana_evidence_ingress_writer", True, False),
    ("retrieval_census_ro", True, True), ("role_jobs", False, True), ("role_ledger_write", False, True), ("role_orchestrator", False, True),
    ("role_sidecar", False, True), ("role_web_serve", False, True), ("suvarna_reader", True, False),
]
NOLOGIN_ROLES = {r[0] for r in ROLES if not r[1]}


def find_pg_bin():
    cands = []
    if os.environ.get("PG_BIN"):
        cands.append(pathlib.Path(os.environ["PG_BIN"]))
    cands += [pathlib.Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@15/bin"))]
    w = shutil.which("initdb")
    if w:
        cands.append(pathlib.Path(w).parent)
    cands += [pathlib.Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [pathlib.Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_exec(name="l5_frozen_guard_exec_t"):
    return load_module(name, PKG / "l5_frozen_guard_exec.py")


def body(sql: str, tag: str) -> str:
    m = re.search(r"AS \$" + tag + r"\$(.*?)\$" + tag + r"\$;", sql, re.S)
    assert m, tag
    return m.group(1)


def _repo_function_body(path: pathlib.Path, fname: str) -> str:
    t = path.read_text(encoding="utf8")
    m = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:public\.)?" + fname + r"\s*\(.*?\bAS\s+(\$\w*\$)(.*?)\1", t, re.S | re.I)
    assert m, fname
    return m.group(2)


BMPL_FREEZE_BODY = _repo_function_body(REPO / "platform/supabase/migrations/470_pariprashna_samiksha_prediction_ledger.sql", "bmpl_freeze_confirmed")
SHAPE_BODY = _repo_function_body(REPO / "platform/supabase/migrations/458_brahma_prospective_ledger.sql", "brahma_prospective_ledger_enforce_shape")
assert hashlib.md5(BMPL_FREEZE_BODY.encode()).hexdigest() == "70c2ddb261d703fa6a33a4feaf39c99c"
assert hashlib.md5(SHAPE_BODY.encode()).hexdigest() == "acc7ec0121fa1fe0752ae938d9edfafe"

WORLD_SQL = """
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner;
GRANT USAGE ON SCHEMA public TO data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve,
  suvarna_reader, role_orchestrator, role_ledger_write, role_jobs, role_sidecar, retrieval_census_ro,
  nirmana_evidence_ingress_writer, amjis_inquiry_serve;

CREATE TABLE public.build_runs (id uuid PRIMARY KEY, chart_id uuid, state text NOT NULL DEFAULT 'completed');
CREATE TABLE public.charts (id uuid PRIMARY KEY, name text);
CREATE TABLE public.message_parts (id uuid PRIMARY KEY);
CREATE TABLE public.life_events (id uuid PRIMARY KEY);
CREATE TABLE public.brahma_event_ontology (event_class_id text PRIMARY KEY, temporal_shape text NOT NULL);

CREATE TABLE public.mimamsa_predictions (
  chart_id uuid NOT NULL, prediction_id text NOT NULL, source_pramana_id text NOT NULL, outcome_claim text NOT NULL,
  domain text NOT NULL, observation_window daterange NOT NULL, eval_date date NOT NULL, confidence_band numrange NOT NULL,
  magnitude_expected text NOT NULL, falsifier_jsonb jsonb NOT NULL, base_rate numeric, emitted_at timestamptz NOT NULL,
  lifecycle_status text NOT NULL, driving_signals jsonb NOT NULL, frozen_bundle_hash text NOT NULL,
  bundle_formula_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), contact_id text,
  chart_context_stale_at timestamptz, chart_context_stale_reason text, chart_context_superseded_by_run_id uuid,
  CONSTRAINT mimamsa_predictions_pkey PRIMARY KEY (chart_id, prediction_id),
  CONSTRAINT mimamsa_predictions_stale_pair_check CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL)),
  CONSTRAINT mimamsa_predictions_stale_reason_check CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason = 'chart_details_changed'),
  CONSTRAINT mimamsa_predictions_superseded_by_run_id_fkey FOREIGN KEY (chart_context_superseded_by_run_id) REFERENCES public.build_runs(id) ON DELETE SET NULL);
CREATE TABLE public.mimamsa_manifestation_sets (
  chart_id uuid NOT NULL, prediction_id text NOT NULL, channel_id text NOT NULL, domain text NOT NULL, source text NOT NULL,
  citation_ref jsonb NOT NULL, is_literal boolean NOT NULL, frozen_at timestamptz NOT NULL,
  CONSTRAINT mimamsa_manifestation_sets_pkey PRIMARY KEY (chart_id, prediction_id, channel_id));
CREATE TABLE public.brahma_prospective_ledger (
  prediction_id uuid NOT NULL DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, claim text NOT NULL,
  event_class text NOT NULL REFERENCES public.brahma_event_ontology(event_class_id), claim_shape text NOT NULL,
  observation_window daterange, milestone_set jsonb, model text NOT NULL, formula_version text NOT NULL, confidence numeric NOT NULL,
  falsifier text NOT NULL, as_of timestamptz NOT NULL DEFAULT now(), generator_class text NOT NULL, configuration_signature text,
  lifecycle_status text NOT NULL DEFAULT 'open', matched_event_id uuid REFERENCES public.life_events(id), matched_at timestamptz, match_note text,
  filed_by text NOT NULL, filing_method text NOT NULL DEFAULT 'explicit_filing_tool', source_citation text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), contact_id text, chart_context_stale_at timestamptz, chart_context_stale_reason text,
  chart_context_superseded_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL,
  CONSTRAINT brahma_prospective_ledger_pkey PRIMARY KEY (prediction_id),
  CONSTRAINT brahma_prospective_ledger_claim_shape_check CHECK (claim_shape IN ('point','interval','chain')),
  CONSTRAINT brahma_prospective_ledger_confidence_check CHECK (confidence > 0.0 AND confidence < 1.0),
  CONSTRAINT brahma_prospective_ledger_filing_method_check CHECK (filing_method = 'explicit_filing_tool'),
  CONSTRAINT brahma_prospective_ledger_generator_class_check CHECK (generator_class IN ('anchor_engine','reading_synthesis','engine','native_intuition')),
  CONSTRAINT brahma_prospective_ledger_lifecycle_status_check CHECK (lifecycle_status IN ('open','matched','confirmed','falsified','withdrawn','lapsed_unobserved')),
  CONSTRAINT brahma_prospective_ledger_no_empty_window CHECK (NOT isempty(observation_window)),
  CONSTRAINT brahma_prospective_ledger_shape_fields_check CHECK (
    (claim_shape = 'point' AND observation_window IS NOT NULL AND upper(observation_window) = lower(observation_window) + 1 AND milestone_set IS NULL)
 OR (claim_shape = 'interval' AND observation_window IS NOT NULL AND upper(observation_window) > lower(observation_window) AND milestone_set IS NULL)
 OR (claim_shape = 'chain' AND observation_window IS NULL AND milestone_set IS NOT NULL AND jsonb_typeof(milestone_set) = 'array' AND jsonb_array_length(milestone_set) >= 1)),
  CONSTRAINT brahma_prospective_ledger_stale_pair_check CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL)));
CREATE TABLE public.brahma_mimamsa_prediction_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, message_part_id uuid REFERENCES public.message_parts(id) ON DELETE SET NULL,
  claim_text text NOT NULL, domain text, "window" daterange, confidence numrange, direction text,
  technique_refs text[] NOT NULL DEFAULT '{}', grounding_fact_ids text[] NOT NULL DEFAULT '{}', created_from_channel text NOT NULL DEFAULT 'pariprashna',
  lifecycle_status text NOT NULL DEFAULT 'detected' CHECK (lifecycle_status IN ('detected','confirmed','open','window_closed','outcome_recorded','dismissed','lapsed','unverifiable','lapsed_unconfirmed')),
  build_id text, priors_version text, formula_versions jsonb, ranking_config jsonb, now_context_date date, stamp_copied_at timestamptz,
  outcome text, outcome_value numeric, outcome_note text, outcome_recorded_at timestamptz, confirmed_at timestamptz, dismissed_reason text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  chart_context_stale_at timestamptz, chart_context_stale_reason text,
  chart_context_superseded_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL);
CREATE TABLE public.chart_subject_consent (
  chart_id uuid PRIMARY KEY, consent_state text NOT NULL CHECK (consent_state IN ('granted','withdrawn')),
  withdrawn_at timestamptz, CHECK (consent_state <> 'withdrawn' OR withdrawn_at IS NOT NULL));
CREATE TABLE public.chart_subject_deletion_disputes (
  dispute_id bigserial PRIMARY KEY, chart_id uuid NOT NULL,
  status text NOT NULL CHECK (status IN ('open','resolved','escalated','reopened')));

ALTER TABLE public.charts OWNER TO amjis_app;
ALTER TABLE public.build_runs OWNER TO amjis_app;
ALTER TABLE public.message_parts OWNER TO amjis_app;
ALTER TABLE public.life_events OWNER TO amjis_app;
ALTER TABLE public.brahma_event_ontology OWNER TO amjis_app;
ALTER TABLE public.mimamsa_predictions OWNER TO amjis_app;
ALTER TABLE public.mimamsa_manifestation_sets OWNER TO amjis_app;
ALTER TABLE public.brahma_prospective_ledger OWNER TO amjis_app;
ALTER TABLE public.brahma_mimamsa_prediction_ledger OWNER TO amjis_app;
ALTER TABLE public.chart_subject_consent OWNER TO amjis_app;
ALTER TABLE public.chart_subject_deletion_disputes OWNER TO amjis_app;
ALTER SEQUENCE public.chart_subject_deletion_disputes_dispute_id_seq OWNER TO amjis_app;

-- production ACLs (relacl read 2026-10-03): the owner entry of mimamsa_predictions has no TRUNCATE
REVOKE TRUNCATE ON public.mimamsa_predictions FROM amjis_app;
GRANT SELECT ON public.mimamsa_predictions, public.mimamsa_manifestation_sets TO retrieval_census_ro, role_web_serve, role_jobs, role_sidecar, nirmana_evidence_ingress_writer, suvarna_reader;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.mimamsa_predictions, public.mimamsa_manifestation_sets TO role_orchestrator;
GRANT SELECT, INSERT, UPDATE ON public.mimamsa_predictions TO role_ledger_write;
GRANT SELECT, INSERT, DELETE ON public.mimamsa_predictions, public.mimamsa_manifestation_sets TO data_plane_builder;   -- the live-only 'ard' grants
GRANT SELECT ON public.brahma_prospective_ledger, public.brahma_mimamsa_prediction_ledger TO retrieval_census_ro, role_web_serve, role_jobs, suvarna_reader;
GRANT SELECT, INSERT, UPDATE ON public.brahma_prospective_ledger, public.brahma_mimamsa_prediction_ledger TO role_ledger_write;
GRANT SELECT ON public.build_runs, public.brahma_event_ontology, public.life_events, public.message_parts TO suvarna_reader, role_orchestrator;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chart_subject_consent TO role_web_serve;
GRANT SELECT ON public.chart_subject_consent TO retrieval_census_ro, role_jobs;
GRANT SELECT, INSERT ON public.chart_subject_deletion_disputes TO role_web_serve;
GRANT SELECT ON public.chart_subject_deletion_disputes TO retrieval_census_ro, role_jobs, suvarna_reader;
GRANT USAGE, SELECT ON SEQUENCE public.chart_subject_deletion_disputes_dispute_id_seq TO role_web_serve;

-- charts as live: owner amjis_app, RLS ON (no FORCE: the owner bypasses), policies that match nothing for ordinary roles
ALTER TABLE public.charts ENABLE ROW LEVEL SECURITY;
CREATE POLICY chart_owner_policy ON public.charts FOR ALL USING (false);
GRANT SELECT ON public.charts TO retrieval_census_ro, role_web_serve, role_ledger_write, role_jobs, role_sidecar, nirmana_evidence_ingress_writer,
  data_plane_builder, data_plane_l1_owner, data_plane_l2_owner;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.charts TO role_orchestrator;
"""


def install_repo_objects(c, builder_body: str, with_builder: bool = True):
    """The functions/triggers that exist beside the guards: the repo's bmpl_freeze_confirmed (470) and shape function (458), and (what the
    BUILDER_GRANT_PLAN executor left in production) the captured builder guard, all owned by amjis_app."""
    c.execute("CREATE FUNCTION public.bmpl_freeze_confirmed() RETURNS trigger AS $fn$" + BMPL_FREEZE_BODY + "$fn$ LANGUAGE plpgsql")
    c.execute("ALTER FUNCTION public.bmpl_freeze_confirmed() OWNER TO amjis_app")
    c.execute("CREATE TRIGGER trg_bmpl_freeze_confirmed BEFORE UPDATE ON public.brahma_mimamsa_prediction_ledger FOR EACH ROW EXECUTE FUNCTION public.bmpl_freeze_confirmed()")
    c.execute("CREATE FUNCTION public.brahma_prospective_ledger_enforce_shape() RETURNS trigger AS $fn$" + SHAPE_BODY + "$fn$ LANGUAGE plpgsql")
    c.execute("ALTER FUNCTION public.brahma_prospective_ledger_enforce_shape() OWNER TO amjis_app")
    c.execute("CREATE TRIGGER trg_brahma_prospective_ledger_enforce_shape BEFORE INSERT OR UPDATE OF claim_shape, event_class ON public.brahma_prospective_ledger "
              "FOR EACH ROW EXECUTE FUNCTION public.brahma_prospective_ledger_enforce_shape()")
    if with_builder:
        c.execute("CREATE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER "
                  "SET search_path = pg_catalog, pg_temp AS $guard$" + builder_body + "$guard$")
        c.execute("REVOKE ALL ON FUNCTION public.mimamsa_predictions_builder_guard() FROM PUBLIC")
        c.execute("ALTER FUNCTION public.mimamsa_predictions_builder_guard() OWNER TO amjis_app")
        c.execute("CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT OR DELETE ON public.mimamsa_predictions "
                  "FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()")


def _lit(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def pred_row(chart, pid, status="pending", **over):
    cols = {"chart_id": chart, "prediction_id": pid, "source_pramana_id": "src_" + pid, "outcome_claim": "claim " + pid,
            "domain": "career", "observation_window": "[2026-01-01,2026-06-01)", "eval_date": "2026-06-01",
            "confidence_band": "[0.4,0.7)", "magnitude_expected": "moderate", "falsifier_jsonb": '{"k":1}',
            "emitted_at": "2026-08-13T01:16:29Z", "lifecycle_status": status, "driving_signals": '["s1"]',
            "frozen_bundle_hash": "h_" + pid, "bundle_formula_version": "v1"}
    cols.update(over)
    return "INSERT INTO public.mimamsa_predictions (" + ", ".join(cols) + ") VALUES (" + ", ".join(_lit(v) for v in cols.values()) + ")"


def pros_row(chart, shape="interval", status="open", pid=None, **over):
    ev = {"point": "ec_point", "interval": "ec_interval", "chain": "ec_chain"}[shape]
    win = {"point": "[2027-01-01,2027-01-02)", "interval": "[2027-01-01,2027-03-01)", "chain": None}[shape]
    mil = '[{"milestone_id": "m1"}]' if shape == "chain" else None
    cols = {"chart_id": chart, "claim": "claim " + shape, "event_class": ev, "claim_shape": shape, "observation_window": win, "milestone_set": mil,
            "model": "m", "formula_version": "v1", "confidence": "0.6", "falsifier": "if not X", "generator_class": "engine", "filed_by": "native",
            "source_citation": "src", "lifecycle_status": status}
    if pid:
        cols["prediction_id"] = pid
    cols.update(over)
    return "INSERT INTO public.brahma_prospective_ledger (" + ", ".join(cols) + ") VALUES (" + ", ".join(_lit(v) for v in cols.values()) + ")"


def seed_sql() -> list:
    s = [
        "INSERT INTO public.charts VALUES ('%s', 'chart a'), ('%s', 'chart b'), ('%s', 'chart c')" % (CHART_A, CHART_B, CHART_C),
        "INSERT INTO public.brahma_event_ontology VALUES ('ec_point','point'), ('ec_interval','interval'), ('ec_chain','chain')",
        "INSERT INTO public.life_events VALUES ('eeeeeeee-0000-4000-8000-000000000001')",
        "INSERT INTO public.message_parts VALUES ('bbbbbbbb-0000-4000-8000-000000000001'), ('bbbbbbbb-0000-4000-8000-000000000002')",
    ]
    for i in range(3):
        s.append(pred_row(CHART_A, "pred_a%d" % i))
    s += [pred_row(CHART_A, "pred_due", "due"), pred_row(CHART_A, "pred_conf", "confirmed"), pred_row(CHART_A, "pred_den", "denied"),
          pred_row(CHART_A, "pred_exp", "expired"), pred_row(CHART_B, "pred_b0"), pred_row(CHART_B, "pred_b1"), pred_row(CHART_C, "pred_c0")]
    for pid in ("pred_a0", "pred_a1", "pred_b0"):
        ch = CHART_B if pid.startswith("pred_b") else CHART_A
        s.append("INSERT INTO public.mimamsa_manifestation_sets VALUES ('%s', '%s', 'ch_career_verbal', 'career', 'phala_anchors', '{\"anchor_id\": \"%s\"}', true, '2026-08-13T01:16:29Z')" % (ch, pid, pid))
    s += [pros_row(CHART_A, "interval", "open", "00000000-0000-4000-8000-0000000000a1"),
          pros_row(CHART_A, "point", "open", "00000000-0000-4000-8000-0000000000a2"),
          pros_row(CHART_A, "chain", "open", "00000000-0000-4000-8000-0000000000a3"),
          pros_row(CHART_A, "interval", "matched", "00000000-0000-4000-8000-0000000000a4",
                   matched_event_id="eeeeeeee-0000-4000-8000-000000000001", matched_at="2027-02-01T00:00:00Z", match_note="n"),
          pros_row(CHART_B, "interval", "open", "00000000-0000-4000-8000-0000000000b1")]
    s += ["INSERT INTO public.brahma_mimamsa_prediction_ledger (id, chart_id, claim_text, lifecycle_status, message_part_id) VALUES "
          "('cccccccc-0000-4000-8000-000000000001', '%s', 'detected claim', 'detected', 'bbbbbbbb-0000-4000-8000-000000000001'), "
          "('cccccccc-0000-4000-8000-000000000002', '%s', 'open claim', 'open', 'bbbbbbbb-0000-4000-8000-000000000002'), "
          "('cccccccc-0000-4000-8000-000000000003', '%s', 'dismissed claim', 'dismissed', NULL), "
          "('cccccccc-0000-4000-8000-000000000004', '%s', 'b claim', 'outcome_recorded', NULL)" % (CHART_A, CHART_A, CHART_A, CHART_B)]
    return s


class World:
    def __init__(self, pg, name):
        self.pg, self.name = pg, name

    def connect(self, role="postgres", **kw):
        psy = self.pg["psycopg"]
        if role in NOLOGIN_ROLES:
            conn = psy.connect(host=self.pg["sock"], port=self.pg["port"], user="postgres", dbname=self.name, autocommit=True)
            conn.execute("SET ROLE " + role)
            conn.autocommit = kw.get("autocommit", False)
            return conn
        return psy.connect(host=self.pg["sock"], port=self.pg["port"], user=role, dbname=self.name, **kw)

    def exec(self, sql, params=None, role="postgres"):
        with self.connect(role) as c:
            cur = c.execute(sql, params)
            rows = cur.fetchall() if cur.description else None
            c.commit()
            return rows

    def query(self, sql, params=None, role="postgres"):
        with self.connect(role) as c:
            return c.execute(sql, params).fetchall()

    def schema_acl(self):
        return self.query("SELECT nspacl::text FROM pg_namespace WHERE nspname = 'public'")[0][0]

    def window(self, action):
        """The grant/revoke the executor performs inside its transaction, here committed on its own (data_plane_migrator route)."""
        with self.connect("data_plane_migrator") as c:
            c.execute("SET LOCAL ROLE data_plane_schema_owner")
            c.execute("GRANT CREATE ON SCHEMA public TO amjis_app" if action == "grant" else "REVOKE CREATE ON SCHEMA public FROM amjis_app")
            c.commit()

    def apply_sql(self, sql, role="amjis_app", window=True, notices=None):
        if window:
            self.window("grant")
        try:
            conn = self.connect(role)
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
        finally:
            if window:
                self.window("revoke")

    def catalog_state(self):
        """Everything the plan may or may not change, as one comparable value."""
        ex = self._ex
        out = {}
        with self.connect("postgres") as c:
            cur = c.cursor()
            for k, sql in ex.SNAP_SQL.items():
                cur.execute(sql)
                out[k] = sorted(tuple(str(x) for x in r) for r in cur.fetchall())
            cur.execute(ex.MEMBERSHIP_SQL)
            out["membership"] = sorted(tuple(str(x) for x in r) for r in cur.fetchall())
            rows = []
            for t in ex.TABLES:
                cur.execute("SELECT '" + t + "', count(*), md5(COALESCE(string_agg(x::text, '|' ORDER BY x::text), '')) FROM public." + t + " x")
                rows += [tuple(str(v) for v in r) for r in cur.fetchall()]
            out["rowdata"] = sorted(rows)
        return out


_counter = 0


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = pathlib.Path(tempfile.mkdtemp(prefix="m1265pg"))
    data = root / "data"
    sockdir = pathlib.Path(tempfile.mkdtemp(prefix="m65", dir="/tmp"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"], check=True, capture_output=True)
    opts = "-p %d -c listen_addresses='' -c unix_socket_directories=%s -c fsync=off" % (port, sockdir)
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"], check=True, capture_output=True)
    try:
        with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            for name, login, inherit in ROLES:
                c.execute("CREATE ROLE %s %s %s NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS" % (name, "LOGIN" if login else "NOLOGIN", "INHERIT" if inherit else "NOINHERIT"))
            for r in ("data_plane_l1_owner", "data_plane_l2_owner", "data_plane_schema_owner"):
                c.execute("GRANT %s TO data_plane_migrator" % r)
            c.execute("GRANT role_web_serve TO amjis_inquiry_serve")
            c.execute("CREATE ROLE adm LOGIN INHERIT NOSUPERUSER CREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS")      # Cloud SQL's postgres, as read live
            c.execute("GRANT pg_monitor TO adm")      # Cloud SQL's postgres reaches pg_monitor (and so pg_read_all_stats) through cloudsqlsuperuser
            c.execute("CREATE ROLE adm_blind LOGIN INHERIT NOSUPERUSER CREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS")      # same, without pg_read_all_stats
            c.execute("CREATE ROLE adm_nocr LOGIN INHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS")
            major = int(c.execute("SHOW server_version_num").fetchone()[0]) // 10000
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg, "bin": binp, "major": major}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


EX = load_exec()


def make_world(pg, builder_guard=True, seed=True, builder_body=None) -> World:
    global _counter
    _counter += 1
    name = "t%d" % _counter
    psycopg = pg["psycopg"]
    with psycopg.connect(host=pg["sock"], port=pg["port"], user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute("CREATE DATABASE " + name)
    w = World(pg, name)
    w._ex = EX
    bb = builder_body if builder_body is not None else body(FORWARD.read_text(encoding="utf8"), "guard")
    with w.connect("postgres", autocommit=True) as c:
        c.execute(WORLD_SQL)
        if pg["major"] >= 16:                       # test adaptation only: PG16+ needs ADMIN OPTION to grant a role (production is 15.18)
            c.execute("GRANT data_plane_schema_owner, amjis_app TO adm WITH ADMIN OPTION, INHERIT FALSE, SET TRUE")
        install_repo_objects(c, bb, builder_guard)
        if seed:
            for q in seed_sql():
                c.execute(q)
    w.baseline_acl = w.schema_acl()
    return w


CASCADE_TABLES = ("mimamsa_predictions", "mimamsa_manifestation_sets", "brahma_prospective_ledger", "brahma_mimamsa_prediction_ledger")


def add_chart_fks(w):
    """What migration 1275 adds (SS N-108): chart_id -> charts(id) ON DELETE CASCADE on the per-chart L5 tables. Run as the table owner."""
    for t in CASCADE_TABLES:
        w.exec("ALTER TABLE public.%s ADD CONSTRAINT %s_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE" % (t, t), role="amjis_app")


def drop_world(pg, w):
    with pg["psycopg"].connect(host=pg["sock"], port=pg["port"], user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute("DROP DATABASE IF EXISTS %s WITH (FORCE)" % w.name)
