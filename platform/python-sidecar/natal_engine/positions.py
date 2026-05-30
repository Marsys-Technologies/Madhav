"""
positions.py — Graha longitude computation via pyswisseph.

This is the load-bearing astronomical primitive. All other modules
(houses, dignities, vargas, dashas, sensitive_points) consume the graha
states this module produces.

Conventions (must not drift):
- Sidereal zodiac; ayanamsha set via `swe.set_sid_mode(...)` per the
  configured `ayanamsha_config_id` (default: Lahiri / SIDM_LAHIRI).
- `swe.MEAN_NODE` for Rahu — TRUE_NODE is forbidden (Phase 4B standard,
  see panchang_engine/planets.py).
- Ketu derived as `(Rahu + 180.0) mod 360`.
- 9 grahas total: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.

This module is pure: no I/O, no LLM, no DB.
"""

from __future__ import annotations

import swisseph as swe

from .schema import GrahaState

# Sign + nakshatra naming. Mirror of panchang_engine/shastra_tables.py to keep
# the natal_engine self-contained (no cross-module reach during scaffold phase).
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Dignity scaffold — exaltation/debilitation/own signs per BPHS. Friend/enemy
# tables are stubbed for the scaffold; unit 1.2 fills in the temporal-friendship
# refinements per JH parity.
_EXALTATION = {
    "Sun": 1,        # Aries
    "Moon": 2,       # Taurus
    "Mars": 10,      # Capricorn
    "Mercury": 6,    # Virgo
    "Jupiter": 4,    # Cancer
    "Venus": 12,     # Pisces
    "Saturn": 7,     # Libra
    "Rahu": 3,       # Gemini (most schools)
    "Ketu": 9,       # Sagittarius (most schools)
}
_DEBILITATION = {n: ((s - 1 + 6) % 12) + 1 for n, s in _EXALTATION.items()}

# Own signs per BPHS Ch.3
_OWN_SIGNS: dict[str, set[int]] = {
    "Sun": {5},
    "Moon": {4},
    "Mars": {1, 8},
    "Mercury": {3, 6},
    "Jupiter": {9, 12},
    "Venus": {2, 7},
    "Saturn": {10, 11},
    "Rahu": set(),  # no traditional own-sign; left empty for scaffold
    "Ketu": set(),
}

# swisseph graha codes — Rahu uses MEAN_NODE (Phase 4B standard).
NINE_GRAHAS_SWE: list[tuple[str, int]] = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
    ("Rahu", swe.MEAN_NODE),
]

_NAKSHATRA_SPAN = 360.0 / 27.0
_PADA_SPAN = _NAKSHATRA_SPAN / 4.0
_SIGN_SPAN = 30.0

_SWE_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED

# Equatorial flag — returns RA + declination instead of ecliptic longitude/latitude.
# Note: FLG_EQUATORIAL is NOT combined with FLG_SIDEREAL; right ascension and
# declination are always tropical/equatorial quantities — applying an ayanamsha
# correction to them is astronomically meaningless.
_EQ_FLAGS = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL

# Out-of-bounds declination threshold: Sun's max declination ≈ 23.44° (obliquity).
# A body beyond this is "out of bounds" — beyond the Sun's path, indicating
# enhanced or erratic expression in Vedic interpretation.
_OOB_THRESHOLD = 23.5

# Heliocentric flag — tropical (not sidereal) per swisseph convention.
# Heliocentric positions are computed in the ecliptic reference frame centred
# on the Sun; applying SEFLG_SIDEREAL to a heliocentric calc would apply the
# ayanamsha twice (once for the frame shift, once for the sidereal correction)
# and produce incorrect results.  We therefore use FLG_SWIEPH | FLG_HELCTR only,
# returning a tropical heliocentric longitude.  Callers that need the sidereal
# equivalent can subtract the chart's ayanamsha value themselves.
_HELIO_FLAGS = swe.FLG_SWIEPH | swe.FLG_HELCTR


def get_heliocentric(body_id: int, jd_ut: float) -> tuple[float, float]:
    """Return (heliocentric_longitude, heliocentric_latitude) for a body.

    Uses tropical ecliptic coordinates (heliocentric frame).

    Special cases:
    - Sun (swe.SUN): the Sun sits at the heliocentric origin — querying it
      directly with FLG_HELCTR yields (0.0, 0.0).  The astronomically
      meaningful "Sun heliocentric" slot is Earth's position as seen from the
      Sun, so we query swe.EARTH with FLG_HELCTR instead.
    - Moon (swe.MOON): swisseph does not support a heliocentric Moon because
      the Moon orbits Earth, not the Sun.  We return (0.0, 0.0) as a sentinel
      that callers replace with the geocentric values (see compute_graha_states).
    - Rahu/Ketu (swe.MEAN_NODE / derived): nodes are a geometric construct with
      no heliocentric meaning; we return (0.0, 0.0) and callers substitute the
      geocentric longitude.
    """
    if body_id in (swe.MOON, swe.MEAN_NODE):
        return 0.0, 0.0  # sentinel; caller replaces
    # For the Sun, query Earth's heliocentric position instead
    effective_id = swe.EARTH if body_id == swe.SUN else body_id
    try:
        result, _ = swe.calc_ut(jd_ut, effective_id, _HELIO_FLAGS)
        lon = result[0] % 360.0
        lat = result[1]
        return lon, lat
    except Exception:
        return 0.0, 0.0


