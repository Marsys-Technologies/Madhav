"""B-0c: kyprobe.py verdicts are earned — each one is shown to flip on a fake harness."""
import json
import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
KYPROBE = FLEET / "kyprobe.py"

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
cfg = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "fake.json")))
a = sys.argv[1:]
if a == ["--version"]:
    print(cfg["version"] + " (Claude Code)"); sys.exit(0)
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "calls.jsonl"), "a") as f:
    f.write(json.dumps({"argv": a, "env_names": sorted(os.environ), "cwd": os.getcwd()}) + "\n")
prompt = sys.stdin.read()
if not cfg["logged_in"]:
    print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                      "result": "Not logged in · Please run /login"}))
    sys.stderr.write("Not logged in\n"); sys.exit(1)
sources = a[a.index("--setting-sources") + 1]
model = a[a.index("--model") + 1]
user = "user" in sources.split(",")
lean = "--disable-slash-commands" in a
def out(ev): print(json.dumps(ev))
skills = [] if lean else ["run-checks"] + (["synced", "superpowers:brainstorming"] if (user or cfg["skills_leak"]) else [])
out({"type": "system", "subtype": "init", "session_id": "sess-1", "model": cfg.get("serve_model") or model,
     "permissionMode": "default", "apiKeySource": "none", "claude_code_version": cfg["version"],
     "tools": ["Read", "Bash"] + cfg["mcp_tools"], "mcp_servers": cfg["mcp_servers"],
     "plugins": [{"name": "cc-plugin-telemetry", "path": "builtin", "source": "cc-plugin-telemetry@builtin"}]
                + ([{"name": "superpowers", "path": "/p", "source": "superpowers@m"}] if (user or cfg["plugins_leak"]) else []),
     "output_style": "default", "memory_paths": {"auto": "/m/"},
     "skills": skills, "slash_commands": skills, "agents": []})
if "Write tool" in prompt:
    if user or cfg["hooks_leak"]:
        out({"type": "system", "subtype": "hook_started", "hook_event": "PreToolUse"})
    if cfg["write_works"] and a[a.index("--permission-mode") + 1] == "acceptEdits":
        open("PROBE_WRITE.txt", "w").write(prompt.split("exactly the text ")[1].split(" ")[0] + "\n")
    text = "DONE"
else:
    footer = None
    if os.path.exists("CLAUDE.md") and cfg["load_project_md"]:
        footer = open("CLAUDE.md").read().strip().splitlines()[-1][:30]
    if cfg["always_footer"]:
        footer = "*CLAUDE.md v9.9 (2030-01-01) —"
    text = (footer or "NO_PROJECT_INSTRUCTIONS") + "\n" + ("/X/Archives" if (user or cfg["load_user_md"]) else "NO_USER_POLICY")
