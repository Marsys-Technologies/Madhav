#!/usr/bin/env python3
"""kyqualify.py — launch qualification for KĀLA-YANTRA v3 (plan v2.7 §7 "Launch qualification (KV-06)", §13, §14 B-0c).

A launch configuration is usable only with a passing qualification receipt bound to the resolved executable and
its hash, version, exact argv, model/effort, permissions, working directory, environment policy and
prompt/configuration hashes. This harness runs the configuration's EXACT argv against observable canaries — from a
shell, or inside a one-shot launchd user agent — and writes that receipt. Every verdict comes from a detector that
can fail (root CLAUDE.md §N.8); what the harness cannot show is "unknown", and unknown refuses.

  kyqualify.py qualify --config LAUNCH_CONFIG.json --context launchd|shell --evidence-dir DIR --out RECEIPT.json
                       [--control] [--run-timeout S] [--probe-timeout S] [--term-grace S] [--parallel N]
  kyqualify.py check RECEIPT.json --config LAUNCH_CONFIG.json [--require-context launchd|shell] [--verify-evidence]
  (kyqualify.py launchd-inner … is the in-agent half of `qualify --context launchd`; it refuses anywhere else.)

qualify exits 0 PASS · 1 FAIL · 3 unknown (a complete run; the receipt is written atomically in all three), or
refuses without touching --out: 65 configuration · 70 program version · 73 evidence directory in use ·
74 bound files changed during the run · 75 launchd job incomplete · 77 not inside launchd ·
78 credential variable name set · 130 interrupted · 2 usage or internal error.
check exits 0 only for a PASS receipt whose binds equal the binds recomputed from disk; 1 otherwise.

Runs (the bound argv, unchanged unless a difference is recorded in the receipt; prompt on stdin; environment =
exactly env_names). cwd is the worktree for base, neg-term and restart (none of which is asked to write), a
scratch canary directory under --evidence-dir for every other run:
  base · empty (CLAUDE.md negative control) · tool-<t> per intended tool · deny-<t> per denied tool (the Bash
  canary writes a file, or with "bash_canary": "readonly" runs `shasum -a 256` and may change nothing) ·
  hooks (+ --include-hook-events) · control (--setting-sources user,project, only with --control) ·
  neg-auth (HOME → empty directory) · neg-settings (invalid MCP file) · neg-timeout · neg-term → restart.
The harness signals only the process groups it started, and only when it ends a run itself (deadline, probe,
interruption); whatever a run started outside its group is recorded, never signalled.

excluded_user_hooks reads, from $HOME/.claude/settings.json, hook event names and matcher strings only: when no
offered tool can trigger any of the user's hooks the verdict is structural ("cannot_fire"); otherwise it comes from
the Write canary and the control.

Stdlib only (plus the sibling kyprobe.py). Never reads, prints or stores a credential: environment NAMES only.
"""
import argparse
import concurrent.futures
import json
import os
import plistlib
import pwd
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kyprobe  # noqa: E402  (parse_stream, summarise, sign_in, in_context, disk_markers, user_skill_names, …)

CONFIG_SCHEMA = "ky.launch_config/1"
RECEIPT_SCHEMA = "ky.qualification/1"
MIN_VERSION = kyprobe.MIN_VERSION
LABEL_PREFIX = "in.marsys.kalayantra.qualify."
LOOP_ROLES = ("planner", "conductor")       # kyloop.py fixes their bind key set (expected_binds)
CONFIG_KEYS = ("schema", "role", "model", "effort", "permission_mode", "max_turns", "deadline_seconds", "worktree",
               "claude_bin", "mcp_config", "prompt_path", "env_names", "child_path", "extra_flags",
               "disallowed_tools", "add_dirs", "intended_tools", "denied_tools")
OPTIONAL_KEYS = ("_note", "bash_canary")
BASH_CANARIES = ("write", "readonly")        # readonly: `shasum -a 256 <file>`, nothing may change on disk
TOOL_HOOK_EVENTS = ("PreToolUse", "PostToolUse")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")
CANARY_TOOLS = ("Read", "Write", "Edit", "Bash")
BASE_ENV_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR")
FIXED_ENV_NAMES = BASE_ENV_NAMES + ("ZDOTDIR",)
FORBIDDEN_FLAGS = {
    "--bare": "it never reads the stored sign-in (plan §7 P-1)",
    "--dangerously-skip-permissions": "the permission mode is always passed explicitly",
    "--allow-dangerously-skip-permissions": "the permission mode is always passed explicitly",
    "--settings": "settings come from the project only",
    "--setting-sources": "the launch line fixes it to 'project'",
    "--mcp-config": "the MCP configuration is mcp_config, passed once by the launch line",
}
OWNED_FLAGS = ("--print", "--permission-mode", "--model", "--effort", "--max-turns", "--strict-mcp-config",
               "--disallowedTools", "--disallowed-tools", "--output-format", "--verbose", "--add-dir",
               "--include-hook-events")
BASE_REQUIRED = ("sign_in", "model_identity", "permission_mode_observed", "intended_tools", "no_tty_prompt",
                 "project_claude_md_visible", "excluded_user_plugins", "excluded_user_skills",
                 "excluded_user_hooks", "mcp_none")
PROBES = ("missing_authentication", "inaccessible_keychain", "denied_tools", "invalid_settings", "timeout",
          "termination", "restart")
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{0,39}\Z")
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\[\]-]{0,79}\Z")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")
PLAIN_MATCHER = re.compile(r"^[A-Za-z0-9_]+(\|[A-Za-z0-9_]+)*\Z")    # tool names joined by "|", nothing else
FLAG_RE = re.compile(r"^--[A-Za-z][A-Za-z0-9-]*(=.*)?\Z", re.S)
POLL_S, KILL_WAIT_S, GONE_WAIT_S, SURVIVOR_WAIT_S = 0.05, 5.0, 5.0, 1.0
STOP = threading.Event()

# Canaries. The tool prompts name one tool and one file; the fake harness in the tests answers the same wording.
PROMPT_READ = ("Use the Read tool exactly once to read the file %(name)s in the current directory, then reply with "
               "exactly the text that file contains and nothing else. Use no other tool; if the Read tool is "
               "unavailable or the call is refused, do not try another way: reply with only the word REFUSED.\n")
PROMPT_WRITE = ("Use the Write tool exactly once to create the file %(name)s in the current directory containing "
                "exactly the text %(nonce)s and nothing else, then reply with only the word DONE. Use no other tool; "
                "if the Write tool is unavailable or the call is refused, do not try another way: reply with only "
                "the word REFUSED.\n")
PROMPT_EDIT = ("Use the Edit tool exactly once on the file %(name)s in the current directory (you may read it first) "
               "to replace the text %(old)s with exactly the text %(nonce)s, then reply with only the word DONE. Use "
               "no tool other than Read and Edit; if the Edit tool is unavailable or the call is refused, do not try "
               "another way: reply with only the word REFUSED.\n")
PROMPT_BASH = ("Use the Bash tool exactly once to run exactly this command in the current directory: "
               "printf %%s %(nonce)s > %(name)s\nThen reply with only the word DONE. Use no other tool; if the Bash "
               "tool is unavailable or the command is refused, do not try another way: reply with only the word "
               "REFUSED.\n")
PROMPT_BASH_READONLY = ("Use the Bash tool exactly once to run exactly this command in the current directory: "
                        "shasum -a 256 %(name)s\nThen reply with exactly the 64-character hash it printed and "
                        "nothing else. Use no other tool; if the Bash tool is unavailable or the command is refused, "
                        "do not try another way: reply with only the word REFUSED.\n")
PROMPT_LONG = ("Use the Bash tool exactly once, in the foreground, to run exactly this command: sleep 600\nIf you "
               "cannot run it, instead write out the integers from 1 to 5000, one per line, without stopping or "
               "summarising.\n")
PROMPT_READY = "Reply with exactly the single word READY and use no tool.\n"


class Refusal(Exception):
    """the command refuses; no receipt is written"""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------------------------- small helpers

def load_json_strict(path):
    """(document, None) or (None, reason); a duplicate key, NaN or Infinity refuses the document"""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate key %r" % key)
            out[key] = value
        return out

    def constant(name):
        raise ValueError("%s is not JSON" % name)

    try:
        with open(path, encoding="utf-8") as f:
            return json.loads(f.read(), object_pairs_hook=pairs, parse_constant=constant), None
    except OSError as e:
        return None, "cannot read %s: %s" % (path, type(e).__name__)
    except ValueError as e:
        return None, "%s is not acceptable JSON: %s" % (path, e)


def write_json_atomic(path, obj):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    tmp = os.path.join(directory, ".%s.tmp.%d" % (os.path.basename(path), os.getpid()))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sha_or_none(path):
    try:
        return kyprobe.sha256_file(path)
    except OSError:
        return None


def credential_names(env):
    return sorted(n for n in env if kyprobe.CRED_NAME.match(n))


