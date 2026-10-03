#!/usr/bin/env python3
"""L5 frozen-history guards, OWNER-PATH executor (1265; SS rulings N-104 and N-107). DRAFT, NEVER RUN against any real system, NEVER APPLIED.

WHAT IT DOES (one transaction; schema code only, no row of any table is written or kept)
  (1) captures the live-only trigger function public.mimamsa_predictions_builder_guard() (md5 guard; no-op replace),
  (2) ASSERTS-AND-RECORDS the live-only builder grants ('ard' on mimamsa_predictions and mimamsa_manifestation_sets; raises if absent; never grants),
  (3) creates the frozen-history guards: mimamsa_predictions, brahma_prospective_ledger, mimamsa_manifestation_sets (UPDATE allow-lists,
      DELETE refused, TRUNCATE refused) and a DELETE/TRUNCATE guard on brahma_mimamsa_prediction_ledger, all ENABLE ALWAYS, with the ONE
      data-driven consent-withdrawal exception for DELETE (public.l5_frozen_withdrawal_authorizes),
  (4) self-tests every guard inside the transaction (rolled-back probe rows) and runs an asserting post-check that RAISES,
  and the exact inverse (--rollback). The SQL lives in ./sql/ and is run as ONE script; it is NEVER under platform/migrations (migrate.ts
  would pick it up and the routine runner, which cannot CREATE in schema public, would fail the migrate job and block deploys).

WHO RUNS WHAT (determined from W1_PRIVILEGE_AUDIT.md and the live ownership, 2026-10-03)
  The administrator (`postgres`, Cloud SQL: CREATEROLE, member of cloudsqlsuperuser, NOT a superuser, no table privilege, no USAGE on public) is
  made a TRANSIENT member of data_plane_schema_owner and amjis_app inside the transaction (GRANT ... TO CURRENT_USER, only if not already a
  member; PostgreSQL 15: a CREATEROLE role may grant any non-superuser role; on 16+ it would need ADMIN OPTION). Then:
    SET LOCAL ROLE data_plane_schema_owner;  GRANT CREATE ON SCHEMA public TO amjis_app          (the schema owner opens the capability)
    SET LOCAL ROLE amjis_app;                <the sql script>   (amjis_app owns the four tables and the captured function, so it can CREATE
                                              TRIGGER / ENABLE ALWAYS / CREATE OR REPLACE; the new functions end up owned by amjis_app too)
    SET LOCAL ROLE data_plane_schema_owner;  REVOKE CREATE ON SCHEMA public FROM amjis_app      (the capability is closed again)
    REVOKE data_plane_schema_owner / amjis_app FROM CURRENT_USER                                (the transient memberships are removed)
  and COMMIT only if the committed schema ACL, memberships, every other catalog object, ACL, policy, constraint, index and every row digest equal the
  pre-state apart from the planned objects. The rollback needs no CREATE capability (DROP of owned objects), so it opens no window.
  Neither the routine migrate role (amjis_app has USAGE without CREATE on public) nor any single role holds both "CREATE on public" and "owner of
  the tables": hence the two-role leg inside one transaction (the BUILDER_GRANT_PLAN v1.3 / jataka window pattern, not a deploy.yml change).

MODES (every mode needs --expect-plan: the administrator credential is fetched only for a plan hash the operator names)
  --count                          read-only: preconditions + pre-state, always ROLLBACK
  --dry-run [--writer-commit S]    everything, print the exact catalog diff, run every commit condition, ROLLBACK
  --apply --expect-plan H --expect-evidence D --writer-commit S
                                   same transaction; COMMIT only if every check holds and D equals this run's evidence digest
  --rollback-dry-run               the inverse, applied then rolled back
  --rollback --expect-plan H --expect-evidence D
                                   the inverse, committed

LAUNCH (GATE_V2). Never started directly: `exec/gate_v2/run_gated.sh <python3.11> l5_frozen_guard_exec.py <args>`. main() calls launch_gate() FIRST and
refuses (exit 93) without a verifying GATE_V2_LAUNCH marker. outcome.json (dry_run | applied | failed | commit_state_unknown) is written in every mode
with python_executable, python_version, psycopg_version and libpq_version, which are also bound into the evidence digest: --apply / --rollback refuse
(exit 92, before any connection) under a different interpreter or driver than the matching dry run. A MISSING outcome.json means check the database.
The source runs on Python 3.11 and 3.12+ (no f-string reuses its own quote type). Under test only, connect() is injected; connect_admin() is never reached.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile

import psycopg

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
SQL_DIR = HERE / "sql"
FORWARD_SQL = SQL_DIR / "1265_l5_frozen_row_guards.sql"
ROLLBACK_SQL = SQL_DIR / "1265_l5_frozen_row_guards.ROLLBACK.sql"
VERIFY_FILES = ("verify_before_apply.sql", "verify_after_apply.sql")

PROJECT = "madhav-astrology"
EXPECTED_DB = "amjis"
SCHEMA_OWNER = "data_plane_schema_owner"
APP_OWNER = "amjis_app"
BUILDER = "data_plane_builder"
LOCK_TIMEOUT = "5s"
STATEMENT_TIMEOUT = "300s"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/L5FrozenGuard1265"
WRITER_IMAGE_JOB = "brahma-build-pipeline-job"
WRITER_IMAGE_REGION = "asia-south1"
WRITER_FILES = ("platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py", "platform/src/lib/cockpit/assetClearSpec.ts")
WRITER_FORBIDDEN = re.compile(r"DELETE\s+FROM\s+(public\.)?mimamsa_(predictions|manifestation_sets)\b", re.I)

TABLES = ("mimamsa_predictions", "brahma_prospective_ledger", "mimamsa_manifestation_sets", "brahma_mimamsa_prediction_ledger")

# ------------------------------------------------------------------------------------------------ bound objects (md5 of pg_proc.prosrc)
BUILDER_SIG, BUILDER_MD5, BUILDER_LEN = "mimamsa_predictions_builder_guard()", "46c23854275c2712b30860a2b174adb2", 1084
NEW_FUNCTIONS = {                       # signature -> (dollar-quote tag in the sql script, md5 of the body)
    "l5_frozen_withdrawal_authorizes(uuid)": ("helper", "3ec94f3a5b54fdb701e56db53cb59ca3"),
    "l5_frozen_chart_cascade_authorizes(uuid)": ("cascade", "4617dbe262a6527a8173fb9e71badb0c"),
    "mimamsa_predictions_frozen_row_guard()": ("predictions", "c70f89cc3be0ce3891e59d4b10f1852d"),
    "brahma_prospective_ledger_frozen_row_guard()": ("prospective", "0e2abf47bc0b16acfdde5783e9689941"),
    "mimamsa_manifestation_sets_frozen_row_guard()": ("manifestation", "e362add1186640c49dc4700dfd94c670"),
    "brahma_mimamsa_prediction_ledger_delete_guard()": ("bmpl", "53bd3d5578281090adee5b253346dc17"),
}
NEW_TRIGGERS = (                        # (table, trigger, tgtype, tgenabled, function)
    ("mimamsa_predictions", "mimamsa_predictions_frozen_row_guard", 27, "A", "mimamsa_predictions_frozen_row_guard"),
    ("mimamsa_predictions", "mimamsa_predictions_frozen_row_guard_truncate", 34, "A", "mimamsa_predictions_frozen_row_guard"),
    ("brahma_prospective_ledger", "brahma_prospective_ledger_frozen_row_guard", 27, "A", "brahma_prospective_ledger_frozen_row_guard"),
    ("brahma_prospective_ledger", "brahma_prospective_ledger_frozen_row_guard_truncate", 34, "A", "brahma_prospective_ledger_frozen_row_guard"),
    ("mimamsa_manifestation_sets", "mimamsa_manifestation_sets_frozen_row_guard", 27, "A", "mimamsa_manifestation_sets_frozen_row_guard"),
    ("mimamsa_manifestation_sets", "mimamsa_manifestation_sets_frozen_row_guard_truncate", 34, "A", "mimamsa_manifestation_sets_frozen_row_guard"),
    ("brahma_mimamsa_prediction_ledger", "brahma_mimamsa_prediction_ledger_delete_guard", 11, "A", "brahma_mimamsa_prediction_ledger_delete_guard"),
    ("brahma_mimamsa_prediction_ledger", "brahma_mimamsa_prediction_ledger_delete_guard_truncate", 34, "A", "brahma_mimamsa_prediction_ledger_delete_guard"),
)
CAPTURED_TRIGGER = ("mimamsa_predictions", "mimamsa_predictions_builder_guard", 15, "O")
EXISTING = {                            # repo objects the script builds beside: asserted, never changed
    "bmpl_freeze_confirmed()": "70c2ddb261d703fa6a33a4feaf39c99c",
    "brahma_prospective_ledger_enforce_shape()": "acc7ec0121fa1fe0752ae938d9edfafe",
}
EXISTING_TRIGGERS = (("brahma_mimamsa_prediction_ledger", "trg_bmpl_freeze_confirmed", 19, "O"),
                     ("brahma_prospective_ledger", "trg_brahma_prospective_ledger_enforce_shape", 23, "O"))
BUILDER_GRANT_TABLES = ("mimamsa_predictions", "mimamsa_manifestation_sets")
BUILDER_GRANT_PRIVS = "DELETE,INSERT,SELECT"


class ExpectedDiffError(Exception):
    """The shipped sql does not carry the bound bodies: nothing may run."""


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_sql(path: pathlib.Path) -> str:
    return path.read_bytes().decode("utf-8")


def dollar_body(sql: str, tag: str) -> str:
    m = re.search(r"AS \$" + tag + r"\$(.*?)\$" + tag + r"\$;", sql, re.S)
    if not m:
        raise ExpectedDiffError("no $" + tag + "$ body in the sql script")
    return m.group(1)


def verify_sql_bodies(forward: str | None = None, rollback: str | None = None) -> None:
    """Before any database work: the shipped script carries exactly the bound bodies (md5), the captured builder guard (md5 + length),
    and its rollback names the same md5s. A hand edit of a body is refused here AND changes the plan hash."""
    fw = forward if forward is not None else read_sql(FORWARD_SQL)
    rb = rollback if rollback is not None else read_sql(ROLLBACK_SQL)
    b = dollar_body(fw, "guard")
    if hashlib.md5(b.encode()).hexdigest() != BUILDER_MD5 or len(b.encode()) != BUILDER_LEN:
        raise ExpectedDiffError("the captured builder guard in the sql script is not the bound body")
    for sig, (tag, md5) in NEW_FUNCTIONS.items():
        if hashlib.md5(dollar_body(fw, tag).encode()).hexdigest() != md5:
            raise ExpectedDiffError(sig + ": the body in the sql script is not the bound body")
        if fw.count(md5) < 2 or rb.count(md5) < 1:
            raise ExpectedDiffError(sig + ": the sql script does not pin its own md5 (replace guard, post-check) or the rollback does not name it")
    for sig, md5 in EXISTING.items():
        if fw.count(md5) < 1:
            raise ExpectedDiffError(sig + ": the sql script does not assert the repo md5")


# ---------------------------------------------------------------------------------------------------------------- EXPECTED_DIFF
def expected_diff() -> dict:
    return {
        "functions_added": sorted(NEW_FUNCTIONS),
        "functions_md5": {k: v[1] for k, v in sorted(NEW_FUNCTIONS.items())},
        "captured": {"function": BUILDER_SIG, "md5": BUILDER_MD5, "bytes": BUILDER_LEN,
                     "attributes": "plpgsql, SECURITY INVOKER, proconfig {search_path=pg_catalog, pg_temp}, VOLATILE, owner amjis_app, proacl {amjis_app=X/amjis_app}",
                     "trigger": list(CAPTURED_TRIGGER), "effect": "no change to the live object (replace of the identical body); refused if it differs"},
        "triggers_added": [list(t[:4]) for t in NEW_TRIGGERS],
        "grants_asserted_not_issued": {"role": BUILDER, "tables": list(BUILDER_GRANT_TABLES), "privileges": BUILDER_GRANT_PRIVS, "grantor": APP_OWNER},
        "existing_repo_objects_asserted": {"functions": EXISTING, "triggers": [list(t) for t in EXISTING_TRIGGERS]},
        "unchanged": ["every other function, trigger (incl. their enablement), constraint, index, policy and table ACL of public",
                      "schema public ACL (amjis_app has CREATE only inside the transaction)", "role memberships (transient only)",
                      "RLS flags (relrowsecurity / relforcerowsecurity) of the four tables", "row data of the four tables (count + md5 of every row)",
                      "asset_registry and every freshness/receipt table (no registry trigger fires)"],
        "exception": ["DELETE only through l5_frozen_withdrawal_authorizes: consent_state = 'withdrawn' and no open/reopened/escalated dispute; fail closed",
                      "DELETE only through l5_frozen_chart_cascade_authorizes (SS N-108), checked first: no charts row with that id, i.e. inside the RI cascade of deleting the chart itself the parent is already gone; SECURITY DEFINER because charts has row-level security on; pg_trigger_depth() is deliberately not used; a direct DELETE of a row whose chart exists is refused"],
        "not_guarded_by_ruling": ["mimamsa_calibration", "mimamsa_calibration_snapshot"],
        "rls": "NOT armed (assessed: unsound for the live role set; see the PR)",
        "rollback": "drops the 8 triggers and 6 functions; the captured builder guard and the existing repo triggers stay; no CREATE capability needed",
        "order": "after S-L1, after the append-only mi_bhavisya writer and the assetClearSpec change are deployed (--writer-commit), before any L5 rebuild",
    }


# ------------------------------------------------------------------------------------------------------------ gate wiring (GATE_V2)
GATE_PINS = {"prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
             "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
             "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
GATE_DIR_ENV = "L5FG_TEST_GATE_DIR"
TEST_EVIDENCE_ENV = "L5FG_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = 93
EXIT_TEST_ENV = 95
EXIT_INTERPRETER = 92
MODES = ("count", "dry-run", "apply", "rollback-dry-run", "rollback")


def gate_dir(environ=None) -> pathlib.Path:
    """exec/gate_v2 next to this folder. L5FG_TEST_GATE_DIR (tests only) is REFUSED, exit 95, outside a pytest run."""
    environ = os.environ if environ is None else environ
    if GATE_DIR_ENV in environ:
        if PYTEST_ENV not in environ:
            sys.stderr.write("REFUSED: " + GATE_DIR_ENV + " is set outside a pytest run; it would redirect the gate files.\n")
            raise SystemExit(EXIT_TEST_ENV)
        return pathlib.Path(environ[GATE_DIR_ENV])
    return HERE.parent / "gate_v2"


_STD: dict = {}


def standards(environ=None):
    d = gate_dir(environ)
    if str(d) not in _STD:
        _STD[str(d)] = _load("executor_standards_" + str(len(_STD)), d / "executor_standards.py")
    return _STD[str(d)]


def launch_gate(environ=None):
    """FIRST thing main() does. Refuses (exit 93) unless executor_standards.py equals its pin AND a verifying GATE_V2_LAUNCH marker is present."""
    environ = os.environ if environ is None else environ
    try:
        es = standards(environ)
    except FileNotFoundError:
        sys.stderr.write("REFUSED: the GATE_V2 files are not at " + str(gate_dir(environ)) + ": this executor cannot be launched.\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    if es.sha256_file(es.__file__) != GATE_PINS["executor_standards.py"]:
        sys.stderr.write("REFUSED: executor_standards.py differs from the version pinned in this executor (GATE_PINS)\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    return es.require_gate_launch(environ, gate_dir=str(gate_dir(environ)), expected_gate_sha=GATE_PINS["prerun_gate.py"],
                                  expected_launcher_sha=GATE_PINS["run_gated.sh"])


# ------------------------------------------------------------------------------------------------------------- plan text + hash
def sha_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def exec_sha(path=None) -> str:
    return sha_file(path or __file__)


def render_plan(sha: str | None = None, pins: dict | None = None) -> str:
    sha = sha or exec_sha()
    pins = pins or GATE_PINS
    L = [
        "-- L5 FROZEN-HISTORY GUARDS (1265; SS N-104 / N-107): owner-path plan. ONE transaction by the administrator `postgres` (CREATEROLE, not a superuser, no table privilege, no USAGE on public).",
        "-- NOT a migration: the sql lives in this package, never under platform/migrations or platform/supabase/migrations.",
        f"SET LOCAL search_path = public, pg_catalog; SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'; SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'",
        f"-- STEP (transient role membership, part of the plan): GRANT {SCHEMA_OWNER} TO CURRENT_USER and GRANT {APP_OWNER} TO CURRENT_USER, each only if the administrator is not already a member; REVOKEd before COMMIT; the memberships are compared with the pre-state.",
        "-- FORWARD (--dry-run / --apply). preconditions (read only; any failure = refuse + ROLLBACK): the database is amjis; no build_runs planned/running/paused on ANY chart; no data_plane_builder session active/idle-in-transaction; "
        f"schema public: owner {SCHEMA_OWNER}, {APP_OWNER} has USAGE and NO CREATE (an already open window is refused); the four tables are owned by {APP_OWNER}; the captured builder guard is live as captured "
        f"(md5 {BUILDER_MD5}, {BUILDER_LEN} bytes, secdef false, owner {APP_OWNER}, ACL {{amjis_app=X/amjis_app}}, trigger tgtype 15 enabled O); NONE of the {len(NEW_FUNCTIONS)} new functions or {len(NEW_TRIGGERS)} new triggers exists; "
        "the repo objects it builds beside are the repo's (" + "; ".join(f"{k} md5 {v}" for k, v in EXISTING.items()) + "; their triggers); "
        f"{BUILDER} holds exactly {BUILDER_GRANT_PRIVS} (grantor {APP_OWNER}) on " + " and ".join(BUILDER_GRANT_TABLES) + "; --writer-commit: full 40-hex sha, the pipeline job image tag equals it, and at that commit "
        + " and ".join(WRITER_FILES) + " contain no DELETE FROM mimamsa_predictions / mimamsa_manifestation_sets.",
        f"-- 1. SET LOCAL ROLE {SCHEMA_OWNER}; GRANT CREATE ON SCHEMA public TO {APP_OWNER}  (transient; closed in step 3)",
        f"-- 2. SET LOCAL ROLE {APP_OWNER}; execute sql/1265_l5_frozen_row_guards.sql (sha256 {sha_file(FORWARD_SQL)}):",
        "--    A capture of the builder guard (md5 guard), B assert-and-record of the builder grants (raises, never grants) and of the repo objects, C the 6 new functions "
        "(" + ", ".join(f"{s} md5 {m}" for s, (_, m) in sorted(NEW_FUNCTIONS.items())) + ") and the 8 triggers (ENABLE ALWAYS), D per-table self-test with rolled-back probe rows, E asserting post-check.",
        f"-- 3. SET LOCAL ROLE {SCHEMA_OWNER}; REVOKE CREATE ON SCHEMA public FROM {APP_OWNER}; then REVOKE the transient memberships.",
        "-- commit only if ALL hold (EXPECTED_DIFF): before/after snapshots of every public function, trigger, constraint, index and policy, the four tables' ACL, owner and RLS flags, the schema ACL, the memberships "
        "and the row digest (count + md5 of every row) of the four tables differ in EXACTLY the planned objects (6 functions, 8 triggers added; the captured builder guard unchanged); the schema ACL and "
        f"memberships equal the pre-state; {APP_OWNER} has no CREATE on public; every function md5 equals its bound md5 and none is SECURITY DEFINER; --expect-plan == plan hash; --expect-evidence == this run's evidence digest (apply).",
        "-- ROLLBACK (--rollback-dry-run / --rollback): the inverse as amjis_app (no CREATE capability needed): precondition = every installed body and trigger is exactly as installed; drops the 8 triggers and the 6 functions "
        f"(sql/1265_l5_frozen_row_guards.ROLLBACK.sql, sha256 {sha_file(ROLLBACK_SQL)}); the captured builder guard and the existing triggers stay; asserting post-check; the snapshot equals the pre-forward state.",
        "-- the real run is started ONLY through exec/gate_v2/run_gated.sh <python3.11> <this file> <args> (GATE_V2): the executor REFUSES (exit 93) unless the marker verifies against the gate files pinned below; "
        "exit 92 when --apply / --rollback run under a different interpreter or driver than the matching dry run; it writes outcome.json (dry_run | applied | failed | commit_state_unknown) in every mode.",
        "-- every mode needs --expect-plan: the in-process administrator credential is fetched only after the plan hash matched.",
        "-- gate files (exec/gate_v2; GATE_V2 revision 3, bound by SS N-86): prerun_gate.py sha256 %s; run_gated.sh sha256 %s; executor_standards.py sha256 %s"
        % (pins["prerun_gate.py"], pins["run_gated.sh"], pins["executor_standards.py"]),
        "-- plan hash = bind_gate_into_plan_hash(sha256(plan text + \"\\n\" + json(EXPECTED_DIFF)), prerun_gate.py pin, run_gated.sh pin)",
        "-- verification SQL (read only, run by the operator as the reader; named in the hashed plan text): " + "; ".join(f"{n} sha256 {sha_file(SQL_DIR / n)}" for n in VERIFY_FILES),
        "-- executor: l5_frozen_guard_exec.py sha256 %s" % sha,
    ]
    return "\n".join(L)


def plan_hash_unbound(sha: str | None = None, pins: dict | None = None) -> str:
    text = render_plan(sha, pins)
    return hashlib.sha256((text + "\n" + json.dumps(expected_diff(), sort_keys=True)).encode()).hexdigest()


def plan_hash(sha: str | None = None, pins: dict | None = None, environ=None) -> str:
    pins = pins or GATE_PINS
    return standards(environ).bind_gate_into_plan_hash(plan_hash_unbound(sha, pins),
                                                        {"gate_sha256": pins["prerun_gate.py"], "run_gated_sha256": pins["run_gated.sh"]})


# ------------------------------------------------------------------------------------------------------------------ db plumbing
def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname=EXPECTED_DB, user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class CountingCursor:
    def __init__(self, cur) -> None:
        self._cur = cur
        self.n = 0

    def execute(self, *a, **k):
        self.n += 1
        return self._cur.execute(*a, **k)

    def __getattr__(self, name):
        return getattr(self._cur, name)


def _run_cmd(argv: list) -> str:
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(argv[0] + " failed: " + r.stderr.strip()[:200])
    return r.stdout.strip()


_TABLES_SQL = "(" + ", ".join("'" + t + "'" for t in TABLES) + ")"
SNAP_SQL = {
    "function": "SELECT p.oid::regprocedure::text, md5(p.prosrc), pg_get_userbyid(p.proowner), p.prosecdef::text, COALESCE(p.proconfig::text,''), "
                "COALESCE(p.proacl::text,'') FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.prokind = 'f' ORDER BY 1",
    "trigger": "SELECT c.relname, t.tgname, t.tgenabled::text, t.tgtype::text, t.tgfoid::regproc::text, md5(pg_get_triggerdef(t.oid, true)) "
               "FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid WHERE NOT t.tgisinternal AND c.relnamespace = 'public'::regnamespace ORDER BY 1, 2",
    "table": "SELECT c.relname, pg_get_userbyid(c.relowner), COALESCE(c.relacl::text,''), c.relrowsecurity::text, c.relforcerowsecurity::text "
             "FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relname IN " + _TABLES_SQL + " ORDER BY 1",
    "policy": "SELECT polrelid::regclass::text, polname, polcmd::text, polroles::regrole[]::text, COALESCE(pg_get_expr(polqual, polrelid),''), "
              "COALESCE(pg_get_expr(polwithcheck, polrelid),'') FROM pg_policy WHERE polrelid::regclass::text IN " + _TABLES_SQL + " ORDER BY 1, 2",
    "constraint": "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid::regclass::text IN " + _TABLES_SQL + " ORDER BY 1, 2",
    "index": "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename IN " + _TABLES_SQL + " ORDER BY 1, 2",
    "schema_acl": "SELECT COALESCE(nspacl::text,'') || '|' || pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'public'",
    "event_triggers": "SELECT count(*)::text FROM pg_event_trigger",
}
MEMBERSHIP_SQL = ("SELECT r.rolname, m.rolname, am.admin_option::text FROM pg_auth_members am JOIN pg_roles r ON r.oid = am.roleid "
                  "JOIN pg_roles m ON m.oid = am.member ORDER BY 1, 2")


def snap(cur) -> dict:
    out = {}
    for k, sql in SNAP_SQL.items():
        cur.execute(sql)
        out[k] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    out["rowdata"] = set()
    cur.execute("SET LOCAL ROLE " + APP_OWNER)            # the administrator holds no table privilege; amjis_app owns the four tables
    for t in TABLES:
        cur.execute("SELECT '" + t + "', count(*), md5(COALESCE(string_agg(x::text, '|' ORDER BY x::text), '')) FROM public." + t + " x")
        out["rowdata"] |= {tuple(str(v) for v in row) for row in cur.fetchall()}
    cur.execute("RESET ROLE")
    return out


def members(cur) -> set:
    cur.execute(MEMBERSHIP_SQL)
    return {tuple(str(x) for x in row) for row in cur.fetchall()}


def is_member(cur, role: str) -> bool:
    cur.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (role,))
    return bool(cur.fetchone()[0])


class Checks:
    def __init__(self) -> None:
        self.items: list = []

    def chk(self, name: str, ok: bool, detail=None) -> bool:
        self.items.append((name, bool(ok), None if detail is None else str(detail)[:300]))
        return bool(ok)

    @property
    def failed(self) -> list:
        return [n for n, ok, _ in self.items if not ok]


@dataclasses.dataclass(frozen=True)
class Leg:
    name: str                  # forward | rollback
    sql_path: pathlib.Path
    needs_window: bool         # forward only: the schema CREATE capability for amjis_app
    transient_roles: tuple


def forward_leg() -> Leg:
    return Leg("forward", FORWARD_SQL, True, (SCHEMA_OWNER, APP_OWNER))


def rollback_leg() -> Leg:
    return Leg("rollback", ROLLBACK_SQL, False, (APP_OWNER,))


# ------------------------------------------------------------------------------------------------------ writer-first (ORDER)
def writer_check(commit, run_cmd=_run_cmd) -> tuple:
    """HARD RULE (SS N-107 e): the append-only mi_bhavisya writer and the assetClearSpec change are deployed BEFORE this plan. Read only: the Cloud Run
    job's image tag, and the two source files at that commit contain no DELETE of mimamsa_predictions / mimamsa_manifestation_sets."""
    if not commit:
        return ["--writer-commit <sha> is required: the append-only writer must be deployed BEFORE this plan applies"], "NOT CHECKED"
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        return ["--writer-commit must be the full 40-hex commit sha (got " + repr(commit) + "); a prefix match is not accepted"], "REFUSED"
    problems = []
    try:
        image = run_cmd(["gcloud", "run", "jobs", "describe", WRITER_IMAGE_JOB, "--project", PROJECT, "--region", WRITER_IMAGE_REGION,
                         "--format=value(spec.template.spec.template.spec.containers[0].image)"])
        tag = image.rsplit(":", 1)[-1] if ":" in image else ""
        if tag != commit:
            problems.append("job " + WRITER_IMAGE_JOB + " runs image tag " + repr(tag) + ", not commit " + commit)
        for path in WRITER_FILES:
            text = run_cmd(["git", "-C", str(REPO_ROOT), "show", commit + ":" + path])
            code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith(("#", "//", "*", "/*")))
            if WRITER_FORBIDDEN.search(code):
                problems.append(path + " at " + commit[:12] + " still deletes mimamsa_predictions / mimamsa_manifestation_sets rows")
    except Exception as exc:        # fail closed: an unverifiable writer is not a deployed writer
        return ["writer check failed: " + type(exc).__name__ + ": " + str(exc)[:160]], "UNVERIFIED"
    return problems, "image tag " + repr(tag[:12]) + "; the writer files at " + commit[:12] + " " + ("still delete" if problems else "do not delete") + " frozen rows"


