"""SR-TEARDOWN-COMPLETION (option 1): the executor publishes a teardown's <op>.completion.json from a COMMITTED teardown receipt plus an
ACCEPTED absence receipt that binds that receipt's digest, without a fence.

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8: each verdict comes from
a detector that can read false). The verdict is the reviewed policy's own `absence_evidence` (platform/scripts/v5_small_test_shared.py, read here
from the working copy exactly as the executor reads it from the reviewed commit); these tests never re-implement it. Each oracle names the single
planted reversion (an exact line of executor.py, applied to a copy) that makes it FAIL.
  T1 COMMITTED teardown + ACCEPTED absence binding its digest      -> <op>.completion.json published, and the tracker's own consumer
     (cli._teardown_completion_published, the SR-TEARDOWN-COMPLETION option 3 rule) reads it as complete
       reversion: the call site in the loop is dropped from `publish_teardown_completions` (the publisher publishes nothing)
  T2 absence not ACCEPTED / bound to a different teardown digest   -> nothing published
       reversion: the policy verdict is ignored (every candidate counts as observed)
  T3 teardown not COMMITTED (FAILED, RUNNING, rolled back proof)  -> nothing published
       reversion: the AWAITING_ABSENCE status gate is dropped
  T4 the publisher never writes the fence                         -> FENCE absent stays absent; a present fence is byte-identical, not removed
       reversion: the publisher writes FENCE
  T5 main() runs the publisher every turn WITHOUT a fence held (one real turn of main(), the loop's sleep stopping it)
       reversion: the call is moved under the `if FENCE.exists()` branch
Each oracle is one function `oracle_tN(w)`; it passes on the real executor.py and `test_revert_proof` shows it FAILS on the reverted copy.
"""
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
EXECUTOR_PY = FLEET / "executor.py"
POLICY_PY = REPO / "platform/scripts/v5_small_test_shared.py"
RUN_ID = "9b8a3c01-6eb9-4679-9434-680c29cf7492"
TEARDOWN_TS = "2026-10-19T00:35:46+00:00"
ABSENCE_TS = "2026-10-19T00:42:20+00:00"
COMMIT = "b" * 40

CALL = "        publish_teardown_completions()        # SR-TEARDOWN-COMPLETION: a committed teardown + its accepted absence complete without a fence\n"
FENCE_LINE = "        if FENCE.exists(): fence_quiescent()  # reconcile independent small-test completion; retain the owner-controlled fence\n"


class Stop(Exception): pass


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def load_policy():
    namespace = {"__name__": "reviewed_smalltest_policy", "__file__": "reviewed_smalltest_policy.py"}
    exec(compile(POLICY_PY.read_text(), "reviewed small-test evidence policy", "exec"), namespace)
    return namespace


POLICY = load_policy()
COUNTS = {t: 0 for t in {t for t, _ in POLICY["ABSENCE_TABLES"]} | {
    "kala_gochara_publication", "build_runs", "build_run_assets", "asset_provenance_receipts", "asset_freshness", "asset_throughput",
    "ka_gochara_eval_window_record", "ka_gochara_record_prerequisite", "ka_gochara_eval_window_verification",
    "ka_gochara_search_inventory_verification", "owned_test_runs"}}


def committed_receipt(**over):
    """A committed measuring-teardown receipt in the executor's wire format (executor.receipt)."""
    return {"operation_id": "J-3d.teardown", "kind": "measuring_teardown", "item_id": "J-3d", "status": "AWAITING_ABSENCE",
            "exit_code": 0, "request_sha256": "4" * 64, "requested_by": "adhikarin", "reviewed_commit": COMMIT, "ts": TEARDOWN_TS,
            "teardown": {"schema": "ky.measuring_teardown/1", "status": "COMMITTED_AWAITING_ABSENCE",
                         "scope": {"run_id": RUN_ID, "chart_id": POLICY["CHART_ID"], "generation": POLICY["GENERATION"]},
                         "scope_sha256": "5" * 64, "rowset_sha256": "6" * 64}, **over}