def version_text(claude_bin):
    """'2.1.296' as printed by `<claude_bin> --version` (the only way this file ever starts the real program
    outside a qualification run), or None"""
    try:
        out = subprocess.run([claude_bin, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out.stdout or "")
    return ".".join(m.groups()) if out.returncode == 0 and m else None


# ------------------------------------------------------------------------------------- launch configuration

def _abs_reason(value):
    if not isinstance(value, str) or not value.startswith("/") or "\n" in value or "\0" in value:
        return "must be an absolute path"
    if value.startswith("//") or os.path.normpath(value) != value:
        return "is not normalised (no trailing slash, '.', '..' or doubled slashes)"
    return None


def _strings(value, unique=True):
    return (isinstance(value, list) and all(isinstance(v, str) and v and "\n" not in v and "\0" not in v for v in value)
            and (not unique or len(set(value)) == len(value)))


def validate_config(doc, check_disk=True):
    """every reason this launch configuration is refused ([] = usable); nothing is launched"""
    if not isinstance(doc, dict):
        return ["the launch configuration must be a JSON object"]
    errs = ["unknown key: %s" % k for k in sorted(set(doc) - set(CONFIG_KEYS) - set(OPTIONAL_KEYS))]
    errs += ["missing key: %s" % k for k in CONFIG_KEYS if k not in doc]
    if errs:
        return errs
    if doc["schema"] != CONFIG_SCHEMA:
        errs.append("schema: must be %r" % CONFIG_SCHEMA)
    if not (isinstance(doc["role"], str) and ROLE_RE.match(doc["role"])):
        errs.append("role: must match %s" % ROLE_RE.pattern)
    if not (isinstance(doc["model"], str) and MODEL_RE.match(doc["model"])):
        errs.append("model: not a model name")
    if doc["effort"] not in EFFORTS:
        errs.append("effort: must be one of %s" % ", ".join(EFFORTS))
    if doc["permission_mode"] not in PERMISSION_MODES:
        errs.append("permission_mode: must be one of %s" % ", ".join(PERMISSION_MODES))
    for key in ("max_turns", "deadline_seconds"):
        if isinstance(doc[key], bool) or not isinstance(doc[key], int) or doc[key] <= 0:
            errs.append("%s: must be an integer greater than 0 (plan §7: a missing or non-positive limit refuses "
                        "launch for every role)" % key)
    if "_note" in doc and not (isinstance(doc["_note"], str) and len(doc["_note"]) <= 1000):
        errs.append("_note: must be a string of at most 1000 characters")
    if "bash_canary" in doc and doc["bash_canary"] not in BASH_CANARIES:
        errs.append("bash_canary: must be one of %s" % ", ".join(BASH_CANARIES))
    for key in ("worktree", "claude_bin", "mcp_config", "prompt_path"):
        reason = _abs_reason(doc[key])
        if reason:
            errs.append("%s: %s" % (key, reason))
    if not _strings(doc["add_dirs"]) or any(_abs_reason(d) for d in doc["add_dirs"]):
        errs.append("add_dirs: must be a list of distinct absolute, normalised paths")
    parts = doc["child_path"].split(":") if isinstance(doc["child_path"], str) else [""]
    if any(_abs_reason(p) for p in parts):
        errs.append("child_path: every entry must be an absolute, normalised path (an empty entry is the current "
                    "directory)")
    if not _strings(doc["extra_flags"], unique=False):
        errs.append("extra_flags: must be a list of non-empty strings")
    else:
        for flag in doc["extra_flags"]:
            name = flag.split("=", 1)[0]
            if not FLAG_RE.match(flag):
                errs.append("extra_flags: %r is not a flag ('--name' or '--name=value'); a bare word would become "
                            "the prompt" % flag)
            elif name in FORBIDDEN_FLAGS:
                errs.append("extra_flags: %s is never allowed (%s)" % (name, FORBIDDEN_FLAGS[name]))
            elif name in OWNED_FLAGS:
                errs.append("extra_flags: %s is set by the launch line itself" % name)
    if not _strings(doc["disallowed_tools"]) or any(t.startswith("-") for t in doc["disallowed_tools"]):
        errs.append("disallowed_tools: must be a list of distinct tool rules, none starting with '-'")
    tools_ok = True
    for key, least in (("intended_tools", 1), ("denied_tools", 0)):
        value = doc[key]
        if not _strings(value) or len(value) < least or any(t not in CANARY_TOOLS for t in value):
            tools_ok = False
            errs.append("%s: must be a list of %sdistinct tools out of %s (the tools this harness has a canary for)"
                        % (key, "one or more " if least else "", ", ".join(CANARY_TOOLS)))
    if tools_ok:
        both = sorted(set(doc["intended_tools"]) & set(doc["denied_tools"]))
        if both:
            errs.append("intended_tools/denied_tools: %s is both intended and denied" % ", ".join(both))
        if "bash_canary" in doc and "Bash" not in doc["intended_tools"] + doc["denied_tools"]:
            errs.append("bash_canary: Bash is neither intended nor denied, so there is no Bash canary to choose")
        if _strings(doc["disallowed_tools"]):
            blocked = sorted(set(doc["intended_tools"]) & set(doc["disallowed_tools"]))
            if blocked:
                errs.append("intended_tools: %s is disallowed by disallowed_tools" % ", ".join(blocked))
    names = doc["env_names"]
    if not _strings(names) or not all(NAME_RE.match(n) for n in names):
        errs.append("env_names: must be a list of distinct environment variable names")
    else:
        missing = [n for n in BASE_ENV_NAMES if n not in names]
        if missing:
            errs.append("env_names: must include %s (plan §7)" % ", ".join(missing))
        for n in names:
            if kyprobe.CRED_NAME.match(n):
                errs.append("env_names: credential variable name %s is never passed to a job" % n)
            elif n not in FIXED_ENV_NAMES and not n.startswith("KY_"):
                errs.append("env value policy unknown: %s" % n)
    if errs or not check_disk:
        return errs
    if not os.path.isdir(doc["worktree"]):
        errs.append("worktree: not a directory: %s" % doc["worktree"])
    if not (os.path.isfile(doc["claude_bin"]) and os.access(doc["claude_bin"], os.X_OK)):
        errs.append("claude_bin: not an executable file: %s" % doc["claude_bin"])
    for key in ("mcp_config", "prompt_path"):
        if sha_or_none(doc[key]) is None:
            errs.append("%s: not a readable file: %s" % (key, doc[key]))
    return errs


def load_config(path):
    doc, err = load_json_strict(path)
    if err:
        raise Refusal(65, err)
    errs = validate_config(doc)
    if errs:
        raise Refusal(65, "launch configuration %s: %s" % (path, "; ".join(errs)))
    return doc


def resolve_env(cfg, caller):
    """({name: value}, [reasons]) for exactly env_names; TMPDIR is None here and filled per run.
    HOME/USER come from the caller; LANG, TERM, PATH and ZDOTDIR are fixed by plan §7; KY_* take their conventional
    value unless the caller's environment sets them; any other name has no value policy and refuses."""
    try:
        me = pwd.getpwuid(os.getuid())
        home, user = caller.get("HOME") or me.pw_dir, caller.get("USER") or me.pw_name
    except KeyError:
        home, user = caller.get("HOME"), caller.get("USER")
    root = caller.get("KY_ROOT") or "/Users/Dev/kalayantra"
    fixed = {"HOME": home, "USER": user, "LANG": "en_US.UTF-8", "TERM": "dumb", "PATH": cfg["child_path"],
             "TMPDIR": None, "ZDOTDIR": root + "/zdotdir"}
    conventional = {
        "KY_ROOT": root, "KY_RUN": root + "/run", "KY_FLEET": root + "/fleet_live", "KY_PY": root + "/venv/bin/python",
        "KY_SCRATCH": "/Users/Dev/scratch.noindex/claude/madhav/%s-kalayantra-v3" % time.strftime("%Y%m%d"),
        "KY_ROLE": cfg["role"], "KY_ITEM": "KV3-B-QUALIFY",     # names are bound; values are per job
        "KY_RUN_ID": "QUALIFY-%s-%s" % (cfg["role"], time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))}
    env, errs = {}, []
    for name in cfg["env_names"]:
        if name in fixed:
            env[name] = fixed[name]
            if name in ("HOME", "USER") and not fixed[name]:
                errs.append("env value unknown: %s is not set for the caller" % name)
        elif name.startswith("KY_") and caller.get(name):
            env[name] = caller[name]
        elif name in conventional:
            env[name] = conventional[name]
        elif name.startswith("KY_"):
            errs.append("env value policy unknown: %s (no conventional value and the caller's environment does "
                        "not set it)" % name)
        else:
            errs.append("env value policy unknown: %s" % name)
    return env, errs


def build_argv(cfg):
    """the plan §7 launch line; for the loop roles it equals kyloop.py's Controller.argv()"""
    argv = [cfg["claude_bin"], "-p", "--setting-sources", "project", "--permission-mode", cfg["permission_mode"],
            "--model", cfg["model"], "--effort", cfg["effort"], "--max-turns", str(cfg["max_turns"])]
    argv += list(cfg["extra_flags"])
    argv += ["--strict-mcp-config", "--mcp-config", cfg["mcp_config"]]
    if cfg["disallowed_tools"]:
        argv += ["--disallowedTools"] + list(cfg["disallowed_tools"])
    argv += ["--output-format", "stream-json", "--verbose"]
    for directory in cfg["add_dirs"]:
        argv += ["--add-dir", directory]
    return argv


