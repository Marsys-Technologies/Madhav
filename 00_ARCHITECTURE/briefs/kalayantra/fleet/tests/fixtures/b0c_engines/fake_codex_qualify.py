#!/usr/bin/env python3
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
rollout_path = None
if cfg["rollout"]:
    day = os.path.join(home, ".codex", "sessions", "2026", "10", "12")
    os.makedirs(day, exist_ok=True)
    rollout_path = os.path.join(day, "rollout-2026-10-12T00-00-00-%s.jsonl" % thread)
    with open(rollout_path, "w") as f:
        f.write(json.dumps({"type": "session_meta", "payload": {"id": thread, "cwd": workdir}}) + "\n")
        if cfg["persistent"]:                   # the model's persistent-mode block, as a developer message
            f.write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": "<persistent_mode>You are now in persistent mode</persistent_mode>"}]}}) + "\n")
        policy = ""
        if cfg["load_user_md"] and os.path.exists(os.path.join(home, ".codex", "AGENTS.md")):
            policy = open(os.path.join(home, ".codex", "AGENTS.md")).read()
        if cfg["load_project_md"] and os.path.exists("AGENTS.md"):
            policy += "\n" + open("AGENTS.md").read()
        if policy:
            f.write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "# AGENTS.md instructions for " + workdir + "\n\n<INSTRUCTIONS>\n" + policy + "\n</INSTRUCTIONS>"}]}}) + "\n")
        f.write(json.dumps({"type": "turn_context", "payload": {
            "cwd": workdir, "model": served, "effort": conf.get("model_reasoning_effort"),
            "approval_policy": conf.get("approval_policy"),
            "sandbox_policy": {"type": cfg["serve_sandbox"] or sandbox, "network_access": network}}}) + "\n")
out({"type": "item.completed", "item": {"id": "item_warning", "type": "error", "message": "web_search_request is deprecated"}})
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
        # Test effects must stay under the rig's scratch root, even when simulating a leak.
        # /tmp effect detection is exercised with recorded observations in a direct judge test.
        if os.path.realpath(target).startswith(("/private/tmp/", "/tmp/")):
            return 1, "zsh:1: operation not permitted: " + target
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
    if first == "NO_PROJECT_INSTRUCTIONS" and cfg["load_user_md"]:
        user_path = os.path.join(home, ".codex", "AGENTS.md")
        if os.path.exists(user_path):
            first = open(user_path).read().strip().splitlines()[-1][:30]
    second = "NO_USER_POLICY"
    user = os.path.join(home, ".codex", "AGENTS.md")
    if os.path.exists(user) and cfg["load_user_md"]:
        second = re.search(r"Archives worth keeping[^`\n]*`([^`\n]+)`", open(user).read()).group(1).rstrip("/")
    skills = os.path.join(home, ".codex", "skills")
    third = ", ".join(sorted(os.listdir(skills))) if (cfg["skills_visible"] or conf.get("skills.include_instructions") != "false") and os.path.isdir(skills) else "NO_SKILLS"
    text = first + "\n" + second + "\n" + third
elif kind == "command" and cfg["never_attempt"] and command != "sleep 600":
    text = "REFUSED"
elif kind == "command":
    turns[0] += 1
    item = {"id": "item_%d" % turns[0], "type": "command_execution", "command": "bash -lc " + shlex.quote(command),
            "aggregated_output": "", "exit_code": None, "status": "in_progress"}
    wrapped = not command.startswith(("sleep ", "curl ")) and "launchctl" not in command and "CANARY_WRITE.txt" not in command
    if not wrapped:
        out({"type": "item.started", "item": item})
    code, shown = run_command(command)
    if cfg["report_success"]:
        code = 0
    if wrapped and rollout_path:
        call_id = "call_real_shape"
        with open(rollout_path, "a") as f:
            f.write(json.dumps({"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                "call_id": call_id, "input": "const r = await tools.exec_command({cmd:" + json.dumps(command) + ",max_output_tokens:1000});text(r);"}}) + "\n")
            f.write(json.dumps({"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": call_id,
                "output": [{"type": "input_text", "text": "Script completed\nWall time 0.2 seconds\nOutput:\n"},
                           {"type": "input_text", "text": json.dumps({"chunk_id": "fake", "exit_code": code,
                            "wall_time_seconds": 0, "output": shown})}]}}) + "\n")
    elif not wrapped:
        out({"type": "item.completed", "item": dict(item, aggregated_output=shown, exit_code=code,
                                                    status="completed" if code == 0 else "failed")})
    text = "DONE" if code == 0 else "REFUSED"
reply = {"type": "item.completed", "item": {"id": "item_r", "type": "agent_message", "text": text}}
out(reply)
final = opt("-o")
if final:
    open(final, "w").write(text)
out({"type": "turn.completed", "usage": {"input_tokens": 12000, "cached_input_tokens": 0, "output_tokens": 9}})