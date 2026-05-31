"""Internal-consistency tests for panchanga."""
from __future__ import annotations

from pyjhora_adapter import panchanga

_ANGAS = ["tithi", "vara", "nakshatra", "yoga", "karana"]


def test_panchanga_all_angas_nonempty(native_jd):
    p = panchanga.compute_panchanga(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    for anga in _ANGAS:
        assert anga in p
        assert isinstance(p[anga], str)
        assert p[anga].strip() != "", f"{anga} is empty"


def test_native_panchanga_values(native_jd):
    """FORENSIC spot-check (internal consistency): native panchanga under Lahiri
    is tithi=Shukla Tritiya, vara=Ravivara, nakshatra=Purva Bhadrapada,
    yoga=Shiva, karana=Garaja."""
    p = panchanga.compute_panchanga(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    assert p["tithi"] == "Shukla Tritiya"
    assert p["vara"] == "Ravivara"
    assert p["nakshatra"] == "Purva Bhadrapada"
    assert p["yoga"] == "Shiva"
    assert p["karana"] == "Garaja"
