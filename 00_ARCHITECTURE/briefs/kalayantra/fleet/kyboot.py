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

  python3 -I -B kyboot.py check <launch_input.json> [--manifest M]   every launch precondition; one named reason
                                           per refusal
  … argv  <launch_input.json> [--manifest M]   after check: {"cwd", "env", "argv"} — the §7 launch line
  … run   <launch_input.json> [--manifest M] [--grace SECONDS]
                                           check, take the item lock, record the action, launch in a new
                                           session, supervise to exit or deadline, record state.json
  … submit <launch_input.json> [--manifest M]  check (for the launchd context), render a one-shot launchd user
                                           agent that runs `run`, bootstrap it, return at once
  … status [<job_id>]                      read-only: state.json, whether the agent's label is loaded, whether
                                           the recorded processes are alive (true | false | "unknown")
  … reap   [<job_id>]                      boot out the agents of jobs that are positively over; never one whose
                                           job, job group or supervisor is alive or cannot be identified
  … validate <schema-name> <file>          shape-check a document against fleet/schemas/<schema-name>.json
                                           (no manifest is involved: kyschema.py is loaded by path, unverified —
                                           a convenience, never a gate)

Nothing is imported from this file's own folder. As a program it runs ONLY in an isolated interpreter (-I: no
script folder, no PYTHONPATH, no user site on the import path) and refuses, exit 2, before its first import
otherwise; the launchd agent it renders runs `python -I -B`. The strict JSON reader lives in this file, and
kyschema.py is executed from the very bytes whose sha256 equalled the manifest's, never through the import
system — so a module or a compiled cache planted beside the reviewed code is not loaded. The manifest tool is
started isolated too, and is given no PYTHON* variable to hand on to what it starts.

Context (a job runs where its qualification was earned): the context is "launchd" only when this process's
parent is pid 1 AND XPC_SERVICE_NAME is the job's own label in.marsys.kalayantra.boot.<job_id> — the way
kyqualify.py proves it — and "shell" otherwise; the receipt's `context` must equal it. `submit` checks against
"launchd" (where the job will run); the `run` it starts checks again from inside the agent. The manifest tool
accepts only receipts earned under launchd, so a real job is started by `submit`; `run` from a shell then
refuses with a context mismatch. The agent's environment is PATH, HOME, USER, LANG, KY_RUN, KY_SCRATCH, KY_ROOT
and nothing else.

Before EVERY launch (check, argv, run and submit alike), in this order — and a refusal at 1 or 2 stops there:
the launch input is then not examined and nothing it names is executed:
  1. the supervisor itself: it does not run from the installed fleet (/Users/Dev/kalayantra/fleet_live or
     $KY_FLEET), and kyboot.py, kyschema.py and kymanifest.py are components of the manifest with exactly the
     reviewed bytes;
  2. the manifest gate: `kymanifest.py check <M> --repo <the repository this file is in> --run <KY_RUN>` exits
     0 (entrypoints, components, generated pairs, probes, qualifications and the ACCEPTED review receipt still
     match disk); M defaults to <KY_RUN>/VERSIONS.bootstrap.json;
  3. the launch input (shape, job id, paths, worktree and branch policy, hashes, the prompt holding the exact
     bytes of the reviewed card and of the packet, empty MCP configuration, scratch and state locations,
     environment allowlist with JOB_SCRATCH and KY_SCRATCH, flags, effort, turn cap, deadline), bound to the
     manifest: the same approved source commit and plan version, and card_path and mcp_config are components;
  4. the qualification gate: <KY_RUN>/QUALIFICATIONS/<role>-<model>.json is recorded in the manifest, says
     exactly "PASS" and binds this launch: program path and sha256, model, effort, permission mode, turn limit,
     MCP configuration hash, environment names, the child PATH, the job worktree's .claude/settings.json
     (sha256 or "absent"), <KY_ROOT>/zdotdir, the qualification harness (kyqualify.py as the manifest lists
     it), a deadline no later than now + the qualified deadline_seconds, and the launch line, flag for flag.
     A receipt lacking any of these binds refuses;
  5. the program: `<claude_bin> --version` is run ONLY after 1–4 found the file to be the one the recorded
     receipt binds (path and sha256); its version must be at least the pin and the receipt's.
`run` then takes <KY_RUN>/locks/kyboot.<item> (one live supervisor per item), writes
<KY_RUN>/actions/ACT-launch-<job_id>.json (INTENDED) before the launch and completes it (DONE | FAILED) with
the observed termination, and records <KY_RUN>/jobs/<job_id>/state.json. It writes nothing else under KY_RUN
(beside a lock, only that lock's own short-lived private directories kyboot.<item>.new.*, .stale.*, .released.*):
no role-state file, nothing of the dispatcher's, nothing in fleet_live.

The item lock (cockpit ruling R2, the same rule in every fleet tool). A lock is a directory that never exists
without its owner.json: it is built in a private directory beside it and renamed into place. It is taken over
only when its recorded owner is POSITIVELY gone (ps: no such process, a zombie, or another start identity) and
the job that owner recorded is too: `child` null (none was started), or an identified job whose leader is
positively gone AND whose process group answers `killpg(pgid, 0)` with ESRCH. `child: "pending"` — written
before the job is started — an unidentified child, a missing or unreadable owner and anything ps cannot answer
are never taken over. A takeover renames the stale lock to a grave, reads the grave's owner.json again and
removes it only if it is exactly the owner that was judged; anything else is put back untouched. kyboot also
serialises its own acquisitions with an exclusive flock on the locks folder (no file is created).

Once the job's process exists nothing can leave it unsupervised: every later step — state writes, the owner
record, the supervision loop — runs inside one guard that ends the process group and records why, and `run`
then never answers 1.

Read from kyboot's own environment: KY_SCRATCH (required; the dated campaign scratch folder), KY_RUN (default
/Users/Dev/kalayantra/run), KY_FLEET (only to refuse running from it), KY_LAUNCHCTL (default /bin/launchctl),
XPC_SERVICE_NAME (set by launchd), PATH (to find git and ps), and three TESTS-ONLY names: KY_SCRATCH_ROOT_OVERRIDE
(replaces the root KY_SCRATCH must lie under), and — honoured only when that one is also set — KY_TEST_PPID
(stands in for the parent pid) and KY_WORKTREE_ROOT_OVERRIDE (replaces the root a job worktree must lie under).
With KY_SCRATCH_ROOT_OVERRIDE set, launchctl is run only from beneath that root: a test can never reach the real
launchd. Every override in use, and a KY_LAUNCHCTL that is not the default, is recorded in state.json and in
the action record and printed in the CHECK-PASSED line.

Exit: 0   check / argv / validate / status passed; run: the job exited 0 and left a valid result.json;
          submit: launchctl bootstrap exited 0; reap: every agent it booted out is confirmed absent
      1   refused (every reason on stderr) — nothing was launched or submitted
      2   malformed command, unknown schema name, a schema that kyschema refuses, or an interpreter that is
          not isolated (python3 -I)
      3   run: the job could not be started, exited non-zero, left a result.json that is invalid or refused (a
          symbolic link is never read), or the supervisor failed after starting it (the job was ended;
          state.json `supervisor_error`); submit: launchctl bootstrap failed; reap: an agent is still loaded
          after bootout
      5   run: the job's process group could not be confirmed gone (the item lock is then left in place), or
          the job ended without leaving result.json (state.json `termination_detail: "no_result"`; never 0)
      78  a credential variable name is set in kyboot's own environment (names printed, values never read)
      124 run: the deadline passed (the group was terminated)      130 run: the supervisor was signalled

The second engine. A launch input with "engine": "codex" (schemas/bootstrap_launch_input_codex.json) starts the
OpenAI Codex CLI instead of Claude Code. Everything above holds for it, with these differences: the launch line
is `codex exec` with launcher-owned flags only (build_codex_launch: --ignore-user-config, --ignore-rules, --json,
-o <job_scratch>/final_message.txt, -C <worktree>, -s <sandbox>, -m <model>, -c model_reasoning_effort, -c
approval_policy="never", -c web_search="disabled", -c sandbox_workspace_write.network_access, --disable <feature>
for each CODEX_DISABLED_FEATURES, --add-dir per writable_dirs and, for workspace-write, the job_scratch,
--output-schema when given, `-` for the prompt on stdin); there is no turn cap (Codex has none: the deadline is
the only limit), no MCP file and no extra flags; for workspace-write the job worktree's common git directory must
lie in the worktree or a writable dir; the receipt must say "engine": "codex" and binds the program as codex_bin /
codex_bin_sha256 / codex_version (`codex --version`, compared whole, pre-release suffix included, and at least
codex_min_version), sandbox, network, writable_dirs, the disabled features, --ignore-user-config and
--ignore-rules, persistent_mode false (the effort is high or xhigh, never "persistent"), output_schema_sha256, and the sha256 (or "absent") of <worktree>/AGENTS.md, $HOME/.codex/AGENTS.md
and $HOME/.codex/hooks.json; the provider session id is the stream's thread.started thread_id; the final result
event is the last turn.completed / turn.failed; and a job with an output_schema that leaves no result.json is
judged on its final message (final_message.txt) by the same rules when it left no result.json. A launch input
with "work_root": "job" (the reviewers, cockpit ruling E1) runs with -C <job_scratch> — with its TMPDIR all it may write; /tmp is excluded on every Codex line —
and --skip-git-repo-check; it names the item's working copy in item_worktree (= worktree) and its prompt carries
the line ITEM_WORKTREE=<item_worktree>; after the job that copy's HEAD and `git status` must be what they were
before. After every Codex job the hooks at both locations and this working copy's own git directory,
.git pointer, config.worktree and commondir must be unchanged (git_guard_record). Shared configuration and
other worktrees' entries may change concurrently; those differences are recorded, never fatal. A Codex builder (cockpit ruling E7) has no write
access to any git directory and no network: its launch input says commit_mode "launcher", network false, and
names no writable dir that holds or lies in a git directory; it does not commit — its result.json
(schemas/job_result_launcher_commit.json) carries status, tests and commit_message, never a head or a PR — and
kyboot, which never commits or pushes either, records awaiting_launcher_commit for the launcher to act on. A guard that changed, or cannot be read, fails the job
(exit 3; state.json `guard_failures`); one that cannot be read before the job refuses the launch.

What `check` passing means: the reviewed source, the manifest, the qualification and the launch input agreed
and the facts they name were true when checked. It is not a review of the prompt or the packet, and `run`
exiting 0 is not acceptance of the job's work (plan §7: independent review follows).

