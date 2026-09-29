"""runtime_settings.py: generating and checking the Suvarṇa execution sessions' local
.claude/settings.local.json (L.15). No real Claude Code CLI invocation; everything is exercised
through the module's own functions and its argv-driven main()."""
import json
import os

import pytest

from suvarna_tracker import runtime_settings as RS


def test_default_template_loads_and_is_an_object():
    template = RS.load_template()
    assert isinstance(template, dict)
    assert "permissions" in template


def test_template_defaultmode_is_dontask_never_bypass():
    template = RS.load_template()
    assert template["permissions"]["defaultMode"] == "dontAsk"
    assert template["permissions"]["defaultMode"] != "bypassPermissions"


def test_template_deny_contains_credential_rules():
    deny = RS.load_template()["permissions"]["deny"]
    joined = " ".join(deny)
    assert any(".config" in d for d in deny)
    assert any(".codex" in d for d in deny)
    assert "printenv" in joined


def test_template_deny_contains_main_push_and_force_push_rules():
    deny = RS.load_template()["permissions"]["deny"]
    assert any("git push" in d and "main" in d for d in deny)
    assert any("--force" in d for d in deny)
    assert any(d.endswith("-f*)") or " -f*" in d for d in deny)


def test_template_deny_blocks_bypass_invocations():
    deny = RS.load_template()["permissions"]["deny"]
    assert any("--dangerously-skip-permissions" in d for d in deny)
    assert any("bypassPermissions" in d for d in deny)


def test_template_allow_never_uses_dead_write_or_glob_path_rules():
    """v2.1.239 finding: Write(<glob>)/Glob(<glob>)/MultiEdit(<glob>) never match file permission
    checks (only Read(<glob>) and Edit(<glob>) do); an allow rule of that dead shape would silently
    grant nothing. The template must not contain one."""
    allow = RS.load_template()["permissions"]["allow"]
    for rule in allow:
        assert not rule.startswith("Write("), f"dead rule shape: {rule}"
        assert not rule.startswith("Glob("), f"dead rule shape: {rule}"
        assert not rule.startswith("Grep("), f"dead rule shape: {rule}"
        assert not rule.startswith("MultiEdit("), f"dead rule shape: {rule}"
        assert not rule.startswith("NotebookEdit("), f"dead rule shape: {rule}"


def test_template_edit_allow_scoped_to_lanes_evidence_and_state():
    allow = RS.load_template()["permissions"]["allow"]
    edit_rules = [r for r in allow if r.startswith("Edit(")]
    assert edit_rules, "expected at least one Edit(...) allow rule"
    for rule in edit_rules:
        assert any(scope in rule for scope in ("/suvarna/lanes/", "/suvarna/evidence/",
                                                "/control/suvarna/state/"))


def test_template_bash_git_status_rule_has_the_significant_space():
    allow = RS.load_template()["permissions"]["allow"]
    assert "Bash(git status *)" in allow


# ---- CODE-21: the arch §2.4 denies this template was missing, and the narrowed psql rule --------

def test_template_denies_gh_api():
    deny = RS.load_template()["permissions"]["deny"]
    assert "Bash(gh api*)" in deny


def test_template_denies_github_merge_and_postgres_mcp_tools():
    deny = RS.load_template()["permissions"]["deny"]
    assert "mcp__github__merge_pull_request" in deny
    assert "mcp__postgres__*" in deny


def test_template_denies_dbenv_and_env_files():
    deny = RS.load_template()["permissions"]["deny"]
    assert any("madhav-l3/dbenv" in d for d in deny)
    assert any(".env" in d for d in deny)


def test_template_denies_edit_on_suvarna_config_and_decisions_log():
    deny = RS.load_template()["permissions"]["deny"]
    assert "Edit(/Users/Dev/suvarna/config/**)" in deny
    assert "Edit(/Users/Dev/suvarna/run/DECISIONS.jsonl)" in deny


def test_template_denies_bare_claude_invocations():
    """The lane launcher (python3 -m suvarna_tracker.lane_launch) is what is allowed to spawn
    `claude` itself; this session's own Bash tool calling `claude` directly is denied."""
    deny = RS.load_template()["permissions"]["deny"]
    assert "Bash(claude *)" in deny


def test_template_psql_allow_rule_is_narrowed_to_the_reader_form():
    allow = RS.load_template()["permissions"]["allow"]
    assert "Bash(psql *)" not in allow  # the old, overly broad rule is gone
    assert any("pgenv.sh && psql" in a for a in allow)


def test_template_allows_lane_launch_and_lane_branch_push():
    allow = RS.load_template()["permissions"]["allow"]
    assert "Bash(python3 -m suvarna_tracker.lane_launch *)" in allow
    assert "Bash(git push origin suvarna/lane/*)" in allow


