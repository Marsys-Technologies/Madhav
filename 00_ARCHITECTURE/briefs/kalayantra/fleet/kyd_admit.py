#!/usr/bin/env python3
"""kyd_admit.py — dispatcher admission for KĀLA-YANTRA v3 (KV3-B-KYDADMIT; relaunch plan v2.7 §5 "Base contract
(KT-04)", §6 "Admission checks", §8.6 "At admission"; KU-02 `dispatcher-ready-receipts`).

version: 1.2 · status: DRAFT (built under the hold; not installed, not merged by its job)
changelog: 1.2 (2026-10-12) review round 2: an intent naming an item the plan model does not hold refuses base as
           unknown instead of reading as an item without prerequisites, and its migration is not reported as known (B1).
           1.1 (2026-10-12) review round 1: code prerequisites are resolved through joins and decisions, an unknown
           dependency or completion_kind refuses (B1); every reported merge commit is verified before it is used or
           recorded, also when the accepted head is in the base (B2).
           1.0 (2026-10-12) first version, packet PACKET_KV3-B-KYDADMIT_v1.

A module of the dispatcher engine (kydispatch.py): no command line, no state of its own. Three calls, each
returning {"admitted": bool, "refusals": [{"code", "detail"}], "facts": {...}}; admitted is true only with no
refusal, and a check that could not be made is a refusal whose detail starts "unknown:" — never a pass.

    precheck(ctx, intent, slot)     read-only; every check runs and every failure is reported
        stale            ctx.next is None: no fresh tracker reading this tick
        packet           `python3 -B fleet/kypacket.py check <packet> --repo <repo>` did not admit the packet
        routing          `python3 -B fleet/kyroute.py packet …` gave no tier, or the plan model is unreadable
        freeze           kyroute.py exit 3: detail "freeze: <path>"
        launch           (model runners) no usable PASS/launchd qualification, turn limit or deadline
        base             the base contract: a code prerequisite is not shown to be contained in the job base, or
                         the intent's item is absent from the plan model (its prerequisites are unknown)
        slot_not_ready   the slot database has no READY receipt of this session that checks out now (KU-02)
        slot_foreign     the slot's receipt belongs to another session (KU-02 ownership conflict)
        ceiling          a new worktree would exceed limits.copies own copies or 24 in all
      facts: tier, launch{}, base_sha, prerequisites[], tests[], test_digests[], migration (kyd_jobs.open reads them)
    provision(ctx, slot)            local_db.sh up + db for a slot with no receipt or this session's non-READY one
    admit(ctx, job)                 after kyd_jobs.open: worktree and item lock; for a BUILD of a feature packet the
                                    packet's tests are installed and the current result classified
        worktree / lock / tests / already_green / unclassified; facts.result expected_red | already_green |
        unclassified | null; $KY_RUN/admission/<item>.json = {item, base_sha, test_digests, result}

What an admission here is NOT (each is another component's detector, named so that nothing reads more into it):
  - the qualification receipt is read, not re-earned: `result`, `context`, role, model and the binds this module
    hands on are compared, and the MCP configuration is hashed now against the bound sha256; the receipt's checks,
    probes, launchd receipt and remaining binds are re-judged by `kyqualify.py check` (install) and kyjob.sh;
  - a non-code prerequisite (artifact, packet, operation) is listed without a Git head: its typed acceptance receipt
    is the tracker's guard, not judged here (plan §5: "never invented Git heads"); a join or decision is listed
    without one too, but the code items beneath it are judged;
  - "verified corresponding merge commit" is: the PR whose head IS the accepted head reports MERGED with a 40-hex
    merge commit that is a single-parent commit of this repository and equals every mapping earlier job states
    recorded for that head. The squash's content is not compared with the head's.

INTERPRETATION (plan and packet silent; each errs to refusal):
  - code prerequisites are the items of completion_kind "code" reached from the plan-model item's `depends_on`,
    resolving through items without a completion_kind (joins, decisions) and stopping at code, artifact, operation
    and packet items; a dependency absent from the model or of another completion_kind refuses as unknown;
  - the item worktree is <WORKTREE_ROOT>/kalayantra-<item, lower case> (kyd_jobs.open's path); "own copies" are
    the registered worktrees under WORKTREE_ROOT named kalayantra-*, "in all" every registered one under it;
  - a slot receipt's mount_source must resolve beneath realpath(scratch), besides `local_db.sh check`;
  - provision raises an owner-wait also for an unreadable receipt and for this session's READY receipt that no
    longer checks out (`reset` is not this module's to run); it never touches another session's database;
  - admit refuses a BUILD of a feature packet whose job does not hold item.<item>: installing tests writes into the
    item worktree; a test file already present with another digest is refused, not overwritten;
  - a MERGED prerequisite PR without a usable merge commit refuses even when the head itself is in the base.
"""
import calendar
import datetime
import math
import os
import re
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kyaction  # noqa: E402
import kyschema  # noqa: E402

GIT = "/usr/bin/git"
PYTHON = "python3"
WORKTREE_ROOT = "/Users/Dev/worktrees.noindex/madhav/claude"
ALL_COPIES_MAX = 24  # owner Amendment A1 D-16
MODELS = {"sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5", "surrogate": "claude-fable-5-1"}
ROUTING_TIERS = ("sonnet", "opus")
CODEX_MODEL = "gpt-6.1-sol"
JOB_ENGINE_ROLES = {kind: kind.lower() for kind in (
    "BUILD", "REWORK", "VERIFY", "ARTIFACT", "PRE-ACCEPT", "POST-READBACK", "RULING",
    "SURROGATE", "REQUEST-PREP", "MODEL", "PLAN")}
CODEX_READ_ONLY_KINDS = {"VERIFY", "PRE-ACCEPT", "POST-READBACK", "RULING"}
# plan §7 "Turn caps", plus the packet's (I) for the kinds §7 does not list
TURN_CAPS = {"BUILD": 150, "REWORK": 100, "VERIFY": 60, "PRE-ACCEPT": 40, "POST-READBACK": 40, "RULING": 30, "PLAN": 300,
             "ARTIFACT": 60, "SURROGATE": 30, "MODEL": 300, "REQUEST-PREP": 300}
