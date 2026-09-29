"""Unit tests: the event log (append, validation, tolerant tailing) and the snapshot builder's rules."""
import datetime as dt
import json
import os
import threading

import pytest

from suvarna_tracker import events as EV
from suvarna_tracker.events import EventError, EventLog, append, read_since_offset, validate
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


# ---- read_since_offset / CLI (CODE-19): a stateless Conductor pass's own reader -----------------

def test_read_since_offset_missing_file_is_empty_not_error(tmp_path):
    r = read_since_offset(str(tmp_path / "nope.jsonl"), 0)
    assert r == {"events": [], "offset": 0, "malformed": 0}


def test_read_since_offset_from_zero_reads_everything(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    append(p, {"kind": "note", "actor": "a", "detail": "two"})
    r = read_since_offset(p, 0)
    assert len(r["events"]) == 2 and r["malformed"] == 0
    assert r["offset"] == os.path.getsize(p)


def test_read_since_offset_returns_only_new_lines(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    mid = os.path.getsize(p)
    append(p, {"kind": "note", "actor": "a", "detail": "two"})
    r = read_since_offset(p, mid)
    assert len(r["events"]) == 1 and r["events"][0]["detail"] == "two"
    assert r["offset"] == os.path.getsize(p)


def test_read_since_offset_skips_and_counts_malformed_lines(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        f.write("not json at all\n")
        f.write(json.dumps({"kind": "note", "actor": "a", "detail": "ok", "ts": "2026-09-29T00:00:00+00:00"}) + "\n")
    r = read_since_offset(p, 0)
    assert len(r["events"]) == 1 and r["malformed"] == 1


def test_read_since_offset_never_counts_an_incomplete_trailing_line(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    complete_size = os.path.getsize(p)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "note", "actor": "a", "detail": "partial"}))  # no trailing newline
    r = read_since_offset(p, 0)
    assert len(r["events"]) == 1  # the incomplete line is not returned
    assert r["offset"] == complete_size  # and not counted into the new offset
    # once the line completes, a call at the same offset picks it up
    with open(p, "a", encoding="utf-8") as f:
        f.write("\n")
    r2 = read_since_offset(p, r["offset"])
    assert len(r2["events"]) == 1 and r2["events"][0]["detail"] == "partial"


def test_read_since_offset_rereads_from_start_if_file_shrank(tmp_path):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    append(p, {"kind": "note", "actor": "a", "detail": "two"})
    big_offset = os.path.getsize(p)
    with open(p, "w", encoding="utf-8") as f:  # truncate + rewrite (rotation)
        pass
    append(p, {"kind": "note", "actor": "a", "detail": "fresh"})
    r = read_since_offset(p, big_offset)
    assert len(r["events"]) == 1 and r["events"][0]["detail"] == "fresh"


def test_read_since_offset_cli_prints_events_and_offset(tmp_path, capsys):
    p = str(tmp_path / "EVENTS.jsonl")
    append(p, {"kind": "note", "actor": "a", "detail": "one"})
    rc = EV.main(["--since-offset", "0", "--path", p])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["events"]) == 1 and out["offset"] == os.path.getsize(p)


def test_default_path_reads_suvarna_events_env(tmp_path, monkeypatch):
    override = str(tmp_path / "custom.jsonl")
    monkeypatch.setenv("SUVARNA_EVENTS", override)
    assert EV.default_path() == override


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


# ---- Fix 2: the authoritative decisions log drives done_by:decision items, not decision events -

def decisions_log(latest: dict) -> dict:
    return {"latest": latest, "malformed": 0}


def test_decisions_none_keeps_old_event_driven_behaviour():
    """Backward compatibility: build_snapshot(..., decisions=None) is unchanged from before Fix 2."""
    s = build_snapshot(MODEL, [ev(kind="decision", decision="N-1", state="decided", detail="approved")],
                       {}, {}, {}, now=NOW, decisions=None)
    assert status_of(s, "C")["status"] == "done"


def test_event_alone_no_longer_marks_a_decision_item_done():
    """The Fix 2 defect: previously ANY actor's decided/delegated event flipped the gate done."""
    s = build_snapshot(MODEL, [ev(kind="decision", decision="N-1", state="decided", detail="approved", actor="anyone")],
                       {}, {}, {}, now=NOW, decisions=decisions_log({}))
    assert status_of(s, "C")["status"] != "done"
    row = next(d for d in s["decisions"] if d["id"] == "N-1")
    assert row["status"] == "conflict" and row["conflict"] == {"event": "decided", "log": "none"}


