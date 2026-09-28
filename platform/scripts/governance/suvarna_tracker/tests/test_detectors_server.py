"""Detector isolation and register parsing; end-to-end server tests: live push, resilience, restart."""
import json
import os
import socket
import threading
import time
import urllib.request

import pytest

from suvarna_tracker import detectors as D
from suvarna_tracker.events import append
from suvarna_tracker.server import serve

REGISTER = """# register
### 0.1 · Count by state

| state | count |
|---|---|
| OPEN | 2 |
| CLOSED | 1 |

### 0.2 · Count by severity
| # | change | surfaced by | severity | depends_on | effort_h | state |
|---|---|---|---|---|---|---|
| R1 | a | s | BLOCKS_LAYER | — | 1 | OPEN |
| R2 | pipe \\| inside | s | DEGRADES | — | 1 | CLOSED 2026-09-28 — done |
| R3 | c | s | DEGRADES | — | 1 | **OPEN** |
| R4 | d | s | COSMETIC | — | 1 | OPEN — x | EXTRA RULING CELL |

## build-system rows (two extra columns)
| # | change | surfaced by | kind | severity | depends_on | effort_h | order | state |
|---|---|---|---|---|---|---|---|---|
| R5 | e | s | OTHER | BLOCKS_FREEZE | — | 1 | first | OPEN |
| R6 | f | s | OTHER | DEGRADES | — | 1 | last | CLOSED_ON_BRANCH |
"""


@pytest.fixture
def nik(tmp_path):
    root = tmp_path / "nik"
    (root / "00_ARCHITECTURE/briefs/nirmana").mkdir(parents=True)
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    (root / "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md").write_text(REGISTER)
    (root / "00_ARCHITECTURE/control/asset_gaps.jsonl").write_text(
        json.dumps({"asset": "_schema"}) + "\n"
        + json.dumps({"asset": "a1", "gap_id": "g1", "state": "OPEN"}) + "\n"
        + json.dumps({"asset": "a2", "gap_id": "g2", "state": "OPEN"}) + "\n"
        + json.dumps({"asset": "a2", "gap_id": "g2", "state": "CLOSED"}) + "\n")
    (root / "00_ARCHITECTURE/control/asset_certs.jsonl").write_text(
        json.dumps({"asset": "_schema"}) + "\n" + json.dumps({"asset": "a2", "criterion": "Idem.pattern", "verdict": "PASS"}) + "\n")
    return str(root)


def dets(nik, tmp_path):
    return D.Detectors(D.Config(repo=str(tmp_path), nikasha_root=nik, pgenv=None, home=str(tmp_path)))


