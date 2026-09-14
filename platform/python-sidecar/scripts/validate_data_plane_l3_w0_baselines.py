"""Emit reproducible, source-local L3 W0 Kshetra baseline measurements.

The harness deliberately uses the strict in-memory connection from the maintained
writer tests.  It performs no network, filesystem or database I/O and must never
be represented as production or PostgreSQL performance evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any


SIDECAR_ROOT = Path(__file__).resolve().parents[1]
if str(SIDECAR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIDECAR_ROOT))

from services.ka_kshetra import stage5_null as S5  # noqa: E402
from services.ka_kshetra import writer as W  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402


_FIXTURE_INPUT_TABLES = {
    "kala_field_kinematics",
    "kala_field_primitives",
    "kala_field_promise_nodes",
    "kala_field_promise_edges",
    "kala_field_routes",
    "kala_field_clocks",
    "kala_field_boundaries",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        default=str,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _statement_counts(statements: list[str]) -> dict[str, int]:
    counts = {"select": 0, "insert": 0, "delete": 0, "update": 0, "other": 0}
    for statement in statements:
        match = re.match(r"\s*(\w+)", statement)
        kind = match.group(1).lower() if match else "other"
        if kind in counts:
            counts[kind] += 1
        else:
            counts["other"] += 1
    return counts


def _one_run(run: int) -> dict[str, Any]:
    original_horizon = W.HORIZON_DAYS
    original_replicates = S5.DEFAULT_REPLICATES
    original_block_size = S5.DEFAULT_BLOCK_SIZE
    original_owned_tables = W._OWNED_TABLES
    module_names = (
        "services.ka_kshetra.stage0_kinematics",
        "services.ka_kshetra.stage1_symbolization",
        "services.ka_kshetra.stage2_promise",
        "services.ka_kshetra.stage3_clocks",
    )
    original_modules = {name: sys.modules.get(name) for name in module_names}
    module_present = {name: name in sys.modules for name in module_names}

    try:
        W.HORIZON_DAYS = 400.0
        S5.DEFAULT_REPLICATES = 8
        S5.DEFAULT_BLOCK_SIZE = 4
        W._OWNED_TABLES = tuple(
            item for item in W._OWNED_TABLES if item[0] not in _FIXTURE_INPUT_TABLES
        )
        for name in module_names:
            sys.modules[name] = None

        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()

        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        steps = writer.plan_substeps(ctx)
        planned_at = time.perf_counter()
        for step in steps:
            writer.run_substep(ctx, step)
        wall_seconds = time.perf_counter() - wall_started
        cpu_seconds = time.process_time() - cpu_started

        output_tables = tuple(dict.fromkeys((*W._HASHED_TABLES, "kala_field_snapshots")))
        row_counts = {table: len(conn.tables.get(table, [])) for table in output_tables}
        output = {table: conn.tables.get(table, []) for table in output_tables}
        encoded = _canonical_bytes(output)
        snapshots = conn.tables.get("kala_field_snapshots", [])

        return {
            "run": run,
            "wall_seconds": round(wall_seconds, 6),
            "cpu_seconds": round(cpu_seconds, 6),
            "planning_wall_seconds": round(planned_at - wall_started, 6),
            "threads": threading.active_count(),
            "plan_substeps": len(steps),
            "statement_counts": _statement_counts(conn.executed),
            "row_counts": row_counts,
            "total_output_rows": sum(row_counts.values()),
            "canonical_output_bytes": len(encoded),
            "canonical_output_sha256": hashlib.sha256(encoded).hexdigest(),
            "field_content_hash": (
                snapshots[0].get("field_content_hash") if snapshots else None
            ),
        }
    finally:
        W.HORIZON_DAYS = original_horizon
        S5.DEFAULT_REPLICATES = original_replicates
        S5.DEFAULT_BLOCK_SIZE = original_block_size
        W._OWNED_TABLES = original_owned_tables
        for name in module_names:
            if module_present[name]:
                sys.modules[name] = original_modules[name]
            else:
                sys.modules.pop(name, None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    payload = {
        "contract": "MADHAV_DATA_PLANE_L3_W0_KSHETRA_BASELINE_v1",
        "scope": "source-local strict in-memory fake; no PostgreSQL or storage I/O",
        "workload": {
            "chart_id": F.CHART_ID,
            "horizon_days": 400.0,
            "null_replicates": 8,
            "null_block_size": 4,
            "cache_state": "fresh process-local writer and fake connection per run",
            "thread_model": "single Python process; no worker threads requested",
        },
        "inapplicable": [
            "database SQL execution time",
            "database I/O",
            "WAL bytes",
            "durable storage bytes",
            "network time",
            "qualified live first-result latency",
        ],
        "runs": [_one_run(run) for run in range(1, args.repeats + 1)],
    }
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
