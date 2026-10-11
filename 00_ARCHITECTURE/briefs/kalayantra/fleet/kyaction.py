#!/usr/bin/env python3
"""kyaction.py — crash-safe action records for KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.1 "Action records" and
"Recovery", §4a.6 "Double-action guard"; B-0c rework rulings R2 "one liveness rule" and R8 "job-authored records").

Before any side effect (push, PR, merge, tracker event, launch, notification, an installed-file write) the actor
persists $KY_RUN/actions/<action_id>.json {inputs, target identity, intended transition}; after it, the OBSERVED
result. A restart reconciles every unfinished record against real evidence before anything is retried.

    status, record = begin(run_dir, action_id, kind, actor, inputs, target, intended_transition)
        "new"          the INTENDED record was created by this call: perform the side effect, then complete()/fail()
        "done"         an earlier attempt finished: skip the side effect, use record["result"]
        "unfinished"   an earlier attempt neither finished nor failed and its first actor is positively gone (or is
                       this very process): reconcile() before anything else
        "in_progress"  an earlier attempt neither finished nor failed and the process that began it is still alive
                       somewhere else, or cannot be told to be gone: it may be in the middle of the side effect.
                       Do nothing — neither the side effect nor a reconciliation — and come back later
        "failed"       an earlier attempt failed: only retry() reopens it (the attempt is kept in attempts[])
    complete(run_dir, action_id, result) / fail(run_dir, action_id, result)      the observed result, exactly once
    retry(run_dir, action_id, actor=None)                                        FAILED → INTENDED, history kept
    outcome, record = reconcile(run_dir, action_id, observer)
        observer(record) returns ("done", {result}) | ("not_done", detail) | ("unknown", detail)
        "done" completes the record with the observed result; "not_done" means the effect is positively absent
        (the caller may perform it now, under the same record); "unknown" changes nothing and permits nothing.
        reconcile() does not ask whether the first actor is still acting: call it only after begin() said
        "unfinished" (or in_progress(record) is False), or while holding the fence that excludes that actor.
    unfinished(run_dir)        INTENDED records, oldest first (an unreadable record is an error, never "finished")
    job_records(run_dir, run_id) / unreadable(run_dir)        what a controller reconciles after a job has exited

Who began a record: `process` {pid, process_start} is stored with every record a controller, supervisor or
cockpit begins (it is what "in_progress" is judged from). It is null for a job's record — the helper process
that writes it exits at once and says nothing about the job — and for a record begun while `ps` could not name
this process; such a record is "unfinished" to a second caller, whose own outer lock is then the only guard.

Actors: {role, holder_kind: cockpit | controller | supervisor, session_id and/or controller_id}, or — for a
record a model job writes about its own side effect — {role, holder_kind: "job", controller_id, run_id}. A job
writes only ids of the form JOB-<run_id>-<slug> (slug: a lower-case letter, then letters, digits, . _ -), and an
id of that form is accepted from a job actor of exactly that run only.

Rules this file enforces (each has a test in tests/test_kycontrol.py):
  * the record is created with an exclusive hard link from a fully written temporary file, so two concurrent
    begin() calls yield exactly one "new" and no reader ever sees a partial record;
  * an existing record is never overwritten by begin(); the same id with a different kind, inputs or target is a
    conflict, not "done";
  * the observed result is set once: repeating the identical observation is a no-op, a different one is refused;
  * every read-modify-write runs under the lock `action.<id>` followed by a fresh read of the record.

Locks (shared with kycommands.py and kyveto.py; the same rule, each with its own copy, in kyloop.py and kyboot.py):
$KY_RUN/locks/<kind>.<id>/owner.json = {session_or_run_id, pid, pgid, process_start, acquired_at}.
  * Liveness has three answers. process_matches(pid, start) → True (alive, the same start identity) · False
    (POSITIVELY gone: ps reports no such process, a zombie, or another start identity) · None (unknown: ps cannot
    be run or times out, the pid is missing or not a positive integer, the start identity cannot be compared).
  * Acquisition is atomic WITH its owner: owner.json is written into a private directory beside the lock, and
    that directory is renamed onto the lock path with the kernel's exclusive rename (macOS renamex_np RENAME_EXCL,
    Linux renameat2 RENAME_NOREPLACE). A lock therefore never exists without an owner. Where the platform or the
    file system has no exclusive rename, the rename is preceded by an existence check; rename(2) itself refuses
    any non-empty directory, so the only thing that could then be replaced is an EMPTY directory that some other
    program created in that instant.
  * A lock is taken over ONLY when its owner is positively gone. A lock without a readable owner record, an
    owner that cannot be judged, an owner whose recorded job (`child`) is "pending", unidentified, alive or not
    provably gone (leader positively gone AND killpg(pgid, 0) → no such process) is never taken over and never
    removed by age: acquire_lock raises LockUnknown, which its caller reports as needing attention.
  * Takeover is verify-after-rename, serialised by flock on locks/.takeover.guard: the stale lock is renamed to a
    private grave, the grave's owner.json is re-read, and only if it is exactly the owner that was judged gone
    (same id, pid and process_start) is it removed; anything else is put back and nothing is taken.
  * A second actor skips and logs. A lock is ALWAYS followed by a fresh handled-state check by its caller.

CLI   kyaction.py list | show <action_id> | unfinished                      read-only
      kyaction.py begin | complete | fail                                  for model jobs; one JSON object on stdin
  The job verbs act in $KY_RUN (it must be set, absolute and an existing directory) and only inside the caller's
  own namespace: the id must be JOB-$KY_RUN_ID-<slug>, and an existing record must have been written by a job of
  that very run.
      begin     stdin {"action_id", "kind", "inputs": {…}, "target": {…}, "intended_transition"[, "actor"]}
                actor = {"role", "controller_id"} (holder_kind "job" and run_id $KY_RUN_ID are filled in; when given
                they must agree). Without it the role is $KY_ROLE and the controller $KY_CONTROLLER_ID.
                stdout {"action_id", "status", "state"}
      complete  stdin {"action_id", "result": {…}}      the side effect happened; stdout {"action_id", "state"}
      fail      stdin {"action_id", "result": {…}}      it did not (or not completely)
  Exit codes of the job verbs:
      0   begin: status "new" — perform the side effect now, then `complete` or `fail`
          complete / fail: recorded (or the identical observation was recorded before)
      3   begin only: the record already existed (stdout says done | unfinished | in_progress | failed). Do NOT
          perform the side effect; the controller reconciles an unfinished record after the job has exited
      1   refused by the record: an id that already names a different action, a result that is already set
          differently, no such record, an unreadable record, or its lock is busy or cannot be judged
      64  usage: stdin is not the expected JSON object, or the actor is incomplete
      66  $KY_RUN is unset, not absolute or not a directory
      75  namespace: $KY_RUN_ID is unset or malformed, the id is not JOB-$KY_RUN_ID-<slug>, or the record
          belongs to another run or was not written by a job
  Exit codes of the read-only verbs: 0 ok · 1 not found / an unreadable record exists · 64 usage.
Python >= 3.9, standard library only.
"""
from __future__ import annotations

