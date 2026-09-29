"""hold_guard.py: the PreToolUse hook enforcing charter §8 (the hold switch) for the two unattended
execution sessions. Pure-function evaluate() covers the branch matrix; main() covers stdin plumbing,
malformed input, and event emission — no real Claude Code hook invocation."""
import io
import json
import os
import subprocess
import sys

import pytest

from suvarna_tracker import hold_guard as HG
from suvarna_tracker.events import EventLog

GOVERNANCE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WRAPPER_PATH = os.path.join(GOVERNANCE_DIR, "suvarna_tracker", "hold_guard.sh")


def _events(events_path):
    log = EventLog(events_path)
    log.refresh()
    return log.events


def _set_hold(tmp_path, home_name="home"):
    home = tmp_path / home_name
    os.makedirs(home / "run", exist_ok=True)
    open(home / "run" / "SUVARNA_HOLD", "w").close()
    return str(home)


def _no_hold_home(tmp_path, home_name="home"):
    home = tmp_path / home_name
    os.makedirs(home / "run", exist_ok=True)
    return str(home)


# ---- evaluate(): the branch matrix ---------------------------------------------------------------

def test_no_hold_bash_command_passes(tmp_path):
    home = _no_hold_home(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": "git status --short"}, home=home)
    assert not blocked and reason == ""


def test_no_hold_agent_passes(tmp_path):
    home = _no_hold_home(tmp_path)
    blocked, reason = HG.evaluate("Agent", {}, home=home)
    assert not blocked


def test_hold_blocks_agent_dispatch(tmp_path):
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Agent", {"description": "new lane work"}, home=home)
    assert blocked and "no new dispatch" in reason and "charter §8" in reason


def test_hold_blocks_dispatch_like_bash(tmp_path):
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": "~/.config/suvarna/bin/suvarna-build --level 3"}, home=home)
    assert blocked and "suvarna-build" in reason


@pytest.mark.parametrize("marker", ["suvarna-build", "suvarna_level_wave", "nikasha_certify",
                                    "gh pr merge", "orchestrator", "--apply"])
def test_hold_blocks_every_dispatch_marker(tmp_path, marker):
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": f"some command with {marker} in it"}, home=home)
    assert blocked and marker in reason


@pytest.mark.parametrize("marker", ["lane_launch", "claude -p", "codex exec", "kimi -p",
                                    "python -m suvarna_tracker.lane_launch"])
def test_hold_blocks_every_f4_added_dispatch_marker(tmp_path, marker):
    """F4 (independent review): the lane launcher and every agent-launching CLI this campaign uses
    are dispatch-like too, not just the build/certify/merge surfaces the marker list originally
    named."""
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": f"some command with {marker} in it"}, home=home)
    # "lane_launch" is a substring of the longer "python -m suvarna_tracker.lane_launch" marker, so
    # the shorter marker can be the one reported — what matters is that the call is blocked at all.
    assert blocked and "charter §6, §8" in reason


def test_hold_allows_non_dispatch_bash_to_finish(tmp_path):
    """'Finish the items already running' (charter §8): a plain git/test/read command is not
    production-visible or dispatch-like, so it must run through even while the hold is set."""
    home = _set_hold(tmp_path)
    for command in ["git commit -- foo/bar.py", "python3 -m pytest suvarna_tracker/tests -q",
                    "python3 -m suvarna_tracker.emit item --actor builder --item X.1 --state running",
                    "git status", "cat evidence/notes.md"]:
        blocked, reason = HG.evaluate("Bash", {"command": command}, home=home)
        assert not blocked, f"unexpectedly blocked: {command}"


def test_hold_allows_other_tools(tmp_path):
    home = _set_hold(tmp_path)
    for tool in ["Read", "Edit", "Write", "Glob", "Grep", "TodoWrite"]:
        blocked, reason = HG.evaluate(tool, {}, home=home)
        assert not blocked, f"unexpectedly blocked tool {tool}"


@pytest.mark.parametrize("command", [
    "rm /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "rm -f $SUVARNA_HOME/run/SUVARNA_HOLD",
    "rm -rf /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "unlink /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "cd /Users/Dev/suvarna/run && rm SUVARNA_HOLD",
])
def test_hold_delete_always_refused_even_without_hold(tmp_path, command):
    home = _no_hold_home(tmp_path)  # hold is NOT even set
    blocked, reason = HG.evaluate("Bash", {"command": command}, home=home)
    assert blocked and "may only be removed by the native" in reason


def test_hold_delete_refused_while_hold_is_set_too(tmp_path):
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": "rm /Users/Dev/suvarna/run/SUVARNA_HOLD"}, home=home)
    assert blocked and "may only be removed by the native" in reason


@pytest.mark.parametrize("command", [
    "mv /Users/Dev/suvarna/run/SUVARNA_HOLD /tmp/moved-away",
    "truncate -s 0 /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "echo cleared > /Users/Dev/suvarna/run/SUVARNA_HOLD",
    ": > $SUVARNA_HOME/run/SUVARNA_HOLD",
])
def test_hold_delete_refused_for_f4_added_verbs_and_redirect(tmp_path, command):
    """F4 (independent review): mv/truncate/redirect can destroy or empty the hold file just as
    effectively as rm/unlink — the original regex only recognised rm/unlink."""
    home = _no_hold_home(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": command}, home=home)
    assert blocked and "may only be removed by the native" in reason


def test_unrelated_rm_is_not_treated_as_hold_delete(tmp_path):
    home = _no_hold_home(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": "rm -rf /Users/Dev/suvarna/lanes/old-lane"}, home=home)
    assert not blocked


def test_missing_tool_input_is_refused_under_uncertainty_while_hold_is_set(tmp_path):
    """F4 (independent review): a missing tool_input can never be classified as a command at all —
    'cannot classify' fails closed while the hold is set (never assumed safe), rather than the
    pre-fix reading of "no command text => not dispatch-like". Never crashes either way."""
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", None, home=home)
    assert blocked and "could not be classified" in reason


def test_missing_tool_input_is_allowed_when_hold_is_off(tmp_path):
    """The same uncertainty is not a reason to wedge non-dispatch work when there is no hold to
    enforce in the first place."""
    home = _no_hold_home(tmp_path)
    blocked, reason = HG.evaluate("Bash", None, home=home)
    assert not blocked


def test_missing_command_key_is_refused_under_uncertainty_while_hold_is_set(tmp_path):
    """F4: tool_input present but with no 'command' key at all is the same 'cannot classify' case
    as a missing tool_input entirely — not the pre-fix reading of "empty command, not dispatch-like".
    An explicit empty string command, by contrast, IS classifiable and safe (see below)."""
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {}, home=home)
    assert blocked and "could not be classified" in reason


def test_explicit_empty_command_string_is_classifiable_and_not_dispatch_like(tmp_path):
    home = _set_hold(tmp_path)
    blocked, reason = HG.evaluate("Bash", {"command": ""}, home=home)
    assert not blocked


# ---- main(): stdin plumbing, exit codes, event emission -----------------------------------------

def _run_main(monkeypatch, tmp_path, payload, home):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload) if payload is not None else ""))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    return HG.main([])


