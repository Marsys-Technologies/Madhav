#!/usr/bin/env python3
"""rehearsal_guard.py — E5.6 URL guard for the off-production rehearsal cluster.

The rehearsal cluster is the ONLY database the rehearsal tooling may touch. This guard is the
single decision point `apply_schema.sh` / `replay_schema.py` (and any later E5.6/E5.7 tooling)
must pass a URL through BEFORE any process receives it. It does not just judge the URL: it
returns the NORMALISED URL rebuilt from validated components, and callers must use that value,
never the original string.

A URL is accepted only if ALL hold (exact, byte-level rules; anything unusual is refused):
  * no whitespace and no control character anywhere (leading/trailing included)
  * lower-case scheme `postgres` or `postgresql`
  * at most one `@`; user (optional) matches [A-Za-z0-9_.-]+; NO password
  * host is EXACTLY the text `127.0.0.1` (no `localhost` — it can resolve to ::1, which an
    ssh tunnel or another listener could own; no 127.1 / decimal / hex / octal / IPv6 / %-encoding)
  * port is EXACTLY the text `55432`
  * database matches `rehearsal` or `rehearsal_<[a-z0-9_]+>` (fullmatch)
  * the only query parameter allowed is a single `application_name` ([A-Za-z0-9_.-]{0,64});
    everything else (host, hostaddr, port, service, sslmode, options, ... any case, any %-encoding)
    is refused; a fragment can never match the strict component patterns
  * nothing matches a production-like marker (cloudsql, amjis, supabase, prod, ...) — belt and braces.

CLI: `rehearsal_guard.py <url>` exits 0 and prints the NORMALISED URL if accepted, exits 2 and
prints `REFUSED: <reason>` on stderr otherwise. An empty / missing URL is refused.
"""
from __future__ import annotations

import re
import sys
from urllib.parse import parse_qsl

REHEARSAL_PORT = 55432
REHEARSAL_HOST = "127.0.0.1"
ALLOWED_SCHEMES = ("postgres", "postgresql")
ALLOWED_QUERY_KEYS = ("application_name",)
DB_NAME_RE = re.compile(r"rehearsal(_[a-z0-9_]+)?")
USER_RE = re.compile(r"[A-Za-z0-9_.-]+")
APPNAME_RE = re.compile(r"[A-Za-z0-9_.-]{0,64}")
PRODUCTION_MARKERS = (
    "cloudsql", "cloud-sql", "googleapis", "amjis", "supabase", "madhav-astrology",
    "asia-south1", "prod", "rds.amazonaws", "neon.tech", "azure", "hstgr",
)
_BAD_CHARS = re.compile(r"[\s\x00-\x1f\x7f-\x9f\\]")


def _evaluate(url: object) -> tuple[str | None, str]:
    """Return (normalised_url, "ok") or (None, reason). Never raises."""
    if not isinstance(url, str) or url == "":
        return None, "empty or missing URL"
    if _BAD_CHARS.search(url):
        return None, "whitespace, control character or backslash in URL"
    low = url.lower()
    for marker in PRODUCTION_MARKERS:
        if marker in low:
            return None, f"production-like marker {marker!r} present in URL"
    scheme, sep, rest = url.partition("://")
    if not sep or scheme not in ALLOWED_SCHEMES:
        return None, f"scheme {scheme!r} is not postgres/postgresql"
    rest, _, query = rest.partition("?")
    authority, _slash, path = rest.partition("/")
    if authority.count("@") > 1:
        return None, "more than one '@' in the authority"
    userinfo, at, hostport = authority.rpartition("@")
    if at:
        if ":" in userinfo:
            return None, "URL carries a password; the rehearsal cluster is password-less"
        if not USER_RE.fullmatch(userinfo):
            return None, "user name has unexpected characters"
    host_raw, _colon, port_raw = hostport.partition(":")
    if host_raw != REHEARSAL_HOST:
        return None, f"host {host_raw!r} is not exactly {REHEARSAL_HOST}"
    if port_raw != str(REHEARSAL_PORT):
        return None, f"port {port_raw!r} is not the rehearsal port {REHEARSAL_PORT}"
    if not DB_NAME_RE.fullmatch(path):
        return None, f"database {path!r} is not 'rehearsal' (or rehearsal_<suffix>)"
    app_name = None
    if query:
        try:
            pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
        except ValueError:
            return None, "malformed query string"
        if len(pairs) != 1:
            return None, "more than one query parameter refused"
        key, value = pairs[0]
        if key not in ALLOWED_QUERY_KEYS or "%" in query.split("=", 1)[0]:
            return None, f"query parameter {key!r} refused (could redirect the connection)"
        if not APPNAME_RE.fullmatch(value) or "%" in query:
            return None, "application_name has unexpected characters"
        app_name = value
    normalised = f"postgresql://{userinfo + '@' if at else ''}{REHEARSAL_HOST}:{REHEARSAL_PORT}/{path}"
    if app_name is not None:
        normalised += f"?application_name={app_name}"
    return normalised, "ok"


def check_rehearsal_url(url: object) -> tuple[bool, str]:
    """Return (ok, reason). Malformed means refused."""
    normalised, reason = _evaluate(url)
    return normalised is not None, reason


def normalise_rehearsal_url(url: object) -> str:
    """Return the normalised URL, or raise ValueError(reason). Callers MUST use this value."""
    normalised, reason = _evaluate(url)
    if normalised is None:
        raise ValueError(reason)
    return normalised


def main(argv: list[str]) -> int:
    url = argv[1] if len(argv) > 1 else ""
    try:
        normalised = normalise_rehearsal_url(url)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(normalised)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
