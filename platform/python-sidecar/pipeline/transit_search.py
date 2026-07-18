"""
pipeline.transit_search — Transit-event search functions for ka_gochara (L3 K2 wave).

Imported by:
  - routers/transit_search.py  (find_aspect_events, find_conjunction_events, TransitEvent)
  - services/ka_gochara/service.py  (all public symbols)
  - services/ka_gochara/writer.py   (self-test)

Ayanamsha: Lahiri sidereal throughout (swe.SIDM_LAHIRI).
Node convention: TRUE_NODE for Rahu (swe_id=11); Ketu = Rahu + 180 (no direct SWE id needed).
NEVER calls ctx.db_conn.commit() / rollback() — caller owns the transaction.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

MEAN_MOTIONS: dict[str, float] = {
    "Sun": 0.9856,
    "Moon": 13.176,
    "Mars": 0.524,
    "Mercury": 1.383,
    "Jupiter": 0.083,
    "Venus": 1.602,
    "Saturn": 0.033,
    "Rahu": -0.053,
    "Ketu": -0.053,
}

# pyswisseph planet IDs (swe module constants)
PLANET_IDS: dict[str, int | str] = {
    "Sun": 0,       # swe.SUN
    "Moon": 1,      # swe.MOON
    "Mercury": 2,   # swe.MERCURY
    "Venus": 3,     # swe.VENUS
    "Mars": 4,      # swe.MARS
    "Jupiter": 5,   # swe.JUPITER
    "Saturn": 6,    # swe.SATURN
    "Rahu": 11,     # swe.TRUE_NODE
    "Ketu": "ketu", # computed as Rahu + 180
}

# Step sizes for scanning (slower planets use coarser step)
_SLOW_PLANETS = {"Saturn", "Jupiter", "Rahu", "Ketu"}
_STEP_DAY_SLOW = 1.0
_STEP_DAY_FAST = 0.5


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class TransitEvent:
    """One transit event found by the search functions."""
    event_type: str                   # 'aspect'|'conjunction'|'ingress'|'return'|'station'|'eclipse'|'multi_planet'|'transit_to_transit'
    event_jd: float                   # Julian day of exact event
    event_datetime_ist: str           # ISO datetime in IST
    transit_planet: str               # primary planet
    secondary_planet: Optional[str]   # secondary planet (conjunction / transit_to_transit)
    exact_longitude_deg: float        # sidereal ecliptic longitude at event
    orb_at_event_deg: float           # orb in degrees at event time
    sign: str                         # sign name
    nakshatra: str                    # nakshatra name
    applying_separating: str          # 'applying' | 'separating' | 'stationary'
    orb_strength: float               # [0, 1] from orb_strength_score()
    speed_at_event_dps: float         # planet speed at event time (degrees/day)
    extra: dict = field(default_factory=dict)


# ── Core helpers ──────────────────────────────────────────────────────────────

def _shortest_arc_diff(lon_a: float, lon_b: float) -> float:
    """
    Signed shortest-arc difference lon_a - lon_b, in (-180, +180].
    Positive = lon_a ahead of lon_b; negative = behind.
    """
    diff = (lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return diff


def _sign_nak(lon: float) -> tuple[str, str]:
    """Return (sign_name, nakshatra_name) for a sidereal longitude."""
    sign = SIGNS[int(lon // 30.0) % 12]
    nak = NAKSHATRAS[int(lon / (360.0 / 27.0)) % 27]
    return sign, nak


def _jd_to_ist_iso(swe, jd: float) -> str:
    """Convert Julian day to ISO-format datetime string in IST (UTC+5:30)."""
    y, m, d, hour_dec = swe.revjul(jd)
    h = int(hour_dec)
    mn = int((hour_dec - h) * 60)
    s = int(((hour_dec - h) * 60 - mn) * 60)
    # Clamp seconds for floating-point edge cases
    s = max(0, min(59, s))
    try:
        dt_utc = datetime(int(y), int(m), int(d), h, mn, s)
    except ValueError:
        # Rare: overflow on hour/min/sec boundary -- fall back to day only
        dt_utc = datetime(int(y), int(m), int(d), 0, 0, 0)
    dt_ist = dt_utc + timedelta(hours=5, minutes=30)
    return dt_ist.isoformat()


def orb_strength_score(
    orb_at_event_deg: float,
    max_orb_deg: float,
    applying_separating: str,
) -> float:
    """
    Score in [0, 1] where 1 = exact and applying, 0 = at max orb and separating.
    Applying events receive a 1.2x multiplier (capped at 1.0).
    """
    if max_orb_deg <= 0.0:
        return 1.0
    base = max(0.0, 1.0 - (orb_at_event_deg / max_orb_deg))
    multiplier = 1.2 if applying_separating == "applying" else 1.0
    return min(1.0, base * multiplier)


# ── SWE position lookup ───────────────────────────────────────────────────────

# PERF-TRIGGER-CACHE (Doctrine-Waves D-3): `_get_planet_pos` is the sole
# swe.calc_ut call site in this module, and is called from every day-step of
# every scan loop below. Two access patterns dominate at real build scale:
#   1. Within a single find_aspect_events/find_transit_to_transit_events call,
#      the `aspect_degrees` loop re-walks the IDENTICAL start_jd/step jd
#      sequence once per aspect degree -- the planet's position at a given jd
#      does not depend on which aspect_deg is being tested, so this was pure
#      redundant computation (a 5-aspect call = up to 5x the necessary
#      ephemeris work).
#   2. Across `services/kala_trigger/trigger.py::compute_trigger_currents`,
#      ~38 separate find_aspects() calls share the SAME window
#      (w_jd_start, w_jd_end) -- planets recur (Saturn/Mars/Rahu/Ketu across
#      malefic_transit_over_mechanism + papa_kartari_sandwich; Jupiter/Saturn
#      in guru_shani_double_transit) -- so the exact-jd day-step sequence
#      repeats across calls, not just within one.
#
# `_calc_ut_cached` memoizes the raw swe.calc_ut(jd, planet_id, flags) call
# on the EXACT (unrounded) jd float actually passed by a caller -- this is
# what keeps the cache a pure performance optimization rather than a
# numerical approximation: a cache hit returns bit-identical output to what
# an uncached swe.calc_ut call would have produced for that same jd, because
# it IS that same call's result, memoized. No jd rounding/snapping is done --
# rounding the cache KEY without also rounding the value actually fed to
# swe.calc_ut would silently substitute a neighboring jd's position for the
# one actually requested, which is exactly the kind of semantic change this
# cache must not make. The within-call and cross-call redundancy above is
# already expressed as EXACT float repeats (same arithmetic: start_jd + n*step
# on the same start_jd/step pair produces bit-identical floats every time),
# so an exact-match cache captures the dominant redundancy without needing
# approximate keys.
#
# Bounded via `maxsize` (LRU eviction) rather than an unbounded dict so a
# very long multi-chart build run cannot leak memory: a single chart's full
# lifetime-horizon (~100 years) x ~365 steps/year x ~9 planets is a few
# hundred thousand entries at most, well under this cap.
_EPHEMERIS_CACHE_MAXSIZE = 400_000


@lru_cache(maxsize=_EPHEMERIS_CACHE_MAXSIZE)
def _calc_ut_cached(swe, jd: float, planet_id: int, flags: int) -> tuple[float, float]:
    """
    Memoized swe.calc_ut(jd, planet_id, flags) -> (sidereal_lon_deg, speed_deg_per_day).
    Keyed on the exact (swe module identity, jd, planet_id, flags) tuple --
    no rounding. See the module note above for the correctness rationale.
    """
    result = swe.calc_ut(jd, planet_id, flags)
    # result[0] is (lon, lat, dist, speed_lon, speed_lat, speed_dist)
    lon = result[0][0] % 360.0
    speed = result[0][3]
    return lon, speed


def clear_ephemeris_cache() -> None:
    """Clear the process-local `_get_planet_pos` memoization cache. Exposed
    for tests/benchmarks; production callers do not need to call this -- the
    cache is keyed on absolute (swe, jd, planet_id, flags), which is valid to
    reuse across charts/builds within the same process (a given jd's
    ephemeris position does not depend on which chart is being built)."""
    _calc_ut_cached.cache_clear()


def ephemeris_cache_info():
    """`functools.lru_cache` CacheInfo (hits, misses, maxsize, currsize) for
    `_get_planet_pos`'s underlying memoization -- exposed for benchmarking."""
    return _calc_ut_cached.cache_info()


