#!/usr/bin/env python3
"""kycommands.py — the durable cockpit command queue of KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.1 "Cockpit
commands enter a durable command queue", §4a.5, §4a.6; cockpit prompt v2.7 item 6).

The cockpit never touches a loop's state: it writes $KY_RUN/commands/<UTC yyyymmddThhmmssZ>-<id>.json (QUEUED)
and the fenced owner of the addressed role applies it, in filename order, exactly once.

    command_id = submit(run_dir, role, command, args, from_)
    pending(run_dir, role)                         QUEUED commands of a role, in filename order
    status, doc = apply(run_dir, command_id, applier, handler, observer=None, in_order=True)
        "applied" | "rejected"                     this call settled the command (handler result / reason recorded)
        "already_applied" | "already_rejected"     settled earlier: the handler was NOT called again
        "locked"                                   another live actor is applying it right now, or the process that
                                                   began applying it is still alive elsewhere: skipped
        "refused"                                  nothing changed; doc = {"reason": …}: the applier is not the
                                                   owner of $KY_RUN/locks/<role>, an earlier command of the role is
                                                   QUEUED or cannot be read, or the command's lock has an owner
                                                   that cannot be judged (then doc also has "attention": true)
        "unreconciled"                             an earlier application died inside the handler and no observer
                                                   could say whether it took effect: it is not repeated blind
    owner_paused(run_dir)                          True/False from the APPLIED pause/resume history
    pause_state(run_dir)                           the same with the pending owner pause and the queue's problems

Rules this file enforces (each has a test in tests/test_kycontrol.py):
  * submit validates the role, the command name, the argument shape and the sender; `veto` is addressed to the
    `veto` role and `pause` / `resume` to the `campaign` role, nowhere else;
  * filename order is submission order, also within one second and when the wall clock has stepped back;
  * apply requires the applier to BE the owner of the role lock: owner.json names its id, the recorded owner
    process is alive with the recorded start identity (kyaction.process_matches is True — unknown is refused),
    and that process is the caller itself or one of its ancestors. Naming the holder's id from another process
    is refused. The check is repeated after the lock `command.<id>` has been taken; then the command is re-read
    (handled-state check), the handler runs through a kyaction record `CMD-<id>`, and the command is marked
    APPLIED or REJECTED once;
  * within a role, a command is not applied while an earlier file in the queue cannot be read (it may be an
    earlier command of that role);
  * an owner pause is ended only by an APPLIED owner `resume`; a `pause` whose handler failed with an error
    (REJECTED "handler_error: …") stays in force as a requested pause until the owner resumes; a queue that
    cannot be read is "unknown", never "not paused".

Origin of a command: `from` = {kind: "cockpit", session_id, pid, process_start} — the submitting process as it
saw itself. This is a CONVENTION, not an enforced boundary: any process that can write $KY_RUN/commands can
queue a command, a `resume` or a `veto` included, and name any session. Until the fleet has an enforced write
boundary for that directory, "only the owner's cockpit submits" rests on the roles' instructions; pid and
process start are recorded so that a command's real origin can be examined afterwards.

A handler receives a copy of the command and returns a JSON object (the result) or raises Reject(reason).
Any other exception is recorded as REJECTED "handler_error: <Type>" and is never retried automatically.

CLI:  kycommands.py submit --role R --command C [--args JSON] --session SESSION_ID      prints the command id
      kycommands.py list [--role R] [--state S]                                         read-only
Exit codes: 0 ok · 1 refused / the queue has unreadable entries · 64 usage.
Python >= 3.9, standard library only.
"""
from __future__ import annotations

import calendar
import copy
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kyaction  # noqa: E402

SCHEMA = "ky.command/1"
ROLES = ("planner", "conductor", "dispatcher", "veto", "campaign")
COMMANDS = ("status", "veto", "decide", "pause", "resume", "priority", "builders", "verifiers", "loops",
            "approve-window", "handoff")
