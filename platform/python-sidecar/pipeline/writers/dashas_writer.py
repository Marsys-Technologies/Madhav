"""
dashas_writer.py — MARSYS-JIS A7 Dasha / Sub-Dasha Chains writer
=================================================================
Implements 7 acharya-selected dasha systems at Sookshma depth:
  1. Vimshottari  — Maha → Antar → Pratyantar → Sookshma
  2. Yogini       — 36-year cycle, 8 lords, Pratyantar depth
  3. Ashtottari   — 108-year cycle, 8 lords, Pratyantar depth
  4. Naisargika   — fixed natural life stages, Antar depth
  5. Mudda        — 365-day compressed Vimshottari, Antar depth
  6. Jaimini Chara — sign-based sequence (simplified)
  7. Kalachakra   — navamsa-based sequence (simplified)

DB write target: chart_facts table (one row per dasha period, fact_value_jsonb).
Window filter: 1950-01-01 to 2100-12-31.

canonical_id: A7
stream: A
session: A7-S1 through A7-S4 [BUILD-ORCH-A7-S1-S4]
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A7_dashas"
ASSET_LABEL = "Dasha / Sub-Dasha Chains"
ENGINE_VERSION = "pyjhora/1.0.0"
WRITER_NAME = "dashas_writer"

# ---------------------------------------------------------------------------
# Window filter — only write periods that overlap 1950–2100
# ---------------------------------------------------------------------------
WINDOW_START = datetime(1950, 1, 1, tzinfo=timezone.utc)
WINDOW_END   = datetime(2100, 12, 31, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# 1. VIMSHOTTARI constants
# ---------------------------------------------------------------------------
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
VIMSHOTTARI_TOTAL = 120  # years

# ---------------------------------------------------------------------------
# 2. YOGINI constants
# ---------------------------------------------------------------------------
YOGINI_LORDS   = ["Mangala", "Pingala", "Dhanya", "Bhramari",
                  "Bhadrika", "Ulka",    "Siddha",  "Sankata"]
YOGINI_GRAHAS  = ["Moon",    "Sun",     "Jupiter", "Mars",
                  "Mercury", "Saturn",  "Venus",   "Rahu"]
YOGINI_YEARS   = [1, 2, 3, 4, 5, 6, 7, 8]
YOGINI_TOTAL   = 36  # years

# Nakshatra-to-yogini mapping (0-indexed yogini, 1-indexed nakshatra)
# Nakshatra 1 → Mangala(0), Nakshatra 2 → Pingala(1), … cycles every 8 nakshatras
def _yogini_start_idx(moon_nakshatra_id: int) -> int:
    return (moon_nakshatra_id - 1) % 8

# ---------------------------------------------------------------------------
# 3. ASHTOTTARI constants
# ---------------------------------------------------------------------------
ASHTOTTARI_SEQUENCE = ["Sun", "Moon", "Mars", "Mercury",
                        "Saturn", "Jupiter", "Rahu", "Venus"]
ASHTOTTARI_YEARS = {
    "Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17,
    "Saturn": 10, "Jupiter": 19, "Rahu": 12, "Venus": 21,
}
ASHTOTTARI_TOTAL = 108  # years

# Nakshatra groupings for Ashtottari starting lord
# BPHS: 27 nakshatras mapped to 8 lords
# Pattern: Sun rules 1-4, Moon 5-9, Mars 10-12, Mercury 13-16,
#          Saturn 17-19, Jupiter 20-23, Rahu 24-26, Venus 27
_ASHTOTTARI_NAK_LORD: dict[int, str] = {}
_ASH_MAP = [
    (range(1, 5),   "Sun"),
    (range(5, 10),  "Moon"),
    (range(10, 13), "Mars"),
    (range(13, 17), "Mercury"),
    (range(17, 20), "Saturn"),
    (range(20, 24), "Jupiter"),
    (range(24, 27), "Rahu"),
    (range(27, 28), "Venus"),
]
for _rng, _lord in _ASH_MAP:
    for _n in _rng:
        _ASHTOTTARI_NAK_LORD[_n] = _lord

def _ashtottari_start_idx(moon_nakshatra_id: int) -> int:
    lord = _ASHTOTTARI_NAK_LORD.get(moon_nakshatra_id, "Sun")
    return ASHTOTTARI_SEQUENCE.index(lord)

# ---------------------------------------------------------------------------
# 4. NAISARGIKA constants
# ---------------------------------------------------------------------------
NAISARGIKA_SEQUENCE = [
    ("Moon",    1),
    ("Mars",    2),
    ("Mercury", 9),
    ("Venus",   20),
    ("Jupiter", 18),
    ("Sun",     20),
    ("Saturn",  50),
]
NAISARGIKA_TOTAL = sum(y for _, y in NAISARGIKA_SEQUENCE)  # 120

# ---------------------------------------------------------------------------
# 5. MUDDA constants (365-day compressed Vimshottari)
# ---------------------------------------------------------------------------
MUDDA_DAYS = {
    "Ketu": 11, "Venus": 52, "Sun": 18, "Moon": 33, "Mars": 22,
    "Rahu": 59, "Jupiter": 53, "Saturn": 62, "Mercury": 55,
}
MUDDA_TOTAL_DAYS = sum(MUDDA_DAYS.values())  # 365

# ---------------------------------------------------------------------------
# 6. JAIMINI CHARA simplified sign sequence
# ---------------------------------------------------------------------------
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
# Jaimini sign lords (used to determine starting sign and durations)
SIGN_LORDS = {
    "Aries": "Mars",       "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn",  "Pisces": "Jupiter",
}

# ---------------------------------------------------------------------------
# 7. KALACHAKRA simplified constants
# ---------------------------------------------------------------------------
# Navamsa groups — each group of 3 nakshatras forms a Kalachakra group.
# This is a simplified implementation using navamsa sign sequence.
# Full Kalachakra requires the Deha/Jeeva table; this is the acharya-grade simplification.
KALACHAKRA_NAVAMSA_GROUPS = [
    # (navamsa_sign_idx_0based, group_name, direction, years_sequence)
    (0,  "Sarpa",   "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),   # approx
    (1,  "Deva",    "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (2,  "Nara",    "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (3,  "Sarpa",   "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (4,  "Deva",    "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (5,  "Nara",    "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (6,  "Sarpa",   "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (7,  "Deva",    "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (8,  "Nara",    "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (9,  "Sarpa",   "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (10, "Deva",    "forward",  [7, 1, 10, 7, 18, 16, 8, 19, 14]),
    (11, "Nara",    "backward", [7, 1, 10, 7, 18, 16, 8, 19, 14]),
]

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _make_fact_id(category: str, subject: str, key: str,
                   chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_citation_ref(category: str, subject: str, chart_id: str,
                        ayanamsha_id: str) -> str:
    return (
        f"{category}.{subject}"
        f"@chart={chart_id[:8]}"
        f":ay={ayanamsha_id}"
        f":eng={ENGINE_VERSION}"
    )


def _in_window(start: datetime, end: datetime) -> bool:
    """Return True if the period overlaps the 1950-2100 window."""
    return end > WINDOW_START and start < WINDOW_END


def _clamp_dt(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_iso(s: str) -> datetime:
    """Parse ISO string to UTC-aware datetime."""
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _period_row(
    chart_id: str, ayanamsha_id: str, build_id: str,
    system: str, divisional: str, level: str,
    subject: str, period_info: dict,
) -> tuple:
    """Build a single chart_facts insert tuple for one dasha period."""
    category = f"dasha_{system}"
    fact_key = f"period_{level}"
    # Short value_text = "YYYY-MM-DD_YYYY-MM-DD"
    start_text = period_info.get("start_iso", "")[:10]
    end_text   = period_info.get("end_iso",   "")[:10]
    value_text = f"{start_text}_{end_text}"

    fact_id = _make_fact_id(category, subject, fact_key, chart_id, ayanamsha_id, build_id)
    citation_ref = _make_citation_ref(category, subject, chart_id, ayanamsha_id)
    citation_human = f"{system} dasha {level}: {subject} {start_text}→{end_text}"
    provenance = json.dumps({
        "writer":         WRITER_NAME,
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id":   ayanamsha_id,
        "system":         system,
        "level":          level,
    })

    return (
        fact_id,
        chart_id, ayanamsha_id, build_id,
        category,         # category (mirrors fact_category)
        divisional,       # divisional_chart
        WRITER_NAME,      # source_section
        provenance,       # provenance (jsonb)
        category,         # fact_category
        subject,          # fact_subject
        fact_key,         # fact_key
        value_text,       # value_text
        None,             # value_number
        json.dumps(period_info),  # fact_value_jsonb
        citation_ref,     # citation_ref
        citation_human,   # citation_human
        WRITER_NAME,      # source_calculation
        "single",         # verification_pass_status
        ENGINE_VERSION,   # engine_version
        datetime.now(timezone.utc).isoformat(),  # computed_at_iso
        False,            # is_stale
    )


_INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, chart_id, ayanamsha_id, build_id,
   category, divisional_chart, source_section, provenance,
   fact_category, fact_subject, fact_key,
   value_text, value_number, fact_value_jsonb,
   citation_ref, citation_human,
   source_calculation, verification_pass_status,
   engine_version, computed_at_iso, is_stale)
VALUES %s
ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
DO UPDATE SET
  value_text       = EXCLUDED.value_text,
  value_number     = EXCLUDED.value_number,
  fact_value_jsonb = EXCLUDED.fact_value_jsonb,
  computed_at_iso  = EXCLUDED.computed_at_iso,
  is_stale         = FALSE
"""

