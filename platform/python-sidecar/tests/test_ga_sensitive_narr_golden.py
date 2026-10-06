"""
tests/test_ga_sensitive_narr_golden.py -- narr golden-value test for ga_sensitive.

ga_sensitive composes ``chart_facts.citation_human`` in ``_citation_human`` via ``_make_row``
as ``{category}.{subject}.{key} = {value} ({ayanamsha}).`` from the row's own computed value.
This pins the REAL row builder, for a fixed numeric row and a fixed text row, against sentences
written out by hand (no database, no ephemeris).
"""
from __future__ import annotations

from ga_writers.ga_sensitive_writer import _make_row

_CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def test_citation_human_states_the_computed_value_and_ayanamsha():
    # Numeric row: natal Sun at 292.5 deg sidereal (22.5 deg Capricorn).
    num_row = _make_row(
        "sensitive_degree", "SUN", "longitude_sidereal", 292.5, None, None,
        _CHART, "lahiri", "build-1", "eng-1",
    )
    assert num_row["citation_human"] == (
        "sensitive_degree.SUN.longitude_sidereal = 292.5 (lahiri)."
    )

    # Text row: the sign is stated as the value text, not as a number.
    text_row = _make_row(
        "sensitive_degree", "SUN", "sign", None, "Capricorn", None,
        _CHART, "lahiri", "build-1", "eng-1",
    )
    assert text_row["citation_human"] == "sensitive_degree.SUN.sign = Capricorn (lahiri)."
