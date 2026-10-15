#!/usr/bin/env python3
"""kyd_jobs.py — the dispatcher's job lifecycle for KĀLA-YANTRA v3 (relaunch plan v2.7 §5 "Job and dispatcher I/O
(KT-08)", §6 "Claims, locks, renewals", "Terminal release (KT-07)", "Failure accounting"; packet KV3-B-KYDJOBS v1).

A module of the dispatcher engine (kydispatch.py); it has no command line. The engine hands in `ctx`:
    ctx.root, ctx.run, ctx.fleet, ctx.scratch, ctx.repo        absolute paths ($KY_ROOT, $KY_RUN, $KY_FLEET, …)
    ctx.controller_id
    ctx.sh(argv, env=None, cwd=None, timeout=120) → (rc, out, err)        rc None: unknown
    ctx.ky(*args, stream=None, lane=None) → (rc, out, err)
    ctx.act(id, kind, inputs, target, effect, observer) → (done | failed | unknown, result)   kyaction's record
    ctx.awaiting(slug, question, options, evidence, item, class_hint)
    ctx.journal(event, text)

    load(ctx)                      readable job states, oldest first; bad folders quarantined in memory
    attempts(ctx, intent)          {"attempt", "blocked"} from $KY_RUN/jobs/failures.json and the ended jobs
    open(ctx, intent, slot, facts) a prepared job, or None with everything undone
    launch(ctx, job)               the job as it is afterwards: phase "live" when it was started
    supervise(ctx)                 the jobs of this controller that are terminating (their close is owed)
    recover(ctx)                   the jobs of an earlier controller this call closed or adopted
    close(ctx, job, result=None)   the job as it is afterwards: phase "ended", or still "terminating" when a
                                   step could not be finished (an owner-wait says why; call it again)

Job state: $KY_RUN/jobs/<job_id>/state.json, schema ky.job/1, exactly LAUNCH_KEYS + LIFECYCLE_KEYS (+ "schema");
every path absolute, an unset key null. phase prepared → live → terminating → ended; outcome done | blocked |
failed | interrupted | timed_out | refused. Time keys (deadline, renewed_at, ended_at) are UTC text
YYYY-MM-DDTHH:MM:SSZ; any other form is unknown and refuses: no job is opened or started with such a deadline,
and a live job whose time keys cannot be read is neither timed out nor renewed (an owner-wait instead).

What "gone" means (kyloop.job_state): the leader is positively gone AND its process group is empty. "unknown"
and "survivors" are never gone: such a job is not finished or released. Claude survivors and unknown
identities are held; known Codex groups remain subject to persisted silence and deadline supervision.
A signal goes only to the group of a job this module started as its own group leader (pgid == pid), and only
while that leader still runs with its recorded start identity, or has left members in that very group.

close — the KT-07 paragraph in its order; each step is persisted (checkpoint.steps) before the next, so a new
controller resumes at the first unfinished one:
    result     outcome, failure_fp, checkpoint; the failure is counted (once per job); phase terminating
    exited     the recorded process group is gone (a job that was never started has none)
    boundary   a boundary verifier's view: `bash fleet/kyboundary.sh release <job_id>` must exit 0
    claim      a held tracker claim: $KY_RUN/claims/<slot>.json must name this job's item, worker and claim_id
               before `ky release` (which releases whatever that file names). Already released for this
               claim_id → nothing is released again. Anything else → no release, the slot stays unavailable,
               owner-wait "reconciliation required".
    locks      the job's locks[] and its job lock — only a lock that is provably this job's (see below)
    handled    outcome done: $KY_RUN/handled/job.<key>.json
    ended      phase ended, ended_at — only now is the slot free (open refuses a slot whose job has not ended)
The steps from `claim` on run under the lock slot.<slot>, which open holds while it looks, claims and writes.

INTERPRETATION (packet (I) and what the packet leaves open; each is this module's reading, not the plan's text):
  * job_id = J-<UTC yyyymmddThhmmssZ>-<slot, else kind in lower case>[.<n>]; the job folder is created WITH its
    state by one exclusive rename, and a scratch folder of that name that already exists is never reused.
  * work worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item, lower case> on branch
    kalayantra/<same> for a job holding item.<item>, added at the job's base_sha when absent; else ctx.repo.
  * the handled record after a done job; blocked at count ≥ 3 with an unchanged evidence_fp.
  * ctx.act: effect() → (done | failed | unknown, result object); observer(record) → kyaction's observer answer.
    Used for the launch (ACT-launch-<job_id>), the claim (ACT-claim-<job_id>) and the release
    (ACT-release-<job_id>); a renewal is repeated freely and has no record.
  * claim_id "pending" is persisted before `ky claim`, as pid "pending" is before the start: a job closed in
    that state reads the claim file — an active claim of its own item and slot is its own (the slot had no other
    job) and is released; no such claim means none was made.
  * renewed_at is set when the claim is made (the lease runs from then) and at every renewal.
  * attempt = 1 + the failures counted for the item (all classes; quota never counted). failures.json entries
    carry last_job beside count and evidence_fp, so that a restart between counting and persisting counts once.
  * requeued: true for the first interrupted job of a key, false for a later one, null otherwise.
  * outcome when close is given none and the controller recorded none: quota → failed; never started → refused;
    else interrupted (plan §6 table: "else interrupted"; §6 recovery: gone → interrupted, re-queue once). The
    job's own result.json is never an outcome — only the kind's finish, which checks what it asserts, says done.
  * a job's locks are bound to the job: their owner id is "<controller_id>:job.<key>" (one job of a key is
    not ended at a time), so another job's lock of the same name never reads as this job's. From the moment the
    job exists its locks record it as their `child` (job_id and state path, no process identity), so kyaction
    reads them as unknown whatever became of the controller and never takes them over while the job is not ended
    (review KYDJOBS-R2-B1); only the job's own close, or its adoption, re-owns such a lock in place (under
    kyaction's takeover guard, and only from an owner that is this process or positively gone). Its locks step keeps a
    ledger (checkpoint.lock_release, name → releasing | released, persisted before and after each release): a
    lock found held by another owner was released by this job when the ledger says releasing, and is left
    alone; one never released by this job and held by another owner is an owner-wait.
  * a header key that is a launch key overrides the fact — except the keys this module determines itself
    (PROTECTED: identity, paths, locks, boundary).
  * a job action record (JOB-<job_id>-*) left INTENDED is settled when the job is first seen gone, by supervise
    as well as by recover: git_push by `git ls-remote` in the job's worktree, anything else unknown → one
    owner-wait per record, never retried (kyloop.py reconcile_job_record).
  * a terminating job whose process still runs (a close handed a live job) is not signalled before its deadline;
    past it supervise reaps its group as at any timeout.
  * supervise returns every terminating job of this controller, also one whose close stopped at a step earlier:
    `outcome` non-null on a returned job is the controller's own finding (timed_out, refused, interrupted, or an
    earlier close); null means the job ended by itself and its kind's finish decides.
  * an owner-wait is raised once per job and reason (checkpoint.awaiting remembers).
Changelog: v1.1 (2026-10-13): optional Codex selection, collection, landing and silence timeout.
Fix B1 (2026-10-13): recover known Codex groups, including pending termination; retain persisted clocks/fences.
Fix WB-01-R (2026-10-13): state-first native identity; retain malformed legacy reservations.
Python >= 3.9, standard library only; kyaction.py, kyloop.py, kyschema.py and schemas/ beside this file.
"""
from __future__ import annotations

import calendar
import fcntl
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kyaction as ka  # noqa: E402
import kyloop  # noqa: E402
import kyschema  # noqa: E402
import kyjob_engines as engines  # noqa: E402

SCHEMA = "ky.job/1"
RESULT_SCHEMA = "ky.job_result/1"
HANDLED_SCHEMA = "ky.handled/1"
LAUNCH_KEYS = ("job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase "
               "evidence_fp pr registered_head queue_authorised prerequisites test_digests migration_number loop "
               "max_loops model effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags "
               "disallowed_tools job_scratch prompt_path stdout_path stderr_path tmp_path tests se_ephe_path "
               "swe_ephe_path card_path packet_path boundary regen fixture locks controller_id").split()
LIFECYCLE_KEYS = ("phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome "
                  "result_path result_event checkpoint failure_fp attempt requeued ended_at").split()
PHASES = ("prepared", "live", "terminating", "ended")
OUTCOMES = ("done", "blocked", "failed", "interrupted", "timed_out", "refused")
CLOSE_STEPS = ("result", "exited", "boundary", "claim", "locks", "handled", "ended")
LIST_KEYS = ("prerequisites", "test_digests", "extra_lean_flags", "disallowed_tools", "tests", "locks")
PATH_KEYS = ("worktree", "claude_bin", "mcp_config", "card_path", "packet_path", "se_ephe_path", "swe_ephe_path")
LAUNCH_FACTS = ("model", "effort", "permission_mode", "max_turns", "deadline", "claude_bin", "mcp_config",
                "extra_lean_flags", "disallowed_tools")                 # facts.launch → the keys of the same name
