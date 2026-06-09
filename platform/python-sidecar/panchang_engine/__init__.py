"""
panchang_engine — Deterministic Panchang computation, Drik-parity, no LLM.

Public API (canonical — P2 re-arch, 2026-06-09):
  panchanga_instant(instant, lat, lon, tz_offset)  → PanchangaInstant
  panchanga_day(date, lat, lon, tz_offset)          → Panchang
  compute_panchang(date, lat, lon, tz_offset)       → Panchang  (alias for panchanga_day)
  panchang_range(date_from, date_to, lat, lon, tz_offset) → list[Panchang]
  find_muhurat(...)                                 → list[MuhuratWindow]

L0 Brahmagyan service asset — deterministic core, zero scoring/judgement.
Muhurat scoring lives in the sibling `muhurat/` package.
"""
__version__ = "2.0.0-P2"  # P2 = panchanga_instant + panchanga_day APIs (2026-06-09)

from .ayanamsha import set_ayanamsha, get_ayanamsha_value, DEFAULT_AYANAMSHA
from .types import Panchang, PanchangaInstant, Anga, Timing, PlanetState, MuhuratWindow, NatalChart
from .exceptions import (
    PanchangEngineError, AyanamshaError, OutOfRangeError, ValidationError,
)


def compute_panchang(date, lat: float, lon: float, tz_offset: int) -> "Panchang":
    """
    High-level: full Panchang for a single day.
    Args:
        date: datetime.date — the LOCAL calendar date
        lat: float — latitude in decimal degrees (+N)
        lon: float — longitude in decimal degrees (+E)
        tz_offset: int — UTC offset in minutes (e.g. +330 for IST +05:30)
    Returns:
        Panchang dataclass fully populated including special_yogas (implemented 4C-1-S2).
    """
    from datetime import date as dt_date
    from .timings import (
        compute_sunrise_sunset, compute_moonrise_moonset,
        compute_inauspicious_timings, compute_auspicious_timings,
        compute_choghadiya, compute_hora,
    )
    from .planets import compute_all_grahas
    from .angas import (
        compute_tithi, compute_nakshatra, compute_yoga,
        compute_karana_pair, compute_vara,
    )
    from .special_yogas import detect_all_special_yogas
    import swisseph as swe
    from datetime import datetime, timezone

    if not isinstance(date, dt_date):
        raise ValidationError(f"date must be datetime.date, got {type(date)}")
    if not (-90 <= lat <= 90):
        raise ValidationError(f"lat out of range: {lat}")
    if not (-180 <= lon <= 180):
        raise ValidationError(f"lon out of range: {lon}")

    # Set ayanamsha to Lahiri (project default)
    set_ayanamsha("lahiri")

    # Sunrise / sunset
    sunrise_utc, sunset_utc = compute_sunrise_sunset(date, lat, lon, tz_offset)

    # Moonrise / moonset
    moonrise_utc, moonset_utc = compute_moonrise_moonset(date, lat, lon, tz_offset)

    # JD at sunrise for planetary computations
    jd_sunrise = _datetime_to_jd(sunrise_utc)

    # Planetary state at sunrise
    planets = compute_all_grahas(jd_sunrise)

    # Sun and Moon longitudes at sunrise
    sun_lon = next(p.longitude_sidereal for p in planets if p.name == "Sun")
    moon_lon = next(p.longitude_sidereal for p in planets if p.name == "Moon")

    # The 5 angas
    tithi = compute_tithi(sun_lon, moon_lon, sunrise_utc)
    nakshatra = compute_nakshatra(moon_lon, sunrise_utc)
    yoga = compute_yoga(sun_lon, moon_lon, sunrise_utc)
    karana_first, karana_second = compute_karana_pair(sun_lon, moon_lon, sunrise_utc, sunrise_utc)
    vara = compute_vara(date)

    # Paksha
    tithi_num = tithi.id
    paksha = "shukla" if tithi_num <= 15 else "krishna"

    # Inauspicious timings
    inauspicious_dict = compute_inauspicious_timings(sunrise_utc, sunset_utc, vara.id)
    inauspicious = list(inauspicious_dict.values())

    # Auspicious timings
    auspicious_dict = compute_auspicious_timings(sunrise_utc, sunset_utc, vara.id, tithi.id, nakshatra.id)
    auspicious = [t for t in auspicious_dict.values() if t is not None]

    # Choghadiya — need next-day sunrise
    from datetime import timedelta
    next_date = date + timedelta(days=1)
    next_sunrise_utc, _ = compute_sunrise_sunset(next_date, lat, lon, tz_offset)

    choghadiya = compute_choghadiya(sunrise_utc, sunset_utc, next_sunrise_utc, vara.id)
    hora = compute_hora(sunrise_utc, next_sunrise_utc, vara.id)

    # Special yogas (implemented 4C-1-S2)
    special_yogas = detect_all_special_yogas(
        sunrise_utc, sunset_utc, next_sunrise_utc,
        tithi, nakshatra, yoga, karana_first, karana_second, vara,
    )

    # ephemeris version
    swe.set_ephe_path(None)
    ephe_ver = swe.version

    return Panchang(
        date=date,
        lat=lat,
        lon=lon,
        tz_offset_minutes=tz_offset,
        sunrise_utc=sunrise_utc,
        sunset_utc=sunset_utc,
        moonrise_utc=moonrise_utc,
        moonset_utc=moonset_utc,
        tithi=tithi,
        nakshatra=nakshatra,
        yoga=yoga,
        karana_first=karana_first,
        karana_second=karana_second,
        vara=vara,
        paksha=paksha,
        inauspicious=inauspicious,
        auspicious=auspicious,
        choghadiya=choghadiya,
        hora=hora,
        special_yogas=special_yogas,
        planets=planets,
        computation_version=__version__,
        ephemeris_version=ephe_ver,
    )


