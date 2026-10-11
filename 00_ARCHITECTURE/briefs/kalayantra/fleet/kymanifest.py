#!/usr/bin/env python3
"""kymanifest.py — the bootstrap version manifest of KĀLA-YANTRA v3 (plan v2.7 pairing rule,
§14 B-0c; Astra KU-03, KX-03 entrypoints).

  kymanifest.py build --approved-commit SHA --review REVIEW.json --out VERSIONS.bootstrap.json
  kymanifest.py check VERSIONS.bootstrap.json
  kymanifest.py entrypoints --commit SHA      (the verified entrypoint binding + its digest)

`build` refuses unless every fact it records can be re-observed: the five entrypoint files
(plan, cockpit prompt, owner decisions, strategy, surrogate agent) are byte-identical to
their blobs at the authorised source commit; every listed component is committed
and unmodified; no unlisted file sits in a covered directory; each canonical/compatibility
pair holds the same bytes; the review receipt is ACCEPTED, names that source commit and
covers exactly the component bytes on disk. Qualification receipts are recorded with their
results (a launcher refuses anything but PASS; the manifest never upgrades one). `check` recomputes all of it. The output carries no timestamp: two builds of the same
tree give the same bytes. It can never authorise campaign admission (mode: bootstrap).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

K = "00_ARCHITECTURE/briefs/kalayantra"
C = "00_ARCHITECTURE/control/kalayantra"
FLEET = K + "/fleet"
PLAN_VERSION = "2.7"
ENTRYPOINTS = {"plan": K + "/KALAYANTRA_RELAUNCH_PLAN_v2_7.md",
               "cockpit_prompt": K + "/KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md",
               "owner_decisions": K + "/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md",
               "strategy": K + "/KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md",
               "surrogate_agent": ".claude/agents/kalayantra-owner-surrogate.md"}
BUNDLE = list(ENTRYPOINTS.values())
# KU-03: the plan's named path is canonical; the prompt's differently named output is a
# compatibility copy with exactly the same reviewed bytes (content version 2.2).
PAIRS = [("WORKTREE_DISPOSITIONS", K + "/WORKTREE_DISPOSITIONS_v2_1.md", K + "/WORKTREE_DISPOSITIONS_v2_2.md"),
         ("ACCEPTANCE_ROOTS", C + "/ACCEPTANCE_ROOTS_v2_1.json", C + "/ACCEPTANCE_ROOTS_v2_2.json"),
         ("CLOSURE", C + "/CLOSURE_v2_1.json", C + "/CLOSURE_v2_2.json")]
COMPONENT_LIST = FLEET + "/BOOTSTRAP_COMPONENTS.txt"
COVERED_DIRS = [FLEET + "/" + d for d in ("cards", "schemas", "templates", "launchd", "prompts")]
ROSTER = ["claude-opus-5-5", "claude-sonnet-5-5"]


class Refused(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def entrypoints_digest(entrypoints):
    """sha256 over the canonical {role: {path, git_blob}} mapping — the `entrypoints_digest` a
    surrogate decision carries in `authority` and the veto handler compares (plan pairing rule)."""
    return hashlib.sha256(canonical({r: {"path": e["path"], "git_blob": e["git_blob"]}
                                     for r, e in entrypoints.items()})).hexdigest()


def observe_entrypoints(repo, approved):
    """The five role→path bindings, each byte-identical to its blob at the authorised commit."""
    entrypoints = {}
    for role, rel in sorted(ENTRYPOINTS.items()):
        if git(repo, "cat-file", "-e", "%s:%s" % (approved, rel)).returncode != 0:
            raise Refused("bundle file absent at the approved commit: " + rel)
        if not os.path.isfile(os.path.join(repo, rel)) or git(repo, "diff", "--quiet", approved, "--", rel).returncode != 0:
            raise Refused("bundle file differs from the approved commit: " + rel)
        entrypoints[role] = {"path": rel, "sha256": sha256(os.path.join(repo, rel)),
                             "git_blob": git(repo, "rev-parse", "%s:%s" % (approved, rel)).stdout.strip()}
    return entrypoints


def read_components(repo):
    path = os.path.join(repo, COMPONENT_LIST)
    if not os.path.isfile(path):
        raise Refused("component list missing: " + COMPONENT_LIST)
    out = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            if line.startswith("/") or ".." in line.split("/"):
                raise Refused("component path must be repository-relative: " + line)
            out.append(line)
    if len(out) != len(set(out)):
        raise Refused("component list has duplicates")
    if COMPONENT_LIST not in out:
        raise Refused("component list must list itself")
    return sorted(out)


def observe(repo, run_dir, approved, review_path):
    """Everything the manifest asserts, observed from disk and git. Raises Refused."""
    repo = os.path.realpath(repo)
    if git(repo, "cat-file", "-e", approved + "^{commit}").returncode != 0:
        raise Refused("approved commit not found: " + approved)
    full = git(repo, "rev-parse", approved + "^{commit}").stdout.strip()
    if full != approved:
        raise Refused("approved commit must be the full 40-hex id")
    entrypoints = observe_entrypoints(repo, approved)
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    listed = read_components(repo)
    components = []
    for rel in listed:
        if not os.path.isfile(os.path.join(repo, rel)):
            raise Refused("component missing: " + rel)
        if git(repo, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
            raise Refused("component is not committed: " + rel)
        if git(repo, "diff", "--quiet", "HEAD", "--", rel).returncode != 0:
            raise Refused("component differs from HEAD: " + rel)
        components.append({"path": rel, "sha256": sha256(os.path.join(repo, rel))})
    for d in COVERED_DIRS:
        for root, _dirs, files in os.walk(os.path.join(repo, d)):
            for name in files:
                rel = os.path.relpath(os.path.join(root, name), repo)
                if rel not in listed and not name.startswith(".") and "__pycache__" not in rel:
                    raise Refused("unlisted file in a covered directory: " + rel)
    pairs = []
    for role, canon, compat in PAIRS:
        a, b = os.path.join(repo, canon), os.path.join(repo, compat)
        if not (os.path.isfile(a) and os.path.isfile(b)):
            raise Refused("generated-output copy missing for " + role)
        if sha256(a) != sha256(b):
            raise Refused("canonical and compatibility copies differ for " + role)
        pairs.append({"role": role, "canonical": canon, "compatibility": compat, "canonical_abs": a,
                      "compatibility_abs": b, "sha256": sha256(a), "content_version": "2.2"})
    probes_path = os.path.join(run_dir, "PROBES.json")
    if not os.path.isfile(probes_path):
        raise Refused("probes not recorded: " + probes_path)
    probes = json.load(open(probes_path))
    contexts = probes.get("contexts") or {}

    def works(ctx):
        v = contexts.get(ctx)
        return isinstance(v, dict) and all((v.get(m) or {}).get("sign_in") == "works" for m in ROSTER)

    probe_rec = {"path": probes_path, "sha256": sha256(probes_path),
                 "sign_in_works_shell": works("shell"), "sign_in_works_launchd": works("launchd"),
                 "extra_lean_flags": (probes.get("extra_lean_flags") or {}).get("chosen")}
    if not os.path.isfile(review_path):
        raise Refused("review record missing: " + review_path)
    review = json.load(open(review_path))
    if review.get("verdict") != "ACCEPTED":
        raise Refused("review verdict is not ACCEPTED: %r" % review.get("verdict"))
    if not review.get("reviewer_session_id"):
        raise Refused("review record names no reviewer session")
    if review.get("source_commit") != approved:
        raise Refused("review record is not bound to the authorised source commit")
    qualifications = []
    qdir = os.path.join(run_dir, "QUALIFICATIONS")
    for name in sorted(os.listdir(qdir)) if os.path.isdir(qdir) else []:
        if name.endswith(".json"):
            q = json.load(open(os.path.join(qdir, name)))
            qualifications.append({"path": os.path.join(qdir, name), "sha256": sha256(os.path.join(qdir, name)),
                                   "result": q.get("result") if q.get("result") in ("PASS", "FAIL") else "unknown"})
    reviewed = review.get("inputs") or {}
    for c in components:
        if reviewed.get(c["path"]) != c["sha256"]:
            raise Refused("review does not cover the bytes on disk: " + c["path"])
    review_rel = os.path.relpath(os.path.realpath(review_path), repo)
    return {"schema": "ky.versions_bootstrap/1", "mode": "bootstrap", "plan_version": PLAN_VERSION,
            "authorises": "Wave B bootstrap work only; never campaign admission or READY_TO_START",
            "approved_source_commit": approved, "entrypoints": entrypoints,
            "entrypoints_digest": entrypoints_digest(entrypoints), "components_commit": head,
            "components": components, "generated_pairs": pairs, "probes": probe_rec,
            "qualifications": qualifications,
            "qualifications_all_pass": bool(qualifications) and all(q["result"] == "PASS" for q in qualifications),
            "review": {"path": review_rel, "sha256": sha256(review_path), "verdict": "ACCEPTED",
                       "reviewer_session_id": review["reviewer_session_id"]}}


def with_digest(obj):
    obj = dict(obj)
    obj["manifest_sha256"] = hashlib.sha256(canonical(obj)).hexdigest()
    return obj


def cmd_build(a):
    try:
        manifest = with_digest(observe(a.repo, a.run, a.approved_commit, a.review))
    except Refused as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    os.replace(tmp, a.out)
    print(json.dumps({"out": a.out, "manifest_sha256": manifest["manifest_sha256"], "file_sha256": sha256(a.out),
                      "components": len(manifest["components"])}))
    return 0


def cmd_check(a):
    try:
        stored = json.load(open(a.manifest))
    except (OSError, ValueError) as e:
        print("refused: manifest unreadable: %s" % e, file=sys.stderr)
        return 1
    body = {k: v for k, v in stored.items() if k != "manifest_sha256"}
    if stored.get("manifest_sha256") != hashlib.sha256(canonical(body)).hexdigest():
        print("refused: manifest digest does not match its content", file=sys.stderr)
        return 1
    if stored.get("mode") != "bootstrap":
        print("refused: not a bootstrap manifest", file=sys.stderr)
        return 1
    try:
        review = os.path.join(os.path.realpath(a.repo), (stored.get("review") or {}).get("path", ""))
        now = observe(a.repo, a.run, stored.get("approved_source_commit", ""), review)
    except Refused as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    diffs = sorted(k for k in set(body) | set(now) if body.get(k) != now.get(k))
    if diffs:
        print("refused: manifest no longer matches disk in: " + ", ".join(diffs), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "manifest_sha256": stored["manifest_sha256"], "components": len(now["components"])}))
    return 0


def cmd_entrypoints(a):
    repo = os.path.realpath(a.repo)
    full = git(repo, "rev-parse", "--verify", "--quiet", a.commit + "^{commit}").stdout.strip()
    if full != a.commit:
        print("refused: --commit must be an existing full 40-hex commit id", file=sys.stderr)
        return 1
    try:
        entrypoints = observe_entrypoints(repo, a.commit)
    except Refused as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    print(json.dumps({"source_commit": a.commit, "entrypoints": entrypoints,
                      "entrypoints_digest": entrypoints_digest(entrypoints)}, indent=1, sort_keys=True))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    here_repo = git(os.path.dirname(os.path.realpath(__file__)), "rev-parse", "--show-toplevel").stdout.strip()

    def common(sp):
        sp.add_argument("--repo", default=here_repo)
        sp.add_argument("--run", default=os.environ.get("KY_RUN", "/Users/Dev/kalayantra/run"))

    b = sub.add_parser("build")
    common(b)
    b.add_argument("--approved-commit", required=True)
    b.add_argument("--review", required=True)
    b.add_argument("--out", required=True)
    b.set_defaults(fn=cmd_build)
    c = sub.add_parser("check")
    common(c)
    c.add_argument("manifest")
    c.set_defaults(fn=cmd_check)
    e = sub.add_parser("entrypoints")
    e.add_argument("--repo", default=here_repo)
    e.add_argument("--commit", required=True)
    e.set_defaults(fn=cmd_entrypoints)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
