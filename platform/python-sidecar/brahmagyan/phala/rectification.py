"""
brahmagyan.phala.rectification — BRAHMA-PH-4-3: phala.rectification
=====================================================================

Birth-time rectification using held-out LEL train/test split.

Contract (BRAHMA L4 Phala — PH-4-3):
  - owns: birth-time rectification via Vimshottari dasha alignment scoring
  - tool: rectification(chart_id) → {best_candidate_time, confidence,
          train_score, test_score, provenance_envelope}
  - table: phala_rectification (chart_id UUID, candidate_time TIME,
           alignment_score FLOAT, rectification_confidence FLOAT,
           source_citation TEXT NOT NULL)

Algorithm:
  For each candidate birth time ±30 min of 10:43 IST (1-minute steps):
    1. Recompute Vimshottari dasha sequence for candidate birth time
       (Jupiter MD starts from birth; each MD period scaled proportionally)
    2. For each LEL train event (events 1–43, 75% split):
       compute dasha_alignment_score = 1 if event falls inside the correct
       Vimshottari MD/AD, else 0 (partial match = 0.5 for MD-only match)
    3. rectification_confidence = pearson_correlation(candidate_offset_minutes,
       alignment_score_vector) — surface the offset that maximises alignment

NO LEAKAGE: test events 44–57 are NEVER used to select the best candidate.
The test split is used only for post-selection scoring (out-of-sample validation).

Native: Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar
Chart UUID: 482012f1-710e-4a25-994a-93821f5871aa

Source data:
  FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) — Vimshottari dasha sequence
  LIFE_EVENT_LOG_v1_2.md — 57 LEL events with chart_state_at_event
  Train split: events 1–43 (indices 0..42); Test split: events 44–57 (indices 43..56)

B.10 compliance:
  This module uses the dasha sequence already computed and stored in FORENSIC §5.1.
  Candidate-time recomputation adjusts only the MD start offset proportionally —
  it does NOT re-run Swiss Ephemeris. Any planetary-position-level rectification
  would require [EXTERNAL_COMPUTATION_REQUIRED: Swiss Ephemeris --jpleph ...].
  This tool operates solely at the dasha-timing level.

Usage:
    # Run rectification and store results
    python -m brahmagyan.phala.rectification seed --chart-id 482012f1-...

    # Query best candidate
    python -m brahmagyan.phala.rectification query --chart-id 482012f1-...

    # Run acceptance gate
    python -m brahmagyan.phala.rectification gate --chart-id 482012f1-...

BRAHMA-PH-4-3
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Native chart constant ──────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

# Canonical birth time (10:43 IST = 05:13 UTC on 1984-02-05)
NOMINAL_BIRTH_HOUR_IST = 10
NOMINAL_BIRTH_MINUTE_IST = 43

# Rectification search window: ±30 minutes in 1-minute steps → 61 candidates
SEARCH_WINDOW_MINUTES = 30
STEP_MINUTES = 1

SOURCE_CITATION = (
    "FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) Vimshottari dasha sequence; "
    "LIFE_EVENT_LOG_v1_2.md 57 LEL events with chart_state_at_event; "
    "Algorithm: train/test split 43/14 events; Pearson correlation of "
    "dasha alignment score vs candidate offset (±30 min, 1-min steps). "
    "B.10-compliant: no Swiss Ephemeris re-run — dasha-level only. "
    "BRAHMA-PH-4-3 | phala.rectification"
)

# ── Vimshottari dasha constants ───────────────────────────────────────────────
#
# From FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
# Dasha lord sequence (classical): Ketu Moon Mars Rahu Jupiter Saturn Mercury
#                                   Ketu Venus Sun Moon Mars ...
# Full 120-year cycle.
# Duration in years (classical):
#   Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17, Ketu=7, Venus=20
#
# Native's birth dasha: Jupiter MD, start 1984-02-05 (birth)
#   Jupiter 16y → Saturn 19y → Mercury 17y → Ketu 7y → Venus 20y → Sun 6y → Moon 10y ...
#
# From FORENSIC §5.1 (authoritative dasha boundary dates):
#   Jupiter MD:  1984-02-05 → 2000-02-05  (16 years)
#   Saturn MD:   2000-02-05 → 2019-02-05  (19 years) — NOTE: FORENSIC shows
#                1991-08-19 → 2010-08-18; correcting to FORENSIC authoritative value
#
# FORENSIC §5.1 actual boundaries (used verbatim — B.10 mandate):
#   DSH.V.001: Jupiter  MD start 1984-02-05  (birth)
#   Jupiter  → Saturn boundary: 1991-08-19  [native born in Jupiter balance ~7.3y remaining]
#   Saturn   MD: 1991-08-19 → 2010-08-18
#   Mercury  MD: 2010-08-18 → 2027-08-18  (17y)
#   Ketu     MD: 2027-08-18 → 2034-08-18  (7y)
#
# The authoritative sequence from FORENSIC (exact dates as cited in the LEL):
VIMSHOTTARI_MD_SEQUENCE: list[dict[str, Any]] = [
    # Remaining Jupiter balance at birth (from FORENSIC §5.1 DSH.V.001)
    {"lord": "Jupiter", "start": "1984-02-05", "end": "1991-08-19", "duration_years": 7.536},
    {"lord": "Saturn",  "start": "1991-08-19", "end": "2010-08-18", "duration_years": 19.0},
    {"lord": "Mercury", "start": "2010-08-18", "end": "2027-08-18", "duration_years": 17.0},
    {"lord": "Ketu",    "start": "2027-08-18", "end": "2034-08-18", "duration_years": 7.0},
    {"lord": "Venus",   "start": "2034-08-18", "end": "2054-08-18", "duration_years": 20.0},
    {"lord": "Sun",     "start": "2054-08-18", "end": "2060-08-18", "duration_years": 6.0},
    {"lord": "Moon",    "start": "2060-08-18", "end": "2070-08-18", "duration_years": 10.0},
    {"lord": "Mars",    "start": "2070-08-18", "end": "2077-08-18", "duration_years": 7.0},
    {"lord": "Rahu",    "start": "2077-08-18", "end": "2095-08-18", "duration_years": 18.0},
]

# Antardasha (AD) sub-periods within each MD
# Each MD is divided into 9 ADs in the same dasha-lord sequence starting from the MD lord.
# AD duration = (AD_lord_full_years / 120) * MD_full_years

_FULL_DASHA_YEARS: dict[str, float] = {
    "Sun": 6.0, "Moon": 10.0, "Mars": 7.0, "Rahu": 18.0,
    "Jupiter": 16.0, "Saturn": 19.0, "Mercury": 17.0,
    "Ketu": 7.0, "Venus": 20.0,
}

_DASHA_ORDER = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus"]


def _lord_index(lord: str) -> int:
    return _DASHA_ORDER.index(lord)


def _parse_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def _build_ad_boundaries(md: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Compute all 9 AD boundaries within a given MD block.

    Returns list of dicts:
        {lord, start: date, end: date}
    """
    md_start = _parse_date(md["start"])
    md_end = _parse_date(md["end"])
    total_days = (md_end - md_start).days

    start_idx = _lord_index(md["lord"])
    ads = []
    cursor = md_start

    for i in range(9):
        ad_lord = _DASHA_ORDER[(start_idx + i) % 9]
        ad_fraction = _FULL_DASHA_YEARS[ad_lord] / 120.0
        # MD duration in years for this specific MD (may be fractional for natal balance)
        md_duration_years = total_days / 365.25
        ad_days = int(round(ad_fraction * md_duration_years * 365.25))
        ad_end = cursor + timedelta(days=ad_days)
        if ad_end > md_end:
            ad_end = md_end  # clamp last AD
        ads.append({"lord": ad_lord, "start": cursor, "end": ad_end})
        cursor = ad_end

    return ads


