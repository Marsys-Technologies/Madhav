#!/opt/homebrew/bin/python3
"""SC-1 — the seal controller (PLAN_A10_1 §5; A10.1 B8; O-12 seal approval DELEGATED to the owner surrogate by OWNER-DEPENDENCY-REMOVAL-20261021).

One poll per invocation (launchd StartInterval).  stdlib only.  It never connects to a database, never calls gcloud, never reads a credential, never approves and never seals:
it MEASURES evidence files, executor receipts and GitHub run records, PREPARES documents (readback_sql request documents, the dispatch command, the approval command + evidence bundle) and PAGES.
Its ONLY gh calls are the allow-list `gh_allowed` (fixed read-only GETs and the two owner-step-11 dispatches), and the dispatches run only with --execute-redeploy under the delegated login.
Root CLAUDE.md §N.8: every transition below is a detector over real evidence that can read false; a missing input is an honest status and no advance.

THE CHAIN (each stage re-evaluates from evidence on every poll; the persisted markers only make the EMISSIONS exactly-once per key):
  1 AGGREGATE   the generation-wide verdict (`numerical_window_gate.generation_verdict` output, retained as `aggregate_file`) is PASSED, carries G-6 evidence, and an independent LIVE grain
                readback (executor `readback_sql`, request document written here) shows: the included pinned universe is EXACTLY the adopted expected class list (26; never taken from
                the surviving rows), every grain VERIFIED under window_qualification/1 with a PASSED attestation, ONE runner commit = the adopted head (mixed head refuses), and the
                live sums equal the aggregate's.  Plus v1's receipt of the verification operation (COMPLETED, exit 0, bound to head) and the INCONCLUSIVE cap (0.5 %).
  1b REDEPLOY   owner step 11 (A11 item 9): the checking job (`gochara-verification-job`) redefined at the sealing head — main tip == head, CI green, delegated login, dispatch of the
                definition workflow (and owner step 11a, the package build with ci_gate=require-ci-green, only when the definition finds no pipeline image), job outcomes read back, surrogate paged.
  2 BRIEF       the MAIN-produced brief (`gochara_seal_brief_check.py` green; the retained execution envelope `check-envelope` green for THIS run/attempt/commit/brief digest/brief id;
                the head is an ancestor of origin/main; the brief's own numerical gate equals the aggregate).  No brief yet => the exact dispatch command is prepared and the surrogate paged.
  3 APPROVAL    all of the above + (when named) the executor's quiescence record => the evidence bundle + the exact approval comment/command are written and the surrogate is paged, ONCE per
                (generation, head, run, attempt).  Nothing is approved by this program: the gochara-seal required reviewer approves.
  4 SEALER      the approval history of THIS run is checked by the reviewed `gochara_seal_approval.py` (the grammar line, run/attempt, digest, brief id) and the approver is the expected
                reviewer; the sealer's own run record (when supplied) must be this run.  A cancelled / failed run is RETRY_NEEDED: only a FRESH run may retry (never this one).
  5 READBACK    an independent `readback_sql` of the publication, seal and receipt rows, classified exactly as `gochara_seal_reconcile.classify`: SEALED is the only success;
                INCONSISTENT / UNREADABLE write a HALT marker, page, and the controller does nothing else for that key.

Adopted-generation file (JSON, written by the cockpit; default /Users/Dev/kalayantra/run/ADOPTED_CENTURY.json):
  chart_id, generation, head (40-hex sealing commit), verification_operation_id, aggregate_file, expected_classes [26 names] (+ optional expected_class_count),
  repo (a checkout whose origin/main contains the head; scripts default to <repo>/platform/scripts), brief_run {run_id, attempt}, brief_file, compact_file, envelope_file,
  optional: approval_history_file, seal_run_file, quiescence_operation_id, expected_approver (default the gochara-seal required reviewer), triggering_actor, readback_epoch,
  item_id, kyd, reviewed_commit, scripts_dir, aggregate_readback_operation_id.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

SCHEMA = "ky.seal_controller/1"
GATE_SCHEMA = "numerical_window_gate/1"
POLICY = "window_qualification/1"
INCONCLUSIVE_REASON = "solver_budget_exhausted"
CAP = Fraction(5, 1000)                                    # 0.5 % of all windows
EXPECTED_CLASSES = 26                                      # PLAN_A10_1 §5: "26 expected classes"
G6_KEY = "g6"                                              # (I) the aggregate's G-6 block; R8X's final key name is one edit here
REPO_SLUG = "Marsys-Technologies/Madhav"                   # fleet/github_run_readback.py REPO
WORKFLOW = "gochara-seal-approved.yml"
ENVIRONMENT = "gochara-seal"
CONFIRM = "SEAL-GOCHARA-CANDIDATE"                         # the workflow's `confirm` input
DEFAULT_APPROVER = "amonty84"                              # the gochara-seal required reviewer = this Mac's gh login (task header)
DEFAULT_ADOPTED = "/Users/Dev/kalayantra/run/ADOPTED_CENTURY.json"
DEFAULT_OPS = "/Users/Dev/kalayantra/run/ops"
DEFAULT_ITEM = "SR-A10-L6-SEAL-CLICK"
TERMINAL_BAD_RUN = ("failure", "cancelled", "timed_out", "startup_failure", "action_required", "stale", "skipped", "neutral")

_SHA = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_GEN = re.compile(r"[0-9A-Za-z._-]{1,40}")
_SAFE_ID = re.compile(r"[A-Za-z0-9._-]{1,200}")
_LOGIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}")
_CLASS = re.compile(r"[A-Za-z0-9_.-]{1,80}")
# the approval comment line — pinned equal to platform/scripts/gochara_seal_approval.py `_LINE` by a parity test
APPROVAL_LINE = "brief-digest: {digest}  run: {run}  attempt: {attempt}  brief-id: {brief_id}"

READY, NOT_READY = "READY", "NOT_READY"
NO_INPUT, STALE_HEAD, REFUSED, NOT_PASSED = "NO_INPUT", "STALE_HEAD", "REFUSED", "NOT_PASSED"
OVER_CAP, DISAGREEMENT, AWAITING_READBACK = "INCONCLUSIVE_OVER_CAP", "DISAGREEMENT", "AWAITING_READBACK"
AWAITING_BRIEF, AWAITING_APPROVAL, AWAITING_SEAL = "AWAITING_BRIEF", "AWAITING_APPROVAL", "AWAITING_SEAL"
RETRY_NEEDED, HALTED, SEALED = "RETRY_NEEDED", "HALTED", "SEALED"
STAGES = ("START", "AGGREGATE", "REDEPLOY", "BRIEF", "APPROVAL_REQUESTED", "APPROVED", "SEALED")

# owner step 11 (OWNER_GUIDE_v2 §6): the checking job redeployed at the sealing version.  Every name below is pinned to the workflow file it reads by a parity test.
DEF_WORKFLOW = "gochara-verification-job-deploy.yml"       # "Gochara verification job (definition, reviewed)"
DEF_CONFIRM = "DEFINE-GOCHARA-VERIFICATION-JOB"            # its `confirm` input
DEF_JOB = "Define the verification job"
DEF_STEPS = ("Resolve the immutable image digest", "Create or update the verification job", "Read the WHOLE definition back", "Run the secret-isolation preflight")
PKG_WORKFLOW = "deploy.yml"                                # owner step 11a: the main "Deploy" workflow builds the pipeline image the definition runs
PKG_JOBS = ("Build & Deploy Pipeline Job Image", "Require earned deployment outcome")
CI_WORKFLOW = "ci.yml"                                     # "CI — Ganga Quality Gate", the workflow deploy.yml's own dispatch gate reads
CI_GATE = "require-ci-green"                               # deploy.yml `ci_gate` input; the only value this program ever sends
RUNS_PAGE, JOBS_PAGE = 50, 100
VISIBLE_SKEW_S, VISIBLE_TIMEOUT_S = 120, 1200              # a dispatched run must show up in the run list within 20 min (clock skew allowance 2 min)
MAX_DEF_DISPATCH = 2                                       # the definition is dispatched at most twice per key: once, and once more after a package build
BAD_JOB = ("failure", "cancelled", "timed_out", "action_required", "startup_failure", "stale")
AWAITING_REDEPLOY, AWAITING_CI = "AWAITING_REDEPLOY", "AWAITING_CI"


class NotReady(Exception):
    def __init__(self, kind: str, reason: str, halt: bool = False):
        self.kind, self.reason, self.halt = kind, reason, halt
        super().__init__(f"{kind}: {reason}")


# ── small helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def utc(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def canon(v) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pct(f: Fraction) -> str:
    return f"{float(f * 100):.3f}%"


def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def load_json(path, what: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise NotReady(NO_INPUT, f"{what} is missing: {path}") from None
    except (OSError, ValueError) as exc:
        raise NotReady(NO_INPUT, f"{what} is not readable JSON ({path}): {exc}") from None


def run_script(python: str, script: Path, args: list[str], what: str, timeout: int = 120) -> subprocess.CompletedProcess:
    if not script.is_file():
        raise NotReady(NO_INPUT, f"{what}: the reviewed script is missing: {script}")
    try:
        # no -I: the execution check imports its sibling modules from its own directory (the reviewed checkout); -B keeps it from writing bytecode into that checkout
        return subprocess.run([python, "-B", str(script), *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NotReady(NO_INPUT, f"{what}: the script could not run: {exc}") from None


def last_line(proc: subprocess.CompletedProcess) -> str:
    return (proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}").splitlines()[-1]


# ── the adopted file ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def load_adopted(path: Path) -> dict:
    a = load_json(path, "the adopted-generation file")
    if not isinstance(a, dict):
        raise NotReady(NO_INPUT, "the adopted-generation file is not a JSON object")
    for k in ("chart_id", "generation", "head", "verification_operation_id"):
        if not isinstance(a.get(k), str) or not a[k].strip():
            raise NotReady(NO_INPUT, f"the adopted-generation file names no {k}")
    if not _UUID.fullmatch(a["chart_id"]):
        raise NotReady(NO_INPUT, "chart_id is not a lowercase UUID")
    if not _GEN.fullmatch(a["generation"]):
        raise NotReady(NO_INPUT, "generation has unsafe characters")
    if not _SHA.fullmatch(a["head"]):
        raise NotReady(NO_INPUT, "head is not a 40-hex commit")
    for k in ("verification_operation_id", "aggregate_readback_operation_id", "quiescence_operation_id"):
        if a.get(k) is not None and not _SAFE_ID.fullmatch(str(a[k])):
            raise NotReady(NO_INPUT, f"{k} has unsafe characters")
    for k in ("expected_approver", "triggering_actor"):
        if a.get(k) is not None and not _LOGIN.fullmatch(str(a[k])):
            raise NotReady(NO_INPUT, f"{k} is not a GitHub login")
    if a.get("readback_epoch") is not None and not is_int(a["readback_epoch"]):
        raise NotReady(NO_INPUT, "readback_epoch is not an integer")
    return a


def key_of(a: dict) -> str:
    return f"{a['generation']}@{a['head']}"


def approver_of(a: dict) -> str:
    return a.get("expected_approver") or DEFAULT_APPROVER


def scripts_dir(a: dict, override: str | None) -> Path:
    base = override or a.get("scripts_dir")
    if base:
        return Path(base)
    if not a.get("repo"):
        raise NotReady(NO_INPUT, "no scripts directory: name `repo` (a checkout at the head) or `scripts_dir` in the adopted file")
    return Path(a["repo"]) / "platform" / "scripts"


def brief_run_of(a: dict) -> tuple[int, int]:
    br = a.get("brief_run")
    if not isinstance(br, dict) or not is_int(br.get("run_id")) or not is_int(br.get("attempt")) or br["run_id"] < 1 or br["attempt"] < 1:
        raise NotReady(AWAITING_BRIEF, "no brief run is named yet (adopted file `brief_run` {run_id, attempt}): the brief job has not been dispatched or recorded")
    return br["run_id"], br["attempt"]


# ── executor receipts (read-only) ──────────────────────────────────────────────────────────────────────────────────────────────────

def read_receipt(ops: Path, op_id: str, what: str) -> tuple[dict, str, str]:
    """(record, output text, receipt sha256).  The output file must match the record's own digest."""
    rec_path, out_path = ops / "receipts" / f"{op_id}.json", ops / "receipts" / f"{op_id}.output.txt"
    try:
        raw = rec_path.read_bytes()
    except FileNotFoundError:
        raise NotReady(NO_INPUT, f"{what}: no executor receipt {rec_path}") from None
    try:
        rec = json.loads(raw)
    except ValueError as exc:
        raise NotReady(NO_INPUT, f"{what}: receipt is not JSON: {exc}") from None
    if not isinstance(rec, dict) or rec.get("operation_id") != op_id:
        raise NotReady(NO_INPUT, f"{what}: the receipt does not bind operation {op_id!r}")
    try:
        body = out_path.read_bytes()
    except FileNotFoundError:
        raise NotReady(NO_INPUT, f"{what}: no output file {out_path}") from None
    if rec.get("output_sha256") != sha256_bytes(body):
        raise NotReady(NO_INPUT, f"{what}: the output file does not match the receipt's output_sha256")
    return rec, body.decode("utf-8", "replace"), sha256_bytes(raw)