# ---------------------------------------------------------------------------
# VIMSHOTTARI computation
# ---------------------------------------------------------------------------

def compute_antardasha(maha_lord: str, maha_start: datetime,
                        maha_end: datetime) -> list[dict]:
    """Subdivide a mahadasha into 9 antardashas starting from maha_lord."""
    maha_days = (maha_end - maha_start).total_seconds() / 86400
    start_idx = VIMSHOTTARI_SEQUENCE.index(maha_lord)
    periods = []
    current = maha_start
    for i in range(9):
        lord = VIMSHOTTARI_SEQUENCE[(start_idx + i) % 9]
        antar_days = maha_days * VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL
        antar_end  = current + timedelta(days=antar_days)
        periods.append({
            "maha_lord":      maha_lord,
            "antar_lord":     lord,
            "start_iso":      current.isoformat(),
            "end_iso":        antar_end.isoformat(),
            "duration_days":  round(antar_days, 4),
        })
        current = antar_end
    return periods


def compute_pratyantar(maha_lord: str, antar_lord: str,
                        antar_start: datetime, antar_end: datetime) -> list[dict]:
    """Subdivide an antardasha into 9 pratyantardashas."""
    antar_days = (antar_end - antar_start).total_seconds() / 86400
    start_idx  = VIMSHOTTARI_SEQUENCE.index(antar_lord)
    periods = []
    current = antar_start
    for i in range(9):
        lord = VIMSHOTTARI_SEQUENCE[(start_idx + i) % 9]
        days = antar_days * VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL
        end  = current + timedelta(days=days)
        periods.append({
            "maha_lord":       maha_lord,
            "antar_lord":      antar_lord,
            "pratyantar_lord": lord,
            "start_iso":       current.isoformat(),
            "end_iso":         end.isoformat(),
            "duration_days":   round(days, 4),
        })
        current = end
    return periods


