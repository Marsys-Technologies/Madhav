#!/usr/bin/env python3
"""kyd_kinds_land.py — the REGEN, MERGE and COMPLETE kinds of the KĀLA-YANTRA v3 dispatcher (relaunch plan v2.7 §6,
the rows of those names and "Inheritance predicate"; §14 B-2 "Under HOLD_MERGES"; packet KV3-B-KYDKINDS-LAND v1).

The engine (kydispatch.py) calls
    intents(ctx)             read-only → the intents that hold NOW, in the order cancel, COMPLETE, MERGE, REGEN
    start(ctx, job)          a script job: do it → {outcome, detail, failure_fp}
    park(ctx, intent)        a `queue` intent under HOLD_MERGES, in place of admission → {parked, path, detail}
    accepted_head(ctx, item) served as ctx.accepted → {head, via} | None | "unknown"
Importing this file runs nothing. It starts no process itself: every command goes through ctx.sh, ctx.ky or ctx.act.

ctx (engine-built; the tests use a recording double): paths `root run fleet scratch repo`; `controller_id`;
`sh(argv, env=None, cwd=None, timeout=120)` → (rc, out, err), rc None = unknown; `ky(*args, stream=None, lane=None)`
→ the same triple; `act(id, kind, inputs, target, effect, observer)` → (done | failed | unknown, result); `next`
(a fresh `ky next --json`, None when stale); `model` (the plan model's absolute path); `events(item)` → the item's
event lines; `pr(item)` → the PR, None or "unknown"; `awaiting(slug, question, options, evidence, item, class_hint)`;
`journal(event, text)`.
  * act: `effect()` performs the side effect and returns the plain-JSON dict {rc, out, err} of its command;
    `observer(record)` answers as kyaction.reconcile expects: ("done", {…}) | ("not_done", {…}) | ("unknown", {…}).
    A result is `done` here only when act said `done` AND the command this call itself ran exited 0.

What is decided here is read from evidence each time, never remembered: `start` computes the item's intent again
(so it reads the PR and the events again) and refuses unless that intent has the job's key. A job state therefore
needs none of the header keys that are not launch keys (`action`, `new_head`, …).

Unknown is never a yes: an unreadable model, event list, PR, receipt or decision log, and a command that does not
answer, yield no intent or a non-`done` result.

INTERPRETATION (each is the packet's "(I)" or is needed to make a row executable; the PR lists them):
  I1  `regen` is the model item's `brief.regen` = {outputs[], generator{}, tests[]}; an item without it has no
      declared generated output, so its conflict is `dirty_outside_generated`.
  I2  A REGEN needs the PR head to be the registered head (kyregen.sh starts from it) and no queue authorisation.
  I3  A queue authorisation is bound to the head it was given at: a submission first records that head in
      merge_requests/queued/<item>.json (`ky.merge_queued/1`). A queued PR (`auto_merge` set) is cancelled
      (`queue` false: it submits nothing, so HOLD_MERGES does not park it) with a reason that names what was
      measured: `head_changed` when the PR head is not the recorded head, whatever accepted_head says (the new head
      needs fresh admission); `queued_head_unknown` when no readable record for this PR exists; at the recorded
      head, `dirty` when it is in conflict (REGEN may not push under a queue authorisation) and `not_accepted` when
      accepted_head measures it not accepted. An unknown acceptance at the unchanged recorded head cancels nothing.
  I4  Only a `head_changed` cancel can invalidate, and only the latest pre_merge verdict when it is ACCEPTED at
      another head and the shared predicate measures that the new head does not inherit it (exit 1). Exit 0 keeps
      it. Any other answer (A8) invalidates nothing, journals `inherit unknown` and falls back to requesting ONE
      independent review of the new head (I10) — the job does not fail on that account. The verifier slot is read
      from that verdict's actor (`stream-V:<slot>`). Invalidation, like the review request, is issued even when
      the cancel itself could not be confirmed: the new head is unreviewed either way.
  I10 A review request (A8) is the file <run>/review_requests/<item>.json (`ky.review_request/1`:
      item, pr, head, old_head, reason, job_id, requested_at), written once per head (an existing request for the
      same head is kept). accepted_head honours it: a head whose inheritance the predicate cannot measure answers
      None — "not accepted, review it" — instead of "unknown" when its review is requested, so the build kinds
      launch the VERIFY; a measured answer (exit 0 or 1) and a verdict at the head come first. A queue submission at
      that head retires the request to review_requests/done/ (the acceptance it rests on was measured).
  I5  Under a `[PROTECTED-WINDOW]` title every `platform/migrations/*.sql` path of the PR must be named in
      `platform/scripts/kala_protected_migrations.txt` as it is at the PR head (the PR observation does not say
      which files are added, so every migration file of the PR counts).
  I6  After the hold a parked request whose head is still the PR head needs the surrogate: an `ask` intent raises
      ONE awaiting item (slug `merge-<item, lower case, other characters as "-">`, options `merge` | `hold`); the
      submission follows only a decision line whose `awaiting` is that item, whose latest state is EFFECTIVE or
      EXECUTED and whose `decision` is exactly `merge`. A parked request whose head is no longer the PR head
      authorises and blocks nothing. A submitted request moves to merge_requests/done/.
  I7  COMPLETE: `--artifact-path`, `--operation-receipt` and `--packet-verdict` are the item's absolute
      `detector.path` (what `ky done` compares them with). The completing stream is K for a K item, else S.
  I8  The refusal code of `ky done` (exit 2, stderr `refused: <text>`) is the leading `<code>:` of the text when
      it has one, else the text before its first colon as lower-case words joined by "_".
  I9  The item's worktree is the one `git worktree list --porcelain` shows on branch `kalayantra/<item, lower
      case>`. It is removed (no force) only if it is not the campaign checkout, not locked, `git status
      --porcelain` is empty and its HEAD is the merged PR's head, i.e. everything in it is on GitHub.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from pathlib import Path

KINDS = ("REGEN", "MERGE", "COMPLETE")

UNKNOWN = "unknown"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
ITEM_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
REVIEW_RE = re.compile(r"PR #([0-9]+) @ ([0-9a-f]{40})(?![0-9a-f])")
VSLOT_RE = re.compile(r"stream-V:([A-Za-z0-9._-]+)\Z")
REFUSAL_RE = re.compile(r"refused:\s*(.+)")
CODE_RE = re.compile(r"([a-z][a-z0-9_]*)(?::|\Z)")
DB_CHECK = "Kāla DB Tests"
PROTECTED_TAG = "[PROTECTED-WINDOW]"
PROTECTED_LIST = "platform/scripts/kala_protected_migrations.txt"
MIGRATIONS = "platform/migrations/"
REQUEST_SCHEMA = "ky.merge_request/1"
QUEUED_SCHEMA = "ky.merge_queued/1"
REVIEW_REQUEST_SCHEMA = "ky.review_request/1"
MERGE_OPTIONS = [{"id": "merge", "text": "Submit the PR to the merge queue at that head."},
                 {"id": "hold", "text": "Do not merge; the request stays parked."}]
REGEN_TIMEOUT = 3600            # kyregen.sh merges, regenerates, tests and pushes inside one call
MAX_FILE = 8 * 1024 * 1024      # an artifact, receipt or verdict larger than this is not read


# ── small pure helpers ──────────────────────────────────────────────────────────────────────────────────────────────

def _utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _fp(obj):
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _key(kind, item, identity, evidence_fp):
    twelve = hashlib.sha256(("%s\n%s" % (identity, evidence_fp)).encode("utf-8")).hexdigest()[:12]
    return "%s.%s.%s" % (kind, item, twelve)


def _result(outcome, detail, failure_fp=None):
    return {"outcome": outcome, "detail": detail, "failure_fp": failure_fp}


def _clip(text, limit=600):
    text = text if isinstance(text, str) else ""
    return text if len(text) <= limit else text[:limit] + "…"


def _is_hex40(value):
    return isinstance(value, str) and bool(HEX40.match(value))


def _slug(item):
    return re.sub(r"[^a-z0-9]+", "-", item.lower()).strip("-")


def _path(ctx, name):
    return Path(str(getattr(ctx, name)))


def _script(ctx, name):
    return str(_path(ctx, "fleet") / name)


def _read_bytes(path):
    """The bytes of a regular file, or None (absent, not a file, too large, unreadable)."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > MAX_FILE:
            return None
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def _read_json(path):
    raw = _read_bytes(path)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return None


