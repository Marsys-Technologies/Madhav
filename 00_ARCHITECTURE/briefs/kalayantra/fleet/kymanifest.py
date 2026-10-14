#!/usr/bin/env python3
"""kymanifest.py — the bootstrap version manifest of KĀLA-YANTRA v3 (plan v2.7 pairing rule,
§14 B-0c; Astra KU-03, KX-03 entrypoints).

  kymanifest.py build --approved-commit SHA --review REVIEW.json --out VERSIONS.bootstrap.json
  kymanifest.py check VERSIONS.bootstrap.json
  kymanifest.py entrypoints --commit SHA      (the verified entrypoint binding + its digest)

`build` refuses unless every fact it records can be re-observed:
  * the five entrypoint files (plan, cockpit prompt, owner decisions, strategy, surrogate agent)
    hold exactly the bytes of their blobs at the authorised source commit;
  * every listed component is tracked and holds exactly the bytes of its blob at HEAD, which is
    recorded as `components_commit`; no unlisted file sits in a covered directory;
  * each canonical/compatibility pair (KU-03) holds the same bytes;
  * the launch probes show sign-in working from a shell and under launchd;
  * launch-qualification receipts exist, each manifest-bound receipt says PASS, and the reviewed
    harness itself (`kyqualify.py check --require-context launchd`) accepts each against its
    launch configuration. External loop configurations are reported only on stdout: the installer/controller
    own those receipts, and kyversion checks their installer-recorded hashes and PASS results;
  * the review receipt says ACCEPTED, names its reviewer session and the authorised source
    commit, and is backed by per-area review records on disk — each ACCEPTED, each with its own
    reviewer session, together covering exactly the component bytes on disk. A self-declared
    verdict without those records is refused.
Tranches (owner decision 2026-10-12): the component list may mark files as deferred with a
line `# tranche: deferred` — every path after it is listed (so it is not an "unlisted file")
and recorded with its hash under `deferred_components`, but it is NOT bound: no review is
required for it, nothing may be launched or installed on its strength, and it must enter a
later manifest through its own accepted review. A line `# tranche: bound` switches back.
`check` recomputes all of it against the recorded `components_commit` (a later commit that
leaves the components untouched does not invalidate the manifest). The output carries no
timestamp: two builds of the same tree give the same bytes. A bootstrap manifest can never
authorise campaign admission (mode: bootstrap).

Byte identity is always a comparison of the file's bytes with `git cat-file blob`, never
`git diff --quiet` (which index flags and filters can blind). Stdlib only.
"""
import argparse
import hashlib
import json
import os
import re
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
# compatibility copy holding exactly the same reviewed bytes. "2.2" is the content version
# KU-03 declares for these outputs: a declared label, not something measured here.
PAIRS = [("WORKTREE_DISPOSITIONS", K + "/WORKTREE_DISPOSITIONS_v2_1.md", K + "/WORKTREE_DISPOSITIONS_v2_2.md"),
         ("ACCEPTANCE_ROOTS", C + "/ACCEPTANCE_ROOTS_v2_1.json", C + "/ACCEPTANCE_ROOTS_v2_2.json"),
         ("CLOSURE", C + "/CLOSURE_v2_1.json", C + "/CLOSURE_v2_2.json")]
PAIR_CONTENT_VERSION_DECLARED = "2.2"
COMPONENT_LIST = FLEET + "/BOOTSTRAP_COMPONENTS.txt"
COVERED_DIRS = [FLEET + "/" + d for d in ("cards", "schemas", "templates", "launchd", "prompts")]
ROSTER = ["claude-opus-5-5", "claude-sonnet-5-5"]
HARNESS = FLEET + "/kyqualify.py"
LAUNCH_CONFIG = FLEET + "/templates/LAUNCH_CONFIG.%s.json"
LAUNCH_CONFIG_CODEX = FLEET + "/templates/LAUNCH_CONFIG.%s.codex.json"     # a receipt that says "engine": "codex"


