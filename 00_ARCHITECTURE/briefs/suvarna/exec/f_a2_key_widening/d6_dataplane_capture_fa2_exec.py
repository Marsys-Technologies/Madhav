#!/usr/bin/env python3
"""COMBINED D6 owner-path executor (DRAFT, NEVER RUN against any real system, NEVER APPLIED):

  (1) F-A2: widen the chart_divisionals natural key (unique index + capture trigger arguments + the one ga_vargas dependency-identity
      hunk of the capture function) to include fact_subject          [d6_f_a2_key_widening_DRAFT.py, imported];
  (2) PATCH A: CREATE OR REPLACE public.l1_data_plane_capture_row() so a chart_facts row that carries no typed value is recorded
      honestly, and a row that carries more than one typed value keeps ONE (precedence num, text, jsonb) with a companion marker
      [d6_capture_patch_a.py, imported];
  (3) COMMENT ON the two L1 snapshot tables and five columns, stating the contract (row_snapshots is the complete record;
      fact_snapshots keeps one typed value by the precedence rule);
  (4) re-attestation of exactly two rows: the capture FUNCTION row and the capture TRIGGER row (immutability triggers disabled and
      re-enabled around each UPDATE, in the same transaction).
  and the exact inverse (--rollback), rehearsed in the tests on a disposable database.

All of it is ONE transaction as data_plane_l1_owner (transient GRANT / SET LOCAL ROLE, as in the I-11 and F-A2 executors); COMMIT only
if every check holds. The live function body is compared BYTE-FOR-BYTE with the shipped pre-state (md5 1e079261aa42eb97a1885a48035e7520,
read from the live catalog as suvarna_reader on 2026-10-02) and the patched body is constrained to differ from it ONLY by the hunks
named in EXPECTED_DIFF (patch A: H1, H2, H3a, H3b; F-A2: one hunk, two diff sites): the md5 and sha256 of the patched body and the sha256
of the zero-context diff are bound in the plan hash and re-checked against the database after the CREATE OR REPLACE.

MODES (every mode needs --expect-plan: the in-process administrator credential is fetched only for a plan hash the operator names)
  --count                            read-only: preconditions + pre-state, always ROLLBACK
  --dry-run [--writer-commit S]      apply everything, print the exact catalog diff, run every commit condition, ROLLBACK
  --apply --expect-plan H --expect-evidence D --writer-commit S
                                     same transaction; COMMIT only if every check holds and D equals this run's evidence digest
  --rollback-dry-run                 the inverse, applied then rolled back
  --rollback --expect-plan H --expect-evidence D
                                     the inverse, committed: re-apply the live definition, 6-column index and trigger, old comments,
                                     re-attest => md5 and attestation rows back to the pre-state (refused if widened rows exist)

LAUNCH (GATE_V2). Never started directly: `exec/gate_v2/run_gated.sh python3 d6_dataplane_capture_fa2_exec.py <args>`. main() calls
launch_gate() FIRST and refuses (exit 93) without a verifying GATE_V2_LAUNCH marker, or while GATE_PINS is TBD. THE THREE GATE SHAS
BELOW ARE A MARKED TBD: the gate files (exec/gate_v2/, PR #2938) are being revised (revision 3) and are not yet bound, so every plan hash
printed by this version is PROVISIONAL BY DESIGN and tests/test_gate_pins_bound fails until the pins are bound and the hash re-frozen.

outcome.json (status dry_run | applied | failed | commit_state_unknown) is written into the run's evidence directory in every mode
(executor_standards.outcome_guard); commit_state_unknown means conn.commit() itself raised (the server MAY have committed: check the database first).
An under_test launch marker is refused (exit 93) in every mode outside pytest. A MISSING outcome.json means check the database. The administrator password is fetched from Secret Manager inside this process ONLY after the
plan hash matched, never printed or saved; tests inject a disposable connection and never reach connect_admin().
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

import psycopg

HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod            # dataclasses (postponed annotations) resolve their module through sys.modules
    spec.loader.exec_module(mod)
    return mod


fa2 = _load("d6_fa2_key_widening_draft", HERE / "d6_f_a2_key_widening_DRAFT.py")
pa = _load("d6_capture_patch_a", HERE / "d6_capture_patch_a.py")

PROJECT = "madhav-astrology"
OWNER = fa2.OWNER
APP_OWNER = fa2.APP_OWNER
TABLE = fa2.TABLE
INDEX = fa2.INDEX
TRIGGER = fa2.TRIGGER
NEW_INDEX_TMP = fa2.NEW_INDEX_TMP
OLD_COLS = fa2.OLD_COLS
NEW_COLS = fa2.NEW_COLS
CAPTURE_FN = fa2.CAPTURE_FN
CAPTURE_FN_SIG = fa2.CAPTURE_FN_SIG
TRG_ATT, TRG_ATT_IMMUTABLE = fa2.TRG_ATT, fa2.TRG_ATT_IMMUTABLE
FN_ATT, FN_ATT_IMMUTABLE = fa2.FN_ATT, fa2.FN_ATT_IMMUTABLE
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/DataPlaneCaptureFA2"
LIVE_DEFS = HERE / "live_defs"

# ---------------------------------------------------------------------------------------------------- bound pre/post state
# DATA-DRIVEN: one FunctionPatch per function this plan replaces. Adding a function or a hunk is adding data here (and one
# live_defs/<name>.LIVE.sql file, the pg_get_functiondef text of the live function): every precondition, apply step, commit
# condition, the rollback and EXPECTED_DIFF are GENERATED from FUNCTION_PATCHES. The numbers below were read live as suvarna_reader on
# 2026-10-02 (PostgreSQL 15.18, database amjis): md5(pg_get_functiondef) and its length, owner / SECURITY DEFINER / proconfig / ACL, and the
# function attestation digest (= sha256 of the same text).


@dataclasses.dataclass(frozen=True)
class FunctionPatch:
    signature: str            # as in l1_data_plane_function_attestations.function_signature
    live_md5: str
    live_len: int
    live_sha256: str
    owner: str
    secdef: bool
    config: str               # proconfig::text
    acl: str                  # proacl::text
    hunks: tuple              # ((name, old, new), ...): each old text must occur EXACTLY ONCE in the live definition
    patched_md5: str          # deterministic consequences of the hunks (bound; re-proved by the tests on PostgreSQL 15 and 17)
    patched_sha256: str
    diff_sha256: str          # sha256 of the zero-context unified diff live -> patched
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
        """The shipped hunks applied to the shipped live definition, constrained to the EXPECTED_DIFF before any database work."""
        live = self.live_def()
        try:
            new = pa.apply_hunks(live, self.hunks)
        except ValueError as exc:
            raise ExpectedDiffError(f"{self.short}: {exc}")
        got = (hashlib.md5(new.encode()).hexdigest(), hashlib.sha256(new.encode()).hexdigest(), pa.diff_digest(live, new),
               len(pa.unified_hunks(live, new)))
        want = (self.patched_md5, self.patched_sha256, self.diff_sha256, self.diff_hunks)
        if got != want:
            raise ExpectedDiffError(f"{self.short}: the patched body differs from the EXPECTED_DIFF (md5/sha256/diff sha256/hunks) {got} != {want}")
        return new


class ExpectedDiffError(Exception):
    """The shipped hunks do not produce the bound patched body: nothing may run."""


LIVE_TRG_DIGEST = "d0064f5ed31f7db91cb239967f783af3a885f21b39aa7c833877989a713768b0"   # the capture-trigger attestation row (default path)
PATCHED_TRG_DIGEST = "ea1281cfcd1d2250e3a073dbb070a566da18cab1431a0547f6c10583a4f5fe83"  # the same trigger with the 7th argument

FA2_HUNK = ("F_A2_dependency_identity_fact_subject", fa2.HUNK_OLD_KEY, fa2.HUNK_NEW_KEY)
CAPTURE_PATCH = FunctionPatch(
    signature=CAPTURE_FN_SIG,
    live_md5="1e079261aa42eb97a1885a48035e7520", live_len=19780,
    live_sha256="0f8f42b6c93a9a5d2d25333cc2bd3cf52aed60e7cb7d51a87979ede92e74b9b8",
    owner=OWNER, secdef=True, config='{"search_path=pg_catalog, public, pg_temp"}', acl="{data_plane_l1_owner=X/data_plane_l1_owner}",
    # patch A: H1, H2, H3a, H3b (4 sites) + the F-A2 dependency-identity hunk (2 diff sites: the key line and the ORDER BY line)
    hunks=tuple(pa.PATCH_A_HUNKS) + (FA2_HUNK,),
    patched_md5="b2f4242f034d1a3983edb08c625dc353",
    patched_sha256="d65a6804508e964e0e92b6a507a12fc747aa69bb0f2bc34170c721e281d0728d",
    diff_sha256="bca80fe61b88a0fcb2d2721c542a25893a4bc8cb77d0d094be31b4324056553f", diff_hunks=6)
FUNCTION_PATCHES = (CAPTURE_PATCH,)
assert len({p.signature for p in FUNCTION_PATCHES}) == len(FUNCTION_PATCHES) and CAPTURE_FN_SIG in {p.signature for p in FUNCTION_PATCHES}
assert all(p.owner == OWNER for p in FUNCTION_PATCHES), "an L2-owned function needs its own owner-role leg and attestation table: not supported"
ALL_HUNKS = tuple(h for p in FUNCTION_PATCHES for h in p.hunks)

# ------------------------------------------------------------------------------------------------------------ the contract
ROW_T, FACT_T = "l1_data_plane_row_snapshots", "l1_data_plane_fact_snapshots"
COMMENT_OLD_TABLES = {
    ROW_T: "Append-only exact L1 producer rows. Active-table replacement never deletes a prior compatible generation.",
    FACT_T: "Append-only typed field facts decomposed from each runtime producer row, preserving unit, zero, null and reason.",
}
COMMENT_NEW_TABLES = {
    ROW_T: COMMENT_OLD_TABLES[ROW_T] + " COMPLETE RECORD: source_row_jsonb holds every column of the producer row exactly as written, "
           "including every typed value column; l1_data_plane_fact_snapshots is a projection of it.",
    FACT_T: COMMENT_OLD_TABLES[FACT_T] + " ONE TYPED VALUE per fact: a chart_facts row may carry fact_value_num, fact_value_text and "
            "fact_value_jsonb together, but this table keeps exactly ONE of them by the fixed precedence num, then text, then jsonb "
            "(value_num, value_text, value_jsonb: the others are NULL). When a column was dropped, grain_jsonb records "
            "typed_value_column (the kept column) and companion_value_columns (the dropped ones); when nothing was dropped neither key "
            "is present. The complete row, every column, is in l1_data_plane_row_snapshots.source_row_jsonb. A row with no typed value "
            "at all is recorded as missingness floored (producer status floored) or unavailable, never present.",
}
COMMENT_NEW_COLUMNS = {
    (ROW_T, "source_row_jsonb"): "The COMPLETE producer row, every column as written (all typed value columns included). The record of truth; "
                                 "l1_data_plane_fact_snapshots keeps one typed value per fact.",
    (FACT_T, "grain_jsonb"): "Fact grain. When the producer row carried more than one typed value, also typed_value_column (the kept column) and "
                             "companion_value_columns (the dropped ones, precedence num, text, jsonb); absent when nothing was dropped. "
                             "The dropped values are in l1_data_plane_row_snapshots.source_row_jsonb.",
    (FACT_T, "value_num"): "Typed value, precedence 1 (num, then text, then jsonb). NULL when another column was kept; see grain_jsonb.",
    (FACT_T, "value_text"): "Typed value, precedence 2. Kept only when value_num is NULL; see grain_jsonb.",
    (FACT_T, "value_jsonb"): "Typed value, precedence 3. Kept only when value_num and value_text are NULL; see grain_jsonb.",
}
COMMENTS_OLD = {(t, "", d) for t, d in COMMENT_OLD_TABLES.items()}
COMMENTS_NEW = {(t, "", d) for t, d in COMMENT_NEW_TABLES.items()} | {(t, c, d) for (t, c), d in COMMENT_NEW_COLUMNS.items()}

def _expected_functions() -> list[dict]:
    return [{
        "function": p.signature, "live_md5": p.live_md5, "patched_md5": p.patched_md5, "live_sha256": p.live_sha256,
        "patched_sha256": p.patched_sha256, "differs_ONLY_by_hunks": [h[0] for h in p.hunks], "zero_context_diff_hunks": p.diff_hunks,
        "zero_context_diff_sha256": p.diff_sha256,
        "owner_security_definer_config_acl": f"unchanged: {p.owner} / SECURITY DEFINER={p.secdef} / {p.config} / {p.acl}",
        "attestation": f"{p.signature}|digest {p.live_sha256} -> {p.patched_sha256}|owner/secdef/config unchanged|ONE row",
    } for p in FUNCTION_PATCHES]


EXPECTED_DIFF = {
    "functions": _expected_functions(),
    "index": [f"{TABLE}|{INDEX}|6col->7col (+fact_subject, NULLS NOT DISTINCT)"],
    "trigger": [f"{TABLE}|{TRIGGER}|args 6->7 (+'fact_subject')"],
    "trigger_attestation": [f"{TABLE}|{TRIGGER}|digest {LIVE_TRG_DIGEST} -> {PATCHED_TRG_DIGEST}|ONE row"],
    "comments": "removed 2 (the 1035 table comments) / added 7 (2 table comments + 5 column comments)",
    "unchanged": ["every other index, trigger, l1_/l2_ function, attestation row", "ACL", "membership", "RLS", "policy",
                  "per-chart row data of chart_divisionals", "append-only (immutable) triggers: all enabled before and after"],
    "identity_probe": fa2.EXPECTED_DIFF["identity_probe"],
    "deploy_gate": fa2.EXPECTED_DIFF["deploy_gate"],
    "writer_first": fa2.EXPECTED_DIFF["writer_first"],
    "rollback": "the exact inverse (live definition re-applied, 6-column index, 6-argument trigger, 1035 comments, two re-attestations): "
                "md5 and attestation rows equal the pre-state; refused if widened rows exist",
}

# ------------------------------------------------------------------------------------------------------ gate wiring (GATE_V2)
GATE_TBD = "TBD_BIND_AT_GATE_REVISION_3"
# TBD: the gate files at exec/gate_v2/ (PR #2938) are being revised (revision 3). Bind the three sha256 here, re-freeze the plan hash.
GATE_PINS = {"prerun_gate.py": GATE_TBD, "run_gated.sh": GATE_TBD, "executor_standards.py": GATE_TBD}
# PROPOSED, NOT BOUND: the sha256 of the gate files at PR #2938 head 7f0db55c3 (Gate v2 revision 3), as handed to this lane. They are NOT in force: only Strategic
# Suvarna binds the pins (by replacing the TBD values above after reviewing the files). tests/gate_fixture holds byte-identical copies of exactly these
# files and a test proves it, so the whole suite runs against the revision-3 gate; the plan prints the hash the plan WOULD have if these were bound as they are.
GATE_REV3_PROPOSED = {"prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
                      "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
                      "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
GATE_DIR_ENV = "DPFA2_TEST_GATE_DIR"
TEST_EVIDENCE_ENV = "DPFA2_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = 93
EXIT_TEST_ENV = 95
MODES = ("count", "dry-run", "apply", "rollback-dry-run", "rollback")


def gate_dir(environ=None) -> pathlib.Path:
    """exec/gate_v2 next to this folder. DPFA2_TEST_GATE_DIR (tests only) is REFUSED, exit 95, outside a pytest run."""
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
    """FIRST thing main() does. Refuses (exit 93) unless the gate pins are bound AND executor_standards.py equals its pin AND a verifying
    GATE_V2_LAUNCH marker (set by run_gated.sh after a passing gate; shas equal the live gate files and the pins) is present."""
    environ = os.environ if environ is None else environ
    try:
        es = standards(environ)
    except FileNotFoundError:
        sys.stderr.write(f"REFUSED: the GATE_V2 files are not at {gate_dir(environ)} (exec/gate_v2, PR #2938): this executor cannot be launched.\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    if any(v == GATE_TBD for v in GATE_PINS.values()):
        sys.stderr.write("REFUSED: the GATE_V2 pins in this executor are TBD (gate revision 3 not yet bound): the plan hash is PROVISIONAL "
                         "and this executor cannot run.\n")
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


def lit(text: str) -> str:
    assert "\\" not in text and "\x00" not in text, text
    return "'" + text.replace("'", "''") + "'"


def comment_sql(tables: dict, columns: dict | None) -> list[str]:
    out = [f"COMMENT ON TABLE public.{t} IS {lit(d)}" for t, d in tables.items()]
    for (t, c), d in (columns if columns is not None else {}).items():
        out.append(f"COMMENT ON COLUMN public.{t}.{c} IS {lit(d)}")
    return out


def comment_null_sql() -> list[str]:
    return [f"COMMENT ON COLUMN public.{t}.{c} IS NULL" for (t, c) in COMMENT_NEW_COLUMNS]


@dataclasses.dataclass(frozen=True)
class FnStep:
    patch: FunctionPatch
    from_def: str
    to_def: str
    from_md5: str
    to_md5: str
    from_sha: str
    to_sha: str


@dataclasses.dataclass(frozen=True)
class Leg:
    name: str                       # forward | rollback
    functions: tuple                # FnStep, one per FunctionPatch
    from_trg: str
    to_trg: str
    from_cols: tuple
    to_cols: tuple
    comments_from: frozenset
    comments_to: frozenset
    comment_stmts: tuple
    removed_comments: int
    added_comments: int


def forward_leg() -> Leg:
    steps = tuple(FnStep(p, p.live_def(), p.patched_def(), p.live_md5, p.patched_md5, p.live_sha256, p.patched_sha256)
                  for p in FUNCTION_PATCHES)
    return Leg("forward", steps, LIVE_TRG_DIGEST, PATCHED_TRG_DIGEST, OLD_COLS, NEW_COLS, frozenset(COMMENTS_OLD), frozenset(COMMENTS_NEW),
               tuple(comment_sql(COMMENT_NEW_TABLES, COMMENT_NEW_COLUMNS)), len(COMMENTS_OLD), len(COMMENTS_NEW))


def rollback_leg() -> Leg:
    steps = tuple(FnStep(p, p.patched_def(), p.live_def(), p.patched_md5, p.live_md5, p.patched_sha256, p.live_sha256)
                  for p in FUNCTION_PATCHES)
    return Leg("rollback", steps, PATCHED_TRG_DIGEST, LIVE_TRG_DIGEST, NEW_COLS, OLD_COLS, frozenset(COMMENTS_NEW), frozenset(COMMENTS_OLD),
               tuple(comment_sql(COMMENT_OLD_TABLES, None) + comment_null_sql()), len(COMMENTS_NEW), len(COMMENTS_OLD))


def trigger_create_sql(cols) -> str:
    args = ", ".join("'%s'" % c for c in cols)
    return (f"CREATE TRIGGER {TRIGGER} AFTER INSERT OR UPDATE ON public.{TABLE} FOR EACH ROW "
            f"EXECUTE FUNCTION {CAPTURE_FN.split('(')[0]}({args})")


def fn_att_update_sql(sig: str) -> str:
    return (f"UPDATE {FN_ATT} a SET definition_digest = encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') FROM pg_proc p "
            f"WHERE a.function_signature='{sig}' AND p.oid=to_regprocedure('public.'||a.function_signature)")


def render_plan(sha: str | None = None, pins: dict | None = None) -> str:
    sha = sha or exec_sha()
    pins = pins or GATE_PINS
    fwd = forward_leg()
    names = ", ".join(p.signature for p in FUNCTION_PATCHES)
    lines = [
        "-- COMBINED D6 plan (data-driven): F-A2 key widening of public.chart_divisionals + function patches [" + names + "] + contract comments + re-attestation (and the exact inverse)",
        "-- one transaction as data_plane_l1_owner (transient GRANT <role> TO CURRENT_USER only if not a member, SET LOCAL ROLE, REVOKE only what was granted)",
        f"SET LOCAL search_path = {fa2.SEARCH_PATH}",
        "SET LOCAL lock_timeout = '5s'",
        "SET LOCAL statement_timeout = '120s'",
        "-- FORWARD (--dry-run / --apply), as data_plane_l1_owner unless noted:",
        f"-- preconditions (read only; any failure = refuse + ROLLBACK): no build_runs planned/running/paused on ANY chart (as {APP_OWNER}); no L1 generation 'building'; "
        "no data_plane_builder session active/idle-in-transaction; public.digest(text,text) resolves; the six-column index and six-argument trigger; the capture-trigger attestation "
        f"row EXISTS exactly once with digest {LIVE_TRG_DIGEST}; the two table comments are the 1035 text and no column comment exists; the deploy gate's own three queries are green "
        "(as amjis_app, search_path public); --writer-commit: image tag == commit and ga_vargas digest == the frozen one; and for EVERY patched function:",
    ]
    for p in FUNCTION_PATCHES:
        lines.append(f"--   {p.signature}: EXISTS, owner {p.owner}, SECURITY DEFINER {p.secdef}, proconfig {p.config}, ACL {p.acl}; pg_get_functiondef equals BYTE-FOR-BYTE the shipped "
                     f"pre-state (md5 {p.live_md5}, {p.live_len} chars, live_defs/{p.short}.LIVE.sql); its attestation row EXISTS exactly once with digest {p.live_sha256}")
    n = 0
    for p in FUNCTION_PATCHES:
        n += 1
        lines.append(f"-- {n}. CREATE OR REPLACE FUNCTION public.{p.signature} with the live definition plus exactly these hunks:")
        for name, old, new in p.hunks:
            lines.append(f"--   hunk {name}:")
            lines.append("--     - " + old.replace("\n", "\n--       "))
            lines.append("--     + " + new.replace("\n", "\n--       "))
        lines.append(f"--   bound: patched md5 {p.patched_md5}, sha256 {p.patched_sha256}; zero-context diff {p.diff_hunks} hunks, sha256 {p.diff_sha256}; "
                     "re-checked against pg_get_functiondef after the statement")
    lines.append("-- contract comments (owner path):")
    lines += ["   " + x for x in fwd.comment_stmts]
    lines.append("-- re-attest each patched function row (immutability trigger off, then on, same transaction; rowcount must be 1):")
    for p in FUNCTION_PATCHES:
        lines += [f"ALTER TABLE {FN_ATT} DISABLE TRIGGER {FN_ATT_IMMUTABLE}", fn_att_update_sql(p.signature), f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}"]
    lines += [
        "-- F-A2 index + trigger (the ACCESS EXCLUSIVE window starts at DROP INDEX; functions, comments, function attestations and the identity-probe inserts run BEFORE it):",
        f"CREATE UNIQUE INDEX {NEW_INDEX_TMP} ON public.{TABLE} ({', '.join(NEW_COLS)}) NULLS NOT DISTINCT",
        f"DROP INDEX public.{INDEX}",
        f"ALTER INDEX public.{NEW_INDEX_TMP} RENAME TO {INDEX}",
        f"DROP TRIGGER {TRIGGER} ON public.{TABLE}",
        trigger_create_sql(NEW_COLS),
        "-- re-attest the capture-trigger row (immutability trigger off, then on; rowcount must be 1):",
        f"ALTER TABLE {TRG_ATT} DISABLE TRIGGER {TRG_ATT_IMMUTABLE}",
        f"UPDATE {TRG_ATT} a SET definition_digest = encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE a.table_name='{TABLE}' AND a.trigger_name='{TRIGGER}' AND c.relname=a.table_name AND t.tgname=a.trigger_name",
        f"ALTER TABLE {TRG_ATT} ENABLE TRIGGER {TRG_ATT_IMMUTABLE}",
        "-- commit only if ALL hold (EXPECTED_DIFF): across a before/after snapshot of every public index, trigger, l1_/l2_ and lifecycle function, both attestation tables and the "
        f"table/column comments of the two snapshot tables, exactly ONE entry changed in each of index, trigger, trigger attestation and EXACTLY {len(FUNCTION_PATCHES)} in function and function attestation "
        "(the patched signatures), comments removed 2 / added 7; ACL, membership, RLS, policy, per-chart row data, every append-only trigger state identical; for each patched function "
        "pg_get_functiondef after == the patched body (md5 as bound) and its diff from the before body has the bound sha256 and hunk count; owner/secdef/config/ACL unchanged; the new index is unique, "
        "valid, NULLS NOT DISTINCT on the 7 columns; every attestation row equals the live object under the gate's own join and equals the bound digest; the gate's three queries "
        "are false AFTER the plan under search_path public and stored == gate-side digests; identity probe 84 landed / 84 distinct identities (legacy 6 args: 18); transient grants "
        "revoked and membership equals the pre-state; --expect-plan == plan hash; --expect-evidence == this run's evidence digest (apply).",
        "-- ROLLBACK (--rollback-dry-run / --rollback), the exact inverse, as data_plane_l1_owner (generic: every function re-applied from its shipped live definition and re-attested):",
        f"-- preconditions: each function md5 == its patched md5 and its attestation == its patched sha256; 7-column index; 7-argument trigger with attestation {PATCHED_TRG_DIGEST}; the patched comments; "
        "NO two chart_divisionals rows share the six-column key (a rebuild that landed widened rows makes the old index impossible: delete them first); no build in flight; gate green",
        "-- CREATE OR REPLACE FUNCTION from each shipped live definition; the 1035 table comments restored and the five column comments set to NULL; 6-column index (create tmp, drop, rename); "
        f"6-argument trigger; re-attest every function row and the trigger row; commit conditions mirror the forward ones with the live constants (trigger digest {LIVE_TRG_DIGEST}).",
        "-- the real run is started ONLY through exec/gate_v2/run_gated.sh <python3> <this file> <args> (GATE_V2): the executor REFUSES (exit 93) unless the marker verifies against "
        "the gate files pinned below; it writes outcome.json (dry_run | applied | failed | commit_state_unknown) in every mode; it refuses an under_test launch marker (exit 93) and a DPFA2_TEST_* variable (exit 95) outside pytest.",
        "-- every mode needs --expect-plan: the in-process administrator credential is fetched only after the plan hash matched.",
        "-- gate files (exec/gate_v2, PR #2938; %s): prerun_gate.py sha256 %s; run_gated.sh sha256 %s; executor_standards.py sha256 %s"
        % ("PINS ARE TBD, plan hash PROVISIONAL" if any(v == GATE_TBD for v in pins.values()) else "pins BOUND by Strategic Suvarna",
           pins["prerun_gate.py"], pins["run_gated.sh"], pins["executor_standards.py"]),
        "-- gate revision 3 PROPOSED, NOT BOUND (PR #2938 head 7f0db55c3): prerun_gate.py sha256 %s; run_gated.sh sha256 %s; executor_standards.py sha256 %s"
        % (GATE_REV3_PROPOSED["prerun_gate.py"], GATE_REV3_PROPOSED["run_gated.sh"], GATE_REV3_PROPOSED["executor_standards.py"]),
        "-- plan hash = bind_gate_into_plan_hash(sha256(plan text + \"\\n\" + json(EXPECTED_DIFF)), prerun_gate.py pin, run_gated.sh pin)",
        "-- F-A2 module: d6_f_a2_key_widening_DRAFT.py sha256 %s" % sha_file(HERE / "d6_f_a2_key_widening_DRAFT.py"),
        "-- patch A module: d6_capture_patch_a.py sha256 %s" % sha_file(HERE / "d6_capture_patch_a.py"),
    ]
    for p in FUNCTION_PATCHES:
        lines.append(f"-- live definition: live_defs/{p.short}.LIVE.sql sha256 %s" % sha_file(p.live_file))
    lines.append("-- executor: d6_dataplane_capture_fa2_exec.py sha256 %s" % sha)
    return "\n".join(lines)


def plan_hash_unbound(sha: str | None = None, pins: dict | None = None) -> str:
    text = render_plan(sha, pins)
    return hashlib.sha256((text + "\n" + json.dumps(EXPECTED_DIFF, sort_keys=True)).encode()).hexdigest()


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
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


SNAP_SQL = dict(fa2.SNAP_SQL)
_LIFECYCLE = ", ".join("'%s'" % n for n in fa2.GATE_LIFECYCLE_FUNCTIONS)
SNAP_SQL["function"] = ("SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)), pg_get_userbyid(p.proowner), "
                        "p.prosecdef::text, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,'') FROM pg_proc p "
                        "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' "
                        "AND (p.proname LIKE 'l1\\_data\\_plane\\_%' OR p.proname LIKE 'l2\\_data\\_plane\\_%' "
                        f"OR p.proname IN ({_LIFECYCLE})) ORDER BY 1")
SNAP_SQL["comment"] = (
    "SELECT c.relname, COALESCE(a.attname,''), d.description FROM pg_description d "
    "JOIN pg_class c ON c.oid=d.objoid AND d.classoid='pg_class'::regclass JOIN pg_namespace n ON n.oid=c.relnamespace "
    "LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=d.objsubid AND d.objsubid > 0 "
    f"WHERE n.nspname='public' AND c.relname IN ('{ROW_T}','{FACT_T}') ORDER BY 1,2")
SNAP_SQL["immutable_triggers"] = (
    "SELECT c.relname, t.tgname, t.tgenabled::text FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
    "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND t.tgname LIKE '%\\_attestations\\_immutable' ORDER BY 1,2")


def snap(cur) -> dict:
    out = {}
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    for k, sql in SNAP_SQL.items():
        cur.execute(sql)
        out[k] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    cur.execute(fa2.ROWDATA_SQL)
    out["rowdata"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    cur.execute("RESET ROLE")
    return out


def trigger_args(trigger_def: str) -> tuple:
    m = re.search(r"l1_data_plane_capture_row\((.*)\)\s*$", trigger_def)
    return tuple(a.strip().strip("'") for a in m.group(1).split(",")) if m else ()


class Checks:
    def __init__(self) -> None:
        self.items: list[tuple[str, bool, str | None]] = []

    def chk(self, name: str, ok: bool, detail=None) -> bool:
        self.items.append((name, bool(ok), None if detail is None else str(detail)[:300]))
        return bool(ok)

    @property
    def failed(self) -> list[str]:
        return [n for n, ok, _ in self.items if not ok]


def preconditions(cur, leg: Leg, ck: Checks, out) -> None:
    """Read-only. Every refusal is a named check; nothing is written and no run is touched."""
    cur.execute(f"SET LOCAL ROLE {APP_OWNER}")
    cur.execute("SELECT count(*), COALESCE(string_agg(DISTINCT left(chart_id::text,8) || ':' || state, ', '), '') "
                "FROM public.build_runs WHERE state IN ('planned','running','paused')")
    n, which = cur.fetchone()
    cur.execute("RESET ROLE")
    ck.chk("pre_no_build_in_flight", n == 0, f"{n} build_run(s) in planned/running/paused on ANY chart ({which}); not touched" if n else None)
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    cur.execute("SELECT count(*) FROM public.l1_data_plane_generations WHERE status = 'building'")
    building = cur.fetchone()[0]
    ck.chk("pre_no_building_generation", building == 0, "an L1 data-plane generation is still 'building'" if building else None)
    cur.execute("RESET ROLE")
    cur.execute("SELECT count(*) FILTER (WHERE state IN ('active','idle in transaction','idle in transaction (aborted)')), "
                "count(*) FILTER (WHERE state IS NULL) FROM pg_stat_activity WHERE usename = %s AND pid <> pg_backend_pid()", (fa2.BUILDER,))
    busy, hidden = cur.fetchone()
    if hidden:
        out(f"WARNING: {hidden} {fa2.BUILDER} session(s) have a hidden state (no pg_read_all_stats); only build_runs guards them")
    ck.chk("pre_no_builder_session", busy == 0, f"a {fa2.BUILDER} session is active or idle-in-transaction" if busy else None)
    cur.execute("SELECT to_regprocedure('public.digest(text,text)') IS NOT NULL")
    ck.chk("pre_pgcrypto_digest_resolves", cur.fetchone()[0], "public.digest(text,text) does not resolve")
    # every patched function: exists, owner/secdef/config/ACL, byte-for-byte the bound body, exactly one attestation row with the bound digest
    for st in leg.functions:
        p, tag = st.patch, st.patch.short
        cur.execute("SELECT pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,''), "
                    "pg_get_functiondef(p.oid) FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", (p.regproc,))
        row = cur.fetchone()
        present = ck.chk(f"pre_{tag}_present", row is not None, f"{p.regproc} does not exist")
        if present:
            owner, secdef, config, acl, definition = row
            ck.chk(f"pre_{tag}_owner_secdef_config_acl", (owner, secdef, config, acl) == (p.owner, p.secdef, p.config, p.acl),
                   f"{(owner, secdef, config, acl)}")
            md5 = hashlib.md5(definition.encode()).hexdigest()
            ck.chk(f"pre_{tag}_body_is_the_bound_body", md5 == st.from_md5 and definition == st.from_def,
                   f"live md5 {md5} != the plan's {st.from_md5}")
        cur.execute(f"SET LOCAL ROLE {OWNER}")
        cur.execute(f"SELECT count(*), min(definition_digest) FROM {FN_ATT} WHERE function_signature = %s", (p.signature,))
        n, dg = cur.fetchone()
        ck.chk(f"pre_{tag}_attestation_row", n == 1 and dg == st.from_sha, f"{n} row(s), digest {dg}")
        cur.execute("RESET ROLE")
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    cur.execute(f"SELECT count(*), min(definition_digest) FROM {TRG_ATT} WHERE table_name = %s AND trigger_name = %s", (TABLE, TRIGGER))
    n, dg = cur.fetchone()
    ck.chk("pre_trigger_attestation_row", n == 1 and dg == leg.from_trg, f"{n} row(s), digest {dg}")
    cur.execute("RESET ROLE")
    cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname=%s", (INDEX,))
    row = cur.fetchone()
    want = "(" + ", ".join(leg.from_cols) + ") NULLS NOT DISTINCT"
    ck.chk("pre_index_shape", bool(row) and want in row[0] and row[0].count("(") == 1, row[0] if row else None)
    cur.execute("SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relname=%s AND t.tgname=%s",
                (TABLE, TRIGGER))
    row = cur.fetchone()
    ck.chk("pre_trigger_shape", bool(row) and trigger_args(row[0]) == leg.from_cols, row[0] if row else None)
    cur.execute("SELECT c.relname, COALESCE(a.attname,''), d.description FROM pg_description d "
                "JOIN pg_class c ON c.oid=d.objoid AND d.classoid='pg_class'::regclass JOIN pg_namespace n ON n.oid=c.relnamespace "
                "LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=d.objsubid AND d.objsubid > 0 "
                "WHERE n.nspname='public' AND c.relname = ANY(%s)", ([ROW_T, FACT_T],))
    have = frozenset(tuple(str(x) for x in r) for r in cur.fetchall())
    ck.chk("pre_comments_are_the_pre_state", have == leg.comments_from, f"{len(have)} comment(s) present, expected {len(leg.comments_from)}")
    if leg.name == "rollback":
        cur.execute(f"SET LOCAL ROLE {OWNER}")
        cur.execute("SELECT count(*) FROM (SELECT 1 FROM public.%s GROUP BY %s HAVING count(*) > 1) x" % (TABLE, ", ".join(OLD_COLS)))
        dup = cur.fetchone()[0]
        cur.execute("RESET ROLE")
        ck.chk("pre_no_widened_rows_collide_on_the_six_column_key", dup == 0,
               f"{dup} six-column key group(s) hold more than one row: the old index cannot be rebuilt; delete the widened rows first")


def apply_leg(cur, leg: Leg, on_exclusive=None) -> dict:
    """The statements, as data_plane_l1_owner. The ACCESS EXCLUSIVE lock is taken as late as possible (see render_plan)."""
    old_defs, fn_rows = {}, {}
    for st in leg.functions:
        cur.execute("SELECT pg_get_functiondef(%s::regprocedure)", (st.patch.regproc,))
        old_defs[st.patch.signature] = cur.fetchone()[0]
        cur.execute(st.to_def)
    for stmt in leg.comment_stmts:
        cur.execute(stmt)
    for st in leg.functions:
        cur.execute(f"ALTER TABLE {FN_ATT} DISABLE TRIGGER {FN_ATT_IMMUTABLE}")
        cur.execute(fn_att_update_sql(st.patch.signature))
        fn_rows[st.patch.signature] = cur.rowcount
        cur.execute(f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}")
    cur.execute(f"CREATE UNIQUE INDEX {NEW_INDEX_TMP} ON public.{TABLE} ({', '.join(leg.to_cols)}) NULLS NOT DISTINCT")
    if on_exclusive:
        on_exclusive()
    cur.execute(f"DROP INDEX public.{INDEX}")
    cur.execute(f"ALTER INDEX public.{NEW_INDEX_TMP} RENAME TO {INDEX}")
    cur.execute(f"DROP TRIGGER {TRIGGER} ON public.{TABLE}")
    cur.execute(trigger_create_sql(leg.to_cols))
    cur.execute(f"ALTER TABLE {TRG_ATT} DISABLE TRIGGER {TRG_ATT_IMMUTABLE}")
    cur.execute(f"UPDATE {TRG_ATT} a SET definition_digest = encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') "
                "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "WHERE a.table_name=%s AND a.trigger_name=%s AND c.relname=a.table_name AND t.tgname=a.trigger_name", (TABLE, TRIGGER))
    trg_rows = cur.rowcount
    cur.execute(f"ALTER TABLE {TRG_ATT} ENABLE TRIGGER {TRG_ATT_IMMUTABLE}")
    return {"function_attestation_rows": fn_rows, "trigger_attestation_rows": trg_rows, "old_defs": old_defs}


def change_accounting(leg: Leg, before: dict, after: dict) -> list:
    """Pure (no database): across the before/after catalog snapshots EXACTLY one index, one trigger, one trigger-attestation row and one entry per
    patched function / function attestation changed, and the functions that changed are EXACTLY the patched ones. [(check name, ok, detail)]."""
    n_fn = len(leg.functions)
    out = []
    for key, want in (("index", 1), ("trigger", 1), ("trigger_attestation", 1), ("function", n_fn), ("function_attestation", n_fn)):
        removed, added = before[key] - after[key], after[key] - before[key]
        out.append((f"post_exactly_{want}_{key}_entries_changed", len(removed) == want and len(added) == want, f"-{len(removed)} +{len(added)}"))
    changed = {r[0] for r in before["function"] - after["function"]}
    out.append(("post_changed_functions_are_exactly_the_patched_ones",
                changed == {st.patch.regproc.replace("public.", "") for st in leg.functions}, sorted(changed)))
    return out


def check_after(cur, leg: Leg, before: dict, after: dict, plan: dict, probe: dict | None, ck: Checks) -> None:
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    ck.chk("post_attestation_update_rowcounts_all_1",
           all(v == 1 for v in plan["function_attestation_rows"].values()) and plan["trigger_attestation_rows"] == 1,
           f"{plan['function_attestation_rows']}/{plan['trigger_attestation_rows']}")
    for name, ok, detail in change_accounting(leg, before, after):
        ck.chk(name, ok, detail)
    removed, added = before["comment"] - after["comment"], after["comment"] - before["comment"]
    ck.chk("post_comment_changes_are_exactly_the_planned_ones",
           (len(removed), len(added)) == (leg.removed_comments, leg.added_comments) and after["comment"] == {tuple(x) for x in leg.comments_to},
           f"-{len(removed)} +{len(added)}")
    for key in ("acl", "membership", "rls", "policy", "rowdata", "immutable_triggers"):
        ck.chk(f"post_{key}_identical", before[key] == after[key])
    # EXPECTED_DIFF, per function: the live body after == the bound body; the diff from the before body is exactly the planned hunks
    for st in leg.functions:
        p, tag = st.patch, st.patch.short
        cur.execute("SELECT pg_get_functiondef(p.oid), pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), "
                    "COALESCE(p.proacl::text,'') FROM pg_proc p WHERE p.oid = to_regprocedure(%s::text)", (p.regproc,))
        new_def, owner, secdef, config, acl = cur.fetchone()
        old_def = plan["old_defs"][p.signature]
        ck.chk(f"post_{tag}_body_is_exactly_the_bound_body",
               new_def == st.to_def and hashlib.md5(new_def.encode()).hexdigest() == st.to_md5, hashlib.md5(new_def.encode()).hexdigest())
        if leg.name == "forward":
            ck.chk(f"post_{tag}_diff_is_exactly_the_planned_hunks",
                   pa.diff_digest(old_def, new_def) == p.diff_sha256 and len(pa.unified_hunks(old_def, new_def)) == p.diff_hunks,
                   pa.diff_digest(old_def, new_def))
        else:
            ck.chk(f"post_{tag}_diff_is_exactly_the_planned_hunks", new_def == st.to_def and old_def == st.from_def)
        ck.chk(f"post_{tag}_owner_secdef_config_acl_unchanged", (owner, secdef, config, acl) == (p.owner, p.secdef, p.config, p.acl),
               (owner, secdef, config, acl))
        cur.execute(f"SELECT count(*) FROM {FN_ATT} a JOIN pg_proc p ON p.oid=to_regprocedure('public.'||a.function_signature) "
                    "WHERE a.function_signature=%s AND a.definition_digest=encode(public.digest(pg_get_functiondef(p.oid),'sha256'),'hex') "
                    "AND a.owner_name=pg_get_userbyid(p.proowner) AND a.security_definer=p.prosecdef "
                    "AND a.config IS NOT DISTINCT FROM p.proconfig", (p.signature,))
        ck.chk(f"post_{tag}_attestation_matches_live_function", cur.fetchone()[0] == 1)
        cur.execute(f"SELECT definition_digest FROM {FN_ATT} WHERE function_signature=%s", (p.signature,))
        ck.chk(f"post_{tag}_attestation_is_the_bound_digest", cur.fetchone()[0] == st.to_sha)
    cur.execute("SELECT i.indisunique, i.indisvalid, i.indnullsnotdistinct, "
                "array(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY k(attnum,ord) "
                "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum ORDER BY k.ord) "
                "FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE c.relname=%s", (INDEX,))
    row = cur.fetchone()
    ck.chk("post_index_shape", bool(row) and row[0] and row[1] and row[2] and tuple(row[3]) == leg.to_cols, row)
    cur.execute(f"SELECT count(*) FROM {TRG_ATT} a JOIN pg_class c ON c.relname=a.table_name JOIN pg_trigger t "
                "ON t.tgrelid=c.oid AND t.tgname=a.trigger_name WHERE a.table_name=%s AND a.trigger_name=%s "
                "AND a.definition_digest=encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') "
                "AND a.trigger_type=t.tgtype AND a.enabled=t.tgenabled AND a.function_oid=t.tgfoid", (TABLE, TRIGGER))
    ck.chk("post_trigger_attestation_matches_live_trigger", cur.fetchone()[0] == 1)
    cur.execute(f"SELECT definition_digest FROM {TRG_ATT} WHERE table_name=%s AND trigger_name=%s", (TABLE, TRIGGER))
    ck.chk("post_trigger_attestation_is_the_bound_digest", cur.fetchone()[0] == leg.to_trg)
    if probe is not None:
        ck.chk("post_identity_probe", probe["landed"] == probe["fixture_rows"] == probe["identities_live_args"]
               and probe["trigger_args"] == NEW_COLS and probe["live_index_cols"] == NEW_COLS
               and probe["identities_legacy_6_args"] < probe["landed"], probe)
    cur.execute("RESET ROLE")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=lambda s: sorted(s) if isinstance(s, (set, frozenset)) else str(s))


def render_report(leg: Leg, before: dict, after: dict, plan: dict, probe, gate_before: dict, gate_after: dict, ck: Checks, window: dict) -> list[str]:
    out = []
    names = {"index": "INDEX DEFINITION", "trigger": "TRIGGER DEFINITION",
             "trigger_attestation": "TRIGGER ATTESTATION ROW (table, trigger, type, enabled, fn oid, fn, digest)",
             "function": "FUNCTION (signature, md5(def), owner, secdef, config, acl)",
             "function_attestation": "FUNCTION ATTESTATION ROW (signature, digest, owner, secdef, config)",
             "comment": "COMMENTS (table, column, text)"}
    for key, title in names.items():
        removed, added = sorted(before[key] - after[key]), sorted(after[key] - before[key])
        want = (leg.removed_comments, leg.added_comments) if key == "comment" else (1, 1)
        out.append(f"== {title}: exactly {len(removed)} removed / {len(added)} added "
                   f"({'AS PLANNED' if (len(removed), len(added)) == want else 'UNEXPECTED'}) ==")
        for r in removed:
            out.append("  - " + " | ".join(r)[:400])
        for a in added:
            out.append("  + " + " | ".join(a)[:400])
    for st in leg.functions:
        out.append(f"== FUNCTION BODY {st.patch.signature} (unified diff of pg_get_functiondef, before -> after) ==")
        out.extend("  " + ln.rstrip("\n") for ln in difflib.unified_diff(plan["old_defs"][st.patch.signature].splitlines(True), st.to_def.splitlines(True),
                                                                         fromfile=f"{st.patch.signature} before", tofile="after", n=0))
    for key in ("acl", "membership", "rls", "policy", "rowdata", "immutable_triggers"):
        out.append(f"== {key.upper()}: {'IDENTICAL' if before[key] == after[key] else 'CHANGED (UNEXPECTED)'} ({len(before[key])} entries) ==")
    out.append("== DEPLOY GATE, the gate's own queries as amjis_app, search_path = %s ==" % fa2.GATE_SEARCH_PATH)
    for tag, g in (("before", gate_before), ("after ", gate_after)):
        out.append(f"  {tag}: trigger_shape_unsafe={g['trigger_shape_unsafe']} trigger_surface_unsafe={g['trigger_surface_unsafe']} "
                   f"function_digests_unsafe={g['function_digests_unsafe']}")
    out.append(f"  capture trigger digest  stored {gate_after['trigger_digest_stored']} / gate {gate_after['trigger_digest_gate_side']}")
    out.append(f"  capture function digest stored {gate_after['function_digest_stored']} / gate {gate_after['function_digest_gate_side']}")
    if probe is not None:
        out.append(f"== IDENTITY PROBE: fixture {probe['fixture_rows']} landed {probe['landed']}; distinct identities live args "
                   f"{probe['identities_live_args']}, legacy 6 args {probe['identities_legacy_6_args']} ==")
    out.append("commit conditions: " + ("ALL HOLD" if not ck.failed else f"FAILED {ck.failed}"))
    out.append(f"ACCESS EXCLUSIVE window (UTC): {window.get('start')} -> {window.get('end')}; statements inside it: {window.get('statements')}")
    return out


def run_leg(conn, leg: Leg, mode: str, out, writer_commit: str | None = None, gate_tables=None, writer_runner=None,
            expect_evidence: str | None = None) -> dict:
    """One transaction. Returns {commit_ok, checks, evidence_digest, report, ...}; the caller commits or rolls back."""
    writer_runner = writer_runner or fa2._run_cmd
    ck = Checks()
    cur = fa2.CountingCursor(conn.cursor())
    out(f"start (UTC): {fa2.utcnow()}")
    cur.execute(f"SET LOCAL search_path = {fa2.SEARCH_PATH}")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '120s'")
    cur.execute(SNAP_SQL["membership"])
    membership_before = {tuple(str(x) for x in row) for row in cur.fetchall()}  # BEFORE any transient grant
    transient = [r for r in (OWNER, APP_OWNER) if not fa2.is_member(cur, r)]
    try:
        for r in transient:
            cur.execute(f"GRANT {r} TO CURRENT_USER")
    except psycopg.Error as exc:
        ck.chk("pre_admin_can_assume_the_owner_roles", False, f"GRANT failed: {type(exc).__name__}")
        out("REFUSED: the administrator cannot assume the owner roles (" + type(exc).__name__ + "); nothing was changed")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    preconditions(cur, leg, ck, out)
    writer_line = "n/a (rollback)"
    if leg.name == "forward":
        problems, writer_line = fa2.writer_check(writer_commit, writer_runner)
        out(f"writer-first check: {writer_line}")
        if mode == "apply" or writer_commit:
            ck.chk("pre_writer_first", not problems, "; ".join(problems))
    try:
        gate_before = fa2.gate_mirror(cur, gate_tables)
    except psycopg.Error as exc:           # e.g. a gate query names a function that does not exist: a clean refusal, not a traceback
        ck.chk("pre_deploy_gate_readable", False, f"the gate's own queries failed: {type(exc).__name__}")
        out("REFUSED: the deploy gate's own queries cannot run (" + type(exc).__name__ + "); nothing was changed")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    ck.chk("pre_deploy_gate_green", not fa2.gate_red(gate_before), f"already RED before the plan: {fa2.gate_red(gate_before)}")
    out("preconditions: " + ("OK" if not ck.failed else "REFUSED"))
    for name, ok, detail in ck.items:
        if not ok:
            out(f"  - {name}: {detail}")
    if mode == "count" or ck.failed:
        out(f"end (UTC): {fa2.utcnow()}")
        return {"commit_ok": False, "checks": ck, "evidence_digest": None, "report": [], "digest_parts": {}}
    before = snap(cur)
    before["membership"] = membership_before
    cur.execute(f"SET LOCAL ROLE {OWNER}")
    prep = fa2.probe_prepare(cur) if leg.name == "forward" else None
    mark: dict = {}

    def on_exclusive() -> None:
        mark["t"], mark["n"] = fa2.utcnow(), cur.n

    plan = apply_leg(cur, leg, on_exclusive)
    probe = fa2.probe_verify(cur, prep) if prep is not None else None
    cur.execute("RESET ROLE")
    after = snap(cur)
    after["membership"] = membership_before
    check_after(cur, leg, before, after, plan, probe, ck)
    gate_after = fa2.gate_mirror(cur, gate_tables)
    ck.chk("post_deploy_gate_green", not fa2.gate_red(gate_after), f"WOULD GO RED after commit: {fa2.gate_red(gate_after)}")
    ck.chk("post_gate_trigger_digest_equals_stored", gate_after["trigger_digest_stored"] == gate_after["trigger_digest_gate_side"])
    ck.chk("post_gate_function_digest_equals_stored", gate_after["function_digest_stored"] == gate_after["function_digest_gate_side"])
    for r in transient:
        cur.execute(f"REVOKE {r} FROM CURRENT_USER")
    cur.execute(SNAP_SQL["membership"])
    after["membership"] = {tuple(str(x) for x in row) for row in cur.fetchall()}
    ck.chk("post_membership_equals_pre_state_after_revoke", after["membership"] == membership_before)
    window = {"start": mark.get("t"), "end": fa2.utcnow(), "statements": cur.n - mark["n"]}
    ck.chk("post_exclusive_window_statements_bounded", window["statements"] <= 60, window["statements"])
    digest = hashlib.sha256(canonical({
        "plan": "see plan_hash", "leg": leg.name, "executor": exec_sha(), "writer_commit": writer_commit, "writer_line": writer_line,
        "before": before, "old_def_md5": {k: hashlib.md5(v.encode()).hexdigest() for k, v in plan["old_defs"].items()},
        "checks": [(n, ok) for n, ok, _ in ck.items]}).encode()).hexdigest()
    if mode in ("apply", "rollback"):
        ck.chk("evidence_digest_matches_expected", expect_evidence == digest, f"expected {expect_evidence} got {digest}")
    report = render_report(leg, before, after, plan, probe, gate_before, gate_after, ck, window)
    for line in report:
        out(line)
    out(f"end (UTC): {fa2.utcnow()}")
    return {"commit_ok": not ck.failed, "checks": ck, "evidence_digest": digest, "report": report, "window": window,
            "digest_parts": {"before": before, "fn_before": plan["old_defs"]}}


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
    """Best effort after the transaction decision; the before-image of the function is the rollback's reference."""
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