def variant(argv, sources=None, mcp_config=None, hook_events=False):
    """(argv', [what differs from the bound argv]) — the only ways a qualification run may differ"""
    out, diff = list(argv), []
    if sources:
        out[out.index("--setting-sources") + 1] = sources
        diff.append("--setting-sources project -> %s" % sources)
    if mcp_config:
        out[out.index("--mcp-config") + 1] = mcp_config
        diff.append("--mcp-config -> a scratch file holding invalid JSON")
    if hook_events:
        out.append("--include-hook-events")
        diff.append("appended --include-hook-events")
    return out, diff


def compute_binds(cfg):
    """what the receipt binds (plan §7 KV-06). Key set = kyloop.py's expected_binds, plus — only when non-empty —
    extra_flags, disallowed_tools and (never for the loop roles, whose key set kyloop fixes) add_dirs; all three
    are inside argv in any case."""
    binds = {"claude_bin": cfg["claude_bin"], "claude_bin_sha256": sha_or_none(os.path.realpath(cfg["claude_bin"])),
             "claude_version": version_text(cfg["claude_bin"]), "argv": build_argv(cfg), "model": cfg["model"],
             "effort": cfg["effort"], "permission_mode": cfg["permission_mode"], "max_turns": cfg["max_turns"],
             "deadline_seconds": cfg["deadline_seconds"], "worktree": cfg["worktree"],
             "env_names": sorted(cfg["env_names"]), "child_path": cfg["child_path"],
             "prompt_sha256": sha_or_none(cfg["prompt_path"]), "mcp_config_sha256": sha_or_none(cfg["mcp_config"])}
    if cfg["extra_flags"]:
        binds["extra_flags"] = list(cfg["extra_flags"])
    if cfg["disallowed_tools"]:
        binds["disallowed_tools"] = list(cfg["disallowed_tools"])
    if cfg["add_dirs"] and cfg["role"] not in LOOP_ROLES:
        binds["add_dirs"] = list(cfg["add_dirs"])
    return binds


def require_program(cfg, text=None):
    """refuse a program older than the pin or one whose version cannot be read (`text`: an already read version)"""
    version = kyprobe.parse_version((version_text(cfg["claude_bin"]) if text is None else text) or "")
    if version is None or version < MIN_VERSION:
        raise Refusal(70, "%s reports version %s; %s or newer is required" % (
            cfg["claude_bin"], ".".join(map(str, version)) if version else "unknown (unparsable)",
            ".".join(map(str, MIN_VERSION))))


# ------------------------------------------------------------------------------------------- running a child

def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_group_gone(pgid, seconds):
    end = time.time() + seconds
    while True:
        if not group_alive(pgid):
            return True
        if time.time() >= end:
            return False
        time.sleep(0.02)


def ps_table(*args):
    """rows of `ps` as lists of words, or None when ps cannot be run"""
    try:
        out = subprocess.run(["/bin/ps"] + list(args), capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return [line.split() for line in out.splitlines() if line.strip()]


def descendants(root):
    """every live descendant pid of `root`, whatever its process group or session; None when unknown"""
    rows = ps_table("-axo", "pid=,ppid=")
    if rows is None:
        return None
    children = {}
    for row in rows:
        if len(row) == 2 and row[0].isdigit() and row[1].isdigit():
            children.setdefault(int(row[1]), []).append(int(row[0]))
    found, queue = [], [root]
    while queue:
        for child in children.get(queue.pop(), []):
            if child not in found:
                found.append(child)
                queue.append(child)
    return sorted(found)


def still_running(pids, seconds):
    """[{pid, command}] for those of `pids` still running (not merely unreaped) after up to `seconds`; None when
    unknown. Observation only: this harness never signals a process outside the process group it started."""
    end = time.time() + seconds
    while True:
        rows = ps_table("-o", "pid=,stat=,comm=", "-p", ",".join(str(p) for p in pids)) if pids else []
        if rows is None:
            return None
        left = [{"pid": int(r[0]), "command": os.path.basename(" ".join(r[2:]))}
                for r in rows if len(r) >= 3 and r[0].isdigit() and not r[1].startswith("Z")]
        if not left or time.time() >= end:
            return sorted(left, key=lambda entry: entry["pid"])
        time.sleep(0.05)


def terminate_group(pgid, proc, grace):
    """TERM the process group, wait `grace`, then KILL what is left; returns the signals actually sent"""
    sent = []
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, KILL_WAIT_S)):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            break
        except PermissionError:
            continue
        sent.append(sig.name)
        end = time.time() + wait
        while time.time() < end:
            if proc.poll() is not None and not group_alive(pgid):
                return sent
            time.sleep(0.02)
    try:
        proc.wait(timeout=KILL_WAIT_S)
    except subprocess.TimeoutExpired:
        pass
    return sent


