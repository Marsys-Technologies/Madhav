"""Cold-start coverage: no warm-up tick or installed tracker is used.

External probes are gated at the I/O boundary; model loading, event replay,
detector scheduling, verification and the HTTP server use their real threads.
"""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D
from pravaha_tracker import server as S


@pytest.fixture
def cold_config(tmp_path, monkeypatch):
    # Keep the complete campaign model (declarations, joins, decision outcomes,
    # steps and detectors), replacing only paths that could read live inputs.
    model_path = Path(S.REPO_ROOT) / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
    model = json.loads(model_path.read_text())
    for stream in model["streams"]:
        stream["worktrees"] = []
    for item in model["items"]:
        specs = [item.get("detector", {})]
        specs += [entry.get("detector", {}) for entry in item.get("step_evidence", {}).values()
                  if isinstance(entry, dict)]
        for spec in specs:
            if "path" in spec:
                spec["path"] = str(tmp_path / "unmeasured")
    model_file = tmp_path / "model.json"
    model_file.write_text(json.dumps(model))
    events = tmp_path / "EVENTS.jsonl"
    items = model["items"]
    with events.open("w") as handle:
        for n in range(14_500):
            handle.write(json.dumps({"kind": "item", "actor": "steward",
                                     "item": items[n % len(items)]["id"], "state": "running",
                                     "ts": "2026-10-16T07:36:00+00:00", "detail": str(n)}) + "\n")
    for key, value in {
        "PRAVAHA_HOME": str(tmp_path), "PRAVAHA_EVENTS": str(events),
        "PRAVAHA_PLAN_MODEL": str(model_file), "PRAVAHA_REPO": str(tmp_path),
        "PRAVAHA_HOLD": str(tmp_path / "HOLD"), "PRAVAHA_PGENV": "",
        "PRAVAHA_DETECTORS": "1", "PRAVAHA_TICK_BUDGET_S": "8",
    }.items():
        monkeypatch.setenv(key, value)
    # No socket probe, real command, credential file or remote DB is accessed.
    monkeypatch.setattr(D, "port_open", lambda *a, **kw: False)

    def run(cmd, **kwargs):
        if cmd[0] == "gh":
            return 0, json.dumps({"state": "MERGED", "mergedAt": "now", "mergeable": "MERGEABLE"})
        return 0, "receipt"

    monkeypatch.setattr(D, "_run", run)
    return S.default_config()


def read(base, path):
    started = time.monotonic()
    try:
        response = urllib.request.urlopen(base + path, timeout=0.8)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, json.load(response), time.monotonic() - started


@pytest.mark.parametrize("restored", [False, True])
def test_cold_start_serves_snapshot_during_first_slow_tick(cold_config, monkeypatch, restored):
    """Catches an uninitialized publication hidden by warmed-up test fixtures."""
    entered, release = threading.Event(), threading.Event()

    def power():
        entered.set()
        release.wait(60)
        return "ac"

    monkeypatch.setattr(D, "power_source", power)
    if restored:
        snapshot = Path(cold_config["snapshot"])
        snapshot.parent.mkdir(parents=True)
        snapshot.write_text(json.dumps({"version": 7, "campaign": "restored", "tracks": [],
                                        "overall": {"total": 0}, "health": {"power": "battery 60%"}}))
    started = time.monotonic()
    httpd, engine = S.serve(0, cold_config)
    serving = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01})
    serving.start()
    verification_entered, verification_release = threading.Event(), threading.Event()

    def measure(spec):
        verification_entered.set()
        verification_release.wait(60)
        return D.DetectorResult("pending", "fixture", "now", "test")

    monkeypatch.setattr(engine.det, "d_file_exists", measure)
    try:
        assert entered.wait(max(0, 2 - (time.monotonic() - started))), "first collector did not start within 2 s"
        assert engine._tick_worker.is_alive()
        base = f"http://127.0.0.1:{httpd.server_port}"
        # The plan is deliberately not published halfway through a tick, so
        # enter the real verification service directly during this first tick.
        with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
            verification = pool.submit(engine.det.verify, {"type": "file_exists", "path": "fixture"})
            try:
                assert verification_entered.wait(0.5)
                burst = time.monotonic()
                replies = list(pool.map(lambda _: read(base, "/api/health"), range(8)))
                assert time.monotonic() - burst < 1
                assert time.monotonic() - started < 2
                assert all(latency < 1 for _, _, latency in replies)
                assert all(status == (200 if restored else 503) for status, _, _ in replies)
                assert all(health["ok"] is restored for _, health, _ in replies)
                assert not release.is_set(), "slow first tick ended before the requests"
                assert engine._tick_worker.is_alive()
                _, state, _ = read(base, "/api/state")
                assert state["tracks"] == []
                assert state["overall"]["total"] == 0
                assert state["version"] == (7 if restored else 0)
                if restored:
                    assert state["campaign"] == "restored"
                    assert state["health"]["power"] == "battery 60%"
                else:
                    assert state["health"]["initializing"] is True
                    assert state["health"]["power"] == "unknown"
                print(f"cold_start restored={restored}: health_max_s={max(r[2] for r in replies):.3f}, "
                      f"startup_s={time.monotonic() - started:.3f}")
            finally:
                verification_release.set()
            assert verification.result(timeout=1).status == "pending"
        release.set()
        deadline = time.monotonic() + 2
        while engine.version <= (7 if restored else 0) and time.monotonic() < deadline:
            time.sleep(0.01)
        status, state, _ = read(base, "/api/state")
        assert status == 200
        assert state["version"] > (7 if restored else 0)
        assert state["overall"]["total"] == 186  # acceptance closure (A9 D-51.3), as pinned in test_closure_headline.py
        assert state["health"]["event_log"]["events"] == 14_500
        assert state["health"]["initializing"] is False
        assert read(base, "/api/health")[1]["ok"] is True
    finally:
        engine.stop()
        release.set()
        verification_release.set()
        httpd.shutdown()
        httpd.server_close()
        serving.join(2)
        if engine._tick_worker:
            engine._tick_worker.join(2)
        engine.det._pool.shutdown(wait=True)
