"""
muhurat.py — Muhurat Finder for panchang_engine.

Scaffold only (4C-1-S2). API signatures are locked here; 4C.6 fills the bodies.
Calling code can import and wire this module without errors; scoring returns
empty/zero results until 4C.6 ships.

6-event MVP set settled 2026-05-19 (D2 decision):
  vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation

Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3 (muhurat scoring spec).
Full implementation deferred to Phase 4C.6.
"""
from datetime import date as DateType
from typing import Optional

from .types import MuhuratWindow, NatalChart


# ---------------------------------------------------------------------------
# MVP event set — locked in 4C-1-S2; 4C.6 scores all 6
# ---------------------------------------------------------------------------
EVENTS_MVP: list[str] = [
    "vivah",              # Marriage
    "griha_pravesh",      # House warming / new home entry
    "vyapara",            # Business start / commerce
    "yatra",              # Journey / travel
    "property_purchase",  # Property / vehicle purchase
    "mantra_initiation",  # Mantra diksha / initiation
]


def is_supported_event(event: str) -> bool:
    """Return True if event is in the curated MVP set (settled D2 2026-05-19)."""
    return event in EVENTS_MVP


def score_muhurat(
    date: DateType,
    lat: float,
    lon: float,
    event: str,
    native_chart: Optional[NatalChart] = None,
) -> float:
    """
    Return a score 0..100 for the given date × event combination.

    SCAFFOLD ONLY (4C-1-S2): returns 0.0 for every valid input.
    Full scoring rubric (panchang factors + dasha weighting) implemented in 4C.6.

    Signature is locked here so 4C.6 can fill the body without API churn.
    The native_chart parameter enables dasha-aware weighting when provided.

    Args:
        date: Local calendar date to score.
        lat: Latitude in decimal degrees (+N).
        lon: Longitude in decimal degrees (+E).
        event: Event key — must be in EVENTS_MVP.
        native_chart: Optional NatalChart for dasha-aware scoring. Ignored in scaffold.

    Returns:
        float — always 0.0 in scaffold.

    Raises:
        ValueError if event is not in EVENTS_MVP.
    """
    if not is_supported_event(event):
        raise ValueError(
            f"Event '{event}' not in MVP set. "
            f"Supported events: {EVENTS_MVP}"
        )
    return 0.0   # 4C.6 implements


def find_muhurat(
    event: str,
    date_from: DateType,
    date_to: DateType,
    lat: float,
    lon: float,
    native_chart: Optional[NatalChart] = None,
) -> list:
    """
    Return top auspicious windows for event in [date_from, date_to].

    SCAFFOLD ONLY (4C-1-S2): returns empty list [].
    Full implementation (day scoring, window ranking, star ratings) in 4C.6.

    Signature is locked here so 4C.6 can fill the body without API churn.

    Args:
        event: Event key — must be in EVENTS_MVP.
        date_from: Search window start (inclusive).
        date_to: Search window end (inclusive).
        lat: Latitude in decimal degrees (+N).
        lon: Longitude in decimal degrees (+E).
        native_chart: Optional NatalChart for dasha-aware scoring. Ignored in scaffold.

    Returns:
        list[MuhuratWindow] — always [] in scaffold.

    Raises:
        ValueError if event is not in EVENTS_MVP.
    """
    if not is_supported_event(event):
        raise ValueError(
            f"Event '{event}' not in MVP set. "
            f"Supported events: {EVENTS_MVP}"
        )
    return []   # 4C.6 implements