NO_MIGRATION = (None, "", "NONE")           # kyroute.py's NONE_METADATA
RESOLVED_KINDS = ("code", "artifact", "operation", "packet")    # completion kinds a prerequisite resolution stops at
PRECHECK_CODES = ("stale", "packet", "routing", "freeze", "launch", "base", "slot_not_ready", "slot_foreign", "ceiling")
ADMIT_CODES = ("worktree", "lock", "tests", "already_green", "unclassified")
RESULTS = ("expected_red", "already_green", "unclassified")
QUALIFICATION_SCHEMA = "ky.qualification/1"
SLOT_SCHEMA = "ky.slot_db/1"
PACKET_CHECK_SCHEMA = "ky.packet_check/1"
SEED_KEYS = ("schema_sha256", "ledger_sha256", "registry_sha256")
SLOT_RE = re.compile(r"^[bv][1-8]\Z")
ITEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{0,39}\Z")
SHA1_RE = re.compile(r"^[0-9a-f]{40}\Z")
SHA256_RE = re.compile(r"^[0-9a-f]{64}\Z")
UP_TIMEOUT_S = 300
DB_TIMEOUT_S = 1800                         # restore + the migration runner
PRECHECK_TIMEOUT_S = 1800
DETAIL_MAX = 300


class AdmitError(Exception):
    """ctx itself is unusable (a path that is not absolute): the engine's tick reports it, nothing is admitted."""


# ───────────────────────────────────────────── small helpers ─────────────────────────────────────────────

def _path(ctx, name):
    paths = ctx.paths
    value = paths.get(name) if isinstance(paths, dict) else getattr(paths, name, None)
    value = os.fspath(value) if isinstance(value, (str, os.PathLike)) else None
    if not value or not os.path.isabs(value):
        raise AdmitError("ctx.paths.%s is not an absolute path" % name)
    return value


def _sh(ctx, argv, env=None, cwd=None, timeout=120):
    """(rc, out, err); rc is an int or None (unknown)."""
    rc, out, err = ctx.sh(argv, env=env, cwd=cwd, timeout=timeout)
    rc = rc if isinstance(rc, int) and not isinstance(rc, bool) else None
    return rc, out if isinstance(out, str) else "", err if isinstance(err, str) else ""


def _refuse(refusals, code, detail):
    refusals.append({"code": code, "detail": kyaction.flat(detail, DETAIL_MAX) or code})


def _result(refusals, facts):
    return {"admitted": not refusals, "refusals": refusals, "facts": facts}


def _said(rc, out, err, what):
    if rc is None:
        return "unknown: %s could not be run or did not end" % what
    return "%s exit %d: %s" % (what, rc, kyaction.flat(err or out, 200) or "no output")


