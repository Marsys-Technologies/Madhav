"""Mechanical evidence for operation-item steps (SR-OP-STEPS, SR-OP-STEPS-2; plan v3.0 §C).

Two detectors here (state.recorded_na_steps is the third, for a plan-declared not-applicable step), each
reading a recorded ledger and nothing else:

* ``check_lease_row_evidence`` — a ``lease_held`` step is evidenced by the lease row on
  origin/campaign-coordination at a cited commit (git show), not by a verifier's verdict.
* ``executor_acceptance`` — the executor's OWN recorded acceptance of an operation
  (run/ops/acceptance/<operation_id>[.post].json) is the accepted verdict at the receipt's digest.

No function here writes anything or synthesises a verdict event.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
from datetime import datetime

from .completion import CompletionError

LEASE_SCHEMA = "ky.lease_row_evidence/1"
COORDINATION_REF = "origin/campaign-coordination"
COORDINATION_FILE = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
LEASE_KEYS = {"coordination_commit", "expires", "item", "lease_id", "row", "schema", "step", "taken"}
MECHANICAL_SCHEMA = "ky.mechanical_acceptance/1"     # audit.py accepts the same record for pre-acceptance
VERIFIER_LANES = ("v1", "v2", "v3", "v4")


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=30, env=env)


def check_lease_row_evidence(raw: bytes, path: str, spec: dict, item: str, step: str, repo: str) -> dict:
    """Bind a ``lease_held`` evidence file to the lease row it cites, by reading the coordination ledger.

    The file is canonical JSON {coordination_commit, expires, item, lease_id, row, schema, step, taken}. The
    commit must be an ancestor of origin/campaign-coordination; the coordination file AT that commit must hold
    exactly one row for the lease id, with status ACTIVE, whose text, started and expiry cells are the cited ones.
    (I) INTERPRETATION: ACTIVE is read at the cited commit (the "take" commit), because the row is later
    RELEASED; the executor's own lease_live check at execution time is not repeated here.
    """
    declared = spec.get("path")
    if not isinstance(declared, str) or not declared or os.path.realpath(path) != os.path.realpath(declared):
        raise CompletionError("lease evidence path does not match the declared evidence file")
    evidence = json.loads(raw)
    if not isinstance(evidence, dict):
        raise CompletionError("lease evidence must be a canonical JSON object")
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if raw not in (canonical, canonical + b"\n"):
        raise CompletionError("lease evidence must use canonical JSON (sorted keys, no spaces or duplicate fields)")
    if set(evidence) != LEASE_KEYS or evidence["schema"] != LEASE_SCHEMA:
        raise CompletionError(f"lease evidence must carry exactly {sorted(LEASE_KEYS)} with schema {LEASE_SCHEMA}")
    if evidence["item"] != item or evidence["step"] != step:
        raise CompletionError("lease evidence item/step does not match the command")
    lease_id, commit, row = evidence["lease_id"], evidence["coordination_commit"], evidence["row"]
    if (not isinstance(lease_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", lease_id) is None
            or not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or not isinstance(row, str) or not isinstance(evidence["taken"], str)
            or not isinstance(evidence["expires"], str)):
        raise CompletionError("lease evidence has a malformed lease_id, coordination_commit, row, taken or expires")

    ancestor = _git(repo, "merge-base", "--is-ancestor", commit, COORDINATION_REF)
    if ancestor.returncode == 1:
        raise CompletionError(f"coordination commit {commit} is not an ancestor of {COORDINATION_REF}")
    if ancestor.returncode != 0:
        raise CompletionError(f"cannot read {COORDINATION_REF} or commit {commit}: {ancestor.stderr.strip()[:200]}")
    shown = _git(repo, "show", f"{commit}:{COORDINATION_FILE}")
    if shown.returncode != 0:
        raise CompletionError(f"{COORDINATION_FILE} is not readable at {commit}")
    rows = [line.rstrip() for line in shown.stdout.splitlines() if line.startswith(f"| {lease_id} | ")]
    if len(rows) != 1:
        raise CompletionError(f"lease {lease_id} has {len(rows)} rows at {commit}; exactly one is required")
    cells = rows[0].strip().strip("|").split(" | ")
    if len(cells) < 6:
        raise CompletionError(f"lease row {lease_id} is not a campaign / purpose / started / expiry / status row")
    started, expiry, status = (cell.strip() for cell in cells[-3:])
    if re.match(r"ACTIVE(?:\s|$)", status) is None:
        raise CompletionError(f"lease {lease_id} is not ACTIVE at {commit} (status: {status[:60]!r})")
    if row != rows[0] or evidence["taken"] != started or evidence["expires"] != expiry:
        raise CompletionError(f"lease evidence row, taken or expires differs from the ledger row of {lease_id} at {commit}")
    return evidence


def _actor_slot(actor: str) -> str | None:
    slot = (actor or "").partition(":")[2].strip()
    return slot or None


def _acceptance_problem(record, opid: str, request_digest: str, receipt_digest: str, executor: dict,
                        requesters: list[str]) -> str | None:
    """Why `record` is not the executor's acceptance of this operation at this request and receipt; None if it is."""
    if not isinstance(record, dict):
        return "is not a JSON object"
    if record.get("operation_id") != opid:
        return f"names operation {record.get('operation_id')!r}, not {opid!r}"
    if record.get("result") != "ACCEPTED":
        return f"result is {record.get('result')!r}, not ACCEPTED"
    by = record.get("by")
    checks = record.get("checks")
    if by == "executor-mechanical":
        if (record.get("schema") != MECHANICAL_SCHEMA or record.get("phase") not in ("pre", "post")
                or not isinstance(checks, dict) or not checks or any(value is not True for value in checks.values())):
            return "is a mechanical acceptance without schema, phase and every check true"
    elif by not in VERIFIER_LANES:
        return f"was signed by {by!r}, neither executor-mechanical nor a verifier lane"
    for requester in requesters:
        if by.casefold() in (requester.strip().casefold(), (_actor_slot(requester) or "").casefold()):
            return "is signed by the requester"
    if record.get("request_sha256") != request_digest:
        return "accepted a different request digest"
    if "receipt_sha256" in record and record["receipt_sha256"] != receipt_digest:
        return "accepted a different receipt digest"
    if "output_sha256" in record and record["output_sha256"] != executor.get("output_sha256"):
        return "accepted a different measured output"
    if "reviewed_commit" in record and record["reviewed_commit"] != executor.get("reviewed_commit"):
        return "accepted a different reviewed commit"
    return None


