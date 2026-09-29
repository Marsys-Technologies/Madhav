"""Suvarṇa Conductor lock (F6 — independent review): exclusive runtime ownership, one fenced owner
per session.

The pre-fix runtime had no such fence at all: `monitor.py`'s own `_latest_conductor_heartbeat_ts`
took the newest `kind: heartbeat, actor: "conductor"` line from *either* interim-runtime session,
so one healthy session could mask the other going silent; and nothing anywhere refused a second
launch for the same session — two Conductor processes for "engine" could simply both run.

    python -m suvarna_tracker.conductor_lock acquire --session engine [--home DIR] [--pid N]
    python -m suvarna_tracker.conductor_lock release --session engine [--home DIR]
    python -m suvarna_tracker.conductor_lock status  --session engine [--home DIR]

Design:
- One lock file per session: ``$SUVARNA_HOME/run/locks/conductor-<session>.lock``, holding exactly
  ``{"pid": <int>, "started_at": "<iso>"}`` — nothing else, never a credential or a command.
- **Refuses, never doubles up.** ``acquire()`` raises ``LockHeld`` if the lock file names a PID
  that is still alive (``os.kill(pid, 0)`` succeeds, or would raise ``PermissionError`` — a process
  we cannot signal but that the OS still lets us *see* is alive is alive, never treated as dead just
  because we lack permission to signal it). The CLI's exit code for a refused acquire is **75**
  (distinct from this package's other exit codes: 0 ok, 2 refused-precondition elsewhere).
- **Stale locks are reclaimed, not treated as errors.** A lock file naming a dead PID (``os.kill``
  raises ``ProcessLookupError``) is silently superseded — `acquire()` overwrites it and reports the
  reclaim in its return value, never raising.
- **Heartbeats are per-session.** A Conductor that holds this lock emits its heartbeats as
  ``actor: "conductor:<session>"`` — never the old, session-blind ``actor: "conductor"`` — so
  `monitor.check_conductor_heartbeat` can tell "engine" going stale from "exec" still healthy,
  instead of one masking the other.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

DEFAULT_HOME = "/Users/Dev/suvarna"

# The CLI's exit code for a refused acquire (lock held by a live process) — distinct from 0 (ok)
# and 2 (refused precondition, used elsewhere in this package for e.g. hold_guard/lane_launch).
EXIT_LOCK_HELD = 75


class LockHeld(RuntimeError):
    """Raised by `acquire()` when the session's lock is already held by a live process."""

    def __init__(self, session: str, pid: int, started_at: str | None):
        self.session = session
        self.pid = pid
        self.started_at = started_at
        super().__init__(f"conductor lock for session {session!r} is held by live pid {pid} "
                          f"(started {started_at or '?'})")


def home_dir() -> str:
    return os.environ.get("SUVARNA_HOME", DEFAULT_HOME)


def locks_dir(home: str | None = None) -> str:
    return os.path.join(home or home_dir(), "run", "locks")


