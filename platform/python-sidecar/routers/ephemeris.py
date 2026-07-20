from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import swisseph as swe

router = APIRouter()

PLANETS = [
    ('Sun', swe.SUN),
    ('Moon', swe.MOON),
    ('Mars', swe.MARS),
    ('Mercury', swe.MERCURY),
    ('Jupiter', swe.JUPITER),
    ('Venus', swe.VENUS),
    ('Saturn', swe.SATURN),
    ('Rahu', swe.MEAN_NODE),  # Ketu = Rahu + 180
]

SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
    'Jyeshtha', 'Moola', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
    'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]


class EphemerisRequest(BaseModel):
    birth_date: str    # YYYY-MM-DD
    birth_time: str    # HH:MM (local time at birth place)
    lat: float
    lng: float
    ut_offset: float = 5.5  # UTC offset of birth place (IST = 5.5)


class PlanetPosition(BaseModel):
    planet: str
    longitude: float
    sign: str
    deg_in_sign: float
    nakshatra: str
    pada: int
    retrograde: bool
    speed: float


def _position_from_lon(lon: float, speed: float, name: str) -> PlanetPosition:
    lon = lon % 360
    sign_idx = int(lon / 30)
    deg_in_sign = lon % 30
    nak_idx = int(lon / (360 / 27))
    pada = int((lon % (360 / 27)) / (360 / 108)) + 1
    return PlanetPosition(
        planet=name,
        longitude=round(lon, 4),
        sign=SIGNS[sign_idx],
        deg_in_sign=round(deg_in_sign, 4),
        nakshatra=NAKSHATRAS[nak_idx],
        pada=pada,
        retrograde=speed < 0,
        speed=round(speed, 6),
    )


@router.post("")
def compute_natal_positions(req: EphemerisRequest) -> dict:
    # Set Lahiri ayanamsa per-invocation to guard against global state mutation
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    h, m = map(int, req.birth_time.split(':'))
    decimal_hour_ut = h + m / 60.0 - req.ut_offset

    parts = req.birth_date.split('-')
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

    jd = swe.julday(year, month, day, decimal_hour_ut)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    positions = []
    rahu_long = None
    rahu_speed = None

    for name, code in PLANETS:
        pos, _ = swe.calc_ut(jd, code, flags)
        lon, speed = pos[0], pos[3]
        positions.append(_position_from_lon(lon, speed, name))
        if name == 'Rahu':
            rahu_long = lon
            rahu_speed = speed

    # Ketu: opposite Rahu, moves at same rate in opposite direction
    if rahu_long is not None:
        ketu_long = rahu_long + 180
        ketu_speed = -(rahu_speed or 0.0)
        positions.append(_position_from_lon(ketu_long, ketu_speed, 'Ketu'))

    return {"jd": jd, "positions": [p.model_dump() for p in positions]}


# ── W2 dark-set wiring: POST /api/compute/ephemeris_at_t (ka_graha_sancara, GT-50) ──
#
# RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0 / RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0's
# top-priority dark-set item and the W-27 commissioning contract's designated first
# live test (per NATIVE_REVIEW_PACKET_W1/TOOL_SHAPE_DESIGN.md worked example (c) and
# platform/src/lib/retrieval/registry/service_manifest/DESIGN_KA_GRAHA_SANCARA_WIRING.md).
#
# A separate APIRouter (not `router` above, which is mounted at prefix "/ephemeris"
# for the birth-params natal-chart endpoint) so this new endpoint can be mounted at
# `/api/compute` per the design note's exact target path — mirrors the existing
# `/api/compute/transit_search` pattern (routers/transit_search.py). Reuses this same
# file's `_position_from_lon`/`PLANETS`/`SIGNS`/`NAKSHATRAS` helpers as-is (design
# note §3 item 1) rather than a second swisseph integration.
compute_router = APIRouter()

# Canonical ayanamsha_id -> swisseph SIDM_* constant. Matches the SAME 5-value
# canonical vocabulary already established elsewhere in this codebase for stored
# chart_facts ayanamsha_id (routers/jaimini.py's _VALID_AYANAMSHAS,
# TS constants.ts's DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha') — NOT the shorter
# "lahiri"/"kp"/"true_chitra_paksha" vocabularies used elsewhere in this sidecar
# (panchang_engine/ayanamsha.py, pyjhora_adapter/_ayanamsha.py,
# brahmagyan/l0_ephemeris.py) — those are pre-existing, independent naming
# conventions this endpoint does not attempt to unify (out of this wave's scope).
# "Lahiri" and "Lahiri (Chitrapaksha)" are the same ayanamsha under two names —
# India's 1955 Calendar Reform Committee value — so lahiri_chitrapaksha maps to
# swe.SIDM_LAHIRI, not a distinct constant.
_AT_T_AYANAMSHA_MAP: dict[str, int] = {
    "lahiri_chitrapaksha":        swe.SIDM_LAHIRI,
    "true_chitra":                swe.SIDM_TRUE_CITRA,
    "krishnamurti":                swe.SIDM_KRISHNAMURTI,
    "raman":                       swe.SIDM_RAMAN,
    "surya_siddhanta_classical":  swe.SIDM_SURYASIDDHANTA,
}
_AT_T_DEFAULT_AYANAMSHA = "lahiri_chitrapaksha"


class EphemerisAtTRequest(BaseModel):
    datetime_utc: str              # ISO 8601 UTC instant, e.g. 2026-07-20T12:00:00Z
    ayanamsha_id: str = _AT_T_DEFAULT_AYANAMSHA


@compute_router.post("/ephemeris_at_t")
def ephemeris_at_t(req: EphemerisAtTRequest) -> dict:
    """
    Graha longitudes at an arbitrary UTC instant (ka_graha_sancara service).
    Geocentric only — no lat/lng, no houses/lagna (those need a birth place;
    this endpoint's declared contract is graha positions only, per the MCP
    descriptor's input_schema). Sub-day precision, live swisseph compute —
    distinct from the bounded 1900-2150 daily-grain ephemeris_daily table.

    Unrecognized ayanamsha_id fails loud (422) — never silently falls back to
    tropical or to a different sidereal mode (design note §3 item 5).
    """
    if req.ayanamsha_id not in _AT_T_AYANAMSHA_MAP:
        raise HTTPException(
            status_code=422,
            detail=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] ayanamsha_id={req.ayanamsha_id!r} is not "
                f"recognized. Valid values: {sorted(_AT_T_AYANAMSHA_MAP.keys())}."
            ),
        )

    try:
        dt = datetime.fromisoformat(req.datetime_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime_utc: {exc}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)

    # Set the requested sidereal mode per-invocation to guard against global
    # swisseph state mutation (same discipline as compute_natal_positions above).
    swe.set_sid_mode(_AT_T_AYANAMSHA_MAP[req.ayanamsha_id])

    decimal_hour_ut = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, decimal_hour_ut)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    positions = []
    rahu_long = None
    rahu_speed = None

    for name, code in PLANETS:
        pos, _ = swe.calc_ut(jd, code, flags)
        lon, speed = pos[0], pos[3]
        positions.append(_position_from_lon(lon, speed, name))
        if name == 'Rahu':
            rahu_long = lon
            rahu_speed = speed

    if rahu_long is not None:
        ketu_long = rahu_long + 180
        ketu_speed = -(rahu_speed or 0.0)
        positions.append(_position_from_lon(ketu_long, ketu_speed, 'Ketu'))

    return {
        "datetime_utc": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ayanamsha_id": req.ayanamsha_id,
        "jd": jd,
        "positions": [p.model_dump() for p in positions],
    }
