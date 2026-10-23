#!/usr/bin/env python3
"""lane_ledger_check.py — TRIAL_READY T22 detector (stdlib only; run with `python3 -I`). Vendored from job X-20261022T111735Z-lane-ledger (TR_GAPS B6) by TR-BIND;
bound in the registry by the `lane_ledger` part kind of trial_ready.py, proven by lane_ledger_selftest.py (28 scenarios: two controls TRUE, 25 single planted defects FALSE, one unreadable ref null).

Reads LANE_LEDGER.json and re-derives every claim in it from git and from the
review jobs' own result.json files. It reads FALSE (exit 1) when ANY of these
holds, and TRUE (exit 0) only when none does:

  * a required lane is absent from the ledger, or a remote kalayantra/od1-* branch
    is claimed by no ledger row (missing lane);
  * a lane row has no review bound to a head, or its review result file is
    unreadable / changed since the ledger was written (sha256 differs);
  * the patch-id of base..reviewed_head recomputed from git differs from the
    ledger's, or from the patch-id the reviewer itself reported;
  * the lane is not merged into the integration ref, or the patch-id of what the
    merge commit actually brought in (merge-base(P1,P2)..P2) differs from the
    reviewed patch-id, or the merge parent is not the reviewed head;
  * the review verdict is not ACCEPTED, or its blocking findings (recounted from
    the review result, not from the ledger) are not all closed (open BLOCKING > 0);
  * a digest-bound artefact (harness) no longer hashes to the reviewed digest.

Exit codes: 0 = TRUE, 1 = FALSE, 2 = the detector could not run (null; never green).
N.8: every PASS here is computed from git / the review file; nothing is trusted
from the ledger except the identities it names (heads, bases, paths).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

SCHEMA = "ky.lane_ledger/1"

# Lanes the plan (PLAN_A10_1 §0.1) and the B6 brief name. A ledger that omits any
# of these reads FALSE no matter what else it contains.
REQUIRED_LANES = [
    "NUMERICAL", "W0", "S1", "S2", "P1A", "P1B", "P1C", "V1", "C2", "I1-D2", "I1-INTEGRATION",
    "R1", "R2", "R3", "R4", "R5", "R67", "R8", "Q3C", "C1", "D1", "D3", "S3", "IMPLMODS",
    "L0-1401", "NDH", "DASH", "K8EDGE", "R8X", "NEARMISS", "SELECT-130", "L0VERIFY",
    "RVINT1-FIX", "AR-SWEEP", "AR-VERIFIER", "DRISHTI-EDGE", "P1-BOUNDARY", "VEDHA-RESIDENCE", "G6-RESOLVER",
    "EQR-3855", "EVALUATOR-3856", "HARNESS-V3.1", "HARNESS-B4-PATCH", "RVINT-PART1",
]
# remote branches that are not lanes
NON_LANE_BRANCHES = {"kalayantra/od1-integration"}
BRANCH_GLOB = "refs/remotes/origin/kalayantra/od1-*"


class DetectorError(Exception):
    """The detector itself could not run: the result is null, never green."""


# ---------------------------------------------------------------- git helpers
def git(repo, *args, stdin=None, check=True):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env.pop(k, None)
    p = subprocess.run(["git", "-C", repo, *args], input=stdin, capture_output=True, env=env)
    if check and p.returncode != 0:
        raise DetectorError("git %s failed: %s" % (" ".join(args), p.stderr.decode(errors="replace").strip()[:300]))
    return p


def rev(repo, ref):
    p = git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}", check=False)
    return p.stdout.decode().strip() if p.returncode == 0 else None


def is_ancestor(repo, a, b):
    return git(repo, "merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def patch_id(repo, base, head):
    """git patch-id --stable of the tree diff base..head."""
    d = git(repo, "diff", "--no-ext-diff", base, head).stdout
    out = git(repo, "patch-id", "--stable", stdin=d).stdout.decode().split()
    return out[0] if out else "EMPTY"


def merge_base(repo, a, b):
    p = git(repo, "merge-base", a, b, check=False)
    return p.stdout.decode().strip() or None


def parents(repo, commit):
    return git(repo, "rev-list", "--parents", "-n", "1", commit).stdout.decode().split()[1:]


def blob_at(repo, commit, path):
    p = git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (commit, path), check=False)
    return p.stdout.decode().strip() if p.returncode == 0 else None


def added_files(repo, base, head):
    out = git(repo, "diff", "--no-ext-diff", "--name-status", "--diff-filter=A", base, head).stdout.decode()
    return [l.split("\t", 1)[1] for l in out.splitlines() if "\t" in l]


# ------------------------------------------------------------- file helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_digest(root):
    """The harness-review convention: find . -type f -not -path '*/__pycache__/*' |
    LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256."""
    rels = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            rels.append("./" + os.path.relpath(os.path.join(dp, f), root))
    rels.sort(key=lambda s: s.encode())
    text = "".join("%s  %s\n" % (sha256_file(os.path.join(root, r)), r) for r in rels)
    return hashlib.sha256(text.encode()).hexdigest()


def _is_blocking_finding(f):
    if isinstance(f, dict):
        if f.get("blocking") is True:
            return True
        sev = f.get("severity")
        if isinstance(sev, str) and sev.strip().lower().startswith("blocking"):
            return True
        if "blocking" not in f and sev is None and re.fullmatch(r"B-?\d+", str(f.get("id", ""))):
            return True
    return False


def _select_verdict(result, lane_key=None, item=None):
    """The verdict dict a row is bound to.
    * item given: the element of the review's `items` list whose id equals `item` (the list is
      proposed_verdict.items, or a top-level items list when proposed_verdict is absent or itself a list).
      Absent id, absent list or an ambiguous id is a DetectorError: a multi-item review never falls back to a
      top-level verdict (that one speaks for the whole job, not for the row).
    * lane_key given: result["lanes"][lane_key] (a pair review).
    * neither: proposed_verdict, which must be a single verdict dict."""
    if item is not None:
        pv = result.get("proposed_verdict")
        cands = pv.get("items") if isinstance(pv, dict) else (pv if isinstance(pv, list) else None)
        if not isinstance(cands, list):
            cands = result.get("items")
        if not isinstance(cands, list):
            raise DetectorError("result has no items list (row names item %r)" % item)
        hits = [c for c in cands if isinstance(c, dict) and str(c.get("id", c.get("item"))) == str(item)]
        if len(hits) != 1:
            raise DetectorError("result has %d items with id %r (need exactly 1)" % (len(hits), item))
        return hits[0]
    pv = (result.get("lanes") or {}).get(lane_key) if lane_key else result.get("proposed_verdict")
    if not isinstance(pv, dict):
        raise DetectorError("result has no %s" % ("lanes[%s]" % lane_key if lane_key else "proposed_verdict"))
    return pv


def _blocking_from(pv):
    ids = []
    if isinstance(pv.get("blocking"), list):
        for x in pv["blocking"]:
            ids.append(str(x.get("id")) if isinstance(x, dict) else (str(x).split() or ["?"])[0])
    fnd = pv.get("findings")
    if isinstance(fnd, list):
        for f in fnd:
            if _is_blocking_finding(f):
                i = str(f.get("id"))
                if i not in ids:
                    ids.append(i)
    return ids


def blocking_ids(result, lane_key=None, item=None):
    """BLOCKING finding ids recounted from a review job's result.json.
    lane_key selects result["lanes"][lane_key] (a pair review that carries one verdict per lane);
    item selects one element of a multi-item review by its id (that item's findings only)."""
    return _blocking_from(_select_verdict(result, lane_key, item))


def review_view(result_path, lane_key=None, item=None):
    with open(result_path, "rb") as f:
        raw = f.read()
    result = json.loads(raw)
    if item is not None:
        pv = _select_verdict(result, lane_key, item)
    else:
        pv = (result.get("lanes") or {}).get(lane_key) if lane_key else result.get("proposed_verdict")
        pv = pv if isinstance(pv, dict) else {}
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "verdict": pv.get("verdict"),
        "head": pv.get("head"),
        "patch_id": pv.get("patch_id"),
        "content_digest": pv.get("content_digest"),
        "blocking_ids": _blocking_from(pv) if pv else blocking_ids(result, lane_key),
    }


