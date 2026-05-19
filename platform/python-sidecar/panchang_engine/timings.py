"""
timings.py — Sunrise/sunset, moonrise/moonset, inauspicious and auspicious
timings, Choghadiya, and planetary Hora computation.

Sunrise definition (Drik Panchang convention):
  The moment the visible upper limb of the Sun appears at the horizon,
  accounting for atmospheric refraction (~34 arcmin) and the semi-diameter
  of the Sun (~16 arcmin). In swisseph this is achieved by using
  swe.CALC_RISE with swe.BIT_DISC_CENTER *not* set — the default (no center
  flag) gives upper-limb rise, which is the Drik standard.
  NOTE: Despite the name "BIT_DISC_CENTER", NOT using this flag is correct.
  See README §5 for the full explanation. This counter-intuitive naming
  in swisseph is a known source of confusion.

References:
  MC  = Muhurta Chintamani
  BS  = Brihat Samhita
  DP  = Drik Panchang (drikpanchang.com) published convention
"""
import swisseph as swe
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from .types import Timing
from .exceptions import OutOfRangeError
from .shastra_tables import (
    RAHU_KALAM_INDEX, YAMAGANDAM_INDEX, GULIKA_INDEX,
    CHOGHADIYA_DAY_TABLE, CHOGHADIYA_NIGHT_TABLE,
    HORA_CYCLE, VARA_HORA_START,
    DUR_MUHURTA_TABLE, AMRIT_KALAM_TABLE, VARJYAM_TABLE,
)

# Atmospheric refraction flag (default — 0 means use atmospheric refraction)
_RISE_FLAG = 0   # No special flags: uses upper limb + atmospheric refraction (Drik standard)
# See note above: BIT_DISC_CENTER is explicitly NOT set.


def _datetime_to_jd(dt: datetime) -> float:
    """Convert a UTC datetime to Julian Day (UT)."""
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def _date_to_jd_local_noon(d: date, tz_offset: int) -> float:
    """
    Convert a local calendar date to a JD near local noon (as UTC).
    tz_offset is in minutes (e.g. 330 for IST +05:30).
    """
    # Local noon in UTC = 12:00 local - tz_offset minutes
    noon_utc_hours = 12.0 - tz_offset / 60.0
    return swe.julday(d.year, d.month, d.day, noon_utc_hours)


def _jd_to_utc(jd: float) -> datetime:
    """Convert Julian Day (UT) to UTC datetime."""
    y, mo, day, h = swe.revjul(jd)
    hour_int = int(h)
    minute_int = int((h - hour_int) * 60)
    second_int = int(((h - hour_int) * 60 - minute_int) * 60)
    # Clamp to valid range
    second_int = max(0, min(59, second_int))
    minute_int = max(0, min(59, minute_int))
    hour_int = max(0, min(23, hour_int))
    return datetime(y, mo, day, hour_int, minute_int, second_int, tzinfo=timezone.utc)


def compute_sunrise_sunset(d: date, lat: float, lon: float,
                           tz_offset: int) -> tuple[datetime, datetime]:
    """
    Compute sunrise and sunset for the local date at the given coordinates.

    Uses swe.rise_trans with CALC_RISE / CALC_SET. Atmospheric refraction
    and upper-limb convention are the default — BIT_DISC_CENTER is NOT set,
    which is correct for Drik Panchang parity. See module docstring for
    the explanation of this counter-intuitive flag naming.

    Args:
        d: local calendar date
        lat: latitude in decimal degrees (+N)
        lon: longitude in decimal degrees (+E)
        tz_offset: UTC offset in minutes (e.g. 330 for IST +05:30)

    Returns:
        (sunrise_utc, sunset_utc) — both timezone-aware UTC datetimes.

    Raises:
        OutOfRangeError: polar latitudes where Sun doesn't rise or set.
    """
    geopos = (lon, lat, 0.0)   # swisseph wants (lon, lat, alt_metres)
    jd_start = _date_to_jd_local_noon(d, tz_offset) - 0.75   # ~6 hours before noon local = start of day

    # Sunrise
    sunrise_result = swe.rise_trans(
        jd_start, swe.SUN, None, swe.CALC_RISE, geopos, 1013.25, 10.0
    )
    if sunrise_result[0] == -2:
        raise OutOfRangeError(
            f"Sun does not rise on {d} at lat={lat}, lon={lon} (polar region or ephemeris limit)."
        )
    sunrise_jd = sunrise_result[1][0]
    sunrise_utc = _jd_to_utc(sunrise_jd)

    # Sunset — search from shortly after sunrise
    sunset_result = swe.rise_trans(
        sunrise_jd + 0.1, swe.SUN, None, swe.CALC_SET, geopos, 1013.25, 10.0
    )
    if sunset_result[0] == -2:
        raise OutOfRangeError(
            f"Sun does not set on {d} at lat={lat}, lon={lon} (polar region or ephemeris limit)."
        )
    sunset_jd = sunset_result[1][0]
    sunset_utc = _jd_to_utc(sunset_jd)

    return sunrise_utc, sunset_utc