INTENT_KEYS = ("head", "digest", "verdict_phase", "evidence_fp")
PROTECTED = ("job_id", "key", "item", "kind", "role", "stream", "slot", "worktree", "job_scratch", "prompt_path",
             "stdout_path", "stderr_path", "tmp_path", "card_path", "packet_path", "boundary", "locks",
             "controller_id")                                           # never taken from an intent's header
WORKTREES = "/Users/Dev/worktrees.noindex/madhav/claude"
LEASE_S = 10800
RENEW_S = 1200
TERM_WAIT_S = 10.0
KILL_WAIT_S = 5.0
FAILURE_LIMIT = 3
INTERRUPT_LIMIT = 2
QUOTA = "quota"
TAKEOVER_GUARD = ".takeover.guard"      # kyaction's guard in $KY_RUN/locks: a re-owning never meets a takeover
PENDING = "pending"
RESULT_MAX_BYTES = 1 << 20
HEADER_LINE = b"--- job header ---\n"
OPTIONS = [{"id": "reconciled", "text": "Checked by hand and put right; the controller may look again."},
           {"id": "investigate", "text": "Leave it as it is; someone looks into it first."}]

_TIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
_KIND = re.compile(r"^[A-Z][A-Z-]{0,31}\Z")
_ITEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_SLOT = re.compile(r"^[a-z][a-z0-9]{0,15}\Z")
_JOB_ID = re.compile(r"^J-([0-9]{8}T[0-9]{6}Z)-([a-z][a-z0-9-]*)(?:\.([0-9]+))?\Z")
_LEGACY = re.compile(r"^legacy-([0-9]+)\Z")
_CHILDREN = {}                  # job_id → Popen of a job THIS process started (its exit code; nobody else's)
_RESULT_SCHEMA = []


class JobsUnreadable(Exception):
    """An individual job state, jobs directory or failure table cannot be read."""


# ───────────────────────────────────────── small helpers ─────────────────────────────────────────

def _now():
    return time.time()


def _stamp(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_now() if t is None else t))


def _when(text):
    """Epoch seconds of a time key in its one form, else None (unknown)."""
    if not isinstance(text, str) or not _TIME.match(text):
        return None
    try:
        return calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return None


def _slug(text):
    return re.sub(r"[^a-z0-9-]", "-", str(text).lower())


def _run(ctx):
    return Path(str(ctx.run))


def _fleet(ctx):
    return Path(str(ctx.fleet))


def _state_path(ctx, job_id):
    return _run(ctx) / "jobs" / job_id / "state.json"


def _save(ctx, job):
    ka.write_json(_state_path(ctx, job["job_id"]), job)


def _text(value):
    return isinstance(value, str) and bool(value)


def _act(ctx, job, action_id, kind, inputs, target, effect, observer):
    """Annotate controller-owned Codex records; Claude's record bytes retain their shape."""
    if job.get("engine") != "codex":
        return ctx.act(action_id, kind, inputs, target, effect, observer)
    meta = engines.metadata(job)

    def annotated(fn, *args, observing=False):
        try:
            status, detail = fn(*args)
        except engines.Hold as exc:
            status, detail = "unknown", {"reason": str(exc)}
        except engines.Refusal as exc:
            status, detail = ("unknown" if observing else "failed"), {"reason": str(exc)}
        return status, dict(detail, **meta)

    return ctx.act(action_id, kind, dict(inputs, **meta), dict(target, **meta),
                   lambda: annotated(effect), lambda record: annotated(observer, record, observing=True))


def _real_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ───────────────────────────────────────── load ─────────────────────────────────────────

def _checked(doc, err, name):
    if err or not isinstance(doc, dict):
        raise JobsUnreadable("job %s: state.json is %s" % (name, err or "not an object"))
    if doc.get("schema") != SCHEMA:
        raise JobsUnreadable("job %s: schema is not %s" % (name, SCHEMA))
    if doc.get("job_id") != name:
        raise JobsUnreadable("job %s: its state names job_id %r" % (name, doc.get("job_id")))
    if doc.get("phase") not in PHASES:
        raise JobsUnreadable("job %s: phase %r is not one of %s" % (name, doc.get("phase"), ", ".join(PHASES)))
    for key in ("key", "item", "kind", "slot", "controller_id"):
        if doc.get(key) is not None and not _text(doc[key]):
            raise JobsUnreadable("job %s: %s must be nonempty text or null" % (name, key))
    for key in LIST_KEYS:
        if doc.get(key) is not None and not isinstance(doc[key], list):
            raise JobsUnreadable("job %s: %s must be a list or null" % (name, key))
    for key in LAUNCH_KEYS + LIFECYCLE_KEYS:
        doc.setdefault(key, None)
    return doc


def _age(job_id):
    m = _LEGACY.match(job_id)
    if m:
        return 0, "", "", int(m.group(1)), job_id
    m = _JOB_ID.match(job_id)
    if m:
        return 1, m.group(1), m.group(2), int(m.group(3) or 1), job_id
    return 2, "", "", 0, job_id


def job_folders(directory):
    """The shared jobs-directory rule: ledger files and staging directories are not jobs."""
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return []
    return [n for n in names if not n.startswith(".") and os.path.isdir(Path(directory) / n)]


def foreign_state(doc, err):
    """Positive quarantine identity, shared by every dispatcher job-state reader."""
    return (not err and isinstance(doc, dict)
            and (doc.get("schema") in ("ky.bootstrap_job_state/3", "ky.legacy_job_state/1")
                 or ("schema" not in doc and doc.get("launcher") == "cockpit-direct")))


def load(ctx):
    """Readable jobs, oldest first. Only positively foreign bad folders are quarantined.
    Unknown native states retain their folder-encoded slot and identifiable slot/key/item reservations;
    they are neither supervised nor recovered, and their bytes are never moved or rewritten.
    (I) INTERPRETATION: if the item cannot be identified, all item admissions wait for reconciliation.
    (I) INTERPRETATION: an unidentified non-J folder or unrecognized schema is not positively foreign;
    retain readable reservations, or refuse all admissions when the item cannot be bounded.
    A schema-less cockpit-direct record is foreign by its launcher marker (launch_direct.py:85).
    A repair is read on the next call; one notice per folder per context.
    Directory-listing and failure-table errors remain fatal because their scope is not one job.
    """
    directory = _run(ctx) / "jobs"
    ctx._job_errors = {}
    try:
        names = job_folders(directory)
    except OSError as e:
        raise JobsUnreadable("%s cannot be listed (%s)" % (directory, type(e).__name__)) from None
    jobs = []
    seen = getattr(ctx, "_job_quarantine_seen", None)
    if seen is None:
        seen = ctx._job_quarantine_seen = set()
    for name in names:
        if name.startswith(".") or not os.path.isdir(directory / name):
            continue                                     # failures.json, a state being created
        doc, err = ka.read_json(directory / name / "state.json")
        try:
            jobs.append(_checked(doc, err, name))
        except JobsUnreadable as exc:
            encoded = _JOB_ID.match(name)
            schema = doc.get("schema") if isinstance(doc, dict) else None
            # State identity × folder form × defect decision table (checked before naming heuristics):
            # STATE IDENTITY                 J-<UTC>-<slot>[.n]     legacy-N / any other folder
            # ky.job/1, valid                load                  load
            # ky.job/1, ANY field defect     native error          native error
            # ky.bootstrap_job_state/3      quarantine            quarantine (even with field defects)
            # ky.legacy_job_state/1         quarantine            quarantine (even with field defects)
            # schema ABSENT + launcher      quarantine            quarantine (even with field defects)
            #   == cockpit-direct
            # NO identity: missing state,   native error          unidentified error (I: conservative)
            # unreadable JSON/I/O, non-object,
            # absent/null/invalid schema,
            # or an unrecognized named schema
            # A ky.job/1 schema wins over a launcher marker. A present schema (even null) prevents
            # the schema-less marker fallback. Only the two recognized foreign schemas are proof.
            # Every error retains each readable declared slot/key/item; J names additionally reserve
            # their encoded slot, even if the declared slot is null, missing, invalid or different.
            # An unidentified item blocks all admissions. Errors/quarantines get one notice per folder;
            # neither is supervised/recovered and neither changes bytes. Tests enumerate all rows,
            # both naming columns (legacy and arbitrary separately), and every _checked field defect.
            native = not err and isinstance(doc, dict) and schema == SCHEMA
            foreign = foreign_state(doc, err)
            if not foreign:
                reservation = {k: doc.get(k) for k in ("slot", "key", "item")
                               if isinstance(doc, dict) and _text(doc.get(k))}
                if encoded:
                    reservation["encoded_slot"] = encoded.group(2)
                    reservation.setdefault("slot", encoded.group(2))
                reservation["unknown_item"] = not _text(reservation.get("item"))
                ctx._job_errors[name] = reservation
            if name not in seen:
                ctx.journal("job quarantine" if foreign else "dispatcher error", str(exc))
                seen.add(name)
    return sorted(jobs, key=lambda j: _age(j["job_id"]))


