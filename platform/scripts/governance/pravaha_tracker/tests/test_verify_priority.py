"""Live completion must stay independent of slow dashboard fetches."""
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import sys
import threading
import time
import urllib.error
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import cli
from pravaha_tracker import detectors as D


@pytest.fixture
def det(tmp_path):
    detector = D.Detectors(D.Config(str(tmp_path), None, str(tmp_path)))
    yield detector
    detector._pool.shutdown(wait=True)


def test_verify_finishes_while_four_other_refs_are_fetching(det, monkeypatch):
    release = threading.Event()
    entered = [threading.Event() for _ in range(4)]

    def run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"] and cmd[-1].startswith("dashboard-"):
            entered[int(cmd[-1][-1])].set()
            assert release.wait(10), "test did not release dashboard fetch"
        return 0, "marker"

    monkeypatch.setattr(D, "_run", run)
    det.poll([{"type": "branch_file_contains", "ref": f"origin/dashboard-{i}",
               "path": "receipt", "pattern": "marker"} for i in range(4)])
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            assert all(e.wait(2) for e in entered), "unrelated refs serialized"
            verification = pool.submit(det.verify, {"type": "branch_merged", "ref": "origin/completion"})
            assert verification.result(timeout=2).status == "done"
            assert not release.is_set(), "verify waited for dashboard release"
        finally:
            release.set()
            det._pool.shutdown(wait=True)


def test_same_ref_inflight_is_shared_but_later_verify_is_fresh(det, monkeypatch):
    entered, release, joined = threading.Event(), threading.Event(), threading.Event()
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        entered.set()
        assert release.wait(10)
        return 0, ""

    class ObservedFuture(Future):
        def result(self, timeout=None):
            joined.set()
            return super().result(timeout)

    monkeypatch.setattr(D, "_run", run)
    monkeypatch.setattr(D, "Future", ObservedFuture, raising=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(det._fetch, "main")
        try:
            assert entered.wait(2)
            second = pool.submit(det.verify, {"type": "branch_merged", "ref": "local"})
            assert joined.wait(2)
        finally:
            release.set()
        first.result(timeout=2)
        assert second.result(timeout=2).status == "done"
    fetches = [c for c in calls if c[:2] == ["git", "fetch"]]
    assert len(fetches) == 1
    assert det.verify({"type": "branch_merged", "ref": "local"}).status == "done"
    assert len([c for c in calls if c[:2] == ["git", "fetch"]]) == 2


def test_poll_defers_during_verify_and_resumes_after_failure(det, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    spec = {"type": "file_exists", "path": "unused"}

    def slow(spec):
        entered.set()
        assert release.wait(10)
        raise RuntimeError("measurement failed")

    monkeypatch.setattr(det, "d_file_exists", slow)
    with ThreadPoolExecutor(max_workers=1) as pool:
        checking = pool.submit(det.verify, spec)
        try:
            assert entered.wait(2)
            det.poll([spec])
            with det._lock:
                assert not det._inflight, "dashboard submitted work during verify"
        finally:
            release.set()
        assert checking.result(timeout=2).status == "error"
    monkeypatch.setattr(det, "d_file_exists", lambda s: D.DetectorResult("pending", "missing", "now", "test"))
    det.poll([spec])
    det._pool.shutdown(wait=True)
    assert det.get(spec).status == "pending"


@pytest.mark.parametrize("failure", ["exit", "timeout"])
def test_failed_live_fetch_never_uses_cached_done_or_stale_refs(det, monkeypatch, failure):
    spec = {"type": "branch_merged", "ref": "local"}
    det.results[det.key(spec)] = D.DetectorResult("done", "old", "then", "test")
    det._fetched["main"] = time.time()
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        if failure == "timeout":
            raise D.subprocess.TimeoutExpired(cmd, 90)
        return (1, "fetch failed") if cmd[:2] == ["git", "fetch"] else (0, "")

    monkeypatch.setattr(D, "_run", run)
    assert det.verify(spec).status == "error"
    assert len(calls) == 1 and calls[0][:2] == ["git", "fetch"]
    assert det.get(spec).status == "done", "verify should not mutate the dashboard cache"


@pytest.mark.parametrize("configured,expected", [(None, 300), ("451.5", 451.5)])
def test_guarded_done_verify_timeout(det, monkeypatch, configured, expected):
    if configured is None:
        monkeypatch.delenv("KY_VERIFY_TIMEOUT_S", raising=False)
    else:
        monkeypatch.setenv("KY_VERIFY_TIMEOUT_S", configured)
    with patch.object(cli, "load_model", return_value={"control_plane": {"guarded_completion": True},
                                                     "items": [{"id": "X"}]}), \
         patch.object(cli, "get", return_value=(None, "unavailable")) as get:
        assert cli.main(["done", "X", "--stream", "K", "--pr", "1"]) == 2
    assert get.call_args.kwargs["timeout"] == expected


@pytest.mark.parametrize("error,message", [
    (TimeoutError("slow"), "tracker timed out"),
    (urllib.error.URLError(TimeoutError("slow")), "tracker timed out"),
    (urllib.error.URLError(ConnectionRefusedError("down")), "tracker unreachable"),
])
def test_guarded_done_transport_refusal_never_falls_back_to_snapshot(tmp_path, monkeypatch, capsys, error, message):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text('{"item":"X","detector":{"status":"done"}}')
    monkeypatch.setattr(cli, "SNAPSHOT", str(snapshot))
    with patch.object(cli, "load_model", return_value={"control_plane": {"guarded_completion": True},
                                                     "items": [{"id": "X"}]}), \
         patch.object(cli.urllib.request, "urlopen", side_effect=error), \
         patch.object(cli, "_locked") as lock:
        assert cli.main(["done", "X", "--stream", "K", "--pr", "1"]) == 2
    assert message in capsys.readouterr().err
    lock.assert_not_called()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "invalid"])
def test_invalid_verify_timeout_refuses_before_network(monkeypatch, value):
    monkeypatch.setenv("KY_VERIFY_TIMEOUT_S", value)
    with patch.object(cli, "load_model", return_value={"control_plane": {"guarded_completion": True},
                                                     "items": [{"id": "X"}]}), \
         patch.object(cli, "get") as get:
        assert cli.main(["done", "X", "--stream", "K", "--pr", "1"]) == 2
    get.assert_not_called()


def test_same_ref_waiter_gets_failure_and_next_call_retries(det, monkeypatch):
    entered, joined, release = threading.Event(), threading.Event(), threading.Event()
    calls = []

    class ObservedFuture(Future):
        def result(self, timeout=None):
            joined.set()
            return super().result(timeout)

    def run(cmd, **kwargs):
        calls.append(cmd)
        entered.set()
        assert release.wait(10)
        return 1, "fetch failed"

    monkeypatch.setattr(D, "Future", ObservedFuture, raising=False)
    monkeypatch.setattr(D, "_run", run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(det._fetch, "main")
        try:
            assert entered.wait(2)
            second = pool.submit(det._fetch, "main")
            assert joined.wait(2)
        finally:
            release.set()
        for result in (first, second):
            with pytest.raises(RuntimeError, match="fetch failed"):
                result.result(timeout=2)
    assert len(calls) == 1
    assert "main" not in det._fetched
    with pytest.raises(RuntimeError, match="fetch failed"):
        det._fetch("main")
    assert len(calls) == 2


def test_dashboard_keeps_fetch_ttl(det, monkeypatch):
    with patch.object(D, "_run", return_value=(0, "")) as run:
        det._fetch("main")
        det._fetch("main")
    assert run.call_count == 1
