#!/usr/bin/env python3
"""kyd_kinds_build.py — the dispatcher's BUILD, REWORK, STEP, VERIFY and ARTIFACT kinds (KĀLA-YANTRA v3,
relaunch plan v2.7 §6 rows BUILD … ARTIFACT and "Verdict publication (controller-owned)"; packet
KV3-B-KYDKINDS-BUILD v1). (I) marks an interpretation of this module or of its packet.

A module of kydispatch.py, which calls
    intents(ctx)          read-only: what could be started now, in the order STEP, VERIFY, ARTIFACT, REWORK, BUILD
    start(ctx, job)       after kyd_jobs.open and kyd_admit.admit: a result, or None (launch the model job)
    finish(ctx, job)      after the job's process group is gone: a result
Everything decided here is script logic over what ctx answers; no model is asked. Importing runs nothing; the
only local kyd_jobs helpers and the standard library are imported; every command goes through ctx.sh, ctx.ky or ctx.act.

ctx (built by the engine; a recording double in the tests)
    root run fleet scratch repo      absolute paths (repo: the campaign checkout)
    sh(argv, env=None, cwd=None, timeout=120) → (rc, out, err); rc None: unknown
    ky(*args, stream=None, lane=None) → (rc, out, err)
    act(id, kind, inputs, target, effect, observer) → (done | failed | unknown, result): kyaction's record around
        one side effect. effect() → (done | failed | unknown, {result}) is called only when the record says the
        effect must (still) happen; observer(record) is kyaction.reconcile's:
        ("done", {…}) | ("not_done", detail) | ("unknown", detail).
    next                             a fresh `ky next --json` ({running[], ready[], blocked[]} of item rows), or
                                     None when the tracker is stale: then nothing is intended
    events(item)                     the item's lines of EVENTS.jsonl, oldest first
    pr(item)                         {number, head, base, title, state, mergeable, merge_state,
                                     checks{name: {status, run_id, attempt}}, merge_commit, files[], auto_merge},
                                     None (no PR) or "unknown". status is the check's result (SUCCESS, FAILURE,
                                     SKIPPED, IN_PROGRESS, …); files[] holds repository-relative paths
    accepted(item)                   {head, via}, None or "unknown" (kyd_kinds_land.accepted_head)
    verify(item, step)               True, False or None: the tracker's fresh /api/verify of the step's detector
    priority[]                       item ids, first first
    journal(event, text)

Intent  {kind, item, key, stream, role, pool, runner, queue, claim, locks[], tier, not_slot, head, digest,
         verdict_phase, evidence_fp, card, packet, header{}}
    role = the kind in lower case · pool builder | verifier | null · runner model | script · claim K | V | null
    key = <kind>.<item>.<12 hex of sha256 over the canonical JSON [head or digest, evidence_fp]>
    card, packet: absolute paths · header: launch keys for the job state (loop, max_loops, pr, registered_head) and
    what the prompt and `start` need (reason, action, detail, run_ids, step, assessment, artifact_path,
    artifact_digest, author_id)
Result  {outcome, detail, failure_fp}; outcome done | blocked | failed | interrupted | refused

What the tracker's events say (pravaha_tracker/cli.py)
    a state event      kind item without `step`; the latest one is the item's state
    code registration  the latest state event is `review` with detail `PR #<n> @ <40-hex head>`
    artifact registration (I)  the latest state event is `review` with `evidence` = the artifact's absolute path
                       and `sha256 <64 hex>` in its detail (`ky review <ID> --evidence <path> --detail "… sha256 <d>"`);
                       the plan says "registers path + digest via `ky review`" and fixes no form
    verdict            kind verdict {phase, head | artifact_digest, result}; claim: kind claim {claim_id, state}

The rows
BUILD      a ready K item (completion_kind code or artifact) named in ctx.priority, in that order, with ctx.pr
           None and a packet PACKET_<ID>_v<n>.md (highest n) in repo. Whether it is unclaimed is decided by the
           claim itself: kyd_jobs.open runs `ky claim`, the only authority that reads the locked log (I).
           $KY_RUN/admission/<item>.json saying already_green: no BUILD; an ARTIFACT intent instead
           (header.assessment already_satisfied) for the admission record at its sha256, unless an artifact verdict
           at that digest exists. An unreadable admission record: neither.
REWORK     an item in review at a registered head H of its open PR (pr.head = H, pr.number as registered), not
           accepted, whose
             · latest pre_merge verdict at H is REJECTED                                      reason rejected
             · a check is FAILURE at attempt ≥ 2 (code-class, I)                              reason ci
             · diff hits an Opus rule though a Sonnet job built it (kyroute diff exit 1)      reason opus_rule
           and, artifact items of K (I): the latest artifact verdict at the registered digest is REJECTED.
           A FAILURE at attempt 1 with a run id is retried first: a script intent (header.action retry_ci) running
           `gh run rerun <run_id> --failed`. Any other failed state (CANCELLED, TIMED_OUT, a FAILURE without a run
           id or attempt, a state this table does not know): journal `unclassifiable CI failure`, nothing started.
           Tier: `kyroute.py escalate --tier T --red-loops N --max-loops M --rejected K` — CONTINUE keeps T,
           OPUS_REWORK → opus, BLOCK → a script intent (header.action block) running `ky block <ID>`.
             T  the tier of the item's last BUILD/REWORK model job that ended `done` (its state.json `model`);
                none on record → sonnet: an unknown builder gets no Opus credit (I)
             N  the unbroken run of such jobs at tier T (at least 1) — the loops this tier has used (I)
             M  the packet's max_loops, else that job's, else 2 (owner Amendment A2 D-17 §2.6)
             K  REJECTED verdicts at the heads (digests) that run produced; an `invalidated:` rejection is the
                controller's, not a reviewer's, and is not counted (I)
           header.loop = that job's loop + 1 (2 when none is on record: the head exists, so one loop has run).
STEP       an unrecorded step of a running, review or ready item whose `step_evidence` detector is not null and
           whose ctx.verify is True. A null detector, False and None (unknown) intend nothing (ruling P18).
           `start` writes $KY_RUN/jobs/<job_id>/step.json and runs `ky step <ID> <step> --evidence <that file>`.
VERIFY     as REWORK's item, with no verdict at H, and every check SUCCESS, SKIPPED or NEUTRAL, at least one
           SUCCESS (I: this repository's CI skips its jobs on a docs-only diff; a PR on which nothing ran is not
           green). `Kāla DB Tests…` (the job is named "Kāla DB Tests (throwaway Postgres)") must be present and
           SUCCESS when files[] touch platform/migrations/ or are not known; otherwise it may be absent or skipped
           (plan: "green where the diff is relevant").
           Then routing on the actual diff: `kyroute.py diff --repo R --base B --head H --built-tier T`, B =
           `git merge-base origin/<pr.base> H` (I): 0 → the VERIFY intent; 1 → an opus REWORK; 3 → a script intent
           running `ky block <ID> --detail "freeze: <path>"` (the path kyroute names; none named → nothing);
           anything else is unknown → nothing.
           evidence_fp = sha256 of {packet_sha256 (of the packet file's bytes, null without one), checks}.
ARTIFACT   an item in review whose latest review event registers a path and sha256, the file's bytes still having
           that sha256, and no artifact verdict at the digest. not_slot = the author's slot; a V claim only for a
           V-owned item; the item lock only for a K-owned item, whose artifact lives in the item worktree (I).

start      re-derives the job's intent from ctx as it is now and refuses a job whose key is no longer intended
           (the fresh look before any side effect; for STEP this is the fresh detector read). Then
             BUILD, REWORK (model)   None
             retry_ci, block, STEP   the command, inside ctx.act → done | failed
             VERIFY                  `gh pr diff <n>` → $JOB_SCRATCH/pr.diff, then the snapshot → None
                                     (a job without an absolute job_scratch or worktree is refused first)
             ARTIFACT                `kyverdicts.py snapshot --worktree W --out $JOB_SCRATCH/snapshot.json` → None
finish     BUILD, REWORK: accept a legacy lane registration after the job's claim, otherwise validate its
           result.json and observe origin head, PR head/number and packet-scoped changed paths. The controller
           writes review/block as the still-claimed job lane and reads the event back before terminal release.
           VERIFY, ARTIFACT: `bash kyboundary.sh check <job_id>`; only on exit 0 `kyverdicts.py publish …` (argv
           as the packet gives it; AU = the actor of the latest review event, RV = stream-V:<slot>). 0 → done;
           else failed, and nothing is published. A value publish needs that the job does not carry (exit code,
           result path, slot, controller) is never invented: failed, nothing published.

Journal: `unclassifiable CI failure` as above; `dispatcher error` when an input this module needs cannot be read
(a tool's exit, an unreadable job state or admission record) — the item is then skipped for this tick.
Changelog 2026-10-13: T0 controller BUILD completion, verified recovery and VERIFY registered-head guard.
Python >= 3.9.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import kyd_jobs as jobs
import kyverdicts

KINDS = ("BUILD", "REWORK", "STEP", "VERIFY", "ARTIFACT")
ORDER = ("STEP", "VERIFY", "ARTIFACT", "REWORK", "BUILD")
PACKETS = os.path.join("00_ARCHITECTURE", "briefs", "kalayantra", "packets")
CARD_BUILDER = os.path.join("cards", "KARAKA.md")
CARD_VERIFIER = os.path.join("cards", "PARIKSAKA.md")
DB_CHECK = "Kāla DB Tests"
MIGRATIONS = "platform/migrations/"
CHECK_GREEN = ("SUCCESS",)
CHECK_NOT_RUN = ("SKIPPED", "NEUTRAL")
CHECK_PENDING = ("PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED", "WAITING", "REQUESTED")
DEFAULT_MAX_LOOPS = 2  # Owner Amendment A2 D-17 §2.6 supersedes plan §8.
ASSESSMENT_AUTHOR = "dispatcher:admission"

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
HEAD_RE = re.compile(r"^[0-9a-f]{40}\Z")
REF_RE = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]{0,199}\Z")
PR_RE = re.compile(r"PR #([0-9]+) @ ([0-9a-f]{40})(?![0-9a-f])")
DIGEST_RE = re.compile(r"sha256[ :=]+([0-9a-f]{64})(?![0-9a-f])")
FRONT_RE = re.compile(r"^```json\n(.*?)\n```", re.S | re.M)


class _Unknown(Exception):
    """An input that cannot be read. The item is skipped for this tick and the reason journalled."""


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def job_key(kind, item, identity, evidence_fp):
    return "%s.%s.%s" % (kind, item, fingerprint([identity, evidence_fp])[:12])


def _result(outcome, detail, failure_fp=None):
    return {"outcome": outcome, "detail": detail, "failure_fp": failure_fp}


def _intent(kind, item, **fields):
    out = {"kind": kind, "item": item, "key": None, "stream": None, "role": kind.lower(), "pool": None,
           "runner": None, "queue": False, "claim": None, "locks": [], "tier": None, "not_slot": None, "head": None,
           "digest": None, "verdict_phase": None, "evidence_fp": None, "card": None, "packet": None, "header": {}}
    out.update(fields)
    out["key"] = job_key(kind, item, out["head"] or out["digest"], out["evidence_fp"])
    return out


# ── what lies on disk (read-only) ───────────────────────────────────────────────────────────────────────────────

def _read(path):
    """The file's bytes; None when there is no such file."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        return None
    except OSError:
        raise _Unknown("%s cannot be read" % path)


