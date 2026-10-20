"""SR-CANCEL-LANE (surrogate ruling 2026-10-20, finding E1 of review X-20261020T005119Z-verify-w56-pack): every cancel / stall-stop kind runs on its own
executor lane, never behind the production worker or the production fence. One doctrine-grounded oracle per claim; doctrine = the ruling and CLAUDE.md §N.8
(each signal is measured by a detector that can read false). Distinct claims:
L1 a cancel filed while a synchronous production op holds the production worker completes without waiting for it ·
L2 a kind that is not a cancel kind is refused by the lane, never executed · L3 every cancel kind is single-signer (signed-only), never mechanical ·
L4 a cancel that does not target the running execution is refused · L5 every production `*_cancel` kind in the table (main's and the kind batch's) is on the
closed allow-list and routed to the lane.
"""
import datetime as dt
import json
import threading
from pathlib import Path

import pytest

from test_executor_measuring_cancel import CancelWorld, EXEC, OTHER
from test_executor_scheduler_reaper import ALL_CAPS, COMMIT, FLEET, LEASE, TABLE, run_main_one_turn, utc_now

BATCH_TABLE = Path("/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kind-batch/00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json")
LANE_KINDS = ("measuring_cancel", "orchestrator_rebuild_cancel", "century_cancel", "verification_cancel")
RUN = "run-0001"


def enabled(*kinds):
    table = json.loads(json.dumps(TABLE))
    for kind in kinds: table[kind]["enabled"] = True
    return table


class LaneWorld(CancelWorld):
    """CancelWorld whose execute() also stubs the rebuild kinds: `orchestrator_rebuild` blocks on `release` (the long synchronous production op)."""

    def __init__(self, tmp_path, monkeypatch):
        super().__init__(tmp_path, monkeypatch)
        self.table = enabled("orchestrator_rebuild_cancel")
        self.rebuild_started, self.release, self.executed = threading.Event(), threading.Event(), []
        monkeypatch.setattr(self.mod, "load_table", lambda: self.table)

    def execute(self, req, op):
        self.executed.append(req["kind"])
        if req["kind"] == "orchestrator_rebuild":
            self.rebuild_started.set(); assert self.release.wait(30); return 0, "rebuilt\n"
        if req["kind"] == "orchestrator_rebuild_cancel": return 0, "cancel requested\n"
        return super().execute(req, op)

    def rebuild_request(self, oid="a-rebuild", run=RUN):
        return self.request("orchestrator_rebuild", {"run-id": run}, oid=oid)

    def rebuild_cancel_request(self, run=RUN, oid="b-rebuild-cancel"):
        return self.request("orchestrator_rebuild_cancel", {"run-id": run}, oid=oid)

    def request(self, kind, args=None, oid=None):
        production = self.table[kind]["production"]
        req = {"operation_id": oid, "idempotency_key": oid, "item_id": "K9-23", "kind": kind, "requested_by": "adhikarin", "kyd": "KYD-FIXTURE",
               "args": args or {}, "reviewed_commit": COMMIT, "expires_at": (utc_now() + dt.timedelta(hours=1)).isoformat()}
        if production:
            req.update(chart_id=self.mod.CANONICAL_CHART, lease_id=LEASE)
            acceptance = self.mod.ACC / f"{oid}.json"
            req["acceptance_receipt"] = str(acceptance)
            acceptance.write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "operation_id": oid, "reviewed_commit": COMMIT, "ts": self.mod.now(),
                                              "request_sha256": self.mod.request_digest(req), "checks": {"dry_run_passed": True}}))
        return req

    def inflight(self, req):
        (self.mod.INFLIGHT / f"{req['operation_id']}.json").write_text(json.dumps(req))

    def validate(self, req):
        return self.mod.validate(req, self.table, ALL_CAPS)

    def receipt_of(self, oid):
        return json.loads((self.mod.REC / f"{oid}.json").read_text())


@pytest.fixture
def world(tmp_path, monkeypatch):
    return LaneWorld(tmp_path, monkeypatch)


# ───────────────────────── L1 a cancel never waits for the production op it must stop ─────────────────────────
@pytest.mark.parametrize("kind", ["orchestrator_rebuild_cancel", "measuring_cancel"])
def test_l1_a_cancel_completes_while_a_synchronous_production_op_still_holds_the_builder(world, monkeypatch, kind):
    w = world
    finished = {}
    real_acceptance = w.mod.mechanical_acceptance
    def done(req, archived): finished.setdefault(req["operation_id"], threading.Event()).set(); real_acceptance(req, archived)
    monkeypatch.setattr(w.mod, "mechanical_acceptance", done)
    finished["cancel"] = threading.Event()
    (w.mod.REQ / "a-rebuild.json").write_text(json.dumps(w.rebuild_request()))      # sorts first: in flight before the cancel is judged
    cancel = w.rebuild_cancel_request(oid="cancel") if kind == "orchestrator_rebuild_cancel" else w.cancel_request(oid="cancel")
    (w.mod.REQ / "b-cancel.json").write_text(json.dumps(cancel))
    try:
        run_main_one_turn(w, monkeypatch)
        assert w.rebuild_started.wait(10), "the stub rebuild never occupied the production worker"
        assert finished["cancel"].wait(10), "the cancel waited behind the synchronous production op"       # the rebuild is still blocked here
        assert not w.release.is_set() and w.receipt_of("cancel")["status"] == "COMPLETED"
        assert w.receipt_of("a-rebuild")["status"] == "RUNNING"
    finally:
        w.release.set()


