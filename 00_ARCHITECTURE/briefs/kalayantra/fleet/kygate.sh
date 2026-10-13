#!/bin/bash
# kygate.sh — the KĀLA-YANTRA v3 release gate (relaunch plan v2.7 §10; packet KV3-B-KYGATE).
#
#   kygate.sh                the full gate: OPEN only with the release receipt, final Wave B acceptance (or the
#                            owner waiver below), no global HOLD and a matching N-467 resume record
#   kygate.sh --pre-resume   the same without the resume record: READY_TO_START only when that record is the sole
#                            thing missing
#   anything else: usage, exit 64, nothing on stdout.
#
# It reads, compares and prints. It writes nothing, calls no network, database or tracker, and authorises nothing:
# the callers act on its exit code (kyloop.py `verify_launch`: `/bin/bash kygate.sh`, 0 = open).
#
# Exit 0 = OPEN (full) or READY_TO_START (--pre-resume); 75 = WAIT: something is missing, inconsistent or unknown.
# stdout, always in this order:
#   line 1                    OPEN | READY_TO_START | WAIT
#   release_id=               the receipt's, when it is a well-formed id; else empty
#   release_receipt_digest=   the receipt's digest, only when check R2 reproduced it; else empty
#   final_manifest_digest=    the final manifest's digest, only when check A2 found all three copies equal; else empty
#   hold_merges=present|absent
#   unobserved=<fields>       the evidence fields the receipt's digest binds and this gate does not re-observe
#   reason=<code>: <detail>   one per failed check; any reason line means WAIT
#   note=<code>: <detail>     --pre-resume only: what is wrong with a resume record that does not satisfy N (it is
#                             reported and does not block)
#   final_acceptance=waived_by_owner  only with the valid OWNER_RESUME.waiver below
#   bootstrap_manifest_digest=       its recomputed digest, used for N instead of A2
#   waived=<code>: <detail>   A findings under that waiver; these alone never mean WAIT
#
# Env: KY_ROOT (default /Users/Dev/kalayantra), KY_RUN (default $KY_ROOT/run), KY_FLEET (default: this script's
# directory), KY_SOURCE_REPO (the git checkout; default as kyctl.sh). All four must be absolute.
# KY_GATE_KYVERSION_TIMEOUT_S, an integer 1..300, can only shorten the 300 s allowed to kyversion.sh; any other
# value is ignored.
#
# Checks (a check that cannot run is a failed check):
#   R1 `python3 -I -B $KY_FLEET/kyschema.py validate $KY_FLEET/schemas/release_receipt.json $KY_RUN/RELEASE_RECEIPT.json`
#      exits 0                                    receipt_schema_invalid (exit 1) · receipt_schema_unverified
#   R2 `digest` == sha256 of the receipt's canonical JSON without `digest` (canonical as kymanifest.py `canonical`:
#      sorted keys, no whitespace, UTF-8)         receipt_digest_mismatch
#   R3 every condition carries the top-level release_id and is SATISFIED with each evidence field the plan names
#                                                 mixed_release_ids · condition_wait · condition_missing ·
#                                                 missing_evidence · traversal_not_exhausted
#   R4 `coordination_commit` and `main_commit` are commits in $KY_SOURCE_REPO; `main_commit` is contained in
#      refs/remotes/origin/main as that checkout has it (nothing is fetched); PR numbers are unique
#                                                 unknown_commit · main_commit_outside_origin_main ·
#                                                 origin_main_unknown · duplicate_pr · git_unanswered
#   A  final Wave B acceptance, from $KY_RUN/INSTALL_RECEIPT.json and $KY_RUN/VERSIONS.json:
#      A1 receipt `mode == "final"`               bootstrap_only_installation · install_receipt_missing|unreadable
#      A2 the manifest says `mode: "final"`; its recomputed digest == its `manifest_sha256` == the receipt's
#         `manifest.manifest_sha256`              changed_final_manifest · final_manifest_missing|unreadable|not_final
#      A3 `rehearsal.results` names a file that has its sha256            absent_rehearsal
#      A4 `rehearsal.tested_components` == the manifest's `components`, neither empty    stale_tested_hashes
#      A5 `coverage.verdict == "ACCEPTED"`, its file has its sha256, `packets[]` is non-empty and each packet file
#         has its sha256                          missing_coverage
#      A6 `backfill.validated == true`            backfill_unvalidated
#      A7 `/bin/bash $KY_FLEET/kyversion.sh` (--pre-resume), or the same with `--expected-manifest-digest
#         <the resume record's approved_bundle_digest>` (full), exits 0 within 300 s    final_acceptance_unverified
#   H  $KY_ROOT/HOLD is absent, looked for after everything else ran       global_hold · ky_root_unusable
#      $KY_RUN/HOLD_MERGES never closes this gate (it blocks queue submission): it is only printed.
#   N  $KY_RUN/OWNER_RESUME.json: `binding == "N-467"`; `release_receipt_digest` == R2's digest;
#      `approved_bundle_digest` == A2's digest; `decided_by {kind: "owner" | "surrogate_decision", id}`; `ts` in UTC
#                                                 resume_missing · resume_unreadable · resume_malformed ·
#                                                 resume_missing_field (one per field) · resume_binding ·
#                                                 stale_resume · resume_bundle_mismatch · resume_decided_by ·
#                                                 resume_ts_not_utc
#      Full gate: N must hold. --pre-resume: a record satisfying N is WAIT `already_resumed`; one that is there
#      and cannot be read is WAIT `resume_unreadable` (it might be the satisfying one).
#   Owner waiver: OWNER_RESUME.waiver = {final_acceptance: true, decided_by: {kind: "owner", id}, reason, ts}.
#      Its schema is inline below (there is no existing OWNER_RESUME schema); malformed waiver = resume_malformed,
#      also in --pre-resume. (I) INTERPRETATION: both the resume and waiver deciders must be owner; a surrogate
#      cannot delegate the waiver. A1-A6 are reported as waived; final-mode A7 is replaced with REQUIRED
#      kyversion.sh --bootstrap (bootstrap_acceptance_unverified). N approves the recomputed digest of
#      VERSIONS.bootstrap.json, which must say bootstrap and state that digest (bootstrap_manifest_invalid).
#      All other N/R/H rules, including already_resumed in --pre-resume, remain in force.
#   The records are read once; one that differs when the gate has finished is WAIT `inputs_changed`.
set -u

