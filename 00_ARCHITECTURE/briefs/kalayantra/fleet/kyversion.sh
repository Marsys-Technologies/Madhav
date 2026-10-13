#!/bin/bash
# kyversion.sh — is the installed KĀLA-YANTRA bundle the reviewed one? (plan v2.7 pairing rule, §10, §11,
# §14 B-2/B-5; Astra KU-03). Read-only: it writes nothing — not even a temporary file — and uses no network.
#
#   kyversion.sh --bootstrap                              the bootstrap installation (B-2, B-3)
#   kyversion.sh                                          the final installation (B-5)
#   kyversion.sh --expected-manifest-digest <64 hex>      the final installation, bound to the activation chain
#   anything else: exit 64.
#
# Exit 0 only when every check of the mode ran in this call and passed; stdout is then
#   kyversion: OK mode=<bootstrap|final> manifest_sha256=<hex> authorises=<bootstrap-only|final-bundle>
# (the final modes add ` tracker_revision=recorded`: the receipt's value, not re-observed here).
# Otherwise exit 1 and one stderr line `kyversion: REFUSED <code>: <detail>` per failed check; a check that
# cannot run refuses.
#
# Environment (as the plists export it): KY_ROOT (default as kyctl.sh), KY_RUN (default $KY_ROOT/run),
# KY_FLEET (default: this script's directory), KY_SOURCE_REPO (the git checkout the manifest is checked in;
# default as kyctl.sh). Read: $KY_RUN/INSTALL_RECEIPT.json, $KY_RUN/ACTIVATION_RECORD*.json, and
# $KY_RUN/VERSIONS.bootstrap.json (--bootstrap) or $KY_RUN/VERSIONS.json (the final modes) — never both.
#
#   E1  KY_RUN, KY_FLEET and KY_SOURCE_REPO are absolute paths (else nothing is checked)
#   E2  KY_SOURCE_REPO is the top of a git work tree
#   --bootstrap                                           the final modes
#   B1  receipt mode is "bootstrap"                       F1  receipt mode is "final"
#   B2  `kymanifest.py check` exits 0 and prints ok:true  F2  VERSIONS.json says mode "final", carries the five-role
#       with the manifest file's own manifest_sha256          entrypoints and its manifest_sha256 is its content's
#   B3  the receipt binds that digest                     F3  as B3
#   B4  every installed component is a manifest           F4  as B4
#       component and holds its bytes
#   B5  KU-03: both copies of WORKTREE_DISPOSITIONS,      F5  as B5
#       ACCEPTANCE_ROOTS and CLOSURE hold the recorded bytes
#   B6  any ACTIVATION_RECORD*.json forms a valid chain   F6  as B6
#       (the rules of kyloop.py `activation_chain`)       F7  the receipt's evidence: rehearsal, coverage, packets,
#                                                             backfill, tracker revision
#   B7  installer loop receipts match recorded sha256 and PASS  F8  as B7
#   --expected-manifest-digest D adds   D1  the manifest's digest is D
#                                       D2  a valid chain exists and its terminal link's manifest digest is D
#   E0  the check program itself could not run or failed
#
# B6/F6 judge the chain's structure only and pass when there is no record at all; D2 alone binds the manifest
# to the chain. --bootstrap prints `bootstrap-only`: it can never authorise campaign admission.
set -u

usage() { echo "usage: kyversion.sh [--bootstrap | --expected-manifest-digest <64 hex>]" >&2; exit 64; }

MODE=final
DIGEST=""
case "$#" in
  0) ;;
  1) [ "$1" = "--bootstrap" ] || usage
     MODE=bootstrap ;;
  2) [ "$1" = "--expected-manifest-digest" ] || usage
     case "$2" in *[!0123456789abcdef]*) usage ;; esac       # the digits are listed: a range depends on the locale
     [ "${#2}" -eq 64 ] || usage
     MODE=expected; DIGEST="$2" ;;
  *) usage ;;
esac

HERE="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ -z "$HERE" ]; then echo "kyversion: REFUSED E0: the script's own directory cannot be resolved" >&2; exit 1; fi
SELF="$HERE/$(basename "$0")"
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
KY_FLEET="${KY_FLEET:-$HERE}"
KY_SOURCE_REPO="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
PY=/opt/homebrew/bin/python3
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then echo "kyversion: REFUSED E0: no python3 to run the checks with" >&2; exit 1; fi

