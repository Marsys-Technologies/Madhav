"""Suvarṇa lane launcher (CODE-18): refusals (hold, missing lane, missing prompt), the exact
`claude` invocation (never a bypass flag), the detached launch, pid recording, and the emitted
`running` event. No real `claude` process is ever spawned — `launch_fn` is injected."""
import json
import os

import pytest

from suvarna_tracker import conductor_lock as CL
from suvarna_tracker import lane_launch as LL
from suvarna_tracker.events import EventLog


def _fake_launch(pid=4242):
    calls = []

    def fn(argv, cwd, log_path):
        calls.append({"argv": argv, "cwd": cwd, "log_path": log_path})
        return pid

    fn.calls = calls
    return fn


def _make_lane(tmp_path, qid, prompt="do the thing\n"):
    home = tmp_path / "home"
    lane = home / "lanes" / qid
    lane.mkdir(parents=True)
    if prompt is not None:
        (lane / "PROMPT.md").write_text(prompt)
    return str(home)


# ---- refusals -------------------------------------------------------------------------------

def test_refuses_when_hold_is_set(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    os.makedirs(os.path.join(home, "run"), exist_ok=True)
    open(os.path.join(home, "run", "SUVARNA_HOLD"), "w").close()
    fn = _fake_launch()
    with pytest.raises(LL.LaunchRefused, match="hold is set"):
        LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert fn.calls == []


def test_refuses_when_lane_worktree_missing(tmp_path):
    home = str(tmp_path / "home")
    fn = _fake_launch()
    with pytest.raises(LL.LaunchRefused, match="lane worktree does not exist"):
        LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert fn.calls == []


def test_refuses_when_no_prompt_file_and_no_default_prompt_md(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001", prompt=None)
    fn = _fake_launch()
    with pytest.raises(LL.LaunchRefused, match="no readable prompt"):
        LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert fn.calls == []


def test_refuses_when_prompt_file_is_empty(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001", prompt="   \n")
    fn = _fake_launch()
    with pytest.raises(LL.LaunchRefused, match="empty"):
        LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)


def test_refuses_when_explicit_prompt_file_missing(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    fn = _fake_launch()
    with pytest.raises(LL.LaunchRefused, match="no readable prompt"):
        LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium",
                  prompt_file=str(tmp_path / "nope.md"), launch_fn=fn)


def test_hold_checked_before_lane_existence(tmp_path):
    """When both the hold is set AND the lane is missing, the hold is the reported reason — the
    cheapest, most decisive refusal is checked first."""
    home = str(tmp_path / "home")  # lane does not exist either
    os.makedirs(os.path.join(home, "run"), exist_ok=True)
    open(os.path.join(home, "run", "SUVARNA_HOLD"), "w").close()
    reason = LL.check_refusal(home, "E1.1-build-001")
    assert reason is not None and "hold is set" in reason


# ---- the happy path ---------------------------------------------------------------------------

def test_launch_invokes_claude_with_exact_argv_never_a_bypass_flag(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001", prompt="the prompt text\n")
    fn = _fake_launch(pid=999)
    result = LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert result["pid"] == 999
    argv = fn.calls[0]["argv"]
    assert argv[0] == "claude"
    assert "-p" in argv and argv[argv.index("-p") + 1] == "the prompt text\n"
    assert "--settings" in argv
    assert argv[argv.index("--settings") + 1] == os.path.join(home, "config", "claude-settings.json")
    assert "--permission-mode" in argv and argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert "--model" in argv and argv[argv.index("--model") + 1] == "sonnet-5"
    assert "--dangerously-skip-permissions" not in argv
    assert not any("bypassPermissions" in a for a in argv)
    assert "--effort" not in argv  # never passed to claude itself


def test_launch_runs_with_the_lane_as_cwd(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    fn = _fake_launch()
    LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert fn.calls[0]["cwd"] == os.path.join(home, "lanes", "E1.1-build-001")


def test_launch_logs_to_evidence_qid_agent_log(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    fn = _fake_launch()
    result = LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    expected = os.path.join(home, "evidence", "E1.1-build-001", "agent.log")
    assert result["log_path"] == expected
    assert fn.calls[0]["log_path"] == expected


def test_launch_records_pid_at_run_lanes_qid_pid(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    fn = _fake_launch(pid=1234)
    result = LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium", launch_fn=fn)
    pid_path = os.path.join(home, "run", "lanes", "E1.1-build-001.pid")
    assert result["pid_path"] == pid_path
    with open(pid_path, encoding="utf-8") as f:
        assert f.read().strip() == "1234"


def test_launch_emits_a_running_item_event_for_the_qid(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001")
    fn = _fake_launch()
    LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "high", launch_fn=fn)
    log = EventLog(os.path.join(home, "run", "EVENTS.jsonl"))
    log.refresh()
    assert len(log.events) == 1
    ev = log.events[0]
    assert ev["kind"] == "item" and ev["item"] == "E1.1-build-001" and ev["state"] == "running"
    assert ev["actor"] == "builder"


def test_launch_uses_explicit_prompt_file_over_default(tmp_path):
    home = _make_lane(tmp_path, "E1.1-build-001", prompt="default prompt\n")
    custom = tmp_path / "custom_prompt.md"
    custom.write_text("custom prompt\n")
    fn = _fake_launch()
    LL.launch(home, "E1.1-build-001", "builder", "sonnet-5", "medium",
              prompt_file=str(custom), launch_fn=fn)
    argv = fn.calls[0]["argv"]
    assert argv[argv.index("-p") + 1] == "custom prompt\n"


# ---- F6 (independent review): exclusive Conductor session launches --------------------------

def test_conductor_launch_does_not_require_a_lane_worktree(tmp_path):
    home = str(tmp_path / "home")  # no lanes/engine directory anywhere
    fn = _fake_launch(pid=777)
    result = LL.launch(home, "engine", "conductor", "sonnet-5", "medium",
                       prompt_file=str(_write_prompt(tmp_path, "conduct\n")), launch_fn=fn)
    assert result["pid"] == 777


def test_second_conductor_launch_for_same_session_is_refused_with_exit_75(tmp_path):
    home = str(tmp_path / "home")
    prompt = str(_write_prompt(tmp_path, "conduct\n"))
    fn1 = _fake_launch(pid=os.getpid())  # alive: our own test process
    LL.launch(home, "engine", "conductor", "sonnet-5", "medium", prompt_file=prompt, launch_fn=fn1)
    fn2 = _fake_launch(pid=4242)
    with pytest.raises(LL.LaunchRefused) as exc_info:
        LL.launch(home, "engine", "conductor", "sonnet-5", "medium", prompt_file=prompt, launch_fn=fn2)
    assert exc_info.value.exit_code == CL.EXIT_LOCK_HELD == 75
    assert fn2.calls == []  # never spawned


def test_conductor_lock_is_updated_to_the_real_launched_pid(tmp_path):
    home = str(tmp_path / "home")
    prompt = str(_write_prompt(tmp_path, "conduct\n"))
    fn = _fake_launch(pid=9999)
    LL.launch(home, "engine", "conductor", "sonnet-5", "medium", prompt_file=prompt, launch_fn=fn)
    status = CL.status("engine", home=home)
    assert status["pid"] == 9999 and status["live"] is False  # 9999 is (almost certainly) not alive


def test_different_conductor_sessions_launch_independently(tmp_path):
    home = str(tmp_path / "home")
    prompt = str(_write_prompt(tmp_path, "conduct\n"))
    fn1 = _fake_launch(pid=os.getpid())
    LL.launch(home, "engine", "conductor", "sonnet-5", "medium", prompt_file=prompt, launch_fn=fn1)
    fn2 = _fake_launch(pid=os.getpid())
    result = LL.launch(home, "exec", "conductor", "sonnet-5", "medium", prompt_file=prompt, launch_fn=fn2)
    assert result["pid"] == os.getpid()


def test_non_conductor_role_is_unaffected_by_conductor_lock(tmp_path):
    """A builder lane launch for a qid that happens to share a name with a Conductor session must
    not be gated by the conductor lock at all — the lock is keyed to role=='conductor' only."""
    home = _make_lane(tmp_path, "engine")
    CL.acquire("engine", home=home, pid=os.getpid())  # a live conductor lock for "engine"
    fn = _fake_launch(pid=555)
    result = LL.launch(home, "engine", "builder", "sonnet-5", "medium", launch_fn=fn)
    assert result["pid"] == 555


def _write_prompt(tmp_path, text):
    p = tmp_path / "conductor_prompt.md"
    p.write_text(text)
    return p


# ---- CLI ------------------------------------------------------------------------------------

def test_cli_refused_prints_reason_and_exits_2(tmp_path, capsys):
    home = str(tmp_path / "home")
    rc = LL.main(["--qid", "E1.1-build-001", "--role", "builder", "--model", "sonnet-5",
                 "--effort", "medium", "--home", home])
    assert rc == 2
    assert "refused" in capsys.readouterr().err


def test_cli_launch_exits_0_and_prints_pid(tmp_path, capsys, monkeypatch):
    home = _make_lane(tmp_path, "E1.1-build-001")
    monkeypatch.setattr(LL, "_default_launch", lambda argv, cwd, log_path: 555)
    rc = LL.main(["--qid", "E1.1-build-001", "--role", "builder", "--model", "sonnet-5",
                 "--effort", "medium", "--home", home])
    assert rc == 0
    assert "555" in capsys.readouterr().out