# ----------------------------------------------------------------- row checks
def check_review(row, ctx, why):
    """Review bound to the row: file unchanged, ACCEPTED, no open BLOCKING (recounted)."""
    rp = row.get("review_result_path")
    if not rp:
        why.append("no_review: no review result is bound to this lane")
        return None
    if not os.path.isfile(rp):
        why.append("review_result_unreadable: %s" % rp)
        return None
    v = review_view(rp, row.get("review_lane_key"), row.get("review_item"))
    if row.get("review_result_sha256") != v["sha256"]:
        why.append("review_result_changed: sha256 differs from the ledger")
    if v["verdict"] != "ACCEPTED":
        why.append("review_not_accepted: verdict is %s" % v["verdict"])
    closed = set(row.get("blocking_closed_by_ruling") or [])
    still = [b for b in v["blocking_ids"] if b not in closed]
    if still:
        why.append("open_blocking: %d (%s)" % (len(still), ",".join(still)))
    if row.get("open_blocking") != len(still):
        why.append("ledger_open_blocking_wrong: ledger %r, recounted %d" % (row.get("open_blocking"), len(still)))
    return v


def check_git_row(row, ctx, why):
    repo = ctx["repo"]
    via = row.get("review_via")  # no lane-level review: the covering row's review is the evidence
    v = None if via else check_review(row, ctx, why)
    if via and ctx["results"].get(via) is not True:
        why.append("cover_review_row_not_true: %s" % via)
    head, base = row.get("reviewed_head"), row.get("base")
    if not head or not base:
        why.append("no_reviewed_head")
        return
    if rev(repo, head) != head or rev(repo, base) != base:
        why.append("unknown_commit: reviewed head or base is not in the repository")
        return
    if v is not None and v["head"] != head:
        why.append("review_head_differs: review is bound to %s, ledger says %s" % (str(v["head"])[:12], head[:12]))
    if not is_ancestor(repo, base, head):
        why.append("base_not_ancestor_of_head")
    re_pid = patch_id(repo, base, head)
    if re_pid != row.get("reviewed_patch_id"):
        why.append("reviewed_patch_id_mismatch: recomputed %s, ledger %s" % (re_pid[:12], str(row.get("reviewed_patch_id"))[:12]))
    if v is not None and v["patch_id"]:
        rb = row.get("reviewer_base")
        if not rb or rev(repo, rb) != rb:
            why.append("reviewer_patch_id_unreproducible: reviewer reported %s; no base reproducing it is recorded" % str(v["patch_id"])[:12])
        elif patch_id(repo, rb, head) != v["patch_id"]:
            why.append("reviewer_patch_id_mismatch: reviewer reported %s, base %s gives %s" % (str(v["patch_id"])[:12], rb[:12], patch_id(repo, rb, head)[:12]))
    check_merge(row, ctx, why, re_pid)


