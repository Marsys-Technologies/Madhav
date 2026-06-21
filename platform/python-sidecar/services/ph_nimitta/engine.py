"""
ph_nimitta engine — predictive anchor derivation (DB-free, purely functional).

8 axes + 5 elevations per D8/D11/D21/D37/D38. Called from the writer which
supplies pre-fetched DB data. The engine never reads from the DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

__all__ = [
    'NimittaContext',
    'AnchorRecord',
    'compute_confidence_range',
    'compute_magnitude',
    'derive_karmic_frame',
    'derive_malleability',
    'derive_domain',
    'derive_event_type',
    'generate_falsifier',
    'derive_anchor_from_convergence',
    'derive_anchor_from_bhavishya',
    'derive_anchor_from_discovery',
]

# ── domain mappings ───────────────────────────────────────────────────────────

_DOMAIN_KEYWORDS: list[tuple[str, str]] = [
    ('CAREER', 'career'), ('PROFESSION', 'career'), ('WORK', 'career'),
    ('FINANCIAL', 'financial'), ('WEALTH', 'financial'), ('MONEY', 'financial'),
    ('HEALTH', 'health'), ('MEDICAL', 'health'), ('BODY', 'health'),
    ('RELATION', 'relationship'), ('MARRIAGE', 'relationship'), ('PARTNER', 'relationship'),
    ('SPIRITUAL', 'spiritual'), ('DHARMA', 'spiritual'), ('MOKSHA', 'spiritual'),
    ('PSYCHOLOG', 'psychological'), ('MENTAL', 'psychological'), ('EMOTIONAL', 'psychological'),
    ('TRANSITION', 'transition'), ('RELOCATION', 'transition'), ('CHANGE', 'transition'),
]

# Axis 7: cross-ayanamsha consistency → 0-5 int (derived from constituent_factors or default 3)
_AYANAMSHA_ROBUSTNESS_DEFAULT = 3

# Axis 2 / G-LADDER (D21): confidence ceiling per ICC level
def compute_confidence_range(
    convergence_score: float,
    n_independent: int,
    ayanamsha_robustness: int,
) -> tuple[float, float]:
    """
    G-LADDER: f = max(0.5, convergence_score); ceiling 0.50 + 0.05×min(n,6);
    robustness factor 0.80–1.00; final range mid ± 0.10, both ≤ 0.80.
    """
    f = max(0.5, float(convergence_score or 0.0))
    ladder_ceiling = min(0.80, 0.50 + 0.05 * min(int(n_independent or 1), 6))
    rob = min(5, max(0, int(ayanamsha_robustness or _AYANAMSHA_ROBUSTNESS_DEFAULT)))
    rob_factor = 0.80 + 0.04 * rob         # 0.80 … 1.00
    mid = min(f, ladder_ceiling, 0.80) * rob_factor
    low  = max(0.0, round(mid - 0.10, 3))
    high = min(0.80, round(mid + 0.10, 3))
    return low, high


# V1: magnitude from rarity_years × effective_score
def compute_magnitude(
    rarity_years: float | None,
    effective_score: float | None,
) -> tuple[str, str]:
    ry = float(rarity_years or 1.0)
    es = float(effective_score or 0.5)
    rarity_score = min(1.0, ry / 10.0)   # 10 yr → full rarity
    combined = rarity_score * es
    if combined >= 0.60:
        tier = 'pivotal'
    elif combined >= 0.40:
        tier = 'major'
    elif combined >= 0.20:
        tier = 'moderate'
    else:
        tier = 'minor'
    basis = f'rarity_years={ry:.1f}yr × effective_score={es:.3f} = {combined:.3f} → {tier}'
    return tier, basis


# V3: karmic-arc framing from root graha lordship
_KARMIC_FRAME: dict[str, tuple[str, str]] = {
    'saturn':  ('debt_surfacing',      'Saturn ripens karmic debt through restriction and discipline.'),
    'ketu':    ('debt_surfacing',      'Ketu compels completion of past-life obligations.'),
    'jupiter': ('reward_ripening',     'Jupiter\'s grace delivers merit accumulated across cycles.'),
    'rahu':    ('desire_entanglement', 'Rahu magnifies desire and brings novelty at karmic cost.'),
    'mars':    ('effort_reward',       'Mars delivers proportional to sustained directed effort.'),
    'sun':     ('effort_reward',       'Sun rewards authority and self-expression with recognition.'),
    'venus':   ('relational_karma',    'Venus unfolds relational and aesthetic karma through pleasure and bond.'),
    'moon':    ('relational_karma',    'Moon ripens emotional bonds and nurturing patterns from the past.'),
    'mercury': ('effort_reward',       'Mercury rewards refined skill and discriminative intelligence.'),
}

def derive_karmic_frame(root_graha: str | None) -> tuple[str | None, str | None]:
    if not root_graha:
        return None, None
    pair = _KARMIC_FRAME.get(root_graha.lower().strip())
    if pair is None:
        return None, None
    return pair


# V4: actionability / malleability
_INFLUENCEABLE_DOMAINS = {'career', 'health', 'transition', 'financial'}

def derive_malleability(domain: str, magnitude: str, direction: str) -> str:
    if magnitude == 'pivotal' and direction == 'suppressed':
        return 'fated'
    if domain in _INFLUENCEABLE_DOMAINS and magnitude in ('minor', 'moderate'):
        return 'influenceable'
    return 'semi_influenceable'


# Axis 1: domain + event_type derivation from signal metadata
def derive_domain(signature_class: str | None, signal_domain: str | None) -> str:
    combined = ((signature_class or '') + ' ' + (signal_domain or '')).upper()
    for keyword, mapped in _DOMAIN_KEYWORDS:
        if keyword in combined:
            return mapped
    return 'transition'   # neutral fallback


def derive_event_type(signature_class: str | None, anchor_source: str) -> str:
    sc = (signature_class or '').upper()
    if 'CAREER' in sc or 'PROFESSION' in sc:   return 'career_shift'
    if 'HEALTH' in sc or 'MEDICAL' in sc:      return 'health_episode'
    if 'RELATION' in sc or 'MARRIAGE' in sc:   return 'relationship_event'
    if 'FINANCIAL' in sc or 'WEALTH' in sc:    return 'financial_event'
    if 'SPIRITUAL' in sc or 'DHARMA' in sc:    return 'spiritual_opening'
    if 'PSYCHOLOG' in sc or 'MENTAL' in sc:    return 'psychological_shift'
    if 'TRANSITION' in sc or 'RELOCAT' in sc:  return 'life_transition'
    return f'{anchor_source}_event'


# Falsifier generator (machine-evaluable, domain-templated)
def generate_falsifier(
    domain: str,
    event_type: str,
    direction: str,
    peak_date: date | None,
    window_end: date | None,
) -> str:
    dir_word = {'elevated': 'positive', 'suppressed': 'negative', 'mixed': 'ambivalent'}.get(direction, 'notable')
    deadline = str(window_end or peak_date or 'end of window')
    return (
        f"REFUTED if no {dir_word} {domain} {event_type or 'development'} is independently "
        f"documented by {deadline}. CONFIRMED if a {domain}-domain event matching the direction "
        f"is recorded in the Life-Event Log before {deadline}."
    )


# ── context dataclass ─────────────────────────────────────────────────────────

@dataclass
class NimittaContext:
    """Pre-fetched DB data for one convergence/bhavishya/discovery row (writer-supplied)."""
    # from bodha_msr_signals
    signal_domain:           Optional[str] = None
    signal_signature_class:  Optional[str] = None
    signal_salience:         Optional[float] = None
    # from bodha_cgm_paths (top path for this signal)
    cgm_path_ids:            list[str] = field(default_factory=list)
    cgm_centrality:          Optional[float] = None
    root_graha:              Optional[str] = None
    # from bodha_signal_embeddings precedent search
    precedent_signal_ids:    list[str] = field(default_factory=list)
    precedent_dates:         list[str] = field(default_factory=list)
    # from bodha_contradictions
    contradiction_contested: bool = False
    contradiction_thread:    Optional[str] = None
    contradiction_net:       Optional[str] = None
    # from dasha consensus service (U1)
    dasha_consensus_count:   int = 0
    # from school consensus (U4)
    school_consensus_jsonb:  Optional[dict] = None
    # cross-ayanamsha robustness
    ayanamsha_robustness:    int = _AYANAMSHA_ROBUSTNESS_DEFAULT


# ── AnchorRecord ──────────────────────────────────────────────────────────────

@dataclass
class AnchorRecord:
    anchor_source:          str
    convergence_id:         Optional[int]  = None
    discovery_id:           Optional[str]  = None
    bhavishya_id:           Optional[int]  = None
    signal_id:              Optional[str]  = None
    subsystem_source:       Optional[str]  = None
    event_type:             Optional[str]  = None
    direction:              str            = 'mixed'
    domain:                 str            = 'transition'
    horizon_tier:           Optional[str]  = None
    window_start:           Optional[date] = None
    peak_date:              Optional[date] = None
    window_end:             Optional[date] = None
    magnitude:              Optional[str]  = None
    magnitude_basis:        Optional[str]  = None
    confidence_low:         Optional[float] = None
    confidence_high:        Optional[float] = None
    confidence_basis:       str            = 'structural_not_yet_empirical'
    karmic_frame:           Optional[str]  = None
    karmic_note:            Optional[str]  = None
    malleability:           Optional[str]  = None
    counterfactual_jsonb:   Optional[dict] = None
    contradiction_jsonb:    Optional[dict] = None
    causal_chain_jsonb:     Optional[dict] = None
    precedent_refs_jsonb:   Optional[dict] = None
    dasha_consensus_count:  Optional[int]  = None
    school_consensus_jsonb: Optional[dict] = None
    ayanamsha_robustness:   Optional[int]  = None
    falsifier:              str            = ''
    derivation_ledger_jsonb: dict          = field(default_factory=dict)
    source_citation:        str            = ''


# ── derivation entry points ───────────────────────────────────────────────────

def derive_anchor_from_convergence(
    row: dict,
    ctx: NimittaContext,
    n_independent: int,
) -> AnchorRecord:
    """
    Derive an AnchorRecord from one kala_convergence row.
    row keys: convergence_id, signal_id, mode, peak_date, window_start, window_end,
              convergence_score, rarity_years, constituent_factors (jsonb), source_citation
    """
    cf = row.get('constituent_factors') or {}
    sig_class = ctx.signal_signature_class or cf.get('signature_class', '')

    domain    = derive_domain(sig_class, ctx.signal_domain)
    evt_type  = derive_event_type(sig_class, 'convergence')

    # direction from constituent_factors or default
    raw_dir = cf.get('direction', 'elevated')
    direction = raw_dir if raw_dir in ('elevated', 'suppressed', 'mixed') else 'elevated'

    # V1 magnitude
    rarity_years    = row.get('rarity_years')
    effective_score = row.get('convergence_score') or row.get('effective_score', 0.5)
    magnitude, magnitude_basis = compute_magnitude(rarity_years, effective_score)

    # Axis 2 / V2 confidence range
    conf_low, conf_high = compute_confidence_range(
        float(row.get('convergence_score') or 0.5),
        n_independent,
        ctx.ayanamsha_robustness,
    )

    # V3 karmic frame
    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)

    # V4 malleability
    malleability = derive_malleability(domain, magnitude, direction)
    counterfactual = {'influenceable_via': 'remedy_or_transit', 'basis': 'malleability_class'}

    # V5 contradiction
    contradiction = {
        'contested': ctx.contradiction_contested,
        'countervailing_thread': ctx.contradiction_thread,
        'net_direction': ctx.contradiction_net or direction,
    }

    # Axis 3 causal chain
    causal_chain = {
        'root_graha': ctx.root_graha,
        'cgm_path_ids': ctx.cgm_path_ids,
        'centrality': ctx.cgm_centrality,
    }

    # Axis 5 precedent
    precedent = {
        'nearest_signal_ids': ctx.precedent_signal_ids,
        'precedent_dates': ctx.precedent_dates,
    }

    falsifier = generate_falsifier(domain, evt_type, direction,
                                   row.get('peak_date'), row.get('window_end'))

    derivation_ledger = {
        'anchor_source':    'convergence',
        'convergence_id':   row.get('convergence_id'),
        'signal_id':        str(row.get('signal_id') or ''),
        'axes_applied':     ['1','2','3','5','6','7'],
        'elevations':       ['V1','V2','V3','V4','V5'],
        'g_ladder_inputs':  {'convergence_score': float(row.get('convergence_score') or 0), 'n_independent': n_independent},
    }

    peak_date = row.get('peak_date')
    if isinstance(peak_date, str):
        try: peak_date = date.fromisoformat(peak_date)
        except ValueError: peak_date = None

    window_start = row.get('window_start')
    if isinstance(window_start, str):
        try: window_start = date.fromisoformat(window_start)
        except ValueError: window_start = None

    window_end = row.get('window_end')
    if isinstance(window_end, str):
        try: window_end = date.fromisoformat(window_end)
        except ValueError: window_end = None

    return AnchorRecord(
        anchor_source='convergence',
        convergence_id=row.get('convergence_id'),
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type=evt_type,
        direction=direction,
        domain=domain,
        horizon_tier='near' if window_end and window_end < date.today().replace(year=date.today().year + 3) else 'lifetime',
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        karmic_frame=karmic_frame,
        karmic_note=karmic_note,
        malleability=malleability,
        counterfactual_jsonb=counterfactual,
        contradiction_jsonb=contradiction,
        causal_chain_jsonb=causal_chain,
        precedent_refs_jsonb=precedent,
        dasha_consensus_count=ctx.dasha_consensus_count,
        school_consensus_jsonb=ctx.school_consensus_jsonb,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
        falsifier=falsifier,
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=str(row.get('source_citation') or f"kala_convergence/{row.get('convergence_id')}"),
    )


def derive_anchor_from_bhavishya(
    row: dict,
    ctx: NimittaContext,
) -> AnchorRecord:
    """
    Inherit kala_bhavishya projection as an anchor (D37).
    row keys: id, domain, peak_date, window_start, window_end, probability_tier,
              effective_score, falsifiability, source_chain, signal_id, convergence_id,
              outcome_recorded, narrative
    """
    domain = (row.get('domain') or 'transition').lower()
    if domain not in ('career','relationship','financial','spiritual','health','transition','psychological'):
        domain = 'transition'

    # inherit bhavishya direction from probability tier
    prob_tier = str(row.get('probability_tier') or 'moderate').lower()
    direction = 'elevated' if 'positive' in prob_tier or 'high' in prob_tier else (
        'suppressed' if 'low' in prob_tier or 'negative' in prob_tier else 'mixed')

    es = float(row.get('effective_score') or 0.5)
    magnitude, magnitude_basis = compute_magnitude(None, es)  # bhavishya has no rarity_years

    conf_low, conf_high = compute_confidence_range(es, 3, ctx.ayanamsha_robustness)
    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)
    malleability = derive_malleability(domain, magnitude, direction)

    peak_date = row.get('peak_date')
    if isinstance(peak_date, str):
        try: peak_date = date.fromisoformat(peak_date)
        except ValueError: peak_date = None

    window_start = row.get('window_start')
    if isinstance(window_start, str):
        try: window_start = date.fromisoformat(window_start)
        except ValueError: window_start = None

    window_end = row.get('window_end')
    if isinstance(window_end, str):
        try: window_end = date.fromisoformat(window_end)
        except ValueError: window_end = None

    # inherit bhavishya's existing falsifier (not overwritten)
    inherited_falsifier = str(row.get('falsifiability') or '')
    if not inherited_falsifier:
        inherited_falsifier = generate_falsifier(domain, 'inherited_projection', direction, peak_date, window_end)

    # preserve outcome hook for L5 (ph_pramana will carry this forward)
    derivation_ledger = {
        'anchor_source':        'bhavishya',
        'bhavishya_id':         row.get('id'),
        'convergence_id':       row.get('convergence_id'),
        'signal_id':            str(row.get('signal_id') or ''),
        'source_chain':         row.get('source_chain'),
        'outcome_recorded':     row.get('outcome_recorded'),
        'inherited_narrative':  row.get('narrative'),
        'axes_applied':         ['1','2','3','7'],
        'elevations':           ['V1','V2','V3','V4','V5'],
        'note':                 'kala_bhavishya inherited per D37; falsifiability preserved',
    }

    return AnchorRecord(
        anchor_source='bhavishya',
        bhavishya_id=row.get('id'),
        convergence_id=row.get('convergence_id'),
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type='inherited_projection',
        direction=direction,
        domain=domain,
        horizon_tier='lifetime',  # bhavishya is lifetime-scope
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        karmic_frame=karmic_frame,
        karmic_note=karmic_note,
        malleability=malleability,
        counterfactual_jsonb={'inherited': True, 'original_outcome_hook': row.get('outcome_recorded')},
        contradiction_jsonb={
            'contested': ctx.contradiction_contested,
            'countervailing_thread': ctx.contradiction_thread,
            'net_direction': ctx.contradiction_net or direction,
        },
        causal_chain_jsonb={'root_graha': ctx.root_graha, 'cgm_path_ids': ctx.cgm_path_ids},
        precedent_refs_jsonb={'nearest_signal_ids': ctx.precedent_signal_ids},
        dasha_consensus_count=ctx.dasha_consensus_count,
        school_consensus_jsonb=ctx.school_consensus_jsonb,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
        falsifier=inherited_falsifier,
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=f"kala_bhavishya/{row.get('id')}",
    )


def derive_anchor_from_discovery(
    row: dict,
    ctx: NimittaContext,
) -> AnchorRecord:
    """
    Axis 4: bodha_discoveries (1,505) as anchor source.
    row keys: id, signal_id, domain, discovery_type, surface_depth_delta, why_an_acharya_misses_it,
              falsifier_jsonb, confidence_score, peak_date, window_start, window_end
    """
    domain = (row.get('domain') or 'transition').lower()
    if domain not in ('career','relationship','financial','spiritual','health','transition','psychological'):
        domain = 'transition'

    cs = float(row.get('confidence_score') or 0.5)
    magnitude, magnitude_basis = compute_magnitude(None, cs)
    conf_low, conf_high = compute_confidence_range(cs, 2, ctx.ayanamsha_robustness)
    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)
    malleability = derive_malleability(domain, magnitude, 'elevated')

    peak_date = row.get('peak_date')
    if isinstance(peak_date, str):
        try: peak_date = date.fromisoformat(peak_date)
        except ValueError: peak_date = None

    window_start = row.get('window_start')
    if isinstance(window_start, str):
        try: window_start = date.fromisoformat(window_start)
        except ValueError: window_start = None

    window_end = row.get('window_end')
    if isinstance(window_end, str):
        try: window_end = date.fromisoformat(window_end)
        except ValueError: window_end = None

    falsifier_data = row.get('falsifier_jsonb') or {}
    falsifier_str = (falsifier_data.get('statement') if isinstance(falsifier_data, dict) else None) or \
                    generate_falsifier(domain, 'discovery_event', 'elevated', peak_date, window_end)

    derivation_ledger = {
        'anchor_source':            'discovery',
        'discovery_id':             str(row.get('id') or ''),
        'signal_id':                str(row.get('signal_id') or ''),
        'discovery_type':           row.get('discovery_type'),
        'surface_depth_delta':      row.get('surface_depth_delta'),
        'why_an_acharya_misses_it': row.get('why_an_acharya_misses_it'),
        'axes_applied':             ['1','2','4','5','7'],
        'elevations':               ['V1','V2','V3','V4','V5'],
    }

    return AnchorRecord(
        anchor_source='discovery',
        discovery_id=str(row.get('id')) if row.get('id') else None,
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type=derive_event_type(ctx.signal_signature_class, 'discovery'),
        direction='elevated',
        domain=domain,
        horizon_tier='near',
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        karmic_frame=karmic_frame,
        karmic_note=karmic_note,
        malleability=malleability,
        counterfactual_jsonb={'basis': 'discovery_seeded'},
        contradiction_jsonb={
            'contested': ctx.contradiction_contested,
            'countervailing_thread': ctx.contradiction_thread,
            'net_direction': ctx.contradiction_net or 'elevated',
        },
        causal_chain_jsonb={'root_graha': ctx.root_graha, 'cgm_path_ids': ctx.cgm_path_ids},
        precedent_refs_jsonb={'nearest_signal_ids': ctx.precedent_signal_ids},
        dasha_consensus_count=ctx.dasha_consensus_count,
        school_consensus_jsonb=ctx.school_consensus_jsonb,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
        falsifier=falsifier_str,
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=f"bodha_discoveries/{row.get('id')}",
    )
