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

    sequence: list[dict[str, str]] = []
    start = birth_dt_utc
    end = start + timedelta(days=first_lord_remaining_years * _YEAR_DAYS)
    sequence.append(
        {
            "lord": nak_lord,
            "start_iso": start.isoformat(),
            "end_iso": end.isoformat(),
        }
    )

    # Subsequent 8 lords in fixed order
    idx = VIMSHOTTARI_ORDER.index(nak_lord)
    for k in range(1, 9):
        lord = VIMSHOTTARI_ORDER[(idx + k) % 9]
        years = VIMSHOTTARI_YEARS[lord]
        start = end
        end = start + timedelta(days=years * _YEAR_DAYS)
        sequence.append(
            {
                "lord": lord,
                "start_iso": start.isoformat(),
                "end_iso": end.isoformat(),
            }
        )

    return {"system": "vimshottari", "mahadasha_sequence": sequence}
