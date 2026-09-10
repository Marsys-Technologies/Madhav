#!/usr/bin/env python3
"""LAN server for the tracker (T3 support): stdlib http.server, bound to this Mac's LAN
address on a fixed port, serving ~/.pariprashna-tracker/ ONLY, under a random path token
generated at first run and persisted (so restarts under launchd keep the same URL) and
printed to the log at every start. Unauthenticated plaintext on the local network -- see
README.md. Stdlib only.
"""
import http.server
import os
import secrets
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RUNTIME_DIR, SERVE_TOKEN_FILE, URL_FILE, ensure_runtime_dirs  # noqa: E402
import shutil  # noqa: E402


def _ensure_dashboard_deployed():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.html")
    dst = os.path.join(RUNTIME_DIR, "tracker.html")
    ensure_runtime_dirs()
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        shutil.copyfile(src, dst)

PORT = 8934


def get_or_create_token():
    ensure_runtime_dirs()
    if os.path.exists(SERVE_TOKEN_FILE):
        with open(SERVE_TOKEN_FILE, encoding="utf-8") as f:
            tok = f.read().strip()
            if tok:
                return tok
    tok = secrets.token_urlsafe(24)
    with open(SERVE_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(tok)
    return tok


def stable_hostname():
    """A name that survives the Mac changing networks. The raw LAN IP does NOT: on
    2026-08-20 this machine moved from 192.168.1.9 to 192.168.101.13 and the IP-based URL
    that had been handed to the operator simply stopped connecting (TCP SYN_SENT), which in
    a browser is an indefinitely-blank page -- indistinguishable from the tracker itself
    having died, and reported as exactly that. An observability tool whose address silently
    expires is failing at its one job.

    macOS publishes <LocalHostName>.local over Bonjour/mDNS, which follows the machine
    across networks. Returns None if it cannot be determined."""
    try:
        r = subprocess.run(["scutil", "--get", "LocalHostName"],
                           capture_output=True, text=True, timeout=5)
        name = (r.stdout or "").strip()
        return f"{name}.local" if r.returncode == 0 and name else None
    except Exception:  # noqa: BLE001 -- never let URL cosmetics stop the server booting
        return None


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def make_handler(token):
    root = RUNTIME_DIR

    class TokenGatedHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def do_GET(self):
            prefix = f"/{token}"
            if self.path == "/" or self.path == "":
                self.send_response(404)
                self.end_headers()
                return
            if not (self.path == prefix or self.path.startswith(prefix + "/")):
                self.send_response(404)
                self.end_headers()
                return
            self.path = self.path[len(prefix):] or "/"
            if self.path == "/":
                self.path = "/tracker.html"
            return super().do_GET()

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    return TokenGatedHandler


def main():
    _ensure_dashboard_deployed()
    token = get_or_create_token()
    ip = lan_ip()
    host = stable_hostname()
    ip_url = f"http://{ip}:{PORT}/{token}/"
    stable_url = f"http://{host}:{PORT}/{token}/" if host else None

    # Persist both, so the current address is always answerable from a file instead of from
    # memory of what was printed at some past boot -- and so a blank page can be told apart
    # from a moved one without having to ask anybody.
    ensure_runtime_dirs()
    with open(URL_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Paripraśna tracker — written at every serve.py start\n")
        f.write(f"# PREFER the stable name: it follows this Mac across networks.\n")
        f.write(f"stable_url: {stable_url or '(unavailable — mDNS name not resolvable)'}\n")
        f.write(f"ip_url:     {ip_url}   # breaks whenever this Mac's LAN IP changes\n")
    if stable_url:
        print(f"Paripraśna tracker URL (stable, survives IP changes): {stable_url}", file=sys.stderr)
    print(f"Paripraśna tracker URL (current IP, breaks on network change): {ip_url}", file=sys.stderr)
    print(f"Both recorded in {URL_FILE}", file=sys.stderr)
    print("UNAUTHENTICATED PLAINTEXT on the local network. Do not port-forward or tunnel this.", file=sys.stderr)
    handler = make_handler(token)
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