def _fresh(ctx, job):
    name = job["job_id"]
    doc, err = ka.read_json(_state_path(ctx, name))
    return _checked(doc, err, name)


# ───────────────────────────────────────── owner-waits ─────────────────────────────────────────

def _checkpoint(job):
    cp = job.get("checkpoint")
    if not isinstance(cp, dict):
        cp = job["checkpoint"] = {}
    cp.setdefault("steps", {})
    cp.setdefault("awaiting", [])
    if job.get("engine") == "codex":
        cp.update(engines.metadata(job))
    return cp


def _await(ctx, job, tag, question, evidence=()):
    """One owner-wait per job and reason."""
    raised = _checkpoint(job)["awaiting"]
    if tag in raised:
        return
    ctx.awaiting("job-%s-%s" % (_slug(job["job_id"]), tag),
                 "Job %s (%s %s%s): %s" % (job["job_id"], job.get("kind"), job.get("item"),
                                           ", slot %s" % job["slot"] if job.get("slot") else "", question),
                 [dict(o) for o in OPTIONS], [str(_state_path(ctx, job["job_id"]))] + [str(e) for e in evidence],
                 job.get("item"), "unknown")
    raised.append(tag)
    _save(ctx, job)


def _await_process(ctx, job, state):
    _await(ctx, job, "process-%s" % state,
           "its process (pid %r, group %r, started %r) is %s — %s. It is not finished, not signalled and "
           "nothing it holds is released. What became of it?"
           % (job.get("pid"), job.get("pgid"), job.get("process_start"), state,
              {"unknown": "whether it still runs cannot be told",
               "survivors": "its leader has exited and its process group still has members",
               "live": "it still runs"}.get(state, "its state is not one this controller acts on")))


def _await_pending(ctx, job):
    _await(ctx, job, "launch-pending",
           "its start was recorded as pending and never completed: whether a process exists is unknown. It is "
           "never started again and never taken to be gone. Does a process of this job exist?")


# ───────────────────────────────────────── locks ─────────────────────────────────────────

def _owner(controller_id, key):
    """The owner id of a job's locks: its controller and its key (one job of a key is not ended at a time)."""
    return "%s:job.%s" % (controller_id, key)


def _take(ctx, name, owner=None):
    """The lock, or None when it is held or its owner cannot be judged (journalled; never taken over then).
    `owner`: a job's owner id (_owner); a controller's own short-lived lock (slot.<slot>) is taken as itself."""
    try:
        lock = ka.acquire_lock(_run(ctx), name, owner or ctx.controller_id,
                               log=lambda text: ctx.journal("lock", text))
    except ka.ActionError as e:
        ctx.journal("lock", ka.flat(e, 300))
        return None
    return lock


def _lock_holder(ctx, name):
    """("free", None) · ("owned", owner record) · ("unknown", None)."""
    owner, err = ka.lock_owner(_run(ctx), name)
    if owner is not None:
        return "owned", owner
    if err == "missing" and not os.path.lexists(ka.lock_path(_run(ctx), name)):
        return "free", None
    return "unknown", None


def _child(ctx, job):
    """What each lock of a job that is not ended records as its `child`: the job, with no process identity. kyaction
    reads such a lock as unknown once its owner is gone, and never takes it over."""
    return {"job_id": job["job_id"], "state": str(_state_path(ctx, job["job_id"])), "pid": None, "pgid": None,
            "process_start": None}