Limits, stated rather than hidden:
  * the group is the unit of supervision: a descendant that leaves the job's session / process group is not
    seen, and `group_gone` says nothing about it;
  * if the supervisor itself is killed, the job runs on with no deadline. Its lock then names it (or says
    "pending") and is never taken over; ending that job before a relaunch is the planner's step (B-1);
  * "gone" is `killpg(pgid, 0)` → ESRCH, asked after the leader has been collected. Signals after that point
    go to a group id that only its surviving members keep reserved; a recorded group id that another process
    group reuses later reads as "not gone" and keeps the lock for a person to reconcile;
  * a process identity is (pid, the text `LC_ALL=C ps -o lstart=` prints): local time, one-second resolution;
  * on Linux an exited-but-uncollected member still answers `killpg(…, 0)`, so a job whose children are
    collected late may be reported as `leftover_group: "terminated"` there; on macOS it is waited out;
  * the lock is installed with rename(2), which replaces an EMPTY directory: an empty directory that a foreign
    program creates at the lock path in the instant after kyboot looked is replaced (it named no owner);
  * the supervisor verifies the bytes on disk of the code it runs, at check time, and executes kyschema.py from
    those bytes; kymanifest.py is run by path (isolated) after its hash matched, and what the manifest tool
    starts in turn (kyqualify.py and what that imports) is verified, and isolated or not, by that tool — not
    here. The gate is as strong as the reviewed kymanifest.py; the interpreter and its standard library are
    trusted;
  * the program is hashed at check time, before `--version` is run; it is not hashed again at the instant it
    is executed or launched;
  * the qualification receipt is read for the fields compared here; its other fields are not judged;
  * the worktree and branch policy is a refusal list (the shared checkout, anything outside the Claude/Madhav
    worktree root, `main`, `suvarna*`); that the worktree is the right one for the item is the planner's;
  * `submit` returns when launchd has accepted the agent, not when the job has started: what the job did is in
    state.json and <job_scratch>/supervisor.err (`status`). A `run` that refuses inside the agent writes no
    state.json, so `reap` leaves that label loaded (its job's identity is unknown) for a person to boot out.
"""
import sys

if __name__ == "__main__" and not sys.flags.isolated:
    # Before anything else is imported: without -I the folder this file is in comes first on the import path, and
    # a file planted beside the reviewed code (json.py, hashlib.py, …) would run inside the supervisor before it
    # has verified anything. An isolated interpreter has neither that folder, nor PYTHONPATH, nor the user site.
    sys.stderr.write("kyboot.py runs only in an isolated interpreter: python3 -I -B kyboot.py <command> …\n"
                     "(without -I this file's own folder, PYTHONPATH and the user site could answer its imports; "
                     "nothing was read and nothing was run)\n")
    sys.exit(2)

import datetime as _dt  # noqa: E402
import errno  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import plistlib  # noqa: E402
import pwd  # noqa: E402
import re  # noqa: E402
import signal  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402

FLEET = os.path.dirname(os.path.realpath(__file__))

SCHEMA_DIR = os.path.join(FLEET, "schemas")
LAUNCH_SCHEMA = "bootstrap_launch_input"
LAUNCH_SCHEMA_CODEX = "bootstrap_launch_input_codex"        # a launch input with "engine": "codex"
RESULT_SCHEMA_LAUNCHER = "job_result_launcher_commit"       # result.json of a commit_mode "launcher" job
GUARD_RETRY_SECONDS = 2.0                                   # one second look before a guard is called changed
STATE_SCHEMA = "ky.bootstrap_job_state/3"
MANIFEST_SCHEMA = "ky.versions_bootstrap/1"
QUALIFICATION_SCHEMA = "ky.qualification/1"
ACTION_SCHEMA = "ky.action/1"

EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_JOB_FAILED, EXIT_GROUP_SURVIVED = 0, 1, 2, 3, 5
EXIT_NO_RESULT = 5                                         # cockpit ruling R1: a job without result.json, never 0
EXIT_CREDENTIAL_ENV, EXIT_TIMED_OUT, EXIT_INTERRUPTED = 78, 124, 130

DEFAULT_KY_RUN = "/Users/Dev/kalayantra/run"
INSTALLED_FLEET = "/Users/Dev/kalayantra/fleet_live"       # never the supervisor's home (plan §14 B-0c)
SUPERVISOR_CODE = ("kyboot.py", "kyschema.py", "kymanifest.py")    # everything this supervisor runs or executes
SCHEMA_TOOL = "kyschema.py"                                # executed from its verified bytes, never imported
HARNESS_FILE = "kyqualify.py"                              # the qualification harness a receipt binds by sha256
MANIFEST_BOUND_FILES = (("card_path", "card_sha256"), ("mcp_config", "mcp_config_sha256"))
LSTART_FMT = "%a %b %d %H:%M:%S %Y"                        # `LC_ALL=C ps -o lstart=`, as every fleet tool pins it
CHILD_PENDING = "pending"                                  # owner.json `child` from just before the job is started
LOCK_ATTEMPTS = 3
LOCK_GUARD_WAIT_SECONDS = 60.0
LABEL_PREFIX = "in.marsys.kalayantra.boot."                # + <job_id>: the one-shot agent of one bootstrap job
DEFAULT_LAUNCHCTL = "/bin/launchctl"
LAUNCHCTL_NOT_FOUND = 113                                  # `launchctl print`: "Could not find service"
LAUNCHCTL_PATH = "/usr/bin:/bin"
PLUTIL = "/usr/bin/plutil"
AGENT_PATH = "/opt/homebrew/bin:/usr/bin:/bin"
AGENT_ENV_NAMES = ("PATH", "HOME", "USER", "LANG", "KY_RUN", "KY_SCRATCH", "KY_ROOT")   # the agent's whole environment
ABSENT_CONFIRM_SECONDS = 2.0
DEFAULT_SCRATCH_ROOT = "/Users/Dev/scratch.noindex"
SCRATCH_ROOT_NEVER = ("/tmp", "/private/tmp", "/var/tmp", "/private/var/tmp")    # owner policy: never /tmp
SHARED_CHECKOUT = "/Users/Dev/Vibe-Coding/Apps/Madhav"     # never a job's worktree (isolation rule)
WORKTREE_ROOT = "/Users/Dev/worktrees.noindex/madhav/claude"   # every job worktree lies beneath it (owner policy)
BRANCHES_NEVER = "`main` and `suvarna*` are never job branches"
DEFAULT_GRACE_SECONDS = 20.0
KILL_CONFIRM_SECONDS = 10.0
POLL_SECONDS = 0.05
SESSION_SCAN_BYTES = 262144
FILE_MAX_BYTES = 8 << 20                                   # prompt, card, packet, MCP configuration: read whole
RESULT_MAX_BYTES = 1 << 20
ACTION_ID_MAX = 160                                        # schemas/action.json and kyaction.py: an action id's length
ACTION_VERBS = ("launch", "submit")                        # ACT-<verb>-<job_id>: the two action ids of one job

# plan §7 launch line plus cockpit ruling R1 (JOB_SCRATCH, KY_SCRATCH): the only names a job's environment may carry
ENV_ALLOWLIST = ("HOME", "PATH", "LANG", "TERM", "USER", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
                 "KY_STREAM", "KY_LANE", "KY_ITEM", "KY_PY", "SE_EPHE_PATH", "SWE_EPHE_PATH", "TESTS",
                 "KY_SCRATCH", "JOB_SCRATCH")
ENV_REQUIRED = ("HOME", "PATH", "KY_ROOT", "TMPDIR", "KY_SCRATCH", "JOB_SCRATCH")
ENV_PATH_VALUED = ("HOME", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_PY", "SE_EPHE_PATH",
                   "SWE_EPHE_PATH", "KY_SCRATCH", "JOB_SCRATCH")
ENV_FORBIDDEN = re.compile(r"^(DATABASE_URL|.*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY|.*TOKEN.*|.*SECRET.*)\Z",
                           re.IGNORECASE)
OWN_ENV_CREDENTIAL = re.compile(r"^(DATABASE_URL|.*_DATABASE_URL|PGPASSWORD|ANTHROPIC_API_KEY)\Z")

# plan §7 turn caps (ARTIFACT is the verifier's job kind and takes the VERIFY cap; SURROGATE is the owner
# surrogate's ruling job and takes the RULING cap)
TURN_CAPS = {"BUILD": 150, "REWORK": 100, "VERIFY": 60, "ARTIFACT": 60, "PRE-ACCEPT": 40, "RULING": 30,
             "SURROGATE": 30, "PLAN": 300}

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
IN_THE_PROMPT = ("card_path", "packet_path")              # their exact bytes must be in the prompt (plan §7)
BENEATH_JOB_SCRATCH = ("prompt_path", "stdout_path", "stderr_path", "tmp_path")
# what a receipt must bind beyond its launch line and its program version (plan §7 KV-06, cockpit ruling R6)
BOUND_FACTS = ("claude_bin", "claude_bin_sha256", "model", "effort", "permission_mode", "max_turns",
               "mcp_config_sha256", "env_names", "child_path", "project_settings_sha256", "zdotdir_sha256",
               "harness_sha256")

# the second engine, the OpenAI Codex CLI ("engine": "codex"; see the module documentation)
CODEX_PATH_FIELDS = ("worktree", "codex_bin", "prompt_path", "card_path", "packet_path", "job_scratch",
                     "stdout_path", "stderr_path", "tmp_path", "state_path")
CODEX_HASHED_FILES = (("prompt_path", "prompt_sha256"), ("card_path", "card_sha256"), ("packet_path", "packet_sha256"))
CODEX_MANIFEST_BOUND_FILES = (("card_path", "card_sha256"),)
OUTPUT_SCHEMA_FILE = ("output_schema", "output_schema_sha256")   # optional; hashed and manifest-bound when given
# byte for byte kyqualify.py's CODEX_DISABLED_FEATURES: the receipt binds the tuple and the line carries it
CODEX_DISABLED_FEATURES = ("memories", "multi_agent", "multi_agent_v2", "apps", "plugins", "remote_plugin",
                           "browser_use", "browser_use_external", "in_app_browser", "computer_use", "hooks",
                           "daemon_auto_start", "goals", "tool_suggest", "worktrees", "image_generation",
                           "in_app_local_automation", "chronicle", "enable_fanout", "agent_message_board",
                           "send_async_message", "web_search_request", "standalone_web_search", "skill_search",
                           "plugin_hooks", "recommended_plugins", "remote_control", "js_repl")
CODEX_BOUND_FACTS = ("engine", "codex_bin", "codex_bin_sha256", "model", "effort", "sandbox", "network",
                     "work_root", "commit_mode", "writable_dirs", "env_names", "child_path", "output_schema_sha256", "codex_disabled_features",
                     "ignore_user_config", "ignore_rules", "skills_include_instructions", "persistent_mode", "exclude_slash_tmp",
                     "exclude_tmpdir_env_var", "project_agents_md_sha256",
                     "user_codex_agents_md_sha256",
                     "user_codex_hooks_sha256", "zdotdir_sha256", "harness_sha256")
FINAL_MESSAGE = "final_message.txt"                        # codex exec -o, in the job's own folder
ITEM_LINE = "ITEM_WORKTREE="                               # + item_worktree: the prompt line of a job-rooted run
JOB_DIR = "<JOB_DIR>"                                      # the job folder in a receipt's bound launch line
_CODEX_VERSION = re.compile(r"^codex-cli ((\d+)\.(\d+)\.(\d+)[0-9A-Za-z.+-]*)\s*\Z")

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


def is_codex(launch) -> bool:
    """the launch input names the second engine (absent "engine" is Claude Code)"""
    return type(launch) is dict and launch.get("engine") == "codex"


def program_field(launch) -> str:
    return "codex_bin" if is_codex(launch) else "claude_bin"


def path_fields(launch) -> tuple:
    if not is_codex(launch):
        return PATH_FIELDS
    return CODEX_PATH_FIELDS + tuple(field for field in ("output_schema", "item_worktree") if field in launch)


def codex_builder(launch) -> bool:
    """a Codex builder: workspace-write, rooted in the item's working copy (cockpit ruling E7 applies to it)"""
    return is_codex(launch) and launch.get("sandbox") == "workspace-write" \
        and launch.get("work_root", "worktree") == "worktree"


def launcher_commit(launch) -> bool:
    """the job leaves its changes uncommitted and a proposed commit message; the launcher commits (commit_mode)"""
    return is_codex(launch) and launch.get("commit_mode") == "launcher"


def job_rooted(launch) -> bool:
    """a Codex run whose -C is its own job folder (work_root "job": the reviewers, cockpit ruling E1)"""
    return is_codex(launch) and launch.get("work_root") == "job"


def tree_digest(directory):
    """sha256 over the relative path, then the content (for a link: its target) of every file under `directory`,
    walked in sorted order · "absent" when there is no such directory · None when it cannot be read — byte for byte
    kyqualify.py's `tree_digest`"""
    if not os.path.lexists(directory):
        return "absent"
    if os.path.islink(directory) or not os.path.isdir(directory):
        return None
    digest = hashlib.sha256()
    try:
        for base, dirs, files in os.walk(directory):
            dirs.sort()
            for name in sorted(files + [d for d in dirs if os.path.islink(os.path.join(base, d))]):
                path = os.path.join(base, name)
                digest.update(os.path.relpath(path, directory).encode("utf-8") + b"\0")
                if os.path.islink(path):
                    digest.update(b"link:" + os.readlink(path).encode("utf-8"))
                else:
                    with open(path, "rb") as handle:
                        digest.update(handle.read())
                digest.update(b"\0")
    except OSError:
        return None
    return digest.hexdigest()


def git_guard_record(worktree, common, gitdir, includes, effective_hooks):
    """the git guard's record (cockpit ruling E2 as amended after reviews r1 and r2) — this function and
    git_guard_changes are the same text in kyboot.py and kyqualify.py:
      config_files   sha256 (or "absent") of every configuration file git reads for the common directory: config,
                     config.worktree, each file an include.path / includeIf.*.path of the common config names
                     ("include:<path>"), and for every <common>/worktrees/<name> its config.worktree, commondir and
                     gitdir (a rewritten commondir makes git in that worktree read another folder's config)
      worktree_entries  the names under <common>/worktrees when the record was taken
      own            the working copy's own git identity: its absolute git dir, its .git pointer (sha256 of the
                     file; "directory" for a plain repository), its config.worktree and commondir, and a tree
                     digest of its private git dir (for a plain repo: HEAD and index only; shared files report below)
      hooks          a tree digest of <common>/hooks and of the effective hooks folder, by path"""
    files = {"config": file_digest(os.path.join(common, "config")),
             "config.worktree": file_digest(os.path.join(common, "config.worktree"))}
    try:
        entries = sorted(name for name in os.listdir(os.path.join(common, "worktrees"))
                         if os.path.isdir(os.path.join(common, "worktrees", name)))
    except OSError:
        entries = []
    for name in entries:
        for part in ("config.worktree", "commondir", "gitdir"):
            files["worktrees/%s/%s" % (name, part)] = file_digest(os.path.join(common, "worktrees", name, part))
    for path in sorted(set(includes)):
        files["include:" + path] = file_digest(path)
    pointer = os.path.join(worktree, ".git")
    own = {"git_dir": gitdir,
           "pointer": file_digest(pointer) if os.path.isfile(pointer) else "directory" if os.path.isdir(pointer) else "absent",
           "config.worktree": file_digest(os.path.join(gitdir, "config.worktree")),
           "commondir": file_digest(os.path.join(gitdir, "commondir")),
           "tree_sha256": tree_digest(gitdir) if gitdir != common else {
               name: file_digest(os.path.join(gitdir, name)) for name in ("HEAD", "index")}}
    hooks = {path: tree_digest(path) for path in sorted({os.path.join(common, "hooks"), effective_hooks})}
    return {"common_dir": common, "config_files": files, "worktree_entries": entries, "own": own, "hooks": hooks}


def git_guard_changes(before, after):
    """Fatal changes: hooks at both locations, common identity, and this job's own git dir / pointer.
    Shared config and other worktrees are reported separately, since concurrent sessions change them."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return ["unreadable"]
    out = ["common_dir"] if before["common_dir"] != after["common_dir"] else []
    for part in ("own", "hooks"):
        out += sorted("%s:%s" % (part, key) for key in set(before[part]) | set(after[part])
                      if before[part].get(key) != after[part].get(key))
        if any(value is None for value in list(before[part].values()) + list(after[part].values())):
            out.append(part + ":unreadable")
    return out


def git_shared_report(before, after):
    """Reported-only churn. Changed keys name the config_files snapshot entries, never their contents.
    Missing records yield null, rather than a claim that nothing changed."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {"shared_config_changed_during_run": None, "shared_config_changed_keys": None}

    own_dirs = {os.path.relpath(record["own"]["git_dir"], record["common_dir"])
                for record in (before, after)}

    def shared(record):
        return {key: value for key, value in record["config_files"].items()
                if not any(own != "." and key.startswith(own + "/") for own in own_dirs)
                and not ("." in own_dirs and key == "config.worktree")}

    old, new = shared(before), shared(after)
    changes = sorted(key for key in set(old) | set(new) if old.get(key) != new.get(key))
    return {"shared_config_changed_during_run": bool(changes), "shared_config_changed_keys": changes}


def include_paths(common, lines):
    """the files an include.path / includeIf.<condition>.path of the common config names, from the lines of `git
    config --file <common>/config --get-regexp`: absolute, '~/' from the home folder, anything else relative to
    the common directory (as git resolves them)"""
    out = []
    for line in lines:
        value = line.split(None, 1)[1].strip() if len(line.split(None, 1)) == 2 else ""
        if value:
            value = os.path.expanduser(value) if value.startswith("~") else value
            out.append(os.path.realpath(value if os.path.isabs(value) else os.path.join(common, value)))
    return out


def git_guard(worktree, environ):
    """the git guard record of a worktree (git_guard_record), everything derived with git — the common directory
    (`rev-parse --git-common-dir`), the worktree's own git dir (`--absolute-git-dir`), the effective hooks folder
    (`--git-path hooks`) and the common config's includes; None when git cannot say"""
    code, common = _git(worktree, environ, "rev-parse", "--path-format=absolute", "--git-common-dir")
    own_code, gitdir = _git(worktree, environ, "rev-parse", "--absolute-git-dir")
    hooks_code, hooks = _git(worktree, environ, "rev-parse", "--git-path", "hooks")
    if code != 0 or own_code != 0 or hooks_code != 0 or not os.path.isabs(common) or not os.path.isabs(gitdir) \
            or not hooks:
        return None
    common = os.path.realpath(common)
    listed_code, listed = _git(worktree, environ, "config", "--file", os.path.join(common, "config"), "--get-regexp",
                               r"^include(if\..*)?\.path$")
    includes = include_paths(common, listed.splitlines() if listed_code == 0 else [])
    return git_guard_record(worktree, common, os.path.realpath(gitdir), includes,
                            os.path.realpath(os.path.join(worktree, hooks)))


def worktree_guard(worktree, environ):
    """{head, status_sha256} of a worktree (cockpit ruling E1: HEAD and `git status`, untracked files included),
    or None when git cannot say"""
    code, head = _git(worktree, environ, "rev-parse", "HEAD")
    status_code, status = _git(worktree, environ, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if code != 0 or status_code != 0 or not _HEX40.match(head):
        return None
    return {"head": head, "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest()}


def codex_guards(launch, environ) -> dict:
    """what must be the same after a Codex job: hooks and its own git directory (every Codex job) and,
    for a job-rooted one, the item's working copy (HEAD and status)"""
    guards = {"git": git_guard(launch["worktree"], environ)}
    if job_rooted(launch):
        guards["worktree"] = worktree_guard(launch["worktree"], environ)
    return guards


def hashed_files(launch) -> tuple:
    if not is_codex(launch):
        return HASHED_FILES
    return CODEX_HASHED_FILES + ((OUTPUT_SCHEMA_FILE,) if all(key in launch for key in OUTPUT_SCHEMA_FILE) else ())


def manifest_bound_files(launch) -> tuple:
    if not is_codex(launch):
        return MANIFEST_BOUND_FILES
    return CODEX_MANIFEST_BOUND_FILES + ((OUTPUT_SCHEMA_FILE,) if all(key in launch for key in OUTPUT_SCHEMA_FILE)
                                         else ())


def file_digest(path):
    """sha256 of a regular file · "absent" when nothing is there · None when it cannot be bound (the rule of
    kyqualify.py's `file_digest`, which writes the instruction and hook binds of a Codex receipt)"""
    if not os.path.lexists(path):
        return "absent"
    try:
        return sha256_file(path) if os.path.isfile(path) else None
    except OSError:
        return None


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


def load_json_text(text: str):
    """strict JSON: a duplicate object key, NaN or Infinity refuses the document (ValueError names the reason).
    The rule of kyschema.py, kept here so that nothing of this folder is needed before it has been verified."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate key {key!r}")
            out[key] = value
        return out

    def constant(name):
        raise ValueError(f"{name} is not JSON")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_json_and_sha(path):
    """(the strictly parsed document, the sha256 of the very bytes it was parsed from); ValueError says why not"""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as unreadable:
        raise ValueError(f"cannot read {path}: {unreadable}") from None
    try:
        return load_json_text(data.decode("utf-8")), hashlib.sha256(data).hexdigest()
    except (ValueError, UnicodeDecodeError, RecursionError) as bad:
        raise ValueError(f"{path} is not acceptable JSON: {bad}") from None


def read_json(path):
    return read_json_and_sha(path)[0]


def read_bounded(path, limit):
    """the whole content of a file, or None when it is larger than `limit` bytes; OSError when it cannot be read"""
    with open(path, "rb") as handle:
        data = handle.read(limit + 1)
    return None if len(data) > limit else data


def same_json(a, b) -> bool:
    """two JSON values are the same value of the same type (150 is not 150.0 and true is not 1)"""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_json(a[key], b[key]) for key in a)
    return a == b


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
    try:
        return sorted(name[:-len(".json")] for name in os.listdir(SCHEMA_DIR) if name.endswith(".json"))
    except OSError:
        return []


def load_schema(name: str):
    return read_json(os.path.join(SCHEMA_DIR, f"{name}.json"))


def module_from_bytes(name, path, data):
    """a module made of exactly these bytes: nothing is looked up on the import path and no compiled cache
    beside the file is read or written"""
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(data, path, "exec"), module.__dict__)
    return module


# --------------------------------------------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------------------------------------------
class Checked:
    """the outcome of `check`: .launch (None when unreadable or not examined), .findings (every refusal),
    .facts (what was observed), .schema_tool (the verified kyschema module, None when the gate refused)"""

    def __init__(self, launch, findings, facts, schema_tool=None):
        self.launch, self.findings, self.facts, self.schema_tool = launch, findings, facts, schema_tool

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


def overrides_in_use(environ) -> dict:
    """{name: value} of every tests-only override this run honours and of a launchctl that is not the default:
    recorded in state.json and in the action record, and printed by `check` (never silently in force)"""
    used = {}
    testing = environ.get("KY_SCRATCH_ROOT_OVERRIDE") is not None
    if testing:
        used["KY_SCRATCH_ROOT_OVERRIDE"] = environ["KY_SCRATCH_ROOT_OVERRIDE"]
        for name in ("KY_TEST_PPID", "KY_WORKTREE_ROOT_OVERRIDE"):
            if environ.get(name) is not None:
                used[name] = environ[name]
    if launchctl_program(environ) != DEFAULT_LAUNCHCTL:
        used["KY_LAUNCHCTL"] = launchctl_program(environ)
    return used


def show_overrides(used) -> str:
    """one line, whatever the values hold: each value as a JSON string, whole"""
    return ", ".join(f"{name}={json.dumps(used[name], ensure_ascii=False)}" for name in sorted(used)) if used else "none"


def env_findings(launch, ky_run, scratch) -> list:
    """the job's environment: allowlist, required names, absolute paths, and the values the supervisor can
    check — TMPDIR, KY_RUN, KY_ITEM, ZDOTDIR, and (ruling R1) JOB_SCRATCH and KY_SCRATCH. `scratch` is the
    supervisor's resolved KY_SCRATCH, None when that was refused."""
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
    if "JOB_SCRATCH" in env and env["JOB_SCRATCH"] != launch["job_scratch"]:
        out.append(f"env.JOB_SCRATCH: {env['JOB_SCRATCH']!r} must equal job_scratch {launch['job_scratch']!r}")
    if "KY_SCRATCH" in env and scratch is not None and env["KY_SCRATCH"] != scratch:
        out.append(f"env.KY_SCRATCH: {env['KY_SCRATCH']!r} differs from the supervisor's resolved KY_SCRATCH "
                   f"{scratch!r}")
    if "KY_RUN" in env and env["KY_RUN"] != ky_run:
        out.append(f"env.KY_RUN: {env['KY_RUN']!r} differs from the supervisor's KY_RUN {ky_run!r}")
    if "KY_ITEM" in env and env["KY_ITEM"] != launch["item"]:
        out.append(f"env.KY_ITEM: {env['KY_ITEM']!r} differs from item {launch['item']!r}")
    root = env.get("KY_ROOT")
    if isinstance(root, str) and os.path.isabs(root) and not os.path.isdir(root):
        out.append(f"env.KY_ROOT: {root} is not an existing directory (it is passed as --add-dir)")
    if "ZDOTDIR" in env and isinstance(root, str) and env["ZDOTDIR"] != os.path.join(root, "zdotdir"):
        out.append(f"env.ZDOTDIR: {env['ZDOTDIR']!r} must equal <KY_ROOT>/zdotdir (the qualified shell start-up)")
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
    to carry TMPDIR, JOB_SCRATCH and KY_SCRATCH with the values the supervisor resolved)"""
    return {name: launch["env"][name] for name in sorted(launch["env"]) if name in ENV_ALLOWLIST}


def worktree_root(environ):
    """(the root every job worktree must lie beneath, whether the tests-only override replaced it).
    TESTS ONLY: KY_WORKTREE_ROOT_OVERRIDE replaces the root, and ONLY when KY_SCRATCH_ROOT_OVERRIDE (itself
    tests-only) is also set; its use is recorded like every override."""
    if environ.get("KY_SCRATCH_ROOT_OVERRIDE") is not None and environ.get("KY_WORKTREE_ROOT_OVERRIDE") is not None:
        return environ["KY_WORKTREE_ROOT_OVERRIDE"], True
    return WORKTREE_ROOT, False


def worktree_policy_findings(launch, environ) -> list:
    """where a job may never run: the shared checkout, anywhere outside the worktree root, `main`, `suvarna*`"""
    out = []
    real = os.path.realpath(launch["worktree"])
    shared = os.path.realpath(SHARED_CHECKOUT)
    if real == shared or _is_beneath(real, shared):
        out.append(f"worktree: {real} is the shared checkout {SHARED_CHECKOUT}; a job never runs there")
    root, overridden = worktree_root(environ)
    if overridden and (not os.path.isabs(root) or not os.path.isdir(root)):
        out.append("KY_WORKTREE_ROOT_OVERRIDE: is set but is not an existing absolute directory")
    elif not _is_beneath(real, os.path.realpath(root)):
        out.append(f"worktree: {real} is not beneath the worktree root {os.path.realpath(root)}")
    branch = launch["branch"]
    if branch == "main" or branch.lower().startswith("suvarna"):
        out.append(f"branch: {branch!r} is refused ({BRANCHES_NEVER})")
    return out


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


def _program_findings(launch, facts) -> list:
    """the program as a file: it exists, is executable, and its resolved bytes are hashed. NOTHING is executed
    here — the hash is compared with the recorded qualification receipt first (see `_version_findings`)."""
    field = program_field(launch)
    binary = launch[field]
    if not os.path.isfile(binary):
        return [f"{field}: does not exist or is not a file: {binary}"]
    if not os.access(binary, os.X_OK):
        return [f"{field}: not executable: {binary}"]
    facts[f"{field}_realpath"] = os.path.realpath(binary)
    try:
        facts[f"{field}_sha256"] = sha256_file(facts[f"{field}_realpath"])
    except OSError as unreadable:
        return [f"{field}: cannot be read: {unreadable}"]
    return []


def _version_findings(launch, facts, binds) -> list:
    """run `<claude_bin> --version` — only ever called for a program the recorded PASS receipt binds by path and
    sha256 — and hold its answer against the pinned minimum and the receipt's version"""
    done = _run_version(launch, "claude_bin")
    if isinstance(done, str):
        return [done]
    found = parse_version(done.stdout)
    first = (done.stdout.strip().splitlines() or [""])[0]
    if found is None:
        return [f"claude_bin: version output is not X.Y.Z: {first[:80]!r}"]
    facts["claude_version"] = first.strip()
    out = []
    minimum = parse_version(launch["claude_min_version"])
    if minimum is None or found < minimum:
        out.append(f"claude_bin: version {'.'.join(map(str, found))} is below the pinned minimum "
                   f"{launch['claude_min_version']}")
    bound = parse_version(binds["claude_version"]) if isinstance(binds.get("claude_version"), str) else None
    if "claude_version" not in binds:
        out.append("qualification: binds.claude_version is missing")
    elif bound is None or found != bound:
        out.append(f"qualification: binds.claude_version {_show(binds['claude_version'])} does not bind this "
                   f"launch ({facts['claude_version']!r})")
    return out


def _run_version(launch, field):
    """the finished `<program> --version` of the launch's program, in the job's environment (no TMPDIR: tmp_path
    need not exist before `run`), or the finding that says why it could not be read"""
    binary = launch[field]
    env = clean_env(launch)
    env.pop("TMPDIR", None)
    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True, env=env, timeout=60,
                              stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError) as failed:
        return f"{field}: --version could not be run: {failed}"
    if done.returncode != 0:
        return f"{field}: --version exited {done.returncode}"
    return done


def _codex_version_findings(launch, facts, binds) -> list:
    """run `<codex_bin> --version` — only for a program the recorded PASS receipt binds by path and sha256 — and
    hold it against codex_min_version and the receipt's codex_version (compared whole: a pre-release build is a
    program of its own)"""
    done = _run_version(launch, "codex_bin")
    if isinstance(done, str):
        return [done]
    first = (done.stdout.strip().splitlines() or [""])[0].strip()
    match = _CODEX_VERSION.match(first)
    if match is None:
        return [f"codex_bin: version output is not 'codex-cli X.Y.Z': {first[:80]!r}"]
    facts["codex_version"] = match.group(1)
    found = tuple(int(part) for part in match.group(2, 3, 4))
    out = []
    minimum = parse_version(launch["codex_min_version"])
    if minimum is None or found < minimum:
        out.append(f"codex_bin: version {facts['codex_version']} is below the pinned minimum "
                   f"{launch['codex_min_version']}")
    if "codex_version" not in binds:
        out.append("qualification: binds.codex_version is missing")
    elif binds["codex_version"] != facts["codex_version"]:
        out.append(f"qualification: binds.codex_version {_show(binds['codex_version'])} does not bind this launch "
                   f"({facts['codex_version']!r})")
    return out


def _codex_findings(launch, environ, facts) -> list:
    """what only a Codex launch needs: writable roots that exist; none (and no network) for read-only; for
    workspace-write the job worktree's common git directory inside a writable root (where a commit is written);
    output_schema and its hash together"""
    out = []
    dirs = launch["writable_dirs"]
    for directory in dirs:
        if not os.path.isabs(directory) or os.path.normpath(directory) != directory:
            out.append(f"writable_dirs: {directory!r} is not an absolute, normalised path")
        elif not os.path.isdir(directory):
            out.append(f"writable_dirs: {directory} is not an existing directory")
    if job_rooted(launch):
        item = launch.get("item_worktree")
        if not isinstance(item, str) or os.path.realpath(item) != os.path.realpath(launch["worktree"]):
            out.append("item_worktree: a job-rooted run names the item's working copy, which is its worktree")
        else:
            try:
                prompt = read_bounded(launch["prompt_path"], FILE_MAX_BYTES) or b""
            except OSError:
                prompt = b""
            if (ITEM_LINE + item + "\n").encode("utf-8") not in prompt:
                out.append(f"prompt_path: the prompt does not tell the job its item's working copy (a line "
                           f"{ITEM_LINE}{item})")
        if dirs:
            out.append("writable_dirs: a job-rooted run writes its own folder and its TMPDIR; no other root")
    if launch["sandbox"] == "read-only":
        if dirs:
            out.append("writable_dirs: a read-only job writes nowhere; writable_dirs must be empty")
        if launch["network"] is not False:
            out.append("network: a read-only sandbox has no network setting; network must be false")
    builder = codex_builder(launch)                  # cockpit ruling E7: no git directory, no network, no commit
    if builder and launch.get("commit_mode") != "launcher":
        out.append('commit_mode: a Codex builder says "launcher" (the launcher commits and pushes for it)')
    if not builder and "commit_mode" in launch:
        out.append("commit_mode: only a Codex builder (worktree-rooted, workspace-write) has one")
    if builder and launch["network"] is not False:
        out.append("network: a Codex builder has no network (the launcher pushes for it); network must be false")
    if any(".git" in directory.split(os.sep) for directory in dirs):
        out.append("writable_dirs: no git directory, and nothing inside one, is ever a writable root")
    if os.path.isdir(launch["worktree"]):
        code, common = _git(launch["worktree"], environ, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if code != 0 or not os.path.isabs(common):
            out.append("worktree: its common git directory cannot be read")
        else:
            common = os.path.realpath(common)
            facts["git_common_dir"] = common
            roots = [os.path.realpath(d) for d in dirs if os.path.isabs(d)] + \
                ([os.path.realpath(launch["worktree"])] if builder else [])
            if any(common == root or _is_beneath(common, root) or _is_beneath(root, common) for root in roots):
                out.append(f"writable_dirs: the worktree's common git directory {common} would be writable (a "
                           f"writable root holds it or lies inside it); a Codex job writes no git directory")
    if (OUTPUT_SCHEMA_FILE[0] in launch) != (OUTPUT_SCHEMA_FILE[1] in launch):
        out.append("output_schema: output_schema and output_schema_sha256 are given together or not at all")
    return out


def _file_findings(launch) -> list:
    """the four hashed files hold the bytes their hashes name; the MCP configuration is the empty one; and the
    prompt carries the exact bytes of the reviewed card and of the packet (plan §7: card + packet + header)"""
    out, content = [], {}
    for path_field, hash_field in hashed_files(launch):
        path = launch[path_field]
        if not os.path.isfile(path):
            out.append(f"{path_field}: does not exist or is not a file: {path}")
            continue
        try:
            data = read_bounded(path, FILE_MAX_BYTES)
        except OSError as unreadable:
            out.append(f"{path_field}: cannot be read: {unreadable}")
            continue
        if data is None:
            out.append(f"{path_field}: larger than {FILE_MAX_BYTES} bytes; refused unread")
            continue
        actual = hashlib.sha256(data).hexdigest()
        if actual != launch[hash_field]:
            out.append(f"{path_field}: sha256 mismatch: the file is {actual}, {hash_field} says {launch[hash_field]}")
        else:
            content[path_field] = data
        if path_field == "mcp_config":
            try:
                configured = load_json_text(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError, RecursionError) as bad:
                out.append(f"mcp_config: {path} is not acceptable JSON: {bad}")
            else:
                if type(configured) is not dict or list(configured) != ["mcpServers"] \
                        or type(configured["mcpServers"]) is not dict or configured["mcpServers"]:
                    out.append('mcp_config: the content must be exactly {"mcpServers":{}} for a bootstrap job')
    if "prompt_path" in content:
        for field in IN_THE_PROMPT:
            if field not in content:
                continue                                  # already refused above, by its own reason
            if not content[field]:
                out.append(f"{field}: the file is empty; an empty file cannot be shown to be in the prompt")
            elif content[field] not in content["prompt_path"]:
                out.append(f"prompt_path: the prompt does not contain the exact bytes of {field} "
                           f"({launch[field]}); a prompt is the reviewed card + the packet + the job header")
    return out


def job_id_findings(job_id: str) -> list:
    """a job id leaves room for its action ids: ACT-launch-<job_id> and ACT-submit-<job_id> are action ids, and an
    action id has at most ACTION_ID_MAX characters. (The launch-input schema's own limit of 128 is the tighter
    one today; this refusal is what stops either limit from moving without the other.)"""
    longest = max(len(f"ACT-{verb}-{job_id}") for verb in ACTION_VERBS)
    if longest > ACTION_ID_MAX:
        return [f"job_id: {len(job_id)} characters; its action ids (ACT-launch-<job_id>, ACT-submit-<job_id>) would "
                f"have {longest}, more than the {ACTION_ID_MAX} an action id may have"]
    return []


def _location_findings(launch, ky_run, scratch) -> list:
    out = []
    job_id = launch["job_id"]
    expected_state = os.path.join(ky_run, "jobs", job_id, "state.json")
    if launch["state_path"] != expected_state:
        out.append(f"state_path: {launch['state_path']} is not <KY_RUN>/jobs/<job_id>/state.json = "
                   f"{expected_state}")
    job_real = os.path.realpath(launch["job_scratch"])
    if scratch is not None:
        expected = os.path.join(scratch, "jobs", job_id)
        if job_real != expected:
            out.append(f"job_scratch: {job_real} is not <KY_SCRATCH>/jobs/<job_id> = {expected}")
        elif launch["job_scratch"] != expected:
            out.append(f"job_scratch: {launch['job_scratch']} is not written as the resolved path {expected} "
                       f"(the job reads it as JOB_SCRATCH)")
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
    """(exit code, stdout, stderr) of the reviewed sibling: kymanifest.py check <manifest> --repo … --run …
    — isolated, and with no GIT_* redirection and no PYTHON* variable to pass on to the harness it starts"""
    env = {name: value for name, value in environ.items() if not name.startswith(("GIT_", "PYTHON"))}
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
    """(manifest or None, components, findings, the verified kyschema module or None): the supervisor is the
    reviewed code and the manifest gate passes. Each sibling is read ONCE: the bytes that are hashed are the
    bytes that are executed (kyschema.py) — nothing is imported from this folder."""
    findings = []
    own = os.path.realpath(__file__)
    facts["supervisor_path"], facts["manifest_path"] = own, manifest_path
    facts["python_isolated"] = bool(sys.flags.isolated)
    try:
        facts["supervisor_sha256"] = sha256_file(own)
    except OSError as unreadable:
        return None, {}, [f"supervisor: cannot read its own file {own}: {unreadable}"], None
    installed = installed_fleet_root(own, environ)
    if installed:
        findings.append(f"supervisor: {own} runs from the installed fleet {installed}; the bootstrap supervisor "
                        f"runs only from the reviewed staged source")
    code, top = _git(os.path.dirname(own), environ, "rev-parse", "--show-toplevel")
    if code != 0 or not top:
        return None, {}, findings + [f"supervisor: {own} is not inside a git work tree; there is no reviewed "
                                     f"source to verify it against"], None
    source = os.path.realpath(top)
    facts["source_repo"] = source
    manifest, components, file_sha, problems = load_manifest(manifest_path)
    if manifest is None:
        return None, {}, findings + problems, None
    facts["manifest_sha256"], facts["manifest_file_sha256"] = manifest["manifest_sha256"], file_sha

    reviewed_code, code_bytes = True, {}
    for name in SUPERVISOR_CODE:
        path = os.path.join(os.path.dirname(own), name)
        relative = os.path.relpath(path, source)
        if relative not in components:
            findings.append(f"supervisor: {relative} is not a component of the manifest")
            reviewed_code = False
            continue
        try:
            with open(path, "rb") as handle:
                code_bytes[name] = handle.read()
            actual = hashlib.sha256(code_bytes[name]).hexdigest()
        except OSError:
            actual = "unreadable"
        if actual != components[relative]:
            findings.append(f"supervisor: {relative} is not the reviewed file (sha256 {actual}, the manifest "
                            f"says {components[relative]})")
            reviewed_code = False
    if not reviewed_code:
        findings.append("manifest gate: kymanifest.py check was not run because the supervisor's own code is not "
                        "the reviewed code")
        return manifest, components, findings, None
    try:
        schema_tool = module_from_bytes("kyschema_reviewed", os.path.join(os.path.dirname(own), SCHEMA_TOOL),
                                        code_bytes[SCHEMA_TOOL])
    except Exception as broken:                      # reviewed bytes that do not even load: a refusal, not a crash
        return manifest, components, findings + [f"supervisor: {SCHEMA_TOOL} could not be loaded from its "
                                                 f"reviewed bytes: {type(broken).__name__}: {broken}"], None
    code, out, err = run_manifest_check(os.path.join(os.path.dirname(own), "kymanifest.py"), manifest_path, source,
                                        ky_run, environ)
    if code != 0:
        first = (err.strip().splitlines() or [f"kymanifest.py check exited {code}"])[0]
        findings.append(f"manifest gate: {first}")
        return manifest, components, findings, schema_tool
    try:
        said = json.loads(out)
    except ValueError:
        said = None
    if type(said) is not dict or said.get("ok") is not True \
            or said.get("manifest_sha256") != manifest["manifest_sha256"]:
        findings.append("manifest gate: kymanifest.py check exited 0 without confirming this manifest's digest")
    return manifest, components, findings, schema_tool


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
    for path_field, hash_field in manifest_bound_files(launch):
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


def portable_codex_argv(argv, worktree, job_dir=None):
    """a Codex launch line without what legitimately differs between launches: the job folder (<JOB_DIR>, as a
    receipt binds it), the --output-schema path (its content is bound by hash) and the worktree prefix"""
    out = []
    for index, element in enumerate(argv):
        if index and argv[index - 1] == "--output-schema":
            out.append("<OUTPUT_SCHEMA>")
        elif isinstance(job_dir, str) and job_dir and (element == job_dir or element.startswith(job_dir + "/")):
            out.append(JOB_DIR + element[len(job_dir):])
        elif isinstance(worktree, str) and worktree and (element == worktree or element.startswith(worktree + "/")):
            out.append("<WORKTREE>" + element[len(worktree):])
        else:
            out.append(element)
    return out


def project_settings_digest(worktree):
    """the sha256 of <worktree>/.claude/settings.json · "absent" when there is no such file · None when it is
    there but cannot be read (cockpit ruling R6: what `--setting-sources project` loads for the job; the same
    value as kyqualify.py's `file_digest`, which writes this bind)"""
    path = os.path.join(worktree, ".claude", "settings.json")
    if not os.path.lexists(path):
        return "absent"
    try:
        return sha256_file(path) if os.path.isfile(path) else None
    except OSError:
        return None


def zdotdir_digest(folder):
    """the sha256 over the name, then the content, of every regular file directly in `folder`, names sorted (no
    separator; links and sub-directories skipped) · "absent" when there is no such folder · None when it is not
    a folder or cannot be read. Cockpit ruling R6: the shell start-up files a job's ZDOTDIR names — byte for
    byte kyqualify.py's `directory_digest`, which writes this bind (and kyloop.py's `zdotdir_digest`)."""
    if not os.path.lexists(folder):
        return "absent"
    if not os.path.isdir(folder):
        return None
    digest = hashlib.sha256()
    try:
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            digest.update(name.encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(handle.read())
    except (OSError, ValueError):
        return None
    return digest.hexdigest()


def expected_binds(launch, components, facts) -> dict:
    """what a receipt must bind for THIS launch, each value observed by the supervisor (None: not observable)"""
    harness = os.path.relpath(os.path.join(FLEET, HARNESS_FILE), facts["source_repo"])
    return {"claude_bin": launch["claude_bin"], "claude_bin_sha256": facts.get("claude_bin_sha256"),
            "model": launch["model"], "effort": launch["effort"], "permission_mode": launch["permission_mode"],
            "max_turns": launch["max_turns"], "mcp_config_sha256": launch["mcp_config_sha256"],
            "env_names": sorted(launch["env"]), "child_path": launch["env"]["PATH"],
            "project_settings_sha256": facts.get("project_settings_sha256"),
            "zdotdir_sha256": facts.get("zdotdir_sha256"), "harness_sha256": components.get(harness)}


def expected_codex_binds(launch, components, facts) -> dict:
    """what a Codex receipt must bind for THIS launch, each value observed by the supervisor (None: not observable)"""
    harness = os.path.relpath(os.path.join(FLEET, HARNESS_FILE), facts["source_repo"])
    return {"engine": "codex", "codex_bin": launch["codex_bin"], "codex_bin_sha256": facts.get("codex_bin_sha256"),
            "model": launch["model"], "effort": launch["effort"], "sandbox": launch["sandbox"],
            "network": launch["network"], "work_root": launch.get("work_root", "worktree"),
            "commit_mode": launch.get("commit_mode", "none"),
            "writable_dirs": list(launch["writable_dirs"]),
            "env_names": sorted(launch["env"]), "child_path": launch["env"]["PATH"],
            "output_schema_sha256": launch.get(OUTPUT_SCHEMA_FILE[1], "absent"),
            "codex_disabled_features": list(CODEX_DISABLED_FEATURES), "ignore_user_config": True,
            "ignore_rules": True, "skills_include_instructions": False, "persistent_mode": False, "exclude_slash_tmp": True,
            "exclude_tmpdir_env_var": False, "project_agents_md_sha256": facts.get("project_agents_md_sha256"),
            "user_codex_agents_md_sha256": facts.get("user_codex_agents_md_sha256"),
            "user_codex_hooks_sha256": facts.get("user_codex_hooks_sha256"),
            "zdotdir_sha256": facts.get("zdotdir_sha256"), "harness_sha256": components.get(harness)}


def qualification_findings(launch, manifest, components, ky_run, facts, context):
    """(findings, the receipt's binds or None, whether the receipt is the one the manifest records as PASS).
    Plan §7 KV-06: only a recorded PASS receipt that binds exactly this launch configuration, earned in the
    context the job runs in, qualifies it. Nothing is executed here."""
    path = os.path.join(ky_run, "QUALIFICATIONS", f"{launch['role']}-{launch['model']}.json")
    facts["qualification_path"] = path
    if not os.path.isfile(path):
        return [f"qualification: no receipt at {path}; role {launch['role']} with model {launch['model']} is not a "
                f"qualified launch configuration"], None, False
    try:
        receipt, facts["qualification_sha256"] = read_json_and_sha(path)
    except ValueError as bad:
        return [f"qualification: {bad}"], None, False
    if type(receipt) is not dict or receipt.get("schema") != QUALIFICATION_SCHEMA:
        return [f"qualification: {path} is not a {QUALIFICATION_SCHEMA} receipt"], None, False
    out = []
    engine = "codex" if is_codex(launch) else "claude"
    if receipt.get("engine", "claude") != engine:
        out.append(f"qualification: the receipt's engine {_show(receipt.get('engine', 'claude'))} is not the launch "
                   f"input's {engine!r}")
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
    listed = manifest.get("qualifications")
    recorded = [entry for entry in listed if type(entry) is dict and isinstance(entry.get("path"), str)
                and os.path.realpath(entry["path"]) == os.path.realpath(path)] if isinstance(listed, list) else []
    is_recorded = bool(recorded) and recorded[0].get("sha256") == facts["qualification_sha256"] \
        and recorded[0].get("result") == "PASS"
    if not recorded:
        out.append("qualification: the receipt is not recorded in the manifest")
    elif not is_recorded:
        out.append("qualification: the receipt is not the one the manifest records as PASS (its bytes or its "
                   "result changed after the manifest was built)")
    binds = receipt.get("binds")
    if type(binds) is not dict:
        return out + ["qualification: the receipt carries no binds"], None, False

    wanted = expected_codex_binds(launch, components, facts) if is_codex(launch) else \
        expected_binds(launch, components, facts)
    for name, want in wanted.items():
        if name not in binds:
            out.append(f"qualification: binds.{name} is missing")
        elif want is None:
            why = "kyqualify.py is not a component of the manifest" if name == "harness_sha256" \
                else "the launch's value was not observed"
            out.append(f"qualification: binds.{name} cannot be compared ({why})")
        elif not same_json(binds[name], want):
            out.append(f"qualification: binds.{name} {_show(binds[name])} does not bind this launch "
                       f"({_show(want)})")
    seconds = binds.get("deadline_seconds")
    if "deadline_seconds" not in binds:
        out.append("qualification: binds.deadline_seconds is missing")
    elif isinstance(seconds, bool) or not isinstance(seconds, int) or seconds <= 0:
        out.append(f"qualification: binds.deadline_seconds {_show(seconds)} is not a positive whole number of "
                   f"seconds")
    elif facts.get("deadline_epoch") is not None and facts["deadline_epoch"] > time.time() + seconds:
        out.append(f"deadline: {launch['deadline']} is later than now + the qualified deadline_seconds "
                   f"({seconds}); a job never runs longer than its configuration was qualified for")
    argv = binds.get("argv")
    if "argv" not in binds:
        out.append("qualification: binds.argv is missing")
    elif type(argv) is not list or not all(isinstance(element, str) for element in argv):
        out.append("qualification: binds.argv is not a list of strings")
    else:
        if is_codex(launch):
            mine = portable_codex_argv(build_launch(launch)["argv"], launch["worktree"], launch["job_scratch"])
            theirs = portable_codex_argv(argv, binds.get("worktree"))
        else:
            mine = portable_argv(build_launch(launch)["argv"], launch["worktree"])
            theirs = portable_argv(argv, binds.get("worktree"))
        if mine != theirs:
            where = next((i for i, pair in enumerate(zip(mine, theirs)) if pair[0] != pair[1]),
                         min(len(mine), len(theirs)))
            out.append(f"qualification: binds.argv is not this launch's line (same flags, same order): they differ at "
                       f"element {where}: qualified {_show(_flag_names(theirs[where:where + 1]))}, this launch "
                       f"{_show(_flag_names(mine[where:where + 1]))}")
    return out, binds, is_recorded


def check(launch_path, environ, manifest_path=None, context=None) -> Checked:
    """every precondition of a bootstrap launch. A refused supervisor or manifest gate stops the check: the
    launch input is then not examined and nothing it names is executed. Past the gate the findings are complete
    (never only the first) once the shape holds. `context` is the context the job will run in when that is not
    this process's own (submit passes "launchd")."""
    facts: dict = {"overrides": overrides_in_use(environ)}
    ky_run = environ.get("KY_RUN") or DEFAULT_KY_RUN
    facts["ky_run"] = ky_run
    if not os.path.isabs(ky_run) or os.path.normpath(ky_run) != ky_run:
        return Checked(None, [f"KY_RUN: {ky_run!r} is not a normalised absolute path"], facts)
    manifest_path = os.path.abspath(manifest_path) if manifest_path else os.path.join(ky_run, "VERSIONS.bootstrap.json")
    manifest, components, gate, schema_tool = manifest_gate(manifest_path, ky_run, environ, facts)
    if gate or manifest is None or schema_tool is None:
        return Checked(None, gate + ["launch input: not examined, and nothing it names was executed, because the "
                                     "supervisor or its manifest gate is refused"], facts)

    try:
        launch = read_json(launch_path)
    except ValueError as bad:
        return Checked(None, [f"launch input: {bad}"], facts, schema_tool)
    findings = list(_placeholders(launch))
    codex = is_codex(launch)
    shape = LAUNCH_SCHEMA_CODEX if codex else LAUNCH_SCHEMA
    try:
        findings += [f"schema: {_value_free(error)}"
                     for error in schema_tool.validate(load_schema(shape), launch)]
    except ValueError as refused:                    # an unreadable schema, or one kyschema refuses (SchemaError)
        return Checked(launch, [f"schema {shape} is refused: {refused}"], facts, schema_tool)
    if findings:
        return Checked(launch, findings, facts, schema_tool)      # the rules below read fields the shape guarantees
    detected, injected = detect_context(environ, launch["job_id"])
    facts["launch_context"] = context or detected
    facts["launch_context_parent_pid_injected"] = injected and context is None

    findings += job_id_findings(launch["job_id"])
    unsafe_paths = set()
    for field in path_fields(launch):
        value = launch[field]
        if not os.path.isabs(value):
            findings.append(f"{field}: not an absolute path: {value!r}")
            unsafe_paths.add(field)
        elif os.path.normpath(value) != value:
            findings.append(f"{field}: path is not normalised (no '..', '.', doubled or trailing slash): {value!r}")
            unsafe_paths.add(field)
    scratch, root, overridden = resolve_scratch(environ, findings)
    facts["scratch_root"], facts["scratch_root_override"], facts["ky_scratch"] = root, overridden, scratch
    environment = env_findings(launch, ky_run, scratch)
    findings += environment
    if not codex:                                    # a Codex launch line has no extra flag at all
        findings += flag_findings(launch["extra_lean_flags"])

    expected_effort = "xhigh" if launch["kind"] == "PLAN" else "high"
    if launch["effort"] != expected_effort:
        findings.append(f"effort: kind {launch['kind']} requires effort {expected_effort}, found {launch['effort']}")
    cap = TURN_CAPS[launch["kind"]]
    if not codex and launch["max_turns"] > cap:      # Codex has no turn limit: its deadline is the only one
        findings.append(f"max_turns: {launch['max_turns']} exceeds the cap {cap} for kind {launch['kind']}")

    deadline = parse_utc(launch["deadline"])
    if deadline is None:
        findings.append(f"deadline: not a UTC ISO-8601 timestamp (…Z or …+00:00): {launch['deadline']!r}")
    elif deadline <= time.time():
        findings.append(f"deadline: {launch['deadline']} is not in the future")
    facts["deadline_epoch"] = deadline

    if unsafe_paths:
        return Checked(launch, findings, facts, schema_tool)      # never probe the filesystem through a relative path
    findings += _location_findings(launch, ky_run, scratch)
    findings += worktree_policy_findings(launch, environ)
    findings += _git_findings(launch, environ, facts)
    findings += _file_findings(launch)
    findings += binding_findings(launch, manifest, components, facts)
    program = _program_findings(launch, facts)       # the file and its hash; nothing is executed yet
    findings += program
    if codex:
        findings += _codex_findings(launch, environ, facts)
    field = program_field(launch)
    if environment:
        findings += [f"{field}: --version was not run because the job environment is refused",
                     "qualification: not compared because the job environment is refused"]
        return Checked(launch, findings, facts, schema_tool)
    facts["project_settings_sha256"] = project_settings_digest(launch["worktree"])
    facts["zdotdir_sha256"] = zdotdir_digest(os.path.join(launch["env"]["KY_ROOT"], "zdotdir"))
    if codex:                                        # the instruction and hook inputs Codex may still read
        home = launch["env"].get("HOME") or ""
        facts["project_agents_md_sha256"] = file_digest(os.path.join(launch["worktree"], "AGENTS.md"))
        facts["user_codex_agents_md_sha256"] = file_digest(os.path.join(home, ".codex", "AGENTS.md"))
        facts["user_codex_hooks_sha256"] = file_digest(os.path.join(home, ".codex", "hooks.json"))
    found, binds, recorded = qualification_findings(launch, manifest, components, ky_run, facts,
                                                    facts["launch_context"])
    findings += found
    if not program:
        if recorded and binds.get(field) == launch[field] \
                and binds.get(f"{field}_sha256") == facts[f"{field}_sha256"]:
            findings += _codex_version_findings(launch, facts, binds) if codex else \
                _version_findings(launch, facts, binds)
        else:
            findings.append(f"{field}: --version was not run because the program is not the one a recorded PASS "
                            "receipt binds (path and sha256 are compared before anything is executed)")
    return Checked(launch, findings, facts, schema_tool)


# --------------------------------------------------------------------------------------------------------------
# argv
# --------------------------------------------------------------------------------------------------------------
def build_codex_launch(launch) -> dict:
    """the Codex launch line for a checked launch input — kyqualify.py's build_codex_argv with the job folder
    filled in; a pure function of the launch input. The prompt is stdin (`-`)."""
    job = launch["job_scratch"]
    rooted = job_rooted(launch)
    argv = [launch["codex_bin"], "exec", "--ignore-user-config", "--ignore-rules", "--json"]
    if rooted:
        argv.append("--skip-git-repo-check")
    argv += ["-o", job + "/" + FINAL_MESSAGE, "-C", job if rooted else launch["worktree"], "-s", launch["sandbox"],
             "-m", launch["model"],
            "-c", f'model_reasoning_effort="{launch["effort"]}"', "-c", 'approval_policy="never"',
            "-c", 'web_search="disabled"',
            "-c", "sandbox_workspace_write.network_access=" + ("true" if launch["network"] is True else "false"),
            "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
            "-c", "skills.include_instructions=false"]
    for feature in CODEX_DISABLED_FEATURES:
        argv += ["--disable", feature]
    for directory in launch["writable_dirs"]:
        argv += ["--add-dir", directory]
    if launch["sandbox"] == "workspace-write" and not rooted:
        argv += ["--add-dir", job]
    if launch.get("output_schema"):
        argv += ["--output-schema", launch["output_schema"]]
    return {"cwd": job if rooted else launch["worktree"], "env": clean_env(launch), "argv": argv + ["-"]}


def build_launch(launch) -> dict:
    """the plan §7 launch line for a checked launch input; a pure function of the launch input"""
    if is_codex(launch):
        return build_codex_launch(launch)
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
        except (ValueError, UnicodeDecodeError, RecursionError):
            continue
        if isinstance(event, dict):
            yield event


def first_session_id(path, limit=None):
    """the session_id of the first stream event that carries one; None when none does (never invented)"""
    for event in _events(path, limit):
        if isinstance(event.get("session_id"), str) and event["session_id"]:
            return event["session_id"]
    return None


def first_thread_id(path, limit=None):
    """Codex: the thread_id of the stream's thread.started event; None when there is none (never invented)"""
    for event in _events(path, limit):
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str) and event["thread_id"]:
            return event["thread_id"]
    return None


def final_codex_turn(path):
    """Codex: type / usage / error of the last turn.completed or turn.failed event, or None when there is none"""
    last = None
    for event in _events(path):
        if event.get("type") in ("turn.completed", "turn.failed"):
            last = event
    if last is None:
        return None
    error = last.get("error")
    return {"type": last.get("type"), "usage": last.get("usage"),
            "error": (error.get("message") if isinstance(error, dict) else error)}


def final_result_event(path):
    """subtype / is_error / num_turns / usage of the last `type: "result"` event, or None when there is none"""
    last = None
    for event in _events(path):
        if event.get("type") == "result":
            last = event
    if last is None:
        return None
    return {key: last.get(key) for key in ("subtype", "is_error", "num_turns", "usage")}


def job_result(launch, schema_tool):
    """(valid, errors, detail) for <job_scratch>/result.json, the job's own report (cockpit ruling R1).
    A job that ends without it is not a success: (False, […], "no_result"). The file must be a regular file of
    the job's own: a symbolic link, or anything else that is not a regular file, is refused and never read
    (detail "result_refused"). A file that is read is strict JSON, schema-valid and names this job and item."""
    path = os.path.join(launch["job_scratch"], "result.json")
    if is_codex(launch) and launch.get("output_schema") and not os.path.lexists(path):
        # a Codex job whose final message has a declared shape (a read-only reviewer cannot write result.json):
        # its -o file is judged by exactly the rules of result.json
        final = os.path.join(launch["job_scratch"], FINAL_MESSAGE)
        if os.path.lexists(final):
            return _judge_result_file(launch, schema_tool, final, FINAL_MESSAGE)
        return False, ["result.json is missing, and so is final_message.txt: the job ended without leaving its "
                       "result"], "no_result"
    return _judge_result_file(launch, schema_tool, path, "result.json")


def _judge_result_file(launch, schema_tool, path, name):
    """(valid, errors, detail) for one result file named `name` (job_result's rules)"""
    try:
        found = os.lstat(path)
    except FileNotFoundError:
        return False, [f"{name} is missing: the job ended without leaving its result"], "no_result"
    except OSError as failed:
        return False, [f"{name} cannot be examined: {failed}"], "result_refused"
    if stat.S_ISLNK(found.st_mode):
        return False, [f"{name} is a symbolic link: it is refused and was not read"], "result_refused"
    if not stat.S_ISREG(found.st_mode):
        return False, [f"{name} is not a regular file: it is refused and was not read"], "result_refused"
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                return False, [f"{name} is not a regular file: it is refused and was not read"], "result_refused"
            data = handle.read(RESULT_MAX_BYTES + 1)
    except OSError as failed:
        return False, [f"{name} cannot be read: {failed}"], "result_refused"
    if len(data) > RESULT_MAX_BYTES:
        return False, [f"{name} is larger than {RESULT_MAX_BYTES} bytes: it is refused"], "result_refused"
    try:
        result = load_json_text(data.decode("utf-8"))
        errors = schema_tool.validate(load_schema(RESULT_SCHEMA_LAUNCHER if launcher_commit(launch) else "job_result"),
                                      result)
    except (ValueError, UnicodeDecodeError, RecursionError) as bad:
        return False, [f"{path} is not acceptable JSON: {bad}"[:400]], None
    if not errors:
        for field in ("job_id", "item"):
            if result[field] != launch[field]:
                errors.append(f"$.{field}: {result[field]!r} is not this job's {field} {launch[field]!r}")
    return not errors, errors[:10], None


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


def recorded_group_state(pgid) -> str:
    """`group_state` of a process group id read from a record · 'unknown' when the record does not hold the id
    of a group that could be a job's (not a whole number above 1): an unidentified group is never 'gone'"""
    if isinstance(pgid, bool) or not isinstance(pgid, int) or pgid <= 1:
        return "unknown"
    try:
        return group_state(pgid)
    except OSError:
        return "unknown"


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
    """The one liveness rule of every fleet tool (cockpit ruling R2).
    True: alive with this start identity · False: POSITIVELY gone (ps reports no such process, an uncollected
    exit, or another process under a reused id) · None: unknown (ps cannot be asked or times out, the id is
    missing or not a positive whole number, the start identity cannot be compared). Unknown is never gone."""
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


def job_gone(pid, start, pgid) -> bool:
    """True only when a recorded job is POSITIVELY gone: its leader is (`process_matches` → False) AND no member
    of its process group answers (`killpg(pgid, 0)` → ESRCH). A live leader, a surviving member, a group that
    cannot be asked and an identity that cannot be read are all 'not gone' (cockpit ruling R2)."""
    return process_matches(pid, start) is False and recorded_group_state(pgid) == "gone"


# --------------------------------------------------------------------------------------------------------------
# the item lock (plan §14 B-0c "its own proven instance lock"; cockpit ruling R2) and the action record (§4a.1)
# --------------------------------------------------------------------------------------------------------------
class LockLost(OSError):
    """the item lock is no longer this run's: whatever it guarded must stop"""


class _FolderGuard:
    """an exclusive flock on the locks folder itself (no file is created): one kyboot acquisition at a time
    looks, judges, renames and installs. Released on exit — and by the system if this process dies."""

    def __init__(self, folder, wait):
        self.folder, self.wait, self.descriptor = folder, wait, None

    def __enter__(self):
        self.descriptor = os.open(self.folder, os.O_RDONLY)
        limit = time.monotonic() + self.wait
        while True:
            try:
                fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError as busy:
                if busy.errno not in (errno.EWOULDBLOCK, errno.EAGAIN) or time.monotonic() >= limit:
                    os.close(self.descriptor)
                    raise
            time.sleep(POLL_SECONDS)

    def __exit__(self, *_exc):
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)
        return False


def lock_folder_guard(folder):
    return _FolderGuard(folder, LOCK_GUARD_WAIT_SECONDS)


def item_lock_path(ky_run, item) -> str:
    return os.path.join(ky_run, "locks", f"kyboot.{item}")


def read_lock_owner(lock):
    """owner.json of a lock directory as a dict, or None when it is missing or not readable as one"""
    try:
        owner = read_json(os.path.join(lock, "owner.json"))
    except ValueError:
        return None
    return owner if type(owner) is dict else None


def _is_mine(owner, run_id) -> bool:
    return type(owner) is dict and owner.get("session_or_run_id") == run_id and owner.get("pid") == os.getpid()


def _remove_lock_directory(path) -> bool:
    """remove a directory this process owns outright (a private new lock, a verified grave) and what is in it"""
    try:
        for name in os.listdir(path):
            os.unlink(os.path.join(path, name))
        os.rmdir(path)
    except OSError:
        return False
    return True


def judge_lock(lock, item):
    """("stale", owner): the recorded owner and the job it recorded are positively gone — the lock may be taken
    over · ("held", reason): anything else, never taken over · ("vanished", None): it went away while it was
    read (look again)."""
    owner = read_lock_owner(lock)
    if owner is None:
        if not os.path.lexists(lock):
            return "vanished", None
        return "held", (f"item lock: {lock} exists and its owner is not recorded or not readable; an unknown "
                        f"owner is never taken over")
    alive = process_matches(owner.get("pid"), owner.get("process_start"))
    if alive is True:
        return "held", (f"item lock: item {item} is held by a live supervisor "
                        f"({owner.get('session_or_run_id')}, pid {owner.get('pid')})")
    if alive is None:
        return "held", (f"item lock: the owner of {lock} (pid {owner.get('pid')}) cannot be confirmed gone; an "
                        f"unknown owner is never taken over")
    if "child" not in owner:
        why = "its record does not say whether it started a job (no child field)"
    elif owner["child"] is None:
        return "stale", owner
    elif owner["child"] == CHILD_PENDING:
        why = "it was about to start a job and never recorded which (child: pending)"
    elif type(owner["child"]) is dict:
        child = owner["child"]
        if job_gone(child.get("pid"), child.get("process_start"), child.get("pgid")):
            return "stale", owner
        why = "the job it recorded is alive or cannot be confirmed gone"
    else:
        why = "the job it recorded cannot be identified"
    return "held", (f"item lock: the previous supervisor of item {item} is gone but {why}; reconcile that job "
                    f"before any new launch (the lock is never taken over)")


def bury_stale_lock(lock, owner):
    """Take a lock that was judged stale out of the way — verify-after-rename (cockpit ruling R2).
    (True, None): it is gone · (False, None): it had moved already (look again) · (False, reason): refuse.
    The lock is renamed to a grave and the grave's owner.json is read again: only if it is exactly the owner
    that was judged gone is the grave removed. If another contender installed its own lock in the instant
    between the judgment and the rename, that lock is what was moved: it is put back untouched."""
    grave = f"{lock}.stale.{os.getpid()}.{os.urandom(4).hex()}"
    try:
        os.rename(lock, grave)
    except OSError:
        return False, None
    found = read_lock_owner(grave)
    if found is not None and same_json(found, owner):
        _remove_lock_directory(grave)
        return True, None
    holder = found.get("session_or_run_id") if found is not None else "an unreadable owner"
    try:
        os.rename(grave, lock)
    except OSError as failed:
        return False, (f"item lock: {lock} changed owner while it was being judged (now {holder}) and could not be "
                       f"put back ({failed}); it is kept untouched at {grave} for a person to reconcile")
    return False, (f"item lock: {lock} changed owner while it was being judged (now {holder}); it was put back "
                   f"untouched and is not taken over")


def acquire_item_lock(ky_run, item, run_id):
    """(lock directory, None, taken-over owner or None) · (None, reason, None). One live supervisor per item.
    The lock appears complete — a directory holding this run's owner.json, renamed into place — or not at all;
    an existing lock is taken over only when `judge_lock` finds it stale, and then by `bury_stale_lock`."""
    lock = item_lock_path(ky_run, item)
    folder = os.path.dirname(lock)
    try:
        os.makedirs(folder, exist_ok=True)
        with lock_folder_guard(folder):
            return _acquire(lock, item, run_id)
    except OSError as failed:
        return None, f"item lock: {lock} could not be taken: {failed}", None


def _acquire(lock, item, run_id):
    record = {"session_or_run_id": run_id, "pid": os.getpid(), "pgid": os.getpgrp(),
              "process_start": process_start(os.getpid()), "acquired_at": utc_now_text(), "child": None}
    if not record["process_start"]:
        return None, ("item lock: this supervisor's own start identity cannot be read (ps); a lock whose owner "
                      "could never be judged is not written"), None
    mine = f"{lock}.new.{os.getpid()}.{os.urandom(4).hex()}"
    taken_over = None
    os.mkdir(mine)
    try:
        write_state(os.path.join(mine, "owner.json"), record)
        for _ in range(LOCK_ATTEMPTS):
            if not os.path.lexists(lock):
                try:
                    os.rename(mine, lock)                 # atomic: the lock exists with its owner, or not at all
                except OSError:
                    continue                              # another contender's lock appeared first: judge it
                mine = None
                return lock, None, taken_over
            verdict, detail = judge_lock(lock, item)
            if verdict == "held":
                return None, detail, None
            if verdict == "stale":
                buried, reason = bury_stale_lock(lock, detail)
                if reason is not None:
                    return None, reason, None
                if buried:
                    taken_over = detail
        return None, f"item lock: lost the race for {lock} to another contender", None
    finally:
        if mine is not None:
            _remove_lock_directory(mine)


def write_lock_owner(lock, run_id, child):
    """record in this run's lock what it knows of its job: "pending" just before the job is started, its
    identity once it runs. LockLost when the lock is not (or no longer) this run's — never written then."""
    owner = read_lock_owner(lock)
    if not _is_mine(owner, run_id):
        raise LockLost(f"the item lock {lock} is not held by this run ({run_id}) any more")
    write_state(os.path.join(lock, "owner.json"), dict(owner, child=child))


def release_item_lock(lock, run_id) -> bool:
    """remove the lock if, and only if, this run still owns it — by the takeover's own rule: rename it away,
    read the owner again, remove it only if it is this run's, otherwise put it back"""
    if not _is_mine(read_lock_owner(lock), run_id):
        return False
    grave = f"{lock}.released.{os.getpid()}.{os.urandom(4).hex()}"
    try:
        os.rename(lock, grave)
    except OSError:
        return False
    if _is_mine(read_lock_owner(grave), run_id):
        return _remove_lock_directory(grave)
    try:
        os.rename(grave, lock)
    except OSError:
        pass
    return False


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


def supervise(proc, pgid, deadline_epoch, grace, stdout_path, on_session, stop, reader=None):
    """wait for exit, the deadline or a signal to the supervisor; always leaves the process group ended.
    `reader` finds the provider session id in the stream (first_session_id; a Codex job: first_thread_id)."""
    reader = reader or first_session_id
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
            session = reader(stdout_path, SESSION_SCAN_BYTES)
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


def _record(state_path, state) -> bool:
    """write state.json; a failure is said on stderr and answered, never raised (the caller is past the point
    where an error may interrupt it)"""
    try:
        write_state(state_path, state)
    except Exception as failed:
        print(f"STATE NOT WRITTEN {state_path}: {type(failed).__name__}: {failed}", file=sys.stderr)
        return False
    return True


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
    outputs = (("stdout_path", launch["stdout_path"]), ("stderr_path", launch["stderr_path"]),
               ("result.json", result_path))
    if is_codex(launch):
        outputs += ((FINAL_MESSAGE, os.path.join(scratch, FINAL_MESSAGE)),)
    for label, path in outputs:
        if os.path.lexists(path):
            occupied.append(f"{label}: {path} already exists (a job never overwrites an earlier run's output)")
    if occupied:
        _refuse(launch_path, occupied)
        return EXIT_REFUSED

    guards = None
    if is_codex(launch):                             # what the job must leave as it was (cockpit rulings E1, E2)
        guards = {"before": codex_guards(launch, environ), "after": None}
        unseen = sorted(name for name, value in guards["before"].items() if value is None)
        if unseen:
            _refuse(launch_path, [f"guards: git cannot read {', '.join(unseen)} before the job, so a change could "
                                  f"not be detected after it"])
            return EXIT_REFUSED
    run_id = f"kyboot-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    lock, held, taken_over = acquire_item_lock(ky_run, launch["item"], run_id)
    if lock is None:
        _refuse(launch_path, [held])
        return EXIT_REFUSED
    keep_lock = False
    try:
        try:
            launch_sha = sha256_file(launch_path)
            action = begin_action(act_path, launch, run_id, {
                "launch_input_path": os.path.abspath(launch_path), "launch_input_sha256": launch_sha,
                "manifest_sha256": facts.get("manifest_sha256"), "supervisor_sha256": facts.get("supervisor_sha256"),
                "qualification_sha256": facts.get("qualification_sha256"), "prompt_sha256": launch["prompt_sha256"],
                "card_sha256": launch["card_sha256"], "packet_sha256": launch["packet_sha256"],
                "argv": plan["argv"], "overrides": facts["overrides"]})
        except FileExistsError:
            _refuse(launch_path, [f"action: {act_path} already exists; a launch of job {launch['job_id']} was "
                                  f"already intended (reconcile it, never repeat it)"])
            return EXIT_REFUSED
        except OSError as failed:
            _refuse(launch_path, [f"action: the intent could not be recorded at {act_path}: {failed}"])
            return EXIT_REFUSED
        state = {
            "schema": STATE_SCHEMA, "phase": "prepared",
            "job_id": launch["job_id"], "item": launch["item"], "kind": launch["kind"], "role": launch["role"],
            "worktree": launch["worktree"], "branch": launch["branch"], "base_sha": launch["base_sha"],
            "worktree_head": facts.get("worktree_head"),
            "job_scratch": scratch, "prompt_path": launch["prompt_path"], "stdout_path": launch["stdout_path"],
            "stderr_path": launch["stderr_path"], "tmp_path": launch["tmp_path"], "state_path": state_path,
            "prompt_sha256": launch["prompt_sha256"], "card_path": launch["card_path"],
            "card_sha256": launch["card_sha256"], "packet_path": launch["packet_path"],
            "packet_sha256": launch["packet_sha256"],
            "model": launch["model"], "effort": launch["effort"], "permission_mode": launch.get("permission_mode"),
            "max_turns": launch.get("max_turns"), "deadline": launch["deadline"], "grace_seconds": grace,
            "claude_bin": launch.get("claude_bin"), "claude_bin_realpath": facts.get("claude_bin_realpath"),
            "claude_bin_sha256": facts.get("claude_bin_sha256"), "claude_version": facts.get("claude_version"),
            "launch_input_path": os.path.abspath(launch_path), "launch_input_sha256": launch_sha,
            "argv": plan["argv"], "plan_version": launch["plan_version"],
            "approved_source_commit": launch["approved_source_commit"],
            "supervisor_path": facts.get("supervisor_path"), "supervisor_sha256": facts.get("supervisor_sha256"),
            "python_isolated": facts.get("python_isolated"),
            "source_repo": facts.get("source_repo"), "manifest_path": facts.get("manifest_path"),
            "manifest_sha256": facts.get("manifest_sha256"),
            "manifest_file_sha256": facts.get("manifest_file_sha256"),
            "qualification_path": facts.get("qualification_path"),
            "qualification_sha256": facts.get("qualification_sha256"),
            "project_settings_sha256": facts.get("project_settings_sha256"),
            "zdotdir_sha256": facts.get("zdotdir_sha256"),
            "scratch_root": facts.get("scratch_root"), "scratch_root_override": facts.get("scratch_root_override"),
            "overrides": facts["overrides"],
            "supervisor_pid": os.getpid(), "supervisor_process_start": process_start(os.getpid()),
            "supervisor_run_id": run_id, "lock_path": lock,
            "launch_context": facts.get("launch_context"),
            "launch_context_parent_pid_injected": facts.get("launch_context_parent_pid_injected"),
            "label": job_label(launch["job_id"]) if facts.get("launch_context") == "launchd" else None,
            "lock_taken_over_from": taken_over, "action_path": act_path,
            "started_at": None, "pid": None, "pgid": None, "process_start": None, "provider_session_id": None,
            "ended_at": None, "exit_code": None, "exit_signal": None, "termination": None,
            "termination_detail": None, "leftover_group": None,
            "group_gone": None, "result_event": None, "job_result_valid": None, "job_result_errors": [],
        }
        if is_codex(launch):                        # the second engine's own program and sandbox facts
            for name in ("permission_mode", "max_turns", "claude_bin", "claude_bin_realpath", "claude_bin_sha256",
                         "claude_version"):
                state.pop(name)
            state.update(engine="codex", codex_bin=launch["codex_bin"],
                         codex_bin_realpath=facts.get("codex_bin_realpath"),
                         codex_bin_sha256=facts.get("codex_bin_sha256"), codex_version=facts.get("codex_version"),
                         sandbox=launch["sandbox"], network=launch["network"],
                         writable_dirs=list(launch["writable_dirs"]), git_common_dir=facts.get("git_common_dir"),
                         final_message_path=os.path.join(scratch, FINAL_MESSAGE), result_source=None,
                         work_root=launch.get("work_root", "worktree"), guards=guards, guard_failures=[],
                         commit_mode=launch.get("commit_mode", "none"), awaiting_launcher_commit=False)
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            write_state(state_path, state, exclusive=True)
        except OSError as failed:
            exists = isinstance(failed, FileExistsError)
            reason = "state.json already exists" if exists else f"state.json could not be written: {failed}"
            try:
                complete_action(act_path, action, False, {"phase": "refused", "reason": reason})
            except OSError:
                pass
            _refuse(launch_path, [f"state_path: {state_path} already exists for job {launch['job_id']} "
                                  f"(no silent re-run)" if exists else f"state_path: {reason}"])
            return EXIT_REFUSED

        # from here on a process may exist: nothing below answers 1, and nothing below raises past the job
        code, started = _launch_and_supervise(launch, plan, facts, state, grace, lock, run_id, checked.schema_tool)
        if guards is not None and state["phase"] == "ended":
            code = _check_guards(launch, environ, state, code)
        launched = state["phase"] == "ended"
        keep_lock = launched and state["group_gone"] is not True    # a job that may still be alive stays locked
        done = launched and state["group_gone"] is True and state["job_result_valid"] is True \
            and not state.get("supervisor_error") and not state.get("guard_failures")
        try:
            complete_action(act_path, action, done, {
                "phase": state["phase"], "termination": state["termination"],
                "termination_detail": state["termination_detail"], "exit_code": state["exit_code"],
                "exit_signal": state["exit_signal"], "group_gone": state["group_gone"], "pid": state["pid"],
                "pgid": state["pgid"], "process_start": state["process_start"],
                "job_result_valid": state["job_result_valid"], "launch_error": state.get("launch_error"),
                "supervisor_error": state.get("supervisor_error"), "state_path": state_path,
                "supervisor_exit": code, **({"guard_failures": state["guard_failures"]} if guards else {})})
        except Exception as failed:
            print(f"ACTION NOT COMPLETED {act_path}: {type(failed).__name__}: {failed} (it may still say INTENDED; "
                  f"state.json and this exit status say what happened)", file=sys.stderr)
            if started and code == EXIT_OK:
                code = EXIT_JOB_FAILED
        try:
            report(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=1))
        except Exception as failed:
            print(f"STATE NOT REPORTED: {type(failed).__name__}: {failed}", file=sys.stderr)
        return code
    finally:
        if not keep_lock and not release_item_lock(lock, run_id):
            print(f"item lock: {lock} was not released by this run (it is not this run's any more, or it could "
                  f"not be removed)", file=sys.stderr)