STATES = ("QUEUED", "APPLIED", "REJECTED")
ROUTING = {"veto": "veto", "pause": "campaign", "resume": "campaign"}        # command → the only role it may address
LOOP_OPS = ("start", "stop", "status")
LOOPS = ("dispatcher", "planner", "conductor", "veto", "all")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
STEM_RE = re.compile(r"^([0-9]{8}T[0-9]{6}Z)-([A-Za-z0-9][A-Za-z0-9._-]{0,79})\Z")
SEQ_RE = re.compile(r"^([0-9]{6})-")
SD_RE = re.compile(r"^SD-[0-9]{8}T[0-9]{6}Z-[0-9]+\Z")
AW_RE = re.compile(r"^AW-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+\Z")
STAMP = "%Y%m%dT%H%M%SZ"
HANDLER_ERROR = "handler_error"                 # REJECTED because the handler raised, not because it said no


class CommandError(Exception):
    """Base class: the command does not exist or the queue cannot serve the request."""


class CommandInvalid(CommandError):
    """The role, command name, arguments or sender are not acceptable."""


class QueueUnreadable(CommandError):
    """A command file cannot be read or understood: the pause history is unknown."""


class Reject(Exception):
    """Raised by a handler: the command is settled as REJECTED with this reason."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = kyaction.flat(reason, 300) or "rejected"


# ───────────────────────────────────────── validation ─────────────────────────────────────────

def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


ARG_RULES = {
    "status": {}, "pause": {}, "resume": {}, "handoff": {},
    "veto": {"decision_id": lambda v: isinstance(v, str) and bool(SD_RE.match(v))},
    "decide": {"awaiting_id": lambda v: isinstance(v, str) and bool(AW_RE.match(v)), "answer": _text},
    "priority": {"item": _text},
    "builders": {"n": _count},
    "verifiers": {"n": _count},
    "loops": {"op": lambda v: v in LOOP_OPS, "loop": lambda v: v in LOOPS},
    "approve-window": {"id": _text},
}


def args_problem(command, args):
    """None, or why `args` is not the argument object of `command`."""
    rules = ARG_RULES.get(command)
    if rules is None:
        return "unknown command %r" % (command,)
    if not isinstance(args, dict):
        return "args must be an object"
    for key in sorted(set(args) - set(rules), key=str):
        return "%s takes no argument %r" % (command, key)
    for key, ok in rules.items():
        if key not in args:
            return "%s needs the argument %r" % (command, key)
        if not ok(args[key]):
            return "%s: argument %r has an unacceptable value" % (command, key)
    return None


def sender_problem(from_):
    """None, or why `from_` is not a sender: {kind: "cockpit", session_id} as submit() is given it, optionally with
    the pid and process_start submit() records beside them."""
    if not isinstance(from_, dict) or not {"kind", "session_id"} <= set(from_) \
            or set(from_) - {"kind", "session_id", "pid", "process_start"}:
        return "from must be {kind, session_id} (pid and process_start are recorded by submit)"
    if from_["kind"] != "cockpit":
        return "only the cockpit submits commands (from.kind %r)" % (from_["kind"],)
    if not _text(from_["session_id"]):
        return "from.session_id must be a non-empty string"
    if "pid" in from_ and not _count(from_["pid"]):
        return "from.pid must be a positive integer"
    if from_.get("process_start") is not None and not _text(from_["process_start"]):
        return "from.process_start must be a non-empty string or null"
    return None


def command_problem(role, command, args, from_):
    if role not in ROLES:
        return "unknown role %r" % (role,)
    if command not in COMMANDS:
        return "unknown command %r" % (command,)
    if ROUTING.get(command, role) != role:
        return "%s is addressed to the %s role, not %s" % (command, ROUTING[command], role)
    return args_problem(command, args) or sender_problem(from_)


# ───────────────────────────────────────── the queue ─────────────────────────────────────────

def queue_dir(run_dir):
    return Path(run_dir) / "commands"


def _scan(run_dir):
    """(entries, [(file name, reason)]); see scan()."""
    directory = queue_dir(run_dir)
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return [], []
    entries, bad = [], []
    for name in names:
        if name.startswith(".") or not name.endswith(".json"):
            continue
        stem, path = name[:-5], directory / name
        m = STEM_RE.match(stem)
        if not m:
            bad.append((name, "not <UTC yyyymmddThhmmssZ>-<id>.json"))
            continue
        doc, err = kyaction.read_json(path)
        if err or not isinstance(doc, dict):
            bad.append((name, err or "not an object"))
            continue
        if doc.get("schema") != SCHEMA or doc.get("id") != m.group(2) or doc.get("role") not in ROLES \
                or doc.get("state") not in STATES:
            bad.append((name, "no usable schema / id / role / state"))
            continue
        invalid = command_problem(doc["role"], doc.get("command"), doc.get("args"), doc.get("from"))
        entries.append({"stem": stem, "path": path, "doc": doc, "invalid": invalid})
    return entries, bad


def scan(run_dir):
    """(entries, problems). Entries are in filename order: {"stem", "path", "doc", "invalid"}; `invalid` is None
    or the reason a structurally identified command (id, role, state readable) is not acceptable — such a command
    is settled as REJECTED by apply(). Files that cannot be identified at all are listed in problems only."""
    entries, bad = _scan(run_dir)
    return entries, ["%s: %s" % (name, why) for name, why in bad]


def find(run_dir, command_id):
    """The queue entry of a command id, or None."""
    if not isinstance(command_id, str) or not ID_RE.match(command_id):
        raise CommandInvalid("command id %r is not [A-Za-z0-9][A-Za-z0-9._-]{0,79}" % (command_id,))
    found = [e for e in scan(run_dir)[0] if e["doc"]["id"] == command_id]
    if len(found) > 1:
        raise CommandError("command id %s names %d files" % (command_id, len(found)))
    return found[0] if found else None


def pending(run_dir, role):
    """QUEUED commands of `role` in filename order (an identifiable but invalid one is included: its role owner
    settles it as REJECTED). Unreadable files are reported by scan(), never by omission here alone."""
    if role not in ROLES:
        raise CommandInvalid("unknown role %r" % (role,))
    return [e["doc"] for e in scan(run_dir)[0] if e["doc"]["role"] == role and e["doc"]["state"] == "QUEUED"]


def _after(last_stem):
    """(timestamp, sequence) of the first filename slot that sorts after `last_stem`."""
    stamp, last_id = STEM_RE.match(last_stem).groups()
    seq = SEQ_RE.match(last_id)
    if seq and int(seq.group(1)) < 999999:
        return stamp, int(seq.group(1)) + 1
    return time.strftime(STAMP, time.gmtime(calendar.timegm(time.strptime(stamp, STAMP)) + 1)), 0


def submit(run_dir, role, command, args, from_):
    """Validate and enqueue one command; → its id. The file is created exclusively and atomically. `from_` is
    {kind: "cockpit", session_id}; the pid and start identity of the submitting process are recorded with it
    (a record of origin, not a proof of it — see the module docstring)."""
    problem = command_problem(role, command, args, from_)
    if not problem and isinstance(from_, dict) and set(from_) != {"kind", "session_id"}:
        problem = "from must be {kind, session_id}: the submitting process is recorded by submit itself"
    if problem:
        raise CommandInvalid(problem)
    try:
        args = json.loads(kyaction.canonical(args).decode("utf-8"))
    except (TypeError, ValueError):
        raise CommandInvalid("args is not JSON-serialisable") from None
    directory = queue_dir(run_dir)
    os.makedirs(directory, exist_ok=True)
    me = kyaction.self_identity()                            # who really wrote this file, as far as it can say
    for _ in range(50):
        now = time.time()
        stamp, seq = time.strftime(STAMP, time.gmtime(now)), int((now % 1) * 1000000)
        stems = [n[:-5] for n in os.listdir(directory) if n.endswith(".json") and STEM_RE.match(n[:-5])]
        last, token = (max(stems) if stems else ""), secrets.token_hex(3)
        if last and "%s-%06d-%s-%s" % (stamp, seq, command, token) <= last:
            # same microsecond, or the wall clock is behind the newest queued command: filename order must stay
            # submission order (a later `resume` may never sort before an earlier `pause`, nor the reverse)
            stamp, seq = _after(last)
        command_id = "%06d-%s-%s" % (seq, command, token)
        doc = {"schema": SCHEMA, "id": command_id, "created_at": kyaction.utc(now),
               "from": {"kind": from_["kind"], "session_id": from_["session_id"], "pid": me["pid"],
                        "process_start": me["process_start"]}, "role": role,
               "command": command, "args": args, "state": "QUEUED", "applied_by": None, "applied_at": None,
               "result": None}
        if kyaction.write_exclusive(directory / ("%s-%s.json" % (stamp, command_id)), _dump(doc)):
            return command_id
    raise CommandError("could not allocate a command id")


def _dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


# ───────────────────────────────────────── applying ─────────────────────────────────────────

APPLIER_KINDS = tuple(kind for kind in kyaction.HOLDER_KINDS if kind != "job")     # as schemas/command.json


def applier_identity(applier):
    """(id, {"holder_kind", "session_id" | "controller_id"}) from a controller id string or an actor-like dict.
    A job never applies a command (holder_kind "job" is refused here as in schemas/command.json)."""
    if isinstance(applier, str) and applier:
        return applier, {"holder_kind": "controller", "controller_id": applier}
    if isinstance(applier, dict) and applier.get("holder_kind") in APPLIER_KINDS:
        keys = [k for k in ("session_id", "controller_id") if k in applier]
        if len(keys) == 1 and set(applier) == {"holder_kind", keys[0]} and _text(applier[keys[0]]):
            return applier[keys[0]], dict(applier)
    raise CommandInvalid("applier must be a controller id or {holder_kind: %s, session_id | controller_id}"
                         % " | ".join(APPLIER_KINDS))


def holds_role_lock(run_dir, role, applier_id):
    """(True, None) iff the CALLER is the owner of $KY_RUN/locks/<role>: owner.json names `applier_id`, its
    recorded process is alive with the recorded start identity, and that process is this process or one of its
    ancestors (a controller applying in-process, or the helper a lock holder started). Otherwise (False, named
    reason): naming the holder's id is not holding the lock, and a stale or unverifiable lock proves nothing."""
    owner, err = kyaction.lock_owner(run_dir, role)
    if owner is None:
        return False, "role_lock_not_held: %s lock %s" % (role, err)
    if owner.get("session_or_run_id") != applier_id:
        return False, "role_lock_held_by_another: %s" % kyaction.flat(owner.get("session_or_run_id"), 80)
    alive = kyaction.process_matches(owner.get("pid"), owner.get("process_start"))
    if alive is False:
        return False, "role_lock_stale: the recorded owner process is not alive"
    if alive is None:
        return False, "role_lock_owner_unverifiable: the recorded owner process cannot be confirmed alive"
    mine = kyaction.is_self_or_ancestor(owner.get("pid"))
    if mine is False:
        return False, ("role_lock_not_owned_by_caller: the %s lock belongs to pid %s, which is neither this process "
                       "nor one of its ancestors" % (role, owner.get("pid")))
    if mine is None:
        return False, "role_lock_owner_unverifiable: this process's ancestry cannot be read"
    return True, None


