#!/usr/bin/env python3
"""Read-only probe of ONE served HTTP response (SR-TEARDOWN-AUTHORITY-GATE item 3).

The executor runs this for the fixed, reviewed, non-production, read-only kind `served_probe` (fleet/executor_ops.json). It holds no argument that
can name a URL: the only request argument is `--endpoint <name>`, and the name must be a key of ENDPOINTS below (a name that is not is REFUSED before
any network call). ENDPOINTS equals the `probe_endpoints` object of the table entry, byte for byte (a test pins that), and the executor's admission
refuses a name the table does not declare before this script is started. A new endpoint is a reviewed edit of both.

What one run does: ONE `GET` of the endpoint's https URL (host fixed to HOST), sending NO credential of any kind (no Authorization, no cookie, no
token header; the child environment carries none), following NO redirect (a 3xx is a non-2xx answer, never a hop to another host). It prints ONE line,
a `ky.served_probe/1` JSON record: the HTTP status, the content type, the byte length and the sha256 of the body, and the body itself ONLY when
(1) the endpoint is declared `store_body: true` (a chart-scoped endpoint for the native is declared false: digest and length only),
(2) the body is UTF-8 text of at most BODY_STORE_MAX bytes and (3) it carries none of PERSONAL_MARKERS. Otherwise `body` is null and `body_withheld`
says which rule held it back. A body larger than BODY_READ_MAX is not digested at all (a digest of a prefix would be a false identity): length and
digest read null beside the reason.

Exit status: 0 only for a 2xx answer. Any other status, a transport error or an oversize body exits 1 with the observed facts in the record; the
executor then writes a FAILED receipt (executor.served_probe_proof re-checks the record and the privacy rule itself). An exit status alone proves nothing.
Honest nulls (CLAUDE.md §N.7.6 / §N.8): a fact that could not be read is null beside the reason, never a default.

(I) INTERPRETATION: the briefs of J-6l, K9-6 and V-J6 name capabilities, not URLs, and the served MCP primitives are POST routes behind a service token that a
credential-free child cannot hold; so ENDPOINTS starts with the one public GET the repository proves (`/api/health`, platform/src/app/api/health/route.ts;
host from platform/scripts/provision_watchdog_scheduler.sh APP_URL). Adding a readback's endpoint is a reviewed one-entry edit once its GET route is named.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SCHEMA = "ky.served_probe/1"
HOST = "madhav.marsys.in"
ENDPOINTS = {
    "app_health": {"url": f"https://{HOST}/api/health", "store_body": True},
}
NAME = re.compile(r"[a-z][a-z0-9_]{0,39}")
TIMEOUT_S = 30
BODY_READ_MAX = 2 * 1024 * 1024        # reading stops one byte past this; beyond it the body has no digest
BODY_STORE_MAX = 16 * 1024             # a body longer than this is never stored, only digested
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"      # CLAUDE.md §B; the executor's CANONICAL_CHART
PERSONAL_MARKERS = (CHART_ID, "abhisek", "mohanty", "1984-02-05", "bhubaneswar")      # CLAUDE.md §B subject; a match keeps the body out of the record


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def default_fetch(url: str, timeout: float = TIMEOUT_S) -> tuple[int, str | None, bytes, bool]:
    """(status, content-type, body prefix, truncated) of ONE credential-free GET; a 3xx/4xx/5xx answer is returned, not raised. A transport error raises."""
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json, text/plain, */*", "User-Agent": "kalayantra-served-probe/1"})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as e:
        response = e
    with response:
        body = response.read(BODY_READ_MAX + 1)
        return response.status, response.headers.get("Content-Type"), body[:BODY_READ_MAX], len(body) > BODY_READ_MAX


def request_digest(req: dict) -> str:
    """The executor's request digest, byte for byte (its own test pins that)."""
    bound = {k: v for k, v in req.items() if k not in ("acceptance_receipt", "expires_at") and not k.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def body_to_store(body: bytes, declared_store: bool) -> tuple[str | None, str | None]:
    """(text, withheld-reason). The text is returned only when every storage rule holds."""
    if declared_store is not True:
        return None, "endpoint_declared_digest_only"
    if len(body) > BODY_STORE_MAX:
        return None, "body_too_large_to_store"
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return None, "body_not_utf8_text"
    lowered = text.lower()
    if any(marker in lowered for marker in PERSONAL_MARKERS):
        return None, "personal_data_marker"
    return text, None


def run(endpoint: str, environ: dict, fetch=default_fetch, endpoints: dict | None = None, now: dt.datetime | None = None) -> tuple[int, dict]:
    now = now or dt.datetime.now(dt.timezone.utc)
    allowed = ENDPOINTS if endpoints is None else endpoints
    try:
        request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError:
        request = None
    request = request if isinstance(request, dict) else {}
    known = isinstance(endpoint, str) and NAME.fullmatch(endpoint) is not None and endpoint in allowed
    declared = allowed[endpoint] if known else {}
    record = {"schema": SCHEMA, "action": "probe", "method": "GET", "status": None, "reason": None, "endpoint": endpoint if known else None,
              "url": declared.get("url"), "operation_id": request.get("operation_id"), "request_sha256": request_digest(request) if request else None,
              "credentials_sent": False, "http_status": None, "content_type": None, "body_bytes": None, "body_sha256": None,
              "body": None, "body_withheld": None, "measured_at": now.isoformat(timespec="seconds")}
    if not known:
        record.update(status="REFUSED", reason="endpoint is not on the served-probe allow-list")
        return 1, record
    url = declared.get("url")
    parts = urllib.parse.urlsplit(url) if isinstance(url, str) else None
    if parts is None or parts.scheme != "https" or parts.hostname != HOST or parts.username or parts.password:
        record.update(status="REFUSED", reason=f"the declared URL is not an https URL on {HOST}")
        return 1, record
    try:
        status, content_type, body, truncated = fetch(url)
    except Exception as e:
        record.update(status="FAILED", reason=f"the request failed: {type(e).__name__}")      # the message may carry a resolved address; the type is enough
        return 1, record
    record["http_status"] = status if isinstance(status, int) and not isinstance(status, bool) else None
    record["content_type"] = content_type[:200] if isinstance(content_type, str) else None
    if truncated:
        record.update(status="FAILED", reason=f"the body is larger than {BODY_READ_MAX} bytes, so it has no digest", body_withheld="body_too_large_to_digest")
        return 1, record
    record["body_bytes"] = len(body)
    record["body_sha256"] = hashlib.sha256(body).hexdigest()
    record["body"], record["body_withheld"] = body_to_store(body, declared.get("store_body"))
    if record["http_status"] is None or not 200 <= record["http_status"] < 300:
        record.update(status="FAILED", reason=f"the served response is HTTP {record['http_status']}, not 2xx")
        return 1, record
    record["status"] = "OK"
    return 0, record


def main(argv: list[str] | None = None, environ: dict | None = None, fetch=default_fetch, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--endpoint", required=True)
    args = parser.parse_args(argv)
    rc, record = run(args.endpoint, os.environ if environ is None else environ, fetch)
    out.write(json.dumps(record, sort_keys=True) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
