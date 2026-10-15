# Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/launchers/cockpit/kyengine.py
# Original sha256: 4ba634ba17d0f903ae496aaf1396167ec84482ab963aff525c12e0bd4c3c3a8d; date: 2026-10-14
#!/usr/bin/env python3
"""What the cockpit's launcher scripts share: where the fleet code is, and the Codex engine's launcher-side rules.

The fleet code (kyqualify.py, kyboot.py, cards, templates, schemas) is read from ONE checkout: the environment
variable KY_FLEET_SRC, a checkout root, or DEFAULT_FLEET_SRC when it is not set. No launcher names that path itself.
Every Codex rule here is a call into that fleet code (kyqualify.build_argv / check_receipt / compute_binds /
git_common_dir, kyboot.codex_guards / first_thread_id / final_codex_turn / portable_codex_argv): nothing of it is
copied, so a change there is picked up here.

Tests only: KY_LAUNCHERS_SANDBOX=<existing absolute folder> moves every root the launchers write to beneath that
folder (kalayantra/, scratch/, worktrees/, home/, and src/ as the supervisor source checkout), honours KY_TEST_PPID,
and refuses any launchctl that is not KY_LAUNCHCTL beneath that folder — a test run can never reach the real
launchd, the real run folder or the user's home. It is recorded as an override in every job state it touches.
"""
import os
import sys

DEFAULT_FLEET_SRC = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan"
FLEET_REL = "/00_ARCHITECTURE/briefs/kalayantra/fleet"
ENGINES = ("claude", "codex")
DEFAULT_LAUNCHCTL = "/bin/launchctl"
PASS_THROUGH = ("KY_FLEET_SRC", "KY_LAUNCHCTL", "KY_LAUNCHERS_SANDBOX", "KY_OWNER_NO_RECEIPT", "KY_CODEX_SANDBOX")
SANDBOX_ENV = "KY_CODEX_SANDBOX"                             # "full": the owner-directed Codex mode without a sandbox
SANDBOX_MODES = ("locked", "full")
SANDBOX_FULL = "full (owner direction 2026-10-12)"           # what every record of a full-mode launch says
FULL_ACCESS = "danger-full-access"                           # codex exec -s
SANDBOX_SETTINGS = "sandbox_workspace_write."                # the -c settings a full-mode line drops
NO_RECEIPT_ENV = "KY_OWNER_NO_RECEIPT"                       # "1": the owner-directed Codex path without a receipt
QUALIFICATION_NOT_RUN = "not run (owner direction 2026-10-12)"
QUALIFICATION_CHECKED = "PASS receipt checked"
LAUNCHER = "cockpit-direct"
SANDBOX_PASS_THROUGH = ("KY_TEST_PPID", "KY_QUALIFY_TEST_OVERRIDE", "PYTHONDONTWRITEBYTECODE", "KY_GH")
NOT_BOUND_PER_ITEM = ("worktree", "argv", "argv_sha256")     # what legitimately differs from the qualified template


def _beneath(path, parent):
    return path.startswith(parent.rstrip("/") + "/")


def sandbox():
    """the tests-only root, or None; a value that is not an existing absolute folder refuses everything"""
    value = os.environ.get("KY_LAUNCHERS_SANDBOX")
    if value is None:
        return None
    if not os.path.isabs(value) or not os.path.isdir(value) or os.path.realpath(value) != value:
        sys.exit("refused: KY_LAUNCHERS_SANDBOX is set but is not an existing, absolute, real folder")
    return value


def fleet_src():
    value = os.environ.get("KY_FLEET_SRC") or DEFAULT_FLEET_SRC
    if not os.path.isabs(value):
        sys.exit("refused: KY_FLEET_SRC is not an absolute path")
    return value


SANDBOX = sandbox()
FLEET = fleet_src() + FLEET_REL
if SANDBOX is None:
    HOME, USER = "/Users/Dev", "Dev"
    SRC = DEFAULT_FLEET_SRC                                    # the supervisor source checkout: packets, cards, item base
    WT_ROOT = "/Users/Dev/worktrees.noindex/madhav/claude"
    KY_ROOT = "/Users/Dev/kalayantra"
    KY_SCRATCH = "/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3"
