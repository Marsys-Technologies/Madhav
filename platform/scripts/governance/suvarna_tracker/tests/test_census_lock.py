"""Fix 4 (review #24): "one census at a time" had no mechanism — this is the mechanism."""
import fcntl
import json
import os
import subprocess
import sys
import threading
import time

import pytest

from suvarna_tracker import census_lock as CL
from suvarna_tracker.events import EventLog


def test_second_holder_gets_75_immediately(tmp_path):
    home = str(tmp_path)
    lock_path, holder_path = CL.lock_paths(home)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        rc = CL.run_locked(home, [sys.executable, "-c", "pass"], wait=0)
        assert rc == CL.EX_TEMPFAIL == 75
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_second_holder_message_names_the_current_holder(tmp_path, capsys):
    home = str(tmp_path)
    lock_path, holder_path = CL.lock_paths(home)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    os.makedirs(os.path.dirname(holder_path), exist_ok=True)
    with open(holder_path, "w") as f:
        json.dump({"pid": 4242, "command": "my_census.py", "started_at": "2026-09-29T00:00:00+00:00"}, f)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        rc = CL.run_locked(home, [sys.executable, "-c", "pass"], wait=0)
        assert rc == 75
        err = capsys.readouterr().err
        assert "4242" in err and "my_census.py" in err
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_release_on_child_failure(tmp_path):
    home = str(tmp_path)
    rc = CL.run_locked(home, [sys.executable, "-c", "import sys; sys.exit(3)"])
    assert rc == 3
    # the lock must be free again immediately — a second run acquires it with no wait
    rc2 = CL.run_locked(home, [sys.executable, "-c", "pass"])
    assert rc2 == 0


def test_release_on_child_success_removes_holder_file(tmp_path):
    home = str(tmp_path)
    _, holder_path = CL.lock_paths(home)
    CL.run_locked(home, [sys.executable, "-c", "pass"])
    assert not os.path.exists(holder_path)


def test_holder_file_content_while_the_command_runs(tmp_path):
    home = str(tmp_path)
    _, holder_path = CL.lock_paths(home)
    out_file = tmp_path / "holder_snapshot.json"
    script = (
        "import json\n"
        f"with open({str(holder_path)!r}) as f:\n"
        "    d = json.load(f)\n"
        f"with open({str(out_file)!r}, 'w') as g:\n"
        "    json.dump(d, g)\n"
    )
    rc = CL.run_locked(home, [sys.executable, "-c", script])
    assert rc == 0
    snap = json.loads(out_file.read_text())
    assert snap["pid"] == os.getpid()
    assert snap["command"] == os.path.basename(sys.executable)
    assert "started_at" in snap and "argv" in snap


def test_wait_acquires_after_a_concurrent_release(tmp_path):
    home = str(tmp_path)
    lock_path, _ = CL.lock_paths(home)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)

    def release_later():
        time.sleep(0.5)
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    threading.Thread(target=release_later, daemon=True).start()
    t0 = time.time()
    rc = CL.run_locked(home, [sys.executable, "-c", "pass"], wait=5)
    elapsed = time.time() - t0
    assert rc == 0
    assert elapsed >= 0.3, "should have waited for the concurrent holder to release"


def test_wait_zero_default_does_not_poll(tmp_path):
    home = str(tmp_path)
    lock_path, _ = CL.lock_paths(home)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        t0 = time.time()
        rc = CL.run_locked(home, [sys.executable, "-c", "pass"])  # default wait=0
        assert rc == 75
        assert time.time() - t0 < 1.0
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_emit_writes_acquire_and_release_notes(tmp_path):
    home = str(tmp_path)
    events_path = os.path.join(home, "run", "EVENTS.jsonl")
    rc = CL.run_locked(home, [sys.executable, "-c", "pass"], emit_flag=True, actor="census-runner")
    assert rc == 0
    log = EventLog(events_path)
    log.refresh()
    notes = [e for e in log.events if e["kind"] == "note" and e["actor"] == "census-runner"]
    assert len(notes) == 2
    assert "acquired" in notes[0]["detail"] and "released" in notes[1]["detail"]


def test_no_emit_by_default(tmp_path):
    home = str(tmp_path)
    events_path = os.path.join(home, "run", "EVENTS.jsonl")
    CL.run_locked(home, [sys.executable, "-c", "pass"])
    assert not os.path.exists(events_path)


