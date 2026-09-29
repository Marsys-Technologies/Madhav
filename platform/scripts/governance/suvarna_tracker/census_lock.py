"""Suvarṇa census lock — one census at a time (review #24: "one census at a time" had no mechanism).

    python -m suvarna_tracker.census_lock [--wait SECONDS] [--emit] [--actor NAME]
        [--census-only] -- <command ...>

Takes an exclusive `fcntl.flock` on `$SUVARNA_HOME/run/locks/census.lock`, writes holder info (pid,
command, start time) to `census.holder` next to it, runs the given command, releases the lock and
holder file, and returns the command's exit code.

`--wait 0` (the default) fails immediately with exit 75 (EX_TEMPFAIL) if another census already
holds the lock, printing who holds it. `--wait N` waits up to N seconds for the lock to free up
before giving up the same way.

B6 (review pass 3): the wildcard permission template allow that used to wrap this tool
(`Bash(python3 -m suvarna_tracker.census_lock --emit -- <any command>)`) let a swarm agent run *any*
command under the lock — a wrapper around every Bash deny in the same template. `--census-only`
closes that: with it set, `run_locked`/`main` refuse to even attempt the lock unless the wrapped
command is exactly the one form the inspector actually needs (`is_census_only_command`). The
template's own allow is narrowed accordingly to `python3 -m suvarna_tracker.census_run`, a small
wrapper (`census_run.py`) that builds this exact command itself from validated `--layer`/`--out`
arguments and always passes `--census-only`.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suvarna_tracker.events import append, now_iso  # noqa: E402

EX_TEMPFAIL = 75
EX_USAGE = 2
EX_LAUNCH_FAILED = 127
EX_NOT_CENSUS_ONLY = 77

# CODE-35 (review pass 3 disposition, arch §12.13/§12.15): the census inspector's checkout is
# either the legacy read-only `/Users/Dev/madhav-nikasha` (until E4.1 lands the inspector on main)
# or the `suvarna/trunk` worktree after — never a third, caller-supplied path. Named here, not
# derived from an env var at match time, so this independent re-validation layer cannot silently
# widen to whatever `census_run.py`'s own environment happens to say.
CENSUS_ALLOWED_ROOTS = ("/Users/Dev/madhav-nikasha", "/Users/Dev/suvarna/trunk")

# The one command shape `--census-only` accepts: `bash -c '<source pgenv> && cd <allowed root> &&
# python3 platform/scripts/governance/asset_census.py [--flag value]*'`. No `&&`/`;`/`|`/backtick/`$`
# anywhere in the flag values (shlex.quote on a plain path/token never introduces one, so a
# legitimate `census_run`-built command always matches; anything else — a second command chained on,
# a different script, a raw shell metacharacter, a root outside the two — is refused).
CENSUS_ONLY_PATTERN = re.compile(
    r"^source [^\s&|;`$]+pgenv\.sh && cd (" + "|".join(re.escape(r) for r in CENSUS_ALLOWED_ROOTS) + r") && "
    r"python3 platform/scripts/governance/asset_census\.py"
    r"( --[A-Za-z0-9_-]+ [\w.@%+:,/-]+)*$"
)


def is_census_only_command(command: list[str]) -> bool:
    """True iff `command` is exactly `["bash", "-c", <the one inspector invocation>]`."""
    return (len(command) == 3 and command[0] == "bash" and command[1] == "-c"
            and bool(CENSUS_ONLY_PATTERN.match(command[2])))


def lock_paths(home: str) -> tuple[str, str]:
    run_dir = os.path.join(home, "run", "locks")
    return os.path.join(run_dir, "census.lock"), os.path.join(run_dir, "census.holder")


def _read_holder(holder_path: str) -> dict | None:
    try:
        with open(holder_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def acquire(lock_path: str, wait: float) -> int | None:
    """Try to take the exclusive lock, polling up to `wait` seconds (0 = try once, no polling).
    Returns an open fd holding the lock, or None if it could not be acquired in time."""
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.time() + max(0.0, wait)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            if time.time() >= deadline:
                os.close(fd)
                return None
            time.sleep(min(0.2, max(0.01, deadline - time.time())))


def _emit(home: str, actor: str, detail: str) -> None:
    events_path = os.environ.get("SUVARNA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl"))
    try:
        append(events_path, {"kind": "note", "actor": actor, "detail": detail})
    except Exception:  # noqa: BLE001 — a note failing to write must never abort the census
        pass


def run_locked(home: str, command: list[str], wait: float = 0.0,
               emit_flag: bool = False, actor: str = "census", census_only: bool = False) -> int:
    if census_only and not is_census_only_command(command):
        print("census: --census-only is set and the wrapped command is not the asset_census.py "
              "inspector invocation; refusing without acquiring the lock", file=sys.stderr)
        return EX_NOT_CENSUS_ONLY
    lock_path, holder_path = lock_paths(home)
    fd = acquire(lock_path, wait)
    if fd is None:
        holder = _read_holder(holder_path)
        who = (f"pid {holder.get('pid')} running {holder.get('command')} since {holder.get('started_at')}"
               if holder else "another holder (holder file unreadable)")
        print(f"census lock held by: {who}", file=sys.stderr)
        return EX_TEMPFAIL

    command_name = os.path.basename(command[0]) if command else "?"
    info = {"pid": os.getpid(), "command": command_name, "argv": list(command), "started_at": now_iso()}
    try:
        os.makedirs(os.path.dirname(holder_path), exist_ok=True)
        tmp = f"{holder_path}.tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(info, f)
        os.replace(tmp, holder_path)  # atomic

        if emit_flag:
            _emit(home, actor, f"census lock acquired: {command_name}")

        try:
            rc = subprocess.run(command).returncode
        except OSError as exc:
            print(f"census: could not launch {command_name}: {exc}", file=sys.stderr)
            rc = EX_LAUNCH_FAILED
        return rc
    finally:
        if emit_flag:
            _emit(home, actor, f"census lock released: {command_name}")
        try:
            os.remove(holder_path)
        except OSError:
            pass
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run a command while holding the Suvarṇa census lock")
    ap.add_argument("--wait", type=float, default=0.0, help="seconds to wait for the lock (default: 0, fail fast)")
    ap.add_argument("--emit", action="store_true", help="emit a note event on acquire and on release")
    ap.add_argument("--actor", default="census", help="actor name used for --emit notes")
    ap.add_argument("--home", default=os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna"))
    ap.add_argument("--census-only", action="store_true",
                    help="B6: refuse any wrapped command other than the exact asset_census.py "
                         "inspector invocation, before even attempting the lock")
    return ap


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else list(argv)
    if "--" in raw:
        idx = raw.index("--")
        own_args, command = raw[:idx], raw[idx + 1:]
    else:
        own_args, command = raw, []
    a = build_arg_parser().parse_args(own_args)
    if not command:
        print("usage: python -m suvarna_tracker.census_lock [--wait SECONDS] [--emit] "
              "[--census-only] -- <command ...>", file=sys.stderr)
        return EX_USAGE
    return run_locked(a.home, command, wait=a.wait, emit_flag=a.emit, actor=a.actor,
                      census_only=a.census_only)


if __name__ == "__main__":
    raise SystemExit(main())
