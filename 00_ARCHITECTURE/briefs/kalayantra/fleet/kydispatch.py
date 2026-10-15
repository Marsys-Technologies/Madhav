#!/usr/bin/env python3
"""kydispatch.py — the dispatcher engine of KĀLA-YANTRA v3 (relaunch plan v2.7 §4 "Capacity", §6 "The dispatcher";
packet KV3-B-KYDISPATCH v1).

version: 1.0 · status: DRAFT (built under the hold; not installed, not merged by its job)
changelog: 1.0 (2026-10-12) first version, packet PACKET_KV3-B-KYDISPATCH_v1.
           1.0 rework (2026-10-13) re-read admission controls, refuse ambiguous PR checks and unknown interfaces.

    /opt/homebrew/bin/python3 -u $KY_FLEET/kydispatch.py            launchd KeepAlive: a tick every 30 s
    … --once                                                         one tick
    … --dry                                                          one tick, no lock, read-only; stdout
                                                                     {"schema": "ky.dispatch_plan/1",
                                                                      "jobs": [{kind, item, key, pool, decision}]}
Exit 0 clean stop · 75 no instance lock · 78 a credential variable name is set · 64 usage (also a $KY_ path that is
not absolute). Modules (kyd_jobs, kyd_admit, kyd_kinds_build, kyd_kinds_land, kyd_kinds_ops, kyaction, kycommands,
kyloop) are imported from this file's directory; scripts (kylock.sh, kygate.sh, kynotify.sh and what the modules
run) are run from $KY_FLEET.

Everything the engine decides is script logic over what the modules and commands answer; no model is asked. It
owns no rule of a kind, of admission or of a job's life: those are the five modules'. What is here is the order.

A tick (J = kyd_jobs, A = kyd_admit)
  1. $KY_RUN/STOP_dispatcher, or the loop file's `enabled` not true → stop (exit 0).
  2. The owner's commands for the dispatcher role, each through kycommands.apply: status · loops stop dispatcher
     (STOP_dispatcher, enabled false) · priority <item> · builders | verifiers <n> (1–8, the pool file); anything
     else is rejected.
  3. J.recover, J.supervise; a job that ended by itself gets its kind's finish; J.close.
  4. $KY_ROOT/HOLD, or an owner pause (unknown counts) → the tick ends: no admission of any kind.
  5. Freshness: `ky next --json` must carry an integer version above the last tick's, or the same one with
     $KY_RUN/EVENTS.jsonl unchanged (size, sha256); else ctx.next is None and nothing is admitted.
  6. git fetch in the campaign checkout; fast-forward to origin/main only while HOLD_MERGES is absent.
  7. Gate: `bash $KY_FLEET/kygate.sh` exit 0 → OPEN; anything else → WAIT: only KV3-B-* items.
  8. The intents of kyd_kinds_land, kyd_kinds_ops, kyd_kinds_build, in that order; under HOLD_MERGES a queue
     intent goes to kyd_kinds_land.park and nowhere else.
  9. Per intent, until a step says no: J.attempts · backoff (model runners) · a free slot of its pool ·
     A.precheck (a slot database that is not ready → A.provision, one slot a tick) · J.open · A.admit · the kind's
     start · J.launch for a model runner whose start gave no result, else J.close. After J.open any refusal or
     failed start → J.close, outcome refused.

decision (in --dry and in the log): `launch` (started, or would be) · `park` · `refused:<code of the refusing
step>` (attempts · open · launch · start · park · a kyd_admit code) · `wait:<hold | gate | backoff | slot | stale>`.

Files: the loop file $KY_RUN/loops/dispatcher.json (kyloop.loop_state / update_loop_state; `enabled` is kyloop.py
admin's and is written here only by `loops stop dispatcher`): last_iteration_at, controller{id, pid}, waiting,
log_path, and this engine's own backoff, tracker, priority and conditions (the gate as last read, and what the
last tick journalled — what "once per changed condition" is judged against). The journal $KY_RUN/JOURNAL_DISPATCHER.md.
The log $KY_SCRATCH/dispatcher/<controller_id>.log. Job state only through kyd_jobs.

INTERPRETATION (the packet's "(I)", and what packet and plan leave open; each errs to doing less)
  * ctx.ky runs $KY_ROOT/bin/ky (install_tracker.sh's wrapper) through ctx.sh, with KY_STREAM and KY_LANE for
    `stream` and `lane`.
  * controller_id = CTL-dispatcher-<UTC yyyymmddThhmmssZ>-<pid>. The instance lock is released only at a stop with
    no job that has not ended; a lock kept for a live job is taken over by the next instance, which adopts the job.
  * --dry reads the run directory as the controller the loop file names (slot databases and jobs are that
    controller's), computes also under a hold (every job `wait:hold`) and performs no step that writes: no
    command, recovery, fetch, provisioning, parking, journal, notification or owner-wait.
  * A job of the intent's key that has not ended, or its handled record backed by its ended done job, is
    `refused:open` without calling J.open. An unreadable or unbacked handled record is unknown (`wait:stale`).
  * Pool sizes: the integer 1–8 in $KY_RUN/KY_WORKERS / KY_VERIFIERS; absent → 6 / 4; anything else → 0 (no
    capacity is never guessed). limits.copies = 16 (owner Amendment A1 D-16). Ready work that finds every slot of its pool in use raises
    ctx.awaiting("capacity-above-max", …) while the pool is below 8.
  * Backoff: a job that ended with failure_fp `quota` steps 5 → 10 → 20 → 30 min (once per job) and no model
    runner is launched before `until`; a model job that ended without it resets the steps.
  * Fresh on the first reading of a run directory (no `tracker` record yet): there is nothing to compare with.
  * ctx.pr: `gh pr list --head kalayantra/<item>` lists open pull requests (gh's default), so "no open PR" is None.
    A check's `attempt` is the number in its detailsUrl and null when the URL names none (never assumed 1). Two
    entries of one name: disagreement is unknown; list order never makes a failing check green.
  * ctx.verify: GET <tracker>/api/verify?id=<item>&step=<step> on loopback (KY_TRACKER_URL, default
    http://127.0.0.1:8767). True only for a reply that names this item AND this step with detector.status `done`;
    False for another status of that step; None for anything else — a reply that does not name the step is a
    tracker answering for the item's own detector, and None never permits `ky step`.
  * ctx.events: the item's lines of EVENTS.jsonl; a line that is not a JSON object makes the whole log unknown
    (None) for this reading — it may be anybody's review or verdict. Objects must also carry the producer's
    required fields; duplicate JSON keys are unknown, never a later value hiding a failure.
  * ctx.act: kyaction's record around one effect. effect() may answer (done | failed | unknown, result) — then
    that is recorded — or a plain result object (kyd_kinds_land, kyd_kinds_ops): then the observer says whether
    it is done; an effect that raises is recorded failed.
  * Journal lines and their notifications are written once per changed condition: a line identical to one of the
    previous tick is not repeated.
  * `surrogate decision` is journalled when a SURROGATE model job's validated proposal is recorded; claimed
    EFFECTIVE/EXECUTED states need the handler's own record. A boundary PLAN intent is logged as waiting for
    planning, never as wave completion. `gate change` is journalled when kygate.sh's answer changes.
  * STOP, global HOLD, enabled and the owner pause are re-read at admission boundaries, before J.open,
    before kind.start and before J.launch. A newly detected control latches `wait:hold` for the remaining
    intents; a job already opened is closed refused before any start or launch.
  * kynotify.sh exit 0 proves its journal append, not notification submission: only its exact
    `notify=submitted` reply completes the notification action. Failed/dry/unknown replies never read done.
  * Corrupt persisted quota/freshness state never becomes a fresh start. An unknown backoff waits; an unknown
    previous tracker version prevents admissions until reconciled. Ambiguous loop JSON is a reported stop.
  * What the modules' contracts do not agree on, bridged here without touching them (each is named in the PR):
      - kyd_kinds_ops lists the job lock first in an intent's locks[]; kyd_jobs.open takes job.<key> itself and
        then every name of locks[]. The job lock is left out of the locks[] handed to J.open and A.precheck.
      - kyd_admit.precheck refuses `base` for an item the plan model does not hold; RULING (msg.<id>), SURROGATE
        (an awaiting id) and PLAN (REPACKET, WAVE-BOUNDARY) name no plan item. They are prechecked with item None,
        the form kyd_admit reads as "no item worktree, no prerequisites".
      - kyd_admit.admit compares the item lock's owner with ctx.controller_id; kyd_jobs binds a job's locks to
        "<controller_id>:job.<key>". A.admit is handed a ctx whose controller_id is that owner id.
      - ctx.now(): kyd_admit wants a time it can add seconds to, kyd_kinds_ops writes it as a record's `ts`.
        A gets epoch seconds; everyone else UTC text YYYY-MM-DDTHH:MM:SSZ.
      - tracker state.py emits status/steps, not completion_kind or step_evidence. The engine joins those
        declarations from ctx.model for kyd_kinds_build, which reads them from rows; missing or contradictory
        declarations on executable items make the tracker context unknown. Decision/join items may have null
        declarations (plan §6 requires them only for retained executable items). They are never detector results.
    A refusal after J.open carries a failure class (`admit_<code>`, the kind's own, `launch`), so that the third
    identical one blocks automatic attempts (kyd_jobs' failure accounting) instead of claiming every tick.
Python >= 3.9, standard library only.
"""
from __future__ import annotations

