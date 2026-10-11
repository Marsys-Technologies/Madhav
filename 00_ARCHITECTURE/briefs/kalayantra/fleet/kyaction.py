#!/usr/bin/env python3
"""kyaction.py — crash-safe action records for KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.1 "Action records" and
"Recovery", §4a.6 "Double-action guard").

Before any side effect (push, PR, merge, tracker event, launch, notification, an installed-file write) the actor
persists $KY_RUN/actions/<action_id>.json {inputs, target identity, intended transition}; after it, the OBSERVED
result. A restart reconciles every unfinished record against real evidence before anything is retried.

    status, record = begin(run_dir, action_id, kind, actor, inputs, target, intended_transition)
        "new"         the INTENDED record was created by this call: perform the side effect, then complete()/fail()
        "done"        an earlier attempt finished: skip the side effect, use record["result"]
        "unfinished"  an earlier attempt neither finished nor failed: reconcile() before anything else
        "failed"      an earlier attempt failed: only retry() reopens it (the attempt is kept in attempts[])
    complete(run_dir, action_id, result) / fail(run_dir, action_id, result)      the observed result, exactly once
    retry(run_dir, action_id, actor=None)                                        FAILED → INTENDED, history kept
    outcome, record = reconcile(run_dir, action_id, observer)
        observer(record) returns ("done", {result}) | ("not_done", detail) | ("unknown", detail)
        "done" completes the record with the observed result; "not_done" means the effect is positively absent
        (the caller may perform it now, under the same record); "unknown" changes nothing and permits nothing.
    unfinished(run_dir)        INTENDED records, oldest first (an unreadable record is an error, never "finished")

Rules this file enforces (each has a test in tests/test_kycontrol.py):
  * the record is created with an exclusive hard link from a fully written temporary file, so two concurrent
    begin() calls yield exactly one "new" and no reader ever sees a partial record;
  * an existing record is never overwritten by begin(); the same id with a different kind, inputs or target is a
    conflict, not "done";
  * the observed result is set once: repeating the identical observation is a no-op, a different one is refused;
  * every read-modify-write runs under the lock `action.<id>` followed by a fresh read of the record.

Locks (shared with kycommands.py and kyveto.py): `mkdir $KY_RUN/locks/<kind>.<id>` is the atomic step, owner.json
records {session_or_run_id, pid, pgid, process_start, acquired_at}. A second actor skips and logs. A lock whose
recorded owner process is positively gone is removed under an flock-serialised takeover, so two contenders can
never remove each other's fresh lock; a live or unverifiable owner is never displaced. A lock is ALWAYS followed
by a fresh handled-state check by its caller.

CLI (read-only):  kyaction.py list | show <action_id> | unfinished
Exit codes: 0 ok · 1 not found / an unreadable record exists · 64 usage.
Python >= 3.9, standard library only.
"""
from __future__ import annotations

import calendar
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "ky.action/1"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,119}\Z")
LOCK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}\Z")
HOLDER_KINDS = ("cockpit", "controller", "supervisor")
STATES = ("INTENDED", "DONE", "FAILED")
OUTCOMES = ("done", "not_done", "unknown")
OWNERLESS_GRACE_S = 60.0        # a lock directory without owner.json is "being acquired" for this long
LOCK_WAIT_S = 10.0              # how long a record update waits for another actor's update of the same record
LSTART_FMT = "%a %b %d %H:%M:%S %Y"
_TS = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(?:Z|\+00:00)\Z")
_IDENTITY = {}


class ActionError(Exception):
    """Base class: the record is missing or the operation cannot be carried out."""


class ActionInvalid(ActionError):
    """An argument cannot be recorded faithfully (bad id, non-JSON value, malformed actor)."""


class ActionRefused(ActionError):
    """The record's state forbids the transition (result already set, retry of a non-failed record)."""


class ActionConflict(ActionRefused):
    """The action id already names a different action (other kind, inputs or target)."""


class ActionUnreadable(ActionError):
    """A record file exists but cannot be read as an action record; it is never treated as finished."""


class LockBusy(ActionError):
    """Another live actor is updating the same record."""


# ───────────────────────── small deterministic helpers (same conventions as kyloop.py) ─────────────────────────

def utc(t=None, fmt="%Y-%m-%dT%H:%M:%SZ"):
    return time.strftime(fmt, time.gmtime(t))


