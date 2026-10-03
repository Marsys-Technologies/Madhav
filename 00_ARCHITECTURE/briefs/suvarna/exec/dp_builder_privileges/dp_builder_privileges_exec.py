#!/usr/bin/env python3
"""OWNER-PATH executor for migration numbers 1272 and 1273 (S-L2 preconditions B3 and B4). HELD: NEVER RUN against any real system, NEVER APPLIED.

  1272 (B3)  public.bind_l2_exact_inputs(uuid, jsonb) is redefined (owner data_plane_l2_owner, SECURITY DEFINER) so that it GRANTs SELECT on the pg_temp shadows
             it creates to data_plane_builder. Today the shadows belong to data_plane_l2_owner and carry no ACL, so the pipeline login gets
             `permission denied for table chart_facts` on its first read of an input table. The function's row in l2_data_plane_function_attestations
             is re-attested in the same transaction (immutability trigger disabled and re-enabled around the UPDATE).
  1273 (B4)  GRANT EXECUTE on bodha_signal_identity / bodha_cgm_node_identity / bodha_cgm_edge_identity / bodha_contradiction_identity and their four
             _namespace() functions to data_plane_builder. These eight functions are owned by amjis_app (read from production pg_proc 2026-10-03), so the
             grants run as amjis_app; nothing else about them changes.

Why an executor and not migrate.ts: the bind function is a protected L2 object (owner data_plane_l2_owner, attested, compared by the deploy gate
data-plane-ownership-status.ts), and SS ruled that both changes use the gated owner path of the D6 executors. The SQL files 1272_*.sql / 1273_*.sql next to this
file carry the numbers for history and are NEVER discovered by migrate.ts (it reads platform/migrations and platform/supabase/migrations only; proven by
platform/tests/unit/migrations/dp_builder_privileges_not_discovered.test.ts).

ONE transaction as the administrator with TRANSIENT role membership (GRANT data_plane_l2_owner / amjis_app TO CURRENT_USER only if not already a member,
SET LOCAL ROLE per step, REVOKE exactly what was granted before COMMIT; net membership identical). COMMIT only if every check holds, including ASSERTING
post-checks that RAISE inside the transaction (has_function_privilege / has_table_privilege), and the evidence digest equals --expect-evidence.

MODES (every mode needs --expect-plan: the in-process administrator credential is fetched only for a plan hash the operator names)
  --count                          read-only: preconditions + pre-state, always ROLLBACK
  --dry-run                        apply everything, print the exact catalog diff, run every commit condition, ROLLBACK
  --apply --expect-plan H --expect-evidence D
                                   same transaction; COMMIT only if every check holds and D equals this run's evidence digest
  --rollback-dry-run               the exact inverse, applied then rolled back
  --rollback --expect-plan H --expect-evidence D
                                   the inverse, committed: the shipped live bind definition re-applied and re-attested, the eight EXECUTE grants revoked

LAUNCH (GATE_V2). Never started directly: `exec/gate_v2/run_gated.sh <python3> dp_builder_privileges_exec.py <args>` (the SAME explicit interpreter for the dry
run and the apply). main() calls launch_gate() FIRST: exit 93 without a verifying GATE_V2_LAUNCH marker or if a pin differs. outcome.json (dry_run | applied | failed
| commit_state_unknown) is written in every mode with python_executable, python_version, psycopg_version and libpq_version, which are also bound into the evidence
digest: --apply / --rollback refuse (exit 92, before any connection) under a different interpreter or driver than the matching dry run. Python 3.11 and 3.12+.
OTHER EXIT CODES: 94 = the connection is not the expected administrator / database / server major version, or is a superuser (checked first, before any other statement); 96 = commit() itself
raised (state unknown: read the database; outcome.json says commit_state_unknown); 92 interpreter; 93 launch gate; 95 test variable outside pytest.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import difflib
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


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod            # dataclasses (postponed annotations) resolve their module through sys.modules
    spec.loader.exec_module(mod)
    return mod


bp = _load("dp_bind_patch", HERE / "bind_patch.py")

PROJECT = "madhav-astrology"
LOCK_TIMEOUT = "5s"
STATEMENT_TIMEOUT = "120s"
OWNER_L2 = "data_plane_l2_owner"
APP_OWNER = "amjis_app"
BUILDER = "data_plane_builder"
SEARCH_PATH = "pg_catalog, public, pg_temp"
GATE_SEARCH_PATH = "public"
FN_ATT = "public.l2_data_plane_function_attestations"
FN_ATT_IMMUTABLE = "l2_data_plane_function_attestations_immutable"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/DpBuilderPrivileges"
LIVE_DEFS = HERE / "live_defs"
SQL_FILES = ("1272_bind_l2_exact_inputs_builder_reads_shadows.sql", "1273_builder_execute_bodha_identity_functions.sql")
GATE_LIFECYCLE_FUNCTIONS = (
    "open_l1_data_plane_generation", "capture_l1_data_plane_dasha_partition", "authorize_l1_chart_facts_delete",
    "complete_l1_data_plane_partition", "select_l1_data_plane_generation", "rollback_l1_data_plane_generation",
    "assert_l2_msr_delete_safe", "bind_l2_exact_inputs", "open_l2_data_plane_generation",
    "complete_l2_data_plane_partition", "select_l2_data_plane_generation", "rollback_l2_data_plane_generation",
)


class ExpectedDiffError(Exception):
    """The shipped hunk does not produce the bound patched body: nothing may run."""


@dataclasses.dataclass(frozen=True)
class FunctionPatch:
    signature: str
    live_md5: str
    live_len: int
    live_sha256: str
    owner: str
    secdef: bool
    config: str
    acl: str
    hunks: tuple
    patched_md5: str
    patched_sha256: str
    diff_sha256: str
    diff_hunks: int

    @property
    def short(self) -> str:
        return self.signature.split("(")[0]

    @property
    def regproc(self) -> str:
        return "public." + self.signature

    @property
    def live_file(self) -> pathlib.Path:
        return LIVE_DEFS / f"{self.short}.LIVE.sql"

    def live_def(self) -> str:
        text = self.live_file.read_bytes().decode("utf-8")
        if hashlib.md5(text.encode()).hexdigest() != self.live_md5 or len(text) != self.live_len \
                or hashlib.sha256(text.encode()).hexdigest() != self.live_sha256:
            raise ExpectedDiffError(f"{self.short}: the shipped live definition does not match the bound live md5/length/sha256")
        return text

    def patched_def(self) -> str:
        live = self.live_def()
        try:
            new = bp.apply_hunks(live, self.hunks)
        except ValueError as exc:
            raise ExpectedDiffError(f"{self.short}: {exc}")
        got = (hashlib.md5(new.encode()).hexdigest(), hashlib.sha256(new.encode()).hexdigest(), bp.diff_digest(live, new), len(bp.unified_hunks(live, new)))
        want = (self.patched_md5, self.patched_sha256, self.diff_sha256, self.diff_hunks)
        if got != want:
            raise ExpectedDiffError(f"{self.short}: the patched body differs from the EXPECTED_DIFF (md5/sha256/diff sha256/hunks) {got} != {want}")
        return new


# Read from the live catalog as suvarna_reader on 2026-10-03 (PostgreSQL 15.18): md5/length/sha256 of pg_get_functiondef (sha256 equals the attestation row),
# owner / SECURITY DEFINER / proconfig / ACL.
BIND_PATCH = FunctionPatch(
    signature="bind_l2_exact_inputs(uuid,jsonb)",
    live_md5="7bf8987517a7b76bd7ffae1c2bcf32ee", live_len=5678,
    live_sha256="af58dae4df9054784e078dfdfbf8a556a129efa01432b27d85d2ee7c3b5ca992",
    owner=OWNER_L2, secdef=True, config='{"search_path=pg_catalog, public, pg_temp"}',
    acl="{data_plane_l2_owner=X/data_plane_l2_owner,data_plane_builder=X/data_plane_l2_owner}",
    hunks=tuple(bp.BIND_HUNKS),
    patched_md5="44c7e524a082ada7c919afd8d325ba8a",
    patched_sha256="ebcb13b44746bef2f9c8b89dcfb75cb68766592d4328295c0babd62938683252",
    diff_sha256="f39b6e211e0a72da8bf0c52497b9518a06504658f28a71fbe25044e2ee4c0241", diff_hunks=2)

# B4: the eight identity functions (all owned by amjis_app, not SECURITY DEFINER, no proconfig). ACL read 2026-10-03.
_EV = "{amjis_app=X/amjis_app,nirmana_evidence_ingress_writer=X/amjis_app}"
_AP = "{amjis_app=X/amjis_app}"
IDENTITY_FUNCTIONS = (
    ("bodha_cgm_edge_identity(uuid,text,text,text,uuid,uuid)", _AP),
    ("bodha_cgm_edge_identity_namespace()", _AP),
    ("bodha_cgm_node_identity(uuid,text,text,text)", _AP),
    ("bodha_cgm_node_identity_namespace()", _AP),
    ("bodha_contradiction_identity(uuid,text,uuid,uuid)", _AP),
    ("bodha_contradiction_identity_namespace()", _AP),
    ("bodha_signal_identity(uuid,text,text,text,jsonb)", _EV),
    ("bodha_signal_identity_namespace()", _EV),
)
IDENTITY_OWNER = APP_OWNER
# NIT-2: md5(pg_get_functiondef) of the eight, read from production 2026-10-03 as suvarna_reader. A GRANT cannot change a body; the guard makes "unchanged" literal.
IDENTITY_BODY_MD5 = {
    "bodha_cgm_edge_identity(uuid,text,text,text,uuid,uuid)": "27687d64d968ca4ea1cf816325aea9a6",
    "bodha_cgm_edge_identity_namespace()": "118b01c9d6c5607f294b3f5ac3eeed79",
    "bodha_cgm_node_identity(uuid,text,text,text)": "f783e24eebfcbad004bf83f4314c2db3",
    "bodha_cgm_node_identity_namespace()": "6ae5e390130f560449f91167afd64922",
    "bodha_contradiction_identity(uuid,text,uuid,uuid)": "ebc7ad85bc4a4df56bf0c60df08cbb87",
    "bodha_contradiction_identity_namespace()": "e9ceb71f71e2b7ee12a5f5ad57e7bc7c",
    "bodha_signal_identity(uuid,text,text,text,jsonb)": "fee6184131bcee9c00865626b972719d",
    "bodha_signal_identity_namespace()": "50e7c33f10f8b546a7709e42d8711fa3",
}


def acl_set(text: str) -> frozenset:
    """'{a=X/b,c=X/d}' -> frozenset of 'a=X/b' items ('' / None -> empty)."""
    t = (text or "").strip()
    if not t or t == "{}":
        return frozenset()
    return frozenset(x.strip().strip('"') for x in t.strip("{}").split(","))


BUILDER_ITEM = f"{BUILDER}=X/{IDENTITY_OWNER}"

EXPECTED_DIFF = {
    "functions": [{
        "function": BIND_PATCH.signature, "live_md5": BIND_PATCH.live_md5, "patched_md5": BIND_PATCH.patched_md5,
        "live_sha256": BIND_PATCH.live_sha256, "patched_sha256": BIND_PATCH.patched_sha256,
        "differs_ONLY_by_hunks": [h[0] for h in BIND_PATCH.hunks], "zero_context_diff_hunks": BIND_PATCH.diff_hunks,
        "zero_context_diff_sha256": BIND_PATCH.diff_sha256,
        "owner_security_definer_config_acl": f"unchanged: {BIND_PATCH.owner} / SECURITY DEFINER={BIND_PATCH.secdef} / {BIND_PATCH.config} / {BIND_PATCH.acl}",
        "attestation": f"{BIND_PATCH.signature}|digest {BIND_PATCH.live_sha256} -> {BIND_PATCH.patched_sha256}|owner/secdef/config unchanged|ONE row"}],
    "identity_function_grants": [f"{sig}|ACL gains exactly {BUILDER_ITEM}|owner/secdef/config unchanged" for sig, _ in IDENTITY_FUNCTIONS],
    "unchanged": ["every other function (definition, owner, SECURITY DEFINER, config, ACL)", "every other function attestation row (L1 and L2)",
                  "every table / sequence / schema / database ACL", "role membership (net)", "RLS", "policy", "append-only (immutable) triggers: all enabled before and after"],
    "no_other_role_gains_access": "across ALL roles, the set of (role, identity function) pairs with EXECUTE gains exactly the eight (data_plane_builder, f) pairs and loses none",
    "grant_mechanics_probe": "a temp table created as data_plane_l2_owner inside the transaction, granted SELECT to data_plane_builder with the statement the patched body issues: "
                             "has_table_privilege true for data_plane_builder and false for every other role",
    "deploy_gate": "the gate's own three queries (trigger shape, trigger surface, function digests) are false AFTER the plan under search_path public; stored == gate-side digest of the bind function",
    "rollback": "the exact inverse: the shipped live bind definition re-applied and re-attested, the eight EXECUTE grants revoked: md5, attestation row and ACLs equal the pre-state",
}

# ------------------------------------------------------------------------------------------------------ gate wiring (GATE_V2)
GATE_TBD = "TBD_BIND_AT_GATE_REVISION_3"
# Bound to GATE_V2 revision 3 (SS decision N-86); exec/gate_v2 on main carries these exact files (shasum -a 256, 2026-10-03).
GATE_PINS = {"prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
             "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
             "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
GATE_DIR_ENV = "DPBP_TEST_GATE_DIR"
TEST_EVIDENCE_ENV = "DPBP_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = 93
EXIT_TEST_ENV = 95
EXIT_INTERPRETER = 92
EXIT_WRONG_TARGET = 94       # connected as the wrong role / to the wrong database / to the wrong server major version / as a superuser: before anything else
EXIT_COMMIT_UNKNOWN = 96     # commit() itself raised: the change may or may not be committed (distinct from every refusal)
MODES = ("count", "dry-run", "apply", "rollback-dry-run", "rollback")


def gate_dir(environ=None) -> pathlib.Path:
    environ = os.environ if environ is None else environ
    if GATE_DIR_ENV in environ:
        if PYTEST_ENV not in environ:
            sys.stderr.write(f"REFUSED: {GATE_DIR_ENV} is set outside a pytest run; it would redirect the gate files.\n")
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
    environ = os.environ if environ is None else environ
    try:
        es = standards(environ)
    except FileNotFoundError:
        sys.stderr.write(f"REFUSED: the GATE_V2 files are not at {gate_dir(environ)} (exec/gate_v2): this executor cannot be launched.\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    if any(v == GATE_TBD for v in GATE_PINS.values()):
        sys.stderr.write("REFUSED: the GATE_V2 pins in this executor are TBD: the plan hash is PROVISIONAL and this executor cannot run.\n")
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


@dataclasses.dataclass(frozen=True)
class Leg:
    name: str                 # forward | rollback
    from_def: str             # the bind definition expected before
    to_def: str               # and after
    from_md5: str
    to_md5: str
    from_sha: str
    to_sha: str
    grant_sql: tuple          # one statement per identity function


def grant_stmt(sig: str, revoke: bool) -> str:
    return (f"REVOKE EXECUTE ON FUNCTION public.{sig} FROM {BUILDER}" if revoke else f"GRANT EXECUTE ON FUNCTION public.{sig} TO {BUILDER}")


def forward_leg() -> Leg:
    p = BIND_PATCH
    return Leg("forward", p.live_def(), p.patched_def(), p.live_md5, p.patched_md5, p.live_sha256, p.patched_sha256,
               tuple(grant_stmt(s, False) for s, _ in IDENTITY_FUNCTIONS))


def rollback_leg() -> Leg:
    p = BIND_PATCH
    return Leg("rollback", p.patched_def(), p.live_def(), p.patched_md5, p.live_md5, p.patched_sha256, p.live_sha256,
               tuple(grant_stmt(s, True) for s, _ in IDENTITY_FUNCTIONS))


def fn_att_update_sql(sig: str) -> str:
    return (f"UPDATE {FN_ATT} a SET definition_digest = encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') FROM pg_proc p "
            f"WHERE a.function_signature='{sig}' AND p.oid=to_regprocedure('public.'||a.function_signature)")


def render_plan(sha: str | None = None, pins: dict | None = None) -> str:
    sha = sha or exec_sha()
    pins = pins or GATE_PINS
    p = BIND_PATCH
    lines = [
        "-- OWNER-PATH plan for migration numbers 1272 (B3) and 1273 (B4): bind_l2_exact_inputs() grants the shadows it creates to data_plane_builder; data_plane_builder gets EXECUTE on the eight bodha_*_identity functions (+ their namespaces) (and the exact inverse)",
        f"-- one transaction as the administrator with TRANSIENT role membership: GRANT {OWNER_L2} TO CURRENT_USER and GRANT {APP_OWNER} TO CURRENT_USER, each only if the administrator is not already a member; SET LOCAL ROLE per step; REVOKE exactly what was granted before COMMIT; net membership identical (checked: post_membership_equals_pre_state_after_revoke)",
        f"SET LOCAL search_path = {SEARCH_PATH}",
        f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'",
        f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'",
        "-- FORWARD (--dry-run / --apply):",
        f"-- preconditions (read only; any failure = refuse + ROLLBACK): no build_runs planned/running/paused on ANY chart (as {APP_OWNER}); no L1 generation 'building' (as {OWNER_L2}); the administrator is a member of pg_read_all_stats (asserted and printed; production `postgres` is a pg_monitor member through cloudsqlsuperuser) and no {BUILDER} session is hidden, active or idle-in-transaction; public.digest(text,text) resolves; the deploy gate's own three queries green BEFORE the plan; "
        f"{p.signature}: EXISTS, owner {p.owner}, SECURITY DEFINER {p.secdef}, proconfig {p.config}, ACL {p.acl}; pg_get_functiondef equals BYTE-FOR-BYTE the shipped pre-state (md5 {p.live_md5}, {p.live_len} chars, live_defs/{p.short}.LIVE.sql); its attestation row EXISTS exactly once with digest {p.live_sha256}; "
        f"each of the eight identity functions EXISTS, owner {IDENTITY_OWNER}, not SECURITY DEFINER, no proconfig, md5(pg_get_functiondef) as bound, with the bound ACL and without any {BUILDER} EXECUTE.",
        f"-- STEP B3 (1272), as {OWNER_L2}: CREATE OR REPLACE FUNCTION public.{p.signature} with the live definition plus exactly these hunks:",
    ]
    for name, old, new in p.hunks:
        lines.append(f"--   hunk {name}:")
        lines.append("--     - " + old.replace("\n", "\n--       "))
        lines.append("--     + " + new.replace("\n", "\n--       "))
    lines.append(f"--   bound: patched md5 {p.patched_md5}, sha256 {p.patched_sha256}; zero-context diff {p.diff_hunks} hunk, sha256 {p.diff_sha256}; re-checked against pg_get_functiondef after the statement")
    lines += [f"-- re-attest the bind function row (immutability trigger off, then on, same transaction; rowcount must be 1):",
              f"ALTER TABLE {FN_ATT} DISABLE TRIGGER {FN_ATT_IMMUTABLE}", fn_att_update_sql(p.signature), f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}",
              f"-- STEP B4 (1273), as {IDENTITY_OWNER} (the owner of the eight functions):"]
    lines += [grant_stmt(s, False) for s, _ in IDENTITY_FUNCTIONS]
    lines += [
        f"-- FIRST, on a new connection and before any other statement (exit {EXIT_WRONG_TARGET} otherwise): current_user = session_user = {PRODUCTION_TARGET.user}, current_database = {PRODUCTION_TARGET.database}, server major version {PRODUCTION_TARGET.server_major}, NOT a superuser, CREATEROLE; the facts are printed.",
        "-- ASSERTING post-checks (DO blocks that RAISE; the transaction is rolled back if any fails): has_function_privilege(data_plane_builder, <each of the eight>, 'EXECUTE') is true; "
        "the grant-mechanics probe (a temp table created as data_plane_l2_owner and granted with the patched body's statement): has_table_privilege true for data_plane_builder and false for every other role.",
        "-- commit only if ALL hold (EXPECTED_DIFF): across a before/after snapshot of every public data-plane function (definition md5, owner, secdef, config, ACL), the identity functions' ACLs, both function attestation tables, "
        "every table/sequence/schema/database ACL, role membership and the append-only trigger states: exactly ONE data-plane function changed (the bind function: new md5, owner/secdef/config/ACL unchanged) and exactly ONE function attestation row changed (digest live -> patched); "
        f"exactly EIGHT identity function ACLs changed, each gaining exactly {BUILDER_ITEM}; across ALL roles the set of (role, identity function) EXECUTE pairs gains exactly the eight builder pairs and loses none; "
        "pg_get_functiondef after == the patched body; the attestation row equals the live function under the gate's own join and equals the bound digest; the gate's three queries are false AFTER the plan under search_path public; "
        "transient grants revoked and membership equals the pre-state; --expect-plan == plan hash; --expect-evidence == this run's evidence digest (the digest binds the interpreter path, the full sys.version, the psycopg and libpq versions).",
        "-- ROLLBACK (--rollback-dry-run / --rollback), the exact inverse: preconditions mirror the forward ones with the patched constants; CREATE OR REPLACE from the shipped live definition, re-attest, REVOKE EXECUTE from data_plane_builder on the eight functions; commit conditions mirror the forward ones.",
        "-- the real run is started ONLY through exec/gate_v2/run_gated.sh <python3> <this file> <args> (GATE_V2), the SAME explicit interpreter for the dry run and the apply (exit 92 otherwise); the executor REFUSES (exit 93) unless the marker verifies against the gate files pinned below; "
        "it writes outcome.json in every mode and refuses an under_test launch marker (exit 93) and a DPBP_TEST_* variable (exit 95) outside pytest.",
        "-- every mode needs --expect-plan: the in-process administrator credential is fetched only after the plan hash matched.",
        "-- gate files (exec/gate_v2; pins BOUND, GATE_V2 revision 3): prerun_gate.py sha256 %s; run_gated.sh sha256 %s; executor_standards.py sha256 %s" % (pins["prerun_gate.py"], pins["run_gated.sh"], pins["executor_standards.py"]),
        "-- plan hash = bind_gate_into_plan_hash(sha256(plan text + \"\\n\" + json(EXPECTED_DIFF)), prerun_gate.py pin, run_gated.sh pin)",
        "-- gate table lists (parsed at run time from platform/scripts/data-plane-ownership-preflight.ts; bound here BY CONTENT): " + "; ".join(
            f"{k} ({len(v)}) sha256 {hashlib.sha256(','.join(v).encode()).hexdigest()} [{','.join(v)}]" for k, v in load_gate_lists().items()),
        "-- bind patch module: bind_patch.py sha256 %s" % sha_file(HERE / "bind_patch.py"),
        "-- live definition: live_defs/%s.LIVE.sql sha256 %s" % (p.short, sha_file(p.live_file)),
        "-- history SQL (never run by migrate.ts): " + "; ".join(f"{n} sha256 {sha_file(HERE / n)}" for n in SQL_FILES),
        "-- executor: dp_builder_privileges_exec.py sha256 %s" % sha,
    ]
    return "\n".join(lines)


def plan_hash_unbound(sha: str | None = None, pins: dict | None = None) -> str:
    return hashlib.sha256((render_plan(sha, pins) + "\n" + json.dumps(EXPECTED_DIFF, sort_keys=True)).encode()).hexdigest()


def plan_hash(sha: str | None = None, pins: dict | None = None, environ=None) -> str:
    pins = pins or GATE_PINS
    return standards(environ).bind_gate_into_plan_hash(plan_hash_unbound(sha, pins),
                                                        {"gate_sha256": pins["prerun_gate.py"], "run_gated_sha256": pins["run_gated.sh"]})


# ------------------------------------------------------------------------------------------------------------------ db plumbing
def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


@dataclasses.dataclass(frozen=True)
class Target:
    """Who and where the administrator connection must be. Production values below; tests pass a mirror target to execute() (there is NO environment route)."""
    user: str = "postgres"
    database: str = "amjis"
    server_major: int = 15


PRODUCTION_TARGET = Target()


class CommitStateUnknown(Exception):
    def __init__(self, exc_name: str) -> None:
        super().__init__(exc_name)
        self.exc_name = exc_name


def check_target(conn, target: Target) -> tuple[bool, list[str]]:
    """LOW-1. The very first statements on a new connection: current_user = session_user = the named administrator, current_database = the named database,
    server major version, NOT a superuser (the plan is written for a CREATEROLE administrator with transient membership), and CREATEROLE. -> (ok, facts)."""
    cur = conn.cursor()
    cur.execute("SELECT current_user, session_user, current_database(), current_setting('server_version_num')::int / 10000, r.rolsuper, r.rolcreaterole, "
                "pg_has_role(current_user, 'pg_monitor', 'MEMBER'), pg_has_role(current_user, 'pg_read_all_stats', 'MEMBER') "
                "FROM pg_roles r WHERE r.rolname = current_user")
    cu, su, db, major, sup, crt, mon, stats = cur.fetchone()
    conn.rollback()
    facts = [f"target: current_user={cu} session_user={su} database={db} server_major={major} superuser={sup} createrole={crt} pg_monitor={mon} pg_read_all_stats={stats}"]
    ok = (cu, su, db, major) == (target.user, target.user, target.database, target.server_major) and not sup and crt
    return ok, facts


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


class CountingCursor:
    def __init__(self, cur) -> None:
        self._cur = cur
        self.n = 0

    def execute(self, *a, **k):
        self.n += 1
        return self._cur.execute(*a, **k)

    def __getattr__(self, name):
        return getattr(self._cur, name)


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_member(cur, role: str) -> bool:
    cur.execute("SELECT pg_has_role(current_user, %s, 'MEMBER')", (role,))
    return bool(cur.fetchone()[0])


_IDS = ", ".join("'%s'" % s.split("(")[0] for s, _ in IDENTITY_FUNCTIONS)
_LIFECYCLE = ", ".join("'%s'" % n for n in GATE_LIFECYCLE_FUNCTIONS)
SNAP_SQL = {
    # every data-plane / lifecycle function: definition md5, owner, secdef, config, ACL (the identity functions are covered by "identity")
    "function": ("SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)), pg_get_userbyid(p.proowner), p.prosecdef::text, COALESCE(p.proconfig::text,''), "
                 "COALESCE(p.proacl::text,'') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' "
                 f"AND (p.proname LIKE 'l1\\_data\\_plane\\_%' OR p.proname LIKE 'l2\\_data\\_plane\\_%' OR p.proname IN ({_LIFECYCLE})) ORDER BY 1"),
    "identity": ("SELECT p.oid::regprocedure::text, pg_get_userbyid(p.proowner), p.prosecdef::text, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,'') "
                 f"FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname IN ({_IDS}) ORDER BY 1"),
    "function_attestation": ("SELECT function_signature, definition_digest, owner_name, security_definer::text, COALESCE(config::text,'') FROM public.l1_data_plane_function_attestations "
                             "UNION ALL SELECT function_signature, definition_digest, owner_name, security_definer::text, COALESCE(config::text,'') FROM public.l2_data_plane_function_attestations ORDER BY 1"),
    "other_function_acl": ("SELECT p.oid::regprocedure::text, COALESCE(p.proacl::text,'') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                           f"WHERE n.nspname='public' AND p.proname NOT IN ({_IDS}) ORDER BY 1"),
    "acl": ("SELECT 'rel', c.relname, COALESCE(c.relacl::text,'') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','S') "
            "UNION ALL SELECT 'schema', nspname, COALESCE(nspacl::text,'') FROM pg_namespace WHERE nspname='public' "
            "UNION ALL SELECT 'database', datname, COALESCE(datacl::text,'') FROM pg_database WHERE datname=current_database() ORDER BY 1,2"),
    "membership": ("SELECT parent.rolname, member.rolname FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member "
                   "WHERE parent.rolname NOT LIKE 'pg\\_%' AND member.rolname NOT LIKE 'pg\\_%' ORDER BY 1,2"),
    "rls": "SELECT c.relname, c.relrowsecurity::text, c.relforcerowsecurity::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' ORDER BY 1",
    "policy": "SELECT tablename, policyname, cmd, roles::text FROM pg_policies WHERE schemaname='public' ORDER BY 1,2",
    "immutable_triggers": ("SELECT c.relname, t.tgname, t.tgenabled::text FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                           "WHERE n.nspname='public' AND t.tgname LIKE '%\\_attestations\\_immutable' ORDER BY 1,2"),
    # (role, identity function) pairs with EXECUTE, across ALL roles (PUBLIC included through the ACL default)
    "execute_pairs": ("SELECT r.rolname, p.oid::regprocedure::text FROM pg_roles r CROSS JOIN pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                      f"WHERE n.nspname='public' AND p.proname IN ({_IDS}) AND has_function_privilege(r.oid, p.oid, 'EXECUTE') ORDER BY 1,2"),
}


def snap(cur) -> dict:
    out = {}
    for k, sql in SNAP_SQL.items():
        cur.execute(sql)
        out[k] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    return out


class Checks:
    def __init__(self) -> None:
        self.items: list[tuple[str, bool, str | None]] = []

    def chk(self, name: str, ok: bool, detail=None) -> bool:
        self.items.append((name, bool(ok), None if detail is None else str(detail)[:300]))
        return bool(ok)

    @property
    def failed(self) -> list[str]:
        return [n for n, ok, _ in self.items if not ok]


# ------------------------------------------------------------------------------------------------------- the deploy gate's own queries
GATE_TRIGGER_SHAPE = """
SELECT EXISTS (
  SELECT 1 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid
  WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
    AND (
      (t.tgname='l1_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l1_data_plane_guard_active_mutation()'::regprocedure))
      OR (t.tgname='l1_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l1_data_plane_capture_row()'::regprocedure))
      OR (t.tgname='l2_data_plane_mutation_guard' AND (t.tgtype<>31 OR p.oid<>'public.l2_data_plane_guard_active_mutation()'::regprocedure))
      OR (t.tgname='l2_data_plane_capture' AND (t.tgtype<>21 OR p.oid<>'public.l2_data_plane_capture_row()'::regprocedure))
    )
) OR (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
       JOIN pg_namespace n ON n.oid=c.relnamespace
       WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
         AND t.tgname IN ('l1_data_plane_mutation_guard','l2_data_plane_mutation_guard')) <> cardinality(%(tables)s::text[])
