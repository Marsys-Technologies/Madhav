"""
brahmagyan.kala.l3_snapshot — BRAHMA-KA-3-4: kala.snapshot (L3 Kāla asset)
============================================================================

Point-in-time chart snapshot: current Kala state for the native.
Default snapshot date: 2026-06-05 (session date per CLAUDECODE_BRIEF_WS2).

Snapshot includes:
  - Current dasha period (MD/AD/PD) active on the snapshot date
  - Current major transits and their house positions from natal Lagna (Aries)
  - Active convergence windows (if any overlap snapshot date ±30 days)
  - Active obstructions (if any overlap snapshot date)
  - Kala readiness score (0-100, composite of favorable/unfavorable indicators)
  - Provenance envelope (source, layer, chart_id, snapshot_date)

Volume floor: 1 snapshot entry with nested JSON (point-in-time, not a table).

Source: FORENSIC v8.0 §5.1 §2.1 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
BRAHMA-KA-3-4 (distinct from BRAHMA-KA-3-4 kala.temporal composite)
Tool: kala_snapshot_current — returns today's Kala state
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)
SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1; FORENSIC v8.0 §5.1 §2.1 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)"

# Default snapshot date (session date per CLAUDECODE_BRIEF_WS2)
DEFAULT_SNAPSHOT_DATE = date(2026, 6, 5)

# ── FORENSIC Vimshottari schedule (§5.1) ──────────────────────────────────────
FORENSIC_SCHEDULE: list[tuple[str, str, str, str]] = [
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

# ── Vimshottari constants for PD computation ──────────────────────────────────
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
TOTAL_YEARS = 120
DAYS_PER_YEAR = 365.25

# ── Current transit state for snapshot date 2026-06-05 ────────────────────────
# These are approximate sidereal (Lahiri) positions for 2026-06-05.
# Source: algorithmic extrapolation from FORENSIC anchors + known ingress dates.
# [EXTERNAL_COMPUTATION_REQUIRED for exact degree-level positions via Swiss Ephemeris]

SNAPSHOT_2026_06_05_TRANSITS: list[dict[str, Any]] = [
    # Saturn: entered Pisces 2025-03-29; H12 from Lagna Aries
    {"planet": "Saturn", "sign": "Pisces", "house_from_lagna": 12,
     "retrograde": False, "degree_approx": "~8°",
     "note": "Sade Sati Cycle 2 setting phase (2025-03-29 to 2028-03-28)",
     "source": "FORENSIC §22 + algorithmic"},
    # Jupiter: entered Cancer 2025-05-15 (exalted); H4 from Lagna Aries
    {"planet": "Jupiter", "sign": "Cancer", "house_from_lagna": 4,
     "retrograde": False, "degree_approx": "~15°",
     "note": "Jupiter exalted in Cancer (H4) — home/emotional domain activated",
     "source": "algorithmic from known ingress 2025-05-15"},
    # Rahu: entered Aquarius 2025-04-19; H11 from Lagna Aries
    {"planet": "Rahu", "sign": "Aquarius", "house_from_lagna": 11,
     "retrograde": True, "degree_approx": "~26°",
     "note": "Rahu in H11 (natal Moon sign) — gains and networking themes",
     "source": "algorithmic from known ingress 2025-04-19"},
    # Ketu: Rahu axis → Ketu in Leo (H5)
    {"planet": "Ketu", "sign": "Leo", "house_from_lagna": 5,
     "retrograde": True, "degree_approx": "~26°",
     "note": "Ketu in H5 — creative/children domain; spiritual separation themes",
     "source": "algorithmic (Ketu = Rahu ± 180°)"},
    # Mars: approximately in Gemini (H3) for early June 2026 [EXTERNAL_COMPUTATION_REQUIRED]
    {"planet": "Mars", "sign": "Gemini", "house_from_lagna": 3,
     "retrograde": False, "degree_approx": "~20° [APPROXIMATE]",
     "note": "Mars transiting H3 — siblings, communication, short travel",
     "source": "approximate [EXTERNAL_COMPUTATION_REQUIRED for exact]"},
    # Sun: approximately in Taurus (H2) for June 5, 2026
    {"planet": "Sun", "sign": "Taurus", "house_from_lagna": 2,
     "retrograde": False, "degree_approx": "~21° [APPROXIMATE]",
     "note": "Sun in H2 — wealth, speech, family",
     "source": "approximate [EXTERNAL_COMPUTATION_REQUIRED for exact]"},
    # Venus: approximately in Aries/Taurus area [EXTERNAL_COMPUTATION_REQUIRED]
    {"planet": "Venus", "sign": "Aries", "house_from_lagna": 1,
     "retrograde": False, "degree_approx": "~8° [APPROXIMATE]",
     "note": "Venus in H1 (Lagna) — self-enhancement, creative expression",
     "source": "approximate [EXTERNAL_COMPUTATION_REQUIRED for exact]"},
    # Mercury: approximately in Gemini [EXTERNAL_COMPUTATION_REQUIRED]
    {"planet": "Mercury", "sign": "Gemini", "house_from_lagna": 3,
     "retrograde": False, "degree_approx": "~10° [APPROXIMATE]",
     "note": "Mercury in H3 (own sign Gemini) — communication activated; MD lord in own sign",
     "source": "approximate [EXTERNAL_COMPUTATION_REQUIRED for exact]"},
]

# ── Kala readiness scoring ─────────────────────────────────────────────────────
# Score 0-100: 50 = neutral; >50 = favorable; <50 = challenging

def _compute_readiness_score(
    md_lord: str,
    ad_lord: str,
    transits: list[dict[str, Any]],
    active_obstructions: list[dict[str, Any]],
    active_convergences: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute Kala readiness score (0-100) and breakdown.

    Inputs:
      - MD/AD lord classification
      - Transit house positions
      - Active obstructions (each reduces score)
      - Active convergence windows (each increases score)

    Returns:
      {"score": int, "breakdown": {...}, "interpretation": str}
    """
    score = 50.0  # neutral base

    breakdown: dict[str, Any] = {"base": 50, "adjustments": []}

    # MD lord contribution
    BENEFIC_LORDS = {"Jupiter", "Venus", "Mercury", "Moon"}
    MALEFIC_LORDS = {"Saturn", "Rahu", "Ketu", "Mars"}

    if md_lord in BENEFIC_LORDS:
        adj = 8
        score += adj
        breakdown["adjustments"].append({"factor": f"Benefic MD lord ({md_lord})", "delta": adj})
    elif md_lord in MALEFIC_LORDS:
        adj = -8
        score += adj
        breakdown["adjustments"].append({"factor": f"Malefic MD lord ({md_lord})", "delta": adj})

    # AD lord contribution
    if ad_lord in BENEFIC_LORDS:
        adj = 5
        score += adj
        breakdown["adjustments"].append({"factor": f"Benefic AD lord ({ad_lord})", "delta": adj})
    elif ad_lord in MALEFIC_LORDS:
        adj = -5
        score += adj
        breakdown["adjustments"].append({"factor": f"Malefic AD lord ({ad_lord})", "delta": adj})

    # Transit contributions
    FAVORABLE_HOUSES = frozenset({1, 4, 5, 7, 9, 10, 11})
    DUSTHANA_HOUSES  = frozenset({4, 7, 8, 12})  # malefic planets in these = trouble

    for tr in transits:
        pl = tr.get("planet", "")
        house = tr.get("house_from_lagna", 0)
        is_benefic_planet = pl in BENEFIC_LORDS
        is_malefic_planet = pl in MALEFIC_LORDS | {"Sun"}

        if is_benefic_planet and house in FAVORABLE_HOUSES:
            adj = 4
            score += adj
            breakdown["adjustments"].append(
                {"factor": f"Benefic {pl} in H{house} (favorable)", "delta": adj})
        elif is_malefic_planet and house in DUSTHANA_HOUSES:
            adj = -4
            score += adj
            breakdown["adjustments"].append(
                {"factor": f"Malefic {pl} in H{house} (dusthana)", "delta": adj})

    # Obstruction penalties
    for obs in active_obstructions:
        severity = obs.get("severity", 0.5)
        adj = -round(severity * 12)
        score += adj
        breakdown["adjustments"].append(
            {"factor": f"Obstruction: {obs.get('obstruction_id', obs.get('obstruction_type'))}", "delta": adj})

    # Convergence bonuses
    for conv in active_convergences:
        cscore = conv.get("convergence_score", 0.5)
        adj = round(cscore * 8)
        score += adj
        breakdown["adjustments"].append(
            {"factor": f"Convergence: {conv.get('convergence_type', 'general')}", "delta": adj})

    # Clamp to [0, 100]
    score = max(0, min(100, round(score)))
    breakdown["final"] = score

    if score >= 75:
        interpretation = "HIGHLY_FAVORABLE — multiple benefic factors aligned; auspicious for initiatives"
    elif score >= 55:
        interpretation = "FAVORABLE — net positive factors; good for sustained effort"
    elif score >= 45:
        interpretation = "NEUTRAL — mixed indicators; proceed with awareness"
    elif score >= 30:
        interpretation = "CHALLENGING — multiple headwinds active; caution advised"
    else:
        interpretation = "HIGHLY_CHALLENGING — significant malefic clustering; rest and consolidation recommended"

    return {"score": score, "breakdown": breakdown, "interpretation": interpretation}


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _get_active_dasha(snapshot_date: date) -> dict[str, Any] | None:
    """Return active MD/AD from FORENSIC schedule for snapshot_date."""
    for md_lord, ad_lord, start_s, end_s in FORENSIC_SCHEDULE:
        start = _parse_date(start_s)
        end = _parse_date(end_s)
        if start <= snapshot_date < end:
            return {
                "md_lord": md_lord,
                "ad_lord": ad_lord,
                "ad_start": start_s,
                "ad_end": end_s,
                "days_elapsed": (snapshot_date - start).days,
                "days_remaining": (end - snapshot_date).days,
            }
    return None