# ───────────────────────── L2 the lane refuses anything that is not a cancel kind ─────────────────────────
@pytest.mark.parametrize("kind", ["orchestrator_rebuild", "scheduler_pause", "publish_head", "measuring_cancel_dryrun", "orchestrator_rebuild_teardown", "unknown_cancel"])
def test_l2_a_non_cancel_kind_routed_to_the_cancel_lane_is_refused_and_never_executed(world, monkeypatch, kind):
    w = world
    ran = []
    monkeypatch.setattr(w.mod, "run_one", lambda *a: ran.append(a))
    req = {"operation_id": "op-x", "idempotency_key": "op-x", "kind": kind, "args": {}}
    path = w.mod.INFLIGHT / "op-x.json"; path.write_text(json.dumps(req))
    w.mod.run_cancel_lane(path, req, w.table.get(kind, {}))
    assert ran == [] and w.executed == []
    assert w.receipt_of("op-x")["status"] == "REFUSED" and "not a cancel kind" in w.receipt_of("op-x")["reason"]
    assert not path.exists() and (w.mod.DONE / "op-x.json").exists()


# ───────────────────────── L3 one signer: a cancel is never admitted mechanically ─────────────────────────
@pytest.mark.parametrize("kind", LANE_KINDS)
def test_l3_a_cancel_kind_without_a_signers_acceptance_is_refused_even_with_a_pack_fill(world, kind):
    w = world
    w.table[kind] = dict(w.table["measuring_cancel"], enabled=True)       # the entry's shape is the table's; the kind is under test
    assert kind in w.mod.SIGNED_ONLY_KINDS and w.mod.mechanical_exempt(kind)
    req = w.request(kind, {"execution": EXEC}, oid="op-unsigned")
    req.pop("acceptance_receipt"); req["pack_fill"] = {"pack_manifest_sha256": "0" * 64, "template": {}, "fill_sha256": "0" * 64}
    assert "needs a V1 signer's acceptance, never a mechanical one" in w.validate(req)
    req.pop("pack_fill")
    assert "acceptance receipt missing" in w.validate(req)


# ───────────────────────── L4 a cancel targets the running execution, no other ─────────────────────────
def test_l4_a_rebuild_cancel_for_a_run_that_is_not_in_flight_is_refused(world):
    w = world
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.rebuild_cancel_request())         # nothing is running
    w.inflight(w.rebuild_request())
    assert w.validate(w.rebuild_cancel_request()) is None                                                      # the running run
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.rebuild_cancel_request(run="run-0002", oid="op-other"))
    assert "run-id required" in w.validate(w.request("orchestrator_rebuild_cancel", {}, oid="op-norun"))


def test_l4_the_lane_refuses_a_cancel_of_another_run_before_executing_anything(world):
    w = world
    w.inflight(w.rebuild_request())
    req = w.rebuild_cancel_request(run="run-0002"); w.inflight(req)
    w.mod.run_cancel_lane(w.mod.INFLIGHT / f"{req['operation_id']}.json", req, w.table[req["kind"]])
    assert w.executed == [] and w.receipt_of(req["operation_id"])["status"] == "REFUSED"


def test_l4_a_measuring_cancel_of_another_execution_is_refused_on_the_lane(world):
    w = world
    req = w.cancel_request(target=OTHER, oid="op-other-exec"); w.inflight(req)
    w.mod.run_cancel_lane(w.mod.INFLIGHT / "op-other-exec.json", req, w.table["measuring_cancel"])
    assert w.executed == [] and w.receipt_of("op-other-exec")["status"] == "REFUSED"
    assert "not the execution named" in w.receipt_of("op-other-exec")["reason"]


# ───────────────────────── L5 table coverage: a `_cancel` kind added to the table must join the lane ─────────────────────────
TABLES = [pytest.param(TABLE, id="main"),
          pytest.param(json.loads(BATCH_TABLE.read_text())["ops"] if BATCH_TABLE.exists() else {}, id="kind-batch",
                       marks=pytest.mark.skipif(not BATCH_TABLE.exists(), reason="the kind-batch copy is gone: its kinds are in main's table (the `main` case)"))]


@pytest.mark.parametrize("ops", TABLES)
def test_l5_every_production_cancel_kind_in_the_table_is_on_the_lane_allow_list_and_routed_to_it(world, ops):
    w = world
    cancels = sorted(k for k, v in ops.items() if k.endswith("_cancel") and v.get("production") is True)
    assert cancels, "the table has no production cancel kind: the test would prove nothing"
    for kind in cancels:
        assert kind in w.mod.CANCEL_LANE_KINDS, f"{kind} is a production cancel kind that is not on the cancel lane's allow-list"
        pool, work = w.mod.pool_for({"kind": kind}, True, "readers", "builder", "cancel-lane")
        assert (pool, work) == ("cancel-lane", w.mod.run_cancel_lane)
    assert w.mod.CANCEL_LANE_KINDS == frozenset(LANE_KINDS)                                           # the list is closed
    assert w.mod.pool_for({"kind": "orchestrator_rebuild"}, True, "readers", "builder", "cancel-lane")[0] == "builder"
    assert w.mod.pool_for({"kind": "measuring_cancel_dryrun"}, False, "readers", "builder", "cancel-lane")[0] == "readers"
