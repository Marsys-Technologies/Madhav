#!/usr/bin/env python3
"""Extract THE approval of THIS run from GitHub's approval history and write the sealing job's approval file (R12-2, R13-4).

Input: the JSON array `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals` returned for this run. The approver (the steward, under the owner's ruling #2) approves the
`gochara-seal` deployment with a comment that carries — on one line, exactly — the digest of the brief they were shown, the run and attempt it is for, and the persisted brief's id:

    brief-digest: <64 lowercase hex>  run: <run id>  attempt: <attempt number>  brief-id: <persisted brief id>

THE CONTRACT (R13-4; none of it depends on the order of the API's array, which GitHub does not document, nor on any attempt field — the run and attempt are read from the COMMENT, which is
claimed by the approver, not API metadata):
  * the candidates are the reviews of the environment whose comment names THIS run AND attempt; a review naming another run or attempt is stale and ignored;
  * ANY ambiguity REFUSES and requires a FRESH workflow run: a refusing review of this attempt (an approval and a later — or earlier — rejection are ambiguous whatever the order); a review
    with no well-formed grammar line (it cannot be attributed to an attempt); a comment stating more than one distinct line; more than one approval of this attempt;
  * exactly one approved candidate remains, and its digest AND brief-id must equal the retained brief's digest and the persisted brief id of THIS run's brief job; the approver login is non-empty;
  * otherwise it REFUSES (exit 2, reason on stderr, nothing written).
On success it writes `{schema: 'seal_approval/1', brief_digest, run_id, run_attempt, approver_login, approved_by_note}` where the NOTE is built mechanically (ruling id + triggering actor), never taken from
the comment — the file Stream A's `seal_job` takes as `--approval-file`, which independently re-checks the run id / attempt against GITHUB_RUN_ID / GITHUB_RUN_ATTEMPT and the digest against its own
recompute. (The brief-id is checked HERE against the artifact of this attempt; carrying it into the seal call is a wire change proposed to the steward — it is NOT in the approval file today.)
The ordering the API actually returns is recorded as an output of the live-gate proof (runbook §7.1)."""
from __future__ import annotations

import argparse
import json
import re
import sys

_LINE = re.compile(r"\s*brief-digest:\s*([0-9a-f]{64})\s+run:\s*(\d+)\s+attempt:\s*(\d+)\s+brief-id:\s*(\d+)\s*")
RULING = "NATIVE_DIRECT_RULINGS_20261002#2"          # the owner ruling that authorises same-account approval (no space: Stream A's grammar refuses one)


def mechanical_note(triggering_actor: str) -> str:
    """The receipt's `approved_by_note` is built MECHANICALLY by the workflow and is EXACTLY Stream A's grammar — `ruling:<owner ruling id>; actor:<github.triggering_actor>` (their
    `seal_flow.NOTE_FORMAT`, which refuses any other text: `approval_note_not_mechanical`). The sentence "approved by the steward under the owner's account (not an independent human
    check)" is NOT stored in the note: it is stated in the brief shown before the gate (run summary) and in the receipt's documented meaning (design record §3-§4)."""
    return f"ruling:{RULING}; actor:{triggering_actor}"


class Refused(Exception):
    pass


def extract(history, *, environment: str, run_id: str, attempt: str, brief_digest: str, brief_id: str, triggering_actor: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", brief_digest or ""):
        raise Refused("the retained brief's digest is not a sha256")
    if not re.fullmatch(r"[0-9]+", str(run_id)) or not re.fullmatch(r"[0-9]+", str(attempt)) or int(attempt) < 1:
        raise Refused("this run's id / attempt are not numeric")
    if not re.fullmatch(r"[1-9][0-9]*", str(brief_id)):
        raise Refused("the persisted brief id of this run's brief job is not a positive integer")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}(\[bot\])?", triggering_actor or ""):
        raise Refused("the workflow's triggering actor is not a GitHub login")
    if not isinstance(history, list):
        raise Refused("the approval history is not a JSON array")
    mine = [h for h in history if isinstance(h, dict) and any((e or {}).get("name") == environment for e in (h.get("environments") or []))]
    if not mine:
        raise Refused(f"no approval of environment {environment!r} exists for this run")
    selected = []
    for h in mine:
        comment = h.get("comment")
        named = {m.groups() for m in (_LINE.fullmatch(l) for l in (comment.splitlines() if isinstance(comment, str) else [])) if m}
        if len(named) > 1:
            raise Refused("an approval comment states more than one distinct digest/run/attempt/brief-id: ambiguous — start a fresh run")
        if not named:
            raise Refused("a review of the environment has no well-formed `brief-digest: <hex>  run: <id>  attempt: <n>  brief-id: <n>` line, so it cannot be attributed to an attempt: "
                          "ambiguous — start a fresh run")
        d, c_run, c_attempt, c_brief = next(iter(named))
        if (c_run, c_attempt) != (str(run_id), str(attempt)):
            continue                                                       # another run or attempt: stale, ignored
        if h.get("state") != "approved":
            raise Refused(f"a review of {environment!r} for this attempt is {h.get('state')!r}, not approved: an approval and a refusal of one attempt are ambiguous — start a fresh run")
        selected.append((h, d, c_brief))
    if not selected:
        raise Refused(f"no approval of environment {environment!r} names run {run_id} attempt {attempt} (a stale approval of another run or attempt is never reused)")
    if len(selected) > 1:
        raise Refused("more than one approval names this run and attempt: ambiguous — start a fresh run")
    latest, digest, c_brief = selected[0]
    login = ((latest.get("user") or {}).get("login") or "").strip()
    if not login:
        raise Refused("the approval names no approver login")
    if digest != brief_digest:
        raise Refused("the approved digest is not the digest of the retained brief (the brief changed after it was approved, or the wrong brief was approved)")
    if c_brief != str(brief_id):
        raise Refused(f"the approval names persisted brief {c_brief}, this run's brief job persisted brief {brief_id}")
    return {"schema": "seal_approval/1", "brief_digest": digest, "run_id": int(run_id), "run_attempt": int(attempt),
            "approver_login": login, "approved_by_note": mechanical_note(triggering_actor)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approvals-file", required=True)
    ap.add_argument("--environment", default="gochara-seal")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--attempt", required=True)
    ap.add_argument("--brief-digest", required=True)
    ap.add_argument("--brief-id", required=True)
    ap.add_argument("--triggering-actor", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        with open(a.approvals_file, encoding="utf-8") as f:
            history = json.load(f)
        out = extract(history, environment=a.environment, run_id=a.run_id, attempt=a.attempt, brief_digest=a.brief_digest, brief_id=a.brief_id, triggering_actor=a.triggering_actor)
    except (Refused, OSError, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True)
    print(f"approval of run {out['run_id']} attempt {out['run_attempt']} by {out['approver_login']} for brief {out['brief_digest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
