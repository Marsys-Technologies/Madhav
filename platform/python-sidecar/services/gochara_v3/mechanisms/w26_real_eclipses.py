"""
gochara_v3.mechanisms.w26_real_eclipses — Wave 2, Lane W2.6

Real eclipse amplification mechanism: replaces the v1 node×luminary proximity
proxy (eclipse_degree in gochara_grammar/primitives.py, uncited_extension=True)
with actual eclipse events sourced from bg_sky_calendar.

Architecture
------------
This is a DORMANT candidate mechanism — it is NOT wired into engine.py.
It lives in the mechanisms/ package for ablation-evidence collection once the
sky_calendar data is pre-fetched into ClassContext (a future Wave 2 context
extension). For now the module operates defensively: if no eclipse rows are
present in the context it returns modifier=1.0 (honest unit — no data, no
amplification).

The v1 proxy (primitives.eclipse_degree) computed Rahu/Ketu node × luminary
conjunction windows as a stand-in for eclipses. That approach has two defects:
  1. Node-luminary conjunction ≠ eclipse (eclipses require alignment in
     ecliptic latitude, not just longitude — the node conjunction is a
     necessary but not sufficient condition).
  2. uncited_extension=True: no classical citation was found in the codebase
     for the specific technique of matching eclipse-degree-to-natal-point
     contact via node proximity.

This mechanism uses real eclipse events (event_type='eclipse_solar' /
'eclipse_lunar' from bg_sky_events / bg_sky_calendar, computed via
pyswisseph's sol_eclipse_when_glob / lun_eclipse_when — real eclipse geometry,
not the orb proxy). When an eclipse's ecliptic longitude is within
ECLIPSE_ORBS_DEG of any resonance target's natal longitude, a multiplicative
modifier > 1.0 is applied, scaled by eclipse type severity.

Classical grounding
-------------------
BPHS eclipse chapters treat eclipses (grahaṇa) as amplifiers of gochara
effects when they occur near sensitive natal degrees. Total solar eclipses are
the strongest event; penumbral lunar eclipses the mildest.

v1 lineage
----------
Replaces: eclipse_degree primitive in services/gochara_grammar/primitives.py
  (uncited_extension=True, node×luminary proximity proxy)
Change type: replacement (not removal of v1 — v1 grammar is frozen per I2;
  this mechanism is the v3 override candidate that will gate its contribution
  once admitted to the engine).

Admission state: candidate (ablation evidence pending).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mechanism identity
# ---------------------------------------------------------------------------

MECHANISM_ID = "w26_real_eclipses"
TOGGLE_KEY = "w26_real_eclipses"

# ---------------------------------------------------------------------------
# Eclipse parameters
# ---------------------------------------------------------------------------

# An eclipse within this arc distance of any resonance target's natal longitude
# is considered "contacted" and amplifies the gochara modifier.
ECLIPSE_ORBS_DEG: float = 10.0

# Temporal relevance window: eclipses within ±90 days of the evaluation JD
# are considered active contributors. Beyond this the eclipse is too far in
# past/future to modulate the current gochara window.
ECLIPSE_TEMPORAL_WINDOW_DAYS: float = 90.0

# Modifier per eclipse type. Values are multiplicative amplifiers applied to
# the gochara intensity when a contacted eclipse is present. Range: [1.0, 2.0].
# Sourced from classical severity ordering (total solar > total lunar >
# annular/partial); exact values are calibrated starting points (candidate
# stage — ablation will tune them).
ECLIPSE_MODIFIERS: dict[str, float] = {
    "total_solar": 1.35,
    "annular_solar": 1.20,
    "annular_total": 1.20,    # pyswisseph ECL_ANNULAR_TOTAL (hybrid)
    "partial_solar": 1.10,
    "total_lunar": 1.25,
    "partial_lunar": 1.10,
    "penumbral_lunar": 1.05,
    "unknown": 1.02,          # honest fallback — some effect, not zero, not full
}

# Default modifier when no eclipse is contacted (unit: no amplification).
_UNIT_MODIFIER: float = 1.0

# Hard bounds for the returned modifier (§N.6 density invariant: never outside
# the declared range even under unexpected inputs).
_MIN_MODIFIER: float = 0.0
_MAX_MODIFIER: float = 2.0


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class MechanismResult:
    """Result returned by compute().

    modifier        Multiplicative modifier in [0.0, 2.0].
                    1.0 = no eclipse effect (unit).
                    >1.0 = eclipse amplification active.
    mechanism_id    Always MECHANISM_ID — for provenance on the caller side.
    enabled         Whether the mechanism was active for this call.
    eclipse_count   Number of temporal + spatial contacts found.
    contacted_eclipses
                    List of dicts, one per contacted eclipse, with keys:
                      event_type, eclipse_type, eclipse_jd, longitude_deg,
                      target_ref, arc_deg, modifier_contribution.
    data_source     'sky_calendar_context' | 'no_data' | 'disabled'.
    detail          Free-form dict for additional provenance.
    """
    modifier: float
    mechanism_id: str = MECHANISM_ID
    enabled: bool = True
    eclipse_count: int = 0
    contacted_eclipses: list[dict] = field(default_factory=list)
    data_source: str = "no_data"
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _shortest_arc_deg(a: float, b: float) -> float:
    """Shortest arc between two ecliptic longitudes (always positive, ≤ 180)."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def _eclipse_type_from_row(row: Any) -> str:
    """Extract eclipse_type from a sky_calendar row (dict or sequence).

    bg_sky_calendar stores eclipse_type inside the detail JSONB column.
    This helper resolves it regardless of whether the row is a dict or a
    positional tuple produced by a raw psycopg cursor.

    Column order assumed for positional rows (matches bg_sky_calendar schema):
      0: event_type, 1: primary_body, 2: secondary_body, 3: event_jd,
      4: longitude_deg, 5: detail (JSONB / dict)
    """
    import json as _json
    if isinstance(row, dict):
        event_type = row.get("event_type", "")
        longitude_deg = row.get("longitude_deg")
        detail = row.get("detail") or {}
        eclipse_jd = row.get("event_jd")
    else:
        try:
            event_type = row[0] if len(row) > 0 else ""
            longitude_deg = row[4] if len(row) > 4 else None
            raw_detail = row[5] if len(row) > 5 else {}
            eclipse_jd = row[3] if len(row) > 3 else None
            if isinstance(raw_detail, str):
                try:
                    detail = _json.loads(raw_detail)
                except Exception:  # noqa: BLE001
                    detail = {}
            else:
                detail = raw_detail or {}
        except (IndexError, TypeError):
            event_type = ""
            longitude_deg = None
            detail = {}
            eclipse_jd = None

    return event_type, longitude_deg, detail, eclipse_jd