def _get_planet_pos(swe, planet: str, jd: float) -> tuple[float, float]:
    """
    Return (sidereal_longitude_deg, speed_deg_per_day) for a planet at JD jd.
    Uses Lahiri sidereal (swe.SIDM_LAHIRI).
    TRUE_NODE for Rahu; Ketu = Rahu + 180.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    if planet == "Ketu":
        rahu_lon, rahu_speed = _get_planet_pos(swe, "Rahu", jd)
        ketu_lon = (rahu_lon + 180.0) % 360.0
        return ketu_lon, rahu_speed  # same speed magnitude for Ketu

    planet_id = PLANET_IDS.get(planet)
    if planet_id is None:
        raise ValueError(f"Unknown planet: {planet!r}")
    if not isinstance(planet_id, int):
        raise ValueError(f"Unexpected planet_id type for {planet!r}: {planet_id!r}")

    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    return _calc_ut_cached(swe, jd, planet_id, flags)


def _step_size(planet: str) -> float:
    return _STEP_DAY_SLOW if planet in _SLOW_PLANETS else _STEP_DAY_FAST


def _determine_applying_separating(swe, planet: str, jd: float, target: float) -> str:
    """
    Determine whether the planet is applying to or separating from target at jd.
    Uses arc_diff before and after event to measure convergence direction.
    """
    lon, speed = _get_planet_pos(swe, planet, jd)
    if abs(speed) < 0.001:
        return "stationary"
    delta = 0.01  # days
    lon_before, _ = _get_planet_pos(swe, planet, jd - delta)
    lon_after, _ = _get_planet_pos(swe, planet, jd + delta)
    arc_before = abs(_shortest_arc_diff(lon_before, target))
    arc_after = abs(_shortest_arc_diff(lon_after, target))
    if arc_before > arc_after:
        return "applying"
    elif arc_before < arc_after:
        return "separating"
    return "stationary"


# ── Aspect-event search ───────────────────────────────────────────────────────

def find_aspect_events(
    swe,
    transit_planet: str,
    target_longitude_deg: float,
    aspect_degrees: list,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find all times within [start_jd, end_jd] when transit_planet is within orb_deg
    of (target_longitude_deg + aspect_deg) for each aspect_deg in aspect_degrees.

    Returns a list of TransitEvent sorted by event_jd.
    """
    events = []
    step = _step_size(transit_planet)

    for aspect_deg in aspect_degrees:
        target = (target_longitude_deg + aspect_deg) % 360.0

        jd = start_jd
        lon_prev, _ = _get_planet_pos(swe, transit_planet, jd)
        arc_prev = _shortest_arc_diff(lon_prev, target)

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            lon_next, _ = _get_planet_pos(swe, transit_planet, jd_next)
            arc_next = _shortest_arc_diff(lon_next, target)

            # Crossing detected: sign change in arc diff
            if arc_prev * arc_next <= 0.0 and not (arc_prev == 0.0 and arc_next == 0.0):
                # Bisect to find exact JD
                lo, hi = jd, jd_next
                for _ in range(20):
                    mid = (lo + hi) / 2.0
                    lon_mid, _ = _get_planet_pos(swe, transit_planet, mid)
                    arc_mid = _shortest_arc_diff(lon_mid, target)
                    if arc_prev * arc_mid <= 0.0:
                        hi = mid
                    else:
                        lo = mid
                exact_jd = (lo + hi) / 2.0
                lon_exact, speed_exact = _get_planet_pos(swe, transit_planet, exact_jd)
                arc_exact = abs(_shortest_arc_diff(lon_exact, target))

                appsep = _determine_applying_separating(swe, transit_planet, exact_jd, target)
                sign, nak = _sign_nak(lon_exact)
                strength = orb_strength_score(arc_exact, orb_deg, appsep)

                events.append(TransitEvent(
                    event_type="aspect",
                    event_jd=exact_jd,
                    event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
                    transit_planet=transit_planet,
                    secondary_planet=None,
                    exact_longitude_deg=round(lon_exact, 4),
                    orb_at_event_deg=round(arc_exact, 4),
                    sign=sign,
                    nakshatra=nak,
                    applying_separating=appsep,
                    orb_strength=round(strength, 4),
                    speed_at_event_dps=round(speed_exact, 6),
                    extra={"aspect_deg": aspect_deg},
                ))

            arc_prev = arc_next
            jd = jd_next

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Conjunction-event search ──────────────────────────────────────────────────