def _write_json(path, obj):
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)
    tmp = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _intent(kind, item, stream, *, head=None, digest=None, evidence, queue=False, locks=(), verdict_phase=None,
            header):
    evidence_fp = _fp(evidence)
    return {"kind": kind, "item": item, "key": _key(kind, item, head or digest, evidence_fp), "stream": stream,
            "role": kind.lower(), "pool": None, "runner": "script", "queue": queue, "claim": None,
            "locks": list(locks), "tier": None, "not_slot": None, "head": head, "digest": digest,
            "verdict_phase": verdict_phase, "evidence_fp": evidence_fp, "card": None, "packet": None,
            "header": header}


# ── what the tracker, the model and the run directory say ───────────────────────────────────────────────────────────

def _rows(ctx):
    """The item rows of `ky next --json` that are running, in review or ready; None when the tracker is stale."""
    snapshot = ctx.next
    if not isinstance(snapshot, dict):
        return None
    rows, seen = [], set()
    for label in ("running", "ready"):
        for row in snapshot.get(label) or []:
            if isinstance(row, dict) and isinstance(row.get("id"), str) and ITEM_RE.match(row["id"]) \
                    and row["id"] not in seen:
                seen.add(row["id"])
                rows.append(row)
    return rows


def _model(ctx):
    """{item id: model item}; {} when the model cannot be read (its declarations are then unknown)."""
    doc = _read_json(str(ctx.model)) if getattr(ctx, "model", None) else None
    items = doc.get("items") if isinstance(doc, dict) else None
    if not isinstance(items, list):
        return {}
    return {row["id"]: row for row in items if isinstance(row, dict) and isinstance(row.get("id"), str)}


def _events(ctx, item):
    events = ctx.events(item)
    if not isinstance(events, list):
        return None
    return [e for e in events if isinstance(e, dict) and e.get("item") == item]


def _registered(events):
    """(PR number, head) of the item's latest `review` event, or None."""
    for event in reversed(events):
        if event.get("kind") == "item" and event.get("state") == "review":
            found = REVIEW_RE.search(event.get("detail") or "")
            return (int(found.group(1)), found.group(2)) if found else None
    return None