def check_merge(row, ctx, why, reviewed_pid):
    repo = ctx["repo"]
    m = row.get("merge") or {}
    kind = m.get("kind")
    mc = m.get("merge_commit")
    if kind in (None, "not_merged"):
        why.append("not_merged: lane is not in %s" % ctx["integration_ref"])
        return
    if not mc or rev(repo, mc) != mc:
        why.append("merge_commit_unknown")
        return
    if not is_ancestor(repo, mc, ctx["integration_head"]):
        why.append("merge_not_in_integration: %s is not an ancestor of %s" % (mc[:12], ctx["integration_ref"]))
        return
    head = row["reviewed_head"]
    if kind == "merge":
        ps = parents(repo, mc)
        if len(ps) != 2 or ps[1] != head:
            why.append("merge_parent_not_reviewed_head: merge parents %s" % [p[:12] for p in ps])
            return
        merged_pid = patch_id(repo, merge_base(repo, ps[0], ps[1]), ps[1])
    elif kind == "squash":
        ps = parents(repo, mc)
        if len(ps) != 1:
            why.append("squash_commit_has_%d_parents" % len(ps))
            return
        merged_pid = patch_id(repo, ps[0], mc)
    elif kind == "ancestor":
        if not is_ancestor(repo, head, ctx["integration_head"]):
            why.append("reviewed_head_not_ancestor_of_integration")
            return
        merged_pid = reviewed_pid  # the very same commits: nothing to translate
    elif kind == "composite":
        check_composite(row, ctx, why)
        return
    else:
        why.append("unknown_merge_kind: %r" % kind)
        return
    if merged_pid != m.get("merged_patch_id"):
        why.append("merged_patch_id_ledger_mismatch: recomputed %s, ledger %s" % (merged_pid[:12], str(m.get("merged_patch_id"))[:12]))
    if merged_pid != reviewed_pid:
        why.append("merged_patch_differs_from_reviewed: merged %s, reviewed %s" % (merged_pid[:12], reviewed_pid[:12]))