usage() {
  echo "usage: kygate.sh [--pre-resume]" >&2
  exit 64
}

MODE=full
case "$#" in
  0) ;;
  1) if [ "$1" = "--pre-resume" ]; then MODE=pre-resume; else usage; fi ;;
  *) usage ;;
esac

case "$0" in
  */*) HERE="$(cd "${0%/*}" && pwd)" ;;
  *)   HERE="$(pwd)" ;;
esac
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
KY_FLEET="${KY_FLEET:-$HERE}"
KY_SOURCE_REPO="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"

# Only when the program below could not report for itself: still WAIT, never a bare failure.
unknown() {
  local hm=absent
  if [ -e "$KY_RUN/HOLD_MERGES" ] || [ -L "$KY_RUN/HOLD_MERGES" ]; then hm=present; fi
  printf 'WAIT\nrelease_id=\nrelease_receipt_digest=\nfinal_manifest_digest=\nhold_merges=%s\n' "$hm"
  printf 'reason=gate_internal_error: %s\n' "$1"
  exit 75
}

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then unknown "python3 not found on PATH"; fi

"$PY" -I -B - "$MODE" "$KY_ROOT" "$KY_RUN" "$KY_FLEET" "$KY_SOURCE_REPO" <<'PYEOF'
import datetime
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys

EXIT_WAIT = 75
HEX64 = re.compile(r"[0-9a-f]{64}")
HEX40 = re.compile(r"[0-9a-f]{40}")
RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
TS_UTC = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d{1,6})?(Z|\+00:00)")
BINDING = "N-467"
DECIDERS = ("owner", "surrogate_decision")
# Only this optional field is schema-validated: the existing N checks and legacy outputs stay unchanged.
WAIVER_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["final_acceptance", "decided_by", "reason", "ts"],
    "properties": {
        "final_acceptance": {"type": "boolean"},
        "decided_by": {
            "type": "object", "additionalProperties": False, "required": ["kind", "id"],
            "properties": {"kind": {"enum": list(DECIDERS)},
                           "id": {"type": "string", "pattern": "\\S"}},
        },
        "reason": {"type": "string", "pattern": "\\S"},
        "ts": {"type": "string", "pattern": "^" + TS_UTC.pattern + "$"},
    },
}
KYVERSION_TIMEOUT_S = 300
TOOL_TIMEOUT_S = 60
# condition → the evidence fields plan §10 names for it
EVIDENCE = (
    ("certification", ("coordination_commit", "record_id")),
    ("pins", ("rebuild_producer", "rebuild_run")),
    ("regeneration", ("main_commit", "generator_version", "output_digest")),
    ("pr_dispositions", ("traversal_exhausted", "prs")),
    ("coordinator_closure", ("handoff_records",)),
)
OBSERVED = {("certification", "coordination_commit"), ("regeneration", "main_commit")}
UNOBSERVED = ",".join("%s.%s" % (name, field) for name, names in EVIDENCE for field in names
                      if (name, field) not in OBSERVED)


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    """as kymanifest.py `canonical`"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest_without(doc, key):
    """sha256 of the canonical JSON of `doc` without `key`; None when it cannot be computed"""
    try:
        return sha256_hex(canonical({k: v for k, v in doc.items() if k != key}))
    except (ValueError, TypeError, RecursionError):
        return None


def is_hex64(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def show(value):
    """an untrusted value, on one line"""
    try:
        text = json.dumps(value, ensure_ascii=True)
    except (ValueError, TypeError, RecursionError):
        text = "<unprintable>"
    return text if len(text) <= 120 else text[:117] + "..."


def one_line(text):
    text = "".join(ch if ch.isprintable() else "?" for ch in str(text))
    return text if len(text) <= 400 else text[:397] + "..."


def load_strict(data):
    """strict JSON as kyschema.py reads it: duplicate keys, NaN and Infinity are refused"""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate key %r" % key)
            out[key] = value
        return out

    def constant(name):
        raise ValueError("%s is not JSON" % name)

    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def read_bytes(path):
    """("absent", None) | ("unreadable", None) | ("ok", bytes)"""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return "absent", None
    except OSError:
        return "unreadable", None
    try:
        with open(path, "rb") as f:
            return "ok", f.read()
    except OSError:
        return "unreadable", None


def fingerprint(path):
    state, data = read_bytes(path)
    return sha256_hex(data) if state == "ok" else state


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def child_env(extra=None):
    """no GIT_* redirection and no PYTHON* variable reaches a child (as kyboot.py `run_manifest_check`)"""
    env = {name: value for name, value in os.environ.items() if not name.startswith(("GIT_", "PYTHON"))}
    env.update(extra or {})
    return env


def bound_file(entry, what):
    """None when `entry` {path, sha256} names an existing regular file with that sha256; else what is wrong"""
    if not isinstance(entry, dict):
        return "%s is absent" % what
    path, recorded = entry.get("path"), entry.get("sha256")
    if not isinstance(path, str) or not os.path.isabs(path):
        return "%s names no absolute path (%s)" % (what, show(path))
    if not is_hex64(recorded):
        return "%s carries no sha256 (%s)" % (what, show(recorded))
    if not os.path.isfile(path):
        return "%s names a file that is not there: %s" % (what, path)
    try:
        actual = file_sha256(path)
    except OSError as failed:
        return "%s cannot be read: %s (%s)" % (what, path, type(failed).__name__)
    if actual != recorded:
        return "%s is recorded as %s and the file %s hashes to %s" % (what, recorded, path, actual)
    return None


def component_map(entries, what):
    """({path: sha256}, None) for a non-empty list of distinct {path, sha256}; else (None, what is wrong)"""
    if not isinstance(entries, list):
        return None, "%s is not a list" % what
    if not entries:
        return None, "%s is empty" % what
    out = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not is_hex64(entry.get("sha256")):
            return None, "%s holds an entry without path and sha256 (%s)" % (what, show(entry))
        if entry["path"] in out:
            return None, "%s names %s twice" % (what, show(entry["path"]))
        out[entry["path"]] = entry["sha256"]
    return out, None


class Gate:
    def __init__(self, mode, root, run, fleet, repo):
        self.mode, self.root, self.run, self.fleet, self.repo = mode, root, run, fleet, repo
        self.reasons, self.notes = [], []
        self.waived = []
        self.owner_waiver = False
        self.resume_record = None
        self.bootstrap_digest = None
        self.read = {}                       # path → fingerprint when this gate read it
        self.release_id = None
        self.receipt_digest = None           # set by R2 only
        self.manifest_digest = None          # A2, or the recomputed bootstrap digest under the owner waiver
        self.git_state = None                # None = not asked yet, True = answering, False = not answering

    def fail(self, code, detail):
        self.reasons.append((code, detail))

    def record(self, name):
        """(state, document): absent | unreadable | malformed | ok; the bytes judged are the bytes fingerprinted"""
        path = os.path.join(self.run, name)
        state, data = read_bytes(path)
        self.read[path] = sha256_hex(data) if state == "ok" else state
        if state != "ok":
            return state, None, path
        try:
            doc = load_strict(data)
        except (ValueError, RecursionError):
            return "malformed", None, path
        if not isinstance(doc, dict):
            return "malformed", None, path
        return "ok", doc, path

    # ── R: the release receipt ──────────────────────────────────────────────────────────────────────────────
    def check_release(self):
        state, doc, path = self.record("RELEASE_RECEIPT.json")
        if state == "absent":
            self.fail("release_receipt_missing", path)
            return
        if state != "ok":
            self.fail("release_receipt_unreadable", "%s is not a readable JSON object" % path)
        self.check_schema(path)
        if doc is None:
            return
        release_id = doc.get("release_id")
        if isinstance(release_id, str) and RELEASE_ID.fullmatch(release_id):
            self.release_id = release_id
        stated, computed = doc.get("digest"), digest_without(doc, "digest")
        if is_hex64(stated) and computed is not None and stated == computed:
            self.receipt_digest = stated
        else:
            self.fail("receipt_digest_mismatch", "the receipt states %s; its canonical content without `digest` "
                      "hashes to %s" % (show(stated), computed or "nothing computable"))
        conditions = doc.get("conditions")
        for name, names in EVIDENCE:
            condition = conditions.get(name) if isinstance(conditions, dict) else None
            if not isinstance(condition, dict):
                self.fail("condition_missing", "%s is not in the receipt" % name)
                continue
            if self.release_id is None or condition.get("release_id") != self.release_id:
                self.fail("mixed_release_ids", "%s carries release_id %s, the receipt %s"
                          % (name, show(condition.get("release_id")), show(release_id)))
            if condition.get("status") != "SATISFIED":
                self.fail("condition_wait", "%s is %s" % (name, show(condition.get("status"))))
                continue
            evidence = condition.get("evidence")
            evidence = evidence if isinstance(evidence, dict) else {}
            for field in names:
                if field not in evidence:
                    self.fail("missing_evidence", "%s.%s is absent from a SATISFIED condition" % (name, field))
            self.check_evidence(name, evidence)

    def check_schema(self, path):
        validator = os.path.join(self.fleet, "kyschema.py")
        schema = os.path.join(self.fleet, "schemas", "release_receipt.json")
        for needed in (validator, schema):
            if not os.path.isfile(needed):
                self.fail("receipt_schema_unverified", "not a file: %s" % needed)
                return
        try:
            done = subprocess.run([sys.executable, "-I", "-B", validator, "validate", schema, path],
                                  capture_output=True, text=True, env=child_env(), timeout=TOOL_TIMEOUT_S,
                                  stdin=subprocess.DEVNULL, cwd="/")
        except (OSError, subprocess.SubprocessError, ValueError) as failed:
            self.fail("receipt_schema_unverified", "kyschema.py could not be run (%s)" % type(failed).__name__)
            return
        if done.returncode == 1:
            findings = [line for line in done.stderr.splitlines()[1:] if line.strip()]
            self.fail("receipt_schema_invalid", "%s: %s" % (path, "; ".join(findings[:6]) or "refused"))
        elif done.returncode != 0:
            self.fail("receipt_schema_unverified", "kyschema.py validate ended rc=%d" % done.returncode)

    def check_evidence(self, name, evidence):
        if name == "certification" and "coordination_commit" in evidence:
            self.commit_known("certification.coordination_commit", evidence["coordination_commit"])
        elif name == "regeneration" and "main_commit" in evidence:
            commit = evidence["main_commit"]
            if self.commit_known("regeneration.main_commit", commit):
                self.contained_in_origin_main(commit)
        elif name == "pr_dispositions":
            if "traversal_exhausted" in evidence and evidence["traversal_exhausted"] is not True:
                self.fail("traversal_not_exhausted", "pr_dispositions.traversal_exhausted is %s"
                          % show(evidence["traversal_exhausted"]))
            prs = evidence.get("prs")
            if isinstance(prs, list):
                seen = {}
                for entry in prs:
                    number = entry.get("pr") if isinstance(entry, dict) else None
                    key = show(number)
                    seen[key] = seen.get(key, 0) + 1
                for key in sorted(k for k, n in seen.items() if n > 1):
                    self.fail("duplicate_pr", "PR %s has %d dispositions" % (key, seen[key]))
        elif name == "coordinator_closure" and "handoff_records" in evidence:
            records = evidence["handoff_records"]
            if not isinstance(records, list) or not records:
                self.fail("missing_evidence", "coordinator_closure.handoff_records is empty: no hand-off record "
                          "is enumerated")

    # ── R4: what git can be asked locally ───────────────────────────────────────────────────────────────────
    def git(self, *args):
        """CompletedProcess, or None when git did not answer"""
        env = child_env({"GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0"})
        try:
            return subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True, env=env,
                                  timeout=TOOL_TIMEOUT_S, stdin=subprocess.DEVNULL, cwd="/")
        except (OSError, subprocess.SubprocessError, ValueError):
            return None

    def git_answers(self):
        """True when $KY_SOURCE_REPO is itself a git work tree that answers; reported once when it does not"""
        if self.git_state is None:
            top = self.git("rev-parse", "--show-toplevel")
            if top is None:
                self.unanswered("git could not be run in %s" % self.repo)
            elif top.returncode != 0:
                self.unanswered("%s is no git work tree (rc=%d)" % (self.repo, top.returncode))
            elif os.path.realpath(top.stdout.rstrip("\n")) != os.path.realpath(self.repo):
                self.unanswered("%s is not the top of a git work tree" % self.repo)
            else:
                self.git_state = True
        return self.git_state

    def unanswered(self, detail):
        if self.git_state is not False:
            self.fail("git_unanswered", detail)
        self.git_state = False

    def commit_known(self, field, commit):
        if not isinstance(commit, str) or not HEX40.fullmatch(commit):
            self.fail("unknown_commit", "%s is no 40-hex commit id (%s)" % (field, show(commit)))
            return False
        if not self.git_answers():
            return False
        kind = self.git("cat-file", "-t", commit)
        if kind is None:
            self.unanswered("git cat-file did not answer for %s" % field)
            return False
        if kind.returncode != 0 or kind.stdout.strip() != "commit":
            what = "a %s" % one_line(kind.stdout.strip()) if kind.returncode == 0 else "not an object"
            self.fail("unknown_commit", "%s %s is %s in %s" % (field, commit, what, self.repo))
            return False
        return True

    def contained_in_origin_main(self, commit):
        ref = "refs/remotes/origin/main"
        tip = self.git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
        if tip is None:
            self.unanswered("git rev-parse did not answer for %s" % ref)
        elif tip.returncode != 0 or not HEX40.fullmatch(tip.stdout.strip()):
            self.fail("origin_main_unknown", "%s has no %s to compare regeneration.main_commit with" % (self.repo, ref))
        else:
            inside = self.git("merge-base", "--is-ancestor", commit, tip.stdout.strip())
            if inside is None or inside.returncode not in (0, 1):
                self.unanswered("git merge-base --is-ancestor did not answer (%s)"
                                % ("not run" if inside is None else "rc=%d" % inside.returncode))
            elif inside.returncode == 1:
                self.fail("main_commit_outside_origin_main", "regeneration.main_commit %s is not contained in %s (%s)"
                          % (commit, ref, tip.stdout.strip()))

    # ── A: final Wave B acceptance ──────────────────────────────────────────────────────────────────────────
    def check_waiver(self):
        state, doc, path = self.resume_record
        if state != "ok" or "waiver" not in doc:
            return
        waiver = doc["waiver"]
        try:
            spec = importlib.util.spec_from_file_location("kygate_schema", os.path.join(self.fleet, "kyschema.py"))
            validator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validator)
            wrong = validator.validate(WAIVER_SCHEMA, waiver)
            if not wrong:
                match = TS_UTC.fullmatch(waiver["ts"])
                datetime.datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
        except (OSError, ValueError, TypeError, AttributeError, RecursionError) as failed:
            wrong = ["waiver validation failed (%s)" % type(failed).__name__]
        if wrong:
            self.fail("resume_malformed", "%s waiver: %s" % (path, "; ".join(wrong)))
            return
        decided = doc.get("decided_by")
        self.owner_waiver = (waiver["final_acceptance"] is True and waiver["decided_by"]["kind"] == "owner"
                             and isinstance(decided, dict) and decided.get("kind") == "owner")

    def check_bootstrap(self):
        state, manifest, path = self.record("VERSIONS.bootstrap.json")
        self.manifest_digest = None
        stated = manifest.get("manifest_sha256") if manifest is not None else None
        computed = digest_without(manifest, "manifest_sha256") if manifest is not None else None
        if (state == "ok" and manifest.get("mode") == "bootstrap" and is_hex64(stated)
                and stated == computed):
            self.manifest_digest = self.bootstrap_digest = computed
        else:
            self.fail("bootstrap_manifest_invalid", "%s is %s, mode %s, hashes to %s and states %s"
                      % (path, state, show(manifest.get("mode") if manifest is not None else None),
                         computed or "nothing computable", show(stated)))

    def check_acceptance(self):
        receipt_state, receipt, receipt_path = self.record("INSTALL_RECEIPT.json")
        manifest_state, manifest, manifest_path = self.record("VERSIONS.json")
        if receipt_state == "absent":
            self.fail("install_receipt_missing", receipt_path)
        elif receipt_state != "ok":
            self.fail("install_receipt_unreadable", "%s is not a readable JSON object" % receipt_path)
        if manifest_state == "absent":
            self.fail("final_manifest_missing", manifest_path)
        elif manifest_state != "ok":
            self.fail("final_manifest_unreadable", "%s is not a readable JSON object" % manifest_path)
        elif manifest.get("mode") != "final":
            self.fail("final_manifest_not_final", "%s says mode %s" % (manifest_path, show(manifest.get("mode"))))
        if receipt is None:
            return
        if receipt.get("mode") != "final":                                                              # A1
            self.fail("bootstrap_only_installation", "%s says mode %s, not \"final\""
                      % (receipt_path, show(receipt.get("mode"))))
        if manifest is not None:                                                                         # A2
            stated, computed = manifest.get("manifest_sha256"), digest_without(manifest, "manifest_sha256")
            bound = receipt.get("manifest")
            bound = bound.get("manifest_sha256") if isinstance(bound, dict) else None
            if is_hex64(stated) and computed is not None and stated == computed == bound:
                self.manifest_digest = stated
            else:
                self.fail("changed_final_manifest", "%s hashes to %s, states %s, and the installation receipt binds %s"
                          % (manifest_path, computed or "nothing computable", show(stated), show(bound)))
        rehearsal = receipt.get("rehearsal")
        rehearsal = rehearsal if isinstance(rehearsal, dict) else {}
        wrong = bound_file(rehearsal.get("results"), "rehearsal.results")                               # A3
        if wrong:
            self.fail("absent_rehearsal", wrong)
        tested, wrong = component_map(rehearsal.get("tested_components"), "rehearsal.tested_components")  # A4
        if wrong is None and manifest is None:
            wrong = "there is no final manifest to compare rehearsal.tested_components with"
        if wrong is None:
            components, wrong = component_map(manifest.get("components"), "the final manifest's components")
        if wrong is None and tested != components:
            differing = sorted(p for p in set(tested) | set(components) if tested.get(p) != components.get(p))
            wrong = "rehearsal.tested_components differs from the final manifest's components at %s" % show(differing)
        if wrong:
            self.fail("stale_tested_hashes", wrong)
        coverage, wrongs = receipt.get("coverage"), []                                                  # A5
        if not isinstance(coverage, dict) or coverage.get("verdict") != "ACCEPTED":
            wrongs.append("coverage.verdict is %s, not \"ACCEPTED\""
                          % show(coverage.get("verdict") if isinstance(coverage, dict) else None))
        wrong = bound_file(coverage, "coverage")
        if wrong:
            wrongs.append(wrong)
        packets = receipt.get("packets")
        if not isinstance(packets, list) or not packets:
            wrongs.append("packets[] names no admitted packet")
        else:
            wrongs.extend(w for w in (bound_file(p, "packets[%d]" % i) for i, p in enumerate(packets)) if w)
        if wrongs:
            self.fail("missing_coverage", "; ".join(wrongs))
        backfill = receipt.get("backfill")                                                              # A6
        validated = backfill.get("validated") if isinstance(backfill, dict) else None
        if validated is not True:
            self.fail("backfill_unvalidated", "backfill.validated is %s, not true" % show(validated))

    def check_kyversion(self, args, failure_code="final_acceptance_unverified"):                         # A7
        """`args` None = there is nothing this mode may hand kyversion.sh, so it is not run"""
        script = os.path.join(self.fleet, "kyversion.sh")
        if args is None:
            self.fail(failure_code, "the resume record gives no approved_bundle_digest to hand "
                      "kyversion.sh --expected-manifest-digest; it was not run")
            return
        if not os.path.isfile(script):
            self.fail(failure_code, "kyversion.sh is missing: %s" % script)
            return
        limit = KYVERSION_TIMEOUT_S
        override = os.environ.get("KY_GATE_KYVERSION_TIMEOUT_S", "")
        if re.fullmatch(r"[0-9]{1,3}", override) and 1 <= int(override) <= KYVERSION_TIMEOUT_S:
            limit = int(override)
        env = child_env({"KY_ROOT": self.root, "KY_RUN": self.run, "KY_FLEET": self.fleet,
                         "KY_SOURCE_REPO": self.repo})
        try:
            child = subprocess.Popen(["/bin/bash", script, *args], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd="/",
                                     start_new_session=True)
        except (OSError, ValueError) as failed:
            self.fail(failure_code, "kyversion.sh could not be run (%s)" % type(failed).__name__)
            return
        try:
            rc = child.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            try:                                  # the session this gate itself started, nothing else
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            child.wait()
            self.fail(failure_code, "kyversion.sh %s timed out after %d s" % (" ".join(args), limit))
            return
        if rc != 0:
            self.fail(failure_code, "kyversion.sh %s ended rc=%d" % (" ".join(args), rc))

    # ── N: the N-467 resume record ──────────────────────────────────────────────────────────────────────────
    def resume_problems(self, doc, path):
        """what keeps a readable record from satisfying N; [] = it satisfies"""
        out = []

        def missing(field):
            out.append(("resume_missing_field", "%s is absent from %s" % (field, path)))

        if "binding" not in doc:
            missing("binding")
        elif doc["binding"] != BINDING:
            out.append(("resume_binding", "binding is %s, not \"%s\"" % (show(doc["binding"]), BINDING)))
        if "release_receipt_digest" not in doc:
            missing("release_receipt_digest")
        elif self.receipt_digest is None or doc["release_receipt_digest"] != self.receipt_digest:
            out.append(("stale_resume", "the record binds release receipt digest %s; the receipt's is %s"
                        % (show(doc["release_receipt_digest"]), self.receipt_digest or "unknown")))
        if "approved_bundle_digest" not in doc:
            missing("approved_bundle_digest")
        elif self.manifest_digest is None or doc["approved_bundle_digest"] != self.manifest_digest:
            out.append(("resume_bundle_mismatch", "the record approves bundle %s; the %s manifest's digest is %s"
                        % (show(doc["approved_bundle_digest"]), "bootstrap" if self.owner_waiver else "final",
                           self.manifest_digest or "unknown")))
        if "decided_by" not in doc:
            missing("decided_by")
        elif not isinstance(doc["decided_by"], dict):
            out.append(("resume_decided_by", "decided_by is %s, not {kind, id}" % show(doc["decided_by"])))
        else:
            decided = doc["decided_by"]
            if "kind" not in decided:
                missing("decided_by.kind")
            elif not isinstance(decided["kind"], str) or decided["kind"] not in DECIDERS:
                out.append(("resume_decided_by", "decided_by.kind is %s, not one of %s"
                            % (show(decided["kind"]), " | ".join(DECIDERS))))
            if "id" not in decided:
                missing("decided_by.id")
            elif not isinstance(decided["id"], str) or not decided["id"].strip():
                out.append(("resume_decided_by", "decided_by.id is %s, not an identity" % show(decided["id"])))
        if "ts" not in doc:
            missing("ts")
        else:
            match = TS_UTC.fullmatch(doc["ts"]) if isinstance(doc["ts"], str) else None
            try:
                if match:
                    datetime.datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                match = None
            if not match:
                out.append(("resume_ts_not_utc", "ts is %s, not a UTC timestamp (…Z or …+00:00)" % show(doc["ts"])))
        return out

    def check_resume(self):
        """the arguments kyversion.sh takes in this mode, or None when the full gate has no digest to hand it"""
        state, doc, path = self.resume_record
        pre = self.mode == "pre-resume"
        if state == "unreadable":
            self.fail("resume_unreadable", "%s is there and cannot be read%s"
                      % (path, ": it may be the satisfying record" if pre else ""))
        elif state == "absent":
            if not pre:
                self.fail("resume_missing", path)
        elif state == "malformed":
            (self.notes if pre else self.reasons).append(("resume_malformed", "%s is not a JSON object" % path))
        else:
            problems = self.resume_problems(doc, path)
            if pre and not problems:
                self.fail("already_resumed", "%s already satisfies the %s resume: nothing is left for a start to add"
                          % (path, BINDING))
            (self.notes if pre else self.reasons).extend(problems)
        if pre:
            return []
        approved = doc.get("approved_bundle_digest") if doc is not None else None
        return ["--expected-manifest-digest", approved] if is_hex64(approved) else None

    # ── H, and the answer ───────────────────────────────────────────────────────────────────────────────────
    def check_holds(self):
        if not os.path.isdir(self.root):
            self.fail("ky_root_unusable", "%s is no directory: an absent HOLD there proves nothing" % self.root)
        elif os.path.lexists(os.path.join(self.root, "HOLD")):
            self.fail("global_hold", "%s is present" % os.path.join(self.root, "HOLD"))
        if not os.path.isdir(self.run):
            self.fail("ky_run_unusable", "%s is no directory" % self.run)
        return "present" if os.path.lexists(os.path.join(self.run, "HOLD_MERGES")) else "absent"

    def decide(self):
        self.check_release()
        self.resume_record = self.record("OWNER_RESUME.json")
        self.check_waiver()
        before = len(self.reasons)
        self.check_acceptance()
        final_digest = self.manifest_digest
        if self.owner_waiver:
            self.waived.extend(self.reasons[before:])
            del self.reasons[before:]
            self.check_bootstrap()
            self.check_resume()
            self.waived.append(("final_acceptance_unverified", "final-mode kyversion.sh replaced by kyversion.sh --bootstrap"))
            self.check_kyversion(["--bootstrap"], "bootstrap_acceptance_unverified")
        else:
            self.check_kyversion(self.check_resume())
        for path in sorted(self.read):
            if fingerprint(path) != self.read[path]:
                self.fail("inputs_changed", "%s changed while the gate ran: %s" % (os.path.basename(path), path))
        hold_merges = self.check_holds()                      # last: a HOLD placed while the gate ran still closes it
        word = "WAIT" if self.reasons else ("READY_TO_START" if self.mode == "pre-resume" else "OPEN")
        lines = [word, "release_id=%s" % (self.release_id or ""),
                 "release_receipt_digest=%s" % (self.receipt_digest or ""),
                 "final_manifest_digest=%s" % (final_digest or ""),
                 "hold_merges=%s" % hold_merges, "unobserved=%s" % UNOBSERVED]
        lines += ["reason=%s: %s" % (code, one_line(detail)) for code, detail in self.reasons]
        lines += ["note=%s: %s" % (code, one_line(detail)) for code, detail in self.notes]
        if self.owner_waiver:
            lines += ["final_acceptance=waived_by_owner", "bootstrap_manifest_digest=%s" % (self.bootstrap_digest or "")]
            lines += ["waived=%s: %s" % (code, one_line(detail)) for code, detail in self.waived]
        return lines, (EXIT_WAIT if self.reasons else 0)


def emit(lines, code):
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.flush()
    return code


def main(argv):
    mode, paths = argv[0], argv[1:5]
    names = ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SOURCE_REPO")
    relative = [name for name, path in zip(names, paths) if not os.path.isabs(path)]
    if mode not in ("full", "pre-resume") or len(paths) != 4 or relative:
        hold_merges = "present" if len(paths) > 1 and os.path.lexists(os.path.join(paths[1], "HOLD_MERGES")) \
            else "absent"
        return emit(["WAIT", "release_id=", "release_receipt_digest=", "final_manifest_digest=",
                     "hold_merges=%s" % hold_merges, "unobserved=%s" % UNOBSERVED,
                     "reason=env_not_absolute: %s must be absolute paths; nothing was checked"
                     % (", ".join(relative) or "the gate's arguments")], EXIT_WAIT)
    return emit(*Gate(mode, *paths).decide())


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as failed:                    # a gate that cannot finish has decided nothing: the caller
        sys.stderr.write("kygate: %s: %s\n" % (type(failed).__name__, one_line(failed)))      # prints WAIT
        sys.exit(70)
PYEOF
rc=$?
case "$rc" in
  0|75) exit "$rc" ;;
  *) unknown "the gate program ended rc=$rc before it decided" ;;
esac
