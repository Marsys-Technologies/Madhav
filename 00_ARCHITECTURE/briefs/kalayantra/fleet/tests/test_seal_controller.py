"""Oracles for seal_controller.py (SC-1; PLAN_A10_1 §5; A10.1 B8) — one doctrine-grounded oracle per distinct claim, fixtures only: no database, no network, no gh / gcloud.

"Green" of every reviewed check is the REAL script's exit 0 (platform/scripts/gochara_seal_brief_check.py, gochara_seal_execution_check.py check-envelope, gochara_seal_approval.py),
never a stub.  The executor's readback answers are written by the fixture from the controller's OWN request documents, so the request -> receipt route is exercised end to end.

Claims (root CLAUDE.md §N.8: each is measured by a detector that can read false; the workflow design record is `00_ARCHITECTURE/briefs/pravaha/design/SEAL_APPROVAL_PAYLOAD_v1_2.md`):
  A1  a numbers-on (`window_qualification/1`) candidate with every stage's evidence reaches "approval requested" and is never refused as an all-NULL candidate   (PLAN §5 SC-1g)
  A2  the class universe is the ADOPTED 26, never the surviving rows: a live universe missing one class refuses                                                       (R8X / B3)
  A3  one runner commit = the head: a grain verified at another commit refuses                                                                                         (R8X / B3)
  A4  an aggregate without PASSED G-6 evidence is not passed                                                                                                           (PLAN §4 R8X, T18)
  A5  the live sums must equal the aggregate's                                                                                                                         (§N.8 recount)
  A6  every grain must be VERIFIED with a PASSED attestation                                                                                                            (generation_verdict)
  A7  INCONCLUSIVE share over 0.5 % is not passed, exactly at the cap is                                                                                                (G-3 check 4)
  A8  no grain readback yet => AWAITING_READBACK and a readback_sql request document (sql digest bound); nothing is passed without it
  B1  no brief yet => the exact dispatch command is prepared and the surrogate paged exactly once
  B2  a brief the reviewed check refuses => REFUSED                                                                                                                     (gochara_seal_brief_check)
  B3  a head that is not an ancestor of main => REFUSED (not main-produced)                                                                                              (workflow step 1)
  B4  an envelope of another run / attempt => REFUSED                                                                                                                    (check_envelope)
  B5  the brief's numerical verdict must equal the aggregate's                                                                                                           (one candidate)
  B6  a brief produced for another head => STALE_HEAD
  C1  approval prepared once per (generation, head, run, attempt): bundle, exact approval comment + command, messages, one page   — and a second run dispatches nothing new   (SC-1a)
  C2  a page that cannot be written leaves no marker, a later run repairs it with exactly one page                                                                       (SC-1f)
  C3  a quiescence record that is not ACCEPTED with every check true => no approval is prepared                                                                          (SC-1h)
  C4  a brief changed after the approval was prepared => REFUSED, never re-approved                                                                                       (SC-1b)
  C5  the controller itself runs only python and git: no gh / gcloud, so it cannot approve or seal
  D1  no approval history => AWAITING_APPROVAL; the valid approval of THIS run by the required reviewer => the seal readback is requested
  D2  an approval naming another run / attempt is never reused => REFUSED                                                                                                 (SC-1d)
  D3  an approval by any other principal => REFUSED                                                                                                                       (SC-1e)
  D4  a sealer run that ended cancelled with nothing sealed => RETRY_NEEDED, paged once, only a fresh run may retry                                                       (SC-1c)
  E1  SEALED needs the readback to name THIS run's approved digest; then one SEALED page
  E2  INCONSISTENT => HALT marker + one page, and the next poll does nothing else
  E3  an unreadable / failed readback is UNKNOWN, never "not sealed" => HALT
  E4  a successful sealer run with nothing sealed => HALT (not a retry)
  P1  `classify` equals gochara_seal_reconcile.classify and the approval line equals gochara_seal_approval's grammar
  R1  owner step 11 done = a completed `success` definition run at the head whose job AND four named steps read back `success`; then one REDEPLOY-DONE page and the evidence in the bundle
  R2  a run that concluded `success` but whose readback/preflight step did not read back `success` is NOT accepted                                                           (OWNER_GUIDE_v2 step 11)
  R3  main moved off the sealing head => STALE_HEAD and nothing is dispatched; after the brief is produced a later merge no longer stales the seal chain
  R4  CI not green at the head (failed / absent / still running) => nothing is dispatched                                                                                    (deploy.yml dispatch gate)
  R5  without --execute-redeploy the dispatch is only PREPARED (exact command) and paged once; no gh write
  R6  with --execute-redeploy and the delegated login: exactly ONE definition dispatch, never repeated while the run is not yet visible / running; success advances
  R7  a gh login other than the delegated one => REFUSED, nothing dispatched
  R8  the definition failing AT the digest step => owner step 11a: ONE deploy.yml dispatch with ci_gate=require-ci-green (never the override), then the definition again; a second digest failure HALTS
  R9  a definition run failing at any other step, a failed or pipeline-job-skipped package run, or a dispatch whose run never appears => HALT marker + one page, nothing else is done
  R10 the gh allow-list: reads + the two dispatches only — never the seal workflow, an approval, the override choice, a POST or gcloud
  R11 run evidence for another commit is refused, never used
  R12 the names the controller reads (workflow files, confirm phrase, job, steps, deploy jobs, ci_gate) exist in the real workflow files
  L1  a retained step-10 proof (view returned >= 1 job entry, only job entries) is re-measured, reaches approval requested, and the bundle + surrogate message carry `view_refusal_outside` = NULL   (surrogate ruling 09:2xZ)
  L2  no retained proof => HOLD (named), no approval prepared
  L3  a non-job entry in the retained view => HOLD naming it
  L4  an empty view => HOLD
  L5  a retained proof that reports `view_refusal_outside` green (or any recorded row/verdict the groups do not give) => HOLD: a signal without a detector is null, never green   (§N.8)
  L6  a proof of another run / attempt is never reused => HOLD
(the detector's own claims V1–V8 are in test_log_view_proof.py)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SCRIPTS = REPO / "platform" / "scripts"
sys.path.insert(0, str(SCRIPTS))                       # the reviewed scripts import their siblings (this process only)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


import os  # noqa: E402

lvp_real = _load("log_view_proof_real", HERE.parent / "log_view_proof.py")        # fixtures are always built by the REAL detector; the controller under test loads its own sibling
sc = _load("seal_controller_under_test", Path(os.environ.get("SEAL_CONTROLLER", HERE.parent / "seal_controller.py")))
chk = _load("seal_check_real", SCRIPTS / "gochara_seal_brief_check.py")
exe = _load("seal_exec_real", SCRIPTS / "gochara_seal_execution_check.py")
appr = _load("seal_approval_real", SCRIPTS / "gochara_seal_approval.py")
rec = _load("seal_reconcile_real", SCRIPTS / "gochara_seal_reconcile.py")

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
GEN = "5.0"
CLASSES = [f"class_{i:02d}" for i in range(26)]
VERIF_OP = "ver-20261021-seal"
RUN, ATT = 7001, 1
APPROVER = sc.DEFAULT_APPROVER
TABLE = chk.QUALIFICATION_TABLE_BINDING


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, env=env, check=True)
    return p.stdout.strip()


NOW = __import__("datetime").datetime(2026, 10, 22, 10, 0, 0, tzinfo=__import__("datetime").timezone.utc)
OLD_SHA = "9" * 40


def run_row(rid, head, *, status="completed", conclusion="success", event="workflow_dispatch", branch="main", created="2026-10-22T09:00:00Z"):
    return {"id": rid, "head_sha": head, "status": status, "conclusion": conclusion if status == "completed" else None, "event": event, "head_branch": branch,
            "created_at": created, "html_url": f"https://github.example/runs/{rid}"}


def def_jobs(*, fail=None, skip=None):
    """The definition workflow's steps (names as in the real file, long forms), one job.  `fail` = a DEF_STEPS prefix that fails (later steps skipped); `skip` = a prefix that reads skipped."""
    steps, failed = [], False
    for name in ("Set up job", "Checkout the dispatched commit", "Authenticate to Google Cloud"):
        steps.append({"name": name, "conclusion": "success"})
    for prefix in sc.DEF_STEPS:
        full = prefix + " (long form as in the workflow)"
        if failed:
            steps.append({"name": full, "conclusion": "skipped"})
        elif fail == prefix:
            steps.append({"name": full, "conclusion": "failure"})
            failed = True
        elif skip == prefix:
            steps.append({"name": full, "conclusion": "skipped"})
        else:
            steps.append({"name": full, "conclusion": "success"})
    return [{"name": sc.DEF_JOB, "status": "completed", "conclusion": "failure" if failed else "success", "steps": steps}]