# ------------------------------------------------------------------------------------------------------------------- preconditions
def trigger_row(cur, table, name):
    cur.execute("SELECT t.tgtype, t.tgenabled::text, t.tgfoid::regproc::text FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
                "WHERE c.relnamespace = 'public'::regnamespace AND c.relname = %s AND t.tgname = %s AND NOT t.tgisinternal", (table, name))
    return cur.fetchone()


def fn_row(cur, sig):
    """Read as the app owner: the administrator has no USAGE on schema public, and resolving public.<name> needs it."""
    cur.execute("SET LOCAL ROLE " + APP_OWNER)
    cur.execute("SELECT md5(p.prosrc), length(convert_to(p.prosrc,'UTF8')), pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), "
                "COALESCE(p.proacl::text,''), p.provolatile::text FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", ("public." + sig,))
    row = cur.fetchone()
    cur.execute("RESET ROLE")
    return row


def preconditions(cur, leg: Leg, ck: Checks, out, expected_db: str) -> None:
    cur.execute("SELECT current_database()")
    ck.chk("pre_database_is_the_expected_one", cur.fetchone()[0] == expected_db, "connected to a database other than " + expected_db)
    cur.execute("SET LOCAL ROLE " + APP_OWNER)
    cur.execute("SELECT count(*), COALESCE(string_agg(DISTINCT left(chart_id::text,8) || ':' || state, ', '), '') FROM public.build_runs "
                "WHERE state IN ('planned','running','paused')")
    n, which = cur.fetchone()
    cur.execute("RESET ROLE")
    ck.chk("pre_no_build_in_flight", n == 0, str(n) + " build_run(s) in planned/running/paused on ANY chart (" + which + "); not touched" if n else None)
    cur.execute("SELECT count(*) FILTER (WHERE state IN ('active','idle in transaction','idle in transaction (aborted)')), count(*) FILTER (WHERE state IS NULL) "
                "FROM pg_stat_activity WHERE usename = %s AND pid <> pg_backend_pid()", (BUILDER,))
    busy, hidden = cur.fetchone()
    if hidden:
        out("WARNING: " + str(hidden) + " " + BUILDER + " session(s) have a hidden state (no pg_read_all_stats); only build_runs guards them")
    ck.chk("pre_no_builder_session", busy == 0, "a " + BUILDER + " session is active or idle-in-transaction" if busy else None)
    cur.execute("SELECT pg_get_userbyid(nspowner), has_schema_privilege(%s, 'public', 'USAGE'), has_schema_privilege(%s, 'public', 'CREATE') "
                "FROM pg_namespace WHERE nspname = 'public'", (APP_OWNER, APP_OWNER))
    owner, usage, create = cur.fetchone()
    ck.chk("pre_schema_public_owner_is_the_schema_owner", owner == SCHEMA_OWNER, owner)
    ck.chk("pre_app_owner_has_usage_and_no_create_on_public", bool(usage) and not create,
           "usage=" + str(usage) + " create=" + str(create) + " (an already open window is refused)")
    cur.execute("SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relname IN " + _TABLES_SQL)
    owners = dict(cur.fetchall())
    ck.chk("pre_the_four_tables_are_owned_by_the_app_owner", set(owners) == set(TABLES) and all(v == APP_OWNER for v in owners.values()), owners)
    row = fn_row(cur, BUILDER_SIG)
    if leg.name == "forward":
        ok = bool(row) and row[0] == BUILDER_MD5 and row[1] == BUILDER_LEN and row[2] == APP_OWNER and row[3] is False \
            and row[4] == '{"search_path=pg_catalog, pg_temp"}' and row[5] == "{amjis_app=X/amjis_app}" and row[6] == "v"
        ck.chk("pre_captured_builder_guard_is_live_as_captured", ok, row)
        tr = trigger_row(cur, CAPTURED_TRIGGER[0], CAPTURED_TRIGGER[1])
        ck.chk("pre_captured_builder_trigger_is_live_as_captured", bool(tr) and tr[0] == CAPTURED_TRIGGER[2] and tr[1] == CAPTURED_TRIGGER[3], tr)
        present = [s for s in NEW_FUNCTIONS if fn_row(cur, s)] + [t[1] for t in NEW_TRIGGERS if trigger_row(cur, t[0], t[1])]
        ck.chk("pre_none_of_the_new_objects_exists", not present, "already present: " + ", ".join(present) + " (apply is single-shot; use --rollback first)" if present else None)
        for sig, md5 in EXISTING.items():
            r = fn_row(cur, sig)
            ck.chk("pre_repo_function_" + sig.split("(")[0], bool(r) and r[0] == md5, r[0] if r else "absent")
        for tbl, name, ttype, en in EXISTING_TRIGGERS:
            tr = trigger_row(cur, tbl, name)
            ck.chk("pre_repo_trigger_" + name, bool(tr) and tr[0] == ttype and tr[1] == en, tr)
        for tbl in BUILDER_GRANT_TABLES:
            cur.execute("SELECT string_agg(a.privilege_type, ',' ORDER BY a.privilege_type), min(pg_get_userbyid(a.grantor)), count(DISTINCT a.grantor) "
                        "FROM pg_class c, aclexplode(c.relacl) a WHERE c.relnamespace = 'public'::regnamespace AND c.relname = %s "
                        "AND a.grantee = %s::regrole", (tbl, BUILDER))
            privs, grantor, ng = cur.fetchone()
            ck.chk("pre_recorded_builder_grant_" + tbl, privs == BUILDER_GRANT_PRIVS and grantor == APP_OWNER and ng == 1,
                   "found " + str(privs) + " grantor " + str(grantor))
    else:
        for sig, (tag, md5) in NEW_FUNCTIONS.items():
            r = fn_row(cur, sig)
            ck.chk("pre_installed_function_" + sig.split("(")[0], bool(r) and r[0] == md5 and r[2] == APP_OWNER and r[3] is sig.startswith("l5_frozen_chart_cascade"),
                   r[0] if r else "absent")
        for tbl, name, ttype, en, fn in NEW_TRIGGERS:
            tr = trigger_row(cur, tbl, name)
            ck.chk("pre_installed_trigger_" + name, bool(tr) and tr[0] == ttype and tr[1] == en, tr)
        ck.chk("pre_captured_builder_guard_is_intact", bool(row) and row[0] == BUILDER_MD5)


