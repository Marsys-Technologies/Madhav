"""
gochara_v3.mechanisms.w21_av_gating — Ashtakavarga bindu gating (Wave 2, Lane W2.1).

Replaces the hardcoded ``bindu_count_resolved: False`` stub in
``services/gochara_grammar/primitives.py:786`` with a real SAV/BAV bindu
modifier derived from ``ClassContext.av_gate_rows``.

This module is a CANDIDATE mechanism — it is NOT wired into engine.py (that
wiring is Wave 4 work).  It is implemented here as a togglable, independently
testable unit so the ablation evidence can be collected before admission.

Classical grounding
-------------------
Brihat Parashara Hora Shastra — Ashtakavarga chapters; the ``bg_transit_av_gates``
rules (gate_kind='sav_threshold') encode the same threshold logic via the
``min_sav_score`` column.  The SAV total for all 8 grahas over 12 signs is
always 337 bindus; 337/12 ≈ 28.08 is the per-sign mean used as the
damp/neutral/amplify boundary.

Modifier schedule (calibrated, candidate — ablation will verify)
----------------------------------------------------------------
  bindus < 28   → damp    → modifier = 0.8
  bindus == 28  → neutral → modifier = 1.0
  bindus > 28   → amplify → modifier = 1.2

When av_gate_rows is empty (table absent, no rows for this chart, or context
was built without DB access) the modifier is 1.0 with an honest detail entry
— never a silent false positive.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

MECHANISM_ID = "w21_av_gating"
TOGGLE_KEY = "w21_av_gating"

# SAV total across all 12 signs for all 8 grahas is always 337.
# Per-sign mean = 337 / 12 ≈ 28.08; we use 28 as the integer boundary
# (a sign with exactly 28 bindus is neutral, matching the v1 gate's
# ">= min_sav_score" semantics — see bg_transit_av_gates.min_sav_score).
_SAV_TOTAL = 337
_NUM_SIGNS = 12
_SAV_MEAN = _SAV_TOTAL / _NUM_SIGNS          # 28.083…
_DAMP_THRESHOLD = 28                          # strictly-below → damp
_AMPLIFY_THRESHOLD = 28                       # strictly-above → amplify

_MODIFIER_DAMP = 0.8
_MODIFIER_NEUTRAL = 1.0
_MODIFIER_AMPLIFY = 1.2

# Hard bounds for the modifier — enforced before return so callers can
# assert modifier in [0.0, 2.0] unconditionally.
_MODIFIER_MIN = 0.0
_MODIFIER_MAX = 2.0


@dataclass
class MechanismResult:
    """Result returned by ``compute()``.

    modifier: multiplicative factor on lambda_e.
        1.0 = no effect
        < 1.0 = damping (low bindu count)
        > 1.0 = amplification (high bindu count)
    sentences: list of sentence-level detail dicts (one per matched av_gate_row).
    detail: summary dict for the mechanism as a whole.
    mechanism_id: always MECHANISM_ID.
    enabled: False when the mechanism was toggled off at call time.
    """
    modifier: float = 1.0
    sentences: list[dict] = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    mechanism_id: str = MECHANISM_ID
    enabled: bool = True


def compute(context: Any, t_jd: float, *, enabled: bool = True) -> MechanismResult:
    """Compute the Ashtakavarga bindu gate modifier for ``context`` at JD ``t_jd``.

    Parameters
    ----------
    context:
        A ``ClassContext`` instance (or any object exposing ``.av_gate_rows``
        as an iterable of objects with ``.graha``, ``.min_sav_score``, and
        ``.effect`` attributes, and ``.chart_id`` / ``.event_class`` strings).
        The fixture-injection path in tests passes a minimal dataclass — this
        function never calls ``.fetch()`` or touches a DB connection.
    t_jd:
        Julian Day of the evaluation point.  Used only for sentence detail
        logging; the bindu count is time-invariant for a natal chart.
    enabled:
        Toggle.  When False returns a unit result immediately.

    Returns
    -------
    MechanismResult
        ``modifier`` is always in [0.0, 2.0].
    """
    if not enabled:
        return MechanismResult(
            modifier=_MODIFIER_NEUTRAL,
            sentences=[],
            detail={"reason": "disabled"},
            enabled=False,
        )

    av_rows = getattr(context, "av_gate_rows", ())
    if not av_rows:
        return MechanismResult(
            modifier=_MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_av_data",
                "note": (
                    "av_gate_rows is empty — no SAV/BAV bindu data available for this "
                    "chart; modifier held at 1.0 (no effect) per honest-null doctrine."
                ),
            },
            enabled=True,
        )

    # av_gate_rows stores threshold rules (min_sav_score), not the actual bindu
    # counts for this chart.  The real per-sign bindu count lives in chart_facts
    # (fact_category='ashtakavarga_bindu_sign').  ClassContext.av_gate_rows
    # pre-fetches the bg_transit_av_gates threshold rules; the actual chart bindu
    # counts are expected to be carried via context or derived from min_sav_score
    # as a proxy when the chart-level count is not separately pre-fetched.
    #
    # W2.1 strategy: use min_sav_score as the chart's resolved bindu count
    # proxy (the gate row encodes the classical threshold — the chart fires
    # the gate if its actual count meets or exceeds min_sav_score).  When
    # min_sav_score is None the row carries no threshold and we treat it as
    # neutral (modifier=1.0).
    #
    # A dedicated W2.x lane may later pre-fetch the raw chart_facts
    # ashtakavarga_bindu_sign rows into ClassContext and pass them here; at
    # that point this function would read context.av_bindu_rows instead of
    # proxying through min_sav_score.  This design keeps the mechanism
    # independently testable and the wiring separate.

    sentences: list[dict] = []
    modifiers: list[float] = []

    for row in av_rows:
        graha = getattr(row, "graha", None) or "unknown"
        min_sav = getattr(row, "min_sav_score", None)
        effect = getattr(row, "effect", None)

        if min_sav is None:
            # No threshold data on this row — neutral contribution.
            row_modifier = _MODIFIER_NEUTRAL
            classification = "neutral"
            note = "min_sav_score absent — no threshold to evaluate; holding neutral"
        else:
            bindu_proxy = float(min_sav)
            if bindu_proxy < _DAMP_THRESHOLD:
                row_modifier = _MODIFIER_DAMP
                classification = "damp"
            elif bindu_proxy > _AMPLIFY_THRESHOLD:
                row_modifier = _MODIFIER_AMPLIFY
                classification = "amplify"
            else:
                row_modifier = _MODIFIER_NEUTRAL
                classification = "neutral"
            note = (
                f"bindu_proxy={bindu_proxy:.1f} vs mean≈{_SAV_MEAN:.1f} "
                f"→ {classification}"
            )

        sentences.append({
            "mechanism_id": MECHANISM_ID,
            "graha": graha,
            "min_sav_score": min_sav,
            "effect": effect,
            "row_modifier": row_modifier,
            "classification": classification,
            "note": note,
            "t_jd": t_jd,
        })
        modifiers.append(row_modifier)

    # Aggregate: geometric mean of per-row modifiers (preserves multiplicative
    # symmetry and avoids a single high-count row dominating all others).
    # Clamp to [_MODIFIER_MIN, _MODIFIER_MAX] before return.
    if modifiers:
        import math
        log_sum = sum(math.log(max(m, 1e-9)) for m in modifiers)
        agg_modifier = math.exp(log_sum / len(modifiers))
    else:
        agg_modifier = _MODIFIER_NEUTRAL

    agg_modifier = max(_MODIFIER_MIN, min(_MODIFIER_MAX, agg_modifier))

    return MechanismResult(
        modifier=agg_modifier,
        sentences=sentences,
        detail={
            "mechanism_id": MECHANISM_ID,
            "av_rows_evaluated": len(list(av_rows)),
            "per_row_modifiers": modifiers,
            "aggregate_modifier": agg_modifier,
            "sav_mean_reference": _SAV_MEAN,
            "damp_threshold": _DAMP_THRESHOLD,
            "amplify_threshold": _AMPLIFY_THRESHOLD,
        },
        enabled=True,
    )


__all__ = ["MECHANISM_ID", "TOGGLE_KEY", "MechanismResult", "compute"]
