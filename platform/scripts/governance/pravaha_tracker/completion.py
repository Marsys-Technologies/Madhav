"""Pure checks for a guarded item completion.

The caller must obtain detector and PR observations from the live services.  This
module checks the conjunction against the event log before a guarded event is
written; a detector marker or a caller's evidence string alone is never enough.
"""
from __future__ import annotations

import re

from .events import actor_stream
from .state import build_snapshot
from .verdicts import accepted_verdict


class CompletionError(ValueError):
    pass


def guarded_done_event(model: dict, events: list[dict], item_id: str, actor: str,
                       detector: dict, proof: dict) -> dict:
    """Validate an item against current observations and return its durable event.

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
    snapshot = build_snapshot(model, events, {}, {}, {})
    rows = {row["id"]: row for track in snapshot["tracks"] for row in track["items"]}
    if rows[item_id]["status"] == "done":
        raise CompletionError("item is already done")
    if rows[item_id]["status"] == "not_applicable":
        raise CompletionError("item is not applicable")
    if rows[item_id]["deps_open"]:
        raise CompletionError("dependencies remain open: " + ", ".join(rows[item_id]["deps_open"]))
    steps = item.get("steps", [])
    completed = {ev.get("step") for ev in events if ev.get("kind") == "item" and
                 ev.get("item") == item_id and ev.get("state") == "done" and ev.get("step")}
    if set(steps) - completed:
        raise CompletionError("steps remain open: " + ", ".join(sorted(set(steps) - completed)))
    if not item.get("detector") or detector.get("status") != "done":
        raise CompletionError("declared detector has not passed")

    kind = proof.get("type")
    if kind == "code":
        observed = proof.get("pr") or {}
        head = observed.get("headRefOid")
        merge = (observed.get("mergeCommit") or {}).get("oid")
        if (observed.get("state") != "MERGED" or not isinstance(observed.get("number"), int)
                or not isinstance(head, str) or not re.fullmatch(r"[0-9a-f]{40}", head)
                or not isinstance(merge, str) or not re.fullmatch(r"[0-9a-f]{40}", merge)
                or head != proof.get("reviewed_head")):
            raise CompletionError("live PR does not map the reviewed head to a merge commit")
        review = next((ev for ev in reversed(events) if ev.get("kind") == "item"
                       and ev.get("item") == item_id and ev.get("state") == "review"), None)
        review_detail = (review or {}).get("detail", "")
        if (f"PR #{observed['number']}" not in review_detail or head not in review_detail):
            raise CompletionError("PR and head are not registered in the item's review event")
        verdict = accepted_verdict(events, item_id, head=head)
        if not verdict or actor_stream(verdict.get("actor", "")) != model["control_plane"].get("verdict_stream"):
            raise CompletionError("independent ACCEPTED verdict at current PR head is missing")
        post = accepted_verdict(events, item_id, head=merge, phase="post_deploy")
        if not post or actor_stream(post.get("actor", "")) != model["control_plane"].get("verdict_stream"):
            raise CompletionError("independent post-deploy verdict at merge commit is missing")
        evidence = f"PR #{observed['number']} head {head} merged {merge}; verdicts {verdict['ts']}, {post['ts']}"
    elif kind == "artifact":
        digest = proof.get("artifact_digest")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CompletionError("artifact requires a SHA-256 digest")
        verdict = accepted_verdict(events, item_id, artifact_digest=digest, phase="artifact")
        if not verdict or actor_stream(verdict.get("actor", "")) != model["control_plane"].get("verdict_stream"):
            raise CompletionError("independent artifact verdict is missing")
        evidence = f"artifact sha256 {digest}; verdict {verdict['ts']}"
    else:
        raise CompletionError("unknown typed evidence")
    return {"kind": "item", "actor": actor, "item": item_id, "state": "done",
            "guarded": True, "evidence": evidence, "completion": {"type": kind, **proof},
            "detail": "guarded completion: dependencies, steps, detector and independent acceptance verified"}