import calendar
import contextlib
import copy
import errno
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
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}\Z")
LOCK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}\Z")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
JOB_SLUG_RE = re.compile(r"^[a-z][a-z0-9._-]{0,47}\Z")      # a letter first: a run's numeric suffix is never a slug
JOB_PREFIX = "JOB-"
HOLDER_KINDS = ("cockpit", "controller", "supervisor", "job")
STATES = ("INTENDED", "DONE", "FAILED")
OUTCOMES = ("done", "not_done", "unknown")
LOCK_WAIT_S = 10.0              # how long a record update waits for another actor's update of the same record
LOCK_POLL_S = 0.05
OWNER_READ_TRIES = 5            # a lock directory seen without owner.json is re-read this often (20 ms apart): only
OWNER_READ_PAUSE_S = 0.02       # another program's two-step release can show one; afterwards it is "unknown"
PS = "/bin/ps"
PS_TIMEOUT_S = 10
LSTART_FMT = "%a %b %d %H:%M:%S %Y"
STDIN_LIMIT = 1 << 20
_TS = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(?:Z|\+00:00)\Z")
_IDENTITY = {}
_EXCLUSIVE = []                 # [callable or None] once the platform's exclusive rename has been looked up


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


class LockUnknown(ActionError):
    """A lock exists whose owner cannot be judged alive or gone. It is never taken over; the caller raises
    attention. `.name` is the lock, `.detail` what could not be established."""

    def __init__(self, name, detail):
        super().__init__("lock %s: %s — an unknown owner is never taken over" % (name, detail))
        self.name, self.detail = name, detail


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
    except (OSError, ValueError):
        return None


