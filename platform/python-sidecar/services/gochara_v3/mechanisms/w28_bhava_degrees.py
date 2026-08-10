"""
gochara_v3.mechanisms.w28_bhava_degrees — Bhava cusp degrees (Wave 2, Lane W2.8).

Problem
-------
``enrich_targets`` (services/gochara_intensity/enrichment.py) resolves bhava-typed
ResonanceTargets to their whole-sign ``target_sign`` ONLY — ``target_longitude_deg``
is left ``None`` (documented gap, enrichment.py lines 46-58).  Degree-hungry
primitives (``station_retro_loop``, ``eclipse_degree``, ``planetary_return``)
guard on ``target_longitude_deg is None`` and silently skip every bhava target.
The result: house targets contribute ZERO to X(t) for these three primitives,
even when they are classically the primary resonance surface.

Fix (§N.5 compliant)
--------------------
This mechanism enriches bhava-typed ResonanceTargets with the cusp midpoint degree
(``sripati_madhya``) from L1 ``chart_facts`` rows (``fact_category='bhava_cusps'``,
``fact_subject='BHAVA_01'..'BHAVA_12'``).  The cusp degree is referenced by its
``fact_id`` — it is NEVER re-derived or re-computed here (§N.5: L1 is the authority).

This module is a CANDIDATE mechanism: NOT wired into engine.py (Wave 4 wiring).
Its modifier is always 1.0 — this mechanism produces SENTENCES (one per resolved
bhava target), not a multiplicative modifier on lambda.  Its job is enabling other
primitives to see house targets; the downstream lambda change happens inside those
primitives.

Classical grounding
-------------------
Bhava cusps are the cusp-system output of the ``ga_positions_writer`` (GA-2),
stored in ``chart_facts`` as Sripati midpoints (``sripati_madhya``).  The Sripati
system is the classical Parashara system for equal/unequal house midpoints.

Per §N.5: every sentence carries the L1 ``fact_id`` it resolved the degree from.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

MECHANISM_ID = "w28_bhava_degrees"
TOGGLE_KEY = "w28_bhava_degrees"

# Bhava cusp fact query parameters (L1 schema — ga_positions_writer.py lines 451-465)
_BHAVA_FACT_CATEGORY = "bhava_cusps"
# Sripati midpoint: the single-degree anchor for a bhava (not start/end span).
# This is the classical cusp point a degree-hungry primitive scans against.
_BHAVA_CUSP_KEY = "sripati_madhya"

# fact_subject naming: BHAVA_01 .. BHAVA_12 (zero-padded two digits)
def _bhava_subject(house_num: int) -> str:
    return f"BHAVA_{house_num:02d}"


@dataclass
class MechanismResult:
    """Result returned by ``compute()``.

    modifier:
        Always 1.0 for this mechanism — bhava-degree enrichment does not
        multiply lambda directly.  Downstream primitives fire (or not) based
        on whether the target now has a degree; the lambda change is theirs.
    sentences:
        One entry per bhava-typed ResonanceTarget that was successfully
        enriched with a cusp degree.  Each entry carries:
          - target_ref: house number string ("1".."12")
          - bhava_subject: BHAVA_NN string (L1 fact_subject)
          - cusp_deg: resolved sripati_madhya degree (float)
          - fact_id: L1 chart_facts.fact_id this degree was read from (§N.5)
          - note: human-readable provenance note
        Empty when no bhava targets are present, or natal_facts carries no
        bhava cusp data.
    detail:
        Summary dict for the mechanism as a whole.
    mechanism_id:
        Always MECHANISM_ID.
    enabled:
        False when the mechanism was toggled off at call time.
    """
    modifier: float = 1.0
    sentences: list[dict] = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    mechanism_id: str = MECHANISM_ID
    enabled: bool = True


def compute(context: Any, t_jd: float, *, enabled: bool = True) -> MechanismResult:
    """Resolve bhava cusp degrees from L1 chart_facts into ClassContext.

    Parameters
    ----------
    context:
        A ``ClassContext`` instance (or any object exposing
        ``.resonance_targets`` as an iterable of objects with
        ``.target_type`` / ``.target_ref`` attributes, and
        ``.natal_facts`` as an object with a ``.bhava_cusp_degrees`` dict
        keyed by bhava subject ("BHAVA_01".."BHAVA_12"), or None).

        The fixture-injection path in tests passes a minimal dataclass —
        this function never calls ``.fetch()`` or touches a DB connection.
    t_jd:
        Julian Day of the evaluation point.  Used only for sentence detail
        logging; cusp degrees are time-invariant for a natal chart.
    enabled:
        Toggle.  When False returns a unit result immediately with modifier=1.0.

    Returns
    -------
    MechanismResult
        modifier is always 1.0.
        sentences contains one entry per bhava target successfully resolved.
    """
    if not enabled:
        return MechanismResult(
            modifier=1.0,
            sentences=[],
            detail={"reason": "disabled"},
            enabled=False,
        )

    # --- collect bhava-typed targets ---
    resonance_targets = getattr(context, "resonance_targets", ()) or ()
    bhava_targets = [
        t for t in resonance_targets
        if getattr(t, "target_type", None) == "bhava"
    ]

    if not bhava_targets:
        return MechanismResult(
            modifier=1.0,
            sentences=[],
            detail={
                "mechanism_id": MECHANISM_ID,
                "reason": "no_bhava_targets",
                "note": (
                    "No bhava-typed ResonanceTargets found in context; "
                    "no degree enrichment needed."
                ),
            },
            enabled=True,
        )

    # --- extract cusp degree map from natal_facts ---
    natal_facts = getattr(context, "natal_facts", None)
    cusp_degrees: dict[str, dict] = {}  # subject -> {"deg": float, "fact_id": str}

    if natal_facts is not None:
        # natal_facts.bhava_cusp_degrees is the dict we expect:
        # {"BHAVA_01": {"deg": 12.34, "fact_id": "..."}, ...}
        bhava_cusp_map = getattr(natal_facts, "bhava_cusp_degrees", None) or {}
        for subj, entry in bhava_cusp_map.items():
            if isinstance(entry, dict) and entry.get("deg") is not None:
                cusp_degrees[subj] = entry

    if not cusp_degrees:
        return MechanismResult(
            modifier=1.0,
            sentences=[],
            detail={
                "mechanism_id": MECHANISM_ID,
                "reason": "no_natal_facts_cusp_data",
                "note": (
                    "natal_facts carries no bhava_cusp_degrees data "
                    "(ClassContext built without DB access, or chart_facts "
                    "has no bhava_cusps rows). "
                    "No enrichment possible — honest empty result per §N.8."
                ),
                "bhava_target_count": len(bhava_targets),
            },
            enabled=True,
        )

    # --- build sentences for each resolved bhava target ---
    sentences: list[dict] = []
    unresolved: list[str] = []

    for target in bhava_targets:
        ref = getattr(target, "target_ref", None)
        try:
            house_num = int(ref)
        except (TypeError, ValueError):
            unresolved.append(str(ref))
            continue

        if house_num < 1 or house_num > 12:
            unresolved.append(str(ref))
            continue

        subj = _bhava_subject(house_num)
        entry = cusp_degrees.get(subj)
        if entry is None:
            unresolved.append(str(ref))
            continue

        cusp_deg = float(entry["deg"])
        fact_id = entry.get("fact_id", "")
        event_class = getattr(target, "event_class", None)
        weight = getattr(target, "weight", None)

        sentences.append({
            "mechanism_id": MECHANISM_ID,
            "target_ref": str(ref),
            "bhava_subject": subj,
            "cusp_deg": cusp_deg,
            "fact_id": fact_id,        # L1 reference per §N.5
            "event_class": event_class,
            "weight": weight,
            "t_jd": t_jd,
            "note": (
                f"Bhava {house_num} cusp resolved: sripati_madhya={cusp_deg:.4f}° "
                f"(L1 fact_id={fact_id!r}); degree-hungry primitives can now "
                f"evaluate station/eclipse/return events against this bhava target."
            ),
        })

    resolved_count = len(sentences)
    total_bhava = len(bhava_targets)

    return MechanismResult(
        modifier=1.0,  # always unit — this mechanism enables, does not scale
        sentences=sentences,
        detail={
            "mechanism_id": MECHANISM_ID,
            "bhava_targets_total": total_bhava,
            "resolved_count": resolved_count,
            "unresolved_refs": unresolved,
            "cusp_key_used": _BHAVA_CUSP_KEY,
            "note": (
                f"Resolved {resolved_count}/{total_bhava} bhava targets with "
                f"L1 sripati_madhya cusp degrees. "
                f"Degree-hungry primitives (station_retro_loop, eclipse_degree, "
                f"planetary_return) will now receive house targets that previously "
                f"had target_longitude_deg=None and were silently skipped."
            ) if resolved_count > 0 else (
                "No bhava targets could be resolved to a cusp degree. "
                f"Unresolved refs: {unresolved}."
            ),
        },
        enabled=True,
    )


__all__ = ["MECHANISM_ID", "TOGGLE_KEY", "MechanismResult", "compute"]
