"""
ph_sankrama engine — DB-free cross-domain spillover derivation (SK1-SK4).

REUSES bodha_cdlm_cells (linkage strength, activation windows, bridge edges).
The lag is DERIVED from real activation windows — never a formula (D44).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from brahmagyan.phala.confidence_vocab import STRUCTURAL_NOT_YET_EMPIRICAL

__all__ = [
    'CdlmCell',
    'SankramaContext',
    'SankramaRecord',
    'derive_projected_window',
    'classify_relationship',
    'derive_cascade_chain',
    'compute_spillover_confidence',
    'generate_spillover_falsifier',
    'derive_spillover',
]

_MAX_CASCADE_DEPTH = 3
_LINKAGE_THRESHOLD = 0.25  # minimum material linkage to emit a spillover


@dataclass
class CdlmCell:
    """One bodha_cdlm_cells row (pre-fetched by writer)."""
    cell_id:                    str
    domain_row:                 str
    domain_col:                 str
    net_linkage_strength:       float = 0.0
    asymmetry_score:            float = 0.0
    contradicting_pairs_count:  int = 0
    cgm_bridge_edge_seeds:      list[dict] = field(default_factory=list)
    predicted_activation_windows: list[dict] = field(default_factory=list)
    evolution_gradient_score:   float = 0.0


@dataclass
class SankramaContext:
    """One anchor + its matching CDLM cells (writer-supplied)."""
    source_anchor_id:       str
    source_domain:          str
    source_window_start:    Optional[date]
    source_window_end:      Optional[date]
    source_confidence:      float
    cdlm_cells:             list[CdlmCell] = field(default_factory=list)
    # all cells for cascade chaining (SK2)
    all_cells_by_domain_pair: dict[tuple[str,str], list[CdlmCell]] = field(default_factory=dict)


@dataclass
class SankramaRecord:
    source_anchor_id:       str
    cdlm_cell_id:           Optional[str]
    source_domain:          str
    target_domain:          str
    relationship_type:      str   # 'contagion' | 'conflict'
    linkage_strength:       float
    asymmetry_score:        float
    trajectory:             str   # 'strengthening' | 'stable' | 'weakening'
    bridge_path_jsonb:      dict
    mechanism_text:         str
    source_window_start:    Optional[date]
    source_window_end:      Optional[date]
    projected_window_start: Optional[date]
    projected_window_end:   Optional[date]
    projected_peak_date:    Optional[date]
    cascade_chain_jsonb:    Optional[dict]
    cascade_depth:          int
    spillover_confidence:   float
    confidence_basis:       str = STRUCTURAL_NOT_YET_EMPIRICAL
    falsifier:              str = ''
    mitigation_ref:         Optional[str] = None   # set post-facto by writer
    derivation_ledger_jsonb: dict = field(default_factory=dict)
    source_citation:        str = ''


def derive_projected_window(
    source_window_start: Optional[date],
    source_window_end: Optional[date],
    activation_windows: list[dict],
) -> tuple[Optional[date], Optional[date], Optional[date]]:
    """
    SK1: project the spillover window by intersecting the source anchor window
    with the cell's predicted_activation_dasha_windows. NOT a formula.
    Returns (start, end, peak).
    """
    if not activation_windows:
        return source_window_start, source_window_end, source_window_start

    best_start: Optional[date] = None
    best_end:   Optional[date] = None
    best_peak:  Optional[date] = None

    for aw in activation_windows:
        raw_start = aw.get('window_start')
        raw_end   = aw.get('window_end')
        raw_peak  = aw.get('peak_date') or raw_start

        try:
            ws = date.fromisoformat(str(raw_start)) if raw_start else None
            we = date.fromisoformat(str(raw_end))   if raw_end   else None
            wp = date.fromisoformat(str(raw_peak))  if raw_peak  else ws
        except (ValueError, TypeError):
            continue

        # intersect with source anchor window
        if source_window_start and ws:
            ws = max(ws, source_window_start)
        if source_window_end and we:
            we = min(we, source_window_end)

        if ws and we and ws <= we:
            if best_start is None or ws < best_start:
                best_start = ws
                best_end   = we
                best_peak  = wp

    if best_start is None:
        return source_window_start, source_window_end, source_window_start

    return best_start, best_end, best_peak


def classify_relationship(contradicting_pairs_count: int) -> str:
    """SK3: conflict if contradicting signal pairs exist; contagion otherwise."""
    return 'conflict' if contradicting_pairs_count > 0 else 'contagion'


def _trajectory(evolution_gradient: float) -> str:
    """SK4: map gradient score to trajectory label."""
    if evolution_gradient > 0.1:
        return 'strengthening'
    elif evolution_gradient < -0.1:
        return 'weakening'
    return 'stable'


def derive_cascade_chain(
    target_domain: str,
    source_confidence: float,
    all_cells_by_domain_pair: dict[tuple[str, str], list[CdlmCell]],
    depth: int = 0,
) -> Optional[dict]:
    """
    SK2: chain up to _MAX_CASCADE_DEPTH hops from target_domain.
    Returns cascade_chain_jsonb or None if no further hops.
    """
    if depth >= _MAX_CASCADE_DEPTH - 1:
        return None

    next_cells = all_cells_by_domain_pair.get((target_domain, ''), [])
    # find any domain pair starting from target
    hops: list[dict] = []
    for key, cells in all_cells_by_domain_pair.items():
        if key[0] == target_domain:
            for c in cells:
                if c.net_linkage_strength >= _LINKAGE_THRESHOLD:
                    hops.append({
                        'domain': c.domain_col,
                        'cell_id': c.cell_id,
                        'linkage_strength': c.net_linkage_strength,
                        'relationship_type': classify_relationship(c.contradicting_pairs_count),
                    })

    if not hops:
        return None

    return {
        'hops': hops[:3],   # cap at 3 hops total
        'depth': depth + 1,
    }


def compute_spillover_confidence(source_confidence: float, linkage_strength: float) -> float:
    """Inherit source confidence × linkage; cap at 0.80 (structural_not_yet_empirical)."""
    raw = source_confidence * linkage_strength
    return round(min(0.80, max(0.0, raw)), 4)


def generate_spillover_falsifier(
    source_domain: str,
    target_domain: str,
    relationship_type: str,
    projected_end: Optional[date],
) -> str:
    rel_word = 'contagion' if relationship_type == 'contagion' else 'conflict'
    deadline = str(projected_end) if projected_end else 'end of projected window'
    return (
        f"REFUTED if no {target_domain}-domain {rel_word} traceable to a {source_domain}-domain "
        f"trigger is independently documented by {deadline}. "
        f"CONFIRMED if the {target_domain} impact is recorded in the Life-Event Log within the window."
    )


def derive_spillover(ctx: SankramaContext) -> list[SankramaRecord]:
    """
    Derive all SankramaRecords for one anchor's CDLM-linked cells.
    Returns a list (one record per material cell + relationship_type combination).
    """
    records: list[SankramaRecord] = []

    for cell in ctx.cdlm_cells:
        if cell.net_linkage_strength < _LINKAGE_THRESHOLD:
            continue

        target_domain = cell.domain_col
        relationship  = classify_relationship(cell.contradicting_pairs_count)
        trajectory    = _trajectory(cell.evolution_gradient_score)

        proj_start, proj_end, proj_peak = derive_projected_window(
            ctx.source_window_start, ctx.source_window_end,
            cell.predicted_activation_windows,
        )

        # SK1: bridge path from CGM seeds
        bridge_seeds = cell.cgm_bridge_edge_seeds[:3] if cell.cgm_bridge_edge_seeds else []
        mechanism_text = (
            f"{ctx.source_domain} domain loads onto {target_domain} "
            f"via {bridge_seeds[0].get('mediating_planet','?')}/{bridge_seeds[0].get('house','?')} bridge"
            if bridge_seeds else
            f"{ctx.source_domain} linkage to {target_domain} (mechanism from CDLM cell {cell.cell_id})"
        )
        bridge_path = {
            'cdlm_cell_id': cell.cell_id,
            'bridge_seeds': bridge_seeds,
            'mechanism':    mechanism_text,
        }

        # SK2: cascade chain
        cascade = derive_cascade_chain(
            target_domain, ctx.source_confidence, ctx.all_cells_by_domain_pair
        )

        conf = compute_spillover_confidence(ctx.source_confidence, cell.net_linkage_strength)
        falsifier = generate_spillover_falsifier(
            ctx.source_domain, target_domain, relationship, proj_end
        )

        derivation = {
            'source_anchor_id':   ctx.source_anchor_id,
            'cdlm_cell_id':       cell.cell_id,
            'source_domain':      ctx.source_domain,
            'target_domain':      target_domain,
            'linkage_strength':   cell.net_linkage_strength,
            'relationship_type':  relationship,
            'sk_elevations':      ['SK1','SK2','SK3','SK4'],
            'lag_method':         'activation_window_intersection (not a formula)',
        }

        records.append(SankramaRecord(
            source_anchor_id=ctx.source_anchor_id,
            cdlm_cell_id=cell.cell_id,
            source_domain=ctx.source_domain,
            target_domain=target_domain,
            relationship_type=relationship,
            linkage_strength=cell.net_linkage_strength,
            asymmetry_score=cell.asymmetry_score,
            trajectory=trajectory,
            bridge_path_jsonb=bridge_path,
            mechanism_text=mechanism_text,
            source_window_start=ctx.source_window_start,
            source_window_end=ctx.source_window_end,
            projected_window_start=proj_start,
            projected_window_end=proj_end,
            projected_peak_date=proj_peak,
            cascade_chain_jsonb=cascade,
            cascade_depth=cascade['depth'] if cascade else 1,
            spillover_confidence=conf,
            falsifier=falsifier,
            derivation_ledger_jsonb=derivation,
            source_citation=f"phala_sankrama/{ctx.source_anchor_id}/{cell.cell_id}",
        ))

    return records
