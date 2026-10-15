"""B-0c: kyqualify.py (plan v2.7 §7 launch qualification, KV-06) — every check and every negative probe is shown
to flip on a fake `claude` and a fake `launchctl` (root CLAUDE.md §N.8: a verdict nothing could turn false is null).
The real program and the real launchd are never called here: launchctl is always the ABSOLUTE fake named by
KY_LAUNCHCTL, and it counts as launchd only because the tests-only gate KY_QUALIFY_TEST_OVERRIDE=1 is set.

The fake `claude` models what the real program (2.1.296) does with permission rules, because the qualification is
about exactly that: project settings are read from <cwd>/.claude/settings.json when --setting-sources names
"project"; rules are `Tool`, `Bash(prefix:*)` and glob forms such as `Bash(git add*)` / `Bash(*--output*)`;
--disallowedTools takes tool names (removed from the offered tools) and rules; a deny rule beats an allow rule in
every permission mode; without a TTY an unlisted command in "default" mode is denied and reported in the result
event's permission_denials."""
import copy
import ast
import hashlib
import json
import os
import plistlib
import shutil
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
import fnmatch, hashlib, json, os, re, signal, subprocess, sys, time
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
cm = re.search(r"to run exactly this command(?: in the current directory| and wait for it to finish)?: (.*)\n", prompt)
command = cm.group(1) if cm else None
m = re.match(r"Use the (\w+) tool", prompt)
long_run = bool(command) and ("sleep 600" in command or "time.sleep(600)" in command)
kind = "sleep" if long_run else m.group(1).lower() if m else "ctx" if "lettered sections" in prompt else "ready"
def digest(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None
with open(os.path.join(here, "calls.jsonl"), "a") as f:
    f.write(json.dumps({"argv": a, "kind": kind, "command": command, "env_names": sorted(os.environ), "cwd": os.getcwd(),
                        "home": os.environ.get("HOME"), "path": os.environ.get("PATH"),
                        "tmpdir": os.environ.get("TMPDIR"), "ky_root": os.environ.get("KY_ROOT"),
                        "job_scratch": os.environ.get("JOB_SCRATCH"), "ky_scratch": os.environ.get("KY_SCRATCH"),
                        "zdotdir": os.environ.get("ZDOTDIR"), "tests": os.environ.get("TESTS"),
                        "project_settings": digest(os.path.join(".claude", "settings.json"))}) + "\n")
def out(ev):
    sys.stdout.write(json.dumps(ev) + "\n"); sys.stdout.flush()
def spawn_sleep(python=False, seconds="600"):
    argv = [sys.executable, "-c", "import time; time.sleep(600)"] if python else ["/bin/sleep", seconds]
    child = subprocess.Popen(argv, start_new_session=cfg["detach_sleep"])        # same group unless detached
    with open(os.path.join(here, "sleep_pids"), "a") as f:
        f.write("%d\n" % child.pid)
    return child
if kind in cfg["hang_on"]:                                    # a run that never answers (an unanswered prompt)
    spawn_sleep(); time.sleep(600)
sources = opt("--setting-sources").split(",")
user = "user" in sources
mode, model = opt("--permission-mode"), opt("--model")
served = cfg["serve_model"] or model
project = {}
if "project" in sources:                                      # project settings: the working directory's own file
    try:
        project = json.load(open(os.path.join(".claude", "settings.json")))
    except (OSError, ValueError):
        project = {}
perms = project.get("permissions") or {}
disallowed = multi("--disallowedTools")
bare_off = [r for r in disallowed if "(" not in r]
deny_rules = [r for r in disallowed if "(" in r] + list(perms.get("deny") or [])
allow_rules = [r for flag in a if flag.startswith("--allowedTools=") for r in flag.split("=", 1)[1].split(",")] \
    + list(perms.get("allow") or [])
project_hooks = bool(project.get("hooks"))
offered = [t for t in cfg["tools"] if not (t in bare_off and cfg["disallow_mode"] == "not_offered")]
skills = ["run-checks"] + (["synced", "superpowers:brainstorming"] if (user or cfg["skills_leak"]) else [])
init = {"type": "system", "subtype": "init", "session_id": "sess-1", "model": served,
        "permissionMode": cfg["serve_permission_mode"] or mode, "apiKeySource": cfg["api_key_source"],
        "claude_code_version": "2.1.296", "tools": offered + cfg["mcp_tools"], "mcp_servers": cfg["mcp_servers"],
        "plugins": [{"name": "cc-plugin-telemetry", "path": "builtin", "source": "cc-plugin-telemetry@builtin"}]
                   + ([{"name": "superpowers", "path": "/p", "source": "superpowers@m"}] if (user or cfg["plugins_leak"]) else []),
        "output_style": "default", "memory_paths": {"auto": "/m/"} if cfg["auto_memory"] else {},
        "skills": skills, "slash_commands": skills, "agents": []}
try:
    json.load(open(opt("--mcp-config")))
except ValueError:
    if cfg["invalid_mcp"] == "refused":                       # the real program: no session at all
        sys.stderr.write("Error: Invalid MCP configuration:\nMCP config is not a valid JSON\n"); sys.exit(1)
    if cfg["invalid_mcp"] == "late":                          # a session starts, then fails for another reason
        out(init)
        out({"type": "result", "subtype": "success", "is_error": True, "result": "API Error: 529 overloaded",
             "num_turns": 1, "permission_denials": []})
        sys.exit(1)
signed = cfg["logged_in"] and (cfg["auth_ignores_home"] or os.path.exists(
    os.path.join(os.environ.get("HOME", "/nonexistent"), ".claude", "signed_in")))
error = None
if not signed:
    error = cfg["unsigned_error"]
elif kind == "ready" and cfg["ready_fails"]:
    error = "Not logged in · Please run /login"
elif kind in cfg["error_on"]:
    error = cfg["error_on"][kind]
if error:                                                     # as the real program: a session, an error text, exit 1
    out(init)
    out({"type": "assistant", "message": {"content": [{"type": "text", "text": error}]}})
    out({"type": "result", "subtype": "success", "is_error": True, "result": error, "num_turns": 1,
         "session_id": "sess-1", "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0,
                                           "cache_read_input_tokens": 0, "output_tokens": 0},
         "modelUsage": {}, "permission_denials": []})
    sys.exit(1)
out(init)
if cfg["session_hook"] and "--include-hook-events" in a and (user or cfg["hooks_leak"]):
    out({"type": "system", "subtype": "hook_started", "hook_name": "SessionStart:startup", "hook_event": "SessionStart"})
denials, turns = [], [1]
def matches(rule, tool, inp):
    mm = re.match(r"^(\w+)(?:\((.*)\))?$", rule, re.S)
    if not mm:
        return False
    name, spec = mm.group(1), mm.group(2)
    if name != tool and not (name == "Edit" and tool == "Write"):       # an Edit rule covers every file-editing tool
        return False
    if spec is None:
        return True
    if tool == "Bash":
        if spec.endswith(":*"):                               # the prefix form
            return inp["command"].startswith(spec[:-2])
        return fnmatch.fnmatchcase(inp["command"], spec)      # the glob form
    return fnmatch.fnmatchcase(inp.get("file_path", ""), spec.replace("**", "*"))
def allowed(tool, inp):
    if tool in cfg["deny_tools"] or tool in bare_off:
        return False
    if any(matches(r, tool, inp) for r in deny_rules):
        return False                                          # a deny rule beats an allow rule, in every mode
    if mode == "bypassPermissions" or tool == "Read" or (mode == "acceptEdits" and tool in ("Write", "Edit")):
        return True
    return any(matches(r, tool, inp) for r in allow_rules)
def use(tool, inp, effect):
    if tool not in offered:
        if cfg["deny_leaks"]:
            effect()                                          # a model that works around the missing tool
        return False
    turns[0] += 1
    tid = "toolu_%d" % turns[0]
    out({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": tool, "input": inp}]}})
    if tool in ("Write", "Edit") and "--include-hook-events" in a and (user or cfg["hooks_leak"] or project_hooks):
        out({"type": "system", "subtype": "hook_started", "hook_name": "PreToolUse:" + tool, "hook_event": "PreToolUse"})
    ok, shown = allowed(tool, inp), None
    if ok or cfg["deny_leaks"]:
        shown = effect()
    failed = ok and isinstance(shown, str) and shown.startswith("Exit code ")     # it ran, and exited non-zero
    quiet = cfg["denial_silent"] and not ok                   # refused, yet the program reports nothing about it
    block = {"type": "tool_result", "tool_use_id": tid,
             "content": (shown or "ok") if ok else ("" if quiet else "permission denied")}
    if not ok and not quiet:
        denials.append({"tool_name": tool, "tool_use_id": tid, "tool_input": inp})
        block["is_error"] = True
    if failed:
        block["is_error"] = True                              # an error, and NOT a permission denial
    out({"type": "user", "message": {"content": [block]}})
    return ok and not failed
def shell_env():
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    zd, home = os.environ.get("ZDOTDIR"), os.environ.get("HOME", "/nonexistent")
    files = ([os.path.join(zd, ".zshenv")] if (zd and not cfg["zdotdir_ignored"])
             else [os.path.join(home, ".zshenv"), os.path.join(home, ".zprofile")])
    for path in files:                                        # a toy zsh: `export PATH="<dir>:$PATH"` lines only
        try:
            for line in open(path):
                mm = re.match(r'export PATH="([^":]+):\$PATH"', line.strip())
                if mm:
                    env["PATH"] = mm.group(1) + ":" + env.get("PATH", "")
        except OSError:
            pass
    return env
def sh(cmd):
    done = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, text=True, env=shell_env())
    return done.stdout if done.returncode == 0 else "Exit code %d\n%s" % (done.returncode, done.stderr + done.stdout)
text = "REFUSED"
if kind == "sleep":
    if not cfg["ignore_sleep"]:
        if cfg["trap_term"]:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)     # inherited by the sleep: only KILL ends the group
        def effect():
            if cfg["sleep_child"]:
                spawn_sleep("python3" in command).wait()
            else:
                if cfg["helper_child"]:
                    spawn_sleep(seconds="599")                # some other process of the program: not the canary's command
                time.sleep(600)                               # the program hangs, but no tool child ever runs
            time.sleep(600 if cfg["trap_term"] else 0)
        use("Bash", {"command": command}, effect)
    text = "1\n2\n3"
elif kind == "ctx":
    if cfg["touch_on_ctx"]:
        open(cfg["touch_on_ctx"], "a").write("changed while qualifying\n")
    footer = None
    if os.path.exists("CLAUDE.md") and cfg["load_project_md"]:
        footer = open("CLAUDE.md").read().strip().splitlines()[-1][:30]
    if cfg["always_footer"]:
        footer = "*CLAUDE.md v9.9 (2030-01-01) —"
    text = (footer or "NO_PROJECT_INSTRUCTIONS") + "\n" + ("/X/Archives" if (user or cfg["load_user_md"]) else "NO_USER_POLICY")
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
elif kind == "bash" and cfg["bash_idle"]:
    text = "REFUSED"                                          # the model never calls the tool
elif kind == "bash" and command.startswith("shasum -a 256"):
    box = []
    def effect():
        box.append("0" * 64 if cfg["bash_digest_wrong"] else sh(command).split()[0])
        if cfg["bash_touches_disk"]:
            open("SIDE_EFFECT.txt", "w").write("x")
        return box[-1]
    use("Bash", {"command": command}, effect)
    text = box[0] if box else "REFUSED"
elif kind == "bash":                                          # any other command really runs, in a real shell
    text = "DONE" if use("Bash", {"command": command}, lambda: sh(command)) else "REFUSED"
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
           "invalid_mcp": "refused", "api_key_source": "none", "load_project_md": True, "always_footer": False,
           "plugins_leak": False, "skills_leak": False, "hooks_leak": False, "mcp_servers": [], "mcp_tools": [],
           "write_works": True, "deny_tools": [], "deny_leaks": False, "disallow_mode": "not_offered",
           "ignore_sleep": False, "trap_term": False, "detach_sleep": False, "ready_fails": False,
           "hang_on": [], "serve_model": None, "serve_permission_mode": None, "lean_hook_run_idle": False,
           "touch_on_ctx": None, "ctx_turns": 1, "session_hook": False, "bash_digest_wrong": False,
           "bash_touches_disk": False, "unsigned_error": "Not logged in · Please run /login", "error_on": {},
           "denial_silent": False, "bash_idle": False, "sleep_child": True, "zdotdir_ignored": False,
           "load_user_md": False, "auto_memory": True, "helper_child": False,
           # init.tools of the real program on the campaign host (2.1.296); the subagent tool is "Task"
           "tools": ["Task", "Bash", "CronCreate", "CronDelete", "CronList", "DesignSync", "Edit", "EnterWorktree",
                     "ExitWorktree", "ListAgents", "Monitor", "NotebookEdit", "PushNotification", "Read",
                     "RemoteTrigger", "ReportFindings", "ScheduleWakeup", "SendMessage", "Skill", "TaskStop",
                     "ToolSearch", "WebFetch", "WebSearch", "Workflow", "Write"]}
REAL_TOOLS = sorted(DEFAULT["tools"])
ENV_NAMES = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
             "KY_SCRATCH", "JOB_SCRATCH"]
BOOT_ENV = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_SCRATCH",
            "JOB_SCRATCH", "KY_ITEM", "KY_PY"]                                  # rework ruling R1
SURROGATE_ENV = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
                 "KY_SCRATCH", "JOB_SCRATCH"]
BUILDER_OFF = ["Task", "Workflow", "CronCreate", "CronDelete", "RemoteTrigger", "ScheduleWakeup", "PushNotification",
               "SendMessage", "EnterWorktree", "ExitWorktree", "WebFetch", "WebSearch", "DesignSync"]