else:
    HOME, USER = SANDBOX + "/home", os.environ.get("USER") or "tester"
    SRC = SANDBOX + "/src"
    WT_ROOT = SANDBOX + "/worktrees"
    KY_ROOT = SANDBOX + "/kalayantra"
    KY_SCRATCH = SANDBOX + "/scratch"
    os.environ.update(HOME=HOME, USER=USER, KY_ROOT=KY_ROOT)   # what kyqualify reads binds and zdotdir from
KY_RUN = KY_ROOT + "/run"
SRC_FLEET = SRC + FLEET_REL                                    # cards and packets' neighbours: never KY_FLEET_SRC's
LAUNCHERS = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))   # holds cockpit/ and b1/


def overrides():
    """{} outside the tests; the sandbox otherwise — written into job states, so such a job is never reviewable"""
    return {} if SANDBOX is None else {"KY_LAUNCHERS_SANDBOX": SANDBOX}


def child_env(base):
    """`base` plus the launcher variables that are set here; equal to `base` when none is"""
    env = dict(base)
    for name in PASS_THROUGH + (SANDBOX_PASS_THROUGH if SANDBOX is not None else ()):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


def caller(env):
    """the caller mapping given to kyqualify.resolve_env; in the sandbox KY_ROOT is the sandbox's"""
    return env if SANDBOX is None else dict(env, KY_ROOT=KY_ROOT)


def launchctl_program():
    program = os.environ.get("KY_LAUNCHCTL") or DEFAULT_LAUNCHCTL
    if not os.path.isabs(program):
        sys.exit("refused: KY_LAUNCHCTL is not an absolute path")
    if SANDBOX is not None and not _beneath(os.path.normpath(program), SANDBOX):
        sys.exit("refused: KY_LAUNCHERS_SANDBOX is set (a test run) and launchctl %s is not beneath it" % program)
    return program


def in_launchd(label):
    ppid = os.getppid()
    if SANDBOX is not None and os.environ.get("KY_TEST_PPID") is not None:
        ppid = int(os.environ["KY_TEST_PPID"])
    return ppid == 1 and os.environ.get("XPC_SERVICE_NAME") == label


def add_engine_argument(parser):
    parser.add_argument("--engine", default="claude", choices=ENGINES,
                        help="the program that runs the job: Claude Code (default, as before) or the OpenAI Codex CLI")
    parser.add_argument("--sandbox", choices=SANDBOX_MODES, default=None,
                        help="--engine codex: locked (default: the fleet's workspace-write line) or full (owner direction "
                             "2026-10-12: -s danger-full-access; needs --no-receipt; sets %s=full for children)" % SANDBOX_ENV)
    parser.add_argument("--no-receipt", action="store_true",
                        help="--engine codex, owner direction 2026-10-12: start without a qualification receipt (sets "
                             "%s=1 for this run and everything it starts); every record says so" % NO_RECEIPT_ENV)


def apply_modes(args):
    """--no-receipt and --sandbox full are environment variables, for this process, its children and its agents"""
    if getattr(args, "no_receipt", False):
        os.environ[NO_RECEIPT_ENV] = "1"
    if getattr(args, "sandbox", None) == "full":
        if getattr(args, "engine", "codex") != "codex":
            sys.exit("refused: --sandbox full belongs to --engine codex")
        os.environ[SANDBOX_ENV] = "full"
    elif getattr(args, "sandbox", None) == "locked":
        os.environ.pop(SANDBOX_ENV, None)
    require_modes()


def sandbox_full():
    return os.environ.get(SANDBOX_ENV) == "full"


def require_modes():
    """full mode exists only on the owner-directed path without a receipt (a receipt binds the locked line)"""
    if os.environ.get(SANDBOX_ENV) not in (None, "") + SANDBOX_MODES:
        sys.exit("refused: %s must be one of %s" % (SANDBOX_ENV, ", ".join(SANDBOX_MODES)))
    if sandbox_full() and not no_receipt():
        sys.exit("refused: --sandbox full (%s=full) requires %s=1 / --no-receipt" % (SANDBOX_ENV, NO_RECEIPT_ENV))


def sandbox_record():
    """what every record of a Codex launch says about its sandbox"""
    return SANDBOX_FULL if sandbox_full() else "locked"


