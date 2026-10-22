"""Amendment A9 D-51/D-53/D-54: the headline counts over the acceptance closure; deferred items are listed apart;
the not_applicable set is recorded the tracker's own way (a refused retirement decision) and does not spread into
the closure.

Source: 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md §2.3, §4, §5;
CONTROL_PLANE.md ("a final incompatible outcome makes dependent executable work not_applicable").
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from pravaha_tracker import cli
from pravaha_tracker.state import build_snapshot, load_closure

NOW = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"

NOT_APPLICABLE = ["JOIN-ALL", "K-CERT-2", "W4-SAFETY-N01", "W4-SAFETY-N02", "KA3B-N1", "KA3B-N2", "OPS-NB-03",
                  "V-K3b", "V-K5", "V-K6", "V-KA", "V-VC", "J-4c-pr2907",
                  "D-GOCHARA-TIMEOUT", "J-GOCHARA-TIMEOUT"]    # the last two: SR-AUDIT-NA-TIMEOUT (D-GOCHARA-TIMEOUT-NA)
DEFERRED = ["J-7a", "J-7a-a62", "J-7a-pr3099", "KR-1", "KR-2", "J-8", "J-8-b63", "J-8-j3", "J-8a", "K9-5",
            "K9-5-NB-01"]
DEFERRED_NB04 = ["J-4a-a25", "J-4a-a26", "J-3a-b44"]   # SR-A9-INTERP A9-NB-04: no phase brief reads their output;
                                                         # J-3a-b44 added by SR-A9-NB-04-B44 (its 4.1 baseline needs a25)
DEFERRED_PREP = ["D-T2", "L0-K"]    # SR-W34-PREP-RULINGS 5b: deferred with re-entry, outside C-1 and the closure (A9 D-53); the two
                                    # GOCHARA-TIMEOUT items left this list for not_applicable (SR-AUDIT-NA-TIMEOUT)


def _closure(model):
    """The closure of THIS model: a pure function of plan_model.json + ACCEPTANCE_ROOTS (kyclosure.compute). The committed
    CLOSURE_v3.json is CI-generated from main (SR-CHURN-CUT 3), so a model change is pinned against the recomputation."""
    spec = importlib.util.spec_from_file_location("kyclosure", REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/kyclosure.py")
    kyclosure = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = kyclosure     # dataclass-style lookups need the module registered
    spec.loader.exec_module(kyclosure)
    roots = json.loads((REPO / "00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v3.json").read_text(encoding="utf-8"))
    return kyclosure.compute(model, roots)


def _rows(snap):
    return {row["id"]: row for track in snap["tracks"] for row in track["items"]}


def _synthetic():
    def item(iid, deps=(), **extra):
        return {"id": iid, "track": "K", "title": iid, "owner": "K", "depends_on": list(deps), "mandatory": True, **extra}
    model = {"campaign": "t", "tracks": [{"id": "K", "title": "K"}], "streams": [], "phases": [], "decisions": [],
             "items": [item("A"), item("B", ["A"]), item("OUT", triage={"class": "b", "re_entry": "after B"}),
                       item("PLAIN")]}
    return model


def test_headline_counts_only_closure_members_and_lists_deferred_apart():
    # A9 §2.3: "counts ... over the closure's item count; deferred items are listed separately with re-entry"
    closure = {"closure": ["A", "B"], "closure_sha256": "x"}
    overall = build_snapshot(_synthetic(), [], {}, {}, {}, now=NOW, closure=closure)["overall"]
    assert (overall["scope"], overall["total"], overall["done"]) == ("closure", 2, 0)
    assert overall["plan_wide"]["total"] == 4
    assert overall["deferred"] == [{"id": "OUT", "status": "ready", "re_entry": "after B"}]
    assert overall["missing"] == []


def test_headline_without_a_closure_stays_plan_wide():
    # N.7.6: no readable closure → no claim of a scope the tracker cannot read
    overall = build_snapshot(_synthetic(), [], {}, {}, {}, now=NOW)["overall"]
    assert overall["total"] == 4 and "scope" not in overall


def test_a_closure_member_absent_from_the_model_is_reported_not_dropped():
    closure = {"closure": ["A", "GONE"], "closure_sha256": "x"}
    overall = build_snapshot(_synthetic(), [], {}, {}, {}, now=NOW, closure=closure)["overall"]
    assert overall["missing"] == ["GONE"] and overall["total"] == 1


def test_load_closure_reads_the_committed_v3_closure_the_model_names():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    closure = load_closure(model)
    assert closure is not None and closure["closure_count"] == len(closure["closure"])
    assert closure["closure_sha256"] == json.loads(
        (REPO / "00_ARCHITECTURE/control/kalayantra/CLOSURE_v3.json").read_text(encoding="utf-8"))["closure_sha256"]


@pytest.fixture(scope="module")
def decided(tmp_path_factory):
    """The real `decide` command records each A9 retirement decision as refused."""
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    log = tmp_path_factory.mktemp("events") / "EVENTS.jsonl"
    saved = cli.EVENTS, cli.load_model
    cli.EVENTS, cli.load_model = str(log), lambda: model
    try:
        # D-J4C-PR2907-NA: #2907's content landed through #2901 (review X-20261019T150725Z-review-3596-pr2907)
        # D-GOCHARA-TIMEOUT-NA: the legacy v3 materializer timeout, superseded by migration 1395 (SR-AUDIT-NA-TIMEOUT)
        for dec in sorted(d["id"] for d in model["decisions"]
                          if d["id"].startswith(("D-A9-NA-", "D-J4C-PR2907-NA", "D-GOCHARA-TIMEOUT-NA"))):
            assert cli.main(["decide", dec, "--outcome", "refused", "--as", "steward", "--delegated",
                             "--detail", f"A9 {dec}"]) == 0
    finally:
        cli.EVENTS, cli.load_model = saved
    events = [json.loads(line) for line in log.read_text().splitlines()]
    return model, build_snapshot(model, events, {}, {}, {}, now=NOW, closure=_closure(model))


def test_the_twelve_items_become_not_applicable_by_the_recorded_decision(decided):
    # A9 D-51.1, D-53, D-54: each listed item is not_applicable (the reason is its decision's text)
    _, snap = decided
    rows = _rows(snap)
    assert {i: rows[i]["status"] for i in NOT_APPLICABLE} == {i: "not_applicable" for i in NOT_APPLICABLE}


def test_not_applicable_does_not_spread_into_the_closure(decided):
    # A9 §7 + D-54: retiring V-K6 must not retire the live K6-N1..N3 follow-ups or K9-4a; closure has no n/a member
    model, snap = decided
    rows = _rows(snap)
    closure = set(_closure(model)["closure"])
    assert [i for i in closure if rows[i]["status"] == "not_applicable"] == []
    assert all(rows[i]["status"] != "not_applicable" for i in ("K6-N1", "K6-N2", "K6-N3", "K9-4a", "C-1", "J-4c"))
    assert snap["overall"]["not_applicable"] == 0


def test_the_headline_denominator_is_the_closure_and_every_deferred_item_is_listed(decided):
    _, snap = decided
    o = snap["overall"]
    assert o["total"] == 181 and o["plan_wide"]["total"] == 276   # 183 -> 181: VC-1 and VC-2 leave with the retired VC-2 (SR-CLOSE-NOW 5); 275 -> 274: D-KA4B-NB02-NA dropped (SR-CLOSE-NOW.amend-7); 274 -> 276: D-GOCHARA-TIMEOUT-NA and D-J4B-1303-NA declared (SR-AUDIT-NA-TIMEOUT, SR-AUDIT-BOOKKEEPING)
    listed = {d["id"]: d for d in o["deferred"]}
    assert set(DEFERRED + DEFERRED_NB04 + DEFERRED_PREP) <= set(listed)
    assert all(listed[i]["re_entry"] for i in DEFERRED + DEFERRED_NB04 + DEFERRED_PREP)
    assert not set(listed) & {"J-7", "J-7b"}   # D-52: the rest of the post-flip phase is not deferred (D-T2, L0-K are: SR-W34-PREP-RULINGS 5b)


# SR-CLOSE-NOW item 4 (PRE-D-VC default; SR-W34-PREP-RULINGS 4): no consenting evaluation population, so D-VC is
# refused as not_evaluable and the K5-2 trial, the G2 work and the compact stage are not_applicable by the model's own
# semantics. Source for the semantics: CONTROL_PLANE.md ("a final incompatible outcome makes dependent executable work
# not_applicable"); PRE-D-VC / PRE-D-G2 / PRE-D-COMPACT in DECISIONS_SURROGATE.jsonl.
VC_FAMILY = ["K5-2", "K5-2-qualify", "K5-2-representation", "K5-2-compiler", "K5-2-null", "K5-2-contract"]


def _decide(model, tmp_path, outcomes):
    log = tmp_path / "EVENTS.jsonl"
    saved = cli.EVENTS, cli.load_model
    cli.EVENTS, cli.load_model = str(log), lambda: model
    try:
        for dec, outcome in outcomes.items():
            assert cli.main(["decide", dec, "--outcome", outcome, "--as", "steward", "--delegated",
                             "--detail", f"SR-CLOSE-NOW {dec}"]) == 0
    finally:
        cli.EVENTS, cli.load_model = saved
    events = [json.loads(line) for line in log.read_text().splitlines()]
    return build_snapshot(model, events, {}, {}, {}, now=NOW, closure=_closure(model))


def test_refused_d_vc_makes_the_k5_2_trial_g2_and_compact_stage_not_applicable(tmp_path):
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    rows = _rows(_decide(model, tmp_path, {"D-VC": "refused", "D-COMPACT": "refused"}))
    assert {i: rows[i]["status"] for i in VC_FAMILY + ["D-G2", "K5-3", "K5-2b"]} == {
        i: "not_applicable" for i in VC_FAMILY + ["D-G2", "K5-3", "K5-2b"]}
    # the decision itself is recorded and, with its VC-2 input retired by that same outcome (no arms are run without a
    # consenting population), reads done rather than waiting on an input that can never complete (SR-CLOSE-NOW 5)
    assert rows["D-VC"]["outcome"] == "refused" and rows["D-VC"]["status"] == "done"
    assert rows["VC-2"]["status"] == "not_applicable" and rows["VC-2"]["skip_origin"] == ["D-VC"]


def test_an_unmerged_branch_does_not_override_the_recorded_not_applicable_ruling_on_k5_2b(tmp_path):
    # K5-2b (K5-2b tracker rule): D-COMPACT refused makes K5-2b not_applicable by the recorded decision
    # (CONTROL_PLANE.md: "a final incompatible outcome makes dependent executable work not_applicable"). Its branch is
    # NOT merged, so the live detector reads "running"; that unmerged reading must not turn the ruling back into waiting.
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    log = tmp_path / "EVENTS.jsonl"
    saved = cli.EVENTS, cli.load_model
    cli.EVENTS, cli.load_model = str(log), lambda: model
    try:
        for dec in ("D-VC", "D-COMPACT"):
            assert cli.main(["decide", dec, "--outcome", "refused", "--as", "steward", "--delegated",
                             "--detail", f"K5-2b {dec}"]) == 0
    finally:
        cli.EVENTS, cli.load_model = saved
    events = [json.loads(line) for line in log.read_text().splitlines()]
    running = {"K5-2b": {"status": "running", "detail": "branch kalayantra/k5-2b not merged",
                         "checked_at": NOW.isoformat()}}
    rows = _rows(build_snapshot(model, events, running, {}, {}, now=NOW, closure=_closure(model)))
    assert rows["K5-2b"]["status"] == "not_applicable" and rows["K5-2b"]["skip_origin"]
    # earned by the ruling, not by the reading: with no ruling the same unmerged reading still shows waiting
    undecided = _rows(build_snapshot(model, [], running, {}, {}, now=NOW, closure=_closure(model)))
    assert undecided["K5-2b"]["status"] == "waiting"


def test_approved_d_vc_leaves_the_k5_2_trial_open(tmp_path):
    # N.8: the not_applicable above is earned by the refused outcome, not by the family's mere presence
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    rows = _rows(_decide(model, tmp_path, {"D-VC": "approved"}))
    assert all(rows[i]["status"] != "not_applicable" for i in VC_FAMILY)


def test_the_d_vc_default_and_the_family_re_entry_are_declared():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    items = {i["id"]: i for i in model["items"]}
    decision = next(d for d in model["decisions"] if d["id"] == "D-VC")
    assert decision["default"].startswith("refused") and "not_evaluable" in decision["default"]
    assert "consenting evaluation population" in decision["default"]
    for iid in VC_FAMILY:
        triage = items[iid]["triage"]
        assert (triage["class"], triage["decision"]) == ("retired", "D-VC") and triage["re_entry"] == (
            "a consenting evaluation population exists"), iid
    assert all(items[i]["requires_outcome"] == {"D-VC": "approved"} for i in ("K5-2", "K5-2-qualify", "K5-2-representation"))


def test_vc2_is_retired_by_d_vcs_refusal_so_d_vc_closes_and_the_headline_stops_counting_it(tmp_path):
    # SR-CLOSE-NOW 5. Claim 1: a refused D-VC makes VC-2 not_applicable (the arms need a consenting population, which
    # PRE-D-VC / SR-W34-PREP-RULINGS 4 record as absent), by the same requires_outcome semantics as the K5-2 family.
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    refused = _decide(model, tmp_path / "refused", {"D-VC": "refused"})
    rows = _rows(refused)
    assert rows["VC-2"]["status"] == "not_applicable" and rows["VC-2"]["skip_origin"] == ["D-VC"]
    # Claim 2: the recorded refusal reads done (it no longer waits on an input its own outcome retired) ...
    assert rows["D-VC"]["status"] == "done"
    # ... and the recomputed closure no longer counts the retired arms run: the headline is clean of it
    closure = _closure(model)
    assert "VC-2" not in closure["closure"] and "D-VC" in closure["closure"]
    before = build_snapshot(model, [], {}, {}, {}, now=NOW, closure=closure)
    undecided = _rows(before)
    assert undecided["D-VC"]["status"] != "done" and undecided["VC-2"]["status"] != "not_applicable"
    assert refused["overall"]["done"] == before["overall"]["done"] + 1       # D-VC itself, nothing else
    assert refused["overall"]["total"] == before["overall"]["total"] == closure["closure_count"] == 181
    # Claim 3: the same outcome at approved leaves the arms live (earned by the outcome, not by the item's presence)
    approved = _rows(_decide(model, tmp_path / "approved", {"D-VC": "approved"}))
    assert approved["VC-2"]["status"] != "not_applicable"


def test_vc2_retirement_is_declared_with_its_re_entry_and_keeps_its_unmeasured_detector():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    items = {i["id"]: i for i in model["items"]}
    vc2, dvc = items["VC-2"], items["D-VC"]
    assert vc2["requires_outcome"] == {"D-VC": "approved"}
    assert (vc2["triage"]["class"], vc2["triage"]["decision"]) == ("retired", "D-VC")
    assert vc2["triage"]["re_entry"] == "a consenting evaluation population exists"
    # the model is acyclic (test_kya9plan counts requires_outcome edges): VC-2 names D-VC, so D-VC cannot name VC-2
    assert "VC-2" not in dvc["depends_on"] and "D-VC" not in vc2["depends_on"]
    # PR #3732 built the mechanisms but ran no arm: it does not satisfy VC-2, so the detector is not re-pointed to it
    assert vc2["detector"]["ref"] == "origin/kalayantra/vc-2" and "UNMEASURED" in vc2["detector"]["measures"]


def test_ka4b_nb_02_is_a_plain_child_of_ka_4b_with_no_declared_retirement():
    # SR-CLOSE-NOW.amend-7: KA4B-NB-02 closes with KA-4b, so D-KA4B-NB02-NA must not be recorded (not declared at all, or it
    # would sit 'ready' forever); the item keeps its plain dependency on KA-4b and its original triage class
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    items = {i["id"]: i for i in model["items"]}
    nb = items["KA4B-NB-02"]
    assert nb["depends_on"] == ["KA-4b"] and "requires_outcome" not in nb
    assert nb["triage"] == {"class": "a"}
    assert "D-KA4B-NB02-NA" not in items and "D-KA4B-NB02-NA" not in {d["id"] for d in model["decisions"]}


def test_k_cert_carries_no_deferral_so_its_real_artifact_acceptance_can_count():
    # SR-DETECTOR-REFS / SR-W34-PREP-RULINGS 5b: K-CERT is an acceptance root (iii) and is never classed deferred; its park
    # is a tracker event (`ky unblock`), not a model marker, so the model must stay clean of one.
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    kcert = next(i for i in model["items"] if i["id"] == "K-CERT")
    assert (kcert.get("triage") or {}).get("class") == "a" and "re_entry" not in (kcert.get("triage") or {})
    assert "K-CERT" in load_closure(model)["closure"]
    assert kcert["detector"]["path"].endswith("K-CERT_ASSESSMENT_REVIEW.md")


# SR-PARKED-OUT-OF-CAMPAIGN / SR-DT2-CANDIDATE (2026-10-22). Source: the two rulings in DECISIONS_SURROGATE.jsonl; mechanism: A9 D-51.3
# (deferred items are listed apart, never counted) and CONTROL_PLANE.md (a recorded decision item reads done once its gates are done).
PARKED_OUT = ["KR-1", "KR-2", "J-7a", "J-7a-pr3099", "J-7a-a62", "J-8", "J-8a", "J-8-b63", "J-8-j3", "J-4a-a25", "J-4a-a26",
              "J-3a-b44", "L0-K"]


def test_the_parked_items_read_deferred_with_re_entry_and_never_done_or_in_the_headline(tmp_path):
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    snap = _decide(model, tmp_path, {"D-T2": "approved"})
    o = snap["overall"]
    listed = {d["id"]: d for d in o["deferred"]}
    rows = _rows(snap)
    members = set(_closure(model)["closure"])
    for iid in PARKED_OUT:
        assert iid in listed and listed[iid]["re_entry"], iid          # listed apart, with the condition to come back
        assert iid not in members, iid                                    # outside the headline count
        assert rows[iid]["status"] != "done", iid                         # never shown as done
    # all thirteen sit in the reconciliation's deferred group, none in the finish path or side work
    by_class = {r["id"] for r in o["deferred"]}
    assert set(PARKED_OUT) <= by_class
    assert o["reconciliation"]["deferred"]["total"] >= len(PARKED_OUT) and o["reconciliation"]["unclassified"]["total"] == 0
    assert o["reconciliation"]["sum_of_parts"] == o["reconciliation"]["plan_items"]


def test_d_t2_reads_done_once_its_decision_is_recorded(tmp_path):
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    rows = _rows(_decide(model, tmp_path, {"D-T2": "approved"}))
    assert rows["D-T2"]["status"] == "done" and rows["D-T2"]["outcome"] == "approved"
    # earned by the record: with no decision event the same item is not done (N.8)
    assert _rows(build_snapshot(model, [], {}, {}, {}, now=NOW, closure=_closure(model)))["D-T2"]["status"] != "done"

