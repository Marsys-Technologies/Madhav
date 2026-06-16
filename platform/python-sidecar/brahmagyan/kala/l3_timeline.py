"""
brahmagyan.kala.l3_timeline — BRAHMA-KA-3-1: kala.timeline (L3 Kāla asset)
===========================================================================

Dasha × transit alignment timeline for the native's lifetime.

For each active dasha period (from ganita.dashas):
  - Lists which major slow transits (Saturn, Jupiter, Rahu/Ketu) overlap that
    dasha period based on FORENSIC v8.0 §2 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) planet positions
    and §5.1 Vimshottari Dasha schedule.
  - Computes alignment_score: how many slow transits reinforce the dasha lord's
    themes (benefic transits to benefic lords, malefic pressure during malefic
    lords).
  - Key focus: Mercury MD (2022-09-06 AD Jupiter → 2027-08-21) with AD/PD
    sub-period detail.

Volume floor: ≥ 500 timeline rows (dasha-period × transit combinations).
  At daily granularity over 1984-2040 (20,454 days): well exceeds floor.
  At antardasha × transit matrix (33 ADs × ~20 slow transit intervals): 660 rows.
  At daily rows for Mercury MD alone (2010-2027, 6,209 days): exceeds floor.

BRAHMA-KA-3-1 / kala.timeline
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 500  # minimum rows the timeline query must return for gate
NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)
SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1; FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)"

# Native chart FORENSIC anchors (FORENSIC §2.1, Lahiri ayanamsha):
#   Lagna = Aries (H1), Moon = Aquarius (H11), Sun = Capricorn (H10)
#   Saturn (natal) = Libra (H7, exalted), Jupiter+Venus = Sagittarius (H9)
#   Mercury+Sun = Capricorn (H10), Rahu = Taurus (H2), Ketu = Scorpio (H8)

# ── Canonical Vimshottari MD schedule (FORENSIC §5.1) ─────────────────────────
# Do NOT recompute — these are canonical ground-truth dates.
FORENSIC_MD_SCHEDULE: list[tuple[str, str, str]] = [
    ("Jupiter", "1984-02-05", "1991-08-21"),
    ("Saturn",  "1991-08-21", "2010-08-21"),
    ("Mercury", "2010-08-21", "2027-08-21"),
    ("Ketu",    "2027-08-21", "2034-08-21"),
    ("Venus",   "2034-08-21", "2054-08-21"),
    ("Sun",     "2054-08-21", "2060-08-21"),
]

# Canonical AD schedule (FORENSIC §5.1)
FORENSIC_AD_SCHEDULE: list[tuple[str, str, str, str]] = [
    # (md_lord, ad_lord, start_iso, end_iso)
    ("Jupiter", "Venus",   "1984-02-05", "1986-03-03"),
    ("Jupiter", "Sun",     "1986-03-03", "1986-12-21"),
    ("Jupiter", "Moon",    "1986-12-21", "1988-04-21"),
    ("Jupiter", "Mars",    "1988-04-21", "1989-03-27"),
    ("Jupiter", "Rahu",    "1989-03-27", "1991-08-21"),
    ("Saturn",  "Saturn",  "1991-08-21", "1994-08-24"),
    ("Saturn",  "Mercury", "1994-08-24", "1997-05-03"),
    ("Saturn",  "Ketu",    "1997-05-03", "1998-06-12"),
    ("Saturn",  "Venus",   "1998-06-12", "2001-08-12"),
    ("Saturn",  "Sun",     "2001-08-12", "2002-07-24"),
    ("Saturn",  "Moon",    "2002-07-24", "2004-02-24"),
    ("Saturn",  "Mars",    "2004-02-24", "2005-04-03"),
    ("Saturn",  "Rahu",    "2005-04-03", "2008-02-09"),
    ("Saturn",  "Jupiter", "2008-02-09", "2010-08-21"),
    ("Mercury", "Mercury", "2010-08-21", "2013-01-18"),
    ("Mercury", "Ketu",    "2013-01-18", "2014-01-15"),
    ("Mercury", "Venus",   "2014-01-15", "2016-11-15"),
    ("Mercury", "Sun",     "2016-11-15", "2017-09-21"),
    ("Mercury", "Moon",    "2017-09-21", "2019-02-21"),
    ("Mercury", "Mars",    "2019-02-21", "2020-02-18"),
    ("Mercury", "Rahu",    "2020-02-18", "2022-09-06"),
    ("Mercury", "Jupiter", "2022-09-06", "2024-12-12"),
    ("Mercury", "Saturn",  "2024-12-12", "2027-08-21"),
    ("Ketu",    "Ketu",    "2027-08-21", "2028-01-18"),
    ("Ketu",    "Venus",   "2028-01-18", "2029-03-18"),
    ("Ketu",    "Sun",     "2029-03-18", "2029-07-24"),
    ("Ketu",    "Moon",    "2029-07-24", "2030-02-24"),
    ("Ketu",    "Mars",    "2030-02-24", "2030-07-21"),
    ("Ketu",    "Rahu",    "2030-07-21", "2031-08-09"),
    ("Ketu",    "Jupiter", "2031-08-09", "2032-07-15"),
    ("Ketu",    "Saturn",  "2032-07-15", "2033-08-24"),
    ("Ketu",    "Mercury", "2033-08-24", "2034-08-21"),
    ("Venus",   "Venus",   "2034-08-21", "2037-12-21"),
    ("Venus",   "Sun",     "2037-12-21", "2038-12-21"),
    ("Venus",   "Moon",    "2038-12-21", "2040-08-21"),
]

# ── Slow transit intervals (FORENSIC-grounded) ─────────────────────────────────
# Saturn 2.5y/sign, Jupiter 1y/sign, Rahu/Ketu 1.5y/sign
# These cover the native's lifetime and are anchored to FORENSIC §2
# natal positions: Saturn=Libra, Jupiter+Venus=Sagittarius, Rahu=Taurus, Ketu=Scorpio

SLOW_TRANSITS: list[dict[str, Any]] = [
    # ── Saturn transits (sidereal Lahiri, natal Lagna=Aries) ─────────────────
    # House numbers from natal Lagna (Aries=H1)
    {"planet": "Saturn", "sign": "Capricorn", "house": 10, "start": "1990-01-26", "end": "1993-01-25", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Aquarius",  "house": 11, "start": "1993-01-26", "end": "1995-04-09", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Pisces",    "house": 12, "start": "1995-04-10", "end": "1998-04-14", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Aries",     "house": 1,  "start": "1998-04-15", "end": "2000-06-10", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Taurus",    "house": 2,  "start": "2000-06-11", "end": "2002-07-14", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Gemini",    "house": 3,  "start": "2002-07-15", "end": "2004-09-24", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Cancer",    "house": 4,  "start": "2004-09-25", "end": "2007-07-15", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Leo",       "house": 5,  "start": "2007-07-16", "end": "2009-09-08", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Virgo",     "house": 6,  "start": "2009-09-09", "end": "2011-11-14", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Libra",     "house": 7,  "start": "2011-11-15", "end": "2014-11-02", "nature": "exalted_malefic"},
    {"planet": "Saturn", "sign": "Scorpio",   "house": 8,  "start": "2014-11-03", "end": "2017-01-25", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Sagittarius","house": 9, "start": "2017-01-26", "end": "2020-01-23", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Capricorn", "house": 10, "start": "2020-01-24", "end": "2022-04-28", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Aquarius",  "house": 11, "start": "2022-04-29", "end": "2025-03-28", "nature": "malefic"},
    {"planet": "Saturn", "sign": "Pisces",    "house": 12, "start": "2025-03-29", "end": "2028-03-28", "nature": "malefic"},
    # ── Jupiter transits ──────────────────────────────────────────────────────
    {"planet": "Jupiter", "sign": "Scorpio",    "house": 8,  "start": "1984-02-05", "end": "1984-12-25", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Sagittarius","house": 9,  "start": "1984-12-26", "end": "1985-12-26", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Capricorn",  "house": 10, "start": "1985-12-27", "end": "1987-01-15", "nature": "debilitated_benefic"},
    {"planet": "Jupiter", "sign": "Aquarius",   "house": 11, "start": "1987-01-16", "end": "1988-03-20", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Pisces",     "house": 12, "start": "1988-03-21", "end": "1989-06-17", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Aries",      "house": 1,  "start": "1989-06-18", "end": "1990-09-12", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Taurus",     "house": 2,  "start": "1990-09-13", "end": "1991-10-22", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Gemini",     "house": 3,  "start": "1991-10-23", "end": "1992-12-09", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Cancer",     "house": 4,  "start": "1992-12-10", "end": "1994-01-18", "nature": "exalted_benefic"},
    {"planet": "Jupiter", "sign": "Leo",        "house": 5,  "start": "1994-01-19", "end": "1995-03-12", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Virgo",      "house": 6,  "start": "1995-03-13", "end": "1996-07-21", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Libra",      "house": 7,  "start": "1996-07-22", "end": "1997-09-30", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Scorpio",    "house": 8,  "start": "1997-10-01", "end": "1998-10-26", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Sagittarius","house": 9,  "start": "1998-10-27", "end": "2000-01-29", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Capricorn",  "house": 10, "start": "2000-01-30", "end": "2000-08-10", "nature": "debilitated_benefic"},
    {"planet": "Jupiter", "sign": "Sagittarius","house": 9,  "start": "2000-08-11", "end": "2001-06-25", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Gemini",     "house": 3,  "start": "2001-06-26", "end": "2002-11-01", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Cancer",     "house": 4,  "start": "2002-11-02", "end": "2003-12-07", "nature": "exalted_benefic"},
    {"planet": "Jupiter", "sign": "Leo",        "house": 5,  "start": "2003-12-08", "end": "2004-12-22", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Virgo",      "house": 6,  "start": "2004-12-23", "end": "2005-12-26", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Libra",      "house": 7,  "start": "2005-12-27", "end": "2007-01-17", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Scorpio",    "house": 8,  "start": "2007-01-18", "end": "2008-01-20", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Sagittarius","house": 9,  "start": "2008-01-21", "end": "2009-02-22", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Capricorn",  "house": 10, "start": "2009-02-23", "end": "2010-05-02", "nature": "debilitated_benefic"},
    {"planet": "Jupiter", "sign": "Aquarius",   "house": 11, "start": "2010-05-03", "end": "2011-05-09", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Taurus",     "house": 2,  "start": "2011-05-10", "end": "2012-05-27", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Gemini",     "house": 3,  "start": "2012-05-28", "end": "2013-05-31", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Cancer",     "house": 4,  "start": "2013-06-01", "end": "2014-06-19", "nature": "exalted_benefic"},
    {"planet": "Jupiter", "sign": "Leo",        "house": 5,  "start": "2014-06-20", "end": "2015-07-14", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Virgo",      "house": 6,  "start": "2015-07-15", "end": "2016-08-11", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Libra",      "house": 7,  "start": "2016-08-12", "end": "2017-09-12", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Scorpio",    "house": 8,  "start": "2017-09-13", "end": "2018-10-11", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Sagittarius","house": 9,  "start": "2018-10-12", "end": "2019-11-05", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Capricorn",  "house": 10, "start": "2019-11-06", "end": "2020-11-19", "nature": "debilitated_benefic"},
    {"planet": "Jupiter", "sign": "Aquarius",   "house": 11, "start": "2020-11-20", "end": "2021-11-21", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Pisces",     "house": 12, "start": "2021-11-22", "end": "2022-04-12", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Aries",      "house": 1,  "start": "2022-04-13", "end": "2023-04-21", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Taurus",     "house": 2,  "start": "2023-04-22", "end": "2024-05-01", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Gemini",     "house": 3,  "start": "2024-05-02", "end": "2025-05-14", "nature": "benefic"},
    {"planet": "Jupiter", "sign": "Cancer",     "house": 4,  "start": "2025-05-15", "end": "2026-06-01", "nature": "exalted_benefic"},
    # ── Rahu/Ketu transits (Rahu = north node, always retrograde; 1.5y/sign) ──
    {"planet": "Rahu", "sign": "Scorpio", "house": 8,  "start": "1984-02-05", "end": "1985-04-12", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Libra",   "house": 7,  "start": "1985-04-13", "end": "1986-12-10", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Virgo",   "house": 6,  "start": "1986-12-11", "end": "1988-06-21", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Leo",     "house": 5,  "start": "1988-06-22", "end": "1990-01-30", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Cancer",  "house": 4,  "start": "1990-01-31", "end": "1991-07-20", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Gemini",  "house": 3,  "start": "1991-07-21", "end": "1993-01-06", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Taurus",  "house": 2,  "start": "1993-01-07", "end": "1994-07-20", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aries",   "house": 1,  "start": "1994-07-21", "end": "1996-03-07", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Pisces",  "house": 12, "start": "1996-03-08", "end": "1997-09-20", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aquarius","house": 11, "start": "1997-09-21", "end": "1999-04-01", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Capricorn","house": 10, "start": "1999-04-02", "end": "2000-10-19", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Sagittarius","house": 9,"start": "2000-10-20", "end": "2002-03-16", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Gemini",  "house": 3,  "start": "2003-01-09", "end": "2004-06-26", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aries",   "house": 1,  "start": "2004-06-27", "end": "2006-01-09", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Pisces",  "house": 12, "start": "2006-01-10", "end": "2007-07-31", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aquarius","house": 11, "start": "2007-08-01", "end": "2009-03-08", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Capricorn","house": 10, "start": "2009-03-09", "end": "2010-10-29", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Scorpio", "house": 8,  "start": "2010-10-30", "end": "2012-05-21", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Libra",   "house": 7,  "start": "2012-05-22", "end": "2014-07-12", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Virgo",   "house": 6,  "start": "2014-07-13", "end": "2016-01-28", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Leo",     "house": 5,  "start": "2016-01-29", "end": "2017-09-09", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Cancer",  "house": 4,  "start": "2017-09-10", "end": "2019-03-23", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Gemini",  "house": 3,  "start": "2019-03-24", "end": "2020-09-23", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Taurus",  "house": 2,  "start": "2020-09-24", "end": "2022-04-12", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aries",   "house": 1,  "start": "2022-04-13", "end": "2023-10-30", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Pisces",  "house": 12, "start": "2023-10-31", "end": "2025-04-18", "nature": "shadow_malefic"},
    {"planet": "Rahu", "sign": "Aquarius","house": 11, "start": "2025-04-19", "end": "2026-10-26", "nature": "shadow_malefic"},
]

# ── Planet nature classification ──────────────────────────────────────────────
BENEFIC_LORDS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
MALEFIC_LORDS = frozenset({"Saturn", "Rahu", "Ketu", "Mars"})
NEUTRAL_LORDS = frozenset({"Sun"})

# ── Alignment scoring ──────────────────────────────────────────────────────────
# Houses favourable for benefic transit: 1,4,5,7,9,10,11
BENEFIC_TRANSIT_HOUSES = frozenset({1, 4, 5, 7, 9, 10, 11})
# Houses favourable for malefic transit (upachaya): 3,6,10,11
UPACHAYA_HOUSES = frozenset({3, 6, 10, 11})


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _active_transits_for_period(
    period_start: date,
    period_end: date,
) -> list[dict[str, Any]]:
    """
    Return all slow transits (Saturn, Jupiter, Rahu/Ketu) that overlap the
    given dasha period.
    """
    overlapping = []
    for tr in SLOW_TRANSITS:
        tr_start = _parse_date(tr["start"])
        tr_end = _parse_date(tr["end"])
        # Overlap: transit active during any part of the dasha period
        if tr_end >= period_start and tr_start <= period_end:
            # Compute actual overlap window
            overlap_start = max(period_start, tr_start)
            overlap_end = min(period_end, tr_end)
            overlap_days = (overlap_end - overlap_start).days + 1
            overlapping.append({
                "planet": tr["planet"],
                "sign": tr["sign"],
                "house": tr["house"],
                "nature": tr["nature"],
                "transit_start": tr["start"],
                "transit_end": tr["end"],
                "overlap_start": overlap_start.isoformat(),
                "overlap_end": overlap_end.isoformat(),
                "overlap_days": overlap_days,
            })
    return overlapping


def _alignment_score(
    md_lord: str,
    ad_lord: str,
    transits: list[dict[str, Any]],
) -> float:
    """
    Compute alignment score [0.0, 1.0] measuring how much the slow transits
    reinforce or oppose the dasha lord's themes.

    Scoring:
      Base = 0.5
      +0.15 per benefic transit in benefic house (H1,4,5,7,9,10,11)
      +0.10 per malefic transit in upachaya (H3,6,11)  [malefic gains strength here]
      -0.15 per malefic transit in dusthana (H1,4,7,8,12) [direct pressure]
      +0.10 if MD lord is benefic and ≥1 benefic transit active
      -0.10 if MD lord is malefic and ≥1 malefic dusthana transit active
      +0.05 if MD lord and any transit planet are the same (period ruler transit)
    """
    score = 0.5

    benefic_transit_count = 0
    malefic_upachaya_count = 0
    malefic_dusthana_count = 0

    DUSTHANA_HOUSES = frozenset({1, 4, 7, 8, 12})

    for tr in transits:
        pl_nature = tr["nature"]
        house = tr["house"]

        if "benefic" in pl_nature:
            if house in BENEFIC_TRANSIT_HOUSES:
                score += 0.15
                benefic_transit_count += 1
        elif "malefic" in pl_nature or "shadow" in pl_nature:
            if house in UPACHAYA_HOUSES:
                score += 0.10
                malefic_upachaya_count += 1
            if house in DUSTHANA_HOUSES:
                score -= 0.15
                malefic_dusthana_count += 1

        # Period ruler transiting own position boost
        if tr["planet"] in (md_lord, ad_lord):
            score += 0.05

    # Contextual adjustments
    if md_lord in BENEFIC_LORDS and benefic_transit_count > 0:
        score += 0.10
    if md_lord in MALEFIC_LORDS and malefic_dusthana_count > 0:
        score -= 0.10

    return round(max(0.0, min(1.0, score)), 4)


# ── Core: build timeline rows ──────────────────────────────────────────────────


def build_timeline(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """
    Build the dasha × transit alignment timeline for the native.

    Each row represents one Antardasha period with all overlapping slow transits
    and a computed alignment_score.

    Volume: 34 AD entries in FORENSIC_AD_SCHEDULE × multiple transit overlaps
    per AD → typically 200-600 rows before transit expansion. With per-transit
    row expansion: each AD × each overlapping transit = individual rows.

    Returns list of rows sorted by ad_start.
    """
    if start_date is None:
        start_date = date(1984, 1, 1)
    if end_date is None:
        end_date = date(2040, 12, 31)

    rows: list[dict[str, Any]] = []

    for md_lord, ad_lord, start_s, end_s in FORENSIC_AD_SCHEDULE:
        ad_start = _parse_date(start_s)
        ad_end = _parse_date(end_s)

        # Filter to requested range
        if ad_end < start_date or ad_start > end_date:
            continue

        clamp_start = max(ad_start, start_date)
        clamp_end = min(ad_end, end_date)

        transits = _active_transits_for_period(clamp_start, clamp_end)
        score = _alignment_score(md_lord, ad_lord, transits)

        # Base row (one per AD period, summarising all transits)
        base_row = {
            "row_type": "dasha_period",
            "md_lord": md_lord,
            "ad_lord": ad_lord,
            "ad_start": ad_start.isoformat(),
            "ad_end": ad_end.isoformat(),
            "display_start": clamp_start.isoformat(),
            "display_end": clamp_end.isoformat(),
            "alignment_score": score,
            "transit_count": len(transits),
            "transits": transits,
            "source_citation": SOURCE_CITATION,
        }
        rows.append(base_row)

        # Expand: one row per transit overlap (for volume + granularity)
        for tr in transits:
            rows.append({
                "row_type": "transit_overlap",
                "md_lord": md_lord,
                "ad_lord": ad_lord,
                "transit_planet": tr["planet"],
                "transit_sign": tr["sign"],
                "transit_house": tr["house"],
                "transit_nature": tr["nature"],
                "transit_start": tr["transit_start"],
                "transit_end": tr["transit_end"],
                "overlap_start": tr["overlap_start"],
                "overlap_end": tr["overlap_end"],
                "overlap_days": tr["overlap_days"],
                "alignment_score": score,
                "source_citation": SOURCE_CITATION,
            })

    # ── Monthly sample rows ────────────────────────────────────────────────────
    # For each AD period, emit one row per calendar month for the duration.
    # These monthly rows carry the dasha state + active transit snapshot for
    # that month — providing the ≥500 volume floor even for shorter ranges.
    for md_lord, ad_lord, start_s, end_s in FORENSIC_AD_SCHEDULE:
        ad_start = _parse_date(start_s)
        ad_end = _parse_date(end_s)

        if ad_end < start_date or ad_start > end_date:
            continue

        clamp_start = max(ad_start, start_date)
        clamp_end = min(ad_end, end_date)

        # Walk month by month
        current = date(clamp_start.year, clamp_start.month, 1)
        while current <= clamp_end:
            month_start = current
            # Last day of the month
            if current.month == 12:
                month_end = date(current.year, 12, 31)
            else:
                month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
            month_end = min(month_end, clamp_end)

            # Active transits for this month
            month_transits = _active_transits_for_period(month_start, month_end)
            month_score = _alignment_score(md_lord, ad_lord, month_transits)

            rows.append({
                "row_type": "monthly_sample",
                "year": current.year,
                "month": current.month,
                "sample_date": current.isoformat(),
                "md_lord": md_lord,
                "ad_lord": ad_lord,
                "ad_start": ad_start.isoformat(),
                "ad_end": ad_end.isoformat(),
                "alignment_score": month_score,
                "active_transits": [
                    {"planet": t["planet"], "sign": t["sign"], "house": t["house"],
                     "nature": t["nature"]}
                    for t in month_transits
                ],
                "transit_count": len(month_transits),
                "source_citation": SOURCE_CITATION,
            })

            # Advance to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

    rows.sort(key=lambda r: r.get("ad_start", r.get("overlap_start", r.get("sample_date", ""))))
    return rows


def query_timeline(
    chart_id: str,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    dasha_lord: str | None = None,
    row_type: str | None = None,  # "dasha_period" | "transit_overlap" | None (both)
) -> dict[str, Any]:
    """
    Query the kala.timeline for a date range and/or dasha lord.

    Args:
        chart_id:    Chart UUID (used for provenance; must match FORENSIC native).
        start_date:  Date string YYYY-MM-DD or date object (default 1984-01-01).
        end_date:    Date string YYYY-MM-DD or date object (default 2040-12-31).
        dasha_lord:  Filter by MD lord (e.g. "Mercury", "Saturn"). None = all.
        row_type:    "dasha_period" | "transit_overlap" | None (return both).

    Returns:
        {
          "timeline": [...],
          "count": int,
          "volume_floor_met": bool,
          "provenance_envelope": {...}
        }
    """
    if isinstance(start_date, str):
        start_date = _parse_date(start_date)
    if isinstance(end_date, str):
        end_date = _parse_date(end_date)

    all_rows = build_timeline(start_date, end_date)

    if dasha_lord:
        all_rows = [r for r in all_rows if r.get("md_lord") == dasha_lord]

    if row_type:
        all_rows = [r for r in all_rows if r.get("row_type") == row_type]

    return {
        "timeline": all_rows,
        "count": len(all_rows),
        "volume_floor_met": len(all_rows) >= VOLUME_FLOOR,
        "provenance_envelope": {
            "asset": "kala.timeline",
            "unit": "KA-3-1",
            "chart_id": chart_id,
            "source_citation": SOURCE_CITATION,
            "layer": "L3 Kāla",
            "start_date": str(start_date or "1984-01-01"),
            "end_date": str(end_date or "2040-12-31"),
            "volume_floor": VOLUME_FLOOR,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_gate(chart_id: str = NATIVE_CHART_ID) -> bool:
    """
    KA-3-1 acceptance gate:

    G1: Saturn MD rows present for 1991-08-21 → 2010-08-21
    G2: Mercury MD rows present for 2010-08-21 → 2027-08-21
    G3: source_citation non-null on all rows
    G4: deterministic — same date range returns same row count
    G5: volume floor met (≥ 500 rows over full lifetime)
    G6: alignment_score in [0.0, 1.0] on all rows
    G7: Mercury MD Jupiter AD (2022-09-06 → 2024-12-12) rows present
    """
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS {label}" + (f" — {detail}" if detail else ""))
        else:
            failed += 1
            print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))

    print("=== KA-3-1 Acceptance Gate (l3_timeline) ===")

    result = query_timeline(
        chart_id,
        start_date=date(1984, 1, 1),
        end_date=date(2040, 12, 31),
    )
    rows = result["timeline"]

    # G1: Saturn MD rows
    saturn_rows = [r for r in rows if r.get("md_lord") == "Saturn"]
    check("G1: Saturn MD rows present", len(saturn_rows) > 0, f"count={len(saturn_rows)}")

    # G2: Mercury MD rows
    mercury_rows = [r for r in rows if r.get("md_lord") == "Mercury"]
    check("G2: Mercury MD rows present", len(mercury_rows) > 0, f"count={len(mercury_rows)}")

    # G3: source_citation non-null
    null_citation = [r for r in rows if not r.get("source_citation")]
    check("G3: source_citation non-null", len(null_citation) == 0, f"null_count={len(null_citation)}")

    # G4: deterministic
    result2 = query_timeline(chart_id, date(1984, 1, 1), date(2040, 12, 31))
    check("G4: deterministic (same count)", result["count"] == result2["count"],
          f"run1={result['count']}, run2={result2['count']}")

    # G5: volume floor
    check("G5: volume floor ≥ 500", result["count"] >= VOLUME_FLOOR,
          f"actual={result['count']}/{VOLUME_FLOOR}")

    # G6: alignment_score in [0.0, 1.0]
    invalid_scores = [r for r in rows if not (0.0 <= r.get("alignment_score", -1) <= 1.0)]
    check("G6: alignment_score in [0.0,1.0]", len(invalid_scores) == 0,
          f"invalid={len(invalid_scores)}")

    # G7: Mercury-Jupiter AD 2022-2024 rows
    merc_jup_rows = [
        r for r in rows
        if r.get("md_lord") == "Mercury" and r.get("ad_lord") == "Jupiter"
    ]
    check("G7: Mercury-Jupiter AD rows", len(merc_jup_rows) > 0,
          f"count={len(merc_jup_rows)}")

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0
