"""
muhurat.py — Muhurat Finder for panchang_engine.

Full implementation (Phase 4C-6-S1). Replaces the 4C-1-S2 scaffold.

6-event MVP set settled 2026-05-19 (D2 decision):
  vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation

Scoring rubric:
  score = sum(weight[factor] * quality[factor]) across tithi/nakshatra/vara/yoga/planet/native
  Knockout: if _in_inauspicious(), score = 0.0

Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3 + §4.4.1 (Muhurat Finder spec).
Classical authorities: Muhurta Chintamani (MC), Brihat Samhita (BS),
  Muhurta Martanda (MMP), Drik Panchang (DP).

WRAPUP-S4 Packet C addition: find_muhurat_from_cache() — reads from
panchanga_daily SQL cache instead of 90× compute_panchang() for Bhubaneswar
requests. Proxy dataclasses (_CachedAnga, _CachedTiming, _CachedPlanet,
_CachedPanchang) present the same attribute surface as the live Panchang type.
"""
import logging
from datetime import date as DateType, datetime, timedelta
from typing import Optional

from .types import MuhuratWindow, NatalChart, Panchang
from .shastra_tables import EVENT_TABLES
from .config_loader import get_weights_for_event as _get_weights_for_event

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

def _in_inauspicious(panchang: Panchang) -> bool:
    """
    Return True if the entire day falls within compound inauspicious windows
    (Rahu Kalam, Yamagandam, Gulika Kalam, or DurMuhurta covering the whole day).

    For a daylong scoring context (MVP; finer per-muhurta windows in v2), we
    treat the day as inauspicious only when ALL of the Panchang's inauspicious
    windows together span the entire sunrise→sunset arc with no gap.

    In practice, on any ordinary day, these windows cover only a fraction of
    the day, so this returns False for most days. Only truly pathological days
    (rare) hit the knockout — the avoid_penalty weight handles partial
    inauspiciousness via the scoring deduction for days where inauspicious
    windows are prominent but don't cover the whole day.

    For MVP: we implement a simpler heuristic:
      - If ANY of the "strong" inauspicious windows (Rahu Kalam or Yamagandam)
        fall AND the tithi is one of the known fully-inauspicious tithis
        (Amavasya, Chaturdashi, Ashtami) AND the vara is Saturday — the day is
        a full knockout.
      - Otherwise, False (scoring handles partial penalties).

    This matches classical usage: absolute prohibitions are reserved for
    compound afflictions on a single day, not for any single factor.

    Source: MC §Rahu Kalam + §DurMuhurta (compound inauspiciousness doctrine).
    """
    has_rahu_kalam = any(
        getattr(t, "label", "") == "rahu_kalam" for t in panchang.inauspicious
    )
    has_yamagandam = any(
        getattr(t, "label", "") == "yamagandam" for t in panchang.inauspicious
    )
    # Fully inauspicious tithis
    worst_tithis = {4, 8, 9, 14, 30}  # Chaturthi, Ashtami, Navami, Chaturdashi, Amavasya
    tithi_inauspicious = panchang.tithi.id in worst_tithis
    vara_saturday = panchang.vara.id == 7

    # Compound knockout: Rahu Kalam + Yamagandam + terrible tithi + Saturday
    if has_rahu_kalam and has_yamagandam and tithi_inauspicious and vara_saturday:
        return True
    return False


# ---------------------------------------------------------------------------
# Star rating conversion
# ---------------------------------------------------------------------------

def _score_to_stars(score: float) -> int:
    """
    Map 0..100 score → 1..5 star rating.
    Thresholds per brief §3 Item 4:
      80+ = 5★, 65-80 = 4★, 50-65 = 3★, 35-50 = 2★, 0-35 = 1★
    """
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

