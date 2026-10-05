"""test_disposable_pg_watchdog.py: a SIGKILLed pytest must not leave a disposable cluster behind.

  * the SEEDED KILL: a child process starts a real disposable cluster, then `kill -9`; within a bounded time the detached watchdog has
    stopped the postmaster and deleted the directory (no postgres process holds that data dir);
  * the SWEEP only reaps what it can attribute: a directory with a valid ownership marker whose owner process (pid + start time) is gone;
    never a directory without a marker, with a live owner, whose recorded pid was RECYCLED (different start time = dead owner: reaped),
    a symlink, a marker naming another root, or an entry that is not `suvarna_pg_*`;
  * the watchdog exits quietly (and touches nothing) once the cluster was stopped normally;
  * a dead owner is concluded ONLY from a conclusive `ps` answer: another timezone / locale, a `ps` timeout or OS error, or an empty start
    time never reads as dead (review round 1, HIGH); `data` must be a real directory inside the root (a symlink is never stopped); only a pid
    file naming a live postgres on THIS data dir is ever signalled (a recycled pid is not); a postmaster still up is never deleted under.
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


def _wait_until(pred, what: str, timeout: float = 30.0, step: float = 0.05):
    """Poll `pred` until it is truthy; raise (never silently continue) when the deadline passes, so a slow machine fails with a clear message and
    cannot let the test read state that an asynchronous step has not produced yet (the merge-queue flake in the immediate-mode stop test)."""
    deadline = time.monotonic() + timeout
    while True:
        got = pred()
        if got:
            return got
        if time.monotonic() >= deadline:
            raise AssertionError(f"timed out after {timeout:.0f}s waiting for {what}")
        time.sleep(step)


def _raw_ps(pid: int, field: str) -> str:
    """`ps` straight from the OS, independent of any monkeypatch of wd._ps in the calling test."""
    return subprocess.run(["ps", "-ww", "-p", str(pid), "-o", f"{field}="], capture_output=True, text=True, timeout=10).stdout.strip()


def _dead_pid(need_stamp: bool = True) -> tuple[int, str | None]:
    """A pid that is now gone, with the start stamp it had. The process is held alive until it is visible to `ps` (a fixed short sleep let a loaded
    machine finish the process before the stamp was read, giving an empty one), then killed and reaped."""
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        _wait_until(lambda: _raw_ps(p.pid, "stat"), "the child to be visible to ps")
        start = wd.proc_start(p.pid)
    finally:
        p.kill()
        p.wait()
    assert start or not need_stamp, "ps could not give the child's start stamp (a None/empty stamp would make every marker built from it invalid)"
    return p.pid, start


def _mk(base: pathlib.Path, name: str, *, pid: int | None, start: str | None, root_field: str | None = None) -> pathlib.Path:
    r = base / name
    r.mkdir()
    (r / "data").mkdir()
    if pid is not None:
        (r / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": root_field or str(r), "created": 0, "v": wd.MARKER_VERSION}))
    return r


def _postgres_running_on(data_dir: pathlib.Path) -> bool:
    out = subprocess.run(["ps", "-ww", "-axo", "command="], capture_output=True, text=True).stdout
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
    (keep / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": str(link), "created": 0, "v": wd.MARKER_VERSION}))   # a VALID marker behind a symlink
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
        def _watchdogs():
            out = subprocess.run(["ps", "-ww", "-axo", "pid=,command="], capture_output=True, text=True, timeout=10).stdout
            return [ln for ln in out.splitlines() if "_pg_watchdog.py" in ln and str(root) in ln]
        for ln in _wait_until(_watchdogs, "the cluster's watchdog process (a single early snapshot could miss it and let it reap the root itself)"):
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


# ---------------------------------------------------------------- review round 1: the "dead owner" decision must be conclusive -------------

def test_a_live_owner_stays_alive_under_another_timezone_or_locale(tmp_path, monkeypatch):
    r = _mk(tmp_path, "suvarna_pg_live_tz", pid=os.getpid(), start=wd.proc_start(os.getpid()))
    for env in ({"TZ": "Asia/Kolkata"}, {"TZ": "America/Los_Angeles"}, {"LC_ALL": "de_DE.UTF-8", "TZ": "Pacific/Auckland"}):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        assert dpg.sweep_stale_clusters(tmp_path) == [] and r.exists(), env


def test_an_inconclusive_ps_reads_the_owner_as_alive(tmp_path, monkeypatch):
    r = _mk(tmp_path, "suvarna_pg_ps_fail", pid=os.getpid(), start=wd.proc_start(os.getpid()))
    for exc in (subprocess.TimeoutExpired("ps", 10), OSError("ps vanished")):
        def boom(*a, _exc=exc, **k):
            raise _exc
        monkeypatch.setattr(wd.subprocess, "run", boom)
        assert wd.proc_start(os.getpid()) is None and wd.owner_alive(os.getpid(), "anything") is True
        assert dpg.sweep_stale_clusters(tmp_path) == [] and r.exists()
    monkeypatch.undo()

    class Odd:                                                    # a non-zero, non-"no such process" exit is also "cannot tell"
        returncode, stdout = 2, "garbled"
    monkeypatch.setattr(wd.subprocess, "run", lambda *a, **k: Odd())
    assert wd.proc_start(os.getpid()) is None and wd.owner_alive(os.getpid(), "x") is True


def test_a_marker_without_a_start_time_never_proves_the_owner_dead(tmp_path):
    pid, _ = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_empty_start", pid=pid, start="")
    assert wd.read_marker(r) is None and dpg.sweep_stale_clusters(tmp_path) == [] and r.exists()
    assert wd.owner_alive(pid, "") is True
    p = subprocess.run([sys.executable, str(HERE / "_pg_watchdog.py"), str(os.getpid()), "", str(r), "/bin/false"], capture_output=True, timeout=60)
    assert p.returncode == 2 and r.exists()                       # the watchdog refuses an empty start time and touches nothing


def test_proc_start_tells_gone_from_alive_and_a_zombie_from_a_live_process():
    pid, start = _dead_pid()
    assert wd.proc_start(pid) == wd.GONE and wd.owner_alive(pid, start) is False
    assert wd.proc_start(os.getpid()) not in (None, wd.GONE)
    z = subprocess.Popen([sys.executable, "-c", "pass"])           # an exited child not yet waited for is a zombie: its owner is gone
    _wait_until(lambda: (wd._ps("-p", str(z.pid), "-o", "stat=") or (0, ""))[1].strip().startswith("Z"), "the exited child to show as a zombie")
    try:
        assert wd.proc_start(z.pid) == wd.GONE
    finally:
        z.wait()


@pytest.mark.parametrize("bad", [True, "123", 1.5, None, [1]])
def test_a_marker_with_a_non_integer_pid_is_not_valid(tmp_path, bad):
    r = tmp_path / "suvarna_pg_badpid"
    r.mkdir()
    (r / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": bad, "parent_start": "x", "root": str(r), "v": wd.MARKER_VERSION}))
    assert wd.read_marker(r) is None


def test_a_file_named_like_a_cluster_dir_is_ignored(tmp_path):
    f = tmp_path / "suvarna_pg_file"
    f.write_text("x")
    assert dpg.sweep_stale_clusters(tmp_path) == [] and f.exists()


# ------------------------------------------------ review round 1: what `pg_ctl stop` may be aimed at (fake postmaster + fake pg_ctl) -----------

FAKE_PG_CTL = """#!/bin/bash
echo "$@" >> "{log}"
if [ "$7" = "stop" ] || [ "$8" = "stop" ] || [[ " $* " == *" stop"* ]]; then
  pid=$(head -1 "$2/postmaster.pid")
  kill "$pid" 2>/dev/null