LOOP_ROLES = ("planner", "conductor")     # kyloop.ROLES, kept as a constant so this file needs no sibling to import;
                                          # tests/test_kymanifest.py compares it with kyloop.ROLES


def repository_path(repo, path):
    """Repository files use relative identities; external (including run) paths retain theirs."""
    real = os.path.realpath(path)
    return os.path.relpath(real, repo) if os.path.commonpath((repo, real)) == repo else path


def launch_config_of(doc):
    """Select a variant from receipt-bound inputs, never the receipt filename.

    The harness subsequently rechecks every bind against this exact configuration.
    TESTS is an environment-name variant; chart data names its MCP file on argv.
    A Codex chart variant, if supplied, still needs its own reviewed bound template.
    """
    role = doc.get("role") if isinstance(doc, dict) else None
    if not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", role):
        return None
    if doc.get("engine", "claude") not in ("claude", "codex"):
        return None
    binds = doc.get("binds", {})
    if not isinstance(binds, dict):
        return None
    names, argv = binds.get("env_names", []), binds.get("argv", [])
    if (not isinstance(names, list) or not all(isinstance(n, str) for n in names)
            or not isinstance(argv, list) or not all(isinstance(a, str) for a in argv)):
        return None
    chart = False
    if "--mcp-config" in argv:
        i = argv.index("--mcp-config")
        if argv.count("--mcp-config") != 1 or i + 1 == len(argv):
            return None
        chart = os.path.basename(argv[i + 1]) == "mcp.marsys-only.json"
    variant = (".chart" if chart else "") + (".tests" if "TESTS" in names else "")
    return (LAUNCH_CONFIG_CODEX if doc.get("engine") == "codex" else LAUNCH_CONFIG) % (role + variant)


class Refused(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args, text=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=text, env=env)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError, RecursionError) as e:
        raise Refused("%s unreadable: %s (%s)" % (what, path, type(e).__name__))
    if not isinstance(doc, dict):
        raise Refused("%s is not a JSON object: %s" % (what, path))
    return doc


def same_bytes_as_blob(repo, commit, rel):
    """(True, blob id) when the working file holds exactly the bytes of commit:rel; else (False, reason)."""
    oid = git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (commit, rel))
    if oid.returncode != 0 or not oid.stdout.strip():
        return False, "absent"
    blob = git(repo, "cat-file", "blob", oid.stdout.strip(), text=False)
    if blob.returncode != 0:
        return False, "blob unreadable"
    try:
        with open(os.path.join(repo, rel), "rb") as f:
            data = f.read()
    except OSError:
        return False, "file missing"
    return (True, oid.stdout.strip()) if data == blob.stdout else (False, "bytes differ")


def entrypoints_digest(entrypoints):
    """sha256 over the canonical {role: {path, git_blob}} mapping — the `entrypoints_digest` a
    surrogate decision carries in `authority` and the veto handler compares (plan pairing rule)."""
    return hashlib.sha256(canonical({r: {"path": e["path"], "git_blob": e["git_blob"]}
                                     for r, e in entrypoints.items()})).hexdigest()


def full_commit(repo, commit, what):
    r = git(repo, "rev-parse", "--verify", "--quiet", str(commit) + "^{commit}")
    if r.returncode != 0 or not r.stdout.strip():
        raise Refused("%s not found: %s" % (what, commit))
    if r.stdout.strip() != commit:
        raise Refused("%s must be the full 40-hex id" % what)
    return commit


def observe_entrypoints(repo, approved):
    """The five role→path bindings, each holding exactly the bytes of its blob at the authorised commit."""
    entrypoints = {}
    for role, rel in sorted(ENTRYPOINTS.items()):
        ok, detail = same_bytes_as_blob(repo, approved, rel)
        if not ok:
            raise Refused(("bundle file absent at the approved commit: " if detail == "absent"
                           else "bundle file differs from the approved commit: ") + rel)
        entrypoints[role] = {"path": rel, "sha256": sha256(os.path.join(repo, rel)), "git_blob": detail}
    return entrypoints