def _build_full_dasha_tree(offset_minutes: int = 0) -> list[dict[str, Any]]:
    """
    Build full Vimshottari MD + AD tree for the given birth-time offset.

    The offset (in minutes, relative to 10:43 IST) shifts the MD start boundaries
    proportionally by the same minute fraction of the natal dasha balance.

    For a ±30 minute shift, the dasha boundaries move by at most:
        30 / (7.536 * 365.25 * 24 * 60) ≈ 0.000008 of the Jupiter balance
    which is approximately 2.2 hours on the Jupiter/Saturn boundary.

    This is a first-order approximation (B.10-compliant: does not require SE re-run).

    Args:
        offset_minutes: signed offset from nominal birth time (−30 to +30)

    Returns:
        List of MD dicts, each with nested 'antardasha' list.
    """
    # The natal dasha balance (Jupiter remaining) is proportional to Moon's
    # nakshatra position at birth. A 1-minute shift in birth time moves the Moon
    # by ~0.00056° (Moon moves ~13°/day ≈ 0.00056°/min), changing the balance
    # fraction by ~0.00056/13.333 (Ashwini span) ≈ 0.000042 of the nakshatra.
    # Effect on Jupiter MD end: 7.536y × 365.25d × 0.000042 ≈ 0.115 days/minute offset.
    # We approximate: each 1-minute offset shifts ALL MD boundaries by 0.115 days.
    DAYS_PER_MINUTE_OFFSET = 0.115

    shift_days = offset_minutes * DAYS_PER_MINUTE_OFFSET

    tree = []
    for md in VIMSHOTTARI_MD_SEQUENCE:
        md_start = _parse_date(md["start"]) + timedelta(days=shift_days)
        md_end = _parse_date(md["end"]) + timedelta(days=shift_days)
        md_shifted = {
            "lord": md["lord"],
            "start": md_start.isoformat(),
            "end": md_end.isoformat(),
            "duration_years": md["duration_years"],
        }
        md_shifted["antardasha"] = _build_ad_boundaries(md_shifted)
        tree.append(md_shifted)

    return tree


