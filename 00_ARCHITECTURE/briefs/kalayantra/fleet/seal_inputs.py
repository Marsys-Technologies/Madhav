#!/opt/homebrew/bin/python3
"""seal_inputs — the input-freshness detectors that stand between a century dispatch / a seal and a stale or foreign input
(BEFORE SEAL, FOLLOWUPS M-W34-07; #3817's dispatch rule; SR-XC-FREEZE-482012f1 = CCD-028).  stdlib only; never calls gh, gcloud or a database.

THE DEFECT.  `implementation_digest.lock.json` is a CI-GENERATED output (platform/scripts/governance/ci_generated.py OUTPUTS; SR-CHURN-CUT 3): the copy committed on main is stale by
design, and the seal workflow replaces it with the lock inside the verified `ci-generated` artifact of a successful ci.yml run for the sealing commit
(.github/actions/apply-generated-overlay).  The seal job then recomputes the digest of the code it runs and refuses (exit 4, own_checkout_digest_mismatch) unless it equals that
lock.  The v1.6 rehearsal measured the committed lock (5721a21c…) differing from the seal job's own digest (e69fdec4… at 8039fe276): the seal would have refused on the
committed lock.  Nothing here edits the lock: the refresh IS the CI regeneration on the sealing commit, so the seal path must REQUIRE a fresh CI artifact for that exact commit.

  seal_inputs_fresh(commit, …)  FRESH only when, for THIS commit: (ci_green) a completed, successful ci.yml run exists; (artifact_present) the run the overlay action would pick has a
                                `ci-generated` artifact that is not expired; (artifact_margin) it stays unexpired for min_remaining_hours more; (artifact_from_selected_run) the
                                directory under test was downloaded from that very run; (overlay_verified) the checkout's OWN apply_generated_overlay.py accepts it (manifest bound to the
                                commit, every byte, the full declared set, nothing extra); (lock_equals_seal_digests) the lock the artifact carries equals the digests of the modules the seal job
                                will import, computed from the checkout (the COMMITTED lock is never the comparand); (checkout_is_commit) HEAD is the commit and the tree is clean;
                                (commit_on_main) the commit is an ancestor of origin/main.
  dispatch_gate(commit, …)      #3817: dispatch only at a commit whose PUSH-to-main ci.yml run is green (the newest such run) AND whose ci-generated artifact exists, unexpired (and
                                for min_remaining_hours more) — the seal overlay lookup requires it.
  freeze_start / freeze_end     the SR-XC-FREEZE-482012f1 START / END events, appended to the campaign ledger (run/DECISIONS_SURROGATE.jsonl) — see "FREEZE LEDGER" below.

Every check is True, False or None (None = could not be measured: a missing evidence document, a digest runner that failed).  A verdict is FRESH only when EVERY check is True; a
None is a HOLD with a named reason, never a pass (root CLAUDE.md §N.8, §N.7.6).  The detectors are PURE over evidence documents (GitHub REST payloads as `gh api` prints them, an
extracted artifact directory, a checkout): `gh_commands()` lists the exact read-only calls and `collect_evidence()` runs them through a runner the CALLER supplies, so the dispatch
chain and the seal controller call these functions; this module never reaches the network itself.

FREEZE LEDGER (CCD-028 in CROSS_CUTTING_DECISION_REGISTER_v1_0.md; ruling SR-XC-FREEZE-482012f1, under SR-BEFORE-SEAL item 4; "recorded in the KĀLA-YANTRA ledger at dispatch, and the
W3W4 lease row carries the same note; the END event at seal, or at an abandoned/aborted window; until START exists the freeze is announced, not in force").  The ledger is the campaign
ledger `$KY_RUN/DECISIONS_SURROGATE.jsonl`, an append-only JSON-lines file.  WHO MAY WRITE: only the governed controller code that runs on the cockpit (`by` in WRITERS: the cockpit
launcher, the dispatch chain, the seal controller, the owner surrogate acting through one of them) — never a build/verify job, whose box has no write access to run/.  A START is
written only against a passing, untampered, recent dispatch_gate verdict for that commit; an END(SEALED) only against the seal controller's own SEALED.json for that commit; an
END(ABANDONED|ABORTED) only with a stated reason.  The lease-row note is returned as text (`lease_note`): the lease table lives on origin/campaign-coordination, which this module does not push to.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "ky.seal_inputs/1"
CI_WORKFLOW = "ci.yml"
ARTIFACT = "ci-generated"
REPO_SLUG = "Marsys-Technologies/Madhav"                  # fleet/github_run_readback.py REPO
LOCK_REL = "platform/python-sidecar/services/gochara_kernel/implementation_digest.lock.json"
OVERLAY_TOOL = "platform/scripts/governance/apply_generated_overlay.py"
SIDECAR_REL = "platform/python-sidecar"
LOCK_SCHEMA = "gochara_implementation_registry/1"          # services/gochara_kernel/implementation_registry.py SCHEMA
DEFAULT_MIN_REMAINING_HOURS = 72                          # (I) the artifact's retention is 90 days (ci.yml); the seal runs hours-to-days after dispatch
GATE_MAX_AGE_MINUTES = 30                                 # (I) a START is written at the dispatch, not off an old verdict

CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
FREEZE_AUTHORITY = "SR-XC-FREEZE-482012f1"
FREEZE_CCD = "CCD-028"
LEDGER_NAME = "DECISIONS_SURROGATE.jsonl"
WRITERS = ("cockpit", "dispatch-chain", "seal-controller", "owner-surrogate")
END_OUTCOMES = ("SEALED", "ABANDONED", "ABORTED")
SEAL_SCHEMA = "ky.seal_controller/1"                      # fleet/seal_controller.py SCHEMA (emit_final writes SEALED.json)

_SHA = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_GEN = re.compile(r"[0-9A-Za-z._-]{1,40}")


# ── helpers ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def utc(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def canon(v) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def parse_ts(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else None


def verdict(detector: str, commit: str, checks: dict, reasons: dict, evidence: dict, now: dt.datetime | None) -> dict:
    """ok only when every check is True.  A check that is not True always carries a reason (a HOLD is never silent)."""
    ok = bool(checks) and all(v is True for v in checks.values())
    why = [f"{k}: {reasons.get(k) or ('not measured' if v is None else 'failed')}" for k, v in checks.items() if v is not True]
    doc = {"schema": SCHEMA, "detector": detector, "commit": commit, "ok": ok, "status": "FRESH" if ok else "HOLD", "checks": checks, "reasons": why,
           "evidence": evidence, "evaluated_at": utc(now)}
    doc["verdict_sha256"] = verdict_digest(doc)
    return doc


def verdict_digest(doc: dict) -> str:
    return sha256_text(canon({k: v for k, v in doc.items() if k != "verdict_sha256"}))


# ── evidence: GitHub runs and artifacts (pure parsing; the fetch is the caller's) ─────────────────────────────────────────────────

def runs_of(doc) -> list[dict] | None:
    """The ci.yml run objects of `gh api …/actions/workflows/ci.yml/runs?head_sha=…` — one page, a list of pages (--paginate), or a bare list.  None when unreadable."""
    pages = doc if isinstance(doc, list) and doc and all(isinstance(p, dict) and "workflow_runs" in p for p in doc) else [doc]
    runs: list = []
    for page in pages:
        if isinstance(page, dict) and isinstance(page.get("workflow_runs"), list):
            runs += page["workflow_runs"]
        elif isinstance(page, list):
            runs += page
        else:
            return None
    if not all(isinstance(r, dict) and isinstance(r.get("id"), int) and not isinstance(r.get("id"), bool) for r in runs):
        return None
    return [r for r in runs if r.get("path") in (None, ".github/workflows/" + CI_WORKFLOW)]


def artifacts_of(doc) -> list[dict] | None:
    pages = doc if isinstance(doc, list) else [doc]
    out: list = []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("artifacts"), list):
            return None
        out += page["artifacts"]
    return out if all(isinstance(a, dict) for a in out) else None


def push_main_green(commit: str, runs: list[dict]) -> tuple[bool | None, str, dict | None]:
    """The NEWEST ci.yml run that is a push to main for `commit` must be completed + success (a re-run keeps its run id; a later red push run is the commit's CI)."""
    mine = [r for r in runs if r.get("head_sha") == commit and r.get("event") == "push" and r.get("head_branch") == "main"]
    if not mine:
        return False, "no push-to-main ci.yml run exists for this commit (a pull_request run or another branch's run is not main's CI)", None
    newest = sorted(mine, key=lambda r: (str(r.get("created_at") or ""), r["id"]))[-1]
    if newest.get("status") != "completed":
        return False, f"the newest push-main run {newest['id']} is {newest.get('status')!r}, not completed", newest
    if newest.get("conclusion") != "success":
        return False, f"the newest push-main run {newest['id']} concluded {newest.get('conclusion')!r}, not success", newest
    return True, f"push-main run {newest['id']} succeeded", newest


def select_overlay_run(commit: str, runs: list[dict], artifacts_by_run: dict, now: dt.datetime) -> tuple[dict, dict | None, dict | None]:
    """The run the seal's apply-generated-overlay action would take: in the order GitHub listed them, the first completed+success ci.yml run for `commit` whose
    `ci-generated` artifact is not expired (action.yml: `r.head_sha === sha && completed && success`, then `a.name === 'ci-generated' && !a.expired`).
    → ({ci_green, artifact_present, …: bool|None, "reasons": {check: text}}, run, artifact)."""
    res: dict = {"reasons": {}}
    good = [r for r in runs if r.get("head_sha") == commit and r.get("status") == "completed" and r.get("conclusion") == "success"]
    res["ci_green"] = bool(good)
    if not good:
        res["reasons"]["ci_green"] = "no completed, successful ci.yml run exists for this commit"
        res["artifact_present"] = False
        res["reasons"]["artifact_present"] = "no successful ci.yml run, so no ci-generated artifact the seal overlay could use"
        return res, None, None
    for run in good:
        key = str(run["id"])
        if key not in artifacts_by_run:
            res["artifact_present"] = None
            res["reasons"]["artifact_present"] = f"no artifact listing was supplied for run {run['id']}"
            return res, run, None
        arts = artifacts_of(artifacts_by_run[key])
        if arts is None:
            res["artifact_present"] = None
            res["reasons"]["artifact_present"] = f"the artifact listing of run {run['id']} is unreadable"
            return res, run, None
        for art in arts:
            if art.get("name") == ARTIFACT and art.get("expired") is False:
                res["artifact_present"] = True
                return res, run, art
    res["artifact_present"] = False
    res["reasons"]["artifact_present"] = f"no successful run of this commit carries a non-expired {ARTIFACT} artifact"
    return res, good[0], None


def margin_check(art: dict | None, now: dt.datetime, hours: float) -> tuple[bool | None, str]:
    if art is None:
        return False, "no artifact to measure"
    exp = parse_ts(art.get("expires_at"))
    if exp is None:
        return None, "the artifact states no readable expires_at"
    left = (exp - now).total_seconds() / 3600
    if left < hours:
        return False, f"the artifact expires {art['expires_at']}, {left:.1f} h from now, under the {hours} h the seal may still need"
    return True, f"{left:.1f} h remain"


# ── the detectors ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def dispatch_gate(commit: str, *, runs_doc, artifacts_by_run: dict, now: dt.datetime | None = None,
                  min_remaining_hours: float = DEFAULT_MIN_REMAINING_HOURS) -> dict:
    """#3817: dispatch only at a commit whose push-main CI is green AND whose ci-generated artifact exists, unexpired (the seal overlay lookup requires it)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    checks: dict = {}
    reasons: dict = {}
    ev: dict = {"workflow": CI_WORKFLOW, "artifact": ARTIFACT, "min_remaining_hours": min_remaining_hours}
    checks["commit_wellformed"] = bool(isinstance(commit, str) and _SHA.fullmatch(commit))
    reasons["commit_wellformed"] = "the commit is not a 40-hex sha"
    runs = runs_of(runs_doc) if checks["commit_wellformed"] else None
    if runs is None:
        for k in ("push_main_ci_green", "artifact_present", "artifact_margin"):
            checks[k], reasons[k] = None, "the ci.yml run evidence is unreadable or was not supplied"
        return verdict("dispatch_gate", str(commit), checks, reasons, ev, now)
    g, why, run = push_main_green(commit, runs)
    checks["push_main_ci_green"], reasons["push_main_ci_green"] = g, why
    ev["push_main_run"] = run["id"] if run else None
    sel, orun, art = select_overlay_run(commit, runs, artifacts_by_run, now)
    checks["artifact_present"] = sel["artifact_present"]
    reasons["artifact_present"] = sel["reasons"].get("artifact_present", "")
    checks["artifact_margin"], reasons["artifact_margin"] = margin_check(art, now, min_remaining_hours)
    ev["overlay_run"] = orun["id"] if orun else None
    ev["artifact_id"] = art.get("id") if art else None
    ev["artifact_expires_at"] = art.get("expires_at") if art else None
    return verdict("dispatch_gate", commit, checks, reasons, ev, now)


def git_run(checkout, args: list[str]) -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        p = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, timeout=120, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return p.returncode, p.stdout.strip()


def default_digest_runner(checkout) -> dict | None:
    """The seal job's OWN digests, computed exactly as `implementation_registry.compute()` does (window_gate.implementation_digest over input_vector.IMPLEMENTATION_MODULES)
    in a fresh interpreter rooted at the checkout's sidecar.  None when it cannot run (a missing module raises 'cannot be located')."""
    code = ("import sys, json; sys.path.insert(0, sys.argv[1]); "
            "from services.gochara_kernel import implementation_registry as r; print(json.dumps(r.compute(), sort_keys=True))")
    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(Path(checkout) / SIDECAR_REL)], capture_output=True, text=True, timeout=300,
                           env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    try:
        doc = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None
    return doc if isinstance(doc, dict) else None


