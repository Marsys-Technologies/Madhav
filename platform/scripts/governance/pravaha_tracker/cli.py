"""pravaha — the one command every participant uses to read and move the campaign.

The tracker is the work queue: a stream asks it what is ready (`next`), claims an item (`start`),
reports steps as it goes (`step`), and closes with evidence (`done`). Because the streams take their
work FROM the tracker, the tracker cannot fall behind the work.

  pravaha preflight --stream A                 session-start checks + heartbeat; exit≠0 → do not start work
  pravaha next      --stream A                 what A may start now (and what is running/blocked)
  pravaha status   [--stream A]                one-screen summary
  pravaha start     A2.1 --stream A [--detail ..]
  pravaha step      A2.1 aspect_direction --stream A [--evidence ..]   (a declaring model: --evidence <file>,
                                                                        recorded only once the step's detector passed)
  pravaha progress  A2.1 0.4 --stream A [--detail ..]
  pravaha review    A2.1 --stream A --detail "K3 review requested"
  pravaha done      A2.1 --stream A --evidence "PR #2760"
  pravaha block     A2.1 --stream A --detail "waiting for N-12"
  pravaha heartbeat --stream A --detail "running battery"
  pravaha metric    NAME VALUE --stream A [--detail ..]
  pravaha note      --stream A --detail ".."
  pravaha request   D-RQ1 --stream B --detail "packet at <path>"      (asks the native)
  pravaha decide    D-RQ1 --detail "what was decided" [--as steward]   (the native's ruling)

Message bus (no human relays messages):
  pravaha send      --to A|B|C --detail ".." [--file path] [--ref ITEM]   steward -> stream
  pravaha report    --stream A --detail ".." [--ref ITEM]             stream -> steward
  pravaha inbox     --stream A | --steward [--wait SECONDS] [--json]  unacked messages; --wait blocks
  pravaha ack       MSG_ID --stream A | --steward [--detail ..]       mark a message acted on

Stream from --stream or $PRAVAHA_STREAM. Exit codes: 0 ok · 2 refused (nothing written) ·
3 cannot write the event log (STOP work and tell the native) · 4 preflight failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker.events import EventError, append, actor_slot, actor_stream  # noqa: E402
from pravaha_tracker.claims import ClaimError, claim_item, renew_claim, release_claim  # noqa: E402
from pravaha_tracker.audit import audit  # noqa: E402
from pravaha_tracker.state import build_snapshot, load_closure, reconciliation_line  # noqa: E402
from pravaha_tracker.detectors import git_activity  # noqa: E402
from pravaha_tracker import merged_deployed  # noqa: E402
from pravaha_tracker.completion import COMPOSED_RECEIPT_SCHEMA, CompletionError, guarded_done_event  # noqa: E402
from pravaha_tracker.claims import _locked, _read, _append, _close  # noqa: E402
from pravaha_tracker.events import validate_against_model  # noqa: E402
from pravaha_tracker.verdicts import accepted_verdict  # noqa: E402
from pravaha_tracker.op_steps import (check_acceptance_file_evidence, check_lease_row_evidence,  # noqa: E402
                                      committed_teardown_absence_accepted, executor_acceptance)
from pravaha_tracker.op_steps import request_digest as _request_digest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
HOME = os.environ.get("PRAVAHA_HOME", "/Users/Dev/pravaha")
EVENTS = os.environ.get("PRAVAHA_EVENTS", os.path.join(HOME, "run", "EVENTS.jsonl"))
SNAPSHOT = os.path.join(HOME, "run", "snapshot.json")
MODEL = os.environ.get("PRAVAHA_PLAN_MODEL", os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "pravaha", "plan_model.json"))
URL = os.environ.get("PRAVAHA_URL", "http://127.0.0.1:" + os.environ.get("PRAVAHA_TRACKER_PORT", "8766"))


def hold_path() -> str:
    return os.environ.get("PRAVAHA_HOLD") or os.path.join(os.environ.get("PRAVAHA_HOME", HOME), "run", "PRAVAHA_HOLD")


def load_model() -> dict:
    with open(MODEL, encoding="utf-8") as f:
        return json.load(f)


def get(path: str, timeout: float = 3.0):
    """Ask the live tracker; fall back to the last persisted snapshot (and say so)."""
    try:
        with urllib.request.urlopen(URL + path, timeout=timeout) as r:  # noqa: S310
            return json.loads(r.read().decode()), "live"
    except Exception as exc:  # noqa: BLE001
        if path.startswith("/api/verify?"):
            # Guarded measurements never fall back to a persisted snapshot.
            reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
            if isinstance(reason, TimeoutError):
                return None, "tracker-timeout"
            # A received HTTP error or malformed reply is not a transport outage.
            if isinstance(exc, urllib.error.HTTPError) or not isinstance(reason, OSError):
                return None, "unavailable"
            return None, "tracker-unreachable"
        try:
            with open(SNAPSHOT, encoding="utf-8") as f:
                return {"_snapshot": json.load(f)}, "stale-snapshot"
        except (OSError, ValueError):
            return None, "unavailable"


def actor_for(a) -> str:
    if getattr(a, "as_", None):
        return a.as_
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).strip().upper()
    if not s:
        raise SystemExit("error: give --stream A|B (or set PRAVAHA_STREAM)")
    return f"stream-{s}"


def observe_containment(repo: str, merge: str) -> dict:
    """Find a SUCCESSFUL `Deploy to Cloud Run` run on main whose deployed sha contains `merge`.

    Only runs triggered by `workflow_run` are trusted: for them DEPLOY_SHA equals the run's head sha (deploy.yml);
    a `workflow_dispatch` run may deploy a different sha than its head (Trap 103) and is ignored here.
    """
    out = {"deployed_sha": None, "run_id": None, "contains_merge": False}
    try:
        subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=repo, capture_output=True, timeout=60, check=False)
        proc = subprocess.run(["gh", "run", "list", "--workflow", "Deploy to Cloud Run", "--branch", "main",
                               "--status", "success", "--limit", "15", "--json", "databaseId,headSha,event,createdAt"],
                              cwd=repo, capture_output=True, text=True, timeout=60, check=False)
        if proc.returncode:
            return out
        try:
            runs = json.loads(proc.stdout or "[]")
        except ValueError:
            return out
        for run in (runs if isinstance(runs, list) else []):
            if not isinstance(run, dict) or run.get("event") != "workflow_run":
                continue
            sha = run.get("headSha") or ""
            anc = subprocess.run(["git", "merge-base", "--is-ancestor", merge, sha], cwd=repo,
                                 capture_output=True, text=True, timeout=30, check=False)
            if anc.returncode == 0:
                return {"deployed_sha": sha, "run_id": run.get("databaseId"), "contains_merge": True,
                        "deployed_at": run.get("createdAt")}
    except (OSError, ValueError, subprocess.SubprocessError):
        return out
    return out


def cmd_claim_lifecycle(a) -> int:
    """Claims always read the locked event log; the dashboard snapshot is never authority."""
    try:
        model = load_model()
        worker = a.worker or os.environ.get("KY_LANE", "")
        if not worker:
            raise ClaimError("worker id is required")
        if a.cmd == "claim":
            stream = (a.stream or os.environ.get("PRAVAHA_STREAM") or os.environ.get("KY_STREAM") or "").upper()
            event = claim_item(EVENTS, model, a.item, stream, worker, a.lease,
                               branch=a.branch, head=a.head, step=a.step)
        else:
            record = os.path.join(os.path.dirname(EVENTS), "claims", worker + ".json")
            with open(record, encoding="utf-8") as handle:
                current = json.load(handle)
            if a.cmd == "renew":
                event = renew_claim(EVENTS, model, current["item"], worker, current["claim_id"],
                                    a.lease, branch=a.branch, head=a.head, step=a.step)
            else:
                event = release_claim(EVENTS, current["item"], worker, current["claim_id"])
        print(json.dumps(event, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, ClaimError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


def write(ev: dict) -> int:
    try:
        model = load_model()
    except (OSError, ValueError) as exc:
        print(f"refused: cannot read the plan model ({exc})", file=sys.stderr)
        return 2
    try:
        event = {k: v for k, v in ev.items() if v not in (None, "")}
        lane = os.environ.get("KY_LANE", "").strip()
        if (model.get("control_plane", {}).get("verdict_stream") and lane
                and str(event.get("actor", "")).startswith("stream-")
                and ":" not in event["actor"]):
            event["actor"] += f":{lane}"
        out = append(EVENTS, event, model)
    except EventError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"CANNOT WRITE THE EVENT LOG ({exc}). Stop work and tell the native — "
              "work that cannot be seen on the tracker must not continue.", file=sys.stderr)
        return 3
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_transition(a, actor: str) -> int:
    """Reopen a review/failure or unblock a hold under the event-log lock."""
    try:
        model = load_model()
        if not model.get("control_plane", {}).get("guarded_completion"):
            raise EventError("explicit transitions require the guarded control plane")
        if not a.detail.strip():
            raise EventError("a transition needs a reason")
        item = next((row for row in model["items"] if row["id"] == a.item), None)
        if item is None:
            raise EventError(f"unknown item {a.item!r}")
        event = {"kind": "item", "actor": actor, "item": a.item, "state": "ready",
                 "detail": a.detail.strip(), "transition": a.cmd}
        validate_against_model(event, model)
        fd = _locked(EVENTS)
        try:
            events = _read(fd)
            history = [e for e in events if e.get("kind") == "item" and
                       e.get("item") == a.item and not e.get("step")]
            if any(e.get("state") == "done" and e.get("guarded") is True for e in history):
                raise EventError("a guarded completion is durable")
            current = history[-1].get("state") if history else None
            allowed = {"unblock": {"blocked", "parked"},
                       "reopen": {"failed", "review"}}[a.cmd]
            if current not in allowed:
                raise EventError(f"{a.cmd} requires {', '.join(sorted(allowed))}; current state is {current}")
            out = _append(fd, event)
        finally:
            _close(fd)
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except (EventError, OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


def observe_derived_done(model: dict, events: list[dict], item_id: str, repo: str) -> dict:
    """The display's merged+deployed derivation for `item_id` and its upstream, read live (SR-BOLD-07).
    Read before the event-log lock is taken: it calls GitHub. A failed read derives fewer items, never more."""
    src = merged_deployed.GitHubSource(repo)
    src.refresh()
    return merged_deployed.derive_for_events(model, events, src, only=merged_deployed.upstream_ids(model, item_id) - {item_id})


def cmd_guarded_done(a, actor: str) -> int:
    """Obtain live observations, then check and append under the event-log lock."""
    try:
        model = load_model()
        item = next(row for row in model["items"] if row["id"] == a.item)
        timeout = float(os.environ.get("KY_VERIFY_TIMEOUT_S", "300"))
        if not math.isfinite(timeout) or timeout <= 0:
            raise CompletionError("KY_VERIFY_TIMEOUT_S must be a positive finite number")
        for attempt in range(4):
            observed, via = get("/api/verify?id=" + quote(a.item, safe=""), timeout=timeout)
            # Stop on any reply or timeout: a retry must never replace a failed verdict.
            if via != "tracker-unreachable" or attempt == 3:
                break
            time.sleep(2 ** (attempt + 1))  # 2/4/8s; at most 14s beyond request timeouts.
        if via == "tracker-timeout":
            raise CompletionError(f"tracker timed out after {timeout:g}s during live detector verification")
        if via == "tracker-unreachable":
            raise CompletionError("tracker unreachable during live detector verification")
        if via != "live" or not isinstance(observed, dict) or observed.get("item") != a.item:
            raise CompletionError("live detector verification is unavailable")
        detector = observed.get("detector") or {}
        evidence_options = (a.pr is not None, bool(a.artifact_path),
                            bool(a.operation_receipt), bool(a.packet_verdict))
        if sum(evidence_options) != 1:
            raise CompletionError("give exactly one typed evidence source")
        if a.pr is not None:
            if not a.reviewed_head:
                raise CompletionError("code completion needs --reviewed-head")
            proc = subprocess.run(["gh", "pr", "view", str(a.pr), "--json",
                                   "number,state,headRefOid,mergeCommit"],
                                  cwd=os.environ.get("PRAVAHA_REPO", REPO_ROOT),
                                  capture_output=True, text=True, timeout=30, check=False)
            if proc.returncode:
                raise CompletionError("GitHub PR observation failed")
            repo = os.environ.get("PRAVAHA_REPO", REPO_ROOT)
            proof = {"type": "code", "reviewed_head": a.reviewed_head, "pr": json.loads(proc.stdout), "repo": repo}
            merge = ((proof["pr"].get("mergeCommit") or {}).get("oid") or "")
            if merge:
                proof["deploy"] = observe_containment(repo, merge)
        elif a.artifact_path:
            declared = item.get("detector", {}).get("path")
            if os.path.realpath(a.artifact_path) != os.path.realpath(declared or ""):
                raise CompletionError("artifact path does not match the declared detector")
            with open(a.artifact_path, "rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            proof = {"type": "artifact", "artifact_digest": digest, "path": os.path.realpath(a.artifact_path)}
        elif a.operation_receipt:
            declared = item.get("detector", {}).get("path")
            if os.path.realpath(a.operation_receipt) != os.path.realpath(declared or ""):
                raise CompletionError("operation receipt path does not match the declared detector")
            with open(a.operation_receipt, "rb") as handle:
                raw = handle.read()
            receipt = json.loads(raw)
            proof = {"type": "operation", "artifact_digest": hashlib.sha256(raw).hexdigest(),
                     "operation_id": a.operation_id, "receipt": receipt,
                     "path": os.path.realpath(a.operation_receipt)}
            if isinstance(receipt, dict) and receipt.get("schema") == COMPOSED_RECEIPT_SCHEMA:
                # Same admission as `ky step` (#3716): every cited component must verify; completion.py then
                # accepts the composed receipt as the item's completed receipt (the accepted verdict at its
                # digest is still required there).
                if not isinstance(a.operation_id, str) or not a.operation_id:
                    raise CompletionError("composed operation receipt needs --operation-id")
                _check_composed_components(receipt, a.operation_id, _ANY_STEP, a.item, _ops_dir())
                proof["composed_components_verified"] = True
        elif a.packet_verdict:
            declared = item.get("detector", {}).get("path")
            if os.path.realpath(a.packet_verdict) != os.path.realpath(declared or ""):
                raise CompletionError("packet verdict path does not match the declared detector")
            with open(a.packet_verdict, "rb") as handle:
                raw = handle.read()
            packet = json.loads(raw)
            review_path = packet.get("review_path")
            if (not isinstance(review_path, str) or
                    os.path.dirname(os.path.realpath(review_path)) != os.path.dirname(os.path.realpath(a.packet_verdict))):
                raise CompletionError("packet review must be an existing file beside the verdict")
            with open(review_path, "rb") as handle:
                review_digest = hashlib.file_digest(handle, "sha256").hexdigest()
            proof = {"type": "packet", "artifact_digest": hashlib.sha256(raw).hexdigest(),
                     "packet": packet, "review_sha256": review_digest,
                     "path": os.path.realpath(a.packet_verdict)}
        else:
            raise CompletionError("typed evidence is required")
        derived = observe_derived_done(model, _read_events(), a.item, os.environ.get("PRAVAHA_REPO", REPO_ROOT))
        fd = _locked(EVENTS)
        try:
            event = guarded_done_event(model, _read(fd), a.item, actor, detector, proof, derived_done=derived)
            validate_against_model(event, model)
            written = _append(fd, event)
        finally:
            _close(fd)
        print(json.dumps(written, ensure_ascii=False))
        return 0
    except (CompletionError, OSError, ValueError, KeyError, StopIteration,
            subprocess.TimeoutExpired) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


def _declared_artifact(item_row: dict | None) -> str | None:
    """The file an artifact item's own completion detector measures (a file_exists on run/residuals/...), else None."""
    if not isinstance(item_row, dict) or item_row.get("completion_kind") != "artifact":
        return None
    detector = item_row.get("detector")
    declared = detector.get("path") if isinstance(detector, dict) and detector.get("type") == "file_exists" else None
    return declared if isinstance(declared, str) and declared else None


