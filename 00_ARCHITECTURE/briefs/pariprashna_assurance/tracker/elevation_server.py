"""Loopback-only server for the shadow elevation dashboard."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from elevation import ElevationStore

DASHBOARD = Path(__file__).with_name("elevation_dashboard.html")


def handler_factory(store: ElevationStore, dashboard: Path):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload: dict) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(encoded))); self.end_headers(); self.wfile.write(encoded)

        def do_GET(self) -> None:  # noqa: N802
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self.send_error(403, "loopback only"); return
            host = self.headers.get("Host", "")
            approved_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}", f"[::1]:{self.server.server_port}"}
            if host not in approved_hosts:
                self.send_error(403, "approved Host required"); return
            if self.path == "/api/elevation":
                self._json(store.dashboard()); return
            if self.path == "/":
                encoded = dashboard.read_bytes()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(encoded))); self.end_headers(); self.wfile.write(encoded); return
            self.send_error(404, "not found")

        def log_message(self, _format: str, *_args) -> None:
            return
    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shadow-db", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "::1"}:
        raise SystemExit("shadow elevation dashboard is loopback-only")
    server = ThreadingHTTPServer((args.host, args.port), handler_factory(ElevationStore(args.shadow_db), DASHBOARD))
    server.serve_forever()


if __name__ == "__main__":
    main()