def _json_object(text):
    try:
        doc = kyschema.load_json_text(text)
    except (ValueError, RecursionError):
        return None
    return doc if isinstance(doc, dict) else None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _strings(value):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def _under(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path != root and os.path.commonpath([path, root]) == root


def deadline_text(now, seconds):
    """`now` (a datetime — naive means UTC — or epoch seconds) + seconds as UTC text YYYY-MM-DDTHH:MM:SSZ, else None."""
    if isinstance(now, datetime.datetime):
        epoch = calendar.timegm(now.utctimetuple())
    elif isinstance(now, (int, float)) and not isinstance(now, bool) and math.isfinite(now):
        epoch = int(now)
    else:
        return None
    return kyaction.utc(epoch + seconds) if _is_int(seconds) and seconds > 0 else None


def front_matter(path):
    """(the packet's front matter object, None) or (None, reason): the first line is ```json, the object ends at the
    next line of exactly three backticks (the form KV3-B-KYPACKET fixes)."""
    try:
        with open(path, "rb") as f:
            lines = f.read().decode("utf-8").split("\n")
    except (OSError, UnicodeDecodeError, TypeError, ValueError) as e:
        return None, "cannot read %s: %s" % (path, type(e).__name__)
    if lines[0] != "```json" or "```" not in lines[1:]:
        return None, "%s does not start with a fenced json front matter" % path
    doc = _json_object("\n".join(lines[1:lines.index("```", 1)]))
    return (doc, None) if doc is not None else (None, "the front matter of %s is not one strict JSON object" % path)


def packet_tests(front):
    """(test_commits[] as [{sha, digest, path}], None) or (None, reason). An absent list is an empty one."""
    commits = front.get("test_commits")
    if commits is None:
        return [], None
    if not isinstance(commits, list):
        return None, "test_commits is not a list"
    for c in commits:
        if not isinstance(c, dict) or not all(isinstance(c.get(k), str) for k in ("sha", "digest", "path")):
            return None, "a test_commits entry lacks sha, digest or path"
        if not SHA1_RE.match(c["sha"]) or not SHA256_RE.match(c["digest"]):
            return None, "test_commits entry %s: sha or digest is not a full hex value" % c["path"]
        parts = c["path"].split("/")
        if os.path.isabs(c["path"]) or any(p in ("", ".", "..") for p in parts) or re.search(r"[\s\\]", c["path"]):
            return None, "test path %r is not a plain repository-relative path" % c["path"]
    if len({c["path"] for c in commits}) != len(commits):
        return None, "test_commits names a path twice"
    return commits, None


def worktrees(ctx):
    """[{path (resolved), head, branch}] of `git worktree list --porcelain` in the repository, or None (unknown)."""
    rc, out, _ = _sh(ctx, [GIT, "worktree", "list", "--porcelain"], cwd=_path(ctx, "repo"))
    if rc != 0:
        return None
    entries = []
    for line in out.splitlines():
        if line.startswith("worktree "):
            entries.append({"path": os.path.realpath(line[9:]), "head": None, "branch": None})
        elif entries and line.startswith("HEAD "):
            entries[-1]["head"] = line[5:]
        elif entries and line.startswith("branch "):
            entries[-1]["branch"] = line[7:]
    return entries


def item_worktree(item):
    return os.path.join(WORKTREE_ROOT, "kalayantra-" + item.lower())


def _entry_at(entries, path):
    path = os.path.realpath(path)
    return next((e for e in entries or [] if e["path"] == path), None)


def model_items(ctx):
    """({id: item}, None) of the plan model at ctx.model, or (None, reason)."""
    try:
        with open(ctx.model, "r", encoding="utf-8") as f:
            doc = _json_object(f.read())
    except (OSError, UnicodeDecodeError, TypeError, ValueError, AttributeError) as e:
        return None, "the plan model cannot be read: %s" % type(e).__name__
    items = doc.get("items") if doc is not None else None
    if not isinstance(items, list) or not all(isinstance(i, dict) and isinstance(i.get("id"), str) for i in items):
        return None, "the plan model has no usable items list"
    if len({i["id"] for i in items}) != len(items):
        return None, "the plan model holds an item id twice"
    return {i["id"]: i for i in items}, None


# ───────────────────────────────────────────── precheck: the checks ─────────────────────────────────────────────

def _check_packet(ctx, intent, packet, refusals, facts):
    """→ the front matter, or None."""
    rc, out, err = _sh(ctx, [PYTHON, "-B", os.path.join(_path(ctx, "fleet"), "kypacket.py"), "check", packet,
                             "--repo", _path(ctx, "repo")])
    report = _json_object(out) if rc == 0 else None
    if rc != 0:
        reasons = (_json_object(out) or {}).get("reasons")
        named = "; ".join("%s: %s" % (r.get("code"), r.get("detail")) for r in reasons if isinstance(r, dict)) \
            if isinstance(reasons, list) else ""
        _refuse(refusals, "packet", named or _said(rc, out, err, "kypacket.py check"))
    elif report is None or report.get("schema") != PACKET_CHECK_SCHEMA or report.get("admitted") is not True:
        _refuse(refusals, "packet", "unknown: kypacket.py check exit 0 without a %s report that admits the packet"
                % PACKET_CHECK_SCHEMA)
    front, reason = front_matter(packet)
    if reason:
        _refuse(refusals, "packet", "unknown: " + reason)
        return None
    if front.get("id") != intent.get("item"):
        _refuse(refusals, "packet", "the packet is %r, the intent's item %r" % (front.get("id"), intent.get("item")))
    commits, reason = packet_tests(front)
    if reason:
        _refuse(refusals, "packet", "unknown: " + reason)
    else:
        facts["tests"] = [c["path"] for c in commits]
        facts["test_digests"] = [c["digest"] for c in commits]
    return front


def _check_routing(ctx, intent, packet, items, items_reason, refusals, facts):
    before = len(refusals)
    rc, out, err = _sh(ctx, [PYTHON, "-B", os.path.join(_path(ctx, "fleet"), "kyroute.py"), "packet", "--packet", packet,
                             "--model", str(ctx.model), "--repo", _path(ctx, "repo")])
    report = _json_object(out) or {}
    routed = None
    if rc == 3:
        frozen = report.get("frozen") if _strings(report.get("frozen")) else []
        for path in frozen or ["unknown: kyroute.py exit 3 named no path"]:
            _refuse(refusals, "freeze", "freeze: " + path)
    elif rc != 0:
        _refuse(refusals, "routing", _said(rc, out, err, "kyroute.py packet"))
    elif report.get("decision") != "ROUTE" or report.get("tier") not in ROUTING_TIERS:
        _refuse(refusals, "routing", "unknown: kyroute.py packet exit 0 without a ROUTE decision and a tier")
    else:
        routed = report["tier"]
    wanted = intent.get("tier")
    if wanted is not None and wanted not in ROUTING_TIERS:
        _refuse(refusals, "routing", "unknown: the intent's tier %r is no tier" % (wanted,))
    if items is None:
        _refuse(refusals, "routing", "unknown: %s (brief.migration)" % items_reason)
    else:
        node = items.get(intent.get("item"))
        brief = node.get("brief") if isinstance(node, dict) else None
        migration = brief.get("migration") if isinstance(brief, dict) else None
        if node is None:
            pass        # not known to be null: an item absent from the plan model is refused by the base check
        elif migration in NO_MIGRATION:
            facts["migration"] = None
        elif isinstance(migration, str):
            facts["migration"] = migration
        else:
            _refuse(refusals, "routing", "unknown: brief.migration of %s is not text" % intent.get("item"))
    if len(refusals) == before:
        facts["tier"] = "opus" if "opus" in (routed, wanted) else "sonnet"


def refresh_job_engine(ctx):
    """Snapshot JOB_ENGINE once at kinds_build.intents (each dispatch tick).

    (I) INTERPRETATION: build still covers REWORK unless explicitly overridden,
    but REWORK earns its own role receipt. Global Codex excludes the owner
    surrogate, which stays on Claude Fable. Unknown syntax,
    duplicate keys/defaults, empty or unreadable files refuse the entire policy.
    """
    run = _path(ctx, "run") if hasattr(ctx, "paths") else os.fspath(ctx.run)
    if not os.path.isabs(run):
        raise AdmitError("ctx.run is not an absolute path")
    path = os.path.join(run, "JOB_ENGINE")
    policy, error = {"default": "claude"}, None
    try:
        # O_NONBLOCK also fences a regular-file -> FIFO replacement between ticks.
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK), encoding="utf-8") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("not a regular file")
            content = handle.read(4097)
        if len(content) > 4096 or not content.strip():
            raise ValueError("empty or larger than 4096 characters")
        seen = set()
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                key, value = (part.strip() for part in line.split("=", 1))
                if key not in JOB_ENGINE_ROLES.values():
                    raise ValueError("unknown kind")
            else:
                key, value = "default", line
            if key in seen or value not in ("claude", "codex"):
                raise ValueError("duplicate choice or unknown engine")
            if key == "surrogate" and value != "claude":
                raise ValueError("owner surrogate requires Claude Fable")
            seen.add(key)
            policy[key] = value
    except FileNotFoundError:
        if os.path.lexists(path):
            error = "JOB_ENGINE: unreadable dangling path"
    except (OSError, UnicodeError, ValueError) as exc:
        error = "JOB_ENGINE: invalid/unreadable policy (%s)" % type(exc).__name__
    ctx.job_engine_policy = policy, error
    if error and error != getattr(ctx, "_job_engine_error", None):
        ctx.journal("dispatcher error", error)
    ctx._job_engine_error = error
    return policy, error


def job_engine(ctx, kind):
    """The tick's role choice; invalid policies are refused by admission, never repaired."""
    policy, error = getattr(ctx, "job_engine_policy", None) or refresh_job_engine(ctx)
    if error or kind == "SURROGATE":
        return "claude"
    choice = policy.get(kind.lower()) if isinstance(kind, str) else None
    if choice is None:
        choice = policy.get("build", policy["default"]) if kind == "REWORK" else policy["default"]
    return choice