def _result_status(launch):
    """the status the job's own result.json states, or None (read only after job_result found the file valid)"""
    try:
        with open(os.path.join(launch["job_scratch"], "result.json"), "rb") as handle:
            result = load_json_text(handle.read(RESULT_MAX_BYTES).decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, RecursionError):
        return None
    return result.get("status") if type(result) is dict else None


def _check_guards(launch, environ, state, code) -> int:
    """After a Codex job, fail on owned git / hooks or item changes; report shared configuration churn."""
    before = state["guards"]["before"]

    def differences():
        after = codex_guards(launch, environ)
        found = []
        for name in sorted(before):
            if after.get(name) is None:
                found.append(f"{name}: cannot be read after the job")
            elif name == "git":
                changes = git_guard_changes(before[name], after[name])
                if changes:
                    found.append("git: the git configuration, hooks or git-directory identity changed during the "
                                 f"job ({', '.join(changes)})")
            elif after[name] != before[name]:
                found.append(f"{name}: the item's working copy (HEAD or git status) changed during the job")
        return after, found

    after, failures = differences()
    if failures:                                     # once more, to rule out a file read while it was being written
        time.sleep(GUARD_RETRY_SECONDS)
        after, failures = differences()
    state["guards"]["after"] = after
    state["guards"].update(git_shared_report(before.get("git"), after.get("git")))
    state["guard_failures"] = failures
    if launcher_commit(launch):                      # kyboot never commits or pushes: the launcher does, afterwards
        state["awaiting_launcher_commit"] = bool(state["job_result_valid"] is True and not failures
                                                 and _result_status(launch) == "done")
    _record(state["state_path"], state)
    if failures:
        print(f"GUARD FAILED {launch['job_id']}: " + "; ".join(failures), file=sys.stderr)
        if code == EXIT_OK:
            return EXIT_JOB_FAILED
    return code


