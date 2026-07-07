"""ph_nimitta base-rate lookup — JL-009 point-2 (native ruling 2026-07-07).

The `brahma_event_ontology.base_rate_by_age` weights are RELATIVE per-class age
weights whose per-row sums are inconsistent (observed 0.81–1.30) — NOT a probability
distribution. The native's structural directive (BA_PHASE4_RUNWAY_PLAN R1.1, point 2):

    ph_nimitta's base_rate consumption MUST row-normalize the age-band vector to
    sum 1.0 at lookup — this is code, not convention.

So the base_rate consumed by the L4 posterior (posterior = base_rate × lifts) is the
NORMALIZED weight for the age band containing the anchor's predicted date (peak_date,
else window_start) relative to the native's birth date. When no age is determinable
(missing vector/birth/date), the lookup falls back to the uniform age prior
(1/n_bands = 0.20 for the 5-band schema) — a truly uninformative base rate, never a
fabricated value.

Recorded as brahma_formula_constants 'ph_nimitta_base_rate_age_normalization'
(class=engineering); test_ph_nimitta_base_rate asserts the normalized lookup.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

# Canonical 5-band schema — keys MUST match brahma_event_ontology.base_rate_by_age.
# (label, inclusive_low_age, inclusive_high_age)
AGE_BANDS: list[tuple[str, int, int]] = [
    ("band_0_12",    0,  12),
    ("band_13_25",  13,  25),
    ("band_26_40",  26,  40),
    ("band_41_60",  41,  60),
    ("band_60_plus", 61, 200),
]
BAND_KEYS: list[str] = [b[0] for b in AGE_BANDS]
UNIFORM_BASE_RATE: float = 1.0 / len(AGE_BANDS)  # 0.20 — uninformative age prior


def age_band_for_years(age_years: int) -> str:
    """Return the band key for a whole-year age. <0 → youngest band; >60 → eldest."""
    for key, lo, hi in AGE_BANDS:
        if lo <= age_years <= hi:
            return key
    return BAND_KEYS[-1] if age_years > 60 else BAND_KEYS[0]


def years_between(birth: date, at: date) -> int:
    """Whole years from birth to `at` (birthday-adjusted)."""
    y = at.year - birth.year
    if (at.month, at.day) < (birth.month, birth.day):
        y -= 1
    return y


def normalize_age_vector(base_rate_by_age: dict) -> dict:
    """Row-normalize the age-band weights so they sum to 1.0.

    Missing keys count as 0.0. If the total is ≤ 0 (empty / all-zero vector), return a
    uniform distribution over the canonical bands (never divide by zero, never fabricate)."""
    vals = {k: float(base_rate_by_age.get(k, 0.0) or 0.0) for k in BAND_KEYS}
    total = sum(vals.values())
    if total <= 0:
        return {k: UNIFORM_BASE_RATE for k in BAND_KEYS}
    return {k: v / total for k, v in vals.items()}


def base_rate_for_age(
    base_rate_by_age: Optional[dict],
    birth: Optional[date],
    at: Optional[date],
) -> float:
    """Normalized base-rate for the age band containing `at` (relative to `birth`).

    - vector present + birth + at known → normalize(vector)[age_band]
    - any of those missing → UNIFORM_BASE_RATE (0.20), the uninformative age prior.
    The returned value is always a valid probability in [0, 1]."""
    if not base_rate_by_age:
        return UNIFORM_BASE_RATE
    norm = normalize_age_vector(base_rate_by_age)
    if birth is None or at is None:
        return UNIFORM_BASE_RATE
    return norm[age_band_for_years(years_between(birth, at))]