def _noisy_or(modifiers: list[float]) -> float:
    """Combine multiple modifiers via noisy-OR logic.

    For amplifiers m_i > 1.0, the combined modifier is:
        combined = 1 + noisy_or_of_excesses
    where excess_i = m_i - 1.0 and noisy-OR is 1 - product(1 - excess_i).

    This ensures the combined modifier never exceeds 2.0 (the declared
    _MAX_MODIFIER bound), is always >= the largest individual modifier,
    and gracefully handles the single-modifier case (returns m unchanged).
    """
    if not modifiers:
        return _UNIT_MODIFIER
    excesses = [max(0.0, m - 1.0) for m in modifiers]
    combined_excess = 1.0 - 1.0
    not_combined = 1.0
    for e in excesses:
        not_combined *= (1.0 - e)
    combined_excess = 1.0 - not_combined
    result = 1.0 + combined_excess
    return max(_MIN_MODIFIER, min(_MAX_MODIFIER, result))


# ---------------------------------------------------------------------------
# Primary interface
# ---------------------------------------------------------------------------

def compute(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Compute the eclipse amplification modifier for evaluation JD t_jd.

    Parameters
    ----------
    context
        A ClassContext (or any object with a `resonance_targets` attribute and
        optionally a `sky_calendar_rows` attribute). The mechanism degrades
        gracefully when sky_calendar data is absent — it returns modifier=1.0
        with data_source='no_data'.
    t_jd
        Julian Day of the evaluation point (UT).
    enabled
        Toggle key — when False, returns unit modifier immediately (disabled).

    Returns
    -------
    MechanismResult with modifier in [0.0, 2.0].
      - modifier == 1.0 when disabled, no data, or no eclipse contact found.
      - modifier > 1.0 when a real eclipse contacts a resonance target natal point.
    """
    if not enabled:
        return MechanismResult(
            modifier=_UNIT_MODIFIER,
            enabled=False,
            data_source="disabled",
            detail={"reason": "mechanism disabled via toggle"},
        )

    # ------------------------------------------------------------------
    # Resolve sky_calendar rows from context.
    # ClassContext (current build) does NOT pre-fetch sky_calendar data —
    # that is a planned Wave 2 context extension. For now we check for an
    # optional `sky_calendar_rows` attribute (synthetic injection for tests
    # and future context extension) and fall back honestly to no_data.
    # ------------------------------------------------------------------
    sky_rows: list[Any] = []
    if hasattr(context, "sky_calendar_rows") and context.sky_calendar_rows:
        sky_rows = list(context.sky_calendar_rows)

    if not sky_rows:
        logger.debug(
            "[w26_real_eclipses] no sky_calendar data in context — modifier=1.0 (honest).",
        )
        return MechanismResult(
            modifier=_UNIT_MODIFIER,
            enabled=True,
            eclipse_count=0,
            data_source="no_data",
            detail={"reason": "sky_calendar_rows not present in context"},
        )

    # ------------------------------------------------------------------
    # Resolve resonance target longitudes.
    # Each target may carry a `target_longitude_deg` attribute (ResonanceTarget).
    # We collect all non-None longitudes as the natal contact set.
    # ------------------------------------------------------------------
    natal_points: list[tuple[str, float]] = []  # (target_ref, longitude_deg)
    targets = getattr(context, "resonance_targets", ()) or ()
    for t in targets:
        lon = getattr(t, "target_longitude_deg", None)
        ref = getattr(t, "target_ref", "?")
        if lon is not None:
            natal_points.append((ref, float(lon)))

    if not natal_points:
        logger.debug(
            "[w26_real_eclipses] no resonance targets with longitudes — modifier=1.0.",
        )
        return MechanismResult(
            modifier=_UNIT_MODIFIER,
            enabled=True,
            eclipse_count=0,
            data_source="sky_calendar_context",
            detail={"reason": "no natal longitudes on resonance targets"},
        )

    # ------------------------------------------------------------------
    # Filter sky_calendar rows to eclipse events within the temporal window.
    # ------------------------------------------------------------------
    active_modifiers: list[float] = []
    contacted: list[dict] = []

    for row in sky_rows:
        event_type, longitude_deg, detail, eclipse_jd = _eclipse_type_from_row(row)

        # Only process eclipse events.
        if not (isinstance(event_type, str) and event_type.startswith("eclipse_")):
            continue

        # Temporal gate: eclipse must be within ±ECLIPSE_TEMPORAL_WINDOW_DAYS.
        if eclipse_jd is None:
            continue
        try:
            eclipse_jd_f = float(eclipse_jd)
        except (TypeError, ValueError):
            continue
        if abs(eclipse_jd_f - t_jd) > ECLIPSE_TEMPORAL_WINDOW_DAYS:
            continue

        # Eclipse longitude for arc computation.
        if longitude_deg is None:
            continue
        try:
            eclipse_lon = float(longitude_deg)
        except (TypeError, ValueError):
            continue

        # Determine eclipse_type from detail JSONB.
        eclipse_type = detail.get("eclipse_type", "unknown") if isinstance(detail, dict) else "unknown"
        if not isinstance(eclipse_type, str) or not eclipse_type:
            eclipse_type = "unknown"

        # Build full key: e.g. "total_solar", "total_lunar".
        family = "solar" if "solar" in event_type else "lunar"
        full_key = f"{eclipse_type}_{family}"
        modifier_val = ECLIPSE_MODIFIERS.get(full_key, ECLIPSE_MODIFIERS.get("unknown", 1.02))

        # Spatial gate: check arc to each natal point.
        for target_ref, natal_lon in natal_points:
            arc = _shortest_arc_deg(eclipse_lon, natal_lon)
            if arc <= ECLIPSE_ORBS_DEG:
                active_modifiers.append(modifier_val)
                contacted.append({
                    "event_type": event_type,
                    "eclipse_type": eclipse_type,
                    "eclipse_key": full_key,
                    "eclipse_jd": round(eclipse_jd_f, 4),
                    "longitude_deg": round(eclipse_lon, 4),
                    "target_ref": target_ref,
                    "natal_longitude_deg": round(natal_lon, 4),
                    "arc_deg": round(arc, 4),
                    "modifier_contribution": modifier_val,
                    "temporal_offset_days": round(eclipse_jd_f - t_jd, 2),
                })

    if not active_modifiers:
        return MechanismResult(
            modifier=_UNIT_MODIFIER,
            enabled=True,
            eclipse_count=0,
            contacted_eclipses=[],
            data_source="sky_calendar_context",
            detail={"sky_rows_checked": len(sky_rows), "natal_points": len(natal_points)},
        )

    combined = _noisy_or(active_modifiers)
    combined = max(_MIN_MODIFIER, min(_MAX_MODIFIER, combined))

    return MechanismResult(
        modifier=combined,
        enabled=True,
        eclipse_count=len(contacted),
        contacted_eclipses=contacted,
        data_source="sky_calendar_context",
        detail={
            "sky_rows_checked": len(sky_rows),
            "natal_points": len(natal_points),
            "individual_modifiers": active_modifiers,
            "combined_via": "noisy_or_of_excesses",
        },
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "ECLIPSE_ORBS_DEG",
    "ECLIPSE_TEMPORAL_WINDOW_DAYS",
    "ECLIPSE_MODIFIERS",
    "MechanismResult",
    "compute",
]
