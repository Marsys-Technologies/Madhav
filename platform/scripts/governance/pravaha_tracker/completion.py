"""Pure checks for a guarded item completion.

The caller must obtain detector and PR observations from the live services.  This
module checks the conjunction against the event log before a guarded event is
written; a detector marker or a caller's evidence string alone is never enough.
"""
from __future__ import annotations

import re

from .events import actor_stream
from .state import D46_KINDS, build_snapshot, index_events, open_dependencies, pending_gates, recorded_na_steps
from .verdicts import accepted_verdict


COMPOSED_RECEIPT_SCHEMA = "ky.a55i_both_runs/1"    # the one composed-receipt schema (cli._check_composed_components)


class CompletionError(ValueError):
    """A refused completion. ``code`` is the audit code of the unmet typed evidence, when that is the reason."""

    def __init__(self, detail: str, code: str | None = None):
        super().__init__(detail)
        self.code = code


# The ONE table of typed evidence (relaunch plan v2.7 §6, KU-01), keyed by an item's declared `reviewer_rule`:
# rule -> (completion kind, the evidence a completion of that kind must carry). `guarded_done_event` refuses a
# completion that `unmet_evidence` finds a gap in; `audit.audit` reports the same gap under the same code.
EVIDENCE_TABLE = {
    "v_exact_head_then_deploy_containment": ("code", ("reviewed_head_verdict", "deployment_containment")),
    # A8 §4 / plan v3.0 §I retired the post-deploy verdict (SR-POSTDEPLOY-RETIRED): the rule name stays declared in
    # the plans, but a data-writing code item now needs exactly what any code item needs. The `post_deploy` verdict
    # TYPE stays readable (events.py, verdicts.py): recorded post-deploy events remain valid history.
    "v_exact_head_then_post_deploy_at_merge_commit": ("code", ("reviewed_head_verdict", "deployment_containment")),
    "v_artifact_digest_reviewer_not_author": ("artifact", ("artifact_verdict",)),
    "finalizer_independent_review_artifact_digest": ("artifact", ("artifact_verdict",)),
    "v_pre_acceptance_then_receipt_readback_digest": ("operation", ("completed_receipt", "artifact_verdict")),
    "v_packet_verdict_bound_to_external_review": ("packet", ("packet_verdict", "artifact_verdict")),
}


# A7 D-46 (owner direction 2026-10-17): a code/artifact item is IMPLEMENTED once merged + accepted + deployed
# (artifact: digest + independent verdict). Its open dependencies no longer block that; they are recorded as
# `activation_pending` and the item is ACTIVATED only when they close. Code items also drop the separate step
# receipts: the PR acceptance covers the code-verifiable steps. Operation, packet, decision and join items keep
# strict ordered completion (SR-A4-01).


def d46_kind(model: dict, item: dict, proof_type) -> str | None:
    """The completion kind that decides whether D-46 applies: the declared one, else the proof's own type."""
    if isinstance(model.get("control_plane", {}).get("declarations"), dict):
        kind = item.get("completion_kind")
    else:
        kind = proof_type
    return kind if kind in D46_KINDS else None


def d46_requirements(requirements: dict, relaxed) -> dict:
    """D-46: EVERY code item is contained in a successful main deploy, measured (a data-writing one too; its
    post-deploy verdict is retired, A8 §4)."""
    if relaxed == "code" and "deployment_containment" not in requirements["evidence"]:
        return {**requirements, "evidence": (*requirements["evidence"], "deployment_containment")}
    return requirements


def _production_metadata(value) -> bool:
    """Normalised (plan §8.5): empty, the string NONE and anything that is not text or a list of text say nothing."""
    if isinstance(value, str):
        return value.strip() not in ("", "NONE")
    if isinstance(value, list):
        return any(isinstance(entry, str) and _production_metadata(entry) for entry in value)
    return False


def writes_data(item: dict) -> bool:
    """An item whose brief declares a migration or a production operation writes data (amendment §5)."""
    brief = item.get("brief") if isinstance(item.get("brief"), dict) else {}
    return _production_metadata(brief.get("migration")) or _production_metadata(brief.get("op"))


