"""
muhurat/finder.py — Muhurat Finder: deterministic scoring against panchang_engine output.

Moved from panchang_engine/muhurat.py (P2 re-arch, 2026-06-09).
Scoring/judgement lives here. panchang_engine/ holds only the deterministic core.

6-event MVP set settled 2026-05-19 (D2 decision):
  vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation

Scoring rubric:
  score = sum(weight[factor] * quality[factor]) across tithi/nakshatra/vara/yoga/planet/native
  Knockout: if _in_inauspicious(), score = 0.0

Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3 + §4.4.1 (Muhurat Finder spec).
Classical authorities: Muhurta Chintamani (MC), Brihat Samhita (BS),
  Muhurta Martanda (MMP), Drik Panchang (DP).
"""
import logging
from datetime import date as DateType, datetime, timedelta
from typing import Optional

from panchang_engine.types import MuhuratWindow, NatalChart, Panchang
from panchang_engine.shastra_tables import EVENT_TABLES
from panchang_engine.config_loader import get_weights_for_event as _get_weights_for_event

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MVP event set — locked in 4C-1-S2; 4C.6 scores all 6
# ---------------------------------------------------------------------------
EVENTS_MVP: list[str] = [
    "vivah",              # Marriage
    "griha_pravesh",      # House warming / new home entry
    "vyapara",            # Business start / commerce
    "yatra",              # Journey / travel
    "property_purchase",  # Property / vehicle purchase
    "mantra_initiation",  # Mantra diksha / initiation
]


def is_supported_event(event: str) -> bool:
    """Return True if event is in the curated MVP set (settled D2 2026-05-19)."""
    return event in EVENTS_MVP


# ---------------------------------------------------------------------------
# Knockout helper
# ---------------------------------------------------------------------------

def _in_inauspicious(panchang) -> bool:
    """
    Return True if the day has compound inauspicious conditions warranting a knockout.
    Compound knockout: Rahu Kalam + Yamagandam + terrible tithi + Saturday.
    Source: MC §Rahu Kalam + §DurMuhurta (compound inauspiciousness doctrine).
    """
    has_rahu_kalam = any(
        getattr(t, "label", "") == "rahu_kalam" for t in panchang.inauspicious
    )
    has_yamagandam = any(
        getattr(t, "label", "") == "yamagandam" for t in panchang.inauspicious
    )
    worst_tithis = {4, 8, 9, 14, 30}  # Chaturthi, Ashtami, Navami, Chaturdashi, Amavasya
    tithi_inauspicious = panchang.tithi.id in worst_tithis
    vara_saturday = panchang.vara.id == 7

    if has_rahu_kalam and has_yamagandam and tithi_inauspicious and vara_saturday:
        return True
    return False


# ---------------------------------------------------------------------------
# Star rating conversion
# ---------------------------------------------------------------------------

def _score_to_stars(score: float) -> int:
    """Map 0..100 score → 1..5 stars. Thresholds: 80+=5, 65+=4, 50+=3, 35+=2, else 1."""
    if score >= 80:
        return 5
    elif score >= 65:
        return 4
    elif score >= 50:
        return 3
    elif score >= 35:
        return 2
    else:
        return 1


# ---------------------------------------------------------------------------
# Score breakdown
# ---------------------------------------------------------------------------