def _repo_artifact_bytes(repo: str, pinned: dict) -> bytes:
    """The bytes of a step's pinned repository-file artifact (SR-J3D-REPORT-STEP).

    The step spec pins {repo_path, blob, sha256}. The bytes are read from the git object store by blob id, never
    from a working tree: a blob id is a content address, so a dirty or stale checkout (or a branch that has since
    moved) can neither fake nor lose the reviewed bytes, and the sha256 is then checked against the pin."""
    blob, pin = pinned.get("blob"), pinned.get("sha256")
    if (not isinstance(blob, str) or re.fullmatch(r"[0-9a-f]{40}", blob) is None
            or not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None
            or not isinstance(pinned.get("repo_path"), str) or not pinned["repo_path"]):
        raise CompletionError("step artifact pin needs repo_path, a 40-hex blob and a 64-hex sha256")
    done = subprocess.run(["git", "-C", repo, "cat-file", "blob", blob], capture_output=True, timeout=60)
    if done.returncode != 0:
        raise CompletionError(f"pinned artifact blob {blob} is not in the repository")
    if hashlib.sha256(done.stdout).hexdigest() != pin:
        raise CompletionError("pinned artifact blob does not match its pinned sha256")
    return done.stdout


def _check_step_receipt(raw: bytes, path: str, spec: dict, item: str, step: str, *, operation: bool = False,
                        declared_artifact: str | None = None, repo_artifact: dict | None = None,
                        repo: str | None = None) -> dict:
    """Bind a file_contains step to the canonical receipt and its source evidence.

    A step whose evidence is a repository file (`repo_artifact`, the step's pinned {repo_path, blob, sha256}) takes
    its artifact_sha256 from that pin alone: the receipt must carry it, must name no artifact_path, and the digest
    is checked against the pinned blob's bytes.

    An artifact_section receipt carries no artifact_path (the plan model's pattern admits only artifact_sha256,
    item, review_job, step, verdict): its artifact_sha256 is checked against `declared_artifact`, the very file
    the item's own detector measures. An explicit artifact_path is accepted only when it is that same file."""
    declared_path = spec.get("path")
    if (not isinstance(declared_path, str) or not declared_path
            or os.path.realpath(path) != os.path.realpath(declared_path)):
        raise CompletionError("step evidence path does not match the declared receipt")
    receipt = json.loads(raw)
    if not isinstance(receipt, dict):
        raise CompletionError("step receipt must be a canonical JSON object")
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if raw not in (canonical, canonical + b"\n"):
        raise CompletionError("step receipt must use canonical JSON (sorted keys, no spaces or duplicate fields)")
    if receipt.get("item") != item or receipt.get("step") != step:
        raise CompletionError("step receipt item/step does not match the command")
    if operation and (receipt.get("verdict") != "MET" or not receipt.get("review_job")):
        raise CompletionError("operation step requires a named independent MET review")

    artifact_bound = False
    if repo_artifact is not None:
        if "artifact_path" in receipt or "artifact_sha256" not in receipt:
            raise CompletionError("repository-file artifact step needs artifact_sha256 and no artifact_path")
        digest = hashlib.sha256(_repo_artifact_bytes(repo or REPO_ROOT, repo_artifact)).hexdigest()
        if receipt["artifact_sha256"] != digest:
            raise CompletionError("step receipt artifact_sha256 does not match its artifact")
        artifact_bound = True
    elif "artifact_sha256" in receipt:
        artifact = receipt.get("artifact_path")
        if declared_artifact and artifact is None:
            artifact = declared_artifact
        elif not isinstance(artifact, str) or not artifact:
            raise CompletionError("step receipt artifact_sha256 needs an artifact_path")
        elif not os.path.isabs(artifact):
            artifact = os.path.join(os.path.dirname(os.path.realpath(path)), artifact)
        if declared_artifact and os.path.realpath(artifact) != os.path.realpath(declared_artifact):
            raise CompletionError("step receipt artifact_path is not the item's declared artifact")
        with open(artifact, "rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if receipt["artifact_sha256"] != digest:
            raise CompletionError("step receipt artifact_sha256 does not match its artifact")
        artifact_bound = True

    if "review_job" in receipt:
        job = receipt["review_job"]
        if (not isinstance(job, str) or not job or job in (".", "..")
                or "/" in job or "\\" in job):
            raise CompletionError("step receipt review_job must name a single job directory")
        jobs = os.path.realpath(os.environ.get(
            "PRAVAHA_REVIEW_JOBS", "/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs"))
        result_path = os.path.realpath(os.path.join(jobs, job, "result.json"))
        if os.path.commonpath((jobs, result_path)) != jobs:
            raise CompletionError("step receipt review_job result escapes the jobs directory")
        with open(result_path, encoding="utf-8") as handle:
            result = json.load(handle)
        batched = isinstance(result, dict) and "items" in result
        if batched:
            items = result["items"]
            matching_items = ([row for row in items if isinstance(row, dict) and row.get("item") == item]
                              if isinstance(items, list) else [])
            if len(matching_items) != 1:
                raise CompletionError("step receipt review result does not match the item")
            result = matching_items[0]
        if not isinstance(result, dict) or result.get("item") != item:
            raise CompletionError("step receipt review result does not match the item")
        steps = result.get("steps")
        matching = ([row for row in steps if isinstance(row, dict) and row.get("step") == step]
                    if isinstance(steps, list) else [])
        # Artifact hashes remain an alternative only for legacy single-item results.
        if (operation or batched or not artifact_bound) and (len(matching) != 1 or matching[0].get("verdict") != "MET"):
            raise CompletionError("step receipt review result does not say MET for this step")
    return receipt


def _teardown_completed(executor: dict, receipts: str, digest: str) -> bool:
    """A committed production teardown stays AWAITING_ABSENCE by design (fleet/executor.py: the
    COMMITTED_AWAITING_ABSENCE proof sets that status). It counts as complete when the executor has published
    <op>.completion.json (_teardown_completion_published), or (SR-TEARDOWN-COMPLETION) while that is not yet
    published, when the receipt is COMMITTED (exit 0, teardown proof COMMITTED_AWAITING_ABSENCE) and an ACCEPTED
    absence receipt binds its evidence_digest (op_steps.committed_teardown_absence_accepted mirrors the executor's
    own absence_evidence check)."""
    return (_teardown_completion_published(executor, receipts, digest)
            or committed_teardown_absence_accepted(executor, receipts))


def _teardown_completion_published(executor: dict, receipts: str, digest: str) -> bool:
    """The executor published <op>.completion.json after the separate absence readback was accepted: status
    COMPLETED, the same operation and request, the digest of this very receipt, and the digest of the named
    absence receipt.

    (I) INTERPRETATION: commit_receipt_sha256 is also bound to this receipt's bytes (the executor writes
    digest_bytes of the commit receipt there); the alternative of checking only the fields named in the
    job brief would let a receipt edited after completion pass.
    """
    opid = executor["operation_id"]
    if (executor.get("status") != "AWAITING_ABSENCE"
            or executor.get("kind") not in ("smalltest_teardown", "measuring_teardown")):
        return False
    path = os.path.join(receipts, opid + ".completion.json")
    try:
        if os.path.realpath(path) != path:
            return False
        with open(path, encoding="utf-8") as handle:
            completion = json.load(handle)
        absence = completion.get("absence_receipt")
        name = absence.get("name") if isinstance(absence, dict) else None
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9_.-]+\.json", name) is None:
            return False
        absence_path = os.path.join(receipts, name)
        if os.path.realpath(absence_path) != absence_path:
            return False
        with open(absence_path, "rb") as handle:
            absence_digest = hashlib.sha256(handle.read()).hexdigest()
    except (OSError, ValueError, AttributeError):
        return False
    return (isinstance(completion, dict) and completion.get("status") == "COMPLETED"
            and completion.get("operation_id") == opid
            and completion.get("request_sha256") == executor.get("request_sha256")
            and completion.get("commit_receipt_sha256") == digest
            and absence.get("sha256") == absence_digest)


