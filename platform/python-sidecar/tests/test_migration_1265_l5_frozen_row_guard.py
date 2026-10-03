"""
Migration 1265 (Suvarna, SS ruling N-104): capture the live-only `mimamsa_predictions_builder_guard` into the repo and
add a DB-enforced UPDATE/DELETE/TRUNCATE guard on frozen `mimamsa_predictions` rows. HELD: own draft PR, merges only
on SS's review, after S-L1, and only into a protected public-schema window (the routine runner cannot run it).

Two tiers:
  * STATIC (always runs, DB-free): file shape, the captured body (md5 + length), the allow-list, header sections.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, no TCP, removed at session end, stopped by its own
    pid file). It never connects to anything else. Skipped, loudly, when no initdb/pg_ctl is found;
    REQUIRE_PG_BINARIES=1 turns the skip into a failure. Set PG_BIN to pin a version (production is PostgreSQL 15.18).

The LIVE fixture MIRRORS PRODUCTION'S ROLES (read from production 2026-10-03 as suvarna_reader): the same roles with
the same LOGIN/INHERIT/SUPERUSER/CREATEROLE attributes and memberships, NO superuser among the application roles, schema
public owned by data_plane_schema_owner with CREATE only for the three owner roles (amjis_app has USAGE only),
mimamsa_predictions / build_runs / chart_subject_consent* owned by amjis_app with production's ACLs (the owner entry on
mimamsa_predictions has no TRUNCATE), the captured builder guard owned by amjis_app with ACL {amjis_app=X/amjis_app}.
What it proves: the privilege determination (routine role fails, protected window passes, schema ACL unchanged after),
the guard behaviours (every frozen column, DELETE, TRUNCATE, transitions, staleness, ON DELETE SET NULL, the subject
withdrawal exception, replication-role bypass), the md5 guard, idempotent re-run, the RLS assessment, and mutation
proofs. It does NOT prove production state (read production structure after apply; Trap 103).
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1265 = _MIG / "1265_l5_predictions_frozen_row_guard.sql"
_REAL = _M1265.read_text()

BUILDER_MD5 = "46c23854275c2712b30860a2b174adb2"
BUILDER_LEN = 1084
PREFIX = "mimamsa_predictions_frozen_row_guard:"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
CHART_C = "11111111-2222-4333-8444-555555555555"

FROZEN_COLUMNS = ["chart_id", "prediction_id", "source_pramana_id", "outcome_claim", "domain", "observation_window",
                  "eval_date", "confidence_band", "magnitude_expected", "falsifier_jsonb", "base_rate", "emitted_at",
                  "driving_signals", "frozen_bundle_hash", "bundle_formula_version", "created_at", "contact_id"]
ALL_COLUMNS = FROZEN_COLUMNS + ["lifecycle_status", "chart_context_stale_at", "chart_context_stale_reason",
                                "chart_context_superseded_by_run_id"]


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _body(sql: str, tag: str) -> str:
    m = re.search(r"AS \$" + tag + r"\$(.*?)\$" + tag + r"\$;", sql, re.S)
    assert m, tag
    return m.group(1)


# -- STATIC tier --------------------------------------------------------------------

def test_captured_builder_guard_body_is_byte_exact_and_guarded_by_md5_and_length():
    body = _body(_REAL, "guard")
    assert hashlib.md5(body.encode()).hexdigest() == BUILDER_MD5
    assert len(body.encode()) == BUILDER_LEN
    assert body.startswith("\nBEGIN\n  IF current_user = 'data_plane_builder'") and body.endswith("\nEND\n")
    # the md5 + length constants appear in the capture guard and the post-check
    assert _REAL.count(BUILDER_MD5) >= 4 and f"<> {BUILDER_LEN}" in _REAL
    assert "SECURITY INVOKER" in _REAL and "SET search_path = pg_catalog, pg_temp" in _REAL


def test_frozen_guard_body_md5_is_pinned_in_the_check_and_post_check():
    body = _body(_REAL, "frozen")
    md5 = hashlib.md5(body.encode()).hexdigest()
    assert _REAL.count(md5) >= 4, "header, replace guard, comment-free post-check must all carry the md5"


def test_allow_list_is_exactly_four_columns_and_everything_else_is_fail_closed():
    body = _body(_REAL, "frozen")
    arr = re.search(r"c_mutable\s+CONSTANT text\[\] := ARRAY\[(.*?)\];", body, re.S)
    assert arr
    cols = re.findall(r"'([a-z_]+)'", arr.group(1))
    assert cols == ["lifecycle_status", "chart_context_stale_at", "chart_context_stale_reason",
                    "chart_context_superseded_by_run_id"]
    assert "to_jsonb(OLD) - c_mutable" in body and "to_jsonb(NEW) - c_mutable" in body
    assert "TG_OP = 'TRUNCATE'" in body


def test_file_is_schema_code_only_no_data_grants_registry_or_transaction_control():
    code = _code(_M1265)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    assert "asset_registry" not in code and "_migrations_applied" not in code
    assert not re.search(r"\bGRANT\b", code), "no grant of any kind (the window grant is the runner's, not this file's)"
    assert code.count("REVOKE ALL ON FUNCTION") == 2 and code.count("FROM PUBLIC") == 2
    # the only DML is the rolled-back self-test probe
    assert len(re.findall(r"\bINSERT INTO\b", code)) == 1 and "1265_selftest_ok" in code
    assert not re.search(r"\b(DROP TABLE|DROP COLUMN|ALTER COLUMN|ADD COLUMN|CREATE TABLE|CREATE INDEX|DROP FUNCTION|DROP TRIGGER)\b", code)
    assert not re.search(r"ALTER TABLE\s+\S+\s+(DISABLE|ENABLE ROW|FORCE|NO FORCE)", code), "RLS is not touched"
    assert "ROW LEVEL SECURITY" not in code and "CREATE POLICY" not in code


def test_triggers_are_enable_always_and_have_the_expected_event_shapes():
    code = _code(_M1265)
    assert "BEFORE UPDATE OR DELETE ON public.mimamsa_predictions" in code and "FOR EACH ROW" in code
    assert "BEFORE TRUNCATE ON public.mimamsa_predictions" in code and "FOR EACH STATEMENT" in code
    assert len(re.findall(r"^ALTER TABLE public\.mimamsa_predictions ENABLE ALWAYS TRIGGER ", code, re.M)) == 2
    assert "tgtype <> 27" in code and "tgtype <> 34" in code and "tgtype <> 15" in code


def test_gate_names_the_missing_privilege_and_the_columns_it_was_written_against():
    code = _code(_M1265)
    for needle in ("has_schema_privilege(current_user, 'public', 'CREATE')", "protected public-schema window",
                   "pg_has_role(current_user, rel_owner, 'MEMBER')", "21-column table", "chart_context_superseded_by_run_id"):
        assert needle in code, needle


def test_header_states_the_decisions_privilege_order_rls_serving_effect_and_what_is_not_done():
    sql = _flat(_M1265)
    for needle in ("N-104", "HELD", "AFTER S-L1", "WHAT IT DOES", "CAPTURE", "MD5 GUARD", "DEFINITION OF \"FROZEN\"",
                   "PENDING rows are protected too", "allow-list", "mi_abhilekha.py:70", "prediction_lifecycle_sweep.ts:348",
                   "migration 680 rewrote", "191 of 195", "ONE exception, narrowly defined and data-driven",
                   "chart_subject_consent", "consent_state = 'withdrawn'", "no chart_subject_deletion_disputes",
                   "RAISE LOG", "TRUNCATE: refused always", "Break-glass", "CAN disable a trigger", "SELF-TEST",
                   "PRIVILEGE", "permission denied for schema public", "CREATE OR REPLACE FUNCTION of an EXISTING function",
                   "jataka-protected-migrations", "PROTECTED_PUBLIC_SCHEMA_MIGRATIONS", "THAT WIRING IS NOT IN THIS PR",
                   "D6-style owner-role executor", "ORDER (hard preconditions)", "mi_bhavisya.py:230",
                   "assetClearSpec.ts:149", "RLS (assessed, NOT done here)", "data_plane_builder", "SERVING EFFECT AT APPLY: none expected",
                   "nirmana_registry_receipt_invalidation does not fire", "NOT DONE HERE", "ROLLBACK", "VERIFICATION BY PRODUCTION STRUCTURE",
                   "suvarna_reader on production on 2026-10-03", "PostgreSQL 15.18", "BUILDER_GRANT_PLAN v1.3"):
        assert needle in sql, f"header no longer states: {needle}"


def test_number_and_name_follow_the_pattern_and_are_free_of_siblings():
    assert _M1265.name.startswith("1265_") and len(list(_MIG.glob("1265_*.sql"))) == 1
    assert 1200 <= int(_M1265.name[:4]) <= 1299


# -- LIVE tier: disposable PostgreSQL ------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@15/bin"))]
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


# Production role attributes (suvarna_reader, 2026-10-03). No application role is a superuser or BYPASSRLS.
ROLES = [
    # name, LOGIN, INHERIT, extra
    ("amjis_app", True, False, ""),
    ("amjis_inquiry_serve", True, True, ""),
    ("data_plane_builder", True, False, ""),
    ("data_plane_l1_owner", False, False, ""),
    ("data_plane_l2_owner", False, False, ""),
    ("data_plane_migrator", True, False, ""),
    ("data_plane_schema_owner", False, False, ""),
    ("data_plane_verifier", True, False, ""),
    ("nirmana_evidence_ingress_writer", True, False, ""),
    ("retrieval_census_ro", True, True, ""),
    ("role_jobs", False, True, ""),
    ("role_ledger_write", False, True, ""),
    ("role_orchestrator", False, True, ""),
    ("role_sidecar", False, True, ""),
    ("role_web_serve", False, True, ""),
    ("suvarna_reader", True, False, ""),
]
APP_ROLES = [r[0] for r in ROLES]
NOLOGIN_ROLES = {r[0] for r in ROLES if not r[1]}


@pytest.fixture(scope="module")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1265pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m65", dir="/tmp"))  # unix socket paths are length-limited
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            for name, login, inherit, extra in ROLES:
                c.execute(f"CREATE ROLE {name} {'LOGIN' if login else 'NOLOGIN'} {'INHERIT' if inherit else 'NOINHERIT'} "
                          f"NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS {extra}")
            c.execute("GRANT data_plane_l1_owner TO data_plane_migrator")
            c.execute("GRANT data_plane_l2_owner TO data_plane_migrator")
            c.execute("GRANT data_plane_schema_owner TO data_plane_migrator")
            c.execute("GRANT role_web_serve TO amjis_inquiry_serve")
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg, "bin": binp}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_WORLD_SQL = """
ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner, data_plane_l1_owner, data_plane_l2_owner;
GRANT USAGE ON SCHEMA public TO data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve,
  suvarna_reader, role_orchestrator, role_ledger_write, role_jobs, role_sidecar, retrieval_census_ro,
  nirmana_evidence_ingress_writer, amjis_inquiry_serve;