def lock_path(session: str, home: str | None = None) -> str:
    return os.path.join(locks_dir(home), f"conductor-{session}.lock")


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def is_pid_alive(pid: int) -> bool:
    """True if `pid` is a live process we can at least see (signal 0 — no actual signal sent). A
    `PermissionError` (the process exists, owned by someone else) still counts as alive; only
    `ProcessLookupError` (no such process) counts as dead. `pid <= 0` is never alive."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_lock(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_lock(path: str, pid: int, started_at: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"pid": pid, "started_at": started_at}, f)
    os.replace(tmp, path)


def is_held_by_live_process(session: str, home: str | None = None) -> bool:
    """True iff this session's lock file names a PID that is still alive. Never raises — a
    missing or malformed lock file reads as "not held" (nothing to reclaim from, nothing live)."""
    data = _read_lock(lock_path(session, home))
    if not data:
        return False
    pid = data.get("pid")
    return isinstance(pid, int) and is_pid_alive(pid)


def acquire(session: str, home: str | None = None, pid: int | None = None,
           now_iso: str | None = None) -> dict:
    """Acquire the exclusive lock for `session`. Raises `LockHeld` if a live process already holds
    it. A stale lock (dead pid) is silently reclaimed — the return value's `reclaimed_from` names
    the dead pid it superseded, or is `None` for a fresh acquire. Never raises for a stale or
    missing lock; only for one genuinely held by a live process."""
    path = lock_path(session, home)
    existing = _read_lock(path)
    reclaimed_from = None
    if existing:
        old_pid = existing.get("pid")
        if isinstance(old_pid, int) and is_pid_alive(old_pid):
            raise LockHeld(session, old_pid, existing.get("started_at"))
        reclaimed_from = old_pid
    my_pid = pid if pid is not None else os.getpid()
    started = now_iso or _now_iso()
    _write_lock(path, my_pid, started)
    return {"session": session, "pid": my_pid, "started_at": started, "path": path,
           "reclaimed_from": reclaimed_from}


def update_pid(session: str, pid: int, home: str | None = None) -> None:
    """The current holder records a different pid for its own already-acquired lock (e.g. a
    launcher that reserved the lock under its own transient pid, then hands ownership to the real,
    detached process it just spawned). Never checks liveness or raises `LockHeld` — that check
    already happened at `acquire()`; this only ever updates the pid of a lock this process is
    assumed to already hold. Preserves the original `started_at`."""
    path = lock_path(session, home)
    existing = _read_lock(path) or {}
    _write_lock(path, pid, existing.get("started_at") or _now_iso())


def release(session: str, home: str | None = None, pid: int | None = None) -> bool:
    """Remove this session's lock file — but only if it still names the caller's own pid (never
    releases a lock some other, later acquirer now owns: a crashed-then-restarted holder must not
    accidentally free the new owner's lock). Returns True if removed, False otherwise (including
    "no such lock" — never raises)."""
    path = lock_path(session, home)
    data = _read_lock(path)
    if not data:
        return False
    my_pid = pid if pid is not None else os.getpid()
    if data.get("pid") != my_pid:
        return False
    try:
        os.remove(path)
    except OSError:
        return False
    return True


def status(session: str, home: str | None = None) -> dict:
    """A read-only snapshot: `{'held': bool, 'pid': int|None, 'started_at': str|None, 'live':
    bool}` — `held` is True whenever a lock file exists at all (even a stale one); `live` is True
    only when its pid is actually alive."""
    data = _read_lock(lock_path(session, home)) or {}
    pid = data.get("pid")
    live = isinstance(pid, int) and is_pid_alive(pid)
    return {"held": bool(data), "pid": pid, "started_at": data.get("started_at"), "live": live}


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suvarṇa Conductor lock — exclusive runtime ownership per session")
    ap.add_argument("action", choices=["acquire", "release", "status"])
    ap.add_argument("--session", required=True, help="the Conductor session name (e.g. engine, exec)")
    ap.add_argument("--home", default=None, help="override $SUVARNA_HOME")
    ap.add_argument("--pid", type=int, default=None, help="override the pid recorded/checked (default: this process)")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_arg_parser().parse_args(argv)
    home = a.home or home_dir()
    if a.action == "acquire":
        try:
            result = acquire(a.session, home=home, pid=a.pid)
        except LockHeld as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return EXIT_LOCK_HELD
        note = f" (reclaimed a stale lock from dead pid {result['reclaimed_from']})" if result["reclaimed_from"] else ""
        print(json.dumps(result, ensure_ascii=False) + note)
        return 0
    if a.action == "release":
        released = release(a.session, home=home, pid=a.pid)
        print(json.dumps({"session": a.session, "released": released}, ensure_ascii=False))
        return 0
    print(json.dumps(status(a.session, home=home), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