def pkg_jobs(*, pipeline="success", outcome="success"):
    return [{"name": "Gate & detect changed paths", "status": "completed", "conclusion": "success", "steps": []},
            {"name": sc.PKG_JOBS[0], "status": "completed", "conclusion": pipeline, "steps": []},
            {"name": sc.PKG_JOBS[1], "status": "completed", "conclusion": outcome, "steps": []}]


def view_entry(job="gochara-verification-job", typ="cloud_run_job"):
    return {"insertId": "x", "resource": {"type": typ, "labels": {"job_name": job, "project_id": "madhav-astrology"}}, "jsonPayload": {"message": "not retained"}}


GOOD_VIEW = [view_entry(), view_entry(), view_entry()]


class FakeGh:
    """The delegated gh login: answers only what the controller's allow-list lets it ask, from fixture state; records every call."""

    def __init__(self, head):
        self.head, self.tip, self.login = head, head, APPROVER
        self.runs = {sc.CI_WORKFLOW: [run_row(100, head, event="push")], sc.DEF_WORKFLOW: [run_row(9001, head)], sc.PKG_WORKFLOW: []}
        self.jobs = {9001: def_jobs()}
        self.calls, self.dispatched = [], []
        self.next_id, self.appear, self.dispatch_rc, self.no_filter = 9100, True, 0, False

    def __call__(self, argv):
        self.calls.append(list(argv))
        assert sc.gh_allowed(argv), f"gh call off the allow-list: {argv}"
        done = lambda doc: subprocess.CompletedProcess(argv, 0, json.dumps(doc), "")          # noqa: E731
        if argv[0] == "workflow":
            self.dispatched.append(list(argv))
            if self.dispatch_rc:
                return subprocess.CompletedProcess(argv, self.dispatch_rc, "", "denied")
            if self.appear:
                wf = argv[2]
                self.runs[wf].append(run_row(self.next_id, self.head, status="queued", created="2026-10-22T10:00:00Z"))
                self.jobs[self.next_id] = []
                self.next_id += 1
            return subprocess.CompletedProcess(argv, 0, "", "")
        path = argv[3]
        if path == "user":
            return done({"login": self.login})
        if path.endswith("git/ref/heads/main"):
            return done({"ref": "refs/heads/main", "object": {"sha": self.tip}})
        m = re.search(r"workflows/([\w.-]+)/runs\?head_sha=([0-9a-f]{40})", path)
        if m:
            rows = [r for r in self.runs[m.group(1)] if self.no_filter or r["head_sha"] == m.group(2)]
            return done({"total_count": len(rows), "workflow_runs": rows})
        m = re.search(r"actions/runs/(\d+)/jobs", path)
        jobs = self.jobs.get(int(m.group(1)), [])
        return done({"total_count": len(jobs), "jobs": jobs})

    def complete(self, wf, rid, conclusion, jobs):
        row = next(r for r in self.runs[wf] if r["id"] == rid)
        row.update(status="completed", conclusion=conclusion)
        self.jobs[rid] = jobs

    def writes(self):
        return [c for c in self.calls if c[0] == "workflow"]


