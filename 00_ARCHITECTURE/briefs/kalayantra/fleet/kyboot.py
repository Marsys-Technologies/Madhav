#!/usr/bin/env python3
"""kyboot.py — the bootstrap supervisor: the planner's direct launcher of Wave B jobs.

Relaunch plan v2.7: front-matter pairing rule ("the bootstrap supervisor verifies the manifest and its review
receipt before every bootstrap launch"), §4a.1 (action records), §7 (launch line; launch qualification KV-06;
"Bootstrap (B-1) launches do not go through kyjob.sh or the dispatcher: the planner prepares and validates …,
launches and supervises the process directly, records its process-group identity and termination result"),
§5 (job I/O, CLAUDE_BIN pin), §6 (job identity), §14 B-0c ("separately reviewed; activated from an immutable
staged source bundle; its own proven instance lock; never starts the campaign dispatcher and never uses
fleet_live as a shortcut"). Stdlib only, Python >= 3.9. It never reads a credential and prints the NAMES of
forbidden environment variables only, never a value.

  kyboot.py check <launch_input.json> [--manifest M]   every launch precondition; one named reason per refusal
  kyboot.py argv  <launch_input.json> [--manifest M]   after check: {"cwd", "env", "argv"} — the §7 launch line
  kyboot.py run   <launch_input.json> [--manifest M] [--grace SECONDS]
                                           check, take the item lock, record the action, launch in a new
                                           session, supervise to exit or deadline, record state.json
  kyboot.py submit <launch_input.json> [--manifest M]  check (for the launchd context), render a one-shot
                                           launchd user agent that runs `run`, bootstrap it, return at once
  kyboot.py status [<job_id>]              read-only: state.json, whether the agent's label is loaded, whether
                                           the recorded processes are alive (true | false | "unknown")
  kyboot.py reap   [<job_id>]              boot out the agents of jobs that are positively over; never one whose
                                           job or supervisor is alive or cannot be identified
  kyboot.py validate <schema-name> <file>  shape-check a document against fleet/schemas/<schema-name>.json

Context (a job runs where its qualification was earned): the context is "launchd" only when this process's
parent is pid 1 AND XPC_SERVICE_NAME is the job's own label in.marsys.kalayantra.boot.<job_id> — the way
kyqualify.py proves it — and "shell" otherwise; the receipt's `context` must equal it. `submit` checks against
"launchd" (where the job will run); the `run` it starts checks again from inside the agent. The agent's
environment is PATH, HOME, USER, LANG, KY_RUN, KY_SCRATCH, KY_ROOT and nothing else.

Before EVERY launch (check, argv and run alike), in this order:
  1. the supervisor itself: it does not run from the installed fleet (/Users/Dev/kalayantra/fleet_live or
     $KY_FLEET), and kyboot.py, kyschema.py and kymanifest.py are components of the manifest with exactly the
     reviewed bytes;
  2. the manifest gate: `kymanifest.py check <M> --repo <the repository this file is in> --run <KY_RUN>` exits
     0 (entrypoints, components, generated pairs, probes, qualifications and the ACCEPTED review receipt still
     match disk); M defaults to <KY_RUN>/VERSIONS.bootstrap.json;
  3. the launch input (shape, paths, worktree, program version, hashes, empty MCP configuration, scratch and
     state locations, environment allowlist, flags, effort, turn cap, deadline), bound to the manifest: the same
     approved source commit and plan version, and card_path and mcp_config are manifest components;
  4. the qualification gate: <KY_RUN>/QUALIFICATIONS/<role>-<model>.json is recorded in the manifest, says
     exactly "PASS" and binds this launch (program path, hash and version, model, effort, permission mode, turn
     limit, MCP configuration hash, environment names, and the launch line itself, flag for flag).
`run` then takes <KY_RUN>/locks/kyboot.<item> (one live supervisor per item), writes
<KY_RUN>/actions/ACT-launch-<job_id>.json (INTENDED) before the launch and completes it (DONE | FAILED) with
the observed termination, and records <KY_RUN>/jobs/<job_id>/state.json. It writes nothing else under KY_RUN:
no role-state file, nothing of the dispatcher's, nothing in fleet_live.

Read from kyboot's own environment: KY_SCRATCH (required; the dated campaign scratch folder), KY_RUN (default
/Users/Dev/kalayantra/run), KY_FLEET (only to refuse running from it), KY_LAUNCHCTL (default /bin/launchctl),
XPC_SERVICE_NAME (set by launchd), PATH (to find git and ps), and two TESTS-ONLY names: KY_SCRATCH_ROOT_OVERRIDE
(replaces the root KY_SCRATCH must lie under) and KY_TEST_PPID (stands in for the parent pid, honoured only
when KY_SCRATCH_ROOT_OVERRIDE is also set). The use of either is recorded in state.json.

Exit: 0   check / argv / validate / status passed; run: the job exited 0 and any result.json it left is valid;
          submit: launchctl bootstrap exited 0; reap: every agent it booted out is confirmed absent
      1   refused (every reason on stderr) — nothing was launched or submitted
      2   malformed command, unknown schema name, or a schema that kyschema refuses
      3   run: the job could not be started, exited non-zero, or left an invalid result.json;
          submit: launchctl bootstrap failed; reap: an agent is still loaded after bootout
      5   run: the job's process group could not be confirmed gone (the item lock is then left in place)
      78  a credential variable name is set in kyboot's own environment (names printed, values never read)
      124 run: the deadline passed (the group was terminated)      130 run: the supervisor was signalled

What `check` passing means: the reviewed source, the manifest, the qualification and the launch input agreed
and the facts they name were true when checked. It is not a review of the prompt or the packet, and `run`
exiting 0 is not acceptance of the job's work (plan §7: independent review follows).

Limits, stated rather than hidden:
  * the group is the unit of supervision: a descendant that leaves the job's session / process group is not
    seen, and `group_gone` says nothing about it;
  * "gone" is `killpg(pgid, 0)` → ESRCH, asked after the leader has been collected. Signals after that point
    go to a group id that only its surviving members keep reserved;
  * a process identity is (pid, the text `LC_ALL=C ps -o lstart=` prints): local time, one-second resolution;
  * on Linux an exited-but-uncollected member still answers `killpg(…, 0)`, so a job whose children are
    collected late may be reported as `leftover_group: "terminated"` there; on macOS it is waited out;
  * the supervisor verifies the bytes on disk of the code it runs, at check time; it cannot prove what an
    interpreter loaded earlier, and the manifest gate is as strong as the reviewed kymanifest.py;
  * the qualification receipt is read for the fields compared here; its other fields are not judged;
  * `submit` returns when launchd has accepted the agent, not when the job has started: what the job did is in
    state.json and <job_scratch>/supervisor.err (`status`). A `run` that refuses inside the agent writes no
    state.json, so `reap` leaves that label loaded (its job's identity is unknown) for a person to boot out.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import plistlib
import pwd
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

FLEET = Path(__file__).resolve().parent
sys.path.insert(0, str(FLEET))

import kyschema  # noqa: E402

SCHEMA_DIR = FLEET / "schemas"
LAUNCH_SCHEMA = "bootstrap_launch_input"
STATE_SCHEMA = "ky.bootstrap_job_state/2"
MANIFEST_SCHEMA = "ky.versions_bootstrap/1"
QUALIFICATION_SCHEMA = "ky.qualification/1"
ACTION_SCHEMA = "ky.action/1"

EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_JOB_FAILED, EXIT_GROUP_SURVIVED = 0, 1, 2, 3, 5
EXIT_CREDENTIAL_ENV, EXIT_TIMED_OUT, EXIT_INTERRUPTED = 78, 124, 130

DEFAULT_KY_RUN = "/Users/Dev/kalayantra/run"
INSTALLED_FLEET = "/Users/Dev/kalayantra/fleet_live"       # never the supervisor's home (plan §14 B-0c)
SUPERVISOR_CODE = ("kyboot.py", "kyschema.py", "kymanifest.py")    # everything this supervisor runs or imports
MANIFEST_BOUND_FILES = (("card_path", "card_sha256"), ("mcp_config", "mcp_config_sha256"))
LSTART_FMT = "%a %b %d %H:%M:%S %Y"                        # `LC_ALL=C ps -o lstart=`, as kyloop.py pins it
LOCK_OWNER_WAIT_SECONDS = 1.0
LABEL_PREFIX = "in.marsys.kalayantra.boot."                # + <job_id>: the one-shot agent of one bootstrap job
DEFAULT_LAUNCHCTL = "/bin/launchctl"
PLUTIL = "/usr/bin/plutil"
AGENT_PATH = "/opt/homebrew/bin:/usr/bin:/bin"
AGENT_ENV_NAMES = ("PATH", "HOME", "USER", "LANG", "KY_RUN", "KY_SCRATCH", "KY_ROOT")   # the agent's whole environment
ABSENT_CONFIRM_SECONDS = 2.0
DEFAULT_SCRATCH_ROOT = "/Users/Dev/scratch.noindex"
SCRATCH_ROOT_NEVER = ("/tmp", "/private/tmp", "/var/tmp", "/private/var/tmp")    # owner policy: never /tmp
DEFAULT_GRACE_SECONDS = 20.0
KILL_CONFIRM_SECONDS = 10.0
POLL_SECONDS = 0.05
SESSION_SCAN_BYTES = 262144

# plan §7 launch line: the only names a job's environment may carry
ENV_ALLOWLIST = ("HOME", "PATH", "LANG", "TERM", "USER", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
                 "KY_STREAM", "KY_LANE", "KY_ITEM", "KY_PY", "SE_EPHE_PATH", "SWE_EPHE_PATH", "TESTS")
ENV_REQUIRED = ("HOME", "PATH", "KY_ROOT", "TMPDIR")
ENV_PATH_VALUED = ("HOME", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_PY", "SE_EPHE_PATH",
                   "SWE_EPHE_PATH")
ENV_FORBIDDEN = re.compile(r"^(DATABASE_URL|.*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY|.*TOKEN.*|.*SECRET.*)\Z",
                           re.IGNORECASE)
OWN_ENV_CREDENTIAL = re.compile(r"^(DATABASE_URL|.*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY)\Z")

# plan §7 turn caps (ARTIFACT is the verifier's job kind and takes the VERIFY cap)
TURN_CAPS = {"BUILD": 150, "REWORK": 100, "VERIFY": 60, "ARTIFACT": 60, "PLAN": 300}

FLAGS_NEVER = {
    "--bare": "P-1: it never reads the stored sign-in and accepts only an API key",
    "--dangerously-skip-permissions": "the permission mode is always passed explicitly",
    "--mcp-config": "the MCP configuration is the launch input's mcp_config, passed once by the launcher",
    "--settings": "settings come from the project only",
    "--setting-sources": "the launcher passes --setting-sources project itself",
}
FLAGS_LAUNCHER_OWNED = ("--print", "--permission-mode", "--model", "--effort", "--max-turns",
                        "--strict-mcp-config", "--output-format", "--verbose", "--add-dir")
FLAG_PREFIXES_NEVER = ("--dangerously-", "--allow-dangerously-")

PATH_FIELDS = ("worktree", "claude_bin", "mcp_config", "prompt_path", "card_path", "packet_path", "job_scratch",
               "stdout_path", "stderr_path", "tmp_path", "state_path")
HASHED_FILES = (("prompt_path", "prompt_sha256"), ("card_path", "card_sha256"), ("packet_path", "packet_sha256"),
                ("mcp_config", "mcp_config_sha256"))
BENEATH_JOB_SCRATCH = ("prompt_path", "stdout_path", "stderr_path", "tmp_path")
EMPTY_MCP = {"mcpServers": {}}

_PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9_]*>")
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?=\s|\Z)")
_UTC = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d{1,6})?(?:Z|\+00:00)\Z")
_HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_LABEL_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)*\Z")
_HEX64 = re.compile(r"^[0-9a-f]{64}\Z")


# --------------------------------------------------------------------------------------------------------------
# small pure helpers
# --------------------------------------------------------------------------------------------------------------
def own_env_credentials(environ) -> list:
    """names (never values) of credential variables set in the supervisor's own environment (plan §7: exit 78)"""
    return sorted(name for name in environ if OWN_ENV_CREDENTIAL.match(name))