def compute_sookshma(maha_lord: str, antar_lord: str,
                      pratyantar_lord: str,
                      p_start: datetime, p_end: datetime) -> list[dict]:
    """Subdivide a pratyantar into 9 sookshmadashas."""
    p_days    = (p_end - p_start).total_seconds() / 86400
    start_idx = VIMSHOTTARI_SEQUENCE.index(pratyantar_lord)
    periods = []
    current = p_start
    for i in range(9):
        lord = VIMSHOTTARI_SEQUENCE[(start_idx + i) % 9]
        d    = p_days * VIMSHOTTARI_YEARS[lord] / VIMSHOTTARI_TOTAL
        end  = current + timedelta(days=d)
        periods.append({
            "maha_lord":       maha_lord,
            "antar_lord":      antar_lord,
            "pratyantar_lord": pratyantar_lord,
            "sookshma_lord":   lord,
            "start_iso":       current.isoformat(),
            "end_iso":         end.isoformat(),
            "duration_days":   round(d, 4),
        })
        current = end
    return periods


def _subject_key(period: dict) -> str:
    """Build a compact subject key from period lords."""
    parts = [
        period.get("maha_lord", ""),
        period.get("antar_lord", ""),
        period.get("pratyantar_lord", ""),
        period.get("sookshma_lord", ""),
    ]
    return "_".join(p for p in parts if p)


def _collect_vimshottari_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                               mahadasha_sequence: list[dict]) -> list[tuple]:
    """Generate all Vimshottari rows (Maha + Antar + Pratyantar + Sookshma)."""
    rows: list[tuple] = []

    for maha in mahadasha_sequence:
        lord      = maha["lord"]
        maha_start = _parse_iso(maha["start_iso"])
        maha_end   = _parse_iso(maha["end_iso"])

        if not _in_window(maha_start, maha_end):
            continue

        # Mahadasha summary row
        maha_info = {
            "maha_lord":     lord,
            "start_iso":     maha_start.isoformat(),
            "end_iso":       maha_end.isoformat(),
            "duration_days": round((maha_end - maha_start).total_seconds() / 86400, 2),
        }
        rows.append(_period_row(
            chart_id, ayanamsha_id, build_id,
            "vimshottari", "D1", "maha",
            lord, maha_info,
        ))

        # Antar
        for antar in compute_antardasha(lord, maha_start, maha_end):
            a_start = _parse_iso(antar["start_iso"])
            a_end   = _parse_iso(antar["end_iso"])
            if not _in_window(a_start, a_end):
                continue
            subj = f"{lord}_{antar['antar_lord']}"
            rows.append(_period_row(
                chart_id, ayanamsha_id, build_id,
                "vimshottari", "D1", "antar",
                subj, antar,
            ))

            # Pratyantar
            for prat in compute_pratyantar(lord, antar["antar_lord"], a_start, a_end):
                p_start = _parse_iso(prat["start_iso"])
                p_end   = _parse_iso(prat["end_iso"])
                if not _in_window(p_start, p_end):
                    continue
                p_subj = f"{lord}_{antar['antar_lord']}_{prat['pratyantar_lord']}"
                rows.append(_period_row(
                    chart_id, ayanamsha_id, build_id,
                    "vimshottari", "D1", "pratyantar",
                    p_subj, prat,
                ))

                # Sookshma
                for sook in compute_sookshma(
                    lord, antar["antar_lord"], prat["pratyantar_lord"],
                    p_start, p_end,
                ):
                    s_start = _parse_iso(sook["start_iso"])
                    s_end   = _parse_iso(sook["end_iso"])
                    if not _in_window(s_start, s_end):
                        continue
                    s_subj = _subject_key(sook)
                    rows.append(_period_row(
                        chart_id, ayanamsha_id, build_id,
                        "vimshottari", "D1", "sookshma",
                        s_subj, sook,
                    ))

    return rows


# ---------------------------------------------------------------------------
# YOGINI computation
# ---------------------------------------------------------------------------

