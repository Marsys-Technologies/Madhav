"""Amendment A9 plan-model claims, one oracle each (source: KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md).

  §2.1  roots exactly as listed; JOIN-ALL is no dependency of C-1 and lies outside the closure
  §2.2  CLOSURE_v3.json is the deterministic closure of those roots over depends_on (kyclosure --check)
  §3.1  the Tier-2 methods and the L5 hand-off depend on J-6l and sit in the closure (not deferred)
  §3.2  K-AVADHI-C is in the closure
  §4    no closure member depends on a deferred or not_applicable item (they could never complete)
  NB-04 (SR-A9-INTERP) J-4a-a25/a26 are deferred and no longer gate J-4a (its brief reads only the settled build);
        J-3a-b44 stays in the closure as class a (J-5q-b54's brief names B4.4)
  §5    K9-4a drops the five retired packet exits and keeps D-FLIP, J-6l, V-J6, K9-23; the plan is acyclic
"""
import json
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
CONTROL = REPO / "00_ARCHITECTURE" / "control" / "kalayantra"
sys.path.insert(0, str(FLEET))
import kya9plan  # noqa: E402
import kyclosure  # noqa: E402


@pytest.fixture(scope="module")
def model():
    return json.loads((CONTROL / "plan_model.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def items(model):
    return {i["id"]: i for i in model["items"]}


@pytest.fixture(scope="module")
def roots():
    return json.loads((CONTROL / "ACCEPTANCE_ROOTS_v3.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def closure():
    return json.loads((CONTROL / "CLOSURE_v3.json").read_text(encoding="utf-8"))


def test_roots_are_exactly_the_listed_ones(roots):  # §2.1
    assert {a["id"]: [r["item"] for r in a["roots"]] for a in roots["acceptances"]} == kya9plan.ROOTS


def test_join_all_is_superseded(items, closure):  # §2.1
    assert "JOIN-ALL" not in items["C-1"]["depends_on"]
    assert "JOIN-ALL" not in closure["closure"]
    assert items["JOIN-ALL"]["requires_outcome"] == {"D-A9-NA-JOIN-ALL": "approved"}


def test_the_close_gates_on_the_acceptance_roots(items, roots):  # §2.1 (I) a rootless C-1 would open the close at once
    first = {r["item"] for a in roots["acceptances"][:3] for r in a["roots"]} | {"V-K9"}
    assert first <= set(items["C-1"]["depends_on"])


def test_closure_is_the_deterministic_closure_of_the_roots(model, roots):  # §2.2
    rendered = kyclosure.render(kyclosure.compute(model, roots))
    assert rendered == (CONTROL / "CLOSURE_v3.json").read_bytes()
    assert rendered == kyclosure.render(kyclosure.compute(model, roots))


def test_post_flip_phase_depends_on_the_flip_and_is_counted(items, closure):  # §3.1
    for iid in kya9plan.POST_FLIP:
        assert "J-6l" in items[iid]["depends_on"], iid
        assert iid in closure["closure"], iid
        assert items[iid]["triage"]["class"] == "a", iid


def test_k_avadhi_c_is_in_the_closure(closure):  # §3.2
    assert "K-AVADHI-C" in closure["closure"]


def test_no_closure_member_waits_on_a_deferred_or_retired_item(items, closure):  # §4
    gone = set(kya9plan.DEFERRED) | set(kya9plan.A9_NB04_DEFERRED) | {t for _, _, ts in kya9plan.NOT_APPLICABLE for t in ts}
    assert not gone & set(closure["closure"])
    assert [(i, d) for i in closure["closure"] for d in items[i]["depends_on"] if d in gone] == []


def test_unread_4_1_evidence_is_deferred_and_no_longer_gates_j_4a(items, closure):  # NB-04
    # J-4a's brief/tests name only the single settled Vimśottarī build; FINAL_BUILD_SCOPE_v1_0 never mentions A2.5/A2.6
    for iid in ("J-4a-a25", "J-4a-a26"):
        assert iid not in closure["closure"] and iid not in items["J-4a"]["depends_on"]
        assert items[iid]["triage"]["class"] == "b" and items[iid]["triage"]["re_entry"]


def test_the_4_1_baseline_is_parked_with_a25_and_outside_the_closure(items, closure):  # SR-A9-NB-04-B44 / SR-CLOSURE-272
    # J-3a-b44 scores the '4.1' baseline, which cannot exist while J-4a-a25 (the '4.1' build) is parked: same re-entry
    assert items["J-3a-b44"]["triage"]["class"] == "b"
    assert items["J-3a-b44"]["triage"]["re_entry"] == items["J-4a-a25"]["triage"]["re_entry"]
    assert "J-3a-b44" not in closure["closure"] and "J-3a-b44" not in items["J-3a"]["depends_on"]


def test_k9_4a_follows_the_flip_without_the_retired_exits(items):  # §5
    deps = set(items["K9-4a"]["depends_on"])
    assert {"D-FLIP", "J-6l", "V-J6", "K9-23"} <= deps
    assert not deps & set(kya9plan.RETIRED_PACKET_EXITS)


def test_the_plan_has_no_dependency_cycle(items):  # §5: V-K9 → K9-6 → K9-4b → K9-4a, so V-K9 cannot gate K9-4a
    state = {}

    def visit(x):
        state[x] = 1
        for d in list(items[x]["depends_on"]) + list(items[x].get("requires_outcome") or {}):
            assert state.get(d) != 1, f"cycle through {x} -> {d}"
            if d not in state:
                visit(d)
        state[x] = 2
    sys.setrecursionlimit(5000)
    for x in items:
        if x not in state:
            visit(x)


def test_every_not_applicable_item_has_a_decision_item_and_entry(model, items):  # tracker mechanism
    decisions = {d["id"] for d in model["decisions"]}
    for did, _reason, targets in kya9plan.NOT_APPLICABLE:
        assert did in decisions and items[did]["done_by"] == "decision"
        for t in targets:
            assert items[t]["requires_outcome"] == {did: "approved"} and did in items[t]["depends_on"]
