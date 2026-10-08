"""Daśā F2 clock facade, with an explicit compatibility path.

KaDashaKalaService.period_context / boundaries / scenarios read kala_core.clocks
with a mandatory L1 build, ayanāṃśa and tier. Scored eligibility and cross-system
votes remain exclusively in query → legacy_query for existing consumers.
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