def _launch_and_supervise(launch, plan, facts, state, grace, lock, run_id, schema_tool):
    """(exit status, whether a process was started). Start the job in a session of its own, supervise it, and
    leave the final record in `state` and on disk. Once the process exists this function does not raise: every
    step after the start runs inside one guard that ends the process group and records why."""
    state_path, scratch = launch["state_path"], launch["job_scratch"]
    stop = {"signal": None}
    previous = {}
    proc = None
    early = None

    def restore_signals():
        for signum, handler in list(previous.items()):
            try:
                signal.signal(signum, handler)
            except (OSError, ValueError):
                pass
        previous.clear()

    try:
        os.makedirs(scratch, exist_ok=True)
        os.makedirs(launch["tmp_path"], exist_ok=True)
        with open(launch["prompt_path"], "rb") as stdin, open(launch["stdout_path"], "xb") as stdout, \
                open(launch["stderr_path"], "xb") as stderr:
            digest = hashlib.sha256(stdin.read()).hexdigest()   # the bytes the job will read, re-hashed on
            if digest != launch["prompt_sha256"]:               # the very descriptor it inherits
                raise OSError(f"prompt_path changed after check: sha256 is now {digest}")
            stdin.seek(0)
            # BEFORE the job's process exists the lock says a job is pending: a supervisor that dies from here on —
            # before it could record which process it started — leaves a lock that is never taken over (ruling R2)
            write_lock_owner(lock, run_id, CHILD_PENDING)
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                previous[signum] = signal.signal(signum, lambda number, _frame: stop.update(signal=number))
            proc = subprocess.Popen(plan["argv"], cwd=plan["cwd"], env=plan["env"], stdin=stdin, stdout=stdout,
                                    stderr=stderr, start_new_session=True, close_fds=True)
    except (OSError, ValueError, subprocess.SubprocessError) as failed:
        if proc is None:                            # nothing was started
            restore_signals()
            try:
                write_lock_owner(lock, run_id, None)            # the marker is withdrawn: there is no job
            except OSError:
                pass
            state.update(phase="launch_failed", ended_at=utc_now_text(), launch_error=str(failed))
            _record(state_path, state)
            print(f"NOT LAUNCHED {launch['job_id']}: {failed}", file=sys.stderr)
            return EXIT_JOB_FAILED, False
        early = failed                              # the process exists: only the guard below may deal with it

    pgid, leads, outcome = None, False, None
    try:
        try:
            pgid = os.getpgid(proc.pid)
        except OSError:
            pgid = proc.pid                         # start_new_session: the child leads its own group
        leads = pgid == proc.pid and pgid != os.getpgrp()
        if early is not None:
            raise early
        if not leads:
            # the job must lead a group of its own: signalling any other group would reach the supervisor,
            # its parents or strangers. End the one process we started, by pid, and record why.
            proc.kill()
            proc.wait()
            state.update(phase="launch_failed", started_at=utc_now_text(), ended_at=utc_now_text(), pid=proc.pid,
                         pgid=pgid,
                         launch_error=f"the job is not the leader of its own process group "
                                      f"(pid {proc.pid}, pgid {pgid}); it was killed by pid")
        else:
            state.update(phase="running", started_at=utc_now_text(), pid=proc.pid, pgid=pgid)
            write_state(state_path, state)              # the identity first; the start time needs another process
            state["process_start"] = process_start(proc.pid)
            write_state(state_path, state)
            write_lock_owner(lock, run_id, {"job_id": launch["job_id"], "pid": proc.pid, "pgid": pgid,
                                            "process_start": state["process_start"]})

            def on_session(session_id):
                state["provider_session_id"] = session_id
                write_state(state_path, state)

            outcome = supervise(proc, pgid, facts["deadline_epoch"], grace, launch["stdout_path"], on_session, stop,
                                first_thread_id if is_codex(launch) else first_session_id)
    except BaseException as crashed:                # a full disk, a removed state folder, a lost lock, a bug:
        if leads:                                   # whatever it was, the job never runs on unsupervised
            how = end_group(proc, pgid, grace)
            ended = _exit_facts(proc, pgid)
        else:
            how = "kill"
            try:
                proc.kill()
                proc.wait(timeout=KILL_CONFIRM_SECONDS)
            except (OSError, subprocess.SubprocessError):
                pass
            ended = {"exit_code": None, "exit_signal": None, "group_gone": proc.poll() is not None}
        outcome = dict({"termination": f"supervisor_error_{how}", "leftover_group": "none"}, **ended)
        state.update(pid=proc.pid, pgid=pgid, started_at=state["started_at"] or utc_now_text(),
                     supervisor_error=f"{type(crashed).__name__}: {crashed}")
    finally:
        restore_signals()

    if outcome is None:                             # the one process was not a group leader: killed, never supervised
        _record(state_path, state)
        print(f"NOT LAUNCHED {launch['job_id']}: {state['launch_error']}", file=sys.stderr)
        return EXIT_JOB_FAILED, True

    # the process group has been ended, or is reported as not confirmed gone: what follows only records
    state.update(outcome)
    if stop["signal"] is not None:
        state["supervisor_signal"] = int(stop["signal"])
    try:
        valid, errors, detail = job_result(launch, schema_tool)
    except Exception as failed:
        valid, errors, detail = False, [f"result.json could not be judged: {type(failed).__name__}: {failed}"], None
    try:
        if is_codex(launch):
            session = state["provider_session_id"] or first_thread_id(launch["stdout_path"])
            event = final_codex_turn(launch["stdout_path"])
            state["result_source"] = None if detail == "no_result" else (
                "result.json" if os.path.lexists(os.path.join(scratch, "result.json")) else FINAL_MESSAGE)
        else:
            session = state["provider_session_id"] or first_session_id(launch["stdout_path"])
            event = final_result_event(launch["stdout_path"])
    except Exception:
        session, event = state["provider_session_id"], None
    state.update(phase="ended", ended_at=utc_now_text(), provider_session_id=session, result_event=event,
                 job_result_valid=valid, job_result_errors=errors, termination_detail=detail)
    recorded = _record(state_path, state)
    job = launch["job_id"]
    if not state["group_gone"]:
        print(f"PROCESS GROUP {state['pgid']} NOT CONFIRMED GONE", file=sys.stderr)
        return EXIT_GROUP_SURVIVED, True
    if state["termination"].startswith("timed_out"):
        return EXIT_TIMED_OUT, True
    if state["termination"].startswith("interrupted"):
        return EXIT_INTERRUPTED, True
    if state.get("supervisor_error"):
        print(f"SUPERVISOR ERROR {job}: {state['supervisor_error']} (the job's process group was ended)",
              file=sys.stderr)
        return EXIT_JOB_FAILED, True
    if detail == "no_result":
        print(f"NO RESULT {job}: the job ended without leaving {os.path.join(scratch, 'result.json')}",
              file=sys.stderr)
        return EXIT_NO_RESULT, True
    if state["exit_code"] != 0 or valid is not True or not recorded:
        return EXIT_JOB_FAILED, True
    return EXIT_OK, True


