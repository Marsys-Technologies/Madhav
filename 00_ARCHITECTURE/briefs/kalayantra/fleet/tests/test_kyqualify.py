"""B-0c: kyqualify.py (plan v2.7 §7 launch qualification, KV-06) — every check and every negative probe is shown
to flip on a fake `claude` and a fake `launchctl` (root CLAUDE.md §N.8: a verdict nothing could turn false is null).
The real program and the real launchd are never called here."""
import copy
import hashlib
import json
import os
import plistlib
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
KYQUALIFY = FLEET / "kyqualify.py"
SCHEMAS = FLEET / "schemas"
TEMPLATES = FLEET / "templates"
sys.path.insert(0, str(FLEET))

import kyqualify  # noqa: E402
import kyschema  # noqa: E402

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, re, signal, subprocess, sys, time
here = os.path.dirname(os.path.realpath(__file__))
cfg = json.load(open(os.path.join(here, "fake.json")))
a = sys.argv[1:]
if a == ["--version"]:
    print(cfg["version"]); sys.exit(0)
def opt(name):
    return a[a.index(name) + 1]
def multi(name):
    got = []
    if name in a:
        for x in a[a.index(name) + 1:]:
            if x.startswith("--"):
                break
            got.append(x)
    return got
prompt = sys.stdin.read()
m = re.match(r"Use the (\w+) tool", prompt)
kind = "sleep" if "sleep 600" in prompt else m.group(1).lower() if m else "ctx" if "lettered sections" in prompt else "ready"
with open(os.path.join(here, "calls.jsonl"), "a") as f:
    f.write(json.dumps({"argv": a, "kind": kind, "env_names": sorted(os.environ), "cwd": os.getcwd(),
                        "home": os.environ.get("HOME"), "path": os.environ.get("PATH"),
                        "tmpdir": os.environ.get("TMPDIR"), "ky_root": os.environ.get("KY_ROOT")}) + "\n")
def out(ev):
    sys.stdout.write(json.dumps(ev) + "\n"); sys.stdout.flush()
def spawn_sleep():
    child = subprocess.Popen(["/bin/sleep", "600"], start_new_session=cfg["detach_sleep"])   # same group unless detached
    with open(os.path.join(here, "sleep_pids"), "a") as f:
        f.write("%d\n" % child.pid)
    return child
if kind in cfg["hang_on"]:                                    # a run that never answers (an unanswered prompt)
    spawn_sleep(); time.sleep(600)
try:
    json.load(open(opt("--mcp-config")))
except ValueError:
    if not cfg["accept_invalid_mcp"]:
        sys.stderr.write("Error: Invalid MCP configuration\n"); sys.exit(1)
signed = cfg["logged_in"] and (cfg["auth_ignores_home"] or os.path.exists(
    os.path.join(os.environ.get("HOME", "/nonexistent"), ".claude", "signed_in")))
if not signed or (kind == "ready" and cfg["ready_fails"]):
    out({"type": "result", "subtype": "error_during_execution", "is_error": True, "result": "Not logged in · Please run /login"})
    sys.stderr.write("Not logged in\n"); sys.exit(1)
user = "user" in opt("--setting-sources").split(",")
mode, model, disallowed = opt("--permission-mode"), opt("--model"), multi("--disallowedTools")
served = cfg["serve_model"] or model
offered = [t for t in cfg["tools"] if not (t in disallowed and cfg["disallow_mode"] == "not_offered")]
allow_rules = [r for flag in a if flag.startswith("--allowedTools=") for r in flag.split("=", 1)[1].split(",")]
skills = ["run-checks"] + (["synced", "superpowers:brainstorming"] if (user or cfg["skills_leak"]) else [])
out({"type": "system", "subtype": "init", "session_id": "sess-1", "model": served,
     "permissionMode": cfg["serve_permission_mode"] or mode, "apiKeySource": cfg["api_key_source"],
     "claude_code_version": "2.1.296", "tools": offered + cfg["mcp_tools"], "mcp_servers": cfg["mcp_servers"],
     "plugins": [{"name": "cc-plugin-telemetry", "path": "builtin", "source": "cc-plugin-telemetry@builtin"}]
                + ([{"name": "superpowers", "path": "/p", "source": "superpowers@m"}] if (user or cfg["plugins_leak"]) else []),
     "output_style": "default", "memory_paths": {"auto": "/m/"}, "skills": skills, "slash_commands": skills, "agents": []})
if cfg["session_hook"] and "--include-hook-events" in a and (user or cfg["hooks_leak"]):
    out({"type": "system", "subtype": "hook_started", "hook_name": "SessionStart:startup", "hook_event": "SessionStart"})
denials, turns = [], [1]
def allowed(tool, inp):
    if tool in cfg["deny_tools"] or tool in disallowed:
        return False
    if mode == "bypassPermissions" or tool == "Read" or (mode == "acceptEdits" and tool in ("Write", "Edit")):
        return True
    return tool == "Bash" and any(r.startswith("Bash(") and r.endswith(":*)") and inp["command"].startswith(r[5:-3])
                                  for r in allow_rules)             # an --allowedTools rule covers this command
def use(tool, inp, effect):
    if tool not in offered:
        if cfg["deny_leaks"]:
            effect()                                          # a model that works around the missing tool
        return False
    turns[0] += 1
    tid = "toolu_%d" % turns[0]
    out({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": tool, "input": inp}]}})
    if tool in ("Write", "Edit") and "--include-hook-events" in a and (user or cfg["hooks_leak"]):
        out({"type": "system", "subtype": "hook_started", "hook_name": "PreToolUse:" + tool, "hook_event": "PreToolUse"})
    ok = allowed(tool, inp)
    if ok or cfg["deny_leaks"]:
        effect()
    block = {"type": "tool_result", "tool_use_id": tid, "content": "ok" if ok else "permission denied"}
    if not ok:
        denials.append({"tool_name": tool, "tool_use_id": tid, "tool_input": inp})
        block["is_error"] = True
    out({"type": "user", "message": {"content": [block]}})
    return ok
text = "REFUSED"
if kind == "sleep":
    if not cfg["ignore_sleep"]:
        if cfg["trap_term"]:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)     # inherited by the sleep: only KILL ends the group
        out({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_s", "name": "Bash",
                                                            "input": {"command": "sleep 600"}}]}})
        spawn_sleep().wait()
        time.sleep(600 if cfg["trap_term"] else 0)
    text = "1\n2\n3"
elif kind == "ctx":
    if cfg["touch_on_ctx"]:
        open(cfg["touch_on_ctx"], "a").write("changed while qualifying\n")
    footer = None
    if os.path.exists("CLAUDE.md") and cfg["load_project_md"]:
        footer = open("CLAUDE.md").read().strip().splitlines()[-1][:30]
    if cfg["always_footer"]:
        footer = "*CLAUDE.md v9.9 (2030-01-01) —"
    text = (footer or "NO_PROJECT_INSTRUCTIONS") + "\n" + ("/X/Archives" if user else "NO_USER_POLICY")
elif kind == "read":
    name, box = re.search(r"read the file (\S+) in", prompt).group(1), []
    use("Read", {"file_path": name}, lambda: box.append(open(name).read().strip()))
    text = box[0] if box else "REFUSED"
elif kind == "write" and cfg["lean_hook_run_idle"] and not user and "--include-hook-events" in a:
    text = "REFUSED"                                          # the model attempts nothing in the hook-detection run
elif kind == "write":
    name = re.search(r"create the file (\S+) in", prompt).group(1)
    nonce = re.search(r"exactly the text (\S+) and", prompt).group(1)
    def effect():
        if cfg["write_works"]:
            open(name, "w").write(nonce + "\n")
    text = "DONE" if use("Write", {"file_path": name, "content": nonce}, effect) else "REFUSED"
elif kind == "edit":
    name, old, new = re.search(r"on the file (\S+) in .*replace the text (\S+) with exactly the text (\S+),", prompt, re.S).groups()
    def effect():
        body = open(name).read()
        open(name, "w").write(body.replace(old, new))
    text = "DONE" if use("Edit", {"file_path": name, "old_string": old, "new_string": new}, effect) else "REFUSED"
elif kind == "bash" and "shasum -a 256" in prompt:
    name, box = re.search(r"shasum -a 256 (\S+)", prompt).group(1), []
    def effect():
        import hashlib
        box.append("0" * 64 if cfg["bash_digest_wrong"] else hashlib.sha256(open(name, "rb").read()).hexdigest())
        if cfg["bash_touches_disk"]:
            open("SIDE_EFFECT.txt", "w").write("x")
    use("Bash", {"command": "shasum -a 256 " + name}, effect)
    text = box[0] if box else "REFUSED"
elif kind == "bash":
    mm = re.search(r"printf %s (\S+) > (\S+)", prompt)
    def effect():
        open(mm.group(2), "w").write(mm.group(1))
    text = "DONE" if use("Bash", {"command": mm.group(0)}, effect) else "REFUSED"
else:
    text = "READY"