def executor_acceptance(ops: str, opid: str, request_digest: str, receipt_digest: str, executor: dict,
                        requesters: list[str]) -> dict:
    """The executor's recorded acceptance of `opid` (run/ops/acceptance/<opid>.post.json, else .json).

    Binds to the file directly: same operation, the request digest (and receipt/output digests where it names
    them) it accepted, signed by executor-mechanical or a verifier lane that is not the requester. Raises
    CompletionError naming each candidate's reason when none qualifies. Never writes a verdict event.
    """
    directory = os.path.join(ops, "acceptance")
    reasons = []
    for name in (opid + ".post.json", opid + ".json"):
        path = os.path.join(directory, name)
        if os.path.realpath(path) != path:
            reasons.append(f"{name} escapes run/ops/acceptance")
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                record = json.load(handle)
        except FileNotFoundError:
            reasons.append(f"{name} is absent")
            continue
        except (OSError, ValueError) as exc:
            reasons.append(f"{name} is unreadable ({exc})")
            continue
        problem = _acceptance_problem(record, opid, request_digest, receipt_digest, executor, requesters)
        if problem is None:
            return record
        reasons.append(f"{name} {problem}")
    raise CompletionError("operation step needs independent acceptance at the executor receipt digest, or the "
                          "executor's own recorded acceptance: " + "; ".join(reasons))


# ----------------------------------------------------------------------------- SR-TEARDOWN-COMPLETION, pre_acceptance