def flat(text, limit=300):
    return " ".join(str(text if text is not None else "").split())[:limit]


def _not_json(name):
    raise ValueError("%s is not JSON" % name)


def read_json(path):
    """(object, None) or (None, reason). Never raises."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f, parse_constant=_not_json), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError, RecursionError) as e:
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


# ───────────────────────────────────── liveness: three answers (ruling R2) ─────────────────────────────────────

def _ps(pid, columns):
    """stdout of `ps -o <columns> -p <pid>` → (returncode, stdout, stderr), or None when ps cannot be asked."""
    try:
        r = subprocess.run([PS, "-o", columns, "-p", str(pid)], capture_output=True, text=True,
                           env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}, timeout=PS_TIMEOUT_S,
                           stdin=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _real_pid(pid):
    return isinstance(pid, int) and not isinstance(pid, bool) and pid > 0


def ps_probe(pid):
    """("alive", stat, lstart) · ("gone",) when ps positively reports no such process · None when the pid is not
    a positive integer, ps cannot be run, times out, or answers something that cannot be read. Unknown is never
    "gone". `ps -o lstart=` is the pinned start identity."""
    if not _real_pid(pid):
        return None
    answer = _ps(pid, "stat=,lstart=")
    if answer is None:
        return None
    rc, out, err = answer
    if rc == 1 and not out and not err:
        return ("gone",)
    parts = out.split(None, 1)
    if rc != 0 or len(parts) < 2:
        return None
    return "alive", parts[0], parts[1].strip()


def ps_identity(pid):
    """(stat, lstart) of a live process, or None when it is gone OR could not be observed. Only for reading an
    identity; whether a process is gone is decided by process_matches."""
    probe = ps_probe(pid)
    return (probe[1], probe[2]) if probe and probe[0] == "alive" else None


def process_matches(pid, start):
    """True: alive with this start identity. False: POSITIVELY gone — ps reports no such process, a zombie, or
    another process under a reused pid (both start identities readable and different). None: it cannot be told
    — a pid that is missing or not a positive integer, a ps that cannot be run or times out, or a recorded start
    identity that cannot be compared. Never take over, never call it finished, on None."""
    probe = ps_probe(pid)
    if probe is None:
        return None
    if probe[0] == "gone" or probe[1].startswith("Z"):
        return False
    if not isinstance(start, str) or not start.strip():
        return None
    a, b = " ".join(start.split()), " ".join(probe[2].split())
    if a == b:
        return True
    try:
        return time.strptime(a, LSTART_FMT) == time.strptime(b, LSTART_FMT)
    except ValueError:
        return None


def self_identity():
    """{pid, pgid, process_start} of this process (cached per pid, so a forked child gets its own)."""
    pid = os.getpid()
    if pid not in _IDENTITY or _IDENTITY[pid]["process_start"] is None:
        ident = ps_identity(pid)
        _IDENTITY.clear()
        _IDENTITY[pid] = {"pid": pid, "pgid": os.getpgid(0), "process_start": ident[1] if ident else None}
    return dict(_IDENTITY[pid])


def is_self_or_ancestor(pid):
    """True: `pid` is this process or one of its ancestors. False: positively neither (the chain was followed to
    its root). None: `pid` is not a positive integer, or the ancestry could not be read."""
    if not _real_pid(pid):
        return None
    if pid == os.getpid():
        return True
    current = os.getppid()
    for _ in range(64):
        if current == pid:
            return True
        if current <= 1:
            return False
        answer = _ps(current, "ppid=")
        if answer is None or answer[0] != 0 or not answer[1].isdigit():
            return None                          # ps cannot answer, or the chain changed under us
        current = int(answer[1])
    return None


def owner_state(owner):
    """→ ("live" | "gone" | "unknown", detail) for a lock's owner record. "gone" is the only state in which the
    lock may be taken over: the owner process is positively gone and so is any job it recorded as `child`."""
    if not isinstance(owner, dict):
        return "unknown", "it has no readable owner record"
    alive = process_matches(owner.get("pid"), owner.get("process_start"))
    if alive is True:
        return "live", None
    if alive is None:
        return "unknown", "its recorded owner (pid %r) cannot be confirmed alive or gone" % (owner.get("pid"),)
    child = owner.get("child")
    if child is None:
        return "gone", None
    if not isinstance(child, dict):              # "pending" (written before the launch) or anything unidentified
        return "unknown", "its owner is gone but the job it recorded is %s" % (
            "pending" if child == "pending" else "unidentified")
    pgid = child.get("pgid")
    if process_matches(child.get("pid"), child.get("process_start")) is not False or not _real_pid(pgid) or pgid == 1:
        return "unknown", "its owner is gone but the job it recorded (pid %r) is alive or cannot be confirmed gone" % (
            child.get("pid"),)
    try:
        os.killpg(pgid, 0)                       # signal 0: nothing is sent, the group is only looked up
    except ProcessLookupError:
        return "gone", None
    except OSError:
        pass
    return "unknown", "its owner is gone but the process group %d of its job still has members" % pgid


# ───────────────────────────────────────── locks (§4a.6, ruling R2) ─────────────────────────────────────────

class Lock:
    __slots__ = ("path", "owner_id")

    def __init__(self, path, owner_id):
        self.path, self.owner_id = Path(path), owner_id


def lock_path(run_dir, name):
    if not isinstance(name, str) or not LOCK_RE.match(name) or name in (".", ".."):
        raise ActionInvalid("lock name %r is not [A-Za-z0-9][A-Za-z0-9._:-]{0,199}" % (name,))
    return Path(run_dir) / "locks" / name


def lock_owner(run_dir, name):
    """(owner.json object, None) or (None, reason) for $KY_RUN/locks/<name>."""
    owner, err = read_json(lock_path(run_dir, name) / "owner.json")
    if err:
        return None, err
    return (owner, None) if isinstance(owner, dict) else (None, "unreadable: not an object")


def _exclusive_rename():
    """The platform's rename-unless-the-target-exists as f(src, dst) → errno (0 = renamed), or None."""
    if not _EXCLUSIVE:
        call = None
        try:
            import ctypes
            libc = ctypes.CDLL(None, use_errno=True)
            if sys.platform == "darwin":
                fn = libc.renamex_np                         # int renamex_np(const char *, const char *, unsigned)
                fn.argtypes, fn.restype = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint], ctypes.c_int

                def call(src, dst):
                    ctypes.set_errno(0)
                    return 0 if fn(src, dst, 0x4) == 0 else (ctypes.get_errno() or errno.EIO)       # RENAME_EXCL
            elif sys.platform.startswith("linux"):
                fn = libc.renameat2                          # int renameat2(int, const char *, int, const char *, unsigned)
                fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
                fn.restype = ctypes.c_int

                def call(src, dst):
                    ctypes.set_errno(0)
                    return 0 if fn(-100, src, -100, dst, 1) == 0 else (ctypes.get_errno() or errno.EIO)  # NOREPLACE
        except Exception:                                    # no ctypes, no libc, no such symbol: the fallback below
            call = None
        _EXCLUSIVE.append(call)
    return _EXCLUSIVE[0]


