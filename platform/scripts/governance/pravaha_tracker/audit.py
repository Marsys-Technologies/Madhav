"""Read-only audit of earned campaign progress and exclusive work claims."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import re

from .verdicts import accepted_verdict


def _time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("audit timestamps need a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def audit(model: dict, events: list[dict], run_root: str | Path, *,
          since: dt.datetime, now: dt.datetime | None = None) -> list[dict]:
    """Return violations. A missing receipt is never silently treated as acceptance."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None or since.tzinfo is None:
        raise ValueError("audit bounds need timezones")
    root = Path(run_root)
    items = {row["id"]: row for row in model.get("items", [])}
    findings: list[dict] = []

    def fail(code: str, ref: str, detail: str) -> None:
        findings.append({"code": code, "ref": ref, "detail": detail})

    active: dict[str, dict] = {}
    completed: set[str] = set()
    completed_heads: list[tuple[str, str, str | None]] = []
    completed_artifacts: list[tuple[str, str]] = []
    outcomes: dict[str, str] = {}
    seen: list[dict] = []
    earned = 0
    blocked = False

    def dependency_done(item_id: str, ancestors: frozenset[str] = frozenset()) -> bool:
        if item_id in completed:
            return True
        row = items.get(item_id)
        if row is None or item_id in ancestors:
            return False
        if row.get("done_by") == "decision":
            return outcomes.get(row.get("decision")) in model.get("control_plane", {}).get(
                "decision_outcomes", {}).get("final", ["approved", "refused"])
        if row.get("done_by") == "join" or row.get("join"):
            return all(dependency_done(dep, ancestors | {item_id}) for dep in row.get("depends_on", []))
        return False

    def dependency_skipped(item_id: str, ancestors: frozenset[str] = frozenset()) -> bool:
        row = items.get(item_id)
        if row is None or item_id in ancestors:
            return False
        for decision, wanted in row.get("requires_outcome", {}).items():
            actual = outcomes.get(decision)
            if actual in ("approved", "refused") and actual != wanted:
                return True
        return any(dependency_skipped(dep, ancestors | {item_id}) for dep in row.get("depends_on", []))

    for ev in events:
        try:
            at = _time(ev["ts"])
        except (KeyError, TypeError, ValueError):
            continue
        kind = ev.get("kind")
        if kind == "claim":
            item_id = ev.get("item", "")
            prior = active.get(item_id)
            if ev.get("state") == "acquired":
                if prior and at < _time(prior["expires_at"]):
                    fail("duplicate_claim", item_id, "new claim overlaps an unexpired claim")
                active[item_id] = ev
            elif ev.get("state") == "renewed":
                if not prior or prior.get("claim_id") != ev.get("claim_id"):
                    fail("invalid_renewal", item_id, "renewal does not name the active claim")
                active[item_id] = ev
            elif ev.get("state") in ("released", "expired"):
                if prior and prior.get("claim_id") == ev.get("claim_id"):
                    active.pop(item_id, None)
        elif kind == "decision" and ev.get("state") in ("decided", "delegated"):
            outcomes[ev.get("decision", "")] = ev.get("outcome", "")
            if at >= since and ev.get("outcome") in ("approved", "refused"):
                earned += 1
        elif kind == "item":
            item_id = ev.get("item", "")
            if ev.get("state") in ("blocked", "parked", "failed") and at >= since:
                blocked = True
            if ev.get("state") == "done" and not ev.get("step"):
                row = items.get(item_id, {})
                for dep in row.get("depends_on", []):
                    if not dependency_done(dep) and not (row.get("accepts_not_applicable_dependencies") and
                                                        dependency_skipped(dep)):
                        fail("unmet_dependency", item_id, f"{dep} was not terminal at completion")
                if any(outcomes.get(decision) in ("approved", "refused") and
                       outcomes[decision] != wanted for decision, wanted in
                       row.get("requires_outcome", {}).items()) or (not row.get(
                           "accepts_not_applicable_dependencies") and dependency_skipped(item_id)):
                    fail("skipped_item_completed", item_id, "item completed despite unavailable required input")
                if model.get("control_plane", {}).get("guarded_completion") and ev.get("guarded") is not True:
                    fail("unguarded_done", item_id, "terminal event bypassed guarded completion")
                completion = ev.get("completion") if isinstance(ev.get("completion"), dict) else {}
                head = completion.get("reviewed_head") or ev.get("reviewed_head") or ev.get("head")
                pr = completion.get("pr") if isinstance(completion.get("pr"), dict) else {}
                merge_commit = pr.get("mergeCommit") if isinstance(pr.get("mergeCommit"), dict) else {}
                merge = merge_commit.get("oid") if completion.get("type") == "code" else None
                if head and accepted_verdict(seen, item_id, head=head) is None:
                    fail("rejected_or_stale_verdict", item_id, "no current ACCEPTED verdict for reviewed head")
                if head:
                    completed_heads.append((item_id, head, merge))
                if merge and accepted_verdict(seen, item_id, head=merge, phase="post_deploy") is None:
                    fail("missing_post_deploy_verdict", item_id, "no ACCEPTED verdict for deployed merge commit")
                digest = completion.get("artifact_digest")
                if completion.get("type") in ("artifact", "operation", "packet"):
                    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or \
                            accepted_verdict(seen, item_id, artifact_digest=digest, phase="artifact") is None:
                        fail("missing_artifact_verdict", item_id, "no ACCEPTED verdict for completed artifact")
                    else:
                        completed_artifacts.append((item_id, digest))
                operation_id = completion.get("operation_id") or ev.get("operation_id")
                if operation_id and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", operation_id):
                    receipt = _read_json(root / "ops" / "receipts" / f"{operation_id}.json")
                    if not receipt or receipt.get("operation_id") != operation_id or receipt.get("item_id") != item_id:
                        fail("unbound_operation", item_id, f"receipt {operation_id} is missing or names another item")
                elif operation_id:
                    fail("unbound_operation", item_id, "operation id is invalid")
                completed.add(item_id)
                if at >= since:
                    earned += 1
        seen.append(ev)

    for item_id, claim in active.items():
        try:
            if _time(claim["expires_at"]) <= now:
                fail("expired_worker", item_id, f"{claim.get('worker_id')} has not renewed its claim")
        except (KeyError, TypeError, ValueError):
            fail("invalid_claim_expiry", item_id, "active claim has no valid expiry")

    for item_id, head, merge in completed_heads:
        if accepted_verdict(events, item_id, head=head) is None and not any(
                f["code"] == "rejected_or_stale_verdict" and f["ref"] == item_id for f in findings):
            fail("rejected_or_stale_verdict", item_id, "reviewed head lost its ACCEPTED verdict")
        if merge and accepted_verdict(events, item_id, head=merge, phase="post_deploy") is None and not any(
                f["code"] == "missing_post_deploy_verdict" and f["ref"] == item_id for f in findings):
            fail("missing_post_deploy_verdict", item_id, "deployed merge commit lost its ACCEPTED verdict")

    for item_id, digest in completed_artifacts:
        if accepted_verdict(events, item_id, artifact_digest=digest, phase="artifact") is None and not any(
                f["code"] == "missing_artifact_verdict" and f["ref"] == item_id for f in findings):
            fail("missing_artifact_verdict", item_id, "completed artifact lost its ACCEPTED verdict")

    # A submitted production request must be bound to an independent acceptance.
    for folder in (root / "ops" / "requests", root / "ops" / "done"):
        if folder.is_dir():
            for path in folder.glob("*.json"):
                req = _read_json(path)
                if not req or not req.get("lease_id"):
                    continue
                operation_id = req.get("operation_id", path.stem)
                if not isinstance(operation_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", operation_id):
                    fail("unbound_production_operation", path.stem, "invalid operation id")
                    continue
                acceptance = _read_json(root / "ops" / "acceptance" / f"{operation_id}.json")
                bound = {key: value for key, value in req.items() if key != "acceptance_receipt"}
                digest = hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if not acceptance or acceptance.get("result") != "ACCEPTED" or \
                        acceptance.get("operation_id") != operation_id or \
                        acceptance.get("by") not in ("v1", "v2", "v3", "v4") or \
                        acceptance.get("request_sha256") != digest or \
                        acceptance.get("reviewed_commit") != req.get("reviewed_commit"):
                    fail("unbound_production_operation", operation_id, "independent acceptance is absent")

    fence = _read_json(root / "ops" / "PRODUCTION_PENDING.json")
    if fence is not None:
        operation_id = fence.get("operation_id", "")
        safe_id = isinstance(operation_id, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", operation_id)
        quiescence = _read_json(root / "ops" / "acceptance" / f"{operation_id}.quiescence.json") if safe_id else None
        if not operation_id or not quiescence or quiescence.get("operation_id") != operation_id or \
                quiescence.get("result") != "ACCEPTED" or quiescence.get("by") not in ("v1", "v2", "v3", "v4"):
            fail("unreleased_production_fence", operation_id or "fence", "no matching verifier quiescence receipt")

    if (now - since).total_seconds() >= 2700 and earned == 0 and not blocked and any(
            ev.get("kind") == "claim" and ev.get("state") == "acquired" and
            _time(ev["ts"]) >= since for ev in events):
        fail("zero_earned_progress", "campaign", "active claims yielded no terminal progress in this interval")
    return findings