# ------------------------------------------------------------------------------------------------------- outcome / execute
_SAFE_CLASS: dict = {}


def safe_outcome_class(es):
    """executor_standards.outcome_guard whose own file write can never mask the real result, with a committed flag: after COMMIT an
    interruption records `applied` with a warning, never `failed`."""
    if id(es) in _SAFE_CLASS:
        return _SAFE_CLASS[id(es)]

    class SafeOutcome(es.outcome_guard):
        write_error = None
        committed = False
        commit_unknown = None              # class name of the exception conn.commit() itself raised: the server MAY have committed
        commit_digest = None

        def mark_committed(self, digest):
            """Called IMMEDIATELY after conn.commit(): from here on the truth is `applied`, whatever happens next."""
            self.committed, self.commit_digest = True, digest

        def mark_commit_unknown(self, digest, exc_name):
            """conn.commit() raised (e.g. the connection dropped at the acknowledgement): neither applied nor failed is known."""
            self.commit_unknown, self.commit_digest = exc_name, digest

        def _write(self, status, digest=None, checks=(), warnings=()):
            try:
                super()._write(status, digest, checks, warnings)
            except OSError as exc:
                self.write_error = type(exc).__name__
                self.done = True

        @staticmethod
        def _warn(text):
            """stderr is best effort: a closed / broken stderr (SIGHUP with the terminal gone) must never cost the outcome file."""
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
                self._write("applied", self.commit_digest, (), ["outcome_write_failed_after_commit:" + why])      # the outcome FIRST
                self._warn("WARNING: THE COMMIT HAPPENED but the run was interrupted (%s) before outcome.json was recorded; recorded "
                           "applied with a warning. Verify in the database.\n" % why)
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
        result.setdefault("warnings", []).append(
            "outcome.json could not be written (%s)%s" % (o.write_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    else:
        result["outcome_file"] = o.path
    return result


def refuse(o, check: str, message: str):
    o.fail([check])
    raise SystemExit("REFUSED: " + message)


_HELD_SIGNALS = {signal.SIGTERM, signal.SIGHUP, signal.SIGINT}


def _on_terminate(signum, frame):
    raise SystemExit(128 + signum)


def install_signal_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _on_terminate)


def execute(args, connect, now=None, gate_fp=None, gate_tables=None, writer_runner=None):
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
            refuse(o, "args_expect_evidence_missing", f"--{args.mode} requires --expect-evidence <digest from the matching dry run>")
        if args.mode == "apply" and not args.writer_commit:
            refuse(o, "args_writer_commit_missing", "--apply requires --writer-commit (the writer deploys BEFORE this plan)")
        try:
            leg = rollback_leg() if args.mode.startswith("rollback") else forward_leg()
        except ExpectedDiffError as exc:
            refuse(o, "expected_diff_mismatch", f"the patched body is not the bound EXPECTED_DIFF body ({str(exc)[:160]})")
        lines: list[str] = []
        conn = connect()                         # the administrator credential is fetched here, never earlier
        try:
            try:
                res = run_leg(conn, leg, args.mode if args.mode != "rollback-dry-run" else "dry-run", lines.append, args.writer_commit,
                              gate_tables, writer_runner, args.expect_evidence)
            except Exception:
                conn.rollback()
                raise
            ck, digest = res["checks"], res["evidence_digest"]
            result = {"plan_hash": phash, "executor_sha256": sha, "mode": args.mode, "evidence_digest": digest,
                      "failed_checks": ck.failed, "checks": {n: ok for n, ok, _ in ck.items},
                      "details": {n: d for n, ok, d in ck.items if d and not ok}, "log": lines, "evidence_dir": str(run_dir)}
            if args.mode in ("apply", "rollback") and res["commit_ok"]:
                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)       # SIGTERM/SIGHUP/SIGINT wait until the COMMIT is recorded
                try:
                    try:
                        conn.commit()
                    except BaseException as exc:                              # the commit call ITSELF failed: the server may have committed
                        o.mark_commit_unknown(digest, type(exc).__name__)
                        raise
                    o.mark_committed(digest)                                  # IMMEDIATELY after the commit
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
    p.add_argument("--writer-commit")
    p.add_argument("--evidence-root", default=None, help=f"ignored unless {TEST_EVIDENCE_ENV} is set (tests only)")
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if not a.expect_plan:
        p.error("every mode requires --expect-plan <sha256> (the credential is fetched only for a named plan hash)")
    if a.mode in ("apply", "rollback") and not a.expect_evidence:
        p.error(f"--{a.mode} requires --expect-evidence <digest printed by the matching dry run>")
    if a.mode == "apply" and not a.writer_commit:
        p.error("--apply requires --writer-commit <full sha>")
    return a


def refuse_under_test_outside_pytest(gate_fp, environ=None):
    """An under_test launch marker (run_gated.sh started with GATE_V2_UNDER_TEST=1) is for the test harness only: the executor refuses it,
    in EVERY mode including --dry-run, unless PYTEST_CURRENT_TEST is set. Otherwise an operator shell with GATE_V2_UNDER_TEST=1 and a
    test pgenv would pass the real launcher and reach the real database with only a WARNING."""
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
