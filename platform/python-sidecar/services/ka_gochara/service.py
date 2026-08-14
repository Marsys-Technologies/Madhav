"""
GocharaTransitService — wraps transit-search functions for use by routers.

MR-09 NAMING NOTE: This module lives at services/ka_gochara/service.py and
its primary class is GocharaTransitService (renamed from KaGocharaService at
MR-09 to resolve the naming collision with the ka_gochara materializer writer
at pipeline/orchestrator/writers/ka_gochara.py).

The two things that share the "ka_gochara" prefix are DISTINCT:
  - This module (GocharaTransitService): a LIVE TRANSIT COMPUTATION ENGINE.
    Wraps Swiss-Ephemeris functions (pipeline.transit_search) to search for
    aspect, ingress, conjunction, station, and other transit events on demand.
    No DB table; no @register; no WriterBase.  Asset kind = 'service'.
  - pipeline/orchestrator/writers/ka_gochara.py (KaGocharaWriter): a PER-CHART
    DATA MATERIALIZER.  @register('ka_gochara') WriterBase subclass that joins
    bg_gochara_arcs against a chart's gochara_resonance_map and writes
    generation='2.0' rows into kala_gochara_windows_v2.

KaGocharaService is retained as a backward-compat alias (see bottom of module)
so existing callers (ka_sangam.py and tests) continue to work without change.

Thin orchestration layer over pipeline.transit_search. All numeric computation
happens in the pipeline module; this class handles dependency injection (swe).
"""
from __future__ import annotations

import logging

from pipeline.transit_search import (
    TransitEvent,
    find_aspect_events,
    find_conjunction_events,
    find_ingress_events,
    find_return_events,
    find_station_events,
    find_eclipse_proximity_events,
    find_multi_planet_confluence_events,
    find_transit_to_transit_events,
    search_long_horizon,
)

logger = logging.getLogger(__name__)

# J2000.0 epoch as a fixed reference point for the health probe computation.
# Using a well-known epoch (2000-01-01 12:00 UT) means any correct swe
# implementation returns a deterministic result — this is a connectivity /
# smoke test for the ephemeris, not an astronomical assertion.
_HEALTH_PROBE_JD = 2451545.0  # J2000.0


class GocharaTransitService:
    """Live transit computation engine wrapping Swiss-Ephemeris functions.

    MR-09: renamed from KaGocharaService to avoid ambiguity with the
    'ka_gochara' materializer writer (pipeline/orchestrator/writers/ka_gochara.py).
    KaGocharaService is kept as a backward-compat alias at the bottom of this
    module.
    """

    def __init__(self, swe):
        self.swe = swe

    def find_aspects(
        self,
        transit_planet: str,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_aspect_events(self.swe, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)

    def find_conjunctions(
        self,
        planet_a: str,
        planet_b: str,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_conjunction_events(self.swe, planet_a, planet_b, orb, start_jd, end_jd)

    def find_ingresses(
        self,
        planet: str,
        target_sign: str,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_ingress_events(self.swe, planet, target_sign, start_jd, end_jd)

    def find_returns(
        self,
        planet: str,
        natal_lon: float,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_return_events(self.swe, planet, natal_lon, orb, start_jd, end_jd)

    def find_stations(
        self,
        planet: str,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_station_events(self.swe, planet, start_jd, end_jd)

    def find_eclipse_proximity(
        self,
        node_planet: str,
        luminary: str,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_eclipse_proximity_events(self.swe, node_planet, luminary, orb, start_jd, end_jd)

    def find_multi_planet_confluence(
        self,
        planets: list,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_multi_planet_confluence_events(
            self.swe, planets, target_lon, aspect_degrees, orb, start_jd, end_jd
        )

    def find_transit_to_transit(
        self,
        planet_a: str,
        planet_b: str,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_transit_to_transit_events(
            self.swe, planet_a, planet_b, aspect_degrees, orb, start_jd, end_jd
        )

    def long_horizon_search(
        self,
        transit_planet: str,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
        region_tile_days: int = 365,
    ) -> list[TransitEvent]:
        return search_long_horizon(
            self.swe, transit_planet, target_lon, aspect_degrees, orb,
            start_jd, end_jd, region_tile_days,
        )

    def service_health(self) -> dict:
        """Transit service connectivity probe (MR-09 health check restore).

        The W6.4 migration retired the old ka_gochara self-test DB row but
        left no replacement.  This method is the replacement: it runs a
        deterministic, side-effect-free Julian Day computation against the
        bound swisseph instance to verify the ephemeris engine is live.

        Returns a dict with:
          "status"  — "ok" if the probe computation succeeded, "error" otherwise.
          "detail"  — human-readable description of what was checked / what failed.
          "probe"   — the test computation type (always "julday_j2000").
          "result"  — the computed JD value on success, None on error.

        This is NOT a DB self-test row (those were retired by design).
        It is a pure live-compute connectivity check on the swe engine.
        """
        try:
            # J2000.0: 2000-01-01 12:00 UT
            computed = self.swe.julday(2000, 1, 1, 12.0)
            # Sanity: J2000.0 must be within 1.0 JD of the known value
            if abs(computed - _HEALTH_PROBE_JD) > 1.0:
                return {
                    "status": "error",
                    "detail": (
                        f"julday(2000-01-01 12h) returned {computed!r}; "
                        f"expected ~{_HEALTH_PROBE_JD} (J2000.0).  "
                        "Ephemeris engine may be mis-configured."
                    ),
                    "probe": "julday_j2000",
                    "result": computed,
                }
            return {
                "status": "ok",
                "detail": (
                    f"julday(2000-01-01 12h) = {computed!r} "
                    f"(expected ~{_HEALTH_PROBE_JD}).  Ephemeris engine live."
                ),
                "probe": "julday_j2000",
                "result": computed,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("[GocharaTransitService.service_health] probe failed: %s", exc)
            return {
                "status": "error",
                "detail": f"julday probe raised: {exc}",
                "probe": "julday_j2000",
                "result": None,
            }


# ---------------------------------------------------------------------------
# Backward-compat alias (MR-09)
# ---------------------------------------------------------------------------
# ka_sangam.py and existing tests import by this name.  Keeping the alias
# here means no change is needed in those callers.  The PRIMARY class is
# GocharaTransitService; this alias exists for continuity only.
KaGocharaService = GocharaTransitService


__all__ = ["GocharaTransitService", "KaGocharaService"]