# --------------------------------------------------------------------------------------------------------------------- accounting
def accounting(leg: Leg, before: dict, after: dict) -> list:
    """Pure (no database): [(check name, ok, detail)]. Forward: exactly the planned functions and triggers are ADDED and nothing else changes anywhere.
    Rollback: exactly them are REMOVED."""
    out = []
    names = {s.split("(")[0] for s in NEW_FUNCTIONS}
    sign = (1, 0) if leg.name == "forward" else (0, 1)
    f_add, f_rem = after["function"] - before["function"], before["function"] - after["function"]
    t_add, t_rem = after["trigger"] - before["trigger"], before["trigger"] - after["trigger"]
    want_f, other_f = (f_add, f_rem) if sign == (1, 0) else (f_rem, f_add)
    want_t, other_t = (t_add, t_rem) if sign == (1, 0) else (t_rem, t_add)
    got_f = {r[0].split("(")[0] for r in want_f}
    out.append(("post_functions_changed_are_exactly_the_planned_ones", got_f == names and len(want_f) == len(NEW_FUNCTIONS) and not other_f,
                "changed: " + ", ".join(sorted(got_f)) + "; the opposite direction: " + str(len(other_f))))
    md5s = {r[0].split("(")[0]: r[1] for r in want_f}
    ck_md5 = all(md5s.get(s.split("(")[0]) == m for s, (_, m) in NEW_FUNCTIONS.items())
    out.append(("post_function_md5s_equal_the_bound_ones", ck_md5, md5s))
    out.append(("post_new_functions_owner_definer_flags_and_acl_as_planned",
                all(r[2] == APP_OWNER for r in want_f)
                and all(r[3] == ("true" if r[0].startswith("l5_frozen_chart_cascade_authorizes") else "false") for r in want_f)
                and all(r[5] == "{amjis_app=X/amjis_app}" for r in want_f if not r[0].startswith("l5_frozen_")),
                sorted((r[0], r[2], r[3], r[5]) for r in want_f)))
    got_t = {(r[0], r[1], r[2], r[3]) for r in want_t}
    planned_t = {(t[0], t[1], t[3], str(t[2])) for t in NEW_TRIGGERS}
    out.append(("post_triggers_changed_are_exactly_the_planned_ones", got_t == planned_t and not other_t,
                "changed " + str(len(got_t)) + " of " + str(len(planned_t)) + "; the opposite direction: " + str(len(other_t))))
    for key in ("table", "policy", "constraint", "index", "schema_acl", "event_triggers", "rowdata"):
        out.append(("post_" + key + "_identical", before[key] == after[key], None if before[key] == after[key] else
                    "-" + str(len(before[key] - after[key])) + " +" + str(len(after[key] - before[key]))))
    return out