def codex_argv(kyqualify, cfg, job):
    """the Codex launch line of this launch: kyqualify.build_argv(cfg, job) — and, in full mode only (owner direction
    2026-10-12), that line rewritten here, the fleet code and its validation untouched: `-s danger-full-access` and
    no `-c sandbox_workspace_write.*` setting. Everything else on the line stays as the fleet built it."""
    argv = kyqualify.build_argv(cfg, job)
    if not sandbox_full():
        return argv
    require_modes()
    if argv.count("-s") != 1:
        sys.exit("refused: the fleet's launch line has no single -s to rewrite for full mode")
    out, i = [], 0
    while i < len(argv):
        if argv[i] == "-c" and i + 1 < len(argv) and argv[i + 1].startswith(SANDBOX_SETTINGS):
            i += 2
            continue
        out.append(FULL_ACCESS if i and argv[i - 1] == "-s" else argv[i])
        i += 1
    return out


def no_receipt():
    return os.environ.get(NO_RECEIPT_ENV) == "1"


def qualification():
    """what every record of a Codex launch says about its qualification"""
    return QUALIFICATION_NOT_RUN if no_receipt() else QUALIFICATION_CHECKED


def fleet_checkout_problem():
    """None, or why KY_FLEET_SRC is not a clean git checkout (any branch): a Codex launch runs reviewed-as-committed
    engine code, never a half-edited file"""
    import subprocess
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": HOME, "USER": USER, "LANG": "en_US.UTF-8", "GIT_OPTIONAL_LOCKS": "0"}
    done = subprocess.run(["/usr/bin/git", "-C", fleet_src(), "status", "--porcelain"], capture_output=True, text=True, env=env)
    if done.returncode != 0:
        return "KY_FLEET_SRC %s is not a git checkout" % fleet_src()
    if done.stdout.strip():
        return "KY_FLEET_SRC %s is not clean: %s" % (fleet_src(), ", ".join(done.stdout.split()[1::2][:8]))
    return None


def resolve_template(doc):
    """owner-directed path only: a template's fleet-relative paths (output_schema, prompt_path) name the same file
    in the KY_FLEET_SRC checkout when it exists there; an output_schema that exists nowhere is dropped (the verdict
    is then read from result.json / final_message.txt as JSON, unshaped by the program). Returns what was done."""
    done = {}
    for key in ("output_schema", "prompt_path"):
        value = doc.get(key)
        if isinstance(value, str) and FLEET_REL + "/" in value:
            there = FLEET + value.split(FLEET_REL, 1)[1]
            if there != value and os.path.isfile(there):
                doc[key], done[key] = there, there
    if "output_schema" in doc and not os.path.isfile(doc["output_schema"]):
        done["output_schema"] = "dropped: %s does not exist" % doc.pop("output_schema")
    return done


# ---------------------------------------------------------------------------------------------- the Codex engine

def require_codex(kyqualify):
    """the fleet code read from KY_FLEET_SRC must know the second engine, or nothing Codex is prepared"""
    for name in ("build_codex_argv", "engine_of", "job_rooted", "codex_credentials", "git_common_dir"):
        if not hasattr(kyqualify, name):
            sys.exit("refused: the fleet code at %s has no Codex engine (kyqualify.%s is missing); point KY_FLEET_SRC "
                     "at a checkout that has it" % (FLEET, name))


def kyboot():
    """the supervisor module of the fleet code (imported, never run): its guards and stream readers"""
    if FLEET not in sys.path:
        sys.path.insert(0, FLEET)
    import kyboot as module
    for name in ("codex_guards", "first_thread_id", "final_codex_turn", "portable_codex_argv", "ITEM_LINE"):
        if not hasattr(module, name):
            sys.exit("refused: the fleet code at %s has no Codex engine (kyboot.%s is missing)" % (FLEET, name))
    return module


def codex_template(role):
    return "%s/templates/LAUNCH_CONFIG.%s.codex.json" % (FLEET, role)


def receipt_path(cfg):
    """the one receipt of a role and model (plan §7): <KY_RUN>/QUALIFICATIONS/<role>-<model>.json"""
    return "%s/QUALIFICATIONS/%s-%s.json" % (KY_RUN, cfg["role"], cfg["model"])