def _packet(ctx, item):
    """{path, sha256, build_tier, max_loops} of the item's packet with the highest version, or None."""
    directory = os.path.join(os.fspath(ctx.repo), PACKETS)
    name_re = re.compile(r"^PACKET_%s_v([0-9]+)\.md\Z" % re.escape(item))
    try:
        names = os.listdir(directory)
    except FileNotFoundError:
        return None
    except OSError:
        raise _Unknown("%s cannot be listed" % directory)
    versions = [(int(m.group(1)), name) for name in names for m in [name_re.match(name)] if m]
    if not versions:
        return None
    path = os.path.join(directory, max(versions)[1])
    data = _read(path)
    if data is None:
        return None
    front = {}
    match = FRONT_RE.search(data.decode("utf-8", "replace"))
    if match:
        try:
            front = json.loads(match.group(1))
        except ValueError:
            front = {}
    if not isinstance(front, dict):
        front = {}
    tier, loops = front.get("build_tier"), front.get("max_loops")
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(),
            "build_tier": tier if tier in ("sonnet", "opus") else None,
            "max_loops": loops if type(loops) is int and loops > 0 else None}


def _admission(ctx, item):
    """{path, sha256, result} of kyd_admit's classification of the item, or None when there is none."""
    path = os.path.join(os.fspath(ctx.run), "admission", item + ".json")
    data = _read(path)
    if data is None:
        return None
    try:
        doc = json.loads(data)
    except ValueError:
        doc = None
    if not isinstance(doc, dict) or doc.get("item") != item:
        raise _Unknown("admission record %s is unreadable" % path)
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "result": doc.get("result")}


def _tier_of(model):
    for tier in ("sonnet", "opus"):
        if isinstance(model, str) and tier in model:
            return tier
    return None


def _history(ctx, item):
    """The item's BUILD/REWORK model jobs that ended `done`, oldest first: [{tier, loop, max_loops, identity}]."""
    directory = os.path.join(os.fspath(ctx.run), "jobs")
    try:
        names = sorted(jobs.job_folders(directory), key=lambda n: (not n.startswith("legacy-"), n))
    except FileNotFoundError:
        return []
    except OSError:
        raise _Unknown("%s cannot be listed" % directory)
    out = []
    for name in names:
        path = os.path.join(directory, name, "state.json")
        data = _read(path) if os.path.isdir(os.path.join(directory, name)) else None
        if data is None:
            raise _Unknown("job state %s is unreadable" % path)
        try:
            state = json.loads(data)
        except ValueError:
            state = None
        if jobs.foreign_state(state, None):
            continue
        if not isinstance(state, dict):
            raise _Unknown("job state %s is unreadable" % path)
        if (state.get("item") == item and state.get("kind") in ("BUILD", "REWORK") and state.get("model")
                and state.get("outcome") == "done"):
            out.append({"tier": _tier_of(state.get("model")), "loop": state.get("loop"),
                        "max_loops": state.get("max_loops"), "identity": state.get("head") or state.get("digest")})
    return out


# ── what the tracker says ───────────────────────────────────────────────────────────────────────────────────────