def _score_breakdown(panchang, event: str, weights: dict, native_chart=None) -> dict:
    """Return per-factor score contributions dict (for MuhuratWindow.breakdown)."""
    quality_table = EVENT_TABLES[event]

    tithi_raw     = quality_table["tithi"].get(panchang.tithi.id, 0.0)
    nakshatra_raw = quality_table["nakshatra"].get(panchang.nakshatra.id, 0.0)
    vara_raw      = quality_table["vara"].get(panchang.vara.id, 0.0)

    auspicious_yogas = [
        y for y in panchang.special_yogas if y.get("strength") == "auspicious"
    ]
    yoga_raw = 0.0
    if auspicious_yogas:
        max_stars = max(y.get("stars", 1) for y in auspicious_yogas)
        yoga_raw = max_stars / 5.0

    jupiter = next((p for p in panchang.planets if p.name == "Jupiter"), None)
    venus   = next((p for p in panchang.planets if p.name == "Venus"), None)
    planet_raw = 0.0
    if jupiter and not jupiter.combust:
        planet_raw += 0.5
    if venus and not venus.combust:
        planet_raw += 0.5

    native_raw = 0.0
    if native_chart:
        from panchang_engine.tara_bala import compute_tara_bala_score
        native_raw = compute_tara_bala_score(
            native_chart.birth_nakshatra_id, panchang.nakshatra.id
        )

    result: dict = {
        "tithi":     round(weights["tithi"]     * tithi_raw,     4),
        "nakshatra": round(weights["nakshatra"] * nakshatra_raw, 4),
        "vara":      round(weights["vara"]      * vara_raw,      4),
        "yoga":      round(weights["yoga"]      * yoga_raw,      4),
        "planet":    round(weights["planet"]    * planet_raw,    4),
    }
    if native_chart:
        result["tara_bala"] = round(weights["native"] * native_raw, 4)
    return result


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def score_muhurat(panchang, event: str, weights: dict = None, native_chart=None) -> float:
    """
    Score a Panchang state for a given event. Returns 0..100.

    Args:
        panchang: Fully-computed Panchang (or _CachedPanchang proxy) for the day.
        event: Event key — must be in EVENTS_MVP.
        weights: Scoring weights dict; defaults to YAML-loaded per-event weights.
        native_chart: Optional NatalChart for Tara Bala native overlay.

    Returns:
        float in 0.0..100.0. Knockout case (compound inauspicious) returns 0.0.
    """
    if not is_supported_event(event):
        raise ValueError(f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}")

    if weights is None:
        weights = _get_weights_for_event(event)
    quality_table = EVENT_TABLES[event]

    if _in_inauspicious(panchang):
        return 0.0

    score = 0.0
    score += weights["tithi"]     * quality_table["tithi"].get(panchang.tithi.id, 0.0)
    score += weights["nakshatra"] * quality_table["nakshatra"].get(panchang.nakshatra.id, 0.0)
    score += weights["vara"]      * quality_table["vara"].get(panchang.vara.id, 0.0)

    auspicious_yogas = [
        y for y in panchang.special_yogas if y.get("strength") == "auspicious"
    ]
    if auspicious_yogas:
        max_stars = max(y.get("stars", 1) for y in auspicious_yogas)
        score += weights["yoga"] * (max_stars / 5.0)

    jupiter = next((p for p in panchang.planets if p.name == "Jupiter"), None)
    venus   = next((p for p in panchang.planets if p.name == "Venus"), None)
    if jupiter and not jupiter.combust:
        score += weights["planet"] * 0.5
    if venus and not venus.combust:
        score += weights["planet"] * 0.5

    if native_chart:
        from panchang_engine.tara_bala import compute_tara_bala_score
        score += weights["native"] * compute_tara_bala_score(
            native_chart.birth_nakshatra_id, panchang.nakshatra.id
        )

    return min(100.0, score * 100.0)


# ---------------------------------------------------------------------------
# Range finder
# ---------------------------------------------------------------------------

def find_muhurat(
    event: str,
    date_from: DateType,
    date_to: DateType,
    lat: float,
    lon: float,
    tz_offset_minutes: int,
    native_chart=None,
    weights: dict = None,
    top_n: int = 10,
) -> list:
    """
    Return top auspicious windows for `event` in [date_from, date_to].

    Args:
        event: Event key — must be in EVENTS_MVP.
        date_from, date_to: Inclusive search window.
        lat, lon: Decimal degrees.
        tz_offset_minutes: UTC offset in minutes. Required — no default.
        native_chart: Optional NatalChart for Tara Bala.
        weights: Custom weights dict; defaults to per-event YAML weights.
        top_n: Number of top windows to return.

    Returns:
        list[MuhuratWindow] sorted by score descending.
    """
    if not is_supported_event(event):
        raise ValueError(f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}")
    if date_from > date_to:
        raise ValueError(f"date_from ({date_from}) must be <= date_to ({date_to})")

    from panchang_engine import compute_panchang

    if weights is None:
        weights = _get_weights_for_event(event)

    candidates: list = []
    current = date_from

    while current <= date_to:
        panchang = compute_panchang(current, lat, lon, tz_offset_minutes)
        s = score_muhurat(panchang, event, weights, native_chart)

        if s > 0:
            breakdown = _score_breakdown(panchang, event, weights, native_chart)
            window = MuhuratWindow(
                event=event,
                start_utc=panchang.sunrise_utc,
                end_utc=panchang.sunset_utc,
                star_rating=_score_to_stars(s),
                score=s,
                breakdown=breakdown,
            )
            candidates.append(window)

        current = current + timedelta(days=1)

    candidates.sort(key=lambda w: w.score, reverse=True)
    return candidates[:top_n]


