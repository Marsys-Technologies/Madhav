#!/usr/bin/env python3
"""kydispatch.py — the dispatcher engine of KĀLA-YANTRA v3 (relaunch plan v2.7 §4 "Capacity", §6 "The dispatcher";
packet KV3-B-KYDISPATCH v1).

version: 1.0 · status: DRAFT (built under the hold; not installed, not merged by its job)
changelog: 1.0 (2026-10-12) first version, packet PACKET_KV3-B-KYDISPATCH_v1.

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
  * A job of the intent's key that has not ended, or its handled record, is `refused:open` without calling J.open
    (J.open's own fresh look would refuse it; nothing is claimed for it).
  * Pool sizes: the integer 1–8 in $KY_RUN/KY_WORKERS / KY_VERIFIERS; absent → 6 / 4; anything else → 0 (no
    capacity is never guessed). limits.copies = 10. Ready work that finds every slot of its pool in use raises
    ctx.awaiting("capacity-above-max", …) while the pool is below 8.
  * Backoff: a job that ended with failure_fp `quota` steps 5 → 10 → 20 → 30 min (once per job) and no model
    runner is launched before `until`; a model job that ended without it resets the steps.
  * Fresh on the first reading of a run directory (no `tracker` record yet): there is nothing to compare with.
  * ctx.pr: `gh pr list --head kalayantra/<item>` lists open pull requests (gh's default), so "no open PR" is None.
    A check's `attempt` is the number in its detailsUrl and null when the URL names none (never assumed 1). Two
    entries of one name: the later one stands.
  * ctx.verify: GET <tracker>/api/verify?id=<item>&step=<step> on loopback (KY_TRACKER_URL, default
    http://127.0.0.1:8767). True only for a reply that names this item AND this step with detector.status `done`;
    False for another status of that step; None for anything else — a reply that does not name the step is a
    tracker answering for the item's own detector, and None never permits `ky step`.
  * ctx.events: the item's lines of EVENTS.jsonl; a line that is not a JSON object makes the whole log unknown
    (None) for this reading — it may be anybody's review or verdict.
  * ctx.act: kyaction's record around one effect. effect() may answer (done | failed | unknown, result) — then
    that is recorded — or a plain result object (kyd_kinds_land, kyd_kinds_ops): then the observer says whether
    it is done; an effect that raises is recorded failed.
  * Journal lines and their notifications are written once per changed condition: a line identical to one of the
    previous tick is not repeated.
  * `surrogate decision` is journalled when a SURROGATE model job ends done; `wave complete` when the PLAN kind
    intends the wave boundary; `gate change` when kygate.sh's answer differs from the last tick's.
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
    A refusal after J.open carries a failure class (`admit_<code>`, the kind's own, `launch`), so that the third
    identical one blocks automatic attempts (kyd_jobs' failure accounting) instead of claiming every tick.
Python >= 3.9, standard library only.
"""
from __future__ import annotations