def panchanga_instant(instant, lat: float, lon: float, tz_offset: int) -> "PanchangaInstant":
    """
    Compute panchang state at the exact given datetime (birth moment / event instant).

    Unlike compute_panchang / panchanga_day (sunrise-based), all angas are
    computed from planetary positions at the precise instant — correct for
    birth-chart queries and any moment where the ruling anga at that exact
    second is required.

    Args:
        instant: datetime.datetime — LOCAL time at the given tz_offset.
                 naive (no tzinfo) — offset applied internally.
        lat:        float — latitude decimal degrees (+N)
        lon:        float — longitude decimal degrees (+E)
        tz_offset:  int   — UTC offset in minutes (e.g. +330 for IST +05:30)

    Returns:
        PanchangaInstant — angas at the exact moment; floor-to-absent contract
        for extended topics (topics_computed lists what is present).

    FORENSIC gate (acharya-grade invariant):
        panchanga_instant(datetime(1984,2,5,10,43), 20.27, 85.84, 330) must return
        tithi="Shukla Tritiya", nakshatra="Purva Bhadrapada", yoga="Shiva",
        karana="Garaja", vara="Ravivara".
    """
    from datetime import timedelta
    from .timings import compute_sunrise_sunset
    from .planets import compute_all_grahas
    from .angas import (
        compute_tithi, compute_nakshatra, compute_yoga,
        compute_karana_pair, compute_vara,
    )
    import swisseph as swe

    if not isinstance(instant, _datetime_type()):
        raise ValidationError(f"instant must be datetime.datetime, got {type(instant)}")
    if not (-90 <= lat <= 90):
        raise ValidationError(f"lat out of range: {lat}")
    if not (-180 <= lon <= 180):
        raise ValidationError(f"lon out of range: {lon}")

    # Set ayanamsha to Lahiri (project default)
    set_ayanamsha("lahiri")

    # Convert local instant to UTC
    instant_utc = instant - timedelta(minutes=tz_offset)

    # Julian Day at this exact moment
    jd = _datetime_to_jd(instant_utc)

    # Planetary positions at the exact instant
    planets = compute_all_grahas(jd)
    sun_lon = next(p.longitude_sidereal for p in planets if p.name == "Sun")
    moon_lon = next(p.longitude_sidereal for p in planets if p.name == "Moon")

    # All 5 angas at the instant (not sunrise-based)
    tithi = compute_tithi(sun_lon, moon_lon, instant_utc)
    nakshatra = compute_nakshatra(moon_lon, instant_utc)
    yoga = compute_yoga(sun_lon, moon_lon, instant_utc)
    karana_first, karana_second = compute_karana_pair(sun_lon, moon_lon, instant_utc, instant_utc)

    # Vara from the local calendar date (day of week is date-level, not moment-level)
    local_date = instant.date()
    vara = compute_vara(local_date)

    paksha = "shukla" if tithi.id <= 15 else "krishna"

    swe.set_ephe_path(None)
    ephe_ver = swe.version

    return PanchangaInstant(
        instant_utc=instant_utc,
        lat=lat,
        lon=lon,
        tz_offset_minutes=tz_offset,
        tithi=tithi,
        nakshatra=nakshatra,
        yoga=yoga,
        karana=karana_first,
        karana_next=karana_second,
        vara=vara,
        paksha=paksha,
        planets=list(planets),
        computation_version=__version__,
        ephemeris_version=ephe_ver,
        topics_computed=["angas", "planets"],
    )