def _settle(entry, state, actor, result):
    doc = dict(entry["doc"], state=state, applied_by=actor, applied_at=kyaction.utc(), result=result)
    kyaction.write_atomic(entry["path"], _dump(doc))
    return ("applied" if state == "APPLIED" else "rejected"), doc


def _as_result(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        try:
            return json.loads(kyaction.canonical(value).decode("utf-8"))
        except (TypeError, ValueError):
            pass
    return {"value": kyaction.flat(value, 300)}


def apply(run_dir, command_id, applier, handler, observer=None, in_order=True, log=None):
    """Apply one queued command as the fenced owner of its role. → (status, doc); see the module docstring.
    `observer` (kyaction.reconcile form) is consulted only when an earlier application died inside the handler.
    `in_order=False` is for roles whose commands have independent targets (the veto role: one decision each)."""
    applier_id, holder = applier_identity(applier)
    entry = find(run_dir, command_id)
    if entry is None:
        raise CommandError("no command %s in the queue" % command_id)
    role = entry["doc"]["role"]
    held, why = holds_role_lock(run_dir, role, applier_id)
    if not held:
        return "refused", {"reason": why}
    try:
        lock = kyaction.acquire_lock(run_dir, "command." + command_id, applier_id, log=log)
    except kyaction.LockUnknown as e:                        # never taken over: somebody has to look at it
        return "refused", {"reason": "command_lock_owner_unknown: %s" % kyaction.flat(e.detail, 200),
                           "attention": True}
    if lock is None:
        return "locked", {"reason": "command_lock_held"}
    try:
        held, why = holds_role_lock(run_dir, role, applier_id)       # still the owner, now that the lock is ours
        if not held:
            return "refused", {"reason": why}
        entry = find(run_dir, command_id)                    # fresh handled-state check under the lock
        if entry is None:
            raise CommandError("command %s disappeared from the queue" % command_id)
        doc = entry["doc"]
        if doc["state"] != "QUEUED":
            return ("already_applied" if doc["state"] == "APPLIED" else "already_rejected"), doc
        if in_order:
            entries, bad = _scan(run_dir)
            for name, _ in bad:                              # its role is unknown: it may be an earlier command
                if name[:-5] < entry["stem"]:
                    return "refused", {"reason": "earlier_command_unreadable: %s" % name}
            for other in entries:
                if other["stem"] >= entry["stem"]:
                    break
                if other["doc"]["role"] == role and other["doc"]["state"] == "QUEUED":
                    return "refused", {"reason": "earlier_command_pending: %s" % other["doc"]["id"]}
        actor = dict(holder, role=role)
        if entry["invalid"]:
            return _settle(entry, "REJECTED", actor, {"reason": "invalid_command: %s" % entry["invalid"]})
        action_id = "CMD-" + command_id
        status, record = kyaction.begin(
            run_dir, action_id, "command:" + doc["command"], actor,
            {"role": role, "command": doc["command"], "args": doc["args"]},
            {"command_id": command_id, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % command_id)
        if status == "in_progress":                          # the process that began applying it may still be at it
            return "locked", {"reason": "application_in_progress: %s was begun by a process that is still alive"
                                        % action_id, "action_id": action_id}
        if status == "unfinished":
            if observer is None:
                return "unreconciled", {"reason": "an earlier application did not finish; no observer was given",
                                        "action_id": action_id}
            status, record = kyaction.reconcile(run_dir, action_id, observer, by=applier_id)
            if status == "unknown":
                return "unreconciled", {"reason": "the earlier application could not be observed",
                                        "action_id": action_id}
        if status == "done":
            return _settle(entry, "APPLIED", actor, record["result"])
        if status == "failed":
            earlier = record.get("result") or {}
            return _settle(entry, "REJECTED", actor,
                           {"reason": earlier.get("rejected") or earlier.get("error") or "handler_failed"})
        try:                                                 # status is "new" or "not_done": the handler runs now
            result = _as_result(handler(copy.deepcopy(doc)))
        except Reject as rejected:
            kyaction.fail(run_dir, action_id, {"rejected": rejected.reason})
            return _settle(entry, "REJECTED", actor, {"reason": rejected.reason})
        except Exception as e:
            reason = "%s: %s" % (HANDLER_ERROR, type(e).__name__)
            kyaction.fail(run_dir, action_id, {"error": reason})
            return _settle(entry, "REJECTED", actor, {"reason": reason})
        kyaction.complete(run_dir, action_id, result)
        return _settle(entry, "APPLIED", actor, result)
    finally:
        kyaction.release_lock(lock)


# ───────────────────────────────────────── owner pause ─────────────────────────────────────────

def pause_state(run_dir):
    """{"state": paused | not_paused | unknown, "applied_pause", "pending_pause", "problems"}.

    paused       an APPLIED `pause` for the campaign role with no later APPLIED `resume` (filename order)
    unknown      a command file is unreadable, or an unsettled command is not acceptable: nothing is concluded
    pending_pause  the id of an owner `pause` that is requested but not in force as APPLIED, with no later owner
                 `resume` (QUEUED or APPLIED) after it: the owner has asked. pending_kind says why it is not
                 applied — "queued" (the campaign role has not applied it yet) or "handler_error" (the role's
                 handler failed while applying it: the request stands, it was not refused on its merits).
                 Callers that must never act against the owner's wish (kyveto) treat it as a pause; it is not
                 part of `state`. A `pause` the role rejected on purpose (Reject) is not a pending pause."""
    entries, problems = scan(run_dir)
    problems = list(problems) + ["%s.json: %s" % (e["stem"], e["invalid"]) for e in entries
                                 if e["invalid"] and e["doc"]["state"] != "REJECTED"]
    applied, pending_pause, pending_kind = None, None, None
    for e in entries:
        doc = e["doc"]
        if e["invalid"] or doc["role"] != "campaign" or doc["command"] not in ("pause", "resume"):
            continue
        if doc["command"] == "pause":
            if doc["state"] == "APPLIED":
                applied, pending_pause, pending_kind = doc["id"], None, None
            elif doc["state"] == "QUEUED":
                pending_pause, pending_kind = doc["id"], "queued"
            elif _handler_error(doc):
                pending_pause, pending_kind = doc["id"], "handler_error"
        elif doc["state"] == "APPLIED":
            applied, pending_pause, pending_kind = None, None, None
        elif doc["state"] == "QUEUED":
            pending_pause, pending_kind = None, None         # the owner's later wish; it never ends an APPLIED pause
    state = "unknown" if problems else ("paused" if applied else "not_paused")
    return {"state": state, "applied_pause": applied, "pending_pause": pending_pause, "pending_kind": pending_kind,
            "problems": problems}


def _handler_error(doc):
    """True for a command settled REJECTED because its handler raised (apply() records "handler_error: <Type>")."""
    result = doc.get("result")
    return doc.get("state") == "REJECTED" and isinstance(result, dict) \
        and isinstance(result.get("reason"), str) and result["reason"].startswith(HANDLER_ERROR)


def owner_paused(run_dir):
    """True while an owner pause is in force, False when none is; QueueUnreadable when that cannot be known."""
    state = pause_state(run_dir)
    if state["state"] == "unknown":
        raise QueueUnreadable("; ".join(state["problems"]))
    return state["state"] == "paused"


# ───────────────────────────────────────── CLI ─────────────────────────────────────────

USAGE = ("usage: kycommands.py submit --role ROLE --command NAME [--args JSON] --session SESSION_ID\n"
         "       kycommands.py list [--role ROLE] [--state QUEUED|APPLIED|REJECTED]")


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
    run_dir = kyaction.default_run_dir()
    if argv and argv[0] == "submit":
        opts = _options(argv[1:], ("--role", "--command", "--args", "--session"))
        if opts is None or not {"--role", "--command", "--session"} <= set(opts):
            print(USAGE, file=sys.stderr)
            return 64
        try:
            args = json.loads(opts.get("--args", "{}"))
        except ValueError:
            print("kycommands: --args is not JSON\n" + USAGE, file=sys.stderr)
            return 64
        if not run_dir.is_dir():
            print("kycommands: run directory missing: %s" % run_dir, file=sys.stderr)
            return 1
        try:
            print(submit(run_dir, opts["--role"], opts["--command"], args,
                         {"kind": "cockpit", "session_id": opts["--session"]}))
        except CommandError as e:
            print("kycommands: REFUSED %s" % e, file=sys.stderr)
            return 1
        return 0
    if argv and argv[0] == "list":
        opts = _options(argv[1:], ("--role", "--state"))
        if opts is None or opts.get("--role", ROLES[0]) not in ROLES or opts.get("--state", STATES[0]) not in STATES:
            print(USAGE, file=sys.stderr)
            return 64
        entries, problems = scan(run_dir)
        for e in entries:
            doc = e["doc"]
            if opts.get("--role", doc["role"]) == doc["role"] and opts.get("--state", doc["state"]) == doc["state"]:
                print("%s\t%s\t%s\t%s\t%s%s" % (doc["state"], doc["role"], kyaction.flat(doc.get("command"), 40),
                                               e["stem"], json.dumps(doc.get("args"), sort_keys=True),
                                               "\tINVALID: " + e["invalid"] if e["invalid"] else ""))
        for problem in problems:
            print("kycommands: UNREADABLE %s" % problem, file=sys.stderr)
        return 1 if problems else 0
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
