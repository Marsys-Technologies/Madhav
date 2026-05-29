"""
vimsopaka_renderer.py — Vimsopaka dignities + 5 Avastha schemes renderer (F-11).

Covers:
  1. Vimsopaka table — 9 grahas × 4 varga groups (scores 0–20)
  2. Baladi Avastha — 5 states by zodiacal degree position
  3. Jagradadi Avastha — 3 states (Jagrat/Swapna/Sushupti)
  4. Deeptadi Avastha — 9 states by dignity
  5. Lajjitadi Avastha — 6 states by house combination
  6. Shayanaadi Avastha — sleeping/sitting/standing by house

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRAHAS: list[str] = [
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
]

GRAHA_DISPLAY: dict[str, str] = {
    "sun":     "Sun",
    "moon":    "Moon",
    "mars":    "Mars",
    "mercury": "Mercury",
    "jupiter": "Jupiter",
    "venus":   "Venus",
    "saturn":  "Saturn",
    "rahu":    "Rahu",
    "ketu":    "Ketu",
}

# 4 varga groups for Vimsopaka
VARGA_GROUPS: list[tuple[str, str, str]] = [
    ("saptavarga",   "Saptavarga",   "D1/D2/D3/D7/D9/D12/D30"),
    ("dashavarga",   "Dashavarga",   "+D4/D10/D16"),
    ("shadvarga",    "Shadvarga",    "+D6/D8/D27/D40/D45/D60"),
    ("shodasavarga", "Shodasavarga", "all 16"),
]

# 5 Avastha scheme definitions
AVASTHA_SCHEMES: list[tuple[str, str, str]] = [
    ("baladi",     "Baladi",     "5 states by zodiacal degree"),
    ("jagradadi",  "Jagradadi",  "3 states: Jagrat/Swapna/Sushupti"),
    ("deeptadi",   "Deeptadi",   "9 states by dignity"),
    ("lajjitadi",  "Lajjitadi",  "6 states by house combination"),
    ("shayanaadi", "Shayanaadi", "sleeping/sitting/standing by house"),
]

_NA = "—"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _fmt_score(value: Any) -> str:
    """Format Vimsopaka score to 1 decimal; '—' if absent."""
    if value is None:
        return _NA
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return _NA


def _safe_str(value: Any, fallback: str = _NA) -> str:
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_vimsopaka(vimsopaka_data: dict) -> str:
    """
    Render Vimsopaka table: 9 grahas × 4 varga groups.

    Data path: vimsopaka_data[graha][group_key] = float (0–20)
    """
    group_header = " | ".join(f"{display} ({note})" for _, display, note in VARGA_GROUPS)
    sep_cols     = " | ".join(["-----"] * len(VARGA_GROUPS))

    lines: list[str] = [
        "### Vimsopaka Dignities (9 Grahas × 4 Varga Groups)\n",
        f"| Graha | {group_header} |",
        f"|-------|{sep_cols}|",
    ]

    for graha in GRAHAS:
        gdata: dict = vimsopaka_data.get(graha) or {}
        cells = [_fmt_score(gdata.get(key)) for key, _, _ in VARGA_GROUPS]
        lines.append(f"| {GRAHA_DISPLAY[graha]} | {' | '.join(cells)} |")

    return "\n".join(lines) + "\n"


def _render_avastha_scheme(scheme_key: str, scheme_display: str, scheme_note: str,
                            avasthas_data: dict) -> str:
    """
    Render one Avastha scheme table: 9 grahas × name + effect.

    Data path: avasthas_data[graha][scheme_key] = {name, effect}
    """
    lines: list[str] = [
        f"### Avastha — {scheme_display} ({scheme_note})\n",
        f"| Graha | {scheme_display} Name | Effect |",
        f"|-------|{''.join(['-'] * (len(scheme_display) + 7))}|--------|",
    ]

    for graha in GRAHAS:
        graha_avasthas: dict = avasthas_data.get(graha) or {}
        scheme_data: dict    = graha_avasthas.get(scheme_key) or {}
        name   = _safe_str(scheme_data.get("name"))
        effect = _safe_str(scheme_data.get("effect"))
        lines.append(f"| {GRAHA_DISPLAY[graha]} | {name} | {effect} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_vimsopaka_section(chart_output: dict) -> str:
    """
    Render the full Vimsopaka + Avastha section for FORENSIC.md (F-11).

    Covers:
    1. Vimsopaka dignities table (9 grahas × 4 varga groups)
    2. Baladi Avastha (5 states by zodiacal position)
    3. Jagradadi Avastha (3 states)
    4. Deeptadi Avastha (9 states by dignity)
    5. Lajjitadi Avastha (6 states by house combination)
    6. Shayanaadi Avastha (sleeping/sitting/standing)

    Expected chart_output keys:
      "vimsopaka" — dict keyed by graha, each with 4 varga-group scores
      "avasthas"  — dict keyed by graha, each with 5 scheme dicts

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder cells when data is absent.
    """
    vimsopaka_data: dict = chart_output.get("vimsopaka") or {}
    avasthas_data: dict  = chart_output.get("avasthas") or {}

    parts: list[str] = []

    # 1. Vimsopaka table
    parts.append(_render_vimsopaka(vimsopaka_data))
    parts.append("\n")

    # 2–6. One table per avastha scheme
    for scheme_key, scheme_display, scheme_note in AVASTHA_SCHEMES:
        parts.append(_render_avastha_scheme(
            scheme_key, scheme_display, scheme_note, avasthas_data
        ))
        parts.append("\n")

    return "\n".join(parts)