def _rehome(ctx, job, name, child):
    """Hold one lock of this job under this controller by rewriting its owner record in place: this process, the
    owner id _owner(controller_id, key) and `child`. Only a lock whose owner id is this job's and whose recorded
    owner is this process or positively gone; under kyaction's takeover guard. → True / False."""
    path, mine, ident = ka.lock_path(_run(ctx), name), _owner(ctx.controller_id, job["key"]), ka.self_identity()
    if ident["process_start"] is None:
        return False                                     # an owner nobody could judge is never written
    try:
        guard = os.open(str(path.parent / TAKEOVER_GUARD), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return False
    try:
        fcntl.flock(guard, fcntl.LOCK_EX)
        owner, _ = ka.lock_owner(_run(ctx), name)
        if owner is None or owner.get("session_or_run_id") not in (_owner(job.get("controller_id"), job["key"]), mine):
            return False
        if owner.get("pid") != os.getpid() and ka.process_matches(owner.get("pid"), owner.get("process_start")) is not False:
            return False                                 # a live owner, or one that cannot be judged, keeps it
        ka.write_json(path / "owner.json", dict(owner, session_or_run_id=mine, child=child, **ident))
        return True
    except OSError:
        return False
    finally:
        os.close(guard)


def _drop(ctx, job, name, ledger):
    """Release one lock of this job. True: this job does not hold it (any more). False: it is held by an owner that
    is not this job although this job never released it, or its owner cannot be judged, or it could not be
    removed. `ledger` (checkpoint.lock_release) is marked "releasing" and persisted only once the lock is shown
    to be this job's, before it is removed; a lock of another owner found after that mark is one taken since —
    never touched. A lock this job's controller left behind, positively gone, is re-owned in place (its child
    names this job, so kyaction would never take it over) and then released."""
    state, owner = _lock_holder(ctx, name)
    if state == "free":
        return True
    if state != "owned":
        return False
    mine = _owner(ctx.controller_id, job["key"])
    if owner.get("session_or_run_id") not in (_owner(job.get("controller_id"), job["key"]), mine):
        return ledger.get(name) == "releasing"
    if ledger.get(name) != "releasing":
        ledger[name] = "releasing"
        _save(ctx, job)
    if owner.get("pid") == os.getpid():
        return ka.release_lock(ka.Lock(ka.lock_path(_run(ctx), name), owner["session_or_run_id"]))
    return _rehome(ctx, job, name, None) and ka.release_lock(ka.Lock(ka.lock_path(_run(ctx), name), mine))


def _own(ctx, job, name):
    """Hold one lock of an adopted job under this controller, still naming the job as its child. → True / False."""
    state, _ = _lock_holder(ctx, name)
    if state == "free" and _take(ctx, name, _owner(ctx.controller_id, job["key"])) is None:
        return False
    return state != "unknown" and _rehome(ctx, job, name, _child(ctx, job))


# ───────────────────────────────────────── failure accounting ─────────────────────────────────────────

def _failures(ctx):
    table, err = ka.read_json(_run(ctx) / "jobs" / "failures.json")
    if err == "missing":
        return {}
    if err or not isinstance(table, dict) or not all(
            isinstance(fps, dict) and all(isinstance(e, dict) and _real_int(e.get("count")) for e in fps.values())
            for fps in table.values()):
        raise JobsUnreadable("failures.json is %s" % (err or "not {item: {failure_fp: {count, evidence_fp}}}"))
    return table


def _interrupted(jobs, key, but=None):
    return [j for j in jobs if j["phase"] == "ended" and j.get("outcome") == "interrupted" and j.get("key") == key
            and j.get("failure_fp") != QUOTA and j["job_id"] != but]


def attempts(ctx, intent):
    """{"attempt": n, "blocked": bool}: n = 1 + the failures counted for the item (never reset; quota never
    counted). Blocked: a failure class counted FAILURE_LIMIT times whose evidence_fp is still the intent's, or
    INTERRUPT_LIMIT interrupted jobs of the intent's key."""
    entries = _failures(ctx).get(intent["item"], {})
    evidence = intent.get("evidence_fp")
    blocked = any(e["count"] >= FAILURE_LIMIT and e.get("evidence_fp") == evidence for e in entries.values()) \
        or len(_interrupted(load(ctx), intent["key"])) >= INTERRUPT_LIMIT
    return {"attempt": 1 + sum(e["count"] for e in entries.values()), "blocked": blocked}


def _account(ctx, job):
    """Count this job's failure class, once per job."""
    fp = job.get("failure_fp")
    if job.get("outcome") == "done" or not _text(fp) or fp == QUOTA:
        return
    table = _failures(ctx)
    entry = table.setdefault(job["item"], {}).setdefault(fp, {"count": 0, "evidence_fp": None, "last_job": None})
    if entry.get("last_job") == job["job_id"]:
        return
    entry.update(count=entry["count"] + 1, evidence_fp=job.get("evidence_fp"), last_job=job["job_id"])
    if job.get("engine") == "codex":
        entry.update(engines.metadata(job))
    os.makedirs(_run(ctx) / "jobs", exist_ok=True)
    ka.write_json(_run(ctx) / "jobs" / "failures.json", table)


# ───────────────────────────────────────── open ─────────────────────────────────────────

def _plan(ctx, intent, slot, facts):
    """(plan, None) — the job state as far as it can be said before anything is touched — or (None, reason)."""
    if not isinstance(intent, dict) or not isinstance(facts, dict):
        return None, "intent and facts must be objects"
    kind, item, key = intent.get("kind"), intent.get("item"), intent.get("key")
    if not (_text(kind) and _KIND.match(kind)):
        return None, "intent.kind %r is not a kind" % (kind,)
    if not (_text(item) and _ITEM.match(item)):
        return None, "intent.item %r is not an item id" % (item,)
    if not (_text(key) and ka.LOCK_RE.match("job." + key)):
        return None, "intent.key %r cannot name a job lock" % (key,)
    if slot is not None and not (_text(slot) and _SLOT.match(slot)):
        return None, "slot %r is not a slot name" % (slot,)
    header, launch = intent.get("header") or {}, facts.get("launch") or {}
    if not isinstance(header, dict) or not isinstance(launch, dict):
        return None, "intent.header and facts.launch must be objects"
    managed_codex = launch.get("codex_config")
    if managed_codex is not None:
        for k in LAUNCH_FACTS + engines.FIELDS + ("role",):
            if k in header and header[k] != launch.get(k):
                return None, "header cannot override admitted Codex %s" % k
    if intent.get("claim") and slot is None:
        return None, "a claiming job needs a slot (the claim's worker)"
    state = dict.fromkeys(["schema"] + LAUNCH_KEYS + LIFECYCLE_KEYS)
    state.update(schema=SCHEMA, key=key, item=item, kind=kind,
                 role=launch.get("role") if managed_codex is not None else intent.get("role") or kind.lower(),
                 stream=intent.get("stream"), slot=slot, base_sha=facts.get("base_sha"),
                 prerequisites=facts.get("prerequisites"), tests=facts.get("tests"),
                 test_digests=facts.get("test_digests"), card_path=intent.get("card"),
                 packet_path=intent.get("packet"), locks=intent.get("locks"),
                 boundary="verifier" if intent.get("pool") == "verifier" else None,
                 controller_id=ctx.controller_id, phase="prepared")
    state.update({k: intent.get(k) for k in INTENT_KEYS})
    state.update({k: launch.get(k) for k in LAUNCH_FACTS})
    state.update({k: v for k, v in header.items() if k in LAUNCH_KEYS and k not in PROTECTED})
    # Optional fields are kept only when provided: legacy Claude state/prompt bytes stay unchanged.
    choices = {k: launch[k] for k in engines.FIELDS if k in launch}
    choices.update({k: header[k] for k in engines.FIELDS if k in header})
    try:
        engines.selection(dict(state, **choices))
    except engines.Refusal as exc:
        return None, str(exc)
    state.update(choices)
    if state.get("engine") == "codex":
        if kind in engines.READ_ONLY_KINDS - {"VERIFY"}:
            state["boundary"] = "verifier"
        state.setdefault("sandbox_mode", "locked")
        state.setdefault("stall_seconds", 300)
        state.update(engines.metadata(state))
    for k in LIST_KEYS:
        state[k] = [] if state[k] is None else state[k]
        if not isinstance(state[k], list):
            return None, "%s must be a list" % k
        state[k] = list(state[k])
    if not all(_text(n) and ka.LOCK_RE.match(n) for n in state["locks"]):
        return None, "intent.locks holds something that cannot name a lock"
    if "item.%s" % item in state["locks"]:
        state["worktree"] = "%s/kalayantra-%s" % (WORKTREES, item.lower())
        state["branch"] = state["branch"] or "kalayantra/%s" % item.lower()
    else:
        state["worktree"] = str(ctx.repo)
    for k in PATH_KEYS:
        if state[k] is not None and not (_text(state[k]) and os.path.isabs(state[k])):
            return None, "%s %r is not an absolute path" % (k, state[k])
    if state["deadline"] is not None and _when(state["deadline"]) is None:
        return None, "deadline %r is not UTC text YYYY-MM-DDTHH:MM:SSZ: unknown" % (state["deadline"],)
    texts = {}
    for k in ("card_path", "packet_path"):
        try:
            texts[k] = Path(state[k]).read_bytes() if state[k] is not None else b""
        except OSError as e:
            return None, "%s %s cannot be read (%s)" % (k, state[k], type(e).__name__)
    plan = {"state": state, "claim": bool(intent.get("claim")), "texts": texts, "added_worktree": False,
            "migration": facts.get("migration") is not None and "migration_number" not in header,
            "header": {k: v for k, v in header.items() if k not in PROTECTED}}
    if managed_codex is not None:
        plan.update(codex_config=managed_codex, codex_config_sha256=launch.get("codex_config_sha256"))
    return plan, None


def _look(ctx, key, slot, item=None):
    """The fresh look under the job lock → why nothing is opened, or None."""
    if os.path.lexists(_run(ctx) / "handled" / ("job.%s.json" % key)):
        return "key %s is handled" % key
    for job in load(ctx):
        if job["phase"] != "ended" and job.get("key") == key:
            return "job %s of key %s has not ended" % (job["job_id"], key)
        if job["phase"] != "ended" and slot is not None and job.get("slot") == slot:
            return "slot %s is not free: job %s has not ended" % (slot, job["job_id"])
    for name, job in ctx._job_errors.items():
        if (job.get("key") == key or (slot is not None and slot in (job.get("slot"), job.get("encoded_slot")))
                or job.get("unknown_item") or (item is not None and job.get("item") == item)):
            return "job %s has an unknown or malformed state; its item/key/slot requires reconciliation" % name
    return None


def _reserve(ctx, state):
    """Create the job: its scratch folder (prompt, logs, tmp) and — by one exclusive rename — its folder under
    $KY_RUN/jobs together with its state. → the job."""
    jobs, scratch_root = _run(ctx) / "jobs", Path(str(ctx.scratch)) / "jobs"
    os.makedirs(jobs, exist_ok=True)
    os.makedirs(scratch_root, exist_ok=True)
    base = "J-%s-%s" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(_now())), state["slot"] or state["kind"].lower())
    for n in range(1, 1000):
        job_id = base if n == 1 else "%s.%d" % (base, n)
        scratch = scratch_root / job_id
        if os.path.lexists(jobs / job_id):
            continue
        try:
            os.mkdir(scratch)
        except FileExistsError:
            continue
        job = dict(state, job_id=job_id, job_scratch=str(scratch), prompt_path=str(scratch / "prompt.md"),
                   stdout_path=str(scratch / "stdout.jsonl"), stderr_path=str(scratch / "stderr.log"),
                   tmp_path=str(scratch / "tmp"))
        os.mkdir(scratch / "tmp")
        for k in ("prompt_path", "stdout_path", "stderr_path"):
            io.open(job[k], "xb").close()
        staging = jobs / (".%s.new.%d" % (job_id, os.getpid()))
        os.mkdir(staging)
        ka.write_json(staging / "state.json", job)
        try:
            ka.rename_exclusive(staging, jobs / job_id)
        except FileExistsError:
            os.unlink(staging / "state.json")
            os.rmdir(staging)
            for k in ("prompt_path", "stdout_path", "stderr_path"):
                os.unlink(job[k])
            os.rmdir(scratch / "tmp")
            os.rmdir(scratch)
            continue
        return job
    raise JobsUnreadable("no free job id of the form %s[.<n>]" % base)