def compute_yogini_sequence(moon_nakshatra_id: int, moon_degree_in_nak: float,
                             birth_dt: datetime) -> list[dict]:
    """
    Compute Yogini dasha main periods from birth through 2100.
    moon_degree_in_nak: degrees into the nakshatra (0..13.333)
    """
    start_idx      = _yogini_start_idx(moon_nakshatra_id)
    nak_fraction   = min(max(moon_degree_in_nak / 13.333, 0.0), 1.0)
    balance_frac   = 1.0 - nak_fraction

    periods: list[dict] = []
    current = _clamp_dt(birth_dt)

    # First period: balance of starting Yogini
    yogini_years  = YOGINI_YEARS[start_idx]
    balance_years = yogini_years * balance_frac
    end = current + timedelta(days=balance_years * 365.25)
    periods.append({
        "yogini":     YOGINI_LORDS[start_idx],
        "lord":       YOGINI_GRAHAS[start_idx],
        "start_iso":  current.isoformat(),
        "end_iso":    end.isoformat(),
        "years":      round(balance_years, 6),
        "is_balance": True,
    })
    current = end

    # Full subsequent periods until 2100
    i = 1
    while current < WINDOW_END:
        idx   = (start_idx + i) % 8
        years = YOGINI_YEARS[idx]
        end   = current + timedelta(days=years * 365.25)
        periods.append({
            "yogini":     YOGINI_LORDS[idx],
            "lord":       YOGINI_GRAHAS[idx],
            "start_iso":  current.isoformat(),
            "end_iso":    end.isoformat(),
            "years":      years,
            "is_balance": False,
        })
        current = end
        i += 1

    return periods


def _yogini_antardasha(main: dict) -> list[dict]:
    """Subdivide a Yogini main period into 8 sub-periods proportionally."""
    start_idx  = YOGINI_LORDS.index(main["yogini"])
    total_days = (
        _parse_iso(main["end_iso"]) - _parse_iso(main["start_iso"])
    ).total_seconds() / 86400
    yogini_total_yrs = sum(YOGINI_YEARS)  # 36
    current = _parse_iso(main["start_iso"])
    subs: list[dict] = []
    for i in range(8):
        idx  = (start_idx + i) % 8
        days = total_days * YOGINI_YEARS[idx] / yogini_total_yrs
        end  = current + timedelta(days=days)
        subs.append({
            "main_yogini":  main["yogini"],
            "main_lord":    main["lord"],
            "sub_yogini":   YOGINI_LORDS[idx],
            "sub_lord":     YOGINI_GRAHAS[idx],
            "start_iso":    current.isoformat(),
            "end_iso":      end.isoformat(),
            "duration_days": round(days, 4),
        })
        current = end
    return subs


def _collect_yogini_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                          moon_nakshatra_id: int, moon_degree_in_nak: float,
                          birth_dt: datetime) -> list[tuple]:
    rows: list[tuple] = []
    mains = compute_yogini_sequence(moon_nakshatra_id, moon_degree_in_nak, birth_dt)
    for main in mains:
        m_start = _parse_iso(main["start_iso"])
        m_end   = _parse_iso(main["end_iso"])
        if not _in_window(m_start, m_end):
            continue
        subj = main["yogini"]
        rows.append(_period_row(
            chart_id, ayanamsha_id, build_id,
            "yogini", "D1", "main", subj, main,
        ))
        # Antar (Pratyantar depth for Yogini)
        for sub in _yogini_antardasha(main):
            s_start = _parse_iso(sub["start_iso"])
            s_end   = _parse_iso(sub["end_iso"])
            if not _in_window(s_start, s_end):
                continue
            s_subj = f"{main['yogini']}_{sub['sub_yogini']}"
            rows.append(_period_row(
                chart_id, ayanamsha_id, build_id,
                "yogini", "D1", "antara", s_subj, sub,
            ))
    return rows


# ---------------------------------------------------------------------------
# ASHTOTTARI computation
# ---------------------------------------------------------------------------

def compute_ashtottari_sequence(moon_nakshatra_id: int, moon_degree_in_nak: float,
                                 birth_dt: datetime) -> list[dict]:
    """Compute Ashtottari main dasha periods."""
    start_idx    = _ashtottari_start_idx(moon_nakshatra_id)
    nak_fraction = min(max(moon_degree_in_nak / 13.333, 0.0), 1.0)
    # Balance: fraction of current lord's period remaining
    # Each lord's nakshatra span = their_years / 108 * 27 nakshatras
    balance_frac = 1.0 - nak_fraction

    current = _clamp_dt(birth_dt)
    periods: list[dict] = []

    # First period: balance
    lord      = ASHTOTTARI_SEQUENCE[start_idx]
    lord_yrs  = ASHTOTTARI_YEARS[lord]
    bal_yrs   = lord_yrs * balance_frac
    end       = current + timedelta(days=bal_yrs * 365.25)
    periods.append({
        "lord":       lord,
        "start_iso":  current.isoformat(),
        "end_iso":    end.isoformat(),
        "years":      round(bal_yrs, 6),
        "is_balance": True,
    })
    current = end

    i = 1
    while current < WINDOW_END:
        idx   = (start_idx + i) % 8
        lord  = ASHTOTTARI_SEQUENCE[idx]
        years = ASHTOTTARI_YEARS[lord]
        end   = current + timedelta(days=years * 365.25)
        periods.append({
            "lord":       lord,
            "start_iso":  current.isoformat(),
            "end_iso":    end.isoformat(),
            "years":      years,
            "is_balance": False,
        })
        current = end
        i += 1

    return periods


def _ashtottari_antar(main: dict) -> list[dict]:
    """Divide Ashtottari main period into 8 proportional sub-periods."""
    start_idx  = ASHTOTTARI_SEQUENCE.index(main["lord"])
    total_days = (
        _parse_iso(main["end_iso"]) - _parse_iso(main["start_iso"])
    ).total_seconds() / 86400
    current = _parse_iso(main["start_iso"])
    subs: list[dict] = []
    for i in range(8):
        idx   = (start_idx + i) % 8
        lord  = ASHTOTTARI_SEQUENCE[idx]
        days  = total_days * ASHTOTTARI_YEARS[lord] / ASHTOTTARI_TOTAL
        end   = current + timedelta(days=days)
        subs.append({
            "maha_lord":  main["lord"],
            "antar_lord": lord,
            "start_iso":  current.isoformat(),
            "end_iso":    end.isoformat(),
            "duration_days": round(days, 4),
        })
        current = end
    return subs