def request_digest(request: dict) -> str:
    """executor.request_digest (A8 §3.9): the complete request without acceptance_receipt, expires_at and *_expires_at."""
    bound = {key: value for key, value in request.items()
             if key not in ("acceptance_receipt", "expires_at") and not key.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _load(path: str, what: str) -> dict:
    if os.path.realpath(path) != path:
        raise CompletionError(f"{what} escapes its run/ops directory")
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        raise CompletionError(f"{what} is unreadable ({exc})") from exc
    if not isinstance(value, dict):
        raise CompletionError(f"{what} is not a JSON object")
    return value


def check_acceptance_file_evidence(raw: bytes, path: str, spec: dict, item: str, step: str, ops: str) -> dict:
    """A ``pre_acceptance`` step is evidenced by the acceptance file run/ops/acceptance/<operation_id>.post.json.

    The evidence file IS that acceptance record (a receipt-equivalent, like the lease row): it must sit in
    run/ops/acceptance under the declared path, name the dispatch operation of THIS item, and accept the digest of
    the archived request (run/ops/done); its signer is a verifier lane or executor-mechanical with every check true,
    and not the requester. No verifier verdict is involved, none is synthesised.
    """
    declared = spec.get("path")
    if not isinstance(declared, str) or not declared or os.path.realpath(path) != os.path.realpath(declared):
        raise CompletionError("acceptance evidence path does not match the declared evidence file")
    try:
        record = json.loads(raw)
    except ValueError as exc:
        raise CompletionError(f"acceptance evidence is not JSON ({exc})") from exc
    opid = record.get("operation_id") if isinstance(record, dict) else None
    if (not isinstance(opid, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", opid) is None or opid in (".", "..")
            or os.path.realpath(path) != os.path.join(ops, "acceptance", opid + ".post.json")):
        raise CompletionError("acceptance evidence must be run/ops/acceptance/<operation_id>.post.json")
    request = _load(os.path.join(ops, "done", opid + ".json"), "operation request")
    executor = _load(os.path.join(ops, "receipts", opid + ".json"), "operation receipt")
    with open(os.path.join(ops, "receipts", opid + ".json"), "rb") as handle:
        receipt_digest = hashlib.sha256(handle.read()).hexdigest()
    digest = request_digest(request)
    requester = request.get("requested_by")
    if (request.get("item_id") != item or executor.get("item_id") != item or executor.get("operation_id") != opid
            or executor.get("request_sha256") != digest or not isinstance(requester, str) or not requester.strip()):
        raise CompletionError(f"{opid} is not this item's operation, or its receipt does not bind the archived request")
    problem = _acceptance_problem(record, opid, digest, receipt_digest, executor, [requester])
    if problem:
        raise CompletionError(f"acceptance {opid}.post.json {problem}")
    return record


# Mirrors v5_small_test_shared.absence_evidence's census (a test ties it to OUTPUT_TABLES in that module); the
# tracker never imports the pinned executor or its reviewed policy.
ABSENCE_CENSUS = frozenset({
    "asset_freshness", "asset_provenance_receipts", "asset_throughput", "build_run_assets", "build_runs",
    "ka_gochara_contact", "ka_gochara_eval_window", "ka_gochara_eval_window_record",
    "ka_gochara_eval_window_verification", "ka_gochara_record_prerequisite", "ka_gochara_relationship_record",
    "ka_gochara_search_input_snapshot", "ka_gochara_search_interval", "ka_gochara_search_inventory",
    "ka_gochara_search_inventory_verification", "ka_gochara_search_obligation", "ka_gochara_search_path_pin",
    "kala_gochara_coverage", "kala_gochara_publication", "owned_test_runs"})
TEARDOWN_KINDS = {"smalltest_teardown": "ky.smalltest_teardown/1", "measuring_teardown": "ky.measuring_teardown/1"}
ABSENCE_SCHEMA = "ky.smalltest_independent_absence/1"


def evidence_digest(value) -> str:
    """v5_small_test_shared.evidence_digest: sha256 of the sorted, compact JSON of the receipt (not of its file bytes)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _independent_acceptance(a: dict) -> bool:
    """v5_small_test_shared.independent_acceptance: a verifier lane, or the executor's mechanical pre-acceptance."""
    checks = a.get("checks")
    return a.get("by") in VERIFIER_LANES or (
        a.get("by") == "executor-mechanical" and a.get("schema") == MECHANICAL_SCHEMA and a.get("phase") == "pre"
        and isinstance(checks, dict) and bool(checks) and all(value is True for value in checks.values()))


def _absence_problem(committed: dict, absence: dict, accepted: dict, receipts: str) -> str | None:
    """Why `absence` (a readback_sql receipt) with its content acceptance `accepted` is not the independent absence
    of the committed teardown `committed`; None if it is. Mirrors executor.fence_quiescent ->
    smalltest_policy(...)["absence_evidence"](proof, OPS, teardown_receipt=committed)."""
    if (absence.get("kind") != "readback_sql" or absence.get("status") != "COMPLETED" or absence.get("exit_code") != 0
            or not absence.get("request_sha256") or not absence.get("reviewed_commit")):
        return "is not a COMPLETED readback_sql receipt"
    if (accepted.get("result") != "ACCEPTED" or not _independent_acceptance(accepted)
            or accepted.get("operation_id") != absence.get("operation_id")
            or accepted.get("request_sha256") != absence["request_sha256"]
            or accepted.get("reviewed_commit") != absence["reviewed_commit"]):
        return "has no independent ACCEPTED acceptance bound to its request"
    requester = absence.get("requested_by")
    if isinstance(requester, str) and accepted["by"].casefold() in (requester.strip().casefold(),
                                                                    (_actor_slot(requester) or "").casefold()):
        return "was accepted by its own requester"
    p = accepted.get("absence")
    output = absence.get("output_file")
    if not isinstance(p, dict) or not isinstance(output, str) or not output:
        return "has no accepted absence record or measured output"
    path = output if os.path.isabs(output) else os.path.join(receipts, output)
    if os.path.dirname(os.path.realpath(path)) != receipts:
        return "has an output outside run/ops/receipts"
    try:
        with open(path, "rb") as handle:
            body = handle.read()
        if hashlib.sha256(body).hexdigest() != absence.get("output_sha256"):
            return "has an output that differs from its output_sha256"
        records = list(csv.DictReader(io.StringIO(body.decode()), delimiter="\t"))
        measured = json.loads(records[0]["absence_proof"]) if len(records) == 1 else None
    except (OSError, ValueError, KeyError, UnicodeError):
        return "has an unreadable measured output (one JSON absence_proof column required)"
    if measured != {key: value for key, value in p.items() if key != "output_sha256"}:
        return "was accepted with an absence that differs from the measured readback output"
    counts = p.get("counts")
    if (p.get("schema") != ABSENCE_SCHEMA or p.get("registry_inert") is not True
            or p.get("output_sha256") != absence.get("output_sha256") or not isinstance(counts, dict)
            or not counts or any(type(n) is not int or n != 0 for n in counts.values())):
        return "is not a measured, scope-bound independent absence with every count zero"
    if not ABSENCE_CENSUS <= counts.keys():
        return "has an incomplete absence census"
    proof = committed.get("teardown") if isinstance(committed.get("teardown"), dict) else {}
    scope = proof.get("scope") if isinstance(proof.get("scope"), dict) else {}
    if (committed.get("kind") not in TEARDOWN_KINDS or proof.get("schema") != TEARDOWN_KINDS[committed["kind"]]
            or committed.get("exit_code") != 0 or committed.get("status") not in ("AWAITING_ABSENCE", "COMPLETED")
            or proof.get("status") != "COMMITTED_AWAITING_ABSENCE"
            or p.get("run_id") is None or p.get("run_id") != scope.get("run_id")
            or p.get("chart_id") != scope.get("chart_id") or p.get("generation") != scope.get("generation")
            or p.get("scope_sha256") != proof.get("scope_sha256") or p.get("rowset_sha256") != proof.get("rowset_sha256")
            or p.get("teardown_request_sha256") != committed.get("request_sha256")
            or p.get("teardown_operation_id") != committed.get("operation_id")
            or p.get("teardown_receipt_sha256") != evidence_digest(committed)
            or absence.get("operation_id") == committed.get("operation_id")):
        return "is not bound to this committed teardown receipt"
    try:
        if datetime.fromisoformat(absence["ts"]) <= datetime.fromisoformat(committed["ts"]):
            return "does not follow the committed teardown"
    except (KeyError, TypeError, ValueError):
        return "has no usable timestamp after the committed teardown"
    return None


def committed_teardown_absence_accepted(committed: dict, receipts: str) -> bool:
    """SR-TEARDOWN-COMPLETION: a teardown executor receipt is complete when it is COMMITTED (status AWAITING_ABSENCE,
    teardown_proof COMMITTED_AWAITING_ABSENCE, exit 0) AND an ACCEPTED absence receipt binds that receipt's
    evidence_digest, with no later staged launch (the same checks as executor.fence_quiescent -> absence_evidence).
    The absence receipt is found by its content acceptance run/ops/acceptance/<operation_id>.absence.json. Nothing is
    written; an unreadable file or a missing binding reads False."""
    if (not isinstance(committed, dict) or committed.get("status") != "AWAITING_ABSENCE"
            or committed.get("kind") not in TEARDOWN_KINDS):
        return False
    acceptance = os.path.join(os.path.dirname(receipts), "acceptance")
    try:
        later = []
        for name in sorted(os.listdir(receipts)):
            if name.endswith(".json"):
                old = _load(os.path.join(receipts, name), "receipt")
                if (old.get("kind") in ("smalltest_dispatch", "measuring_dispatch") and old.get("status") == "COMPLETED"
                        and old.get("launch") and datetime.fromisoformat(old["ts"]) > datetime.fromisoformat(committed["ts"])):
                    later.append(name)      # a later launch needs its own teardown and absence
        if later:
            return False
        candidates = [name for name in sorted(os.listdir(acceptance)) if name.endswith(".absence.json")]
    except (OSError, CompletionError, KeyError, TypeError, ValueError):
        return False
    for name in candidates:
        try:
            accepted = _load(os.path.join(acceptance, name), "absence acceptance")
            opid = accepted.get("operation_id")
            if (not isinstance(opid, str) or name != opid + ".absence.json"
                    or re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", opid) is None):
                continue
            absence = _load(os.path.join(receipts, opid + ".json"), "absence receipt")
            if _absence_problem(committed, absence, accepted, receipts) is None:
                return True
        except CompletionError:
            continue
    return False