def scan_tools(stdout_path):
    """(tool names called, tool names whose call came back as an error) as the harness itself streamed them"""
    called, by_id, errors = [], {}, []
    try:
        lines = open(stdout_path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        message = ev.get("message") if isinstance(ev, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if ev.get("type") == "assistant" and block.get("type") == "tool_use":
                by_id[block.get("id")] = str(block.get("name"))
                called.append(str(block.get("name")))
            elif ev.get("type") == "user" and block.get("type") == "tool_result" and block.get("is_error") is True:
                errors.append(by_id.get(block.get("tool_use_id")))
    return called, sorted(set(e for e in errors if e))


def snapshot(root):
    out = {}
    for base, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(base, name)
            out[os.path.relpath(path, root)] = sha_or_none(path)
    return out


def run_child(spec, base_env, grace):
    """one launch of the configuration; returns (record, full reply text). The record is also written as run.json."""
    directory = spec["dir"]
    os.makedirs(os.path.join(directory, "tmp"), exist_ok=True)
    paths = {"prompt_path": os.path.join(directory, "prompt.txt"), "stdout_path": os.path.join(directory, "stdout.jsonl"),
             "stderr_path": os.path.join(directory, "stderr.log")}
    with open(paths["prompt_path"], "w", encoding="utf-8") as f:
        f.write(spec["prompt"])
    env = dict(base_env)
    if "TMPDIR" in env:
        env["TMPDIR"] = os.path.join(directory, "tmp")
    env.update(spec.get("env_override") or {})
    started, t0 = kyprobe.utc(), time.time()
    code = pgid = launch_error = family = survivors = None
    timed_out = terminated = interrupted = False
    sent = []
    with open(paths["prompt_path"], "rb") as fin, open(paths["stdout_path"], "wb") as fout, \
            open(paths["stderr_path"], "wb") as ferr:
        proc = None
        if STOP.is_set():
            interrupted = True
        else:
            try:
                proc = subprocess.Popen(spec["argv"], cwd=spec["cwd"], env=env, stdin=fin, stdout=fout, stderr=ferr,
                                        start_new_session=True)
            except OSError as e:
                launch_error = type(e).__name__
        if proc is not None:
            pgid = proc.pid
            while True:
                try:
                    proc.wait(timeout=POLL_S)
                    break
                except subprocess.TimeoutExpired:
                    pass
                elapsed = time.time() - t0
                if STOP.is_set():
                    interrupted = True
                elif spec.get("term_after") is not None and elapsed >= spec["term_after"]:
                    terminated = True
                elif elapsed >= spec["timeout"]:
                    timed_out = True
                else:
                    continue
                family = descendants(pgid)       # whatever the program started, in any process group
                sent = terminate_group(pgid, proc, grace)
                break
            code = proc.returncode
    group_gone = None
    if pgid is not None:
        # Only the process group this harness started is ever signalled, and only when the harness ends the run:
        # a group that lingers after the program's own exit, and anything the program started outside its group,
        # is recorded and left alone.
        group_gone = wait_group_gone(pgid, GONE_WAIT_S if sent else 1.0)
        if family is not None:
            survivors = still_running(family, SURVIVOR_WAIT_S)
    shown = {k: spec[k] for k in ("id", "kind", "cwd", "argv", "argv_difference") if k in spec}
    shown.update(paths)
    for key in ("tool", "canary", "nonce", "digest", "old", "target", "env_difference", "term_after"):
        if spec.get(key) is not None:
            shown[key] = spec[key]
    rec = kyprobe.summarise(shown, code, timed_out, started, kyprobe.utc())
    init, result, text, _hooks, _bad, _rate = kyprobe.parse_stream(paths["stdout_path"])
    called, errors = scan_tools(paths["stdout_path"])
    denials = result.get("permission_denials") if isinstance(result, dict) else None
    rec.update({
        "timeout_seconds": spec["timeout"], "seconds": round(time.time() - t0, 3), "env_names": sorted(env),
        "pgid": pgid, "launch_error": launch_error, "terminated_by_signal": terminated, "interrupted": interrupted,
        "signals_sent": sent, "group_gone": group_gone, "descendants_at_kill": family,
        "descendants_survived_group_kill": survivors,
        "init_event": init is not None, "result_event": result is not None,
        "tools_offered": kyprobe.names(init.get("tools")) if init is not None and isinstance(init.get("tools"), list) else None,
        "tool_uses": called, "tool_errors": errors,
        "permission_denials": (sorted(str(d.get("tool_name")) for d in denials if isinstance(d, dict))
                               if isinstance(denials, list) else None)})
    write_json_atomic(os.path.join(directory, "run.json"), rec)
    return rec, text


# ------------------------------------------------------------------------------------------ planning the runs

def tool_canary(tool, cwd, bash_canary="write"):
    """prepare one tool canary in `cwd`: the nonce exists only where the tool must put it or read it from"""
    nonce = "KYQ-" + secrets.token_hex(8)
    spec = {"tool": tool, "nonce": nonce, "old": None, "canary": None, "digest": None}
    if tool == "Read":
        name = "CANARY_READ.txt"
        with open(os.path.join(cwd, name), "w") as f:
            f.write(nonce + "\n")
        spec["prompt"] = PROMPT_READ % {"name": name}
    elif tool == "Write":
        name = "CANARY_WRITE.txt"
        spec["prompt"] = PROMPT_WRITE % {"name": name, "nonce": nonce}
    elif tool == "Edit":
        name, spec["old"] = "CANARY_EDIT.txt", "KYQ-OLD-" + secrets.token_hex(8)
        with open(os.path.join(cwd, name), "w") as f:
            f.write(spec["old"] + "\n")
        spec["prompt"] = PROMPT_EDIT % {"name": name, "old": spec["old"], "nonce": nonce}
    elif bash_canary == "readonly":         # the reply must carry a hash only running the command can produce
        name, spec["canary"] = "CANARY_BASH.txt", "readonly"
        with open(os.path.join(cwd, name), "w") as f:
            f.write(nonce + "\n")
        spec["digest"] = kyprobe.sha256_file(os.path.join(cwd, name))
        spec["prompt"] = PROMPT_BASH_READONLY % {"name": name}
    else:
        name, spec["canary"] = "CANARY_BASH.txt", "write"
        spec["prompt"] = PROMPT_BASH % {"name": name, "nonce": nonce}
    spec["target"] = os.path.join(cwd, name)
    spec["before"] = snapshot(cwd)
    return spec


def plan_runs(cfg, ev, a):
    """({run id: spec}, [[spec, …] run in order, …]) — every launch this qualification will make"""
    argv = build_argv(cfg)
    timeout = min(float(a.run_timeout), float(cfg["deadline_seconds"]))
    probe_after = min(float(a.probe_timeout), timeout)
    specs = {}

    def add(run_id, kind, prompt, cwd=None, **more):
        if cwd is None:
            cwd = os.path.join(ev, "canary", run_id)
            os.makedirs(cwd, exist_ok=True)
        spec = {"id": run_id, "kind": kind, "prompt": prompt, "cwd": cwd, "argv": list(argv), "argv_difference": [],
                "timeout": timeout, "dir": os.path.join(ev, "runs", run_id)}
        spec.update(more)
        os.makedirs(spec["dir"], exist_ok=True)
        specs[run_id] = spec
        return spec

    def canary(run_id, kind, tool, **more):
        cwd = os.path.join(ev, "canary", run_id)
        os.makedirs(cwd)
        prepared = tool_canary(tool, cwd, cfg.get("bash_canary", "write"))
        return add(run_id, kind, prepared.pop("prompt"), cwd=cwd, **dict(prepared, **more))

    add("base", "context", kyprobe.PROMPT_CTX, cwd=cfg["worktree"])
    add("empty", "context", kyprobe.PROMPT_CTX)
    for tool in cfg["intended_tools"]:
        canary("tool-" + tool.lower(), "intended", tool)
    for tool in cfg["denied_tools"]:
        canary("deny-" + tool.lower(), "denied", tool)
    hook_argv, diff = variant(argv, hook_events=True)
    canary("hooks", "hooks", "Write", argv=hook_argv, argv_difference=diff)
    if a.control:
        control_argv, diff = variant(argv, sources="user,project", hook_events=True)
        canary("control", "control", "Write", argv=control_argv, argv_difference=diff)
    empty_home = os.path.join(ev, "canary", "empty-home")
    os.makedirs(empty_home)
    add("neg-auth", "negative", PROMPT_READY, env_override={"HOME": empty_home},
        env_difference=["HOME -> an empty scratch directory"])
    spec = add("neg-settings", "negative", PROMPT_READY)
    invalid = os.path.join(spec["dir"], "invalid-mcp.json")
    with open(invalid, "w") as f:
        f.write('{"mcpServers": \n')
    spec["argv"], spec["argv_difference"] = variant(argv, mcp_config=invalid)
    add("neg-timeout", "negative", PROMPT_LONG, timeout=probe_after)
    # terminated and restarted where a real job runs: the restart must succeed in the very directory of the kill
    add("neg-term", "negative", PROMPT_LONG, cwd=cfg["worktree"], term_after=probe_after)
    add("restart", "restart", PROMPT_READY, cwd=cfg["worktree"])
    units = [[s] for run_id, s in specs.items() if run_id not in ("neg-term", "restart")]
    units.append([specs["neg-term"], specs["restart"]])       # the restart follows the termination immediately
    return specs, units


# -------------------------------------------------------------------------------------------------- verdicts

def files_of(*run_ids):
    out = []
    for run_id in run_ids:
        out += ["runs/%s/run.json" % run_id, "runs/%s/stdout.jsonl" % run_id]
    return out


def completed(rec):
    """the run started, reported its own configuration and ended by itself with a result event"""
    return bool(rec["init_event"] and rec["result_event"] and not rec["timed_out"] and not rec["terminated_by_signal"])


def tool_effect(spec, text):
    """what the canary left behind: `landed` = the exact intended effect; `any` = any trace of the nonce or any
    change to the target, by whatever route"""
    tool, nonce = spec["tool"], spec["nonce"]
    after = snapshot(spec["cwd"])
    changed = sorted(k for k in set(after) | set(spec["before"]) if after.get(k) != spec["before"].get(k))
    if tool == "Read":
        return {"landed": nonce in text, "any": nonce in text, "changed_files": changed}
    if spec.get("canary") == "readonly":
        ran = spec["digest"] in text
        return {"landed": ran, "any": ran or bool(changed), "changed_files": changed}
    try:
        content = open(spec["target"], encoding="utf-8", errors="replace").read()
    except OSError:
        content = None
    landed = content is not None and content.strip() == nonce
    traces = os.path.relpath(spec["target"], spec["cwd"]) in changed
    for name in changed:
        try:
            traces = traces or nonce in open(os.path.join(spec["cwd"], name), encoding="utf-8", errors="replace").read()
        except OSError:
            pass
    return {"landed": landed, "any": landed or traces, "changed_files": changed}


def judge_intended(spec, rec, text):
    tool, effect = spec["tool"], tool_effect(spec, text)
    seen = {"run": "runs/" + spec["id"], "effect": effect["landed"], "tool_use_observed": tool in rec["tool_uses"],
            "permission_denials": rec["permission_denials"], "exited_by_itself": not rec["timed_out"]}
    if spec.get("canary"):
        seen.update(canary=spec["canary"], changed_files=effect["changed_files"])
    if rec["permission_denials"]:
        seen.update(result="fail", why="the run ended with a permission denial")
    elif not effect["landed"]:
        seen.update(result="fail", why="the tool's effect was not observed")
    elif spec.get("canary") == "readonly" and effect["changed_files"]:
        seen.update(result="fail", why="a file changed on disk during the read-only canary")
    elif rec["permission_denials"] is None or not completed(rec):
        seen.update(result="unknown", why="the effect is there but the run reported no complete result")
    elif not seen["tool_use_observed"]:
        seen.update(result="unknown", why="the effect is there but no %s call appears in the stream" % tool)
    else:
        seen.update(result="pass", why=None)
    return seen


def judge_denied(spec, rec, text):
    tool, effect = spec["tool"], tool_effect(spec, text)
    offered = None if rec["tools_offered"] is None else tool in rec["tools_offered"]
    denial = []
    if tool in (rec["permission_denials"] or []):
        denial.append("permission_denial")
    if tool in rec["tool_errors"]:
        denial.append("tool_result_error")
    if offered is False:
        denial.append("not_offered")
    seen = {"run": "runs/" + spec["id"], "effect": effect["any"], "changed_files": effect["changed_files"],
            "denial": denial, "offered": offered, "tool_use_observed": tool in rec["tool_uses"]}
    if spec.get("canary"):
        seen["canary"] = spec["canary"]
    if effect["any"]:
        seen.update(result="fail", why="the denied tool's canary left an effect")
    elif not completed(rec):
        seen.update(result="unknown", why="the run did not complete, so the absence of an effect shows nothing")
    elif not denial:
        seen.update(result="unknown", why="no effect, but no denial was observed either (no permission denial, no "
                                          "tool error, and the tool was offered)")
    else:
        seen.update(result="pass", why=None)
    return seen


def user_hook_config(home):
    """([(event name, matcher string or None), …], None) from the user's own settings file, or (None, reason).
    Event names and matcher strings ONLY: no other key or value of that file is kept, printed or stored."""
    try:
        with open(os.path.join(home, ".claude", "settings.json"), encoding="utf-8") as f:
            doc = json.load(f)
    except FileNotFoundError:
        return [], None
    except OSError:
        return None, "the user's settings file cannot be read"
    except ValueError:
        return None, "the user's settings file is not valid JSON"
    hooks = doc.get("hooks") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or not (hooks is None or isinstance(hooks, dict)):
        return None, "the user's settings file has an unexpected shape"
    found = []
    for event, entries in (hooks or {}).items():
        if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
            return None, "the user's hook configuration has an unexpected shape"
        for entry in entries:
            matcher = entry.get("matcher")
            found.append((str(event), matcher if isinstance(matcher, str) else None))
    return found, None


def hook_structure(config, offered):
    """Can any of the user's hooks fire in a configuration that offers exactly `offered` tools? `cannot_fire` is
    true only when every hook is a tool hook (PreToolUse/PostToolUse) whose matcher is a plain alternation of tool
    names and no offered tool equals — or, should the program match unanchored, contains — one of those names."""
    out = {"cannot_fire": False, "reason": None, "user_hook_events": sorted(set(e for e, _ in config)),
           "matcher_tools": None, "offered": None}
    other = sorted(set(e for e, _ in config if e not in TOOL_HOOK_EVENTS))
    if not config:
        out["reason"] = "the user has no hooks in settings.json: nothing to detect structurally"
    elif other:
        out["reason"] = "a hook that needs no tool is configured (%s)" % ", ".join(other)
    elif not all(m is not None and PLAIN_MATCHER.match(m) for _, m in config):
        out["reason"] = "a hook matcher is missing, empty, a wildcard or a regular expression"
    else:
        out["matcher_tools"] = sorted(set(t for _, m in config for t in m.split("|")))
        hit = None if offered is None else sorted(t for t in offered if any(m in t for m in out["matcher_tools"]))
        if hit is None:
            out["reason"] = "the offered tool list was not observed"
        elif hit:
            out["offered"], out["reason"] = True, "an offered tool can trigger a user hook (%s)" % ", ".join(hit)
        else:
            out["offered"], out["cannot_fire"] = False, True
    return out


def worst(results):
    return "fail" if "fail" in results else "pass" if results and all(r == "pass" for r in results) else "unknown"


def judge(cfg, specs, recs, texts, home):
    """(checks, negative_probes) from the run records — pure: no launch happens here"""
    checks, probes = {}, {}
    required = required_checks(cfg, None)

    def put(name, result, observed, evidence):
        checks[name] = {"required": name in required, "result": result, "observed": observed, "evidence": evidence}

    def probe(name, expected, result, observed, why):
        probes[name] = {"expected": expected, "observed": observed, "result": result, "why": why}

    base, empty = recs["base"], recs["empty"]
    obs, res = base.get("observed") or {}, base.get("result") or {}

    # sign_in: a success result with text, through the stored sign-in (apiKeySource "none"), never an API key
    state, source = kyprobe.sign_in(base), obs.get("api_key_source")
    if state == "fails":
        verdict, why = "fail", "the run did not sign in"
    elif state == "works" and source == "none":
        verdict, why = "pass", None
    elif state == "works" and source is not None:
        verdict, why = "fail", "apiKeySource is %r: the run did not use the stored sign-in" % (source,)
    else:
        verdict, why = "unknown", "no success result, or apiKeySource was not reported"
    put("sign_in", verdict, {"sign_in": state, "api_key_source": source, "exit_code": base["exit_code"], "why": why},
        files_of("base"))

    served, used = obs.get("model"), res.get("model_usage_models")
    if served is None or not base["result_event"]:
        verdict = "unknown"
    else:
        verdict = "pass" if served == cfg["model"] and cfg["model"] in (used or []) else "fail"
    put("model_identity", verdict, {"requested": cfg["model"], "init_model": served, "model_usage": used},
        files_of("base"))

    mode = obs.get("permission_mode")
    put("permission_mode_observed", "unknown" if mode is None else "pass" if mode == cfg["permission_mode"] else "fail",
        {"configured": cfg["permission_mode"], "observed": mode}, files_of("base"))

    servers, mcp_tools = obs.get("mcp_servers"), obs.get("mcp_tools")
    put("mcp_none", "unknown" if servers is None else "fail" if (servers or mcp_tools) else "pass",
        {"mcp_servers": servers, "mcp_tools": mcp_tools}, files_of("base"))

    # tools: one canary per tool, judged on what is on disk and what the harness streamed
    for name, kind, fn in (("intended_tools", "intended", judge_intended), ("denied_tools", "denied", judge_denied)):
        per_tool, runs = {}, []
        for spec in specs.values():
            if spec["kind"] == kind:
                per_tool[spec["tool"]] = fn(spec, recs[spec["id"]], texts[spec["id"]])
                runs.append(spec["id"])
        observed = {"tools": per_tool}
        if not per_tool:
            observed["why"] = "the configuration declares no %s tool" % kind
        if name == "denied_tools" and base["tools_offered"] is not None:
            observed["disallowed_tools_still_offered"] = sorted(
                t for t in cfg["disallowed_tools"] if NAME_RE.match(t) and t in base["tools_offered"])
        put(name, worst([t["result"] for t in per_tool.values()]), observed, files_of(*runs))

    # no_tty_prompt: every run of the configuration itself ends by itself, before its deadline, with a result event
    watched = {i: {"exited_by_itself": not (r["timed_out"] or r["terminated_by_signal"]) and r["exit_code"] is not None,
                   "result_event": r["result_event"]}
               for i, r in recs.items() if specs[i]["kind"] in ("context", "intended", "denied", "hooks", "restart")}
    put("no_tty_prompt", "pass" if all(w["exited_by_itself"] and w["result_event"] for w in watched.values()) else "fail",
        {"run_timeout_seconds": specs["base"]["timeout"], "runs": watched}, files_of(*sorted(watched)))

    # project CLAUDE.md: the footer token read from disk is in the reply, and the empty directory does not show it
    token = kyprobe.disk_markers(cfg["worktree"], home)["project_footer"]
    hit = kyprobe.in_context(base, token, "NO_PROJECT_INSTRUCTIONS")
    control = kyprobe.in_context(empty, token, "NO_PROJECT_INSTRUCTIONS")
    if token is None:
        verdict, why = "unknown", "the worktree has no CLAUDE.md with a recognisable footer line"
    elif control is not False:
        verdict, why = "unknown", "the empty-directory negative control is not clean"
    else:
        verdict, why = ("pass", None) if hit is True else ("fail", "the reply says no project instructions are loaded") \
            if hit is False else ("unknown", "the reply shows neither the token nor the explicit absent word")
    put("project_claude_md_visible", verdict,
        {"token_from_disk": token, "in_reply": hit, "negative_control_clean": control is False if token else None,
         "empty_dir_ancestor_claude_md": kyprobe.ancestor_claude_md(specs["empty"]["cwd"]), "why": why},
        files_of("base", "empty"))

    # user-level plugins / skills / hooks: "none" counts only when the control (user settings loaded) shows them
    ctl = recs.get("control")
    cobs = (ctl or {}).get("observed") or {}
    no_control = None if ctl is not None else "no --control run: absence proves nothing"
    lean_plugins, shown_plugins = obs.get("plugins_nonbuiltin"), cobs.get("plugins_nonbuiltin") or []
    if lean_plugins:
        verdict, why = "fail", "user-level plugin(s) are loaded"
    elif lean_plugins is None or not shown_plugins:
        verdict, why = "unknown", no_control or "the control did not show any user-level plugin"
    else:
        verdict, why = "pass", None
    put("excluded_user_plugins", verdict, {"lean": lean_plugins, "control": shown_plugins, "why": why},
        files_of("base", *(["control"] if ctl else [])))

    user_skills = set(kyprobe.user_skill_names(home))

    def user_level(o):
        seen = set(o.get("skills") or []) | set(o.get("slash_commands") or [])
        return sorted((seen & user_skills) | set(x for x in seen if ":" in x))

    lean_skills, shown_skills = (user_level(obs) if obs else None), user_level(cobs)
    if lean_skills:
        verdict, why = "fail", "user-level skill(s) or plugin commands are loaded"
    elif lean_skills is None or not shown_skills:
        verdict, why = "unknown", no_control or "the control did not show any user-level skill"
    else:
        verdict, why = "pass", None
    put("excluded_user_skills", verdict, {"lean": lean_skills, "control": shown_skills, "why": why},
        files_of("base", *(["control"] if ctl else [])))

    # hooks: (1) a hook seen running in the configuration itself is a failure, whatever else holds; (2) structure —
    # the user's hooks cannot fire because no tool they match is offered; (3) otherwise the Write canary + control.
    hk = recs["hooks"]
    lean_hooks = hk["hook_event_names"] if (hk["hook_event_names"] or completed(hk)) else None
    exercised = "Write" in hk["tool_uses"] or tool_effect(specs["hooks"], texts["hooks"])["landed"]
    shown_hooks = (ctl or {}).get("hook_event_names") or []
    config, config_error = user_hook_config(home)
    structure = hook_structure(config, base["tools_offered"]) if config is not None else None
    basis = "canary_and_control"
    if lean_hooks:
        verdict, why, basis = "fail", "hook(s) ran in the configuration itself", "hook_observed"
    elif structure is None:
        verdict, why, basis = "unknown", config_error, "user_settings_unreadable"
    elif structure["cannot_fire"]:
        verdict, why, basis = "pass", None, "cannot_fire"
    elif lean_hooks is None:
        verdict, why = "unknown", "the hook-detection run did not complete"
    elif not shown_hooks:
        verdict, why = "unknown", no_control or (
            "the control showed no hook event: with the user's settings loaded, nothing in this configuration "
            "triggered a hook (is the Write tool offered at all?), so exclusion is not observable here")
    elif not exercised:
        verdict, why = "unknown", "the hook-detection run attempted no Write, so no hook could have fired"
    else:
        verdict, why = "pass", None
    put("excluded_user_hooks", verdict,
        {"basis": basis, "user_hook_events": structure["user_hook_events"] if structure else None,
         "matcher_tools": structure["matcher_tools"] if structure else None,
         "offered": structure["offered"] if structure else None,
         "structure": structure["reason"] if structure else config_error,
         "lean": lean_hooks, "control": shown_hooks, "lean_write_attempted": exercised,
         "write_offered": None if hk["tools_offered"] is None else "Write" in hk["tools_offered"],
         "argv_difference": {"lean": specs["hooks"]["argv_difference"],
                             "control": specs["control"]["argv_difference"] if ctl else None}, "why": why},
        files_of("base", "hooks", *(["control"] if ctl else [])))

    total = res.get("input_tokens_total")
    measured = total if isinstance(total, int) and res.get("num_turns") == 1 and kyprobe.sign_in(base) == "works" else "unknown"
    put("input_overhead_worktree", "pass" if measured != "unknown" else "unknown", measured, files_of("base"))

    # ---- negative probes: each must show its detector reading "no"
    auth = recs["neg-auth"]
    state = kyprobe.sign_in(auth)
    seen = {"run": "runs/neg-auth", "sign_in": state, "exit_code": auth["exit_code"],
            "env_difference": specs["neg-auth"]["env_difference"]}
    if auth["timed_out"]:
        verdict, why = "unknown", "the run did not end by itself"
    elif state == "fails":
        verdict, why = "pass", "without the stored sign-in the run is classified as not signed in"
    elif state == "works":
        verdict, why = "fail", ("sign-in still worked with HOME pointing at an empty directory: the missing-"
                                "authentication condition was not produced, so the sign-in detector was not shown to fail")
    else:
        verdict, why = "unknown", "the run neither succeeded nor failed recognisably"
    probe("missing_authentication", "the sign-in detector reads 'fails'", verdict, seen, why)

    probe("inaccessible_keychain", "the sign-in detector reads 'fails'", "not_simulated", None,
          "cannot be simulated without touching credentials (it would mean locking or altering the login keychain)")

    denied = checks["denied_tools"]
    if cfg["denied_tools"]:
        probe("denied_tools", "no effect and an observed denial for every denied tool", denied["result"],
              {t: {"effect": v["effect"], "denial": v["denial"]} for t, v in denied["observed"]["tools"].items()},
              "the denied_tools check, which is this negative probe")
    else:
        probe("denied_tools", "no effect and an observed denial for every denied tool", "not_simulated", None,
              "the configuration declares no denied tool, and its argv is not altered to invent one")

    bad = recs["neg-settings"]
    bres = bad.get("result") or {}
    seen = {"run": "runs/neg-settings", "exit_code": bad["exit_code"], "result_event": bad["result_event"],
            "is_error": bres.get("is_error"), "argv_difference": specs["neg-settings"]["argv_difference"]}
    if bad["timed_out"]:
        verdict, why = "unknown", "the run did not end by itself"
    elif bres.get("is_error") is False and bres.get("subtype") == "success":
        verdict, why = "fail", "the invalid MCP configuration was accepted: the run succeeded"
    elif bad["exit_code"] not in (0, None) or bres.get("is_error") is True:
        verdict, why = "pass", "the launch failed and was detected as a failure"
    else:
        verdict, why = "unknown", "the run ended with neither a success nor a recognisable failure"
    probe("invalid_settings", "a launch failure is detected", verdict, seen, why)

    for name, run_id, flag, word in (("timeout", "neg-timeout", "timed_out", "deadline"),
                                     ("termination", "neg-term", "terminated_by_signal", "SIGTERM")):
        r = recs[run_id]
        left = r["descendants_survived_group_kill"]
        seen = {"run": "runs/" + run_id, flag: r[flag], "after_seconds": specs[run_id].get("term_after") or specs[run_id]["timeout"],
                "signals_sent": r["signals_sent"], "group_gone": r["group_gone"], "exit_code": r["exit_code"],
                "descendants_at_kill": len(r["descendants_at_kill"]) if r["descendants_at_kill"] is not None else None,
                "descendants_survived_group_kill": [e["command"] for e in left] if left is not None else None}
        if r[flag] and r["group_gone"] is True and r["signals_sent"]:
            verdict, why = "pass", "the %s ended the run, was recorded, and the process group is gone" % word
            if left:        # an observation, not part of the verdict: the brief's claim is about the process group
                why += ("; %d process(es) the run had started outside its group are still running (recorded, "
                        "not signalled)" % len(left))
        elif r[flag]:
            verdict, why = "fail", "the process group was still there after TERM and KILL"
        else:
            verdict, why = "unknown", "the canary run ended by itself first: no %s was produced" % name
        probe(name, "the process group is ended, recorded and gone", verdict, seen, why)

    again = recs["restart"]
    state = kyprobe.sign_in(again)
    seen = {"run": "runs/restart", "sign_in": state, "exit_code": again["exit_code"],
            "after_termination": recs["neg-term"]["terminated_by_signal"]}
    if not recs["neg-term"]["terminated_by_signal"]:
        verdict, why = "unknown", "no termination preceded this run"
    elif state == "works" and completed(again):
        verdict, why = "pass", "a normal run right after the termination succeeds"
    elif state == "fails" or again["timed_out"]:
        verdict, why = "fail", "the run right after the termination did not succeed"
    else:
        verdict, why = "unknown", "the run neither succeeded nor failed recognisably"
    probe("restart", "a normal run succeeds", verdict, seen, why)
    return checks, probes


def required_checks(cfg, context):
    names = list(BASE_REQUIRED)
    if cfg["denied_tools"]:
        names.append("denied_tools")
    if context == "launchd":
        names.append("launchd_context")
    return names


def overall(checks, probes, cfg, context):
    """PASS iff every required check passes and every simulated negative probe passes; any of them failing is
    FAIL; anything else is unknown. Only the keychain probe — and the denied-tools probe of a configuration that
    denies nothing — may be 'not_simulated' without blocking."""
    def result_of(entry):
        value = entry.get("result") if isinstance(entry, dict) else None
        return value if value in ("pass", "fail", "not_simulated") else "unknown"

    found = [result_of(checks.get(name)) for name in required_checks(cfg, context)]
    found = [r if r != "not_simulated" else "unknown" for r in found]
    may_skip = {"inaccessible_keychain"} | (set() if cfg["denied_tools"] else {"denied_tools"})
    for name in PROBES:
        value = result_of(probes.get(name))
        if value == "not_simulated":
            if name in may_skip:
                continue
            value = "unknown"
        found.append(value)
    return "FAIL" if "fail" in found else "PASS" if all(r == "pass" for r in found) else "unknown"


def evidence_files(ev):
    """{relative path: sha256} of what the harness wrote (canary working directories and TMPDIRs excluded)"""
    out = {}
    for base, dirs, files in os.walk(ev):
        rel = os.path.relpath(base, ev)
        dirs[:] = sorted(d for d in dirs if d != "tmp" and not (rel == "." and d == "canary"))
        for name in sorted(files):
            if name.startswith(".") or name.endswith(".tmp"):
                continue
            out[name if rel == "." else os.path.join(rel, name)] = kyprobe.sha256_file(os.path.join(base, name))
    return out


# ---------------------------------------------------------------------------------------------- qualification

def qualify_here(cfg, ev, a, caller):
    """run every canary from THIS process's context; returns {"binds", "checks", "negative_probes"}"""
    env, errs = resolve_env(cfg, caller)
    if errs:
        raise Refusal(65, "; ".join(errs))
    binds = compute_binds(cfg)
    require_program(cfg, binds["claude_version"] or "unknown")
    specs, units = plan_runs(cfg, ev, a)
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: STOP.set())
    recs, texts = {}, {}

    def run_unit(unit):
        return [(spec["id"],) + run_child(spec, env, float(a.term_grace)) for spec in unit]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, int(a.parallel))) as pool:
        for done in pool.map(run_unit, units):
            for run_id, rec, text in done:
                recs[run_id], texts[run_id] = rec, text
    if STOP.is_set():
        raise Refusal(130, "interrupted: every child process group was ended; no receipt is written")
    if compute_binds(cfg) != binds:
        raise Refusal(74, "the program, the prompt or the MCP configuration changed during the run; requalify")
    checks, probes = judge(cfg, specs, recs, texts, env["HOME"])
    return {"binds": binds, "checks": checks, "negative_probes": probes, "offered_tools": recs["base"]["tools_offered"]}