def surrogate_config(ctx):
    """Only the installed owner-surrogate template may select its allowed Claude model."""
    import kyqualify

    fleet = _path(ctx, "fleet") if hasattr(ctx, "paths") else os.fspath(ctx.fleet)
    if not os.path.isabs(fleet):
        raise AdmitError("ctx.fleet is not an absolute path")
    path = os.path.join(fleet, "templates", "LAUNCH_CONFIG.surrogate.json")
    cfg, error = kyaction.read_json(path)
    if error or not isinstance(cfg, dict):
        return None, "surrogate template %s: %s" % (path, error or "not an object")
    errors = kyqualify.validate_config(cfg, check_disk=False)
    if (kyqualify.engine_of(cfg), cfg.get("role"), cfg.get("model"), cfg.get("effort")) != (
            "claude", "surrogate", MODELS["surrogate"], "high"):
        errors.append("owner surrogate template requires Claude claude-fable-5-1/high")
    return (None, "; ".join(errors)) if errors else (cfg, None)


def qualification_name(role, model, chart=False, tests=False):
    """Receipt variant names keep the qualified role itself unchanged."""
    return "%s%s%s-%s.json" % (role, "-chart" if chart else "", "-tests" if tests else "", model)


def _check_codex_launch(ctx, intent, front, front_known, refusals, facts, slot):
    """Re-judge the real launchd receipt against the installed role template.

    The template and its hash travel as admission facts; kyd_jobs adapts only
    worktree/prompt to this job. Claude fields remain null, never mixed in.
    """
    import kyqualify

    role = JOB_ENGINE_ROLES[intent["kind"]]
    model = CODEX_MODEL
    tests_variant = bool((front or {}).get("test_commits"))
    template = os.path.join(_path(ctx, "fleet"), "templates", "LAUNCH_CONFIG.%s%s.codex.json"
                            % (role, ".tests" if tests_variant else ""))
    receipt = os.path.join(_path(ctx, "run"), "QUALIFICATIONS", qualification_name(role, model, tests=tests_variant))
    digest = kyaction.sha_file(template)
    cfg, cfg_error = kyaction.read_json(template)
    doc, doc_error = kyaction.read_json(receipt)
    reasons = []
    if not front_known or (front or {}).get("needs_chart_data", False) is not False:
        reasons.append("Codex job template has no chart-data MCP qualification")
    if cfg_error or not isinstance(cfg, dict):
        reasons.append("Codex template %s is unreadable" % template)
    else:
        reasons.extend(kyqualify.validate_codex_config(cfg))
        if (cfg.get("engine"), cfg.get("role"), cfg.get("model"), cfg.get("effort")) != ("codex", role, model, "high"):
            reasons.append("Codex template requires the selected role and gpt-6.1-sol/high")
        verifier = intent["kind"] in CODEX_READ_ONLY_KINDS
        if not verifier and intent.get("pool") == "verifier":
            reasons.append("Codex builder posture conflicts with the dispatcher verifier pool; kind is unqualified")
        if (kyqualify.job_rooted(cfg) != verifier or cfg.get("sandbox") != "workspace-write"
                or cfg.get("network") is not False or cfg.get("writable_dirs") != []
                or (not verifier and cfg.get("commit_mode") != "launcher")):
            reasons.append("Codex template does not preserve the accepted builder/verifier boundary")
    if doc_error or not isinstance(doc, dict):
        reasons.append("Codex qualification receipt %s: %s" % (receipt, doc_error or "not an object"))
    else:
        binds = doc.get("binds") or {}
        if ((doc.get("schema"), doc.get("engine"), doc.get("role"), doc.get("model"), doc.get("result"), doc.get("context"))
                != (QUALIFICATION_SCHEMA, "codex", role, model, "PASS", "launchd")
                or not isinstance(binds, dict) or binds.get("engine") != "codex"
                or binds.get("model") != model or binds.get("effort") != "high"):
            reasons.append("Codex receipt must be PASS/launchd for the selected role and gpt-6.1-sol/high")
    if not reasons:
        env = {name: os.environ[name] for name in ("HOME", "USER", "PATH") if name in os.environ}
        env.update(KY_RUN=_path(ctx, "run"), KY_FLEET=_path(ctx, "fleet"),
                   KY_STREAM=intent.get("stream") or "K", KY_LANE=slot or "qualification-check",
                   KY_CONTROLLER_ID=ctx.controller_id)
        for key, name in (("root", "KY_ROOT"), ("scratch", "KY_SCRATCH")):
            value = ctx.paths.get(key) if isinstance(ctx.paths, dict) else getattr(ctx.paths, key, None)
            if value:
                env[name] = os.fspath(value)
        rc, out, err = _sh(ctx, [PYTHON, "-I", "-B", os.path.join(_path(ctx, "fleet"), "kyqualify.py"),
                                "check", receipt, "--config", template, "--require-context", "launchd"], env=env)
        if rc != 0:
            reasons.append(_said(rc, out, err, "Codex qualification check"))
        if digest is None or digest != kyaction.sha_file(template):
            reasons.append("Codex template changed while checking qualification")
        deadline = deadline_text(ctx.now(), cfg["deadline_seconds"])
        if deadline is None:
            reasons.append("unknown: ctx.now() gave no UTC time, so there is no deadline")
        if not reasons:
            facts["launch"] = dict(engine="codex", role=role, model=model, effort="high", deadline=deadline,
                                   permission_mode=None, max_turns=None, claude_bin=None, mcp_config=None,
                                   extra_lean_flags=[], disallowed_tools=[], launch_config_path=template,
                                   codex_config=cfg, codex_config_sha256=digest)
    for reason in reasons:
        _refuse(refusals, "launch", reason)
    if reasons:
        facts["launch"] = None