_ANY_STEP = object()    # guarded completion records no step: the composed receipt's own step is not compared
_COMPOSED_RUN_PARTS = ("dispatch", "terminal", "execution_readback", "absence")


def _ops_dir() -> str:
    return os.path.realpath(os.path.join(os.environ.get("PRAVAHA_HOME", HOME), "run", "ops"))


def _check_composed_components(composed: dict, opid: str, step, item_id: str, ops: str) -> None:
    """Verify a COMPOSED operation receipt (SR-J2A-A55I-1/-ORDER: J-2d-a55i.json has no status, kind or
    request of its own) by its components.

    Every component is cited by name + sha256 and must exist byte-identical under run/ops/receipts (or
    run/ops/acceptance); every cited executor receipt must be COMPLETED (or a committed teardown whose
    completion is published) with exit 0 and the cited operation_id.

    (I) INTERPRETATION: the composed receipt has no request or requester of its own, so only the signer's
    stream and slot are checked for it (each component carries its own acceptance); each run must cite
    dispatch, terminal, execution_readback and an absence receipt WITH accepted evidence.
    """
    receipts = os.path.join(ops, "receipts")
    acceptance = os.path.join(ops, "acceptance")
    runs = composed.get("runs")
    if (composed.get("item") != item_id or composed.get("operation_id") != opid
            or (step is not _ANY_STEP and composed.get("step") != step) or not isinstance(runs, list) or not runs):
        raise CompletionError("composed operation receipt does not name this item, operation and step")

    def digest_of(directory: str, name, expected) -> bytes:
        if (not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9_.-]+\.json", name) is None
                or not isinstance(expected, str)):
            raise CompletionError("composed operation receipt cites a malformed component")
        path = os.path.join(directory, name)
        if os.path.realpath(path) != path:
            raise CompletionError("composed component escapes its run/ops directory")
        try:
            with open(path, "rb") as handle:
                body = handle.read()
        except OSError as exc:
            raise CompletionError(f"composed component {name} is not present ({exc.strerror})") from exc
        if hashlib.sha256(body).hexdigest() != expected:
            raise CompletionError(f"composed component {name} differs from the digest it is cited by")
        return body

    for run in runs:
        if not isinstance(run, dict) or any(not isinstance(run.get(part), dict) for part in _COMPOSED_RUN_PARTS):
            raise CompletionError("composed operation receipt lacks a run's dispatch/terminal/execution/absence")
        if any("receipt" not in run[part] for part in _COMPOSED_RUN_PARTS):
            raise CompletionError("composed operation receipt cites no executor receipt for a run part")
        for part, cite in run.items():
            if not isinstance(cite, dict) or "receipt" not in cite:
                continue
            ref = cite["receipt"] if isinstance(cite["receipt"], dict) else {}
            component_id = cite.get("operation_id")
            if not isinstance(component_id, str) or ref.get("name") != component_id + ".json":
                raise CompletionError("composed component receipt must be named after its operation_id")
            body = digest_of(receipts, ref.get("name"), ref.get("sha256"))
            component = json.loads(body)
            if (not isinstance(component, dict) or component.get("operation_id") != component_id
                    or type(component.get("exit_code")) is not int or component["exit_code"] != 0
                    or component.get("output_sha256") != cite.get("output_sha256")
                    or not (component.get("status") == "COMPLETED"
                            or _teardown_completed(component, receipts, ref["sha256"]))):
                raise CompletionError(f"composed component {component_id} is not a COMPLETED executor receipt with exit 0")
            accepted = cite.get("acceptance")
            if not isinstance(accepted, list) or (part == "absence" and not accepted):
                raise CompletionError(f"composed component {component_id} cites no accepted evidence")
            for entry in accepted:
                entry = entry if isinstance(entry, dict) else {}
                record = json.loads(digest_of(acceptance, entry.get("name"), entry.get("sha256")))
                if (not isinstance(record, dict) or record.get("result") != "ACCEPTED"
                        or record.get("operation_id") != component_id):
                    raise CompletionError(f"composed component {component_id} cites an acceptance that is not ACCEPTED for it")