def _pre_merge(events):
    return [e for e in events if e.get("kind") == "verdict" and e.get("phase") == "pre_merge"
            and _is_hex40(e.get("head")) and e.get("artifact_digest") is None]


def _latest_accepted(events):
    """The latest pre_merge verdict if it is ACCEPTED, else None: the acceptance a queue authorisation rests on."""
    verdicts = _pre_merge(events)
    return verdicts[-1] if verdicts and verdicts[-1].get("result") == "ACCEPTED" else None


def _artifact_accepted(events, digest):
    for event in reversed(events):
        if event.get("kind") == "verdict" and event.get("phase") == "artifact" \
                and event.get("artifact_digest") == digest and event.get("head") is None:
            return event.get("result") == "ACCEPTED"
    return False


def _held(ctx, name, where="run"):
    return os.path.lexists(str(_path(ctx, where) / name))


def _worktrees(ctx):
    """`git worktree list --porcelain` of the campaign checkout as [{path, head, branch, locked}], or None."""
    rc, out, _err = ctx.sh(["git", "worktree", "list", "--porcelain"], cwd=str(_path(ctx, "repo")))
    if rc != 0:
        return None
    entries, entry = [], None
    for line in (out or "").splitlines():
        word, _, rest = line.partition(" ")
        if word == "worktree":
            entry = {"path": rest, "head": None, "branch": None, "locked": False}
            entries.append(entry)
        elif entry is not None and word == "HEAD":
            entry["head"] = rest
        elif entry is not None and word == "branch":
            entry["branch"] = rest
        elif entry is not None and word == "locked":
            entry["locked"] = True
    return entries


def _item_worktree(ctx, item, entries):
    branch = "refs/heads/kalayantra/%s" % item.lower()
    return next((e for e in entries or [] if e["branch"] == branch), None)


def _inherit(ctx, item, old_head, new_head):
    """The exit code of the shared predicate (kyverdicts.py inherit): 0 inherits · 1 not · anything else unknown."""
    found = _item_worktree(ctx, item, _worktrees(ctx))
    repo = found["path"] if found else str(_path(ctx, "repo"))
    rc, _out, _err = ctx.sh(["python3", "-B", _script(ctx, "kyverdicts.py"), "inherit", "--repo", repo,
                             "--old-head", old_head, "--new-head", new_head])
    return rc


def _review_request_path(ctx, item):
    return _path(ctx, "run") / "review_requests" / ("%s.json" % item)


def _review_requested(ctx, item, head):
    """True when a readable review request (I10) for this item names this head."""
    doc = _read_json(str(_review_request_path(ctx, item)))
    return isinstance(doc, dict) and doc.get("schema") == REVIEW_REQUEST_SCHEMA and doc.get("item") == item \
        and doc.get("head") == head


def _request_review(ctx, item, number, head, old_head, reason, job_id):
    """Write the one review request for this head (I10) → what happened, in words. An existing request for the
    same head is kept; one for another head is replaced (that head is no longer the PR's)."""
    path = _review_request_path(ctx, item)
    if _review_requested(ctx, item, head):
        return "one independent review of %s already requested (%s)" % (head, path)
    _write_json(path, {"schema": REVIEW_REQUEST_SCHEMA, "item": item, "pr": number, "head": head, "old_head": old_head,
                       "reason": reason, "job_id": job_id, "requested_at": _utc()})
    return "one independent review of %s requested (%s)" % (head, path)


def _retire_review_request(ctx, item, head):
    """A queue submission at `head` rests on a measured acceptance: a request to review that head is moved to done/."""
    path = _review_request_path(ctx, item)
    if _review_requested(ctx, item, head):
        os.makedirs(str(path.parent / "done"), exist_ok=True)
        os.replace(str(path), str(path.parent / "done" / path.name))


def accepted_head(ctx, item):
    """The head at which the item is independently accepted NOW (served to the other modules as ctx.accepted).

    H = the head in the item's latest `review` event. {head: H, via: "direct"} if the latest pre_merge verdict at H
    is ACCEPTED; {head: H, via: H0} if there is no verdict at H, the latest pre_merge verdict is ACCEPTED at an
    older H0 and the shared predicate says H inherits it; None if not accepted; "unknown" if that cannot be told —
    unless a review of H is requested (I10): then None, so that the review is launched.
    """
    events = _events(ctx, item)
    if events is None:
        return UNKNOWN
    registered = _registered(events)
    if registered is None:
        return None
    head = registered[1]
    at_head = [v for v in _pre_merge(events) if v["head"] == head]
    if at_head:
        return {"head": head, "via": "direct"} if at_head[-1].get("result") == "ACCEPTED" else None
    latest = _latest_accepted(events)
    if latest is None:
        return None
    rc = _inherit(ctx, item, latest["head"], head)
    if rc == 0:
        return {"head": head, "via": latest["head"]}
    if rc == 1:
        return None
    return None if _review_requested(ctx, item, head) else UNKNOWN


# ── REGEN ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def _dirty(pr):
    return pr.get("mergeable") == "CONFLICTING" or pr.get("merge_state") == "DIRTY"


