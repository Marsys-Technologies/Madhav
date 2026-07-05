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
    'compute_tarabala_score',
    'classify_verdict',
    'ACTION_GRAHA_MAP',
]

# M1: which graha governs each action class
ACTION_GRAHA_MAP: dict[str, str] = {
    'start_business':       'saturn',   # default: writer overrides with chart's actual 10th lord
    'career_launch':        'saturn',   # default: writer overrides with chart's actual 10th lord
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
    'new_venture':          'saturn',   # default: writer overrides with chart's actual 10th lord
    'charity':              'jupiter',
}

# M4: minimum panchanga_score to be "genuine" quality
_GENUINE_THRESHOLD = 0.55
_STRONG_THRESHOLD  = 0.75


# BA-P5B: Classical tarabala count from natal Moon nakshatra ordinal [0..26].
# Tarabala cycle: every 9 nakshatras from natal Moon, cycle repeats.
# Tara 1 (Janma)=mixed, 2 (Sampat)=good, 3 (Vipat)=bad, 4 (Kshema)=good,
# 5 (Pratyari)=bad, 6 (Sadhaka)=good, 7 (Vadha)=bad, 8 (Mitra)=good, 9 (Ati-mitra)=good.
_TARABALA_WEIGHTS = [0.5, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0]  # indices 0–8


def compute_tarabala_score(
    natal_moon_nakshatra_idx: int,
    transit_moon_nakshatra_idx: int,
) -> float:
    """Structural tarabala score [0..1] from natal × transit nakshatra indices.

    Both indices are 0-based ordinals into the 27-nakshatra sequence.
    At build time: transit_moon_nakshatra_idx = natal (self-tarabala score = 0.5).
    At serve time: pass actual transit Moon nakshatra.
    """
    offset = (transit_moon_nakshatra_idx - natal_moon_nakshatra_idx) % 27
    tara_idx = offset % 9
    return _TARABALA_WEIGHTS[tara_idx]


def compute_composite_quality(
    panchanga_score: float,
    chart_personalization_score: float,
    personal_adversity_penalty: float,
    tarabala_score: float = 0.5,
    chandrabala_score: float = 0.5,
) -> float:
    """composite = panchanga × personalization × tara_candra_factor × (1 − penalty); clamped [0,1].

    BA-P5B EXT: tara_candra_factor = (tarabala × chandrabala)^0.5 — geometric mean
    of the two classical Moon-strength factors. At build time both default to 0.5.
    """
    tara_candra = (float(tarabala_score) * float(chandrabala_score)) ** 0.5
    raw = (
        float(panchanga_score) *
        float(chart_personalization_score) *
        tara_candra *
        (1.0 - float(personal_adversity_penalty))
    )
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
    # BA-P5B EXT: activity ontology enrichment
    tarabala_score:              float      = 0.5  # Moon tara strength vs natal; 0.5 placeholder if no live source
    chandrabala_score:           float      = 0.5  # Moon rasi strength; 0.5 placeholder if no live source
    # JL-016 (BA-2.5 P3 J6): 'panchang_engine_live' when tarabala_score/chandrabala_score
    # come from a real transit-Moon lookup via panchang_engine; 'placeholder_no_ephemeris'
    # when the 0.5 defaults above are an honest stand-in (natal data or ephemeris unavailable).
    tarabala_chandrabala_source: str        = 'placeholder_no_ephemeris'
    natal_moon_nakshatra_idx:    int        = 0    # from chart_facts (0-based ordinal)
    activity_significators:      dict       = field(default_factory=dict)  # from brahma_activity_ontology
    fructification_rules:        dict       = field(default_factory=dict)  # timing_anchor + panchanga_rules
    fructification_anchor:       Optional[str] = None  # plain-text anchor for this activity class


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
    # BA-P5B EXT: activity ontology enrichment
    tarabala_chandrabala_jsonb:     Optional[dict] = None  # scores + natal Moon nakshatra
    significators_met_jsonb:        Optional[dict] = None  # which conditions satisfied
    fructification_anchor:          Optional[str] = None
    follow_up_hook_jsonb:           Optional[dict] = None  # for P7B scheduler


def derive_muhurta_record(ctx: MuhurtaContext) -> MuhurtaRecord:
    """Derive one MuhurtaRecord from pre-fetched context (no DB calls)."""
    # M1: personalization = avg(condition, transit)
    personalization = round((ctx.condition_score + ctx.transit_score) / 2.0, 4)
    graha = ACTION_GRAHA_MAP.get(ctx.action_class, 'saturn')

    # M2: penalty from overlapping obstruction
    penalty = ctx.obstruction_penalty if ctx.overlapping_obstruction_id else 0.0

    # BA-P5B EXT: incorporate tarabala/chandrabala into composite
    composite = compute_composite_quality(
        ctx.panchanga_score, personalization, penalty,
        tarabala_score=ctx.tarabala_score,
        chandrabala_score=ctx.chandrabala_score,
    )
    verdict, reason = classify_verdict(composite)

    # Significators: check which are noted (structural; full check needs live ephemeris)
    strengthen_grahas = ctx.activity_significators.get('strengthen_grahas', [])
    significators_met = {
        'strengthen_grahas': strengthen_grahas,
        'personalization_graha_match': graha in strengthen_grahas,
        'note': 'structural_check_only; serve-time enrichment adds live ephemeris check',
    }

    is_live = ctx.tarabala_chandrabala_source == 'panchang_engine_live'
    tarabala_chandrabala = {
        'tarabala_score': ctx.tarabala_score,
        'chandrabala_score': ctx.chandrabala_score,
        'natal_moon_nakshatra_idx': ctx.natal_moon_nakshatra_idx,
        'source': ctx.tarabala_chandrabala_source,
        'note': (
            'real transit-Moon tarabala/chandrabala via panchang_engine (JL-016)'
            if is_live else
            'honest 0.5 placeholder — natal Moon data or live ephemeris unavailable '
            'for this candidate; NOT a computed score (JL-016)'
        ),
    }

    # Only surface the enrichment hook when this record is still riding the
    # placeholder — a live-computed record has nothing left to enrich.
    follow_up_hook = {
        'action': 'enrich_tarabala_chandrabala',
        'requires': 'transit_moon_nakshatra_at_window_start',
        'natal_moon_nakshatra_idx': ctx.natal_moon_nakshatra_idx,
        'action_class': ctx.action_class,
        'fructification_anchor': ctx.fructification_anchor,
        'consumed_by': 'P7B_prashna_followup_scheduler',
        'already_satisfied': is_live,
    }

    derivation = {
        'action_class':              ctx.action_class,
        'panchanga_score':           ctx.panchanga_score,
        'chart_personalization':     personalization,
        'personalization_graha':     graha,
        'condition_score':           ctx.condition_score,
        'transit_score':             ctx.transit_score,
        'tarabala_score':            ctx.tarabala_score,
        'chandrabala_score':         ctx.chandrabala_score,
        'tarabala_chandrabala_source': ctx.tarabala_chandrabala_source,
        'adversity_penalty':         penalty,
        'obstruction_id':            ctx.overlapping_obstruction_id,
        'linked_anchor_id':          ctx.linked_anchor_id,
        'composite_formula':         'panchanga × personalization × tara_candra^0.5 × (1−penalty)',
        'fructification_rules':      ctx.fructification_rules,
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
        tarabala_chandrabala_jsonb=tarabala_chandrabala,
        significators_met_jsonb=significators_met,
        fructification_anchor=ctx.fructification_anchor,
        follow_up_hook_jsonb=follow_up_hook,
    )
