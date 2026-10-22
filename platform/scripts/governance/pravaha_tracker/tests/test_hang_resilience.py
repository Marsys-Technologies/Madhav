"""Regressions for the live tracker's unresponsive health/state endpoints.

All slow I/O is gated and released in cleanup; no installed service is changed.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time
import urllib.request
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D
from pravaha_tracker import server as S


@pytest.fixture
def engine(tmp_path):
    model = tmp_path / "model.json"
    model.write_text(json.dumps({"campaign": "cached", "tracks": [], "items": [], "streams": [], "decisions": [], "phases": []}))
    cfg = {"home": str(tmp_path), "events": str(tmp_path / "EVENTS.jsonl"),
           "snapshot": str(tmp_path / "snapshot.json"), "backup_dir": str(tmp_path / "backup"),
           "hold": str(tmp_path / "HOLD"), "model": str(model), "repo": str(tmp_path),
           "pgenv": None, "db_port": 1, "detectors_enabled": False,
           "git_every_s": 3600, "backup_every_s": 3600, "tick_budget_s": 2}
    with patch.object(D, "power_source", return_value="ac"), patch.object(D, "port_open", return_value=False):
        eng = S.Engine(cfg)
        eng.tick()
        assert eng.snapshot, "initial fixture snapshot did not finish"
        eng.cfg["tick_budget_s"] = 0.15
        yield eng
        eng.stop()
        eng.det._pool.shutdown(wait=True)


@pytest.fixture
def http(engine):
    httpd = S._QuietServer(("127.0.0.1", 0), S.make_handler(engine))
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02})
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()
    thread.join(2)


def get(url):
    # A timeout fails the regression instead of leaving the suite hung indefinitely.
    try:
        with urllib.request.urlopen(url, timeout=0.7) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        return json.load(exc)


def concurrent_reads(base):
    start = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(get, [base + path for path in
                                    ("/api/health", "/api/state", "/api/health", "/api/health")]))
    assert time.monotonic() - start < 1
    return results


@pytest.mark.parametrize("probe", ["power_source", "port_open"])
def test_health_uses_cached_probes_even_when_external_probe_stalls(engine, http, probe):
    entered, release = threading.Event(), threading.Event()

    def slow_probe(*args):
        entered.set()
        release.wait(3)
        return "battery"

    try:
        with patch.object(D, probe, side_effect=slow_probe):
            replies = concurrent_reads(http)
        assert replies[0]["power"] == "ac"
        assert not entered.is_set(), "a health request invoked an external probe"
    finally:
        release.set()


def test_snapshot_persistence_does_not_lock_out_http(engine, http):
    entered, release = threading.Event(), threading.Event()
    original = S.Engine._persist

    def slow_persist(self, snap):
        entered.set()
        release.wait(3)
        return original(self, snap)

    engine.model = {**engine.model, "campaign": "changed"}
    engine._dirty = True
    with patch.object(S.Engine, "_persist", slow_persist):
        tick = threading.Thread(target=engine._rebuild)
        tick.start()
        try:
            assert entered.wait(1)
            concurrent_reads(http)
        finally:
            release.set()
            tick.join(2)


def test_over_budget_tick_is_abandoned_and_never_publishes_late(engine, http):
    entered, release = threading.Event(), threading.Event()
    before = engine.snapshot
    original = S.Engine._reload_model
    calls = []

    def stalled_reload(self):
        calls.append(1)
        entered.set()
        release.wait(3)
        original(self)
        self.model = {**self.model, "campaign": "late result must be discarded"}
        self._dirty = True

    with patch.object(S.Engine, "_reload_model", stalled_reload):
        tick = threading.Thread(target=engine.tick)
        tick.start()
        try:
            assert entered.wait(1)
            tick.join(0.5)
            returned_within_budget = not tick.is_alive()
            health = concurrent_reads(http)[0]
            # Calling again while an abandoned worker is stuck must not spawn more workers.
            if returned_within_budget:
                engine.tick()
            same_before_release = engine.snapshot is before
        finally:
            release.set()
            tick.join(2)
            worker = getattr(engine, "_tick_worker", None)
            if worker:
                worker.join(2)
    assert returned_within_budget, "tick waited indefinitely for a slow operation"
    assert any("budget" in error for error in health["tick_errors"])
    assert health["ok"] is False
    assert calls == [1], "stuck ticks accumulated workers"
    assert same_before_release and engine.snapshot is before, "an abandoned tick published its result"
    engine.tick()
    assert engine.health()["tick_errors"], "recovery erased the timeout diagnostic"
    assert engine.snapshot["campaign"] == "cached"
    assert any("budget" in error for error in engine.snapshot["health"]["tick_errors"])


def test_slow_detector_verify_does_not_delay_cached_health(engine, http):
    entered, release = threading.Event(), threading.Event()
    engine.model = {**engine.model, "items": [{"id": "slow", "detector": {"type": "file_exists", "path": "unused"}}]}

    def slow_detector(spec):
        entered.set()
        release.wait(3)
        return D.DetectorResult("pending", "slow", "now", "test")

    with patch.object(engine.det, "d_file_exists", slow_detector):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            verifying = pool.submit(get, http + "/api/verify?id=slow")
            try:
                assert entered.wait(1)
                concurrent_reads(http)
            finally:
                release.set()
            assert verifying.result()["detector"]["status"] == "pending"


@pytest.mark.parametrize("shell", [False, True])
@pytest.mark.parametrize("startup_delay", [0, 1.25], ids=["normal-start", "delayed-start"])
def test_hung_git_timeout_kills_descendants_holding_output_pipes(tmp_path, monkeypatch, shell, startup_delay):
    """Killing only git leaves ssh/helpers alive with inherited stdout/stderr."""
    git = tmp_path / "git"
    parent_pid, child_pid, heartbeat = (tmp_path / name for name in ("parent", "child", "heartbeat"))
    git.write_text(f'''#!{sys.executable}
import os, signal, subprocess, sys, time
from pathlib import Path
root = Path(__file__).parent
if len(sys.argv) == 1 or sys.argv[1] != "helper":
    time.sleep({startup_delay})
if len(sys.argv) > 1 and sys.argv[1] == "helper":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    (root / "child").write_text(str(os.getpid()))
    while True:
        (root / "heartbeat").write_text(str(time.monotonic_ns()))
        time.sleep(0.02)
(root / "parent").write_text(str(os.getpid()))
subprocess.Popen([sys.executable, __file__, "helper"])
while True: time.sleep(1)
''')
    git.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    result = []
    helper_ready = threading.Event()
    communicate = D.subprocess.Popen.communicate

    def communicate_after_ready(process, *args, **kwargs):
        # Exercise the real timeout/kill/drain path only after the fixture is ready.
        # Interpreter startup has its own bounded allowance below.
        assert helper_ready.wait(10), "stub startup exceeded readiness deadline"
        return communicate(process, *args, **kwargs)

    monkeypatch.setattr(D.subprocess.Popen, "communicate", communicate_after_ready)

    def run():
        try:
            D._run("git log" if shell else ["git", "log"], timeout=1.0, shell=shell)
        except Exception as exc:
            result.append(exc)

    thread = threading.Thread(target=run)
    try:
        thread.start()
        deadline = time.monotonic() + 10
        while not heartbeat.exists() and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert heartbeat.exists(), "stub helper never became ready"
        helper_ready.set()
        thread.join(2.5)
        assert not thread.is_alive(), "timeout waited on pipes still held by a child"
        assert len(result) == 1 and isinstance(result[0], D.subprocess.TimeoutExpired)
        assert child_pid.exists(), "stub helper never started"
        first = heartbeat.read_text()
        time.sleep(0.12)
        assert heartbeat.read_text() == first, "timed-out git left its helper alive"
    finally:
        helper_ready.set()
        for path in (parent_pid, child_pid):
            if path.exists():
                pid = int(path.read_text())
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        thread.join(2)


def test_subprocess_success_and_failure_keep_output_contract():
    assert D._run([sys.executable, "-c", "print('ok')"]) == (0, "ok\n")
    assert D._run([sys.executable, "-c", "import sys; print('bad', file=sys.stderr); sys.exit(7)"]) == (7, "bad\n")


def test_abandoned_tick_keeps_event_cursor_and_persisted_snapshot(engine):
    from pravaha_tracker.events import append

    before_disk = Path(engine.cfg["snapshot"]).read_bytes()
    append(engine.cfg["events"], {"kind": "note", "actor": "steward", "detail": "must replay"})
    entered, release = threading.Event(), threading.Event()
    original = S.Engine._sample_health

    def slow_sample(self):
        entered.set()
        release.wait(3)
        return original(self)

    with patch.object(S.Engine, "_sample_health", slow_sample):
        tick = threading.Thread(target=engine.tick)
        tick.start()
        try:
            assert entered.wait(1)
            tick.join(0.5)
            returned = not tick.is_alive()
            unpublished_events = list(engine.log.events)
        finally:
            release.set()
            tick.join(2)
            worker = getattr(engine, "_tick_worker", None)
            if worker:
                worker.join(2)
    assert returned
    assert unpublished_events == [], "a timed-out collector consumed the live event cursor"
    assert Path(engine.cfg["snapshot"]).read_bytes() == before_disk
    engine.tick()
    assert [event["detail"] for event in engine.log.events] == ["must replay"]


def test_hung_git_activity_does_not_delay_health(engine, http, tmp_path, monkeypatch):
    git = tmp_path / "git"
    started = tmp_path / "git-started"
    git.write_text(f"#!{sys.executable}\nimport time\nopen({str(started)!r}, 'w').close()\ntime.sleep(10)\n")
    git.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    engine.model = {**engine.model, "streams": [{"id": "A", "worktrees": [str(tmp_path)]}]}
    original = D._run

    def short_timeout(cmd, **kwargs):
        return original(cmd, **{**kwargs, "timeout": 1})

    with patch.object(D, "_run", short_timeout):
        activity = threading.Thread(target=engine._refresh_activity)
        activity.start()
        try:
            deadline = time.monotonic() + 0.8
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert started.exists()
            assert activity.is_alive(), "git finished before the concurrent requests"
            concurrent_reads(http)
        finally:
            activity.join(3)
        assert not activity.is_alive()
    assert any("git activity" in error for error in engine.health()["tick_errors"])


def test_detector_change_during_collection_is_not_lost(engine):
    spec = {"type": "file_exists", "path": "unused"}
    engine.model = {**engine.model, "tracks": [{"id": "t", "title": "T"}],
                    "items": [{"id": "x", "track": "t", "title": "X", "owner": "steward",
                               "depends_on": [], "detector": spec}]}
    engine._dirty = True
    # The claim is about notification ordering, never about speed: a loaded runner must not turn this
    # into a timeout test (an abandoned first tick leaves its collector alive and the follow-up tick returns early).
    engine.cfg["tick_budget_s"] = 60
    entered, release = threading.Event(), threading.Event()
    original = S.Engine._sample_health

    def slow_sample(self):
        # Patched on the class: only this engine's collector (a staged copy sharing its detectors) gates the test.
        if self.det is engine.det:
            entered.set()
            release.wait(30)
        return original(self)

    with patch.object(S.Engine, "_sample_health", slow_sample):
        tick = threading.Thread(target=engine.tick)
        tick.start()
        try:
            assert entered.wait(30)
            with engine.det._lock:
                engine.det.results[engine.det.key(spec)] = D.DetectorResult("done", "found", "now", "test")
            engine._mark_dirty()
        finally:
            release.set()
            tick.join(30)
    assert not tick.is_alive(), "the first tick never finished"
    assert not engine._tick_abandoned, "the first tick was abandoned, so nothing was published to lose"
    assert engine.snapshot["tracks"][0]["items"][0]["status"] == "unknown", \
        "the published snapshot predates the detector change"
    assert engine._dirty, "publishing a tick lost a detector's concurrent change notification"
    engine.tick()
    assert engine.snapshot["tracks"][0]["items"][0]["status"] == "done"


def test_http_verify_bypasses_saturated_dashboard_fetches(engine, http, monkeypatch):
    entered = [threading.Event() for _ in range(4)]
    release = threading.Event()
    engine.model = {**engine.model, "items": [
        {"id": "completion", "detector": {"type": "branch_merged", "ref": "origin/completion"}}]}

    def run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"] and cmd[-1].startswith("dashboard-"):
            entered[int(cmd[-1][-1])].set()
            assert release.wait(10)
        return 0, "marker"

    monkeypatch.setattr(D, "_run", run)
    engine.det.poll([{"type": "branch_file_contains", "ref": f"origin/dashboard-{i}",
                      "path": "receipt", "pattern": "marker"} for i in range(4)])
    try:
        assert all(e.wait(2) for e in entered)
        assert get(http + "/api/verify?id=completion")["detector"]["status"] == "done"
        assert not release.is_set()
    finally:
        release.set()
        engine.det._pool.shutdown(wait=True)