def parse_utc(text):
    """Epoch seconds of a UTC ISO-8601 timestamp ('Z' or '+00:00', optional fraction), else None."""
    m = _TS.match(text) if isinstance(text, str) else None
    if not m:
        return None
    try:
        whole = calendar.timegm(time.strptime(text[:19], "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None
    return whole + (float(m.group(1)) if m.group(1) else 0.0)


def canonical(obj):
    """The byte form used for every comparison and digest: sorted keys, no padding, UTF-8, no NaN."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    """sha256 hex of a file, or None when it cannot be read."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def flat(text, limit=300):
    return " ".join(str(text if text is not None else "").split())[:limit]


def read_json(path):
    """(object, None) or (None, reason). Never raises."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError) as e:
        return None, "unreadable: %s" % type(e).__name__


def _fsync_dir(directory):
    try:
        fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _write_tmp(path, data, mode):
    path = Path(path)
    tmp = path.with_name(".%s.tmp.%d.%s" % (path.name, os.getpid(), secrets.token_hex(4)))
    with open(tmp, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    if mode is not None:
        os.chmod(tmp, mode)
    return tmp


def write_atomic(path, data, mode=None):
    """Replace `path` with `data`: temporary file, fsync, rename. A reader sees the old file or the new one."""
    tmp = _write_tmp(path, data, mode)
    try:
        os.replace(tmp, path)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    _fsync_dir(Path(path).parent)


def write_exclusive(path, data, mode=None):
    """Create `path` with `data` only if it does not exist (hard link from a complete temporary file).
    True: this call created it. False: it already existed and was left untouched."""
    tmp = _write_tmp(path, data, mode)
    try:
        os.link(tmp, path)
    except FileExistsError:
        return False
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
    _fsync_dir(Path(path).parent)
    return True


def write_json(path, obj, mode=None):
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=1) + "\n", mode)


def ps_identity(pid):
    """(stat, lstart) of a live process, or None. `ps -o lstart=` is the pinned start identity (as in kyloop.py)."""
    try:
        r = subprocess.run(["/bin/ps", "-o", "stat=,lstart=", "-p", str(int(pid))], capture_output=True, text=True,
                           env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}, timeout=10)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    parts = r.stdout.strip().split(None, 1)
    if r.returncode != 0 or len(parts) < 2:
        return None
    return parts[0], parts[1].strip()


def process_matches(pid, start):
    """True: alive with this start identity. False: gone, a zombie, or positively another process.
    None: alive but the recorded identity cannot be compared (never displace, never trust, on None)."""
    ident = ps_identity(pid) if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 else None
    if ident is None or ident[0].startswith("Z"):
        return False
    if not start:
        return None
    a, b = " ".join(str(start).split()), " ".join(ident[1].split())
    if a == b:
        return True
    try:
        return time.strptime(a, LSTART_FMT) == time.strptime(b, LSTART_FMT)
    except ValueError:
        return None


def self_identity():
    """{pid, pgid, process_start} of this process (cached per pid, so a forked child gets its own)."""
    pid = os.getpid()
    if pid not in _IDENTITY:
        ident = ps_identity(pid)
        _IDENTITY.clear()
        _IDENTITY[pid] = {"pid": pid, "pgid": os.getpgid(0), "process_start": ident[1] if ident else None}
    return dict(_IDENTITY[pid])


# ───────────────────────────────────────── locks (§4a.6) ─────────────────────────────────────────

class Lock:
    __slots__ = ("path", "owner_id")

    def __init__(self, path, owner_id):
        self.path, self.owner_id = Path(path), owner_id


def lock_path(run_dir, name):
    if not isinstance(name, str) or not LOCK_RE.match(name) or name in (".", ".."):
        raise ActionInvalid("lock name %r is not [A-Za-z0-9][A-Za-z0-9._:-]{0,159}" % (name,))
    return Path(run_dir) / "locks" / name


def lock_owner(run_dir, name):
    """(owner.json object, None) or (None, reason) for $KY_RUN/locks/<name>."""
    owner, err = read_json(lock_path(run_dir, name) / "owner.json")
    if err:
        return None, err
    return (owner, None) if isinstance(owner, dict) else (None, "unreadable: not an object")


def _remove_if_stale(path, log):
    """Remove the lock directory iff its recorded owner process is positively gone (or it has had no owner record
    for longer than the grace period). Serialised by flock, and re-read under it, so that a contender can never
    remove a lock another contender has just taken. → True when the caller should try mkdir again."""
    guard = os.open(str(path.parent / ".takeover.guard"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(guard, fcntl.LOCK_EX)
        owner, _ = read_json(path / "owner.json")
        if isinstance(owner, dict):
            if process_matches(owner.get("pid"), owner.get("process_start")) is not False:
                return False
        else:
            try:
                age = time.time() - path.stat().st_mtime
            except FileNotFoundError:
                return True                      # released in the meantime
            except OSError:
                return False
            if age < OWNERLESS_GRACE_S:
                return False
        try:
            for entry in path.iterdir():
                entry.unlink()
            os.rmdir(path)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        if log:
            log("stale lock %s removed (previous owner %s, pid %s, not alive)"
                % (path.name, flat((owner or {}).get("session_or_run_id"), 80), (owner or {}).get("pid")))
        return True
    finally:
        os.close(guard)


def acquire_lock(run_dir, name, owner_id, wait_s=0.0, log=None):
    """Take $KY_RUN/locks/<name>. → Lock, or None when another actor holds it (the caller skips; `log` is told).
    The caller must follow a successful acquisition with a fresh handled-state check."""
    path = lock_path(run_dir, name)
    if not isinstance(owner_id, str) or not owner_id:
        raise ActionInvalid("a lock owner id must be a non-empty string")
    os.makedirs(path.parent, exist_ok=True)
    deadline = time.monotonic() + max(0.0, wait_s)
    for _ in range(100000):
        try:
            os.mkdir(path)
        except FileExistsError:
            if _remove_if_stale(path, log):
                continue
            if time.monotonic() >= deadline:
                if log:
                    owner, _ = read_json(path / "owner.json")
                    log("%s is locked by another actor (%s); skipped"
                        % (name, flat((owner or {}).get("session_or_run_id") if isinstance(owner, dict) else None, 80)))
                return None
            time.sleep(0.02)
            continue
        try:
            write_json(path / "owner.json", dict(self_identity(), session_or_run_id=owner_id, acquired_at=utc()))
        except BaseException:
            with contextlib.suppress(OSError):
                os.rmdir(path)
            raise
        return Lock(path, owner_id)
    return None


def release_lock(lock):
    """Remove a lock this process still owns. → False (and nothing removed) when the record names another owner."""
    owner, _ = read_json(lock.path / "owner.json")
    if not isinstance(owner, dict) or owner.get("session_or_run_id") != lock.owner_id \
            or owner.get("pid") != os.getpid():
        return False
    try:
        (lock.path / "owner.json").unlink()
        os.rmdir(lock.path)
    except OSError:
        return False
    return True


@contextlib.contextmanager
def _record_lock(run_dir, action_id):
    lock = acquire_lock(run_dir, "action." + action_id, "kyaction-%d" % os.getpid(), wait_s=LOCK_WAIT_S)
    if lock is None:
        raise LockBusy("action %s is being updated by another actor" % action_id)
    try:
        yield
    finally:
        release_lock(lock)


# ───────────────────────────────────────── records ─────────────────────────────────────────

def _check_id(action_id):
    if not isinstance(action_id, str) or not ID_RE.match(action_id):
        raise ActionInvalid("action id %r is not [A-Za-z0-9][A-Za-z0-9._:-]{0,119}" % (action_id,))
    return action_id


def _plain_json(value, name, want=dict):
    """`value` exactly as JSON will store it, or ActionInvalid: no NaN, no tuple, no non-string key, no object."""
    if not isinstance(value, want):
        raise ActionInvalid("%s must be a JSON %s" % (name, "object" if want is dict else "value"))
    try:
        back = json.loads(canonical(value).decode("utf-8"))
    except (TypeError, ValueError) as e:
        raise ActionInvalid("%s is not JSON-serialisable: %s" % (name, flat(e, 120))) from None
    if back != value:               # a tuple, a non-string key: JSON would silently store something else
        raise ActionInvalid("%s would not be recorded as given (use plain JSON values and string keys)" % name)
    return back


def check_actor(actor):
    """{"role", "holder_kind": cockpit|controller|supervisor, "session_id" and/or "controller_id"} or ActionInvalid."""
    if not isinstance(actor, dict) or set(actor) - {"role", "holder_kind", "session_id", "controller_id"}:
        raise ActionInvalid("actor must be {role, holder_kind, session_id | controller_id}")
    if not isinstance(actor.get("role"), str) or not actor["role"]:
        raise ActionInvalid("actor.role must be a non-empty string")
    if actor.get("holder_kind") not in HOLDER_KINDS:
        raise ActionInvalid("actor.holder_kind must be one of %s" % ", ".join(HOLDER_KINDS))
    ids = [k for k in ("session_id", "controller_id") if k in actor]
    if not ids or any(not isinstance(actor[k], str) or not actor[k] for k in ids):
        raise ActionInvalid("actor needs a non-empty session_id or controller_id")
    return dict(actor)


def record_path(run_dir, action_id):
    return Path(run_dir) / "actions" / (_check_id(action_id) + ".json")


def _dump(record):
    return json.dumps(record, ensure_ascii=False, indent=1) + "\n"


def load(run_dir, action_id):
    """The record, or ActionError (missing) / ActionUnreadable (present but not a record of this id)."""
    path = record_path(run_dir, action_id)
    doc, err = read_json(path)
    if err == "missing":
        raise ActionError("no action record %s" % action_id)
    if err or not isinstance(doc, dict):
        raise ActionUnreadable("%s: %s" % (path.name, err or "not an object"))
    if doc.get("schema") != SCHEMA or doc.get("action_id") != action_id or doc.get("state") not in STATES:
        raise ActionUnreadable("%s: not a %s record of this id with a known state" % (path.name, SCHEMA))
    return doc


def peek(run_dir, action_id):
    """The record, or None when there is none (an unreadable record still raises ActionUnreadable)."""
    if not record_path(run_dir, action_id).exists():
        return None
    return load(run_dir, action_id)


def begin(run_dir, action_id, kind, actor, inputs, target, intended_transition):
    """Persist the intention before the side effect. → (status, record); see the module docstring."""
    path = record_path(run_dir, action_id)
    if not isinstance(kind, str) or not kind:
        raise ActionInvalid("kind must be a non-empty string")
    if not isinstance(intended_transition, str) or not intended_transition:
        raise ActionInvalid("intended_transition must be a non-empty string")
    record = {"schema": SCHEMA, "action_id": action_id, "kind": kind, "actor": check_actor(actor),
              "inputs": _plain_json(inputs, "inputs"), "target": _plain_json(target, "target"),
              "intended_transition": intended_transition, "created_at": utc(), "state": "INTENDED",
              "result": None, "completed_at": None}
    os.makedirs(path.parent, exist_ok=True)
    if write_exclusive(path, _dump(record)):             # exclusive: exactly one concurrent begin gets "new"
        return "new", record
    existing = load(run_dir, action_id)
    for field in ("kind", "inputs", "target"):
        try:
            same = canonical(existing.get(field)) == canonical(record[field])
        except (TypeError, ValueError):
            same = False
        if not same:
            raise ActionConflict("action id %s already records a different %s; it is not this action"
                                 % (action_id, field))
    return {"DONE": "done", "INTENDED": "unfinished", "FAILED": "failed"}[existing["state"]], existing


def _finish(run_dir, action_id, state, result):
    path = record_path(run_dir, action_id)
    result = _plain_json(result, "result")
    with _record_lock(run_dir, action_id):
        record = load(run_dir, action_id)                    # fresh read under the lock
        if record["state"] == "INTENDED":
            record.update(state=state, result=result, completed_at=utc())
            write_atomic(path, _dump(record))
            return record
        if record["state"] == state and canonical(record.get("result")) == canonical(result):
            return record                                    # the same observation again: nothing to write
        raise ActionRefused("action %s is already %s; its observed result is set once" % (action_id, record["state"]))


def complete(run_dir, action_id, result):
    """Record the observed result of a side effect that happened. Exactly once."""
    return _finish(run_dir, action_id, "DONE", result)


def fail(run_dir, action_id, result):
    """Record the observed failure of a side effect that did not happen (or did not complete). Exactly once."""
    return _finish(run_dir, action_id, "FAILED", result)


def retry(run_dir, action_id, actor=None):
    """FAILED → INTENDED, keeping the failed attempt in attempts[]. Refused from any other state: an unfinished
    record is reconciled, never retried blind."""
    path = record_path(run_dir, action_id)
    actor = check_actor(actor) if actor is not None else None
    with _record_lock(run_dir, action_id):
        record = load(run_dir, action_id)
        if record["state"] != "FAILED":
            raise ActionRefused("action %s is %s: retry is only possible from FAILED%s" % (
                action_id, record["state"], " (reconcile it first)" if record["state"] == "INTENDED" else ""))
        attempts = list(record.get("attempts") or [])
        attempts.append({"n": len(attempts) + 1, "actor": record.get("actor"),
                         "started_at": record.get("retried_at") or record.get("created_at"), "state": "FAILED",
                         "result": record.get("result"), "completed_at": record.get("completed_at")})
        record.update(state="INTENDED", result=None, completed_at=None, attempts=attempts, retried_at=utc())
        if actor is not None:
            record["actor"] = actor
        write_atomic(path, _dump(record))
        return record


def _observe(observer, record):
    try:
        answer = observer(copy.deepcopy(record))
    except Exception as e:                                   # an observer that cannot look has seen nothing
        return "unknown", {"error": "observer_raised: %s" % type(e).__name__}
    if not isinstance(answer, (tuple, list)) or len(answer) != 2 or answer[0] not in OUTCOMES:
        return "unknown", {"error": "observer_answer_invalid"}
    outcome, detail = answer
    try:
        detail = _plain_json(detail, "detail", want=dict if outcome == "done" else object)
    except ActionInvalid:
        return "unknown", {"error": "observer_%s_detail_invalid" % outcome}
    return outcome, detail


def reconcile(run_dir, action_id, observer, by=None):
    """Ask real evidence what became of an unfinished action and record the answer in reconciliations[].
    → (outcome, record) with outcome ∈ done | not_done | unknown, or "failed" for a FAILED record (not observed)."""
    path = record_path(run_dir, action_id)
    with _record_lock(run_dir, action_id):
        record = load(run_dir, action_id)
        if record["state"] == "DONE":
            return "done", record
        if record["state"] == "FAILED":
            return "failed", record
        outcome, detail = _observe(observer, record)
        now = utc()
        history = list(record.get("reconciliations") or [])
        entry = {"at": now, "outcome": outcome, "detail": detail, "count": 1}
        if by is not None:
            entry["by"] = flat(by, 120)
        last = history[-1] if history else None
        if last and last.get("outcome") == outcome and last.get("by") == entry.get("by") \
                and canonical(last.get("detail")) == canonical(detail):
            history[-1] = dict(last, count=int(last.get("count", 1)) + 1, last_at=now)
        else:
            history.append(entry)
        record["reconciliations"] = history
        if outcome == "done":
            record.update(state="DONE", result=detail, completed_at=now)
        write_atomic(path, _dump(record))
        return outcome, record


def scan(run_dir):
    """(records, problems): every readable record, and one line per record file that is not readable."""
    directory = Path(run_dir) / "actions"
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return [], []
    records, problems = [], []
    for name in names:
        if name.startswith(".") or not name.endswith(".json"):
            continue
        try:
            records.append(load(run_dir, name[:-5]))
        except ActionError as e:
            problems.append(str(e) if name in str(e) else "%s: %s" % (name, e))
    return records, problems


def _age_key(record):
    when = parse_utc(record.get("created_at"))
    return (when if when is not None else float("inf"), str(record.get("action_id")))


def unfinished(run_dir, strict=True):
    """INTENDED records, oldest first. With strict (the default) an unreadable record file raises
    ActionUnreadable: what cannot be read may be an unfinished side effect."""
    records, problems = scan(run_dir)
    if problems and strict:
        raise ActionUnreadable("; ".join(problems))
    return sorted((r for r in records if r["state"] == "INTENDED"), key=_age_key)


# ───────────────────────────────────────── CLI (read-only) ─────────────────────────────────────────

USAGE = "usage: kyaction.py list | show <action_id> | unfinished        (read-only; $KY_RUN or $KY_ROOT/run)"


def default_run_dir(environ=None):
    e = os.environ if environ is None else environ
    return Path(e.get("KY_RUN") or Path(e.get("KY_ROOT") or "/Users/Dev/kalayantra") / "run")


def _line(record):
    return "%s\t%s\t%s\t%s" % (record["state"], record.get("created_at"), record["action_id"],
                               flat(record.get("kind"), 60))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    run_dir = default_run_dir()
    if argv in (["list"], ["unfinished"]):
        records, problems = scan(run_dir)
        if argv[0] == "unfinished":
            records = [r for r in records if r["state"] == "INTENDED"]
        for record in sorted(records, key=_age_key):
            print(_line(record))
        for problem in problems:
            print("kyaction: UNREADABLE %s" % problem, file=sys.stderr)
        return 1 if problems else 0
    if len(argv) == 2 and argv[0] == "show":
        try:
            print(_dump(load(run_dir, argv[1])), end="")
        except ActionInvalid as e:
            print("kyaction: %s\n%s" % (e, USAGE), file=sys.stderr)
            return 64
        except ActionError as e:
            print("kyaction: %s" % e, file=sys.stderr)
            return 1
        return 0
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
