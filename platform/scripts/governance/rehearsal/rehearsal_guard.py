#!/usr/bin/env python3
"""rehearsal_guard.py — E5.6 URL guard for the off-production rehearsal cluster.

The rehearsal cluster is the ONLY database the rehearsal tooling may touch. This guard is the
single decision point `apply_schema.sh` (and any later E5.6/E5.7 tooling) must call before it
hands a connection URL to `migrate.ts`, `psql`, or the orchestrator.

A URL is accepted only if ALL hold:
  * scheme is postgres:// or postgresql://
  * exactly ONE host, and it is `localhost` or `127.0.0.1` (no list, no unix-socket path, no IPv6)
  * the port is present and equals REHEARSAL_PORT (55432)
  * the database name is `rehearsal` (or `rehearsal_<suffix>`)
  * NO password (a production credential must never be pasted into a rehearsal URL)
  * NO libpq override parameters (host, hostaddr, port, service, sslrootcert ... any query param
    that could redirect the connection elsewhere); the only allowed query parameter is
    `application_name`
  * nothing in the URL matches a production-like marker (cloudsql, googleapis, amjis, supabase,
    madhav-astrology, prod, rds, ...) — belt and braces on top of the host allow-list.

CLI: `rehearsal_guard.py <url>` exits 0 and prints the normalised URL if accepted, exits 2 and
prints `REFUSED: <reason>` on stderr otherwise. An empty / missing URL is refused.
"""
from __future__ import annotations

import re
import sys
from urllib.parse import parse_qsl, urlsplit

REHEARSAL_PORT = 55432
ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1"})
ALLOWED_SCHEMES = frozenset({"postgres", "postgresql"})
ALLOWED_QUERY_KEYS = frozenset({"application_name"})
DB_NAME_RE = re.compile(r"^rehearsal(_[a-z0-9_]+)?$")
PRODUCTION_MARKERS = (
    "cloudsql", "cloud-sql", "googleapis", "amjis", "supabase", "madhav-astrology",
    "asia-south1", "prod", "rds.amazonaws", "neon.tech", "azure", "hstgr",
)


def check_rehearsal_url(url: object) -> tuple[bool, str]:
    """Return (ok, reason). Never raises for a malformed value; malformed means refused."""
    if not isinstance(url, str) or not url.strip():
        return False, "empty or missing URL"
    raw = url.strip()
    low = raw.lower()
    for marker in PRODUCTION_MARKERS:
        if marker in low:
            return False, f"production-like marker {marker!r} present in URL"
    try:
        parts = urlsplit(raw)
        port = parts.port  # raises ValueError on a non-numeric / out-of-range port
    except ValueError as exc:
        return False, f"unparseable URL: {exc}"
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        return False, f"scheme {parts.scheme!r} is not postgres/postgresql"
    if "," in parts.netloc:
        return False, "multi-host URL refused"
    host = (parts.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        return False, f"host {host!r} is not localhost/127.0.0.1"
    if port is None:
        return False, f"port missing; must be explicitly {REHEARSAL_PORT}"
    if port != REHEARSAL_PORT:
        return False, f"port {port} is not the rehearsal port {REHEARSAL_PORT}"
    if parts.password:
        return False, "URL carries a password; the rehearsal cluster is password-less"
    dbname = parts.path.lstrip("/")
    if not DB_NAME_RE.match(dbname):
        return False, f"database {dbname!r} is not 'rehearsal' (or rehearsal_<suffix>)"
    if parts.fragment:
        return False, "URL fragment refused"
    for key, _ in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() not in ALLOWED_QUERY_KEYS:
            return False, f"query parameter {key!r} refused (could redirect the connection)"
    return True, "ok"


def main(argv: list[str]) -> int:
    url = argv[1] if len(argv) > 1 else ""
    ok, reason = check_rehearsal_url(url)
    if not ok:
        print(f"REFUSED: {reason}", file=sys.stderr)
        return 2
    print(url.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
