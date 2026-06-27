"""
Per-chart birth-parameter provider (Orchestrator Convergence Phase 3B — writer
generalization; B1 elimination pass).

Every chart (native 482012f1 included) reads birth params from public.charts.
There is no NATIVE_BIRTH constant to fall back to and no CANONICAL_CHART_ID
special case. Contamination becomes structurally impossible.

Design:
- Any chart → fetched from public.charts, matched on `id` OR `chart_id`
  (both unique uuids — robust to which column the orchestrator's chart_id maps to).
  tz_offset_hours is derived from the chart's IANA `timezone_id` at the birth instant.
- Chart row absent → raises ValueError; insert birth data into public.charts first.
- A row missing the data needed for a CORRECT chart (date/time/lat/lng/timezone)
  raises — a loud halt is safer than silently building a wrong chart.
- resolve_birth_params(): if birth_params already truthy, return as-is (orchestrator
  already pre-fetched). If falsy, raises ValueError for ANY chart — the native is no
  longer exempt. Callers must pass real birth_params from fetch_birth_params().
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Canonical native chart ID — exported for writers that use it for FORENSIC-gating
# (e.g. asserting native-specific anchors only on the native chart). NOT used for
# birth-param routing — every chart (native included) now fetches from public.charts.
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

_REQUIRED = ("birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id")


def fetch_birth_params(conn: Any, chart_id: str) -> dict[str, Any]:
    """Return a birth-params dict for chart_id fetched from public.charts.

    Raises ValueError when the charts row is absent or lacks data required to
    build a correct chart. The native (482012f1) is treated exactly like any
    other chart — no special case, no hardcoded fallback.
    """
    from psycopg.rows import dict_row  # psycopg v3 — always available

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT birth_date, birth_time, birth_lat, birth_lng, birth_place,
                   timezone_id, COALESCE(subject_name, preferred_name, name) AS label
            FROM public.charts
            WHERE id = %s OR chart_id = %s
            LIMIT 1
            """,
            [chart_id, chart_id],
        )
        row = cur.fetchone()

    if not row:
        raise ValueError(
            f"[fetch_birth_params] no charts row found for chart_id={chart_id}; "
            "insert birth data into public.charts before building"
        )

    missing = [k for k in _REQUIRED if row.get(k) in (None, "")]
    if missing:
        raise ValueError(
            f"[birth_params] chart {chart_id} is missing required birth fields "
            f"{missing}; cannot build a correct chart. Populate public.charts first."
        )
    return _to_birth_params(row)


def resolve_birth_params(chart_id: str, birth_params) -> dict:
    """Guard: return birth_params if truthy; raise for any chart with falsy params.

    - birth_params is truthy (non-None, non-empty dict) → return as-is.
    - birth_params is falsy → raise ValueError for ANY chart (native included).

    Writers must call this at the top of their run(). The orchestrator always
    pre-fetches from public.charts via fetch_birth_params() and passes the result
    in ctx.config['birth_params']. A falsy birth_params means the orchestrator
    failed to populate it — that is always a bug, never a legitimate fallback.
    """
    if birth_params:
        return birth_params
    raise ValueError(
        f"[resolve_birth_params] chart {chart_id} has no usable birth_params"
        " — orchestrator must populate ctx.config['birth_params'] from"
        " fetch_birth_params() before calling any writer"
    )


def _to_birth_params(row: dict[str, Any]) -> dict[str, Any]:
    from zoneinfo import ZoneInfo

    birth_dt = datetime.combine(row["birth_date"], row["birth_time"])
    tzid = row["timezone_id"]
    try:
        offset = ZoneInfo(tzid).utcoffset(birth_dt)
    except Exception as exc:  # unknown/invalid IANA zone
        raise ValueError(f"[birth_params] unknown timezone_id {tzid!r}: {exc}") from exc
    if offset is None:
        raise ValueError(f"[birth_params] could not resolve UTC offset for timezone_id {tzid!r}")

    return {
        "datetime_iso": birth_dt.isoformat(timespec="seconds"),
        "latitude_deg": float(row["birth_lat"]),
        "longitude_deg": float(row["birth_lng"]),
        "tz_offset_hours": offset.total_seconds() / 3600.0,
        "place_name": row.get("birth_place") or "",
        "subject_label": row.get("label") or "",
    }
