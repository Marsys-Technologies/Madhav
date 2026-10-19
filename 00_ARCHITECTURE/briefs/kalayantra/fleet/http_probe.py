#!/usr/bin/env python3
"""Read-only, credential-free HTTP MEASUREMENT of ONE fixed URL (SR-TEARDOWN-AUTHORITY-GATE item 3: production:false, fixed URL set, one review).

The executor runs this for the fixed, reviewed, non-production kind `http_probe`. The only request argument is `--probe <id>`; the id selects
one entry of PROBES below, and the entry holds the whole URL. Nothing a request carries can name a host, a path or a header. One
unauthenticated `GET` is made (no cookie, no token, no authorization header, no proxy, no redirect followed) and ONE line is printed,
a `ky.http_probe/1` record (EXPECTED_TABLE.json `http_probe.record` of the W5/W6 union pack):

  {schema, status, probe, url, http_status, generation, image, migration_set, body_sha256, body_format, body_bytes, revision, deployed_sha, measured_at}

  status         MEASURED when a response was read, whatever its HTTP status (a 503 is a measurement, `http_status` says so); UNREACHABLE when no
                 response was read (connection, TLS or timeout failure: the reason is the failure class only); REFUSED when the probe id is not one
                 this kind can measure, or the response is not readable as the thing it claims to be. Only MEASURED carries `http_status`.
  generation / image / migration_set
                 what the response itself states, else null. `generation` is the body's own `generation` string; `image` the body's own
                 `image_digest` (sha256:<64 hex>); `migration_set` the body's own list of {filename, sha256}. A field the response does not state
                 is null, never inferred from the URL or the clock (CLAUDE.md §N.7.6 / §N.8).
  body_sha256    sha256 of the CANONICAL body: a JSON object is re-serialised with sorted keys and compact separators after every volatile key
                 (`*_at`, `timestamp`, `time`, `uptime*`) is dropped, so two reads of an unchanged surface hash equal and the J-6r "served response
                 byte-identical to before the flip" comparison cannot be defeated by a clock. A body that is not a JSON object hashes as its raw bytes
                 (`body_format: raw`).

Probes that are NOT measurable here (REFUSED, no request made): the Gochara served-head, the seven Kāla views, the `kala_now_get` sentinel and the
arrival line are served only to an authenticated principal through the MCP/consumer path, and this kind holds no credential by design. They need an
authenticated consumer-path kind (J-6l-a61 owns the independent consumer path); registering a URL for them here would measure a login page.

Credentials: this script never reads the environment for one, never prints one, never sends one. Standard library only: the executor copies this
single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import re
import ssl
import sys
from urllib.parse import urlsplit

SCHEMA = "ky.http_probe/1"
MAX_BODY = 1024 * 1024
TIMEOUT_S = 20
PROBES = {
    # The MCP service's own liveness route (platform-mcp/src/server.ts `app.get('/health')`: status, deployed_sha, revision, tools); the same route
    # the deploy workflow's candidate smoke reads (.github/workflows/deploy.yml `$SMOKE_MCP_URL/health`). Host: the service URL the repository's
    # audit scripts use as their default target (platform/scripts/audit/doctrine_harness/run.ts DEFAULT_TARGET, minus `/mcp`).
    "mcp_health": "https://amjis-mcp-qm256lasva-el.a.run.app/health",
}
NOT_MEASURABLE = {
    "gochara_served_head": "served only to an authenticated principal through the consumer path",
    "kala_now_sentinel": "kala_now_get is an authenticated MCP tool call",
    "kala_seven_views": "the seven views are authenticated MCP tool calls",
    "kala_arrival_line": "the arrival line is an authenticated MCP tool call",
}
VOLATILE = re.compile(r"(.*_at|timestamp|time|uptime.*)\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
MIGRATION_FILE = re.compile(r"[0-9]+_[A-Za-z0-9_]+\.sql\Z")


class Refused(RuntimeError):
    pass


class Unreachable(RuntimeError):
    pass


def fetch(url: str) -> tuple[int, bytes]:
    """ONE unauthenticated GET. No redirect is followed and no proxy is used (http.client honours neither); the body is cut at MAX_BODY + 1."""
    parts = urlsplit(url)
    conn = http.client.HTTPSConnection(parts.netloc, timeout=TIMEOUT_S, context=ssl.create_default_context())
    try:
        conn.request("GET", parts.path, headers={"Accept": "application/json", "User-Agent": "kalayantra-http-probe/1"})
        response = conn.getresponse()
        return response.status, response.read(MAX_BODY + 1)
    except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
        raise Unreachable(type(exc).__name__) from None
    finally:
        conn.close()


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items() if not VOLATILE.fullmatch(str(k).lower())}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value


def digest(body: bytes) -> tuple[str, str]:
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        text = json.dumps(canonical(parsed), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(text.encode("utf-8")).hexdigest(), "json"
    return hashlib.sha256(body).hexdigest(), "raw"


def stated(body: bytes) -> dict:
    """What the response says about itself; every field null unless it is stated in the exact shape."""
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = None
    doc = parsed if isinstance(parsed, dict) else {}
    generation = doc.get("generation")
    image = doc.get("image_digest")
    deployed = doc.get("deployed_sha")
    revision = doc.get("revision")
    migrations = doc.get("migration_set")
    if not (isinstance(migrations, list) and migrations and all(
            isinstance(m, dict) and set(m) == {"filename", "sha256"} and isinstance(m["filename"], str) and MIGRATION_FILE.fullmatch(m["filename"])
            and isinstance(m["sha256"], str) and HEX64.fullmatch(m["sha256"]) for m in migrations)):
        migrations = None
    return {
        "generation": generation if isinstance(generation, str) and generation else None,
        "image": image if isinstance(image, str) and IMAGE.fullmatch(image) else None,
        "migration_set": migrations,
        "revision": revision if isinstance(revision, str) and revision else None,
        "deployed_sha": deployed if isinstance(deployed, str) and SHA40.fullmatch(deployed) else None,
    }


def measure(probe: str, transport=fetch, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    if probe in NOT_MEASURABLE:
        raise Refused(f"probe {probe!r} is not measurable without a credential: {NOT_MEASURABLE[probe]}")
    url = PROBES.get(probe)
    if url is None:
        raise Refused("the probe id is not in the fixed set")
    status, body = transport(url)
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
        raise Refused("the response carries no HTTP status")
    if not isinstance(body, bytes) or len(body) > MAX_BODY:
        raise Refused("the response body is not readable within the size limit")
    sha, form = digest(body)
    return {"schema": SCHEMA, "status": "MEASURED", "probe": probe, "url": url, "http_status": status, **stated(body),
            "body_sha256": sha, "body_format": form, "body_bytes": len(body), "measured_at": clock().strftime("%Y-%m-%dT%H:%M:%SZ")}


def cli(argv=None, transport=fetch) -> int:
    parser = argparse.ArgumentParser(description="Read-only HTTP measurement of one fixed URL.", allow_abbrev=False)
    parser.add_argument("--probe", required=True)
    args = parser.parse_args(argv)                                        # any other argument exits 2 before a call
    try:
        record, code = measure(args.probe, transport), 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "probe": args.probe, "reason": str(exc)}, 1
    except Unreachable as exc:
        record, code = {"schema": SCHEMA, "status": "UNREACHABLE", "probe": args.probe, "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