CREATE TABLE public.build_runs (id uuid PRIMARY KEY);
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
CREATE INDEX idx_mimamsa_predictions_lifecycle ON public.mimamsa_predictions (chart_id, lifecycle_status);
CREATE TABLE public.chart_subject_consent (
  chart_id uuid PRIMARY KEY, consent_state text NOT NULL CHECK (consent_state IN ('granted','withdrawn')),
  withdrawn_at timestamptz, CHECK (consent_state <> 'withdrawn' OR withdrawn_at IS NOT NULL));
CREATE TABLE public.chart_subject_deletion_disputes (
  dispute_id bigserial PRIMARY KEY, chart_id uuid NOT NULL,
  status text NOT NULL CHECK (status IN ('open','resolved','escalated','reopened')));

ALTER TABLE public.build_runs OWNER TO amjis_app;
ALTER TABLE public.mimamsa_predictions OWNER TO amjis_app;
ALTER TABLE public.chart_subject_consent OWNER TO amjis_app;
ALTER TABLE public.chart_subject_deletion_disputes OWNER TO amjis_app;
ALTER SEQUENCE public.chart_subject_deletion_disputes_dispute_id_seq OWNER TO amjis_app;

-- production ACLs (relacl read 2026-10-03)
REVOKE TRUNCATE ON public.mimamsa_predictions FROM amjis_app;
GRANT SELECT ON public.mimamsa_predictions TO retrieval_census_ro, role_web_serve, role_jobs, role_sidecar,
  nirmana_evidence_ingress_writer, suvarna_reader;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.mimamsa_predictions TO role_orchestrator;