_BAD_STATUS = re.compile(r'"status"\s*:\s*"(DISAGREE|REFUSED)"')


def check_verification_receipt(ops: Path, a: dict) -> dict:
    op = a["verification_operation_id"]
    rec, text, rsha = read_receipt(ops, op, "verification receipt")
    code = rec.get("exit_code")
    m = _BAD_STATUS.search(text)
    if code == 3 or (m and m.group(1) == "DISAGREE"):
        raise NotReady(DISAGREEMENT, f"verification {op}: the verification job reported a DISAGREE (exit {code})")
    if code == 2 or (m and m.group(1) == "REFUSED"):
        raise NotReady(REFUSED, f"verification {op}: the verification job REFUSED (exit {code})")
    if rec.get("status") != "COMPLETED" or code != 0:
        raise NotReady(NOT_PASSED, f"verification {op}: receipt status {rec.get('status')!r}, exit {code!r}, not COMPLETED / 0")
    if rec.get("reviewed_commit") != a["head"]:
        raise NotReady(STALE_HEAD, f"verification {op}: the receipt is bound to commit {rec.get('reviewed_commit')!r}, not the adopted head {a['head']}")
    return {"operation_id": op, "receipt_sha256": rsha, "ts": rec.get("ts")}


def check_quiescence(ops: Path, a: dict) -> dict | None:
    """SC-1h: when the adopted file names a quiescence operation, the executor's own mechanical record for it must be ACCEPTED with every check true and bound to the head.
    None = not named = NOT MEASURED (the bundle says so; it is never reported as quiescent)."""
    op = a.get("quiescence_operation_id")
    if not op:
        return None
    path = ops / "acceptance" / f"{op}.quiescence.json"
    doc = load_json(path, f"quiescence record of {op}")
    ok = (isinstance(doc, dict) and doc.get("schema") == "ky.mechanical_quiescence/1" and doc.get("by") == "executor-mechanical" and doc.get("operation_id") == op
          and doc.get("result") == "ACCEPTED" and isinstance(doc.get("checks"), dict) and bool(doc["checks"]) and all(v is True for v in doc["checks"].values()))
    if not ok:
        failed = sorted(k for k, v in (doc.get("checks") or {}).items() if v is not True) if isinstance(doc, dict) and isinstance(doc.get("checks"), dict) else []
        raise NotReady(NOT_PASSED, f"quiescence {op}: not an ACCEPTED executor-mechanical record with every check true (failing: {failed or 'record malformed'}): "
                                   "a build or verification execution may still be live")
    if doc.get("reviewed_commit") != a["head"]:
        raise NotReady(STALE_HEAD, f"quiescence {op}: bound to commit {doc.get('reviewed_commit')!r}, not the adopted head")
    return {"operation_id": op, "record_sha256": sha256_file(path), "ts": doc.get("ts")}


# ── readback_sql request documents (nothing connects to a database here) ───────────────────────────────────────────────────────────

