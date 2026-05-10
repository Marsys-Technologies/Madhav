"""
runner.py — eval-harness runner.

Loads fixtures.json, hits POST /api/chat/consume per fixture, scores each
result with scorer.py, prints a summary table and optionally writes a
structured JSON results file.

Usage:
    python3 platform/scripts/eval/runner.py [--planner-on|--planner-off]
        [--fixture-ids F001,F005,...] [--base-url http://localhost:3000]
        [--chart-id <uuid>] [--session-cookie <__session value>]
        [--output path/to/results.json]

Environment:
    SMOKE_CHART_ID         — chart UUID (or pass --chart-id)
    SMOKE_SESSION_COOKIE   — __session cookie value (or --session-cookie)
    ANTHROPIC_API_KEY      — needed for synthesis_score; otherwise 0.5 fallback
    MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED — set by --planner-on/off when local
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scorer import (  # noqa: E402  (path-adjusted import)
    keyword_recall_score,
    signal_recall_score,
    synthesis_score,
    weighted_score,
)

DEFAULT_FIXTURES = SCRIPT_DIR / "fixtures.json"
DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_TIMEOUT_S = 60

# AI SDK stream metadata patterns
QUERY_ID_RE = re.compile(r'"query[_]?[Ii]d"\s*:\s*"([0-9a-f-]{36})"')
PLANNER_ACTIVE_RE = re.compile(r'"planner_active"\s*:\s*(true|false)')
TOOLS_USED_RE = re.compile(r'"step_name"\s*:\s*"([a-z_]+)"[^}]*"status"\s*:\s*"done"')


def load_fixtures(path: Path, ids_filter: list[str] | None) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = data["fixtures"]
    if ids_filter:
        wanted = {x.strip() for x in ids_filter if x.strip()}
        fixtures = [f for f in fixtures if f["fixture_id"] in wanted]
    return fixtures


def build_request_body(query: str, chart_id: str) -> bytes:
    payload: dict = {
        "chartId": chart_id,
        "messages": [
            {
                "role": "user",
                "id": f"eval-msg-{int(time.time() * 1000)}",
                "parts": [{"type": "text", "text": query}],
            }
        ],
    }
    stack = os.environ.get("EVAL_STACK", "")
    if stack:
        payload["stack"] = stack
    return json.dumps(payload).encode("utf-8")


def call_consume(
    base_url: str,
    chart_id: str,
    session_cookie: str,
    query: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> tuple[str, int, float]:
    """Returns (raw_stream_text, http_status, latency_ms). Raises on transport error."""
    body = build_request_body(query, chart_id)
    req = urlrequest.Request(
        f"{base_url.rstrip('/')}/api/chat/consume",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"__session={session_cookie}" if session_cookie else "",
            "X-Eval-Session": "true",
        },
    )
    started = time.time()
    with urlrequest.urlopen(req, timeout=timeout_s) as resp:  # nosec B310
        status = resp.status
        raw = resp.read().decode("utf-8", errors="replace")
    latency_ms = (time.time() - started) * 1000.0
    return raw, status, latency_ms


def extract_response_text(raw_stream: str) -> str:
    """
    Handles two stream formats emitted by /api/chat/consume:

    1. SSE (Vercel AI UI message stream): lines prefixed `data: {...}`
       with `{"type":"text-delta","delta":"..."}` payload objects.
    2. AI SDK data stream: lines prefixed `0:"..."` or `0:{...}`.

    Tries SSE first (it's what production emits); falls back to the
    data-stream format. Returns raw body if neither yields text.
    """
    pieces: list[str] = []

    # ── 1. SSE format: data: {"type":"text-delta","delta":"..."} ──────────────
    for line in raw_stream.splitlines():
        line = line.strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            if obj.get("type") == "text-delta" and isinstance(obj.get("delta"), str):
                pieces.append(obj["delta"])
            elif isinstance(obj.get("text"), str):
                pieces.append(obj["text"])
            elif isinstance(obj.get("content"), str):
                pieces.append(obj["content"])
        elif isinstance(obj, str):
            pieces.append(obj)

    if pieces:
        return "".join(pieces).strip()

    # ── 2. AI SDK data stream: 0:"..." or 0:{...} ────────────────────────────
    for line in raw_stream.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) > 2 and line[0].isdigit() and line[1] == ":":
            try:
                value = json.loads(line[2:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, str):
                pieces.append(value)
            elif isinstance(value, dict) and isinstance(value.get("text"), str):
                pieces.append(value["text"])

    text = "".join(pieces).strip()
    return text if text else raw_stream


def parse_planner_active(raw_stream: str) -> bool | None:
    m = PLANNER_ACTIVE_RE.search(raw_stream)
    if not m:
        return None
    return m.group(1) == "true"


def parse_tools_used(raw_stream: str) -> list[str]:
    """
    Extract distinct successful tool step_names from emitted trace events.
    Excludes pipeline-stage non-tool steps (classify, compose_bundle, plan_per_tool, synthesis).
    """
    pipeline_steps = {"classify", "compose_bundle", "plan_per_tool", "synthesis", "context_assembly"}
    seen: list[str] = []
    for match in TOOLS_USED_RE.finditer(raw_stream):
        name = match.group(1)
        if name in pipeline_steps or name in seen:
            continue
        seen.append(name)
    return seen


def score_fixture(
    fixture: dict[str, Any],
    response_text: str,
    judge_enabled: bool,
    rubric: str = "jyotish",
    judge: str = "gemini",
) -> dict[str, float]:
    kw = keyword_recall_score(response_text, fixture)
    sig = signal_recall_score(response_text, fixture)
    syn = synthesis_score(response_text, fixture, rubric=rubric, judge=judge) if judge_enabled else 0.5
    weights = fixture.get("scoring_weights", {})
    wtd = weighted_score(kw, sig, syn, weights)
    return {
        "keyword_recall": round(kw, 4),
        "signal_recall": round(sig, 4),
        "synthesis": round(syn, 4),
        "weighted": round(wtd, 4),
    }


def run_one(
    fixture: dict[str, Any],
    base_url: str,
    chart_id: str,
    session_cookie: str,
    timeout_s: int,
    judge_enabled: bool,
    rubric: str = "jyotish",
    judge: str = "gemini",
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "fixture_id": fixture["fixture_id"],
        "type": fixture["type"],
        "status": "ok",
        "planner_active": None,
        "tools_used": [],
        "tool_count": 0,
        "scores": {"keyword_recall": 0.0, "signal_recall": 0.0, "synthesis": 0.0, "weighted": 0.0},
        "response_excerpt": "",
        "latency_ms": 0,
        "error": None,
    }
    try:
        raw, http_status, latency_ms = call_consume(
            base_url, chart_id, session_cookie, fixture["query"], timeout_s
        )
        record["latency_ms"] = round(latency_ms)
        if http_status != 200:
            record["status"] = "error"
            record["error"] = f"HTTP {http_status}"
            record["response_excerpt"] = raw[:200]
            return record
        response_text = extract_response_text(raw)
        record["response_excerpt"] = response_text[:200]
        record["planner_active"] = parse_planner_active(raw)
        record["tools_used"] = parse_tools_used(raw)
        record["tool_count"] = len(record["tools_used"])
        record["scores"] = score_fixture(fixture, response_text, judge_enabled, rubric=rubric, judge=judge)
    except urlerror.HTTPError as err:
        record["status"] = "error"
        try:
            body = err.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            body = ""
        record["error"] = f"HTTP {err.code}: {err.reason}"
        record["response_excerpt"] = body
    except urlerror.URLError as err:
        record["status"] = "error"
        record["error"] = f"URLError: {err.reason}"
    except (TimeoutError, OSError) as err:
        record["status"] = "timeout" if isinstance(err, TimeoutError) else "error"
        record["error"] = str(err)
    except Exception as err:  # noqa: BLE001 — runner must keep going
        record["status"] = "error"
        record["error"] = f"{type(err).__name__}: {err}"
    return record


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    ok_records = [r for r in records if r["status"] == "ok"]
    n = len(ok_records)
    if n == 0:
        return {
            "fixture_count": len(records),
            "ok_count": 0,
            "error_count": len(records),
            "keyword_recall": 0.0,
            "signal_recall": 0.0,
            "synthesis": 0.0,
            "weighted": 0.0,
        }
    return {
        "fixture_count": len(records),
        "ok_count": n,
        "error_count": len(records) - n,
        "keyword_recall": round(sum(r["scores"]["keyword_recall"] for r in ok_records) / n, 4),
        "signal_recall": round(sum(r["scores"]["signal_recall"] for r in ok_records) / n, 4),
        "synthesis": round(sum(r["scores"]["synthesis"] for r in ok_records) / n, 4),
        "weighted": round(sum(r["scores"]["weighted"] for r in ok_records) / n, 4),
    }


def print_summary(records: list[dict[str, Any]], agg: dict[str, Any]) -> None:
    print()
    print(f"{'Fixture':<8}{'Type':<14}{'KW':>6}{'Sig':>6}{'Syn':>6}{'Wtd':>6}  Status")
    print("─" * 60)
    for r in records:
        s = r["scores"]
        print(
            f"{r['fixture_id']:<8}{r['type']:<14}"
            f"{s['keyword_recall']:>6.2f}{s['signal_recall']:>6.2f}"
            f"{s['synthesis']:>6.2f}{s['weighted']:>6.2f}  {r['status']}"
        )
    print("─" * 60)
    print(
        f"{'AGGREGATE':<22}"
        f"{agg['keyword_recall']:>6.2f}{agg['signal_recall']:>6.2f}"
        f"{agg['synthesis']:>6.2f}{agg['weighted']:>6.2f}  "
        f"{agg['ok_count']}/{agg['fixture_count']} ok"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MARSYS-JIS eval-harness runner")
    flag = parser.add_mutually_exclusive_group()
    flag.add_argument("--planner-on", dest="planner_on", action="store_true")
    flag.add_argument("--planner-off", dest="planner_off", action="store_true")
    parser.add_argument("--fixture-ids", default="", help="Comma-separated subset (e.g. F001,F005)")
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--base-url", default=os.environ.get("EVAL_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--chart-id", default=os.environ.get("SMOKE_CHART_ID", ""))
    parser.add_argument("--session-cookie", default=os.environ.get("SMOKE_SESSION_COOKIE", ""))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--output", default="", help="If set, write full JSON results here")
    parser.add_argument("--no-judge", action="store_true", help="Skip judge calls")
    parser.add_argument("--judge", choices=["gemini", "anthropic", "none"],
                        default=os.environ.get("EVAL_JUDGE", "gemini"),
                        help="Judge provider (default: gemini)")
    # P3 D.3.1: pre-loop warm-up to absorb cold-start latency on the endpoint.
    warm_group = parser.add_mutually_exclusive_group()
    warm_group.add_argument("--warm-up", dest="warm_up", action="store_true", default=True,
                            help="(default) Send one trivial request and wait 3s before scoring loop")
    warm_group.add_argument("--no-warm-up", dest="warm_up", action="store_false",
                            help="Skip the pre-loop warm-up request")
    # P3 D.3.2: inter-fixture sleep to ease pressure on rate limits / dev server.
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds to sleep between fixtures (default: 2.0)")
    # P3 D.3.4: opt out of the new structured Jyotish rubric, restore old single-score behavior.
    parser.add_argument("--legacy-rubric", action="store_true",
                        help="Use pre-P3 single-score judge prompt instead of structured 4-axis rubric")
    args = parser.parse_args(argv)

    # Set planner env so a locally-spawned dev server picks it up. For an
    # already-running external server, the trace's planner_active is what we
    # actually trust at scoring time.
    if args.planner_on:
        os.environ["MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED"] = "true"
    elif args.planner_off:
        os.environ["MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED"] = "false"

    if not args.chart_id:
        print(
            "ERROR: --chart-id (or SMOKE_CHART_ID env) required. "
            "Get it via: SELECT id FROM charts LIMIT 1;",
            file=sys.stderr,
        )
        return 2

    ids_filter = [x.strip() for x in args.fixture_ids.split(",") if x.strip()] or None
    fixtures = load_fixtures(Path(args.fixtures), ids_filter)
    if not fixtures:
        print("ERROR: no fixtures matched filter", file=sys.stderr)
        return 2

    judge_enabled = not args.no_judge and args.judge != "none"
    rubric = "legacy" if args.legacy_rubric else "jyotish"
    judge_provider = args.judge

    if args.warm_up:
        warmup_query = "What is the ascendant of the chart?"
        try:
            call_consume(
                args.base_url, args.chart_id, args.session_cookie,
                warmup_query, min(args.timeout, 30),
            )
        except Exception as err:  # noqa: BLE001 — warmup is best-effort
            print(f"  warm-up request errored ({err}); continuing", file=sys.stderr)
        print("  warm-up complete; sleeping 3s before fixture #1")
        time.sleep(3)

    records: list[dict[str, Any]] = []
    for idx, fixture in enumerate(fixtures):
        if idx > 0 and args.delay > 0:
            time.sleep(args.delay)
        record = run_one(
            fixture, args.base_url, args.chart_id, args.session_cookie,
            args.timeout, judge_enabled, rubric=rubric, judge=judge_provider,
        )
        records.append(record)
        s = record["scores"]
        print(
            f"  {record['fixture_id']} {record['status']:<8} "
            f"kw={s['keyword_recall']:.2f} sig={s['signal_recall']:.2f} "
            f"syn={s['synthesis']:.2f} wtd={s['weighted']:.2f} "
            f"({record['latency_ms']}ms)"
        )

    agg = aggregate(records)
    plan_branch = (
        "on" if args.planner_on else ("off" if args.planner_off else "unspecified")
    )
    out = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "planner_branch": plan_branch,
        "judge_enabled": judge_enabled,
        "aggregate": agg,
        "results": records,
    }
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nResults written to: {args.output}")
    else:
        print()
        print(json.dumps(out, indent=2))

    print_summary(records, agg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