def rename_exclusive(src, dst):
    """Rename `src` onto `dst` only if nothing is at `dst`; FileExistsError otherwise. See the module docstring
    for the fallback where the kernel offers no exclusive rename."""
    call = _exclusive_rename()
    if call is not None:
        code = call(os.fsencode(str(src)), os.fsencode(str(dst)))
        if code == 0:
            return
        if code in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(code, os.strerror(code), str(dst))
        if code not in (errno.ENOTSUP, errno.EINVAL, errno.ENOSYS, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)):
            raise OSError(code, os.strerror(code), str(dst))
    if os.path.lexists(dst):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dst))
    try:
        os.rename(src, dst)
    except OSError as e:
        if e.errno in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOTDIR, errno.EISDIR):
            raise FileExistsError(e.errno, os.strerror(e.errno), str(dst)) from None
        raise


def _private(path, tag):
    return path.parent / (".%s.%s.%d.%s" % (path.name, tag, os.getpid(), secrets.token_hex(4)))


def _discard(directory):
    """Remove a private directory and the files in it; whatever cannot be removed is left where it is."""
    with contextlib.suppress(OSError):
        for entry in os.listdir(directory):
            with contextlib.suppress(OSError):
                os.unlink(os.path.join(directory, entry))
        os.rmdir(directory)