def test_template_deny_entries_are_only_read_edit_bash_or_mcp_tool_forms():
    """Per the v2.1.239 finding, a Write(...)/Glob(...)/Grep(...)/MultiEdit(...) path rule is dead
    (matches nothing) — every deny entry is either a Read(...)/Edit(...) file rule, a Bash(...) rule,
    or a literal mcp__<server>__<tool> tool-name rule (not a file-glob rule, so the v2.1.239 finding
    does not apply to it)."""
    deny = RS.load_template()["permissions"]["deny"]
    for rule in deny:
        assert (rule.startswith("Read(") or rule.startswith("Edit(") or rule.startswith("Bash(")
                or rule.startswith("mcp__")), f"unexpected deny rule shape: {rule}"
        assert not rule.startswith("Write("), f"dead rule shape: {rule}"
        assert not rule.startswith("Glob("), f"dead rule shape: {rule}"
        assert not rule.startswith("Grep("), f"dead rule shape: {rule}"
        assert not rule.startswith("MultiEdit("), f"dead rule shape: {rule}"
        assert not rule.startswith("NotebookEdit("), f"dead rule shape: {rule}"


def test_template_hooks_pretooluse_runs_hold_guard():
    hooks = RS.load_template()["hooks"]["PreToolUse"]
    commands = [h["command"] for entry in hooks for h in entry["hooks"]]
    assert any("suvarna_tracker.hold_guard" in c for c in commands)


# ---- write_settings / validate_target_path -------------------------------------------------------

def test_validate_target_path_accepts_settings_local_json():
    RS.validate_target_path("/some/dir/.claude/settings.local.json")  # must not raise


@pytest.mark.parametrize("bad_path", [
    "/some/dir/.claude/settings.json",
    "/some/dir/.claude/settings.local.json.bak",
    "/some/dir/settings.local.json.txt",
    "/some/dir/not_settings.local.json.tmp",
])
def test_validate_target_path_refuses_anything_else(bad_path):
    with pytest.raises(RS.RuntimeSettingsError):
        RS.validate_target_path(bad_path)


# ---- CODE-20: also accept $SUVARNA_HOME/config/claude-settings.json ------------------------------

def test_claude_settings_target_path_default(monkeypatch):
    monkeypatch.delenv("SUVARNA_HOME", raising=False)
    assert RS.claude_settings_target_path() == "/Users/Dev/suvarna/config/claude-settings.json"


def test_claude_settings_target_path_reads_suvarna_home_env(monkeypatch):
    monkeypatch.setenv("SUVARNA_HOME", "/tmp/suvarna-test")
    assert RS.claude_settings_target_path() == "/tmp/suvarna-test/config/claude-settings.json"


def test_claude_settings_target_path_explicit_home_overrides_env(monkeypatch):
    monkeypatch.setenv("SUVARNA_HOME", "/tmp/suvarna-env")
    assert RS.claude_settings_target_path(home="/tmp/suvarna-explicit") == "/tmp/suvarna-explicit/config/claude-settings.json"


def test_validate_target_path_accepts_the_exact_claude_settings_path(tmp_path):
    home = str(tmp_path / "suvarna_home")
    target = os.path.join(home, "config", "claude-settings.json")
    RS.validate_target_path(target, home=home)  # must not raise


@pytest.mark.parametrize("bad_path_suffix", [
    "config/claude-settings.json.bak",
    "other/claude-settings.json",
    "config/claude_settings.json",
])
def test_validate_target_path_refuses_near_misses_of_claude_settings_path(tmp_path, bad_path_suffix):
    home = str(tmp_path / "suvarna_home")
    with pytest.raises(RS.RuntimeSettingsError):
        RS.validate_target_path(os.path.join(home, bad_path_suffix), home=home)


def test_write_settings_accepts_claude_settings_json_target(tmp_path):
    home = str(tmp_path / "suvarna_home")
    target = os.path.join(home, "config", "claude-settings.json")
    RS.write_settings(target, home=home)
    assert os.path.exists(target)
    with open(target, encoding="utf-8") as f:
        data = json.load(f)
    assert data["permissions"]["defaultMode"] == "dontAsk"


def test_check_settings_no_drift_against_claude_settings_json_target(tmp_path):
    home = str(tmp_path / "suvarna_home")
    target = os.path.join(home, "config", "claude-settings.json")
    RS.write_settings(target, home=home)
    assert RS.check_settings(target) == []


def test_main_write_accepts_claude_settings_json_target(tmp_path, capsys):
    home = str(tmp_path / "suvarna_home")
    target = os.path.join(home, "config", "claude-settings.json")
    rc = RS.main(["--write", target, "--home", home])
    assert rc == 0
    assert os.path.exists(target)


def test_main_check_against_claude_settings_json_target(tmp_path, capsys):
    home = str(tmp_path / "suvarna_home")
    target = os.path.join(home, "config", "claude-settings.json")
    RS.main(["--write", target, "--home", home])
    rc = RS.main(["--write", target, "--home", home, "--check"])
    assert rc == 0
    assert "ok:" in capsys.readouterr().out