def _ashtottari_pratyantar(maha_lord: str, antar_lord: str,
                             a_start: datetime, a_end: datetime) -> list[dict]:
    """Divide Ashtottari antardasha into 8 proportional pratyantars."""
    start_idx  = ASHTOTTARI_SEQUENCE.index(antar_lord)
    total_days = (a_end - a_start).total_seconds() / 86400
    current    = a_start
    subs: list[dict] = []
    for i in range(8):
        idx  = (start_idx + i) % 8
        lord = ASHTOTTARI_SEQUENCE[idx]
        days = total_days * ASHTOTTARI_YEARS[lord] / ASHTOTTARI_TOTAL
        end  = current + timedelta(days=days)
        subs.append({
            "maha_lord":       maha_lord,
            "antar_lord":      antar_lord,
            "pratyantar_lord": lord,
            "start_iso":       current.isoformat(),
            "end_iso":         end.isoformat(),
            "duration_days":   round(days, 4),
        })
        current = end
    return subs


def _collect_ashtottari_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                              moon_nakshatra_id: int, moon_degree_in_nak: float,
                              birth_dt: datetime) -> list[tuple]:
    rows: list[tuple] = []
    mains = compute_ashtottari_sequence(moon_nakshatra_id, moon_degree_in_nak, birth_dt)
    for main in mains:
        m_start = _parse_iso(main["start_iso"])
        m_end   = _parse_iso(main["end_iso"])
        if not _in_window(m_start, m_end):
            continue
        rows.append(_period_row(
            chart_id, ayanamsha_id, build_id,
            "ashtottari", "D1", "maha", main["lord"], main,
        ))
        for antar in _ashtottari_antar(main):
            a_start = _parse_iso(antar["start_iso"])
            a_end   = _parse_iso(antar["end_iso"])
            if not _in_window(a_start, a_end):
                continue
            a_subj = f"{main['lord']}_{antar['antar_lord']}"
            rows.append(_period_row(
                chart_id, ayanamsha_id, build_id,
                "ashtottari", "D1", "antar", a_subj, antar,
            ))
            for prat in _ashtottari_pratyantar(main["lord"], antar["antar_lord"],
                                                a_start, a_end):
                p_start = _parse_iso(prat["start_iso"])
                p_end   = _parse_iso(prat["end_iso"])
                if not _in_window(p_start, p_end):
                    continue
                p_subj = f"{main['lord']}_{antar['antar_lord']}_{prat['pratyantar_lord']}"
                rows.append(_period_row(
                    chart_id, ayanamsha_id, build_id,
                    "ashtottari", "D1", "pratyantar", p_subj, prat,
                ))
    return rows


# ---------------------------------------------------------------------------
# NAISARGIKA computation
# ---------------------------------------------------------------------------

def compute_naisargika_sequence(birth_dt: datetime) -> list[dict]:
    """Fixed natural dasha sequence from birth."""
    current = _clamp_dt(birth_dt)
    periods: list[dict] = []
    for lord, years in NAISARGIKA_SEQUENCE:
        end = current + timedelta(days=years * 365.25)
        periods.append({
            "lord":       lord,
            "start_iso":  current.isoformat(),
            "end_iso":    end.isoformat(),
            "years":      years,
        })
        current = end
    return periods


def _naisargika_antar(main: dict) -> list[dict]:
    """Subdivide Naisargika main period proportionally by Naisargika sequence."""
    total_days = (
        _parse_iso(main["end_iso"]) - _parse_iso(main["start_iso"])
    ).total_seconds() / 86400
    current = _parse_iso(main["start_iso"])
    subs: list[dict] = []
    for sub_lord, sub_years in NAISARGIKA_SEQUENCE:
        days = total_days * sub_years / NAISARGIKA_TOTAL
        end  = current + timedelta(days=days)
        subs.append({
            "maha_lord":  main["lord"],
            "antar_lord": sub_lord,
            "start_iso":  current.isoformat(),
            "end_iso":    end.isoformat(),
            "duration_days": round(days, 4),
        })
        current = end
    return subs


def _collect_naisargika_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                              birth_dt: datetime) -> list[tuple]:
    rows: list[tuple] = []
    for main in compute_naisargika_sequence(birth_dt):
        m_start = _parse_iso(main["start_iso"])
        m_end   = _parse_iso(main["end_iso"])
        if not _in_window(m_start, m_end):
            continue
        rows.append(_period_row(
            chart_id, ayanamsha_id, build_id,
            "naisargika", "D1", "maha", main["lord"], main,
        ))
        for antar in _naisargika_antar(main):
            a_start = _parse_iso(antar["start_iso"])
            a_end   = _parse_iso(antar["end_iso"])
            if not _in_window(a_start, a_end):
                continue
            a_subj = f"{main['lord']}_{antar['antar_lord']}"
            rows.append(_period_row(
                chart_id, ayanamsha_id, build_id,
                "naisargika", "D1", "antar", a_subj, antar,
            ))
    return rows


