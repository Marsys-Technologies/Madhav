"""
brahmagyan.kala.l3_obstruction — BRAHMA-KA-3-3: kala.obstruction (L3 Kāla asset)
==================================================================================

Obstruction periods: times when major malefic influences cluster (Saturn transit
+ arishta dasha + challenged L2 signals).

Obstruction types:
  sade_sati          — Saturn transit over natal Moon sign ±1
                       Native Moon = Aquarius → Sade Sati spans Capricorn/Aquarius/Pisces
  ashtama_shani      — Saturn in 8H from natal Moon (Scorpio/H8 from Aquarius → Leo is 7th
                       from Moon sign; 8th from Moon = Pisces-relative)
                       NOTE: 8H from NATAL MOON SIGN (Aquarius) = Virgo
  malefic_dasha      — Saturn, Rahu, or Ketu Mahadasha (or double-malefic MD+AD)
  combustion_period  — Major benefic planet combust (within 6° of Sun) during a
                       sensitive dasha period
  double_affliction  — Both malefic transit AND adverse dasha active simultaneously

Volume floor: ≥ 10 obstruction entries.
  The native has 2 Sade Sati cycles (1990-98, 2020-28), multiple malefic dashas
  (Saturn MD 1991-2010, Ketu MD 2027-2034), and several combustion periods.

Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §22 Sade Sati, §5.1 Vimshottari, §2.1
BRAHMA-KA-3-3 / kala.obstruction
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 10  # minimum obstruction entries
NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0"
)
SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1; FORENSIC_ASTROLOGICAL_DATA_v8_0 §5.1 §22"

# ── Native chart FORENSIC anchors ─────────────────────────────────────────────
# FORENSIC §2.1: Moon = Aquarius (H11 from Lagna=Aries)
# Sade Sati: Saturn in Capricorn (H10), Aquarius (H11), Pisces (H12) from Lagna
#            but classically from Moon sign: Capricorn(12th), Aquarius(1st), Pisces(2nd)
# Ashtama Shani (8H from Moon sign Aquarius) = Virgo
# FORENSIC §22 provides explicit Sade Sati cycle dates.

NATIVE_MOON_SIGN = "Aquarius"
NATIVE_LAGNA = "Aries"

# ── Sade Sati windows (FORENSIC §22, canonical) ────────────────────────────────
# Phase labels: rising (12th from Moon), peak (on Moon), setting (2nd from Moon)

SADE_SATI_WINDOWS: list[dict[str, Any]] = [
    # ── Cycle 1 (1990-1998) ──────────────────────────────────────────────────
    {
        "obstruction_id": "OBS.SS.C1.RISING",
        "obstruction_type": "sade_sati",
        "phase": "rising",
        "saturn_sign": "Capricorn",
        "start": "1990-01-26",
        "end": "1993-01-25",
        "severity": 0.65,
        "description": (
            "Sade Sati Cycle 1 — Rising phase: Saturn in Capricorn (12th from natal Moon Aquarius). "
            "Overlapping Saturn MD (1991-08-21) + Saturn-Saturn AD (1991-08-21 to 1994-08-24). "
            "Double-reinforcement: transit Saturn + Mahadasha Saturn. Intensified karmic pressure. "
            "Source: FORENSIC §22 Sade Sati Cycle 1."
        ),
        "concurrent_dashas": [{"md": "Jupiter/Saturn", "ad": "Rahu/Saturn", "note": "Saturn MD starts 1991-08-21 within this window"}],
    },
    {
        "obstruction_id": "OBS.SS.C1.PEAK",
        "obstruction_type": "sade_sati",
        "phase": "peak",
        "saturn_sign": "Aquarius",
        "start": "1993-01-26",
        "end": "1995-04-09",
        "severity": 0.80,
        "description": (
            "Sade Sati Cycle 1 — Peak phase: Saturn exactly over natal Moon (Aquarius). "
            "Saturn in natal Moon sign = maximum emotional, health, mental pressure. "
            "Concurrent: Saturn MD Saturn-Mercury AD (1994-08-24 → 1997-05-03 starts mid-window). "
            "Source: FORENSIC §22 Sade Sati Cycle 1."
        ),
        "concurrent_dashas": [{"md": "Saturn", "ad": "Saturn/Mercury", "note": "Peak of Saturn MD + Saturn transit exact"}],
    },
    {
        "obstruction_id": "OBS.SS.C1.SETTING",
        "obstruction_type": "sade_sati",
        "phase": "setting",
        "saturn_sign": "Pisces",
        "start": "1995-04-10",
        "end": "1998-04-14",
        "severity": 0.60,
        "description": (
            "Sade Sati Cycle 1 — Setting phase: Saturn in Pisces (2nd from natal Moon). "
            "Financial/resource pressure. Saturn MD continues (ends 2010-08-21). "
            "Source: FORENSIC §22 Sade Sati Cycle 1."
        ),
        "concurrent_dashas": [{"md": "Saturn", "ad": "Mercury/Ketu/Venus", "note": "Saturn MD setting Sade Sati"}],
    },
    # ── Cycle 2 (2020-2028) ──────────────────────────────────────────────────
    {
        "obstruction_id": "OBS.SS.C2.RISING",
        "obstruction_type": "sade_sati",
        "phase": "rising",
        "saturn_sign": "Capricorn",
        "start": "2020-01-24",
        "end": "2022-04-28",
        "severity": 0.70,
        "description": (
            "Sade Sati Cycle 2 — Rising phase: Saturn in Capricorn (12th from natal Moon). "
            "Concurrent Mercury MD / Rahu AD (2020-02-18 → 2022-09-06) — amplified by Mercury-Rahu. "
            "COVID-19 context (2020-2022). Rahu amplifies disruption. "
            "Source: FORENSIC §22 Sade Sati Cycle 2."
        ),
        "concurrent_dashas": [{"md": "Mercury", "ad": "Rahu", "note": "Mercury-Rahu AD during Capricorn Sade Sati"}],
    },
    {
        "obstruction_id": "OBS.SS.C2.PEAK",
        "obstruction_type": "sade_sati",
        "phase": "peak",
        "saturn_sign": "Aquarius",
        "start": "2022-04-29",
        "end": "2025-03-28",
        "severity": 0.85,
        "description": (
            "Sade Sati Cycle 2 — Peak phase: Saturn exactly over natal Moon (Aquarius). "
            "Concurrent Mercury-Jupiter AD (2022-09-06 → 2024-12-12) + Mercury-Saturn AD (2024-12-12 → 2027-08-21). "
            "Peak Sade Sati during a high-convergence career period — tension between opportunity and restriction. "
            "Source: FORENSIC §22 Sade Sati Cycle 2."
        ),
        "concurrent_dashas": [{"md": "Mercury", "ad": "Jupiter/Saturn", "note": "Mercury-Jupiter then Mercury-Saturn AD during peak Sade Sati"}],
    },
    {
        "obstruction_id": "OBS.SS.C2.SETTING",
        "obstruction_type": "sade_sati",
        "phase": "setting",
        "saturn_sign": "Pisces",
        "start": "2025-03-29",
        "end": "2028-03-28",
        "severity": 0.65,
        "description": (
            "Sade Sati Cycle 2 — Setting phase: Saturn in Pisces (2nd from natal Moon). "
            "Financial/resource pressure. Concurrent: end of Mercury MD (2027-08-21) → Ketu MD start. "
            "Transition between Mercury and Ketu MD during setting Sade Sati. "
            "Source: FORENSIC §22 Sade Sati Cycle 2."
        ),
        "concurrent_dashas": [{"md": "Mercury/Ketu", "ad": "Saturn/Ketu", "note": "MD transition during setting Sade Sati"}],
    },
]

# ── Ashtama Shani (Saturn 8H from natal Moon) ─────────────────────────────────
# 8H from natal Moon Aquarius = Virgo (Aquarius → count 8 = Virgo)
# Saturn in Virgo = H6 from Lagna Aries, H8 from Moon Aquarius

ASHTAMA_SHANI_WINDOWS: list[dict[str, Any]] = [
    {
        "obstruction_id": "OBS.ASHTA.1",
        "obstruction_type": "ashtama_shani",
        "saturn_sign": "Virgo",
        "house_from_moon": 8,
        "start": "2009-09-09",
        "end": "2011-11-14",
        "severity": 0.60,
        "description": (
            "Ashtama Shani: Saturn in Virgo = 8H from natal Moon (Aquarius). "
            "8H from Moon: hidden obstacles, unexpected health concerns, property matters. "
            "Concurrent: Saturn MD / Jupiter AD (2008-02-09 → 2010-08-21) then Mercury MD opens. "
            "Source: FORENSIC §2.1 Moon=Aquarius; classic Jyotish Ashtama Shani rule."
        ),
        "concurrent_dashas": [{"md": "Saturn", "ad": "Jupiter", "note": "Saturn-Jupiter AD during Ashtama Shani"}],
    },
]

# ── Malefic dasha confluence windows ──────────────────────────────────────────
# Both MD and AD are natural malefics simultaneously

MALEFIC_DASHA_WINDOWS: list[dict[str, Any]] = [
    {
        "obstruction_id": "OBS.MALDASH.SAT.SAT",
        "obstruction_type": "malefic_dasha",
        "md": "Saturn", "ad": "Saturn",
        "start": "1991-08-21", "end": "1994-08-24",
        "severity": 0.75,
        "description": (
            "Saturn MD / Saturn AD (DSH.V.006): double Saturn affliction. "
            "Most intense dasha period for discipline, hardship, and delay. "
            "Coincides with Sade Sati Cycle 1 rising+peak. Triple Saturn signature. "
            "Source: FORENSIC §5.1 DSH.V.006."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.SAT.KETU",
        "obstruction_type": "malefic_dasha",
        "md": "Saturn", "ad": "Ketu",
        "start": "1997-05-03", "end": "1998-06-12",
        "severity": 0.65,
        "description": (
            "Saturn MD / Ketu AD (DSH.V.008): both shadow/separative. "
            "Spiritual disruption, detachment forced on career/relationships. "
            "Ketu AD during Saturn MD = sudden separations, foreign travel themes. "
            "Source: FORENSIC §5.1 DSH.V.008."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.SAT.RAHU",
        "obstruction_type": "malefic_dasha",
        "md": "Saturn", "ad": "Rahu",
        "start": "2005-04-03", "end": "2008-02-09",
        "severity": 0.75,
        "description": (
            "Saturn MD / Rahu AD (DSH.V.013): dual shadow-malefic. "
            "Rahu in Saturn MD = intense ambition under karmic pressure. "
            "Technology/foreign domains activated but with obstacles. "
            "Source: FORENSIC §5.1 DSH.V.013."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.MERC.RAHU",
        "obstruction_type": "malefic_dasha",
        "md": "Mercury", "ad": "Rahu",
        "start": "2020-02-18", "end": "2022-09-06",
        "severity": 0.60,
        "description": (
            "Mercury MD / Rahu AD (DSH.V.021): Mercury (functional benefic) + Rahu (shadow). "
            "Rahu in Mercury MD = amplified ambition, digital/tech disruption, scattered focus. "
            "Coincides with Sade Sati Cycle 2 rising. "
            "Source: FORENSIC §5.1 DSH.V.021."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.KETU.KETU",
        "obstruction_type": "malefic_dasha",
        "md": "Ketu", "ad": "Ketu",
        "start": "2027-08-21", "end": "2028-01-18",
        "severity": 0.70,
        "description": (
            "Ketu MD / Ketu AD (DSH.V.024): double Ketu. "
            "Most intense spiritual-karmic isolation. Sudden separations, health attention. "
            "Strong moksha orientation; worldly agenda disrupted. "
            "Source: FORENSIC §5.1 DSH.V.024."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.KETU.RAHU",
        "obstruction_type": "malefic_dasha",
        "md": "Ketu", "ad": "Rahu",
        "start": "2030-07-21", "end": "2031-08-09",
        "severity": 0.65,
        "description": (
            "Ketu MD / Rahu AD (DSH.V.029): nodal axis fully active. "
            "Karmic resolution period — north node (Rahu) ambition within south-node (Ketu) release. "
            "Major life recalibration expected. "
            "Source: FORENSIC §5.1 DSH.V.029."
        ),
    },
    {
        "obstruction_id": "OBS.MALDASH.KETU.SAT",
        "obstruction_type": "malefic_dasha",
        "md": "Ketu", "ad": "Saturn",
        "start": "2032-07-15", "end": "2033-08-24",
        "severity": 0.65,
        "description": (
            "Ketu MD / Saturn AD (DSH.V.031): spiritual isolation + Saturnine pressure. "
            "Disciplined withdrawal; delays and karmic debts surface. "
            "Source: FORENSIC §5.1 DSH.V.031."
        ),
    },
]

# ── Combustion periods ─────────────────────────────────────────────────────────
# Key: Jupiter and Venus are the native's primary benefics.
# Jupiter combustion (within 11° of Sun): occurs briefly each year (~20-30 days).
# Most significant: when Jupiter is combust during a dasha AD when Jupiter is the AD lord.
# Source: Classical rules; exact dates require Swiss Ephemeris (approximated here).

COMBUSTION_WINDOWS: list[dict[str, Any]] = [
    {
        "obstruction_id": "OBS.COMB.JUP.1989",
        "obstruction_type": "combustion_period",
        "planet": "Jupiter",
        "start": "1989-11-15", "end": "1989-12-10",
        "severity": 0.50,
        "description": (
            "Jupiter combustion ~Nov-Dec 1989 (near Sagittarius): benefic Jupiter weakened. "
            "Concurrent Jupiter MD / Rahu AD. Protection reduced during Rahu sub-period. "
            "Source: classical combustion rule; approximate dates [EXTERNAL_COMPUTATION_REQUIRED for exact]."
        ),
    },
    {
        "obstruction_id": "OBS.COMB.JUP.2002",
        "obstruction_type": "combustion_period",
        "planet": "Jupiter",
        "start": "2002-09-05", "end": "2002-09-30",
        "severity": 0.50,
        "description": (
            "Jupiter combustion ~Sep 2002 (Leo/Cancer): benefic Jupiter weakened. "
            "Concurrent Saturn MD / Moon AD (2002-07-24 → 2004-02-24). "
            "Public/emotional domain affected during Moon AD. "
            "Source: classical combustion rule; approximate dates [EXTERNAL_COMPUTATION_REQUIRED]."
        ),
    },
    {
        "obstruction_id": "OBS.COMB.JUP.2022",
        "obstruction_type": "combustion_period",
        "planet": "Jupiter",
        "start": "2022-12-10", "end": "2023-01-05",
        "severity": 0.45,
        "description": (
            "Jupiter combustion ~Dec 2022 (Pisces): benefic Jupiter weakened near start of Taurus transit. "
            "Concurrent Mercury MD / Jupiter AD (2022-09-06 → 2024-12-12) — AD lord temporarily combust. "
            "Short window; career/expansion subdued briefly. "
            "Source: classical combustion rule; approximate [EXTERNAL_COMPUTATION_REQUIRED for exact]."
        ),
    },
]


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def compute_obstructions(
    start_date: date | None = None,
    end_date: date | None = None,
    obstruction_types: list[str] | None = None,
    min_severity: float = 0.0,
) -> list[dict[str, Any]]:
    """
    Compute all obstruction periods for the native that overlap [start_date, end_date].

    Includes: Sade Sati, Ashtama Shani, malefic dasha confluence, combustion periods,
    and double-affliction markers (where ≥2 obstruction types coincide).

    Args:
        start_date:         Inclusive start (default 1984-01-01).
        end_date:           Inclusive end (default 2040-12-31).
        obstruction_types:  Filter list (e.g. ["sade_sati", "malefic_dasha"]). None=all.
        min_severity:       Minimum severity threshold [0.0, 1.0].

    Returns:
        Sorted list of obstruction dicts, plus synthesized double_affliction entries.
    """
    if start_date is None:
        start_date = date(1984, 1, 1)
    if end_date is None:
        end_date = date(2040, 12, 31)

    all_entries: list[dict[str, Any]] = (
        SADE_SATI_WINDOWS
        + ASHTAMA_SHANI_WINDOWS
        + MALEFIC_DASHA_WINDOWS
        + COMBUSTION_WINDOWS
    )

    # Filter to date range
    in_range: list[dict[str, Any]] = []
    for entry in all_entries:
        e_start = _parse_date(entry["start"])
        e_end = _parse_date(entry["end"])
        if e_end < start_date or e_start > end_date:
            continue

        # Clamp display dates
        display_start = max(e_start, start_date)
        display_end = min(e_end, end_date)

        row = dict(entry)
        row["display_start"] = display_start.isoformat()
        row["display_end"] = display_end.isoformat()
        row.setdefault("source_citation", SOURCE_CITATION)
        in_range.append(row)

    # ── Synthesize double_affliction entries ───────────────────────────────────
    # Double affliction: a sade_sati or ashtama_shani + a malefic_dasha overlap
    sade_sati_entries = [e for e in in_range if e["obstruction_type"] == "sade_sati"]
    ashtama_entries = [e for e in in_range if e["obstruction_type"] == "ashtama_shani"]
    malefic_dashas = [e for e in in_range if e["obstruction_type"] == "malefic_dasha"]

    double_afflictions: list[dict[str, Any]] = []
    for transit_obs in sade_sati_entries + ashtama_entries:
        t_start = _parse_date(transit_obs["start"])
        t_end = _parse_date(transit_obs["end"])
        for dash_obs in malefic_dashas:
            d_start = _parse_date(dash_obs["start"])
            d_end = _parse_date(dash_obs["end"])
            # Check overlap
            overlap_start = max(t_start, d_start, start_date)
            overlap_end = min(t_end, d_end, end_date)
            if overlap_start > overlap_end:
                continue
            combined_severity = min(transit_obs["severity"] + dash_obs["severity"] * 0.3, 1.0)
            oid = f"OBS.DOUBLE.{transit_obs['obstruction_id']}.{dash_obs['obstruction_id']}"
            double_afflictions.append({
                "obstruction_id": oid,
                "obstruction_type": "double_affliction",
                "start": overlap_start.isoformat(),
                "end": overlap_end.isoformat(),
                "display_start": overlap_start.isoformat(),
                "display_end": overlap_end.isoformat(),
                "severity": round(combined_severity, 4),
                "description": (
                    f"Double affliction: {transit_obs['obstruction_type']} "
                    f"({transit_obs.get('saturn_sign', transit_obs['obstruction_id'])}) "
                    f"+ {dash_obs['obstruction_type']} "
                    f"({dash_obs.get('md', '')} MD / {dash_obs.get('ad', '')} AD). "
                    "Concurrent malefic transit + malefic dasha = peak obstruction window."
                ),
                "source_obstruction_a": transit_obs["obstruction_id"],
                "source_obstruction_b": dash_obs["obstruction_id"],
                "source_citation": SOURCE_CITATION,
            })

    in_range.extend(double_afflictions)

    # Apply type filter
    if obstruction_types:
        in_range = [e for e in in_range if e["obstruction_type"] in obstruction_types]

    # Apply severity filter
    if min_severity > 0.0:
        in_range = [e for e in in_range if e["severity"] >= min_severity]

    # Sort by start date
    in_range.sort(key=lambda e: e.get("display_start", e.get("start", "")))
    return in_range


def query_obstruction_periods(
    chart_id: str,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    obstruction_types: list[str] | None = None,
    min_severity: float = 0.0,
) -> dict[str, Any]:
    """
    Query obstruction periods for a chart.

    Args:
        chart_id:           Chart UUID (for provenance).
        start_date:         Filter start date.
        end_date:           Filter end date.
        obstruction_types:  List of types to include. None = all.
        min_severity:       Minimum severity threshold.

    Returns:
        {
          "obstructions": [...],
          "count": int,
          "volume_floor_met": bool,
          "by_type": {"sade_sati": N, ...},
          "peak_periods": [...],  # severity >= 0.75
          "provenance_envelope": {...}
        }
    """
    if isinstance(start_date, str):
        start_date = _parse_date(start_date)
    if isinstance(end_date, str):
        end_date = _parse_date(end_date)

    entries = compute_obstructions(
        start_date, end_date, obstruction_types, min_severity
    )

    by_type: dict[str, int] = {}
    for e in entries:
        ot = e["obstruction_type"]
        by_type[ot] = by_type.get(ot, 0) + 1

    peak = [e for e in entries if e["severity"] >= 0.75]

    # Volume floor counts all obstruction types (not just base types)
    base_types = [e for e in entries if e["obstruction_type"] != "double_affliction"]

    return {
        "obstructions": entries,
        "count": len(entries),
        "base_count": len(base_types),
        "volume_floor_met": len(base_types) >= VOLUME_FLOOR,
        "by_type": by_type,
        "peak_periods": [
            {"obstruction_id": e["obstruction_id"],
             "start": e.get("display_start", e.get("start")),
             "end": e.get("display_end", e.get("end")),
             "severity": e["severity"],
             "type": e["obstruction_type"]}
            for e in peak
        ],
        "provenance_envelope": {
            "asset": "kala.obstruction",
            "unit": "KA-3-3",
            "chart_id": chart_id,
            "source_citation": SOURCE_CITATION,
            "layer": "L3 Kāla",
            "start_date": str(start_date or "1984-01-01"),
            "end_date": str(end_date or "2040-12-31"),
            "volume_floor": VOLUME_FLOOR,
            "native_moon_sign": NATIVE_MOON_SIGN,
            "native_lagna": NATIVE_LAGNA,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_gate(chart_id: str = NATIVE_CHART_ID) -> bool:
    """
    KA-3-3 acceptance gate:

    G1: ≥ 10 base obstruction entries (volume floor)
    G2: Sade Sati Cycle 1 (1990-1998) present
    G3: Sade Sati Cycle 2 (2020-2028) present
    G4: Double-affliction entries present (synthesized overlap)
    G5: All severity values in [0.0, 1.0]
    G6: source_citation non-null on all entries
    G7: Saturn-Saturn AD period (1991-1994) flagged as malefic_dasha
    G8: Peak obstructions (severity ≥ 0.75) present
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

    print("=== KA-3-3 Acceptance Gate (l3_obstruction) ===")

    result = query_obstruction_periods(
        chart_id,
        start_date=date(1984, 1, 1),
        end_date=date(2040, 12, 31),
    )
    entries = result["obstructions"]
    base = [e for e in entries if e["obstruction_type"] != "double_affliction"]

    # G1: volume floor
    check("G1: ≥ 10 base obstruction entries", result["base_count"] >= VOLUME_FLOOR,
          f"actual={result['base_count']}/{VOLUME_FLOOR}")

    # G2: Sade Sati Cycle 1 (1990-1998)
    ss_c1 = [e for e in entries
             if e["obstruction_type"] == "sade_sati"
             and _parse_date(e.get("start", "9999-01-01")) <= date(1998, 4, 14)
             and _parse_date(e.get("end", "1900-01-01")) >= date(1990, 1, 1)]
    check("G2: Sade Sati Cycle 1 (1990-1998) present", len(ss_c1) > 0,
          f"ss_c1_entries={len(ss_c1)}")

    # G3: Sade Sati Cycle 2 (2020-2028)
    ss_c2 = [e for e in entries
             if e["obstruction_type"] == "sade_sati"
             and _parse_date(e.get("start", "9999-01-01")) <= date(2028, 3, 28)
             and _parse_date(e.get("end", "1900-01-01")) >= date(2020, 1, 1)]
    check("G3: Sade Sati Cycle 2 (2020-2028) present", len(ss_c2) > 0,
          f"ss_c2_entries={len(ss_c2)}")

    # G4: Double-affliction entries
    double = [e for e in entries if e["obstruction_type"] == "double_affliction"]
    check("G4: double_affliction entries present", len(double) > 0,
          f"double_count={len(double)}")

    # G5: severity in [0.0, 1.0]
    bad_sev = [e for e in entries if not (0.0 <= e.get("severity", -1) <= 1.0)]
    check("G5: severity in [0.0,1.0]", len(bad_sev) == 0,
          f"bad_count={len(bad_sev)}")

    # G6: source_citation non-null
    null_cit = [e for e in entries if not e.get("source_citation")]
    check("G6: source_citation non-null", len(null_cit) == 0,
          f"null_count={len(null_cit)}")

    # G7: Saturn-Saturn AD (1991-1994) as malefic_dasha
    sat_sat = [e for e in entries
               if e["obstruction_type"] == "malefic_dasha"
               and e.get("md") == "Saturn" and e.get("ad") == "Saturn"]
    check("G7: Saturn-Saturn AD flagged as malefic_dasha", len(sat_sat) > 0,
          f"count={len(sat_sat)}")

    # G8: peak periods (severity ≥ 0.75)
    check("G8: peak periods (severity ≥ 0.75) present", len(result["peak_periods"]) > 0,
          f"peak_count={len(result['peak_periods'])}")

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0
