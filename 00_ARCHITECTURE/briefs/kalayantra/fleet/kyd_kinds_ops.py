#!/usr/bin/env python3
"""kyd_kinds_ops.py — the operation and ruling kinds of the KĀLA-YANTRA v3 dispatcher (relaunch plan v2.7 §6).

REQUEST-PREP · PRE-ACCEPT · EXECUTE · POST-READBACK · MODEL · RULING · SURROGATE · PLAN.

The engine (`kydispatch.py`) calls three functions and nothing else:

    intents(ctx)       read-only: the jobs that are owed now, as intent records (see `_intent`)
    start(ctx, job)    before a launch: a result (the job's work was script work, or the launch is refused), or None → launch
    finish(ctx, job)   after the job's process group is gone: a result {outcome, detail, failure_fp}

The module keeps no state of its own. What has been done is read from files under `ctx.run` and from the tracker's
events, so a restart changes nothing: the same evidence gives the same job key, and the engine's lock on `job.<key>`
is what makes one job of it. Importing it runs nothing; standard library only (`kyveto` is imported on demand when
the engine's ctx offers no `veto_status`).

Every status here is earned (CLAUDE.md §N.8): `done` is only returned from a detector that measures the claim (a
file read back at the digest the job was started for, an inbox without the message, an event that was not there at the
launch); evidence that cannot be read is `interrupted`, never a guess. An answer `intents` cannot recognise (the
tracker's, the plan model's, the table's, the inbox's, a record's) is unknown: no job is derived from it and the tick
says so in one `ops_unknown` journal line (I-15) — it is never read as "nothing owed". Nothing in this file starts
executor.py, holds a credential, dispatches a workflow or runs a tracker-state `ky` verb.

INTERPRETATIONS (the packet's "(I)" — what the plan leaves open, and what is done here):
  I-1  Items are the rows of `ctx.next`, the live tracker's `ky next --json`: {stream: "", version: <int>, running[],
       ready[], blocked[]} (pravaha_tracker server.py /api/next), each row {id, owner, status, …} as
       state.build_snapshot writes it; the status is the row's (running: running | review; ready: ready; blocked:
       blocked | failed | parked | conflict). Waiting and done items are not shown and are not looked for. A row
       carries no brief, done_by or join: those (and completion_kind) are read from the plan model the engine's ctx
       names (`ctx.model`, an absolute path; {items: [{id, completion_kind, brief{op, migration}, done_by, join}]}).
       Anything else — no fresh answer, another shape, one stream's answer, an unreadable model, a row the model
       does not know — is unknown (I-15), never an empty list.
  I-2  `brief.op` is what the plan model states (its brief_keys.op: "executor operation kinds, in order"): a list.
       A step is the name of a table kind (the only form the model carries today), or — an interpretation no
       producer emits yet, kept so that a request a PLAN job has fully stated needs no model — an object {kind,
       args, kyd, requested_by?, operation_id?, idempotency_key?, chart_id?, lease_id?, reviewed_commit?,
       expires_at?, timeout_s?}. No brief.op is no operation; any other shape, or a step naming no table kind, is
       unknown (I-15). Steps are prepared in order: step n is owed once every earlier step has a prepared request
       whose executor receipt is COMPLETED and measured and whose latest artifact verdict at that receipt's sha256
       is ACCEPTED. operation_id defaults to OP-<item> (OP-<item>-s<n> for step n of several); idempotency_key to
       the operation_id; requested_by to `adhikarin` (the N lane) when the entry admits it; chart_id to the
       canonical chart. A field that cannot be derived (kyd; args when the step states none and the entry allows
       some; for a production kind lease_id, reviewed_commit, expires_at) makes the job a model job — with the plan
       model as it is today, every job. That job's request must carry every derived field unchanged and add
       nothing; it fills only the missing ones. A step with any valid prepared record of the item at that step,
       under any operation id, is prepared.
  I-3  A request is "accepted by executor.validate" if `static_validate` — its field, entry, requester, argument and
       production-field checks, kept equal to executor.py by a test that imports both — passes. What only the executor
       can know (lease liveness, ancestry of reviewed_commit, idempotency, capability) stays the executor's.
  I-4  The prepared request is `$KY_RUN/ops/prepared/<operation_id>.json` {schema ky.op_prepared/1, operation_id, item,
       step, request, request_sha256, prepared_by, prepared_by_slot}; request_sha256 is the executor's digest; step is
       the 1-based place of the request in brief.op.
  I-5  Only a production kind needs a PRE-ACCEPT; a read-only kind goes straight from prepared to EXECUTE.
  I-6  EXECUTE submits `$KY_RUN/ops/requests/<operation_id>.json` and nothing else. A receipt of that request that is
       FAILED, REFUSED or INTERRUPTED raises one awaiting item (slug exec-<operation>-<12 hex of the receipt digest>)
       and never a second submission.
  I-7  POST-READBACK (a): a K-owned `code` item with data-writing metadata whose PR is MERGED with a merge commit, no
       verdict yet at (post_deploy, merge commit), and a COMPLETED, measured readback receipt of that item
       (kind readback_sql / migration_readback). None → one journal line, by a script intent, per merge commit.
       "Measured": status COMPLETED, exit_code 0, and an output file whose sha256 is the receipt's output_sha256 and
       that is not empty. Nothing here measures that the deployment has landed, or that the receipt was taken after
       the merge: the packet's trigger is the merge commit plus a receipt, and this kind claims no more than that.
       (b): a prepared operation whose executor receipt is COMPLETED and measured, for that request and item, with no
       artifact verdict at the receipt's sha256. The quiescence record, when present, is part of the evidence.
  I-8  A job's author identity: (a) the actor of the item's latest review event (`stream-K:<slot>`; its slot is the
       intent's not_slot); (b) the preparer of the request (`stream-N:<slot>`, or `controller:<id>` for a script
       preparation). Unknown → nothing is published.
  I-9  Job keys: job_key(kind, item, head or digest, evidence_fp) = "<kind>.<item>.<12 hex of sha256 of the canonical
       JSON [head-or-digest, evidence_fp]>". Locks list the job lock first.
  I-10 Tracker events are the lines of EVENTS.jsonl as pravaha_tracker writes them (events.py validate, cli.py):
       a review is {kind: "item", state: "review"} and a block {kind: "item", state: "blocked"} (a `step` line is
       neither); a verdict is {kind: "verdict", phase, head | artifact_digest, result}. The author is the line's
       `actor` (`stream-<S>` or `stream-<S>:<slot>`); there is no lane or slot key. MODEL's and PLAN's "after the
       launch" is recovered from the job's own evidence_fp (the event count / packet set it was started on).
  I-11 PLAN's wave boundary: an open executable item is shown by `ky next` and nothing is in flight — none ready,
       none in review, none running with an admission record (kyd_admit's {item, base_sha, test_digests, result},
       read back as that item's; a `running` item without one is not admitted work; one that cannot be read is
       unknown). An unknown tracker or plan model is no boundary.
  I-12 Cards: ADHIKARIN (N/S operators), PARIKSAKA (verifiers), OWNER_SURROGATE; Opus 5.5; effort xhigh for the PLAN
       class (REQUEST-PREP / MODEL / PLAN), high otherwise.
  I-13 Kind order within a tick: EXECUTE, PRE-ACCEPT, REQUEST-PREP, POST-READBACK, SURROGATE, RULING, MODEL, PLAN.
  I-14 SURROGATE's move to awaiting/done/ (review r4 KO4-B1): kyveto.status() takes a row's state from the model-written
       log when the handler accepted no terminal state, so the row counts only with a record behind it. The handled
       record's and the row's class are both `veto`; the row is this item's and carries no hard_stop, anomaly, refused
       or unresolved flag; its state is its latest line's; EXECUTED needs executed_by_handler true (the handler's DONE
       execution record); VETOED needs the owner's veto command. FAILED never moves an item: status() shows no handler
       record behind a FAILED line, so the owner-wait stays open for the owner. A hard_stop item is never moved here.
  I-15 Unknown is said, once a tick: `intents` collects what it could not read or recognise (and a stated request
       the executor's own rules refuse) and writes one journal line (`ops_unknown`) naming each; `start` and `finish`
       answer `refused` / `interrupted` for the same. A kind that is listed but not enabled is a known wait. A handled
       marker counts only when read back as that record: one that is merely present handles nothing (the job is owed
       again). A prepared record that does not load could be any item's, so no request is prepared while it is there.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re

KINDS = ("REQUEST-PREP", "PRE-ACCEPT", "EXECUTE", "POST-READBACK", "MODEL", "RULING", "SURROGATE", "PLAN")
ORDER = ("EXECUTE", "PRE-ACCEPT", "REQUEST-PREP", "POST-READBACK", "SURROGATE", "RULING", "MODEL", "PLAN")

OPS_TABLE_PATH = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
PACKETS_REL = "00_ARCHITECTURE/briefs/kalayantra/packets"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")                      # executor.py, byte for byte (a test compares them)
SAFE_ARG = re.compile(r"^[A-Za-z0-9_.:,=/@+-]{1,300}$")
SHA = re.compile(r"^[0-9a-f]{7,40}$")
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
MESSAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")      # kyloop.ID_RE
AWAITING_ID = re.compile(r"^AW-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+$")
OWNER_DECISION_SUFFIX = ".owner_decision.json"
V_SLOTS = ("v1", "v2", "v3", "v4")
READBACK_KINDS = ("readback_sql", "migration_readback")
MODEL_EXCLUDED = ("C-3", "C-4")
DECISION_CLASSES = ("routine", "veto", "hard_stop")
DECISION_STATES = ("PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED", "VETOED", "FAILED")
MOVE_STATES = ("EXECUTED", "VETOED")             # the terminal states a record of the handler or owner can stand behind (I-14)
RECEIPT_AWAITED = ("FAILED", "REFUSED", "INTERRUPTED")
VERDICT_VALUES = ("ACCEPTED", "REJECTED")
OPUS = "claude-opus-5-5"
CARDS = {"adhikarin": "ADHIKARIN.md", "verifier": "PARIKSAKA.md", "surrogate": "OWNER_SURROGATE.md"}
PREPARED_SCHEMA = "ky.op_prepared/1"
HANDLED_SCHEMA = "ky.handled/1"
NEXT_BUCKETS = (("running", ("running", "review")), ("ready", ("ready",)),       # server.py /api/next, cli.py cmd_next
                ("blocked", ("blocked", "failed", "parked", "conflict")))
EVENT_KINDS = ("item", "decision", "heartbeat", "note", "metric", "message", "ack", "claim", "verdict")   # events.py KINDS
UNKNOWN_EVENT = "ops_unknown"


# ───────────────────────────────────────── small helpers ─────────────────────────────────────────

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_canonical(obj):
    return sha_text(canonical(obj))


def file_sha(path):
    try:
        return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path, obj, exclusive=False):
    """Write-then-rename. `exclusive`: link the finished file into place, never replacing one (FileExistsError)."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    try:
        if exclusive:
            os.link(tmp, path)
        else:
            os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def write_once(path, obj):
    """An exclusive write that accepts the identical record already in place (a replayed effect), nothing else."""
    try:
        write_json(path, obj, exclusive=True)
    except FileExistsError:
        if canonical(read_json(path)) != canonical(obj):
            raise


