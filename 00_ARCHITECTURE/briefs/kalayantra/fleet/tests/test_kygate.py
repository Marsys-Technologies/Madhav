"""kygate.sh (relaunch plan v2.7 §10; packet KV3-B-KYGATE): the release gate and its --pre-resume mode.

Every test builds its own KY_ROOT, KY_RUN, KY_FLEET (the real kygate.sh, kyschema.py and release-receipt schema
copied in; kyversion.sh a recording double) and git repository, then runs the gate the way kyloop.py does:
`/bin/bash <fleet>/kygate.sh [--pre-resume]`. One fully satisfied world gives READY_TO_START and OPEN; every
negative case changes one thing in it and must end WAIT, exit 75, with exactly its reason codes."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
FIXTURES = HERE / "fixtures" / "b0c"
GATE = FLEET / "kygate.sh"

MODES = ("full", "pre-resume")
CONDITIONS = ("certification", "pins", "regeneration", "pr_dispositions", "coordinator_closure")
EVIDENCE_FIELDS = [
    ("certification", "coordination_commit"), ("certification", "record_id"),
    ("pins", "rebuild_producer"), ("pins", "rebuild_run"),
    ("regeneration", "main_commit"), ("regeneration", "generator_version"), ("regeneration", "output_digest"),
    ("pr_dispositions", "traversal_exhausted"), ("pr_dispositions", "prs"),
    ("coordinator_closure", "handoff_records"),
]
UNOBSERVED = ("certification.record_id,pins.rebuild_producer,pins.rebuild_run,regeneration.generator_version,"
              "regeneration.output_digest,pr_dispositions.traversal_exhausted,pr_dispositions.prs,"
              "coordinator_closure.handoff_records")

# The recording double of kyversion.sh: one line per call in <script>.calls; exit code from <script>.rc;
# <script>.hang makes it sleep (its pid in <script>.pid); <script>.append names a file it appends a byte to.
KYVERSION_DOUBLE = """#!/bin/bash
printf 'argc=%s argv=%s\\n' "$#" "$*" >> "$0.calls"
printf '%s %s %s %s\\n' "${KY_ROOT:-}" "${KY_RUN:-}" "${KY_FLEET:-}" "${KY_SOURCE_REPO:-}" > "$0.env"
if [ -f "$0.append" ]; then printf ' ' >> "$(cat "$0.append")"; fi
if [ -f "$0.create" ]; then : > "$(cat "$0.create")"; fi
if [ -f "$0.hang" ]; then echo "$$" > "$0.pid"; sleep 60 & echo "$!" > "$0.childpid"; wait; fi
if [ -f "$0.rc" ]; then exit "$(cat "$0.rc")"; fi
exit 0
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    """as kymanifest.py `canonical`"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest_without(doc, key):
    return sha(canonical({k: v for k, v in doc.items() if k != key}))


def git_env():
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git_in(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, env=git_env())
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture(scope="session")
def template(tmp_path_factory):
    """main one ← main two = origin/main ← unmerged (HEAD): two commits contained in origin/main, one outside."""
    repo = tmp_path_factory.mktemp("kygate-template")
    out = {"repo": repo}
    git_in(repo, "init", "-q")
    for name in ("main_commit", "coordination_commit", "side_commit"):
        git_in(repo, "commit", "-q", "--allow-empty", "-m", name)
        out[name] = git_in(repo, "rev-parse", "HEAD")
        if name == "coordination_commit":
            git_in(repo, "update-ref", "refs/remotes/origin/main", out[name])
    out["tree"] = git_in(repo, "rev-parse", out["main_commit"] + "^{tree}")
    return out


class World:
    """A fully satisfied installation; tests change one thing and write it back."""

    def __init__(self, tmp, template):
        self.tmp = tmp
        self.root = tmp / "kalayantra"
        self.run = self.root / "run"
        self.fleet = tmp / "fleet_live"
        self.repo = tmp / "source"
        self.evidence = tmp / "evidence"
        for d in (self.run, self.fleet / "schemas", self.evidence):
            d.mkdir(parents=True)
        if GATE.exists():
            shutil.copy(GATE, self.fleet / "kygate.sh")
        shutil.copy(FLEET / "kyschema.py", self.fleet / "kyschema.py")
        shutil.copy(FLEET / "schemas" / "release_receipt.json", self.fleet / "schemas" / "release_receipt.json")
        self.kyversion = self.fleet / "kyversion.sh"
        self.kyversion.write_text(KYVERSION_DOUBLE)
        self.env_extra = {"KY_GATE_KYVERSION_TIMEOUT_S": "300"}

        # the source repository: built once per session, copied per test (each test owns and may change its copy)
        shutil.copytree(template["repo"], self.repo, dirs_exist_ok=True)
        self.main_commit, self.coordination_commit = template["main_commit"], template["coordination_commit"]
        self.side_commit, self.tree = template["side_commit"], template["tree"]

        self.manifest = {"schema": "ky.manifest/1", "mode": "final", "entrypoints": {},
                         "components": [{"path": "fleet/kygate.sh", "sha256": "a" * 64},
                                        {"path": "fleet/kyversion.sh", "sha256": "b" * 64}],
                         "generated_pairs": []}
        self.install = {
            "mode": "final", "manifest": {"manifest_sha256": None},
            "components": [], "tracker_revision": "tracker-r1",
            "rehearsal": {"tested_components": copy.deepcopy(self.manifest["components"]),
                          "results": self.bound("rehearsal.json", b"measured\n")},
            "coverage": dict(self.bound("coverage.md", b"coverage\n"), verdict="ACCEPTED"),
            "packets": [self.bound("PACKET_A.md", b"packet a\n"), self.bound("PACKET_B.md", b"packet b\n")],
            "backfill": dict(self.bound("backfill.json", b"backfill\n"), validated=True),
        }
        self.receipt = json.loads((FIXTURES / "release_receipt_satisfied.json").read_text())
        self.receipt["conditions"]["certification"]["evidence"]["coordination_commit"] = self.coordination_commit
        self.receipt["conditions"]["regeneration"]["evidence"]["main_commit"] = self.main_commit
        self.resume = None
        self.resume_overrides = {}
        self.with_resume = True
        self.write()

    def git(self, *args):
        return git_in(self.repo, *args)

    def bound(self, name, data):
        path = self.evidence / name
        path.write_bytes(data)
        return {"path": str(path), "sha256": sha(data)}

    def write(self, receipt_digest=True, manifest_digest=True, bind_manifest=True):
        """Write the four records consistently; the keyword switches leave one binding as the test set it."""
        if manifest_digest:
            self.manifest["manifest_sha256"] = digest_without(self.manifest, "manifest_sha256")
        if bind_manifest and isinstance(self.install.get("manifest"), dict):
            self.install["manifest"]["manifest_sha256"] = self.manifest.get("manifest_sha256")
        if receipt_digest:
            self.receipt["digest"] = digest_without(self.receipt, "digest")
        (self.run / "VERSIONS.json").write_text(json.dumps(self.manifest))
        (self.run / "INSTALL_RECEIPT.json").write_text(json.dumps(self.install))
        (self.run / "RELEASE_RECEIPT.json").write_text(json.dumps(self.receipt))
        self.resume = {"binding": "N-467", "release_receipt_digest": self.receipt.get("digest"),
                       "approved_bundle_digest": self.manifest.get("manifest_sha256"),
                       "decided_by": {"kind": "owner", "id": "abhisek"}, "ts": "2026-10-12T09:30:00Z"}
        self.resume.update(self.resume_overrides)
        path = self.run / "OWNER_RESUME.json"
        if self.with_resume:
            path.write_text(json.dumps(self.resume))
        elif path.exists():
            path.unlink()

    def gate(self, mode="full", args=None, env=None):
        """mode full: with the satisfying record the test left; pre-resume: without one, unless the test wrote it."""
        if args is None:
            args = [] if mode == "full" else ["--pre-resume"]
        full = dict(os.environ, KY_ROOT=str(self.root), KY_RUN=str(self.run), KY_FLEET=str(self.fleet),
                    KY_SOURCE_REPO=str(self.repo), **self.env_extra)
        full.update(env or {})
        return subprocess.run(["/bin/bash", str(self.fleet / "kygate.sh"), *args], capture_output=True, text=True,
                              env=full, timeout=120, stdin=subprocess.DEVNULL)

    def run_mode(self, mode):
        """Run `mode` on its own baseline: the full gate has a satisfying record, --pre-resume has none."""
        self.with_resume = (mode == "full")
        self.write_resume_only()
        return self.gate(mode)

    def write_resume_only(self):
        path = self.run / "OWNER_RESUME.json"
        if self.with_resume:
            path.write_text(json.dumps(self.resume))
        elif path.exists():
            path.unlink()

    def calls(self):
        path = Path(str(self.kyversion) + ".calls")
        return path.read_text().splitlines() if path.exists() else []

    def snapshot(self):
        out = {}
        for base in (self.root, self.fleet, self.evidence):
            for p in sorted(base.rglob("*")):
                if p.name.startswith("kyversion.sh."):
                    continue
                out[str(p)] = sha(p.read_bytes()) if p.is_file() else "dir"
        return out


@pytest.fixture
def w(tmp_path, template):
    return World(tmp_path, template)


def fields(r):
    out = {}
    for line in r.stdout.splitlines()[1:]:
        key, _, value = line.partition("=")
        out.setdefault(key, []).append(value)
    return out


def codes(r):
    return sorted(v.split(":", 1)[0] for v in fields(r).get("reason", []))


def reason(r, code):
    return [v for v in fields(r).get("reason", []) if v.split(":", 1)[0] == code]


def assert_wait(r, *expected):
    """WAIT, exit 75, and exactly these reason codes: the changed thing is reported and nothing else is."""
    assert r.stdout.splitlines()[:1] == ["WAIT"], r.stdout + r.stderr
    assert r.returncode == 75, r.stdout + r.stderr
    assert codes(r) == sorted(expected), r.stdout + r.stderr
    for v in fields(r)["reason"]:
        code, sep, detail = v.partition(": ")
        assert sep and detail, v


def assert_status(r, word):
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.splitlines()[0] == word
    assert "reason" not in fields(r)


# ───────────────────────────── the script itself ─────────────────────────────

def test_script_is_an_executable_bash_script():
    assert GATE.is_file() and os.access(GATE, os.X_OK)
    assert GATE.read_text().splitlines()[0] == "#!/bin/bash"
    mode = subprocess.run(["git", "-C", str(FLEET), "ls-files", "-s", "--", "kygate.sh"], capture_output=True,
                          text=True, env=git_env())
    assert mode.returncode == 0 and mode.stdout.startswith("100755 "), mode.stdout + mode.stderr


@pytest.mark.parametrize("args", [["--full"], ["--pre-resume", "x"], ["x"], ["--pre-resume", "--pre-resume"], [""],
                                  ["--help"]])
def test_any_other_usage_is_64_and_says_nothing_on_stdout(w, args):
    r = w.gate(args=args)
    assert r.returncode == 64 and r.stdout == "" and "usage" in r.stderr
    assert w.calls() == []


# ───────────────────────────── positive ─────────────────────────────

def test_pre_resume_prints_ready_to_start_without_a_resume_record(w):
    r = w.run_mode("pre-resume")
    assert_status(r, "READY_TO_START")
    f = fields(r)
    assert f["release_id"] == ["REL-20261011-01"]
    assert f["release_receipt_digest"] == [w.receipt["digest"]]
    assert f["final_manifest_digest"] == [w.manifest["manifest_sha256"]]
    assert f["hold_merges"] == ["absent"]
    assert f["unobserved"] == [UNOBSERVED]
    assert r.stdout.splitlines()[1:5] == ["release_id=REL-20261011-01",
                                          "release_receipt_digest=" + w.receipt["digest"],
                                          "final_manifest_digest=" + w.manifest["manifest_sha256"],
                                          "hold_merges=absent"]
    assert w.calls() == ["argc=0 argv="]                                    # the double's argv, pre-resume


def test_full_gate_prints_open_with_a_satisfying_record(w):
    r = w.run_mode("full")
    assert_status(r, "OPEN")
    f = fields(r)
    assert f["release_receipt_digest"] == [w.receipt["digest"]]
    assert f["final_manifest_digest"] == [w.manifest["manifest_sha256"]]
    assert w.calls() == ["argc=2 argv=--expected-manifest-digest " + w.manifest["manifest_sha256"]]
    assert Path(str(w.kyversion) + ".env").read_text().split() == [str(w.root), str(w.run), str(w.fleet),
                                                                   str(w.repo)]


def test_pre_resume_with_a_satisfying_record_is_wait_already_resumed(w):
    r = w.gate("pre-resume")
    assert_wait(r, "already_resumed")
    assert w.calls() == ["argc=0 argv="]


@pytest.mark.parametrize("kind", ["owner", "surrogate_decision"])
def test_both_deciding_identities_satisfy(w, kind):
    w.resume_overrides = {"decided_by": {"kind": kind, "id": "D-7-0001"}}
    w.write()
    assert_status(w.gate("full"), "OPEN")


@pytest.mark.parametrize("ts", ["2026-10-12T09:30:00Z", "2026-10-12T09:30:00.123456Z", "2026-10-12T09:30:00+00:00"])
def test_utc_timestamps_satisfy(w, ts):
    w.resume_overrides = {"ts": ts}
    w.write()
    assert_status(w.gate("full"), "OPEN")


@pytest.mark.parametrize("mode,word", [("full", "OPEN"), ("pre-resume", "READY_TO_START")])
def test_hold_merges_changes_no_result_and_is_printed(w, mode, word):
    (w.run / "HOLD_MERGES").write_text("queue submissions blocked\n")
    r = w.run_mode(mode)
    assert_status(r, word)
    assert fields(r)["hold_merges"] == ["present"]


def test_hold_merges_is_printed_on_wait_too(w):
    (w.run / "HOLD_MERGES").write_text("")
    (w.root / "HOLD").write_text("")
    r = w.run_mode("full")
    assert_wait(r, "global_hold")
    assert fields(r)["hold_merges"] == ["present"]


@pytest.mark.parametrize("mode", MODES)
def test_the_gate_writes_nothing(w, mode):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    before = w.snapshot()
    refs = w.git("for-each-ref")
    assert w.gate(mode).returncode == 0
    assert w.snapshot() == before and w.git("for-each-ref") == refs
    assert w.git("status", "--porcelain") == ""


def test_defaults_ky_run_under_ky_root_and_ky_fleet_beside_the_script(w):
    w.with_resume = False
    w.write_resume_only()
    env = {k: v for k, v in os.environ.items() if k not in ("KY_RUN", "KY_FLEET")}
    env.update(KY_ROOT=str(w.root), KY_SOURCE_REPO=str(w.repo))
    r = subprocess.run(["/bin/bash", str(w.fleet / "kygate.sh"), "--pre-resume"], capture_output=True, text=True,
                       env=env, timeout=120)
    assert_status(r, "READY_TO_START")
    assert Path(str(w.kyversion) + ".env").read_text().split()[1:3] == [str(w.run), str(w.fleet)]


# ───────────────────────────── H: the global HOLD ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["file", "empty", "directory", "dangling-symlink"])
def test_a_surviving_global_hold_is_wait(w, mode, how):
    hold = w.root / "HOLD"
    if how == "file":
        hold.write_text("held by the owner\n")
    elif how == "empty":
        hold.write_text("")
    elif how == "directory":
        hold.mkdir()
    else:
        hold.symlink_to(w.tmp / "nowhere")
    assert_wait(w.run_mode(mode), "global_hold")


def test_a_hold_that_appears_while_the_gate_runs_is_wait(w):
    Path(str(w.kyversion) + ".create").write_text(str(w.root / "HOLD"))
    assert_wait(w.run_mode("full"), "global_hold")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("which,code", [("KY_ROOT", "ky_root_unusable"), ("KY_RUN", "ky_run_unusable")])
def test_a_root_that_is_no_directory_proves_no_absent_hold(w, mode, which, code):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    r = w.gate(mode, env={which: str(w.tmp / "absent")})
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert code in codes(r)


@pytest.mark.parametrize("which", ["KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SOURCE_REPO"])
def test_a_relative_path_in_the_environment_is_wait(w, which):
    r = w.gate("full", env={which: "relative/path"})
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert "env_not_absolute" in codes(r) and w.calls() == []


# ───────────────────────────── R1, R2: schema and digest ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
def test_missing_release_receipt_is_wait(w, mode):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    (w.run / "RELEASE_RECEIPT.json").unlink()
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert "release_receipt_missing" in codes(r)
    assert fields(r)["release_id"] == [""] and fields(r)["release_receipt_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("text", ["{torn", "[]", '"a string"', '{"release_id": "A", "release_id": "B"}', "NaN"])
def test_unreadable_release_receipt_is_wait(w, mode, text):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    (w.run / "RELEASE_RECEIPT.json").write_text(text)
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert "release_receipt_unreadable" in codes(r) and "receipt_schema_invalid" in codes(r)
    assert fields(r)["release_receipt_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("change", ["extra-top-key", "schema-version", "bad-status", "extra-evidence-key",
                                    "pr-without-owner", "parked-without-re-entry"])
def test_a_schema_invalid_receipt_is_wait(w, mode, change):
    c = w.receipt["conditions"]
    if change == "extra-top-key":
        w.receipt["note"] = "x"
    elif change == "schema-version":
        w.receipt["schema_version"] = "ky.release_receipt/2"
    elif change == "bad-status":
        c["pins"]["status"] = "satisfied"
    elif change == "extra-evidence-key":
        c["pins"]["evidence"]["extra"] = "x"
    elif change == "pr-without-owner":
        del c["pr_dispositions"]["evidence"]["prs"][0]["owner"]
    else:
        c["pr_dispositions"]["evidence"]["prs"][1]["re_entry"] = None
    w.write()                                                       # the digest is right: only the shape is wrong
    r = w.run_mode(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert "receipt_schema_invalid" in codes(r) and "receipt_digest_mismatch" not in codes(r)
    if change != "bad-status":
        assert codes(r) == ["receipt_schema_invalid"]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("missing", ["kyschema.py", "schemas/release_receipt.json"])
def test_no_schema_status_without_the_validator_having_run(w, mode, missing):
    (w.fleet / missing).unlink()
    assert_wait(w.run_mode(mode), "receipt_schema_unverified")


@pytest.mark.parametrize("mode", MODES)
def test_a_validator_that_cannot_validate_is_not_a_pass(w, mode):
    (w.fleet / "schemas" / "release_receipt.json").write_text("{torn")      # kyschema.py exits 2
    assert_wait(w.run_mode(mode), "receipt_schema_unverified")


@pytest.mark.parametrize("mode", MODES)
def test_a_wrong_receipt_digest_is_wait(w, mode):
    w.receipt["digest"] = "3" * 64
    w.write(receipt_digest=False)                    # the resume record binds that same stated digest
    r = w.run_mode(mode)
    assert_wait(r, *(("receipt_digest_mismatch", "stale_resume") if mode == "full" else ("receipt_digest_mismatch",)))
    assert fields(r)["release_receipt_digest"] == [""]              # unknown: never the unverified claim


@pytest.mark.parametrize("mode", MODES)
def test_content_changed_after_the_digest_was_taken_is_wait(w, mode):
    w.receipt["conditions"]["pins"]["evidence"]["rebuild_run"] = "run-other"
    w.write(receipt_digest=False)
    r = w.run_mode(mode)
    assert "receipt_digest_mismatch" in codes(r) and r.returncode == 75


@pytest.mark.parametrize("mode", MODES)
def test_the_b0c_satisfied_fixture_carries_a_placeholder_digest_and_is_wait(w, mode):
    """Schema-valid, all five SATISFIED, and still no passed gate: its digest and commits are placeholders."""
    shutil.copy(FIXTURES / "release_receipt_satisfied.json", w.run / "RELEASE_RECEIPT.json")
    w.with_resume = False
    w.write_resume_only()
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert "receipt_digest_mismatch" in codes(r) and "receipt_schema_invalid" not in codes(r)
    assert codes(r).count("unknown_commit") == 2


def test_the_b0c_wait_fixture_is_wait(w):
    shutil.copy(FIXTURES / "release_receipt_wait.json", w.run / "RELEASE_RECEIPT.json")
    r = w.gate("pre-resume")
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT" and "condition_wait" in codes(r)


# ───────────────────────────── R3: one release, five satisfied conditions ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_mixed_release_ids_are_wait(w, mode, condition):
    w.receipt["conditions"][condition]["release_id"] = "REL-20261010-09"
    w.write()
    r = w.run_mode(mode)
    assert_wait(r, "mixed_release_ids")
    assert condition in reason(r, "mixed_release_ids")[0]


@pytest.mark.parametrize("mode", MODES)
def test_a_top_level_release_id_no_condition_shares_is_wait(w, mode):
    w.receipt["release_id"] = "REL-20261010-09"
    w.write()
    r = w.run_mode(mode)
    assert codes(r) == ["mixed_release_ids"] * 5 and r.returncode == 75


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_each_condition_at_wait_is_wait(w, mode, condition):
    """Condition 5 (coordinator_closure) included: it has no producer today and stays WAIT until one publishes."""
    w.receipt["conditions"][condition]["status"] = "WAIT"
    w.write()
    r = w.run_mode(mode)
    assert_wait(r, "condition_wait")
    assert condition in reason(r, "condition_wait")[0]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_wait_condition_with_empty_evidence_is_reported_once(w, mode, condition):
    w.receipt["conditions"][condition].update(status="WAIT", evidence={})
    w.write()
    assert_wait(w.run_mode(mode), "condition_wait")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition,field", EVIDENCE_FIELDS)
def test_each_missing_evidence_field_of_each_condition_is_wait(w, mode, condition, field):
    del w.receipt["conditions"][condition]["evidence"][field]
    w.write()
    r = w.run_mode(mode)
    assert_wait(r, "missing_evidence", "receipt_schema_invalid")
    assert reason(r, "missing_evidence")[0].startswith("missing_evidence: %s.%s " % (condition, field))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_missing_condition_is_wait(w, mode, condition):
    del w.receipt["conditions"][condition]
    w.write()
    r = w.run_mode(mode)
    assert r.returncode == 75 and "condition_missing" in codes(r) and "receipt_schema_invalid" in codes(r)


@pytest.mark.parametrize("mode", MODES)
def test_a_traversal_that_was_not_exhausted_is_wait(w, mode):
    w.receipt["conditions"]["pr_dispositions"]["evidence"]["traversal_exhausted"] = False
    w.write()
    assert_wait(w.run_mode(mode), "traversal_not_exhausted", "receipt_schema_invalid")


@pytest.mark.parametrize("mode", MODES)
def test_no_enumerated_handoff_record_is_wait(w, mode):
    w.receipt["conditions"]["coordinator_closure"]["evidence"]["handoff_records"] = []
    w.write()
    assert_wait(w.run_mode(mode), "missing_evidence", "receipt_schema_invalid")


# ───────────────────────────── R4: what the gate can observe locally ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("condition,field", [("certification", "coordination_commit"), ("regeneration", "main_commit")])
@pytest.mark.parametrize("what", ["absent", "tree"])
def test_an_unknown_commit_is_wait(w, mode, condition, field, what):
    w.receipt["conditions"][condition]["evidence"][field] = "1" * 40 if what == "absent" else w.tree
    w.write()
    r = w.run_mode(mode)
    assert_wait(r, "unknown_commit")
    assert "%s.%s" % (condition, field) in reason(r, "unknown_commit")[0]


@pytest.mark.parametrize("mode", MODES)
def test_main_commit_outside_origin_main_is_wait(w, mode):
    w.receipt["conditions"]["regeneration"]["evidence"]["main_commit"] = w.side_commit
    w.write()
    assert_wait(w.run_mode(mode), "main_commit_outside_origin_main")


def test_the_coordination_commit_need_not_be_on_origin_main(w):
    w.receipt["conditions"]["certification"]["evidence"]["coordination_commit"] = w.side_commit
    w.write()
    assert_status(w.run_mode("full"), "OPEN")


@pytest.mark.parametrize("mode", MODES)
def test_no_origin_main_to_compare_against_is_wait(w, mode):
    w.git("update-ref", "-d", "refs/remotes/origin/main")
    assert_wait(w.run_mode(mode), "origin_main_unknown")


def test_a_local_main_branch_is_not_origin_main(w):
    w.git("update-ref", "-d", "refs/remotes/origin/main")
    w.git("update-ref", "refs/heads/main", w.coordination_commit)
    w.git("update-ref", "refs/heads/origin/main", w.coordination_commit)
    assert_wait(w.run_mode("full"), "origin_main_unknown")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["not-a-repository", "absent"])
def test_git_not_answering_is_wait(w, mode, how):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    other = w.tmp / "plain"
    if how == "not-a-repository":
        other.mkdir()
    r = w.gate(mode, env={"KY_SOURCE_REPO": str(other)})
    assert_wait(r, "git_unanswered")


@pytest.mark.parametrize("mode", MODES)
def test_a_directory_inside_the_checkout_is_not_the_checkout(w, mode):
    """git would answer from the enclosing repository; the gate asks about $KY_SOURCE_REPO itself."""
    w.with_resume = (mode == "full")
    w.write_resume_only()
    inner = w.repo / "inner"
    inner.mkdir()
    assert_wait(w.gate(mode, env={"KY_SOURCE_REPO": str(inner)}), "git_unanswered")


@pytest.mark.parametrize("mode", MODES)
def test_no_git_program_is_wait(w, mode):
    """PATH holds python3 and nothing else: git cannot be started, so nothing about the commits is known."""
    w.with_resume = (mode == "full")
    w.write_resume_only()
    bindir = w.tmp / "bin"
    bindir.mkdir()
    python = shutil.which("python3")
    (bindir / "python3").symlink_to(python)
    probe = subprocess.run([str(bindir / "python3"), "-c", "print(1)"], capture_output=True, text=True)
    assert probe.stdout.strip() == "1"
    r = w.gate(mode, env={"PATH": str(bindir)})
    assert_wait(r, "git_unanswered")


def test_git_environment_redirection_does_not_reach_the_gate(w):
    """A GIT_DIR pointing at another repository must not answer for $KY_SOURCE_REPO."""
    other = w.tmp / "other"
    other.mkdir()
    subprocess.run(["git", "-C", str(other), "init", "-q"], check=True, env=git_env(), capture_output=True)
    r = w.gate("full", env={"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)})
    assert_status(r, "OPEN")


@pytest.mark.parametrize("mode", MODES)
def test_a_duplicate_pr_is_wait(w, mode):
    prs = w.receipt["conditions"]["pr_dispositions"]["evidence"]["prs"]
    prs.append(dict(prs[0], disposition="closed"))
    w.write()
    r = w.run_mode(mode)
    assert_wait(r, "duplicate_pr")
    assert "3379" in reason(r, "duplicate_pr")[0]


def test_no_pr_at_all_is_a_valid_exhausted_traversal(w):
    w.receipt["conditions"]["pr_dispositions"]["evidence"]["prs"] = []
    w.write()
    assert_status(w.run_mode("full"), "OPEN")


# ───────────────────────────── A: final Wave B acceptance ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("value", ["bootstrap", None, "FINAL", ["final"]])
def test_bootstrap_only_installation_is_wait(w, mode, value):
    if value is None:
        del w.install["mode"]
    else:
        w.install["mode"] = value
    w.write()
    assert_wait(w.run_mode(mode), "bootstrap_only_installation")


@pytest.mark.parametrize("mode", MODES)
def test_a_real_bootstrap_only_installation_is_wait(w, mode):
    """As B-2 leaves it: a bootstrap receipt, no final manifest, none of the final evidence."""
    w.install = {"mode": "bootstrap", "manifest": {"manifest_sha256": "c" * 64}, "components": []}
    w.write(bind_manifest=False)
    (w.run / "VERSIONS.json").unlink()
    w.resume_overrides = {"approved_bundle_digest": "c" * 64}
    w.write_resume_only()
    r = w.run_mode(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    for code in ("bootstrap_only_installation", "final_manifest_missing", "absent_rehearsal", "stale_tested_hashes",
                 "missing_coverage", "backfill_unvalidated"):
        assert code in codes(r)
    assert fields(r)["final_manifest_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["missing", "torn", "list"])
def test_no_readable_installation_receipt_is_wait(w, mode, how):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    path = w.run / "INSTALL_RECEIPT.json"
    if how == "missing":
        path.unlink()
    else:
        path.write_text("{torn" if how == "torn" else "[]")
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert ("install_receipt_missing" if how == "missing" else "install_receipt_unreadable") in codes(r)
    assert "OPEN" not in r.stdout and "READY_TO_START" not in r.stdout


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["component-changed", "component-added", "digest-restated", "receipt-binds-other",
                                 "receipt-binds-nothing"])
def test_changed_final_manifest_is_wait(w, mode, how):
    if how == "component-changed":
        w.manifest["components"][0]["sha256"] = "d" * 64
        w.write(manifest_digest=False)                       # the manifest no longer hashes to what it states
        expect = ("changed_final_manifest", "stale_tested_hashes")
    elif how == "component-added":
        w.manifest["entrypoints"] = {"conductor": "fleet/kyloop.py"}
        w.write(manifest_digest=False)
        expect = ("changed_final_manifest",)
    elif how == "digest-restated":
        w.manifest["entrypoints"] = {"conductor": "fleet/kyloop.py"}
        w.write(bind_manifest=False)                         # self-consistent again, but not the one installed
        w.install["manifest"]["manifest_sha256"] = "e" * 64
        w.write(bind_manifest=False)
        expect = ("changed_final_manifest",)
    elif how == "receipt-binds-other":
        w.install["manifest"]["manifest_sha256"] = "e" * 64
        w.write(bind_manifest=False)
        expect = ("changed_final_manifest",)
    else:
        del w.install["manifest"]
        w.write()
        expect = ("changed_final_manifest",)
    r = w.run_mode(mode)
    if mode == "full":
        expect += ("resume_bundle_mismatch",)                # no known final digest for the record to equal
    assert_wait(r, *expect)
    assert fields(r)["final_manifest_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["missing", "torn"])
def test_no_readable_final_manifest_is_wait(w, mode, how):
    w.with_resume = (mode == "full")
    w.write_resume_only()
    if how == "missing":
        (w.run / "VERSIONS.json").unlink()
    else:
        (w.run / "VERSIONS.json").write_text("{torn")
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert ("final_manifest_missing" if how == "missing" else "final_manifest_unreadable") in codes(r)
    assert fields(r)["final_manifest_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
def test_a_bootstrap_manifest_in_the_final_place_is_wait(w, mode):
    w.manifest["mode"] = "bootstrap"
    w.write()
    assert_wait(w.run_mode(mode), "final_manifest_not_final")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["no-rehearsal", "no-results", "file-absent", "file-changed", "no-sha256",
                                 "relative-path", "directory"])
def test_absent_rehearsal_is_wait(w, mode, how):
    results = w.install["rehearsal"]["results"]
    expect = ("absent_rehearsal",)
    if how == "no-rehearsal":
        del w.install["rehearsal"]
        expect = ("absent_rehearsal", "stale_tested_hashes")
    elif how == "no-results":
        del w.install["rehearsal"]["results"]
    elif how == "file-absent":
        Path(results["path"]).unlink()
    elif how == "file-changed":
        Path(results["path"]).write_bytes(b"measured differently\n")
    elif how == "no-sha256":
        del results["sha256"]
    elif how == "relative-path":
        results["path"] = "rehearsal.json"
    else:
        Path(results["path"]).unlink()
        Path(results["path"]).mkdir()
    w.write()
    assert_wait(w.run_mode(mode), *expect)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["one-hash-older", "one-missing", "one-extra", "none", "not-a-list", "duplicate-path",
                                 "both-empty"])
def test_stale_tested_hashes_are_wait(w, mode, how):
    tested = w.install["rehearsal"]["tested_components"]
    if how == "one-hash-older":
        tested[0]["sha256"] = "f" * 64
    elif how == "one-missing":
        tested.pop()
    elif how == "one-extra":
        tested.append({"path": "fleet/extra.py", "sha256": "c" * 64})
    elif how == "none":
        del w.install["rehearsal"]["tested_components"]
    elif how == "not-a-list":
        w.install["rehearsal"]["tested_components"] = {"fleet/kygate.sh": "a" * 64}
    elif how == "duplicate-path":
        tested.append(dict(tested[0]))
    else:
        w.install["rehearsal"]["tested_components"] = []
        w.manifest["components"] = []
    w.write()
    assert_wait(w.run_mode(mode), "stale_tested_hashes")


def test_tested_components_compare_as_a_set_of_path_and_hash(w):
    w.install["rehearsal"]["tested_components"].reverse()
    w.write()
    assert_status(w.run_mode("full"), "OPEN")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("how", ["no-coverage", "verdict-rejected", "verdict-absent", "file-absent", "file-changed",
                                 "no-packets", "empty-packets", "packet-file-changed", "packet-without-sha256"])
def test_missing_coverage_is_wait(w, mode, how):
    coverage = w.install["coverage"]
    if how == "no-coverage":
        del w.install["coverage"]
    elif how == "verdict-rejected":
        coverage["verdict"] = "REJECTED"
    elif how == "verdict-absent":
        del coverage["verdict"]
    elif how == "file-absent":
        Path(coverage["path"]).unlink()
    elif how == "file-changed":
        Path(coverage["path"]).write_bytes(b"other coverage\n")
    elif how == "no-packets":
        del w.install["packets"]
    elif how == "empty-packets":
        w.install["packets"] = []
    elif how == "packet-file-changed":
        Path(w.install["packets"][1]["path"]).write_bytes(b"packet b, edited after admission\n")
    else:
        del w.install["packets"][0]["sha256"]
    w.write()
    assert_wait(w.run_mode(mode), "missing_coverage")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("value", [False, None, "true", 1, "absent", "no-backfill"])
def test_an_unvalidated_backfill_is_wait(w, mode, value):
    if value == "no-backfill":
        del w.install["backfill"]
    elif value == "absent":
        del w.install["backfill"]["validated"]
    else:
        w.install["backfill"]["validated"] = value
    w.write()
    assert_wait(w.run_mode(mode), "backfill_unvalidated")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rc", ["1", "2", "64", "75", "127"])
def test_kyversion_non_zero_is_wait(w, mode, rc):
    Path(str(w.kyversion) + ".rc").write_text(rc)
    r = w.run_mode(mode)
    assert_wait(r, "final_acceptance_unverified")
    assert "rc=%s" % rc in reason(r, "final_acceptance_unverified")[0]
    assert len(w.calls()) == 1


@pytest.mark.parametrize("mode", MODES)
def test_kyversion_missing_is_wait(w, mode):
    w.kyversion.unlink()
    assert_wait(w.run_mode(mode), "final_acceptance_unverified")


@pytest.mark.parametrize("mode", MODES)
def test_kyversion_hanging_is_wait_and_is_not_left_running(w, mode):
    Path(str(w.kyversion) + ".hang").write_text("")
    w.env_extra = {"KY_GATE_KYVERSION_TIMEOUT_S": "2"}
    started = time.monotonic()
    r = w.run_mode(mode)
    assert time.monotonic() - started < 30
    assert_wait(r, "final_acceptance_unverified")
    assert "timed out" in reason(r, "final_acceptance_unverified")[0]
    for name in (".pid", ".childpid"):                      # processes this test's own double started
        pid = int(Path(str(w.kyversion) + name).read_text())
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            pytest.fail("the hanging kyversion.sh (pid %d) outlived the gate" % pid)


@pytest.mark.parametrize("value", ["0", "-1", "301", "100000", "fast", ""])
def test_the_timeout_override_can_only_shorten_and_a_bad_one_is_ignored(w, value):
    w.env_extra = {"KY_GATE_KYVERSION_TIMEOUT_S": value}
    assert_status(w.run_mode("full"), "OPEN")


@pytest.mark.parametrize("target,codes_expected", [
    ("RELEASE_RECEIPT.json", ("inputs_changed",)), ("INSTALL_RECEIPT.json", ("inputs_changed",)),
    ("VERSIONS.json", ("inputs_changed",)), ("OWNER_RESUME.json", ("inputs_changed",))])
def test_a_record_rewritten_while_the_gate_runs_is_wait(w, target, codes_expected):
    Path(str(w.kyversion) + ".append").write_text(str(w.run / target))
    r = w.run_mode("full")
    assert_wait(r, *codes_expected)
    assert target in reason(r, "inputs_changed")[0]


def test_a_resume_record_that_appears_during_pre_resume_is_wait(w):
    w.with_resume = False
    w.write_resume_only()
    Path(str(w.kyversion) + ".create").write_text(str(w.run / "OWNER_RESUME.json"))
    assert_wait(w.gate("pre-resume"), "inputs_changed")


# ───────────────────────────── N: the N-467 resume record ─────────────────────────────

def test_a_full_gate_without_record_is_wait(w):
    w.with_resume = False
    w.write_resume_only()
    r = w.gate("full")
    assert_wait(r, "resume_missing", "final_acceptance_unverified")
    assert w.calls() == []                         # no approved digest to hand kyversion.sh: it is not guessed


@pytest.mark.parametrize("text", ["{torn", "[]", "null", '{"binding": "N-467", "binding": "N-467"}'])
def test_a_malformed_record_closes_the_full_gate(w, text):
    (w.run / "OWNER_RESUME.json").write_text(text)
    r = w.gate("full")
    assert_wait(r, "resume_malformed", "final_acceptance_unverified")


@pytest.mark.parametrize("field,expect", [
    ("binding", ("resume_missing_field",)),
    ("release_receipt_digest", ("resume_missing_field",)),
    ("approved_bundle_digest", ("resume_missing_field", "final_acceptance_unverified")),
    ("decided_by", ("resume_missing_field",)),
    ("decided_by.kind", ("resume_missing_field",)),
    ("decided_by.id", ("resume_missing_field",)),
    ("ts", ("resume_missing_field",))])
def test_each_missing_resume_field_is_its_own_reason(w, field, expect):
    w.write()
    record = copy.deepcopy(w.resume)
    if "." in field:
        del record["decided_by"][field.split(".")[1]]
    else:
        del record[field]
    (w.run / "OWNER_RESUME.json").write_text(json.dumps(record))
    r = w.gate("full")
    assert_wait(r, *expect)
    assert reason(r, "resume_missing_field") == ["resume_missing_field: " + field + " is absent from "
                                                 + str(w.run / "OWNER_RESUME.json")]


def test_all_missing_fields_are_reported_one_reason_each(w):
    (w.run / "OWNER_RESUME.json").write_text("{}")
    r = w.gate("full")
    assert r.returncode == 75
    named = sorted(v.split(": ")[1].split(" ")[0] for v in reason(r, "resume_missing_field"))
    assert named == ["approved_bundle_digest", "binding", "decided_by", "release_receipt_digest", "ts"]


@pytest.mark.parametrize("field,value,code", [
    ("binding", "N-468", "resume_binding"),
    ("binding", None, "resume_binding"),
    ("release_receipt_digest", "9" * 64, "stale_resume"),
    ("release_receipt_digest", "short", "stale_resume"),
    ("release_receipt_digest", 7, "stale_resume"),
    ("approved_bundle_digest", "9" * 64, "resume_bundle_mismatch"),
    ("decided_by", "owner", "resume_decided_by"),
    ("decided_by", {"kind": "planner", "id": "x"}, "resume_decided_by"),
    ("decided_by", {"kind": "owner", "id": ""}, "resume_decided_by"),
    ("decided_by", {"kind": "owner", "id": 7}, "resume_decided_by"),
    ("ts", "2026-10-12T15:00:00+05:30", "resume_ts_not_utc"),
    ("ts", "2026-10-12T09:30:00", "resume_ts_not_utc"),
    ("ts", "2026-13-40T09:30:00Z", "resume_ts_not_utc"),
    ("ts", 1791800000, "resume_ts_not_utc"),
    ("ts", "yesterday", "resume_ts_not_utc")])
def test_each_wrong_resume_field_is_wait(w, field, value, code):
    w.resume_overrides = {field: value}
    w.write()
    assert_wait(w.gate("full"), code)


def test_stale_resume_binds_an_earlier_receipt(w):
    """The record was written for the receipt as it then was; the receipt has since been re-issued."""
    w.write()
    earlier = w.resume["release_receipt_digest"]
    w.receipt["conditions"]["pins"]["evidence"]["rebuild_run"] = "run-20261012T0100Z"
    w.resume_overrides = {"release_receipt_digest": earlier}
    w.write()
    assert w.receipt["digest"] != earlier
    r = w.gate("full")
    assert_wait(r, "stale_resume")
    assert fields(r)["release_receipt_digest"] == [w.receipt["digest"]]


def test_a_record_for_another_bundle_hands_kyversion_that_digest_and_still_waits(w):
    w.resume_overrides = {"approved_bundle_digest": "9" * 64}
    w.write()
    assert_wait(w.gate("full"), "resume_bundle_mismatch")
    assert w.calls() == ["argc=2 argv=--expected-manifest-digest " + "9" * 64]


@pytest.mark.parametrize("value", ["short", "--bootstrap", "9" * 63 + "G", ["9" * 64], None])
def test_a_malformed_approved_digest_is_never_passed_to_kyversion(w, value):
    w.resume_overrides = {"approved_bundle_digest": value}
    w.write()
    r = w.gate("full")
    assert_wait(r, "resume_bundle_mismatch", "final_acceptance_unverified")
    assert w.calls() == []


@pytest.mark.parametrize("overrides,code", [
    ({"release_receipt_digest": "9" * 64}, "stale_resume"),
    ({"approved_bundle_digest": "9" * 64}, "resume_bundle_mismatch"),
    ({"binding": "N-468"}, "resume_binding"),
    ({"ts": "yesterday"}, "resume_ts_not_utc"),
    ({"decided_by": {"kind": "planner", "id": "x"}}, "resume_decided_by")])
def test_pre_resume_reports_a_stale_record_and_is_not_blocked_by_it(w, overrides, code):
    w.resume_overrides = overrides
    w.write()
    r = w.gate("pre-resume")
    assert_status(r, "READY_TO_START")
    assert [v.split(":", 1)[0] for v in fields(r)["note"]] == [code]
    assert w.calls() == ["argc=0 argv="]


@pytest.mark.parametrize("text", ["{torn", "[]", "{}"])
def test_pre_resume_reports_a_malformed_record_and_is_not_blocked_by_it(w, text):
    (w.run / "OWNER_RESUME.json").write_text(text)
    r = w.gate("pre-resume")
    assert_status(r, "READY_TO_START")
    assert fields(r)["note"]


def test_pre_resume_cannot_call_a_record_it_cannot_read_stale(w):
    """A record that is there but cannot be read might be the satisfying one: unknown is WAIT."""
    (w.run / "OWNER_RESUME.json").unlink()
    (w.run / "OWNER_RESUME.json").mkdir()
    assert_wait(w.gate("pre-resume"), "resume_unreadable")
    assert_wait(w.gate("full"), "resume_unreadable", "final_acceptance_unverified")


# ───────────────────────────── never a status without its check ─────────────────────────────

@pytest.mark.parametrize("mode", MODES)
def test_an_empty_run_directory_is_wait(w, mode):
    for p in w.run.iterdir():
        p.unlink()
    r = w.gate(mode)
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    for code in ("release_receipt_missing", "install_receipt_missing", "final_manifest_missing"):
        assert code in codes(r)
    f = fields(r)
    assert f["release_id"] == [""] and f["release_receipt_digest"] == [""] and f["final_manifest_digest"] == [""]


@pytest.mark.parametrize("mode", MODES)
def test_no_python_is_wait_never_a_bare_failure(w, mode):
    empty = w.tmp / "nobin"
    empty.mkdir()
    r = w.gate(mode, env={"PATH": str(empty)})
    assert r.returncode == 75 and r.stdout.splitlines()[0] == "WAIT"
    assert codes(r) == ["gate_internal_error"]


@pytest.mark.parametrize("mode", MODES)
def test_untrusted_text_cannot_forge_an_output_line(w, mode):
    w.receipt["release_id"] = "REL\nOPEN"
    for name in CONDITIONS:
        w.receipt["conditions"][name]["release_id"] = "REL\nOPEN"
    w.receipt["conditions"]["pins"]["evidence"]["rebuild_run"] = "x\nreason=none\nOPEN"
    w.write()
    r = w.run_mode(mode)
    assert r.returncode == 75
    lines = r.stdout.splitlines()
    assert lines[0] == "WAIT" and "OPEN" not in lines and "READY_TO_START" not in lines
    assert fields(r)["release_id"] == [""]
    assert all(line.split("=", 1)[0] in ("release_id", "release_receipt_digest", "final_manifest_digest",
                                         "hold_merges", "unobserved", "reason", "note") for line in lines[1:])


def test_first_line_is_always_one_of_the_three_words(w):
    seen = set()
    for mode in MODES:
        for with_resume in (True, False):
            w.with_resume = with_resume
            w.write_resume_only()
            r = w.gate(mode)
            first = r.stdout.splitlines()[0]
            seen.add((mode, with_resume, first, r.returncode))
    assert seen == {("full", True, "OPEN", 0), ("full", False, "WAIT", 75),
                    ("pre-resume", True, "WAIT", 75), ("pre-resume", False, "READY_TO_START", 0)}