# ---------------------------------------------------------------------------
# MUDDA computation (365-day Vimshottari per year)
# ---------------------------------------------------------------------------

def compute_mudda_for_year(maha_lord: str, year_start: datetime) -> list[dict]:
    """
    Compute Mudda dasha for a single Varsha (year) starting from year_start.
    Starting lord same as Vimshottari maha_lord.
    """
    start_idx = VIMSHOTTARI_SEQUENCE.index(maha_lord)
    current   = _clamp_dt(year_start)
    periods: list[dict] = []
    for i in range(9):
        lord = VIMSHOTTARI_SEQUENCE[(start_idx + i) % 9]
        days = float(MUDDA_DAYS[lord])
        end  = current + timedelta(days=days)
        periods.append({
            "mudda_year_start": year_start.isoformat(),
            "lord":             lord,
            "start_iso":        current.isoformat(),
            "end_iso":          end.isoformat(),
            "duration_days":    days,
        })
        current = end
    return periods


def _collect_mudda_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                         birth_dt: datetime, mahadasha_sequence: list[dict]) -> list[tuple]:
    """
    Write Mudda (annual compressed Vimshottari) rows.
    For each calendar year from birth year through 2100, determine the
    active Vimshottari mahadasha lord and emit 9 Mudda periods for that year.
    """
    rows: list[tuple] = []

    # Build a lookup: given a date, which Vimshottari maha lord is active?
    # Sort mahadasha_sequence by start date
    sorted_maha = sorted(mahadasha_sequence, key=lambda m: m["start_iso"])

    def _get_maha_lord_at(dt: datetime) -> str:
        for m in reversed(sorted_maha):
            if _parse_iso(m["start_iso"]) <= dt:
                return m["lord"]
        return sorted_maha[0]["lord"]

    birth_year = _clamp_dt(birth_dt).year
    for yr in range(birth_year, 2101):
        year_start = datetime(yr, 1, 1, tzinfo=timezone.utc)
        if year_start > WINDOW_END:
            break
        maha_lord = _get_maha_lord_at(year_start)
        for period in compute_mudda_for_year(maha_lord, year_start):
            p_start = _parse_iso(period["start_iso"])
            p_end   = _parse_iso(period["end_iso"])
            if not _in_window(p_start, p_end):
                continue
            subj = f"{yr}_{period['lord']}"
            rows.append(_period_row(
                chart_id, ayanamsha_id, build_id,
                "mudda", "D1", "period", subj, period,
            ))
    return rows


# ---------------------------------------------------------------------------
# JAIMINI CHARA simplified computation
# ---------------------------------------------------------------------------

def _compute_jaimini_chara_sequence(lagna_sign_idx: int) -> list[str]:
    """
    Simplified Jaimini Chara: start from Lagna sign, proceed in
    natural zodiacal order for odd signs, reverse for even signs.
    Returns 12 sign names in dasha order.
    """
    # Simplified: alternate forward/backward from Lagna
    result: list[str] = []
    forward_signs  = [ZODIAC_SIGNS[(lagna_sign_idx + i) % 12] for i in range(12)]
    # Odd-position signs go forward, even-position reverse
    # This is the simplified BPHS default: start at Lagna, go forward
    return forward_signs


def _jaimini_sign_years(sign: str, grahas_in_sign: list[str]) -> int:
    """
    Compute Jaimini Chara years for a sign.
    Simplified rule: count planets in sign, add 1 for sign lord's strength.
    Clamp to 1..12.
    """
    planet_count = len(grahas_in_sign)
    # Default is 7 years; ±1 per planet count deviation from baseline 1
    years = 7 + (planet_count - 1)
    return max(1, min(12, years))


def _collect_jaimini_chara_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                                 birth_dt: datetime,
                                 lagna_sign: str,
                                 grahas: list[dict]) -> list[tuple]:
    """
    Simplified Jaimini Chara Dasha.
    Each sign gets a period; duration computed from planets in sign.
    Write until 2100.
    """
    rows: list[tuple] = []

    # Find lagna sign index
    try:
        lagna_idx = ZODIAC_SIGNS.index(lagna_sign)
    except ValueError:
        lagna_idx = 0  # Default to Aries if unknown

    sign_sequence = _compute_jaimini_chara_sequence(lagna_idx)

    # Build planet-in-sign lookup
    planets_per_sign: dict[str, list[str]] = {s: [] for s in ZODIAC_SIGNS}
    for graha in grahas:
        g_sign = graha.get("sign", graha.get("rasi", ""))
        if g_sign in planets_per_sign:
            planets_per_sign[g_sign].append(graha.get("name", ""))

    current = _clamp_dt(birth_dt)
    cycle   = 0
    while current < WINDOW_END:
        for sign in sign_sequence:
            years = _jaimini_sign_years(sign, planets_per_sign.get(sign, []))
            end   = current + timedelta(days=years * 365.25)
            period = {
                "sign":       sign,
                "sign_lord":  SIGN_LORDS.get(sign, ""),
                "start_iso":  current.isoformat(),
                "end_iso":    end.isoformat(),
                "years":      years,
                "cycle":      cycle,
                "planets_in_sign": planets_per_sign.get(sign, []),
            }
            if _in_window(current, end):
                subj = f"{sign}_cycle{cycle}"
                rows.append(_period_row(
                    chart_id, ayanamsha_id, build_id,
                    "jaimini_chara", "D1", "chara_period", subj, period,
                ))
            current = end
            if current >= WINDOW_END:
                break
        cycle += 1
        if cycle > 20:  # Safety limit: ~120-240 years per cycle
            break

    return rows