def composite_edits(repo, composite, head, files):
    """{path: "+a/-d" or "absent"} for each file the lane added that the composite commit does not hold byte-for-byte."""
    out = {}
    for f in files:
        if blob_at(repo, composite, f) == blob_at(repo, head, f):
            continue
        if blob_at(repo, composite, f) is None:
            out[f] = "absent"
            continue
        ns = git(repo, "diff", "--no-ext-diff", "--numstat", head, composite, "--", f).stdout.decode().split()
        out[f] = "+%s/-%s" % (ns[0], ns[1]) if len(ns) >= 2 else "changed"
    return out


def check_composite(row, ctx, why):
    """Lane content entered integration inside one composite commit: every file the lane ADDED
    must be byte-identical (git blob) in the composite commit, and the covering row must pass."""
    repo = ctx["repo"]
    m = row["merge"]
    cc = m.get("merge_commit")
    covered = m.get("covered_by")
    if covered not in ctx["by_id"]:
        why.append("composite_cover_row_missing: %s" % covered)
        return
    if ctx["results"].get(covered) is not True:
        why.append("composite_cover_row_not_true: %s" % covered)
    files = added_files(repo, row["base"], row["reviewed_head"])
    if not files or len(files) != m.get("added_files_total"):
        why.append("composite_added_file_count_differs: ledger %r, git %d" % (m.get("added_files_total"), len(files)))
    # edits the composite commit made on top of the lane's files are legitimate only when the ledger records them
    # exactly (they are then covered by the cover row's review of the composite); any other drift is a mismatch
    got = composite_edits(repo, cc, row["reviewed_head"], files)
    if got != (m.get("edited_in_composite") or {}):
        why.append("composite_edits_differ_from_ledger: git %s, ledger %s" % (got, m.get("edited_in_composite") or {}))


def check_digest_row(row, ctx, why):
    v = check_review(row, ctx, why)
    d = row.get("reviewed_digest")
    if not d:
        why.append("no_reviewed_digest")
        return
    if v is not None and v["content_digest"] != d:
        why.append("review_digest_differs: review %s, ledger %s" % (str(v["content_digest"])[:12], d[:12]))
    p = row.get("artifact_path")
    if not p or not os.path.isdir(p):
        why.append("artifact_missing: %s" % p)
        return
    got = tree_digest(p)
    if got != d:
        why.append("artifact_digest_mismatch: %s hashes to %s, reviewed %s" % (p, got[:12], d[:12]))


def check_patch_digest_row(row, ctx, why):
    """Harness B4 patch. Reads false until a review binds it; the patch must also still hash to the
    ledger's sha256 and, applied to the v3.1 base, give exactly the installed harness."""
    check_review(row, ctx, why)
    pf = row.get("patch_file")
    if not pf or not os.path.isfile(pf):
        why.append("patch_file_missing")
        return
    if sha256_file(pf) != row.get("patch_sha256"):
        why.append("patch_sha256_mismatch")
    base_dir, inst = row.get("base_artifact_path"), row.get("installed_artifact_path")
    if not (base_dir and os.path.isdir(base_dir) and inst and os.path.isdir(inst)):
        why.append("artifact_missing")
        return
    if tree_digest(base_dir) != row.get("base_digest"):
        why.append("base_digest_mismatch")
    if tree_digest(inst) != row.get("installed_digest"):
        why.append("installed_digest_mismatch: the installed harness changed since the ledger")
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "h")
        subprocess.run(["cp", "-R", base_dir, dst], check=True)
        pr = subprocess.run(["patch", "-p%d" % row.get("patch_strip", 1), "-d", dst, "-i", pf], capture_output=True)
        if pr.returncode != 0:
            why.append("patch_does_not_apply_to_base")
        elif tree_digest(dst) != row.get("installed_digest"):
            why.append("patched_base_is_not_the_installed_harness")


def check_gate_row(row, ctx, why):
    """A review gate (RV-INT part 1): its own findings recounted; a finding may be closed only by a named ruling."""
    check_review(row, ctx, why)


def check_pending_row(row, ctx, why):
    why.append("lane_not_delivered: %s" % row.get("pending_reason", "no branch, no review"))