def _rows(ctx):
    """item id → row (with the list it came from), in the tracker's order; None when the tracker is stale."""
    if not isinstance(ctx.next, dict):
        return None
    rows = {}
    for group in ("running", "ready", "blocked"):
        for row in ctx.next.get(group) or []:
            if isinstance(row, dict) and isinstance(row.get("id"), str) and ID_RE.match(row["id"]):
                rows.setdefault(row["id"], dict(row, _group=group))
    return rows


def _events(ctx, item):
    events = ctx.events(item)
    if not isinstance(events, list):
        raise _Unknown("the event log cannot be read")
    return [e for e in events if isinstance(e, dict)]


def _state_events(events):
    return [e for e in events if e.get("kind") == "item" and not e.get("step")]


def _registration_of(event):
    """What a review event registers: a PR head, an artifact (path, digest), or None."""
    if not event or event.get("state") != "review":
        return None
    detail = event.get("detail") if isinstance(event.get("detail"), str) else ""
    actor = event.get("actor") if isinstance(event.get("actor"), str) and event.get("actor") else None
    code = PR_RE.search(detail)
    if code:
        return {"type": "code", "pr": int(code.group(1)), "head": code.group(2), "digest": None, "path": None,
                "actor": actor, "detail": detail}
    digest, path = DIGEST_RE.search(detail), event.get("evidence")
    if digest and isinstance(path, str) and os.path.isabs(path):
        return {"type": "artifact", "pr": None, "head": None, "digest": digest.group(1), "path": path,
                "actor": actor, "detail": detail}
    return None


def _registration(events):
    states = _state_events(events)
    return _registration_of(states[-1]) if states else None


def _slot_of(actor):
    """'stream-K:b2' → 'b2'; None for an actor without a slot."""
    if isinstance(actor, str) and actor.lower().startswith("stream-") and ":" in actor:
        return actor.split(":", 1)[1] or None
    return None


def _verdicts(events, phase, head=None, digest=None):
    return [e for e in events if e.get("kind") == "verdict" and (e.get("phase") or "pre_merge") == phase
            and e.get("head") == head and e.get("artifact_digest") == digest]


def _classify(checks):
    """Check names by what their state means for the row: success, not_run, pending, retry, code, other."""
    out = {"success": [], "not_run": [], "pending": [], "retry": [], "code": [], "other": []}
    for name in sorted(checks if isinstance(checks, dict) else {}):
        check = checks[name] if isinstance(checks[name], dict) else {}
        status, attempt, run_id = check.get("status"), check.get("attempt"), _run_id(check.get("run_id"))
        if status in CHECK_GREEN:
            out["success"].append(name)
        elif status in CHECK_NOT_RUN:
            out["not_run"].append(name)
        elif status in CHECK_PENDING:
            out["pending"].append(name)
        elif status == "FAILURE" and type(attempt) is int and attempt >= 2:
            out["code"].append(name)
        elif status == "FAILURE" and attempt == 1 and type(attempt) is int and run_id:
            out["retry"].append(name)
        else:
            out["other"].append(name)
    return out


def _run_id(value):
    if type(value) is int and value > 0:
        return str(value)
    return value if isinstance(value, str) and value.isdigit() else None


def _db_tests_green(pr):
    checks = pr.get("checks")
    db = [name for name in checks if name.startswith(DB_CHECK)]
    files = pr.get("files")
    if isinstance(files, list):
        paths = [f.get("path") if isinstance(f, dict) else f for f in files]
        relevant = any(not isinstance(p, str) or p.startswith(MIGRATIONS) for p in paths)
    else:
        relevant = True                                     # the diff is not known: the check must have run
    if not relevant:
        return True                                         # absent or skipped is fine; a failure never gets here
    return bool(db) and all(checks[name].get("status") == "SUCCESS" for name in db)


# ── intents ─────────────────────────────────────────────────────────────────────────────────────────────────────

def intents(ctx):
    """Read-only: every job of these kinds that could be started now."""
    import kyd_admit
    kyd_admit.refresh_job_engine(ctx)
    return _compute(ctx, None)


def _compute(ctx, only):
    rows = _rows(ctx)
    if rows is None:
        return []
    out = []
    for item, row in rows.items():
        if only is not None and item != only:
            continue
        try:
            out.extend(_steps(ctx, row))
            out.extend(_in_review(ctx, row))
        except _Unknown as exc:
            ctx.journal("dispatcher error", "%s: %s" % (item, exc))
    order = {}
    for position, item in enumerate(ctx.priority if isinstance(ctx.priority, list) else []):
        order.setdefault(item, position)
    for item in sorted((i for i in rows if i in order), key=order.get):
        if only is not None and item != only:
            continue
        try:
            out.extend(_ready(ctx, rows[item]))
        except _Unknown as exc:
            ctx.journal("dispatcher error", "%s: %s" % (item, exc))
    return sorted(out, key=lambda intent: ORDER.index(intent["kind"]))


def _fleet(ctx, *parts):
    return os.path.join(os.fspath(ctx.fleet), *parts)


def _steps(ctx, row):
    item, owner = row["id"], row.get("owner")
    if row.get("status") not in ("running", "review", "ready") or not isinstance(owner, str) or not owner:
        return []
    detectors = row.get("step_evidence") if isinstance(row.get("step_evidence"), dict) else {}
    out = []
    for step in row.get("steps") if isinstance(row.get("steps"), list) else []:
        name = step.get("name") if isinstance(step, dict) else None
        if not isinstance(name, str) or not ID_RE.match(name) or step.get("done") is not False:
            continue
        declared = detectors.get(name)
        if declared is None or (isinstance(declared, dict) and "detector" in declared
                                and declared["detector"] is None):  # real model: {evidence, detector}; null is P18's wait
            continue
        if ctx.verify(item, name) is not True:
            continue
        out.append(_intent("STEP", item, stream=owner, runner="script", header={"step": name},
                           evidence_fp=fingerprint({"step": name})))
    return out


def _in_review(ctx, row):
    if row.get("status") != "review":
        return []
    events = _events(ctx, row["id"])
    registration = _registration(events)
    if registration is None:
        return []
    if registration["type"] == "code":
        return _code(ctx, row, events, registration)
    return _artifact(ctx, row, events, registration)