def request_digest(req):
    """executor.request_digest, byte for byte (A8 §3.9): sha256 of the request as sorted compact JSON without `acceptance_receipt`,
    `expires_at` and any `*_expires_at` lease-expiry field — a lease renewal or an expiry extension never voids an acceptance."""
    bound = {k: v for k, v in req.items() if k not in ("acceptance_receipt", "expires_at") and not k.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def job_key(kind, item, ident, evidence_fp):
    return "%s.%s.%s" % (kind, item, sha_text(canonical([ident, evidence_fp]))[:12])


def action_part(text):
    return re.sub(r"[^A-Za-z0-9_.-]", "-", str(text))


def _run(ctx):
    return pathlib.Path(str(ctx.run))


def _fleet(ctx):
    return pathlib.Path(str(ctx.fleet))


def _repo(ctx):
    return pathlib.Path(str(ctx.repo))


def _now(ctx):
    now = getattr(ctx, "now", None)
    if callable(now):
        return now()
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _result(outcome, detail, failure_fp=None):
    return {"outcome": outcome, "detail": detail, "failure_fp": failure_fp}


def _fail(kind, item, code, detail):
    """A failed result; its fingerprint is the class of failure (kind, item, code), never the free text."""
    return _result("failed", "%s: %s" % (code, detail), sha_canonical([kind, item, code]))


def _from_act(kind, item, status, result, done_detail):
    if status == "done":
        return _result("done", done_detail)
    if status == "failed":
        return _fail(kind, item, "action_failed", "the action record failed: %s" % (result,))
    return _result("interrupted", "the action's outcome is unknown; the next tick reconciles it")


def _truthy_meta(value):
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, str):
        return value.strip() not in ("", "NONE", "None", "none", "null")
    if isinstance(value, list):
        return bool(value)
    return value is True


def _say(unknown, text):
    """Note one thing this tick could not read or recognise (I-15); `unknown` is the tick's list, or None."""
    if unknown is not None and text not in unknown:
        unknown.append(text)


def _brief(model_item):
    return model_item.get("brief") if isinstance(model_item.get("brief"), dict) else {}


def _writes_data(model_item):
    brief = _brief(model_item)
    return _truthy_meta(brief.get("migration")) or _truthy_meta(brief.get("op"))


def _tracker_rows(ctx):
    """(rows, None): the item rows of the live tracker's `ky next --json`, by id; or (None, why) when the answer is
    not that — no fresh answer, the snapshot fallback (no stream, no version), one stream's answer, or another shape."""
    nxt = ctx.next() if callable(ctx.next) else ctx.next
    if nxt is None:
        return None, "the engine holds no fresh `ky next --json` answer"
    if (not isinstance(nxt, dict) or isinstance(nxt.get("version"), bool) or not isinstance(nxt.get("version"), int)
            or nxt.get("stream") != ""):
        return None, "`ky next --json` is not the live tracker's all-stream answer {stream: \"\", version, running, ready, blocked}"
    rows = []
    for bucket, statuses in NEXT_BUCKETS:
        part = nxt.get(bucket)
        if not isinstance(part, list):
            return None, "`ky next --json` carries no `%s` list" % bucket
        for row in part:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row.get("status") not in statuses:
                return None, "a `%s` row of `ky next --json` is not a tracker item row with that status" % bucket
            rows.append(row)
    if len({r["id"] for r in rows}) != len(rows):
        return None, "`ky next --json` shows an item twice"
    return sorted(rows, key=lambda r: r["id"]), None


def _plan_items(ctx):
    """({id: item}, None) of the plan model the engine's ctx names, or (None, why)."""
    path = getattr(ctx, "model", None)
    if not isinstance(path, (str, os.PathLike)) or not str(path):
        return None, "the engine's ctx names no plan model"
    doc = read_json(path)
    items = doc.get("items") if isinstance(doc, dict) else None
    if not isinstance(items, list) or any(not isinstance(i, dict) or not isinstance(i.get("id"), str) for i in items):
        return None, "the plan model %s is unreadable or carries no items list" % path
    return {i["id"]: i for i in items}, None


def _items(ctx, unknown=None):
    """The tracker's shown rows joined to their plan-model items: [{id, owner, status, model}] by id (I-1). None when
    the tracker's answer or the model is unknown, or a row is not an item of the model (two different plans)."""
    rows, why = _tracker_rows(ctx)
    model = None
    if rows is not None:
        model, why = _plan_items(ctx)
    if model is not None:
        absent = [r["id"] for r in rows if r["id"] not in model]
        if not absent:
            return [{"id": r["id"], "owner": r.get("owner"), "status": r["status"], "model": model[r["id"]]} for r in rows]
        why = "tracker item %s is not in the plan model %s" % (", ".join(absent), getattr(ctx, "model", None))
    _say(unknown, why)
    return None


def _events(ctx, item_id):
    """The item's lines of EVENTS.jsonl, or None: not a list, or a line that is not a tracker event (I-10) — a line
    this module cannot read may be the review, the block or the verdict it is looking for."""
    ev = ctx.events(item_id)
    return ev if isinstance(ev, list) and all(isinstance(e, dict) and e.get("kind") in EVENT_KINDS for e in ev) else None


def _is_review(event):
    return event.get("kind") == "item" and event.get("state") == "review" and not event.get("step")


def _is_block(event):
    return event.get("kind") == "item" and event.get("state") == "blocked" and not event.get("step")


def _verdicts(events, phase, head=None, digest=None):
    return [e for e in events if e.get("kind") == "verdict" and e.get("phase") == phase
            and ((head is not None and e.get("head") == head) or (digest is not None and e.get("artifact_digest") == digest))]


def _has_verdict(events, phase, head=None, digest=None):
    return bool(_verdicts(events, phase, head, digest))


def _latest_review(events):
    reviews = [e for e in events if _is_review(e)]
    return reviews[-1] if reviews else None


def _actor_slot(actor):
    """`stream-K:b2` → b2; an actor without a slot (or no actor) → None."""
    return actor.split(":", 1)[1] or None if isinstance(actor, str) and actor.startswith("stream-") and ":" in actor else None


def _marker(path, **fields):
    """A handled record read back: True only when it is that record (the schema and each named field). A file that is
    merely present, truncated or of another thing handles nothing."""
    have = read_json(path)
    return isinstance(have, dict) and have.get("schema") == HANDLED_SCHEMA and all(have.get(k) == v for k, v in fields.items())


def _card(ctx, name):
    return str(_fleet(ctx) / "cards" / CARDS[name])


def _packet_path(ctx, item_id):
    best, best_n = None, -1
    directory = _repo(ctx) / PACKETS_REL
    pattern = re.compile(r"^PACKET_%s_v([0-9]+)\.md$" % re.escape(str(item_id)))
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return None
    for name in names:
        m = pattern.match(name)
        if m and int(m.group(1)) > best_n:
            best, best_n = directory / name, int(m.group(1))
    return str(best) if best else None


def _intent(ctx, kind, item, *, stream, runner, evidence_fp, pool=None, tier=None, head=None, digest=None, verdict_phase=None,
            locks=(), card=None, packet=None, not_slot=None, effort=None, claim=None):
    ident = head or digest
    key = job_key(kind, item, ident, evidence_fp)
    all_locks = ["job." + key] + list(locks)
    model = runner == "model"
    selected_model = OPUS if model else None
    if model:
        import kyd_admit as admit
        if kind == "SURROGATE":
            cfg, _ = admit.surrogate_config(ctx)
            selected_model = cfg["model"] if cfg is not None else None  # admission refuses a missing/invalid template
            effort = "high"
        elif admit.job_engine(ctx, kind) == "codex":
            selected_model, effort = admit.CODEX_MODEL, "high"
    return {
        "kind": kind, "item": item, "key": key, "stream": stream, "role": kind.lower(), "pool": pool, "runner": runner,
        "queue": None, "claim": claim, "locks": all_locks, "tier": tier, "not_slot": not_slot, "head": head, "digest": digest,
        "verdict_phase": verdict_phase, "evidence_fp": evidence_fp, "card": card, "packet": packet,
        "header": {"model": selected_model, "effort": effort if model else None, "card_path": card,
                   "packet_path": packet, "head": head, "digest": digest, "verdict_phase": verdict_phase,
                   "evidence_fp": evidence_fp, "locks": all_locks},
    }


def _find(ctx, kind, job):
    for intent, payload in CANDIDATES[kind](ctx):
        if intent["key"] == job.get("key"):
            return intent, payload
    return None


# ───────────────────────────────────────── the operations table and the request ─────────────────────────────────────────

def read_table(ctx):
    """The `ops` mapping of executor_ops.json at origin/main (the only place the executor trusts), or None."""
    rc, out, _ = ctx.sh(["git", "-C", str(_repo(ctx)), "show", "origin/main:" + OPS_TABLE_PATH], timeout=60)
    if rc != 0 or not out:
        return None
    try:
        ops = json.loads(out)["ops"]
    except (ValueError, KeyError, TypeError):
        return None
    return ops if isinstance(ops, dict) else None


def entry_usable(entry):
    return (isinstance(entry, dict) and bool(entry.get("enabled"))
            and "TO_BE_SET" not in str(entry.get("script", "")) and "TO_BE_SET" not in str(entry.get("needs", "")))


def _utc(value):
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)