# --------------------------------------------------------------------------------------------------------------
# submit / status / reap: the job as a one-shot launchd user agent, so that it outlives the session that sent it
# --------------------------------------------------------------------------------------------------------------
def launchctl_program(environ) -> str:
    return environ.get("KY_LAUNCHCTL") or DEFAULT_LAUNCHCTL


def launchctl_environment(environ) -> dict:
    """the whole environment launchctl is given: a fixed PATH and this user's HOME and USER, never the caller's"""
    me = pwd.getpwuid(os.getuid())
    home = environ.get("HOME") or ""
    return {"PATH": LAUNCHCTL_PATH, "HOME": home if os.path.isabs(home) else me.pw_dir,
            "USER": environ.get("USER") or me.pw_name, "LANG": "en_US.UTF-8"}


def launchctl(environ, *args):
    """(exit status, stdout, stderr) of ${KY_LAUNCHCTL:-/bin/launchctl} <args>; 127 when it was not run.
    The program is never looked up on PATH: a name that is not an absolute path is not run at all. With the
    tests-only KY_SCRATCH_ROOT_OVERRIDE set, a program that does not lie beneath that root is not run either —
    a test run can never reach the real launchd."""
    program = launchctl_program(environ)
    if not os.path.isabs(program):
        return 127, "", f"KY_LAUNCHCTL {program!r} is not an absolute path; it was not run"
    testing = environ.get("KY_SCRATCH_ROOT_OVERRIDE")
    if testing is not None and not (os.path.isabs(testing)
                                    and _is_beneath(os.path.normpath(program), os.path.normpath(testing))):
        return 127, "", (f"KY_SCRATCH_ROOT_OVERRIDE is set (a test run): {program} is not beneath that root; it "
                         f"was not run")
    try:
        done = subprocess.run([program, *args], capture_output=True, text=True, env=launchctl_environment(environ),
                              timeout=120, stdin=subprocess.DEVNULL)
    except (OSError, KeyError, subprocess.SubprocessError) as failed:
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
    """the one-shot agent: RunAtLoad, never KeepAlive, running this very file's `run` on the same launch input
    in an isolated interpreter (-I: no script folder, no user site, no PYTHON* variable; -B: no compiled cache)"""
    scratch = launch["job_scratch"]
    return {"Label": job_label(launch["job_id"]),
            "ProgramArguments": [sys.executable, "-I", "-B", "-u", facts["supervisor_path"], "run",
                                 os.path.abspath(launch_path), "--manifest", facts["manifest_path"]],
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
    present = (("state_path", launch["state_path"]), ("action", action_path(ky_run, job_id)),
               ("action", submit_path), ("stdout_path", launch["stdout_path"]),
               ("stderr_path", launch["stderr_path"]), ("result.json", os.path.join(scratch, "result.json")),
               ("plist", plist), ("supervisor.out", document["StandardOutPath"]),
               ("supervisor.err", document["StandardErrorPath"]))
    if is_codex(launch):
        present += ((FINAL_MESSAGE, os.path.join(scratch, FINAL_MESSAGE)),)
    for label_of, path in present:
        if os.path.lexists(path):
            refusals.append(f"submit: {label_of} {path} already exists; job {job_id} was already submitted or run "
                            f"(never repeat it)")
    if refusals:
        _refuse(launch_path, refusals)
        return EXIT_REFUSED

    try:
        with open(plist, "xb") as handle:
            plistlib.dump(document, handle)
    except OSError as failed:
        _refuse(launch_path, [f"submit: the agent's plist could not be written at {plist}: {failed}"])
        return EXIT_REFUSED
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
            "card_sha256": launch["card_sha256"], "program_arguments": document["ProgramArguments"],
            "environment_names": sorted(document["EnvironmentVariables"]), "overrides": facts["overrides"]},
            kind="submit", more_target={"label": label, "domain": domain, "plist": plist},
            transition=f"bootstrap the one-shot launchd agent {label} that runs job {job_id}")
    except OSError as failed:
        os.unlink(plist)
        _refuse(launch_path, [f"submit: action {submit_path} already exists; job {job_id} was already submitted "
                              f"(never repeat it)" if isinstance(failed, FileExistsError) else
                              f"submit: the intent could not be recorded at {submit_path}: {failed}"])
        return EXIT_REFUSED
    code, _, error = launchctl(environ, "bootstrap", domain, plist)
    try:                                            # launchd has been asked: what follows records, and never raises
        complete_action(submit_path, action, code == 0, {
            "launchctl": "bootstrap", "exit": code, "stderr": (error.strip().splitlines() or [""])[0][:300],
            "label": label, "domain": domain, "plist": plist})
        report(json.dumps({"job_id": job_id, "label": label, "plist": plist, "state_path": launch["state_path"]},
                          ensure_ascii=False, sort_keys=True, indent=1))
    except Exception as failed:
        print(f"ACTION NOT COMPLETED {submit_path}: {type(failed).__name__}: {failed} (launchctl bootstrap exited "
              f"{code}; `status` shows whether the agent is loaded)", file=sys.stderr)
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
        document = read_json(path)
    except ValueError:
        return None, "unreadable"
    return (document, None) if type(document) is dict else (None, "unreadable")