class World:
    def __init__(self, tmp, mutations=()):
        text = EXECUTOR_PY.read_text()
        for old, new in mutations:
            if text.count(old) != 1: raise RuntimeError(f"mutation anchor not unique: {old!r}")     # a bad anchor is never a failed oracle
            text = text.replace(old, new)
        path = tmp / "executor_under_test.py"
        path.write_text(text)
        saved = os.environ.get("KY_ROOT")
        os.environ["KY_ROOT"] = str(tmp / "ky")
        try:
            spec = importlib.util.spec_from_file_location(f"ky_exec_teardown_{abs(hash((str(tmp), tuple(mutations))))}", path)
            self.mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        finally:
            os.environ.pop("KY_ROOT", None) if saved is None else os.environ.__setitem__("KY_ROOT", saved)
        m = self.mod
        for d in (m.REQ, m.REC, m.DONE, m.ACC, m.INFLIGHT, m.TMP, m.KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
        m.smalltest_policy = lambda req: POLICY          # the reviewed policy, from the working copy instead of `git show <reviewed_commit>`
        self.committed = committed_receipt()

    def write_committed(self, committed=None):
        self.committed = committed or self.committed
        (self.mod.REC / f"{self.committed['operation_id']}.json").write_text(json.dumps(self.committed))

    def write_absence(self, committed=None, *, ts=ABSENCE_TS, accepted_over=None, absence_over=None, opid="J-3d.absence"):
        """The independent absence readback of `committed`: receipt + measured output + content acceptance by v1."""
        committed = committed or self.committed
        m = self.mod
        measured = {"counts": COUNTS, "run_id": RUN_ID, "schema": "ky.smalltest_independent_absence/1", "baseline": False,
                    "chart_id": POLICY["CHART_ID"], "generation": POLICY["GENERATION"], "scope_sha256": "5" * 64, "rowset_sha256": "6" * 64,
                    "registry_inert": True, "teardown_operation_id": committed["operation_id"],
                    "teardown_receipt_sha256": POLICY["evidence_digest"](committed), "teardown_request_sha256": committed["request_sha256"]}
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
        writer.writerow(["absence_proof"]); writer.writerow([json.dumps(measured)])
        output = m.REC / f"{opid}.output.txt"
        output.write_text(buffer.getvalue())
        output_sha = sha(output.read_bytes())
        absence = {"operation_id": opid, "kind": "readback_sql", "item_id": "J-3d", "status": "COMPLETED", "exit_code": 0,
                   "request_sha256": "7" * 64, "requested_by": "adhikarin", "reviewed_commit": COMMIT, "output_file": str(output),
                   "output_sha256": output_sha, "ts": ts, **(absence_over or {})}
        (m.REC / f"{opid}.json").write_text(json.dumps(absence))
        accepted = {"by": "v1", "result": "ACCEPTED", "operation_id": opid, "request_sha256": "7" * 64, "reviewed_commit": COMMIT,
                    "absence": {**measured, "output_sha256": output_sha}, **(accepted_over or {})}
        (m.ACC / f"{opid}.absence.json").write_text(json.dumps(accepted))

    @property
    def completion(self):
        return self.mod.REC / f"{self.committed['operation_id']}.completion.json"


@pytest.fixture
def world(tmp_path):
    w = World(tmp_path)
    w.write_committed(); w.write_absence()
    return w


def tracker_consumer():
    sys.path.insert(0, str(REPO / "platform/scripts/governance"))
    try:
        from pravaha_tracker import cli
    finally:
        sys.path.pop(0)
    return cli._teardown_completion_published


# ---------------------------------------------------------------------------------------------------- oracles

def oracle_t1(w):
    w.write_committed(); w.write_absence()
    receipt_bytes = (w.mod.REC / "J-3d.teardown.json").read_bytes()
    w.mod.publish_teardown_completions()
    assert w.completion.exists(), "a COMMITTED teardown with an ACCEPTED bound absence published no completion"
    doc = json.loads(w.completion.read_text())
    assert doc["schema"] == "ky.measuring_completion/1" and doc["status"] == "COMPLETED"
    assert (doc["operation_id"], doc["request_sha256"], doc["run_id"]) == ("J-3d.teardown", "4" * 64, RUN_ID)
    assert doc["commit_receipt_sha256"] == sha(receipt_bytes), "the completion must bind the immutable commit receipt's bytes"
    assert doc["absence_receipt"] == {"name": "J-3d.absence.json", "sha256": sha((w.mod.REC / "J-3d.absence.json").read_bytes())}
    assert (w.mod.REC / "J-3d.teardown.json").read_bytes() == receipt_bytes
    # the tracker's rule (option 3, cli._teardown_completion_published) consumes exactly this document
    assert tracker_consumer()(json.loads(receipt_bytes), str(w.mod.REC), sha(receipt_bytes)) is True


def oracle_t2(w):
    w.write_committed(); w.write_absence(accepted_over={"result": "REJECTED"})
    w.mod.publish_teardown_completions()
    assert not w.completion.exists(), "an absence that is not ACCEPTED completed the teardown"


def oracle_t3(w):
    c = committed_receipt(status="COMPLETED")      # the reviewed policy tolerates COMPLETED; only a COMMITTED (AWAITING_ABSENCE) receipt may publish
    w.write_committed(c); w.write_absence(c)
    w.mod.publish_teardown_completions()
    assert not w.completion.exists(), "a teardown receipt that is not the committed AWAITING_ABSENCE one was completed"


def oracle_t4(w):
    w.write_committed(); w.write_absence()
    assert not w.mod.FENCE.exists()
    w.mod.publish_teardown_completions()
    assert w.completion.exists(), "premise: the completion is published"
    assert not w.mod.FENCE.exists(), "publishing a completion created a production fence"


def oracle_t5(w):
    w.write_committed(); w.write_absence()
    m = w.mod
    m.sync = lambda: None; m.refresh_from_main_or_fail_closed = lambda: True; m.load_table = lambda: {}
    m.capabilities = lambda on_main: {}; m.scheduler_backstop_tick = lambda: None; m.scheduler_backstop_records = lambda: []
    def stop(_seconds): raise Stop()
    m.time = type("T", (), {"time": staticmethod(__import__("time").time), "sleep": staticmethod(stop)})
    assert not m.FENCE.exists()
    with pytest.raises(Stop):
        m.main()
    assert w.completion.exists(), "one turn of main() with no fence held did not publish the completion"
    assert not m.FENCE.exists()


ORACLES = {"t1": oracle_t1, "t2": oracle_t2, "t3": oracle_t3, "t4": oracle_t4, "t5": oracle_t5}


@pytest.mark.parametrize("key", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, key):
    ORACLES[key](World(tmp_path))


# ---------------------------------------------------------------------------------------------------- siblings of the claims (same detectors, other inputs)

def test_t1_publication_is_idempotent_and_the_smalltest_family_is_covered(world, tmp_path):
    world.mod.publish_teardown_completions()
    first = world.completion.read_bytes()
    world.mod.publish_teardown_completions()
    assert world.completion.read_bytes() == first
    (tmp_path / "other").mkdir()
    other = World(tmp_path / "other")
    c = committed_receipt(operation_id="J-2b.teardown", kind="smalltest_teardown",
                          teardown={**committed_receipt()["teardown"], "schema": "ky.smalltest_teardown/1"})
    other.write_committed(c); other.write_absence(c)
    other.mod.publish_teardown_completions()
    assert json.loads(other.completion.read_text())["schema"] == "ky.smalltest_completion/1"


@pytest.mark.parametrize("accepted_over", [{"by": "adhikarin"}, {"request_sha256": "8" * 64}])
def test_t2_other_unaccepted_absences_publish_nothing(world, accepted_over):
    world.write_absence(accepted_over=accepted_over)
    world.mod.publish_teardown_completions()
    assert not world.completion.exists()


def test_t2_an_absence_bound_to_a_different_teardown_digest_publishes_nothing(world):
    world.write_absence(committed_receipt(reason="a different receipt"))      # honestly bound to ANOTHER receipt's digest
    world.mod.publish_teardown_completions()
    assert not world.completion.exists()


def test_t2_no_absence_at_all_publishes_nothing(world):
    (world.mod.ACC / "J-3d.absence.absence.json").unlink()
    world.mod.publish_teardown_completions()
    assert not world.completion.exists()


@pytest.mark.parametrize("change", [{"status": "FAILED"}, {"status": "RUNNING"}, {"exit_code": 1},
                                   {"teardown": {**committed_receipt()["teardown"], "status": "ROLLED_BACK"}}])
def test_t3_other_non_committed_teardowns_publish_nothing(world, change):
    c = committed_receipt(**change)
    world.write_committed(c); world.write_absence(c)      # an absence honestly bound to THIS receipt: only the commit state is wrong
    world.mod.publish_teardown_completions()
    assert not world.completion.exists()


def test_t4_a_present_fence_is_left_byte_identical(world):
    world.mod.FENCE.write_text(json.dumps({"operation_id": "J-3c.dispatch", "request_sha256": "9" * 64, "ts": "2026-10-19T00:00:00+00:00"}))
    before = world.mod.FENCE.read_bytes()
    world.mod.publish_teardown_completions()
    assert world.completion.exists() and world.mod.FENCE.read_bytes() == before


# ---------------------------------------------------------------------------------------------------- revert proofs (ONE planted reversion per claim)

REVERSIONS = {
    "t1": ('commit_receipt_sha256=digest_bytes(commit_bytes), run_id=observed["run_id"],\n                    scope_sha256=observed["scope_sha256"], rowset_sha256=observed["rowset_sha256"],\n                    absence_receipt=proof["absence_receipt"], absence_acceptance=proof["absence_acceptance"])\n                target =',
           'commit_receipt_sha256=digest_bytes(b""), run_id=observed["run_id"],\n                    scope_sha256=observed["scope_sha256"], rowset_sha256=observed["rowset_sha256"],\n                    absence_receipt=proof["absence_receipt"], absence_acceptance=proof["absence_acceptance"])\n                target ='),
    "t2": ('                try: observed = policy["absence_evidence"](proof, OPS, teardown_receipt=committed)\n                except Exception: continue\n',
           f'                observed = {{"run_id": "{RUN_ID}", "scope_sha256": "5", "rowset_sha256": "6"}}\n'),
    "t3": ('committed.get("status") != "AWAITING_ABSENCE"\n                    or committed.get("operation_id") != path.stem',
           'False\n                    or committed.get("operation_id") != path.stem'),
    "t4": ('                log(f"{path.stem} teardown completion published (absence {absence.stem})")\n',
           '                FENCE.write_text(json.dumps({"operation_id": path.stem, "ts": now()}))\n'),
    "t5": (CALL + "", ""),
}


@pytest.mark.parametrize("key", sorted(REVERSIONS))
def test_revert_proof_the_oracle_fails_on_its_single_planted_reversion(tmp_path, key):
    old, new = REVERSIONS[key]
    mutations = [(old, new)]
    if key == "t5": mutations = [(CALL, ""), (FENCE_LINE, FENCE_LINE.replace("fence_quiescent()", "(fence_quiescent(), publish_teardown_completions())"))]
    with pytest.raises(AssertionError):
        ORACLES[key](World(tmp_path, mutations))
