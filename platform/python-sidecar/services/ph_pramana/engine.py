"""
ph_pramana engine — DB-free falsifiability scaffolding (D5 / L4-L5 boundary).

D5 NO-SCORING gate (hard): this engine and the writer it backs MUST NEVER
produce calibration_score, posterior_probability, accuracy_rate, Brier_score,
hit_rate, or any other empirical accuracy metric.

These engines are exclusively structural:
  - Extract and structure the observable criteria from each anchor's falsifier
  - Classify window status relative to today (pending / open / past_window)
  - Link life_event_log entries that fall within the anchor's window (pre-fetched)
  - Classify evidence_strength_label (direct / indirect / proxy) from evidence type
  - Build the falsification_ledger derivation chain

L5 Mimamsa will read phala_pramana to compute calibration. L4 never does.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

__all__ = [
    'AnchorForPramana',
    'LelEntry',
    'PramanaContext',
    'PramanaRecord',
    'D5ViolationError',
    'classify_window_status',
    'parse_observable_criteria',
    'classify_evidence_strength',
    'derive_pramana_records',
]


class D5ViolationError(RuntimeError):
    """Raised if any caller attempts to set a scoring field on PramanaRecord."""


_REFUTED_PAT = re.compile(r'REFUTED\s+if\s+(.+?)(?:\.|CONFIRMED)', re.IGNORECASE | re.DOTALL)
_CONFIRMED_PAT = re.compile(r'CONFIRMED\s+if\s+(.+?)(?:\.|$)', re.IGNORECASE | re.DOTALL)
_DEADLINE_PAT = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')


@dataclass
class AnchorForPramana:
    """Subset of phala_anchors needed by ph_pramana."""
    anchor_id:              str
    domain:                 str
    anchor_source:          str
    falsifier:              str
    window_start:           Optional[date] = None
    window_end:             Optional[date] = None
    peak_date:              Optional[date] = None
    magnitude:              Optional[str]  = None
    confidence_high:        Optional[float] = None
    derivation_ledger_jsonb: dict = field(default_factory=dict)


@dataclass
class LelEntry:
    """One life_event_log row (pre-fetched by writer)."""
    lel_id:         int
    event_date:     date
    domain:         str
    event_summary:  str
    outcome_valence: Optional[str] = None  # 'positive' | 'negative' | 'neutral'
    lel_jsonb:      dict = field(default_factory=dict)


@dataclass
class PramanaContext:
    """All anchor+LEL data for one chart (writer-supplied; engine is DB-free)."""
    chart_id:           str
    today:              date
    anchors:            list[AnchorForPramana] = field(default_factory=list)
    lel_entries:        list[LelEntry]         = field(default_factory=list)


@dataclass
class PramanaRecord:
    """
    One phala_pramana row.
    D5: no calibration_score, no posterior_probability, no accuracy_rate.
    """
    anchor_id:                  str
    evidence_type:              str   # see CHECK constraint
    evidence_strength_label:    str   # 'direct' | 'indirect' | 'proxy'
    falsifier_text:             str
    observable_criteria_jsonb:  dict
    window_status:              str   # 'pending' | 'open' | 'past_window'
    lel_entry_id:               Optional[int] = None
    lel_entry_jsonb:            Optional[dict] = None
    linked_sodhana_id:          Optional[str] = None
    derivation_ledger_jsonb:    dict = field(default_factory=dict)
    source_citation:            str = ''


def classify_window_status(
    window_start: Optional[date],
    window_end: Optional[date],
    today: date,
) -> str:
    if window_start and today < window_start:
        return 'pending'
    if window_end and today > window_end:
        return 'past_window'
    return 'open'


def parse_observable_criteria(falsifier_text: str) -> dict:
    """
    Extract machine-evaluable criteria from the falsifier string.
    Returns {refuted_criterion, confirmed_criterion, deadline, raw}.
    """
    refuted = ''
    confirmed = ''
    deadline = None

    m_r = _REFUTED_PAT.search(falsifier_text)
    if m_r:
        refuted = m_r.group(1).strip()

    m_c = _CONFIRMED_PAT.search(falsifier_text)
    if m_c:
        confirmed = m_c.group(1).strip()

    dates = _DEADLINE_PAT.findall(falsifier_text)
    if dates:
        deadline = max(dates)  # latest date in text

    return {
        'refuted_criterion':    refuted or '(see falsifier_text)',
        'confirmed_criterion':  confirmed or '(see falsifier_text)',
        'deadline':             deadline,
        'raw':                  falsifier_text[:300],
    }


def classify_evidence_strength(evidence_type: str, lel_domain: Optional[str], anchor_domain: str) -> str:
    """
    Classify structural evidence quality label (NOT a score).
    direct   — LEL match in same domain as anchor
    indirect — LEL match in adjacent/related domain
    proxy    — pending observation or cross-domain proxy indicator
    """
    if evidence_type == 'pending_observation':
        return 'proxy'
    if evidence_type in ('life_event_match', 'life_event_miss'):
        if lel_domain and lel_domain.lower() == anchor_domain.lower():
            return 'direct'
        return 'indirect'
    if evidence_type == 'self_report':
        return 'indirect'
    return 'proxy'


def _find_matching_lel(anchor: AnchorForPramana, lel_entries: list[LelEntry]) -> Optional[LelEntry]:
    """Find first LEL entry whose date is within anchor's window and domain matches."""
    if not anchor.window_start or not anchor.window_end:
        return None
    for lel in lel_entries:
        if anchor.window_start <= lel.event_date <= anchor.window_end:
            if lel.domain.lower() == anchor.domain.lower():
                return lel
    return None


def derive_pramana_records(ctx: PramanaContext) -> list[PramanaRecord]:
    """
    Derive PramanaRecords for every anchor in ctx.
    Each anchor gets exactly ONE primary record:
      - if a matching LEL entry exists: life_event_match / life_event_miss
      - if window is open or pending: pending_observation
    D5: this function never computes a score; only structural classification.
    """
    records: list[PramanaRecord] = []

    for anchor in ctx.anchors:
        falsifier = (anchor.falsifier or '').strip()
        criteria  = parse_observable_criteria(falsifier)
        w_status  = classify_window_status(anchor.window_start, anchor.window_end, ctx.today)

        lel_match = _find_matching_lel(anchor, ctx.lel_entries)

        if lel_match:
            ev_type = 'life_event_match'
        elif w_status == 'past_window':
            ev_type = 'life_event_miss'
        else:
            ev_type = 'pending_observation'

        lel_domain = lel_match.domain if lel_match else None
        strength   = classify_evidence_strength(ev_type, lel_domain, anchor.domain)

        derivation = {
            'anchor_id':        anchor.anchor_id,
            'anchor_source':    anchor.anchor_source,
            'evidence_type':    ev_type,
            'window_status':    w_status,
            'strength':         strength,
            'd5_boundary':      'no_calibration_score_in_l4 (L5 Mimamsa owns calibration)',
        }

        records.append(PramanaRecord(
            anchor_id=anchor.anchor_id,
            evidence_type=ev_type,
            evidence_strength_label=strength,
            falsifier_text=falsifier,
            observable_criteria_jsonb=criteria,
            window_status=w_status,
            lel_entry_id=lel_match.lel_id if lel_match else None,
            lel_entry_jsonb=lel_match.lel_jsonb if lel_match else None,
            derivation_ledger_jsonb=derivation,
            source_citation=f'ph_pramana/{anchor.anchor_id}/{ev_type}',
        ))

    return records
