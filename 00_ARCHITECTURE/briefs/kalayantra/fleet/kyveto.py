#!/usr/bin/env python3
"""kyveto.py — the deterministic veto-window handler of KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.3, §6 SURROGATE
row, §10 "Start (D-7)", §13 "veto expired", pairing rule KW-04; owner decisions D-4 amended, D-7; B-0c rework
rulings R2–R5).

    kyveto.py tick [--authorised-commit C --entrypoints-digest D] [--as HOLDER_ID]
                   [--holder-kind controller|supervisor]          one pass over the pending veto-class decisions
    kyveto.py status [--now ISO] [--authorised-commit C --entrypoints-digest D]        read-only
    kyveto.py fingerprint --target FILE        the target fingerprint the surrogate records at proposal (read-only)

    tick(env=None, *, authorised=None, holder=None, holder_kind="controller", publish_observer=None, log=None)
    status(env=None, now=None, authorised=None)          fingerprint(target, env)

The owner surrogate only PROPOSES a veto-class decision: it appends a PENDING_VETO line to
$KY_RUN/DECISIONS_SURROGATE.jsonl and publishes nothing. This handler — a script, never a model — is the only
actor that makes such a decision effective.

THE CLOCK. The effecting path (`tick`) reads the wall clock and nothing else: it takes no time argument, on the
command line or in Python, and honours no environment variable. Tests replace the module-level function
`wall_clock` in-process. Only the read-only `status` accepts `--now`.

WHAT THE HANDLER BELIEVES. The decision log is written by a model, so nothing in it is evidence of what this
handler did — a line saying `"by": "kyveto"` least of all. The handler's memory is what it wrote itself:
  $KY_RUN/veto/<SD id>.first_seen.json   {first_seen_at, proposal_line_sha256}: created exclusively the first time a
                                         tick sees the decision PENDING_VETO; the sha256 is over the canonical JSON
                                         of the decision's first PENDING_VETO line (proposal_sha)
  $KY_RUN/actions/<SD id>.publish        the kyaction record of making it effective (with `ky decide …` when the
                                         target names a tracker decision); DONE = the handler made it effective
  $KY_RUN/actions/<SD id>.execute        the kyaction record of the class executor; DONE = the handler executed it
                                         (both are handled-state: they are never pruned — without them the log's
                                         EFFECTIVE / EXECUTED lines are claims nothing backs)
  $KY_RUN/veto/<SD id>.refused.json      {refused_at, reason, published[, executed, partial_effect]}: a record
                                         the handler will never act on and cannot answer in the log (see
                                         "refused" below)
  $KY_RUN/veto/<SD id>.closed.json       {closed_at, state, reason}: the handler brought the decision to VETOED or
                                         FAILED itself — written after its line, for every decision it holds an
                                         action record for (see "A TERMINAL STATE" below)
PUBLICATION HAS THREE ANSWERS (`publication`): true — `<id>.publish` names a tracker decision and is DONE; false —
there is no such record, it names no tracker decision, or it is FAILED with `result.published: false` (`ky` never
started, or a readback proved the tracker holds nothing); "unknown" — anything else: `ky decide` was started and
neither its exit status 0 nor a readback says what the tracker holds. Unknown is never reported as "not published":
VETOED / FAILED lines and rows then carry `published: "unknown"` with attention, and `status` keeps the decision
`unresolved` until the record is reconciled (a tick given a `publish_observer` does that, also for a finished
decision; until B-3 delivers one, the owner corrects the tracker and the record by hand).
and what `kynotify.sh` wrote: a $KY_RUN/JOURNAL_COCKPIT.md line `- <UTC> [<level>] <SD id>: … [notify=submitted]`
(one physical line, split at LF only: a Unicode line separator smuggled into a message starts no new line).
These files are the handler's by the roles' instructions; the enforced write boundary that would stop a job from
planting one is a B-1 deliverable, and until then this is a convention the reviewer of a job's writes checks.

A TERMINAL STATE IS ACCEPTED BY STATE, NEVER BY AUTHORSHIP (C4-01, ruling R14; `first_terminal`). While the
handler holds no action record for a decision, its first VETOED or FAILED line is final: nothing of the
handler's is out. Once it holds one, no line ends its custody — a line's `by` is whatever the model wrote:
  `<id>.execute` DONE       the effect is in place: the decision is EXECUTED and nothing else. A VETOED or FAILED
                            line beside it is overruled: the handler appends EXECUTED itself (`already_executed`)
  `<id>.execute` INTENDED   nothing is final. EVERY exit that gives the decision up — an owner veto, a failed
                            check, a refusal, a terminal line the handler did not write — first closes that
                            record (`give_up`): reconciled against the disk; complete → DONE (EXECUTED); otherwise
                            what is in place is put back and verified, or recorded as `partial_effect` in the
                            record, the line and the row; what cannot be judged stays `blocked`, on every tick
  otherwise                 VETOED / FAILED is final once the handler closed the decision itself
                            (`<id>.closed.json`). A VETOED or FAILED line found without that closing is a claim
                            (anomaly `terminal_line_not_the_handlers`): the tick answers it ONCE — an owner veto
                            for it first, else FAILED `closed_by_log_line: <state>` — with attention, the
                            three-valued `published` and the `executed` flag, and writes the closing; until then
                            `status` keeps the decision `unresolved` and shows the state the handler accepts.

For every decision that needs the handler (ANY of its lines says PENDING_VETO, EFFECTIVE or EXECUTED, or the
handler holds an action record for it, and it has no terminal state the handler accepts; or a line was appended
after its terminal state), under the lock `decision.<id>` and after a FRESH re-read:

  A LINE THAT STEPS BACK (C3-02) — PROPOSED appended after PENDING_VETO, PENDING_VETO after EFFECTIVE, … — takes
  the decision out of nothing: it carries on from the handler's own memory (the proposal, its first-seen stamp,
  the action records), exactly as below; a step back that changes what the owner was told fails in (6) like any
  other mutation. Every row of such a decision carries `anomaly: line_regressed_before_terminal_state` with
  attention until the handler's next line answers it, and `status` shows the handler-accepted state, the
  anomaly and `unresolved`.

  (0) a record the handler could not answer with a schema-valid line — class `hard_stop` (owner-only: never
      delegated, never published), any class but `veto`, or malformed base fields — gets NO line: it is REFUSED
      once in $KY_RUN/veto/<id>.refused.json and reported with attention; `status` keeps showing it
  (1) a line after the decision's terminal state → the terminal state is appended again (terminal_state_is_final),
      reported with attention; a VETOED / FAILED line that is not final (above) → answered as said there;
      EFFECTIVE without a DONE `<id>.publish`, or EXECUTED without a DONE `<id>.execute`
      → FAILED log_claims_<state>_without_action_record: that decision is blocked for good
  (2) first sight is stamped; a stamp whose sha256 is not this proposal → FAILED decision_record_mutated: proposal
  (3) an owner `veto` command for it, QUEUED or APPLIED      → VETOED; the command is marked applied; never executed
  (4) while the handler has not begun to make it effective:
        veto_deadline unreadable                             → FAILED veto_deadline_unreadable
        notification.submitted is not exactly true           → FAILED notification_not_submitted
        no `<SD id>: … [notify=submitted]` journal line      → FAILED notification_unverified
        now < max(first_seen_at, notified_at) + 30 min, or now < the record's own veto_deadline
                                                             → left pending (seconds remaining reported)
      notified_at is the time of the latest such journal line. A backdated proposal therefore still waits 30 real
      minutes from the handler's first sight of it.
  (5) $KY_ROOT/HOLD, an owner pause (applied, or requested and not applied), $KY_RUN/STOP_veto, or a command
      queue that cannot be read                              → left pending, reported "held"; nothing fails.
      Looked at three times — here, before the publication and before the execution, each time beside the last
      look at the veto (C4-05): a hold placed while the recheck or `ky decide` ran stops what has not happened
  (6) recheck — the first failure appends FAILED with its named reason: record immutability across the decision's
      lines (decision_record_mutated: <field>), authority (authority_unbound / authority_changed), target
      (target_unbound / unknown_target_kind / target_malformed / target_changed), tracker_decision shape, the
      awaiting item (awaiting_unbound / awaiting_not_open / awaiting_unreadable / tracker_decision_not_the_
      awaiting_items — also when the item names no tracker decision at all / superseded_by_owner_decide /
      awaiting_already_decided), class hold (class_hold:
      HOLD_MERGES), the ky CLI when a tracker decision must be published, and the class's own prerequisites.
      An authority that cannot be established (no arguments, no usable PLANNER_STATE.json `authorised_source`,
      or one an activation chain has superseded) is NOT a failure: the decision is HELD and the tick reports
      one `authority_unknown` problem.
  (7) publish, then execute, each through its own kyaction record:
        <id>.publish   `ky decide <D-id> --outcome <o> --as steward --delegated --detail "<id>: <decision>"`
                       where target.tracker_decision = {"id", "outcome"} is set (otherwise the record only says
                       that nothing was to be published); a non-zero exit is read back: proven published → DONE,
                       proven not → the record FAILED (published: false); no readback → the record stays
                       unfinished (published unknown) — in both of the latter the decision is FAILED
                       publication_failed; an exit that was not observed at all stays unfinished and blocks —
                       never retried
        EFFECTIVE      appended with effective_at once that record is DONE
        <id>.execute   the class executor; an unfinished record is reconciled against the disk first
        EXECUTED       appended only after the executor's observed result is recorded
      The plan's order is kept (§4a.3: "publishes the effective decision … and executes"): nothing irreversible
      is executed for a decision the tracker refused, and a failed publication is FAILED, never EXECUTED.

THE REPORT of a tick: {schema "ky.veto_tick/1", now, holder, authority {…, source}, holds[], decisions[],
commands[], problems[], attention}. One row per decision the pass looked at — {id, outcome, …}:
  pending     inside its window: seconds_remaining; veto_deadline = effective_not_before = the earliest moment the
              handler will let it become effective (what a controller sleeps until); record_veto_deadline,
              first_seen_at, notified_at
  held        reasons[] (HOLD, STOP_veto, owner_paused, owner_pause_pending, command_queue_unreadable,
              authority_unknown); nothing was changed
  locked      another LIVE actor has the decision or its awaiting item, or (reason publication_in_progress /
              execution_in_progress) the process that began that action is alive elsewhere: come back later.
              When that process cannot be told alive or gone the row carries attention and `owner: "unknown"`
  blocked     needs somebody (attention): an unreconciled publication or execution, a lock or stamp or journal
              that cannot be judged or read, a foreign action record, an unexpected error; reported on every tick.
              `giving_up` names what the handler was about to say when the execution could not be closed first
  vetoed · executed · failed · refused      final for the decision: reported ONCE (it then no longer needs the
              handler). `failed` and `refused` always carry attention; `vetoed` / `executed` carry it when the
              tracker holds, or may hold, a decision that contradicts the outcome (`published`: true or
              "unknown" — the key is absent only when nothing was published) or a veto came too late; a finished
              decision whose unknown publication a later readback settled is reported once more (reason
              publication_reconciled, with attention when the tracker does hold the decision); `anomaly`
              names a log line the handler did not write (line_appended_after_terminal_state,
              log_claim_without_action_record, terminal_line_not_the_handlers,
              line_regressed_before_terminal_state — the last two on any row);
              `partial_effect` (restored | in_place | unknown, always with attention) on a `vetoed` / `failed`
              / `refused` row: part of the execution was in place when it was given up — put back and
              verified, or left and said so in the line's detail (the refusal marker) and the `<id>.execute`
              record (`status` keeps the latter two `unresolved`, listed in `partial_effects`, for as long as
              a fresh look does not find the recorded before values); `executed` (with attention) on a row
              that was about to give the decision up: is the effect in place by the handler's own record?
              — `executed` / `already_executed` with `instead_of` when it is; an owner veto that reaches an
              EXECUTED decision in a LATER tick is reported like one inside the tick (`executed`, reason
              veto_too_late, attention, `command`; C4-02)
  not_pending another handler finished it between this pass's first look and its lock; with reason
              veto_too_late, `state` and attention: an owner veto of a decision that is not the handler's
`attention` (exit 3) is true when any row or command carries it or `problems` is not empty.

Target classes (registry keyed by target.kind; every target carries `fingerprint`, see `kyveto.py fingerprint`):
  capacity            {kind, builders 1–8, verifiers 1–8[, tracker_decision]} → $KY_RUN/KY_WORKERS, KY_VERIFIERS;
                      both files are written under the one `<id>.execute` record, which stores their exact
                      before values (inputs.before) with the intention: a crash between them leaves it
                      unfinished, its reconciliation sees the pair incomplete and the executor finishes it.
                      When the execution is given up instead (an owner veto, an executor error, any other
                      exit — see "A TERMINAL STATE" above), "incomplete" is never read as "nothing happened"
                      (C3-01): the pair is compared with the before values — nothing in place →
                      vetoed_before_execution / given_up_before_execution; this change's own half → put back
                      and verified (…_partial_effect_restored / partial_effect restored); anything else →
                      reported as in place (…_with_partial_effect) or, when it cannot be judged at all,
                      blocked execution_unreconciled
  plan_bundle_change  {kind, old_commit, new_commit, old_manifest_digest, new_manifest_digest, new_manifest_path,
                      review_receipts[][, tracker_decision]} → the next immutable $KY_RUN/ACTIVATION_RECORD.<n>.json.
                      "Independently reviewed" is computed, not asserted: every receipt says ACCEPTED, names a
                      reviewer_session_id that is none of the decision's own sessions, carries source_commit =
                      new_commit, manifest_sha256 = new_manifest_digest and a non-empty `inputs`; the manifest file
                      exists, its recomputed digest (canonical JSON without `manifest_sha256`, as kymanifest.py)
                      is new_manifest_digest, it names new_commit as its (approved_)source_commit, it carries
                      the five-role `entrypoints` mapping, any `entrypoints_digest` it states is that mapping's,
                      and its owner_decisions entrypoint is the unchanged blob at new_commit; the activation
                      record stores the absolute paths of the manifest and of every receipt
  campaign_start, protected_window        their executors are later deliverables: always FAILED
                      "executor_unavailable: …" — never a faked success
An unknown kind is FAILED unknown_target_kind.

Exactly one handler runs at a time: `--as ID` must name the owner of $KY_RUN/locks/veto, and the caller must be
that owner process or its child (kycommands.holds_role_lock); otherwise the tick takes that lock for its own
duration (and reports "skipped" when another handler holds it).

Environment: KY_ROOT (/Users/Dev/kalayantra), KY_RUN ($KY_ROOT/run), KY_FLEET ($KY_ROOT/fleet_live), KY_BIN
($KY_ROOT/bin/ky), KY_SOURCE_REPO (the git checkout used to compare the owner-decisions blob; when the variable
is absent, DEFAULT_SOURCE_REPO is used only if it exists and is itself a git work tree — otherwise that
comparison is unverifiable and a bundle change is refused), KY_GIT (/usr/bin/git), KY_OWNER_DECISIONS_PATH.
`ky` receives an allow-listed environment only.

Exit codes: 0 pass completed · 1 fingerprint refused · 3 completed, but something needs attention (a failed or
refused decision, an anomaly, an unreadable log or queue, an unreconciled action, an unknown authority or lock
owner) · 64 usage (`tick --now` included) · 66 run directory missing · 75 `--as` does not name the caller's own
veto role lock.   Python >= 3.9, standard library only.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kyaction  # noqa: E402
import kycommands  # noqa: E402

HANDLER = "kyveto"
SURROGATE = "kalayantra-owner-surrogate"
STATES = ("PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED", "VETOED", "FAILED")
ORDER = {"PROPOSED": 0, "PENDING_VETO": 1, "EFFECTIVE": 2, "EXECUTED": 3}       # a later line never steps back
REGRESSED = "line_regressed_before_terminal_state"
CLAIMED = "terminal_line_not_the_handlers"     # a VETOED / FAILED line the handler's own records do not bear out
GIVEN_UP = {"absent": "given_up_before_execution", "restored": "given_up_partial_effect_restored",
            "in_place": "given_up_with_partial_effect"}       # how an unfinished `<id>.execute` was closed, by `undo`
VETO_WINDOW_S = 1800                    # the owner's window: 30 minutes of real time
# Source of CAPACITY_MAX: owner direction of 2026-10-12 — builders up to 8; recorded in the run directory's
# PLANNER_STATE active.owner_directions_20261012, not yet in the owner decisions file; verifier maximum 8 is an
# interpretation pending the owner.
CAPACITY_MAX = {"builders": 8, "verifiers": 8}
ENTRYPOINT_ROLES = ("plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent")
OWNER_DECISIONS_PATH = "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md"
DEFAULT_SOURCE_REPO = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"     # second line of defence
KY_ENV_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "KY_ROOT", "KY_RUN", "KY_FLEET")
BASE_FIELDS = ("id", "awaiting", "class", "decision", "rationale", "evidence", "target", "authority",
               "notification", "veto_deadline", "effective_at")
LINE_FIELDS = BASE_FIELDS + ("state", "by", "session", "reason", "at", "detail")
FIXED_FIELDS = ("target", "authority", "class", "awaiting")                    # the same on every line of a decision
WINDOW_FIELDS = ("decision", "evidence", "notification", "veto_deadline")      # … from the first PENDING_VETO line on
JOURNAL = "JOURNAL_COCKPIT.md"
UNKNOWN = "unknown"                     # tick(authorised=UNKNOWN): the caller could not establish the authority
SD_RE, AW_RE = kycommands.SD_RE, kycommands.AW_RE
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
ISO_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|\+00:00)\Z")
TRACKER_ID = re.compile(r"^D-[A-Za-z0-9][A-Za-z0-9._-]{0,59}\Z")
TRACKER_OUTCOME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
RECORD_NAME = re.compile(r"^ACTIVATION_RECORD\.([1-9][0-9]{0,5})\.json\Z")
NOTIFY_LINE = re.compile(r"^- (\S+) \[[a-z_]+\] (.*) \[notify=(submitted|failed|dry)\]\s*\Z")


def wall_clock():
    """The one clock of the effecting path, in epoch seconds. Tests replace this function in-process; no
    argument, option or environment variable reaches it."""
    return time.time()


class TargetError(Exception):
    """The target cannot be bound: .reason is the named refusal."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class NotHolder(Exception):
    """`--as` does not name the caller's own veto role lock."""


