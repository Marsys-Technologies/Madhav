"""
W2G V1 — the v1-sweep cost profile, and whether a PHASE SPLIT of it exists.

Design §6 V1: "profile split from the bulk-read lane (confirms what fraction
of residual cost 2.0 eliminates)."

Two distinct claims hide in that one line, and this validation keeps them
apart rather than letting the easier one stand in for the harder one:

  (a) WHAT THE v1 SWEEP COSTS, measured. Real and available now:
      `build_substep_progress` carries a `completed_at` per committed
      substep, so consecutive commits within one build give real wall-clock
      per-substep durations for `ka_gochara_sweep`.

  (b) HOW THAT COST SPLITS BY PHASE — position lookup / grammar primitive
      evaluation / composition / intensity integration / row assembly. This
      is the number design §6 V1 actually wants, because it is the number
      that says what fraction 2.0's spline substrate eliminates. It requires
      per-phase instrumentation.

If (b) has no substrate, V1 is INDETERMINATE — it does NOT report (a) and
call the split done. That substitution (a proxy standing in for the claim)
is precisely the defect class CLAUDE.md §N.8 names.

MEASUREMENT HONESTY for (a): `completed_at` deltas measure INTER-COMMIT
intervals, not pure compute. They include orchestrator overhead, and a delta
spanning two separate dispatches (a build that stopped overnight and
resumed) is a wall-clock gap, not a substep cost. Such deltas are excluded
by a stated threshold and the exclusion is REPORTED — never silently
dropped, and never averaged in to make the number look better or worse.
"""
from __future__ import annotations

import statistics
from datetime import datetime
from typing import Any

from ._db import QueryFn, table_exists
from .types import INDETERMINATE, PASS, ValidationResult

V1_ASSET_ID = "ka_gochara_sweep"
PROGRESS_TABLE = "build_substep_progress"

# A delta wider than this is treated as a DISPATCH GAP (the build was not
# running), not as one substep's cost. Stated, not hidden; every excluded
# delta is counted and its total reported.
DISPATCH_GAP_SECONDS = 3600.0

# Column names that would indicate real per-phase timing instrumentation.
# The detector looks for the SUBSTANCE, not for a table by name.
_PHASE_TIMING_COLUMN_HINTS = (
    "phase_seconds",
    "phase_timings",
    "profile_json",
    "phase_profile",
    "timing_breakdown",
)


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _detect_phase_profile_source(query: QueryFn) -> dict[str, Any]:
    """Real detector for claim (b): does ANY table carry per-phase timing
    for the sweep? Returns the evidence, empty when there is none."""
    rows = query(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND column_name = ANY(%s) "
        "ORDER BY table_name, column_name",
        [list(_PHASE_TIMING_COLUMN_HINTS)],
    )
    return {
        "columns_searched": list(_PHASE_TIMING_COLUMN_HINTS),
        "matches": [{"table": r["table_name"], "column": r["column_name"]} for r in rows],
    }


def _substep_durations(
    query: QueryFn, chart_id: str, gap_seconds: float
) -> dict[str, Any]:
    rows = query(
        f"SELECT substep_key, build_fingerprint, rows_written, completed_at "
        f"FROM {PROGRESS_TABLE} WHERE asset_id = %s AND chart_id = %s "
        f"ORDER BY build_fingerprint, completed_at",
        [V1_ASSET_ID, chart_id],
    )
    if not rows:
        return {"n_substeps": 0, "deltas": [], "excluded": [], "rows_written": 0}

    deltas: list[float] = []
    excluded: list[dict[str, Any]] = []
    prev_fp = None
    prev_t: datetime | None = None
    for r in rows:
        t = _as_dt(r["completed_at"])
        fp = r["build_fingerprint"]
        if prev_t is not None and fp == prev_fp and t is not None:
            delta = (t - prev_t).total_seconds()
            if delta > gap_seconds:
                excluded.append(
                    {
                        "substep_key": r["substep_key"],
                        "delta_seconds": delta,
                        "reason": "exceeds_dispatch_gap_threshold",
                    }
                )
            elif delta >= 0:
                deltas.append(delta)
        prev_fp, prev_t = fp, t

    return {
        "n_substeps": len(rows),
        "deltas": deltas,
        "excluded": excluded,
        "rows_written": sum(int(r["rows_written"] or 0) for r in rows),
        "n_fingerprints": len({r["build_fingerprint"] for r in rows}),
    }


