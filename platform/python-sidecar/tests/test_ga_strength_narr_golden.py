"""
tests/test_ga_strength_narr_golden.py -- narr golden-value test for ga_strength.

``_citation_human_strength`` composes ``chart_facts.citation_human`` for the shadbala total
(achieved rupa, surplus/deficit against the classical Parashara minimum), the vimsopaka score,
the ashtakavarga bindu count and the bhava bala ratio. Classical minimums (BPHS), in virupa:
Sun 390 (6.50 rupa), Moon 360 (6.00), Mars 300 (5.00), Mercury 420 (7.00), Jupiter 390 (6.50),
Venus 330 (5.50), Saturn 300 (5.00). Pure function, no database.
"""
from __future__ import annotations

from ga_writers.ga_strength_writer import _citation_human_strength


def test_citation_human_grades_total_shadbala_against_classical_minimum():
    # Saturn: 5.4 rupa achieved vs 5.00 required -> surplus 0.40.
    citation_human = _citation_human_strength("graha_shadbala_total", "SAT", "rupa", 5.4, "lahiri")
    assert citation_human == (
        "SAT total shadbala: 5.4000 rupa (surplus 0.40 vs required 5.00 rupa) (Lahiri)."
    )

    # Sun: 6.0 rupa achieved vs 6.50 required -> deficit 0.50 (not graded against 5.0).
    citation_human = _citation_human_strength("graha_shadbala_total", "SUN", "rupa", 6.0, "lahiri")
    assert citation_human == (
        "SUN total shadbala: 6.0000 rupa (deficit 0.50 vs required 6.50 rupa) (Lahiri)."
    )

    # Ashtakavarga bindu count for the 10th house of the Sun.
    citation_human = _citation_human_strength("ashtakavarga_bindu", "SUN-HOUSE_10", "bindu", 5, "lahiri")
    assert citation_human == "Sun ashtakavarga house 10: 5 bindu (Lahiri)."
