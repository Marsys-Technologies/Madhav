"""
test_calendrical.py — Calendrical computation tests.
FORENSIC: birth 1984-02-05, sun_lon ~321.5° (Makara/Capricorn sidereal).
"""
from datetime import date


def test_birth_ayana():
    """Birth date 1984-02-05: Sun in Makara (lon ~321°) → Uttarayana."""
    from panchang_engine.calendrical import compute_calendrical
    cal = compute_calendrical(date(1984, 2, 5), sun_lon=321.5, tithi_id=3, paksha="shukla")
    assert cal.ayana == "Uttarayana", f"Got: {cal.ayana}"


def test_birth_ritu():
    """Sun in Makara (sign 10) → Hemanta or Shishira ritu."""
    from panchang_engine.calendrical import compute_calendrical
    cal = compute_calendrical(date(1984, 2, 5), sun_lon=321.5, tithi_id=3, paksha="shukla")
    # Makara=sign 10 → Hemanta; Kumbha=sign 11 → Shishira. sun_lon=321.5 → sign 10 (Makara)
    assert cal.ritu in ("Hemanta", "Shishira"), f"Got: {cal.ritu}"


def test_samvat_formulas_2026():
    """For 2026: kali=5128, shaka=1948."""
    from panchang_engine.calendrical import compute_calendrical
    cal = compute_calendrical(date(2026, 6, 9), sun_lon=55.0, tithi_id=1, paksha="shukla")
    assert cal.kali_samvat == 5128, f"Got kali={cal.kali_samvat}"
    assert cal.shaka_samvat == 1948, f"Got shaka={cal.shaka_samvat}"


def test_jovian_year_range():
    """Jovian year number must be 1..60 and name in the 60-cycle list."""
    from panchang_engine.calendrical import compute_calendrical
    from panchang_engine.shastra_tables import JOVIAN_60_YEAR_NAMES
    cal = compute_calendrical(date(2026, 6, 9), sun_lon=55.0, tithi_id=1, paksha="shukla")
    assert 1 <= cal.jovian_year_number <= 60, f"Got: {cal.jovian_year_number}"
    assert cal.jovian_year_name in JOVIAN_60_YEAR_NAMES, f"Got: {cal.jovian_year_name}"


def test_masa_purnimanta_makara():
    """Sun in Makara (sign 10) → masa Magha."""
    from panchang_engine.calendrical import compute_calendrical
    cal = compute_calendrical(date(1984, 2, 5), sun_lon=321.5, tithi_id=3, paksha="shukla")
    assert cal.masa_purnimanta == "Magha", f"Got: {cal.masa_purnimanta}"


def test_sankranti_flag():
    """Sun within 0.5° of sign boundary triggers sankranti_name."""
    from panchang_engine.calendrical import compute_calendrical
    # sun_lon=0.2 → within 0.5° of entering Mesha
    cal = compute_calendrical(date(2026, 4, 14), sun_lon=0.2, tithi_id=1, paksha="shukla")
    assert cal.sankranti_name is not None, "Expected sankranti at sign entry"