def write_readback_request(a: dict, out: Path, op: str, sql: str, what: str) -> Path:
    sql_path, req_path = out / "readback" / "sql" / f"{op}.sql", out / "readback" / "requests" / f"{op}.json"
    atomic_write(sql_path, sql + "\n")
    doc = {"operation_id": op, "kind": "readback_sql", "item_id": a.get("item_id") or DEFAULT_ITEM, "idempotency_key": op, "requested_by": "seal-controller",
           "kyd": a.get("kyd") or DEFAULT_ITEM, "args": {"sql_file": f"run/ops/sql/{op}.sql"}, "sql_sha256": sha256_bytes((sql + "\n").encode()),
           "reviewed_commit": a.get("reviewed_commit") or a["head"]}
    atomic_write(req_path, json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return req_path


def readback_or_request(ops: Path, out: Path, a: dict, op: str, sql: str, what: str) -> tuple[dict, str, str]:
    """The receipt of `op` (completed, exit 0, output intact), or AWAITING_READBACK with the request document written.  A receipt that exists but is not a clean
    COMPLETED/0 is NOT silently re-requested: it is reported (a failed read is information)."""
    try:
        rec, text, rsha = read_receipt(ops, op, what)
    except NotReady as exc:
        if (ops / "receipts" / f"{op}.json").exists():
            raise
        req = write_readback_request(a, out, op, sql, what)
        raise NotReady(AWAITING_READBACK, f"{what}: no live readback yet; the request document is {req} (copy it, and its sql, into the executor's requests/sql)") from exc
    if rec.get("kind") != "readback_sql" or rec.get("status") != "COMPLETED" or rec.get("exit_code") != 0:
        raise NotReady(NOT_PASSED, f"{what} {op}: receipt kind {rec.get('kind')!r} status {rec.get('status')!r} exit {rec.get('exit_code')!r}")
    return rec, text, rsha


def parse_table(text: str, header: list[str], what: str) -> list[dict]:
    lines = text.splitlines()
    if not lines or lines[0].split("\t") != header:
        raise NotReady(NO_INPUT, f"{what}: the readback output does not start with the expected header {header}")
    rows = []
    for ln in lines[1:]:
        if not ln.strip("\t \r"):
            continue
        cells = ln.split("\t")
        if len(cells) != len(header):
            raise NotReady(NO_INPUT, f"{what}: a readback row has {len(cells)} cells, expected {len(header)}")
        rows.append(dict(zip(header, cells)))
    return rows


# ── stage 1: the aggregate ─────────────────────────────────────────────────────────────────────────────────────────────────────────

GRAIN_HEADER = ["event_class", "path_id", "rule_version", "status", "policy_version", "windows_stored", "commit", "attestation"]


def grain_sql(a: dict) -> str:
    return ("SELECT p.event_class, p.path_id, p.rule_version, v.status, v.policy_version, v.windows_stored, v.runner_identity ->> 'commit' AS commit,"
            " v.runner_identity -> 'numerical_window_gate' ->> 'status' AS attestation FROM public.ka_gochara_search_path_pin p"
            " LEFT JOIN public.ka_gochara_eval_window_verification v ON v.chart_id = p.chart_id AND v.generation = p.generation AND v.event_class = p.event_class"
            " AND v.path_id = p.path_id AND v.rule_version = p.rule_version"
            f" WHERE p.chart_id = '{a['chart_id']}' AND p.generation = '{a['generation']}' AND p.disposition = 'included' AND p.path_id IN ('P1', 'P2', 'P3', 'P4')"
            " ORDER BY 1, 2, 3")


def op_id(prefix: str, a: dict, *extra: str) -> str:
    gen = re.sub(r"[^0-9A-Za-z]+", "-", a["generation"])
    return "-".join([prefix, gen, a["head"][:12], *extra])


def gate_numbers(g, where: str) -> dict:
    if not isinstance(g, dict) or g.get("schema") != GATE_SCHEMA:
        raise NotReady(NOT_PASSED, f"{where} carries no {GATE_SCHEMA} verdict (the gate did not run)")
    if g.get("status") != "PASSED" or g.get("problems") != [] or g.get("policy") != POLICY:
        raise NotReady(NOT_PASSED, f"{where}: the numerical-window gate is {g.get('status')!r} under {g.get('policy')!r} with problems {g.get('problems')!r}, not PASSED")
    nums = {k: g.get(k) for k in ("windows", "numbered_windows", "blank_windows")}
    if any(not is_int(v) or v < 0 for v in nums.values()):
        raise NotReady(NOT_PASSED, f"{where}: the gate's window counts are not non-negative integers: {nums!r}")
    if nums["windows"] == 0:
        raise NotReady(NOT_PASSED, f"{where}: the gate counts no windows: nothing was measured (an honest null, not a pass)")
    if nums["numbered_windows"] + nums["blank_windows"] != nums["windows"]:
        raise NotReady(NOT_PASSED, f"{where}: numbered + blank does not add up to the windows counted")
    inconclusive = sum(h["windows"] for h in (g.get("honest_nulls") or []) if isinstance(h, dict) and h.get("reason") == INCONCLUSIVE_REASON and is_int(h.get("windows")))
    return {"windows": nums["windows"], "numbered": nums["numbered_windows"], "blank": nums["blank_windows"], "inconclusive": inconclusive, "gate": g}


def cap_check(windows: int, inconclusive: int, where: str) -> Fraction:
    share = Fraction(inconclusive, windows)
    if share > CAP:
        raise NotReady(OVER_CAP, f"{where}: INCONCLUSIVE windows {inconclusive} of {windows} = {pct(share)}, over the {pct(CAP)} cap")
    return share


def expected_classes(a: dict) -> list[str]:
    cls = a.get("expected_classes")
    want = a.get("expected_class_count", EXPECTED_CLASSES)
    if not is_int(want) or want < 1:
        raise NotReady(NO_INPUT, "expected_class_count is not a positive integer")
    if not isinstance(cls, list) or not all(isinstance(c, str) and _CLASS.fullmatch(c) for c in cls):
        raise NotReady(NO_INPUT, "the adopted file names no expected_classes list (the pinned universe is never taken from the surviving rows)")
    if len(set(cls)) != len(cls) or len(cls) != want:
        raise NotReady(NO_INPUT, f"expected_classes has {len(set(cls))} distinct names ({len(cls)} listed), the universe is {want}")
    return sorted(cls)


def check_aggregate(a: dict, ops: Path, out: Path) -> dict:
    classes = expected_classes(a)
    if not a.get("aggregate_file"):
        raise NotReady(NO_INPUT, "the adopted file names no aggregate_file (the persisted generation-wide verdict)")
    agg = load_json(a["aggregate_file"], "the persisted aggregate verdict")
    nums = gate_numbers(agg, "the aggregate")
    for k, want in (("chart_id", a["chart_id"]), ("generation", a["generation"]), ("head", a["head"])):
        if k in agg and agg[k] != want:
            raise NotReady(STALE_HEAD, f"the aggregate is bound to {k} {agg[k]!r}, not the adopted {want!r}")
    g6 = agg.get(G6_KEY)
    if not isinstance(g6, dict) or g6.get("status") != "PASSED":
        raise NotReady(NOT_PASSED, f"the aggregate carries no PASSED G-6 evidence (`{G6_KEY}` block): the aggregate refuses missing G-6 evidence")
    if not is_int(agg.get("grains")) or agg["grains"] < 1:
        raise NotReady(NOT_PASSED, "the aggregate states no grain count")
    share = cap_check(nums["windows"], nums["inconclusive"], "aggregate")
    op = a.get("aggregate_readback_operation_id") or op_id("seal-controller-grains", a)
    rec, text, rsha = readback_or_request(ops, out, a, op, grain_sql(a), "live grain readback")
    rows = parse_table(text, GRAIN_HEADER, "live grain readback")
    live_classes = sorted({r["event_class"] for r in rows})
    missing, extra = sorted(set(classes) - set(live_classes)), sorted(set(live_classes) - set(classes))
    if missing or extra:
        raise NotReady(REFUSED, f"the live pinned universe is not the {len(classes)} expected classes (missing {missing}, unexpected {extra}): a class is never dropped or added by what survived")
    if len(rows) != agg["grains"]:
        raise NotReady(DISAGREEMENT, f"live readback shows {len(rows)} included grains, the aggregate counts {agg['grains']}")
    total, commits = 0, set()
    for r in rows:
        tag = f"{r['event_class']}/{r['path_id']}@{r['rule_version']}"
        if r["status"] != "VERIFIED" or r["policy_version"] != POLICY or r["attestation"] != "PASSED":
            raise NotReady(REFUSED, f"{tag}: window verification {r['status']!r} under {r['policy_version']!r}, attestation {r['attestation']!r}: not VERIFIED/PASSED")
        if not r["windows_stored"].isdigit():
            raise NotReady(REFUSED, f"{tag}: windows_stored {r['windows_stored']!r} is not a count")
        total += int(r["windows_stored"])
        commits.add(r["commit"])
    if commits != {a["head"]}:
        raise NotReady(STALE_HEAD if len(commits) == 1 else REFUSED, f"the grains were verified at commits {sorted(commits)}, not exactly the adopted head {a['head']} (a mixed or foreign head never aggregates)")
    if total != nums["windows"]:
        raise NotReady(DISAGREEMENT, f"live readback stores {total} windows across the grains, the aggregate states {nums['windows']}")
    verification = check_verification_receipt(ops, a)
    return {"aggregate": nums, "share": share, "classes": len(classes), "grains": len(rows), "g6": g6.get("status"),
            "aggregate_sha256": sha256_file(Path(a["aggregate_file"])), "grain_readback": {"operation_id": op, "receipt_sha256": rsha, "ts": rec.get("ts")},
            "verification": verification}


# ── stage 2: the main-produced brief ───────────────────────────────────────────────────────────────────────────────────────────────

def dispatch_command(a: dict) -> str:
    return (f"gh workflow run {WORKFLOW} --repo {REPO_SLUG} --ref main -f chart_id={a['chart_id']} -f generation={a['generation']} -f confirm={CONFIRM}")


def dispatch_text(a: dict) -> str:
    return (f"BRIEF DISPATCH NEEDED — generation {a['generation']}, sealing head {a['head']}\n\n"
            "The aggregate is PASSED. The seal brief is produced by the trusted workflow from `main` at ONE commit; it runs only when main's tip IS the adopted head.\n"
            f"Check first:   test \"$(git -C <repo> rev-parse origin/main)\" = {a['head']}\n"
            f"Dispatch:      {dispatch_command(a)}\n"
            "Then record the run in the adopted file: brief_run {run_id, attempt}, and the retained artifact files brief_file / compact_file / envelope_file\n"
            f"(the `seal-brief-<run>-<attempt>` artifact). Nothing is dispatched by the controller.\n")


def ancestor_of_main(a: dict, main_ref: str) -> None:
    repo = a.get("repo")
    if not repo:
        raise NotReady(NO_INPUT, "no `repo` in the adopted file: whether the sealing commit is on main cannot be measured")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0")
    try:
        proc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", a["head"], main_ref], capture_output=True, text=True, timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NotReady(NO_INPUT, f"git could not run: {exc}") from None
    if proc.returncode == 1:
        raise NotReady(REFUSED, f"the adopted head {a['head']} is not an ancestor of {main_ref}: the brief is not main-produced")
    if proc.returncode != 0:
        raise NotReady(NO_INPUT, f"git merge-base failed (exit {proc.returncode}): {proc.stderr.strip()[:200]}")


def check_brief(a: dict, agg: dict, sdir: Path, python: str, main_ref: str) -> dict:
    run_id, attempt = brief_run_of(a)
    paths = {k: a.get(k) for k in ("brief_file", "compact_file", "envelope_file")}
    absent = [k for k, v in paths.items() if not v or not Path(v).is_file()]
    if absent:
        raise NotReady(AWAITING_BRIEF, f"the retained brief evidence is not there yet (missing: {', '.join(absent)}); the dispatch command is prepared")
    brief_path, compact_path, env_path = (Path(paths[k]) for k in ("brief_file", "compact_file", "envelope_file"))
    compact = load_json(compact_path, "the compact result line")
    if not isinstance(compact, dict):
        raise NotReady(NO_INPUT, "the compact result line is not a JSON object")
    produced_by = (compact.get("producer") or {}).get("commit") if isinstance(compact.get("producer"), dict) else None
    if produced_by != a["head"]:
        raise NotReady(STALE_HEAD, f"the retained brief was produced by commit {produced_by!r}, not the adopted head {a['head']}")
    ancestor_of_main(a, main_ref)
    raw = brief_path.read_bytes()
    check = sdir / "gochara_seal_brief_check.py"
    proc = run_script(python, check, ["--brief-file", str(brief_path), "--compact-file", str(compact_path), "--chart-id", a["chart_id"], "--generation", a["generation"],
                                      "--sealing-commit", a["head"]], "seal brief check")
    if proc.returncode != 0:
        raise NotReady(REFUSED, f"seal brief check exit {proc.returncode}: {last_line(proc)}")
    digest = proc.stdout.strip()
    if not _HEX64.fullmatch(digest) or digest != sha256_bytes(raw):
        raise NotReady(REFUSED, f"the brief check printed {digest!r}, which is not the retained brief's sha256")
    brief = json.loads(raw.decode("utf-8"))
    if (brief.get("code") or {}).get("sealing_commit") != a["head"]:
        raise NotReady(STALE_HEAD, "the brief's sealing commit is not the adopted head")
    if brief.get("result_policy") != POLICY:
        raise NotReady(REFUSED, f"the brief's result policy is {brief.get('result_policy')!r}, not {POLICY}")
    nums = gate_numbers(brief.get("numerical_window_gate"), "the brief")
    share = cap_check(nums["windows"], nums["inconclusive"], "retained brief")
    for k in ("windows", "numbered", "blank", "inconclusive"):
        if nums[k] != agg["aggregate"][k]:
            raise NotReady(DISAGREEMENT, f"the brief's numerical verdict ({k} {nums[k]}) differs from the aggregate's ({agg['aggregate'][k]}): another candidate than the one verified")
    brief_id = (compact.get("persisted") or {}).get("brief_id")
    envproc = run_script(python, sdir / "gochara_seal_execution_check.py",
                         ["check-envelope", "--envelope-file", str(env_path), "--compact-file", str(compact_path), "--run-id", str(run_id), "--attempt", str(attempt),
                          "--sealing-commit", a["head"], "--brief-digest", digest, "--chart-id", a["chart_id"], "--generation", a["generation"]], "execution envelope check")
    if envproc.returncode != 0:
        raise NotReady(REFUSED, f"execution envelope check exit {envproc.returncode}: {last_line(envproc)}")
    envelope = load_json(env_path, "the execution envelope")
    return {"brief_digest": digest, "brief_id": brief_id, "brief_path": str(brief_path), "compact_path": str(compact_path), "envelope_path": str(env_path),
            "producer_execution_id": envelope["producer_execution_id"], "run_id": run_id, "attempt": attempt, "producer": compact.get("producer"),
            "share": share, "brief_gate_digest": sha256_bytes(canon(nums["gate"]).encode()),
            "scripts": {n: {"path": str(sdir / n), "sha256": sha256_file(sdir / n)} for n in ("gochara_seal_brief_check.py", "gochara_seal_execution_check.py")}}


# ── stage 3: the approval preparation (emission, exactly once per generation × head × run × attempt) ───────────────────────────

def approval_comment(brief: dict) -> str:
    return APPROVAL_LINE.format(digest=brief["brief_digest"], run=brief["run_id"], attempt=brief["attempt"], brief_id=brief["brief_id"])


def approval_command(a: dict, brief: dict) -> str:
    return (f"test \"$(gh api user --jq .login)\" = {approver_of(a)} && \\\n"
            f"ENV_ID=\"$(gh api repos/{REPO_SLUG}/environments/{ENVIRONMENT} --jq .id)\" && \\\n"
            f"gh api -X POST repos/{REPO_SLUG}/actions/runs/{brief['run_id']}/pending_deployments -F 'environment_ids[]='\"$ENV_ID\" -f state=approved \\\n"
            f"  -f comment='{approval_comment(brief)}'")


def bundle_doc(a: dict, agg: dict, brief: dict, quiescence: dict | None, out: Path, now, redeploy: dict | None = None) -> dict:
    n = agg["aggregate"]
    return {"schema": SCHEMA, "kind": "approval_bundle", "key": key_of(a), "run": {"run_id": brief["run_id"], "attempt": brief["attempt"]}, "chart_id": a["chart_id"],
            "generation": a["generation"], "head": a["head"], "approver": approver_of(a), "approval_comment": approval_comment(brief), "brief_digest": brief["brief_digest"],
            "brief_id": brief["brief_id"], "producer_execution_id": brief["producer_execution_id"], "producer": brief["producer"],
            "verdict": {"status": "PASSED", "windows": n["windows"], "numbered": n["numbered"], "blank": n["blank"], "inconclusive": n["inconclusive"],
                        "share_percent": pct(brief["share"]), "cap_percent": pct(CAP), "classes": agg["classes"], "grains": agg["grains"], "g6": agg["g6"],
                        "gate_digest": brief["brief_gate_digest"]},
            "evidence": {"aggregate_sha256": agg["aggregate_sha256"], "brief": brief["brief_path"], "compact": brief["compact_path"], "envelope": brief["envelope_path"],
                         "grain_readback": agg["grain_readback"], "verification": agg["verification"], "scripts": brief["scripts"],
                         "redeploy": redeploy,                                                          # owner step 11: the definition run (and package run) read back at the sealing head
                         "quiescence": quiescence if quiescence is not None else None,
                         "quiescence_note": "measured and ACCEPTED" if quiescence is not None else "NOT MEASURED: the adopted file names no quiescence operation"},
            "prepared_at": utc(now), "bundle_dir": str(out)}


def surrogate_text(doc: dict, cmd: str) -> str:
    v = doc["verdict"]
    return (f"To: madhav-44 (owner surrogate) — O-12 seal approval, delegated by OWNER-DEPENDENCY-REMOVAL-20261021\n"
            f"Key: {doc['key']}  run {doc['run']['run_id']} attempt {doc['run']['attempt']}\n\n"
            f"APPROVAL REQUESTED. Generation {doc['generation']} (chart {doc['chart_id']}), sealing head {doc['head']}: the aggregate is PASSED over {v['classes']} classes / {v['grains']} grains,\n"
            f"  G-6 {v['g6']}; windows {v['windows']}, numbered {v['numbered']}, blank-with-reason {v['blank']}; INCONCLUSIVE {v['inconclusive']} of {v['windows']} = {v['share_percent']} (cap {v['cap_percent']}).\n"
            f"  brief digest {doc['brief_digest']}, brief id {doc['brief_id']}, producer execution {doc['producer_execution_id']}.\n"
            f"  checking job redeployed at the sealing head: definition run {((doc['evidence'].get('redeploy') or {}).get('definition') or {}).get('run_id')} read back green (owner step 11).\n"
            f"  quiescence: {doc['evidence']['quiescence_note']}.\n"
            f"  evidence bundle: {doc['bundle_dir']}/APPROVAL_BUNDLE.json\n\n"
            f"Approval comment (exactly this line):\n  {doc['approval_comment']}\n\n"
            f"Approval command (run as the `{ENVIRONMENT}` required reviewer = `{doc['approver']}`; the controller never runs it):\n{cmd}\n\n"
            "Read the brief in the run summary before approving. This message grants nothing by itself; the hard stops in your charter stay with the native.\n")


def owner_text(doc: dict) -> str:
    v = doc["verdict"]
    return (f"NOTICE to the owner (no action needed)\n\nThe numbers check for generation {doc['generation']} passed over {v['classes']} event classes and the seal brief is ready for approval: "
            f"{v['windows']} time windows, {v['numbered']} numbered, {v['blank']} honestly blank with a stated reason, {v['share_percent']} undecidable (limit {v['cap_percent']}). "
            "The approval is with the standing deputy under your delegation; you will be told the outcome. Nothing has been sealed by this notice.\n"
            f"Reference: {doc['key']} run {doc['run']['run_id']}\n")


@contextlib.contextmanager
def locked(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / ".seal_controller.lock", "a+") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        yield


def append_page(pages_log: Path, needle: str, line: str) -> bool:
    """Append `line` unless a line carrying `needle` is already in the log.  True when written."""
    have = pages_log.read_text() if pages_log.exists() else ""
    if needle in have:
        return False
    pages_log.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(pages_log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line.encode())
    finally:
        os.close(fd)
    return True


def write_marker(out: Path, name: str, payload: dict) -> None:
    atomic_write(out / "markers" / name, json.dumps(payload, sort_keys=True) + "\n")


def emit_dispatch(a: dict, out: Path, pages_log: Path, now) -> str:
    key = key_of(a)
    with locked(out):
        marker = out / "markers" / f"BRIEF_DISPATCH.{a['generation']}.{a['head']}.done"
        if marker.exists():
            return "ALREADY"
        atomic_write(out / "BRIEF_DISPATCH.txt", dispatch_text(a))
        append_page(pages_log, f"PAGE SEAL-BRIEF-DISPATCH key={key} ", f"{utc(now)} PAGE SEAL-BRIEF-DISPATCH key={key} head={a['head'][:12]} dispatch={out / 'BRIEF_DISPATCH.txt'}\n")
        write_marker(out, marker.name, {"key": key, "ts": utc(now)})
        return "NEW"


def emit_approval(a: dict, agg: dict, brief: dict, quiescence: dict | None, out: Path, pages_log: Path, now, redeploy: dict | None = None) -> tuple[str, dict]:
    key = key_of(a)
    run_key = f"{key} run={brief['run_id']} attempt={brief['attempt']}"
    bdir = out / "approval" / a["generation"] / f"{a['head'][:12]}-r{brief['run_id']}a{brief['attempt']}"
    with locked(out):
        marker = out / "markers" / f"APPROVAL_REQUESTED.{a['generation']}.{a['head']}.r{brief['run_id']}a{brief['attempt']}.done"
        bundle_path = bdir / "APPROVAL_BUNDLE.json"
        existing = None
        if bundle_path.exists():
            with contextlib.suppress(ValueError):
                existing = json.loads(bundle_path.read_text())
        if existing is not None and existing.get("brief_digest") != brief["brief_digest"]:
            raise NotReady(REFUSED, f"the approval prepared for {run_key} names brief digest {existing.get('brief_digest')!r}, the retained brief is now {brief['brief_digest']!r}: "
                                    "a stale or altered brief is never re-approved; start a fresh run")
        doc = existing if existing is not None else bundle_doc(a, agg, brief, quiescence, bdir, now, redeploy)
        if marker.exists():
            return "ALREADY", doc
        if existing is None:                                                          # the bundle is complete on disk BEFORE any page or marker
            atomic_write(bundle_path, json.dumps(doc, indent=1, sort_keys=True) + "\n")
        cmd = approval_command(a, brief)
        atomic_write(bdir / "APPROVE_COMMAND.txt", cmd + "\n")
        atomic_write(bdir / "SURROGATE_MESSAGE.txt", surrogate_text(doc, cmd))
        atomic_write(bdir / "OWNER_NOTICE.txt", owner_text(doc))
        atomic_write(out / "SURROGATE_MESSAGE.txt", surrogate_text(doc, cmd))
        atomic_write(out / "OWNER_NOTICE.txt", owner_text(doc))
        v = doc["verdict"]
        append_page(pages_log, f"PAGE SEAL-APPROVAL-REQUESTED key={key} run={brief['run_id']} attempt={brief['attempt']} ",
                    f"{utc(now)} PAGE SEAL-APPROVAL-REQUESTED key={key} run={brief['run_id']} attempt={brief['attempt']} generation={a['generation']} head={a['head'][:12]} "
                    f"windows={v['windows']} numbered={v['numbered']} inconclusive={v['inconclusive']}/{v['windows']}({v['share_percent']} vs {v['cap_percent']} cap) "
                    f"brief_digest={doc['brief_digest'][:12]} brief_id={doc['brief_id']} bundle={bundle_path}\n")
        write_marker(out, marker.name, {"key": key, "run": brief["run_id"], "attempt": brief["attempt"], "brief_digest": brief["brief_digest"], "ts": utc(now)})
        return "NEW", doc


# ── stage 4: the approval and the sealer's run ───────────────────────────────────────────────────────────────────────────────────

def check_approval(a: dict, brief: dict, sdir: Path, python: str, scratch: Path) -> dict:
    hist_path = a.get("approval_history_file")
    if not hist_path or not Path(hist_path).is_file():
        raise NotReady(AWAITING_APPROVAL, "no approval history of this run yet (the reviewer has not approved, or the history was not fetched)")
    history = load_json(hist_path, "the approval history")
    if not isinstance(history, list):
        raise NotReady(REFUSED, "the approval history is not a JSON array")
    if not any(isinstance(h, dict) and any((e or {}).get("name") == ENVIRONMENT for e in (h.get("environments") or [])) for h in history):
        raise NotReady(AWAITING_APPROVAL, f"the approval history holds no review of environment {ENVIRONMENT!r} yet")
    out_file = scratch / "approval_check.json"
    scratch.mkdir(parents=True, exist_ok=True)
    out_file.unlink(missing_ok=True)
    proc = run_script(python, sdir / "gochara_seal_approval.py",
                      ["--approvals-file", str(hist_path), "--environment", ENVIRONMENT, "--run-id", str(brief["run_id"]), "--attempt", str(brief["attempt"]),
                       "--brief-digest", brief["brief_digest"], "--brief-id", str(brief["brief_id"]), "--producer-execution-id", brief["producer_execution_id"],
                       "--triggering-actor", a.get("triggering_actor") or approver_of(a), "--out", str(out_file)], "approval check")
    if proc.returncode != 0:
        raise NotReady(REFUSED, f"approval check exit {proc.returncode}: {last_line(proc)} (an approval of another run/attempt/digest is never reused; only a fresh run may retry)")
    doc = json.loads(out_file.read_text())
    if doc.get("approver_login") != approver_of(a):
        raise NotReady(REFUSED, f"the approval is by {doc.get('approver_login')!r}, not the {ENVIRONMENT} required reviewer {approver_of(a)!r}: only that principal approves")
    return {"approver": doc["approver_login"], "history_sha256": sha256_file(Path(hist_path)), "run_id": doc["run_id"], "attempt": doc["run_attempt"]}


def check_seal_run(a: dict, brief: dict) -> dict | None:
    """The sealer's run record (a `ky.window_run/1`-shaped JSON the cockpit saves; optional).  None = not supplied = unknown."""
    p = a.get("seal_run_file")
    if not p or not Path(p).is_file():
        return None
    rec = load_json(p, "the seal run record")
    if not isinstance(rec, dict) or str(rec.get("run_id")) != str(brief["run_id"]):
        raise NotReady(REFUSED, f"the seal run record is for run {rec.get('run_id') if isinstance(rec, dict) else None!r}, not this run {brief['run_id']}")
    if rec.get("run_attempt") is not None and str(rec["run_attempt"]) != str(brief["attempt"]):
        raise NotReady(REFUSED, f"the seal run record is for attempt {rec.get('run_attempt')!r}, not this attempt {brief['attempt']}")
    return {"status": rec.get("status"), "conclusion": rec.get("conclusion"), "sha256": sha256_file(Path(p))}


# ── stage 5: the independent readback of the seal ──────────────────────────────────────────────────────────────────────────────────

SEAL_HEADER = ["publication_statuses", "seal_rows", "receipts"]


def seal_sql(a: dict) -> str:
    c, g = a["chart_id"], a["generation"]
    return ("SELECT (SELECT string_agg(status, ',' ORDER BY status) FROM public.kala_gochara_publication"
            f" WHERE chart_id = '{c}'::uuid AND generation = '{g}') AS publication_statuses,"
            f" (SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = '{c}'::uuid AND generation = '{g}') AS seal_rows,"
            " (SELECT string_agg(brief_digest || ':' || run_id || ':' || run_attempt, ',' ORDER BY brief_digest, run_id, run_attempt) FROM public.ka_gochara_seal_approval"
            f" WHERE chart_id = '{c}'::uuid AND generation = '{g}') AS receipts")


def classify(pub: list[str], seals: int, receipts: list[tuple[str, int, int]], *, digest: str, run_id: int, attempt: int) -> tuple[str, str]:
    """Mirrors platform/scripts/gochara_seal_reconcile.py `classify` (a parity test pins them equal)."""
    status = pub[0] if len(pub) == 1 else None
    if status == "candidate" and seals == 0 and not receipts:
        return "NOT_SEALED", "the candidate was not published and not sealed; no receipt exists"
    if status == "published" and seals == 1 and len(receipts) == 1:
        if receipts[0] == (digest, run_id, attempt):
            return "SEALED", "published, sealed, and the receipt names this run's approved digest"
        return "INCONSISTENT", "the generation is sealed but its receipt names another digest, run or attempt"
    return "INCONSISTENT", f"publication {status!r}, {seals} seal row(s), {len(receipts)} receipt(s): not a state this workflow can produce"


def parse_seal(text: str) -> tuple[list[str], int, list[tuple[str, int, int]]]:
    rows = parse_table(text, SEAL_HEADER, "seal readback")
    if len(rows) != 1:
        raise NotReady(NO_INPUT, f"seal readback: {len(rows)} rows, expected exactly one")
    r = rows[0]
    if not r["seal_rows"].isdigit():
        raise NotReady(NO_INPUT, "seal readback: seal_rows is not a count")
    receipts = []
    for item in [x for x in r["receipts"].split(",") if x]:
        parts = item.split(":")
        if len(parts) != 3 or not _HEX64.fullmatch(parts[0]) or not parts[1].isdigit() or not parts[2].isdigit():
            raise NotReady(NO_INPUT, f"seal readback: a receipt entry {item!r} is not digest:run:attempt")
        receipts.append((parts[0], int(parts[1]), int(parts[2])))
    return [x for x in r["publication_statuses"].split(",") if x], int(r["seal_rows"]), receipts


def check_sealed(a: dict, brief: dict, approval: dict, seal_run: dict | None, ops: Path, out: Path) -> dict:
    epoch = sha256_bytes(canon({"seal_run": seal_run, "epoch": a.get("readback_epoch", 0), "approval": approval["history_sha256"]}).encode())[:12]
    op = op_id("seal-controller-final", a, f"r{brief['run_id']}a{brief['attempt']}", epoch)
    try:
        rec, text, rsha = readback_or_request(ops, out, a, op, seal_sql(a), "seal readback")
    except NotReady as exc:
        if exc.kind == NOT_PASSED:                                                   # the read itself failed: the outcome is UNKNOWN — never "not sealed"
            raise NotReady(HALTED, f"UNREADABLE: {exc.reason}", halt=True) from None
        raise
    pub, seals, receipts = parse_seal(text)
    state, why = classify(pub, seals, receipts, digest=brief["brief_digest"], run_id=brief["run_id"], attempt=brief["attempt"])
    info = {"operation_id": op, "receipt_sha256": rsha, "ts": rec.get("ts"), "state": state, "why": why}
    if state == "SEALED":
        return info
    if state == "INCONSISTENT":
        raise NotReady(HALTED, f"INCONSISTENT: {why}", halt=True)
    run_done = seal_run is not None and seal_run.get("status") == "completed"
    if run_done and seal_run.get("conclusion") == "success":
        raise NotReady(HALTED, "INCONSISTENT: the sealer's run completed successfully but the readback shows nothing sealed", halt=True)
    if run_done and seal_run.get("conclusion") in TERMINAL_BAD_RUN:
        raise NotReady(RETRY_NEEDED, f"the sealer's run {brief['run_id']} ended {seal_run.get('conclusion')!r} and nothing was sealed: only a FRESH run may retry (never this run or attempt)")
    raise NotReady(AWAITING_SEAL, "approved; the readback shows the candidate not yet sealed (the sealer's run is pending, or its record was not supplied)")


def emit_final(a: dict, brief: dict, approval: dict, final: dict, out: Path, pages_log: Path, now) -> str:
    key = key_of(a)
    with locked(out):
        marker = out / "markers" / f"SEALED.{a['generation']}.{a['head']}.done"
        if marker.exists():
            return "ALREADY"
        doc = {"schema": SCHEMA, "kind": "sealed", "key": key, "chart_id": a["chart_id"], "generation": a["generation"], "head": a["head"], "run_id": brief["run_id"],
               "attempt": brief["attempt"], "brief_digest": brief["brief_digest"], "approver": approval["approver"], "readback": final, "ts": utc(now)}
        atomic_write(out / "SEALED.json", json.dumps(doc, indent=1, sort_keys=True) + "\n")
        append_page(pages_log, f"PAGE SEAL-SEALED key={key} ", f"{utc(now)} PAGE SEAL-SEALED key={key} run={brief['run_id']} attempt={brief['attempt']} head={a['head'][:12]} "
                                                               f"brief_digest={brief['brief_digest'][:12]} readback={final['operation_id']}\n")
        write_marker(out, marker.name, {"key": key, "ts": utc(now)})
        return "NEW"


def emit_stop(a: dict, kind: str, reason: str, run: tuple[int, int] | None, out: Path, pages_log: Path, now, halt: bool) -> None:
    key = key_of(a)
    tag = "SEAL-HALT" if halt else "SEAL-RETRY-NEEDED"
    suffix = f" run={run[0]} attempt={run[1]}" if run else ""
    with locked(out):
        name = f"HALT.{a['generation']}.{a['head']}" if halt else f"RETRY.{a['generation']}.{a['head']}.r{run[0]}a{run[1]}" if run else f"RETRY.{a['generation']}.{a['head']}"
        if (out / "markers" / name).exists():
            return
        append_page(pages_log, f"PAGE {tag} key={key}{suffix} ", f"{utc(now)} PAGE {tag} key={key}{suffix} kind={kind} reason={reason[:300]}\n")
        write_marker(out, name, {"key": key, "kind": kind, "reason": reason, "ts": utc(now)})


# ── stage 1b: owner step 11 — the checking job redeployed at the sealing version (A11 item 9) ─────────────────────────────────────
# Owner step 11 (OWNER_GUIDE_v2 §6): "sealing refuses unless the checking job was set up at the very same version that runs the seal".  The controller does it, under the
# DELEGATED gh login of this Mac (OWNER-DEPENDENCY-REMOVAL-20261021), through the ONLY gh calls in `gh_allowed` below: fixed read-only GETs, and the two workflow dispatches.
# It never dispatches the approval/seal workflow, never approves, never sends the CI-gate override choice, never runs gcloud, and never reads a credential (gh uses its own login).
# Evidence per transition (§N.8) — every detector below can read false:
#   main tip == the adopted head (live)        refuses STALE_HEAD "main moved" — step 11 goes stale if anything merges after it
#   CI green at the head                       the newest COMPLETED ci.yml run of the head is `success` and no newer run is still going (deploy.yml's own gate reads the same)
#   delegated login                            `gh api user` login == the expected reviewer login
#   done                                       a COMPLETED `success` definition run at head_sha == head on main, whose job "Define the verification job" and each of its four
#                                              named steps (digest, create/update, whole-definition readback, isolation preflight) read back `success`
#   no package                                 the definition run failed AT the digest step => owner step 11a: deploy.yml with ci_gate=require-ci-green, force_all_services=true
#                                              (the pipeline-image job runs only then when the head did not change the pipeline), then the definition once more
# Exactly-once: a marker is written BEFORE each dispatch (at most once per key and kind; a crash after the dispatch can only wait, never re-dispatch); a run that never appears
# within 20 min, a failed run, or a package that still leaves no image HALTS (marker + one page); nothing is retried by guess.

def api_get(path: str) -> list[str]:
    return ["api", "-X", "GET", path]


def runs_path(workflow: str, head: str) -> str:
    return f"repos/{REPO_SLUG}/actions/workflows/{workflow}/runs?head_sha={head}&per_page={RUNS_PAGE}"


def jobs_path(run_id: int) -> str:
    return f"repos/{REPO_SLUG}/actions/runs/{run_id}/jobs?per_page={JOBS_PAGE}"


def def_dispatch_argv() -> list[str]:
    return ["workflow", "run", DEF_WORKFLOW, "--repo", REPO_SLUG, "--ref", "main", "-f", f"confirm={DEF_CONFIRM}"]


def pkg_dispatch_argv() -> list[str]:
    return ["workflow", "run", PKG_WORKFLOW, "--repo", REPO_SLUG, "--ref", "main", "-f", f"ci_gate={CI_GATE}", "-f", "force_all_services=true"]


_READ_PATHS = tuple(re.compile(p) for p in (
    r"user",
    re.escape(f"repos/{REPO_SLUG}/git/ref/heads/main"),
    re.escape(f"repos/{REPO_SLUG}/actions/workflows/") + r"(ci|deploy|gochara-verification-job-deploy)\.yml/runs\?head_sha=[0-9a-f]{40}&per_page=" + str(RUNS_PAGE),
    re.escape(f"repos/{REPO_SLUG}/actions/runs/") + r"[1-9][0-9]{0,18}/jobs\?per_page=" + str(JOBS_PAGE)))


def gh_allowed(argv: list[str]) -> bool:
    """The complete list of gh invocations this program may make: four fixed read-only GET shapes and exactly two workflow dispatches."""
    if len(argv) == 4 and argv[:3] == ["api", "-X", "GET"]:
        return any(rx.fullmatch(argv[3]) for rx in _READ_PATHS)
    return argv in (def_dispatch_argv(), pkg_dispatch_argv())


def default_gh(argv: list[str], timeout: int = 90) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["gh", *argv], capture_output=True, text=True, timeout=timeout, env=env)


