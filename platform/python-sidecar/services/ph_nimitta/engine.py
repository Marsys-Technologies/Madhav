"""
ph_nimitta engine v2 — predictive anchor derivation (DB-free, purely functional).

8 axes + 5 elevations per D8/D11/D21/D37/D38. Called from the writer which
supplies pre-fetched DB data. The engine never reads from the DB.

BA-P5B: G-LADDER (compute_confidence_range) REPLACED by structured posterior model.
  posterior = base_rate × promise_lift × activation_lift × trigger_lift × robustness_mod

JL-009 OPEN GATE: base_rate priors in brahma_event_ontology are PLACEHOLDER values
(default 0.10). The native MUST review and ratify these before any anchor freeze.
Do NOT treat computed posteriors as calibrated until JL-009 is closed.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Optional

from brahmagyan.phala.confidence_vocab import STRUCTURAL_NOT_YET_EMPIRICAL

__all__ = [
    'NimittaContext',
    'AnchorLiftVector',
    'StructuredFalsifier',
    'AnchorRecord',
    'compute_posterior',
    'compute_magnitude',
    'derive_karmic_frame',
    'derive_malleability',
    'derive_anchor_from_convergence',
    'derive_anchor_from_bhavishya',
    'derive_anchor_from_discovery',
]

# ── date coercion ─────────────────────────────────────────────────────────────


def _coerce_date(v) -> Optional[date]:
    """Coerce a psycopg date/datetime or ISO string to a plain date; None on failure.

    R6 fix: the 3 call sites below previously only coerced the `str` case, silently
    passing through a raw `datetime.datetime` untouched whenever the source column is
    `timestamptz` rather than `date`. A `datetime` window_end downstream compared against
    a plain-`date` birth_date (the writer's T-5 pre-birth gate) then crashed with
    "TypeError: can't compare datetime.datetime to datetime.date" — this cascaded to fail
    every asset downstream of ph_nimitta. Handling `datetime` explicitly here closes that
    gap at the one shared source instead of three separately-drifting inline blocks.
    """
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


# ── domain validation ─────────────────────────────────────────────────────────

# CR-66 root cause #1 (wealth=0): this set was a STALE vocabulary
# ({career, relationship, financial, spiritual, health, transition, psychological})
# that agreed with NEITHER (a) the upstream kala_convergence / kala_bhavishya /
# bodha_discoveries / bodha_msr_signals domain values (career, relationship, wealth,
# spirituality, health, character, general) NOR (b) the phala_anchors_domain_canonical
# DB CHECK constraint. Consequence: every 'wealth' / 'spirituality' / 'character' source
# row fell through to 'transition' (so wealth anchors could NEVER exist), and any row that
# DID map to 'financial'/'spiritual'/'psychological' would have violated the DB CHECK and
# aborted the whole asset — the writer only ever survived on the accidental intersection
# {career, relationship, health, transition}. This is now the canonical DB vocabulary
# (migration: phala_anchors_domain_canonical), so upstream domains pass through unchanged.
_VALID_DOMAINS = frozenset({
    'career', 'wealth', 'relationship', 'progeny', 'health',
    'education', 'family', 'residence', 'travel', 'spirituality',
    'character', 'transition', 'general',
})

# Legacy/synonym inputs → canonical DB vocabulary. Keeps any caller or older source that
# still emits the pre-CR-66 words landing on a VALID canonical value (never a CHECK-violating
# one), instead of silently collapsing to 'transition'. Not a fabrication: these are exact
# 1:1 renamings of the same domain concept.
_DOMAIN_SYNONYMS = {
    'financial': 'wealth',
    'money': 'wealth',
    'finance': 'wealth',
    'spiritual': 'spirituality',
    'dharma': 'spirituality',
    'psychological': 'character',
    'psychology': 'character',
    'mind': 'character',
    'marriage': 'relationship',
    'spouse': 'relationship',
    'children': 'progeny',
    'progeny_children': 'progeny',
}

_AYANAMSHA_ROBUSTNESS_DEFAULT = 3

# CR-66 root cause #3: a window already closed in the past is historical/retrodictive, not
# a "near" (upcoming) prediction. ~3 years is the near horizon.
_NEAR_HORIZON_DAYS = 1096


def _canonical_domain(*candidates: Optional[str]) -> str:
    """Return first valid canonical domain from candidates; else 'transition'.

    Applies _DOMAIN_SYNONYMS first so a legacy/synonym word (e.g. 'financial') resolves to
    its canonical DB value ('wealth') rather than falling through to 'transition'.
    """
    for c in candidates:
        if not c:
            continue
        cl = c.lower().strip()
        cl = _DOMAIN_SYNONYMS.get(cl, cl)
        if cl in _VALID_DOMAINS:
            return cl
    return 'transition'


def _horizon_tier(window_end: Optional[date]) -> str:
    """Map a window_end to the DB-legal horizon tier ('near' | 'lifetime').

    CR-66 root cause #3: the prior inline test (`window_end < today + 3yr → 'near'`) labeled
    EVERY past window 'near', so the writer's stale-'near' clip gate then rejected 100% of the
    convergence anchors (whose top-scoring windows lie in the past) — leaving zero convergence
    anchors. Corrected banding:
      • window_end already in the past          → 'lifetime' (historical / retrodictive)
      • window_end within ~3 years of today      → 'near'     (a genuine upcoming prediction)
      • window_end further out / unknown          → 'lifetime'
    """
    if window_end is None:
        return 'lifetime'
    today = date.today()
    if window_end < today:
        return 'lifetime'
    if window_end <= today + timedelta(days=_NEAR_HORIZON_DAYS):
        return 'near'
    return 'lifetime'


def _resolve_event_type(event_class_id: Optional[str], domain: str, anchor_source: str) -> str:
    """Structured event type: prefer event_class_id (from bodha_pratijna), else synthesize."""
    if event_class_id:
        return event_class_id
    return f'{domain}_{anchor_source}_event'


# ── V1: magnitude from rarity_years × effective_score ────────────────────────

def compute_magnitude(
    rarity_years: float | None,
    effective_score: float | None,
) -> tuple[str, str]:
    ry = float(rarity_years or 1.0)
    es = float(effective_score or 0.5)
    rarity_score = min(1.0, ry / 10.0)
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


# ── V3: karmic-arc framing from root graha ───────────────────────────────────

_KARMIC_FRAME: dict[str, tuple[str, str]] = {
    'saturn':  ('debt_surfacing',      'Saturn ripens karmic debt through restriction and discipline.'),
    'ketu':    ('debt_surfacing',      'Ketu compels completion of past-life obligations.'),
    'rahu':    ('desire_amplification','Rahu intensifies desire and drives worldly ambition.'),
    'mars':    ('energy_directive',    'Mars channels raw force into action and assertion.'),
    'sun':     ('authority_assertion', 'Sun crystallises identity and claims recognition.'),
    'moon':    ('emotional_flux',      'Moon cycles the mind through feeling and receptivity.'),
    'mercury': ('discernment_push',    'Mercury sharpens the intellect and drives communication.'),
    'jupiter': ('grace_expansion',     'Jupiter grants wisdom-gifts and expands dharmic possibility.'),
    'venus':   ('pleasure_integration','Venus weaves beauty and relationship into life-fabric.'),
}


def derive_karmic_frame(root_graha: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not root_graha:
        return None, None
    pair = _KARMIC_FRAME.get(root_graha.lower().strip())
    if pair is None:
        return None, None
    return pair


# ── V4: actionability / malleability ─────────────────────────────────────────

_INFLUENCEABLE_DOMAINS = {'career', 'health', 'transition', 'wealth'}


def derive_malleability(domain: str, magnitude: str, direction: str) -> str:
    if magnitude == 'pivotal' and direction == 'suppressed':
        return 'fated'
    if domain in _INFLUENCEABLE_DOMAINS and magnitude in ('minor', 'moderate'):
        return 'influenceable'
    return 'semi_influenceable'


# ── BA-P5B: structured posterior model ───────────────────────────────────────

@dataclass
class AnchorLiftVector:
    """Decomposed posterior product — written to lift_vector JSONB per anchor."""
    base_rate:                    float
    promise_lift:                 float
    activation_lift:              float
    trigger_lift:                 float
    ayanamsha_robustness_modifier: float
    posterior:                    float

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class StructuredFalsifier:
    """Machine-evaluable refutation specification per BA-P5B spec."""
    event_class_id:       Optional[str]
    magnitude_floor:      str    # 'minor' | 'moderate' | 'major' | 'pivotal'
    domain:               str
    window_end:           Optional[str]   # ISO date string
    attestation_required: str    # 'lel_entry' | 'documented_external' | 'native_attestation'
    refutation_condition:  str
    confirmation_condition: str

    def as_text(self) -> str:
        deadline = self.window_end or 'end of window'
        return (
            f"REFUTED if no {self.domain} event of magnitude ≥ {self.magnitude_floor} "
            f"is independently documented by {deadline}. "
            f"CONFIRMED if a {self.domain}-domain event of matching magnitude is recorded "
            f"in the Life-Event Log before {deadline}. "
            f"Attestation: {self.attestation_required}."
        )

    def as_dict(self) -> dict:
        return asdict(self)


def _promise_lift(grade: float, status: str) -> float:
    """bodha_pratijna grade [0..10] → Bayesian lift factor.

    Fix (SHABDA-SHUDDHI lane L4 / R6): corrects a sign-inversion bug in the
    'denied' branch and adds an explicit 'no_evidence' case.

    Correct semantics:
      'promised' / 'conditional':
        grade is promise strength; grade=0 -> 1.0x, grade=10 -> 2.5x.
      'denied':
        grade is denial strength; grade=0 -> 1.0 (neutral, no evidence),
        grade=10 -> 0.1 (floor — promise is modifier, never a gate per R6).
      'no_evidence':
        lift = 1.0 always (no information -> no modification).

    Previous bug: denied branch used max(0.20, 1.0 - (grade/10.0) * 0.80)
    which compressed the dynamic range and left 'no_evidence' falling into
    the promised/conditional formula (non-neutral lift).
    """
    if status == 'no_evidence':
        return 1.0
    if status == 'denied':
        # grade=0 -> 1.0 (neutral: no denial evidence); grade=10 -> 0.1 (floor)
        return max(0.1, 1.0 - grade / 10.0)
    # 'promised' / 'conditional': grade=0 -> 1.0x; grade=10 -> 2.5x
    return 1.0 + (grade / 10.0) * 1.50


def _activation_lift(multi_system_count: int) -> float:
    """ka_yojaka multi_system_confirmation_count → lift factor. 5+ systems → 2.0x."""
    return 1.0 + min(multi_system_count, 5) / 5.0


def _trigger_lift(av_transit_potency: float) -> float:
    """AV-transit potency [0..1] → lift factor. Full potency → 1.5x."""
    return 1.0 + max(0.0, min(1.0, av_transit_potency)) * 0.50


def compute_posterior(
    base_rate: float,
    pratijna_grade: float,
    pratijna_status: str,
    multi_system_confirmation_count: int,
    av_transit_potency: float,
    ayanamsha_robustness: int = _AYANAMSHA_ROBUSTNESS_DEFAULT,
) -> tuple[float, AnchorLiftVector]:
    """
    Bayesian product model per BA-P5B spec.

    posterior = base_rate × promise_lift × activation_lift × trigger_lift × robustness_mod

    Returns (posterior, AnchorLiftVector) — posterior clamped [0.02, 0.95].

    JL-009: base_rate priors are PLACEHOLDERS until native review and freeze.
    """
    promise    = _promise_lift(pratijna_grade, pratijna_status)
    activation = _activation_lift(multi_system_confirmation_count)
    trigger    = _trigger_lift(av_transit_potency)
    rob_mod    = 0.80 + (min(max(0, int(ayanamsha_robustness)), 5) / 5.0) * 0.20

    raw       = float(base_rate) * promise * activation * trigger * rob_mod
    posterior = round(min(0.95, max(0.02, raw)), 4)

    lift = AnchorLiftVector(
        base_rate=round(float(base_rate), 4),
        promise_lift=round(promise, 4),
        activation_lift=round(activation, 4),
        trigger_lift=round(trigger, 4),
        ayanamsha_robustness_modifier=round(rob_mod, 4),
        posterior=posterior,
    )
    return posterior, lift


def _build_structured_falsifier(
    domain: str,
    magnitude: str,
    window_end: Optional[date],
    event_class_id: Optional[str] = None,
) -> StructuredFalsifier:
    deadline_str = str(window_end) if window_end else None
    return StructuredFalsifier(
        event_class_id=event_class_id,
        magnitude_floor=magnitude or 'minor',
        domain=domain,
        window_end=deadline_str,
        attestation_required='lel_entry',
        refutation_condition=(
            f"No {domain} event of magnitude ≥ {magnitude or 'minor'} "
            f"independently documented by {deadline_str or 'end of window'}."
        ),
        confirmation_condition=(
            f"{domain.capitalize()}-domain event of matching magnitude recorded "
            f"in Life-Event Log before {deadline_str or 'end of window'}."
        ),
    )


def _posterior_confidence_band(posterior: float) -> tuple[float, float]:
    """Map posterior → (confidence_low, confidence_high) for backward compat with DB schema.

    The phala_anchors schema carries confidence_low/confidence_high with CHECK <= 0.80.
    We derive a ±0.05 band around posterior, clamped to [0.01, 0.80].
    The true point estimate is stored in the separate `posterior` column (migration 398).
    """
    low  = round(max(0.01, min(0.75, posterior - 0.05)), 3)
    high = round(min(0.80, max(0.01, posterior + 0.05)), 3)
    return low, high


# ── context dataclass ─────────────────────────────────────────────────────────

@dataclass
class NimittaContext:
    """Pre-fetched DB data for one convergence/bhavishya/discovery row (writer-supplied)."""
    # from bodha_msr_signals
    signal_domain:           Optional[str]  = None
    signal_signature_class:  Optional[str]  = None
    signal_salience:         Optional[float] = None
    # from bodha_cgm_paths (top path for this signal)
    cgm_path_ids:            list[str]      = field(default_factory=list)
    cgm_centrality:          Optional[float] = None
    root_graha:              Optional[str]  = None
    # from bodha_signal_embeddings precedent search
    precedent_signal_ids:    list[str]      = field(default_factory=list)
    precedent_dates:         list[str]      = field(default_factory=list)
    # from bodha_contradictions
    contradiction_contested: bool           = False
    contradiction_thread:    Optional[str]  = None
    contradiction_net:       Optional[str]  = None
    # from dasha consensus service (U1)
    dasha_consensus_count:   int            = 0
    # from school consensus (U4)
    school_consensus_jsonb:  Optional[dict] = None
    # cross-ayanamsha robustness [0..5]
    ayanamsha_robustness:    int            = _AYANAMSHA_ROBUSTNESS_DEFAULT
    # BA-P5B: posterior model inputs (writer-supplied from pratijna + activation + transit)
    event_class_id:                  Optional[str] = None
    pratijna_grade:                  float         = 5.0   # bodha_pratijna grade [0..10]
    pratijna_status:                 str           = 'conditional'
    multi_system_confirmation_count: int           = 0     # ka_yojaka enrichment
    av_transit_potency:              float         = 0.0   # AV/SAV gate score [0..1]
    base_rate:                       float         = 0.10  # brahma_event_ontology prior (JL-009)


# ── AnchorRecord ──────────────────────────────────────────────────────────────

@dataclass
class AnchorRecord:
    anchor_source:          str
    convergence_id:         Optional[int]   = None
    discovery_id:           Optional[str]   = None
    bhavishya_id:           Optional[int]   = None
    signal_id:              Optional[str]   = None
    subsystem_source:       Optional[str]   = None
    event_type:             Optional[str]   = None
    direction:              str             = 'mixed'
    domain:                 str             = 'transition'
    horizon_tier:           Optional[str]   = None
    window_start:           Optional[date]  = None
    peak_date:              Optional[date]  = None
    window_end:             Optional[date]  = None
    magnitude:              Optional[str]   = None
    magnitude_basis:        Optional[str]   = None
    # confidence band — backward compat with phala_anchors schema (derived from posterior)
    confidence_low:         Optional[float] = None
    confidence_high:        Optional[float] = None
    confidence_basis:       str             = STRUCTURAL_NOT_YET_EMPIRICAL
    # BA-P5B: true posterior point estimate + lift decomposition
    posterior:              Optional[float] = None
    lift_vector:            Optional[dict]  = None
    # V3-V5
    karmic_frame:           Optional[str]   = None
    karmic_note:            Optional[str]   = None
    malleability:           Optional[str]   = None
    counterfactual_jsonb:   Optional[dict]  = None
    contradiction_jsonb:    Optional[dict]  = None
    causal_chain_jsonb:     Optional[dict]  = None
    precedent_refs_jsonb:   Optional[dict]  = None
    dasha_consensus_count:  Optional[int]   = None
    school_consensus_jsonb: Optional[dict]  = None
    ayanamsha_robustness:   Optional[int]   = None
    falsifier:              str             = ''
    structured_falsifier:   Optional[dict]  = None   # StructuredFalsifier.as_dict()
    derivation_ledger_jsonb: dict           = field(default_factory=dict)
    source_citation:        str             = ''


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

    domain    = _canonical_domain(ctx.signal_domain, cf.get('domain'), row.get('domain'))
    evt_type  = _resolve_event_type(ctx.event_class_id, domain, 'convergence')

    # P0-11 (SUDDHA-VACA D4_GRADE_INVERSION): a missing or malformed direction value
    # must never silently launder into the favorable-sounding 'elevated'. The
    # phala_anchors.direction column is NOT NULL CHECK IN ('elevated','suppressed','mixed')
    # (migration 330), so an honest null/'unknown' sentinel cannot be persisted — the
    # DB-legal honest-unknown value is 'mixed' (neutral, not favorable), which is already
    # this file's own convention: AnchorRecord.direction defaults to 'mixed', and
    # derive_anchor_from_bhavishya's prob_tier resolution below falls back to 'mixed' for
    # any value it doesn't recognize. This mirrors that same convention for convergence rows.
    raw_dir = cf.get('direction')
    direction = raw_dir if raw_dir in ('elevated', 'suppressed', 'mixed') else 'mixed'

    rarity_years    = row.get('rarity_years')
    effective_score = row.get('convergence_score') or row.get('effective_score', 0.5)
    magnitude, magnitude_basis = compute_magnitude(rarity_years, effective_score)

    # BA-P5B: structured posterior (replaces G-LADDER)
    posterior, lift = compute_posterior(
        base_rate=ctx.base_rate,
        pratijna_grade=ctx.pratijna_grade,
        pratijna_status=ctx.pratijna_status,
        multi_system_confirmation_count=ctx.multi_system_confirmation_count,
        av_transit_potency=ctx.av_transit_potency,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
    )
    conf_low, conf_high = _posterior_confidence_band(posterior)

    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)
    malleability = derive_malleability(domain, magnitude, direction)
    counterfactual = {'influenceable_via': 'remedy_or_transit', 'basis': 'malleability_class'}

    contradiction = {
        'contested': ctx.contradiction_contested,
        'countervailing_thread': ctx.contradiction_thread,
        'net_direction': ctx.contradiction_net or direction,
    }

    causal_chain = {
        'root_graha': ctx.root_graha,
        'cgm_path_ids': ctx.cgm_path_ids,
        'centrality': ctx.cgm_centrality,
    }

    precedent = {
        'nearest_signal_ids': ctx.precedent_signal_ids,
        'precedent_dates': ctx.precedent_dates,
    }

    peak_date = _coerce_date(row.get('peak_date'))
    window_start = _coerce_date(row.get('window_start'))
    window_end = _coerce_date(row.get('window_end'))

    sf = _build_structured_falsifier(domain, magnitude, window_end, ctx.event_class_id)

    derivation_ledger = {
        'anchor_source':     'convergence',
        'convergence_id':    row.get('convergence_id'),
        'signal_id':         str(row.get('signal_id') or ''),
        'axes_applied':      ['1', '2', '3', '5', '6', '7'],
        'elevations':        ['V1', 'V2', 'V3', 'V4', 'V5'],
        'posterior_inputs':  {
            'base_rate':                    ctx.base_rate,
            'pratijna_grade':               ctx.pratijna_grade,
            'pratijna_status':              ctx.pratijna_status,
            'multi_system_confirmation':    ctx.multi_system_confirmation_count,
            'av_transit_potency':           ctx.av_transit_potency,
            'n_independent_currents':       n_independent,
        },
    }

    return AnchorRecord(
        anchor_source='convergence',
        convergence_id=row.get('convergence_id'),
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type=evt_type,
        direction=direction,
        domain=domain,
        horizon_tier=_horizon_tier(window_end),
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        posterior=posterior,
        lift_vector=lift.as_dict(),
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
        falsifier=sf.as_text(),
        structured_falsifier=sf.as_dict(),
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
    domain = _canonical_domain(row.get('domain'), ctx.signal_domain)

    prob_tier = str(row.get('probability_tier') or 'moderate').lower()
    direction = 'elevated' if 'positive' in prob_tier or 'high' in prob_tier else (
        'suppressed' if 'low' in prob_tier or 'negative' in prob_tier else 'mixed')

    es = float(row.get('effective_score') or 0.5)
    magnitude, magnitude_basis = compute_magnitude(None, es)

    # BA-P5B: structured posterior
    posterior, lift = compute_posterior(
        base_rate=ctx.base_rate,
        pratijna_grade=ctx.pratijna_grade,
        pratijna_status=ctx.pratijna_status,
        multi_system_confirmation_count=ctx.multi_system_confirmation_count,
        av_transit_potency=ctx.av_transit_potency,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
    )
    conf_low, conf_high = _posterior_confidence_band(posterior)

    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)
    malleability = derive_malleability(domain, magnitude, direction)

    peak_date = _coerce_date(row.get('peak_date'))
    window_start = _coerce_date(row.get('window_start'))
    window_end = _coerce_date(row.get('window_end'))

    # inherit bhavishya's existing falsifier text; wrap in structured form if absent
    inherited_text = str(row.get('falsifiability') or '')
    if inherited_text:
        sf_text = inherited_text
        sf_dict = {
            'inherited': True,
            'original_text': inherited_text,
            'event_class_id': ctx.event_class_id,
        }
    else:
        sf = _build_structured_falsifier(domain, magnitude, window_end, ctx.event_class_id)
        sf_text = sf.as_text()
        sf_dict = sf.as_dict()

    derivation_ledger = {
        'anchor_source':       'bhavishya',
        'bhavishya_id':        row.get('id'),
        'convergence_id':      row.get('convergence_id'),
        'signal_id':           str(row.get('signal_id') or ''),
        'source_chain':        row.get('source_chain'),
        'outcome_recorded':    row.get('outcome_recorded'),
        'inherited_narrative': row.get('narrative'),
        'axes_applied':        ['1', '2', '3', '7'],
        'elevations':          ['V1', 'V2', 'V3', 'V4', 'V5'],
        'note':                'kala_bhavishya inherited per D37; falsifiability preserved',
        'posterior_inputs':    {
            'base_rate':                 ctx.base_rate,
            'pratijna_grade':            ctx.pratijna_grade,
            'pratijna_status':           ctx.pratijna_status,
            'multi_system_confirmation': ctx.multi_system_confirmation_count,
            'av_transit_potency':        ctx.av_transit_potency,
        },
    }

    return AnchorRecord(
        anchor_source='bhavishya',
        bhavishya_id=row.get('id'),
        convergence_id=row.get('convergence_id'),
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type=_resolve_event_type(ctx.event_class_id, domain, 'bhavishya'),
        direction=direction,
        domain=domain,
        horizon_tier='lifetime',
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        posterior=posterior,
        lift_vector=lift.as_dict(),
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
        falsifier=sf_text,
        structured_falsifier=sf_dict,
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=f"kala_bhavishya/{row.get('id')}",
    )


def derive_anchor_from_discovery(
    row: dict,
    ctx: NimittaContext,
) -> AnchorRecord:
    """
    Axis 4: bodha_discoveries as anchor source.
    row keys: id, signal_id, domain, discovery_type, surface_depth_delta,
              why_an_acharya_misses_it, falsifier_jsonb, confidence_score,
              peak_date, window_start, window_end
    """
    domain = _canonical_domain(row.get('domain'), ctx.signal_domain)

    cs = float(row.get('confidence_score') or 0.5)
    magnitude, magnitude_basis = compute_magnitude(None, cs)

    # BA-P5B: structured posterior
    posterior, lift = compute_posterior(
        base_rate=ctx.base_rate,
        pratijna_grade=ctx.pratijna_grade,
        pratijna_status=ctx.pratijna_status,
        multi_system_confirmation_count=ctx.multi_system_confirmation_count,
        av_transit_potency=ctx.av_transit_potency,
        ayanamsha_robustness=ctx.ayanamsha_robustness,
    )
    conf_low, conf_high = _posterior_confidence_band(posterior)

    karmic_frame, karmic_note = derive_karmic_frame(ctx.root_graha)
    malleability = derive_malleability(domain, magnitude, 'elevated')

    peak_date = _coerce_date(row.get('peak_date'))
    window_start = _coerce_date(row.get('window_start'))
    window_end = _coerce_date(row.get('window_end'))

    falsifier_data = row.get('falsifier_jsonb') or {}
    existing_text = (falsifier_data.get('statement') if isinstance(falsifier_data, dict) else None)
    if existing_text:
        sf_text = existing_text
        sf_dict = {
            'inherited': True,
            'original_text': existing_text,
            'event_class_id': ctx.event_class_id,
        }
    else:
        sf = _build_structured_falsifier(domain, magnitude, window_end, ctx.event_class_id)
        sf_text = sf.as_text()
        sf_dict = sf.as_dict()

    derivation_ledger = {
        'anchor_source':            'discovery',
        'discovery_id':             str(row.get('id') or ''),
        'signal_id':                str(row.get('signal_id') or ''),
        'discovery_type':           row.get('discovery_type'),
        'surface_depth_delta':      row.get('surface_depth_delta'),
        'why_an_acharya_misses_it': row.get('why_an_acharya_misses_it'),
        'axes_applied':             ['1', '2', '4', '5', '7'],
        'elevations':               ['V1', 'V2', 'V3', 'V4', 'V5'],
        'posterior_inputs':         {
            'base_rate':                 ctx.base_rate,
            'pratijna_grade':            ctx.pratijna_grade,
            'pratijna_status':           ctx.pratijna_status,
            'multi_system_confirmation': ctx.multi_system_confirmation_count,
            'av_transit_potency':        ctx.av_transit_potency,
        },
    }

    return AnchorRecord(
        anchor_source='discovery',
        discovery_id=str(row.get('id')) if row.get('id') else None,
        signal_id=str(row.get('signal_id')) if row.get('signal_id') else None,
        event_type=_resolve_event_type(ctx.event_class_id, domain, 'discovery'),
        direction='elevated',
        domain=domain,
        horizon_tier=_horizon_tier(window_end),
        window_start=window_start,
        peak_date=peak_date,
        window_end=window_end,
        magnitude=magnitude,
        magnitude_basis=magnitude_basis,
        confidence_low=conf_low,
        confidence_high=conf_high,
        posterior=posterior,
        lift_vector=lift.as_dict(),
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
        falsifier=sf_text,
        structured_falsifier=sf_dict,
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=f"bodha_discoveries/{row.get('id')}",
    )