def _score_breakdown(
    panchang: Panchang,
    event: str,
    weights: dict,
    native_chart: Optional[NatalChart] = None,
) -> dict:
    """
    Return a dict of per-factor score contributions (raw, not multiplied by weight).
    Used for explainability in MuhuratWindow.breakdown.
    """
    quality_table = EVENT_TABLES[event]

    tithi_raw     = quality_table["tithi"].get(panchang.tithi.id, 0.0)
    nakshatra_raw = quality_table["nakshatra"].get(panchang.nakshatra.id, 0.0)
    vara_raw      = quality_table["vara"].get(panchang.vara.id, 0.0)

    # Yoga bonus
    auspicious_yogas = [
        y for y in panchang.special_yogas if y.get("strength") == "auspicious"
    ]
    yoga_raw = 0.0
    if auspicious_yogas:
        max_stars = max(y.get("stars", 1) for y in auspicious_yogas)
        yoga_raw = max_stars / 5.0

    # Planet bonus (Jupiter and Venus non-combust)
    jupiter = next((p for p in panchang.planets if p.name == "Jupiter"), None)
    venus   = next((p for p in panchang.planets if p.name == "Venus"), None)
    planet_raw = 0.0
    if jupiter and not jupiter.combust:
        planet_raw += 0.5
    if venus and not venus.combust:
        planet_raw += 0.5

    # Native overlay
    native_raw = 0.0
    if native_chart:
        from .tara_bala import compute_tara_bala_score
        native_raw = compute_tara_bala_score(
            native_chart.birth_nakshatra_id, panchang.nakshatra.id
        )

    # Return simple {factor: weighted_contribution} dict — all values are floats.
    # Keys match labelForBreakdownKey() in the UI (MuhuratResultsList.tsx).
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

def score_muhurat(
    panchang: Panchang,
    event: str,
    weights: dict = None,
    native_chart: Optional[NatalChart] = None,
) -> float:
    """
    Score a Panchang state for a given event. Returns 0..100.

    Args:
        panchang: Fully-computed Panchang for the day.
        event: Event key — must be in EVENTS_MVP.
        weights: Scoring weights dict; defaults to YAML-loaded per-event weights
                 from config/muhurat_weights.yaml via config_loader.get_weights_for_event().
                 Pass an explicit dict to override (useful for testing).
        native_chart: Optional NatalChart for Tara Bala native overlay.

    Returns:
        float in 0.0..100.0. Knockout case (compound inauspicious day) returns 0.0.

    Raises:
        ValueError if event is not in EVENTS_MVP.

    Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3; MC scoring rubric.
    """
    if not is_supported_event(event):
        raise ValueError(
            f"Event '{event}' not in MVP set. Supported events: {EVENTS_MVP}"
        )

    if weights is None:
        weights = _get_weights_for_event(event)
    quality_table = EVENT_TABLES[event]

    # Knockout check — compound inauspicious day → 0.0
    if _in_inauspicious(panchang):
        return 0.0

    score = 0.0

    # Tithi contribution
    score += weights["tithi"] * quality_table["tithi"].get(panchang.tithi.id, 0.0)

    # Nakshatra contribution
    score += weights["nakshatra"] * quality_table["nakshatra"].get(panchang.nakshatra.id, 0.0)

    # Vara contribution
    score += weights["vara"] * quality_table["vara"].get(panchang.vara.id, 0.0)

    # Special yoga bonus — auspicious yogas detected by special_yogas engine
    auspicious_yogas = [
        y for y in panchang.special_yogas if y.get("strength") == "auspicious"
    ]
    if auspicious_yogas:
        max_stars = max(y.get("stars", 1) for y in auspicious_yogas)
        score += weights["yoga"] * (max_stars / 5.0)

    # Planet bonus (Jupiter and/or Venus non-combust each contribute half)
    jupiter = next((p for p in panchang.planets if p.name == "Jupiter"), None)
    venus   = next((p for p in panchang.planets if p.name == "Venus"), None)
    if jupiter and not jupiter.combust:
        score += weights["planet"] * 0.5
    if venus and not venus.combust:
        score += weights["planet"] * 0.5

    # Native overlay — Tara Bala when NatalChart is provided
    if native_chart:
        from .tara_bala import compute_tara_bala_score
        score += weights["native"] * compute_tara_bala_score(
            native_chart.birth_nakshatra_id, panchang.nakshatra.id
        )

    # Convert 0..~0.95 range to 0..100; cap at 100
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
    tz_offset_minutes: int = 330,
    native_chart: Optional[NatalChart] = None,
    weights: dict = None,
    top_n: int = 10,
) -> list[MuhuratWindow]:
    """
    Return top auspicious windows for `event` in [date_from, date_to].

    Iterates each day in the range, computes Panchang, scores it, and returns
    the top_n days by score as MuhuratWindow objects with a per-factor breakdown.

    Args:
        event: Event key — must be in EVENTS_MVP.
        date_from: Search window start (inclusive).
        date_to: Search window end (inclusive).
        lat: Latitude in decimal degrees (+N).
        lon: Longitude in decimal degrees (+E).
        tz_offset_minutes: UTC offset in minutes (default 330 = IST +05:30).
        native_chart: Optional NatalChart for Tara Bala native overlay.
        weights: Custom scoring weights dict; defaults to YAML-loaded per-event weights
                 from config/muhurat_weights.yaml. Pass an explicit dict to override.
        top_n: Number of top windows to return (default 10).

    Returns:
        list[MuhuratWindow] — sorted by score descending, length <= top_n.

    Raises:
        ValueError if event is not in EVENTS_MVP or date_from > date_to.

    Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.1 + §5.3.
    """
    if not is_supported_event(event):
        raise ValueError(
            f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}"
        )
    if date_from > date_to:
        raise ValueError(
            f"date_from ({date_from}) must be <= date_to ({date_to})"
        )

    # Lazy import to avoid circular deps; compute_panchang is the top-level function
    from panchang_engine import compute_panchang

    if weights is None:
        weights = _get_weights_for_event(event)

    candidates: list[MuhuratWindow] = []
    current = date_from

    while current <= date_to:
        panchang = compute_panchang(current, lat, lon, tz_offset_minutes)
        s = score_muhurat(panchang, event, weights, native_chart)

        if s > 0:
            breakdown = _score_breakdown(panchang, event, weights, native_chart)
            window = MuhuratWindow(
                event=event,
                start_utc=panchang.sunrise_utc,
                end_utc=panchang.sunset_utc,        # daylong for MVP; finer in v2
                star_rating=_score_to_stars(s),
                score=s,
                breakdown=breakdown,
            )
            candidates.append(window)

        current = current + timedelta(days=1)

    # Sort by score descending; return top_n
    candidates.sort(key=lambda w: w.score, reverse=True)
    return candidates[:top_n]


