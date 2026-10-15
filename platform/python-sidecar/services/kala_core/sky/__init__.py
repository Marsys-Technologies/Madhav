"""kala_core.sky — the layer's one door to sky geometry (plan §3.2 `sky/`).

Chart-free: ephemeris at an instant (two read paths, one memo cache keyed by
JD and convention), boundary events with canonical identity and occurrence
ordinals, directed dṛṣṭi geometry, the arc-index → Swiss contact solver with
Swiss-refined stations, and coverage on every answer. The Gochara kernel's
pure modules are imported in place (R-1); nothing here moves or edits them.
"""
from .contacts import Contact, Station, solve_contacts, stations
from .coverage import SkyCoverage, SkyResult, coverage_of, unavailable
from .ephemeris import (
    BodyPosition, CivilTime, DailyRow, EphemerisAnswer, EphemerisCache,
    GeoLocation, LocalAnswer, SkyConvention, ephemeris_at, ephemeris_from_row,
    lagna_at, row_jd,
)
from .events import SkyEvent, boundary_events
from .geometry import aspected_points, aspects, contact_level, drishti_angles
from .identity import event_object, kernel_body, merge_events, occurrence_id

__all__ = [
    "BodyPosition", "CivilTime", "Contact", "DailyRow", "EphemerisAnswer",
    "EphemerisCache", "GeoLocation", "LocalAnswer", "SkyConvention", "SkyCoverage",
    "SkyEvent", "SkyResult", "Station", "aspected_points", "aspects",
    "boundary_events", "contact_level", "coverage_of", "drishti_angles",
    "ephemeris_at", "ephemeris_from_row", "event_object", "kernel_body",
    "lagna_at", "merge_events", "occurrence_id", "row_jd", "solve_contacts",
    "stations", "unavailable",
]
