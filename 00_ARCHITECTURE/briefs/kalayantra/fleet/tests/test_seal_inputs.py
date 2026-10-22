"""Oracles for seal_inputs.py (BEFORE SEAL M-W34-07; #3817; SR-XC-FREEZE-482012f1 / CCD-028) — one doctrine-grounded oracle per distinct production claim, fixtures only: no gh, no
gcloud, no database, no network, no run/ directory.  The only subprocesses are `git` on repositories the tests create, the checkout's own apply_generated_overlay.py and the sidecar's own
implementation_registry.compute() on a throw-away copy.

Sources: ci_generated.py (OUTPUTS: the lock is CI-GENERATED, SR-CHURN-CUT 3), .github/actions/apply-generated-overlay/action.yml (the lookup the seal runs), the seal workflow
(.github/workflows/gochara-seal-approved.yml: lock vs the job's own digest, exit 4), implementation_registry.py (the digest definition), CROSS_CUTTING_DECISION_REGISTER CCD-028.

DG-1 a commit whose push-main ci.yml run is green and whose ci-generated artifact is unexpired passes the dispatch gate                                         (#3817)
DG-2 only a PUSH to MAIN counts, and only its NEWEST run, completed and successful                                                                                 (#3817)
DG-3 no artifact / an expired artifact / a green run without the artifact => HOLD                                                                                 (action.yml `!a.expired`)
DG-4 an artifact too close to expiry for the seal, or with an unreadable expiry => HOLD (the latter an honest null)                                                (N.8, N.7.6)
DG-5 evidence for another commit proves nothing about this one                                                                                                   (head_sha binding)
DG-6 unreadable / absent evidence is a null, never a pass                                                                                                          (N.7.6)
SI-1 fresh CI artifact of the commit whose lock equals the seal job's own digests, on a clean checkout of the commit on main => FRESH
SI-2 a lock that differs from the seal job's own digests (the digest, or one stage) => HOLD, naming the seal's own refusal                                          (seal workflow exit 4)
SI-3 the COMMITTED lock is never the comparand: stale on main by design, the artifact's lock decides                                                              (SR-CHURN-CUT 3; the M-W34-07 defect)
SI-4 an artifact downloaded from any run but the one the seal overlay would pick => HOLD
SI-5 the checkout's own overlay tool decides the artifact: a changed byte, another source sha or an unlisted file => HOLD
SI-6 CI not green for the commit => HOLD, whatever the artifact says
SI-7 the digests of the code the seal job runs cannot be computed => null, not green
SI-8 the checkout must be the commit, clean, and the commit an ancestor of origin/main                                                                              (workflow 'Bind to the reviewed sealing revision')
SI-9 the seal job's own digest is the registry's definition over the checkout's modules and follows an edit of a governed module                                   (implementation_registry; ST-WIRE-2 item 3)
SI-10 a verdict is FRESH only when every check is True, and every non-True check says why                                                                          (N.8)
OV-1 the overlay selection equals the action's predicates (pinned to action.yml), and the lock/tool paths are the repository's
CO-1 the evidence calls are read-only `gh` calls, the artifact goes into a fresh directory, and the selected run is the one downloaded
FZ-1 START is written only against a passing, untampered, recent dispatch_gate verdict for that commit
FZ-2 START is exactly-once per freeze and one freeze is open per chart; a new freeze after an END gets its own id
FZ-3 END(SEALED) needs the seal controller's own SEALED.json for that chart/generation/head; ABANDONED/ABORTED need a reason; END is exactly-once
FZ-4 only the governed writers, only the canonical chart, only the campaign ledger, never over a ledger that cannot be read
FZ-5 the append leaves every existing byte alone (including an unterminated last line)
FZ-6 the freeze state is replayed from the ledger; an order the writers cannot produce is UNKNOWN and nothing is written over it
FZ-7 the lease-row note carries the authority, the chart and the commit / outcome
FZ-8 the SEALED.json the seal controller really writes is accepted by END(SEALED)
CL-1 the command line exits 0 on FRESH, 2 on HOLD, and writes the freeze events end to end
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(os.environ.get("SEAL_INPUTS_UNDER_TEST_DIR") or Path(__file__).resolve().parents[1])
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(FLEET))
import seal_inputs as si  # noqa: E402

GOV = REPO / "platform" / "scripts" / "governance"
UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 22, 9, 0, 0, tzinfo=UTC)
C = "a" * 40
OTHER = "b" * 40
CHART = si.CANONICAL_CHART
GEN = "5.0"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


ci_generated = _load("ci_generated_for_seal_inputs", GOV / "ci_generated.py")


# ── fixtures ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def run(id=101, sha=C, event="push", branch="main", status="completed", conclusion="success", created="2026-10-22T08:00:00Z", path=None):
    r = {"id": id, "head_sha": sha, "event": event, "head_branch": branch, "status": status, "conclusion": conclusion, "created_at": created}
    if path:
        r["path"] = path
    return r


def runs_doc(*runs):
    return {"total_count": len(runs), "workflow_runs": list(runs)}


def art(id=9001, name="ci-generated", expired=False, expires="2027-01-20T08:00:00Z"):
    return {"id": id, "name": name, "expired": expired, "expires_at": expires}


def listing(*arts):
    return {"total_count": len(arts), "artifacts": list(arts)}


def good_gate_inputs():
    return dict(runs_doc=runs_doc(run()), artifacts_by_run={"101": listing(art())}, now=NOW)


LOCK = {"schema": si.LOCK_SCHEMA, "implementation_digest": "d" * 64, "stages": {"evaluation": "e" * 64, "geometry": "f" * 64, "window": "1" * 64}}
STALE = {**LOCK, "implementation_digest": "5" * 64, "stages": {**LOCK["stages"], "window": "2" * 64}}


def make_artifact(root, sha=C, lock=LOCK):
    """A ci-generated artifact for `sha`: every declared output, the lock inside, a manifest in the real shape (ci_generated.manifest)."""
    root = Path(root)
    for rel in ci_generated.OUTPUTS:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n" if rel == si.LOCK_REL else f"generated {rel}\n", encoding="utf-8")
    (root / ci_generated.MANIFEST).write_text(json.dumps(ci_generated.manifest(root, sha, ci_generated.OUTPUTS), indent=2) + "\n", encoding="utf-8")
    return root


def fake_git(commit=C, dirty="", ancestor=0, committed=STALE):
    def git(args):
        if args[:2] == ["rev-parse", "HEAD"]:
            return 0, commit
        if args[:2] == ["status", "--porcelain"]:
            return 0, dirty
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return ancestor, ""
        if args[0] == "show":
            return 0, json.dumps(committed)
        return 1, ""
    return git


def fresh(tmp_path, **over):
    art_dir = make_artifact(tmp_path / "artifact", lock=over.pop("lock", LOCK))
    own = over.pop("own", LOCK)
    kw = dict(checkout=tmp_path, artifact_dir=art_dir, downloaded_run_id=101, runs_doc=runs_doc(run()), artifacts_by_run={"101": listing(art())}, now=NOW,
              digest_runner=lambda c: copy.deepcopy(own), overlay_runner=lambda c, a, s: (0, ""), git=fake_git())
    kw.update(over)
    return si.seal_inputs_fresh(C, **kw)


def holds(v, check):
    assert v["ok"] is False and v["status"] == "HOLD"
    assert any(r.startswith(check + ":") for r in v["reasons"]), v["reasons"]
    return v["checks"][check]


# ── the #3817 dispatch gate ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_dg1_green_push_main_run_and_unexpired_artifact_pass():
    v = si.dispatch_gate(C, **good_gate_inputs())
    assert v["ok"] is True and v["status"] == "FRESH" and v["reasons"] == []
    assert v["checks"] == {"commit_wellformed": True, "push_main_ci_green": True, "artifact_present": True, "artifact_margin": True}
    assert v["evidence"]["push_main_run"] == 101 and v["evidence"]["artifact_id"] == 9001


@pytest.mark.parametrize("runs", [
    [run(event="pull_request")],                                                   # a PR run for the same sha is not main's CI
    [run(branch="feature/x")],                                                     # a push to another branch
    [run(conclusion="failure")],
    [run(status="in_progress", conclusion=None)],
    [run(id=101, conclusion="success", created="2026-10-22T08:00:00Z"), run(id=102, conclusion="failure", created="2026-10-22T08:30:00Z")],   # the NEWEST push-main run is red
], ids=["pr-event", "other-branch", "failed", "in-progress", "newest-red"])
def test_dg2_only_the_newest_push_to_main_run_counts(runs):
    v = si.dispatch_gate(C, runs_doc=runs_doc(*runs), artifacts_by_run={str(r["id"]): listing(art()) for r in runs}, now=NOW)
    assert holds(v, "push_main_ci_green") is False


@pytest.mark.parametrize("listing_doc,present", [
    (listing(), False),
    (listing(art(expired=True)), False),
    (listing(art(name="something-else")), False),
])
def test_dg3_no_unexpired_ci_generated_artifact_holds(listing_doc, present):
    v = si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={"101": listing_doc}, now=NOW)
    assert holds(v, "artifact_present") is present
    assert v["checks"]["push_main_ci_green"] is True                                # the CI is green; the hold is the artifact alone


def test_dg3b_the_artifact_may_come_from_an_older_green_run_of_the_same_commit():
    """action.yml walks the successful runs in listing order and takes the first with a non-expired artifact."""
    runs = [run(id=102, created="2026-10-22T08:30:00Z"), run(id=101)]
    v = si.dispatch_gate(C, runs_doc=runs_doc(*runs), artifacts_by_run={"102": listing(art(expired=True)), "101": listing(art(id=7))}, now=NOW)
    assert v["ok"] is True and v["evidence"]["overlay_run"] == 101 and v["evidence"]["artifact_id"] == 7


def test_dg4_margin_and_unreadable_expiry():
    soon = si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={"101": listing(art(expires="2026-10-23T09:00:00Z"))}, now=NOW)   # 24 h left, 72 h needed
    assert holds(soon, "artifact_margin") is False
    assert si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={"101": listing(art(expires="2026-10-23T09:00:00Z"))}, now=NOW, min_remaining_hours=12)["ok"] is True
    unreadable = si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={"101": listing(art(expires=None))}, now=NOW)
    assert holds(unreadable, "artifact_margin") is None


def test_dg5_evidence_for_another_commit_is_not_evidence_for_this_one():
    v = si.dispatch_gate(C, runs_doc=runs_doc(run(sha=OTHER)), artifacts_by_run={"101": listing(art())}, now=NOW)
    assert holds(v, "push_main_ci_green") is False and v["checks"]["artifact_present"] is False
    assert si.dispatch_gate("zzz", **good_gate_inputs())["checks"]["commit_wellformed"] is False


def test_dg6_unreadable_or_missing_evidence_is_null_not_pass():
    assert holds(si.dispatch_gate(C, runs_doc="garbage", artifacts_by_run={}, now=NOW), "push_main_ci_green") is None
    missing = si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={}, now=NOW)                  # a green run whose artifact listing was never fetched
    assert holds(missing, "artifact_present") is None and missing["checks"]["push_main_ci_green"] is True
    assert holds(si.dispatch_gate(C, runs_doc=runs_doc(run()), artifacts_by_run={"101": {"nope": 1}}, now=NOW), "artifact_present") is None


# ── the seal-input detector ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_si1_fresh(tmp_path):
    v = fresh(tmp_path)
    assert v["ok"] is True and v["reasons"] == [] and set(v["checks"]) == {
        "ci_green", "artifact_present", "artifact_margin", "artifact_from_selected_run", "overlay_verified", "lock_equals_seal_digests", "checkout_is_commit", "commit_on_main"}
    assert v["evidence"]["lock_implementation_digest"] == v["evidence"]["seal_job_implementation_digest"] == LOCK["implementation_digest"]


def test_si2_a_lock_that_differs_from_the_seal_jobs_digests_holds(tmp_path):
    v = fresh(tmp_path, lock=STALE, own=LOCK)                                      # same shape of defect the v1.6 rehearsal measured
    assert holds(v, "lock_equals_seal_digests") is False
    assert "own_checkout_digest_mismatch" in " ".join(v["reasons"]) and "window" in " ".join(v["reasons"])
    # the top digest equal but one stage differing is still a mismatch (a lock that is not self-consistent registers nothing)
    odd = {**LOCK, "stages": {**LOCK["stages"], "geometry": "9" * 64}}
    assert holds(fresh(tmp_path / "b", lock=odd, own=LOCK), "lock_equals_seal_digests") is False


def test_si3_the_committed_lock_is_not_the_comparand(tmp_path):
    v = fresh(tmp_path, git=fake_git(committed=STALE))                              # main's committed lock is stale; the artifact's lock is current
    assert v["ok"] is True
    assert v["evidence"]["committed_lock_implementation_digest"] == STALE["implementation_digest"] != v["evidence"]["lock_implementation_digest"]


def test_si4_an_artifact_from_another_run_than_the_overlay_would_pick_holds(tmp_path):
    v = fresh(tmp_path, downloaded_run_id=777)
    assert holds(v, "artifact_from_selected_run") is False


def test_si5_the_checkouts_own_overlay_tool_decides_the_artifact(tmp_path):
    """Real tool, real manifest shape (apply_generated_overlay.py: source SHA, every byte, the full declared set, nothing extra)."""
    ok = fresh(tmp_path / "ok", overlay_runner=None, checkout=REPO)
    assert ok["checks"]["overlay_verified"] is True and ok["checks"]["lock_equals_seal_digests"] is True       # the real tool accepts a real-shaped artifact
    bad_byte = make_artifact(tmp_path / "byte")
    (bad_byte / "00_ARCHITECTURE/control/registry_coverage_report.json").write_text("tampered\n")
    other_sha = make_artifact(tmp_path / "sha", sha=OTHER)
    extra = make_artifact(tmp_path / "extra")
    (extra / "platform/src/evil.ts").parent.mkdir(parents=True, exist_ok=True)
    (extra / "platform/src/evil.ts").write_text("x\n")
    for d in (bad_byte, other_sha, extra):
        v = fresh(tmp_path / ("v" + d.name), artifact_dir=d, overlay_runner=None, checkout=REPO)
        assert v["checks"]["overlay_verified"] is False, d
        assert v["checks"]["lock_equals_seal_digests"] is False                     # an unverified artifact's lock is never read as evidence
        assert v["ok"] is False


def test_si6_ci_not_green_holds_whatever_the_artifact_says(tmp_path):
    v = fresh(tmp_path, runs_doc=runs_doc(run(conclusion="failure")), artifacts_by_run={"101": listing(art())})
    assert holds(v, "ci_green") is False and v["checks"]["artifact_present"] is False
    assert holds(fresh(tmp_path / "b", runs_doc=runs_doc(run(sha=OTHER))), "ci_green") is False


def test_si7_digests_of_the_seal_jobs_code_that_cannot_be_computed_are_null(tmp_path):
    v = fresh(tmp_path, digest_runner=lambda c: None)
    assert holds(v, "lock_equals_seal_digests") is None


def test_si8_checkout_must_be_the_clean_commit_on_main(tmp_path):
    assert holds(fresh(tmp_path / "1", git=fake_git(commit=OTHER)), "checkout_is_commit") is False
    assert holds(fresh(tmp_path / "2", git=fake_git(dirty=" M platform/python-sidecar/x.py")), "checkout_is_commit") is False
    assert holds(fresh(tmp_path / "3", git=fake_git(ancestor=1)), "commit_on_main") is False
    assert holds(fresh(tmp_path / "4", git=fake_git(ancestor=128)), "commit_on_main") is None


def _git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


def test_si8b_real_git_checkout_checks(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "f.txt").write_text("1\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "one")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/main", head)

    def verdict_for(commit):
        art_dir = make_artifact(tmp_path / ("a" + commit[:4]), sha=commit)
        return si.seal_inputs_fresh(commit, checkout=repo, artifact_dir=art_dir, downloaded_run_id=101, runs_doc=runs_doc(run(sha=commit)), artifacts_by_run={"101": listing(art())},
                                    now=NOW, digest_runner=lambda c: copy.deepcopy(LOCK), overlay_runner=lambda c, a, s: (0, ""))
    v = verdict_for(head)
    assert v["checks"]["checkout_is_commit"] is True and v["checks"]["commit_on_main"] is True
    (repo / "g.txt").write_text("untracked\n")
    assert verdict_for(head)["checks"]["checkout_is_commit"] is False             # an untracked file: the code the seal runs is not the commit
    (repo / "g.txt").unlink()
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "f.txt").write_text("2\n")
    _git(repo, "commit", "-q", "-am", "two")
    side = _git(repo, "rev-parse", "HEAD")
    assert verdict_for(side)["checks"]["commit_on_main"] is False                # on a branch, not on main


def test_si9_the_seal_jobs_digest_follows_its_own_code(tmp_path):
    """window_gate.implementation_digest = sha256(canonical {stage: stage digest}); `seal_job` is a governed module (implementation_registry docstring, ST-WIRE-2 item 3)."""
    own = si.default_digest_runner(REPO)
    assert own is not None and set(own["stages"]) >= {"geometry", "evaluation", "window"}
    assert own["implementation_digest"] == hashlib.sha256(si.canon(own["stages"]).encode()).hexdigest()
    sidecar = tmp_path / "platform" / "python-sidecar"
    shutil.copytree(REPO / "platform" / "python-sidecar", sidecar, ignore=shutil.ignore_patterns("__pycache__", "tests", "*.pyc", ".venv", "node_modules", "data"))
    assert si.default_digest_runner(tmp_path) == own                                # an identical copy digests identically
    job = sidecar / "pipeline" / "orchestrator" / "seal_job.py"
    job.write_text(job.read_text() + "\n# an edit after review\n")
    edited = si.default_digest_runner(tmp_path)
    assert edited is not None and edited["implementation_digest"] != own["implementation_digest"]
    assert [s for s in own["stages"] if own["stages"][s] != edited["stages"][s]] == ["window"]
    assert si.default_digest_runner(tmp_path / "nowhere") is None                   # nothing to import => null, not a digest


@pytest.mark.parametrize("over", [{}, {"lock": STALE}, {"downloaded_run_id": 5}, {"digest_runner": lambda c: None}, {"git": fake_git(ancestor=128)},
                                  {"runs_doc": "garbage"}, {"runs_doc": runs_doc(run(conclusion="failure"))}])
def test_si10_fresh_only_when_every_check_is_true_and_every_other_check_says_why(tmp_path, over):
    v = fresh(tmp_path, **over)
    assert v["ok"] == all(c is True for c in v["checks"].values())
    assert v["status"] == ("FRESH" if v["ok"] else "HOLD")
    for name, value in v["checks"].items():
        if value is not True:
            assert any(r.startswith(name + ":") and len(r) > len(name) + 3 for r in v["reasons"]), name
    assert v["verdict_sha256"] == si.verdict_digest(v)


# ── parity with the repository's own machinery ───────────────────────────────────────────────────────────────────────────────────────

def test_ov1_selection_and_paths_are_the_repositories():
    action = (REPO / ".github/actions/apply-generated-overlay/action.yml").read_text()
    for needle in ("workflow_id: 'ci.yml'", "head_sha: sha", "r.status === 'completed' && r.conclusion === 'success'", "a.name === 'ci-generated' && !a.expired"):
        assert needle in action, needle
    assert si.ARTIFACT == "ci-generated" and si.CI_WORKFLOW == "ci.yml"
    assert si.LOCK_REL in ci_generated.OUTPUTS                                      # the lock IS a CI-generated output: it is never hand-edited
    assert (REPO / si.OVERLAY_TOOL).is_file() and (REPO / si.LOCK_REL).is_file()
    assert si.LOCK_SCHEMA == json.loads((REPO / si.LOCK_REL).read_text())["schema"]
    seal_controller = _load("seal_controller_for_seal_inputs", FLEET / "seal_controller.py")
    assert si.SEAL_SCHEMA == seal_controller.SCHEMA and si.REPO_SLUG == seal_controller.REPO_SLUG
    assert si.CANONICAL_CHART == "482012f1-710e-4a25-994a-93821f5871aa"


def test_co1_collection_is_read_only_into_a_fresh_directory(tmp_path):
    calls = []

    def runner(argv):
        calls.append(argv)
        if "/artifacts" in argv[-1]:
            return 0, json.dumps([listing(art(id=7))])
        if argv[:3] == ["gh", "run", "download"]:
            Path(argv[argv.index("-D") + 1]).mkdir(parents=True, exist_ok=True)
            return 0, ""
        return 0, json.dumps([runs_doc(run(id=102, created="2026-10-22T08:30:00Z"), run(id=101, conclusion="failure"))])
    dest = tmp_path / "fresh"
    got = si.collect_evidence(C, runner, dest, now=NOW)
    assert got["downloaded_run_id"] == 102 and list(got["artifacts_by_run"]) == ["102"]
    assert all(c[:2] == ["gh", "api"] or c[:3] == ["gh", "run", "download"] for c in calls)
    assert not any(w in " ".join(" ".join(c) for c in calls) for w in ("-X", "--method", "POST", "PATCH", "DELETE", "workflow run"))
    assert si.gh_commands(C)["runs"][-1].startswith("repos/Marsys-Technologies/Madhav/actions/workflows/ci.yml/runs?head_sha=" + C)
    dest2 = tmp_path / "used"
    dest2.mkdir()
    (dest2 / "old").write_text("x")
    with pytest.raises(RuntimeError):
        si.collect_evidence(C, runner, dest2, now=NOW)


# ── the XC-FREEZE ledger ──────────────────────────────────────────────────────────────────────────────────────────────────────────

EXISTING = (json.dumps({"id": "SR-BEFORE-SEAL", "kind": "surrogate ruling", "decision": "B-03 cross-campaign freeze imposed (SR-XC-FREEZE-482012f1)"}) + "\n"
            + json.dumps({"id": "EXEC-X", "kind": "execution record", "detail": "unrelated"}) + "\n")


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "run" / si.LEDGER_NAME
    p.parent.mkdir()
    p.write_text(EXISTING, encoding="utf-8")
    return p


def gate_verdict(commit=C, at=NOW, **over):
    inputs = good_gate_inputs()
    inputs["now"] = at
    inputs.update(over)
    return si.dispatch_gate(commit, **inputs)


def start(ledger, gate=None, **over):
    kw = dict(chart_id=CHART, generation=GEN, commit=C, gate=gate if gate is not None else gate_verdict(), by="dispatch-chain", now=NOW + dt.timedelta(minutes=2))
    kw.update(over)
    return si.freeze_start(ledger, **kw)


def events(ledger):
    return [json.loads(l) for l in ledger.read_text().splitlines() if '"freeze event"' in l]


def sealed_doc(commit=C, **over):
    d = {"schema": si.SEAL_SCHEMA, "kind": "sealed", "key": f"{GEN}@{commit}", "chart_id": CHART, "generation": GEN, "head": commit, "run_id": 4242, "attempt": 1,
         "brief_digest": "c" * 64, "approver": "amonty84", "readback": {"operation_id": "seal-controller-final-x", "state": "SEALED", "why": "ok"}, "ts": "2026-10-22T20:00:00Z"}
    d.update(over)
    return d


def test_fz1_start_needs_a_passing_untampered_recent_gate_for_that_commit(ledger):
    before = ledger.read_bytes()
    bad_gate = gate_verdict(runs_doc=runs_doc(run(conclusion="failure")))
    forged = copy.deepcopy(bad_gate)
    forged["ok"], forged["status"] = True, "FRESH"                                    # edited after measurement: the digest no longer matches
    edited = copy.deepcopy(gate_verdict())
    edited["commit"] = OTHER
    for gate, why in ((None, "dispatch_gate verdict"), (bad_gate, "not a pass"), (forged, "digest"), (gate_verdict(commit=OTHER), "not a pass"),
                      (gate_verdict(at=NOW - dt.timedelta(hours=2)), "last"), (edited, "digest")):
        with pytest.raises(si.LedgerRefused, match=why):
            start(ledger, gate=gate if gate is not None else {})
    assert ledger.read_bytes() == before                                              # nothing written by any refusal
    seal_gate = {"detector": "seal_inputs_fresh"}
    with pytest.raises(si.LedgerRefused):
        start(ledger, gate=seal_gate)
    r = start(ledger)
    assert r["result"] == "NEW" and r["event"]["event"] == "START" and r["event"]["authority"] == "SR-XC-FREEZE-482012f1" and r["event"]["ccd"] == "CCD-028"
    assert r["event"]["gate"]["verdict_sha256"] == gate_verdict()["verdict_sha256"] and r["event"]["by"] == "dispatch-chain"


def test_fz2_start_is_once_per_freeze_and_one_freeze_is_open_per_chart(ledger):
    first = start(ledger)
    again = start(ledger)
    assert again["result"] == "ALREADY" and len(events(ledger)) == 1 and again["event"]["id"] == first["event"]["id"]
    with pytest.raises(si.LedgerRefused, match="one open freeze"):
        start(ledger, generation="6.0")
    other_gate = gate_verdict(commit=OTHER, runs_doc=runs_doc(run(sha=OTHER)))
    assert other_gate["ok"] is True
    with pytest.raises(si.LedgerRefused, match="one open freeze"):
        start(ledger, commit=OTHER, gate=other_gate)
    si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="ABORTED", by="cockpit", reason="dispatch aborted: image digest mismatch", now=NOW)
    second = start(ledger)                                                            # a re-dispatch after an END is a new freeze with its own id
    assert second["result"] == "NEW" and second["event"]["id"] != first["event"]["id"] and second["event"]["id"].endswith("-START-2")
    assert len({e["id"] for e in events(ledger)}) == 3


def test_fz3_end_needs_the_seal_controllers_evidence_or_a_reason_and_is_once(ledger):
    with pytest.raises(si.LedgerRefused, match="no freeze is IN FORCE"):
        si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="SEALED", by="seal-controller", sealed_doc=sealed_doc())
    start(ledger)
    before = ledger.read_bytes()
    for bad, why in ((None, "SEALED.json"), (sealed_doc(commit=OTHER), "not this freeze"), (sealed_doc(generation="9.9"), "not this freeze"), (sealed_doc(chart_id="x"), "not this freeze"),
                     (sealed_doc(readback={"state": "INCONSISTENT"}), "readback"), (sealed_doc(kind="approval_bundle"), "SEALED.json"), (sealed_doc(brief_digest="short"), "brief digest")):
        with pytest.raises(si.LedgerRefused, match=why):
            si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="SEALED", by="seal-controller", sealed_doc=bad)
    for outcome in ("ABANDONED", "ABORTED"):
        with pytest.raises(si.LedgerRefused, match="reason"):
            si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome=outcome, by="cockpit", reason="  short ")
    with pytest.raises(si.LedgerRefused, match="outcome"):
        si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="DONE", by="cockpit")
    with pytest.raises(si.LedgerRefused, match="open freeze"):
        si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=OTHER, outcome="ABANDONED", by="cockpit", reason="a different dispatch commit was abandoned")
    assert ledger.read_bytes() == before
    done = si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="SEALED", by="seal-controller", sealed_doc=sealed_doc(), now=NOW)
    assert done["result"] == "NEW" and done["event"]["outcome"] == "SEALED" and done["event"]["sealed"]["brief_digest"] == "c" * 64
    assert si.freeze_state(ledger)["state"] == "ENDED"
    twice = si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="SEALED", by="seal-controller", sealed_doc=sealed_doc(), now=NOW)
    assert twice["result"] == "ALREADY" and len(events(ledger)) == 2


def test_fz4_only_governed_writers_the_canonical_chart_the_campaign_ledger_and_a_readable_ledger(ledger, tmp_path):
    before = ledger.read_bytes()
    with pytest.raises(si.LedgerRefused, match="may not write"):
        start(ledger, by="build-job")
    with pytest.raises(si.LedgerRefused, match="canonical|covers chart"):
        start(ledger, chart_id="362f9f17-0000-0000-0000-000000000000")
    elsewhere = tmp_path / "notes.jsonl"
    elsewhere.write_text(EXISTING)
    with pytest.raises(si.LedgerRefused, match="campaign ledger"):
        start(elsewhere)
    with pytest.raises(si.LedgerRefused, match="missing"):
        start(tmp_path / "nodir" / si.LEDGER_NAME)
    assert not (tmp_path / "nodir").exists()                                          # a freeze event never creates the ledger
    garbage = tmp_path / "g" / si.LEDGER_NAME
    garbage.parent.mkdir()
    garbage.write_text(EXISTING + "not json at all\n")
    with pytest.raises(si.LedgerRefused, match="not JSON"):
        start(garbage)
    assert ledger.read_bytes() == before and "not json" in garbage.read_text() and "freeze event" not in garbage.read_text()
    with pytest.raises(si.LedgerRefused, match="unsafe"):
        start(ledger, generation="5 0;rm")


def test_fz5_the_append_leaves_every_existing_byte_alone(ledger):
    ledger.write_bytes(EXISTING.encode() + b'{"id": "SR-TAIL", "kind": "surrogate ruling"}')   # an unterminated last line
    before = ledger.read_bytes()
    start(ledger)
    after = ledger.read_bytes()
    assert after.startswith(before) and after[len(before):len(before) + 1] == b"\n"           # the old tail is not swallowed
    lines = after.decode().splitlines()
    assert len(lines) == 4 and json.loads(lines[2])["id"] == "SR-TAIL" and json.loads(lines[3])["event"] == "START"


def test_fz6_state_is_replayed_and_an_impossible_order_is_unknown(ledger):
    assert si.freeze_state(ledger)["state"] == "NONE"
    start(ledger)
    assert si.freeze_state(ledger)["state"] == "IN_FORCE"
    other_chart = copy.deepcopy(events(ledger)[0])
    other_chart.update(chart_id="11111111-1111-1111-1111-111111111111", event="END", id="X")
    with ledger.open("a") as f:
        f.write(json.dumps(other_chart) + "\n")
    assert si.freeze_state(ledger)["state"] == "IN_FORCE"                             # another chart's events are none of this freeze's business
    stray = copy.deepcopy(events(ledger)[0])
    stray.update(event="END", generation="7.7", id="XC-stray")
    with ledger.open("a") as f:
        f.write(json.dumps(stray) + "\n")
    st = si.freeze_state(ledger)
    assert st["state"] == "UNKNOWN" and st["problems"]
    before = ledger.read_bytes()
    with pytest.raises(si.LedgerRefused, match="inconsistent"):
        start(ledger)
    with pytest.raises(si.LedgerRefused, match="no freeze is IN FORCE"):
        si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="ABORTED", by="cockpit", reason="the window was abandoned")
    assert ledger.read_bytes() == before


def test_fz7_the_lease_note_names_authority_chart_and_commit(ledger):
    s = start(ledger)
    note = s["lease_note"]
    assert "SR-XC-FREEZE-482012f1" in note and "CCD-028" in note and CHART in note and C[:12] in note and "IN FORCE" in note
    e = si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="ABANDONED", by="cockpit", reason="window abandoned by the owner", now=NOW)
    assert "ENDED" in e["lease_note"] and "ABANDONED" in e["lease_note"] and "no longer frozen" in e["lease_note"]


def test_fz8_the_sealed_json_the_seal_controller_really_writes_ends_the_freeze(ledger, tmp_path):
    sc = _load("seal_controller_for_seal_inputs_emit", FLEET / "seal_controller.py")
    a = {"chart_id": CHART, "generation": GEN, "head": C}
    brief = {"run_id": 4242, "attempt": 1, "brief_digest": "c" * 64}
    out = tmp_path / "out"
    sc.emit_final(a, brief, {"approver": "amonty84"}, {"operation_id": "seal-controller-final-x", "state": "SEALED", "why": "ok"}, out, tmp_path / "pages.log", NOW)
    doc = json.loads((out / "SEALED.json").read_text())
    assert si.sealed_problem(doc, CHART, GEN, C) is None
    start(ledger)
    assert si.freeze_end(ledger, chart_id=CHART, generation=GEN, commit=C, outcome="SEALED", by="seal-controller", sealed_doc=doc, now=NOW)["result"] == "NEW"


def test_cl1_command_line_end_to_end(tmp_path, ledger):
    runs, arts = tmp_path / "runs.json", tmp_path / "arts.json"
    runs.write_text(json.dumps([runs_doc(run())]))
    arts.write_text(json.dumps({"101": listing(art(expires="2099-01-01T00:00:00Z"))}))
    cli = [sys.executable, str(FLEET / "seal_inputs.py")]
    ok = subprocess.run(cli + ["dispatch-gate", "--commit", C, "--runs", str(runs), "--artifacts", str(arts)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(ok.stdout)
    assert json.loads(ok.stdout)["ok"] is True
    runs.write_text(json.dumps([runs_doc(run(conclusion="failure"))]))
    red = subprocess.run(cli + ["dispatch-gate", "--commit", C, "--runs", str(runs), "--artifacts", str(arts)], capture_output=True, text=True)
    assert red.returncode == 2 and json.loads(red.stdout)["status"] == "HOLD"
    started = subprocess.run(cli + ["freeze-start", "--ledger", str(ledger), "--generation", GEN, "--commit", C, "--gate", str(gate_file), "--by", "dispatch-chain"], capture_output=True, text=True)
    assert started.returncode == 0, started.stderr
    stale = tmp_path / "stale.json"
    g = json.loads(ok.stdout)
    g["evaluated_at"] = "2020-01-01T00:00:00Z"
    stale.write_text(json.dumps(g))
    refused = subprocess.run(cli + ["freeze-start", "--ledger", str(ledger), "--generation", "6.0", "--commit", C, "--gate", str(stale), "--by", "dispatch-chain"], capture_output=True, text=True)
    assert refused.returncode == 2 and "REFUSED" in refused.stderr
    state = subprocess.run(cli + ["freeze-state", "--ledger", str(ledger)], capture_output=True, text=True)
    assert json.loads(state.stdout)["state"] == "IN_FORCE"
    ended = subprocess.run(cli + ["freeze-end", "--ledger", str(ledger), "--generation", GEN, "--commit", C, "--outcome", "ABORTED", "--by", "cockpit", "--reason", "aborted before the build ran"],
                           capture_output=True, text=True)
    assert ended.returncode == 0, ended.stderr
    assert [e["event"] for e in events(ledger)] == ["START", "END"]
