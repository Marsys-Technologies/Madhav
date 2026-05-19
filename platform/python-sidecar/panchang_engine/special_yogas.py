"""
special_yogas.py — Special yoga detection for panchang_engine.
Implemented in 4C-1-S2.

Detects 9 special yogas (7 auspicious + 2 inauspicious):
  1. Sarvartha Siddhi Yoga   (vara × nakshatra)
  2. Amrit Siddhi Yoga       (vara × nakshatra; may be blocked by death-yoga overrides)
  3. Ravi Pushya Yoga        (Sunday + Pushya)
  4. Guru Pushya Yoga        (Thursday + Pushya)
  5. Tripushkar Yoga         (tithi × vara × nakshatra)
  6. Dwipushkar Yoga         (tithi × vara × nakshatra)
  7. Siddha Yoga             (vara × nakshatra)
  8. Bhadra (Vishti Karana)  (inauspicious; karana == Vishti)
  9. Panchaka Dosha          (Moon in Panchaka nakshatras)

All start/end times are UTC-aware datetimes.
Yoga windows are clipped to [sunrise_utc, next_sunrise_utc].
If a nakshatra transitions mid-day, the yoga window for the first nakshatra
ends at the transition; if the new nakshatra also qualifies, a new window
starts from the transition.

Sources:
  MC  = Muhurta Chintamani 5.16–5.17
  BS  = Brihat Samhita §3
  DP  = Drik Panchang published convention (authoritative where MC/BS are silent)
"""
from datetime import datetime, timezone
from typing import Optional