def _check_launch(ctx, intent, tier, front, front_known, refusals, facts, slot=None):
    policy, error = getattr(ctx, "job_engine_policy", None) or refresh_job_engine(ctx)
    if error:
        _refuse(refusals, "launch", error)
        facts["launch"] = None
        return
    kind = intent.get("kind")
    choice = job_engine(ctx, kind)
    chart = (front or {}).get("needs_chart_data", False)
    if kind in JOB_ENGINE_ROLES and choice == "codex" and chart is True:
        # (I) INTERPRETATION: Claude is necessary under the accepted locked contract:
        # kyqualify's Codex schema/argv has no MCP configuration, network stays off.
        # Never silently launch a chart job without its chart-data qualification.
        ctx.journal("chart engine", "%s %s: Claude necessary; locked Codex has no qualified chart-data MCP"
                    % (kind, intent.get("item")))
        choice = "claude"
    if kind in JOB_ENGINE_ROLES and choice == "codex":
        _check_codex_launch(ctx, intent, front, front_known, refusals, facts, slot)
        return
    reasons = []
    kind, role = intent.get("kind"), intent.get("role")
    model = MODELS["sonnet" if tier == "sonnet" else "opus"]
    surrogate = None
    if kind == "SURROGATE":
        surrogate, reason = surrogate_config(ctx)
        if reason:
            _refuse(refusals, "launch", reason)
            facts["launch"] = None
            return
        model = surrogate["model"]
    cap = TURN_CAPS.get(kind) if isinstance(kind, str) else None
    if cap is None:
        reasons.append("unknown: the kind %r has no turn cap (plan §7)" % (kind,))
    chart = (front or {}).get("needs_chart_data", False)
    if not front_known or not isinstance(chart, bool):
        reasons.append("unknown: the packet does not say whether chart data is needed, so the MCP configuration is open")
    doc, launch = None, None
    if not isinstance(role, str) or not ROLE_RE.match(role):
        reasons.append("unknown: the intent's role %r names no qualification" % (role,))
    else:
        path = os.path.join(_path(ctx, "run"), "QUALIFICATIONS", qualification_name(role, model, chart is True, bool((front or {}).get("test_commits"))))
        doc, err = kyaction.read_json(path)
        if err or not isinstance(doc, dict):
            reasons.append("qualification receipt %s: %s" % (path, err or "not an object"))
            doc = None
    if doc is not None:
        binds = doc.get("binds") if isinstance(doc.get("binds"), dict) else {}
        if doc.get("schema") != QUALIFICATION_SCHEMA or doc.get("role") != role or doc.get("model") != model:
            reasons.append("the receipt is %r for role %r, model %r; wanted %s for %s, %s"
                           % (doc.get("schema"), doc.get("role"), doc.get("model"), QUALIFICATION_SCHEMA, role, model))
        if doc.get("result") != "PASS":
            reasons.append("the receipt's result is %r; only PASS qualifies" % (doc.get("result"),))
        if doc.get("context") != "launchd":
            reasons.append("the receipt was earned in context %r; launchd is required" % (doc.get("context"),))
        if not binds:
            reasons.append("the receipt has no binds")
        elif binds.get("model") != model:
            reasons.append("the receipt binds model %r, not %s" % (binds.get("model"), model))
        if surrogate is not None and binds.get("effort") != surrogate["effort"]:
            reasons.append("surrogate receipt effort must match its Claude Fable/high template")
        for key in ("effort", "permission_mode"):
            if binds and not (isinstance(binds.get(key), str) and binds[key]):
                reasons.append("binds.%s is missing" % key)
        if binds and not (isinstance(binds.get("claude_bin"), str) and os.path.isabs(binds["claude_bin"])):
            reasons.append("binds.claude_bin is not an absolute path")
        turns, seconds = binds.get("max_turns"), binds.get("deadline_seconds")
        if binds and not (_is_int(turns) and turns > 0):
            reasons.append("binds.max_turns %r is not a positive turn limit" % (turns,))
        elif binds and cap is not None and turns > cap:
            reasons.append("binds.max_turns %d exceeds the %s cap %d" % (turns, kind, cap))
        deadline = None
        if binds and not (_is_int(seconds) and seconds > 0):
            reasons.append("binds.deadline_seconds %r is not a positive wall-clock limit" % (seconds,))
        elif binds:
            deadline = deadline_text(ctx.now(), seconds)
            if deadline is None:
                reasons.append("unknown: ctx.now() gave no UTC time, so there is no deadline")
        flags, tools = binds.get("extra_flags", []), binds.get("disallowed_tools", [])
        if not _strings(flags) or not _strings(tools):
            reasons.append("binds.extra_flags or binds.disallowed_tools is not a list of strings")
        mcp = os.path.join(_path(ctx, "fleet"), "mcp.marsys-only.json" if chart is True else "mcp.none.json")
        digest = kyaction.sha_file(mcp)
        if binds and (digest is None or digest != binds.get("mcp_config_sha256")):
            reasons.append("the mcp configuration %s has sha256 %s, the receipt binds %r"
                           % (mcp, digest or "unknown (unreadable)", binds.get("mcp_config_sha256")))
        if not reasons:
            launch = {"model": model, "effort": binds["effort"], "permission_mode": binds["permission_mode"],
                      "max_turns": turns, "deadline": deadline, "claude_bin": binds["claude_bin"], "mcp_config": mcp,
                      "extra_lean_flags": list(flags), "disallowed_tools": list(tools)}
    for reason in reasons:
        _refuse(refusals, "launch", reason)
    facts["launch"] = launch if not reasons else None


def recorded_mappings(ctx):
    """({(item, head): {merge commits}}, None) from every earlier job state's prerequisites[], or (None, reason)."""
    jobs = os.path.join(_path(ctx, "run"), "jobs")
    found = {}
    try:
        import kyd_jobs
        names = kyd_jobs.job_folders(jobs)
    except FileNotFoundError:
        return found, None
    except OSError as e:
        return None, "%s cannot be listed: %s" % (jobs, type(e).__name__)
    for name in names:
        state, err = kyaction.read_json(os.path.join(jobs, name, "state.json"))
        if kyd_jobs.foreign_state(state, err):
            continue
        if err or not isinstance(state, dict) or not isinstance(state.get("prerequisites", []) or [], list):
            return None, "the job state of %s is unreadable" % name
        for p in state.get("prerequisites") or []:
            if isinstance(p, dict) and isinstance(p.get("merge_commit"), str):
                found.setdefault((p.get("item"), p.get("head")), set()).add(p["merge_commit"])
    return found, None


def _contained(ctx, commit, base):
    """True: commit is base or an ancestor of it; False: shown not to be; None: unknown."""
    rc, _, _ = _sh(ctx, [GIT, "merge-base", "--is-ancestor", commit, base], cwd=_path(ctx, "repo"))
    return None if rc is None else rc == 0


def _is_squash(ctx, commit):
    """True only for a commit of this repository with exactly one parent."""
    rc, out, _ = _sh(ctx, [GIT, "rev-list", "--parents", "-n", "1", commit + "^{commit}"], cwd=_path(ctx, "repo"))
    return rc == 0 and len(out.split()) == 2 and out.split()[0] == commit


