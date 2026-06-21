"""
ka_dasha_kala — Daśā-Eligibility Service (L3 Kāla K1-wave).

Public API
----------
    from services.ka_dasha_kala import KaDashaKalaService

    svc = KaDashaKalaService(db_conn=conn)
    result = svc.query(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri",
        target_lords={"Saturn", "Rahu"},
        related_lords={"Mercury", "Venus"},
        date_start=date(2024, 1, 1),
        date_end=date(2026, 12, 31),
        max_level=4,
        prana_grain=False,
    )

The service performs a lazy pruning tree-walk over ``chart_dashas``,
scores surviving intervals by eligibility, and reports cross-dasa
agreement across all 7 production systems.

All 7 systems (vimshottari, yogini, ashtottari, chara_karaka, naisargika,
mudda, kalachakra) are served from ``chart_dashas`` (level 1-4 max).
KP is a Vimshottari sub-level (``kp_sublevel`` column) -- not a standalone
system.  Level-5 (Prana) is NOT persisted; the service computes it
in-memory on demand only, without writing to the DB.
"""
from .service import KaDashaKalaService
from .eligibility import EligibilityBand, score_eligibility
from .tree_walk import DashaInterval, walk_eligible_intervals

__all__ = [
    "KaDashaKalaService",
    "EligibilityBand",
    "score_eligibility",
    "DashaInterval",
    "walk_eligible_intervals",
]