import hashlib
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
COPIES = 10
BACKOFF_MINUTES = (5, 10, 20, 30)
BOOTSTRAP_PREFIX = "KV3-B-"
NO_PLAN_ITEM = ("RULING", "SURROGATE", "PLAN")      # kinds whose intent names no item of the plan model
SLOT_CODES = ("slot_not_ready", "slot_foreign")
SH_ENV = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR")
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
        else:                                                              # a CheckRun
            status, url = entry.get("status"), entry.get("detailsUrl")
            if status == "COMPLETED" and isinstance(entry.get("conclusion"), str) and entry["conclusion"]:
                status = entry["conclusion"]
        found = RUN_URL.search(url) if isinstance(url, str) else None
        checks[name] = {"status": status.upper() if isinstance(status, str) else None,
                        "run_id": int(found.group(1)) if found else None,
                        "attempt": int(found.group(2)) if found and found.group(2) else None}
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
        loop, _ = kyloop.loop_state(self.run, ROLE)
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
        self.ctx = Ctx(self)
        self.admit_ctx = _View(self.ctx, now=lambda: int(self.clock()))

    def _adopt(self, loop):
        """This engine's own keys of the loop file, as an earlier controller left them."""
        backoff = loop.get("backoff")
        if isinstance(backoff, dict) and _is_int(backoff.get("level")) and 0 <= backoff["level"] <= len(BACKOFF_MINUTES):
            self.backoff = {"level": backoff["level"], "until": backoff.get("until"), "job": backoff.get("job")}
        priority = loop.get("priority")
        self.priority_cmd = [p for p in priority if isinstance(p, str) and p] if isinstance(priority, list) else []
        tracker = loop.get("tracker")
        self.tracker_seen = tracker if isinstance(tracker, dict) and _is_int(tracker.get("version")) else None
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
            result = {"result": ka.flat(result, 300)}
        if outcome == "done":
            ka.complete(self.run, action_id, result)
        elif outcome == "failed":
            ka.fail(self.run, action_id, result)
        return outcome, result

    # ── messaging ──
    def journal(self, event, text):
        """One line of $KY_RUN/JOURNAL_DISPATCHER.md — and, for the plan's quoted events, one notification — per
        changed condition: a line the previous tick already wrote is not written again."""
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
            return ("done" if rc == 0 else "unknown" if rc is None else "failed"), \
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
            doc, _ = ka.read_json(path)
            if isinstance(doc, dict) and doc.get("id") == path.stem and doc.get("question") == question \
                    and not path.with_name(path.stem + kyloop.OWNER_DECISION_SUFFIX).exists():
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
        rc, out, _ = self.ky("next", "--json")
        try:
            nxt = json.loads(out) if rc == 0 else None
        except (ValueError, RecursionError):
            nxt = None
        now = self._events_signature()
        value = nxt if fresh(nxt, self.tracker_seen, now) else None
        if value is not None:
            self.tracker_seen = dict(now or {"events_size": None, "events_sha256": None}, version=nxt["version"])
        self._next = (True, value)
        return value

    def _all_events(self):
        path = os.path.join(self.run, "EVENTS.jsonl")
        try:
            st = os.stat(path)
        except OSError:
            return None
        signature = (st.st_size, st.st_mtime_ns)
        if self._events_cache[0] == signature:
            return self._events_cache[1]
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("not an object")
                    events.append(event)
        except (OSError, ValueError, RecursionError):
            events = None
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
        events = self.events(item)
        if events is None or not isinstance(item, str):
            return "unknown"
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
            return "unknown"
        try:
            doc = json.loads(out)
        except (ValueError, RecursionError):
            return "unknown"
        if number is None:
            if not isinstance(doc, list):
                return "unknown"
            if not doc:
                return None
            doc = doc[0]
        return map_pr(doc)

    def verify(self, item, step):
        base = self.environ.get("KY_TRACKER_URL") or TRACKER_URL
        if not LOOPBACK.match(base) or not isinstance(item, str) or not isinstance(step, str):
            return None
        url = "%s/api/verify?id=%s&step=%s" % (base, urllib.parse.quote(item, safe=""), urllib.parse.quote(step, safe=""))
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(url, timeout=90) as reply:
                doc = json.loads(reply.read(1 << 20).decode("utf-8"))
        except Exception:                                # unreachable, 404 (a null detector), not JSON
            return None
        detector = doc.get("detector") if isinstance(doc, dict) else None
        if not isinstance(detector, dict) or doc.get("item") != item or doc.get("step") != step \
                or not isinstance(detector.get("status"), str):
            return None
        return detector["status"] == "done"

    def veto_status(self):
        import kyveto
        return kyveto.status(kyveto.Env({"KY_ROOT": self.root, "KY_RUN": self.run, "KY_FLEET": self.fleet,
                                         "KY_SOURCE_REPO": self.repo, "PATH": "/usr/bin:/bin"}))

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
        self.log("stop: kylock.sh release exit %s %s" % (rc, ka.flat(err, 200)))
        return rc == 0

    # ── a tick ──
    def tick(self):
        """→ {"stop": bool, "jobs": [{kind, item, key, pool, decision}]}. An exception is caught and journalled."""
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
        if not self.dry and not out.get("idle"):
            try:
                self._persist()
            except Exception as e:
                sys.stderr.write("kydispatch: the loop file was not written: %s\n" % ka.flat(e, 300))
            self.log("tick %s" % json.dumps({"waiting": self._waiting, "jobs": out["jobs"]}, ensure_ascii=False))
        self.seen_before = self.seen_now
        return {"stop": out["stop"], "jobs": out["jobs"]}

    def _persist(self):
        def update(doc):
            doc.update(last_iteration_at=ka.utc(), controller={"id": self.controller_id, "pid": os.getpid()},
                       waiting=self._waiting, log_path=self.log_path, backoff=dict(self.backoff),
                       priority=list(self.priority_cmd), tracker=self.tracker_seen,
                       conditions={"gate": self.gate_seen, "seen": sorted(self.seen_now)})
            return doc
        kyloop.update_loop_state(self.run, ROLE, update)

    def _stopped(self):
        if os.path.lexists(os.path.join(self.run, "STOP_dispatcher")):
            return True
        loop, _ = kyloop.loop_state(self.run, ROLE)
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
                self.journal("wave complete", "no item is ready, in review or running admitted; a PLAN job is "
                                              "intended for the boundary (%s)" % intent["key"])
        state = {"hold": hold, "gate": gate, "hold_merges": hold_merges, "sizes": sizes, "provisioned": False,
                 "short": set(), "busy": {j["slot"] for j in J.load(ctx) if j["phase"] != "ended" and j.get("slot")},
                 "open_keys": {j["key"] for j in J.load(ctx) if j["phase"] != "ended"}}
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
        loop, _ = kyloop.loop_state(self.run, ROLE)
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
            return finish(self.ctx, job)
        except Exception as e:                           # what the job did is then not known: never done
            self.journal("dispatcher error", "finish of %s (%s %s): %s: %s" % (
                job["job_id"], job.get("kind"), job.get("item"), type(e).__name__, ka.flat(e, 300)))
            return {"outcome": "interrupted", "detail": "its kind's finish raised %s" % type(e).__name__,
                    "failure_fp": "finish_error"}

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
        until = ka.parse_utc(self.backoff.get("until"))
        return until is not None and self.clock() < until

    # 4 ── holds
    def _owner_paused(self):
        try:
            return kc.owner_paused(self.run) is True
        except Exception:                                # unknown counts
            return True

    # 6 ── the campaign checkout
    def _refresh_checkout(self, hold_merges):
        rc, _, err = self.sh(["git", "-C", self.repo, "fetch", "--quiet", "origin"], timeout=300)
        if rc != 0:
            self.journal("dispatcher error", "git fetch in %s: exit %s %s" % (self.repo, rc, ka.flat(err, 200)))
            return
        if hold_merges:
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
        return min(free, key=lambda s: (rank.get(A.slot_state(self.admit_ctx, s)[0], 2), names.index(s))) if free else None

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

    def _admit(self, intent, state):
        ctx, kind, item, key, pool = self.ctx, intent["kind"], intent["item"], intent["key"], intent.get("pool")
        if state["hold"]:
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
        if key in state["open_keys"] or os.path.lexists(os.path.join(self.run, "handled", "job.%s.json" % key)):
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
        if not check["admitted"]:
            codes = [r["code"] for r in check["refusals"]]
            for refusal in check["refusals"]:
                if refusal["code"] == "ceiling":
                    self.journal("ceiling hit", "%s %s: %s" % (kind, item, refusal["detail"]))
            if set(codes) <= set(SLOT_CODES):                                  # only its slot database is missing
                state["busy"].add(slot)
                if not self.dry and not state["provisioned"]:
                    state["provisioned"] = True                                # one slot a tick
                    A.provision(self.admit_ctx, slot)
                return "wait:slot"
            code = next(c for c in codes if c not in SLOT_CODES)
            return "wait:stale" if code == "stale" else "refused:%s" % code
        if self.dry:
            if slot is not None:
                state["busy"].add(slot)
            return "launch"
        job = J.open(ctx, self._plain(intent, False), slot, check["facts"])
        if job is None:
            return "refused:open"
        state["open_keys"].add(key)
        if slot is not None:
            state["busy"].add(slot)
        admitted = A.admit(_View(self.admit_ctx, controller_id=job_lock_owner(self.controller_id, key)), job)
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
