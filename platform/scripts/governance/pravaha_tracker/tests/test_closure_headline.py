"""Amendment A9 D-51/D-53/D-54: the headline counts over the acceptance closure; deferred items are listed apart;
the not_applicable set is recorded the tracker's own way (a refused retirement decision) and does not spread into
the closure.

Source: 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md §2.3, §4, §5;
CONTROL_PLANE.md ("a final incompatible outcome makes dependent executable work not_applicable").
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from pravaha_tracker import cli
from pravaha_tracker.state import build_snapshot, load_closure

NOW = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"

NOT_APPLICABLE = ["JOIN-ALL", "K-CERT-2", "W4-SAFETY-N01", "W4-SAFETY-N02", "KA3B-N1", "KA3B-N2", "OPS-NB-03",
                  "V-K3b", "V-K5", "V-K6", "V-KA", "V-VC", "J-4c-pr2907"]
DEFERRED = ["J-7a", "J-7a-a62", "J-7a-pr3099", "KR-1", "KR-2", "J-8", "J-8-b63", "J-8-j3", "J-8a", "K9-5",
            "K9-5-NB-01"]
DEFERRED_NB04 = ["J-4a-a25", "J-4a-a26", "J-3a-b44"]   # SR-A9-INTERP A9-NB-04: no phase brief reads their output;
                                                         # J-3a-b44 added by SR-A9-NB-04-B44 (its 4.1 baseline needs a25)
DEFERRED_PREP = ["D-T2", "L0-K", "D-GOCHARA-TIMEOUT"]    # SR-W34-PREP-RULINGS 5b/5f: deferred with re-entry, outside C-1 and the closure


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
        for dec in sorted(d["id"] for d in model["decisions"] if d["id"].startswith(("D-A9-NA-", "D-J4C-PR2907-NA"))):
            assert cli.main(["decide", dec, "--outcome", "refused", "--as", "steward", "--delegated",
                             "--detail", f"A9 {dec}"]) == 0
    finally:
        cli.EVENTS, cli.load_model = saved
    events = [json.loads(line) for line in log.read_text().splitlines()]
    return model, build_snapshot(model, events, {}, {}, {}, now=NOW, closure=load_closure(model))


def test_the_twelve_items_become_not_applicable_by_the_recorded_decision(decided):
    # A9 D-51.1, D-53, D-54: each listed item is not_applicable (the reason is its decision's text)
    _, snap = decided
    rows = _rows(snap)
    assert {i: rows[i]["status"] for i in NOT_APPLICABLE} == {i: "not_applicable" for i in NOT_APPLICABLE}


def test_not_applicable_does_not_spread_into_the_closure(decided):
    # A9 §7 + D-54: retiring V-K6 must not retire the live K6-N1..N3 follow-ups or K9-4a; closure has no n/a member
    model, snap = decided
    rows = _rows(snap)
    closure = set(load_closure(model)["closure"])
    assert [i for i in closure if rows[i]["status"] == "not_applicable"] == []
    assert all(rows[i]["status"] != "not_applicable" for i in ("K6-N1", "K6-N2", "K6-N3", "K9-4a", "C-1", "J-4c"))
    assert snap["overall"]["not_applicable"] == 0


def test_the_headline_denominator_is_the_closure_and_every_deferred_item_is_listed(decided):
    _, snap = decided
    o = snap["overall"]
    assert o["total"] == 183 and o["plan_wide"]["total"] == 274
    listed = {d["id"]: d for d in o["deferred"]}
    assert set(DEFERRED + DEFERRED_NB04 + DEFERRED_PREP) <= set(listed)
    assert all(listed[i]["re_entry"] for i in DEFERRED + DEFERRED_NB04 + DEFERRED_PREP)
    assert not set(listed) & {"J-7", "J-7b"}   # D-52: the rest of the post-flip phase is not deferred (D-T2, L0-K are: SR-W34-PREP-RULINGS 5b)