def compute_moonrise_moonset(d: date, lat: float, lon: float,
                             tz_offset: int) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Compute moonrise and moonset for the local date.

    May return None if the Moon doesn't rise or set on the local date
    (normal at high latitudes — not an error).

    Args:
        d: local calendar date
        lat, lon: decimal degrees
        tz_offset: UTC offset in minutes

    Returns:
        (moonrise_utc, moonset_utc) — None where not applicable.
    """
    geopos = (lon, lat, 0.0)
    jd_start = _date_to_jd_local_noon(d, tz_offset) - 0.75

    moonrise_utc = None
    moonset_utc = None

    # Moonrise
    r = swe.rise_trans(jd_start, swe.MOON, None, swe.CALC_RISE, geopos, 1013.25, 10.0)
    if r[0] == 0 and r[1][0] > 0:
        moonrise_utc = _jd_to_utc(r[1][0])

    # Moonset — search from a bit before start to capture moonsets early in the day
    s = swe.rise_trans(jd_start, swe.MOON, None, swe.CALC_SET, geopos, 1013.25, 10.0)
    if s[0] == 0 and s[1][0] > 0:
        moonset_utc = _jd_to_utc(s[1][0])

    return moonrise_utc, moonset_utc


def _inauspicious_segment(sunrise_utc: datetime, sunset_utc: datetime,
                          segment_index: int, label: str) -> Timing:
    """
    Divide the day (sunrise→sunset) into 8 equal parts and return
    the segment at 1-based `segment_index` as a Timing object.
    """
    day_seconds = (sunset_utc - sunrise_utc).total_seconds()
    segment_seconds = day_seconds / 8.0
    start = sunrise_utc + timedelta(seconds=(segment_index - 1) * segment_seconds)
    end = sunrise_utc + timedelta(seconds=segment_index * segment_seconds)
    return Timing(label=label, start_utc=start, end_utc=end)


def compute_inauspicious_timings(sunrise_utc: datetime, sunset_utc: datetime,
                                 vara_id: int) -> dict[str, Timing]:
    """
    Compute inauspicious Muhurta periods for the day.

    Rahu Kalam, Yamagandam, Gulika Kalam:
      Day (sunrise→sunset) split into 8 equal parts; the table index
      identifies which part is inauspicious for each period.
      Source: DP published tables (RAHU_KALAM_INDEX etc. in shastra_tables.py).

    Dur Muhurta:
      Variable; 1–2 windows per day. Computed from DUR_MUHURTA_TABLE.
      1 ghatika = 24 minutes; offset from sunrise.
      Source: MC §9.

    Args:
        sunrise_utc, sunset_utc: UTC datetimes
        vara_id: 1 (Sun) .. 7 (Sat)

    Returns:
        dict with keys 'rahu_kalam', 'yamagandam', 'gulika_kalam',
        and 'dur_muhurta_1' (+ 'dur_muhurta_2' if applicable).
    """
    result: dict[str, Timing] = {}

    # Rahu Kalam
    rahu_idx = RAHU_KALAM_INDEX[vara_id]
    result["rahu_kalam"] = _inauspicious_segment(sunrise_utc, sunset_utc, rahu_idx, "rahu_kalam")

    # Yamagandam
    yama_idx = YAMAGANDAM_INDEX[vara_id]
    result["yamagandam"] = _inauspicious_segment(sunrise_utc, sunset_utc, yama_idx, "yamagandam")

    # Gulika Kalam
    guli_idx = GULIKA_INDEX[vara_id]
    result["gulika_kalam"] = _inauspicious_segment(sunrise_utc, sunset_utc, guli_idx, "gulika_kalam")

    # Dur Muhurta (MC §9; 1 ghatika = 24 minutes)
    ghatika_seconds = 24 * 60  # 1 ghatika = 24 minutes = 1440 seconds
    dur_entries = DUR_MUHURTA_TABLE.get(vara_id, [])
    for i, (offset_ghatika, duration_ghatika) in enumerate(dur_entries, 1):
        start = sunrise_utc + timedelta(seconds=offset_ghatika * ghatika_seconds)
        end = sunrise_utc + timedelta(seconds=(offset_ghatika + duration_ghatika) * ghatika_seconds)
        result[f"dur_muhurta_{i}"] = Timing(label=f"dur_muhurta_{i}", start_utc=start, end_utc=end)

    return result


def compute_auspicious_timings(sunrise_utc: datetime, sunset_utc: datetime,
                               vara_id: int,
                               tithi_id: int = 0,
                               nakshatra_id: int = 0) -> dict[str, Optional[Timing]]:
    """
    Compute auspicious Muhurta periods for the day.

    Brahma Muhurta:
      96 minutes before sunrise to 48 minutes before sunrise.
      Source: DP convention (commonly cited as 2 muhurtas = 48 min each = 96 min before sunrise).

    Abhijit Muhurta:
      The 8th muhurta of the day, centered on solar noon.
      Day is divided into 15 equal muhurtas (sunrise→sunset);
      Abhijit is the middle (8th) muhurta = most powerful auspicious window.
      NOT present on Wednesdays (Budhavara = vara_id 4). Source: MC §5.

    Amrit Kalam:
      Computed from nakshatra_id via AMRIT_KALAM_TABLE.
      Returns None if the table has no entry for this nakshatra (S1 stubs).
      Source: MC §7.

    Varjyam:
      Inauspicious sub-period within the nakshatra. Included here as
      the "inverse auspicious" concept — callers may treat it separately.
      Returns None if VARJYAM_TABLE has no entry (S1 stubs).
      Source: MC §8.

    Args:
        sunrise_utc, sunset_utc: UTC datetimes
        vara_id: 1..7
        tithi_id: 1..30 (for Amrit Kalam; optional in S1)
        nakshatra_id: 1..27 (for Amrit Kalam + Varjyam)

    Returns:
        dict with keys 'brahma_muhurta', 'abhijit', 'amrit_kalam', 'varjyam'.
        Values are Timing or None.
    """
    result: dict[str, Optional[Timing]] = {}

    # Brahma Muhurta: 96–48 minutes before sunrise (DP convention)
    result["brahma_muhurta"] = Timing(
        label="brahma_muhurta",
        start_utc=sunrise_utc - timedelta(minutes=96),
        end_utc=sunrise_utc - timedelta(minutes=48),
    )

    # Abhijit Muhurta: 8th of 15 equal day-muhurtas (not on Wednesday)
    if vara_id == 4:  # Budhavara — no Abhijit on Wednesday (MC §5)
        result["abhijit"] = None
    else:
        day_seconds = (sunset_utc - sunrise_utc).total_seconds()
        muhurta_seconds = day_seconds / 15.0
        # 8th muhurta (1-indexed) = index 7 start
        abhijit_start = sunrise_utc + timedelta(seconds=7 * muhurta_seconds)
        abhijit_end = sunrise_utc + timedelta(seconds=8 * muhurta_seconds)
        result["abhijit"] = Timing(
            label="abhijit",
            start_utc=abhijit_start,
            end_utc=abhijit_end,
        )

    # Amrit Kalam (S1: AMRIT_KALAM_TABLE is stub — returns None for all nakshatras)
    amrit_entry = AMRIT_KALAM_TABLE.get(nakshatra_id, [None, None])
    if amrit_entry and amrit_entry[0] is not None:
        ghatika_seconds = 24 * 60
        start = sunrise_utc + timedelta(seconds=amrit_entry[0] * ghatika_seconds)
        end = start + timedelta(seconds=amrit_entry[1] * ghatika_seconds)
        result["amrit_kalam"] = Timing(label="amrit_kalam", start_utc=start, end_utc=end)
    else:
        result["amrit_kalam"] = None  # S1 stub; S2 populates AMRIT_KALAM_TABLE

    # Varjyam (S1: VARJYAM_TABLE is stub — returns None)
    varjyam_entry = VARJYAM_TABLE.get(nakshatra_id, [None, None])
    if varjyam_entry and varjyam_entry[0] is not None:
        ghatika_seconds = 24 * 60
        start = sunrise_utc + timedelta(seconds=varjyam_entry[0] * ghatika_seconds)
        end = start + timedelta(seconds=varjyam_entry[1] * ghatika_seconds)
        result["varjyam"] = Timing(label="varjyam", start_utc=start, end_utc=end)
    else:
        result["varjyam"] = None  # S1 stub; S2 populates VARJYAM_TABLE

    return result


def compute_choghadiya(sunrise_utc: datetime, sunset_utc: datetime,
                       next_sunrise_utc: datetime, vara_id: int) -> dict[str, list[Timing]]:
    """
    Compute the 8 day-segments (Choghadiya) + 8 night-segments.

    Day = sunrise → sunset (8 equal segments).
    Night = sunset → next sunrise (8 equal segments).

    Segment names from CHOGHADIYA_DAY_TABLE and CHOGHADIYA_NIGHT_TABLE,
    indexed by vara_id. Source: MC §5; DP.

    Args:
        sunrise_utc, sunset_utc: UTC datetimes for the current day.
        next_sunrise_utc: UTC datetime for the next day's sunrise (night end boundary).
        vara_id: 1..7

    Returns:
        {'day': [8 × Timing], 'night': [8 × Timing]}
    """
    # Day choghadiyas
    day_seconds = (sunset_utc - sunrise_utc).total_seconds()
    day_segment = day_seconds / 8.0
    day_names = CHOGHADIYA_DAY_TABLE[vara_id]
    day_timings = []
    for i, name in enumerate(day_names):
        start = sunrise_utc + timedelta(seconds=i * day_segment)
        end = sunrise_utc + timedelta(seconds=(i + 1) * day_segment)
        day_timings.append(Timing(label=f"choghadiya_{name.lower()}", start_utc=start, end_utc=end))

    # Night choghadiyas
    night_seconds = (next_sunrise_utc - sunset_utc).total_seconds()
    night_segment = night_seconds / 8.0
    night_names = CHOGHADIYA_NIGHT_TABLE[vara_id]
    night_timings = []
    for i, name in enumerate(night_names):
        start = sunset_utc + timedelta(seconds=i * night_segment)
        end = sunset_utc + timedelta(seconds=(i + 1) * night_segment)
        night_timings.append(Timing(label=f"choghadiya_{name.lower()}", start_utc=start, end_utc=end))

    return {"day": day_timings, "night": night_timings}


def compute_hora(sunrise_utc: datetime, next_sunrise_utc: datetime,
                 vara_id: int) -> list[Timing]:
    """
    Compute the 24 planetary hours (Hora) for the day+night cycle.

    Each Hora spans 1/24 of the full day-night cycle (sunrise to next sunrise).
    Starting planet = the vara lord (VARA_HORA_START table).
    Sequence = Chaldean order (HORA_CYCLE: Sat→Jup→Mar→Sun→Ven→Mer→Moon, repeating).
    Source: VS; Hora Sara (Prithuyashas).

    Args:
        sunrise_utc: current day's sunrise
        next_sunrise_utc: next day's sunrise (defines the 24-hora cycle end)
        vara_id: 1..7

    Returns:
        list of 24 Timing objects (labeled 'hora_<planet_name_lower>').
    """
    total_seconds = (next_sunrise_utc - sunrise_utc).total_seconds()
    hora_seconds = total_seconds / 24.0

    start_planet = VARA_HORA_START[vara_id]
    start_idx = HORA_CYCLE.index(start_planet)

    timings = []
    for i in range(24):
        planet = HORA_CYCLE[(start_idx + i) % len(HORA_CYCLE)]
        start = sunrise_utc + timedelta(seconds=i * hora_seconds)
        end = sunrise_utc + timedelta(seconds=(i + 1) * hora_seconds)
        timings.append(Timing(
            label=f"hora_{planet.lower()}",
            start_utc=start,
            end_utc=end,
        ))

    return timings