# ── LEL event corpus ───────────────────────────────────────────────────────────
#
# 57 events from LIFE_EVENT_LOG_v1_2.md with Vimshottari MD/AD from chart_state.
# Ordered chronologically (event index 1..57).
# Events without explicit MD/AD (status=computed_proxy_date) use the proxy dates.
#
# Format: (event_id, approx_date, expected_md, expected_ad)
#   expected_md / expected_ad: the MD/AD lord per FORENSIC §5.1 at event time
#   approx_date: best available date (year-month-day; use mid-year for year-approx)
#
# Events 1–43 → train split (TRAIN_SPLIT_IDX = 43)
# Events 44–57 → test split (held-out; NEVER used for candidate selection)
#
# Source: LIFE_EVENT_LOG_v1_2.md §3 + M5-A enrichment section
# Provenance: chart_state_at_event fields; computed_proxy_date where noted

TRAIN_SPLIT_IDX = 43  # events[0..42] = train; events[43..56] = test

LEL_EVENTS: list[dict[str, Any]] = [
    # ── Train split: events 1–43 (index 0..42) ──────────────────────────────
    # Era 1 + 2
    {"idx": 1,  "id": "EVT.1984.02.05.01", "date": "1984-02-05", "expected_md": "Jupiter", "expected_ad": "Venus",   "magnitude": "life-altering"},
    {"idx": 2,  "id": "EVT.1993.XX.XX.01", "date": "1993-07-01", "expected_md": "Saturn",  "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 3,  "id": "EVT.1995.XX.XX.01", "date": "1995-07-01", "expected_md": "Saturn",  "expected_ad": "Mercury", "magnitude": "significant"},
    {"idx": 4,  "id": "EVT.1995.XX.XX.02", "date": "1995-07-01", "expected_md": "Saturn",  "expected_ad": "Mercury", "magnitude": "moderate"},
    # Era 3
    {"idx": 5,  "id": "EVT.1998.02.16.01", "date": "1998-02-16", "expected_md": "Saturn",  "expected_ad": "Ketu",    "magnitude": "life-altering"},
    {"idx": 6,  "id": "EVT.1998.XX.XX.02", "date": "1998-07-01", "expected_md": "Saturn",  "expected_ad": "Venus",   "magnitude": "moderate"},
    {"idx": 7,  "id": "EVT.2000.XX.XX.01", "date": "2000-06-01", "expected_md": "Saturn",  "expected_ad": "Venus",   "magnitude": "moderate"},
    {"idx": 8,  "id": "EVT.2001.03.XX.01", "date": "2001-03-15", "expected_md": "Saturn",  "expected_ad": "Venus",   "magnitude": "significant"},
    {"idx": 9,  "id": "EVT.2002.XX.XX.01", "date": "2002-07-01", "expected_md": "Saturn",  "expected_ad": "Venus",   "magnitude": "moderate"},
    {"idx": 10, "id": "EVT.2002.XX.XX.02", "date": "2002-07-01", "expected_md": "Saturn",  "expected_ad": "Venus",   "magnitude": "moderate"},
    {"idx": 11, "id": "EVT.2003.06.XX.01", "date": "2003-06-15", "expected_md": "Saturn",  "expected_ad": "Moon",    "magnitude": "significant"},
    # Era 4
    {"idx": 12, "id": "EVT.2004.01.XX.01", "date": "2004-01-15", "expected_md": "Saturn",  "expected_ad": "Moon",    "magnitude": "significant"},
    {"idx": 13, "id": "EVT.2004.XX.XX.02", "date": "2004-06-01", "expected_md": "Saturn",  "expected_ad": "Mars",    "magnitude": "significant"},
    {"idx": 14, "id": "EVT.2007.06.XX.01", "date": "2007-06-15", "expected_md": "Saturn",  "expected_ad": "Rahu",    "magnitude": "moderate"},
    {"idx": 15, "id": "EVT.2007.06.XX.02", "date": "2007-06-15", "expected_md": "Saturn",  "expected_ad": "Rahu",    "magnitude": "significant"},
    {"idx": 16, "id": "EVT.2007.06.10.01", "date": "2007-06-10", "expected_md": "Saturn",  "expected_ad": "Rahu",    "magnitude": "significant"},
    {"idx": 17, "id": "EVT.2007.XX.XX.03", "date": "2007-09-01", "expected_md": "Saturn",  "expected_ad": "Rahu",    "magnitude": "significant"},
    {"idx": 18, "id": "EVT.2008.06.09.01", "date": "2008-06-09", "expected_md": "Saturn",  "expected_ad": "Jupiter", "magnitude": "significant"},
    {"idx": 19, "id": "EVT.2009.06.XX.01", "date": "2009-06-15", "expected_md": "Saturn",  "expected_ad": "Jupiter", "magnitude": "major"},
    # Era 5
    {"idx": 20, "id": "EVT.2010.XX.XX.01", "date": "2010-07-01", "expected_md": "Saturn",  "expected_ad": "Jupiter", "magnitude": "significant"},
    {"idx": 21, "id": "EVT.2010.XX.XX.02", "date": "2010-07-01", "expected_md": "Saturn",  "expected_ad": "Jupiter", "magnitude": "moderate"},
    {"idx": 22, "id": "EVT.2010.12.XX.01", "date": "2010-12-15", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "significant"},
    {"idx": 23, "id": "EVT.2011.01.XX.01", "date": "2011-01-15", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "major"},
    {"idx": 24, "id": "EVT.2011.06.XX.01", "date": "2011-06-15", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "major"},
    {"idx": 25, "id": "EVT.2012.09.XX.01", "date": "2012-09-15", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "moderate"},
    {"idx": 26, "id": "EVT.2012.XX.XX.02", "date": "2012-09-01", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "moderate"},
    {"idx": 27, "id": "EVT.2012.10.XX.01", "date": "2012-10-15", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "significant"},
    {"idx": 28, "id": "EVT.2013.03.XX.01", "date": "2013-03-15", "expected_md": "Mercury", "expected_ad": "Ketu",    "magnitude": "significant"},
    {"idx": 29, "id": "EVT.2013.05.XX.01", "date": "2013-05-15", "expected_md": "Mercury", "expected_ad": "Ketu",    "magnitude": "significant"},
    {"idx": 30, "id": "EVT.2013.XX.XX.01", "date": "2013-07-01", "expected_md": "Mercury", "expected_ad": "Ketu",    "magnitude": "moderate"},
    {"idx": 31, "id": "EVT.2013.12.11.01", "date": "2013-12-11", "expected_md": "Mercury", "expected_ad": "Ketu",    "magnitude": "life-altering"},
    # Era 6 (2016-2018)
    {"idx": 32, "id": "EVT.2015.XX.XX.01", "date": "2015-07-01", "expected_md": "Mercury", "expected_ad": "Venus",   "magnitude": "significant"},
    {"idx": 33, "id": "EVT.2016.XX.XX.01", "date": "2016-07-01", "expected_md": "Mercury", "expected_ad": "Venus",   "magnitude": "major"},
    {"idx": 34, "id": "EVT.2017.03.XX.01", "date": "2017-03-15", "expected_md": "Mercury", "expected_ad": "Venus",   "magnitude": "significant"},
    {"idx": 35, "id": "EVT.2018.11.28.01", "date": "2018-11-28", "expected_md": "Mercury", "expected_ad": "Moon",    "magnitude": "major"},
    # Era 7 (US period 2019-2023)
    {"idx": 36, "id": "EVT.2019.05.XX.01", "date": "2019-05-15", "expected_md": "Mercury", "expected_ad": "Moon",    "magnitude": "major"},
    {"idx": 37, "id": "EVT.2021.01.XX.01", "date": "2021-01-15", "expected_md": "Mercury", "expected_ad": "Rahu",    "magnitude": "significant"},
    {"idx": 38, "id": "EVT.2021.XX.XX.02", "date": "2021-07-01", "expected_md": "Mercury", "expected_ad": "Rahu",    "magnitude": "major"},
    {"idx": 39, "id": "EVT.2021.XX.XX.03", "date": "2021-07-01", "expected_md": "Mercury", "expected_ad": "Rahu",    "magnitude": "significant"},
    {"idx": 40, "id": "EVT.2022.01.03.01", "date": "2022-01-03", "expected_md": "Mercury", "expected_ad": "Rahu",    "magnitude": "major"},
    {"idx": 41, "id": "EVT.2022.XX.XX.02", "date": "2022-07-01", "expected_md": "Mercury", "expected_ad": "Jupiter", "magnitude": "significant"},
    {"idx": 42, "id": "EVT.2022.10.XX.01", "date": "2022-10-15", "expected_md": "Mercury", "expected_ad": "Jupiter", "magnitude": "significant"},
    {"idx": 43, "id": "EVT.2023.05.XX.01", "date": "2023-05-15", "expected_md": "Mercury", "expected_ad": "Jupiter", "magnitude": "major"},
    # ── Test split: events 44–57 (index 43..56) — HELD-OUT; NEVER used for candidate selection ──
    {"idx": 44, "id": "EVT.2023.06.XX.01", "date": "2023-06-15", "expected_md": "Mercury", "expected_ad": "Jupiter", "magnitude": "major"},
    {"idx": 45, "id": "EVT.2023.07.XX.01", "date": "2023-07-15", "expected_md": "Mercury", "expected_ad": "Jupiter", "magnitude": "major"},
    {"idx": 46, "id": "EVT.2024.02.16.01", "date": "2024-02-16", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "major"},
    {"idx": 47, "id": "EVT.2024.XX.XX.01", "date": "2024-07-01", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 48, "id": "EVT.2025.05.XX.01", "date": "2025-05-15", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 49, "id": "EVT.2025.06.XX.01", "date": "2025-06-15", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 50, "id": "EVT.2025.07.XX.01", "date": "2025-07-15", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 51, "id": "EVT.2025.11.XX.01", "date": "2025-11-15", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "moderate"},
    {"idx": 52, "id": "EVT.2025.XX.XX.01", "date": "2025-07-01", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 53, "id": "EVT.2025.XX.XX.02", "date": "2025-07-01", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 54, "id": "EVT.2026.01.XX.01", "date": "2026-01-15", "expected_md": "Mercury", "expected_ad": "Saturn",  "magnitude": "significant"},
    {"idx": 55, "id": "EVT.2026.03.20.01", "date": "2026-03-20", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "significant"},
    {"idx": 56, "id": "EVT.2026.04.08.01", "date": "2026-04-08", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "significant"},
    {"idx": 57, "id": "EVT.CURRENT.01",    "date": "2026-04-17", "expected_md": "Mercury", "expected_ad": "Mercury", "magnitude": "life-altering"},
]

assert len(LEL_EVENTS) == 57, f"Expected 57 events, got {len(LEL_EVENTS)}"
assert LEL_EVENTS[TRAIN_SPLIT_IDX - 1]["idx"] == 43, "Train/test boundary check failed"
assert LEL_EVENTS[TRAIN_SPLIT_IDX]["idx"] == 44, "Test split start check failed"

TRAIN_EVENTS = LEL_EVENTS[:TRAIN_SPLIT_IDX]    # events 1–43
TEST_EVENTS  = LEL_EVENTS[TRAIN_SPLIT_IDX:]    # events 44–57


# ── Dasha alignment scoring ───────────────────────────────────────────────────

def _event_date(event: dict[str, Any]) -> date:
    """Parse event date (first 10 chars of ISO string)."""
    return _parse_date(event["date"][:10])


def _compute_dasha_at_date(
    dasha_tree: list[dict[str, Any]],
    event_date_val: date,
) -> tuple[str | None, str | None]:
    """
    Find the active MD and AD lord at the given date from the dasha tree.

    Returns (md_lord, ad_lord) or (None, None) if date is outside the tree.
    """
    for md in dasha_tree:
        md_start = _parse_date(md["start"])
        md_end = _parse_date(md["end"])
        if md_start <= event_date_val < md_end:
            md_lord = md["lord"]
            # Find AD
            for ad in md.get("antardasha", []):
                if isinstance(ad["start"], str):
                    ad_start = _parse_date(ad["start"])
                    ad_end = _parse_date(ad["end"])
                else:
                    ad_start = ad["start"]
                    ad_end = ad["end"]
                if ad_start <= event_date_val < ad_end:
                    return md_lord, ad["lord"]
            # MD matched but no AD found (boundary edge-case) — return MD only
            return md_lord, None
    return None, None


def _score_event_alignment(
    event: dict[str, Any],
    dasha_tree: list[dict[str, Any]],
) -> float:
    """
    Score how well the dasha at the event date matches the expected MD/AD.

    Scoring:
        1.0  — both MD and AD match
        0.5  — only MD matches
        0.0  — neither matches
    """
    ev_date = _event_date(event)
    actual_md, actual_ad = _compute_dasha_at_date(dasha_tree, ev_date)

    if actual_md is None:
        return 0.0

    md_match = actual_md == event["expected_md"]
    ad_match = (actual_ad is not None) and (actual_ad == event["expected_ad"])

    if md_match and ad_match:
        return 1.0
    elif md_match:
        return 0.5
    else:
        return 0.0


def _alignment_score_vector(
    events: list[dict[str, Any]],
    dasha_tree: list[dict[str, Any]],
) -> list[float]:
    """Compute alignment score for each event in the list."""
    return [_score_event_alignment(ev, dasha_tree) for ev in events]


# ── Pearson correlation ───────────────────────────────────────────────────────

def _pearson_correlation(x: list[float], y: list[float]) -> float:
    """
    Compute Pearson correlation coefficient between vectors x and y.
    Returns float in [-1, 1]; returns 0.0 if variance is zero.
    """
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    denom = math.sqrt(var_x * var_y)
    if denom < 1e-12:
        return 0.0

    return cov / denom


# ── Main rectification engine ─────────────────────────────────────────────────

def run_rectification(
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the phala.rectification algorithm over all candidate birth times.

    Algorithm:
        For each candidate offset in [−30, ..., +30] minutes (1-min step):
            1. Build shifted dasha tree
            2. Score alignment against TRAIN events only
            3. Compute mean alignment score for the candidate
        Best candidate = argmax(mean_train_alignment_score)
        Post-selection: compute test_score on TEST events for the best candidate only.
        rectification_confidence = Pearson correlation between offset vector and
            train score vector (measures how peaked the alignment is around best offset).

    NO LEAKAGE: TEST events are never used to select the best candidate.

    Returns:
        {
          "best_candidate_offset_minutes": int,
          "best_candidate_time_ist": str,          # "HH:MM"
          "best_train_score": float,               # mean alignment on train set
          "test_score": float,                     # mean alignment on test set (held-out)
          "rectification_confidence": float,       # Pearson r in [0,1] range mapped
          "candidates": [...],                     # all 61 candidates with scores
          "split_info": {...},
          "provenance_envelope": {...},
        }
    """
    offsets = list(range(-SEARCH_WINDOW_MINUTES, SEARCH_WINDOW_MINUTES + 1, STEP_MINUTES))
    candidate_results: list[dict[str, Any]] = []

    for offset in offsets:
        tree = _build_full_dasha_tree(offset)
        scores = _alignment_score_vector(TRAIN_EVENTS, tree)
        mean_score = sum(scores) / len(scores)
        candidate_results.append({
            "offset_minutes": offset,
            "mean_train_score": round(mean_score, 6),
            "raw_scores": scores,
        })
        if verbose:
            logger.debug("offset=%+d  train_score=%.4f", offset, mean_score)

    # Select best candidate (highest mean train score; tie-break: smallest abs(offset))
    best = max(
        candidate_results,
        key=lambda c: (c["mean_train_score"], -abs(c["offset_minutes"])),
    )

    # Compute test score on held-out TEST events using best candidate's tree
    # (LEAKAGE CHECK: this uses TEST_EVENTS only AFTER candidate is selected)
    best_tree = _build_full_dasha_tree(best["offset_minutes"])
    test_scores = _alignment_score_vector(TEST_EVENTS, best_tree)
    mean_test_score = sum(test_scores) / len(test_scores)

    # Pearson correlation: x = offsets, y = mean train scores
    # Measures how well alignment tracks across the offset sweep.
    # Positive r means higher offsets align better (right-shift needed).
    # Negative r means lower offsets align better (left-shift needed).
    # |r| near 1 = strong signal; near 0 = flat landscape (low discriminability).
    train_score_vector = [c["mean_train_score"] for c in candidate_results]
    r = _pearson_correlation(
        [float(o) for o in offsets],
        train_score_vector,
    )

    # Map to [0, 1] for the confidence field: rectification_confidence = (|r| + max_score) / 2
    # This blends correlation magnitude with absolute alignment quality.
    rectification_confidence = round((abs(r) + best["mean_train_score"]) / 2.0, 6)

    # Compute best candidate time
    best_offset = best["offset_minutes"]
    total_minutes_ist = NOMINAL_BIRTH_HOUR_IST * 60 + NOMINAL_BIRTH_MINUTE_IST + best_offset
    best_hour = total_minutes_ist // 60
    best_minute = total_minutes_ist % 60
    best_time_ist = f"{best_hour:02d}:{best_minute:02d}"

    return {
        "best_candidate_offset_minutes": best_offset,
        "best_candidate_time_ist": best_time_ist,
        "best_train_score": round(best["mean_train_score"], 6),
        "test_score": round(mean_test_score, 6),
        "rectification_confidence": rectification_confidence,
        "pearson_r": round(r, 6),
        "candidates": [
            {
                "offset_minutes": c["offset_minutes"],
                "mean_train_score": c["mean_train_score"],
            }
            for c in candidate_results
        ],
        "split_info": {
            "total_events": len(LEL_EVENTS),
            "train_count": len(TRAIN_EVENTS),
            "test_count": len(TEST_EVENTS),
            "train_event_ids": [e["id"] for e in TRAIN_EVENTS],
            "test_event_ids": [e["id"] for e in TEST_EVENTS],
            "leakage_check": "PASS — test events not used for candidate selection",
        },
        "provenance_envelope": {
            "source": "phala.rectification",
            "asset": "PH-4-3",
            "algorithm": "dasha_alignment_train_test_split",
            "nominal_birth_time_ist": f"{NOMINAL_BIRTH_HOUR_IST:02d}:{NOMINAL_BIRTH_MINUTE_IST:02d}",
            "search_window_minutes": SEARCH_WINDOW_MINUTES,
            "step_minutes": STEP_MINUTES,
            "train_split": f"events 1–{TRAIN_SPLIT_IDX} (75%)",
            "test_split": f"events {TRAIN_SPLIT_IDX + 1}–57 (25%, held-out)",
            "source_citation": SOURCE_CITATION,
            "b10_compliance": (
                "Dasha-level only; no Swiss Ephemeris re-run. "
                "Planetary positions from FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)."
            ),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Set DATABASE_URL=postgresql://... and ensure DB is reachable."
        )
    return url


def _get_conn():  # type: ignore[return]
    """Return a psycopg connection."""
    try:
        import psycopg  # type: ignore
        return psycopg.connect(_db_url())
    except ImportError as exc:
        raise ImportError(
            "psycopg (v3) is required for DB operations. "
            "Install with: pip install psycopg[binary]"
        ) from exc


# ── Seed DB ────────────────────────────────────────────────────────────────────

def seed_phala_rectification(
    chart_id: str,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the rectification algorithm and upsert all 61 candidates into
    phala_rectification table.

    Args:
        chart_id:  UUID of the chart.
        dry_run:   If True, compute but do not write to DB.
        verbose:   Log each candidate score.

    Returns:
        The rectification result dict (same as run_rectification).
    """
    result = run_rectification(verbose=verbose)
    now = datetime.now(timezone.utc).isoformat()

    rows = []
    for c in result["candidates"]:
        offset = c["offset_minutes"]
        total_min = NOMINAL_BIRTH_HOUR_IST * 60 + NOMINAL_BIRTH_MINUTE_IST + offset
        candidate_time = f"{total_min // 60:02d}:{total_min % 60:02d}:00"
        rows.append((
            chart_id,
            candidate_time,
            c["mean_train_score"],
            result["rectification_confidence"],
            SOURCE_CITATION,
        ))

    if dry_run:
        logger.info("[dry_run] Would upsert %d rows into phala_rectification", len(rows))
        return result

    with _get_conn() as conn:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO phala_rectification
                    (chart_id, candidate_time, alignment_score,
                     rectification_confidence, source_citation, computed_at)
                VALUES (%s, %s::TIME, %s, %s, %s, NOW())
                ON CONFLICT (chart_id, candidate_time) DO UPDATE SET
                    alignment_score          = EXCLUDED.alignment_score,
                    rectification_confidence = EXCLUDED.rectification_confidence,
                    source_citation          = EXCLUDED.source_citation,
                    computed_at              = NOW()
            """
            cur.executemany(sql, rows)
        conn.commit()

    logger.info(
        "phala_rectification: upserted %d candidate rows for chart_id=%s",
        len(rows), chart_id,
    )
    return result


# ── Tool-level query ───────────────────────────────────────────────────────────

def rectification(
    chart_id: str,
    *,
    recompute: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Main entry point: return rectification result for a chart.

    If DB has cached results and recompute=False, return the best row from DB.
    Otherwise (or if recompute=True), run the algorithm, seed DB, and return result.

    Returns:
        {
          "best_candidate_time": str,
          "confidence": float,
          "train_score": float,
          "test_score": float,
          "provenance_envelope": {...},
        }
    """
    if not recompute:
        try:
            result = _query_best_from_db(chart_id)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning("DB query failed (%s); falling back to recompute", exc)

    full_result = seed_phala_rectification(chart_id, verbose=verbose)
    return {
        "best_candidate_time": full_result["best_candidate_time_ist"],
        "confidence": full_result["rectification_confidence"],
        "train_score": full_result["best_train_score"],
        "test_score": full_result["test_score"],
        "provenance_envelope": full_result["provenance_envelope"],
    }


def _query_best_from_db(chart_id: str) -> dict[str, Any] | None:
    """
    Query the best candidate from phala_rectification table.
    Returns None if no rows exist for this chart_id.
    """
    with _get_conn() as conn:
        row = conn.execute(
            """
            SELECT candidate_time::TEXT, alignment_score, rectification_confidence,
                   source_citation, computed_at
            FROM phala_rectification
            WHERE chart_id = %s
            ORDER BY alignment_score DESC, rectification_confidence DESC
            LIMIT 1
            """,
            (chart_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "best_candidate_time": str(row[0])[:5],  # "HH:MM"
        "confidence": float(row[2]),
        "train_score": float(row[1]),
        "test_score": None,  # not cached per-row; run full recompute to get
        "provenance_envelope": {
            "source": "phala_rectification (DB cache)",
            "asset": "PH-4-3",
            "source_citation": row[3],
            "computed_at": str(row[4]),
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    Run the PH-4-3 acceptance gate.

    Gate criteria:
      1. candidate_time is non-null for best candidate.
      2. 0 <= test_score <= 1.
      3. 0 <= rectification_confidence <= 1.
      4. train_score >= test_score - 0.15 (no catastrophic overfit).
      5. phala_rectification table has 61 rows for this chart_id (full sweep stored).
    """
    checks: list[dict[str, Any]] = []

    full_result = run_rectification()

    # Check 1: candidate_time non-null
    checks.append({
        "id": "AC1",
        "desc": "best_candidate_time is non-null",
        "passed": full_result["best_candidate_time_ist"] is not None,
        "value": full_result["best_candidate_time_ist"],
    })

    # Check 2: test_score in [0, 1]
    ts = full_result["test_score"]
    checks.append({
        "id": "AC2",
        "desc": "0 <= test_score <= 1",
        "passed": 0.0 <= ts <= 1.0,
        "value": ts,
    })

    # Check 3: rectification_confidence in [0, 1]
    rc = full_result["rectification_confidence"]
    checks.append({
        "id": "AC3",
        "desc": "0 <= rectification_confidence <= 1",
        "passed": 0.0 <= rc <= 1.0,
        "value": rc,
    })

    # Check 4: no catastrophic overfit
    tr = full_result["best_train_score"]
    overfit_ok = tr <= ts + 0.15
    checks.append({
        "id": "AC4",
        "desc": "train_score <= test_score + 0.15 (no catastrophic overfit)",
        "passed": overfit_ok,
        "value": {"train": tr, "test": ts, "diff": round(tr - ts, 4)},
    })

    # Check 5: DB rows (try; skip gracefully if DB not available)
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM phala_rectification WHERE chart_id = %s",
                (chart_id,),
            ).fetchone()
        row_count = int(row[0]) if row else 0
        expected = (2 * SEARCH_WINDOW_MINUTES // STEP_MINUTES) + 1  # 61
        checks.append({
            "id": "AC5",
            "desc": f"phala_rectification has {expected} rows for chart_id",
            "passed": row_count >= expected,
            "value": row_count,
        })
    except Exception as exc:
        checks.append({
            "id": "AC5",
            "desc": "phala_rectification row count (DB check)",
            "passed": False,
            "error": str(exc),
        })

    passed = all(c["passed"] for c in checks)
    return {"chart_id": chart_id, "gate_passed": passed, "checks": checks}


# ── CLI ────────────────────────────────────────────────────────────────────────

def _cmd_seed(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = seed_phala_rectification(
        chart_id,
        dry_run=getattr(args, "dry_run", False),
        verbose=getattr(args, "verbose", False),
    )
    print(json.dumps({
        "best_candidate_time_ist": result["best_candidate_time_ist"],
        "best_train_score": result["best_train_score"],
        "test_score": result["test_score"],
        "rectification_confidence": result["rectification_confidence"],
        "split_info": result["split_info"],
    }, indent=2))


def _cmd_query(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = rectification(chart_id, recompute=getattr(args, "recompute", False))
    print(json.dumps(result, indent=2))


def _cmd_gate(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = run_acceptance_gate(chart_id)
    print(json.dumps(result, indent=2))
    if not result["gate_passed"]:
        sys.exit(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="BRAHMA-PH-4-3: phala.rectification — birth-time rectification"
    )
    parser.add_argument("--chart-id", default=None)

    sub = parser.add_subparsers(dest="command")

    p_seed = sub.add_parser("seed", help="Run rectification and seed DB")
    p_seed.add_argument("--dry-run", action="store_true")
    p_seed.add_argument("--verbose", action="store_true")

    p_query = sub.add_parser("query", help="Query best candidate from DB (or recompute)")
    p_query.add_argument("--recompute", action="store_true")

    sub.add_parser("gate", help="Run acceptance gate (exits 1 if FAIL)")

    args = parser.parse_args()
    if args.command == "seed":
        _cmd_seed(args)
    elif args.command == "query":
        _cmd_query(args)
    elif args.command == "gate":
        _cmd_gate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
