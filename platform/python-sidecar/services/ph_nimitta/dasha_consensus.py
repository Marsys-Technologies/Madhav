"""
services.ph_nimitta.dasha_consensus — U1 consumption contract: dāśā consensus derivation.

Purpose
-------
ph_nimitta Axis 6 (and U4 Yoginī engine) consume `dasha_consensus_count` — the number
of DISTINCT dāśā systems whose eligible window overlaps a prediction window for a given
domain's significator lords.

The 536,471-row L1 dasha corpus (7 systems) + KaDashaKalaService are ALREADY built.
U1 surfaces the cross-system agreement as a first-class queryable count rather than
leaving it buried as a 0.18-weighted I-16 term.

Canonical definition (ratified U1 / D20a)
------------------------------------------
For a prediction window [window_start, window_end] in domain D:

    1. Call KaDashaKalaService.query(chart_id, ayanamsha_id,
           target_lords=<domain's significator lords>,
           date_start=window_start, date_end=window_end,
           max_level=4, systems=ALL_7).
    2. dasha_consensus_count = max cross_dasha_agreement.count across all windows
       that overlap [window_start, window_end].  Equivalently: the count of DISTINCT
       systems whose eligible window overlaps the prediction window.
    3. dasha_consensus_systems = the corresponding systems_agreeing list.
    4. Floor = 1 (any system that returns a window contributes ≥ 1).
    5. Ceiling = 7 (all 7 systems agree).

The ONLY new write from U1 is `dasha_consensus_count` on `phala_anchors` (L4's own table).
U1 adds NO new column to chart_dashas or kala_convergence.

Zero-duplication: strictly through KaDashaKalaService — never re-derives a dāśā tree-walk.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional, Set

logger = logging.getLogger(__name__)

# ── All 7 dāśā systems (GATE-A verified; 536,471 rows in prod) ───────────────
ALL_7_SYSTEMS: Set[str] = {
    'vimshottari', 'yogini', 'ashtottari',
    'chara_karaka', 'naisargika', 'mudda', 'kalachakra',
}


@dataclass
class DashaConsensusResult:
    """
    Output of derive_dasha_consensus for a single prediction window + domain.

    Attributes
    ----------
    count : int
        Number of distinct dāśā systems whose eligible window overlaps the
        prediction window for the domain's significators.  Floor 1, ceiling 7.
    systems_agreeing : list[str]
        Which systems concur (subset of the 7 ratified systems).
    confidence_multiplier : float
        G-LADDER factor: max(0.5, count/7).  Capped at 1.0 per D21.
        ph_nimitta multiplies its raw confidence by this before the [0,1] clamp.
    high_agreement : bool
        True when count >= 4 (strong multi-system consensus).
    all_systems_checked : list[str]
        The full set of systems that were queried (sanity reference).
    """
    count: int
    systems_agreeing: list[str]
    confidence_multiplier: float
    high_agreement: bool
    all_systems_checked: list[str]


def derive_dasha_consensus(
    db_conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    target_lords: Set[str],
    window_start: date,
    window_end: date,
    related_lords: Optional[Set[str]] = None,
) -> DashaConsensusResult:
    """
    Derive the multi-dāśā consensus for a prediction window.

    This is the canonical U1 consumption function used by ph_nimitta Axis 6
    and the U4 Yoginī school engine.  It is the ONLY entry-point through which
    L4 writers access dāśā consensus; they must NOT re-derive a dāśā tree-walk.

    Parameters
    ----------
    db_conn : psycopg connection (caller-owned, read-only)
    chart_id : str   UUID of the chart
    ayanamsha_id : str   e.g. 'lahiri'
    target_lords : set[str]   Domain's significator lords (graha names)
    window_start, window_end : date   The prediction window
    related_lords : set[str] | None   Optionally broaden the search

    Returns
    -------
    DashaConsensusResult
    """
    from services.ka_dasha_kala.service import KaDashaKalaService

    svc = KaDashaKalaService(db_conn)
    result = svc.query(
        chart_id=chart_id,
        ayanamsha_id=ayanamsha_id,
        target_lords=target_lords,
        related_lords=related_lords or set(),
        date_start=window_start,
        date_end=window_end,
        max_level=4,
        systems=ALL_7_SYSTEMS,
    )

    # Find max agreement count across overlapping windows
    # and collect all distinct agreeing systems
    max_count = 0
    all_agreeing: set[str] = set()

    for w in result.windows:
        c = w.cross_dasha_agreement.count
        if c > max_count:
            max_count = c
        all_agreeing.update(w.cross_dasha_agreement.systems_agreeing)

    # Floor at 1 if any window returned (floor 0 only when no windows at all)
    if result.windows and max_count == 0:
        max_count = 1

    systems_agreeing = sorted(all_agreeing)
    # G-LADDER confidence multiplier per D21: f = max(0.5, count/7), capped at 1.0
    conf_mult = min(1.0, max(0.5, max_count / 7.0))

    logger.info(
        "[u1_dasha_consensus] chart=%s window=%s–%s lords=%s → count=%d systems=%s",
        chart_id, window_start, window_end, sorted(target_lords),
        max_count, systems_agreeing,
    )

    return DashaConsensusResult(
        count=max_count,
        systems_agreeing=systems_agreeing,
        confidence_multiplier=conf_mult,
        high_agreement=(max_count >= 4),
        all_systems_checked=sorted(ALL_7_SYSTEMS),
    )


def confirm_seven_systems_reachable(
    db_conn: Any,
    chart_id: str,
    ayanamsha_id: str = 'lahiri',
) -> dict[str, int]:
    """
    GATE-A verification: confirm all 7 dāśā systems return rows for this chart
    via the KaDashaKalaService path.  Returns {system_id: row_count}.
    """
    from services.ka_dasha_kala.service import KaDashaKalaService
    return KaDashaKalaService(db_conn).confirm_systems_present(chart_id, ayanamsha_id)
