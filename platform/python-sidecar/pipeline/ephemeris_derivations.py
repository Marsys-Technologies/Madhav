"""
ephemeris_derivations — Vedic-interpretable derived state for ephemeris_daily.

All derivations are pure functions of base columns (date, planet, longitude_deg,
sign, sign_degree, nakshatra_pada, is_retrograde) and prior-day state (sign at
date - 1 day) plus a same-day sun row (for combust + graha-yuddha).

Constants are BPHS-canonical Parashari. See PHASE_4B brief §3 for sources.

Single-native mode: whole_sign_house is anchored to NATIVE_LAGNA_SIGN_INDEX = 0
(Aries). Multi-native extension is M7 scope.
"""
from __future__ import annotations
from typing import Optional

# Sign index: 0=Aries, 1=Taurus, ..., 11=Pisces.
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_TO_IDX = {s: i for i, s in enumerate(SIGNS)}

NATIVE_LAGNA_SIGN = "Aries"
NATIVE_LAGNA_IDX = SIGN_TO_IDX[NATIVE_LAGNA_SIGN]

# ── Combust thresholds (BPHS classical) ───────────────────────────────────────
# Direction-aware for Mercury and Venus (their retrograde orbs are tighter).
# Keyed by planet (lowercase), value is (direct_deg, retrograde_deg).
# For planets without direction variance, both values are equal.
COMBUST_THRESHOLDS_DEG: dict[str, tuple[float, float]] = {
    "moon":    (12.0, 12.0),   # only meaningful for amavasya proximity
    "mars":    (17.0, 17.0),
    "mercury": (14.0, 12.0),
    "jupiter": (11.0, 11.0),
    "venus":   (10.0,  8.0),
    "saturn":  (15.0, 15.0),
    # Sun/Rahu/Ketu: combustion N/A (Sun is the reference; nodes are shadows).
}

# ── D1 dignity tables ─────────────────────────────────────────────────────────
# Each entry: {planet: (exalted_sign, exalt_deg, debilitated_sign, debil_deg,
#                        own_signs:list, mooltrikona_sign, mooltrikona_range:(start,end))}
# Rahu/Ketu use sign-only (no exact deg) — set deg=None.
DIGNITY_TABLE: dict[str, tuple] = {
    "sun":     ("Aries",      10.0, "Libra",       10.0, ["Leo"],                       "Leo",         (0.0, 20.0)),
    "moon":    ("Taurus",      3.0, "Scorpio",      3.0, ["Cancer"],                    "Taurus",      (3.0, 30.0)),
    "mars":    ("Capricorn",  28.0, "Cancer",      28.0, ["Aries", "Scorpio"],          "Aries",       (0.0, 12.0)),
    "mercury": ("Virgo",      15.0, "Pisces",      15.0, ["Gemini", "Virgo"],           "Virgo",       (16.0, 20.0)),
    "jupiter": ("Cancer",      5.0, "Capricorn",    5.0, ["Sagittarius", "Pisces"],     "Sagittarius", (0.0, 10.0)),
    "venus":   ("Pisces",     27.0, "Virgo",       27.0, ["Taurus", "Libra"],           "Libra",       (0.0, 15.0)),
    "saturn":  ("Libra",      20.0, "Aries",       20.0, ["Capricorn", "Aquarius"],     "Aquarius",    (0.0, 20.0)),
    "rahu":    ("Taurus",     None, "Scorpio",     None, [],                            None,          None),
    "ketu":    ("Scorpio",    None, "Taurus",      None, [],                            None,          None),
}

# ── D9 navamsha mapping ──────────────────────────────────────────────────────
# For each sign, the D9 starts based on movable/fixed/dual:
#   - Movable (Aries, Cancer, Libra, Capricorn): D9 starts at the same sign.
#   - Fixed (Taurus, Leo, Scorpio, Aquarius): D9 starts at the 9th from that sign.
#   - Dual (Gemini, Virgo, Sagittarius, Pisces): D9 starts at the 5th from that sign.
# Each navamsha spans 3°20'.
_MOVABLE = {"Aries", "Cancer", "Libra", "Capricorn"}
_FIXED   = {"Taurus", "Leo", "Scorpio", "Aquarius"}