def test_write_settings_creates_valid_parseable_json(tmp_path):
    target = tmp_path / ".claude" / "settings.local.json"
    RS.write_settings(str(target))
    assert target.exists()
    with open(target, encoding="utf-8") as f:
        data = json.load(f)  # must parse
    assert data["permissions"]["defaultMode"] == "dontAsk"


def test_write_settings_refuses_bad_target_and_writes_nothing(tmp_path):
    target = tmp_path / ".claude" / "settings.json"
    with pytest.raises(RS.RuntimeSettingsError):
        RS.write_settings(str(target))
    assert not target.exists()


def test_write_settings_creates_parent_dirs(tmp_path):
    target = tmp_path / "nested" / "dir" / ".claude" / "settings.local.json"
    RS.write_settings(str(target))
    assert target.exists()


def test_write_settings_overwrites_existing_file(tmp_path):
    target = tmp_path / ".claude" / "settings.local.json"
    os.makedirs(target.parent, exist_ok=True)
    target.write_text('{"stale": true}')
    RS.write_settings(str(target))
    with open(target, encoding="utf-8") as f:
        data = json.load(f)
    assert "stale" not in data


# ---- diff_settings / check_settings ---------------------------------------------------------------

def test_diff_settings_empty_when_identical():
    t = RS.load_template()
    assert RS.diff_settings(t, t) == []


def test_diff_settings_reports_changed_value():
    t = RS.load_template()
    actual = json.loads(json.dumps(t))
    actual["permissions"]["defaultMode"] = "bypassPermissions"
    diffs = RS.diff_settings(actual, t)
    assert any("permissions.defaultMode" in d for d in diffs)


def test_diff_settings_reports_missing_key():
    t = RS.load_template()
    actual = json.loads(json.dumps(t))
    del actual["hooks"]
    diffs = RS.diff_settings(actual, t)
    assert any(d.startswith("missing: hooks") for d in diffs)


def test_diff_settings_reports_unexpected_key():
    t = RS.load_template()
    actual = json.loads(json.dumps(t))
    actual["extra_top_level_key"] = True
    diffs = RS.diff_settings(actual, t)
    assert any(d.startswith("unexpected: extra_top_level_key") for d in diffs)


def test_check_settings_missing_file(tmp_path):
    diffs = RS.check_settings(str(tmp_path / "nope" / "settings.local.json"))
    assert diffs and diffs[0].startswith("missing:")


def test_check_settings_no_drift_after_write(tmp_path):
    target = tmp_path / ".claude" / "settings.local.json"
    RS.write_settings(str(target))
    assert RS.check_settings(str(target)) == []


def test_check_settings_reports_drift(tmp_path):
    target = tmp_path / ".claude" / "settings.local.json"
    RS.write_settings(str(target))
    data = json.loads(target.read_text())
    data["permissions"]["allow"].append("Bash(rm -rf /)")
    target.write_text(json.dumps(data))
    diffs = RS.check_settings(str(target))
    assert diffs


def test_check_settings_unreadable_json(tmp_path):
    target = tmp_path / ".claude" / "settings.local.json"
    os.makedirs(target.parent, exist_ok=True)
    target.write_text("{not valid json")
    diffs = RS.check_settings(str(target))
    assert diffs and diffs[0].startswith("unreadable:")


# ---- CLI (main) -------------------------------------------------------------------------------

def test_main_write_exits_0_and_creates_file(tmp_path, capsys):
    target = tmp_path / ".claude" / "settings.local.json"
    rc = RS.main(["--write", str(target)])
    assert rc == 0
    assert target.exists()
    assert "wrote" in capsys.readouterr().out


def test_main_write_bad_path_exits_2(tmp_path, capsys):
    target = tmp_path / ".claude" / "settings.json"
    rc = RS.main(["--write", str(target)])
    assert rc == 2
    assert not target.exists()
    assert "refused" in capsys.readouterr().err


def test_main_check_no_drift_exits_0(tmp_path, capsys):
    target = tmp_path / ".claude" / "settings.local.json"
    RS.main(["--write", str(target)])
    rc = RS.main(["--write", str(target), "--check"])
    assert rc == 0
    assert "ok:" in capsys.readouterr().out


def test_main_check_drift_exits_1(tmp_path, capsys):
    target = tmp_path / ".claude" / "settings.local.json"
    RS.main(["--write", str(target)])
    data = json.loads(target.read_text())
    data["permissions"]["defaultMode"] = "bypassPermissions"
    target.write_text(json.dumps(data))
    rc = RS.main(["--write", str(target), "--check"])
    assert rc == 1
    assert "drift" in capsys.readouterr().err


def test_main_check_missing_file_exits_1(tmp_path, capsys):
    target = tmp_path / ".claude" / "settings.local.json"
    rc = RS.main(["--write", str(target), "--check"])
    assert rc == 1


def test_main_requires_write_argument():
    with pytest.raises(SystemExit):
        RS.main([])