def gh_call(gh, argv: list[str], what: str) -> str:
    if not gh_allowed(argv):
        raise NotReady(REFUSED, f"{what}: internal error — this gh call is not on the controller's allow-list")
    try:
        proc = gh(argv)
    except (OSError, subprocess.TimeoutExpired):
        raise NotReady(NO_INPUT, f"{what}: gh could not be run or timed out") from None
    if proc.returncode != 0:
        raise NotReady(NO_INPUT, f"{what}: gh exited {proc.returncode}")                  # stderr is never relayed (it may name an identity)
    return proc.stdout


def gh_json(gh, argv: list[str], what: str) -> dict:
    try:
        doc = json.loads(gh_call(gh, argv, what))
    except ValueError:
        raise NotReady(NO_INPUT, f"{what}: gh output is not JSON") from None
    if not isinstance(doc, dict):
        raise NotReady(NO_INPUT, f"{what}: gh output is not a JSON object")
    return doc


def parse_ts(v, what: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        raise NotReady(NO_INPUT, f"{what}: {v!r} is not a GitHub timestamp") from None


def list_runs(gh, workflow: str, head: str) -> list[dict]:
    """Runs of `workflow` whose head_sha is `head`, newest first.  A response for another commit, a malformed row or a cut-short list refuses the whole read."""
    doc = gh_json(gh, api_get(runs_path(workflow, head)), f"{workflow} runs")
    rows = doc.get("workflow_runs")
    if not isinstance(rows, list) or (is_int(doc.get("total_count")) and doc["total_count"] > len(rows)):
        raise NotReady(NO_INPUT, f"{workflow} runs: the run list is missing or cut short")
    out = []
    for r in rows:
        if not isinstance(r, dict) or not is_int(r.get("id")) or r.get("status") not in ("queued", "in_progress", "completed", "waiting", "requested", "pending"):
            raise NotReady(NO_INPUT, f"{workflow} runs: a run row is malformed")
        if r.get("head_sha") != head:
            raise NotReady(NO_INPUT, f"{workflow} runs: run {r['id']} is for commit {r.get('head_sha')!r}, not the requested {head}")
        if r.get("event") == "pull_request":
            continue
        out.append({"id": r["id"], "status": r["status"], "conclusion": r.get("conclusion"), "event": r.get("event"), "branch": r.get("head_branch"),
                    "created_at": parse_ts(r.get("created_at"), f"{workflow} run {r['id']} created_at"), "url": r.get("html_url")})
    out.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)
    return out


