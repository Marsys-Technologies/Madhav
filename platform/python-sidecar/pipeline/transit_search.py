"""
transit_search — Swiss Ephemeris event-search primitives for §4.D.

Three search algorithms:
  - find_aspect_events(swe, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)
  - find_conjunction_events(swe, planet_a, planet_b, orb, start_jd, end_jd)
  - find_ingress_events(swe, planet, target_sign, start_jd, end_jd)

For Sun/Moon, longitude crossings use swe.solcross / swe.mooncross (fast, exact).
For Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu, longitude crossings are found via
adaptive sign-bracketing + bisection.

All returned events carry:
  - event_jd (UTC Julian Day, second-precision)
  - event_datetime_ist (ISO datetime string, IST = UTC+5:30, carry-forward from §4.C vara convention)
  - exact_longitude_deg (Lahiri sidereal)
  - orb_at_event_deg (degrees)

Window cap: caller supplies start_jd + end_jd. Internal logic does not extend.

Imports SIGNS + SIGN_TO_IDX from ephemeris_derivations and NAKSHATRAS from
panchanga_derivations — single-source-of-truth pattern established in §4.B/§4.C.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .ephemeris_derivations import SIGNS, SIGN_TO_IDX
from .panchanga_derivations import NAKSHATRAS

IST_OFFSET_HOURS = 5.5

# Swiss Ephemeris planet name → swe attribute lookup key.
# Rahu = MEAN_NODE per §4.B locked decision; Ketu handled separately below.
_PLANET_SWE_ATTR = {
    "sun":     "SUN",
    "moon":    "MOON",
    "mars":    "MARS",
    "mercury": "MERCURY",
    "jupiter": "JUPITER",
    "venus":   "VENUS",
    "saturn":  "SATURN",
    "rahu":    "MEAN_NODE",
}


@dataclass
class TransitEvent:
    event_type: str                    # 'ingress' | 'aspect' | 'conjunction' | 'station'
    event_jd: float                    # Julian Day UTC (second precision)
    event_datetime_ist: str            # ISO datetime in IST (UTC+5:30)
    transit_planet: str
    secondary_planet: Optional[str]    # for conjunctions / aspect-to-planet
    exact_longitude_deg: float
    orb_at_event_deg: float
    sign: str
    nakshatra: str
    extra: dict = field(default_factory=dict)   # event-type-specific metadata


# ── Public helpers ────────────────────────────────────────────────────────────

def jd_to_ist_iso(swe, jd_utc: float) -> str:
    """Convert UTC Julian Day to ISO datetime string in IST (UTC+5:30)."""
    y, m, d, hour_dec = swe.revjul(jd_utc)
    h = int(hour_dec)
    mn = int((hour_dec - h) * 60)
    s = int(((hour_dec - h) * 60 - mn) * 60)
    dt_utc = datetime(int(y), int(m), int(d), h, mn, s)
    dt_ist = dt_utc + timedelta(hours=IST_OFFSET_HOURS)
    return dt_ist.isoformat()


# ── Search algorithms ─────────────────────────────────────────────────────────

def find_aspect_events(
    swe,
    transit_planet: str,
    target_longitude_deg: float,
    aspect_degrees: list[int],
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find all events where transit_planet's sidereal longitude crosses
    (target_longitude_deg + aspect_degree) % 360 within orb_deg of that target,
    between start_jd and end_jd.

    For Sun:  swe.solcross for exact crossing.
    For Moon: swe.mooncross for exact crossing.
    For other planets: adaptive day-step bracketing + bisection.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    planet_code = _swe_planet_code(swe, transit_planet)
    events: list[TransitEvent] = []

    for aspect_deg in aspect_degrees:
        target_lon = (target_longitude_deg + aspect_deg) % 360.0
        pl_lower = transit_planet.lower()

        if pl_lower == "sun":
            jd = start_jd
            while jd < end_jd:
                next_jd = swe.solcross(target_lon, jd, flags)
                if next_jd < 0 or next_jd > end_jd:
                    break
                events.append(_build_event(
                    swe, "aspect", next_jd, transit_planet,
                    None, target_lon, 0.0, {"aspect_deg": aspect_deg},
                ))
                jd = next_jd + 1.0

        elif pl_lower == "moon":
            jd = start_jd
            while jd < end_jd:
                next_jd = swe.mooncross(target_lon, jd, flags)
                if next_jd < 0 or next_jd > end_jd:
                    break
                events.append(_build_event(
                    swe, "aspect", next_jd, transit_planet,
                    None, target_lon, 0.0, {"aspect_deg": aspect_deg},
                ))
                jd = next_jd + 1.0

        else:
            events.extend(_find_crossings_by_bisection(
                swe, planet_code, target_lon, orb_deg, start_jd, end_jd,
                event_type="aspect", transit_planet=transit_planet,
                extra={"aspect_deg": aspect_deg},
            ))

    return sorted(events, key=lambda e: e.event_jd)


def find_conjunction_events(
    swe,
    planet_a: str,
    planet_b: str,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find times when planet_a and planet_b are within orb_deg of each other.
    Day-step iteration + bisection on the signed longitude difference.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    code_a = _swe_planet_code(swe, planet_a)
    code_b = _swe_planet_code(swe, planet_b)

    events: list[TransitEvent] = []
    step = 1.0
    jd = start_jd
    prev_diff = _shortest_arc_diff(
        _planet_lon(swe, code_a, jd, flags),
        _planet_lon(swe, code_b, jd, flags),
    )

    while jd < end_jd:
        jd_next = jd + step
        lon_a = _planet_lon(swe, code_a, jd_next, flags)
        lon_b = _planet_lon(swe, code_b, jd_next, flags)
        diff = _shortest_arc_diff(lon_a, lon_b)

        if abs(diff) <= orb_deg and abs(prev_diff) > orb_deg:
            # Entered orb — bisect to the moment |diff| == orb.
            exact_jd = _bisect_diff(swe, code_a, code_b, jd, jd_next, orb_deg, flags)
            events.append(_build_event(
                swe, "conjunction", exact_jd, planet_a,
                planet_b, lon_a, abs(diff),
                {"planet_b": planet_b, "orb_deg": orb_deg},
            ))

        prev_diff = diff
        jd = jd_next

    return events


def find_ingress_events(
    swe,
    planet: str,
    target_sign: str,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find when planet enters target_sign (longitude crosses sign boundary).
    Used as a sidecar fallback when ephemeris_daily window is exceeded, or
    for sub-day precision. For 1900-2100 queries the TS tool routes to
    ephemeris_daily.sign_ingress_today instead; this is the backstop.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sign_idx = SIGN_TO_IDX[target_sign]
    target_lon = sign_idx * 30.0
    code = _swe_planet_code(swe, planet)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED

    return _find_crossings_by_bisection(
        swe, code, target_lon, orb_deg=0.0, start_jd=start_jd, end_jd=end_jd,
        event_type="ingress", transit_planet=planet,
        extra={"target_sign": target_sign},
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _swe_planet_code(swe, name: str) -> int:
    """Map planet name to swisseph integer code. Ketu = MEAN_NODE (caller adds 180°)."""
    name_lower = name.lower()
    if name_lower == "ketu":
        return getattr(swe, "MEAN_NODE")  # longitude + 180° applied at query time
    attr = _PLANET_SWE_ATTR.get(name_lower)
    if attr is None:
        raise ValueError(f"Unknown planet: {name!r}")
    return getattr(swe, attr)


def _planet_lon(swe, code: int, jd: float, flags: int) -> float:
    """Return Lahiri sidereal longitude [0, 360)."""
    pos, _ = swe.calc_ut(jd, code, flags)
    return pos[0] % 360.0


def _shortest_arc_diff(lon_a: float, lon_b: float) -> float:
    """Signed shortest arc from lon_b to lon_a, in (−180, 180]."""
    diff = (lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return diff


def _bisect_diff(
    swe, code_a: int, code_b: int,
    jd_lo: float, jd_hi: float,
    orb_deg: float, flags: int,
    max_iter: int = 30,
) -> float:
    """Bisect to find the JD where |longitude_diff| crosses orb_deg."""
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2.0
        lon_a = _planet_lon(swe, code_a, jd_mid, flags)
        lon_b = _planet_lon(swe, code_b, jd_mid, flags)
        diff = abs(_shortest_arc_diff(lon_a, lon_b))
        if abs(diff - orb_deg) < 0.001:
            return jd_mid
        if diff > orb_deg:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def _find_crossings_by_bisection(
    swe,
    planet_code: int,
    target_lon: float,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
    event_type: str,
    transit_planet: str,
    extra: Optional[dict] = None,
    step: float = 1.0,
) -> list[TransitEvent]:
    """Day-step bracketing + bisection for longitude crossings."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    events: list[TransitEvent] = []
    jd = start_jd
    prev_lon = _planet_lon(swe, planet_code, jd, flags)

    while jd < end_jd:
        jd_next = jd + step
        cur_lon = _planet_lon(swe, planet_code, jd_next, flags)
        prev_diff = (prev_lon - target_lon) % 360.0
        cur_diff = (cur_lon - target_lon) % 360.0
        # Hemisphere swap → crossing in [jd, jd_next]
        if (prev_diff < 180.0) != (cur_diff < 180.0):
            exact_jd = _bisect_longitude_to_target(
                swe, planet_code, target_lon, jd, jd_next, flags
            )
            events.append(_build_event(
                swe, event_type, exact_jd, transit_planet,
                None, target_lon, 0.0, extra or {},
            ))
        prev_lon = cur_lon
        jd = jd_next

    return events


