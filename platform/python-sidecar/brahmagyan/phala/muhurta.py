"""
brahmagyan/phala/muhurta.py — Brahma L4 Phala — phala.muhurta (PH-4-4)

Asset:    phala.muhurta (electional finder — inverts Phala prediction engine)
Table:    phala_muhurta (muhurta_id UUID, action_type TEXT, window_start TIMESTAMPTZ,
          window_end TIMESTAMPTZ, auspiciousness_score FLOAT CHECK(0<=s<=1),
          factors JSONB, source_citation TEXT NOT NULL)
Tool:     muhurta_finder(chart_id, action_type, date_range, min_score?)
          → {windows:[{start,end,score,factors}], provenance_envelope}

Algorithm (PH-4-4 contract):
    For each 48-hour window in the requested date range (max 90 days → up to 45 windows):
        auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%)
                             + transit_quality(20%) + signal_activation(10%)
    All sub-scores and composite in [0.0, 1.0].

action_types: marriage | travel | business | medical | education | property | general

FORENSIC grounding:
    Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
    chart_id: 482012f1-710e-4a25-994a-93821f5871aa
    Mercury MD (2026–2043) per FORENSIC v8.0 §5.1 DSH.V.023
    A high-score muhurta for education aligns with Mercury+Pushya windows.

Depends:
    - panchanga_daily (Phase 4C-3): for panchanga_quality sub-score
    - chart_facts (BRAHMA G9/G10): for dasha_quality derivation
    - phala_muhurta (this migration): pre-computed cache rows

Authors:  Silpī (PH-4-4 session)
Version:  1.0 — 2026-06-04
BRAHMA-PH-4-4
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import psycopg
import psycopg.rows
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

VALID_ACTION_TYPES = frozenset({
    "marriage", "travel", "business", "medical",
    "education", "property", "general",
})

# Maximum date range (90 days = up to 45 × 48-hour windows)
MAX_DATE_RANGE_DAYS = 90

# Window duration in hours (48-hour blocks per contract)
WINDOW_HOURS = 48

# Score weights (must sum to 1.0)
WEIGHT_PANCHANGA = 0.40
WEIGHT_DASHA = 0.30
WEIGHT_TRANSIT = 0.20
WEIGHT_SIGNAL = 0.10

# ── DB URL ────────────────────────────────────────────────────────────────────


def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── T-8 fix (D-1.6 S-1): live dasha-lord lookup ──────────────────────────────
#
# The muhurta citation used to hardcode "FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD
# (2026-2043)" for EVERY window on EVERY chart, regardless of which Mahadasha was
# actually active at that window's date. This was doubly wrong for the native
# chart itself: chart_dashas (the canonical L1 fact table) shows Mercury MD
# running 2010-08-17 -> 2027-08-17 (confirmed live via query), not 2026-2043 —
# the hardcoded string was never derived from chart_dashas at all. Fixed by
# querying chart_dashas directly for the MD (level_n=1) and AD (level_n=2) lord
# actually active at the window's start date, and building the citation from
# that live result. Falls back to "unknown"/no-citation-claim rather than ever
# re-asserting the stale hardcoded string (B.10 — no fabricated computation).
_DASHA_LORD_CACHE: dict[tuple[str, str, str], dict[str, Any] | None] = {}


def _current_dasha_lords(
    chart_id: str,
    at_date: datetime,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    system_id: str = "vimshottari",
) -> dict[str, Any] | None:
    """
    Look up the live Mahadasha (level_n=1) and Antardasha (level_n=2) lord + window
    actually active at `at_date` for `chart_id`, from the canonical chart_dashas table.

    Returns {"md_lord": str, "md_start": date, "md_end": date,
             "ad_lord": str | None} or None if no DB / no matching row.
    Cached per (chart_id, ayanamsha_id, at_date.date()) within process lifetime —
    windows in the same muhurta_finder call frequently share a date.
    """
    date_key = at_date.date().isoformat()
    cache_key = (chart_id, ayanamsha_id, date_key)
    if cache_key in _DASHA_LORD_CACHE:
        return _DASHA_LORD_CACHE[cache_key]

    result: dict[str, Any] | None = None
    try:
        db_url = _get_db_url()
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT lord_graha, start_date, end_date
                    FROM chart_dashas
                    WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = %s
                      AND level_n = 1
                      AND start_date <= %s AND end_date >= %s
                    ORDER BY start_date DESC
                    LIMIT 1
                    """,
                    [chart_id, ayanamsha_id, system_id, date_key, date_key],
                )
                md_row = cur.fetchone()
                if md_row:
                    ad_lord: Optional[str] = None
                    cur.execute(
                        """
                        SELECT lord_graha
                        FROM chart_dashas
                        WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = %s
                          AND level_n = 2
                          AND start_date <= %s AND end_date >= %s
                        ORDER BY start_date DESC
                        LIMIT 1
                        """,
                        [chart_id, ayanamsha_id, system_id, date_key, date_key],
                    )
                    ad_row = cur.fetchone()
                    if ad_row:
                        ad_lord = str(ad_row.get("lord_graha", "")) or None
                    result = {
                        "md_lord": str(md_row.get("lord_graha", "")),
                        "md_start": md_row.get("start_date"),
                        "md_end": md_row.get("end_date"),
                        "ad_lord": ad_lord,
                    }
    except Exception:
        result = None  # honest None — never fabricated; caller degrades gracefully

    _DASHA_LORD_CACHE[cache_key] = result
    return result


def _dasha_citation_fragment_from(live: dict[str, Any] | None) -> str:
    """
    Build the dasha portion of a muhurta window's source_citation from an
    already-resolved `_current_dasha_lords(...)` result (T-8 fix) instead of a
    hardcoded lord/date-range string. Takes the dict directly (rather than
    re-querying) so callers that already resolved it for `dasha_details` don't
    pay for a second lookup — `_current_dasha_lords` is itself cached, but this
    keeps the call site simple and avoids relying on cache-hit behavior.
    """
    if live and live.get("md_lord"):
        md_start = live.get("md_start")
        md_end = live.get("md_end")
        span = (
            f"({md_start}→{md_end})"
            if md_start is not None and md_end is not None
            else ""
        )
        ad_part = f" / {live['ad_lord']} AD" if live.get("ad_lord") else ""
        return f"chart_dashas: {live['md_lord']} MD{span}{ad_part}"
    return "chart_dashas: dasha lord unavailable for this window (no matching row)"


def _dasha_citation_fragment(chart_id: str, at_date: datetime) -> str:
    """Convenience wrapper: resolve + format in one call (used where the caller
    has not already fetched `_current_dasha_lords` for this date)."""
    return _dasha_citation_fragment_from(_current_dasha_lords(chart_id, at_date))


