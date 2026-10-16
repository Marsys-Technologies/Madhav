"""Live completion must stay independent of slow dashboard fetches."""
from concurrent.futures import Future, ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import json
import socket
from pathlib import Path
import sys
from types import SimpleNamespace
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


@pytest.mark.parametrize("old_failure", [None, "exit", "timeout"])
def test_same_ref_older_flight_is_followed_by_fresh_verify(det, monkeypatch, old_failure):
    entered, release, joined = threading.Event(), threading.Event(), threading.Event()
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        entered.set()
        assert release.wait(10)
        if len(calls) == 1:
            if old_failure == "timeout":
                raise D.subprocess.TimeoutExpired(cmd, 90)
            if old_failure == "exit":
                return 1, "old measurement failed"
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
        if old_failure:
            with pytest.raises((RuntimeError, D.subprocess.TimeoutExpired)):
                first.result(timeout=2)
        else:
            first.result(timeout=2)
        assert second.result(timeout=2).status == "done"
    fetches = [c for c in calls if c[:2] == ["git", "fetch"]]
    assert len(fetches) == 2
    assert det.verify({"type": "branch_merged", "ref": "local"}).status == "done"
    assert len([c for c in calls if c[:2] == ["git", "fetch"]]) == 3


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
         patch.object(cli, "time", SimpleNamespace(sleep=lambda _: None), create=True), \
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


@pytest.mark.parametrize("failure", ["exit", "timeout"])
def test_guarded_done_refuses_old_success_when_post_request_fetch_fails(tmp_path, monkeypatch, failure):
    """An older green branch measurement cannot authorize an event append (TV-B01)."""
    import json
    from test_kalayantra_control_plane import GuardedCompletionCases
    from pravaha_tracker.events import append

    fixture = GuardedCompletionCases()
    fixture.setUp()
    path = tmp_path / "EVENTS.jsonl"
    for event in (fixture.step, fixture.review, fixture.verdict, fixture.post):
        append(str(path), event, fixture.model)
    before = path.read_bytes()
    detector = D.Detectors(D.Config(str(tmp_path), None, str(tmp_path)))
    target = fixture.model["items"][0]["detector"]
    detector.results[detector.key(target)] = D.DetectorResult("done", "cached", "old", "test")
    entered, release = threading.Event(), threading.Event()
    branch_fetches = []

    class ObservedFuture(Future):
        def result(self, timeout=None):
            release.set()
            return super().result(timeout)

    def run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"] and cmd[-1] == "k-1":
            branch_fetches.append(list(cmd))
            if len(branch_fetches) == 1:
                entered.set()
                assert release.wait(5), "verify never waited for older flight"
                return 0, ""
            if failure == "timeout":
                raise D.subprocess.TimeoutExpired(cmd, 90)
            return 1, "remote measurement unavailable"
        return 0, fixture.head

    def live_get(path, timeout):
        return {"item": "K-1", "detector": detector.verify(target).to_dict()}, "live"

    monkeypatch.setattr(D, "Future", ObservedFuture)
    monkeypatch.setattr(D, "_run", run)
    monkeypatch.setattr(cli, "EVENTS", str(path))
    monkeypatch.setattr(cli, "load_model", lambda: fixture.model)
    monkeypatch.setattr(cli, "get", live_get)
    monkeypatch.setattr(cli, "observe_containment", lambda *a: {})
    gh = D.subprocess.CompletedProcess([], 0, stdout=json.dumps(fixture.pr), stderr="")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(detector._fetch, "k-1")
            try:
                assert entered.wait(2)
                with patch.object(cli.subprocess, "run", return_value=gh):
                    rc = cli.main(["done", "K-1", "--stream", "K", "--pr", "3210",
                                   "--reviewed-head", fixture.head])
            finally:
                release.set()
            first.result(timeout=2)
        assert rc == 2, "guarded done accepted a pre-request fetch"
        assert path.read_bytes() == before, "refused completion appended an event"
        assert len(branch_fetches) == 2, "verify must attempt a post-request fetch"
    finally:
        detector._pool.shutdown(wait=True)


