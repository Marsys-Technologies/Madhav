"""
ka_graha_sancara — Ephemeris-at-T service (L3 Kāla K1).

Public API:
    from services.ka_graha_sancara import get_ephemeris

    result = get_ephemeris(
        dt=datetime(1984, 2, 5, 10, 43, tzinfo=IST),
        ayanamsha='lahiri',
        db_conn=conn,   # optional legacy compatibility argument
    )

The public facade uses the shared Swiss instant path and declares its mean-node
convention, JD/time scale, flags, ayanāṃśa and coverage. Missing backend data
returns a typed null with no grahas or fabricated ayanāṃśa value. Supply one
kala_core.sky.EphemerisCache via _cache to reuse computations across requests;
the key includes the exact JD and convention, never a rounded calendar day.
The engine module retains the historical paths as comparison APIs.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from services.kala_core.ayanamsha import CANONICAL_AYANAMSHA
from services.kala_core.sky import EphemerisCache, SkyConvention, ephemeris_at as sky_ephemeris_at
from services.kala_core.sky.ephemeris import EPHE_FLAGS, EPHE_FLAG_NAMES, SWISS_INSTANT, TIME_SCALE

from .engine import EphemerisResult, GrahaState, NAKSHATRAS, NAK_SIZE_DEG, SIGNS, SIGN_SIZE_DEG

_JD_UNIX_EPOCH = 2440587.5
_IST = timezone(timedelta(hours=5, minutes=30))


def _utc_jd(instant: datetime) -> float:
    """Convert the legacy datetime input to the shared sky API's UT JD."""
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=_IST)
    return instant.astimezone(timezone.utc).timestamp() / 86400.0 + _JD_UNIX_EPOCH


def get_ephemeris(
    dt: datetime,
    ayanamsha: str = "lahiri",
    db_conn: Any = None,
    *,
    force_live: bool = False,
    _cache: EphemerisCache | None = None,
) -> EphemerisResult:
    """Compatibility facade over the instant-grain `kala_core.sky` contract.

    The legacy response dataclasses remain intact for existing callers.  Their
    values now come from the layer's single Swiss-backed sky door; an uncovered
    instant returns an empty, explicitly unavailable legacy envelope rather
    than falling back to Moshier or a day-grade stored number.
    """
    del db_conn, force_live
    convention_id = CANONICAL_AYANAMSHA if ayanamsha == "lahiri" else ayanamsha
    convention = SkyConvention(ayanamsha_id=convention_id)
    jd = _utc_jd(dt)
    cache = _cache if _cache is not None else EphemerisCache()
    answer = sky_ephemeris_at(jd, convention, cache=cache)
    if not answer.available:
        return EphemerisResult(
            dt, ayanamsha, "information_unavailable", {}, jd=jd, time_scale=TIME_SCALE,
            path=SWISS_INSTANT, backend=answer.coverage.backend, flags=EPHE_FLAGS,
            flag_names=EPHE_FLAG_NAMES, node_model=convention.node_model,
            ayanamsha_id=convention.ayanamsha_id, convention_id=answer.coverage.convention_id,
            coverage=answer.coverage, null_reason=answer.null_reason,
        )

    instant = answer.values[0]
    grahas: dict[str, GrahaState] = {}
    for position in instant.positions:
        longitude = position.longitude_deg
        sign_idx = int(longitude // SIGN_SIZE_DEG) % 12
        nakshatra_idx = int(longitude // NAK_SIZE_DEG) % 27
        grahas[position.body] = GrahaState(
            name=position.body,
            sidereal_lon_deg=longitude,
            sign=SIGNS[sign_idx],
            sign_idx=sign_idx,
            nakshatra=NAKSHATRAS[nakshatra_idx],
            nakshatra_idx=nakshatra_idx,
            degrees_in_sign=longitude % SIGN_SIZE_DEG,
            degrees_in_nakshatra=longitude % NAK_SIZE_DEG,
            speed_dps=position.speed_deg_per_day,
            is_retrograde=position.speed_deg_per_day < 0,
            source=instant.backend,
        )
    return EphemerisResult(
        dt, ayanamsha, instant.backend, grahas, jd=instant.jd, time_scale=instant.time_scale,
        path=instant.path, backend=instant.backend, flags=instant.flags,
        flag_names=instant.flag_names, node_model=instant.node_model,
        ayanamsha_id=instant.ayanamsha_id, ayanamsha_deg=instant.ayanamsha_deg,
        convention_id=instant.convention_id, coverage=answer.coverage,
        null_reason=answer.null_reason,
    )

__all__ = [
    "get_ephemeris",
    "EphemerisResult",
    "GrahaState",
    "SkyConvention",
    "sky_ephemeris_at",
]