# The checks are the stdlib program below the final `exit`, read from this file by the interpreter itself: a
# here-document on stdin would make bash 3.2 write a temporary file.
rc=0
"$PY" -I -B -c 'import sys
quote = chr(39)
with open(sys.argv[1], encoding="utf-8") as f:
    text = f.read()
program = text.split("\n: <<" + quote + "KYVERSION_PY" + quote + "\n", 1)[1].rsplit("\nKYVERSION_PY\n", 1)[0]
exec(compile(program, sys.argv[1], "exec"))' "$SELF" "$MODE" "$DIGEST" "$KY_RUN" "$KY_FLEET" "$KY_SOURCE_REPO" </dev/null || rc=$?
case "$rc" in
  0) exit 0 ;;
  1) exit 1 ;;
  *) echo "kyversion: REFUSED E0: the check program ended with status $rc" >&2; exit 1 ;;
esac
exit 1
: <<'KYVERSION_PY'
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
# the three patterns of kyloop.py `activation_chain`, unchanged
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
ACTIVATION_NAME = re.compile(r"^ACTIVATION_RECORD(?:\.([1-9][0-9]{0,5}))?\.json\Z")
ENTRYPOINT_ROLES = ("plan", "cockpit_prompt", "owner_decisions", "strategy", "surrogate_agent")
LOOP_ROLES = ("planner", "conductor")  # pinned against kyloop.ROLES by the regression suite
PAIR_ROLES = ("WORKTREE_DISPOSITIONS", "ACCEPTANCE_ROOTS", "CLOSURE")
CHILD_TIMEOUT = 240     # the callers allow this script 300 s: refuse in words before they give up on it


def flat(text, limit=1000):
    text = " ".join(str(text).split())
    return "".join(ch if ch.isprintable() else "?" for ch in text)[:limit]


def read_json(path):
    """(object, None) or (None, reason); never raises."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError, RecursionError) as e:
        return None, "unreadable (%s)" % type(e).__name__


def sha_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, ValueError):
        return None


def canonical(obj):
    """kymanifest.py `canonical`."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def file_problem(what, path, want, regular_only=False):
    """None when `path` is an absolute path to a file holding the bytes of sha256 `want`; else why not.
    regular_only: the path itself must be a regular file — a link to one is not."""
    if not isinstance(path, str) or not os.path.isabs(path):
        return "%s: no absolute path recorded (%r)" % (what, path)
    if not isinstance(want, str) or not HEX64.match(want):
        return "%s: no sha256 recorded for %s" % (what, path)
    try:
        mode = (os.lstat(path) if regular_only else os.stat(path)).st_mode
    except (OSError, ValueError):
        return "%s: missing: %s" % (what, path)
    if not stat.S_ISREG(mode):
        return "%s: not a regular file: %s" % (what, path)
    got = sha_file(path)
    if got != want:
        return "%s: %s holds %s, not the recorded %s" % (what, path, got, want)
    return None


def component_map(listed):
    """{path: sha256} of a list of distinct {path, sha256} entries, or None when it is not one."""
    if not isinstance(listed, list):
        return None
    out = {}
    for entry in listed:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"] \
                or not isinstance(entry.get("sha256"), str) or not HEX64.match(entry["sha256"]) or entry["path"] in out:
            return None
        out[entry["path"]] = entry["sha256"]
    return out


def clean_env(*prefixes):
    return {name: value for name, value in os.environ.items() if not name.startswith(prefixes)}


