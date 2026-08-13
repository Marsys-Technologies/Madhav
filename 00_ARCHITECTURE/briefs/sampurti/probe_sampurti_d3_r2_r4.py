#!/usr/bin/env python3
"""
probe_sampurti_d3_r2_r4.py — SAMPŪRTI Δ3 R2+R4 MCP proof runner.

Calls the deployed MCP server to produce gate evidence for:
  R2 [SEV-2]: gochara_forecast_get — marriage row in roots (not legacy_flat),
              resolution='era', is_timing_window=true nested under era parent.
  R4 [G-P4]:  kala_ahead_get — field_snapshot_id=kfs_* (not 'field_not_yet_built');
              prospective row keyed to live field window_id + authority_basis shown.

PRECONDITIONS (verify before running):
  1. FIELD-INTEGRATED marker posted by Δ1 to campaign-coordination.
  2. Deployed MCP server at amjis-mcp-938361928218.asia-south1.run.app live.
  3. MARSYS_MCP_KEY set (via --mcp-key or env var MARSYS_MCP_KEY).

Usage:
  python3 probe_sampurti_d3_r2_r4.py \\
    --chart-id 482012f1-710e-4a25-994a-93821f5871aa \\
    --mcp-key <MARSYS_MCP_KEY> \\
    [--r2-date-from 2020-01-01] \\
    [--r2-date-to 2030-12-31] \\
    [--r2-only | --r4-only]

Exit codes: 0=PASS, 1=FAIL (assertion), 2=error (network/auth).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
MCP_URL = "https://amjis-mcp-938361928218.asia-south1.run.app"
MCP_VERSION = "2025-03-26"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chart-id", required=True, help="Chart UUID (canonical: 482012f1-...)")
    p.add_argument("--mcp-key", default=os.environ.get("MARSYS_MCP_KEY", ""), help="MCP bearer token")
    p.add_argument("--r2-date-from", default="2020-01-01", help="gochara_forecast_get date_from (YYYY-MM-DD)")
    p.add_argument("--r2-date-to", default="2030-12-31", help="gochara_forecast_get date_to (YYYY-MM-DD)")
    p.add_argument("--r2-only", action="store_true", help="Run R2 proof only")
    p.add_argument("--r4-only", action="store_true", help="Run R4 proof only")
    return p.parse_args()


def mcp_call(tool: str, arguments: dict, mcp_key: str) -> Any:
    """Call an MCP tool via JSON-RPC over HTTP.  Returns the content dict."""
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        raise SystemExit("urllib not available")

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }).encode()

    req = urllib.request.Request(
        f"{MCP_URL}/mcp",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mcp_key}",
            "MCP-Protocol-Version": MCP_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
    except Exception as e:
        raise SystemExit(f"ERROR: MCP call to {tool} failed: {e}", 2)

    # Handle SSE or plain JSON response
    data: Any = None
    if raw.startswith("data:"):
        # SSE stream — extract first data line that is valid JSON
        for line in raw.splitlines():
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    break
                except json.JSONDecodeError:
                    continue
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise SystemExit(f"ERROR: Non-JSON response from {tool}: {raw[:200]}", 2)

    if data is None:
        raise SystemExit(f"ERROR: No parseable data from {tool}: {raw[:200]}", 2)

    if "error" in data:
        raise SystemExit(f"ERROR: MCP error from {tool}: {data['error']}", 2)

    result = data.get("result", data)
    # MCP tools/call wraps content in result.content[0].text
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and content:
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return result


# ---------------------------------------------------------------------------
# R2 proof — gochara_forecast_get
# ---------------------------------------------------------------------------

def run_r2_proof(chart_id: str, mcp_key: str, date_from: str, date_to: str) -> bool:
    print(f"\n{'='*60}")
    print("R2 PROOF: gochara_forecast_get (marriage domain)")
    print(f"  chart_id  : {chart_id}")
    print(f"  date_range: {date_from} → {date_to}")
    print(f"{'='*60}")

    result = mcp_call("gochara_forecast_get", {
        "chart_id": chart_id,
        "domain": "marriage",
        "date_from": date_from,
        "date_to": date_to,
    }, mcp_key)

    print("\nRaw result (trimmed):")
    print(json.dumps(result, indent=2)[:3000])

    # --- Assertions ---
    passed = True
    checks: list[tuple[str, bool, str]] = []

    # Check coverage non-empty (R1 fix still holding)
    coverage = result.get("coverage", {}) if isinstance(result, dict) else {}
    ec = coverage.get("event_classes_covered", []) if isinstance(coverage, dict) else []
    checks.append(("R1-STILL-HOLDS: event_classes_covered non-empty", bool(ec), str(ec[:3])))

    # Core R2 assertion: marriage rows must appear in roots (not just legacy_flat)
    nested = result.get("nested_hierarchy", {}) if isinstance(result, dict) else {}
    roots = nested.get("roots", []) if isinstance(nested, dict) else []

    # Look for marriage-class row with resolution='era' in roots
    marriage_root = None
    for row in roots:
        ec_val = row.get("event_class", "") or ""
        if "marriage" in ec_val.lower():
            marriage_root = row
            break

    checks.append((
        "R2-CORE: marriage row in nested_hierarchy.roots",
        marriage_root is not None,
        f"found: {json.dumps(marriage_root, default=str)[:300]}" if marriage_root else "NOT FOUND — check legacy_flat",
    ))

    if marriage_root:
        res = marriage_root.get("resolution")
        checks.append(("R2-CORE: resolution='era'", res == "era", f"resolution={res!r}"))

        itw = marriage_root.get("is_timing_window")
        checks.append(("R2-CORE: is_timing_window=true", itw is True, f"is_timing_window={itw!r}"))

    # Legacy_flat should NOT contain marriage rows (they moved to roots)
    legacy = nested.get("legacy_flat", []) if isinstance(nested, dict) else []
    marriage_legacy = [r for r in legacy if "marriage" in (r.get("event_class", "") or "").lower()]
    checks.append((
        "R2-CORE: marriage row NOT in legacy_flat",
        len(marriage_legacy) == 0,
        f"legacy_flat marriage rows: {len(marriage_legacy)}",
    ))

    for label, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}")
        print(f"         {detail}")
        if not ok:
            passed = False

    return passed


# ---------------------------------------------------------------------------
# R4 proof — kala_ahead_get (G-P4 gate)
# ---------------------------------------------------------------------------

def run_r4_proof(chart_id: str, mcp_key: str) -> bool:
    print(f"\n{'='*60}")
    print("R4 PROOF: kala_ahead_get (G-P4 / γ residual)")
    print(f"  chart_id: {chart_id}")
    print(f"{'='*60}")

    result = mcp_call("kala_ahead_get", {"chart_id": chart_id}, mcp_key)

    print("\nRaw result (trimmed):")
    print(json.dumps(result, indent=2)[:3000])

    passed = True
    checks: list[tuple[str, bool, str]] = []

    # Core R4 assertion: field_snapshot_id must be a real kfs_* ID
    fsi = result.get("field_snapshot_id", "") if isinstance(result, dict) else ""
    is_real = isinstance(fsi, str) and fsi.startswith("kfs_")
    checks.append((
        "R4-CORE: field_snapshot_id starts with 'kfs_'",
        is_real,
        f"field_snapshot_id={fsi!r}",
    ))
    is_not_placeholder = fsi != "field_not_yet_built"
    checks.append((
        "R4-CORE: field_snapshot_id != 'field_not_yet_built'",
        is_not_placeholder,
        f"value={fsi!r}",
    ))

    # Prospective rows must exist (proves field is built + kala_ahead populated)
    windows = result.get("windows", []) if isinstance(result, dict) else []
    checks.append((
        "R4-CORE: windows non-empty (field built)",
        len(windows) > 0,
        f"windows count: {len(windows)}",
    ))

    if windows:
        first = windows[0]
        wid = first.get("window_id", "")
        auth = first.get("authority_basis", first.get("authority", ""))
        checks.append((
            "R4-CORE: first window has window_id",
            bool(wid),
            f"window_id={wid!r} authority_basis={auth!r}",
        ))

    # A5 agreement facet (explain field)
    a5 = result.get("a5_agreement") or result.get("explain", {})
    checks.append((
        "R4-CORE: A5 agreement facet present (explain or a5_agreement)",
        bool(a5),
        f"a5/explain present: {bool(a5)}",
    ))

    for label, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}")
        print(f"         {detail}")
        if not ok:
            passed = False

    return passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if not args.mcp_key:
        print("ERROR: --mcp-key required (or set MARSYS_MCP_KEY env var)", file=sys.stderr)
        sys.exit(2)

    if args.chart_id != CANONICAL_CHART_ID:
        print(f"WARNING: chart_id {args.chart_id!r} differs from canonical {CANONICAL_CHART_ID!r}")

    results: list[bool] = []

    run_r2 = not args.r4_only
    run_r4 = not args.r2_only

    if run_r2:
        results.append(run_r2_proof(args.chart_id, args.mcp_key, args.r2_date_from, args.r2_date_to))
    if run_r4:
        results.append(run_r4_proof(args.chart_id, args.mcp_key))

    print(f"\n{'='*60}")
    overall = all(results)
    verdict = "PASS" if overall else "FAIL"
    print(f"OVERALL VERDICT: {verdict}")
    print(f"  Probes run: R2={'YES' if run_r2 else 'SKIP'} R4={'YES' if run_r4 else 'SKIP'}")
    print(f"{'='*60}")

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
