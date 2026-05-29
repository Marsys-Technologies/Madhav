"""
houses_renderer.py — House cusps, 6-system comparison, and Arudha padas
renderer for FORENSIC.md (F-03).

Produces deterministic, tabular output.
No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOUSE_SYSTEMS: list[str] = [
    "placidus",
    "whole_sign",
    "equal",
    "koch",
    "campanus",
    "porphyry",
]

HOUSE_SYSTEM_LABELS: dict[str, str] = {
    "placidus": "Placidus",
    "whole_sign": "Whole Sign",
    "equal": "Equal",
    "koch": "Koch",
    "campanus": "Campanus",
    "porphyry": "Porphyry",
}

ARUDHA_NAMES: list[str] = [f"A{i}" for i in range(1, 13)]

_NA = "—"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_houses_list(houses_data: Any) -> list[dict]:
    """Normalise houses data to a list of 12 dicts (or empty list)."""
    if not houses_data:
        return []
    if isinstance(houses_data, list):
        return houses_data
    return []


def _index_houses(houses_list: list[dict]) -> dict[int, dict]:
    """Return dict keyed by house number (1–12)."""
    index: dict[int, dict] = {}
    for entry in houses_list:
        h = entry.get("house")
        if h is not None:
            try:
                index[int(h)] = entry
            except (TypeError, ValueError):
                pass
    return index


def _fmt_sign(val: Any) -> str:
    if val is None:
        return "N/A"
    return str(val)


def _fmt_lord(val: Any) -> str:
    if val is None:
        return _NA
    return str(val)


def _fmt_nakshatra(entry: dict) -> str:
    nakshatra = entry.get("nakshatra")
    pada = entry.get("pada")
    if nakshatra is None:
        return "N/A"
    if pada is None:
        return str(nakshatra)
    return f"{nakshatra} Pada {pada}"


def _fmt_occupants(entry: dict) -> str:
    occ = entry.get("occupying_planets")
    if not occ:
        return _NA
    # Capitalise each body name for display
    names = [str(p).replace("_", " ").title() for p in occ]
    return ", ".join(names)


def _fmt_co_lord(entry: dict) -> str:
    co = entry.get("co_lord")
    if co is None:
        return _NA
    return str(co)


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_house_details(houses_list: list[dict]) -> str:
    """Per-house detail table (12 rows) using Placidus data."""
    lines: list[str] = [
        "### House Details (Placidus Default)\n",
        "| House | Sign | Lord | Co-Lord | Nakshatra | Occupants |",
        "|-------|------|------|---------|-----------|-----------|",
    ]
    index = _index_houses(houses_list)

    for h in range(1, 13):
        entry = index.get(h, {})
        if entry:
            sign = _fmt_sign(entry.get("sign"))
            lord = _fmt_lord(entry.get("lord"))
            co_lord = _fmt_co_lord(entry)
            nakshatra = _fmt_nakshatra(entry)
            occupants = _fmt_occupants(entry)
        else:
            sign = lord = co_lord = nakshatra = occupants = "N/A"

        lines.append(
            f"| {h} | {sign} | {lord} | {co_lord} | {nakshatra} | {occupants} |"
        )

    return "\n".join(lines) + "\n"


def _render_house_system_comparison(houses: dict) -> str:
    """6-system × 12-house sign grid."""
    # Build per-system index: system_key → {house_num: sign}
    system_indices: dict[str, dict[int, str]] = {}
    for sys_key in HOUSE_SYSTEMS:
        raw = houses.get(sys_key) or []
        idx = {}
        for entry in raw:
            h = entry.get("house")
            sign = entry.get("sign")
            if h is not None and sign is not None:
                try:
                    idx[int(h)] = str(sign)
                except (TypeError, ValueError):
                    pass
        system_indices[sys_key] = idx

    labels = [HOUSE_SYSTEM_LABELS[s] for s in HOUSE_SYSTEMS]
    header = "| House | " + " | ".join(labels) + " |"
    sep = "|-------|" + "|".join(["----------"] * len(HOUSE_SYSTEMS)) + "|"

    lines: list[str] = [
        "### House System Comparison\n",
        header,
        sep,
    ]

    for h in range(1, 13):
        cells = []
        for sys_key in HOUSE_SYSTEMS:
            cells.append(system_indices[sys_key].get(h, "N/A"))
        lines.append("| " + str(h) + " | " + " | ".join(cells) + " |")

    return "\n".join(lines) + "\n"


def _render_arudhas(arudhas: dict) -> str:
    """A1–A12 table."""
    lines: list[str] = [
        "### Arudha Padas (A1–A12)\n",
        "| Arudha | Sign | Lord |",
        "|--------|------|------|",
    ]

    for name in ARUDHA_NAMES:
        entry = arudhas.get(name) if arudhas else None
        if entry:
            sign = _fmt_sign(entry.get("sign"))
            lord = _fmt_lord(entry.get("lord"))
        else:
            sign = lord = "N/A"
        lines.append(f"| {name} | {sign} | {lord} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_houses_section(chart_output: dict) -> str:
    """
    Render the full houses + Arudha section for FORENSIC.md.

    Covers:
    - Per-house detail table (sign, lord, co-lord, nakshatra, occupants)
      derived from the Placidus system.
    - 6-house-system comparison grid (Placidus / Whole Sign / Equal /
      Koch / Campanus / Porphyry).
    - Arudha Padas A1–A12.

    Returns a markdown string with no narration verbs.
    Gracefully degrades to N/A when data is absent.
    """
    houses: dict = chart_output.get("houses") or {}
    arudhas: dict = chart_output.get("arudhas") or {}

    placidus_list = _get_houses_list(houses.get("placidus"))

    parts: list[str] = []

    # 1. Per-house detail (Placidus)
    parts.append(_render_house_details(placidus_list))
    parts.append("\n")

    # 2. 6-system comparison
    parts.append(_render_house_system_comparison(houses))
    parts.append("\n")

    # 3. Arudha padas
    parts.append(_render_arudhas(arudhas))

    return "\n".join(parts)