def _code(ctx, row, events, reg):
    item, head = row["id"], reg["head"]
    pr = ctx.pr(item)
    if not isinstance(pr, dict) or pr.get("state") != "OPEN" or pr.get("number") != reg["pr"]:
        return []
    if pr.get("head") != head:
        return _changed_registration(ctx, row, reg, pr)
    if ctx.accepted(item) is not None:                      # accepted (MERGE's business) or unknown
        return []
    packet = _packet(ctx, item)
    at_head = _verdicts(events, "pre_merge", head=head)
    if at_head:
        if at_head[-1].get("result") == "REJECTED":
            return _rework(ctx, row, events, reg, packet, "rejected", {"verdict": at_head[-1].get("ts")})
        return []                                           # a verdict exists at this head
    checks = pr.get("checks") if isinstance(pr.get("checks"), dict) else {}
    ci = _classify(checks)
    if ci["other"]:
        ctx.journal("unclassifiable CI failure", "%s PR #%d @ %s: %s" % (item, reg["pr"], head, ", ".join(
            "%s=%s" % (name, (checks[name] or {}).get("status") if isinstance(checks[name], dict) else None)
            for name in ci["other"])))
        return []
    if ci["code"]:
        return _rework(ctx, row, events, reg, packet, "ci", {"checks": {n: checks[n] for n in ci["code"]}})
    if ci["retry"]:
        run_ids = sorted({_run_id(checks[name]["run_id"]) for name in ci["retry"]}, key=int)
        return [_intent("REWORK", item, stream=row.get("owner"), runner="script", head=head,
                        evidence_fp=fingerprint({"action": "retry_ci", "checks": {n: checks[n] for n in ci["retry"]}}),
                        header={"action": "retry_ci", "run_ids": run_ids, "pr": reg["pr"], "registered_head": head})]
    if ci["pending"] or not ci["success"] or not _db_tests_green(pr):
        return []
    # routing runs again on the actual diff before VERIFY (plan §9)
    history = _history(ctx, item)
    built = (history[-1]["tier"] if history else None) or "sonnet"
    base_ref = pr.get("base")
    if not isinstance(base_ref, str) or not REF_RE.match(base_ref):
        raise _Unknown("PR base %r is not a branch name" % (base_ref,))
    rc, out, _ = ctx.sh(["git", "-C", os.fspath(ctx.repo), "merge-base", "origin/" + base_ref, head])
    base = out.strip() if isinstance(out, str) else ""
    if rc != 0 or not HEAD_RE.match(base):
        raise _Unknown("git merge-base origin/%s exit %r" % (base_ref, rc))
    rc, out, _ = ctx.sh(["python3", "-B", _fleet(ctx, "kyroute.py"), "diff", "--repo", os.fspath(ctx.repo),
                         "--base", base, "--head", head, "--built-tier", built])
    if rc == 0:
        return [_intent("VERIFY", item, stream="V", pool="verifier", runner="model",
                        claim="V" if row.get("owner") == "V" else None, locks=["item." + item], tier="opus",
                        not_slot=_slot_of(reg["actor"]), head=head, verdict_phase="pre_merge",
                        evidence_fp=fingerprint({"packet_sha256": packet["sha256"] if packet else None,
                                                 "checks": checks}),
                        card=_fleet(ctx, CARD_VERIFIER), packet=packet["path"] if packet else None,
                        header={"pr": reg["pr"], "registered_head": head})]
    if rc == 1:                                             # the Sonnet diff is preserved; Opus assesses it
        return _rework(ctx, row, events, reg, packet, "opus_rule", {"base": base}, history=history, tier="opus")
    if rc == 3:
        frozen = _frozen_path(out)
        if frozen is None:
            raise _Unknown("kyroute diff exit 3 names no frozen path")
        return [_block("VERIFY", row, head, "freeze: " + frozen)]
    raise _Unknown("kyroute diff exit %r" % (rc,))


class _ReviewedGit:
    """Read-only ctx adapter: reviewed-patch observations always cover ALL paths."""
    def __init__(self, ctx):
        self.ctx = ctx

    def __call__(self, *args):
        rc, out, _ = self.ctx.sh(["git", "-C", os.fspath(self.ctx.repo), *args],
                                 env={"GIT_OPTIONAL_LOCKS": "0"})
        if rc is None or not isinstance(out, str) or "\ufffd" in out:
            raise _Unknown("reviewed patch Git observation unavailable")
        return rc, out.encode("utf-8")

    def ok(self, *args):
        rc, out = self(*args)
        if rc != 0:
            raise _Unknown("reviewed patch git %s exit %s" % (args[0], rc))
        return out


