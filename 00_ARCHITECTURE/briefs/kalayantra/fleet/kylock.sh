#!/bin/bash
# kylock.sh v1.0 — the atomic role lock of KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.2, §6, §11; KU-02; ruling R2).
# status: built by packet KV3-B-KYLOCK, pending its independent review.
# changelog: v1.0 (2026-10-12) first version.
#
#   kylock.sh acquire <role> <identity>                  take $KY_RUN/locks/<role> for the calling session
#   kylock.sh release <role> <identity>                  remove the session's test databases, THEN the lock
#   kylock.sh child   <role> <identity> pending|none|<JSON {run_id, pid, pgid, process_start}>
#   kylock.sh status  <role>                             report, change nothing
#
# The lock is the directory $KY_RUN/locks/<role> holding owner.json with exactly the keys kyloop.py writes:
# session_or_run_id, holder_kind (controller | cockpit), pid, pgid, process_start (`LC_ALL=C ps -o lstart=`),
# acquired_at (UTC), child (null | "pending" | {run_id, pid, pgid, process_start}).
#
# HOLDER. The recorded process is the nearest ancestor of this script that is not a shell (sh, bash, zsh, dash,
# ksh; a login shell's leading `-` dropped): a transient tool-shell pid is never an identity. An identity
# `CTL-…-<pid>` is a controller and <pid> must be that holder; any other identity is a cockpit session id.
#
# LIVENESS (ruling R2) is True | False | unknown. False is POSITIVE only: ps reports no such process, a zombie,
# or another start identity under the same pid. A lock is taken over ONLY from an owner that is positively gone
# and whose recorded child is positively gone too (its leader gone AND its process group empty; "pending" or an
# unidentified child never is). An unknown owner is never taken over and nothing is ever removed by its age.
# A lock never exists without its owner (owner.json is built in a private directory that is renamed onto the
# lock path exclusively), and a takeover is verify-after-rename under flock on locks/.takeover.guard.
#
# RELEASE (KU-02, ruling P26). Only the recorded owner releases. It first runs
#   /bin/bash "$KY_FLEET/local_db.sh" close --session <identity>        (900 s; needs KY_SCRATCH)
# and ONLY that step's exit 0 buries the lock. Missing, non-zero or timed out: the lock is KEPT (exit 74).
# A takeover never runs this step: nobody removes another session's databases.
#
# Stdout: EXACTLY one line — `kylock: <verb> role=<role> state=<state> holder=<identity> pid=<pid>` (`-` where
# there is none), plus `took_over=<old identity>`, `already_held=1`, `child=…` and, last, `test_hook=…` when a
# tests-only hook is in force. Reasons go to stderr.
# Exit: 0  acquired · released · recorded · every `status` (state=free|live|cockpit|gone|unknown)
#       64 usage, a relative KY_RUN, or a refused tests-only hook
#       70 role or identity outside the grammar, holder unidentifiable, identity/pid disagree, or the lock
#          could not be worked on — nothing is written
#       73 release / child by anyone but the recorded owner (identity, holder pid, start identity)
#       74 release: the database removal is not proven — the lock is kept
#       75 a live non-cockpit owner holds the lock, or the race for it was lost
#       76 a live cockpit holds the lock
#       77 the owner is unknown — untouched
# Env: KY_RUN (default ${KY_ROOT:-/Users/Dev/kalayantra}/run), KY_FLEET (default: this script's directory).
# Tests only, refused when KY_RUN is /Users/Dev/kalayantra/run: KY_LOCK_PS (absolute path used instead of
# /bin/ps) and KY_LOCK_DB_TIMEOUT_S (a shorter limit for the database step).
set -u

KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
if [ -z "${KY_FLEET:-}" ]; then
  KY_FLEET="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)" || KY_FLEET=""
fi
export KY_RUN KY_FLEET

PY="$(command -v python3 2>/dev/null)" || PY=""
if [ -z "$PY" ]; then
  echo "kylock: python3 not found; nothing was read or written" >&2
  echo "kylock: - role=- state=error holder=- pid=-"
  exit 70
fi

# exec: the program below IS this script's process, so its parent is this script's caller
exec "$PY" -I -B /dev/fd/3 "$@" 3<<'KYLOCK_PY'
import contextlib
import errno
import fcntl
import json
import os
import re
import secrets
import signal
import stat
import subprocess
import sys
import time

