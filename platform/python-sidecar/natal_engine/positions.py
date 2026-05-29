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
        }

    return result