out({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
out({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "rateLimitType": "five_hour",
     "overageStatus": "rejected", "unifiedWindows": {"five_hour": {"utilization": 0.04}, "seven_day": {"utilization": 0.5}}}})
tokens = 20000 - (cfg["lean_saving"] if lean else 0)
out({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "session_id": "sess-1",
     "usage": {"input_tokens": 2, "cache_creation_input_tokens": tokens - 2, "cache_read_input_tokens": 0, "output_tokens": 9},
     "modelUsage": {model: {}}})
'''

FAKE_LAUNCHCTL = r'''#!/usr/bin/env python3
import os, plistlib, subprocess, sys
state = os.path.join(os.path.dirname(os.path.realpath(__file__)), "booted")
cmd = sys.argv[1]
if cmd == "bootstrap":
    pl = plistlib.load(open(sys.argv[3], "rb"))
    open(state, "w").write(pl["Label"])
    env = dict(pl["EnvironmentVariables"]); env["HOME"] = os.environ["HOME"]
    subprocess.run(pl["ProgramArguments"], env=env, stdout=open(pl["StandardOutPath"], "w"),
                   stderr=open(pl["StandardErrorPath"], "w"))
    sys.exit(0)
if cmd == "bootout":
    if os.path.exists(state): os.remove(state)
    sys.exit(0)
if cmd == "print":
    sys.exit(0 if os.path.exists(state) else 113)
sys.exit(64)
'''

DEFAULT = {"version": "2.1.296", "logged_in": True, "load_project_md": True, "load_user_md": False,
           "always_footer": False, "plugins_leak": False, "skills_leak": False, "hooks_leak": False,
           "mcp_servers": [], "mcp_tools": [], "lean_saving": 900, "write_works": True}


@pytest.fixture()
def rig(tmp_path):
    home = tmp_path / "home"
    (home / ".claude" / "skills" / "synced").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text("- Archives worth keeping (e.g. bundles): `/X/Archives/`\n")
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("# rules\n\n§A …\n\n*CLAUDE.md v9.9 (2030-01-01) — test footer.*\n")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, body in (("claude", FAKE_CLAUDE), ("launchctl", FAKE_LAUNCHCTL)):
        p = bindir / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
    mcp = tmp_path / "mcp.none.json"
    mcp.write_text('{"mcpServers":{}}\n')

    def configure(**over):
        (bindir / "fake.json").write_text(json.dumps(dict(DEFAULT, **over)))

    def run(*args, extra_env=None):
        env = {"HOME": str(home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
               "KY_LAUNCHCTL": str(bindir / "launchctl")}
        env.update(extra_env or {})
        return subprocess.run([sys.executable, str(KYPROBE)] + [str(a) for a in args], env=env,
                              capture_output=True, text=True, timeout=120)

    def matrix(context="shell", control=True, extra_env=None):
        out = tmp_path / context
        args = ["matrix", "--context", context, "--out-dir", out, "--project-dir", proj,
                "--claude-bin", bindir / "claude", "--mcp-config", mcp, "--add-dir", tmp_path]
        return run(*(args + (["--with-control"] if control else [])), extra_env=extra_env), out

    def verdicts(control=True):
        r, out = matrix(control=control)
        assert r.returncode == 0, r.stderr
        probes = tmp_path / "PROBES.json"
        r = run("assemble", "--shell-dir", out, "--out", probes)
        assert r.returncode == 0, r.stderr
        return json.loads(probes.read_text())

    configure()
    return type("Rig", (), dict(tmp=tmp_path, proj=proj, bindir=bindir, mcp=mcp, configure=staticmethod(configure),
                                run=staticmethod(run), matrix=staticmethod(matrix), verdicts=staticmethod(verdicts)))


def test_clean_launch_line_earns_every_verdict(rig):
    p = rig.verdicts()
    for model in ("claude-opus-5-5", "claude-sonnet-5-5"):
        v = p["contexts"]["shell"][model]
        assert v["sign_in"] == "works" and v["model_served"] is True
        assert v["project_claude_md_in_context"] is True and v["project_claude_md_negative_control"] is False
        assert v["user_claude_md_in_context"] is False
        assert v["mcp_servers_active"] == "none"
        assert v["user_plugins_active"] == "none" and v["user_skills_active"] == "none"
        assert v["user_hooks_active"] == "none" and v["tool_probe_write_landed"] is True
        assert v["builtin_plugins_observed"] == ["cc-plugin-telemetry"] and v["output_style_observed"] == "default"
        assert v["rate_limit_observed"]["utilization"] == {"five_hour": 0.04, "seven_day": 0.5}
        assert v["fixed_input_tokens_empty_dir"] == 20000 and v["fixed_input_tokens_lean"] == 19100
    assert p["extra_lean_flags"]["chosen"] == ["--disable-slash-commands"]
    assert p["contexts"]["launchd"] == "unknown"  # not run → unknown, never assumed
    calls = [json.loads(l) for l in (rig.bindir / "calls.jsonl").read_text().splitlines()]
    assert calls and all("--bare" not in c["argv"] and "--strict-mcp-config" in c["argv"]
                         and "--permission-mode" in c["argv"] for c in calls)
    assert sum(c["argv"][c["argv"].index("--setting-sources") + 1] != "project" for c in calls) == 1  # the control only
    assert all(set(c["env_names"]) <= {"HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "__CF_USER_TEXT_ENCODING"} for c in calls)


def test_not_signed_in_is_fails_and_everything_else_unknown(rig):
    rig.configure(logged_in=False)
    v = rig.verdicts()["contexts"]["shell"]["claude-opus-5-5"]
    assert v["sign_in"] == "fails"
    assert v["project_claude_md_in_context"] == "unknown" and v["user_hooks_active"] == "unknown"
    assert v["fixed_input_tokens_empty_dir"] == "unknown"


def test_project_instructions_absent_reads_false(rig):
    rig.configure(load_project_md=False)
    assert rig.verdicts()["contexts"]["shell"]["claude-opus-5-5"]["project_claude_md_in_context"] is False


def test_dirty_negative_control_voids_the_positive(rig):
    rig.configure(always_footer=True)
    v = rig.verdicts()["contexts"]["shell"]["claude-opus-5-5"]
    assert v["project_claude_md_negative_control"] is True and v["project_claude_md_in_context"] == "unknown"


def test_user_level_leaks_are_named(rig):
    rig.configure(plugins_leak=True, skills_leak=True, hooks_leak=True, load_user_md=True,
                  mcp_servers=[{"name": "github"}], mcp_tools=["mcp__github__x"])
    v = rig.verdicts()["contexts"]["shell"]["claude-sonnet-5-5"]
    assert v["user_plugins_active"] == ["superpowers"]
    assert v["user_skills_active"] == ["superpowers:brainstorming", "synced"]
    assert v["user_hooks_active"] == ["PreToolUse"]
    assert v["user_claude_md_in_context"] is True
    assert v["mcp_servers_active"] == ["github", "mcp__github__x"]


def test_without_a_control_absence_proves_nothing(rig):
    v = rig.verdicts(control=False)["contexts"]["shell"]["claude-opus-5-5"]
    assert v["user_plugins_active"] == "unknown" and v["user_skills_active"] == "unknown"
    assert v["user_hooks_active"] == "unknown"
    assert v["sign_in"] == "works" and v["mcp_servers_active"] == "none"


def test_hook_verdict_needs_the_write_to_land(rig):
    rig.configure(write_works=False)
    v = rig.verdicts()["contexts"]["shell"]["claude-opus-5-5"]
    assert v["tool_probe_write_landed"] is False and v["user_hooks_active"] == "unknown"


def test_wrong_model_served_reads_false(rig):
    rig.configure(serve_model="claude-haiku-5-5")
    assert rig.verdicts()["contexts"]["shell"]["claude-opus-5-5"]["model_served"] is False


def test_lean_flag_needs_a_measured_saving(rig):
    rig.configure(lean_saving=100)
    p = rig.verdicts()
    assert p["extra_lean_flags"]["chosen"] == []
    assert p["extra_lean_flags"]["basis"]["claude-opus-5-5"]["saving_tokens"] == 100


def test_refuses_old_program_and_credential_names(rig):
    rig.configure(version="2.1.239")
    r, _ = rig.matrix()
    assert r.returncode == 70 and "below" in r.stderr
    rig.configure()
    r, _ = rig.matrix(extra_env={"KY_DATABASE_URL": "x"})
    assert r.returncode == 78 and "KY_DATABASE_URL" in r.stderr and "=x" not in r.stderr


def test_launchd_one_shot_is_linted_run_and_removed(rig):
    out = rig.tmp / "launchd"
    r = rig.run("launchd", "--out-dir", out, "--project-dir", rig.proj, "--claude-bin", rig.bindir / "claude",
                "--mcp-config", rig.mcp, "--add-dir", rig.tmp, "--wait", "60", "--poll", "0.1")
    assert r.returncode == 0, r.stderr + (out / "launchd.err").read_text()
    receipt = json.loads((out / "LAUNCHD_RECEIPT.json").read_text())
    assert receipt["finished"] is True and receipt["absent_after_bootout"] is True
    pl = plistlib.load(open(out / "in.marsys.kalayantra.probe.plist", "rb"))
    assert "KeepAlive" not in pl and set(pl["EnvironmentVariables"]) == {"PATH", "HOME", "USER", "LANG"}
    probes = rig.tmp / "PROBES.json"
    assert rig.run("assemble", "--launchd-dir", out, "--out", probes).returncode == 0
    v = json.loads(probes.read_text())["contexts"]["launchd"]["claude-opus-5-5"]
    assert v["sign_in"] == "works" and v["project_claude_md_in_context"] is True
    assert v["user_hooks_active"] == "unknown"  # no control in this assembly
    assert rig.run("launchd", "--out-dir", out, "--project-dir", rig.proj).returncode == 73  # no silent re-run