def test_main_exit_0_when_not_blocked(monkeypatch, tmp_path):
    home = _no_hold_home(tmp_path)
    rc = _run_main(monkeypatch, tmp_path, {"tool_name": "Bash", "tool_input": {"command": "git status"}}, home)
    assert rc == 0


def test_main_exit_2_and_stderr_when_blocked(monkeypatch, tmp_path, capsys):
    home = _set_hold(tmp_path)
    rc = _run_main(monkeypatch, tmp_path, {"tool_name": "Agent", "tool_input": {}}, home)
    assert rc == 2
    err = capsys.readouterr().err
    assert "charter §8" in err


def test_main_emits_a_note_on_block(monkeypatch, tmp_path):
    home = _set_hold(tmp_path)
    _run_main(monkeypatch, tmp_path, {"tool_name": "Agent", "tool_input": {}}, home)
    events = _events(os.path.join(home, "run", "EVENTS.jsonl"))
    notes = [e for e in events if e["kind"] == "note" and e["actor"] == "hold-guard"]
    assert len(notes) == 1 and "BLOCKED Agent" in notes[0]["detail"]


def test_main_emits_no_note_when_allowed(monkeypatch, tmp_path):
    home = _no_hold_home(tmp_path)
    _run_main(monkeypatch, tmp_path, {"tool_name": "Bash", "tool_input": {"command": "git status"}}, home)
    events_file = os.path.join(home, "run", "EVENTS.jsonl")
    events = _events(events_file) if os.path.exists(events_file) else []
    assert events == []