def read_jobs(gh, run_id: int) -> list[dict]:
    doc = gh_json(gh, api_get(jobs_path(run_id)), f"run {run_id} jobs")
    jobs = doc.get("jobs")
    if not isinstance(jobs, list) or (is_int(doc.get("total_count")) and doc["total_count"] > len(jobs)):
        raise NotReady(NO_INPUT, f"run {run_id} jobs: the job list is missing or cut short")
    out = []
    for j in jobs:
        steps = j.get("steps") if isinstance(j, dict) else None
        if not isinstance(j, dict) or not isinstance(j.get("name"), str) or not isinstance(steps, list):
            raise NotReady(NO_INPUT, f"run {run_id} jobs: a job row is malformed")
        out.append({"name": j["name"], "status": j.get("status"), "conclusion": j.get("conclusion"),
                    "steps": [{"name": s.get("name"), "conclusion": s.get("conclusion")} for s in steps if isinstance(s, dict)]})
    return out


def def_verdict(jobs: list[dict]) -> tuple[str, dict]:
    """PASS | DIGEST_MISSING | FAIL, measured from the run's own job/step conclusions.  PASS needs the job AND every named step to read `success`."""
    job = next((j for j in jobs if j["name"] == DEF_JOB), None)
    ev = {"job": DEF_JOB, "job_conclusion": job["conclusion"] if job else None, "steps": {}}
    if job is None:
        return "FAIL", ev
    for prefix in DEF_STEPS:
        ev["steps"][prefix] = next((s["conclusion"] for s in job["steps"] if isinstance(s["name"], str) and s["name"].startswith(prefix)), None)
    failed = next((s["name"] for s in job["steps"] if s["conclusion"] in BAD_JOB), None)
    ev["failed_step"] = failed
    if job["conclusion"] == "success" and all(v == "success" for v in ev["steps"].values()):
        return "PASS", ev
    if failed and failed.startswith(DEF_STEPS[0]):
        return "DIGEST_MISSING", ev
    return "FAIL", ev