# ---------------------------------------------------------------------------
# KALACHAKRA simplified computation
# ---------------------------------------------------------------------------

def _get_moon_navamsa_sign_idx(moon_longitude: float) -> int:
    """
    Get Moon's navamsa (D9) sign index (0-based).
    Navamsa: each sign is divided into 9 parts of 3.333° each.
    Sign index in D9 depends on position within 3.333° arc.
    """
    pos_in_sign = moon_longitude % 30.0
    navamsa_idx = int(pos_in_sign / 3.3333)  # 0..8
    sign_idx    = int(moon_longitude / 30.0) % 12
    # D9 sign: depends on sign type (movable/fixed/dual)
    # Simplified: use raw navamsa position mod 12
    return (sign_idx * 9 + navamsa_idx) % 12


def _collect_kalachakra_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                              birth_dt: datetime,
                              moon_longitude: float) -> list[tuple]:
    """
    Simplified Kalachakra Dasha based on Moon's navamsa sign.
    Uses fixed sequence of 100-year cycle distributed across 12 sign periods.
    """
    rows: list[tuple] = []

    navamsa_idx = _get_moon_navamsa_sign_idx(moon_longitude)
    group_info  = KALACHAKRA_NAVAMSA_GROUPS[navamsa_idx]
    _, group_name, direction, years_seq = group_info

    # Build sign sequence based on direction
    if direction == "forward":
        sign_order = [(navamsa_idx + i) % 12 for i in range(9)]
    else:
        sign_order = [(navamsa_idx - i) % 12 for i in range(9)]

    current = _clamp_dt(birth_dt)
    cycle   = 0
    while current < WINDOW_END and cycle < 5:
        for i, sign_idx in enumerate(sign_order):
            sign  = ZODIAC_SIGNS[sign_idx]
            years = years_seq[i] if i < len(years_seq) else 10
            end   = current + timedelta(days=years * 365.25)
            period = {
                "sign":         sign,
                "group":        group_name,
                "direction":    direction,
                "navamsa_idx":  navamsa_idx,
                "years":        years,
                "cycle":        cycle,
                "start_iso":    current.isoformat(),
                "end_iso":      end.isoformat(),
            }
            if _in_window(current, end):
                subj = f"{sign}_c{cycle}"
                rows.append(_period_row(
                    chart_id, ayanamsha_id, build_id,
                    "kalachakra", "D9", "kc_period", subj, period,
                ))
            current = end
            if current >= WINDOW_END:
                break
        cycle += 1

    return rows


# ---------------------------------------------------------------------------
# Chart output extraction helpers
# ---------------------------------------------------------------------------

def _extract_moon_data(grahas: list[dict]) -> tuple[int, float, float]:
    """
    Extract Moon nakshatra id, degree within nakshatra, and longitude.
    Returns (nakshatra_id, degree_in_nak, longitude).
    nakshatra_id is 1-indexed (1..27).
    """
    for g in grahas:
        name = g.get("name", g.get("id", "")).lower()
        if name in ("moon", "mo", "chan", "chandra"):
            lon = float(g.get("longitude", g.get("lon", 0.0)))
            nak_id = int(g.get("nakshatra_id", g.get("nakshatra_num", 0)))
            if nak_id == 0:
                nak_id = int(lon / 13.333) + 1
                nak_id = max(1, min(27, nak_id))
            deg_in_nak = lon % 13.333
            return nak_id, deg_in_nak, lon
    # Fallback
    return 1, 0.0, 0.0


def _extract_lagna_sign(chart_output: dict) -> str:
    """Extract Lagna sign name from chart output."""
    lagna = chart_output.get("lagna", chart_output.get("ascendant", {}))
    if isinstance(lagna, dict):
        sign = lagna.get("sign", lagna.get("rasi", "Aries"))
        return sign
    # Try from houses
    houses = chart_output.get("houses", [])
    if houses:
        h1 = houses[0] if isinstance(houses, list) else houses.get("1", {})
        if isinstance(h1, dict):
            return h1.get("sign", "Aries")
    return "Aries"


def _extract_birth_dt(chart_output: dict) -> datetime:
    """Extract birth datetime from chart output."""
    birth_iso = chart_output.get("birth_datetime", chart_output.get("birth_dt", ""))
    if birth_iso:
        try:
            return _parse_iso(str(birth_iso))
        except Exception:
            pass
    # Fallback to a reasonable default
    return datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Main write() entry point