KIND_CHECK = {
    "git": check_git_row,
    "digest": check_digest_row,
    "patch_digest": check_patch_digest_row,
    "gate": check_gate_row,
    "pending": check_pending_row,
}


def evaluate(ledger, repo, integration_ref):
    """Return the detector's reading as a dict; raises DetectorError when it cannot read."""
    if ledger.get("schema") != SCHEMA:
        raise DetectorError("ledger schema is %r, expected %r" % (ledger.get("schema"), SCHEMA))
    ihead = rev(repo, integration_ref)
    if ihead is None:
        raise DetectorError("integration ref %s not found in %s" % (integration_ref, repo))
    rows = ledger.get("lanes")
    if not isinstance(rows, list):
        raise DetectorError("ledger has no lanes list")
    by_id = {r.get("id"): r for r in rows}
    ctx = {"repo": repo, "integration_ref": integration_ref, "integration_head": ihead, "by_id": by_id, "results": {}}
    problems = [("missing_lane: %s" % l) for l in REQUIRED_LANES if l not in by_id]
    if ledger.get("integration_head") != ihead:
        # the ledger is a claim about one head; any advance voids it until it is rebuilt
        problems.append("stale_ledger: built at %s, %s is now %s" % (str(ledger.get("integration_head"))[:12], integration_ref, ihead[:12]))
    # a remote od1 branch that no row claims is a lane nobody ledgered
    refs = git(repo, "for-each-ref", "--format=%(refname:strip=3)", BRANCH_GLOB).stdout.decode().split()
    claimed = {r.get("branch") for r in rows if r.get("branch")}
    for b in refs:
        if b not in claimed and b not in NON_LANE_BRANCHES:
            problems.append("unledgered_branch: origin/%s" % b)
    # composite rows lean on their cover row: evaluate those last
    order = sorted(rows, key=lambda r: 1 if ((r.get("merge") or {}).get("kind") == "composite" or r.get("review_via")) else 0)
    row_out = {}
    for r in order:
        why = []
        try:
            fn = KIND_CHECK.get(r.get("kind"))
            if fn is None:
                why.append("unknown_row_kind: %r" % r.get("kind"))
            else:
                fn(r, ctx, why)
        except DetectorError as e:
            why.append("detector_error: %s" % e)
        ctx["results"][r.get("id")] = not why
        row_out[r.get("id")] = {"ok": not why, "why": why}
    open_blocking = sum(r["open_blocking"] for r in rows if isinstance(r.get("open_blocking"), int))
    value = not problems and bool(row_out) and all(x["ok"] for x in row_out.values())
    return {
        "check": "T22 lane ledger",
        "value": value,
        "integration_ref": integration_ref,
        "integration_head": ihead,
        "ledger_integration_head": ledger.get("integration_head"),
        "lanes_total": len(rows),
        "lanes_ok": sum(1 for x in row_out.values() if x["ok"]),
        "lanes_not_ok": [i for i in row_out if not row_out[i]["ok"]],
        "ledger_problems": problems,
        "open_blocking_total": open_blocking,
        "rows": row_out,
    }


# ----------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ledger", required=True, help="LANE_LEDGER.json (outside the repository), rebuilt at the integration head after the last merge or review")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--integration-ref", required=True, help="the commit (or ref) the ledger is a claim about; any other head reads FALSE (stale ledger)")
    ap.add_argument("--json-out")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.ledger) as f:
            ledger = json.load(f)
        res = evaluate(ledger, a.repo, a.integration_ref)
    except (DetectorError, OSError, ValueError) as e:
        print("T22 lane ledger: NULL (detector could not run): %s" % e, file=sys.stderr)
        return 2
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(res, f, indent=1, sort_keys=True)
    if not a.quiet:
        print("T22 lane ledger: %s  (%d/%d lanes ok, open BLOCKING %d, integration %s)" % (
            "TRUE" if res["value"] else "FALSE", res["lanes_ok"], res["lanes_total"],
            res["open_blocking_total"], res["integration_head"][:12]))
        for p in res["ledger_problems"]:
            print("  LEDGER  %s" % p)
        for i, x in res["rows"].items():
            if not x["ok"]:
                print("  %-18s %s" % (i, "; ".join(x["why"])))
    return 0 if res["value"] else 1


if __name__ == "__main__":
    sys.exit(main())