class RunMissing(Exception):
    """The run directory does not exist; the handler never creates one."""


class Foreign(kyaction.ActionError):
    """An action record under one of the handler's ids that the veto role did not write: it is not memory."""


class Unwritable(kyaction.ActionError):
    """A line the handler was about to append would violate the decision schema; nothing was written."""


class Env:
    """Paths and tools, all taken from one mapping (the process environment unless one is given)."""

    def __init__(self, environ=None):
        e = dict(os.environ if environ is None else environ)
        self.environ = e
        self.root = Path(e.get("KY_ROOT") or "/Users/Dev/kalayantra")
        self.run = Path(e.get("KY_RUN") or self.root / "run")
        self.fleet = Path(e.get("KY_FLEET") or self.root / "fleet_live")
        self.ky_bin = Path(e.get("KY_BIN") or self.root / "bin" / "ky")
        self.git = e.get("KY_GIT") or "/usr/bin/git"
        self._repo, self._repo_known = e.get("KY_SOURCE_REPO") or None, "KY_SOURCE_REPO" in e
        self.owner_decisions_path = e.get("KY_OWNER_DECISIONS_PATH") or OWNER_DECISIONS_PATH
        try:
            self.ky_timeout = float(e.get("KYVETO_KY_TIMEOUT_S") or 120)
        except ValueError:
            self.ky_timeout = 120.0

    @property
    def repo(self):
        """The checkout the owner-decisions blob is read from, or None (then nothing is verifiable). An explicit
        KY_SOURCE_REPO is taken as given, even empty; only an absent one falls back to the default, resolved on
        first use so that nothing but a bundle change ever looks at that checkout."""
        if not self._repo_known:
            self._repo, self._repo_known = default_source_repo(self), True
        return self._repo


class Ctx:
    """What a target class may look at: the environment, the deciding id, its authority, the tick's time and the
    decision's own sessions (the ids no independent reviewer may carry; None = not known, which refuses)."""

    def __init__(self, env, decision_id, authority, now, sessions=None):
        self.env, self.decision_id, self.authority, self.now = env, decision_id, authority or {}, now
        self.sessions = None if sessions is None else frozenset(sessions)


# ───────────────────────────────────────── the decision log ─────────────────────────────────────────

def _not_json(name):
    raise ValueError("%s is not JSON" % name)


def load_decisions(path):
    """→ (history, problems, unusable). history: {decision id: [its lines, in file order]}.
    problems: lines that cannot be attributed to a decision (not JSON, no SD id) — while any exists NO decision's
    state is known, so the handler makes no transition at all. unusable: {id: reason} for decisions with a line
    whose state is not a decision state (a hard_stop record without a state is not the handler's business)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return {}, [], {}
    except OSError as e:
        return {}, ["decision log unreadable: %s" % type(e).__name__], {}
    history, problems, unusable = {}, [], {}
    for n, raw in enumerate(data.split(b"\n"), 1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw.decode("utf-8"), parse_constant=_not_json)
        except (ValueError, RecursionError):
            problems.append("decision log line %d: not JSON" % n)
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not SD_RE.match(obj["id"]):
            problems.append("decision log line %d: no usable decision id" % n)
            continue
        history.setdefault(obj["id"], []).append(obj)
        if obj.get("state") not in STATES and obj.get("class") != "hard_stop":
            unusable.setdefault(obj["id"], "decision log line %d: %s has no usable state" % (n, obj["id"]))
    return history, problems, unusable


def append_line(path, obj):
    """One line, one write, fsynced. A previous writer's unterminated last line never swallows this one."""
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        size = os.fstat(fd).st_size
        if size:
            with open(path, "rb") as f:
                f.seek(size - 1)
                if f.read(1) != b"\n":
                    data = b"\n" + data
        if os.write(fd, data) != len(data):
            raise OSError("short append to %s" % path)
        os.fsync(fd)
    finally:
        os.close(fd)


def _state(line):
    return line.get("state") if line.get("state") in STATES else None


def _done(record):
    return record is not None and record["state"] == "DONE"


def in_domain(lines):
    """A decision is the handler's business unless it is a routine decision that never entered a veto window."""
    return any(line.get("class") != "routine" or _state(line) in ("PENDING_VETO", "VETOED") for line in lines)


def claimed(lines):
    """The first VETOED or FAILED state among a decision's lines, or None. A claim until first_terminal accepts it."""
    return next((state for state in map(_state, lines) if state in ("VETOED", "FAILED")), None)


def first_terminal(lines, executed, held=False, closed=None):
    """The terminal state the handler accepts for a decision, or None. A state rule (C4-01, ruling R14): the
    handler's own records decide — who a line says wrote it plays no part.
      executed  `<id>.execute` is DONE: EXECUTED once a line says so, else None. The effect is in place, and a
                VETOED or FAILED line beside it is a claim that record overrules
      held      the handler holds an action record of its own for the decision: the state it closed the decision
                with itself (`closed` — see closed_as: its own marker, never while `<id>.execute` is INTENDED),
                else None. Without that no VETOED or FAILED line ends the handler's custody
      neither   the first VETOED or FAILED line (`claimed`): nothing of the handler's is out. An EXECUTED line
                never counts without the DONE record."""
    if executed:
        return "EXECUTED" if any(_state(line) == "EXECUTED" for line in lines) else None
    if held:
        return closed if closed in ("VETOED", "FAILED") else None
    return claimed(lines)


def needs_handler(lines, executed, begun=False, closed=None):
    """True when a tick has something to do or to say about this decision (see the module docstring). `begun`:
    the handler holds an action record of its own for it; `closed`: the state it closed the decision with itself
    (closed_as). Once a decision has entered its window (ANY line of it says PENDING_VETO, EFFECTIVE or EXECUTED)
    or the handler has begun to act on it, it needs the handler until it has a terminal state the handler
    accepts (first_terminal) — whatever its latest line says (C3-02, C4-01)."""
    if not lines or not (begun or in_domain(lines)):
        return False
    latest, finished = _state(lines[-1]), first_terminal(lines, executed, begun, closed)
    if finished:
        return latest != finished
    return begun or any(_state(line) in ("PENDING_VETO", "EFFECTIVE", "EXECUTED") for line in lines)


def regressed(lines):
    """True when the latest line steps back behind an earlier line of the same decision (PROPOSED appended after
    PENDING_VETO, PENDING_VETO after EFFECTIVE, …). Such a line changes nothing: the decision carries on from the
    handler's own memory, and the step back is reported as an anomaly until the handler's next line answers it."""
    latest = ORDER.get(_state(lines[-1])) if lines else None
    return latest is not None and any(ORDER.get(_state(line), -1) > latest for line in lines[:-1])


def accepted_state(lines, published, executed, begun=False, closed=None):
    """A decision's state as the handler accepts it: its terminal state (first_terminal; `begun` and `closed` as
    in needs_handler); else EFFECTIVE once the handler's own publication record is DONE (`published`); else
    PENDING_VETO when a later line stepped back behind the proposal or claims a VETOED / FAILED the handler does
    not accept; else what the latest line says."""
    if not in_domain(lines):
        return _state(lines[-1])
    finished = first_terminal(lines, executed, begun or published or executed, closed)
    if finished:
        return finished
    if published:
        return "EFFECTIVE"
    if (regressed(lines) or claimed(lines)) and proposal_of(lines) is not None:
        return "PENDING_VETO"
    return _state(lines[-1])


def proposal_of(lines):
    """The proposal a veto window belongs to: the decision's first PENDING_VETO line, or None."""
    return next((line for line in lines if _state(line) == "PENDING_VETO"), None)


def proposal_sha(line):
    """sha256 over the canonical JSON of a proposal line: what a first-seen stamp binds."""
    return kyaction.sha_bytes(kyaction.canonical(line))


def base_problem(line):
    """None, or why the handler cannot answer this record with a schema-valid line (schemas/
    surrogate_decision.json): it copies these fields unchanged into every line it appends."""
    cls = line.get("class")
    if cls == "hard_stop":
        return "hard_stop_never_delegated"
    if cls != "veto":
        return "class_not_veto: %s" % kyaction.flat(cls if isinstance(cls, str) else type(cls).__name__, 40)
    if not isinstance(line.get("awaiting"), str) or not AW_RE.match(line["awaiting"]):
        return "record_malformed: awaiting"
    for key in ("decision", "rationale"):
        if not isinstance(line.get(key), str) or not line[key]:
            return "record_malformed: %s" % key
    evidence = line.get("evidence")
    if not isinstance(evidence, list) or any(not isinstance(x, str) for x in evidence):
        return "record_malformed: evidence"
    target = line.get("target")
    if not isinstance(target, dict) or not isinstance(target.get("kind"), str) or not target["kind"] \
            or not isinstance(target.get("fingerprint"), str) or not HEX64.match(target["fingerprint"]):
        return "record_malformed: target (a veto target carries kind and fingerprint)"
    authority = line.get("authority")
    if not isinstance(authority, dict) or set(authority) != {"source_commit", "entrypoints_digest"} \
            or not isinstance(authority["source_commit"], str) or not HEX40.match(authority["source_commit"]) \
            or not isinstance(authority["entrypoints_digest"], str) or not HEX64.match(authority["entrypoints_digest"]):
        return "record_malformed: authority"
    notification = line.get("notification")
    if not isinstance(notification, dict) or set(notification) != {"submitted", "ts"} \
            or not isinstance(notification["submitted"], bool) \
            or not (notification["ts"] is None or isinstance(notification["ts"], str)):
        return "record_malformed: notification"
    if not isinstance(line.get("veto_deadline"), str) or not ISO_RE.match(line["veto_deadline"]):
        return "record_malformed: veto_deadline"
    effective = line.get("effective_at")
    if effective is not None and (not isinstance(effective, str) or not ISO_RE.match(effective)):
        return "record_malformed: effective_at"
    return None