def read_component_list(repo):
    """(bound, deferred): repository-relative paths, each sorted. Bound files are what the manifest
    binds and a review must cover; deferred files are listed and hashed only."""
    path = os.path.join(repo, COMPONENT_LIST)
    if not os.path.isfile(path):
        raise Refused("component list missing: " + COMPONENT_LIST)
    bound, deferred, target = [], [], None
    target = bound
    for raw in open(path, encoding="utf-8").read().splitlines():
        marker = raw.strip().lower()
        if marker.startswith("# tranche:"):
            word = marker[len("# tranche:"):].split()[:1]
            if word == ["deferred"]:
                target = deferred
            elif word == ["bound"]:
                target = bound
            else:
                raise Refused("unknown tranche marker in the component list: " + raw.strip())
            continue
        line = raw.split("#", 1)[0].strip()
        if line:
            if line.startswith("/") or ".." in line.split("/"):
                raise Refused("component path must be repository-relative: " + line)
            target.append(line)
    both = bound + deferred
    if len(both) != len(set(both)):
        raise Refused("component list has duplicates")
    if COMPONENT_LIST not in bound:
        raise Refused("component list must list itself among the bound components")
    return sorted(bound), sorted(deferred)


def read_components(repo):
    """Every listed path, bound and deferred."""
    bound, deferred = read_component_list(repo)
    return sorted(bound + deferred)