def alive(pid, start):
    """true | false | "unknown" — and None when no process was recorded at all"""
    if pid is None:
        return None
    verdict = process_matches(pid, start)
    return "unknown" if verdict is None else verdict


def label_state(environ, job_id):
    """(true | false | "unknown", launchctl's exit status). Loaded: `launchctl print` exits 0. Not loaded: ONLY
    its genuine not-found status (113, "Could not find service"). Any other answer — launchctl not run, a
    domain error, a timeout — is unknown, never "not loaded"."""
    code, _, _ = launchctl(environ, "print", agent_target(job_id))
    return (True if code == 0 else False if code == LAUNCHCTL_NOT_FOUND else "unknown"), code


def label_loaded(environ, job_id):
    return label_state(environ, job_id)[0]


def recorded_job_over(state):
    """(None, None) when the job a state.json records is positively over, else (why it is not, the group's
    state). Over: no process was recorded; or its leader is positively gone AND — when it led a group of its
    own — that group answers `killpg` with ESRCH; a job that never led a group (recorded as a failed launch)
    is over with its one process."""
    pid, pgid = state.get("pid"), state.get("pgid")
    job = alive(pid, state.get("process_start"))
    if job is None:
        return None, None
    if job is not False:
        return ("the job's process is alive" if job is True else "the job's process cannot be identified"), None
    if isinstance(pgid, bool) or not isinstance(pgid, int):
        return "the job's process group is not recorded", "unknown"
    if pgid != pid:
        if state.get("phase") == "launch_failed":
            return None, None
        return "the job's process group cannot be identified", "unknown"
    group = recorded_group_state(pgid)
    if group == "gone":
        return None, group
    return ("members of the job's process group are alive" if group == "live"
            else "the job's process group cannot be confirmed gone"), group