def static_validate(req, entry):
    """The part of executor.validate that needs nothing outside the request and its table entry (I-3). A reason or None."""
    for k in ("operation_id", "kind", "item_id", "idempotency_key", "requested_by", "kyd"):
        if not req.get(k):
            return "missing field %s" % k
    if not SAFE_ID.match(str(req["operation_id"])):
        return "operation_id has unsafe characters"
    if not isinstance(entry, dict):
        return "unknown kind %s" % req["kind"]
    if not entry.get("enabled"):
        return "kind %s is not enabled" % req["kind"]
    if "TO_BE_SET" in str(entry.get("script", "")) or "TO_BE_SET" in str(entry.get("needs", "")):
        return "operation script not yet reviewed/landed"
    if req["requested_by"] not in entry.get("requesters", ["adhikarin"]):
        return "requested_by %s may not request %s" % (req["requested_by"], req["kind"])
    args = req.get("args") or {}
    if not isinstance(args, dict):
        return "args is not an object"
    bad = [k for k in args if k not in entry.get("allowed_args", [])]
    if bad:
        return "disallowed args %s" % bad
    if any(not SAFE_ARG.match(str(v)) for v in args.values()):
        return "an argument value has unsafe characters"
    if entry.get("production"):
        if req.get("chart_id") != CANONICAL_CHART:
            return "chart_id is not the canonical chart"
        if not req.get("lease_id"):
            return "lease_id required for a production operation"
        if not SHA.match(str(req.get("reviewed_commit", ""))):
            return "reviewed_commit required for a production operation"
        try:
            _utc(req["expires_at"])
        except (KeyError, TypeError, ValueError):
            return "a timezone-qualified request expires_at is required"
    return None


def required_checks(kind):
    """executor.validate's attestation rule (A8 §5), names of the checks that must be true: `dry_run_passed` for a mutating kind.
    `backup_taken`, `restore_verified` and the table's `required_rows` are retired as preconditions (SR-A12-BACKUP-REMOVAL)."""
    required = []
    if kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun"):
        required.append("dry_run_passed")
    return required


def op_steps(model_item):
    """brief.op as steps (I-2): [] when the item states no operation, None when it is not the plan model's list of
    kind names (or stated steps). A kind name becomes {kind: <name>}."""
    op = _brief(model_item).get("op")
    if op is None:
        return []
    if not isinstance(op, list):
        return None
    steps = []
    for step in op:
        if isinstance(step, str) and step:
            steps.append({"kind": step})
        elif isinstance(step, dict) and isinstance(step.get("kind"), str) and step["kind"]:
            steps.append(step)
        else:
            return None
    return steps


def derive_request(item_id, op, entry, step=1, steps=1):
    """(request, missing): the request of step `step` of `steps` as far as brief.op and the table determine it (I-2)."""
    operation_id = op.get("operation_id") or ("OP-" + item_id if steps == 1 else "OP-%s-s%d" % (item_id, step))
    requesters = entry.get("requesters", ["adhikarin"])
    req = {"operation_id": operation_id, "kind": op["kind"], "item_id": item_id,
           "idempotency_key": op.get("idempotency_key") or operation_id,
           "requested_by": op.get("requested_by") or ("adhikarin" if "adhikarin" in requesters else None),
           "kyd": op.get("kyd"), "args": dict(op.get("args") or {}) if isinstance(op.get("args") or {}, dict) else op.get("args")}
    if op.get("timeout_s") is not None:
        req["timeout_s"] = op["timeout_s"]
    missing = []
    if "args" not in op and entry.get("allowed_args"):
        missing.append("args")                           # a kind name states no arguments; the entry takes some
    if entry.get("production"):
        req["chart_id"] = op.get("chart_id") or CANONICAL_CHART
        for k in ("lease_id", "reviewed_commit", "expires_at"):
            req[k] = op.get(k)
            if not op.get(k):
                missing.append(k)
    if not req["kyd"]:
        missing.append("kyd")
    if not req["requested_by"]:
        missing.append("requested_by")
    return req, missing


def request_unbound(request, item_id, op, entry, step=1, steps=1):
    """A model-authored request may fill only the fields derive_request left missing; every field it fixes (and no
    other) must be there with its derived value. The first difference, or None."""
    derived, missing = derive_request(item_id, op, entry, step, steps)
    extra = sorted(k for k in request if k not in derived)
    if extra:
        return "fields neither derived nor missing: %s" % extra
    for k in sorted(derived):
        if k not in missing and (k not in request or request[k] != derived[k]):
            return "%s differs from the value brief.op and the table fix" % k
    return None


def _prep_digest(item_id, step, op, entry, missing):
    return sha_canonical({"item": item_id, "step": step, "op": op, "entry": entry, "missing": missing})


# ───────────────────────────────────────── prepared / accepted / submitted state ─────────────────────────────────────────

def prepared_dir(run):
    return run / "ops" / "prepared"


def load_prepared(path):
    doc = read_json(path)
    if not isinstance(doc, dict) or doc.get("schema") != PREPARED_SCHEMA or not isinstance(doc.get("request"), dict):
        return None
    req = doc["request"]
    opid = req.get("operation_id")
    step = doc.get("step")
    if (not isinstance(opid, str) or not SAFE_ID.match(opid) or pathlib.Path(path).name != opid + ".json" or doc.get("operation_id") != opid
            or doc.get("item") != req.get("item_id") or doc.get("request_sha256") != request_digest(req)
            or isinstance(step, bool) or not isinstance(step, int) or step < 1):
        return None
    return doc


def all_prepared(run, unknown=None):
    """The valid prepared records, by file name. One that is there but does not load is unknown (I-15), not absent."""
    try:
        names = sorted(os.listdir(prepared_dir(run)))
    except FileNotFoundError:
        return []
    except OSError:
        _say(unknown, "the prepared requests under %s could not be listed" % prepared_dir(run))
        return []
    out = []
    for name in names:
        if name.endswith(".json"):
            doc = load_prepared(prepared_dir(run) / name)
            if doc is not None:
                out.append((prepared_dir(run) / name, doc))
            else:
                _say(unknown, "the prepared record %s is not a valid %s" % (prepared_dir(run) / name, PREPARED_SCHEMA))
    return out


SUBMITTED_DIRS = ("requests", "inflight", "done")       # executor.py: REQ → INFLIGHT (RUNNING receipt after the move) → DONE


def _acceptance_path(run, opid):
    return run / "ops" / "acceptance" / (opid + ".json")


def _receipt_path(run, opid):
    return run / "ops" / "receipts" / (opid + ".json")


def _submitted(run, opid):
    return any((run / "ops" / d / (opid + ".json")).exists() for d in SUBMITTED_DIRS + ("receipts",))


def acceptance_matches(acc, prepared):
    req = prepared["request"]
    return (isinstance(acc, dict) and acc.get("result") == "ACCEPTED" and acc.get("operation_id") == req["operation_id"]
            and acc.get("by") in V_SLOTS and acc.get("request_sha256") == prepared["request_sha256"]
            and acc.get("reviewed_commit") == req.get("reviewed_commit"))


def _awaiting_recorded(run, slug):
    """An awaiting item of this slug is raised: a readable record whose id is its file name, open or done."""
    for directory in (run / "awaiting", run / "awaiting" / "done"):
        try:
            names = os.listdir(directory)
        except OSError:
            continue
        for n in names:
            if n.startswith("AW-") and n.endswith("-%s.json" % slug):
                doc = read_json(directory / n)
                if isinstance(doc, dict) and doc.get("id") == n[:-len(".json")]:
                    return True
    return False


def _measured_receipt(path, doc):
    """A COMPLETED executor receipt with a measured readback: exit 0 and an output that still has its digest."""
    if not isinstance(doc, dict) or doc.get("status") != "COMPLETED":
        return False
    code = doc.get("exit_code")
    if isinstance(code, bool) or code != 0:
        return False
    out_file, out_sha = doc.get("output_file"), doc.get("output_sha256")
    if not isinstance(out_file, str) or not out_file or not isinstance(out_sha, str) or not HEX64.match(out_sha):
        return False
    out_path = pathlib.Path(out_file)
    if not out_path.is_absolute():
        out_path = pathlib.Path(path).parent / out_path
    try:
        body = out_path.read_bytes()
    except OSError:
        return False
    return bool(body) and hashlib.sha256(body).hexdigest() == out_sha


def _readback_receipts(run, item_id):
    """The item's measured COMPLETED readback receipts, newest first, in a total order (ts, operation_id)."""
    directory = run / "ops" / "receipts"
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    found = []
    for name in names:
        if not name.endswith(".json"):
            continue
        doc = read_json(directory / name)
        if (isinstance(doc, dict) and doc.get("item_id") == item_id and doc.get("kind") in READBACK_KINDS
                and _measured_receipt(directory / name, doc)):
            found.append((str(doc.get("ts", "")), str(doc.get("operation_id", "")), directory / name, doc))
    found.sort(key=lambda r: (r[0], r[1]), reverse=True)
    return [(path, doc) for _, _, path, doc in found]


# ───────────────────────────────────────── REQUEST-PREP ─────────────────────────────────────────

TABLE_UNKNOWN = "the operations table at origin/main could not be read"
NO_KIND = "the prepared request %s names %r, which is no kind of the operations table"


def _owed_step(ctx, run, item_id, steps, prepared, unknown=None):
    """(n, step) of the first step with no prepared request, once every step before it is complete: a prepared
    request of that step with a COMPLETED, measured receipt whose latest artifact verdict is ACCEPTED (I-2). Else None."""
    events = False
    for n, op in enumerate(steps, 1):
        mine = [doc for _, doc in prepared if doc["item"] == item_id and doc["step"] == n]
        if not mine:
            return n, op
        receipts = [r for r in (_b_receipt(run, doc) for doc in mine) if r is not None]
        if n == len(steps) or not receipts:
            return None
        if events is False:
            events = _events(ctx, item_id)
        if events is None:
            _say(unknown, "the events of %s could not be read" % item_id)
            return None
        latest = [(_verdicts(events, "artifact", digest=sha) or [{}])[-1].get("result") for _, sha in receipts]
        if "ACCEPTED" not in latest:
            return None
    return None