def _check_operation_step(receipt: dict, item: dict, model: dict, events: list[dict]) -> None:
    """Check the executor's receipt, archived request, measured output and independent acceptance.

    (I) INTERPRETATION: request_id is the executor's request filename stem. The executor
    moves <operation_id>.json to ops/done and hashes the complete request without its
    acceptance_receipt, expires_at and *_expires_at fields (fleet/executor.py:request_digest, A8 §3.9).
    Acceptance is the latest artifact verdict at the executor receipt's digest, as in
    guarded operation completion; a review job's MET marker alone has no signer identity.
    Failing that (SR-OP-STEPS-2), the executor's OWN recorded acceptance for this operation is read directly
    (op_steps.executor_acceptance); no verdict event is ever synthesised. (I) INTERPRETATION: a composed
    receipt has no request digest of its own, so only the verdict path applies to it.
    """
    opid, request_id = receipt.get("operation_id"), receipt.get("request_id")
    if (not isinstance(opid, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", opid) is None
            or opid in (".", "..") or request_id != opid):
        raise CompletionError("operation step must name the same executor operation and request")
    ops = _ops_dir()
    receipts = os.path.join(ops, "receipts")
    path = os.path.join(receipts, opid + ".json")
    if os.path.realpath(path) != path:
        raise CompletionError("operation receipt escapes run/ops/receipts")
    with open(path, "rb") as handle:
        raw = handle.read()
    digest = hashlib.sha256(raw).hexdigest()
    if receipt.get("evidence_sha256") != digest:
        raise CompletionError("operation step evidence_sha256 does not match the executor receipt")
    executor = json.loads(raw)
    composed = isinstance(executor, dict) and executor.get("schema") == COMPOSED_RECEIPT_SCHEMA
    if not composed and (not isinstance(executor, dict) or executor.get("operation_id") != opid
            or executor.get("item_id") != item["id"]
            or type(executor.get("exit_code")) is not int or executor["exit_code"] != 0
            or not (executor.get("status") == "COMPLETED"
                    or _teardown_completed(executor, receipts, digest))):
        raise CompletionError("operation step requires this item's COMPLETED executor receipt with exit 0")

    if composed:
        _check_composed_components(executor, opid, receipt.get("step"), item["id"], ops)
        requesters = []
    else:
        request_path = os.path.join(ops, "done", request_id + ".json")
        if os.path.realpath(request_path) != request_path:
            raise CompletionError("operation request escapes run/ops/done")
        with open(request_path, encoding="utf-8") as handle:
            request = json.load(handle)
        if not isinstance(request, dict):
            raise CompletionError("operation request must be a JSON object")
        request_digest = _request_digest(request)    # executor.request_digest, A8 §3.9
        requester = request.get("requested_by")
        if (not isinstance(requester, str) or not requester.strip()
                or any(request.get(key) != executor.get(key)
                       for key in ("operation_id", "item_id", "requested_by", "kind", "reviewed_commit", "kyd"))
                or executor.get("request_sha256") != request_digest
                or receipt.get("request_sha256", request_digest) != request_digest):
            raise CompletionError("operation receipt does not bind the complete request and requester")

        output = executor.get("output_file")
        if not isinstance(output, str) or not output:
            raise CompletionError("operation receipt has no measured output file")
        if not os.path.isabs(output):
            output = os.path.join(receipts, output)
        if os.path.dirname(os.path.realpath(output)) != receipts:
            raise CompletionError("operation output escapes run/ops/receipts")
        with open(output, "rb") as handle:
            body = handle.read()
        if not body or hashlib.sha256(body).hexdigest() != executor.get("output_sha256"):
            raise CompletionError("operation output_sha256 does not match its measured output")
        requesters = [requester]

    verdict = accepted_verdict(events, item["id"], artifact_digest=digest, phase="artifact")
    signer = verdict.get("actor", "") if verdict else ""
    slot = actor_slot(signer)
    # A requester may be a role, a bare slot, or a stream-qualified slot. Compare
    # slots as well as actor strings so switching stream prefixes cannot self-accept.
    if (not verdict or actor_stream(signer) != model.get("control_plane", {}).get("verdict_stream")
            or not slot or any(signer.strip().casefold() == requester.strip().casefold()
                               or slot.casefold() == (actor_slot(requester) or requester.strip()).casefold()
                               for requester in requesters)):
        if composed:
            raise CompletionError("operation step needs independent acceptance at the executor receipt digest")
        latest = next((ev for ev in reversed(events) if ev.get("kind") == "verdict" and ev.get("item") == item["id"]
                       and ev.get("phase") == "artifact" and ev.get("head") is None
                       and ev.get("artifact_digest") == digest), None)
        if latest and latest.get("result") != "ACCEPTED":    # a recorded rejection at this digest revokes acceptance
            raise CompletionError(f"the independent verdict at the executor receipt digest is {latest.get('result')!r}")
        executor_acceptance(ops, opid, request_digest, digest, executor, requesters)
        return
    validate_against_model(verdict, model, events)


def cmd_step(a, actor: str) -> int:
    """Record a step. In a model that declares its items (relaunch plan v2.7 §6 STEP) only after the step's own
    named detector passed in the live tracker, with the evidence file's absolute path and SHA-256."""
    try:
        model = load_model()
    except (OSError, ValueError) as exc:
        print(f"refused: cannot read the plan model ({exc})", file=sys.stderr)
        return 2
    if not isinstance(model.get("control_plane", {}).get("declarations"), dict):
        return write({"kind": "item", "actor": actor, "item": a.item, "state": "done", "step": a.step_name,
                      "detail": a.detail, "evidence": a.evidence or f"step {a.step_name} reported by {actor}"})
    try:
        item = next((row for row in model.get("items", []) if row["id"] == a.item), None)
        if item is None or a.step_name not in item.get("steps", []):
            raise CompletionError(f"{a.item} declares no step {a.step_name!r}")
        declared = item.get("step_evidence", {}).get(a.step_name)
        spec = declared.get("detector") if isinstance(declared, dict) else None
        if not isinstance(spec, dict) or not spec:
            raise CompletionError(f"step {a.step_name} has no named detector; it cannot be recorded")
        # Plan v2.7 §6 STEP / §N.8: a code prerequisite may cite executor
        # provenance while its live DB detector measures the production fact.
        # Actual operation items still require independently bound receipts.
        operation = item.get("completion_kind") == "operation" or (
            declared.get("evidence") == "executor_receipt" and spec.get("type") != "db_query")
        # SR-J3D-REPORT-STEP: a step whose evidence is a repository file is an artifact_section step even on an
        # operation item; it carries no executor receipt, so the executor-receipt binding below does not apply.
        repo_artifact = declared.get("artifact") if declared.get("evidence") == "artifact_section" else None
        if repo_artifact is not None and not isinstance(repo_artifact, dict):
            raise CompletionError("step artifact pin must be a mapping")
        lease_row = declared.get("evidence") == "lease_row"    # SR-OP-STEPS item 2: a ledger read, no verdict
        acceptance_file = declared.get("evidence") == "acceptance_file"    # pre_acceptance: the executor's acceptance record
        ledger = lease_row or acceptance_file
        if (operation or ledger) and spec.get("type") != "file_contains":
            raise CompletionError("operation step requires a canonical file_contains acceptance receipt")
        if not a.evidence or not os.path.isfile(a.evidence):
            raise CompletionError("step evidence must be an existing file (--evidence <path>)")
        observed, via = get("/api/verify?id=" + quote(a.item, safe="") + "&step=" + quote(a.step_name, safe=""),
                            timeout=90)
        if (via != "live" or not isinstance(observed, dict) or observed.get("item") != a.item
                or observed.get("step") != a.step_name or observed.get("spec") != spec):
            raise CompletionError("live verification of the step detector is unavailable")
        if (observed.get("detector") or {}).get("status") != "done":
            raise CompletionError(f"the detector of step {a.step_name} has not passed")
        path = os.path.abspath(a.evidence)
        with open(path, "rb") as handle:
            if ledger:
                raw = handle.read()
                if lease_row:
                    check_lease_row_evidence(raw, path, spec, a.item, a.step_name,
                                             os.environ.get("PRAVAHA_REPO", REPO_ROOT))
                else:
                    check_acceptance_file_evidence(raw, path, spec, a.item, a.step_name, _ops_dir())
                digest = hashlib.sha256(raw).hexdigest()
            elif spec.get("type") == "file_contains":
                raw = handle.read()
                receipt = _check_step_receipt(raw, path, spec, a.item, a.step_name, operation=operation,
                                              declared_artifact=_declared_artifact(item),
                                              repo_artifact=repo_artifact,
                                              repo=os.environ.get("PRAVAHA_REPO", REPO_ROOT))
                digest = hashlib.sha256(raw).hexdigest()
            else:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
        event = {"kind": "item", "actor": actor, "item": a.item, "state": "done", "step": a.step_name,
                 "detail": a.detail, "evidence": path, "evidence_sha256": digest}
        if (operation and repo_artifact is None) or ledger:
            # Check the current verdict and append under the same lock: a concurrent
            # rejection must not be lost between acceptance lookup and step recording.
            if not os.path.isfile(EVENTS):
                raise CompletionError("operation step has no independent acceptance history")
            fd = _locked(EVENTS)
            try:
                events = _read(fd)
                if not ledger:    # the lease row / acceptance record was read from its ledger above
                    _check_operation_step(receipt, item, model, events)
                lane = os.environ.get("KY_LANE", "").strip()
                if (model.get("control_plane", {}).get("verdict_stream") and lane
                        and actor.startswith("stream-") and ":" not in actor):
                    event["actor"] += f":{lane}"
                validate_against_model(event, model, events)
                written = _append(fd, event)
            finally:
                _close(fd)
            print(json.dumps(written, ensure_ascii=False))
            return 0
    except (CompletionError, EventError, OSError, ValueError, AttributeError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return write({"kind": "item", "actor": actor, "item": a.item, "state": "done", "step": a.step_name,
                  "detail": a.detail, "evidence": path, "evidence_sha256": digest})


def _items_from(res) -> list[dict]:
    snap = res.get("_snapshot") if isinstance(res, dict) and "_snapshot" in res else None
    if snap:
        return [t for tr in snap.get("tracks", []) for t in tr["items"]]
    return []


def cmd_next(a) -> int:
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).upper()
    res, via = get(f"/api/next?stream={s}")
    if res is None:
        print("tracker unreachable and no snapshot on disk", file=sys.stderr)
        return 3
    if via != "live":
        flat = [t for t in _items_from(res) if not s or t.get("owner") == s]
        res = {"running": [t for t in flat if t["status"] in ("running", "review")],
               "ready": [t for t in flat if t["status"] == "ready"],
               "blocked": [t for t in flat if t["status"] in ("blocked", "failed", "parked", "conflict")]}
        print(f"WARNING: tracker not reachable — showing the last saved snapshot. Start it: launchctl kickstart -k gui/$(id -u)/com.madhav.pravaha.tracker", file=sys.stderr)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    for label in ("running", "ready", "blocked"):
        rows = res.get(label, [])
        print(f"{label.upper()} ({len(rows)})")
        for t in rows:
            extra = f" — {t.get('detail')}" if t.get("detail") else ""
            print(f"  {t['id']:<8} {t['title']}{extra}")
    return 0


def cmd_status(a) -> int:
    res, via = get("/api/state")
    snap = res.get("_snapshot") if (res and "_snapshot" in res) else res
    if not snap:
        print("tracker unreachable and no snapshot on disk", file=sys.stderr)
        return 3
    o = snap["overall"]
    scope = " (closure)" if o.get("scope") == "closure" else ""
    print(f"{snap.get('campaign')} — {o['pct']}% · done {o['done']}/{o['total']}{scope} · running {o['running']} · ready {o['ready']} · "
          f"blocked {o['blocked']} · unmeasured {o['unknown']}   [{via}, v{snap.get('version')}]")
    if o.get("reconciliation") and not a.stream:
        print("  " + reconciliation_line(o["reconciliation"]))
    for st in snap.get("streams", []):
        if a.stream and st["id"] != a.stream.upper():
            continue
        hb = st.get("heartbeat") or {}
        g = st.get("git") or {}
        print(f"  Stream {st['id']} ({st.get('name')}) · {st['liveness']} · {st['done']}/{st['total']} done · "
              f"heartbeat {int(hb['age_s'])}s ago" if hb.get("age_s") is not None else f"  Stream {st['id']} ({st.get('name')}) · {st['liveness']} · no heartbeat yet")
        for t in st.get("running", []):
            print(f"     running  {t['id']} {t['title']}")
        if g.get("subject"):
            print(f"     last commit {g.get('last_commit')} on {g.get('branch')}: {g.get('subject')}")
    if o.get("deferred") and not a.stream:
        print(f"  Deferred (not counted): {', '.join(d['id'] for d in o['deferred'])}")
    nq = snap.get("native_queue", [])
    if nq and not a.stream:
        print(f"  Native decisions open: {', '.join(d['id'] for d in nq)}")
    return 0


def cmd_preflight(a) -> int:
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).upper()
    problems = []
    try:
        model = load_model()
    except (OSError, ValueError) as exc:
        print(f"FAIL plan model unreadable: {exc}")
        return 4
    stream = next((x for x in model.get("streams", []) if x["id"] == s), None)
    if not stream:
        print(f"FAIL unknown stream {s!r}")
        return 4
    h, via = get("/api/health")
    if via != "live" or not h or not h.get("ok", False):
        problems.append("tracker is not live on " + URL)
    cwd = os.path.realpath(os.getcwd())
    wts = [os.path.realpath(w) for w in stream.get("worktrees", [])]
    wt = next((w for w in wts if cwd == w or cwd.startswith(w + os.sep)), None)
    if wts and wt is None:
        problems.append(f"you are in {cwd}, but Stream {s} works in one of: {', '.join(wts)}")
    act = git_activity(wt) if wt else {}
    want = stream.get("branch_pattern")
    # Between claims a lane intentionally sits at detached origin/main.
    worker = os.environ.get("KY_LANE", "")
    claim_file = os.path.join(HOME, "run", "claims", worker + ".json") if worker else ""
    active_claim = False
    if claim_file and os.path.exists(claim_file):
        try:
            with open(claim_file, encoding="utf-8") as handle:
                active_claim = json.load(handle).get("state") in ("acquired", "renewed")
        except (OSError, ValueError):
            problems.append("claim record is unreadable")
    detached_without_claim = act.get("branch") == "HEAD" and not active_claim
    if want and act.get("branch") and not detached_without_claim and not __import__("re").match(want, act["branch"]):
        problems.append(f"worktree is on branch {act.get('branch')}, expected {want}")
    if os.path.exists(hold_path()):
        problems.append("HOLD switch is on — the native has paused new work")
    rc = write({"kind": "heartbeat", "actor": f"stream-{s}", "detail": "preflight: " + ("ok" if not problems else "FAILED: " + "; ".join(problems))})
    if rc != 0:
        problems.append("cannot write the event log")
    for p in problems:
        print("FAIL " + p)
    if problems:
        return 4
    print(f"OK Stream {s} ({stream.get('name')}) — tracker live, worktree {wt}, branch {act.get('branch')}. Now run: pravaha next --stream {s}")
    return 0