# ---------------------------------------------------------------------------
# Cache-path proxy dataclasses
# ---------------------------------------------------------------------------
# score_muhurat() and _in_inauspicious() access these attributes on a Panchang:
#   panchang.tithi.id, .name
#   panchang.nakshatra.id, .name
#   panchang.vara.id, .name
#   panchang.inauspicious   — iterable; each item needs getattr(t, "label", "")
#   panchang.special_yogas  — list of dicts (already dicts in DB cache → OK)
#   panchang.planets        — iterable; each item needs .name and .combust
#   panchang.sunrise_utc, .sunset_utc  — for MuhuratWindow construction
#
# The panchanga_daily table stores:
#   - tithi_id/nakshatra_id/vara_id as plain int columns
#   - Tithi/nakshatra/vara names are NOT stored as separate columns — the JSONB
#     enrichment columns do not carry these names directly either (they are in
#     the serialize output but not in the core SQL columns from bootstrap).
#
# Strategy: we store lightweight proxy objects with only the fields that
# score_muhurat() and _in_inauspicious() actually read.
# Names (tithi.name, nakshatra.name, vara.name) appear in _score_breakdown()
# for display only; we supply empty strings when the DB row does not carry them.

class _CachedAnga:
    """Lightweight proxy for Anga — presents .id and .name."""
    __slots__ = ("id", "name", "end_utc")

    def __init__(self, id: int, name: str = "", end_utc=None):  # noqa: A002
        self.id = id
        self.name = name
        self.end_utc = end_utc


class _CachedTiming:
    """Lightweight proxy for Timing — presents .label, .start_utc, .end_utc."""
    __slots__ = ("label", "start_utc", "end_utc")

    def __init__(self, label: str, start_utc=None, end_utc=None):
        self.label = label
        self.start_utc = start_utc
        self.end_utc = end_utc


