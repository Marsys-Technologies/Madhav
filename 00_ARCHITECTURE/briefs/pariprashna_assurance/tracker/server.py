#!/usr/bin/env python3
"""Local CG-0 HTTP/SSE service. Write APIs require a bearer token; default bind is loopback."""
from __future__ import annotations

import argparse
import json
import mimetypes
import queue
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from control import EventStore, RejectedEvent


class EventBus:
    def __init__(self) -> None:
        self._queues: list[queue.Queue[str]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue()
        with self._lock: self._queues.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[str]) -> None:
        with self._lock:
            if q in self._queues: self._queues.remove(q)

    def publish(self, message: dict) -> None:
        payload = json.dumps(message, separators=(",", ":"))
        with self._lock:
            for q in list(self._queues): q.put(payload)


def adapter_health() -> dict:
    """Safe current-scope adapter: no credentials, no mutation, and no cache-as-freshness."""
    return {"github": {"health": "UNKNOWN", "reason": "not configured for local CG-0 runtime"}, "ci": {"health": "UNKNOWN", "reason": "not configured for local CG-0 runtime"}, "canonical_state_unchanged": True}


def handler_factory(store: EventStore, bus: EventBus, dashboard: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PariprashnaAssuranceTracker/1"

        def log_message(self, *_args):
            return

        def _json(self, status: int, value: dict) -> None:
            body = json.dumps(value, separators=(",", ":")).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

        def _body(self) -> dict:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 1024 * 1024: raise RejectedEvent("REQUEST_TOO_LARGE", "request exceeds 1 MiB")
            return json.loads(self.rfile.read(size) or b"{}")

        def _actor(self) -> str | None:
            header = self.headers.get("Authorization", "")
            return store.authenticate(header.removeprefix("Bearer ")) if header.startswith("Bearer ") else None

        def _local_only(self) -> bool:
            return self.client_address[0] in {"127.0.0.1", "::1"}

        def do_GET(self) -> None:
            if not self._local_only(): self._json(403, {"error": "CG-0 runtime is loopback-only"}); return
            path = urlparse(self.path).path
            if path == "/":
                data = dashboard.read_bytes(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            if path == "/api/projection": self._json(200, store.projection()); return
            if path == "/api/integrity": self._json(200, store.verify_replay()); return
            if path == "/api/rejected": self._json(200, {"rejected_events": store.rejected()}); return
            if path == "/api/adapters": self._json(200, adapter_health()); return
            if path == "/events":
                self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.send_header("Connection", "keep-alive"); self.end_headers()
                q = bus.subscribe()
                try:
                    self.wfile.write(("event: projection\ndata: " + json.dumps(store.projection(), separators=(",", ":")) + "\n\n").encode()); self.wfile.flush()
                    while True:
                        try: data = q.get(timeout=15); event = "projection"
                        except queue.Empty: data = json.dumps({"at": time.time()}); event = "ping"
                        self.wfile.write((f"event: {event}\ndata: {data}\n\n").encode()); self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError): pass
                finally: bus.unsubscribe(q)
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if not self._local_only(): self._json(403, {"error": "CG-0 runtime is loopback-only"}); return
            path = urlparse(self.path).path; actor = self._actor()
            if not actor: self._json(401, {"error": "bearer token required"}); return
            try:
                body = self._body(); body["actor_id"] = actor
                if path == "/api/events":
                    result = store.submit(body); bus.publish(store.projection()); self._json(201, result); return
                if path == "/api/presence":
                    store.record_presence(actor, body["session_id"], body.get("stream_id"), body["state"], body.get("detail", ""), body.get("observed_at")); bus.publish(store.projection()); self._json(201, {"accepted": True}); return
                if path == "/api/rebuild":
                    store.rebuild(); bus.publish(store.projection()); self._json(200, {"accepted": True, "integrity": store.verify_replay()}); return
                self._json(404, {"error": "not found"})
            except RejectedEvent as exc: self._json(409, {"accepted": False, "code": exc.code, "error": str(exc)})
            except (KeyError, json.JSONDecodeError, ValueError) as exc: self._json(400, {"accepted": False, "code": "REQUEST", "error": str(exc)})
    return Handler


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--runtime", required=True); p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", default=8787, type=int); args = p.parse_args()
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("CG-0 tracker is deliberately loopback-only; non-local deployment requires A3")
    store = EventStore(args.runtime); store.rebuild(); bus = EventBus(); dashboard = Path(__file__).with_name("dashboard.html")
    httpd = ThreadingHTTPServer((args.host, args.port), handler_factory(store, bus, dashboard))
    print(f"http://{args.host}:{args.port}", flush=True); httpd.serve_forever()


if __name__ == "__main__": main()