def _regen(ctx, item, owner, decl, pr, events, journal):
    number, head = pr.get("number"), pr.get("head")
    registered = _registered(events)
    if registered is None or registered != (number, head):
        return None                                               # I2: kyregen.sh starts from the registered head
    brief = decl.get("brief") if isinstance(decl.get("brief"), dict) else {}
    regen = brief.get("regen")
    outputs = regen.get("outputs") if isinstance(regen, dict) else None
    if not isinstance(outputs, list) or not outputs or not all(isinstance(o, str) and o for o in outputs):
        if journal:
            ctx.journal("dirty_outside_generated", "%s: PR #%d is in conflict with main and the item declares no "
                        "generated outputs" % (item, number))
        return None
    repo = str(_path(ctx, "repo"))
    rc, out, _err = ctx.sh(["git", "merge-tree", "--write-tree", "--name-only", "origin/main", head], cwd=repo)
    if rc != 1:                                                   # 0: no conflict here · else: git did not answer
        return None
    lines = (out or "").split("\n")[1:]                           # line 1 is the tree; a blank line ends the names
    conflicted = lines[:lines.index("")] if "" in lines else lines
    if not conflicted:
        return None
    outside = sorted(set(conflicted) - set(outputs))
    if outside:
        if journal:
            ctx.journal("dirty_outside_generated", "%s: PR #%d conflicts outside its declared generated outputs: %s"
                        % (item, number, ", ".join(outside)))
        return None
    rc, out, _err = ctx.sh(["git", "rev-parse", "--verify", "origin/main^{commit}"], cwd=repo)
    base = (out or "").strip()
    if rc != 0 or not _is_hex40(base):
        return None
    return _intent("REGEN", item, owner, head=head, locks=["item.%s" % item],
                   evidence={"base_sha": base, "conflicted": sorted(set(conflicted))},
                   header={"pr": number, "registered_head": head, "base_sha": base, "queue_authorised": False,
                           "regen": regen})


def _start_regen(ctx, job):
    job_id = job["job_id"]
    rc, _out, err = ctx.sh(["bash", _script(ctx, "kyregen.sh"), job_id],
                           env={"KY_RUN_ID": job_id, "KY_ROLE": "dispatcher",
                                "KY_CONTROLLER_ID": str(ctx.controller_id)},
                           timeout=REGEN_TIMEOUT)
    if rc == 0:
        return _result("done", "kyregen.sh pushed and registered the new head")
    detail = "kyregen.sh exit %s: %s" % ("unknown" if rc is None else rc, _clip(err, 200) or "no message")
    fp = "regen_unknown" if rc is None else "regen_exit_%s" % rc
    if rc in (3, 4):
        return _result("blocked", detail, fp)
    if rc in (5, 6):
        return _result("failed", detail, fp)
    return _result("refused", detail, fp)


# ── MERGE ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def _checks_green(pr):
    checks = pr.get("checks")
    return (isinstance(checks, dict) and DB_CHECK in checks
            and all(isinstance(c, dict) and c.get("status") == "SUCCESS" for c in checks.values()))


def _protected_ok(ctx, pr, head):
    """True when the protected-window listing is satisfied (or the title asks for none); False otherwise (I5)."""
    if PROTECTED_TAG not in (pr.get("title") or ""):
        return True
    files = pr.get("files")
    if not isinstance(files, list):
        return False
    paths = [f if isinstance(f, str) else f.get("path") if isinstance(f, dict) else None for f in files]
    if any(not isinstance(p, str) for p in paths):
        return False
    migrations = [p for p in paths if p.startswith(MIGRATIONS) and p.endswith(".sql")]
    if not migrations:
        return True
    rc, out, _err = ctx.sh(["git", "show", "%s:%s" % (head, PROTECTED_LIST)], cwd=str(_path(ctx, "repo")))
    if rc != 0:
        return False
    listed = {line.split("#", 1)[0].strip() for line in (out or "").splitlines()} - {""}
    return all(os.path.basename(p) in listed for p in migrations)


def _request_path(ctx, item):
    return _path(ctx, "run") / "merge_requests" / ("%s.json" % item)


def _valid_request(doc, item):
    return (isinstance(doc, dict) and doc.get("schema") == REQUEST_SCHEMA and doc.get("item") == item
            and type(doc.get("pr")) is int and _is_hex40(doc.get("registered_head")))


def _queued_path(ctx, item):
    return _path(ctx, "run") / "merge_requests" / "queued" / ("%s.json" % item)


def _queued_head(ctx, item, number):
    """The head this PR's queue authorisation was given at, from the submission's own record (I3), or None."""
    doc = _read_json(str(_queued_path(ctx, item)))
    if (isinstance(doc, dict) and doc.get("schema") == QUEUED_SCHEMA and doc.get("item") == item
            and type(doc.get("pr")) is int and doc["pr"] == number and _is_hex40(doc.get("queued_head"))):
        return doc["queued_head"]
    return None


def _awaiting_ids(ctx, item, head):
    """The ids of the awaiting items (open or done) that ask about merging this item at this head."""
    ids = []
    for directory in (_path(ctx, "run") / "awaiting", _path(ctx, "run") / "awaiting" / "done"):
        for path in sorted(directory.glob("AW-*-merge-%s.json" % _slug(item))) if directory.is_dir() else []:
            doc = _read_json(str(path))
            if isinstance(doc, dict) and doc.get("id") == path.stem and doc.get("item") == item \
                    and head in (doc.get("question") or ""):
                ids.append(doc["id"])
    return ids


