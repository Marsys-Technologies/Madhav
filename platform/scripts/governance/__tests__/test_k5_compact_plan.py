"""K5-2-NB-02: source acceptance cannot substitute for the compact parent join.

The committed plan is input to the real tracker, not a prose checklist. Reverting
its decomposition must allow the old branch completion through and fail here.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform/scripts/governance"))
from pravaha_tracker.completion import evidence_requirements  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402
from pravaha_tracker.server import check_model  # noqa: E402

CHILDREN = (
    "K5-2-representation",
    "K5-2-compiler",
    "K5-2-null",
    "K5-2-contract",
    "K5-2-qualify",
)


def model():
    return json.loads((ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text())


def snapshot(plan, *, pending=(), admission=None):
    """Synthetic guarded completions, including the historical parent source claim.

    This tests status derivation, which consumes already-guarded events; it does
    not create acceptance receipts or bypass the guard in the running tracker.
    """
    events = []
    for row in plan["items"]:
        iid = row["id"]
        if iid in pending or iid in ("D-COMPACT", "K5-2b", "K5-2-NB-02"):
            continue
        if row.get("done_by") == "decision":
            events.append(dict(kind="decision", decision=iid, actor="steward",
                               state="decided", outcome="approved", ts="2026-10-16T00:00:00Z"))
        else:
            events.append(dict(kind="item", item=iid, actor="steward", state="done",
                               guarded=True, evidence="synthetic independently accepted input",
                               ts="2026-10-16T00:00:00Z"))
    if admission:
        events.append(dict(kind="decision", decision="D-COMPACT", actor="steward",
                           state="decided", outcome=admission, ts="2026-10-16T00:01:00Z"))
    # All branch/file detectors match: a child still needs its own acceptance.
    measured = {iid: {"status": "done", "detail": "source branch or evidence file exists",
                      "checked_at": "2026-10-16T00:00:00Z"}
                for iid in ("K5-2", *CHILDREN)}
    view = build_snapshot(plan, events, measured, {}, {})
    return {row["id"]: row for track in view["tracks"] for row in track["items"]}


@pytest.mark.parametrize("pending", (*CHILDREN, "D-VC"))
def test_parent_waits_for_each_child_and_original_dependency_despite_source_completion(pending):
    rows = snapshot(model(), pending=(pending,))
    assert rows["K5-2"]["status"] == "waiting", "isolated source acceptance cannot complete K5-2"
    assert rows["K5-2"]["source"] == "join"
    assert pending in rows["K5-2"]["deps_open_strict"]
    assert rows["D-COMPACT"]["status"] == "waiting"


def test_join_unlocks_admission_only_after_all_children_and_keeps_the_refusal_path():
    plan = model()
    rows = snapshot(plan)
    assert rows["K5-2"]["source"] == "join"
    assert rows["K5-2"]["status"] == "done"
    assert rows["D-COMPACT"]["status"] == "ready"
    assert rows["K5-2b"]["status"] == "waiting"
    assert snapshot(plan, admission="refused")["K5-2b"]["status"] == "not_applicable"


def test_children_are_individually_guarded_and_runtime_evidence_is_separate_from_code():
    plan = model()
    items = {row["id"]: row for row in plan["items"]}
    assert set(CHILDREN) <= items.keys(), "register every independently reviewable deliverable"
    assert set(items["K5-2"]["depends_on"]) == {"D-VC", *CHILDREN}
    for iid in CHILDREN:
        child = items[iid]
        assert child["brief"]["owns"] and child["brief"]["tests"] and child["detector"]
        requirements = evidence_requirements(plan, child)
        assert requirements and requirements["conflict"] is None
        assert "K5-2" not in child["depends_on"], "a child cannot depend on its own parent join"
    assert all(items[iid]["completion_kind"] == "code" for iid in CHILDREN[:-1])
    assert items["K5-2-qualify"]["completion_kind"] == "artifact"
    assert set(CHILDREN[:-1]) <= set(items["K5-2-qualify"]["depends_on"])
    assert items["K5-2-qualify"]["detector"]["path"] == "/Users/Dev/kalayantra/run/COMPACT_CONTRACT_RESULT.json"
    assert items["D-COMPACT"]["depends_on"] == ["K5-2"]
    assert "K5-2" in items["V-K5"]["depends_on"]
    carry = items["K5-2-NB-02"]
    assert carry["depends_on"] == ["K5-2"]
    assert "K5-2-NB-02" not in items["K5-2"]["depends_on"]
    assert evidence_requirements(plan, carry)["conflict"] is None
    assert {*CHILDREN, "K5-2-NB-02"} <= set(items["JOIN-ALL"]["depends_on"])
    assert check_model(plan) == [], "all declarations, dependency references and cycles must validate"


def test_plan_regression_is_in_exactly_one_required_ci_shard():
    from ci_shard import partition, test_files
    shards = partition(test_files(), 5)
    assert sum(Path(__file__).resolve() in shard for shard in shards) == 1