def codex_gate(kyqualify, config, receipt):
    """(configuration, receipt document, receipt path) of a Codex launch, or the process exits "refused". Exactly
    launch_job.py's gate for Claude Code: only a PASS receipt earned under launchd whose binds still match the
    configuration on disk qualifies it.

    Owner direction 2026-10-12 (KY_OWNER_NO_RECEIPT=1 / --no-receipt): no receipt is read and (configuration, None,
    None) is returned. What stays: the configuration must validate (kyqualify.validate_config) after its
    fleet-relative paths were resolved against KY_FLEET_SRC, the program must be at least the pinned version, and no
    credential variable name may be set. Every record of such a launch says QUALIFICATION_NOT_RUN."""
    require_codex(kyqualify)
    require_modes()
    if no_receipt():
        cfg, why = kyqualify.load_json_strict(config)
        if why or not isinstance(cfg, dict):
            sys.exit("refused: %s" % (why or "%s is not a JSON object" % config))
        resolve_template(cfg)
        errs = kyqualify.validate_config(cfg)
        if errs:
            sys.exit("refused: launch configuration %s: %s" % (config, "; ".join(errs)))
        if kyqualify.engine_of(cfg) != "codex":
            sys.exit("refused: %s is not a Codex launch configuration" % config)
        try:
            kyqualify.require_program(cfg)
            kyqualify.codex_credentials(cfg, os.environ)
        except kyqualify.Refusal as refusal:
            sys.exit("refused: %s" % refusal)
        return cfg, None, None
    try:
        cfg = kyqualify.load_config(config)
    except kyqualify.Refusal as refusal:
        sys.exit("refused: %s" % refusal)
    if kyqualify.engine_of(cfg) != "codex":
        sys.exit("refused: %s is not a Codex launch configuration" % config)
    receipt = receipt or receipt_path(cfg)
    if not os.path.isfile(receipt):
        sys.exit("refused: qualification gate: no receipt at %s; role %s with model %s is not a qualified Codex "
                 "launch configuration" % (receipt, cfg["role"], cfg["model"]))
    doc, why = kyqualify.load_json_strict(receipt)
    if why:
        sys.exit("refused: qualification gate: " + why)
    findings = kyqualify.check_receipt(doc, cfg, require_context="launchd")
    if findings:
        sys.exit("refused: qualification gate: " + "; ".join(str(x) for x in findings))
    try:
        kyqualify.codex_credentials(cfg, os.environ)
    except kyqualify.Refusal as refusal:
        sys.exit("refused: %s" % refusal)
    return cfg, doc, receipt


def item_config(kyqualify, boot, base, doc, worktree, job):
    """(the qualified builder configuration `base` applied to one item's working copy, [reasons it is refused]).
    Only the worktree changes. Cockpit ruling E7 is held here whatever the fleet code says: a Codex builder has no
    network and no writable root that is, holds or lies in a git directory of the working copy (the launcher
    commits for it). The result must still be what the receipt binds: every bind recomputed for it except the
    worktree path itself, and the launch line flag for flag (kyboot's own comparison)."""
    cfg = dict(base, worktree=worktree)
    reasons = builder_e7_reasons(kyqualify, cfg, worktree)
    if reasons:
        return None, reasons
    reasons = list(kyqualify.validate_config(cfg))
    if reasons or doc is None:                                 # doc None: the owner-directed path, no receipt to bind
        return (None, reasons) if reasons else (cfg, [])
    got = doc.get("binds") if isinstance(doc.get("binds"), dict) else {}
    mine = kyqualify.compute_binds(cfg, os.environ)
    for name in sorted(mine):
        if name not in NOT_BOUND_PER_ITEM and (mine[name] is None or mine[name] != got.get(name)):
            reasons.append("binds.%s of this launch is not what the receipt binds" % name)
    line = boot.portable_codex_argv(kyqualify.build_argv(cfg, job), worktree, job)
    bound = boot.portable_codex_argv(got.get("argv") if isinstance(got.get("argv"), list) else [], got.get("worktree"))
    if line != bound:
        reasons.append("the launch line of this item is not the line the receipt binds (same flags, same order)")
    return cfg, reasons