def forbidden_env_name(name: str) -> bool:
    return bool(ENV_FORBIDDEN.match(name))


def parse_version(text: str):
    """(X, Y, Z) from the first line of `--version` output, or None when it does not start with X.Y.Z"""
    lines = text.strip().splitlines()
    match = _VERSION.match(lines[0].strip()) if lines else None
    return tuple(int(part) for part in match.groups()) if match else None


def parse_utc(text: str):
    """epoch seconds of a UTC ISO-8601 timestamp ('Z' or '+00:00'); None for anything else, local time included"""
    match = _UTC.match(text) if isinstance(text, str) else None
    if not match:
        return None
    year, month, day, hour, minute, second = (int(part) for part in match.groups()[:6])
    try:
        whole = _dt.datetime(year, month, day, hour, minute, second, tzinfo=_dt.timezone.utc)
    except ValueError:
        return None
    return whole.timestamp() + float(match.group(7) or 0)


def utc_now_text() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json_and_sha(path):
    """(the strictly parsed document, the sha256 of the very bytes it was parsed from); ValueError says why not"""
    try:
        data = Path(path).read_bytes()
    except OSError as unreadable:
        raise ValueError(f"cannot read {path}: {unreadable}") from None
    try:
        return kyschema.load_json_text(data.decode("utf-8")), hashlib.sha256(data).hexdigest()
    except (ValueError, UnicodeDecodeError) as bad:
        raise ValueError(f"{path} is not acceptable JSON: {bad}") from None


def _show(value) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= 120 else text[:117] + "..."


def _is_beneath(path: str, parent: str) -> bool:
    return path.startswith(parent.rstrip(os.sep) + os.sep)


