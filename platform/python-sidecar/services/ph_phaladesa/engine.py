"""
ph_phaladesa engine — DB-free domain result declaration synthesis.

B.11 WHOLE-CHART-READ: writer pre-fetches all L2 Bodha synthesis references
(MSR domain scores, CDLM linkage summary, CGM paths) before calling this engine.
The engine then combines phala_* data with Bodha context to produce each
domain's declaration structure.

DETERMINISTIC-FIRST: all logic here is pure Python. No LLM.
MODEL POLICY: narration_status is set to 'pending'; narration_model is None.
A separate async narration step (Gemini/DeepSeek only) populates narration_jsonb.
Anthropic is BANNED from narration (model policy).

PERMITTED_NARRATION_MODELS constant is the authoritative allowlist.
Any code that passes an Anthropic model name to narration_model is a policy
violation and will be caught by the DB CHECK constraint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

__all__ = [
    'PERMITTED_NARRATION_MODELS',
    'BANNED_MODEL_PREFIXES',
    'DomainAnchorSummary',
    'SpilloverSummary',
    'BodhaSynthesisContext',
    'PhaladesakContext',
    'PhaladosaRecord',
    'NarrationModelError',
    'rank_top_anchor',
    'derive_phaladesa_record',
    'derive_phaladesa_for_chart',
]

# Model policy allowlist (Gemini/DeepSeek only)
# SUDDHA-VACA Phase C §2: 'gpt-4o' / 'gpt-4-turbo' (OpenAI) were previously included
# here despite the comment's own stated "Gemini/DeepSeek only" policy — a standing
# contamination hole letting an OpenAI model pass any permission check against this
# frozenset. Removed to match the file's own documented intent.
PERMITTED_NARRATION_MODELS: frozenset[str] = frozenset({
    'gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
    'deepseek-chat', 'deepseek-r1',
})

# Any model whose ID starts with one of these prefixes is BANNED
BANNED_MODEL_PREFIXES: tuple[str, ...] = (
    'claude-', 'anthropic/', 'claude3', 'claude2',
)

_ALL_DOMAINS = ('career', 'wealth', 'health', 'relationship', 'spirituality', 'character', 'transition')


class NarrationModelError(ValueError):
    """Raised if a banned (Anthropic) narration model is detected."""


@dataclass
class DomainAnchorSummary:
    """Aggregated anchor data for one domain (writer-supplied)."""
    domain:                 str
    anchor_ids:             list[str]       = field(default_factory=list)
    clean_ids:              list[str]       = field(default_factory=list)
    staged_revision_ids:    list[str]       = field(default_factory=list)
    anomaly_flag_count:     int = 0
    # top anchor fields
    top_anchor_id:          Optional[str]   = None
    window_start:           Optional[date]  = None
    window_end:             Optional[date]  = None
    peak_date:              Optional[date]  = None
    magnitude:              Optional[str]   = None
    confidence_low:         Optional[float] = None
    confidence_high:        Optional[float] = None
    malleability:           Optional[str]   = None
    precedent_refs_jsonb:   Optional[dict]  = None
    contradiction_summary:  Optional[dict]  = None
    pramana_window_status:  Optional[str]   = None
    evidence_type:          Optional[str]   = None


@dataclass
class SpilloverSummary:
    """CDLM-derived spillover info for one domain pair (writer-supplied)."""
    source_domain:          str
    target_domain:          str
    relationship_type:      str   # 'contagion' | 'conflict'
    spillover_confidence:   float


@dataclass
class BodhaSynthesisContext:
    """Pre-fetched L2 Bodha synthesis for B.11 compliance (writer-supplied)."""
    msr_domain_scores:      dict[str, float]    = field(default_factory=dict)
    cdlm_linkage_summary:   dict[str, list]     = field(default_factory=dict)
    cgm_paths_by_domain:    dict[str, list]     = field(default_factory=dict)
    # True if any Bodha data was available; writer must set this
    bodha_consulted:        bool = False


@dataclass
class PhaladesakContext:
    """All inputs for one chart's ph_phaladesa derivation (writer-supplied)."""
    chart_id:               str
    domain_summaries:       dict[str, DomainAnchorSummary]  = field(default_factory=dict)
    spillovers:             list[SpilloverSummary]           = field(default_factory=list)
    mitigation_domains:     set[str]                        = field(default_factory=set)
    muhurta_domains:        set[str]                        = field(default_factory=set)
    bodha:                  BodhaSynthesisContext            = field(default_factory=BodhaSynthesisContext)


@dataclass
class PhaladosaRecord:
    domain:                     str
    anchor_count:               int
    clean_anchor_count:         int
    staged_revision_count:      int
    anomaly_flag_count:         int
    top_anchor_id:              Optional[str]
    prediction_window_start:    Optional[date]
    prediction_window_end:      Optional[date]
    peak_date:                  Optional[date]
    magnitude:                  Optional[str]
    confidence_low:             Optional[float]
    confidence_high:            Optional[float]
    malleability:               Optional[str]
    spillover_domains_jsonb:    Optional[list]
    incoming_spillover_count:   int
    mitigation_available:       bool
    muhurta_available:          bool
    pramana_window_status:      Optional[str]
    evidence_type:              Optional[str]
    precedent_refs_jsonb:       Optional[dict]
    contradiction_summary_jsonb: Optional[dict]
    derivation_summary_jsonb:   dict
    narration_status:           str = 'pending'   # writer always sets this
    narration_model:            None = None        # LOCKED: set by narration step only
    derivation_ledger_jsonb:    dict = field(default_factory=dict)
    source_citation:            str = ''