def line_problem(line):
    """None, or why a complete line the handler is about to append is not a valid decision line."""
    problem = base_problem(line)
    if problem:
        return problem
    if set(line) - set(LINE_FIELDS) or not {"id", "state", "by", "session", "effective_at"} <= set(line):
        return "line_malformed: keys"
    if not isinstance(line["id"], str) or not SD_RE.match(line["id"]) or line["state"] not in STATES \
            or line["by"] not in (HANDLER, SURROGATE) or not isinstance(line["session"], str) or not line["session"]:
        return "line_malformed: id / state / by / session"
    if line["state"] in ("EFFECTIVE", "EXECUTED") and not isinstance(line["effective_at"], str):
        return "line_malformed: an %s line carries effective_at" % line["state"]
    if not isinstance(line.get("reason", ""), str) or not isinstance(line.get("at", "x"), str) or not line.get("at", "x") \
            or not isinstance(line.get("detail", {}), (dict, str)):
        return "line_malformed: reason / at / detail"
    return None


# ─────────────────────── evidence the surrogate does not write: first sight, notification ───────────────────────

def stamp_path(run, decision_id, kind="first_seen"):
    return Path(run) / "veto" / ("%s.%s.json" % (decision_id, kind))


def read_first_seen(run, decision_id):
    """→ (stamp, None), (None, None) when there is none yet, or (None, problem)."""
    stamp, err = kyaction.read_json(stamp_path(run, decision_id))
    if err == "missing":
        return None, None
    if err or not isinstance(stamp, dict) or kyaction.parse_utc(stamp.get("first_seen_at")) is None \
            or not isinstance(stamp.get("proposal_line_sha256"), str) or not HEX64.match(stamp["proposal_line_sha256"]):
        return None, "first_seen_unreadable: %s" % stamp_path(run, decision_id).name
    return stamp, None


def first_seen(run, decision_id, proposal, now):
    """The handler's first sight of a proposal → (stamp, None) or (None, problem). Created exclusively, once, with
    the time `now` rounded UP to the second; an existing stamp is never rewritten."""
    stamp, problem = read_first_seen(run, decision_id)
    if stamp is None and problem is None:
        path = stamp_path(run, decision_id)
        os.makedirs(path.parent, exist_ok=True)
        doc = {"first_seen_at": kyaction.utc(math.ceil(now)), "proposal_line_sha256": proposal_sha(proposal)}
        kyaction.write_exclusive(path, json.dumps(doc, indent=1, sort_keys=True) + "\n", mode=0o444)
        stamp, problem = read_first_seen(run, decision_id)       # ours, or the one another handler wrote first
        if stamp is None and problem is None:
            problem = "first_seen_unreadable: %s" % path.name
    return stamp, problem