def render_report(leg: Leg, before: dict, after: dict, ck: Checks, extra: dict) -> list:
    out = ["== L5 FROZEN-HISTORY GUARDS, " + leg.name.upper() + " =="]
    for key, title in (("function", "FUNCTION (signature, md5(prosrc), owner, secdef, config, acl)"),
                       ("trigger", "TRIGGER (table, name, enabled, tgtype, function, md5(def))")):
        removed, added = sorted(before[key] - after[key]), sorted(after[key] - before[key])
        out.append("== " + title + ": " + str(len(removed)) + " removed / " + str(len(added)) + " added ==")
        out.extend("  - " + " | ".join(r)[:300] for r in removed)
        out.extend("  + " + " | ".join(r)[:300] for r in added)
    for key in ("table", "policy", "constraint", "index", "schema_acl", "event_triggers", "rowdata"):
        out.append("== " + key.upper() + ": " + ("IDENTICAL" if before[key] == after[key] else "CHANGED (UNEXPECTED)") + " (" + str(len(before[key])) + " entries) ==")
    out.append("== MEMBERSHIP after the transient revoke: " + ("equals the pre-state" if extra.get("membership_equal") else "DIFFERS (UNEXPECTED)") + " ==")
    out.append("== SCHEMA public CREATE for amjis_app after the plan: " + str(extra.get("app_create_after")) + " (must be False) ==")
    out.append("commit conditions: " + ("ALL HOLD" if not ck.failed else "FAILED " + str(ck.failed)))
    out.append("statements issued: " + str(extra.get("statements")))
    return out


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=lambda s: sorted(s) if isinstance(s, (set, frozenset)) else str(s))


