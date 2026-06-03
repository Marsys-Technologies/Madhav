"""
brahmagyan.almanac — Daily Almanac (0.8 · brahmagyan.almanac)
Brahmagyan / Foundation Layer — asset BG-0-8

Public API
----------
query(date_range, location) → list[AlmanacDay]
    Main tool interface. Computes (or retrieves from cache) the full
    Panchanga + day-quality windows for each date in the requested range
    at the given location.

Design decisions
----------------
- Built directly on top of the existing panchang_engine (Phase 4C engine,
  verified at 30/30 Drik parity, FORENSIC spot-check PASS 5/5 on 1984-02-05).
- Location cache: lat/lon normalized to nearest 0.1° before lookup; keyed as
  "lat_lon_tzname" so distinct IANA TZs at the same coordinates are separate
  entries (handles half-hour and non-integer UTC offsets correctly via
  zoneinfo/backports.zoneinfo).
- In-process LRU cache (maxsize=512 location×date combos) on top of the
  per-date computation; no DB dependency (Brahmagyan L0 is self-contained).
- Thread-safe: the panchang_engine and swisseph are effectively stateless per
  call (ayanamsha is set inside each call); functools.lru_cache uses an
  internal lock.
- IANA DST: caller provides an IANA timezone name (e.g. "Asia/Kolkata");
  the almanac resolves the UTC offset for each specific date in the range so
  DST transitions within the range are handled correctly.

References
----------
- L0 contract: 00_ARCHITECTURE/CONDUCTOR/brahma/L0_CONTRACT_REGISTRY_SEED_v1_0.md §C 0.8
- Engine: platform/python-sidecar/panchang_engine/__init__.py (v1.0.0-S3)
- FORENSIC benchmark: 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
"""
from .core import query, AlmanacDay, AlmanacLocation, AlmanacDateRange
from .cache import get_cache_stats, clear_cache

__all__ = [
    "query",
    "AlmanacDay",
    "AlmanacLocation",
    "AlmanacDateRange",
    "get_cache_stats",
    "clear_cache",
]
