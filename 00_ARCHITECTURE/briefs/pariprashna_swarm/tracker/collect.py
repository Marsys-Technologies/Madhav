#!/usr/bin/env python3
"""Collector: derives ground truth every cycle. Each signal category is wrapped so one
failure degrades one cell (evidence_class UNKNOWN) rather than the whole page. Never
carries a previous value forward on failure — that is the projector's job to refuse to do.
Stdlib only.

Two separate git sources, deliberately not consolidated:
  - The MIRROR (~/.pariprashna-tracker/mirror.git) — a private clone this daemon owns
    outright, fetched every cycle on its own cadence. ALL origin/* ref reads (lane
    branches, ahead/behind, main's tip, campaign-coordination, code staleness) come from
    here. A shared checkout's remote-tracking refs only advance when some UNRELATED
    process fetches there — reading origin/* from one is silently-stale-looking-fresh,
    exactly the failure mode this whole tracker exists to prevent.
  - The SHARED checkout (REPO_ROOT / TRACKER_GIT_REPO) — read-only, --no-optional-locks,
    used ONLY for `git worktree list` (the one signal a bare mirror structurally cannot
    provide: it has no worktrees) and for filesystem reads that need an actual working
    tree (expected_artifacts path existence, migration numbering).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    CODE_DIR, GIT_REMOTE_URL, INSTALLED_FROM_JSON, MIRROR_DIR, MIRROR_FETCH_STATE_JSON,
    REPO_ROOT, atomic_write_json, ensure_runtime_dirs, run, run_mirror,
)

GH_REPO = "Marsys-Technologies/Madhav"
GCLOUD_PROJECT = "madhav-astrology"
GCLOUD_REGION = "asia-south1"
GCLOUD_SERVICE = "amjis-web"
TRACKER_SUBTREE_PATH = "00_ARCHITECTURE/briefs/pariprashna_swarm/tracker"


def _unknown(reason):
    return {"evidence_class": "UNKNOWN", "provenance": reason, "value": None}


def _derived(value, provenance):
    return {"evidence_class": "DERIVED", "provenance": provenance, "value": value}


def mirror_fetch():
    """Fetch the daemon's own mirror on its own cadence (every cycle). Bootstraps with a
    one-time `clone --mirror` if the mirror doesn't exist yet. Never raises. Tracks
    consecutive failures + last success time across cycles via MIRROR_FETCH_STATE_JSON —
    a plain counter file, deliberately NOT part of the event-log/pure-fold state, since
    it's read back by THIS SAME process next cycle, not folded by the projector."""
    ensure_runtime_dirs()
    t0 = time.time()
    if not os.path.isdir(MIRROR_DIR):
        ok, _, err = run(["git", "clone", "--mirror", GIT_REMOTE_URL, MIRROR_DIR],
                          cwd=os.path.dirname(MIRROR_DIR), timeout=300)
        action = "git clone --mirror (bootstrap)"
    else:
        ok, _, err = run_mirror(["fetch", "--prune", "--quiet"], timeout=60)
        action = "git fetch --prune (mirror)"
    duration_ms = int((time.time() - t0) * 1000)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    prior = {"consecutive_failures": 0, "last_success_ts": None}
    if os.path.exists(MIRROR_FETCH_STATE_JSON):
        try:
            with open(MIRROR_FETCH_STATE_JSON, encoding="utf-8") as f:
                prior = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    if ok:
        new_state = {"consecutive_failures": 0, "last_success_ts": ts}
    else:
        new_state = {"consecutive_failures": prior.get("consecutive_failures", 0) + 1,
                      "last_success_ts": prior.get("last_success_ts")}
    atomic_write_json(MIRROR_FETCH_STATE_JSON, new_state)

    return {
        "ok": ok, "action": action, "duration_ms": duration_ms, "ts": ts,
        "error": None if ok else (err or "").strip()[:300],
        "consecutive_failures": new_state["consecutive_failures"],
        "last_success_ts": new_state["last_success_ts"],
    }