out({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
out({"type": "result", "subtype": "success", "is_error": False,
     "num_turns": cfg["ctx_turns"] if kind == "ctx" else turns[0], "session_id": "sess-1",
     "usage": {"input_tokens": 2, "cache_creation_input_tokens": 19998, "cache_read_input_tokens": 0, "output_tokens": 9},
     "modelUsage": {served: {}}, "permission_denials": denials})
'''

FAKE_LAUNCHCTL = r'''#!/usr/bin/env python3
import json, os, plistlib, subprocess, sys, time
here = os.path.dirname(os.path.realpath(__file__))
state = os.path.join(here, "booted")
try:
    mode = json.load(open(os.path.join(here, "launchctl.json")))
except OSError:
    mode = {}
with open(os.path.join(here, "launchctl_calls.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
cmd = sys.argv[1]
if cmd == "bootstrap":
    if mode.get("bootstrap_fails"):
        sys.stderr.write("Bootstrap failed: 5: Input/output error\n"); sys.exit(5)
    pl = plistlib.load(open(sys.argv[3], "rb"))
    open(state, "w").write(pl["Label"])
    if mode.get("never_starts"):                 # loaded, but the program never runs
        sys.exit(0)
    if mode.get("dies"):                         # the agent started and was killed before it could say anything
        gone = subprocess.Popen(["/usr/bin/true"]); gone.wait()
        evidence = pl["ProgramArguments"][pl["ProgramArguments"].index("--evidence-dir") + 1]
        json.dump({"pid": gone.pid}, open(os.path.join(evidence, "launchd", "INNER_STARTED.json"), "w"))
        sys.exit(0)
    env = dict(pl["EnvironmentVariables"])
    env["XPC_SERVICE_NAME"] = mode.get("xpc_service_name", pl["Label"])
    args = pl["ProgramArguments"]
    if mode.get("direct"):                       # NOT launchd: the job stays this program's own child
        subprocess.run(args, env=env, cwd="/", stdout=open(pl["StandardOutPath"], "w"),
                       stderr=open(pl["StandardErrorPath"], "w"))
        sys.exit(0)
    pid = os.fork()                              # like launchd: the job is nobody's child but PID 1's
    if pid == 0:
        os.setsid()
        if os.fork() > 0:
            os._exit(0)
        end = time.time() + 5
        while os.getppid() != 1 and time.time() < end:
            time.sleep(0.005)
        os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
        os.dup2(os.open(pl["StandardOutPath"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644), 1)
        os.dup2(os.open(pl["StandardErrorPath"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644), 2)
        os.chdir("/")
        os.execve(args[0], args, env)
    os.waitpid(pid, 0)
    sys.exit(0)
if cmd == "bootout":
    if os.path.exists(state) and not mode.get("sticky"):
        os.remove(state)
    sys.exit(0)
if cmd == "print":
    sys.exit(0 if os.path.exists(state) and not mode.get("never_listed") else 113)
sys.exit(64)
'''

DEFAULT = {"version": "2.1.296 (Claude Code)", "logged_in": True, "auth_ignores_home": False,
           "accept_invalid_mcp": False, "api_key_source": "none", "load_project_md": True, "always_footer": False,
           "plugins_leak": False, "skills_leak": False, "hooks_leak": False, "mcp_servers": [], "mcp_tools": [],
           "write_works": True, "deny_tools": [], "deny_leaks": False, "disallow_mode": "not_offered",
           "ignore_sleep": False, "trap_term": False, "detach_sleep": False, "ready_fails": False,
           "hang_on": [], "serve_model": None, "serve_permission_mode": None, "lean_hook_run_idle": False,
           "touch_on_ctx": None, "ctx_turns": 1, "session_hook": False, "bash_digest_wrong": False,
           "bash_touches_disk": False,
           # init.tools of the real program on the campaign host (2.1.296); the subagent tool is "Task"
           "tools": ["Task", "Bash", "CronCreate", "CronDelete", "CronList", "DesignSync", "Edit", "EnterWorktree",
                     "ExitWorktree", "ListAgents", "Monitor", "NotebookEdit", "PushNotification", "Read",
                     "RemoteTrigger", "ReportFindings", "ScheduleWakeup", "SendMessage", "Skill", "TaskStop",
                     "ToolSearch", "WebFetch", "WebSearch", "Workflow", "Write"]}
REAL_TOOLS = sorted(DEFAULT["tools"])
ENV_NAMES = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "KY_ROOT", "KY_RUN", "KY_FLEET"]
BOOT_ENV = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_ITEM", "KY_PY"]
BUILDER_OFF = ["Task", "Workflow", "CronCreate", "CronDelete", "RemoteTrigger", "ScheduleWakeup", "PushNotification",
               "SendMessage", "EnterWorktree", "ExitWorktree", "WebFetch", "WebSearch", "DesignSync"]
REVIEWER_OFF = ["Edit", "Write", "NotebookEdit"] + BUILDER_OFF + ["Skill"]
ALLOW = ("--allowedTools=Bash(shasum:*),Bash(wc:*),Bash(ls:*),Bash(plutil:*),Bash(python3:*),Bash(git show:*),"
         "Bash(git diff:*),Bash(git log:*),Bash(git status:*)")
REVIEWER = {"role": "bootstrap-reviewer", "permission_mode": "default", "max_turns": 60, "deadline_seconds": 3600,
            "env_names": BOOT_ENV, "disallowed_tools": REVIEWER_OFF, "extra_flags": [ALLOW],
            "intended_tools": ["Read", "Bash"], "bash_canary": "readonly", "denied_tools": ["Write", "Edit"]}
USER_HOOKS = {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": "echo s3cr3t-hook-command"}]}],
              "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "true"}]},
                              {"matcher": "Write", "hooks": [{"type": "command", "command": "true"}]}]}
REQUIRED = ["sign_in", "model_identity", "permission_mode_observed", "intended_tools", "no_tty_prompt",
            "project_claude_md_visible", "excluded_user_plugins", "excluded_user_skills", "excluded_user_hooks",
            "mcp_none"]
PASS, FAIL, UNKNOWN = 0, 1, 3      # kyqualify.py qualify exit codes when a receipt is written


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def results(receipt, part="checks"):
    return {name: entry["result"] for name, entry in receipt[part].items()}


def make_rig(tmp):
    home = tmp / "home"
    (home / ".claude" / "skills" / "synced").mkdir(parents=True)
    (home / ".claude" / "signed_in").write_text("fake sign-in marker; not a credential\n")
    (home / ".claude" / "CLAUDE.md").write_text("- Archives worth keeping (e.g. bundles): `/X/Archives/`\n")
    proj = tmp / "proj"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("# rules\n\n§A …\n\n*CLAUDE.md v9.9 (2030-01-01) — test footer.*\n")
    root = tmp / "ky"
    (root / "bin").mkdir(parents=True)
    bindir = tmp / "bin"
    bindir.mkdir()
    for name, body in (("claude", FAKE_CLAUDE), ("launchctl", FAKE_LAUNCHCTL)):
        p = bindir / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
    mcp = tmp / "mcp.none.json"
    mcp.write_text('{"mcpServers":{}}\n')
    card = tmp / "CARD.md"
    card.write_text("# role card\n")
    counter = [0]

    def configure(**over):
        (bindir / "fake.json").write_text(json.dumps(dict(DEFAULT, **over)))

    def launchctl(**mode):
        (bindir / "launchctl.json").write_text(json.dumps(mode))

    def user_settings(hooks=None, raw=None):
        """the user's ~/.claude/settings.json: hooks plus keys the harness must never read out"""
        doc = {"env": {"SOME_TOKEN": "s3cr3t-env-value"}, "permissions": {"defaultMode": "bypassPermissions"}}
        if hooks is not None:
            doc["hooks"] = hooks
        (home / ".claude" / "settings.json").write_text(raw if raw is not None else json.dumps(doc))

    def doc(**over):
        base = {"schema": "ky.launch_config/1", "role": "bootstrap-builder", "model": "claude-opus-5-5",
                "effort": "high", "permission_mode": "bypassPermissions", "max_turns": 150,
                "deadline_seconds": 14400, "worktree": str(proj), "claude_bin": str(bindir / "claude"),
                "mcp_config": str(mcp), "prompt_path": str(card), "env_names": list(ENV_NAMES),
                "child_path": "%s/bin:/opt/homebrew/bin:/usr/bin:/bin" % root, "extra_flags": [],
                "disallowed_tools": [], "add_dirs": [str(root)],
                "intended_tools": ["Read", "Write", "Edit", "Bash"], "denied_tools": []}
        base.update(over)
        return base

    def config(name=None, **over):
        counter[0] += 1
        path = tmp / (name or "config-%d.json" % counter[0])
        path.write_text(json.dumps(doc(**over), indent=1))
        return path

    def run(*args, extra_env=None):
        env = {"HOME": str(home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
               "KY_LAUNCHCTL": str(bindir / "launchctl"), "KY_ROOT": str(root)}
        env.update(extra_env or {})
        return subprocess.run([sys.executable, str(KYQUALIFY)] + [str(a) for a in args], env=env,
                              capture_output=True, text=True, timeout=120)

    def qualify(cfg=None, context="shell", control=True, extra_env=None, args=(), out=None, evidence=None):
        counter[0] += 1
        cfg = cfg or config()
        evidence = evidence or tmp / ("evidence-%d" % counter[0])
        out = out or tmp / ("receipt-%d.json" % counter[0])
        argv = ["qualify", "--config", cfg, "--context", context, "--evidence-dir", evidence, "--out", out,
                "--run-timeout", "30", "--probe-timeout", "0.3", "--term-grace", "2", "--parallel", "16",
                "--wait", "60", "--poll", "0.05"] + (["--control"] if control else []) + list(args)
        r = run(*argv, extra_env=extra_env)
        receipt = json.loads(out.read_text()) if out.exists() else None
        return r, receipt, evidence

    def calls():
        path = bindir / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def sleep_pids():
        path = bindir / "sleep_pids"
        return [int(line) for line in path.read_text().split()] if path.exists() else []

    configure()
    return type("Rig", (), dict(tmp=tmp, home=home, proj=proj, root=root, bindir=bindir, mcp=mcp, card=card,
                                configure=staticmethod(configure), launchctl=staticmethod(launchctl),
                                user_settings=staticmethod(user_settings),
                                doc=staticmethod(doc), config=staticmethod(config), run=staticmethod(run),
                                qualify=staticmethod(qualify), calls=staticmethod(calls),
                                sleep_pids=staticmethod(sleep_pids)))


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    out = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return bool(out) and not out.startswith("Z")


@pytest.fixture()
def rig(tmp_path):
    return make_rig(tmp_path)


@pytest.fixture(scope="module")
def clean(tmp_path_factory):
    """one clean builder-shaped qualification, shared by the tests that only read it"""
    r = make_rig(tmp_path_factory.mktemp("clean"))
    r.cfg = r.config("builder.json")
    r.done, r.receipt, r.evidence = r.qualify(r.cfg, out=r.tmp / "receipt.json", args=("--probe-timeout", "0.8"))
    r.out = r.tmp / "receipt.json"
    return r


# ---------------------------------------------------------------------------------------------- the clean run

def test_clean_configuration_earns_pass_with_every_detector_exercised(clean):
    rc = clean.receipt
    assert clean.done.returncode == PASS, clean.done.stderr
    assert rc["schema"] == "ky.qualification/1" and rc["result"] == "PASS"
    assert (rc["role"], rc["model"], rc["context"], rc["launchd_receipt"]) == \
        ("bootstrap-builder", "claude-opus-5-5", "shell", None)
    want = dict({name: "pass" for name in REQUIRED}, input_overhead_worktree="pass", denied_tools="unknown")
    assert results(rc) == want
    assert all(rc["checks"][name]["required"] for name in REQUIRED)
    assert rc["checks"]["denied_tools"]["required"] is False and rc["checks"]["input_overhead_worktree"]["required"] is False
    assert rc["checks"]["input_overhead_worktree"]["observed"] == 20000
    assert set(rc["checks"]["intended_tools"]["observed"]["tools"]) == {"Read", "Write", "Edit", "Bash"}
    assert rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]["canary"] == "write"
    assert rc["offered_tools"] == REAL_TOOLS                    # what the program itself listed in the base run
    assert rc["checks"]["excluded_user_hooks"]["observed"]["basis"] == "canary_and_control"
    assert results(rc, "negative_probes") == {
        "missing_authentication": "pass", "inaccessible_keychain": "not_simulated", "denied_tools": "not_simulated",
        "invalid_settings": "pass", "timeout": "pass", "termination": "pass", "restart": "pass"}
    assert all(p["why"] for p in rc["negative_probes"].values() if p["result"] == "not_simulated")
    assert json.loads(clean.done.stdout)["result"] == "PASS"


def test_binds_are_the_plan_launch_line_and_the_files_on_disk(clean):
    b = clean.receipt["binds"]
    claude, root = str(clean.bindir / "claude"), str(clean.root)
    assert b["argv"] == [claude, "-p", "--setting-sources", "project", "--permission-mode", "bypassPermissions",
                         "--model", "claude-opus-5-5", "--effort", "high", "--max-turns", "150",
                         "--strict-mcp-config", "--mcp-config", str(clean.mcp),
                         "--output-format", "stream-json", "--verbose", "--add-dir", root]
    assert b["claude_bin"] == claude and b["claude_bin_sha256"] == sha(os.path.realpath(claude))
    assert b["claude_version"] == "2.1.296" and b["prompt_sha256"] == sha(clean.card)
    assert b["mcp_config_sha256"] == sha(clean.mcp) and b["env_names"] == sorted(ENV_NAMES)
    assert (b["model"], b["effort"], b["permission_mode"], b["max_turns"], b["deadline_seconds"]) == \
        ("claude-opus-5-5", "high", "bypassPermissions", 150, 14400)
    assert b["worktree"] == str(clean.proj) and b["child_path"] == "%s/bin:/opt/homebrew/bin:/usr/bin:/bin" % root
    assert b["add_dirs"] == [root] and "extra_flags" not in b and "disallowed_tools" not in b


def test_every_run_used_the_bound_argv_and_the_exact_environment(clean):
    bound, calls = clean.receipt["binds"]["argv"][1:], clean.calls()
    assert len(calls) == 13     # base, empty, 4 tools, hooks, control, 4 negative runs, restart
    hook_runs = control_runs = other_mcp = 0
    for c in calls:
        argv = list(c["argv"])
        if argv[-1] == "--include-hook-events":                       # the only flag ever appended
            argv, hook_runs = argv[:-1], hook_runs + 1
        i = argv.index("--setting-sources") + 1
        if argv[i] != "project":
            assert argv[i] == "user,project" and c["argv"][-1] == "--include-hook-events"
            argv[i], control_runs = "project", control_runs + 1
        j = argv.index("--mcp-config") + 1
        if argv[j] != str(clean.mcp):
            argv[j], other_mcp = str(clean.mcp), other_mcp + 1
        assert argv == bound
        assert set(c["env_names"]) - {"__CF_USER_TEXT_ENCODING"} == set(ENV_NAMES)
        assert c["path"] == clean.receipt["binds"]["child_path"] and c["ky_root"] == str(clean.root)
        assert c["tmpdir"].startswith(str(clean.evidence) + "/runs/") and c["tmpdir"].endswith("/tmp")
    assert (hook_runs, control_runs, other_mcp) == (2, 1, 1)
    foreign_home = [c for c in calls if c["home"] != str(clean.home)]
    assert len(foreign_home) == 1 and os.listdir(foreign_home[0]["home"]) == []      # missing-authentication probe
    in_worktree = sorted(c["kind"] for c in calls if c["cwd"] == str(clean.proj))
    assert in_worktree == ["ctx", "ready", "sleep"]                 # base, the terminated run and its restart
    assert all(c["cwd"].startswith(str(clean.evidence) + "/canary/") for c in calls if c["cwd"] != str(clean.proj))
    hooks = clean.receipt["checks"]["excluded_user_hooks"]["observed"]
    assert hooks["argv_difference"]["lean"] == ["appended --include-hook-events"]
    assert "--setting-sources project -> user,project" in hooks["argv_difference"]["control"]


def test_evidence_is_hashed_and_the_receipt_matches_its_schema(clean):
    ev = clean.receipt["evidence"]
    assert ev["dir"] == str(clean.evidence) and "runs/base/stdout.jsonl" in ev["files"]
    assert "launch_config.json" in ev["files"] and len(ev["files"]) >= 4 * 13
    for rel, digest in ev["files"].items():
        assert sha(clean.evidence / rel) == digest, rel
    for entry in clean.receipt["checks"].values():
        assert all(rel in ev["files"] for rel in entry["evidence"])
    schema = json.loads((SCHEMAS / "qualification.json").read_text())
    assert kyschema.validate(schema, clean.receipt) == []
    broken = copy.deepcopy(clean.receipt)
    broken["checks"]["sign_in"]["result"] = "PASSED"
    del broken["binds"]["argv"]
    assert len(kyschema.validate(schema, broken)) == 2


# ---------------------------------------------------------------------------------- each check, shown flipping

def test_not_signed_in_fails(rig):
    rig.configure(logged_in=False)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["checks"]["sign_in"]["result"] == "fail"
    assert rc["checks"]["intended_tools"]["result"] == "fail"           # nothing landed
    assert rc["checks"]["model_identity"]["result"] == "unknown"        # never observed, never assumed
    assert rc["checks"]["excluded_user_plugins"]["result"] == "unknown"
    assert rc["checks"]["input_overhead_worktree"]["observed"] == "unknown"


def test_sign_in_through_an_api_key_fails(rig):
    rig.configure(api_key_source="ANTHROPIC_API_KEY")
    r, rc, _ = rig.qualify()
    assert rc["result"] == "FAIL" and rc["checks"]["sign_in"]["result"] == "fail"
    assert {n: v for n, v in results(rc).items() if v == "fail"} == {"sign_in": "fail"}


def test_wrong_model_served_fails(rig):
    rig.configure(serve_model="claude-haiku-5-5", ctx_turns=2)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert {n: v for n, v in results(rc).items() if v != "pass"} == {
        "model_identity": "fail", "denied_tools": "unknown", "input_overhead_worktree": "unknown"}
    assert rc["checks"]["model_identity"]["observed"]["init_model"] == "claude-haiku-5-5"
    # a base run of more than one turn is not a clean measure of the fixed overhead: unknown, never a number
    assert rc["checks"]["input_overhead_worktree"]["observed"] == "unknown"


def test_permission_mode_and_mcp_are_observed_not_assumed(rig):
    rig.configure(serve_permission_mode="default", mcp_servers=[{"name": "github"}], mcp_tools=["mcp__github__x"])
    r, rc, _ = rig.qualify()
    assert rc["result"] == "FAIL"
    assert {n for n, v in results(rc).items() if v == "fail"} == {"permission_mode_observed", "mcp_none"}
    assert rc["checks"]["permission_mode_observed"]["observed"] == {"configured": "bypassPermissions", "observed": "default"}
    assert rc["checks"]["mcp_none"]["observed"] == {"mcp_servers": ["github"], "mcp_tools": ["mcp__github__x"]}


def test_an_intended_tool_that_is_denied_fails(rig):
    rig.configure(deny_tools=["Bash"])
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    tools = rc["checks"]["intended_tools"]["observed"]["tools"]
    assert {t: v["result"] for t, v in tools.items()} == {"Read": "pass", "Write": "pass", "Edit": "pass", "Bash": "fail"}
    assert tools["Bash"]["permission_denials"] == ["Bash"] and tools["Bash"]["effect"] is False
    assert {n for n, v in results(rc).items() if v == "fail"} == {"intended_tools"}
    rig.configure(deny_tools=["Bash"], deny_leaks=True)     # the effect lands, yet the call ended in a denial
    r, rc, _ = rig.qualify()
    bash = rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]
    assert rc["result"] == "FAIL" and bash["result"] == "fail" and bash["effect"] is True and "denial" in bash["why"]


def test_an_intended_tool_without_an_effect_fails(rig):
    rig.configure(write_works=False)        # the tool call "succeeds" but nothing lands on disk
    r, rc, _ = rig.qualify()
    tools = rc["checks"]["intended_tools"]["observed"]["tools"]
    assert rc["result"] == "FAIL" and tools["Write"]["result"] == "fail" and tools["Write"]["tool_use_observed"] is True
    assert {n for n, v in results(rc).items() if v == "fail"} == {"intended_tools"}
    assert rc["checks"]["excluded_user_hooks"]["result"] == "pass"      # a hook fires on the attempt, landed or not


@pytest.mark.parametrize("mode", ["not_offered", "deny_on_call"])
def test_denied_tools_need_no_effect_and_an_observed_denial(rig, mode):
    rig.configure(disallow_mode=mode)
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    denied = rc["checks"]["denied_tools"]
    assert denied["required"] is True and denied["result"] == "pass"
    assert rc["negative_probes"]["denied_tools"]["result"] == "pass"
    seen = {t: v["denial"] for t, v in denied["observed"]["tools"].items()}
    if mode == "not_offered":
        # The tool is absent from the harness's own tool list, so no Write can be attempted and the user's
        # Edit|Write hooks cannot be shown firing even in the control: exclusion is not observable → unknown.
        assert seen == {"Write": ["not_offered"], "Edit": ["not_offered"]}
        assert rc["checks"]["excluded_user_hooks"]["result"] == "unknown"
        assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    else:
        assert seen == {"Write": ["permission_denial", "tool_result_error"], "Edit": ["permission_denial", "tool_result_error"]}
        assert rc["checks"]["excluded_user_hooks"]["result"] == "pass"   # the attempt fires the control's hook
        assert r.returncode == PASS and rc["result"] == "PASS"
    assert rc["binds"]["disallowed_tools"] == REVIEWER_OFF and rc["binds"]["extra_flags"] == [ALLOW]
    # an observation, not a verdict: bare disallowed names the program still lists
    assert denied["observed"]["disallowed_tools_still_offered"] == ([] if mode == "not_offered" else sorted(REVIEWER_OFF))
    assert rc["offered_tools"] == [t for t in REAL_TOOLS if mode == "deny_on_call" or t not in REVIEWER_OFF]
    argv = rc["binds"]["argv"]
    assert argv[10:16] == ["--max-turns", "60", ALLOW, "--strict-mcp-config", "--mcp-config", str(rig.mcp)]
    assert argv.count(ALLOW) == 1 and argv[16:17 + len(REVIEWER_OFF)] == ["--disallowedTools"] + REVIEWER_OFF
    assert argv[17 + len(REVIEWER_OFF):] == ["--output-format", "stream-json", "--verbose", "--add-dir", str(rig.root)]
    bash = rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]
    assert (bash["result"], bash["canary"], bash["changed_files"]) == ("pass", "readonly", [])


@pytest.mark.parametrize("mode", ["not_offered", "deny_on_call"])
def test_a_denied_tool_that_still_writes_fails(rig, mode):
    rig.configure(disallow_mode=mode, deny_leaks=True)
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["checks"]["denied_tools"]["result"] == "fail" and rc["negative_probes"]["denied_tools"]["result"] == "fail"
    assert all(v["effect"] is True for v in rc["checks"]["denied_tools"]["observed"]["tools"].values())


def test_a_denied_tool_nobody_denied_is_unknown(rig):
    # Write is declared denied but nothing in the configuration denies it: in bypass mode it simply works.
    r, rc, _ = rig.qualify(rig.config(intended_tools=["Read"], denied_tools=["Write"]))
    assert rc["result"] == "FAIL" and rc["checks"]["denied_tools"]["result"] == "fail"
    # ... and when it is offered, not attempted and not refused, nothing was shown either way.
    rig.configure(write_works=False)
    r, rc, _ = rig.qualify(rig.config(intended_tools=["Read"], denied_tools=["Write"]))
    assert rc["checks"]["denied_tools"]["result"] == "unknown" and rc["result"] != "PASS"


@pytest.mark.parametrize("leak,check,named", [
    ("plugins_leak", "excluded_user_plugins", ["superpowers"]),
    ("skills_leak", "excluded_user_skills", ["superpowers:brainstorming", "synced"]),
    ("hooks_leak", "excluded_user_hooks", ["PreToolUse"])])
def test_a_user_level_leak_fails_and_is_named(rig, leak, check, named):
    rig.configure(**{leak: True})
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert {n for n, v in results(rc).items() if v == "fail"} == {check}
    assert rc["checks"][check]["observed"]["lean"] == named


def test_reviewer_passes_when_no_offered_tool_can_trigger_the_users_hooks(rig):
    rig.user_settings(USER_HOOKS)
    cfg, out = rig.config("reviewer.json", **REVIEWER), rig.tmp / "reviewer-receipt.json"
    r, rc, ev = rig.qualify(cfg, out=out)                 # disallowed tools are removed from the tool list
    assert r.returncode == PASS and rc["result"] == "PASS", r.stderr
    hooks = rc["checks"]["excluded_user_hooks"]
    assert hooks["result"] == "pass" and {k: hooks["observed"][k] for k in ("basis", "user_hook_events", "matcher_tools", "offered")} == {
        "basis": "cannot_fire", "user_hook_events": ["PostToolUse", "PreToolUse"],
        "matcher_tools": ["Edit", "MultiEdit", "Write"], "offered": False}
    assert hooks["observed"]["control"] == [] and hooks["observed"]["lean"] == []       # nothing to see by canary
    assert rc["offered_tools"] == [t for t in REAL_TOOLS if t not in REVIEWER_OFF]
    assert kyschema.validate(json.loads((SCHEMAS / "qualification.json").read_text()), rc) == []
    # only event names and matcher strings ever leave the user's settings file
    written = out.read_text() + "".join(p.read_text(errors="replace") for p in ev.rglob("*") if p.is_file())
    assert "s3cr3t" not in written and "SOME_TOKEN" not in written and "defaultMode" not in written
    assert all(c["env_names"] == sorted(BOOT_ENV + ["__CF_USER_TEXT_ENCODING"]) or set(c["env_names"]) == set(BOOT_ENV) for c in rig.calls())
    assert rig.run("check", out, "--config", cfg, "--verify-evidence").returncode == 0
    other = rig.run("check", out, "--config", rig.config(**dict(REVIEWER, bash_canary="write")))
    assert other.returncode == 1 and "bash_canary: the receipt used 'readonly'" in other.stdout


def test_a_hook_seen_running_fails_even_when_the_structure_says_it_cannot(rig):
    rig.user_settings(USER_HOOKS)
    rig.configure(session_hook=True, hooks_leak=True)     # a hook that needs no tool runs in the lean configuration
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    hooks = rc["checks"]["excluded_user_hooks"]
    assert rc["result"] == "FAIL" and hooks["result"] == "fail"
    assert hooks["observed"]["lean"] == ["SessionStart"] and hooks["observed"]["basis"] == "hook_observed"


def test_hooks_that_an_offered_tool_can_trigger_fall_back_to_the_canary_and_the_control(rig):
    rig.user_settings({"PreToolUse": [{"matcher": "Edit|Bash", "hooks": []}]})
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))        # Bash is offered to the reviewer
    hooks = rc["checks"]["excluded_user_hooks"]
    assert hooks["result"] == "unknown" and r.returncode == UNKNOWN and rc["result"] == "unknown"
    assert hooks["observed"]["basis"] == "canary_and_control" and hooks["observed"]["offered"] is True
    assert hooks["observed"]["structure"] == "an offered tool can trigger a user hook (Bash)"
    rig.user_settings(USER_HOOKS)
    r, rc, _ = rig.qualify()                              # the builder is offered Write: the canary decides, and passes
    hooks = rc["checks"]["excluded_user_hooks"]
    assert r.returncode == PASS and hooks["result"] == "pass" and hooks["observed"]["basis"] == "canary_and_control"
    assert hooks["observed"]["structure"] == "an offered tool can trigger a user hook (Edit, NotebookEdit, Write)"
    assert hooks["observed"]["control"] == ["PreToolUse"]


def test_an_unreadable_user_settings_file_leaves_hooks_unknown(rig):
    rig.user_settings(raw="{ this is not JSON s3cr3t")
    r, rc, ev = rig.qualify()                             # even the builder, whose canary would have passed
    hooks = rc["checks"]["excluded_user_hooks"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown" and hooks["result"] == "unknown"
    assert hooks["observed"]["basis"] == "user_settings_unreadable"
    assert hooks["observed"]["why"] == "the user's settings file is not valid JSON"
    assert "s3cr3t" not in json.dumps(rc)
    assert {n for n, v in results(rc).items() if v == "unknown"} == {"excluded_user_hooks", "denied_tools"}


HOOK_STRUCTURES = [
    ("plain matchers, no such tool offered", USER_HOOKS, ["Bash", "Read", "ToolSearch"], True, None),
    ("a matcher names an offered tool", USER_HOOKS, ["Read", "Write"], False, "an offered tool can trigger a user hook (Write)"),
    ("an offered tool contains a matcher name", {"PreToolUse": [{"matcher": "Edit"}]}, ["NotebookEdit", "Read"], False, "(NotebookEdit)"),
    ("a SessionStart hook", dict(USER_HOOKS, SessionStart=[{"hooks": []}]), ["Read"], False, "needs no tool is configured (SessionStart)"),
    ("only prompt and stop hooks", {"UserPromptSubmit": [{}], "Stop": [{}]}, ["Read"], False, "(Stop, UserPromptSubmit)"),
    ("a * matcher", {"PreToolUse": [{"matcher": "*"}]}, ["Read"], False, "wildcard"),
    ("an empty matcher", {"PostToolUse": [{"matcher": ""}]}, ["Read"], False, "empty"),
    ("no matcher at all", {"PreToolUse": [{"hooks": []}]}, ["Read"], False, "missing"),
    ("a regular expression", {"PreToolUse": [{"matcher": "Notebook.*"}]}, ["Read"], False, "regular expression"),
    ("an alternation with spaces", {"PostToolUse": [{"matcher": "Edit | Write"}]}, ["Read"], False, "regular expression"),
    ("no hooks key", None, ["Read"], False, "no hooks"),
    ("only empty event lists", {"PreToolUse": [], "Stop": []}, ["Read"], False, "no hooks"),
    ("the offered tools were not observed", USER_HOOKS, None, False, "not observed"),
]


@pytest.mark.parametrize("name,hooks,offered,cannot_fire,reason", HOOK_STRUCTURES, ids=[c[0] for c in HOOK_STRUCTURES])
def test_structural_hook_detector_decides_only_what_the_structure_shows(rig, name, hooks, offered, cannot_fire, reason):
    rig.user_settings(hooks)
    config, error = kyqualify.user_hook_config(str(rig.home))
    assert error is None and "s3cr3t" not in repr(config) and all(len(entry) == 2 for entry in config)
    found = kyqualify.hook_structure(config, offered)
    assert found["cannot_fire"] is cannot_fire
    if cannot_fire:
        assert found == {"cannot_fire": True, "reason": None, "user_hook_events": ["PostToolUse", "PreToolUse"],
                         "matcher_tools": ["Edit", "MultiEdit", "Write"], "offered": False}
    else:
        assert reason in found["reason"]


def test_user_hook_configuration_is_read_narrowly_or_not_at_all(rig):
    settings = rig.home / ".claude" / "settings.json"
    assert kyqualify.user_hook_config(str(rig.home)) == ([], None)                       # no file: no hooks
    rig.user_settings(USER_HOOKS)
    assert kyqualify.user_hook_config(str(rig.home)) == ([("PreToolUse", "Edit|Write|MultiEdit"), ("PostToolUse", "Edit|Write"),
                                                          ("PostToolUse", "Write")], None)
    for raw, why in (("{ nope", "not valid JSON"), ("[1, 2]", "unexpected shape"), ('{"hooks": ["PreToolUse"]}', "unexpected shape"),
                     ('{"hooks": {"PreToolUse": {"matcher": "Write"}}}', "unexpected shape"),
                     ('{"hooks": {"PreToolUse": ["Write"]}}', "unexpected shape")):
        rig.user_settings(raw=raw)
        config, error = kyqualify.user_hook_config(str(rig.home))
        assert config is None and why in error, raw
    rig.user_settings(USER_HOOKS)
    settings.chmod(0)
    try:
        assert kyqualify.user_hook_config(str(rig.home)) == (None, "the user's settings file cannot be read")
    finally:
        settings.chmod(0o600)


READONLY_CASES = [
    ("a wrong hash", {"bash_digest_wrong": True}, {}, "effect was not observed"),
    ("a file changed on disk", {"bash_touches_disk": True}, {}, "a file changed on disk"),
    ("the command is not allowed", {}, {"extra_flags": []}, "permission denial"),
    ("the write canary in a read-only shell", {}, {"bash_canary": "write"}, "permission denial"),
]


@pytest.mark.parametrize("name,fake,config,why", READONLY_CASES, ids=[c[0] for c in READONLY_CASES])
def test_the_bash_canary_fails_on(rig, name, fake, config, why):
    rig.user_settings(USER_HOOKS)                         # as in the passing reviewer run above: only Bash differs
    rig.configure(**fake)
    r, rc, _ = rig.qualify(rig.config(**dict(REVIEWER, **config)))
    bash = rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert bash["result"] == "fail" and why in bash["why"] and bash["canary"] == config.get("bash_canary", "readonly")
    assert {n for n, v in results(rc).items() if v == "fail"} == {"intended_tools"}
    if name == "a file changed on disk":
        assert bash["effect"] is True and bash["changed_files"] == ["SIDE_EFFECT.txt"]


def test_without_a_control_absence_proves_nothing(rig):
    r, rc, _ = rig.qualify(control=False)
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    assert {n: v for n, v in results(rc).items() if v != "pass"} == {
        "excluded_user_plugins": "unknown", "excluded_user_skills": "unknown", "excluded_user_hooks": "unknown",
        "denied_tools": "unknown"}
    assert all(c["argv"][c["argv"].index("--setting-sources") + 1] == "project" for c in rig.calls())


def test_project_instructions_absent_fails(rig):
    rig.configure(load_project_md=False)
    r, rc, _ = rig.qualify()
    assert rc["result"] == "FAIL" and rc["checks"]["project_claude_md_visible"]["result"] == "fail"


def test_project_instructions_need_a_clean_negative_control_and_a_file(rig):
    rig.configure(always_footer=True)       # the token shows up even in the empty directory
    r, rc, _ = rig.qualify()
    seen = rc["checks"]["project_claude_md_visible"]
    assert seen["result"] == "unknown" and seen["observed"]["negative_control_clean"] is False
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    rig.configure()
    (rig.proj / "CLAUDE.md").unlink()
    r, rc, _ = rig.qualify()
    assert rc["checks"]["project_claude_md_visible"]["result"] == "unknown" and rc["result"] == "unknown"


def test_a_hung_run_fails_and_its_process_group_is_killed(rig):
    rig.configure(hang_on=["bash"])
    r, rc, ev = rig.qualify(args=("--run-timeout", "1.5"))
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    hung = rc["checks"]["no_tty_prompt"]
    assert hung["result"] == "fail" and hung["observed"]["runs"]["tool-bash"] == {
        "exited_by_itself": False, "result_event": False}
    assert hung["observed"]["run_timeout_seconds"] == 1.5
    record = json.loads((ev / "runs" / "tool-bash" / "run.json").read_text())
    assert record["timed_out"] is True and record["signals_sent"][0] == "SIGTERM" and record["group_gone"] is True
    assert rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]["result"] == "fail"
    pids = rig.sleep_pids()
    assert pids and not any(alive(p) for p in pids)              # the hung run's child (and the probes' sleeps)


# ------------------------------------------------------------------------------ each negative probe, flipping

def test_missing_authentication_probe_that_still_signs_in_fails(rig):
    rig.configure(auth_ignores_home=True)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)       # only the probe says no
    probe = rc["negative_probes"]["missing_authentication"]
    assert probe["result"] == "fail" and probe["observed"]["sign_in"] == "works" and "empty" in probe["why"]


def test_invalid_settings_that_are_accepted_fail(rig):
    rig.configure(accept_invalid_mcp=True)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    assert rc["negative_probes"]["invalid_settings"]["result"] == "fail"
    assert {n for n, p in rc["negative_probes"].items() if p["result"] == "fail"} == {"invalid_settings"}


def test_timeout_and_termination_probes_need_a_run_that_was_really_killed(rig):
    rig.configure(ignore_sleep=True)        # the canary ends by itself: no timeout, no termination was produced
    r, rc, _ = rig.qualify(args=("--probe-timeout", "10"))
    probes = results(rc, "negative_probes")
    assert (probes["timeout"], probes["termination"], probes["restart"]) == ("unknown", "unknown", "unknown")
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"


def test_a_group_that_ignores_term_is_killed_and_recorded(rig):
    rig.configure(trap_term=True)
    r, rc, ev = rig.qualify(args=("--probe-timeout", "1.5", "--term-grace", "0.5"))
    assert r.returncode == PASS and rc["result"] == "PASS", r.stderr
    for probe, run in (("timeout", "neg-timeout"), ("termination", "neg-term")):
        seen = rc["negative_probes"][probe]["observed"]
        assert seen["signals_sent"] == ["SIGTERM", "SIGKILL"] and seen["group_gone"] is True
        assert seen["descendants_at_kill"] == 1 and seen["descendants_survived_group_kill"] == []
        record = json.loads((ev / "runs" / run / "run.json").read_text())
        assert record["exit_code"] == -9 and record["result_event"] is False
    assert rc["negative_probes"]["timeout"]["observed"]["timed_out"] is True
    assert rc["negative_probes"]["termination"]["observed"]["terminated_by_signal"] is True
    pids = rig.sleep_pids()
    assert len(pids) == 2 and not any(alive(p) for p in pids)


def test_a_child_outside_the_process_group_is_recorded_and_never_signalled(rig):
    rig.configure(detach_sleep=True)        # the program starts its shell command in a session of its own
    r, rc, ev = rig.qualify(args=("--probe-timeout", "1.5"))
    pids = rig.sleep_pids()
    try:
        assert r.returncode == PASS and rc["result"] == "PASS"      # the brief's claim is about the process group
        for probe, run in (("timeout", "neg-timeout"), ("termination", "neg-term")):
            seen = rc["negative_probes"][probe]
            assert seen["result"] == "pass" and seen["observed"]["group_gone"] is True
            assert seen["observed"]["descendants_survived_group_kill"] == ["sleep"] and "still running" in seen["why"]
            record = json.loads((ev / "runs" / run / "run.json").read_text())
            assert [e["pid"] for e in record["descendants_survived_group_kill"]] == [p for p in pids if p in record["descendants_at_kill"]]
        assert len(pids) == 2 and all(alive(p) for p in pids)       # observed, reported, left alone
    finally:
        for pid in pids:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass


def test_hook_exclusion_needs_an_attempted_write_in_the_configuration_itself(rig):
    rig.configure(lean_hook_run_idle=True)  # the control shows the hook, but the lean run never tried to write
    r, rc, _ = rig.qualify()
    hooks = rc["checks"]["excluded_user_hooks"]
    assert hooks["result"] == "unknown" and hooks["observed"]["lean_write_attempted"] is False
    assert hooks["observed"]["control"] == ["PreToolUse"] and r.returncode == UNKNOWN and rc["result"] == "unknown"


def test_a_bound_file_that_changes_during_the_run_refuses(rig):
    rig.configure(touch_on_ctx=str(rig.card))
    r, rc, _ = rig.qualify()
    assert r.returncode == 74 and rc is None and "changed during the run" in r.stderr


def test_restart_after_termination_must_succeed(rig):
    rig.configure(ready_fails=True)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["negative_probes"]["termination"]["result"] == "pass"
    assert rc["negative_probes"]["restart"]["result"] == "fail"
    assert rc["checks"]["no_tty_prompt"]["result"] == "pass"       # it exited by itself, with a result event


# ------------------------------------------------------------------------------------------- launchd context

LABEL = "in.marsys.kalayantra.qualify.bootstrap-builder"


def test_launchd_context_runs_inside_the_one_shot_agent_and_removes_it(rig):
    cfg, out = rig.config("launchd.json"), rig.tmp / "launchd-receipt.json"
    r, rc, ev = rig.qualify(cfg, context="launchd", out=out)
    assert r.returncode == PASS, r.stderr + (ev / "launchd" / "launchd.err").read_text()
    assert rc["result"] == "PASS" and rc["context"] == "launchd"
    lr = rc["launchd_receipt"]
    assert lr["label"] == LABEL and lr["domain"] == "gui/%d" % os.getuid()
    assert (lr["bootstrap_exit"], lr["loaded_after_bootstrap"], lr["finished"], lr["absent_after_bootout"]) == \
        (0, True, True, True)
    assert lr["inner"]["ppid"] == 1 and lr["inner"]["xpc_service_name"] == LABEL
    assert rc["checks"]["launchd_context"] == dict(rc["checks"]["launchd_context"], required=True, result="pass")
    pl = plistlib.load(open(ev / "launchd" / (LABEL + ".plist"), "rb"))
    assert pl["Label"] == LABEL and pl["RunAtLoad"] is True and "KeepAlive" not in pl
    assert set(pl["EnvironmentVariables"]) == {"PATH", "HOME", "USER", "LANG"}
    assert pl["ProgramArguments"][2:4] == [str(KYQUALIFY), "launchd-inner"]
    assert not (rig.bindir / "booted").exists()
    seen = [json.loads(line)[0] for line in (rig.bindir / "launchctl_calls.jsonl").read_text().splitlines()]
    assert seen[0] == "bootstrap" and "bootout" in seen and seen[-1] == "print"
    assert rc["evidence"]["files"]["launchd/%s.plist" % LABEL] == sha(ev / "launchd" / (LABEL + ".plist"))
    assert kyschema.validate(json.loads((SCHEMAS / "qualification.json").read_text()), rc) == []
    # the caller's KY_ROOT reached the children although the plist carries PATH/HOME/USER/LANG only
    assert {c["ky_root"] for c in rig.calls()} == {str(rig.root)}
    check = rig.run("check", out, "--config", cfg, "--require-context", "launchd", "--verify-evidence")
    assert check.returncode == 0, check.stdout
    assert rig.run("check", out, "--config", cfg, "--require-context", "shell").returncode == 1


def test_an_agent_that_is_still_loaded_after_bootout_fails(rig):
    rig.launchctl(sticky=True)
    r, rc, _ = rig.qualify(context="launchd")
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["checks"]["launchd_context"]["result"] == "fail" and rc["launchd_receipt"]["absent_after_bootout"] is False
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    # "absent after bootout" means nothing unless the same query showed the agent while it was loaded
    rig.launchctl(never_listed=True)
    r, rc, _ = rig.qualify(context="launchd")
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    seen = rc["checks"]["launchd_context"]
    assert seen["result"] == "unknown" and seen["observed"]["loaded_after_bootstrap"] is False
    assert seen["observed"]["absent_after_bootout"] is True and seen["observed"]["parent_pid"] == 1


def test_a_shell_run_can_never_carry_the_launchd_label(rig, clean):
    assert clean.receipt["context"] == "shell" and "launchd_context" not in clean.receipt["checks"]
    # (a) the in-agent entry point, started from a shell with the label forged in the environment
    ev = rig.tmp / "forged"
    r = rig.run("launchd-inner", "--config", rig.config(), "--evidence-dir", ev, "--label", LABEL,
                extra_env={"XPC_SERVICE_NAME": LABEL})
    assert r.returncode == 77 and "not inside launchd" in r.stderr
    assert not (ev / "launchd" / "receipt.inner.json").exists() and rig.calls() == []
    # (b) a launchctl that runs the job as its own child, or under another service name, is not launchd
    for mode in ({"direct": True}, {"xpc_service_name": "0"}):
        rig.launchctl(**mode)
        r, rc, _ = rig.qualify(context="launchd")
        assert r.returncode == 75 and rc is None and "not inside launchd" in r.stderr
        assert rig.calls() == []                                    # nothing was launched at all
        assert not (rig.bindir / "booted").exists()                 # and the agent was still booted out
    # (c) relabelling a shell receipt by hand is refused by check
    forged = copy.deepcopy(clean.receipt)
    forged["context"] = "launchd"
    path = rig.tmp / "forged.json"
    path.write_text(json.dumps(forged))
    r = clean.run("check", path, "--config", clean.cfg)
    assert r.returncode == 1 and "launchd" in r.stdout
    forged["checks"]["launchd_context"] = {"required": True, "result": "pass", "observed": {}, "evidence": []}
    path.write_text(json.dumps(forged))                             # even with the check itself forged in
    r = clean.run("check", path, "--config", clean.cfg)
    assert r.returncode == 1 and json.loads(r.stdout)["reasons"] == [
        "context: labelled launchd without a launchd receipt that shows the agent ran and was removed"]
    r = clean.run("check", clean.out, "--config", clean.cfg, "--require-context", "launchd")
    assert r.returncode == 1 and "context" in r.stdout


def test_an_incomplete_run_never_replaces_an_existing_receipt(rig):
    out = rig.tmp / "kept.json"
    out.write_text('{"sentinel": true}\n')
    rig.launchctl(bootstrap_fails=True)
    r, _, ev = rig.qualify(context="launchd", out=out)
    assert r.returncode == 75 and json.loads(out.read_text()) == {"sentinel": True}
    assert json.loads((ev / "launchd" / "LAUNCHD_RECEIPT.json").read_text())["bootstrap_exit"] == 5
    assert "bootout gui/%d/%s" % (os.getuid(), LABEL) in r.stderr                 # how to clear a leftover agent
    assert [json.loads(line)[0] for line in (rig.bindir / "launchctl_calls.jsonl").read_text().splitlines()] == ["bootstrap"]
    r, _, _ = rig.qualify(out=out, evidence=ev)                    # evidence directory already used
    assert r.returncode == 73 and json.loads(out.read_text()) == {"sentinel": True}
    for mode, wait in (({"never_starts": True}, "1"), ({"dies": True}, "60")):
        rig.launchctl(**mode)
        began = time.time()
        r, _, _ = rig.qualify(context="launchd", out=out, args=("--wait", wait))
        assert r.returncode == 75 and "no exit record" in r.stderr and time.time() - began < 15
        assert json.loads(out.read_text()) == {"sentinel": True} and not (rig.bindir / "booted").exists()
    rig.launchctl()
    r, _, _ = rig.qualify(out=out, extra_env={"PGPASSWORD": "x"})
    assert r.returncode == 78 and json.loads(out.read_text()) == {"sentinel": True}
    r, _, _ = rig.qualify(out=out, evidence=rig.proj / "evidence")  # never inside the checkout being qualified
    assert r.returncode == 73 and "outside the worktree" in r.stderr and not (rig.proj / "evidence").exists()
    rig.configure(hang_on=["ctx"])
    r, rc, _ = rig.qualify(out=out, args=("--run-timeout", "1"))   # complete but failing: this one does replace it
    assert r.returncode == FAIL and rc["result"] == "FAIL"


def test_interrupting_the_harness_kills_its_children_and_writes_no_receipt(rig):
    rig.configure(hang_on=["ctx", "read", "write", "edit", "bash", "ready"])
    out, ev = rig.tmp / "never.json", rig.tmp / "interrupted"
    env = {"HOME": str(rig.home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin", "KY_ROOT": str(rig.root)}
    proc = subprocess.Popen([sys.executable, str(KYQUALIFY), "qualify", "--config", str(rig.config()), "--context", "shell",
                             "--evidence-dir", str(ev), "--out", str(out), "--control", "--parallel", "8",
                             "--term-grace", "2"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    end = time.time() + 20
    while len(rig.sleep_pids()) < 6 and time.time() < end:
        time.sleep(0.05)
    pids = rig.sleep_pids()
    assert len(pids) >= 6 and all(alive(p) for p in pids)
    proc.terminate()
    _, stderr = proc.communicate(timeout=60)
    assert proc.returncode == 130 and "interrupted" in stderr and not out.exists()
    assert not any(alive(p) for p in rig.sleep_pids())


# ---------------------------------------------------------------------------------------------------- check

def test_check_passes_only_for_a_pass_receipt_with_identical_binds(clean):
    r = clean.run("check", clean.out, "--config", clean.cfg, "--verify-evidence")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout) == {"check": "PASS", "context": "shell", "reasons": [], "receipt": str(clean.out)}
    for path, key in ((clean.bindir / "claude", "claude_bin_sha256"), (clean.card, "prompt_sha256"),
                      (clean.mcp, "mcp_config_sha256")):
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# changed\n" if path != clean.mcp else b'{"mcpServers": {}}\n')
            r = clean.run("check", clean.out, "--config", clean.cfg)
            assert r.returncode == 1 and json.loads(r.stdout)["reasons"] == ["binds differ: %s" % key]
        finally:
            path.write_bytes(original)
    assert clean.run("check", clean.out, "--config", clean.cfg).returncode == 0
    (clean.bindir / "fake.json").write_text(json.dumps(dict(DEFAULT, version="2.1.297 (Claude Code)")))
    try:
        r = clean.run("check", clean.out, "--config", clean.cfg)
        assert r.returncode == 1 and json.loads(r.stdout)["reasons"] == ["binds differ: claude_version"]
    finally:
        clean.configure()


@pytest.mark.parametrize("change,differs", [
    ({"model": "claude-sonnet-5-5"}, "argv, model"),
    ({"effort": "xhigh"}, "argv, effort"),
    ({"permission_mode": "acceptEdits"}, "argv, permission_mode"),
    ({"max_turns": 151}, "argv, max_turns"),
    ({"extra_flags": ["--disable-slash-commands"]}, "argv, extra_flags"),
    ({"disallowed_tools": ["NotebookEdit"]}, "argv, disallowed_tools"),
    ({"add_dirs": []}, "add_dirs, argv"),
    ({"mcp_config": "COPY"}, "argv"),
    ({"claude_bin": "LINK"}, "argv, claude_bin"),
    ({"deadline_seconds": 14401}, "deadline_seconds"),
    ({"worktree": "OTHER"}, "worktree"),
    ({"env_names": ENV_NAMES + ["KY_SCRATCH"]}, "env_names"),
    ({"child_path": "/usr/bin:/bin"}, "child_path")])
def test_check_fails_when_any_bound_element_changes(clean, change, differs):
    change = dict(change)
    if change.get("mcp_config") == "COPY":                 # same bytes, another path: the argv element changes
        copy_path = clean.tmp / "mcp.copy.json"
        copy_path.write_bytes(clean.mcp.read_bytes())
        change["mcp_config"] = str(copy_path)
    if change.get("claude_bin") == "LINK":                 # same program, another path
        link = clean.tmp / "claude-link"
        if not link.exists():
            link.symlink_to(clean.bindir / "claude")
        change["claude_bin"] = str(link)
    if change.get("worktree") == "OTHER":
        (clean.tmp / "other").mkdir(exist_ok=True)
        change["worktree"] = str(clean.tmp / "other")
    r = clean.run("check", clean.out, "--config", clean.config(**change))
    assert r.returncode == 1 and "binds differ: %s" % differs in json.loads(r.stdout)["reasons"]


def test_check_recomputes_the_result_and_the_tool_coverage(clean, rig):
    def verdict(mutate, cfg=None):
        doc = copy.deepcopy(clean.receipt)
        mutate(doc)
        path = rig.tmp / "mutated.json"
        path.write_text(json.dumps(doc))
        r = clean.run("check", path, "--config", cfg or clean.cfg)
        return r.returncode, " | ".join(json.loads(r.stdout)["reasons"])

    assert verdict(lambda d: None) == (0, "")
    code, why = verdict(lambda d: d["checks"]["mcp_none"].update(result="unknown"))     # "PASS" left in place
    assert code == 1 and "result" in why
    code, why = verdict(lambda d: d["checks"].pop("excluded_user_hooks"))
    assert code == 1 and "result" in why
    code, why = verdict(lambda d: d["negative_probes"]["timeout"].update(result="not_simulated"))
    assert code == 1 and "result" in why
    code, why = verdict(lambda d: d.update(result="FAIL"))
    assert code == 1 and "FAIL" in why
    code, why = verdict(lambda d: d.update(role="surrogate"))
    assert code == 1 and "role" in why
    code, why = verdict(lambda d: d["evidence"]["files"].update({"runs/base/stdout.jsonl": "0" * 64}))
    assert code == 0                                              # evidence is only compared on request
    code, why = verdict(lambda d: d["checks"]["intended_tools"]["observed"]["tools"]["Bash"].update(canary="readonly"))
    assert code == 1 and why.startswith("bash_canary: the receipt used 'readonly'")
    # the receipt covers Read/Write/Edit/Bash: a configuration declaring other tools is not the one it qualified
    code, why = verdict(lambda d: None, clean.config(intended_tools=["Read", "Bash"]))
    assert code == 1 and why.startswith("intended_tools: the receipt covers")
    code, why = verdict(lambda d: None, clean.config(intended_tools=["Read", "Bash"], denied_tools=["Write", "Edit"]))
    assert code == 1 and "denied_tools: the receipt covers" in why and "result" in why
    path = rig.tmp / "evidence-edited.json"
    doc = copy.deepcopy(clean.receipt)
    doc["evidence"]["files"]["runs/base/stdout.jsonl"] = "0" * 64
    path.write_text(json.dumps(doc))
    r = clean.run("check", path, "--config", clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and "runs/base/stdout.jsonl" in r.stdout
    doc = copy.deepcopy(clean.receipt)
    doc["offered_tools"] = [t for t in doc["offered_tools"] if t != "Task"]       # hide the subagent tool
    path.write_text(json.dumps(doc))
    assert clean.run("check", path, "--config", clean.cfg).returncode == 0        # recomputed only from the evidence
    r = clean.run("check", path, "--config", clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and json.loads(r.stdout)["reasons"] == ["offered_tools: not the tool list of the base run in the evidence"]


def test_planner_receipt_satisfies_the_loop_controller(rig, monkeypatch):
    import kyloop

    assert tuple(kyloop.ROLES) == tuple(kyqualify.LOOP_ROLES)
    fleet, run_dir = rig.root / "fleet_live", rig.root / "run"
    (fleet / "prompts").mkdir(parents=True)
    run_dir.mkdir()
    (fleet / "prompts" / kyloop.PROMPTS["planner"]).write_text("# planner loop prompt\n")
    (fleet / "mcp.none.json").write_text('{"mcpServers":{}}\n')
    for name, value in (("KY_ROOT", rig.root), ("KY_RUN", run_dir), ("KY_FLEET", fleet),
                        ("CLAUDE_BIN", rig.bindir / "claude")):
        monkeypatch.setenv(name, str(value))
    controller = kyloop.Controller("planner")
    loop_cfg = dict(kyloop.DEFAULTS["planner"], worktree=str(rig.proj), mcp_config=str(fleet / "mcp.none.json"))
    cfg = rig.config(role="planner", model=loop_cfg["model"], effort=loop_cfg["effort"],
                     permission_mode=loop_cfg["permission_mode"], max_turns=loop_cfg["max_turns"],
                     deadline_seconds=loop_cfg["deadline_seconds"], mcp_config=loop_cfg["mcp_config"],
                     prompt_path=str(fleet / "prompts" / kyloop.PROMPTS["planner"]),
                     env_names=list(kyloop.CHILD_ENV_NAMES), child_path=controller.child_path(),
                     add_dirs=[str(rig.root)])
    out = controller.qualification_path(loop_cfg)
    assert controller.check_qualification(loop_cfg) == ["qualification_missing: %s" % out]
    r, rc, _ = rig.qualify(cfg, out=out, extra_env={"KY_RUN": str(run_dir), "KY_FLEET": str(fleet)})
    assert r.returncode == PASS, r.stderr
    assert rc["binds"] == controller.expected_binds(loop_cfg)           # same keys, same values, nothing extra
    assert rc["binds"]["argv"] == controller.argv(loop_cfg)
    assert controller.check_qualification(loop_cfg) == []
    assert all(set(c["env_names"]) - {"__CF_USER_TEXT_ENCODING"} == set(kyloop.CHILD_ENV_NAMES) for c in rig.calls())
    # a receipt that did not pass never satisfies the controller, whatever it binds
    rig.configure(serve_model="claude-haiku-5-5")
    r, rc, _ = rig.qualify(cfg, out=out, extra_env={"KY_RUN": str(run_dir), "KY_FLEET": str(fleet)})
    assert rc["result"] == "FAIL" and controller.check_qualification(loop_cfg)[0].startswith("qualification_not_pass")


# ------------------------------------------------------------------------------ configuration and refusals

BAD_SHAPES = [
    ("unknown key", lambda d: d.update(sandbox=True), "unknown key: sandbox"),
    ("zero max_turns", lambda d: d.update(max_turns=0), "max_turns"),
    ("boolean max_turns", lambda d: d.update(max_turns=True), "max_turns"),
    ("missing deadline", lambda d: d.pop("deadline_seconds"), "missing key: deadline_seconds"),
    ("negative deadline", lambda d: d.update(deadline_seconds=-5), "deadline_seconds"),
    ("--bare", lambda d: d.update(extra_flags=["--bare"]), "--bare"),
    ("--settings=", lambda d: d.update(extra_flags=["--settings=/x.json"]), "--settings"),
    ("--setting-sources", lambda d: d.update(extra_flags=["--setting-sources", "user"]), "--setting-sources"),
    ("--mcp-config", lambda d: d.update(extra_flags=["--mcp-config", "/x.json"]), "--mcp-config"),
    ("skip permissions", lambda d: d.update(extra_flags=["--dangerously-skip-permissions"]), "--dangerously-skip-permissions"),
    ("flag the line owns", lambda d: d.update(extra_flags=["--model=claude-haiku-5-5"]), "--model is set by the launch line"),
    ("bare word flag", lambda d: d.update(extra_flags=["--disable-slash-commands", "now do this instead"]), "would become the prompt"),
    ("short flag", lambda d: d.update(extra_flags=["-p"]), "is not a flag"),
    ("dashed tool rule", lambda d: d.update(disallowed_tools=["--bare"]), "disallowed_tools"),
    ("credential env name", lambda d: d.update(env_names=ENV_NAMES + ["ANTHROPIC_API_KEY"]), "credential"),
    ("empty path entry", lambda d: d.update(child_path="/usr/bin::/bin"), "child_path"),
    ("relative worktree", lambda d: d.update(worktree="proj"), "worktree"),
    ("relative add_dir", lambda d: d.update(add_dirs=["ky"]), "add_dirs"),
    ("relative prompt", lambda d: d.update(prompt_path="cards/X.md"), "prompt_path"),
    ("wrong schema", lambda d: d.update(schema="ky.launch_config/2"), "schema"),
    ("unknown effort", lambda d: d.update(effort="extreme"), "effort"),
    ("unknown mode", lambda d: d.update(permission_mode="yolo"), "permission_mode"),
    ("no intended tool", lambda d: d.update(intended_tools=[]), "intended_tools"),
    ("tool without a canary", lambda d: d.update(intended_tools=["Read", "WebFetch"]), "intended_tools"),
    ("bad role", lambda d: d.update(role="Builder One"), "role"),
    ("unknown bash canary", lambda d: d.update(bash_canary="append"), "bash_canary"),
]


@pytest.mark.parametrize("name,mutate,needle", BAD_SHAPES, ids=[b[0] for b in BAD_SHAPES])
def test_launch_configuration_shape_is_strict_in_the_validator_and_in_the_schema(rig, name, mutate, needle):
    schema = json.loads((SCHEMAS / "launch_config.json").read_text())
    for good in (rig.doc(), rig.doc(bash_canary="readonly", extra_flags=[ALLOW]), rig.doc(**REVIEWER)):
        assert kyqualify.validate_config(good) == [] and kyschema.validate(schema, good) == []
    bad = rig.doc()
    mutate(bad)
    found = kyqualify.validate_config(bad)
    assert found and any(needle in f for f in found), found
    assert kyschema.validate(schema, bad), "the schema admits what the validator refuses: %s" % name


def test_launch_configuration_is_checked_against_the_disk_and_the_environment_policy(rig):
    def refused(**over):
        return " | ".join(kyqualify.validate_config(rig.doc(**over)))

    assert "worktree" in refused(worktree=str(rig.tmp / "nowhere"))
    assert "claude_bin" in refused(claude_bin=str(rig.mcp))                       # exists, not executable
    assert "prompt_path" in refused(prompt_path=str(rig.tmp / "NO_CARD.md"))
    assert "mcp_config" in refused(mcp_config=str(rig.tmp / "no.json"))
    assert "not normalised" in refused(worktree=str(rig.proj) + "/")
    assert "env value policy unknown: SE_EPHE_PATH" in refused(env_names=ENV_NAMES + ["SE_EPHE_PATH"])
    assert "credential" in refused(env_names=ENV_NAMES + ["KY_DATABASE_URL"])
    assert "env_names" in refused(env_names=["HOME", "PATH"])                     # the six plan §7 basics
    assert "child_path" in refused(child_path="/usr/bin::/bin")                   # an empty entry is the cwd
    assert "both intended and denied" in refused(denied_tools=["Write"])
    assert "disallowed" in refused(disallowed_tools=["Bash"])
    # KY_* names: conventional value, else the caller's, else refused — and nothing else ever
    names = ENV_NAMES + ["ZDOTDIR", "KY_PY", "KY_ROLE", "KY_ITEM", "KY_STREAM"]
    env, errs = kyqualify.resolve_env(rig.doc(env_names=names),
                                      {"HOME": "/h", "USER": "u", "KY_ROOT": "/k", "ZDOTDIR": "/mine", "LANG": "C"})
    assert errs == ["env value policy unknown: KY_STREAM (no conventional value and the caller's environment does not set it)"]
    env, errs = kyqualify.resolve_env(rig.doc(env_names=names),
                                      {"HOME": "/h", "USER": "u", "KY_ROOT": "/k", "ZDOTDIR": "/mine", "LANG": "C",
                                       "KY_STREAM": "S-1", "KY_FLEET": "/elsewhere"})
    assert errs == [] and env == {
        "HOME": "/h", "USER": "u", "LANG": "en_US.UTF-8", "TERM": "dumb", "TMPDIR": None,
        "PATH": "%s/bin:/opt/homebrew/bin:/usr/bin:/bin" % rig.root, "KY_ROOT": "/k", "KY_RUN": "/k/run",
        "KY_FLEET": "/elsewhere", "ZDOTDIR": "/k/zdotdir", "KY_PY": "/k/venv/bin/python",
        "KY_ROLE": "bootstrap-builder", "KY_ITEM": "KV3-B-QUALIFY", "KY_STREAM": "S-1"}   # names bound, values per job
    assert kyqualify.resolve_env(rig.doc(env_names=names), {"HOME": "/h", "USER": "u", "KY_STREAM": "S", "KY_ITEM": "KV3-B-7"})[0]["KY_ITEM"] == "KV3-B-7"
    assert "no Bash canary" in refused(intended_tools=["Read"], bash_canary="readonly")
    # the command refuses before anything is launched, and writes no receipt
    r, rc, _ = rig.qualify(rig.config(max_turns=0))
    assert r.returncode == 65 and rc is None and "max_turns" in r.stderr and rig.calls() == []
    dup = rig.tmp / "dup.json"
    dup.write_text(json.dumps(rig.doc())[:-1] + ', "max_turns": 5}')
    r, rc, _ = rig.qualify(dup)
    assert r.returncode == 65 and "duplicate key" in r.stderr


def test_the_launch_line_keeps_the_plan_order_with_every_optional_part(rig):
    doc = rig.doc(extra_flags=["--disable-slash-commands"], disallowed_tools=["NotebookEdit", "Bash(git push:*)"],
                  add_dirs=["/a", "/b"], role="conductor")
    assert kyqualify.validate_config(doc) == []
    assert kyqualify.build_argv(doc) == [
        doc["claude_bin"], "-p", "--setting-sources", "project", "--permission-mode", "bypassPermissions",
        "--model", "claude-opus-5-5", "--effort", "high", "--max-turns", "150", "--disable-slash-commands",
        "--strict-mcp-config", "--mcp-config", doc["mcp_config"], "--disallowedTools", "NotebookEdit",
        "Bash(git push:*)", "--output-format", "stream-json", "--verbose", "--add-dir", "/a", "--add-dir", "/b"]
    binds = kyqualify.compute_binds(doc)
    assert binds["extra_flags"] == ["--disable-slash-commands"] and "add_dirs" not in binds   # a loop role
    assert kyqualify.compute_binds(dict(doc, role="surrogate"))["add_dirs"] == ["/a", "/b"]
    assert kyqualify.variant(binds["argv"], sources="user,project", hook_events=True)[0] == \
        binds["argv"][:3] + ["user,project"] + binds["argv"][4:] + ["--include-hook-events"]


def test_refuses_credential_names_and_an_old_or_unreadable_program(rig):
    r, rc, _ = rig.qualify(extra_env={"KY_DATABASE_URL": "postgres://secret"})
    assert r.returncode == 78 and "KY_DATABASE_URL" in r.stderr and "secret" not in r.stderr + r.stdout
    r, rc, _ = rig.qualify(extra_env={"ANTHROPIC_API_KEY": "sk-secret"})
    assert r.returncode == 78 and "sk-secret" not in r.stderr + r.stdout and rc is None
    for version in ("2.1.295 (Claude Code)", "banana"):
        rig.configure(version=version)
        r, rc, _ = rig.qualify()
        assert r.returncode == 70 and rc is None and "2.1.296" in r.stderr
    assert rig.calls() == []


# ------------------------------------------------------------------------------------- schemas and templates

def test_schemas_use_only_the_supported_keywords():
    for name in ("launch_config", "qualification"):
        schema = json.loads((SCHEMAS / (name + ".json")).read_text())
        assert kyschema.lint(schema) == [], name
        assert schema["$id"] == "ky.%s/1" % name and schema["additionalProperties"] is False


TEMPLATE_FACTS = {
    # role: (permission mode, max turns, deadline, env names, extra flags, disallowed, intended, denied, card, optional keys)
    "bootstrap-builder": ("bypassPermissions", 150, 14400, BOOT_ENV, [], BUILDER_OFF, ["Read", "Write", "Edit", "Bash"], [],
                          "BOOTSTRAP.md", {}),
    "bootstrap-reviewer": ("default", 60, 3600, BOOT_ENV, [ALLOW], REVIEWER_OFF, ["Read", "Bash"], ["Write", "Edit"],
                           "FIXTURE_VERIFIER.md", {"bash_canary": "readonly"}),
    "surrogate": ("bypassPermissions", 30, 1800,
                  ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET"], [],
                  BUILDER_OFF, ["Read", "Write", "Bash"], [], "OWNER_SURROGATE.md", {}),
}


@pytest.mark.parametrize("role", sorted(TEMPLATE_FACTS))
def test_wave_b_templates_are_valid_launch_configurations(role):
    mode, turns, deadline, env_names, extra, disallowed, intended, denied, card, optional = TEMPLATE_FACTS[role]
    doc = json.loads((TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role)).read_text())
    schema = json.loads((SCHEMAS / "launch_config.json").read_text())
    assert kyschema.validate(schema, doc) == []
    assert kyqualify.validate_config(doc, check_disk=False) == []
    fleet = doc["mcp_config"].rsplit("/", 1)[0]
    assert fleet.endswith("/00_ARCHITECTURE/briefs/kalayantra/fleet") and doc["worktree"] == fleet.rsplit("/", 4)[0]
    assert {k: v for k, v in doc.items() if k != "_note"} == dict({
        "schema": "ky.launch_config/1", "role": role, "model": "claude-opus-5-5", "effort": "high",
        "permission_mode": mode, "max_turns": turns, "deadline_seconds": deadline, "worktree": doc["worktree"],
        "claude_bin": "/Users/Dev/.local/bin/claude", "mcp_config": fleet + "/mcp.none.json",
        "prompt_path": fleet + "/cards/" + card, "env_names": env_names,
        "child_path": "/Users/Dev/kalayantra/bin:/opt/homebrew/bin:/usr/bin:/bin", "extra_flags": extra,
        "disallowed_tools": disallowed, "add_dirs": ["/Users/Dev/kalayantra"], "intended_tools": intended,
        "denied_tools": denied}, **optional)
    assert ("_note" in doc) == (role == "bootstrap-reviewer")
    assert all(t in REAL_TOOLS for t in disallowed) and "Agent" not in disallowed       # real tool names only
    argv = kyqualify.build_argv(doc)
    assert argv[:12] == ["/Users/Dev/.local/bin/claude", "-p", "--setting-sources", "project", "--permission-mode", mode,
                         "--model", "claude-opus-5-5", "--effort", "high", "--max-turns", str(turns)]
    assert argv[12:-5] == extra + ["--strict-mcp-config", "--mcp-config", doc["mcp_config"], "--disallowedTools"] + disallowed
    assert argv[-5:] == ["--output-format", "stream-json", "--verbose", "--add-dir", "/Users/Dev/kalayantra"]
    assert all(argv.count(flag) == 1 and argv.index(flag) < argv.index("--strict-mcp-config") for flag in extra)
    assert "--bare" not in argv and "--dangerously-skip-permissions" not in argv
    # every environment name has a value without the caller supplying anything (KY_ITEM takes the qualification value)
    env, errs = kyqualify.resolve_env(doc, {"HOME": "/h", "USER": "u"})
    assert errs == [] and sorted(env) == sorted(env_names)
    assert env.get("KY_ITEM") in (None, "KV3-B-QUALIFY") and env.get("KY_PY") in (None, "/Users/Dev/kalayantra/venv/bin/python")
    if os.path.isdir(doc["worktree"]) and os.path.exists(doc["claude_bin"]):        # on the campaign host itself
        assert kyqualify.validate_config(doc) == []
        assert json.loads(Path(doc["mcp_config"]).read_text()) == {"mcpServers": {}}