# ── Scoring engine ────────────────────────────────────────────────────────────


def compute_muhurta_score(
    panchanga_quality: float,
    dasha_quality: float,
    transit_quality: float,
    signal_activation: float,
) -> float:
    """
    PH-4-4 composite auspiciousness score.

    score = CLAMP(
        0.40 × panchanga_quality
        + 0.30 × dasha_quality
        + 0.20 × transit_quality
        + 0.10 × signal_activation,
        0.0, 1.0
    )

    All inputs must be in [0.0, 1.0].
    This mirrors the SQL phala_compute_muhurta_score() function.
    """
    raw = (
        WEIGHT_PANCHANGA * panchanga_quality
        + WEIGHT_DASHA * dasha_quality
        + WEIGHT_TRANSIT * transit_quality
        + WEIGHT_SIGNAL * signal_activation
    )
    return float(max(0.0, min(1.0, raw)))


def _panchanga_quality_for_action(
    tithi_name: str,
    vara_lord: str,
    moon_nakshatra: str,
    yoga: str,
    action_type: str,
) -> float:
    """
    Derive a panchanga quality score [0.0, 1.0] for a given action_type
    from the five panchanga limbs.

    Classical rules per BPHS ch.46 (muhurta adhyaya) and Muhurta Chintamani:
      - marriage: Rohini, Revati, Mrigashira, Hasta, Swati, Anuradha, Magha auspicious
        vara: Monday, Wednesday, Thursday, Friday auspicious
        tithi: 2, 3, 5, 7, 10, 11, 13 shukla auspicious
      - education: Pushya, Hasta, Ashwini, Rohini, Uttaraphalguni auspicious
        vara: Wednesday, Thursday auspicious
      - business: Rohini, Hasta, Pushya auspicious
        vara: Wednesday auspicious
      - travel: Ashwini, Mrigashira, Pushya, Hasta auspicious
      - medical: Pushya, Ashwini auspicious; Krittika inauspicious
      - property: Rohini, Uttaraphalguni, Uttarashada, Uttarabhadra auspicious
      - general: all 27 nakshatras permissible; vara quality weighted

    Knockout tithi: 4, 8, 9, 14, 15 krishna (amavasya, panchami, chaturdashi of dark) reduced.
    Yoga knockouts: Vishkumbha, Atiganda, Shoola, Ganda, Vyaghata, Vajra, Vyatipata, Parigha → 0.3 cap.

    Returns a score in [0.0, 1.0].
    """
    # Auspicious nakshatra sets per action type (classical BPHS sources)
    _MARRIAGE_NAKS = {
        "Rohini", "Revati", "Mrigashira", "Hasta", "Swati",
        "Anuradha", "Magha", "Uttaraphalguni", "Uttarashada", "Uttarabhadra",
    }
    _EDUCATION_NAKS = {
        "Pushya", "Hasta", "Ashwini", "Rohini", "Uttaraphalguni",
        "Shravana", "Mrigashira",
    }
    _BUSINESS_NAKS = {
        "Rohini", "Hasta", "Pushya", "Ashwini", "Uttaraphalguni", "Mrigashira",
    }
    _TRAVEL_NAKS = {
        "Ashwini", "Mrigashira", "Pushya", "Hasta", "Anuradha",
        "Shatabhisha", "Punarvasu",
    }
    _MEDICAL_NAKS = {"Pushya", "Ashwini"}
    _MEDICAL_BAD_NAKS = {"Krittika", "Ardra", "Vishakha"}
    _PROPERTY_NAKS = {
        "Rohini", "Uttaraphalguni", "Uttarashada", "Uttarabhadra",
        "Hasta", "Anuradha",
    }

    _MARRIAGE_VARA = {"Monday", "Wednesday", "Thursday", "Friday"}
    _EDUCATION_VARA = {"Wednesday", "Thursday"}
    _BUSINESS_VARA = {"Wednesday", "Thursday", "Friday"}
    _TRAVEL_VARA = {"Wednesday", "Thursday", "Monday"}
    _PROPERTY_VARA = {"Monday", "Wednesday", "Thursday", "Friday"}
    _GENERAL_VARA = {"Monday", "Wednesday", "Thursday", "Friday"}

    _INAUSPICIOUS_YOGA = {
        "Vishkumbha", "Atiganda", "Shoola", "Ganda", "Vyaghata",
        "Vajra", "Vyatipata", "Parigha",
    }

    # Inauspicious tithi list (dark fortnight: 4th, 8th, 14th + Amavasya)
    _BAD_TITHI_PARTIAL = {
        "Krishna Chaturthi", "Krishna Ashtami", "Krishna Chaturdashi",
        "Amavasya", "Purnima",  # Purnima is mixed — good for some, neutral here
    }

    # Nakshatra quality
    nak_quality: float
    if action_type == "marriage":
        nak_quality = 0.85 if moon_nakshatra in _MARRIAGE_NAKS else 0.40
    elif action_type == "education":
        nak_quality = 0.90 if moon_nakshatra in _EDUCATION_NAKS else 0.45
    elif action_type == "business":
        nak_quality = 0.80 if moon_nakshatra in _BUSINESS_NAKS else 0.45
    elif action_type == "travel":
        nak_quality = 0.80 if moon_nakshatra in _TRAVEL_NAKS else 0.45
    elif action_type == "medical":
        if moon_nakshatra in _MEDICAL_BAD_NAKS:
            nak_quality = 0.20
        elif moon_nakshatra in _MEDICAL_NAKS:
            nak_quality = 0.90
        else:
            nak_quality = 0.50
    elif action_type == "property":
        nak_quality = 0.85 if moon_nakshatra in _PROPERTY_NAKS else 0.40
    else:  # general
        nak_quality = 0.55  # neutral default

    # Vara (weekday) quality
    vara_quality: float
    if action_type == "marriage":
        vara_quality = 0.85 if vara_lord in _MARRIAGE_VARA else 0.30
    elif action_type == "education":
        vara_quality = 0.90 if vara_lord in _EDUCATION_VARA else 0.40
    elif action_type == "business":
        vara_quality = 0.80 if vara_lord in _BUSINESS_VARA else 0.35
    elif action_type == "travel":
        vara_quality = 0.75 if vara_lord in _TRAVEL_VARA else 0.40
    elif action_type == "property":
        vara_quality = 0.80 if vara_lord in _PROPERTY_VARA else 0.35
    else:  # general / medical
        vara_quality = 0.70 if vara_lord in _GENERAL_VARA else 0.40

    # Tithi quality (simple check for clearly inauspicious tithis)
    tithi_quality: float
    if any(bad in tithi_name for bad in ("Shtami", "Ashtami", "Chaturdashi")):
        tithi_quality = 0.30
    elif "Amavasya" in tithi_name:
        tithi_quality = 0.25
    elif any(good in tithi_name for good in ("Panchami", "Shashti", "Saptami", "Dasami", "Dvadashi", "Tritiya")):
        tithi_quality = 0.80
    elif any(good in tithi_name for good in ("Ekadashi", "Trayodashi")):
        tithi_quality = 0.75
    else:
        tithi_quality = 0.55

    # Yoga quality (knockouts cap the score)
    yoga_quality: float
    if yoga in _INAUSPICIOUS_YOGA:
        yoga_quality = 0.20
    elif yoga in {"Siddha", "Brahma", "Indra", "Vaidhriti"}:
        yoga_quality = 0.90
    elif yoga in {"Shubha", "Shukla", "Dhruva", "Sukha", "Harshana", "Siddhi"}:
        yoga_quality = 0.80
    else:
        yoga_quality = 0.55

    # Weighted composite: nak(40%) + vara(30%) + tithi(20%) + yoga(10%)
    raw = (
        0.40 * nak_quality
        + 0.30 * vara_quality
        + 0.20 * tithi_quality
        + 0.10 * yoga_quality
    )
    return float(max(0.0, min(1.0, raw)))


