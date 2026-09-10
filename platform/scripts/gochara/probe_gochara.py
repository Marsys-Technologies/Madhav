#!/usr/bin/env python3
"""
probe_gochara.py — PARIṢKĀRA MR-30 / MR-08 gochara MCP serving probe.

Calls the DEPLOYED gochara MCP tools via the live MCP HTTP endpoint and
verifies that all three tools return valid (non-error) responses.

CRITICAL DESIGN NOTE — WHY THIS PROBE CALLS MCP, NOT SQL
---------------------------------------------------------
The lesson from GOCHARA-UTKARṢA: probe_utkarsha_w63_e2e_abhinandan.py
(utk-w61) probed the DB directly via SQL. A SQL-only probe can pass even
when the deployed MCP product is broken (wrong deployment, missing table
access, runtime misconfiguration). MR-08's closure gate requires a probe
that catches deployment errors — which means calling the DEPLOYED MCP
server's HTTP endpoint, not psycopg.

This probe calls the MCP server via JSON-RPC 2.0 POST (the same wire
protocol check_reconciliation_cadence.py uses for its live-mode canary
calls). It never opens a DB connection.

CAMPAIGN CONTEXT
----------------
Authored as part of PARIṢKĀRA MR-30 (Evidence + worktree hygiene).
Feeds MR-08's closure gate: "scripts in git" + "probe calls deployed
product, not just SQL".

TOOLS PROBED
------------
  gochara_forecast_get        — forward window forecast for a chart+date range
  gochara_activation_get      — point-in-time activation check for a chart+date
  gochara_election_avoidance_get — adverse windows for a chart+date range

All three tools in register_gochara_windows.ts. A non-500, non-RPC-error
response from each is the pass criterion (data presence depends on the
chart's build state; an honest empty response is still a PASS).

MCP ENDPOINT
------------
Reads MCP_URL from environment (default: https://amjis-mcp-qm256lasva-el.a.run.app/mcp).
Reads MCP_KEY (Bearer token) from MCP_KEY environment variable, or falls
back to gcloud:

    gcloud secrets versions access latest --secret=mcp-canary-key

Never prints or logs the key value.

Usage:
    python3 probe_gochara.py --chart-id <uuid>
    python3 probe_gochara.py --chart-id <uuid> --date 2026-09-01
    python3 probe_gochara.py --chart-id <uuid> --mcp-url https://custom-host/mcp
    python3 probe_gochara.py --help

Exit codes:
    0 — all 3 gochara tools returned ok
    1 — at least one tool returned an error or connection failed
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MCP_URL = "https://amjis-mcp-qm256lasva-el.a.run.app/mcp"
DEFAULT_TIMEOUT_S = 45


# ---------------------------------------------------------------------------
# Credential helpers  (never log the values)
# ---------------------------------------------------------------------------

def _resolve_mcp_url(override: str | None) -> str:
    if override:
        return override
    return os.environ.get("MCP_URL", DEFAULT_MCP_URL)


def _resolve_mcp_key() -> str | None:
    key = os.environ.get("MCP_KEY")
    if key:
        return key
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret=mcp-canary-key"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        key = result.stdout.strip()
        if key:
            return key
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


# ---------------------------------------------------------------------------
# MCP JSON-RPC call
# ---------------------------------------------------------------------------

def _call_mcp_tool(
    mcp_url: str,
    key: str | None,
    tool: str,
    arguments: dict,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """
    POST a JSON-RPC 2.0 tools/call request to the MCP HTTP endpoint.

    Returns a dict with keys:
      ok     (bool)  — True if call succeeded without RPC error
      status (int)   — HTTP status code (0 on transport error)
      error  (str)   — error message if not ok
      content        — parsed response content object, or None
    """
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }).encode("utf-8")

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(
        mcp_url,
        data=payload,
        method="POST",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = resp.status
            body_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc), "content": None}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": 0, "error": str(exc), "content": None}

    # MCP over HTTP may return SSE (data: ...) or plain JSON
    data_line = next(
        (ln for ln in body_text.splitlines() if ln.startswith("data:")),
        None,
    )
    json_text = data_line[len("data:"):].strip() if data_line else body_text

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        if status >= 400:
            return {
                "ok": False,
                "status": status,
                "error": f"HTTP {status}, unparseable body",
                "content": None,
            }
        return {"ok": True, "status": status, "error": None, "content": None}

    rpc_error = parsed.get("error") if isinstance(parsed, dict) else None
    if rpc_error:
        msg = rpc_error.get("message", str(rpc_error)) if isinstance(rpc_error, dict) else str(rpc_error)
        return {"ok": False, "status": status, "error": f"RPC error: {msg}", "content": None}

    result = parsed.get("result") if isinstance(parsed, dict) else None
    content = None
    if isinstance(result, dict):
        struct = result.get("structuredContent")
        if isinstance(struct, dict) and "object" in struct:
            content = struct["object"]
        else:
            texts = result.get("content")
            if isinstance(texts, list) and texts and isinstance(texts[0], dict):
                text_val = texts[0].get("text")
                if isinstance(text_val, str):
                    try:
                        content = json.loads(text_val)
                    except json.JSONDecodeError:
                        content = text_val

    return {"ok": True, "status": status, "error": None, "content": content}


# ---------------------------------------------------------------------------
# Main probe
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe the DEPLOYED gochara MCP tools via HTTP. "
            "Calls gochara_forecast_get, gochara_activation_get, and "
            "gochara_election_avoidance_get. "
            "PARIṢKĀRA MR-30/MR-08 versioned tooling. "
            "CRITICAL: calls the deployed MCP product, never direct SQL."
        ),
    )
    parser.add_argument(
        "--chart-id", required=True,
        help="UUID of the chart to probe (e.g. 482012f1-710e-4a25-994a-93821f5871aa)",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="ISO date for activation/forecast queries (default: today)",
    )
    parser.add_argument(
        "--mcp-url",
        default=None,
        help=f"MCP server URL (default: MCP_URL env or {DEFAULT_MCP_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Per-call timeout in seconds (default: {DEFAULT_TIMEOUT_S})",
    )
    args = parser.parse_args(argv)

    chart_id: str = args.chart_id
    probe_date: str = args.date
    mcp_url: str = _resolve_mcp_url(args.mcp_url)
    timeout_s: int = args.timeout

    mcp_key = _resolve_mcp_key()
    if mcp_key is None:
        print(
            "[probe_gochara] WARNING: no MCP key found (MCP_KEY env not set, "
            "gcloud fallback failed). Proceeding unauthenticated — will likely "
            "receive 401.",
            file=sys.stderr,
        )

    # Date range: probe_date to probe_date + 30 days
    try:
        from_date_obj = date.fromisoformat(probe_date)
    except ValueError:
        print(f"ERROR: --date must be ISO format (YYYY-MM-DD), got: {probe_date!r}", file=sys.stderr)
        return 1
    to_date = (from_date_obj + timedelta(days=30)).isoformat()
    from_date = probe_date

    print(f"[probe_gochara] MCP endpoint: {mcp_url}", file=sys.stderr)
    print(f"[probe_gochara] chart_id: {chart_id}", file=sys.stderr)
    print(f"[probe_gochara] date window: {from_date} -> {to_date}", file=sys.stderr)
    print(f"[probe_gochara] key present: {mcp_key is not None}", file=sys.stderr)

    # ── Define the three probe calls ─────────────────────────────────────────
    probes = [
        (
            "gochara_forecast_get",
            {
                "chart_id": chart_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        ),
        (
            "gochara_activation_get",
            {
                "chart_id": chart_id,
                "date": probe_date,
            },
        ),
        (
            "gochara_election_avoidance_get",
            {
                "chart_id": chart_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        ),
    ]

    # ── Execute and evaluate ─────────────────────────────────────────────────
    failures: list[str] = []

    for tool, arguments in probes:
        print(f"[probe_gochara] calling {tool}...", file=sys.stderr)
        result = _call_mcp_tool(mcp_url, mcp_key, tool, arguments, timeout_s)
        if result["ok"]:
            content_summary = "ok"
            content = result.get("content")
            if isinstance(content, dict):
                # Surface a few top-level keys for confirmation (not the whole payload)
                top_keys = list(content.keys())[:4]
                content_summary = f"ok (keys: {top_keys})"
            print(f"[probe_gochara]   {tool}: PASS — {content_summary}", file=sys.stderr)
        else:
            error_msg = result.get("error", "unknown error")
            status = result.get("status", 0)
            print(
                f"[probe_gochara]   {tool}: FAIL — status={status} error={error_msg}",
                file=sys.stderr,
            )
            failures.append(f"{tool} returned error: {error_msg} (HTTP {status})")

    # ── Print final verdict ──────────────────────────────────────────────────
    if not failures:
        print(f"PROBE PASS: all 3 gochara tools returned ok for chart {chart_id}")
        return 0
    else:
        for failure in failures:
            print(f"PROBE FAIL: {failure}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
