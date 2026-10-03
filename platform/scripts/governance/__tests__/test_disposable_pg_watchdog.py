"""test_disposable_pg_watchdog.py: a SIGKILLed pytest must not leave a disposable cluster behind.

  * the SEEDED KILL: a child process starts a real disposable cluster, then `kill -9`; within a bounded time the detached watchdog has
    stopped the postmaster and deleted the directory (no postgres process holds that data dir);
  * the SWEEP only reaps what it can attribute: a directory with a valid ownership marker whose owner process (pid + start time) is gone;
    never a directory without a marker, with a live owner, whose recorded pid was RECYCLED (different start time = dead owner: reaped),
    a symlink, a marker naming another root, or an entry that is not `suvarna_pg_*`;
  * the watchdog exits quietly (and touches nothing) once the cluster was stopped normally.
"""
from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import textwrap
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import _disposable_pg as dpg  # noqa: E402
import _pg_watchdog as wd  # noqa: E402

BIN = dpg.find_bin_dir()
NEEDS_PG = pytest.mark.skipif(BIN is None, reason="no PostgreSQL server binaries (initdb + pg_ctl) on this machine: the real kill test cannot run")


def _dead_pid() -> tuple[int, str]:
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.2)"])
    start = wd.proc_start(p.pid)
    p.wait()
    return p.pid, start


