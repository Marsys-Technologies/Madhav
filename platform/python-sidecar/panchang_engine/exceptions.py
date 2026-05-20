"""
exceptions.py — Exception hierarchy for panchang_engine.
All exceptions inherit from PanchangEngineError for easy catch-all handling.
"""


class PanchangEngineError(Exception):
    """Root exception for all panchang_engine errors."""


class AyanamshaError(PanchangEngineError):
    """Invalid ayanamsha mode or computation failure."""


class OutOfRangeError(PanchangEngineError):
    """Date/location outside computable range (polar latitudes, ephemeris bounds)."""


class ValidationError(PanchangEngineError):
    """Input validation failure (bad lat/lon/date/param)."""