def _authorising_decision(ctx, awaiting_ids):
    """The id of a surrogate decision that says `merge` on one of those awaiting items and is EFFECTIVE or EXECUTED
    on its latest line; None when there is none or the log cannot be read line by line."""
    raw = _read_bytes(str(_path(ctx, "run") / "DECISIONS_SURROGATE.jsonl"))
    if raw is None:
        return None
    decisions, order = {}, []
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except ValueError:
            return None                                           # a line that cannot be read may be a veto
        if not isinstance(doc, dict) or not isinstance(doc.get("id"), str):
            return None
        seen = decisions.setdefault(doc["id"], {"awaiting": set(), "decision": set(), "class": set(), "state": None})
        if doc["id"] not in order:
            order.append(doc["id"])
        for name in ("awaiting", "decision", "class"):
            if name in doc:
                seen[name].add(doc[name] if isinstance(doc[name], str) else None)
        seen["state"] = doc.get("state")
    for decision_id in reversed(order):
        seen = decisions[decision_id]
        if (len(seen["awaiting"]) == 1 and next(iter(seen["awaiting"])) in awaiting_ids
                and seen["decision"] == {"merge"} and "hard_stop" not in seen["class"]
                and seen["state"] in ("EFFECTIVE", "EXECUTED")):
            return decision_id
    return None


def _merge(ctx, item, owner, pr):
    number, head = pr.get("number"), pr.get("head")
    if type(number) is not int or not _is_hex40(head):
        return None
    if pr.get("auto_merge"):                                      # I3
        queued = _queued_head(ctx, item, number)
        if queued is None:
            reason = "queued_head_unknown"
        elif queued != head:
            reason = "head_changed"
        elif _dirty(pr):
            reason = "dirty"
        else:
            accepted = accepted_head(ctx, item)
            if accepted == UNKNOWN:
                return None                                       # unknown at the queued head: neither yes nor no
            if isinstance(accepted, dict) and accepted.get("head") == head:
                return None                                       # queued at the accepted head: GitHub's turn
            reason = "not_accepted"
        return _intent("MERGE", item, owner, head=queued or head, verdict_phase="pre_merge",
                       evidence={"action": "cancel", "pr": number, "queued_head": queued, "new_head": head,
                                 "reason": reason},
                       header={"action": "cancel", "reason": reason, "pr": number, "registered_head": queued,
                               "new_head": head, "queue_authorised": True})
    if _dirty(pr) or _held(ctx, "HOLD", "root"):
        return None
    accepted = accepted_head(ctx, item)
    if not isinstance(accepted, dict) or accepted.get("head") != head:
        return None                                               # the head-match guard
    if not _checks_green(pr) or pr.get("base") != "main" or not _protected_ok(ctx, pr, head):
        return None
    decision = None
    request_path = _request_path(ctx, item)
    if os.path.lexists(str(request_path)) and not _held(ctx, "HOLD_MERGES"):
        request = _read_json(str(request_path))
        if not _valid_request(request, item):
            return None                                           # a parked request that cannot be read: unknown
        if request["registered_head"] == head and request["pr"] == number:      # I6
            awaiting_ids = _awaiting_ids(ctx, item, head)
            if not awaiting_ids:
                return _intent("MERGE", item, owner, head=head, verdict_phase="pre_merge",
                               evidence={"action": "ask", "pr": number, "recorded_at": request.get("recorded_at")},
                               header={"action": "ask", "pr": number, "registered_head": head,
                                       "queue_authorised": False})
            decision = _authorising_decision(ctx, awaiting_ids)
            if decision is None:
                return None
    header = {"action": "submit", "pr": number, "registered_head": head, "queue_authorised": False}
    if decision:
        header["decision"] = decision
    return _intent("MERGE", item, owner, head=head, queue=True, verdict_phase="pre_merge",
                   evidence={"action": "submit", "pr": number, "base": "main", "decision": decision}, header=header)


def _acted(ctx, action_id, kind, inputs, target, run, observer):
    """One side effect inside its action record → (status, rc, out, err, ran). `run()` → (rc, out, err)."""
    seen = {}

    def effect():
        rc, out, err = run()
        seen.update(rc=rc, out=out or "", err=err or "")
        return {"rc": rc, "out": _clip(out), "err": _clip(err)}

    status, _record = ctx.act(action_id, kind, inputs, target, effect, observer)
    return status, seen.get("rc"), seen.get("out", ""), seen.get("err", ""), bool(seen)


