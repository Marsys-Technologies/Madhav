"""
w2g_validations.runner — run V1–V6 and assemble the bind-time report.

CALLED AT BIND TIME BY THE 2.0 WRITER (design §6 names these "bind-time
validations"), and runnable standalone as a diagnostic
(`scripts/run_w2g_bind_validations.py`).

BIND SEMANTICS. `bind_gate(report)` answers the one question the writer
actually needs: may the 2.0 writer proceed? A FAIL blocks; an INDETERMINATE
blocks too, because "we could not check" is not "it is fine" — that
equivalence is the defect §N.8 names. The gate returns the blocking ids so
the caller reports WHICH claim stopped it, never a bare boolean.

CHART SCOPE follows ADJUDICATION-4's tiering: Tier 1 is the two canonical
charts together, never separately.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ._db import QueryFn
from .types import FAIL, INDETERMINATE, PASS, WAVE_ID, ValidationResult
from .v1_profile_split import validate_v1_profile_split
from .v2_ephemeris_coverage import NOMINAL_EPOCH_START, REQUIRED_END, validate_v2_ephemeris_coverage
from .v3_spline_accuracy import validate_v3_spline_accuracy
from .v4_transition_sizing import validate_v4_transition_sizing
from .v5_corpus_readiness import validate_v5_corpus_readiness
from .v6_divergence_pilot import validate_v6_divergence_pilot

# ADJUDICATION-4 Tier 1 — "together, never separately".
TIER1_CHART_IDS = [
    "482012f1-710e-4a25-994a-93821f5871aa",  # Abhisek Mohanty (canonical)
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",  # Abhinandan Mohanty (canonical)
]
# ADJUDICATION-4 Tier 2 — the only third chart with a v1 corpus.
TIER2_CHART_IDS = ["cb73cd3d-9eba-4220-9902-0de91566e980"]

# Design §3.3 names 2013 (the marriage double-transit specimen year) as a
# specimen-continuity year, which makes it the most informative single
# materialized year for the V6 pilot.
DEFAULT_PILOT_YEAR = 2013


def run_all(
    query: QueryFn,
    tier1_chart_ids: list[str] | None = None,
    tier2_chart_ids: list[str] | None = None,
    pilot_year: int = DEFAULT_PILOT_YEAR,
) -> dict[str, Any]:
    tier1 = list(tier1_chart_ids or TIER1_CHART_IDS)
    tier2 = list(tier2_chart_ids or TIER2_CHART_IDS)
    all_charts = tier1 + tier2

    v2 = validate_v2_ephemeris_coverage(query)
    # V4 is sized over the epoch V2 MEASURED, never over an assumed one —
    # ADJUDICATION-5's "the epoch is derived from live coverage".
    epoch_start = (
        date.fromisoformat(v2.data["calendar_epoch_start"])
        if v2.data.get("calendar_epoch_start")
        else NOMINAL_EPOCH_START
    )
    epoch_end_measured = v2.data.get("calendar_epoch_end")
    epoch_end = min(
        date.fromisoformat(epoch_end_measured) if epoch_end_measured else REQUIRED_END,
        REQUIRED_END,
    )

    results: list[ValidationResult] = [
        validate_v1_profile_split(query, all_charts),
        v2,
        validate_v3_spline_accuracy(query),
        validate_v4_transition_sizing(query, all_charts, epoch_start, epoch_end),
        validate_v5_corpus_readiness(query, tier1, tier2),
        validate_v6_divergence_pilot(query, tier1, pilot_year),
    ]

    by_status = {PASS: [], FAIL: [], INDETERMINATE: []}
    for r in results:
        by_status[r.status].append(r.validation_id)

    return {
        "wave": WAVE_ID,
        "epoch_used_for_sizing": [epoch_start.isoformat(), epoch_end.isoformat()],
        "tier1_chart_ids": tier1,
        "tier2_chart_ids": tier2,
        "pilot_year": pilot_year,
        "results": [r.to_dict() for r in results],
        "summary": {
            "pass": by_status[PASS],
            "fail": by_status[FAIL],
            "indeterminate": by_status[INDETERMINATE],
            "n_findings": sum(len(r.findings) for r in results),
        },
    }


def bind_gate(report: dict[str, Any]) -> dict[str, Any]:
    """May the 2.0 writer proceed?

    Blocks on FAIL *and* on INDETERMINATE. An unmeasured claim is not a
    satisfied one.
    """
    blocking = list(report["summary"]["fail"]) + list(report["summary"]["indeterminate"])
    return {
        "may_proceed": not blocking,
        "blocking_validation_ids": blocking,
        "blocked_by_fail": list(report["summary"]["fail"]),
        "blocked_by_indeterminate": list(report["summary"]["indeterminate"]),
    }


__all__ = [
    "run_all",
    "bind_gate",
    "TIER1_CHART_IDS",
    "TIER2_CHART_IDS",
    "DEFAULT_PILOT_YEAR",
]
