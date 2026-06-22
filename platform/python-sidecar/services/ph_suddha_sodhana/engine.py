"""
ph_suddha_sodhana engine — DB-free cleansed anchor disposition (D43 safety rail).

D43 SAFETY RAIL (hard): staged_revision_jsonb proposes corrections for native review.
The writer MUST NEVER set revision_approved_by or revision_applied_at.
These fields can only be updated by a future operator action after explicit
native sign-off. Any writer that sets them is a build-time bug.

Disposition logic:
  clean            — 0 flags from phala_sodhana
  flagged          — only minor/informational flags (usable with caveat)
  staged_revision  — any major/critical flag (correction staged, pending review)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    'FlagSummary',
    'SuddhaContext',
    'SuddhaRecord',
    'D43RevisionError',
    'classify_cleanliness',
    'build_staged_revision',
    'derive_suddha_record',
]


class D43RevisionError(RuntimeError):
    """Raised if caller attempts to set revision_approved_by or revision_applied_at."""


@dataclass
class FlagSummary:
    """Aggregated flags for one anchor (writer supplies from phala_sodhana query)."""
    anchor_id:              str
    sodhana_ids:            list[str]           = field(default_factory=list)
    critical_count:         int = 0
    major_count:            int = 0
    minor_count:            int = 0
    informational_count:    int = 0
    flag_details:           list[dict] = field(default_factory=list)
    # Each flag_detail: {sodhana_id, anomaly_type, detected_field, expected, observed, recommendation}


@dataclass
class SuddhaContext:
    """Pre-fetched flags per anchor (writer supplies; engine is DB-free)."""
    chart_id:       str
    anchor_flags:   list[FlagSummary] = field(default_factory=list)


@dataclass
class SuddhaRecord:
    anchor_id:                      str
    cleanliness_status:             str     # 'clean' | 'flagged' | 'staged_revision'
    critical_flag_count:            int
    major_flag_count:               int
    minor_flag_count:               int
    flag_ids_jsonb:                 Optional[list]
    staged_revision_jsonb:          Optional[list]  # proposals; native must approve
    # D43: writer NEVER sets these — always None from engine
    revision_approved_by:           None = None     # LOCKED: None from engine
    revision_applied_at:            None = None     # LOCKED: None from engine
    confidence_delta_if_applied:    Optional[float] = None
    magnitude_delta_if_applied:     Optional[str]   = None
    derivation_ledger_jsonb:        dict = field(default_factory=dict)
    source_citation:                str  = ''


def classify_cleanliness(flags: FlagSummary) -> str:
    """Derive cleanliness_status from flag severity counts."""
    if flags.critical_count > 0 or flags.major_count > 0:
        return 'staged_revision'
    elif flags.minor_count > 0 or flags.informational_count > 0:
        return 'flagged'
    return 'clean'


def build_staged_revision(flags: FlagSummary) -> Optional[list]:
    """
    Build staged_revision_jsonb: list of {field, current_behavior, proposed_fix, basis}.
    Only non-None for major/critical flags.
    NEVER sets revision_approved_by or revision_applied_at (D43).
    """
    if flags.critical_count == 0 and flags.major_count == 0:
        return None
    proposals = []
    for detail in flags.flag_details:
        sev = detail.get('severity', 'minor')
        if sev in ('critical', 'major'):
            proposals.append({
                'sodhana_id':       detail.get('sodhana_id'),
                'field':            detail.get('detected_field'),
                'anomaly_type':     detail.get('anomaly_type'),
                'current_value':    detail.get('observed'),
                'proposed_basis':   detail.get('expected'),
                'recommendation':   detail.get('recommendation'),
                'approval_required': True,
                'auto_apply':       False,  # D43: always False
            })
    return proposals if proposals else None


def _estimate_confidence_delta(flags: FlagSummary) -> Optional[float]:
    """
    Rough delta estimate for confidence_high if all confidence_inflation flags were fixed.
    Returns negative delta (correction would reduce confidence).
    """
    total = 0.0
    n = 0
    for detail in flags.flag_details:
        if detail.get('anomaly_type') == 'confidence_inflation':
            try:
                obs = float(detail.get('observed', 0) or 0)
                exp_text = str(detail.get('expected', '') or '')
                # extract first float from expected text
                import re
                match = re.search(r'[\d.]+', exp_text)
                if match:
                    exp = float(match.group())
                    total += exp - obs
                    n += 1
            except (ValueError, TypeError):
                pass
    return round(total / n, 3) if n > 0 else None


def _estimate_magnitude_delta(flags: FlagSummary) -> Optional[str]:
    """Describe proposed magnitude correction if magnitude_drift flags exist."""
    for detail in flags.flag_details:
        if detail.get('anomaly_type') == 'magnitude_drift':
            return 'downgrade_magnitude_one_level'
    return None


def derive_suddha_record(ctx: SuddhaContext, flags: FlagSummary) -> SuddhaRecord:
    """
    Derive one SuddhaRecord for one anchor. DB-free.
    D43 safety rail: revision_approved_by and revision_applied_at are NEVER set here.
    """
    status   = classify_cleanliness(flags)
    staged   = build_staged_revision(flags)
    conf_d   = _estimate_confidence_delta(flags) if staged else None
    mag_d    = _estimate_magnitude_delta(flags)  if staged else None

    derivation = {
        'anchor_id':            flags.anchor_id,
        'cleanliness_status':   status,
        'critical_flags':       flags.critical_count,
        'major_flags':          flags.major_count,
        'minor_flags':          flags.minor_count,
        'd43_safety_rail':      'revision_approved_by and revision_applied_at set to NULL by engine (never auto-applied)',
    }

    return SuddhaRecord(
        anchor_id=flags.anchor_id,
        cleanliness_status=status,
        critical_flag_count=flags.critical_count,
        major_flag_count=flags.major_count,
        minor_flag_count=flags.minor_count,
        flag_ids_jsonb=flags.sodhana_ids if flags.sodhana_ids else None,
        staged_revision_jsonb=staged,
        revision_approved_by=None,   # D43: LOCKED
        revision_applied_at=None,    # D43: LOCKED
        confidence_delta_if_applied=conf_d,
        magnitude_delta_if_applied=mag_d,
        derivation_ledger_jsonb=derivation,
        source_citation=f'ph_suddha_sodhana/{ctx.chart_id}/{flags.anchor_id}',
    )