def _start_submit(ctx, job, intent):
    item, head, number = intent["item"], intent["head"], intent["header"]["pr"]
    if _held(ctx, "HOLD_MERGES") or _held(ctx, "HOLD", "root"):
        return _result("refused", "a hold is present: no queue submission", "hold")
    argv = ["gh", "pr", "merge", str(number), "--auto", "--squash", "--match-head-commit", head]

    def observer(_record):
        now = ctx.pr(item)
        if not isinstance(now, dict):
            return "unknown", {"pr": None}
        seen = {"pr": now.get("number"), "head": now.get("head"), "state": now.get("state"),
                "auto_merge": bool(now.get("auto_merge"))}
        queued = now.get("head") == head and (now.get("auto_merge") or now.get("state") == "MERGED")
        return ("done" if queued else "not_done"), seen

    action_id = "ACT-merge-%s" % job["job_id"]
    _write_json(_queued_path(ctx, item), {"schema": QUEUED_SCHEMA, "item": item, "pr": number, "queued_head": head,
                                          "job_id": job["job_id"], "action_id": action_id,
                                          "decision": intent["header"].get("decision"), "recorded_at": _utc()})
    status, rc, _out, err, ran = _acted(
        ctx, action_id, "merge",
        {"argv": argv, "pr": number, "registered_head": head, "decision": intent["header"].get("decision")},
        {"kind": "pull_request", "item": item, "pr": number, "head": head},
        lambda: ctx.sh(argv, cwd=str(_path(ctx, "repo"))), observer)
    if status != "done" or (ran and rc != 0):
        return _result("failed", "PR #%d was not queued at %s (record %s, gh exit %s): %s"
                       % (number, head, status, rc if ran else "not run", _clip(err, 200) or "no message"),
                       "merge_unknown" if status == "unknown" else "merge_failed")
    request_path = _request_path(ctx, item)
    request = _read_json(str(request_path))
    if _valid_request(request, item) and request["registered_head"] == head:
        os.makedirs(str(request_path.parent / "done"), exist_ok=True)
        os.replace(str(request_path), str(request_path.parent / "done" / request_path.name))
    _retire_review_request(ctx, item, head)
    return _result("done", "PR #%d queued (auto-merge, squash) at the accepted head %s" % (number, head))


def _start_cancel(ctx, job, intent, events):
    item, header = intent["item"], intent["header"]
    number, new_head = header["pr"], header["new_head"]
    argv = ["gh", "pr", "merge", str(number), "--disable-auto"]

    def observer(_record):
        now = ctx.pr(item)
        if not isinstance(now, dict):
            return "unknown", {"pr": None}
        return ("not_done" if now.get("auto_merge") else "done"), {"pr": now.get("number"),
                                                                    "auto_merge": bool(now.get("auto_merge"))}

    status, rc, _out, err, ran = _acted(
        ctx, "ACT-cancel-%s" % job["job_id"], "merge_cancel",
        {"argv": argv, "pr": number, "reason": header["reason"], "new_head": new_head},
        {"kind": "pull_request", "item": item, "pr": number, "head": new_head},
        lambda: ctx.sh(argv, cwd=str(_path(ctx, "repo"))), observer)
    cancelled = status == "done" and not (ran and rc != 0)
    problems = [] if cancelled else ["the queue authorisation of PR #%d was not cancelled (record %s, gh exit %s): %s"
                                     % (number, status, rc if ran else "not run", _clip(err, 200) or "no message")]
    fp = None if cancelled else ("cancel_unknown" if status == "unknown" else "cancel_failed")
    done = ["auto-merge of PR #%d disabled" % number] if cancelled else []
    latest = _latest_accepted(events)
    if header["reason"] == "head_changed" and latest and latest["head"] != new_head:      # I4
        old = latest["head"]
        inherits = _inherit(ctx, item, old, new_head)
        if inherits == 0:
            done.append("%s inherits the acceptance at %s; it needs fresh admission" % (new_head, old))
        elif inherits != 1:                                                                  # I10 (A8)
            text = ("PR #%d head changed from %s to %s after queueing; whether the new head inherits the acceptance "
                    "at %s is unknown (kyverdicts.py inherit exit %s): nothing invalidated"
                    % (number, header["registered_head"], new_head, old, "unknown" if inherits is None else inherits))
            requested = _request_review(ctx, item, number, new_head, old, text, job["job_id"])
            done.append("%s; %s" % (text, requested))
            ctx.journal("inherit unknown", "%s: %s; %s" % (item, text, requested))
        else:
            slot = VSLOT_RE.match(latest.get("actor") or "")
            reason = "PR #%d head changed to %s after queueing; the new head does not inherit the review" \
                % (number, new_head)
            rc = None
            if slot:
                rc, _out, err = ctx.sh(["python3", "-B", _script(ctx, "kyverdicts.py"), "invalidate", "--item", item,
                                        "--phase", "pre_merge", "--head", old, "--vslot", slot.group(1),
                                        "--reason", reason, "--as", str(ctx.controller_id)])
            if rc == 0:
                done.append("the acceptance at %s is REJECTED" % old)
                ctx.journal("verdict invalidation", "%s: %s; ACCEPTED at %s invalidated" % (item, reason, old))
            else:
                problems.append("the acceptance at %s was NOT invalidated (%s)" % (
                    old, "its verdict names no verifier slot" if not slot else "kyverdicts.py exit %s: %s"
                    % (rc, _clip(err, 200) or "no message")))
                fp = fp or ("invalidate_no_vslot" if not slot else "invalidate_exit_%s" % rc)
                ctx.journal("verdict invalidation", "%s: %s; invalidation of ACCEPTED at %s FAILED" % (item, reason, old))
    if problems:
        return _result("failed", "; ".join(problems + done), fp)
    return _result("done", "; ".join(done))


