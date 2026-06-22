"""
ph_pratikara engine — DB-free derivation for mitigation program (P1–P5).

CONSUMES bodha_rm_remedy_prescriptions; never authors remedy text.
All topological sort + conflict-exclusion done here; DB reads in writer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

__all__ = [
    'RemedyPrescription',
    'MitigationContext',
    'MitigationRecord',
    'topo_sort_prescriptions',
    'exclude_incompatibles',
    'tier_prescriptions',
    'cross_tradition_count',
    'derive_intensity_tier',
    'derive_mitigation_record',
]

_TRADITION_KEYS = ['vedic', 'tantra', 'ayurvedic', 'vastu', 'lal_kitab', 'modern']

# P4: intensity from severity × magnitude
_SEVERITY_MAGNITUDE_TO_INTENSITY: dict[tuple[str, str], str] = {
    ('low',    'minor'):    'light',
    ('low',    'moderate'): 'light',
    ('low',    'major'):    'moderate',
    ('low',    'pivotal'):  'moderate',
    ('medium', 'minor'):    'light',
    ('medium', 'moderate'): 'moderate',
    ('medium', 'major'):    'moderate',
    ('medium', 'pivotal'):  'intensive',
    ('high',   'minor'):    'moderate',
    ('high',   'moderate'): 'intensive',
    ('high',   'major'):    'intensive',
    ('high',   'pivotal'):  'intensive',
}


@dataclass
class RemedyPrescription:
    prescription_id:            str
    tradition:                  str
    remedy_category:            str
    classical_strength_rating:  float = 0.5
    resonance_match_score:      float = 0.5
    feasibility_score:          float = 0.5
    estimated_cost_inr_range:   dict = field(default_factory=dict)
    estimated_time_minutes:     Optional[int] = None
    requires_acharya_review:    bool = False
    prerequisite_ids:           list[str] = field(default_factory=list)
    incompatible_ids:           list[str] = field(default_factory=list)
    recommended_hora:           Optional[str] = None
    recommended_choghadiya:     Optional[str] = None
    pranapratishtha:            bool = False
    classical_citation:         str = ''


def topo_sort_prescriptions(prescriptions: list[RemedyPrescription]) -> list[str]:
    """
    Topological sort respecting prerequisite_ids.
    Returns ordered list of prescription_ids. Cycles → break by original order.
    """
    id_set = {p.prescription_id for p in prescriptions}
    prereqs = {p.prescription_id: [x for x in p.prerequisite_ids if x in id_set] for p in prescriptions}

    visited: set[str] = set()
    order: list[str] = []

    def visit(pid: str, stack: set[str]) -> None:
        if pid in stack:
            return  # cycle guard
        if pid in visited:
            return
        stack.add(pid)
        for dep in prereqs.get(pid, []):
            visit(dep, stack)
        stack.discard(pid)
        visited.add(pid)
        order.append(pid)

    for p in prescriptions:
        visit(p.prescription_id, set())

    return order


def exclude_incompatibles(
    prescriptions: list[RemedyPrescription],
    sorted_ids: list[str],
) -> list[str]:
    """
    Remove later-scheduled items that are incompatible with already-scheduled ones.
    Greedy: keep earlier items, drop conflicting later ones.
    """
    p_map = {p.prescription_id: p for p in prescriptions}
    scheduled: list[str] = []
    scheduled_set: set[str] = set()

    for pid in sorted_ids:
        p = p_map.get(pid)
        if p is None:
            continue
        conflicts = set(p.incompatible_ids) & scheduled_set
        if conflicts:
            continue  # skip: incompatible with something already scheduled
        scheduled.append(pid)
        scheduled_set.add(pid)

    return scheduled


def tier_prescriptions(
    prescriptions: list[RemedyPrescription],
    scheduled_ids: list[str],
) -> dict:
    """P1: group scheduled prescriptions into free/low_cost/high_investment tiers."""
    p_map = {p.prescription_id: p for p in prescriptions}
    tiers: dict[str, list[dict]] = {'free': [], 'low_cost': [], 'high_investment': []}

    for pid in scheduled_ids:
        p = p_map.get(pid)
        if p is None:
            continue
        cost_range = p.estimated_cost_inr_range
        max_cost = cost_range.get('max_inr', 0) if isinstance(cost_range, dict) else 0
        entry = {
            'prescription_id':      pid,
            'tradition':            p.tradition,
            'remedy_category':      p.remedy_category,
            'cost_range_inr':       cost_range,
            'estimated_time_min':   p.estimated_time_minutes,
            'requires_acharya':     p.requires_acharya_review,
            'citation':             p.classical_citation,
        }
        if max_cost == 0:
            tiers['free'].append(entry)
        elif max_cost <= 5000:
            tiers['low_cost'].append(entry)
        else:
            tiers['high_investment'].append(entry)

    return tiers


def cross_tradition_count(prescriptions: list[RemedyPrescription], scheduled_ids: list[str]) -> int:
    """P5: count distinct traditions represented in scheduled prescriptions."""
    p_map = {p.prescription_id: p for p in prescriptions}
    traditions_seen: set[str] = set()
    for pid in scheduled_ids:
        p = p_map.get(pid)
        if p:
            traditions_seen.add(p.tradition.lower())
    return len(traditions_seen & set(_TRADITION_KEYS))


def derive_intensity_tier(obstruction_severity: str, anchor_magnitude: Optional[str]) -> tuple[str, str]:
    """P4: match remedy intensity to obstruction severity × anchor magnitude."""
    sev = (obstruction_severity or 'medium').lower()
    mag = (anchor_magnitude or 'moderate').lower()
    tier = _SEVERITY_MAGNITUDE_TO_INTENSITY.get((sev, mag), 'moderate')
    basis = f'severity={sev} × anchor_magnitude={mag} → {tier}'
    return tier, basis


@dataclass
class MitigationContext:
    obstruction_id:         Optional[int]
    obstruction_severity:   str
    obstruction_window_start: Optional[date]
    obstruction_window_end:   Optional[date]
    afflicting_graha:       Optional[str]
    linked_anchor_id:       Optional[str]
    anchor_magnitude:       Optional[str]
    prescriptions:          list[RemedyPrescription] = field(default_factory=list)


@dataclass
class MitigationRecord:
    obstruction_id:             Optional[int]
    linked_anchor_id:           Optional[str]
    afflicting_graha:           Optional[str]
    obstruction_severity:       Optional[str]
    program_jsonb:              dict
    tradition_options_jsonb:    dict
    recommended_tier_jsonb:     dict
    intensity_tier:             str
    proportionality_basis:      str
    initiation_muhurta_ref:     Optional[str]  # set post-facto by writer
    window_start:               Optional[date]
    window_end:                 Optional[date]
    re_evaluation_date:         date
    outcome_hook_jsonb:         dict
    classical_citation:         str
    cross_tradition_corroboration: int
    derivation_ledger_jsonb:    dict
    source_citation:            str


def derive_mitigation_record(ctx: MitigationContext) -> MitigationRecord:
    """Derive one MitigationRecord from pre-fetched context (no DB calls)."""
    prescriptions = ctx.prescriptions

    # P2: topological sort + conflict exclusion
    sorted_ids    = topo_sort_prescriptions(prescriptions)
    scheduled_ids = exclude_incompatibles(prescriptions, sorted_ids)

    # P1: tier
    tiers = tier_prescriptions(prescriptions, scheduled_ids)

    # P5: cross-tradition
    ctc = cross_tradition_count(prescriptions, scheduled_ids)

    # P5: tradition options grouped
    p_map = {p.prescription_id: p for p in prescriptions}
    trad_map: dict[str, list[str]] = {t: [] for t in _TRADITION_KEYS}
    for pid in scheduled_ids:
        p = p_map.get(pid)
        if p:
            key = p.tradition.lower()
            if key in trad_map:
                trad_map[key].append(pid)

    # P4: intensity
    intensity_tier, prop_basis = derive_intensity_tier(ctx.obstruction_severity, ctx.anchor_magnitude)

    # P4: re-evaluation date = window_end (or 90 days if unknown)
    if ctx.obstruction_window_end:
        re_eval = ctx.obstruction_window_end
    else:
        from datetime import date as _date
        re_eval = _date.today() + timedelta(days=90)

    # P4: outcome hook (falsifiable, for L5)
    outcome_hook = {
        'question':         f"Did the {ctx.obstruction_severity} obstruction ease by {re_eval}?",
        'obstruction_id':   ctx.obstruction_id,
        'linked_anchor_id': ctx.linked_anchor_id,
        'evaluation_date':  str(re_eval),
        'outcome_recorded': None,  # filled by L5 Mimamsa
    }

    # program structure for P2
    program = {
        'scheduled_ids':  scheduled_ids,
        'sequence_basis': 'prerequisite_topo_sort + incompatible_exclusion',
        'total_scheduled': len(scheduled_ids),
    }

    # classical citation: pick from first prescription or generic
    citation = next(
        (p.classical_citation for p in prescriptions if p.classical_citation),
        'Brihat Parashara Hora Shastra — Upaya chapter'
    )

    derivation = {
        'obstruction_id':    ctx.obstruction_id,
        'linked_anchor_id':  ctx.linked_anchor_id,
        'prescription_count': len(prescriptions),
        'scheduled_count':   len(scheduled_ids),
        'intensity_tier':    intensity_tier,
        'ctc':               ctc,
        'p_elevations':      ['P1','P2','P4','P5'],
    }

    return MitigationRecord(
        obstruction_id=ctx.obstruction_id,
        linked_anchor_id=ctx.linked_anchor_id,
        afflicting_graha=ctx.afflicting_graha,
        obstruction_severity=ctx.obstruction_severity,
        program_jsonb=program,
        tradition_options_jsonb=trad_map,
        recommended_tier_jsonb=tiers,
        intensity_tier=intensity_tier,
        proportionality_basis=prop_basis,
        initiation_muhurta_ref=None,   # writer sets this after ph_muhurta insert
        window_start=ctx.obstruction_window_start,
        window_end=ctx.obstruction_window_end,
        re_evaluation_date=re_eval,
        outcome_hook_jsonb=outcome_hook,
        classical_citation=citation,
        cross_tradition_corroboration=ctc,
        derivation_ledger_jsonb=derivation,
        source_citation=f"ph_pratikara/{ctx.obstruction_id or 'anchor'}/{ctx.linked_anchor_id or 'none'}",
    )