def _c_request_prep(ctx, unknown=None):
    table = read_table(ctx)
    if table is None:
        _say(unknown, TABLE_UNKNOWN)
        return []
    items = _items(ctx, unknown)
    if items is None:
        return []
    run, out, unloadable = _run(ctx), [], []
    prepared = all_prepared(run, unloadable)
    for why in unloadable:
        _say(unknown, why)
    if unloadable:
        return []                                        # whose request that record was is unknown: no second one on a guess
    for item in items:
        if item["owner"] != "N" or item["status"] != "ready" or item["model"].get("completion_kind") != "operation":
            continue
        steps = op_steps(item["model"])
        if steps is None:
            _say(unknown, "brief.op of %s is not the plan model's list of operation kinds" % item["id"])
            continue
        owed = _owed_step(ctx, run, item["id"], steps, prepared, unknown)
        if owed is None:
            continue
        step, op = owed
        entry = table.get(op["kind"])
        if entry is None:
            _say(unknown, "step %d of %s names %r, which is no kind of the operations table" % (step, item["id"], op["kind"]))
            continue
        if not entry_usable(entry):
            continue                                     # listed, not enabled yet: the item waits for the entry
        req, missing = derive_request(item["id"], op, entry, step, len(steps))
        opid = req["operation_id"]
        if not isinstance(opid, str) or not SAFE_ID.match(opid):
            _say(unknown, "step %d of %s states an operation id the executor refuses" % (step, item["id"]))
            continue
        if os.path.lexists(str(prepared_dir(run) / (opid + ".json"))):
            _say(unknown, "the operation id %s of step %d of %s is another prepared record's" % (opid, step, item["id"]))
            continue
        if missing:
            digest = _prep_digest(item["id"], step, op, entry, missing)
            intent = _intent(ctx, "REQUEST-PREP", item["id"], stream="N", runner="model", pool="builder", tier="opus", digest=digest,
                             evidence_fp=digest, card=_card(ctx, "adhikarin"), effort="xhigh")
            out.append((intent, {"op": op, "entry": entry, "missing": missing, "step": step, "steps": len(steps)}))
            continue
        refused = static_validate(req, entry)
        if refused is not None:                          # fully stated, and the executor would refuse it: nothing to prepare, said
            _say(unknown, "step %d of %s states a request the executor refuses (%s)" % (step, item["id"], refused))
            continue
        digest = request_digest(req)
        fp = sha_canonical({"request_sha256": digest, "entry": entry})
        intent = _intent(ctx, "REQUEST-PREP", item["id"], stream="N", runner="script", digest=digest, evidence_fp=fp)
        out.append((intent, {"op": op, "entry": entry, "request": req, "step": step, "steps": len(steps)}))
    return out


def _prepared_doc(job, request, slot, step):
    return {"schema": PREPARED_SCHEMA, "operation_id": request["operation_id"], "item": request["item_id"], "step": step,
            "request": request, "request_sha256": request_digest(request), "prepared_by": job.get("controller_id"),
            "prepared_by_slot": slot}


def _write_prepared(ctx, job, request, slot, item, step):
    run = _run(ctx)
    path = prepared_dir(run) / (request["operation_id"] + ".json")
    doc = _prepared_doc(job, request, slot, step)

    def effect():
        write_once(path, doc)
        return {"path": str(path), "request_sha256": doc["request_sha256"]}

    def observer(record):
        have = load_prepared(path)
        if have is not None and have["request_sha256"] == doc["request_sha256"] and have["step"] == step:
            return "done", {"path": str(path), "request_sha256": doc["request_sha256"]}
        return ("not_done", "absent") if not os.path.lexists(str(path)) else ("unknown", "another prepared record is in place")

    status, result = ctx.act("PREPARE-%s-%s" % (action_part(request["operation_id"]), doc["request_sha256"][:12]), "request_prep",
                             {"operation_id": request["operation_id"], "request_sha256": doc["request_sha256"]},
                             {"path": str(path)}, effect, observer)
    return _from_act("REQUEST-PREP", item, status, result, "prepared %s at %s" % (request["operation_id"], doc["request_sha256"]))


def _start_request_prep(ctx, job):
    found = _find(ctx, "REQUEST-PREP", job)
    if found is None:
        return _result("refused", "the operation, the table or the prepared state changed since the intent")
    intent, payload = found
    if intent["runner"] == "model":
        return None
    return _write_prepared(ctx, job, payload["request"], None, job["item"], payload["step"])


def _model_prep_payload(ctx, job):
    """({op, entry, step, steps}, None) when brief.op and the table still give the model job's digest, whatever has
    been prepared since; else (None, the result that stops the finish)."""
    table = read_table(ctx)
    if table is None:
        return None, _result("interrupted", TABLE_UNKNOWN)
    unknown = []
    items = _items(ctx, unknown)
    if items is None:
        return None, _result("interrupted", "the item cannot be read: %s" % "; ".join(unknown))
    item = next((i for i in items if i["id"] == job.get("item")), None)
    steps = op_steps(item["model"]) if item else None
    for step, op in enumerate(steps or [], 1):
        entry = table.get(op["kind"])
        if entry_usable(entry):
            _, missing = derive_request(item["id"], op, entry, step, len(steps))
            if missing and _prep_digest(item["id"], step, op, entry, missing) == job.get("digest"):
                return {"op": op, "entry": entry, "step": step, "steps": len(steps)}, None
    return None, _fail("REQUEST-PREP", job.get("item"), "evidence_changed", "the operation or the table changed during the job")


def _finish_request_prep(ctx, job):
    run = _run(ctx)
    for path, doc in all_prepared(run):                                  # a script job: its digest is the derived request's
        if doc["item"] == job.get("item") and doc["request_sha256"] == job.get("digest"):
            return _result("done", "prepared record %s carries the request digest" % path)
    if job.get("exit_code") != 0:
        return _fail("REQUEST-PREP", job.get("item"), "job_exit_nonzero", "exit %r" % (job.get("exit_code"),))
    request = read_json(pathlib.Path(str(job.get("job_scratch"))) / "request.json")
    if not isinstance(request, dict):
        return _result("interrupted", "the job proposed no request.json")
    payload, stop = _model_prep_payload(ctx, job)
    if stop is not None:
        return stop
    # No kyboundary check: a builder-pool job gets no prepared view, so `check` could only answer 3 (review r2 KO2-B1);
    # the packet names the boundary for PRE-ACCEPT and POST-READBACK. The binding checks and the digest read-back gate this.
    if request.get("item_id") != job["item"] or request.get("kind") != payload["op"]["kind"]:
        return _fail("REQUEST-PREP", job["item"], "request_for_another_operation", "item_id/kind do not match the item's operation")
    unbound = request_unbound(request, job["item"], payload["op"], payload["entry"], payload["step"], payload["steps"])
    if unbound:
        return _fail("REQUEST-PREP", job["item"], "request_not_bound", unbound)
    reason = static_validate(request, payload["entry"])
    if reason:
        return _fail("REQUEST-PREP", job["item"], "request_invalid", reason)
    path = prepared_dir(run) / (request["operation_id"] + ".json")
    if os.path.lexists(str(path)):          # a repeated finish only when it is exactly the record this finish writes
        if canonical(read_json(path)) == canonical(_prepared_doc(job, request, job.get("slot"), payload["step"])):
            return _result("done", "prepared record %s is the checked request's, by this job" % path)
        return _fail("REQUEST-PREP", job["item"], "already_prepared", request["operation_id"])
    return _write_prepared(ctx, job, request, job.get("slot"), job["item"], payload["step"])


def _boundary(ctx, job):
    """`kyboundary.sh check <job_id>`: None when intact, else the result that stops the finish."""
    rc, _, _ = ctx.sh(["bash", str(_fleet(ctx) / "kyboundary.sh"), "check", str(job["job_id"])], timeout=300)
    if rc == 0:
        return None
    if rc == 1:
        return _fail(job.get("kind"), job.get("item"), "boundary_not_intact", "kyboundary.sh check exited 1")
    return _result("interrupted", "the boundary could not be judged (kyboundary.sh check exited %r)" % (rc,))


# ───────────────────────────────────────── PRE-ACCEPT ─────────────────────────────────────────

def _c_pre_accept(ctx, unknown=None):
    table = read_table(ctx)
    if table is None:
        _say(unknown, TABLE_UNKNOWN)
        return []
    run, out = _run(ctx), []
    for _, doc in all_prepared(run, unknown):
        req = doc["request"]
        entry = table.get(req["kind"])
        if not isinstance(entry, dict):
            _say(unknown, NO_KIND % (req["operation_id"], req["kind"]))
            continue
        if not entry.get("production"):
            continue
        if _submitted(run, req["operation_id"]) or os.path.lexists(str(_acceptance_path(run, req["operation_id"]))):
            continue                                     # an acceptance file is there; whether it is this request's is EXECUTE's to say
        fp = sha_canonical({"request_sha256": doc["request_sha256"], "entry": entry})
        out.append((_intent(ctx, "PRE-ACCEPT", doc["item"], stream="V", runner="model", pool="verifier", tier="opus",
                            digest=doc["request_sha256"], evidence_fp=fp, card=_card(ctx, "verifier"),
                            packet=_packet_path(ctx, doc["item"]), not_slot=doc.get("prepared_by_slot"), effort="high"),
                    {"prepared": doc, "entry": entry}))
    return out


def _start_pre_accept(ctx, job):
    if _find(ctx, "PRE-ACCEPT", job) is None:
        return _result("refused", "the prepared request, its table entry or its acceptance state changed since the intent")
    return None


def _finish_pre_accept(ctx, job):
    item, run = job.get("item"), _run(ctx)
    if job.get("exit_code") != 0:
        return _fail("PRE-ACCEPT", item, "job_exit_nonzero", "exit %r" % (job.get("exit_code"),))
    slot = job.get("slot")
    if slot not in V_SLOTS:
        return _fail("PRE-ACCEPT", item, "slot_unknown", "the reviewing slot is %r" % (slot,))
    prepared = next((doc for _, doc in all_prepared(run) if doc["item"] == item and doc["request_sha256"] == job.get("digest")), None)
    if prepared is None:
        return _fail("PRE-ACCEPT", item, "prepared_changed", "no prepared request carries the digest the job reviewed")
    req = prepared["request"]
    table = read_table(ctx)
    entry = table.get(req["kind"]) if table else None
    if not isinstance(entry, dict):
        return _result("interrupted", "the operations table at origin/main could not be read")
    if prepared.get("prepared_by_slot") == slot:
        return _fail("PRE-ACCEPT", item, "not_independent", "the preparer and the signer are the same slot")
    proposed = read_json(pathlib.Path(str(job.get("job_scratch"))) / "acceptance.json")
    if not isinstance(proposed, dict):
        return _result("interrupted", "the job proposed no acceptance.json")
    boundary = _boundary(ctx, job)
    if boundary is not None:
        return boundary
    if proposed.get("result") != "ACCEPTED":
        return _fail("PRE-ACCEPT", item, "not_accepted", "the verifier did not accept the request")
    if (proposed.get("operation_id") != req["operation_id"] or proposed.get("request_sha256") != prepared["request_sha256"]
            or proposed.get("by") != slot or proposed.get("reviewed_commit") != req.get("reviewed_commit")):
        return _fail("PRE-ACCEPT", item, "acceptance_not_bound", "operation, digest, signer or reviewed commit differ from the request")
    checks, rows = proposed.get("checks"), proposed.get("rows")
    rows = {} if rows is None else rows
    if not isinstance(checks, dict) or not isinstance(rows, dict):
        return _fail("PRE-ACCEPT", item, "attestation_missing", "checks / rows are not objects")
    if any(checks.get(k) is not True for k in required_checks(req["kind"])):
        return _fail("PRE-ACCEPT", item, "attestation_missing", "a required backup / dry-run check is not true")
    record = {"result": "ACCEPTED", "operation_id": req["operation_id"], "by": slot, "reviewed_commit": req.get("reviewed_commit"),
              "ts": _now(ctx), "request_sha256": prepared["request_sha256"], "rows": rows, "checks": checks}
    path = _acceptance_path(run, req["operation_id"])
    if path.exists():                       # a repeated finish only when it is, apart from ts, the record this finish writes
        existing = read_json(path)
        if isinstance(existing, dict) and {k: v for k, v in existing.items() if k != "ts"} == {k: v for k, v in record.items() if k != "ts"}:
            return _result("done", "acceptance of %s by %s is already in place" % (req["operation_id"], slot))
        return _fail("PRE-ACCEPT", item, "acceptance_exists", req["operation_id"])

    def effect():
        write_once(path, record)
        return {"path": str(path)}

    def observer(rec):
        have = read_json(path)
        if isinstance(have, dict) and have.get("request_sha256") == record["request_sha256"] and have.get("by") == slot:
            return "done", {"path": str(path)}
        return ("not_done", "absent") if not path.exists() else ("unknown", "another acceptance is in place")

    status, result = ctx.act("ACCEPT-%s-%s" % (action_part(req["operation_id"]), prepared["request_sha256"][:12]), "pre_accept",
                             {"operation_id": req["operation_id"], "request_sha256": prepared["request_sha256"], "by": slot},
                             {"path": str(path)}, effect, observer)
    return _from_act("PRE-ACCEPT", item, status, result, "acceptance of %s written by %s" % (req["operation_id"], slot))