def test_main_malformed_stdin_exits_0_and_logs(monkeypatch, tmp_path):
    home = _no_hold_home(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json { at all"))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    rc = HG.main([])
    assert rc == 0
    events = _events(os.path.join(home, "run", "EVENTS.jsonl"))
    notes = [e for e in events if e["kind"] == "note" and e["actor"] == "hold-guard"]
    assert len(notes) == 1 and "malformed hook stdin" in notes[0]["detail"]


def test_main_empty_stdin_exits_0(monkeypatch, tmp_path):
    home = _no_hold_home(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    assert HG.main([]) == 0


def test_main_non_object_json_stdin_exits_0(monkeypatch, tmp_path):
    home = _no_hold_home(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(["not", "an", "object"])))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    assert HG.main([]) == 0


# ---- F4 (independent review): malformed stdin fails closed while the hold is set ----------------

def test_main_malformed_stdin_exits_2_while_hold_is_set(monkeypatch, tmp_path, capsys):
    home = _set_hold(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json { at all"))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    rc = HG.main([])
    assert rc == 2
    assert "refusing under uncertainty" in capsys.readouterr().err
    events = _events(os.path.join(home, "run", "EVENTS.jsonl"))
    notes = [e for e in events if e["kind"] == "note" and e["actor"] == "hold-guard"]
    assert len(notes) == 1 and "BLOCKED" in notes[0]["detail"]


def test_main_empty_stdin_exits_2_while_hold_is_set(monkeypatch, tmp_path):
    home = _set_hold(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    assert HG.main([]) == 2


def test_main_non_object_json_stdin_exits_2_while_hold_is_set(monkeypatch, tmp_path):
    home = _set_hold(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(["not", "an", "object"])))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    assert HG.main([]) == 2


def test_main_missing_tool_name_exits_2_while_hold_is_set(monkeypatch, tmp_path):
    home = _set_hold(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "git status"}})))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    assert HG.main([]) == 2


def test_main_never_crashes_when_events_log_unwritable(monkeypatch, tmp_path):
    """A logging failure must never turn into an unhandled exception in the hook."""
    home = _set_hold(tmp_path)
    events_dir_as_file = os.path.join(home, "run", "EVENTS.jsonl")
    # events_path is a directory, not a file: append() will fail internally
    os.remove(events_dir_as_file) if os.path.exists(events_dir_as_file) else None
    os.makedirs(events_dir_as_file, exist_ok=True)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Agent", "tool_input": {}})))
    monkeypatch.setenv("SUVARNA_HOME", home)
    monkeypatch.delenv("SUVARNA_EVENTS", raising=False)
    rc = HG.main([])  # must not raise
    assert rc == 2


# ---- helper functions ------------------------------------------------------------------------

def test_home_dir_defaults(monkeypatch):
    monkeypatch.delenv("SUVARNA_HOME", raising=False)
    assert HG.home_dir() == HG.DEFAULT_HOME


def test_home_dir_reads_env(monkeypatch):
    monkeypatch.setenv("SUVARNA_HOME", "/tmp/custom-home")
    assert HG.home_dir() == "/tmp/custom-home"


def test_hold_path_join(tmp_path):
    assert HG.hold_path(str(tmp_path)) == os.path.join(str(tmp_path), "run", "SUVARNA_HOLD")


def test_matched_dispatch_marker_returns_none_when_absent():
    assert HG.matched_dispatch_marker("git status") is None


def test_matched_dispatch_marker_returns_the_marker():
    assert HG.matched_dispatch_marker("run suvarna-build now") == "suvarna-build"


# ---- hold_guard.sh: the S14 fail-closed wrapper (review pass 3) ---------------------------------
#
# Every subprocess below runs with cwd=/tmp (never the governance dir), so a "broken PYTHONPATH"
# genuinely cannot resolve `suvarna_tracker` via `python3 -m`'s own cwd-on-sys.path behaviour — the
# same trap a first version of this test tripped over.

_BROKEN_PYTHONPATH = "/nonexistent/suvarna-broken-pythonpath"


