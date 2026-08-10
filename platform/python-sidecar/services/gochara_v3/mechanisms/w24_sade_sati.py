"""
gochara_v3.mechanisms.w24_sade_sati — Sade Sati, fully.

Wave 2 Lane W2.4: phase-quarter intensity modifier + cancellation rules.

v1 consumed only a boolean phase-membership signal from `ga_sade_sati`.
`ga_sade_sati` actually writes ~11k rows to `chart_facts` including:
  - per-phase start/end ISO timestamps (category `sade_sati_phase`)
  - cancellation_active_flag + cancellation_rules_invoked_jsonb
    (category `sade_sati_cancellation_check`)

This mechanism reads those pre-fetched rows from ClassContext.sade_sati_phases
and produces:
  - A phase intensity modifier in [0.95, 1.30] (adverse amplifier during Sade Sati)
  - A detail dict carrying phase_type, cancellation info, rules_fired
  - modifier == 1.0 when the mechanism is disabled or t_jd is outside any phase

Phase intensity multipliers (adverse amplification):
  VISHAKHA (12th from Moon, rising) : 1.15
  JANMA    (Moon sign, peak)         : 1.30
  ANUMUKHA (2nd from Moon, setting)  : 1.10
  none (outside all phases)          : 1.00

Cancellation rules: when `cancellation_active_flag` is "true" for the
matched cycle, the modifier is stepped down by 0.05 (partial mitigation),
and the fired rules are recorded in the detail for downstream audit.

CONSTRAINT: this module is DORMANT — it computes and returns MechanismResult
but is NOT wired into engine.py. Admission is gated on ablation evidence
per the UTK-R3 registry entry.

I2 compliance: does NOT import or modify services/gochara_grammar/* or
services/gochara_intensity/*.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Toggle key (must match registry YAML toggle_key)
# ---------------------------------------------------------------------------

MECHANISM_ID = "w24_sade_sati"
TOGGLE_KEY = "w24_sade_sati"

# ---------------------------------------------------------------------------
# Phase name mapping: chart_facts subject suffix → classification
# ---------------------------------------------------------------------------
# ga_sade_sati writes fact_subject like "CY_2017.VISHAKHA", "CY_2017.JANMA",
# "CY_2017.ANUMUKHA" for category sade_sati_phase.
# The phase_type here is our internal three-valued enum.

_PHASE_NAME_TO_TYPE: dict[str, str] = {
    "VISHAKHA": "rising",   # 12th from natal Moon — onset
    "JANMA": "peak",        # natal Moon sign — maximum intensity
    "ANUMUKHA": "setting",  # 2nd from natal Moon — waning
}

# Phase intensity multipliers for adverse event classes.
# These amplify PERMISSION weight when the native is in Sade Sati.
# Gain/neutral event classes receive modifier == 1.0 regardless (see compute()).
PHASE_MODIFIERS: dict[str, float] = {
    "rising": 1.15,    # VISHAKHA — onset, building dread
    "peak": 1.30,      # JANMA — maximum intensity
    "setting": 1.10,   # ANUMUKHA — waning but still active
    "none": 1.00,      # outside Sade Sati
}

# When a cancellation rule fires, apply this step-down to the modifier.
# Partial mitigation — does not zero out Sade Sati effect entirely.
CANCELLATION_STEP_DOWN: float = 0.05

# ---------------------------------------------------------------------------
# MechanismResult dataclass (shared across all W2 mechanisms)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechanismResult:
    """Output of a dormant mechanism's compute() call.

    modifier : float in [0.9, 1.5] — multiplicative factor on the
               upstream PERMISSION weight for this event_class×JD.
               1.0 = no effect; >1.0 = amplify; <1.0 = suppress.
    detail   : dict — provenance; what fired, which phase, which rules.
    fired    : bool — True when the mechanism produced a non-unity modifier.
    mechanism_id : str — links back to the registry entry.
    """
    modifier: float
    detail: dict
    fired: bool
    mechanism_id: str = MECHANISM_ID


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _iso_to_jd(iso_str: str) -> Optional[float]:
    """Convert an ISO datetime string to a Julian Day number.

    Supports both full ISO (with time component) and date-only strings.
    Returns None on any parse failure so callers can degrade gracefully.

    JD formula: JD = 2440587.5 + (unix_timestamp_seconds / 86400.0).
    This gives noon-referenced JD consistent with Swiss Ephemeris conventions.
    """
    if not iso_str:
        return None
    try:
        # Try full ISO first (with time zone or naive)
        s = iso_str.strip()
        if "T" in s or " " in s:
            # Normalize: replace space separator, add Z if naive UTC-like
            s_norm = s.replace(" ", "T")
            if s_norm.endswith("+00:00"):
                s_norm = s_norm[:-6] + "Z"
            try:
                dt = datetime.fromisoformat(s_norm.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.fromisoformat(s_norm)
        else:
            # Date-only: assume midnight UTC
            dt = datetime.fromisoformat(s + "T00:00:00+00:00")

        # Ensure UTC-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        unix_ts = dt.timestamp()
        return 2440587.5 + unix_ts / 86400.0
    except Exception as exc:  # noqa: BLE001
        logger.debug("[w24_sade_sati] ISO→JD parse failed for %r: %s", iso_str, exc)
        return None


def _extract_phase_intervals(
    sade_sati_phases: tuple[dict, ...],
) -> list[dict]:
    """Extract phase time intervals from pre-fetched chart_facts rows.

    Scans for rows with fact_category='sade_sati_phase' and collects
    (start_jd, end_jd, phase_type, cycle_id) tuples.

    The chart_facts rows for each phase subject carry separate keys:
      fact_key='phase_start_iso' -> fact_value_text = ISO datetime
      fact_key='phase_end_iso'   -> fact_value_text = ISO datetime

    We group by fact_subject (e.g. "CY_2017.JANMA") and extract both
    start and end for each phase.

    Returns a list of dicts:
      {
        'cycle_id': str,          # e.g. "CY_2017"
        'phase_name': str,        # VISHAKHA / JANMA / ANUMUKHA
        'phase_type': str,        # rising / peak / setting
        'start_jd': float,
        'end_jd': float,
      }
    """
    # Accumulate start/end per subject
    by_subject: dict[str, dict] = {}
    for row in sade_sati_phases:
        cat = row.get("fact_category", "")
        if cat != "sade_sati_phase":
            continue
        subj = row.get("fact_subject", "")
        key = row.get("fact_key", "")
        val_text = row.get("fact_value_text") or ""

        if subj not in by_subject:
            by_subject[subj] = {"subject": subj, "start_iso": None, "end_iso": None}

        if key == "phase_start_iso":
            by_subject[subj]["start_iso"] = val_text
        elif key == "phase_end_iso":
            by_subject[subj]["end_iso"] = val_text

    intervals: list[dict] = []
    for subj, data in by_subject.items():
        start_iso = data.get("start_iso")
        end_iso = data.get("end_iso")
        if not start_iso or not end_iso:
            continue

        start_jd = _iso_to_jd(start_iso)
        end_jd = _iso_to_jd(end_iso)
        if start_jd is None or end_jd is None:
            continue

        # Parse phase_name from subject: "CY_2017.JANMA" → phase_name="JANMA"
        parts = subj.rsplit(".", 1)
        if len(parts) != 2:
            continue
        cycle_id, phase_name = parts[0], parts[1]
        phase_type = _PHASE_NAME_TO_TYPE.get(phase_name)
        if phase_type is None:
            continue

        intervals.append({
            "cycle_id": cycle_id,
            "phase_name": phase_name,
            "phase_type": phase_type,
            "start_jd": start_jd,
            "end_jd": end_jd,
        })

    return intervals


def _extract_cancellation_by_cycle(
    sade_sati_phases: tuple[dict, ...],
) -> dict[str, dict]:
    """Extract cancellation info keyed by cycle_id.

    Looks for rows with fact_category='sade_sati_cancellation_check':
      fact_key='cancellation_active_flag'       -> fact_value_text "true"/"false"
      fact_key='cancellation_rules_invoked_jsonb' -> fact_value_text (JSON list)

    Returns dict: {cycle_id: {"cancellation_active": bool, "rules_fired": list[str]}}
    """
    result: dict[str, dict] = {}
    for row in sade_sati_phases:
        cat = row.get("fact_category", "")
        if cat != "sade_sati_cancellation_check":
            continue
        cycle_id = row.get("fact_subject", "")
        key = row.get("fact_key", "")
        val_text = row.get("fact_value_text") or ""

        if cycle_id not in result:
            result[cycle_id] = {"cancellation_active": False, "rules_fired": []}

        if key == "cancellation_active_flag":
            result[cycle_id]["cancellation_active"] = (val_text.strip().lower() == "true")
        elif key == "cancellation_rules_invoked_jsonb":
            if val_text:
                try:
                    parsed = json.loads(val_text)
                    if isinstance(parsed, list):
                        result[cycle_id]["rules_fired"] = parsed
                except Exception:  # noqa: BLE001
                    pass

    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Compute the Sade Sati phase-intensity modifier for a given Julian Day.

    Parameters
    ----------
    context : ClassContext
        Pre-fetched gochara_v3 ClassContext. Must have .sade_sati_phases and
        .is_adverse attributes. Only the is_adverse attribute governs whether
        a non-unity modifier is returned — Sade Sati amplifies adverse events;
        for gain/neutral classes it is a no-op (modifier == 1.0).
    t_jd : float
        Julian Day to evaluate. Compared against phase start/end JDs derived
        from the pre-fetched chart_facts rows.
    enabled : bool
        Toggle controlled by TOGGLE_KEY in the caller's feature flags.
        When False, returns modifier == 1.0 unconditionally (unit modifier).

    Returns
    -------
    MechanismResult with:
      modifier  — PHASE_MODIFIERS[phase_type], stepped down by
                  CANCELLATION_STEP_DOWN if a cancellation rule fires.
                  Always 1.0 when disabled, not in Sade Sati, or is_adverse=False.
      fired     — True when modifier != 1.0.
      detail    — provenance dict including phase_type, cycle_id, cancellation.
    """
    if not enabled:
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "disabled", "toggle_key": TOGGLE_KEY},
            fired=False,
        )

    sade_sati_phases: tuple[dict, ...] = getattr(context, "sade_sati_phases", ())
    is_adverse: bool = getattr(context, "is_adverse", False)

    # No phase data — honest unit modifier
    if not sade_sati_phases:
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "no_sade_sati_phases", "phase_type": "none"},
            fired=False,
        )

    # Extract phase intervals and cancellation info
    intervals = _extract_phase_intervals(sade_sati_phases)
    cancellation_by_cycle = _extract_cancellation_by_cycle(sade_sati_phases)

    # Find the active phase for t_jd
    active_interval: Optional[dict] = None
    for interval in intervals:
        if interval["start_jd"] <= t_jd < interval["end_jd"]:
            active_interval = interval
            break

    if active_interval is None:
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "not_in_sade_sati", "phase_type": "none", "t_jd": t_jd},
            fired=False,
        )

    phase_type = active_interval["phase_type"]
    cycle_id = active_interval["cycle_id"]
    phase_name = active_interval["phase_name"]

    # Base modifier from phase type
    base_modifier = PHASE_MODIFIERS[phase_type]

    # Sade Sati only amplifies adverse events; for neutral/gain, no-op.
    if not is_adverse:
        return MechanismResult(
            modifier=1.0,
            detail={
                "reason": "not_adverse_class",
                "phase_type": phase_type,
                "phase_name": phase_name,
                "cycle_id": cycle_id,
                "base_modifier_suppressed": base_modifier,
            },
            fired=False,
        )

    # Cancellation check
    cancel_info = cancellation_by_cycle.get(cycle_id, {})
    cancellation_active: bool = cancel_info.get("cancellation_active", False)
    rules_fired: list[str] = cancel_info.get("rules_fired", [])

    modifier = base_modifier
    if cancellation_active:
        modifier = max(1.0, modifier - CANCELLATION_STEP_DOWN)

    detail: dict = {
        "phase_type": phase_type,
        "phase_name": phase_name,
        "cycle_id": cycle_id,
        "base_modifier": base_modifier,
        "modifier_applied": modifier,
        "cancellation_active": cancellation_active,
        "rules_fired": rules_fired,
        "cancellation_step_down": CANCELLATION_STEP_DOWN if cancellation_active else 0.0,
        "is_adverse": is_adverse,
        "t_jd": t_jd,
    }

    fired = abs(modifier - 1.0) > 1e-9

    return MechanismResult(
        modifier=modifier,
        detail=detail,
        fired=fired,
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "PHASE_MODIFIERS",
    "CANCELLATION_STEP_DOWN",
    "MechanismResult",
    "compute",
]