def runtime_record() -> dict:
    return {"python_executable": sys.executable, "python_version": sys.version, "psycopg_version": psycopg.__version__,
            "libpq_version": psycopg.pq.version()}


RUNTIME_KEYS = ("python_executable", "python_version", "psycopg_version", "libpq_version")


def run_leg(conn, leg: Leg, mode: str, out, writer_commit=None, writer_runner=None, expect_evidence=None, expected_db: str = EXPECTED_DB) -> dict:
    """One transaction. Returns {commit_ok, checks, evidence_digest, report}; the caller commits or rolls back."""
    writer_runner = writer_runner or _run_cmd
    ck = Checks()
    cur = CountingCursor(conn.cursor())
    out("start (UTC): " + utcnow())
    cur.execute("SET LOCAL search_path = public, pg_catalog")
    cur.execute("SET LOCAL lock_timeout = '" + LOCK_TIMEOUT + "'")
    cur.execute("SET LOCAL statement_timeout = '" + STATEMENT_TIMEOUT + "'")
    membership_before = members(cur)                       # BEFORE any transient grant
    transient = [r for r in leg.transient_roles if not is_member(cur, r)]
    try:
        for r in transient:
            cur.execute("GRANT " + r + " TO CURRENT_USER")
    except psycopg.Error as exc:
        ck.chk("pre_admin_can_assume_the_owner_roles", False, "GRANT failed: " + type(exc).__name__)
        out("REFUSED: the administrator cannot assume the owner roles (" + type(exc).__name__ + "); nothing was changed")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    preconditions(cur, leg, ck, out, expected_db)
    writer_line = "n/a (rollback)"
    if leg.name == "forward":
        problems, writer_line = writer_check(writer_commit, writer_runner)
        out("writer-first check: " + writer_line)
        if mode == "apply" or writer_commit:
            ck.chk("pre_writer_first", not problems, "; ".join(problems))
    out("preconditions: " + ("OK" if not ck.failed else "REFUSED"))
    for name, ok, detail in ck.items:
        if not ok:
            out("  - " + name + ": " + str(detail))
    if mode == "count" or ck.failed:
        out("end (UTC): " + utcnow())
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    before = snap(cur)
    sql = read_sql(leg.sql_path)
    if leg.needs_window:
        cur.execute("SET LOCAL ROLE " + SCHEMA_OWNER)
        cur.execute("GRANT CREATE ON SCHEMA public TO " + APP_OWNER)
        cur.execute("RESET ROLE")
    cur.execute("SET LOCAL ROLE " + APP_OWNER)
    cur.execute(sql)                                       # the script RAISES on any failed assertion: the exception aborts the whole transaction
    cur.execute("RESET ROLE")
    if leg.needs_window:
        cur.execute("SET LOCAL ROLE " + SCHEMA_OWNER)
        cur.execute("REVOKE CREATE ON SCHEMA public FROM " + APP_OWNER)
        cur.execute("RESET ROLE")
    after = snap(cur)                                      # read as amjis_app: while the transient membership still exists
    builder_after = fn_row(cur, BUILDER_SIG) if leg.name == "forward" else None
    cur.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE')", (APP_OWNER,))
    app_create_after = cur.fetchone()[0]
    for r in transient:
        cur.execute("REVOKE " + r + " FROM CURRENT_USER")
    membership_after = members(cur)
    ck.chk("post_membership_equals_pre_state_after_revoke", membership_after == membership_before,
           None if membership_after == membership_before else "pre " + str(sorted(membership_before)) + " post " + str(sorted(membership_after)))
    ck.chk("post_app_owner_has_no_create_on_public_again", app_create_after is False)
    for name, ok, detail in accounting(leg, before, after):
        ck.chk(name, ok, detail)
    if leg.name == "forward":
        ck.chk("post_captured_builder_guard_unchanged", bool(builder_after) and builder_after[0] == BUILDER_MD5 and builder_after[2] == APP_OWNER
               and builder_after[5] == "{amjis_app=X/amjis_app}")
    digest = hashlib.sha256(canonical({
        "plan": "see plan_hash", "leg": leg.name, "executor": exec_sha(), "sql": sha_file(leg.sql_path), "writer_commit": writer_commit,
        "writer_line": writer_line, "runtime": runtime_record(), "before": before, "checks": [(n, ok) for n, ok, _ in ck.items]}).encode()).hexdigest()
    if mode in ("apply", "rollback"):
        ck.chk("evidence_digest_matches_expected", expect_evidence == digest, "expected " + str(expect_evidence) + " got " + digest)
    extra = {"membership_equal": membership_after == membership_before, "app_create_after": app_create_after, "statements": cur.n}
    report = render_report(leg, before, after, ck, extra)
    for line in report:
        out(line)
    out("end (UTC): " + utcnow())
    return {"commit_ok": not ck.failed, "checks": ck, "evidence_digest": digest, "report": report, "digest_parts": {"before": before}}