PROD_RUN = "/Users/Dev/kalayantra/run"
ROLE_RE = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
IDENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
CTL_RE = re.compile(r"CTL-.+-([1-9][0-9]*)\Z")                    # kyloop.py: CTL-<ROLE>-<UTC stamp>-<pid>
SHELLS = ("sh", "bash", "zsh", "dash", "ksh")
LSTART_FMT = "%a %b %d %H:%M:%S %Y"
OWNER_IDENTITY = ("session_or_run_id", "pid", "process_start")    # what makes two owner records the same owner
CHILD_KEYS = {"run_id", "pid", "pgid", "process_start"}
PS_TIMEOUT_S = 10
DB_TIMEOUT_S = 900
OWNER_WAIT = (8, 0.25)                  # tries × seconds for an acquirer that makes its lock in two steps
USAGE = ("usage: kylock.sh acquire <role> <identity> | release <role> <identity> | "
         "child <role> <identity> pending|none|<JSON> | status <role>")
ARGC = {"acquire": 2, "release": 2, "child": 3, "status": 1}
EX_OK, EX_USAGE, EX_REFUSED, EX_NOT_OWNER, EX_KEPT, EX_LIVE, EX_COCKPIT, EX_UNKNOWN = 0, 64, 70, 73, 74, 75, 76, 77

CFG = {"ps": "/bin/ps", "db_timeout": DB_TIMEOUT_S, "hooks": [], "run": None, "fleet": None}


# ───────────────────────────────────────── output ─────────────────────────────────────────

def say(text):
    sys.stderr.write("kylock: %s\n" % " ".join(str(text).split()))
    sys.stderr.flush()


def real_pid(pid):
    return isinstance(pid, int) and not isinstance(pid, bool) and pid > 0


def show(value):
    """A recorded value as ONE token of the status line: nothing in it can add a field or a line."""
    if value is None:
        return "-"
    if not isinstance(value, str):
        return "?"
    return re.sub(r"[^A-Za-z0-9_.:-]", "?", value)[:64] or "-"


def emit(verb, role, state, holder=None, pid=None, **extra):
    parts = ["kylock:", verb, "role=%s" % (role or "-"), "state=%s" % state, "holder=%s" % show(holder),
             "pid=%s" % (pid if real_pid(pid) else "-")]
    parts += ["%s=%s" % (k, show(v)) for k, v in extra.items()]
    if CFG["hooks"]:
        parts.append("test_hook=" + ",".join(CFG["hooks"]))
    sys.stdout.write(" ".join(parts) + "\n")
    sys.stdout.flush()


# ───────────────────────────────────────── processes (ruling R2) ─────────────────────────────────────────

def ps(pid, columns):
    """`ps -o <columns> -p <pid>` → (returncode, stdout, stderr), or None when ps cannot be asked."""
    try:
        r = subprocess.run([CFG["ps"], "-o", columns, "-p", str(pid)], capture_output=True, text=True,
                           env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}, timeout=PS_TIMEOUT_S,
                           stdin=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def ps_probe(pid):
    """("alive", stat, lstart) · ("gone",) when ps positively reports no such process · None when the pid is not
    a positive integer, ps cannot be run, times out, or answers something that cannot be read. Unknown is never
    "gone"."""
    if not real_pid(pid):
        return None
    answer = ps(pid, "stat=,lstart=")
    if answer is None:
        return None
    rc, out, err = answer
    if rc == 1 and not out and not err:
        return ("gone",)
    parts = out.split(None, 1)
    if rc != 0 or len(parts) < 2:
        return None
    return "alive", parts[0], parts[1].strip()


def process_matches(pid, start):
    """True: alive with this start identity. False: POSITIVELY gone — no such process, a zombie, or another
    process under a reused pid (both start identities readable and different). None: it cannot be told."""
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