def _placeholders(value, path="$"):
    if isinstance(value, str):
        if _PLACEHOLDER.search(value):
            yield f"{path}: unfilled placeholder {value!r}"
    elif isinstance(value, list):
        for index, element in enumerate(value):
            yield from _placeholders(element, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, element in value.items():
            if isinstance(key, str) and _PLACEHOLDER.search(key):
                yield f"{path}: unfilled placeholder in the name {key!r}"
            yield from _placeholders(element, f"{path}.{key}")


def _value_free(error: str) -> str:
    """a schema refusal of a free-text launch field, without echoing the refused value"""
    path = error.split(": ", 1)[0]
    if not path.startswith(("$.extra_lean_flags", "$.disallowed_tools", "$.env")):
        return error
    location = error[error.rfind(" (schema "):] if " (schema " in error else ""
    return f"{path}: refused by the launch-input schema (value not shown){location}"


def _git(worktree, environ, *args):
    """read-only git (rev-parse, merge-base) with no inherited GIT_* redirection and no optional locks"""
    env = {name: value for name, value in environ.items() if not name.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        done = subprocess.run(["git", "-C", worktree, *args], capture_output=True, text=True, env=env,
                              timeout=30, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as failed:
        return 127, f"git could not be run: {failed}"
    return done.returncode, done.stdout.strip()


def schema_names() -> list:
    return sorted(path.stem for path in SCHEMA_DIR.glob("*.json"))


def load_schema(name: str):
    return kyschema.load_json(SCHEMA_DIR / f"{name}.json")


# --------------------------------------------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------------------------------------------
class Checked:
    """the outcome of `check`: .launch (None when unreadable), .findings (every refusal), .facts (what was observed)"""

    def __init__(self, launch, findings, facts):
        self.launch, self.findings, self.facts = launch, findings, facts

    @property
    def ok(self) -> bool:
        return not self.findings


def resolve_scratch(environ, findings):
    """(realpath of KY_SCRATCH, the root it must lie under, whether the override is in use) or (None, root, flag)"""
    override = environ.get("KY_SCRATCH_ROOT_OVERRIDE")
    root = os.path.realpath(DEFAULT_SCRATCH_ROOT)
    if override is not None:
        if not os.path.isabs(override) or not os.path.isdir(override):
            findings.append("KY_SCRATCH_ROOT_OVERRIDE: is set but is not an existing absolute directory")
            return None, root, True
        root = os.path.realpath(override)
        if any(root == never or _is_beneath(root, never) for never in SCRATCH_ROOT_NEVER):
            findings.append(f"KY_SCRATCH_ROOT_OVERRIDE: {root} is under a system temporary directory "
                            f"(scratch never lives under /tmp)")
            return None, root, True
    scratch = environ.get("KY_SCRATCH")
    if not scratch:
        findings.append("KY_SCRATCH: not set in the environment (the dated campaign scratch folder is required)")
        return None, root, override is not None
    if not os.path.isabs(scratch) or not os.path.isdir(scratch):
        findings.append(f"KY_SCRATCH: {scratch!r} is not an existing absolute directory")
        return None, root, override is not None
    real = os.path.realpath(scratch)
    if not _is_beneath(real, root):
        findings.append(f"KY_SCRATCH: {real} is not beneath the scratch root {root}")
        return None, root, override is not None
    return real, root, override is not None


def env_findings(launch, ky_run) -> list:
    out = []
    env = launch["env"]
    for name in sorted(env):
        if forbidden_env_name(name):
            out.append(f"env: {name} is a forbidden credential-bearing name")
        if name not in ENV_ALLOWLIST:
            out.append(f"env: {name} is not in the plan §7 allowlist")
        value = env[name]
        if not isinstance(value, str) or "\x00" in value:
            out.append(f"env.{name}: the value must be a string without NUL")
    for name in ENV_REQUIRED:
        if name not in env:
            out.append(f"env: required name {name} is missing")
    for name in ENV_PATH_VALUED:
        value = env.get(name)
        if isinstance(value, str) and not os.path.isabs(value):
            out.append(f"env.{name}: not an absolute path: {value!r}")
    if isinstance(env.get("PATH"), str):
        for entry in env["PATH"].split(os.pathsep):
            if not os.path.isabs(entry):
                out.append(f"env.PATH: entry {entry!r} is not an absolute path")
    if "TMPDIR" in env and env["TMPDIR"] != launch["tmp_path"]:
        out.append(f"env.TMPDIR: {env['TMPDIR']!r} must equal tmp_path {launch['tmp_path']!r}")
    if "KY_RUN" in env and env["KY_RUN"] != ky_run:
        out.append(f"env.KY_RUN: {env['KY_RUN']!r} differs from the supervisor's KY_RUN {ky_run!r}")
    if "KY_ITEM" in env and env["KY_ITEM"] != launch["item"]:
        out.append(f"env.KY_ITEM: {env['KY_ITEM']!r} differs from item {launch['item']!r}")
    root = env.get("KY_ROOT")
    if isinstance(root, str) and os.path.isabs(root) and not os.path.isdir(root):
        out.append(f"env.KY_ROOT: {root} is not an existing directory (it is passed as --add-dir)")
    return out


def flag_findings(flags) -> list:
    out = []
    for flag in flags:
        name = flag.split("=", 1)[0]                 # the name only: a value is never echoed
        if name in FLAGS_NEVER:
            out.append(f"extra_lean_flags: {name} is forbidden ({FLAGS_NEVER[name]})")
        elif name in FLAGS_LAUNCHER_OWNED:
            out.append(f"extra_lean_flags: {name} is forbidden (the launch line sets {name} itself)")
        elif name.startswith(FLAG_PREFIXES_NEVER):
            out.append(f"extra_lean_flags: {name} is forbidden (no permission bypass by flag)")
    return out


def clean_env(launch) -> dict:
    """the job's whole environment: the launch input's allowlisted env, nothing inherited (check has required it
    to carry TMPDIR and that TMPDIR to be tmp_path)"""
    return {name: launch["env"][name] for name in sorted(launch["env"]) if name in ENV_ALLOWLIST}


def _git_findings(launch, environ, facts) -> list:
    out = []
    worktree = launch["worktree"]
    if not os.path.isdir(worktree):
        return [f"worktree: does not exist or is not a directory: {worktree}"]
    # one question, four answers: inside a work tree · its top level · HEAD's commit · HEAD's branch
    # (a repository without a commit answers the first two and then fails; anything else answers nothing)
    code, answer = _git(worktree, environ, "rev-parse", "--is-inside-work-tree", "--show-toplevel", "HEAD",
                        "--symbolic-full-name", "HEAD")
    lines = answer.split("\n")
    if len(lines) < 2 or lines[0] != "true":
        return [f"worktree: not a git work tree: {worktree}"]
    if os.path.realpath(lines[1]) != os.path.realpath(worktree):
        return [f"worktree: is not the top level of its git work tree (top level is {lines[1]})"]
    if code != 0 or len(lines) != 4 or not _HEX40.match(lines[2]):
        return ["worktree: HEAD does not name a commit"]
    head, head_ref = lines[2], lines[3]
    facts["worktree_head"] = head
    if head_ref != "refs/heads/" + launch["branch"]:
        actual = head_ref[len("refs/heads/"):] if head_ref.startswith("refs/heads/") else "a detached HEAD"
        out.append(f"branch: the worktree is on {actual!r}, the launch input says {launch['branch']!r}")
    code, _ = _git(worktree, environ, "merge-base", "--is-ancestor", launch["base_sha"], "HEAD")
    if code == 1:                                      # git: 0 an ancestor · 1 not one · anything else: no such commit
        out.append(f"base_sha: {launch['base_sha']} is not an ancestor of HEAD {head}")
    elif code != 0:
        out.append(f"base_sha: {launch['base_sha']} is not a commit in the worktree's repository")
    code, _ = _git(worktree, environ, "rev-parse", "--verify", "--quiet", launch["approved_source_commit"] + "^{commit}")
    if code != 0:
        out.append(f"approved_source_commit: {launch['approved_source_commit']} is not a commit in the worktree's "
                   f"repository")
    return out


def _claude_findings(launch, facts) -> list:
    binary = launch["claude_bin"]
    if not os.path.isfile(binary):
        return [f"claude_bin: does not exist or is not a file: {binary}"]
    if not os.access(binary, os.X_OK):
        return [f"claude_bin: not executable: {binary}"]
    facts["claude_bin_realpath"] = os.path.realpath(binary)
    try:
        facts["claude_bin_sha256"] = sha256_file(facts["claude_bin_realpath"])
    except OSError as unreadable:
        return [f"claude_bin: cannot be read: {unreadable}"]
    env = clean_env(launch)
    env.pop("TMPDIR", None)                       # tmp_path need not exist before `run`
    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True, env=env, timeout=60,
                              stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError) as failed:
        return [f"claude_bin: --version could not be run: {failed}"]
    if done.returncode != 0:
        return [f"claude_bin: --version exited {done.returncode}"]
    found = parse_version(done.stdout)
    first = (done.stdout.strip().splitlines() or [""])[0]
    if found is None:
        return [f"claude_bin: version output is not X.Y.Z: {first[:80]!r}"]
    facts["claude_version"] = first.strip()
    minimum = parse_version(launch["claude_min_version"])
    if minimum is None or found < minimum:
        return [f"claude_bin: version {'.'.join(map(str, found))} is below the pinned minimum "
                f"{launch['claude_min_version']}"]
    return []


def _file_findings(launch) -> list:
    out = []
    for path_field, hash_field in HASHED_FILES:
        path = launch[path_field]
        if not os.path.isfile(path):
            out.append(f"{path_field}: does not exist or is not a file: {path}")
            continue
        try:
            actual = sha256_file(path)
        except OSError as unreadable:
            out.append(f"{path_field}: cannot be read: {unreadable}")
            continue
        if actual != launch[hash_field]:
            out.append(f"{path_field}: sha256 mismatch: the file is {actual}, {hash_field} says {launch[hash_field]}")
    if os.path.isfile(launch["mcp_config"]):
        try:
            content = kyschema.load_json(launch["mcp_config"])
        except ValueError as bad:
            out.append(f"mcp_config: {bad}")
        else:
            if type(content) is not dict or not kyschema.json_equal(content, EMPTY_MCP):
                out.append('mcp_config: the content must be exactly {"mcpServers":{}} for a bootstrap job')
    return out


def _location_findings(launch, environ, ky_run, facts) -> list:
    out = []
    job_id = launch["job_id"]
    scratch, root, overridden = resolve_scratch(environ, out)
    facts["scratch_root"], facts["scratch_root_override"], facts["ky_scratch"] = root, overridden, scratch
    expected_state = os.path.join(ky_run, "jobs", job_id, "state.json")
    if launch["state_path"] != expected_state:
        out.append(f"state_path: {launch['state_path']} is not <KY_RUN>/jobs/<job_id>/state.json = "
                   f"{expected_state}")
    job_real = os.path.realpath(launch["job_scratch"])
    if scratch is not None:
        expected = os.path.join(scratch, "jobs", job_id)
        if job_real != expected:
            out.append(f"job_scratch: {job_real} is not <KY_SCRATCH>/jobs/<job_id> = {expected}")
    for field in BENEATH_JOB_SCRATCH:
        real = os.path.realpath(launch[field])
        if not _is_beneath(real, job_real):
            out.append(f"{field}: {real} is not beneath job_scratch {job_real}")
    reals = [os.path.realpath(launch[field]) for field in BENEATH_JOB_SCRATCH]
    reals.append(os.path.join(job_real, "result.json"))
    if len(set(reals)) != len(reals):
        out.append("job_scratch: prompt_path, stdout_path, stderr_path, tmp_path and result.json must all differ")
    if os.path.lexists(launch["tmp_path"]) and not os.path.isdir(launch["tmp_path"]):
        out.append(f"tmp_path: {launch['tmp_path']} exists and is not a directory")
    return out


# --------------------------------------------------------------------------------------------------------------
# the reviewed source: supervisor, manifest gate, qualification gate (plan v2.7 pairing rule, §7 KV-06)
# --------------------------------------------------------------------------------------------------------------
def job_label(job_id: str) -> str:
    return LABEL_PREFIX + job_id


def parent_pid(environ):
    """(parent pid, whether it was injected). In production this is the real parent, os.getppid().
    TESTS ONLY: KY_TEST_PPID replaces it, and ONLY when KY_SCRATCH_ROOT_OVERRIDE (itself tests-only) is also set —
    a test cannot make launchd, pid 1, the parent of a process it starts. The injection is recorded in state.json."""
    if environ.get("KY_SCRATCH_ROOT_OVERRIDE") is not None and environ.get("KY_TEST_PPID") is not None:
        try:
            return int(environ["KY_TEST_PPID"]), True
        except ValueError:
            return -1, True
    return os.getppid(), False


def detect_context(environ, job_id: str):
    """("launchd" | "shell", whether the parent pid was injected). "launchd" only when this very process is the
    launchd job of this launch: its parent is pid 1 AND XPC_SERVICE_NAME is the job's label — the proof
    kyqualify.py requires of a launchd qualification. Anything else is "shell"."""
    parent, injected = parent_pid(environ)
    inside = parent == 1 and environ.get("XPC_SERVICE_NAME") == job_label(job_id)
    return ("launchd" if inside else "shell"), injected


def manifest_canonical(obj) -> bytes:
    """the bytes kymanifest.py digests (its `canonical`): sorted keys, compact separators, UTF-8"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def installed_fleet_root(path, environ):
    """the installed-fleet root `path` lies in (fleet_live, or $KY_FLEET), or None"""
    real = os.path.realpath(path)
    for root in (INSTALLED_FLEET, environ.get("KY_FLEET")):
        if root and os.path.isabs(root):
            base = os.path.realpath(root)
            if real == base or _is_beneath(real, base):
                return root
    return None


def run_manifest_check(kymanifest_path, manifest_path, source_repo, ky_run, environ):
    """(exit code, stdout, stderr) of the reviewed sibling: kymanifest.py check <manifest> --repo … --run …"""
    env = {name: value for name, value in environ.items() if not name.startswith("GIT_")}
    try:
        done = subprocess.run([sys.executable, "-I", "-B", kymanifest_path, "check", manifest_path,
                               "--repo", source_repo, "--run", ky_run], capture_output=True, text=True, env=env,
                              timeout=600, stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError) as failed:
        return 127, "", f"kymanifest.py could not be run: {failed}"
    return done.returncode, done.stdout, done.stderr


def load_manifest(manifest_path):
    """(manifest, components {path: sha256}, sha256 of the manifest file, findings): the manifest's own
    shape and digest, nothing about disk"""
    try:
        manifest, file_sha = read_json_and_sha(manifest_path)
    except ValueError as bad:
        return None, {}, None, [f"manifest: {bad}"]
    if type(manifest) is not dict or manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("mode") != "bootstrap":
        return None, {}, None, [f"manifest: {manifest_path} is not a {MANIFEST_SCHEMA} manifest in mode bootstrap"]
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != hashlib.sha256(manifest_canonical(body)).hexdigest():
        return None, {}, None, ["manifest: manifest_sha256 does not match the manifest's content"]
    if not isinstance(manifest.get("approved_source_commit"), str) \
            or not _HEX40.match(manifest["approved_source_commit"]):
        return None, {}, None, ["manifest: approved_source_commit is not a 40-hex commit id"]
    components = {}
    listed = manifest.get("components")
    for entry in listed if isinstance(listed, list) else [None]:
        if type(entry) is not dict or not isinstance(entry.get("path"), str) \
                or not isinstance(entry.get("sha256"), str) or not _HEX64.match(entry["sha256"]) \
                or entry["path"] in components:
            return None, {}, None, ["manifest: components is not a list of distinct {path, sha256} entries"]
        components[entry["path"]] = entry["sha256"]
    return manifest, components, file_sha, []


def manifest_gate(manifest_path, ky_run, environ, facts):
    """(manifest or None, components, findings): the supervisor is the reviewed code and the manifest gate passes"""
    findings = []
    own = os.path.realpath(__file__)
    facts["supervisor_path"], facts["manifest_path"] = own, manifest_path
    try:
        facts["supervisor_sha256"] = sha256_file(own)
    except OSError as unreadable:
        return None, {}, [f"supervisor: cannot read its own file {own}: {unreadable}"]
    installed = installed_fleet_root(own, environ)
    if installed:
        findings.append(f"supervisor: {own} runs from the installed fleet {installed}; the bootstrap supervisor "
                        f"runs only from the reviewed staged source")
    code, top = _git(os.path.dirname(own), environ, "rev-parse", "--show-toplevel")
    if code != 0 or not top:
        return None, {}, findings + [f"supervisor: {own} is not inside a git work tree; there is no reviewed "
                                     f"source to verify it against"]
    source = os.path.realpath(top)
    facts["source_repo"] = source
    manifest, components, file_sha, problems = load_manifest(manifest_path)
    if manifest is None:
        return None, {}, findings + problems
    facts["manifest_sha256"], facts["manifest_file_sha256"] = manifest["manifest_sha256"], file_sha

    reviewed_code = True
    for name in SUPERVISOR_CODE:
        path = os.path.join(os.path.dirname(own), name)
        relative = os.path.relpath(path, source)
        if relative not in components:
            findings.append(f"supervisor: {relative} is not a component of the manifest")
            reviewed_code = False
            continue
        try:
            actual = sha256_file(path)
        except OSError:
            actual = "unreadable"
        if actual != components[relative]:
            findings.append(f"supervisor: {relative} is not the reviewed file (sha256 {actual}, the manifest "
                            f"says {components[relative]})")
            reviewed_code = False
    if not reviewed_code:
        findings.append("manifest gate: kymanifest.py check was not run because the supervisor's own code is not "
                        "the reviewed code")
        return manifest, components, findings
    code, out, err = run_manifest_check(os.path.join(os.path.dirname(own), "kymanifest.py"), manifest_path, source,
                                        ky_run, environ)
    if code != 0:
        first = (err.strip().splitlines() or [f"kymanifest.py check exited {code}"])[0]
        findings.append(f"manifest gate: {first}")
        return manifest, components, findings
    try:
        said = json.loads(out)
    except ValueError:
        said = None
    if type(said) is not dict or said.get("ok") is not True \
            or said.get("manifest_sha256") != manifest["manifest_sha256"]:
        findings.append("manifest gate: kymanifest.py check exited 0 without confirming this manifest's digest")
    return manifest, components, findings


def binding_findings(launch, manifest, components, facts) -> list:
    """the launch input is bound to the reviewed manifest: commit, plan version, and the card and MCP files"""
    out = []
    if manifest.get("plan_version") != launch["plan_version"]:
        out.append(f"manifest: its plan_version {manifest.get('plan_version')!r} is not the launch input's "
                   f"{launch['plan_version']!r}")
    if manifest["approved_source_commit"] != launch["approved_source_commit"]:
        out.append(f"approved_source_commit: the launch input says {launch['approved_source_commit']}, the manifest "
                   f"authorises {manifest['approved_source_commit']}")
    roots = (facts["source_repo"], os.path.realpath(launch["worktree"]))
    for path_field, hash_field in MANIFEST_BOUND_FILES:
        real = os.path.realpath(launch[path_field])
        listed = [relative for relative in (os.path.relpath(real, root) for root in roots if _is_beneath(real, root))
                  if relative in components]
        if not listed:
            out.append(f"{path_field}: {launch[path_field]} is not a component of the manifest (it must be a listed "
                       f"path of the reviewed source or of the worktree)")
        elif components[listed[0]] != launch[hash_field]:
            out.append(f"{path_field}: {hash_field} {launch[hash_field]} is not the reviewed "
                       f"{components[listed[0]]} of manifest component {listed[0]}")
    return out


def _flag_names(elements) -> list:
    """launch-line elements for a message: a flag keeps its name, never its value"""
    return [element.split("=", 1)[0] + "=…" if element.startswith("--") and "=" in element else element
            for element in elements]


def portable_argv(argv, worktree):
    """a launch line without what legitimately differs between worktrees: the --mcp-config path (its content is
    bound by hash) and the worktree prefix of any path under the worktree"""
    out = []
    for index, element in enumerate(argv):
        if index and argv[index - 1] == "--mcp-config":
            out.append("<MCP_CONFIG>")
        elif isinstance(worktree, str) and worktree and (element == worktree or element.startswith(worktree + "/")):
            out.append("<WORKTREE>" + element[len(worktree):])
        else:
            out.append(element)
    return out


def qualification_findings(launch, manifest, ky_run, facts, context) -> list:
    """plan §7 KV-06: only a recorded PASS receipt that binds exactly this launch configuration, earned in the
    context the job runs in, qualifies it"""
    path = os.path.join(ky_run, "QUALIFICATIONS", f"{launch['role']}-{launch['model']}.json")
    facts["qualification_path"] = path
    if not os.path.isfile(path):
        return [f"qualification: no receipt at {path}; role {launch['role']} with model {launch['model']} is not a "
                f"qualified launch configuration"]
    try:
        receipt, facts["qualification_sha256"] = read_json_and_sha(path)
    except ValueError as bad:
        return [f"qualification: {bad}"]
    if type(receipt) is not dict or receipt.get("schema") != QUALIFICATION_SCHEMA:
        return [f"qualification: {path} is not a {QUALIFICATION_SCHEMA} receipt"]
    out = []
    if receipt.get("context") != context:
        earned = receipt["context"] if isinstance(receipt.get("context"), str) else _show(receipt.get("context"))
        out.append(f"qualification context mismatch: receipt {earned}, launch {context}")
    if receipt.get("result") != "PASS":
        out.append(f"qualification: result is {_show(receipt.get('result'))}; only \"PASS\" qualifies a "
                   f"launch (FAIL, unknown and missing refuse)")
    for key in ("role", "model"):
        if receipt.get(key) != launch[key]:
            out.append(f"qualification: the receipt's {key} {_show(receipt.get(key))} is not the launch "
                       f"input's {launch[key]!r}")
    if manifest is not None:
        recorded = [entry for entry in manifest.get("qualifications") or [] if type(entry) is dict
                    and isinstance(entry.get("path"), str) and os.path.realpath(entry["path"]) == os.path.realpath(path)]
        if not recorded:
            out.append("qualification: the receipt is not recorded in the manifest")
        elif recorded[0].get("sha256") != facts["qualification_sha256"] or recorded[0].get("result") != "PASS":
            out.append("qualification: the receipt is not the one the manifest records as PASS (its bytes or its "
                       "result changed after the manifest was built)")
    binds = receipt.get("binds")
    if type(binds) is not dict:
        return out + ["qualification: the receipt carries no binds"]

    expected = {"claude_bin": launch["claude_bin"], "claude_bin_sha256": facts.get("claude_bin_sha256"),
                "model": launch["model"], "effort": launch["effort"], "permission_mode": launch["permission_mode"],
                "max_turns": launch["max_turns"], "mcp_config_sha256": launch["mcp_config_sha256"],
                "env_names": sorted(launch["env"])}
    for name, want in expected.items():
        if name not in binds:
            out.append(f"qualification: binds.{name} is missing")
        elif want is None:
            out.append(f"qualification: binds.{name} cannot be compared (the launch's value was not observed)")
        elif type(binds[name]) is not type(want) or not kyschema.json_equal(binds[name], want):
            out.append(f"qualification: binds.{name} {_show(binds[name])} does not bind this launch "
                       f"({_show(want)})")
    observed = parse_version(facts.get("claude_version") or "")
    bound = parse_version(binds["claude_version"]) if isinstance(binds.get("claude_version"), str) else None
    if "claude_version" not in binds:
        out.append("qualification: binds.claude_version is missing")
    elif observed is None or bound is None or observed != bound:
        out.append(f"qualification: binds.claude_version {_show(binds['claude_version'])} does not bind this "
                   f"launch ({facts.get('claude_version')!r})")
    argv = binds.get("argv")
    if "argv" not in binds:
        out.append("qualification: binds.argv is missing")
    elif type(argv) is not list or not all(isinstance(element, str) for element in argv):
        out.append("qualification: binds.argv is not a list of strings")
    else:
        mine = portable_argv(build_launch(launch)["argv"], launch["worktree"])
        theirs = portable_argv(argv, binds.get("worktree"))
        if mine != theirs:
            where = next((i for i, pair in enumerate(zip(mine, theirs)) if pair[0] != pair[1]),
                         min(len(mine), len(theirs)))
            out.append(f"qualification: binds.argv is not this launch's line (same flags, same order): they differ at "
                       f"element {where}: qualified {_show(_flag_names(theirs[where:where + 1]))}, this launch "
                       f"{_show(_flag_names(mine[where:where + 1]))}")
    return out


def check(launch_path, environ, manifest_path=None, context=None) -> Checked:
    """every precondition of a bootstrap launch; findings are complete (never only the first) once the shape holds.
    `context` is the context the job will run in when that is not this process's own (submit passes "launchd")."""
    facts: dict = {}
    ky_run = environ.get("KY_RUN") or DEFAULT_KY_RUN
    facts["ky_run"] = ky_run
    if not os.path.isabs(ky_run) or os.path.normpath(ky_run) != ky_run:
        return Checked(None, [f"KY_RUN: {ky_run!r} is not a normalised absolute path"], facts)
    manifest_path = os.path.abspath(manifest_path) if manifest_path else os.path.join(ky_run, "VERSIONS.bootstrap.json")
    manifest, components, gate = manifest_gate(manifest_path, ky_run, environ, facts)

    try:
        launch = kyschema.load_json(launch_path)
    except ValueError as bad:
        return Checked(None, gate + [f"launch input: {bad}"], facts)
    findings = list(_placeholders(launch))
    try:
        findings += [f"schema: {_value_free(error)}"
                     for error in kyschema.validate(load_schema(LAUNCH_SCHEMA), launch)]
    except (ValueError, kyschema.SchemaError) as refused:
        return Checked(launch, gate + [f"schema {LAUNCH_SCHEMA} is refused: {refused}"], facts)
    if findings:
        return Checked(launch, gate + findings, facts)  # the rules below read fields the shape must guarantee
    detected, injected = detect_context(environ, launch["job_id"])
    facts["launch_context"] = context or detected
    facts["launch_context_parent_pid_injected"] = injected and context is None

    unsafe_paths = set()
    for field in PATH_FIELDS:
        value = launch[field]
        if not os.path.isabs(value):
            findings.append(f"{field}: not an absolute path: {value!r}")
            unsafe_paths.add(field)
        elif os.path.normpath(value) != value:
            findings.append(f"{field}: path is not normalised (no '..', '.', doubled or trailing slash): {value!r}")
            unsafe_paths.add(field)
    findings += env_findings(launch, ky_run)
    findings += flag_findings(launch["extra_lean_flags"])

    expected_effort = "xhigh" if launch["kind"] == "PLAN" else "high"
    if launch["effort"] != expected_effort:
        findings.append(f"effort: kind {launch['kind']} requires effort {expected_effort}, found {launch['effort']}")
    cap = TURN_CAPS[launch["kind"]]
    if launch["max_turns"] > cap:
        findings.append(f"max_turns: {launch['max_turns']} exceeds the cap {cap} for kind {launch['kind']}")

    deadline = parse_utc(launch["deadline"])
    if deadline is None:
        findings.append(f"deadline: not a UTC ISO-8601 timestamp (…Z or …+00:00): {launch['deadline']!r}")
    elif deadline <= time.time():
        findings.append(f"deadline: {launch['deadline']} is not in the future")
    facts["deadline_epoch"] = deadline

    if unsafe_paths:
        return Checked(launch, gate + findings, facts)  # never probe the filesystem through a relative path
    findings += _location_findings(launch, environ, ky_run, facts)
    findings += _git_findings(launch, environ, facts)
    env_is_clean = not any(line.startswith("env") for line in findings)
    findings += _claude_findings(launch, facts) if env_is_clean else \
        ["claude_bin: --version was not run because the job environment is refused"]
    findings += _file_findings(launch)
    if manifest is not None:
        findings += binding_findings(launch, manifest, components, facts)
    if env_is_clean:
        findings += qualification_findings(launch, manifest, ky_run, facts, facts["launch_context"])
    else:
        findings.append("qualification: not compared because the job environment is refused")
    return Checked(launch, gate + findings, facts)


# --------------------------------------------------------------------------------------------------------------
# argv
# --------------------------------------------------------------------------------------------------------------
def build_launch(launch) -> dict:
    """the plan §7 launch line for a checked launch input; a pure function of the launch input"""
    argv = [launch["claude_bin"], "-p", "--setting-sources", "project",
            "--permission-mode", launch["permission_mode"], "--model", launch["model"],
            "--effort", launch["effort"], "--max-turns", str(launch["max_turns"]),
            *launch["extra_lean_flags"],
            "--strict-mcp-config", "--mcp-config", launch["mcp_config"]]
    if launch["disallowed_tools"]:
        argv += ["--disallowedTools", *launch["disallowed_tools"]]
    argv += ["--output-format", "stream-json", "--verbose", "--add-dir", launch["env"]["KY_ROOT"]]
    return {"cwd": launch["worktree"], "env": clean_env(launch), "argv": argv}


# --------------------------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------------------------
def write_state(path, state, exclusive=False):
    """atomic: a complete temporary file, then rename; `exclusive` creates the file only if it does not exist"""
    temporary = f"{path}.tmp.{os.getpid()}"
    data = (json.dumps(state, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if exclusive:
        try:
            os.link(temporary, path)               # fails if `path` exists; the content is already complete
        finally:
            os.unlink(temporary)
    else:
        os.replace(temporary, path)


def _events(path, limit=None):
    """the JSON objects of a stream-json file, in order; anything that is not a JSON object line is skipped"""
    try:
        with open(path, "rb") as handle:
            data = handle.read() if limit is None else handle.read(limit)
    except OSError:
        return
    for raw in data.split(b"\n"):                   # a line cut by `limit` is not a JSON object: it is skipped
        try:
            event = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(event, dict):
            yield event


def first_session_id(path, limit=None):
    """the session_id of the first stream event that carries one; None when none does (never invented)"""
    for event in _events(path, limit):
        if isinstance(event.get("session_id"), str) and event["session_id"]:
            return event["session_id"]
    return None


def final_result_event(path):
    """subtype / is_error / num_turns / usage of the last `type: "result"` event, or None when there is none"""
    last = None
    for event in _events(path):
        if event.get("type") == "result":
            last = event
    if last is None:
        return None
    return {key: last.get(key) for key in ("subtype", "is_error", "num_turns", "usage")}


def job_result(launch):
    """(valid, errors): (None, []) when <job_scratch>/result.json is absent"""
    path = os.path.join(launch["job_scratch"], "result.json")
    if not os.path.lexists(path):
        return None, []
    try:
        result = kyschema.load_json(path)
        errors = kyschema.validate(load_schema("job_result"), result)
    except (ValueError, kyschema.SchemaError) as bad:
        return False, [str(bad)][:10]
    if not errors:
        for field in ("job_id", "item"):
            if result[field] != launch[field]:
                errors.append(f"$.{field}: {result[field]!r} is not this job's {field} {launch[field]!r}")
    return not errors, errors[:10]


def group_state(pgid: int) -> str:
    """'live' (a member can be signalled) · 'unreaped' (members exist but none can be signalled: on macOS, exited
    members their parent has not collected yet — or a member of another user) · 'gone' (no such group)"""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return "gone"
    except PermissionError:
        return "unreaped"
    return "live"


def _signal_group(pgid: int, signum) -> None:
    try:
        os.killpg(pgid, signum)
    except (ProcessLookupError, PermissionError):
        pass


def end_group(proc, pgid: int, grace: float) -> str:
    """SIGTERM the group, wait up to `grace`, then SIGKILL; 'term' when the group ended without SIGKILL"""
    def gone():
        return proc.poll() is not None and group_state(pgid) == "gone"

    _signal_group(pgid, signal.SIGTERM)
    limit = time.monotonic() + grace
    while time.monotonic() < limit:
        if gone():
            return "term"
        time.sleep(POLL_SECONDS)
    if gone():
        return "term"
    _signal_group(pgid, signal.SIGKILL)
    limit = time.monotonic() + KILL_CONFIRM_SECONDS
    while time.monotonic() < limit and not gone():
        time.sleep(POLL_SECONDS)
    return "kill"


def ps_identity(pid: int):
    """(stat, lstart) as `LC_ALL=C ps -o stat=,lstart= -p <pid>` prints them · "gone" when ps reports no such
    process · None when ps could not be asked or its answer cannot be read (unknown is never 'gone')"""
    try:
        done = subprocess.run(["ps", "-o", "stat=,lstart=", "-p", str(int(pid))], capture_output=True, text=True,
                              env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}, timeout=15, stdin=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if done.returncode == 1 and not done.stdout.strip() and not done.stderr.strip():
        return "gone"
    parts = done.stdout.strip().split(None, 1)
    if done.returncode != 0 or len(parts) < 2:
        return None
    return parts[0], " ".join(parts[1].split())


def process_start(pid: int):
    """the start identity of a process (the lstart text), or None when ps does not report it"""
    identity = ps_identity(pid)
    return identity[1] if isinstance(identity, tuple) else None


def process_matches(pid, start):
    """True: alive with this start identity · False: positively gone (no such process, an uncollected exit, or
    another process under a reused id) · None: it cannot be told. The rule of kyloop.py `process_matches`, with
    one difference: a malformed record or an unanswerable ps is None here, never False. Never steal on None."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None
    identity = ps_identity(pid)
    if identity is None:
        return None
    if identity == "gone" or identity[0].startswith("Z"):
        return False
    if not isinstance(start, str) or not start.strip():
        return None
    recorded = " ".join(start.split())
    if recorded == identity[1]:
        return True
    try:
        return time.strptime(recorded, LSTART_FMT) == time.strptime(identity[1], LSTART_FMT)
    except ValueError:
        return None


# --------------------------------------------------------------------------------------------------------------
# the item lock (plan §14 B-0c "its own proven instance lock") and the action record (plan §4a.1)
# --------------------------------------------------------------------------------------------------------------
def item_lock_path(ky_run, item) -> str:
    return os.path.join(ky_run, "locks", f"kyboot.{item}")


def read_lock_owner(lock, wait=0.0):
    """owner.json of a lock directory as a dict, or None when it is missing (after `wait`) or not readable"""
    limit = time.monotonic() + wait
    while True:
        try:
            owner = kyschema.load_json(os.path.join(lock, "owner.json"))
            return owner if type(owner) is dict else None
        except ValueError:
            if os.path.lexists(os.path.join(lock, "owner.json")) or time.monotonic() >= limit:
                return None
        time.sleep(POLL_SECONDS)


def acquire_item_lock(ky_run, item, run_id):
    """(lock directory, None, taken-over owner or None) · (None, reason, None). One live supervisor per item:
    an existing lock is taken over only when its recorded owner — and the job that owner recorded — are
    positively gone; an unknown identity is never taken over."""
    lock = item_lock_path(ky_run, item)
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    taken_over = None
    for _ in range(2):
        try:
            os.mkdir(lock)
        except FileExistsError:
            owner = read_lock_owner(lock, LOCK_OWNER_WAIT_SECONDS)
            if owner is None:
                return None, (f"item lock: {lock} exists and its owner is not recorded or not readable; an unknown "
                              f"owner is never taken over"), None
            alive = process_matches(owner.get("pid"), owner.get("process_start"))
            if alive is True:
                return None, (f"item lock: item {item} is held by a live supervisor "
                              f"({owner.get('session_or_run_id')}, pid {owner.get('pid')})"), None
            if alive is None:
                return None, (f"item lock: the owner of {lock} (pid {owner.get('pid')}) cannot be confirmed gone; an "
                              f"unknown owner is never taken over"), None
            child = owner.get("child")
            if child is not None:
                gone = process_matches(child.get("pid"), child.get("process_start")) if type(child) is dict else None
                if gone is not False:
                    return None, (f"item lock: the previous supervisor of item {item} is gone but the job it "
                                  f"recorded is alive or cannot be confirmed gone; reconcile that job before any "
                                  f"new launch"), None
            grave = f"{lock}.stale.{os.getpid()}"
            try:
                os.rename(lock, grave)                 # atomic: exactly one contender wins the takeover
            except OSError:
                continue
            for name in os.listdir(grave):
                os.unlink(os.path.join(grave, name))
            os.rmdir(grave)
            taken_over = owner
            continue
        write_lock_owner(lock, run_id, None)
        return lock, None, taken_over
    return None, f"item lock: lost the takeover race for {lock}", None


def write_lock_owner(lock, run_id, child, acquired_at=None):
    previous = read_lock_owner(lock) or {}
    write_state(os.path.join(lock, "owner.json"), {
        "session_or_run_id": run_id, "pid": os.getpid(), "pgid": os.getpgrp(),
        "process_start": process_start(os.getpid()),
        "acquired_at": acquired_at or previous.get("acquired_at") or utc_now_text(), "child": child})


def release_item_lock(lock, run_id) -> bool:
    """remove the lock if, and only if, this run still owns it"""
    owner = read_lock_owner(lock)
    if owner is None or owner.get("session_or_run_id") != run_id:
        return False
    try:
        os.unlink(os.path.join(lock, "owner.json"))
        os.rmdir(lock)
    except OSError:
        return False
    return True


def action_path(ky_run, job_id, verb="launch") -> str:
    return os.path.join(ky_run, "actions", f"ACT-{verb}-{job_id}.json")


def begin_action(path, launch, run_id, inputs, kind="launch", more_target=None, transition=None):
    """persist the intent before the side effect (plan §4a.1); FileExistsError when the action already exists"""
    record = {"schema": ACTION_SCHEMA, "action_id": os.path.basename(path)[:-len(".json")], "kind": kind,
              "actor": {"role": "planner", "holder_kind": "supervisor", "controller_id": run_id},
              "inputs": inputs,
              "target": dict({"job_id": launch["job_id"], "item": launch["item"], "kind": launch["kind"],
                              "role": launch["role"], "worktree": launch["worktree"], "branch": launch["branch"],
                              "state_path": launch["state_path"]}, **(more_target or {})),
              "intended_transition": transition or (f"launch job {launch['job_id']} for item {launch['item']} and "
                                                    f"supervise it to its termination"),
              "created_at": utc_now_text(), "state": "INTENDED", "result": None, "completed_at": None}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_state(path, record, exclusive=True)
    return record


def complete_action(path, record, done: bool, result):
    """the observed result, atomically: DONE when the side effect happened as intended, FAILED otherwise"""
    record.update(state="DONE" if done else "FAILED", result=result, completed_at=utc_now_text())
    write_state(path, record)


def supervise(proc, pgid, deadline_epoch, grace, stdout_path, on_session, stop):
    """wait for exit, the deadline or a signal to the supervisor; always leaves the process group ended"""
    session = None
    next_scan = 0.0
    reason = None
    while proc.poll() is None:
        if stop["signal"] is not None:
            reason = "interrupted"
            break
        if time.time() >= deadline_epoch:
            reason = "timed_out"
            break
        if session is None and time.monotonic() >= next_scan:
            next_scan = time.monotonic() + 1.0
            session = first_session_id(stdout_path, SESSION_SCAN_BYTES)
            if session is not None:
                on_session(session)
        time.sleep(POLL_SECONDS)
    outcome = {"termination": "exited", "leftover_group": "none"}
    if reason is not None:
        outcome["termination"] = f"{reason}_{end_group(proc, pgid, grace)}"
    else:                                            # the leader exited by itself: did it leave members behind?
        limit = time.monotonic() + KILL_CONFIRM_SECONDS
        while group_state(pgid) == "unreaped" and time.monotonic() < limit:
            time.sleep(POLL_SECONDS)
        if group_state(pgid) == "live":
            outcome["leftover_group"] = "terminated" if end_group(proc, pgid, grace) == "term" else "killed"
    outcome.update(_exit_facts(proc, pgid))
    return outcome


def _exit_facts(proc, pgid) -> dict:
    code = proc.poll()
    return {"exit_code": code if code is not None and code >= 0 else None,
            "exit_signal": -code if code is not None and code < 0 else None,
            "group_gone": code is not None and group_state(pgid) == "gone"}


def run(launch_path, environ, grace=DEFAULT_GRACE_SECONDS, report=print, manifest_path=None) -> int:
    checked = check(launch_path, environ, manifest_path)
    if not checked.ok:
        _refuse(launch_path, checked.findings)
        return EXIT_REFUSED
    launch, facts = checked.launch, checked.facts
    ky_run = facts["ky_run"]
    plan = build_launch(launch)
    state_path, scratch = launch["state_path"], launch["job_scratch"]
    result_path = os.path.join(scratch, "result.json")
    act_path = action_path(ky_run, launch["job_id"])
    occupied = []
    if os.path.lexists(state_path):
        occupied.append(f"state_path: {state_path} already exists for job {launch['job_id']} (no silent re-run)")
    if os.path.lexists(act_path):
        occupied.append(f"action: {act_path} already exists; a launch of job {launch['job_id']} was already intended "
                        f"(reconcile it, never repeat it)")
    for label, path in (("stdout_path", launch["stdout_path"]), ("stderr_path", launch["stderr_path"]),
                        ("result.json", result_path)):
        if os.path.lexists(path):
            occupied.append(f"{label}: {path} already exists (a job never overwrites an earlier run's output)")
    if occupied:
        _refuse(launch_path, occupied)
        return EXIT_REFUSED

    run_id = f"kyboot-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    lock, held, taken_over = acquire_item_lock(ky_run, launch["item"], run_id)
    if lock is None:
        _refuse(launch_path, [held])
        return EXIT_REFUSED
    keep_lock = False
    try:
        launch_sha = sha256_file(launch_path)
        try:
            action = begin_action(act_path, launch, run_id, {
                "launch_input_path": os.path.abspath(launch_path), "launch_input_sha256": launch_sha,
                "manifest_sha256": facts.get("manifest_sha256"), "supervisor_sha256": facts.get("supervisor_sha256"),
                "qualification_sha256": facts.get("qualification_sha256"), "prompt_sha256": launch["prompt_sha256"],
                "packet_sha256": launch["packet_sha256"], "argv": plan["argv"]})
        except FileExistsError:
            _refuse(launch_path, [f"action: {act_path} already exists; a launch of job {launch['job_id']} was "
                                  f"already intended (reconcile it, never repeat it)"])
            return EXIT_REFUSED
        state = {
            "schema": STATE_SCHEMA, "phase": "prepared",
            "job_id": launch["job_id"], "item": launch["item"], "kind": launch["kind"], "role": launch["role"],
            "worktree": launch["worktree"], "branch": launch["branch"], "base_sha": launch["base_sha"],
            "worktree_head": facts.get("worktree_head"),
            "job_scratch": scratch, "prompt_path": launch["prompt_path"], "stdout_path": launch["stdout_path"],
            "stderr_path": launch["stderr_path"], "tmp_path": launch["tmp_path"], "state_path": state_path,
            "model": launch["model"], "effort": launch["effort"], "permission_mode": launch["permission_mode"],
            "max_turns": launch["max_turns"], "deadline": launch["deadline"], "grace_seconds": grace,
            "claude_bin": launch["claude_bin"], "claude_bin_realpath": facts.get("claude_bin_realpath"),
            "claude_bin_sha256": facts.get("claude_bin_sha256"), "claude_version": facts.get("claude_version"),
            "launch_input_path": os.path.abspath(launch_path), "launch_input_sha256": launch_sha,
            "argv": plan["argv"], "plan_version": launch["plan_version"],
            "approved_source_commit": launch["approved_source_commit"],
            "supervisor_path": facts.get("supervisor_path"), "supervisor_sha256": facts.get("supervisor_sha256"),
            "source_repo": facts.get("source_repo"), "manifest_path": facts.get("manifest_path"),
            "manifest_sha256": facts.get("manifest_sha256"),
            "manifest_file_sha256": facts.get("manifest_file_sha256"),
            "qualification_path": facts.get("qualification_path"),
            "qualification_sha256": facts.get("qualification_sha256"),
            "scratch_root": facts.get("scratch_root"), "scratch_root_override": facts.get("scratch_root_override"),
            "supervisor_pid": os.getpid(), "supervisor_process_start": process_start(os.getpid()),
            "supervisor_run_id": run_id, "lock_path": lock,
            "launch_context": facts.get("launch_context"),
            "launch_context_parent_pid_injected": facts.get("launch_context_parent_pid_injected"),
            "label": job_label(launch["job_id"]) if facts.get("launch_context") == "launchd" else None,
            "lock_taken_over_from": taken_over, "action_path": act_path,
            "started_at": None, "pid": None, "pgid": None, "process_start": None, "provider_session_id": None,
            "ended_at": None, "exit_code": None, "exit_signal": None, "termination": None, "leftover_group": None,
            "group_gone": None, "result_event": None, "job_result_valid": None, "job_result_errors": [],
        }
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        try:
            write_state(state_path, state, exclusive=True)
        except FileExistsError:
            complete_action(act_path, action, False, {"phase": "refused", "reason": "state.json already exists"})
            _refuse(launch_path, [f"state_path: {state_path} already exists for job {launch['job_id']} "
                                  f"(no silent re-run)"])
            return EXIT_REFUSED
        keep_lock = True                               # until the outcome says the job cannot be alive
        code = _launch_and_supervise(launch, plan, facts, state, grace, lock, run_id)
        launched = state["phase"] == "ended"
        keep_lock = state["phase"] == "running" or (launched and state["group_gone"] is not True)
        complete_action(act_path, action, launched and state["group_gone"] is True, {
            "phase": state["phase"], "termination": state["termination"], "exit_code": state["exit_code"],
            "exit_signal": state["exit_signal"], "group_gone": state["group_gone"], "pid": state["pid"],
            "pgid": state["pgid"], "process_start": state["process_start"],
            "launch_error": state.get("launch_error"), "state_path": state_path, "supervisor_exit": code})
        report(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=1))
        return code
    finally:
        if not keep_lock:                              # a job that may still be alive keeps its item locked
            release_item_lock(lock, run_id)


def _launch_and_supervise(launch, plan, facts, state, grace, lock, run_id) -> int:
    """start the job in a session of its own, supervise it, and leave the final record in `state` and on disk"""
    state_path, scratch = launch["state_path"], launch["job_scratch"]
    stop = {"signal": None}
    previous = {}
    proc = None
    try:
        os.makedirs(scratch, exist_ok=True)
        os.makedirs(launch["tmp_path"], exist_ok=True)
        with open(launch["prompt_path"], "rb") as stdin, open(launch["stdout_path"], "xb") as stdout, \
                open(launch["stderr_path"], "xb") as stderr:
            digest = hashlib.sha256(stdin.read()).hexdigest()   # the bytes the job will read, re-hashed on
            if digest != launch["prompt_sha256"]:               # the very descriptor it inherits
                raise OSError(f"prompt_path changed after check: sha256 is now {digest}")
            stdin.seek(0)
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                previous[signum] = signal.signal(signum, lambda number, _frame: stop.update(signal=number))
            proc = subprocess.Popen(plan["argv"], cwd=plan["cwd"], env=plan["env"], stdin=stdin, stdout=stdout,
                                    stderr=stderr, start_new_session=True, close_fds=True)
    except OSError as failed:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        state.update(phase="launch_failed", ended_at=utc_now_text(), launch_error=str(failed))
        write_state(state_path, state)
        print(f"NOT LAUNCHED {launch['job_id']}: {failed}", file=sys.stderr)
        return EXIT_JOB_FAILED

    try:
        try:
            pgid = os.getpgid(proc.pid)
        except OSError:
            pgid = proc.pid                         # start_new_session: the child leads its own group
        if pgid != proc.pid or pgid == os.getpgrp():
            # the job must lead a group of its own: signalling any other group would reach the supervisor,
            # its parents or strangers. End the one process we started, by pid, and record why.
            proc.kill()
            proc.wait()
            state.update(phase="launch_failed", started_at=utc_now_text(), ended_at=utc_now_text(), pid=proc.pid,
                         pgid=pgid,
                         launch_error=f"the job is not the leader of its own process group "
                                      f"(pid {proc.pid}, pgid {pgid}); it was killed by pid")
            write_state(state_path, state)
            print(f"NOT LAUNCHED {launch['job_id']}: {state['launch_error']}", file=sys.stderr)
            return EXIT_JOB_FAILED
        state.update(phase="running", started_at=utc_now_text(), pid=proc.pid, pgid=pgid)
        write_state(state_path, state)              # the identity first; the start time needs another process
        state["process_start"] = process_start(proc.pid)
        write_state(state_path, state)
        write_lock_owner(lock, run_id, {"job_id": launch["job_id"], "pid": proc.pid, "pgid": pgid,
                                        "process_start": state["process_start"]})

        def on_session(session_id):
            state["provider_session_id"] = session_id
            write_state(state_path, state)

        try:
            outcome = supervise(proc, pgid, facts["deadline_epoch"], grace, launch["stdout_path"], on_session, stop)
        except BaseException as crashed:            # never leave an unsupervised job behind
            outcome = {"termination": f"interrupted_{end_group(proc, pgid, grace)}", "leftover_group": "none"}
            outcome.update(_exit_facts(proc, pgid))
            state["supervisor_error"] = f"{type(crashed).__name__}: {crashed}"
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)

    state.update(outcome)
    if stop["signal"] is not None:
        state["supervisor_signal"] = int(stop["signal"])
    valid, errors = job_result(launch)
    state.update(phase="ended", ended_at=utc_now_text(),
                 provider_session_id=state["provider_session_id"] or first_session_id(launch["stdout_path"]),
                 result_event=final_result_event(launch["stdout_path"]),
                 job_result_valid=valid, job_result_errors=errors)
    write_state(state_path, state)
    if not state["group_gone"]:
        print(f"PROCESS GROUP {state['pgid']} NOT CONFIRMED GONE", file=sys.stderr)
        return EXIT_GROUP_SURVIVED
    if state["termination"].startswith("timed_out"):
        return EXIT_TIMED_OUT
    if state["termination"].startswith("interrupted"):
        return EXIT_INTERRUPTED
    if state["exit_code"] != 0 or valid is False:
        return EXIT_JOB_FAILED
    return EXIT_OK


# --------------------------------------------------------------------------------------------------------------
# submit / status / reap: the job as a one-shot launchd user agent, so that it outlives the session that sent it
# --------------------------------------------------------------------------------------------------------------
def launchctl_program(environ) -> str:
    return environ.get("KY_LAUNCHCTL") or DEFAULT_LAUNCHCTL


def launchctl(environ, *args):
    """(exit status, stdout, stderr) of ${KY_LAUNCHCTL:-/bin/launchctl} <args>; 127 when it could not be run.
    The program is never looked up on PATH: a name that is not an absolute path is not run at all."""
    program = launchctl_program(environ)
    if not os.path.isabs(program):
        return 127, "", f"KY_LAUNCHCTL {program!r} is not an absolute path; it was not run"
    try:
        done = subprocess.run([program, *args], capture_output=True, text=True, env=dict(environ), timeout=120,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as failed:
        return 127, "", f"{program} could not be run: {failed}"
    return done.returncode, done.stdout, done.stderr


def agent_target(job_id: str) -> str:
    return f"gui/{os.getuid()}/{job_label(job_id)}"


def agent_environment(launch, facts, environ) -> dict:
    """the agent's whole environment: PATH, HOME, USER, LANG and the three KY_ values this supervisor resolved.
    Never a credential, never the caller's environment."""
    me = pwd.getpwuid(os.getuid())
    home = environ.get("HOME") or ""
    return {"PATH": AGENT_PATH, "HOME": home if os.path.isabs(home) else me.pw_dir,
            "USER": environ.get("USER") or me.pw_name, "LANG": "en_US.UTF-8", "KY_RUN": facts["ky_run"],
            "KY_SCRATCH": facts["ky_scratch"], "KY_ROOT": launch["env"]["KY_ROOT"]}


def agent_plist(launch, facts, environ, launch_path) -> dict:
    """the one-shot agent: RunAtLoad, never KeepAlive, running this very file's `run` on the same launch input"""
    scratch = launch["job_scratch"]
    return {"Label": job_label(launch["job_id"]),
            "ProgramArguments": [sys.executable, "-u", facts["supervisor_path"], "run", os.path.abspath(launch_path),
                                 "--manifest", facts["manifest_path"]],
            "RunAtLoad": True, "ProcessType": "Background",
            "EnvironmentVariables": agent_environment(launch, facts, environ),
            "StandardOutPath": os.path.join(scratch, "supervisor.out"),
            "StandardErrorPath": os.path.join(scratch, "supervisor.err")}


def submit(launch_path, environ, manifest_path=None, report=print) -> int:
    if os.geteuid() == 0:
        _refuse(launch_path, ["submit: refused as root; a user agent belongs to the user's own gui domain"])
        return EXIT_REFUSED
    checked = check(launch_path, environ, manifest_path, context="launchd")
    if not checked.ok:
        _refuse(launch_path, checked.findings)
        return EXIT_REFUSED
    launch, facts = checked.launch, checked.facts
    job_id, scratch, ky_run = launch["job_id"], launch["job_scratch"], facts["ky_run"]
    label, domain = job_label(job_id), f"gui/{os.getuid()}"
    document = agent_plist(launch, facts, environ, launch_path)
    plist = os.path.join(scratch, label + ".plist")
    submit_path = action_path(ky_run, job_id, "submit")
    refusals = []
    if not _LABEL_COMPONENT.match(job_id):
        refusals.append(f"submit: job_id {job_id!r} is not a safe launchd label component (letters, digits, '-' and "
                        f"'_' in parts joined by single dots)")
    if not os.path.isabs(launchctl_program(environ)):
        refusals.append("submit: KY_LAUNCHCTL is not an absolute path")
    if not os.path.isabs(sys.executable or ""):
        refusals.append("submit: this interpreter has no absolute path to give the agent")
    if sorted(document["EnvironmentVariables"]) != sorted(AGENT_ENV_NAMES):
        refusals.append("submit: the agent's environment is not exactly the allowed names")
    for label_of, path in (("state_path", launch["state_path"]), ("action", action_path(ky_run, job_id)),
                           ("action", submit_path), ("stdout_path", launch["stdout_path"]),
                           ("stderr_path", launch["stderr_path"]), ("result.json", os.path.join(scratch, "result.json")),
                           ("plist", plist), ("supervisor.out", document["StandardOutPath"]),
                           ("supervisor.err", document["StandardErrorPath"])):
        if os.path.lexists(path):
            refusals.append(f"submit: {label_of} {path} already exists; job {job_id} was already submitted or run "
                            f"(never repeat it)")
    if refusals:
        _refuse(launch_path, refusals)
        return EXIT_REFUSED

    with open(plist, "xb") as handle:
        plistlib.dump(document, handle)
    try:
        lint = subprocess.run([PLUTIL, "-lint", plist], capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL).returncode
    except (OSError, subprocess.SubprocessError):
        lint = 127
    if lint != 0:
        os.unlink(plist)
        _refuse(launch_path, [f"submit: the rendered plist fails plutil -lint (exit {lint}); it was removed"])
        return EXIT_REFUSED
    run_id = f"kyboot-submit-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    try:
        action = begin_action(submit_path, launch, run_id, {
            "launch_input_path": os.path.abspath(launch_path), "launch_input_sha256": sha256_file(launch_path),
            "manifest_path": facts["manifest_path"], "manifest_sha256": facts.get("manifest_sha256"),
            "supervisor_sha256": facts.get("supervisor_sha256"), "plist_sha256": sha256_file(plist),
            "program_arguments": document["ProgramArguments"],
            "environment_names": sorted(document["EnvironmentVariables"])},
            kind="submit", more_target={"label": label, "domain": domain, "plist": plist},
            transition=f"bootstrap the one-shot launchd agent {label} that runs job {job_id}")
    except FileExistsError:
        os.unlink(plist)
        _refuse(launch_path, [f"submit: action {submit_path} already exists; job {job_id} was already submitted "
                              f"(never repeat it)"])
        return EXIT_REFUSED
    code, _, error = launchctl(environ, "bootstrap", domain, plist)
    complete_action(submit_path, action, code == 0, {
        "launchctl": "bootstrap", "exit": code, "stderr": (error.strip().splitlines() or [""])[0][:300],
        "label": label, "domain": domain, "plist": plist})
    report(json.dumps({"job_id": job_id, "label": label, "plist": plist, "state_path": launch["state_path"]},
                      ensure_ascii=False, sort_keys=True, indent=1))
    if code != 0:
        print(f"NOT SUBMITTED {job_id}: launchctl bootstrap exited {code}", file=sys.stderr)
        return EXIT_JOB_FAILED
    return EXIT_OK


def known_jobs(ky_run) -> list:
    """job ids with a state folder or a submission record"""
    found = set()
    try:
        found.update(name for name in os.listdir(os.path.join(ky_run, "jobs")) if _JOB_ID.match(name))
    except OSError:
        pass
    try:
        for name in os.listdir(os.path.join(ky_run, "actions")):
            if name.startswith("ACT-submit-") and name.endswith(".json") and _JOB_ID.match(name[11:-5]):
                found.add(name[11:-5])
    except OSError:
        pass
    return sorted(found)


def read_record(path):
    """(document, None) · (None, "missing") · (None, "unreadable")"""
    if not os.path.lexists(path):
        return None, "missing"
    try:
        document = kyschema.load_json(path)
    except ValueError:
        return None, "unreadable"
    return (document, None) if type(document) is dict else (None, "unreadable")


def alive(pid, start):
    """true | false | "unknown" — and None when no process was recorded at all"""
    if pid is None:
        return None
    verdict = process_matches(pid, start)
    return "unknown" if verdict is None else verdict


def label_loaded(environ, job_id):
    """true | false from `launchctl print`'s exit status; "unknown" when launchctl could not be run"""
    code, _, _ = launchctl(environ, "print", agent_target(job_id))
    return "unknown" if code == 127 else code == 0


STATUS_FIELDS = ("item", "kind", "role", "phase", "termination", "exit_code", "exit_signal", "group_gone", "pid", "pgid",
                 "process_start", "supervisor_pid", "supervisor_process_start", "started_at", "ended_at", "deadline",
                 "launch_context", "provider_session_id", "job_result_valid", "launch_error")


def status_of(ky_run, environ, job_id) -> dict:
    """read-only: what is recorded and what can be observed now; nothing is changed"""
    state, problem = read_record(os.path.join(ky_run, "jobs", job_id, "state.json"))
    submitted, _ = read_record(action_path(ky_run, job_id, "submit"))
    state = state or {}
    return {"job_id": job_id, "label": job_label(job_id), "label_loaded": label_loaded(environ, job_id),
            "state_file": problem or "present",
            "state": {name: state.get(name) for name in STATUS_FIELDS} if state else None,
            "process_alive": alive(state.get("pid"), state.get("process_start")),
            "supervisor_alive": alive(state.get("supervisor_pid"), state.get("supervisor_process_start")),
            "submit": {"state": submitted.get("state"), "result": submitted.get("result")} if submitted else None}


def reap_one(ky_run, environ, job_id) -> dict:
    """boot out the agent of a job that is positively over: its state.json is readable, the process it recorded
    (if any) is positively gone, and so is its supervisor. A live or unidentifiable process leaves the label alone."""
    entry = {"job_id": job_id, "label": job_label(job_id), "action": "left", "why": None}
    state, problem = read_record(os.path.join(ky_run, "jobs", job_id, "state.json"))
    if state is None:
        entry["why"] = f"state.json is {problem}: the job's identity is unknown"
        return entry
    job = alive(state.get("pid"), state.get("process_start"))
    supervisor = alive(state.get("supervisor_pid"), state.get("supervisor_process_start"))
    if job is not None and job is not False:
        entry["why"] = "the job's process is alive" if job is True else "the job's process cannot be identified"
        return entry
    if supervisor is not False:
        entry["why"] = "the supervisor is alive" if supervisor is True else "the supervisor cannot be identified"
        return entry
    loaded = label_loaded(environ, job_id)
    if loaded is not True:
        entry.update(action="not_loaded" if loaded is False else "left",
                     why=None if loaded is False else "launchctl could not be asked")
        return entry
    code, _, _ = launchctl(environ, "bootout", agent_target(job_id))
    limit = time.monotonic() + ABSENT_CONFIRM_SECONDS
    absent = label_loaded(environ, job_id) is False
    while not absent and time.monotonic() < limit:
        time.sleep(POLL_SECONDS)
        absent = label_loaded(environ, job_id) is False
    entry.update(action="booted_out", bootout_exit=code, absent=absent, phase=state.get("phase"),
                 termination=state.get("termination"))
    return entry


# --------------------------------------------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------------------------------------------
USAGE = ("usage: kyboot.py check <launch_input.json> [--manifest M] | argv <launch_input.json> [--manifest M] | "
         "run <launch_input.json> [--manifest M] [--grace SECONDS] | submit <launch_input.json> [--manifest M] | "
         "status [<job_id>] | reap [<job_id>] | validate <schema-name> <file>")


def _refuse(launch_path, findings):
    print(f"REFUSED {launch_path} ({len(findings)} reason(s); nothing was launched)", file=sys.stderr)
    for line in findings:
        print(f"  {line}", file=sys.stderr)


def _validate(name, path) -> int:
    if name not in schema_names():
        print(f"unknown schema {name!r}; known: {', '.join(schema_names())}", file=sys.stderr)
        return EXIT_USAGE
    try:
        schema = load_schema(name)
        findings = kyschema.lint(schema)
    except ValueError as bad:
        findings = [str(bad)]
    if findings:
        print(f"SCHEMA REFUSED {name}\n" + "\n".join(findings), file=sys.stderr)
        return EXIT_USAGE
    try:
        errors = kyschema.validate(schema, kyschema.load_json(path))
    except ValueError as bad:
        errors = [str(bad)]
    if errors:
        print(f"REFUSED {path} against {name}\n" + "\n".join(errors), file=sys.stderr)
        return EXIT_REFUSED
    print(f"SCHEMA-VALID {path} against {name} "
          f"(shape only; cross-field rules named in the schema's descriptions are not checked here)")
    return EXIT_OK


def _options(rest, allowed):
    """{option: value} of `--name value` pairs, or None when the command line is malformed"""
    found = {}
    while rest:
        if len(rest) < 2 or rest[0] not in allowed or rest[0] in found:
            return None
        found[rest[0]] = rest[1]
        rest = rest[2:]
    return found


def _status_or_reap(command, job_id, environ) -> int:
    ky_run = environ.get("KY_RUN") or DEFAULT_KY_RUN
    if not os.path.isabs(ky_run) or (job_id is not None and not _JOB_ID.match(job_id)):
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE
    jobs = known_jobs(ky_run)
    if job_id is not None and job_id not in jobs:
        print(f"no job {job_id} under {ky_run}", file=sys.stderr)
        return EXIT_REFUSED
    chosen = jobs if job_id is None else [job_id]
    if command == "status":
        print(json.dumps({"jobs": [status_of(ky_run, environ, job) for job in chosen]}, ensure_ascii=False,
                         sort_keys=True, indent=1))
        return EXIT_OK
    done = [reap_one(ky_run, environ, job) for job in chosen]
    print(json.dumps({"reaped": done}, ensure_ascii=False, sort_keys=True, indent=1))
    return EXIT_JOB_FAILED if any(entry["action"] == "booted_out" and not entry["absent"] for entry in done) else EXIT_OK


def main(argv=None, environ=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    environ = os.environ if environ is None else environ
    if len(argv) == 3 and argv[0] == "validate":
        return _validate(argv[1], argv[2])
    if argv and argv[0] in ("status", "reap") and len(argv) <= 2:
        return _status_or_reap(argv[0], argv[1] if len(argv) == 2 else None, environ)
    if len(argv) < 2 or argv[0] not in ("check", "argv", "run", "submit"):
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE
    command, launch_path = argv[:2]
    options = _options(argv[2:], ("--manifest", "--grace") if command == "run" else ("--manifest",))
    if options is None:
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE
    grace = DEFAULT_GRACE_SECONDS
    if "--grace" in options:
        try:
            grace = float(options["--grace"])
        except ValueError:
            grace = -1.0
        if not 0 <= grace <= 600:
            print(f"--grace must be a number of seconds between 0 and 600\n{USAGE}", file=sys.stderr)
            return EXIT_USAGE
    names = own_env_credentials(environ)
    if names:
        print("REFUSED: credential variable name(s) set in this process's own environment: "
              f"{', '.join(names)} (values not read; plan §7 → exit 78)", file=sys.stderr)
        return EXIT_CREDENTIAL_ENV
    manifest_path = options.get("--manifest")
    if command == "run":
        return run(launch_path, environ, grace, manifest_path=manifest_path)
    if command == "submit":
        return submit(launch_path, environ, manifest_path)
    checked = check(launch_path, environ, manifest_path)
    if not checked.ok:
        _refuse(launch_path, checked.findings)
        return EXIT_REFUSED
    if command == "argv":
        print(json.dumps(build_launch(checked.launch), ensure_ascii=False, sort_keys=True, indent=1))
    else:
        print(f"CHECK-PASSED {launch_path}: every launch precondition kyboot checks held when checked "
              f"(job {checked.launch['job_id']}, {checked.launch['kind']}, role {checked.launch['role']}, "
              f"context {checked.facts.get('launch_context')}, {checked.facts.get('claude_version')}, "
              f"manifest {checked.facts.get('manifest_sha256')})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
