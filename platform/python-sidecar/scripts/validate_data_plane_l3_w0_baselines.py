"""Emit reproducible, source-local L3 W0 Kshetra baseline measurements.

The harness deliberately uses the strict in-memory connection from the maintained
writer tests. It performs no network, filesystem write or database I/O; its
backend context performs bounded file-existence metadata checks and, only when a
file-backed path resolves, reads the selected ephemeris file to identify it by
digest. It must never be represented as production or PostgreSQL performance
evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
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


def _transit_ephemeris_context() -> dict[str, Any]:
    """Record which Swiss backend actually serves the transit benchmark host."""
    import swisseph as swe

    from panchang_engine.swiss_state import swiss_state_scope
    from pipeline import transit_search as transit

    resolved = transit._resolved_ephemeris_path()
    candidates = (
        os.environ.get("SWE_EPHE_PATH"),
        os.environ.get("SWISSEPH_EPHE_PATH"),
        "/app/ephe",
        "/tmp/se1",
    )
    candidate_files = []
    for candidate in candidates:
        if candidate:
            file_path = Path(candidate) / "sepl_18.se1"
            exists = file_path.is_file()
            record = {"path": str(file_path), "exists": exists}
            if (
                exists
                and resolved is not None
                and file_path.parent.resolve() == Path(resolved).resolve()
            ):
                with file_path.open("rb") as ephemeris_file:
                    record["sha256"] = hashlib.file_digest(
                        ephemeris_file, "sha256"
                    ).hexdigest()
                record["bytes"] = file_path.stat().st_size
            candidate_files.append(record)

    input_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    with swiss_state_scope():
        swe.set_ephe_path(resolved)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        _, returned_flags = swe.calc_ut(
            swe.julday(2024, 1, 1), swe.SATURN, input_flags
        )
    if returned_flags & swe.FLG_MOSEPH:
        backend = "Moshier fallback"
    elif returned_flags & swe.FLG_SWIEPH:
        backend = "Swiss .se1 files"
    elif returned_flags & swe.FLG_JPLEPH:
        backend = "JPL ephemeris"
    else:
        backend = "unclassified"

    return {
        "pyswisseph_version": getattr(swe, "version", None),
        "module_file": getattr(swe, "__file__", None),
        "resolved_ephemeris_path": resolved,
        "candidate_files": candidate_files,
        "input_flags": input_flags,
        "input_flag_names": ["FLG_SIDEREAL", "FLG_SPEED"],
        "effective_return_flags": returned_flags,
        "backend": backend,
        "sidereal_mode": "SIDM_LAHIRI",
        "node_mode": "TRUE_NODE; Ketu derived as Rahu + 180 degrees",
    }


def _numeric_summaries(runs: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    summaries = {}
    for field in ("wall_seconds", "cpu_seconds", "planning_wall_seconds"):
        values = [float(run[field]) for run in runs]
        summaries[field] = {
            "median": round(statistics.median(values), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
        }
    return summaries


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

    runs = [_one_run(run) for run in range(1, args.repeats + 1)]
    payload = {
        "contract": "MADHAV_DATA_PLANE_L3_W0_KSHETRA_BASELINE_v1",
        "scope": "source-local strict in-memory fake; no PostgreSQL or storage I/O",
        "transit_ephemeris_context": _transit_ephemeris_context(),
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
        "runs": runs,
        "numeric_summaries": _numeric_summaries(runs),
    }
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