def owner_state(owner):
    """→ ("live" | "gone" | "unknown", detail). "gone" is the only state in which a lock may be taken over: the
    owner process is positively gone and so is any child it recorded."""
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
    if not isinstance(child, dict):             # "pending" (written before the launch) or anything unidentified
        return "unknown", "its owner is gone but the child it recorded is %s" % (
            "pending" if child == "pending" else "unidentified")
    pgid = child.get("pgid")
    if process_matches(child.get("pid"), child.get("process_start")) is not False or not real_pid(pgid) or pgid == 1:
        return "unknown", "its owner is gone but the child it recorded (pid %r) is alive or cannot be confirmed gone" % (
            child.get("pid"),)
    try:
        os.killpg(pgid, 0)                      # signal 0: nothing is sent, the group is only looked up
    except ProcessLookupError:
        return "gone", None
    except OSError:
        pass
    return "unknown", "its owner is gone but the process group %d of its child still has members" % pgid


def find_holder():
    """The session's process: the nearest ancestor that is not a shell → ({pid, pgid, process_start}, None), or
    (None, reason) when the chain cannot be read or ends without one. Nothing is ever guessed."""
    pid = os.getppid()
    for _ in range(64):
        if pid <= 1:
            return None, "no ancestor of this call is anything but a shell"
        answer = ps(pid, "ppid=,comm=")
        parts = answer[1].split(None, 1) if answer is not None and answer[0] == 0 else []
        if len(parts) < 2 or not parts[0].isdigit():
            return None, "the ancestry of this call cannot be read (ps, pid %d)" % pid
        name = os.path.basename(parts[1].strip())
        if name.startswith("-"):
            name = name[1:]
        if name not in SHELLS:
            probe = ps_probe(pid)
            if probe is None or probe[0] != "alive" or probe[1].startswith("Z"):
                return None, "the start identity of the calling process (pid %d) cannot be read" % pid
            try:
                pgid = os.getpgid(pid)
            except OSError:
                return None, "the process group of the calling process (pid %d) cannot be read" % pid
            return {"pid": pid, "pgid": pgid, "process_start": probe[2]}, None
        pid = int(parts[0])
    return None, "the ancestry of this call is too deep to follow"


# ───────────────────────────────────────── files ─────────────────────────────────────────

def read_json(path):
    """(object, None) or (None, reason); never raises, never blocks: only a regular file of sane size is read."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError) as e:
        return None, "unreadable: %s" % type(e).__name__
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None, "unreadable: not a regular file"
        with os.fdopen(os.dup(fd), "rb") as f:
            data = f.read((1 << 20) + 1)
        if len(data) > 1 << 20:
            return None, "unreadable: too large"
        return json.loads(data.decode("utf-8")), None
    except (OSError, ValueError, RecursionError) as e:
        return None, "unreadable: %s" % type(e).__name__
    finally:
        os.close(fd)


def write_json(path, obj):
    """Atomic: a reader sees the old file or the new one, never a part of either."""
    tmp = os.path.join(os.path.dirname(path), ".%s.tmp.%d.%s" % (os.path.basename(path), os.getpid(),
                                                                  secrets.token_hex(4)))
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)


def present(path):
    """True · False (positively no such entry) · None (it cannot be examined: never read as absent)."""
    try:
        os.lstat(path)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return None


_NATIVE = []


def _native_rename():
    """The platform's rename-unless-the-target-exists as f(src, dst) → errno (0 = renamed), or None."""
    if not _NATIVE:
        call = None
        try:
            import ctypes
            libc = ctypes.CDLL(None, use_errno=True)
            if sys.platform == "darwin":
                fn = libc.renamex_np            # int renamex_np(const char *, const char *, unsigned)
                fn.argtypes, fn.restype = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint], ctypes.c_int

                def call(src, dst):
                    ctypes.set_errno(0)
                    return 0 if fn(src, dst, 0x4) == 0 else (ctypes.get_errno() or errno.EIO)      # RENAME_EXCL
            elif sys.platform.startswith("linux"):
                fn = libc.renameat2             # int renameat2(int, const char *, int, const char *, unsigned)
                fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
                fn.restype = ctypes.c_int

                def call(src, dst):
                    ctypes.set_errno(0)
                    return 0 if fn(-100, src, -100, dst, 0x1) == 0 else (ctypes.get_errno() or errno.EIO)  # NOREPLACE
        except (ImportError, AttributeError, OSError):
            call = None
        _NATIVE.append(call)
    return _NATIVE[0]