def _read_events() -> list[dict]:
    out = []
    try:
        with open(EVENTS, encoding="utf-8") as f:
            for raw in f:
                try:
                    out.append(json.loads(raw))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def cmd_audit(a) -> int:
    import datetime as dt
    events = _read_events()
    try:
        if a.since == "kickoff":
            since = dt.datetime.fromisoformat(events[0]["ts"]) if events else dt.datetime.now(dt.timezone.utc)
        else:
            since = dt.datetime.fromisoformat(a.since.replace("Z", "+00:00"))
        model = load_model()
        findings = audit(model, events, os.path.dirname(EVENTS), since=since,
                         repo=os.environ.get("PRAVAHA_REPO", REPO_ROOT))
        snapshot = build_snapshot(model, events, {}, {}, {}, closure=load_closure(model))
    except (OSError, KeyError, ValueError) as exc:
        print(f"audit unavailable: {exc}", file=sys.stderr)
        return 2
    for finding in findings:
        print(f"FAIL {finding['code']} {finding['ref']}: {finding['detail']}")
    by_id = {row["id"]: row for row in model.get("items", [])}
    gaps = [row for track in snapshot["tracks"] for row in track["items"]
            if row["status"] == "not_applicable" and by_id[row["id"]].get("mandatory", True)]
    for row in gaps:
        print(f"GAP {row['id']}: {', '.join(row.get('skip_origin', [])) or row.get('detail', '')}")
    print(f"AUDIT {'FAIL' if findings else 'PASS'}: {len(findings)} findings")
    return 1 if findings else 0


