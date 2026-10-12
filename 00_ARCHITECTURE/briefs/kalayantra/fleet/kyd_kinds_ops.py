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
launch); evidence that cannot be read is `interrupted`, never a guess. Nothing in this file starts executor.py, holds a
credential, dispatches a workflow or runs a tracker-state `ky` verb.

INTERPRETATIONS (the packet's "(I)" — what the plan leaves open, and what is done here):
  I-1  Items come from `ctx.next` (`ky next --json`): a list, or {"items": [...]}; each item {id, owner, status,
       ready, completion_kind, brief{op, migration}, detector, done_by, join}. Ready = `ready` true or status "ready".
  I-2  `brief.op` is {kind, args, kyd, requested_by?, operation_id?, idempotency_key?, chart_id?, lease_id?,
       reviewed_commit?, expires_at?, timeout_s?} or the bare name of a table kind. Prose and "NONE" are not an
       operation. operation_id defaults to OP-<item>; idempotency_key to the operation_id; requested_by to
       `adhikarin` (the N lane) when the entry admits it; chart_id to the canonical chart. A field that cannot be
       derived (kyd; for a production kind lease_id, reviewed_commit, expires_at) makes the job a model job.
       That job's request must carry every derived field unchanged and add nothing; it fills only the missing
       ones. An item with any valid prepared record, under any operation id, is prepared.
  I-3  A request is "accepted by executor.validate" if `static_validate` — its field, entry, requester, argument and
       production-field checks, kept equal to executor.py by a test that imports both — passes. What only the executor
       can know (lease liveness, ancestry of reviewed_commit, idempotency, capability) stays the executor's.
  I-4  The prepared request is `$KY_RUN/ops/prepared/<operation_id>.json` {schema ky.op_prepared/1, operation_id, item,
       request, request_sha256, prepared_by, prepared_by_slot}; request_sha256 is the executor's digest.
  I-5  Only a production kind needs a PRE-ACCEPT; a read-only kind goes straight from prepared to EXECUTE.
  I-6  EXECUTE submits `$KY_RUN/ops/requests/<operation_id>.json` and nothing else. A receipt of that request that is
       FAILED, REFUSED or INTERRUPTED raises one awaiting item (slug exec-<operation>-<12 hex of the receipt digest>)
       and never a second submission.
  I-7  POST-READBACK (a): a K-owned `code` item with data-writing metadata whose PR is MERGED with a merge commit, no
       verdict yet at (post_deploy, merge commit), and a COMPLETED, measured readback receipt of that item
       (kind readback_sql / migration_readback). None → one journal line, by a script intent, per merge commit.
       "Measured": status COMPLETED, exit_code 0, and an output file whose sha256 is the receipt's output_sha256 and
       that is not empty. Whether the deployment itself has landed is the tracker's guard at COMPLETE (deployment
       containment); this kind does not claim it.
       (b): a prepared operation whose executor receipt is COMPLETED and measured, for that request and item, with no
       artifact verdict at the receipt's sha256. The quiescence record, when present, is part of the evidence.
  I-8  A job's author identity: (a) the actor of the item's latest `review` event; (b) the preparer of the request
       (`stream-N:<slot>`, or `controller:<id>` for a script preparation). Unknown → nothing is published.
  I-9  Job keys: job_key(kind, item, head or digest, evidence_fp) = "<kind>.<item>.<12 hex of sha256 of the canonical
       JSON [head-or-digest, evidence_fp]>". Locks list the job lock first.
  I-10 Tracker events are dicts with a type (`type`, `event` or `kind`): review, block / blocked, verdict (phase, head,
       artifact_digest, result), and an actor. MODEL's and PLAN's "after the launch" is recovered from the job's own
       evidence_fp (the event count / packet set it was started on).
  I-11 PLAN's wave boundary: an open executable item exists and nothing is in flight — none ready, none in review,
       none running with an admission record (a `running` item without one is not admitted work).
  I-12 Cards: ADHIKARIN (N/S operators), PARIKSAKA (verifiers), OWNER_SURROGATE; Opus 5.5; effort xhigh for the PLAN
       class (REQUEST-PREP / MODEL / PLAN), high otherwise.
  I-13 Kind order within a tick: EXECUTE, PRE-ACCEPT, REQUEST-PREP, POST-READBACK, SURROGATE, RULING, MODEL, PLAN.
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
VETO_TERMINAL = ("EXECUTED", "VETOED", "FAILED")
RECEIPT_AWAITED = ("FAILED", "REFUSED", "INTERRUPTED")
CLOSED = ("done", "completed", "complete", "abandoned", "retired", "cancelled", "superseded")
VERDICT_VALUES = ("ACCEPTED", "REJECTED")
OPUS = "claude-opus-5-5"
CARDS = {"adhikarin": "ADHIKARIN.md", "verifier": "PARIKSAKA.md", "surrogate": "OWNER_SURROGATE.md"}
PREPARED_SCHEMA = "ky.op_prepared/1"
HANDLED_SCHEMA = "ky.handled/1"


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
    """executor.request_digest: sha256 of the request as sorted compact JSON without `acceptance_receipt`."""
    bound = {k: v for k, v in req.items() if k != "acceptance_receipt"}
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


