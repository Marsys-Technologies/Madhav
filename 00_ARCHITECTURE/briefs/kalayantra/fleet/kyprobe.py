#!/usr/bin/env python3
"""kyprobe.py — B-0c launch probes for KĀLA-YANTRA v3 (plan v2.7 §7, §14 B-0c).

Runs the plan §7 launch line (no --bare, explicit --permission-mode, --setting-sources
project, strict empty MCP config) once per roster model, from a shell and from a one-shot
launchd job, and records what the harness itself reports. Every verdict comes from a
detector that can fail (CLAUDE.md §N.8); an item the probe cannot show is "unknown".

  kyprobe.py matrix  --context shell|launchd --out-dir DIR --project-dir DIR [--with-control]
  kyprobe.py launchd --out-dir DIR --project-dir DIR        (one-shot job; booted out after)
  kyprobe.py assemble --shell-dir DIR --launchd-dir DIR --out PROBES.json

"launchd" is a proven context, never a label: `matrix --context launchd` refuses (exit 77) unless this very
process is the one-shot agent — its parent is pid 1 AND XPC_SERVICE_NAME is the agent's label, the proof
kyqualify.py asks of its own agent — and records that proof in MATRIX.json. `assemble` reports the launchd
context as "unknown" without it.

launchctl is /bin/launchctl. KY_LAUNCHCTL (an ABSOLUTE path) replaces it for tests; the path used is always
recorded, and a run made with a replaced launchctl counts as launchd only under the tests-only gate
KY_QUALIFY_TEST_OVERRIDE=1 (recorded too) — see launchctl_choice().

Stdlib only. Never reads, prints or stores a credential: environment NAMES only.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import plistlib
import re
import signal
import subprocess
import sys
import time

ROSTER = ["claude-opus-5-5", "claude-sonnet-5-5"]
MIN_VERSION = (2, 1, 296)
LABEL = "in.marsys.kalayantra.probe"
CRED_NAME = re.compile(r"^(DATABASE_URL|.*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY)$")
FOOTER = re.compile(r"^\*(CLAUDE\.md v[0-9.]+ \(\d{4}-\d{2}-\d{2}\))", re.M)
ARCHIVE = re.compile(r"Archives worth keeping[^`\n]*`([^`\n]+)`")
LEAN_FLAG = "--disable-slash-commands"
LEAN_MIN_SAVING = 500  # tokens; the flag is chosen only on a measured saving of at least this
SYSTEM_LAUNCHCTL = "/bin/launchctl"
LAUNCHCTL_ENV = "KY_LAUNCHCTL"                  # tests: an ABSOLUTE fake; always recorded in the receipt
TEST_GATE_ENV = "KY_QUALIFY_TEST_OVERRIDE"      # tests only: "1" lets a replaced launchctl count as launchd

PROMPT_CTX = (
    "Reply in exactly two lines and use no tool.\n"
    "Line 1: if project instructions from a file named CLAUDE.md with lettered sections "
    "(§A, §B, …) are present in your context, copy the first 30 characters of that file's "
    "final footer line (the line that begins with an asterisk followed by the file name); "
    "otherwise write NO_PROJECT_INSTRUCTIONS.\n"
    "Line 2: if your context contains an owner policy about temporary code copies, scratch "
    "files and Git worktrees, write the directory path it gives for archives worth keeping; "
    "otherwise write NO_USER_POLICY.\n"
)
# The user's own hooks on this host match Edit|Write|MultiEdit only, so the hook probe must
# write: one file, inside its own scratch directory, under an explicit acceptEdits mode.
PROMPT_TOOL = (
    "Use the Write tool exactly once to create the file PROBE_WRITE.txt in the current "
    "directory containing exactly the text %s and nothing else, then reply with only the word DONE.\n"
)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def parse_version(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def claude_version(claude_bin):
    try:
        out = subprocess.run([claude_bin, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_version(out.stdout)


def launchctl_choice(environ):
    """(path, replaced, test_gate, error). The launchctl this run uses: /bin/launchctl unless KY_LAUNCHCTL names
    another ABSOLUTE path (never a PATH lookup). `replaced` is recorded in every receipt; `test_gate` is true only
    when the tests-only variable KY_QUALIFY_TEST_OVERRIDE is "1" as well — outside it a run made with a replaced
    launchctl is never accepted as having run under launchd."""
    path = environ.get(LAUNCHCTL_ENV) or SYSTEM_LAUNCHCTL
    if not path.startswith("/") or os.path.normpath(path) != path:
        return path, True, False, "%s must be an absolute, normalised path (got %r)" % (LAUNCHCTL_ENV, path)
    replaced = path != SYSTEM_LAUNCHCTL
    return path, replaced, replaced and environ.get(TEST_GATE_ENV) == "1", None


def launchd_proof(label, environ=None):
    """what this very process can show about being the launchd job `label`"""
    environ = os.environ if environ is None else environ
    return {"pid": os.getpid(), "ppid": os.getppid(), "xpc_service_name": environ.get("XPC_SERVICE_NAME"),
            "label": label, "env_names": sorted(environ)}


def inside_launchd(proof, label):
    """true only for the proof kyqualify.py asks of its own agent: parent pid 1 AND XPC_SERVICE_NAME == label"""
    return isinstance(proof, dict) and proof.get("ppid") == 1 and proof.get("xpc_service_name") == label


def ancestor_claude_md(path):
    """CLAUDE.md files in `path` and every ancestor (the harness walks upwards)."""
    found, cur = [], os.path.realpath(path)
    while True:
        cand = os.path.join(cur, "CLAUDE.md")
        if os.path.isfile(cand):
            found.append(cand)
        parent = os.path.dirname(cur)
        if parent == cur:
            return found
        cur = parent


def disk_markers(project_dir, home):
    """Tokens read from disk that a reply can only contain if the file is in context."""
    proj = user = None
    try:
        m = FOOTER.search(open(os.path.join(project_dir, "CLAUDE.md"), encoding="utf-8").read())
        proj = m.group(1) if m else None
    except OSError:
        pass
    try:
        m = ARCHIVE.search(open(os.path.join(home, ".claude", "CLAUDE.md"), encoding="utf-8").read())
        user = m.group(1).rstrip("/") if m else None
    except OSError:
        pass
    return {"project_footer": proj, "user_archive_path": user}


def user_skill_names(home):
    d = os.path.join(home, ".claude", "skills")
    try:
        return sorted(n for n in os.listdir(d) if not n.startswith(".") and os.path.isdir(os.path.join(d, n)))
    except OSError:
        return []


def build_argv(claude_bin, model, mcp_config, add_dir, setting_sources, extra, max_turns, mode="default"):
    return [claude_bin, "-p", "--setting-sources", setting_sources, "--permission-mode", mode,
            "--model", model, "--effort", "high", "--max-turns", str(max_turns)] + list(extra) + [
            "--strict-mcp-config", "--mcp-config", mcp_config,
            "--output-format", "stream-json", "--verbose", "--include-hook-events",
            "--add-dir", add_dir]


def clean_env(home, user, tmp):
    return {"HOME": home, "USER": user, "LANG": "en_US.UTF-8", "TERM": "dumb",
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin", "TMPDIR": tmp}


def parse_stream(path):
    init, result, texts, hooks, bad, rate = None, None, [], [], 0, None
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if not isinstance(ev, dict):
            continue
        t, st = ev.get("type"), str(ev.get("subtype") or "")
        if t == "system" and st == "init" and init is None:
            init = ev
        elif (t == "system" and st.startswith("hook")) or "hook_event" in ev or "hook_name" in ev:
            hooks.append(str(ev.get("hook_event") or ev.get("hook_name") or st))
        elif t == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text") or "")
        elif t == "rate_limit_event":
            rate = ev.get("rate_limit_info") if isinstance(ev.get("rate_limit_info"), dict) else None
        elif t == "result":
            result = ev
    return init, result, "\n".join(texts), hooks, bad, rate


def nonbuiltin(plugins):
    """Plugin names the harness did not ship itself (its own carry path/source 'builtin')."""
    out = []
    for p in plugins or []:
        builtin = isinstance(p, dict) and (p.get("path") == "builtin" or str(p.get("source", "")).endswith("@builtin"))
        if not builtin:
            out.append(p.get("name") if isinstance(p, dict) else p)
    return sorted(str(n) for n in out if n is not None)


def names(seq):
    out = []
    for x in seq or []:
        out.append(x.get("name") if isinstance(x, dict) else x)
    return sorted(str(n) for n in out if n is not None)


def summarise(spec, exit_code, timed_out, started, ended):
    init, result, text, hooks, bad, rate = parse_stream(spec["stdout_path"])
    try:
        stderr_text = open(spec["stderr_path"], encoding="utf-8", errors="replace").read()
    except OSError:
        stderr_text = ""
    rec = dict(spec)
    rec.update({"started_at": started, "ended_at": ended, "exit_code": exit_code, "timed_out": timed_out,
                "stdout_sha256": sha256_file(spec["stdout_path"]) if os.path.exists(spec["stdout_path"]) else None,
                "unparsed_lines": bad, "not_logged_in": "not logged in" in (stderr_text + text).lower(),
                "hook_events": len(hooks), "hook_event_names": sorted(set(hooks)),
                "reply": text[:400], "observed": None, "result": None, "rate_limit": None})
    if rate is not None:
        windows = rate.get("unifiedWindows") if isinstance(rate.get("unifiedWindows"), dict) else {}
        rec["rate_limit"] = {"status": rate.get("status"), "type": rate.get("rateLimitType"),
                             "overage_status": rate.get("overageStatus"),
                             "utilization": {k: (v or {}).get("utilization") for k, v in sorted(windows.items())}}
    if spec.get("write_target"):
        try:
            rec["write_landed"] = open(spec["write_target"]).read().strip() == spec["nonce"]
        except OSError:
            rec["write_landed"] = False
    if init is not None:
        tools = names(init.get("tools"))
        rec["observed"] = {
            "session_id": init.get("session_id"), "model": init.get("model"),
            "claude_code_version": init.get("claude_code_version"),
            "permission_mode": init.get("permissionMode"), "api_key_source": init.get("apiKeySource"),
            "mcp_servers": names(init.get("mcp_servers")) if "mcp_servers" in init else None,
            "mcp_tools": [t for t in tools if t.startswith("mcp__")],
            "plugins": names(init.get("plugins")) if "plugins" in init else None,
            "plugins_nonbuiltin": nonbuiltin(init.get("plugins")) if "plugins" in init else None,
            "output_style": init.get("output_style"),
            "auto_memory_path_present": bool((init.get("memory_paths") or {}).get("auto")) if "memory_paths" in init else None,
            "skills": names(init.get("skills")) if "skills" in init else None,
            "slash_commands": names(init.get("slash_commands")) if "slash_commands" in init else None,
            "agents": names(init.get("agents")) if "agents" in init else None,
            "tools_count": len(tools)}
    if result is not None:
        usage = result.get("usage") or {}
        parts = [usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
        rec["result"] = {
            "subtype": result.get("subtype"), "is_error": result.get("is_error"),
            "num_turns": result.get("num_turns"), "session_id": result.get("session_id"),
            "usage": {k: usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens",
                                                 "cache_read_input_tokens", "output_tokens")},
            "input_tokens_total": sum(parts) if all(isinstance(p, int) for p in parts) else None,
            "model_usage_models": sorted((result.get("modelUsage") or {}).keys())}
    return rec


def run_one(spec, timeout):
    os.makedirs(spec["tmp_path"], exist_ok=True)
    with open(spec["prompt_path"], "w") as f:
        f.write(spec["prompt"])
    env = clean_env(spec["home"], spec["user"], spec["tmp_path"])
    started = utc()
    with open(spec["prompt_path"]) as fin, open(spec["stdout_path"], "w") as fout, \
            open(spec["stderr_path"], "w") as ferr:
        proc = subprocess.Popen(spec["argv"], cwd=spec["cwd"], env=env, stdin=fin, stdout=fout,
                                stderr=ferr, start_new_session=True)
        timed_out = False
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    proc.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    continue
            code = proc.returncode
    rec = summarise({k: v for k, v in spec.items() if k not in ("prompt", "home", "user")},
                    code, timed_out, started, utc())
    rec["env_names"] = sorted(env)
    write_json(os.path.join(os.path.dirname(spec["stdout_path"]), "result.json"), rec)
    return rec


def plan_runs(context, out_dir, project_dir, claude_bin, mcp_config, add_dir, with_control):
    empty = os.path.join(out_dir, "emptydir")
    tooldir = os.path.join(out_dir, "tooldir")
    controldir = os.path.join(out_dir, "controldir")
    for d in (empty, tooldir, controldir):
        os.makedirs(d, exist_ok=True)
    nonce = "KYPROBE-" + hashlib.sha256((out_dir + utc()).encode()).hexdigest()[:16]
    home, user = os.environ.get("HOME", ""), os.environ.get("USER", "")
    runs = []

    def add(run_id, model, cwd, kind, prompt, sources="project", extra=(), max_turns=1, mode="default"):
        d = os.path.join(out_dir, run_id)
        os.makedirs(d, exist_ok=True)
        writes = kind in ("tool", "control")
        runs.append({"id": run_id, "context": context, "kind": kind, "model_requested": model, "cwd": cwd,
                     "setting_sources": sources, "extra_flags": list(extra), "permission_mode": mode,
                     "nonce": nonce if writes else None,
                     "write_target": os.path.join(cwd, "PROBE_WRITE.txt") if writes else None,
                     "argv": build_argv(claude_bin, model, mcp_config, add_dir, sources, extra, max_turns, mode),
                     "prompt": prompt, "prompt_path": os.path.join(d, "prompt.txt"),
                     "stdout_path": os.path.join(d, "stdout.jsonl"), "stderr_path": os.path.join(d, "stderr.log"),
                     "tmp_path": os.path.join(d, "tmp"), "home": home, "user": user})

    for model in ROSTER:
        short = model.replace("claude-", "")
        add("%s.project" % short, model, project_dir, "project", PROMPT_CTX)
        add("%s.empty" % short, model, empty, "empty", PROMPT_CTX)
        if context == "shell":
            add("%s.lean" % short, model, empty, "lean", PROMPT_CTX, extra=(LEAN_FLAG,))
    add("sonnet-5-5.tool", ROSTER[1], tooldir, "tool", PROMPT_TOOL % nonce, max_turns=3, mode="acceptEdits")
    if with_control:
        # Positive control: with the user's own settings loaded, hooks/plugins/skills must
        # become visible in the stream — otherwise their absence above proves nothing.
        add("sonnet-5-5.control", ROSTER[1], controldir, "control", PROMPT_TOOL % nonce, sources="user,project",
            max_turns=3, mode="acceptEdits")
    return runs


def cmd_matrix(a):
    bad = sorted(n for n in os.environ if CRED_NAME.match(n))
    if bad:
        print("refused: credential variable name(s) set: " + ", ".join(bad), file=sys.stderr)
        return 78
    out_dir = os.path.realpath(a.out_dir)
    proof = None
    if a.context == "launchd":          # a shell run is never labelled launchd: prove it or refuse
        proof = launchd_proof(LABEL)
        if not inside_launchd(proof, LABEL):
            reason = ("not inside launchd: parent pid %s (launchd is 1), XPC_SERVICE_NAME %r (the agent's label is %r)"
                      % (proof["ppid"], proof["xpc_service_name"], LABEL))
            os.makedirs(out_dir, exist_ok=True)
            write_json(os.path.join(out_dir, "REFUSED.json"), {"reason": reason, "context_proof": proof})
            print("refused: " + reason, file=sys.stderr)
            return 77
    version = claude_version(a.claude_bin)
    if version is None or version < MIN_VERSION:
        print("refused: %s version %s is below %s" % (a.claude_bin, version, MIN_VERSION), file=sys.stderr)
        return 70
    os.makedirs(out_dir, exist_ok=True)
    runs = plan_runs(a.context, out_dir, os.path.realpath(a.project_dir), a.claude_bin,
                     os.path.realpath(a.mcp_config), a.add_dir, a.with_control)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:
        recs = list(pool.map(lambda s: run_one(s, a.timeout), runs))
    home = os.environ.get("HOME", "")
    write_json(os.path.join(out_dir, "MATRIX.json"), {
        "schema": "ky.probe_matrix/1", "context": a.context, "context_proof": proof, "generated_at": utc(),
        "claude_bin": a.claude_bin, "claude_version": ".".join(map(str, version)),
        "mcp_config": os.path.realpath(a.mcp_config), "mcp_config_sha256": sha256_file(a.mcp_config),
        "project_dir": os.path.realpath(a.project_dir),
        "markers": disk_markers(a.project_dir, home), "user_skill_names": user_skill_names(home),
        "ancestor_claude_md": {"project": ancestor_claude_md(a.project_dir),
                               "empty": ancestor_claude_md(os.path.join(out_dir, "emptydir"))},
        "parent_env_names_count": len(os.environ), "runs": recs})
    with open(os.path.join(out_dir, "DONE"), "w") as f:
        f.write(utc() + "\n")
    return 0


# ---------------------------------------------------------------- launchd one-shot

def render_plist(a, out_dir):
    """the one-shot agent as a property list (RunAtLoad, no KeepAlive), serialised by plistlib — never by hand"""
    me = os.path.realpath(__file__)
    args = [a.python, "-u", me, "matrix", "--context", "launchd", "--out-dir", out_dir,
            "--project-dir", os.path.realpath(a.project_dir), "--claude-bin", a.claude_bin,
            "--mcp-config", os.path.realpath(a.mcp_config), "--add-dir", a.add_dir,
            "--timeout", str(a.timeout)]
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": os.environ["HOME"],
           "USER": os.environ["USER"], "LANG": "en_US.UTF-8"}
    return {"Label": LABEL, "ProgramArguments": args, "EnvironmentVariables": env, "RunAtLoad": True,
            "ProcessType": "Background", "StandardOutPath": os.path.join(out_dir, "launchd.out"),
            "StandardErrorPath": os.path.join(out_dir, "launchd.err")}


def cmd_launchd(a):
    launchctl, replaced, gate, error = launchctl_choice(os.environ)
    if error:
        print("refused: " + error, file=sys.stderr)
        return 65
    out_dir = os.path.realpath(a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    done, refused = os.path.join(out_dir, "DONE"), os.path.join(out_dir, "REFUSED.json")
    if os.path.exists(done) or os.path.exists(refused):
        print("refused: %s already holds a finished probe" % out_dir, file=sys.stderr)
        return 73
    plist = os.path.join(out_dir, LABEL + ".plist")
    with open(plist, "wb") as f:
        plistlib.dump(render_plist(a, out_dir), f)
    if subprocess.run(["/usr/bin/plutil", "-lint", plist], capture_output=True).returncode != 0:
        print("refused: rendered plist fails plutil -lint", file=sys.stderr)
        return 65
    domain = "gui/%d" % os.getuid()
    target = "%s/%s" % (domain, LABEL)
    receipt = {"label": LABEL, "plist": plist, "domain": domain, "bootstrapped_at": utc(),
               "launchctl": launchctl, "launchctl_replaced": replaced, "test_override": gate}
    boot = subprocess.run([launchctl, "bootstrap", domain, plist], capture_output=True, text=True)
    receipt["bootstrap_exit"] = boot.returncode
    receipt["loaded_after_bootstrap"] = (boot.returncode == 0 and subprocess.run(
        [launchctl, "print", target], capture_output=True, text=True).returncode == 0)
    deadline = time.time() + a.wait
    while (boot.returncode == 0 and not os.path.exists(done) and not os.path.exists(refused)
           and time.time() < deadline):
        time.sleep(a.poll)
    receipt["finished"] = os.path.exists(done)
    out = subprocess.run([launchctl, "bootout", target], capture_output=True, text=True)
    receipt["bootout_exit"] = out.returncode
    gone = subprocess.run([launchctl, "print", target], capture_output=True, text=True)
    receipt["absent_after_bootout"] = gone.returncode != 0
    # the agent's own proof of where it ran: from the matrix it wrote, or from its refusal
    proof = None
    for name in ("MATRIX.json", "REFUSED.json"):
        try:
            with open(os.path.join(out_dir, name), encoding="utf-8") as f:
                proof = proof or (json.load(f) or {}).get("context_proof")
        except (OSError, ValueError, AttributeError):
            pass
    receipt["inner"] = proof if isinstance(proof, dict) else None
    receipt["launchd_context"] = launchd_context(receipt)
    receipt["ended_at"] = utc()
    write_json(os.path.join(out_dir, "LAUNCHD_RECEIPT.json"), receipt)
    return 0 if (receipt["finished"] and receipt["absent_after_bootout"]
                 and receipt["launchd_context"] == "proven") else 1


def launchd_context(receipt):
    """"proven" only when launchd listed the agent, the agent itself saw parent pid 1 and its own label, and the
    launchctl was the system's (or the tests-only gate was set and recorded); otherwise the reason it is not."""
    if not isinstance(receipt, dict):
        return "no launchd receipt"
    if receipt.get("launchctl") != SYSTEM_LAUNCHCTL and receipt.get("test_override") is not True:
        return "launchctl was replaced (%s): nothing shows the job ran under the system's launchd" % (
            receipt.get("launchctl"),)
    if receipt.get("loaded_after_bootstrap") is not True:
        return "launchd did not list the agent after bootstrap"
    if not inside_launchd(receipt.get("inner"), receipt.get("label")):
        return "the job's own context was not launchd's (parent pid 1 and XPC_SERVICE_NAME = the label)"
    return "proven"


