"""Owner request 2026-10-18: the status headline accounts for EVERY plan item exactly once.

Every number is computed from the model (item triage.class) and live statuses; an oracle asserts the parts sum to the
model's item count. Source: Amendment A9 D-51 (closure headline), CLAUDE.md §N.8 (earned signal), §N.7.6 (honest null).
"""
from __future__ import annotations

import datetime as dt
import importlib
import json
from pathlib import Path

import pytest

from pravaha_tracker import cli, state
from pravaha_tracker.state import build_snapshot, load_closure, reconciliation_line

NOW = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
REPO = Path(__file__).resolve().parents[5]
MODEL_PATH = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
PARTS = ("finish_path", "side_work", "deferred", "cancelled", "bookkeeping_decisions", "done_outside_plan", "unclassified")


def _ev(item, state_, **kw):
    return {"kind": "item", "item": item, "state": state_, "ts": "2026-10-17T00:00:00+00:00", "actor": "K", **kw}


def _synthetic():
    def item(iid, deps=(), cls=None, **extra):
        row = {"id": iid, "track": "K", "title": iid, "owner": "K", "depends_on": list(deps), "mandatory": True, **extra}
        if cls:
            row["triage"] = {"class": cls, **({"re_entry": "later"} if cls == "b" else {})}
        return row
    items = [item("F-DONE", cls="a"), item("F-RUN", ["F-DONE"], cls="a"), item("F-WAIT", ["F-RUN"], cls="a"),
             item("F-READY", cls="a"), item("F-REV", cls="a"),
             item("F-DEC", ["F-DONE"], cls="a_close", done_by="decision", decision="D-1"),
             item("S-DONE", cls="a"), item("S-RUN", cls="a"), item("S-WAIT", ["S-RUN"], cls="a"),
             item("S-NA", cls="a"),
             item("DEF-1", cls="b"), item("DEF-2", cls="b"),
             item("RET-1", cls="retired"), item("RET-2", cls="retired"),
             item("BK-1", cls="retire_decision", done_by="decision", decision="D-2"),
             item("OUT-1", cls="done_outside"), item("OUT-2", cls="done_outside"), item("OUT-3", cls="done_outside"),
             item("PLAIN")]
    return {"campaign": "t", "tracks": [{"id": "K", "title": "K"}], "streams": [], "phases": [],
            "decisions": [{"id": "D-1", "title": "d1"}, {"id": "D-2", "title": "d2"}], "items": items}


CLOSURE = {"closure": ["F-DONE", "F-RUN", "F-WAIT", "F-READY", "F-REV", "F-DEC"], "closure_sha256": "x"}


def _snap():
    events = [_ev("F-DONE", "done", evidence="e"), _ev("F-RUN", "running"), _ev("F-REV", "review"),
              _ev("S-DONE", "done", evidence="e"), _ev("S-RUN", "running"), _ev("S-NA", "parked"),
              _ev("DEF-1", "parked"), _ev("OUT-1", "done", evidence="e"),
              {"kind": "decision", "decision": "D-1", "state": "decided", "ts": "2026-10-17T00:00:00+00:00", "actor": "N"}]
    return build_snapshot(_synthetic(), events, {}, {}, {}, now=NOW, closure=CLOSURE)


def _rec(snap=None):
    return (snap or _snap())["overall"]["reconciliation"]


def test_every_plan_item_is_counted_exactly_once_synthetic():
    rec = _rec()
    assert rec["plan_items"] == len(_synthetic()["items"]) == 19
    assert sum(rec[p]["total"] for p in PARTS) == rec["sum_of_parts"] == rec["plan_items"]


