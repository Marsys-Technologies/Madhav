"""Real sleep-60 children exercise the tracker boundary; no installed service is used."""
from __future__ import annotations

import concurrent.futures
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D
from pravaha_tracker import server as S


@pytest.fixture
def stubs(tmp_path, monkeypatch):
    for name in ("git", "gh", "pmset", "psql"):
        binary = tmp_path / name
        binary.write_text(f'''#!{sys.executable}
import json, os, sys, time
from pathlib import Path
root = Path(__file__).parent
name = Path(__file__).name
if (root / (name + "-hang")).exists():
    (root / (name + "-pid")).write_text(str(os.getpid()))
    time.sleep(60)
if name == "pmset": print("Now drawing from 'AC Power'")
elif name == "gh": print(json.dumps({{"state": "MERGED", "mergedAt": "now", "mergeable": "MERGEABLE"}}))
elif name == "git" and sys.argv[1] == "show": print("receipt")
''')
        binary.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    yield tmp_path
    for pidfile in tmp_path.glob("*-pid"):
        try:
            os.killpg(int(pidfile.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            pass


def wait_for(path, timeout=2):
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert path.exists(), f"child did not start: {path}"


def read(base, path):
    try:
        response = urllib.request.urlopen(base + path, timeout=0.8)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return json.load(response)


@pytest.fixture
def tracker(stubs):
    model = stubs / "model.json"
    model.write_text(json.dumps({"campaign": "completed", "tracks": [], "items": [], "streams": [], "decisions": [], "phases": []}))
    cfg = dict(home=str(stubs), events=str(stubs / "EVENTS.jsonl"), snapshot=str(stubs / "snapshot.json"),
               backup_dir=str(stubs / "backup"), hold=str(stubs / "HOLD"), model=str(model), repo=str(stubs),
               pgenv=None, db_port=1, detectors_enabled=False, git_every_s=3600, backup_every_s=3600, tick_budget_s=8)
    eng = S.Engine(cfg)
    with patch.object(D, "port_open", return_value=False):
        eng.tick()
        httpd = S._QuietServer(("127.0.0.1", 0), S.make_handler(eng))
        serving = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02})
        serving.start()
        yield eng, f"http://127.0.0.1:{httpd.server_port}"
        eng.stop()
        httpd.shutdown()
        httpd.server_close()
        serving.join(2)
        eng.det._pool.shutdown(wait=True)


def test_completed_tick_reads_age_and_keep_power_after_sleep60_timeout(tracker, stubs):
    """Catches missing age fields and discarding last power value on timeout."""
    eng, base = tracker
    before = read(base, "/api/state")
    (stubs / "pmset-hang").touch()
    eng._dirty = True
    tick = threading.Thread(target=eng.tick)
    tick.start()
    try:
        wait_for(stubs / "pmset-pid")
        started = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            replies = list(pool.map(lambda p: read(base, p), ["/api/health", "/api/state", "/api/next", "/api/item?id=absent"] * 3))
        assert time.monotonic() - started < 1
        assert replies[1]["campaign"] == "completed"
        assert replies[1]["version"] == before["version"]
        assert replies[1]["tick_age_s"] >= before["tick_age_s"]
        with urllib.request.urlopen(base + "/events", timeout=0.8) as events:
            lines = []
            while True:
                line = events.readline().decode().strip()
                if not line:
                    break
                lines.append(line)
            event = json.loads(next(line[6:] for line in lines if line.startswith("data: ")))
            assert event["version"] == before["version"]
            assert event["campaign"] == "completed"
            assert event["tick_age_s"] >= before["tick_age_s"]
        age = replies[0]["tick_age_s"]
        time.sleep(0.2)
        assert read(base, "/api/state")["tick_age_s"] > age
        tick.join(5.8)
        assert not tick.is_alive(), "power child exceeded the five-second call limit"
        health = read(base, "/api/health")
        assert health["power"] == "ac", "timeout discarded last measured power value"
        assert health["sources"]["power"]["stale"] is True
        assert health["sources"]["power"]["age_s"] >= 5
        assert health["tick_abandoned"] is False, "a timed-out source discarded the entire tick"
        assert read(base, "/api/state")["tick_age_s"] < 1
    finally:
        if tick.is_alive():
            os.killpg(int((stubs / "pmset-pid").read_text()), signal.SIGKILL)
        tick.join(2)


