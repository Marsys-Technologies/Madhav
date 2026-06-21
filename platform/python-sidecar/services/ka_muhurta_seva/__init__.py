"""
services/ka_muhurta_seva — Panchāṅga-Muhūrta Service (L3 Kāla asset ka_muhurta_seva)

Public API
----------
  score(date, location, event, native_chart=None) -> float
      Score a single day for a given event using the full panchang_engine + muhurat
      scorer. Returns 0.0..100.0. Knockout returns 0.0.

  find_windows(event, window, location, native_chart=None, top_n=10) -> list[MuhuratWindow]
      Find the top-N auspicious windows for an event within a date range.

Contract
--------
  - `location` is REQUIRED for both calls. Passing None raises ValueError immediately.
  - `location` must be a dict with keys: lat (float), lon (float), tz_offset_minutes (int).
  - `date` is a datetime.date.
  - `window` is a dict with keys: date_from (datetime.date), date_to (datetime.date).
  - `native_chart` is an optional panchang_engine.NatalChart (for Tāra Bala native overlay).
    To activate Tāra Bala for the native Abhisek Mohanty, construct:
        NatalChart(birth_nakshatra_id=25, birth_lagna_sign_id=1, moon_sign_id=11,
                   active_dasha_lord="Jupiter")
    (birth_nakshatra_id=25 = Purva Bhadrapada; 1-indexed Ashwini=1..Revati=27)

Layer: L3 Kāla (ka_muhurta_seva)
Asset type: service (no DB rows; service_health written to asset_registry)
Depends on: ka_graha_sancara (planned)
"""

from .service import KaMuhurtaSevaService, score, find_windows

__all__ = [
    "KaMuhurtaSevaService",
    "score",
    "find_windows",
]
