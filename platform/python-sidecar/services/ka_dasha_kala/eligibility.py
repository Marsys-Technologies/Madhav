"""
eligibility.py — Eligibility scoring logic for ka_dasha_kala.

Three-tier soft prior:
  EXACT   (score >= 0.8) — lord IS in the target_lords signature set
  RELATED (score ~= 0.5) — lord is in related_lords (dispositors, house-lords)
  NEUTRAL (score ~= 0.2) — lord has no specific connection to the signature

The scoring is deliberately soft/probabilistic so that downstream consumers
can layer their own weights on top.  The enum keeps the semantics stable.
"""
from __future__ import annotations

from enum import Enum
from typing import Set


class EligibilityBand(str, Enum):
    """Semantic band for a dasha lord's relationship to a target signature."""
    EXACT   = "exact"
    RELATED = "related"
    NEUTRAL = "neutral"


# Default scores per band.  Callers may override.
BAND_SCORE: dict[EligibilityBand, float] = {
    EligibilityBand.EXACT:   0.85,
    EligibilityBand.RELATED: 0.50,
    EligibilityBand.NEUTRAL: 0.20,
}


def score_eligibility(
    lord: str,
    target_lords: Set[str],
    related_lords: Set[str],
    band_scores: dict[EligibilityBand, float] | None = None,
) -> tuple[EligibilityBand, float]:
    """
    Return (band, score) for *lord* relative to the given signature sets.

    Parameters
    ----------
    lord : str
        The dasha lord graha name (e.g. 'Saturn', 'Jupiter').
    target_lords : set[str]
        Lords that directly define the target signature (exact-match).
    related_lords : set[str]
        Lords that are related to the signature (dispositors, house-lords).
    band_scores : dict | None
        Optional override map.  Keys must be EligibilityBand members.

    Returns
    -------
    (band, score) tuple.
    """
    scores = band_scores if band_scores is not None else BAND_SCORE

    if lord in target_lords:
        band = EligibilityBand.EXACT
    elif lord in related_lords:
        band = EligibilityBand.RELATED
    else:
        band = EligibilityBand.NEUTRAL

    return band, scores[band]


def is_eligible_for_pruning(
    lord: str,
    target_lords: Set[str],
    related_lords: Set[str],
    min_band: EligibilityBand = EligibilityBand.RELATED,
) -> bool:
    """
    Return True if this lord's band is >= min_band, False otherwise.

    Used by the tree-walk to decide whether to PRUNE a subtree at level-1
    (Maha-dasa): if the MD lord is not at least as relevant as ``min_band``,
    the entire subtree is skipped without querying children.

    Default ``min_band`` is RELATED — purely NEUTRAL MDs are pruned.
    """
    band, _ = score_eligibility(lord, target_lords, related_lords)
    order = [EligibilityBand.NEUTRAL, EligibilityBand.RELATED, EligibilityBand.EXACT]
    return order.index(band) >= order.index(min_band)