def default_overlay_runner(checkout, artifact_dir, commit) -> tuple[int, str]:
    """Run THE CHECKOUT'S OWN apply_generated_overlay.py (what the seal job runs) against the artifact, into a scratch root that is discarded."""
    tool = Path(checkout) / OVERLAY_TOOL
    if not tool.is_file():
        return 127, f"{OVERLAY_TOOL} is missing from the checkout"
    with tempfile.TemporaryDirectory(prefix="seal-inputs-overlay-") as root:
        try:
            p = subprocess.run([sys.executable, "-I", "-B", str(tool), "--artifact", str(artifact_dir), "--sha", commit, "--root", root],
                               capture_output=True, text=True, timeout=300, env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 127, str(exc)
    return p.returncode, (p.stderr.strip() or p.stdout.strip())[-600:]


def seal_inputs_fresh(commit: str, *, checkout, artifact_dir, downloaded_run_id, runs_doc, artifacts_by_run: dict, now: dt.datetime | None = None,
                      min_remaining_hours: float = DEFAULT_MIN_REMAINING_HOURS, main_ref: str = "origin/main",
                      digest_runner=None, overlay_runner=None, git=None) -> dict:
    """The implementation lock the seal job will see equals the digests of the code the seal job runs, on a fresh CI artifact of this exact commit."""
    now = now or dt.datetime.now(dt.timezone.utc)
    digest_runner = digest_runner or default_digest_runner
    overlay_runner = overlay_runner or default_overlay_runner
    git = git or (lambda args: git_run(checkout, args))
    checks: dict = {}
    reasons: dict = {}
    ev: dict = {"workflow": CI_WORKFLOW, "artifact": ARTIFACT, "checkout": str(checkout), "artifact_dir": str(artifact_dir), "min_remaining_hours": min_remaining_hours}
    names = ("ci_green", "artifact_present", "artifact_margin", "artifact_from_selected_run", "overlay_verified", "lock_equals_seal_digests", "checkout_is_commit", "commit_on_main")
    if not (isinstance(commit, str) and _SHA.fullmatch(commit)):
        return verdict("seal_inputs_fresh", str(commit), {"commit_wellformed": False}, {"commit_wellformed": "the commit is not a 40-hex sha"}, ev, now)
    runs = runs_of(runs_doc)
    if runs is None:
        for k in ("ci_green", "artifact_present", "artifact_margin", "artifact_from_selected_run"):
            checks[k], reasons[k] = None, "the ci.yml run evidence is unreadable or was not supplied"
        run = art = None
    else:
        sel, run, art = select_overlay_run(commit, runs, artifacts_by_run, now)
        for k in ("ci_green", "artifact_present"):
            checks[k], reasons[k] = sel[k], sel["reasons"].get(k, "")
        checks["artifact_margin"], reasons["artifact_margin"] = margin_check(art, now, min_remaining_hours)
        if run is None or art is None:
            checks["artifact_from_selected_run"], reasons["artifact_from_selected_run"] = False, "no overlay run could be selected"
        else:
            checks["artifact_from_selected_run"] = str(downloaded_run_id) == str(run["id"])
            reasons["artifact_from_selected_run"] = f"the directory under test came from run {downloaded_run_id!r}; the seal overlay would take run {run['id']}"
        ev["overlay_run"] = run["id"] if run else None
        ev["artifact_id"] = art.get("id") if art else None
        ev["artifact_expires_at"] = art.get("expires_at") if art else None
    # the artifact is accepted by the checkout's own overlay tool: bound to the commit, every byte, the declared set, nothing extra
    if not Path(artifact_dir).is_dir():
        checks["overlay_verified"], reasons["overlay_verified"] = False, f"{artifact_dir} is not a directory"
    else:
        rc, text = overlay_runner(checkout, artifact_dir, commit)
        checks["overlay_verified"] = None if rc == 127 else rc == 0
        reasons["overlay_verified"] = text or f"apply_generated_overlay exit {rc}"
    # the lock the artifact carries vs the digests of the code the seal job will import
    carried = None
    if checks["overlay_verified"] is True:
        try:
            carried = json.loads((Path(artifact_dir) / LOCK_REL).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            carried = None
    if checks["overlay_verified"] is not True:
        checks["lock_equals_seal_digests"], reasons["lock_equals_seal_digests"] = None if checks["overlay_verified"] is None else False, "the artifact is not verified, so its lock is not read"
    elif not (isinstance(carried, dict) and carried.get("schema") == LOCK_SCHEMA and isinstance(carried.get("implementation_digest"), str) and isinstance(carried.get("stages"), dict)):
        checks["lock_equals_seal_digests"], reasons["lock_equals_seal_digests"] = False, "the artifact carries no readable gochara_implementation_registry/1 lock"
    else:
        own = digest_runner(checkout)
        if not (isinstance(own, dict) and isinstance(own.get("implementation_digest"), str) and isinstance(own.get("stages"), dict)):
            checks["lock_equals_seal_digests"], reasons["lock_equals_seal_digests"] = None, "the seal job's own module digests could not be computed from the checkout"
        else:
            ev["lock_implementation_digest"], ev["seal_job_implementation_digest"] = carried["implementation_digest"], own["implementation_digest"]
            differ = sorted(s for s in set(carried["stages"]) | set(own["stages"]) if carried["stages"].get(s) != own["stages"].get(s))
            checks["lock_equals_seal_digests"] = carried["implementation_digest"] == own["implementation_digest"] and not differ
            reasons["lock_equals_seal_digests"] = (f"the CI lock registers {carried['implementation_digest']}, the seal job's code digests to {own['implementation_digest']} (stages differing: {differ}):"
                                                   " the seal would refuse (own_checkout_digest_mismatch)")
    # the checkout is the commit and is clean; the commit is on main (the workflow's 'Bind to the reviewed sealing revision')
    rc, head = git(["rev-parse", "HEAD"])
    rc2, dirty = git(["status", "--porcelain"])
    if rc != 0 or rc2 != 0:
        checks["checkout_is_commit"], reasons["checkout_is_commit"] = None, "git could not read the checkout"
    else:
        checks["checkout_is_commit"] = head == commit and dirty == ""
        reasons["checkout_is_commit"] = f"checkout HEAD is {head}" if head != commit else "the checkout has uncommitted or untracked files"
    rc3, _ = git(["merge-base", "--is-ancestor", commit, main_ref])
    checks["commit_on_main"] = None if rc3 not in (0, 1) else rc3 == 0
    reasons["commit_on_main"] = f"{commit} is not an ancestor of {main_ref}" if rc3 == 1 else f"git merge-base failed (exit {rc3})"
    rc4, committed = git(["show", f"{commit}:{LOCK_REL}"])
    with contextlib.suppress(ValueError):
        ev["committed_lock_implementation_digest"] = json.loads(committed).get("implementation_digest") if rc4 == 0 else None   # informational: stale by design (SR-CHURN-CUT 3)
    return verdict("seal_inputs_fresh", commit, {k: checks[k] for k in names}, reasons, ev, now)


# ── evidence collection: the read-only calls, run through the CALLER'S runner ────────────────────────────────────────────────────────

def gh_commands(commit: str, repo: str = REPO_SLUG, run_id=None, dest=None) -> dict:
    """The exact read-only `gh` calls (argv lists) that produce the evidence — the caller runs them (this module never does)."""
    cmds = {"runs": ["gh", "api", "--paginate", "--slurp", f"repos/{repo}/actions/workflows/{CI_WORKFLOW}/runs?head_sha={commit}&per_page=100"]}
    if run_id is not None:
        cmds["artifacts"] = ["gh", "api", "--paginate", "--slurp", f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"]
        if dest is not None:
            cmds["download"] = ["gh", "run", "download", str(run_id), "--repo", repo, "-n", ARTIFACT, "-D", str(dest)]
    return cmds


def collect_evidence(commit: str, runner, dest, repo: str = REPO_SLUG, now: dt.datetime | None = None) -> dict:
    """runner(argv) -> (rc, stdout).  Fetches the runs and every successful run's artifact listing; downloads the selected run's artifact into `dest` (must not exist or be empty).
    → {runs_doc, artifacts_by_run, downloaded_run_id}  (downloaded_run_id None when nothing was selected)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    rc, out = runner(gh_commands(commit, repo)["runs"])
    if rc != 0:
        raise RuntimeError(f"runs query failed (exit {rc})")
    runs_doc = json.loads(out)
    runs = runs_of(runs_doc) or []
    by_run: dict = {}
    for r in runs:
        if r.get("head_sha") == commit and r.get("status") == "completed" and r.get("conclusion") == "success":
            rc, out = runner(gh_commands(commit, repo, run_id=r["id"])["artifacts"])
            if rc != 0:
                raise RuntimeError(f"artifact listing of run {r['id']} failed (exit {rc})")
            by_run[str(r["id"])] = json.loads(out)
    _, run, art = select_overlay_run(commit, runs, by_run, now)
    downloaded = None
    if run is not None and art is not None:
        dest = Path(dest)
        if dest.exists() and any(dest.iterdir()):
            raise RuntimeError(f"{dest} is not empty: an artifact is extracted into a fresh directory only")
        rc, _ = runner(gh_commands(commit, repo, run_id=run["id"], dest=dest)["download"])
        if rc != 0:
            raise RuntimeError(f"artifact download of run {run['id']} failed (exit {rc})")
        downloaded = run["id"]
    return {"runs_doc": runs_doc, "artifacts_by_run": by_run, "downloaded_run_id": downloaded}


# ── the XC-FREEZE ledger events ────────────────────────────────────────────────────────────────────────────────────────────────────

class LedgerRefused(Exception):
    pass


def _ledger_path(p: Path) -> None:
    if p.name != LEDGER_NAME:
        raise LedgerRefused(f"{p.name!r} is not the campaign ledger {LEDGER_NAME}")
    if not p.is_file():
        raise LedgerRefused(f"the campaign ledger {p} is missing (a freeze event never creates the ledger)")


def read_ledger(path) -> list[dict]:
    p = Path(path)
    out = []
    _ledger_path(p)
    for n, raw in enumerate(p.read_bytes().split(b"\n"), 1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw.decode("utf-8"))
        except ValueError:
            raise LedgerRefused(f"ledger line {n} is not JSON: the freeze state cannot be read") from None
        if not isinstance(obj, dict):
            raise LedgerRefused(f"ledger line {n} is not an object: the freeze state cannot be read")
        out.append(obj)
    return out


def freeze_state(path, chart_id: str = CANONICAL_CHART) -> dict:
    """Replay the chart's freeze events.  state: NONE | IN_FORCE (START without END) | ENDED | UNKNOWN (an order the writers cannot produce — nothing is written over it)."""
    events = [e for e in read_ledger(path) if e.get("kind") == "freeze event" and e.get("authority") == FREEZE_AUTHORITY and e.get("chart_id") == chart_id]
    state: dict = {"state": "NONE", "open": None, "starts": 0, "last": None, "problems": []}
    for e in events:
        if e.get("event") == "START":
            if state["state"] == "IN_FORCE":
                state["problems"].append(f"START {e.get('id')} while {state['open'].get('id')} is open")
            state.update(state="IN_FORCE", open=e, starts=state["starts"] + 1)
        elif e.get("event") == "END":
            if state["state"] != "IN_FORCE" or e.get("generation") != state["open"].get("generation"):
                state["problems"].append(f"END {e.get('id')} without a matching open START")
            else:
                state.update(state="ENDED", open=None)
        else:
            state["problems"].append(f"unknown freeze event {e.get('event')!r}")
        state["last"] = e
    if state["problems"]:
        state["state"] = "UNKNOWN"
    return state


def lease_note(event: dict) -> str:
    """The note the W3W4 lease row carries beside the ledger event (CCD-028: 'the W3W4 lease row carries the same note')."""
    if event["event"] == "START":
        return (f"{FREEZE_AUTHORITY} ({FREEZE_CCD}) IN FORCE from {event['ts']}: no L1 rebuild, registry change or corpus change for chart {event['chart_id']} "
                f"(generation {event['generation']}, dispatch commit {event['commit'][:12]}) until the END event at seal or at an abandoned/aborted window.")
    return (f"{FREEZE_AUTHORITY} ({FREEZE_CCD}) ENDED {event['ts']} ({event['outcome']}) for chart {event['chart_id']}, generation {event['generation']}: "
            "L1 rebuilds, registry and corpus changes for this chart are no longer frozen by it.")


def _append(path: Path, obj: dict) -> None:
    """One line, one write, fsynced; an unterminated last line never swallows it (kyveto.append_line's discipline)."""
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND)
    try:
        size = os.fstat(fd).st_size
        if size:
            with open(path, "rb") as f:
                f.seek(size - 1)
                if f.read(1) != b"\n":
                    data = b"\n" + data
        if os.write(fd, data) != len(data):
            raise OSError(f"short append to {path}")
        os.fsync(fd)
    finally:
        os.close(fd)


@contextlib.contextmanager
def _locked(path: Path):
    with open(path.with_name("." + path.name + ".freeze.lock"), "a+") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        yield


def _common(path, chart_id, generation, commit, by):
    _ledger_path(Path(path))
    if chart_id != CANONICAL_CHART:
        raise LedgerRefused(f"the freeze covers chart {CANONICAL_CHART} only, not {chart_id!r}")
    if by not in WRITERS:
        raise LedgerRefused(f"{by!r} may not write freeze events (governed writers: {', '.join(WRITERS)})")
    if not (isinstance(generation, str) and _GEN.fullmatch(generation)):
        raise LedgerRefused("the generation is missing or has unsafe characters")
    if not (isinstance(commit, str) and _SHA.fullmatch(commit)):
        raise LedgerRefused("the commit is not a 40-hex sha")


def freeze_start(path, *, chart_id: str, generation: str, commit: str, gate: dict, by: str, now: dt.datetime | None = None) -> dict:
    """Append the START event, only against a passing, untampered, recent dispatch_gate verdict for `commit`.  Exactly once per freeze: the same (generation, commit) while
    IN_FORCE is ALREADY (nothing written); any other START while a freeze is open, or over an UNKNOWN history, is refused."""
    now = now or dt.datetime.now(dt.timezone.utc)
    path = Path(path)
    _common(path, chart_id, generation, commit, by)
    if not (isinstance(gate, dict) and gate.get("schema") == SCHEMA and gate.get("detector") == "dispatch_gate"):
        raise LedgerRefused("no dispatch_gate verdict: a freeze starts only at a dispatch that passed the gate")
    if gate.get("verdict_sha256") != verdict_digest(gate):
        raise LedgerRefused("the dispatch_gate verdict does not match its own digest (altered after it was measured)")
    if gate.get("ok") is not True or gate.get("commit") != commit:
        raise LedgerRefused(f"the dispatch_gate verdict is not a pass for {commit} (status {gate.get('status')!r}, commit {gate.get('commit')!r})")
    at = parse_ts(gate.get("evaluated_at"))
    if at is None or not (dt.timedelta(0) <= now - at <= dt.timedelta(minutes=GATE_MAX_AGE_MINUTES)):
        raise LedgerRefused(f"the dispatch_gate verdict is not from the last {GATE_MAX_AGE_MINUTES} minutes (evaluated_at {gate.get('evaluated_at')!r})")
    with _locked(path):
        st = freeze_state(path, chart_id)
        if st["state"] == "UNKNOWN":
            raise LedgerRefused("the ledger's freeze history is inconsistent: " + "; ".join(st["problems"]))
        if st["state"] == "IN_FORCE":
            o = st["open"]
            if o.get("generation") == generation and o.get("commit") == commit:
                return {"result": "ALREADY", "event": o, "lease_note": lease_note(o)}
            raise LedgerRefused(f"a freeze is already IN FORCE ({o.get('id')}, generation {o.get('generation')}, commit {str(o.get('commit'))[:12]}): one open freeze per chart")
        ev = {"id": f"XC-FREEZE-{chart_id[:8]}-{generation}-{commit[:12]}-START-{st['starts'] + 1}", "kind": "freeze event", "event": "START", "authority": FREEZE_AUTHORITY,
              "ccd": FREEZE_CCD, "chart_id": chart_id, "generation": generation, "commit": commit, "by": by, "ts": utc(now),
              "gate": {"detector": "dispatch_gate", "verdict_sha256": gate["verdict_sha256"], "evaluated_at": gate["evaluated_at"], "evidence": gate.get("evidence")},
              "scope": "no L1 rebuild, registry change or corpus change for this chart until the END event"}
        ev["lease_note"] = lease_note(ev)
        _append(path, ev)
        return {"result": "NEW", "event": ev, "lease_note": ev["lease_note"]}


def sealed_problem(doc, chart_id: str, generation: str, commit: str) -> str | None:
    """None when `doc` is the seal controller's own SEALED.json for exactly this chart, generation and sealing head (emit_final writes it only after the readback classified SEALED)."""
    if not isinstance(doc, dict) or doc.get("schema") != SEAL_SCHEMA or doc.get("kind") != "sealed":
        return "not the seal controller's SEALED.json (ky.seal_controller/1, kind sealed)"
    if (doc.get("chart_id"), doc.get("generation"), doc.get("head")) != (chart_id, generation, commit):
        return f"SEALED.json is for {doc.get('chart_id')!r}/{doc.get('generation')!r}@{doc.get('head')!r}, not this freeze"
    rb = doc.get("readback")
    if not isinstance(rb, dict) or rb.get("state") != "SEALED":
        return "SEALED.json carries no independent readback in state SEALED"
    if not _HEX64.fullmatch(str(doc.get("brief_digest"))):
        return "SEALED.json names no brief digest"
    return None


def freeze_end(path, *, chart_id: str, generation: str, commit: str, outcome: str, by: str, sealed_doc: dict | None = None, reason: str = "",
               now: dt.datetime | None = None) -> dict:
    """Append the END event for the open freeze of `generation` (and its START commit).  SEALED needs the seal controller's SEALED.json for that commit; ABANDONED / ABORTED need a
    stated reason.  A second END of an already-ended freeze is ALREADY."""
    now = now or dt.datetime.now(dt.timezone.utc)
    path = Path(path)
    _common(path, chart_id, generation, commit, by)
    if outcome not in END_OUTCOMES:
        raise LedgerRefused(f"outcome {outcome!r} is not one of {END_OUTCOMES}")
    if outcome == "SEALED":
        bad = sealed_problem(sealed_doc, chart_id, generation, commit)
        if bad:
            raise LedgerRefused("END(SEALED) needs the seal controller's own evidence: " + bad)
    elif len(reason.strip()) < 10:
        raise LedgerRefused(f"END({outcome}) needs a stated reason (at least 10 characters)")
    with _locked(path):
        st = freeze_state(path, chart_id)
        last = st["last"]
        if st["state"] == "ENDED" and last and last.get("generation") == generation and last.get("commit") == commit and last.get("outcome") == outcome:
            return {"result": "ALREADY", "event": last, "lease_note": lease_note(last)}
        if st["state"] != "IN_FORCE":
            raise LedgerRefused(f"no freeze is IN FORCE to end (state {st['state']}" + (": " + "; ".join(st["problems"]) if st["problems"] else "") + ")")
        o = st["open"]
        if o.get("generation") != generation or o.get("commit") != commit:
            raise LedgerRefused(f"the open freeze is generation {o.get('generation')} at {str(o.get('commit'))[:12]}, not {generation} at {commit[:12]}")
        ev = {"id": f"XC-FREEZE-{chart_id[:8]}-{generation}-{commit[:12]}-END-{st['starts']}", "kind": "freeze event", "event": "END", "authority": FREEZE_AUTHORITY, "ccd": FREEZE_CCD,
              "chart_id": chart_id, "generation": generation, "commit": commit, "outcome": outcome, "by": by, "ts": utc(now), "start_id": o.get("id")}
        if outcome == "SEALED":
            ev["sealed"] = {"brief_digest": sealed_doc["brief_digest"], "run_id": sealed_doc.get("run_id"), "attempt": sealed_doc.get("attempt"),
                            "readback": sealed_doc["readback"].get("operation_id")}
        else:
            ev["reason"] = reason.strip()
        ev["lease_note"] = lease_note(ev)
        _append(path, ev)
        return {"result": "NEW", "event": ev, "lease_note": ev["lease_note"]}


# ── command line ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _load(p, what):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"seal_inputs: {what} {p} is not readable JSON: {exc}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("dispatch-gate", "seal-inputs"):
        s = sub.add_parser(name)
        s.add_argument("--commit", required=True)
        s.add_argument("--runs", required=True, help="JSON from `gh api …/workflows/ci.yml/runs?head_sha=…` (gh_commands()['runs'])")
        s.add_argument("--artifacts", required=True, help="JSON object {run_id: artifact listing}")
        s.add_argument("--min-remaining-hours", type=float, default=DEFAULT_MIN_REMAINING_HOURS)
        if name == "seal-inputs":
            s.add_argument("--checkout", required=True)
            s.add_argument("--artifact-dir", required=True)
            s.add_argument("--downloaded-run-id", required=True)
    fs = sub.add_parser("freeze-start")
    fs.add_argument("--ledger", required=True)
    fs.add_argument("--generation", required=True)
    fs.add_argument("--commit", required=True)
    fs.add_argument("--gate", required=True, help="the dispatch-gate verdict JSON this program printed")
    fs.add_argument("--by", required=True)
    fe = sub.add_parser("freeze-end")
    fe.add_argument("--ledger", required=True)
    fe.add_argument("--generation", required=True)
    fe.add_argument("--commit", required=True)
    fe.add_argument("--outcome", required=True, choices=END_OUTCOMES)
    fe.add_argument("--by", required=True)
    fe.add_argument("--sealed-file")
    fe.add_argument("--reason", default="")
    st = sub.add_parser("freeze-state")
    st.add_argument("--ledger", required=True)
    a = ap.parse_args(argv)
    if a.cmd in ("dispatch-gate", "seal-inputs"):
        kw = dict(runs_doc=_load(a.runs, "runs"), artifacts_by_run=_load(a.artifacts, "artifacts"), min_remaining_hours=a.min_remaining_hours)
        v = dispatch_gate(a.commit, **kw) if a.cmd == "dispatch-gate" else seal_inputs_fresh(
            a.commit, checkout=a.checkout, artifact_dir=a.artifact_dir, downloaded_run_id=a.downloaded_run_id, **kw)
        print(json.dumps(v, indent=1, sort_keys=True))
        return 0 if v["ok"] else 2
    try:
        if a.cmd == "freeze-state":
            s = freeze_state(a.ledger)
            print(json.dumps({"state": s["state"], "open": s["open"], "problems": s["problems"]}, indent=1, sort_keys=True))
            return 0 if s["state"] != "UNKNOWN" else 2
        if a.cmd == "freeze-start":
            r = freeze_start(a.ledger, chart_id=CANONICAL_CHART, generation=a.generation, commit=a.commit, gate=_load(a.gate, "gate verdict"), by=a.by)
        else:
            r = freeze_end(a.ledger, chart_id=CANONICAL_CHART, generation=a.generation, commit=a.commit, outcome=a.outcome, by=a.by,
                           sealed_doc=_load(a.sealed_file, "SEALED.json") if a.sealed_file else None, reason=a.reason)
    except LedgerRefused as exc:
        print(f"seal_inputs: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(r, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