def _brief(item):
    return item.get("brief") if isinstance(item.get("brief"), dict) else {}


def _writes_data(item):
    brief = _brief(item)
    return _truthy_meta(brief.get("migration")) or _truthy_meta(brief.get("op"))


def _is_ready(item):
    return item.get("ready") is True or item.get("status") == "ready"


def _is_closed(item):
    return str(item.get("status", "")).lower() in CLOSED


def _items(ctx):
    nxt = ctx.next() if callable(ctx.next) else ctx.next
    rows = nxt.get("items") if isinstance(nxt, dict) else nxt
    if not isinstance(rows, list):
        return []
    return sorted((r for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str)), key=lambda r: r["id"])


def _events(ctx, item_id):
    ev = ctx.events(item_id)
    return ev if isinstance(ev, list) and all(isinstance(e, dict) for e in ev) else None


def _etype(event):
    return str(event.get("type") or event.get("event") or event.get("kind") or "").lower()


def _has_verdict(events, phase, head=None, digest=None):
    for e in events:
        if _etype(e) != "verdict" or e.get("phase") != phase:
            continue
        if (head is not None and e.get("head") == head) or (digest is not None and e.get("artifact_digest") == digest):
            return True
    return False


def _latest_review(events):
    reviews = [e for e in events if _etype(e) == "review"]
    return reviews[-1] if reviews else None


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
    return {
        "kind": kind, "item": item, "key": key, "stream": stream, "role": kind.lower(), "pool": pool, "runner": runner,
        "queue": None, "claim": claim, "locks": all_locks, "tier": tier, "not_slot": not_slot, "head": head, "digest": digest,
        "verdict_phase": verdict_phase, "evidence_fp": evidence_fp, "card": card, "packet": packet,
        "header": {"model": OPUS if model else None, "effort": effort if model else None, "card_path": card,
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
    """executor.validate's attestation rule: (names of the checks that must be true, whether required_rows apply)."""
    required = []
    if kind != "backup_snapshot":
        required.append("backup_taken")
    if kind not in ("backup_snapshot", "backup_restore_verify"):
        required.append("restore_verified")
    mutating = kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun")
    if mutating:
        required.append("dry_run_passed")
    return required, mutating


def op_spec(item, table):
    op = _brief(item).get("op")
    if isinstance(op, str):
        op = {"kind": op} if op in table else None
    if not isinstance(op, dict) or not isinstance(op.get("kind"), str) or not op["kind"]:
        return None
    return op


def derive_request(item_id, op, entry):
    """(request, missing): the request as far as brief.op and the table determine it (I-2)."""
    operation_id = op.get("operation_id") or "OP-" + item_id
    requesters = entry.get("requesters", ["adhikarin"])
    req = {"operation_id": operation_id, "kind": op["kind"], "item_id": item_id,
           "idempotency_key": op.get("idempotency_key") or operation_id,
           "requested_by": op.get("requested_by") or ("adhikarin" if "adhikarin" in requesters else None),
           "kyd": op.get("kyd"), "args": dict(op.get("args") or {}) if isinstance(op.get("args") or {}, dict) else op.get("args")}
    if op.get("timeout_s") is not None:
        req["timeout_s"] = op["timeout_s"]
    missing = []
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


def request_unbound(request, item_id, op, entry):
    """A model-authored request may fill only the fields derive_request left missing; every field it fixes (and no
    other) must be there with its derived value. The first difference, or None."""
    derived, missing = derive_request(item_id, op, entry)
    extra = sorted(k for k in request if k not in derived)
    if extra:
        return "fields neither derived nor missing: %s" % extra
    for k in sorted(derived):
        if k not in missing and (k not in request or request[k] != derived[k]):
            return "%s differs from the value brief.op and the table fix" % k
    return None


# ───────────────────────────────────────── prepared / accepted / submitted state ─────────────────────────────────────────

def prepared_dir(run):
    return run / "ops" / "prepared"


def load_prepared(path):
    doc = read_json(path)
    if not isinstance(doc, dict) or doc.get("schema") != PREPARED_SCHEMA or not isinstance(doc.get("request"), dict):
        return None
    req = doc["request"]
    opid = req.get("operation_id")
    if (not isinstance(opid, str) or not SAFE_ID.match(opid) or pathlib.Path(path).stem != opid or doc.get("operation_id") != opid
            or doc.get("item") != req.get("item_id") or doc.get("request_sha256") != request_digest(req)):
        return None
    return doc


def all_prepared(run):
    try:
        names = sorted(os.listdir(prepared_dir(run)))
    except OSError:
        return []
    out = []
    for name in names:
        if name.endswith(".json"):
            doc = load_prepared(prepared_dir(run) / name)
            if doc is not None:
                out.append((prepared_dir(run) / name, doc))
    return out


def _acceptance_path(run, opid):
    return run / "ops" / "acceptance" / (opid + ".json")


def _receipt_path(run, opid):
    return run / "ops" / "receipts" / (opid + ".json")


def _submitted(run, opid):
    return any((run / "ops" / d / (opid + ".json")).exists() for d in ("requests", "done", "receipts"))


def acceptance_matches(acc, prepared):
    req = prepared["request"]
    return (isinstance(acc, dict) and acc.get("result") == "ACCEPTED" and acc.get("operation_id") == req["operation_id"]
            and acc.get("by") in V_SLOTS and acc.get("request_sha256") == prepared["request_sha256"]
            and acc.get("reviewed_commit") == req.get("reviewed_commit"))


def _awaiting_recorded(run, slug):
    for directory in (run / "awaiting", run / "awaiting" / "done"):
        try:
            if any(n.startswith("AW-") and n.endswith("-%s.json" % slug) for n in os.listdir(directory)):
                return True
        except OSError:
            pass
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

def _c_request_prep(ctx):
    table = read_table(ctx)
    if table is None:
        return []
    run, out = _run(ctx), []
    for item in _items(ctx):
        if item.get("owner") != "N" or not _is_ready(item) or item.get("completion_kind", "operation") != "operation":
            continue
        op = op_spec(item, table)
        entry = table.get(op["kind"]) if op else None
        if not entry_usable(entry):
            continue
        req, missing = derive_request(item["id"], op, entry)
        opid = req["operation_id"]
        if not SAFE_ID.match(str(opid)) or (prepared_dir(run) / (opid + ".json")).exists():
            continue
        if any(doc["item"] == item["id"] for _, doc in all_prepared(run)):
            continue                                     # a prepared request of the item, under any operation id
        if missing:
            digest = sha_canonical({"item": item["id"], "op": op, "entry": entry, "missing": missing})
            intent = _intent(ctx, "REQUEST-PREP", item["id"], stream="N", runner="model", pool="builder", tier="opus", digest=digest,
                             evidence_fp=digest, card=_card(ctx, "adhikarin"), effort="xhigh")
            out.append((intent, {"op": op, "entry": entry, "missing": missing}))
            continue
        if static_validate(req, entry) is not None:
            continue                                     # stated but refused by the executor's own rules: not ours to prepare
        digest = request_digest(req)
        fp = sha_canonical({"request_sha256": digest, "entry": entry})
        intent = _intent(ctx, "REQUEST-PREP", item["id"], stream="N", runner="script", digest=digest, evidence_fp=fp)
        out.append((intent, {"op": op, "entry": entry, "request": req}))
    return out


def _prepared_doc(job, request, slot):
    return {"schema": PREPARED_SCHEMA, "operation_id": request["operation_id"], "item": request["item_id"], "request": request,
            "request_sha256": request_digest(request), "prepared_by": job.get("controller_id"), "prepared_by_slot": slot}


def _write_prepared(ctx, job, request, slot, item):
    run = _run(ctx)
    path = prepared_dir(run) / (request["operation_id"] + ".json")
    doc = _prepared_doc(job, request, slot)

    def effect():
        write_once(path, doc)
        return {"path": str(path), "request_sha256": doc["request_sha256"]}

    def observer(record):
        have = read_json(path)
        if isinstance(have, dict) and have.get("request_sha256") == doc["request_sha256"]:
            return "done", {"path": str(path), "request_sha256": doc["request_sha256"]}
        return ("not_done", "absent") if not path.exists() else ("unknown", "another prepared record is in place")

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
    return _write_prepared(ctx, job, payload["request"], None, job["item"])


def _finish_request_prep(ctx, job):
    run = _run(ctx)
    for path, doc in all_prepared(run):
        if doc["item"] == job.get("item") and doc["request_sha256"] == job.get("digest"):
            return _result("done", "prepared record %s carries the request digest" % path)
    if job.get("exit_code") != 0:
        return _fail("REQUEST-PREP", job.get("item"), "job_exit_nonzero", "exit %r" % (job.get("exit_code"),))
    request = read_json(pathlib.Path(str(job.get("job_scratch"))) / "request.json")
    if not isinstance(request, dict):
        return _result("interrupted", "the job proposed no request.json")
    for path, doc in all_prepared(run):                                  # a repeated finish after the effect: read it back
        if doc["item"] == job.get("item") and doc["request_sha256"] == request_digest(request):
            return _result("done", "prepared record %s carries the proposed request's digest" % path)
    found = _find(ctx, "REQUEST-PREP", job)
    if found is None:
        return _fail("REQUEST-PREP", job.get("item"), "evidence_changed", "the operation or the table changed during the job")
    _, payload = found
    # No kyboundary check: a builder-pool job gets no prepared view, so `check` could only answer 3 (review r2 KO2-B1);
    # the packet names the boundary for PRE-ACCEPT and POST-READBACK. The binding checks and the digest read-back gate this.
    if request.get("item_id") != job["item"] or request.get("kind") != payload["op"]["kind"]:
        return _fail("REQUEST-PREP", job["item"], "request_for_another_operation", "item_id/kind do not match the item's operation")
    unbound = request_unbound(request, job["item"], payload["op"], payload["entry"])
    if unbound:
        return _fail("REQUEST-PREP", job["item"], "request_not_bound", unbound)
    reason = static_validate(request, payload["entry"])
    if reason:
        return _fail("REQUEST-PREP", job["item"], "request_invalid", reason)
    if (prepared_dir(run) / (request["operation_id"] + ".json")).exists():
        return _fail("REQUEST-PREP", job["item"], "already_prepared", request["operation_id"])
    return _write_prepared(ctx, job, request, job.get("slot"), job["item"])


def _boundary(ctx, job):
    """`kyboundary.sh check <job_id>`: None when intact, else the result that stops the finish."""
    rc, _, _ = ctx.sh(["bash", str(_fleet(ctx) / "kyboundary.sh"), "check", str(job["job_id"])], timeout=300)
    if rc == 0:
        return None
    if rc == 1:
        return _fail(job.get("kind"), job.get("item"), "boundary_not_intact", "kyboundary.sh check exited 1")
    return _result("interrupted", "the boundary could not be judged (kyboundary.sh check exited %r)" % (rc,))


# ───────────────────────────────────────── PRE-ACCEPT ─────────────────────────────────────────

def _c_pre_accept(ctx):
    table = read_table(ctx)
    if table is None:
        return []
    run, out = _run(ctx), []
    for _, doc in all_prepared(run):
        req = doc["request"]
        entry = table.get(req["kind"])
        if not isinstance(entry, dict) or not entry.get("production"):
            continue
        if _submitted(run, req["operation_id"]) or _acceptance_path(run, req["operation_id"]).exists():
            continue
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
    existing = read_json(_acceptance_path(run, req["operation_id"]))
    if isinstance(existing, dict) and existing.get("result") == "ACCEPTED" and existing.get("by") == slot \
            and existing.get("request_sha256") == prepared["request_sha256"]:
        return _result("done", "acceptance of %s by %s is already in place" % (req["operation_id"], slot))     # a repeated finish
    if _acceptance_path(run, req["operation_id"]).exists():
        return _fail("PRE-ACCEPT", item, "acceptance_exists", req["operation_id"])
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
    needed, mutating = required_checks(req["kind"])
    if any(checks.get(k) is not True for k in needed):
        return _fail("PRE-ACCEPT", item, "attestation_missing", "a required backup / restore / dry-run check is not true")
    if mutating and any(rows.get(k) is not True for k in entry.get("required_rows", [])):
        return _fail("PRE-ACCEPT", item, "rows_not_true", "a required row of the table entry is not true")
    record = {"result": "ACCEPTED", "operation_id": req["operation_id"], "by": slot, "reviewed_commit": req.get("reviewed_commit"),
              "ts": _now(ctx), "request_sha256": prepared["request_sha256"], "rows": rows, "checks": checks}
    path = _acceptance_path(run, req["operation_id"])

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


def _c_execute(ctx):
    table = read_table(ctx)
    if table is None:
        return []
    run, out = _run(ctx), []
    for ppath, doc in all_prepared(run):
        req, sha = doc["request"], doc["request_sha256"]
        opid = req["operation_id"]
        entry = table.get(req["kind"])
        if not isinstance(entry, dict):
            continue
        if not _submitted(run, opid):
            acc_path, acc_sha = _acceptance_path(run, opid), None
            if entry.get("production"):
                if not acceptance_matches(read_json(acc_path), doc):
                    continue
                acc_sha = file_sha(acc_path)
            fp = sha_canonical({"request_sha256": sha, "acceptance_sha256": acc_sha})
            out.append((_intent(ctx, "EXECUTE", doc["item"], stream="N", runner="script", digest=sha, evidence_fp=fp),
                        {"variant": "submit", "prepared": doc, "acceptance_path": acc_path, "production": bool(entry.get("production"))}))
            continue
        rpath = _receipt_path(run, opid)
        receipt = read_json(rpath)
        if not isinstance(receipt, dict) or receipt.get("request_sha256") != sha or receipt.get("status") not in RECEIPT_AWAITED:
            continue
        rsha = file_sha(rpath)
        if rsha is None or _awaiting_recorded(run, _exec_slug(opid, rsha)):
            continue
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
        for d in ("requests", "done"):
            have = read_json(run / "ops" / d / (opid + ".json"))
            if isinstance(have, dict) and request_digest(have) == digest:
                return _result("done", "request %s is in %s/" % (opid, d))
        return _result("interrupted", "request %s is not in requests/ or done/" % opid)
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


def _c_post_readback(ctx):
    run, out = _run(ctx), []
    for item in _items(ctx):                                                  # (a) a deployed data-writing code item
        if item.get("completion_kind") != "code" or not _writes_data(item) or _is_closed(item):
            continue
        pr = ctx.pr(item["id"])
        if not isinstance(pr, dict) or str(pr.get("state", "")).upper() != "MERGED" or not HEX40.match(str(pr.get("merge_commit", ""))):
            continue
        merge = pr["merge_commit"]
        events = _events(ctx, item["id"])
        if events is None or _has_verdict(events, "post_deploy", head=merge):
            continue
        review = _latest_review(events) or {}
        receipts = _readback_receipts(run, item["id"])
        if not receipts:
            fp = _wait_evidence(item["id"], merge)
            if _handled_path(run, "readback.%s.%s.json" % (action_part(item["id"]), fp[:12])).exists():
                continue
            out.append((_intent(ctx, "POST-READBACK", item["id"], stream="V", runner="script", head=merge,
                                verdict_phase="post_deploy", evidence_fp=fp),
                        {"variant": "wait", "item": item, "merge_commit": merge}))
            continue
        path, doc = receipts[0]
        out.append((_intent(ctx, "POST-READBACK", item["id"], stream="V", runner="model", pool="verifier", tier="opus", head=merge,
                            verdict_phase="post_deploy", evidence_fp=_a_evidence(item["id"], merge, path, doc),
                            card=_card(ctx, "verifier"), packet=_packet_path(ctx, item["id"]),
                            not_slot=review.get("lane") or review.get("slot"), effort="high"),
                    {"variant": "a", "item": item, "merge_commit": merge, "events": events}))
    for _, prepared in all_prepared(run):                                      # (b) a receipted operation
        found = _b_receipt(run, prepared)
        if found is None:
            continue
        path, rsha = found
        events = _events(ctx, prepared["item"])
        if events is None or _has_verdict(events, "artifact", digest=rsha):
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

        def effect():
            write_json(path, record)
            ctx.journal("post_readback_waiting", "%s is merged at %s and owes a post_deploy readback, but no COMPLETED measured readback "
                        "receipt of the item exists; none has been requested" % (job["item"], p["merge_commit"]))
            return {"path": str(path)}

        def observer(rec):
            return ("done", {"path": str(path)}) if path.exists() else ("not_done", "no marker")

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
    if rc == 0 and said.get("published", True) is not False:
        return _result("done", "kyverdicts.py published %s (%s)" % (said.get("result"), said.get("action_id")))
    why = said.get("reasons") or (err or out or "")[-200:]
    return _fail("POST-READBACK", job["item"], "publication_refused", "kyverdicts.py publish exited %r: %s" % (rc, why))


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
        if not isinstance(pr, dict):
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

def _executable(item):
    return item.get("done_by") not in ("decision", "join") and item.get("join") is not True


def _c_model(ctx):
    out = []
    for item in _items(ctx):
        if (item.get("owner") != "S" or not _is_ready(item) or not _executable(item) or item["id"] in MODEL_EXCLUDED):
            continue
        events = _events(ctx, item["id"])
        if events is None:
            continue
        digest = sha_canonical(item)
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
    kinds = [_etype(e) for e in later]
    if "review" in kinds:
        return _result("done", "the job registered a review")
    if "block" in kinds or "blocked" in kinds:
        return _result("blocked", "the job blocked the item")
    return _result("interrupted", "the job ended with neither a review nor a block event")


# ───────────────────────────────────────── RULING ─────────────────────────────────────────

def _inbox(ctx):
    """Unacked N messages: a list, or None when the inbox could not be read (exit 1 is "none")."""
    rc, out, _ = ctx.ky("inbox", "--stream", "N", "--json", stream="N")
    if rc == 1:
        return []
    if rc != 0:
        return None
    try:
        rows = json.loads(out)
    except (ValueError, TypeError):
        return None
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else None


def _c_ruling(ctx):
    rows = _inbox(ctx)
    if not rows:
        return []
    run, out, seen = _run(ctx), [], set()
    for msg in rows:
        mid = msg.get("msg_id")
        if not isinstance(mid, str) or not MESSAGE_ID.match(mid) or mid in seen or _handled_path(run, "msg.%s.json" % mid).exists():
            continue
        seen.add(mid)
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
        have = read_json(path)
        return ("done", {"path": str(path)}) if isinstance(have, dict) and have.get("msg_id") == mid else ("not_done", "no handled record")

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


def _awaiting_docs(ctx):
    directory, out = _run(ctx) / "awaiting", []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return out
    for name in names:
        if not name.endswith(".json") or name.endswith(OWNER_DECISION_SUFFIX):
            continue
        doc = read_json(directory / name)
        if isinstance(doc, dict) and doc.get("id") == name[:-len(".json")] and AWAITING_ID.match(str(doc["id"])):
            out.append(doc)
    return out


def _owner_answered(run, aid):
    """kyloop.open_awaiting's test: the owner has answered the item when <id>.owner_decision.json sits beside it."""
    return (run / "awaiting" / (aid + OWNER_DECISION_SUFFIX)).exists()


def _c_surrogate(ctx):
    run, out, rows = _run(ctx), [], False
    for doc in _awaiting_docs(ctx):
        aid, fp = doc["id"], awaiting_fingerprint(ctx, doc)
        handled = read_json(_handled_path(run, "awaiting.%s.json" % aid))
        if isinstance(handled, dict) and handled.get("fingerprint") == fp:
            if rows is False:
                rows = _veto_rows(ctx)
            row = rows.get(handled.get("decision_id")) if rows else None
            if row and row.get("state") in VETO_TERMINAL:
                digest = sha_canonical({"move": aid, "decision_id": handled["decision_id"], "state": row["state"]})
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


def _finish_surrogate(ctx, job):
    run, aid = _run(ctx), job.get("item")
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
    if (run / "awaiting" / "done" / ("%s.json" % aid)).exists() and not (run / "awaiting" / ("%s.json" % aid)).exists():
        return _result("done", "awaiting item %s is in awaiting/done/" % aid)
    return _result("interrupted", "the job's session wrote no decision line for %s" % aid)


# ───────────────────────────────────────── PLAN ─────────────────────────────────────────

def _packets_sha(ctx):
    directory = _repo(ctx) / PACKETS_REL
    try:
        names = sorted(n for n in os.listdir(directory) if n.startswith("PACKET_") and n.endswith(".md"))
    except OSError:
        names = []
    return sha_canonical([[n, file_sha(directory / n)] for n in names])


def _c_plan(ctx):
    run = _run(ctx)
    try:
        text = (run / "REPACKET.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""
    if text.strip():
        trigger, item, digest = "repacket", "REPACKET", sha_text(text)
    else:
        items = [i for i in _items(ctx) if not _is_closed(i) and _executable(i)]
        admitted = [i for i in items if i.get("status") == "running" and (run / "admission" / ("%s.json" % i["id"])).exists()]
        in_flight = [i for i in items if _is_ready(i) or str(i.get("status", "")).lower() == "review"]
        if not items or in_flight or admitted:
            return []
        trigger, item, digest = "boundary", "WAVE-BOUNDARY", sha_canonical(sorted(i["id"] for i in items))
    if _handled_path(run, "plan.%s.json" % digest[:12]).exists():
        return []
    fp = sha_canonical({"trigger": trigger, "digest": digest, "packets_sha256": _packets_sha(ctx)})
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
    if sha_canonical({"trigger": trigger, "digest": job.get("digest"), "packets_sha256": _packets_sha(ctx)}) == job.get("evidence_fp"):
        return _result("interrupted", "the packet set is unchanged: nothing was repacketed")
    path = _handled_path(_run(ctx), "plan.%s.json" % str(job.get("digest"))[:12])
    record = {"schema": HANDLED_SCHEMA, "kind": "plan", "trigger": trigger, "digest": job.get("digest"), "job_id": job.get("job_id")}

    def effect():
        write_json(path, record)
        return {"path": str(path)}

    def observer(rec):
        return ("done", {"path": str(path)}) if path.exists() else ("not_done", "no handled record")

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
    """Every job owed now, in kind order (I-13). Read-only: it reads files, the table, the inbox and the tracker."""
    out, seen = [], set()
    for kind in ORDER:
        for intent, _ in CANDIDATES[kind](ctx):
            if intent["key"] not in seen:
                seen.add(intent["key"])
                out.append(intent)
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