def rename_exclusive(src, dst):
    """Rename the directory `src` onto `dst`, failing with FileExistsError when `dst` exists AT ALL. A plain
    rename() silently replaces an existing EMPTY directory — an ownerless lock would be taken by accident — so
    the exclusive form is used where the platform has one; elsewhere existence is checked first."""
    native = _native_rename()
    if native is not None:
        err = native(os.fsencode(src), os.fsencode(dst))
        if err == 0:
            return
        if err in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(err, os.strerror(err), dst)
        if err not in (errno.ENOTSUP, errno.EINVAL, errno.ENOSYS):
            raise OSError(err, os.strerror(err), dst)
    if present(dst) is not False:
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), dst)
    try:
        os.rename(src, dst)
    except OSError as e:
        if e.errno in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(e.errno, os.strerror(e.errno), dst) from None
        raise


def remove_dir(path):
    with contextlib.suppress(OSError):
        for name in os.listdir(path):
            os.unlink(os.path.join(path, name))
        os.rmdir(path)


# ───────────────────────────────────────── the lock ─────────────────────────────────────────

def lock_path(role):
    return os.path.join(CFG["run"], "locks", role)


def read_owner(lock, wait):
    """→ (owner object, None) · (None, "absent") when there is positively no lock · (None, reason) when a lock is
    there whose owner cannot be read. `wait` gives an acquirer that makes its lock in two steps (the documented
    mkdir fence) a moment to write its record; a lock created by this script never needs it."""
    tries, pause = OWNER_WAIT if wait else (1, 0)
    for attempt in range(tries):
        owner, err = read_json(os.path.join(lock, "owner.json"))
        if err is None:
            return (owner, None) if isinstance(owner, dict) else (None, "its owner record is not an object")
        if err != "missing":
            return None, "its owner record cannot be read (%s)" % err
        there = present(lock)
        if there is False:
            return None, "absent"
        if there is None:
            return None, "the lock directory cannot be examined"
        if attempt + 1 < tries:
            time.sleep(pause)
    return None, "it has no owner record"


def same_owner(a, b):
    return isinstance(a, dict) and isinstance(b, dict) and all(a.get(k) == b.get(k) for k in OWNER_IDENTITY)


def lock_create(lock, owner):
    """Take the lock directory atomically WITH its owner record: owner.json is written into a private directory
    beside the lock, and that directory is renamed onto the lock path exclusively. → True when this call created
    the lock, False when the path already exists."""
    tmp = os.path.join(os.path.dirname(lock), ".%s.new.%d.%s" % (os.path.basename(lock), os.getpid(),
                                                                 secrets.token_hex(4)))
    os.mkdir(tmp)
    try:
        write_json(os.path.join(tmp, "owner.json"), owner)
        rename_exclusive(tmp, lock)
        return True
    except FileExistsError:
        return False
    finally:
        if present(tmp) is not False:           # not renamed: nothing of it may stay behind
            remove_dir(tmp)


