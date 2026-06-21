"""
KaGocharaService — wraps transit-search functions for use by routers.

Thin orchestration layer over pipeline.transit_search. All numeric computation
happens in the pipeline module; this class handles dependency injection (swe).
"""
from __future__ import annotations

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


class KaGocharaService:
    """Wraps transit-search functions with a bound swisseph module."""

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


__all__ = ["KaGocharaService"]
