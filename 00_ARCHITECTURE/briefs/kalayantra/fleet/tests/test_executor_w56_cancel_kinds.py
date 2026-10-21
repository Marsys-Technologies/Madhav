"""W5W6-READINESS WP2 (brief 02), the executor side of the two K9 cancel kinds: `orchestrator_rebuild_cancel` and `orchestrator_rebuild_cancel_dryrun` are ENABLED in the committed table
(shard W56-WP2-cancel.json). One doctrine-grounded oracle per distinct claim; each has ONE planted reversion that fails (§N.8). Unlike test_executor_cancel_lane.py, which patches the kinds
on in a copy, these oracles read the committed table as shipped.

  C1  the cancel is admitted only for the run-id of the rebuild in flight (SR-CANCEL-LANE): the committed cancel and cancel dry run are admitted for that run-id; another run-id and a request
      with nothing in flight are refused; the cancel is signed-only, never mechanical; it runs on the cancel lane's own worker
  C6  enabling changes nothing else the executor admits (the #3808 layout pattern): the enabled set equals the earlier set plus exactly the kinds this item enables, and each of their entries
      equals the pinned BASE entry with `enabled` flipped, key order unchanged
"""
import json
from pathlib import Path

import pytest

import executor_pin_shards
from test_executor_cancel_lane import LaneWorld, RUN, TABLE
from test_executor_table import BASE_ENABLED_KINDS, ENABLED_KINDS, OPS_FILE, REBUILD_CONTROL_BINDINGS, SHARDS, load_ops

CANCEL_KINDS = ("orchestrator_rebuild_cancel_dryrun", "orchestrator_rebuild_cancel")
TEARDOWN_KINDS = ("orchestrator_rebuild_teardown_dryrun", "orchestrator_rebuild_teardown")
TEARDOWN_SHARD = Path(executor_pin_shards.SHARD_DIR) / "W56-WP2-teardown.json"
ENABLED_HERE = set(CANCEL_KINDS) | (set(TEARDOWN_KINDS) if TEARDOWN_SHARD.exists() else set())      # the teardown pair rides its own shard so the cockpit can hold it (surrogate ruling S-1)


class ShippedWorld(LaneWorld):
    """LaneWorld whose table is the committed executor_ops.json, untouched."""

    def __init__(self, tmp_path, monkeypatch):
        super().__init__(tmp_path, monkeypatch)
        self.table = json.loads(json.dumps(TABLE))

    def cancel_dryrun_request(self, run=RUN, oid="c-cancel-dry"):
        req = self.request("orchestrator_rebuild_cancel_dryrun", {"run-id": run}, oid=oid)
        return req


@pytest.fixture
def world(tmp_path, monkeypatch):
    return ShippedWorld(tmp_path, monkeypatch)


def c1(w):
    assert all(w.table[k]["enabled"] is True for k in CANCEL_KINDS)
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.rebuild_cancel_request())                  # nothing in flight
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.cancel_dryrun_request())
    w.inflight(w.rebuild_request())
    assert w.validate(w.rebuild_cancel_request()) is None                                                              # the in-flight run: admitted
    assert w.validate(w.cancel_dryrun_request()) is None
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.rebuild_cancel_request(run="run-0002", oid="op-other"))
    assert "not the run of an orchestrator_rebuild in flight" in w.validate(w.cancel_dryrun_request(run="run-0002", oid="op-other-dry"))
    req = w.rebuild_cancel_request(oid="op-unsigned")
    req.pop("acceptance_receipt"); req["pack_fill"] = {"pack_manifest_sha256": "0" * 64, "template": {}, "fill_sha256": "0" * 64}
    assert "needs a V1 signer's acceptance, never a mechanical one" in w.validate(req)                                  # signed-only
    assert w.mod.pool_for({"kind": "orchestrator_rebuild_cancel"}, True, "readers", "builder", "cancel-lane") == ("cancel-lane", w.mod.run_cancel_lane)
    assert w.mod.pool_for({"kind": "orchestrator_rebuild_cancel_dryrun"}, False, "readers", "builder", "cancel-lane")[0] == "readers"


def test_c1_the_enabled_cancel_is_admitted_only_for_the_run_in_flight_signed_only_on_the_cancel_lane(world):
    c1(world)


def test_c1_planted_reversion_the_cancel_off_the_lane_allow_list_fails(world, monkeypatch):
    # reversion: orchestrator_rebuild_cancel is removed from CANCEL_LANE_KINDS (it would share the builder worker, behind the rebuild it must stop)
    monkeypatch.setattr(world.mod, "CANCEL_LANE_KINDS", world.mod.CANCEL_LANE_KINDS - {"orchestrator_rebuild_cancel"})
    with pytest.raises(AssertionError):
        c1(world)


def check_c6(ops):
    """AssertionError unless `ops` (a loaded executor_ops table) is the earlier table plus exactly the kinds this item enables."""
    now = {kind for kind, entry in ops.items() if entry["enabled"] is True}
    earlier = executor_pin_shards.enabled_after(BASE_ENABLED_KINDS, [s for s in SHARDS if not str(s["item"]).startswith("W56-WP2")])
    assert now == earlier | ENABLED_HERE, f"enabled set differs: +{sorted(now - earlier - ENABLED_HERE)} -{sorted((earlier | ENABLED_HERE) - now)}"
    assert now == ENABLED_KINDS
    for kind in ENABLED_HERE:
        pinned = {**REBUILD_CONTROL_BINDINGS[kind], "enabled": True}
        assert ops[kind] == pinned and list(ops[kind]) == list(REBUILD_CONTROL_BINDINGS[kind]) and next(iter(ops[kind])) == "enabled", kind
    for kind in set(TEARDOWN_KINDS) - ENABLED_HERE:
        assert ops[kind]["enabled"] is False, kind


def test_c6_enabling_changes_nothing_else_the_executor_admits():
    check_c6(load_ops(OPS_FILE.read_text())["ops"])


def test_c6_planted_reversion_a_fifth_row_flipped_fails():
    ops = load_ops(OPS_FILE.read_text())["ops"]
    flipped = next(k for k, e in ops.items() if e["enabled"] is False and k not in ENABLED_HERE and k not in TEARDOWN_KINDS)
    ops[flipped]["enabled"] = True                                       # reversion: one more row enabled
    with pytest.raises(AssertionError):
        check_c6(ops)
