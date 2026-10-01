"""P2 favourable house sets (Phaladīpikā XXVI.1–8) — cited-table tests.

The expected table below is written out INDEPENDENTLY of the module, from
the served corpus chunks read verbatim 2026-10-01 (PG321:C1 śl.1–2;
PG322:C1 śl.3–5; PG323:C1 śl.6–8). A mutation that moves one house in the
module turns the relevant test red (demonstrated in the PR body).
"""
from __future__ import annotations

import pytest

from services.gochara_rules import favourable_houses as fh
from services.gochara_rules import vedha

# Independent transcription of the served text (see module docstring for the
# verbatim quotes). śl.2 table + "all planets in the 11th"; Venus as the
# text's complement of {6, 7, 10}; nodes by the śl.2 equivalence clause.
EXPECTED = {
    "Sun": {3, 6, 10, 11},
    "Moon": {1, 3, 6, 7, 10, 11},
    "Mars": {3, 6, 11},
    "Mercury": {2, 4, 6, 8, 10, 11},
    "Jupiter": {2, 5, 7, 9, 11},
    "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "Saturn": {3, 6, 11},
    "Rahu": {3, 6, 10, 11},
    "Ketu": {3, 6, 10, 11},
}


def test_exactly_the_nine_grahas_all_cited():
    assert set(fh.FAVOURABLE_HOUSES_FROM_MOON) == set(EXPECTED)
    for graha, row in fh.FAVOURABLE_HOUSES_FROM_MOON.items():
        assert row["state"] == "cited", graha  # nothing unresolved (B.10)
        assert row["citations"], graha


@pytest.mark.parametrize("graha,houses", sorted(EXPECTED.items()))
def test_set_equals_the_cited_table(graha, houses):
    assert set(fh.favourable_houses(graha)) == houses
    assert fh.FAVOURABLE_HOUSES_FROM_MOON[graha]["houses"] == frozenset(houses)


def test_frame_is_moon_and_provenance_verse_cited():
    assert fh.FRAME == "moon"          # janma-rāśi (XXVI.1, PG321:C1)
    assert fh.PROVENANCE == "verse_cited"


def test_every_house_number_1_to_12():
    for graha in EXPECTED:
        assert fh.favourable_houses(graha) <= set(range(1, 13))


def test_venus_is_the_texts_complement():
    # "all places other than the 10th, 7th and 6th" — the 11th already inside
    assert fh.favourable_houses("Venus") == frozenset(set(range(1, 13)) - {6, 7, 10})


def test_nodes_equal_the_sun_by_the_sloka_2_equivalence():
    assert fh.favourable_houses("Rahu") == fh.favourable_houses("Sun")
    assert fh.favourable_houses("Ketu") == fh.favourable_houses("Sun")


def test_is_favourable_membership_helper():
    assert fh.is_favourable("Jupiter", 11)
    assert not fh.is_favourable("Jupiter", 8)
    assert fh.is_favourable("Saturn", 3) and not fh.is_favourable("Saturn", 8)


def test_vedha_not_duplicated_reference_only():
    # O-VI-3 exceptions and pairs live in vedha.py / bg_transit_rules; this
    # module must not re-declare them.
    assert fh.VEDHA_EXCEPTIONS_REF == "gochara_rules.vedha.EXCEPTION_PAIRS"
    assert not hasattr(fh, "EXCEPTION_PAIRS")
    assert not any("vedha_house" in k.lower() for row in fh.FAVOURABLE_HOUSES_FROM_MOON.values()
                   for k in row)
    assert vedha.exception_for("Sun", "Saturn") == "sun_saturn"   # O-VI-3 intact
    assert vedha.exception_for("Moon", "Mercury") == "moon_mercury"
    assert vedha.exception_for("Mars", "Jupiter") == "none"
