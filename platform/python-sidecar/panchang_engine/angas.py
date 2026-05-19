"""
angas.py — The five Panchanga elements (angas) computation.
Pure math, swisseph-backed. All longitudes are sidereal (Lahiri).

References:
- Panchanga theory: Muhurta Chintamani §1, Brihat Samhita §2
- Boundary-crossing algorithm: bisection to ±1 second precision
"""
import swisseph as swe
from datetime import datetime, timedelta, timezone
from .types import Anga
from .exceptions import PanchangEngineError
from .shastra_tables import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_NAMES, VARA_NAMES,
)

# swisseph flags for sidereal positions
_SWE_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SWIEPH

# Anga spans in degrees
_TITHI_SPAN = 12.0          # Each tithi = 12° of moon-sun separation
_NAKSHATRA_SPAN = 360.0 / 27  # ≈ 13.333°
_YOGA_SPAN = 360.0 / 27       # ≈ 13.333°
_KARANA_SPAN = 6.0            # Each karana = 6° of moon-sun separation

# Precision target for boundary bisection
_BISECT_PRECISION_SEC = 1.0   # ±1 second


def _jd(dt: datetime) -> float:
    """Convert UTC datetime to Julian Day (UT)."""
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def _jd_to_utc(jd: float) -> datetime:
    """Convert Julian Day (UT) to UTC datetime."""
    y, mo, d, h = swe.revjul(jd)
    hour_int = int(h)
    minute_int = int((h - hour_int) * 60)
    second_int = int(((h - hour_int) * 60 - minute_int) * 60)
    return datetime(y, mo, d, hour_int, minute_int, second_int, tzinfo=timezone.utc)


def _get_sun_moon_lon(jd: float):
    """Return (sun_lon_sidereal, moon_lon_sidereal) at given JD."""
    sun = swe.calc_ut(jd, swe.SUN, _SWE_FLAGS)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, _SWE_FLAGS)[0][0]
    return sun % 360, moon % 360


def _bisect_boundary(fn_value, target: float, jd_lo: float, jd_hi: float) -> float:
    """
    Find the JD when fn_value(jd) first crosses `target` (upward).
    fn_value must be monotonically increasing in the interval (with possible
    wrap handling done by the caller).
    Uses bisection to ±1 second precision.
    """
    precision_jd = _BISECT_PRECISION_SEC / 86400.0
    for _ in range(60):  # max 60 iterations → well under 1 sec
        mid = (jd_lo + jd_hi) / 2
        val = fn_value(mid)
        if val < target:
            jd_lo = mid
        else:
            jd_hi = mid
        if (jd_hi - jd_lo) < precision_jd:
            break
    return (jd_lo + jd_hi) / 2