STATUS_FIELDS = ("item", "kind", "role", "phase", "termination", "termination_detail", "exit_code", "exit_signal",
                 "group_gone", "pid", "pgid", "process_start", "supervisor_pid", "supervisor_process_start",
                 "started_at", "ended_at", "deadline", "launch_context", "provider_session_id", "job_result_valid",
                 "launch_error", "supervisor_error", "overrides")


def status_of(ky_run, environ, job_id) -> dict:
    """read-only: what is recorded and what can be observed now; nothing is changed"""
    state, problem = read_record(os.path.join(ky_run, "jobs", job_id, "state.json"))
    submitted, _ = read_record(action_path(ky_run, job_id, "submit"))
    state = state or {}
    pgid = state.get("pgid")
    return {"job_id": job_id, "label": job_label(job_id), "label_loaded": label_loaded(environ, job_id),
            "state_file": problem or "present",
            "state": {name: state.get(name) for name in STATUS_FIELDS} if state else None,
            "process_alive": alive(state.get("pid"), state.get("process_start")),
            "process_group": recorded_group_state(pgid) if pgid is not None and pgid == state.get("pid") else None,
            "supervisor_alive": alive(state.get("supervisor_pid"), state.get("supervisor_process_start")),
            "submit": {"state": submitted.get("state"), "result": submitted.get("result")} if submitted else None}


