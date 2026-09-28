"""Unit tests: the event log (append, validation, tolerant tailing) and the snapshot builder's rules."""
import datetime as dt
import json
import os
import threading

import pytest

from suvarna_tracker.events import EventError, EventLog, append, validate
from suvarna_tracker.state import build_snapshot

NOW = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


# ---- event validation ------------------------------------------------------------------------

def test_done_without_evidence_is_rejected():
    with pytest.raises(EventError):
        validate({"kind": "item", "actor": "b", "item": "X", "state": "done"})


def test_decided_without_detail_is_rejected():
    with pytest.raises(EventError):
        validate({"kind": "decision", "actor": "native", "decision": "N-1", "state": "decided"})


@pytest.mark.parametrize("ev", [
    {"kind": "nope", "actor": "a"},
    {"kind": "item", "actor": "a", "state": "running"},                 # no item
    {"kind": "item", "actor": "a", "item": "X", "state": "sort-of"},    # bad state
    {"kind": "item", "item": "X", "state": "running"},                  # no actor
    {"kind": "note", "actor": "a", "ts": "yesterday"},                  # bad ts
])
def test_invalid_events_rejected(ev):
    with pytest.raises(EventError):
        validate(ev)


# ---- the tolerant, rotation-safe reader --------------------------------------------------------

def test_append_and_tail(tmp_path):
    p = str(tmp_path / "run" / "EVENTS.jsonl")
    log = EventLog(p)
    assert log.refresh() is False and log.events == []          # missing file is fine
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    assert log.refresh() is True and len(log.events) == 1
    assert log.refresh() is False                                 # nothing new
    append(p, {"kind": "note", "actor": "a", "detail": "two"})
    assert log.refresh() is True and [e["detail"] for e in log.events] == ["one", "two"]


def test_malformed_lines_are_skipped_and_counted(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a"})
    with open(p, "a") as f:
        f.write("{not json}\n")
        f.write(json.dumps({"kind": "item", "actor": "a", "item": "X", "state": "done"}) + "\n")  # done w/o evidence
    append(p, {"kind": "note", "actor": "b"})
    log = EventLog(p)
    log.refresh()
    assert len(log.events) == 2 and log.malformed == 2


def test_partial_trailing_line_waits_for_newline(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    line = json.dumps({"kind": "note", "actor": "a", "detail": "x"})
    with open(p, "w") as f:
        f.write(line[:10])                                        # a writer mid-line
    log = EventLog(p)
    log.refresh()
    assert log.events == [] and log.malformed == 0
    with open(p, "a") as f:
        f.write(line[10:] + "\n")
    log.refresh()
    assert len(log.events) == 1 and log.malformed == 0


def test_truncation_and_rotation_reread(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    for i in range(3):
        append(p, {"kind": "note", "actor": "a", "detail": str(i)})
    log = EventLog(p)
    log.refresh()
    assert len(log.events) == 3
    os.replace(p, p + ".old")                                     # rotated away
    append(p, {"kind": "note", "actor": "a", "detail": "fresh"})
    log.refresh()
    assert [e["detail"] for e in log.events] == ["fresh"]
    with open(p, "w"):                                            # truncated
        pass
    log.refresh()
    assert log.events == []


def test_concurrent_appends_never_interleave(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")

    def writer(n):
        for i in range(50):
            append(p, {"kind": "note", "actor": f"w{n}", "detail": "x" * 200 + str(i)})

    ts = [threading.Thread(target=writer, args=(n,)) for n in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    log = EventLog(p)
    log.refresh()
    assert len(log.events) == 400 and log.malformed == 0


# ---- snapshot rules ----------------------------------------------------------------------------

MODEL = {
    "campaign": "Suvarṇa",
    "tracks": [{"id": "T", "title": "T", "mode": "parallel"}],
    "items": [
        {"id": "A", "track": "T", "title": "detector item", "depends_on": [], "detector": {"type": "pr_merged", "pr": 1}},
        {"id": "B", "track": "T", "title": "event item", "depends_on": ["A"], "done_by": "event"},
        {"id": "C", "track": "T", "title": "decision item", "depends_on": [], "done_by": "decision", "decision": "N-1"},
        {"id": "D", "track": "T", "title": "stepped", "depends_on": [], "done_by": "event", "steps": ["s1", "s2", "s3", "s4"]},
    ],
    "decisions": [{"id": "N-1", "title": "approve", "recommendation": "yes"}],
}


def det(status, detail="x", progress=None):
    return {"status": status, "detail": detail, "checked_at": "2026-09-29T11:59:00+00:00", "source": "detector:t", "progress": progress}


def snap(events=(), dets=None):
    return build_snapshot(MODEL, list(events), dets or {}, {}, {}, now=NOW)


def status_of(s, iid):
    return next(i for t in s["tracks"] for i in t["items"] if i["id"] == iid)


def ev(**kw):
    return validate({"actor": "a", "ts": "2026-09-29T11:00:00+00:00", **kw})


def test_detector_decides_done():
    s = snap(dets={"A": det("done")})
    assert status_of(s, "A")["status"] == "done"
    assert status_of(s, "B")["status"] == "ready"                 # its dependency is done


def test_event_cannot_override_detector_to_done():
    s = snap([ev(kind="item", item="A", state="done", evidence="trust me")], dets={"A": det("pending", "PR open")})
    assert status_of(s, "A")["status"] == "conflict"
    assert status_of(s, "B")["status"] == "waiting"               # a conflict never releases dependents


def test_unmeasurable_detector_is_unknown_never_done():
    s = snap(dets={"A": det("error", "gh: auth")})
    assert status_of(s, "A")["status"] == "unknown"
    s2 = snap()                                                   # not yet measured at all
    assert status_of(s2, "A")["status"] == "unknown"


def test_event_running_shown_while_detector_pending():
    s = snap([ev(kind="item", item="A", state="running")], dets={"A": det("pending")})
    assert status_of(s, "A")["status"] == "running"
    assert status_of(s, "A")["elapsed_s"] == 3600


def test_decision_drives_item():
    assert status_of(snap(), "C")["status"] == "ready"
    s = snap([ev(kind="decision", decision="N-1", state="requested")])
    assert status_of(s, "C")["status"] == "running"
    s = snap([ev(kind="decision", decision="N-1", state="decided", detail="approved")])
    assert status_of(s, "C")["status"] == "done"
    assert next(d for d in s["decisions"] if d["id"] == "N-1")["status"] == "decided"


def test_steps_progress_and_overall():
    s = snap([ev(kind="item", item="D", state="running"),
              ev(kind="item", item="D", state="done", step="s1", evidence="e1"),
              ev(kind="item", item="D", state="done", step="s2", evidence="e2")],
             dets={"A": det("done")})
    d = status_of(s, "D")
    assert d["progress"] == 0.5 and [x["done"] for x in d["steps"]] == [True, True, False, False]
    # one of four items done (A) + half of D → 1.5 / 4 = 37.5 %
    assert s["overall"]["pct"] == 37.5


def test_waiting_vs_ready():
    s = snap()
    assert status_of(s, "B")["status"] == "waiting" and status_of(s, "B")["deps_open"] == ["A"]
