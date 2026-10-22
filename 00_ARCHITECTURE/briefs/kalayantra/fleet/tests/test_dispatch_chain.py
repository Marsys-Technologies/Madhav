"""Oracles for dispatch_chain.py (A11 items 5 and 7: the automatic chain TR pass -> merge -> image -> equivalence -> rebind/admission -> dispatch -> verification -> seal hand-off).

Fixtures only: no database, no network, no gh / gcloud, no process started by the chain (one test makes `subprocess.run` raise and walks the whole chain).  The REAL reviewed code runs wherever
the chain reads a verdict: `equivalence_record.py compare` produces the decisions from real records, `seal_controller.check_aggregate` judges the aggregate, `seal_controller.load_adopted`
loads the hand-off file.  Executor receipts are written by the fixture from the chain's OWN request documents (request -> receipt route end to end).

Every gate is an oracle FUNCTION `o_*(m, tmp)` taking the module under test; `REVERSIONS` plants ONE reversion per gate (a one-line source edit loaded as a second module) and a meta-test
shows that the gate's oracle FAILS on it (D-OWNER-TESTS-20261016).  Claims (root CLAUDE.md §N.8: each is measured by a detector that can read false):
  S0  a  25/25 true at H arms the TR once; b  one null check holds (N.7.6); c  a file for another head holds; d  a missing check holds; e  the file's `ready` is never trusted
  S1  a  all of G-1..G-7 + RV-INT part 2 + PR still at H -> `gh pr merge --auto` bound to H, once; b  a null gate holds; c  a verdict not bound to this trial_ready holds; d  DIAGNOSTIC is no
      evidence; e  RV-INT not ACCEPTED / other head holds; f  a PR whose head moved is never merged
  S2  a  M not on main holds; b  CI red holds AND no deploy is dispatched; c  the forced deploy is a NEW run (an older dispatch run is not accepted) and is never repeated; d  the deployed image
      must carry M; e  a DIFFERS decision holds with the table's action; f  a decision about other records is recomputed, never reused; g  a main record of another commit holds
  S3  a  executor not refreshed to M holds; b  a rebind of another head / edited staged files / stale pin holds; c  rehearsal flags / a control that admitted its defect / an unadmitted template hold;
      d  all green -> the pack's template is queued byte for byte, once
  S4  a  a dispatch receipt without LAUNCHED evidence holds; b  a RUNNING build holds; c  an execution of another run holds; d  SUCCEEDED -> ALL verification requests in the same poll
  S5  a  a verification receipt of another commit holds; b  an aggregate without PASSED G-6 holds; c  PASSED -> the adopted file is written, loads in the seal controller, one page; d  a file of
      another generation is never overwritten
  X   paging once per reason / only after the stall limit; dry-run writes nothing; gh argv shapes and the forbidden tokens; no process is started by the chain; the action catalogue
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = HERE.parents[4]
SCRIPTS = REPO / "platform" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(FLEET))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


import dispatch_chain as dc  # noqa: E402  (the real module)
import equivalence_record as eqr  # noqa: E402

SRC = Path(os.environ.get("DISPATCH_CHAIN_UNDER_TEST", FLEET / "dispatch_chain.py"))
seal_h = _load("seal_tests_helper", HERE / "test_seal_controller.py")       # its World: aggregate, ops dir, a git repo whose main holds the head
eq_h = _load("eqr_tests_helper", HERE / "test_equivalence_record.py")        # its Case: real EQUIVALENCE_RECORD/1 documents

NOW = dt.datetime(2026, 10, 22, 12, 0, 0, tzinfo=dt.timezone.utc)
H = "ab" * 20                                   # the trial (integration) head
PR = 3841
RUN_ID = "11111111-2222-3333-4444-555555555555"
EXEC = "brahma-build-pipeline-job-abc12"
CHART = seal_h.CHART


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class FakeGh:
    """The GitHub state the chain reads, and the three acts it may make (recorded; a failing act changes nothing)."""

    def __init__(self, c):
        self.c = c
        self.reads, self.acts, self.act_rc = [], [], 0
        self.pr = {"number": PR, "state": "OPEN", "isDraft": False, "baseRefName": "main", "headRefOid": H, "mergeCommit": None, "autoMergeRequest": None, "labels": []}
        self.compare = {"status": "identical", "ahead_by": 0, "behind_by": 0}
        self.runs = [self.run_row(1, "CI", ".github/workflows/ci.yml", "push", "completed", "success"),
                     self.run_row(5, "Deploy to Cloud Run", dc.DEPLOY_PATH, "workflow_dispatch", "completed", "success", created="2026-10-22T09:00:00Z")]
        self.deploy_on_dispatch, self.deploy_conclusion, self.deploy_status = True, "success", "completed"

    def run_row(self, rid, name, path, event, status, conclusion, created="2026-10-22T10:00:00Z"):
        return {"id": rid, "name": name, "path": path, "event": event, "head_sha": self.c.M, "head_branch": "main", "status": status, "conclusion": conclusion,
                "created_at": created, "run_attempt": 1}

    def merge(self):
        self.pr.update(state="MERGED", mergeCommit={"oid": self.c.M}, autoMergeRequest=None)

    def read(self, argv):
        self.reads.append(argv)
        if argv[:2] == ["pr", "view"]:
            return copy.deepcopy(self.pr)
        if argv[0] == "api" and "/compare/" in argv[1]:
            return copy.deepcopy(self.compare)
        if argv[0] == "api" and "/actions/runs" in argv[1]:
            return {"runs": copy.deepcopy(self.runs)}
        raise AssertionError(f"unexpected gh read {argv}")

    def act(self, argv):
        self.acts.append(argv)
        if self.act_rc != 0:
            return self.act_rc, "boom"
        if argv[:2] == ["pr", "merge"]:
            self.pr["autoMergeRequest"] = {"enabledAt": "2026-10-22T11:00:00Z"}
        elif argv[:2] == ["pr", "edit"]:
            self.pr["labels"] = [lb for lb in self.pr["labels"] if lb["name"] != argv[argv.index("--remove-label") + 1]]
        elif argv[:2] == ["workflow", "run"] and self.deploy_on_dispatch:
            self.runs.append(self.run_row(900 + len(self.acts), "Deploy to Cloud Run", dc.DEPLOY_PATH, "workflow_dispatch", self.deploy_status, self.deploy_conclusion,
                                          created="2026-10-22T11:30:00Z"))
        return 0, ""


class FakeTools:
    """The two local tools.  `compare` is the REAL equivalence_record main; `record` writes the prepared main record (no git repo of the sources exists here); the rehearsal writes the prepared report."""

    def __init__(self, c):
        self.c, self.calls = c, []

    def run(self, script, args, timeout=0):
        self.calls.append((script, args))
        if script == "equivalence_record.py" and args[0] == "record":
            rec, mans = self.c.main_case.build()
            rec["E6"]["commit"] = self.c.record_commit or self.c.M
            eqr.write_record(rec, mans, args[args.index("--out") + 1])
            return 0, "", ""
        if script == "equivalence_record.py" and args[0] == "compare":
            return eqr.main(args), "", ""
        if script == "admission_rehearsal.py":
            out = Path(args[args.index("--out") + 1])
            out.mkdir(parents=True, exist_ok=True)
            doc = self.c.rehearsal_doc(args[args.index("--main-ref") + 1])
            (out / "REHEARSAL.json").write_text(json.dumps(doc))
            return (1 if doc["flags"] else 0), "", ""
        raise AssertionError(f"unexpected tool {script}")


class Chain:
    def __init__(self, m, tmp, differs=False):
        self.m, self.tmp = m, Path(tmp)
        self.seal = seal_h.World(self.tmp / "seal", verification=False, with_brief=False)
        self.M, self.ops = self.seal.head, self.seal.ops
        self.out, self.pages, self.queue = self.tmp / "out", self.tmp / "PAGES.log", self.tmp / "queue"
        self.ev, self.staged = self.tmp / "ev", self.tmp / "staged"
        for d in (self.ev, self.staged):
            d.mkdir(parents=True)
        self.now, self.stale_caps, self.record_commit = NOW, False, None
        self.rehearsal_flags, self.rehearsal_bad_control, self.rehearsal_refused = [], False, set()
        self.gh, self.tools = FakeGh(self), FakeTools(self)
        solver = eq_h.K + "window_solver.py"
        self.trial_case = eq_h.Case(self.tmp, "trialw")
        edits = [(solver, "MAX_EVALS = 40_000", "MAX_EVALS = 50_000")] if differs else ()
        self.main_case = eq_h.Case(self.tmp, "mainw", src=self.trial_case, tree_edits=edits)
        self.write_trial_ready()
        self.write_trial_record()
        self.write_tr_verdict()
        self.write_rvint()
        self.write_templates()
        self.write_cfg()

    # ── evidence writers ──
    def put(self, name, doc):
        p = self.ev / name
        p.write_text(json.dumps(doc))
        return p

    def write_trial_ready(self, head=None, mutate=None):
        doc = {"predicate": "TRIAL_READY/1", "head_sha": head or H, "evaluated_at": "2026-10-22T09:00:00Z", "ready": True,
               "checks": [{"id": i, "claim": f"claim {i}", "value": True, "evidence_ref": f"git:{H[:12]}:{i}", "sha256": "0" * 64} for i in dc.TRIAL_IDS]}
        if mutate:
            mutate(doc)
        self.put("trial_ready.json", doc)

    def write_trial_record(self):
        rec, mans = self.trial_case.build()
        eqr.write_record(rec, mans, self.ev / "trial_record.json")

    def write_tr_verdict(self, mutate=None, bind=True):
        doc = {"schema": "ky.tr_verdict/1", "head_sha": H, "trial_ready_sha256": sha((self.ev / "trial_ready.json").read_bytes()) if bind else "f" * 64,
               "qualifying": True, "label": None, "classes": [f"class_{i:02d}" for i in range(12)], "verdict": "PASS",
               "gates": {g: {"value": True, "evidence_ref": f"tr:{g}"} for g in dc.GATES},
               "equivalence_record_sha256": sha((self.ev / "trial_record.json").read_bytes())}
        if mutate:
            mutate(doc)
        self.put("tr_verdict.json", doc)

    def write_rvint(self, mutate=None):
        doc = {"schema": "ky.job_result/1", "item": "RV-INT part 2", "status": "done",
               "proposed_verdict": {"verdict": "ACCEPTED", "head": H, "patch_id": "c" * 40, "claims": ["seam: anchor x Form B"], "findings": []}}
        if mutate:
            mutate(doc)
        self.put("rvint_part2.result.json", doc)

    def write_templates(self):
        base = {"item_id": "J-4e", "requested_by": "adhikarin", "reviewed_commit": self.M}
        docs = {"century.json": {**base, "operation_id": "century-5-0-d1", "kind": "century_dispatch", "args": {"classes": "all", "result_policy": "window_qualification/1"}},
                "verify-1.json": {**base, "operation_id": "verify-5-0-s1", "kind": "verification_job", "args": {"generation": "5.0"}},
                "verify-2.json": {**base, "operation_id": "verify-5-0-s2", "kind": "verification_job", "args": {"generation": "5.0"}}}
        for n, d in docs.items():
            (self.staged / n).write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")

    def write_rebind(self, version="1.7", head=None, staged=None):
        self.put("pack_rebind.json", {"schema": "ky.pack_rebind/1", "pack_version": version, "main_head": head or self.M, "staged_sha256": staged or dc.sha_dir(self.staged)})

    def write_caps(self, **kw):
        ts = self.now - dt.timedelta(seconds=(7200 if self.stale_caps else 30))
        doc = {"builder": True, "gcloud": True, "pgenv": True, "ops_table_on_main": True, "production_slot": "free", "executor_revision": "e" * 64, "main_revision": self.M,
               "refresh_state": "ACTIVE", "ts": ts.isoformat(timespec="seconds"), **kw}
        (self.ops / "CAPABILITIES.json").write_text(json.dumps(doc))

    def rehearsal_doc(self, main):
        rows = [{"template": n, "verdict": {"admitted": n not in self.rehearsal_refused, "code": "stale_pin"}} for n in ("century.json", "verify-1.json", "verify-2.json")]
        return {"schema": "ky.admission_rehearsal/1", "main": main, "flags": list(self.rehearsal_flags),
                "controls": [{"control": "stale_pin", "ok": not self.rehearsal_bad_control}, {"control": "scope_missing", "ok": True}],
                "sets": {dc.REHEARSAL_SET: rows}}

    def cfg(self):
        return {"schema": dc.CONFIG_SCHEMA, "chart_id": CHART, "generation": "5.0", "repo": str(self.seal.repo), "evidence_dir": str(self.ev), "stall_s": 3600,
                "trial": {"head": H, "arm": {"where": "cloud", "argv": ["tr_harness", "--head", "{head}", "--ready", "{trial_ready}"]}},
                "pr": {"number": PR, "hold_labels": ["hold"]}, "ci": {"required": ["CI"]}, "main": {"pinned_inputs_file": str(self.tmp / "pinned.json")},
                "dispatch": {"pack_version": "1.7", "staged_dir": str(self.staged), "century_template": "century.json", "rebind_argv": ["repin", "--head", "{head}"],
                             "sandbox_root": str(self.tmp / "sandbox")},
                "verification": {"templates": ["verify-1.json", "verify-2.json"]},
                "seal": {"aggregate_file": str(self.seal.aggregate), "expected_classes": seal_h.CLASSES, "adopted_file": str(self.tmp / "ADOPTED_CENTURY.json"),
                         "out": str(self.tmp / "seal-out")}}

    def write_cfg(self, mutate=None):
        c = self.cfg()
        if mutate:
            mutate(c)
        (self.tmp / "chain.json").write_text(json.dumps(c))

    # ── running ──
    def poll(self, apply=False, dry=False, **kw):
        self.write_caps()
        return self.m.run(self.tmp / "chain.json", self.ops, self.out, self.pages, requests_dir=self.queue, gh=self.gh, tools=self.tools, now=self.now, apply=apply, dry=dry, **kw)

    def pages_lines(self, tag=None):
        if not self.pages.exists():
            return []
        return [ln for ln in self.pages.read_text().splitlines() if not tag or f"PAGE {tag}" in ln]

    def queued(self, prefix):
        return sorted(self.queue.glob(prefix + "*.json")) if self.queue.is_dir() else []

    def answer(self, op, kind, text, commit=None):
        self.seal.receipt(op, kind, "COMPLETED", 0, text, commit or self.M)

    def readback_text(self, commit=None, outcome=None, run_id=RUN_ID):
        d = {"schema": "ky.cloudrun_readback/1", "status": "MEASURED", "provenance": {"image_commit": commit or self.M}}
        if outcome:
            d["execution"] = {"name": EXEC, "outcome": outcome, "args": ["--run-id", run_id]}
        return json.dumps(d) + "\n"

    # ── walking the chain ──
    def expect(self, st, kind):
        assert st["kind"] == kind, (kind, st["line"])
        return st

    def advance_to(self, target):
        """Walk the chain with --apply and the fixture playing cockpit/executor, up to (and not past) the START of stage `target`."""
        order = ["S1", "S2", "S3", "S4", "S5", "DONE"]
        goal = order.index(target)
        if goal == 0:
            return None
        st = self.poll(apply=True)
        assert st["kind"].startswith("S1_MERGE_ENQUEUE"), st["line"]
        self.gh.merge()
        if goal == 1:
            return None
        st = self.poll(apply=True)
        self.expect(st, "S2_DEPLOY_NO_RUN")                                      # the deploy was dispatched in this poll; its run appears in the next readback
        st = self.poll(apply=True)
        self.expect(st, "S2_AWAITING_RECEIPT")                                   # the image readback request is queued
        (img,) = self.queued("chain-image-")
        self.answer(img.stem, "cloudrun_job_readback", self.readback_text())
        st = self.poll(apply=True)
        self.expect(st, "S3_REBIND_PENDING")                                     # S2 passed: EQUIVALENCE computed and EQUAL; the executor is refreshed
        if goal == 2:
            return None
        self.write_rebind()
        st = self.poll(apply=True)
        assert st["stage"] == "S3", st["line"]                                   # rehearsal ran; the century request was queued; S3 passed
        st = self.expect(st, "S4_AWAITING_RECEIPT")
        if goal == 3:
            return None
        launch = {"schema": "ky.century_launch/1", "status": "LAUNCHED", "run_id": RUN_ID, "execution_name": EXEC}
        self.answer("century-5-0-d1", "century_dispatch", json.dumps(launch) + "\n")
        st = self.poll(apply=True)
        self.expect(st, "S4_AWAITING_RECEIPT")
        (rb,) = self.queued("chain-build-")
        self.answer(rb.stem, "cloudrun_job_readback", self.readback_text(outcome="RUNNING"))
        st = self.poll(apply=True)
        self.expect(st, "S4_BUILD_RUNNING")
        self.now += dt.timedelta(seconds=600)                                    # the next period: a fresh read-only readback is requested
        st = self.poll(apply=True)
        self.expect(st, "S4_BUILD_RUNNING")
        rb2 = [p for p in self.queued("chain-build-") if p != rb][-1]
        self.answer(rb2.stem, "cloudrun_job_readback", self.readback_text(outcome="SUCCEEDED"))
        if goal == 4:
            return None
        st = self.poll(apply=True)
        self.expect(st, "S5_AWAITING_RECEIPT")
        for op in ("verify-5-0-s1", "verify-5-0-s2"):
            self.answer(op, "verification_job", "ok\n")
        return None


def boom_if_process(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError(f"the chain started a process: {a[:1]}")
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)


# ═════════════════════════════════════════ S0 ═════════════════════════════════════════

def o_s0_ready_arms_the_tr_once(m, tmp):
    c = Chain(m, tmp)
    st = c.poll()
    assert st["stages"][0]["state"] == "PASS" and st["stages"][0]["evidence"]["true_checks"] == 25, st["line"]
    doc = json.loads((c.out / "actions" / f"ARM_TR.5.0.{H}.json").read_text())
    assert doc["kind"] == "harness_command" and doc["runs"] is False and doc["argv"][:3] == ["tr_harness", "--head", H], doc
    c.poll()
    assert len(c.pages_lines("CHAIN-ARM-TR")) == 1


def o_s0_null_check_holds_and_no_tr(m, tmp):
    c = Chain(m, tmp)
    c.write_trial_ready(mutate=lambda d: d["checks"][6].update(value=None))
    st = c.poll()
    assert st["kind"] == "S0_NOT_READY" and "T07" in st["reason"], st["line"]
    assert not (c.out / "actions").exists() and st["stages"][1]["state"] == "NOT_REACHED"


def o_s0_other_head_holds(m, tmp):
    c = Chain(m, tmp)
    c.write_trial_ready(head="cd" * 20)
    st = c.poll()
    assert st["kind"] == "S0_STALE_HEAD" and not (c.out / "actions").exists(), st["line"]


def o_s0_missing_check_holds(m, tmp):
    c = Chain(m, tmp)
    c.write_trial_ready(mutate=lambda d: d["checks"].pop())
    st = c.poll()
    assert st["kind"] == "S0_CHECKS_INCOMPLETE" and "T25" in st["reason"], st["line"]


def o_s0_claimed_ready_is_not_trusted(m, tmp):
    c = Chain(m, tmp)
    c.write_trial_ready(mutate=lambda d: d["checks"][0].update(value=False))      # ready:true is still in the file
    st = c.poll()
    assert st["kind"] == "S0_NOT_READY" and not (c.out / "actions").exists(), st["line"]


def test_s0_ready_arms_the_tr_once(tmp_path):
    o_s0_ready_arms_the_tr_once(dc, tmp_path)


def test_s0_null_check_holds_and_no_tr(tmp_path):
    o_s0_null_check_holds_and_no_tr(dc, tmp_path)


def test_s0_other_head_holds(tmp_path):
    o_s0_other_head_holds(dc, tmp_path)


def test_s0_missing_check_holds(tmp_path):
    o_s0_missing_check_holds(dc, tmp_path)


def test_s0_claimed_ready_is_not_trusted(tmp_path):
    o_s0_claimed_ready_is_not_trusted(dc, tmp_path)


def test_s0_ready_true_with_all_checks_true_but_a_check_without_evidence_holds(tmp_path):
    c = Chain(dc, tmp_path)
    c.write_trial_ready(mutate=lambda d: d["checks"][3].update(evidence_ref=None))
    assert c.poll()["kind"] == "S0_GREEN_WITHOUT_EVIDENCE"


def test_s0_the_25_ids_equal_the_evaluators_required_ids():
    """Parity: the recount here and platform/scripts/governance/trial_ready.py name the same T01..T25."""
    ev = _load("trial_ready_real", SCRIPTS / "governance" / "trial_ready.py")
    assert tuple(dc.TRIAL_IDS) == tuple(ev.REQUIRED_IDS) and ev.PREDICATE == dc.TRIAL_READY_PREDICATE


# ═════════════════════════════════════════ S1 ═════════════════════════════════════════

def o_s1_pass_enqueues_the_bound_merge_once(m, tmp):
    c = Chain(m, tmp)
    st = c.poll(apply=True)
    assert st["kind"] == "S1_MERGE_ENQUEUE_APPLIED", st["line"]
    assert c.gh.acts == [["pr", "merge", str(PR), "--repo", dc.REPO_SLUG, "--auto", "--squash", "--match-head-commit", H]], c.gh.acts
    c.gh.pr["autoMergeRequest"] = None                                          # GitHub dropped the request: the (generation, head) key already acted, so no second enqueue
    st = c.poll(apply=True)
    assert st["kind"] == "S1_MERGE_ENQUEUE_ALREADY" and len(c.gh.acts) == 1, st["line"]


def o_s1_null_gate_holds_and_nothing_merges(m, tmp):
    c = Chain(m, tmp)
    c.write_tr_verdict(mutate=lambda d: d["gates"].__setitem__("G-4", {"value": None, "evidence_ref": "tr:G-4"}))
    st = c.poll(apply=True)
    assert st["kind"] == "S1_GATES_NOT_PASSED" and "G-4" in st["reason"] and c.gh.acts == [], st["line"]


def o_s1_unbound_verdict_holds(m, tmp):
    c = Chain(m, tmp)
    c.write_tr_verdict(bind=False)
    st = c.poll(apply=True)
    assert st["kind"] == "S1_VERDICT_UNBOUND" and c.gh.acts == [], st["line"]


def o_s1_diagnostic_is_no_evidence(m, tmp):
    c = Chain(m, tmp)
    c.write_tr_verdict(mutate=lambda d: d.update(qualifying=False, label="DIAGNOSTIC"))
    st = c.poll(apply=True)
    assert st["kind"] == "S1_VERDICT_NOT_QUALIFYING" and c.gh.acts == [], st["line"]


def o_s1_rvint_not_accepted_holds(m, tmp):
    c = Chain(m, tmp)
    c.write_rvint(mutate=lambda d: d["proposed_verdict"].update(verdict="REJECTED"))
    st = c.poll(apply=True)
    assert st["kind"] == "S1_RVINT_NOT_PASSED" and c.gh.acts == [], st["line"]


def o_s1_rvint_other_head_holds(m, tmp):
    c = Chain(m, tmp)
    c.write_rvint(mutate=lambda d: d["proposed_verdict"].update(head="cd" * 20))
    st = c.poll(apply=True)
    assert st["kind"] == "S1_RVINT_STALE_HEAD" and c.gh.acts == [], st["line"]


def o_s1_pr_head_moved_is_never_merged(m, tmp):
    c = Chain(m, tmp)
    c.gh.pr["headRefOid"] = "cd" * 20
    st = c.poll(apply=True)
    assert st["kind"] == "S1_PR_HEAD_MOVED" and c.gh.acts == [], st["line"]


def test_s1_pass_enqueues_the_bound_merge_once(tmp_path):
    o_s1_pass_enqueues_the_bound_merge_once(dc, tmp_path)


def test_s1_null_gate_holds_and_nothing_merges(tmp_path):
    o_s1_null_gate_holds_and_nothing_merges(dc, tmp_path)


def test_s1_unbound_verdict_holds(tmp_path):
    o_s1_unbound_verdict_holds(dc, tmp_path)


def test_s1_diagnostic_is_no_evidence(tmp_path):
    o_s1_diagnostic_is_no_evidence(dc, tmp_path)


def test_s1_rvint_not_accepted_holds(tmp_path):
    o_s1_rvint_not_accepted_holds(dc, tmp_path)


def test_s1_rvint_other_head_holds(tmp_path):
    o_s1_rvint_other_head_holds(dc, tmp_path)


def test_s1_pr_head_moved_is_never_merged(tmp_path):
    o_s1_pr_head_moved_is_never_merged(dc, tmp_path)


def test_s1_auto_merge_on_waits_without_enqueueing_again(tmp_path):
    c = Chain(dc, tmp_path)
    c.poll(apply=True)
    st = c.poll(apply=True)
    assert st["kind"] == "S1_MERGE_QUEUED" and st["soft"] is True and len(c.gh.acts) == 1


def test_s1_emit_mode_writes_the_gh_command_and_runs_nothing(tmp_path):
    c = Chain(dc, tmp_path)
    st = c.poll()                                                                 # no --apply
    assert st["kind"] == "S1_MERGE_ENQUEUE_EMITTED" and c.gh.acts == [], st["line"]
    cmd = (c.out / "actions" / f"PR_AUTOMERGE.{PR}.{H}.txt").read_text()
    assert cmd.startswith("gh pr merge 3841") and "--match-head-commit " + H in cmd


def test_s1_a_held_pr_is_unheld_with_the_exact_label_then_enqueued(tmp_path):
    c = Chain(dc, tmp_path)
    c.gh.pr["labels"] = [{"name": "hold"}]
    st = c.poll(apply=True)
    assert c.gh.acts[0] == ["pr", "edit", str(PR), "--repo", dc.REPO_SLUG, "--remove-label", "hold"], c.gh.acts
    assert st["kind"] == "S1_MERGE_ENQUEUE_APPLIED", st["line"]


def test_s1_draft_closed_and_other_base_hold(tmp_path):
    for field, val, code in (("isDraft", True, "S1_PR_DRAFT"), ("state", "CLOSED", "S1_PR_CLOSED"), ("baseRefName", "release", "S1_PR_BASE")):
        c = Chain(dc, tmp_path / code)
        c.gh.pr[field] = val
        assert c.poll(apply=True)["kind"] == code and c.gh.acts == []


# ═════════════════════════════════════════ S2 ═════════════════════════════════════════

def o_s2_not_on_main_holds(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S2")
    c.gh.compare["status"] = "diverged"
    st = c.poll(apply=True)
    assert st["kind"] == "S2_NOT_ON_MAIN", st["line"]


def o_s2_red_ci_holds_and_no_deploy(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S2")
    c.gh.runs[0]["conclusion"] = "failure"
    before = len(c.gh.acts)
    st = c.poll(apply=True)
    assert st["kind"] == "S2_CI_RED" and len(c.gh.acts) == before, st["line"]


def o_s2_deploy_is_a_new_run_not_an_older_dispatch(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S2")
    c.gh.deploy_on_dispatch = False                                              # the dispatch makes no new run; run 5 (success) predates it
    st = c.poll(apply=True)
    assert st["kind"] == "S2_DEPLOY_NO_RUN", st["line"]
    assert c.gh.acts[-1] == ["workflow", "run", "deploy.yml", "--repo", dc.REPO_SLUG, "--ref", "main", "-f", "force_all_services=true"]


def o_s2_deploy_is_never_repeated(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S2")
    c.gh.act_rc = 1
    st = c.poll(apply=True)
    assert st["kind"] == "A2.DEPLOY_OUTCOME_UNKNOWN" and len(c.gh.acts) == 2, st["line"]      # (merge, deploy)
    c.gh.act_rc = 0
    c.poll(apply=True)
    assert len(c.gh.acts) == 2, c.gh.acts                                        # nothing repeated after the unknown outcome


def o_s2_image_must_carry_m(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S2")
    c.poll(apply=True)
    c.poll(apply=True)
    (img,) = c.queued("chain-image-")
    c.answer(img.stem, "cloudrun_job_readback", c.readback_text(commit="cd" * 20))
    st = c.poll(apply=True)
    assert st["kind"] == "S2_IMAGE_NOT_M", st["line"]


def _to_equivalence(c):
    c.advance_to("S2")
    c.poll(apply=True)
    c.poll(apply=True)
    (img,) = c.queued("chain-image-")
    c.answer(img.stem, "cloudrun_job_readback", c.readback_text())


def o_s2_differs_holds_with_the_tables_action(m, tmp):
    c = Chain(m, tmp, differs=True)
    _to_equivalence(c)
    st = c.poll(apply=True)
    assert st["kind"] == "S2_EQ_DIFFERS" and "blocks_dispatch" in st["reason"], st["line"]
    assert st["stages"][3]["state"] == "NOT_REACHED" and not c.queued("century"), st["line"]


def o_s2_decision_about_other_records_is_recomputed(m, tmp):
    c = Chain(m, tmp)
    _to_equivalence(c)
    assert c.poll(apply=True)["stage"] == "S2"                                    # EQUAL decision on disk
    c.main_case = eq_h.Case(c.tmp, "mainw2", src=c.trial_case, tree_edits=[(eq_h.K + "window_solver.py", "MAX_EVALS = 40_000", "MAX_EVALS = 50_000")])
    (c.ev / "main_record.json").unlink()                                          # a new main record (DIFFERS) is produced; the old EQUAL decision is about the previous one
    st = c.poll(apply=True)
    assert st["kind"] == "S2_EQ_DIFFERS", st["line"]


def o_s2_main_record_of_another_commit_holds(m, tmp):
    c = Chain(m, tmp)
    c.record_commit = "cd" * 20
    _to_equivalence(c)
    st = c.poll(apply=True)
    assert st["kind"] == "S2_EQ_RECORD_OTHER_COMMIT", st["line"]


def o_s2_tampered_equal_decision_holds(m, tmp):
    c = Chain(m, tmp, differs=True)
    _to_equivalence(c)
    c.poll(apply=True)                                                            # real DIFFERS decision written
    p = c.ev / "equivalence_decision.json"
    d = json.loads(p.read_text())
    d["decision"] = "EQUAL"                                                       # tampered: still bound to the right record digests
    p.write_text(json.dumps(d))
    st = c.poll(apply=True)
    assert st["kind"] == "S2_EQ_DISAGREEMENT" and not c.queued("century"), st["line"]


def test_s2_not_on_main_holds(tmp_path):
    o_s2_not_on_main_holds(dc, tmp_path)


def test_s2_red_ci_holds_and_no_deploy(tmp_path):
    o_s2_red_ci_holds_and_no_deploy(dc, tmp_path)


def test_s2_ci_running_is_a_soft_hold_and_no_deploy(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S2")
    c.gh.runs[0].update(status="in_progress", conclusion=None)
    st = c.poll(apply=True)
    assert st["kind"] == "S2_CI_RUNNING" and st["soft"] is True and len(c.gh.acts) == 1


def test_s2_deploy_is_a_new_run_not_an_older_dispatch(tmp_path):
    o_s2_deploy_is_a_new_run_not_an_older_dispatch(dc, tmp_path)


def test_s2_deploy_is_never_repeated(tmp_path):
    o_s2_deploy_is_never_repeated(dc, tmp_path)


def test_s2_a_failed_deploy_run_holds(tmp_path):
    c = Chain(dc, tmp_path)
    c.gh.deploy_conclusion = "failure"
    c.advance_to("S2")
    c.poll(apply=True)
    st = c.poll(apply=True)
    assert st["kind"] == "S2_DEPLOY_FAILED", st["line"]


def test_s2_image_must_carry_m(tmp_path):
    o_s2_image_must_carry_m(dc, tmp_path)


def test_s2_differs_holds_with_the_tables_action(tmp_path):
    o_s2_differs_holds_with_the_tables_action(dc, tmp_path)


def test_s2_decision_about_other_records_is_recomputed(tmp_path):
    o_s2_decision_about_other_records_is_recomputed(dc, tmp_path)


def test_s2_main_record_of_another_commit_holds(tmp_path):
    o_s2_main_record_of_another_commit_holds(dc, tmp_path)


def test_s2_tampered_equal_decision_holds(tmp_path):
    o_s2_tampered_equal_decision_holds(dc, tmp_path)


def test_s2_equal_passes_with_the_real_tool_and_stores_both_provenances(tmp_path):
    c = Chain(dc, tmp_path)
    _to_equivalence(c)
    st = c.poll(apply=True)
    assert st["stage"] == "S2", st["line"]
    d = json.loads((c.ev / "equivalence_decision.json").read_text())
    assert d["decision"] == "EQUAL" and d["main_record_sha"] == sha((c.ev / "main_record.json").read_bytes())
    assert d["provenance"]["main"]["commit"] == c.M


def test_s2_emit_mode_records_the_prior_runs_and_writes_the_deploy_command(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S2")
    st = c.poll()                                                                  # emit mode: no --apply
    assert st["kind"] == "S2_DEPLOY_NO_RUN" and len(c.gh.acts) == 1, st["line"]    # the only act is the merge from advance_to
    assert json.loads((c.out / "markers" / f"DEPLOY.{c.M}").read_text())["prior_run_ids"] == [5]
    cmd = (c.out / "actions" / f"DEPLOY.{c.M}.txt").read_text().strip()
    assert cmd == "gh workflow run deploy.yml --repo " + dc.REPO_SLUG + " --ref main -f force_all_services=true"
    c.gh.runs.append(c.gh.run_row(901, "Deploy to Cloud Run", dc.DEPLOY_PATH, "workflow_dispatch", "completed", "success", created="2026-10-22T11:30:00Z"))   # the cockpit ran it
    st = c.poll()
    assert st["kind"] == "S2_AWAITING_RECEIPT" and list((c.out / "requests").glob("chain-image-*.json")), st["line"]


# ═════════════════════════════════════════ S3 ═════════════════════════════════════════

def _s3_perturb(c, mutate, code):
    """S2 passed (EQUAL, executor refreshed); the rebind is written; ONE input is perturbed; S3 must hold with `code` and queue nothing."""
    c.advance_to("S3")
    c.write_rebind()
    mutate(c)
    st = c.poll(apply=True)
    assert st["kind"] == code, st["line"]
    assert not c.queued("century") and not c.queued("verify"), st["line"]
    return st


def _caps(**override):
    def mutate(c):
        orig = c.write_caps
        c.write_caps = lambda **kw: orig(**{**kw, **override})
    return mutate


def o_s3_executor_not_at_m_holds(m, tmp):
    _s3_perturb(Chain(m, tmp), _caps(main_revision="cd" * 20), "S3_EXECUTOR_NOT_REFRESHED")


def o_s3_busy_slot_holds(m, tmp):
    _s3_perturb(Chain(m, tmp), _caps(production_slot="busy"), "S3_PRODUCTION_SLOT_BUSY")


def o_s3_rebind_other_head_holds(m, tmp):
    c = Chain(m, tmp)
    _s3_perturb(c, lambda cc: cc.write_rebind(head="cd" * 20), "S3_REBIND_STALE_HEAD")


def o_s3_staged_edited_after_rebind_holds(m, tmp):
    c = Chain(m, tmp)

    def edit(cc):
        t = json.loads((cc.staged / "century.json").read_text())
        t["args"]["classes"] = "one"
        (cc.staged / "century.json").write_text(json.dumps(t))
    _s3_perturb(c, edit, "S3_REBIND_STAGED_CHANGED")


def o_s3_stale_pin_holds(m, tmp):
    c = Chain(m, tmp)

    def stale(cc):
        t = json.loads((cc.staged / "verify-2.json").read_text())
        t["reviewed_commit"] = "cd" * 20
        (cc.staged / "verify-2.json").write_text(json.dumps(t))
        cc.write_rebind()                                                          # the digest is honest; the pin inside is stale
    _s3_perturb(c, stale, "S3_STALE_PINS")


def o_s3_rehearsal_flags_hold(m, tmp):
    c = Chain(m, tmp)
    c.rehearsal_flags = ["stale_pin_sql: VALIDATOR_ADMITS"]
    _s3_perturb(c, lambda cc: None, "S3_REHEARSAL_FLAGS")


def o_s3_control_that_admitted_its_defect_holds(m, tmp):
    c = Chain(m, tmp)
    c.rehearsal_bad_control = True
    _s3_perturb(c, lambda cc: None, "S3_REHEARSAL_CONTROLS")


def o_s3_unadmitted_template_holds(m, tmp):
    c = Chain(m, tmp)
    c.rehearsal_refused = {"verify-2.json"}
    st = _s3_perturb(c, lambda cc: None, "S3_TEMPLATES_NOT_ADMITTED")
    assert "verify-2.json" in st["reason"]


def o_s3_rehearsal_of_another_main_is_not_reused(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S3")
    c.write_rebind()
    d = c.ev / "rehearsal" / c.M[:12]
    d.mkdir(parents=True)
    (d / "REHEARSAL.json").write_text(json.dumps(c.rehearsal_doc("cd" * 20)))     # a clean report about ANOTHER main
    c.poll(apply=True)
    assert any(s == "admission_rehearsal.py" for s, _ in c.tools.calls), c.tools.calls
    assert json.loads((d / "REHEARSAL.json").read_text())["main"] == c.M


def o_s3_green_queues_the_pack_template_byte_for_byte_once(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S4")
    (q,) = c.queued("century-")
    assert q.read_bytes() == (c.staged / "century.json").read_bytes()
    q.unlink()                                                                  # the executor consumed it: a later poll must not queue the same operation again
    c.poll(apply=True)
    assert c.queued("century-") == [] and len([p for p in c.tools.calls if p[0] == "admission_rehearsal.py"]) == 1


def test_s3_executor_not_at_m_holds(tmp_path):
    o_s3_executor_not_at_m_holds(dc, tmp_path)


def test_s3_stale_executor_evidence_is_a_soft_hold(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S3")
    c.stale_caps = True
    st = c.poll(apply=True)
    assert st["kind"] == "S3_EXECUTOR_EVIDENCE_STALE" and st["soft"] is True


def test_s3_busy_slot_holds(tmp_path):
    o_s3_busy_slot_holds(dc, tmp_path)


def test_s3_rebind_other_head_holds(tmp_path):
    o_s3_rebind_other_head_holds(dc, tmp_path)


def test_s3_staged_edited_after_rebind_holds(tmp_path):
    o_s3_staged_edited_after_rebind_holds(dc, tmp_path)


def test_s3_stale_pin_holds(tmp_path):
    o_s3_stale_pin_holds(dc, tmp_path)


def test_s3_rebind_wrong_version_holds(tmp_path):
    c = Chain(dc, tmp_path)
    _s3_perturb(c, lambda cc: cc.write_rebind(version="1.6"), "S3_REBIND_VERSION")


def test_s3_no_rebind_writes_the_rebind_command_and_holds_soft(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S3")
    st = c.poll(apply=True)
    assert st["kind"] == "S3_REBIND_PENDING" and st["soft"] is True
    doc = json.loads((c.out / "actions" / f"REBIND.{c.M}.json").read_text())
    assert doc["runs"] is False and doc["argv"] == ["repin", "--head", c.M]


def test_s3_rehearsal_flags_hold(tmp_path):
    o_s3_rehearsal_flags_hold(dc, tmp_path)


def test_s3_control_that_admitted_its_defect_holds(tmp_path):
    o_s3_control_that_admitted_its_defect_holds(dc, tmp_path)


def test_s3_unadmitted_template_holds(tmp_path):
    o_s3_unadmitted_template_holds(dc, tmp_path)


def test_s3_rehearsal_of_another_main_is_not_reused(tmp_path):
    o_s3_rehearsal_of_another_main_is_not_reused(dc, tmp_path)


def test_s3_green_queues_the_pack_template_byte_for_byte_once(tmp_path):
    o_s3_green_queues_the_pack_template_byte_for_byte_once(dc, tmp_path)


# ═════════════════════════════════════════ S4 ═════════════════════════════════════════

def o_s4_receipt_without_launch_evidence_holds(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S4")
    pending = {"schema": "ky.century_launch/1", "status": "LAUNCH_PENDING", "run_id": RUN_ID, "execution_name": EXEC}
    c.answer("century-5-0-d1", "century_dispatch", json.dumps(pending) + "\n")
    st = c.poll(apply=True)
    assert st["kind"] == "S4_NO_LAUNCH_EVIDENCE" and not c.queued("verify"), st["line"]


def o_s4_running_build_holds_and_no_verification(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S4")
    c.answer("century-5-0-d1", "century_dispatch", json.dumps({"schema": "ky.century_launch/1", "status": "LAUNCHED", "run_id": RUN_ID, "execution_name": EXEC}) + "\n")
    c.poll(apply=True)
    (rb,) = c.queued("chain-build-")
    c.answer(rb.stem, "cloudrun_job_readback", c.readback_text(outcome="RUNNING"))
    st = c.poll(apply=True)
    assert st["kind"] == "S4_BUILD_RUNNING" and not c.queued("verify"), st["line"]


def o_s4_execution_of_another_run_holds(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("S4")
    c.answer("century-5-0-d1", "century_dispatch", json.dumps({"schema": "ky.century_launch/1", "status": "LAUNCHED", "run_id": RUN_ID, "execution_name": EXEC}) + "\n")
    c.poll(apply=True)
    (rb,) = c.queued("chain-build-")
    c.answer(rb.stem, "cloudrun_job_readback", c.readback_text(outcome="SUCCEEDED", run_id="99999999-2222-3333-4444-555555555555"))
    st = c.poll(apply=True)
    assert st["kind"] == "S4_BUILD_OTHER_RUN" and not c.queued("verify"), st["line"]


def o_s4_succeeded_launches_all_shards_in_the_same_poll(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("DONE")
    assert sorted(p.name for p in c.queued("verify-")) == ["verify-5-0-s1.json", "verify-5-0-s2.json"]
    for n, op in (("verify-1.json", "verify-5-0-s1"), ("verify-2.json", "verify-5-0-s2")):
        assert (c.queue / f"{op}.json").read_bytes() == (c.staged / n).read_bytes()
    ts = {json.loads((c.out / "markers" / f"REQ.{op}").read_text())["ts"] for op in ("verify-5-0-s1", "verify-5-0-s2")}
    assert len(ts) == 1, ts                                                       # one poll -> one second


def test_s4_receipt_without_launch_evidence_holds(tmp_path):
    o_s4_receipt_without_launch_evidence_holds(dc, tmp_path)


def test_s4_running_build_holds_and_no_verification(tmp_path):
    o_s4_running_build_holds_and_no_verification(dc, tmp_path)


def test_s4_execution_of_another_run_holds(tmp_path):
    o_s4_execution_of_another_run_holds(dc, tmp_path)


def test_s4_succeeded_launches_all_shards_in_the_same_poll(tmp_path):
    o_s4_succeeded_launches_all_shards_in_the_same_poll(dc, tmp_path)


def test_s4_a_failed_build_holds_and_pages_once(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S4")
    c.answer("century-5-0-d1", "century_dispatch", json.dumps({"schema": "ky.century_launch/1", "status": "LAUNCHED", "run_id": RUN_ID, "execution_name": EXEC}) + "\n")
    c.poll(apply=True)
    (rb,) = c.queued("chain-build-")
    c.answer(rb.stem, "cloudrun_job_readback", c.readback_text(outcome="FAILED"))
    assert c.poll(apply=True)["kind"] == "S4_BUILD_FAILED"
    c.poll(apply=True)
    assert len(c.pages_lines("CHAIN-HOLD")) == 1


# ═════════════════════════════════════════ S5 ═════════════════════════════════════════

def o_s5_verification_of_another_commit_holds(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("DONE")
    c.answer("verify-5-0-s2", "verification_job", "ok\n", commit="cd" * 20)
    st = c.poll(apply=True)
    assert st["kind"] == "S5_VERIFY_OTHER_COMMIT" and not (c.tmp / "ADOPTED_CENTURY.json").exists(), st["line"]


def o_s5_aggregate_without_g6_holds(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("DONE")
    agg = json.loads(c.seal.aggregate.read_text())
    agg.pop("g6")
    c.seal.aggregate.write_text(json.dumps(agg))
    st = c.poll(apply=True)
    assert st["kind"] == "S5_AGGREGATE_NOT_PASSED" and "G-6" in st["reason"] and not (c.tmp / "ADOPTED_CENTURY.json").exists(), st["line"]


def o_s5_passed_aggregate_writes_the_adopted_file_and_pages_once(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("DONE")
    st = c.poll(apply=True)
    assert st["state"] == "HANDED_OFF" and st["stage"] == "S5", st["line"]
    target = c.tmp / "ADOPTED_CENTURY.json"
    a = dc.sc.load_adopted(target)                                                # the seal controller's own loader accepts it
    assert a["head"] == c.M and a["generation"] == "5.0" and a["verification_operation_id"] == "verify-5-0-s1" and len(a["expected_classes"]) == 26
    c.poll(apply=True)
    assert len(c.pages_lines("CHAIN-HANDOFF")) == 1
    # and the seal controller takes over from the file: the aggregate stage and owner step 11 (the redeploy, read from the seal world's fake gh login) pass and it waits for the brief
    s = seal_h.sc.run(target, c.ops, c.tmp / "seal-out", c.pages, scripts_override=str(SCRIPTS), python=sys.executable, main_ref="main", gh=c.seal.gh, now=seal_h.NOW)
    assert s["stage"] == "REDEPLOY" and s["kind"] == seal_h.sc.AWAITING_BRIEF, s


def o_s5_adopted_file_of_another_generation_is_never_overwritten(m, tmp):
    c = Chain(m, tmp)
    c.advance_to("DONE")
    (c.tmp / "ADOPTED_CENTURY.json").write_text(json.dumps({"generation": "4.0", "head": "cd" * 20}))
    st = c.poll(apply=True)
    assert st["kind"] == "S5_ADOPTED_FILE_CONFLICT", st["line"]
    assert json.loads((c.tmp / "ADOPTED_CENTURY.json").read_text())["generation"] == "4.0"


def test_s5_verification_of_another_commit_holds(tmp_path):
    o_s5_verification_of_another_commit_holds(dc, tmp_path)


def test_s5_aggregate_without_g6_holds(tmp_path):
    o_s5_aggregate_without_g6_holds(dc, tmp_path)


def test_s5_passed_aggregate_writes_the_adopted_file_and_pages_once(tmp_path):
    o_s5_passed_aggregate_writes_the_adopted_file_and_pages_once(dc, tmp_path)


def test_s5_adopted_file_of_another_generation_is_never_overwritten(tmp_path):
    o_s5_adopted_file_of_another_generation_is_never_overwritten(dc, tmp_path)


def test_s5_without_apply_the_adopted_file_is_only_proposed(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("DONE")
    st = c.poll()                                                                  # emit mode
    assert st["state"] == "HANDED_OFF" and not (c.tmp / "ADOPTED_CENTURY.json").exists()
    assert dc.sc.load_adopted(c.out / "ADOPTED_CENTURY.proposed.json")["head"] == c.M
    assert len(c.pages_lines("CHAIN-HANDOFF-PROPOSED")) == 1


# ═════════════════════════════════════════ cross-cutting ═════════════════════════════════════════

def o_x_a_hard_hold_pages_once_per_reason(m, tmp):
    c = Chain(m, tmp)
    c.write_trial_ready(mutate=lambda d: d["checks"][0].update(value=False))
    c.poll()
    c.now += dt.timedelta(minutes=5)
    c.poll()
    assert len(c.pages_lines("CHAIN-HOLD")) == 1, c.pages_lines()


def o_x_a_soft_hold_pages_only_after_the_stall_limit(m, tmp):
    c = Chain(m, tmp)
    c.gh.pr["autoMergeRequest"] = {"enabledAt": "x"}                               # queued, not merged: a soft hold
    c.poll()
    c.now += dt.timedelta(seconds=60)
    st = c.poll()
    assert st["kind"] == "S1_MERGE_QUEUED" and c.pages_lines("CHAIN-STALL") == []
    c.now += dt.timedelta(seconds=4000)
    c.poll()
    c.poll()
    assert len(c.pages_lines("CHAIN-STALL")) == 1, c.pages_lines()


def o_x_dry_run_writes_nothing(m, tmp):
    c = Chain(m, tmp)
    st = c.poll(dry=True)
    assert not c.out.exists() and not c.pages.exists() and not c.queue.exists() and c.gh.acts == [], st["line"]
    assert [r["stage"] for r in st["stages"]] == list(dc.STAGE_IDS) and st["stages"][1]["state"] == "HOLD"
    text = m.format_plan(st)
    assert "A0.ARM_TR" in text and "A1.PR_AUTOMERGE" in text and "A5.HANDOFF" in text and "NOT_REACHED" in text


def test_x_a_hard_hold_pages_once_per_reason(tmp_path):
    o_x_a_hard_hold_pages_once_per_reason(dc, tmp_path)


def test_x_a_soft_hold_pages_only_after_the_stall_limit(tmp_path):
    o_x_a_soft_hold_pages_only_after_the_stall_limit(dc, tmp_path)


def test_x_dry_run_writes_nothing(tmp_path):
    o_x_dry_run_writes_nothing(dc, tmp_path)


def _snapshot(c):
    files = {str(p): p.stat().st_size for root in (c.out, c.queue, c.ev, c.ops) if root.exists() for p in root.rglob("*") if p.is_file()}
    if c.pages.exists():
        files[str(c.pages)] = c.pages.stat().st_size
    return files


def test_x_dry_run_deep_in_the_chain_changes_nothing_and_lists_the_remaining_actions(tmp_path):
    c = Chain(dc, tmp_path)
    c.advance_to("S4")
    c.write_caps()
    before = _snapshot(c)
    st = c.poll(dry=True)
    assert [r["state"] for r in st["stages"]] == ["PASS", "PASS", "PASS", "PASS", "HOLD", "NOT_REACHED"], [r["state"] for r in st["stages"]]
    assert _snapshot(c) == before
    assert "A5.HANDOFF" in dc.format_plan(st)


def test_x_the_full_chain_starts_no_process_and_reaches_the_hand_off(tmp_path, monkeypatch):
    c = Chain(dc, tmp_path)
    boom_if_process(monkeypatch)
    c.advance_to("DONE")
    assert c.poll(apply=True)["state"] == "HANDED_OFF"
    assert all(a[0] in ("pr", "workflow") for a in c.gh.acts)


def test_x_gh_act_shapes_and_forbidden_tokens():
    assert dc.argv_deploy(dc.REPO_SLUG) == ["workflow", "run", "deploy.yml", "--repo", dc.REPO_SLUG, "--ref", "main", "-f", "force_all_services=true"]
    assert dc.argv_automerge(dc.REPO_SLUG, 3841, H)[-2:] == ["--match-head-commit", H]
    gh = dc.GhCli(run=lambda *a, **k: (_ for _ in ()).throw(AssertionError("a process was started for a refused argv")))
    for bad in (["workflow", "run", "deploy.yml", "-f", "ci_gate=EMERGENCY-OVERRIDE-CI-NOT-GREEN"], ["pr", "merge", "1", "--admin"], ["workflow", "run", "deploy.yml", "-f", "data_plane_cutover=true"],
                ["repo", "delete", "x"], ["pr", "close", "1"]):
        with pytest.raises(ValueError):
            gh.act(bad)
    for bad in (["api", "repos/other/repo/actions/runs"], ["api", f"repos/{dc.REPO_SLUG}/issues", "-X", "POST"], ["repo", "view"]):
        with pytest.raises(ValueError):
            gh.read(bad)


def test_x_the_action_catalogue_names_an_authority_for_every_action_and_the_code_uses_only_those():
    ids = [a["id"] for a in dc.ACTIONS]
    assert len(set(ids)) == len(ids)
    for a in dc.ACTIONS:
        assert a["authority"].strip() and a["kind"] in ("harness_command", "gh_call", "executor_request", "local_tool", "file_write") and a["stage"] in dc.STAGE_IDS
        assert a["performed_by"] and isinstance(a["retry_safe"], bool)
    assert not next(a for a in dc.ACTIONS if a["id"] == "A2.DEPLOY")["retry_safe"]
    src = SRC.read_text()
    import re
    used = set(re.findall(r'"([AS]?[0-5]\.[A-Z_]+)"', src))
    assert {u for u in used if u[0] == "A"} <= set(ids), sorted({u for u in used if u[0] == "A"} - set(ids))
    assert subprocess.run([sys.executable, str(SRC), "--list-actions"], capture_output=True, text=True).stdout.count("authority:") == len(ids)


def test_x_only_the_two_seams_start_processes():
    """The single `subprocess.run` use is behind GhCli._call and Tools.run; nothing else in the module starts a process."""
    src = SRC.read_text()
    assert "subprocess.run(" not in src               # both seams hold `subprocess.run` as an injectable default and call it only as self._run(...)
    assert src.count("self._run(") == 2
    assert "os.system" not in src and "Popen" not in src and "shell=True" not in src


def test_x_config_is_validated(tmp_path):
    c = Chain(dc, tmp_path)
    for mutate, text in ((lambda d: d["trial"].update(head="nothex"), "trial.head"), (lambda d: d.update(chart_id="362f9f17-0000-0000-0000-000000000000x"), "chart_id"),
                         (lambda d: d["pr"].update(repo="evil/repo"), "pr.repo"), (lambda d: d["trial"]["arm"].update(argv=["a; rm -rf /"]), "trial.arm")):
        c.write_cfg(mutate)
        st = c.poll()
        assert st["kind"] == "CONFIG_INVALID" and text in st["reason"], st["line"]


# ═════════════════════════════════ planted reversions: ONE per gate ═════════════════════════════════
# (gate, oracle, source text, planted replacement).  Each source text occurs exactly once; the mutated module is loaded beside the real one and the oracle MUST fail on it.

REVERSIONS = [
    ("S0 a null check counts as ready", o_s0_null_check_holds_and_no_tr, 'c["id"] for c in checks if c.get("value") is not True', 'c["id"] for c in checks if c.get("value") is False'),
    ("S0 the file for another head is accepted", o_s0_other_head_holds, 'if doc.get("head_sha") != ctx.H:\n        raise Hold("S0_STALE_HEAD"', 'if False:\n        raise Hold("S0_STALE_HEAD"'),
    ("S0 a missing check is accepted", o_s0_missing_check_holds, "if sorted(ids) != sorted(TRIAL_IDS):", "if False:"),
    ("S0 the file's own ready is trusted", o_s0_claimed_ready_is_not_trusted, 'c["id"] for c in checks if c.get("value") is not True', 'c["id"] for c in checks if False'),
    ("S0 the TR is armed on any poll (before ready)", o_s0_null_check_holds_and_no_tr, "    ready = stage(\"S0\", s0)", "    act_arm_tr(ctx); ready = stage(\"S0\", s0)"),
    ("S1 a null gate counts as passed", o_s1_null_gate_holds_and_nothing_merges, 'and gates[g].get("value") is True))', 'and gates[g].get("value") is not False))'),
    ("S1 the verdict need not cite this trial_ready", o_s1_unbound_verdict_holds, 'if doc.get("trial_ready_sha256") != ready["trial_ready_sha256"]:', "if False:"),
    ("S1 a DIAGNOSTIC run counts", o_s1_diagnostic_is_no_evidence, 'if doc.get("qualifying") is not True or str(doc.get("label") or "").upper() == "DIAGNOSTIC":', "if False:"),
    ("S1 RV-INT need not be ACCEPTED", o_s1_rvint_not_accepted_holds, 'if pv.get("verdict") != "ACCEPTED":', "if False:"),
    ("S1 RV-INT of another head counts", o_s1_rvint_other_head_holds, 'if pv.get("head") != ctx.H:', "if False:"),
    ("S1 a moved PR head is merged", o_s1_pr_head_moved_is_never_merged, 'if pr.get("headRefOid") != ctx.H:', "if False:"),
    ("S1 the merge is not bound to H", o_s1_pass_enqueues_the_bound_merge_once, '"--match-head-commit", head]', "]"),
    ("S1 the merge is enqueued again every poll", o_s1_pass_enqueues_the_bound_merge_once,
     'a = next(x for x in ACTIONS if x["id"] == action_id)\n    if ctx.read_marker(marker_name) is not None:', 'a = next(x for x in ACTIONS if x["id"] == action_id)\n    if False:'),
    ("S2 a merge commit off main is accepted", o_s2_not_on_main_holds, 'if st not in ("identical", "behind"):', "if False:"),
    ("S2 red main CI is accepted", o_s2_red_ci_holds_and_no_deploy, 'if last.get("conclusion") != "success":\n            raise Hold("S2_CI_RED"', 'if False:\n            raise Hold("S2_CI_RED"'),
    ("S2 the deploy is dispatched without looking at CI", o_s2_red_ci_holds_and_no_deploy, "ev.update(check_ci(ctx, m, runs))", "pass"),
    ("S2 an older dispatch run counts as the deploy", o_s2_deploy_is_a_new_run_not_an_older_dispatch, 'and r.get("id") not in old)', "and True)"),
    ("S2 a deploy with an unknown outcome is repeated", o_s2_deploy_is_never_repeated, 'if not a["retry_safe"]:', "if False:"),
    ("S2 the deployed image need not carry M", o_s2_image_must_carry_m, "if commit != m:", "if False:"),
    ("S2 a DIFFERS decision is accepted", o_s2_differs_holds_with_the_tables_action, "    judge_decision(d, trial_rec, main_rec)\n", "    pass\n"),
    ("S2 a decision about other records is reused", o_s2_decision_about_other_records_is_recomputed,
     'return d.get("trial_record_sha") != sc.sha256_file(trial_rec) or d.get("main_record_sha") != sc.sha256_file(main_rec)', "return False"),
    ("S2 a main record of another commit counts", o_s2_main_record_of_another_commit_holds, 'if (d.get("E6") or {}).get("commit") != m:', "if False:"),
    ("S2 a tampered EQUAL decision is trusted", o_s2_tampered_equal_decision_holds, 'if wrong or per.get("E3b_coverage") != "ok":', "if False:"),
]
REVERSIONS += [
    ("S3 the executor need not be at M", o_s3_executor_not_at_m_holds, 'if not isinstance(c, dict) or c.get("main_revision") != m or', "if not isinstance(c, dict) or False or"),
    ("S3 a busy production slot is accepted", o_s3_busy_slot_holds, 'if c.get("production_slot") != "free":', "if False:"),
    ("S3 a rebind of another head counts", o_s3_rebind_other_head_holds, 'if d.get("main_head") != m:', "if False:"),
    ("S3 staged files edited after the rebind are accepted", o_s3_staged_edited_after_rebind_holds, 'or d.get("staged_sha256") != sha_dir(sd):', "or False:"),
    ("S3 a stale pin is accepted", o_s3_stale_pin_holds, 'and t.get("reviewed_commit") != m:\n            stale.append', "and False:\n            stale.append"),
    ("S3 rehearsal flags are ignored", o_s3_rehearsal_flags_hold, 'if rep.get("flags") != []:', "if False:"),
    ("S3 a control that admitted its defect is ignored", o_s3_control_that_admitted_its_defect_holds, 'any(c.get("ok") is not True for c in controls if isinstance(c, dict))', "False"),
    ("S3 an unadmitted template is dispatched", o_s3_unadmitted_template_holds, "if not (isinstance(v, dict) and v.get(\"admitted\") is True):", "if False:"),
    ("S3 a rehearsal of another main is reused", o_s3_rehearsal_of_another_main_is_not_reused, 'return json.loads(p.read_text(encoding="utf-8")).get("main") != m', "return False"),
    ("S3 the dispatch request is queued again every poll", o_s3_green_queues_the_pack_template_byte_for_byte_once,
     '    if ctx.read_marker(marker_name) is not None:\n        if target.exists() and target.read_bytes() != doc_bytes:', '    if False:\n        if target.exists() and target.read_bytes() != doc_bytes:'),
    ("S4 completion without LAUNCHED evidence counts", o_s4_receipt_without_launch_evidence_holds, 'launch.get("status") != "LAUNCHED" or', "False or"),
    ("S4 a RUNNING build counts as complete", o_s4_running_build_holds_and_no_verification, 'if e.get("outcome") != "SUCCEEDED":', "if False:"),
    ("S4 an execution of another run counts", o_s4_execution_of_another_run_holds,
     'if "--run-id" not in args or args[args.index("--run-id") + 1:][:1] != [run_id]:', "if False:"),
    ("S4 only one verification shard is launched", o_s4_succeeded_launches_all_shards_in_the_same_poll, "    for op, raw in loaded:  ", "    for op, raw in loaded[:1]:  "),
    ("S5 a verification receipt of another commit counts", o_s5_verification_of_another_commit_holds,
     'if rec.get("reviewed_commit") != m:\n            raise Hold("S5_VERIFY_OTHER_COMMIT"', 'if False:\n            raise Hold("S5_VERIFY_OTHER_COMMIT"'),
    ("S5 the aggregate detector is skipped", o_s5_aggregate_without_g6_holds, "sc.check_aggregate(adopted, ctx.ops, scratch)", "pass"),
    ("S5 another generation's adopted file is overwritten/accepted", o_s5_adopted_file_of_another_generation_is_never_overwritten,
     'if isinstance(cur, dict) and (cur.get("generation"), cur.get("head")) == (adopted["generation"], adopted["head"]):', "if isinstance(cur, dict):"),
    ("X a hard hold pages on every poll", o_x_a_hard_hold_pages_once_per_reason, 'f"stage={stage_id} code={h.code} r={tag}"', 'f"stage={stage_id} code={h.code} r={tag}{ctx.now.timestamp()}"'),
    ("X a soft hold pages immediately", o_x_a_soft_hold_pages_only_after_the_stall_limit, "if first is not None and (ctx.now - first).total_seconds() > stall_s:", "if first is not None:"),
    ("X dry-run writes the status file", o_x_dry_run_writes_nothing, "    if not dry:\n        out.mkdir(parents=True, exist_ok=True)", "    if True:\n        out.mkdir(parents=True, exist_ok=True)"),
]


def mutated(tmp_path, old, new):
    text = SRC.read_text()
    assert text.count(old) == 1, f"the planted reversion's source text occurs {text.count(old)} times: {old[:80]!r}"
    path = tmp_path / "mutant" / "dispatch_chain.py"
    path.parent.mkdir(parents=True)
    path.write_text(text.replace(old, new))
    return _load(f"dispatch_chain_mutant_{abs(hash(old)) % 10**8}", path)


@pytest.mark.parametrize("gate,oracle,old,new", REVERSIONS, ids=[r[0] for r in REVERSIONS])
def test_planted_reversion_fails_its_gates_oracle(tmp_path, gate, oracle, old, new):
    oracle(dc, tmp_path / "real")                                                  # the oracle passes on the real module ...
    m = mutated(tmp_path, old, new)
    with pytest.raises(AssertionError):                                            # ... and FAILS (an assertion, not a crash) with the one gate reverted
        oracle(m, tmp_path / "mut")


def test_gh_act_forbidden_tokens_planted_reversion(tmp_path):
    m = mutated(tmp_path, 'FORBIDDEN_GH_TOKENS = ("--admin", "ci_gate", "data_plane_cutover", "--delete-branch", "--force", "EMERGENCY-OVERRIDE-CI-NOT-GREEN")', "FORBIDDEN_GH_TOKENS = ()")
    gh = m.GhCli(run=lambda *a, **k: type("P", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    gh.act(["workflow", "run", "deploy.yml", "-f", "ci_gate=EMERGENCY-OVERRIDE-CI-NOT-GREEN"])            # the reverted guard lets it through ...
    with pytest.raises(ValueError):                                                                           # ... and the real one does not
        dc.GhCli(run=lambda *a, **k: None).act(["workflow", "run", "deploy.yml", "-f", "ci_gate=EMERGENCY-OVERRIDE-CI-NOT-GREEN"])


def test_x_a_missing_config_holds_and_pages_once(tmp_path):
    pages = tmp_path / "PAGES.log"
    for _ in range(2):
        st = dc.run(tmp_path / "none.json", tmp_path / "ops", tmp_path / "out", pages)
        assert st["kind"] == "CONFIG_NO_INPUT"
    assert len([ln for ln in pages.read_text().splitlines() if "PAGE CHAIN-HOLD key=config" in ln]) == 1