def _judge_prerequisite(ctx, dep, base, recorded):
    """→ (entry, None) or (None, reason) for one code prerequisite against the job base (plan §5 KT-04)."""
    accepted = ctx.accepted(dep)
    if accepted is None:
        return None, "missing: %s has no accepted head; tracker readiness alone does not prove code availability" % dep
    if not isinstance(accepted, dict) or not isinstance(accepted.get("head"), str) or not SHA1_RE.match(accepted["head"]):
        return None, "unknown: the accepted head of %s is not known" % dep
    head = accepted["head"]
    pr = ctx.pr(dep)
    if pr is not None and not (isinstance(pr, dict) and isinstance(pr.get("state"), str)):
        return None, "unknown: the PR of %s is not known" % dep
    merge = None
    if pr is not None and pr["state"] == "MERGED":
        if pr.get("head") != head:
            return None, ("changed: the merged PR of %s has head %s, the accepted head is %s; its merge commit maps "
                          "another head" % (dep, pr.get("head"), head))
        merge = pr.get("merge_commit")
        if not isinstance(merge, str) or not SHA1_RE.match(merge):
            return None, "unverified: the PR of %s is MERGED and reports no merge commit" % dep
        # verified before it is used or recorded, whether or not the head itself is in the base
        if not _is_squash(ctx, merge):
            return None, ("unverified: the merge commit %s reported for %s is not a single-parent commit of this "
                          "repository" % (merge, dep))
    earlier = recorded.get((dep, head), set())
    if earlier and merge is None:
        return None, ("missing: an earlier job recorded %s → %s for %s and no such mapping is observed now"
                      % (head, ", ".join(sorted(earlier)), dep))
    if earlier - {merge}:
        return None, ("changed: an earlier job recorded %s → %s for %s, the PR now reports %s"
                      % (head, ", ".join(sorted(earlier - {merge})), dep, merge))
    entry = {"item": dep, "kind": "code", "head": head, "via": accepted.get("via"), "merge_commit": merge,
             "contained_by": None}
    inside = _contained(ctx, head, base)
    if inside is None:
        return None, "unknown: whether %s (%s) is in the base %s could not be asked" % (head, dep, base)
    if inside:
        return dict(entry, contained_by="head"), None
    if merge is None:
        return None, "missing: the accepted head %s of %s is not contained in the base %s and it has not merged" % (head, dep, base)
    inside = _contained(ctx, merge, base)
    if inside is None:
        return None, "unknown: whether the merge commit %s (%s) is in the base %s could not be asked" % (merge, dep, base)
    if not inside:
        return None, ("missing: neither the accepted head %s of %s nor its merge commit %s is contained in the base %s"
                      % (head, dep, merge, base))
    return dict(entry, contained_by="merge_commit"), None


def resolve_prerequisites(items, item, deps):
    """([(id, completion_kind)] in depth-first order, each id once; [reasons]) for the dependencies of `item`.
    An item without a completion_kind (a join or a decision) stands for what lies beneath it and is resolved through;
    the resolution stops at code (judged by the base contract) and at artifact, operation and packet items (their
    typed receipts govern). An id absent from the plan model or an unrecognised completion_kind is unknown."""
    reached, reasons, seen = [], [], set()
    stack = [(d, item) for d in reversed(deps)]
    while stack:
        dep, parent = stack.pop()
        if dep in seen:
            continue
        seen.add(dep)
        node = items.get(dep)
        if node is None:
            reasons.append("unknown: %s (a dependency of %s) is absent from the plan model" % (dep, parent))
            continue
        kind = node.get("completion_kind")
        if kind is None:
            below = node.get("depends_on")
            below = [] if below is None else below
            if not _strings(below):
                reasons.append("unknown: depends_on of %s (a dependency of %s) is not a list of item ids" % (dep, parent))
                continue
            reached.append((dep, None))
            stack.extend((d, dep) for d in reversed(below))
        elif kind in RESOLVED_KINDS:
            reached.append((dep, kind))
        else:
            reasons.append("unknown: %s (a dependency of %s) has the unrecognised completion_kind %r" % (dep, parent, kind))
    return reached, reasons


def _check_base(ctx, intent, entries, items, items_reason, refusals, facts):
    item = intent.get("item")
    if item is not None and not (isinstance(item, str) and ITEM_RE.match(item) and ".." not in item):
        _refuse(refusals, "base", "unknown: the intent's item %r is no item id" % (item,))
        return
    own = _entry_at(entries, item_worktree(item)) if item is not None else None
    base = own["head"] if own else None
    if own is None:
        rc, out, _ = _sh(ctx, [GIT, "rev-parse", "HEAD"], cwd=_path(ctx, "repo"))
        base = out.strip() if rc == 0 else None
    if entries is None or not isinstance(base, str) or not SHA1_RE.match(base):
        _refuse(refusals, "base", "unknown: the HEAD of the item worktree or of the repository could not be read")
        return
    facts["base_sha"] = base
    if items is None:
        _refuse(refusals, "base", "unknown: %s (prerequisites)" % items_reason)
        return
    if item is not None and item not in items:
        _refuse(refusals, "base", "unknown: %s is absent from the plan model" % item)
        return
    deps = (items.get(item) or {}).get("depends_on")
    deps = [] if deps is None else deps
    if not _strings(deps):
        _refuse(refusals, "base", "unknown: depends_on of %s is not a list of item ids" % item)
        return
    reached, reasons = resolve_prerequisites(items, item, deps)
    for reason in reasons:
        _refuse(refusals, "base", reason)
    if reasons:
        return
    code = [d for d, kind in reached if kind == "code"]
    recorded, reason = recorded_mappings(ctx) if code else ({}, None)
    if reason:
        _refuse(refusals, "base", "unknown: %s, so a changed head→merge mapping could not be ruled out" % reason)
        return
    out, before = [], len(refusals)
    for dep, kind in reached:
        if kind != "code":
            out.append({"item": dep, "kind": kind, "head": None, "via": None, "merge_commit": None, "contained_by": None})
            continue
        entry, reason = _judge_prerequisite(ctx, dep, base, recorded)
        if reason:
            _refuse(refusals, "base", reason)
        else:
            out.append(entry)
    if len(refusals) == before:
        facts["prerequisites"] = out


