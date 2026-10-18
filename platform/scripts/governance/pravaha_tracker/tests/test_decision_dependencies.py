"""F3: recording a ruling cannot bypass a decision residual's original gates."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from pravaha_tracker import cli
from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.state import build_snapshot


NOW = dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc)
MODEL_PATH = Path(__file__).resolve().parents[5] / "00_ARCHITECTURE/control/kalayantra/plan_model.json"


def event(kind, **fields):
    return {"kind": kind, "ts": NOW.isoformat(), **fields}


def snapshot(model, events, detectors=None):
    snap = build_snapshot(model, events, detectors or {}, {}, {}, now=NOW)
    return snap, {row["id"]: row for track in snap["tracks"] for row in track["items"]}


@pytest.mark.parametrize("iid,decision,original_inputs", [
    ("J-4d-n-g9", "D-G9", ["J-0m", "J-4c", "J-4p"]),
    ("J-7-n-t2", "D-T2", ["J-0m", "K1-1b", "KA-3b"]),
])
@pytest.mark.parametrize("outcome", ["approved", "refused", "deferred", "insufficient_evidence"])
@pytest.mark.parametrize("delegated", [False, True])
def test_original_residual_dependencies_survive_real_decide_command(
        tmp_path, monkeypatch, iid, decision, original_inputs, outcome, delegated):
    model = json.loads(MODEL_PATH.read_text())
    log = tmp_path / "EVENTS.jsonl"
    monkeypatch.setattr(cli, "EVENTS", str(log))
    monkeypatch.setattr(cli, "load_model", lambda: model)
    args = ["decide", decision, "--outcome", outcome, "--as", "steward",
            "--detail", "scratch ruling; original prerequisites still open"]
    if delegated:
        args.append("--delegated")
    assert cli.main(args) == 0
    events = [json.loads(line) for line in log.read_text().splitlines()]
    snap, rows = snapshot(model, events)
    row = rows[iid]
    assert row["status"] == "waiting"
    assert row["outcome"] == outcome
    assert all(dep in row["deps_open"] for dep in original_inputs)
    assert row["deps_open"] == row["deps_open_strict"]
    assert iid not in {done["id"] for done in snap["done"]}
    recorded = next(d for d in snap["decisions"] if d["id"] == decision)
    assert recorded["status"] == ("delegated" if delegated else "decided")


@pytest.fixture
def chain():
    def item(iid, **extra):
        return {"id": iid, "track": "K", "title": iid, "owner": "K", **extra}

    # Consumers precede producers to require fixed-point resolution.
    return {
        "control_plane": {
            "guarded_completion": True, "ready_at_merge": True, "ready_at_accepted": True,
            "decision_outcomes": {"final": ["approved", "refused"],
                                  "open": ["deferred", "insufficient_evidence"]},
        },
        "tracks": [{"id": "K", "title": "K"}], "streams": [],
        "decisions": [{"id": "D-RULE", "title": "ruling"}],
        "items": [
            item("JOIN-OUT", done_by="join", depends_on=["RESIDUAL"]),
            item("WORK", depends_on=["RESIDUAL"]),
            item("RESIDUAL", done_by="decision", decision="D-RULE", depends_on=["JOIN-IN"]),
            item("JOIN-IN", done_by="join", depends_on=["DECISION-IN"]),
            item("DECISION-IN", done_by="decision", decision="D-RULE", depends_on=["CODE"]),
            item("CODE", detector={"type": "branch_merged", "ref": "origin/code"}),
        ],
    }


@pytest.mark.parametrize("outcome", ["approved", "refused", "deferred", "insufficient_evidence"])
@pytest.mark.parametrize("merged", [False, True])
def test_accepted_or_merged_code_does_not_complete_decision_chain(chain, outcome, merged):
    events = [event("decision", decision="D-RULE", state="decided", outcome=outcome, detail="ruling"),
              event("verdict", item="CODE", phase="pre_merge", result="ACCEPTED")]
    detectors = {"CODE": {"status": "done" if merged else "pending", "detail": "merge evidence",
                          "checked_at": NOW.isoformat()}}
    snap, rows = snapshot(chain, events, detectors)
    for iid, dep in [("DECISION-IN", "CODE"), ("JOIN-IN", "DECISION-IN"),
                     ("RESIDUAL", "JOIN-IN"), ("JOIN-OUT", "RESIDUAL"), ("WORK", "RESIDUAL")]:
        assert rows[iid]["status"] == "waiting"
        assert rows[iid]["deps_open"] == [dep]
        assert rows[iid]["deps_open_strict"] == [dep]
    assert snap["overall"]["done"] == 0
    with pytest.raises(CompletionError, match="dependencies remain open: RESIDUAL"):
        guarded_done_event(chain, events, "WORK", "stream-K:builder", None, {})


@pytest.mark.parametrize("outcome", ["approved", "refused", "deferred", "insufficient_evidence"])
@pytest.mark.parametrize("reverse", [False, True])
def test_decision_chain_closes_only_after_inputs_and_final_ruling(chain, outcome, reverse):
    if reverse:
        chain["items"].reverse()
    events = [event("decision", decision="D-RULE", state="delegated", outcome=outcome, detail="ruling")]
    assert snapshot(chain, events)[1]["RESIDUAL"]["status"] == "waiting"
    events.append(event("item", item="CODE", state="done", guarded=True, evidence="accepted readback"))
    snap, rows = snapshot(chain, events)
    final = outcome in ("approved", "refused")
    for iid in ("DECISION-IN", "JOIN-IN", "RESIDUAL", "JOIN-OUT"):
        assert rows[iid]["status"] == ("done" if final else "waiting")
    assert rows["DECISION-IN"]["deps_open"] == []
    assert rows["RESIDUAL"]["deps_open"] == ([] if final else ["JOIN-IN"])
    assert rows["WORK"]["status"] == ("ready" if final else "waiting")
    assert snap["overall"]["done"] == (5 if final else 1)


@pytest.mark.parametrize("state", ["decided", "delegated"])
def test_legacy_decision_also_waits_for_declared_inputs(chain, state):
    chain.pop("control_plane")
    events = [event("decision", decision="D-RULE", state=state, detail="legacy ruling")]
    assert snapshot(chain, events)[1]["RESIDUAL"]["status"] == "waiting"
    events.append(event("item", item="CODE", state="done", evidence="legacy proof"))
    # Legacy detectors decide completion themselves.
    detectors = {"CODE": {"status": "done", "detail": "merged", "checked_at": NOW.isoformat()}}
    assert snapshot(chain, events, detectors)[1]["RESIDUAL"]["status"] == "done"