@contextlib.contextmanager
def takeover_guard(lock):
    fd = os.open(os.path.join(os.path.dirname(lock), ".takeover.guard"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def lock_bury(lock, judged, rejudge):
    """Verify-after-rename removal of the lock whose owner record `judged` the caller holds to be removable
    (positively gone, or the caller's own). Under the takeover guard: the record is read again, a gone owner is
    judged once more (`rejudge`), the lock is renamed to a grave beside it — atomic — and the grave's owner.json
    re-read: only when it is exactly the owner that was judged (same id, pid and start) is it removed. Anything
    else is put back, exclusively.
      → "removed"   it was that lock and it is gone: the path is free
        "absent"    there was no lock at that path any more
        "changed"   the lock there is not (or no longer provably) the judged owner's: untouched
        "restored"  it became another owner's between that look and the rename: put back untouched
        "conflict"  as "restored", but the path was re-taken meanwhile: the buried lock is left in its grave
                    for a human — never deleted, never overwritten."""
    with takeover_guard(lock):
        there = present(lock)
        if there is False:
            return "absent"
        if there is None or not same_owner(read_json(os.path.join(lock, "owner.json"))[0], judged):
            return "changed"
        if rejudge and owner_state(judged)[0] != "gone":
            return "changed"
        grave = os.path.join(os.path.dirname(lock), ".%s.grave.%d.%s" % (os.path.basename(lock), os.getpid(),
                                                                         secrets.token_hex(4)))
        try:
            os.rename(lock, grave)
        except FileNotFoundError:
            return "absent"
        if same_owner(read_json(os.path.join(grave, "owner.json"))[0], judged):
            remove_dir(grave)
            return "removed"
        try:
            rename_exclusive(grave, lock)
        except FileExistsError:
            return "conflict"
        return "restored"


def prove_owner(lock, ident):
    """Is the CALLER the recorded owner — the identity, the holder pid and its start identity all those on record?
    → (owner, holder, None) when it is; (owner or None, None, reason) when that is not proven."""
    owner, err = read_owner(lock, wait=False)
    if owner is None:
        return None, None, "there is no lock" if err == "absent" else "the lock is there but %s" % err
    if owner.get("session_or_run_id") != ident:
        return owner, None, "the lock is recorded for %s" % show(owner.get("session_or_run_id"))
    holder, why = find_holder()
    if holder is None:
        return owner, None, why
    if owner.get("pid") != holder["pid"]:
        return owner, None, "the lock belongs to pid %s; this call comes from pid %d" % (
            show(str(owner.get("pid"))), holder["pid"])
    if process_matches(owner.get("pid"), owner.get("process_start")) is not True:
        return owner, None, "the recorded start identity is not that of the calling process (pid %d)" % holder["pid"]
    return owner, holder, None


# ───────────────────────────────────────── verbs ─────────────────────────────────────────

def do_acquire(role, ident):
    holder, why = find_holder()
    if holder is None:
        say("acquire %s refused: %s; nothing written" % (role, why))
        emit("acquire", role, "refused")
        return EX_REFUSED
    kind = "cockpit"
    if ident.startswith("CTL-"):
        named = CTL_RE.match(ident)
        if not named or int(named.group(1)) != holder["pid"]:
            say("acquire %s refused: a controller identity is CTL-…-<pid> of the calling process (pid %d), "
                "which %s is not; nothing written" % (role, holder["pid"], ident))
            emit("acquire", role, "refused")
            return EX_REFUSED
        kind = "controller"
    lock = lock_path(role)
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    mine = {"session_or_run_id": ident, "holder_kind": kind, "pid": holder["pid"], "pgid": holder["pgid"],
            "process_start": holder["process_start"],
            "acquired_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "child": None}
    extra = {}
    for _ in range(3):
        if present(lock) is False and lock_create(lock, mine):    # a refusal writes nothing, not even beside it
            emit("acquire", role, "acquired", ident, holder["pid"], **extra)
            return EX_OK
        extra = {}                              # whoever stands there now, it was not put there by this call
        owner, err = read_owner(lock, wait=True)
        if owner is None and err == "absent":
            continue                            # released between the failed create and the look: try again
        if owner is None:
            say("acquire %s: %s exists but %s; an unknown owner is never taken over, at any age" % (role, lock, err))
            emit("acquire", role, "unknown")
            return EX_UNKNOWN
        oid, opid = owner.get("session_or_run_id"), owner.get("pid")
        state, detail = owner_state(owner)
        if state == "live":
            if oid == ident and opid == holder["pid"]:
                say("acquire %s: this session already holds the lock; nothing rewritten" % role)
                emit("acquire", role, "acquired", ident, holder["pid"], already_held="1")
                return EX_OK
            cockpit = owner.get("holder_kind") == "cockpit"
            say("acquire %s refused: held by a live %s (%s, pid %s)" % (
                role, "cockpit" if cockpit else "owner", show(oid), opid))
            emit("acquire", role, "cockpit" if cockpit else "live", oid, opid)
            return EX_COCKPIT if cockpit else EX_LIVE
        if state == "unknown":
            say("acquire %s: %s is held and %s; an unknown owner is never taken over, at any age" % (
                role, lock, detail))
            emit("acquire", role, "unknown", oid, opid)
            return EX_UNKNOWN
        outcome = lock_bury(lock, owner, rejudge=True)
        if outcome == "removed":
            say("acquire %s: the lock of %s (pid %s, positively gone) is taken over; its databases are not touched"
                % (role, show(oid), opid))
            extra = {"took_over": oid if isinstance(oid, str) else "?"}
        elif outcome == "conflict":
            say("acquire %s: a takeover found another owner's lock and could not put it back; it is left buried "
                "beside %s for a human" % (role, lock))
            emit("acquire", role, "unknown")
            return EX_UNKNOWN
        # "absent" / "changed" / "restored": someone else moved first — create again: one contender gets it
    say("acquire %s refused: lost the race for the lock" % role)
    emit("acquire", role, "race")
    return EX_LIVE


def db_close(ident):
    """The KU-02 step. → None when the session's databases are PROVEN removed (the step's exit 0), else why not."""
    scratch = os.environ.get("KY_SCRATCH", "")
    if not os.path.isabs(scratch):
        return "KY_SCRATCH is not set to an absolute path, so the step was not run"
    script = os.path.join(CFG["fleet"], "local_db.sh")
    if not os.path.isfile(script):
        return "%s is missing, so the step was not run" % script
    try:
        proc = subprocess.Popen(["/bin/bash", script, "close", "--session", ident], stdin=subprocess.DEVNULL,
                                stdout=sys.stderr, stderr=sys.stderr, start_new_session=True)
    except OSError as e:
        return "the step could not be started (%s)" % type(e).__name__
    try:
        rc = proc.wait(timeout=CFG["db_timeout"])
    except subprocess.TimeoutExpired:
        for sig, grace in ((signal.SIGTERM, 5), (signal.SIGKILL, 5)):
            with contextlib.suppress(OSError):
                os.killpg(proc.pid, sig)        # the group this call started itself (its own unreaped child)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=grace)
                break
        return "the step did not finish within %g s and was stopped" % CFG["db_timeout"]
    return None if rc == 0 else "the step ended with exit %d" % rc


def do_release(role, ident):
    lock = lock_path(role)
    owner, holder, why = prove_owner(lock, ident)
    if holder is None:
        say("release %s refused: %s is not proven to be its owner (%s); nothing changed" % (role, ident, why))
        emit("release", role, "not_owner", owner.get("session_or_run_id") if owner else None,
             owner.get("pid") if owner else None)
        return EX_NOT_OWNER
    why = db_close(ident)
    if why is not None:
        say("release %s: the test databases of session %s are NOT proven removed (%s); the lock %s is KEPT"
            % (role, ident, why, lock))
        emit("release", role, "kept", ident, holder["pid"])
        return EX_KEPT
    outcome = lock_bury(lock, owner, rejudge=False)
    if outcome != "removed":
        say("release %s: the databases of session %s are removed but the lock is no longer this session's (%s); "
            "nothing removed" % (role, ident, outcome))
        emit("release", role, "not_owner")
        return EX_NOT_OWNER
    emit("release", role, "released", ident, holder["pid"])
    return EX_OK


def parse_child(text):
    """→ (True, value) for pending | none | a child identity object, else (False, reason)."""
    if text == "pending":
        return True, "pending"
    if text == "none":
        return True, None
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return False, "not pending, none or JSON"
    if not isinstance(value, dict) or set(value) != CHILD_KEYS:
        return False, "the object must have exactly run_id, pid, pgid, process_start"
    run_id, start = value["run_id"], value["process_start"]
    if not isinstance(run_id, str) or not 0 < len(run_id) <= 200 or not run_id.isprintable() or " " in run_id:
        return False, "run_id must be a printable token"
    if not real_pid(value["pid"]) or not real_pid(value["pgid"]):
        return False, "pid and pgid must be positive integers"
    if start is not None and (not isinstance(start, str) or not start.strip()):
        return False, "process_start must be the ps start text, or null when it could not be read"
    return True, value


def do_child(role, ident, text):
    ok, value = parse_child(text)
    if not ok:
        say("child %s: %s; nothing changed" % (role, value))
        say(USAGE)
        emit("child", role, "usage")
        return EX_USAGE
    lock = lock_path(role)
    owner, holder, why = prove_owner(lock, ident)
    if holder is not None:
        with takeover_guard(lock):
            current, _ = read_owner(lock, wait=False)
            if same_owner(current, owner):
                write_json(os.path.join(lock, "owner.json"), dict(current, child=value))
                emit("child", role, "recorded", ident, holder["pid"],
                     child="none" if value is None else value if value == "pending" else value["run_id"])
                return EX_OK
        why = "the lock changed while it was being written"
    say("child %s refused: %s is not proven to be its owner (%s); nothing changed" % (role, ident, why))
    emit("child", role, "not_owner", owner.get("session_or_run_id") if owner else None,
         owner.get("pid") if owner else None)
    return EX_NOT_OWNER


def do_status(role):
    lock = lock_path(role)
    owner, err = read_owner(lock, wait=False)
    if owner is None:
        if err != "absent":
            say("status %s: %s exists but %s" % (role, lock, err))
        emit("status", role, "free" if err == "absent" else "unknown")
        return EX_OK
    state, detail = owner_state(owner)
    if state == "live" and owner.get("holder_kind") == "cockpit":
        state = "cockpit"
    if detail:
        say("status %s: %s" % (role, detail))
    emit("status", role, state, owner.get("session_or_run_id"), owner.get("pid"))
    return EX_OK


# ───────────────────────────────────────── entry ─────────────────────────────────────────

def configure():
    """KY_RUN / KY_FLEET and the tests-only hooks → None, or (state, reason) when the call must not go on."""
    run, fleet = os.environ.get("KY_RUN", ""), os.environ.get("KY_FLEET", "")
    if not os.path.isabs(run) or not os.path.isabs(fleet):
        return "usage", "KY_RUN and KY_FLEET must be absolute paths"
    CFG.update(run=os.path.normpath(run), fleet=os.path.normpath(fleet))
    hook_ps, hook_db = os.environ.get("KY_LOCK_PS", ""), os.environ.get("KY_LOCK_DB_TIMEOUT_S", "")
    if not hook_ps and not hook_db:
        return None
    if CFG["run"] == PROD_RUN or os.path.realpath(run) == os.path.realpath(PROD_RUN):
        return "refused", "KY_LOCK_PS / KY_LOCK_DB_TIMEOUT_S are tests-only hooks: refused for %s" % PROD_RUN
    hooks = []
    if hook_db:
        try:
            limit = float(hook_db)
        except ValueError:
            limit = -1.0
        if not 0 < limit <= DB_TIMEOUT_S:
            return "refused", "the tests-only hook KY_LOCK_DB_TIMEOUT_S must be a number in (0, %d]" % DB_TIMEOUT_S
        CFG["db_timeout"] = limit
        hooks.append("db_timeout")
    if hook_ps:
        if not os.path.isabs(hook_ps) or not os.path.isfile(hook_ps) or not os.access(hook_ps, os.X_OK):
            return "refused", "the tests-only hook KY_LOCK_PS must be the absolute path of an executable file"
        CFG["ps"] = hook_ps
        hooks.append("ps")
    CFG["hooks"] = hooks
    return None


def main(argv):
    verb = argv[0] if argv and argv[0] in ARGC else "-"
    if verb == "-" or len(argv) - 1 != ARGC[verb]:
        say(USAGE)
        emit(verb, None, "usage")
        return EX_USAGE
    stop = configure()
    if stop is not None:
        say(stop[1])
        emit(verb, None, stop[0])
        return EX_USAGE
    role = argv[1]
    if not ROLE_RE.match(role):
        say("%s refused: a role is [a-z][a-z0-9_]{0,31}; nothing read or written" % verb)
        emit(verb, None, "refused")
        return EX_REFUSED
    if verb == "status":
        try:
            return do_status(role)
        except Exception as e:                  # a state that could not be measured is unknown, never free
            say("status %s: %s (%s)" % (role, type(e).__name__, e))
            emit("status", role, "unknown")
            return EX_OK
    ident = argv[2]
    if not IDENT_RE.match(ident) or ".." in ident:
        say("%s %s refused: an identity is [A-Za-z0-9][A-Za-z0-9_.-]{0,63} without `..`; nothing read or written"
            % (verb, role))
        emit(verb, role, "refused")
        return EX_REFUSED
    try:
        if verb == "acquire":
            return do_acquire(role, ident)
        if verb == "release":
            return do_release(role, ident)
        return do_child(role, ident, argv[3])
    except Exception as e:
        say("%s %s failed: %s (%s); this call reports nothing as acquired, released or recorded — see `status`"
            % (verb, role, type(e).__name__, e))
        emit(verb, role, "error")
        return EX_REFUSED


with contextlib.suppress(OSError):
    os.close(3)                                 # the descriptor this program was read from
sys.exit(main(sys.argv[1:]))
KYLOCK_PY