class _CachedPlanet:
    """Lightweight proxy for PlanetState — presents .name and .combust."""
    __slots__ = ("name", "combust")

    def __init__(self, name: str, combust: bool = False):
        self.name = name
        self.combust = combust


class _CachedPanchang:
    """
    Proxy presenting the same attribute surface as Panchang to score_muhurat().

    Built from a panchanga_daily DB row. The row carries:
      - tithi_id, nakshatra_id, vara_id (int columns)
      - sunrise_utc, sunset_utc (datetime or ISO string)
      - special_yogas (list of dicts — same shape as live engine output)
      - inauspicious (list of dicts with "label" key)
      - planets column is NOT stored in panchanga_daily core columns;
        we supply an empty planet list, which means the planet bonus is 0.
        This is a known limitation documented in the brief.
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

        # Inauspicious: list[dict] → list of _CachedTiming proxies
        self.inauspicious = [
            _CachedTiming(t.get("label", ""), t.get("start_utc"), t.get("end_utc"))
            for t in (row.get("inauspicious") or [])
        ]

        # Auspicious: same treatment
        self.auspicious = [
            _CachedTiming(t.get("label", ""), t.get("start_utc"), t.get("end_utc"))
            for t in (row.get("auspicious") or [])
        ]

        # special_yogas: already list[dict] from JSONB — score_muhurat uses .get()
        self.special_yogas = row.get("special_yogas") or []

        # Planets: panchanga_daily does not store planet states in the core columns.
        # We emit an empty list; planet bonus = 0 for cache path.
        # Jupiter/Venus combust data is unavailable from cache — acceptable trade-off
        # (planet weight is typically 0.05–0.10; tithi/nakshatra/vara dominate).
        self.planets = []

        # sunrise/sunset: may be datetime or ISO string
        sr = row.get("sunrise_utc")
        ss = row.get("sunset_utc")
        self.sunrise_utc = _parse_dt(sr)
        self.sunset_utc  = _parse_dt(ss)


def _parse_dt(value) -> Optional[datetime]:
    """Convert a datetime, ISO string, or None to a datetime (or None)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle both "2026-05-21T01:23:45Z" and "2026-05-21 01:23:45"
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
    native_chart: Optional[NatalChart] = None,
    weights: dict = None,
    top_n: int = 10,
) -> Optional[list[MuhuratWindow]]:
    """
    Cache-path alternative to find_muhurat().

    Reads panchanga_daily rows for [date_from, date_to], builds lightweight
    proxy Panchang objects, then runs the identical score_muhurat() + breakdown
    logic without calling compute_panchang() / Swiss Ephemeris.

    Returns:
        list[MuhuratWindow] — same shape as find_muhurat(), or
        None on any failure (DB unavailable, partial data, exception) so the
        caller can fall back to engine-direct.

    Limitation: planet bonus is 0 for cache path because panchanga_daily does
    not store per-planet combust states in its core columns. The tithi /
    nakshatra / vara / yoga / native scoring factors are fully preserved.
    Planet weight is typically <= 0.10 of total score; the trade-off is
    acceptable for the 90-day scan performance gain.

    Performance: single SELECT (~1–5 ms) vs 90 × compute_panchang() (~30–90 s).
    """
    try:
        from .panchang_daily_reader import fetch_panchanga_range

        rows = fetch_panchanga_range(date_from, date_to, db_url)
        if rows is None:
            return None  # cache miss — fall through to engine-direct

        if weights is None:
            weights = _get_weights_for_event(event)

        candidates: list[MuhuratWindow] = []

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
                logger.warning(
                    "Cache-path scoring failed for row date=%s: %s",
                    row.get("date"), row_exc,
                )
                # Skip this day rather than aborting the whole range
                continue

        candidates.sort(key=lambda w: w.score, reverse=True)
        return candidates[:top_n]

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "find_muhurat_from_cache failed (%s: %s); falling back to engine-direct",
            type(exc).__name__, exc,
        )
        return None
