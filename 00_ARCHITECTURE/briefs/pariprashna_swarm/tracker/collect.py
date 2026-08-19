#!/usr/bin/env python3
"""Collector: derives ground truth every cycle. Each signal category is wrapped so one
failure degrades one cell (evidence_class UNKNOWN) rather than the whole page. Never
carries a previous value forward on failure — that is the projector's job to refuse to do.
Stdlib only.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import REPO_ROOT, atomic_write_json, run  # noqa: E402

GH_REPO = "Marsys-Technologies/Madhav"
GCLOUD_PROJECT = "madhav-astrology"
GCLOUD_REGION = "asia-south1"
GCLOUD_SERVICE = "amjis-web"


def _unknown(reason):
    return {"evidence_class": "UNKNOWN", "provenance": reason, "value": None}


def _derived(value, provenance):
    return {"evidence_class": "DERIVED", "provenance": provenance, "value": value}


def collect_git_lane_branches():
    """Per-lane branch existence, ahead/behind origin/main, last commit."""
    ok, out, err = run(["git", "--no-optional-locks", "for-each-ref",
                         "--format=%(refname)|%(objectname)|%(committerdate:iso-strict)|%(subject)",
                         "refs/remotes/origin/pariprashna/"])
    if not ok:
        return _unknown(f"git for-each-ref failed: {err.strip()[:200]}")
    branches = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        refname, sha, date, subject = parts
        branch = refname.replace("refs/remotes/origin/", "")
        ab_ok, ab_out, _ = run(["git", "--no-optional-locks", "rev-list",
                                 "--left-right", "--count",
                                 f"origin/main...{refname.replace('refs/remotes/', '')}"])
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
    return _derived(branches, "git --no-optional-locks for-each-ref refs/remotes/origin/pariprashna/")


def collect_git_worktrees():
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
    return _derived(worktrees, "git --no-optional-locks worktree list --porcelain")


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


def collect_github_rate_limit():
    ok, out, err = run(["gh", "api", "rate_limit"], timeout=15)
    if not ok:
        return _unknown(f"gh api rate_limit failed: {err.strip()[:200]}")
    try:
        data = json.loads(out)
        core = data.get("resources", {}).get("core", {})
        return _derived(
            {"remaining": core.get("remaining"), "limit": core.get("limit"), "reset": core.get("reset")},
            "gh api rate_limit",
        )
    except json.JSONDecodeError as e:
        return _unknown(f"gh api rate_limit returned non-JSON: {e}")


def collect_expected_artifacts(plan):
    results = {}
    for lane in plan["lanes"]:
        spec = lane.get("expected_artifacts") or {}
        entry = {"paths": [], "merge_commit": None}
        for rel in spec.get("paths", []):
            abs_path = os.path.join(REPO_ROOT, rel)
            exists = os.path.exists(abs_path)
            mtime = os.path.getmtime(abs_path) if exists else None
            entry["paths"].append({"path": rel, "exists": exists, "mtime": mtime})
        if spec.get("merge_commit"):
            sha = spec["merge_commit"]
            ok, _, _ = run(["git", "--no-optional-locks", "merge-base", "--is-ancestor", sha, "origin/main"])
            entry["merge_commit"] = {"sha": sha, "is_ancestor_of_main": ok}
        results[lane["id"]] = entry
    return _derived(results, "filesystem existence/mtime + git merge-base --is-ancestor, per PLAN.yaml expected_artifacts")


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


def collect_shared_surfaces():
    out_obj = {}
    ok, sha, err = run(["git", "--no-optional-locks", "rev-parse", "origin/main"])
    out_obj["origin_main_sha"] = _derived(sha.strip(), "git rev-parse origin/main") if ok else _unknown(err[:200])

    ok, coord, err = run(["git", "--no-optional-locks", "show",
                           "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"])
    if ok:
        holder = _extract_lease_holder(coord)
        out_obj["coordination_lease_holder"] = _derived(holder, "git show origin/campaign-coordination:.../CAMPAIGN_COORDINATION.md, last '- ' line mentioning lease")
    else:
        out_obj["coordination_lease_holder"] = _unknown(f"git show origin/campaign-coordination failed: {err.strip()[:200]}")

    deploy = collect_deploy()
    out_obj["live_cloud_run_revision"] = deploy

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
                next_mig = _derived(max(nums) + 1, f"max numeric prefix in {rel}/ + 1")
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

    snapshot = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_lane_branches": collect_git_lane_branches(),
        "git_worktrees": collect_git_worktrees(),
        "github_prs": collect_github_prs(),
        "github_rate_limit": collect_github_rate_limit(),
        "expected_artifacts": collect_expected_artifacts(plan),
        "deploy": collect_deploy(),
        "shared_surfaces": collect_shared_surfaces(),
    }
    from _common import COLLECTOR_SNAPSHOT_JSON, ensure_runtime_dirs
    ensure_runtime_dirs()
    atomic_write_json(COLLECTOR_SNAPSHOT_JSON, snapshot)
    return snapshot


if __name__ == "__main__":
    main()