def _party(a) -> str:
    if getattr(a, "steward", False):
        return "steward"
    s = (a.stream or os.environ.get("PRAVAHA_STREAM", "")).strip().upper()
    if not s:
        raise SystemExit("error: give --stream A|B or --steward")
    return s


def _unacked(party: str) -> list[dict]:
    evs = _read_events()
    acked = set()
    for e in evs:
        if e.get("kind") == "ack":
            who = "steward" if e.get("actor") in ("steward", "native") else (e.get("actor", "").split("-", 1)[-1][:1].upper())
            acked.add((who, e.get("msg_id")))
    return [e for e in evs if e.get("kind") == "message" and e.get("to") == party and (party, e.get("msg_id")) not in acked]


def cmd_inbox(a) -> int:
    import time
    party = _party(a)
    deadline = time.time() + max(0, int(a.wait or 0))
    while True:
        msgs = _unacked(party)
        if msgs or time.time() >= deadline:
            break
        time.sleep(3)
    if a.json:
        print(json.dumps(msgs, ensure_ascii=False, indent=1))
    else:
        print(f"INBOX {party}: {len(msgs)} unacked")
        for m in msgs:
            ref = f" [{m['ref']}]" if m.get("ref") else ""
            print(f"--- {m['msg_id']} from {m.get('actor')} at {m.get('ts')}{ref}\n{m.get('detail')}")
    return 0 if msgs else 1