def _run_wrapper(payload: dict, home: str, pythonpath: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": pythonpath, "SUVARNA_HOME": home}
    return subprocess.run(["bash", WRAPPER_PATH], input=json.dumps(payload), text=True,
                          capture_output=True, cwd="/tmp", env=env, timeout=15)


def test_wrapper_exists_and_is_executable():
    assert os.path.exists(WRAPPER_PATH)
    assert os.access(WRAPPER_PATH, os.X_OK)


def test_wrapper_passes_through_allow_with_working_pythonpath(tmp_path):
    p = _run_wrapper({"tool_name": "Bash", "tool_input": {"command": "git status"}},
                     str(tmp_path), GOVERNANCE_DIR)
    assert p.returncode == 0


def test_wrapper_passes_through_block_with_working_pythonpath(tmp_path):
    os.makedirs(tmp_path / "run", exist_ok=True)
    open(tmp_path / "run" / "SUVARNA_HOLD", "w").close()
    p = _run_wrapper({"tool_name": "Agent", "tool_input": {}}, str(tmp_path), GOVERNANCE_DIR)
    assert p.returncode == 2
    assert "charter §8" in p.stderr


def test_wrapper_fails_closed_for_agent_when_guard_cannot_load(tmp_path):
    p = _run_wrapper({"tool_name": "Agent", "tool_input": {}}, str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 2
    assert "failing closed" in p.stderr


@pytest.mark.parametrize("marker", ["suvarna-build", "suvarna_level_wave", "nikasha_certify",
                                    "gh pr merge", "orchestrator", "--apply"])
def test_wrapper_fails_closed_for_dispatch_like_bash_when_guard_cannot_load(tmp_path, marker):
    p = _run_wrapper({"tool_name": "Bash", "tool_input": {"command": f"some command with {marker} in it"}},
                     str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 2
    assert "failing closed" in p.stderr


@pytest.mark.parametrize("marker", ["lane_launch", "claude -p", "codex exec", "kimi -p",
                                    "python -m suvarna_tracker.lane_launch"])
def test_wrapper_fails_closed_for_f4_added_dispatch_markers_when_guard_cannot_load(tmp_path, marker):
    """F4 (independent review): the wrapper's own independent fallback classifier mirrors the same
    extended marker list the real guard now uses — a broken PYTHONPATH must not narrow coverage."""
    p = _run_wrapper({"tool_name": "Bash", "tool_input": {"command": f"some command with {marker} in it"}},
                     str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 2
    assert "failing closed" in p.stderr


@pytest.mark.parametrize("command", [
    "rm /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "mv /Users/Dev/suvarna/run/SUVARNA_HOLD /tmp/gone",
    "truncate -s 0 /Users/Dev/suvarna/run/SUVARNA_HOLD",
    "echo x > /Users/Dev/suvarna/run/SUVARNA_HOLD",
])
def test_wrapper_refuses_hold_delete_when_guard_cannot_load(tmp_path, command):
    """F4: the pre-fix wrapper fallback checked dispatch markers only — it never protected the hold
    file itself when the real guard could not even load. Now it does, unconditionally."""
    p = _run_wrapper({"tool_name": "Bash", "tool_input": {"command": command}}, str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 2
    assert "may only be removed by the native" in p.stderr


def test_wrapper_allows_non_dispatch_bash_when_guard_cannot_load(tmp_path):
    p = _run_wrapper({"tool_name": "Bash", "tool_input": {"command": "git status"}},
                     str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 0
    assert "allowing" in p.stderr


def test_wrapper_allows_unknown_tool_when_guard_cannot_load(tmp_path):
    p = _run_wrapper({"tool_name": "Read", "tool_input": {}}, str(tmp_path), _BROKEN_PYTHONPATH)
    assert p.returncode == 0


def test_wrapper_allows_malformed_stdin_when_guard_cannot_load(tmp_path):
    """The independent fallback classifier must never itself crash or hang on bad stdin."""
    env = {**os.environ, "PYTHONPATH": _BROKEN_PYTHONPATH, "SUVARNA_HOME": str(tmp_path)}
    p = subprocess.run(["bash", WRAPPER_PATH], input="not json { at all", text=True,
                       capture_output=True, cwd="/tmp", env=env, timeout=15)
    assert p.returncode == 0