def pkg_verdict(run: dict, jobs: list[dict]) -> tuple[bool, dict]:
    by = {j["name"]: j["conclusion"] for j in jobs}
    ev = {"run_id": run["id"], "run_conclusion": run["conclusion"], "jobs": by}
    ok = (run["conclusion"] == "success" and all(by.get(n) == "success" for n in PKG_JOBS) and not any(c in BAD_JOB for c in by.values()))
    return ok, ev


def main_tip(gh) -> str:
    sha = (gh_json(gh, api_get(f"repos/{REPO_SLUG}/git/ref/heads/main"), "main tip").get("object") or {}).get("sha")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise NotReady(NO_INPUT, "main tip: the response carries no commit sha")
    return sha


def ci_green(gh, head: str) -> dict:
    runs = list_runs(gh, CI_WORKFLOW, head)
    if not runs:
        raise NotReady(NOT_PASSED, f"CI is not green: no {CI_WORKFLOW} run exists for {head}")
    if runs[0]["status"] != "completed":
        raise NotReady(AWAITING_CI, f"CI is still running for {head} (run {runs[0]['id']}, {runs[0]['status']})")
    if runs[0]["conclusion"] != "success":
        raise NotReady(NOT_PASSED, f"CI is not green for {head}: run {runs[0]['id']} concluded {runs[0]['conclusion']!r}")
    return {"run_id": runs[0]["id"], "conclusion": "success"}


