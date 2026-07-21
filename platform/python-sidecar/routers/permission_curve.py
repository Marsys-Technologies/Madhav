"""
routers/permission_curve.py — D-4b permission-bridge lane (wave/D-4b/permission-bridge).

Mounted at /api/compute (see main.py). Exposes ONE new, read-only,
curve-servable HTTP route around the ALREADY-EXISTING
`services.gochara_intensity.permission.compute_permission()` (D-5 Lane
G-3). This module does NOT modify `compute_permission`'s internal
computation in any way — it only imports it and calls it repeatedly across
a date range, exactly the pattern `gochara_intensity.engine.
compute_lambda_e_series` already uses for the full lambda_e pipeline (see
that module's own comment: "Resolves targets/dasha_periods ONCE ... rather
than per-point").

Why this route exists (BRIEF_D4B.md §1 B-1; B1_BAKEOFF_STATUS_v1_0.md §3,
§6 "Recommendation"): B-1's Grand Bakeoff names "the 12 D-5 PERMISSION
system-generators, standalone ... run as if each were the SOLE timing
signal" as 12 of its contenders. `compute_permission()` itself only
returns ONE point-in-time `(permission, detail)` pair; `detail["systems"]`
is the per-system decomposition (12 entries: `system_id`, `active`,
`weight`, `detail`) already computed on every call — this route is the
thinnest possible wrap of that EXISTING decomposition into a
`curve(chart, event_class, [t1, t2])`-shaped series, so the
`model_interface.ts` a3_scoring_harness bridge (a3_scoring_harness/
model_interface.ts, this same lane) has something real to call over HTTP.

A system's per-point "intensity" here is its OWN `active` boolean from
`compute_permission`'s decomposition, taken as 1.0/0.0 — never re-weighted,
re-derived, or blended with the other 11 systems' contributions. This is
the honest "as if this system alone were the SOLE timing signal" reading
BRIEF_D4B asks for: `compute_permission`'s own SYSTEM_WEIGHTS blending
happens ONLY in its returned scalar `permission`, which this route also
reports per-point (as `combined_permission`) for reference, but which no
standalone-system TemporalCurveModel adapter should read.

Read-only: no write to any table, no change to `permission.py`,
`ka_gochara_sweep`, `gochara_grammar`, or any other must_not_touch module.
CR-87 discipline preserved: `chart_id` is a required body field, never
defaulted.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
import swisseph as swe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar import resonance_map as RM
from services.gochara_intensity.enrichment import enrich_targets
from services.gochara_intensity.permission import (
    DASHA_SYSTEM_IDS,
    SYSTEM_WEIGHTS,
    compute_permission,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Same live DSN convention as routers/sutravali.py / routers/transit_search.py
# (env override, hard-coded local-proxy fallback for dev).
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis",
)

# The 12 PERMISSION system_ids this route can serve a curve for, in the
# same order compute_permission's own `detail["systems"]` emits them
# (8 DASHA_SYSTEM_IDS, then sade_sati, guru_shani_double_transit,
# av_threshold, planetary_return) — confirmed live against
# services/gochara_intensity/permission.py, not re-declared independently.
PERMISSION_SYSTEM_IDS: tuple[str, ...] = tuple(DASHA_SYSTEM_IDS) + (
    "sade_sati",
    "guru_shani_double_transit",
    "av_threshold",
    "planetary_return",
)
assert set(PERMISSION_SYSTEM_IDS) == set(SYSTEM_WEIGHTS.keys()), (
    "permission_curve.py's PERMISSION_SYSTEM_IDS has drifted from permission.py's live "
    "SYSTEM_WEIGHTS keys — this route must always name exactly the 12 generators "
    "compute_permission() actually decomposes, never a stale copy."
)
assert len(PERMISSION_SYSTEM_IDS) == 12


def _to_jd(t: datetime) -> float:
    t_utc = t.astimezone(timezone.utc) if t.tzinfo else t.replace(tzinfo=timezone.utc)
    return swe.julday(
        t_utc.year, t_utc.month, t_utc.day,
        t_utc.hour + t_utc.minute / 60.0 + t_utc.second / 3600.0,
    )


def _get_conn():
    return psycopg.connect(DB_URL, row_factory=psycopg.rows.dict_row)


class PermissionCurveRequest(BaseModel):
    chart_id: str = Field(..., min_length=1, description="REQUIRED — CR-87, never defaulted")
    event_class: str = Field(..., min_length=1, description="A-2 event-class id (e.g. 'marriage', 'major_gain')")
    t_start: datetime
    t_end: datetime
    step_days: float = Field(5.0, gt=0, le=90, description="Sampling step; matches curve.ts's own 5-day default")
    window_days: float = Field(15.0, gt=0, le=90, description="compute_permission's own +/- search window for the point-primitive-sourced generators")
    ayanamsha_id: str = "lahiri_chitrapaksha"
    system_ids: Optional[list[str]] = Field(
        None,
        description="Optional filter: only include these PERMISSION system_ids in the response "
                    "`systems` map (compute_permission always evaluates all 12 internally per "
                    "point regardless — this only trims the JSON payload). Omit for all 12.",
    )


@router.post("/permission_curve")
def post_permission_curve(req: PermissionCurveRequest) -> dict[str, Any]:
    if req.t_end < req.t_start:
        raise HTTPException(status_code=400, detail="t_end must be >= t_start")

    wanted_systems = set(req.system_ids) if req.system_ids else None
    if wanted_systems is not None:
        unknown = wanted_systems - set(PERMISSION_SYSTEM_IDS)
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"unknown system_ids requested: {sorted(unknown)}; valid ids are {list(PERMISSION_SYSTEM_IDS)}",
            )

    conn = None
    try:
        try:
            conn = _get_conn()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"permission_curve: DB unavailable — {exc}") from exc

        raw_targets = RM.fetch_resonance_targets(conn, req.chart_id, req.event_class)
        targets = enrich_targets(conn, raw_targets, ayanamsha_id=req.ayanamsha_id)
        dasha_periods = DD.fetch_dasha_periods(
            conn, req.chart_id, ayanamsha_id=req.ayanamsha_id, systems=list(DASHA_SYSTEM_IDS)
        )

        t_start_jd = _to_jd(req.t_start)
        t_end_jd = _to_jd(req.t_end)

        systems_out: dict[str, list[dict[str, Any]]] = {
            sid: [] for sid in PERMISSION_SYSTEM_IDS if wanted_systems is None or sid in wanted_systems
        }
        combined_points: list[dict[str, Any]] = []

        t_jd = t_start_jd
        points_computed = 0
        while t_jd <= t_end_jd:
            permission, detail = compute_permission(
                swe, conn, req.chart_id, req.event_class, targets, t_jd,
                dasha_periods=dasha_periods, window_days=req.window_days,
                ayanamsha_id=req.ayanamsha_id,
            )
            t_iso = detail["t_datetime_ist"]
            for s in detail["systems"]:
                sid = s["system_id"]
                if sid not in systems_out:
                    continue
                systems_out[sid].append({
                    "t_jd": t_jd,
                    "t_datetime_ist": t_iso,
                    "active": bool(s["active"]),
                    "intensity": 1.0 if s["active"] else 0.0,
                    "weight": s["weight"],
                })
            combined_points.append({
                "t_jd": t_jd, "t_datetime_ist": t_iso, "combined_permission": permission,
                "system_count_active": detail["system_count_active"],
            })
            points_computed += 1
            t_jd += req.step_days

        notes: list[str] = []
        if not targets:
            notes.append(
                "no gochara_resonance_map targets resolved for this chart/event_class — every "
                "point's per-system 'active' flag reflects compute_permission's own honest degrade "
                "for zero targets (dasha systems fall back to the coarser 'any period covering t' "
                "check per permission.py's own lord_relevance_check discipline; the four "
                "geometry-sourced generators cannot fire without at least one target and will read "
                "inactive throughout)."
            )

        return {
            "chart_id": req.chart_id,
            "event_class": req.event_class,
            "ayanamsha_id": req.ayanamsha_id,
            "t_start": req.t_start.isoformat(),
            "t_end": req.t_end.isoformat(),
            "step_days": req.step_days,
            "window_days": req.window_days,
            "points_computed": points_computed,
            "target_count": len(targets),
            "system_ids": list(systems_out.keys()),
            "systems": systems_out,
            "combined_permission_series": combined_points,
            "calibration_state": "structural_prior",
            "notes": notes,
            "source": "live",
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 -- loud, never a silent empty curve (B.10 / model_interface.ts's own NotImplementedModelError discipline)
        logger.exception("[permission_curve] failed for chart_id=%s event_class=%s", req.chart_id, req.event_class)
        raise HTTPException(status_code=500, detail=f"permission_curve failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


__all__ = ["router", "PERMISSION_SYSTEM_IDS"]