def wait_result(det, spec, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = det.get(spec)
        if r is not None:
            return r
        time.sleep(0.05)
    raise AssertionError("detector never produced a result")


# ---- register ----------------------------------------------------------------------------------

def test_register_parsing_handles_escaped_pipes_and_flags_extra_cells(nik):
    reg = D.parse_register(os.path.join(nik, "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"))
    assert set(reg["rows"]) == {"R1", "R2", "R3", "R4", "R5", "R6"}
    assert reg["rows"]["R2"]["state_class"] == "CLOSED"          # escaped pipe did not shift columns
    assert reg["rows"]["R3"]["state_class"] == "OPEN"            # bold marker handled
    assert reg["malformed"] == ["R4"]                            # the extra cell is flagged
    # a table with a different layout is read by its own header, not by fixed positions
    assert reg["rows"]["R5"]["severity"] == "BLOCKS_FREEZE" and reg["rows"]["R5"]["state_class"] == "OPEN"
    assert reg["rows"]["R6"]["severity"] == "DEGRADES" and reg["rows"]["R6"]["state"] == "CLOSED_ON_BRANCH"
    assert reg["header"] == {"OPEN": 2, "CLOSED": 1}


def test_tally_detector_catches_drift(nik, tmp_path):
    d = dets(nik, tmp_path)
    spec = {"type": "register_tally_consistent"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "OPEN: header 2 vs rows 4" in r.detail


def test_rows_closed_progress(nik, tmp_path):
    d = dets(nik, tmp_path)
    spec = {"type": "register_rows_closed", "rows": ["R1", "R2"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running" and r.progress == 0.5


def test_broken_detector_is_isolated_and_reports_error(nik, tmp_path):
    d = dets(nik, tmp_path)
    bad = {"type": "register_rows_closed", "rows": ["R999"]}
    boom = {"type": "no_such_detector"}
    good = {"type": "register_wellformed"}
    d.poll([bad, boom, good])
    assert wait_result(d, bad).status == "error"
    assert wait_result(d, boom).status == "error"
    assert wait_result(d, good).status == "pending"              # R4 is malformed; still measured


def test_ttl_prevents_rerun(nik, tmp_path):
    d = dets(nik, tmp_path)
    spec = {"type": "register_wellformed"}
    calls = []
    orig = d.d_register_wellformed
    d.d_register_wellformed = lambda s: (calls.append(1), orig(s))[1]
    d.poll([spec]); wait_result(d, spec)
    d.poll([spec]); time.sleep(0.2)
    assert len(calls) == 1


def test_db_detector_without_env_is_error_not_pass(nik, tmp_path):
    d = dets(nik, tmp_path)
    spec = {"type": "db_columns_exist", "columns": [["t", "c"]]}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


def test_elevation_proxy(nik):
    cfg = D.Config(repo=".", nikasha_root=nik, pgenv=None, home=".")
    assert D.elevated_assets(cfg) == {"a2"}                      # a1 has an open gap and no PASS certification


# ---- end-to-end server ---------------------------------------------------------------------------

MODEL = {
    "campaign": "Suvarṇa", "plan_ref": "test",
    "tracks": [{"id": "T", "title": "Track", "mode": "parallel"}],
    "items": [{"id": "I1", "track": "T", "title": "one", "depends_on": [], "done_by": "event"},
              {"id": "I2", "track": "T", "title": "two", "depends_on": ["I1"], "done_by": "event"}],
    "decisions": [],
}


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


@pytest.fixture
def server(tmp_path, nik):
    home = tmp_path / "home"
    (home / "run").mkdir(parents=True)
    model = tmp_path / "model.json"
    model.write_text(json.dumps(MODEL))
    cfg = {"home": str(home), "events": str(home / "run/EVENTS.jsonl"), "snapshot": str(home / "run/snapshot.json"),
           "hold": str(home / "run/SUVARNA_HOLD"), "model": str(model), "repo": str(tmp_path), "nikasha_root": nik,
           "pgenv": None, "db_port": 1, "metrics_ttl": 3600, "detectors_enabled": False}
    port = free_port()
    httpd, engine = serve(port, cfg)
    th = threading.Thread(target=httpd.serve_forever, daemon=True); th.start()
    base = f"http://127.0.0.1:{port}"
    t0 = time.time()
    while time.time() - t0 < 10:
        try:
            if json.load(urllib.request.urlopen(base + "/api/state", timeout=2)).get("tracks"):
                break
        except Exception:
            pass
        time.sleep(0.1)
    yield {"base": base, "cfg": cfg, "engine": engine, "httpd": httpd, "model": model}
    engine.stop(); httpd.shutdown(); httpd.server_close()


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=5))


def item(snap, iid):
    return next(i for t in snap["tracks"] for i in t["items"] if i["id"] == iid)


def sse_versions(base, stop_after, timeout=10):
    """Read SSE snapshots until `stop_after(snapshot)` is true; return the snapshots seen."""
    seen = []
    resp = urllib.request.urlopen(base + "/events", timeout=timeout)
    buf, t0 = b"", time.time()
    while time.time() - t0 < timeout:
        line = resp.readline()
        if not line:
            break
        buf += line
        if line == b"\n" and b"data: " in buf:
            data = [l for l in buf.split(b"\n") if l.startswith(b"data: ")][0][6:]
            snap = json.loads(data)
            seen.append(snap)
            buf = b""
            if stop_after(snap):
                break
    resp.close()
    return seen


def test_page_and_api_served(server):
    html = urllib.request.urlopen(server["base"] + "/", timeout=5).read().decode()
    assert "Suvarṇa" in html and "/static/app.js" in html
    assert urllib.request.urlopen(server["base"] + "/static/app.js", timeout=5).status == 200
    s = get(server["base"] + "/api/state")
    assert item(s, "I1")["status"] == "ready" and item(s, "I2")["status"] == "waiting"
    h = get(server["base"] + "/api/health")
    assert h["ok"] is True


def test_path_traversal_blocked(server):
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(server["base"] + "/static/../server.py", timeout=5)


def test_event_is_pushed_live_within_seconds(server):
    ev_path = server["cfg"]["events"]

    def later():
        time.sleep(1.0)
        append(ev_path, {"kind": "item", "actor": "builder", "item": "I1", "state": "done", "evidence": "proof.md"})

    threading.Thread(target=later, daemon=True).start()
    t0 = time.time()
    seen = sse_versions(server["base"], lambda s: item(s, "I1")["status"] == "done", timeout=10)
    latency = time.time() - t0 - 1.0
    assert item(seen[-1], "I1")["status"] == "done"
    assert item(seen[-1], "I2")["status"] == "ready"             # dependency released in the same push
    assert latency < 3.0, f"push took {latency:.1f}s"


def test_corrupt_lines_do_not_break_the_view(server):
    with open(server["cfg"]["events"], "a") as f:
        f.write("garbage\n{\"kind\":\"item\"}\n")
    append(server["cfg"]["events"], {"kind": "note", "actor": "a", "detail": "after garbage"})
    time.sleep(2.5)
    s = get(server["base"] + "/api/state")
    assert s["health"]["event_log"]["malformed"] == 2
    assert s["activity"][0]["detail"] == "after garbage"


def test_bad_model_edit_keeps_last_good_model(server):
    time.sleep(1.1)                                               # ensure a new mtime
    server["model"].write_text("{ this is not json")
    time.sleep(2.5)
    s = get(server["base"] + "/api/state")
    assert "rejected" in (s["health"]["model_error"] or "")
    assert item(s, "I1")                                          # still showing the previous plan


def test_hold_switch_visible(server):
    open(server["cfg"]["hold"], "w").close()
    time.sleep(6)                                                 # health refreshes at least every 5 s
    assert get(server["base"] + "/api/state")["health"]["hold"] is True


def test_snapshot_persisted_and_restored(server, tmp_path):
    append(server["cfg"]["events"], {"kind": "item", "actor": "b", "item": "I1", "state": "running"})
    time.sleep(2.5)
    with open(server["cfg"]["snapshot"]) as f:
        disk = json.load(f)
    assert item(disk, "I1")["status"] == "running"
    # a second engine on the same home starts with the saved state before its first tick
    from suvarna_tracker.server import Engine
    e2 = Engine(server["cfg"])
    assert item(e2.snapshot, "I1")["status"] == "running"
    assert e2.snapshot["health"].get("restored_from_disk") is True


def test_quiet_stream_still_sends_visible_heartbeat(server):
    """With nothing changing, the stream must still deliver a named event (not just a comment) within ~5 s,
    so the page reads 'quiet but live' instead of raising a false 'stale' alarm."""
    resp = urllib.request.urlopen(server["base"] + "/events", timeout=15)
    t0, got = time.time(), None
    while time.time() - t0 < 12:
        line = resp.readline()
        if line.startswith(b"event: alive"):
            data = resp.readline()
            got = json.loads(data[len(b"data: "):])
            break
    resp.close()
    assert got is not None, "no alive event on a quiet stream"
    assert got["tick_age_s"] < 5 and "version" in got