# ---- E2
def check_source_repo(repo):
    try:
        said = subprocess.run(["git", "-C", repo, "rev-parse", "--is-inside-work-tree", "--show-toplevel"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=dict(clean_env("GIT_"), GIT_OPTIONAL_LOCKS="0"), timeout=60, stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return ["git could not be asked about KY_SOURCE_REPO %s (%s)" % (repo, type(e).__name__)]
    answer = said.stdout.split("\n")
    if answer[0] != "true":                     # a bare repository answers false; no repository answers nothing
        return ["KY_SOURCE_REPO is not a git work tree: %s" % repo]
    if said.returncode != 0 or len(answer) != 3 or os.path.realpath(answer[1]) != os.path.realpath(repo):
        return ["KY_SOURCE_REPO is not the top of its git work tree: %s" % repo]
    return []


# ---- B1 / F1
def check_receipt_mode(receipt, receipt_state, want):
    if receipt is None:
        return [receipt_state]
    if not isinstance(receipt.get("mode"), str) or receipt["mode"] != want:
        return ["the receipt's mode is %r; this mode needs %r" % (receipt.get("mode"), want)]
    return []


# ---- B2
def check_kymanifest(fleet, manifest_path, repo, run, own):
    """The reviewed sibling judges the bootstrap manifest against disk and git (kyboot.py `run_manifest_check`
    form: cwd /, no GIT_* and no PYTHON* variable handed on)."""
    tool = os.path.join(fleet, "kymanifest.py")
    try:
        done = subprocess.run([sys.executable, "-I", "-B", tool, "check", manifest_path, "--repo", repo, "--run", run],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=clean_env("GIT_", "PYTHON"), timeout=CHILD_TIMEOUT, stdin=subprocess.DEVNULL, cwd="/")
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return ["%s check could not be run (%s)" % (tool, type(e).__name__)]
    if done.returncode != 0:
        return ["%s check exited %d: %s" % (tool, done.returncode, (done.stderr.strip().splitlines() or ["no reason given"])[-1])]
    try:
        said = json.loads(done.stdout)
    except (ValueError, RecursionError):
        said = None
    if not isinstance(said, dict) or said.get("ok") is not True:
        return ["%s check exited 0 without ok: true" % tool]
    if own is None:
        return ["the manifest file states no manifest_sha256: %s" % manifest_path]
    if said.get("manifest_sha256") != own:
        return ["%s check answered for manifest %r; the manifest file states %s" % (tool, said.get("manifest_sha256"), own)]
    return []


# ---- F2
def check_final_manifest(manifest, manifest_state):
    if manifest is None:
        return [manifest_state]
    found = []
    if not isinstance(manifest.get("mode"), str) or manifest["mode"] != "final":
        found.append("the manifest's mode is %r, not 'final'" % (manifest.get("mode"),))
    entrypoints = manifest.get("entrypoints")
    if not isinstance(entrypoints, dict) or sorted(entrypoints) != sorted(ENTRYPOINT_ROLES):
        found.append("the manifest's entrypoints are not exactly the five roles %s" % ", ".join(ENTRYPOINT_ROLES))
    else:
        for role in ENTRYPOINT_ROLES:
            entry = entrypoints[role]
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"]:
                found.append("the manifest's entrypoint %s names no path" % role)
    stated = manifest.get("manifest_sha256")
    try:
        actual = hashlib.sha256(canonical({k: v for k, v in manifest.items() if k != "manifest_sha256"})).hexdigest()
    except (ValueError, TypeError, RecursionError):
        actual = None
    if actual is None or stated != actual:
        found.append("the manifest's manifest_sha256 (%r) is not the sha256 of its content (%s)" % (stated, actual))
    return found


# ---- B3 / F3
def check_binding(receipt, receipt_state, own, manifest_state):
    if receipt is None:
        return [receipt_state]
    if own is None:
        return [manifest_state]
    bound = receipt.get("manifest")
    bound = bound.get("manifest_sha256") if isinstance(bound, dict) else None
    if not isinstance(bound, str) or bound != own:
        return ["the receipt binds manifest %r; the manifest is %s" % (bound, own)]
    return []


# ---- B4 / F4
def check_installed(receipt, receipt_state, components, manifest_state):
    if receipt is None:
        return [receipt_state]
    if components is None:
        return [manifest_state]
    listed = receipt.get("components")
    if not isinstance(listed, list) or not listed:
        return ["the receipt lists no installed component"]
    found = []
    for entry in listed:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            found.append("a receipt component is not a {path, installed_path, sha256} entry")
        elif not isinstance(entry.get("sha256"), str) or components.get(entry["path"]) != entry["sha256"]:
            found.append("not a manifest component (path and sha256): %s" % entry["path"])
        else:
            problem = file_problem("installed " + entry["path"], entry.get("installed_path"), entry["sha256"])
            if problem:
                found.append(problem)
    return found


# ---- B5 / F5 (KU-03)
def check_pairs(manifest, manifest_state, repo):
    if manifest is None:
        return [manifest_state]
    pairs = manifest.get("generated_pairs")
    if not isinstance(pairs, list):
        return ["the manifest records no generated_pairs list"]
    found, seen = [], []
    for pair in pairs:
        if not isinstance(pair, dict) or not isinstance(pair.get("role"), str):
            found.append("a generated_pairs entry names no role")
            continue
        role = pair["role"]
        if role in seen:
            found.append("%s is recorded twice" % role)
        seen.append(role)
        def copy_path(label):
            # Keep the existing absolute representation readable for final/older manifests.
            if label + "_abs" in pair:
                return pair[label + "_abs"]
            rel = pair.get(label)
            if not isinstance(rel, str) or not rel or os.path.isabs(rel) or ".." in rel.split("/"):
                return None
            path = os.path.join(repo, rel)
            return path if os.path.commonpath((os.path.realpath(repo), os.path.realpath(path))) == os.path.realpath(repo) else None
        canon, compat = copy_path("canonical"), copy_path("compatibility")
        for label, path in (("canonical", canon), ("compatibility", compat)):
            problem = file_problem("%s %s copy" % (role, label), path, pair.get("sha256"), regular_only=True)
            if problem:
                found.append(problem)
        if isinstance(canon, str) and isinstance(compat, str) and os.path.normpath(canon) == os.path.normpath(compat):
            found.append("%s: the canonical and the compatibility copy are one path" % role)
    for role in PAIR_ROLES:
        if role not in seen:
            found.append("%s: no canonical / compatibility pair recorded" % role)
    return found


# ---- B7 / F8: the installer owns generated loop qualification receipts.
def check_loop_qualifications(receipt, receipt_state):
    if receipt is None:
        return []  # B1/F1 already refuses a missing/unreadable installer receipt.
    rows = receipt.get("qualifications")
    if not isinstance(rows, list):
        return ["the installer records no qualifications list"]
    found = []
    for role in LOOP_ROLES:
        own = [row for row in rows if isinstance(row, dict) and row.get("role") == role]
        if len(own) != 1:
            found.append("the installer must record exactly one %s qualification" % role)
            continue
        row = own[0]
        problem = file_problem(role + " qualification", row.get("receipt"), row.get("receipt_sha256"))
        if problem:
            found.append(problem)
            continue
        doc, err = read_json(row["receipt"])
        if err or not isinstance(doc, dict) or doc.get("result") != "PASS" or row.get("result") != "PASS":
            found.append("the installer-recorded %s qualification is not PASS" % role)
        elif doc.get("role") != role or not isinstance(row.get("model"), str) or not row["model"] or doc.get("model") != row["model"]:
            found.append("the installer-recorded %s qualification has the wrong role/model" % role)
    return found


# ---- B6 / F6
def activation_chain(run):
    """kyloop.py `Controller.activation_chain`, rule for rule: → ([link, …], None), with no link when there is
    no record at all, or (None, reason). $KY_RUN/ACTIVATION_RECORD.json, when present, is link 0; the numbered
    links follow, contiguous from 1; the first link has previous = null, every later one names its predecessor
    by file and sha256 and continues its commit and manifest digest. Anything else matching
    ACTIVATION_RECORD*.json is a fork."""
    try:
        names = sorted(n for n in os.listdir(run) if n.startswith("ACTIVATION_RECORD") and n.endswith(".json"))
    except OSError as e:
        return None, "activation_chain_unreadable: %s cannot be listed (%s)" % (run, type(e).__name__)
    numbered, root = {}, None
    for name in names:
        m = ACTIVATION_NAME.match(name)
        if not m:
            return None, "activation_chain_forked: unexpected file %s beside the activation chain" % name
        if m.group(1) is None:
            root = name
        else:
            numbered[int(m.group(1))] = name

    def agreed(doc, keys, pattern):
        values = [doc[k] for k in keys if k in doc]
        ok = values and all(isinstance(v, str) and pattern.match(v) and v == values[0] for v in values)
        return values[0] if ok else None

    links = []
    if root is not None:
        doc, err = read_json(os.path.join(run, root))
        if err or not isinstance(doc, dict):
            return None, "activation_record_invalid: %s is unreadable" % root
        digest = agreed(doc, ("new_manifest_digest", "final_manifest_digest"), SHA_RE)
        if digest is None:
            return None, "activation_record_invalid: %s needs final_manifest_digest (sha256 hex)" % root
        links.append({"n": 0, "file": root, "sha256": sha_file(os.path.join(run, root)),
                      "commit": agreed(doc, ("new_commit", "source_commit"), HEX_COMMIT), "manifest_digest": digest})
    for n in range(1, len(numbered) + 1):
        name, before = numbered.get(n), links[-1] if links else None
        if name is None:
            return None, "activation_chain_broken: ACTIVATION_RECORD.%d.json is missing from the sequence" % n
        doc, err = read_json(os.path.join(run, name))
        if err or not isinstance(doc, dict) or type(doc.get("n")) is not int or doc["n"] != n:
            return None, "activation_chain_broken: %s is unreadable or misnumbered" % name
        if any(not isinstance(doc.get(k), str) or not HEX_COMMIT.match(doc[k]) for k in ("old_commit", "new_commit")) \
                or any(not isinstance(doc.get(k), str) or not SHA_RE.match(doc[k])
                       for k in ("old_manifest_digest", "new_manifest_digest")):
            return None, "activation_chain_broken: %s lacks old/new source commits or manifest digests" % name
        if before is None:
            if doc.get("previous") is not None:
                return None, "activation_chain_broken: %s names a predecessor that is not there" % name
        elif doc.get("previous") is None:
            return None, "activation_chain_forked: %s names no predecessor although %s exists" % (name, before["file"])
        elif before["sha256"] is None or doc["previous"] != {"file": before["file"], "sha256": before["sha256"]}:
            return None, "activation_chain_broken: %s does not name its predecessor %s by sha256" % (name, before["file"])
        elif doc["old_commit"] != before["commit"] or doc["old_manifest_digest"] != before["manifest_digest"]:
            return None, "activation_chain_broken: %s does not continue %s" % (name, before["file"])
        links.append({"n": n, "file": name, "sha256": sha_file(os.path.join(run, name)), "commit": doc["new_commit"],
                      "manifest_digest": doc["new_manifest_digest"]})
    return links, None


# ---- F7
def check_evidence(receipt, receipt_state, components, manifest_state):
    if receipt is None:
        return [receipt_state]
    found = []
    rehearsal = receipt.get("rehearsal") if isinstance(receipt.get("rehearsal"), dict) else {}
    tested = component_map(rehearsal.get("tested_components"))
    if components is None:
        found.append(manifest_state)
    elif tested is None:
        found.append("rehearsal.tested_components is not a list of distinct {path, sha256} entries")
    elif tested != components:
        stale = sorted(p for p in set(tested) | set(components) if tested.get(p) != components.get(p))
        found.append("the rehearsal did not test the manifest's components: %s" % ", ".join(stale))
    packets = receipt.get("packets")
    named = [("rehearsal.results", rehearsal.get("results")), ("coverage", receipt.get("coverage")),
             ("backfill", receipt.get("backfill"))]
    if not isinstance(packets, list) or not packets:
        found.append("the receipt lists no packet")
    else:
        named += [("packets[%d]" % i, entry) for i, entry in enumerate(packets)]
    for what, entry in named:
        if not isinstance(entry, dict):
            found.append("%s: no {path, sha256} recorded" % what)
            continue
        problem = file_problem(what, entry.get("path"), entry.get("sha256"))
        if problem:
            found.append(problem)
        if what == "coverage" and not (isinstance(entry.get("verdict"), str) and entry["verdict"] == "ACCEPTED"):
            found.append("coverage.verdict is %r, not 'ACCEPTED'" % (entry.get("verdict"),))
        if what == "backfill" and entry.get("validated") is not True:
            found.append("backfill.validated is %r, not true" % (entry.get("validated"),))
    revision = receipt.get("tracker_revision")
    if not (isinstance(revision, str) and revision.strip()) and (type(revision) is not int):
        found.append("the receipt records no tracker_revision")
    return found


def run_checks(mode, expected, run, fleet, repo):
    """[(code, [problem, …])] for every check of the mode, in order; a check with no problem passed. → that
    list and the manifest's stated digest."""
    prefix = "B" if mode == "bootstrap" else "F"
    receipt_path = os.path.join(run, "INSTALL_RECEIPT.json")
    manifest_path = os.path.join(run, "VERSIONS.bootstrap.json" if mode == "bootstrap" else "VERSIONS.json")
    receipt, err = read_json(receipt_path)
    if err is None and not isinstance(receipt, dict):
        receipt, err = None, "not a JSON object"
    receipt_state = "the installation receipt is %s: %s" % (err, receipt_path)
    manifest, err = read_json(manifest_path)
    if err is None and not isinstance(manifest, dict):
        manifest, err = None, "not a JSON object"
    manifest_state = "the manifest is %s: %s" % (err, manifest_path)
    own = manifest.get("manifest_sha256") if manifest is not None else None
    if not isinstance(own, str) or not HEX64.match(own):
        own = None
    if manifest is not None and own is None:
        manifest_state = "the manifest states no manifest_sha256: %s" % manifest_path
    components = component_map(manifest.get("components")) if manifest is not None else None
    components_state = manifest_state if manifest is None else \
        "the manifest's components are not a list of distinct {path, sha256} entries: %s" % manifest_path

    results = [("E2", check_source_repo(repo)),
               (prefix + "1", check_receipt_mode(receipt, receipt_state, "bootstrap" if mode == "bootstrap" else "final"))]
    if mode == "bootstrap":
        results.append(("B2", check_kymanifest(fleet, manifest_path, repo, run, own)))
    else:
        results.append(("F2", check_final_manifest(manifest, manifest_state)))
    results.append((prefix + "3", check_binding(receipt, receipt_state, own, manifest_state)))
    results.append((prefix + "4", check_installed(receipt, receipt_state, components, components_state)))
    results.append((prefix + "5", check_pairs(manifest, manifest_state, repo)))
    links, reason = activation_chain(run)
    results.append((prefix + "6", [reason] if links is None else []))
    if mode != "bootstrap":
        results.append(("F7", check_evidence(receipt, receipt_state, components, components_state)))
    results.append(("B7" if mode == "bootstrap" else "F8", check_loop_qualifications(receipt, receipt_state)))
    if mode == "expected":
        results.append(("D1", [] if own is not None and own == expected else
                        ["the manifest's digest is %s, not the expected %s" % (own, expected)]))
        if links is None:
            terminal = ["the activation chain is not valid, so its terminal link is unknown"]
        elif not links:
            terminal = ["no activation record: %s" % os.path.join(run, "ACTIVATION_RECORD.json")]
        elif links[-1]["manifest_digest"] != expected:
            terminal = ["the terminal link %s carries manifest digest %s, not the expected %s"
                        % (links[-1]["file"], links[-1]["manifest_digest"], expected)]
        else:
            terminal = []
        results.append(("D2", terminal))
    return results, own


def main(argv):
    mode, expected, run, fleet, repo = argv
    if mode not in ("bootstrap", "final", "expected") or (mode == "expected") != bool(HEX64.match(expected)):
        raise ValueError("unknown mode")
    relative = [name for name, value in (("KY_RUN", run), ("KY_FLEET", fleet), ("KY_SOURCE_REPO", repo))
                if not os.path.isabs(value)]
    if relative:
        sys.stderr.write("kyversion: REFUSED E1: not an absolute path: %s (nothing was checked)\n" % ", ".join(relative))
        return 1
    results, own = run_checks(mode, expected, run, fleet, repo)
    refused = [(code, found) for code, found in results if found]
    for code, found in refused:
        more = " (and %d more)" % (len(found) - 1) if len(found) > 1 else ""
        sys.stderr.write("kyversion: REFUSED %s: %s%s\n" % (code, flat(found[0]) or "refused", more))
    if refused or own is None:
        return 1
    sys.stdout.write("kyversion: OK mode=%s manifest_sha256=%s authorises=%s\n" % (
        ("bootstrap", own, "bootstrap-only") if mode == "bootstrap" else
        ("final", own, "final-bundle tracker_revision=recorded")))
    sys.stdout.flush()
    return 0


try:
    status = main(sys.argv[2:])
except Exception as failed:                     # a check program that failed has verified nothing
    sys.stderr.write("kyversion: REFUSED E0: the check program failed (%s)\n" % type(failed).__name__)
    status = 1
sys.exit(status)
KYVERSION_PY
