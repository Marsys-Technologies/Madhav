"""Shared fixtures for the B5.1 gochara_rules oracle tests.

CHART pins GOCHARA_TEST_ORACLES_v1_4 constants verbatim: lagna 12.43° Aries;
natal longitudes per L1 chart_facts build 1c092ffb (Venus carried as 259.19
per constants.natal_precision_note — no printed arithmetic depends on it);
day birth, Śukla pakṣa (O-RP-4 / O-PP-3 operands).
"""
from __future__ import annotations

import pytest

# GOCHARA_TEST_ORACLES_v1_4 constants (literal).
LAGNA_DEG = 12.43
NATAL = {
    "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
    "Jupiter": 249.79, "Venus": 259.19, "Saturn": 202.43,
    "Rahu": 49.03, "Ketu": 229.03,
}


@pytest.fixture
def chart() -> dict:
    return {"lagna_deg": LAGNA_DEG, "natal": dict(NATAL),
            "day_birth": True, "paksha": "Shukla"}
