"""
tests/test_ga_yoga_narr_golden.py -- narr golden-value test for ga_yoga.

Two ga_yoga builders compose ``ga_yoga_firings.citation_human`` from computed facts; both are pure:

  * ``_compute_constituent_bala_strength`` -- the strength citation names the constituent grahas of
    the shadbala mean (actual rupa / classical required rupa, plain mean). Fixed Sarasvati Yoga
    constituents Jupiter 6.5/6.5, Venus 5.5/6.6, Mercury 7.0/7.0 -> ratios 1.0, 0.8333, 1.0, mean
    0.9444; the sentence lists the grahas sorted. A Rahu-only constituent set has no shadbala, so
    every element, the citation included, stays None (an honest null, not an invented sentence);
  * ``_cancel_sarasvati_yoga`` -- the cancelling ground names exactly the constituent grahas that are
    debilitated or combust (classical: an afflicted constituent cancels the yoga), in constituent
    order, and says plainly when none is afflicted.
"""
from __future__ import annotations

from ga_writers.ga_yoga_writer import _cancel_sarasvati_yoga, _compute_constituent_bala_strength

_SHADBALA = {
    "jupiter": {"rupa": 6.5, "required_rupa": 6.5},
    "venus": {"rupa": 5.5, "required_rupa": 6.6},
    "mercury": {"rupa": 7.0, "required_rupa": 7.0},
}
_FINDING = {"constituent_planets": ["jupiter", "venus", "mercury"]}


def test_citation_human_names_constituent_grahas_and_cancelling_ground():
    citation_human = _compute_constituent_bala_strength(
        ["jupiter", "venus", "mercury"], _SHADBALA, "sarasvati_yoga", "chart-1", "lahiri",
    )[4]
    assert citation_human == (
        "sarasvati_yoga strength = mean of normalized shadbala (actual/required rupa, "
        "graha_shadbala_total bala_gate) across constituent grahas "
        "['jupiter', 'mercury', 'venus']; derivation=constituent_bala_v1 "
        "(computed_extension — not a classical per-yoga formula, B.10)."
    )

    citation_human = _compute_constituent_bala_strength(
        ["rahu"], _SHADBALA, "sarasvati_yoga", "chart-1", "lahiri",
    )[4]
    assert citation_human is None

    cancelled = _cancel_sarasvati_yoga(
        _FINDING, None,
        {"venus": {"is_combust": True}, "mercury": {"is_debilitated": True}, "jupiter": {}}, [],
    )
    assert cancelled["citation_human"] == (
        "A constituent graha (venus, mercury) is debilitated or combust — "
        "Sarasvati Yoga is cancelled."
    )

    intact = _cancel_sarasvati_yoga(_FINDING, None, {"jupiter": {}, "venus": {}}, [])
    assert intact["citation_human"] == "No constituent graha is debilitated or combust."
