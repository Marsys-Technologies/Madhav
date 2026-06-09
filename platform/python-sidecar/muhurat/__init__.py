"""
muhurat — Muhurat Finder and scoring package.

Deterministic muhurat scoring against panchang_engine output.
Zero LLM. Scoring/judgement lives here; panchang_engine holds only
the deterministic core (angas, timings, planets).

Public surface:
  find_muhurat(event, date_from, date_to, lat, lon, tz_offset_minutes, ...) → list[MuhuratWindow]
  score_muhurat(panchang, event, ...) → float (0..100)
  is_supported_event(event) → bool
  EVENTS_MVP — list of supported event keys
"""

from .finder import (
    find_muhurat,
    find_muhurat_from_cache,
    score_muhurat,
    is_supported_event,
    EVENTS_MVP,
)

__all__ = [
    "find_muhurat",
    "find_muhurat_from_cache",
    "score_muhurat",
    "is_supported_event",
    "EVENTS_MVP",
]