class World:
    """A disposable cockpit: a git repo whose main holds the head, adopted file, aggregate, retained brief + compact + envelope, executor receipts, output dir, PAGES.log."""

    def __init__(self, root: Path, *, windows=1000, numbered=400, inconclusive=5, g6=True, brief_gate_shift=0, head_on_main=True, grain_commit=None,
                 drop_class=False, grain_status="VERIFIED", attestation="PASSED", live_extra=0, with_brief=True, env_run=RUN, env_attempt=ATT, brief_producer_head=None,
                 quiescence=None, verification=True, candidate_violations=(), logview="ok"):
        self.root = root
        self.ops, self.out, self.pages = root / "ops", root / "out", root / "fast" / "PAGES.log"
        (self.ops / "receipts").mkdir(parents=True)
        (self.ops / "acceptance").mkdir()
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "f").write_text("1")
        git(self.repo, "add", "f")
        git(self.repo, "commit", "-q", "-m", "one")
        main_head = git(self.repo, "rev-parse", "HEAD")
        if head_on_main:
            self.head = main_head
        else:
            git(self.repo, "checkout", "-q", "-b", "side")
            (self.repo / "f").write_text("2")
            git(self.repo, "commit", "-q", "-am", "side")
            self.head = git(self.repo, "rev-parse", "HEAD")
            git(self.repo, "checkout", "-q", "main")
        self.windows, self.numbered, self.inconclusive = windows, numbered, inconclusive
        blank = windows - numbered
        honest = [{"path_id": "P1", "group": "categorical_factor_unmapped", "reason": "value_mapping_undeclared", "windows": blank - inconclusive}]
        if inconclusive:
            honest.append({"path_id": "P2", "group": "other_named_reason", "reason": sc.INCONCLUSIVE_REASON, "windows": inconclusive})
        self.honest = [h for h in honest if h["windows"]]
        gate = {"schema": "numerical_window_gate/1", "status": "PASSED", "policy": sc.POLICY, "table": TABLE, "problems": [], "windows": windows, "numbered_windows": numbered,
                "blank_windows": blank, "honest_nulls": self.honest, "grains": len(CLASSES)}
        self.aggregate = root / "aggregate.json"
        agg = dict(gate)
        if g6:
            agg["g6"] = {"status": "PASSED"}
        self.aggregate.write_text(json.dumps(agg))
        # the retained brief (real check script must accept it)
        bw = windows + brief_gate_shift
        # SR-OD1 S3 / R-6: the brief's gate also carries the blank windows per GRAIN and the windows the verifier demoted (the INCONCLUSIVE ones), and each persisted
        # attestation carries its own demoted counts; the real check script refuses a brief without them or whose counts disagree with the summary.
        demoted_by_reason = {sc.INCONCLUSIVE_REASON: inconclusive} if inconclusive else {}
        honest_brief = [dict(h, windows=h["windows"] + (brief_gate_shift if i == 0 else 0)) for i, h in enumerate(self.honest)]
        by_grain = [{"event_class": "bereavement", "path_id": h["path_id"], "rule_version": "v1", "reason": h["reason"], "group": h["group"], "windows": h["windows"]}
                    for h in honest_brief]
        payload = {"schema": "seal_approval_payload/1", "chart_id": CHART, "generation": GEN, "manifest": {"manifest_id": "m-1", "status": "candidate"},
                   "candidate_gate": {"violations": list(candidate_violations)}, "result_policy": sc.POLICY, "code": {"sealing_commit": self.head},
                   "classes": [{"event_class": "bereavement", "grains": [{"status": "VERIFIED", "path_id": "P1", "rule_version": "v1"}]}],
                   "attestations": {"ka_gochara_eval_window_verification": [json.dumps({"runner_identity": {"numerical_window_gate": {
                       "status": "PASSED", "table": TABLE, "windows": bw, "numbered": numbered, "demoted": demoted_by_reason}}})]},
                   "qualification_table": {"bound": TABLE, "implemented": TABLE, "agrees": True},
                   "numerical_window_gate": {**{k: v for k, v in gate.items() if k != "grains"}, "windows": bw, "blank_windows": bw - numbered,
                                             "honest_nulls": honest_brief, "honest_nulls_by_grain": by_grain, "demoted_windows": inconclusive,
                                             "demoted_by_reason": demoted_by_reason}}
        self.raw = chk.canon(payload).encode("utf-8")
        self.brief, self.compact, self.envelope = root / "brief.json", root / "compact.json", root / "envelope.json"
        self.history, self.run_file = root / "approvals.json", root / "seal_run.json"
        self.digest = sha(self.raw)
        producer_head = brief_producer_head or self.head
        if with_brief:
            self.brief.write_bytes(self.raw)
            self.compact.write_text(json.dumps({"brief_bytes": len(self.raw), "brief_chunks": True, "brief_file": "brief.json", "contract_version": "seal_brief_transport/1",
                                                "persisted": {"brief_id": 11, "manifest_id": "m-1", "state_digest": "c" * 64},
                                                "producer": {"commit": producer_head, "execution_id": "exec-1", "image_digest": "sha256:" + "d" * 64}, "sha256": self.digest,
                                                "status": "BRIEFED"}))
            verified = {"execution": "exec-1", "image_digest": "sha256:" + "d" * 64, "service_account": exe.VERIFIER_SERVICE_ACCOUNT, "runner_commit": self.head,
                        "args": ["--chart", CHART, "--generation", GEN, "--final-rules", "--brief", "--sealing-commit", self.head]}
            self.envelope.write_text(json.dumps(exe.build_envelope(verified, run_id=str(env_run), attempt=str(env_attempt), sealing_commit=self.head, brief_digest=self.digest,
                                                                   brief_id=11, producer_execution_id="exec-1"), sort_keys=True))
        self.cfg = {"chart_id": CHART, "generation": GEN, "head": self.head, "verification_operation_id": VERIF_OP, "aggregate_file": str(self.aggregate),
                    "expected_classes": CLASSES, "repo": str(self.repo), "approval_history_file": str(self.history), "seal_run_file": str(self.run_file)}
        if with_brief:
            self.cfg.update(brief_run={"run_id": RUN, "attempt": ATT}, brief_file=str(self.brief), compact_file=str(self.compact), envelope_file=str(self.envelope))
            self.proof = root / "logview_proof.json"
            if logview is not None:
                self.write_proof(**({} if logview == "ok" else logview))
                self.cfg["logview_proof_file"] = str(self.proof)
        if quiescence is not None:
            self.cfg["quiescence_operation_id"] = "q-op"
            doc = {"schema": "ky.mechanical_quiescence/1", "by": "executor-mechanical", "operation_id": "q-op", "result": "ACCEPTED", "checks": quiescence, "reviewed_commit": self.head,
                   "ts": "2026-10-22T01:00:00Z"}
            (self.ops / "acceptance" / "q-op.quiescence.json").write_text(json.dumps(doc))
        self.write_cfg()
        self.gh = FakeGh(self.head)
        if verification:
            self.receipt(VERIF_OP, "verification_job", "COMPLETED", 0, "ok\n", self.head)
        # the live grain readback
        classes = CLASSES[:-1] if drop_class else CLASSES
        per, rem = divmod(windows, len(CLASSES))
        rows = []
        for i, c in enumerate(classes):
            commit = grain_commit if (grain_commit and i == 3) else self.head
            stat = grain_status if i == 5 else "VERIFIED"
            att = attestation if i == 5 else "PASSED"
            n = per + (rem if i == 0 else 0) + (live_extra if i == 1 else 0)
            rows.append(f"{c}\tP1\tv1\t{stat}\t{sc.POLICY}\t{n}\t{commit}\t{att}")
        self.rows = rows
        if drop_class:                                                       # the dropped class's windows vanish from the live sums as well, as a surviving-rows report would
            pass
        self.answer(sc.op_id("seal-controller-grains", self.cfg), "\t".join(sc.GRAIN_HEADER) + "\n" + "\n".join(rows) + "\n")

    # -- fixture plumbing
    def write_proof(self, *, probe=None, execution=None, run=RUN, attempt=ATT):
        doc = lvp_real.build({"probe": GOOD_VIEW if probe is None else probe, "execution": GOOD_VIEW if execution is None else execution}, run_id=run, attempt=attempt, execution="gochara-verification-job-7bwpr")
        self.proof.write_text(json.dumps(doc))
        return doc

    def write_cfg(self):
        (self.root / "ADOPTED.json").write_text(json.dumps(self.cfg))

    def receipt(self, op, kind, status, exit_code, output, commit):
        body = output.encode()
        (self.ops / "receipts" / f"{op}.output.txt").write_bytes(body)
        (self.ops / "receipts" / f"{op}.json").write_text(json.dumps({"operation_id": op, "kind": kind, "status": status, "exit_code": exit_code, "ts": "2026-10-22T01:00:00+00:00",
                                                                      "reviewed_commit": commit, "output_sha256": sha(body)}))

    def answer(self, op, text, status="COMPLETED", code=0):
        self.receipt(op, "readback_sql", status, code, text, self.head)

    def answer_latest_request(self, text, status="COMPLETED", code=0):
        """What the executor does: take the controller's newest request document and answer it."""
        reqs = sorted((self.out / "readback" / "requests").glob("seal-controller-final-*.json"), key=lambda p: p.stat().st_mtime_ns)
        op = json.loads(reqs[-1].read_text())["operation_id"]
        self.answer(op, text, status, code)
        return op

    def approve(self, *, run=RUN, attempt=ATT, login=APPROVER, digest=None, state="approved", brief_id=11):
        line = sc.APPROVAL_LINE.format(digest=digest or self.digest, run=run, attempt=attempt, brief_id=brief_id)
        self.history.write_text(json.dumps([{"state": state, "comment": line, "user": {"login": login}, "environments": [{"name": sc.ENVIRONMENT}]}]))

    def seal_row(self, *, digest=None, run=RUN, attempt=ATT, pub="published", seals=1, receipts=True):
        r = f"{digest or self.digest}:{run}:{attempt}" if receipts else ""
        return "\t".join(sc.SEAL_HEADER) + f"\n{pub}\t{seals}\t{r}\n"

    def run(self, **kw):
        kw.setdefault("gh", self.gh)
        kw.setdefault("now", NOW)
        return sc.run(self.root / "ADOPTED.json", self.ops, self.out, self.pages, scripts_override=str(SCRIPTS), python=sys.executable, main_ref="main", **kw)

    def pages_lines(self, tag=None):
        if not self.pages.exists():
            return []
        return [ln for ln in self.pages.read_text().splitlines() if f"PAGE {tag}" in ln] if tag else self.pages.read_text().splitlines()

    def to_approval_requested(self):
        st = self.run()
        assert st["stage"] == "APPROVAL_REQUESTED" and st["kind"] == sc.AWAITING_APPROVAL, st
        return st


