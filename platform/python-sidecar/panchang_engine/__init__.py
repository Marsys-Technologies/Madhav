"""
panchang_engine — Deterministic Panchang computation, Drik-parity, no LLM.
Public API: compute_panchang, panchang_range, find_muhurat.
"""
__version__ = "1.0.0-S1"

from .ayanamsha import set_ayanamsha, get_ayanamsha_value, DEFAULT_AYANAMSHA
from .types import Panchang, Anga, Timing, PlanetState, MuhuratWindow, NatalChart
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
        Panchang dataclass fully populated (special_yogas=[] this session).
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
        special_yogas=[],  # 4C-1-S2 implements
        planets=planets,
        computation_version=__version__,
        ephemeris_version=ephe_ver,
    )


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


def find_muhurat(event: str, date_from, date_to, lat: float, lon: float, native_chart=None):
    """
    STUB — 4C.6 implements Muhurat Finder. 4C-1-S1 only wires the entry point.
    Args:
        event: str — e.g. "vivaha", "griha_pravesh", "business_start"
        date_from: datetime.date — search window start
        date_to: datetime.date — search window end
        lat, lon: float — location
        native_chart: NatalChart | None — for dasha-aware scoring
    Raises:
        NotImplementedError — always; implemented in 4C.6
    """
    raise NotImplementedError(
        "4C.6 implements Muhurat Finder. 4C-1-S1 only wires the entry point. "
        f"Event='{event}', window={date_from}..{date_to}."
    )