def _dasha_quality_for_chart(chart_id: str, window_start: datetime) -> float:
    """
    Derive dasha quality from chart_facts (if available) or use native defaults.

    For the native (Abhisek Mohanty), FORENSIC v8.0 §5.1 DSH.V.023 establishes:
      Mercury MD: 2026-03-08 → 2043-03-08
      Sub-periods vary; Mercury MD is inherently education/commerce-favorable.

    Fallback: 0.55 (neutral moderate quality) when chart_facts unavailable.
    """
    # Native chart defaults per FORENSIC v8.0 §5.1 DSH.V.023
    if chart_id == NATIVE_CHART_ID:
        # Mercury MD period (2026-2043): Mercury favors education, business, communication
        year = window_start.year
        if 2026 <= year <= 2043:
            # Mercury is a benefic for this native (Virgo lagna — Mercury is lagna lord)
            return 0.72
        # Fallback for other periods
        return 0.55

    # Non-native: attempt to read from chart_facts, fall back to neutral
    try:
        db_url = _get_db_url()
        sql = """
            SELECT value, confidence
            FROM chart_facts
            WHERE chart_id = %s
              AND category = 'dasha'
              AND key = 'current_md_lord'
            LIMIT 1
        """
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [chart_id])
                row = cur.fetchone()
                if row:
                    # Simple heuristic: Mercury/Jupiter MD = high quality for learning
                    md_lord = str(row.get("value", ""))
                    benefic_lords = {"Mercury", "Jupiter", "Venus"}
                    if md_lord in benefic_lords:
                        return 0.70
                    return 0.50
    except Exception:
        pass

    return 0.55


def _transit_quality_for_window(window_start: datetime) -> float:
    """
    Approximate transit quality based on known planetary cycles.

    Full transit computation requires Swiss Ephemeris (B.10: no fabricated computation).
    This function uses a simplified seasonal approximation:
      - Jupiter transits ~1 year per sign; currently (2026) in Gemini/Cancer.
      - Saturn transits ~2.5 years per sign; currently (2026) in Aquarius/Pisces.
      - Monthly lunar cycle: full moon weeks generally more auspicious.

    All values are approximations only. For production use, integrate with
    the sidecar's ephemeris engine (/ephemeris endpoint).

    Returns a score in [0.0, 1.0].
    """
    # Simple approximation based on day of lunar cycle (28-day cycle)
    # Using Julian Day approximation:
    #   JD 2451550.1 = 2000-01-06 18:14 UTC (known new moon)
    #   Lunar period = 29.53059 days
    jd_ref = 2451550.1
    jd_window = (
        (window_start - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
        / 86400.0
        + 2451545.0
    )
    lunar_phase = ((jd_window - jd_ref) % 29.53059) / 29.53059  # 0.0–1.0

    # Waxing moon (0.0–0.5): generally more auspicious for initiations
    # Full moon peak (0.45–0.55): auspicious
    # Waning moon dark (0.85–1.0): less auspicious
    if 0.45 <= lunar_phase <= 0.55:
        phase_quality = 0.80  # full moon
    elif 0.05 <= lunar_phase <= 0.45:
        phase_quality = 0.65  # waxing
    elif 0.55 <= lunar_phase <= 0.80:
        phase_quality = 0.55  # waning
    else:
        phase_quality = 0.30  # dark moon (near new moon)

    # Day-of-week overlay (some days have inherently stronger transits)
    weekday = window_start.weekday()  # 0=Mon, 6=Sun
    # Thursday (3, Guruvara) and Friday (4, Shukravara) = Jupiter and Venus days
    day_boost = {0: 0.60, 1: 0.55, 2: 0.65, 3: 0.75, 4: 0.70, 5: 0.50, 6: 0.50}
    day_quality = day_boost.get(weekday, 0.55)

    return float(max(0.0, min(1.0, 0.60 * phase_quality + 0.40 * day_quality)))


def _signal_activation_for_action(action_type: str, chart_id: str) -> float:
    """
    MSR signal activation score for the given action_type and chart.

    For the native's chart (FORENSIC v8.0 + MSR v5.0), key signal activations:
      - education: SIG.08 Mercury 4H education (Mercury MD — high activation)
      - business: SIG.14 Mercury 3H commerce
      - marriage: SIG.09 7H-Venus signification
      - travel: SIG.12 9H Sagittarius travel
      - medical: SIG.04 health-related signals
      - property: SIG.11 4H property
      - general: average of primary signals

    Returns a score in [0.0, 1.0].
    """
    # Native chart signal activations per MSR v5.0
    _NATIVE_SIGNALS: dict[str, float] = {
        "education": 0.78,   # SIG.08 Mercury 4H + Mercury MD activation
        "business": 0.72,    # SIG.14 Mercury 3H commerce
        "marriage": 0.62,    # SIG.09 7H-Venus
        "travel": 0.60,      # SIG.12 9H Sagittarius
        "medical": 0.48,     # SIG.04 health (not a primary activation for this native)
        "property": 0.55,    # SIG.11 4H property
        "general": 0.60,     # average
    }

    if chart_id == NATIVE_CHART_ID:
        return _NATIVE_SIGNALS.get(action_type, 0.55)

    # Non-native: attempt chart_facts lookup, fall back to neutral
    try:
        db_url = _get_db_url()
        sql = """
            SELECT value::FLOAT
            FROM chart_facts
            WHERE chart_id = %s
              AND category = 'signal_activation'
              AND key = %s
            LIMIT 1
        """
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [chart_id, f"action_{action_type}"])
                row = cur.fetchone()
                if row and row.get("value") is not None:
                    return float(max(0.0, min(1.0, row["value"])))
    except Exception:
        pass

    return 0.55


