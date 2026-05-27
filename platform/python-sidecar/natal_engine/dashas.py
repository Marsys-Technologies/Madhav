"""
dashas.py — Vimshottari dasha skeleton.

Scaffold: emits the 9-lord mahadasha sequence starting from the
Moon-nakshatra lord, with conventional Parashari period lengths and a
naive elapsed-portion calculation. Antardashas / pratyantardashas are unit 1.2.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .positions import _lon_to_nakshatra
from .schema import GrahaState

# Vimshottari standard: 120-year cycle, fixed lord order, fixed durations.
VIMSHOTTARI_ORDER: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
# Nakshatra ownership cycles Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
# repeating across the 27 nakshatras (3 cycles).
_NAK_LORD_ORDER = VIMSHOTTARI_ORDER


def _nakshatra_lord(nakshatra_id: int) -> str:
    # nakshatra_id is 1..27
    return _NAK_LORD_ORDER[(nakshatra_id - 1) % 9]


# Solar-year length used by classical Vimshottari (365.25 days)
_YEAR_DAYS = 365.25


def compute_vimshottari_mahadasha(
    moon: GrahaState, birth_dt_utc: datetime
) -> dict[str, object]:
    """Compute the Vimshottari mahadasha sequence over the 120-year cycle.

    Returns a dict matching CHART_OUTPUT_SCHEMA.dashas:
      {"system": "vimshottari", "mahadasha_sequence": [{"lord", "start_iso", "end_iso"}, ...]}
    """
    nak_id = moon.nakshatra_id  # 1..27
    nak_lord = _nakshatra_lord(nak_id)

    # Position within the moon's nakshatra (0..1).
    nak_span = 360.0 / 27.0
    pos_in_nak = (moon.longitude_deg - (nak_id - 1) * nak_span) / nak_span
    pos_in_nak = max(0.0, min(1.0, pos_in_nak))

    # Elapsed fraction of the current lord's period at birth = pos_in_nak
    first_lord_total_years = VIMSHOTTARI_YEARS[nak_lord]
    first_lord_elapsed_years = pos_in_nak * first_lord_total_years
    first_lord_remaining_years = first_lord_total_years - first_lord_elapsed_years

    # Back-compute the first MD start so birth falls inside [start, end].
    # JH classical convention: integer-year boundaries advance the CALENDAR
    # year by N (so Jupiter 1975-08-14 → 1991-08-14 = exactly 16 cal years,
    # NOT 16 * 365.25 days). The fractional first-MD ends/back-tracks via
    # day-arithmetic at _YEAR_DAYS = 365.25.
    sequence: list[dict[str, str]] = []
    md_start = birth_dt_utc - timedelta(days=first_lord_elapsed_years * _YEAR_DAYS)
    # md_end = md_start advanced by `first_lord_total_years` CALENDAR years
    md_end = _add_calendar_years(md_start, first_lord_total_years)
    sequence.append(
        {
            "lord": nak_lord,
            "start_iso": md_start.isoformat(),
            "end_iso": md_end.isoformat(),
        }
    )

    # Subsequent 8 lords in fixed order — calendar-year arithmetic
    idx = VIMSHOTTARI_ORDER.index(nak_lord)
    cursor = md_end
    for k in range(1, 9):
        lord = VIMSHOTTARI_ORDER[(idx + k) % 9]
        years = VIMSHOTTARI_YEARS[lord]
        start = cursor
        end = _add_calendar_years(start, years)
        sequence.append(
            {
                "lord": lord,
                "start_iso": start.isoformat(),
                "end_iso": end.isoformat(),
            }
        )
        cursor = end

    return {"system": "vimshottari", "mahadasha_sequence": sequence}


def _add_calendar_years(dt: datetime, years: int) -> datetime:
    """Add integer calendar years to a datetime, preserving month/day/time.

    Handles Feb-29 by falling back to Feb-28 in the target year (JH-equivalent
    behavior for the rare leap-day case). All other dates are exact.
    """
    new_year = dt.year + int(years)
    try:
        return dt.replace(year=new_year)
    except ValueError:
        # Feb 29 → Feb 28 in non-leap target
        return dt.replace(year=new_year, day=28)