def _start_ask(ctx, intent):
    item, head, number = intent["item"], intent["head"], intent["header"]["pr"]
    request_path = _request_path(ctx, item)
    request = _read_json(str(request_path)) or {}
    question = ("Merge PR #%d of %s at its independently accepted head %s? The request was parked under HOLD_MERGES "
                "at %s; the hold is gone, the head is unchanged and the required checks are green. Answer with the "
                "option id as the decision." % (number, item, head, request.get("recorded_at")))
    ctx.awaiting("merge-%s" % _slug(item), question, [dict(o) for o in MERGE_OPTIONS], [str(request_path)], item,
                 "routine")
    return _result("done", "awaiting item raised for the parked merge of PR #%d at %s" % (number, head))


# ── COMPLETE ────────────────────────────────────────────────────────────────────────────────────────────────────────

def _strict_open(row):
    """The row's open strict dependencies; None when the row does not say (unknown waits)."""
    strict = row.get("deps_open_strict", row.get("deps_open"))
    return strict if isinstance(strict, list) else None


def _complete_code(ctx, item, stream, row, pr):
    number, head, merge = pr.get("number"), pr.get("head"), pr.get("merge_commit")
    merge = merge.get("oid") if isinstance(merge, dict) else merge
    if type(number) is not int or not _is_hex40(head) or not _is_hex40(merge) or _strict_open(row) != []:
        return None
    return _intent("COMPLETE", item, stream, head=head, verdict_phase="pre_merge",
                   evidence={"type": "code", "pr": number, "merge_commit": merge},
                   header={"completion_kind": "code", "pr": number, "registered_head": head, "merge_commit": merge,
                           "argv": ["done", item, "--pr", str(number), "--reviewed-head", head]})


def _complete_typed(ctx, item, stream, kind, row, decl, events):
    detector = decl.get("detector") if isinstance(decl.get("detector"), dict) else {}
    path = detector.get("path")
    if not isinstance(path, str) or not os.path.isabs(path) or _strict_open(row) != []:
        return None
    raw = _read_bytes(path)
    if raw is None:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    evidence = {"type": kind, "path": path}
    if kind == "artifact":
        argv = ["done", item, "--artifact-path", path]
    else:
        try:
            doc = json.loads(raw.decode("utf-8"))
        except ValueError:
            return None
        if not isinstance(doc, dict):
            return None
        if kind == "operation":
            operation_id = doc.get("operation_id")
            if doc.get("status") != "COMPLETED" or doc.get("item_id") != item \
                    or not isinstance(operation_id, str) or not operation_id:
                return None
            evidence["operation_id"] = operation_id
            argv = ["done", item, "--operation-receipt", path, "--operation-id", operation_id]
        else:
            if doc.get("result") != "ACCEPTED" or doc.get("item") != item:
                return None
            argv = ["done", item, "--packet-verdict", path]
    if not _artifact_accepted(events, digest):
        return None
    return _intent("COMPLETE", item, stream, digest=digest, verdict_phase="artifact", evidence=evidence,
                   header={"completion_kind": kind, "argv": argv})


def _refusal_code(err):
    found = REFUSAL_RE.search(err or "")
    if not found:
        return "refused_unknown"
    text = found.group(1).strip()
    coded = CODE_RE.match(text)
    if coded:
        return coded.group(1)
    return re.sub(r"[^a-z0-9]+", "_", text.split(":", 1)[0].lower()).strip("_")[:60] or "refused_unknown"


def _remove_worktree(ctx, item, head):
    """`git worktree remove` of the item's worktree if it is clean and pushed (I9) → what happened, in words."""
    repo = str(_path(ctx, "repo"))
    entries = _worktrees(ctx)
    if entries is None:
        return "worktree list unknown: nothing removed"
    found = _item_worktree(ctx, item, entries)
    if found is None:
        return "no worktree on its branch"
    path = found["path"]
    if found is entries[0] or os.path.realpath(path) == os.path.realpath(repo):
        return "its branch is checked out in the campaign checkout: nothing removed"
    if found["locked"]:
        return "worktree %s is locked: kept" % path
    if found["head"] != head:
        return "worktree %s is not at the merged PR head: kept" % path
    rc, out, _err = ctx.sh(["git", "status", "--porcelain"], cwd=path)
    if rc != 0 or (out or "").strip():
        return "worktree %s is not clean: kept" % path
    rc, _out, err = ctx.sh(["git", "worktree", "remove", path], cwd=repo)
    if rc != 0:
        return "git worktree remove %s exit %s: %s" % (path, rc, _clip(err, 200) or "no message")
    ctx.sh(["git", "worktree", "prune"], cwd=repo)
    return "worktree %s removed" % path


def _start_complete(ctx, job, intent):
    item, header = intent["item"], intent["header"]
    argv = header["argv"]

    def observer(_record):
        events = _events(ctx, item)
        if events is None:
            return "unknown", {"events": None}
        states = [e.get("state") for e in events if e.get("kind") == "item" and not e.get("step")]
        return ("done" if states and states[-1] == "done" else "not_done"), {"latest_state": states[-1] if states else None}

    status, rc, _out, err, ran = _acted(
        ctx, "ACT-done-%s" % job["job_id"], "tracker_event",
        {"argv": ["ky"] + argv, "stream": intent["stream"]},
        {"kind": "item", "item": item, "state": "done", "identity": intent["head"] or intent["digest"]},
        lambda: ctx.ky(*argv, stream=intent["stream"]), observer)
    if ran and rc == 2:
        code = _refusal_code(err)
        ctx.journal("completion refused", "%s: ky done refused: %s (%s)" % (item, code, _clip(err, 200).strip()))
        return _result("blocked", "ky done refused: %s" % _clip(err, 200).strip(), code)
    if ran and rc != 0:
        return _result("failed", "ky done exit %s: %s" % ("unknown" if rc is None else rc,
                                                        _clip(err, 200) or "no message"),
                       "done_unknown" if rc is None else "done_exit_%s" % rc)
    if status != "done":
        return _result("failed", "the done event of %s is not observed (record %s)" % (item, status),
                       "done_%s" % ("unknown" if status == "unknown" else "unobserved"))
    detail = "guarded completion recorded (%s)" % header["completion_kind"]
    if header["completion_kind"] == "code":
        detail += "; " + _remove_worktree(ctx, item, intent["head"])
    return _result("done", detail)