def find_conjunction_events(
    swe,
    planet_a: str,
    planet_b: str,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find all times within [start_jd, end_jd] when planet_a is within orb_deg of planet_b
    (passes through minimum separation).

    Returns a list of TransitEvent sorted by event_jd.
    """
    events = []
    step = max(_step_size(planet_a), _step_size(planet_b))

    jd = start_jd
    lon_a_prev, _ = _get_planet_pos(swe, planet_a, jd)
    lon_b_prev, _ = _get_planet_pos(swe, planet_b, jd)
    arc_prev = abs(_shortest_arc_diff(lon_a_prev, lon_b_prev))

    in_window = arc_prev <= orb_deg
    window_min_jd = jd if in_window else None
    window_min_arc = arc_prev if in_window else float("inf")

    while jd < end_jd:
        jd_next = min(jd + step, end_jd)
        lon_a_next, _ = _get_planet_pos(swe, planet_a, jd_next)
        lon_b_next, _ = _get_planet_pos(swe, planet_b, jd_next)
        arc_next = abs(_shortest_arc_diff(lon_a_next, lon_b_next))

        newly_in = arc_next <= orb_deg
        was_in = in_window

        if newly_in:
            if arc_next < window_min_arc:
                window_min_arc = arc_next
                window_min_jd = jd_next
        elif was_in and window_min_jd is not None:
            # Just left the orb window -- bisect around minimum
            exact_jd = window_min_jd
            # Refine: bisect for minimum arc around window_min_jd
            lo_b = max(start_jd, exact_jd - step)
            hi_b = min(end_jd, exact_jd + step)
            for _ in range(20):
                m1 = lo_b + (hi_b - lo_b) / 3.0
                m2 = hi_b - (hi_b - lo_b) / 3.0
                arc1 = abs(_shortest_arc_diff(
                    _get_planet_pos(swe, planet_a, m1)[0],
                    _get_planet_pos(swe, planet_b, m1)[0],
                ))
                arc2 = abs(_shortest_arc_diff(
                    _get_planet_pos(swe, planet_a, m2)[0],
                    _get_planet_pos(swe, planet_b, m2)[0],
                ))
                if arc1 < arc2:
                    hi_b = m2
                else:
                    lo_b = m1

            exact_jd = (lo_b + hi_b) / 2.0
            lon_a_exact, speed_a = _get_planet_pos(swe, planet_a, exact_jd)
            lon_b_exact, _ = _get_planet_pos(swe, planet_b, exact_jd)
            arc_exact = abs(_shortest_arc_diff(lon_a_exact, lon_b_exact))

            appsep = _determine_applying_separating(swe, planet_a, exact_jd, lon_b_exact)
            sign, nak = _sign_nak(lon_a_exact)
            strength = orb_strength_score(arc_exact, orb_deg, appsep)

            events.append(TransitEvent(
                event_type="conjunction",
                event_jd=exact_jd,
                event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
                transit_planet=planet_a,
                secondary_planet=planet_b,
                exact_longitude_deg=round(lon_a_exact, 4),
                orb_at_event_deg=round(arc_exact, 4),
                sign=sign,
                nakshatra=nak,
                applying_separating=appsep,
                orb_strength=round(strength, 4),
                speed_at_event_dps=round(speed_a, 6),
                extra={"planet_b_lon": round(lon_b_exact, 4)},
            ))

            # Reset window tracking
            window_min_arc = float("inf")
            window_min_jd = None

        if not was_in and newly_in:
            # Entering the orb window
            window_min_arc = arc_next
            window_min_jd = jd_next

        in_window = newly_in
        arc_prev = arc_next
        jd = jd_next

    # Handle case where we end still inside the window
    if in_window and window_min_jd is not None:
        exact_jd = window_min_jd
        lon_a_exact, speed_a = _get_planet_pos(swe, planet_a, exact_jd)
        lon_b_exact, _ = _get_planet_pos(swe, planet_b, exact_jd)
        arc_exact = abs(_shortest_arc_diff(lon_a_exact, lon_b_exact))
        appsep = _determine_applying_separating(swe, planet_a, exact_jd, lon_b_exact)
        sign, nak = _sign_nak(lon_a_exact)
        strength = orb_strength_score(arc_exact, orb_deg, appsep)
        events.append(TransitEvent(
            event_type="conjunction",
            event_jd=exact_jd,
            event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
            transit_planet=planet_a,
            secondary_planet=planet_b,
            exact_longitude_deg=round(lon_a_exact, 4),
            orb_at_event_deg=round(arc_exact, 4),
            sign=sign,
            nakshatra=nak,
            applying_separating=appsep,
            orb_strength=round(strength, 4),
            speed_at_event_dps=round(speed_a, 6),
            extra={"planet_b_lon": round(lon_b_exact, 4)},
        ))

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Ingress events ────────────────────────────────────────────────────────────

def find_ingress_events(
    swe,
    planet: str,
    target_sign: str,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find all times when planet enters target_sign (crosses the sign cusp at entry longitude).
    """
    if target_sign not in SIGNS:
        raise ValueError(f"Unknown sign: {target_sign!r}")

    sign_idx = SIGNS.index(target_sign)
    events = []
    step = _step_size(planet)

    jd = start_jd
    lon_prev, _ = _get_planet_pos(swe, planet, jd)
    in_sign_prev = (int(lon_prev // 30.0) % 12) == sign_idx

    while jd < end_jd:
        jd_next = min(jd + step, end_jd)
        lon_next, _ = _get_planet_pos(swe, planet, jd_next)
        in_sign_next = (int(lon_next // 30.0) % 12) == sign_idx

        # Entering the sign (not_in -> in)
        if not in_sign_prev and in_sign_next:
            # Bisect for ingress crossing
            lo, hi = jd, jd_next
            for _ in range(20):
                mid = (lo + hi) / 2.0
                lon_mid, _ = _get_planet_pos(swe, planet, mid)
                in_mid = (int(lon_mid // 30.0) % 12) == sign_idx
                if in_mid:
                    hi = mid
                else:
                    lo = mid
            exact_jd = (lo + hi) / 2.0
            lon_exact, speed_exact = _get_planet_pos(swe, planet, exact_jd)
            sign, nak = _sign_nak(lon_exact)

            events.append(TransitEvent(
                event_type="ingress",
                event_jd=exact_jd,
                event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
                transit_planet=planet,
                secondary_planet=None,
                exact_longitude_deg=round(lon_exact, 4),
                orb_at_event_deg=0.0,
                sign=sign,
                nakshatra=nak,
                applying_separating="applying",
                orb_strength=1.0,
                speed_at_event_dps=round(speed_exact, 6),
                extra={"target_sign": target_sign},
            ))

        in_sign_prev = in_sign_next
        jd = jd_next

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Return events ─────────────────────────────────────────────────────────────

def find_return_events(
    swe,
    planet: str,
    natal_longitude_deg: float,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find all times when planet returns to within orb_deg of its natal longitude.
    Equivalent to find_aspect_events with aspect_degrees=[0] but event_type='return'.
    """
    base_events = find_aspect_events(
        swe, planet, natal_longitude_deg, [0], orb_deg, start_jd, end_jd
    )
    # Retype as 'return'
    return_events = []
    for ev in base_events:
        return_events.append(TransitEvent(
            event_type="return",
            event_jd=ev.event_jd,
            event_datetime_ist=ev.event_datetime_ist,
            transit_planet=ev.transit_planet,
            secondary_planet=None,
            exact_longitude_deg=ev.exact_longitude_deg,
            orb_at_event_deg=ev.orb_at_event_deg,
            sign=ev.sign,
            nakshatra=ev.nakshatra,
            applying_separating=ev.applying_separating,
            orb_strength=ev.orb_strength,
            speed_at_event_dps=ev.speed_at_event_dps,
            extra={**ev.extra, "natal_longitude_deg": natal_longitude_deg},
        ))
    return return_events


# ── Station events (retrograde/direct) ───────────────────────────────────────

def find_station_events(
    swe,
    planet: str,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find retrograde (R) and direct (D) station events for a planet.
    Detected by speed sign change.
    """
    events = []

    # Nodes / luminaries don't station in the traditional sense
    if planet in ("Rahu", "Ketu", "Sun", "Moon"):
        return events

    step = _step_size(planet)
    jd = start_jd
    _, speed_prev = _get_planet_pos(swe, planet, jd)

    while jd < end_jd:
        jd_next = min(jd + step, end_jd)
        lon_next, speed_next = _get_planet_pos(swe, planet, jd_next)

        # Speed sign change = station
        if speed_prev * speed_next < 0.0:
            # Bisect for zero-crossing
            lo, hi = jd, jd_next
            for _ in range(20):
                mid = (lo + hi) / 2.0
                _, speed_mid = _get_planet_pos(swe, planet, mid)
                if speed_prev * speed_mid <= 0.0:
                    hi = mid
                else:
                    lo = mid
            exact_jd = (lo + hi) / 2.0
            lon_exact, speed_exact = _get_planet_pos(swe, planet, exact_jd)
            sign, nak = _sign_nak(lon_exact)

            # Determine station type: positive speed -> going retrograde; negative -> going direct
            station_type = "retrograde" if speed_prev > 0.0 else "direct"

            events.append(TransitEvent(
                event_type="station",
                event_jd=exact_jd,
                event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
                transit_planet=planet,
                secondary_planet=None,
                exact_longitude_deg=round(lon_exact, 4),
                orb_at_event_deg=0.0,
                sign=sign,
                nakshatra=nak,
                applying_separating="stationary",
                orb_strength=1.0,
                speed_at_event_dps=round(speed_exact, 6),
                extra={"station_type": station_type},
            ))

        speed_prev = speed_next
        jd = jd_next

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Eclipse proximity events ──────────────────────────────────────────────────

def find_eclipse_proximity_events(
    swe,
    node_planet: str,
    luminary: str,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find windows where node_planet (Rahu/Ketu) is within orb_deg of luminary (Sun/Moon).
    Flags potential eclipse windows.
    """
    conj_events = find_conjunction_events(
        swe, node_planet, luminary, orb_deg, start_jd, end_jd
    )
    eclipse_events = []
    for ev in conj_events:
        eclipse_events.append(TransitEvent(
            event_type="eclipse",
            event_jd=ev.event_jd,
            event_datetime_ist=ev.event_datetime_ist,
            transit_planet=ev.transit_planet,
            secondary_planet=ev.secondary_planet,
            exact_longitude_deg=ev.exact_longitude_deg,
            orb_at_event_deg=ev.orb_at_event_deg,
            sign=ev.sign,
            nakshatra=ev.nakshatra,
            applying_separating=ev.applying_separating,
            orb_strength=ev.orb_strength,
            speed_at_event_dps=ev.speed_at_event_dps,
            extra={**ev.extra, "eclipse_type": f"{node_planet}_{luminary}"},
        ))
    return eclipse_events


# ── Multi-planet confluence ───────────────────────────────────────────────────

def find_multi_planet_confluence_events(
    swe,
    planets: list,
    target_longitude_deg: float,
    aspect_degrees: list,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find windows where ALL listed planets simultaneously aspect target_longitude_deg
    within orb_deg for at least one aspect_degree each.

    Returns one event per window at the peak confluence (minimum total orb).
    """
    events = []
    if not planets:
        return events

    step = max(_step_size(p) for p in planets)

    def _all_within_orb(jd_check):
        planet_info = {}
        for planet in planets:
            lon, speed = _get_planet_pos(swe, planet, jd_check)
            min_orb = float("inf")
            best_aspect = None
            for asp in aspect_degrees:
                target = (target_longitude_deg + asp) % 360.0
                orb = abs(_shortest_arc_diff(lon, target))
                if orb < min_orb:
                    min_orb = orb
                    best_aspect = asp
            if min_orb > orb_deg:
                return None
            planet_info[planet] = {"lon": lon, "speed": speed, "orb": min_orb, "aspect": best_aspect}
        return planet_info

    in_confluence = False
    conf_min_total_orb = float("inf")
    conf_min_jd = None

    jd = start_jd
    while jd <= end_jd:
        info = _all_within_orb(jd)
        currently_in = info is not None

        if currently_in:
            total_orb = sum(v["orb"] for v in info.values())
            if not in_confluence:
                in_confluence = True
                conf_min_total_orb = total_orb
                conf_min_jd = jd
            elif total_orb < conf_min_total_orb:
                conf_min_total_orb = total_orb
                conf_min_jd = jd
        else:
            if in_confluence and conf_min_jd is not None:
                peak_info = _all_within_orb(conf_min_jd)
                if peak_info:
                    primary = planets[0]
                    lon_p = peak_info[primary]["lon"]
                    speed_p = peak_info[primary]["speed"]
                    sign, nak = _sign_nak(lon_p)
                    avg_orb = conf_min_total_orb / len(planets)
                    appsep = _determine_applying_separating(swe, primary, conf_min_jd, target_longitude_deg)
                    strength = orb_strength_score(avg_orb, orb_deg, appsep)
                    events.append(TransitEvent(
                        event_type="multi_planet",
                        event_jd=conf_min_jd,
                        event_datetime_ist=_jd_to_ist_iso(swe, conf_min_jd),
                        transit_planet=primary,
                        secondary_planet=None,
                        exact_longitude_deg=round(lon_p, 4),
                        orb_at_event_deg=round(avg_orb, 4),
                        sign=sign,
                        nakshatra=nak,
                        applying_separating=appsep,
                        orb_strength=round(strength, 4),
                        speed_at_event_dps=round(speed_p, 6),
                        extra={
                            "planets": planets,
                            "per_planet_orb": {k: round(v["orb"], 4) for k, v in peak_info.items()},
                            "target_longitude_deg": target_longitude_deg,
                        },
                    ))
            in_confluence = False
            conf_min_total_orb = float("inf")
            conf_min_jd = None

        jd = jd + step
        if jd > end_jd and jd - step < end_jd:
            jd = end_jd  # ensure we check end boundary

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Transit-to-transit events ─────────────────────────────────────────────────

def find_transit_to_transit_events(
    swe,
    planet_a: str,
    planet_b: str,
    aspect_degrees: list,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list:
    """
    Find times when transiting planet_a aspects transiting planet_b
    (i.e., planet_a is within orb_deg of planet_b + aspect_deg).
    """
    events = []
    step = max(_step_size(planet_a), _step_size(planet_b))

    for aspect_deg in aspect_degrees:
        jd = start_jd
        lon_a_prev, _ = _get_planet_pos(swe, planet_a, jd)
        lon_b_prev, _ = _get_planet_pos(swe, planet_b, jd)
        target_prev = (lon_b_prev + aspect_deg) % 360.0
        arc_prev = _shortest_arc_diff(lon_a_prev, target_prev)

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            lon_a_next, _ = _get_planet_pos(swe, planet_a, jd_next)
            lon_b_next, _ = _get_planet_pos(swe, planet_b, jd_next)
            target_next = (lon_b_next + aspect_deg) % 360.0
            arc_next = _shortest_arc_diff(lon_a_next, target_next)

            # Crossing detected
            if arc_prev * arc_next <= 0.0 and not (arc_prev == 0.0 and arc_next == 0.0):
                # Bisect
                lo, hi = jd, jd_next
                for _ in range(20):
                    mid = (lo + hi) / 2.0
                    lon_a_mid, _ = _get_planet_pos(swe, planet_a, mid)
                    lon_b_mid, _ = _get_planet_pos(swe, planet_b, mid)
                    target_mid = (lon_b_mid + aspect_deg) % 360.0
                    arc_mid = _shortest_arc_diff(lon_a_mid, target_mid)
                    if arc_prev * arc_mid <= 0.0:
                        hi = mid
                    else:
                        lo = mid

                exact_jd = (lo + hi) / 2.0
                lon_a_exact, speed_a = _get_planet_pos(swe, planet_a, exact_jd)
                lon_b_exact, _ = _get_planet_pos(swe, planet_b, exact_jd)
                target_exact = (lon_b_exact + aspect_deg) % 360.0
                arc_exact = abs(_shortest_arc_diff(lon_a_exact, target_exact))

                appsep = _determine_applying_separating(swe, planet_a, exact_jd, target_exact)
                sign, nak = _sign_nak(lon_a_exact)
                strength = orb_strength_score(arc_exact, orb_deg, appsep)

                events.append(TransitEvent(
                    event_type="transit_to_transit",
                    event_jd=exact_jd,
                    event_datetime_ist=_jd_to_ist_iso(swe, exact_jd),
                    transit_planet=planet_a,
                    secondary_planet=planet_b,
                    exact_longitude_deg=round(lon_a_exact, 4),
                    orb_at_event_deg=round(arc_exact, 4),
                    sign=sign,
                    nakshatra=nak,
                    applying_separating=appsep,
                    orb_strength=round(strength, 4),
                    speed_at_event_dps=round(speed_a, 6),
                    extra={
                        "aspect_deg": aspect_deg,
                        "planet_b_lon": round(lon_b_exact, 4),
                    },
                ))

            arc_prev = arc_next
            jd = jd_next

    events.sort(key=lambda e: e.event_jd)
    return events


# ── Long-horizon coarse-to-fine search ───────────────────────────────────────

def search_long_horizon(
    swe,
    transit_planet: str,
    target_longitude_deg: float,
    aspect_degrees: list,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
    region_tile_days: int = 365,
) -> list:
    """
    Tile the horizon into region_tile_days chunks and call find_aspect_events
    on each tile. Deduplicates events within 1.0 day and sorts by event_jd.

    Suitable for 50-year searches on slow planets.
    """
    all_events = []
    tile_start = start_jd

    while tile_start < end_jd:
        tile_end = min(tile_start + region_tile_days, end_jd)
        tile_events = find_aspect_events(
            swe, transit_planet, target_longitude_deg,
            aspect_degrees, orb_deg, tile_start, tile_end,
        )
        all_events.extend(tile_events)
        tile_start = tile_end

    # Dedup: keep first event within any 1-day window
    all_events.sort(key=lambda e: e.event_jd)
    deduped = []
    for ev in all_events:
        if not deduped or (ev.event_jd - deduped[-1].event_jd) > 1.0:
            deduped.append(ev)

    return deduped


__all__ = [
    "TransitEvent",
    "SIGNS",
    "NAKSHATRAS",
    "MEAN_MOTIONS",
    "PLANET_IDS",
    "orb_strength_score",
    "_shortest_arc_diff",
    "_sign_nak",
    "_jd_to_ist_iso",
    "_get_planet_pos",
    "clear_ephemeris_cache",
    "ephemeris_cache_info",
    "find_aspect_events",
    "find_conjunction_events",
    "find_ingress_events",
    "find_return_events",
    "find_station_events",
    "find_eclipse_proximity_events",
    "find_multi_planet_confluence_events",
    "find_transit_to_transit_events",
    "search_long_horizon",
]