def _reviewed_patch(ctx, packet, old, new, base_ref):
    """Re-register only an identical WHOLE patch whose changed paths all belong to the packet.

    (I) INTERPRETATION: compare full binary diffs exactly, retaining full blob ids because ctx.sh
    decodes text. Unlike verdict inheritance, re-registration permits an identical rebased patch
    and must not write merge-tree objects. Empty patches or lossy observations stay unknown.
    """
    if not packet:
        return "scope_unknown"
    # front_matter is the existing strict packet reader; no prose-derived path guesses.
    import kyd_admit
    front, error = kyd_admit.front_matter(packet["path"])
    paths = front.get("d1_paths") if isinstance(front, dict) else None
    if (error or not isinstance(paths, list) or not paths
            or not all(isinstance(p, str) and p and not os.path.isabs(p)
                       and not any(x in ("", ".", "..") for x in p.split("/"))
                       and not re.search(r"[\\*?\[\]\x00]", p) for p in paths)):
        return "scope_unknown"
    if (not isinstance(old, str) or not HEAD_RE.match(old)
            or not isinstance(new, str) or not HEAD_RE.match(new)
            or not isinstance(base_ref, str) or not REF_RE.match(base_ref)):
        return "unknown_commit"
    git = _ReviewedGit(ctx)
    if not kyverdicts._is_commit(git, old) or not kyverdicts._is_commit(git, new):
        return "unknown_commit"
    # Pin the observed remote base once; never fetch or fall back to a local branch.
    rc, out = git("rev-parse", "--verify", "origin/" + base_ref + "^{commit}")
    main = out.decode("ascii", "replace").strip()
    if rc != 0 or not HEAD_RE.match(main):
        return "unproven_base"
    old_base = kyverdicts._derived_base(git, main, old)
    new_base = kyverdicts._derived_base(git, main, new)
    if not old_base or not new_base or old_base == old or new_base == new:
        return "unproven_base"
    diff_args = ("diff", "--binary", "--full-index", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames")
    old_patch = git.ok(*diff_args, old_base, old, "--")
    new_patch = git.ok(*diff_args, new_base, new, "--")
    if not old_patch.strip():
        return "unproven_base"
    if not kyverdicts._same_patch(old_patch, new_patch):
        return "patch_differs"
    for base, head in ((old_base, old), (new_base, new)):
        changed = git.ok("diff", "--name-only", "--no-renames", "-z", base, head, "--")
        if changed and not changed.endswith(b"\0"):
            raise _Unknown("reviewed patch changed paths unavailable")
        names = changed[:-1].decode("utf-8").split("\0") if changed else []
        if any(name not in paths for name in names):
            return "paths_outside_scope"
    return "identical_patch"


def _changed_registration(ctx, row, reg, pr):
    packet = _packet(ctx, row["id"])
    try:
        reason = _reviewed_patch(ctx, packet, reg["head"], pr.get("head"), pr.get("base"))
    except (_Unknown, kyverdicts._GitFailed):
        reason = "git_failed"
    if reason != "identical_patch":
        # Existing changed-head path remains unknown; never pretend the old review covers new code.
        ctx.journal("review head unknown", "%s: registered %s, PR %s: %s"
                    % (row["id"], reg["head"], pr.get("head"), reason))
        return []
    if not reg.get("actor") or not _slot_of(reg["actor"]):
        raise _Unknown("review author has no lane; cannot preserve independence in re-registration")
    return [_intent("REWORK", row["id"], stream=row.get("owner"), runner="script",
                    locks=["item." + row["id"]], head=pr["head"],
                    evidence_fp=fingerprint({"old_head": reg["head"], "packet_sha256": packet["sha256"],
                                             "author": reg["actor"], "pr": reg["pr"]}),
                    packet=packet["path"], header={"action": "reregister_review", "registered_head": reg["head"],
                                                  "pr": reg["pr"], "author_id": reg["actor"]})]


def _reregister_review(ctx, job, intent):
    item, old, new = intent["item"], intent["header"]["registered_head"], intent["head"]
    author = intent["header"]["author_id"]
    stream = author.split(":", 1)[0][7:]
    lane = _slot_of(author)
    detail = "PR #%d @ %s" % (intent["header"]["pr"], new)

    def observer(record):
        reg = _registration(_events(ctx, item))
        pr = ctx.pr(item)
        if not isinstance(pr, dict) or pr.get("head") != new or pr.get("number") != intent["header"]["pr"]:
            return "unknown", {"reason": "PR changed during re-registration"}
        if reg and reg["head"] == new and reg["actor"] == author and reg["detail"] == detail:
            return "done", {"detail": detail}
        return "not_done", {"reason": "new registration not observed"}

    def effect():
        current = next((i for i in _compute(ctx, item) if i["key"] == intent["key"]), None)
        if current is None:
            return "unknown", {"reason": "registration inputs changed"}
        # Controller action preserves original builder attribution, so its lane remains excluded from VERIFY.
        rc, _, _ = ctx.ky("review", item, "--detail", detail, stream=stream, lane=lane)
        status, value = observer(None)
        return ("done" if status == "done" else "failed" if rc not in (None, 0) else "unknown"), value

    status, result = ctx.act("ACT-reregister-" + job["job_id"], "review_reregistration",
                             {"item": item, "old_head": old, "new_head": new, "author": author,
                              "packet_sha256": _packet(ctx, item)["sha256"]},
                             {"item": item, "pr": intent["header"]["pr"], "head": new}, effect, observer)
    if status == "done" and observer(None)[0] != "done":
        status = "unknown"
    ctx.journal("review re-registration", "%s %s → %s: %s (original author %s)" % (item, old, new, status, author))
    return _acted(status, result, "review_reregistration")


def _frozen_path(out):
    try:
        doc = json.loads(out)
    except (TypeError, ValueError):
        return None
    paths = doc.get("frozen") if isinstance(doc, dict) else None
    if isinstance(paths, list) and paths and isinstance(paths[0], str) and paths[0].strip():
        return paths[0].strip()
    return None


def _block(kind, row, identity, detail):
    return _intent(kind, row["id"], stream=row.get("owner"), runner="script",
                   head=identity if HEAD_RE.match(identity or "") else None,
                   digest=None if HEAD_RE.match(identity or "") else identity,
                   evidence_fp=fingerprint({"action": "block", "detail": detail}),
                   header={"action": "block", "detail": detail})


def _rework(ctx, row, events, reg, packet, reason, basis, history=None, tier=None):
    item = row["id"]
    if packet is None or row.get("owner") != "K":           # a builder job needs its packet; K builds
        return []
    if history is None:
        history = _history(ctx, item)
    identity = reg["head"] or reg["digest"]
    last = history[-1] if history else None
    current = (last["tier"] if last else None) or "sonnet"
    run = []
    for job in reversed(history):
        if (job["tier"] or "sonnet") != current:
            break
        run.insert(0, job)
    last_loops = last["max_loops"] if last and type(last["max_loops"]) is int and last["max_loops"] > 0 else None
    max_loops = packet["max_loops"] or last_loops or DEFAULT_MAX_LOOPS
    loop = (last["loop"] if last and type(last["loop"]) is int and last["loop"] > 0 else max(len(history), 1)) + 1
    if tier is None:
        loops = max(len(run), 1)
        produced = {job["identity"] for job in run[1:]} | {identity}
        rejected = sum(1 for e in events if e.get("kind") == "verdict" and e.get("result") == "REJECTED"
                       and (e.get("head") or e.get("artifact_digest")) in produced
                       and not str(e.get("detail") or "").startswith("invalidated:"))
        rc, out, _ = ctx.sh(["python3", "-B", _fleet(ctx, "kyroute.py"), "escalate", "--tier", current,
                             "--red-loops", str(loops), "--max-loops", str(max_loops), "--rejected", str(rejected)])
        try:
            decision = json.loads(out).get("decision") if rc == 0 else None
        except (TypeError, ValueError, AttributeError):
            decision = None
        if decision == "BLOCK":
            return [_block("REWORK", row, identity, "escalation: %s tier, %d of %d loops, %d rejected"
                           % (current, loops, max_loops, rejected))]
        if decision not in ("CONTINUE", "OPUS_REWORK"):
            raise _Unknown("kyroute escalate gave no decision (exit %r)" % (rc,))
        tier = "opus" if decision == "OPUS_REWORK" else current
    header = {"loop": loop, "max_loops": max_loops, "reason": reason}
    if reg["type"] == "code":
        header.update(pr=reg["pr"], registered_head=reg["head"])
    return [_intent("REWORK", item, stream="K", pool="builder", runner="model", claim="K", locks=["item." + item],
                    tier=tier, head=reg["head"], digest=reg["digest"],
                    evidence_fp=fingerprint({"packet_sha256": packet["sha256"], "reason": reason, "basis": basis}),
                    card=_fleet(ctx, CARD_BUILDER), packet=packet["path"], header=header)]


def _artifact_intent(ctx, row, packet, path, digest, author, extra=None):
    item, owner = row["id"], row.get("owner")
    header = dict(extra or {}, artifact_path=path, artifact_digest=digest, author_id=author)
    return _intent("ARTIFACT", item, stream="V", pool="verifier", runner="model",
                   claim="V" if owner == "V" else None, locks=["item." + item] if owner == "K" else [],
                   tier="opus", not_slot=_slot_of(author), digest=digest, verdict_phase="artifact",
                   evidence_fp=fingerprint({"packet_sha256": packet["sha256"] if packet else None, "path": path}),
                   card=_fleet(ctx, CARD_VERIFIER), packet=packet["path"] if packet else None, header=header)


def _artifact(ctx, row, events, reg):
    item, digest = row["id"], reg["digest"]
    packet = _packet(ctx, item)
    judged = _verdicts(events, "artifact", digest=digest)
    if judged:
        if judged[-1].get("result") == "REJECTED":
            return _rework(ctx, row, events, reg, packet, "rejected", {"verdict": judged[-1].get("ts")})
        return []
    data = _read(reg["path"])
    if data is None or hashlib.sha256(data).hexdigest() != digest:
        return []                                           # the registered bytes are not there (any more)
    return [_artifact_intent(ctx, row, packet, reg["path"], digest, reg["actor"])]


def _ready(ctx, row):
    """BUILD, or the already-satisfied assessment in its place."""
    item = row["id"]
    if row.get("owner") == "K" and row.get("completion_kind") == "code" and row.get("status") in ("ready", "running"):
        recovery = _recovery(ctx, row)
        if recovery:
            return [recovery]
    if (row.get("status") != "ready" or row.get("owner") != "K"
            or row.get("completion_kind") not in ("code", "artifact")):
        return []
    if ctx.pr(item) is not None:                            # an open PR, or unknown
        return []
    packet = _packet(ctx, item)
    if packet is None:
        return []
    admission = _admission(ctx, item)
    if admission and admission["result"] == "already_green":
        if _verdicts(_events(ctx, item), "artifact", digest=admission["sha256"]):
            return []
        return [_artifact_intent(ctx, row, packet, admission["path"], admission["sha256"], ASSESSMENT_AUTHOR,
                                 {"assessment": "already_satisfied"})]
    return [_intent("BUILD", item, stream="K", pool="builder", runner="model", claim="K", locks=["item." + item],
                    tier=packet["build_tier"], evidence_fp=fingerprint({"packet_sha256": packet["sha256"]}),
                    card=_fleet(ctx, CARD_BUILDER), packet=packet["path"],
                    header={"loop": 1, "max_loops": packet["max_loops"] or DEFAULT_MAX_LOOPS})]


# ── start ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _job_scratch(job):
    path = job.get("job_scratch")
    return path if isinstance(path, str) and os.path.isabs(path) else None


def _write(path, data):
    temporary = "%s.tmp.%d" % (path, os.getpid())
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _acted(status, result, what):
    detail = json.dumps(result, ensure_ascii=False, sort_keys=True)[:300] if result else what
    if status == "done":
        return _result("done", "%s: %s" % (what, detail))
    return _result("failed", "%s %s: %s" % (what, status, detail),
                   "%s_%s" % (what, "failed" if status == "failed" else "unknown"))


def _command(reply, **more):
    """A command's exit as an effect's answer: 0 done, None unknown, anything else failed."""
    rc, out, err = reply
    status = "done" if rc == 0 else "unknown" if rc is None else "failed"
    return status, dict(more, exit=rc, err=(err or "").strip()[:200] if isinstance(err, str) else "")


def start(ctx, job):
    """A result, or None to launch the model job."""
    kind, item, job_id = job.get("kind"), job.get("item"), job.get("job_id")
    if kind not in KINDS or not isinstance(item, str) or not isinstance(job_id, str) or not ID_RE.match(job_id):
        return _result("refused", "not a job of this module: kind %r, item %r, job %r" % (kind, item, job_id),
                       "not_this_module")
    intent = next((i for i in _compute(ctx, item) if i["kind"] == kind and i["key"] == job.get("key")), None)
    if intent is None:
        return _result("refused", "%s %s is no longer intended: its trigger changed since admission" % (kind, item),
                       "intent_not_current")
    action = intent["header"].get("action")
    if action == "reregister_review":
        return _reregister_review(ctx, job, intent)
    if action == "recover_review":
        return _recover_review(ctx, job, intent)
    if action == "block":
        return _start_block(ctx, job, intent)
    if action == "retry_ci":
        return _start_retry(ctx, job, intent)
    if kind == "STEP":
        return _start_step(ctx, job, intent)
    if kind in ("BUILD", "REWORK"):
        return None
    scratch = _job_scratch(job)
    if scratch is None:
        return _result("refused", "the job carries no absolute job_scratch", "job_scratch_unknown")
    if kind == "VERIFY":
        rc, out, _ = ctx.sh(["gh", "pr", "diff", str(intent["header"]["pr"])], cwd=os.fspath(ctx.repo))
        if rc != 0 or not isinstance(out, str):
            return _result("refused", "gh pr diff %d exit %r" % (intent["header"]["pr"], rc), "pr_diff_unavailable")
        _write(os.path.join(scratch, "pr.diff"), out.encode("utf-8"))
    worktree = job.get("worktree")
    if not isinstance(worktree, str) or not os.path.isabs(worktree):
        return _result("refused", "the job carries no absolute worktree", "worktree_unknown")
    rc, _, _ = ctx.sh(["python3", "-B", _fleet(ctx, "kyverdicts.py"), "snapshot", "--worktree", worktree,
                       "--out", os.path.join(scratch, "snapshot.json")])
    if rc != 0:
        return _result("refused", "kyverdicts snapshot exit %r" % (rc,), "snapshot_unavailable")
    return None


def _start_block(ctx, job, intent):
    item, detail = intent["item"], intent["header"]["detail"]

    def effect():
        return _command(ctx.ky("block", item, "--detail", detail, stream=intent["stream"], lane=None))

    def observer(record):
        states = _state_events(_events(ctx, item))
        if states and states[-1].get("state") == "blocked":
            return "done", {"state": "blocked", "detail": states[-1].get("detail")}
        return "not_done", "the item's latest state is not blocked"

    status, result = ctx.act("ACT-block-" + job["job_id"], "block", {"item": item, "detail": detail},
                             {"item": item, "state": "blocked"}, effect, observer)
    return _acted(status, result, "block")


def _start_retry(ctx, job, intent):
    item, run_ids = intent["item"], intent["header"]["run_ids"]

    def effect():
        for run_id in run_ids:
            status, result = _command(ctx.sh(["gh", "run", "rerun", run_id, "--failed"], cwd=os.fspath(ctx.repo)),
                                      run_id=run_id)
            if status != "done":
                return status, result
        return "done", {"run_ids": run_ids}

    def observer(record):
        pr = ctx.pr(item)
        if not isinstance(pr, dict) or not isinstance(pr.get("checks"), dict):
            return "unknown", "the PR's checks cannot be read"
        first = {_run_id(c.get("run_id")) for c in pr["checks"].values()
                 if isinstance(c, dict) and c.get("status") == "FAILURE" and c.get("attempt") == 1}
        if set(run_ids) <= first:
            return "not_done", "every run is still a failure at attempt 1"
        return "unknown", "the runs have moved on; whether by this action cannot be told"

    status, result = ctx.act("ACT-retryci-" + job["job_id"], "retry_ci",
                             {"item": item, "pr": intent["header"]["pr"], "head": intent["head"], "run_ids": run_ids},
                             {"pr": intent["header"]["pr"], "head": intent["head"]}, effect, observer)
    return _acted(status, result, "retry_ci")


def _start_step(ctx, job, intent):
    item, step, job_id = intent["item"], intent["header"]["step"], job["job_id"]
    directory = os.path.join(os.fspath(ctx.run), "jobs", job_id)
    evidence = os.path.join(directory, "step.json")
    # the intent was re-derived a moment ago, so ctx.verify(item, step) has just answered True
    os.makedirs(directory, exist_ok=True)
    _write(evidence, json.dumps({"schema": "ky.step_evidence/1", "job_id": job_id, "item": item, "step": step,
                                 "detector_passed": True, "detector": "ctx.verify (tracker /api/verify)",
                                 "key": intent["key"]}, ensure_ascii=False, sort_keys=True, indent=1).encode("utf-8")
           + b"\n")

    def effect():
        return _command(ctx.ky("step", item, step, "--evidence", evidence, stream=intent["stream"], lane=None))

    def observer(record):
        for event in _events(ctx, item):
            if event.get("kind") == "item" and event.get("step") == step and event.get("state") == "done":
                return "done", {"step": step, "recorded_at": event.get("ts")}
        return "not_done", "no event records the step"

    status, result = ctx.act("ACT-step-" + job_id, "step", {"item": item, "step": step, "evidence": evidence},
                             {"item": item, "step": step}, effect, observer)
    return _acted(status, result, "step")


# ── finish ──────────────────────────────────────────────────────────────────────────────────────────────────────

def finish(ctx, job):
    """The row's post-action, once the job's process group is gone."""
    kind = job.get("kind")
    if kind in ("BUILD", "REWORK"):
        return _post_action(ctx, job)
    if kind in ("VERIFY", "ARTIFACT"):
        return _publish(ctx, job)
    return _result("failed", "%r has no post-action in this module" % (kind,), "not_this_module")


def _post_action(ctx, job):
    """BUILD and REWORK must end in `ky review` with a registration, or in `ky block`; else interrupted."""
    item, claim_id = job.get("item"), job.get("claim_id")
    lane = "stream-%s:%s" % (job.get("stream"), job.get("slot"))
    try:
        events = _events(ctx, item)
    except _Unknown as exc:
        return _result("interrupted", str(exc), "events_unreadable")
    anchor = next((n for n, e in enumerate(events) if e.get("kind") == "claim" and claim_id
                   and e.get("claim_id") == claim_id and e.get("state") == "acquired"), None)
    if anchor is None:
        return _result("interrupted", "the job's claim is not in the event log: nothing can be attributed to it",
                       "no_claim_event")
    mine = [e for e in _state_events(events[anchor + 1:]) if e.get("actor") == lane]
    last = mine[-1] if mine else None
    if last and last.get("state") == "blocked":
        return _result("blocked", str(last.get("detail") or "blocked"))
    registration = _registration_of(last)
    if registration:
        return _result("done", registration["detail"])
    scratch = _job_scratch(job)
    if scratch and os.path.lexists(os.path.join(scratch, "result.json")):
        doc = jobs.read_result(job)
        if doc is None:
            return _result("interrupted", "result.json is invalid or names another job/item", "job_result_invalid")
        return _register_result(ctx, job, doc)
    return _result("interrupted", "%s wrote neither a review registration nor a block after its claim" % lane,
                   "no_post_action")


def _held_claim(ctx, job):
    """The controller registers only while this exact job still holds its lane claim."""
    slot = job.get("slot")
    if not isinstance(slot, str) or not ID_RE.match(slot) or job.get("stream") != "K":
        return False
    path = os.path.join(os.fspath(ctx.run), "claims", slot + ".json")
    try:
        doc = json.loads(_read(path) or b"null")
    except (ValueError, _Unknown):
        return False
    return (isinstance(doc, dict) and doc.get("item") == job.get("item")
            and doc.get("worker_id") == slot and doc.get("claim_id") == job.get("claim_id")
            and doc.get("state") in ("acquired", "renewed"))


def _review_problem(ctx, job, doc):
    """Observe origin, the existing PR reader and the job's packet-scoped diff; never trust a reported head.

    (I) INTERPRETATION: scope is the exact packet d1_paths, measured from the recorded job base, not the
    entire PR diff (bootstrap PRs also contain the installed assembly base). Unknown scope refuses.
    """
    branch, head, pr = doc.get("branch"), doc.get("head_sha"), doc.get("pr_number")
    if (not isinstance(branch, str) or not REF_RE.match(branch) or ".." in branch
            or not isinstance(head, str) or not HEAD_RE.match(head) or type(pr) is not int or pr < 1):
        return "review_identity_missing", "done result must name branch, full head_sha and pr_number"
    if branch != job.get("branch"):
        return "review_branch_mismatch", "result branch differs from the assigned branch"
    rc, out, _ = ctx.sh(["git", "-C", os.fspath(ctx.repo), "ls-remote", "origin", "refs/heads/" + branch])
    rows = [line.split() for line in out.splitlines()] if isinstance(out, str) else []
    if rc != 0 or rows != [[head, "refs/heads/" + branch]]:
        return "review_origin_head_mismatch", "origin branch does not observably equal result head_sha"
    observed = ctx.pr(job["item"])
    if not isinstance(observed, dict):
        return "review_pr_missing", "the existing PR reader could not observe the reported PR"
    if observed.get("number") != pr:
        return "review_pr_number_mismatch", "observed PR number differs from result pr_number"
    if observed.get("head") != head:
        return "review_pr_head_mismatch", "PR headRefOid differs from result head_sha"
    if observed.get("state") != "OPEN":
        return "review_pr_not_open", "reported PR is not open"
    try:
        data = _read(job.get("packet_path"))
        match = FRONT_RE.search(data.decode("utf-8")) if data else None
        front = json.loads(match.group(1)) if match else {}
        allowed = front.get("d1_paths")
    except (TypeError, ValueError, UnicodeError, _Unknown):
        allowed = None
    if (not isinstance(allowed, list) or not allowed or not all(isinstance(p, str) and p
            and not os.path.isabs(p) and ".." not in p.split("/") for p in allowed)
            or not isinstance(job.get("base_sha"), str) or not HEAD_RE.match(job["base_sha"])):
        return "review_scope_unknown", "packet d1_paths or recorded job base cannot be verified"
    rc, out, _ = ctx.sh(["git", "-C", os.fspath(ctx.repo), "diff", "--name-only", "--no-renames", "-z",
                         job["base_sha"], head, "--"])
    if rc != 0 or not isinstance(out, str) or (out and not out.endswith("\0")):
        return "review_paths_unknown", "changed paths could not be observed"
    changed = out[:-1].split("\0") if out else []
    outside = [p for p in changed if p not in allowed]
    if outside:
        return "review_paths_outside_scope", "changed paths outside packet d1_paths: " + ", ".join(outside)
    return None


def _register_result(ctx, job, doc, source=None):
    """Controller-owned, action-recorded registration, read back before success or claim release."""
    if not _held_claim(ctx, job):
        return _result("interrupted", "the job's exact lane claim is not held", "claim_not_held")
    try:
        events = _events(ctx, job["item"])
    except _Unknown as exc:
        return _result("interrupted", str(exc), "events_unreadable")
    if not any(e.get("kind") == "claim" and e.get("claim_id") == job["claim_id"]
               and e.get("state") == "acquired" for e in events):
        return _result("interrupted", "the job's claim is not in the event log", "no_claim_event")
    if doc["status"] == "blocked":
        verb, detail, state = "block", doc["blocked_reason"], "blocked"
    elif doc["status"] == "done":
        problem = _review_problem(ctx, source or job, doc)
        if problem:
            return _result("interrupted", problem[1], problem[0])
        verb, detail, state = "review", "PR #%d @ %s" % (doc["pr_number"], doc["head_sha"]), "review"
    else:
        return _result("interrupted", "builder result status is failed", "job_result_failed")
    lane = "stream-%s:%s" % (job["stream"], job["slot"])

    def observer(record):
        events = _events(ctx, job["item"])
        anchor = next((n for n, e in enumerate(events) if e.get("kind") == "claim"
                       and e.get("claim_id") == job["claim_id"] and e.get("state") == "acquired"), None)
        last = _state_events(events[anchor + 1:]) if anchor is not None else []
        if last and last[-1].get("actor") == lane and last[-1].get("state") == state and last[-1].get("detail") == detail:
            return "done", {"event": last[-1]}
        return "not_done", "no matching registration after this job's claim"

    def effect():
        if not _held_claim(ctx, job):
            return "unknown", {"reason": "claim changed before registration"}
        rc, _, _ = ctx.ky(verb, job["item"], "--detail", detail, stream=job["stream"], lane=job["slot"])
        observed, event = observer(None)
        if observed == "done":
            return "done", event
        return "unknown" if rc is None or rc == 0 else "failed", {"exit": rc}

    status, _ = ctx.act("ACT-%s-%s" % (verb, job["job_id"]), "ky_" + verb,
                       {"item": job["item"], "claim_id": job["claim_id"], "detail": detail,
                        "source_job": (source or job)["job_id"]},
                       {"item": job["item"], "actor": lane, "state": state}, effect, observer)
    if status != "done" or observer(None)[0] != "done":
        return _result("interrupted", "controller %s was not observed in the tracker" % verb,
                       verb + "_event_not_observed")
    jobs.record_registration(ctx, job, doc, source)
    return _result("done" if state == "review" else "blocked", detail)


def _recovery(ctx, row):
    """(I) INTERPRETATION: a fresh script BUILD reclaims ended no_post_action work; no third model build.
    The key binds the source result and current packet, so the old interruption limit cannot mask recovery.
    Invalid results are never repaired or inferred from the PR. Recheck every observation at start.
    """
    directory = os.path.join(os.fspath(ctx.run), "jobs")
    try:
        names = sorted(jobs.job_folders(directory), reverse=True)
    except FileNotFoundError:
        return None
    for name in names:
        path = os.path.join(directory, name, "state.json")
        if not os.path.isdir(os.path.dirname(path)):
            continue
        try:
            old = json.loads(_read(path) or b"null")
        except ValueError:
            continue  # cannot recover an unreadable state; ordinary BUILD keeps its existing selection rules
        if jobs.foreign_state(old, None):
            continue
        if (not isinstance(old, dict) or old.get("item") != row["id"] or old.get("kind") not in ("BUILD", "REWORK")
                or old.get("phase") != "ended" or old.get("outcome") != "interrupted"
                or old.get("failure_fp") != "no_post_action"):
            continue
        doc = jobs.read_result(old)
        if not doc or doc["status"] != "done" or jobs._process(old) != "gone":
            continue
        packet = _packet(ctx, row["id"])
        if not packet or packet["path"] != old.get("packet_path") or _review_problem(ctx, old, doc):
            continue
        return _intent("BUILD", row["id"], stream="K", pool="builder", runner="script", claim="K",
                       locks=["item." + row["id"]], tier=packet["build_tier"], head=doc["head_sha"],
                       evidence_fp=fingerprint({"recovery_job": name, "result": doc, "packet_sha256": packet["sha256"]}),
                       card=_fleet(ctx, CARD_BUILDER), packet=packet["path"],
                       header={"action": "recover_review", "source_job": name, "branch": doc["branch"],
                               "pr": doc["pr_number"], "model": old.get("model"),
                               "loop": old.get("loop"), "max_loops": old.get("max_loops")})
    return None


def _recover_review(ctx, job, intent):
    old = next((j for j in jobs.load(ctx) if j["job_id"] == intent["header"]["source_job"]), None)
    doc = jobs.read_result(old) if old else None
    if not doc or doc["status"] != "done" or jobs._process(old) != "gone":
        return _result("interrupted", "recovery source is no longer verifiable", "recovery_source_changed")
    return _register_result(ctx, job, doc, source=old)


def _publish(ctx, job):
    """Verdict publication is the controller's: boundary evidence first, then kyverdicts.py publish."""
    kind, item, job_id = job.get("kind"), job.get("item"), job.get("job_id")
    scratch = _job_scratch(job)
    if scratch is None or not isinstance(job_id, str) or not ID_RE.match(job_id) or not isinstance(item, str):
        return _result("failed", "the job carries no absolute job_scratch or no job id: nothing published",
                       "job_scratch_unknown")
    steps = (job.get("checkpoint") or {}).get("steps") or {}
    released = job.get("phase") == "ended" and "boundary" in steps
    # (I) INTERPRETATION: terminal release removes the verifier view. Replaying check would destroy its
    # original attestation. For an ended/released job, publish validates the preserved boundary evidence
    # and freshly observes the worktree against the pre-job snapshot; never rebuild a verifier view here.
    if not released:
        rc, _, _ = ctx.sh(["bash", _fleet(ctx, "kyboundary.sh"), "check", job_id])
        if rc != 0:
            return _result("failed", "kyboundary check exit %r: nothing published" % (rc,),
                           "boundary_violated" if rc == 1 else "boundary_unknown")
    phase = {"VERIFY": "pre_merge", "ARTIFACT": "artifact"}[kind]
    try:
        events = _events(ctx, item)
    except _Unknown as exc:
        return _result("failed", "%s: nothing published" % exc, "events_unreadable")
    registration = _registration(events)
    if kind == "VERIFY":
        head = job.get("head")
        author = registration["actor"] if (registration and registration["type"] == "code"
                                           and registration["head"] == head) else None
        identity = ["--head", head] if isinstance(head, str) and HEAD_RE.match(head) else None
    else:
        digest, path, author = job.get("digest"), None, None
        if registration and registration["type"] == "artifact" and registration["digest"] == digest:
            path, author = registration["path"], registration["actor"]
        else:
            try:
                admission = _admission(ctx, item)
            except _Unknown:
                admission = None
            if admission and admission["result"] == "already_green" and admission["sha256"] == digest:
                path, author = admission["path"], ASSESSMENT_AUTHOR
        identity = ["--artifact-digest", digest, "--artifact-path", path] if digest and path else None
    if identity is None or not author:
        return _result("failed", "what the job reviewed is no longer what the item registers: nothing published",
                       "registration_changed")
    slot, worktree, exit_code = job.get("slot"), job.get("worktree"), job.get("exit_code")
    # Older prepared/ended states did not carry this lifecycle value. The prompt has always named this
    # file; keep its identity even when absent or invalid so publish can report the precise requirement.
    result_path = job.get("result_path") or os.path.join(scratch, "result.json")
    controller = job.get("controller_id")
    if (job.get("verdict_phase") != phase or not isinstance(slot, str) or not slot
            or not isinstance(worktree, str) or not os.path.isabs(worktree) or type(exit_code) is not int
            or not isinstance(result_path, str) or not os.path.isabs(result_path)
            or not isinstance(controller, str) or not controller):
        return _result("failed", "the job state lacks a value publication needs (phase, slot, worktree, exit code, "
                                 "result path or controller): nothing published", "publish_inputs_unknown")
    rc, out, _ = ctx.sh(["python3", "-B", _fleet(ctx, "kyverdicts.py"), "publish", "--job-id", job_id, "--item", item,
                         "--phase", phase] + identity +
                        ["--vslot", slot, "--author-id", author, "--reviewer-id", "stream-V:" + slot,
                         "--worktree", worktree, "--snapshot", os.path.join(scratch, "snapshot.json"),
                         "--job-exit", str(exit_code), "--result", result_path,
                         "--boundary", os.path.join(scratch, "boundary.check.json"), "--as", controller])
    if rc == 0:
        return _result("done", "verdict published for %s (%s)" % (item, phase))
    try:
        said = json.loads(out)
    except (ValueError, TypeError):
        said = None
    reasons = said.get("reasons") if isinstance(said, dict) else None
    if (isinstance(reasons, list) and reasons
            and all(isinstance(r, str) and re.fullmatch(r"[a-z][a-z0-9_]*", r) for r in reasons)):
        return _result("failed", "kyverdicts publish exit %r: %s: nothing published" % (rc, ", ".join(reasons)),
                       "publish_" + reasons[0])
    return _result("failed", "kyverdicts publish exit %r: nothing published" % (rc,), "publish_exit_%s" % (rc,))
