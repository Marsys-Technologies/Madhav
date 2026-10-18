"""A5 D-39: merge evidence earns a display signal, never a completion shortcut."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import subprocess

import pytest

from pravaha_tracker import cli
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
def test_names_every_strict_blocker_even_when_start_policy_relaxes_it(scenario, detector_type):
    scenario[0]["items"][0]["detector"]["type"] = detector_type
    snap, rows = snapshot(scenario)
    row = rows["K-BUILT"]
    assert row.get("built_waiting_on_gate") is True
    assert row["gate_blockers"] == ["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"]
    assert row["deps_open"] == ["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"]
    assert row["deps_merged_pending_deploy"] == ["K-INPUT"]
    assert row["status"] == "running"  # the completed step starts work, not guarded completion
    assert snap["overall"]["built_waiting_on_gate"] == 1
    assert snap["overall"]["done"] == 0


@pytest.mark.parametrize("ready_at_merge", [False, True])
@pytest.mark.parametrize("ready_at_accepted", [False, True])
def test_dashboard_open_dependencies_equal_guarded_done_refusal(
        scenario, ready_at_merge, ready_at_accepted):
    """A merged child must name its merged-but-not-done parent as an open gate."""
    model, events, detectors = scenario
    model["control_plane"].update(ready_at_merge=ready_at_merge,
                                  ready_at_accepted=ready_at_accepted)
    # Exercise both the mixed gate list and the remaining merged-only parent.
    for close_other_gates in (False, True):
        if close_other_gates:
            events.append({"kind": "item", "item": "V-GATE", "state": "done",
                           "guarded": True, "ts": NOW.isoformat()})
            events.append({"kind": "decision", "decision": "D-APPROVE",
                           "state": "decided", "ts": NOW.isoformat()})
        expected = (["K-INPUT"] if close_other_gates else
                    ["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"])
        row = snapshot(scenario)[1]["K-BUILT"]
        with pytest.raises(CompletionError) as refusal:
            guarded_done_event(model, events, "K-BUILT", "stream-K:builder",
                               detectors["K-BUILT"], {})
        assert str(refusal.value) == "dependencies remain open: " + ", ".join(expected)
        assert row["deps_open"] == expected
        assert row["deps_open"] == str(refusal.value).removeprefix(
            "dependencies remain open: ").split(", ")
        assert row["built_waiting_on_gate"] is True
        assert row["gate_blockers"] == expected
        assert row["status"] != "done"


def test_cli_done_refusal_matches_dashboard_and_does_not_append(scenario, tmp_path, monkeypatch, capsys):
    model, events, detectors = scenario
    # Use local artifact evidence to exercise the real CLI without any network or GitHub call.
    # An operation receipt: D-46 defers a code/artifact item's open gates, an operation keeps strict ordering.
    artifact = tmp_path / "receipt.json"
    artifact.write_text("{}")
    model["items"][0]["detector"]["path"] = str(artifact)
    log = tmp_path / "EVENTS.jsonl"
    log.write_text("".join(json.dumps(event) + "\n" for event in events))
    before = log.read_bytes()
    monkeypatch.setattr(cli, "EVENTS", str(log))
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "get", lambda *args, **kwargs: (
        {"item": "K-BUILT", "detector": detectors["K-BUILT"]}, "live"))
    expected = ["D-GATE", "V-GATE", "JOIN-GATE", "K-INPUT"]
    assert cli.main(["done", "K-BUILT", "--stream", "K", "--operation-receipt", str(artifact),
                     "--operation-id", "op-1"]) == 2
    assert capsys.readouterr().err.strip() == "refused: dependencies remain open: " + ", ".join(expected)
    assert snapshot(scenario)[1]["K-BUILT"]["deps_open"] == expected
    assert log.read_bytes() == before


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


@pytest.mark.parametrize("event_state", ["running", "review", None])
def test_built_waiters_have_an_exclusive_display_class(scenario, event_state):
    model, events, detectors = scenario
    model["streams"] = [{"id": "K", "name": "builders"}]
    model["items"][0]["steps"] = []
    model["items"][4]["depends_on"] = ["V-GATE"]
    events.clear()
    if event_state:
        events.append({"kind": "item", "item": "K-BUILT", "state": event_state,
                       "ts": NOW.isoformat()})
    # A genuine review still belongs in running; an ordinary ready item stays ready.
    model["items"].extend([
        {"id": "K-REVIEW", "title": "review", "owner": "K", "track": "K"},
        {"id": "K-READY", "title": "ready", "owner": "K", "track": "K"},
    ])
    events.append({"kind": "item", "item": "K-REVIEW", "state": "review", "ts": NOW.isoformat()})
    snap, rows = snapshot(scenario)
    built = rows["K-BUILT"]
    assert built["display_status"] == "built_waiting_on_gate"
    assert built["status"] == (event_state or "waiting")
    assert snap["overall"]["running"] == 1
    assert snap["overall"]["ready"] == 3  # D-GATE, V-GATE and K-READY
    assert snap["overall"]["waiting"] == 1  # JOIN-GATE only
    assert [row["id"] for row in snap["now"]] == ["K-REVIEW"]
    assert [row["id"] for row in snap["next"]] == ["D-GATE", "V-GATE", "K-READY"]
    assert [row["id"] for row in snap["built_waiting_on_gate"]] == ["K-BUILT", "K-INPUT"]
    stream = snap["streams"][0]
    assert [row["id"] for row in stream["running"]] == ["K-REVIEW"]
    assert [row["id"] for row in stream["ready"]] == ["D-GATE", "V-GATE", "K-READY"]
    assert [row["id"] for row in stream["built_waiting_on_gate"]] == ["K-BUILT", "K-INPUT"]
    # The display class disappears on the next snapshot if merge evidence is lost.
    detectors["K-BUILT"]["status"] = "running"
    cleared, rows = snapshot(scenario)
    assert rows["K-BUILT"]["display_status"] == rows["K-BUILT"]["status"]
    assert "K-BUILT" not in {row["id"] for row in cleared["built_waiting_on_gate"]}


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
  return {plan: nodes.plan.innerHTML, counts: nodes.counts.innerHTML, foot: nodes.foot.textContent,
          now: nodes.now.innerHTML, built: nodes["built-waiting"]?.innerHTML, streams: nodes.streams.innerHTML};
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


def test_dashboard_separates_built_waiters_from_review_and_clears_them(scenario):
    model, events, _ = scenario
    model["streams"] = [{"id": "K", "name": "builders"}]
    events.append({"kind": "item", "item": "K-BUILT", "state": "review", "ts": NOW.isoformat()})
    snap, rows = snapshot(scenario)
    # Explicit API fields isolate the renderer from the state fix.
    row = rows["K-BUILT"]
    row.update(display_status="built_waiting_on_gate", gate_blockers=["D-<GATE>"])
    snap["now"] = []
    snap["built_waiting_on_gate"] = [row]
    snap["streams"][0].update(running=[], built_waiting_on_gate=[row])
    cleared = json.loads(json.dumps(snap))
    cleared["tracks"][0]["items"][0].update(display_status="review", built_waiting_on_gate=False, gate_blockers=[])
    cleared["built_waiting_on_gate"] = []
    cleared["streams"][0]["built_waiting_on_gate"] = []
    cleared["overall"]["built_waiting_on_gate"] = 0
    app = Path(__file__).resolve().parents[1] / "static" / "app.js"
    result = subprocess.run(["node", "-e", CLIENT_PROBE, str(app)], input=json.dumps([snap, cleared]),
                            text=True, capture_output=True, check=True)
    shown, hidden = json.loads(result.stdout)
    assert "Render error" not in shown["foot"]
    assert 'class="card st-built_waiting_on_gate' in shown["plan"]
    assert '<span class="badge">built, waiting on gate</span>' in shown["plan"]
    assert '<span class="badge">in review</span>' not in shown["plan"]
    assert "K-BUILT" not in shown["now"]
    assert "K-BUILT" in shown["built"] and "D-&lt;GATE&gt;" in shown["built"]
    assert "D-<GATE>" not in shown["built"]
    assert "Built, waiting on gate" in shown["streams"]
    assert 'class="mini st-built_waiting_on_gate' in shown["streams"]
    assert "K-BUILT" not in hidden["built"]
    assert 'class="card st-built_waiting_on_gate' not in hidden["plan"]
    assert '<span class="badge">in review</span>' in hidden["plan"]
    # The new list must exist in the real page, not only in the fake DOM.
    page = (app.parent / "index.html").read_text()
    assert 'id="built-waiting"' in page
