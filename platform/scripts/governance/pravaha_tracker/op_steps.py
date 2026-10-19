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

import json
import os
import re
import subprocess

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