# ── the engine's entry points ───────────────────────────────────────────────────────────────────────────────────────

def _item_intent(ctx, row, model, journal):
    """The one intent an item's evidence supports now, or None."""
    item, status = row["id"], row.get("status")
    decl = model.get(item) or {}
    kind = decl.get("completion_kind") or row.get("completion_kind")
    owner = row.get("owner") or decl.get("owner")
    if not isinstance(owner, str) or status not in ("review", "running", "ready"):
        return None
    completer = "K" if owner == "K" else "S"                     # K completes K items; S its own and accepted N/V
    if kind in ("artifact", "operation", "packet"):
        events = _events(ctx, item)
        return None if events is None else _complete_typed(ctx, item, completer, kind, row, decl, events)
    if kind != "code" or status != "review":
        return None
    events = _events(ctx, item)
    pr = ctx.pr(item)
    if events is None or not isinstance(pr, dict):
        return None
    if pr.get("state") == "MERGED":
        return _complete_code(ctx, item, completer, row, pr)
    if pr.get("state") != "OPEN":
        return None
    intent = _merge(ctx, item, owner, pr)
    if intent is None and _dirty(pr) and not pr.get("auto_merge"):
        intent = _regen(ctx, item, owner, decl, pr, events, journal)
    return intent


def _order(intent):
    if intent["kind"] == "MERGE":
        return 0 if intent["header"]["action"] == "cancel" else 2
    return 1 if intent["kind"] == "COMPLETE" else 3


def intents(ctx):
    """Read-only: what REGEN, MERGE and COMPLETE work the evidence supports now. Writes nothing but journal lines."""
    rows = _rows(ctx)
    if rows is None:
        return []
    model = _model(ctx)
    found = [i for i in (_item_intent(ctx, row, model, True) for row in rows) if i is not None]
    return sorted(found, key=_order)                              # stable: tracker order within a group


def start(ctx, job):
    """Run one script job → {outcome, detail, failure_fp}. Nothing is done unless the item's evidence, read again,
    still gives the intent the job was opened for."""
    kind, item = job.get("kind"), job.get("item")
    if kind not in KINDS:
        return _result("refused", "kind %r is not one of %s" % (kind, ", ".join(KINDS)), "unknown_kind")
    rows = _rows(ctx)
    if rows is None:
        return _result("refused", "the tracker snapshot is stale", "stale")
    row = next((r for r in rows if r["id"] == item), None)
    intent = _item_intent(ctx, row, _model(ctx), False) if row else None
    if intent is None or intent["kind"] != kind or intent["key"] != job.get("key"):
        return _result("refused", "the evidence no longer gives %s for %s at this identity" % (kind, item),
                       "stale_intent")
    if kind == "REGEN":
        return _start_regen(ctx, job)
    if kind == "COMPLETE":
        return _start_complete(ctx, job, intent)
    action = intent["header"]["action"]
    if action == "submit":
        return _start_submit(ctx, job, intent)
    if action == "cancel":
        return _start_cancel(ctx, job, intent, _events(ctx, item) or [])
    return _start_ask(ctx, intent)


def park(ctx, intent):
    """Under HOLD_MERGES a queue submission becomes a durable local request (owner decision D-6 revised): one file
    per item, no GitHub call. → {parked, path, detail}."""
    header = intent.get("header") if isinstance(intent.get("header"), dict) else {}
    item, number, head = intent.get("item"), header.get("pr"), header.get("registered_head")
    if intent.get("kind") != "MERGE" or intent.get("queue") is not True or header.get("action") != "submit":
        return {"parked": False, "path": None, "detail": "not a queue submission"}
    if not isinstance(item, str) or not ITEM_RE.match(item) or type(number) is not int or not _is_hex40(head):
        return {"parked": False, "path": None, "detail": "the intent names no item, PR and head"}
    if not _held(ctx, "HOLD_MERGES"):
        return {"parked": False, "path": None, "detail": "HOLD_MERGES is absent"}
    path = _request_path(ctx, item)
    if os.path.lexists(str(path)):
        existing = _read_json(str(path))
        if not _valid_request(existing, item):
            return {"parked": False, "path": str(path), "detail": "an unreadable request is already there: kept"}
        if existing["pr"] == number and existing["registered_head"] == head:
            return {"parked": True, "path": str(path), "detail": "already parked at %s" % existing.get("recorded_at")}
    _write_json(path, {"schema": REQUEST_SCHEMA, "item": item, "pr": number, "registered_head": head,
                       "recorded_at": _utc()})
    return {"parked": True, "path": str(path), "detail": "parked: PR #%d at %s" % (number, head)}