def observe_components(repo, components_commit, at_build):
    """(bound components, deferred components). Both must hold the bytes of the components commit —
    a deferred file is unreviewed, not unpinned."""
    bound, deferred = read_component_list(repo)
    listed = set(bound) | set(deferred)
    components, later = [], []
    for rel, out in [(r, components) for r in bound] + [(r, later) for r in deferred]:
        if not os.path.isfile(os.path.join(repo, rel)):
            raise Refused("component missing: " + rel)
        if at_build and git(repo, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
            raise Refused("component is not committed: " + rel)
        ok, detail = same_bytes_as_blob(repo, components_commit, rel)
        if not ok:
            raise Refused(("component is not committed: " if detail == "absent"
                           else "component differs from the components commit: ") + rel)
        out.append({"path": rel, "sha256": sha256(os.path.join(repo, rel))})
    for d in COVERED_DIRS:
        for root, _dirs, files in os.walk(os.path.join(repo, d)):
            for name in files:
                rel = os.path.relpath(os.path.join(root, name), repo)
                if rel not in listed and not name.startswith(".") and "__pycache__" not in rel:
                    raise Refused("unlisted file in a covered directory: " + rel)
    return components, later


def observe_pairs(repo):
    pairs = []
    for role, canon, compat in PAIRS:
        a, b = os.path.join(repo, canon), os.path.join(repo, compat)
        if not (os.path.isfile(a) and os.path.isfile(b)):
            raise Refused("generated-output copy missing for " + role)
        if sha256(a) != sha256(b):
            raise Refused("canonical and compatibility copies differ for " + role)
        pairs.append({"role": role, "canonical": canon, "compatibility": compat, "sha256": sha256(a),
                      "content_version_declared": PAIR_CONTENT_VERSION_DECLARED})
    return pairs


def observe_probes(run_dir):
    path = os.path.join(run_dir, "PROBES.json")
    if not os.path.isfile(path):
        raise Refused("probes not recorded: " + path)
    doc = load_json(path, "probes")
    contexts = doc.get("contexts") or {}
    for ctx in ("shell", "launchd"):
        v = contexts.get(ctx)
        if not (isinstance(v, dict) and all((v.get(m) or {}).get("sign_in") == "works" for m in ROSTER)):
            raise Refused("probes do not show sign-in working for every roster model in the %s context" % ctx)
    return {"path": path, "sha256": sha256(path), "sign_in_works_shell": True, "sign_in_works_launchd": True,
            "extra_lean_flags": (doc.get("extra_lean_flags") or {}).get("chosen")}


def observe_qualifications(repo, run_dir, bound=None, reported=None):
    qdir = os.path.join(run_dir, "QUALIFICATIONS")
    names = sorted(n for n in os.listdir(qdir) if n.endswith(".json")) if os.path.isdir(qdir) else []
    if not names:
        raise Refused("no launch-qualification receipt recorded under " + qdir)
    out = []
    for name in names:
        path = os.path.join(qdir, name)
        doc = load_json(path, "qualification receipt")
        evidence = doc.get("evidence")
        evidence_dir = evidence.get("dir") if isinstance(evidence, dict) else None
        if doc.get("role") in LOOP_ROLES and isinstance(evidence_dir, str) and os.path.isabs(evidence_dir):
            config_path = os.path.join(evidence_dir, "launch_config.json")
            if os.path.commonpath((repo, os.path.realpath(config_path))) != repo:
                # Installer step 9 verifies the evidence; kyversion binds its receipt hash.
                if reported is not None:
                    reported.append(name)
                continue
        if doc.get("result") != "PASS":
            raise Refused("qualification receipt is not PASS (%r): %s" % (doc.get("result"), name))
        role = doc.get("role")
        listed = launch_config_of(doc)
        config = os.path.join(repo, listed) if listed else None
        if not config or not os.path.isfile(config):
            raise Refused("no launch configuration in the reviewed source for the receipt's role: " + name)
        if bound is not None and listed not in bound:
            raise Refused("the receipt's launch configuration is not a bound component (deferred or unlisted): " + name)
        # -I: the harness must not import a module planted beside it or named by the environment.
        harness = subprocess.run([sys.executable, "-I", "-B", os.path.join(repo, HARNESS), "check", path, "--config", config,
                                  "--require-context", "launchd"], capture_output=True, text=True)
        if harness.returncode != 0:
            raise Refused("the qualification harness does not accept %s (exit %d)" % (name, harness.returncode))
        out.append({"path": path, "sha256": sha256(path), "result": "PASS", "role": role, "model": doc.get("model"),
                    "context": doc.get("context"), "config": listed, "config_sha256": sha256(config)})
    return out


def observe_review(repo, review_path, approved, components, recorded_locations=()):
    if not os.path.isfile(review_path):
        raise Refused("review record missing: " + review_path)
    review = load_json(review_path, "review record")
    if review.get("verdict") != "ACCEPTED":
        raise Refused("review verdict is not ACCEPTED: %r" % review.get("verdict"))
    if not review.get("reviewer_session_id"):
        raise Refused("review record names no reviewer session")
    if review.get("source_commit") != approved:
        raise Refused("review record is not bound to the authorised source commit")
    reviewed = review.get("inputs") or {}
    for c in components:
        if reviewed.get(c["path"]) != c["sha256"]:
            raise Refused("review does not cover the bytes on disk: " + c["path"])
    areas = review.get("area_reviews")
    if not isinstance(areas, list) or not areas:
        raise Refused("review record carries no per-area review records")
    covered, recorded, sessions = {}, [], {review["reviewer_session_id"]}
    for entry in areas:
        if not isinstance(entry, dict) or not isinstance(entry.get("record"), str):
            raise Refused("malformed per-area review entry")
        path = os.path.join(repo, entry["record"])
        # An unchanged review may embed its original checkout's absolute location.
        # The digest-bound relative identity directs checks to THIS checkout's bytes.
        local = [r["record"] for r in recorded_locations if r.get("record_sha256") == entry.get("record_sha256")
                 and isinstance(r.get("record"), str) and not os.path.isabs(r["record"])
                 and ".." not in r["record"].split("/")]
        if os.path.isabs(entry["record"]) and len(local) == 1:
            path = os.path.join(repo, local[0])
        if not os.path.isfile(path) or sha256(path) != entry.get("record_sha256"):
            raise Refused("per-area review record missing or changed: " + path)
        doc = load_json(path, "per-area review record")
        verdict = (doc.get("review") or {}).get("verdict") if isinstance(doc.get("review"), dict) else None
        if verdict != "ACCEPTED":
            raise Refused("per-area review is not ACCEPTED (%r): %s" % (verdict, doc.get("area")))
        session = doc.get("reviewer_session_id")
        if not session:
            raise Refused("per-area review names no reviewer session: %s" % doc.get("area"))
        if session in sessions:
            raise Refused("one reviewer session signs twice: %s" % session)
        sessions.add(session)
        if isinstance(doc.get("inputs"), dict):
            covered.update(doc["inputs"])
        recorded.append({"area": doc.get("area"), "record": repository_path(repo, path), "record_sha256": entry["record_sha256"],
                         "reviewer_session_id": session})
    for c in components:
        if covered.get(c["path"]) != c["sha256"]:
            raise Refused("no ACCEPTED per-area review covers the bytes on disk: " + c["path"])
    return {"path": repository_path(repo, review_path), "sha256": sha256(review_path),
            "verdict": "ACCEPTED", "reviewer_session_id": review["reviewer_session_id"],
            "area_reviews": sorted(recorded, key=lambda r: str(r["area"]))}


def observe(repo, run_dir, approved, review_path, components_commit=None, recorded_locations=(), reported=None):
    """Everything the manifest asserts, observed from disk and git. Raises Refused."""
    repo = os.path.realpath(repo)
    full_commit(repo, approved, "approved commit")
    entrypoints = observe_entrypoints(repo, approved)
    at_build = components_commit is None
    if at_build:
        components_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
    full_commit(repo, components_commit, "components commit")
    components, deferred = observe_components(repo, components_commit, at_build)
    qualifications = observe_qualifications(repo, run_dir, {c["path"] for c in components}, reported)
    return {"schema": "ky.versions_bootstrap/1", "mode": "bootstrap", "plan_version": PLAN_VERSION,
            "deferred_components": deferred,
            "deferred_note": "listed and pinned, NOT reviewed and NOT bound: nothing is launched or installed on their strength",
            "authorises": "Wave B bootstrap work only; never campaign admission or READY_TO_START",
            "approved_source_commit": approved, "entrypoints": entrypoints,
            "entrypoints_digest": entrypoints_digest(entrypoints), "components_commit": components_commit,
            "components": components, "generated_pairs": observe_pairs(repo), "probes": observe_probes(run_dir),
            "qualifications": qualifications,
            "qualifications_all_pass": True,
            "review": observe_review(repo, review_path, approved, components, recorded_locations)}


def with_digest(obj):
    obj = dict(obj)
    obj["manifest_sha256"] = hashlib.sha256(canonical({k: v for k, v in obj.items() if k != "manifest_sha256"})).hexdigest()
    return obj


def cmd_build(a):
    reported = []
    try:
        manifest = with_digest(observe(a.repo, a.run, a.approved_commit, a.review, reported=reported))
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
                      "components": len(manifest["components"]), "loop_qualifications_outside_manifest": reported}))
    return 0