def collect_git_lane_branches(mirror_gate):
    """Per-lane branch existence, ahead/behind mirror's main, last commit. All mirror-
    sourced -- see module docstring."""
    if mirror_gate:
        return mirror_gate
    ok, out, err = run_mirror(["for-each-ref",
                                "--format=%(refname)|%(objectname)|%(committerdate:iso-strict)|%(subject)",
                                "refs/heads/pariprashna/"])
    if not ok:
        return _unknown(f"mirror for-each-ref failed: {err.strip()[:200]}")
    branches = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        refname, sha, date, subject = parts
        branch = refname.replace("refs/heads/", "")
        ab_ok, ab_out, _ = run_mirror(["rev-list", "--left-right", "--count", f"main...{branch}"])
        ahead_behind = None
        if ab_ok and ab_out.strip():
            try:
                behind_s, ahead_s = ab_out.strip().split()
                ahead_behind = {"ahead": int(ahead_s), "behind": int(behind_s)}
            except ValueError:
                ahead_behind = None
        branches[branch] = {
            "sha": sha, "committer_date": date, "subject": subject,
            "ahead_behind_main": ahead_behind,
        }
    return _derived(branches, "mirror for-each-ref refs/heads/pariprashna/ (fetched this cycle)")


def collect_git_worktrees():
    """The ONE signal the mirror structurally cannot provide (a bare mirror has no
    worktrees) -- deliberately still reads the SHARED checkout, read-only,
    --no-optional-locks. Do not consolidate this with the mirror reads above."""
    ok, out, err = run(["git", "--no-optional-locks", "worktree", "list", "--porcelain"])
    if not ok:
        return _unknown(f"git worktree list failed: {err.strip()[:200]}")
    worktrees, cur = [], {}
    for line in out.splitlines():
        if not line.strip():
            if cur:
                worktrees.append(cur)
            cur = {}
            continue
        if " " in line:
            k, v = line.split(" ", 1)
            cur[k] = v
        else:
            cur[line] = True
    if cur:
        worktrees.append(cur)
    return _derived(worktrees, "git --no-optional-locks worktree list --porcelain (shared checkout)")