def evidence_requirements(model: dict, item: dict) -> dict | None:
    """The typed evidence a completion of `item` must carry, read from EVIDENCE_TABLE.

    None for a model without `control_plane.declarations` (it completes and audits as before). ``conflict`` names
    a declaration that cannot be trusted: such an item is refused by the guard and reported by the audit.
    """
    declarations = model.get("control_plane", {}).get("declarations")
    if not isinstance(declarations, dict):
        return None
    rule, kind = item.get("reviewer_rule"), item.get("completion_kind")
    legend = declarations.get("reviewer_rule")
    entry = EVIDENCE_TABLE.get(rule) if isinstance(rule, str) else None
    conflict = None
    if not item.get("id"):
        conflict = "item is not in the plan model"
    elif item.get("done_by") in ("decision", "join") or item.get("join"):
        conflict = "item is completed by its decision or join, never by typed evidence"
    elif entry is None or not isinstance(legend, dict) or rule not in legend:
        conflict = f"reviewer_rule {rule!r} is not a declared rule"
    elif kind != entry[0]:
        conflict = f"completion_kind {kind!r} contradicts reviewer_rule {rule} ({entry[0]})"
    return {"reviewer_rule": rule, "completion_kind": entry[0] if entry else None,
            "evidence": entry[1] if entry else (), "conflict": conflict}


def _undeclared_requirements(item: dict, kind) -> dict | None:
    """A model without declarations: the proof's own type selects the evidence, as before."""
    evidence = {"code": ("reviewed_head_verdict", "deployment_containment"),
                "artifact": ("artifact_verdict",), "operation": ("completed_receipt", "artifact_verdict"),
                "packet": ("packet_verdict", "artifact_verdict")}.get(kind if isinstance(kind, str) else None)
    if evidence is None:
        return None
    return {"reviewer_rule": None, "completion_kind": kind, "evidence": evidence, "conflict": None}


