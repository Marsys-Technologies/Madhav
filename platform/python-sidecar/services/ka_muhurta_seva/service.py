"""
service.py — KaMuhurtaSevaService: panchāṅga/muhūrta service for L3 Kāla.

This module is the thin ka_* service wrapper around the existing muhurat/ engine.
It enforces the L3 service contract:
  - (date, location) are REQUIRED — no defaults, never silently assumed
  - Tāra Bala is live when native_chart.birth_nakshatra_id is supplied
  - Two public module-level functions (score, find_windows) expose the service
    without requiring explicit instantiation

DO NOT register this file as an asset_id — it is a service module.
The WriterBase subclass (writer.py) handles orchestrator registration.

Layer: L3 Kāla
Asset: ka_muhurta_seva
Source: L3_KALA_CAMPAIGN_PLAN_v0_8.md §K1
"""
from __future__ import annotations

import logging
from datetime import date as DateType
from typing import Optional

from panchang_engine.types import NatalChart, MuhuratWindow

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Native constants (Purva Bhadrapada = nakshatra id 25, 1-indexed)
# ---------------------------------------------------------------------------
NATIVE_BIRTH_NAKSHATRA_ID: int = 25   # Purva Bhadrapada (FORENSIC anchor)
NATIVE_BIRTH_LAGNA_SIGN_ID: int = 1   # Mesha (Aries) — all 5 ayanamshas
NATIVE_MOON_SIGN_ID: int = 11         # Kumbha — Purva Bhadrapada pada 1..3 falls in Kumbha
NATIVE_ACTIVE_DASHA_LORD: str = "Jupiter"  # current period; update as dasha changes


def _validate_location(location) -> None:
    """
    Raise ValueError if location is None or missing required keys.

    Location is ALWAYS required in ka_muhurta_seva. There is no Bhubaneswar default.
    The caller must supply explicit coordinates for every call.
    """
    if location is None:
        raise ValueError(
            "ka_muhurta_seva: location is required (got None). "
            "Provide: {'lat': float, 'lon': float, 'tz_offset_minutes': int}"
        )
    missing = [k for k in ("lat", "lon", "tz_offset_minutes") if k not in location]
    if missing:
        raise ValueError(
            f"ka_muhurta_seva: location is missing required keys: {missing}. "
            f"Provide: {{'lat': float, 'lon': float, 'tz_offset_minutes': int}}"
        )
    lat = location["lat"]
    lon = location["lon"]
    if not (-90 <= lat <= 90):
        raise ValueError(f"ka_muhurta_seva: location lat out of range: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"ka_muhurta_seva: location lon out of range: {lon}")


class KaMuhurtaSevaService:
    """
    Panchāṅga-Muhūrta Service — L3 Kāla layer service asset.

    Wraps muhurat.finder (score_muhurat / find_muhurat) with the L3 contract:
      - location is always required
      - Tāra Bala is live when native_chart carries birth_nakshatra_id
      - all scoring is deterministic (no LLM, no generative path)

    Usage:
        svc = KaMuhurtaSevaService()
        score = svc.score(date(2026, 6, 21), location={"lat": 20.30, "lon": 85.82, "tz_offset_minutes": 330}, event="vivah")
        windows = svc.find_windows("vivah", window={"date_from": ..., "date_to": ...}, location={...})
    """

    def score(
        self,
        date: DateType,
        location: dict,
        event: str,
        native_chart: Optional[NatalChart] = None,
        weights: Optional[dict] = None,
    ) -> float:
        """
        Score a single day for a given event.

        Args:
            date: The local calendar date to score.
            location: REQUIRED dict with keys lat, lon, tz_offset_minutes.
            event: One of the supported EVENTS_MVP keys.
            native_chart: Optional NatalChart for Tāra Bala native overlay.
                          When birth_nakshatra_id=25 (Purva Bhadrapada), the native
                          overlay is active and will produce a real Tāra Bala score
                          instead of being skipped (the "un-floor" contract).
            weights: Optional custom weight dict (for testing / overrides). If None,
                     the per-event YAML weights are used.

        Returns:
            float in 0.0..100.0. Knockout case (compound inauspicious) returns 0.0.

        Raises:
            ValueError: if location is None, missing keys, or lat/lon out of range.
            ValueError: if event is not in EVENTS_MVP.
        """
        _validate_location(location)

        from panchang_engine import compute_panchang
        from muhurat.finder import score_muhurat

        panchang = compute_panchang(
            date,
            location["lat"],
            location["lon"],
            location["tz_offset_minutes"],
        )

        return score_muhurat(panchang, event, weights=weights, native_chart=native_chart)

    def find_windows(
        self,
        event: str,
        window: dict,
        location: dict,
        native_chart: Optional[NatalChart] = None,
        weights: Optional[dict] = None,
        top_n: int = 10,
    ) -> list:
        """
        Find the top-N auspicious windows for an event within a date range.

        Args:
            event: One of the supported EVENTS_MVP keys.
            window: REQUIRED dict with keys date_from (datetime.date) and date_to (datetime.date).
            location: REQUIRED dict with keys lat, lon, tz_offset_minutes.
            native_chart: Optional NatalChart for Tāra Bala native overlay.
            weights: Optional custom weight dict.
            top_n: Number of top-scoring windows to return (default 10).

        Returns:
            list[MuhuratWindow] sorted by score descending, length <= top_n.

        Raises:
            ValueError: if location is None, missing keys, or lat/lon out of range.
            ValueError: if event is not in EVENTS_MVP.
            ValueError: if window is missing date_from / date_to, or date_from > date_to.
        """
        _validate_location(location)

        if window is None:
            raise ValueError("ka_muhurta_seva: window is required (got None).")
        missing_w = [k for k in ("date_from", "date_to") if k not in window]
        if missing_w:
            raise ValueError(f"ka_muhurta_seva: window is missing required keys: {missing_w}.")

        from muhurat.finder import find_muhurat

        return find_muhurat(
            event=event,
            date_from=window["date_from"],
            date_to=window["date_to"],
            lat=location["lat"],
            lon=location["lon"],
            tz_offset_minutes=location["tz_offset_minutes"],
            native_chart=native_chart,
            weights=weights,
            top_n=top_n,
        )


# ---------------------------------------------------------------------------
# Module-level convenience functions (primary public surface)
# ---------------------------------------------------------------------------
_svc = KaMuhurtaSevaService()


def score(
    date: DateType,
    location: dict,
    event: str,
    native_chart: Optional[NatalChart] = None,
    weights: Optional[dict] = None,
) -> float:
    """
    Module-level score() — delegates to KaMuhurtaSevaService.score().

    location is REQUIRED — passing None raises ValueError.
    """
    return _svc.score(date, location, event, native_chart=native_chart, weights=weights)


def find_windows(
    event: str,
    window: dict,
    location: dict,
    native_chart: Optional[NatalChart] = None,
    weights: Optional[dict] = None,
    top_n: int = 10,
) -> list:
    """
    Module-level find_windows() — delegates to KaMuhurtaSevaService.find_windows().

    location is REQUIRED — passing None raises ValueError.
    """
    return _svc.find_windows(
        event, window, location,
        native_chart=native_chart,
        weights=weights,
        top_n=top_n,
    )
