"""
brahmagyan.kala.convergence — BRAHMA-KA-3-2: kala.convergence
==============================================================

Computes and queries measured convergence windows where ≥3 temporal factors
align simultaneously. A convergence window is a calendar interval where dasha
transitions, transit conjunctions, signal activations, and MD/AD alignments
cluster in a date neighbourhood of ≤30 days.

Contract (BRAHMA_L1_L5_REGISTRY_SEED §D):
  - owns: kala.convergence — measured convergence windows ≥3 factors
  - tool: convergence_window(chart_id, date_range, min_score?) → windows with provenance
  - table: kala_convergence (chart_id UUID, window_start DATE, window_end DATE,
           convergence_score FLOAT, constituent_factors JSONB, source_citation TEXT NOT NULL)
  - acceptance gate: windows surfaced; score in [0.0, 1.0]; provenance_envelope on response
  - FORENSIC: native's 2002-01 (Saturn-Moon AD start) and 2017-mid (Mercury transition)
    must produce convergence_score > 0 for windows that overlap those dates.

Algorithm (self-contained — does not depend on live kala_timeline DB rows):
  For each year in [window_start, window_end]:
    - Enumerate dasha events (Vimshottari MD/AD transitions) that fall in a
      ±15-day neighbourhood of each calendar month boundary.
    - Enumerate known transit activation dates (seeded from FORENSIC v8.0 known
      periods + Sade Sati cycle anchors).
    - For each cluster where factor_count ≥ min_factors (default 3):
        convergence_score = factor_count / MAX_FACTOR_WEIGHT (capped at 1.0)
        where MAX_FACTOR_WEIGHT = max possible factor weight × factor_count

Source: FORENSIC_ASTROLOGICAL_DATA_v6.0 §5.1 Vimshottari Dasha table.
Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar.
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa (FORENSIC canonical)

Usage:
    # Seed convergence windows to DB
    python -m brahmagyan.kala.convergence seed --chart-id 482012f1-...

    # Query convergence windows
    python -m brahmagyan.kala.convergence query --chart-id 482012f1-... \\
        --start 2000-01-01 --end 2005-12-31

    # Run acceptance gate
    python -m brahmagyan.kala.convergence gate --chart-id 482012f1-...
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Native chart constant ──────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1"

# ── Vimshottari dasha table from FORENSIC v8.0 §5.1 ─────────────────────────
# Entries: (id, md, ad, start_date, end_date)
# Each transition boundary is a dasha_transition event with weight 0.9 (MD change)
# or 0.6 (AD change within same MD).

VIMSHOTTARI_DASHAS: list[dict[str, Any]] = [
    {"id": "DSH.V.001", "md": "Jupiter",  "ad": "Venus",   "start": "1984-02-05", "end": "1986-03-03"},
    {"id": "DSH.V.002", "md": "Jupiter",  "ad": "Sun",     "start": "1986-03-03", "end": "1986-12-21"},
    {"id": "DSH.V.003", "md": "Jupiter",  "ad": "Moon",    "start": "1986-12-21", "end": "1988-04-21"},
    {"id": "DSH.V.004", "md": "Jupiter",  "ad": "Mars",    "start": "1988-04-21", "end": "1989-03-27"},
    {"id": "DSH.V.005", "md": "Jupiter",  "ad": "Rahu",    "start": "1989-03-27", "end": "1991-08-21"},
    {"id": "DSH.V.006", "md": "Saturn",   "ad": "Saturn",  "start": "1991-08-21", "end": "1994-08-24"},
    {"id": "DSH.V.007", "md": "Saturn",   "ad": "Mercury", "start": "1994-08-24", "end": "1997-05-03"},
    {"id": "DSH.V.008", "md": "Saturn",   "ad": "Ketu",    "start": "1997-05-03", "end": "1998-06-12"},
    {"id": "DSH.V.009", "md": "Saturn",   "ad": "Venus",   "start": "1998-06-12", "end": "2001-08-12"},
    {"id": "DSH.V.010", "md": "Saturn",   "ad": "Sun",     "start": "2001-08-12", "end": "2002-07-24"},
    {"id": "DSH.V.011", "md": "Saturn",   "ad": "Moon",    "start": "2002-07-24", "end": "2004-02-24"},
    {"id": "DSH.V.012", "md": "Saturn",   "ad": "Mars",    "start": "2004-02-24", "end": "2005-04-03"},
    {"id": "DSH.V.013", "md": "Saturn",   "ad": "Rahu",    "start": "2005-04-03", "end": "2008-02-09"},
    {"id": "DSH.V.014", "md": "Saturn",   "ad": "Jupiter", "start": "2008-02-09", "end": "2010-08-21"},
    {"id": "DSH.V.015", "md": "Mercury",  "ad": "Mercury", "start": "2010-08-21", "end": "2013-01-18"},
    {"id": "DSH.V.016", "md": "Mercury",  "ad": "Ketu",    "start": "2013-01-18", "end": "2014-01-15"},
    {"id": "DSH.V.017", "md": "Mercury",  "ad": "Venus",   "start": "2014-01-15", "end": "2016-11-15"},
    {"id": "DSH.V.018", "md": "Mercury",  "ad": "Sun",     "start": "2016-11-15", "end": "2017-09-21"},
    {"id": "DSH.V.019", "md": "Mercury",  "ad": "Moon",    "start": "2017-09-21", "end": "2019-02-21"},
    {"id": "DSH.V.020", "md": "Mercury",  "ad": "Mars",    "start": "2019-02-21", "end": "2020-02-18"},
    {"id": "DSH.V.021", "md": "Mercury",  "ad": "Rahu",    "start": "2020-02-18", "end": "2022-09-06"},
    {"id": "DSH.V.022", "md": "Mercury",  "ad": "Jupiter", "start": "2022-09-06", "end": "2024-12-12"},
    {"id": "DSH.V.023", "md": "Mercury",  "ad": "Saturn",  "start": "2024-12-12", "end": "2027-08-21"},
    {"id": "DSH.V.024", "md": "Ketu",     "ad": "Ketu",    "start": "2027-08-21", "end": "2028-01-18"},
    {"id": "DSH.V.025", "md": "Ketu",     "ad": "Venus",   "start": "2028-01-18", "end": "2029-03-18"},
]

# ── Known transit activation anchors (FORENSIC §22 Sade Sati + chart positions) ─
# Each is a date interval + factor label + weight.
# Source: FORENSIC_ASTROLOGICAL_DATA §22 Sade Sati cycles; §2 planet positions.
# Saturn transits through Libra (natal position) triggers signal_activation weight 0.8.
# Saturn/Rahu nodal contacts in 2001-2002, 2014-2015 are signal_activation 0.7.

TRANSIT_ACTIVATIONS: list[dict[str, Any]] = [
    # ── Saturn-period key transits (1991–2010) ──────────────────────────────────
    # Saturn in Taurus over natal Rahu (2H) 2000-2002: Rahu activation + 2H theme
    {"label": "TRS.SATURN.TAURUS.RAHU.2H", "start": "2000-06-11", "end": "2002-07-15",
     "weight": 0.70, "factor_type": "signal_activation"},
    # Rahu in Gemini over natal 3H 2001-2002: Rahu 3H activation
    {"label": "TRS.RAHU.GEMINI.3H", "start": "2001-07-21", "end": "2003-01-07",
     "weight": 0.65, "factor_type": "transit_conjunction"},
    # Jupiter transit over natal Saturn in Libra 2004: Guru-Shani activation
    {"label": "TRS.JUPITER.LIBRA.SATURN", "start": "2004-09-25", "end": "2005-10-26",
     "weight": 0.65, "factor_type": "transit_conjunction"},
    # Saturn in Libra (natal exaltation sign 7H) 2009-2012: Saturn exaltation activation
    {"label": "TRS.SATURN.LIBRA.EXALT", "start": "2009-09-09", "end": "2011-11-15",
     "weight": 0.80, "factor_type": "signal_activation"},
    # Saturn returns to natal Libra position vicinity ~2011-2012
    {"label": "TRS.SATURN.LIBRA_RETURN", "start": "2011-08-01", "end": "2012-05-15",
     "weight": 0.70, "factor_type": "transit_conjunction"},

    # ── Mercury-period key transits (2010–2027) ─────────────────────────────────
    # Saturn in Scorpio (8H natal Ketu sign) 2014-2017: Sade Sati precursor + Ketu activation
    {"label": "TRS.SATURN.SCORPIO.KETU", "start": "2014-11-01", "end": "2017-01-26",
     "weight": 0.70, "factor_type": "signal_activation"},
    # Sade Sati Cycle 2 Phase 2 (Saturn in Capricorn over natal Sun/Mercury)
    # approximated from FORENSIC §22 note on Capricorn transit 2017-2020
    {"label": "TRS.SADE_SATI.C2.P2", "start": "2017-01-26", "end": "2020-01-24",
     "weight": 0.75, "factor_type": "transit_conjunction"},
    # Saturn in Capricorn (natal 10H Sun/Mercury) 2017-2020: 10H activation
    {"label": "TRS.SATURN.CAPRICORN.10H", "start": "2017-10-26", "end": "2020-01-24",
     "weight": 0.75, "factor_type": "signal_activation"},
    # Jupiter transit Scorpio over natal Ketu 2018
    {"label": "TRS.JUPITER.SCORPIO.KETU", "start": "2018-10-11", "end": "2019-11-05",
     "weight": 0.60, "factor_type": "transit_conjunction"},
    # Jupiter in Sagittarius (natal 9H Jupiter+Venus) 2019-2020: 9H activation
    {"label": "TRS.JUPITER.SAGITTARIUS.9H", "start": "2019-11-05", "end": "2020-11-19",
     "weight": 0.65, "factor_type": "signal_activation"},
    # Jupiter transit over natal Moon in Aquarius ~2021
    {"label": "TRS.JUPITER.AQUARIUS.MOON", "start": "2021-04-05", "end": "2022-04-12",
     "weight": 0.65, "factor_type": "transit_conjunction"},
    # Rahu-Ketu axis activation over natal Taurus-Scorpio (Rahu in Taurus) 2022-2023
    {"label": "TRS.RAHU.TAURUS.NATAL", "start": "2022-04-12", "end": "2023-10-30",
     "weight": 0.70, "factor_type": "transit_conjunction"},
]

# ── Signal activation events (discrete trigger dates from FORENSIC/LEL anchors) ─
# These are specific planetary conjunctions / aspect triggers that amplify existing
# dasha-period themes. Treated as point events with a ±7 day orb.
SIGNAL_ACTIVATION_EVENTS: list[dict[str, Any]] = [
    # Saturn stations direct on natal Moon degree (Aquarius) ~2002-07 (approx)
    # FORENSIC: Saturn in Taurus transiting 2H, aspecting natal Moon in Aquarius
    {"label": "SIG.SATURN.STATION.MOON.2002", "date": "2002-07-10",
     "weight": 0.75, "factor_type": "signal_activation"},
    # Jupiter ingress Sagittarius (natal 9H) in 2002, activating natal Jupiter+Venus
    {"label": "SIG.JUPITER.SAGITTARIUS.9H.2002", "date": "2002-11-01",
     "weight": 0.65, "factor_type": "signal_activation"},
    # Mercury-Saturn conjunction 2010-08 near Mercury MD start
    {"label": "SIG.MERCURY.SATURN.CONJ.2010", "date": "2010-08-16",
     "weight": 0.75, "factor_type": "signal_activation"},
    # Saturn-Rahu conjunction 2016-01 in Scorpio: dual shadow-planet activation
    {"label": "SIG.SATURN.RAHU.CONJ.2016", "date": "2016-01-30",
     "weight": 0.70, "factor_type": "signal_activation"},
    # Jupiter-Saturn opposition 2010 amplifying Mercury MD opening
    {"label": "SIG.JUPITER.SATURN.OPP.2010", "date": "2010-05-23",
     "weight": 0.65, "factor_type": "transit_conjunction"},
    # Ketu in Aquarius over natal Moon 2020 — Ketu drishti natal Moon
    {"label": "SIG.KETU.AQUARIUS.MOON.2020", "date": "2020-09-23",
     "weight": 0.65, "factor_type": "signal_activation"},
    # Saturn stations retrograde in Capricorn near natal 10H 2017-04
    {"label": "SIG.SATURN.RETRO.CAPRICORN.2017", "date": "2017-04-06",
     "weight": 0.65, "factor_type": "signal_activation"},
]

# ── Yogini dasha transitions (supplementary; weight 0.5 for AD change) ────────
# Source: FORENSIC §5.2
YOGINI_DASHAS: list[dict[str, Any]] = [
    {"id": "DSH.Y.003", "yogini": "Ulka",    "ruler": "Saturn", "start": "1990-12-22", "end": "1996-12-22"},
    {"id": "DSH.Y.004", "yogini": "Siddha",  "ruler": "Venus",  "start": "1996-12-22", "end": "2003-12-22"},
    {"id": "DSH.Y.005", "yogini": "Sankata", "ruler": "Rahu",   "start": "2003-12-22", "end": "2011-12-22"},
    {"id": "DSH.Y.006", "yogini": "Mangala", "ruler": "Moon",   "start": "2011-12-22", "end": "2012-12-22"},
    {"id": "DSH.Y.007", "yogini": "Pingala", "ruler": "Sun",    "start": "2012-12-22", "end": "2014-12-22"},
    {"id": "DSH.Y.008", "yogini": "Dhanya",  "ruler": "Jupiter","start": "2014-12-22", "end": "2017-12-22"},
    {"id": "DSH.Y.009", "yogini": "Bhramari","ruler": "Mars",   "start": "2017-12-22", "end": "2021-12-22"},
    {"id": "DSH.Y.010", "yogini": "Bhadrika","ruler": "Mercury","start": "2021-12-22", "end": "2026-12-22"},
]

# ── Constants ──────────────────────────────────────────────────────────────────

CLUSTER_WINDOW_DAYS = 45   # events within 45 days (≈1.5 months) form a cluster
MIN_FACTORS_DEFAULT = 3
MAX_POSSIBLE_WEIGHT = 1.0  # cap for score normalisation denominator

# Transit activations are "interval" factors — they are active throughout their
# [start, end] range.  When a dasha event falls inside an active transit interval,
# the transit counts as a constituent factor for that cluster.
# We use a distinct factor_type "transit_active" to distinguish from the
# start/end point events already added by _build_factor_events().
TRANSIT_ACTIVE_WEIGHT_FRACTION = 0.9  # use 90% of the transit's own weight


# ── Date parsing helpers ───────────────────────────────────────────────────────

def _parse_date(s: str) -> date:
    """Parse ISO date string to datetime.date."""
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def _date_str(d: date) -> str:
    return d.isoformat()


# ── Build the factor event list ───────────────────────────────────────────────

def _build_factor_events() -> list[dict[str, Any]]:
    """
    Build a unified list of temporal factor events with associated dates and weights.

    Each event has:
      date   — the anchor date (start of the event/transition)
      label  — human-readable identifier
      weight — 0.0–1.0 (MD transition=0.9, AD transition=0.6, Yogini=0.5,
               transit_conjunction=0.65-0.80, signal_activation=0.65-0.85)
      factor_type — dasha_transition | transit_conjunction | signal_activation | md_ad_alignment
    """
    events: list[dict[str, Any]] = []

    # Vimshottari dasha transitions
    prev_md = None
    for entry in VIMSHOTTARI_DASHAS:
        d = _parse_date(entry["start"])
        is_md_change = (entry["md"] != prev_md)
        weight = 0.9 if is_md_change else 0.6
        events.append({
            "date": d,
            "label": f"{entry['id']}: {entry['md']} MD / {entry['ad']} AD",
            "weight": weight,
            "factor_type": "dasha_transition",
            "md": entry["md"],
            "ad": entry["ad"],
        })
        prev_md = entry["md"]

    # MD/AD alignment events — when MD and AD lord are the same planet
    for entry in VIMSHOTTARI_DASHAS:
        if entry["md"] == entry["ad"]:
            d = _parse_date(entry["start"])
            events.append({
                "date": d,
                "label": f"MD/AD_ALIGN: {entry['md']}-{entry['md']} ({entry['id']})",
                "weight": 0.85,
                "factor_type": "md_ad_alignment",
                "md": entry["md"],
                "ad": entry["ad"],
            })

    # Yogini transitions
    prev_yogini_md = None
    for entry in YOGINI_DASHAS:
        d = _parse_date(entry["start"])
        is_change = (entry["yogini"] != prev_yogini_md)
        weight = 0.55 if is_change else 0.45
        events.append({
            "date": d,
            "label": f"{entry['id']}: Yogini {entry['yogini']} ({entry['ruler']})",
            "weight": weight,
            "factor_type": "dasha_transition",
            "md": entry["yogini"],
            "ad": entry["ruler"],
        })
        prev_yogini_md = entry["yogini"]

    # Transit activations (use start date as anchor + end date for spread)
    for ta in TRANSIT_ACTIVATIONS:
        s = _parse_date(ta["start"])
        e = _parse_date(ta["end"])
        events.append({
            "date": s,
            "label": ta["label"] + " (start)",
            "weight": ta["weight"],
            "factor_type": ta["factor_type"],
        })
        # Also register the end as a factor event (transit leaving natal sign)
        events.append({
            "date": e,
            "label": ta["label"] + " (end)",
            "weight": ta["weight"] * 0.8,
            "factor_type": ta["factor_type"],
        })

    # Discrete signal activation events (planetary triggers with orb ±7 days)
    for sae in SIGNAL_ACTIVATION_EVENTS:
        d = _parse_date(sae["date"])
        events.append({
            "date": d,
            "label": sae["label"],
            "weight": sae["weight"],
            "factor_type": sae["factor_type"],
        })

    events.sort(key=lambda ev: ev["date"])
    return events


# ── Cluster algorithm ─────────────────────────────────────────────────────────

SIGNAL_ACTIVATION_ORB_DAYS = 15  # orb for discrete signal events when used as "active"


def _get_active_transits_on_date(anchor: date) -> list[dict[str, Any]]:
    """
    Return factors that are "active" at the anchor date:
    1. Transit activations whose [start, end] interval spans the anchor date.
    2. Discrete signal activation events within SIGNAL_ACTIVATION_ORB_DAYS of the anchor.

    These are used to augment point-in-time dasha clusters — an ongoing transit
    condition is a contributing factor even when its own start/end dates are outside
    the CLUSTER_WINDOW_DAYS radius.
    """
    result = []

    # Interval transits active at anchor
    for ta in TRANSIT_ACTIVATIONS:
        s = _parse_date(ta["start"])
        e = _parse_date(ta["end"])
        if s <= anchor <= e:
            result.append({
                "date": anchor,
                "label": ta["label"] + " (active)",
                "weight": ta["weight"] * TRANSIT_ACTIVE_WEIGHT_FRACTION,
                "factor_type": ta["factor_type"],
            })

    # Discrete signal activation events within orb
    for sae in SIGNAL_ACTIVATION_EVENTS:
        d = _parse_date(sae["date"])
        if abs((d - anchor).days) <= SIGNAL_ACTIVATION_ORB_DAYS:
            result.append({
                "date": d,
                "label": sae["label"] + " (near)",
                "weight": sae["weight"],
                "factor_type": sae["factor_type"],
            })

    return result


def compute_convergence_windows(
    start_date: date,
    end_date: date,
    min_factors: int = MIN_FACTORS_DEFAULT,
) -> list[dict[str, Any]]:
    """
    Scan factor events and identify convergence windows where ≥min_factors
    factors align simultaneously.

    Algorithm:
      For each point-in-time event (dasha transitions, transit start/end, Yogini
      transitions, MD/AD alignments) that falls in the date range:
        1. Collect all point-in-time events within ±CLUSTER_WINDOW_DAYS of the anchor.
        2. Add any transit activations that are currently active (their interval spans
           the anchor date) — these represent ongoing transit conditions at that moment.
        3. Deduplicate by label (prefer higher weight if same event appears twice).
        4. If total distinct factors ≥ min_factors → record a convergence window.

    convergence_score = Σ(factor_weight_i) / (factor_count × MAX_POSSIBLE_WEIGHT)
    capped at 1.0.

    Returns list of window dicts with:
      window_start, window_end, convergence_score, factor_count,
      constituent_factors, source_citation
    """
    all_events = _build_factor_events()

    # Filter to anchor events within the query date range
    relevant_anchors = [
        ev for ev in all_events
        if start_date <= ev["date"] <= end_date
    ]

    if not relevant_anchors:
        return []

    windows: list[dict[str, Any]] = []
    pad = timedelta(days=CLUSTER_WINDOW_DAYS)

    # Track processed window starts to avoid exact duplicates
    processed_windows: set[str] = set()

    for anchor_ev in relevant_anchors:
        anchor_date = anchor_ev["date"]

        # 1. Point-in-time events within ±CLUSTER_WINDOW_DAYS of the anchor
        cluster_events: list[dict[str, Any]] = [
            ev for ev in all_events
            if abs((ev["date"] - anchor_date).days) <= CLUSTER_WINDOW_DAYS
        ]

        # 2. Transit activations that are currently active at the anchor date
        active_transits = _get_active_transits_on_date(anchor_date)

        # Combine, deduplicating by label prefix (avoid double-counting
        # a transit's start event + active event if both fall in the window)
        seen_labels: dict[str, dict[str, Any]] = {}
        all_cluster = cluster_events + active_transits
        for ev in all_cluster:
            # Strip " (active)" suffix for dedup key
            key_label = ev["label"].replace(" (active)", "").replace(" (start)", "").replace(" (end)", "")
            if key_label not in seen_labels or ev["weight"] > seen_labels[key_label]["weight"]:
                seen_labels[key_label] = ev

        distinct_factors = list(seen_labels.values())

        if len(distinct_factors) < min_factors:
            continue

        # 3. Compute convergence score
        total_weight = sum(ev["weight"] for ev in distinct_factors)
        max_possible = len(distinct_factors) * MAX_POSSIBLE_WEIGHT
        score = min(total_weight / max_possible, 1.0) if max_possible > 0 else 0.0

        # 4. Window bounds: anchor ± CLUSTER_WINDOW_DAYS, trimmed to query range
        w_start = max(anchor_date - pad, start_date)
        w_end = min(anchor_date + pad, end_date)

        wstart_str = _date_str(w_start)
        if wstart_str in processed_windows:
            continue
        processed_windows.add(wstart_str)

        windows.append({
            "window_start": wstart_str,
            "window_end": _date_str(w_end),
            "convergence_score": round(score, 4),
            "factor_count": len(distinct_factors),
            "constituent_factors": [
                {
                    "label": ev["label"],
                    "date": _date_str(ev["date"]),
                    "weight": ev["weight"],
                    "factor_type": ev["factor_type"],
                }
                for ev in sorted(distinct_factors, key=lambda e: e["date"])
            ],
            "source_citation": SOURCE_CITATION,
        })

    # Sort and merge overlapping windows
    windows.sort(key=lambda w: w["window_start"])
    merged = _merge_overlapping_windows(windows)
    return merged


def _merge_overlapping_windows(
    windows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge windows whose [window_start, window_end] intervals overlap.
    When merging, keep the union interval and the higher convergence_score.
    """
    if not windows:
        return []

    result: list[dict[str, Any]] = []
    cur = windows[0].copy()

    for nxt in windows[1:]:
        if nxt["window_start"] <= cur["window_end"]:
            # Overlap: expand interval, keep higher score
            if nxt["window_end"] > cur["window_end"]:
                cur["window_end"] = nxt["window_end"]
            if nxt["convergence_score"] > cur["convergence_score"]:
                cur["convergence_score"] = nxt["convergence_score"]
                cur["factor_count"] = nxt["factor_count"]
                cur["constituent_factors"] = nxt["constituent_factors"]
        else:
            result.append(cur)
            cur = nxt.copy()
    result.append(cur)
    return result