def _mk(base: pathlib.Path, name: str, *, pid: int | None, start: str | None, root_field: str | None = None) -> pathlib.Path:
    r = base / name
    r.mkdir()
    (r / "data").mkdir()
    if pid is not None:
        (r / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": root_field or str(r), "created": 0}))
    return r


def _postgres_running_on(data_dir: pathlib.Path) -> bool:
    out = subprocess.run(["ps", "-axo", "command="], capture_output=True, text=True).stdout
    return any("postgres" in ln and str(data_dir) in ln for ln in out.splitlines())


# ---------------------------------------------------------------- the sweep: attribution rules ----------------------------------------------

def test_sweep_reaps_a_marked_directory_whose_owner_process_is_gone(tmp_path):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_dead", pid=pid, start=start)
    assert dpg.sweep_stale_clusters(tmp_path) == [str(r)] and not r.exists()


def test_sweep_never_touches_a_directory_without_a_marker(tmp_path):
    r = _mk(tmp_path, "suvarna_pg_nomarker", pid=None, start=None)
    assert dpg.sweep_stale_clusters(tmp_path) == [] and r.exists()


def test_sweep_never_touches_a_directory_whose_owner_is_alive(tmp_path):
    r = _mk(tmp_path, "suvarna_pg_live", pid=os.getpid(), start=wd.proc_start(os.getpid()))
    assert dpg.sweep_stale_clusters(tmp_path) == [] and r.exists()


def test_a_recycled_pid_is_a_dead_owner_because_the_start_time_differs(tmp_path):
    r = _mk(tmp_path, "suvarna_pg_recycled", pid=os.getpid(), start="Mon Jan  1 00:00:00 2001")        # same live pid, another process generation
    assert dpg.sweep_stale_clusters(tmp_path) == [str(r)] and not r.exists()


def test_sweep_ignores_a_marker_that_names_another_root_and_entries_that_are_not_ours(tmp_path):
    pid, start = _dead_pid()
    wrong = _mk(tmp_path, "suvarna_pg_wrongroot", pid=pid, start=start, root_field="/somewhere/else")
    other = _mk(tmp_path, "other_dir", pid=pid, start=start)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    keep = elsewhere / "keepme"
    keep.mkdir()
    (keep / "data").mkdir()
    base = tmp_path / "base"
    base.mkdir()
    link = base / "suvarna_pg_link"
    link.symlink_to(keep)
    (keep / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": str(link), "created": 0}))   # a VALID marker behind a symlink
    assert dpg.sweep_stale_clusters(base) == [] and dpg.sweep_stale_clusters(tmp_path) == []
    assert wrong.exists() and other.exists() and keep.exists() and (keep / "data").exists() and link.is_symlink()


def test_sweep_is_quiet_on_an_empty_or_missing_base(tmp_path):
    assert dpg.sweep_stale_clusters(tmp_path) == []
    assert dpg.sweep_stale_clusters(tmp_path / "nope") == []


def test_reap_refuses_without_a_marker(tmp_path):
    r = _mk(tmp_path, "suvarna_pg_x", pid=None, start=None)
    assert wd.reap(r, "/bin/false") is False and r.exists()


def test_the_watchdog_exits_quietly_when_the_root_is_already_gone(tmp_path):
    gone = tmp_path / "suvarna_pg_gone"
    p = subprocess.run([sys.executable, str(HERE / "_pg_watchdog.py"), str(os.getpid()), wd.proc_start(os.getpid()), str(gone), "/bin/false"],
                       capture_output=True, timeout=60)
    assert p.returncode == 0 and not gone.exists()


# ---------------------------------------------------------------- the seeded kill -9 ---------------------------------------------------------

CHILD = textwrap.dedent('''
    import sys, time, pathlib
    sys.path.insert(0, {here!r})
    import _disposable_pg as d
    cl = d.start_cluster(d.find_bin_dir())
    print(cl.root, flush=True)
    time.sleep(600)
''')


@NEEDS_PG
def test_a_sigkilled_owner_leaves_no_cluster_and_no_directory_behind(tmp_path):
    child = subprocess.Popen([sys.executable, "-c", CHILD.format(here=str(HERE))], stdout=subprocess.PIPE, text=True,
                             env={k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"})
    root = None
    try:
        root = pathlib.Path(child.stdout.readline().strip())
        assert root.name.startswith("suvarna_pg_") and (root / wd.OWNER_MARKER).exists() and (root / "data" / "postmaster.pid").exists()
        assert _postgres_running_on(root / "data")
        os.kill(child.pid, signal.SIGKILL)
        child.wait(timeout=30)
        deadline = time.time() + 60
        while time.time() < deadline and (root.exists() or _postgres_running_on(root / "data")):
            time.sleep(1.0)
        assert not root.exists(), "the watchdog did not delete the directory of a SIGKILLed owner"
        assert not _postgres_running_on(root / "data"), "a postmaster of a SIGKILLed owner is still running"
    finally:
        if child.poll() is None:
            child.kill()
        if root is not None and root.exists():                       # never leave the leak this test is about
            wd.reap(root, str(BIN / "pg_ctl"))


@NEEDS_PG
def test_a_normal_stop_removes_everything_and_the_watchdog_then_exits(tmp_path):
    cl = dpg.start_cluster(BIN)
    root = cl.root
    cl.stop()
    assert not root.exists()
    time.sleep(wd.POLL_SECONDS + 2)                                   # the watchdog notices the root is gone and exits without touching anything
    assert not root.exists()


@NEEDS_PG
def test_the_sweep_reaps_a_real_leaked_cluster_of_a_dead_owner(tmp_path):
    """Seed a real orphan: start a cluster in a child, SIGKILL the child AND its watchdog, then a new start sweeps it."""
    child = subprocess.Popen([sys.executable, "-c", CHILD.format(here=str(HERE))], stdout=subprocess.PIPE, text=True)
    root = pathlib.Path(child.stdout.readline().strip())
    try:
        out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
        for ln in out.splitlines():
            if "_pg_watchdog.py" in ln and str(root) in ln:
                os.kill(int(ln.split()[0]), signal.SIGKILL)
        os.kill(child.pid, signal.SIGKILL)
        child.wait(timeout=30)
        assert root.exists() and _postgres_running_on(root / "data")      # a genuine leak (no watchdog left)
        reaped = dpg.sweep_stale_clusters(pg_ctl=str(BIN / "pg_ctl"))
        assert str(root) in reaped and not root.exists() and not _postgres_running_on(root / "data")
    finally:
        if child.poll() is None:
            child.kill()
        if root.exists():
            wd.reap(root, str(BIN / "pg_ctl"))