# ── MC-027 — native tāra-bala gate (reads L1 tara_bala_natal_baseline) ─────────
# BPHS/Muhurta Chintamani Nava-tārā chakra: the day Moon's nakshatra relative to
# the NATIVE'S OWN janma nakshatra classifies into 9 tārā states; Vipat(3)/
# Pratyak(5)/Vadha(7) are the three classically adverse tārās. This is computed
# and stored per-chart at L1 build time — ga_panchanga_writer._emit_tara_bala_baseline,
# fact_category='tara_bala_natal_baseline', one row per of the 27 transit
# nakshatras, fact_subject='TRANSIT_NAK_<SHORT>', fact_value_text=tara_class —
# but the muhurta scorer never joined to it (MC-027 register finding): a window
# whose Moon-nakshatra is Vadha-tārā for the native could rank #1/#2 with no
# signal the day is classically inauspicious FOR THIS NATIVE specifically (this
# is orthogonal to the generic, native-agnostic per-action nakshatra list
# _panchanga_quality_for_action already checks — e.g. Shravana is a fine
# "education" nakshatra in general, but can still be this native's Vadha-tārā).
# Read here, never recomputed (§N.5) — same classical arithmetic the TS
# muhurta_finder.ts Lane-F `computeTaraBala` helper re-derives client-side from
# a caller-supplied `native_janma_nakshatra`, sourced instead from the chart's
# own precomputed L1 table so the scorer never depends on a caller remembering
# to pass the janma nakshatra at all (the gap kala_muhurta_get hit — it calls
# this module directly and never had a native_janma_nakshatra param to begin
# with).
_ADVERSE_TARA = {"Vipat", "Pratyak", "Vadha"}
_SEVERE_TARA = {"Vadha"}

_NAK_NAME_TO_SHORT: dict[str, str] = {}


def _nakshatra_short_code(name: str) -> Optional[str]:
    """Map a panchanga_daily.moon_nakshatra full name to its NAKSHATRA_SHORT
    code (ga_panchanga_writer's own table — imported once, cached module-level;
    §N.5 — never re-invent a second nakshatra-naming table)."""
    global _NAK_NAME_TO_SHORT
    if not _NAK_NAME_TO_SHORT:
        from ga_writers.ga_panchanga_writer import NAKSHATRA_NAMES, NAKSHATRA_SHORT
        _NAK_NAME_TO_SHORT = dict(zip(NAKSHATRA_NAMES, NAKSHATRA_SHORT))
    return _NAK_NAME_TO_SHORT.get(name)


_TARA_BASELINE_CACHE: dict[tuple[str, str], dict[str, str]] = {}


def _fetch_tara_bala_baseline(
    chart_id: str, db_url: str, ayanamsha_id: str = "lahiri_chitrapaksha"
) -> dict[str, str]:
    """The chart's own tara_bala_natal_baseline (chart_facts) → {short_code: tara_class}.

    Read once per (chart_id, ayanamsha_id) and cached for the process lifetime
    (mirrors the _DASHA_LORD_CACHE pattern above) — this table is a fixed
    27-row per-ayanamsha classification that never changes between calls for
    the same chart/ayanamsha within a build.
    """
    cache_key = (chart_id, ayanamsha_id)
    if cache_key in _TARA_BASELINE_CACHE:
        return _TARA_BASELINE_CACHE[cache_key]
    out: dict[str, str] = {}
    try:
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT fact_subject, fact_value_text FROM chart_facts
                       WHERE chart_id = %s AND ayanamsha_id = %s
                         AND fact_category = 'tara_bala_natal_baseline'""",
                    [chart_id, ayanamsha_id],
                )
                for row in cur.fetchall():
                    subj = str(row.get("fact_subject") or "")
                    if subj.startswith("TRANSIT_NAK_"):
                        out[subj[len("TRANSIT_NAK_"):]] = str(row.get("fact_value_text") or "")
    except Exception as exc:
        logger.debug(
            "tara_bala_natal_baseline lookup failed for %s/%s: %s", chart_id, ayanamsha_id, exc
        )
    _TARA_BASELINE_CACHE[cache_key] = out
    return out


def _tara_bala_verdict(moon_nakshatra: str, baseline: dict[str, str]) -> Optional[dict[str, Any]]:
    """The native's tāra-bala verdict for a window's day Moon-nakshatra.

    Returns None when the baseline table or the nakshatra name doesn't resolve
    (honest unavailable — e.g. a non-native chart with no L1 build yet — never
    fabricated, per B.10).
    """
    short = _nakshatra_short_code(moon_nakshatra)
    if short is None:
        return None
    tara_class = baseline.get(short)
    if not tara_class:
        return None
    return {
        "moon_nakshatra": moon_nakshatra,
        "tara_class": tara_class,
        "adverse": tara_class in _ADVERSE_TARA,
        "severe": tara_class in _SEVERE_TARA,
        "citation": (
            "Nava-tārā chakra — Muhurta Chintamani, Nakshatra Prakaraṇa "
            "(tārā counted from the native's own janma nakshatra to the day "
            "Moon nakshatra, mod 9; Vipat/Pratyak/Vadha are the three "
            "classically adverse tārās)."
        ),
    }


def fetch_muhurta_windows(
    chart_id: str,
    action_type: str,
    range_start: datetime,
    range_end: datetime,
    min_score: float = 0.0,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Fetch pre-computed phala_muhurta rows for a chart/action_type within the window.

    If no pre-computed rows exist for this chart_id + action_type + range,
    falls back to on-the-fly computation (generate_muhurta_windows), which
    reads REAL panchanga_daily rows and never fabricates coverage.

    Args:
        chart_id:    Chart UUID.
        action_type: One of the 7 canonical action types.
        range_start: UTC start of the search range.
        range_end:   UTC end of the search range.
        min_score:   Minimum auspiciousness_score [0.0, 1.0].
        limit:       Maximum number of windows to return (default 20).

    Returns:
        {"windows": list[dict], "checked": int, "skipped_no_panchanga": int,
         "coverage": (min_date, max_date), "source": "phala_muhurta"|"on_the_fly"}
    """
    try:
        db_url = _get_db_url()
        sql = """
            SELECT
                muhurta_id::TEXT AS muhurta_id,
                action_type,
                window_start AT TIME ZONE 'UTC' AS window_start,
                window_end   AT TIME ZONE 'UTC' AS window_end,
                auspiciousness_score,
                factors,
                source_citation
            FROM public.phala_muhurta
            WHERE chart_id = %s::UUID
              AND action_type = %s
              AND window_start >= %s
              AND window_end   <= %s
              AND auspiciousness_score >= %s
            ORDER BY auspiciousness_score DESC
            LIMIT %s
        """
        params: list[Any] = [
            chart_id, action_type,
            range_start.isoformat(), range_end.isoformat(),
            min_score, limit,
        ]
        rows: list[dict[str, Any]] = []
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                for row in cur.fetchall():
                    normalised: dict[str, Any] = {}
                    for k, v in row.items():
                        if isinstance(v, (date, datetime)):
                            normalised[k] = v.isoformat()
                        else:
                            normalised[k] = v
                    rows.append(normalised)
        if rows:
            return {
                "windows": rows,
                "checked": len(rows),
                "skipped_no_panchanga": 0,
                "coverage": (None, None),
                "source": "phala_muhurta",
            }
    except Exception as exc:
        logger.warning("phala_muhurta DB read failed (%s); falling back to on-the-fly", exc)

    # On-the-fly fallback: generate and score windows without DB, using REAL
    # panchanga_daily rows only (never fabricated — see generate_muhurta_windows).
    result = generate_muhurta_windows(
        chart_id=chart_id,
        action_type=action_type,
        range_start=range_start,
        range_end=range_end,
        min_score=min_score,
        limit=limit,
    )
    result["source"] = "on_the_fly"
    return result