def delegated_login(gh, a: dict) -> str:
    login = gh_json(gh, api_get("user"), "gh login").get("login")
    if login != approver_of(a):
        raise NotReady(REFUSED, f"the gh login on this machine is not the delegated login `{approver_of(a)}`: nothing is dispatched under another identity")
    return login


def redeploy_markers(out: Path, a: dict, kind: str) -> list[tuple[Path, dt.datetime]]:
    found = []
    for p in sorted((out / "markers").glob(f"REDEPLOY_{kind}.{a['generation']}.{a['head']}.n*")) if (out / "markers").is_dir() else []:
        try:
            ts = parse_ts(json.loads(p.read_text())["ts"], "redeploy marker")
        except (ValueError, KeyError, TypeError, NotReady):                                                # an unreadable marker still counts as a dispatch, at its file time
            ts = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
        found.append((p, ts))
    return found


def answered(marker_ts: dt.datetime, runs: list[dict]) -> bool:
    return any(r["created_at"] >= marker_ts - dt.timedelta(seconds=VISIBLE_SKEW_S) for r in runs)


def halt_redeploy(reason: str):
    raise NotReady(HALTED, reason, halt=True)


def dispatch_redeploy(a: dict, ops: Path, out: Path, pages_log: Path, gh, execute: bool, now, kind: str, argv: list[str], why: str) -> None:
    """Gate, then (only under --execute and the delegated login) dispatch once.  Always ends by raising AWAITING_REDEPLOY."""
    head, key = a["head"], key_of(a)
    tip = main_tip(gh)
    if tip != head:
        raise NotReady(STALE_HEAD, f"main moved: its tip is {tip}, the sealing head is {head}; step 11 must be repeated at the sealing version, nothing is dispatched")
    ci = ci_green(gh, head)
    quiescence = check_quiescence(ops, a)
    n = len(redeploy_markers(out, a, kind)) + 1
    tag = f"{kind.lower()}#{n}"
    cmd = "gh " + shlex.join(argv)
    note = "quiescence measured and ACCEPTED" if quiescence else "quiescence NOT MEASURED (the adopted file names no quiescence operation)"
    qtag = "measured" if quiescence else "NOT_MEASURED"
    if not execute:
        with locked(out):
            atomic_write(out / "REDEPLOY_DISPATCH.txt", f"OWNER STEP 11 — {why}\nkey {key}  main tip = head {head}  CI green (run {ci['run_id']})  {note}\n\nDispatch (delegated login `{approver_of(a)}`):\n{cmd}\n")
            append_page(pages_log, f"PAGE SEAL-REDEPLOY-DISPATCH-NEEDED key={key} step={tag} ",
                        f"{utc(now)} PAGE SEAL-REDEPLOY-DISPATCH-NEEDED key={key} step={tag} head={head[:12]} dispatch={out / 'REDEPLOY_DISPATCH.txt'}\n")
        raise NotReady(AWAITING_REDEPLOY, f"{why}: the dispatch is prepared, not executed (the controller runs without --execute-redeploy): {cmd}")
    delegated_login(gh, a)
    with locked(out):
        marker = out / "markers" / f"REDEPLOY_{kind}.{a['generation']}.{head}.n{n}"
        if marker.exists():
            raise NotReady(AWAITING_REDEPLOY, f"{why}: already dispatched ({tag})")
        write_marker(out, marker.name, {"key": key, "kind": kind, "n": n, "cmd": cmd, "ts": utc(now)})       # BEFORE the dispatch: at most once
        try:
            gh_call(gh, argv, f"dispatch {tag}")
        except NotReady:
            marker.unlink(missing_ok=True)                                                                   # the dispatch did not happen: a later poll may try again
            raise
        append_page(pages_log, f"PAGE SEAL-REDEPLOY-DISPATCHED key={key} step={tag} ",
                    f"{utc(now)} PAGE SEAL-REDEPLOY-DISPATCHED key={key} step={tag} head={head[:12]} workflow={argv[2]} ci_run={ci['run_id']} quiescence={qtag}\n")
    raise NotReady(AWAITING_REDEPLOY, f"{why}: dispatched ({tag}); waiting for the run to appear and finish")


def verified_definition(gh, run: dict) -> dict:
    verdict, ev = def_verdict(read_jobs(gh, run["id"]))
    if verdict != "PASS":
        raise NotReady(NOT_PASSED, f"definition run {run['id']} concluded success but its jobs do not read back as the full definition (job {ev['job_conclusion']!r}, steps {ev['steps']}): not accepted")
    return {"run_id": run["id"], "url": run["url"], "created_at": utc(run["created_at"]), **ev}


def emit_redeploy_done(a: dict, ev: dict, out: Path, pages_log: Path, now) -> None:
    key = key_of(a)
    with locked(out):
        marker = out / "markers" / f"REDEPLOY_DONE.{a['generation']}.{a['head']}.done"
        if marker.exists():
            return
        doc = {"schema": SCHEMA, "kind": "redeploy", "key": key, "head": a["head"], "evidence": ev, "ts": utc(now),
               "step8_permission": "NOT MEASURED by this program: after a redeploy the cockpit re-reads `gcloud run jobs get-iam-policy gochara-verification-job` (owner step 8); if the grant is gone the owner redoes step 8"}
        atomic_write(out / "REDEPLOY.json", json.dumps(doc, indent=1, sort_keys=True) + "\n")
        append_page(pages_log, f"PAGE SEAL-REDEPLOY-DONE key={key} ",
                    f"{utc(now)} PAGE SEAL-REDEPLOY-DONE key={key} head={a['head'][:12]} definition_run={ev['definition']['run_id']} package_run={(ev.get('package') or {}).get('run_id')} "
                    f"evidence={out / 'REDEPLOY.json'} reread_step8_permission=required\n")
        write_marker(out, marker.name, {"key": key, "ts": utc(now)})