def test_log_decided_marks_the_item_done_with_evidence():
    log = decisions_log({"N-1": {"id": "N-1", "state": "decided", "detail": "approved for real",
                                 "source": "Native, 2026-09-29: yes", "ts": "2026-09-29T10:00:00+00:00"}})
    s = build_snapshot(MODEL, [], {}, {}, {}, now=NOW, decisions=log)
    c = status_of(s, "C")
    assert c["status"] == "done"
    assert "approved for real" in c["evidence"] and "Native, 2026-09-29: yes" in c["evidence"]


def test_log_delegated_shows_waiting_not_done():
    log = decisions_log({"N-1": {"id": "N-1", "state": "delegated", "detail": "handed off",
                                 "source": "Native, 2026-09-29: delegate", "delegated_to": "L3 family session",
                                 "ts": "2026-09-29T10:00:00+00:00"}})
    s = build_snapshot(MODEL, [], {}, {}, {}, now=NOW, decisions=log)
    c = status_of(s, "C")
    assert c["status"] == "waiting"
    assert c["detail"] == "delegated to L3 family session; not yet decided"


def test_requested_event_still_shows_running_awaiting_native_when_log_has_no_record():
    log = decisions_log({})
    s = build_snapshot(MODEL, [ev(kind="decision", decision="N-1", state="requested")], {}, {}, {}, now=NOW, decisions=log)
    assert status_of(s, "C")["status"] == "running"


def test_decision_event_disagreeing_with_log_is_a_conflict_row():
    log = decisions_log({"N-1": {"id": "N-1", "state": "delegated", "detail": "handed off",
                                 "source": "Native, 2026-09-29: delegate", "ts": "2026-09-29T10:00:00+00:00"}})
    s = build_snapshot(MODEL, [ev(kind="decision", decision="N-1", state="decided", detail="I say it's decided")],
                       {}, {}, {}, now=NOW, decisions=log)
    row = next(d for d in s["decisions"] if d["id"] == "N-1")
    assert row["status"] == "conflict"
    assert row["conflict"] == {"event": "decided", "log": "delegated"}
    # the item itself follows the log (delegated → waiting), never the disagreeing event
    assert status_of(s, "C")["status"] == "waiting"


def test_decision_event_warnings_flag_unauthorized_actors():
    """CODE-14 (S2): only strategic-suvarna is authorized to write the decisions log going forward
    — a decided/delegated decision *event* from "steward" is now flagged too, same as any other
    unexpected actor."""
    evs = [ev(kind="decision", decision="N-1", state="decided", detail="x", actor="random-builder"),
           ev(kind="decision", decision="N-1", state="decided", detail="x", actor="steward")]
    s = build_snapshot(MODEL, evs, {}, {}, {}, now=NOW, decisions=decisions_log({}))
    warnings = s["health"]["decision_event_warnings"]
    assert len(warnings) == 2
    assert any("random-builder" in w for w in warnings)
    assert any("steward" in w for w in warnings)


def test_detector_activity_does_not_bypass_open_dependencies():
    """An open PR on a gated item (e.g. #2731 before its preconditions) shows as waiting, not running."""
    import datetime as dt
    from suvarna_tracker.state import build_snapshot
    model = {"tracks": [{"id": "T", "title": "t", "mode": "sequential"}], "decisions": [],
             "items": [{"id": "A", "track": "T", "title": "a", "depends_on": [], "done_by": "event"},
                       {"id": "B", "track": "T", "title": "b", "depends_on": ["A"], "detector": {"type": "pr_merged", "pr": 1}}]}
    det = {"B": {"status": "running", "detail": "PR #1 open", "checked_at": "2026-09-29T00:00:00+00:00", "progress": None}}
    snap = build_snapshot(model, [], det, {}, {}, dt.datetime(2026, 9, 29, tzinfo=dt.timezone.utc))
    b = next(i for i in snap["tracks"][0]["items"] if i["id"] == "B")
    assert b["status"] == "waiting" and b["detail"] == "PR #1 open" and "soft" not in b
    # once A is done, the same detector reading shows as running
    ev = [{"kind": "item", "actor": "x", "item": "A", "state": "done", "evidence": "e", "ts": "2026-09-29T00:00:00+00:00"}]
    snap = build_snapshot(model, ev, det, {}, {}, dt.datetime(2026, 9, 29, tzinfo=dt.timezone.utc))
    assert next(i for i in snap["tracks"][0]["items"] if i["id"] == "B")["status"] == "running"