@pytest.fixture
def w(tmp_path):
    return lambda **kw: World(tmp_path, **kw)


def not_passed(world, st, kind, stage=None):
    assert st["state"] == sc.NOT_READY and st["kind"] == kind, st
    if stage:
        assert st["stage"] == stage, st
    assert world.pages_lines("SEAL-APPROVAL-REQUESTED") == []


# ── A: the aggregate ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a1_numbers_on_candidate_reaches_approval_requested_never_all_null_refusal(w):
    world = w()                                                        # inconclusive 5 of 1000 = exactly the 0.5 % cap
    st = world.run()
    assert st["stage"] == "APPROVAL_REQUESTED" and st["kind"] == sc.AWAITING_APPROVAL, st
    assert "all_null" not in json.dumps(st)
    assert len(world.pages_lines("SEAL-APPROVAL-REQUESTED")) == 1


def test_a2_universe_is_the_adopted_26_not_the_surviving_rows(w):
    world = w(drop_class=True)
    st = world.run()
    not_passed(world, st, sc.REFUSED, "START")
    assert "class_25" in st["reason"] and "missing" in st["reason"]


def test_a3_mixed_head_never_aggregates(w):
    world = w(grain_commit="b" * 40)
    st = world.run()
    not_passed(world, st, sc.REFUSED, "START")
    assert "mixed or foreign head" in st["reason"]


def test_a4_aggregate_without_passed_g6_is_not_passed(w):
    world = w(g6=False)
    st = world.run()
    not_passed(world, st, sc.NOT_PASSED, "START")
    assert "G-6" in st["reason"]


def test_a5_live_sums_must_equal_the_aggregate(w):
    world = w(live_extra=1)
    not_passed(world, world.run(), sc.DISAGREEMENT, "START")


def test_a6_every_grain_verified_and_attested(w):
    world = w(attestation="FAILED")
    st = world.run()
    not_passed(world, st, sc.REFUSED, "START")
    assert "not VERIFIED/PASSED" in st["reason"]


def test_a7_inconclusive_over_cap_is_not_passed(w):
    world = w(inconclusive=6)                                           # 6 of 1000 = 0.6 % > 0.5 %
    not_passed(world, world.run(), sc.OVER_CAP, "START")


def test_a8_no_grain_readback_requests_one_and_passes_nothing(w, tmp_path):
    world = w()
    (world.ops / "receipts" / f"{sc.op_id('seal-controller-grains', world.cfg)}.json").unlink()
    st = world.run()
    not_passed(world, st, sc.AWAITING_READBACK, "START")
    op = sc.op_id("seal-controller-grains", world.cfg)
    req = json.loads((world.out / "readback" / "requests" / f"{op}.json").read_text())
    sql = (world.out / "readback" / "sql" / f"{op}.sql").read_text()
    assert req["kind"] == "readback_sql" and req["sql_sha256"] == sha(sql.encode()) and sql.lstrip().upper().startswith("SELECT")


# ── B: the main-produced brief ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_b1_no_brief_prepares_the_dispatch_command_and_pages_once(w):
    world = w(with_brief=False)
    st = world.run()
    assert st["kind"] == sc.AWAITING_BRIEF and st["stage"] == "REDEPLOY", st
    world.run()
    pages = world.pages_lines("SEAL-BRIEF-DISPATCH")
    assert len(pages) == 1
    text = (world.out / "BRIEF_DISPATCH.txt").read_text()
    assert f"gh workflow run {sc.WORKFLOW}" in text and f"-f confirm={sc.CONFIRM}" in text and world.head in text


def test_b2_brief_the_reviewed_check_refuses_is_refused(w):
    world = w(candidate_violations=[{"violation": "x"}])                # internally consistent (digest, envelope) but the candidate gate has a violation: only the check sees it
    st = world.run()
    not_passed(world, st, sc.REFUSED, "REDEPLOY")
    assert "seal brief check exit 2" in st["reason"]


def test_b3_head_not_on_main_is_refused(w):
    world = w(head_on_main=False)
    st = world.run()
    not_passed(world, st, sc.REFUSED, "REDEPLOY")
    assert "not main-produced" in st["reason"]


def test_b4_envelope_of_another_run_is_refused(w):
    world = w(env_run=RUN + 1)
    st = world.run()
    not_passed(world, st, sc.REFUSED, "REDEPLOY")
    assert "envelope" in st["reason"]


def test_b5_brief_verdict_must_equal_the_aggregate(w):
    world = w(brief_gate_shift=2)
    st = world.run()
    not_passed(world, st, sc.DISAGREEMENT, "REDEPLOY")


def test_b6_brief_produced_for_another_head_is_stale(w):
    world = w(brief_producer_head="b" * 40)
    not_passed(world, world.run(), sc.STALE_HEAD, "REDEPLOY")


# ── C: the approval preparation ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_c1_approval_prepared_once_with_exact_comment_and_nothing_new_on_rerun(w):
    world = w()
    world.to_approval_requested()
    before = (world.out / "markers").glob("*")
    snapshot = sorted(p.name for p in before)
    world.pages.write_text(world.pages.read_text())
    st2 = world.run()
    assert st2["approval_emission"] == "already_paged"
    assert sorted(p.name for p in (world.out / "markers").glob("*")) == snapshot
    assert len(world.pages_lines("SEAL-APPROVAL-REQUESTED")) == 1
    bdir = next((world.out / "approval" / GEN).iterdir())
    bundle = json.loads((bdir / "APPROVAL_BUNDLE.json").read_text())
    line = sc.APPROVAL_LINE.format(digest=world.digest, run=RUN, attempt=ATT, brief_id=11)
    assert bundle["approval_comment"] == line and bundle["verdict"]["classes"] == 26
    cmd = (bdir / "APPROVE_COMMAND.txt").read_text()
    assert line in cmd and f"actions/runs/{RUN}/pending_deployments" in cmd and "state=approved" in cmd and APPROVER in cmd
    assert line in (world.out / "SURROGATE_MESSAGE.txt").read_text()
    assert "NOT MEASURED" in bundle["evidence"]["quiescence_note"]                 # an unmeasured quiescence is never reported as measured


