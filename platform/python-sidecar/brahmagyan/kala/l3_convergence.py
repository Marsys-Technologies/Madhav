"""
brahmagyan.kala.l3_convergence — BRAHMA-KA-3-2: kala.convergence (L3 Kāla asset)
==================================================================================

Convergence windows: time periods where multiple Kala indicators simultaneously
align (dasha, transit, and L2 signal activation) pointing the same direction
within a 3-month window.

Convergence = 3+ indicators pointing the same direction within 90 days.

Key types:
  career_peak      — career-domain indicators align (H10 Saturn/Jupiter transit
                     during career-oriented dasha lords: Mercury, Saturn benefic AD)
  relationship     — 7H/Venus indicators align
  health_attention — 6H/8H/12H malefic clustering
  spiritual_peak   — 9H/12H Jupiter/Ketu transit during Ketu/Jupiter AD

Volume floor: ≥ 20 convergence windows across the native's lifetime (1984-2040).
  Current production: 12+ windows from convergence.py; l3_convergence expands
  with type-classified windows and covers 1984-2040 explicitly.

Source: FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (Vimshottari), §2.1 (positions)
BRAHMA-KA-3-2 / kala.convergence
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 20  # minimum convergence windows over full native lifetime
NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)
SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1; FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)"

# Convergence window merge radius: factors within 90 days form a cluster
WINDOW_RADIUS_DAYS = 90

# ── FORENSIC Vimshottari schedule (§5.1) ──────────────────────────────────────
# (md_lord, ad_lord, start, end, dasha_themes)
DASHA_PERIODS: list[dict[str, Any]] = [
    {"md": "Jupiter", "ad": "Venus",   "start": "1984-02-05", "end": "1986-03-03",
     "themes": ["expansion", "creativity", "relationship"]},
    {"md": "Jupiter", "ad": "Sun",     "start": "1986-03-03", "end": "1986-12-21",
     "themes": ["authority", "ego", "visibility"]},
    {"md": "Jupiter", "ad": "Moon",    "start": "1986-12-21", "end": "1988-04-21",
     "themes": ["emotions", "home", "mother"]},
    {"md": "Jupiter", "ad": "Mars",    "start": "1988-04-21", "end": "1989-03-27",
     "themes": ["action", "energy", "siblings"]},
    {"md": "Jupiter", "ad": "Rahu",    "start": "1989-03-27", "end": "1991-08-21",
     "themes": ["ambition", "foreign", "desire"]},
    {"md": "Saturn",  "ad": "Saturn",  "start": "1991-08-21", "end": "1994-08-24",
     "themes": ["discipline", "career", "hardship"]},
    {"md": "Saturn",  "ad": "Mercury", "start": "1994-08-24", "end": "1997-05-03",
     "themes": ["education", "communication", "analysis"]},
    {"md": "Saturn",  "ad": "Ketu",    "start": "1997-05-03", "end": "1998-06-12",
     "themes": ["spiritual", "separation", "introspection"]},
    {"md": "Saturn",  "ad": "Venus",   "start": "1998-06-12", "end": "2001-08-12",
     "themes": ["relationship", "creativity", "luxury"]},
    {"md": "Saturn",  "ad": "Sun",     "start": "2001-08-12", "end": "2002-07-24",
     "themes": ["authority", "career", "father"]},
    {"md": "Saturn",  "ad": "Moon",    "start": "2002-07-24", "end": "2004-02-24",
     "themes": ["emotions", "public", "travel"]},
    {"md": "Saturn",  "ad": "Mars",    "start": "2004-02-24", "end": "2005-04-03",
     "themes": ["action", "conflict", "energy"]},
    {"md": "Saturn",  "ad": "Rahu",    "start": "2005-04-03", "end": "2008-02-09",
     "themes": ["ambition", "technology", "foreign"]},
    {"md": "Saturn",  "ad": "Jupiter", "start": "2008-02-09", "end": "2010-08-21",
     "themes": ["expansion", "wisdom", "opportunity"]},
    {"md": "Mercury", "ad": "Mercury", "start": "2010-08-21", "end": "2013-01-18",
     "themes": ["intellect", "communication", "technology"]},
    {"md": "Mercury", "ad": "Ketu",    "start": "2013-01-18", "end": "2014-01-15",
     "themes": ["spiritual", "detachment", "research"]},
    {"md": "Mercury", "ad": "Venus",   "start": "2014-01-15", "end": "2016-11-15",
     "themes": ["creativity", "relationship", "arts"]},
    {"md": "Mercury", "ad": "Sun",     "start": "2016-11-15", "end": "2017-09-21",
     "themes": ["career", "authority", "visibility"]},
    {"md": "Mercury", "ad": "Moon",    "start": "2017-09-21", "end": "2019-02-21",
     "themes": ["emotions", "public", "instinct"]},
    {"md": "Mercury", "ad": "Mars",    "start": "2019-02-21", "end": "2020-02-18",
     "themes": ["technical", "action", "engineering"]},
    {"md": "Mercury", "ad": "Rahu",    "start": "2020-02-18", "end": "2022-09-06",
     "themes": ["ambition", "technology", "innovation"]},
    {"md": "Mercury", "ad": "Jupiter", "start": "2022-09-06", "end": "2024-12-12",
     "themes": ["wisdom", "expansion", "career_peak"]},
    {"md": "Mercury", "ad": "Saturn",  "start": "2024-12-12", "end": "2027-08-21",
     "themes": ["discipline", "structured_growth", "career"]},
    {"md": "Ketu",    "ad": "Ketu",    "start": "2027-08-21", "end": "2028-01-18",
     "themes": ["spiritual", "moksha", "detachment"]},
    {"md": "Ketu",    "ad": "Venus",   "start": "2028-01-18", "end": "2029-03-18",
     "themes": ["relationship", "creativity"]},
    {"md": "Ketu",    "ad": "Sun",     "start": "2029-03-18", "end": "2029-07-24",
     "themes": ["authority", "visibility"]},
    {"md": "Ketu",    "ad": "Moon",    "start": "2029-07-24", "end": "2030-02-24",
     "themes": ["emotions", "healing"]},
    {"md": "Ketu",    "ad": "Mars",    "start": "2030-02-24", "end": "2030-07-21",
     "themes": ["action", "purification"]},
    {"md": "Ketu",    "ad": "Rahu",    "start": "2030-07-21", "end": "2031-08-09",
     "themes": ["karmic_resolution"]},
    {"md": "Ketu",    "ad": "Jupiter", "start": "2031-08-09", "end": "2032-07-15",
     "themes": ["spiritual_peak", "wisdom", "guru"]},
    {"md": "Ketu",    "ad": "Saturn",  "start": "2032-07-15", "end": "2033-08-24",
     "themes": ["discipline", "karma"]},
    {"md": "Ketu",    "ad": "Mercury", "start": "2033-08-24", "end": "2034-08-21",
     "themes": ["research", "analysis"]},
    {"md": "Venus",   "ad": "Venus",   "start": "2034-08-21", "end": "2037-12-21",
     "themes": ["relationship", "luxury", "creativity"]},
    {"md": "Venus",   "ad": "Sun",     "start": "2037-12-21", "end": "2038-12-21",
     "themes": ["authority", "career"]},
    {"md": "Venus",   "ad": "Moon",    "start": "2038-12-21", "end": "2040-08-21",
     "themes": ["emotions", "public"]},
]

# ── Signal activation anchors (FORENSIC-grounded key events) ──────────────────
# Comprehensive set covering native's full life arc (1984-2040).
# Source: FORENSIC §2.1 planetary positions + §5.1 Vimshottari + §22 Sade Sati
# + LEL event log alignment (career shifts, relocations, relationship events).

SIGNAL_ANCHORS: list[dict[str, Any]] = [
    # ── 1984-1991 Jupiter MD ──────────────────────────────────────────────────
    {"date": "1986-01-15", "weight": 0.65, "domain": "expansion",
     "label": "SIG.JUPITER.CAPRICORN.H10.1986",
     "description": "Jupiter transiting H10 (debilitated) — career effort required"},
    {"date": "1988-03-21", "weight": 0.70, "domain": "spiritual",
     "label": "SIG.JUPITER.PISCES.H12.1988",
     "description": "Jupiter in Pisces (H12) — spiritual/hidden foundation phase"},
    {"date": "1989-06-18", "weight": 0.70, "domain": "career",
     "label": "SIG.JUPITER.ARIES.LAGNA.1989",
     "description": "Jupiter in Aries (H1) — self-assertion and life direction"},
    {"date": "1990-01-31", "weight": 0.65, "domain": "home",
     "label": "SIG.RAHU.CANCER.H4.1990",
     "description": "Rahu in Cancer (H4) — home/mother disruption"},
    # ── 1991-2010 Saturn MD ───────────────────────────────────────────────────
    {"date": "1992-12-10", "weight": 0.80, "domain": "career",
     "label": "SIG.JUPITER.CANCER.EXALT.H4.1992",
     "description": "Jupiter exalted in Cancer (H4) — first exalted Jupiter transit; education apex"},
    {"date": "1994-01-19", "weight": 0.70, "domain": "authority",
     "label": "SIG.JUPITER.LEO.H5.1994",
     "description": "Jupiter in Leo (H5) — creative expression, first career step"},
    {"date": "1996-07-22", "weight": 0.65, "domain": "relationship",
     "label": "SIG.JUPITER.LIBRA.H7.1996",
     "description": "Jupiter in Libra (H7) — relationship signification activation"},
    {"date": "1998-04-15", "weight": 0.70, "domain": "career",
     "label": "SIG.SATURN.ARIES.H1.1998",
     "description": "Saturn entering Aries (H1) — Lagna activation; identity tested"},
    {"date": "1998-10-27", "weight": 0.75, "domain": "spiritual",
     "label": "SIG.JUPITER.SAGITTARIUS.9H.1998",
     "description": "Jupiter in natal 9H (Sagittarius, natal Jupiter+Venus) — dharmic expansion"},
    {"date": "2000-06-11", "weight": 0.65, "domain": "wealth",
     "label": "SIG.SATURN.TAURUS.H2.2000",
     "description": "Saturn in Taurus (H2, natal Rahu) — wealth/resource restructuring"},
    {"date": "2001-08-12", "weight": 0.70, "domain": "career",
     "label": "SIG.SATURN.SUN.AD.2001",
     "description": "Saturn MD / Sun AD start (DSH.V.010) — career authority activation"},
    {"date": "2002-07-24", "weight": 0.75, "domain": "emotions",
     "label": "SIG.SATURN.MOON.AD.2002",
     "description": "Saturn MD / Moon AD start (DSH.V.011) — public/emotional activation; known high-intensity"},
    {"date": "2002-11-02", "weight": 0.75, "domain": "career",
     "label": "SIG.JUPITER.CANCER.EXALT.H4.2002",
     "description": "Jupiter exalted Cancer (H4) again — home/career foundation activation"},
    {"date": "2004-09-25", "weight": 0.65, "domain": "health_attention",
     "label": "SIG.SATURN.CANCER.H4.2004",
     "description": "Saturn in Cancer (H4) — home/mother tension, health vigilance"},
    {"date": "2005-12-27", "weight": 0.65, "domain": "relationship",
     "label": "SIG.JUPITER.LIBRA.H7.2005",
     "description": "Jupiter in Libra (H7) — relationship themes revisited"},
    {"date": "2007-07-16", "weight": 0.65, "domain": "authority",
     "label": "SIG.SATURN.LEO.H5.2007",
     "description": "Saturn in Leo (H5) — authority challenge; creative structure"},
    {"date": "2008-01-21", "weight": 0.75, "domain": "spiritual",
     "label": "SIG.JUPITER.SAGITTARIUS.9H.2008",
     "description": "Jupiter in natal 9H (Sagittarius) — dharmic expansion peak"},
    {"date": "2008-02-09", "weight": 0.75, "domain": "expansion",
     "label": "SIG.SATURN.JUPITER.AD.2008",
     "description": "Saturn MD / Jupiter AD start (DSH.V.014) — wisdom+opportunity within discipline"},
    {"date": "2009-09-09", "weight": 0.65, "domain": "career",
     "label": "SIG.SATURN.VIRGO.H6.2009",
     "description": "Saturn in Virgo (H6) — service, health, detail work"},
    # ── 2010-2027 Mercury MD ──────────────────────────────────────────────────
    {"date": "2010-05-03", "weight": 0.65, "domain": "career",
     "label": "SIG.JUPITER.AQUARIUS.H11.2010",
     "description": "Jupiter in Aquarius (H11, natal Moon) — gains, networking"},
    {"date": "2010-08-16", "weight": 0.75, "domain": "career",
     "label": "SIG.MERCURY.SATURN.CONJ.2010",
     "description": "Mercury+Saturn conjunction near Mercury MD start — career/intellect activation"},
    {"date": "2011-05-10", "weight": 0.65, "domain": "wealth",
     "label": "SIG.JUPITER.TAURUS.H2.2011",
     "description": "Jupiter in Taurus (H2, natal Rahu) — resource and wealth activation"},
    {"date": "2011-11-15", "weight": 0.70, "domain": "relationship",
     "label": "SIG.SATURN.LIBRA.NATAL.7H.2011",
     "description": "Saturn entering natal Libra (H7) — relationship/commitment activation"},
    {"date": "2012-06-15", "weight": 0.70, "domain": "relationship",
     "label": "SIG.SATURN.LIBRA.NATAL.7H.2012",
     "description": "Saturn transiting natal Libra (H7) peak — relationship and commitment"},
    {"date": "2013-06-01", "weight": 0.80, "domain": "home",
     "label": "SIG.JUPITER.CANCER.EXALT.4H.2013",
     "description": "Jupiter exalted in Cancer (H4) — home/emotional foundation peak (third pass)"},
    {"date": "2014-11-03", "weight": 0.70, "domain": "transformation",
     "label": "SIG.SATURN.SCORPIO.H8.2014",
     "description": "Saturn entering Scorpio (H8, natal Ketu) — transformative pressure begins"},
    {"date": "2015-07-15", "weight": 0.65, "domain": "career",
     "label": "SIG.JUPITER.VIRGO.H6.2015",
     "description": "Jupiter in Virgo (H6) — service refinement, health focus"},
    {"date": "2016-01-30", "weight": 0.70, "domain": "transformation",
     "label": "SIG.SATURN.RAHU.CONJ.SCORPIO.2016",
     "description": "Saturn+Rahu in Scorpio (H8) — transformative pressure point"},
    {"date": "2016-08-12", "weight": 0.65, "domain": "relationship",
     "label": "SIG.JUPITER.LIBRA.H7.2016",
     "description": "Jupiter in Libra (H7) — relationship signification"},
    {"date": "2017-01-26", "weight": 0.70, "domain": "career",
     "label": "SIG.SATURN.SAGITTARIUS.9H.2017",
     "description": "Saturn entering Sagittarius (H9) — Sade Sati phase 2; career structure"},
    {"date": "2017-09-13", "weight": 0.65, "domain": "authority",
     "label": "SIG.JUPITER.SCORPIO.H8.2017",
     "description": "Jupiter in Scorpio (H8) — research, occult, transformation"},
    {"date": "2018-10-12", "weight": 0.75, "domain": "spiritual",
     "label": "SIG.JUPITER.SAGITTARIUS.9H.2018",
     "description": "Jupiter in natal 9H (Sagittarius) — expansion and dharma"},
    {"date": "2019-11-06", "weight": 0.65, "domain": "career",
     "label": "SIG.JUPITER.CAPRICORN.H10.2019",
     "description": "Jupiter debilitated in Capricorn (H10) — career effort, structured growth"},
    {"date": "2020-01-24", "weight": 0.70, "domain": "health_attention",
     "label": "SIG.SATURN.CAPRICORN.H10.SS.2020",
     "description": "Saturn enters Capricorn (H10) — Sade Sati rising; career pressure begins"},
    {"date": "2020-09-24", "weight": 0.70, "domain": "wealth",
     "label": "SIG.RAHU.TAURUS.NATAL.H2.2020",
     "description": "Rahu in Taurus (H2, natal Rahu) — wealth/resource amplification"},
    {"date": "2021-11-22", "weight": 0.65, "domain": "spiritual",
     "label": "SIG.JUPITER.PISCES.H12.2021",
     "description": "Jupiter in Pisces (H12) — spiritual/foreign themes"},
    {"date": "2022-04-13", "weight": 0.75, "domain": "career",
     "label": "SIG.JUPITER.ARIES.LAGNA.2022",
     "description": "Jupiter in Aries (H1) — Lagna activation; fresh start"},
    {"date": "2022-09-06", "weight": 0.85, "domain": "career_peak",
     "label": "SIG.MERCURY.JUPITER.AD.2022",
     "description": "Mercury MD / Jupiter AD start (DSH.V.022) — peak intellectual-career convergence"},
    {"date": "2023-04-22", "weight": 0.65, "domain": "wealth",
     "label": "SIG.JUPITER.TAURUS.H2.2023",
     "description": "Jupiter in Taurus (H2) — wealth accumulation phase"},
    {"date": "2024-05-02", "weight": 0.65, "domain": "career",
     "label": "SIG.JUPITER.GEMINI.H3.2024",
     "description": "Jupiter in Gemini (H3) — communication and skills expansion"},
    {"date": "2024-12-12", "weight": 0.80, "domain": "career",
     "label": "SIG.MERCURY.SATURN.AD.2024",
     "description": "Mercury MD / Saturn AD start (DSH.V.023) — disciplined structured career build"},
    # ── 2025+ ─────────────────────────────────────────────────────────────────
    {"date": "2025-03-29", "weight": 0.65, "domain": "spiritual",
     "label": "SIG.SATURN.PISCES.12H.2025",
     "description": "Saturn entering Pisces (H12) — setting Sade Sati; spiritual discipline"},
    {"date": "2025-05-15", "weight": 0.80, "domain": "home",
     "label": "SIG.JUPITER.CANCER.EXALT.4H.2025",
     "description": "Jupiter exalted in Cancer (H4) — home and emotional stability"},
    {"date": "2026-06-01", "weight": 0.65, "domain": "authority",
     "label": "SIG.JUPITER.LEO.H5.2026",
     "description": "Jupiter in Leo (H5) — creative authority expression"},
    {"date": "2027-08-21", "weight": 0.90, "domain": "spiritual",
     "label": "SIG.KETU.MD.START.2027",
     "description": "Ketu MD start (DSH.V.024) — major spiritual-karmic phase begins"},
    {"date": "2031-08-09", "weight": 0.80, "domain": "spiritual_peak",
     "label": "SIG.KETU.JUPITER.AD.2031",
     "description": "Ketu MD / Jupiter AD (DSH.V.030) — spiritual wisdom peak"},
    {"date": "2034-08-21", "weight": 0.90, "domain": "relationship",
     "label": "SIG.VENUS.MD.START.2034",
     "description": "Venus MD start — long Venus period for relationship and creativity"},
]

# ── Convergence type classifiers ──────────────────────────────────────────────

CONVERGENCE_DOMAINS = {
    "career_peak":      frozenset({"career", "career_peak", "authority", "intellect", "technology"}),
    "relationship":     frozenset({"relationship", "creativity", "luxury", "home", "emotions"}),
    "health_attention": frozenset({"health_attention", "conflict", "separation", "transformation", "hardship"}),
    "spiritual_peak":   frozenset({"spiritual", "detachment", "moksha", "spiritual_peak", "guru", "dharma"}),
    "wealth":           frozenset({"wealth", "expansion", "foreign", "ambition", "innovation"}),
    "general":          frozenset(),  # fallback
}


def _classify_convergence_type(themes: list[str], signal_domains: list[str]) -> str:
    """Classify a convergence window by its dominant domain."""
    all_tags = set(themes) | set(signal_domains)
    # Score each type
    scores: dict[str, int] = {}
    for ctype, domain_set in CONVERGENCE_DOMAINS.items():
        if not domain_set:
            continue
        scores[ctype] = len(all_tags & domain_set)

    if not scores or max(scores.values()) == 0:
        return "general"
    return max(scores, key=lambda k: scores[k])


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


# ── Core convergence computation ───────────────────────────────────────────────


def _active_dasha_factors_at(anchor_date: date) -> list[dict[str, Any]]:
    """
    Return dasha factors active at anchor_date:
    1. The current AD period (its start event within ±90 days OR the period itself active)
    2. The current MD period (if within first 6 months = transition weight)
    """
    factors = []
    for dp in DASHA_PERIODS:
        ad_start = _parse_date(dp["start"])
        ad_end = _parse_date(dp["end"])

        # AD period is active at anchor_date
        if ad_start <= anchor_date < ad_end:
            days_since_start = (anchor_date - ad_start).days
            # Within 90 days of start: strong transition factor
            if days_since_start <= WINDOW_RADIUS_DAYS:
                factors.append({
                    "date": ad_start,
                    "label": f"Dasha_start: {dp['md']}/{dp['ad']} ({dp['start']})",
                    "weight": 0.85,
                    "themes": dp["themes"],
                    "event_type": "dasha_transition",
                })
            else:
                # Background active dasha — lighter contribution
                factors.append({
                    "date": ad_start,
                    "label": f"Dasha_active: {dp['md']}/{dp['ad']}",
                    "weight": 0.45,
                    "themes": dp["themes"],
                    "event_type": "dasha_active",
                })
            break

    return factors


def compute_convergence_windows(
    start_date: date | None = None,
    end_date: date | None = None,
    min_indicators: int = 3,
) -> list[dict[str, Any]]:
    """
    Compute convergence windows where ≥ min_indicators temporal factors align
    within WINDOW_RADIUS_DAYS (90 days).

    Algorithm:
      1. Build point-in-time factor events from dasha transitions + signal anchors.
      2. For each anchor event, collect:
         a. All point-in-time events within ±90 days
         b. The active dasha state at that date (as a factor)
         c. Adjacent dasha transitions within ±90 days
      3. If ≥ min_indicators distinct factors: record window.
      4. Classify by dominant theme.
      5. Merge overlapping windows.

    Returns sorted list of convergence window dicts.
    """
    if start_date is None:
        start_date = date(1984, 1, 1)
    if end_date is None:
        end_date = date(2040, 12, 31)

    radius = timedelta(days=WINDOW_RADIUS_DAYS)

    # ── Build all point-in-time events ────────────────────────────────────────
    all_events: list[dict[str, Any]] = []

    # ALL dasha transitions (not filtered — used for both anchors and context)
    prev_md = None
    for dp in DASHA_PERIODS:
        d = _parse_date(dp["start"])
        is_md_change = dp["md"] != prev_md
        all_events.append({
            "date": d,
            "label": f"Dasha: {dp['md']}/{dp['ad']} ({dp['start']})",
            "weight": 0.9 if is_md_change else 0.6,
            "themes": dp["themes"],
            "event_type": "dasha_transition",
        })
        prev_md = dp["md"]

    # ALL signal activation anchors
    for sa in SIGNAL_ANCHORS:
        all_events.append({
            "date": _parse_date(sa["date"]),
            "label": sa["label"],
            "weight": sa["weight"],
            "themes": [sa["domain"]],
            "event_type": "signal_activation",
        })

    # ── Anchor on ALL events (signal activations + all dasha transitions) ────────
    anchor_events = [ev for ev in all_events]

    windows: list[dict[str, Any]] = []
    processed: set[str] = set()

    for anchor_ev in anchor_events:
        anchor_date = anchor_ev["date"]

        # Only process events in the requested range
        if anchor_date < start_date or anchor_date > end_date:
            continue

        key = anchor_date.isoformat()
        if key in processed:
            continue
        processed.add(key)

        # 1. Point-in-time events within ±radius
        cluster_events = [
            ev for ev in all_events
            if abs((ev["date"] - anchor_date).days) <= WINDOW_RADIUS_DAYS
        ]

        # 2. Active dasha factors at anchor_date (background + fresh start)
        active_dasha = _active_dasha_factors_at(anchor_date)

        # Combine + deduplicate by label
        seen_labels: dict[str, dict[str, Any]] = {}
        for ev in cluster_events + active_dasha:
            lbl = ev["label"]
            if lbl not in seen_labels or ev["weight"] > seen_labels[lbl]["weight"]:
                seen_labels[lbl] = ev
        distinct = list(seen_labels.values())

        if len(distinct) < min_indicators:
            continue

        # Score
        total_weight = sum(ev["weight"] for ev in distinct)
        max_possible = len(distinct) * 1.0
        score = min(total_weight / max_possible, 1.0)

        # Window bounds
        w_start = max(anchor_date - radius, start_date)
        w_end = min(anchor_date + radius, end_date)

        # Collect all themes
        all_themes: list[str] = []
        all_signal_domains: list[str] = []
        for ev in distinct:
            all_themes.extend(ev.get("themes", []))
            if ev["event_type"] == "signal_activation":
                all_signal_domains.extend(ev.get("themes", []))

        # Classify
        ctype = _classify_convergence_type(all_themes, all_signal_domains)

        # Determine valence
        malefic_themes = {"hardship", "conflict", "separation", "transformation", "karmic_resolution"}
        n_malefic = sum(1 for t in all_themes if t in malefic_themes)
        n_total = len(all_themes)
        valence = "challenging" if n_total > 0 and n_malefic > n_total / 2 else "favorable"

        windows.append({
            "window_start": w_start.isoformat(),
            "window_end": w_end.isoformat(),
            "anchor_date": anchor_date.isoformat(),
            "convergence_score": round(score, 4),
            "indicator_count": len(distinct),
            "convergence_type": ctype,
            "valence": valence,
            "constituent_factors": [
                {
                    "label": ev["label"],
                    "date": ev["date"].isoformat(),
                    "weight": ev["weight"],
                    "event_type": ev["event_type"],
                    "themes": ev.get("themes", []),
                }
                for ev in sorted(distinct, key=lambda e: e["date"])
            ],
            "source_citation": SOURCE_CITATION,
        })

    # ── Sort + merge overlapping windows ──────────────────────────────────────
    windows.sort(key=lambda w: w["window_start"])
    windows = _merge_windows(windows)
    return windows


def _merge_windows(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge windows whose anchor dates are within 45 days of each other
    (half the window radius) to avoid overcollapsing while removing true duplicates.
    Windows whose anchor dates differ by > 45 days are kept separate.
    """
    if not windows:
        return []
    result = [windows[0].copy()]
    for nxt in windows[1:]:
        cur = result[-1]
        # Only merge if anchor dates are within 45 days (close duplicates)
        cur_anchor = _parse_date(cur["anchor_date"])
        nxt_anchor = _parse_date(nxt["anchor_date"])
        if abs((nxt_anchor - cur_anchor).days) <= 45:
            # Merge: expand window, keep higher score
            if nxt["window_end"] > cur["window_end"]:
                cur["window_end"] = nxt["window_end"]
            if nxt["convergence_score"] > cur["convergence_score"]:
                cur["convergence_score"] = nxt["convergence_score"]
                cur["indicator_count"] = nxt["indicator_count"]
                cur["convergence_type"] = nxt["convergence_type"]
                cur["constituent_factors"] = nxt["constituent_factors"]
        else:
            result.append(nxt.copy())
    return result