def collect_github_prs():
    ok, out, err = run([
        "gh", "pr", "list", "--repo", GH_REPO, "--state", "open",
        "--json", "number,headRefName,url,mergeStateStatus,statusCheckRollup,isDraft",
        "--limit", "200",
    ], timeout=30)
    if not ok:
        return _unknown(f"gh pr list failed: {err.strip()[:200]}")
    try:
        prs = json.loads(out)
    except json.JSONDecodeError as e:
        return _unknown(f"gh pr list returned non-JSON: {e}")
    by_branch = {}
    for pr in prs:
        checks = pr.get("statusCheckRollup") or []
        conclusions = [c.get("conclusion") for c in checks if isinstance(c, dict)]
        rollup = "PENDING"
        if conclusions:
            if all(c == "SUCCESS" for c in conclusions if c):
                rollup = "SUCCESS" if all(c is not None for c in conclusions) else "PENDING"
            if any(c in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT") for c in conclusions):
                rollup = "FAILURE"
        by_branch[pr["headRefName"]] = {
            "number": pr["number"], "url": pr["url"],
            "merge_state_status": pr.get("mergeStateStatus"),
            "check_rollup": rollup, "is_draft": pr.get("isDraft", False),
        }
    return _derived(by_branch, "gh pr list --repo Marsys-Technologies/Madhav --state open")


def parse_rate_limit(data):
    """Pure: gh api rate_limit's parsed JSON -> the cell this collector reports. `gh pr
    list` (both open and merged polls, every cycle) is a GraphQL-backed command -- verified
    empirically (2026-08-20): `resources.core.used` stayed 0 across a `gh pr list` call
    while `resources.graphql.used` incremented by 2 in the same call. Reading `core` here
    reports a bucket this tracker's own polling never spends from, so it always reads
    5000/5000 regardless of load -- a decorative meter, not a budget one. `graphql` is the
    bucket actually being spent; report that one."""
    graphql = data.get("resources", {}).get("graphql", {})
    return {"bucket": "graphql", "remaining": graphql.get("remaining"),
            "limit": graphql.get("limit"), "reset": graphql.get("reset")}


def collect_github_rate_limit():
    ok, out, err = run(["gh", "api", "rate_limit"], timeout=15)
    if not ok:
        return _unknown(f"gh api rate_limit failed: {err.strip()[:200]}")
    try:
        data = json.loads(out)
        return _derived(
            parse_rate_limit(data),
            "gh api rate_limit (graphql bucket -- the bucket gh pr list actually spends "
            "from, verified empirically against resources.core staying flat)",
        )
    except json.JSONDecodeError as e:
        return _unknown(f"gh api rate_limit returned non-JSON: {e}")


def collect_recent_merged_prs(mirror_gate):
    """Free consistency check (item 4): gh is network-live, the mirror could lag. If gh
    says a PR merged but its merge commit isn't an ancestor of the mirror's main, that's a
    genuine, real ref-lag signal -- project.py turns it into an anomaly."""
    if mirror_gate:
        return mirror_gate
    ok, out, err = run([
        "gh", "pr", "list", "--repo", GH_REPO, "--state", "merged", "--limit", "20",
        "--json", "number,mergeCommit,mergedAt,headRefName",
    ], timeout=30)
    if not ok:
        return _unknown(f"gh pr list --state merged failed: {err.strip()[:200]}")
    try:
        prs = json.loads(out)
    except json.JSONDecodeError as e:
        return _unknown(f"gh pr list --state merged returned non-JSON: {e}")
    results = []
    for pr in prs:
        mc = (pr.get("mergeCommit") or {}).get("oid")
        if not mc:
            continue
        anc_ok, _, _ = run_mirror(["merge-base", "--is-ancestor", mc, "main"])
        results.append({
            "number": pr["number"], "merge_commit_sha": mc, "merged_at": pr.get("mergedAt"),
            "head_ref": pr.get("headRefName"), "is_ancestor_of_mirror_main": anc_ok,
        })
    return _derived(results, "gh pr list --state merged --limit 20, cross-checked via "
                              "git merge-base --is-ancestor against the mirror's main")


def collect_expected_artifacts(plan, mirror_gate):
    results = {}
    for lane in plan["lanes"]:
        spec = lane.get("expected_artifacts") or {}
        entry = {"paths": [], "merge_commit": None}
        for rel in spec.get("paths", []):
            # Path existence needs an actual working tree -- the shared checkout, not the
            # bare mirror. Independent of mirror freshness; not gated on mirror_gate.
            abs_path = os.path.join(REPO_ROOT, rel)
            exists = os.path.exists(abs_path)
            mtime = os.path.getmtime(abs_path) if exists else None
            entry["paths"].append({"path": rel, "exists": exists, "mtime": mtime})
        if spec.get("merge_commit"):
            sha = spec["merge_commit"]
            if mirror_gate:
                entry["merge_commit"] = {"sha": sha, "is_ancestor_of_main": None,
                                          "evidence_class": "UNKNOWN", "provenance": mirror_gate["provenance"]}
            else:
                ok, _, _ = run_mirror(["merge-base", "--is-ancestor", sha, "main"])
                entry["merge_commit"] = {"sha": sha, "is_ancestor_of_main": ok}
        results[lane["id"]] = entry
    return _derived(results, "filesystem existence/mtime (shared checkout) + git merge-base "
                              "--is-ancestor (mirror), per PLAN.yaml expected_artifacts")


def collect_code_provenance(mirror_gate):
    """What code is this daemon actually running, and is it current? Reads
    INSTALLED_FROM.json next to the running code (written by install.sh --install-from-ref
    at snapshot-install time; absent in in-place/dev mode, which is honestly UNKNOWN rather
    than faked). Freshness is checked against the tracker/ subtree's latest commit on the
    MIRROR's main -- NOT the shared checkout (stale origin/*) and NOT this code directory,
    which in snapshot mode has no .git of its own to check."""
    if not os.path.exists(INSTALLED_FROM_JSON):
        return _unknown(f"no INSTALLED_FROM.json at {INSTALLED_FROM_JSON} (in-place/dev install, not a snapshot)")
    try:
        with open(INSTALLED_FROM_JSON, encoding="utf-8") as f:
            installed = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return _unknown(f"could not read INSTALLED_FROM.json: {e}")

    source_sha = installed.get("source_sha")
    if not source_sha:
        return _unknown("INSTALLED_FROM.json has no source_sha")

    if mirror_gate:
        return _unknown(f"cannot check code staleness: {mirror_gate['provenance']}")

    ok, latest, err = run_mirror(["log", "-1", "--format=%H", "main", "--", TRACKER_SUBTREE_PATH])
    if not ok or not latest.strip():
        return _unknown(f"could not determine mirror main's latest tracker/ subtree commit: {err.strip()[:200]}")
    latest = latest.strip()

    is_current = (source_sha == latest)
    ok2, _, _ = run_mirror(["merge-base", "--is-ancestor", source_sha, "main"])
    is_ancestor_of_main = ok2

    return _derived({
        "installed": installed,
        "latest_tracker_subtree_commit_on_main": latest,
        "is_current": is_current,
        "is_ancestor_of_origin_main": is_ancestor_of_main,
        "code_dir": CODE_DIR,
    }, f"INSTALLED_FROM.json ({INSTALLED_FROM_JSON}) vs. mirror log -1 main -- {TRACKER_SUBTREE_PATH}")


def collect_deploy():
    ok, out, err = run([
        "gcloud", "run", "revisions", "list",
        "--service", GCLOUD_SERVICE, "--region", GCLOUD_REGION, "--project", GCLOUD_PROJECT,
        "--format=json", "--limit=5",
    ], timeout=30)
    if not ok:
        return _unknown(f"gcloud run revisions list failed: {err.strip()[:200]}")
    try:
        revisions = json.loads(out)
    except json.JSONDecodeError as e:
        return _unknown(f"gcloud run revisions list returned non-JSON: {e}")
    ok2, out2, err2 = run([
        "gcloud", "run", "services", "describe", GCLOUD_SERVICE,
        "--region", GCLOUD_REGION, "--project", GCLOUD_PROJECT, "--format=json",
    ], timeout=30)
    traffic = None
    if ok2:
        try:
            svc = json.loads(out2)
            traffic = svc.get("status", {}).get("traffic", [])
        except json.JSONDecodeError:
            traffic = None
    return _derived(
        {"revisions": revisions[:5], "traffic": traffic},
        f"gcloud run revisions list --service={GCLOUD_SERVICE} --region={GCLOUD_REGION}",
    )


def _extract_lease_holder(text):
    lease_lines = [ln for ln in text.splitlines() if "lease" in ln.lower() and ln.strip().startswith("-")]
    return lease_lines[-1].strip() if lease_lines else None


def collect_shared_surfaces(mirror_gate):
    out_obj = {}
    if mirror_gate:
        out_obj["origin_main_sha"] = mirror_gate
        out_obj["coordination_lease_holder"] = mirror_gate
    else:
        ok, sha, err = run_mirror(["rev-parse", "main"])
        out_obj["origin_main_sha"] = _derived(sha.strip(), "git rev-parse main (mirror)") if ok else _unknown(err[:200])

        ok, coord, err = run_mirror(["show", "campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"])
        if ok:
            holder = _extract_lease_holder(coord)
            out_obj["coordination_lease_holder"] = _derived(
                holder, "git show campaign-coordination:.../CAMPAIGN_COORDINATION.md (mirror), last '- ' line mentioning lease")
        else:
            out_obj["coordination_lease_holder"] = _unknown(f"mirror show campaign-coordination failed: {err.strip()[:200]}")

    deploy = collect_deploy()
    out_obj["live_cloud_run_revision"] = deploy

    # Migration numbering needs actual files on disk -- the shared checkout's working
    # tree, independent of mirror freshness.
    next_mig = _unknown("no migrations directory found")
    for rel in ("platform/migrations", "platform/supabase/migrations"):
        abs_dir = os.path.join(REPO_ROOT, rel)
        if os.path.isdir(abs_dir):
            nums = []
            for fn in os.listdir(abs_dir):
                digits = "".join(ch for ch in fn.split("_")[0] if ch.isdigit())
                if digits:
                    nums.append(int(digits))
            if nums:
                next_mig = _derived(max(nums) + 1, f"max numeric prefix in {rel}/ + 1 (shared checkout)")
            break
    out_obj["next_free_migration_number"] = next_mig
    return out_obj


def main():
    plan = None
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "PLAN.yaml"), encoding="utf-8") as f:
            plan = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: cannot load PLAN.yaml: {e}", file=sys.stderr)
        sys.exit(1)

    mirror_status = mirror_fetch()
    mirror_gate = None if mirror_status["ok"] else _unknown(
        f"mirror fetch failed ({mirror_status['action']}): {mirror_status['error']}"
    )

    snapshot = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mirror_fetch": mirror_status,
        "git_lane_branches": collect_git_lane_branches(mirror_gate),
        "git_worktrees": collect_git_worktrees(),
        "github_prs": collect_github_prs(),
        "github_rate_limit": collect_github_rate_limit(),
        "recent_merged_prs": collect_recent_merged_prs(mirror_gate),
        "expected_artifacts": collect_expected_artifacts(plan, mirror_gate),
        "code_provenance": collect_code_provenance(mirror_gate),
        "deploy": collect_deploy(),
        "shared_surfaces": collect_shared_surfaces(mirror_gate),
    }
    from _common import COLLECTOR_SNAPSHOT_JSON
    ensure_runtime_dirs()
    atomic_write_json(COLLECTOR_SNAPSHOT_JSON, snapshot)
    return snapshot


if __name__ == "__main__":
    main()