import hashlib
import datetime as dt
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kyaction as ka  # noqa: E402
import kycommands as kc  # noqa: E402
import kyd_admit as A  # noqa: E402
import kyd_jobs as J  # noqa: E402
import kyd_kinds_build as B  # noqa: E402
import kyd_kinds_land as L  # noqa: E402
import kyd_kinds_ops as O  # noqa: E402
import kyloop  # noqa: E402
import kyschema  # noqa: E402

VERSION = "1.0"
PLAN_SCHEMA = "ky.dispatch_plan/1"
ROLE = "dispatcher"
TICK_S = 30
EX_OK, EX_USAGE, EX_NO_LOCK, EX_CREDENTIAL = 0, 64, 75, 78
USAGE = "usage: kydispatch.py [--once | --dry]"
DEFAULT_ROOT = "/Users/Dev/kalayantra"
CAMPAIGN_CHECKOUT = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"      # plan §5
PLAN_MODEL = os.path.join("00_ARCHITECTURE", "control", "kalayantra", "plan_model.json")
TRACKER_URL = "http://127.0.0.1:8767"
LOOPBACK = re.compile(r"^http://(127\.0\.0\.1|localhost):[0-9]{1,5}\Z")
POOLS = {"builder": ("b", "KY_WORKERS", 6), "verifier": ("v", "KY_VERIFIERS", 4)}
POOL_MAX = 8                # owner direction of 2026-10-12 (PLANNER_STATE active.owner_directions_20261012)
COPIES = 16
BACKOFF_MINUTES = (5, 10, 20, 30)
BOOTSTRAP_PREFIX = "KV3-B-"
NO_PLAN_ITEM = ("RULING", "SURROGATE", "PLAN")      # kinds whose intent names no item of the plan model
SLOT_CODES = ("slot_not_ready", "slot_foreign")
SH_ENV = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "KY_SOURCE_REPO", "KY_TRACKER_URL",
          "GIT_OPTIONAL_LOCKS", "PYTHONDONTWRITEBYTECODE",
          "PRAVAHA_HOME", "PRAVAHA_EVENTS", "PRAVAHA_PLAN_MODEL", "PRAVAHA_REPO", "PRAVAHA_HOLD",
          "PRAVAHA_TRACKER_PORT", "PRAVAHA_URL")  # preserve overrides; the ky wrapper validates the complete set
PR_FIELDS = ("number,headRefOid,baseRefName,title,state,mergeable,mergeStateStatus,statusCheckRollup,mergeCommit,"
             "files,autoMergeRequest")
RUN_URL = re.compile(r"/actions/runs/([0-9]+)(?:/attempts/([0-9]+))?")
REVIEW_PR = re.compile(r"PR #([0-9]+) @ [0-9a-f]{40}(?![0-9a-f])")
HEAD_RE = re.compile(r"^[0-9a-f]{40}\Z")
# plan §6 "Messaging": the events that also notify the owner, and at which level
NOTIFY = {"surrogate decision": "decision", "hard stop": "hard_stop", "verdict invalidation": "info",
          "gate change": "info", "wave complete": "info", "quota backoff": "info", "dispatcher error": "info",
          "ceiling hit": "info", "unclassifiable ci failure": "info"}
MODULES = dict([(k, B) for k in B.KINDS] + [(k, L) for k in L.KINDS] + [(k, O) for k in O.KINDS])
NO_BACKOFF = {"level": 0, "until": None, "job": None}
CAPACITY_OPTIONS = [{"id": "raise", "text": "Raise the pool's maximum (kyveto capacity, at most 8)."},
                    {"id": "keep", "text": "Keep the maximum; the ready work waits for a slot."}]


# ───────────────────────────────────────── what is decided from an answer alone ─────────────────────────────────────────

def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _json(text):
    """Reject duplicate keys and non-JSON constants: a second key must never hide a failure."""
    return kyschema.load_json_text(text)


def read_loop(run):
    """kyloop's state, with ambiguous JSON refused rather than selecting the last enabled/backoff value."""
    doc, err = kyloop.loop_state(run, ROLE)
    if err:
        return None, err
    try:
        checked = kyschema.load_json(Path(run) / "loops" / (ROLE + ".json"))
    except FileNotFoundError:
        return ({}, None) if doc == {} else (None, "loop file disappeared")
    except (OSError, ValueError):
        return None, "loop file unreadable or ambiguous"
    return (doc, None) if isinstance(checked, dict) and checked == doc else (None, "loop file changed while reading")


def next_known(nxt):
    """The unfiltered /api/next shape produced by pravaha_tracker/server.py, not a snapshot or a guessed bucket."""
    if not isinstance(nxt, dict) or nxt.get("stream") != "" or not _is_int(nxt.get("version")) or nxt["version"] < 0:
        return False
    ids = set()
    for bucket, states in O.NEXT_BUCKETS:
        rows = nxt.get(bucket)
        if not isinstance(rows, list):
            return False
        for row in rows:
            if (not isinstance(row, dict) or not isinstance(row.get("id"), str) or not A.ITEM_RE.fullmatch(row["id"])
                    or not isinstance(row.get("owner"), str) or not row["owner"] or row.get("status") not in states
                    or row["id"] in ids):
                return False
            ids.add(row["id"])
    return True


def event_known(event):
    """Required fields of the records events.py validate/append actually emits (including normalized ts).
    A malformed object may conceal a verdict or a review; it makes the whole reading unknown."""
    if not isinstance(event, dict) or event.get("kind") not in O.EVENT_KINDS \
            or not isinstance(event.get("actor"), str) or not event["actor"]:
        return False
    try:
        dt.datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError):
        return False
    kind = event["kind"]
    if kind in ("item", "claim", "verdict") and not isinstance(event.get("item"), str):
        return False
    if kind == "item":
        return (bool(event["item"]) and event.get("state") in ("ready", "running", "review", "blocked", "parked", "failed", "done")
                and (event["state"] != "done" or bool(event.get("evidence")))
                and (event["state"] not in ("blocked", "failed", "parked") or bool(event.get("detail"))))
    if kind == "claim":
        try:
            dt.datetime.fromisoformat(event["expires_at"].replace("Z", "+00:00"))
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
        return (event.get("state") in ("acquired", "renewed", "released", "expired")
                and all(isinstance(event.get(k), str) and event[k] for k in ("item", "worker_id", "claim_id")))
    if kind == "verdict":
        head, digest = event.get("head"), event.get("artifact_digest")
        return (bool(event["item"]) and event.get("result") in ("ACCEPTED", "REJECTED") and bool(event.get("detail"))
                and ((event.get("phase") == "artifact" and not head and isinstance(digest, str) and kyloop.SHA_RE.fullmatch(digest))
                     or (event.get("phase") in ("pre_merge", "post_deploy") and not digest
                         and isinstance(head, str) and HEAD_RE.fullmatch(head))))
    if kind == "decision":
        return (bool(event.get("decision")) and event.get("state") in ("pending", "requested", "decided", "delegated")
                and (event["state"] not in ("decided", "delegated") or bool(event.get("detail"))))
    if kind == "message":
        return (isinstance(event.get("to"), str) and bool(re.fullmatch(r"[A-Z][A-Z0-9_-]*|steward", event["to"]))
                and bool(event.get("msg_id")) and bool(event.get("detail")))
    if kind == "ack":
        return bool(event.get("msg_id"))
    return kind != "metric" or bool(event.get("name"))


