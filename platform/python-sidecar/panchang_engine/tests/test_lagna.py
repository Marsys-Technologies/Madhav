"""
test_lagna.py — FORENSIC gate for Lagna computation.
FORENSIC anchor: birth 1984-02-05 10:43 IST, Bhubaneswar (20.27N, 85.84E)
Expected Lagna: Mesha (Aries), per A4_PANCHANGA_SPEC anchors.
"""
from datetime import datetime
import pytest

BIRTH = datetime(1984, 2, 5, 10, 43, 0)
LAT, LON, TZ = 20.27, 85.84, 330


def test_lagna_forensic_mesha():
    from panchang_engine.lagna import compute_lagna
    lagna = compute_lagna(BIRTH, LAT, LON, TZ)
    assert lagna.ascendant_sign_id == 1, (
        f"Expected Mesha (1), got {lagna.ascendant_sign_id} ({lagna.ascendant_sign_name}). "
        f"Ascendant deg: {lagna.ascendant_deg}"
    )
    assert lagna.ascendant_sign_name == "Mesha"


def test_lagna_returns_12_cusps():
    from panchang_engine.lagna import compute_lagna
    lagna = compute_lagna(BIRTH, LAT, LON, TZ)
    assert len(lagna.house_cusps) == 12
    assert all(0 <= c < 360 for c in lagna.house_cusps)


def test_lagna_mc_present():
    from panchang_engine.lagna import compute_lagna
    lagna = compute_lagna(BIRTH, LAT, LON, TZ)
    assert 0 <= lagna.mc_deg < 360


def test_lagna_nakshatra_pada():
    from panchang_engine.lagna import compute_lagna
    lagna = compute_lagna(BIRTH, LAT, LON, TZ)
    assert 1 <= lagna.ascendant_nak_id <= 27
    assert 1 <= lagna.ascendant_pada <= 4
