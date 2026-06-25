"""
Per-chart birth-parameter provider (Orchestrator Convergence Phase 3B — writer
generalization).

The L1 Gaṇita writers were authored native-only: they default birth_params to the
native and carry native-specific FORENSIC anchors. To let the orchestrator drive a
build for ANY chart, the orchestrator must hand each writer that chart's real birth
data via ctx.config['birth_params']. This module fetches it from public.charts.

Design:
- Native chart → returns None. The native is the verified ground-truth chart; its
  writers keep their hard-coded NATIVE_BIRTH constant (zero risk of a charts-row
  rounding difference perturbing the FORENSIC-guarded native build).
- Any other chart → fetched from public.charts, matched on `id` OR `chart_id`
  (both unique uuids — robust to which column the orchestrator's chart_id maps to).
  tz_offset_hours is derived from the chart's IANA `timezone_id` at the birth instant.
- Chart row absent → None (writer falls back to NATIVE_BIRTH; a no-row build is a
  CLI/test path, not a real client).
- A non-native row missing the data needed for a CORRECT chart (date/time/lat/lng/
  timezone) raises — a loud halt is safer than silently building a wrong chart.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Verified ground-truth chart (Abhisek Mohanty). Kept in sync with the writers'
# CANONICAL_CHART_ID; the native build uses the writers' hard-coded NATIVE_BIRTH.
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

_REQUIRED = ("birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id")


def fetch_birth_params(conn: Any, chart_id: str) -> dict[str, Any] | None:
    """Return NATIVE_BIRTH-shaped birth params for chart_id, or None to signal the
    writer should use its hard-coded native default. Raises ValueError when a
    non-native chart row exists but lacks data required to build a correct chart."""
    if chart_id == CANONICAL_CHART_ID:
        return None

    row = conn.execute(
        """
        SELECT birth_date, birth_time, birth_lat, birth_lng, birth_place,
               timezone_id, COALESCE(subject_name, preferred_name, name) AS label
        FROM public.charts
        WHERE id = %s OR chart_id = %s
        LIMIT 1
        """,
        [chart_id, chart_id],
    ).fetchone()

    if not row:
        raise ValueError(
            f"[fetch_birth_params] no charts row found for non-native chart_id={chart_id}; "
            "insert birth data into public.charts before building"
        )

    missing = [k for k in _REQUIRED if row.get(k) in (None, "")]
    if missing:
        raise ValueError(
            f"[birth_params] chart {chart_id} is missing required birth fields "
            f"{missing}; cannot build a correct chart. Populate public.charts first."
        )
    return _to_birth_params(row)


def resolve_birth_params(chart_id: str, birth_params) -> dict | None:
    """3-way guard: raise for non-native charts with no birth_params.

    - birth_params is truthy (non-None, non-empty dict) → return as-is.
    - birth_params is falsy AND chart_id == CANONICAL_CHART_ID → return None
      (signal for writer to use its own hard-coded NATIVE_BIRTH constant).
    - birth_params is falsy AND chart_id != CANONICAL_CHART_ID → raise ValueError.

    Writers should call this at the top of their run() before any computation
    that depends on birth_params, replacing any 'birth_params or NATIVE_BIRTH'
    silent-fallback pattern.
    """
    if birth_params:
        return birth_params
    if chart_id == CANONICAL_CHART_ID:
        return None
    raise ValueError(
        f"[resolve_birth_params] non-native chart {chart_id} has no usable birth_params"
        " — refusing NATIVE_BIRTH fallback; ensure birth data is in public.charts before building"
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