def pool_size(path, default):
    """The pool file's integer 1–8; `default` when there is no file; 0 for anything else (unreadable)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read(64).strip()
    except FileNotFoundError:
        return default
    except (OSError, ValueError):
        return 0
    return int(text) if re.match(r"^[1-8]\Z", text) else 0


def fresh(nxt, seen, events_now):
    """Is this `ky next --json` answer the live tracker's, and no older than what the last tick stood on?
    nxt: the parsed answer · seen: the last tick's {version, events_size, events_sha256} or None · events_now:
    {events_size, events_sha256} of EVENTS.jsonl now, None when it cannot be read."""
    if not isinstance(nxt, dict) or not _is_int(nxt.get("version")):
        return False                                     # the snapshot fallback carries no version
    if not isinstance(seen, dict) or not _is_int(seen.get("version")):
        return True
    if nxt["version"] != seen["version"]:
        return nxt["version"] > seen["version"]
    return isinstance(events_now, dict) and all(events_now.get(k) == seen.get(k) and seen.get(k) is not None
                                                for k in ("events_size", "events_sha256"))


def map_pr(doc):
    """`gh pr view --json …` → the shape KV3-B-KYDKINDS-BUILD's module documents, or "unknown"."""
    if not isinstance(doc, dict) or not _is_int(doc.get("number")) or not isinstance(doc.get("state"), str) \
            or not isinstance(doc.get("headRefOid"), str) or not HEAD_RE.match(doc["headRefOid"]):
        return "unknown"
    checks = {}
    rollup = doc.get("statusCheckRollup")
    if rollup is not None and not isinstance(rollup, list):
        return "unknown"
    for entry in rollup or []:
        if not isinstance(entry, dict):
            return "unknown"
        name = entry.get("name") if isinstance(entry.get("name"), str) else entry.get("context")
        if not isinstance(name, str) or not name:
            return "unknown"
        if "state" in entry and "status" not in entry:                    # a StatusContext
            status, url = entry.get("state"), entry.get("targetUrl")
            if status not in ("ERROR", "FAILURE", "PENDING", "SUCCESS"):
                return "unknown"
        else:                                                              # a CheckRun
            status, url = entry.get("status"), entry.get("detailsUrl")
            if status not in ("QUEUED", "IN_PROGRESS", "COMPLETED", "WAITING", "REQUESTED", "PENDING") or "state" in entry:
                return "unknown"
            if status == "COMPLETED":
                if entry.get("conclusion") not in ("ACTION_REQUIRED", "CANCELLED", "FAILURE", "NEUTRAL", "SKIPPED", "STALE",
                                                    "STARTUP_FAILURE", "SUCCESS", "TIMED_OUT"):
                    return "unknown"
                status = entry["conclusion"]
        found = RUN_URL.search(url) if isinstance(url, str) else None
        check = {"status": status.upper() if isinstance(status, str) else None,
                 "run_id": int(found.group(1)) if found else None,
                 "attempt": int(found.group(2)) if found and found.group(2) else None}
        if name in checks and checks[name] != check:
            return "unknown"
        checks[name] = check
    files = doc.get("files")
    if files is not None:
        if not isinstance(files, list) or not all(isinstance(f, dict) and isinstance(f.get("path"), str) for f in files):
            return "unknown"
        files = [f["path"] for f in files]
    merge = doc.get("mergeCommit")
    merge = merge.get("oid") if isinstance(merge, dict) else None
    return {"number": doc["number"], "head": doc["headRefOid"], "base": doc.get("baseRefName"), "title": doc.get("title"),
            "state": doc["state"], "mergeable": doc.get("mergeable"), "merge_state": doc.get("mergeStateStatus"),
            "checks": checks, "merge_commit": merge if isinstance(merge, str) and HEAD_RE.match(merge) else None,
            "files": files, "auto_merge": doc.get("autoMergeRequest")}


def paths_problem(environ):
    """None, or why the engine's paths are unusable (a relative or missing $KY_ path)."""
    root = environ.get("KY_ROOT") or DEFAULT_ROOT
    paths = {"KY_ROOT": root, "KY_RUN": environ.get("KY_RUN") or os.path.join(root, "run"),
             "KY_FLEET": environ.get("KY_FLEET") or os.path.join(root, "fleet_live"),
             "KY_SCRATCH": environ.get("KY_SCRATCH"), "KY_SOURCE_REPO": environ.get("KY_SOURCE_REPO") or CAMPAIGN_CHECKOUT}
    for name, value in paths.items():
        if not isinstance(value, str) or not os.path.isabs(value):
            return "%s is %s" % (name, "not set" if not value else "not an absolute path")
    return None


def _observed(observer, record):
    """An observer's answer in kyaction.reconcile's form; one that raises or answers otherwise has seen nothing."""
    try:
        answer = observer(json.loads(json.dumps(record)))
    except Exception as e:
        return "unknown", {"error": "observer_raised: %s" % type(e).__name__}
    if not isinstance(answer, (tuple, list)) or len(answer) != 2 or answer[0] not in ("done", "not_done", "unknown"):
        return "unknown", {"error": "observer_answer_invalid"}
    return answer[0], answer[1]


def job_lock_owner(controller_id, key):
    """The owner id kyd_jobs gives a job's locks (its _owner): what kyd_admit.admit must find on the item lock."""
    return "%s:job.%s" % (controller_id, key)


class _View:
    """ctx as one module's contract wants it: the engine's ctx with the named attributes replaced."""

    def __init__(self, base, **replaced):
        self.__dict__["_base"] = base
        self.__dict__.update(replaced)

    def __getattr__(self, name):
        return getattr(self._base, name)


# ───────────────────────────────────────── ctx ─────────────────────────────────────────

class Ctx:
    """What the five modules are handed (their packets' `ctx`)."""

    def __init__(self, engine):
        e = self._engine = engine
        self.root, self.run, self.fleet, self.scratch, self.repo = e.root, e.run, e.fleet, e.scratch, e.repo
        self.paths = {"root": e.root, "run": e.run, "fleet": e.fleet, "scratch": e.scratch, "repo": e.repo}
        self.model = os.path.join(e.repo, PLAN_MODEL)
        self.controller_id = e.controller_id
        self.limits = {"builders": 0, "verifiers": 0, "copies": COPIES}
        self.priority = []
        self.sh, self.ky, self.act, self.awaiting, self.journal = e.sh, e.ky, e.act, e.awaiting, e.journal
        self.events, self.pr, self.verify, self.veto_status = e.events, e.pr, e.verify, e.veto_status

    @property
    def next(self):
        return self._engine.tracker_next()

    def now(self):
        return ka.utc(int(self._engine.clock()))

    def accepted(self, item):
        return L.accepted_head(self, item)


# ───────────────────────────────────────── the engine ─────────────────────────────────────────

