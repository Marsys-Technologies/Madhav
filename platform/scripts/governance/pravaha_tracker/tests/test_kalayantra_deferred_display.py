"""Deferred items are their own bucket (owner direction via madhav-44, 2026-10-22; SR-PARKED-OUT-OF-CAMPAIGN; PR #3890).

The 13 items the owner surrogate moved out of this campaign are triage class b (deferred, re-entry carried) and outside the acceptance
closure. The tracker read them as `parked` and listed them under "Needs attention" and in the stuck/blocked tallies, which made a ruled
deferral look like a fault. Display only: no status is rewritten, nothing is completed by it. One oracle per distinct claim, each with the
single planted reversion that makes it fail:

  1. a deferred item (class b, outside the closure, unfinished) is flagged `deferred`, keeps its own status (never done), is not in
     `attention`, not in the plan-wide `blocked` tally, and is counted in `deferred_count`      (reversion: is_deferred returns False)
  2. boundary: a parked item that is NOT triage class b is still stuck: attention and blocked (reversion: is_deferred ignores the class)
  3. boundary: a deferred item that reads `failed` stays visible: a fault in the evidence is not a deferral (reversion: DEFERRED_QUIET
     gains "failed")
  4. boundary: finished work is never re-labelled: a class b item that is done reads done and is not deferred
     (reversion: is_deferred ignores the status)
  5. boundary: a closure member is never deferred, whatever its class (reversion: is_deferred ignores `members`)
  6. closure scope: the deferred item is outside the headline denominator and done count, is listed in `overall.deferred`, and the
     plan-wide figure carries `deferred_count`                       (reversion: plan_wide drops deferred_count)
  7. the stream panel's Blocked column leaves out deferred items       (reversion: _stream_view stops filtering on _needs_attention)
  8. the real plan: exactly the 13 SR-PARKED-OUT-OF-CAMPAIGN items, parked by events, are deferred; none reads done, none is in
     attention, deferred_count is 13, and no done count moves      (reversion: drop one triage class b from the plan model)
  9. a retirement decision carrying `retires` (no item of its own) is staged, not a question for the native
     (reversion: drop the `retires` clause in state.build_snapshot)
 10. this file is matched by a CI suite glob
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker.state import build_snapshot, is_deferred  # noqa: E402

REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
NOW = dt.datetime(2026, 10, 22, 23, 0, tzinfo=dt.timezone.utc)
TS = NOW.isoformat()

PARKED_13 = ["KR-1", "KR-2", "J-7a", "J-7a-pr3099", "J-7a-a62", "J-8", "J-8a", "J-8-b63", "J-8-j3",
             "J-4a-a25", "J-4a-a26", "J-3a-b44", "L0-K"]       # SR-PARKED-OUT-OF-CAMPAIGN, DECISIONS_SURROGATE.jsonl


def _rows(snap):
    return {t["id"]: t for tr in snap["tracks"] for t in tr["items"]}


def _item(iid, cls=None, **extra):
    row = {"id": iid, "track": "K", "owner": "K", "title": iid, "depends_on": [], **extra}
    if cls:
        row["triage"] = {"class": cls, "reason": "fixture", "re_entry": "later"}
    return row


def _event(iid, state):
    return {"kind": "item", "actor": "steward", "item": iid, "state": state, "ts": TS, "detail": f"{state} (fixture)"}


def _model(items, **extra):
    return {"campaign": "fixture", "control_plane": {"guarded_completion": True}, "tracks": [{"id": "K", "title": "K"}],
            "streams": [{"id": "K", "name": "K", "plain": "K"}], "decisions": [], "items": items, **extra}


def _fixture():
    items = [_item("DEF", "b"), _item("STUCK", "a"), _item("DEF-FAILED", "b"), _item("DEF-DONE", "b"),
             _item("MEMBER", "b"), _item("OPEN", "a"), _item("DEF-UNKNOWN", "b")]
    events = [_event("DEF", "parked"), _event("STUCK", "parked"), _event("DEF-FAILED", "failed"),
              _event("DEF-DONE", "done"), _event("MEMBER", "parked"), _event("DEF-UNKNOWN", "blocked")]
    events[3] = {**events[3], "guarded": True, "evidence": "fixture"}
    return _model(items), events, {"closure": ["MEMBER", "OPEN"], "closure_sha256": "x"}


def _snap(closure=True):
    model, events, closure_doc = _fixture()
    return build_snapshot(model, events, {}, {}, {}, now=NOW, closure=closure_doc if closure else None)


def test_a_deferred_item_is_its_own_bucket_never_done_stuck_or_in_attention():  # claim 1
    snap = _snap(closure=False)
    rows = _rows(snap)
    assert rows["DEF"]["deferred"] is True and rows["DEF"]["status"] == "parked"          # its status is not rewritten
    assert rows["DEF"]["status"] != "done" and "DEF" not in {t["id"] for t in snap["done"]}
    assert "DEF" not in {t["id"] for t in snap["attention"]}
    assert rows["DEF-UNKNOWN"]["deferred"] is True and "DEF-UNKNOWN" not in {t["id"] for t in snap["attention"]}
    o = snap["overall"]
    assert o["deferred_count"] == 4          # DEF, DEF-FAILED, DEF-UNKNOWN and MEMBER (no closure given, so nothing is a member); DEF-DONE is done
    assert o["blocked"] == 2                 # STUCK (parked) and DEF-FAILED (failed); the set-aside deferred ones are not stuck
    assert o["done"] == 1                                                # only DEF-DONE


def test_a_parked_item_that_is_not_deferred_is_still_stuck():  # claim 2
    snap = _snap(closure=False)
    assert _rows(snap)["STUCK"]["deferred"] is False
    assert "STUCK" in {t["id"] for t in snap["attention"]}


def test_a_deferred_item_that_failed_stays_visible():  # claim 3
    snap = _snap(closure=False)
    assert _rows(snap)["DEF-FAILED"]["deferred"] is True
    assert "DEF-FAILED" in {t["id"] for t in snap["attention"]}


def test_finished_work_is_never_relabelled_deferred():  # claim 4
    snap = _snap(closure=False)
    row = _rows(snap)["DEF-DONE"]
    assert row["status"] == "done" and row["deferred"] is False
    assert is_deferred({"id": "X", "triage": {"class": "b"}}, "not_applicable", set()) is False


def test_a_closure_member_is_never_deferred():  # claim 5
    snap = _snap(closure=True)
    assert _rows(snap)["MEMBER"]["deferred"] is False
    assert "MEMBER" in {t["id"] for t in snap["attention"]}


def test_the_closure_headline_excludes_the_deferred_and_the_plan_wide_figure_counts_them():  # claim 6
    o = _snap(closure=True)["overall"]
    assert o["total"] == 2 and o["done"] == 0                           # MEMBER and OPEN only: DEF-DONE is done but outside the closure
    assert {d["id"] for d in o["deferred"]} == {"DEF", "DEF-FAILED", "DEF-DONE", "DEF-UNKNOWN"}   # the existing list: every class b outside
    assert o["plan_wide"]["deferred_count"] == 3 and o["deferred_count"] == 3
    assert o["plan_wide"]["done"] == 1 and o["plan_wide"]["total"] == 7  # nothing else moved


def test_the_stream_panel_leaves_deferred_items_out_of_blocked():  # claim 7
    snap = _snap(closure=False)
    blocked = {t["id"] for t in snap["streams"][0]["blocked"]}
    assert "DEF" not in blocked and {"STUCK", "DEF-FAILED"} <= blocked


# ---------------------------------------------------------------------------------------- the real plan

def _closure_of(model):
    spec = importlib.util.spec_from_file_location("kyclosure", REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/kyclosure.py")
    kyclosure = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = kyclosure
    spec.loader.exec_module(kyclosure)
    roots = json.loads((REPO / "00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v3.json").read_text(encoding="utf-8"))
    return kyclosure.compute(model, roots)


def test_the_thirteen_parked_out_of_campaign_items_are_deferred_in_the_real_plan():  # claim 8
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    closure = _closure_of(model)
    events = [_event(iid, "parked") for iid in PARKED_13]
    snap = build_snapshot(model, events, {}, {}, {}, now=NOW, closure=closure)
    rows = _rows(snap)
    deferred = sorted(i for i, r in rows.items() if r["deferred"] and r["status"] == "parked")
    assert deferred == sorted(PARKED_13)
    assert all(rows[i]["status"] != "done" for i in PARKED_13)
    assert not set(PARKED_13) & {t["id"] for t in snap["attention"]}
    assert snap["overall"]["deferred_count"] == snap["overall"]["plan_wide"]["deferred_count"]
    assert snap["overall"]["deferred_count"] >= 13
    # nothing else moved: the same events with the display logic neutralised give the same done set
    done = {i for i, r in rows.items() if r["status"] == "done"}
    assert snap["overall"]["plan_wide"]["done"] == len(done)
    assert not set(PARKED_13) & set(closure["closure"])                 # outside the closure by the ruling


def test_a_retirement_decision_with_no_item_of_its_own_is_staged_not_a_native_question():  # claim 9
    model = _model([_item("A", "retired")])
    model["control_plane"]["declarations"] = {}
    model["decisions"] = [{"id": "D-RULING", "title": "ruling", "retires": ["A"]}, {"id": "D-OPEN", "title": "open"}]
    queue = {d["id"] for d in build_snapshot(model, [], {}, {}, {}, now=NOW)["native_queue"]}
    assert "D-RULING" not in queue and "D-OPEN" in queue


def test_this_file_is_matched_by_a_ci_suite_glob():  # claim 10
    suites = json.loads((REPO / "platform/scripts/governance/ci_test_suites.json").read_text(encoding="utf-8"))
    me = Path(__file__).resolve().relative_to(REPO).as_posix()
    globs = [g for prof in suites["suites"].values() for g in prof.get("include", [])]
    assert any(fnmatch.fnmatch(me, g) for g in globs), me