# -------------------------------------------------------------------------------------------------------------------- evidence
def resolve_evidence_root(flag=None, environ=None) -> str:
    environ = os.environ if environ is None else environ
    if TEST_EVIDENCE_ENV not in environ:
        return EVIDENCE_ROOT
    if PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: " + TEST_EVIDENCE_ENV + " is set outside a pytest run; it would redirect the evidence directory.\n")
        raise SystemExit(EXIT_TEST_ENV)
    root = flag or environ[TEST_EVIDENCE_ENV]
    if not root:
        sys.stderr.write("REFUSED: " + TEST_EVIDENCE_ENV + " is set but empty: refusing to fall back to the real evidence root.\n")
        raise SystemExit(EXIT_TEST_ENV)
    return root


class EvidenceError(Exception):
    pass


def mkdir_0700(path) -> None:
    path = pathlib.Path(path)
    missing = [p for p in [path] + list(path.parents) if not p.exists()]
    for p in reversed(missing):
        p.mkdir(mode=0o700)
        os.chmod(p, 0o700)
    if not missing:
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def make_run_dir(root, mode: str, ts: str) -> pathlib.Path:
    try:
        rootp = pathlib.Path(root)
        mkdir_0700(rootp)
        d = rootp / (mode + "_" + ts)
        d.mkdir(mode=0o700)                      # NOT exist_ok: a collision aborts, never overwrites another run's evidence
        os.chmod(d, 0o700)
    except OSError as exc:
        raise EvidenceError("cannot create the evidence directory under " + str(root) + " (" + type(exc).__name__ + ")")
    return d