def compute_tithi(sun_lon: float, moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Tithi = floor((moon_lon - sun_lon) % 360 / 12) + 1.  Range 1..30.
    Each tithi spans 12° of moon-sun separation. Paksha:
      tithis 1..15 = Shukla (new→full moon). Tithi 15 = Purnima.
      tithis 16..30 = Krishna (full→new). Tithi 30 = Amavasya.

    end_utc is when moon-sun separation crosses the next 12° boundary (±1 sec).
    """
    sep = (moon_lon - sun_lon) % 360
    tithi_num = int(sep / _TITHI_SPAN) + 1

    # Find end_utc: next tithi boundary
    next_boundary = tithi_num * _TITHI_SPAN  # degrees at end of this tithi
    jd_start = _jd(asof_utc)
    jd_search_end = jd_start + 2.0  # search up to 2 days ahead

    def _sep(jd):
        s, m = _get_sun_moon_lon(jd)
        raw = (m - s) % 360
        return raw

    # Walk forward to find when sep first exceeds next_boundary
    # (handling wrap at 360°)
    step = 0.01  # ~15 min steps
    jd = jd_start + step
    prev = _sep(jd_start)
    found_lo = None
    while jd <= jd_search_end:
        curr = _sep(jd)
        # Handle wrap: if sep drops (360→0 crossing), check if we should stop
        if curr < prev and prev > 300 and curr < 60:
            # Wrapping - we've crossed tithi 30->1
            if next_boundary >= 360:
                # boundary wraps too
                found_lo = jd - step
                break
        if curr >= next_boundary and prev < next_boundary:
            found_lo = jd - step
            break
        prev = curr
        jd += step

    if found_lo is None:
        # Tithi spans > 2 days (unusual but theoretically possible for slow moon)
        # Use a rough estimate: ~1 day per tithi
        jd_end = jd_start + ((_TITHI_SPAN - (sep % _TITHI_SPAN)) / 360) * 27.3
        end_utc = _jd_to_utc(jd_end)
    else:
        # Refine with bisection
        jd_end = _bisect_boundary(
            lambda j: (_sep(j) if _sep(j) >= prev else _sep(j) + 360),
            next_boundary, found_lo, found_lo + step,
        )
        # Re-do bisection more carefully
        jd_lo2 = found_lo
        jd_hi2 = found_lo + step
        precision_jd = _BISECT_PRECISION_SEC / 86400.0
        for _ in range(60):
            mid = (jd_lo2 + jd_hi2) / 2
            val = _sep(mid)
            # Adjust for wrap
            if val < 50 and next_boundary > 300:
                val += 360
            if val < next_boundary:
                jd_lo2 = mid
            else:
                jd_hi2 = mid
            if (jd_hi2 - jd_lo2) < precision_jd:
                break
        jd_end = (jd_lo2 + jd_hi2) / 2
        end_utc = _jd_to_utc(jd_end)

    name = TITHI_NAMES[tithi_num]
    return Anga(id=tithi_num, name=name, end_utc=end_utc)


def compute_nakshatra(moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Nakshatra = floor(moon_lon / (360/27)) + 1.  Range 1..27.
    Each nakshatra spans 13°20' (13.333...°).
    Pada = floor((moon_lon mod 13.333) / 3.333) + 1.  Range 1..4.
    end_utc = moment moon reaches next nakshatra boundary (±1 sec).
    """
    nak_num = int(moon_lon / _NAKSHATRA_SPAN) + 1
    next_boundary = nak_num * _NAKSHATRA_SPAN
    if next_boundary >= 360:
        next_boundary = 360.0  # Revati → Ashwini

    jd_start = _jd(asof_utc)
    jd_search_end = jd_start + 2.0

    def _moon_lon(jd):
        return swe.calc_ut(jd, swe.MOON, _SWE_FLAGS)[0][0] % 360

    step = 0.01
    jd = jd_start + step
    prev = _moon_lon(jd_start)
    found_lo = None
    while jd <= jd_search_end:
        curr = _moon_lon(jd)
        if curr < prev and prev > 350 and curr < 30:
            # Moon wrapped around 360
            found_lo = jd - step
            break
        if curr >= next_boundary and prev < next_boundary:
            found_lo = jd - step
            break
        prev = curr
        jd += step

    if found_lo is None:
        # Estimate: Moon moves ~13.2°/day
        deg_remaining = next_boundary - moon_lon
        if deg_remaining < 0:
            deg_remaining += 360
        jd_end = jd_start + deg_remaining / 13.2
        end_utc = _jd_to_utc(jd_end)
    else:
        # Bisect
        jd_lo2, jd_hi2 = found_lo, found_lo + step
        precision_jd = _BISECT_PRECISION_SEC / 86400.0
        for _ in range(60):
            mid = (jd_lo2 + jd_hi2) / 2
            val = _moon_lon(mid)
            if val < 30 and next_boundary > 350:
                val += 360  # wrap-correct
            if val < next_boundary:
                jd_lo2 = mid
            else:
                jd_hi2 = mid
            if (jd_hi2 - jd_lo2) < precision_jd:
                break
        end_utc = _jd_to_utc((jd_lo2 + jd_hi2) / 2)

    name = NAKSHATRA_NAMES[nak_num - 1]  # 0-indexed list
    return Anga(id=nak_num, name=name, end_utc=end_utc)


def compute_yoga(sun_lon: float, moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Yoga = floor((sun_lon + moon_lon) % 360 / (360/27)) + 1.  Range 1..27.
    end_utc = moment (sun_lon + moon_lon) crosses next 13°20' boundary (±1 sec).
    """
    combo = (sun_lon + moon_lon) % 360
    yoga_num = int(combo / _YOGA_SPAN) + 1
    next_boundary = yoga_num * _YOGA_SPAN
    if next_boundary >= 360:
        next_boundary = 360.0

    jd_start = _jd(asof_utc)
    jd_search_end = jd_start + 2.0

    def _combo(jd):
        s, m = _get_sun_moon_lon(jd)
        return (s + m) % 360

    step = 0.01
    jd = jd_start + step
    prev = _combo(jd_start)
    found_lo = None
    while jd <= jd_search_end:
        curr = _combo(jd)
        if curr < prev and prev > 350 and curr < 30:
            found_lo = jd - step
            break
        if curr >= next_boundary and prev < next_boundary:
            found_lo = jd - step
            break
        prev = curr
        jd += step

    if found_lo is None:
        deg_remaining = next_boundary - combo
        if deg_remaining < 0:
            deg_remaining += 360
        jd_end = jd_start + deg_remaining / 14.5  # combo moves ~14.5°/day
        end_utc = _jd_to_utc(jd_end)
    else:
        jd_lo2, jd_hi2 = found_lo, found_lo + step
        precision_jd = _BISECT_PRECISION_SEC / 86400.0
        for _ in range(60):
            mid = (jd_lo2 + jd_hi2) / 2
            val = _combo(mid)
            if val < 30 and next_boundary > 350:
                val += 360
            if val < next_boundary:
                jd_lo2 = mid
            else:
                jd_hi2 = mid
            if (jd_hi2 - jd_lo2) < precision_jd:
                break
        end_utc = _jd_to_utc((jd_lo2 + jd_hi2) / 2)

    name = YOGA_NAMES[yoga_num - 1]
    return Anga(id=yoga_num, name=name, end_utc=end_utc)


def compute_karana_pair(sun_lon: float, moon_lon: float, asof_utc: datetime,
                        sunrise_utc: datetime) -> tuple:
    """
    Karana = half a tithi (6° of moon-sun separation). Each tithi has 2 karanas.

    There are 11 karanas:
    - 7 movable (Chara): Bava, Balava, Kaulava, Taitila, Garaja, Vanija, Vishti/Bhadra.
      These cycle through 56 of the 60 half-tithis (half-tithis 2..57).
    - 4 fixed (Sthira): Shakuni, Chatushpada, Naga, Kintughna.
      These occupy the last 4 half-tithis (57..60).

    Returns (karana_at_sunrise, karana_after_first_transition_within_day).

    References: Muhurta Chintamani §2; Brihat Samhita §2.
    """
    sep = (moon_lon - sun_lon) % 360

    def _karana_id(half_tithi_index: int) -> int:
        """
        Map half-tithi index (0-based, 0..59) to karana id (1..11).
        Half-tithis 0 = Kintughna (fixed, first)
        Half-tithis 1..56 = 7 movable cycling (Bava=1..Vishti=7)
        Half-tithis 57 = Shakuni (8), 58 = Chatushpada (9), 59 = Naga (10)
        [Kintughna=11 is index 0 of the month]
        """
        if half_tithi_index == 0:
            return 11  # Kintughna
        elif 1 <= half_tithi_index <= 56:
            return ((half_tithi_index - 1) % 7) + 1  # 1..7 cycling
        elif half_tithi_index == 57:
            return 8   # Shakuni
        elif half_tithi_index == 58:
            return 9   # Chatushpada
        elif half_tithi_index == 59:
            return 10  # Naga
        else:
            return ((half_tithi_index) % 7) + 1  # fallback

    # Current half-tithi index (0-based within the lunar month of 60 half-tithis)
    half_tithi_idx = int(sep / _KARANA_SPAN)

    kar1_id = _karana_id(half_tithi_idx)
    kar1_name = KARANA_NAMES[kar1_id - 1]

    # end_utc for first karana: next 6° boundary
    next_boundary_1 = (half_tithi_idx + 1) * _KARANA_SPAN
    if next_boundary_1 >= 360:
        next_boundary_1 -= 360

    jd_start = _jd(asof_utc)

    def _sep(jd):
        s, m = _get_sun_moon_lon(jd)
        return (m - s) % 360

    # Find end_utc for karana1
    step = 0.005  # ~7 min
    jd = jd_start + step
    prev = _sep(jd_start)
    found_lo1 = None
    jd_search_end = jd_start + 1.5
    while jd <= jd_search_end:
        curr = _sep(jd)
        if curr < prev and prev > 350 and curr < 30:
            found_lo1 = jd - step
            break
        if curr >= next_boundary_1 and prev < next_boundary_1:
            found_lo1 = jd - step
            break
        prev = curr
        jd += step

    if found_lo1 is None:
        deg_remaining = next_boundary_1 - sep
        if deg_remaining < 0:
            deg_remaining += 360
        jd_end1 = jd_start + deg_remaining / 13.2
    else:
        jd_lo2, jd_hi2 = found_lo1, found_lo1 + step
        precision_jd = _BISECT_PRECISION_SEC / 86400.0
        for _ in range(60):
            mid = (jd_lo2 + jd_hi2) / 2
            val = _sep(mid)
            if val < 30 and next_boundary_1 > 350:
                val += 360
            if val < next_boundary_1:
                jd_lo2 = mid
            else:
                jd_hi2 = mid
            if (jd_hi2 - jd_lo2) < precision_jd:
                break
        jd_end1 = (jd_lo2 + jd_hi2) / 2

    end_utc1 = _jd_to_utc(jd_end1)
    karana1 = Anga(id=kar1_id, name=kar1_name, end_utc=end_utc1)

    # Second karana: the one after the first transition within the day
    kar2_id = _karana_id(half_tithi_idx + 1)
    kar2_name = KARANA_NAMES[kar2_id - 1]

    next_boundary_2 = (half_tithi_idx + 2) * _KARANA_SPAN
    if next_boundary_2 >= 360:
        next_boundary_2 -= 360

    # Find end_utc for karana2 (search from end of karana1)
    jd = jd_end1 + step
    prev = _sep(jd_end1)
    found_lo2 = None
    jd_search_end2 = jd_end1 + 1.5
    while jd <= jd_search_end2:
        curr = _sep(jd)
        if curr < prev and prev > 350 and curr < 30:
            found_lo2 = jd - step
            break
        if curr >= next_boundary_2 and prev < next_boundary_2:
            found_lo2 = jd - step
            break
        prev = curr
        jd += step

    if found_lo2 is None:
        jd_end2 = jd_end1 + 0.5  # ~12 hours estimate
    else:
        jd_lo2, jd_hi2 = found_lo2, found_lo2 + step
        precision_jd = _BISECT_PRECISION_SEC / 86400.0
        for _ in range(60):
            mid = (jd_lo2 + jd_hi2) / 2
            val = _sep(mid)
            if val < 30 and next_boundary_2 > 350:
                val += 360
            if val < next_boundary_2:
                jd_lo2 = mid
            else:
                jd_hi2 = mid
            if (jd_hi2 - jd_lo2) < precision_jd:
                break
        jd_end2 = (jd_lo2 + jd_hi2) / 2

    end_utc2 = _jd_to_utc(jd_end2)
    karana2 = Anga(id=kar2_id, name=kar2_name, end_utc=end_utc2)

    return karana1, karana2


def compute_vara(d) -> Anga:
    """
    Vara = day of week (Hindu sunrise-to-sunrise convention).
    1=Ravivara(Sun), 2=Somavara(Mon), 3=Mangalavara(Tue),
    4=Budhavara(Wed), 5=Guruvara(Thu), 6=Shukravara(Fri), 7=Shanivara(Sat).

    end_utc = next sunrise at the location (passed in from timings context;
    for the vara object we use midnight UTC of the next day as a placeholder —
    callers must use timings.compute_sunrise_sunset for precise boundary).
    """
    from datetime import date as dt_date, datetime, timezone
    if isinstance(d, datetime):
        d = d.date()

    # Python weekday: Mon=0..Sun=6
    # Hindu vara: Sun=1, Mon=2, ..., Sat=7
    # Python Sunday=6 → Hindu 1; Monday=0 → Hindu 2; ...
    py_wd = d.weekday()  # 0=Mon..6=Sun
    hindu_vara = ((py_wd + 2) % 7) + 1  # Sun→1, Mon→2, ..., Sat→7

    vara_info = VARA_NAMES[hindu_vara]
    name = vara_info["name_sanskrit"]

    # end_utc placeholder: midnight UTC of next day
    # The precise boundary is next day's sunrise — callers wire that if needed.
    from datetime import timedelta
    next_day = d + timedelta(days=1)
    end_utc = datetime(next_day.year, next_day.month, next_day.day, 0, 0, 0,
                       tzinfo=timezone.utc)

    return Anga(id=hindu_vara, name=name, end_utc=end_utc)