def _claim_id(out):
    """The claim_id `ky claim` printed (its event, one JSON object), or None."""
    for line in reversed(str(out or "").splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and _text(event.get("claim_id")):
            return event["claim_id"]
    return None


def _claims_path(ctx, job):
    return _run(ctx) / "claims" / ("%s.json" % job["slot"])


def _claim(ctx, job):
    """`ky claim` under an action record → why the job cannot go on, or None."""
    job["claim_id"] = PENDING
    _save(ctx, job)

    def effect():
        rc, out, err = ctx.ky("claim", job["item"], "--worker", job["slot"], "--lease", str(LEASE_S),
                              stream=job["stream"], lane=job["slot"])
        if rc == 0 and _claim_id(out):
            return "done", {"claim_id": _claim_id(out)}
        if rc is None or rc == 0:
            return "unknown", {"rc": rc, "reason": "ky claim did not say whether a claim was made"}
        return "failed", {"rc": rc, "stderr": ka.flat(err, 300)}

    outcome, result = _act(ctx, job, "ACT-claim-%s" % job["job_id"], "ky_claim",
                              {"item": job["item"], "worker": job["slot"], "lease_s": LEASE_S},
                              {"claims": str(_claims_path(ctx, job))}, effect,
                              lambda record: ("unknown", {"reason": "a claim is reconciled from the claim file"}))
    if outcome == "done":
        job.update(claim_id=result["claim_id"], renewed_at=_stamp())
        _save(ctx, job)
        return None
    if outcome == "failed":
        job["claim_id"] = None                           # positively refused: nothing is held
        _save(ctx, job)
    return "ky claim %s for slot %s: %s (%s)" % (job["item"], job["slot"], outcome, ka.flat(result, 200))


def _worktree(ctx, job, plan):
    if "item.%s" % job["item"] not in job["locks"] or os.path.isdir(job["worktree"]):
        return None
    repo, path, branch = str(ctx.repo), job["worktree"], job["branch"]
    if not _text(job["base_sha"]) or not _text(branch):
        return "the work worktree %s is absent and there is no base_sha or branch to add it at" % path
    rc, _, _ = ctx.sh(["git", "-C", repo, "rev-parse", "--verify", "--quiet", "refs/heads/%s" % branch])
    if rc not in (0, 1):
        return "whether branch %s exists cannot be told (git rev-parse rc=%r)" % (branch, rc)
    argv = ["git", "-C", repo, "worktree", "add"] + ([path, branch] if rc == 0 else ["-b", branch, path, job["base_sha"]])
    rc, _, err = ctx.sh(argv)
    if rc != 0 or not os.path.isdir(path):
        return "git worktree add %s: rc=%r %s" % (path, rc, ka.flat(err, 200))
    plan["added_worktree"] = True
    return None


def _migration(ctx, job, plan):
    if not plan["migration"]:
        return None
    if not _text(job["branch"]):
        return "a migration number is reserved by item and branch; this job has no branch"
    rc, out, err = ctx.sh(["python3", "-I", "-B", str(_fleet(ctx) / "kyalloc.py"), "reserve", "--item", job["item"],
                           "--branch", job["branch"], "--repo", str(ctx.repo)])
    try:
        numbers = json.loads(out).get("numbers") if rc == 0 else None
    except (ValueError, AttributeError, TypeError):
        numbers = None
    if not isinstance(numbers, list) or not numbers or not _real_int(numbers[0]):
        return "kyalloc.py reserve: rc=%r %s" % (rc, ka.flat(err, 200))
    job["migration_number"] = numbers[0]
    return None


def _prompt(job, plan):
    """card bytes, packet bytes, the header line, one JSON object (plan §7 header fields, then the intent's)."""
    header = dict(plan["header"])
    if job.get("engine") == "codex":
        header.update({k: job[k] for k in engines.FIELDS})
        header.update(engines.metadata(job))
    header.update({"job_id": job["job_id"], "item": job["item"], "kind": job["kind"], "slot": job["slot"],
                   "worktree": job["worktree"], "branch": job["branch"], "base_sha": job["base_sha"],
                   "prerequisite_heads": job["prerequisites"], "migration_number": job["migration_number"],
                   "loop": job["loop"], "max_loops": job["max_loops"], "deadline": job["deadline"],
                   "job_scratch": job["job_scratch"], "result_path": job["job_scratch"] + "/result.json"})
    parts = []
    for k in ("card_path", "packet_path"):
        data = plan["texts"][k]
        parts.append(data + (b"" if not data or data.endswith(b"\n") else b"\n"))
    parts.append(HEADER_LINE + json.dumps(header, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    ka.write_atomic(job["prompt_path"], b"".join(parts))


def _codex_config(job, plan):
    """Adapt the qualification template only at its per-job worktree/prompt paths.

    (I) Optional environment names must equal the qualified variant; never trim tests.
    Ephemeris/fixture environments still need a dedicated reviewed qualification.
    """
    cfg = plan.get("codex_config")
    if cfg is None:  # Preserve the accepted caller-supplied engine adapter path.
        return
    if engines.digest(job["launch_config_path"]) != plan["codex_config_sha256"]:
        raise engines.Refusal("Codex template changed after admission")
    if (bool(job.get("tests")) != ("TESTS" in cfg["env_names"])
            or job.get("se_ephe_path") is not None or job.get("swe_ephe_path") is not None or job.get("fixture")):
        raise engines.Refusal("Codex role template does not qualify optional TESTS/ephemeris/fixture environment")
    adapted = dict(cfg, worktree=job["worktree"], prompt_path=job["prompt_path"], role=job["role"])
    job["launch_config_path"] = os.path.join(job["job_scratch"], "launch_config.json")
    ka.write_json(job["launch_config_path"], adapted)


def _prepare(ctx, job, plan):
    """Everything open does after the job exists → why it cannot be a prepared job, or None."""
    try:
        why = _claim(ctx, job) if plan["claim"] else None
        why = why or _worktree(ctx, job, plan) or _migration(ctx, job, plan)
        if why is None:
            if job.get("engine") == "codex":
                _codex_config(job, plan)
            _prompt(job, plan)
            if job.get("engine") == "codex":
                engines.prepare(ctx, job)
            _save(ctx, job)
    except (OSError, ka.ActionError, engines.Refusal) as e:
        why = "%s: %s" % (type(e).__name__, ka.flat(e, 200))
    if why is not None and plan["added_worktree"]:
        rc, _, err = ctx.sh(["git", "-C", str(ctx.repo), "worktree", "remove", job["worktree"]])
        if rc != 0:
            ctx.journal("job not opened", "the worktree %s added for it was not removed: rc=%r %s"
                        % (job["worktree"], rc, ka.flat(err, 200)))
    return why


def open(ctx, intent, slot, facts):                      # noqa: A001 — the packet's name; io.open is used here
    """A prepared job for `intent` on `slot` (None: a job without a slot), or None with everything undone: the
    locks free again, a claim that was made released, a worktree that was added removed. A job that existed by
    then is closed `refused` (its record stays; where that close cannot finish — a claim that cannot be shown
    released — the slot stays unavailable and an owner-wait says so)."""
    plan, why = _plan(ctx, intent, slot, facts)
    if plan is None:
        ctx.journal("job not opened", "%s %s: %s" % (intent.get("kind") if isinstance(intent, dict) else None,
                                                     intent.get("item") if isinstance(intent, dict) else None, why))
        return None
    load(ctx)                                            # an unreadable job state: nothing is opened on top of it
    plan["state"]["attempt"] = attempts(ctx, intent)["attempt"]
    key = plan["state"]["key"]
    held, slot_lock, job = [], None, None
    lock = _take(ctx, "job.%s" % key, _owner(ctx.controller_id, key))
    if lock is None:
        return None
    held.append(lock)
    try:
        why = _look(ctx, key, slot, plan["state"]["item"])
        if why is None and slot is not None:
            slot_lock = _take(ctx, "slot.%s" % slot)
            why = None if slot_lock is not None else "slot %s is being released or opened" % slot
        if why is None:
            for name in plan["state"]["locks"]:
                lock = _take(ctx, name, _owner(ctx.controller_id, key))
                if lock is None:
                    why = "lock %s is held" % name
                    break
                held.append(lock)
        if why is None:
            try:
                job = _reserve(ctx, plan["state"])
            except OSError as e:
                why = "the job could not be written (%s: %s)" % (type(e).__name__, ka.flat(e, 200))
        if job is not None:                              # from now on its locks name it: never taken over
            unmarked = [lk.path.name for lk in held if not _rehome(ctx, job, lk.path.name, _child(ctx, job))]
            why = "lock(s) %s could not record the job" % ", ".join(unmarked) if unmarked else _prepare(ctx, job, plan)
            if why is not None:
                _close(ctx, job, {"outcome": "refused", "detail": "open: %s" % why, "failure_fp": None})
                held, job = [], None                     # that close released what the job held, or keeps it
        if why is not None:
            for lock in reversed(held):
                ka.release_lock(lock)
            ctx.journal("job not opened", "%s %s on %s: %s" % (intent["kind"], intent["item"], slot, why))
        return job
    finally:
        if slot_lock is not None:
            ka.release_lock(slot_lock)


# ───────────────────────────────────────── launch ─────────────────────────────────────────

def _identity(pid):
    for _ in range(5):
        seen = kyloop.ps_identity(pid)
        if seen is not None:
            return seen[1]
        time.sleep(0.02)
    return None


def launch(ctx, job):
    """Start the job: `/bin/bash <fleet>/kyjob.sh <job_id>` as the leader of a new session, under the action
    record ACT-launch-<job_id>. pid "pending" is persisted before the start; pid, pgid, process_start and phase
    live after it. → the job as it is afterwards; anything but phase "live" means it was not started here.
    A job found "pending" is never started again."""
    job = _fresh(ctx, job)
    if job["phase"] != "prepared":
        return job
    if job["pid"] is not None:
        _await_pending(ctx, job)
        return job
    if _when(job["deadline"]) is None:
        ctx.journal("job not started", "%s: deadline %r is not UTC text YYYY-MM-DDTHH:MM:SSZ: unknown"
                    % (job["job_id"], job["deadline"]))
        return job
    argv = ["/bin/bash", str(_fleet(ctx) / "kyjob.sh"), job["job_id"]]
    meta = engines.metadata(job) if job.get("engine") == "codex" else {}

    def effect():
        if job.get("engine") == "codex":
            engines.prepare(ctx, job)
            engines.stalled(job, _now())
        job["pid"] = PENDING
        _save(ctx, job)
        env = {k: os.environ[k] for k in ("HOME", "USER", "LANG", "TERM", "PATH") if k in os.environ}
        env.update(KY_ROOT=str(ctx.root), KY_RUN=str(ctx.run), KY_FLEET=str(ctx.fleet), KY_SCRATCH=str(ctx.scratch))
        try:
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, start_new_session=True, env=env,
                                     cwd=str(ctx.root))
        except (OSError, ValueError) as e:
            job["pid"] = None                            # positively not started
            _save(ctx, job)
            return "failed", {"error": "%s: %s" % (type(e).__name__, ka.flat(e, 200))}
        _CHILDREN[job["job_id"]] = child
        job.update(pid=child.pid, pgid=child.pid, process_start=_identity(child.pid), phase="live")
        _save(ctx, job)
        return "done", dict(pid=job["pid"], pgid=job["pgid"], process_start=job["process_start"], **meta)

    def observer(record):
        seen = _fresh(ctx, job)
        if _real_int(seen["pid"]):
            return "done", dict(pid=seen["pid"], pgid=seen["pgid"], process_start=seen["process_start"], **meta)
        if seen["pid"] is None:
            return "not_done", {"pid": None}
        return "unknown", {"pid": seen["pid"]}

    try:
        outcome, result = _act(ctx, job, "ACT-launch-%s" % job["job_id"], "launch", dict(job_id=job["job_id"], argv=argv, **meta),
                                  dict(state=str(_state_path(ctx, job["job_id"])), **meta), effect, observer)
    except ka.ActionError as e:                          # the record, not the start: the state says what happened
        outcome, result = "unknown", {"error": "%s: %s" % (type(e).__name__, ka.flat(e, 200))}
    if outcome != "done":
        ctx.journal("job not started", "%s: %s (%s)" % (job["job_id"], outcome, ka.flat(result, 200)))
    job = _fresh(ctx, job)
    if job["phase"] == "prepared" and job["pid"] is not None:
        _await_pending(ctx, job)
    return job


# ───────────────────────────────────────── what a finished job left ─────────────────────────────────────────

def _result_schema():
    if not _RESULT_SCHEMA:
        try:
            _RESULT_SCHEMA.append(kyschema.load_json(HERE / "schemas" / "job_result.json"))
        except ValueError:
            _RESULT_SCHEMA.append(None)
    return _RESULT_SCHEMA[0]


def _result(job):
    """The job's own result.json when it is a regular file (never a symbolic link), valid as ky.job_result/1 and
    naming this job and item; else None."""
    try:
        schema = engines.result_schema(job) if job.get("engine") == "codex" else _result_schema()
    except (OSError, ValueError):
        return None
    path = os.path.join(job["job_scratch"], "result.json")
    if schema is None:
        return None
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with io.open(fd, "rb") as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                return None
            data = f.read(RESULT_MAX_BYTES + 1)
        if len(data) > RESULT_MAX_BYTES:
            return None
        doc = kyschema.load_json_text(data.decode("utf-8"))
        if kyschema.validate(schema, doc):
            return None
    except (OSError, ValueError, RecursionError):
        return None
    return doc if doc["job_id"] == job["job_id"] and doc["item"] == job["item"] else None


def read_result(job):
    """Shared strict result reader for controller finish/recovery; no symlink or schema compatibility fallback."""
    if (not isinstance(job, dict) or not _text(job.get("job_id")) or not _text(job.get("item"))
            or not _text(job.get("job_scratch")) or not os.path.isabs(job["job_scratch"])):
        return None
    return _result(job)


def record_registration(ctx, job, doc, source=None):
    """Persist only identities whose registration the kind observed, before claim release.

    (I) INTERPRETATION: recovery is a recorded changed condition, clearing only no_post_action at the source
    evidence fingerprint. Other failure classes and the original ended jobs remain as history.
    """
    job["result_path"] = os.path.join((source or job)["job_scratch"], "result.json")
    if doc["status"] == "done":
        job.update(head=doc["head_sha"], pr=doc["pr_number"], registered_head=doc["head_sha"])
    if source:
        _checkpoint(job)["review_recovery"] = {"job_id": source["job_id"], "evidence_fp": source.get("evidence_fp"),
                                                "head": doc["head_sha"], "pr": doc["pr_number"]}
    _save(ctx, job)
    if source:
        clear_review_failure(ctx, job)


def clear_review_failure(ctx, job):
    """Idempotent after a persisted, observed recovery registration, including a restart during close."""
    recovery = _checkpoint(job).get("review_recovery")
    if not isinstance(recovery, dict):
        return
    table = _failures(ctx)
    entry = table.get(job["item"], {}).get("no_post_action")
    if isinstance(entry, dict) and entry.get("evidence_fp") == recovery.get("evidence_fp"):
        del table[job["item"]]["no_post_action"]
        ka.write_json(_run(ctx) / "jobs" / "failures.json", table)


def _result_event(path):
    """subtype / is_error / num_turns / usage of the last stream `result` event (as kyboot.py records it), or None."""
    last = None
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except (ValueError, RecursionError):
                    continue
                if isinstance(event, dict) and event.get("type") == "result":
                    last = event
    except OSError:
        return None
    return None if last is None else {k: last.get(k) for k in ("subtype", "is_error", "num_turns", "usage")}


def _reap(job):
    """Collect the job's leader if this process started it and it has exited → its exit code, else None."""
    child = _CHILDREN.get(job["job_id"])
    return child.poll() if child is not None else None


def _process(job):
    _reap(job)
    return kyloop.job_state(job.get("pid"), job.get("pgid"), job.get("process_start"))


def _observe_push(ctx, job, record):
    """kyaction observer for a job's `git_push` (kyloop.py observe_git_push, in this job's worktree)."""
    inputs = record.get("inputs") if isinstance(record.get("inputs"), dict) else {}
    target = record.get("target") if isinstance(record.get("target"), dict) else {}

    def named(key):
        value = inputs.get(key, target.get(key))
        return value if isinstance(value, str) else None

    remote, ref, commit, repo = named("remote"), named("ref"), named("commit"), named("repo")
    if ref and not ref.startswith("refs/"):
        ref = "refs/heads/" + ref
    if not (remote and kyloop.GIT_REMOTE_RE.match(remote) and ref and kyloop.GIT_REF_RE.match(ref)
            and ".." not in ref and commit and kyloop.HEX_COMMIT.match(commit)):
        return "unknown", {"reason": "the record does not name a remote, a ref and a full commit id"}
    worktree = job.get("worktree")
    if not _text(worktree) or not os.path.isdir(worktree):
        return "unknown", {"reason": "the job's worktree is not known"}
    if repo is not None and os.path.realpath(repo) != os.path.realpath(worktree):
        return "unknown", {"reason": "the record names another repository than the job's worktree"}
    rc, out, _ = ctx.sh(["git", "-C", worktree, "ls-remote", remote, ref], timeout=120)
    if rc != 0:
        return "unknown", {"reason": "git ls-remote rc=%r" % (rc,)}
    at = [parts[0] for parts in (line.split() for line in str(out).splitlines()) if len(parts) == 2 and parts[1] == ref]
    if at == [commit]:
        return "done", {"remote": remote, "ref": ref, "commit": commit, "observed_by": "git ls-remote",
                        "reconciled": True}
    return "not_done", {"remote": remote, "ref": ref, "intended": commit, "observed": at[0] if at else None}


def _settle(ctx, job):
    """The JOB-<job_id>-* action records the job left INTENDED, as kyloop.py settles them: an observer's "done"
    → DONE; "not_done" → FAILED; no observer, or it cannot tell → recorded unknown, one owner-wait, no retry."""
    run = _run(ctx)
    try:
        records = ka.job_records(run, job["job_id"], state="INTENDED")
    except (ka.ActionError, OSError) as e:
        ctx.journal("job actions", "%s: not read (%s)" % (job["job_id"], type(e).__name__))
        return
    for rec in records:
        aid, kind = rec["action_id"], str(rec.get("kind"))
        raised = any(isinstance(x, dict) and x.get("outcome") == "unknown" for x in rec.get("reconciliations") or [])
        observer = (lambda r: _observe_push(ctx, job, r)) if kind == "git_push" else \
            (lambda r: ("unknown", {"reason": "no observer for kind %r" % kind}))
        try:
            outcome, after = ka.reconcile(run, aid, observer, by=ctx.controller_id)
            detail = (after.get("reconciliations") or [{}])[-1].get("detail")
            if outcome == "not_done":
                ka.fail(run, aid, dict(detail if isinstance(detail, dict) else {"observed": detail},
                                       reconciled=True, reason="the side effect was not observed"))
        except (ka.ActionError, OSError) as e:
            ctx.journal("job actions", "%s not reconciled (%s: %s)" % (aid, type(e).__name__, ka.flat(e, 160)))
            continue
        if outcome == "unknown" and not raised:
            why = detail.get("reason") if isinstance(detail, dict) else None
            ctx.awaiting("job-action-%s" % _slug(aid),
                         "Job %s recorded the intention of a side effect (action %s, kind %s) and exited without "
                         "recording its result; the controller cannot observe what became of it (%s). It is not "
                         "retried. Did it happen?" % (job["job_id"], aid, kind, ka.flat(why, 160) or "unknown"),
                         [{"id": "happened", "text": "It happened: settle the record as done."},
                          {"id": "did-not-happen", "text": "It did not happen: settle the record as failed; the "
                                                           "next job may do it under its own record."}],
                         [str(run / "actions" / (aid + ".json"))], job.get("item"), "unknown")


def _collect(ctx, job):
    """What a job whose group is gone left behind, into its state (not saved here)."""
    child = _CHILDREN.pop(job["job_id"], None)
    job["exit_code"] = child.poll() if child is not None else None       # null for a job this process adopted
    job["result_path"] = os.path.join(job["job_scratch"], "result.json") if _result(job) is not None else None
    if job.get("engine") == "codex":
        job["provider_session_id"] = job.get("provider_session_id") or engines.boot.first_thread_id(job["stdout_path"])
        job["result_event"] = engines.boot.final_codex_turn(job["stdout_path"])
    else:
        job["provider_session_id"] = job.get("provider_session_id") or kyloop.provider_session(job["stdout_path"])
        job["result_event"] = _result_event(job["stdout_path"])
    refusal = os.path.join(job["job_scratch"], "kyjob.refusal.json")
    if job.get("outcome") is None and os.path.isfile(refusal) and not os.path.islink(refusal):
        job["outcome"] = "refused"
    if kyloop.detect_quota(job["stdout_path"], job["stderr_path"])["refusal"]:
        job["failure_fp"] = QUOTA
    _checkpoint(job)["collected"] = _stamp()
    if job.get("engine") == "codex":
        job["phase"] = "terminating"
        _save(ctx, job)  # exit/turn evidence survives a crash between a landing effect and its action record
        _engine_finish(ctx, job)
    _settle(ctx, job)


def _engine_finish(ctx, job):
    cp = _checkpoint(job)
    if job.get("outcome") is not None or cp.get("codex_finished"):
        return True
    result = engines.finish(ctx, job, _result(job))
    if result and result.get("outcome") == "held":
        cp["codex_finish_pending"] = result
        _await(ctx, job, "codex-finish", result["detail"])
        return False
    cp.pop("codex_finish_pending", None)
    cp["codex_finished"] = dict(result or {}, **engines.metadata(job))
    if result:
        job.update(outcome=result["outcome"], failure_fp=result.get("failure_fp"))
    _save(ctx, job)
    return True


# ───────────────────────────────────────── supervise ─────────────────────────────────────────

def _signal(job, sig):
    """Signal the group this module started for the job. → True when the signal was sent (or the group is empty)."""
    pid, pgid = job.get("pid"), job.get("pgid")
    if not _real_int(pid) or not _real_int(pgid) or pgid != pid or pgid <= 1 or pgid in (os.getpid(), os.getpgrp()):
        return False
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return True


def _terminate(job):
    """TERM the job's group, wait TERM_WAIT_S, KILL what is left → the job's process state afterwards. A state
    that cannot be told is never signalled."""
    state = _process(job)
    for sig, wait in ((signal.SIGTERM, TERM_WAIT_S), (signal.SIGKILL, KILL_WAIT_S)):
        if state not in ("live", "survivors") or not _signal(job, sig):
            break
        end = time.monotonic() + wait
        while True:
            state = _process(job)
            if state == "gone" or time.monotonic() >= end:
                break
            time.sleep(0.05)
    return state


def _renew(ctx, job, last):
    if not _text(job.get("claim_id")) or job["claim_id"] == PENDING or (last is not None and _now() - last < RENEW_S):
        return
    rc, _, err = ctx.ky("renew", "--lease", str(LEASE_S), stream=job["stream"], lane=job["slot"])
    if rc == 0:
        job["renewed_at"] = _stamp()
        _save(ctx, job)
    else:
        ctx.journal("renewal", "%s: ky renew for slot %s rc=%r %s" % (job["job_id"], job["slot"], rc, ka.flat(err, 200)))


def _overdue(ctx, job):
    """A terminating job whose process still runs past its deadline (a close handed a live job, a kill that had
    not finished): its group is reaped as at any timeout. Before the deadline nothing is signalled."""
    cp = _checkpoint(job)
    if "exited" in cp["steps"] or not _real_int(job.get("pid")):
        return
    deadline = _when(job["deadline"])
    stalled = job.get("engine") == "codex" and job.get("failure_fp") == "codex_stalled"
    if (not stalled and (deadline is None or _now() < deadline)) or _process(job) not in (("live", "survivors") if job.get("engine") == "codex" else ("live",)):
        return
    if _terminate(job) == "gone" and not cp.get("collected"):
        _collect(ctx, job)
        _save(ctx, job)


def supervise(ctx):
    """One look at every live job of this controller: renewal, timeout, and what a finished job left.
    → the jobs of this controller that are terminating; the engine owes each its close."""
    out = []
    for job in load(ctx):
        if job.get("controller_id") != ctx.controller_id:
            continue
        if job["phase"] == "terminating":
            _overdue(ctx, job)
            out.append(job)
            continue
        if job["phase"] != "live":
            continue
        state = _process(job)
        if state == "gone":
            _collect(ctx, job)
            job["phase"] = "terminating"
            _save(ctx, job)
            out.append(job)
            continue
        if job.get("engine") == "codex" and state in ("live", "survivors"):
            if not _checkpoint(job).get("codex_activity"):
                _await(ctx, job, "codex-activity", "launch/activity times are unknown; no stall decision is possible")
                continue
            try:
                silent = engines.stalled(job, _now())
            except engines.Hold as exc:
                _await(ctx, job, "codex-activity", str(exc))
                continue
            _save(ctx, job)
            if silent:
                job.update(phase="terminating", outcome="failed", failure_fp="codex_stalled")
                _checkpoint(job)["codex_activity"]["reason"] = "codex_stalled"
                _save(ctx, job)  # no renewal once terminating
                if _terminate(job) == "gone":
                    _collect(ctx, job)
                    _save(ctx, job)
                out.append(job)
                continue
        if state != "live" and not (job.get("engine") == "codex" and state == "survivors"):
            _await_process(ctx, job, state)
            continue
        deadline, last = _when(job["deadline"]), _when(job["renewed_at"])
        if deadline is None or (job["renewed_at"] is not None and last is None):
            _await(ctx, job, "time-unknown",
                   "its deadline %r or renewed_at %r is not UTC text YYYY-MM-DDTHH:MM:SSZ: when it times out or "
                   "is due for renewal is unknown, so it is neither stopped nor renewed. What are its times?"
                   % (job["deadline"], job["renewed_at"]))
            continue
        if _now() < deadline:
            _renew(ctx, job, last)
            continue
        job.update(phase="terminating", outcome="timed_out")             # renewal stops here
        _save(ctx, job)
        if _terminate(job) == "gone":                    # not gone yet: its close finds out, and says so
            _collect(ctx, job)
            _save(ctx, job)
        out.append(job)
    return out


# ───────────────────────────────────────── recover ─────────────────────────────────────────

def _adopt(ctx, job):
    """Transfer supervision only after all existing job/item lock fences succeed."""
    if all([_own(ctx, job, name) for name in ["job.%s" % job["key"]] + list(job["locks"] or [])]):
        job["controller_id"] = ctx.controller_id
        _save(ctx, job)
        return True
    _await(ctx, job, "locks", "it still runs and is this controller's to supervise, but its locks "
                              "could not be taken under this controller. Who holds them?",
           [ka.lock_path(_run(ctx), "job.%s" % job["key"])])
    return False


def recover(ctx):
    """The jobs an earlier controller left: prepared and never started → closed refused; terminating → its close
    carried on; live and gone → interrupted and closed; live and running → adopted (its locks and its
    supervision are this controller's now). Known Codex survivors and terminating groups are also adopted;
    unknown identity, Claude survivors and a pending start → an owner-wait only.
    → the jobs this call closed (or tried to) or adopted, as they are now."""
    out = []
    for job in load(ctx):
        if job["phase"] == "ended" or job.get("controller_id") == ctx.controller_id:
            continue
        if job["phase"] == "prepared":
            if job["pid"] is None:
                out.append(close(ctx, job, {"outcome": "refused", "failure_fp": None,
                                            "detail": "prepared by controller %s and never started"
                                                      % job.get("controller_id")}))
            else:
                _await_pending(ctx, job)
            continue
        if job["phase"] == "terminating":
            if job.get("engine") == "codex" and _process(job) in ("live", "survivors"):
                if not _adopt(ctx, job):
                    continue
            out.append(close(ctx, job, None if job.get("outcome") in OUTCOMES else {
                "outcome": "interrupted", "failure_fp": None,
                "detail": "terminating under controller %s with no outcome recorded: its kind's finish never ran"
                          % job.get("controller_id")}))
            continue
        state = _process(job)
        if state == "gone":
            # An adopted Codex job has no observable exit code; preserve strict refusal at collection.
            job.update(phase="terminating", outcome="interrupted")
            _collect(ctx, job)
            _save(ctx, job)
            out.append(close(ctx, job, None))
        elif state == "live" or (job.get("engine") == "codex" and state == "survivors"):
            if _adopt(ctx, job):
                out.append(job)
        else:
            _await_process(ctx, job, state)
    return out


# ───────────────────────────────────────── close ─────────────────────────────────────────

def _step_result(ctx, job, result):
    if job.get("engine") == "codex" and job.get("pid") is not None and not _checkpoint(job).get("collected"):
        state = _process(job)
        if state != "gone":
            _await_process(ctx, job, state)
            return False
        _collect(ctx, job)  # a caller's done cannot precede the engine's exit/turn/guard detectors
    if job.get("engine") == "codex" and _checkpoint(job).get("collected"):
        if not _engine_finish(ctx, job):
            return False
    result = result if isinstance(result, dict) else {}
    fp = job.get("failure_fp") or result.get("failure_fp")
    fp = fp if _text(fp) else None
    outcome = job.get("outcome") if job.get("outcome") in OUTCOMES else result.get("outcome")
    if outcome not in OUTCOMES:                          # never the job's own result.json: nothing checked it
        outcome = "failed" if fp == QUOTA else "refused" if job.get("pid") is None else "interrupted"
    if outcome == "interrupted" and fp != QUOTA:
        job["requeued"] = not _interrupted(load(ctx), job["key"], but=job["job_id"])
    job.update(outcome=outcome, failure_fp=fp, phase="terminating")
    if outcome == "done":
        clear_review_failure(ctx, job)
    detail = result.get("detail")
    _checkpoint(job).update(at=_stamp(), outcome=outcome, failure_fp=fp, exit_code=job.get("exit_code"),
                            detail=None if detail is None else ka.flat(detail, 2000),
                            result_path=job.get("result_path"),
                            result_sha256=ka.sha_file(job["result_path"]) if job.get("result_path") else None)
    _account(ctx, job)
    return True


def _step_exited(ctx, job, result):
    if job.get("pid") is None:
        return True                                      # never started: there is no process group
    if not _real_int(job["pid"]):
        _await_pending(ctx, job)
        return False
    state = _process(job)
    if state != "gone":
        _await_process(ctx, job, state)
        return False
    if not _checkpoint(job).get("collected"):            # first seen gone here: what it left is read now
        _collect(ctx, job)
    return True


def _step_boundary(ctx, job, result):
    if not job.get("boundary"):
        return True
    rc, _, err = ctx.sh(["bash", str(_fleet(ctx) / "kyboundary.sh"), "release", job["job_id"]])
    if rc == 0:
        return True
    _await(ctx, job, "boundary", "its verifier boundary could not be shown released (kyboundary.sh release rc=%r "
                                 "%s); the slot stays unavailable. Is the view gone?" % (rc, ka.flat(err, 200)))
    return False


def _step_claim(ctx, job, result):
    cid = job.get("claim_id")
    if cid is None:
        return True                                      # a claimless job releases only its locks
    path = _claims_path(ctx, job)
    doc, err = ka.read_json(path)

    def held(d):
        return isinstance(d, dict) and d.get("item") == job["item"] and d.get("worker_id") == job["slot"]

    def stop(why):
        _await(ctx, job, "claim", "reconciliation required — %s. Nothing was released (`ky release` releases "
                                  "whatever that file names) and slot %s stays unavailable. Whose claim is it?"
               % (why, job["slot"]), [path])
        return False

    if cid == PENDING:                                   # the claim was being made when the controller died
        if err == "missing" or (err is None and not (held(doc) and doc.get("state") in ("acquired", "renewed"))):
            job["claim_id"] = None                       # no active claim of this item by this slot: none was made
            return True
        if err or not _text(doc.get("claim_id")):
            return stop("its claim was never recorded and %s cannot be read (%s)" % (path, err))
        cid = job["claim_id"] = doc["claim_id"]          # the slot had no other job: that claim is this job's
        _save(ctx, job)
    if err or not isinstance(doc, dict):
        return stop("the job holds claim_id %s and %s is %s" % (cid, path, err or "not an object"))
    if not held(doc) or doc.get("claim_id") != cid:
        return stop("the job holds %s for %s as %s, and %s names item %r, worker %r, claim_id %r"
                    % (cid, job["item"], job["slot"], path, doc.get("item"), doc.get("worker_id"), doc.get("claim_id")))
    if doc.get("state") in ("released", "expired"):
        return True                                      # already released for this very claim: never twice
    if doc.get("state") not in ("acquired", "renewed"):
        return stop("%s is in state %r for claim_id %s" % (path, doc.get("state"), cid))

    def seen():
        now, _ = ka.read_json(path)
        if held(now) and now.get("claim_id") == cid:
            return "released" if now.get("state") in ("released", "expired") else \
                "active" if now.get("state") in ("acquired", "renewed") else None
        return None

    def effect():
        rc, _, stderr = ctx.ky("release", stream=job["stream"], lane=job["slot"])
        if rc == 0 and seen() == "released":
            return "done", {"claim_id": cid, "state": "released"}
        if rc is None or rc == 0:
            return "unknown", {"rc": rc, "reason": "the claim file does not show this claim released"}
        return "failed", {"rc": rc, "stderr": ka.flat(stderr, 300)}

    def observer(record):
        state = seen()
        return ("done", {"claim_id": cid, "state": "released", "reconciled": True}) if state == "released" else \
            ("not_done", {"claim_id": cid, "state": "active"}) if state == "active" else \
            ("unknown", {"reason": "the claim file no longer names this claim"})

    try:
        outcome, detail = _act(ctx, job, "ACT-release-%s" % job["job_id"], "ky_release",
                                  {"item": job["item"], "worker": job["slot"], "claim_id": cid},
                                  {"claims": str(path)}, effect, observer)
    except ka.ActionError as e:
        outcome, detail = "unknown", {"error": "%s: %s" % (type(e).__name__, ka.flat(e, 200))}
    if outcome == "done" or seen() == "released":
        return True
    return stop("`ky release` for claim_id %s: %s (%s)" % (cid, outcome, ka.flat(detail, 200)))


def _step_locks(ctx, job, result):
    ledger = _checkpoint(job).setdefault("lock_release", {})
    kept = []
    for name in list(job.get("locks") or []) + ["job.%s" % job["key"]]:
        if ledger.get(name) == "released":
            continue
        if _drop(ctx, job, name, ledger):
            ledger[name] = "released"
            _save(ctx, job)
        else:
            kept.append(name)
    if not kept:
        return True
    _await(ctx, job, "locks", "its lock(s) %s could not be released: another owner holds them, or their owner "
                              "cannot be judged. The slot stays unavailable. Whose are they?" % ", ".join(kept),
           [ka.lock_path(_run(ctx), name) for name in kept])
    return False


def _step_handled(ctx, job, result):
    if job["outcome"] == "done":
        os.makedirs(_run(ctx) / "handled", exist_ok=True)
        ka.write_json(_run(ctx) / "handled" / ("job.%s.json" % job["key"]), {
            "schema": HANDLED_SCHEMA, "id": "job.%s" % job["key"], "handled_at": _stamp(),
            "by": {"role": "dispatcher", "controller_id": ctx.controller_id},
            "checkpoint": {k: job.get(k) for k in ("job_id", "item", "kind", "outcome", "head", "digest",
                                                    "evidence_fp", "result_path")},
            **(engines.metadata(job) if job.get("engine") == "codex" else {})})
    return True


_STEPS = {"result": _step_result, "exited": _step_exited, "boundary": _step_boundary, "claim": _step_claim,
          "locks": _step_locks, "handled": _step_handled, "ended": lambda ctx, job, result: True}


def _close(ctx, job, result):
    steps = _checkpoint(job)["steps"]
    for name in CLOSE_STEPS:
        if name in steps:
            continue
        if not _STEPS[name](ctx, job, result):
            return job
        steps[name] = _stamp()
        if name == "ended":
            job.update(phase="ended", ended_at=steps[name])
        _save(ctx, job)
    return job


def close(ctx, job, result=None):
    """Carry the job to `ended` (see the module docstring). `result` = {outcome, detail, failure_fp} from the
    kind's finish or the engine's refusal; an outcome the controller itself recorded (timed_out, refused,
    interrupted, an earlier close) is kept. → the job as it is afterwards."""
    job = _fresh(ctx, job)
    if job["phase"] == "ended":
        return job
    slot_lock = None
    if job.get("slot"):
        slot_lock = _take(ctx, "slot.%s" % job["slot"])
        if slot_lock is None:
            return job
    try:
        return _close(ctx, job, result)
    finally:
        if slot_lock is not None:
            ka.release_lock(slot_lock)