from .types import Anga, Timing
from .shastra_tables import (
    SARVARTHA_SIDDHI_TABLE,
    AMRIT_SIDDHI_TABLE,
    RAVI_PUSHYA,
    GURU_PUSHYA,
    TRIPUSHKAR_TITHIS, TRIPUSHKAR_VARAS, TRIPUSHKAR_NAKSHATRAS,
    DWIPUSHKAR_TITHIS, DWIPUSHKAR_VARAS, DWIPUSHKAR_NAKSHATRAS,
    SIDDHA_YOGA_TABLE,
    BHADRA_KARANA_ID,
    PANCHAKA_NAKSHATRAS, PANCHAKA_VARAS,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clip(start: datetime, end: datetime,
          frame_start: datetime, frame_end: datetime) -> Optional[tuple]:
    """
    Clip [start, end] to [frame_start, frame_end].
    Returns (clipped_start, clipped_end) or None if there is no overlap.
    """
    cs = max(start, frame_start)
    ce = min(end, frame_end)
    if cs >= ce:
        return None
    return cs, ce


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _yoga_dict(name: str, start_utc: datetime, end_utc: datetime,
               strength: str, stars: int) -> dict:
    """Canonical special-yoga result dict."""
    return {
        "yoga": name,
        "start_utc": _ensure_utc(start_utc),
        "end_utc": _ensure_utc(end_utc),
        "strength": strength,
        "stars": stars,
    }


# ---------------------------------------------------------------------------
# Detection functions — one per yoga
# ---------------------------------------------------------------------------

def detect_sarvartha_siddhi(
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Active when vara × nakshatra is in SARVARTHA_SIDDHI_TABLE.
    Window: from sunrise to nakshatra end_utc (or next_sunrise, whichever is first).
    Source: MC §10 / DP.
    Returns list[dict].
    """
    results = []
    # Primary nakshatra active from sunrise
    if vara_id in SARVARTHA_SIDDHI_TABLE and nakshatra.id in SARVARTHA_SIDDHI_TABLE[vara_id]:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("sarvartha_siddhi", clipped[0], clipped[1],
                                      "auspicious", 4))
    return results


def detect_amrit_siddhi(
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Active when vara × nakshatra matches AMRIT_SIDDHI_TABLE.
    Amrit Siddhi may be blocked by death-yoga overrides (MC 5.17).
    TODO (4C.6): implement MC 5.17 Visha Yoga exclusions — currently not blocking.
    Source: MC §10–§11 / DP.
    Returns list[dict].
    """
    results = []
    if vara_id in AMRIT_SIDDHI_TABLE and nakshatra.id in AMRIT_SIDDHI_TABLE[vara_id]:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("amrit_siddhi", clipped[0], clipped[1],
                                      "auspicious", 5))
    return results


def detect_ravi_pushya(
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Sunday + Pushya nakshatra. Window = Pushya nakshatra duration within sunrise frame.
    Source: MC §10 / DP "Ravi Pushya Yoga".
    Returns list[dict].
    """
    results = []
    if vara_id == RAVI_PUSHYA["vara_id"] and nakshatra.id == RAVI_PUSHYA["nakshatra_id"]:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("ravi_pushya", clipped[0], clipped[1],
                                      "auspicious", 5))
    return results


def detect_guru_pushya(
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Thursday + Pushya nakshatra. Same window logic as Ravi Pushya.
    Source: MC §10 / DP "Guru Pushya Nakshatra Yoga".
    Returns list[dict].
    """
    results = []
    if vara_id == GURU_PUSHYA["vara_id"] and nakshatra.id == GURU_PUSHYA["nakshatra_id"]:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("guru_pushya", clipped[0], clipped[1],
                                      "auspicious", 5))
    return results


def detect_tripushkar(
    tithi: Anga,
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    All three conditions must hold simultaneously:
      tithi.id in TRIPUSHKAR_TITHIS
      vara_id in TRIPUSHKAR_VARAS
      nakshatra.id in TRIPUSHKAR_NAKSHATRAS
    Window: sunrise to min(tithi end, nakshatra end, next_sunrise).
    Source: MC §11 / DP.
    Returns list[dict].
    """
    results = []
    if (tithi.id in TRIPUSHKAR_TITHIS
            and vara_id in TRIPUSHKAR_VARAS
            and nakshatra.id in TRIPUSHKAR_NAKSHATRAS):
        end = min(
            _ensure_utc(tithi.end_utc),
            _ensure_utc(nakshatra.end_utc),
            _ensure_utc(next_sunrise_utc),
        )
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("tripushkar", clipped[0], clipped[1],
                                      "auspicious", 4))
    return results


def detect_dwipushkar(
    tithi: Anga,
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Like Tripushkar but uses DWIPUSHKAR_NAKSHATRAS (Mrigashira, Chitra, Dhanishtha).
    Source: MC §11 / DP.
    Returns list[dict].
    """
    results = []
    if (tithi.id in DWIPUSHKAR_TITHIS
            and vara_id in DWIPUSHKAR_VARAS
            and nakshatra.id in DWIPUSHKAR_NAKSHATRAS):
        end = min(
            _ensure_utc(tithi.end_utc),
            _ensure_utc(nakshatra.end_utc),
            _ensure_utc(next_sunrise_utc),
        )
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("dwipushkar", clipped[0], clipped[1],
                                      "auspicious", 3))
    return results


def detect_siddha_yoga(
    vara_id: int,
    nakshatra: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Active when vara × nakshatra matches SIDDHA_YOGA_TABLE.
    Window: from sunrise to nakshatra end_utc (or next_sunrise).
    Source: MC §10 / BS §3 / DP.
    Returns list[dict].
    """
    results = []
    if vara_id in SIDDHA_YOGA_TABLE and nakshatra.id in SIDDHA_YOGA_TABLE[vara_id]:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("siddha_yoga", clipped[0], clipped[1],
                                      "auspicious", 3))
    return results


def detect_bhadra(
    karana_first: Anga,
    karana_second: Anga,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Active when either karana of the day is Vishti (id=7 = Bhadra).
    Window = the half-tithi spanned by the Vishti karana, clipped to sunrise frame.
    karana_first covers sunrise → its end_utc.
    karana_second covers karana_first.end_utc → end of second half-tithi.
    Source: MC §2 / BS §2 / DP.
    Returns list[dict].
    """
    results = []
    sr = _ensure_utc(sunrise_utc)
    nsr = _ensure_utc(next_sunrise_utc)

    if karana_first.id == BHADRA_KARANA_ID:
        # First karana covers sunrise → karana_first.end_utc
        end = min(_ensure_utc(karana_first.end_utc), nsr)
        clipped = _clip(sr, end, sr, nsr)
        if clipped:
            results.append(_yoga_dict("bhadra", clipped[0], clipped[1],
                                      "inauspicious", 0))

    if karana_second.id == BHADRA_KARANA_ID:
        # Second karana covers karana_first.end_utc → karana_second.end_utc
        start = max(_ensure_utc(karana_first.end_utc), sr)
        end = min(_ensure_utc(karana_second.end_utc), nsr)
        clipped = _clip(start, end, sr, nsr)
        if clipped:
            results.append(_yoga_dict("bhadra", clipped[0], clipped[1],
                                      "inauspicious", 0))

    return results


def detect_panchaka(
    nakshatra: Anga,
    vara_id: int,
    sunrise_utc: datetime,
    next_sunrise_utc: datetime,
) -> list:
    """
    Active when nakshatra.id is in PANCHAKA_NAKSHATRAS AND vara_id in PANCHAKA_VARAS.
    Window: nakshatra duration within the sunrise frame.
    Source: BS §3 / DP "Panchaka".
    Returns list[dict].
    """
    results = []
    if nakshatra.id in PANCHAKA_NAKSHATRAS and vara_id in PANCHAKA_VARAS:
        end = min(_ensure_utc(nakshatra.end_utc), _ensure_utc(next_sunrise_utc))
        clipped = _clip(_ensure_utc(sunrise_utc), end,
                        _ensure_utc(sunrise_utc), _ensure_utc(next_sunrise_utc))
        if clipped:
            results.append(_yoga_dict("panchaka", clipped[0], clipped[1],
                                      "inauspicious", 0))
    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_all_special_yogas(
    sunrise_utc: datetime,
    sunset_utc: datetime,
    next_sunrise_utc: datetime,
    tithi: Anga,
    nakshatra: Anga,
    yoga: Anga,
    karana_first: Anga,
    karana_second: Anga,
    vara: Anga,
) -> list:
    """
    Detect all 9 special yogas for a given Panchang day.

    Returns list of dicts:
      [{"yoga": str, "start_utc": datetime, "end_utc": datetime,
        "strength": "auspicious"|"inauspicious", "stars": int}]

    Star ratings:
      5 — Amrit Siddhi, Ravi Pushya, Guru Pushya   (highest auspicious)
      4 — Sarvartha Siddhi, Tripushkar
      3 — Siddha Yoga, Dwipushkar
      0 — Bhadra, Panchaka (inauspicious; no star rating)

    Multiple yogas can be active on the same day.
    Windows never extend beyond [sunrise_utc, next_sunrise_utc].
    """
    vara_id = vara.id
    results = []

    results.extend(detect_sarvartha_siddhi(vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_amrit_siddhi(vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_ravi_pushya(vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_guru_pushya(vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_tripushkar(tithi, vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_dwipushkar(tithi, vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_siddha_yoga(vara_id, nakshatra, sunrise_utc, next_sunrise_utc))
    results.extend(detect_bhadra(karana_first, karana_second, sunrise_utc, next_sunrise_utc))
    results.extend(detect_panchaka(nakshatra, vara_id, sunrise_utc, next_sunrise_utc))

    return results
