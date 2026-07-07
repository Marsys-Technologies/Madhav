"""test_ph_nimitta_base_rate.py — JL-009 point-2 (native ruling 2026-07-07).

Asserts ph_nimitta's base_rate consumption ROW-NORMALIZES the brahma_event_ontology
age-band vector to sum 1.0 at lookup, selects the band by the native's age at the
anchor's predicted date, and falls back to the uniform age prior (0.20) when age is
unknown. DB-free — exercises the pure helper.
"""
from __future__ import annotations

import sys
import pathlib
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from services.ph_nimitta.base_rate import (  # noqa: E402
    normalize_age_vector,
    base_rate_for_age,
    age_band_for_years,
    years_between,
    BAND_KEYS,
    UNIFORM_BASE_RATE,
)

# bereavement v1.1 (JL-009): relative weights, per-row sum = 1.30 (NOT a distribution).
BEREAVEMENT_V1_1 = {
    "band_0_12": 0.10, "band_13_25": 0.15, "band_26_40": 0.30,
    "band_41_60": 0.35, "band_60_plus": 0.40,
}
BIRTH = date(1984, 2, 5)  # the native's DOB


def test_normalize_sums_to_one():
    n = normalize_age_vector(BEREAVEMENT_V1_1)
    assert abs(sum(n.values()) - 1.0) < 1e-9
    # proportions preserved: band_41_60 = 0.35 / 1.30
    assert abs(n["band_41_60"] - (0.35 / 1.30)) < 1e-9


def test_normalize_zero_vector_is_uniform():
    n = normalize_age_vector({k: 0.0 for k in BAND_KEYS})
    assert all(abs(v - UNIFORM_BASE_RATE) < 1e-9 for v in n.values())


def test_normalize_missing_keys_treated_as_zero():
    n = normalize_age_vector({"band_26_40": 1.0})  # only one band present
    assert abs(n["band_26_40"] - 1.0) < 1e-9
    assert abs(sum(n.values()) - 1.0) < 1e-9


def test_age_band_boundaries_are_contiguous():
    assert age_band_for_years(12) == "band_0_12"
    assert age_band_for_years(13) == "band_13_25"
    assert age_band_for_years(25) == "band_13_25"
    assert age_band_for_years(26) == "band_26_40"
    assert age_band_for_years(60) == "band_41_60"
    assert age_band_for_years(61) == "band_60_plus"
    assert age_band_for_years(120) == "band_60_plus"
    assert age_band_for_years(0) == "band_0_12"


def test_years_between_birthday_adjusted():
    assert years_between(BIRTH, date(2026, 2, 5)) == 42   # exact birthday
    assert years_between(BIRTH, date(2026, 2, 4)) == 41   # day before
    assert years_between(BIRTH, date(2026, 7, 7)) == 42


def test_base_rate_is_normalized_band_value():
    # age 42 at peak 2026 → band_41_60 → 0.35/1.30
    br = base_rate_for_age(BEREAVEMENT_V1_1, BIRTH, date(2026, 7, 7))
    assert abs(br - (0.35 / 1.30)) < 1e-9
    # crucially it is NOT the raw stored weight 0.35, nor the old 0.10 placeholder
    assert abs(br - 0.35) > 1e-3
    assert abs(br - 0.10) > 1e-3


def test_base_rate_uniform_when_age_unknown():
    assert base_rate_for_age(BEREAVEMENT_V1_1, BIRTH, None) == UNIFORM_BASE_RATE   # no date
    assert base_rate_for_age(BEREAVEMENT_V1_1, None, date(2026, 7, 7)) == UNIFORM_BASE_RATE  # no birth
    assert base_rate_for_age(None, BIRTH, date(2026, 7, 7)) == UNIFORM_BASE_RATE   # no vector
    assert base_rate_for_age({}, BIRTH, date(2026, 7, 7)) == UNIFORM_BASE_RATE      # empty vector


def test_base_rate_always_valid_probability():
    for at_year in (5, 2000, 2010, 2026, 2050):
        br = base_rate_for_age(BEREAVEMENT_V1_1, BIRTH, date(at_year, 6, 1))
        assert 0.0 <= br <= 1.0
