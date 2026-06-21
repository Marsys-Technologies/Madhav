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
from .engine import get_ephemeris, EphemerisResult, GrahaState

__all__ = ["get_ephemeris", "EphemerisResult", "GrahaState"]