REVIEWER_OFF = ["Edit", "Write", "NotebookEdit"] + BUILDER_OFF + ["Skill"]
BASH_DENY = ["Bash(git add*)", "Bash(git commit*)", "Bash(git push*)", "Bash(git merge*)", "Bash(git switch*)",
             "Bash(git checkout*)", "Bash(git worktree*)", "Bash(git branch*)", "Bash(git reset*)",
             "Bash(git rebase*)", "Bash(git stash*)", "Bash(git tag*)", "Bash(git fetch*)", "Bash(git pull*)",
             "Bash(git config*)", "Bash(git remote*)", "Bash(*--output*)", "Bash(gh *)", "Bash(npm *)",
             "Bash(psql*)", "Bash(launchctl*)", "Bash(curl*)"]                 # rework ruling R7
ALLOW = ("--allowedTools=Bash(shasum:*),Bash(wc:*),Bash(ls:*),Bash(plutil -lint*),Bash(python3:*),Bash(git show:*),"
         "Bash(git diff:*),Bash(git log:*),Bash(git status:*)")
DENIED_BASH = ["touch DENIED_CANARY.txt", "git add -A", "git commit --allow-empty -m canary"]
REVIEWER = {"role": "bootstrap-reviewer", "permission_mode": "default", "max_turns": 60, "deadline_seconds": 3600,
            "env_names": BOOT_ENV, "disallowed_tools": REVIEWER_OFF + BASH_DENY, "extra_flags": [ALLOW],
            "intended_tools": ["Read", "Bash"], "bash_canary": "readonly", "shell_canary": "python3",
            "denied_tools": ["Write", "Edit"], "denied_bash": DENIED_BASH}
USER_HOOKS = {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": "echo s3cr3t-hook-command"}]}],
              "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "true"}]},
                              {"matcher": "Write", "hooks": [{"type": "command", "command": "true"}]}]}
# the worktree's project settings, shaped like the real ones: an env block, project-allowed git verbs, deny rules
PROJECT_SETTINGS = {"env": {"SOME_PROJECT_ENV": "pr0ject-env-value"},
                    "permissions": {"allow": ["Read(**)", "Bash(git status*)", "Bash(git add*)", "Bash(git commit*)",
                                              "Bash(git push*)"],
                                    "deny": ["Bash(*printenv*)", "Edit(.claude/settings.json)"]}}
REQUIRED = ["sign_in", "model_identity", "permission_mode_observed", "intended_tools", "no_tty_prompt",
            "project_claude_md_visible", "excluded_user_plugins", "excluded_user_skills", "excluded_user_hooks",
            "mcp_none"]
BIND_KEYS = {"claude_bin", "claude_bin_sha256", "claude_version", "argv", "model", "effort", "permission_mode",
             "max_turns", "deadline_seconds", "worktree", "env_names", "child_path", "prompt_sha256",
             "mcp_config_sha256"}                                              # what kyloop.py has always compared
NEW_BIND_KEYS = {"project_settings_sha256", "zdotdir_sha256", "harness_sha256"}  # rework ruling R6, every role
USER_BIND_KEYS = {"user_claude_md_sha256", "user_settings_hooks_sha256"}        # never for the loop roles
PASS, FAIL, UNKNOWN = 0, 1, 3      # kyqualify.py qualify exit codes when a receipt is written


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def results(receipt, part="checks"):
    return {name: entry["result"] for name, entry in receipt[part].items()}


def qualification_schema():
    return json.loads((SCHEMAS / "qualification.json").read_text())


