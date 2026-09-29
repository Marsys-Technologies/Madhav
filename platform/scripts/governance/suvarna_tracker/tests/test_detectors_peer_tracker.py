"""peer_tracker_item: reads another campaign's tracker (the same tracker software; e.g. Pravāha)
and is done only when the named item's status there matches. A local fake HTTP server (thread,
127.0.0.1, ephemeral port) stands in for the peer tracker — no real network, no real peer process."""
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from suvarna_tracker import detectors as D


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _FakeState:
    """Mutable holder so the handler (constructed fresh per request by HTTPServer) can see the
    current canned response without any class-level global."""
    body: bytes = b"{}"
    status: int = 200


def _make_handler(state: _FakeState):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(state.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(state.body)

        def log_message(self, fmt, *args):  # noqa: D401 — silence test output
            pass

    return Handler


@pytest.fixture
def fake_peer(tmp_path):
    state = _FakeState()
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _make_handler(state))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield state, f"http://127.0.0.1:{port}/api/state"
    finally:
        server.shutdown()
        t.join(timeout=5)


def dets(tmp_path):
    return D.Detectors(D.Config(repo=str(tmp_path), nikasha_root=str(tmp_path), pgenv=None, home=str(tmp_path)))


def wait_result(det, spec, timeout=10):
    import time
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = det.get(spec)
        if r is not None:
            return r
        time.sleep(0.05)
    raise AssertionError("detector never produced a result")


def state_with_item(item_id, status, evidence=None):
    item = {"id": item_id, "status": status}
    if evidence is not None:
        item["evidence"] = evidence
    return {"tracks": [{"id": "T", "items": [item]}]}


def test_peer_tracker_item_empty_params_is_pending(tmp_path):
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": "", "item": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_peer_tracker_item_done_when_status_matches(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("W1.landed", "done")).encode()
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_peer_tracker_item_wrong_status_is_pending(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("W1.landed", "running")).encode()
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "'running'" in r.detail and "'done'" in r.detail


def test_peer_tracker_item_custom_expect(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("W1.landed", "ready")).encode()
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed", "expect": "ready"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done"


def test_peer_tracker_item_missing_item_is_pending(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("other-item", "done")).encode()
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "not found" in r.detail


def test_peer_tracker_item_unreachable_is_pending_never_error(tmp_path):
    d = dets(tmp_path)
    # nothing listening on this port
    spec = {"type": "peer_tracker_item", "url": "http://127.0.0.1:1/api/state", "item": "W1.landed"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "unreachable" in r.detail


def test_peer_tracker_item_evidence_required_blocks_without_evidence(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("W1.landed", "done")).encode()  # no evidence field
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed", "evidence_required": True}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "no evidence" in r.detail


def test_peer_tracker_item_evidence_required_done_with_evidence(tmp_path, fake_peer):
    state, url = fake_peer
    state.body = json.dumps(state_with_item("W1.landed", "done", evidence="PR #123 merged")).encode()
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed", "evidence_required": True}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done"


@pytest.mark.parametrize("url", [
    "http://example.com/api/state",
    "http://10.0.0.5:8766/api/state",
    "http://localhost:8766/api/state",  # not the literal 127.0.0.1 host string — refused too
])
def test_peer_tracker_item_non_loopback_url_refused(tmp_path, url):
    d = dets(tmp_path)
    spec = {"type": "peer_tracker_item", "url": url, "item": "W1.landed"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and "127.0.0.1" in r.detail


def test_peer_tracker_item_is_registered_and_has_a_ttl(tmp_path):
    assert hasattr(D.Detectors, "d_peer_tracker_item")
    assert D.Detectors.TTL.get("peer_tracker_item") == 60