# ---------------------------------------------------------------- verdicts

def by_id(matrix):
    return {r["id"]: r for r in (matrix or {}).get("runs", [])}


def sign_in(rec):
    if rec is None:
        return "unknown"
    res = rec.get("result")
    if rec.get("not_logged_in") or (res and res.get("is_error")) or (res is None and rec.get("exit_code") not in (0, None)):
        return "fails"
    if res and res.get("is_error") is False and res.get("subtype") == "success" and rec.get("reply"):
        return "works"
    return "unknown"


def in_context(rec, token, absent_word):
    """true only when the on-disk token is in the reply; false only on the explicit absent word."""
    if rec is None or not token or sign_in(rec) != "works":
        return "unknown"
    reply = rec.get("reply") or ""
    if token in reply:
        return True
    return False if absent_word in reply else "unknown"


def verdict_for(model, matrix, control):
    short = model.replace("claude-", "")
    runs = by_id(matrix)
    proj, empty, lean = runs.get(short + ".project"), runs.get(short + ".empty"), runs.get(short + ".lean")
    tool = runs.get("sonnet-5-5.tool")
    markers = (matrix or {}).get("markers") or {}
    v = {"model": model, "sign_in": sign_in(proj)}
    obs = (proj or {}).get("observed") or {}
    v["model_served"] = (obs.get("model") == model) if obs.get("model") else "unknown"
    v["permission_mode_observed"] = obs.get("permission_mode", "unknown") if obs else "unknown"
    v["output_style_observed"] = obs.get("output_style", "unknown") if obs else "unknown"
    v["auto_memory_path_present"] = obs.get("auto_memory_path_present", "unknown") if obs else "unknown"
    v["builtin_plugins_observed"] = (sorted(set(obs.get("plugins") or []) - set(obs.get("plugins_nonbuiltin") or []))
                                     if obs.get("plugins") is not None else "unknown")
    v["rate_limit_observed"] = (proj or {}).get("rate_limit") or "unknown"
    v["api_key_source_observed"] = obs.get("api_key_source", "unknown") if obs else "unknown"
    # Project CLAUDE.md: needs the positive hit AND a clean negative control in the empty directory.
    hit = in_context(proj, markers.get("project_footer"), "NO_PROJECT_INSTRUCTIONS")
    ctl = in_context(empty, markers.get("project_footer"), "NO_PROJECT_INSTRUCTIONS")
    v["project_claude_md_in_context"] = hit if ctl is False else "unknown"
    v["project_claude_md_negative_control"] = ctl
    v["user_claude_md_in_context"] = in_context(proj, markers.get("user_archive_path"), "NO_USER_POLICY")
    v["mcp_servers_active"] = ("unknown" if obs.get("mcp_servers") is None
                               else (obs["mcp_servers"] + obs.get("mcp_tools", [])) or "none")
    cobs = (control or {}).get("observed") or {}
    user_skills = set((matrix or {}).get("user_skill_names") or [])

    def namespaced(xs):
        return sorted(x for x in (xs or []) if ":" in x)

    # Plugins / skills / hooks are "none" only if the control (user settings loaded) showed them.
    if obs.get("plugins_nonbuiltin") is None or not cobs.get("plugins_nonbuiltin"):
        v["user_plugins_active"] = "unknown"
    else:
        v["user_plugins_active"] = obs["plugins_nonbuiltin"] or "none"
    seen = set(obs.get("skills") or []) | set(obs.get("slash_commands") or [])
    cseen = set(cobs.get("skills") or []) | set(cobs.get("slash_commands") or [])
    leaked = sorted((seen & user_skills) | set(namespaced(seen)))
    control_shows = bool((cseen & user_skills) or namespaced(cseen))
    v["user_skills_active"] = "unknown" if (not obs or not control_shows) else (leaked or "none")
    if (tool is None or sign_in(tool) != "works" or tool.get("write_landed") is not True
            or (control or {}).get("hook_events", 0) == 0 or (control or {}).get("write_landed") is not True):
        v["user_hooks_active"] = "unknown"
    else:
        v["user_hooks_active"] = tool["hook_event_names"] if tool["hook_events"] else "none"
    v["tool_probe_write_landed"] = tool.get("write_landed", "unknown") if tool else "unknown"

    def total(rec):
        return ((rec or {}).get("result") or {}).get("input_tokens_total")

    v["fixed_input_tokens_empty_dir"] = total(empty) if total(empty) is not None else "unknown"
    v["fixed_input_tokens_project_dir"] = total(proj) if total(proj) is not None else "unknown"
    v["fixed_input_tokens_lean"] = total(lean) if total(lean) is not None else "unknown"
    v["lean_sign_in"] = sign_in(lean) if lean else "unknown"
    return v