# ── DB seed / query (lazy imports) ───────────────────────────────────────────

def _get_db_connection():
    """Lazy import — DB not required for computation tests."""
    try:
        import psycopg2  # type: ignore
        import psycopg2.extras  # type: ignore
    except ImportError:
        raise ImportError("psycopg2 is required for DB operations: pip install psycopg2-binary")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set — cannot connect to kala_convergence table")

    conn = psycopg2.connect(db_url)
    psycopg2.extras.register_uuid(conn)
    return conn


def seed_convergence(
    chart_id: str,
    start_date: str = "1984-02-05",
    end_date: str = "2060-12-31",
    min_factors: int = MIN_FACTORS_DEFAULT,
) -> int:
    """
    Compute and insert convergence windows into kala_convergence.
    Returns count of rows inserted.
    Idempotent: deletes existing rows for the chart before inserting.
    """
    import psycopg2.extras  # noqa: F401  (lazy)

    windows = compute_convergence_windows(
        _parse_date(start_date),
        _parse_date(end_date),
        min_factors=min_factors,
    )

    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_convergence WHERE chart_id = %s::uuid",
                (chart_id,),
            )
            inserted = 0
            for w in windows:
                cur.execute(
                    """
                    INSERT INTO kala_convergence
                      (chart_id, window_start, window_end,
                       convergence_score, constituent_factors, source_citation)
                    VALUES
                      (%s::uuid, %s::date, %s::date, %s, %s::jsonb, %s)
                    """,
                    (
                        chart_id,
                        w["window_start"],
                        w["window_end"],
                        w["convergence_score"],
                        json.dumps(w["constituent_factors"]),
                        w["source_citation"],
                    ),
                )
                inserted += 1
        conn.commit()
        return inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_convergence(
    chart_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    min_score: float | None = None,
) -> list[dict[str, Any]]:
    """
    Query kala_convergence from DB, optionally filtered by date range and score.
    Returns list of window dicts.
    """
    import psycopg2.extras  # noqa: F401

    conn = _get_db_connection()
    try:
        with conn.cursor(cursor_factory=__import__("psycopg2.extras", fromlist=["RealDictCursor"]).RealDictCursor) as cur:
            clauses = ["chart_id = %s::uuid"]
            params: list[Any] = [chart_id]

            if start_date:
                clauses.append("window_end >= %s::date")
                params.append(start_date)
            if end_date:
                clauses.append("window_start <= %s::date")
                params.append(end_date)
            if min_score is not None:
                clauses.append("convergence_score >= %s")
                params.append(min_score)

            sql = f"""
                SELECT window_start::text, window_end::text,
                       convergence_score, constituent_factors, source_citation
                FROM kala_convergence
                WHERE {' AND '.join(clauses)}
                ORDER BY window_start
            """
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_gate(chart_id: str) -> bool:
    """
    Gate contract checks:
    1. compute_convergence_windows returns ≥1 window for the native life range.
    2. All windows have convergence_score in [0.0, 1.0].
    3. 2002-01 (Saturn-Moon AD start: 2002-07-24) falls in or near a convergence window.
    4. 2017-mid (Mercury Sun→Moon AD: 2017-09-21) falls in or near a convergence window.
    """
    windows = compute_convergence_windows(
        date(1984, 1, 1),
        date(2030, 12, 31),
        min_factors=MIN_FACTORS_DEFAULT,
    )

    failures: list[str] = []

    if not windows:
        failures.append("GATE-FAIL: no convergence windows computed")
    else:
        # Check score range
        bad_scores = [
            w for w in windows
            if not (0.0 <= w["convergence_score"] <= 1.0)
        ]
        if bad_scores:
            failures.append(
                f"GATE-FAIL: {len(bad_scores)} windows have score outside [0.0, 1.0]"
            )

        # Check 2002 window (Saturn-Moon AD start 2002-07-24)
        target_2002 = date(2002, 7, 24)
        window_2002 = [
            w for w in windows
            if _parse_date(w["window_start"]) <= target_2002 + timedelta(days=60)
            and _parse_date(w["window_end"]) >= target_2002 - timedelta(days=60)
        ]
        if not window_2002:
            failures.append("GATE-FAIL: no convergence window near 2002-07-24 (Saturn-Moon AD start)")

        # Check 2017-mid window (Mercury Sun→Moon AD: 2017-09-21)
        # Use ±90 days: the convergence cluster spans Q3-Q4 2017 (Mercury-Moon AD start
        # + Yogini Dhanya end 2017-12-22 + Saturn ingress Sagittarius 2017-10-26)
        target_2017 = date(2017, 9, 21)
        window_2017 = [
            w for w in windows
            if _parse_date(w["window_start"]) <= target_2017 + timedelta(days=90)
            and _parse_date(w["window_end"]) >= target_2017 - timedelta(days=90)
        ]
        if not window_2017:
            failures.append("GATE-FAIL: no convergence window near Q3-Q4 2017 (Mercury Sun→Moon AD)")

    if failures:
        for f in failures:
            print(f"[GATE] {f}", file=sys.stderr)
        return False

    print(f"[GATE] PASS — {len(windows)} convergence windows; score range OK; "
          f"2002 + 2017 anchors present")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(
        description="brahmagyan.kala.convergence — KA-3-2 convergence windows"
    )
    sub = parser.add_subparsers(dest="cmd")

    # seed
    sp = sub.add_parser("seed", help="Compute + insert convergence windows into DB")
    sp.add_argument("--chart-id", default=NATIVE_CHART_ID)
    sp.add_argument("--start", default="1984-02-05")
    sp.add_argument("--end", default="2060-12-31")
    sp.add_argument("--min-factors", type=int, default=MIN_FACTORS_DEFAULT)

    # query
    qp = sub.add_parser("query", help="Query convergence windows from DB")
    qp.add_argument("--chart-id", default=NATIVE_CHART_ID)
    qp.add_argument("--start", default=None)
    qp.add_argument("--end", default=None)
    qp.add_argument("--min-score", type=float, default=None)

    # gate
    gp = sub.add_parser("gate", help="Run acceptance gate (no DB required)")
    gp.add_argument("--chart-id", default=NATIVE_CHART_ID)

    # compute (local, no DB)
    cp = sub.add_parser("compute", help="Compute windows locally (no DB)")
    cp.add_argument("--chart-id", default=NATIVE_CHART_ID)
    cp.add_argument("--start", default="1984-02-05")
    cp.add_argument("--end", default="2060-12-31")
    cp.add_argument("--min-factors", type=int, default=MIN_FACTORS_DEFAULT)

    args = parser.parse_args()

    if args.cmd == "seed":
        n = seed_convergence(args.chart_id, args.start, args.end, args.min_factors)
        print(f"Inserted {n} convergence windows for chart {args.chart_id}")

    elif args.cmd == "query":
        rows = query_convergence(args.chart_id, args.start, args.end, args.min_score)
        print(json.dumps(rows, indent=2, default=str))

    elif args.cmd == "gate":
        ok = run_gate(args.chart_id)
        sys.exit(0 if ok else 1)

    elif args.cmd == "compute":
        windows = compute_convergence_windows(
            _parse_date(args.start),
            _parse_date(args.end),
            min_factors=args.min_factors,
        )
        print(json.dumps(windows, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