# ───────────────────────────────────────── EXECUTE ─────────────────────────────────────────

def _exec_slug(opid, receipt_sha):
    base = re.sub(r"[^a-z0-9-]+", "-", ("exec-" + opid).lower()).strip("-")
    return "%s-%s" % (base, receipt_sha[:12])


def _c_execute(ctx, unknown=None):
    table = read_table(ctx)
    if table is None:
        _say(unknown, TABLE_UNKNOWN)
        return []
    run, out = _run(ctx), []
    for ppath, doc in all_prepared(run, unknown):
        req, sha = doc["request"], doc["request_sha256"]
        opid = req["operation_id"]
        entry = table.get(req["kind"])
        if not isinstance(entry, dict):
            _say(unknown, NO_KIND % (opid, req["kind"]))
            continue
        if not _submitted(run, opid):
            acc_path, acc_sha = _acceptance_path(run, opid), None
            if entry.get("production"):
                if not acceptance_matches(read_json(acc_path), doc):
                    if os.path.lexists(str(acc_path)):       # present, and not this request's acceptance: nobody will redo it
                        _say(unknown, "the acceptance %s is not an ACCEPTED record of the prepared request %s" % (acc_path, sha))
                    continue
                acc_sha = file_sha(acc_path)
            fp = sha_canonical({"request_sha256": sha, "acceptance_sha256": acc_sha})
            out.append((_intent(ctx, "EXECUTE", doc["item"], stream="N", runner="script", digest=sha, evidence_fp=fp),
                        {"variant": "submit", "prepared": doc, "acceptance_path": acc_path, "production": bool(entry.get("production"))}))
            continue
        rpath = _receipt_path(run, opid)
        if not os.path.lexists(str(rpath)):
            continue                                     # submitted, no receipt yet
        receipt, rsha = read_json(rpath), file_sha(rpath)
        if not isinstance(receipt, dict) or rsha is None or not isinstance(receipt.get("status"), str):
            _say(unknown, "the executor receipt %s could not be read" % rpath)
            continue
        if receipt.get("request_sha256") not in (sha, None):
            _say(unknown, "the executor receipt %s is of another request than the prepared one" % rpath)
            continue
        if receipt.get("request_sha256") is None and receipt["status"] not in RECEIPT_AWAITED:
            _say(unknown, "the executor receipt %s names no request" % rpath)
            continue
        if receipt["status"] not in RECEIPT_AWAITED or _awaiting_recorded(run, _exec_slug(opid, rsha)):
            continue                                     # RUNNING or COMPLETED; or the owner-wait is already raised
        fp = sha_canonical({"request_sha256": sha, "receipt_sha256": rsha})
        out.append((_intent(ctx, "EXECUTE", doc["item"], stream="N", runner="script", digest=rsha, evidence_fp=fp),
                    {"variant": "await", "prepared": doc, "prepared_path": ppath, "receipt_path": rpath, "receipt": receipt,
                     "receipt_sha256": rsha}))
    return out


def _start_execute(ctx, job):
    found = _find(ctx, "EXECUTE", job)
    if found is None:
        already = _finish_execute(ctx, job)                              # the effect is already in place: a repeated start
        if already["outcome"] == "done":
            return already
        return _result("refused", "the prepared request, its acceptance or its receipt changed since the intent")
    _, p = found
    run, doc = _run(ctx), found[1]["prepared"]
    req, opid, sha = doc["request"], doc["request"]["operation_id"], doc["request_sha256"]
    if p["variant"] == "submit":
        path = run / "ops" / "requests" / (opid + ".json")
        submitted = dict(req)
        if p["production"]:
            submitted["acceptance_receipt"] = str(p["acceptance_path"])

        def effect():
            write_once(path, submitted)
            return {"path": str(path), "request_sha256": sha}

        def observer(record):
            have = read_json(path)
            if isinstance(have, dict) and request_digest(have) == sha:
                return "done", {"path": str(path), "request_sha256": sha}
            return ("not_done", "absent") if not path.exists() else ("unknown", "another request is in place")

        status, result = ctx.act("SUBMIT-%s-%s" % (action_part(opid), sha[:12]), "submit", {"operation_id": opid, "request_sha256": sha},
                                 {"path": str(path)}, effect, observer)
        return _from_act("EXECUTE", job["item"], status, result, "request %s submitted for the executor" % opid)
    slug = _exec_slug(opid, p["receipt_sha256"])
    status_word = p["receipt"].get("status")

    def effect():
        ctx.awaiting(slug, "The executor receipt for %s is %s (%s). Nothing is resubmitted; how should the operation proceed?"
                     % (opid, status_word, p["receipt"].get("reason") or "no reason recorded"),
                     [{"id": "new-request", "text": "Prepare a new request for the operation (new operation id and idempotency key)."},
                      {"id": "abandon", "text": "Abandon the operation."}],
                     [str(p["receipt_path"]), str(p["prepared_path"])], job["item"], "unknown")
        return {"awaiting_slug": slug}

    def observer(record):
        return ("done", {"awaiting_slug": slug}) if _awaiting_recorded(run, slug) else ("not_done", "no awaiting item")

    status, result = ctx.act("EXECAWAIT-%s-%s" % (action_part(opid), p["receipt_sha256"][:12]), "execute_awaiting",
                             {"operation_id": opid, "receipt_sha256": p["receipt_sha256"]}, {"slug": slug}, effect, observer)
    return _from_act("EXECUTE", job["item"], status, result, "awaiting item %s raised for the %s receipt" % (slug, status_word))


def _finish_execute(ctx, job):
    run, digest = _run(ctx), job.get("digest")
    for _, doc in all_prepared(run):
        if doc["request_sha256"] != digest:
            continue
        opid = doc["request"]["operation_id"]
        for d in SUBMITTED_DIRS:
            have = read_json(run / "ops" / d / (opid + ".json"))
            if isinstance(have, dict) and request_digest(have) == digest:
                return _result("done", "request %s is in %s/" % (opid, d))
        return _result("interrupted", "request %s is not in requests/, inflight/ or done/" % opid)
    directory = run / "ops" / "receipts"
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        names = []
    for name in names:
        if name.endswith(".json") and file_sha(directory / name) == digest:
            slug = _exec_slug(name[:-len(".json")], digest)
            return (_result("done", "awaiting item %s exists" % slug) if _awaiting_recorded(run, slug)
                    else _result("interrupted", "awaiting item %s was not raised" % slug))
    return _result("interrupted", "no prepared request or receipt carries the job's digest")


# ───────────────────────────────────────── POST-READBACK ─────────────────────────────────────────

def _latest_actor(events):
    review = _latest_review(events)
    actor = review.get("actor") if review else None
    return actor if isinstance(actor, str) and actor else None


def _a_evidence(item_id, merge_commit, receipt_path, receipt):
    return sha_canonical({"item": item_id, "merge_commit": merge_commit, "operation_id": receipt.get("operation_id"),
                          "receipt_sha256": file_sha(receipt_path)})


def _wait_evidence(item_id, merge_commit):
    return sha_canonical({"item": item_id, "merge_commit": merge_commit, "readback_receipt": None})


def _b_evidence(run, prepared, receipt_sha):
    opid = prepared["request"]["operation_id"]
    return sha_canonical({"item": prepared["item"], "operation_id": opid, "receipt_sha256": receipt_sha,
                          "request_sha256": prepared["request_sha256"],
                          "quiescence_sha256": file_sha(run / "ops" / "acceptance" / (opid + ".quiescence.json"))})


def _b_receipt(run, prepared):
    """(path, receipt sha) of the prepared operation's receipt when it is COMPLETED, measured and of this very request."""
    req = prepared["request"]
    path = _receipt_path(run, req["operation_id"])
    doc = read_json(path)
    if (_measured_receipt(path, doc) and doc.get("request_sha256") == prepared["request_sha256"]
            and doc.get("item_id") == prepared["item"] and doc.get("operation_id") == req["operation_id"]):
        return path, file_sha(path)
    return None


def _handled_path(run, name):
    return run / "handled" / name


def _wait_marked(path, item_id, merge_commit):
    """The readback-wait marker of this item at this merge commit, read back (not merely present)."""
    have = read_json(path)
    return _marker(path, kind="readback_wait", item=item_id, merge_commit=merge_commit) is True