def _sha(value, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _code_mapping(completion: dict) -> tuple[dict, str | None, str | None]:
    """→ (PR observation, reviewed head, squash merge commit); the head is None unless the merged PR maps it."""
    observed = completion.get("pr") if isinstance(completion.get("pr"), dict) else {}
    head = observed.get("headRefOid")
    commit = observed.get("mergeCommit") if isinstance(observed.get("mergeCommit"), dict) else {}
    merge = commit.get("oid") if _sha(commit.get("oid"), 40) else None
    mapped = (observed.get("state") == "MERGED" and isinstance(observed.get("number"), int) and _sha(head, 40)
              and merge is not None and head == completion.get("reviewed_head"))
    return observed, (head if mapped else None), merge


def unmet_evidence(model: dict, item: dict, events: list[dict], completion: dict, requirements: dict, *,
                   repo: str | None = None) -> list[dict]:
    """Every typed requirement that `completion` (a proof, or a recorded completion) does not meet in `events`.

    → [{"code", "requirement", "detail"}], in the order the guard refuses; empty when the evidence is complete.
    `repo` is only ever handed to the shared inheritance predicate (verdicts.accepted_verdict).
    """
    gaps: list[dict] = []

    def gap(code: str, requirement: str, detail: str) -> None:
        gaps.append({"code": code, "requirement": requirement, "detail": detail})

    if requirements.get("conflict"):
        gap("declaration_conflict", "declaration", "declaration_conflict: " + requirements["conflict"])
        return gaps
    kind = requirements["completion_kind"]
    if completion.get("type") != kind:
        gap("completion_kind_mismatch", "completion_kind",
            f"completion_kind_mismatch: item declares {kind}; the completion is typed {completion.get('type')!r}")
        return gaps
    item_id = item.get("id")
    verdict_stream = model.get("control_plane", {}).get("verdict_stream")

    def independent(verdict: dict | None) -> bool:
        return bool(verdict) and actor_stream(verdict.get("actor", "")) == verdict_stream

    digest = completion.get("artifact_digest")
    for requirement in requirements["evidence"]:
        if requirement == "reviewed_head_verdict":
            _, head, _ = _code_mapping(completion)
            if head is None:
                gap("rejected_or_stale_verdict", requirement, "live PR does not map the reviewed head to a merge commit")
            elif not independent(accepted_verdict(events, item_id, head=head, repo=repo)):
                gap("rejected_or_stale_verdict", requirement, "independent ACCEPTED verdict at current PR head is missing")
        elif requirement == "deployment_containment":
            # a code-only item is live when a successful deployment of main CONTAINS the merge commit (R-COORD-7 a);
            # the caller observes the live deploy list and the repository, never a worker's word
            deploy = completion.get("deploy") if isinstance(completion.get("deploy"), dict) else {}
            if (_code_mapping(completion)[2] is None or not _sha(deploy.get("deployed_sha"), 40)
                    or deploy.get("contains_merge") is not True or not deploy.get("run_id")):
                gap("missing_deployment_containment", requirement,
                    "no successful deployment of main containing the merge commit was observed")
        elif requirement == "completed_receipt":
            receipt, operation_id = completion.get("receipt"), completion.get("operation_id")
            # A composed receipt (ky.a55i_both_runs/1) has no status or item_id of its own: it counts only when
            # the caller verified every cited component (cli._check_composed_components) and it names this item.
            composed = isinstance(receipt, dict) and receipt.get("schema") == COMPOSED_RECEIPT_SCHEMA
            if composed:
                bound = completion.get("composed_components_verified") is True and receipt.get("item") == item_id
            else:
                bound = (isinstance(receipt, dict) and receipt.get("item_id") == item_id
                         and receipt.get("status") == "COMPLETED")
            if (not isinstance(receipt, dict) or not isinstance(operation_id, str) or not operation_id
                    or not _sha(digest, 64) or receipt.get("operation_id") != operation_id or not bound):
                gap("unbound_operation", requirement, "operation requires a completed receipt for this item and identity")
        elif requirement == "packet_verdict":
            packet, review_digest = completion.get("packet"), completion.get("review_sha256")
            declared = item.get("detector", {}).get("path", "") if isinstance(item.get("detector"), dict) else ""
            packet_id = declared.rsplit("/", 1)[-1].removesuffix(".VERDICT.json")
            if (not isinstance(packet, dict) or not str(item_id).startswith("V-")
                    or not declared.endswith(".VERDICT.json") or not _sha(digest, 64) or not _sha(review_digest, 64)
                    or packet.get("item") != item_id or packet.get("packet") != packet_id
                    or packet.get("result") != "ACCEPTED" or type(packet.get("blocking_open")) is not int
                    or packet["blocking_open"] != 0 or packet.get("review_sha256") != review_digest):
                gap("missing_artifact_verdict", requirement,
                    "packet verdict must accept the exact model item and reviewed packet without open blockers")
        elif requirement == "artifact_verdict":
            if kind == "artifact" and not _sha(digest, 64):
                gap("missing_artifact_verdict", requirement, "artifact requires a SHA-256 digest")
            elif not _sha(digest, 64) or not independent(
                    accepted_verdict(events, item_id, artifact_digest=digest, phase="artifact")):
                gap("missing_artifact_verdict", requirement,
                    {"artifact": "independent artifact verdict is missing",
                     "operation": "independent operation receipt verdict is missing",
                     "packet": "independent packet verdict is missing"}[kind])
    return gaps


def guarded_done_event(model: dict, events: list[dict], item_id: str, actor: str,
                       detector: dict, proof: dict, *, derived_done: dict | None = None) -> dict:
    """Validate an item against current observations and return its durable event.

    ``derived_done`` is the merged+deployed map the display uses (merged_deployed.derive_for_events): a dependency
    the tracker shows as done by that derivation counts as done here too (SR-BOLD-07).

    ``proof['pr']`` is the caller's live GitHub observation, not an assertion from
    the worker.  The write path must obtain it itself and re-read the event log
    while holding the log lock before appending this returned event.
    """
    if model.get("control_plane", {}).get("guarded_completion") is not True:
        raise CompletionError("model does not enable guarded completion")
    item = next((row for row in model.get("items", []) if row["id"] == item_id), None)
    if not item or item.get("done_by") in ("decision", "join") or item.get("join"):
        raise CompletionError("unknown item or item is completed by decision/join")
    stream = actor_stream(actor)
    owner = item.get("owner")
    if owner in ("N", "V") and stream != "S":
        raise CompletionError("S must complete independently accepted N/V work")
    if stream != owner and not (stream == "S" and owner in ("N", "V")):
        raise CompletionError("only the owner or S for independently accepted N/V work may complete")
    # the item's own completion still writes its durable event: only what it depends on is read through the derivation
    upstream = {k: v for k, v in (derived_done or {}).items() if k != item_id}
    snapshot = build_snapshot(model, events, {}, {}, {}, derived_done=upstream)
    rows = {row["id"]: row for track in snapshot["tracks"] for row in track["items"]}
    if rows[item_id]["status"] == "done":
        raise CompletionError("item is already done")
    if rows[item_id]["status"] == "not_applicable":
        raise CompletionError("item is not applicable")
    relaxed = d46_kind(model, item, proof.get("type"))
    # an implemented-but-not-activated dependency satisfies only a code/artifact item (D-46); every other kind
    # still waits for it to be activated (SR-A4-01)
    strict = open_dependencies(item, rows, relaxed=relaxed is not None)
    activation_pending: list[str] = []
    if strict and relaxed is None:
        raise CompletionError("dependencies remain open: " + ", ".join(strict))
    if strict:
        unknown = [dep for dep in strict if dep not in rows]
        if unknown:    # D-46 defers to another plan item or gate, never to an id the plan does not know
            raise CompletionError("dependencies unknown to the plan: " + ", ".join(unknown))
    if relaxed is not None:
        activation_pending = pending_gates(item, rows)    # transitive: an upstream's own open gates count too
    steps = item.get("steps", [])
    completed = {ev.get("step") for ev in events if ev.get("kind") == "item" and
                 ev.get("item") == item_id and ev.get("state") == "done" and ev.get("step")}
    # a plan-declared not-applicable step is satisfied while its cited decision is recorded (SR-OP-STEPS item 3)
    completed |= set(recorded_na_steps(item, index_events(events)["decisions"],
                                       model.get("control_plane", {}).get("decision_outcomes")))
    if set(steps) - completed and relaxed != "code":
        raise CompletionError("steps remain open: " + ", ".join(sorted(set(steps) - completed)))
    if not item.get("detector") or detector.get("status") != "done":
        raise CompletionError("declared detector has not passed")

    kind = proof.get("type")
    requirements = evidence_requirements(model, item) or _undeclared_requirements(item, kind)
    if requirements is None:
        raise CompletionError("unknown typed evidence")
    requirements = d46_requirements(requirements, relaxed)
    gaps = unmet_evidence(model, item, events, proof, requirements, repo=proof.get("repo"))
    first = gaps[0] if gaps else None
    if first and first["requirement"] in ("declaration", "completion_kind"):
        raise CompletionError(first["detail"], first["code"])
    if kind == "code":
        observed, head, merge = _code_mapping(proof)
        if head is not None:    # an unmapped head is the first gap, raised below
            review = next((ev for ev in reversed(events) if ev.get("kind") == "item"
                           and ev.get("item") == item_id and ev.get("state") == "review"), None)
            review_detail = (review or {}).get("detail", "")
            if (f"PR #{observed['number']}" not in review_detail or head not in review_detail):
                raise CompletionError("PR and head are not registered in the item's review event")
    if first:
        raise CompletionError(first["detail"], first["code"])

    digest = proof.get("artifact_digest")
    d46 = {"merged_pr": None, "acceptance_ref": None, "deploy_run_id": None}
    if kind == "code":
        verdict = accepted_verdict(events, item_id, head=head, repo=proof.get("repo"))
        deploy = proof.get("deploy") if isinstance(proof.get("deploy"), dict) else {}
        d46.update(merged_pr=observed["number"], deploy_run_id=deploy.get("run_id"),
                   acceptance_ref={"phase": "pre_merge", "head": head, "verdict_ts": verdict["ts"],
                                   "actor": verdict.get("actor")})
        evidence = (f"PR #{observed['number']} head {head} merged {merge}; verdict {verdict['ts']}; "
                    f"deployed {deploy['deployed_sha']} (run {deploy['run_id']}) contains the merge commit")
    elif kind == "artifact":
        verdict = accepted_verdict(events, item_id, artifact_digest=digest, phase="artifact")
        d46["acceptance_ref"] = {"phase": "artifact", "artifact_digest": digest, "verdict_ts": verdict["ts"],
                                 "actor": verdict.get("actor")}
        evidence = f"artifact sha256 {digest}; verdict {verdict['ts']}"
    elif kind == "operation":
        verdict = accepted_verdict(events, item_id, artifact_digest=digest, phase="artifact")
        evidence = f"operation {proof['operation_id']} receipt sha256 {digest}; verdict {verdict['ts']}"
    else:
        packet_id = item["detector"]["path"].rsplit("/", 1)[-1].removesuffix(".VERDICT.json")
        evidence = f"packet {packet_id} verdict sha256 {digest}; review sha256 {proof['review_sha256']}"
    event = {"kind": "item", "actor": actor, "item": item_id, "state": "done",
             "guarded": True, "evidence": evidence, "completion": {"type": kind, **proof},
             "detail": "guarded completion: dependencies, steps, detector and independent acceptance verified"}
    if relaxed:
        event.update(d46, activation_pending=activation_pending,
                     detail="D-46 implemented: independent acceptance and detector verified" + (
                         "; activation pending on " + ", ".join(activation_pending) if activation_pending else ""))
    return event