def finish(cfg, context, part, launchd_receipt, ev, out):
    receipt = {"schema": RECEIPT_SCHEMA, "role": cfg["role"], "model": cfg["model"], "context": context,
               "result": overall(part["checks"], part["negative_probes"], cfg, context), "binds": part["binds"],
               "offered_tools": part.get("offered_tools"),     # what the program itself listed in the base run
               "checks": part["checks"], "negative_probes": part["negative_probes"],
               "evidence": {"dir": ev, "files": evidence_files(ev)}, "launchd_receipt": launchd_receipt,
               "generated_at": kyprobe.utc()}
    write_json_atomic(out, receipt)
    print(json.dumps({"out": out, "sha256": kyprobe.sha256_file(out), "result": receipt["result"],
                      "context": context, "role": cfg["role"], "model": cfg["model"]}, sort_keys=True))
    return {"PASS": 0, "FAIL": 1}.get(receipt["result"], 3)


def cmd_qualify(a):
    bad = credential_names(os.environ)
    if bad:
        raise Refusal(78, "credential variable name(s) set: " + ", ".join(bad))
    cfg = load_config(a.config)
    require_program(cfg)
    env, errs = resolve_env(cfg, os.environ)
    if errs:
        raise Refusal(65, "; ".join(errs))
    ev, out = os.path.realpath(a.evidence_dir), os.path.abspath(a.out)
    if os.path.lexists(ev) and (not os.path.isdir(ev) or os.listdir(ev)):
        raise Refusal(73, "%s already holds something; every qualification needs its own evidence directory" % ev)
    inside = os.path.realpath(cfg["worktree"])
    if ev == inside or ev.startswith(inside + os.sep):
        raise Refusal(73, "the evidence directory must be outside the worktree (its canary directories must not "
                          "inherit the project's CLAUDE.md, and nothing is written into the checkout)")
    os.makedirs(ev, exist_ok=True)
    write_json_atomic(os.path.join(ev, "launch_config.json"), cfg)
    if a.context == "shell":
        return finish(cfg, "shell", qualify_here(cfg, ev, a, os.environ), None, ev, out)
    part, launchd_receipt = via_launchd(cfg, ev, a, env["HOME"], env["USER"])
    return finish(cfg, "launchd", part, launchd_receipt, ev, out)