def get_equatorial(body_id: int, jd_ut: float) -> tuple[float, float]:
    """Return (right_ascension_deg, declination_deg) for a body.

    Uses tropical geocentric equatorial coordinates (swisseph FLG_EQUATORIAL).
    RA is in degrees (0–360); declination in degrees (−90 to +90).

    Special cases:
    - Moon (swe.MOON): standard equatorial computation — Moon has a well-defined
      geocentric equatorial position.
    - Rahu/Ketu (swe.MEAN_NODE): nodes are a geometric construct; equatorial
      coordinates are computed normally (the node point on the ecliptic does
      project to an equatorial position).

    For the Sun: uses swe.SUN directly (not Earth) because we want the
    geocentric direction toward the Sun, which is meaningful for equatorial coords.
    """
    try:
        result, _ = swe.calc_ut(jd_ut, body_id, _EQ_FLAGS)
        ra_deg = result[0] % 360.0
        dec_deg = result[1]
        return ra_deg, dec_deg
    except Exception:
        return 0.0, 0.0


def get_horizontal(
    jd_ut: float,
    geo_lon: float,
    geo_lat: float,
    body_ecl_lon: float,
    body_ecl_lat: float,
) -> tuple[float, float]:
    """Return (azimuth_deg, altitude_deg) for a body at the birth location.

    Uses swe.azalt with ECL2HOR: input is tropical geocentric ecliptic
    longitude + latitude; output is horizontal coordinates.

    Azimuth convention: swisseph returns azimuth measured from the south
    point rotating westward (S=0°, W=90°, N=180°, E=270°).  We convert
    to the standard compass convention N=0°, E=90°, S=180°, W=270° by
    adding 180° mod 360°.

    Returns true altitude (not apparent/refracted altitude).
    """
    try:
        az_raw, alt_true, _ = swe.azalt(
            jd_ut,
            swe.ECL2HOR,
            (geo_lon, geo_lat, 0.0),  # geopos: (lon, lat, altitude_m)
            1013.25,                   # standard atmospheric pressure (mbar)
            15.0,                      # standard temperature (°C)
            (body_ecl_lon, body_ecl_lat, 1.0),  # (ecl_lon, ecl_lat, distance)
        )
        # Convert S=0 → N=0 compass convention
        az_north = (az_raw + 180.0) % 360.0
        return az_north, alt_true
    except Exception:
        return 0.0, 0.0


