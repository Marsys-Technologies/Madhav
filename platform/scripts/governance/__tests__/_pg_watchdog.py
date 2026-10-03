"""Detached watchdog for a disposable test cluster (started by _disposable_pg.start_cluster; never collected by pytest).

The fixture's "always stops and deletes the cluster" only holds when pytest exits normally. A SIGKILLed / pkill'ed / OOM-killed pytest
leaves the postmaster running and the temp dir behind (nine such orphans were found on one host). This process outlives its parent
by design: it polls the owning pytest process (pid AND its start time, so a recycled pid is not mistaken for the owner) and, once that
process is gone, stops the cluster it was told about and deletes its root. It acts ONLY on a root that carries the ownership marker
this very pytest process wrote (`OWNER_MARKER`), and only on a postmaster whose data directory is `<root>/data`.

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
POLL_SECONDS = 2.0


def proc_start(pid: int) -> str:
    """The process start time as `ps` prints it ('' when no such process): with the pid it identifies one process, not a recycled pid."""
    try:
        p = subprocess.run(["ps", "-p", str(int(pid)), "-o", "lstart="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError, ValueError):
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def owner_alive(pid: int, start: str) -> bool:
    cur = proc_start(pid)
    return bool(cur) and cur == start


def read_marker(root: Path) -> dict | None:
    try:
        m = json.loads((root / OWNER_MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = (isinstance(m, dict) and isinstance(m.get("parent_pid"), int) and isinstance(m.get("parent_start"), str)
          and m.get("root") == str(root))
    return m if ok else None


def reap(root: Path, pg_ctl: str | None = None) -> bool:
    """Stop the cluster under `root` (when one runs) and delete the root, but ONLY for a root with a valid ownership marker."""
    if read_marker(root) is None:
        return False
    data = root / "data"
    if pg_ctl and (data / "postmaster.pid").exists():
        try:
            subprocess.run([pg_ctl, "-D", str(data), "-m", "immediate", "-w", "-t", "30", "stop"], capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
    shutil.rmtree(root, ignore_errors=True)
    return True


def main(argv: list[str]) -> int:
    pid, start, root, pg_ctl = int(argv[1]), argv[2], Path(argv[3]), argv[4]
    while True:
        if not root.exists():
            return 0                                   # the fixture stopped the cluster normally
        if not owner_alive(pid, start):
            reap(root, pg_ctl)
            return 0
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