fi
exit {rc}
"""


def _fake_postmaster(data: pathlib.Path, startup_delay: float = 0.0) -> subprocess.Popen:
    """A process whose command line reads `postgres -D <data>`, with a pid file naming it. Returns only once `ps` shows the EXEC'D form: before the
    `exec` the process is `bash -c ...`, whose command line already contains the data-dir string, so matching on the string alone returned too early
    (review of #3123). `startup_delay` stands in for a loaded runner where bash takes long to reach the exec."""
    p = subprocess.Popen(["bash", "-c", f'sleep {startup_delay}; exec -a "postgres -D {data}" sleep 600'])
    try:
        _wait_until(lambda: (wd._ps("-p", str(p.pid), "-o", "command=") or (0, ""))[1].strip().startswith(f"postgres -D {data}"),
                    "the fake postmaster's exec'd command line")
        (data / "postmaster.pid").write_text(f"{p.pid}\n{data}\n")
    except BaseException:
        p.kill()
        p.wait()
        raise
    return p


def _fake_ctl(tmp_path: pathlib.Path, rc: int = 0) -> tuple[str, pathlib.Path]:
    log = tmp_path / "ctl.log"
    script = tmp_path / "fake_pg_ctl"
    script.write_text(FAKE_PG_CTL.format(log=log, rc=rc))
    script.chmod(0o755)
    return str(script), log


def _alive(pid: int) -> bool:
    return wd.proc_start(pid) not in (None, wd.GONE)


def test_reap_stops_our_postmaster_with_the_immediate_mode_on_the_roots_own_data_dir(tmp_path):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_ours", pid=pid, start=start)
    pm = _fake_postmaster(r / "data")
    ctl, log = _fake_ctl(tmp_path)
    try:
        assert wd.reap(r, ctl) is True and not r.exists()
        argv = log.read_text().split()
        assert argv[:2] == ["-D", str(r / "data")] and "-m" in argv and argv[argv.index("-m") + 1] == "immediate" and argv[-1] == "stop"
    finally:
        pm.kill()
        pm.wait()


def test_a_stale_pid_file_naming_an_unrelated_live_process_is_never_signalled(tmp_path):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_stalepid", pid=pid, start=start)
    bystander = subprocess.Popen(["sleep", "600"])                # a recycled pid: alive, but not a postmaster on this data dir
    (r / "data" / "postmaster.pid").write_text(f"{bystander.pid}\n")
    ctl, log = _fake_ctl(tmp_path)
    try:
        assert wd.reap(r, ctl) is True and not r.exists()          # the directory goes, nothing is signalled
        assert not log.exists() and _alive(bystander.pid)
    finally:
        bystander.kill()
        bystander.wait()


def test_a_symlinked_data_dir_is_never_stopped_or_followed(tmp_path):
    pid, start = _dead_pid()
    victim = tmp_path / "victim"
    (victim / "data").mkdir(parents=True)
    pm = _fake_postmaster(victim / "data")
    evil = tmp_path / "suvarna_pg_evil"
    evil.mkdir()
    (evil / "data").symlink_to(victim / "data")
    (evil / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": str(evil), "created": 0, "v": wd.MARKER_VERSION}))
    ctl, log = _fake_ctl(tmp_path)
    try:
        assert wd.reap(evil, ctl) is False and dpg.sweep_stale_clusters(tmp_path, ctl) == []
        assert evil.exists() and _alive(pm.pid) and not log.exists() and (victim / "data" / "postmaster.pid").exists()
    finally:
        pm.kill()
        pm.wait()


def test_a_postmaster_that_will_not_stop_keeps_its_directory(tmp_path):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_stubborn", pid=pid, start=start)
    pm = _fake_postmaster(r / "data")
    ctl = tmp_path / "noop_ctl"
    ctl.write_text("#!/bin/bash\nexit 1\n")                       # a pg_ctl that does not stop anything
    ctl.chmod(0o755)
    try:
        assert wd.reap(r, str(ctl)) is False and r.exists() and _alive(pm.pid)
        assert wd.reap(r, None) is False and r.exists()            # a running postmaster and no pg_ctl at all
    finally:
        pm.kill()
        pm.wait()


def test_reap_does_nothing_when_ps_cannot_tell_whether_a_postmaster_runs(tmp_path, monkeypatch):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_unknown", pid=pid, start=start)
    (r / "data" / "postmaster.pid").write_text("12345\n")
    monkeypatch.setattr(wd, "_ps", lambda *a: None)
    assert wd.reap(r, "/bin/false") is False and r.exists()


def test_reap_refuses_a_symlinked_or_foreign_root_itself(tmp_path):
    pid, start = _dead_pid()
    real = _mk(tmp_path, "real", pid=pid, start=start)
    link = tmp_path / "suvarna_pg_link"
    link.symlink_to(real)
    (real / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": pid, "parent_start": start, "root": str(link), "created": 0, "v": wd.MARKER_VERSION}))
    assert wd.reap(link, "/bin/false") is False and real.exists() and link.is_symlink()


# ------------------------------------------------ review round 1: the wiring that the fixture promises (surviving mutants M14/M19/M21/M22) ----

@NEEDS_PG
def test_start_cluster_sweeps_first_with_its_own_pg_ctl_and_survives_a_failing_sweep(monkeypatch):
    calls = []

    def spy(base=None, pg_ctl=None):
        calls.append(pg_ctl)
        raise RuntimeError("housekeeping blew up")                # housekeeping must never fail a test run
    monkeypatch.setattr(dpg, "sweep_stale_clusters", spy)
    cl = dpg.start_cluster(BIN)
    try:
        assert len(calls) == 1 and calls[0] == str(BIN / "pg_ctl")
    finally:
        cl.stop()


@NEEDS_PG
def test_the_watchdog_is_detached_into_its_own_session():
    cl = dpg.start_cluster(BIN)
    try:
        def _find():
            out = subprocess.run(["ps", "-ww", "-axo", "pid=,pgid=,command="], capture_output=True, text=True, timeout=10).stdout
            return [ln.split(None, 2) for ln in out.splitlines() if "_pg_watchdog.py" in ln and str(cl.root) in ln]
        found = _wait_until(_find, "the watchdog process for this cluster")
        assert int(found[0][1]) != os.getpgrp(), "the watchdog shares this process group: a group kill would take it down too"
    finally:
        cl.stop()


# ------------------------------------------------ review round 2 --------------------------------------------------------------------------

def test_a_marker_from_an_earlier_stamp_format_is_never_reaped(tmp_path):
    """Round 2 MEDIUM-1: a marker without the current version (an earlier local-time start stamp) must not read a live owner as dead."""
    r = tmp_path / "suvarna_pg_oldstamp"
    (r / "data").mkdir(parents=True)
    (r / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": os.getpid(), "parent_start": "Mon Jan  1 00:00:00 2001", "root": str(r), "created": 0}))
    assert wd.read_marker(r) is None and dpg.sweep_stale_clusters(tmp_path) == [] and r.exists()


def test_the_stamp_the_fixture_writes_is_a_current_version_marker(tmp_path):
    dpg._write_owner_marker(tmp_path)
    m = json.loads((tmp_path / wd.OWNER_MARKER).read_text())
    assert m["v"] == wd.MARKER_VERSION and m["parent_pid"] == os.getpid() and m["parent_start"] == wd.proc_start(os.getpid())


def _cmdline_state(tmp_path: pathlib.Path, argv0: str) -> str:
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    p = subprocess.Popen(["bash", "-c", f'exec -a "{argv0.format(data=data)}" sleep 600'])
    try:
        shown = argv0.format(data=data)
        _wait_until(lambda: (wd._ps("-p", str(p.pid), "-o", "command=") or (0, ""))[1].strip().startswith(shown), "the fake process's command line (exec -a done)")
        (data / "postmaster.pid").write_text(f"{p.pid}\n")
        return wd._postmaster_state(data)
    finally:
        p.kill()
        p.wait()


def test_only_a_postgres_command_on_exactly_this_data_dir_is_ours(tmp_path):
    other = tmp_path / "other_data"
    assert _cmdline_state(tmp_path, "postgres -D {data} -p 5432") == "ours"
    assert _cmdline_state(tmp_path, "/opt/homebrew/bin/postgres -D {data}") == "ours"
    assert _cmdline_state(tmp_path, f"postgres -D {other}") == "foreign"                        # a live postmaster of ANOTHER data dir
    assert _cmdline_state(tmp_path, "tail -f {data}/postgresql.log") == "foreign"               # names the data dir, is not a postmaster
    assert _cmdline_state(tmp_path, "/opt/postgresql@15/bin/pg_ctl -D {data} stop") == "foreign"  # 'postgres' only as a substring
    assert _cmdline_state(tmp_path, "postgres -D {data}x") == "foreign"                         # a data dir that only starts with ours


def test_a_pid_file_naming_a_dead_process_reads_as_none_and_an_odd_ps_reply_as_unknown(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    dead, _ = _dead_pid()
    (data / "postmaster.pid").write_text(f"{dead}\n")
    assert wd._postmaster_state(data) == "none"
    monkeypatch.setattr(wd, "_ps", lambda *a: (2, "garbled"))
    assert wd._postmaster_state(data) == "unknown"


def test_ps_saying_gone_is_confirmed_by_the_kernel(monkeypatch):
    """Round 2 LOW-2: `ps` exit 1 with no output is only 'gone' when kill(pid, 0) agrees; a live pid under a lying ps is 'cannot tell'."""
    monkeypatch.setattr(wd, "_ps", lambda *a: (1, ""))
    assert wd.proc_start(os.getpid()) is None and wd.owner_alive(os.getpid(), "x") is True
    dead, _ = _dead_pid(need_stamp=False)                         # wd._ps is patched here, so the stamp is not meaningful
    assert wd.proc_start(dead) == wd.GONE


def test_a_stopped_owner_is_alive_and_ps_is_not_looked_up_on_the_path():
    s = subprocess.Popen(["sleep", "600"])
    try:
        os.kill(s.pid, signal.SIGSTOP)
        _wait_until(lambda: (wd._ps("-p", str(s.pid), "-o", "stat=") or (0, ""))[1].strip().startswith("T"), "the process to show as stopped")
        assert wd.proc_start(s.pid) not in (None, wd.GONE)
    finally:
        os.kill(s.pid, signal.SIGKILL)
        s.wait()
    assert os.path.isabs(wd._PS)


def test_rc_zero_with_empty_output_and_rc_nonzero_with_output_are_both_cannot_tell(monkeypatch):
    monkeypatch.setattr(wd, "_ps", lambda *a: (0, ""))
    assert wd.proc_start(os.getpid()) is None
    monkeypatch.setattr(wd, "_ps", lambda *a: (2, "Sat Oct  3 17:54:24 2026 S"))
    assert wd.proc_start(os.getpid()) is None


# ------------------------------------------------ review round 3 (LOW hardening + the unguarded mutants) --------------------------------------

@pytest.mark.parametrize("pid", [2**31, 2**63, 10**30, -5, 0, True])
def test_a_pid_that_cannot_exist_never_raises_and_never_reads_as_gone_by_kill(pid):
    assert wd._pid_absent(pid) is False
    if not isinstance(pid, bool):
        assert wd.proc_start(pid) in (None, wd.GONE)           # no exception escapes the ownership decision
        assert wd.owner_alive(pid, "x") in (True, False)


def test_a_marker_naming_an_impossible_pid_does_not_abort_the_sweep(tmp_path):
    bad = _mk(tmp_path, "suvarna_pg_a_hugepid", pid=10**30, start="Mon Jan  1 00:00:00 2001")
    pid, start = _dead_pid()
    good = _mk(tmp_path, "suvarna_pg_b_dead", pid=pid, start=start)
    reaped = dpg.sweep_stale_clusters(tmp_path)
    assert str(good) in reaped and not good.exists() and bad.exists()      # the bad marker reads alive (cannot tell), the sweep goes on


def test_a_pid_file_with_an_impossible_pid_reads_foreign_not_an_exception(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "postmaster.pid").write_text("99999999999999999999999\n")
    assert wd._postmaster_state(data) == "foreign"


def test_only_the_exact_postgres_basename_is_a_postmaster(tmp_path):
    assert _cmdline_state(tmp_path, "/x/notpostgres -D {data}") == "foreign"
    assert _cmdline_state(tmp_path, "/x/postgres -D {data}") == "ours"


def test_a_lying_ps_about_a_live_pid_file_pid_is_cannot_tell_not_none(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    (data / "postmaster.pid").write_text(f"{os.getpid()}\n")           # a live pid
    monkeypatch.setattr(wd, "_ps", lambda *a: (1, ""))                  # ps claims there is no such process
    assert wd._postmaster_state(data) == "unknown"


def test_the_postmaster_state_is_rechecked_after_the_stop(tmp_path, monkeypatch):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_recheck", pid=pid, start=start)
    pm = _fake_postmaster(r / "data")
    ctl, _ = _fake_ctl(tmp_path)
    try:
        real = subprocess.run
        monkeypatch.setattr(wd.subprocess, "run", lambda argv, *a, **k: None if argv[0] == ctl else real(argv, *a, **k))   # the stop does nothing at all
        assert wd.reap(r, ctl) is False and r.exists() and _alive(pm.pid)
    finally:
        monkeypatch.undo()
        pm.kill()
        pm.wait()


def test_the_fake_postmaster_helper_waits_for_the_exec_even_when_bash_is_slow(tmp_path):
    """Review of #3123 (HIGH): the wait used to be satisfied by the pre-exec `bash -c` line, so a slow exec let reap() see `bash`, skip pg_ctl and delete
    the root. With a 1.5 s startup delay the helper must still return only after the exec'd form is visible."""
    data = tmp_path / "data"
    data.mkdir()
    pm = _fake_postmaster(data, startup_delay=1.5)
    try:
        cmd = subprocess.run(["ps", "-ww", "-p", str(pm.pid), "-o", "command="], capture_output=True, text=True, timeout=10).stdout.strip()
        assert cmd.startswith(f"postgres -D {data}") and (data / "postmaster.pid").exists()
    finally:
        pm.kill()
        pm.wait()


def test_reap_stops_our_postmaster_even_when_the_fake_is_slow_to_exec(tmp_path):
    pid, start = _dead_pid()
    r = _mk(tmp_path, "suvarna_pg_slow", pid=pid, start=start)
    pm = _fake_postmaster(r / "data", startup_delay=1.5)
    ctl, log = _fake_ctl(tmp_path)
    try:
        assert wd.reap(r, ctl) is True and not r.exists()
        argv = log.read_text().split()
        assert argv[:2] == ["-D", str(r / "data")] and argv[-1] == "stop"
    finally:
        pm.kill()
        pm.wait()


def test_wait_until_raises_on_timeout_instead_of_continuing():
    with pytest.raises(AssertionError, match="timed out"):
        _wait_until(lambda: False, "a condition that never holds", timeout=0.3, step=0.05)
    assert _wait_until(lambda: "ok", "an immediately true condition", timeout=0.3) == "ok"
