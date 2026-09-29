"""F6 (independent review): exclusive Conductor runtime ownership, one fenced lock per session."""
import json
import os

import pytest

from suvarna_tracker import conductor_lock as CL


def test_lock_path_is_per_session(tmp_path):
    p1 = CL.lock_path("engine", home=str(tmp_path))
    p2 = CL.lock_path("exec", home=str(tmp_path))
    assert p1 != p2
    assert p1 == os.path.join(str(tmp_path), "run", "locks", "conductor-engine.lock")


def test_acquire_writes_pid_and_start(tmp_path):
    result = CL.acquire("engine", home=str(tmp_path), pid=4242)
    assert result["pid"] == 4242 and result["reclaimed_from"] is None
    with open(result["path"], encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"pid": 4242, "started_at": result["started_at"]}


def test_second_acquire_for_same_session_is_refused_when_pid_is_alive(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=os.getpid())  # our own pid: definitely alive
    with pytest.raises(CL.LockHeld) as exc_info:
        CL.acquire("engine", home=str(tmp_path), pid=99999)
    assert exc_info.value.session == "engine" and exc_info.value.pid == os.getpid()


def test_different_sessions_do_not_conflict(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=os.getpid())
    result = CL.acquire("exec", home=str(tmp_path), pid=os.getpid())  # must not raise
    assert result["session"] == "exec"


def test_stale_lock_from_dead_pid_is_reclaimed(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=999999)  # a pid that (almost certainly) does not exist
    result = CL.acquire("engine", home=str(tmp_path), pid=os.getpid())
    assert result["reclaimed_from"] == 999999
    assert result["pid"] == os.getpid()


def test_is_held_by_live_process_true_for_live_pid(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=os.getpid())
    assert CL.is_held_by_live_process("engine", home=str(tmp_path)) is True


def test_is_held_by_live_process_false_for_dead_pid(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=999999)
    assert CL.is_held_by_live_process("engine", home=str(tmp_path)) is False


def test_is_held_by_live_process_false_when_no_lock_at_all(tmp_path):
    assert CL.is_held_by_live_process("engine", home=str(tmp_path)) is False


def test_release_removes_lock_owned_by_the_same_pid(tmp_path):
    CL.acquire("engine", home=str(tmp_path), pid=4242)
    assert CL.release("engine", home=str(tmp_path), pid=4242) is True
    assert not os.path.exists(CL.lock_path("engine", home=str(tmp_path)))


def test_release_refuses_to_remove_a_lock_owned_by_a_different_pid(tmp_path):
    """A crashed-then-restarted holder must never accidentally free a NEW owner's lock."""
    CL.acquire("engine", home=str(tmp_path), pid=999999)  # dead pid
    CL.acquire("engine", home=str(tmp_path), pid=os.getpid())  # reclaimed by us
    assert CL.release("engine", home=str(tmp_path), pid=999999) is False  # the old, dead pid
    assert os.path.exists(CL.lock_path("engine", home=str(tmp_path)))


def test_update_pid_preserves_started_at_and_changes_pid(tmp_path):
    result = CL.acquire("engine", home=str(tmp_path), pid=os.getpid())
    CL.update_pid("engine", 4242, home=str(tmp_path))
    s = CL.status("engine", home=str(tmp_path))
    assert s["pid"] == 4242 and s["started_at"] == result["started_at"]


def test_release_of_nonexistent_lock_returns_false(tmp_path):
    assert CL.release("engine", home=str(tmp_path)) is False


def test_status_reports_held_and_live(tmp_path):
    assert CL.status("engine", home=str(tmp_path)) == {"held": False, "pid": None, "started_at": None, "live": False}
    CL.acquire("engine", home=str(tmp_path), pid=os.getpid())
    s = CL.status("engine", home=str(tmp_path))
    assert s["held"] is True and s["live"] is True and s["pid"] == os.getpid()


def test_is_pid_alive_false_for_zero_and_negative():
    assert CL.is_pid_alive(0) is False
    assert CL.is_pid_alive(-1) is False


def test_is_pid_alive_true_for_our_own_pid():
    assert CL.is_pid_alive(os.getpid()) is True


def test_is_pid_alive_false_for_a_pid_that_does_not_exist():
    assert CL.is_pid_alive(999999) is False


# ---- CLI --------------------------------------------------------------------------------------

def test_cli_acquire_and_release(tmp_path, capsys):
    rc = CL.main(["acquire", "--session", "engine", "--home", str(tmp_path), "--pid", "4242"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out.split(" (")[0])
    assert out["pid"] == 4242

    rc2 = CL.main(["release", "--session", "engine", "--home", str(tmp_path), "--pid", "4242"])
    assert rc2 == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["released"] is True


def test_cli_acquire_refused_exits_75(tmp_path, capsys):
    CL.main(["acquire", "--session", "engine", "--home", str(tmp_path), "--pid", str(os.getpid())])
    capsys.readouterr()
    rc = CL.main(["acquire", "--session", "engine", "--home", str(tmp_path), "--pid", "4242"])
    assert rc == CL.EXIT_LOCK_HELD == 75
    assert "refused" in capsys.readouterr().err


def test_cli_status(tmp_path, capsys):
    rc = CL.main(["status", "--session", "engine", "--home", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"held": False, "pid": None, "started_at": None, "live": False}