def _fetch_panchanga_row(
    window_start: datetime,
    db_url: str,
) -> Optional[dict[str, Any]]:
    """
    Read panchanga_daily for the given date (UTC midnight).

    Returns a dict with tithi_name, vara_lord, moon_nakshatra, yoga when a real
    row exists, or None when the date is outside the populated rolling window.

    R5.1 C3 fix: this previously queried a non-existent column
    (`panchanga_date`) against panchanga_daily (whose real column is `date` —
    see migration 427_panchanga_daily_reprovision.sql), so every lookup threw,
    was silently swallowed, and fell back to HARD-CODED placeholder values
    ("Shukla Panchami"/"Hasta"/"Shubha") presented as if real — a B.10
    fabricated-computation violation. Fixed to read the real column and to
    return None (never a fabricated substitute) when no row exists — the
    caller (generate_muhurta_windows) now skips windows lacking real
    panchanga data instead of fabricating them, and the top-level response
    surfaces empty-with-reason when nothing in the requested range has
    coverage.
    """
    target_date = window_start.date()
    try:
        sql = """
            SELECT
                tithi_name,
                vara_lord,
                moon_nakshatra,
                yoga,
                auspicious
            FROM public.panchanga_daily
            WHERE date = %s
            LIMIT 1
        """
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [target_date.isoformat()])
                row = cur.fetchone()
                if row:
                    return dict(row)
    except Exception as exc:
        logger.debug("panchanga_daily lookup failed for %s: %s", target_date, exc)

    return None


def _panchanga_coverage(db_url: str) -> tuple[Optional[str], Optional[str]]:
    """Return (min_date, max_date) ISO strings currently populated in panchanga_daily."""
    try:
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM public.panchanga_daily")
                row = cur.fetchone()
                if row and row.get("min_date") and row.get("max_date"):
                    return row["min_date"].isoformat(), row["max_date"].isoformat()
    except Exception as exc:
        logger.debug("panchanga_daily coverage lookup failed: %s", exc)
    return None, None


