"""
test_phala_muhurta_nakshatra_read_normalised.py -- FAIL-ON-BASE (SS N-568): brahmagyan/phala/muhurta.py reads
panchanga_daily.moon_nakshatra, a table this round does NOT rebuild (it still stores the adapter's spelling,
e.g. 'Mrigashira'), and used to look it up in ga_panchanga_writer.NAKSHATRA_NAMES, which is now the lexicon's
(Mrigasira): _nakshatra_short_code('Mrigashira') returned None and the tara verdict silently vanished on
Mrigashira days. Every stored name is now normalised on read through the ONE normaliser.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES  # noqa: E402
from brahmagyan.phala import muhurta as m  # noqa: E402
from ga_writers.ga_panchanga_writer import NAKSHATRA_SHORT  # noqa: E402

SHORT = dict(zip(CANONICAL_NAKSHATRA_NAMES, NAKSHATRA_SHORT))


@pytest.mark.parametrize("stored,canon", [("Mrigashira", "Mrigasira"), ("Mula", "Moola"), ("Dhanishta", "Dhanishtha"),
                                          ("Mrigasira", "Mrigasira"), ("Purva Bhadrapada", "Purva Bhadrapada"), ("purva_bhadrapada", "Purva Bhadrapada")])
def test_short_code_resolves_the_stored_adapter_spelling(stored, canon):
    assert m._nakshatra_short_code(stored) == SHORT[canon]       # fails on base for the three adapter spellings: None


@pytest.mark.parametrize("bad", ["", "NotANakshatra", "Purva", "Abhijit"])
def test_short_code_is_none_for_an_unregistered_or_ambiguous_name(bad):
    assert m._nakshatra_short_code(bad) is None


def test_tara_verdict_appears_on_a_mrigashira_day():
    baseline = {SHORT["Mrigasira"]: "Vipat"}
    v = m._tara_bala_verdict("Mrigashira", baseline)             # fails on base: None (short code unresolved)
    assert v is not None and v["moon_nakshatra"] == "Mrigashira"
    assert m._tara_bala_verdict("Mrigasira", baseline) is not None
    assert m._tara_bala_verdict("NotANakshatra", baseline) is None


def test_action_sets_are_canonical_and_the_stored_spelling_scores_like_the_lexicons():
    for S in (m._MARRIAGE_NAKS, m._EDUCATION_NAKS, m._BUSINESS_NAKS, m._TRAVEL_NAKS, m._MEDICAL_NAKS, m._MEDICAL_BAD_NAKS, m._PROPERTY_NAKS):
        assert S and S <= set(CANONICAL_NAKSHATRA_NAMES), sorted(S - set(CANONICAL_NAKSHATRA_NAMES))
    assert "Mrigasira" in m._MARRIAGE_NAKS and "Uttara Phalguni" in m._MARRIAGE_NAKS   # the old space-less 'Uttaraphalguni' literal never matched a stored spaced name
    for action in ("marriage", "education", "business", "travel"):
        legacy = m._panchanga_quality_for_action("Shukla Dwitiya", "Jupiter", "Mrigashira", "Siddha", action)
        canon = m._panchanga_quality_for_action("Shukla Dwitiya", "Jupiter", "Mrigasira", "Siddha", action)
        other = m._panchanga_quality_for_action("Shukla Dwitiya", "Jupiter", "Ardra", "Siddha", action)
        assert legacy == canon > other, action                     # fails on base: the lexicon spelling got no boost
    assert m._panchanga_quality_for_action("Shukla Dwitiya", "Jupiter", "Uttara Phalguni", "Siddha", "marriage") == \
        m._panchanga_quality_for_action("Shukla Dwitiya", "Jupiter", "Uttaraphalguni", "Siddha", "marriage")
