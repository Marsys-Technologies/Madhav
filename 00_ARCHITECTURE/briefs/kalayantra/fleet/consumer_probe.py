#!/usr/bin/env python3
"""Authenticated consumer-path MEASUREMENT of ONE fixed MCP tool call (J-6l-a61; SR-TEARDOWN-AUTHORITY-GATE item 3: production:false, fixed call set, one review).

The executor runs this for the fixed, reviewed, non-production kind `consumer_probe`. The only request argument is `--probe <id>`; the id selects one entry of
PROBES below and the entry holds the whole call: the tool name and its arguments. Nothing a request carries can name a host, a path, a tool, a chart or a header.
ONE `POST https://<HOST>/mcp` (JSON-RPC `tools/call`, the stateless Streamable-HTTP form the repository's own clients use) is made with the credential in the
`Authorization: Bearer` header ONLY (never `?api_key=`: URLs get logged; platform-mcp/src/server.ts resolveAuthHeader), no redirect followed, no proxy. ONE line is
printed, a `ky.consumer_probe/1` record of TYPED FIELDS ONLY: never a response body, never the credential, never the chart id.

  {schema, status, probe, tool, http_status, generation, manifest_id, image, migration_set, result, effective_states, body_sha256, body_bytes, measured_at,
   operation_id, request_sha256, credentials_sent, credential_echoed}

  status         MEASURED when a response was read, whatever its HTTP status (a 401 or 503 is a measurement, `http_status` says so); UNREACHABLE when no response was
                 read (connection, TLS or timeout failure: the reason is the failure class only); REFUSED when the probe id is not in the fixed set, no usable credential
                 is present (nothing is sent), the response is not readable as the thing it claims to be, or the response echoed the credential. Only MEASURED carries
                 `http_status`, `result`, `generation`, `manifest_id`, `effective_states`, `body_sha256` and `body_bytes`.
  result         per probe, a closed enum (RESULTS): `served` (a published answer), `absent` (the response states the surface is unpublished), `no_matching_rows` (a
                 published snapshot with no rows), `no_obstruction_state` (a published NOW snapshot with no usable obstruction state, so no arrival line), `sentinel_
                 negative_space` (kala_now_sentinel: every published obstruction state is information_unavailable or evaluated_silent), `unstated` (a served answer
                 that states no generation), `refused` (an HTTP non-200, an RPC or tool error, or a payload that is not the documented shape).
  generation / manifest_id
                 what the response itself states, else null. The Kāla snapshot states both at top level (platform-mcp/src/tools/kala_views/published_request.ts); the
                 Gochara tool states the generation in `coverage.coverage_manifest.generation` and on its window rows. A field the response does not state is null, never
                 inferred from the URL, the clock or a default (CLAUDE.md §N.7.6 / §N.8).
  image / migration_set
                 stated by NEITHER response: always null here. The deployed image and migration set come from `http_probe mcp_health` (image_digest, migration_set).
  effective_states
                 the sorted, de-duplicated `effective_state` values of the published kala_obstruction rows of a NOW snapshot (the closed vocabulary of
                 platform/src/lib/retrieval/registry/layers/L3_kala/arrival_state.ts), for `kala_now_sentinel` and `kala_arrival_line` only; else null.
  body_sha256    sha256 of the CANONICAL tool result object (the parsed `structuredContent.object` or `content[0].text`): a JSON object is re-serialised with sorted keys
                 and compact separators after every volatile key (`*_at`, `timestamp`, `time`, `uptime*`) is dropped (as http_probe.digest), so it does not depend on
                 JSON-vs-SSE framing and two reads of an unchanged surface hash equal. `body_bytes` is the length of the raw HTTP body.
  credentials_sent / credential_echoed
                 `credentials_sent` is true once the request carrying the header was handed to the socket (false for a refusal before any call). `credential_echoed` is
                 MEASURED: true iff the raw response body or its Content-Type contains the credential's exact bytes; such a response is REFUSED and nothing of it is kept.

The credential is read ONCE from the environment variable KY_CONSUMER_PROBE_KEY (the executor hands it to this kind's child only; executor.py `execute`). It is never
printed, never placed in a URL, never part of an error message (a failure is reported as its class name only). The chart id lives only in the PROBES table below.
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import re
import ssl
import sys
from typing import NamedTuple

SCHEMA = "ky.consumer_probe/1"
KEY_ENV = "KY_CONSUMER_PROBE_KEY"
HOST = "amjis-mcp-qm256lasva-el.a.run.app"     # the MCP service the repository's audit harness targets (platform/scripts/audit/doctrine_harness/run.ts DEFAULT_TARGET)
PATH = "/mcp"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
MAX_BODY = 1024 * 1024
TIMEOUT_S = 30
REQUEST_ID = 1
KEY_SHAPE = re.compile(r"[A-Za-z0-9._~+/=-]{8,512}\Z")          # header-safe: no whitespace, no CR/LF, no quote
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
VOLATILE = re.compile(r"(.*_at|timestamp|time|uptime.*)\Z")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
RESULTS = ("served", "absent", "no_matching_rows", "no_obstruction_state", "sentinel_negative_space", "unstated", "refused")
# arrival_state.ts `labels`: the closed vocabulary of an obstruction's effective_state; the first two are the "silent" ones
EFFECTIVE_STATES = ("outside_risk_set", "method_inapplicable", "information_unavailable", "evaluated_silent", "obstruction_in_force",
                    "obstruction_cancelled", "obstruction_partly_cancelled", "obstruction_contested")
SILENT_STATES = ("information_unavailable", "evaluated_silent")
# registry_alias.ts KalaView, in the order of platform/python-sidecar/services/ka_tulana/__init__.py `views`: kala_view_1 .. kala_view_7
KALA_VIEWS = ("now", "ahead", "priority", "elect", "story", "ritual", "explain")


def _call(tool: str, arguments: dict, reader: str) -> dict:
    return {"tool": tool, "arguments": arguments, "reader": reader}


PROBES = {
    # gochara_activation_get with no as_of_date: the tool resolves the AUTHORITATIVE generation (kala_gochara_authority) itself and withholds a governed generation that
    # is not published and sealed (register_gochara_windows.ts governedGenerationGate), so after the J-6 flip it is the served head as a consumer sees it.
    "gochara_served_head": _call("gochara_activation_get", {"chart_id": CANONICAL_CHART}, "gochara"),
    # kala_now_sentinel and kala_arrival_line are the SAME call (kala_now_get, K9-6 published_request) read two ways.
    "kala_now_sentinel": _call("kala_now_get", {"chart_id": CANONICAL_CHART, "published_request": {"limit": 50}}, "now_sentinel"),
    "kala_arrival_line": _call("kala_now_get", {"chart_id": CANONICAL_CHART, "published_request": {"limit": 50}}, "now_arrival"),
    **{f"kala_view_{n}": _call(f"kala_{view}_get", {"chart_id": CANONICAL_CHART, "published_request": {"limit": 1}}, f"view:{view}")
       for n, view in enumerate(KALA_VIEWS, start=1)},
}


class Refused(RuntimeError):
    pass


class Unreachable(RuntimeError):
    def __init__(self, reason: str, sent: bool):
        super().__init__(reason)
        self.sent = sent


class Response(NamedTuple):
    status: int
    content_type: str
    body: bytes


def fetch(request: dict) -> Response:
    """ONE POST. No redirect is followed and no proxy is used (http.client honours neither); the body is cut at MAX_BODY + 1. A failure raises Unreachable(class name)."""
    conn = http.client.HTTPSConnection(request["host"], timeout=TIMEOUT_S, context=ssl.create_default_context())
    sent = False
    try:
        conn.request("POST", request["path"], body=request["body"], headers=request["headers"])
        sent = True
        response = conn.getresponse()
        return Response(response.status, response.getheader("Content-Type") or "", response.read(MAX_BODY + 1))
    except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
        raise Unreachable(type(exc).__name__, sent) from None
    finally:
        conn.close()


def build_request(spec: dict, key: str) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": REQUEST_ID, "method": "tools/call", "params": {"name": spec["tool"], "arguments": spec["arguments"]}},
                      sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"host": HOST, "path": PATH, "body": body,
            "headers": {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                        "Authorization": "Bearer " + key, "User-Agent": "kalayantra-consumer-probe/1"}}


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items() if not VOLATILE.fullmatch(str(k).lower())}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value


def digest(payload) -> str:
    return hashlib.sha256(json.dumps(canonical(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def rpc_message(body: bytes, content_type: str) -> dict:
    """The one JSON-RPC message answering REQUEST_ID, from a plain JSON body or an SSE (`data:`) body."""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("the response is not UTF-8 text") from None
    candidates = []
    if "text/event-stream" in content_type.lower():
        for event in re.split(r"\r?\n\r?\n", text):
            data = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
            if data:
                candidates.append(data)
    else:
        candidates.append(text)
    for raw in candidates:
        try:
            message = json.loads(raw)
        except ValueError:
            continue
        if isinstance(message, dict) and message.get("jsonrpc") == "2.0" and message.get("id") == REQUEST_ID and ("result" in message or "error" in message):
            return message
    raise Refused("the response carries no JSON-RPC answer to this request")


def tool_payload(message: dict) -> tuple[dict | None, bool]:
    """(the tool's result object, is_error). None when the call was an RPC error or the result is not a JSON object."""
    result = message.get("result")
    if "error" in message or not isinstance(result, dict):
        return None, True
    error = result.get("isError") is True
    structured = result.get("structuredContent")
    payload = structured.get("object") if isinstance(structured, dict) else None
    if not isinstance(payload, dict):
        content = result.get("content")
        text = content[0].get("text") if isinstance(content, list) and content and isinstance(content[0], dict) else None
        try:
            payload = json.loads(text) if isinstance(text, str) else None
        except ValueError:
            payload = None
    return (payload if isinstance(payload, dict) else None), error


def _obj(value):
    return value if isinstance(value, dict) else {}


def snapshot(payload: dict, view: str) -> tuple[str, str | None, str | None]:
    """(kind, generation, manifest_id) of a K9-6 published snapshot (published_request.ts servePublishedRequest). kind: published | unpublished | invalid."""
    manifest = payload.get("manifest")
    rows = payload.get("rows")
    base_ok = payload.get("view") == view and payload.get("chart_id") == CANONICAL_CHART and isinstance(rows, list)
    if not base_ok:
        return "invalid", None, None
    if payload.get("manifest_id") is None:
        unpublished = payload.get("empty_reason") == "unpublished" and rows == [] and payload.get("generation") is None and manifest is None
        return ("unpublished" if unpublished else "invalid"), None, None
    manifest_id, generation = payload.get("manifest_id"), payload.get("generation")
    if (not (isinstance(manifest_id, str) and manifest_id and isinstance(generation, str) and generation)
            or _obj(manifest).get("manifest_id") != manifest_id or _obj(manifest).get("generation") != generation
            or payload.get("empty_reason") != (None if rows else "no_matching_rows")):
        return "invalid", None, None
    return "published", generation, (manifest_id if UUID.fullmatch(manifest_id) else None)


def obstruction_states(payload: dict, generation: str) -> list[str] | None:
    """arrival_state.ts arrivalFromPublishedNow: the sorted effective states of the published kala_obstruction rows, or None when the derivation is null."""
    states = set()
    for row in payload["rows"]:
        row = _obj(row)
        if row.get("source_table") != "kala_obstruction" or row.get("qualification") != "published":
            continue
        data = _obj(row.get("data"))
        state = _obj(_obj(data.get("assertion")).get("payload")).get("effective_state")
        if data.get("generation") != generation or not isinstance(state, str) or state not in EFFECTIVE_STATES:
            return None
        states.add(state)
    return sorted(states) or None


def read_view(payload: dict, view: str, reader: str) -> dict:
    kind, generation, manifest_id = snapshot(payload, view)
    out = {"result": "refused", "generation": None, "manifest_id": None, "effective_states": None}
    if kind == "unpublished":
        out["result"] = "absent"
    elif kind == "published":
        out.update(generation=generation, manifest_id=manifest_id)
        out["result"] = "served" if payload["rows"] else "no_matching_rows"
        if payload["rows"] and reader in ("now_sentinel", "now_arrival"):
            states = obstruction_states(payload, generation)
            out["effective_states"] = states
            if states is None:
                out["result"] = "no_obstruction_state"
            elif reader == "now_sentinel" and all(s in SILENT_STATES for s in states):
                out["result"] = "sentinel_negative_space"
    return out


def read_gochara(payload: dict) -> dict:
    """The served head as gochara_activation_get states it: `coverage.status == 'unpublished'` is absent; otherwise the generation named by the coverage manifest and
    the window rows (one generation per response by construction: AUTHORITATIVE_GENERATION_FILTER), else unstated."""
    coverage, envelope = payload.get("coverage"), payload.get("provenance_envelope")
    out = {"result": "refused", "generation": None, "manifest_id": None, "effective_states": None}
    if not isinstance(coverage, dict) or not isinstance(envelope, dict) or not isinstance(payload.get("windows"), list):
        return out
    if coverage.get("status") == "unpublished":
        out["result"] = "absent"
        return out
    if envelope.get("backing_data_reachable") is False:
        return out
    stated = set()
    manifest_generation = _obj(coverage.get("coverage_manifest")).get("generation")
    if isinstance(manifest_generation, str) and manifest_generation:
        stated.add(manifest_generation)
    for window in payload["windows"]:
        generation = _obj(window).get("generation")
        if isinstance(generation, str) and generation:
            stated.add(generation)
    if len(stated) > 1:
        return out                                  # two generations in one answer is not a served head
    out["generation"] = next(iter(stated)) if stated else None
    out["result"] = "served" if stated else "unstated"
    return out


def read_payload(probe: str, payload: dict) -> dict:
    reader = PROBES[probe]["reader"]
    if reader == "gochara":
        return read_gochara(payload)
    view = PROBES[probe]["tool"][len("kala_"):-len("_get")]
    return read_view(payload, view, reader)


def request_digest(req: dict) -> str:
    """The executor's request digest, byte for byte (as served_probe.request_digest; the executor's own test pins that)."""
    bound = {k: v for k, v in req.items() if k not in ("acceptance_receipt", "expires_at") and not k.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def measure(probe: str, environ: dict, transport=fetch, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> tuple[int, dict]:
    try:
        request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError:
        request = None
    request = request if isinstance(request, dict) else {}
    record = {"schema": SCHEMA, "status": None, "probe": probe if probe in PROBES else None, "operation_id": request.get("operation_id"),
              "request_sha256": request_digest(request) if request else None, "credentials_sent": False, "credential_echoed": False}
    if probe not in PROBES:
        record.update(status="REFUSED", reason="the probe id is not in the fixed set")
        return 1, record
    key = environ.get(KEY_ENV) or ""
    if not KEY_SHAPE.fullmatch(key):
        record.update(status="REFUSED", reason="no usable consumer credential is present; nothing was sent")
        return 1, record
    spec = PROBES[probe]
    record["tool"] = spec["tool"]
    try:
        response = transport(build_request(spec, key))
    except Unreachable as exc:
        record.update(status="UNREACHABLE", reason=str(exc), credentials_sent=exc.sent)
        return 1, record
    except Exception as exc:                        # a transport bug: its class name only, never a traceback that could carry the request
        record.update(status="UNREACHABLE", reason=type(exc).__name__, credentials_sent=True)
        return 1, record
    record["credentials_sent"] = True
    if isinstance(response.status, bool) or not isinstance(response.status, int) or not 100 <= response.status <= 599:
        record.update(status="REFUSED", reason="the response carries no HTTP status")
        return 1, record
    if not isinstance(response.body, bytes) or len(response.body) > MAX_BODY:
        record.update(status="REFUSED", reason="the response body is not readable within the size limit")
        return 1, record
    if key.encode() in response.body or key in (response.content_type or ""):
        record.update(status="REFUSED", reason="the response echoed the credential; nothing of it is kept", credential_echoed=True)
        return 1, record
    payload, is_error = None, False
    if response.status == 200:
        try:
            payload, is_error = tool_payload(rpc_message(response.body, response.content_type or ""))
        except Refused as exc:
            record.update(status="REFUSED", reason=str(exc))
            return 1, record
    stated = {"result": "refused", "generation": None, "manifest_id": None, "effective_states": None, "body_sha256": None}
    if payload is not None:
        stated["body_sha256"] = digest(payload)
        if not is_error:
            stated.update(read_payload(probe, payload))
    record.update(status="MEASURED", http_status=response.status, image=None, migration_set=None, body_bytes=len(response.body),
                  measured_at=clock().strftime("%Y-%m-%dT%H:%M:%SZ"), **stated)
    return 0, record


def main(argv=None, environ=None, transport=fetch, out=None, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> int:
    parser = argparse.ArgumentParser(description="Authenticated read-only measurement of one fixed MCP tool call.", allow_abbrev=False)
    parser.add_argument("--probe", required=True)
    args = parser.parse_args(argv)                                        # any other argument exits 2 before a call
    code, record = measure(args.probe, os.environ if environ is None else environ, transport, clock)
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), file=out or sys.stdout, flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
