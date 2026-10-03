"""Detached watchdog for a disposable test cluster (started by _disposable_pg.start_cluster; never collected by pytest).

The fixture's "always stops and deletes the cluster" only holds when pytest exits normally. A SIGKILLed / pkill'ed / OOM-killed pytest
leaves the postmaster running and the temp dir behind (nine such orphans were found on one host). This process outlives its parent
by design: it polls the owning pytest process (pid AND its start time, so a recycled pid is not mistaken for the owner) and, once that
process is gone, stops the cluster it was told about and deletes its root. It acts ONLY on a root that carries the ownership marker
this very pytest process wrote (`OWNER_MARKER`), and only on a postmaster whose data directory is `<root>/data`.

A "dead owner" is only ever concluded from a CONCLUSIVE `ps` answer (no such process, or a zombie). A timeout, an OS error, an unexpected
exit status or an empty start time is "cannot tell" and reads ALIVE: reaping a live run's cluster is the one unrecoverable mistake here.
`ps` is always run with a fixed locale and timezone (LC_ALL=C, TZ=UTC) so a start time written by one process matches the one read by
another session, CI job or a machine whose timezone changed.

argv: parent_pid parent_start root pg_ctl_path
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

OWNER_MARKER = ".suvarna_pg_owner.json"
MARKER_VERSION = 2          # v2: start time read under LC_ALL=C/TZ=UTC; a marker without it (an earlier local-time stamp) is never reaped
POLL_SECONDS = 2.0
_PS_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
_PS = next((c for c in ("/bin/ps", "/usr/bin/ps") if os.path.exists(c)), "ps")      # not looked up on a caller-controlled PATH
GONE = ""                    # proc_start: `ps` answered that there is no such process
# proc_start returns None when `ps` could not answer conclusively (timeout, OS error, odd status/output): the caller must treat it as alive.


def _ps(*args: str) -> tuple[int, str] | None:
    try:
        p = subprocess.run([_PS, "-ww", *args], capture_output=True, text=True, timeout=10, env=_PS_ENV)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return p.returncode, p.stdout


def _pid_absent(pid: int) -> bool:
    """True only when the kernel itself says there is no such process (`kill(pid, 0)` -> ESRCH); EPERM means it exists."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False                                   # kill(-n, 0) / kill(0, 0) address process GROUPS: never "absent"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except (OSError, OverflowError, ValueError):       # EPERM (exists), or a pid that does not even fit a C long
        return False
    return False


def proc_start(pid: int) -> str | None:
    """The process start time as `ps` prints it under a fixed locale/timezone: with the pid it identifies one process, not a recycled pid.
    '' (GONE) when there is no such process or it is a zombie; None when `ps` could not answer conclusively."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    r = _ps("-p", str(pid), "-o", "lstart=,stat=")
    if r is None:
        return None
    rc, out = r
    out = out.strip()
    if rc == 1 and not out:
        return GONE if _pid_absent(pid) else None      # ps exits 1 with nothing printed when the pid does not exist: the kernel must agree
    if rc != 0 or not out:
        return None
    start, _, stat = out.rpartition(" ")
    if not start.strip():
        return None
    return GONE if stat.startswith("Z") else start.strip()


def owner_alive(pid: int, start: str) -> bool:
    """False ONLY on a conclusive answer: the process is gone, a zombie, or a different process generation (start time differs)."""
    if not isinstance(start, str) or not start:
        return True                                    # a marker without a start time cannot prove the owner dead
    cur = proc_start(pid)
    if cur is None:
        return True
    return cur != GONE and cur == start


def _postmaster_state(data: Path) -> str:
    """'none' (no pid file / no such process), 'ours' (the pid file names a live postgres whose command line carries this data dir),
    'foreign' (the pid is alive but is not that postmaster: a recycled pid), 'unknown' (could not tell)."""
    try:
        first = (data / "postmaster.pid").read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        pid = int(first)
        if pid > 2**31 - 1:
            return "foreign"                           # not a pid this kernel can have issued
    except (OSError, IndexError, ValueError):
        return "none"
    if pid <= 1:
        return "foreign"
    r = _ps("-p", str(pid), "-o", "command=")
    if r is None:
        return "unknown"
    rc, out = r
    out = out.strip()
    if rc == 1 and not out:
        return "none" if _pid_absent(pid) else "unknown"
    if rc != 0:
        return "unknown"
    tok = out.split()
    # the command line of a postmaster on THIS data dir: `<...>/postgres -D <data> ...` (token-wise, never a substring match)
    ours = (bool(tok) and os.path.basename(tok[0]) == "postgres" and "-D" in tok[:-1] and tok[tok.index("-D") + 1] == str(data))
    return "ours" if ours else "foreign"


def read_marker(root: Path) -> dict | None:
    try:
        m = json.loads((root / OWNER_MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = (isinstance(m, dict) and isinstance(m.get("parent_pid"), int) and not isinstance(m.get("parent_pid"), bool)
          and isinstance(m.get("parent_start"), str) and bool(m.get("parent_start")) and m.get("root") == str(root)
          and m.get("v") == MARKER_VERSION)
    return m if ok else None


def reap(root: Path, pg_ctl: str | None = None) -> bool:
    """Stop the cluster under `root` (when one runs) and delete the root, but ONLY for a root with a valid ownership marker."""
    try:
        if root.is_symlink() or not root.is_dir() or root.stat().st_uid != os.getuid():
            return False
    except OSError:
        return False
    if read_marker(root) is None:
        return False
    data = root / "data"
    if data.exists() or data.is_symlink():
        # `data` must be a real directory inside this root: a symlink would aim `pg_ctl stop` at somebody else's cluster
        if data.is_symlink() or not data.is_dir() or os.path.realpath(data) != os.path.join(os.path.realpath(root), "data"):
            return False
    state = _postmaster_state(data)
    if state == "unknown":
        return False                                   # cannot tell whether a postmaster runs here: touch nothing
    if state == "ours" and pg_ctl:
        # only a pid file that names a live postgres on THIS data dir is ever signalled (pg_ctl signals whatever pid the file holds)
        try:
            subprocess.run([pg_ctl, "-D", str(data), "-m", "immediate", "-w", "-t", "30", "stop"], capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
        if _postmaster_state(data) in ("ours", "unknown"):
            return False                               # the postmaster is still up: never delete a running cluster's directory
    elif state == "ours":
        return False                                   # a running postmaster and no pg_ctl to stop it
    shutil.rmtree(root, ignore_errors=True)
    return True


def main(argv: list[str]) -> int:
    pid, start, root, pg_ctl = int(argv[1]), argv[2], Path(argv[3]), argv[4]
    if not start:
        return 2                                       # no start time = no way to prove the owner dead: do nothing
    while True:
        if not root.exists():
            return 0                                   # the fixture stopped the cluster normally
        if not owner_alive(pid, start):
            reap(root, pg_ctl)
            return 0
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