def write_private(path: pathlib.Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


def write_evidence(run_dir: pathlib.Path, res: dict, result: dict) -> None:
    try:
        parts = res.get("digest_parts") or {}
        if parts:
            write_private(run_dir / "before_state.json", canonical(parts["before"]) + "\n")
        write_private(run_dir / "report.txt", "\n".join(res.get("report") or []) + "\n")
        write_private(run_dir / "result.json", json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    except OSError:
        result.setdefault("warnings", []).append("evidence files could not be fully written")


# ------------------------------------------------------------------------------------------------------- outcome / execute
_SAFE_CLASS: dict = {}


def add_interpreter_to_outcome(path):
    with open(path) as f:
        body = json.load(f)
    body.update(runtime_record())
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".outcome.", dir=d)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(body, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def safe_outcome_class(es):
    """executor_standards.outcome_guard whose own file write can never mask the real result, with a committed flag: after COMMIT an
    interruption records `applied` with a warning, never `failed`; a commit() that itself raised records commit_state_unknown."""
    if id(es) in _SAFE_CLASS:
        return _SAFE_CLASS[id(es)]

    class SafeOutcome(es.outcome_guard):
        write_error = None
        interpreter_record_error = None
        committed = False
        commit_unknown = None
        commit_digest = None

        def mark_committed(self, digest):
            self.committed, self.commit_digest = True, digest

        def mark_commit_unknown(self, digest, exc_name):
            self.commit_unknown, self.commit_digest = exc_name, digest

        def _write(self, status, digest=None, checks=(), warnings=()):
            try:
                super()._write(status, digest, checks, warnings)
            except OSError as exc:
                self.write_error = type(exc).__name__
                self.done = True
                return
            try:
                add_interpreter_to_outcome(self.path)
            except Exception as exc:
                self.interpreter_record_error = type(exc).__name__

        @staticmethod
        def _warn(text):
            try:
                sys.stderr.write(text)
                sys.stderr.flush()
            except BaseException:
                pass

        def __exit__(self, exc_type, exc, tb):
            if self.commit_unknown and not self.done:
                self._write("commit_state_unknown", self.commit_digest, (), ["commit_raised:" + self.commit_unknown])
                self._warn("WARNING: COMMIT STATE UNKNOWN (" + self.commit_unknown + " raised by commit()): the change may or may not be committed. "
                           "outcome.json records commit_state_unknown. CHECK THE DATABASE before doing anything else.\n")
                return False
            if self.committed and not self.done:
                why = re.sub(r"[^A-Za-z0-9_.:\-]", "_", exc_type.__name__ if exc_type is not None else "outcome_not_declared")[:40]
                self._write("applied", self.commit_digest, (), ["outcome_write_failed_after_commit:" + why])
                self._warn("WARNING: THE COMMIT HAPPENED but the run was interrupted (" + why + ") before outcome.json was recorded; recorded applied with a warning.\n")
                return False
            return super().__exit__(exc_type, exc, tb)

    _SAFE_CLASS[id(es)] = SafeOutcome
    return SafeOutcome


def conclude(o, result, kind, digest=None, checks=()):
    if kind == "dry_run":
        o.dry_run(digest)
    elif kind == "applied":
        o.applied(digest)
    else:
        o.fail(list(checks) or ["refused_unspecified"], digest)
    if o.write_error:
        result.setdefault("warnings", []).append("outcome.json could not be written (" + o.write_error + ")" + ("; THE COMMIT HAPPENED" if kind == "applied" else ""))
    else:
        result["outcome_file"] = o.path
        if o.interpreter_record_error:
            result.setdefault("warnings", []).append("outcome.json written without the interpreter record (" + o.interpreter_record_error + ")")
    return result


def refuse(o, check: str, message: str):
    o.fail([check])
    raise SystemExit("REFUSED: " + message)


def refuse_interpreter(o, check: str, message: str):
    o.fail([check])
    o._warn("REFUSED (interpreter): " + message + "\n")
    raise SystemExit(EXIT_INTERPRETER)


def interpreter_precheck(o, evidence_root, expect_evidence: str, log: list) -> None:
    """--apply / --rollback, BEFORE the credential is fetched: compare the recorded runtime of the matching dry run(s) with this process.
    A record missing a field = cannot compare = REFUSED; any difference = REFUSED (exit 92). No dry-run evidence under this root: no early
    verdict; the evidence digest itself binds the runtime, so a different interpreter still fails evidence_digest_matches_expected."""
    now, matches = runtime_record(), []
    try:
        entries = sorted(pathlib.Path(evidence_root).iterdir())
    except OSError:
        entries = []
    for d in entries:
        try:
            body = json.loads((d / "outcome.json").read_text())
        except (OSError, ValueError):
            continue
        if isinstance(body, dict) and body.get("status") == "dry_run" and body.get("evidence_digest") == expect_evidence:
            matches.append((d.name, body))
    if not matches:
        log.append("interpreter check: no dry-run evidence for this digest under " + str(evidence_root) + "; the evidence digest itself binds the interpreter")
        return
    for name, body in matches:
        missing = [k for k in RUNTIME_KEYS if body.get(k) in (None, "")]
        if missing:
            refuse_interpreter(o, "dry_run_evidence_lacks_interpreter_record", "cannot compare: the dry run " + name + " recorded no " + ", ".join(missing)
                               + "; repeat the dry run with this executor and use its evidence digest")
        differs = [k for k in RUNTIME_KEYS if body[k] != now[k]]
        if differs:
            refuse_interpreter(o, "interpreter_differs_from_dry_run", "the dry run " + name + " used a different interpreter or driver ("
                               + "; ".join(k + ": dry run " + repr(body[k]) + ", now " + repr(now[k]) for k in differs)
                               + "): run the apply with the SAME interpreter, or repeat the dry run under this one")
    log.append("interpreter check: " + str(len(matches)) + " dry run(s) with this digest used the same interpreter, psycopg and libpq")


_HELD_SIGNALS = {signal.SIGTERM, signal.SIGHUP, signal.SIGINT}


def _on_terminate(signum, frame):
    raise SystemExit(128 + signum)


def install_signal_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _on_terminate)


def execute(args, connect, now=None, gate_fp=None, writer_runner=None, expected_db: str = EXPECTED_DB):
    """Returns (exit_code, result). `connect` is the only door to a database and is called ONLY after the plan hash matched."""
    now = now or dt.datetime.now(dt.timezone.utc)
    es = standards()
    evidence_root = resolve_evidence_root(getattr(args, "evidence_root", None))
    sha = exec_sha()
    phash = plan_hash(sha)
    gate_fp = gate_fp or dict(es.fingerprint(str(gate_dir())), under_test=False)
    try:
        run_dir = make_run_dir(evidence_root, args.mode, now.strftime("%Y%m%dT%H%M%S%fZ"))
    except EvidenceError as exc:
        return 1, {"status": "ABORTED_ROLLED_BACK", "reason": str(exc), "plan_hash": phash, "executor_sha256": sha}
    with safe_outcome_class(es)(run_dir, __file__, phash, gate_fp) as o:
        if args.expect_plan != phash:
            refuse(o, "args_expect_plan_mismatch", "--expect-plan does not equal the plan hash")
        if args.mode in ("apply", "rollback") and not args.expect_evidence:
            refuse(o, "args_expect_evidence_missing", "--" + args.mode + " requires --expect-evidence <digest from the matching dry run>")
        if args.mode == "apply" and not args.writer_commit:
            refuse(o, "args_writer_commit_missing", "--apply requires --writer-commit (the append-only writer deploys BEFORE this plan)")
        try:
            verify_sql_bodies()
        except ExpectedDiffError as exc:
            refuse(o, "expected_diff_mismatch", "the sql script is not the bound EXPECTED_DIFF (" + str(exc)[:160] + ")")
        leg = rollback_leg() if args.mode.startswith("rollback") else forward_leg()
        lines: list = []
        if args.mode in ("apply", "rollback"):
            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)
        conn = connect()                         # the administrator credential is fetched here, never earlier
        try:
            try:
                res = run_leg(conn, leg, args.mode if args.mode != "rollback-dry-run" else "dry-run", lines.append, args.writer_commit,
                              writer_runner, args.expect_evidence, expected_db)
            except Exception as exc:
                conn.rollback()
                if isinstance(exc, psycopg.Error):             # the script RAISED (an asserting check) or a statement failed: nothing is committed
                    res = {"commit_ok": False, "checks": Checks(), "evidence_digest": None, "report": [], "digest_parts": {}}
                    res["checks"].chk("sql_raised_" + type(exc).__name__, False, str(exc).strip().splitlines()[0][:280] if str(exc).strip() else "")
                    lines.append("REFUSED: the sql script raised " + type(exc).__name__ + ": " + (str(exc).strip().splitlines() or [""])[0][:280])
                else:
                    raise
            ck, digest = res["checks"], res["evidence_digest"]
            result = {"plan_hash": phash, "executor_sha256": sha, "mode": args.mode, "evidence_digest": digest,
                      "failed_checks": ck.failed, "checks": {n: ok for n, ok, _ in ck.items}, "runtime": runtime_record(),
                      "details": {n: d for n, ok, d in ck.items if d and not ok}, "log": lines, "evidence_dir": str(run_dir)}
            if args.mode in ("apply", "rollback") and res["commit_ok"]:
                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)       # SIGTERM/SIGHUP/SIGINT wait until the COMMIT is recorded
                try:
                    try:
                        conn.commit()
                    except BaseException as exc:                              # the commit call ITSELF failed: the server may have committed
                        o.mark_commit_unknown(digest, type(exc).__name__)
                        raise
                    o.mark_committed(digest)
                finally:
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, _HELD_SIGNALS)
                result["status"] = "COMMITTED"
                write_evidence(run_dir, res, result)
                return 0, conclude(o, result, "applied", digest)
            conn.rollback()
            if args.mode in ("apply", "rollback"):
                result["status"] = "REFUSED_ROLLED_BACK"
                write_evidence(run_dir, res, result)
                return 1, conclude(o, result, "failed", digest, ck.failed or ["refused_unspecified"])
            good = res["commit_ok"] if args.mode != "count" else not ck.failed
            result["status"] = ("COUNT_READ_ONLY_OK" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD") if good else \
                ("COUNT_REFUSED" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_REFUSED")
            write_evidence(run_dir, res, result)
            if good:
                return 0, conclude(o, result, "dry_run", digest)
            return 2, conclude(o, result, "failed", digest, ck.failed or ["refused_unspecified"])
        finally:
            conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    for m in MODES:
        g.add_argument("--" + m, action="store_const", const=m, dest="mode")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    p.add_argument("--writer-commit")
    p.add_argument("--evidence-root", default=None, help="ignored unless " + TEST_EVIDENCE_ENV + " is set (tests only)")
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if not a.expect_plan:
        p.error("every mode requires --expect-plan <sha256> (the credential is fetched only for a named plan hash)")
    if a.mode in ("apply", "rollback") and not a.expect_evidence:
        p.error("--" + a.mode + " requires --expect-evidence <digest printed by the matching dry run>")
    if a.mode == "apply" and not a.writer_commit:
        p.error("--apply requires --writer-commit <full sha>")
    return a


def refuse_under_test_outside_pytest(gate_fp, environ=None):
    environ = os.environ if environ is None else environ
    if gate_fp.get("under_test") and PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: the launch marker says the gate ran under test (GATE_V2_UNDER_TEST=1): the executor does not run against a "
                         "database from such a launch outside a pytest run. Start it through run_gated.sh without the test flag.\n")
        raise SystemExit(EXIT_NO_LAUNCH)


def main(argv=None) -> int:
    gate_fp = launch_gate()                  # FIRST: before the arguments are even parsed
    refuse_under_test_outside_pytest(gate_fp)
    args = parse_args(sys.argv[1:] if argv is None else argv)
    install_signal_handlers()
    try:
        code, result = execute(args, connect_admin, gate_fp=gate_fp)
    except SystemExit:
        raise
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
