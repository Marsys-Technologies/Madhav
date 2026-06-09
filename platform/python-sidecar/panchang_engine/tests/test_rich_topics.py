"""
test_rich_topics.py — Tests for rich_topics.py computations.
"""
from datetime import datetime, date, timezone, timedelta

BIRTH = datetime(1984, 2, 5, 10, 43, 0)
LAT, LON, TZ = 20.27, 85.84, 330


# ---- Topic 4: Sun/Moon dynamics ----
def test_sun_moon_dynamics():
    import swisseph as swe
    from panchang_engine.rich_topics import compute_sun_moon_dynamics
    instant_utc = BIRTH - timedelta(minutes=TZ)
    jd = swe.julday(instant_utc.year, instant_utc.month, instant_utc.day,
                    instant_utc.hour + instant_utc.minute / 60.0)
    result = compute_sun_moon_dynamics(jd)
    assert 0 <= result.moon_illumination_pct <= 100
    assert 0 <= result.sun_moon_separation_deg < 360


# ---- Topic 10: Anandadi Yoga ----
def test_anandadi_formula():
    from panchang_engine.rich_topics import compute_anandadi_yoga
    # vara=1, nak=1 → (1+1-2)%28 = 0 → index 0 = "Ananda" (yoga_number=1)
    yoga = compute_anandadi_yoga(vara_id=1, nakshatra_id=1)
    assert yoga.yoga_name == "Ananda"
    assert yoga.yoga_number == 1

def test_anandadi_range():
    from panchang_engine.rich_topics import compute_anandadi_yoga
    yoga = compute_anandadi_yoga(vara_id=1, nakshatra_id=25)
    assert 1 <= yoga.yoga_number <= 28
    assert yoga.yoga_name


# ---- Topic 11: Vasa family ----
def test_vasa_all_fields():
    from panchang_engine.rich_topics import compute_vasa_family
    vasa = compute_vasa_family(tithi_id=3, vara_id=1, nakshatra_id=25)
    assert vasa.agni_vasa in ("Prithvi", "Jala", "Vayu", "Akasha")
    assert vasa.disha_vasa in ("East", "West", "North", "South")
    assert vasa.rahu_vasa in ("East", "West", "North", "South")
    assert vasa.nakshatra_vasa in ("East", "West", "North", "South")
    assert vasa.bhadra_vasa


# ---- Topic 12: 5-Panchaka ----
def test_panchaka_active():
    from panchang_engine.rich_topics import compute_panchaka
    p = compute_panchaka(nakshatra_id=27)  # Revati → Mrityu
    assert p.active is True
    assert p.panchaka_type == "Mrityu"

def test_panchaka_inactive():
    from panchang_engine.rich_topics import compute_panchaka
    p = compute_panchaka(nakshatra_id=1)  # Ashwini → not Panchaka
    assert p.active is False
    assert p.panchaka_type is None


# ---- Topic 15: Shoonya ----
def test_shoonya_present():
    from panchang_engine.rich_topics import compute_shoonya
    s = compute_shoonya(tithi_id=3, nakshatra_id=25)
    assert s.tithi_shoonya_sign_id is not None
    assert s.nakshatra_shoonya_sign_id is not None


# ---- Topic 19: Window membership ----
def test_window_membership():
    from panchang_engine.rich_topics import compute_window_membership
    from panchang_engine.types import Timing
    import datetime as dt_mod
    now_utc = dt_mod.datetime(1984, 2, 5, 5, 0, 0, tzinfo=dt_mod.timezone.utc)
    rahu = Timing("rahu_kalam",
        dt_mod.datetime(1984, 2, 5, 4, 0, tzinfo=dt_mod.timezone.utc),
        dt_mod.datetime(1984, 2, 5, 5, 30, tzinfo=dt_mod.timezone.utc))
    result = compute_window_membership(now_utc, [rahu], [], [], [])
    assert "rahu_kalam" in result.inauspicious_active


# ---- Topic 20: Micro-timing ----
def test_micro_timing():
    from panchang_engine.rich_topics import compute_micro_timing
    sunrise = datetime(1984, 2, 5, 1, 10, 0, tzinfo=timezone.utc)   # ~6:40 IST
    instant = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)   # ~10:43 IST
    mt = compute_micro_timing(instant, sunrise)
    assert mt.ghati_from_sunrise >= 0
    assert 1 <= mt.muhurta_of_day <= 30
    assert 1 <= mt.pranapada_sign_id <= 12


# ---- Topic 1 extended: Anga attributes ----
def test_tithi_attrs():
    from panchang_engine.rich_topics import compute_tithi_attrs
    a = compute_tithi_attrs(tithi_id=3)
    assert a.lord
    assert a.deity
    assert a.anga_type in ("Nanda", "Bhadra", "Jaya", "Rikta", "Poorna")

def test_nakshatra_attrs():
    from panchang_engine.rich_topics import compute_nakshatra_attrs
    a = compute_nakshatra_attrs(nak_id=1)  # Ashwini
    assert a.lord == "Ketu"