def test_c1b_page_log_rotated_away_does_not_repage_the_same_marker(w):
    world = w()
    world.to_approval_requested()
    world.pages.unlink()
    world.run()
    assert world.pages_lines("SEAL-APPROVAL-REQUESTED") == []                      # the marker is the authority: exactly once per key, never repaged


def test_c2_page_failure_leaves_no_marker_and_a_later_run_repairs_with_one_page(w):
    world = w()
    world.pages.mkdir(parents=True)                                                # appending to a directory fails: the page cannot be written
    with pytest.raises(OSError):
        world.run()
    assert not list((world.out / "markers").glob("APPROVAL_REQUESTED*"))
    world.pages.rmdir()
    world.to_approval_requested()
    world.run()
    assert len(world.pages_lines("SEAL-APPROVAL-REQUESTED")) == 1


def test_c3_quiescence_not_accepted_prepares_no_approval(w):
    world = w(quiescence={"remote_execution_terminal": False, "no_live_session_carries_the_marker": True})
    st = world.run()
    not_passed(world, st, sc.NOT_PASSED, "BRIEF")
    assert "remote_execution_terminal" in st["reason"] and not (world.out / "approval").exists()


def test_c3b_quiescence_accepted_is_recorded_in_the_bundle(w):
    world = w(quiescence={"remote_execution_terminal": True})
    world.to_approval_requested()
    bundle = json.loads(next((world.out / "approval" / GEN).iterdir()).joinpath("APPROVAL_BUNDLE.json").read_text())
    assert bundle["evidence"]["quiescence"]["operation_id"] == "q-op" and bundle["evidence"]["quiescence_note"] == "measured and ACCEPTED"


def test_c4_brief_changed_after_preparation_is_refused_not_reapproved(w):
    world = w()
    world.to_approval_requested()
    bundle_path = next((world.out / "approval" / GEN).iterdir()) / "APPROVAL_BUNDLE.json"
    doc = json.loads(bundle_path.read_text())
    doc["brief_digest"] = "e" * 64                                                  # what was prepared names another brief than the one now retained
    bundle_path.write_text(json.dumps(doc))
    st = world.run()
    assert st["kind"] == sc.REFUSED and "start a fresh run" in st["reason"], st


def test_c5_the_controller_itself_runs_only_python_and_git_and_gh_only_through_the_allow_list(w, monkeypatch):
    world = w()
    seen = []
    real = subprocess.run

    def spy(argv, *a, **k):
        seen.append(Path(argv[0]).name)
        return real(argv, *a, **k)

    monkeypatch.setattr(sc.subprocess, "run", spy)
    world.run()
    world.approve()
    world.run()
    assert seen and set(seen) <= {"git", Path(sys.executable).name}, seen             # gh is only ever called through the injected runner
    assert world.gh.calls and all(sc.gh_allowed(c) for c in world.gh.calls)
    src = (HERE.parent / "seal_controller.py").read_text()
    assert not re.search(r"subprocess\.\w+\(\s*\[\s*[\"'](gcloud|claude|codex)[\"']", src)
    assert len(re.findall(r"subprocess\.\w+\(\s*\[\s*[\"']gh[\"']", src)) == 1       # the one default runner; every other gh call goes through gh_allowed


# ── D: approval and sealer ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_d1_valid_approval_by_the_reviewer_requests_the_seal_readback(w):
    world = w()
    world.to_approval_requested()
    world.approve()
    st = world.run()
    assert st["stage"] == "APPROVED" and st["kind"] == sc.AWAITING_READBACK, st
    assert list((world.out / "readback" / "requests").glob("seal-controller-final-*.json"))


def test_d2_approval_of_another_run_or_attempt_is_never_reused(w):
    world = w()
    world.to_approval_requested()
    world.approve(attempt=ATT + 1)
    st = world.run()
    assert st["kind"] == sc.REFUSED and st["stage"] == "APPROVAL_REQUESTED", st


def test_d3_approval_by_another_principal_is_refused(w):
    world = w()
    world.to_approval_requested()
    world.approve(login="some-builder")
    st = world.run()
    assert st["kind"] == sc.REFUSED and "required reviewer" in st["reason"], st


def test_d4_cancelled_sealer_run_with_nothing_sealed_needs_a_fresh_run_paged_once(w):
    world = w()
    world.to_approval_requested()
    world.approve()
    world.run()
    world.run_file.write_text(json.dumps({"run_id": RUN, "run_attempt": ATT, "status": "completed", "conclusion": "cancelled"}))
    world.run()                                                                     # new run record => a new readback request
    world.answer_latest_request(world.seal_row(pub="candidate", seals=0, receipts=False))
    st = world.run()
    assert st["kind"] == sc.RETRY_NEEDED and "FRESH run" in st["reason"], st
    world.run()
    assert len(world.pages_lines("SEAL-RETRY-NEEDED")) == 1


# ── E: the independent readback ──────────────────────────────────────────────────────────────────────────────────────────────────

def _to_final_request(world):
    world.to_approval_requested()
    world.approve()
    assert world.run()["kind"] == sc.AWAITING_READBACK


def test_e1_sealed_needs_the_receipt_of_this_runs_digest_then_one_page(w):
    world = w()
    _to_final_request(world)
    world.answer_latest_request(world.seal_row())
    st = world.run()
    assert st["state"] == sc.READY and st["kind"] == sc.SEALED and st["stage"] == "SEALED", st
    world.run()
    assert len(world.pages_lines("SEAL-SEALED")) == 1 and (world.out / "SEALED.json").exists()


def test_e2_inconsistent_halts_and_the_next_poll_does_nothing_else(w):
    world = w()
    _to_final_request(world)
    world.answer_latest_request(world.seal_row(digest="f" * 64))                    # sealed with a receipt of another digest
    st = world.run()
    assert st["kind"] == sc.HALTED and "INCONSISTENT" in st["reason"], st
    def files():
        return sorted(str(p.relative_to(world.out)) for p in world.out.rglob("*") if p.is_file() and p.name != "SEAL_CONTROLLER_STATUS.json")
    before = (world.pages.read_text(), files())
    st2 = world.run()
    assert st2["kind"] == sc.HALTED and "STOPPED" in st2["reason"]
    assert (world.pages.read_text(), files()) == before, "no emission, request or page after a halt"
    assert len(world.pages_lines("SEAL-HALT")) == 1


def test_e3_unreadable_outcome_is_unknown_never_not_sealed(w):
    world = w()
    _to_final_request(world)
    world.answer_latest_request("", status="FAILED", code=1)
    st = world.run()
    assert st["kind"] == sc.HALTED and "UNREADABLE" in st["reason"], st
    assert len(world.pages_lines("SEAL-HALT")) == 1