AS unsafe
"""
GATE_TRIGGER_SURFACE = """
WITH expected AS (
  SELECT * FROM public.l1_data_plane_trigger_attestations
  UNION ALL SELECT * FROM public.l2_data_plane_trigger_attestations
), actual AS (
  SELECT c.relname table_name,t.tgname trigger_name,t.tgtype trigger_type,
         t.tgenabled enabled,t.tgfoid function_oid,t.tgfoid::regprocedure::text function_signature,
         encode(digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') definition_digest
  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE NOT t.tgisinternal AND n.nspname='public' AND c.relname=ANY(%(tables)s::text[])
)
SELECT EXISTS (
  SELECT 1 FROM actual a FULL JOIN expected e
    ON a.table_name=e.table_name AND a.trigger_name=e.trigger_name
   AND a.trigger_type=e.trigger_type AND a.enabled=e.enabled
   AND a.function_oid=e.function_oid AND a.function_signature=e.function_signature
   AND a.definition_digest=e.definition_digest
  WHERE a.table_name IS NULL OR e.table_name IS NULL
) AS unsafe
"""
GATE_FUNCTION_DIGESTS = """
SELECT EXISTS (
  SELECT 1 FROM (
    SELECT * FROM public.l1_data_plane_function_attestations
    UNION ALL SELECT * FROM public.l2_data_plane_function_attestations
  ) a
  LEFT JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature)
  WHERE p.oid IS NULL OR a.definition_digest<>encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
    OR a.owner_name<>pg_get_userbyid(p.proowner)
    OR a.security_definer<>p.prosecdef
    OR a.config IS DISTINCT FROM p.proconfig
) OR EXISTS (
  SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  JOIN pg_roles owner ON owner.oid=p.proowner
  WHERE n.nspname='public' AND owner.rolname=ANY(%(owners)s::text[])
    AND (p.proname LIKE 'l1_data_plane_%%' OR p.proname LIKE 'l2_data_plane_%%'
      OR p.proname=ANY(%(lifecycle)s::text[]))
    AND NOT EXISTS (
      SELECT 1 FROM (
        SELECT function_signature FROM public.l1_data_plane_function_attestations
        UNION ALL SELECT function_signature FROM public.l2_data_plane_function_attestations
      ) a WHERE p.oid=to_regprocedure('public.'||a.function_signature)
    )
) AS unsafe
"""
GATE_FN_DIGEST_SHOW = """
SELECT a.definition_digest, encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
FROM public.l2_data_plane_function_attestations a
JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature)
WHERE a.function_signature=%s
"""


def load_gate_lists(root: pathlib.Path = REPO_ROOT) -> dict[str, list[str]]:
    """L1_ACTIVE_TABLES and L2_ACTIVE_TABLES parsed from the gate's own source (12 + 29), asserted so the gate mirror can never be vacuously green."""
    text = (root / "platform/scripts/data-plane-ownership-preflight.ts").read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    lists: dict[str, list[str]] = {}
    for name in ("L1_ACTIVE_TABLES", "L2_ACTIVE_TABLES"):
        m = re.search(r"export const %s = \[(.*?)\] as const" % name, text, re.S)
        if not m:
            raise SystemExit(f"cannot parse {name} from data-plane-ownership-preflight.ts")
        lists[name] = re.findall(r"'([a-z0-9_]+)'", m.group(1))
    if (len(lists["L1_ACTIVE_TABLES"]), len(lists["L2_ACTIVE_TABLES"])) != (12, 29):
        raise SystemExit("unexpected gate table counts (expected 12 + 29); the gate's lists changed: re-review this plan")
    return lists