class Engine:
    def __init__(self, environ, dry=False):
        self.environ, self.dry = dict(environ), dry
        self.root = environ.get("KY_ROOT") or DEFAULT_ROOT
        self.run = environ.get("KY_RUN") or os.path.join(self.root, "run")
        self.fleet = environ.get("KY_FLEET") or os.path.join(self.root, "fleet_live")
        self.scratch = environ["KY_SCRATCH"]
        self.repo = environ.get("KY_SOURCE_REPO") or CAMPAIGN_CHECKOUT
        self.clock = time.time
        self.stopping = False
        self.controller_id = "CTL-%s-%s-%d" % (ROLE, ka.utc(fmt="%Y%m%dT%H%M%SZ"), os.getpid())
        loop, _ = read_loop(self.run)
        loop = loop or {}
        if dry:                                          # read the run directory as the controller that runs it
            named = loop.get("controller") if isinstance(loop.get("controller"), dict) else {}
            if isinstance(named.get("id"), str) and named["id"]:
                self.controller_id = named["id"]
        self.log_path = os.path.join(self.scratch, "dispatcher", self.controller_id + ".log")
        self.backoff = dict(NO_BACKOFF)
        self.priority_cmd = []
        self.tracker_seen = None
        self.gate_seen = None
        self.seen_before, self.seen_now = set(), set()
        self._adopt(loop)
        self._events_cache = (None, None)
        self._pr_cache = {}
        self._next = (False, None)
        self._tick_error = False
        self.ctx = Ctx(self)
        self.admit_ctx = _View(self.ctx, now=lambda: int(self.clock()))

    def _adopt(self, loop):
        """This engine's own keys of the loop file, as an earlier controller left them."""
        backoff = loop.get("backoff")
        if (isinstance(backoff, dict) and _is_int(backoff.get("level")) and 0 <= backoff["level"] <= len(BACKOFF_MINUTES)
                and ((backoff["level"] == 0 and backoff.get("until") is None and backoff.get("job") is None)
                     or (backoff["level"] > 0 and ka.parse_utc(backoff.get("until")) is not None
                         and isinstance(backoff.get("job"), str) and backoff["job"]))):
            self.backoff = {"level": backoff["level"], "until": backoff.get("until"), "job": backoff.get("job")}
        elif "backoff" in loop:
            self.backoff = {"level": None, "until": None, "job": None}
        priority = loop.get("priority")
        self.priority_cmd = [p for p in priority if isinstance(p, str) and p] if isinstance(priority, list) else []
        tracker = loop.get("tracker")
        self._tracker_unknown = tracker is not None and (not isinstance(tracker, dict) or not _is_int(tracker.get("version"))
                                                         or tracker["version"] < 0)
        self.tracker_seen = tracker
        self.tracker_retry = loop.get("tracker_retry") is True
        conditions = loop.get("conditions") if isinstance(loop.get("conditions"), dict) else {}
        self.gate_seen = conditions.get("gate") if conditions.get("gate") in ("OPEN", "WAIT") else None
        seen = conditions.get("seen")
        self.seen_before = {s for s in seen if isinstance(s, str)} if isinstance(seen, list) else set()

    # ── commands ──
    def sh(self, argv, env=None, cwd=None, timeout=120):
        """(rc, out, err); rc None: the command could not be run or did not end."""
        full = {k: self.environ[k] for k in SH_ENV if k in self.environ}
        full.update(KY_ROOT=self.root, KY_RUN=self.run, KY_FLEET=self.fleet, KY_SCRATCH=self.scratch)
        full.update({k: str(v) for k, v in (env or {}).items()})
        try:
            done = subprocess.run([os.fspath(a) for a in argv], env=full, cwd=os.fspath(cwd) if cwd else None,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                                  stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return None, "", "no answer within %s s" % timeout
        except (OSError, ValueError) as e:
            return None, "", "%s: %s" % (type(e).__name__, ka.flat(e, 200))
        return done.returncode, done.stdout, done.stderr

    def ky(self, *args, stream=None, lane=None):
        env = {k: v for k, v in (("KY_STREAM", stream), ("KY_LANE", lane)) if v is not None}
        return self.sh([os.path.join(self.root, "bin", "ky")] + [str(a) for a in args], env=env)

    def _script(self, name):
        return os.path.join(self.fleet, name)

    # ── kyaction's record around one side effect ──
    def act(self, action_id, kind, inputs, target, effect, observer):
        if self.dry:
            return "unknown", {"reason": "--dry performs no side effect"}
        self._pr_cache.clear()
        actor = {"role": ROLE, "holder_kind": "controller", "controller_id": self.controller_id}
        status, record = ka.begin(self.run, action_id, kind, actor, inputs, target, kind)
        if status in ("done", "failed"):
            return status, record.get("result")
        if status == "in_progress":
            return "unknown", {"reason": "another actor is in the middle of it"}
        if status == "unfinished":
            outcome, after = ka.reconcile(self.run, action_id, observer, by=self.controller_id)
            if outcome == "done":
                return "done", after.get("result")
            if outcome != "not_done":
                return "unknown", {"reason": "reconciliation: %s" % outcome}
        elif status != "new":
            self._unknown("action", "begin returned an unrecognised status")
            return "unknown", {"reason": "action status unknown"}
        try:
            answer = effect()
        except Exception as e:                           # the observed failure of the effect is the record
            result = {"error": "%s: %s" % (type(e).__name__, ka.flat(e, 300))}
            ka.fail(self.run, action_id, result)
            return "failed", result
        finally:
            self._pr_cache.clear()
        if isinstance(answer, tuple) and len(answer) == 2 and answer[0] in ("done", "failed", "unknown"):
            outcome, result = answer
        else:                                            # a plain result: only the observer says it is done
            seen, detail = _observed(observer, record)
            outcome = {"done": "done", "not_done": "failed"}.get(seen, "unknown")
            result = answer if outcome == "done" and isinstance(answer, dict) else \
                {"effect": answer if isinstance(answer, dict) else ka.flat(answer, 300), "observed": detail}
        try:
            json.loads(ka.canonical(result).decode("utf-8"))
        except (TypeError, ValueError, RecursionError):
            self._unknown("action", "effect returned a result that is not JSON")
            return "unknown", {"reason": "action result is not JSON"}
        if outcome == "done":
            ka.complete(self.run, action_id, result)
        elif outcome == "failed":
            ka.fail(self.run, action_id, result)
        return outcome, result

    # ── messaging ──
    def journal(self, event, text):
        """One line of $KY_RUN/JOURNAL_DISPATCHER.md — and, for the plan's quoted events, one notification — per
        changed condition: a line the previous tick already wrote is not written again."""
        if event.lower() == "dispatcher error":
            self._tick_error = True
        event, text = ka.flat(event, 80), ka.flat(text, 2000)
        key = hashlib.sha256(("%s\n%s" % (event, text)).encode("utf-8")).hexdigest()[:16]
        if key in self.seen_before or key in self.seen_now:
            self.seen_now.add(key)
            return
        self.seen_now.add(key)
        if self.dry:
            sys.stderr.write("kydispatch: [%s] %s\n" % (event, text))
            return
        os.makedirs(self.run, exist_ok=True)
        with open(os.path.join(self.run, "JOURNAL_DISPATCHER.md"), "a", encoding="utf-8") as f:
            f.write("- %s [%s] %s\n" % (ka.utc(), event, text))
        level = NOTIFY.get(event.lower())
        if level is None:
            return
        message = "%s: %s" % (event, ka.flat(text, 400))

        def effect():
            rc, out, err = self.sh(["bash", self._script("kynotify.sh"), message, "--level", level])
            outcome = ("done" if rc == 0 and out in ("notify=submitted", "notify=submitted\n") else
                       "failed" if rc is not None and (rc != 0 or out in ("notify=failed\n", "notify=dry\n")) else "unknown")
            return outcome, \
                {"rc": rc, "notify": ka.flat(out, 40), "err": ka.flat(err, 200)}

        try:
            outcome, result = self.act("NOTIFY-%s-%s" % (ka.utc(fmt="%Y%m%dT%H%M%SZ"), key), "notification",
                                       {"message": message, "level": level},
                                       {"journal": os.path.join(self.run, "JOURNAL_COCKPIT.md")}, effect,
                                       lambda record: ("unknown", {"reason": "a notification cannot be observed"}))
        except ka.ActionError as e:
            outcome, result = "unknown", {"error": ka.flat(e, 200)}
        if outcome != "done":
            self.log("notification of [%s] %s: %s" % (event, outcome, ka.flat(result, 200)))

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        """A ky.awaiting/1 item in $KY_RUN/awaiting — none while an open one of this slug asks the same question.
        → its id, or None."""
        if self.dry:
            sys.stderr.write("kydispatch: [awaiting] %s: %s\n" % (slug, ka.flat(question, 300)))
            return None
        if not re.match(r"^[a-z0-9-]+\Z", slug or ""):
            raise ValueError("awaiting slug %r is not lower-case letters, digits and hyphens" % (slug,))
        directory = Path(self.run) / "awaiting"
        os.makedirs(directory, exist_ok=True)
        for path in sorted(directory.glob("AW-*-%s.json" % slug)):
            try:
                doc = kyschema.load_json(path)
                valid = (isinstance(doc, dict) and doc.get("id") == path.stem
                         and not kyschema.validate(kyschema.load_json(HERE / "schemas" / "awaiting.json"), doc))
            except (OSError, ValueError):
                valid = False
            if not valid:
                return self._unknown("awaiting", "%s is not a readable awaiting record" % path)
            if doc.get("question") == question and self._owner_answered(path.stem) is not True:
                return doc["id"]
        t = int(time.time())
        while True:
            aid = "AW-%s-%s" % (ka.utc(t, "%Y%m%dT%H%M%SZ"), slug)
            if not any(os.path.lexists(p) for p in (directory / (aid + ".json"),
                                                    directory / (aid + kyloop.OWNER_DECISION_SUFFIX),
                                                    directory / kyloop.AWAITING_DONE / (aid + ".json"))):
                break
            t += 1
        ka.write_json(directory / (aid + ".json"), {
            "schema": "ky.awaiting/1", "id": aid, "created_at": ka.utc(),
            "raised_by": {"role": ROLE, "session_id": self.controller_id, "job_id": None},
            "item": item if isinstance(item, str) and item else None, "question": question,
            "options": [{"id": str(o["id"]), "text": str(o["text"])} for o in options], "recommendation": None,
            "evidence": [os.fspath(e) for e in evidence if e is not None], "deadline": None,
            "class_hint": class_hint if class_hint in ("routine", "veto", "hard_stop", "unknown") else "unknown",
            "blocks": "item" if isinstance(item, str) and item else "none"})
        return aid

    def _owner_answered(self, aid):
        """kyloop.owner_answers' predicate: the owner's record AND its acceptable cockpit decide command."""
        path = Path(self.run) / "awaiting" / (aid + kyloop.OWNER_DECISION_SUFFIX)
        if not os.path.lexists(path):
            return False
        try:
            rec = kyschema.load_json(path)
            entries, problems = kc.scan(self.run)
            if problems:
                return self._unknown("owner answer", "the command queue cannot be read")
            if isinstance(rec, dict) and rec.get("schema") == kyloop.OWNER_DECISION_SCHEMA and rec.get("awaiting_id") == aid:
                for entry in entries:
                    cmd = entry["doc"]
                    if (not entry["invalid"] and cmd["id"] == rec.get("command_id") and cmd["command"] == "decide"
                            and cmd["state"] in ("QUEUED", "APPLIED") and cmd["args"].get("awaiting_id") == aid
                            and cmd["args"].get("answer") == rec.get("answer")):
                        return True
        except (OSError, ValueError, kc.CommandError):
            pass
        return self._unknown("owner answer", "%s has no matching owner command" % path)

    def log(self, text):
        if self.dry:
            return
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write("%s %s\n" % (ka.utc(), ka.flat(text, 4000)))
        except OSError:
            pass

    # ── what the tracker, GitHub and the event log say ──
    def _unknown(self, interface, reason):
        self.journal("dispatcher error", "%s unknown: %s" % (interface, reason))
        return None

    def _events_signature(self):
        path = os.path.join(self.run, "EVENTS.jsonl")
        try:
            size = os.path.getsize(path)
        except OSError:
            return None
        digest = ka.sha_file(path)
        return {"events_size": size, "events_sha256": digest} if digest else None

    def tracker_next(self):
        """The tick's one `ky next --json` reading: the answer when it is fresh, else None."""
        read, value = self._next
        if read:
            return value
        if self._tracker_unknown:
            self._next = (True, None)
            return self._unknown("tracker checkpoint", "the previous version is unreadable; it cannot be reset to a first tick")
        before = self._events_signature()
        rc, out, _ = self.ky("next", "--json")
        try:
            nxt = _json(out) if rc == 0 else None
        except (ValueError, RecursionError):
            nxt = None
        now = self._events_signature()
        # ky next carries only a snapshot version (server.py:388-391), not a processed EVENTS
        # digest/count. After an error, keep the original freshness fence: changed checkpoint bytes
        # require a version ABOVE the last accepted one. Stability during the request alone proves nothing.
        stable_retry = not self.tracker_retry or (isinstance(before, dict) and before == now)
        known = next_known(nxt)
        value = self._declarations(nxt) if known and stable_retry and fresh(nxt, self.tracker_seen, now) else None
        if value is None:
            if (self.tracker_retry and known and isinstance(self.tracker_seen, dict)
                    and nxt["version"] == self.tracker_seen["version"] and isinstance(now, dict)
                    and not fresh(nxt, self.tracker_seen, now)):
                self.journal("tracker wait", "EVENTS changed since checkpoint; waiting for tracker version above %s"
                             % self.tracker_seen["version"])
            else:
                self._unknown("tracker", "ky next has no recognisable fresh unfiltered live answer (exit %s)" % rc)
        if value is not None:
            self.tracker_seen = dict(now or {"events_size": None, "events_sha256": None}, version=nxt["version"])
        self._next = (True, value)
        return value

    def _declarations(self, nxt):
        """Bridge actual tracker rows to the build module using the real plan model's declared fields."""
        try:
            doc = kyschema.load_json(self.ctx.model)
            items = doc.get("items") if isinstance(doc, dict) else None
            if (not isinstance(items, list) or any(not isinstance(i, dict) or not isinstance(i.get("id"), str) for i in items)
                    or len({i["id"] for i in items}) != len(items)):
                raise ValueError("model has no unique items list")
            declared = {i["id"]: i for i in items}
            result = dict(nxt)
            for bucket, _ in O.NEXT_BUCKETS:
                result[bucket] = []
                for row in nxt[bucket]:
                    item = declared.get(row["id"])
                    if (item is None or item.get("owner") != row["owner"]
                            or (item.get("completion_kind") not in ("code", "artifact", "packet", "operation")
                                and not (not O._executable(item) and item.get("completion_kind") is None))
                            or item.get("step_evidence") is not None and not isinstance(item["step_evidence"], dict)):
                        raise ValueError("%s lacks a usable declaration" % row["id"])
                    fields = {key: item.get(key) for key in ("completion_kind", "step_evidence")}
                    if any(key in row and row[key] != value for key, value in fields.items()):
                        raise ValueError("%s contradicts its declaration" % row["id"])
                    result[bucket].append(dict(row, **fields))
            return result
        except (OSError, ValueError) as e:
            return self._unknown("tracker declaration", "%s: %s" % (self.ctx.model, ka.flat(e, 200)))

    def _all_events(self):
        path = os.path.join(self.run, "EVENTS.jsonl")
        try:
            data = Path(path).read_bytes()
        except OSError:
            return self._unknown("events", "EVENTS.jsonl cannot be read")
        signature = hashlib.sha256(data).hexdigest()
        if self._events_cache[0] == signature:
            return self._events_cache[1]
        events = []
        try:
            for line in data.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                event = _json(line)
                if not event_known(event):
                    raise ValueError("unrecognised event record")
                events.append(event)
        except (OSError, ValueError, RecursionError):
            events = self._unknown("events", "EVENTS.jsonl has an unreadable or unrecognised record")
        self._events_cache = (signature, events)
        return events

    def events(self, item):
        events = self._all_events()
        return None if events is None else [dict(e) for e in events if e.get("item") == item]

    def pr(self, item):
        if item in self._pr_cache:
            return self._pr_cache[item]
        self._pr_cache[item] = found = self._pr(item)
        return found

    def _pr(self, item):
        def unknown(reason):
            self._unknown("PR", "%s: %s" % (item, reason))
            return "unknown"

        events = self.events(item)
        if events is None or not isinstance(item, str):
            return unknown("events or item cannot be read")
        number = None
        for event in reversed(events):
            if event.get("kind") == "item" and event.get("state") == "review" and not event.get("step"):
                found = REVIEW_PR.search(event.get("detail") if isinstance(event.get("detail"), str) else "")
                number = int(found.group(1)) if found else None
                break
        argv = ["gh", "pr", "view", str(number), "--json", PR_FIELDS] if number is not None else \
            ["gh", "pr", "list", "--head", "kalayantra/" + item.lower(), "--json", PR_FIELDS]
        rc, out, _ = self.sh(argv, cwd=self.repo)
        if rc != 0:
            return unknown("gh did not answer (exit %s)" % rc)
        try:
            doc = _json(out)
        except (ValueError, RecursionError):
            return unknown("gh answered invalid JSON")
        if number is None:
            if not isinstance(doc, list):
                return unknown("gh pr list did not answer a list")
            if not doc:
                return None
            if len(doc) != 1:
                return unknown("gh pr list answered more than one PR for this branch")
            doc = doc[0]
        if number is not None and (not isinstance(doc, dict) or doc.get("number") != number):
            return unknown("gh pr view answered for another PR")
        mapped = map_pr(doc)
        return unknown("PR fields or checks are unrecognised or ambiguous") if mapped == "unknown" else mapped

    def verify(self, item, step):
        base = self.environ.get("KY_TRACKER_URL") or TRACKER_URL
        if not LOOPBACK.match(base) or not isinstance(item, str) or not isinstance(step, str):
            return self._unknown("step detector", "no usable loopback tracker or step identity")
        url = "%s/api/verify?id=%s&step=%s" % (base, urllib.parse.quote(item, safe=""), urllib.parse.quote(step, safe=""))
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(url, timeout=90) as reply:
                doc = _json(reply.read(1 << 20).decode("utf-8"))
        except Exception:                                # unreachable, 404 (a null detector), not JSON
            return self._unknown("step detector", "%s/%s: tracker unavailable or detector null" % (item, step))
        detector = doc.get("detector") if isinstance(doc, dict) else None
        if not isinstance(detector, dict) or doc.get("item") != item or doc.get("step") != step \
                or detector.get("status") not in ("done", "blocked", "pending", "running"):
            return self._unknown("step detector", "%s/%s: no recognised detector bound to this step; an item detector is insufficient"
                                 % (item, step))
        return detector["status"] == "done"

    def veto_status(self):
        import kyveto
        try:
            log = Path(self.run) / "DECISIONS_SURROGATE.jsonl"
            if os.path.lexists(log):
                schema = kyschema.load_json(HERE / "schemas" / "surrogate_decision.json")
                for raw in log.read_text(encoding="utf-8").splitlines():
                    if raw.strip() and kyschema.validate(schema, _json(raw)):
                        return self._unknown("veto status", "the decision log has an unrecognised proposal shape")
            status = kyveto.status(kyveto.Env({"KY_ROOT": self.root, "KY_RUN": self.run, "KY_FLEET": self.fleet,
                                               "KY_SOURCE_REPO": self.repo, "PATH": "/usr/bin:/bin"}))
        except Exception as e:
            return self._unknown("veto status", "producer raised %s" % type(e).__name__)
        if (not isinstance(status, dict) or status.get("schema") != "ky.veto_status/1"
                or not isinstance(status.get("problems"), list) or status["problems"]
                or not isinstance(status.get("decisions"), list)
                or any(not isinstance(r, dict) or not isinstance(r.get("id"), str) or not r["id"] for r in status["decisions"])):
            return self._unknown("veto status", "producer reports unreadable or unrecognised decision records")
        return status

    # ── the instance ──
    def acquire(self):
        rc, out, err = self.sh(["bash", self._script("kylock.sh"), "acquire", ROLE, self.controller_id])
        if rc != 0:
            sys.stderr.write("kydispatch: no instance lock (kylock.sh acquire exit %s): %s\n"
                             % ("unknown" if rc is None else rc, ka.flat(err or out, 300)))
            return EX_NO_LOCK
        self.log("controller %s holds the instance lock" % self.controller_id)
        return EX_OK

    def stop(self):
        """Release the instance lock — only when no job is left that has not ended."""
        try:
            open_jobs = [j["job_id"] for j in J.load(self.ctx) if j["phase"] != "ended"]
        except J.JobsUnreadable as e:
            self.log("stop: the instance lock is kept: %s" % ka.flat(e, 200))
            return False
        if open_jobs:
            self.log("stop: the instance lock is kept for %s" % ", ".join(open_jobs))
            return False
        rc, out, err = self.sh(["bash", self._script("kylock.sh"), "release", ROLE, self.controller_id], timeout=960)
        detail = "kylock.sh release exit %s: %s" % (rc, ka.flat(err or out, 1000) or "no output")
        self.log("stop: " + detail)
        if rc != 0:
            self.journal("dispatcher error", detail)
        return rc == 0

    # ── a tick ──
    def tick(self):
        """→ {"stop": bool, "jobs": [{kind, item, key, pool, decision}]}. An exception is caught and journalled."""
        tracker_before = self.tracker_seen
        self._tick_error = False
        self.seen_now = set()
        self._next = (False, None)
        self._pr_cache = {}
        self._waiting = None
        out = {"stop": False, "jobs": []}
        try:
            out = self._tick()
        except Exception as e:                           # a tick's exception is caught: journal dispatcher error
            self._waiting = "error"
            try:
                self.journal("dispatcher error", "%s: %s" % (type(e).__name__, ka.flat(e, 600)))
            except Exception as again:
                sys.stderr.write("kydispatch: %s; and the journal: %s\n" % (ka.flat(e, 300), ka.flat(again, 300)))
        if self._tick_error:
            self.tracker_seen = tracker_before
            self.tracker_retry = True
            self._next = (False, None)
            self._events_cache = (None, None)
        elif self._next[0] and self._next[1] is not None:
            self.tracker_retry = False
        if not self.dry and not out.get("idle"):
            try:
                self._persist()
            except Exception as e:
                sys.stderr.write("kydispatch: the loop file was not written: %s\n" % ka.flat(e, 300))
            # A fleet-sized gate backlog must never consume a launchable job's log line.
            for job in out["jobs"]:
                if job["decision"] != "wait:gate":
                    self.log("tick job %s" % json.dumps(job, ensure_ascii=False))
            self.log("tick %s" % json.dumps({"waiting": self._waiting,
                "jobs": len(out["jobs"]), "wait:gate": sum(j["decision"] == "wait:gate" for j in out["jobs"])},
                ensure_ascii=False))
        self.seen_before = self.seen_now
        return {"stop": out["stop"], "jobs": out["jobs"]}

    def _persist(self):
        def update(doc):
            doc.update(last_iteration_at=ka.utc(), controller={"id": self.controller_id, "pid": os.getpid()},
                       waiting=self._waiting, log_path=self.log_path, backoff=dict(self.backoff),
                       priority=list(self.priority_cmd), tracker=self.tracker_seen,
                       tracker_retry=self.tracker_retry,
                       conditions={"gate": self.gate_seen, "seen": sorted(self.seen_now)})
            return doc
        kyloop.update_loop_state(self.run, ROLE, update)

    def _stopped(self):
        if os.path.lexists(os.path.join(self.run, "STOP_dispatcher")):
            return True
        loop, err = read_loop(self.run)
        if err:
            self._unknown("loop", err)
            return True
        return not isinstance(loop, dict) or loop.get("enabled") is not True

    def _tick(self):
        ctx = self.ctx
        if self._stopped():                                                    # 1
            return {"stop": True, "jobs": [], "idle": True}
        if not self.dry:
            self._commands()                                                   # 2
            if self._stopped():
                return {"stop": True, "jobs": []}
            self._settle()                                                     # 3
        hold = os.path.lexists(os.path.join(self.root, "HOLD")) or self._owner_paused()
        if hold:                                                               # 4
            self._waiting = "hold"
            if not self.dry:
                return {"stop": False, "jobs": []}
        nxt = ctx.next                                                         # 5
        hold_merges = os.path.lexists(os.path.join(self.run, "HOLD_MERGES"))
        if not self.dry:                                                       # 6
            self._refresh_checkout(hold_merges)
            # Refresh may have moved the model. A changed declaration cannot inherit the earlier reading.
            if nxt is not None:
                self._next = (True, self._declarations(nxt))
                nxt = ctx.next
        rc, _, _ = self.sh(["bash", self._script("kygate.sh")], env={"KY_SOURCE_REPO": self.repo}, timeout=600)
        gate = "OPEN" if rc == 0 else "WAIT"                                   # 7
        if gate != self.gate_seen:
            self.journal("gate change", "%s → %s (kygate.sh exit %s)%s" % (
                self.gate_seen or "not yet read", gate, "unknown" if rc is None else rc,
                "" if gate == "OPEN" else ": only %s* items are admitted" % BOOTSTRAP_PREFIX))
        if not self.dry:
            self.gate_seen = gate
        sizes = {pool: pool_size(os.path.join(self.run, name), default) for pool, (_, name, default) in POOLS.items()}
        for pool, (_, name, _) in POOLS.items():
            if sizes[pool] == 0:
                self.journal("dispatcher error", "%s is not an integer 1–8: no %s capacity" % (
                    os.path.join(self.run, name), pool))
        ctx.limits = {"builders": sizes["builder"], "verifiers": sizes["verifier"], "copies": COPIES}
        ctx.priority = self._priority()
        intents = []
        for module in (L, O, B):                                               # 8
            try:
                intents.extend(module.intents(ctx))
            except Exception as e:
                self.journal("dispatcher error", "%s.intents: %s: %s" % (module.__name__, type(e).__name__, ka.flat(e, 400)))
        for intent in intents:
            if intent["kind"] == "PLAN" and intent["item"] == "WAVE-BOUNDARY":
                self.log("wave boundary awaiting PLAN job (%s); this intent does not prove wave completion" % intent["key"])
        loaded = J.load(ctx)
        bad = list(getattr(ctx, "_job_errors", {}).values())
        active = [j for j in loaded if j["phase"] != "ended"] + bad
        state = {"hold": hold, "gate": gate, "hold_merges": hold_merges, "sizes": sizes, "provisioned": False,
                 "short": set(), "busy": {slot for j in active for slot in (j.get("slot"), j.get("encoded_slot")) if slot},
                 "open_keys": {j["key"] for j in active if j.get("key")},
                 "bad_items": {j["item"] for j in bad if j.get("item")},
                 "unknown_item": any(j.get("unknown_item") for j in bad)}
        jobs = []
        for intent in intents:                                                 # 9
            decision = self._admit(intent, state)
            jobs.append({"kind": intent["kind"], "item": intent["item"], "key": intent["key"],
                         "pool": intent.get("pool"), "decision": decision})
        for pool in sorted(state["short"]):
            if 1 <= sizes[pool] < POOL_MAX:
                ctx.awaiting("capacity-above-max",
                             "Ready %s work is waiting and every one of the %d %s slots is in use. Raise the pool's "
                             "maximum (at most %d)?" % (pool, sizes[pool], pool, POOL_MAX),
                             [dict(o) for o in CAPACITY_OPTIONS], [os.path.join(self.run, POOLS[pool][1])], None, "routine")
        decisions = {j["decision"] for j in jobs}
        self._waiting = self._waiting or ("stale" if nxt is None else "gate" if gate != "OPEN" else
                                          "backoff" if "wait:backoff" in decisions else None)
        return {"stop": False, "jobs": jobs}

    # 2 ── the owner's commands
    def _commands(self):
        try:
            pending = kc.pending(self.run, ROLE)
        except (kc.CommandError, OSError) as e:
            self.journal("dispatcher error", "the command queue cannot be read: %s" % ka.flat(e, 300))
            return
        for doc in pending:
            try:
                status, out = kc.apply(self.run, doc["id"], self.controller_id, self._handle,
                                       observer=lambda record, doc=doc: self._observe_command(doc),
                                       log=lambda text: self.log("command: %s" % text))
            except (kc.CommandError, ka.ActionError, OSError) as e:
                status, out = "refused", {"reason": "%s: %s" % (type(e).__name__, ka.flat(e, 200))}
            self.log("command %s (%s): %s" % (doc["id"], doc.get("command"), status))
            if status in ("refused", "locked", "unreconciled"):                # in order: nothing later is applied
                self.journal("dispatcher error", "command %s (%s) was not applied: %s %s" % (
                    doc["id"], doc.get("command"), status, ka.flat(out.get("reason"), 200)))
                return

    def _pool_file(self, command):
        return os.path.join(self.run, POOLS["builder" if command == "builders" else "verifier"][1])

    def _handle(self, command):
        name = command.get("command")
        args = command.get("args") if isinstance(command.get("args"), dict) else {}
        if name == "status":
            return self._status()
        if name == "loops":
            if args.get("loop") != ROLE:
                raise kc.Reject("not_this_roles_loop: the dispatcher stops only its own loop, not %r" % (args.get("loop"),))
            if args.get("op") != "stop":
                raise kc.Reject("loops_op_not_applicable: a running dispatcher takes `loops stop dispatcher` only")
            ka.write_atomic(os.path.join(self.run, "STOP_dispatcher"),
                            ("%s %s: owner command %s: loops stop dispatcher\n" % (ka.utc(), self.controller_id,
                                                                                  command.get("id"))).encode("utf-8"))
            kyloop.update_loop_state(self.run, ROLE, lambda d: dict(d, enabled=False, disabled_at=ka.utc(),
                                                                    disabled_by_command=command.get("id")))
            return {"loop": ROLE, "enabled": False}
        if name == "priority":
            item = args.get("item")
            if not isinstance(item, str) or not A.ITEM_RE.match(item):
                raise kc.Reject("priority_item_invalid: %r is no item id" % (item,))
            self.priority_cmd = [item] + [p for p in self.priority_cmd if p != item]
            kyloop.update_loop_state(self.run, ROLE, lambda d: dict(d, priority=list(self.priority_cmd)))
            return {"priority": list(self.priority_cmd)}
        if name in ("builders", "verifiers"):
            n = args.get("n")
            if not _is_int(n) or not 1 <= n <= POOL_MAX:
                raise kc.Reject("%s_out_of_range: n must be an integer from 1 to %d" % (name, POOL_MAX))
            ka.write_atomic(self._pool_file(name), ("%d\n" % n).encode("utf-8"))
            return {name: n, "file": self._pool_file(name)}
        raise kc.Reject("unsupported_by_dispatcher: %s" % name)

    def _observe_command(self, command):
        """What an application that died inside its handler left (kyaction.reconcile's form)."""
        name = command.get("command")
        args = command.get("args") if isinstance(command.get("args"), dict) else {}
        loop, err = read_loop(self.run)
        if err:
            self._unknown("command observation", "loop state cannot be read: %s" % err)
            return "unknown", {"reason": "loop state unknown"}
        loop = loop or {}
        if name in ("builders", "verifiers"):
            ok = pool_size(self._pool_file(name), None) == args.get("n")
            return ("done", {name: args.get("n"), "reconciled": True}) if ok else ("not_done", {"file": "not written"})
        if name == "priority":
            ok = (loop.get("priority") or [None])[0] == args.get("item")
            return ("done", {"priority": loop.get("priority"), "reconciled": True}) if ok else ("not_done", {"priority": "not first"})
        if name == "loops" and args.get("op") == "stop" and args.get("loop") == ROLE:
            ok = os.path.lexists(os.path.join(self.run, "STOP_dispatcher")) and loop.get("enabled") is False
            return ("done", {"loop": ROLE, "enabled": False, "reconciled": True}) if ok else ("not_done", {"stop": "not in force"})
        return "not_done", {"reason": "the command has no effect to observe"}

    def _status(self):
        try:
            jobs = [{"job_id": j["job_id"], "kind": j["kind"], "item": j["item"], "slot": j.get("slot"), "phase": j["phase"]}
                    for j in J.load(self.ctx) if j["phase"] != "ended"]
        except J.JobsUnreadable as e:
            jobs = "unknown: %s" % ka.flat(e, 200)
        return {"controller_id": self.controller_id, "pid": os.getpid(), "version": VERSION, "jobs": jobs,
                "gate": self.gate_seen, "backoff": dict(self.backoff), "priority": list(self.priority_cmd),
                "tracker": self.tracker_seen, "log_path": self.log_path,
                "pools": {pool: pool_size(os.path.join(self.run, name), default)
                          for pool, (_, name, default) in POOLS.items()}}

    # 3 ── jobs that ended
    def _settle(self):
        ctx = self.ctx
        for job in J.recover(ctx):
            self._account(job, None)
        for job in J.supervise(ctx):
            result = self._finish(job) if job.get("outcome") is None else None
            self._account(J.close(ctx, job, result), result)

    def _finish(self, job):
        finish = getattr(MODULES.get(job.get("kind")), "finish", None)
        if finish is None:
            return None
        try:
            if job.get("kind") == "SURROGATE" and _is_int(job.get("pid")) and not self._surrogate_proposal_known(job):
                return {"outcome": "interrupted", "detail": "surrogate proposal or its claimed state is unknown",
                        "failure_fp": "surrogate_state_unknown"}
            return finish(self.ctx, job)
        except Exception as e:                           # what the job did is then not known: never done
            self.journal("dispatcher error", "finish of %s (%s %s): %s: %s" % (
                job["job_id"], job.get("kind"), job.get("item"), type(e).__name__, ka.flat(e, 300)))
            return {"outcome": "interrupted", "detail": "its kind's finish raised %s" % type(e).__name__,
                    "failure_fp": "finish_error"}

    def _surrogate_proposal_known(self, job):
        """A proposal can be recorded; model-written EFFECTIVE/EXECUTED never stands in for the handler's action.
        Check before the kind can write a handled marker from that line."""
        import kyveto
        status = self.veto_status()
        if status is None:
            return False
        history, problems, unusable = kyveto.load_decisions(Path(self.run) / "DECISIONS_SURROGATE.jsonl")
        mine = [line for lines in history.values() for line in lines if line.get("awaiting") == job.get("item")
                and line.get("session") == job.get("provider_session_id")]
        if problems or unusable or not mine:
            self._unknown("surrogate proposal", "no recognised decision from the job's provider session")
            return False
        line = mine[-1]
        row = next((r for r in status["decisions"] if r["id"] == line["id"] and r.get("awaiting") == job["item"]), None)
        state = line["state"]
        known = row is not None
        if state in ("EFFECTIVE", "EXECUTED", "VETOED", "FAILED"):
            known = (known and row.get("state") == state and not row.get("anomaly") and not row.get("unresolved")
                     and not row.get("refused") and not row.get("hard_stop"))
            if state in ("EFFECTIVE", "EXECUTED"):
                known = known and row.get("made_effective_by_handler" if state == "EFFECTIVE" else "executed_by_handler") is True
            elif state == "VETOED":
                known = known and bool(row.get("veto_command"))
        if not known:
            self._unknown("surrogate state", "%s claims %s without the handler or owner's matching record" % (line["id"], state))
        return bool(known)

    def _account(self, job, result):
        """Backoff and the surrogate's journal line, for a job that has ended."""
        if not isinstance(job, dict) or job.get("phase") != "ended":
            return
        if job.get("failure_fp") == J.QUOTA:
            if self.backoff.get("job") != job["job_id"]:
                level = min(int(self.backoff.get("level") or 0) + 1, len(BACKOFF_MINUTES))
                minutes = BACKOFF_MINUTES[level - 1]
                until = ka.utc(int(self.clock()) + minutes * 60)
                self.backoff = {"level": level, "until": until, "job": job["job_id"]}
                self.journal("quota backoff", "job %s (%s %s) was refused by the subscription: no model launch for "
                                              "%d min, until %s (step %d of %d); launches resume by themselves"
                             % (job["job_id"], job.get("kind"), job.get("item"), minutes, until, level, len(BACKOFF_MINUTES)))
        elif _is_int(job.get("pid")):                    # a model job that ran and ended without a refusal
            if self.backoff.get("level"):
                self.journal("quota backoff", "ended: job %s ran without a subscription refusal" % job["job_id"])
            self.backoff = dict(NO_BACKOFF)
        if job.get("kind") == "SURROGATE" and job.get("outcome") == "done" and _is_int(job.get("pid")):
            detail = result.get("detail") if isinstance(result, dict) else None
            self.journal("surrogate decision", "%s: %s (job %s)" % (job.get("item"), ka.flat(detail, 400), job["job_id"]))

    def _in_backoff(self):
        if not _is_int(self.backoff.get("level")):
            self._unknown("backoff", "the persisted quota state cannot be read; no model launch")
            return True
        until = ka.parse_utc(self.backoff.get("until"))
        return until is not None and self.clock() < until

    # 4 ── holds
    def _owner_paused(self):
        try:
            paused = kc.owner_paused(self.run)
            if paused not in (True, False) or not isinstance(paused, bool):
                self.journal("dispatcher error", "owner pause unknown: kycommands.owner_paused gave no boolean")
            return paused is not False
        except Exception as e:                           # unknown counts
            self.journal("dispatcher error", "owner pause unknown: %s" % type(e).__name__)
            return True

    def _admission_held(self, state, job=None):
        """Re-read the owner's controls at each admission boundary; a hold latches for the rest of the tick."""
        state["hold"] = (state["hold"] or self.stopping or self._stopped()
                         or os.path.lexists(os.path.join(self.root, "HOLD")) or self._owner_paused())
        if not state["hold"]:
            return False
        self._waiting = "hold"
        if job is not None:
            self._refuse(job, state, "hold", "owner control changed during admission: no start or launch")
        return True

    # 6 ── the campaign checkout
    def _refresh_checkout(self, hold_merges):
        rc, _, err = self.sh(["git", "-C", self.repo, "fetch", "--quiet", "origin"], timeout=300)
        if rc != 0:
            self.journal("dispatcher error", "git fetch in %s: exit %s %s" % (self.repo, rc, ka.flat(err, 200)))
            return
        if hold_merges or os.path.lexists(os.path.join(self.run, "HOLD_MERGES")):
            return
        rc, _, err = self.sh(["git", "-C", self.repo, "merge", "--ff-only", "--quiet", "origin/main"], timeout=300)
        if rc != 0:
            self.journal("dispatcher error", "%s was not fast-forwarded to origin/main: exit %s %s"
                         % (self.repo, rc, ka.flat(err, 200)))

    def _priority(self):
        """Item ids, first first: the owner's priority commands, then $KY_RUN/PRIORITY.txt."""
        out = list(self.priority_cmd)
        try:
            with open(os.path.join(self.run, "PRIORITY.txt"), "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except (OSError, ValueError):
            lines = []
        for line in lines:
            words = line.split("#", 1)[0].split()
            if words and words[0] not in out:
                out.append(words[0])
        return out

    # 9 ── one intent
    def _slot(self, intent, state):
        """A free slot of the intent's pool (never not_slot), a ready database first; None when there is none."""
        pool = intent["pool"]
        prefix = POOLS[pool][0]
        names = ["%s%d" % (prefix, n) for n in range(1, state["sizes"][pool] + 1)]
        free = [s for s in names if s not in state["busy"] and s != intent.get("not_slot")]
        if not free and not [s for s in names if s not in state["busy"]]:
            state["short"].add(pool)                     # the pool itself is used up
        rank = {"own_ready": 0, "absent": 1, "own_not_ready": 1}
        states = {}
        for slot in free:
            status, detail, _ = A.slot_state(self.admit_ctx, slot)
            states[slot] = status
            if status in ("unreadable", "invalid") or status not in ("own_ready", "absent", "own_not_ready", "foreign"):
                self._unknown("slot readiness", "%s: %s" % (slot, ka.flat(detail, 200)))
        return min(free, key=lambda s: (rank.get(states[s], 2), names.index(s))) if free else None

    def _plain(self, intent, for_admit):
        """The intent as kyd_jobs.open and kyd_admit.precheck read it (see INTERPRETATION)."""
        out = dict(intent, locks=[n for n in intent.get("locks") or [] if n != "job.%s" % intent["key"]])
        if for_admit and intent["kind"] in NO_PLAN_ITEM:
            out["item"] = None
        return out

    def _refuse(self, job, state, code, detail):
        closed = J.close(self.ctx, job, {"outcome": "refused", "detail": detail, "failure_fp": code})
        self._freed(closed, state)
        return closed

    def _freed(self, job, state):
        if job.get("phase") == "ended":
            state["busy"].discard(job.get("slot"))
            state["open_keys"].discard(job.get("key"))

    def _handled(self, intent):
        """The kyd_jobs handled record counts only with its ended, done job returned by kyd_jobs.load."""
        path = Path(self.run) / "handled" / ("job.%s.json" % intent["key"])
        if not os.path.lexists(path):
            return False
        try:
            doc = kyschema.load_json(path)
            checkpoint = doc.get("checkpoint") if isinstance(doc, dict) else None
            if (isinstance(doc, dict) and doc.get("schema") == J.HANDLED_SCHEMA and doc.get("id") == "job." + intent["key"]
                    and isinstance(checkpoint, dict) and checkpoint.get("outcome") == "done"):
                for job in J.load(self.ctx):
                    if (job["job_id"] == checkpoint.get("job_id") and job["key"] == intent["key"] and job["phase"] == "ended"
                            and job.get("outcome") == "done" and job["kind"] == intent["kind"] and job["item"] == intent["item"]
                            and all(checkpoint.get(k) == job.get(k) and k in checkpoint for k in
                                    ("item", "kind", "outcome", "head", "digest", "evidence_fp", "result_path"))):
                        return True
        except (OSError, ValueError, J.JobsUnreadable):
            pass
        return self._unknown("handled job", "%s has no matching ended, done job record" % path)

    def _admit(self, intent, state):
        ctx, kind, item, key, pool = self.ctx, intent["kind"], intent["item"], intent["key"], intent.get("pool")
        if self._admission_held(state):
            return "wait:hold"
        if state["gate"] != "OPEN" and not str(item).startswith(BOOTSTRAP_PREFIX):
            return "wait:gate"
        if intent.get("queue") is True and state["hold_merges"]:               # no queue submission of any kind
            if self.dry:
                return "park"
            parked = L.park(ctx, intent)
            if not parked.get("parked"):
                self.journal("dispatcher error", "%s %s was not parked: %s" % (kind, item, ka.flat(parked.get("detail"), 200)))
            return "park" if parked.get("parked") else "refused:park"
        if ctx.next is None:
            return "wait:stale"
        if key in state["open_keys"] or item in state.get("bad_items", set()) or state.get("unknown_item"):
            return "refused:open"
        handled = self._handled(intent)
        if handled is None:
            return "wait:stale"
        if handled:
            return "refused:open"
        if J.attempts(ctx, intent)["blocked"]:
            return "refused:attempts"
        model = intent.get("runner") == "model"
        if model and self._in_backoff():
            return "wait:backoff"
        slot = None
        if pool is not None:
            slot = self._slot(intent, state) if pool in POOLS else None
            if slot is None:
                return "wait:slot"
        check = A.precheck(self.admit_ctx, self._plain(intent, True), slot)
        if self._admission_held(state):
            return "wait:hold"
        if not check["admitted"]:
            codes = [r["code"] for r in check["refusals"]]
            for refusal in check["refusals"]:
                if refusal["code"] == "ceiling":
                    self.journal("ceiling hit", "%s %s: %s" % (kind, item, refusal["detail"]))
            if set(codes) <= set(SLOT_CODES):                                  # only its slot database is missing
                state["busy"].add(slot)
                if not self.dry and not state["provisioned"]:
                    state["provisioned"] = True                                # one slot a tick
                    provision = A.provision(self.admit_ctx, slot)
                    if not provision["admitted"]:
                        detail = "; ".join(r["detail"] for r in provision["refusals"])
                        self.journal("dispatcher error", "%s %s slot %s: %s" % (kind, item, slot, detail))
                        if self._admission_held(state):
                            return "wait:hold"
                        # (I) INTERPRETATION: retain wait:slot, with the failed helper's reason;
                        # no job was opened and a later changed condition may make the slot ready.
                        return "wait:slot (%s)" % ka.flat(detail, 1000)
                    if self._admission_held(state):
                        return "wait:hold"
                return "wait:slot"
            code = next(c for c in codes if c not in SLOT_CODES)
            if self.dry:
                detail = "; ".join(r["detail"] for r in check["refusals"] if r["code"] == code)
                sys.stderr.write("kydispatch: [refused] %s %s: %s: %s\n" % (kind, item, code, ka.flat(detail, 1000)))
            return "wait:stale" if code == "stale" else "refused:%s" % code
        if self.dry:
            if slot is not None:
                state["busy"].add(slot)
            return "launch"
        if self._admission_held(state):
            return "wait:hold"
        job = J.open(ctx, self._plain(intent, False), slot, check["facts"])
        if job is None:
            return "refused:open"
        state["open_keys"].add(key)
        if slot is not None:
            state["busy"].add(slot)
        if self._admission_held(state, job):
            return "wait:hold"
        admitted = A.admit(_View(self.admit_ctx, controller_id=job_lock_owner(self.controller_id, key)), job)
        if self._admission_held(state, job):
            return "wait:hold"
        if not admitted["admitted"]:
            first = admitted["refusals"][0]
            self._refuse(job, state, "admit_%s" % first["code"], "admit: %s: %s" % (first["code"], first["detail"]))
            return "refused:%s" % first["code"]
        self._pr_cache.clear()                           # the kind's start looks afresh
        try:
            result = MODULES[kind].start(ctx, job)
        except Exception as e:
            self.journal("dispatcher error", "start of %s (%s %s): %s: %s" % (job["job_id"], kind, item,
                                                                             type(e).__name__, ka.flat(e, 300)))
            result = {"outcome": "refused", "detail": "its kind's start raised %s" % type(e).__name__,
                      "failure_fp": "start_error"}
        if result is None and model:
            if self._admission_held(state, job):
                return "wait:hold"
            job = J.launch(ctx, job)
            if job["phase"] == "live":
                return "launch"
            self._refuse(job, state, "launch", "the job was not started")
            return "refused:launch"
        if not isinstance(result, dict):
            result = {"outcome": "refused", "detail": "a script job's start gave no result", "failure_fp": "start_no_result"}
        closed = J.close(ctx, job, result)
        self._freed(closed, state)
        self._account(closed, result)
        return "refused:start" if closed.get("outcome") == "refused" else "launch"


# ───────────────────────────────────────── command line ─────────────────────────────────────────

def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv not in ([], ["--once"], ["--dry"]):
        sys.stderr.write(USAGE + "\n")
        return EX_USAGE
    names = kyloop.credential_names(os.environ)
    if names:                                            # names only: a value is never read or printed
        sys.stderr.write("kydispatch: credential variable name(s) set: %s; the dispatcher does not run with them\n"
                         % ", ".join(names))
        return EX_CREDENTIAL
    problem = paths_problem(os.environ)
    if problem:
        sys.stderr.write("kydispatch: %s\n%s\n" % (problem, USAGE))
        return EX_USAGE
    dry, once = argv == ["--dry"], argv == ["--once"]
    engine = Engine(os.environ, dry=dry)
    if dry:
        plan = engine.tick()
        sys.stdout.write(json.dumps({"schema": PLAN_SCHEMA, "jobs": plan["jobs"]}, ensure_ascii=False) + "\n")
        return EX_OK
    rc = engine.acquire()
    if rc != EX_OK:
        return rc

    def asked_to_stop(signum, frame):
        engine.stopping = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, asked_to_stop)
    try:
        while True:
            if engine.tick()["stop"] or once or engine.stopping:
                break
            end = time.monotonic() + TICK_S
            while not engine.stopping and time.monotonic() < end:
                time.sleep(0.5)
    finally:
        engine.stop()
    return EX_OK


if __name__ == "__main__":
    sys.exit(main())
