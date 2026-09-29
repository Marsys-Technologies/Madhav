"""Suvarṇa hq commit lock (arch §12.12) — serializes commits to the shared `suvarna/hq` worktree.

    python -m suvarna_tracker.hq_commit --paths <p...> --message <m> [--home DIR] [--hq DIR] [--wait SECONDS]

Every Conductor pass ends by committing its own queue file on `suvarna/hq` (§5.1, §12.1). Two
sessions' Conductors (Exec Suvarṇa and Nikaṣa Engine) share that one worktree, so two passes
committing at the same moment would race the git index. This CLI takes an exclusive `fcntl.flock`
on `$SUVARNA_HOME/run/locks/hq.lock`, runs `git -C <hq> commit -- <paths>` — explicit paths only,
never `-A`/`--all`/a whole-tree commit — and returns git's exit code unchanged, then releases the
lock.

Design rules (mirrors `census_lock.py`, the project's other flock-based serializer):
- **Only-mode.** No path list, or a path list containing `-A`/`--all`/`-a`/`.`, is refused before
  the lock is even taken and before git is ever invoked (exit `EX_USAGE`, 2).
- **Blocking with a bound.** Unlike the census lock (which fails fast — a second concurrent census
  is a bug), a second concurrent hq commit is expected and must simply wait its turn: `acquire()`
  polls for the lock up to `--wait` seconds (default 300) and reports `EX_LOCK_TIMEOUT` if it never
  clears, rather than hanging a stateless Conductor pass forever on a stuck holder.
- **No `git add`, except `--add-new` (CODE-16).** `git commit -- <pathspec>` stages and commits
  modifications to already-tracked paths by itself, so the wrapper never runs a separate `add` step
  for those (arch §12.12's own wording: `git commit -- <paths>` only). `--add-new` is the one
  exception: inside the lock, for each listed path git does not already track, it runs `git add --
  <path>` (that one path only) before the commit — a Conductor pass's queue file is untracked the
  very first time it is ever committed. The refusal rules are unchanged and still apply: no
  `-A`/`--all`/`-a`/`.`, and no glob-like path (`*`, `?`, `[`) — `--add-new` only ever adds the exact
  paths named, one at a time, never a pattern that could pick up more than intended.
"""
from __future__ import annotations

import argparse
import fcntl
import os
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EX_USAGE = 2
EX_LOCK_TIMEOUT = 75  # same convention as census_lock.EX_TEMPFAIL, distinct meaning (timed out, not "occupied, fail fast")

REFUSED_PATH_TOKENS = ("-A", "--all", "-a", ".")
GLOB_CHARS = ("*", "?", "[", "]")


def lock_path(home: str) -> str:
    return os.path.join(home, "run", "locks", "hq.lock")


def acquire(path: str, wait: float) -> int | None:
    """Try to take the exclusive lock, polling up to `wait` seconds. Returns an open fd holding
    the lock, or None if it could not be acquired in time."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
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


def _refused(paths: list[str]) -> str | None:
    if not paths:
        return "hq_commit: refuses to commit with no paths (never -A / a whole-tree commit)"
    bad = [p for p in paths if p in REFUSED_PATH_TOKENS]
    if bad:
        return f"hq_commit: refuses {', '.join(bad)} — pass explicit paths only, never -A/--all/-a/."
    globby = [p for p in paths if any(c in p for c in GLOB_CHARS)]
    if globby:
        return f"hq_commit: refuses glob-like path(s): {', '.join(globby)} — pass explicit paths only, never a pattern"
    return None


def _is_tracked(hq: str, path: str) -> bool:
    """True iff git already tracks `path` in `hq` — `git ls-files --error-unmatch` exits 0 only for
    a path that is (or once was, if since deleted) in the index; used by `--add-new` to decide
    which listed paths need a `git add` before the commit."""
    return subprocess.run(["git", "-C", hq, "ls-files", "--error-unmatch", "--", path],
                          capture_output=True).returncode == 0


def commit(hq: str, paths: list[str], message: str, home: str, wait: float = 300.0,
           add_new: bool = False) -> int:
    """Take the hq lock, run `git -C hq commit -m <message> -- <paths>`, release, and return git's
    exit code unchanged. Refuses (before taking the lock, before invoking git) an empty path list,
    any -A/--all/-a/. path, or any glob-like path; times out with EX_LOCK_TIMEOUT if the lock never
    clears.

    CODE-16: `add_new=True` runs `git add -- <path>` (that path only) inside the lock, before the
    commit, for each listed path git does not already track — the one exception to "no `git add`",
    for a queue file's first-ever commit. A failed `add` aborts before the commit is attempted, with
    the lock released in `finally` either way."""
    reason = _refused(paths)
    if reason:
        print(reason, file=sys.stderr)
        return EX_USAGE
    fd = acquire(lock_path(home), wait)
    if fd is None:
        print(f"hq_commit: could not acquire the hq lock within {wait}s", file=sys.stderr)
        return EX_LOCK_TIMEOUT
    try:
        if add_new:
            for p in paths:
                if _is_tracked(hq, p):
                    continue
                add_rc = subprocess.run(["git", "-C", hq, "add", "--", p]).returncode
                if add_rc != 0:
                    return add_rc
        argv = ["git", "-C", hq, "commit", "-m", message, "--", *paths]
        return subprocess.run(argv).returncode
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Commit explicit paths to the shared suvarna/hq worktree, under the hq lock")
    ap.add_argument("--paths", nargs="+", default=[], help="explicit paths to commit (never -A/--all/-a/.)")
    ap.add_argument("--message", "-m", required=True, help="the commit message")
    ap.add_argument("--home", default=os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna"))
    ap.add_argument("--hq", default=None, help="the hq worktree path (default: <home>/hq)")
    ap.add_argument("--wait", type=float, default=300.0, help="seconds to wait for the lock (default: 300)")
    ap.add_argument("--add-new", action="store_true",
                    help="inside the lock, `git add -- <path>` for any listed path git does not "
                         "already track (CODE-16) — still refuses -A/--all/-a/./globs")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_arg_parser().parse_args(argv)
    hq = a.hq or os.path.join(a.home, "hq")
    return commit(hq, a.paths, a.message, a.home, wait=a.wait, add_new=a.add_new)


if __name__ == "__main__":
    raise SystemExit(main())
