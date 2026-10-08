"""
ka_graha_sancara — Ephemeris-at-T service (L3 Kāla K1).

Public API:
    from services.ka_graha_sancara import get_ephemeris

    result = get_ephemeris(
        dt=datetime(1984, 2, 5, 10, 43, tzinfo=IST),
        ayanamsha='lahiri',
        db_conn=conn,   # optional; enables bg_ephemeris read path
    )

The service returns per-graha sidereal positions, speeds, retrograde flags, sign,
nakshatra, and an applying/separating helper.  Internally it maintains a per-call
memo keyed on (T_rounded, ayanamsha) — repeated queries for the same (T, ayanamsha)
within one call are served from cache without a second swisseph computation.

Two read paths (mandatory per L3 brief):
  1. Within bg_ephemeris range (1900-01-01 → 2150-12-31) + day-resolution:
       Read stored tropical_longitude + speed_dps from ephemeris_daily,
       then apply ayanamsha derivation via brahmagyan.l0_ephemeris.derive_sidereal.
       No swisseph call.
  2. Out-of-range date OR intra-day sub-day precision requested:
       Delegate to compute_transits.get_transit_states (pyswisseph + Moshier).

TRUE_NODE everywhere — Rahu uses swe.TRUE_NODE (swe_id=11); Ketu = Rahu + 180.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from services.kala_core.ayanamsha import CANONICAL_AYANAMSHA
from services.kala_core.sky import SkyConvention, ephemeris_at as sky_ephemeris_at

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
    _cache: Any = None,
) -> EphemerisResult:
    """Compatibility facade over the instant-grain `kala_core.sky` contract.

    The legacy response dataclasses remain intact for existing callers.  Their
    values now come from the layer's single Swiss-backed sky door; an uncovered
    instant returns an empty, explicitly unavailable legacy envelope rather
    than falling back to Moshier or a day-grade stored number.
    """
    del db_conn, force_live, _cache
    convention_id = CANONICAL_AYANAMSHA if ayanamsha == "lahiri" else ayanamsha
    convention = SkyConvention(ayanamsha_id=convention_id)
    answer = sky_ephemeris_at(_utc_jd(dt), convention)
    if not answer.available:
        return EphemerisResult(dt, ayanamsha, "information_unavailable", {})

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
    return EphemerisResult(dt, ayanamsha, instant.backend, grahas)

__all__ = [
    "get_ephemeris",
    "EphemerisResult",
    "GrahaState",
    "SkyConvention",
    "sky_ephemeris_at",
]