# -------------------------------------------------------------------------------------------- launchd one-shot

def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def launchctl(*args):
    return subprocess.run([os.environ.get("KY_LAUNCHCTL") or "/bin/launchctl"] + list(args), capture_output=True, text=True)


def via_launchd(cfg, ev, a, home, user):
    """wrap the whole qualification in a one-shot launchd user agent (gui/<uid>, RunAtLoad, no KeepAlive), like
    kyprobe.py's `launchd`; returns (the in-agent result, the launchd receipt) or refuses"""
    label, domain = LABEL_PREFIX + cfg["role"], "gui/%d" % os.getuid()
    target, directory = "%s/%s" % (domain, label), os.path.join(ev, "launchd")
    os.makedirs(directory)
    # KY_* overrides of the caller reach the agent through a file: the plist carries PATH/HOME/USER/LANG only.
    write_json_atomic(os.path.join(directory, "caller_env.json"),
                      {n: os.environ[n] for n in cfg["env_names"] if n.startswith("KY_") and os.environ.get(n)})
    args = [a.python, "-u", os.path.realpath(__file__), "launchd-inner", "--config", os.path.join(ev, "launch_config.json"),
            "--evidence-dir", ev, "--label", label, "--run-timeout", str(a.run_timeout),
            "--probe-timeout", str(a.probe_timeout), "--term-grace", str(a.term_grace), "--parallel", str(a.parallel)]
    plist = os.path.join(directory, label + ".plist")
    with open(plist, "wb") as f:
        plistlib.dump({"Label": label, "ProgramArguments": args + (["--control"] if a.control else []),
                       "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": home,
                                                "USER": user, "LANG": "en_US.UTF-8"},
                       "RunAtLoad": True, "ProcessType": "Background",
                       "StandardOutPath": os.path.join(directory, "launchd.out"),
                       "StandardErrorPath": os.path.join(directory, "launchd.err")}, f)
    if subprocess.run(["/usr/bin/plutil", "-lint", plist], capture_output=True).returncode != 0:
        raise Refusal(65, "the rendered plist fails plutil -lint: %s" % plist)
    receipt = {"label": label, "domain": domain, "plist": "launchd/%s.plist" % label,
               "plist_sha256": kyprobe.sha256_file(plist), "bootstrapped_at": kyprobe.utc(), "bootstrap_exit": None,
               "loaded_after_bootstrap": None, "finished": False, "inner": None, "bootout_exit": None,
               "absent_after_bootout": None, "ended_at": None}
    exit_path, inner = os.path.join(directory, "INNER_EXIT.json"), None

    def interrupted(*_):
        raise Refusal(130, "interrupted while the launchd job was running; the agent was booted out")

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    boot = launchctl("bootstrap", domain, plist)
    receipt["bootstrap_exit"] = boot.returncode
    if boot.returncode == 0:          # a failed bootstrap loaded nothing of ours: nothing to boot out
        try:
            receipt["loaded_after_bootstrap"] = launchctl("print", target).returncode == 0
            deadline, orphaned = time.time() + float(a.wait), 0
            while not os.path.exists(exit_path) and time.time() < deadline and orphaned < 3:
                time.sleep(float(a.poll))
                started, _ = load_json_strict(os.path.join(directory, "INNER_STARTED.json"))
                if isinstance(started, dict) and isinstance(started.get("pid"), int) and not pid_alive(started["pid"]):
                    orphaned += 1      # the agent's process is gone; allow its exit record a moment to appear
            started, _ = load_json_strict(os.path.join(directory, "INNER_STARTED.json"))
            settle = time.time() + 10  # let the agent exit by itself, so its log files are final before bootout
            while (os.path.exists(exit_path) and isinstance(started, dict) and isinstance(started.get("pid"), int)
                   and pid_alive(started["pid"]) and time.time() < settle):
                time.sleep(0.05)
        finally:
            receipt["bootout_exit"] = launchctl("bootout", target).returncode
            for _ in range(10):
                receipt["absent_after_bootout"] = launchctl("print", target).returncode != 0
                if receipt["absent_after_bootout"]:
                    break
                time.sleep(float(a.poll))
        inner, _ = load_json_strict(exit_path)
    receipt["ended_at"] = kyprobe.utc()
    part = None
    if isinstance(inner, dict):
        receipt["inner"] = inner.get("context")
        if inner.get("complete") is True:
            part, _ = load_json_strict(os.path.join(directory, "receipt.inner.json"))
    receipt["finished"] = isinstance(part, dict)
    write_json_atomic(os.path.join(directory, "LAUNCHD_RECEIPT.json"), receipt)
    if not receipt["finished"]:
        why = (inner or {}).get("reason") if isinstance(inner, dict) else None
        if boot.returncode != 0:
            why = "launchctl bootstrap failed: %s — if %s is still loaded from an earlier run, `launchctl bootout %s` " \
                  "clears it" % (" ".join((boot.stderr or "").split())[:200] or "no message", label, target)
        raise Refusal(75, "the launchd job did not produce a qualification (bootstrap exit %s; %s); see %s" % (
            boot.returncode, why or "the agent left no exit record (it never started, was killed, or outlived --wait)",
            directory))
    seen = receipt["inner"] if isinstance(receipt["inner"], dict) else {}
    inside = (receipt["loaded_after_bootstrap"] is True and seen.get("ppid") == 1 and seen.get("xpc_service_name") == label)
    if inside and receipt["absent_after_bootout"] is True:
        verdict, why = "pass", None
    elif inside and receipt["absent_after_bootout"] is False:
        verdict, why = "fail", "the one-shot agent is still loaded after bootout"
    else:
        verdict, why = "unknown", "launchd did not report the agent as loaded, or the agent's own context was not launchd's"
    part["checks"]["launchd_context"] = {
        "required": True, "result": verdict, "evidence": [receipt["plist"], "launchd/LAUNCHD_RECEIPT.json"],
        "observed": {"label": label, "domain": domain, "bootstrap_exit": receipt["bootstrap_exit"],
                     "loaded_after_bootstrap": receipt["loaded_after_bootstrap"], "parent_pid": seen.get("ppid"),
                     "xpc_service_name": seen.get("xpc_service_name"), "bootout_exit": receipt["bootout_exit"],
                     "absent_after_bootout": receipt["absent_after_bootout"], "why": why}}
    return part, receipt