def d9_sign(sign: str, sign_degree: float) -> str:
    """Return the D9 (navamsha) sign for a given D1 sign and degree-within-sign."""
    navamsha_idx = int(sign_degree // (30.0 / 9))  # 0..8
    sign_idx = SIGN_TO_IDX[sign]
    if sign in _MOVABLE:
        start_offset = 0
    elif sign in _FIXED:
        start_offset = 8  # 9th from = +8 (0-indexed)
    else:  # dual
        start_offset = 4  # 5th from = +4
    d9_idx = (sign_idx + start_offset + navamsha_idx) % 12
    return SIGNS[d9_idx]


# ── Derivation functions ─────────────────────────────────────────────────────

def compute_dignity(planet: str, sign: str, sign_degree: float) -> str:
    """Return one of: 'exalted', 'debilitated', 'own_sign', 'mooltrikona', 'neutral'."""
    p = planet.lower()
    if p not in DIGNITY_TABLE:
        return "neutral"
    exalted, ex_deg, debil, deb_deg, own, mt_sign, mt_range = DIGNITY_TABLE[p]
    # Rahu/Ketu: sign-only check.
    if ex_deg is None:
        if sign == exalted: return "exalted"
        if sign == debil:   return "debilitated"
        return "neutral"
    # Standard planets: mooltrikona takes precedence over own_sign within range.
    if mt_sign and sign == mt_sign:
        lo, hi = mt_range
        if lo <= sign_degree < hi:
            return "mooltrikona"
        # Outside mooltrikona range but in mooltrikona sign → still own_sign if listed.
        if sign in own:
            return "own_sign"
    if sign == exalted:
        return "exalted"
    if sign == debil:
        return "debilitated"
    if sign in own:
        return "own_sign"
    return "neutral"


def compute_combust(
    planet: str,
    longitude_deg: float,
    sun_longitude_deg: float,
    is_retrograde: bool,
) -> tuple[bool, Optional[float]]:
    """Return (is_combust, combust_orb_deg). Returns (False, None) when N/A."""
    p = planet.lower()
    if p in ("sun", "rahu", "ketu"):
        return False, None
    if p not in COMBUST_THRESHOLDS_DEG:
        return False, None
    direct_orb, retro_orb = COMBUST_THRESHOLDS_DEG[p]
    threshold = retro_orb if is_retrograde else direct_orb
    # Shortest arc between planet and Sun longitudes.
    diff = abs(longitude_deg - sun_longitude_deg) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return (diff <= threshold), round(diff, 4)


def compute_vargottama(sign: str, sign_degree: float) -> bool:
    """True when D1 sign == D9 sign."""
    return d9_sign(sign, sign_degree) == sign


def compute_whole_sign_house(sign: str, native_lagna_idx: int = NATIVE_LAGNA_IDX) -> int:
    """Return whole-sign house 1..12 relative to native lagna."""
    sign_idx = SIGN_TO_IDX[sign]
    return ((sign_idx - native_lagna_idx + 12) % 12) + 1


def compute_sign_ingress(today_sign: str, prior_day_sign: Optional[str]) -> bool:
    """True when sign changed from prior day. False for the very first day in the table."""
    if prior_day_sign is None:
        return False
    return today_sign != prior_day_sign


def compute_graha_yuddha(
    planet: str,
    longitude_deg: float,
    same_day_positions: dict[str, float],
) -> Optional[str]:
    """
    Return the OTHER planet's name when this planet is within 1° of another.
    Only checked among {mars, mercury, jupiter, venus, saturn}.
    same_day_positions: {planet_name: longitude_deg} for the same date.

    Note on form (resolved in §4.D — no code change):
    This function uses the LONGITUDE-ONLY form of graha-yuddha. The classical
    BPHS strict form additionally requires the planets' ecliptic latitudes to
    differ by less than ~0.5°. Modern Vedic practice (including most production
    Jyotish software: Jagannatha Hora, Parashara's Light) commonly relaxes the
    latitude requirement because planet pairs at the same ecliptic longitude
    nearly always have similar enough latitudes for visual conjunction, and
    surface-level Vedic interpretation uses sign+degree position primarily.
    The longitude-only form is therefore the ACCEPTED VEDIC APPROXIMATION for
    this codebase. If a future workstream requires BPHS strict-form, extend
    this function to accept a `latitudes` dict and add the latitude check.
    """
    YUDDHA_PARTICIPANTS = {"mars", "mercury", "jupiter", "venus", "saturn"}
    p = planet.lower()
    if p not in YUDDHA_PARTICIPANTS:
        return None
    for other, other_lon in same_day_positions.items():
        o = other.lower()
        if o == p or o not in YUDDHA_PARTICIPANTS:
            continue
        diff = abs(longitude_deg - other_lon) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        if diff <= 1.0:
            return o
    return None


# ── Bhava-Chalit (Sripati cusps) — Phase 4 §6.6 follow-up ─────────────────────
#
# Sripati cusps are computed once at chart birth via Swiss Ephemeris's houses_ex
# function with house system code 'S'. The 12 cusps are FIXED for the native
# chart (they do not change with transit time — they're properties of the
# birth moment + observer). For a transit-planet longitude L, the Bhava-Chalit
# house is determined by which cusp-midpoint band L falls into.
#
# Convention: cusps[N] is the MIDPOINT of bhava N (Sripati tradition). Bhava N
# spans the half-arc band centered on cusps[N]:
#   boundary_start_N = midpoint(cusps[N-1], cusps[N])
#   boundary_end_N   = midpoint(cusps[N], cusps[N+1])
#
# This differs from the Whole-Sign convention (where each sign IS a house) and
# from the Equal-house convention (where each house is exactly 30°). For the
# native's Aries lagna at 12°23'55", Whole-Sign and Bhava-Chalit will mostly
# agree for non-sandhi planets but diverge at sign boundaries.


def midpoint_arc(a: float, b: float) -> float:
    """Shortest-arc midpoint between two longitudes (degrees, 0-360)."""
    a = a % 360.0
    b = b % 360.0
    diff = (b - a) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (a + diff / 2.0) % 360.0


def _in_arc(lon: float, start: float, end: float) -> bool:
    """True if lon lies in the arc from start to end going forward (mod 360)."""
    lon = lon % 360.0
    start = start % 360.0
    end = end % 360.0
    if start <= end:
        return start <= lon < end
    return lon >= start or lon < end


def compute_bhava_chalit_house(planet_lon: float, cusps: list[float]) -> int:
    """
    Return the Bhava-Chalit house (1..12) for a planet at planet_lon, given
    the native's 12 natal Sripati cusps.

    `cusps` is a length-12 list where cusps[i] is the midpoint of bhava i+1
    (i.e., cusps[0] is the midpoint of the 1st bhava ≈ ascendant degree).

    Sripati convention: bhava N spans the half-arc band centered on cusps[N-1].
    """
    if len(cusps) != 12:
        raise ValueError(f"compute_bhava_chalit_house: expected 12 cusps, got {len(cusps)}")

    planet_lon = planet_lon % 360.0
    # Compute the 12 boundary points: between consecutive cusp midpoints
    boundaries = [midpoint_arc(cusps[i], cusps[(i + 1) % 12]) for i in range(12)]

    # bhava N starts at boundaries[N-1] and ends at boundaries[N] (mod 12).
    # i.e., bhava 1 spans boundaries[11] → boundaries[0] (the band centered on cusps[0]).
    for n in range(12):
        start = boundaries[(n - 1) % 12]
        end = boundaries[n]
        if _in_arc(planet_lon, start, end):
            return n + 1

    raise RuntimeError(
        f"compute_bhava_chalit_house: longitude {planet_lon} did not match any bhava "
        f"— cusps={cusps}"
    )