def load_gate_tables(root: pathlib.Path = REPO_ROOT) -> list[str]:
    lists = load_gate_lists(root)
    return lists["L1_ACTIVE_TABLES"] + lists["L2_ACTIVE_TABLES"]


def gate_mirror(cur, tables: list[str] | None = None) -> dict:
    tables = tables if tables is not None else load_gate_tables()
    cur.execute(f"SET LOCAL ROLE {APP_OWNER}")
    cur.execute(f"SET LOCAL search_path = {GATE_SEARCH_PATH}")
    out: dict = {}
    cur.execute(GATE_TRIGGER_SHAPE, {"tables": tables})
    out["trigger_shape_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_TRIGGER_SURFACE, {"tables": tables})
    out["trigger_surface_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_FUNCTION_DIGESTS, {"owners": ["data_plane_l1_owner", "data_plane_l2_owner"], "lifecycle": list(GATE_LIFECYCLE_FUNCTIONS)})
    out["function_digests_unsafe"] = bool(cur.fetchone()[0])
    cur.execute(GATE_FN_DIGEST_SHOW, (BIND_PATCH.signature,))
    row = cur.fetchone()
    out["function_digest_stored"], out["function_digest_gate_side"] = (row[0], row[1]) if row else (None, None)
    cur.execute(f"SET LOCAL search_path = {SEARCH_PATH}")
    cur.execute("RESET ROLE")
    return out


def gate_red(g: dict) -> list[str]:
    return [k for k in ("trigger_shape_unsafe", "trigger_surface_unsafe", "function_digests_unsafe") if g[k]]


# ------------------------------------------------------------------------------------------------------------------ preconditions
def preconditions(cur, leg: Leg, ck: Checks, out) -> None:
    """Read-only. Every refusal is a named check; nothing is written and no run is touched."""
    p = BIND_PATCH
    cur.execute(f"SET LOCAL ROLE {APP_OWNER}")
    cur.execute("SELECT count(*), COALESCE(string_agg(DISTINCT left(chart_id::text,8) || ':' || state, ', '), '') FROM public.build_runs WHERE state IN ('planned','running','paused')")
    n, which = cur.fetchone()
    cur.execute("RESET ROLE")
    ck.chk("pre_no_build_in_flight", n == 0, f"{n} build_run(s) in planned/running/paused on ANY chart ({which}); not touched" if n else None)
    cur.execute(f"SET LOCAL ROLE {OWNER_L2}")
    cur.execute("SELECT count(*) FROM public.l1_data_plane_generations WHERE status = 'building'")
    building = cur.fetchone()[0]
    cur.execute("RESET ROLE")
    ck.chk("pre_no_building_generation", building == 0, "an L1 data-plane generation is still 'building'" if building else None)
    # MED-1: the builder-session check is only a detector if the administrator CAN see other sessions' state. Fail closed: assert the fact, print it, and also
    # refuse when any builder session's state is hidden. (Production `postgres` is a member of pg_monitor via cloudsqlsuperuser; read 2026-10-03.)
    cur.execute("SELECT pg_has_role(current_user, 'pg_monitor', 'MEMBER'), pg_has_role(current_user, 'pg_read_all_stats', 'MEMBER')")
    mon, stats = cur.fetchone()
    out(f"administrator {'is' if stats else 'is NOT'} a member of pg_read_all_stats (pg_monitor member: {mon}): the {BUILDER} session check {'can' if stats else 'CANNOT'} see other sessions")
    ck.chk("pre_admin_can_see_all_sessions", bool(stats), None if stats else "the administrator lacks pg_read_all_stats: the builder-session check would pass blind")
    # a session whose state is hidden (NULL) counts as busy: unknown is never read as idle
    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE usename = %s AND pid <> pg_backend_pid() "
                "AND (state IS NULL OR state IN ('active','idle in transaction','idle in transaction (aborted)'))", (BUILDER,))
    busy = cur.fetchone()[0]
    ck.chk("pre_no_builder_session", busy == 0, f"{busy} {BUILDER} session(s) active, idle-in-transaction or with a hidden state" if busy else None)
    cur.execute("SELECT to_regprocedure('public.digest(text,text)') IS NOT NULL")
    ck.chk("pre_pgcrypto_digest_resolves", cur.fetchone()[0], "public.digest(text,text) does not resolve")
    cur.execute("SELECT pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,''), pg_get_functiondef(p.oid) "
                "FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", (p.regproc,))
    row = cur.fetchone()
    if ck.chk("pre_bind_present", row is not None, f"{p.regproc} does not exist"):
        owner, secdef, config, acl, definition = row
        ck.chk("pre_bind_owner_secdef_config_acl", (owner, secdef, config, acl_set(acl)) == (p.owner, p.secdef, p.config, acl_set(p.acl)), (owner, secdef, config, acl))
        md5 = hashlib.md5(definition.encode()).hexdigest()
        ck.chk("pre_bind_body_is_the_bound_body", md5 == leg.from_md5 and definition == leg.from_def, f"live md5 {md5} != the plan's {leg.from_md5}")
    cur.execute(f"SET LOCAL ROLE {OWNER_L2}")
    cur.execute(f"SELECT count(*), min(definition_digest) FROM {FN_ATT} WHERE function_signature = %s", (p.signature,))
    n, dg = cur.fetchone()
    cur.execute("RESET ROLE")
    ck.chk("pre_bind_attestation_row", n == 1 and dg == leg.from_sha, f"{n} row(s), digest {dg}")
    for idx, (sig, acl_want) in enumerate(IDENTITY_FUNCTIONS, 1):
        short = f"id{idx}_" + sig.split("(")[0].replace("bodha_", "").replace("_identity", "").replace("_namespace", "_ns")
        cur.execute("SELECT pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,''), "
                    "has_function_privilege(%s, p.oid, 'EXECUTE') FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", (BUILDER, "public." + sig))
        row = cur.fetchone()
        if not ck.chk(f"pre_{short}_present", row is not None, f"public.{sig} does not exist"):
            continue
        owner, secdef, config, acl, builder_exec = row
        base_ok = (owner, secdef, config) == (IDENTITY_OWNER, False, "")
        ck.chk(f"pre_{short}_owner_secdef_config", base_ok, (owner, secdef, config))
        cur.execute("SELECT md5(pg_get_functiondef(to_regprocedure(%s::text)))", ("public." + sig,))
        ck.chk(f"pre_{short}_body_is_the_bound_body", cur.fetchone()[0] == IDENTITY_BODY_MD5[sig], f"md5 differs from the bound {IDENTITY_BODY_MD5[sig]}")
        if leg.name == "forward":
            ck.chk(f"pre_{short}_acl_bound_no_builder", acl_set(acl) == acl_set(acl_want) and not builder_exec, (acl, builder_exec))
        else:
            ck.chk(f"pre_{short}_acl_bound_plus_builder", acl_set(acl) == acl_set(acl_want) | {BUILDER_ITEM} and builder_exec, (acl, builder_exec))


# ------------------------------------------------------------------------------------------------------------------ apply
GRANT_PROBE_TABLE = "_dpbp_b3_probe"


def apply_leg(cur, leg: Leg) -> dict:
    p = BIND_PATCH
    cur.execute(f"SET LOCAL ROLE {OWNER_L2}")
    cur.execute("SELECT pg_get_functiondef(%s::regprocedure)", (p.regproc,))
    old_def = cur.fetchone()[0]
    cur.execute(leg.to_def)
    cur.execute(f"ALTER TABLE {FN_ATT} DISABLE TRIGGER {FN_ATT_IMMUTABLE}")
    cur.execute(fn_att_update_sql(p.signature))
    att_rows = cur.rowcount
    cur.execute(f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}")
    probe = None
    if leg.name == "forward":
        # grant-mechanics probe, as the function owner: a temp table granted with the very statement the patched body issues
        cur.execute(f"CREATE TEMP TABLE {GRANT_PROBE_TABLE} (x integer) ON COMMIT DROP")
        cur.execute(f"GRANT SELECT ON pg_temp.{GRANT_PROBE_TABLE} TO {BUILDER}")
        # every role except superusers and the administrator running this very transaction (who holds the owner role TRANSIENTLY and is revoked before COMMIT)
        cur.execute("SELECT r.rolname, has_table_privilege(r.oid, to_regclass('pg_temp.' || %s), 'SELECT') FROM pg_roles r "
                    "WHERE r.rolname NOT LIKE 'pg\\_%%' AND NOT r.rolsuper AND r.rolname <> session_user ORDER BY 1", (GRANT_PROBE_TABLE,))
        probe = {name: bool(ok) for name, ok in cur.fetchall()}
    cur.execute("RESET ROLE")
    cur.execute(f"SET LOCAL ROLE {IDENTITY_OWNER}")
    for stmt in leg.grant_sql:
        cur.execute(stmt)
    cur.execute("RESET ROLE")
    return {"function_attestation_rows": att_rows, "old_def": old_def, "grant_probe": probe}


def asserting_post_checks(cur, leg: Leg) -> None:
    """ASSERTING checks: DO blocks that RAISE. A failure aborts the transaction (the caller rolls back)."""
    sigs = [s for s, _ in IDENTITY_FUNCTIONS]
    cond = "NOT" if leg.name == "forward" else ""
    for s in sigs:
        cur.execute("DO $chk$ BEGIN IF " + cond + f" has_function_privilege('{BUILDER}', 'public.{s}', 'EXECUTE') THEN "
                    f"RAISE EXCEPTION 'asserting post-check failed: {BUILDER} EXECUTE on {s} is not as planned ({leg.name})'; END IF; END $chk$")


def check_after(cur, leg: Leg, before: dict, after: dict, plan: dict, ck: Checks) -> None:
    p = BIND_PATCH
    ck.chk("post_attestation_update_rowcount_is_1", plan["function_attestation_rows"] == 1, plan["function_attestation_rows"])
    # exactly ONE data-plane function changed: the bind function, and only its definition md5
    removed, added = before["function"] - after["function"], after["function"] - before["function"]
    ck.chk("post_exactly_1_data_plane_function_entry_changed", len(removed) == 1 and len(added) == 1, f"-{len(removed)} +{len(added)}")
    ck.chk("post_changed_function_is_exactly_the_bind_function",
           {r[0] for r in removed} == {p.signature} == {r[0] for r in added}, sorted({r[0] for r in removed}))
    if removed and added:
        r, a = next(iter(removed)), next(iter(added))
        ck.chk("post_bind_only_the_definition_md5_changed", r[0] == a[0] and r[2:] == a[2:] and r[1] == leg.from_md5 and a[1] == leg.to_md5, (r, a))
    removed, added = before["function_attestation"] - after["function_attestation"], after["function_attestation"] - before["function_attestation"]
    ck.chk("post_exactly_1_function_attestation_row_changed", len(removed) == 1 and len(added) == 1
           and {r[0] for r in removed} == {p.signature} == {a[0] for a in added}
           and next(iter(removed))[1] == leg.from_sha and next(iter(added))[1] == leg.to_sha and next(iter(removed))[2:] == next(iter(added))[2:], f"-{len(removed)} +{len(added)}")
    # the eight identity functions: each ACL gains (or loses) exactly the builder item; owner/secdef/config unchanged
    removed, added = before["identity"] - after["identity"], after["identity"] - before["identity"]
    ck.chk("post_exactly_8_identity_function_acls_changed", len(removed) == 8 and len(added) == 8, f"-{len(removed)} +{len(added)}")
    b_by, a_by = {r[0]: r for r in before["identity"]}, {r[0]: r for r in after["identity"]}
    bad = []
    for sig, _ in IDENTITY_FUNCTIONS:
        b, a = b_by.get(sig), a_by.get(sig)
        if b is None or a is None or b[1:4] != a[1:4]:
            bad.append(sig)
            continue
        want = acl_set(b[4]) | {BUILDER_ITEM} if leg.name == "forward" else acl_set(b[4]) - {BUILDER_ITEM}
        if acl_set(a[4]) != want:
            bad.append(sig)
    ck.chk("post_each_identity_acl_changed_by_exactly_the_builder_item_and_nothing_else", not bad, bad)
    changed_bodies = []
    for sig, want_md5 in IDENTITY_BODY_MD5.items():
        cur.execute("SELECT md5(pg_get_functiondef(to_regprocedure(%s::text)))", ("public." + sig,))
        if cur.fetchone()[0] != want_md5:
            changed_bodies.append(sig)
    ck.chk("post_identity_function_bodies_unchanged", not changed_bodies, changed_bodies)
    gained = after["execute_pairs"] - before["execute_pairs"]
    lost = before["execute_pairs"] - after["execute_pairs"]
    pairs = {(BUILDER, "public." + s) for s, _ in IDENTITY_FUNCTIONS}
    pairs = {(r, f) for r, f in pairs}
    got_gained = {(r[0], r[1]) for r in gained}
    got_lost = {(r[0], r[1]) for r in lost}
    # regprocedure text omits the schema when public is on the search_path: normalise
    norm = lambda s: s if s.startswith("public.") else "public." + s
    got_gained, got_lost = {(r, norm(f)) for r, f in got_gained}, {(r, norm(f)) for r, f in got_lost}
    if leg.name == "forward":
        ck.chk("post_no_other_role_gains_execute_on_any_identity_function", got_gained == pairs and not got_lost, f"gained={sorted(got_gained - pairs)} lost={sorted(got_lost)}")
    else:
        ck.chk("post_no_other_role_loses_execute_on_any_identity_function", got_lost == pairs and not got_gained, f"gained={sorted(got_gained)} lost={sorted(got_lost - pairs)}")
    # LOW-2: membership is NOT compared here: inside the transaction the administrator holds the transient owner roles. The real comparison is
    # post_membership_equals_pre_state_after_revoke (a fresh query after the REVOKE, compared with the pre-state).
    for key in ("other_function_acl", "acl", "rls", "policy", "immutable_triggers"):
        ck.chk(f"post_{key}_identical", before[key] == after[key])
    cur.execute(f"SET LOCAL ROLE {OWNER_L2}")
    cur.execute("SELECT pg_get_functiondef(p.oid), pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,'') "
                "FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", (p.regproc,))
    new_def, owner, secdef, config, acl = cur.fetchone()
    ck.chk("post_bind_body_is_exactly_the_bound_body", new_def == leg.to_def and hashlib.md5(new_def.encode()).hexdigest() == leg.to_md5, hashlib.md5(new_def.encode()).hexdigest())
    if leg.name == "forward":
        ck.chk("post_bind_diff_is_exactly_the_planned_hunk", bp.diff_digest(plan["old_def"], new_def) == p.diff_sha256 and len(bp.unified_hunks(plan["old_def"], new_def)) == p.diff_hunks)
    else:
        ck.chk("post_bind_diff_is_exactly_the_planned_hunk", new_def == leg.to_def and plan["old_def"] == leg.from_def)
    ck.chk("post_bind_owner_secdef_config_acl_unchanged", (owner, secdef, config, acl_set(acl)) == (p.owner, p.secdef, p.config, acl_set(p.acl)), (owner, secdef, config, acl))
    cur.execute(f"SELECT count(*) FROM {FN_ATT} a JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature) "
                "WHERE a.function_signature=%s AND a.definition_digest=encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') "
                "AND a.owner_name=pg_get_userbyid(p.proowner) AND a.security_definer=p.prosecdef AND a.config IS NOT DISTINCT FROM p.proconfig", (p.signature,))
    ck.chk("post_bind_attestation_matches_live_function", cur.fetchone()[0] == 1)
    cur.execute(f"SELECT definition_digest FROM {FN_ATT} WHERE function_signature=%s", (p.signature,))
    ck.chk("post_bind_attestation_is_the_bound_digest", cur.fetchone()[0] == leg.to_sha)
    cur.execute("RESET ROLE")
    if leg.name == "forward":
        probe = plan["grant_probe"] or {}
        others = {r: ok for r, ok in probe.items() if r != BUILDER}
        ck.chk("post_grant_probe_builder_can_select", probe.get(BUILDER) is True, probe.get(BUILDER))
        owner_ok = probe.get(OWNER_L2) is True
        ck.chk("post_grant_probe_no_other_role_can_select", not [r for r, ok in others.items() if ok and r != OWNER_L2] and owner_ok,
               sorted(r for r, ok in others.items() if ok))


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=lambda s: sorted(s) if isinstance(s, (set, frozenset)) else str(s))