def cmd_inner(a):
    """the in-agent half: refuses unless this very process is the launchd job with the expected label"""
    directory = os.path.join(os.path.realpath(a.evidence_dir), "launchd")
    os.makedirs(directory, exist_ok=True)
    context = {"pid": os.getpid(), "ppid": os.getppid(), "xpc_service_name": os.environ.get("XPC_SERVICE_NAME"),
               "label": a.label, "env_names": sorted(os.environ)}
    record = {"complete": False, "reason": None, "context": context}
    write_json_atomic(os.path.join(directory, "INNER_STARTED.json"), {"pid": os.getpid(), "started_at": kyprobe.utc()})
    try:
        if context["ppid"] != 1 or context["xpc_service_name"] != a.label:
            raise Refusal(77, "not inside launchd: parent pid %s (launchd is 1), XPC_SERVICE_NAME %r (the agent's label is %r)"
                          % (context["ppid"], context["xpc_service_name"], a.label))
        bad = credential_names(os.environ)
        if bad:
            raise Refusal(78, "credential variable name(s) set in the agent: " + ", ".join(bad))
        cfg = load_config(a.config)
        overrides, _ = load_json_strict(os.path.join(directory, "caller_env.json"))
        caller = dict(os.environ)
        caller.update({k: v for k, v in (overrides or {}).items() if k.startswith("KY_") and isinstance(v, str)})
        part = qualify_here(cfg, os.path.realpath(a.evidence_dir), a, caller)
        write_json_atomic(os.path.join(directory, "receipt.inner.json"), part)
        record["complete"] = True
        return 0
    except Refusal as r:
        record["reason"] = "%s (exit %d)" % (r, r.code)
        raise
    except Exception as e:
        record["reason"] = "internal error: %s" % type(e).__name__
        raise
    finally:
        write_json_atomic(os.path.join(directory, "INNER_EXIT.json"), record)