def validate_narration_model(model: Optional[str]) -> None:
    """
    Raise NarrationModelError if model is an Anthropic model or not in the allowlist.
    Called at narration-step time, not at writer build time.
    """
    if model is None:
        return  # pending — fine
    model_lower = model.lower()
    for prefix in BANNED_MODEL_PREFIXES:
        if model_lower.startswith(prefix):
            raise NarrationModelError(
                f"Model policy violation: Anthropic model '{model}' is BANNED for ph_phaladesa narration. "
                f"Use one of: {sorted(PERMITTED_NARRATION_MODELS)}"
            )
    if model not in PERMITTED_NARRATION_MODELS:
        raise NarrationModelError(
            f"Model '{model}' is not in the permitted narration models list. "
            f"Permitted: {sorted(PERMITTED_NARRATION_MODELS)}"
        )


def rank_top_anchor(summary: DomainAnchorSummary) -> Optional[str]:
    """
    Return the top anchor_id: prefer clean anchors by confidence_high.
    If summary already has top_anchor_id set (writer-supplied), trust it.
    """
    return summary.top_anchor_id


def derive_phaladesa_record(
    domain: str,
    ctx: PhaladesakContext,
) -> PhaladosaRecord:
    """
    Derive one PhaladosaRecord for a given domain. DB-free; purely structural.
    Narration_status is always 'pending'; narration_model is always None.
    """
    summary = ctx.domain_summaries.get(domain) or DomainAnchorSummary(domain=domain)

    # Spillover outgoing (this domain → others)
    spillover_out = [
        {
            'target_domain':     s.target_domain,
            'relationship_type': s.relationship_type,
            'spillover_confidence': s.spillover_confidence,
        }
        for s in ctx.spillovers
        if s.source_domain == domain
    ]

    # Spillover incoming (other domains → this)
    incoming_count = sum(1 for s in ctx.spillovers if s.target_domain == domain)

    # B.11: Bodha synthesis cross-reference
    msr_score = ctx.bodha.msr_domain_scores.get(domain)
    cdlm_links = ctx.bodha.cdlm_linkage_summary.get(domain, [])
    cgm_paths  = ctx.bodha.cgm_paths_by_domain.get(domain, [])

    derivation_summary = {
        'domain':               domain,
        'anchor_count':         len(summary.anchor_ids),
        'clean_count':          len(summary.clean_ids),
        'top_anchor_id':        summary.top_anchor_id,
        'spillover_out_count':  len(spillover_out),
        'incoming_count':       incoming_count,
        'b11_msr_score':        msr_score,
        'b11_cdlm_link_count':  len(cdlm_links),
        'b11_cgm_path_count':   len(cgm_paths),
        'b11_bodha_consulted':  ctx.bodha.bodha_consulted,
        'narration_model_policy': 'gemini_or_deepseek_only (anthropic_banned)',
    }

    derivation_ledger = {
        'chart_id':             ctx.chart_id,
        'domain':               domain,
        'b11_whole_chart_read': ctx.bodha.bodha_consulted,
        'deterministic_first':  True,
        'narration_model':      None,
        'model_policy':         'BANNED: anthropic/* PERMITTED: gemini/deepseek/gpt',
    }

    return PhaladosaRecord(
        domain=domain,
        anchor_count=len(summary.anchor_ids),
        clean_anchor_count=len(summary.clean_ids),
        staged_revision_count=len(summary.staged_revision_ids),
        anomaly_flag_count=summary.anomaly_flag_count,
        top_anchor_id=summary.top_anchor_id,
        prediction_window_start=summary.window_start,
        prediction_window_end=summary.window_end,
        peak_date=summary.peak_date,
        magnitude=summary.magnitude,
        confidence_low=summary.confidence_low,
        confidence_high=summary.confidence_high,
        malleability=summary.malleability,
        spillover_domains_jsonb=spillover_out if spillover_out else None,
        incoming_spillover_count=incoming_count,
        mitigation_available=(domain in ctx.mitigation_domains),
        muhurta_available=(domain in ctx.muhurta_domains),
        pramana_window_status=summary.pramana_window_status,
        evidence_type=summary.evidence_type,
        precedent_refs_jsonb=summary.precedent_refs_jsonb,
        contradiction_summary_jsonb=summary.contradiction_summary,
        derivation_summary_jsonb=derivation_summary,
        narration_status='pending',   # LOCKED: writer never triggers narration
        narration_model=None,         # LOCKED: narration step sets this (never writer)
        derivation_ledger_jsonb=derivation_ledger,
        source_citation=f'ph_phaladesa/{ctx.chart_id}/{domain}',
    )


def derive_phaladesa_for_chart(ctx: PhaladesakContext) -> list[PhaladosaRecord]:
    """Derive one PhaladosaRecord per domain (7 total)."""
    return [derive_phaladesa_record(domain, ctx) for domain in _ALL_DOMAINS]