def notified_at(run, decision_id):
    """When the owner notification of a decision was submitted, from evidence `kynotify.sh` wrote → (epoch, None),
    (None, None) when $KY_RUN/JOURNAL_COCKPIT.md has no line `- <UTC> [<level>] <SD id>: … [notify=submitted]`,
    or (None, problem) when the journal cannot be read. With several such lines the latest counts."""
    try:
        with open(Path(run) / JOURNAL, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return None, None
    except OSError as e:
        return None, "journal_unreadable: %s" % type(e).__name__
    best = None
    for raw in data.split(b"\n"):
        try:
            m = NOTIFY_LINE.match(raw.decode("utf-8").rstrip("\r"))
        except UnicodeDecodeError:
            continue
        if m and m.group(3) == "submitted" and m.group(2).startswith(decision_id + ":"):
            when = kyaction.parse_utc(m.group(1))
            if when is not None and (best is None or when > best):
                best = when
    return best, None


def read_refusal(run, decision_id):
    """The handler's refusal of a record → its marker, or None when there is none. A marker that cannot be read
    still means "refused"."""
    marker, err = kyaction.read_json(stamp_path(run, decision_id, "refused"))
    if err == "missing":
        return None
    return marker if isinstance(marker, dict) else {"reason": "refusal_marker_unreadable"}


def closed_as(run, decision_id, exe=None):
    """The state the handler closed a decision with itself — VETOED or FAILED, from its own marker
    $KY_RUN/veto/<id>.closed.json — or None: there is no usable marker, or the decision's `<id>.execute` record
    (`exe`) is INTENDED or DONE. Such a record overrules any closing: part of the effect may be, or all of it is,
    in place (ruling R14)."""
    if exe is not None and exe.get("state") != "FAILED":
        return None
    marker, err = kyaction.read_json(stamp_path(run, decision_id, "closed"))
    state = marker.get("state") if not err and isinstance(marker, dict) else None
    return state if state in ("VETOED", "FAILED") else None


# ───────────────────────────────────────── authority ─────────────────────────────────────────

def _bundle(commit, digest):
    if isinstance(commit, str) and HEX_COMMIT.match(commit) and isinstance(digest, str) and HEX64.match(digest):
        return {"source_commit": commit, "entrypoints_digest": digest}
    return None


def resolve_authority(env, commit=None, digest=None):
    """→ ({"source_commit", "entrypoints_digest"} | None, source). Arguments win (source "arguments"). Otherwise
    $KY_RUN/PLANNER_STATE.json `authorised_source` {source_commit, entrypoints_digest} (source "planner_state")
    — but only while no activation chain says otherwise: a chain that cannot be validated, or whose terminal
    link names another commit, makes the state file's answer stale ("activation_chain_invalid" /
    "planner_state_superseded"). None = unknown: decisions are held, never failed."""
    if commit is not None or digest is not None:
        bundle = _bundle(commit, digest)
        if bundle is None:
            raise ValueError("--authorised-commit (full commit id) and --entrypoints-digest (sha256) go together")
        return bundle, "arguments"
    state, _ = kyaction.read_json(env.run / "PLANNER_STATE.json")
    source = state.get("authorised_source") if isinstance(state, dict) else None
    bundle = _bundle(source.get("source_commit", source.get("commit")), source.get("entrypoints_digest")) \
        if isinstance(source, dict) else None
    if bundle is None:
        return None, "unknown"
    links, err = REGISTRY["plan_bundle_change"].chain(Ctx(env, None, None, None))
    if err:
        return None, "activation_chain_invalid"
    if links:
        head = links[-1][2]
        if head.get("new_commit", head.get("source_commit")) != bundle["source_commit"]:
            return None, "planner_state_superseded"
    return bundle, "planner_state"


def _authority(env, authorised):
    """tick/status argument → (bundle | None, source)."""
    if authorised is None:
        return resolve_authority(env)
    if authorised == UNKNOWN:
        return None, "unknown"
    if not isinstance(authorised, dict):
        raise ValueError("authorised must be {source_commit, entrypoints_digest}, kyveto.UNKNOWN or None")
    bundle = _bundle(authorised.get("source_commit"), authorised.get("entrypoints_digest"))
    if bundle is None:
        raise ValueError("authorised must carry a full source_commit and a sha256 entrypoints_digest")
    return bundle, "arguments"


def _git(env, repo, *args):
    """stdout of a read-only `git -C <repo> rev-parse …`, or None when git fails or cannot be run."""
    try:
        r = subprocess.run([env.git, "-C", str(repo), "rev-parse"] + list(args),
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
                           env={"PATH": env.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C",
                                "HOME": env.environ.get("HOME", "/nonexistent"), "GIT_CONFIG_NOSYSTEM": "1",
                                "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def default_source_repo(env):
    """DEFAULT_SOURCE_REPO iff that directory exists and git itself says it is the top level of a work tree
    (being merely inside another checkout does not count); otherwise None — never a guess."""
    path = DEFAULT_SOURCE_REPO
    if not isinstance(path, str) or not path or not os.path.isdir(path):
        return None
    top = _git(env, path, "--show-toplevel")
    if not top or os.path.realpath(top) != os.path.realpath(path):
        return None
    return path


def owner_decisions_blob(env, commit, path=None):
    """The blob id of the owner-decisions file (at `path`, default the configured one) at a full commit id, or
    None when it cannot be established."""
    repo, path = env.repo, env.owner_decisions_path if path is None else path
    if not repo or not isinstance(commit, str) or not HEX_COMMIT.match(commit) or not _repo_path(path):
        return None
    out = _git(env, repo, "--verify", "--quiet", "%s:%s" % (commit, path))
    return out if out and HEX_COMMIT.match(out) else None


def _repo_path(path):
    return isinstance(path, str) and bool(path) and not path.startswith("/") and ":" not in path \
        and not path.startswith("-") and "\n" not in path and ".." not in path.split("/")


# ───────────────────────────────────────── target classes ─────────────────────────────────────────

def _digest(path):
    """sha256 of a file, None when it does not exist; any other read error propagates (the state is unknown)."""
    try:
        with open(path, "rb") as f:
            return kyaction.sha_bytes(f.read())
    except FileNotFoundError:
        return None


def _text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(4096)
    except FileNotFoundError:
        return None


def _shown(text):
    return None if text is None else text.strip()[:32]


def _exact(path):
    """The whole text of a small file exactly as it is, None when it does not exist. ValueError when it is not
    UTF-8 or larger than a pool-size file ever is: such a file could not be put back exactly."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            text = f.read(4097)
    except FileNotFoundError:
        return None
    if len(text) > 4096:
        raise ValueError("%s is too large to be recorded and put back exactly" % Path(path).name)
    return text


class Capacity:
    """target {kind, builders, verifiers}: the pool sizes the dispatcher reads from KY_WORKERS / KY_VERIFIERS.
    The pair is one effect under one action record: `observer` calls it done only when BOTH files hold the
    requested values, and `execute` writes whichever of the two does not. Its "not_done" means "not complete",
    NOT "nothing happened": what is in place of an execution that will not be completed is judged by `effect`
    against the before values stored with the INTENDED record (`before`), and put back by `restore` (C3-01)."""
    kind = "capacity"
    merge_action = False
    FILES = (("builders", "KY_WORKERS"), ("verifiers", "KY_VERIFIERS"))

    def check(self, p):
        for key in sorted(set(p) - {"kind", "builders", "verifiers", "tracker_decision"}):
            return "unexpected key %s" % key
        for key, _ in self.FILES:
            v = p.get(key)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= CAPACITY_MAX[key]:
                return "%s must be an integer from 1 to %d" % (key, CAPACITY_MAX[key])
        return None

    def observed(self, p, ctx):                # fingerprint = current file contents + requested values
        return {name: _digest(ctx.env.run / name) for _, name in self.FILES}

    def precheck(self, p, ctx):
        return None

    def describe(self, p):
        return "capacity: KY_WORKERS → %d, KY_VERIFIERS → %d" % (p["builders"], p["verifiers"])

    def execute(self, p, ctx):
        result = {}
        for key, name in self.FILES:
            path, want = ctx.env.run / name, str(p[key])
            before = _text(path)
            written = before is None or before.strip() != want
            if written:
                kyaction.write_atomic(path, want + "\n")
            result[name] = {"before": _shown(before), "after": want, "written": written}
        return True, result

    def before(self, p, ctx):
        """The pair before anything is written: {file: its exact text, None when absent}. The handler stores it
        with the INTENDED record (inputs.before); a file that cannot be recorded exactly raises."""
        return {name: _exact(ctx.env.run / name) for _, name in self.FILES}

    def effect(self, p, ctx, before):
        """How much of this change is in place, judged against the recorded before values → (answer, detail):
        "absent"   every file holds exactly its recorded before content — nothing is in place
        "partial"  some file does not: detail.in_place names the files that now hold the requested value,
                   detail.foreign those that hold something else (neither the before value nor this change's)
        "unknown"  no before values were recorded with the action, or a file cannot be read."""
        if not isinstance(before, dict) or set(before) != {name for _, name in self.FILES} \
                or any(not (v is None or isinstance(v, str)) for v in before.values()):
            return "unknown", {"error": "before_values_not_recorded"}
        try:
            now = {name: _exact(ctx.env.run / name) for _, name in self.FILES}
        except (OSError, ValueError) as e:
            return "unknown", {"error": "unreadable: %s" % type(e).__name__}
        detail = {"before": {name: _shown(before[name]) for name in sorted(before)},
                  "observed": {name: _shown(now[name]) for name in sorted(now)}}
        changed = [(key, name) for key, name in self.FILES if now[name] != before[name]]
        if not changed:
            return "absent", detail
        ours = sorted(name for key, name in changed if now[name] is not None and now[name].strip() == str(p[key]))
        return "partial", dict(detail, in_place=ours, foreign=sorted(name for _, name in changed if name not in ours))

    def restore(self, p, ctx, before, names):
        """Put the named files back to their recorded before content (a file that did not exist is removed).
        The caller verifies the result with `effect`; nothing here is taken on trust."""
        for name in names:
            path = ctx.env.run / name
            if before[name] is None:
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
            else:
                kyaction.write_atomic(path, before[name])

    def observer(self, p, ctx):
        try:
            seen = {name: _text(ctx.env.run / name) for _, name in self.FILES}
        except (OSError, ValueError) as e:
            return "unknown", {"error": type(e).__name__}
        shown = {name: _shown(text) for name, text in seen.items()}
        if all(shown[name] == str(p[key]) for key, name in self.FILES):
            return "done", {"observed": shown, "reconciled": True}
        return "not_done", {"observed": shown, "incomplete": sorted(
            name for key, name in self.FILES if shown[name] != str(p[key]))}


class PlanBundleChange:
    """target {kind, old_commit, new_commit, old_manifest_digest, new_manifest_digest, new_manifest_path,
    review_receipts[]}: one more link of the activation chain (pairing rule KW-04, entrypoints KX-03). It
    authorises a bundle, never campaign admission."""
    kind = "plan_bundle_change"
    merge_action = False
    KEYS = {"kind", "old_commit", "new_commit", "old_manifest_digest", "new_manifest_digest", "new_manifest_path",
            "review_receipts", "tracker_decision"}

    def check(self, p):
        for key in sorted(set(p) - self.KEYS):
            return "unexpected key %s" % key
        for key in ("old_commit", "new_commit"):
            if not isinstance(p.get(key), str) or not HEX_COMMIT.match(p[key]):
                return "%s must be a full commit id" % key
        for key in ("old_manifest_digest", "new_manifest_digest"):
            if not isinstance(p.get(key), str) or not HEX64.match(p[key]):
                return "%s must be a sha256 digest" % key
        if not isinstance(p.get("new_manifest_path"), str) or not p["new_manifest_path"].strip():
            return "new_manifest_path must name the reviewed manifest file"
        receipts = p.get("review_receipts")
        if not isinstance(receipts, list) or not receipts or len(set(map(str, receipts))) != len(receipts) \
                or any(not isinstance(r, str) or not r.strip() for r in receipts):
            return "review_receipts must be a non-empty list of distinct paths"
        return None

    def _file(self, ctx, raw):
        path = Path(raw)
        return path if path.is_absolute() else ctx.env.run / path

    def _numbered(self, ctx):
        """{n: path} of ACTIVATION_RECORD.<n>.json, or a string naming a file that does not belong."""
        found = {}
        for path in sorted(ctx.env.run.glob("ACTIVATION_RECORD.*.json")):
            m = RECORD_NAME.match(path.name)
            if not m:
                return "unexpected file %s" % path.name
            found[int(m.group(1))] = path
        return found

    def chain(self, ctx):
        """→ ([(n, path, doc)], None) validated from its start, or (None, named reason).

        Every activation record is a link; the chain's root is the trust-root commit itself (no record). The
        un-numbered ACTIVATION_RECORD.json, when present, is link 0 and every numbered link chains after it:
        link 1 MUST name link 0 (file + sha256) as `previous`; a link 1 with `previous: null` beside it is a
        fork. Without link 0 a numbered-only chain is valid when link 1 has `previous: null`. Numbered links are
        contiguous from 1 and each names its predecessor's sha256."""
        found = self._numbered(ctx)
        if isinstance(found, str):
            return None, "activation_chain_invalid: %s" % found
        links, previous = [], None
        root = ctx.env.run / "ACTIVATION_RECORD.json"
        if os.path.lexists(root):
            doc, err = kyaction.read_json(root)
            if err or not isinstance(doc, dict):
                return None, "activation_chain_invalid: ACTIVATION_RECORD.json is unreadable"
            links.append((0, root, doc))
            previous = {"file": root.name, "sha256": kyaction.sha_file(root)}
        for n in range(1, len(found) + 1):
            if n not in found:                               # a gap: fewer files than the highest number
                return None, "activation_chain_invalid: ACTIVATION_RECORD.%d.json is missing from the sequence" % n
            doc, err = kyaction.read_json(found[n])
            if err or not isinstance(doc, dict) or doc.get("n") != n:
                return None, "activation_chain_invalid: %s is unreadable or misnumbered" % found[n].name
            if "previous" not in doc:
                return None, "activation_chain_invalid: %s states no `previous`" % found[n].name
            link = doc["previous"]
            if n == 1 and link is None and previous is not None:
                return None, ("activation_chain_fork: %s has no predecessor although ACTIVATION_RECORD.json exists"
                              % found[n].name)
            if link != previous:                             # None == None only for link 1 of a numbered-only chain
                return None, "activation_chain_invalid: %s does not chain to its predecessor" % found[n].name
            links.append((n, found[n], doc))
            previous = {"file": found[n].name, "sha256": kyaction.sha_file(found[n])}
        return links, None

    def observed(self, p, ctx):
        links, err = self.chain(ctx)
        head = {"error": err} if err else ({"file": links[-1][1].name, "sha256": kyaction.sha_file(links[-1][1])}
                                           if links else None)
        return {"chain_head": head,
                "manifest": {"path": p["new_manifest_path"],
                             "sha256": kyaction.sha_file(self._file(ctx, p["new_manifest_path"]))},
                "receipts": [{"path": raw, "sha256": kyaction.sha_file(self._file(ctx, raw))}
                             for raw in p["review_receipts"]]}

    def _manifest(self, p, ctx):
        """The successor manifest, checked → ({path, sha256, entrypoints, entrypoints_digest}, None) or
        (None, named reason)."""
        raw = p["new_manifest_path"]
        path = self._file(ctx, raw)
        doc, err = kyaction.read_json(path)
        if err == "missing":
            return None, "manifest_missing: %s" % raw
        if err or not isinstance(doc, dict):
            return None, "manifest_unreadable: %s" % raw
        try:
            digest = kyaction.sha_bytes(kyaction.canonical({k: v for k, v in doc.items() if k != "manifest_sha256"}))
        except (TypeError, ValueError, RecursionError):
            return None, "manifest_unreadable: %s" % raw
        if digest != p["new_manifest_digest"]:
            return None, "manifest_digest_mismatch: the recomputed digest of %s is not new_manifest_digest" % raw
        if "manifest_sha256" in doc and doc["manifest_sha256"] != digest:
            return None, "manifest_digest_mismatch: %s states a manifest_sha256 that is not its content's" % raw
        entrypoints = doc.get("entrypoints")
        if not isinstance(entrypoints, dict) or set(entrypoints) != set(ENTRYPOINT_ROLES):
            return None, "manifest_entrypoints_missing: %s needs exactly the roles %s" % (raw, ", ".join(ENTRYPOINT_ROLES))
        for role in ENTRYPOINT_ROLES:
            entry = entrypoints[role]
            if not isinstance(entry, dict) or not _repo_path(entry.get("path")) \
                    or not isinstance(entry.get("git_blob"), str) or not HEX_COMMIT.match(entry["git_blob"]):
                return None, ("manifest_entrypoints_missing: %s gives no repository-relative path and blob id for %s"
                              % (raw, role))
        named = doc.get("approved_source_commit", doc.get("source_commit"))
        if named != p["new_commit"]:                          # a manifest that names no source commit binds nothing
            return None, "manifest_not_for_new_commit: %s %s" % (
                raw, "names no source commit" if named is None else "is a manifest of another source commit")
        binding = {role: {"path": entrypoints[role]["path"], "git_blob": entrypoints[role]["git_blob"]}
                   for role in ENTRYPOINT_ROLES}
        digest = kyaction.sha_bytes(kyaction.canonical(binding))
        if "entrypoints_digest" in doc and doc["entrypoints_digest"] != digest:
            return None, ("manifest_entrypoints_digest_mismatch: %s states an entrypoints_digest that is not its "
                          "mapping's" % raw)
        return {"path": os.path.abspath(str(path)), "sha256": kyaction.sha_file(path), "entrypoints": binding,
                "entrypoints_digest": digest}, None

    def _receipts(self, p, ctx):
        """→ ([{path, sha256, verdict, reviewer_session_id, manifest_sha256}], None) or (None, named reason)."""
        if ctx.sessions is None:
            return None, "review_independence_unverifiable: the deciding session is not known"
        out = []
        for raw in p["review_receipts"]:
            path = self._file(ctx, raw)
            doc, err = kyaction.read_json(path)
            if err == "missing":
                return None, "review_receipt_missing: %s" % raw
            if err or not isinstance(doc, dict):
                return None, "review_receipt_unreadable: %s" % raw
            reviewer = doc.get("reviewer_session_id")
            if doc.get("verdict") != "ACCEPTED" or not isinstance(reviewer, str) or not reviewer.strip():
                return None, "review_receipt_not_accepted: %s" % raw
            if reviewer.strip() in {s.strip() for s in ctx.sessions}:
                return None, "review_receipt_not_independent: the reviewer of %s is the deciding session" % raw
            if doc.get("source_commit") != p["new_commit"]:
                return None, "review_receipt_not_bound: %s is not a review of new_commit" % raw
            if doc.get("manifest_sha256") != p["new_manifest_digest"]:
                return None, "review_receipt_not_bound: %s does not carry new_manifest_digest" % raw
            if not isinstance(doc.get("inputs"), dict) or not doc["inputs"]:
                return None, "review_receipt_without_inputs: %s names nothing it reviewed" % raw
            out.append({"path": os.path.abspath(str(path)), "sha256": kyaction.sha_file(path), "verdict": "ACCEPTED",
                        "reviewer_session_id": reviewer, "manifest_sha256": doc["manifest_sha256"]})     # C4-04
        return out, None

    def _verify(self, p, ctx):
        """→ (facts, None) when this change may be activated now, else (None, named reason)."""
        if p["old_commit"] != ctx.authority.get("source_commit"):
            return None, "old_commit_not_authorised_source"
        receipts, reason = self._receipts(p, ctx)
        if reason:
            return None, reason
        manifest, reason = self._manifest(p, ctx)
        if reason:
            return None, reason
        links, err = self.chain(ctx)
        if err:
            return None, err                                  # activation_chain_invalid / activation_chain_fork
        head = links[-1] if links else None                   # the true terminal link (link 0 if it is the only one)
        if head is not None:
            doc = head[2]
            if doc.get("new_commit", doc.get("source_commit")) != p["old_commit"]:
                return None, "activation_chain_mismatch: the previous record's new_commit is not old_commit"
            if doc.get("new_manifest_digest", doc.get("final_manifest_digest")) != p["old_manifest_digest"]:
                return None, ("activation_chain_mismatch: the previous record's manifest digest is not "
                              "old_manifest_digest")
        mapped = manifest["entrypoints"]["owner_decisions"]
        old_blob = owner_decisions_blob(ctx.env, p["old_commit"])
        new_blob = owner_decisions_blob(ctx.env, p["new_commit"], mapped["path"])
        if old_blob is None or new_blob is None:
            return None, "owner_decisions_unverifiable"
        if old_blob != new_blob:
            return None, "owner_decisions_changed_owner_only"
        if mapped["git_blob"] != new_blob:
            return None, "manifest_entrypoint_mismatch: owner_decisions is not the blob at new_commit"
        return {"receipts": receipts, "manifest": manifest, "head": head, "old_blob": old_blob,
                "new_blob": new_blob, "new_path": mapped["path"]}, None

    def precheck(self, p, ctx):
        return self._verify(p, ctx)[1]

    def describe(self, p):
        return "authorised bundle: %s → %s (next activation record)" % (p["old_commit"][:12], p["new_commit"][:12])

    def _mine(self, p, ctx):
        """The record this decision already wrote: (result, None), (None, None) when there is none, or
        (None, why) when a record names this decision but is not this change."""
        found = self._numbered(ctx)
        for n, path in sorted(found.items()) if isinstance(found, dict) else []:
            doc, err = kyaction.read_json(path)
            act = doc.get("authorising_act") if isinstance(doc, dict) else None
            if isinstance(act, dict) and act.get("id") == ctx.decision_id:
                if err or any(doc.get(k) != p[k] for k in ("old_commit", "new_commit", "old_manifest_digest",
                                                           "new_manifest_digest")):
                    return None, "%s names this decision but records another change" % path.name
                return {"file": path.name, "path": str(path), "n": n, "sha256": kyaction.sha_file(path)}, None
        return None, None

    def execute(self, p, ctx):
        mine, conflict = self._mine(p, ctx)
        if conflict:
            return False, {"reason": "activation_record_conflict: %s" % conflict}
        if mine:
            return True, mine                                 # idempotent: the same decision, the same record
        facts, reason = self._verify(p, ctx)
        if reason:
            return False, {"reason": reason}
        head, manifest = facts["head"], facts["manifest"]
        n = (head[0] if head else 0) + 1
        path = ctx.env.run / ("ACTIVATION_RECORD.%d.json" % n)
        doc = {"schema": "ky.activation_record/1", "n": n,
               "previous": {"file": head[1].name, "sha256": kyaction.sha_file(head[1])} if head else None,
               "old_commit": p["old_commit"], "new_commit": p["new_commit"],
               "old_manifest_digest": p["old_manifest_digest"], "new_manifest_digest": p["new_manifest_digest"],
               "new_manifest": {"path": manifest["path"], "sha256": manifest["sha256"],
                                "entrypoints_digest": manifest["entrypoints_digest"]},
               "review_receipts": facts["receipts"],
               "owner_decisions": {"path": ctx.env.owner_decisions_path, "new_path": facts["new_path"],
                                   "old_blob": facts["old_blob"], "new_blob": facts["new_blob"]},
               "authorising_act": {"kind": "surrogate_decision", "id": ctx.decision_id},
               "campaign_admission": False, "created_at": ctx.now or kyaction.utc(), "created_by": HANDLER}
        if not kyaction.write_exclusive(path, json.dumps(doc, ensure_ascii=False, indent=1) + "\n", mode=0o444):
            return False, {"reason": "activation_chain_mismatch: %s was written by another actor" % path.name}
        return True, {"file": path.name, "path": str(path), "n": n, "sha256": kyaction.sha_file(path)}

    def observer(self, p, ctx):
        mine, conflict = self._mine(p, ctx)
        if conflict:
            return "unknown", {"error": conflict}
        return ("done", mine) if mine else ("not_done", {"activation_record_for": ctx.decision_id, "found": False})


class Unavailable:
    """A veto class whose executor is a later deliverable. It fails closed, in the recheck and again if it were
    ever reached: a helper's mere presence is not an executor, and no success is ever reported."""
    merge_action = False

    def __init__(self, kind, helper, evidence=()):
        self.kind, self.helper, self.evidence = kind, helper, tuple(evidence)

    def check(self, p):
        return None

    def observed(self, p, ctx):
        return {name: _digest(ctx.env.run / name) for name in self.evidence}

    def _reason(self, ctx):
        if not (ctx.env.fleet / self.helper).is_file():
            return "executor_unavailable: %s" % self.helper
        return "executor_unavailable: the %s executor is a later deliverable; %s alone executes nothing" % (
            self.kind, self.helper)

    def precheck(self, p, ctx):
        return self._reason(ctx)

    def describe(self, p):
        return "%s (no executor installed)" % self.kind

    def execute(self, p, ctx):
        return False, {"reason": self._reason(ctx)}

    def observer(self, p, ctx):
        return "unknown", {"error": self._reason(ctx)}


REGISTRY = {
    "capacity": Capacity(),
    "plan_bundle_change": PlanBundleChange(),
    "campaign_start": Unavailable("campaign_start", "kygate.sh", ("RELEASE_RECEIPT.json", "VERSIONS.json")),
    "protected_window": Unavailable("protected_window", "executor.py"),
}


def bind(target):
    """→ (class, params) of a target, or TargetError with the named refusal. params = target without fingerprint."""
    if not isinstance(target, dict):
        raise TargetError("target_unbound")
    cls = REGISTRY.get(target["kind"]) if isinstance(target.get("kind"), str) else None
    if cls is None:
        raise TargetError("unknown_target_kind")
    params = {k: v for k, v in target.items() if k != "fingerprint"}
    problem = cls.check(params)
    if problem:
        raise TargetError("target_malformed: %s" % problem)
    return cls, params


def fingerprint(target, env, ctx=None):
    """sha256 over the target's parameters (everything but `fingerprint`) and the class's view of the disk state
    it depends on. The surrogate records it at proposal; the handler recomputes it at expiry."""
    cls, params = bind(target)
    try:
        observed = cls.observed(params, ctx or Ctx(env, None, None, None))
        return kyaction.sha_bytes(kyaction.canonical(
            {"schema": "ky.target_fingerprint/1", "target": params, "observed": observed}))
    except (OSError, TypeError, ValueError, RecursionError) as e:
        raise TargetError("target_unreadable: %s" % type(e).__name__) from None


def tracker_decision(params):
    """→ None (nothing to publish) or {"id", "outcome"}; TargetError when it cannot be published exactly."""
    td = params.get("tracker_decision")
    if td is None:
        return None
    if not isinstance(td, dict) or set(td) != {"id", "outcome"} or not isinstance(td["id"], str) \
            or not TRACKER_ID.match(td["id"]) or not isinstance(td["outcome"], str) \
            or not TRACKER_OUTCOME.match(td["outcome"]):
        raise TargetError("tracker_decision_malformed: need {id: D-…, outcome: <token>}")
    return td


def named_tracker_decision(item):
    """The tracker decision an awaiting item names, or None when it names none: its `item` when that is a tracker
    decision id (D-…), or a `tracker_decision` it carries (the id, or {"id": …})."""
    for value in (item.get("tracker_decision"), item.get("item")):
        if isinstance(value, dict):
            value = value.get("id")
        if isinstance(value, str) and TRACKER_ID.match(value):
            return value
    return None


# ───────────────────────────────────────── publication ─────────────────────────────────────────

def run_ky(argv, env):
    """Run the tracker CLI once. → ("exited", rc, text) | ("not_started", None, why) | ("unknown", None, why).
    "unknown" (killed, timed out) is NOT a failure: whether the tracker recorded the decision is not known."""
    child = {k: env.environ[k] for k in KY_ENV_NAMES if k in env.environ}
    child.update(KY_ROOT=str(env.root), KY_RUN=str(env.run), KY_FLEET=str(env.fleet))
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=env.ky_timeout, env=child,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return "unknown", None, "no exit status within %gs" % env.ky_timeout
    except OSError as e:
        return "not_started", None, "ky could not be started: %s" % type(e).__name__
    if r.returncode < 0:
        return "unknown", None, "terminated by signal %d" % -r.returncode
    return "exited", r.returncode, kyaction.flat(r.stderr or r.stdout, 300)


def _no_tracker_readback(record):
    return "unknown", "no tracker readback is available to this handler"


def _nothing_was_published(record):
    return "not_done", "this record publishes nothing: there is no outside effect to observe"


def _own(record):
    actor = record.get("actor")
    return isinstance(actor, dict) and actor.get("role") == "veto" \
        and actor.get("holder_kind") in ("controller", "supervisor")


def _abandoned(record):
    """True for an INTENDED record nobody is known to be carrying out: the process that began it is gone, is this
    very process, was never recorded, or cannot be judged at all."""
    if record is None or record.get("state") != "INTENDED":
        return False
    process = record.get("process") if isinstance(record.get("process"), dict) else {}
    alive = kyaction.process_matches(process.get("pid"), process.get("process_start"))
    return not (alive is True and process.get("pid") != os.getpid())


def publication(record):
    """Does the tracker hold the delegated decision of this `<id>.publish` record? Three answers, never two:
    True     the record names a tracker decision and is DONE (`ky decide` exited 0, or a readback saw it)
    False    there is no record (the handler never began), the record names no tracker decision, or it is FAILED
             with `result.published` exactly false (`ky` was never started, or a readback proved nothing is held)
    UNKNOWN  everything else — an unfinished record, a failure nothing read back, a record that cannot be judged."""
    if record is None:
        return False
    target = record.get("target")
    if not isinstance(target, dict) or "tracker_decision" not in target:
        return UNKNOWN
    if target["tracker_decision"] is None:
        return False
    if record.get("state") == "DONE":
        return True
    result = record.get("result")
    if record.get("state") == "FAILED" and isinstance(result, dict) and result.get("published") is False:
        return False
    return UNKNOWN


def _effective_at(record):
    """When the handler made a decision effective, from its DONE publication record."""
    at = (record.get("result") or {}).get("effective_at")
    return at if kyaction.parse_utc(at) is not None else record.get("completed_at")


# ───────────────────────────────────────── the handler ─────────────────────────────────────────

class Handler:
    def __init__(self, env, now, authorised, holder, holder_kind, publish_observer, log):
        self.env, self.now, self.now_iso = env, now, kyaction.utc(now)
        self.authorised, self.holder, self.publish_observer = authorised, holder, publish_observer
        self.actor = {"role": "veto", "holder_kind": holder_kind, "controller_id": holder}
        self.applier = {"holder_kind": holder_kind, "controller_id": holder}
        self.log_path = env.run / "DECISIONS_SURROGATE.jsonl"
        self.log = log or (lambda text: print("kyveto: %s" % text, file=sys.stderr))
        self.commands = []
        self.late = []                       # rows of decisions an owner veto reached too late (sweep)
        self.authority_held = []

    # ---- small readers
    def holds(self):
        out = []
        if os.path.lexists(self.env.root / "HOLD"):
            out.append("HOLD")
        if os.path.lexists(self.env.run / "STOP_veto"):
            out.append("STOP_veto")
        pause = kycommands.pause_state(self.env.run)
        if pause["state"] == "unknown":
            out.append("command_queue_unreadable")
        elif pause["state"] == "paused":
            out.append("owner_paused")
        elif pause["pending_pause"]:
            out.append("owner_pause_pending")
        return out

    def commands_about(self, name, key, value):
        return [e for e in kycommands.scan(self.env.run)[0]
                if not e["invalid"] and e["doc"]["command"] == name and e["doc"]["state"] in ("QUEUED", "APPLIED")
                and e["doc"]["args"].get(key) == value]

    def veto_command(self, did):
        found = self.commands_about("veto", "decision_id", did)
        return found[0] if found else None

    def memory(self, did):
        """The handler's own action records of a decision → (publish record | None, execute record | None).
        A record under one of these ids that the veto role did not write is not memory: Foreign."""
        out = []
        for which in ("publish", "execute"):
            record = kyaction.peek(self.env.run, "%s.%s" % (did, which))
            if record is not None and not _own(record):
                raise Foreign("%s.%s was not written by the veto role" % (did, which))
            out.append(record)
        return out[0], out[1]

    def terminal(self, did, lines, pub, exe):
        """first_terminal by the handler's own memory of the decision: its two action records and its closing."""
        return first_terminal(lines, _done(exe), pub is not None or exe is not None,
                              closed_as(self.env.run, did, exe))

    def state_of(self, did, lines):
        """A decision's state as the handler accepts it: its terminal state when it has one, else its latest."""
        try:
            finished = self.terminal(did, lines, *self.memory(did))
        except kyaction.ActionError:
            finished = first_terminal(lines, False)
        return (finished if in_domain(lines) else None) or _state(lines[-1])

    def candidate(self, did, lines):
        if read_refusal(self.env.run, did) is not None:
            return False
        try:
            pub, exe = self.memory(did)
            return needs_handler(lines, _done(exe), pub is not None or exe is not None,
                                 closed_as(self.env.run, did, exe))
        except kyaction.ActionError:
            return bool(lines) and in_domain(lines)          # unreadable memory: let the decision's pass report it

    # ---- writers
    def line(self, latest, state, reason, effective_at=None, detail=None):
        line = {k: latest[k] for k in BASE_FIELDS if k in latest}
        line["effective_at"] = effective_at          # the handler's own knowledge, never a value copied from the log
        line.update(state=state, by=HANDLER, reason=reason, at=self.now_iso, session=self.holder)
        if detail:
            line["detail"] = detail
        return line

    def append(self, latest, state, reason, effective_at=None, detail=None):
        """Append one transition line — never one the decision schema would refuse (Unwritable instead)."""
        line = self.line(latest, state, reason, effective_at, detail)
        problem = line_problem(line)
        if problem:
            raise Unwritable("%s: a %s line was not written (%s)" % (line.get("id"), state, problem))
        append_line(self.log_path, line)
        return line

    def published(self, did):
        """`publication` of the decision's own record, after ONE readback of an unfinished one (recorded in its
        reconciliations[]): a readback that proves nothing is held closes the record as not published; one that
        cannot say — or none at all — leaves it unfinished and the answer UNKNOWN."""
        run, action_id = self.env.run, did + ".publish"
        record = self.memory(did)[0]
        if publication(record) == UNKNOWN and record.get("state") == "INTENDED" and not kyaction.in_progress(record):
            outcome, record = kyaction.reconcile(run, action_id, self.publish_observer or _no_tracker_readback,
                                                 by=self.holder)
            if outcome == "not_done":
                record = kyaction.fail(run, action_id, {"published": False, "reason": "readback: not published"})
        return publication(record)

    def close(self, did, state, reason):
        """The handler's own memory of having brought a decision to VETOED or FAILED: $KY_RUN/veto/<id>.closed.json,
        written AFTER its line and only for a decision it holds an action record for — there a line alone, whoever
        wrote it, never ends the handler's custody (R14). A crash between the line and the marker leaves a line
        the next tick answers once more, with attention; never a closing nobody was told of."""
        pub, exe = self.memory(did)
        if pub is None and exe is None:
            return
        path = stamp_path(self.env.run, did, "closed")
        os.makedirs(path.parent, exist_ok=True)
        marker = {"closed_at": self.now_iso, "state": state, "reason": reason, "by": self.holder}
        kyaction.write_atomic(path, json.dumps(marker, indent=1, sort_keys=True) + "\n", mode=0o444)

    def busy(self, record, what):
        """Another process began this action and has not finished it: `locked`, come back later. When that process
        cannot be told alive or gone (`ps` does not answer, no start identity to compare), later may never come
        by itself: the row then carries attention (R16) — still nothing is repeated, reconciled or failed."""
        row = {"outcome": "locked", "reason": "%s_in_progress" % what}
        process = record.get("process") if isinstance(record.get("process"), dict) else {}
        if kyaction.process_matches(process.get("pid"), process.get("process_start")) is None:
            row.update(attention=True, owner=UNKNOWN)
        return row

    def give_up(self, did, result):
        """What stands of a decision's execution when the handler is about to give the decision up — an owner
        veto, a check that failed, a record it cannot answer, a terminal line it did not write? Its own
        `<id>.execute` record answers, and an INTENDED one is never left behind (C3-01, C4-01 / R14): it is
        reconciled against the disk, and what is in place of an incomplete effect is put back and verified, or
        recorded as it is (`undo`), before the record is closed FAILED with `result(state)` — the result for the
        state `undo` found: absent | restored | in_place. The target and the before values are the record's
        own, never the log's. → (row, executed, partial):
          row       not None: the decision cannot be given up now, and nothing was closed — another process may
                    be executing it (`locked`), or what is in place cannot be judged (`blocked`, with attention,
                    on every tick)
          executed  True: the effect is completely in place (the record is DONE — it was, or the disk showed it)
          partial   what `undo` found and the FAILED record holds (None: positively nothing is in place)."""
        run, action_id = self.env.run, did + ".execute"
        record = self.memory(did)[1]
        if record is None:
            return None, False, None
        if record["state"] == "INTENDED":
            if kyaction.in_progress(record):                 # another live process may be executing it right now
                return self.busy(record, "execution"), False, None
            blocked = {"outcome": "blocked", "reason": "execution_unreconciled", "attention": True}
            try:
                cls, params = bind(record.get("target"))
            except TargetError:
                return blocked, False, None
            ctx = Ctx(self.env, did, (record.get("inputs") or {}).get("authority"), self.now_iso)
            outcome, record = kyaction.reconcile(run, action_id, lambda r: cls.observer(params, ctx), by=self.holder)
            if outcome == "unknown":
                return blocked, False, None
            if outcome == "not_done":                        # "not complete" — what IS in place is looked at now
                state, partial = self.undo(cls, params, ctx, record)
                if state == UNKNOWN:         # neither "nothing happened" nor what did can be recorded
                    return dict(blocked, reason="execution_unreconciled: %s" % kyaction.flat(
                        partial.get("error") or "the effect in place cannot be judged", 120)), False, None
                closing = dict(result(state))
                if partial:
                    closing["partial_effect"] = partial
                record = kyaction.fail(run, action_id, closing)
        if _done(record):
            return None, True, None
        partial = (record.get("result") or {}).get("partial_effect")
        return None, False, partial if isinstance(partial, dict) and partial else None

    def failed(self, did, latest, reason, effective_at=None, published=None, partial=None):
        """FAILED, always with attention: the owner is told of every decision that did not go through.
        `published`: the three-valued answer when the caller has just read it back; otherwise it is read here.
        `partial`: what `undo` found of an execution that was not completed (None: positively nothing).
        No decision is called FAILED past its own execution record (`give_up`): an INTENDED `<id>.execute` is
        closed first — or the row says why it cannot be (`giving_up` names what was about to be said) — and a
        DONE one makes the decision EXECUTED instead (`stands`)."""
        row, executed, left = self.give_up(did, lambda state: {"reason": GIVEN_UP[state], "because": reason})
        if row:
            return dict(row, giving_up=reason)
        if executed:
            return self.stands(did, latest, reason, effective_at)
        partial = partial or left
        published = self.published(did) if published is None else published
        detail = {} if published is False else {"published": published}
        if partial:
            detail["partial_effect"] = partial
        self.append(latest, "FAILED", reason, effective_at, detail or None)
        self.close(did, "FAILED", reason)
        out = {"outcome": "failed", "reason": reason, "attention": True}
        if published is not False:           # the tracker holds, or may hold, a decision that was not carried out
            out["published"] = published
        if partial:                          # part of the effect was, or still is, in place
            out["partial_effect"] = partial.get("state", UNKNOWN)
        return out

    def stands(self, did, latest, reason, effective_at=None):
        """The decision was about to be given up (`reason`), but the handler's own `<id>.execute` record is DONE:
        the effect is in place, so the decision is EXECUTED. The handler says so in the log from its own memory
        and reports it with attention: what was about to be said (`instead_of`) is the owner's to look at."""
        pub = self.memory(did)[0]
        effective_at = effective_at or (_effective_at(pub) if _done(pub) else None)
        self.append(latest, "EXECUTED", "executed", effective_at, {"action": did + ".execute",
                                                                   "already_executed": reason})
        out = {"outcome": "executed", "reason": "already_executed", "instead_of": reason, "attention": True,
               "executed": True}
        published = self.published(did)
        if published is not False:
            out["published"] = published
        return out

    def undo(self, cls, params, ctx, record):
        """What is left of an execution that will not be completed (an owner veto, a failed executor), judged
        against the before values of its own INTENDED record → (state, partial):
          "absent"    observed: nothing is in place (partial None). A class without `effect` writes its effect in
                      one step, so its observer's "not_done" already is that observation
          "restored"  part of the effect was in place, consisted only of this change's own values, was put back
                      and a SECOND look found the recorded before values
          "in_place"  part of the effect is in place and was not (or could not be) put back
          "unknown"   it cannot be told (no before values recorded, an unreadable file)
        `partial` = {"state", …evidence} for every state but "absent"; it goes into the action record's result,
        the decision line's detail and the row, and `status` keeps an unrestored one unresolved."""
        if not hasattr(cls, "effect"):
            return "absent", None
        before = (record.get("inputs") or {}).get("before")
        answer, detail = cls.effect(params, ctx, before)
        if answer == "absent":
            return "absent", None
        if answer == "partial" and detail["in_place"] and not detail["foreign"]:
            names = detail["in_place"]
            try:
                cls.restore(params, ctx, before, names)
            except (OSError, ValueError) as e:
                detail = dict(detail, restore_error=type(e).__name__)
            answer, after = cls.effect(params, ctx, before)          # verified, never assumed
            if answer == "absent" and "restore_error" not in detail:
                return "restored", {"state": "restored", "restored": names, "before": detail["before"],
                                    "was": detail["observed"], "observed": after["observed"]}
            detail = dict(detail, after_restore=after)
        state = "in_place" if answer == "partial" else UNKNOWN
        return state, dict(detail, state=state)

    def refuse(self, did, reason, published=False):
        """A record the handler cannot answer in the log: nothing is appended; the refusal is the handler's own
        marker, written once, and reported once with attention. `published`: True, False or UNKNOWN.
        A refusal gives the decision up like any other exit (`give_up`): an INTENDED `<id>.execute` is closed
        first (or the row says why it cannot be, and nothing is refused yet), and the marker and the row say
        what stands of the execution — `executed`, or the `partial_effect` that record holds."""
        row, executed, partial = self.give_up(did, lambda state: {"reason": GIVEN_UP[state],
                                                                  "because": "refused: %s" % reason})
        if row:
            return dict(row, giving_up="refused: %s" % reason)
        path = stamp_path(self.env.run, did, "refused")
        os.makedirs(path.parent, exist_ok=True)
        marker = {"refused_at": self.now_iso, "reason": reason, "published": published, "by": self.holder}
        out = {"outcome": "refused", "reason": reason, "attention": True}
        if published is not False:
            out["published"] = published
        if executed:                         # the effect is in place, whatever the record says now
            marker["executed"] = out["executed"] = True
        if partial:                          # part of the effect was, or still is, in place
            marker["partial_effect"], out["partial_effect"] = partial, partial.get("state", UNKNOWN)
        kyaction.write_exclusive(path, json.dumps(marker, indent=1, sort_keys=True) + "\n", mode=0o444)
        return out

    def settle(self, entry, result=None, reject=None):
        """Mark an owner command applied (or rejected) as the fenced owner of the veto role; never twice."""
        if entry["doc"]["state"] != "QUEUED":
            return

        def handler(command):
            if reject:
                raise kycommands.Reject(reject)
            return result

        status, doc = kycommands.apply(self.env.run, entry["doc"]["id"], self.applier, handler, in_order=False,
                                       log=self.log)
        note = {"id": entry["doc"]["id"], "command": entry["doc"].get("command"), "status": status}
        if status in ("refused", "unreconciled"):
            note.update(reason=doc.get("reason"), attention=True)
        elif status == "rejected":
            note["reason"] = (doc.get("result") or {}).get("reason")
        self.commands.append(note)

    # ---- one decision, under its lock
    def guarded(self, did):
        try:
            lock = kyaction.acquire_lock(self.env.run, "decision." + did, self.holder, log=self.log)
        except kyaction.LockUnknown as e:
            return {"id": did, "outcome": "blocked", "reason": "lock_owner_unknown: %s" % kyaction.flat(e, 200),
                    "attention": True}
        if lock is None:
            return {"id": did, "outcome": "locked"}
        try:
            try:
                out = self.process(did)
            except Unwritable as e:          # a record that cannot be answered in the log after all: refused instead
                out = self.refuse(did, "record_unanswerable: %s" % kyaction.flat(e, 160), self.published(did))
        except Exception as e:               # one decision's trouble never ends the pass: blocked, with attention
            out = {"outcome": "blocked", "reason": "error: %s: %s" % (type(e).__name__, kyaction.flat(e, 160)),
                   "attention": True}
        finally:
            kyaction.release_lock(lock)
        return dict(out, id=did)

    def process(self, did):
        history, problems, unusable = load_decisions(self.log_path)       # the fresh handled-state check
        if problems or did in unusable:
            return {"outcome": "blocked", "reason": "decision_log_unreadable", "attention": True}
        lines = history.get(did) or []
        if not self.candidate(did, lines):
            return {"outcome": "not_pending", "state": _state(lines[-1]) if lines else None}
        awaiting, aw_lock = lines[-1].get("awaiting"), None
        if isinstance(awaiting, str) and AW_RE.match(awaiting):
            try:
                aw_lock = kyaction.acquire_lock(self.env.run, "awaiting." + awaiting, self.holder, log=self.log)
            except kyaction.LockUnknown as e:
                return {"outcome": "blocked", "reason": "lock_owner_unknown: %s" % kyaction.flat(e, 200),
                        "attention": True}
            if aw_lock is None:
                return {"outcome": "locked", "reason": "awaiting_item_locked"}
        try:
            return self.decide(did, lines, history)
        finally:
            if aw_lock is not None:
                kyaction.release_lock(aw_lock)

    def decide(self, did, lines, history):
        """One decision under its locks. A line that stepped back behind an earlier one (C3-02) changes nothing
        — the decision carries on from the proposal, the stamp and the action records — but it is an anomaly
        the row reports with attention."""
        out = self.judge(did, lines, history)
        if regressed(lines) and "anomaly" not in out:
            out = dict(out, anomaly=REGRESSED, attention=True)
        return out

    def judge(self, did, lines, history):
        latest, proposal = lines[-1], proposal_of(lines)
        pub, exe = self.memory(did)
        effective_at = _effective_at(pub) if _done(pub) else None
        problem = base_problem(latest) or (base_problem(proposal) if proposal is not None else None)
        if problem:                                           # (0) nothing this handler could write would be valid
            return self.refuse(did, problem, publication(pub))
        finished = self.terminal(did, lines, pub, exe)        # (1) a later line never resurrects a finished decision
        if finished:
            self.append(latest, finished, "terminal_state_is_final", effective_at)
            return {"outcome": finished.lower(), "reason": "terminal_state_is_final", "attention": True,
                    "anomaly": "line_appended_after_terminal_state"}
        claim = claimed(lines)
        if claim:                                             # … and a line never ends the handler's custody (R14):
            veto = self.veto_command(did)                     # the handler closes what it began, then says so itself
            out = self.vetoed(did, latest, veto, effective_at) if veto \
                else self.failed(did, latest, "closed_by_log_line: %s" % claim, effective_at)
            pub, exe = self.memory(did)
            return dict(out, anomaly=CLAIMED, attention=True, published=publication(pub), executed=_done(exe))
        for claim, backed in (("EFFECTIVE", _done(pub)), ("EXECUTED", _done(exe))):
            if not backed and any(_state(line) == claim for line in lines):
                return dict(self.failed(did, latest, "log_claims_%s_without_action_record" % claim.lower(),
                                        effective_at), anomaly="log_claim_without_action_record")
        if proposal is None:
            return self.failed(did, latest, "proposal_missing", effective_at)
        stamp, problem = first_seen(self.env.run, did, proposal, self.now)       # (2)
        if problem:
            return {"outcome": "blocked", "reason": problem, "attention": True}
        if stamp["proposal_line_sha256"] != proposal_sha(proposal):
            return self.failed(did, latest, "decision_record_mutated: proposal", effective_at)
        veto = self.veto_command(did)
        if veto:                                              # (3) the owner's veto wins, also at and after expiry
            return self.vetoed(did, latest, veto, effective_at)
        if pub is None:                                       # (4) the handler has not begun to make it effective
            deadline = kyaction.parse_utc(proposal.get("veto_deadline"))
            if deadline is None:
                return self.failed(did, latest, "veto_deadline_unreadable")
            if proposal["notification"].get("submitted") is not True:
                return self.failed(did, latest, "notification_not_submitted")
            notified, problem = notified_at(self.env.run, did)
            if problem:
                return {"outcome": "blocked", "reason": problem, "attention": True}
            if notified is None:
                return self.failed(did, latest, "notification_unverified")
            seen = kyaction.parse_utc(stamp["first_seen_at"])
            not_before = max(max(seen, notified) + VETO_WINDOW_S, deadline)
            if self.now < not_before:
                at = kyaction.utc(math.ceil(not_before))
                return {"outcome": "pending", "seconds_remaining": int(math.ceil(not_before - self.now)),
                        "veto_deadline": at, "effective_not_before": at,
                        "record_veto_deadline": proposal["veto_deadline"], "first_seen_at": stamp["first_seen_at"],
                        "notified_at": kyaction.utc(notified)}
        held = self.holds()                                   # (5)
        if held:
            return {"outcome": "held", "reasons": held}
        ctx = Ctx(self.env, did, latest["authority"], self.now_iso,
                  sessions=[x for line in lines for x in (line.get("session"), line.get("by")) if isinstance(x, str)])
        if not (_done(pub) and exe is not None):              # (6) — once execution has begun the disk is ours
            verdict = self.recheck(did, lines, history, ctx)
            if verdict == "authority_unknown":
                self.authority_held.append(did)
                return {"outcome": "held", "reasons": ["authority_unknown"]}
            if verdict:
                return self.failed(did, latest, verdict, effective_at)
        try:
            cls, params = bind(latest.get("target"))
            td = tracker_decision(params)
        except TargetError as e:
            return {"outcome": "blocked", "reason": "execution_unreconciled: %s" % e.reason, "attention": True}
        veto = self.veto_command(did)                         # a last look before anything is published
        if veto:
            return self.vetoed(did, latest, veto, effective_at)
        held = self.holds()                                   # … also at the holds: the recheck took its time (C4-05)
        if held:
            return {"outcome": "held", "reasons": held}
        out = self.publish(did, latest, td, effective_at)     # (7) publish …
        if out:
            return out
        pub, _ = self.memory(did)
        effective_at = _effective_at(pub)
        if not any(_state(line) == "EFFECTIVE" for line in lines):
            latest = self.append(latest, "EFFECTIVE", "veto_window_expired_unvetoed", effective_at,
                                 {"publication": did + ".publish", "published": td is not None})
        veto = self.veto_command(did)                         # a last look before anything is executed
        if veto:
            return self.vetoed(did, latest, veto, effective_at)
        held = self.holds()                  # a HOLD or pause placed while `ky decide` ran stops the execution
        if held:
            return {"outcome": "held", "reasons": held}
        out = self.execute(did, latest, cls, params, ctx, effective_at)     # … then execute
        if out:
            return out
        self.append(latest, "EXECUTED", "executed", effective_at, {"action": did + ".execute"})
        return {"outcome": "executed"}

    def vetoed(self, did, latest, veto, effective_at):
        action_id, command_id = did + ".execute", veto["doc"]["id"]
        row, executed, partial = self.give_up(did, lambda state: {"command": command_id, "reason": {
            "absent": "vetoed_before_execution", "restored": "vetoed_partial_effect_restored",
            "in_place": "vetoed_with_partial_effect"}[state]})
        if row:                              # locked or blocked: the veto is settled when the execution is known
            return row
        if executed:                                          # the effect is already in place: the veto is too late
            self.append(latest, "EXECUTED", "executed", effective_at, {"action": action_id,
                                                                       "veto_too_late": command_id})
            self.settle(veto, reject="too_late: decision %s was already executed" % did)
            return {"outcome": "executed", "reason": "veto_too_late", "attention": True}
        published = self.published(did)      # True, False or UNKNOWN — unknown is never "not published"
        detail = {"command": command_id, "published": published}
        if partial:
            detail["partial_effect"] = partial
        self.append(latest, "VETOED", "owner_veto", effective_at, detail)
        self.close(did, "VETOED", "owner_veto")
        self.settle(veto, result={"decision": did, "outcome": "VETOED"})
        out = {"outcome": "vetoed", "command": command_id}
        if published is not False:           # the tracker decision is out, or may be, and contradicts the owner
            out.update(attention=True, published=published)
        if partial:                          # part of what the owner vetoed was, or still is, in place
            out.update(attention=True, partial_effect=partial.get("state", UNKNOWN))
        return out

    def recheck(self, did, lines, history, ctx):
        """None when the decision may be published and executed now; "authority_unknown" when it has to be held;
        otherwise the named reason it is FAILED."""
        latest = lines[-1]
        for field in FIXED_FIELDS:
            if any(kyaction.canonical(line.get(field)) != kyaction.canonical(latest.get(field)) for line in lines):
                return "decision_record_mutated: %s" % field
        window = lines[lines.index(proposal_of(lines)):]
        for field in WINDOW_FIELDS:
            if any(kyaction.canonical(line.get(field)) != kyaction.canonical(latest.get(field)) for line in window):
                return "decision_record_mutated: %s" % field
        authority = latest.get("authority")
        if not isinstance(authority, dict) or _bundle(authority.get("source_commit"),
                                                      authority.get("entrypoints_digest")) is None:
            return "authority_unbound"
        if self.authorised is None:
            return "authority_unknown"
        if _bundle(authority["source_commit"], authority["entrypoints_digest"]) != self.authorised:
            return "authority_changed"
        try:
            cls, params = bind(latest.get("target"))
            td = tracker_decision(params)
            recorded = latest["target"].get("fingerprint")
            if not isinstance(recorded, str) or not HEX64.match(recorded):
                return "target_unbound"
            if fingerprint(latest["target"], self.env, ctx) != recorded:
                return "target_changed"
        except TargetError as e:
            return e.reason
        awaiting = latest.get("awaiting")
        if not isinstance(awaiting, str) or not AW_RE.match(awaiting):
            return "awaiting_unbound"
        item, err = kyaction.read_json(self.env.run / "awaiting" / (awaiting + ".json"))
        if err == "missing":
            return "awaiting_not_open"
        if err or not isinstance(item, dict) or item.get("id", awaiting) != awaiting:
            return "awaiting_unreadable"
        named = named_tracker_decision(item)
        if td is not None and td["id"] != named:              # also when the item names none: nothing binds the id
            return "tracker_decision_not_the_awaiting_items: %s would be published, the item names %s" % (
                td["id"], named or "no tracker decision")
        decided = self.commands_about("decide", "awaiting_id", awaiting)
        if decided:
            return "superseded_by_owner_decide: %s" % decided[0]["doc"]["id"]
        for other, theirs in sorted(history.items()):
            if other != did and any(line.get("awaiting") == awaiting and _state(line) in ("EFFECTIVE", "EXECUTED")
                                    for line in theirs):
                return "awaiting_already_decided: %s" % other
        if cls.merge_action and os.path.lexists(self.env.run / "HOLD_MERGES"):
            return "class_hold: HOLD_MERGES"
        if td is not None and not (self.env.ky_bin.is_file() and os.access(self.env.ky_bin, os.X_OK)):
            return "publication_unavailable: no executable ky at %s" % self.env.ky_bin
        return cls.precheck(params, ctx)

    def publish(self, did, latest, td, effective_at):
        """Make the decision effective through `<id>.publish`. → None when that record is DONE, else the outcome."""
        run, action_id = self.env.run, did + ".publish"
        if td is None:
            argv, observer = None, _nothing_was_published
            status, record = kyaction.begin(
                run, action_id, "effective_without_tracker_decision", self.actor, {"decision_id": did, "argv": None},
                {"tracker_decision": None}, "decision %s: PENDING_VETO → EFFECTIVE (no tracker decision is named: "
                                            "nothing is published)" % did)
        else:
            argv = ["decide", td["id"], "--outcome", td["outcome"], "--as", "steward", "--delegated", "--detail",
                    "%s: %s" % (did, kyaction.flat(latest.get("decision"), 400))]
            observer = self.publish_observer or _no_tracker_readback
            status, record = kyaction.begin(
                run, action_id, "tracker_decision_publish", self.actor, {"decision_id": did, "argv": argv},
                {"tracker_decision": td["id"], "outcome": td["outcome"]},
                "tracker decision %s: open → %s (steward, delegated) for %s" % (td["id"], td["outcome"], did))
        if status == "in_progress":          # the process that began it is alive elsewhere: it may be publishing now
            return self.busy(record, "publication")
        if status == "unfinished":           # a restart inside the publication: observe, never repeat blind
            status, record = kyaction.reconcile(run, action_id, observer, by=self.holder)
            if status == "unknown":
                return {"outcome": "blocked", "reason": "publication_unreconciled", "attention": True}
        if status == "done":
            return None
        if status == "failed":
            earlier = record.get("result") or {}
            return self.failed(did, latest, "publication_failed: %s" % (
                "rc=%d" % earlier["exit_status"] if isinstance(earlier.get("exit_status"), int)
                else kyaction.flat(earlier.get("error") or earlier.get("reason"), 120)), effective_at)
        if td is None:                       # "new" or "not_done", and nothing to send
            kyaction.complete(run, action_id, {"published": False, "effective_at": self.now_iso})
            return None
        kind, rc, text = run_ky([str(self.env.ky_bin)] + argv, self.env)     # "new" or "not_done"
        if kind == "exited" and rc == 0:
            kyaction.complete(run, action_id, {"exit_status": 0, "output": text, "published": True,
                                               "effective_at": self.now_iso})
            return None
        if kind == "exited":                 # a non-zero exit says nothing about the tracker: only a readback does
            def readback(record):
                outcome, detail = observer(record)
                if outcome == "unknown":     # kept with the record: why it is unfinished, and what `ky` said
                    detail = {"readback": detail, "ky_exit_status": rc, "ky_output": text}
                return outcome, detail

            status, record = kyaction.reconcile(run, action_id, readback, by=self.holder)
            if status == "done":             # the tracker holds the decision although `ky` complained
                self.log("%s: `ky decide` exited %d but the readback shows the decision published" % (did, rc))
                return None
            if status == "not_done":
                record = kyaction.fail(run, action_id, {"exit_status": rc, "output": text, "published": False})
            # … else the record stays unfinished: published unknown (the line and the row say so), never retried
            return self.failed(did, latest, "publication_failed: rc=%d" % rc, effective_at, publication(record))
        if kind == "not_started":
            kyaction.fail(run, action_id, {"exit_status": None, "error": text, "published": False})
            return self.failed(did, latest, "publication_failed: %s" % text, effective_at)
        self.log("%s: `ky decide` gave no exit status (%s); the publication stays unreconciled" % (did, text))
        return {"outcome": "blocked", "reason": "publication_unreconciled", "attention": True}

    def execute(self, did, latest, cls, params, ctx, effective_at):
        run, action_id = self.env.run, did + ".execute"
        inputs = {"decision_id": did, "class": latest.get("class"), "authority": latest.get("authority")}
        earlier = self.memory(did)[1]
        if earlier is not None:              # the before values are those of the FIRST begin, never re-read
            if "before" in (earlier.get("inputs") or {}):
                inputs["before"] = earlier["inputs"]["before"]
        elif hasattr(cls, "before"):         # recorded with the intention, before anything is written (C3-01)
            try:
                inputs["before"] = cls.before(params, ctx)
            except (OSError, ValueError) as e:
                return self.failed(did, latest, "execution_failed: before_state_unreadable: %s" % type(e).__name__,
                                   effective_at)
        status, record = kyaction.begin(
            run, action_id, "veto_decision_execute:" + cls.kind, self.actor, inputs,
            latest.get("target"), cls.describe(params))
        if status == "in_progress":          # the process that began it is alive elsewhere: it may be executing now
            return self.busy(record, "execution")
        if status == "unfinished":           # a restart between begin and execution: reconcile first
            status, record = kyaction.reconcile(run, action_id, lambda r: cls.observer(params, ctx), by=self.holder)
            if status == "unknown":
                return {"outcome": "blocked", "reason": "execution_unreconciled", "attention": True}
        if status == "done":
            return None
        if status == "failed":
            earlier = record.get("result") or {}
            partial = earlier.get("partial_effect")
            return self.failed(did, latest, "execution_failed: %s" % kyaction.flat(earlier.get("reason"), 160),
                               effective_at, partial=partial if isinstance(partial, dict) and partial else None)
        try:                                 # "new" or "not_done"
            ok, result = cls.execute(params, ctx)
        except Exception as e:
            ok, result = False, {"reason": "executor_error: %s" % type(e).__name__}
        if not ok:                           # what did the failed executor leave behind? put back, or said so
            try:
                _, partial = self.undo(cls, params, ctx, record)
            except Exception as e:           # the look itself failed: unknown, never "nothing"
                partial = {"state": UNKNOWN, "error": "undo_error: %s" % type(e).__name__}
            if partial:
                result = dict(result, partial_effect=partial)
            kyaction.fail(run, action_id, result)
            return self.failed(did, latest, "execution_failed: %s" % kyaction.flat(result.get("reason"), 160),
                               effective_at, partial=partial)
        kyaction.complete(run, action_id, result)
        return None

    # ---- owner commands addressed to the veto role that no pending decision consumed
    def sweep(self):
        history, problems, unusable = load_decisions(self.log_path)
        if problems:
            return
        for entry in kycommands.scan(self.env.run)[0]:
            doc = entry["doc"]
            if doc["role"] != "veto" or doc["state"] != "QUEUED":
                continue
            if entry["invalid"]:
                self.settle(entry)           # kycommands settles it as REJECTED invalid_command
            elif doc["command"] != "veto":
                continue                     # the veto controller's (kyloop.VetoController.apply_commands): stays queued
            else:
                did = doc["args"]["decision_id"]
                lines = history.get(did)
                state = self.state_of(did, lines) if lines else None
                refusal = read_refusal(self.env.run, did)
                if not lines:
                    self.settle(entry, reject="unknown_decision")
                elif refusal is not None:
                    self.settle(entry, result={"decision": did, "outcome": "REFUSED", "note": (
                        "the handler refused this record (%s); nothing was or will be executed for it"
                        % kyaction.flat(refusal.get("reason"), 160))})
                elif did in unusable or self.candidate(did, lines) or state == "PROPOSED":
                    continue                 # settled under the decision lock / not yet in its window: stays queued
                elif state in ("VETOED", "FAILED"):
                    self.settle(entry, result={"decision": did, "outcome": state,
                                               "note": "the decision was already %s" % state})
                else:                        # C4-02: the owner is told, as when the veto arrives inside the tick —
                    self.settle(entry, reject="too_late: decision %s is %s" % (did, state))    # and until it is settled
                    row = {"id": did, "reason": "veto_too_late", "attention": True, "command": doc["id"]}
                    self.late.append(dict(row, outcome="executed") if state == "EXECUTED"
                                     else dict(row, outcome="not_pending", state=state))

    # ---- finished decisions whose publication is still unknown: settled when a readback exists
    def reconcile_publications(self, history, report):
        if self.publish_observer is None:    # nothing could answer: `status` keeps them unresolved
            return
        seen = {row.get("id") for row in report["decisions"]}
        for did, lines in sorted(history.items()):
            try:
                pub, exe = self.memory(did)
                finished = self.terminal(did, lines, pub, exe) if in_domain(lines) else None
                if did in seen or finished not in ("VETOED", "FAILED") or publication(pub) != UNKNOWN:
                    continue
                lock = kyaction.acquire_lock(self.env.run, "decision." + did, self.holder, log=self.log)
            except kyaction.ActionError:     # unreadable or foreign memory, a lock nobody can judge: still unknown
                continue
            if lock is None:
                continue
            try:
                published = self.published(did)
            finally:
                kyaction.release_lock(lock)
            if published != UNKNOWN:
                row = {"id": did, "outcome": finished.lower(), "reason": "publication_reconciled",
                       "published": published}
                if published:                # the tracker holds a decision the owner vetoed or that was not carried out
                    row["attention"] = True
                report["decisions"].append(row)

    def run(self, report):
        history, problems, unusable = load_decisions(self.log_path)
        pause = kycommands.pause_state(self.env.run)
        report["problems"] = problems + sorted(unusable.values()) + ["command queue: %s" % p for p in pause["problems"]]
        report["holds"] = self.holds()
        if not problems:                     # an unattributable line: no decision's state is known → no transition
            for did in sorted(d for d, lines in history.items() if d not in unusable and self.candidate(d, lines)):
                report["decisions"].append(self.guarded(did))
            try:
                self.reconcile_publications({d: x for d, x in history.items() if d not in unusable}, report)
            except (kyaction.ActionError, OSError) as e:
                report["problems"].append("publication readback: %s: %s" % (type(e).__name__, kyaction.flat(e, 160)))
            try:
                self.sweep()
            except (kyaction.ActionError, kycommands.CommandError, OSError) as e:
                report["problems"].append("command sweep: %s: %s" % (type(e).__name__, kyaction.flat(e, 160)))
            report["decisions"].extend(self.late)
        if self.authority_held:              # ONE attention item, however many decisions wait for it
            report["problems"].append(
                "authority_unknown: the authorised source cannot be established (%s); held, not failed: %s"
                % (report["authority"].get("source"), ", ".join(self.authority_held)))
        report["commands"] = self.commands
        report["attention"] = bool(report["problems"]) or any(
            x.get("attention") for x in report["decisions"] + report["commands"])


def tick(env=None, *, authorised=None, holder=None, holder_kind="controller", publish_observer=None, log=None):
    """One pass, at the wall clock (there is no time argument). `authorised` = {"source_commit",
    "entrypoints_digest"} as the caller established it, kyveto.UNKNOWN when the caller could not, or None (then
    PLANNER_STATE.json is read, see resolve_authority). `holder` must be the caller's own $KY_RUN/locks/veto;
    without one the tick fences itself for its own duration. → the report."""
    env = env or Env()
    moment = wall_clock()
    if not env.run.is_dir():
        raise RunMissing(str(env.run))
    if holder_kind not in ("controller", "supervisor"):
        raise ValueError("holder_kind must be controller or supervisor")
    authorised, source = _authority(env, authorised)
    report = {"schema": "ky.veto_tick/1", "now": kyaction.utc(moment), "holder": holder,
              "authority": dict(authorised or {}, source=source), "holds": [], "decisions": [], "commands": [],
              "problems": [], "attention": False}
    own = None
    if holder is None:
        holder = "kyveto-%s-%d" % (kyaction.utc(fmt="%Y%m%dT%H%M%SZ"), os.getpid())
        try:
            own = kyaction.acquire_lock(env.run, "veto", holder, log=log)
        except kyaction.LockUnknown as e:
            return dict(report, skipped="veto_role_lock_owner_unknown", attention=True,
                        problems=["veto role lock: %s" % kyaction.flat(e, 200)])
        if own is None:
            return dict(report, skipped="veto_role_lock_held")
        report["holder"] = holder
    else:
        held, why = kycommands.holds_role_lock(env.run, "veto", holder)
        if not held:
            raise NotHolder(why)
    try:
        Handler(env, moment, authorised, holder, holder_kind, publish_observer, log).run(report)
    finally:
        if own is not None:
            kyaction.release_lock(own)
    return report


def _now(now):
    if now is None:
        return wall_clock()
    parsed = kyaction.parse_utc(now)
    if parsed is None:
        raise ValueError("--now must be a UTC ISO-8601 timestamp (…Z)")
    return parsed


def status(env=None, now=None, authorised=None):
    """Read-only: every decision as the handler sees it (§13: a surrogate decision IS its state, not a journal
    line). `state` is the state the handler accepts (`accepted_state`: its terminal state, else EFFECTIVE once
    the handler's own publication is DONE, else PENDING_VETO under a line that stepped back, else the latest line's);
    `latest_line_state` is what the log's last line says. `now` only moves the remaining-time arithmetic.
    `attention` is what needs somebody NOW: problems; an anomaly no tick has answered yet (`anomaly` on a row);
    a refused record or a hard stop whose awaiting item is still open (`unresolved` on a row, `hard_stops`);
    a decision — finished or not — whose publication is unknown (`published: "unknown"`, `unresolved`, listed in
    `publication_unknown`) until its `<id>.publish` record is reconciled; a decision whose latest line stepped
    back behind an earlier one, or that has handler records but no proposal (`unresolved`, an anomaly); a
    VETOED / FAILED line the handler's own records do not bear out (`unresolved`, anomaly
    terminal_line_not_the_handlers — until a tick has closed the decision itself); an `<id>.execute` record
    that is INTENDED with nobody known to be carrying it out (`execution_unfinished`, `unresolved`); a given-up
    execution part of which is still in place or cannot be judged (`partial_effect`, `unresolved`, listed in
    `partial_effects` — looked at afresh on every call). `published` on every row is the
    three-valued `publication` of the handler's own record ("unknown" too when that record is not the handler's).
    What a tick has answered and the owner has dealt with stays in the rows and no longer raises it."""
    env = env or Env()
    moment = _now(now)
    authorised, source = _authority(env, authorised)
    history, problems, unusable = load_decisions(env.run / "DECISIONS_SURROGATE.jsonl")
    pause = kycommands.pause_state(env.run)
    reader = Handler(env, moment, authorised, "status", "controller", None, None)
    actions, action_problems = kyaction.scan(env.run)
    by_id = {a["action_id"]: a for a in actions}
    vetoes = {}
    for entry in kycommands.scan(env.run)[0]:
        doc = entry["doc"]
        if not entry["invalid"] and doc["command"] == "veto" and doc["state"] in ("QUEUED", "APPLIED"):
            vetoes.setdefault(doc["args"]["decision_id"], doc["id"])
    decisions, hard_stops, unknown_publications, partial_effects = [], [], [], []
    for did, lines in sorted(history.items()):
        latest = lines[-1]
        target, notification = latest.get("target"), latest.get("notification")
        pub, exe = by_id.get(did + ".publish"), by_id.get(did + ".execute")
        published = publication(pub) if pub is None or _own(pub) else UNKNOWN
        pub, exe = (pub if pub and _own(pub) else None), (exe if exe and _own(exe) else None)
        begun, closed = pub is not None or exe is not None, closed_as(env.run, did, exe)
        finished = first_terminal(lines, _done(exe), begun, closed) if in_domain(lines) else None
        row = {"id": did, "class": latest.get("class"),
               "state": accepted_state(lines, _done(pub), _done(exe), begun, closed),
               "latest_line_state": _state(latest), "by": latest.get("by"), "awaiting": latest.get("awaiting"),
               "kind": target.get("kind") if isinstance(target, dict) else None,
               "veto_deadline": latest.get("veto_deadline"), "effective_at": latest.get("effective_at"),
               "notification_submitted": isinstance(notification, dict) and notification.get("submitted") is True,
               "veto_command": vetoes.get(did), "reason": latest.get("reason"),
               "made_effective_by_handler": _done(pub), "executed_by_handler": _done(exe), "published": published}
        if published == UNKNOWN:                               # never shown as "not published"; somebody must look
            row["unresolved"] = True
            unknown_publications.append(did)
        anomalies, refusal = [], read_refusal(env.run, did)
        awaiting = latest.get("awaiting")
        named = isinstance(awaiting, str) and bool(AW_RE.match(awaiting))
        open_item = named and (env.run / "awaiting" / (awaiting + ".json")).is_file()
        if in_domain(lines) and refusal is None:              # what the next tick will answer
            if finished and _state(latest) != finished:
                anomalies.append("line_appended_after_terminal_state")
            for claim, backed in (("EFFECTIVE", _done(pub)), ("EXECUTED", _done(exe))):
                if not backed and not finished and any(_state(line) == claim for line in lines):
                    anomalies.append("log_claims_%s_without_action_record" % claim.lower())
            if not finished and claimed(lines):               # C4-01: a VETOED / FAILED line the handler's records
                anomalies.append(CLAIMED)                     # do not bear out ends nothing: unresolved until the
                row["unresolved"] = True                      # handler has closed the decision itself
            if not finished and regressed(lines):             # C3-02: the handler carries on; somebody is told
                anomalies.append(REGRESSED)
                row["unresolved"] = True
            if not finished and (pub or exe) and proposal_of(lines) is None:
                anomalies.append("proposal_missing")          # handler records without a proposal in the log
                row["unresolved"] = True
        if _abandoned(exe):                                   # R16: begun, not finished, nobody carrying it out —
            row["execution_unfinished"] = True                # part of the effect may be in force until a tick
            row["unresolved"] = True                          # has completed or closed it
        partial = (exe.get("result") or {}).get("partial_effect") if exe and exe["state"] == "FAILED" else None
        if isinstance(partial, dict) and partial:             # C3-01: part of an execution that was not completed
            row["partial_effect"] = partial.get("state", UNKNOWN)
            if row["partial_effect"] != "restored":           # looked at again, now: is it still in place?
                try:
                    cls, params = bind(exe.get("target"))
                    answer = cls.effect(params, Ctx(env, did, None, None), (exe.get("inputs") or {}).get("before"))[0]
                except Exception:
                    answer = UNKNOWN
                if answer == "absent":
                    row["partial_effect"] = "no_longer_in_place"
                else:
                    row["unresolved"] = True
                    partial_effects.append(did)
        if any(line.get("class") == "hard_stop" for line in lines):
            row["hard_stop"] = True
            if refusal is None and any(_state(line) not in (None, "PROPOSED") for line in lines):
                anomalies.append("hard_stop_record_outside_proposed")
            if open_item:
                hard_stops.append(did)                         # still unresolved: the owner has not decided it
        if refusal is not None:                                # the handler will never act on it; is anybody on it?
            row["refused"] = refusal.get("reason")
            if open_item or not named:
                row["unresolved"] = True
        if row["state"] == "PENDING_VETO" and refusal is None:
            stamp, _ = read_first_seen(env.run, did)
            notified, _ = notified_at(env.run, did)
            deadline = kyaction.parse_utc(latest.get("veto_deadline"))
            row["first_seen_at"] = stamp["first_seen_at"] if stamp else None
            row["notified_at"] = kyaction.utc(notified) if notified is not None else None
            if stamp and notified is not None and deadline is not None:
                not_before = max(max(kyaction.parse_utc(stamp["first_seen_at"]), notified) + VETO_WINDOW_S, deadline)
                row["effective_not_before"] = kyaction.utc(math.ceil(not_before))
                row["seconds_remaining"] = max(0, int(math.ceil(not_before - moment)))
            else:                                              # not yet seen by a tick, or no notification evidence
                row["effective_not_before"] = None
        if anomalies:
            row["anomaly"], row["anomalies"] = anomalies[0], anomalies
        decisions.append(row)
    all_problems = problems + sorted(unusable.values()) + ["command queue: %s" % p for p in pause["problems"]] \
        + ["action record: %s" % p for p in action_problems]
    return {"schema": "ky.veto_status/1", "now": kyaction.utc(moment),
            "authority": dict(authorised or {}, source=source), "holds": reader.holds(),
            "pause": {k: pause[k] for k in ("state", "applied_pause", "pending_pause")}, "decisions": decisions,
            "hard_stops": hard_stops, "publication_unknown": unknown_publications,
            "partial_effects": partial_effects,
            "unfinished_actions": sorted(a["action_id"] for a in actions if a["state"] == "INTENDED"),
            "problems": all_problems,
            "attention": bool(all_problems) or bool(hard_stops) or any("anomaly" in row or row.get("unresolved")
                                                                      for row in decisions)}


# ───────────────────────────────────────── CLI ─────────────────────────────────────────

USAGE = ("usage: kyveto.py tick [--authorised-commit C --entrypoints-digest D] [--as HOLDER_ID]\n"
         "                      [--holder-kind controller|supervisor]      (the wall clock only: there is no --now)\n"
         "       kyveto.py status [--now ISO] [--authorised-commit C --entrypoints-digest D]\n"
         "       kyveto.py fingerprint --target FILE")


def _options(argv, allowed):
    out = {}
    while argv:
        if argv[0] not in allowed or len(argv) < 2 or argv[0] in out:
            return None
        out[argv[0]] = argv[1]
        argv = argv[2:]
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    env = Env()
    common = ("--authorised-commit", "--entrypoints-digest")
    if argv and argv[0] in ("tick", "status"):
        opts = _options(argv[1:], common + (("--as", "--holder-kind") if argv[0] == "tick" else ("--now",)))
        if opts is None or opts.get("--holder-kind", "controller") not in ("controller", "supervisor") \
                or ("--as" in opts and not opts["--as"]):
            print(USAGE, file=sys.stderr)
            return 64
        try:
            if "--now" in opts:
                _now(opts["--now"])
            authorised = None
            if "--authorised-commit" in opts or "--entrypoints-digest" in opts:
                authorised, _ = resolve_authority(env, opts.get("--authorised-commit"),
                                                  opts.get("--entrypoints-digest"))
        except ValueError as e:
            print("kyveto: %s\n%s" % (e, USAGE), file=sys.stderr)
            return 64
        if not env.run.is_dir():
            print("kyveto: run directory missing: %s" % env.run, file=sys.stderr)
            return 66
        try:
            if argv[0] == "status":
                report = status(env, opts.get("--now"), authorised)
            else:
                report = tick(env, authorised=authorised, holder=opts.get("--as"),
                              holder_kind=opts.get("--holder-kind", "controller"))
        except NotHolder as e:
            print("kyveto: REFUSED %s" % e, file=sys.stderr)
            return 75
        print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
        return 3 if report.get("attention") else 0
    if argv and argv[0] == "fingerprint":
        opts = _options(argv[1:], ("--target",))
        if not opts or "--target" not in opts:
            print(USAGE, file=sys.stderr)
            return 64
        target, err = kyaction.read_json(opts["--target"])
        if err:
            print("kyveto: target file %s" % err, file=sys.stderr)
            return 1
        try:
            print(fingerprint(target, env))
        except TargetError as e:
            print("kyveto: REFUSED %s" % e.reason, file=sys.stderr)
            return 1
        return 0
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