@pytest.mark.parametrize("failure", [None, "exit", "timeout"])
def test_verify_shares_flight_started_after_its_request(det, monkeypatch, failure):
    requested, proceed, entered, joined, release = (threading.Event() for _ in range(5))
    original = det.d_branch_merged
    calls = []

    def delayed(spec):
        requested.set()
        assert proceed.wait(5)
        return original(spec)

    class ObservedFuture(Future):
        def result(self, timeout=None):
            joined.set()
            return super().result(timeout)

    def run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            calls.append(cmd)
            entered.set()
            assert release.wait(5)
            if failure == "timeout":
                raise D.subprocess.TimeoutExpired(cmd, 90)
            if failure == "exit":
                return 1, "fetch failed"
        return 0, ""

    monkeypatch.setattr(det, "d_branch_merged", delayed)
    monkeypatch.setattr(D, "Future", ObservedFuture)
    monkeypatch.setattr(D, "_run", run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        verifying = pool.submit(det.verify, {"type": "branch_merged", "ref": "local"})
        try:
            assert requested.wait(2)
            fetching = pool.submit(det._fetch, "main")
            assert entered.wait(2)
            proceed.set()
            assert joined.wait(2)
        finally:
            proceed.set()
            release.set()
        if failure:
            with pytest.raises((RuntimeError, D.subprocess.TimeoutExpired)):
                fetching.result(timeout=2)
        else:
            fetching.result(timeout=2)
        assert verifying.result(timeout=2).status == ("error" if failure else "done")
    assert len(calls) == 1, "qualifying flight should be shared, including its error"


@pytest.fixture
def verify_server(tmp_path, monkeypatch):
    """Closed loopback port: genuine connection refusal before server recovery."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.server.requests.append(self.path)
            status, body = self.server.replies.pop(0)
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler, bind_and_activate=False)
    server.server_bind()
    server.server_address = server.socket.getsockname()
    server.server_close()
    server.requests = []
    server.replies = [(200, b'{"item":"K-RETRY","detector":{"status":"done"}}')]
    thread = None

    def start():
        nonlocal thread
        server.socket = socket.socket(server.address_family, server.socket_type)
        server.server_bind()
        server.server_activate()
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()

    attempts, delays = [], []
    urlopen = cli.urllib.request.urlopen

    def request(url, *, timeout):
        attempts.append((url, timeout))
        return urlopen(url, timeout=timeout)

    def sleep(seconds):
        delays.append(seconds)
        server.on_sleep()

    server.on_sleep = lambda: None
    monkeypatch.setattr(cli, "URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setattr(cli.urllib.request, "urlopen", request)
    # Replace only the CLI's clock, leaving the fake server's real clock alone.
    monkeypatch.setattr(cli, "time", SimpleNamespace(sleep=sleep), raising=False)
    monkeypatch.setenv("KY_VERIFY_TIMEOUT_S", "0.2")
    artifact = tmp_path / "proof.txt"
    artifact.write_text("independently accepted artifact")
    model = {"campaign": "retry", "control_plane": {"guarded_completion": True, "verdict_stream": "V"},
             "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
             "items": [{"id": "K-RETRY", "track": "K", "title": "retry", "owner": "K",
                        "detector": {"type": "file_exists", "path": str(artifact)}}]}
    events = tmp_path / "EVENTS.jsonl"
    events.write_text(json.dumps({"kind": "verdict", "actor": "stream-V:reviewer", "item": "K-RETRY",
                                  "phase": "artifact", "result": "ACCEPTED",
                                  "artifact_digest": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                                  "detail": "accepted", "ts": "2026-10-16T00:00:00Z"}) + "\n")
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    # A tempting stale success must never become authority after a transport error.
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text('{"item":"K-RETRY","detector":{"status":"done"}}')
    monkeypatch.setattr(cli, "SNAPSHOT", str(snapshot))
    fixture = SimpleNamespace(server=server, start=start, attempts=attempts, delays=delays,
                              events=events, before=events.read_bytes(),
                              run=lambda: cli.main(["done", "K-RETRY", "--stream", "K",
                                                    "--artifact-path", str(artifact)]))
    try:
        yield fixture
    finally:
        if thread is not None:
            server.shutdown()
            thread.join(2)
            assert not thread.is_alive()
        server.server_close()


@pytest.mark.parametrize("failures", [1, 2, 3])
def test_guarded_done_retries_refused_connection_then_records_done(verify_server, failures):
    fixture = verify_server
    fixture.server.on_sleep = lambda: fixture.start() if len(fixture.delays) == failures else None
    assert fixture.run() == 0
    assert len(fixture.attempts) == failures + 1
    assert fixture.delays == [2, 4, 8][:failures]
    assert fixture.server.requests == ["/api/verify?id=K-RETRY"]
    event = json.loads(fixture.events.read_text().splitlines()[-1])
    assert event["state"] == "done" and event["guarded"] is True


def test_guarded_done_persistent_unreachable_is_bounded(verify_server, capsys):
    fixture = verify_server
    assert fixture.run() == 2
    assert capsys.readouterr().err == "refused: tracker unreachable during live detector verification\n"
    assert len(fixture.attempts) == 4
    assert fixture.delays == [2, 4, 8]
    assert sum(fixture.delays) == 14
    assert [timeout for _, timeout in fixture.attempts] == [0.2] * 4
    assert fixture.events.read_bytes() == fixture.before


@pytest.mark.parametrize("status", ["pending", "error", "NOT_MET", False])
@pytest.mark.parametrize("transport_first", [False, True])
def test_guarded_done_never_retries_a_received_false(verify_server, capsys, status, transport_first):
    fixture = verify_server
    fixture.server.replies.insert(0, (200, json.dumps({"item": "K-RETRY", "detector": {"status": status}}).encode()))
    if transport_first:
        fixture.server.on_sleep = fixture.start
    else:
        fixture.start()
    assert fixture.run() == 2
    assert "declared detector has not passed" in capsys.readouterr().err
    assert len(fixture.attempts) == (2 if transport_first else 1)
    assert fixture.delays == ([2] if transport_first else [])
    assert fixture.server.requests == ["/api/verify?id=K-RETRY"]
    assert fixture.events.read_bytes() == fixture.before


@pytest.mark.parametrize("reply", [(503, b"unavailable"), (200, b"invalid JSON"), (200, b"{}")])
def test_guarded_done_never_retries_http_or_invalid_responses(verify_server, reply):
    fixture = verify_server
    fixture.server.replies.insert(0, reply)
    fixture.start()
    assert fixture.run() == 2
    assert len(fixture.attempts) == 1
    assert fixture.delays == []
    assert fixture.events.read_bytes() == fixture.before


@pytest.mark.parametrize("error", [ConnectionResetError("reset"), urllib.error.URLError(ConnectionRefusedError("down"))])
def test_guarded_done_retries_connection_error_before_live_answer(verify_server, monkeypatch, error):
    fixture = verify_server
    fixture.start()
    urlopen = cli.urllib.request.urlopen
    calls = []

    def interrupted(url, *, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise error
        return urlopen(url, timeout=timeout)

    monkeypatch.setattr(cli.urllib.request, "urlopen", interrupted)
    assert fixture.run() == 0
    assert len(calls) == 2
    assert fixture.delays == [2]


@pytest.mark.parametrize("transport_first", [False, True])
def test_guarded_done_timeout_is_not_retried(verify_server, monkeypatch, capsys, transport_first):
    fixture = verify_server
    calls = []

    def timed_out(url, *, timeout):
        calls.append(timeout)
        if transport_first and len(calls) == 1:
            raise urllib.error.URLError(ConnectionRefusedError("down"))
        raise urllib.error.URLError(TimeoutError("slow"))

    monkeypatch.setattr(cli.urllib.request, "urlopen", timed_out)
    assert fixture.run() == 2
    assert capsys.readouterr().err == "refused: tracker timed out after 0.2s during live detector verification\n"
    assert calls == ([0.2, 0.2] if transport_first else [0.2])
    assert fixture.delays == ([2] if transport_first else [])
    assert fixture.events.read_bytes() == fixture.before