@pytest.mark.parametrize("requested_timeout", [None, 90])
def test_every_external_call_caps_sleep60_at_five_seconds(stubs, requested_timeout):
    """Catches both the default and explicitly longer subprocess timeouts."""
    (stubs / "git-hang").touch()
    outcomes = []
    def invoke():
        try:
            D._run(["git", "fetch", "-q", "origin", "main"], **({} if requested_timeout is None else {"timeout": requested_timeout}))
        except D.subprocess.TimeoutExpired:
            outcomes.append("timeout")
    start = time.monotonic()
    thread = threading.Thread(target=invoke)
    thread.start()
    try:
        wait_for(stubs / "git-pid")
        thread.join(5.8)
        assert not thread.is_alive(), "external call ignored the hard five-second ceiling"
        assert outcomes == ["timeout"]
        assert 4.8 <= time.monotonic() - start < 5.9
        with pytest.raises(ProcessLookupError):
            os.kill(int((stubs / "git-pid").read_text()), 0)
    finally:
        if thread.is_alive():
            os.killpg(int((stubs / "git-pid").read_text()), signal.SIGKILL)
        thread.join(2)


def test_dashboard_timeout_keeps_last_measurement_and_marks_gh_stale(tracker, stubs):
    eng, base = tracker
    spec = {"type": "pr_merged", "pr": 1}
    key = eng.det.key(spec)
    eng.det._run_one(key, spec)
    previous = eng.det.get(spec)
    assert previous.status == "done"
    (stubs / "gh-hang").touch()
    thread = threading.Thread(target=eng.det._run_one, args=(key, spec))
    thread.start()
    try:
        wait_for(stubs / "gh-pid")
        assert read(base, "/api/health")["power"] == "ac"
        thread.join(5.8)
        assert not thread.is_alive(), "gh timeout was not bounded"
        result = eng.det.get(spec).to_dict()
        assert result["status"] == "done"
        assert result["checked_at"] == previous.checked_at
        assert result["stale"] is True and result["age_s"] >= 5
        eng.tick()
        assert read(base, "/api/health")["sources"]["gh"]["stale"] is True
    finally:
        if thread.is_alive():
            os.killpg(int((stubs / "gh-pid").read_text()), signal.SIGKILL)
        thread.join(2)


def test_verify_uses_own_bounded_worker_and_refuses_late_success(tracker, monkeypatch):
    eng, base = tracker
    eng.det.cfg.verify_budget_s = 0.15
    eng.model = {**eng.model, "items": [{"id": "live", "detector": {"type": "file_exists", "path": "unused"}}]}
    release, entered = threading.Event(), threading.Event()
    workers = []
    def stalled(spec):
        workers.append(threading.current_thread().name)
        entered.set()
        release.wait(3)
        return D.DetectorResult("done", "too late", "now", "test")
    monkeypatch.setattr(eng.det, "d_file_exists", stalled)
    try:
        started = time.monotonic()
        result = read(base, "/api/verify?id=live")["detector"]
        assert time.monotonic() - started < 0.7
        assert entered.is_set()
        assert result["status"] == "error", "verification accepted a result outside its budget"
        assert workers[0].startswith("verify-"), "request thread performed live measurement"
        assert read(base, "/api/health")["power"] == "ac"
    finally:
        release.set()