def test_e4_successful_sealer_run_with_nothing_sealed_halts(w):
    world = w()
    _to_final_request(world)
    world.run_file.write_text(json.dumps({"run_id": RUN, "run_attempt": ATT, "status": "completed", "conclusion": "success"}))
    world.run()
    world.answer_latest_request(world.seal_row(pub="candidate", seals=0, receipts=False))
    st = world.run()
    assert st["kind"] == sc.HALTED and "nothing sealed" in st["reason"], st


def test_e5_not_yet_sealed_while_the_run_is_pending_waits(w):
    world = w()
    _to_final_request(world)
    world.answer_latest_request(world.seal_row(pub="candidate", seals=0, receipts=False))
    st = world.run()
    assert st["kind"] == sc.AWAITING_SEAL and world.pages_lines("SEAL-HALT") == [] and world.pages_lines("SEAL-RETRY-NEEDED") == [], st


# ── R: owner step 11 — the checking job redeployed at the sealing version (A11 item 9) ────────────────────────────────────────────

def digest_failed(world, rid=9001, created="2026-10-22T09:00:00Z"):
    """The only definition run at the head failed at the digest step: no pipeline image exists for the sealing commit."""
    world.gh.runs[sc.DEF_WORKFLOW] = [run_row(rid, world.head, conclusion="failure", created=created)]
    world.gh.jobs[rid] = def_jobs(fail=sc.DEF_STEPS[0])


def no_definition(world):
    world.gh.runs[sc.DEF_WORKFLOW] = []


def test_r1_done_is_a_success_run_at_the_head_whose_job_and_named_steps_read_back_then_one_page_and_the_bundle_carries_it(w):
    world = w()
    st = world.run()
    assert st["stage"] == "APPROVAL_REQUESTED" and st["kind"] == sc.AWAITING_APPROVAL, st
    assert len(world.pages_lines("SEAL-REDEPLOY-DONE")) == 1 and "reread_step8_permission=required" in world.pages_lines("SEAL-REDEPLOY-DONE")[0]
    ev = json.loads((world.out / "REDEPLOY.json").read_text())["evidence"]["definition"]
    assert ev["run_id"] == 9001 and ev["job_conclusion"] == "success" and set(ev["steps"]) == set(sc.DEF_STEPS) and set(ev["steps"].values()) == {"success"}
    bundle = json.loads(next((world.out / "approval").rglob("APPROVAL_BUNDLE.json")).read_text())
    assert bundle["evidence"]["redeploy"]["definition"]["run_id"] == 9001
    world.run()
    assert len(world.pages_lines("SEAL-REDEPLOY-DONE")) == 1 and world.gh.writes() == []        # evidence found => nothing is dispatched, the page is not repeated


@pytest.mark.parametrize("skipped_step", [sc.DEF_STEPS[2], sc.DEF_STEPS[3]])
def test_r2_a_success_run_whose_readback_or_preflight_did_not_read_back_is_not_accepted(w, skipped_step):
    world = w()
    world.gh.jobs[9001] = def_jobs(skip=skipped_step)                                      # the run itself concluded `success`
    st = world.run()
    not_passed(world, st, sc.NOT_PASSED, "AGGREGATE")
    assert skipped_step in st["reason"] and world.gh.writes() == [] and world.pages_lines("SEAL-REDEPLOY-DONE") == []


def test_r3_main_moved_stales_step_11_and_nothing_is_dispatched(w):
    world = w()
    no_definition(world)
    world.gh.tip = "b" * 40
    st = world.run(execute_redeploy=True)
    not_passed(world, st, sc.STALE_HEAD, "AGGREGATE")
    assert "main moved" in st["reason"] and world.gh.writes() == []


def test_r3b_a_finished_redeploy_is_stale_when_main_moves_before_the_brief_but_not_after(tmp_path):
    before = World(tmp_path / "a", with_brief=False)
    before.gh.tip = "b" * 40
    not_passed(before, before.run(), sc.STALE_HEAD, "AGGREGATE")
    after = World(tmp_path / "b")                                                          # the brief is produced: later merges no longer stale the seal chain
    after.gh.tip = "b" * 40
    assert after.run()["stage"] == "APPROVAL_REQUESTED"


@pytest.mark.parametrize("ci,kind", [([], sc.NOT_PASSED), ([("failure", "completed", "2026-10-22T08:00:00Z")], sc.NOT_PASSED),
                                     ([("success", "completed", "2026-10-22T08:00:00Z"), (None, "in_progress", "2026-10-22T08:30:00Z")], sc.AWAITING_CI)])
def test_r4_ci_not_green_at_the_head_dispatches_nothing(w, ci, kind):
    world = w()
    no_definition(world)
    world.gh.runs[sc.CI_WORKFLOW] = [run_row(200 + i, world.head, status=stt, conclusion=c, event="push", created=t) for i, (c, stt, t) in enumerate(ci)]
    st = world.run(execute_redeploy=True)
    not_passed(world, st, kind, "AGGREGATE")
    assert world.gh.writes() == []


def test_r5_without_the_execute_flag_the_dispatch_is_prepared_and_paged_once_and_nothing_is_written_to_github(w):
    world = w()
    no_definition(world)
    st = world.run()
    assert st["kind"] == sc.AWAITING_REDEPLOY and st["stage"] == "AGGREGATE", st
    text = (world.out / "REDEPLOY_DISPATCH.txt").read_text()
    assert f"gh workflow run {sc.DEF_WORKFLOW} --repo {sc.REPO_SLUG} --ref main -f confirm=DEFINE-GOCHARA-VERIFICATION-JOB" in text
    world.run()
    assert len(world.pages_lines("SEAL-REDEPLOY-DISPATCH-NEEDED")) == 1 and world.gh.writes() == []


def test_r6_execute_dispatches_the_definition_exactly_once_and_advances_on_the_read_back(w):
    world = w()
    no_definition(world)
    world.gh.appear = False                                                                # the run is not visible yet
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.AWAITING_REDEPLOY and world.gh.writes() == [sc.def_dispatch_argv()], st
    assert len(world.pages_lines("SEAL-REDEPLOY-DISPATCHED")) == 1
    world.run(execute_redeploy=True)
    assert world.gh.writes() == [sc.def_dispatch_argv()], "a dispatch that is not visible yet must not be repeated"
    world.gh.runs[sc.DEF_WORKFLOW].append(run_row(9100, world.head, status="in_progress", created="2026-10-22T10:00:30Z"))
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.AWAITING_REDEPLOY and "9100" in st["reason"] and len(world.gh.writes()) == 1
    world.gh.complete(sc.DEF_WORKFLOW, 9100, "success", def_jobs())
    st = world.run(execute_redeploy=True)
    assert st["stage"] == "APPROVAL_REQUESTED" and len(world.gh.writes()) == 1
    assert len(world.pages_lines("SEAL-REDEPLOY-DONE")) == 1