def _lon_to_sign(lon: float) -> tuple[int, str]:
    sign_idx = int(lon // _SIGN_SPAN) % 12
    return sign_idx + 1, SIGN_NAMES[sign_idx]


# ---------------------------------------------------------------------------
# E-06: Varga (D1/D9/D10) computation for any longitude
# ---------------------------------------------------------------------------

def _navamsa_sign_idx_for(sign_id: int, deg_in_sign: float) -> int:
    """Return 0-based sign index for D9 (Navamsa) given natal sign_id (1..12)
    and degree within sign (0..30).

    Standard Parashari Navamsa rule:
      - Movable signs (1,4,7,10): navamsa cycle starts from itself
      - Fixed signs (2,5,8,11):   cycle starts from 9th sign
      - Dual signs (3,6,9,12):    cycle starts from 5th sign
    """
    nav_idx = int(deg_in_sign // (30.0 / 9.0))  # 0..8
    quality = (sign_id - 1) % 3  # 0=movable, 1=fixed, 2=dual
    if quality == 0:
        start = sign_id
    elif quality == 1:
        start = ((sign_id - 1 + 8) % 12) + 1  # 9th from itself
    else:
        start = ((sign_id - 1 + 4) % 12) + 1  # 5th from itself
    return ((start - 1 + nav_idx) % 12)


def _dasamsa_sign_idx_for(sign_id: int, deg_in_sign: float) -> int:
    """Return 0-based sign index for D10 (Dasamsa / Dashamsha).

    Standard Parashari Dasamsa rule:
      - Odd signs (1,3,5,7,9,11):  10 arcs of 3° each, cycle starts from itself
      - Even signs (2,4,6,8,10,12): 10 arcs of 3° each, cycle starts from 9th sign
    """
    das_idx = int(deg_in_sign // 3.0)  # 0..9 (each arc = 3°)
    das_idx = min(das_idx, 9)          # guard fp edge at exactly 30°
    if sign_id % 2 == 1:
        # Odd sign: start from itself
        start = sign_id
    else:
        # Even sign: start from 9th sign (counting from itself)
        start = ((sign_id - 1 + 8) % 12) + 1
    return ((start - 1 + das_idx) % 12)


def compute_varga_for_lon(longitude: float) -> dict:
    """Compute D1, D9, D10 varga positions for a given sidereal longitude (0–360°).

    Returns a dict with keys 'D1', 'D9', 'D10', each containing:
      {'sign': str, 'sign_index': int (1-based), 'degree': float (for D1 only)}

    Self-contained: does not depend on GrahaState or pipeline.varga_formulas.
    Uses the same Parashari formulae as vargas.py (_d9_sign) and the standard
    Dasamsa (10-arc / 3°-each) rule for D10.
    """
    sign_idx = int(longitude // _SIGN_SPAN) % 12  # 0-based
    sign_id = sign_idx + 1                          # 1-based
    deg_in_sign = longitude % _SIGN_SPAN

    d9_idx = _navamsa_sign_idx_for(sign_id, deg_in_sign)
    d10_idx = _dasamsa_sign_idx_for(sign_id, deg_in_sign)

    return {
        "D1":  {"sign": SIGN_NAMES[sign_idx], "sign_index": sign_id,     "degree": round(deg_in_sign, 6)},
        "D9":  {"sign": SIGN_NAMES[d9_idx],   "sign_index": d9_idx + 1},
        "D10": {"sign": SIGN_NAMES[d10_idx],  "sign_index": d10_idx + 1},
    }


def _lon_to_nakshatra(lon: float) -> tuple[int, str, int]:
    nak_idx = int(lon // _NAKSHATRA_SPAN) % 27
    pada = int((lon - nak_idx * _NAKSHATRA_SPAN) // _PADA_SPAN) + 1
    pada = max(1, min(4, pada))
    return nak_idx + 1, NAKSHATRA_NAMES[nak_idx], pada


def _dignity_for(name: str, sign_id: int) -> str:
    if _EXALTATION.get(name) == sign_id:
        return "exalted"
    if _DEBILITATION.get(name) == sign_id:
        return "debilitated"
    if sign_id in _OWN_SIGNS.get(name, set()):
        return "own"
    # friend / enemy / neutral refinement deferred to unit 1.2
    return "unknown"


def set_ayanamsha(ayanamsha_config_id: str, jd_ut: float | None = None) -> None:
    """Configure swisseph's sidereal mode by config id.

    Accepted ids:
    - Engine-registry ids (unit 1.2; preferred): 'jh_true_chitra', 'kp',
      'lahiri_standard'. For `jh_true_chitra`, `jd_ut` is required so the
      SIDM_USER calibration can pin to JH's exact value at that JD.
    - Legacy unit-1.1 aliases (kept for back-compat with existing tests):
      'lahiri' / 'lahiri-chitrapaksha-true' → SIDM_LAHIRI
      'raman'                                → SIDM_RAMAN
      'krishnamurti'                         → SIDM_KRISHNAMURTI
    """
    config = ayanamsha_config_id.lower()
    # New engine-registry ids
    from .ayanamsha_registry import AYANAMSHA_REGISTRY, apply_ayanamsha
    if config in AYANAMSHA_REGISTRY:
        if config == "jh_true_chitra" and jd_ut is None:
            # Best-effort: pin at the canonical reference JD (native birth)
            jd_ut = AYANAMSHA_REGISTRY[config]["pinned_at_jd_ut"]
        apply_ayanamsha(jd_ut if jd_ut is not None else 0.0, config)
        return
    # Legacy aliases (unit 1.1 scaffold compatibility)
    if config in ("lahiri", "lahiri-chitrapaksha-true"):
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    elif config == "raman":
        swe.set_sid_mode(swe.SIDM_RAMAN, 0, 0)
    elif config == "krishnamurti":
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI, 0, 0)
    # Pipeline aliases — map build-pipeline IDs to engine registry IDs
    elif config == "true_chitra":
        apply_ayanamsha(
            AYANAMSHA_REGISTRY["jh_true_chitra"]["pinned_at_jd_ut"],
            "jh_true_chitra",
        )
    elif config == "surya_siddhanta":
        swe.set_sid_mode(swe.SIDM_SURYASIDDHANTA, 0, 0)
    else:
        raise ValueError(f"Unknown ayanamsha_config_id: {ayanamsha_config_id!r}")


_TROPICAL_FLAGS = swe.FLG_SWIEPH  # tropical geocentric: lon+lat needed for swe.azalt


def compute_graha_states(
    jd_ut: float,
    geo_lat: float = 20.27,
    geo_lon: float = 85.84,
) -> list[GrahaState]:
    """Compute the 9 graha states at the given Julian Day (UT).

    Caller must have already invoked `set_ayanamsha(...)`.

    Args:
        jd_ut:   Julian Day number (Universal Time).
        geo_lat: Geographic latitude of the observer in degrees (N positive).
                 Defaults to Bhubaneswar (native birth location).
        geo_lon: Geographic longitude of the observer in degrees (E positive).
                 Defaults to Bhubaneswar (native birth location).

    Each GrahaState now carries:
    - heliocentric_longitude / heliocentric_latitude  (tropical ecliptic, helio)
    - declination_deg / right_ascension_deg           (geocentric equatorial)
    - altitude_deg / azimuth_deg                      (horizon coords at birth loc)
    - out_of_bounds                                   (|dec| > 23.5°)

    Conventions for non-standard bodies:
    - Moon: heliocentric coords are meaningless (Moon orbits Earth).
      We mirror the geocentric longitude/latitude so consumers always
      have a valid float rather than a sentinel.
    - Rahu/Ketu: pure geometric constructs; we mirror the geocentric
      longitude and set latitude to 0.0 (nodes lie on the ecliptic by
      definition).
    """
    states: list[GrahaState] = []
    for name, swe_code in NINE_GRAHAS_SWE:
        result, _ = swe.calc_ut(jd_ut, swe_code, _SWE_FLAGS)
        lon = result[0] % 360.0
        lat = result[1]  # geocentric latitude (unused for sidereal lon but kept)
        speed = result[3]
        retrograde = speed < 0.0
        sign_id, sign_name = _lon_to_sign(lon)
        nak_id, nak_name, pada = _lon_to_nakshatra(lon)

        # Heliocentric coordinates
        helio_lon, helio_lat = get_heliocentric(swe_code, jd_ut)
        if name == "Moon":
            # Mirror geocentric — Moon has no Sun-centred orbit
            helio_lon, helio_lat = lon, lat
        elif name == "Rahu":
            # Nodes lie on the ecliptic plane
            helio_lon, helio_lat = lon, 0.0

        # Equatorial coordinates (geocentric, tropical)
        ra_deg, dec_deg = get_equatorial(swe_code, jd_ut)

        # Horizon coordinates — need tropical ecliptic lon/lat for swe.azalt
        # Rahu uses MEAN_NODE; tropical ecliptic lon is the same value as
        # the sidereal one with ayanamsha added back — but for azalt we use
        # the raw tropical geocentric result.
        trop_result, _ = swe.calc_ut(jd_ut, swe_code, _TROPICAL_FLAGS)
        trop_lon = trop_result[0] % 360.0
        trop_lat = trop_result[1]
        az_deg, alt_deg = get_horizontal(jd_ut, geo_lon, geo_lat, trop_lon, trop_lat)

        # Out-of-bounds: declination exceeds the Sun's maximum (~23.5°)
        oob = abs(dec_deg) > _OOB_THRESHOLD

        states.append(
            GrahaState(
                name=name,
                longitude_deg=lon,
                sign=sign_name,
                sign_id=sign_id,
                nakshatra=nak_name,
                nakshatra_id=nak_id,
                pada=pada,
                retrograde=retrograde,
                speed_deg_per_day=speed,
                dignity_status=_dignity_for(name, sign_id),
                heliocentric_longitude=helio_lon,
                heliocentric_latitude=helio_lat,
                declination_deg=dec_deg,
                right_ascension_deg=ra_deg,
                altitude_deg=alt_deg,
                azimuth_deg=az_deg,
                out_of_bounds=oob,
            )
        )

    # Ketu = Rahu + 180° mod 360. Speed = -Rahu.speed (counter-node).
    rahu = next(s for s in states if s.name == "Rahu")

    # Ketu equatorial: directly compute via MEAN_NODE + 180° projection trick.
    # swisseph has no direct "south node" body; compute Rahu's equatorial and
    # derive Ketu as the antipodal point (RA+180°, -dec).
    rahu_ra = rahu.right_ascension_deg
    rahu_dec = rahu.declination_deg
    ketu_ra = (rahu_ra + 180.0) % 360.0
    ketu_dec = -rahu_dec  # antipodal declination

    ketu_lon = (rahu.longitude_deg + 180.0) % 360.0
    ketu_sign_id, ketu_sign_name = _lon_to_sign(ketu_lon)
    ketu_nak_id, ketu_nak_name, ketu_pada = _lon_to_nakshatra(ketu_lon)

    # Ketu horizon: use antipodal ecliptic longitude (tropical) for azalt
    ketu_trop_lon = (rahu.longitude_deg + 180.0) % 360.0  # approx tropical antip.
    ketu_az_deg, ketu_alt_deg = get_horizontal(
        jd_ut, geo_lon, geo_lat, ketu_trop_lon, 0.0
    )
    ketu_oob = abs(ketu_dec) > _OOB_THRESHOLD

    states.append(
        GrahaState(
            name="Ketu",
            longitude_deg=ketu_lon,
            sign=ketu_sign_name,
            sign_id=ketu_sign_id,
            nakshatra=ketu_nak_name,
            nakshatra_id=ketu_nak_id,
            pada=ketu_pada,
            retrograde=True,  # nodes are always retrograde in mean-node convention
            speed_deg_per_day=-rahu.speed_deg_per_day,
            dignity_status=_dignity_for("Ketu", ketu_sign_id),
            # Ketu mirrors the antipodal Rahu helio_lon; latitude = 0 (ecliptic plane)
            heliocentric_longitude=(rahu.heliocentric_longitude + 180.0) % 360.0,
            heliocentric_latitude=0.0,
            declination_deg=ketu_dec,
            right_ascension_deg=ketu_ra,
            altitude_deg=ketu_alt_deg,
            azimuth_deg=ketu_az_deg,
            out_of_bounds=ketu_oob,
        )
    )

    return states


def compute_node_states(
    jd_ut: float,
    ayanamsha_deg: float,
    geo_lat: float = 20.27,
    geo_lon: float = 85.84,
) -> dict[str, dict]:
    """Compute True Node and Mean Node Rahu/Ketu positions separately.

    Returns a dict with 4 entries:
      rahu_true  — osculating (true) node Rahu (swe.TRUE_NODE = 11)
      ketu_true  — antipodal to rahu_true
      rahu_mean  — mean node Rahu (swe.MEAN_NODE = 10)
      ketu_mean  — antipodal to rahu_mean

    Both node types are always retrograde by astronomical convention.

    Implementation note — why we use tropical flags + manual ayanamsha subtraction:
    swisseph 2.10 with SIDM_TRUE_CITRA active raises a Moshier-range error when
    FLG_SIDEREAL is combined with TRUE_NODE (body 11).  This is a swisseph internal
    behaviour where TRUE_NODE's ephemeris code path triggers a range check against
    the Moshier table limits when the sidereal mode's internal epoch (t0) is set.
    MEAN_NODE (body 10) does not trigger this bug under the same sidereal mode.

    The safe workaround — used here and matching how `get_heliocentric()` handles
    nodes — is to compute tropical longitude via `_TROPICAL_FLAGS` (no FLG_SIDEREAL)
    and subtract the ayanamsha value explicitly:
        sidereal_lon = (tropical_lon - ayanamsha_deg) % 360.0

    The ayanamsha value passed in is the one already computed by `apply_ayanamsha()`
    for the chart's JD, ensuring consistency with the rest of the engine output.

    Equatorial coordinates (RA / declination) for the nodes are computed via
    the existing `get_equatorial()` helper which uses FLG_EQUATORIAL.
    Horizontal coordinates (azimuth / altitude) are computed via `get_horizontal()`.
    """
    node_pairs = [
        ("true", swe.TRUE_NODE, "rahu_true", "ketu_true"),
        ("mean", swe.MEAN_NODE, "rahu_mean", "ketu_mean"),
    ]
    result: dict[str, dict] = {}

    for _node_type, body_id, label_rahu, label_ketu in node_pairs:
        # Use tropical flags (no FLG_SIDEREAL) to avoid a swisseph 2.10 bug where
        # TRUE_NODE + FLG_SIDEREAL + SIDM_TRUE_CITRA triggers a Moshier range error.
        # We apply the ayanamsha correction manually instead.
        calc_result, _ = swe.calc_ut(jd_ut, body_id, _TROPICAL_FLAGS | swe.FLG_SPEED)
        tropical_lon = calc_result[0] % 360.0
        speed = calc_result[3]  # typically negative (retrograde)

        # Sidereal longitude = tropical − ayanamsha (mod 360)
        rahu_lon = (tropical_lon - ayanamsha_deg) % 360.0

        ketu_lon = (rahu_lon + 180.0) % 360.0

        # Equatorial coordinates via FLG_EQUATORIAL (tropical, not sidereal)
        rahu_ra, rahu_dec = get_equatorial(body_id, jd_ut)
        ketu_ra = (rahu_ra + 180.0) % 360.0
        ketu_dec = -rahu_dec  # antipodal declination

        # Horizontal coordinates: reuse the tropical longitude already computed above.
        trop_rahu_lon = tropical_lon
        trop_ketu_lon = (trop_rahu_lon + 180.0) % 360.0

        rahu_az, rahu_alt = get_horizontal(jd_ut, geo_lon, geo_lat, trop_rahu_lon, 0.0)
        ketu_az, ketu_alt = get_horizontal(jd_ut, geo_lon, geo_lat, trop_ketu_lon, 0.0)

        # Sign + nakshatra for Rahu
        rahu_sign_id, rahu_sign_name = _lon_to_sign(rahu_lon)
        rahu_nak_id, rahu_nak_name, rahu_pada = _lon_to_nakshatra(rahu_lon)

        # Sign + nakshatra for Ketu
        ketu_sign_id, ketu_sign_name = _lon_to_sign(ketu_lon)
        ketu_nak_id, ketu_nak_name, ketu_pada = _lon_to_nakshatra(ketu_lon)

        result[label_rahu] = {
            "longitude": rahu_lon,
            "latitude": 0.0,             # nodes lie on the ecliptic by definition
            "speed": speed,
            "retro": True,               # nodes are always retrograde
            "sign": rahu_sign_name,
            "sign_index": rahu_sign_id,
            "degree": rahu_lon % 30.0,
            "nakshatra": rahu_nak_name,
            "nakshatra_id": rahu_nak_id,
            "pada": rahu_pada,
            "heliocentric_longitude": rahu_lon,  # nodes: mirror geocentric (no helio meaning)
            "heliocentric_latitude": 0.0,
            "declination_deg": rahu_dec,
            "right_ascension_deg": rahu_ra,
            "altitude_deg": rahu_alt,
            "azimuth_deg": rahu_az,
            "out_of_bounds": abs(rahu_dec) > _OOB_THRESHOLD,
            "varga_position": compute_varga_for_lon(rahu_lon),
        }

        result[label_ketu] = {
            "longitude": ketu_lon,
            "latitude": 0.0,
            "speed": -speed,             # counter-node: negated speed
            "retro": True,               # nodes are always retrograde
            "sign": ketu_sign_name,
            "sign_index": ketu_sign_id,
            "degree": ketu_lon % 30.0,
            "nakshatra": ketu_nak_name,
            "nakshatra_id": ketu_nak_id,
            "pada": ketu_pada,
            "heliocentric_longitude": ketu_lon,
            "heliocentric_latitude": 0.0,
            "declination_deg": ketu_dec,
            "right_ascension_deg": ketu_ra,
            "altitude_deg": ketu_alt,
            "azimuth_deg": ketu_az,
            "out_of_bounds": abs(ketu_dec) > _OOB_THRESHOLD,
            "varga_position": compute_varga_for_lon(ketu_lon),
        }

    return result


# ---------------------------------------------------------------------------
# E-05: Outer planets + asteroids
# ---------------------------------------------------------------------------

# swisseph body IDs for outer planets (built-in constants)
# swe.CHIRON = 15, swe.CERES = 17, swe.PALLAS = 18, swe.JUNO = 19, swe.VESTA = 20
# swe.URANUS = 7, swe.NEPTUNE = 8, swe.PLUTO = 9
OUTER_BODIES: list[tuple[str, int, str]] = [
    ("chiron",  swe.CHIRON,   "wounded healer, maverick"),
    ("ceres",   swe.CERES,    "nurturing, agriculture, grief"),
    ("pallas",  swe.PALLAS,   "wisdom, strategy, crafts"),
    ("juno",    swe.JUNO,     "marriage, partnership equality"),
    ("vesta",   swe.VESTA,    "focus, dedication, sacred fire"),
    ("uranus",  swe.URANUS,   "disruption, innovation, revolution"),
    ("neptune", swe.NEPTUNE,  "illusion, spirituality, dissolution"),
    ("pluto",   swe.PLUTO,    "transformation, power, death-rebirth"),
]

# Numbered asteroids require optional SE asteroid ephemeris files
_SEDNA_ID = 90377
_ERIS_ID  = 136199

NUMBERED_ASTEROIDS: list[tuple[str, int, str]] = [
    ("sedna", _SEDNA_ID, "isolation, extreme cold, transition"),
    ("eris",  _ERIS_ID,  "discord, feminism, rivalry"),
]


def _outer_null() -> dict:
    """Sentinel dict used when a body cannot be computed."""
    return {
        "longitude": 0.0,
        "latitude": 0.0,
        "speed": 0.0,
        "retro": False,
        "sign": SIGN_NAMES[0],
        "sign_index": 1,
        "degree": 0.0,
        "nakshatra": NAKSHATRA_NAMES[0],
        "nakshatra_id": 1,
        "pada": 1,
        "significance": "",
        "heliocentric_longitude": 0.0,
        "heliocentric_latitude": 0.0,
        "declination_deg": 0.0,
        "right_ascension_deg": 0.0,
        "altitude_deg": 0.0,
        "azimuth_deg": 0.0,
        "out_of_bounds": False,
        "varga_position": compute_varga_for_lon(0.0),
    }


def _body_dict_from_result(
    result: tuple,
    ayanamsha_deg: float,
    significance: str,
) -> dict:
    """Build a standard outer-body dict from a swe.calc_ut result tuple."""
    tropical_lon = result[0] % 360.0
    lat = result[1]
    speed = result[3]
    sidereal_lon = (tropical_lon - ayanamsha_deg) % 360.0
    sign_idx = int(sidereal_lon / _SIGN_SPAN) % 12
    nak_idx = int(sidereal_lon / _NAKSHATRA_SPAN) % 27
    pada = int((sidereal_lon - nak_idx * _NAKSHATRA_SPAN) / _PADA_SPAN) + 1
    pada = max(1, min(4, pada))
    return {
        "longitude": sidereal_lon,
        "latitude": lat,
        "speed": speed,
        "retro": speed < 0,
        "sign": SIGN_NAMES[sign_idx],
        "sign_index": sign_idx + 1,
        "degree": sidereal_lon % _SIGN_SPAN,
        "nakshatra": NAKSHATRA_NAMES[nak_idx],
        "nakshatra_id": nak_idx + 1,
        "pada": pada,
        "significance": significance,
        "heliocentric_longitude": 0.0,
        "heliocentric_latitude": 0.0,
        "declination_deg": 0.0,
        "right_ascension_deg": 0.0,
        "altitude_deg": 0.0,
        "azimuth_deg": 0.0,
        "out_of_bounds": False,
        "varga_position": compute_varga_for_lon(sidereal_lon),
    }


def compute_outer_bodies(
    jd_ut: float,
    ayanamsha_deg: float,
    geo_lat: float = 20.27,
    geo_lon: float = 85.84,
) -> dict[str, dict | None]:
    """Compute positions for 8 outer planets/asteroids + 2 numbered asteroids.

    The 8 built-in bodies (Chiron, Ceres, Pallas, Juno, Vesta, Uranus, Neptune,
    Pluto) use standard swisseph body ids and are expected to always succeed.

    The 2 numbered asteroids (Sedna=90377, Eris=136199) require optional SE
    asteroid ephemeris files and may be absent.  Their dict slot is set to None
    when unavailable — callers must guard for None.

    Implementation note — same tropical-flags + manual ayanamsha subtraction
    pattern used by compute_node_states() and compute_lilith_states().
    """
    import logging
    logger = logging.getLogger(__name__)

    results: dict[str, dict | None] = {}

    # --- 8 main outer bodies (always available) ---
    for name, body_id, significance in OUTER_BODIES:
        try:
            raw, _ = swe.calc_ut(jd_ut, body_id, _TROPICAL_FLAGS | swe.FLG_SPEED)
            results[name] = _body_dict_from_result(raw, ayanamsha_deg, significance)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Outer body %s (id=%d) failed: %s", name, body_id, exc)
            sentinel = _outer_null()
            sentinel["significance"] = significance
            results[name] = sentinel

    # --- 2 numbered asteroids (optional — None when ephemeris files absent) ---
    for name, asteroid_id, significance in NUMBERED_ASTEROIDS:
        try:
            raw, _ = swe.calc_ut(
                jd_ut,
                swe.AST_OFFSET + asteroid_id,
                swe.FLG_SWIEPH | swe.FLG_SPEED,
            )
            results[name] = _body_dict_from_result(raw, ayanamsha_deg, significance)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Numbered asteroid %s (id=%d) unavailable: %s", name, asteroid_id, exc
            )
            results[name] = None  # signal: ephemeris file absent

    return results


def compute_lilith_states(
    jd_ut: float,
    ayanamsha_deg: float,
    geo_lat: float = 20.27,
    geo_lon: float = 85.84,
) -> dict[str, dict]:
    """Compute Mean Lilith (MEAN_APOG) and True Lilith (OSCU_APOG) positions.

    Returns a dict with 2 entries:
      lilith_mean  — mean apogee of the Moon's orbit (swe.MEAN_APOG = 12)
      lilith_true  — osculating (true) apogee of the Moon's orbit (swe.OSCU_APOG = 13)

    Both are virtual points on the Moon's orbit, not real bodies.  They represent
    the Moon's apogee (farthest point from Earth).  In Vedic astrology these are
    sometimes called Black Moon Lilith (mean) and its osculating counterpart (true).

    Implementation note — same tropical-flags + manual ayanamsha subtraction
    workaround used by compute_node_states() to avoid swisseph FLG_SIDEREAL
    interaction issues with non-planetary body codes.

    The `retro` field reflects the actual computed speed sign.  Unlike the lunar
    nodes (which are always retrograde), the apogee direction varies: the mean
    apogee is always prograde (speed > 0), while the true/osculating apogee
    oscillates and can be retrograde at certain phases.
    """
    result: dict[str, dict] = {}

    for _lilith_type, body_id, label in [
        ("mean", swe.MEAN_APOG, "lilith_mean"),   # swe.MEAN_APOG = 12
        ("true", swe.OSCU_APOG, "lilith_true"),   # swe.OSCU_APOG = 13
    ]:
        try:
            calc_result, _ = swe.calc_ut(jd_ut, body_id, _TROPICAL_FLAGS | swe.FLG_SPEED)
            tropical_lon = calc_result[0] % 360.0
            lat = calc_result[1]
            speed = calc_result[3]

            # Sidereal longitude = tropical − ayanamsha (mod 360)
            sidereal_lon = (tropical_lon - ayanamsha_deg) % 360.0

            sign_id, sign_name = _lon_to_sign(sidereal_lon)
            nak_id, nak_name, pada = _lon_to_nakshatra(sidereal_lon)

            # Equatorial coordinates
            ra, dec = get_equatorial(body_id, jd_ut)

            # Horizontal coordinates (uses tropical longitude per get_horizontal convention)
            az, alt = get_horizontal(jd_ut, geo_lon, geo_lat, tropical_lon, lat)

            result[label] = {
                "longitude": sidereal_lon,
                "latitude": lat,
                "speed": speed,
                "retro": speed < 0,
                "sign": sign_name,
                "sign_index": sign_id,
                "degree": sidereal_lon % _SIGN_SPAN,
                "nakshatra": nak_name,
                "nakshatra_id": nak_id,
                "pada": pada,
                "heliocentric_longitude": 0.0,  # apogee: no heliocentric meaning
                "heliocentric_latitude": 0.0,
                "declination_deg": dec,
                "right_ascension_deg": ra,
                "altitude_deg": alt,
                "azimuth_deg": az,
                "out_of_bounds": abs(dec) > _OOB_THRESHOLD,
                "varga_position": compute_varga_for_lon(sidereal_lon),
            }
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning(
                "Lilith %s computation failed: %s", _lilith_type, exc
            )
            # Emit a zero-sentinel so callers always have both keys
            result[label] = {
                "longitude": 0.0,
                "latitude": 0.0,
                "speed": 0.0,
                "retro": False,
                "sign": SIGN_NAMES[0],
                "sign_index": 1,
                "degree": 0.0,
                "nakshatra": NAKSHATRA_NAMES[0],
                "nakshatra_id": 1,
                "pada": 1,
                "heliocentric_longitude": 0.0,
                "heliocentric_latitude": 0.0,
                "declination_deg": 0.0,
                "right_ascension_deg": 0.0,
                "altitude_deg": 0.0,
                "azimuth_deg": 0.0,
                "out_of_bounds": False,
                "varga_position": compute_varga_for_lon(0.0),
            }

    return result


# ---------------------------------------------------------------------------
# E-07: Cross-ayanamsha divergence report generator
# ---------------------------------------------------------------------------

# Canonical graha names used for comparison across chart outputs.
_COMPARISON_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
# Lowercase aliases (for robustness when consumer uses lowercase keys)
_COMPARISON_GRAHAS_LOWER = [g.lower() for g in _COMPARISON_GRAHAS]


def _extract_graha_entry(chart_output: dict, graha_name: str) -> dict | None:
    """Extract a graha dict from a chart_output by name (case-insensitive).

    Supports two common structures:
    - chart_output['grahas'] as a list[dict] with a 'name' key
    - chart_output['grahas'] as a dict keyed by graha name
    """
    grahas_raw = chart_output.get("grahas")
    if grahas_raw is None:
        return None
    name_lower = graha_name.lower()
    if isinstance(grahas_raw, list):
        for entry in grahas_raw:
            if isinstance(entry, dict) and entry.get("name", "").lower() == name_lower:
                return entry
        return None
    if isinstance(grahas_raw, dict):
        # Try exact case first, then case-insensitive scan
        if graha_name in grahas_raw:
            return grahas_raw[graha_name]
        for k, v in grahas_raw.items():
            if k.lower() == name_lower:
                return v
        return None
    return None


def generate_cross_ayanamsha_report(chart_outputs_by_ayanamsha: dict[str, dict]) -> dict:
    """Compare chart_output dicts for different ayanamshas.

    Returns divergence metrics and high-divergence flags per pair and overall.

    Parameters
    ----------
    chart_outputs_by_ayanamsha : dict
        Maps ayanamsha id → chart_output dict (as returned by compute_chart).
        At least 2 entries required; fewer returns an empty report.

    Returns
    -------
    dict with keys:
      ayanamsha_pairs : list of per-pair dicts
        ayanamsha_1, ayanamsha_2,
        max_position_delta_deg, divergent_grahas, convergent_grahas,
        sign_change_count, navamsa_change_count, divergence_score (0.0–1.0)
      overall_divergence : 'low' | 'medium' | 'high'
      most_divergent_pair : (a1, a2) tuple or None
      pair_count : int
      graha_variance : dict mapping each graha → max delta across all ayanamshas
      most_stable_graha : str  (smallest max delta)
      most_variable_graha : str  (largest max delta)
    """
    ayanamshas = list(chart_outputs_by_ayanamsha.keys())

    if len(ayanamshas) < 2:
        return {
            "ayanamsha_pairs": [],
            "overall_divergence": "low",
            "most_divergent_pair": None,
            "pair_count": 0,
            "graha_variance": {},
            "most_stable_graha": None,
            "most_variable_graha": None,
        }

    pairs: list[dict] = []

    for i in range(len(ayanamshas)):
        for j in range(i + 1, len(ayanamshas)):
            a1, a2 = ayanamshas[i], ayanamshas[j]
            co1 = chart_outputs_by_ayanamsha[a1]
            co2 = chart_outputs_by_ayanamsha[a2]

            deltas: list[float] = []
            sign_changes = 0
            nav_changes = 0
            divergent: list[str] = []
            convergent: list[str] = []

            for graha_name in _COMPARISON_GRAHAS:
                g1 = _extract_graha_entry(co1, graha_name)
                g2 = _extract_graha_entry(co2, graha_name)
                if not g1 or not g2:
                    continue

                # Longitude key: try 'longitude_deg' (GrahaState asdict) then 'longitude'
                lon1 = g1.get("longitude_deg") if g1.get("longitude_deg") is not None else g1.get("longitude", 0.0)
                lon2 = g2.get("longitude_deg") if g2.get("longitude_deg") is not None else g2.get("longitude", 0.0)
                if lon1 is None or lon2 is None:
                    continue

                delta = abs(float(lon1) - float(lon2))
                if delta > 180.0:
                    delta = 360.0 - delta
                deltas.append(delta)

                if delta > 1.0:
                    divergent.append(graha_name)
                else:
                    convergent.append(graha_name)

                # Sign-change check: use 'sign' key or derive from longitude
                sign1 = g1.get("sign") or SIGN_NAMES[int(float(lon1) // 30) % 12]
                sign2 = g2.get("sign") or SIGN_NAMES[int(float(lon2) // 30) % 12]
                if sign1 != sign2:
                    sign_changes += 1

                # Navamsa change: prefer varga_position.D9 if present
                vp1 = g1.get("varga_position", {}) or {}
                vp2 = g2.get("varga_position", {}) or {}
                d9_1 = vp1.get("D9", {}).get("sign") if vp1 else None
                d9_2 = vp2.get("D9", {}).get("sign") if vp2 else None
                if d9_1 is None:
                    # Fall back to computing from longitude
                    vp_fb1 = compute_varga_for_lon(float(lon1))
                    d9_1 = vp_fb1["D9"]["sign"]
                if d9_2 is None:
                    vp_fb2 = compute_varga_for_lon(float(lon2))
                    d9_2 = vp_fb2["D9"]["sign"]
                if d9_1 != d9_2:
                    nav_changes += 1

            max_delta = max(deltas) if deltas else 0.0
            # Normalize: 30° = 1.0 (maximum meaningful divergence within one sign)
            score = round(min(1.0, max_delta / 30.0), 4)

            pairs.append({
                "ayanamsha_1": a1,
                "ayanamsha_2": a2,
                "max_position_delta_deg": round(max_delta, 4),
                "divergent_grahas": divergent,
                "convergent_grahas": convergent,
                "sign_change_count": sign_changes,
                "navamsa_change_count": nav_changes,
                "divergence_score": score,
            })

    # Most divergent pair
    most_divergent: dict | None = max(pairs, key=lambda p: p["divergence_score"]) if pairs else None

    # Overall assessment
    avg_score = sum(p["divergence_score"] for p in pairs) / len(pairs) if pairs else 0.0
    if avg_score < 0.1:
        overall = "low"
    elif avg_score < 0.3:
        overall = "medium"
    else:
        overall = "high"

    # Per-graha variance: max delta across all ayanamsha pairs for each graha
    graha_variance: dict[str, float] = {}
    for graha_name in _COMPARISON_GRAHAS:
        max_g_delta = 0.0
        for i in range(len(ayanamshas)):
            for j in range(i + 1, len(ayanamshas)):
                g1 = _extract_graha_entry(chart_outputs_by_ayanamsha[ayanamshas[i]], graha_name)
                g2 = _extract_graha_entry(chart_outputs_by_ayanamsha[ayanamshas[j]], graha_name)
                if not g1 or not g2:
                    continue
                lon1 = g1.get("longitude_deg") if g1.get("longitude_deg") is not None else g1.get("longitude", 0.0)
                lon2 = g2.get("longitude_deg") if g2.get("longitude_deg") is not None else g2.get("longitude", 0.0)
                if lon1 is None or lon2 is None:
                    continue
                d = abs(float(lon1) - float(lon2))
                if d > 180.0:
                    d = 360.0 - d
                if d > max_g_delta:
                    max_g_delta = d
        graha_variance[graha_name] = round(max_g_delta, 4)

    most_stable = min(graha_variance, key=lambda g: graha_variance[g]) if graha_variance else None
    most_variable = max(graha_variance, key=lambda g: graha_variance[g]) if graha_variance else None

    return {
        "ayanamsha_pairs": pairs,
        "overall_divergence": overall,
        "most_divergent_pair": (
            (most_divergent["ayanamsha_1"], most_divergent["ayanamsha_2"])
            if most_divergent else None
        ),
        "pair_count": len(pairs),
        "graha_variance": graha_variance,
        "most_stable_graha": most_stable,
        "most_variable_graha": most_variable,
    }