def _bisect_longitude_to_target(
    swe, code: int, target: float,
    jd_lo: float, jd_hi: float,
    flags: int, max_iter: int = 30,
) -> float:
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2.0
        lon = _planet_lon(swe, code, jd_mid, flags)
        diff = (lon - target) % 360.0
        if diff > 180.0:
            diff -= 360.0
        if abs(diff) < 0.001:
            return jd_mid
        lo_lon = _planet_lon(swe, code, jd_lo, flags)
        lo_diff = (lo_lon - target) % 360.0
        if lo_diff > 180.0:
            lo_diff -= 360.0
        if (diff > 0) == (lo_diff > 0):
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def _build_event(
    swe,
    event_type: str,
    jd: float,
    transit_planet: str,
    secondary_planet: Optional[str],
    longitude: float,
    orb: float,
    extra: Optional[dict] = None,
) -> TransitEvent:
    sign_idx = int(longitude // 30) % 12
    sign = SIGNS[sign_idx]
    nak_idx = int(longitude / (360.0 / 27)) % 27
    return TransitEvent(
        event_type=event_type,
        event_jd=jd,
        event_datetime_ist=jd_to_ist_iso(swe, jd),
        transit_planet=transit_planet,
        secondary_planet=secondary_planet,
        exact_longitude_deg=round(longitude, 7),
        orb_at_event_deg=round(orb, 4),
        sign=sign,
        nakshatra=NAKSHATRAS[nak_idx],
        extra=extra or {},
    )