# ---------------------------------------------------------------------------
# Cache-path proxy dataclasses
# ---------------------------------------------------------------------------

class _CachedAnga:
    __slots__ = ("id", "name", "end_utc")

    def __init__(self, id: int, name: str = "", end_utc=None):  # noqa: A002
        self.id = id
        self.name = name
        self.end_utc = end_utc


class _CachedTiming:
    __slots__ = ("label", "start_utc", "end_utc")

    def __init__(self, label: str, start_utc=None, end_utc=None):
        self.label = label
        self.start_utc = start_utc
        self.end_utc = end_utc


class _CachedPlanet:
    __slots__ = ("name", "combust")

    def __init__(self, name: str, combust: bool = False):
        self.name = name
        self.combust = combust


class _CachedPanchang:
    """
    Proxy presenting the same attribute surface as Panchang to score_muhurat().
    Built from a panchanga_daily DB row.
    """
    __slots__ = (
        "tithi", "nakshatra", "vara",
        "inauspicious", "auspicious",
        "special_yogas", "planets",
        "sunrise_utc", "sunset_utc",
    )

    def __init__(self, row: dict):
        self.tithi     = _CachedAnga(row["tithi_id"])
        self.nakshatra = _CachedAnga(row["nakshatra_id"])
        self.vara      = _CachedAnga(row["vara_id"])

        self.inauspicious = [
            _CachedTiming(t.get("label", ""), t.get("start_utc"), t.get("end_utc"))
            for t in (row.get("inauspicious") or [])
        ]
        self.auspicious = [
            _CachedTiming(t.get("label", ""), t.get("start_utc"), t.get("end_utc"))
            for t in (row.get("auspicious") or [])
        ]
        self.special_yogas = row.get("special_yogas") or []
        self.planets = []  # planet bonus = 0 for cache path (no combust data)

        sr = row.get("sunrise_utc")
        ss = row.get("sunset_utc")
        self.sunrise_utc = _parse_dt(sr)
        self.sunset_utc  = _parse_dt(ss)


def _parse_dt(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.rstrip("Z").replace("T", " ")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Cache-backed muhurat finder
# ---------------------------------------------------------------------------

def find_muhurat_from_cache(
    event: str,
    date_from: DateType,
    date_to: DateType,
    lat: float,
    lon: float,
    db_url: str,
    native_chart=None,
    weights: dict = None,
    top_n: int = 10,
) -> Optional[list]:
    """
    Cache-path alternative to find_muhurat().
    Reads panchanga_daily rows, builds proxy Panchang objects, runs scoring.
    Returns None on any failure (DB unavailable / partial data) → caller falls back.
    """
    try:
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        rows = fetch_panchanga_range(date_from, date_to, db_url)
        if rows is None:
            return None

        if weights is None:
            weights = _get_weights_for_event(event)

        candidates: list = []

        for row in rows:
            try:
                proxy = _CachedPanchang(row)
                s = score_muhurat(proxy, event, weights, native_chart)

                if s > 0:
                    breakdown = _score_breakdown(proxy, event, weights, native_chart)
                    window = MuhuratWindow(
                        event=event,
                        start_utc=proxy.sunrise_utc,
                        end_utc=proxy.sunset_utc,
                        star_rating=_score_to_stars(s),
                        score=s,
                        breakdown=breakdown,
                    )
                    candidates.append(window)

            except Exception as row_exc:  # noqa: BLE001
                logger.warning("Cache-path scoring failed for date=%s: %s",
                               row.get("date"), row_exc)
                continue

        candidates.sort(key=lambda w: w.score, reverse=True)
        return candidates[:top_n]

    except Exception as exc:  # noqa: BLE001
        logger.warning("find_muhurat_from_cache failed (%s: %s); falling back",
                       type(exc).__name__, exc)
        return None