def _same_owner(a, b):
    return isinstance(a, dict) and isinstance(b, dict) and all(
        a.get(k) == b.get(k) for k in ("session_or_run_id", "pid", "process_start"))


def _try_acquire(path, owner_id):
    """Put a complete lock — the directory WITH its owner.json — in place, or change nothing. → True / False."""
    staging = _private(path, "acq")
    os.mkdir(staging)
    try:
        record = dict(self_identity(), session_or_run_id=owner_id, acquired_at=utc())
        with open(staging / "owner.json", "wb") as f:
            f.write((json.dumps(record, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        rename_exclusive(staging, path)
    except FileExistsError:
        _discard(staging)
        return False
    except BaseException:
        _discard(staging)
        raise
    _fsync_dir(path.parent)
    return True


def _existing(path):
    """What holds the lock path now → (state, owner, detail), state ∈ free | live | gone | unknown."""
    owner = None
    for attempt in range(OWNER_READ_TRIES):
        owner, err = read_json(path / "owner.json")
        if isinstance(owner, dict):
            break
        if not os.path.lexists(path):
            return "free", None, None
        if err != "missing":
            break
        if attempt + 1 < OWNER_READ_TRIES:
            time.sleep(OWNER_READ_PAUSE_S)
    state, detail = owner_state(owner)
    return state, owner if isinstance(owner, dict) else None, detail


def _take_over(path, judged, log):
    """Remove the lock iff it is STILL the lock whose owner was judged positively gone (verify after rename).
    → True when the caller should try to acquire again, False when nothing was taken."""
    try:
        guard = os.open(str(path.parent / ".takeover.guard"), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return False
    try:
        fcntl.flock(guard, fcntl.LOCK_EX)
        current, err = read_json(path / "owner.json")
        if not _same_owner(current, judged):
            return True                              # released, or taken by another contender: judge afresh
        grave = _private(path, "grave")
        try:
            os.rename(path, grave)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        buried, _ = read_json(grave / "owner.json")
        if not _same_owner(buried, judged):          # it changed hands between the look and the rename: not ours
            try:
                rename_exclusive(grave, path)
            except OSError:
                raise LockUnknown(path.name, "a lock that had changed hands was moved aside and could not be put "
                                             "back; it is kept at %s" % grave) from None
            return False
        _discard(grave)
        if log:
            log("stale lock %s taken over (previous owner %s, pid %s, positively gone)"
                % (path.name, flat(judged.get("session_or_run_id"), 80), judged.get("pid")))
        return True
    finally:
        os.close(guard)


def acquire_lock(run_dir, name, owner_id, wait_s=0.0, log=None):
    """Take $KY_RUN/locks/<name>. → Lock, or None when another LIVE actor holds it (the caller skips; `log` is
    told). LockUnknown when the lock exists and its owner cannot be judged — never taken over, the caller raises
    attention. The caller must follow a successful acquisition with a fresh handled-state check."""
    path = lock_path(run_dir, name)
    if not isinstance(owner_id, str) or not owner_id:
        raise ActionInvalid("a lock owner id must be a non-empty string")
    os.makedirs(path.parent, exist_ok=True)
    deadline, straight = time.monotonic() + max(0.0, wait_s), 0
    for _ in range(100000):
        if _try_acquire(path, owner_id):
            return Lock(path, owner_id)
        state, owner, detail = _existing(path)
        if state == "free" or (state == "gone" and _take_over(path, owner, log)):
            straight += 1                            # released or taken over just now: straight back to acquire
            if straight <= 20:
                continue
        straight = 0
        if time.monotonic() >= deadline:
            if state == "unknown":
                if log:
                    log("%s is locked and %s; it is not taken over" % (name, detail))
                raise LockUnknown(name, detail)
            if log:
                log("%s is locked by another actor (%s); skipped"
                    % (name, flat((owner or {}).get("session_or_run_id"), 80)))
            return None
        time.sleep(LOCK_POLL_S)
    return None


def release_lock(lock):
    """Remove a lock this process still owns, in one rename. → False (and nothing removed) when the record names
    another owner."""
    def mine(owner):
        return isinstance(owner, dict) and owner.get("session_or_run_id") == lock.owner_id \
            and owner.get("pid") == os.getpid()

    owner, _ = read_json(lock.path / "owner.json")
    if not mine(owner):
        return False
    grave = _private(lock.path, "released")
    try:
        os.rename(lock.path, grave)
    except OSError:
        return False
    buried, _ = read_json(grave / "owner.json")
    if not mine(buried):                             # it was no longer this process's lock: put it back
        with contextlib.suppress(OSError):
            rename_exclusive(grave, lock.path)
        return False
    _discard(grave)
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
        raise ActionInvalid("action id %r is not [A-Za-z0-9][A-Za-z0-9._:-]{0,159}" % (action_id,))
    return action_id


def _plain_json(value, name, want=dict):
    """`value` exactly as JSON will store it, or ActionInvalid: no NaN, no tuple, no non-string key, no object."""
    if not isinstance(value, want):
        raise ActionInvalid("%s must be a JSON %s" % (name, "object" if want is dict else "value"))
    try:
        back = json.loads(canonical(value).decode("utf-8"))
    except (TypeError, ValueError, RecursionError) as e:
        raise ActionInvalid("%s is not JSON-serialisable: %s" % (name, flat(e, 120))) from None
    if back != value:               # a tuple, a non-string key: JSON would silently store something else
        raise ActionInvalid("%s would not be recorded as given (use plain JSON values and string keys)" % name)
    return back


def check_actor(actor):
    """{"role", "holder_kind": cockpit|controller|supervisor, "session_id" and/or "controller_id"}, or
    {"role", "holder_kind": "job", "controller_id", "run_id"}; ActionInvalid otherwise."""
    if not isinstance(actor, dict):
        raise ActionInvalid("actor must be an object")
    if not isinstance(actor.get("role"), str) or not actor["role"]:
        raise ActionInvalid("actor.role must be a non-empty string")
    if actor.get("holder_kind") not in HOLDER_KINDS:
        raise ActionInvalid("actor.holder_kind must be one of %s" % ", ".join(HOLDER_KINDS))
    if actor["holder_kind"] == "job":
        if set(actor) != {"role", "holder_kind", "controller_id", "run_id"}:
            raise ActionInvalid("a job actor is exactly {role, holder_kind, controller_id, run_id}")
        if not isinstance(actor["controller_id"], str) or not actor["controller_id"]:
            raise ActionInvalid("actor.controller_id must be a non-empty string")
        if not isinstance(actor["run_id"], str) or not RUN_ID_RE.match(actor["run_id"]):
            raise ActionInvalid("actor.run_id must be a run id ([A-Za-z0-9][A-Za-z0-9._-]{0,95})")
        return dict(actor)
    if set(actor) - {"role", "holder_kind", "session_id", "controller_id"}:
        raise ActionInvalid("actor must be {role, holder_kind, session_id | controller_id}")
    ids = [k for k in ("session_id", "controller_id") if k in actor]
    if not ids or any(not isinstance(actor[k], str) or not actor[k] for k in ids):
        raise ActionInvalid("actor needs a non-empty session_id or controller_id")
    return dict(actor)


def job_slug(action_id, run_id):
    """The slug of `action_id` inside the namespace of `run_id` (JOB-<run_id>-<slug>), or None."""
    if not isinstance(action_id, str) or not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        return None
    prefix = "%s%s-" % (JOB_PREFIX, run_id)
    slug = action_id[len(prefix):] if action_id.startswith(prefix) else ""
    return slug if JOB_SLUG_RE.match(slug) and ID_RE.match(action_id) else None


def _check_namespace(action_id, actor):
    """A job writes only its own run's JOB-<run_id>-<slug>; nobody else writes an id of that form."""
    if actor["holder_kind"] == "job":
        if job_slug(action_id, actor["run_id"]) is None:
            raise ActionInvalid("a job of run %s records only ids of the form %s%s-<slug> (slug: a lower-case "
                                "letter, then letters, digits, . _ -); %r is outside that namespace"
                                % (actor["run_id"], JOB_PREFIX, actor["run_id"], action_id))
    elif action_id.startswith(JOB_PREFIX):
        raise ActionInvalid("ids beginning %s are reserved for job actors; %r was given by a %s"
                            % (JOB_PREFIX, action_id, actor["holder_kind"]))


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


def _process_of(actor):
    """Who begins the record, as begin() stores it: {pid, process_start}, or None (see the module docstring)."""
    if actor["holder_kind"] == "job":
        return None
    me = self_identity()
    return {"pid": me["pid"], "process_start": me["process_start"]} if me["process_start"] else None


def in_progress(record):
    """True when the process that began an INTENDED record is alive somewhere else, or cannot be told gone: it
    may be in the middle of the side effect, so nobody else reconciles, repeats or fails the record now."""
    process = record.get("process")
    if record.get("state") != "INTENDED" or not isinstance(process, dict):
        return False                                 # not recorded: the caller's own outer lock is the only guard
    alive = process_matches(process.get("pid"), process.get("process_start"))
    if alive is False:
        return False
    return not (alive is True and process.get("pid") == os.getpid())


def begin(run_dir, action_id, kind, actor, inputs, target, intended_transition):
    """Persist the intention before the side effect. → (status, record); see the module docstring."""
    path = record_path(run_dir, action_id)
    if not isinstance(kind, str) or not kind:
        raise ActionInvalid("kind must be a non-empty string")
    if not isinstance(intended_transition, str) or not intended_transition:
        raise ActionInvalid("intended_transition must be a non-empty string")
    actor = check_actor(actor)
    _check_namespace(action_id, actor)
    record = {"schema": SCHEMA, "action_id": action_id, "kind": kind, "actor": actor,
              "inputs": _plain_json(inputs, "inputs"), "target": _plain_json(target, "target"),
              "intended_transition": intended_transition, "created_at": utc(), "state": "INTENDED",
              "result": None, "completed_at": None, "process": _process_of(actor)}
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
    if existing["state"] == "INTENDED":
        return ("in_progress" if in_progress(existing) else "unfinished"), existing
    return {"DONE": "done", "FAILED": "failed"}[existing["state"]], existing


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
    if actor is not None:
        _check_namespace(action_id, actor)
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
        try:
            record["process"] = _process_of(check_actor(record.get("actor")))
        except ActionInvalid:
            record["process"] = None
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


def _scan(run_dir):
    """(records, [(file name, reason)])."""
    directory = Path(run_dir) / "actions"
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return [], []
    records, bad = [], []
    for name in names:
        if name.startswith(".") or not name.endswith(".json"):
            continue                                         # temporary files, the quarantine directory
        try:
            records.append(load(run_dir, name[:-5]))
        except ActionError as e:
            bad.append((name, str(e)))
    return records, bad


def scan(run_dir):
    """(records, problems): every readable record, and one line per record file that is not readable."""
    records, bad = _scan(run_dir)
    return records, [why if name in why else "%s: %s" % (name, why) for name, why in bad]


def unreadable(run_dir):
    """[(file name, reason)] for every record file under actions/ that cannot be read as an action record."""
    return _scan(run_dir)[1]


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


def is_job_record(record, run_id):
    """True iff `record` was written by a job of exactly this run, under an id of that run's namespace."""
    actor = record.get("actor") if isinstance(record, dict) else None
    return isinstance(actor, dict) and actor.get("holder_kind") == "job" and actor.get("run_id") == run_id \
        and job_slug(record.get("action_id"), run_id) is not None


def job_records(run_dir, run_id, state=None):
    """The readable records the jobs of run `run_id` wrote, oldest first; `state` keeps one state only. A file
    that cannot be read is not in this list: see unreadable()."""
    return sorted((r for r in _scan(run_dir)[0] if is_job_record(r, run_id) and state in (None, r["state"])),
                  key=_age_key)


# ───────────────────────────────────────── CLI ─────────────────────────────────────────

USAGE = ("usage: kyaction.py list | show <action_id> | unfinished        (read-only; $KY_RUN or $KY_ROOT/run)\n"
         "       kyaction.py begin | complete | fail                    (model jobs: one JSON object on stdin;\n"
         "                                                               $KY_RUN, ids JOB-$KY_RUN_ID-<slug> only)")
JOB_VERBS = ("begin", "complete", "fail")
BEGIN_KEYS = ("action_id", "kind", "inputs", "target", "intended_transition")


def default_run_dir(environ=None):
    e = os.environ if environ is None else environ
    return Path(e.get("KY_RUN") or Path(e.get("KY_ROOT") or "/Users/Dev/kalayantra") / "run")


def _line(record):
    return "%s\t%s\t%s\t%s" % (record["state"], record.get("created_at"), record["action_id"],
                               flat(record.get("kind"), 60))


class _Exit(Exception):
    def __init__(self, code, text):
        super().__init__(text)
        self.code, self.text = code, text


def _job_actor(given, run_id, environ):
    """The job's actor from stdin's optional `actor` and the environment; _Exit(64 | 75) when it cannot be built."""
    given = {} if given is None else given
    if not isinstance(given, dict) or set(given) - {"role", "holder_kind", "controller_id", "run_id"}:
        raise _Exit(64, "actor must be {role, controller_id} (holder_kind \"job\" and run_id are filled in)")
    if given.get("holder_kind", "job") != "job":
        raise _Exit(75, "these verbs write job records only (actor.holder_kind %r)" % (given.get("holder_kind"),))
    if given.get("run_id", run_id) != run_id:
        raise _Exit(75, "actor.run_id %r is not $KY_RUN_ID" % (given.get("run_id"),))
    actor = {"role": given.get("role") or environ.get("KY_ROLE"), "holder_kind": "job",
             "controller_id": given.get("controller_id") or environ.get("KY_CONTROLLER_ID"), "run_id": run_id}
    try:
        return check_actor(actor)
    except ActionInvalid as e:
        raise _Exit(64, "%s (give actor.role and actor.controller_id on stdin, or set $KY_ROLE and "
                        "$KY_CONTROLLER_ID)" % e) from None


def job_verb(verb, stdin_text, environ):
    """One job verb. → (exit code, stdout object or None, stderr text or None). See the module docstring."""
    try:
        run_text = environ.get("KY_RUN") or ""
        if not os.path.isabs(run_text) or not os.path.isdir(run_text):
            raise _Exit(66, "$KY_RUN must name the existing run directory (absolute path)")
        run_dir, run_id = Path(run_text), environ.get("KY_RUN_ID") or ""
        if not RUN_ID_RE.match(run_id):
            raise _Exit(75, "$KY_RUN_ID is unset or not a run id: a job records only inside its own namespace")
        try:
            doc = json.loads(stdin_text, parse_constant=_not_json) if len(stdin_text) <= STDIN_LIMIT else None
        except (ValueError, RecursionError):
            doc = None
        wanted = set(BEGIN_KEYS) if verb == "begin" else {"action_id", "result"}
        if not isinstance(doc, dict) or not wanted <= set(doc) or set(doc) - wanted - ({"actor"} if verb == "begin"
                                                                                       else set()):
            raise _Exit(64, "%s needs exactly {%s}%s on stdin" % (verb, ", ".join(sorted(wanted)),
                                                                  " and optionally actor" if verb == "begin" else ""))
        action_id = doc["action_id"]
        if job_slug(action_id, run_id) is None:
            raise _Exit(75, "action id %r is outside this job's namespace %s%s-<slug>" % (action_id, JOB_PREFIX, run_id))
        if verb == "begin":
            actor = _job_actor(doc.get("actor"), run_id, environ)
            existing = peek(run_dir, action_id)
            if existing is not None and not is_job_record(existing, run_id):
                raise _Exit(75, "action %s exists and was not written by a job of run %s" % (action_id, run_id))
            status, record = begin(run_dir, action_id, doc["kind"], actor, doc["inputs"], doc["target"],
                                   doc["intended_transition"])
            return (0 if status == "new" else 3), {"action_id": action_id, "status": status,
                                                   "state": record["state"]}, None
        if not is_job_record(load(run_dir, action_id), run_id):
            raise _Exit(75, "action %s was not written by a job of run %s" % (action_id, run_id))
        record = (complete if verb == "complete" else fail)(run_dir, action_id, doc["result"])
        return 0, {"action_id": action_id, "state": record["state"]}, None
    except _Exit as e:
        return e.code, None, e.text
    except ActionInvalid as e:
        return 64, None, str(e)
    except ActionError as e:
        return 1, None, "%s: %s" % (type(e).__name__, e)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 1 and argv[0] in JOB_VERBS:
        code, out, err = job_verb(argv[0], sys.stdin.read(STDIN_LIMIT + 1), os.environ)
        if out is not None:
            print(json.dumps(out, ensure_ascii=False, sort_keys=True))
        if err is not None:
            print("kyaction: REFUSED %s" % err, file=sys.stderr)
        return code
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