def cmd_assemble(a):
    def load(d):
        p = os.path.join(d, "MATRIX.json") if d else None
        return (json.load(open(p)), sha256_file(p)) if p and os.path.exists(p) else (None, None)

    shell, shell_sha = load(a.shell_dir)
    launchd, launchd_sha = load(a.launchd_dir)
    control = by_id(shell).get("sonnet-5-5.control")
    receipt = None
    if a.launchd_dir:
        try:
            with open(os.path.join(a.launchd_dir, "LAUNCHD_RECEIPT.json"), encoding="utf-8") as f:
                receipt = json.load(f)
        except (OSError, ValueError):
            receipt = None
    # the launchd context counts only with its proof: the receipt's, and the same proof inside the matrix itself
    proven = launchd_context(receipt)
    if proven == "proven" and not (isinstance(launchd, dict) and launchd.get("context") == "launchd"
                                   and inside_launchd(launchd.get("context_proof"), LABEL)):
        proven = "the launchd matrix does not carry the job's own launchd proof"
    out = {"schema": "ky.probes/1", "plan_version": "2.7", "generated_at": utc(),
           "claude_version": (shell or launchd or {}).get("claude_version", "unknown"),
           "launch_line": "plan v2.7 §7: -p --setting-sources project --permission-mode <explicit> "
                          "--strict-mcp-config --mcp-config mcp.none.json (no --bare)",
           "evidence": {"shell_matrix": a.shell_dir, "shell_matrix_sha256": shell_sha,
                        "launchd_matrix": a.launchd_dir, "launchd_matrix_sha256": launchd_sha,
                        "launchd_launchctl": (receipt or {}).get("launchctl", "unknown") if isinstance(receipt, dict) else "unknown",
                        "launchd_test_override": (receipt or {}).get("test_override", "unknown") if isinstance(receipt, dict) else "unknown",
                        "launchd_context": proven if launchd is not None else "not run",
                        "launchd_context_proof": (launchd or {}).get("context_proof") if isinstance(launchd, dict) else None},
           "control": {"hook_events": (control or {}).get("hook_events", "unknown"),
                       "write_landed": (control or {}).get("write_landed", "unknown"),
                       "user_plugins_seen": len(((control or {}).get("observed") or {}).get("plugins_nonbuiltin") or []),
                       "note": "the control loads the user's settings on purpose; calibration only"},
           "contexts": {}}
    for name, matrix in (("shell", shell), ("launchd", launchd if proven == "proven" else None)):
        out["contexts"][name] = ("unknown" if matrix is None
                                 else {m: verdict_for(m, matrix, control) for m in ROSTER})
    # EXTRA_LEAN_FLAGS: chosen by rule from measured numbers, per model, never by judgment.
    chosen, basis = [], {}
    if shell is not None:
        ok = True
        for m in ROSTER:
            v = out["contexts"]["shell"][m]
            e, l = v["fixed_input_tokens_empty_dir"], v["fixed_input_tokens_lean"]
            saving = (e - l) if isinstance(e, int) and isinstance(l, int) else None
            basis[m] = {"saving_tokens": saving if saving is not None else "unknown", "lean_sign_in": v["lean_sign_in"]}
            ok = ok and saving is not None and saving >= LEAN_MIN_SAVING and v["lean_sign_in"] == "works"
        chosen = [LEAN_FLAG] if ok else []
    out["extra_lean_flags"] = {"chosen": chosen, "rule": "%s iff every roster model signs in with it and saves ≥ %d "
                               "input tokens in the empty directory" % (LEAN_FLAG, LEAN_MIN_SAVING), "basis": basis}
    write_json(a.out, out)
    print(json.dumps({"out": a.out, "sha256": sha256_file(a.out)}))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--out-dir", required=True)
        sp.add_argument("--project-dir", required=True)
        sp.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "/Users/Dev/.local/bin/claude"))
        sp.add_argument("--mcp-config", default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "mcp.none.json"))
        sp.add_argument("--add-dir", default=os.environ.get("KY_ROOT", "/Users/Dev/kalayantra"))
        sp.add_argument("--timeout", type=int, default=240)

    m = sub.add_parser("matrix")
    common(m)
    m.add_argument("--context", choices=["shell", "launchd"], required=True)
    m.add_argument("--with-control", action="store_true")
    m.add_argument("--parallel", type=int, default=4)
    m.set_defaults(fn=cmd_matrix)
    l = sub.add_parser("launchd")
    common(l)
    l.add_argument("--python", default=sys.executable)
    l.add_argument("--wait", type=int, default=900)
    l.add_argument("--poll", type=float, default=2.0)
    l.set_defaults(fn=cmd_launchd)
    s = sub.add_parser("assemble")
    s.add_argument("--shell-dir")
    s.add_argument("--launchd-dir")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_assemble)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