def slot_state(ctx, slot):
    """→ (state, detail, receipt path) from $KY_RUN/local_db/<slot>.json alone, nothing run:
    invalid | absent | unreadable | foreign | own_not_ready | own_ready_bad | own_ready."""
    if not isinstance(slot, str) or not SLOT_RE.match(slot):
        return "invalid", "%r is not a slot (b1..b8, v1..v8)" % (slot,), None
    path = os.path.join(_path(ctx, "run"), "local_db", slot + ".json")
    doc, err = kyaction.read_json(path)
    if err == "missing":
        return "absent", "ky_%s has no receipt" % slot, path
    session = doc.get("session_id") if isinstance(doc, dict) else None
    if err or not isinstance(doc, dict) or doc.get("schema") != SLOT_SCHEMA or doc.get("slot") != slot \
            or not (isinstance(session, str) and session):
        return "unreadable", "unknown: %s is not a readable %s receipt of %s with a session" % (path, SLOT_SCHEMA, slot), path
    if session != ctx.controller_id:
        return "foreign", "ky_%s belongs to session %s, this is %s" % (slot, session, ctx.controller_id), path
    if doc.get("result") != "READY":
        return "own_not_ready", "ky_%s is %r: %s" % (slot, doc.get("result"), doc.get("reason")), path
    seed = doc.get("seed") if isinstance(doc.get("seed"), dict) else {}
    bad = [k for k in SEED_KEYS if not (isinstance(seed.get(k), str) and SHA256_RE.match(seed[k]))]
    if bad:
        return "own_ready_bad", "the READY receipt of ky_%s binds no %s" % (slot, ", ".join(bad)), path
    mount = doc.get("mount_source")
    if not (isinstance(mount, str) and os.path.isabs(mount) and _under(mount, _path(ctx, "scratch"))):
        return "own_ready_bad", ("the mount_source %r of ky_%s is not beneath the scratch root %s"
                                 % (mount, slot, os.path.realpath(_path(ctx, "scratch")))), path
    return "own_ready", "", path


def _slot_checks_out(ctx, slot):
    """None when `bash fleet/local_db.sh check <slot>` exits 0 now, else the reason."""
    rc, out, err = _sh(ctx, ["bash", os.path.join(_path(ctx, "fleet"), "local_db.sh"), "check", slot])
    return None if rc == 0 else _said(rc, out, err, "local_db.sh check %s" % slot)


def _check_slot(ctx, slot, refusals):
    state, detail, _ = slot_state(ctx, slot)
    if state == "own_ready":
        detail = _slot_checks_out(ctx, slot)
        if detail is None:
            return
    _refuse(refusals, "slot_foreign" if state == "foreign" else "slot_not_ready", detail)


def _check_ceiling(ctx, intent, entries, refusals):
    item, locks = intent.get("item"), intent.get("locks")
    if not isinstance(item, str) or not ITEM_RE.match(item) or not isinstance(locks, list) or "item." + item not in locks:
        return
    if entries is None:
        _refuse(refusals, "ceiling", "unknown: git worktree list could not be read")
        return
    if _entry_at(entries, item_worktree(item)):
        return
    limits = ctx.limits if isinstance(ctx.limits, dict) else {}
    copies = limits.get("copies")
    if not _is_int(copies) or copies < 0:
        _refuse(refusals, "ceiling", "unknown: limits.copies is %r" % (copies,))
        return
    under = [e for e in entries if _under(e["path"], WORKTREE_ROOT)]
    own = [e for e in under if os.path.basename(e["path"]).startswith("kalayantra-")]
    if len(own) + 1 > copies:
        _refuse(refusals, "ceiling", "a new worktree would be own copy %d of at most %d" % (len(own) + 1, copies))
    if len(under) + 1 > ALL_COPIES_MAX:
        _refuse(refusals, "ceiling", "a new worktree would be copy %d of at most %d in all under %s"
                % (len(under) + 1, ALL_COPIES_MAX, WORKTREE_ROOT))


# ───────────────────────────────────────────── the three calls ─────────────────────────────────────────────

def precheck(ctx, intent, slot):
    """Read-only: every admission check that applies to the intent runs; each failure is one refusal."""
    refusals = []
    facts = {"tier": None, "launch": None, "base_sha": None, "prerequisites": [], "tests": [], "test_digests": [],
             "migration": None}
    if getattr(ctx, "next", None) is None:
        _refuse(refusals, "stale", "no fresh tracker reading this tick (ky next --json)")
    items, items_reason = model_items(ctx)
    packet, front, front_known = intent.get("packet"), None, True
    if packet is None:
        facts["tier"] = "opus"
    elif not isinstance(packet, str) or not os.path.isabs(packet):
        _refuse(refusals, "packet", "unknown: the intent's packet %r is not an absolute path" % (packet,))
        _refuse(refusals, "routing", "unknown: no packet to route")
        front_known = False
    else:
        front = _check_packet(ctx, intent, packet, refusals, facts)
        front_known = front is not None
        _check_routing(ctx, intent, packet, items, items_reason, refusals, facts)
    runner = intent.get("runner")
    if runner == "model":
        _check_launch(ctx, intent, facts["tier"], front, front_known, refusals, facts, slot)
    elif runner != "script":
        _refuse(refusals, "launch", "unknown: the intent's runner %r is neither model nor script" % (runner,))
    entries = worktrees(ctx)
    _check_base(ctx, intent, entries, items, items_reason, refusals, facts)
    if slot is not None:
        _check_slot(ctx, slot, refusals)
    _check_ceiling(ctx, intent, entries, refusals)
    return _result(refusals, facts)


def provision(ctx, slot):
    """Bring up a slot database that has no receipt or this session's non-READY one. Nothing of another session
    is adopted, reset or removed: that, an unreadable receipt and a stale READY one go to the owner-wait."""
    refusals, facts = [], {"slot": slot, "provisioned": False}
    state, detail, receipt = slot_state(ctx, slot)
    if state == "invalid":
        _refuse(refusals, "slot_not_ready", detail)
        return _result(refusals, facts)
    if state == "own_ready":
        detail = _slot_checks_out(ctx, slot)
        if detail is None:
            return _result(refusals, facts)
        state = "own_ready_bad"
    if state in ("foreign", "unreadable", "own_ready_bad"):
        word = {"foreign": "foreign", "unreadable": "unreadable", "own_ready_bad": "stale"}[state]
        ctx.awaiting("slot-db-%s-%s" % (word, slot),
                     "The slot database ky_%s cannot be used or rebuilt by this dispatcher: %s. What should happen to it?"
                     % (slot, kyaction.flat(detail, 200)),
                     [{"id": "leave", "text": "Leave it as it is; the slot stays unavailable until its session closes it."},
                      {"id": "owner-removes", "text": "The owner removes or resets it by hand; the dispatcher then provisions the slot."}],
                     [receipt], None, "unknown")
        _refuse(refusals, "slot_foreign" if state == "foreign" else "slot_not_ready", detail)
        return _result(refusals, facts)
    script = os.path.join(_path(ctx, "fleet"), "local_db.sh")
    for argv, timeout in ((["bash", script, "up", "--session", ctx.controller_id], UP_TIMEOUT_S),
                          (["bash", script, "db", slot, "--session", ctx.controller_id], DB_TIMEOUT_S)):
        rc, out, err = _sh(ctx, argv, timeout=timeout)
        if rc != 0:
            _refuse(refusals, "slot_not_ready", _said(rc, out, err, "local_db.sh " + " ".join(argv[2:4])))
            return _result(refusals, facts)
    facts["provisioned"] = True
    return _result(refusals, facts)