def check_redeploy(a: dict, ops: Path, out: Path, pages_log: Path, gh, execute: bool, now) -> dict:
    head = a["head"]
    clock = now or dt.datetime.now(dt.timezone.utc)
    defs = [r for r in list_runs(gh, DEF_WORKFLOW, head) if r["event"] == "workflow_dispatch" and r["branch"] == "main"]
    for r in defs:                                                                                           # done: evidence first, whoever dispatched it
        if r["status"] == "completed" and r["conclusion"] == "success":
            ev = {"definition": verified_definition(gh, r)}
            if redeploy_markers(out, a, "PKG"):                                                              # a package build was dispatched: read its job outcomes back too
                for p in list_runs(gh, PKG_WORKFLOW, head):
                    if p["status"] == "completed" and p["conclusion"] == "success" and p["created_at"] <= r["created_at"]:
                        ok, pev = pkg_verdict(p, read_jobs(gh, p["id"]))
                        if ok:
                            ev["package"] = pev
                            break
            if not a.get("brief_run"):                                                                       # until the brief is produced, main must still BE the sealing head
                tip = main_tip(gh)
                if tip != head:
                    raise NotReady(STALE_HEAD, f"main moved: its tip is {tip}, the sealing head is {head}; the redeploy is stale and must be repeated at the sealing version")
            emit_redeploy_done(a, ev, out, pages_log, now)
            return ev
    live = [r for r in defs if r["status"] != "completed"]
    if live:
        raise NotReady(AWAITING_REDEPLOY, f"the definition run {live[0]['id']} is {live[0]['status']}: {live[0]['url']}")
    def_marks = redeploy_markers(out, a, "DEF")
    if def_marks and not answered(def_marks[-1][1], defs):
        if (clock - def_marks[-1][1]).total_seconds() > VISIBLE_TIMEOUT_S:
            halt_redeploy("the definition was dispatched but no run appeared within 20 minutes: a person looks (the controller dispatches nothing more for this key)")
        raise NotReady(AWAITING_REDEPLOY, "the definition was dispatched; its run is not visible yet")
    if not defs:
        dispatch_redeploy(a, ops, out, pages_log, gh, execute, now, "DEF", def_dispatch_argv(), "owner step 11: define the checking job at the sealing version")
    latest = defs[0]
    verdict, ev = def_verdict(read_jobs(gh, latest["id"]))
    if verdict != "DIGEST_MISSING":
        halt_redeploy(f"the definition run {latest['id']} concluded {latest['conclusion']!r} at step {ev.get('failed_step')!r}: the deployed definition is left in place to inspect, nothing is retried automatically ({latest['url']})")
    pkgs = list_runs(gh, PKG_WORKFLOW, head)                                                                 # owner step 11a: there is no pipeline image for the sealing commit
    after = [p for p in pkgs if p["created_at"] > latest["created_at"]]
    if any(p["status"] != "completed" for p in after):
        raise NotReady(AWAITING_REDEPLOY, "owner step 11a: the package build (deploy.yml) is running")
    pkg_marks = redeploy_markers(out, a, "PKG")
    if pkg_marks and not answered(pkg_marks[-1][1], pkgs):
        if (clock - pkg_marks[-1][1]).total_seconds() > VISIBLE_TIMEOUT_S:
            halt_redeploy("the package build was dispatched but no run appeared within 20 minutes: a person looks")
        raise NotReady(AWAITING_REDEPLOY, "owner step 11a: the package build was dispatched; its run is not visible yet")
    for p in after:
        ok, pev = pkg_verdict(p, read_jobs(gh, p["id"]))
        if not ok:
            halt_redeploy(f"owner step 11a: the package build run {p['id']} did not succeed ({pev}); nothing is retried automatically ({p['url']})")
        if len(def_marks) >= MAX_DEF_DISPATCH:
            halt_redeploy("the definition still reports no pipeline image after the package build; it was already dispatched twice for this key")
        dispatch_redeploy(a, ops, out, pages_log, gh, execute, now, "DEF", def_dispatch_argv(), "owner step 11: define the checking job again, after the package build")
    if pkg_marks:
        halt_redeploy("a package build was already dispatched for this key and the definition still finds no pipeline image: a person looks")
    dispatch_redeploy(a, ops, out, pages_log, gh, execute, now, "PKG", pkg_dispatch_argv(), "owner step 11a: no pipeline image exists for the sealing commit, build and deploy it (CI-green gate)")


# ── the poll ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def halted(a: dict, out: Path) -> dict | None:
    p = out / "markers" / f"HALT.{a['generation']}.{a['head']}"
    if not p.exists():
        return None
    with contextlib.suppress(ValueError):
        return json.loads(p.read_text())
    return {"kind": HALTED, "reason": "a HALT marker exists and is unreadable"}


def advance(a: dict, ops: Path, out: Path, pages_log: Path, sdir: Path, python: str, main_ref: str, now, status: dict, gh=None, execute: bool = False) -> None:
    status["key"] = key_of(a)
    stop = halted(a, out)
    if stop:
        status["stage"] = status.get("stage", "START")
        raise NotReady(HALTED, f"STOPPED for {key_of(a)}: {stop.get('reason')} (the controller does nothing else for this key until a person clears the HALT marker)")
    agg = check_aggregate(a, ops, out)
    status["stage"] = "AGGREGATE"
    try:
        redeploy = check_redeploy(a, ops, out, pages_log, gh or default_gh, execute, now)
    except NotReady as exc:
        if exc.kind == HALTED:
            emit_stop(a, exc.kind, exc.reason, None, out, pages_log, now, halt=True)
        raise
    status["stage"] = "REDEPLOY"
    try:
        brief = check_brief(a, agg, sdir, python, main_ref)
    except NotReady as exc:
        if exc.kind == AWAITING_BRIEF and not a.get("brief_run"):                  # a named run is already dispatched: only its artifacts are missing
            how = emit_dispatch(a, out, pages_log, now)
            exc.reason += f" ({'dispatch paged' if how == 'NEW' else 'dispatch already paged'})"
        raise
    status["stage"] = "BRIEF"
    quiescence = check_quiescence(ops, a)
    how, doc = emit_approval(a, agg, brief, quiescence, out, pages_log, now, redeploy)
    status["stage"] = "APPROVAL_REQUESTED"
    status["approval_emission"] = "paged" if how == "NEW" else "already_paged"
    run = (brief["run_id"], brief["attempt"])
    try:
        approval = check_approval(a, brief, sdir, python, out / "scratch")
        status["stage"] = "APPROVED"
        seal_run = check_seal_run(a, brief)
        final = check_sealed(a, brief, approval, seal_run, ops, out)
    except NotReady as exc:
        if exc.kind in (RETRY_NEEDED, HALTED):
            emit_stop(a, exc.kind, exc.reason, run, out, pages_log, now, halt=exc.halt)
        raise
    emit_final(a, brief, approval, final, out, pages_log, now)
    status["stage"] = "SEALED"


def run(adopted_path, ops, out, pages_log, scripts_override=None, python=sys.executable, main_ref="origin/main", now=None, gh=None, execute_redeploy: bool = False) -> dict:
    adopted_path, ops, out, pages_log = Path(adopted_path), Path(ops), Path(out), Path(pages_log)
    status = {"schema": SCHEMA, "ts": utc(now), "state": NOT_READY, "stage": "START"}
    try:
        a = load_adopted(adopted_path)
        sdir = scripts_dir(a, scripts_override)
        advance(a, ops, out, pages_log, sdir, python, main_ref, now, status, gh, execute_redeploy)
        status.update(state=READY, kind=SEALED)
        line = f"SEAL-CONTROLLER {status['ts']} SEALED key={status['key']}"
    except NotReady as exc:
        status.update(kind=exc.kind, reason=exc.reason)
        line = f"SEAL-CONTROLLER {status['ts']} stage={status['stage']} {exc.kind}: {exc.reason}"
    status["line"] = line
    out.mkdir(parents=True, exist_ok=True)
    atomic_write(out / "SEAL_CONTROLLER_STATUS.json", json.dumps(status, indent=1, sort_keys=True) + "\n")
    return status


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--adopted", default=os.environ.get("SEAL_ADOPTED", DEFAULT_ADOPTED))
    ap.add_argument("--ops", default=os.environ.get("SEAL_OPS", DEFAULT_OPS))
    ap.add_argument("--out", default=os.environ.get("OUT"))
    ap.add_argument("--pages-log", default=os.environ.get("SEAL_PAGES_LOG"))
    ap.add_argument("--scripts-dir", default=os.environ.get("SEAL_SCRIPTS_DIR"))
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--execute-redeploy", action="store_true", default=os.environ.get("SEAL_EXECUTE_REDEPLOY") == "1",
                    help="owner step 11: dispatch the redeploy under the delegated gh login (without it the dispatch is only prepared and paged)")
    ap.add_argument("--python", default="/opt/homebrew/bin/python3")
    a = ap.parse_args(argv)
    if not a.out or not a.pages_log:
        print("seal_controller: --out (or $OUT) and --pages-log are required", file=sys.stderr)
        return 2
    status = run(a.adopted, a.ops, a.out, a.pages_log, a.scripts_dir, a.python, a.main_ref, execute_redeploy=a.execute_redeploy)
    print(status["line"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