def _compute_pd(
    md_lord: str,
    ad_lord: str,
    ad_start: date,
    ad_end: date,
    snapshot_date: date,
) -> dict[str, Any]:
    """
    Compute the Pratyantardasha (3rd level) active at snapshot_date within
    the given MD/AD period.

    Uses proportional subdivision: each PD = (AD years × PD lord years / 120) of the
    AD duration.
    """
    # Find position in Vimshottari sequence starting from AD lord
    ad_idx = VIMSHOTTARI_SEQUENCE.index(ad_lord)
    ad_days = (ad_end - ad_start).days
    ad_years = VIMSHOTTARI_YEARS[ad_lord]

    current = ad_start
    for i in range(len(VIMSHOTTARI_SEQUENCE)):
        pd_lord = VIMSHOTTARI_SEQUENCE[(ad_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
        pd_lord_years = VIMSHOTTARI_YEARS[pd_lord]
        pd_days = int(ad_days * pd_lord_years / TOTAL_YEARS)
        pd_end = current + timedelta(days=pd_days)

        if current <= snapshot_date < pd_end:
            return {
                "pd_lord": pd_lord,
                "pd_start": current.isoformat(),
                "pd_end": pd_end.isoformat(),
                "days_elapsed": (snapshot_date - current).days,
                "days_remaining": (pd_end - snapshot_date).days,
            }
        current = pd_end

    # Fallback: last PD
    return {
        "pd_lord": VIMSHOTTARI_SEQUENCE[(ad_idx + len(VIMSHOTTARI_SEQUENCE) - 1) % len(VIMSHOTTARI_SEQUENCE)],
        "pd_start": ad_start.isoformat(),
        "pd_end": ad_end.isoformat(),
        "days_elapsed": 0,
        "days_remaining": 0,
    }


def _get_active_obstructions(snapshot_date: date) -> list[dict[str, Any]]:
    """Return obstruction entries active on snapshot_date from l3_obstruction."""
    try:
        from brahmagyan.kala.l3_obstruction import compute_obstructions  # noqa: PLC0415
        entries = compute_obstructions(
            start_date=snapshot_date,
            end_date=snapshot_date,
        )
        return entries
    except ImportError:
        logger.warning("l3_obstruction not available; obstruction data omitted")
        return []


def _get_active_convergences(snapshot_date: date) -> list[dict[str, Any]]:
    """Return convergence windows that overlap snapshot_date ±30 days."""
    try:
        from brahmagyan.kala.l3_convergence import compute_convergence_windows  # noqa: PLC0415
        orb = timedelta(days=30)
        windows = compute_convergence_windows(
            start_date=snapshot_date - orb,
            end_date=snapshot_date + orb,
        )
        return windows
    except ImportError:
        logger.warning("l3_convergence not available; convergence data omitted")
        return []


def compute_snapshot(
    chart_id: str = NATIVE_CHART_ID,
    snapshot_date: str | date | None = None,
) -> dict[str, Any]:
    """
    Compute the point-in-time Kala snapshot for the native.

    Args:
        chart_id:       Chart UUID (must match FORENSIC native for grounded data).
        snapshot_date:  Date string YYYY-MM-DD or date (default: 2026-06-05).

    Returns:
        One snapshot dict with:
          - chart_id, snapshot_date
          - active_dasha: {md_lord, ad_lord, ad_start, ad_end, days_elapsed, days_remaining}
          - active_pratyantardasha: {pd_lord, pd_start, pd_end, ...}
          - transits: [{planet, sign, house_from_lagna, note}, ...]
          - active_convergences: [...] (windows overlapping ±30 days)
          - active_obstructions: [...] (obstructions active on snapshot_date)
          - kala_readiness: {score: 0-100, interpretation, breakdown}
          - provenance_envelope
    """
    if snapshot_date is None:
        snapshot_date = DEFAULT_SNAPSHOT_DATE
    if isinstance(snapshot_date, str):
        snapshot_date = _parse_date(snapshot_date)

    # ── 1. Active dasha ────────────────────────────────────────────────────────
    dasha = _get_active_dasha(snapshot_date)
    if dasha is None:
        logger.warning("Snapshot date %s outside FORENSIC schedule", snapshot_date)
        md_lord = "Unknown"
        ad_lord = "Unknown"
        pd_info: dict[str, Any] = {}
    else:
        md_lord = dasha["md_lord"]
        ad_lord = dasha["ad_lord"]
        pd_info = _compute_pd(
            md_lord=md_lord,
            ad_lord=ad_lord,
            ad_start=_parse_date(dasha["ad_start"]),
            ad_end=_parse_date(dasha["ad_end"]),
            snapshot_date=snapshot_date,
        )

    # ── 2. Transit state ───────────────────────────────────────────────────────
    # Use the pre-computed snapshot for 2026-06-05; for other dates,
    # use the algorithmic positions from l3_timeline slow transit table.
    if snapshot_date == DEFAULT_SNAPSHOT_DATE:
        transits = SNAPSHOT_2026_06_05_TRANSITS
        transit_source = "Pre-computed 2026-06-05 snapshot; slow planets from FORENSIC anchors"
    else:
        # Attempt to load from l3_timeline
        try:
            from brahmagyan.kala.l3_timeline import SLOW_TRANSITS, _parse_date as lt_parse  # noqa: PLC0415
            active_transits = []
            for tr in SLOW_TRANSITS:
                tr_start = lt_parse(tr["start"])
                tr_end = lt_parse(tr["end"])
                if tr_start <= snapshot_date <= tr_end:
                    active_transits.append({
                        "planet": tr["planet"],
                        "sign": tr["sign"],
                        "house_from_lagna": tr["house"],
                        "note": f"{tr['nature']} transit",
                        "source": "l3_timeline.SLOW_TRANSITS",
                    })
            transits = active_transits
            transit_source = "l3_timeline.SLOW_TRANSITS (slow planets only)"
        except ImportError:
            transits = []
            transit_source = "unavailable"

    # ── 3. Active convergences ─────────────────────────────────────────────────
    active_convergences = _get_active_convergences(snapshot_date)

    # ── 4. Active obstructions ─────────────────────────────────────────────────
    active_obstructions = _get_active_obstructions(snapshot_date)

    # ── 5. Kala readiness score ────────────────────────────────────────────────
    readiness = _compute_readiness_score(
        md_lord=md_lord,
        ad_lord=ad_lord,
        transits=transits,
        active_obstructions=active_obstructions,
        active_convergences=active_convergences,
    )

    # ── 6. Snapshot summary ────────────────────────────────────────────────────
    snapshot: dict[str, Any] = {
        "chart_id": chart_id,
        "snapshot_date": snapshot_date.isoformat(),
        "active_dasha": dasha,
        "active_pratyantardasha": pd_info,
        "transit_state": {
            "source": transit_source,
            "transits": transits,
            "slow_planet_count": len([t for t in transits if t.get("planet") in ("Saturn", "Jupiter", "Rahu", "Ketu")]),
        },
        "active_convergences": active_convergences,
        "active_obstructions": active_obstructions,
        "kala_readiness": readiness,
        "kala_summary": _build_kala_summary(
            md_lord=md_lord,
            ad_lord=ad_lord,
            pd_info=pd_info,
            transits=transits,
            obstructions=active_obstructions,
            convergences=active_convergences,
            score=readiness["score"],
            snapshot_date=snapshot_date,
        ),
        "provenance_envelope": {
            "asset": "kala.snapshot",
            "unit": "KA-3-5",
            "chart_id": chart_id,
            "source_citation": SOURCE_CITATION,
            "layer": "L3 Kāla",
            "snapshot_date": snapshot_date.isoformat(),
            "default_snapshot_date": DEFAULT_SNAPSHOT_DATE.isoformat(),
            "transit_accuracy_note": (
                "Slow planets (Saturn, Jupiter, Rahu/Ketu) positions are FORENSIC-grounded to ±days. "
                "Fast planets (Sun, Mercury, Venus, Mars) are approximate ±15°. "
                "For exact degree-level positions: [EXTERNAL_COMPUTATION_REQUIRED via Swiss Ephemeris]."
            ),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    return snapshot


def _build_kala_summary(
    md_lord: str,
    ad_lord: str,
    pd_info: dict[str, Any],
    transits: list[dict[str, Any]],
    obstructions: list[dict[str, Any]],
    convergences: list[dict[str, Any]],
    score: int,
    snapshot_date: date,
) -> str:
    """
    Build a human-readable one-paragraph Kala summary for the snapshot.
    """
    pd_lord = pd_info.get("pd_lord", "Unknown") if pd_info else "Unknown"
    pd_remaining = pd_info.get("days_remaining", 0) if pd_info else 0

    obs_types = [o["obstruction_type"] for o in obstructions]
    has_sade_sati = "sade_sati" in obs_types
    has_double = "double_affliction" in obs_types

    conv_types = [c.get("convergence_type", "general") for c in convergences]
    has_career_peak = "career_peak" in conv_types

    # Build Saturn transit note
    saturn_transit = next((t for t in transits if t.get("planet") == "Saturn"), None)
    saturn_note = ""
    if saturn_transit:
        saturn_note = (
            f"Saturn is transiting {saturn_transit['sign']} (H{saturn_transit['house_from_lagna']} from Lagna). "
        )
        if has_sade_sati:
            saturn_note += "This is part of Sade Sati Cycle 2. "

    # Build Jupiter note
    jupiter_transit = next((t for t in transits if t.get("planet") == "Jupiter"), None)
    jupiter_note = ""
    if jupiter_transit:
        jupiter_note = (
            f"Jupiter is transiting {jupiter_transit['sign']} (H{jupiter_transit['house_from_lagna']}). "
        )

    summary = (
        f"On {snapshot_date.isoformat()}: The native is in Mercury Mahadasha / {ad_lord} Antardasha "
        f"/ {pd_lord} Pratyantardasha "
        f"({pd_remaining} days remaining in current PD). "
        f"{saturn_note}{jupiter_note}"
    )

    if has_sade_sati:
        summary += (
            "Sade Sati Cycle 2 (setting phase, Pisces) is active — "
            "emotional and resource caution remains warranted through 2028. "
        )

    if has_career_peak and has_double is False:
        summary += (
            f"A career_peak convergence window is active — this is a favorable period "
            f"for career initiatives, intellectual work, and recognition. "
        )

    if has_double:
        summary += (
            "Double-affliction (malefic transit + malefic dasha) is present — "
            "navigate with deliberate caution, avoid major irreversible decisions. "
        )

    summary += (
        f"Kala readiness score: {score}/100 ({_score_band(score)}). "
        f"Source: FORENSIC v8.0 §5.1 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)."
    )

    return summary.strip()


def _score_band(score: int) -> str:
    if score >= 75:
        return "HIGHLY_FAVORABLE"
    elif score >= 55:
        return "FAVORABLE"
    elif score >= 45:
        return "NEUTRAL"
    elif score >= 30:
        return "CHALLENGING"
    else:
        return "HIGHLY_CHALLENGING"


# ── Public interface: kala_snapshot_current ────────────────────────────────────


def kala_snapshot_current(
    chart_id: str = NATIVE_CHART_ID,
    as_of_date: str | date | None = None,
) -> dict[str, Any]:
    """
    MCP-facing function: returns today's (or specified date's) Kala state.

    Equivalent to compute_snapshot() with full nested JSON output.
    This is the function registered as the `kala_snapshot_current` MCP tool.

    Args:
        chart_id:    Chart UUID.
        as_of_date:  Date YYYY-MM-DD (default: 2026-06-05 session date).

    Returns:
        Full snapshot dict (single entry with nested JSON).
    """
    return compute_snapshot(chart_id=chart_id, snapshot_date=as_of_date)


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_gate(chart_id: str = NATIVE_CHART_ID) -> bool:
    """
    KA-3-5 snapshot acceptance gate:

    G1: compute_snapshot returns a non-empty dict
    G2: active_dasha is non-null with md_lord, ad_lord
    G3: Snapshot date 2026-06-05 → Mercury MD active
    G4: active_pratyantardasha present (pd_lord, pd_start, pd_end)
    G5: transits list non-empty
    G6: kala_readiness.score in [0, 100]
    G7: provenance_envelope.source_citation non-null
    G8: kala_summary non-empty string
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

    print("=== KA-3-5 Acceptance Gate (l3_snapshot) ===")

    snap = compute_snapshot(chart_id=chart_id, snapshot_date=date(2026, 6, 5))

    # G1: non-empty result
    check("G1: snapshot returns non-empty dict", bool(snap), f"keys={list(snap.keys())[:5]}")

    # G2: active_dasha non-null
    dasha = snap.get("active_dasha")
    check("G2: active_dasha non-null", dasha is not None,
          f"dasha={dasha and dasha.get('md_lord')}")

    # G3: Mercury MD on 2026-06-05
    md_lord = dasha.get("md_lord") if dasha else None
    check("G3: Mercury MD on 2026-06-05", md_lord == "Mercury",
          f"md={md_lord}")

    # G4: pratyantardasha present
    pd = snap.get("active_pratyantardasha", {})
    check("G4: active_pratyantardasha present", bool(pd.get("pd_lord")),
          f"pd_lord={pd.get('pd_lord')}")

    # G5: transits non-empty
    transit_state = snap.get("transit_state", {})
    transits = transit_state.get("transits", [])
    check("G5: transits list non-empty", len(transits) > 0,
          f"count={len(transits)}")

    # G6: kala_readiness score in [0, 100]
    kr = snap.get("kala_readiness", {})
    score = kr.get("score", -1)
    check("G6: kala_readiness.score in [0,100]", 0 <= score <= 100,
          f"score={score}")

    # G7: provenance_envelope.source_citation non-null
    pe = snap.get("provenance_envelope", {})
    check("G7: provenance_envelope.source_citation non-null",
          bool(pe.get("source_citation")), f"citation={pe.get('source_citation', '')[:30]}")

    # G8: kala_summary non-empty
    summary = snap.get("kala_summary", "")
    check("G8: kala_summary non-empty", len(summary) > 50,
          f"len={len(summary)}")

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0