def render_report(leg: Leg, before: dict, after: dict, plan: dict, gate_before: dict, gate_after: dict, ck: Checks) -> list[str]:
    out = []
    names = {"function": "FUNCTION (signature, md5(def), owner, secdef, config, acl)", "function_attestation": "FUNCTION ATTESTATION ROW (signature, digest, owner, secdef, config)",
             "identity": "IDENTITY FUNCTION (signature, owner, secdef, config, acl)"}
    for key, title in names.items():
        removed, added = sorted(before[key] - after[key]), sorted(after[key] - before[key])
        want = 8 if key == "identity" else 1
        out.append(f"== {title}: exactly {len(removed)} removed / {len(added)} added ({'AS PLANNED' if (len(removed), len(added)) == (want, want) else 'UNEXPECTED'}) ==")
        for r in removed:
            out.append("  - " + " | ".join(r)[:400])
        for a in added:
            out.append("  + " + " | ".join(a)[:400])
    out.append("== FUNCTION BODY bind_l2_exact_inputs (unified diff of pg_get_functiondef, before -> after) ==")
    out.extend("  " + ln.rstrip("\n") for ln in difflib.unified_diff(plan["old_def"].splitlines(True), leg.to_def.splitlines(True), fromfile="before", tofile="after", n=0))
    for key in ("other_function_acl", "acl", "membership", "rls", "policy", "immutable_triggers"):
        out.append(f"== {key.upper()}: {'IDENTICAL' if before[key] == after[key] else 'CHANGED (UNEXPECTED)'} ({len(before[key])} entries) ==")
    gained = sorted(after["execute_pairs"] - before["execute_pairs"])
    lost = sorted(before["execute_pairs"] - after["execute_pairs"])
    out.append(f"== EXECUTE PAIRS (role, identity function), all roles: gained {len(gained)}, lost {len(lost)} ==")
    out.extend("  + " + " | ".join(g) for g in gained)
    out.extend("  - " + " | ".join(g) for g in lost)
    if plan.get("grant_probe") is not None:
        out.append("== GRANT-MECHANICS PROBE (temp table created as %s, granted to %s): roles able to SELECT: %s ==" % (OWNER_L2, BUILDER, sorted(r for r, ok in plan["grant_probe"].items() if ok)))
    out.append("== DEPLOY GATE, the gate's own queries as amjis_app, search_path = %s ==" % GATE_SEARCH_PATH)
    for tag, g in (("before", gate_before), ("after ", gate_after)):
        out.append(f"  {tag}: trigger_shape_unsafe={g['trigger_shape_unsafe']} trigger_surface_unsafe={g['trigger_surface_unsafe']} function_digests_unsafe={g['function_digests_unsafe']}")
    out.append(f"  bind function digest  stored {gate_after['function_digest_stored']} / gate {gate_after['function_digest_gate_side']}")
    out.append("commit conditions: " + ("ALL HOLD" if not ck.failed else f"FAILED {ck.failed}"))
    return out