def _c_post_readback(ctx, unknown=None):
    run, out = _run(ctx), []
    for item in _items(ctx, unknown) or []:                                   # (a) a deployed data-writing code item
        if item["model"].get("completion_kind") != "code" or not _writes_data(item["model"]):
            continue
        pr = ctx.pr(item["id"])
        if pr is not None and not (isinstance(pr, dict) and "state" in pr and "merge_commit" in pr):
            _say(unknown, "the pull request of %s could not be read" % item["id"])
            continue
        if pr is None or str(pr.get("state", "")).upper() != "MERGED" or not HEX40.match(str(pr.get("merge_commit", ""))):
            continue
        merge = pr["merge_commit"]
        events = _events(ctx, item["id"])
        if events is None:
            _say(unknown, "the events of %s could not be read" % item["id"])
            continue
        if _has_verdict(events, "post_deploy", head=merge):
            continue
        receipts = _readback_receipts(run, item["id"])
        if not receipts:
            fp = _wait_evidence(item["id"], merge)
            marker = _handled_path(run, "readback.%s.%s.json" % (action_part(item["id"]), fp[:12]))
            if _wait_marked(marker, item["id"], merge):
                continue                                 # a marker that is not that record marks nothing: the line is owed again
            out.append((_intent(ctx, "POST-READBACK", item["id"], stream="V", runner="script", head=merge,
                                verdict_phase="post_deploy", evidence_fp=fp),
                        {"variant": "wait", "item": item, "merge_commit": merge}))
            continue
        path, doc = receipts[0]
        out.append((_intent(ctx, "POST-READBACK", item["id"], stream="V", runner="model", pool="verifier", tier="opus", head=merge,
                            verdict_phase="post_deploy", evidence_fp=_a_evidence(item["id"], merge, path, doc),
                            card=_card(ctx, "verifier"), packet=_packet_path(ctx, item["id"]),
                            not_slot=_actor_slot(_latest_actor(events)), effort="high"),
                    {"variant": "a", "item": item, "merge_commit": merge, "events": events}))
    for _, prepared in all_prepared(run, unknown):                             # (b) a receipted operation
        found = _b_receipt(run, prepared)
        if found is None:
            rpath = _receipt_path(run, prepared["request"]["operation_id"])
            receipt = read_json(rpath)
            if (isinstance(receipt, dict) and receipt.get("status") == "COMPLETED"
                    and receipt.get("request_sha256") == prepared["request_sha256"]):
                _say(unknown, "the COMPLETED receipt %s carries no measured readback (exit 0 and an output of its digest, for this item)" % rpath)
            continue
        path, rsha = found
        events = _events(ctx, prepared["item"])
        if events is None:
            _say(unknown, "the events of %s could not be read" % prepared["item"])
            continue
        if _has_verdict(events, "artifact", digest=rsha):
            continue
        out.append((_intent(ctx, "POST-READBACK", prepared["item"], stream="V", runner="model", pool="verifier", tier="opus", digest=rsha,
                            verdict_phase="artifact", evidence_fp=_b_evidence(run, prepared, rsha), card=_card(ctx, "verifier"),
                            packet=_packet_path(ctx, prepared["item"]), effort="high"),
                    {"variant": "b", "prepared": prepared, "receipt_path": path, "receipt_sha256": rsha}))
    return out


def _start_post_readback(ctx, job):
    found = _find(ctx, "POST-READBACK", job)
    if found is None:
        return _result("refused", "the merge commit, the receipt or the verdict state changed since the intent")
    _, p = found
    run = _run(ctx)
    if p["variant"] == "wait":
        fp = job["evidence_fp"]
        path = _handled_path(run, "readback.%s.%s.json" % (action_part(job["item"]), fp[:12]))
        record = {"schema": HANDLED_SCHEMA, "kind": "readback_wait", "item": job["item"], "merge_commit": p["merge_commit"]}

        def effect():                       # the journal line first: the marker is what says it was written
            ctx.journal("post_readback_waiting", "%s is merged at %s and owes a post_deploy readback, but no COMPLETED measured readback "
                        "receipt of the item exists; none has been requested" % (job["item"], p["merge_commit"]))
            write_json(path, record)
            return {"path": str(path)}

        def observer(rec):
            return ("done", {"path": str(path)}) if _wait_marked(path, job["item"], p["merge_commit"]) else ("not_done", "no marker")

        status, result = ctx.act("READBACK-WAIT-%s-%s" % (action_part(job["item"]), fp[:12]), "readback_wait",
                                 {"item": job["item"], "merge_commit": p["merge_commit"]}, {"path": str(path)}, effect, observer)
        return _from_act("POST-READBACK", job["item"], status, result, "journalled that %s awaits a readback receipt" % job["item"])
    if not job.get("worktree"):
        return _result("refused", "the job has no worktree to snapshot")
    rc, _, err = ctx.sh(["python3", "-B", str(_fleet(ctx) / "kyverdicts.py"), "snapshot", "--worktree", str(job["worktree"]),
                         "--out", str(pathlib.Path(str(job["job_scratch"])) / "snapshot.json")], timeout=300)
    if rc != 0:
        return _result("refused", "kyverdicts.py snapshot exited %r" % (rc,))
    return None


def _proposed_verdict(job):
    """The job's own report, read from its result file: a dict, or the reason it carries no semantic verdict."""
    result = read_json(job.get("result_path") or "")
    if not isinstance(result, dict) or result.get("status") != "done":
        return None, "the job's result is not a done ky.job_result/1"
    proposed = result.get("proposed_verdict")
    if not isinstance(proposed, dict) or proposed.get("verdict") not in VERDICT_VALUES:
        return None, "the job proposed no ACCEPTED / REJECTED verdict"
    if proposed.get("head") is not None and proposed.get("head") != job.get("head"):
        return None, "the proposed verdict names another head"
    return proposed, None


def _publish(ctx, job, phase_args, author):
    boundary = _boundary(ctx, job)
    if boundary is not None:
        return boundary
    scratch = pathlib.Path(str(job["job_scratch"]))
    argv = (["python3", "-B", str(_fleet(ctx) / "kyverdicts.py"), "publish", "--job-id", str(job["job_id"]), "--item", job["item"]]
            + phase_args + ["--vslot", job["slot"], "--author-id", author, "--reviewer-id", "stream-V:" + job["slot"],
                            "--worktree", str(job["worktree"]), "--snapshot", str(scratch / "snapshot.json"),
                            "--job-exit", str(job["exit_code"]), "--result", str(job["result_path"]),
                            "--boundary", str(scratch / "boundary.check.json"), "--as", str(job["controller_id"])])
    rc, out, err = ctx.sh(argv, timeout=300)
    try:
        said = json.loads(out)
    except (ValueError, TypeError):
        said = None
    said = said if isinstance(said, dict) else {}
    why = said.get("reasons") or (err or out or "")[-200:]
    if rc == 0 and said.get("published") is True:
        return _result("done", "kyverdicts.py published %s (%s)" % (said.get("result"), said.get("action_id")))
    if rc == 1 or (rc == 0 and said.get("published") is False):
        return _fail("POST-READBACK", job["item"], "publication_refused", "kyverdicts.py publish exited %r: %s" % (rc, why))
    return _result("interrupted", "kyverdicts.py publish exited %r with no published answer (unknown; nothing proceeds): %s" % (rc, why))


def _finish_post_readback(ctx, job):
    item, run = job.get("item"), _run(ctx)
    if job.get("exit_code") != 0 or isinstance(job.get("exit_code"), bool):
        return _fail("POST-READBACK", item, "job_exit_nonzero", "exit %r" % (job.get("exit_code"),))
    if job.get("slot") not in V_SLOTS:
        return _fail("POST-READBACK", item, "slot_unknown", "the reviewing slot is %r" % (job.get("slot"),))
    if not job.get("worktree") or not job.get("controller_id"):
        return _fail("POST-READBACK", item, "job_identity_unknown", "worktree or controller id missing")
    if job.get("verdict_phase") == "post_deploy":
        head = job.get("head")
        pr = ctx.pr(item)
        if not isinstance(pr, dict) or "state" not in pr or "merge_commit" not in pr:
            return _result("interrupted", "the pull request of %s could not be read" % item)
        if not HEX40.match(str(head or "")) or str(pr.get("state", "")).upper() != "MERGED" or pr.get("merge_commit") != head:
            return _fail("POST-READBACK", item, "not_the_merge_commit", "the job's head is not the squash merge commit of the PR")
        events = _events(ctx, item)
        receipts = _readback_receipts(run, item)
        if events is None:
            return _result("interrupted", "the events of %s could not be read" % item)
        if not receipts or _a_evidence(item, head, receipts[0][0], receipts[0][1]) != job.get("evidence_fp"):
            return _fail("POST-READBACK", item, "evidence_changed", "the readback receipt is not the one the job reviewed")
        author = _latest_actor(events)
        phase_args = ["--phase", "post_deploy", "--head", head]
    elif job.get("verdict_phase") == "artifact":
        digest = job.get("digest")
        prepared, receipt_path = None, None
        for _, doc in all_prepared(run):
            if doc["item"] != item:
                continue
            found = _b_receipt(run, doc)
            if found is not None and found[1] == digest:
                prepared, receipt_path = doc, found[0]
                break
        if prepared is None:
            return _fail("POST-READBACK", item, "receipt_digest_mismatch", "no COMPLETED measured receipt of the item has the job's digest")
        if _b_evidence(run, prepared, digest) != job.get("evidence_fp"):
            return _fail("POST-READBACK", item, "evidence_changed", "the receipt's quiescence evidence changed during the job")
        if prepared.get("prepared_by_slot"):
            author = "stream-N:%s" % prepared["prepared_by_slot"]
        elif prepared.get("prepared_by"):
            author = "controller:%s" % prepared["prepared_by"]
        else:
            author = None
        phase_args = ["--phase", "artifact", "--artifact-digest", digest, "--artifact-path", str(receipt_path)]
    else:
        return _fail("POST-READBACK", item, "unknown_phase", "verdict_phase %r" % (job.get("verdict_phase"),))
    if not author:
        return _fail("POST-READBACK", item, "author_unknown", "independence cannot be shown without the author's identity")
    proposed, why = _proposed_verdict(job)
    if proposed is None:
        return _fail("POST-READBACK", item, "no_semantic_verdict", why)
    return _publish(ctx, job, phase_args, author)


# ───────────────────────────────────────── MODEL ─────────────────────────────────────────

def _executable(model_item):
    return model_item.get("done_by") not in ("decision", "join") and model_item.get("join") is not True


def _c_model(ctx, unknown=None):
    out = []
    for item in _items(ctx, unknown) or []:
        if item["owner"] != "S" or item["status"] != "ready" or not _executable(item["model"]) or item["id"] in MODEL_EXCLUDED:
            continue
        events = _events(ctx, item["id"])
        if events is None:
            _say(unknown, "the events of %s could not be read" % item["id"])
            continue
        digest = sha_canonical(item["model"])
        fp = sha_canonical({"item_sha": digest, "event_count": len(events)})
        out.append((_intent(ctx, "MODEL", item["id"], stream="S", runner="model", pool="builder", tier="opus", digest=digest,
                            evidence_fp=fp, locks=["item." + item["id"]], card=_card(ctx, "adhikarin"), effort="xhigh"), {"item": item}))
    return out


