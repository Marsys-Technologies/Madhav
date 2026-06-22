"""
ph_muhurta engine — DB-free derivation for muhurta quality + elevations M1-M4.

Calls ka_muhurta_seva / panchang_engine via the writer (passed as pre-fetched data).
NEVER reimplements panchanga math — that lives in ka_muhurta_seva.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

__all__ = [
    'MuhurtaContext',
    'MuhurtaRecord',
    'compute_composite_quality',
    'classify_verdict',
    'ACTION_GRAHA_MAP',
]

# M1: which graha governs each action class
ACTION_GRAHA_MAP: dict[str, str] = {
    'start_business':       'saturn',   # 10th-lord = Saturn (Capricorn lagna)
    'career_launch':        'saturn',
    'contract_signing':     'mercury',
    'marriage':             'venus',
    'partnership':          'venus',
    'medical':              'moon',
    'surgery':              'mars',
    'travel':               'mercury',
    'relocation':           'moon',
    'spiritual_initiation': 'jupiter',
    'sadhana':              'jupiter',
    'ceremony':             'jupiter',
    'property_purchase':    'mars',
    'vehicle_purchase':     'venus',
    'new_venture':          'saturn',
    'charity':              'jupiter',
}

# M4: minimum panchanga_score to be "genuine" quality
_GENUINE_THRESHOLD = 0.55
_STRONG_THRESHOLD  = 0.75


def compute_composite_quality(
    panchanga_score: float,
    chart_personalization_score: float,
    personal_adversity_penalty: float,
) -> float:
    """composite = panchanga × personalization × (1 − penalty); clamped [0,1]."""
    raw = float(panchanga_score) * float(chart_personalization_score) * (1.0 - float(personal_adversity_penalty))
    return round(max(0.0, min(1.0, raw)), 4)


def classify_verdict(composite_quality: float) -> tuple[str, Optional[str]]:
    """M4: honest verdict; never fabricate 'strong' for weak windows."""
    if composite_quality >= _STRONG_THRESHOLD:
        return 'strong', None
    elif composite_quality >= _GENUINE_THRESHOLD:
        return 'adequate', None
    elif composite_quality > 0.0:
        reason = (
            f"Best available window scores {composite_quality:.2f} — below genuine threshold "
            f"({_GENUINE_THRESHOLD}). Moon may be afflicted or no fixed nakshatra available."
        )
        return 'mediocre', reason
    else:
        return 'none_genuine', "No auspicious window found in the requested timeframe."


@dataclass
class MuhurtaContext:
    """Pre-fetched per-candidate data from the writer."""
    action_class:                str
    window_start:                Optional[datetime] = None
    window_end:                  Optional[datetime] = None
    hora_lord:                   Optional[str] = None
    panchanga_score:             float = 0.5
    panchanga_snapshot:          dict = field(default_factory=dict)
    classical_citation:          str = ''
    # M1
    condition_score:             float = 0.5    # from ga_condition_composite for the relevant graha
    transit_score:               float = 0.5    # from ka_gochara for the relevant graha
    # M2
    overlapping_obstruction_id:  Optional[int] = None
    obstruction_penalty:         float = 0.0
    # M3
    linked_anchor_id:            Optional[str] = None
    linked_anchor_domain:        Optional[str] = None


@dataclass
class MuhurtaRecord:
    action_class:                   str
    window_start:                   Optional[datetime] = None
    window_end:                     Optional[datetime] = None
    hora_lord:                      Optional[str] = None
    panchanga_score:                Optional[float] = None
    chart_personalization_score:    Optional[float] = None
    personalization_graha:          Optional[str] = None
    personal_adversity_penalty:     Optional[float] = None
    overlapping_obstruction_id:     Optional[int] = None
    linked_anchor_id:               Optional[str] = None
    composite_quality:              Optional[float] = None
    window_quality_verdict:         Optional[str] = None
    verdict_reason:                 Optional[str] = None
    panchanga_snapshot_jsonb:       Optional[dict] = None
    classical_citation:             Optional[str] = None
    derivation_ledger_jsonb:        dict = field(default_factory=dict)
    source_citation:                str = ''


def derive_muhurta_record(ctx: MuhurtaContext) -> MuhurtaRecord:
    """Derive one MuhurtaRecord from pre-fetched context (no DB calls)."""
    # M1: personalization = avg(condition, transit)
    personalization = round((ctx.condition_score + ctx.transit_score) / 2.0, 4)
    graha = ACTION_GRAHA_MAP.get(ctx.action_class, 'saturn')

    # M2: penalty from overlapping obstruction
    penalty = ctx.obstruction_penalty if ctx.overlapping_obstruction_id else 0.0

    composite = compute_composite_quality(ctx.panchanga_score, personalization, penalty)
    verdict, reason = classify_verdict(composite)

    derivation = {
        'action_class':             ctx.action_class,
        'panchanga_score':          ctx.panchanga_score,
        'chart_personalization':    personalization,
        'personalization_graha':    graha,
        'condition_score':          ctx.condition_score,
        'transit_score':            ctx.transit_score,
        'adversity_penalty':        penalty,
        'obstruction_id':           ctx.overlapping_obstruction_id,
        'linked_anchor_id':         ctx.linked_anchor_id,
        'composite_formula':        'panchanga × personalization × (1−penalty)',
    }

    start_str = ctx.window_start.isoformat() if ctx.window_start else ''
    src = f"ph_muhurta/{ctx.action_class}/{start_str}"

    return MuhurtaRecord(
        action_class=ctx.action_class,
        window_start=ctx.window_start,
        window_end=ctx.window_end,
        hora_lord=ctx.hora_lord,
        panchanga_score=ctx.panchanga_score,
        chart_personalization_score=personalization,
        personalization_graha=graha,
        personal_adversity_penalty=penalty,
        overlapping_obstruction_id=ctx.overlapping_obstruction_id,
        linked_anchor_id=ctx.linked_anchor_id,
        composite_quality=composite,
        window_quality_verdict=verdict,
        verdict_reason=reason,
        panchanga_snapshot_jsonb=ctx.panchanga_snapshot,
        classical_citation=ctx.classical_citation,
        derivation_ledger_jsonb=derivation,
        source_citation=src,
    )
