"""The second engine: kyqualify.py with an OpenAI Codex CLI launch configuration ("engine": "codex"). Every Codex
check and negative probe is shown to flip on a fake `codex` and a fake `launchctl` (root CLAUDE.md §N.8: a verdict
nothing could turn false is null). The real program and the real launchd are never called here: launchctl is the
ABSOLUTE fake named by KY_LAUNCHCTL, every qualification runs in the shell context, and the fake `codex` refuses
to run any launchctl but that fake.

The fake `codex` models what the brief expects of the real one (codex-cli 0.162.0-alpha.17.2), because the
qualification is about exactly that: `exec --json` prints thread.started / item.* / turn.completed lines; `-o`
receives the last agent message; -s read-only lets a command write nowhere, -s workspace-write lets it write in the
-C directory, every --add-dir and $TMPDIR; the network is reachable only under workspace-write with
sandbox_workspace_write.network_access=true; a launchctl call is blocked by the sandbox; the session record of the
thread is written to $HOME/.codex/sessions/<y>/<m>/<d>/rollout-…-<thread id>.jsonl with a turn_context carrying
model, effort, approval policy and sandbox policy; without the sign-in marker under $HOME/.codex the run fails with
"Not logged in". Each of those behaviours can be switched off in fake.json to show the detector reading no."""
import copy
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
KYQUALIFY = FLEET / "kyqualify.py"
SCHEMAS = FLEET / "schemas"
TEMPLATES = FLEET / "templates"
sys.path.insert(0, str(FLEET))

import kyqualify  # noqa: E402
import kyschema  # noqa: E402

FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, re, secrets, shlex, subprocess, sys, time
here = os.path.dirname(os.path.realpath(__file__))
cfg = json.load(open(os.path.join(here, "fake.json")))
a = sys.argv[1:]
if a == ["--version"]:
    print(cfg["version"]); sys.exit(0)
assert a[0] == "exec" and a[-1] == "-", a
def opt(name):
    return a[a.index(name) + 1] if name in a else None
def every(name):
    return [a[i + 1] for i, x in enumerate(a) if x == name]
conf = {}
for item in every("-c"):
    key, value = item.split("=", 1)
    conf[key] = value.strip('"')
sandbox, model, workdir = opt("-s"), opt("-m"), opt("-C")
network = sandbox == "workspace-write" and conf.get("sandbox_workspace_write.network_access") == "true"
roots = [workdir] + every("--add-dir") + ([os.environ["TMPDIR"]] if sandbox == "workspace-write" else [])
if sandbox == "workspace-write" and (conf.get("sandbox_workspace_write.exclude_slash_tmp") != "true"
                                     or cfg["slash_tmp_leaks"]):
    roots.append("/tmp")                      # the real program's default: /tmp is a writable root unless excluded
roots = [os.path.realpath(r) for r in roots if r]
for path, content in cfg["write"].items():    # a job that replaces a file it must leave alone
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
for path in cfg["touch"]:                     # a job that changes what it must leave alone
    with open(path, "a") as f:
        f.write("# changed by a job\n")
prompt = sys.stdin.read()
cm = re.search(r"(?:with your shell tool|wait for it to finish): (.*)\n", prompt)
command = cm.group(1) if cm else None
kind = "command" if command else "ctx" if "AGENTS.md" in prompt else "ready"
with open(os.path.join(here, "calls.jsonl"), "a") as f:
    f.write(json.dumps({"argv": a, "kind": kind, "command": command, "env_names": sorted(os.environ),
                        "cwd": os.getcwd(), "home": os.environ.get("HOME"), "tmpdir": os.environ.get("TMPDIR"),
                        "job_scratch": os.environ.get("JOB_SCRATCH")}) + "\n")
def out(ev):
    sys.stdout.write(json.dumps(ev) + "\n"); sys.stdout.flush()
thread = "0199c0de-0000-7000-8000-" + secrets.token_hex(6)
home = os.environ.get("HOME", "/nonexistent")
if not (cfg["logged_in"] and (cfg["auth_ignores_home"] or os.path.exists(os.path.join(home, ".codex", "signed_in")))):
    sys.stderr.write(cfg["unsigned_error"] + "\n")
    out({"type": "thread.started", "thread_id": thread})
    out({"type": "error", "message": cfg["unsigned_error"]})
    out({"type": "turn.failed", "error": {"message": cfg["unsigned_error"]}})
    sys.exit(1)
served = cfg["serve_model"] or model
out({"type": "thread.started", "thread_id": thread})
if cfg["rollout"]:
    day = os.path.join(home, ".codex", "sessions", "2026", "10", "12")
    os.makedirs(day, exist_ok=True)
    with open(os.path.join(day, "rollout-2026-10-12T00-00-00-%s.jsonl" % thread), "w") as f:
        f.write(json.dumps({"type": "session_meta", "payload": {"id": thread, "cwd": workdir}}) + "\n")
        if cfg["persistent"]:                   # the model's persistent-mode block, as a developer message
            f.write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": "<persistent_mode>You are now in persistent mode</persistent_mode>"}]}}) + "\n")
        f.write(json.dumps({"type": "turn_context", "payload": {
            "cwd": workdir, "model": served, "effort": conf.get("model_reasoning_effort"),
            "approval_policy": conf.get("approval_policy"),
            "sandbox_policy": {"mode": cfg["serve_sandbox"] or sandbox, "network_access": network}}}) + "\n")
out({"type": "turn.started"})
if kind in cfg["hang_on"]:
    time.sleep(600)
if cfg["mcp_call"]:
    out({"type": "item.completed", "item": {"id": "item_m", "type": "mcp_tool_call", "server": "db", "tool": "q",
                                            "status": "completed"}})
if cfg["extra_item"]:
    out({"type": "item.completed", "item": {"id": "item_x", "type": cfg["extra_item"], "status": "completed"}})
turns = [0]
def inside(path):
    real = os.path.realpath(path)
    return any(real == r or real.startswith(r + "/") for r in roots)
def shell(line, env=None):
    done = subprocess.run(["/bin/sh", "-c", line], capture_output=True, text=True, env=env)
    return done.returncode, done.stdout + done.stderr