def _stats(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        return {"n": 0}
    ordered = sorted(deltas)
    return {
        "n": len(ordered),
        "min_seconds": round(ordered[0], 3),
        "median_seconds": round(statistics.median(ordered), 3),
        "mean_seconds": round(statistics.fmean(ordered), 3),
        "p90_seconds": round(ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))], 3),
        "max_seconds": round(ordered[-1], 3),
        "measured_total_seconds": round(sum(ordered), 3),
    }


def validate_v1_profile_split(
    query: QueryFn,
    chart_ids: list[str],
    gap_seconds: float = DISPATCH_GAP_SECONDS,
) -> ValidationResult:
    title = (
        "V1 — v1 sweep cost profile, and whether a per-PHASE split exists "
        "(the fraction 2.0 eliminates)"
    )

    if not table_exists(query, PROGRESS_TABLE):
        return ValidationResult(
            validation_id="V1",
            title=title,
            status=INDETERMINATE,
            summary=f"`{PROGRESS_TABLE}` is not present in this database.",
            reason=(
                f"neither the aggregate cost nor its phase split is measurable — "
                f"`{PROGRESS_TABLE}` (the substep-commit ledger) does not exist."
            ),
        )

    phase_source = _detect_phase_profile_source(query)

    per_chart: dict[str, Any] = {}
    for chart_id in chart_ids:
        raw = _substep_durations(query, chart_id, gap_seconds)
        st = _stats(raw["deltas"])
        excluded = raw["excluded"]
        per_chart[chart_id] = {
            "n_substeps_committed": raw["n_substeps"],
            "n_build_fingerprints": raw.get("n_fingerprints", 0),
            "rows_written_total": raw["rows_written"],
            "substep_wall_clock": st,
            "excluded_deltas": {
                "n": len(excluded),
                "threshold_seconds": gap_seconds,
                "total_seconds": round(sum(e["delta_seconds"] for e in excluded), 3),
                "samples": excluded[:10],
                "note": (
                    "inter-commit gaps wider than the threshold — treated as dispatch "
                    "gaps (build not running), reported not discarded"
                ),
            },
        }
        if st.get("n"):
            per_chart[chart_id]["projected_full_horizon_seconds"] = round(
                st["median_seconds"] * raw["n_substeps"], 1
            )

    findings: list[str] = []
    measured_charts = [c for c, v in per_chart.items() if v["substep_wall_clock"].get("n")]

    if not measured_charts:
        findings.append(
            f"No `{PROGRESS_TABLE}` rows for asset_id={V1_ASSET_ID!r} on any requested chart — "
            "the v1 sweep's own cost is unmeasured on this database."
        )

    findings.append(
        "Measured durations are INTER-COMMIT wall clock (substep compute + orchestrator "
        "commit overhead), not isolated compute time. They bound v1's cost from above; "
        "they do not attribute it."
    )

    if not phase_source["matches"]:
        return ValidationResult(
            validation_id="V1",
            title=title,
            status=INDETERMINATE,
            summary=(
                "v1 aggregate cost IS measured from the substep-commit ledger, but NO "
                "per-phase timing instrumentation exists anywhere in the schema, so the "
                "SPLIT design §6 V1 asks for cannot be computed."
            ),
            data={
                "asset_id": V1_ASSET_ID,
                "aggregate_cost_measured": bool(measured_charts),
                "per_chart": per_chart,
                "phase_profile_source": phase_source,
            },
            findings=findings
            + [
                "BLOCKING FOR THE V1 CLAIM: no table carries per-phase timings "
                f"(searched for columns {list(_PHASE_TIMING_COLUMN_HINTS)}). The "
                "'fraction of residual cost 2.0 eliminates' is therefore UNKNOWN, not "
                "small and not large. Producing it requires instrumenting the v1 sweep "
                "path (position lookup vs grammar vs composition vs intensity) and one "
                "profiled re-run — it cannot be recovered from the existing ledger.",
                "The measured aggregate below is still the right BASELINE for the 2.0 "
                "'minutes per chart' target (design §1.1) and should be recorded as such.",
            ],
            reason=(
                "no per-phase timing substrate exists; only aggregate inter-commit wall "
                "clock is recoverable, and an aggregate is not a split"
            ),
        )

    return ValidationResult(
        validation_id="V1",
        title=title,
        status=PASS,
        summary=(
            f"Per-phase timing instrumentation found ({len(phase_source['matches'])} column(s)); "
            "aggregate v1 cost measured alongside it."
        ),
        data={
            "asset_id": V1_ASSET_ID,
            "aggregate_cost_measured": bool(measured_charts),
            "per_chart": per_chart,
            "phase_profile_source": phase_source,
        },
        findings=findings,
    )


__all__ = ["validate_v1_profile_split", "V1_ASSET_ID", "DISPATCH_GAP_SECONDS"]