def panchanga_day(date, lat: float, lon: float, tz_offset: int) -> "Panchang":
    """
    Return the full Panchang for a calendar day at the given location.

    Equivalent to compute_panchang(); canonical name per P2 re-arch (2026-06-09).
    Angas are sunrise-based (the ruling anga at the moment of sunrise).
    For anga at an exact moment (e.g. birth time), use panchanga_instant().

    Args:
        date:      datetime.date — local calendar date
        lat, lon:  float — decimal degrees
        tz_offset: int   — UTC offset in minutes

    Returns:
        Panchang — full day record including timings, choghadiya, hora,
        special yogas, and 9 graha states at sunrise.
    """
    return compute_panchang(date, lat, lon, tz_offset)


def _datetime_type():
    from datetime import datetime
    return datetime


def _datetime_to_jd(dt) -> float:
    """Convert a UTC datetime to Julian Day (UT)."""
    import swisseph as swe
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def panchang_range(date_from, date_to, lat: float, lon: float, tz_offset: int) -> list:
    """
    Compute Panchang for a range of dates (inclusive).
    Args:
        date_from: datetime.date — start date (local)
        date_to: datetime.date — end date (local, inclusive)
    Returns:
        list[Panchang]
    """
    from datetime import timedelta
    results = []
    current = date_from
    while current <= date_to:
        results.append(compute_panchang(current, lat, lon, tz_offset))
        current += timedelta(days=1)
    return results


def find_muhurat(
    event: str,
    date_from,
    date_to,
    lat: float,
    lon: float,
    tz_offset_minutes: int,
    native_chart=None,
    weights=None,
    top_n: int = 10,
):
    """
    Return top auspicious windows for event in [date_from, date_to].
    Implemented in 4C-6-S1 (muhurat.py); this function delegates to it.

    Args:
        event: str — e.g. "vivah", "griha_pravesh"
        date_from: datetime.date — search window start (inclusive)
        date_to: datetime.date — search window end (inclusive)
        lat, lon: float — location
        tz_offset_minutes: int — UTC offset in minutes (default 330 = IST)
        native_chart: NatalChart | None — for Tara Bala native overlay
        weights: dict | None — custom weights; defaults to YAML-loaded per-event weights
                 from config/muhurat_weights.yaml
        top_n: int — number of top windows to return
    Returns:
        list[MuhuratWindow] sorted by score descending
    """
    from muhurat.finder import find_muhurat as _find_muhurat
    return _find_muhurat(
        event, date_from, date_to, lat, lon,
        tz_offset_minutes=tz_offset_minutes,
        native_chart=native_chart,
        weights=weights,
        top_n=top_n,
    )