def _install_tests(ctx, job, commits, refusals, facts):
    """Missing test files are taken from their test commits, compared with their digests and committed alone."""
    worktree, before = job["worktree"], len(refusals)
    paths = [c["path"] for c in commits]
    for c in commits:
        target = os.path.join(worktree, c["path"])
        present = os.path.lexists(target)
        if not present:
            rc, out, err = _sh(ctx, [GIT, "checkout", c["sha"], "--", c["path"]], cwd=worktree)
            if rc != 0:
                _refuse(refusals, "tests", _said(rc, out, err, "git checkout %s -- %s" % (c["sha"], c["path"])))
                continue
        digest = kyaction.sha_file(target)
        if digest != c["digest"]:
            if not present:                 # what this call put there is taken away again; an older file is left alone
                _sh(ctx, [GIT, "rm", "-q", "-f", "--", c["path"]], cwd=worktree)
            _refuse(refusals, "tests", "%s has sha256 %s, the packet's digest is %s (%s)"
                    % (c["path"], digest or "unknown", c["digest"], "already in the branch" if present else "from its test commit"))
    if len(refusals) != before:
        return
    rc, out, err = _sh(ctx, [GIT, "status", "--porcelain", "--untracked-files=all", "--"] + paths, cwd=worktree)
    if rc != 0:
        _refuse(refusals, "tests", _said(rc, out, err, "git status"))
        return
    pending = [p for p in paths if any(line[3:] == p for line in out.splitlines())]
    if not pending:
        return
    message = "KĀLA-YANTRA v3 %s: packet tests installed at admission (plan §8.6)" % job["item"]
    for argv in ([GIT, "add", "--"] + pending, [GIT, "commit", "-q", "-m", message, "--"] + pending):
        rc, out, err = _sh(ctx, argv, cwd=worktree)
        if rc != 0:
            _refuse(refusals, "tests", _said(rc, out, err, "git " + argv[1]))
            return
    rc, out, _ = _sh(ctx, [GIT, "rev-parse", "HEAD"], cwd=worktree)
    facts["installed"], facts["commit"] = pending, out.strip() if rc == 0 and SHA1_RE.match(out.strip()) else None


def admit(ctx, job):
    """After kyd_jobs.open: the job's worktree is registered on its branch and its item lock is this controller's;
    then, for a BUILD of a feature packet, plan §8.6: install the tests, classify the current result."""
    refusals, facts = [], {"result": None, "installed": [], "commit": None}
    item, kind, locks = job.get("item"), job.get("kind"), job.get("locks")
    if not isinstance(item, str) or not ITEM_RE.match(item) or ".." in item or not isinstance(locks, list):
        _refuse(refusals, "worktree", "unknown: the job names no item or no lock list")
        return _result(refusals, facts)
    lock, holds = "item." + item, "item." + item in locks
    if holds:
        worktree, branch = job.get("worktree"), job.get("branch")
        entries = worktrees(ctx)
        entry = _entry_at(entries, worktree) if isinstance(worktree, str) and os.path.isabs(worktree) else None
        if entries is None:
            _refuse(refusals, "worktree", "unknown: git worktree list could not be read")
        elif entry is None:
            _refuse(refusals, "worktree", "%r is not a registered worktree of the repository" % (worktree,))
        elif not isinstance(branch, str) or entry["branch"] != "refs/heads/" + branch:
            _refuse(refusals, "worktree", "%s is on %s, the job's branch is %r" % (worktree, entry["branch"] or "no branch", branch))
        owner, err = kyaction.lock_owner(_path(ctx, "run"), lock)
        if err:
            _refuse(refusals, "lock", "the lock %s is %s" % (lock, "not held" if err == "missing" else "unknown: " + err))
        elif owner.get("session_or_run_id") != ctx.controller_id:
            _refuse(refusals, "lock", "the lock %s is held by %r, this controller is %s"
                    % (lock, owner.get("session_or_run_id"), ctx.controller_id))
    if refusals or kind != "BUILD" or job.get("packet_path") is None:
        return _result(refusals, facts)
    front, reason = front_matter(job["packet_path"])
    if reason:
        _refuse(refusals, "tests", "unknown: " + reason)
        return _result(refusals, facts)
    if front.get("kind") != "feature":
        return _result(refusals, facts)
    if not holds:
        _refuse(refusals, "lock", "a BUILD of a feature packet installs tests into the item worktree and the job does not hold %s" % lock)
        return _result(refusals, facts)
    commits, reason = packet_tests(front)
    if reason or not commits:
        _refuse(refusals, "tests", "unknown: " + reason if reason else "the feature packet names no test_commits: nothing can be classified")
        return _result(refusals, facts)
    digests = [c["digest"] for c in commits]
    if job.get("test_digests") is not None and job["test_digests"] != digests:
        _refuse(refusals, "tests", "changed: the job was opened with test digests %r, the packet now names %r" % (job["test_digests"], digests))
        return _result(refusals, facts)
    _install_tests(ctx, job, commits, refusals, facts)
    if refusals:
        return _result(refusals, facts)
    rc, out, err = _sh(ctx, ["bash", os.path.join(_path(ctx, "fleet"), "precheck.sh"), "--item"],
                       env={"KY_ITEM": item, "TESTS": "\n".join(c["path"] for c in commits)}, cwd=job["worktree"],
                       timeout=PRECHECK_TIMEOUT_S)
    expected = front.get("expected_failing_assertion")
    if rc == 0:
        result = "already_green"
        _refuse(refusals, "already_green", "precheck is green with the packet's tests at the base: an independent "
                "already-satisfied assessment (ARTIFACT) decides, not this admission")
    elif rc == 1 and isinstance(expected, str) and expected and expected in out + err:
        result = "expected_red"
    else:
        result = "unclassified"
        _refuse(refusals, "unclassified", "unknown: precheck could not be run or did not end" if rc is None else
                "precheck exit %d without the packet's expected failing assertion %r in its output" % (rc, expected))
    facts["result"] = result
    target = os.path.join(_path(ctx, "run"), "admission", item + ".json")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    kyaction.write_json(target, {"item": item, "base_sha": job.get("base_sha"), "test_digests": digests, "result": result})
    return _result(refusals, facts)
