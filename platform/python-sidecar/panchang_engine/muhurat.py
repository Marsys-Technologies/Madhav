"""
panchang_engine/muhurat.py — BACKWARD-COMPAT SHIM (P2 re-arch, 2026-06-09).

Implementation moved to muhurat/finder.py (sibling package).
This shim re-exports the full public surface so existing imports continue to work:
    from panchang_engine.muhurat import find_muhurat, score_muhurat, ...
"""
from muhurat.finder import (
    find_muhurat,
    find_muhurat_from_cache,
    score_muhurat,
    is_supported_event,
    EVENTS_MVP,
    _score_to_stars,
    _in_inauspicious,
    _score_breakdown,
    _CachedAnga,
    _CachedTiming,
    _CachedPlanet,
    _CachedPanchang,
    _parse_dt,
)

__all__ = [
    "find_muhurat",
    "find_muhurat_from_cache",
    "score_muhurat",
    "is_supported_event",
    "EVENTS_MVP",
    "_score_to_stars",
    "_in_inauspicious",
    "_score_breakdown",
    "_CachedAnga",
    "_CachedTiming",
    "_CachedPlanet",
    "_CachedPanchang",
    "_parse_dt",
]
