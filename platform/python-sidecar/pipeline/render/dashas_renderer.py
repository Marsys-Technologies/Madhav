"""
dashas_renderer.py — All 32 dasha systems at Sookshma depth renderer (F-13).

Covers:
  1. Condensed current-period chain tables for all 32 dasha systems
     (Maha → Antar → Pratyantar → Sookshma)
  2. Next-10 Mahadasha table for 7 acharya-selected systems
  3. Two-pass verification for Vimshottari + Jaimini Chara Dasha

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 7 acharya-selected systems for next-10 Mahas table
ACHARYA_SYSTEMS: list[tuple[str, str]] = [
    ("vimshottari",      "Vimshottari"),
    ("yogini",           "Yogini"),
    ("ashtottari",       "Ashtottari"),
    ("chara_karaka",     "Jaimini Chara Karaka"),
    ("naisargika",       "Naisargika"),
    ("mudda",            "Mudda (Annual)"),
    ("kalachakra",       "Kalachakra"),
]

# Full 32 dasha system list (key, display label)
ALL_DASHA_SYSTEMS: list[tuple[str, str]] = [
    ("vimshottari",          "Vimshottari"),
    ("ashtottari",           "Ashtottari"),
    ("shodashottari",        "Shodashottari"),
    ("dvadashottari",        "Dvadashottari"),
    ("panchottari",          "Panchottari"),
    ("shatabdika",           "Shatabdika"),
    ("chaturashiti_sama",    "Chaturashiti Sama"),
    ("dvisaptati_sama",      "Dvisaptati Sama"),
    ("shat_trimsha_sama",    "Shat Trimsha Sama"),
    ("yogini",               "Yogini"),
    ("naisargika",           "Naisargika"),
    ("mudda",                "Mudda (Annual)"),
    ("kalachakra",           "Kalachakra"),
    ("chara_karaka",         "Jaimini Chara Karaka"),
    ("sthira",               "Jaimini Sthira"),
    ("brahma",               "Jaimini Brahma"),
    ("mandooka",             "Jaimini Mandooka"),
    ("niryana_shoola",       "Niryana Shoola"),
    ("shoola",               "Shoola"),
    ("pinda",                "Pinda"),
    ("amsha",                "Amsha"),
    ("narayana",             "Narayana"),
    ("lagna_kendradi",       "Lagna Kendradi"),
    ("hora",                 "Hora"),
    ("paryaya",              "Paryaya"),
    ("tara",                 "Tara"),
    ("ashtama",              "Ashtama"),
    ("drig",                 "Drig"),
    ("pancha_swara",         "Pancha Swara"),
    ("tithi_ashtottari",     "Tithi Ashtottari"),
    ("navamsha",             "Navamsha Dasha"),
    ("dwisaptati",           "Dwisaptati Sama"),
]

PERIOD_LEVELS: list[tuple[str, str]] = [
    ("maha",       "Maha"),
    ("antar",      "Antar"),
    ("pratyantar", "Pratyantar"),
    ("sookshma",   "Sookshma"),
]

_NA = "—"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe(value: Any, fallback: str = _NA) -> str:
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback


def _safe_int(value: Any) -> str:
    if value is None:
        return _NA
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return _NA


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_current_chain(system_key: str, system_display: str, system_data: dict) -> str:
    """
    Render current dasha period chain table for one system.

    system_data keys:
      birth_nakshatra_balance (str, optional)
      current_chain (list[str], optional)
      current_dates (dict: maha/antar/pratyantar/sookshma → {lord, start, end})
    """
    balance = _safe(system_data.get("birth_nakshatra_balance"), "N/A")
    current_dates: dict = system_data.get("current_dates") or {}

    lines: list[str] = [
        f"#### {system_display}\n",
    ]

    if balance != "N/A":
        lines.append(f"**Birth balance:** {balance}\n")

    lines += [
        "| Level | Lord | Start | End |",
        "|-------|------|-------|-----|",
    ]

    for level_key, level_display in PERIOD_LEVELS:
        pdata: dict = current_dates.get(level_key) or {}
        lord  = _safe(pdata.get("lord"))
        start = _safe(pdata.get("start"))
        end   = _safe(pdata.get("end"))
        lines.append(f"| {level_display} | {lord} | {start} | {end} |")

    return "\n".join(lines) + "\n"


def _render_next_10_mahas(system_key: str, system_display: str, system_data: dict) -> str:
    """
    Render next-10 Mahadasha table.

    system_data["next_10_mahas"] = list of {lord, start, end, years}
    """
    mahas: list = system_data.get("next_10_mahas") or []

    lines: list[str] = [
        f"##### {system_display} — Next 10 Mahadashas\n",
        "| # | Lord | Start | End | Years |",
        "|---|------|-------|-----|-------|",
    ]

    for i, maha in enumerate(mahas[:10], start=1):
        if not isinstance(maha, dict):
            continue
        lord  = _safe(maha.get("lord"))
        start = _safe(maha.get("start"))
        end   = _safe(maha.get("end"))
        years = _safe_int(maha.get("years"))
        lines.append(f"| {i} | {lord} | {start} | {end} | {years} |")

    if not mahas:
        lines.append("| — | — | — | — | — |")

    return "\n".join(lines) + "\n"


def _render_verification(system_key: str, system_display: str, verif_data: dict) -> str:
    """
    Render two-pass verification block for one system.
    """
    match: bool  = bool(verif_data.get("match", False))
    notes: str   = _safe(verif_data.get("notes"), "")
    status = "PASS" if match else "FAIL"
    match_icon = "✓" if match else "✗"

    lines: list[str] = [
        f"#### Two-Pass Verification — {system_display}\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| Match | {match_icon} {status} |",
    ]
    if notes:
        lines.append(f"| Notes | {notes} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_dashas_section(chart_output: dict) -> str:
    """
    Render the full Dashas section for FORENSIC.md (F-13).

    Covers:
    1. Current period chain (Maha→Antar→Pratyantar→Sookshma) for all 32 systems
    2. Next-10 Mahas for 7 acharya-selected systems
    3. Two-pass verification for Vimshottari + Jaimini Chara Dasha

    Expected chart_output keys:
      "dashas"                    — dict keyed by system key
      "d9_verification_vimshottari" — dict with match + optional notes
      "d9_verification_chara"     — dict with match + optional notes

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder cells when data is absent.
    """
    dashas_data: dict         = chart_output.get("dashas") or {}
    verif_vimsh: dict         = chart_output.get("d9_verification_vimshottari") or {}
    verif_chara: dict         = chart_output.get("d9_verification_chara") or {}

    parts: list[str] = []

    # 1. All 32 systems — current period chain
    parts.append("### Current Period Chains (All 32 Dasha Systems)\n\n")
    for system_key, system_display in ALL_DASHA_SYSTEMS:
        sdata = dashas_data.get(system_key) or {}
        parts.append(_render_current_chain(system_key, system_display, sdata))
        parts.append("\n")

    # 2. Next-10 Mahas for acharya-selected systems
    parts.append("### Next 10 Mahadashas — Acharya-Selected Systems\n\n")
    for system_key, system_display in ACHARYA_SYSTEMS:
        sdata = dashas_data.get(system_key) or {}
        parts.append(_render_next_10_mahas(system_key, system_display, sdata))
        parts.append("\n")

    # 3. Two-pass verification
    parts.append("### Two-Pass Dasha Verification\n\n")
    parts.append(_render_verification("vimshottari", "Vimshottari", verif_vimsh))
    parts.append("\n")
    parts.append(_render_verification("chara_karaka", "Jaimini Chara", verif_chara))

    return "\n".join(parts)