def test_r7_a_gh_login_other_than_the_delegated_one_dispatches_nothing(w):
    world = w()
    no_definition(world)
    world.gh.login = "someone-else"
    st = world.run(execute_redeploy=True)
    not_passed(world, st, sc.REFUSED, "AGGREGATE")
    assert world.gh.writes() == [] and not list((world.out / "markers").glob("REDEPLOY_*"))


def test_r8_no_pipeline_image_builds_the_package_with_the_ci_gate_then_defines_again(w):
    world = w()
    digest_failed(world)
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.AWAITING_REDEPLOY and world.gh.writes() == [sc.pkg_dispatch_argv()], st
    argv = world.gh.writes()[0]
    assert "ci_gate=require-ci-green" in argv and not any("EMERGENCY" in x or "OVERRIDE" in x.upper() for x in argv)
    world.run(execute_redeploy=True)
    assert len(world.gh.writes()) == 1, "the package build is dispatched once"
    world.gh.complete(sc.PKG_WORKFLOW, 9100, "success", pkg_jobs())
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.AWAITING_REDEPLOY and world.gh.writes() == [sc.pkg_dispatch_argv(), sc.def_dispatch_argv()], st
    world.gh.complete(sc.DEF_WORKFLOW, 9101, "success", def_jobs())
    st = world.run(execute_redeploy=True)
    assert st["stage"] == "APPROVAL_REQUESTED", st
    ev = json.loads((world.out / "REDEPLOY.json").read_text())["evidence"]
    assert ev["definition"]["run_id"] == 9101 and ev["package"]["run_id"] == 9100 and ev["package"]["jobs"][sc.PKG_JOBS[0]] == "success"


def test_r8b_a_second_digest_failure_after_the_package_build_halts(w):
    world = w()
    digest_failed(world)
    world.run(execute_redeploy=True)
    world.gh.complete(sc.PKG_WORKFLOW, 9100, "success", pkg_jobs())
    world.run(execute_redeploy=True)
    world.gh.complete(sc.DEF_WORKFLOW, 9101, "failure", def_jobs(fail=sc.DEF_STEPS[0]))
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.HALTED and len(world.gh.writes()) == 2, st
    assert len(world.pages_lines("SEAL-HALT")) == 1 and (world.out / "markers" / f"HALT.{GEN}.{world.head}").exists()
    world.run(execute_redeploy=True)
    assert len(world.gh.writes()) == 2 and len(world.pages_lines("SEAL-HALT")) == 1


def test_r8c_the_definition_is_dispatched_at_most_twice_per_key_even_after_a_person_rebuilds_the_package(w):
    world = w()
    digest_failed(world)
    world.run(execute_redeploy=True)                                                       # package build (9100)
    world.gh.complete(sc.PKG_WORKFLOW, 9100, "success", pkg_jobs())
    world.run(execute_redeploy=True)                                                       # definition #1 (9101)
    world.gh.complete(sc.DEF_WORKFLOW, 9101, "failure", def_jobs(fail=sc.DEF_STEPS[0]))
    world.gh.runs[sc.PKG_WORKFLOW].append(run_row(9200, world.head, created="2026-10-22T10:30:00Z"))      # a person rebuilt the package by hand
    world.gh.jobs[9200] = pkg_jobs()
    world.run(execute_redeploy=True)                                                       # definition #2 (9102)
    world.gh.complete(sc.DEF_WORKFLOW, 9102, "failure", def_jobs(fail=sc.DEF_STEPS[0]))
    world.gh.runs[sc.PKG_WORKFLOW].append(run_row(9201, world.head, created="2026-10-22T10:45:00Z"))
    world.gh.jobs[9201] = pkg_jobs()
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.HALTED and "twice" in st["reason"] and len(world.gh.writes()) == 3, st.get("reason")


def test_r9a_a_definition_failing_after_the_digest_step_halts_and_is_never_retried(w):
    world = w()
    world.gh.runs[sc.DEF_WORKFLOW] = [run_row(9001, world.head, conclusion="failure")]
    world.gh.jobs[9001] = def_jobs(fail=sc.DEF_STEPS[1])
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.HALTED and world.gh.writes() == [] and len(world.pages_lines("SEAL-HALT")) == 1, st


@pytest.mark.parametrize("pkg_conclusion,jobs", [("failure", pkg_jobs(pipeline="failure", outcome="failure")), ("success", pkg_jobs(pipeline="skipped"))])
def test_r9b_a_failed_or_image_less_package_run_halts(w, pkg_conclusion, jobs):
    world = w()
    digest_failed(world)
    world.gh.runs[sc.PKG_WORKFLOW] = [run_row(9050, world.head, conclusion=pkg_conclusion, created="2026-10-22T09:30:00Z")]
    world.gh.jobs[9050] = jobs
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.HALTED and world.gh.writes() == [] and len(world.pages_lines("SEAL-HALT")) == 1, st


def test_r9c_a_dispatch_whose_run_never_appears_waits_then_halts_after_twenty_minutes(w):
    import datetime
    world = w()
    no_definition(world)
    world.gh.appear = False
    world.run(execute_redeploy=True)
    st = world.run(execute_redeploy=True, now=NOW + datetime.timedelta(minutes=5))
    assert st["kind"] == sc.AWAITING_REDEPLOY and len(world.gh.writes()) == 1
    st = world.run(execute_redeploy=True, now=NOW + datetime.timedelta(minutes=25))
    assert st["kind"] == sc.HALTED and len(world.gh.writes()) == 1 and len(world.pages_lines("SEAL-HALT")) == 1, st


def test_r9d_a_dispatch_that_gh_refuses_leaves_no_marker_and_is_not_counted(w):
    world = w()
    no_definition(world)
    world.gh.dispatch_rc = 1
    st = world.run(execute_redeploy=True)
    assert st["kind"] == sc.NO_INPUT and not list((world.out / "markers").glob("REDEPLOY_DEF*")), st
    world.gh.dispatch_rc = 0
    world.run(execute_redeploy=True)
    assert len(world.gh.writes()) == 2 and len(list((world.out / "markers").glob("REDEPLOY_DEF*"))) == 1


def test_r10_the_gh_allow_list_is_reads_and_the_two_dispatches_only():
    slug, head = sc.REPO_SLUG, "a" * 40
    allowed = [["api", "-X", "GET", "user"], ["api", "-X", "GET", f"repos/{slug}/git/ref/heads/main"], sc.def_dispatch_argv(), sc.pkg_dispatch_argv(),
               ["api", "-X", "GET", sc.runs_path("ci.yml", head)], ["api", "-X", "GET", sc.jobs_path(123)]]
    assert all(sc.gh_allowed(a) for a in allowed)
    refused = [["workflow", "run", sc.WORKFLOW, "--repo", slug, "--ref", "main", "-f", f"confirm={sc.CONFIRM}"],                    # the seal / brief workflow
               sc.def_dispatch_argv() + ["-f", "x=y"],
               [x.replace("require-ci-green", "EMERGENCY-OVERRIDE-CI-NOT-GREEN") for x in sc.pkg_dispatch_argv()],                  # the CI-gate override choice
               [x for x in sc.pkg_dispatch_argv() if x != "force_all_services=true"],
               ["api", "-X", "POST", f"repos/{slug}/actions/runs/1/pending_deployments"], ["api", "-X", "GET", f"repos/{slug}/environments/{sc.ENVIRONMENT}"],
               ["api", "-X", "GET", f"repos/{slug}/actions/workflows/ci.yml/runs?head_sha=main&per_page=50"], ["pr", "merge", "1"], ["run", "jobs", "execute"],
               ["workflow", "run", sc.PKG_WORKFLOW, "--repo", "other/repo", "--ref", "main", "-f", "ci_gate=require-ci-green", "-f", "force_all_services=true"]]
    assert not any(sc.gh_allowed(a) for a in refused), [a for a in refused if sc.gh_allowed(a)]
    src = (HERE.parent / "seal_controller.py").read_text()
    assert "EMERGENCY" not in src and sc.CI_GATE == "require-ci-green"