def cmd_check(a):
    try:
        stored = load_json(a.manifest, "manifest")
    except Refused as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    body = {k: v for k, v in stored.items() if k != "manifest_sha256"}
    if stored.get("manifest_sha256") != hashlib.sha256(canonical(body)).hexdigest():
        print("refused: manifest digest does not match its content", file=sys.stderr)
        return 1
    if stored.get("mode") != "bootstrap":
        print("refused: not a bootstrap manifest", file=sys.stderr)
        return 1
    reported = []
    try:
        review = os.path.join(os.path.realpath(a.repo), str((stored.get("review") or {}).get("path", "")))
        now = observe(a.repo, a.run, str(stored.get("approved_source_commit", "")), review,
                      components_commit=str(stored.get("components_commit", "")),
                      recorded_locations=(stored.get("review") or {}).get("area_reviews", []), reported=reported)
    except Refused as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    diffs = sorted(k for k in set(body) | set(now) if body.get(k) != now.get(k))
    if diffs:
        print("refused: manifest no longer matches disk in: " + ", ".join(diffs), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "manifest_sha256": stored["manifest_sha256"], "components": len(now["components"]),
                      "loop_qualifications_outside_manifest": reported}))
    return 0


def cmd_entrypoints(a):
    repo = os.path.realpath(a.repo)
    try:
        full_commit(repo, a.commit, "--commit")
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