GRANT SELECT, INSERT, UPDATE ON public.mimamsa_predictions TO role_ledger_write;
GRANT SELECT, INSERT, DELETE ON public.mimamsa_predictions TO data_plane_builder;
GRANT SELECT ON public.build_runs TO suvarna_reader, role_orchestrator;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chart_subject_consent TO role_web_serve;
GRANT SELECT ON public.chart_subject_consent TO retrieval_census_ro, role_jobs;
GRANT SELECT, INSERT ON public.chart_subject_deletion_disputes TO role_web_serve;
GRANT SELECT ON public.chart_subject_deletion_disputes TO retrieval_census_ro, role_jobs, suvarna_reader;
GRANT USAGE, SELECT ON SEQUENCE public.chart_subject_deletion_disputes_dispute_id_seq TO role_web_serve;
"""


def _install_builder_guard(c, body: str):
    """What the BUILDER_GRANT_PLAN executor left in production: function + trigger owned by amjis_app."""
    c.execute("CREATE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql "
              "SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS $guard$" + body + "$guard$")
    c.execute("REVOKE ALL ON FUNCTION public.mimamsa_predictions_builder_guard() FROM PUBLIC")
    c.execute("ALTER FUNCTION public.mimamsa_predictions_builder_guard() OWNER TO amjis_app")
    c.execute("CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT OR DELETE ON public.mimamsa_predictions "
              "FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()")


class World:
    def __init__(self, pg, name):
        self.pg, self.name = pg, name

    def connect(self, role="postgres", **kw):
        """LOGIN roles connect directly; the NOLOGIN group roles (role_*, data_plane_*_owner) are assumed with SET ROLE
        (production reaches them through a member login role), set outside the transaction so rollback keeps it."""
        psy = self.pg["psycopg"]
        if role in NOLOGIN_ROLES:
            conn = psy.connect(host=self.pg["sock"], port=self.pg["port"], user="postgres", dbname=self.name, autocommit=True)
            conn.execute(f"SET ROLE {role}")
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

    # -- the protected public-schema window, as scripts/jataka-schema-capability.ts does it
    def window(self, action):
        with self.connect("data_plane_migrator") as c:
            c.execute("SET LOCAL ROLE data_plane_schema_owner")
            c.execute("GRANT CREATE ON SCHEMA public TO amjis_app" if action == "grant"
                      else "REVOKE CREATE ON SCHEMA public FROM amjis_app")
            c.commit()

    def apply(self, sql, role="amjis_app", window=True, notices=None):
        """migrate.ts: BEGIN; <sql>; COMMIT, ROLLBACK on error. window=True wraps it in the grant/revoke window."""
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


_db_counter = 0


def _make_world(pg, builder_guard=True, seed=True) -> World:
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg = pg["psycopg"]
    with psycopg.connect(host=pg["sock"], port=pg["port"], user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")
    w = World(pg, name)
    with w.connect("postgres", autocommit=True) as c:
        c.execute(_WORLD_SQL)
        if builder_guard:
            _install_builder_guard(c, _body(_REAL, "guard"))
        if seed:
            for q in _seed_sql():
                c.execute(q)
    w.baseline_acl = w.schema_acl()
    return w


def _row(chart, pid, status="pending", **over):
    cols = {"chart_id": chart, "prediction_id": pid, "source_pramana_id": f"src_{pid}", "outcome_claim": f"claim {pid}",
            "domain": "career", "observation_window": "[2026-01-01,2026-06-01)", "eval_date": "2026-06-01",
            "confidence_band": "[0.4,0.7)", "magnitude_expected": "moderate", "falsifier_jsonb": '{"k":1}',
            "emitted_at": "2026-08-13T01:16:29Z", "lifecycle_status": status, "driving_signals": '["s1"]',
            "frozen_bundle_hash": f"h_{pid}", "bundle_formula_version": "v1"}
    cols.update(over)
    names = ", ".join(cols)
    vals = ", ".join("NULL" if v is None else "'" + str(v).replace("'", "''") + "'" for v in cols.values())
    return f"INSERT INTO public.mimamsa_predictions ({names}) VALUES ({vals})"


def _seed_sql() -> list[str]:
    s = []
    for i in range(3):
        s.append(_row(CHART_A, f"pred_a{i}"))
    s.append(_row(CHART_A, "pred_due", "due"))
    s.append(_row(CHART_A, "pred_conf", "confirmed"))
    s.append(_row(CHART_A, "pred_den", "denied"))
    s.append(_row(CHART_A, "pred_exp", "expired"))
    s.append(_row(CHART_B, "pred_b0"))
    s.append(_row(CHART_B, "pred_b1"))
    s.append(_row(CHART_C, "pred_c0"))
    return s


@pytest.fixture()
def world(pg_cluster):
    w = _make_world(pg_cluster)
    yield w
    with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres",
                                       dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


@pytest.fixture()
def applied(world):
    world.apply(_REAL)
    return world


def _refused(world, role, sql, params=None, prefix=PREFIX):
    """The statement must be refused BY THE GUARD (message prefix), never by a missing privilege."""
    psy = world.pg["psycopg"]
    with world.connect(role) as c:
        try:
            c.execute(sql, params)
        except psy.errors.InsufficientPrivilege as e:
            c.rollback()
            msg = str(e).splitlines()[0]
            assert msg.startswith(f"{prefix}") or prefix in msg, f"refused, but not by the guard: {msg}"
            return msg
        c.rollback()
    raise AssertionError(f"{role}: expected the guard to refuse: {sql}")


def _passes(world, role, sql, params=None):
    with world.connect(role) as c:
        cur = c.execute(sql, params)
        n = cur.rowcount
        c.rollback()
        return n


# ---- PRECONDITION: the 680 failure mode and the replaceable pending rows really are possible before 1265 ------

def test_before_1265_nothing_stops_a_frozen_column_rewrite_or_a_pending_delete(world):
    # migration 680's UPDATE of source_pramana_id on frozen rows, and mi_bhavisya's DELETE of pending rows
    assert _passes(world, "amjis_app", "UPDATE mimamsa_predictions SET source_pramana_id = 'x' WHERE chart_id = %s", (CHART_A,)) == 7
    assert _passes(world, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending','due')", (CHART_A,)) == 4
    assert _passes(world, "postgres", "TRUNCATE mimamsa_predictions") in (-1, 0)


# ---- PRIVILEGE DETERMINATION (mirrored roles, no superuser) ----------------------------------------------------

def test_the_routine_role_has_no_create_on_public_and_cannot_even_replace_an_existing_function(world):
    assert world.query("SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE')") == [(False, True)]
    psy = world.pg["psycopg"]
    with world.connect("amjis_app") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
            c.execute("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger "
                      "LANGUAGE plpgsql AS $x$ BEGIN RETURN NEW; END $x$")


def test_routine_runner_as_amjis_app_fails_at_the_gate_with_the_missing_privilege_and_changes_nothing(world):
    before = world.query("SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal ORDER BY 1")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException) as ei:
        world.apply(_REAL, window=False)
    msg = str(ei.value)
    assert "1265: missing privilege" in msg and "no CREATE on schema public" in msg and "protected public-schema window" in msg
    assert world.query("SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal ORDER BY 1") == before
    assert world.query("SELECT count(*) FROM pg_proc WHERE proname = 'mimamsa_predictions_frozen_row_guard'") == [(0,)]


def test_without_the_gate_the_raw_statement_would_have_failed_with_permission_denied(world):
    # mutant of the file with the gate removed: the first CREATE OR REPLACE FUNCTION fails inside PostgreSQL
    start = _REAL.index("-- 0. GATE")
    end = _REAL.index("-- 1a. CAPTURE guard")
    ungated = _REAL[:start] + _REAL[end:]
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
        world.apply(ungated, window=False)


def test_protected_window_applies_it_as_amjis_app_and_the_schema_acl_is_byte_identical_afterwards(world):
    notices: list[str] = []
    world.apply(_REAL, notices=notices)
    assert world.schema_acl() == world.baseline_acl, "the window must leave the schema ACL exactly as found"
    assert world.query("SELECT has_schema_privilege('amjis_app','public','CREATE')") == [(False,)]
    rows = world.query("SELECT p.proname, pg_get_userbyid(p.proowner), p.prosecdef, p.proacl::text, p.proconfig::text "
                       "FROM pg_proc p WHERE p.proname LIKE 'mimamsa_predictions_%guard' ORDER BY 1")
    assert rows == [("mimamsa_predictions_builder_guard", "amjis_app", False, "{amjis_app=X/amjis_app}", '{"search_path=pg_catalog, pg_temp"}'),
                    ("mimamsa_predictions_frozen_row_guard", "amjis_app", False, "{amjis_app=X/amjis_app}", '{"search_path=pg_catalog, pg_temp"}')]
    assert world.query("SELECT tgname, tgenabled, tgtype FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal ORDER BY 1") == [
        ("mimamsa_predictions_builder_guard", "O", 15), ("mimamsa_predictions_frozen_row_guard", "A", 27),
        ("mimamsa_predictions_frozen_row_guard_truncate", "A", 34)]
    # no row of the table was added, removed or changed
    assert world.query("SELECT count(*) FROM mimamsa_predictions") == [(10,)]
    assert any("TRUNCATE branch skipped" in n for n in notices), "amjis_app holds no TRUNCATE: the self-test says so honestly"


def test_captured_builder_guard_in_the_fixture_equals_the_capture_so_the_replace_is_a_no_op(world):
    before = world.query("SELECT md5(prosrc), length(prosrc), proacl::text, pg_get_userbyid(proowner) FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'")
    assert before[0][:2] == (BUILDER_MD5, BUILDER_LEN)
    world.apply(_REAL)
    assert world.query("SELECT md5(prosrc), length(prosrc), proacl::text, pg_get_userbyid(proowner) FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'") == before


def test_a_superuser_or_ci_replay_on_a_fresh_database_creates_everything(pg_cluster):
    w = _make_world(pg_cluster, builder_guard=False, seed=False)
    try:
        w.apply(_REAL, role="postgres", window=False)  # CI scratch DB: superuser, no builder guard yet
        assert w.query("SELECT md5(prosrc) FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'") == [(BUILDER_MD5,)]
        assert w.query("SELECT count(*) FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal") == [(3,)]
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


# ---- GUARD BEHAVIOUR (every case runs as a role that HOLDS the privilege, so a refusal can only be the guard) -----

ACTORS_UPDATE = ["amjis_app", "role_orchestrator", "role_ledger_write", "postgres"]
ACTORS_DELETE = ["amjis_app", "role_orchestrator", "data_plane_builder", "postgres"]


@pytest.mark.parametrize("col,newval", [
    ("chart_id", "'99999999-9999-4999-8999-999999999999'"), ("prediction_id", "'renamed'"), ("source_pramana_id", "'rewritten'"),
    ("outcome_claim", "'other claim'"), ("domain", "'health'"), ("observation_window", "'[2030-01-01,2030-02-01)'"),
    ("eval_date", "'2031-01-01'"), ("confidence_band", "'[0.1,0.2)'"), ("magnitude_expected", "'large'"),
    ("falsifier_jsonb", "'{\"k\":2}'"), ("base_rate", "0.5"), ("emitted_at", "'2020-01-01T00:00:00Z'"),
    ("driving_signals", "'[\"other\"]'"), ("frozen_bundle_hash", "'rehashed'"), ("bundle_formula_version", "'v2'"),
    ("created_at", "'2020-01-01T00:00:00Z'"), ("contact_id", "'sha256:abc'"),
])
@pytest.mark.parametrize("status_row", ["pred_a0", "pred_conf"])
def test_every_frozen_column_is_immutable_on_pending_and_terminal_rows(applied, col, newval, status_row):
    for role in ("amjis_app", "role_orchestrator", "postgres"):
        msg = _refused(applied, role, f"UPDATE mimamsa_predictions SET {col} = {newval} WHERE chart_id = %s AND prediction_id = %s",
                       (CHART_A, status_row))
        assert col in msg


@pytest.mark.parametrize("role", ACTORS_UPDATE)
def test_migration_680_style_rewrite_of_the_whole_chart_is_refused_for_every_role(applied, role):
    _refused(applied, role, "UPDATE mimamsa_predictions SET source_pramana_id = md5(source_pramana_id) WHERE chart_id = %s", (CHART_A,))


@pytest.mark.parametrize("role", ACTORS_DELETE)
@pytest.mark.parametrize("pid", ["pred_a0", "pred_due", "pred_conf", "pred_den", "pred_exp"])
def test_delete_is_refused_for_every_role_and_every_status_pending_and_due_included(applied, role, pid):
    # data_plane_builder on a terminal row is refused first by the captured builder guard (trigger-name order);
    # on pending/due rows only the new guard stops it (the builder guard allows those).
    prefix = "mimamsa_predictions_builder_guard:" if role == "data_plane_builder" and pid in ("pred_conf", "pred_den", "pred_exp") else PREFIX
    _refused(applied, role, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = %s", (CHART_A, pid), prefix=prefix)


def test_the_live_mi_bhavisya_delete_and_the_cockpit_clear_delete_now_fail_loudly(applied):
    sql = "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending', 'due')"
    _refused(applied, "amjis_app", sql, (CHART_A,))
    _refused(applied, "data_plane_builder", sql, (CHART_A,))  # allowed by the builder guard, refused by the frozen guard
    assert applied.query("SELECT count(*) FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,)) == [(7,)]


def test_a_delete_of_many_rows_is_refused_as_a_whole(applied):
    _refused(applied, "amjis_app", "DELETE FROM mimamsa_predictions")
    assert applied.query("SELECT count(*) FROM mimamsa_predictions") == [(10,)]


def test_truncate_is_refused_even_for_a_superuser(applied):
    _refused(applied, "postgres", "TRUNCATE mimamsa_predictions")
    _refused(applied, "postgres", "TRUNCATE mimamsa_predictions CASCADE")
    assert applied.query("SELECT count(*) FROM mimamsa_predictions") == [(10,)]


def test_the_owner_without_truncate_privilege_gets_permission_denied_not_the_guard_and_after_a_regrant_the_guard(applied):
    psy = applied.pg["psycopg"]
    with applied.connect("amjis_app") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for table mimamsa_predictions"):
            c.execute("TRUNCATE mimamsa_predictions")
    applied.exec("GRANT TRUNCATE ON mimamsa_predictions TO amjis_app")
    _refused(applied, "amjis_app", "TRUNCATE mimamsa_predictions")


def test_replication_role_replica_does_not_bypass_because_the_triggers_are_enable_always(applied):
    with applied.connect("postgres") as c:
        c.execute("SET session_replication_role = replica")
        psy = applied.pg["psycopg"]
        with pytest.raises(psy.errors.InsufficientPrivilege, match=PREFIX):
            c.execute("UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_A,))
        c.rollback()
        c.execute("SET session_replication_role = replica")
        with pytest.raises(psy.errors.InsufficientPrivilege, match=PREFIX):
            c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,))


def test_disabling_the_trigger_is_possible_for_the_owner_and_leaves_a_visible_signature(applied):
    """Honest limit: PostgreSQL cannot stop a table owner. The detector is tgenabled <> 'A'."""
    applied.exec("ALTER TABLE mimamsa_predictions DISABLE TRIGGER mimamsa_predictions_frozen_row_guard", role="amjis_app")
    assert applied.query("SELECT tgenabled FROM pg_trigger WHERE tgname = 'mimamsa_predictions_frozen_row_guard'") == [("D",)]
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_A,)) == 7


def test_non_owner_roles_cannot_disable_it(applied):
    psy = applied.pg["psycopg"]
    for role in ("role_orchestrator", "role_ledger_write", "data_plane_builder"):
        with applied.connect(role) as c:
            with pytest.raises(psy.errors.InsufficientPrivilege):
                c.execute("ALTER TABLE mimamsa_predictions DISABLE TRIGGER mimamsa_predictions_frozen_row_guard")


def test_the_legal_status_transitions_the_live_writers_issue_pass_with_their_exact_statements(applied):
    # mi_abhilekha.py:70
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s AND lifecycle_status = 'pending'",
                   ("confirmed", CHART_A, "pred_a0")) == 1
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s AND lifecycle_status = 'pending'",
                   ("denied", CHART_A, "pred_a1")) == 1
    # prediction_lifecycle_sweep.ts:348
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = $1 AND prediction_id = $2".replace("$1", "%s").replace("$2", "%s"),
                   (CHART_A, "pred_a2")) == 1
    for src, dst in [("pred_a0", "due"), ("pred_a0", "partial"), ("pred_due", "confirmed"), ("pred_due", "denied"),
                     ("pred_due", "partial"), ("pred_due", "expired")]:
        assert _passes(applied, "role_ledger_write", "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s",
                       (dst, CHART_A, src)) == 1, (src, dst)
    # a no-op update (the sweep re-run on an already expired row) is allowed
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = %s AND prediction_id = 'pred_exp'", (CHART_A,)) == 1


@pytest.mark.parametrize("pid,dst", [
    ("pred_conf", "pending"), ("pred_conf", "denied"), ("pred_conf", "expired"), ("pred_conf", "due"),
    ("pred_den", "confirmed"), ("pred_exp", "pending"), ("pred_exp", "confirmed"),
    ("pred_due", "pending"), ("pred_a0", "bogus"), ("pred_a0", "Confirmed"), ("pred_a0", "detected"),
])
def test_a_terminal_status_never_changes_and_no_regression_or_unknown_status_is_accepted(applied, pid, dst):
    for role in ("amjis_app", "postgres"):
        _refused(applied, role, "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s", (dst, CHART_A, pid))


def test_terminal_rows_are_fully_frozen_but_still_take_the_stale_marker(applied):
    mark = ("UPDATE mimamsa_predictions SET chart_context_stale_at = NOW(), chart_context_stale_reason = 'chart_details_changed', "
            "chart_context_superseded_by_run_id = %s WHERE chart_id = %s AND chart_context_stale_at IS NULL")
    applied.exec("INSERT INTO build_runs VALUES ('aaaaaaaa-0000-4000-8000-000000000001'), ('aaaaaaaa-0000-4000-8000-000000000002')")
    # recomputeChart / chartContextStaleness.ts statement: all 7 rows of the chart, pending AND terminal
    assert _passes(applied, "amjis_app", mark, ("aaaaaaaa-0000-4000-8000-000000000001", CHART_A)) == 7


def test_the_stale_marker_is_set_once_and_never_changed_or_cleared(applied):
    applied.exec("INSERT INTO build_runs VALUES ('aaaaaaaa-0000-4000-8000-000000000001'), ('aaaaaaaa-0000-4000-8000-000000000002')")
    applied.exec("UPDATE mimamsa_predictions SET chart_context_stale_at = '2026-09-01T00:00:00Z', chart_context_stale_reason = 'chart_details_changed', "
                 f"chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000001' WHERE chart_id = '{CHART_A}'")
    _refused(applied, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NULL, chart_context_stale_reason = NULL WHERE chart_id = %s", (CHART_A,))
    _refused(applied, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NOW() WHERE chart_id = %s", (CHART_A,))
    _refused(applied, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000002' WHERE chart_id = %s", (CHART_A,))
    # the idempotent re-marking statement touches no already-stale row, so it passes with zero rows
    assert _passes(applied, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NOW(), chart_context_stale_reason = 'chart_details_changed', "
                   "chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000002' WHERE chart_id = %s AND chart_context_stale_at IS NULL", (CHART_A,)) == 0
    # a run link without the marker is refused
    _refused(applied, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000002' WHERE chart_id = %s", (CHART_B,))


def test_on_delete_set_null_of_the_supersession_column_still_works_through_the_guard(applied):
    applied.exec("INSERT INTO build_runs VALUES ('aaaaaaaa-0000-4000-8000-000000000001')")
    applied.exec("UPDATE mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed', "
                 f"chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000001' WHERE chart_id = '{CHART_A}'")
    assert applied.query("SELECT count(*) FROM mimamsa_predictions WHERE chart_context_superseded_by_run_id IS NOT NULL") == [(7,)]
    applied.exec("DELETE FROM build_runs WHERE id = 'aaaaaaaa-0000-4000-8000-000000000001'", role="amjis_app")
    assert applied.query("SELECT count(*) FROM mimamsa_predictions WHERE chart_context_superseded_by_run_id IS NOT NULL") == [(0,)]
    # the marker itself survives (an additive fact), only the run link is cleared
    assert applied.query("SELECT count(*) FROM mimamsa_predictions WHERE chart_context_stale_at IS NOT NULL") == [(7,)]


def test_insert_is_not_touched_by_the_new_guard_and_the_builder_guard_still_works(applied):
    assert applied.exec(_row(CHART_C, "pred_new"), role="amjis_app") is None
    assert applied.exec(_row(CHART_C, "pred_new2", "pending"), role="data_plane_builder") is None
    psy = applied.pg["psycopg"]
    with applied.connect("data_plane_builder") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="mimamsa_predictions_builder_guard: data_plane_builder may insert only pending/due"):
            c.execute(_row(CHART_C, "pred_bad", "confirmed"))


# ---- THE ONE EXCEPTION: subject withdrawal ---------------------------------------------------------------------

def test_delete_is_authorized_only_for_a_chart_whose_subject_withdrew_and_has_no_open_dispute(applied):
    q = "DELETE FROM mimamsa_predictions WHERE chart_id = %s"
    # consent granted: refused
    applied.exec("INSERT INTO chart_subject_consent VALUES (%s, 'granted', NULL)", (CHART_B,))
    _refused(applied, "amjis_app", q, (CHART_B,))
    # withdrawn: the sweep's own statement passes, for pending rows too
    applied.exec("UPDATE chart_subject_consent SET consent_state = 'withdrawn', withdrawn_at = now() WHERE chart_id = %s", (CHART_B,))
    assert _passes(applied, "amjis_app", q + " AND lifecycle_status = 'pending'", (CHART_B,)) == 2
    assert _passes(applied, "amjis_app", q, (CHART_B,)) == 2
    # the authorization is per chart: another chart is still refused in the same statement
    _refused(applied, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id IN (%s, %s)", (CHART_B, CHART_A))
    # an open / reopened / escalated dispute blocks it again; a resolved one does not
    for status, ok in (("open", False), ("reopened", False), ("escalated", False), ("resolved", True)):
        applied.exec("DELETE FROM chart_subject_deletion_disputes")
        applied.exec("INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, %s)", (CHART_B, status))
        if ok:
            assert _passes(applied, "amjis_app", q, (CHART_B,)) == 2, status
        else:
            _refused(applied, "amjis_app", q, (CHART_B,))
    # withdrawal does not unfreeze UPDATE of content
    applied.exec("DELETE FROM chart_subject_deletion_disputes")
    _refused(applied, "amjis_app", "UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_B,))


def test_the_withdrawal_exception_fails_closed_when_the_invoker_cannot_read_the_consent_tables(applied):
    applied.exec("INSERT INTO chart_subject_consent VALUES (%s, 'withdrawn', now())", (CHART_B,))
    # role_orchestrator holds DELETE on the ledger but NO privilege on the consent tables (576 revokes it): refused
    _refused(applied, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    assert _passes(applied, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,)) == 2


def test_the_withdrawal_exception_fails_closed_when_the_consent_tables_do_not_exist(pg_cluster):
    w = _make_world(pg_cluster)
    try:
        w.exec("DROP TABLE chart_subject_consent; DROP TABLE chart_subject_deletion_disputes")
        w.apply(_REAL)
        _refused(w, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


def test_no_session_setting_or_role_name_opens_an_exception(applied):
    for setting in ("SET madhav.allow_frozen_delete = 'on'", "RESET session_authorization", "SET app.chart_context = '" + CHART_A + "'",
                    "SET madhav.frozen_row_erasure = 'subject_withdrawal'"):
        psy = applied.pg["psycopg"]
        with applied.connect("amjis_app") as c:
            c.execute(setting)
            with pytest.raises(psy.errors.InsufficientPrivilege, match=PREFIX):
                c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,))


# ---- MD5 GUARD, REFUSALS, IDEMPOTENCE --------------------------------------------------------------------------

def _catalog_state(w):
    return w.query("SELECT p.proname, md5(p.prosrc), p.prosecdef, p.proacl::text, p.proconfig::text, pg_get_userbyid(p.proowner) FROM pg_proc p "
                   "WHERE p.proname LIKE 'mimamsa_predictions_%guard' ORDER BY 1") + \
           w.query("SELECT tgname, tgenabled, tgtype FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal ORDER BY 1")


def test_rerun_is_idempotent_and_changes_nothing(world):
    world.apply(_REAL)
    state = _catalog_state(world)
    world.apply(_REAL)
    world.apply(_REAL)
    assert _catalog_state(world) == state
    assert world.schema_acl() == world.baseline_acl


def test_md5_guard_refuses_a_different_live_builder_guard_body_and_changes_nothing(world):
    world.window("grant")
    try:
        world.exec("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql "
                   "SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS $g$" + _body(_REAL, "guard").replace("'pending', 'due'", "'pending', 'due', 'confirmed'") + "$g$",
                   role="amjis_app")
    finally:
        world.window("revoke")
    before = _catalog_state(world)
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="refusing to overwrite it"):
        world.apply(_REAL)
    assert _catalog_state(world) == before
    assert world.query("SELECT count(*) FROM pg_proc WHERE proname = 'mimamsa_predictions_frozen_row_guard'") == [(0,)]


def test_md5_guard_refuses_a_one_byte_change_even_when_the_length_is_unchanged(world):
    world.window("grant")
    try:
        body = _body(_REAL, "guard").replace("refusing chart_id", "refusing chart_ID")
        assert len(body) == BUILDER_LEN and hashlib.md5(body.encode()).hexdigest() != BUILDER_MD5
        world.exec("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql "
                   "SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS $g$" + body + "$g$", role="amjis_app")
    finally:
        world.window("revoke")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="refusing to overwrite it"):
        world.apply(_REAL)


@pytest.mark.parametrize("alter", ["SECURITY DEFINER", "SET search_path = public", "STABLE"])
def test_attribute_drift_of_the_live_builder_guard_with_the_same_body_is_refused(world, alter):
    world.exec(f"ALTER FUNCTION public.mimamsa_predictions_builder_guard() {alter}", role="amjis_app")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="other attributes"):
        world.apply(_REAL)


def test_a_live_builder_trigger_with_another_shape_is_refused(world):
    world.exec("DROP TRIGGER mimamsa_predictions_builder_guard ON mimamsa_predictions; "
               "CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT ON mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()",
               role="amjis_app")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="is not the captured one"):
        world.apply(_REAL)


def test_a_changed_live_frozen_guard_is_refused_but_the_exact_one_is_replaced_quietly(world):
    world.apply(_REAL)
    world.window("grant")
    try:
        world.exec("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_frozen_row_guard() RETURNS trigger LANGUAGE plpgsql "
                   "SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS $g$ BEGIN RETURN NEW; END $g$", role="amjis_app")
    finally:
        world.window("revoke")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="refusing to overwrite a changed live guard"):
        world.apply(_REAL)


def test_missing_columns_or_table_are_refused_by_the_gate(world):
    world.exec("ALTER TABLE mimamsa_predictions DROP COLUMN contact_id", role="amjis_app")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="has no column contact_id"):
        world.apply(_REAL)


def test_a_non_owner_that_has_create_is_refused_by_the_gate(world):
    with world.connect("data_plane_migrator") as c:
        c.execute("SET LOCAL ROLE data_plane_schema_owner")
        c.execute("GRANT CREATE ON SCHEMA public TO role_orchestrator")
        c.commit()
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="not a member of the table owner"):
        world.apply(_REAL, role="role_orchestrator", window=False)


def test_lock_timeout_fails_fast_when_another_session_holds_the_table(world):
    psy = world.pg["psycopg"]
    holder = world.connect("amjis_app")
    holder.execute("LOCK TABLE mimamsa_predictions IN ACCESS EXCLUSIVE MODE")
    try:
        with pytest.raises(psy.errors.LockNotAvailable):
            world.apply(_REAL)
    finally:
        holder.rollback()
        holder.close()


# ---- SELF-TEST DETECTOR is itself non-vacuous ------------------------------------------------------------------

def _strip_selftest(sql: str) -> str:
    a = sql.index("-- 3. SELF-TEST")
    b = sql.index("-- 4. POST-CHECK")
    return sql[:a] + sql[b:]


def _rebuild_md5(sql: str) -> str:
    """After mutating the frozen body, re-pin its md5 so the md5 post-check does not mask the behavioural mutant."""
    old = hashlib.md5(_body(_REAL, "frozen").encode()).hexdigest()
    new = hashlib.md5(_body(sql, "frozen").encode()).hexdigest()
    return sql.replace(old, new)


def _mutate(old: str, new: str, count: int = 1, tag: str = "frozen") -> str:
    body = _body(_REAL, tag)
    assert body.count(old) == count, f"mutation target not found exactly {count}x: {old!r} ({body.count(old)})"
    sql = _REAL.replace(body, body.replace(old, new))
    return _rebuild_md5(sql) if tag == "frozen" else sql


def test_selftest_is_in_the_file_and_touches_nothing_it_leaves_behind(world):
    world.apply(_REAL)
    assert world.query("SELECT count(*) FROM mimamsa_predictions WHERE prediction_id = 'm1265_probe'") == [(0,)]


# ---- BEHAVIOUR PROBES shared by the main proof and the mutants -------------------------------------------------

def run_probes(w: World) -> list[str]:
    """Apply nothing; probe an already-applied world. Returns the names of probes that did NOT behave. Roles hold the
    privilege each statement needs, so a refusal can only come from the guard."""
    psy = w.pg["psycopg"]
    failed: list[str] = []

    def must_refuse(name, role, sql, params=None, contains=None):
        with w.connect(role) as c:
            try:
                c.execute(sql, params)
                failed.append(f"{name}: not refused")
            except psy.errors.InsufficientPrivilege as e:
                if PREFIX not in str(e) or (contains and contains not in str(e)):
                    failed.append(f"{name}: refused by something else: {str(e).splitlines()[0]}")
            except Exception as e:  # noqa: BLE001
                failed.append(f"{name}: unexpected {type(e).__name__}")
            finally:
                c.rollback()

    def must_pass(name, role, sql, params=None, rows=None):
        with w.connect(role) as c:
            try:
                cur = c.execute(sql, params)
                if rows is not None and cur.rowcount != rows:
                    failed.append(f"{name}: affected {cur.rowcount}, expected {rows}")
            except Exception as e:  # noqa: BLE001
                failed.append(f"{name}: refused {type(e).__name__}")
            finally:
                c.rollback()

    for col, val in [("source_pramana_id", "'x'"), ("outcome_claim", "'x'"), ("eval_date", "'2031-01-01'"), ("falsifier_jsonb", "'{}'"),
                     ("frozen_bundle_hash", "'x'"), ("contact_id", "'x'"), ("prediction_id", "'x'"), ("confidence_band", "'[0.1,0.2)'")]:
        must_refuse(f"update {col} pending", "amjis_app", f"UPDATE mimamsa_predictions SET {col} = {val} WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,))
        must_refuse(f"update {col} terminal", "postgres", f"UPDATE mimamsa_predictions SET {col} = {val} WHERE chart_id = %s AND prediction_id = 'pred_conf'", (CHART_A,))
    must_refuse("delete pending", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,))
    must_refuse("delete due by builder", "data_plane_builder", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_due'", (CHART_A,))
    must_refuse("delete terminal", "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_conf'", (CHART_A,))
    must_refuse("truncate", "postgres", "TRUNCATE mimamsa_predictions", contains="TRUNCATE of public.mimamsa_predictions is refused")
    must_refuse("status set to NULL", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = NULL WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,), contains="transition")
    must_refuse("terminal to pending", "postgres", "UPDATE mimamsa_predictions SET lifecycle_status = 'pending' WHERE chart_id = %s AND prediction_id = 'pred_conf'", (CHART_A,))
    must_refuse("confirmed to denied", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'denied' WHERE chart_id = %s AND prediction_id = 'pred_conf'", (CHART_A,))
    must_refuse("unknown status", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'bogus' WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,))
    must_refuse("due to pending", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'pending' WHERE chart_id = %s AND prediction_id = 'pred_due'", (CHART_A,))
    must_pass("pending to confirmed", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'confirmed' WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,), rows=1)
    must_pass("pending to expired", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = %s AND prediction_id = 'pred_a1'", (CHART_A,), rows=1)
    must_pass("due to partial", "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'partial' WHERE chart_id = %s AND prediction_id = 'pred_due'", (CHART_A,), rows=1)
    must_pass("stale marking", "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed' WHERE chart_id = %s AND chart_context_stale_at IS NULL", (CHART_A,), rows=7)
    # no session setting opens an exception (the names a bypass might plausibly read)
    for setting in ("madhav.allow_frozen_delete", "madhav.frozen_row_erasure", "madhav.migration_bypass", "app.allow_frozen_delete"):
        with w.connect("amjis_app") as c:
            c.execute(f"SET {setting} = 'on'")
            try:
                c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a2'", (CHART_A,))
                failed.append(f"setting {setting}: delete not refused")
            except psy.errors.InsufficientPrivilege as e:
                if PREFIX not in str(e):
                    failed.append(f"setting {setting}: refused by something else")
            c.rollback()
    # replica role must not bypass
    with w.connect("postgres") as c:
        c.execute("SET session_replication_role = replica")
        try:
            c.execute("UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_A,))
            failed.append("replica update: not refused")
        except psy.errors.InsufficientPrivilege:
            pass
        c.rollback()
    # withdrawal exception: granted -> refused, withdrawn -> passes, withdrawn+open dispute -> refused
    with w.connect("postgres") as c:
        c.execute("INSERT INTO chart_subject_consent VALUES (%s, 'granted', NULL)", (CHART_B,))
        c.commit()
    must_refuse("delete after consent granted", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    with w.connect("postgres") as c:
        c.execute("UPDATE chart_subject_consent SET consent_state = 'withdrawn', withdrawn_at = now() WHERE chart_id = %s", (CHART_B,))
        c.commit()
    must_pass("delete after withdrawal", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), rows=2)
    with w.connect("postgres") as c:
        c.execute("INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, 'open')", (CHART_B,))
        c.commit()
    must_refuse("delete after withdrawal with open dispute", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    with w.connect("postgres") as c:
        c.execute("DELETE FROM chart_subject_deletion_disputes")
        c.execute("DELETE FROM chart_subject_consent")
        c.commit()
    # ON DELETE SET NULL
    with w.connect("postgres") as c:
        c.execute("INSERT INTO build_runs VALUES ('aaaaaaaa-0000-4000-8000-000000000009')")
        c.execute("UPDATE mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed', chart_context_superseded_by_run_id = 'aaaaaaaa-0000-4000-8000-000000000009' WHERE chart_id = %s", (CHART_C,))
        c.commit()
    must_pass("set null via build_runs delete", "amjis_app", "DELETE FROM build_runs WHERE id = 'aaaaaaaa-0000-4000-8000-000000000009'")
    must_refuse("clear stale marker", "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NULL, chart_context_stale_reason = NULL WHERE chart_id = %s", (CHART_C,))
    return failed


def test_probe_suite_passes_on_the_real_file(applied):
    assert run_probes(applied) == []


MUTANTS = [
    ("delete refusal removed (pending deletable)", dict(old="  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted", new="  RETURN OLD; RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted")),
    ("pending rows exempt from delete", dict(old="  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted", new="  IF OLD.lifecycle_status IN ('pending', 'due') THEN RETURN OLD; END IF;\n  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted")),
    ("frozen columns not compared (guard on status only)", dict(old="IF v_new IS DISTINCT FROM v_old THEN", new="IF false THEN")),
    ("source_pramana_id added to the allow-list", dict(old="ARRAY['lifecycle_status', 'chart_context_stale_at',", new="ARRAY['lifecycle_status', 'source_pramana_id', 'chart_context_stale_at',")),
    ("pending rows exempt from the column check", dict(old="    IF v_new IS DISTINCT FROM v_old THEN", new="    IF v_new IS DISTINCT FROM v_old AND OLD.lifecycle_status <> 'pending' THEN")),
    ("terminal statuses may change", dict(old="OR (OLD.lifecycle_status = 'due'     AND NEW.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired')),", new="OR (OLD.lifecycle_status = 'due'     AND NEW.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired')) OR OLD.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired'),")),
    ("unknown target status accepted", dict(old="NEW.lifecycle_status IN ('due', 'confirmed', 'denied', 'partial', 'expired'))", new="true)")),
    ("NULL transition result not coalesced to false", dict(old="           false)\n      THEN", new="           true)\n      THEN")),
    ("TRUNCATE branch removed", dict(old="  IF TG_OP = 'TRUNCATE' THEN\n    RAISE EXCEPTION", new="  IF false THEN\n    RAISE EXCEPTION")),
    ("withdrawal exception ignores the consent state", dict(old="WHERE c.chart_id = OLD.chart_id AND c.consent_state = 'withdrawn')", new="WHERE c.chart_id = OLD.chart_id)")),
    ("withdrawal exception ignores open disputes", dict(old="\n         AND NOT EXISTS (SELECT 1 FROM public.chart_subject_deletion_disputes d\n                          WHERE d.chart_id = OLD.chart_id AND d.status IN ('open', 'reopened', 'escalated'))", new="")),
    ("stale marker may be cleared", dict(old="    IF OLD.chart_context_stale_at IS NOT NULL\n       AND", new="    IF false\n       AND")),
    ("any role named amjis_app is exempt", dict(old="  IF TG_OP = 'TRUNCATE' THEN\n", new="  IF current_user = 'amjis_app' AND TG_OP <> 'TRUNCATE' THEN RETURN COALESCE(NEW, OLD); END IF;\n  IF TG_OP = 'TRUNCATE' THEN\n")),
    ("a session setting turns the guard off", dict(old="  IF TG_OP = 'TRUNCATE' THEN\n", new="  IF current_setting('madhav.allow_frozen_delete', true) = 'on' THEN RETURN COALESCE(NEW, OLD); END IF;\n  IF TG_OP = 'TRUNCATE' THEN\n")),
]


@pytest.mark.parametrize("name,spec", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_caught_by_the_behaviour_probes_with_the_in_migration_self_test_removed(pg_cluster, name, spec):
    mutant = _strip_selftest(_mutate(**spec))
    w = _make_world(pg_cluster)
    try:
        w.apply(mutant)
        failed = run_probes(w)
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")
    assert failed, f"mutant survived the probes: {name}"


@pytest.mark.parametrize("name,spec", MUTANTS[:6] + MUTANTS[8:9], ids=[m[0] for m in MUTANTS[:6] + MUTANTS[8:9]])
def test_the_same_mutants_are_also_caught_by_the_migrations_own_self_test(pg_cluster, name, spec):
    mutant = _mutate(**spec)
    w = _make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        try:
            w.apply(mutant)
        except psy.errors.RaiseException as e:
            assert "1265 self-test FAILED" in str(e) or "TRUNCATE" in str(e) or "post-check" in str(e), str(e)
            return
        # the TRUNCATE branch is not self-testable as amjis_app (no privilege): it must then be caught by the probes
        assert "TRUNCATE" in name, f"mutant survived the in-migration self-test: {name}"
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


FILE_MUTANTS = [
    ("md5 guard on the builder body neutered", lambda s: s.replace("IF f.body_md5 <> '" + BUILDER_MD5 + "' OR f.body_len <> 1084 THEN", "IF false THEN")),
    ("builder trigger shape check neutered", lambda s: s.replace("ELSIF t.tgtype <> 15 OR", "ELSIF false AND t.tgtype <> 15 OR")),
    ("frozen guard md5 refusal neutered", lambda s: s.replace("IF live_md5 IS NOT NULL AND live_md5 <>", "IF false AND live_md5 <>")),
    ("ENABLE ALWAYS dropped", lambda s: s.replace("ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard;\n", "")),
    ("truncate trigger dropped", lambda s: s.replace("""    CREATE TRIGGER mimamsa_predictions_frozen_row_guard_truncate
      BEFORE TRUNCATE ON public.mimamsa_predictions
      FOR EACH STATEMENT EXECUTE FUNCTION public.mimamsa_predictions_frozen_row_guard();""", "    NULL;")),
    ("privilege gate neutered", lambda s: s.replace("IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN", "IF false THEN")),
]


def test_file_mutant_gate_neutered_is_caught_by_the_privilege_test(world):
    mutant = FILE_MUTANTS[5][1](_REAL)
    assert mutant != _REAL
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
        world.apply(mutant, window=False)  # the explicit message is gone, the privilege failure remains and the test still sees it


def test_file_mutant_enable_always_dropped_is_caught_by_the_replica_probe_and_the_post_check(pg_cluster):
    mutant = FILE_MUTANTS[3][1](_REAL)
    assert mutant != _REAL
    w = _make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        with pytest.raises(psy.errors.RaiseException, match="post-check: the three triggers"):
            w.apply(mutant)
        # with the post-check also removed the replica probe still sees the bypass
        w.apply(_strip_selftest(mutant).replace("""  IF (SELECT count(*) FROM pg_trigger WHERE tgrelid""", """  IF false AND (SELECT count(*) FROM pg_trigger WHERE tgrelid"""))
        assert any("replica" in f for f in run_probes(w))
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


def test_file_mutant_truncate_trigger_dropped_is_caught_by_the_post_check_and_the_truncate_probe(pg_cluster):
    mutant = FILE_MUTANTS[4][1](_REAL)
    assert mutant != _REAL
    w = _make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        with pytest.raises(Exception):
            w.apply(mutant)  # ALTER TABLE ... ENABLE ALWAYS TRIGGER ..._truncate fails: no such trigger
        w2 = mutant.replace("ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard_truncate;\n", "")
        with pytest.raises(psy.errors.RaiseException, match="post-check: the three triggers"):
            w.apply(w2)
        w.apply(_strip_selftest(w2).replace("""  IF (SELECT count(*) FROM pg_trigger WHERE tgrelid""", """  IF false AND (SELECT count(*) FROM pg_trigger WHERE tgrelid"""))
        assert any("truncate" in f for f in run_probes(w))
    finally:
        with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


def test_file_mutants_md5_guards_neutered_are_caught_by_the_refusal_tests(pg_cluster):
    for idx, expect in ((0, "builder"), (1, "trigger"), (2, "frozen")):
        mutant = FILE_MUTANTS[idx][1](_REAL)
        assert mutant != _REAL, idx
        w = _make_world(pg_cluster)
        try:
            w.window("grant")
            try:
                if idx == 0:
                    w.exec("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER "
                           "SET search_path = pg_catalog, pg_temp AS $g$" + _body(_REAL, "guard").replace("'pending', 'due'", "'pending', 'due', 'confirmed'") + "$g$", role="amjis_app")
                elif idx == 1:
                    w.exec("DROP TRIGGER mimamsa_predictions_builder_guard ON mimamsa_predictions; CREATE TRIGGER mimamsa_predictions_builder_guard "
                           "BEFORE INSERT ON mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()", role="amjis_app")
                else:
                    pass
            finally:
                w.window("revoke")
            if idx == 2:
                w.apply(_REAL)  # first apply creates it (amjis_app, in the window)
                w.window("grant")
                try:
                    w.exec("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_frozen_row_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER "
                           "SET search_path = pg_catalog, pg_temp AS $g$ BEGIN RETURN NEW; END $g$", role="amjis_app")
                finally:
                    w.window("revoke")
            # the real file refuses...
            psy = pg_cluster["psycopg"]
            with pytest.raises(psy.errors.RaiseException):
                w.apply(_REAL)
            # ...and the mutant does not (that is what makes the refusal test non-vacuous)
            w.apply(mutant)
        finally:
            with pg_cluster["psycopg"].connect(host=pg_cluster["sock"], port=pg_cluster["port"], user="postgres", dbname="postgres", autocommit=True) as c:
                c.execute(f"DROP DATABASE IF EXISTS {w.name} WITH (FORCE)")


# ---- RLS ASSESSMENT (migration 576's g1c policies) --------------------------------------------------------------

def _install_g1c(w: World):
    """The policies as they are live (pg_policy, read 2026-10-03) plus app_chart_context() verbatim (md5 c8e77092...)."""
    w.exec("""
CREATE OR REPLACE FUNCTION app_chart_context() RETURNS uuid LANGUAGE plpgsql STABLE PARALLEL SAFE AS $ctx$
DECLARE
  raw text;
BEGIN
  raw := nullif(current_setting('app.chart_context', true), '');
  IF raw IS NULL THEN
    RETURN NULL;
  END IF;
  BEGIN
    RETURN raw::uuid;
  EXCEPTION WHEN others THEN
    RETURN NULL;   -- malformed pin == no pin == deny
  END;
END
$ctx$;
GRANT EXECUTE ON FUNCTION app_chart_context() TO PUBLIC;
CREATE POLICY mimamsa_predictions_g1c_chart_context ON mimamsa_predictions AS PERMISSIVE FOR ALL TO role_web_serve, role_sidecar
  USING (chart_id = app_chart_context()) WITH CHECK (chart_id = app_chart_context());
CREATE POLICY mimamsa_predictions_g1c_unscoped ON mimamsa_predictions AS PERMISSIVE FOR ALL TO role_orchestrator, role_ledger_write, role_jobs
  USING (true) WITH CHECK (true);
""")


def _count(w, role, pin=None):
    with w.connect(role) as c:
        if pin:
            c.execute(f"SET app.chart_context = '{pin}'")
        n = c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0]
        c.rollback()
        return n


def test_rls_arming_is_within_the_routine_role_but_hides_every_row_from_roles_without_a_policy(world):
    _install_g1c(world)
    assert [r[0] for r in world.query("SELECT polname FROM pg_policy WHERE polrelid = 'mimamsa_predictions'::regclass ORDER BY 1")] == [
        "mimamsa_predictions_g1c_chart_context", "mimamsa_predictions_g1c_unscoped"]
    # arming needs table ownership: the ROUTINE role amjis_app is the owner, so it can (no protected window needed)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    assert world.query("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'mimamsa_predictions'::regclass") == [(True, False)]
    psy = world.pg["psycopg"]
    with world.connect("role_orchestrator") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege):
            c.execute("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY")
    total = 10
    # owner and superuser bypass (no FORCE)
    assert _count(world, "amjis_app") == total and _count(world, "postgres") == total
    # roles with a policy
    assert _count(world, "role_orchestrator") == total and _count(world, "role_ledger_write") == total and _count(world, "role_jobs") == total
    # the chart-pinned serving roles: unpinned = nothing, pinned = that chart only
    assert _count(world, "role_web_serve") == 0 and _count(world, "role_web_serve", CHART_A) == 7 and _count(world, "role_web_serve", CHART_B) == 2
    assert _count(world, "amjis_inquiry_serve") == 0 and _count(world, "amjis_inquiry_serve", CHART_B) == 2
    assert _count(world, "role_sidecar") == 0 and _count(world, "role_sidecar", CHART_C) == 1
    # roles with a SELECT grant but NO policy are blinded: the reader, census, evidence ingress, and the S-L1 BUILDER
    for role in ("suvarna_reader", "retrieval_census_ro", "nirmana_evidence_ingress_writer", "data_plane_builder"):
        assert _count(world, role) == 0, role


def test_rls_arming_breaks_the_data_plane_builder_silently_on_delete_and_loudly_on_insert(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    psy = world.pg["psycopg"]
    with world.connect("data_plane_builder") as c:
        # mi_bhavisya's delete-then-insert: the DELETE sees no rows (a SILENT no-op), the INSERT is refused by RLS
        assert c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending','due')", (CHART_A,)).rowcount == 0
        with pytest.raises(psy.errors.InsufficientPrivilege, match="row-level security"):
            c.execute(_row(CHART_C, "pred_new"))


def test_rls_pin_is_client_asserted_so_a_serving_session_can_re_pin_itself(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    with world.connect("role_web_serve") as c:
        c.execute(f"SET app.chart_context = '{CHART_A}'")
        assert c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0] == 7
        c.execute(f"SET app.chart_context = '{CHART_B}'")  # nothing in the database stops this
        assert c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0] == 2


def test_rls_does_not_provide_immutability_the_owner_and_the_unscoped_roles_can_still_rewrite_frozen_rows(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    assert _passes(world, "amjis_app", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'") == 10
    assert _passes(world, "role_orchestrator", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'") == 10
    assert _passes(world, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE lifecycle_status = 'pending'") == 6


def test_with_rls_armed_and_1265_applied_the_guard_still_holds_independently_of_rls(world):
    world.apply(_REAL)
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    _refused(world, "amjis_app", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'")
    _refused(world, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE lifecycle_status = 'pending'")
    # and the builder's delete is a silent no-op (RLS hides the rows), the guard never sees it
    with world.connect("data_plane_builder") as c:
        assert c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,)).rowcount == 0