def test_r11_run_evidence_for_another_commit_or_branch_is_never_used(w):
    world = w()
    world.gh.runs[sc.DEF_WORKFLOW] = [run_row(9001, OLD_SHA)]
    world.gh.no_filter = True                                                              # a response about another commit is refused outright
    not_passed(world, world.run(), sc.NO_INPUT, "AGGREGATE")
    world.gh.no_filter = False
    world.gh.runs[sc.DEF_WORKFLOW] = [run_row(9001, world.head, branch="feature/x")]       # a success run from another branch is not the main definition
    st = world.run()
    assert st["kind"] == sc.AWAITING_REDEPLOY and "prepared" in st["reason"] and world.pages_lines("SEAL-REDEPLOY-DONE") == []


def test_r12_the_names_the_controller_reads_exist_in_the_real_workflow_files():
    wf = REPO / ".github" / "workflows"
    d, dep, ci = (wf / sc.DEF_WORKFLOW).read_text(), (wf / sc.PKG_WORKFLOW).read_text(), (wf / sc.CI_WORKFLOW).read_text()
    assert sc.DEF_CONFIRM in d and f"name: {sc.DEF_JOB}" in d and "name: Gochara verification job (definition, reviewed)" in d
    assert re.search(r"on:\s*\n\s*workflow_dispatch:", d)
    for prefix in sc.DEF_STEPS:
        assert re.search(rf"^\s*- name: {re.escape(prefix)}", d, re.M), prefix
    for job in sc.PKG_JOBS:
        assert re.search(rf"^\s*name: {re.escape(job)}\s*$", dep, re.M), job
    assert re.search(r"ci_gate:.*?default: require-ci-green", dep, re.S) and "force_all_services:" in dep and 'workflows: ["CI — Ganga Quality Gate"]' in dep
    assert "name: CI — Ganga Quality Gate" in ci



# ── L: step 10, the positive log-view proof ───────────────────────────────────────────────────────────────────────────────────────

def test_l1_a_proven_view_reaches_approval_requested_and_the_outside_refusal_is_carried_as_null(w):
    world = w()
    world.to_approval_requested()
    bundle = json.loads(next((world.out / "approval").rglob("APPROVAL_BUNDLE.json")).read_text())
    rows = {r["check"]: r for r in bundle["evidence"]["logview"]["rows"]}
    assert rows["view_returns_job_entries"]["result"] is True and rows["view_only_job_entries"]["result"] is True
    assert rows["view_refusal_outside"]["result"] is None                                  # null, never green
    assert "SR-LOGVIEW-NARROW-KEEP" in rows["view_refusal_outside"]["reason"] and "LOGVIEW-NARROW-IAC" in rows["view_refusal_outside"]["reason"]
    msg = (world.out / "SURROGATE_MESSAGE.txt").read_text()
    assert "view_refusal_outside = NULL" in msg and "not green" in msg


def test_l2_no_retained_proof_holds_with_a_named_reason_and_prepares_no_approval(w):
    world = w(logview=None)
    st = world.run()
    not_passed(world, st, sc.HOLD, "BRIEF")
    assert "positive_log_view_proof" in st["reason"] and "no retained proof" in st["reason"]
    assert not (world.out / "approval").exists()


def test_l3_a_non_job_entry_in_the_view_holds_naming_it(w):
    world = w(logview={"probe": GOOD_VIEW + [view_entry(job="some-other-job"), view_entry(typ="gce_instance")]})
    st = world.run()
    not_passed(world, st, sc.HOLD, "BRIEF")
    assert "positive_log_view_proof" in st["reason"] and "view_only_job_entries" in st["reason"] and "some-other-job" in st["reason"]


@pytest.mark.parametrize("kw", [{"probe": []}, {"execution": []}])
def test_l4_an_empty_view_holds(w, kw):
    world = w(logview=kw)
    st = world.run()
    not_passed(world, st, sc.HOLD, "BRIEF")
    assert "view_returns_job_entries" in st["reason"] and "empty view proves nothing" in st["reason"], st


def test_l5_a_proof_that_reports_the_outside_refusal_green_holds(w):
    world = w()
    doc = json.loads(world.proof.read_text())
    doc["rows"][-1]["result"] = True                                                       # a green signal with no detector behind it
    world.proof.write_text(json.dumps(doc))
    st = world.run()
    not_passed(world, st, sc.HOLD, "BRIEF")
    assert "recorded rows differ" in st["reason"], st
    doc["rows"][-1]["result"] = None
    doc["passed"] = False                                                                    # a recorded verdict the rows do not give
    world.proof.write_text(json.dumps(doc))
    assert "recorded verdict differs" in world.run()["reason"]


@pytest.mark.parametrize("kw", [{"run": RUN + 1}, {"attempt": ATT + 1}])
def test_l6_a_proof_of_another_run_or_attempt_is_never_reused(w, kw):
    world = w(logview=kw)
    st = world.run()
    not_passed(world, st, sc.HOLD, "BRIEF")
    assert "not the brief run" in st["reason"], st


# ── P: parity with the reviewed scripts the controller must agree with ─────────────────────────────────────────────────────────────

def test_p1_classify_and_approval_grammar_equal_the_reviewed_scripts():
    d = "a" * 64
    cases = [(["candidate"], 0, [], "NOT_SEALED"), (["published"], 1, [(d, 7, 1)], "SEALED"), (["published"], 1, [("b" * 64, 7, 1)], "INCONSISTENT"),
             (["published"], 0, [], "INCONSISTENT"), ([], 0, [], "INCONSISTENT"), (["candidate", "published"], 1, [(d, 7, 1)], "INCONSISTENT"), (["candidate"], 1, [], "INCONSISTENT")]
    for pub, seals, receipts, want in cases:
        mine = sc.classify(pub, seals, receipts, digest=d, run_id=7, attempt=1)[0]
        theirs = rec.classify(pub[0] if len(pub) == 1 else None, seals, [dict(zip(("brief_digest", "run_id", "run_attempt"), r)) for r in receipts], digest=d, run_id=7, attempt=1)[0]
        assert mine == theirs == want, (pub, seals, receipts)
    line = sc.APPROVAL_LINE.format(digest=d, run=7, attempt=2, brief_id=3)
    assert appr._LINE.fullmatch(line).groups() == (d, "7", "2", "3")