def _msg_id() -> str:
    import datetime as _dt
    import secrets
    return _dt.datetime.now(_dt.timezone.utc).strftime("M%Y%m%dT%H%M%S") + "-" + secrets.token_hex(2)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pravaha", description="Pravāha campaign CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, *pos, evidence=False, detail=True):
        p = sub.add_parser(name)
        for x in pos:
            p.add_argument(x)
        p.add_argument("--stream")
        p.add_argument("--as", dest="as_", choices=["steward", "native"])
        if detail:
            p.add_argument("--detail", default="")
        if evidence:
            p.add_argument("--evidence")
        return p

    p = sub.add_parser("next"); p.add_argument("--stream"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("status"); p.add_argument("--stream")
    p = sub.add_parser("preflight"); p.add_argument("--stream")
    p = sub.add_parser("audit"); p.add_argument("--since", required=True)
    p = sub.add_parser("claim"); p.add_argument("item"); p.add_argument("--stream"); p.add_argument("--worker")
    p.add_argument("--lease", type=int, default=5400); p.add_argument("--branch"); p.add_argument("--head"); p.add_argument("--step")
    p = sub.add_parser("renew"); p.add_argument("--worker"); p.add_argument("--lease", type=int, default=5400)
    p.add_argument("--branch"); p.add_argument("--head"); p.add_argument("--step")
    p = sub.add_parser("release"); p.add_argument("--worker")
    p = sub.add_parser("verdict"); p.add_argument("item"); p.add_argument("--stream")
    p.add_argument("--head"); p.add_argument("--artifact-digest")
    p.add_argument("--phase", choices=["pre_merge", "post_deploy", "artifact"], default="pre_merge")
    p.add_argument("--result", choices=["ACCEPTED", "REJECTED"], required=True)
    p.add_argument("--detail", required=True)
    p.add_argument("--external-review-path"); p.add_argument("--external-review-sha256")
    add("start", "item"); add("review", "item"); add("block", "item"); add("park", "item"); add("fail", "item")
    add("reopen", "item"); add("unblock", "item")
    p = add("done", "item", evidence=True)
    p.add_argument("--pr", type=int); p.add_argument("--reviewed-head")
    p.add_argument("--artifact-path")
    p.add_argument("--operation-receipt"); p.add_argument("--operation-id")
    p.add_argument("--packet-verdict")
    add("step", "item", "step_name", evidence=True)
    add("progress", "item", "value")
    add("heartbeat"); add("note")
    add("metric", "name", "value")
    add("request", "decision")
    p = sub.add_parser("send"); p.add_argument("--to", required=True); p.add_argument("--detail", default="")
    p.add_argument("--file"); p.add_argument("--ref"); p.add_argument("--as", dest="as_", default="steward")
    p = sub.add_parser("report"); p.add_argument("--stream"); p.add_argument("--detail", required=True); p.add_argument("--ref")
    p = sub.add_parser("inbox"); p.add_argument("--stream"); p.add_argument("--steward", action="store_true")
    p.add_argument("--wait", type=int, default=0); p.add_argument("--json", action="store_true")
    p = sub.add_parser("ack"); p.add_argument("msg_id"); p.add_argument("--stream"); p.add_argument("--steward", action="store_true")
    p.add_argument("--detail", default="")
    p = sub.add_parser("decide"); p.add_argument("decision"); p.add_argument("--detail", required=True)
    p.add_argument("--outcome", choices=["approved", "refused", "deferred", "insufficient_evidence"])
    p.add_argument("--as", dest="as_", choices=["native", "steward"], default="native")
    p.add_argument("--delegated", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "next":
        return cmd_next(a)
    if a.cmd == "status":
        return cmd_status(a)
    if a.cmd == "preflight":
        return cmd_preflight(a)
    if a.cmd == "audit":
        return cmd_audit(a)
    if a.cmd in ("claim", "renew", "release"):
        return cmd_claim_lifecycle(a)
    if a.cmd == "inbox":
        return cmd_inbox(a)
    if a.cmd == "send":
        body = a.detail
        if a.file:
            with open(a.file, encoding="utf-8") as f:
                body = (body + "\n\n" if body else "") + f.read()
        actor = a.as_ if a.as_ in ("steward", "native") else f"stream-{a.as_.upper()}"
        return write({"kind": "message", "actor": actor, "to": a.to.upper() if a.to.lower() != "steward" else "steward",
                      "msg_id": _msg_id(), "ref": a.ref, "detail": body.strip()})
    if a.cmd == "report":
        return write({"kind": "message", "actor": actor_for(a), "to": "steward", "msg_id": _msg_id(), "ref": a.ref, "detail": a.detail})
    if a.cmd == "ack":
        actor = "steward" if a.steward else actor_for(a)
        return write({"kind": "ack", "actor": actor, "msg_id": a.msg_id, "detail": a.detail})
    if a.cmd == "decide":
        return write({"kind": "decision", "actor": a.as_, "decision": a.decision,
                      "state": "delegated" if a.delegated else "decided", "outcome": a.outcome,
                      "detail": a.detail})
    actor = actor_for(a)
    if a.cmd in ("reopen", "unblock"):
        return cmd_transition(a, actor)
    if a.cmd == "verdict":
        return write({"kind": "verdict", "actor": actor, "item": a.item, "head": a.head,
                      "artifact_digest": a.artifact_digest, "phase": a.phase,
                      "result": a.result, "detail": a.detail,
                      "external_review": {"path": a.external_review_path,
                                          "sha256": a.external_review_sha256}
                      if a.external_review_path or a.external_review_sha256 else None})
    state_of = {"start": "running", "review": "review", "block": "blocked", "park": "parked", "fail": "failed", "done": "done"}
    if a.cmd in state_of:
        if a.cmd == "done":
            try:
                if load_model().get("control_plane", {}).get("guarded_completion") is True:
                    return cmd_guarded_done(a, actor)
            except (OSError, ValueError) as exc:
                print(f"refused: cannot read the plan model ({exc})", file=sys.stderr)
                return 2
        return write({"kind": "item", "actor": actor, "item": a.item, "state": state_of[a.cmd],
                      "detail": a.detail, "evidence": getattr(a, "evidence", None)})
    if a.cmd == "step":
        return cmd_step(a, actor)
    if a.cmd == "progress":
        return write({"kind": "item", "actor": actor, "item": a.item, "state": "running",
                      "progress": max(0.0, min(1.0, float(a.value))), "detail": a.detail})
    if a.cmd == "heartbeat":
        stream = (a.stream or os.environ.get("PRAVAHA_STREAM") or os.environ.get("KY_STREAM") or "").upper()
        try:
            claim_streams = load_model().get("control_plane", {}).get("claims", {}).get("streams", [])
        except (OSError, ValueError):
            claim_streams = []
        worker = os.environ.get("KY_LANE", "")
        if stream in claim_streams and worker:
            actor = f"stream-{stream}:{worker}"
        return write({"kind": "heartbeat", "actor": actor, "detail": a.detail})
    if a.cmd == "note":
        return write({"kind": "note", "actor": actor, "detail": a.detail})
    if a.cmd == "metric":
        return write({"kind": "metric", "actor": actor, "name": a.name, "value": a.value, "detail": a.detail})
    if a.cmd == "request":
        return write({"kind": "decision", "actor": actor, "decision": a.decision, "state": "requested", "detail": a.detail})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
