"""A5 D-39: merge evidence earns a display signal, never a completion shortcut."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import subprocess

import pytest

from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.state import build_snapshot


NOW = dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc)


@pytest.fixture
def scenario():
    def item(iid, **extra):
        return {"id": iid, "title": iid, "track": "K", "owner": "K", **extra}

    model = {
        "control_plane": {"guarded_completion": True, "ready_at_merge": True},
        "tracks": [{"id": "K", "title": "K"}], "decisions": [], "streams": [],
        "items": [
            item("K-BUILT", detector={"type": "branch_merged", "ref": "origin/built"},
                 depends_on=["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"], steps=["tests"]),
            item("D-GATE", done_by="decision", decision="D-APPROVE"),
            item("V-GATE"),
            item("JOIN-GATE", done_by="join", depends_on=["V-GATE"]),
            item("K-INPUT", detector={"type": "branch_merged", "ref": "origin/input"}),
        ],
    }
    detectors = {iid: {"status": "done", "detail": "merged", "checked_at": NOW.isoformat()}
                 for iid in ("K-BUILT", "K-INPUT")}
    events = [
        {"kind": "item", "item": "K-BUILT", "state": "done", "step": "tests", "ts": NOW.isoformat()},
        {"kind": "verdict", "item": "K-INPUT", "result": "ACCEPTED", "ts": NOW.isoformat()},
    ]
    return model, events, detectors


def snapshot(scenario):
    model, events, detectors = scenario
    snap = build_snapshot(model, events, detectors, {}, {}, now=NOW)
    rows = {it["id"]: it for tr in snap["tracks"] for it in tr["items"]}
    return snap, rows


@pytest.mark.parametrize("detector_type", ["branch_merged", "pr_merged"])
def test_names_every_strict_blocker_even_when_readiness_relaxes_it(scenario, detector_type):
    scenario[0]["items"][0]["detector"]["type"] = detector_type
    snap, rows = snapshot(scenario)
    row = rows["K-BUILT"]
    assert row.get("built_waiting_on_gate") is True
    assert row["gate_blockers"] == ["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"]
    assert row["deps_open"] == ["D-GATE", "V-GATE", "JOIN-GATE"]
    assert row["deps_merged_pending_deploy"] == ["K-INPUT"]
    assert row["status"] == "running"  # the completed step starts work, not guarded completion
    assert snap["overall"]["built_waiting_on_gate"] == 1
    assert snap["overall"]["done"] == 0


@pytest.mark.parametrize("missing", ["unmeasured", "pending", "running", "error", "blocked",
                                     "step", "no-deps", "unknown-dep", "no-detector", "null-detector",
                                     "file-detector", "pr-ready",
                                     "blocked-event", "failed-event", "parked-event", "conflict",
                                     "completed", "outcome"])
def test_signal_reads_false_without_merge_or_with_another_open_requirement(scenario, missing):
    model, events, detectors = scenario
    item = model["items"][0]
    if missing == "unmeasured":
        detectors.pop("K-BUILT")
    elif missing in ("pending", "running", "error", "blocked"):
        detectors["K-BUILT"]["status"] = missing
    elif missing == "step":
        events.clear()
    elif missing == "no-deps":
        item["depends_on"] = []
    elif missing == "unknown-dep":
        item["depends_on"].append("MISSING")
    elif missing == "no-detector":
        item.pop("detector")
    elif missing == "null-detector":
        item["detector"] = None
    elif missing in ("file-detector", "pr-ready"):
        item["detector"]["type"] = "file_exists" if missing == "file-detector" else "pr_ready"
    elif missing in ("blocked-event", "failed-event", "parked-event", "conflict", "completed"):
        state = {"conflict": "done", "completed": "done"}.get(missing, missing.split("-")[0])
        events.append({"kind": "item", "item": "K-BUILT", "state": state,
                       "guarded": missing == "completed", "ts": NOW.isoformat()})
    elif missing == "outcome":
        item["requires_outcome"] = {"D-APPROVE": "approved"}
    snap, rows = snapshot(scenario)
    assert rows["K-BUILT"].get("built_waiting_on_gate") is False
    assert rows["K-BUILT"]["gate_blockers"] == []
    assert snap["overall"]["built_waiting_on_gate"] == 0


def test_recomputes_when_gates_close(scenario):
    assert snapshot(scenario)[0]["overall"].get("built_waiting_on_gate") == 1
    model, events, detectors = scenario
    for iid in ("V-GATE", "K-INPUT"):
        events.append({"kind": "item", "item": iid, "state": "done", "guarded": True,
                       "ts": NOW.isoformat()})
    events.append({"kind": "decision", "decision": "D-APPROVE", "state": "decided", "ts": NOW.isoformat()})
    snap, rows = snapshot(scenario)
    assert rows["K-BUILT"]["gate_blockers"] == []
    assert snap["overall"]["built_waiting_on_gate"] == 0
    assert rows["K-BUILT"]["status"] != "done"


def test_recomputes_when_detector_stops_matching(scenario):
    assert snapshot(scenario)[1]["K-BUILT"].get("built_waiting_on_gate") is True
    scenario[2]["K-BUILT"]["status"] = "running"
    snap, rows = snapshot(scenario)
    assert rows["K-BUILT"]["built_waiting_on_gate"] is False
    assert rows["K-BUILT"]["gate_blockers"] == []
    assert snap["overall"]["built_waiting_on_gate"] == 0


def test_counts_items_with_no_steps_and_satisfied_outcome_requirements(scenario):
    model, events, detectors = scenario
    model["items"][0]["requires_outcome"] = {"D-APPROVE": "approved"}
    events.append({"kind": "decision", "decision": "D-APPROVE", "state": "decided",
                   "outcome": "approved", "ts": NOW.isoformat()})
    model["items"].append({"id": "K-SECOND", "title": "second", "track": "K",
                            "detector": {"type": "branch_merged", "ref": "origin/second"},
                            "depends_on": ["V-GATE"]})
    detectors["K-SECOND"] = {"status": "done", "detail": "merged", "checked_at": NOW.isoformat()}
    snap, rows = snapshot(scenario)
    assert rows["K-BUILT"]["gate_blockers"] == ["V-GATE", "JOIN-GATE", "K-INPUT"]
    assert rows["K-SECOND"]["built_waiting_on_gate"] is True
    assert rows["K-SECOND"]["gate_blockers"] == ["V-GATE"]
    assert snap["overall"]["built_waiting_on_gate"] == 2


def test_derived_signal_does_not_allow_guarded_completion(scenario):
    model, events, detectors = scenario
    assert snapshot(scenario)[1]["K-BUILT"].get("built_waiting_on_gate") is True
    with pytest.raises(CompletionError, match="dependencies remain open: D-GATE, V-GATE, JOIN-GATE, K-INPUT"):
        guarded_done_event(model, events, "K-BUILT", "stream-K:builder", detectors["K-BUILT"], {})


# Execute the shipped browser client with DOM/network boundaries replaced. Reverting
# the row or count rendering must fail on user-visible HTML, not source-string checks.
CLIENT_PROBE = r"""
const fs = require('fs'), vm = require('vm');
const nodes = {};
const handlers = {};
const context = {
  document: {getElementById: id => nodes[id] ||= {style: {}}},
  navigator: {}, Date, console,
  setInterval: () => 0, clearInterval: () => {},
  fetch: () => new Promise(() => {}),
  EventSource: class {addEventListener(name, cb) {handlers[name] = cb;}},
};
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), context);
const snaps = JSON.parse(fs.readFileSync(0, 'utf8'));
const rendered = snaps.map(snap => {
  handlers.snapshot({data: JSON.stringify(snap)});
  return {plan: nodes.plan.innerHTML, counts: nodes.counts.innerHTML, foot: nodes.foot.textContent};
});
process.stdout.write(JSON.stringify(rendered));
"""


def test_dashboard_renders_blocker_ids_and_count_and_clears_them(scenario):
    snap, rows = snapshot(scenario)
    # Supply the new API fields explicitly so this test isolates the real renderer.
    rows["K-BUILT"].update(built_waiting_on_gate=True, gate_blockers=["D-<GATE>", "V-GATE", "JOIN-GATE", "K-INPUT"])
    snap["overall"]["built_waiting_on_gate"] = 1
    cleared = json.loads(json.dumps(snap))
    cleared["tracks"][0]["items"][0].update(built_waiting_on_gate=False, gate_blockers=[])
    cleared["overall"]["built_waiting_on_gate"] = 0
    app = Path(__file__).resolve().parents[1] / "static" / "app.js"
    result = subprocess.run(["node", "-e", CLIENT_PROBE, str(app)], input=json.dumps([snap, cleared]),
                            text=True, capture_output=True, check=True)
    shown, hidden = json.loads(result.stdout)
    assert "Render error" not in shown["foot"]
    assert "built, waiting on gate: D-&lt;GATE&gt;, V-GATE, JOIN-GATE, K-INPUT" in shown["plan"]
    assert "<b>1</b>built, waiting on gate" in shown["counts"]
    assert "built, waiting on gate:" not in hidden["plan"]
    assert "<b>0</b>built, waiting on gate" in hidden["counts"]
