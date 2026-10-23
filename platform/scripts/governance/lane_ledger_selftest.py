#!/usr/bin/env python3
"""lane_ledger_selftest.py — proves lane_ledger_check can read TRUE and that each single planted
defect flips it to FALSE (N.8). Builds a throwaway git repo + fake review files under $TMPDIR.
Run: python3 -I lane_ledger_selftest.py   (exit 0 = all scenarios behaved)."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("llc", os.path.join(HERE, "lane_ledger_check.py"))
llc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llc)


def sh(repo, *a, env=None):
    e = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
             GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        e.pop(k, None)
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, env=e)
    if p.returncode:
        raise SystemExit("fixture git %s failed: %s" % (a, p.stderr))
    return p.stdout.strip()


def commit(repo, name, text, msg):
    with open(os.path.join(repo, name), "w") as f:
        f.write(text)
    sh(repo, "add", name)
    sh(repo, "commit", "-q", "-m", msg)
    return sh(repo, "rev-parse", "HEAD")


def review_file(td, name, head, pid, verdict="ACCEPTED", blocking=None, digest=None, findings=None):
    pv = {"verdict": verdict, "head": head, "patch_id": pid, "claims": [], "findings": findings or [], "blocking": blocking or []}
    if digest:
        pv["content_digest"] = digest
    path = os.path.join(td, name + ".json")
    with open(path, "w") as f:
        json.dump({"schema": "ky.job_result/1", "status": "done", "proposed_verdict": pv}, f)
    return path, hashlib.sha256(open(path, "rb").read()).hexdigest()


def build(td):
    repo = os.path.join(td, "repo")
    os.makedirs(repo)
    sh(repo, "init", "-q", "-b", "main")
    base = commit(repo, "a.txt", "base\n", "base")
    # lane L1 branches from base; two commits
    sh(repo, "checkout", "-q", "-b", "lane1")
    commit(repo, "l1.txt", "one\n", "l1 a")
    l1 = commit(repo, "l1.txt", "one\ntwo\n", "l1 b")
    # lane L2 (will be squash-merged)
    sh(repo, "checkout", "-q", "-b", "lane2", base)
    l2 = commit(repo, "l2.txt", "x\n", "l2")
    sh(repo, "checkout", "-q", "-b", "lane3", base)
    commit(repo, "l3a.txt", "a\n", "l3 a")
    l3 = commit(repo, "l3b.txt", "b\n", "l3 b")
    # integration: base + merge of lane1 (no-ff) + squash of lane2 content
    sh(repo, "checkout", "-q", "-b", "integration", base)
    sh(repo, "merge", "-q", "--no-ff", "-m", "merge lane1", "lane1")
    m1 = sh(repo, "rev-parse", "HEAD")
    sh(repo, "checkout", "-q", "lane2", "--", "l2.txt")
    sh(repo, "commit", "-q", "-m", "squash lane2")
    sq = sh(repo, "rev-parse", "HEAD")
    sh(repo, "checkout", "-q", "lane3", "--", "l3a.txt", "l3b.txt")
    sh(repo, "commit", "-q", "-m", "composite lane3")
    comp = sh(repo, "rev-parse", "HEAD")
    sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", comp)
    sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-lane1", l1)
    sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-lane2", l2)
    sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-lane3", l3)
    pid1 = llc.patch_id(repo, base, l1)
    pid2 = llc.patch_id(repo, base, l2)
    # a digest-bound artefact
    art = os.path.join(td, "art")
    os.makedirs(art)
    with open(os.path.join(art, "f.py"), "w") as f:
        f.write("print(1)\n")
    dg = llc.tree_digest(art)
    rp1, h1 = review_file(td, "rev1", l1, pid1)
    rp2, h2 = review_file(td, "rev2", l2, pid2)
    rp3, h3 = review_file(td, "rev3", None, None, digest=dg)
    ledger = {
        "schema": llc.SCHEMA, "integration_head": comp,
        "lanes": [
            {"id": "L1", "kind": "git", "branch": "kalayantra/od1-lane1", "review_result_path": rp1, "review_result_sha256": h1,
             "reviewed_head": l1, "base": base, "reviewed_patch_id": pid1, "reviewer_base": base, "open_blocking": 0,
             "merge": {"kind": "merge", "merge_commit": m1, "merged_patch_id": pid1}},
            {"id": "L2", "kind": "git", "branch": "kalayantra/od1-lane2", "review_result_path": rp2, "review_result_sha256": h2,
             "reviewed_head": l2, "base": base, "reviewed_patch_id": pid2, "reviewer_base": base, "open_blocking": 0,
             "merge": {"kind": "squash", "merge_commit": sq, "merged_patch_id": llc.patch_id(repo, base, sq) if False else None}},
            {"id": "L3", "kind": "git", "branch": "kalayantra/od1-lane3", "review_via": "L1", "reviewed_head": l3, "base": base,
             "reviewed_patch_id": llc.patch_id(repo, base, l3), "open_blocking": 0,
             "merge": {"kind": "composite", "merge_commit": comp, "covered_by": "L1", "added_files_total": 2, "edited_in_composite": {}}},
            {"id": "H", "kind": "digest", "review_result_path": rp3, "review_result_sha256": h3, "reviewed_digest": dg,
             "artifact_path": art, "open_blocking": 0},
        ],
    }
    # the squash commit also carries lane1's merge (it sits on top of m1): its own diff is lane2's file only
    ledger["lanes"][1]["merge"]["merged_patch_id"] = llc.patch_id(repo, m1, sq)
    return repo, ledger, dict(base=base, l1=l1, l2=l2, m1=m1, sq=sq, comp=comp, td=td, art=art)


def run(repo, ledger):
    return llc.evaluate(ledger, repo, "origin/kalayantra/od1-integration")


def main():
    llc.REQUIRED_LANES = ["L1", "L2", "L3", "H"]
    results = []

    def expect(name, want, got, extra=""):
        ok = (got["value"] is want)
        results.append(ok)
        why = "; ".join(w for r in got["rows"].values() for w in r["why"]) + " " + " ".join(got["ledger_problems"])
        print("%-4s %-52s -> %-5s %s" % ("ok" if ok else "FAIL", name, got["value"], why.strip()[:140]))

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as td:
        repo, ledger, c = build(td)
        expect("control: correct ledger reads TRUE", True, run(repo, ledger))

        # integration advances by one unrelated commit after the ledger was built
        adv = commit(repo, "unrelated.txt", "u\n", "unrelated advance")
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", adv)
        got = run(repo, ledger)
        expect("reversion: integration advanced since the ledger was built", False, got)
        assert any("stale_ledger" in p for p in got["ledger_problems"]), got["ledger_problems"]
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", c["comp"])
        lg0 = copy.deepcopy(ledger)
        lg0["lanes"][2]["merge"]["edited_in_composite"] = {"l3a.txt": "+1/-1"}
        expect("reversion: composite edit recorded that git does not show", False, run(repo, lg0))
        lg0 = copy.deepcopy(ledger)
        lg0["lanes"][2]["merge"]["added_files_total"] = 3
        expect("reversion: composite file count differs", False, run(repo, lg0))
        lg0 = copy.deepcopy(ledger)
        lg0["lanes"][0]["reviewed_patch_id"] = "0" * 40  # cover row false -> composite row false
        expect("reversion: cover row false makes the composite row false", False, run(repo, lg0))

        def mut(fn):
            lg = copy.deepcopy(ledger)
            fn(lg)
            return lg

        L = lambda lg, i: next(r for r in lg["lanes"] if r["id"] == i)
        expect("reversion: ledger patch-id altered", False, run(repo, mut(lambda lg: L(lg, "L1").update(reviewed_patch_id="0" * 40))))
        expect("reversion: merged patch-id altered", False, run(repo, mut(lambda lg: L(lg, "L1")["merge"].update(merged_patch_id="0" * 40))))
        expect("reversion: required lane removed from ledger", False, run(repo, mut(lambda lg: lg["lanes"].pop(0))))
        expect("reversion: base moved (patch-id no longer matches)", False, run(repo, mut(lambda lg: L(lg, "L1").update(base=c["l1"]))))
        expect("reversion: merge commit not the lane's merge", False, run(repo, mut(lambda lg: L(lg, "L1")["merge"].update(merge_commit=c["sq"]))))
        expect("reversion: lane marked not merged", False, run(repo, mut(lambda lg: L(lg, "L1")["merge"].update(kind="not_merged"))))
        # integration ref moved back before the merge
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", c["base"])
        expect("reversion: integration ref does not contain the merge", False, run(repo, ledger))
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", c["comp"])
        # a branch nobody ledgered
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-ghost", c["l1"])
        expect("reversion: an od1 branch no row claims", False, run(repo, ledger))
        sh(repo, "update-ref", "-d", "refs/remotes/origin/kalayantra/od1-ghost")
        # review file variants
        for label, kw in [("verdict REJECTED", dict(verdict="REJECTED")), ("one open BLOCKING finding", dict(blocking=["B1"]))]:
            lg = copy.deepcopy(ledger)
            r = L(lg, "L1")
            r["review_result_path"], r["review_result_sha256"] = review_file(td, "rev1x", c["l1"], r["reviewed_patch_id"], **kw)
            expect("reversion: review has " + label, False, run(repo, lg))
        # the REAL verdict files carry their findings in `findings` (not in a `blocking` list): TR-BIND recount scenarios, one per spelling the review jobs use
        for label, fnd in [("a finding with severity 'blocking'", [{"id": "F1", "severity": "blocking", "text": "x"}]),
                           ("a finding flagged blocking: true", [{"id": "F2", "blocking": True}]),
                           ("a finding with a B-number id and no severity", [{"id": "B3", "text": "x"}])]:
            lg = copy.deepcopy(ledger)
            r = L(lg, "L1")
            r["review_result_path"], r["review_result_sha256"] = review_file(td, "rev1f", c["l1"], r["reviewed_patch_id"], findings=fnd)
            expect("reversion: review carries " + label, False, run(repo, lg))
        lg = copy.deepcopy(ledger)
        r = L(lg, "L1")
        r["review_result_path"], r["review_result_sha256"] = review_file(td, "rev1n", c["l1"], r["reviewed_patch_id"],
                                                                         findings=[{"id": "N1", "severity": "non_blocking"}, {"id": "N2", "severity": "info"}])
        expect("control: non_blocking findings leave the lane TRUE", True, run(repo, lg))
        lg = copy.deepcopy(ledger)
        r = L(lg, "L1")
        r["review_result_path"], r["review_result_sha256"] = review_file(td, "rev1y", c["l1"], r["reviewed_patch_id"], blocking=["B1"])
        r["open_blocking"] = 0  # ledger lies: says 0 while the review file still carries B1
        expect("reversion: ledger claims 0 BLOCKING, review has 1", False, run(repo, lg))
        lg = copy.deepcopy(ledger)
        r = L(lg, "L1")
        r["review_result_path"], r["review_result_sha256"] = review_file(td, "rev1z", c["base"], r["reviewed_patch_id"])
        expect("reversion: review bound to another head", False, run(repo, lg))
        lg = copy.deepcopy(ledger)
        L(lg, "L1")["review_result_sha256"] = "0" * 64
        expect("reversion: review file changed since the ledger", False, run(repo, lg))
        lg = copy.deepcopy(ledger)
        L(lg, "L1")["reviewer_base"] = None
        expect("reversion: reviewer's patch-id not reproducible", False, run(repo, lg))
        lg = copy.deepcopy(ledger)
        L(lg, "L1").pop("review_result_path")
        expect("reversion: lane with no review", False, run(repo, lg))
        # the merged head differs from the reviewed head: lane gets a further commit that is merged instead
        sh(repo, "checkout", "-q", "lane1")
        l1b = commit(repo, "l1.txt", "one\ntwo\nthree\n", "l1 unreviewed extra")
        sh(repo, "checkout", "-q", "integration")
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", c["comp"])
        sh(repo, "checkout", "-q", "-B", "int2", c["base"])
        sh(repo, "merge", "-q", "--no-ff", "-m", "merge lane1 (unreviewed head)", "lane1")
        m1b = sh(repo, "rev-parse", "HEAD")
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", m1b)
        lg = copy.deepcopy(ledger)
        L(lg, "L1")["merge"]["merge_commit"] = m1b
        L(lg, "L2")["merge"]["kind"] = "not_merged"
        got = run(repo, lg)
        expect("reversion: merged head is not the reviewed head", False, got)
        # squash that carries content the review never saw
        sh(repo, "checkout", "-q", "-B", "int3", c["base"])
        sh(repo, "checkout", "-q", "lane2", "--", "l2.txt")
        with open(os.path.join(repo, "extra.txt"), "w") as f:
            f.write("unreviewed\n")
        sh(repo, "add", "extra.txt")
        sh(repo, "commit", "-q", "-m", "squash lane2 + extra")
        sq2 = sh(repo, "rev-parse", "HEAD")
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", sq2)
        lg = copy.deepcopy(ledger)
        L(lg, "L2")["merge"].update(merge_commit=sq2, merged_patch_id=llc.patch_id(repo, c["base"], sq2))
        L(lg, "L1")["merge"]["kind"] = "not_merged"
        L(lg, "L3")["merge"]["merge_commit"] = sq2
        got = run(repo, lg)
        expect("reversion: squash carries unreviewed content", False, got)
        assert any("merged_patch_differs_from_reviewed" in w for w in got["rows"]["L2"]["why"]), got["rows"]["L2"]
        # digest-bound artefact edited
        sh(repo, "update-ref", "refs/remotes/origin/kalayantra/od1-integration", c["comp"])
        with open(os.path.join(c["art"], "f.py"), "a") as f:
            f.write("print(2)\n")
        expect("reversion: digest-bound artefact edited after review", False, run(repo, ledger))
        # detector cannot run -> null, never green
        try:
            llc.evaluate(ledger, repo, "origin/does-not-exist")
            results.append(False)
            print("FAIL unreadable integration ref did not raise")
        except llc.DetectorError:
            results.append(True)
            print("ok   unreadable integration ref -> detector error (exit 2), not green")
    n_ok = sum(results)
    print("%d/%d scenarios behaved" % (n_ok, len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