def run_command(line):
    """(exit code, output) as the sandbox would let the command run"""
    m = re.match(r"^printf %s (\S+) > (.+)$", line)
    if m:
        target = shlex.split(m.group(2))[0]
        if inside(os.path.dirname(os.path.abspath(target)) or ".") and sandbox != "read-only" or cfg["sandbox_leaks"]:
            return shell(line)
        return 1, "sh: %s: Operation not permitted" % target
    if "launchctl" in line:
        program = shlex.split(line)[0]
        if not program.startswith(here + "/"):              # SAFETY: never any launchctl but the test's fake
            open(os.path.join(here, "VIOLATION"), "a").write(line + "\n")
            return 99, "refused by the fake: not the fake launchctl"
        if cfg["launchctl_blocked"]:
            return 1, "Bootstrap failed: 1: Operation not permitted"
        return shell(line)
    if line.startswith("curl "):
        if network or cfg["network_leaks"]:
            return shell(line)
        return 7, "curl: (7) Failed to connect to 127.0.0.1: Operation not permitted"
    if line.startswith("git commit"):
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True).stdout.strip()
        if not cfg["git_blocked"] and (sandbox == "workspace-write" and inside(".") and inside(common)
                                       or cfg["sandbox_leaks"]):
            return shell(line, dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1"))
        return 128, "fatal: Unable to create '%s/index.lock': Operation not permitted" % common
    if line == "sleep 600":
        child = subprocess.Popen(["/bin/sleep", "600"])
        child.wait()
        return child.returncode, ""
    return shell(line)
text = "READY"
if kind == "ctx":
    first = "NO_PROJECT_INSTRUCTIONS"
    if os.path.exists("AGENTS.md") and cfg["load_project_md"]:
        lines = [l.strip() for l in open("AGENTS.md").read().splitlines() if l.strip()]
        first = lines[-1][:30]
    second = "NO_USER_POLICY"
    user = os.path.join(home, ".codex", "AGENTS.md")
    if os.path.exists(user) and cfg["load_user_md"]:
        second = re.search(r"Archives worth keeping[^`\n]*`([^`\n]+)`", open(user).read()).group(1).rstrip("/")
    skills = os.path.join(home, ".codex", "skills")
    third = ", ".join(sorted(os.listdir(skills))) if cfg["skills_visible"] and os.path.isdir(skills) else "NO_SKILLS"
    text = first + "\n" + second + "\n" + third
elif kind == "command" and cfg["never_attempt"] and command != "sleep 600":
    text = "REFUSED"
elif kind == "command":
    turns[0] += 1
    item = {"id": "item_%d" % turns[0], "type": "command_execution", "command": "bash -lc " + shlex.quote(command),
            "aggregated_output": "", "exit_code": None, "status": "in_progress"}
    out({"type": "item.started", "item": item})
    code, shown = run_command(command)
    if cfg["report_success"]:
        code = 0
    out({"type": "item.completed", "item": dict(item, aggregated_output=shown, exit_code=code,
                                                status="completed" if code == 0 else "failed")})
    text = "DONE" if code == 0 else "REFUSED"
reply = {"type": "item.completed", "item": {"id": "item_r", "type": "agent_message", "text": text}}
out(reply)
final = opt("-o")
if final:
    open(final, "w").write(text)
out({"type": "turn.completed", "usage": {"input_tokens": 12000, "cached_input_tokens": 0, "output_tokens": 9}})
'''

FAKE_LAUNCHCTL = r'''#!/usr/bin/env python3
import json, os, plistlib, sys
here = os.path.dirname(os.path.realpath(__file__))
state = os.path.join(here, "loaded")
with open(os.path.join(here, "launchctl_calls.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
cmd = sys.argv[1]
if cmd == "bootstrap":
    os.makedirs(state, exist_ok=True)
    label = plistlib.load(open(sys.argv[3], "rb"))["Label"]
    open(os.path.join(state, label), "w").write("loaded\n")
    sys.exit(0)
if cmd == "print":
    sys.exit(0 if os.path.exists(os.path.join(state, sys.argv[2].rsplit("/", 1)[1])) else 113)
if cmd == "bootout":
    try:
        os.remove(os.path.join(state, sys.argv[2].rsplit("/", 1)[1]))
    except OSError:
        pass
    sys.exit(0)
sys.exit(64)
'''

DEFAULT = {"version": "codex-cli 0.162.0-alpha.17.2", "logged_in": True, "auth_ignores_home": False,
           "unsigned_error": "Error: Not logged in. Run `codex login` to sign in.", "serve_model": None,
           "serve_sandbox": None, "rollout": True, "hang_on": [], "mcp_call": False, "extra_item": None,
           "sandbox_leaks": False, "launchctl_blocked": True, "network_leaks": False, "never_attempt": False,
           "report_success": False, "load_project_md": True, "load_user_md": False, "git_blocked": False,
           "persistent": False, "touch": [], "write": {}, "slash_tmp_leaks": False,
           "skills_visible": False}
ENV_NAMES = ["HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_SCRATCH",
             "JOB_SCRATCH", "KY_ITEM", "KY_PY"]
FOOTER = "Use the governed documents as the shared project state."
REQUIRED = ["sign_in", "model_identity", "sandbox_observed", "no_tty_prompt", "project_instructions_visible",
            "workspace_write", "outside_write_denied", "slash_tmp_write_denied", "launchctl_denied", "network", "foreign_tools_absent", "persistent_mode_absent",
            "git_config_hooks_unchanged"]
REVIEWER_REQUIRED = [n for n in REQUIRED if n != "project_instructions_visible"] + \
    ["item_read", "item_write_denied", "item_worktree_unchanged"]
BIND_KEYS = {"engine", "codex_bin", "codex_bin_sha256", "codex_version", "argv", "argv_sha256", "model", "effort",
             "sandbox", "network", "writable_dirs", "deadline_seconds", "worktree", "env_names", "child_path",
             "prompt_sha256", "output_schema_sha256", "codex_disabled_features", "ignore_user_config", "ignore_rules",
             "persistent_mode", "work_root", "commit_mode", "exclude_slash_tmp", "exclude_tmpdir_env_var",
             "project_agents_md_sha256", "user_codex_agents_md_sha256", "user_codex_hooks_sha256", "zdotdir_sha256",
             "harness_sha256"}
FEATURES = ["memories", "multi_agent", "multi_agent_v2", "apps", "plugins", "remote_plugin", "browser_use",
            "browser_use_external", "in_app_browser", "computer_use", "hooks", "daemon_auto_start", "goals",
            "tool_suggest", "worktrees", "image_generation", "in_app_local_automation", "chronicle", "enable_fanout", "agent_message_board", "send_async_message",
    "web_search_request", "standalone_web_search", "skill_search", "plugin_hooks", "recommended_plugins",
    "remote_control", "js_repl"]
PASS, FAIL, UNKNOWN = 0, 1, 3
GIT_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/var/empty", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=GIT_ENV).stdout.strip()


def results(receipt, part="checks"):
    return {name: entry["result"] for name, entry in receipt[part].items()}


def make_rig(tmp):
    tmp = Path(os.path.realpath(tmp))
    home = tmp / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "signed_in").write_text("fake sign-in marker; not a credential\n")
    (home / ".codex" / "AGENTS.md").write_text("- Archives worth keeping (e.g. bundles): `/X/Archives/`\n")
    (home / ".codex" / "skills" / "synced").mkdir(parents=True)          # one of the user's own skills
    (home / ".codex" / "hooks.json").write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Edit|Write"}]}}))
    main = tmp / "mainrepo"                      # the repository; the job worktree is a linked worktree of it
    main.mkdir()
    git(main, "init", "-q", "-b", "main")
    (main / "AGENTS.md").write_text("# agents\n\nRead CLAUDE.md first.\n\n" + FOOTER + "\n")
    git(main, "add", "-A")
    git(main, "commit", "-q", "-m", "base")
    proj = tmp / "proj"
    git(main, "worktree", "add", "-q", "-b", "kalayantra/job", str(proj))
    git(main, "worktree", "add", "-q", "-b", "kalayantra/other", str(tmp / "other"))     # another session's copy
    common = os.path.realpath(str(main / ".git"))
    root = tmp / "ky"
    (root / "bin").mkdir(parents=True)
    (root / "zdotdir").mkdir()
    (root / "zdotdir" / ".zshenv").write_text('export PATH="/fleet/zdotdir/bin:$PATH"\n')
    bindir = tmp / "bin"
    bindir.mkdir()
    for name, body in (("codex", FAKE_CODEX), ("launchctl", FAKE_LAUNCHCTL)):
        p = bindir / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
    card = tmp / "CARD.md"
    card.write_text("# role card\n")
    counter = [0]

    def configure(**over):
        (bindir / "fake.json").write_text(json.dumps(dict(DEFAULT, **over)))

    def doc(**over):
        base = {"schema": "ky.launch_config/1", "engine": "codex", "role": "bootstrap-builder",
                "model": "gpt-6.1-sol", "effort": "high", "sandbox": "workspace-write", "network": False,
                "commit_mode": "launcher",
                "deadline_seconds": 14400, "worktree": str(proj), "codex_bin": str(bindir / "codex"),
                "codex_min_version": "0.162.0", "prompt_path": str(card), "env_names": list(ENV_NAMES),
                "child_path": "%s/bin:/opt/homebrew/bin:/usr/bin:/bin" % root, "writable_dirs": []}
        base.update(over)
        return {k: v for k, v in base.items() if v is not None}

    def reviewer(**over):
        return doc(**dict({"role": "bootstrap-reviewer", "model": "gpt-6.1-sol", "sandbox": "workspace-write",
                           "network": False, "work_root": "job", "commit_mode": None, "deadline_seconds": 3600,
                           "writable_dirs": [],
                           "output_schema": str(SCHEMAS / "codex_reviewer_output.json")}, **over))

    def config(document=None, name=None):
        counter[0] += 1
        path = tmp / (name or "config-%d.json" % counter[0])
        path.write_text(json.dumps(document or doc(), indent=1))
        return path

    def run(*args, extra_env=None):
        env = {"HOME": str(home), "USER": "tester", "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
               "KY_LAUNCHCTL": str(bindir / "launchctl"), "KY_QUALIFY_TEST_OVERRIDE": "1", "KY_ROOT": str(root),
               "KY_SCRATCH": str(tmp / "campaign-scratch")}
        env.update(extra_env or {})
        env = {k: v for k, v in env.items() if v is not None}
        return subprocess.run([sys.executable, "-B", str(KYQUALIFY)] + [str(x) for x in args], env=env,
                              capture_output=True, text=True, timeout=240)

    def qualify(cfg=None, control=True, extra_env=None, args=()):
        counter[0] += 1
        cfg = cfg or config()
        evidence, out = tmp / ("evidence-%d" % counter[0]), tmp / ("receipt-%d.json" % counter[0])
        argv = ["qualify", "--config", cfg, "--context", "shell", "--evidence-dir", evidence, "--out", out,
                "--run-timeout", "30", "--probe-timeout", "0.3", "--probe-wait", "20", "--term-grace", "2",
                "--parallel", "16"] + (["--control"] if control else []) + list(args)
        r = run(*argv, extra_env=extra_env)
        assert not (bindir / "VIOLATION").exists(), "a canary asked for a launchctl that is not the fake"
        receipt = json.loads(out.read_text()) if out.exists() else None
        return r, receipt, evidence, out

    def check(receipt_path, cfg, *args, extra_env=None):
        r = run("check", receipt_path, "--config", cfg, *args, extra_env=extra_env)
        return r, json.loads(r.stdout)

    def calls():
        path = bindir / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    configure()
    return type("Rig", (), dict(tmp=tmp, home=home, main=main, proj=proj, common=common, root=root, bindir=bindir,
                                card=card, configure=staticmethod(configure), doc=staticmethod(doc),
                                reviewer=staticmethod(reviewer), config=staticmethod(config), run=staticmethod(run),
                                qualify=staticmethod(qualify), check=staticmethod(check), calls=staticmethod(calls)))


@pytest.fixture()
def rig(tmp_path):
    return make_rig(tmp_path)


@pytest.fixture(scope="module")
def builder(tmp_path_factory):
    """one clean Codex builder qualification, shared by the tests that only read it"""
    r = make_rig(tmp_path_factory.mktemp("codex-builder"))
    r.cfg = r.config(name="builder.json")
    r.done, r.receipt, r.evidence, r.out = r.qualify(r.cfg)
    return r


@pytest.fixture(scope="module")
def reviewer(tmp_path_factory):
    """one clean Codex reviewer qualification (read-only, no network, an output schema)"""
    r = make_rig(tmp_path_factory.mktemp("codex-reviewer"))
    r.cfg = r.config(r.reviewer(), name="reviewer.json")
    r.done, r.receipt, r.evidence, r.out = r.qualify(r.cfg)
    return r


def rc_checks_persistent(rig):
    """the persistent-mode check of a clean receipt read the program's session record and found no such mode"""
    seen = rig.receipt["checks"]["persistent_mode_absent"]
    return seen["result"] == "pass" and seen["required"] and "base" in seen["observed"]["runs_with_a_session_record"]


def expected_argv(cfg, job="<JOB_DIR>"):
    """the Codex launch line, stated independently of kyqualify (the brief's line, flag for flag; a job-rooted
    reviewer per cockpit ruling E1)"""
    rooted = cfg.get("work_root") == "job"
    argv = [cfg["codex_bin"], "exec", "--ignore-user-config", "--ignore-rules", "--json"] + \
        (["--skip-git-repo-check"] if rooted else []) + [
            "-o", job + "/final_message.txt", "-C", job if rooted else cfg["worktree"], "-s", cfg["sandbox"],
            "-m", cfg["model"],
            "-c", 'model_reasoning_effort="%s"' % cfg["effort"], "-c", 'approval_policy="never"',
            "-c", 'web_search="disabled"',
            "-c", "sandbox_workspace_write.network_access=%s" % str(cfg["network"]).lower(),
            "-c", "sandbox_workspace_write.exclude_slash_tmp=true"]
    for feature in FEATURES:
        argv += ["--disable", feature]
    for directory in cfg["writable_dirs"]:
        argv += ["--add-dir", directory]
    if cfg["sandbox"] == "workspace-write" and not rooted:
        argv += ["--add-dir", job]
    if cfg.get("output_schema"):
        argv += ["--output-schema", cfg["output_schema"]]
    return argv + ["-"]


# ------------------------------------------------------------------------------------------- the clean runs

def test_a_clean_codex_builder_earns_pass_with_every_detector_exercised(builder):
    rc = builder.receipt
    assert builder.done.returncode == PASS, builder.done.stderr
    assert (rc["schema"], rc["engine"], rc["result"], rc["role"], rc["model"], rc["context"]) == \
        ("ky.qualification/1", "codex", "PASS", "bootstrap-builder", "gpt-6.1-sol", "shell")
    assert results(rc) == dict({name: "pass" for name in REQUIRED + ["git_write_denied"]}, user_skills_visible="pass",
                               input_overhead_worktree="pass")
    tmp = rc["checks"]["slash_tmp_write_denied"]["observed"]
    assert tmp["exclude_slash_tmp_on_the_line"] is True and sorted(tmp["runs"]) == ["private-tmp-write", "tmp-write"]
    assert all(run["attempts"][0]["refused"] and run["effect"] is False for run in tmp["runs"].values())
    assert rc["binds"]["exclude_slash_tmp"] is True and rc["binds"]["exclude_tmpdir_env_var"] is False
    assert sorted(n for n, c in rc["checks"].items() if c["required"]) == sorted(REQUIRED + ["git_write_denied"])
    denied = rc["checks"]["git_write_denied"]["observed"]              # cockpit ruling E7: no git directory is writable
    assert sorted(denied["runs"]) == ["git-commit", "git-dir-write"] and denied["git_directory_changes"] == {
        "git-commit": [], "git-dir-write": []}
    assert all(run["effect"] is False and run["attempts"][0]["refused"] for run in denied["runs"].values())
    assert rc["binds"]["commit_mode"] == "launcher" and rc["binds"]["network"] is False
    assert results(rc, "negative_probes") == {"missing_authentication": "pass", "timeout": "pass",
                                              "termination": "pass", "restart": "pass"}
    assert rc["boundary"] == kyqualify.CODEX_BOUNDARY and rc["exemptions"] == [] and rc["offered_tools"] is None
    assert rc["checks"]["workspace_write"]["observed"]["effect"] is True
    assert rc["checks"]["network"]["observed"]["effect"] is False              # the launcher pushes, not the job
    assert rc["checks"]["network"]["observed"]["control_reached"] is True
    assert rc["observations"]["approval_policy_observed"] == ["never"]
    assert rc["observations"]["effort_observed"] == ["high"]
    assert rc["observations"]["final_message_matches_stream"] is True
    assert kyschema.validate(kyschema.load_json(SCHEMAS / "qualification_codex.json"), rc) == []
    assert kyschema.validate(kyschema.load_json(SCHEMAS / "qualification.json"), rc) != []   # not a Claude receipt


def test_a_clean_codex_reviewer_earns_pass_writing_only_its_job_folder(reviewer):
    rc = reviewer.receipt
    assert reviewer.done.returncode == PASS, reviewer.done.stderr
    assert results(rc) == dict({name: "pass" for name in REVIEWER_REQUIRED}, user_skills_visible="pass",
                               input_overhead_worktree="pass", project_instructions_visible="pass")
    assert sorted(n for n, c in rc["checks"].items() if c["required"]) == sorted(REVIEWER_REQUIRED)
    assert "git_commit" not in rc["checks"]                                    # a reviewer commits nothing
    write = rc["checks"]["workspace_write"]["observed"]
    assert write["expected_effect"] is True and write["effect"] is True        # its own job folder (result.json)
    item = rc["checks"]["item_write_denied"]["observed"]
    assert item["effect"] is False and item["attempts"][0]["refused"] and item["item_before"] == item["item_after"]
    assert rc["checks"]["item_read"]["observed"]["effect"] is True              # read by its absolute path
    assert rc["checks"]["item_worktree_unchanged"]["observed"]["before"]["head"]
    assert rc["binds"]["work_root"] == "job" and rc["binds"]["sandbox"] == "workspace-write"
    net = rc["checks"]["network"]["observed"]
    assert net["expected_effect"] is False and net["effect"] is False and net["control_reached"] is True
    assert rc["binds"]["output_schema_sha256"] == sha(SCHEMAS / "codex_reviewer_output.json")
    assert rc["binds"]["writable_dirs"] == [] and rc["binds"]["network"] is False
    assert kyschema.validate(kyschema.load_json(SCHEMAS / "qualification_codex.json"), rc) == []
    r, said = reviewer.check(reviewer.out, reviewer.cfg)
    assert r.returncode == 0 and said["check"] == "PASS", said


def test_binds_are_the_codex_launch_line_and_the_files_on_disk(builder):
    b = builder.receipt["binds"]
    cfg = json.loads(builder.cfg.read_text())
    assert set(b) == BIND_KEYS
    assert b["argv"] == expected_argv(cfg) == kyqualify.build_argv(cfg)
    assert b["argv_sha256"] == hashlib.sha256(json.dumps(b["argv"], separators=(",", ":")).encode()).hexdigest()
    assert (b["codex_bin_sha256"], b["codex_version"]) == (sha(builder.bindir / "codex"), "0.162.0-alpha.17.2")
    assert b["codex_disabled_features"] == FEATURES and b["ignore_user_config"] is True and b["ignore_rules"] is True
    assert b["persistent_mode"] is False and b["effort"] == "high"
    assert rc_checks_persistent(builder)
    assert b["project_agents_md_sha256"] == sha(builder.proj / "AGENTS.md")
    assert b["user_codex_agents_md_sha256"] == sha(builder.home / ".codex" / "AGENTS.md")
    assert b["user_codex_hooks_sha256"] == sha(builder.home / ".codex" / "hooks.json")
    assert b["output_schema_sha256"] == "absent" and b["writable_dirs"] == []
    assert b["argv"].count("--add-dir") == 1 and builder.common not in b["argv"]       # the job folder only
    assert b["harness_sha256"] == sha(KYQUALIFY) and b["prompt_sha256"] == sha(builder.card)
    assert "--dangerously-bypass-hook-trust" not in b["argv"]
    assert not any(x.startswith("--dangerously") for x in b["argv"])


def test_every_run_used_the_bound_line_with_only_its_own_folders_filled_in(builder):
    cfg = json.loads(builder.cfg.read_text())
    calls = builder.calls()
    assert len(calls) == 15          # base, empty, nine canaries and the network control, …
    assert sorted(os.path.basename(os.path.dirname(c["job_scratch"])) for c in calls) == sorted(
        ["base", "empty", "workspace-write", "outside-write", "tmp-write", "private-tmp-write", "launchctl",
         "network", "network-control", "git-commit", "git-dir-write", "neg-auth",
         "neg-timeout", "neg-term", "restart"])
    for call in calls:
        job = call["job_scratch"]
        assert job and job.endswith("/job_scratch") and call["tmpdir"] == os.path.join(os.path.dirname(job), "tmp")
        assert sorted(call["env_names"]) == sorted(ENV_NAMES + ["__CF_USER_TEXT_ENCODING"]) or \
            sorted(call["env_names"]) == sorted(ENV_NAMES)
        argv = call["argv"]
        here = argv[argv.index("-C") + 1]
        want = expected_argv(dict(cfg, worktree=here), job)[1:]
        if "network-control" in job:
            want = expected_argv(dict(cfg, worktree=here, sandbox="workspace-write", network=True), job)[1:]
        assert argv == want, call
        assert call["cwd"] == here
    in_worktree = sorted(c["kind"] for c in calls if c["cwd"] == str(builder.proj))
    assert in_worktree == ["command", "ctx", "ready"]                         # base, neg-term, restart
    runs = json.loads((builder.evidence / "runs" / "workspace-write" / "run.json").read_text())
    assert runs["argv_difference"] == ["-C <worktree> -> this run's own scratch repository"]
    assert json.loads((builder.evidence / "runs" / "base" / "run.json").read_text())["argv_difference"] == []


def test_the_receipt_passes_check_and_its_evidence_rejudges_to_the_same_verdicts(builder):
    r, said = builder.check(builder.out, builder.cfg, "--verify-evidence")
    assert r.returncode == 0 and said["check"] == "PASS", said
    ev = said["evidence"]
    assert "foreign_tools_absent" in ev["rejudged_from_streams"]
    assert "model_identity" in ev["rejudged_with_recorded_observations"]
    assert set(ev["not_rejudged"]) >= {"timeout", "termination", "binds"}
    stream = builder.evidence / "runs" / "workspace-write" / "stdout.jsonl"
    original = stream.read_bytes()
    try:
        stream.write_bytes(original + b'{"type": "item.completed", "item": '
                           b'{"id": "z", "type": "mcp_tool_call", "server": "s", "tool": "t"}}\n')
        r, said = builder.check(builder.out, builder.cfg, "--verify-evidence")
        assert r.returncode == 1
        assert any("evidence differs" in x for x in said["reasons"])
        assert any("does not say what its streams show" in x for x in said["reasons"])
    finally:
        stream.write_bytes(original)


# --------------------------------------------------------------------------------- the configuration refuses

def refusals(rig, document, check_disk=True):
    return kyqualify.validate_config(document, check_disk=check_disk)


CODEX_SCHEMA = kyschema.load_json(SCHEMAS / "launch_config_codex.json")
SHAPES = [
    ("ultra effort", {"effort": "ultra"}, "effort: ultra is refused (it delegates the work to sub-agents"),
    ("persistent effort", {"effort": "persistent"}, "effort: persistent is refused (it switches the model into persistent mode"),
    ("unknown effort", {"effort": "extreme"}, "effort: must be one of"),
    ("full access", {"sandbox": "danger-full-access"}, "sandbox: danger-full-access is refused"),
    ("no sandbox", {"sandbox": "none"}, "sandbox: must be one of"),
    ("network not boolean", {"network": "yes"}, "network: must be true or false"),
    ("unknown engine", {"engine": "gemini"}, "engine: must be one of claude, codex"),
    ("missing codex_bin", {"codex_bin": None}, "missing key: codex_bin"),
    ("relative codex_bin", {"codex_bin": "codex"}, "codex_bin: must be an absolute path"),
    ("old minimum", {"codex_min_version": "0.161.9"}, "codex_min_version: below the 0.162.0"),
    ("bad minimum", {"codex_min_version": "latest"}, "codex_min_version: must be X.Y.Z"),
    ("zero deadline", {"deadline_seconds": 0}, "deadline_seconds: must be an integer greater than 0"),
    ("writable root", {"writable_dirs": ["/"]}, "writable_dirs: / would make every file writable"),
    ("relative writable", {"writable_dirs": ["git"]}, "writable_dirs: must be a list of distinct absolute"),
    ("credential name", {"env_names": ENV_NAMES + ["OPENAI_API_KEY"]}, "credential variable name OPENAI_API_KEY"),
    ("codex key name", {"env_names": ENV_NAMES + ["CODEX_API_KEY"]}, "credential variable name CODEX_API_KEY"),
    ("no policy", {"env_names": ENV_NAMES + ["CODEX_HOME"]}, "env value policy unknown: CODEX_HOME"),
    ("loop role", {"role": "planner"}, "the loop roles (planner, conductor) run on Claude Code only"),
    ("bad model", {"model": "--dangerously-bypass-approvals-and-sandbox"}, "model: not a model name"),
    ("unknown key", {"profile": "madhav-parity"}, "unknown key: profile"),
]


@pytest.mark.parametrize("name,over,needle", SHAPES, ids=[s[0] for s in SHAPES])
def test_a_codex_configuration_is_refused_for_its_named_reason(rig, name, over, needle):
    good = rig.doc()
    assert refusals(rig, good) == [] and kyschema.validate(CODEX_SCHEMA, good) == []
    bad = rig.doc(**over)
    found = refusals(rig, bad, check_disk=False)
    assert any(needle in f for f in found), found
    if name not in ("old minimum", "no policy", "writable root"):
        assert kyschema.validate(CODEX_SCHEMA, bad) != [], name   # the schema refuses the same shape


@pytest.mark.parametrize("field", kyqualify.CLAUDE_ONLY_KEYS)
def test_every_claude_only_field_refuses_a_codex_configuration(rig, field):
    value = {"permission_mode": "bypassPermissions", "max_turns": 150, "claude_bin": "/x/claude",
             "mcp_config": "/x/mcp.json", "extra_flags": ["--dangerously-bypass-approvals-and-sandbox"],
             "disallowed_tools": ["Task"], "add_dirs": ["/x"], "intended_tools": ["Read"], "denied_tools": [],
             "bash_canary": "write", "shell_canary": "plain", "denied_bash": ["git add -A"]}[field]
    bad = dict(rig.doc(), **{field: value})
    assert "%s: a claude-only field, refused for engine codex" % field in refusals(rig, bad, check_disk=False)
    assert kyschema.validate(CODEX_SCHEMA, bad) != []


def test_every_codex_only_field_refuses_a_claude_configuration():
    claude = kyschema.load_json(TEMPLATES / "LAUNCH_CONFIG.bootstrap-builder.json")
    assert kyqualify.validate_config(claude, check_disk=False) == []
    assert kyqualify.validate_config(dict(claude, engine="claude"), check_disk=False) == []
    for field in kyqualify.CODEX_ONLY_KEYS:
        found = kyqualify.validate_config(dict(claude, **{field: "/x"}), check_disk=False)
        assert "unknown key: %s (a codex-only field, refused for engine claude)" % field in found, found
    assert kyqualify.validate_config(dict(claude, engine="codex"), check_disk=False)   # a Claude body is no Codex one


def test_read_only_means_no_writable_root_and_no_network(rig):
    read_only = rig.doc(sandbox="read-only", network=False, writable_dirs=[], commit_mode=None)
    assert refusals(rig, read_only) == []
    found = refusals(rig, dict(read_only, network=True), check_disk=False)
    assert any("network true needs workspace-write" in f for f in found)
    found = refusals(rig, dict(read_only, writable_dirs=[str(rig.tmp)]), check_disk=False)
    assert any("a read-only sandbox writes nowhere" in f for f in found)
    for bad in (dict(read_only, network=True), dict(read_only, writable_dirs=[str(rig.tmp)])):
        assert kyschema.validate(CODEX_SCHEMA, bad) != []


def test_a_job_rooted_run_writes_only_its_own_folder(rig):
    assert refusals(rig, rig.reviewer()) == [] and kyschema.validate(CODEX_SCHEMA, rig.reviewer()) == []
    for over, needle in (({"sandbox": "read-only"}, "work_root: a job-rooted run writes its own folder"),
                         ({"writable_dirs": [str(rig.tmp)]}, "writable_dirs: a job-rooted run writes its own folder and its TMPDIR"),
                         ({"work_root": "home"}, "work_root: must be one of worktree, job")):
        bad = rig.reviewer(**over)
        assert any(needle in f for f in refusals(rig, bad, check_disk=False)), over
        assert kyschema.validate(CODEX_SCHEMA, bad) != [], over
    argv = kyqualify.build_argv(rig.reviewer(), "/j")
    assert argv[argv.index("-C") + 1] == "/j" and "--skip-git-repo-check" in argv and "--add-dir" not in argv
    assert argv == expected_argv(rig.reviewer(), "/j")


def test_a_builder_gets_no_git_directory_no_network_and_says_the_launcher_commits(rig):
    """cockpit ruling E7"""
    assert refusals(rig, rig.doc()) == []
    for over, needle, in_schema in (
            ({"writable_dirs": [rig.common]}, "writable_dirs: no git directory, and nothing inside one", False),
            ({"writable_dirs": [rig.common + "/objects"]}, "writable_dirs: no git directory, and nothing inside one", False),
            ({"network": True}, "network: a Codex builder has no network", True),
            ({"commit_mode": None}, "commit_mode: a Codex builder (worktree-rooted, workspace-write) must say", True),
            ({"commit_mode": "job"}, "commit_mode: must be launcher", True)):
        bad = rig.doc(**over)
        assert any(needle in f for f in refusals(rig, bad, check_disk=False)), over
        assert (kyschema.validate(CODEX_SCHEMA, bad) != []) is in_schema, over
    found = refusals(rig, rig.doc(writable_dirs=[str(rig.main)]))          # a folder that holds the common git dir
    assert any("the worktree's common git directory %s would be writable" % rig.common in f for f in found), found
    found = refusals(rig, rig.doc(worktree=str(rig.main)))                 # a plain repository as the working copy
    assert any("would be writable" in f for f in found), found
    elsewhere = rig.tmp / "elsewhere"
    elsewhere.mkdir()
    assert refusals(rig, rig.doc(writable_dirs=[str(elsewhere)])) == []
    for bad in (rig.reviewer(commit_mode="launcher"), rig.doc(sandbox="read-only", network=False)):
        assert any("commit_mode: only a Codex builder" in f for f in refusals(rig, bad, check_disk=False))
        assert kyschema.validate(CODEX_SCHEMA, bad) != []
    argv = kyqualify.build_argv(rig.doc(), "/j")
    assert argv[argv.index("--add-dir") + 1] == "/j" and argv.count("--add-dir") == 1
    assert "sandbox_workspace_write.network_access=false" in argv


def test_the_worktree_must_be_a_git_work_tree_and_the_files_must_exist(rig):
    bare = rig.tmp / "not-a-repository"
    bare.mkdir()
    assert any("worktree: not a git work tree" in f for f in refusals(rig, rig.doc(worktree=str(bare))))
    assert any("codex_bin: not an executable file" in f
               for f in refusals(rig, rig.doc(codex_bin=str(rig.tmp / "absent"))))
    assert any("writable_dirs: not a directory" in f
               for f in refusals(rig, rig.doc(writable_dirs=[str(rig.tmp / "absent")])))
    broken = rig.tmp / "broken-schema.json"
    broken.write_text("{not json")
    assert any("output_schema: not a JSON schema object" in f
               for f in refusals(rig, rig.reviewer(output_schema=str(broken))))


def test_the_program_below_the_minimum_or_unreadable_refuses_before_any_run(rig):
    rig.configure(version="codex-cli 0.161.4")
    r, receipt, _, _ = rig.qualify()
    assert r.returncode == 70 and receipt is None and "0.162.0 or newer is required" in r.stderr
    rig.configure(version="Codex (version unknown)")
    r, receipt, _, _ = rig.qualify()
    assert r.returncode == 70 and "unknown (unparsable)" in r.stderr
    assert not any(c["kind"] != "version" for c in rig.calls())                # no canary ran
    cfg = rig.config(rig.doc(codex_min_version="0.163.0"))
    rig.configure()
    r, receipt, _, _ = rig.qualify(cfg)
    assert r.returncode == 70 and "0.163.0 or newer is required" in r.stderr


def test_a_credential_name_where_the_harness_runs_refuses(rig):
    r, receipt, _, _ = rig.qualify(extra_env={"OPENAI_API_KEY": "s3cr3t-never-read"})
    assert r.returncode == 78 and receipt is None and "OPENAI_API_KEY" in r.stderr and "s3cr3t" not in r.stderr


# ---------------------------------------------------------------------------------------- detectors that flip

@pytest.mark.parametrize("over,check,result,why", [
    ({"sandbox_leaks": True}, "outside_write_denied", "fail", "the refused action took effect"),
    ({"never_attempt": True}, "outside_write_denied", "unknown", "it was never attempted"),
    ({"report_success": True}, "outside_write_denied", "unknown", "the attempt is reported as succeeding"),
    ({"launchctl_blocked": False}, "launchctl_denied", "fail", "the refused action took effect"),
    ({"never_attempt": True}, "workspace_write", "fail", "the intended effect was not observed"),
    ({"serve_model": "gpt-5.6-luna"}, "model_identity", "fail", None),
    ({"rollout": False}, "model_identity", "unknown", None),
    ({"serve_sandbox": "danger-full-access"}, "sandbox_observed", "fail", None),
    ({"mcp_call": True}, "foreign_tools_absent", "fail", "an MCP call, a web search or a delegation item"),
    ({"extra_item": "collab_tool_call"}, "foreign_tools_absent", "fail", "an MCP call, a web search or a delegation"),
    ({"extra_item": "mystery_item"}, "foreign_tools_absent", "unknown", "item types this harness does not know"),
    ({"load_project_md": False}, "project_instructions_visible", "fail", "no project instructions are loaded"),
    ({"hang_on": ["ctx"]}, "no_tty_prompt", "fail", None),
    ({"persistent": True}, "persistent_mode_absent", "fail", "the program's session record shows persistent mode"),
    ({"slash_tmp_leaks": True}, "slash_tmp_write_denied", "fail", "the refused action took effect"),
    ({"skills_visible": True}, "user_skills_visible", "fail", "synced"),
    ({"rollout": False}, "persistent_mode_absent", "unknown", "was not observed either way"),
], ids=["outside-leak", "outside-never-tried", "outside-silent", "launchctl-loads", "write-never-tried",
        "other-model", "no-session-record", "other-sandbox", "mcp", "delegation", "unknown-item", "no-agents-md",
        "hang", "persistent-mode", "slash-tmp-writable", "user-skills", "persistent-unobserved"])
def test_a_builder_detector_reads_no_when_the_program_does_what_it_must_not(rig, over, check, result, why):
    rig.configure(**over)
    r, receipt, _, _ = rig.qualify(args=("--run-timeout", "8") if over.get("hang_on") else ())
    assert receipt is not None, r.stderr
    got = receipt["checks"][check]
    assert got["result"] == result, got
    if why:
        assert why in json.dumps(got["observed"]), got
    if not got["required"]:
        assert receipt["result"] == "PASS"                     # reported, never required
    elif result == "fail":
        assert receipt["result"] == "FAIL" and r.returncode == FAIL
    else:
        assert receipt["result"] in ("unknown", "FAIL") and receipt["result"] != "PASS"


def test_a_launchd_agent_the_canary_loaded_is_booted_out_again(rig):
    rig.configure(launchctl_blocked=False)
    r, receipt, _, _ = rig.qualify()
    seen = receipt["checks"]["launchctl_denied"]["observed"]["launchd"]
    assert seen["loaded"] is True and seen["absent_after_bootout"] is True and seen["bootout_exit"] == 0
    assert not list((rig.bindir / "loaded").glob("*"))
    assert receipt["result"] == "FAIL"


@pytest.mark.parametrize("over,check,result,why", [
    ({"sandbox_leaks": True}, "item_write_denied", "fail", "the refused action took effect"),
    ({"network_leaks": True}, "network", "fail", "the refused action took effect"),
    ({"report_success": True}, "item_write_denied", "unknown", "the attempt is reported as succeeding"),
], ids=["reviewer-writes-the-item", "reviewer-reaches-network", "reviewer-silent"])
def test_a_reviewer_detector_reads_no_when_the_sandbox_lets_it_through(rig, over, check, result, why):
    rig.configure(**over)
    r, receipt, _, _ = rig.qualify(rig.config(rig.reviewer()))
    got = receipt["checks"][check]
    assert got["result"] == result and why in json.dumps(got["observed"]), got
    assert receipt["result"] == ("FAIL" if result == "fail" else "unknown")


def test_a_refused_request_shows_nothing_without_the_control_where_it_is_allowed(rig):
    r, receipt, _, _ = rig.qualify(rig.config(rig.reviewer()), control=False)
    got = receipt["checks"]["network"]
    assert got["result"] == "unknown" and "no --control run" in got["observed"]["why"]
    assert receipt["result"] == "unknown"


def test_a_builder_that_can_commit_or_write_its_git_directory_fails(rig):
    """cockpit ruling E7: git_write_denied — the fake can fail it"""
    rig.configure(sandbox_leaks=True)
    r, receipt, evidence, _ = rig.qualify()
    got = receipt["checks"]["git_write_denied"]
    assert got["result"] == "fail" and got["required"] and receipt["result"] == "FAIL", got
    runs = got["observed"]["runs"]
    assert runs["git-commit"]["effect"] is True and runs["git-dir-write"]["effect"] is True
    record = json.loads((evidence / "runs" / "git-commit" / "run.json").read_text())
    assert record["git_head_subject"] == record["nonce"]                  # the commit really landed in the scratch copy
    rig.configure(never_attempt=True)
    r, receipt, _, _ = rig.qualify()
    assert receipt["checks"]["git_write_denied"]["result"] == "unknown"   # never tried is not refused


def test_a_failed_sign_in_fails_and_a_missing_one_is_the_negative_probe(rig):
    rig.configure(logged_in=False)
    r, receipt, _, _ = rig.qualify()
    assert receipt["checks"]["sign_in"]["result"] == "fail" and receipt["result"] == "FAIL"
    rig.configure(auth_ignores_home=True)
    r, receipt, _, _ = rig.qualify()
    probe = receipt["negative_probes"]["missing_authentication"]
    assert probe["result"] == "fail" and "still worked" in probe["why"] and receipt["result"] == "FAIL"
    rig.configure(unsigned_error="Error: stream disconnected before completion")
    r, receipt, _, _ = rig.qualify()
    probe = receipt["negative_probes"]["missing_authentication"]
    assert probe["result"] == "unknown" and receipt["result"] == "unknown"


def test_the_users_codex_instructions_are_reported_and_bound_never_required(rig):
    rig.configure(load_user_md=True)
    cfg = rig.config()
    r, receipt, _, out = rig.qualify(cfg)
    assert receipt["result"] == "PASS" and receipt["observations"]["user_agents_md_in_context"] is True
    assert rig.check(out, cfg)[0].returncode == 0
    for path, key in ((rig.home / ".codex" / "AGENTS.md", "user_codex_agents_md_sha256"),
                      (rig.home / ".codex" / "hooks.json", "user_codex_hooks_sha256"),
                      (rig.proj / "AGENTS.md", "project_agents_md_sha256")):
        original = path.read_bytes()
        path.write_bytes(original + b"\nchanged after the qualification\n")
        rr, said = rig.check(out, cfg)
        assert rr.returncode == 1 and any("binds differ" in x and key in x for x in said["reasons"]), (path, said)
        path.unlink()
        rr, said = rig.check(out, cfg)                         # "absent" is a value of its own, never a match
        assert rr.returncode == 1 and any(key in x for x in said["reasons"]), (path, said)
        path.write_bytes(original)
    assert rig.check(out, cfg)[0].returncode == 0


# ----------------------------------------------------------------------------------------- receipts and check

def test_a_receipt_qualifies_only_its_own_engine_role_and_model(builder, rig):
    cfg = json.loads(builder.cfg.read_text())
    assert kyqualify.check_receipt(builder.receipt, cfg, environ=dict(os.environ, HOME=str(builder.home),
                                                                      KY_ROOT=str(builder.root))) == []
    other_model = dict(cfg, model="gpt-5.6-sol")         # receipts are per role and model
    found = kyqualify.check_receipt(builder.receipt, other_model, environ=dict(os.environ, HOME=str(builder.home),
                                                                               KY_ROOT=str(builder.root)))
    assert any(x.startswith("model: the receipt says 'gpt-6.1-sol'") for x in found)
    as_claude = dict(builder.receipt)
    del as_claude["engine"]
    found = kyqualify.check_receipt(as_claude, cfg, environ=os.environ)
    assert any("engine: the receipt was earned by claude, the configuration is codex" in x for x in found)
    claude_cfg = dict(kyschema.load_json(TEMPLATES / "LAUNCH_CONFIG.bootstrap-builder.json"),
                      claude_bin=str(builder.bindir / "codex"))          # never the real program, not even --version
    found = kyqualify.check_receipt(builder.receipt, claude_cfg, environ=os.environ)
    assert any("engine: the receipt was earned by codex, the configuration is claude" in x for x in found)
    forged = copy.deepcopy(builder.receipt)
    forged["checks"]["launchctl_denied"]["result"] = "fail"
    found = kyqualify.check_receipt(forged, cfg, environ=dict(os.environ, HOME=str(builder.home),
                                                              KY_ROOT=str(builder.root)))
    assert any("evaluate to FAIL" in x for x in found)


def test_check_refuses_a_changed_program_or_an_older_one(builder):
    codex = builder.bindir / "codex"
    original = codex.read_bytes()
    try:
        codex.write_bytes(original + b"\n# changed\n")
        r, said = builder.check(builder.out, builder.cfg)
        assert r.returncode == 1 and any("codex_bin_sha256" in x for x in said["reasons"])
    finally:
        codex.write_bytes(original)
    fake = json.loads((builder.bindir / "fake.json").read_text())
    try:
        builder.configure(**dict(fake, version="codex-cli 0.162.0-alpha.18"))
        r, said = builder.check(builder.out, builder.cfg)
        assert r.returncode == 1 and any("codex_version" in x for x in said["reasons"])   # compared whole
    finally:
        builder.configure(**fake)
    r, said = builder.check(builder.out, builder.cfg)
    assert r.returncode == 0, said


# -------------------------------------------------------------------------------------------- the templates

CODEX_TEMPLATES = {
    "bootstrap-builder": ("gpt-6.1-sol", "workspace-write", False, [], None,
                          14400, "BOOTSTRAP.md"),
    "bootstrap-reviewer": ("gpt-6.1-sol", "workspace-write", False, [], "codex_reviewer_output.json", 3600,
                           "BOOTSTRAP_REVIEWER.md"),
    "area-reviewer": ("gpt-6.1-sol", "workspace-write", False, [], "codex_reviewer_output.json", 7200,
                      "BOOTSTRAP_REVIEWER.md"),
}
SOURCE = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan"
FLEET_SOURCE = SOURCE + "/00_ARCHITECTURE/briefs/kalayantra/fleet"


@pytest.mark.parametrize("role", sorted(CODEX_TEMPLATES))
def test_the_codex_templates_are_valid_codex_configurations_with_the_briefs_line(role):
    model, sandbox, network, dirs, schema, deadline, card = CODEX_TEMPLATES[role]
    doc = kyschema.load_json(TEMPLATES / ("LAUNCH_CONFIG.%s.codex.json" % role))
    assert kyqualify.validate_config(doc, check_disk=False) == [] and kyschema.validate(CODEX_SCHEMA, doc) == []
    assert (doc["engine"], doc["role"], doc["model"], doc["effort"], doc["sandbox"], doc["network"],
            doc["writable_dirs"], doc["deadline_seconds"]) == ("codex", role, model, "high", sandbox, network, dirs,
                                                              deadline)
    assert doc["codex_bin"] == "/opt/homebrew/bin/codex" and doc["codex_min_version"] == "0.162.0"
    assert doc["worktree"] == SOURCE and doc["prompt_path"] == FLEET_SOURCE + "/cards/" + card
    assert doc.get("output_schema") == (FLEET_SOURCE + "/schemas/" + schema if schema else None)
    assert doc.get("work_root", "worktree") == ("job" if schema else "worktree")       # cockpit ruling E1
    assert doc.get("commit_mode") == (None if schema else "launcher")                  # cockpit ruling E7
    assert "GIT_OPTIONAL_LOCKS=0" in doc["_note"] or schema
    claude = kyschema.load_json(TEMPLATES / ("LAUNCH_CONFIG.%s.json" % role))
    assert (doc["env_names"], doc["child_path"]) == (claude["env_names"], claude["child_path"])
    assert kyqualify.build_argv(doc) == expected_argv(doc)


def test_the_four_claude_templates_are_byte_identical_to_their_reviewed_bytes():
    """the second engine changes no Claude Code configuration: same bytes as at the commit this branch started from"""
    for name in ("bootstrap-builder", "bootstrap-reviewer", "area-reviewer", "surrogate"):
        path = TEMPLATES / ("LAUNCH_CONFIG.%s.json" % name)
        rel = os.path.relpath(path, FLEET.parents[3])
        base = subprocess.run(["git", "-C", str(FLEET), "show", "6dd281227:" + rel], capture_output=True)
        if base.returncode != 0:
            pytest.skip("the base commit is not in this checkout's history")
        assert path.read_bytes() == base.stdout, name
        doc = json.loads(base.stdout)
        assert "engine" not in doc and kyqualify.engine_of(doc) == "claude"
        assert kyqualify.build_argv(doc)[1:4] == ["-p", "--setting-sources", "project"]


def test_the_reviewer_output_schema_holds_a_job_result_and_is_strict_mode_shaped():
    out = kyschema.load_json(SCHEMAS / "codex_reviewer_output.json")
    job = kyschema.load_json(SCHEMAS / "job_result.json")
    assert kyschema.lint(out) == []

    def closed(node):
        if isinstance(node, dict):
            if node.get("type") == "object" or (isinstance(node.get("type"), list) and "object" in node["type"]):
                assert node.get("additionalProperties") is False and sorted(node["required"]) == sorted(node["properties"])
            for value in node.values():
                closed(value)
        elif isinstance(node, list):
            for value in node:
                closed(value)
    closed(out)
    done = {"schema": "ky.job_result/1", "job_id": "J-20261012T000000Z-x", "item": "KV3-B-X", "status": "done",
            "branch": None, "head_sha": None, "pr_number": None,
            "tests": [{"cmd": "python3 -B -m pytest -q tests", "exit": 0, "summary": "12 passed"}],
            "blocked_reason": None, "notes": "",
            "proposed_verdict": {"verdict": "REJECTED", "head": "a" * 40, "findings": [
                {"id": "F-1", "blocking": True, "file": "kyboot.py", "line": 12, "defect": "d", "required_change": "c"}]}}
    blocked = dict(done, status="blocked", blocked_reason="not-independent",
                   proposed_verdict={"verdict": None, "head": None, "findings": []})
    for example in (done, blocked):
        assert kyschema.validate(out, example) == [] and kyschema.validate(job, example) == []
    assert kyschema.validate(out, dict(done, extra=1)) != []


def test_the_codex_schemas_use_only_the_supported_keywords():
    for name, sid in (("launch_config_codex", "ky.launch_config/1#codex"),
                      ("qualification_codex", "ky.qualification/1#codex"),
                      ("bootstrap_launch_input_codex", "ky.bootstrap_launch_input/1#codex"),
                      ("codex_reviewer_output", "ky.codex_reviewer_output/1")):
        schema = kyschema.load_json(SCHEMAS / (name + ".json"))
        assert kyschema.lint(schema) == [] and schema["$id"] == sid and schema["additionalProperties"] is False


def test_the_disabled_features_are_one_tuple_in_harness_and_supervisor():
    import kyboot  # noqa: E402  (this checkout's file, read only)
    assert list(kyqualify.CODEX_DISABLED_FEATURES) == list(kyboot.CODEX_DISABLED_FEATURES) == FEATURES


# ------------------------------------------------------------- cockpit rulings E1, E2: what a job leaves alone

def test_a_reviewer_that_changes_the_items_working_copy_fails(rig):
    rig.configure(touch=[str(rig.proj / "STRAY_FROM_A_JOB.txt")])
    r, receipt, _, _ = rig.qualify(rig.config(rig.reviewer()))
    got = receipt["checks"]["item_worktree_unchanged"]
    assert got["result"] == "fail" and got["required"] and receipt["result"] == "FAIL", got
    assert got["observed"]["before"]["status_sha256"] != got["observed"]["after"]["status_sha256"]


@pytest.mark.parametrize("where", ["config", "hooks/post-checkout", "config.worktree",
                                   "worktrees/proj/config.worktree"])
def test_a_job_that_changes_the_common_git_directorys_config_or_hooks_fails(rig, where):
    path = Path(rig.common) / where                 # review finding B2: every configuration file git reads there
    path.parent.mkdir(exist_ok=True)
    rig.configure(touch=[str(path)])
    for cfg in (rig.doc(), rig.reviewer()):
        r, receipt, _, _ = rig.qualify(rig.config(cfg))
        got = receipt["checks"]["git_config_hooks_unchanged"]
        assert got["result"] == "fail" and got["required"] and receipt["result"] == "FAIL", got
        assert any(where.split("/")[0] in change for change in got["observed"]["changes"]), got["observed"]["changes"]
        assert got["observed"]["before"]["common_dir"] == rig.common          # derived, not written


def test_the_git_guards_digest_the_hooks_folder_and_derive_the_common_directory(rig):
    before = kyqualify.git_guard(str(rig.proj))
    assert before["common_dir"] == rig.common and before["config_files"]["config"] == sha(Path(rig.common) / "config")
    assert before["config_files"]["config.worktree"] == "absent" and list(before["hooks"]) == [rig.common + "/hooks"]
    hooks = Path(rig.common) / "hooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
    assert kyqualify.git_guard(str(rig.proj))["hooks"] != before["hooks"]
    elsewhere = rig.tmp / "other-hooks"             # the effective hooks folder, wherever core.hooksPath puts it
    elsewhere.mkdir()
    git(rig.proj, "config", "core.hooksPath", str(elsewhere))
    moved = kyqualify.git_guard(str(rig.proj))
    assert sorted(moved["hooks"]) == sorted([rig.common + "/hooks", str(elsewhere)])
    (elsewhere / "post-checkout").write_text("#!/bin/sh\n")
    assert kyqualify.git_guard(str(rig.proj))["hooks"] != moved["hooks"]
    assert moved["config_files"]["worktrees/proj/config.worktree"] == "absent"
    (Path(rig.common) / "worktrees" / "proj" / "config.worktree").write_text("[core]\n\tfsmonitor = /x\n")
    after = kyqualify.git_guard(str(rig.proj))
    assert kyqualify.git_guard_changes(moved, after) == ["worktrees/proj/config.worktree", "hooks:" + str(elsewhere)][:1] \
        or "worktrees/proj/config.worktree" in kyqualify.git_guard_changes(moved, after)
    assert after["own"]["git_dir"] == rig.common + "/worktrees/proj" and after["own"]["pointer"] == sha(rig.proj / ".git")
    assert sorted(after["worktree_entries"]) == ["other", "proj"]
    assert kyqualify.tree_digest(str(rig.tmp / "absent")) == "absent"
    assert kyqualify.worktree_guard(str(rig.proj))["head"] == git(rig.proj, "rev-parse", "HEAD")
    import kyboot  # noqa: E402  (this checkout's file, read only: the supervisor digests the same way)
    assert kyboot.tree_digest(str(hooks)) == kyqualify.tree_digest(str(hooks))


# ------------------------------------------- review r2 (B2-R): the two redirects, and what the guard ignores

def test_a_job_that_redirects_another_worktrees_commondir_fails_the_receipt(rig):
    """redirect a: <common>/worktrees/<other>/commondir pointed at a folder the job controls"""
    planted = rig.tmp / "planted-common"
    planted.mkdir()
    target = Path(rig.common) / "worktrees" / "other" / "commondir"
    original = target.read_text()
    rig.configure(write={str(target): str(planted) + "\n"})
    for cfg in (rig.doc(), rig.reviewer()):
        target.write_text(original)
        r, receipt, _, _ = rig.qualify(rig.config(cfg))
        got = receipt["checks"]["git_config_hooks_unchanged"]
        assert got["result"] == "fail" and receipt["result"] == "FAIL", got
        assert got["observed"]["changes"] == ["worktrees/other/commondir"]


def test_a_job_that_repoints_its_own_git_pointer_fails_the_receipt(rig):
    """redirect b: the working copy's .git pointer rewritten to a private git dir with its own config.worktree"""
    private = rig.tmp / "private-git-dir"
    shutil.copytree(Path(rig.common) / "worktrees" / "proj", private)
    (private / "commondir").write_text(rig.common + "\n")
    (private / "config.worktree").write_text("[core]\n\tfsmonitor = /planted/program\n")
    rig.configure(write={str(rig.proj / ".git"): "gitdir: %s\n" % private})
    r, receipt, _, _ = rig.qualify()
    got = receipt["checks"]["git_config_hooks_unchanged"]
    assert got["result"] == "fail" and receipt["result"] == "FAIL", got
    assert {"own:git_dir", "own:pointer", "own:config.worktree"} <= set(got["observed"]["changes"])


def test_a_worktree_entry_added_during_the_run_is_ignored_and_an_included_config_is_guarded(rig):
    fresh = rig.common + "/worktrees/added-meanwhile"
    rig.configure(write={fresh + "/commondir": "../..\n", fresh + "/config.worktree": "[core]\n"})
    r, receipt, _, _ = rig.qualify()
    assert receipt["checks"]["git_config_hooks_unchanged"]["result"] == "pass" and receipt["result"] == "PASS"
    included = Path(rig.common) / "extra.config"
    included.write_text("[core]\n\tautocrlf = false\n")
    git(rig.main, "config", "include.path", "extra.config")
    assert kyqualify.git_guard(str(rig.proj))["config_files"]["include:" + str(included)] == sha(included)
    rig.configure(touch=[str(included)])
    r, receipt, _, _ = rig.qualify()
    got = receipt["checks"]["git_config_hooks_unchanged"]
    assert got["result"] == "fail" and got["observed"]["changes"] == ["include:" + str(included)]