def test_verify_refuses_hung_post_request_fetch_despite_cached_done(tracker, stubs):
    eng, base = tracker
    spec = {"type": "branch_merged", "ref": "local"}
    eng.det.results[eng.det.key(spec)] = D.DetectorResult("done", "old success", "old", "test")
    eng.det._fetched["main"] = time.time()
    eng.model = {**eng.model, "items": [{"id": "live", "detector": spec}]}
    (stubs / "git-hang").touch()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        # This request legitimately waits for a live five-second measurement.
        def verify():
            with urllib.request.urlopen(base + "/api/verify?id=live", timeout=6.5) as response:
                return json.load(response)
        result = pool.submit(verify)
        try:
            wait_for(stubs / "git-pid")
            started = time.monotonic()
            read(base, "/api/health")
            read(base, "/api/state")
            assert time.monotonic() - started < 1
            reply = result.result(timeout=5.8)
            assert reply["detector"]["status"] == "error"
            assert eng.det.get(spec).status == "done", "verify mutated dashboard cache"
            eng._dirty = True
            eng.tick()
            assert read(base, "/api/health")["sources"]["git"]["stale"] is True
        finally:
            try:
                os.killpg(int((stubs / "git-pid").read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_cached_reads_do_not_take_publication_or_detector_locks(tracker):
    """A request cannot inherit a collector's or detector worker's lock delay."""
    eng, base = tracker
    with eng.cond, eng.det._lock, eng.det._fetch_lock:
        started = time.monotonic()
        assert read(base, "/api/state")["campaign"] == "completed"
        assert read(base, "/api/health")["power"] == "ac"
        assert time.monotonic() - started < 1


def test_verify_same_ref_wait_is_bounded_without_using_old_success(tracker):
    eng, base = tracker
    eng.det.cfg.verify_budget_s = 0.15
    spec = {"type": "branch_merged", "ref": "local"}
    eng.model = {**eng.model, "items": [{"id": "live", "detector": spec}]}
    older = D.Future()
    eng.det._fetching["main"] = (older, time.monotonic_ns() - 1_000_000)
    eng.det.results[eng.det.key(spec)] = D.DetectorResult("done", "old", "old", "test")
    try:
        assert read(base, "/api/verify?id=live")["detector"]["status"] == "error"
        assert read(base, "/api/state")["campaign"] == "completed"
    finally:
        older.set_exception(RuntimeError("fixture released"))


def test_dashboard_preserves_tick_age_and_displays_stale_source_ages():
    """Exercise the shipped browser script, including SSE acceptance and health rendering."""
    import subprocess

    app = Path(S.STATIC) / "app.js"
    script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = {}, listeners = {};
const document = {getElementById(id) {
  return nodes[id] ||= {textContent: '', innerHTML: '', className: '', style: {}};
}};
class EventSource {
  addEventListener(name, handler) { listeners[name] = handler; }
  close() {}
}
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
  document, EventSource, Date, navigator: {}, setInterval: () => 1,
  clearInterval() {}, fetch: () => new Promise(() => {})
});
const snapshot = {tracks: [], decisions: [], activity: [], now: [], next: [], attention: [], done: [], version: 1,
  overall: {pct: 0, done: 0, running: 0, ready: 0, waiting: 0, blocked: 0, unknown: 0, total: 0},
  generated_at: new Date().toISOString(), tick_age_s: 45,
  health: {power: 'ac', sources: {gh: {stale: true, age_s: 65}, power: {stale: true, age_s: null}}}
};
listeners.snapshot({data: JSON.stringify(snapshot)});
assert.match(nodes['live-text'].textContent, /engine stuck.*45s/);
assert.match(nodes.health.innerHTML, /gh: stale.*1m/);
assert.match(nodes.health.innerHTML, /power: stale.*unmeasured/);
assert.ok(!nodes.health.innerHTML.includes('Checkers: all measuring'));
assert.ok(!nodes.foot.textContent.startsWith('Render error'), nodes.foot.textContent);
'''
    result = subprocess.run(["node", "-e", script, str(app)], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr


def test_campaign_burst_can_queue_ten_connections_before_accept(tracker):
    """A burst must fit while the server thread is waiting to be scheduled."""
    import socket

    eng, _ = tracker
    httpd = S._QuietServer(("127.0.0.1", 0), S.make_handler(eng))
    connections = []
    try:
        for _ in range(10):
            connections.append(socket.create_connection(httpd.server_address, timeout=0.1))
        assert len(connections) == 10
    finally:
        for connection in connections:
            connection.close()
        httpd.server_close()


def test_unmeasured_fetch_stays_visible_after_successful_git_read(tracker, stubs):
    """A successful local git command cannot measure a timed-out remote fetch."""
    eng, base = tracker
    with D.external_context(eng.det.sources):
        D._run(["git", "show", "main:receipt"])
        (stubs / "git-hang").touch()
        with pytest.raises(D.subprocess.TimeoutExpired):
            D._run(["git", "fetch", "-q", "origin", "main"], timeout=0.1)
        (stubs / "git-hang").unlink()
        D._run(["git", "show", "main:receipt"])
    eng._dirty = True
    eng.tick()
    health = read(base, "/api/health")
    assert health["degraded"] is True
    assert health["sources"]["git"]["stale"] is True
    assert health["sources"]["git"]["age_s"] is None, "local reads supplied an age for an unmeasured fetch"
    with D.external_context(eng.det.sources):
        D._run(["git", "fetch", "-q", "origin", "main"])
    eng._dirty = True
    eng.tick()
    assert read(base, "/api/health")["sources"]["git"]["stale"] is False


def test_completed_power_change_updates_the_sse_version(tracker):
    eng, base = tracker
    previous = read(base, "/api/state")
    eng._dirty = True
    with patch.object(D, "power_source", return_value="battery 60%"):
        eng.tick()
    completed = read(base, "/api/state")
    assert completed["health"]["power"] == "battery 60%"
    assert completed["version"] > previous["version"], "SSE clients would retain the previous power value"