def make_rig(tmp):
    home = tmp / "home"
    (home / ".claude" / "skills" / "synced").mkdir(parents=True)
    (home / ".claude" / "signed_in").write_text("fake sign-in marker; not a credential\n")
    (home / ".claude" / "CLAUDE.md").write_text("- Archives worth keeping (e.g. bundles): `/X/Archives/`\n")
    (home / ".zprofile").write_text('export PATH="/user/profile/bin:$PATH"\n')      # the user's own shell profile
    proj = tmp / "proj"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("# rules\n\n§A …\n\n*CLAUDE.md v9.9 (2030-01-01) — test footer.*\n")
    root = tmp / "ky"
    (root / "bin").mkdir(parents=True)
    (root / "zdotdir").mkdir()
    (root / "zdotdir" / ".zshenv").write_text('export PATH="/fleet/zdotdir/bin:$PATH"\n')
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

    def user_settings(hooks=None, raw=None, **more):
        """the user's ~/.claude/settings.json: hooks plus keys the harness must never read out"""
        doc = {"env": {"SOME_TOKEN": "s3cr3t-env-value"}, "permissions": {"defaultMode": "bypassPermissions"}}
        doc.update(more)
        if hooks is not None:
            doc["hooks"] = hooks
        (home / ".claude" / "settings.json").write_text(raw if raw is not None else json.dumps(doc))

    def project_settings(doc=None, absent=False):
        """the worktree's .claude/settings.json (None = the default above; absent = no file and no directory)"""
        directory = proj / ".claude"
        if directory.exists():
            shutil.rmtree(directory)
        if not absent:
            directory.mkdir()
            (directory / "settings.json").write_text(json.dumps(PROJECT_SETTINGS if doc is None else doc, indent=2))
        return directory / "settings.json"

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

    def run(*args, extra_env=None, script=KYQUALIFY):
        # launchctl is ALWAYS the absolute fake, and only the tests-only gate lets it count as launchd
        env = {"HOME": str(home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
               "KY_LAUNCHCTL": str(bindir / "launchctl"), "KY_QUALIFY_TEST_OVERRIDE": "1", "KY_ROOT": str(root),
               "KY_SCRATCH": str(tmp / "campaign-scratch")}
        env.update(extra_env or {})
        env = {k: v for k, v in env.items() if v is not None}          # None removes a variable
        return subprocess.run([sys.executable, "-B", str(script)] + [str(a) for a in args], env=env,
                              capture_output=True, text=True, timeout=180)

    def qualify(cfg=None, context="shell", control=True, extra_env=None, args=(), out=None, evidence=None,
                script=KYQUALIFY):
        counter[0] += 1
        cfg = cfg or config()
        evidence = evidence or tmp / ("evidence-%d" % counter[0])
        out = out or tmp / ("receipt-%d.json" % counter[0])
        argv = ["qualify", "--config", cfg, "--context", context, "--evidence-dir", evidence, "--out", out,
                "--run-timeout", "30", "--probe-timeout", "0.3", "--probe-wait", "20", "--term-grace", "2",
                "--parallel", "16", "--wait", "90", "--poll", "0.05"] + (["--control"] if control else []) + list(args)
        r = run(*argv, extra_env=extra_env, script=script)
        receipt = json.loads(out.read_text()) if out.exists() else None
        return r, receipt, evidence

    def check(receipt_path, cfg, *args, extra_env=None, script=KYQUALIFY):
        r = run("check", receipt_path, "--config", cfg, *args, extra_env=extra_env, script=script)
        return r, json.loads(r.stdout)

    def calls():
        path = bindir / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def sleep_pids():
        path = bindir / "sleep_pids"
        return [int(line) for line in path.read_text().split()] if path.exists() else []

    configure()
    project_settings()
    return type("Rig", (), dict(tmp=tmp, home=home, proj=proj, root=root, bindir=bindir, mcp=mcp, card=card,
                                configure=staticmethod(configure), launchctl=staticmethod(launchctl),
                                user_settings=staticmethod(user_settings),
                                project_settings=staticmethod(project_settings),
                                doc=staticmethod(doc), config=staticmethod(config), run=staticmethod(run),
                                qualify=staticmethod(qualify), check=staticmethod(check), calls=staticmethod(calls),
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
    want = dict({name: "pass" for name in REQUIRED}, input_overhead_worktree="pass", denied_tools="unknown",
                denied_bash="unknown", excluded_user_shell_profile="pass")
    assert results(rc) == want
    assert all(rc["checks"][name]["required"] for name in REQUIRED)
    assert not any(rc["checks"][name]["required"] for name in set(want) - set(REQUIRED))
    assert rc["checks"]["input_overhead_worktree"]["observed"] == 20000
    assert set(rc["checks"]["intended_tools"]["observed"]["tools"]) == {"Read", "Write", "Edit", "Bash"}
    assert rc["checks"]["intended_tools"]["observed"]["tools"]["Bash"]["canary"] == "write"
    assert rc["offered_tools"] == REAL_TOOLS                    # what the program itself listed in the base run
    hooks = rc["checks"]["excluded_user_hooks"]["observed"]
    assert hooks["basis"] == "canary_and_control" and hooks["meaning"].startswith("excluded, by observation")
    assert results(rc, "negative_probes") == {
        "missing_authentication": "pass", "inaccessible_keychain": "not_simulated", "denied_tools": "not_simulated",
        "invalid_settings": "pass", "timeout": "pass", "termination": "pass", "restart": "pass"}
    assert all(p["why"] for p in rc["negative_probes"].values() if p["result"] == "not_simulated")
    assert json.loads(clean.done.stdout)["result"] == "PASS"


def test_the_receipt_says_what_it_is_not(clean, rig):
    want = "configuration and controller after-exit checks; not sandboxed — the enforced verifier boundary is a B-1 deliverable"
    assert clean.receipt["boundary"] == want == kyqualify.BOUNDARY
    assert qualification_schema()["properties"]["boundary"]["const"] == want
    for mutate in (lambda d: d.pop("boundary"), lambda d: d.update(boundary="read-only, sandboxed")):
        doc = copy.deepcopy(clean.receipt)
        mutate(doc)
        path = rig.tmp / "no-boundary.json"
        path.write_text(json.dumps(doc))
        r, said = clean.check(path, clean.cfg)
        assert r.returncode == 1 and len(said["reasons"]) == 1 and said["reasons"][0].startswith("boundary:")
        assert kyschema.validate(qualification_schema(), doc) != []


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
    # rework ruling R6: the worktree's project settings, the fleet's ZDOTDIR files and the harness itself
    assert b["project_settings_sha256"] == sha(clean.proj / ".claude" / "settings.json")
    assert b["zdotdir_sha256"] == hashlib.sha256(b".zshenv" + (clean.root / "zdotdir" / ".zshenv").read_bytes()).hexdigest()
    assert b["harness_sha256"] == sha(KYQUALIFY)
    assert clean.receipt["harness"] == {"kyqualify_sha256": sha(KYQUALIFY), "kyprobe_sha256": sha(FLEET / "kyprobe.py")}
    # the user-level instruction sources (never bound for the loop roles)
    assert b["user_claude_md_sha256"] == sha(clean.home / ".claude" / "CLAUDE.md")
    assert b["user_settings_hooks_sha256"] == hashlib.sha256(b"[]").hexdigest()      # no user settings file: no hooks
    assert set(b) == BIND_KEYS | NEW_BIND_KEYS | USER_BIND_KEYS | {"add_dirs"}


def test_every_run_used_the_bound_argv_and_the_exact_environment(clean):
    bound, calls = clean.receipt["binds"]["argv"][1:], clean.calls()
    # base, empty, 4 tools, hooks, control, shell-path and its control, 4 negative runs, restart
    assert len(calls) == 15
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
        without = {"ZDOTDIR"} if c["cwd"].endswith("/shell-path-control") else set()     # that control's one difference
        assert set(c["env_names"]) - {"__CF_USER_TEXT_ENCODING"} == set(ENV_NAMES) - without
        assert c["path"] == clean.receipt["binds"]["child_path"] and c["ky_root"] == str(clean.root)
        assert c["tmpdir"].startswith(str(clean.evidence) + "/runs/") and c["tmpdir"].endswith("/tmp")
        # rework ruling R1: JOB_SCRATCH is that run's own scratch directory, KY_SCRATCH the campaign scratch root
        assert c["job_scratch"] == c["tmpdir"][:-len("tmp")] + "job_scratch" and os.path.isdir(c["job_scratch"])
        assert c["ky_scratch"] == str(clean.tmp / "campaign-scratch")
        assert c["zdotdir"] == (None if without else str(clean.root / "zdotdir"))
    assert (hook_runs, control_runs, other_mcp) == (2, 1, 1)
    assert len({c["job_scratch"] for c in calls}) == 15                # one per run, never shared
    foreign_home = [c for c in calls if c["home"] != str(clean.home)]
    assert len(foreign_home) == 1 and os.listdir(foreign_home[0]["home"]) == []      # missing-authentication probe
    in_worktree = sorted(c["kind"] for c in calls if c["cwd"] == str(clean.proj))
    assert in_worktree == ["ctx", "ready", "sleep"]                 # base, the terminated run and its restart
    assert all(c["cwd"].startswith(str(clean.evidence) + "/canary/") for c in calls if c["cwd"] != str(clean.proj))
    hooks = clean.receipt["checks"]["excluded_user_hooks"]["observed"]
    assert hooks["argv_difference"]["lean"] == ["appended --include-hook-events"]
    assert "--setting-sources project -> user,project" in hooks["argv_difference"]["control"]


def test_canaries_run_in_canary_projects_under_a_byte_copy_of_the_project_settings(clean):
    settings = clean.proj / ".claude" / "settings.json"
    want = sha(settings)
    by_cwd = {os.path.basename(c["cwd"]): c for c in clean.calls() if c["cwd"] != str(clean.proj)}
    projects = {"tool-read", "tool-write", "tool-edit", "tool-bash", "hooks", "control", "shell-path",
                "shell-path-control", "neg-timeout"}
    assert set(by_cwd) == projects | {"empty", "neg-auth", "neg-settings"}
    for name, call in by_cwd.items():       # what the program found in its own working directory
        assert call["project_settings"] == (want if name in projects else None), name
    for name in projects:                   # the copy and nothing else of the repository
        directory = clean.evidence / "canary" / name
        assert (directory / ".claude" / "settings.json").read_bytes() == settings.read_bytes()
        assert [p.name for p in (directory / ".claude").iterdir()] == ["settings.json"]
        assert not (directory / "CLAUDE.md").exists() and not (directory / ".git").exists()
    assert sorted(p.name for p in clean.proj.iterdir()) == [".claude", "CLAUDE.md"]       # the worktree is untouched
    assert sha(settings) == want
    seen = clean.receipt["observations"]["project_settings"]
    assert seen == {"sha256": want, "canary_projects": sorted(projects), "copies_intact": True, "in_force": None,
                    "note": kyqualify.PROJECT_SETTINGS_NOTE}
    assert clean.receipt["binds"]["project_settings_sha256"] == want
    for name in projects:
        record = json.loads((clean.evidence / "runs" / name / "run.json").read_text())
        assert record["project"] is True and record["project_settings_copy"] == want
    # the copy is bytes, never parsed or printed: its env block is in no receipt and no hashed evidence file
    hashed = "".join((clean.evidence / rel).read_text(errors="replace") for rel in clean.receipt["evidence"]["files"])
    assert "pr0ject-env-value" not in hashed + clean.out.read_text() + clean.done.stdout + clean.done.stderr
    assert "SOME_PROJECT_ENV" not in hashed + clean.out.read_text()


def test_evidence_is_hashed_and_the_receipt_matches_its_schema(clean):
    ev = clean.receipt["evidence"]
    assert ev["dir"] == str(clean.evidence) and "runs/base/stdout.jsonl" in ev["files"]
    assert "launch_config.json" in ev["files"] and "facts.json" in ev["files"] and len(ev["files"]) >= 4 * 15
    assert not any("/tmp/" in rel or "/job_scratch/" in rel or rel.startswith("canary/") for rel in ev["files"])
    for rel, digest in ev["files"].items():
        assert sha(clean.evidence / rel) == digest, rel
    for entry in clean.receipt["checks"].values():
        assert all(rel in ev["files"] for rel in entry["evidence"])
    schema = qualification_schema()
    assert kyschema.validate(schema, clean.receipt) == []
    broken = copy.deepcopy(clean.receipt)
    broken["checks"]["sign_in"]["result"] = "PASSED"
    del broken["binds"]["argv"]
    assert len(kyschema.validate(schema, broken)) == 2
    for key in ("project_settings_sha256", "zdotdir_sha256", "harness_sha256"):       # the R6 binds are not optional
        broken = copy.deepcopy(clean.receipt)
        del broken["binds"][key]
        assert len(kyschema.validate(schema, broken)) == 1, key


# ------------------------------------------------------------- project settings in force (ruling R6, finding Q-01)

def test_a_project_deny_rule_flips_an_intended_tool_to_fail(rig):
    rig.project_settings({"permissions": {"deny": ["Bash(printf*)", "Edit(CANARY_*)"]}})
    r, rc, _ = rig.qualify()                # bypassPermissions: only the project's own deny rules stand in the way
    tools = rc["checks"]["intended_tools"]["observed"]["tools"]
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert {t: v["result"] for t, v in tools.items()} == {"Read": "pass", "Write": "fail", "Edit": "fail", "Bash": "fail"}
    assert tools["Bash"]["permission_denials"] == ["Bash"] and tools["Bash"]["effect"] is False
    assert {n for n, v in results(rc).items() if v == "fail"} == {"intended_tools"}
    rig.project_settings({"permissions": {"deny": ["Bash(*printenv*)"]}})     # the same configuration, another project
    r, rc, _ = rig.qualify()
    assert r.returncode == PASS and rc["result"] == "PASS"


def test_a_project_allow_rule_flips_a_denied_command_to_fail(rig):
    rig.user_settings(USER_HOOKS)
    cfg = rig.config("reviewer.json", **REVIEWER)
    r, rc, _ = rig.qualify(cfg)             # the reviewer as templated, under the default project settings
    commands = rc["checks"]["denied_bash"]["observed"]["commands"]
    assert r.returncode == PASS and rc["result"] == "PASS", r.stderr
    assert rc["checks"]["denied_bash"]["required"] is True and sorted(commands) == sorted(DENIED_BASH)
    assert all(v == dict(v, result="pass", effect=False, denial=["permission_denial"], attempted=True,
                         changed_files=[], repository_changed=[], tool_error="permission denied", other_commands=[])
               for v in commands.values())
    assert rc["negative_probes"]["denied_tools"]["result"] == "pass"
    # (a) the project starts allowing a command nothing in the configuration denies: it runs
    allowing = copy.deepcopy(PROJECT_SETTINGS)
    allowing["permissions"]["allow"].append("Bash(touch*)")
    rig.project_settings(allowing)
    r, rc, ev = rig.qualify(cfg)
    touch = rc["checks"]["denied_bash"]["observed"]["commands"]["touch DENIED_CANARY.txt"]
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert touch["result"] == "fail" and touch["effect"] is True and touch["changed_files"] == ["DENIED_CANARY.txt"]
    assert touch["denial"] == [] and (ev / "canary" / "denybash-1" / "DENIED_CANARY.txt").exists()
    assert rc["negative_probes"]["denied_tools"]["result"] == "fail"
    assert {n for n, v in results(rc).items() if v == "fail"} == {"denied_bash"}
    # (b) verbs the project allows, in a configuration that forgot to deny them: the project's allow rule lets them run
    rig.project_settings()
    weak = [t for t in REVIEWER["disallowed_tools"] if t not in ("Bash(git add*)", "Bash(git commit*)")]
    r, rc, _ = rig.qualify(rig.config(**dict(REVIEWER, disallowed_tools=weak)))
    commands = rc["checks"]["denied_bash"]["observed"]["commands"]
    assert r.returncode == FAIL and commands["touch DENIED_CANARY.txt"]["result"] == "pass"
    assert commands["git add -A"]["result"] == "fail" and commands["git add -A"]["repository_changed"] == ["index"]
    assert commands["git commit --allow-empty -m canary"]["result"] == "fail"
    assert commands["git commit --allow-empty -m canary"]["repository_changed"] == ["head", "refs"]
    # (c) without the project's allow rules the same weak configuration is refused by the default mode instead
    rig.project_settings({"permissions": {"allow": ["Read(**)"]}})
    r, rc, _ = rig.qualify(rig.config(**dict(REVIEWER, disallowed_tools=weak)))
    assert r.returncode == PASS and results(rc)["denied_bash"] == "pass"


def test_check_refuses_once_the_worktrees_project_settings_change(rig):
    cfg, out = rig.config(), rig.tmp / "receipt.json"
    r, rc, _ = rig.qualify(cfg, out=out)
    assert r.returncode == PASS and rig.check(out, cfg)[0].returncode == 0
    settings = rig.proj / ".claude" / "settings.json"
    original = settings.read_bytes()
    settings.write_bytes(original + b"\n")                 # one byte of drift
    r, said = rig.check(out, cfg)
    assert r.returncode == 1 and said["reasons"] == ["binds differ: project_settings_sha256"]
    settings.unlink()                                      # … or the file going away
    assert rig.check(out, cfg)[1]["reasons"] == ["binds differ: project_settings_sha256"]
    settings.write_bytes(original)
    assert rig.check(out, cfg)[0].returncode == 0


def test_a_worktree_without_project_settings_is_bound_as_absent(rig):
    settings = rig.project_settings(absent=True)
    cfg, out = rig.config(), rig.tmp / "receipt.json"
    r, rc, ev = rig.qualify(cfg, out=out)
    assert r.returncode == PASS and rc["binds"]["project_settings_sha256"] == "absent"
    assert rc["observations"]["project_settings"]["sha256"] == "absent"
    assert rc["observations"]["project_settings"]["copies_intact"] is True
    assert not list((ev / "canary").rglob("settings.json")) and not (rig.proj / ".claude").exists()
    assert all(c["project_settings"] is None for c in rig.calls())
    assert kyschema.validate(qualification_schema(), rc) == []
    assert rig.check(out, cfg, "--verify-evidence")[0].returncode == 0
    rig.project_settings()                                 # a settings file appears afterwards
    assert rig.check(out, cfg)[1]["reasons"] == ["binds differ: project_settings_sha256"]
    settings.unlink()
    settings.mkdir()                                       # something is there that cannot be bound: refuse, launch nothing
    before = len(rig.calls())
    r, rc, _ = rig.qualify(cfg)
    assert r.returncode == 65 and rc is None and "cannot be bound" in r.stderr and len(rig.calls()) == before


def test_check_refuses_when_the_zdotdir_or_the_user_instructions_change(rig):
    cfg, out = rig.config(), rig.tmp / "receipt.json"
    r, rc, _ = rig.qualify(cfg, out=out)
    assert r.returncode == PASS

    def reasons():
        return rig.check(out, cfg)[1]["reasons"]

    zshenv = rig.root / "zdotdir" / ".zshenv"
    original = zshenv.read_bytes()
    zshenv.write_bytes(original + b"export EXTRA=1\n")
    assert reasons() == ["binds differ: zdotdir_sha256"]
    zshenv.write_bytes(original)
    (rig.root / "zdotdir" / ".zshrc").write_text("")       # a new file counts by its name, even empty
    assert reasons() == ["binds differ: zdotdir_sha256"]
    (rig.root / "zdotdir" / ".zshrc").unlink()
    (rig.root / "zdotdir" / "sub").mkdir()                 # only regular files directly inside are hashed
    (rig.root / "zdotdir" / "sub" / "x").write_text("x")
    assert reasons() == []
    # a symbolic link is not a regular file: the digest skips it (as kyloop.py's and kyboot.py's must), and so
    # nothing would bind what it points at — check and qualify refuse it by name instead
    digest = kyqualify.directory_digest(str(rig.root / "zdotdir"))
    (rig.root / "zdotdir" / ".zlogin").symlink_to(rig.tmp / "elsewhere.zsh")
    assert kyqualify.directory_digest(str(rig.root / "zdotdir")) == digest
    assert reasons() == ["zdotdir: it holds symbolic link(s) (.zlogin) that zdotdir_sha256 does not cover"]
    before = len(rig.calls())
    r, refused, _ = rig.qualify(cfg)
    assert r.returncode == 65 and refused is None and "symbolic link(s) (.zlogin)" in r.stderr and len(rig.calls()) == before
    (rig.root / "zdotdir" / ".zlogin").unlink()
    assert reasons() == []
    user_md = rig.home / ".claude" / "CLAUDE.md"
    text = user_md.read_text()
    user_md.write_text(text + "- a new owner rule\n")
    assert reasons() == ["binds differ: user_claude_md_sha256"]
    user_md.unlink()
    assert reasons() == ["binds differ: user_claude_md_sha256"]
    user_md.write_text(text)
    assert reasons() == []
    shutil.rmtree(rig.root / "zdotdir")
    assert reasons() == ["binds differ: zdotdir_sha256"]
    assert kyqualify.directory_digest(str(rig.root / "zdotdir")) == "absent"
    assert kyqualify.directory_digest(str(rig.card)) is None                  # a file where a directory is expected
    r, rc, _ = rig.qualify(cfg)                            # no ZDOTDIR directory at all is bound as such
    assert r.returncode == PASS and rc["binds"]["zdotdir_sha256"] == "absent"
    assert rc["checks"]["excluded_user_shell_profile"]["result"] == "pass"    # nothing is read from a missing ZDOTDIR


def test_check_refuses_a_receipt_judged_by_another_harness(rig):
    harness = rig.tmp / "harness"
    harness.mkdir()
    for name in ("kyqualify.py", "kyprobe.py"):
        shutil.copyfile(FLEET / name, harness / name)
    script, cfg, out = harness / "kyqualify.py", rig.config(), rig.tmp / "receipt.json"
    r, rc, _ = rig.qualify(cfg, out=out, script=script)
    assert r.returncode == PASS and rc["binds"]["harness_sha256"] == sha(script) == sha(KYQUALIFY)
    assert rig.check(out, cfg, script=script)[0].returncode == 0
    (harness / "kyprobe.py").write_text((harness / "kyprobe.py").read_text() + "\n# changed\n")
    assert rig.check(out, cfg, script=script)[1]["reasons"] == [
        "harness: the receipt was not judged by this kyqualify.py and kyprobe.py"]
    script.write_text(script.read_text() + "\n# changed\n")
    assert rig.check(out, cfg, script=script)[1]["reasons"] == [
        "binds differ: harness_sha256", "harness: the receipt was not judged by this kyqualify.py and kyprobe.py"]


def test_loop_roles_bind_only_what_kyloop_compares_plus_the_three_r6_keys(rig):
    caller = {"HOME": str(rig.home), "USER": "tester", "KY_ROOT": str(rig.root)}
    loop = kyqualify.compute_binds(rig.doc(role="planner"), caller)
    other = kyqualify.compute_binds(rig.doc(role="surrogate"), caller)
    assert set(loop) == BIND_KEYS | NEW_BIND_KEYS
    assert set(other) - set(loop) == USER_BIND_KEYS | {"add_dirs"} == set(kyqualify.LOOP_UNBOUND)
    assert {k: v for k, v in other.items() if k in loop} == loop and None not in loop.values()
    assert kyqualify.compute_binds(rig.doc(role="conductor"), caller) == loop


# ---------------------------------------------------------------------------------- each check, shown flipping

def test_not_signed_in_fails(rig):
    rig.configure(logged_in=False)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["checks"]["sign_in"]["result"] == "fail" and rc["checks"]["sign_in"]["observed"]["not_logged_in"] is True
    assert rc["checks"]["intended_tools"]["result"] == "fail"           # nothing landed
    assert rc["checks"]["model_identity"]["result"] == "unknown"        # never observed, never assumed
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
        "model_identity": "fail", "denied_tools": "unknown", "denied_bash": "unknown",
        "input_overhead_worktree": "unknown"}
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


def test_a_tool_disallowed_by_name_that_the_program_still_offers_never_earns_pass(rig):
    """review round 4, Q4-01: the builder disallows thirteen tools by name and has no canary for them"""
    r, rc, _ = rig.qualify(rig.config(disallowed_tools=BUILDER_OFF))     # the default: names are honoured
    denied = rc["checks"]["denied_tools"]
    assert r.returncode == PASS and denied["required"] is True and denied["result"] == "pass"
    assert denied["observed"]["disallowed_names"] and denied["observed"]["disallowed_tools_still_offered"] == []
    assert rc["negative_probes"]["denied_tools"]["result"] == "pass"     # no longer skipped as "denies nothing"
    rig.configure(disallow_mode="deny_on_call")                           # the program stops honouring the names
    r, rc, _ = rig.qualify(rig.config(disallowed_tools=BUILDER_OFF))
    denied = rc["checks"]["denied_tools"]
    assert denied["observed"]["disallowed_tools_still_offered"] == denied["observed"]["disallowed_names"]
    assert denied["result"] == "unknown" and rc["negative_probes"]["denied_tools"]["result"] == "unknown"
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"


@pytest.mark.parametrize("mode", ["not_offered", "deny_on_call"])
def test_denied_tools_need_no_effect_and_an_observed_denial(rig, mode):
    rig.configure(disallow_mode=mode)
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    denied, off = rc["checks"]["denied_tools"], REVIEWER_OFF + BASH_DENY
    assert denied["required"] is True
    # Every tool disallowed BY NAME is judged from the program's own list: absent = cleared; still listed = only
    # a canary that showed its denial clears it. Write and Edit have canaries; the other names do not.
    assert denied["result"] == ("pass" if mode == "not_offered" else "unknown")
    assert rc["negative_probes"]["denied_tools"]["result"] == ("pass" if mode == "not_offered" else "unknown")
    assert denied["observed"]["disallowed_names"] == sorted(REVIEWER_OFF)
    assert all(v["result"] == "pass" for v in denied["observed"]["tools"].values())      # the two canaries themselves
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
        assert r.returncode == UNKNOWN and rc["result"] == "unknown"     # names still listed without a canary
    assert rc["binds"]["disallowed_tools"] == off and rc["binds"]["extra_flags"] == [ALLOW]
    # bare disallowed names the program still lists (rules are not names) — judged above, never merely recorded
    assert denied["observed"]["disallowed_tools_still_offered"] == ([] if mode == "not_offered" else sorted(REVIEWER_OFF))
    assert rc["offered_tools"] == [t for t in REAL_TOOLS if mode == "deny_on_call" or t not in REVIEWER_OFF]
    argv = rc["binds"]["argv"]
    assert argv[10:16] == ["--max-turns", "60", ALLOW, "--strict-mcp-config", "--mcp-config", str(rig.mcp)]
    assert argv.count(ALLOW) == 1 and argv[16:17 + len(off)] == ["--disallowedTools"] + off     # each rule its own argument
    assert argv[17 + len(off):] == ["--output-format", "stream-json", "--verbose", "--add-dir", str(rig.root)]
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


# ------------------------------------------------------------- denied commands (ruling R7, finding Q-02)

DENIED_BASH_CASES = [
    # name, fake, what every command must read, why
    ("the denial is reported but the command runs", {"deny_leaks": True}, "fail", "took effect"),
    ("refused without any reported denial", {"denial_silent": True}, "unknown", "no permission denial names it"),
    ("the model never calls the command", {"bash_idle": True}, "unknown", "it was never called"),
]


@pytest.mark.parametrize("name,fake,verdict,why", DENIED_BASH_CASES, ids=[c[0] for c in DENIED_BASH_CASES])
def test_a_denied_command_passes_only_with_no_effect_and_an_observed_denial(rig, name, fake, verdict, why):
    rig.user_settings(USER_HOOKS)           # as in the passing reviewer run: only the fake's behaviour differs
    rig.configure(**fake)
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    check = rc["checks"]["denied_bash"]
    commands = check["observed"]["commands"]
    assert check["required"] is True and check["result"] == verdict and rc["result"] != "PASS" and r.returncode != PASS
    assert {c: v["result"] for c, v in commands.items()} == {c: verdict for c in DENIED_BASH}
    assert all(why in v["why"] for v in commands.values())
    assert rc["negative_probes"]["denied_tools"]["result"] == verdict
    if verdict == "fail":                   # each effect is seen where it lands: a file, the index, HEAD and its ref
        assert commands["touch DENIED_CANARY.txt"]["changed_files"] == ["DENIED_CANARY.txt"]
        assert commands["git add -A"]["repository_changed"] == ["index"]
        assert commands["git commit --allow-empty -m canary"]["repository_changed"] == ["head", "refs"]
        assert all(v["denial"] == ["permission_denial"] for v in commands.values())      # reported, and yet it ran
    else:
        assert all(v["effect"] is False and v["denial"] == [] for v in commands.values())
        assert all(v["attempted"] is (name != "the model never calls the command") for v in commands.values())


def test_a_denied_command_that_is_allowed_and_leaves_no_trace_is_unknown_never_pass(rig):
    rig.user_settings(USER_HOOKS)
    cfg = rig.config(**dict(REVIEWER, denied_bash=["git status", "touch DENIED_CANARY.txt"]))
    r, rc, _ = rig.qualify(cfg)             # `git status` is on the reviewer's own allow list: it runs, changes nothing
    commands = rc["checks"]["denied_bash"]["observed"]["commands"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    assert commands["git status"]["result"] == "unknown" and commands["git status"]["attempted"] is True
    assert commands["git status"]["effect"] is False and "may have run without a visible effect" in commands["git status"]["why"]
    assert commands["touch DENIED_CANARY.txt"]["result"] == "pass"
    assert {n for n, v in results(rc).items() if n in REQUIRED + ["denied_tools"] and v != "pass"} == set()
    # A command that ran and FAILED comes back as a tool error too. That is not a denial: `git push` is allowed by
    # the project, the configuration forgot to deny it, it runs in the scratch repository and fails for want of a remote.
    weak = [t for t in REVIEWER["disallowed_tools"] if t != "Bash(git push*)"]
    r, rc, _ = rig.qualify(rig.config(**dict(REVIEWER, disallowed_tools=weak, denied_bash=["git push"])))
    push = rc["checks"]["denied_bash"]["observed"]["commands"]["git push"]
    assert r.returncode == UNKNOWN and push["result"] == "unknown" and push["denial"] == [] and push["effect"] is False
    assert push["attempted"] is True and push["tool_error"].startswith("Exit code ")
    # with the deny rule in place the very same command is refused, and that is a pass
    r, rc, _ = rig.qualify(rig.config(**dict(REVIEWER, denied_bash=["git push"])))
    push = rc["checks"]["denied_bash"]["observed"]["commands"]["git push"]
    assert r.returncode == PASS and push["result"] == "pass" and push["denial"] == ["permission_denial"]


def test_check_covers_the_denied_commands_the_configuration_declares(rig):
    rig.user_settings(USER_HOOKS)
    cfg, out = rig.config(**REVIEWER), rig.tmp / "receipt.json"
    r, rc, _ = rig.qualify(cfg, out=out)
    assert r.returncode == PASS and rig.check(out, cfg, "--verify-evidence")[0].returncode == 0
    r, said = rig.check(out, rig.config(**dict(REVIEWER, denied_bash=DENIED_BASH + ["git push"])))
    assert r.returncode == 1 and said["reasons"] == [
        "denied_bash: the receipt covers the commands %s, the configuration declares %s"
        % (sorted(DENIED_BASH), sorted(DENIED_BASH + ["git push"]))]
    fewer = {k: v for k, v in REVIEWER.items() if k != "denied_bash"}
    r, said = rig.check(out, rig.config(**fewer))
    assert r.returncode == 1 and said["reasons"][0].startswith("denied_bash: the receipt covers the commands")
    # the scratch repositories lived in canary projects: settings copy, one commit, one untracked file
    repo = Path(rc["evidence"]["dir"]) / "canary" / "denybash-2"
    assert (repo / ".git").is_dir() and (repo / ".claude" / "settings.json").read_bytes() == \
        (rig.proj / ".claude" / "settings.json").read_bytes()
    assert sorted(p.name for p in repo.iterdir()) == [".claude", ".git", "TRACKED.txt", "UNTRACKED_CANARY.txt"]


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
    assert kyschema.validate(qualification_schema(), rc) == []
    # only event names and matcher strings ever leave the user's settings file
    written = out.read_text() + "".join(p.read_text(errors="replace") for p in ev.rglob("*") if p.is_file())
    assert "s3cr3t" not in written and "SOME_TOKEN" not in written and "defaultMode" not in written
    for c in rig.calls():
        want = set(BOOT_ENV) - ({"ZDOTDIR"} if c["zdotdir"] is None else set())
        assert set(c["env_names"]) - {"__CF_USER_TEXT_ENCODING"} == want
    assert rig.check(out, cfg, "--verify-evidence")[0].returncode == 0
    r, said = rig.check(out, rig.config(**dict(REVIEWER, bash_canary="write")))
    assert r.returncode == 1 and "bash_canary: the receipt used 'readonly'" in r.stdout


def test_a_cannot_fire_hook_verdict_is_bound_to_the_users_hook_structure(rig):
    rig.user_settings(USER_HOOKS)
    cfg, out = rig.config(**REVIEWER), rig.tmp / "receipt.json"
    r, rc, _ = rig.qualify(cfg, out=out)
    hooks = rc["checks"]["excluded_user_hooks"]["observed"]
    digest = kyqualify.hooks_digest(kyqualify.user_hook_config(str(rig.home))[0])
    assert r.returncode == PASS and hooks["basis"] == "cannot_fire"
    assert hooks["meaning"].startswith("irrelevant, not excluded") and "user_settings_hooks_sha256" in hooks["meaning"]
    assert hooks["user_settings_hooks_sha256"] == rc["binds"]["user_settings_hooks_sha256"] == digest
    assert digest == hashlib.sha256(json.dumps(
        [["PostToolUse", "Edit|Write"], ["PostToolUse", "Write"], ["PreToolUse", "Edit|Write|MultiEdit"]],
        separators=(",", ":")).encode()).hexdigest()       # event names and matchers, nothing else
    # what is not a hook event name or matcher is not bound: another key, or a hook's command, may change
    quiet = copy.deepcopy(USER_HOOKS)
    quiet["PreToolUse"][0]["hooks"][0]["command"] = "echo another-command"
    rig.user_settings(quiet, model="some-model")
    assert rig.check(out, cfg)[0].returncode == 0
    rig.user_settings(dict(USER_HOOKS, Stop=[{"hooks": []}]))           # a hook that needs no tool appears
    stale = "excluded_user_hooks: the user's hook events or matchers are no longer the ones the 'cannot_fire' verdict was read from"
    assert rig.check(out, cfg)[1]["reasons"] == ["binds differ: user_settings_hooks_sha256", stale]
    forged = copy.deepcopy(rc)              # moving the bind along does not move the verdict's own record
    forged["binds"]["user_settings_hooks_sha256"] = kyqualify.hooks_digest(kyqualify.user_hook_config(str(rig.home))[0])
    path = rig.tmp / "forged.json"
    path.write_text(json.dumps(forged))
    assert rig.check(path, cfg)[1]["reasons"] == [stale]
    rig.user_settings(raw="{ not JSON")
    assert rig.check(out, cfg)[1]["reasons"] == ["binds differ: user_settings_hooks_sha256", stale]
    rig.user_settings(USER_HOOKS)
    assert rig.check(out, cfg)[0].returncode == 0


def test_a_hook_seen_running_fails_even_when_the_structure_says_it_cannot(rig):
    rig.user_settings(USER_HOOKS)
    rig.configure(session_hook=True, hooks_leak=True)     # a hook that needs no tool runs in the lean configuration
    r, rc, _ = rig.qualify(rig.config(**REVIEWER))
    hooks = rc["checks"]["excluded_user_hooks"]
    assert rc["result"] == "FAIL" and hooks["result"] == "fail"
    assert hooks["observed"]["lean"] == ["SessionStart"] and hooks["observed"]["basis"] == "hook_observed"


def test_a_hook_under_project_settings_that_define_hooks_is_not_blamed_on_the_user(rig):
    with_hooks = dict(PROJECT_SETTINGS, hooks={"PreToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "true"}]}]})
    rig.project_settings(with_hooks)        # in force in the canary project now, so its hook fires on the Write canary
    r, rc, _ = rig.qualify()
    hooks = rc["checks"]["excluded_user_hooks"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown" and hooks["result"] == "unknown"
    assert hooks["observed"]["basis"] == "hook_observed_unattributed" and hooks["observed"]["lean"] == ["PreToolUse"]
    assert hooks["observed"]["project_hook_events"] == ["PreToolUse"]
    assert {n for n, v in results(rc).items() if n in REQUIRED and v != "pass"} == {"excluded_user_hooks"}


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
    assert rc["binds"]["user_settings_hooks_sha256"] == "unreadable" and "s3cr3t" not in json.dumps(rc)
    assert kyschema.validate(qualification_schema(), rc) == []
    assert {n for n, v in results(rc).items() if v == "unknown"} == {"excluded_user_hooks", "denied_tools", "denied_bash"}


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
        assert kyqualify.hooks_digest(config) == "unreadable"
    rig.user_settings(USER_HOOKS)
    settings.chmod(0)
    try:
        assert kyqualify.user_hook_config(str(rig.home)) == (None, "the user's settings file cannot be read")
    finally:
        settings.chmod(0o600)
    # the digest is over the sorted (event, matcher) pairs: order in the file does not matter, a matcher does
    one = kyqualify.hooks_digest([("PreToolUse", "Write"), ("Stop", None)])
    assert one == kyqualify.hooks_digest([("Stop", None), ("PreToolUse", "Write")])
    assert one != kyqualify.hooks_digest([("PreToolUse", "Write|Edit"), ("Stop", None)])
    assert one != kyqualify.hooks_digest([("PreToolUse", "Write")]) != kyqualify.hooks_digest([])


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
        "excluded_user_shell_profile": "unknown", "denied_tools": "unknown", "denied_bash": "unknown"}
    assert all(c["argv"][c["argv"].index("--setting-sources") + 1] == "project" for c in rig.calls())
    assert all(c["zdotdir"] for c in rig.calls())           # no run without ZDOTDIR either


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


# ------------------------------------------------------------- what else reaches the job (findings Q-08, Q-11)

def test_user_level_instruction_sources_are_reported_and_bound_never_required(rig):
    user_md = rig.home / ".claude" / "CLAUDE.md"
    r, rc, _ = rig.qualify()
    seen = rc["observations"]
    assert r.returncode == PASS
    assert seen["user_claude_md_in_context"] is False and seen["auto_memory_path_present"] is True
    assert seen["user_claude_md_sha256"] == rc["binds"]["user_claude_md_sha256"] == sha(user_md)
    assert seen["offered_tools_without_canary"] == [t for t in REAL_TOOLS if t not in ("Read", "Write", "Edit", "Bash")]
    rig.configure(load_user_md=True, auto_memory=False)   # the user's own instructions do reach the job
    r, rc, _ = rig.qualify()
    assert r.returncode == PASS and rc["result"] == "PASS"                    # reported, and that is all
    assert rc["observations"]["user_claude_md_in_context"] is True
    assert rc["observations"]["auto_memory_path_present"] is False
    assert "observations" not in json.dumps(kyqualify.required_checks(rig.doc(), "launchd"))
    user_md.unlink()                        # nothing to look for: unknown, never "false"
    r, rc, _ = rig.qualify()
    assert r.returncode == PASS and rc["observations"]["user_claude_md_in_context"] == "unknown"
    assert rc["observations"]["user_claude_md_sha256"] == rc["binds"]["user_claude_md_sha256"] == "absent"
    assert kyschema.validate(qualification_schema(), rc) == []
    # the surrogate is offered Edit without intending it: named, not judged
    r, rc, _ = rig.qualify(rig.config(role="surrogate", intended_tools=["Read", "Write", "Bash"]))
    assert "Edit" in rc["observations"]["offered_tools_without_canary"]


def test_the_users_shell_profile_is_shown_absent_under_zdotdir_or_not_shown_at_all(rig, clean):
    seen = clean.receipt["checks"]["excluded_user_shell_profile"]
    assert seen["required"] is False and seen["result"] == "pass"
    assert seen["observed"]["control_only"] == ["/user/profile/bin"]         # what the user's own profile adds
    assert seen["observed"]["shell_path"][0] == "/fleet/zdotdir/bin"         # what the fleet's ZDOTDIR adds
    assert seen["observed"]["outside_child_path"] == ["/fleet/zdotdir/bin"]
    assert seen["observed"]["shell_path"][1:] == clean.receipt["binds"]["child_path"].split(":")
    control = [c for c in clean.calls() if c["zdotdir"] is None]
    assert len(control) == 1 and control[0]["cwd"].endswith("/shell-path-control")
    assert not (clean.home / ".zshenv").exists() and (clean.home / ".zprofile").read_text().count("\n") == 1   # nothing planted
    # a shell that reads the user's profile whatever ZDOTDIR says: the same PATH both times shows nothing
    rig.configure(zdotdir_ignored=True)
    r, rc, _ = rig.qualify()
    seen = rc["checks"]["excluded_user_shell_profile"]
    assert seen["result"] == "unknown" and seen["observed"]["control_only"] == []
    assert "/user/profile/bin" in seen["observed"]["shell_path"] and "loaded either way" in seen["observed"]["why"]
    assert r.returncode == PASS             # reported, not required
    # the canary's command refused: nothing printed, nothing shown
    rig.configure()
    rig.project_settings({"permissions": {"deny": ["Bash(printf 'KYQ-PATH*)"]}})
    r, rc, _ = rig.qualify()
    seen = rc["checks"]["excluded_user_shell_profile"]
    assert seen["result"] == "unknown" and seen["observed"]["shell_path"] is None and "printed no PATH" in seen["observed"]["why"]
    # no ZDOTDIR in the configuration, or no shell: nothing to run, and the check says why
    rig.project_settings()
    rig.bindir.joinpath("calls.jsonl").unlink()
    r, rc, _ = rig.qualify(rig.config(env_names=[n for n in ENV_NAMES if n != "ZDOTDIR"]))
    seen = rc["checks"]["excluded_user_shell_profile"]
    assert seen["result"] == "unknown" and "ZDOTDIR is not part" in seen["observed"]["why"]
    assert not any((c["command"] or "").startswith("printf 'KYQ-PATH") for c in rig.calls())
    r, rc, _ = rig.qualify(rig.config(intended_tools=["Read", "Write", "Edit"]))
    assert "starts no shell" in rc["checks"]["excluded_user_shell_profile"]["observed"]["why"]


def test_the_python3_shell_canaries_serve_a_role_whose_shell_allows_little_else(rig):
    rig.user_settings(USER_HOOKS)
    r, rc, ev = rig.qualify(rig.config(**REVIEWER))
    assert r.returncode == PASS
    commands = {c["command"] for c in rig.calls() if c["kind"] in ("bash", "sleep")}
    assert 'python3 -c "import time; time.sleep(600)"' in commands and "sleep 600" not in commands
    assert "python3 -c \"import os; print('KYQ-PATH=' + os.environ.get('PATH', ''))\"" in commands
    assert rc["checks"]["excluded_user_shell_profile"]["observed"]["control_only"] == ["/user/profile/bin"]
    for probe in ("timeout", "termination"):
        assert rc["negative_probes"][probe]["observed"]["tool_children_at_kill"] == 1
    # with the plain wording the reviewer's shell refuses the long command: no tool child, so nothing was shown
    r, rc, _ = rig.qualify(rig.config(**{k: v for k, v in REVIEWER.items() if k != "shell_canary"}))
    assert r.returncode == UNKNOWN and results(rc, "negative_probes")["timeout"] == "unknown"
    assert "ended by itself" in rc["negative_probes"]["timeout"]["why"]


# ------------------------------------------------------------------------------ each negative probe, flipping

def test_missing_authentication_probe_that_still_signs_in_fails(rig):
    rig.configure(auth_ignores_home=True)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)       # only the probe says no
    probe = rc["negative_probes"]["missing_authentication"]
    assert probe["result"] == "fail" and probe["observed"]["sign_in"] == "works" and "empty" in probe["why"]


def test_only_the_not_logged_in_signal_counts_as_missing_authentication(rig):
    rig.configure(unsigned_error="API Error: 429 rate_limit_error")     # the empty-HOME run fails, but not for sign-in
    r, rc, _ = rig.qualify()
    probe = rc["negative_probes"]["missing_authentication"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    assert probe["result"] == "unknown" and "rate limit" in probe["why"]
    assert probe["observed"]["sign_in"] == "fails" and probe["observed"]["not_logged_in"] is False
    assert probe["observed"]["exit_code"] == 1 and probe["observed"]["error_text"].startswith("API Error: 429")
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    assert {n for n, p in rc["negative_probes"].items() if p["result"] == "unknown"} == {"missing_authentication"}
    rig.configure()                         # the specific signal: pass, and it says which signal
    r, rc, _ = rig.qualify()
    probe = rc["negative_probes"]["missing_authentication"]
    assert r.returncode == PASS and probe["result"] == "pass" and probe["observed"]["not_logged_in"] is True
    assert probe["observed"]["error_text"].startswith("Not logged in")
    # the configuration's own run failing that way is not "not signed in" either: unknown, with the reason
    rig.configure(error_on={"ctx": "API Error: 529 overloaded"})
    r, rc, _ = rig.qualify()
    sign_in = rc["checks"]["sign_in"]
    assert sign_in["result"] == "unknown" and "rate limit" in sign_in["observed"]["why"]
    assert sign_in["observed"]["not_logged_in"] is False and rc["result"] != "PASS" and r.returncode != PASS


def test_invalid_settings_that_are_accepted_fail(rig):
    rig.configure(invalid_mcp="accepted")
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    assert rc["negative_probes"]["invalid_settings"]["result"] == "fail"
    assert {n for n, p in rc["negative_probes"].items() if p["result"] == "fail"} == {"invalid_settings"}


def test_invalid_settings_pass_only_on_a_launch_that_never_became_a_session(rig):
    rig.configure(invalid_mcp="late")       # a session starts and then fails: an outage looks exactly like this
    r, rc, _ = rig.qualify()
    probe = rc["negative_probes"]["invalid_settings"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown" and probe["result"] == "unknown"
    assert probe["observed"]["init_event"] is True and probe["observed"]["exit_code"] == 1 and "outage" in probe["why"]
    assert {n for n, p in rc["negative_probes"].items() if p["result"] == "unknown"} == {"invalid_settings"}
    rig.configure()
    r, rc, _ = rig.qualify()
    probe = rc["negative_probes"]["invalid_settings"]
    assert probe["result"] == "pass" and probe["observed"]["init_event"] is False and probe["observed"]["exit_code"] == 1


def test_timeout_and_termination_probes_need_a_run_that_was_really_killed(rig):
    rig.configure(ignore_sleep=True)        # the canary ends by itself: no timeout, no termination was produced
    r, rc, _ = rig.qualify(args=("--probe-timeout", "10"))
    probes = results(rc, "negative_probes")
    assert (probes["timeout"], probes["termination"], probes["restart"]) == ("unknown", "unknown", "unknown")
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"


def test_the_kill_probes_wait_for_a_live_tool_child_and_say_so(clean):
    for probe, run, flag in (("timeout", "neg-timeout", "timed_out"), ("termination", "neg-term", "terminated_by_signal")):
        entry = clean.receipt["negative_probes"][probe]
        seen = entry["observed"]
        record = json.loads((clean.evidence / "runs" / run / "run.json").read_text())
        assert entry["result"] == "pass" and "live tool child" in entry["why"] and seen[flag] is True
        assert seen["descendants_at_kill"] >= 1 and seen["tool_children_at_kill"] == 1
        assert record["live_marker"] == "sleep 600" and record["kill"] == ("timeout" if probe == "timeout" else "term")
        # the kill came --probe-timeout (0.8 s here) after the child was first seen running, not at a fixed moment
        assert record["live_child_seen_after"] is not None
        assert record["ended_by_harness_after"] - record["live_child_seen_after"] >= 0.8 - 0.002      # both rounded
        assert seen["ended_after_seconds"] == record["ended_by_harness_after"]
        assert record["tool_children_at_kill"] == [p for p in clean.sleep_pids() if p in record["descendants_at_kill"]]
    assert not any(alive(p) for p in clean.sleep_pids())


def test_a_kill_that_lands_on_a_run_without_a_live_tool_child_is_unknown(rig):
    rig.configure(sleep_child=False)        # the tool call is streamed, the run hangs — but no command is running
    r, rc, ev = rig.qualify(args=("--probe-wait", "1.2"))
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    for probe, run, flag in (("timeout", "neg-timeout", "timed_out"), ("termination", "neg-term", "terminated_by_signal")):
        entry = rc["negative_probes"][probe]
        seen = entry["observed"]
        record = json.loads((ev / "runs" / run / "run.json").read_text())
        assert entry["result"] == "unknown" and "no tool child was running when the kill landed" in entry["why"]
        # the harness did end it, and its group is gone: what was shown is an idle run being ended
        assert seen[flag] is True and seen["group_gone"] is True and seen["signals_sent"] == ["SIGTERM"]
        assert seen["descendants_at_kill"] == 0 and seen["tool_children_at_kill"] == 0
        assert seen["live_child_seen_after_seconds"] is None and record["tool_uses"] == ["Bash"]
        assert 1.2 <= seen["ended_after_seconds"] < 5
    assert rc["negative_probes"]["restart"]["result"] == "pass"      # the restart did follow a termination
    assert {n for n, p in rc["negative_probes"].items() if p["result"] == "unknown"} == {"timeout", "termination"}
    # some other descendant being alive is not the tool child either: the canary's own command must be running
    rig.configure(sleep_child=False, helper_child=True)
    r, rc, ev = rig.qualify(args=("--probe-wait", "1.2"))
    assert r.returncode == UNKNOWN and rc["result"] == "unknown"
    for probe in ("timeout", "termination"):
        entry = rc["negative_probes"][probe]
        assert entry["result"] == "unknown" and "no tool child was running" in entry["why"]
        assert entry["observed"]["descendants_at_kill"] == 1 and entry["observed"]["tool_children_at_kill"] == 0
        assert entry["observed"]["group_gone"] is True
    assert not any(alive(p) for p in rig.sleep_pids())


def test_a_group_that_ignores_term_is_killed_and_recorded(rig):
    rig.configure(trap_term=True)
    r, rc, ev = rig.qualify(args=("--probe-timeout", "1.5", "--term-grace", "0.5"))
    assert r.returncode == PASS and rc["result"] == "PASS", r.stderr
    for probe, run in (("timeout", "neg-timeout"), ("termination", "neg-term")):
        seen = rc["negative_probes"][probe]["observed"]
        assert seen["signals_sent"] == ["SIGTERM", "SIGKILL"] and seen["group_gone"] is True
        assert seen["descendants_at_kill"] == 1 and seen["descendants_survived_group_kill"] == []
        assert seen["tool_children_at_kill"] == 1
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


def test_a_configuration_without_a_shell_has_no_tool_child_to_end(rig):
    r, rc, ev = rig.qualify(rig.config(intended_tools=["Read", "Write", "Edit"]))
    assert r.returncode == PASS
    for probe, run in (("timeout", "neg-timeout"), ("termination", "neg-term")):
        entry = rc["negative_probes"][probe]
        assert entry["result"] == "pass" and "no shell tool" in entry["why"]
        assert entry["observed"]["tool_children_at_kill"] == "not applicable"
        assert "live_marker" not in json.loads((ev / "runs" / run / "run.json").read_text())


def test_hook_exclusion_needs_an_attempted_write_in_the_configuration_itself(rig):
    rig.configure(lean_hook_run_idle=True)  # the control shows the hook, but the lean run never tried to write
    r, rc, _ = rig.qualify()
    hooks = rc["checks"]["excluded_user_hooks"]
    assert hooks["result"] == "unknown" and hooks["observed"]["lean_write_attempted"] is False
    assert hooks["observed"]["control"] == ["PreToolUse"] and r.returncode == UNKNOWN and rc["result"] == "unknown"


def test_a_bound_file_that_changes_during_the_run_refuses(rig):
    rig.configure(touch_on_ctx=str(rig.card))
    r, rc, _ = rig.qualify()
    assert r.returncode == 74 and rc is None and "changed during the run (prompt_sha256)" in r.stderr
    rig.configure(touch_on_ctx=str(rig.proj / ".claude" / "settings.json"))     # … the project settings included
    r, rc, _ = rig.qualify()
    assert r.returncode == 74 and rc is None and "changed during the run (project_settings_sha256)" in r.stderr


def test_restart_after_termination_must_succeed(rig):
    rig.configure(ready_fails=True)
    r, rc, _ = rig.qualify()
    assert r.returncode == FAIL and rc["result"] == "FAIL"
    assert rc["negative_probes"]["termination"]["result"] == "pass"
    assert rc["negative_probes"]["restart"]["result"] == "fail"
    assert rc["checks"]["no_tty_prompt"]["result"] == "pass"       # it exited by itself, with a result event


def test_the_keychain_probe_is_an_exemption_recorded_as_such(clean, rig):
    listed = clean.receipt["exemptions"]
    assert [e["probe"] for e in listed] == ["inaccessible_keychain", "denied_tools"]
    keychain = listed[0]
    assert keychain["result"] == "not_simulated" and "credentials" in keychain["reason"] and keychain["note"] is None
    assert keychain["basis"].startswith("exempt by a recorded cockpit note, not by an observation")
    assert listed[1]["basis"].startswith("nothing to probe")
    rig.user_settings(USER_HOOKS)
    note = rig.tmp / "KEYCHAIN_NOTE.md"
    note.write_text("Q-05: the cockpit accepts that the inaccessible-keychain probe is not simulated.\n")
    r, rc, _ = rig.qualify(rig.config(**REVIEWER), args=("--exemption-note", note))
    assert r.returncode == PASS
    assert [e["probe"] for e in rc["exemptions"]] == ["inaccessible_keychain"]     # this configuration does deny
    assert rc["exemptions"][0]["note"] == {"path": str(note), "sha256": sha(note)}
    assert kyschema.validate(qualification_schema(), rc) == []
    r, rc, _ = rig.qualify(args=("--exemption-note", rig.tmp / "NO_NOTE.md"))
    assert r.returncode == 65 and rc is None and "--exemption-note" in r.stderr
    # an exemption is a named gap, not a pass: no other probe may be skipped that way
    assert kyqualify.skippable_probes(rig.doc()) == {"inaccessible_keychain", "denied_tools"}
    assert kyqualify.skippable_probes(rig.doc(**REVIEWER)) == {"inaccessible_keychain"}
    assert kyqualify.skippable_probes(rig.doc(denied_bash=["touch X"])) == {"inaccessible_keychain"}


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
    assert kyschema.validate(qualification_schema(), rc) == []
    # the caller's KY_* values reached the children although the plist carries PATH/HOME/USER/LANG only
    assert {c["ky_root"] for c in rig.calls()} == {str(rig.root)}
    assert {c["ky_scratch"] for c in rig.calls()} == {str(rig.tmp / "campaign-scratch")}
    assert rc["binds"]["zdotdir_sha256"] == kyqualify.directory_digest(str(rig.root / "zdotdir"))
    r, said = rig.check(out, cfg, "--require-context", "launchd", "--verify-evidence")
    assert r.returncode == 0, r.stdout
    assert said["evidence"]["not_rejudged"]["launchd_context"].startswith("the launchd receipt")
    assert rig.check(out, cfg, "--require-context", "shell")[0].returncode == 1


def test_a_replaced_launchctl_is_recorded_and_never_earns_pass_outside_the_test_gate(rig):
    fake, cfg, out = str(rig.bindir / "launchctl"), rig.config(), rig.tmp / "receipt.json"
    no_gate = {"KY_QUALIFY_TEST_OVERRIDE": None}
    r, rc, _ = rig.qualify(cfg, context="launchd", out=out, extra_env=no_gate)      # the same fake, without the gate
    seen = rc["checks"]["launchd_context"]
    assert r.returncode == UNKNOWN and rc["result"] == "unknown" and seen["result"] == "unknown"
    assert seen["observed"]["launchctl"] == fake and seen["observed"]["launchctl_replaced"] is True
    assert seen["observed"]["test_override"] is False and "replaced through KY_LAUNCHCTL" in seen["observed"]["why"]
    assert rc["launchd_receipt"]["launchctl"] == fake and rc["launchd_receipt"]["test_override"] is False
    # everything a fake can stage was staged — PID 1 as parent, the label, bootout — and it still proves nothing
    assert seen["observed"]["parent_pid"] == 1 and seen["observed"]["xpc_service_name"] == LABEL
    assert seen["observed"]["absent_after_bootout"] is True
    assert all(v == "pass" for n, v in results(rc).items() if n in REQUIRED)
    assert rig.check(out, cfg, extra_env=no_gate)[0].returncode == 1
    # under the gate the tests can earn PASS, the receipt says how, and `check` outside the gate refuses it
    r, rc, _ = rig.qualify(cfg, context="launchd", out=out)
    assert r.returncode == PASS and rc["launchd_receipt"]["launchctl"] == fake
    assert rc["launchd_receipt"]["test_override"] is True and rc["checks"]["launchd_context"]["observed"]["test_override"] is True
    assert rig.check(out, cfg, "--require-context", "launchd")[0].returncode == 0
    r, said = rig.check(out, cfg, "--require-context", "launchd", extra_env=no_gate)
    assert r.returncode == 1 and said["reasons"] == [
        "launchctl: the receipt was earned with %r, not /bin/launchctl; a replaced launchctl qualifies nothing outside the tests" % fake]
    # the gate in the checking process alone is not enough either: the receipt must say it was earned under it
    forged = copy.deepcopy(rc)
    forged["launchd_receipt"]["test_override"] = False
    path = rig.tmp / "forged.json"
    path.write_text(json.dumps(forged))
    assert rig.check(path, cfg)[1]["reasons"][0].startswith("launchctl: the receipt was earned with")
    # … and a receipt that names the system's launchctl while its evidence does not is caught by the evidence
    forged = copy.deepcopy(rc)
    forged["launchd_receipt"]["launchctl"] = "/bin/launchctl"
    path.write_text(json.dumps(forged))
    r, said = rig.check(path, cfg, "--verify-evidence", extra_env=no_gate)
    assert r.returncode == 1 and "evidence: launchd/LAUNCHD_RECEIPT.json is not the receipt's launchd receipt" in said["reasons"]
    # launchctl is never looked up on PATH
    r, rc, _ = rig.qualify(cfg, context="launchd", extra_env={"KY_LAUNCHCTL": "launchctl"})
    assert r.returncode == 65 and rc is None and "absolute" in r.stderr
    assert kyqualify.SYSTEM_LAUNCHCTL == "/bin/launchctl"
    assert kyqualify.kyprobe.launchctl_choice({}) == ("/bin/launchctl", False, False, None)
    assert kyqualify.kyprobe.launchctl_choice({"KY_QUALIFY_TEST_OVERRIDE": "1"}) == ("/bin/launchctl", False, False, None)
    assert kyqualify.kyprobe.launchctl_choice({"KY_LAUNCHCTL": "/x/launchctl"}) == ("/x/launchctl", True, False, None)


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
    rig.configure(hang_on=["ctx", "read", "write", "edit", "bash", "ready", "sleep"])
    out, ev = rig.tmp / "never.json", rig.tmp / "interrupted"
    env = {"HOME": str(rig.home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin", "KY_ROOT": str(rig.root)}
    proc = subprocess.Popen([sys.executable, "-B", str(KYQUALIFY), "qualify", "--config", str(rig.config()), "--context", "shell",
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
    r, said = clean.check(clean.out, clean.cfg)
    assert r.returncode == 0, r.stdout + r.stderr
    assert said == {"check": "PASS", "context": "shell", "reasons": [], "receipt": str(clean.out)}
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
    ({"disallowed_tools": ["Bash(git push*)"]}, "argv, disallowed_tools"),
    ({"add_dirs": []}, "add_dirs, argv"),
    ({"mcp_config": "COPY"}, "argv"),
    ({"claude_bin": "LINK"}, "argv, claude_bin"),
    ({"deadline_seconds": 14401}, "deadline_seconds"),
    ({"worktree": "OTHER"}, "project_settings_sha256, worktree"),
    ({"env_names": ENV_NAMES + ["KY_ITEM"]}, "env_names"),
    ({"env_names": [n for n in ENV_NAMES if n != "JOB_SCRATCH"]}, "env_names"),
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
    if change.get("worktree") == "OTHER":                  # another checkout, with no project settings of its own
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
    code, why = verdict(lambda d: None, clean.config(denied_bash=["touch DENIED_CANARY.txt"]))
    assert code == 1 and "denied_bash: the receipt covers the commands []" in why and "result" in why
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


def test_verify_evidence_rejudges_from_the_streams_and_says_what_it_could_not(clean, rig):
    r, said = clean.check(clean.out, clean.cfg, "--verify-evidence")
    assert r.returncode == 0 and said["reasons"] == [], r.stdout
    seen = said["evidence"]
    assert sorted(seen["rejudged_from_streams"]) == sorted(kyqualify.REJUDGED_FROM_STREAMS)
    assert set(seen["rejudged_with_recorded_observations"]) == set(kyqualify.REJUDGED_WITH_RECORD)
    assert set(seen["not_rejudged"]) == {"timeout", "termination", "inaccessible_keychain", "binds"}
    assert "process observations" in seen["not_rejudged"]["timeout"]
    # every verdict of the receipt is in exactly one of the three lists
    named = set(seen["rejudged_from_streams"]) | set(seen["rejudged_with_recorded_observations"]) | set(seen["not_rejudged"])
    assert named == set(clean.receipt["checks"]) | set(clean.receipt["negative_probes"]) - {"denied_tools"} | {"probe:denied_tools", "binds"}

    def forged(change, relist=("runs/base/stdout.jsonl", "runs/base/run.json")):
        """a copy of the evidence, edited, with the receipt's hash list brought along — as a forger would"""
        directory = rig.tmp / ("forged-%d" % len(list(rig.tmp.glob("forged-*"))))
        shutil.copytree(clean.evidence, directory)
        change(directory)
        doc = copy.deepcopy(clean.receipt)
        doc["evidence"]["dir"] = str(directory)
        for rel in relist:
            doc["evidence"]["files"][rel] = sha(directory / rel)
        path = directory / "receipt.json"
        path.write_text(json.dumps(doc))
        return path

    def other_model(directory):
        stream = directory / "runs" / "base" / "stdout.jsonl"
        text = stream.read_text()
        assert text.count('"model": "claude-opus-5-5"') == 1
        stream.write_text(text.replace('"model": "claude-opus-5-5"', '"model": "claude-haiku-5-5"'))

    path = forged(other_model)              # the stream is edited; hash comparison alone sees nothing wrong
    assert clean.check(path, clean.cfg)[0].returncode == 0                       # without the flag nothing reads it
    r, said = clean.check(path, clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and said["reasons"] == [
        "evidence: runs/base/run.json does not say what its streams show (observed, stdout_sha256)",
        "re-judged: checks.model_identity is 'fail' from the evidence, the receipt says 'pass'"]

    def other_model_everywhere(directory):  # … and the run record edited to agree with the edited stream
        other_model(directory)
        record_path = directory / "runs" / "base" / "run.json"
        record = json.loads(record_path.read_text())
        record["observed"]["model"] = "claude-haiku-5-5"
        record["stdout_sha256"] = sha(directory / "runs" / "base" / "stdout.jsonl")
        record_path.write_text(json.dumps(record))

    r, said = clean.check(forged(other_model_everywhere), clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and said["reasons"] == [
        "re-judged: checks.model_identity is 'fail' from the evidence, the receipt says 'pass'"]

    def no_effect(directory):               # a recorded observation: the Write canary's file was never what was asked
        record_path = directory / "runs" / "tool-write" / "run.json"
        record = json.loads(record_path.read_text())
        record["disk"]["target_is_nonce"] = False
        record_path.write_text(json.dumps(record))

    r, said = clean.check(forged(no_effect, relist=("runs/tool-write/run.json",)), clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and said["reasons"] == [
        "re-judged: checks.intended_tools is 'fail' from the evidence, the receipt says 'pass'"]

    def other_project(directory):           # a canary that did not run under the bound project settings
        record_path = directory / "runs" / "tool-bash" / "run.json"
        record = json.loads(record_path.read_text())
        record["project_settings_copy"] = "absent"
        record_path.write_text(json.dumps(record))

    r, said = clean.check(forged(other_project, relist=("runs/tool-bash/run.json",)), clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and "evidence: runs/tool-bash did not run under the bound project settings" in said["reasons"]
    assert "re-judged: observations are not what the evidence shows" in said["reasons"]

    def no_facts(directory):
        (directory / "facts.json").unlink()

    r, said = clean.check(forged(no_facts, relist=()), clean.cfg, "--verify-evidence")
    assert r.returncode == 1 and any("facts.json" in reason for reason in said["reasons"])
    # another configuration's evidence is not this configuration's
    r, said = clean.check(clean.out, clean.config(max_turns=151), "--verify-evidence")
    assert "evidence: launch_config.json is not this configuration" in said["reasons"]


@pytest.mark.parametrize("role", ["planner", "conductor"])
def test_loop_python_shell_canary_receipt_satisfies_the_controller(rig, monkeypatch, role):
    import kyloop

    assert tuple(kyloop.ROLES) == tuple(kyqualify.LOOP_ROLES)
    fleet, run_dir = rig.root / "fleet_live", rig.root / "run"
    (fleet / "prompts").mkdir(parents=True)
    run_dir.mkdir()
    (fleet / "prompts" / kyloop.PROMPTS[role]).write_text("# loop prompt\n")
    (fleet / "mcp.none.json").write_text('{"mcpServers":{}}\n')
    for name, value in (("KY_ROOT", rig.root), ("KY_RUN", run_dir), ("KY_FLEET", fleet),
                        ("CLAUDE_BIN", rig.bindir / "claude"), ("HOME", rig.home)):
        monkeypatch.setenv(name, str(value))
    controller = kyloop.Controller(role)
    loop_cfg = dict(kyloop.DEFAULTS[role], worktree=str(rig.proj), mcp_config=str(fleet / "mcp.none.json"))
    (run_dir / "loops.json").write_text(json.dumps({role: {"worktree": loop_cfg["worktree"],
                                                         "mcp_config": loop_cfg["mcp_config"]}}))
    extra_env = {"KY_RUN": str(run_dir), "KY_FLEET": str(fleet), "CLAUDE_BIN": str(rig.bindir / "claude")}
    printed = rig.run("admin", "launch-config", role, script=FLEET / "kyloop.py", extra_env=extra_env)
    assert printed.returncode == 0, printed.stderr
    launch = json.loads(printed.stdout)
    assert launch.get("shell_canary") == "python3"
    assert launch == controller.launch_config(loop_cfg)
    cfg = rig.config(role=role, model=loop_cfg["model"], effort=loop_cfg["effort"],
                     permission_mode=loop_cfg["permission_mode"], max_turns=loop_cfg["max_turns"],
                     deadline_seconds=loop_cfg["deadline_seconds"], mcp_config=loop_cfg["mcp_config"],
                     prompt_path=str(fleet / "prompts" / kyloop.PROMPTS[role]),
                     env_names=list(kyloop.CHILD_ENV_NAMES), child_path=controller.child_path(),
                     add_dirs=[str(rig.root)], shell_canary="python3")
    out = controller.qualification_path(loop_cfg)
    assert controller.check_qualification(loop_cfg) == ["qualification_missing: %s" % out]
    r, rc, _ = rig.qualify(cfg, out=out, extra_env={"KY_RUN": str(run_dir), "KY_FLEET": str(fleet)})
    assert r.returncode == PASS, r.stderr
    expected = controller.expected_binds(loop_cfg)
    # The loop roles' key set is the fourteen kyloop has always compared plus the three of ruling R6 — nothing of
    # what the other roles bind beyond that (add_dirs, the user-level hashes): kyloop compares key for key.
    assert set(rc["binds"]) == BIND_KEYS | NEW_BIND_KEYS
    # every key kyloop computes is in the receipt with kyloop's own value; the only key it may leave to the harness
    # is harness_sha256 (it computes that one only when kyqualify.py is installed beside it, as it is here)
    assert {key: value for key, value in rc["binds"].items() if key in expected} == expected
    assert set(rc["binds"]) - set(expected) <= {"harness_sha256"}
    assert rc["binds"]["argv"] == controller.argv(loop_cfg)
    assert controller.check_qualification(loop_cfg) == []
    if hasattr(controller, "launch_config"):                 # the configuration kyloop hands to check_receipt
        assert controller.launch_config(loop_cfg) == json.loads(Path(cfg).read_text())
    assert all(set(c["env_names"]) - {"__CF_USER_TEXT_ENCODING"} | {"ZDOTDIR"} == set(kyloop.CHILD_ENV_NAMES) for c in rig.calls())
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
    ("unknown shell canary", lambda d: d.update(shell_canary="perl"), "shell_canary"),
    ("no denied command", lambda d: d.update(denied_bash=[]), "denied_bash"),
    ("denied command twice", lambda d: d.update(denied_bash=["touch X", "touch X"]), "denied_bash"),
    ("denied command with shell syntax", lambda d: d.update(denied_bash=["touch X; touch Y"]), "denied_bash"),
    ("denied command with a redirect", lambda d: d.update(denied_bash=["echo x > X"]), "denied_bash"),
    ("denied command with a variable", lambda d: d.update(denied_bash=["touch $HOME"]), "denied_bash"),
    ("denied command with a path", lambda d: d.update(denied_bash=["touch sub/X"]), "denied_bash"),
    ("denied command reaching the home", lambda d: d.update(denied_bash=["touch ~x"]), "denied_bash"),
    ("denied command reaching upwards", lambda d: d.update(denied_bash=["touch .. X"]), "denied_bash"),
    ("denied command with doubled spaces", lambda d: d.update(denied_bash=["touch  X"]), "denied_bash"),
    ("denied command ending in a space", lambda d: d.update(denied_bash=["touch X "]), "denied_bash"),
    ("too many denied commands", lambda d: d.update(denied_bash=["touch X%d" % n for n in range(13)]), "denied_bash"),
]


@pytest.mark.parametrize("name,mutate,needle", BAD_SHAPES, ids=[b[0] for b in BAD_SHAPES])
def test_launch_configuration_shape_is_strict_in_the_validator_and_in_the_schema(rig, name, mutate, needle):
    schema = json.loads((SCHEMAS / "launch_config.json").read_text())
    for good in (rig.doc(), rig.doc(bash_canary="readonly", extra_flags=[ALLOW]), rig.doc(**REVIEWER),
                 rig.doc(shell_canary="plain", denied_bash=["git commit --allow-empty -m canary", "npm run x=1"])):
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
    assert refused(disallowed_tools=["Bash(git push*)", "Bash(*--output*)"]) == ""          # a rule is not the tool
    assert "denied_bash: Bash is not an intended tool" in refused(intended_tools=["Read"], denied_bash=["touch X"])
    # KY_* names: conventional value, else the caller's, else refused — and nothing else ever. TMPDIR and
    # JOB_SCRATCH are filled per run; KY_SCRATCH is the campaign scratch root (rework ruling R1).
    names = ENV_NAMES + ["KY_PY", "KY_ROLE", "KY_ITEM", "KY_STREAM"]
    env, errs = kyqualify.resolve_env(rig.doc(env_names=names),
                                      {"HOME": "/h", "USER": "u", "KY_ROOT": "/k", "ZDOTDIR": "/mine", "LANG": "C"})
    assert errs == ["env value policy unknown: KY_STREAM (no conventional value and the caller's environment does not set it)"]
    env, errs = kyqualify.resolve_env(rig.doc(env_names=names),
                                      {"HOME": "/h", "USER": "u", "KY_ROOT": "/k", "ZDOTDIR": "/mine", "LANG": "C",
                                       "KY_STREAM": "S-1", "KY_FLEET": "/elsewhere", "JOB_SCRATCH": "/callers/own"})
    assert errs == [] and env == {
        "HOME": "/h", "USER": "u", "LANG": "en_US.UTF-8", "TERM": "dumb", "TMPDIR": None, "JOB_SCRATCH": None,
        "PATH": "%s/bin:/opt/homebrew/bin:/usr/bin:/bin" % rig.root, "KY_ROOT": "/k", "KY_RUN": "/k/run",
        "KY_FLEET": "/elsewhere", "ZDOTDIR": "/k/zdotdir", "KY_PY": "/k/venv/bin/python",
        "KY_SCRATCH": "/Users/Dev/scratch.noindex/claude/madhav/%s-kalayantra-v3" % time.strftime("%Y%m%d"),
        "KY_ROLE": "bootstrap-builder", "KY_ITEM": "KV3-B-QUALIFY", "KY_STREAM": "S-1"}   # names bound, values per job
    assert kyqualify.resolve_env(rig.doc(env_names=names), {"HOME": "/h", "USER": "u", "KY_STREAM": "S", "KY_ITEM": "KV3-B-7"})[0]["KY_ITEM"] == "KV3-B-7"
    assert kyqualify.resolve_env(rig.doc(), {"HOME": "/h", "USER": "u", "KY_SCRATCH": "/campaign"})[0]["KY_SCRATCH"] == "/campaign"
    assert "no Bash canary" in refused(intended_tools=["Read"], bash_canary="readonly")
    # the worktree's project settings must be bindable: a regular, readable file — or not there at all
    settings = rig.proj / ".claude" / "settings.json"
    settings.unlink()
    assert refused() == ""
    settings.mkdir()
    assert "project settings cannot be bound" in refused()
    settings.rmdir()
    settings.symlink_to(rig.tmp / "nowhere.json")
    assert "project settings cannot be bound" in refused()
    settings.unlink()
    rig.project_settings()
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
                          "BOOTSTRAP.md", {"shell_canary": "python3"}),
    "bootstrap-reviewer": ("default", 60, 3600, BOOT_ENV, [ALLOW], REVIEWER_OFF + BASH_DENY, ["Read", "Bash"], ["Write", "Edit"],
                           "BOOTSTRAP_REVIEWER.md", {"bash_canary": "readonly", "shell_canary": "python3",
                                                     "denied_bash": DENIED_BASH}),
    "area-reviewer": ("default", 120, 7200, BOOT_ENV, [ALLOW], REVIEWER_OFF + BASH_DENY, ["Read", "Bash"], ["Write", "Edit"],
                      "BOOTSTRAP_REVIEWER.md", {"bash_canary": "readonly", "shell_canary": "python3",
                                                "denied_bash": DENIED_BASH}),
    "surrogate": ("bypassPermissions", 30, 1800, SURROGATE_ENV, [], BUILDER_OFF, ["Read", "Write", "Bash"], [],
                  "OWNER_SURROGATE.md", {"shell_canary": "python3"}),
}


@pytest.mark.parametrize("role", sorted(TEMPLATE_FACTS))
def test_wave_b_templates_are_valid_launch_configurations(role, tmp_path):
    mode, turns, deadline, env_names, extra, disallowed, intended, denied, card, optional = TEMPLATE_FACTS[role]
    doc = json.loads((TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role)).read_text())
    schema = json.loads((SCHEMAS / "launch_config.json").read_text())
    assert kyschema.validate(schema, doc) == []
    assert kyqualify.validate_config(doc, check_disk=False) == []
    fleet = doc["mcp_config"].rsplit("/", 1)[0]
    assert fleet.endswith("/00_ARCHITECTURE/briefs/kalayantra/fleet") and doc["worktree"] == fleet.rsplit("/", 4)[0]
    assert {k: v for k, v in doc.items() if k != "_note"} == dict({
        "schema": "ky.launch_config/1", "role": role,
        "model": "claude-fable-5-1" if role == "surrogate" else "claude-opus-5-5", "effort": "high",
        "permission_mode": mode, "max_turns": turns, "deadline_seconds": deadline, "worktree": doc["worktree"],
        "claude_bin": "/Users/Dev/.local/bin/claude", "mcp_config": fleet + "/mcp.none.json",
        "prompt_path": fleet + "/cards/" + card, "env_names": env_names,
        "child_path": "/Users/Dev/kalayantra/bin:/opt/homebrew/bin:/usr/bin:/bin", "extra_flags": extra,
        "disallowed_tools": disallowed, "add_dirs": ["/Users/Dev/kalayantra"], "intended_tools": intended,
        "denied_tools": denied}, **optional)
    assert "_note" in doc      # every template says why it is shaped as it is (reviewer: boundary; all: the python3 canary)
    names = [t for t in disallowed if "(" not in t]
    assert all(t in REAL_TOOLS for t in names) and "Agent" not in names                 # real tool names only
    # rework ruling R1: every job carries its own scratch directory and the campaign scratch root
    assert {"JOB_SCRATCH", "KY_SCRATCH"} <= set(doc["env_names"])
    argv = kyqualify.build_argv(doc)
    assert argv[:12] == ["/Users/Dev/.local/bin/claude", "-p", "--setting-sources", "project", "--permission-mode", mode,
                         "--model", "claude-fable-5-1" if role == "surrogate" else "claude-opus-5-5",
                         "--effort", "high", "--max-turns", str(turns)]
    assert argv[12:-5] == extra + ["--strict-mcp-config", "--mcp-config", doc["mcp_config"], "--disallowedTools"] + disallowed
    assert argv[-5:] == ["--output-format", "stream-json", "--verbose", "--add-dir", "/Users/Dev/kalayantra"]
    assert all(argv.count(flag) == 1 and argv.index(flag) < argv.index("--strict-mcp-config") for flag in extra)
    assert "--bare" not in argv and "--dangerously-skip-permissions" not in argv
    # every environment name has a value without the caller supplying anything (KY_ITEM takes the qualification
    # value; TMPDIR and JOB_SCRATCH are filled per run)
    env, errs = kyqualify.resolve_env(doc, {"HOME": "/h", "USER": "u"})
    assert errs == [] and sorted(env) == sorted(env_names) and env["JOB_SCRATCH"] is None
    assert env["KY_SCRATCH"].startswith("/Users/Dev/scratch.noindex/claude/madhav/")
    assert env.get("KY_ITEM") in (None, "KV3-B-QUALIFY") and env.get("KY_PY") in (None, "/Users/Dev/kalayantra/venv/bin/python")
    if os.path.isdir(doc["worktree"]) and os.path.exists(doc["claude_bin"]):        # on the campaign host itself
        # The reviewer card is written by the cards area in this same rework round: until it lands the template's
        # own prompt_path does not exist, so everything else is checked against the disk with a card of this test.
        own_card = tmp_path / "CARD.md"
        own_card.write_text("# a card of this test\n")
        assert kyqualify.validate_config(dict(doc, prompt_path=str(own_card))) == []
        assert json.loads(Path(doc["mcp_config"]).read_text()) == {"mcpServers": {}}
        if os.path.exists(doc["prompt_path"]):
            assert kyqualify.validate_config(doc) == []


def test_the_reviewer_template_says_what_it_is_and_denies_what_ruling_r7_lists():
    doc = json.loads((TEMPLATES / "LAUNCH_CONFIG.bootstrap-reviewer.json").read_text())
    rules = [t for t in doc["disallowed_tools"] if t.startswith("Bash(")]
    assert rules == BASH_DENY and len(rules) == 22
    verbs = ("add", "commit", "push", "merge", "switch", "checkout", "worktree", "branch", "reset", "rebase", "stash",
             "tag", "fetch", "pull", "config", "remote")
    assert rules[:16] == ["Bash(git %s*)" % verb for verb in verbs]
    assert rules[16:] == ["Bash(*--output*)", "Bash(gh *)", "Bash(npm *)", "Bash(psql*)", "Bash(launchctl*)", "Bash(curl*)"]
    allowed = doc["extra_flags"][0].split("=", 1)[1].split(",")
    assert "Bash(plutil -lint*)" in allowed and not any(rule.startswith("Bash(plutil:") for rule in allowed)
    assert "Bash(python3:*)" in allowed                    # stays, recorded for an owner-surrogate decision
    assert doc["denied_bash"] == ["touch DENIED_CANARY.txt", "git add -A", "git commit --allow-empty -m canary"]
    assert doc["prompt_path"].endswith("/fleet/cards/BOOTSTRAP_REVIEWER.md")
    note = doc["_note"]
    assert "Bash(python3:*) permits writes" in note and "Not read-only and not sandboxed" in note
    assert "B-1 deliverable" in note and "placeholder" not in note
    # each default denied command is refused by a rule of this very template, or by the default mode alone
    import fnmatch
    for command, by_rule in (("touch DENIED_CANARY.txt", False), ("git add -A", True), ("git commit --allow-empty -m canary", True)):
        assert any(fnmatch.fnmatchcase(command, rule[5:-1]) for rule in rules) is by_rule, command
        assert not any(fnmatch.fnmatchcase(command, rule[5:-1]) or (rule.endswith(":*)") and command.startswith(rule[5:-3]))
                       for rule in allowed), command


def job_launcher_helpers():
    """Read the real shell launcher's Python helper without executing its CLI or any child."""
    source = (FLEET / "kyjob.sh").read_text().split("\n#>>> kyjob helper\n", 1)[1].split(
        "\n#<<< kyjob helper\n", 1)[0]
    tree = ast.parse(source)
    assert ast.unparse(tree.body[-1]) == "sys.exit(main(ARGV))"
    tree.body.pop()
    namespace = {"__file__": str(FLEET / "kyjob.sh")}
    exec(compile(tree, str(FLEET / "kyjob.sh"), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("role,parent,card", [("build", "bootstrap-builder", "KARAKA.md"),
                                             ("verify", "bootstrap-reviewer", "PARIKSAKA.md")])
def test_live_bootstrap_job_templates_match_the_actual_launcher(role, parent, card, tmp_path, monkeypatch):
    from types import SimpleNamespace
    import datetime
    import kyd_admit
    import kyd_jobs
    import kymanifest

    cfg = json.loads((TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role)).read_text())
    baseline = json.loads((TEMPLATES / ("LAUNCH_CONFIG.%s.json" % parent)).read_text())
    assert kyschema.validate(json.loads((SCHEMAS / "launch_config.json").read_text()), cfg) == []
    assert kyqualify.validate_config(cfg, check_disk=False) == []
    for key in ("effort", "permission_mode", "max_turns", "deadline_seconds", "extra_flags", "disallowed_tools",
                "intended_tools", "denied_tools", "add_dirs", "shell_canary", "bash_canary", "denied_bash"):
        assert cfg.get(key) == baseline.get(key)
    assert cfg["role"] == role and cfg["model"] == "claude-opus-5-5"
    assert cfg["worktree"] == "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
    assert cfg["mcp_config"] == "/Users/Dev/kalayantra/fleet_live/mcp.none.json"
    assert cfg["prompt_path"] == "/Users/Dev/kalayantra/fleet_live/cards/" + card
    assert cfg["max_turns"] <= kyd_admit.TURN_CAPS[role.upper()]
    launcher = job_launcher_helpers()
    # Read nullability from the real packet and real job-state planner, not a retyped env-name list.
    packet = FLEET.parent / "packets" / "PACKET_KV3-B-OPS-CONTRACT_v1.md"
    front, reason = kyd_admit.front_matter(str(packet))
    assert reason is None and front["needs_chart_data"] is False
    tests, reason = kyd_admit.packet_tests(front)
    assert reason is None and tests == []
    ctx = SimpleNamespace(repo=str(tmp_path), controller_id="test-controller")
    intent = {"kind": role.upper(), "role": role, "item": front["id"], "key": "template-test",
              "claim": None, "locks": ["item." + front["id"]], "stream": "K" if role == "build" else "V",
              "pool": "builder" if role == "build" else "verifier", "header": {}}
    plan, reason = kyd_jobs._plan(ctx, intent, "b1" if role == "build" else "v1", {"tests": tests})
    assert reason is None
    state = plan["state"]
    state.update(tmp_path=str(tmp_path), job_scratch=str(tmp_path), job_id="template-test", PRAVAHA=[])
    own = {"HOME": str(tmp_path), "USER": "test", "KY_ROOT": "/Users/Dev/kalayantra",
           "KY_RUN": str(tmp_path), "KY_FLEET": str(FLEET), "KY_SCRATCH": str(tmp_path)}
    # Supply the recorded node directory to the real child_path reader without depending on the host's disk.
    node = cfg["child_path"].split(":")[1]
    (tmp_path / "NODE_BIN").write_text(node + "\n")
    original_isdir = launcher["os"].path.isdir
    monkeypatch.setattr(launcher["os"].path, "isdir", lambda path: path == node or original_isdir(path))
    env = launcher["job_environment"](state, own)
    assert cfg["env_names"] == [name for name, _ in env]
    assert cfg["child_path"] == dict(env)["PATH"]
    caller = dict(own, KY_STREAM=state["stream"], KY_LANE=state["slot"], KY_CONTROLLER_ID=ctx.controller_id)
    resolved, errors = kyqualify.resolve_env(cfg, caller)
    assert errors == [] and sorted(resolved) == sorted(cfg["env_names"])
    state.update(claude_bin=cfg["claude_bin"], model=cfg["model"], effort=cfg["effort"],
                 permission_mode=cfg["permission_mode"], max_turns=cfg["max_turns"], mcp_config=cfg["mcp_config"],
                 extra_lean_flags=cfg["extra_flags"], disallowed_tools=cfg["disallowed_tools"], KY_ROOT=own["KY_ROOT"])
    assert launcher["build_argv"](state) == kyqualify.build_argv(cfg)
    assert kymanifest.launch_config_of({"role": role}) == str(
        (TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role)).relative_to(FLEET.parents[3]))
    assert kymanifest.launch_config_of({"role": role}) in (FLEET / "BOOTSTRAP_COMPONENTS.txt").read_text().splitlines()

    # Contract-only receipt: test admission and every launch-time bind without fabricating earned evidence.
    run = tmp_path / "run"
    (run / "QUALIFICATIONS").mkdir(parents=True)
    state["worktree"] = str(tmp_path / "different-per-job-worktree")
    state["deadline"] = kyd_admit.deadline_text(datetime.datetime.now(datetime.timezone.utc), cfg["deadline_seconds"])
    facts = {"claude_bin_sha256": "a" * 64, "mcp_config_sha256": hashlib.sha256(
        (FLEET / "mcp.none.json").read_bytes()).hexdigest(), "harness_sha256": "b" * 64}
    binds = {"claude_bin": cfg["claude_bin"], "model": cfg["model"], "effort": cfg["effort"],
             "permission_mode": cfg["permission_mode"], "max_turns": cfg["max_turns"], **facts,
             "env_names": sorted(cfg["env_names"]), "child_path": cfg["child_path"],
             "project_settings_sha256": "absent",
             "zdotdir_sha256": kyqualify.directory_digest(own["KY_ROOT"] + "/zdotdir"),
             "deadline_seconds": cfg["deadline_seconds"], "argv": kyqualify.build_argv(cfg),
             "worktree": cfg["worktree"], "extra_flags": cfg["extra_flags"], "disallowed_tools": cfg["disallowed_tools"]}
    receipt = {"schema": "ky.qualification/1", "role": role, "model": cfg["model"], "result": "PASS",
               "context": "launchd", "binds": binds}
    receipt_path = run / "QUALIFICATIONS" / (role + "-" + cfg["model"] + ".json")
    receipt_path.write_text(json.dumps(receipt))
    admission_ctx = SimpleNamespace(paths={"run": str(run), "fleet": str(FLEET)},
                                    now=lambda: datetime.datetime.now(datetime.timezone.utc))
    refusals, admitted_facts = [], {}
    kyd_admit._check_launch(admission_ctx, intent, "opus", front, True, refusals, admitted_facts)
    assert refusals == [] and admitted_facts["launch"]["max_turns"] == cfg["max_turns"]
    own["KY_RUN"] = str(run)
    assert launcher["check_qualification"](state, own, env, launcher["build_argv"](state), facts,
                                           launcher["parse_deadline"](state["deadline"]))[0] == binds
    for key in launcher["BOUND_FACTS"]:
        changed = dict(binds, **{key: None})
        receipt_path.write_text(json.dumps(dict(receipt, binds=changed)))
        with pytest.raises(launcher["Refuse"], match="binds\\." + key):
            launcher["check_qualification"](state, own, env, launcher["build_argv"](state), facts,
                                              launcher["parse_deadline"](state["deadline"]))
    receipt_path.write_text(json.dumps(receipt))
    listed = kymanifest.launch_config_of(receipt)
    with pytest.raises(kymanifest.Refused, match="not a bound component"):
        kymanifest.observe_qualifications(str(FLEET.parents[3]), str(run), bound=set())
    # An earned receipt must separately pass the real harness. Here isolate the manifest's routing/binding
    # contract: assert the exact checker call and template; this stand-in asserts no real qualification.
    calls = []

    def accepted_harness(argv, **kwargs):
        calls.append(argv)
        assert argv == [sys.executable, "-I", "-B", str(FLEET / "kyqualify.py"), "check", str(receipt_path),
                        "--config", str(TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role)),
                        "--require-context", "launchd"]
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(kymanifest.subprocess, "run", accepted_harness)
    observed = kymanifest.observe_qualifications(str(FLEET.parents[3]), str(run), bound={listed})
    assert len(calls) == 1 and observed[0]["config"] == listed


@pytest.mark.parametrize("engine", ["claude", "codex"])
def test_tests_environment_has_bounded_value_policy(engine):
    cfg = json.loads((TEMPLATES / ("LAUNCH_CONFIG.build.tests" + (".codex" if engine == "codex" else "") + ".json")).read_text())
    assert kyqualify.validate_config(cfg, check_disk=False) == []
    caller = {"HOME": "/h", "USER": "u", "KY_STREAM": "K", "KY_LANE": "b1", "KY_CONTROLLER_ID": "CTL-q"}
    env, errors = kyqualify.resolve_env(cfg, caller)
    assert errors == []
    assert env["TESTS"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyqualify.py"
    value = "tests/test_a.py\nplatform/tests/test_b.py"
    env, errors = kyqualify.resolve_env(cfg, dict(caller, TESTS=value))
    assert errors == [] and env["TESTS"] == value
    for bad in ("", "../outside.py", "/absolute.py", "tests/../escape.py", "a\r\nb", "a\x00b", "x" * 65537):
        assert any("TESTS" in e for e in kyqualify.resolve_env(cfg, dict(caller, TESTS=bad))[1])
    assert any("unknown" in e for e in kyqualify.validate_config(dict(cfg, env_names=cfg["env_names"] + ["UNKNOWN"]), check_disk=False))



def test_tests_caller_value_survives_launchd_with_exact_receipt_names(rig):
    value = "tests/test_one.py\ntests/test_two.py"
    cfg = rig.config(env_names=ENV_NAMES + ["TESTS"])
    result, receipt, evidence = rig.qualify(cfg, context="launchd", extra_env={"TESTS": value})
    assert result.returncode == PASS, result.stderr
    assert "TESTS" in receipt["binds"]["env_names"]
    calls = [c for c in rig.calls() if "TESTS" in c["env_names"]]
    assert calls and all(c["tests"] == value for c in calls)