def reap_one(ky_run, environ, job_id) -> dict:
    """boot out the agent of a job that is positively over: its state.json is readable, the job it recorded
    (leader AND process group) is positively gone, and so is its supervisor. A live or unidentifiable process,
    group or launchctl answer leaves the label alone."""
    entry = {"job_id": job_id, "label": job_label(job_id), "action": "left", "why": None}
    state, problem = read_record(os.path.join(ky_run, "jobs", job_id, "state.json"))
    if state is None:
        entry["why"] = f"state.json is {problem}: the job's identity is unknown"
        return entry
    entry["why"], _ = recorded_job_over(state)
    if entry["why"] is not None:
        return entry
    supervisor = alive(state.get("supervisor_pid"), state.get("supervisor_process_start"))
    if supervisor is not False:
        entry["why"] = "the supervisor is alive" if supervisor is True else "the supervisor cannot be identified"
        return entry
    loaded, code = label_state(environ, job_id)
    if loaded is not True:
        entry.update(action="not_loaded" if loaded is False else "left",
                     why=None if loaded is False else "launchctl could not be asked" if code == 127
                     else f"launchctl did not say whether the agent is loaded (exit {code})")
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
USAGE = ("usage: python3 -I -B kyboot.py check <launch_input.json> [--manifest M] | argv <launch_input.json> "
         "[--manifest M] | run <launch_input.json> [--manifest M] [--grace SECONDS] | submit <launch_input.json> "
         "[--manifest M] | status [<job_id>] | reap [<job_id>] | validate <schema-name> <file>")


def _refuse(launch_path, findings):
    print(f"REFUSED {launch_path} ({len(findings)} reason(s); nothing was launched)", file=sys.stderr)
    for line in findings:
        print(f"  {line}", file=sys.stderr)


def _validate(name, path) -> int:
    """shape-check one document. No manifest is involved, so kyschema.py is executed from its bytes on disk
    WITHOUT being verified: this is a convenience for people and tests, never one of the launch gates."""
    if name not in schema_names():
        print(f"unknown schema {name!r}; known: {', '.join(schema_names())}", file=sys.stderr)
        return EXIT_USAGE
    try:
        with open(os.path.join(FLEET, SCHEMA_TOOL), "rb") as handle:
            schema_tool = module_from_bytes("kyschema_by_path", os.path.join(FLEET, SCHEMA_TOOL), handle.read())
        schema = load_schema(name)
        findings = schema_tool.lint(schema)
    except Exception as bad:
        findings = [f"{type(bad).__name__}: {bad}"]
    if findings:
        print(f"SCHEMA REFUSED {name}\n" + "\n".join(findings), file=sys.stderr)
        return EXIT_USAGE
    try:
        errors = schema_tool.validate(schema, read_json(path))
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
    names = own_env_credentials(environ)
    if names:
        return _credential_refusal(names)
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


def _credential_refusal(names) -> int:
    print("REFUSED: credential variable name(s) set in this process's own environment: "
          f"{', '.join(names)} (values not read; plan §7 → exit 78)", file=sys.stderr)
    return EXIT_CREDENTIAL_ENV


def main(argv=None, environ=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    environ = os.environ if environ is None else environ
    if len(argv) == 3 and argv[0] == "validate":
        names = own_env_credentials(environ)
        return _credential_refusal(names) if names else _validate(argv[1], argv[2])
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
        return _credential_refusal(names)
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
              f"context {checked.facts.get('launch_context')}, "
              f"{checked.facts.get('codex_version' if is_codex(checked.launch) else 'claude_version')}, "
              f"manifest {checked.facts.get('manifest_sha256')}, overrides: "
              f"{show_overrides(checked.facts['overrides'])})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
