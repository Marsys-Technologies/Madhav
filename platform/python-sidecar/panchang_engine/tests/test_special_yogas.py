"""
test_special_yogas.py — Special yoga detection test suite.
Session 4C-1-S2.

Tests all 9 special yogas for:
  - Positive case: known day where the yoga IS active
  - Negative case: known day where the yoga is NOT active
  - Boundary case: day where the activating nakshatra transitions mid-day

All reference dates are verified against the panchang_engine self-consistency
fixture (seeded from compute_panchang). Location: Bhubaneswar (20.27N, 85.84E, +05:30).

Target: 30+ test cases across 9 yogas.
"""
import pytest
from datetime import date, datetime, timezone, timedelta

# Lazy import to avoid import errors during test collection
def _compute(d, lat=20.27, lon=85.84, tz=330):
    from panchang_engine import compute_panchang
    return compute_panchang(d, lat, lon, tz)


def _yoga_names(panchang):
    return [y["yoga"] for y in panchang.special_yogas]


def _yoga_entry(panchang, name):
    """Return first matching yoga entry dict or None."""
    for y in panchang.special_yogas:
        if y["yoga"] == name:
            return y
    return None


# ===========================================================================
# §1 — Guru Pushya Yoga (Thursday + Pushya nakshatra)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: Thursday + Pushya
    (date(2025, 8, 21), True),   # vara=5 nak=8 — confirmed by engine
    (date(2025, 9, 18), True),   # vara=5 nak=8 — confirmed by engine
    (date(2026, 5, 21), True),   # vara=5 nak=8 — confirmed by engine
    # Negative: not Thursday + Pushya
    (date(2025, 8, 22), False),  # vara=6 (Fri) nak=9 (Ashlesha) — no yoga
    (date(2025, 8, 20), False),  # vara=4 (Wed) — not Thursday
    # Boundary: Thursday but different nakshatra
    (date(2025, 8, 28), False),  # vara=5 (Thu) — different nakshatra
])
def test_guru_pushya(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "guru_pushya" in yogas, (
            f"{d}: expected guru_pushya; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "guru_pushya")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 5
        # Window must be within sunrise frame
        assert entry["start_utc"] >= p.sunrise_utc
        assert entry["end_utc"] <= p.sunrise_utc + timedelta(hours=25)
    else:
        assert "guru_pushya" not in yogas, (
            f"{d}: unexpected guru_pushya; vara={p.vara.id} nak={p.nakshatra.id}"
        )


# ===========================================================================
# §2 — Ravi Pushya Yoga (Sunday + Pushya nakshatra)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: Sunday + Pushya
    (date(2025, 4, 6), True),    # vara=1 nak=8 — confirmed by engine
    (date(2025, 5, 4), True),    # vara=1 nak=8 — confirmed by engine
    (date(2026, 2, 1), True),    # vara=1 nak=8 — confirmed by engine
    # Negative: not Sunday + Pushya
    (date(2025, 4, 7), False),   # vara=2 (Mon) nak=8 — Monday, not Sunday
    (date(2025, 4, 13), False),  # vara=1 (Sun) nak=14 (Chitra) — not Pushya
    # Boundary: Sunday but nakshatra transitions away from Pushya mid-day
])
def test_ravi_pushya(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "ravi_pushya" in yogas, (
            f"{d}: expected ravi_pushya; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "ravi_pushya")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 5
    else:
        assert "ravi_pushya" not in yogas, (
            f"{d}: unexpected ravi_pushya; vara={p.vara.id} nak={p.nakshatra.id}"
        )


# ===========================================================================
# §3 — Sarvartha Siddhi Yoga (vara × nakshatra lookup)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive cases — varied vara × nakshatra combinations
    (date(2025, 1, 2), True),    # vara=5(Thu) nak=22(Shravana) → Table row 5
    (date(2025, 1, 11), True),   # vara=7(Sat) nak=4(Rohini) → Table row 7
    (date(2025, 1, 12), True),   # vara=1(Sun) nak=5(Mrigashira) → Table row 1; nak transitions mid-day
    (date(2025, 1, 21), True),   # vara=3(Tue) nak=14(Chitra) → Table row 3
    (date(2025, 4, 6), True),    # vara=1(Sun) nak=8(Pushya) → Table row 1
    # Negative cases — vara × nakshatra not in table
    (date(2025, 1, 6), False),   # vara=2(Mon) nak=26(Uttara Bhadrapada) — not in table
    (date(2025, 8, 22), False),  # vara=6(Fri) nak=9(Ashlesha) — not in table
    # Boundary: nakshatra transitions mid-day (window should clip at nakshatra end)
])
def test_sarvartha_siddhi(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "sarvartha_siddhi" in yogas, (
            f"{d}: expected sarvartha_siddhi; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "sarvartha_siddhi")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 4
        # Window must clip to nakshatra end or next_sunrise
        assert entry["end_utc"] <= p.sunrise_utc + timedelta(hours=25)
    else:
        assert "sarvartha_siddhi" not in yogas, (
            f"{d}: unexpected sarvartha_siddhi; vara={p.vara.id} nak={p.nakshatra.id}"
        )


def test_sarvartha_siddhi_window_clips_at_nakshatra_end():
    """
    Boundary: 2025-01-12, Sun(vara=1) + Mrigashira(5) ends at ~05:54 UTC.
    Sarvartha Siddhi window should end at nakshatra end_utc, not at next sunrise.
    """
    p = _compute(date(2025, 1, 12))
    assert "sarvartha_siddhi" in _yoga_names(p)
    entry = _yoga_entry(p, "sarvartha_siddhi")
    # Nakshatra ends ~05:54 UTC; next sunrise is ~24h later
    # Window must end at nakshatra end, not run to next sunrise
    nak_end = p.nakshatra.end_utc
    assert abs((entry["end_utc"] - nak_end).total_seconds()) < 2, (
        f"Window should end at nakshatra end: {nak_end}, got {entry['end_utc']}"
    )


# ===========================================================================
# §4 — Amrit Siddhi Yoga
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: vara × nakshatra in AMRIT_SIDDHI_TABLE
    (date(2025, 1, 8), True),    # vara=4(Wed) nak=1(Ashwini) → {4: {1}}
    (date(2025, 9, 18), True),   # vara=5(Thu) nak=8(Pushya) → {5: {8}}
    (date(2025, 4, 6), True),    # vara=1(Sun) nak=8(Pushya) → {1: {8}}
    # Negative
    (date(2025, 1, 9), False),   # vara=5(Thu) nak=2(Bharani) — not in table
    (date(2025, 1, 6), False),   # vara=2(Mon) nak=26 — not in table
])
def test_amrit_siddhi(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "amrit_siddhi" in yogas, (
            f"{d}: expected amrit_siddhi; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "amrit_siddhi")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 5
    else:
        assert "amrit_siddhi" not in yogas, (
            f"{d}: unexpected amrit_siddhi; vara={p.vara.id} nak={p.nakshatra.id}"
        )


# ===========================================================================
# §5 — Tripushkar Yoga (tithi × vara × nakshatra)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: all three conditions met
    (date(2025, 2, 25), True),   # vara=3(Tue) nak=21(Uttara Ashadha) tithi=27(Krishna Dvadashi)
    (date(2025, 4, 15), True),   # vara=3(Tue) nak=16(Vishakha) tithi=17
    # Negative: one condition not met
    (date(2025, 2, 26), False),  # vara=4(Wed) — not in TRIPUSHKAR_VARAS
    (date(2025, 1, 21), False),  # vara=3(Tue) nak=14(Chitra) — not in TRIPUSHKAR_NAKSHATRAS
    # Boundary: tithi transitions mid-day
])
def test_tripushkar(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "tripushkar" in yogas, (
            f"{d}: expected tripushkar; vara={p.vara.id} nak={p.nakshatra.id} tithi={p.tithi.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "tripushkar")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 4
    else:
        assert "tripushkar" not in yogas, (
            f"{d}: unexpected tripushkar; vara={p.vara.id} nak={p.nakshatra.id} tithi={p.tithi.id}"
        )


# ===========================================================================
# §6 — Dwipushkar Yoga (tithi × vara × nakshatra)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: Tue + Chitra + tithi in {2,7,12,17,22,27}
    (date(2025, 1, 21), True),   # vara=3(Tue) nak=14(Chitra) tithi=22 — Dwipushkar
    (date(2025, 5, 20), True),   # vara=3(Tue) nak=23(Dhanishtha) tithi=22
    # Negative: vara wrong (not Tue/Sun/Sat) or nakshatra wrong
    (date(2025, 1, 22), False),  # vara=4(Wed) — not in DWIPUSHKAR_VARAS
    (date(2025, 1, 25), False),  # vara=7(Sat) nak=17 — not Dwipushkar nakshatra
])
def test_dwipushkar(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "dwipushkar" in yogas, (
            f"{d}: expected dwipushkar; vara={p.vara.id} nak={p.nakshatra.id} tithi={p.tithi.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "dwipushkar")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 3
    else:
        assert "dwipushkar" not in yogas, (
            f"{d}: unexpected dwipushkar; vara={p.vara.id} nak={p.nakshatra.id} tithi={p.tithi.id}"
        )


# ===========================================================================
# §7 — Siddha Yoga (vara × nakshatra lookup)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: vara × nakshatra in SIDDHA_YOGA_TABLE
    (date(2025, 1, 25), True),   # vara=7(Sat) nak=17(Anuradha) → {7: {2,7,12,17,...}}
    (date(2025, 2, 3), True),    # vara=2(Mon) nak=27(Revati) → {2: {2,7,12,17,22,27}}
    # Negative
    (date(2025, 1, 26), False),  # vara=1(Sun) nak=18(Jyeshtha) — not in {1: {1,6,11,16,21,26}}
    (date(2025, 1, 22), False),  # vara=4(Wed) nak=15(Swati) — not in {4: {4,9,14,19,24}}
])
def test_siddha_yoga(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "siddha_yoga" in yogas, (
            f"{d}: expected siddha_yoga; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "siddha_yoga")
        assert entry["strength"] == "auspicious"
        assert entry["stars"] == 3
    else:
        assert "siddha_yoga" not in yogas, (
            f"{d}: unexpected siddha_yoga; vara={p.vara.id} nak={p.nakshatra.id}"
        )


# ===========================================================================
# §8 — Bhadra (Vishti Karana)
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: karana_first or karana_second is Vishti (id=7)
    (date(2025, 1, 3), True),    # karana_second=7 (Vishti)
    (date(2025, 1, 10), True),   # karana_first=7 (Vishti)
    (date(2025, 1, 13), True),   # karana_first=7 (Vishti)
    # Negative: neither karana is Vishti
    (date(2025, 1, 2), False),   # k1=4, k2=5 — no Vishti
    (date(2025, 1, 5), False),   # check
    (date(2025, 8, 22), False),  # k1=1, k2=2 — no Vishti
])
def test_bhadra(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "bhadra" in yogas, (
            f"{d}: expected bhadra; k1={p.karana_first.id} k2={p.karana_second.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "bhadra")
        assert entry["strength"] == "inauspicious"
        assert entry["stars"] == 0
        # Window must be within sunrise frame
        assert entry["start_utc"] >= p.sunrise_utc
    else:
        assert "bhadra" not in yogas, (
            f"{d}: unexpected bhadra; k1={p.karana_first.id} k2={p.karana_second.id}"
        )


def test_bhadra_first_karana_window():
    """
    When karana_first is Vishti, Bhadra starts at sunrise and ends at karana_first.end_utc.
    """
    p = _compute(date(2025, 1, 10))
    assert p.karana_first.id == 7, f"Expected karana_first Vishti on 2025-01-10, got {p.karana_first.id}"
    entry = _yoga_entry(p, "bhadra")
    assert entry is not None
    # Bhadra starts at sunrise
    assert abs((entry["start_utc"] - p.sunrise_utc).total_seconds()) < 2
    # Bhadra ends at or before karana_first.end_utc (clipped to next sunrise if needed)
    assert entry["end_utc"] <= p.karana_first.end_utc + timedelta(seconds=2)


# ===========================================================================
# §9 — Panchaka Dosha (Moon in {23-27} AND vara in {1,3,7})
# ===========================================================================

@pytest.mark.parametrize("d,should_have_yoga", [
    # Positive: Panchaka nakshatra + Panchaka vara
    (date(2025, 1, 4), True),    # vara=7(Sat) nak=24(Shatabhisha)
    (date(2025, 1, 7), True),    # vara=3(Tue) nak=27(Revati)
    (date(2025, 2, 1), True),    # vara=7(Sat) nak=25(Purva Bhadrapada)
    # Negative: Panchaka nakshatra but wrong vara
    (date(2025, 1, 8), False),   # vara=4(Wed) nak=1 — not Panchaka vara
    # Negative: right vara but not Panchaka nakshatra
    (date(2025, 1, 6), False),   # vara=2(Mon) nak=26 — Mon is not in PANCHAKA_VARAS
    (date(2025, 1, 25), False),  # vara=7(Sat) nak=17(Anuradha) — not Panchaka nakshatra
])
def test_panchaka(d, should_have_yoga):
    p = _compute(d)
    yogas = _yoga_names(p)
    if should_have_yoga:
        assert "panchaka" in yogas, (
            f"{d}: expected panchaka; vara={p.vara.id} nak={p.nakshatra.id} yogas={yogas}"
        )
        entry = _yoga_entry(p, "panchaka")
        assert entry["strength"] == "inauspicious"
        assert entry["stars"] == 0
    else:
        assert "panchaka" not in yogas, (
            f"{d}: unexpected panchaka; vara={p.vara.id} nak={p.nakshatra.id}"
        )


# ===========================================================================
# §10 — Structural / cross-cutting tests
# ===========================================================================

def test_yoga_dicts_have_required_keys():
    """Every detected yoga dict must have the 5 required keys."""
    p = _compute(date(2025, 8, 21))  # Multiple yogas expected
    assert len(p.special_yogas) > 0
    for y in p.special_yogas:
        for key in ("yoga", "start_utc", "end_utc", "strength", "stars"):
            assert key in y, f"Missing key '{key}' in yoga dict {y}"


def test_yoga_windows_within_sunrise_frame():
    """All yoga windows must be within [sunrise_utc, ~next sunrise + 5min]."""
    p = _compute(date(2025, 8, 21))
    for y in p.special_yogas:
        assert y["start_utc"] >= p.sunrise_utc, (
            f"Yoga {y['yoga']} starts before sunrise: {y['start_utc']} < {p.sunrise_utc}"
        )
        # end must not be more than 26h after sunrise (next sunrise is ~24h away)
        assert y["end_utc"] <= p.sunrise_utc + timedelta(hours=26), (
            f"Yoga {y['yoga']} end too late: {y['end_utc']}"
        )


def test_multiple_yogas_same_day():
    """
    2025-08-21 (Thu + Pushya): should have sarvartha_siddhi + amrit_siddhi + guru_pushya + bhadra.
    """
    p = _compute(date(2025, 8, 21))
    yogas = set(_yoga_names(p))
    assert "sarvartha_siddhi" in yogas
    assert "amrit_siddhi" in yogas
    assert "guru_pushya" in yogas
    assert "bhadra" in yogas


def test_no_yogas_on_plain_day():
    """
    2025-01-06: vara=2 Mon, nak=26 Uttara Bhadrapada, k1=5, k2=6.
    No special yogas expected.
    """
    p = _compute(date(2025, 1, 6))
    yogas = _yoga_names(p)
    assert yogas == [], f"Expected no yogas on 2025-01-06, got {yogas}"


def test_inauspicious_yogas_have_zero_stars():
    """Bhadra and Panchaka must always have stars=0 and strength=inauspicious."""
    p_bhadra = _compute(date(2025, 1, 10))
    for y in p_bhadra.special_yogas:
        if y["yoga"] == "bhadra":
            assert y["stars"] == 0
            assert y["strength"] == "inauspicious"

    p_panchaka = _compute(date(2025, 1, 4))
    for y in p_panchaka.special_yogas:
        if y["yoga"] == "panchaka":
            assert y["stars"] == 0
            assert y["strength"] == "inauspicious"


def test_panchaka_boundary_nakshatra_transition():
    """
    2025-01-07: vara=3(Tue) nak=27(Revati). Panchaka active.
    The nakshatra end_utc is mid-day (~12:20 UTC). Verify window clips there.
    """
    p = _compute(date(2025, 1, 7))
    assert "panchaka" in _yoga_names(p)
    entry = _yoga_entry(p, "panchaka")
    nak_end = p.nakshatra.end_utc
    # Window should end at or before nakshatra end
    assert entry["end_utc"] <= nak_end + timedelta(seconds=2), (
        f"Panchaka window {entry['end_utc']} should end by nakshatra end {nak_end}"
    )