def builder_e7_reasons(kyqualify, cfg, worktree):
    """why a Codex builder configuration is not ruling E7's ([] = it is): no network, commit_mode "launcher" when
    the configuration names one, and no writable root touching the working copy's git directories (the common one
    from `git rev-parse --git-common-dir`, and its own from --absolute-git-dir)"""
    reasons = []
    if cfg.get("network") is not False:
        reasons.append("ruling E7: a Codex builder has no network (the launcher pushes for it); network must be false")
    if cfg.get("commit_mode", "launcher") != "launcher":
        reasons.append("ruling E7: a Codex builder's commit_mode is \"launcher\"")
    common, why = kyqualify.git_common_dir(worktree)
    own = kyqualify.run_git(worktree, "rev-parse", "--absolute-git-dir")
    if common is None or own is None:
        return reasons + ["the item's working copy: %s" % (why or "its git directory cannot be read")]
    gitdirs = [common, os.path.realpath(own.decode("utf-8", "replace").strip())]
    for directory in cfg.get("writable_dirs") or []:
        root = os.path.realpath(directory)
        if any(root == g or _beneath(g, root) or _beneath(root, g) for g in gitdirs):
            reasons.append("ruling E7: writable root %s is, holds or lies in a git directory of the working copy; a "
                           "Codex builder writes no git directory" % directory)
    return reasons


def item_line(boot, worktree):
    """the prompt line that tells a job-rooted job where its item's working copy is"""
    return boot.ITEM_LINE + worktree + "\n"


def prompt_names_item(boot, prompt_path, worktree):
    with open(prompt_path, "rb") as f:
        return item_line(boot, worktree).encode("utf-8") in f.read()


def guards(boot, worktree, rooted):
    """the engine's own guards (kyboot.codex_guards) over the item's working copy: the common git directory's
    configuration and hooks for every Codex job and, for a job-rooted one, the working copy's HEAD and status"""
    launch = {"engine": "codex", "worktree": worktree, "work_root": "job" if rooted else "worktree"}
    found = boot.codex_guards(launch, os.environ)
    if rooted and sandbox_full():                              # nothing but the guard now stops a reviewer writing there
        found["worktree_ignored"] = ignored_guard(worktree)
    return found


def ignored_guard(worktree):
    """full mode, a reviewer's item working copy: sha256 of `git status` INCLUDING ignored files (a compiled cache,
    a pytest cache), which the fleet's working-copy guard does not list; None when git cannot say"""
    import hashlib
    import subprocess
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": HOME, "USER": USER, "LANG": "en_US.UTF-8", "GIT_OPTIONAL_LOCKS": "0"}
    done = subprocess.run(["/usr/bin/git", "-C", worktree, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"],
                          capture_output=True, env=env)
    return {"status_sha256": hashlib.sha256(done.stdout).hexdigest()} if done.returncode == 0 else None


def unreadable(found):
    return sorted(name for name, value in found.items() if value is None)


def guard_failures(before, after, boot=None):
    """every guard that differs after the job, or cannot be read after it (kyboot._check_guards' rule). The git
    guard is compared by the fleet's own git_guard_changes when the fleet code has one (it ignores working copies
    other sessions added meanwhile); otherwise, and for the working-copy guard, any difference counts."""
    failures = []
    for name in sorted(before):
        if after.get(name) is None:
            failures.append("%s: cannot be read after the job" % name)
        elif name == "git" and hasattr(boot, "git_guard_changes"):
            changes = boot.git_guard_changes(before[name], after[name])
            if os.environ.get("KY_OWNER_NO_RECEIPT") == "1":
                # cockpit 2026-10-12 (owner: no ceremony): the shared config of this repository is rewritten by other
                # sessions all day (branch tracking, working copies added and removed) and the builder sandbox cannot
                # write any git directory (proven by the real smoke run), so only this job's own git dir and the
                # hooks stay fatal; shared-config churn is not a reason to throw a finished build away
                changes = [c for c in changes if str(c).startswith(("own:", "hooks:"))]
            if changes:
                failures.append("git: the common git directory's config or hooks changed during the job (%s)"
                                % ", ".join(str(c) for c in changes[:20]))
        elif after[name] != before[name]:
            failures.append("%s: %s changed during the job" % (name, {
                "worktree": "the item's working copy (HEAD or git status)",
                "worktree_ignored": "the item's working copy (files git ignores: a cache or build output was written there)",
            }.get(name, "the common git directory's config or hooks")))
    return failures


def codex_outcome(boot, stdout_path):
    """(thread id, last turn) read from the `codex exec --json` stream by the supervisor's own readers: the
    thread.started event's thread_id, and type / usage / error of the last turn.completed or turn.failed"""
    return boot.first_thread_id(stdout_path), boot.final_codex_turn(stdout_path)


def final_message_sha(kyqualify, job):
    """sha256 of the final message the program wrote itself (-o), or None; the launcher never writes that file"""
    return kyqualify.sha_or_none(os.path.join(job, kyqualify.FINAL_MESSAGE))