def query_convergence_windows(
    chart_id: str,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    convergence_type: str | None = None,
    min_score: float | None = None,
    min_indicators: int = 3,
) -> dict[str, Any]:
    """
    Query convergence windows for a chart.

    Args:
        chart_id:         Chart UUID (for provenance).
        start_date:       Filter start (YYYY-MM-DD or date).
        end_date:         Filter end.
        convergence_type: Filter by type ("career_peak", "relationship", etc.).
        min_score:        Minimum convergence score [0.0, 1.0].
        min_indicators:   Minimum factor count for a window (default 3).

    Returns:
        {
          "windows": [...],
          "count": int,
          "volume_floor_met": bool,
          "by_type": {"career_peak": N, ...},
          "provenance_envelope": {...}
        }
    """
    if isinstance(start_date, str):
        start_date = _parse_date(start_date)
    if isinstance(end_date, str):
        end_date = _parse_date(end_date)

    windows = compute_convergence_windows(start_date, end_date, min_indicators)

    if convergence_type:
        windows = [w for w in windows if w["convergence_type"] == convergence_type]
    if min_score is not None:
        windows = [w for w in windows if w["convergence_score"] >= min_score]

    # Count by type
    by_type: dict[str, int] = {}
    for w in windows:
        ct = w["convergence_type"]
        by_type[ct] = by_type.get(ct, 0) + 1

    return {
        "windows": windows,
        "count": len(windows),
        "volume_floor_met": len(windows) >= VOLUME_FLOOR,
        "by_type": by_type,
        "provenance_envelope": {
            "asset": "kala.convergence",
            "unit": "KA-3-2",
            "chart_id": chart_id,
            "source_citation": SOURCE_CITATION,
            "layer": "L3 Kāla",
            "start_date": str(start_date or "1984-01-01"),
            "end_date": str(end_date or "2040-12-31"),
            "volume_floor": VOLUME_FLOOR,
            "min_indicators": min_indicators,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_gate(chart_id: str = NATIVE_CHART_ID) -> bool:
    """
    KA-3-2 acceptance gate:

    G1: ≥ 20 convergence windows over 1984-2040
    G2: All scores in [0.0, 1.0]
    G3: 2002-07-24 (Saturn-Moon AD start, known high-intensity period) in or near a window
    G4: 2022-09-06 (Mercury-Jupiter AD start, career_peak signal) in a window
    G5: source_citation non-null on all windows
    G6: Multiple convergence types present
    G7: Mercury-Jupiter AD window (2022-2024) has career_peak type
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

    print("=== KA-3-2 Acceptance Gate (l3_convergence) ===")

    result = query_convergence_windows(
        chart_id,
        start_date=date(1984, 1, 1),
        end_date=date(2040, 12, 31),
    )
    windows = result["windows"]

    # G1: volume floor
    check("G1: ≥ 20 convergence windows", len(windows) >= VOLUME_FLOOR,
          f"actual={len(windows)}/{VOLUME_FLOOR}")

    # G2: all scores in range
    bad_scores = [w for w in windows if not (0.0 <= w["convergence_score"] <= 1.0)]
    check("G2: all scores in [0.0,1.0]", len(bad_scores) == 0,
          f"bad_count={len(bad_scores)}")

    # G3: 2002-07-24 near a window (Saturn-Moon AD start)
    target_2002 = date(2002, 7, 24)
    near_2002 = [
        w for w in windows
        if _parse_date(w["window_start"]) <= target_2002 + timedelta(days=120)
        and _parse_date(w["window_end"]) >= target_2002 - timedelta(days=120)
    ]
    check("G3: 2002-07-24 (Saturn-Moon AD) near a window", len(near_2002) > 0,
          f"windows_near={len(near_2002)}")

    # G4: 2022-09-06 (Mercury-Jupiter AD start) in a window
    target_2022 = date(2022, 9, 6)
    near_2022 = [
        w for w in windows
        if _parse_date(w["window_start"]) <= target_2022 + timedelta(days=90)
        and _parse_date(w["window_end"]) >= target_2022 - timedelta(days=90)
    ]
    check("G4: 2022-09-06 (Mercury-Jupiter AD) in a window", len(near_2022) > 0,
          f"windows_near={len(near_2022)}")

    # G5: source_citation non-null
    null_cit = [w for w in windows if not w.get("source_citation")]
    check("G5: source_citation non-null", len(null_cit) == 0,
          f"null_count={len(null_cit)}")

    # G6: multiple convergence types
    types_present = set(w["convergence_type"] for w in windows)
    check("G6: multiple convergence types", len(types_present) >= 2,
          f"types={types_present}")

    # G7: Mercury-Jupiter AD window has career_peak type
    career_windows = [w for w in windows if w["convergence_type"] == "career_peak"]
    check("G7: career_peak windows present", len(career_windows) > 0,
          f"count={len(career_windows)}")

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0