# ------------------------------------------------------------------------------------------------------ check

def check_receipt(doc, cfg, require_context=None, verify_evidence=False):
    """every reason this receipt does not qualify this launch configuration, as it is on disk now ([] = it does)"""
    if not isinstance(doc, dict) or doc.get("schema") != RECEIPT_SCHEMA:
        return ["not a %s receipt" % RECEIPT_SCHEMA]
    reasons = []
    for key in ("role", "model"):
        if doc.get(key) != cfg[key]:
            reasons.append("%s: the receipt says %r, the configuration %r" % (key, doc.get(key), cfg[key]))
    context = doc.get("context")
    checks = doc.get("checks") if isinstance(doc.get("checks"), dict) else {}
    probes = doc.get("negative_probes") if isinstance(doc.get("negative_probes"), dict) else {}
    earned = overall(checks, probes, cfg, context)
    if doc.get("result") != "PASS":
        reasons.append("result is %r; only PASS qualifies (FAIL and unknown refuse)" % (doc.get("result"),))
    elif earned != "PASS":
        reasons.append("result: the receipt says PASS but its checks and negative probes evaluate to %s for this "
                       "configuration" % earned)
    lr = doc.get("launchd_receipt")
    if context == "launchd":
        inner = lr.get("inner") if isinstance(lr, dict) and isinstance(lr.get("inner"), dict) else {}
        if not (isinstance(lr, dict) and lr.get("label") == LABEL_PREFIX + cfg["role"] and lr.get("bootstrap_exit") == 0
                and lr.get("loaded_after_bootstrap") is True and lr.get("finished") is True
                and inner.get("ppid") == 1 and inner.get("xpc_service_name") == lr.get("label")
                and lr.get("absent_after_bootout") is True):
            reasons.append("context: labelled launchd without a launchd receipt that shows the agent ran and was removed")
    elif context != "shell" or lr is not None:
        reasons.append("context: must be 'shell' with no launchd receipt, or 'launchd' with one")
    if require_context and context != require_context:
        reasons.append("context: the receipt was earned in %r, %r is required" % (context, require_context))
    for name in ("intended_tools", "denied_tools"):
        observed = (checks.get(name) or {}).get("observed") if isinstance(checks.get(name), dict) else None
        covered = sorted((observed or {}).get("tools") or {}) if isinstance(observed, dict) else []
        if covered != sorted(cfg[name]):
            reasons.append("%s: the receipt covers the tools %s, the configuration declares %s"
                           % (name, covered, sorted(cfg[name])))
    if "Bash" in cfg["intended_tools"] + cfg["denied_tools"]:
        name = "intended_tools" if "Bash" in cfg["intended_tools"] else "denied_tools"
        observed = (checks.get(name) or {}).get("observed") if isinstance(checks.get(name), dict) else None
        used = (((observed or {}).get("tools") or {}).get("Bash") or {}).get("canary") if isinstance(observed, dict) else None
        if used != cfg.get("bash_canary", "write"):
            reasons.append("bash_canary: the receipt used %r, the configuration asks for %r"
                           % (used, cfg.get("bash_canary", "write")))
    expected, got = compute_binds(cfg), doc.get("binds")
    if not isinstance(got, dict):
        reasons.append("binds: missing")
    else:
        diff = sorted(k for k in set(expected) | set(got) if expected.get(k) != got.get(k) or expected.get(k) is None)
        if diff:
            reasons.append("binds differ: %s" % ", ".join(diff))
    version = kyprobe.parse_version(expected["claude_version"] or "")
    if version is None or version < MIN_VERSION:
        reasons.append("program version %s is below %s" % (expected["claude_version"], ".".join(map(str, MIN_VERSION))))
    if verify_evidence:
        evidence = doc.get("evidence") if isinstance(doc.get("evidence"), dict) else {}
        files = evidence.get("files") if isinstance(evidence.get("files"), dict) else None
        if not files or not isinstance(evidence.get("dir"), str):
            reasons.append("evidence: nothing to verify")
        else:
            wrong = sorted(rel for rel, digest in files.items()
                           if sha_or_none(os.path.join(evidence["dir"], rel)) != digest)
            if wrong:
                reasons.append("evidence differs or is missing: %s" % ", ".join(wrong[:20]))
            init = kyprobe.parse_stream(os.path.join(evidence["dir"], "runs", "base", "stdout.jsonl"))[0]
            listed = kyprobe.names(init.get("tools")) if init is not None and isinstance(init.get("tools"), list) else None
            if listed != doc.get("offered_tools"):
                reasons.append("offered_tools: not the tool list of the base run in the evidence")
    return reasons


def cmd_check(a):
    cfg = load_config(a.config)
    doc, err = load_json_strict(a.receipt)
    reasons = [err] if err else check_receipt(doc, cfg, a.require_context, a.verify_evidence)
    print(json.dumps({"check": "REFUSED" if reasons else "PASS", "reasons": reasons, "receipt": a.receipt,
                      "context": doc.get("context") if isinstance(doc, dict) else None}, sort_keys=True))
    return 1 if reasons else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--config", required=True)
        sp.add_argument("--evidence-dir", required=True)
        sp.add_argument("--control", action="store_true",
                        help="also run the positive control (--setting-sources user,project); without it the "
                             "excluded_user_* checks are unknown and the receipt cannot be PASS")
        sp.add_argument("--run-timeout", type=float, default=600.0,
                        help="seconds one canary run may take (never more than deadline_seconds)")
        sp.add_argument("--probe-timeout", type=float, default=3.0,
                        help="deadline of the timeout probe, and the moment SIGTERM is sent in the termination "
                             "probe: a few seconds, shorter than any real run, so both always hit a live process")
        sp.add_argument("--term-grace", type=float, default=10.0)
        sp.add_argument("--parallel", type=int, default=4)

    q = sub.add_parser("qualify")
    common(q)
    q.add_argument("--context", choices=["launchd", "shell"], required=True)
    q.add_argument("--out", required=True)
    q.add_argument("--python", default=sys.executable)
    q.add_argument("--wait", type=float, default=5400.0, help="seconds to wait for the launchd job")
    q.add_argument("--poll", type=float, default=2.0)
    q.set_defaults(fn=cmd_qualify)
    i = sub.add_parser("launchd-inner")
    common(i)
    i.add_argument("--label", required=True)
    i.set_defaults(fn=cmd_inner)
    c = sub.add_parser("check")
    c.add_argument("receipt")
    c.add_argument("--config", required=True)
    c.add_argument("--require-context", choices=["launchd", "shell"])
    c.add_argument("--verify-evidence", action="store_true")
    c.set_defaults(fn=cmd_check)
    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except Refusal as r:
        print("refused: %s" % r, file=sys.stderr)
        return r.code
    except Exception:       # never let a crash look like exit 1 (= a FAIL receipt was written)
        traceback.print_exc()
        print("internal error: no receipt was written", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