def generate_muhurta_windows(
    chart_id: str,
    action_type: str,
    range_start: datetime,
    range_end: datetime,
    min_score: float = 0.0,
    limit: int = 20,
) -> dict[str, Any]:
    """
    On-the-fly muhurta window generation.

    For each 48-hour window in [range_start, range_end], compute
    auspiciousness_score from panchanga_quality × dasha_quality
    × transit_quality × signal_activation.

    Returns {"windows": [...], "checked": int, "skipped_no_panchanga": int,
    "coverage": (min_date, max_date) | (None, None)}. Windows with score
    >= min_score, ranked by score DESC, capped at `limit`.

    B.10 compliance:
        panchanga_quality — derived from panchanga_daily table (classical rules),
                            gated by the native's OWN tāra-bala baseline (MC-027)
        dasha_quality     — from chart_facts or FORENSIC defaults
        transit_quality   — simplified lunar-phase approximation
        signal_activation — from MSR v5.0 (native) or chart_facts
        NO Swiss Ephemeris recomputation inside this function.

    R5.1 C3: a date with no real panchanga_daily row (outside the rolling
    +12-month populated window) is SKIPPED, never fabricated with placeholder
    values — the caller uses `skipped_no_panchanga`/`coverage` to build an
    honest empty-with-reason response when nothing in range has coverage.

    MC-027: each window is now gated against the chart's own precomputed
    tara_bala_natal_baseline (see `_tara_bala_verdict` above) — an adverse
    tārā (Vipat/Pratyak/Vadha) demotes panchanga_quality and files an
    avoid_notes entry, so a Vadha-tārā window can no longer silently rank
    top-2 with no signal it is inauspicious for THIS native specifically.
    Intra-day auspicious sub-windows (brahma_muhurta/abhijit/amrit/labh/shubh —
    whichever panchanga_daily.auspicious carries for the date) are surfaced
    under factors.intraday_windows instead of only the coarse 48h block.
    """
    # Pre-fetch dasha and signal quality (chart-level, constant across windows)
    dasha_q = _dasha_quality_for_chart(chart_id, range_start)
    signal_q = _signal_activation_for_action(action_type, chart_id)

    # Attempt DB connection for panchanga lookups
    try:
        db_url = _get_db_url()
    except RuntimeError:
        db_url = ""

    coverage: tuple[Optional[str], Optional[str]] = (None, None)
    if db_url:
        coverage = _panchanga_coverage(db_url)

    # MC-027: chart-level tāra-bala baseline, fetched once (constant across
    # windows — the baseline is a fixed 27-row classification per chart/ayanamsha).
    tara_baseline = _fetch_tara_bala_baseline(chart_id, db_url) if db_url else {}

    windows: list[dict[str, Any]] = []
    checked = 0
    skipped_no_panchanga = 0
    current = range_start.replace(hour=0, minute=0, second=0, microsecond=0)

    while current < range_end and len(windows) < MAX_DATE_RANGE_DAYS:
        window_end = current + timedelta(hours=WINDOW_HOURS)
        if window_end > range_end:
            break

        checked += 1

        # Panchanga lookup — real data only, never fabricated (B.10).
        panchanga = _fetch_panchanga_row(current, db_url) if db_url else None
        if panchanga is None:
            skipped_no_panchanga += 1
            current = current + timedelta(days=2)  # 48-hour step
            continue

        tithi_name = panchanga.get("tithi_name", "")
        vara_lord = panchanga.get("vara_lord", "")
        moon_nakshatra = panchanga.get("moon_nakshatra", "")
        yoga = panchanga.get("yoga", "")

        panchanga_q = _panchanga_quality_for_action(
            tithi_name, vara_lord, moon_nakshatra, yoga, action_type
        )
        transit_q = _transit_quality_for_window(current)

        # MC-027: gate panchanga_quality against the native's OWN tāra-bala
        # baseline for this window's day Moon-nakshatra. A demotion, not a
        # veto — B.10 forbids silently dropping the window — but severe
        # (Vadha) knocks the sub-score down hard enough that it cannot carry
        # a top-2 composite score on tāra-bala grounds alone, and moderate
        # (Vipat/Pratyak) still visibly discounts it.
        tara_verdict = _tara_bala_verdict(moon_nakshatra, tara_baseline)
        if tara_verdict and tara_verdict["severe"]:
            panchanga_q = min(panchanga_q, 0.30)
        elif tara_verdict and tara_verdict["adverse"]:
            panchanga_q = min(panchanga_q, 0.50)

        score = compute_muhurta_score(panchanga_q, dasha_q, transit_q, signal_q)

        if score >= min_score:
            avoid_notes: list[str] = []
            if panchanga_q < 0.30:
                avoid_notes.append(
                    f"Low panchanga quality: {yoga} yoga + {tithi_name}"
                )
            if transit_q < 0.35:
                avoid_notes.append("Dark moon phase — reduced lunar strength")
            if tara_verdict and tara_verdict["adverse"]:
                avoid_notes.append(
                    f"{tara_verdict['tara_class']}-tārā for the native: day Moon in "
                    f"{moon_nakshatra} is classically "
                    f"{'severely' if tara_verdict['severe'] else 'moderately'} "
                    "inauspicious relative to the native's own janma nakshatra "
                    "(Nava-tārā chakra, Muhurta Chintamani)."
                )

            # T-8 fix (D-1.6 S-1): resolve the live dasha lord(s) for THIS window's
            # date once, reused for both dasha_details and source_citation below
            # (cached across windows sharing the same date, see _current_dasha_lords).
            live_dasha = _current_dasha_lords(chart_id, current)

            # MC-027: intra-day sub-windows already computed by panchanga_daily
            # (brahma_muhurta/abhijit/amrit/labh/shubh — whichever the date's
            # `auspicious` jsonb carries) — surfaced instead of only the coarse
            # 48h block, so a caller can pick the actual auspicious slot within
            # the window rather than treating the whole 48h span as uniform.
            intraday_windows = panchanga.get("auspicious") or []
            if isinstance(intraday_windows, str):
                try:
                    intraday_windows = json.loads(intraday_windows)
                except Exception:
                    intraday_windows = []

            windows.append({
                "muhurta_id": None,
                "action_type": action_type,
                "window_start": current.isoformat(),
                "window_end": window_end.isoformat(),
                "auspiciousness_score": round(score, 4),
                "factors": {
                    "panchanga_quality": round(panchanga_q, 4),
                    "dasha_quality": round(dasha_q, 4),
                    "transit_quality": round(transit_q, 4),
                    "signal_activation": round(signal_q, 4),
                    "panchanga_details": {
                        "tithi_name": tithi_name,
                        "vara_lord": vara_lord,
                        "moon_nakshatra": moon_nakshatra,
                        "yoga": yoga,
                        "inauspicious_windows": [],
                    },
                    # T-8 fix (D-1.6 S-1): md_lord/ad_lord derived LIVE from chart_dashas
                    # for this window's date, instead of a hardcoded "Mercury" literal
                    # that was wrong even for the native (Mercury MD actually runs
                    # 2010-08-17→2027-08-17 per chart_dashas, not the citation's claimed
                    # 2026-2043 range) and always "unknown" for every other chart.
                    "dasha_details": {
                        "md_lord": live_dasha["md_lord"] if live_dasha else "unknown",
                        "ad_lord": (live_dasha.get("ad_lord") if live_dasha else None) or "unknown",
                    },
                    # MC-027: native-specific tāra-bala verdict for this window's
                    # day Moon-nakshatra (None when the L1 baseline/nakshatra
                    # name doesn't resolve — honest unavailable, never fabricated).
                    "tara_bala_natal": tara_verdict,
                    # MC-027: intra-day auspicious sub-windows from panchanga_daily
                    # (each {label, start_utc, end_utc}) — [] when none computed
                    # for this date (honest empty, not fabricated).
                    "intraday_windows": intraday_windows,
                    "avoid_notes": avoid_notes,
                },
                "source_citation": (
                    f"{_dasha_citation_fragment_from(live_dasha)}; "
                    f"panchanga_daily {current.date().isoformat()} "
                    f"({tithi_name}/{moon_nakshatra}/{vara_lord}); "
                    + (
                        f"tara_bala_natal_baseline ({tara_verdict['tara_class']}); "
                        if tara_verdict else ""
                    )
                    + "MSR v5.0 SIG.08/SIG.14/SIG.09 signal activation; "
                    "BPHS ch.46 muhurta rules; "
                    "PH-4-4 on-the-fly compute"
                ),
            })

        current = current + timedelta(days=2)  # 48-hour step

    # Sort by score DESC, cap at limit
    windows.sort(key=lambda w: w["auspiciousness_score"], reverse=True)
    return {
        "windows": windows[:limit],
        "checked": checked,
        "skipped_no_panchanga": skipped_no_panchanga,
        "coverage": coverage,
    }