# ------------------------------------------------------------------------------------------------------- runtime / outcome (D6 pattern)
RUNTIME_KEYS = ("python_executable", "python_version", "psycopg_version", "libpq_version")


def runtime_record() -> dict:
    return {"python_executable": sys.executable, "python_version": sys.version, "psycopg_version": psycopg.__version__, "libpq_version": psycopg.pq.version()}


def run_leg(conn, leg: Leg, mode: str, out, gate_tables=None, expect_evidence: str | None = None) -> dict:
    """One transaction. Returns {commit_ok, checks, evidence_digest, report, ...}; the caller commits or rolls back."""
    ck = Checks()
    cur = CountingCursor(conn.cursor())
    out(f"start (UTC): {utcnow()}")
    cur.execute(f"SET LOCAL search_path = {SEARCH_PATH}")
    cur.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")
    cur.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")
    cur.execute(SNAP_SQL["membership"])
    membership_before = {tuple(str(x) for x in row) for row in cur.fetchall()}
    transient = [r for r in (OWNER_L2, APP_OWNER) if not is_member(cur, r)]
    try:
        for r in transient:
            cur.execute(f"GRANT {r} TO CURRENT_USER")
    except psycopg.Error as exc:
        ck.chk("pre_admin_can_assume_the_owner_roles", False, f"GRANT failed: {type(exc).__name__}")
        out("REFUSED: the administrator cannot assume the owner roles (" + type(exc).__name__ + "); nothing was changed")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    preconditions(cur, leg, ck, out)
    try:
        gate_before = gate_mirror(cur, gate_tables)
    except psycopg.Error as exc:
        ck.chk("pre_deploy_gate_readable", False, f"the gate's own queries failed: {type(exc).__name__}")
        out("REFUSED: the deploy gate's own queries cannot run (" + type(exc).__name__ + "); nothing was changed")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    ck.chk("pre_deploy_gate_green", not gate_red(gate_before), f"already RED before the plan: {gate_red(gate_before)}")
    out("preconditions: " + ("OK" if not ck.failed else "REFUSED"))
    for name, ok, detail in ck.items:
        if not ok:
            out(f"  - {name}: {detail}")
    if mode == "count" or ck.failed:
        out(f"end (UTC): {utcnow()}")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    before = snap(cur)
    before["membership"] = membership_before
    plan = apply_leg(cur, leg)
    after = snap(cur)
    try:
        asserting_post_checks(cur, leg)
        ck.chk("post_asserting_privilege_checks_hold", True)
    except psycopg.Error as exc:
        ck.chk("post_asserting_privilege_checks_hold", False, str(exc).splitlines()[0])
        conn.rollback()
        out("ASSERTING post-check RAISED; the transaction was rolled back: " + str(exc).splitlines()[0])
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    check_after(cur, leg, before, after, plan, ck)
    gate_after = gate_mirror(cur, gate_tables)
    ck.chk("post_deploy_gate_green", not gate_red(gate_after), f"WOULD GO RED after commit: {gate_red(gate_after)}")
    ck.chk("post_gate_function_digest_equals_stored", gate_after["function_digest_stored"] == gate_after["function_digest_gate_side"] == leg.to_sha)
    for r in transient:
        cur.execute(f"REVOKE {r} FROM CURRENT_USER")
    cur.execute(SNAP_SQL["membership"])
    after["membership"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    ck.chk("post_membership_equals_pre_state_after_revoke", after["membership"] == membership_before)
    digest = hashlib.sha256(canonical({
        "leg": leg.name, "executor": exec_sha(), "runtime": runtime_record(), "before": before,
        "old_def_md5": hashlib.md5(plan["old_def"].encode()).hexdigest(), "checks": [(n, ok) for n, ok, _ in ck.items]}).encode()).hexdigest()
    if mode in ("apply", "rollback"):
        ck.chk("evidence_digest_matches_expected", expect_evidence == digest, f"expected {expect_evidence} got {digest}")
    report = render_report(leg, before, after, plan, gate_before, gate_after, ck)
    for line in report:
        out(line)
    out(f"end (UTC): {utcnow()}; statements: {cur.n}")
    return {"commit_ok": not ck.failed, "checks": ck, "evidence_digest": digest, "report": report,
            "digest_parts": {"before": before, "fn_before": {BIND_PATCH.signature: plan["old_def"]}}}


# -------------------------------------------------------------------------------------------------------------------- evidence
def resolve_evidence_root(flag=None, environ=None) -> str:
    environ = os.environ if environ is None else environ
    if TEST_EVIDENCE_ENV not in environ:
        return EVIDENCE_ROOT
    if PYTEST_ENV not in environ:
        sys.stderr.write(f"REFUSED: {TEST_EVIDENCE_ENV} is set outside a pytest run; it would redirect the evidence directory.\n")
        raise SystemExit(EXIT_TEST_ENV)
    root = flag or environ[TEST_EVIDENCE_ENV]
    if not root:
        sys.stderr.write(f"REFUSED: {TEST_EVIDENCE_ENV} is set but empty: refusing to fall back to the real evidence root.\n")
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
        d = rootp / f"{mode}_{ts}"
        d.mkdir(mode=0o700)            # NOT exist_ok: a collision aborts, never overwrites another run's evidence
        os.chmod(d, 0o700)
    except OSError as exc:
        raise EvidenceError(f"cannot create the evidence directory under {root} ({type(exc).__name__})")
    return d


def write_private(path: pathlib.Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


def write_evidence(run_dir: pathlib.Path, res: dict, result: dict) -> None:
    try:
        parts = res.get("digest_parts") or {}
        if parts:
            for sig, text in parts["fn_before"].items():
                write_private(run_dir / ("fn_before_" + sig.split("(")[0] + ".sql"), text)
            write_private(run_dir / "before_state.json", canonical(parts["before"]) + "\n")
        write_private(run_dir / "report.txt", "\n".join(res.get("report") or []) + "\n")
        write_private(run_dir / "result.json", json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    except OSError:
        result.setdefault("warnings", []).append("evidence files could not be fully written")


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
    """executor_standards.outcome_guard whose own file write can never mask the real result, with a committed flag (after COMMIT an interruption records
    `applied` with a warning, never `failed`) and a commit_state_unknown record when conn.commit() itself raised."""
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
                self._warn("WARNING: COMMIT STATE UNKNOWN (%s raised by commit()): the change may or may not be committed. outcome.json records "
                           "commit_state_unknown. CHECK THE DATABASE before doing anything else.\n" % self.commit_unknown)
                return False
            if self.committed and not self.done:
                why = re.sub(r"[^A-Za-z0-9_.:\-]", "_", exc_type.__name__ if exc_type is not None else "outcome_not_declared")[:40]
                self._write("applied", self.commit_digest, (), ["outcome_write_failed_after_commit:" + why])
                self._warn("WARNING: THE COMMIT HAPPENED but the run was interrupted (%s) before outcome.json was recorded; recorded applied with a warning. "
                           "Verify in the database.\n" % why)
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
        result.setdefault("warnings", []).append("outcome.json could not be written (%s)%s" % (o.write_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    else:
        result["outcome_file"] = o.path
        if o.interpreter_record_error:
            result.setdefault("warnings", []).append("outcome.json written without the interpreter record (%s)%s"
                                                     % (o.interpreter_record_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    return result


def refuse(o, check: str, message: str):
    o.fail([check])
    raise SystemExit("REFUSED: " + message)


def refuse_interpreter(o, check: str, message: str):
    """Distinct from every other refusal and from every gate code: exit EXIT_INTERPRETER (92), its own check name in outcome.json, before any connection."""
    o.fail([check])
    o._warn("REFUSED (interpreter): " + message + "\n")
    raise SystemExit(EXIT_INTERPRETER)


def interpreter_precheck(o, evidence_root, expect_evidence: str, log: list) -> None:
    """--apply / --rollback, BEFORE the credential is fetched: compare the runtime recorded by the dry run(s) with this process (exit 92 on any difference or
    on a record missing a field); with no dry-run evidence under this root the evidence digest itself binds the interpreter."""
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
        log.append(f"interpreter check: no dry-run evidence for this digest under {evidence_root}; the evidence digest itself binds the interpreter")
        return
    for name, body in matches:
        missing = [k for k in RUNTIME_KEYS if body.get(k) in (None, "")]
        if missing:
            refuse_interpreter(o, "dry_run_evidence_lacks_interpreter_record", f"cannot compare: the dry run {name} recorded no {', '.join(missing)}; repeat the dry run with this executor")
        differs = [k for k in RUNTIME_KEYS if body[k] != now[k]]
        if differs:
            refuse_interpreter(o, "interpreter_differs_from_dry_run", f"the dry run {name} used a different interpreter or driver ("
                               + "; ".join(f"{k}: dry run {body[k]!r}, now {now[k]!r}" for k in differs)
                               + "): run the apply with the SAME interpreter, or repeat the dry run under this one")
    log.append(f"interpreter check: {len(matches)} dry run(s) with this digest used the same interpreter, psycopg and libpq")


_HELD_SIGNALS = {signal.SIGTERM, signal.SIGHUP, signal.SIGINT}


def _on_terminate(signum, frame):
    raise SystemExit(128 + signum)


def install_signal_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _on_terminate)


def refuse_target(o, facts: list[str]):
    """LOW-1: distinct exit code, own check name in outcome.json, before anything else touches the database."""
    o.fail(["connected_to_the_wrong_target"])
    o._warn("REFUSED (target): the connection is not the expected administrator on the expected database/server: " + " | ".join(facts) + "\n")
    raise SystemExit(EXIT_WRONG_TARGET)


def execute(args, connect, now=None, gate_fp=None, gate_tables=None, target=None):
    """Returns (exit_code, result). `connect` is the only door to a database and is called ONLY after the plan hash matched. `target` defaults to the production
    administrator/database/major version; only tests pass another (there is no environment or command-line route)."""
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
            refuse(o, "args_expect_evidence_missing", f"--{args.mode} requires --expect-evidence <digest from the matching dry run>")
        try:
            leg = rollback_leg() if args.mode.startswith("rollback") else forward_leg()
        except ExpectedDiffError as exc:
            refuse(o, "expected_diff_mismatch", f"the patched body is not the bound EXPECTED_DIFF body ({str(exc)[:160]})")
        lines: list[str] = []
        if args.mode in ("apply", "rollback"):
            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)
        conn = connect()                         # the administrator credential is fetched here, never earlier
        try:
            target_ok, target_facts = check_target(conn, target or PRODUCTION_TARGET)
            lines.extend(target_facts)
            if not target_ok:
                refuse_target(o, target_facts)
            try:
                res = run_leg(conn, leg, args.mode if args.mode != "rollback-dry-run" else "dry-run", lines.append, gate_tables, args.expect_evidence)
            except Exception:
                conn.rollback()
                raise
            ck, digest = res["checks"], res["evidence_digest"]
            result = {"plan_hash": phash, "executor_sha256": sha, "mode": args.mode, "evidence_digest": digest, "failed_checks": ck.failed,
                      "checks": {n: ok for n, ok, _ in ck.items}, "runtime": runtime_record(),
                      "details": {n: d for n, ok, d in ck.items if d and not ok}, "log": lines, "evidence_dir": str(run_dir)}
            if args.mode in ("apply", "rollback") and res["commit_ok"]:
                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)
                try:
                    try:
                        conn.commit()
                    except BaseException as exc:
                        o.mark_commit_unknown(digest, type(exc).__name__)
                        if isinstance(exc, Exception):
                            raise CommitStateUnknown(type(exc).__name__) from exc    # NIT-3: its own exit code in main()
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
                return 1, conclude(o, result, "failed", digest, ck.failed)
            good = res["commit_ok"] if args.mode != "count" else not ck.failed
            result["status"] = ("COUNT_READ_ONLY_OK" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD") if good else \
                ("COUNT_REFUSED" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_REFUSED")
            write_evidence(run_dir, res, result)
            if good:
                return 0, conclude(o, result, "dry_run", digest)
            return 2, conclude(o, result, "failed", digest, ck.failed)
        finally:
            conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    for m in MODES:
        g.add_argument("--" + m, action="store_const", const=m, dest="mode")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    p.add_argument("--evidence-root", default=None, help=f"ignored unless {TEST_EVIDENCE_ENV} is set (tests only)")
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if not a.expect_plan:
        p.error("every mode requires --expect-plan <sha256> (the credential is fetched only for a named plan hash)")
    if a.mode in ("apply", "rollback") and not a.expect_evidence:
        p.error(f"--{a.mode} requires --expect-evidence <digest printed by the matching dry run>")
    return a


def refuse_under_test_outside_pytest(gate_fp, environ=None):
    environ = os.environ if environ is None else environ
    if gate_fp.get("under_test") and PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: the launch marker says the gate ran under test (GATE_V2_UNDER_TEST=1): the executor does not run against a database from such a "
                         "launch outside a pytest run. Start it through run_gated.sh without the test flag.\n")
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
    except CommitStateUnknown as exc:
        print("COMMIT STATE UNKNOWN (%s raised by commit()): the change may or may not be committed; outcome.json records commit_state_unknown. "
              "CHECK THE DATABASE before doing anything else." % exc.exc_name)
        return EXIT_COMMIT_UNKNOWN
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