def test_cli_main_requires_a_command(tmp_path, capsys):
    rc = CL.main(["--home", str(tmp_path)])
    assert rc == 2
    assert "usage" in capsys.readouterr().err


def test_cli_main_runs_command_and_returns_its_exit_code(tmp_path):
    rc = CL.main(["--home", str(tmp_path), "--", sys.executable, "-c", "import sys; sys.exit(7)"])
    assert rc == 7


# ---- --census-only (B6, review pass 3) --------------------------------------------------------

GOOD_CENSUS_COMMAND = ["bash", "-c",
                      "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && "
                      "python3 platform/scripts/governance/asset_census.py --layer ka_gochara "
                      "--out /Users/Dev/suvarna/evidence/census.json"]


def test_is_census_only_command_accepts_the_exact_inspector_form():
    assert CL.is_census_only_command(GOOD_CENSUS_COMMAND)


def test_is_census_only_command_accepts_with_no_flags():
    assert CL.is_census_only_command(
        ["bash", "-c", "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && "
                       "python3 platform/scripts/governance/asset_census.py"])


def test_is_census_only_command_accepts_the_trunk_worktree_root():
    """CODE-35 (review pass 3 disposition): the second, post-E4.1 checkout is validated too."""
    assert CL.is_census_only_command(
        ["bash", "-c", "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/suvarna/trunk && "
                       "python3 platform/scripts/governance/asset_census.py --layer ka_gochara"])


def test_is_census_only_command_rejects_a_third_checkout_root():
    assert not CL.is_census_only_command(
        ["bash", "-c", "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/some-other-checkout && "
                       "python3 platform/scripts/governance/asset_census.py"])


@pytest.mark.parametrize("bad_inner", [
    "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && "
    "python3 platform/scripts/governance/asset_census.py && rm -rf /",
    "source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && "
    "python3 some_other_script.py",
    "source ~/.config/suvarna/pgenv.sh && cd /tmp && "
    "python3 platform/scripts/governance/asset_census.py",
    "echo hello",
])
def test_is_census_only_command_rejects_anything_else(bad_inner):
    assert not CL.is_census_only_command(["bash", "-c", bad_inner])


def test_is_census_only_command_rejects_wrong_argv_shape():
    assert not CL.is_census_only_command(["python3", "-c", "print(1)"])
    assert not CL.is_census_only_command(["bash", "-c", "x", "extra"])


def test_run_locked_census_only_refuses_a_non_matching_command_without_the_lock(tmp_path):
    home = str(tmp_path)
    rc = CL.run_locked(home, ["bash", "-c", "echo not the census"], census_only=True)
    assert rc == CL.EX_NOT_CENSUS_ONLY
    # the lock must never have been touched: a second, ordinary call acquires it immediately
    rc2 = CL.run_locked(home, [sys.executable, "-c", "pass"])
    assert rc2 == 0


def test_run_locked_census_only_allows_the_exact_form(tmp_path, monkeypatch):
    home = str(tmp_path)
    # Substitute a harmless real command for the fixed asset_census.py invocation so this test
    # does not depend on a real /Users/Dev/madhav-nikasha checkout.
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0))
    rc = CL.run_locked(home, GOOD_CENSUS_COMMAND, census_only=True)
    assert rc == 0


def test_cli_main_census_only_flag_refuses_arbitrary_command(tmp_path, capsys):
    rc = CL.main(["--home", str(tmp_path), "--census-only", "--", sys.executable, "-c", "pass"])
    assert rc == CL.EX_NOT_CENSUS_ONLY
    assert "census-only" in capsys.readouterr().err


def test_two_concurrent_processes_only_one_gets_in(tmp_path):
    """End-to-end with real subprocesses: launch the CLI twice at once against the same lock; one
    must succeed and the other must get exit 75."""
    home = str(tmp_path)
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../governance
    script = (
        "import time\n"
        "time.sleep(1.0)\n"
    )
    import subprocess
    env = dict(os.environ)
    procs = [
        subprocess.Popen([sys.executable, "-m", "suvarna_tracker.census_lock", "--home", home,
                          "--", sys.executable, "-c", script], cwd=here, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(2)
    ]
    time.sleep(0.2)  # let the first one grab the lock
    rcs = [p.wait(timeout=10) for p in procs]
    assert sorted(rcs) == [0, 75]