def _after_launch(ctx, job):
    """The item's events that came after the job's launch, recovered from the event count its evidence_fp was built on;
    None when that count cannot be recovered (the events shrank or changed shape) — unknown, never a guess."""
    events = _events(ctx, job.get("item"))
    if events is None:
        return None
    for n in range(len(events) + 1):
        if sha_canonical({"item_sha": job.get("digest"), "event_count": n}) == job.get("evidence_fp"):
            return events[n:]
    return None


def _finish_model(ctx, job):
    later = _after_launch(ctx, job)
    if later is None:
        return _result("interrupted", "the events of the item could not be matched to the launch")
    if any(_is_review(e) for e in later):
        return _result("done", "the job registered a review")
    if any(_is_block(e) for e in later):
        return _result("blocked", "the job blocked the item")
    return _result("interrupted", "the job ended with neither a review nor a block event")


# ───────────────────────────────────────── RULING ─────────────────────────────────────────

def _inbox(ctx):
    """Unacked N messages: a list, or None when the inbox could not be read. Exit 1 is "none" only with the
    empty JSON list `ky inbox --json` prints then; an exit 1 with any other stdout (a traceback) is unreadable."""
    rc, out, _ = ctx.ky("inbox", "--stream", "N", "--json", stream="N")
    if rc not in (0, 1):
        return None
    try:
        rows = json.loads(out)
    except (ValueError, TypeError):
        return None
    if rc == 1:
        return [] if rows == [] else None
    if not isinstance(rows, list) or any(not isinstance(r, dict) or not isinstance(r.get("msg_id"), str)
                                         or not MESSAGE_ID.match(r["msg_id"]) for r in rows):
        return None                                      # a row that is no message event (cli.py _unacked): not an inbox
    return rows


def _c_ruling(ctx, unknown=None):
    rows = _inbox(ctx)
    if rows is None:
        _say(unknown, "the N inbox (`ky inbox --stream N --json`) could not be read")
        return []
    run, out, seen = _run(ctx), [], set()
    for msg in rows:
        mid = msg["msg_id"]
        if mid in seen:
            continue
        seen.add(mid)
        if _marker(_handled_path(run, "msg.%s.json" % mid), kind="msg", msg_id=mid) is True:
            continue                                     # read back, not merely present: a truncated marker handles nothing
        digest = sha_canonical(msg)
        fp = sha_canonical({"msg_id": mid, "digest": digest})
        out.append((_intent(ctx, "RULING", "msg." + mid, stream="N", runner="model", pool="builder", tier="opus", digest=digest,
                            evidence_fp=fp, locks=["msg." + mid], card=_card(ctx, "adhikarin"), effort="high"), {"msg": msg}))
    return out


def _finish_ruling(ctx, job):
    mid = str(job.get("item", ""))[len("msg."):]
    rows = _inbox(ctx)
    if rows is None:
        return _result("interrupted", "the inbox could not be read")
    if any(r.get("msg_id") == mid for r in rows):
        return _result("interrupted", "message %s is still unacked" % mid)
    path = _handled_path(_run(ctx), "msg.%s.json" % mid)
    record = {"schema": HANDLED_SCHEMA, "kind": "msg", "msg_id": mid, "job_id": job.get("job_id"), "digest": job.get("digest")}

    def effect():
        write_json(path, record)
        return {"path": str(path)}

    def observer(rec):
        return ("done", {"path": str(path)}) if _marker(path, kind="msg", msg_id=mid) is True else ("not_done", "no handled record")

    status, result = ctx.act("HANDLED-msg-%s-%s" % (action_part(mid), str(job.get("digest"))[:12]), "handled",
                             {"msg_id": mid}, {"path": str(path)}, effect, observer)
    return _from_act("RULING", job.get("item"), status, result, "message %s acked and recorded as handled" % mid)


# ───────────────────────────────────────── SURROGATE ─────────────────────────────────────────

def awaiting_fingerprint(ctx, doc):
    """sha256 of the canonical {id, item, question, options, evidence, each evidence file's sha256} (I)."""
    evidence = doc.get("evidence") if isinstance(doc.get("evidence"), list) else []
    shas = []
    for e in evidence:
        p = pathlib.Path(str(e))
        shas.append(file_sha(p if p.is_absolute() else _repo(ctx) / p))
    return sha_canonical({"id": doc.get("id"), "item": doc.get("item"), "question": doc.get("question"), "options": doc.get("options"),
                          "evidence": evidence, "evidence_sha256": shas})


def _veto_rows(ctx):
    """kyveto.status() decisions by id, or None when the status cannot be read."""
    fn = getattr(ctx, "veto_status", None)
    status = None
    try:
        if callable(fn):
            status = fn()
        else:
            import kyveto                                              # the engine normally supplies veto_status
            env = kyveto.Env({"KY_ROOT": str(ctx.root), "KY_RUN": str(ctx.run), "KY_FLEET": str(ctx.fleet),
                              "KY_SOURCE_REPO": str(ctx.repo), "PATH": "/usr/bin:/bin"})
            status = kyveto.status(env)
    except Exception:
        return None
    rows = status.get("decisions") if isinstance(status, dict) else None
    return {r["id"]: r for r in rows if isinstance(r, dict) and "id" in r} if isinstance(rows, list) else None


def _awaiting_docs(ctx, unknown=None):
    directory, out = _run(ctx) / "awaiting", []
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return out
    except OSError:
        _say(unknown, "the awaiting items under %s could not be listed" % directory)
        return out
    for name in names:
        if not name.endswith(".json") or name.endswith(OWNER_DECISION_SUFFIX):
            continue
        doc = read_json(directory / name)
        if isinstance(doc, dict) and doc.get("id") == name[:-len(".json")] and AWAITING_ID.match(str(doc["id"])):
            out.append(doc)
        else:
            _say(unknown, "the awaiting file %s is not an awaiting item of that id" % (directory / name))
    return out


def _owner_answered(run, aid):
    """kyloop.open_awaiting's test: the owner has answered the item when <id>.owner_decision.json sits beside it."""
    return (run / "awaiting" / (aid + OWNER_DECISION_SUFFIX)).exists()


def move_refusal(aid, handled, row):
    """Why awaiting item `aid` may not move to awaiting/done/ on this kyveto.status() row, or None (I-14). The log is
    model-written, so a row's state counts only with a record behind it that no model line can stand in for."""
    if not isinstance(handled, dict) or not isinstance(row, dict):
        return "no handled record or no decision row"
    if handled.get("class") != "veto" or row.get("class") != "veto":
        return "not a veto-class decision (a hard_stop is the owner's to resolve)"
    if row.get("id") != handled.get("decision_id") or row.get("awaiting") != aid:
        return "the decision row is not this awaiting item's"
    if row.get("hard_stop") or row.get("anomaly") or row.get("anomalies") or row.get("refused") or row.get("unresolved"):
        return "the row carries a hard_stop, anomaly or refusal flag"
    state = row.get("state")
    if state not in MOVE_STATES or row.get("latest_line_state") != state:
        return "state %r is not a terminal state with a record behind it" % (state,)
    if state == "EXECUTED" and row.get("executed_by_handler") is not True:
        return "EXECUTED without the handler's DONE execution record"
    if state == "VETOED" and not (isinstance(row.get("veto_command"), str) and row["veto_command"]):
        return "VETOED without the owner's veto command"
    return None


def _move_digest(aid, decision_id, state):
    return sha_canonical({"move": aid, "decision_id": decision_id, "state": state})


def _c_surrogate(ctx, unknown=None):
    run, out, rows = _run(ctx), [], False
    for doc in _awaiting_docs(ctx, unknown):
        aid, fp = doc["id"], awaiting_fingerprint(ctx, doc)
        handled = read_json(_handled_path(run, "awaiting.%s.json" % aid))
        if isinstance(handled, dict) and handled.get("fingerprint") == fp:
            if rows is False:
                rows = _veto_rows(ctx)
                if rows is None:
                    _say(unknown, "kyveto.status() could not be read")
            row = rows.get(handled.get("decision_id")) if rows else None
            if rows is not None and row is None:
                _say(unknown, "kyveto.status() shows no decision %r, the one recorded for %s" % (handled.get("decision_id"), aid))
            if move_refusal(aid, handled, row) is None:
                digest = _move_digest(aid, handled["decision_id"], row["state"])
                move_fp = sha_canonical({"fingerprint": fp, "decision_id": handled["decision_id"], "state": row["state"]})
                out.append((_intent(ctx, "SURROGATE", aid, stream="steward", runner="script", digest=digest, evidence_fp=move_fp,
                                    locks=["awaiting." + aid]), {"variant": "move", "doc": doc}))
            continue                                                    # handled at this fingerprint: no further job
        if _owner_answered(run, aid):
            continue                                                    # resolved by the owner: not the surrogate's
        out.append((_intent(ctx, "SURROGATE", aid, stream="steward", runner="model", pool="builder", tier="opus", digest=fp,
                            evidence_fp=fp, locks=["awaiting." + aid], card=_card(ctx, "surrogate"), effort="high"),
                    {"variant": "decide", "doc": doc}))
    return out


def _start_surrogate(ctx, job):
    run, aid = _run(ctx), job.get("item")
    doc = read_json(run / "awaiting" / ("%s.json" % aid))
    if not isinstance(doc, dict):
        return _result("refused", "awaiting item %s is gone" % aid)
    fp = awaiting_fingerprint(ctx, doc)
    if job.get("digest") == fp:                                         # a decide job: the handled state is read again under the lock
        handled = read_json(_handled_path(run, "awaiting.%s.json" % aid))
        if isinstance(handled, dict) and handled.get("fingerprint") == fp:
            return _result("done", "awaiting item %s is already handled at this fingerprint" % aid)
        if _owner_answered(run, aid):
            return _result("refused", "the owner has answered awaiting item %s" % aid)
        return None
    found = _find(ctx, "SURROGATE", job)
    if found is None or found[1]["variant"] != "move":
        return _result("refused", "the awaiting item's evidence or its decision state changed since the intent")
    handled = read_json(_handled_path(run, "awaiting.%s.json" % aid))        # the move conditions, again, under the lock
    rows = _veto_rows(ctx)
    row = rows.get(handled.get("decision_id")) if rows and isinstance(handled, dict) else None
    refusal = move_refusal(aid, handled, row)
    if refusal is not None or _move_digest(aid, handled.get("decision_id"), row.get("state")) != job.get("digest"):
        return _result("refused", "awaiting item %s may not be moved: %s" % (aid, refusal or "the decision state changed"))
    src, dst = run / "awaiting" / ("%s.json" % aid), run / "awaiting" / "done" / ("%s.json" % aid)

    def effect():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise FileExistsError(str(dst))
        os.replace(src, dst)
        return {"moved_to": str(dst)}

    def observer(rec):
        if dst.exists() and not src.exists():
            return "done", {"moved_to": str(dst)}
        return ("not_done", "not moved") if src.exists() and not dst.exists() else ("unknown", "both or neither exist")

    status, result = ctx.act("AWDONE-%s-%s" % (action_part(aid), job["digest"][:12]), "awaiting_done",
                             {"awaiting": aid, "digest": job["digest"]}, {"from": str(src), "to": str(dst)}, effect, observer)
    return _from_act("SURROGATE", aid, status, result, "awaiting item %s moved to awaiting/done/" % aid)