def test_each_triage_class_lands_in_its_own_line():
    # closure members → finish path; class b → deferred (1 parked); retired + status not_applicable → cancelled;
    # retire_decision → bookkeeping; done_outside → outside; no class → unclassified (never folded into a neighbour)
    rec = _rec()
    assert rec["finish_path"]["total"] == 6
    assert rec["side_work"]["total"] == 4          # S-DONE, S-RUN, S-WAIT, S-NA(parked, still class a)
    assert rec["deferred"] == {"total": 2, "parked": 1, "other": 1}
    assert rec["cancelled"]["total"] == 2
    assert rec["bookkeeping_decisions"]["total"] == 1
    assert rec["done_outside_plan"]["total"] == 3
    assert rec["unclassified"]["total"] == 1


def test_finish_and_side_split_done_and_remaining_by_reason():
    rec = _rec()
    fp, sw = rec["finish_path"], rec["side_work"]
    assert (fp["done"], fp["remaining"]) == (2, 4)       # F-DONE, and F-DEC (decided counts as done, as the headline does)
    assert (fp["in_progress"], fp["built_awaiting_review_or_merge"], fp["ready_to_start"],
            fp["waiting_on_dependencies"], fp["decision_pending"]) == (1, 1, 1, 1, 0)
    assert (sw["done"], sw["remaining"], sw["in_progress"], sw["waiting_on_dependencies"], sw["needs_attention"]) == (1, 3, 1, 1, 1)
    for t in (fp, sw):
        assert t["done"] + t["not_applicable"] + t["remaining"] == t["total"]
        assert t["remaining"] == sum(t[k] for k in state.REMAINING_KEYS)


def test_a_decision_not_yet_decided_is_pending_and_a_decided_one_is_done():
    snap = build_snapshot(_synthetic(), [_ev("F-DONE", "done", evidence="e")], {}, {}, {}, now=NOW, closure=CLOSURE)
    assert _rec(snap)["finish_path"]["decision_pending"] == 1
    assert _rec()["finish_path"]["decision_pending"] == 0


def test_the_closure_headline_is_unchanged_and_the_finish_path_matches_it():
    o = _snap()["overall"]
    assert (o["scope"], o["total"], o["done"]) == ("closure", 6, o["reconciliation"]["finish_path"]["done"])


def test_no_closure_gives_no_reconciliation():
    # N.7.6: without a readable closure the finish path is unknowable, so no numbers are claimed
    assert "reconciliation" not in build_snapshot(_synthetic(), [], {}, {}, {}, now=NOW)["overall"]


def test_ky_status_prints_the_reconciliation_second_line(capsys, monkeypatch):
    snap = _snap()
    snap["version"] = 1
    monkeypatch.setattr(cli, "get", lambda path: (snap, "live"))
    assert cli.main(["status"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("t — ") and "done 2/6 (closure)" in lines[0]
    assert lines[1].startswith("  All 19 plan items: finish path 2/6 done (4 left: ")
    assert "side work 1/4 done" in lines[1] and "deferred 2 (1 parked)" in lines[1] and "cancelled 2" in lines[1]
    assert "decisions recorded 1" in lines[1] and "done outside plan 3" in lines[1] and "unclassified 1" in lines[1]
    assert json.dumps(snap["overall"]["reconciliation"])   # reaches /api/state as overall.reconciliation (JSON-safe)


def test_repo_root_honours_pravaha_repo(monkeypatch, tmp_path):
    monkeypatch.setenv("PRAVAHA_REPO", str(tmp_path))
    try:
        assert importlib.reload(state).REPO_ROOT == tmp_path
    finally:
        monkeypatch.delenv("PRAVAHA_REPO")
        importlib.reload(state)
    assert state.REPO_ROOT == REPO


def test_the_live_model_reconciles_to_its_item_count():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    rec = build_snapshot(model, [], {}, {}, {}, now=NOW, closure=load_closure(model))["overall"]["reconciliation"]
    assert rec["plan_items"] == len(model["items"]) == rec["sum_of_parts"]
    assert rec["unclassified"]["total"] == 0
    assert rec["finish_path"]["total"] == 187 and reconciliation_line(rec).startswith(f"All {len(model['items'])} plan items")
