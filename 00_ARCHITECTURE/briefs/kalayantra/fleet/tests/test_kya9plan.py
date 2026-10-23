"""Amendment A9 plan-model claims, one oracle each (source: KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md).

  §2.1  roots exactly as listed; JOIN-ALL is no dependency of C-1 and lies outside the closure
  §2.2  the closure of those roots over depends_on is deterministic (kyclosure compute). CLOSURE_v3.json itself is CI-generated
        from the reviewed source (SR-CHURN-CUT 3) and not carried in PRs, so every claim below reads the COMPUTED closure
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
sys.path.insert(0, str(REPO / "platform/scripts/governance"))
import generated_paths  # noqa: E402


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
def closure(model, roots):
    return kyclosure.compute(model, roots)      # SR-CHURN-CUT 3: the committed copy may lag the model until CI/refresh regenerates it


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
    assert rendered == kyclosure.render(kyclosure.compute(model, roots))
    assert rendered == generated_paths.closure_bytes(REPO)      # the CI generator and this oracle agree on the bytes


def test_post_flip_phase_depends_on_the_flip_and_is_counted(items, closure):  # §3.1
    for iid in kya9plan.POST_FLIP:
        assert "J-6l" in items[iid]["depends_on"], iid
        assert iid in closure["closure"], iid
        assert items[iid]["triage"]["class"] == "a", iid


def test_k_avadhi_c_is_in_the_closure(closure):  # §3.2
    assert "K-AVADHI-C" in closure["closure"]


def test_no_closure_member_waits_on_a_deferred_or_retired_item(items, closure):  # §4
    gone = (set(kya9plan.DEFERRED) | set(kya9plan.A9_NB04_DEFERRED) | set(kya9plan.PREP_DEFERRED)
            | {t for _, _, ts in kya9plan.NOT_APPLICABLE for t in ts})
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


def test_prep_deferred_items_are_deferred_outside_c1_and_the_closure(items, closure):  # SR-W34-PREP-RULINGS 5b
    # D-T2 and L0-K (L0-K has no branch yet, D-T2 is parked) would keep C-1 from ever starting; the surrogate deferred both
    # with re-entry 'post-flip'. Fail-on-revert: put either back in C-1.depends_on, or class a, and this reads false.
    for iid in kya9plan.PREP_DEFERRED:
        assert iid not in items["C-1"]["depends_on"], iid
        assert iid not in closure["closure"], iid
        assert items[iid]["triage"]["class"] == "b" and items[iid]["triage"]["re_entry"].startswith("post-flip"), iid
    for iid, cut in kya9plan.PREP_CUT_EDGES.items():
        assert not set(cut) & set(items[iid]["depends_on"]) and not set(cut) & set(items[iid].get("requires_outcome") or {}), iid


# SR-PARKED-OUT-OF-CAMPAIGN (2026-10-22): the ruling names exactly these thirteen; the ruling text is the source, not the script
PARKED_RULING = ["KR-1", "KR-2", "J-7a", "J-7a-pr3099", "J-7a-a62", "J-8", "J-8a", "J-8-b63", "J-8-j3",
                 "J-4a-a25", "J-4a-a26", "J-3a-b44", "L0-K"]


def test_the_thirteen_parked_items_are_deferred_out_of_the_campaign_with_their_re_entry(items, closure):  # SR-PARKED-OUT-OF-CAMPAIGN
    # Fail-on-revert: drop an item from kya9plan.PARKED_OUT_OF_CAMPAIGN (or put it back to class a / empty re-entry) and this reads false.
    assert sorted(kya9plan.PARKED_OUT_OF_CAMPAIGN) == sorted(PARKED_RULING)
    for iid in PARKED_RULING:
        triage = items[iid]["triage"]
        assert triage["class"] == "b" and triage["re_entry"] == kya9plan.PARKED_OUT_OF_CAMPAIGN[iid], iid
        assert "SR-PARKED-OUT-OF-CAMPAIGN" in triage["reason"], iid
        assert iid not in closure["closure"], iid
    assert [(i, d) for i in closure["closure"] for d in items[i]["depends_on"] if d in PARKED_RULING] == []


def test_the_parked_items_are_carried_to_the_post_campaign_list_with_the_same_re_entry(items):  # SR-PARKED-OUT-OF-CAMPAIGN
    # The list is read back, not trusted: every item has a table row ending in its re_entry text from the model.
    rows = {}
    for line in (FLEET.parent / "POST_CAMPAIGN_v1_0.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and len(cells) == 3:
            rows[cells[0]] = cells[2]
    for iid in PARKED_RULING:
        assert rows.get(iid) == items[iid]["triage"]["re_entry"], iid


def test_d_t2_is_closed_by_its_recorded_decision_and_waits_on_nothing(items, closure):  # SR-DT2-CANDIDATE
    # The tracker reads a recorded decision item done only while every dependency is done; L0-K leaves the campaign, so the edges go.
    assert items["D-T2"]["depends_on"] == [] and "D-T2" not in closure["closure"]



def test_the_committed_model_is_the_fixed_point_of_the_plan_script(model):  # SR-AUDIT-NA-TIMEOUT / SR-AUDIT-BOOKKEEPING
    # Fail-on-revert: drop an `if ... not in items` guard in kya9plan (a second run then appends the retirement items again) or
    # hand-edit the model away from the script's output, and this reads false.
    once = kya9plan.apply_model_edits(model)
    assert once == model
    assert kya9plan.apply_model_edits(once) == once
    ids = [i["id"] for i in model["items"]]
    assert len(ids) == len(set(ids)) and len([d["id"] for d in model["decisions"]]) == len({d["id"] for d in model["decisions"]})


def test_the_two_timeout_items_are_retired_by_the_existing_decision_outside_the_closure(items, model, closure):  # SR-AUDIT-NA-TIMEOUT (R1)
    # Source: audit R1 text, carried verbatim as the reason. The fold-out (owner: add nothing to the tracker) removed the retirement
    # item #3896 added; the pair reads not_applicable through requires_outcome on the existing decision item D-GOCHARA-TIMEOUT.
    # Fail-on-revert: put either item back to class b (deferred), restore the folded-out decision, or drop the requirement.
    for iid in kya9plan.TIMEOUT_NA_TARGETS:
        assert items[iid]["triage"] == {"class": "retired", "decision": "D-GOCHARA-TIMEOUT", "reason": kya9plan.TIMEOUT_NA_REASON}, iid
        assert iid not in closure["closure"], iid
    assert items["J-GOCHARA-TIMEOUT"]["requires_outcome"] == {"D-GOCHARA-TIMEOUT": "approved"}
    assert "requires_outcome" not in items["D-GOCHARA-TIMEOUT"]       # a decision cannot require itself (the plan has no cycles)
    assert "Re-entry: if J-4f shows a timeout binding" in kya9plan.TIMEOUT_NA_REASON and "1395" in kya9plan.TIMEOUT_NA_REASON
    assert "D-GOCHARA-TIMEOUT-NA" not in items and "D-GOCHARA-TIMEOUT-NA" not in {d["id"] for d in model["decisions"]}
    assert [(i, d) for i in closure["closure"] for d in items[i]["depends_on"] if d in kya9plan.TIMEOUT_NA_TARGETS] == []


def test_the_fold_out_removes_the_two_decision_items_from_a_model_that_still_has_them(model):  # FOLD-OUT (owner via madhav-44, 2026-10-22)
    # Fail-on-revert: delete the fold-out step in apply_model_edits -> the two items (and the edges onto them) survive, 276 items.
    import copy
    before = copy.deepcopy(model)
    anchor = next(i for i in before["items"] if i["id"] == "D-J4C-PR2907-NA")
    for did in kya9plan.FOLDED_OUT_DECISION_ITEMS:
        before["items"].append({**copy.deepcopy(anchor), "id": did, "decision": did,
                                "triage": {"class": "retire_decision", "retires": "x"}})
    for iid in kya9plan.TIMEOUT_NA_TARGETS:
        for it in before["items"]:
            if it["id"] == iid:
                it["depends_on"] = it["depends_on"] + ["D-GOCHARA-TIMEOUT-NA"]
                it["requires_outcome"] = {**(it.get("requires_outcome") or {}), "D-GOCHARA-TIMEOUT-NA": "approved"}
    before["decisions"].append({"id": "D-GOCHARA-TIMEOUT-NA", "title": "t", "owner": "o", "default": "d"})
    assert len(before["items"]) == 276
    after = kya9plan.apply_model_edits(before)
    assert len(after["items"]) == 274 and after == model
    assert all(d not in i["depends_on"] for i in after["items"] for d in kya9plan.FOLDED_OUT_DECISION_ITEMS)