def _decision_line(run, aid, session):
    """The job's own line of DECISIONS_SURROGATE.jsonl: the latest valid line for the awaiting item by its session."""
    if not session:
        return None
    try:
        text = (run / "DECISIONS_SURROGATE.jsonl").read_text(encoding="utf-8")
    except OSError:
        return None
    found = None
    for raw in text.splitlines():
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        if (isinstance(line, dict) and line.get("awaiting") == aid and line.get("session") == session
                and line.get("class") in DECISION_CLASSES and line.get("state") in DECISION_STATES and isinstance(line.get("id"), str)):
            found = line
    return found


def _is_move_job(run, aid, job):
    """True for the script job that moves the item: its digest is a move digest of the handled decision."""
    handled = read_json(_handled_path(run, "awaiting.%s.json" % aid))
    did = handled.get("decision_id") if isinstance(handled, dict) else None
    return isinstance(did, str) and job.get("digest") in [_move_digest(aid, did, s) for s in MOVE_STATES]


def _finish_surrogate(ctx, job):
    run, aid = _run(ctx), job.get("item")
    if _is_move_job(run, aid, job):
        if (run / "awaiting" / "done" / ("%s.json" % aid)).exists() and not (run / "awaiting" / ("%s.json" % aid)).exists():
            return _result("done", "awaiting item %s is in awaiting/done/" % aid)
        return _result("interrupted", "awaiting item %s has not been moved to awaiting/done/" % aid)
    line = _decision_line(run, aid, job.get("provider_session_id"))
    if line is not None:
        path = _handled_path(run, "awaiting.%s.json" % aid)
        record = {"schema": HANDLED_SCHEMA, "kind": "awaiting", "awaiting": aid, "fingerprint": job.get("digest"), "decision_id": line["id"],
                  "class": line["class"], "state": line["state"], "job_id": job.get("job_id"), "session": job.get("provider_session_id")}

        def effect():
            write_json(path, record)
            return {"path": str(path)}

        def observer(rec):
            have = read_json(path)
            if isinstance(have, dict) and have.get("fingerprint") == record["fingerprint"] and have.get("decision_id") == record["decision_id"]:
                return "done", {"path": str(path)}
            return "not_done", "no handled record at this fingerprint"

        status, result = ctx.act("HANDLED-awaiting-%s-%s" % (action_part(aid), str(job.get("digest"))[:12]), "handled",
                                 {"awaiting": aid, "fingerprint": job.get("digest"), "decision_id": line["id"]}, {"path": str(path)}, effect, observer)
        if status == "done" and line["class"] == "hard_stop":
            ctx.journal("hard stop", "owner-only decision %s on awaiting item %s: no delegated approval is published; the item stays unresolved"
                        % (line["id"], aid))
        return _from_act("SURROGATE", aid, status, result, "decision %s (%s, %s) recorded for %s" % (line["id"], line["class"], line["state"], aid))
    return _result("interrupted", "the job's session wrote no decision line for %s (wherever the item now is)" % aid)


# ───────────────────────────────────────── PLAN ─────────────────────────────────────────

def _packets_sha(ctx):
    """The packet set's digest; an absent directory is the empty set, an unreadable directory or packet is None."""
    directory = _repo(ctx) / PACKETS_REL
    try:
        names = sorted(n for n in os.listdir(directory) if n.startswith("PACKET_") and n.endswith(".md"))
    except FileNotFoundError:
        names = []
    except OSError:
        return None
    shas = [[n, file_sha(directory / n)] for n in names]
    return None if any(s is None for _, s in shas) else sha_canonical(shas)


def _admitted(run, item_id):
    """kyd_admit's `$KY_RUN/admission/<item>.json` {item, base_sha, test_digests, result}, read back: True when it is
    that item's record, False when there is none, None when a file is there that is not it."""
    path = run / "admission" / ("%s.json" % item_id)
    if not os.path.lexists(str(path)):
        return False
    doc = read_json(path)
    return True if isinstance(doc, dict) and doc.get("item") == item_id and isinstance(doc.get("result"), str) else None


def _c_plan(ctx, unknown=None):
    run = _run(ctx)
    try:
        text = (run / "REPACKET.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    except (OSError, ValueError):
        _say(unknown, "%s could not be read" % (run / "REPACKET.txt"))
        return []                                                       # unreadable is unknown, not empty
    packets = _packets_sha(ctx)
    if packets is None:
        _say(unknown, "the packet set under %s could not be read" % (_repo(ctx) / PACKETS_REL))
        return []
    if text.strip():
        trigger, item, digest = "repacket", "REPACKET", sha_text(text)
    else:
        items = _items(ctx, unknown)
        if items is None:
            return []                                                   # an unknown tracker is no wave boundary
        items = [i for i in items if _executable(i["model"])]
        in_flight = [i for i in items if i["status"] in ("ready", "review")]
        admitted = [_admitted(run, i["id"]) for i in items if i["status"] == "running"]
        if None in admitted and not in_flight:
            _say(unknown, "an admission record under %s is not its item's record" % (run / "admission"))
        if not items or in_flight or any(a is not False for a in admitted):
            return []
        trigger, item, digest = "boundary", "WAVE-BOUNDARY", sha_canonical(sorted(i["id"] for i in items))
    if _marker(_handled_path(run, "plan.%s.json" % digest[:12]), kind="plan", digest=digest) is True:
        return []                                                       # read back, not merely present
    fp = sha_canonical({"trigger": trigger, "digest": digest, "packets_sha256": packets})
    return [(_intent(ctx, "PLAN", item, stream="S", runner="model", pool="builder", tier="opus", digest=digest, evidence_fp=fp,
                     locks=["plan"], card=_card(ctx, "adhikarin"), effort="xhigh"), {"trigger": trigger})]


def _finish_plan(ctx, job):
    if job.get("exit_code") != 0:
        return _fail("PLAN", job.get("item"), "job_exit_nonzero", "exit %r" % (job.get("exit_code"),))
    result = read_json(job.get("result_path") or "")
    if not isinstance(result, dict) or result.get("status") not in ("done", "blocked", "failed"):
        return _result("interrupted", "the job left no ky.job_result/1")
    if result["status"] == "blocked":
        return _result("blocked", str(result.get("blocked_reason") or "the job blocked"))
    if result["status"] == "failed":
        return _fail("PLAN", job.get("item"), "job_reported_failure", str(result.get("notes") or ""))
    trigger = "repacket" if job.get("item") == "REPACKET" else "boundary"
    packets = _packets_sha(ctx)
    if packets is None:
        return _result("interrupted", "the packet set could not be read: whether it changed is unknown")
    if sha_canonical({"trigger": trigger, "digest": job.get("digest"), "packets_sha256": packets}) == job.get("evidence_fp"):
        return _result("interrupted", "the packet set is unchanged: nothing was repacketed")
    path = _handled_path(_run(ctx), "plan.%s.json" % str(job.get("digest"))[:12])
    record = {"schema": HANDLED_SCHEMA, "kind": "plan", "trigger": trigger, "digest": job.get("digest"), "job_id": job.get("job_id")}

    def effect():
        write_json(path, record)
        return {"path": str(path)}

    def observer(rec):
        return (("done", {"path": str(path)}) if _marker(path, kind="plan", digest=job.get("digest")) is True
                else ("not_done", "no handled record"))

    status, res = ctx.act("HANDLED-plan-%s" % str(job.get("digest"))[:12], "handled", {"trigger": trigger, "digest": job.get("digest")},
                          {"path": str(path)}, effect, observer)
    return _from_act("PLAN", job.get("item"), status, res, "the packet set changed; the %s trigger is recorded as handled" % trigger)


# ───────────────────────────────────────── the engine's three calls ─────────────────────────────────────────

CANDIDATES = {"REQUEST-PREP": _c_request_prep, "PRE-ACCEPT": _c_pre_accept, "EXECUTE": _c_execute, "POST-READBACK": _c_post_readback,
              "MODEL": _c_model, "RULING": _c_ruling, "SURROGATE": _c_surrogate, "PLAN": _c_plan}
START = {"REQUEST-PREP": _start_request_prep, "PRE-ACCEPT": _start_pre_accept, "EXECUTE": _start_execute,
         "POST-READBACK": _start_post_readback, "SURROGATE": _start_surrogate}
FINISH = {"REQUEST-PREP": _finish_request_prep, "PRE-ACCEPT": _finish_pre_accept, "EXECUTE": _finish_execute,
          "POST-READBACK": _finish_post_readback, "MODEL": _finish_model, "RULING": _finish_ruling,
          "SURROGATE": _finish_surrogate, "PLAN": _finish_plan}


def intents(ctx):
    """Every job owed now, in kind order (I-13). Read-only: it reads files, the table, the inbox and the tracker;
    what it could not read or recognise goes into one journal line (I-15)."""
    out, seen, unknown = [], set(), []
    for kind in ORDER:
        for intent, _ in CANDIDATES[kind](ctx, unknown):
            if intent["key"] not in seen:
                seen.add(intent["key"])
                out.append(intent)
    if unknown:                                                         # I-15: unknown is said, never read as nothing owed
        try:
            ctx.journal(UNKNOWN_EVENT, "no job is derived this tick from what could not be read, recognised or used: " + "; ".join(unknown))
        except Exception:
            pass                                                        # the intents that are known still stand
    return out


def start(ctx, job):
    """None → launch the model job; a result → the job's work was script work, or the launch is refused / not needed."""
    if job.get("kind") not in KINDS:
        return _result("refused", "%r is not a kind of this module" % (job.get("kind"),))
    handler = START.get(job["kind"])
    return handler(ctx, job) if handler else (None if _find(ctx, job["kind"], job) is not None
                                              else _result("refused", "the evidence changed since the intent"))


def finish(ctx, job):
    """The result of a job whose process group is gone (or of a script job, to confirm it)."""
    if job.get("kind") not in KINDS:
        return _result("refused", "%r is not a kind of this module" % (job.get("kind"),))
    return FINISH[job["kind"]](ctx, job)
