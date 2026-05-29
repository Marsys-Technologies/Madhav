"""
upagrahas_renderer.py — Upagrahas and Saturn-derived points renderer
for FORENSIC.md (F-04).

Covers the 7 classical upagrahas (BPHS Ch 4) plus Saturn-derived
sensitive points. Produces deterministic, tabular output.
No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UPAGRAHAS: list[str] = [
    "gulika",
    "maandi",
    "dhuma",
    "vyatipata",
    "parivesha",
    "indrachapa",
    "upaketu",
]

SATURN_DERIVED: list[str] = [
    "mrityu_sahama",
]

UPAGRAHA_LABELS: dict[str, str] = {
    "gulika":      "Gulika (Mandi)",
    "maandi":      "Maandi",
    "dhuma":       "Dhuma",
    "vyatipata":   "Vyatipata",
    "parivesha":   "Parivesha",
    "indrachapa":  "Indrachapa (Indra Chapa)",
    "upaketu":     "Upaketu",
}

SATURN_DERIVED_LABELS: dict[str, str] = {
    "mrityu_sahama": "Mrityu Sahama",
}

# BPHS Ch 4 formula references (verse ranges per standard editions)
BPHS_REFS: dict[str, str] = {
    "gulika":      "Ch 4, v 33-36",
    "maandi":      "Ch 4, v 33-36",
    "dhuma":       "Ch 4, v 37-38",
    "vyatipata":   "Ch 4, v 37-38",
    "parivesha":   "Ch 4, v 37-38",
    "indrachapa":  "Ch 4, v 37-38",
    "upaketu":     "Ch 4, v 37-38",
    "mrityu_sahama": "Ch 4 (sahama formula)",
}

_NA = "N/A"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_degree(value: Any) -> str:
    """Format a decimal longitude as DD°MM'."""
    if value is None:
        return _NA
    try:
        f = float(value)
        deg_int = int(f)
        minutes = round((f - deg_int) * 60)
        return f"{deg_int}°{minutes:02d}'"
    except (TypeError, ValueError):
        return _NA


def _fmt_sign(value: Any) -> str:
    if value is None:
        return _NA
    return str(value)


def _fmt_nakshatra(entry: dict) -> str:
    nakshatra = entry.get("nakshatra")
    pada = entry.get("pada")
    if nakshatra is None:
        return _NA
    if pada is None:
        return str(nakshatra)
    return f"{nakshatra} Pada {pada}"


def _fmt_house(entry: dict) -> str:
    house = entry.get("house")
    if house is None:
        return _NA
    return str(house)


def _fmt_day_night(entry: dict, key: str) -> str:
    """Format day_birth_value or night_birth_value as DD°MM'."""
    value = entry.get(key)
    return _fmt_degree(value)


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_upagrahas_table(upagrahas_data: dict) -> str:
    """Render the 7 classical upagrahas as a markdown table."""
    lines: list[str] = [
        "### Upagrahas\n",
        "| Upagraha | Longitude | Sign | Nakshatra | Pada | House"
        " | Day-Birth Formula | Night-Birth Formula | BPHS Ref |",
        "|----------|-----------|------|-----------|------|-------|"
        "-------------------|---------------------|----------|",
    ]

    for key in UPAGRAHAS:
        label = UPAGRAHA_LABELS[key]
        entry = upagrahas_data.get(key) or {}

        longitude = _fmt_degree(entry.get("degree") if entry.get("degree") is not None
                                else entry.get("longitude"))
        sign      = _fmt_sign(entry.get("sign"))
        nakshatra = entry.get("nakshatra", _NA) or _NA
        pada_raw  = entry.get("pada")
        pada      = str(pada_raw) if pada_raw is not None else _NA
        house     = _fmt_house(entry)
        day_val   = _fmt_day_night(entry, "day_birth_value")
        night_val = _fmt_day_night(entry, "night_birth_value")
        bphs_ref  = BPHS_REFS.get(key, _NA)

        lines.append(
            f"| {label} | {longitude} | {sign} | {nakshatra} | {pada}"
            f" | {house} | {day_val} | {night_val} | {bphs_ref} |"
        )

    lines.append("")
    lines.append(
        "**Formula source:** BPHS Ch 4 (upagraha computation rules)"
    )
    return "\n".join(lines) + "\n"


def _render_saturn_derived_table(upagrahas_data: dict) -> str:
    """Render Saturn-derived sensitive points as a markdown table."""
    lines: list[str] = [
        "### Saturn-Derived Points\n",
        "| Point | Longitude | Sign | Nakshatra | Pada | House |",
        "|-------|-----------|------|-----------|------|-------|",
    ]

    for key in SATURN_DERIVED:
        label = SATURN_DERIVED_LABELS.get(key, key.replace("_", " ").title())
        entry = upagrahas_data.get(key) or {}

        longitude = _fmt_degree(entry.get("degree") if entry.get("degree") is not None
                                else entry.get("longitude"))
        sign      = _fmt_sign(entry.get("sign"))
        nakshatra = entry.get("nakshatra", _NA) or _NA
        pada_raw  = entry.get("pada")
        pada      = str(pada_raw) if pada_raw is not None else _NA
        house     = _fmt_house(entry)

        lines.append(
            f"| {label} | {longitude} | {sign} | {nakshatra} | {pada} | {house} |"
        )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_upagrahas_section(chart_output: dict) -> str:
    """
    Render the full upagrahas + Saturn-derived points section for FORENSIC.md.

    Covers:
    - 7 classical upagrahas (Gulika/Mandi, Maandi, Dhuma, Vyatipata,
      Parivesha, Indrachapa, Upaketu) with day/night birth variants.
    - Saturn-derived sensitive points (Mrityu Sahama).

    Returns a markdown string with no narration verbs.
    Gracefully degrades to N/A when data is absent.
    """
    upagrahas_data: dict = chart_output.get("upagrahas") or {}

    parts: list[str] = []

    # 1. Classical upagrahas table
    parts.append(_render_upagrahas_table(upagrahas_data))
    parts.append("\n")

    # 2. Saturn-derived points table
    parts.append(_render_saturn_derived_table(upagrahas_data))

    return "\n".join(parts)