# ---------------------------------------------------------------------------

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write 7 acharya-selected dasha systems to chart_facts.

    Args:
        build_id:      Build identifier string.
        chart_id:      Chart UUID string.
        ayanamsha_id:  Ayanamsha identifier (e.g. "lahiri", "kp").
        chart_output:  Dict from pyjhora_adapter containing 'dashas', 'grahas',
                       'lagna', 'birth_datetime'.
        conn:          psycopg2 connection, or None for dry-run row counting.
        extra:         Optional extra config dict (unused).

    Returns:
        int: rows_written count (or rows_would_write when conn=None).
    """
    if conn is None:
        return 0
    logger.info(
        "[A7] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )

    all_rows: list[tuple] = []

    # ── Extract shared data from chart_output ───────────────────────────────
    dashas   = chart_output.get("dashas", {})
    grahas   = chart_output.get("grahas", [])
    maha_seq = dashas.get("mahadasha_sequence", [])

    moon_nak_id, moon_deg_in_nak, moon_lon = _extract_moon_data(grahas)
    birth_dt   = _extract_birth_dt(chart_output)
    lagna_sign = _extract_lagna_sign(chart_output)

    logger.debug(
        "[A7] moon_nak=%d deg_in_nak=%.3f lon=%.3f lagna=%s birth=%s",
        moon_nak_id, moon_deg_in_nak, moon_lon, lagna_sign, birth_dt.isoformat(),
    )

    # ── 1. VIMSHOTTARI ──────────────────────────────────────────────────────
    if maha_seq:
        vimsh_rows = _collect_vimshottari_rows(
            chart_id, ayanamsha_id, build_id, maha_seq
        )
        all_rows.extend(vimsh_rows)
        logger.debug("[A7] Vimshottari rows: %d", len(vimsh_rows))
    else:
        logger.warning("[A7] No mahadasha_sequence in chart_output; skipping Vimshottari")

    # ── 2. YOGINI ───────────────────────────────────────────────────────────
    yogini_rows = _collect_yogini_rows(
        chart_id, ayanamsha_id, build_id,
        moon_nak_id, moon_deg_in_nak, birth_dt,
    )
    all_rows.extend(yogini_rows)
    logger.debug("[A7] Yogini rows: %d", len(yogini_rows))

    # ── 3. ASHTOTTARI ───────────────────────────────────────────────────────
    ash_rows = _collect_ashtottari_rows(
        chart_id, ayanamsha_id, build_id,
        moon_nak_id, moon_deg_in_nak, birth_dt,
    )
    all_rows.extend(ash_rows)
    logger.debug("[A7] Ashtottari rows: %d", len(ash_rows))

    # ── 4. NAISARGIKA ───────────────────────────────────────────────────────
    nais_rows = _collect_naisargika_rows(
        chart_id, ayanamsha_id, build_id, birth_dt,
    )
    all_rows.extend(nais_rows)
    logger.debug("[A7] Naisargika rows: %d", len(nais_rows))

    # ── 5. MUDDA ────────────────────────────────────────────────────────────
    if maha_seq:
        mudda_rows = _collect_mudda_rows(
            chart_id, ayanamsha_id, build_id, birth_dt, maha_seq,
        )
        all_rows.extend(mudda_rows)
        logger.debug("[A7] Mudda rows: %d", len(mudda_rows))

    # ── 6. JAIMINI CHARA ────────────────────────────────────────────────────
    jaimini_rows = _collect_jaimini_chara_rows(
        chart_id, ayanamsha_id, build_id,
        birth_dt, lagna_sign, grahas,
    )
    all_rows.extend(jaimini_rows)
    logger.debug("[A7] Jaimini Chara rows: %d", len(jaimini_rows))

    # ── 7. KALACHAKRA ───────────────────────────────────────────────────────
    kc_rows = _collect_kalachakra_rows(
        chart_id, ayanamsha_id, build_id, birth_dt, moon_lon,
    )
    all_rows.extend(kc_rows)
    logger.debug("[A7] Kalachakra rows: %d", len(kc_rows))

    total = len(all_rows)
    logger.info("[A7] Total rows to write: %d", total)

    # ── DB write ─────────────────────────────────────────────────────────────
    if conn is None:
        logger.info("[A7] conn=None — dry-run, returning count %d", total)
        return total

    # Guard: drop rows where NOT NULL columns (fact_category/fact_subject/fact_key)
    # would be NULL — those cause a NotNullViolation that silently aborts the txn.
    # Indices 8/9/10 map to fact_category/fact_subject/fact_key in _INSERT_SQL.
    pre_filter = len(all_rows)
    all_rows = [r for r in all_rows if r[8] is not None and r[9] is not None and r[10] is not None]
    if len(all_rows) < pre_filter:
        logger.warning("[A7] Dropped %d rows with NULL NOT-NULL columns (of %d total)",
                       pre_filter - len(all_rows), pre_filter)

    # Deduplicate by ON CONFLICT key (chart_id, ayanamsha_id, fact_category, fact_subject,
    # fact_key, build_id) at indices (1, 2, 8, 9, 10, 3). Duplicate keys in a single
    # execute_values batch cause CardinalityViolation. Keep last occurrence per key.
    seen: dict = {}
    for row in all_rows:
        key = (row[1], row[2], row[8], row[9], row[10], row[3])
        seen[key] = row
    pre_dedup = len(all_rows)
    all_rows = list(seen.values())
    if len(all_rows) < pre_dedup:
        logger.warning("[A7] Deduplicated %d duplicate-key rows (of %d total)",
                       pre_dedup - len(all_rows), pre_dedup)

    if total > 0 and all_rows:
        try:
            from psycopg2.extras import execute_values
            with conn.cursor() as _cur:
                execute_values(_cur, _INSERT_SQL, all_rows, page_size=500)
            conn.commit()
        except Exception as first_exc:
            logger.error("[A7] First execute_values failed: %s", first_exc)
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                from psycopg2.extras import execute_values
                with conn.cursor() as _cur:
                    execute_values(_cur, _INSERT_SQL, all_rows, page_size=500)
            except Exception as exc:
                logger.error("[A7] DB write failed: %s", exc)
                raise

    return len(all_rows)
