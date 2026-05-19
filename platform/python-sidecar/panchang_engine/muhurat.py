"""
muhurat.py — Muhurat Finder for panchang_engine.
STUB this session (4C-1-S1). Implemented in 4C.6 phase.
"""
from .exceptions import PanchangEngineError


def find_muhurat_windows(event: str, date_from, date_to,
                         lat: float, lon: float,
                         native_chart=None) -> list:
    """
    Find auspicious windows for the given event within the date range.
    STUB — raises NotImplementedError. Implemented in 4C.6.

    In 4C.6 this will:
    - Score each day's auspicious timings against event requirements
    - Apply dasha-lord weighting from native_chart
    - Return ranked MuhuratWindow list with star_rating + score breakdown

    Args:
        event: str — e.g. "vivaha", "griha_pravesh", "business_start"
        date_from: datetime.date
        date_to: datetime.date
        lat, lon: float — location decimal degrees
        native_chart: NatalChart | None — for dasha-aware scoring

    Raises:
        NotImplementedError — always in this session
    """
    raise NotImplementedError(
        "muhurat.find_muhurat_windows is implemented in 4C.6. "
        f"Event='{event}', window={date_from}..{date_to}."
    )