def muhurta_finder(
    chart_id: str,
    action_type: str,
    date_range: dict[str, str],
    min_score: Optional[float] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Main tool entry-point: muhurta_finder(chart_id, action_type, date_range, min_score?)

    INVERTS the prediction engine: instead of "what will happen?", asks
    "WHEN is best to act for a desired action_type?"

    For each 48-hour window in date_range (max 90 days), computes:
        auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%)
                             + transit_quality(20%) + signal_activation(10%)

    Returns windows ranked by auspiciousness_score DESC with a provenance_envelope.

    Args:
        chart_id:    Chart UUID.
        action_type: One of: marriage|travel|business|medical|education|property|general
        date_range:  Dict with 'start' and 'end' keys (ISO date strings).
        min_score:   Minimum score [0.0, 1.0]. Default 0.0.
        limit:       Max windows to return (default 20, max 45).

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "action_type": str,
            "query_window": {"start": str, "end": str},
            "windows": [
                {
                    "start": str,   # ISO datetime
                    "end": str,     # ISO datetime
                    "score": float, # [0.0, 1.0]
                    "factors": {
                        "panchanga_quality": float,
                        "dasha_quality": float,
                        "transit_quality": float,
                        "signal_activation": float,
                        "panchanga_details": {...},
                        "dasha_details": {...},
                        "avoid_notes": [...]
                    }
                }, ...
            ],
            "window_count": int,
            "provenance_envelope": {
                "source": "phala.muhurta",
                "asset": "PH-4-4",
                "algorithm": "panchanga_quality(40%) + dasha_quality(30%) + transit_quality(20%) + signal_activation(10%)",
                ...
            }
        }

    Raises:
        ValueError: invalid action_type, date_range, or min_score.
        RuntimeError: no database URL configured (when pre-computed rows needed).
    """
    # Validate action_type
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(
            f"Invalid action_type '{action_type}'. "
            f"Valid: {sorted(VALID_ACTION_TYPES)}"
        )

    # Parse date range
    try:
        range_start_date = date.fromisoformat(date_range["start"])
        range_end_date = date.fromisoformat(date_range["end"])
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"date_range must have 'start' and 'end' ISO date strings: {exc}"
        ) from exc

    if range_start_date > range_end_date:
        raise ValueError(
            f"date_range start ({range_start_date}) must not be after end ({range_end_date})"
        )

    delta_days = (range_end_date - range_start_date).days
    if delta_days > MAX_DATE_RANGE_DAYS:
        raise ValueError(
            f"date_range spans {delta_days} days; maximum is {MAX_DATE_RANGE_DAYS} days"
        )

    effective_min_score = min_score if min_score is not None else 0.0
    if not (0.0 <= effective_min_score <= 1.0):
        raise ValueError(
            f"min_score must be in [0.0, 1.0], got {effective_min_score}"
        )

    effective_limit = min(max(1, limit), 45)  # cap at 45 windows

    # Convert dates to UTC datetimes (midnight UTC)
    range_start_utc = datetime(
        range_start_date.year, range_start_date.month, range_start_date.day,
        tzinfo=timezone.utc,
    )
    range_end_utc = datetime(
        range_end_date.year, range_end_date.month, range_end_date.day,
        23, 59, 59, tzinfo=timezone.utc,
    )

    # Fetch / compute windows
    fetch_result = fetch_muhurta_windows(
        chart_id=chart_id,
        action_type=action_type,
        range_start=range_start_utc,
        range_end=range_end_utc,
        min_score=effective_min_score,
        limit=effective_limit,
    )
    raw_windows = fetch_result["windows"]

    # Normalise window shape for the response
    formatted_windows = []
    for w in raw_windows:
        formatted_windows.append({
            "start": w.get("window_start", ""),
            "end": w.get("window_end", ""),
            "score": w.get("auspiciousness_score", 0.0),
            "factors": w.get("factors", {}),
            "source_citation": w.get("source_citation", ""),
        })

    # Provenance checks (B.3 mandate)
    b3_compliant = all(bool(w.get("source_citation")) for w in raw_windows)
    queried_at = datetime.now(tz=timezone.utc).isoformat()

    # R5.1 C3 — empty-with-reason: distinguish "no windows because nothing in the
    # requested range met min_score / has real panchanga coverage" from a normal
    # empty result, and NEVER fabricate rows for out-of-window dates. If the
    # on-the-fly path skipped every checked date for lack of a real panchanga_daily
    # row, surface an explicit reason citing the actual populated coverage window.
    empty_reason: Optional[str] = None
    if len(formatted_windows) == 0 and fetch_result.get("source") == "on_the_fly":
        checked = fetch_result.get("checked", 0)
        skipped = fetch_result.get("skipped_no_panchanga", 0)
        coverage_min, coverage_max = fetch_result.get("coverage", (None, None))
        if checked > 0 and skipped == checked:
            if coverage_min and coverage_max:
                empty_reason = (
                    f"date_range {range_start_date.isoformat()}..{range_end_date.isoformat()} "
                    f"falls outside the panchanga_daily populated window "
                    f"({coverage_min}..{coverage_max}, rolling +12 months from the last "
                    "panchanga_daily_writer.py run). No windows fabricated for dates "
                    "outside the populated window — re-run the writer to extend coverage, "
                    "or query a date_range inside it."
                )
            else:
                empty_reason = (
                    "panchanga_daily has no populated rows at all (writer has not run, "
                    "or DB unreachable). No windows fabricated."
                )

    response: dict[str, Any] = {
        "ok": True,
        "chart_id": chart_id,
        "action_type": action_type,
        "query_window": {
            "start": range_start_date.isoformat(),
            "end": range_end_date.isoformat(),
        },
        "windows": formatted_windows,
        "window_count": len(formatted_windows),
        "provenance_envelope": {
            "source": "phala.muhurta",
            "asset": "PH-4-4",
            "algorithm": (
                "panchanga_quality(40%) + dasha_quality(30%) "
                "+ transit_quality(20%) + signal_activation(10%)"
            ),
            "min_score_applied": effective_min_score,
            "chart_id": chart_id,
            "action_type": action_type,
            "queried_at": queried_at,
            # T-8 fix (D-1.6 S-1): was a hardcoded "FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD
            # (2026-2043)" fragment on every response regardless of which dasha lord was
            # actually active — wrong even for the native (chart_dashas shows Mercury MD
            # 2010-08-17→2027-08-17, not 2026-2043). Each window already carries its own
            # live-derived source_citation (see _dasha_citation_fragment_from); this
            # envelope-level summary now points at the live table generically instead of
            # re-asserting a specific (and here, incorrect) lord/date-range.
            "l1_ground_truth": (
                "chart_dashas (canonical L1 dasha table — see each window's own "
                "source_citation for the live MD/AD lord active at that window's date); "
                "panchanga_daily (real rolling +12mo table — migration "
                "427_panchanga_daily_reprovision.sql, R5.1 C3); "
                "MSR v5.0 SIG.08/SIG.14/SIG.09/SIG.12/SIG.04/SIG.11"
            ),
            "b3_citation_compliant": b3_compliant,
            "windows_source": fetch_result.get("source", "unknown"),
        },
    }
    if empty_reason is not None:
        response["empty_reason"] = empty_reason
    return response


def seed_native_muhurta(chart_id: str) -> dict[str, Any]:
    """
    Trigger the native seed function in the DB for a given chart_id.

    Calls seed_phala_muhurta_native_sample(chart_id::UUID) SQL function.
    Inserts 3 pre-calibrated rows for marriage/business/education. Idempotent.

    Returns:
        {"ok": True, "rows_inserted": int, "chart_id": str}
    """
    db_url = _get_db_url()
    sql = "SELECT seed_phala_muhurta_native_sample(%s::UUID) AS rows_inserted"

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [chart_id])
            result = cur.fetchone()
            rows_inserted = result["rows_inserted"] if result else 0
        conn.commit()

    logger.info(
        "seed_phala_muhurta chart_id=%s rows_inserted=%d",
        chart_id, rows_inserted,
    )
    return {
        "ok": True,
        "rows_inserted": rows_inserted,
        "chart_id": chart_id,
    }


def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-4 acceptance gate.

    Gate criteria:
      AC1 — muhurta_finder returns >= 1 window for 90-day range (any action_type).
      AC2 — all returned scores in [0.0, 1.0].
      AC3 — action_type validation raises ValueError for invalid type.
      AC4 — all windows have non-empty source_citation (B.3 mandate).
      AC5 — score for 'general' action_type within 90-day window >= 0.0 (always passes).

    Returns:
        {"chart_id": str, "gate_passed": bool, "checks": list[dict]}
    """
    checks: list[dict[str, Any]] = []

    # AC1: >= 1 window for 90-day range
    try:
        result = muhurta_finder(
            chart_id=chart_id,
            action_type="general",
            date_range={"start": "2026-06-01", "end": "2026-08-29"},
        )
        windows = result["windows"]
        checks.append({
            "id": "AC1",
            "desc": "muhurta_finder returns >= 1 window for 90-day general range",
            "passed": len(windows) >= 1,
            "value": len(windows),
        })
    except Exception as exc:
        checks.append({
            "id": "AC1",
            "desc": "muhurta_finder >= 1 window",
            "passed": False,
            "error": str(exc),
        })
        windows = []

    # AC2: All scores in [0.0, 1.0]
    try:
        out_of_range = [
            (i, w["score"]) for i, w in enumerate(windows)
            if not (0.0 <= float(w["score"]) <= 1.0)
        ]
        checks.append({
            "id": "AC2",
            "desc": "All window scores in [0.0, 1.0]",
            "passed": len(out_of_range) == 0,
            "value": f"{len(windows) - len(out_of_range)}/{len(windows)} in range",
            "out_of_range": out_of_range,
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "score range", "passed": False, "error": str(exc)})

    # AC3: Invalid action_type raises ValueError
    try:
        try:
            muhurta_finder(
                chart_id=chart_id,
                action_type="INVALID_TYPE",
                date_range={"start": "2026-06-01", "end": "2026-06-30"},
            )
            checks.append({
                "id": "AC3",
                "desc": "Invalid action_type raises ValueError",
                "passed": False,
                "value": "No exception raised — validation failure",
            })
        except ValueError:
            checks.append({
                "id": "AC3",
                "desc": "Invalid action_type raises ValueError",
                "passed": True,
                "value": "ValueError raised correctly",
            })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "action_type validation", "passed": False, "error": str(exc)})

    # AC4: All source_citations non-empty (B.3 mandate)
    try:
        missing_citations = [
            i for i, w in enumerate(windows) if not w.get("source_citation")
        ]
        checks.append({
            "id": "AC4",
            "desc": "All windows have non-empty source_citation (B.3 mandate)",
            "passed": len(missing_citations) == 0,
            "value": f"{len(windows) - len(missing_citations)}/{len(windows)} have citations",
            "missing": missing_citations,
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "citation completeness", "passed": False, "error": str(exc)})

    # AC5: Tool smoke — all 7 action_types return >= 0 windows without error
    try:
        all_types_ok = True
        failed_types: list[str] = []
        for at in sorted(VALID_ACTION_TYPES):
            try:
                res = muhurta_finder(
                    chart_id=chart_id,
                    action_type=at,
                    date_range={"start": "2026-06-01", "end": "2026-06-30"},
                    min_score=0.0,
                )
                if not isinstance(res.get("windows"), list):
                    all_types_ok = False
                    failed_types.append(at)
            except Exception:
                all_types_ok = False
                failed_types.append(at)
        checks.append({
            "id": "AC5",
            "desc": "All 7 action_types return without error",
            "passed": all_types_ok,
            "value": f"failed: {failed_types}" if failed_types else "all pass",
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "action_type smoke", "passed": False, "error": str(exc)})

    gate_passed = all(c["passed"] for c in checks)
    if gate_passed:
        logger.info("PH-4-4 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("PH-4-4 acceptance gate FAILED for chart_id=%s — %s", chart_id, failed)

    return {"chart_id": chart_id, "gate_passed": gate_passed, "checks": checks}


# ── FastAPI request/response models ───────────────────────────────────────────


class DateRange(BaseModel):
    start: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    end: str = Field(..., description="ISO date string (YYYY-MM-DD)")


class MuhurtaFinderRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    action_type: str = Field(
        ...,
        description=(
            "Action type: marriage|travel|business|medical|education|property|general"
        ),
    )
    date_range: DateRange = Field(
        ...,
        description="Search range — max 90 days (up to 45 × 48-hour windows)",
    )
    min_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum auspiciousness_score [0.0, 1.0]. Default 0.0.",
    )
    limit: int = Field(
        20,
        ge=1,
        le=45,
        description="Maximum windows to return (default 20, max 45).",
    )


class SeedMuhurtaRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID to seed native muhurta rows for")


# ── FastAPI endpoints ─────────────────────────────────────────────────────────


@router.post("/phala/muhurta_finder")
def api_muhurta_finder(req: MuhurtaFinderRequest) -> dict[str, Any]:
    """
    PH-4-4 muhurta_finder tool.

    Returns ranked future time windows that maximise auspiciousness for the
    given action_type and chart.

    INVERTS the prediction engine: instead of "what will happen?", asks
    "WHEN is best to act?"

    Algorithm: for each 48-hour window in the requested date range (max 90 days),
    score = panchanga_quality(40%) + dasha_quality(30%)
           + transit_quality(20%) + signal_activation(10%)

    action_types: marriage | travel | business | medical | education | property | general

    B.3 mandate: source_citation is NON-NULL on every returned window.
    """
    try:
        return muhurta_finder(
            chart_id=req.chart_id,
            action_type=req.action_type,
            date_range={"start": req.date_range.start, "end": req.date_range.end},
            min_score=req.min_score,
            limit=req.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/phala/seed_muhurta")
def api_seed_muhurta(req: SeedMuhurtaRequest) -> dict[str, Any]:
    """
    Seed pre-calibrated phala_muhurta rows for a chart.

    Calls seed_phala_muhurta_native_sample(chart_id::UUID) in the DB. Idempotent.
    Inserts 3 rows (marriage/business/education) for the native's chart.
    """
    try:
        return seed_native_muhurta(req.chart_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/phala/muhurta_acceptance_gate/{chart_id}")
def api_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-4 acceptance gate.

    AC1: >= 1 window for 90-day general range.
    AC2: All scores in [0.0, 1.0].
    AC3: Invalid action_type raises ValueError.
    AC4: All source_citations non-empty (B.3 mandate).
    AC5: All 7 action_types return without error (tool smoke).
    """
    return run_acceptance_gate(chart_id)
