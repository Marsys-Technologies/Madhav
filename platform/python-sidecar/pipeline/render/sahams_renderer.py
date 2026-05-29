"""
sahams_renderer.py — Tajik Sahams + Esoteric Bindus renderer
for FORENSIC.md (F-05).

Covers 40+ Tajik Sahams (sensitive points computed from chart positions)
and 9 esoteric bindus (Bhrigu Bindu, Yogi Point, Avayogi, Mrityu Point,
Trisphuta, Chatursphuta, Panchasphuta, Pranasphuta, Dehasphuta).

Per point: name, formula used, computed longitude (sign + degree +
nakshatra + lord), day/night variant flag.

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAHAMS_CANONICAL_ORDER: list[str] = [
    "punya",
    "vidya",
    "yasas",
    "vivah",
    "karma",
    "bhagya",
    "putra",
    "aayur",
    "mrityu",
    "roga",
    "sukha",
    "dhan",
    "raja",
    "bandhu",
    "shatru",
    "labha",
    "vyaya",
    "matru",
    "pitru",
    "bhratra",
    "jalapatana",
    "paradesa",
    "vanik",
    "kheta",
    "pashu",
    "shoola",
    "bahu",
    "kshetra",
    "siddhi",
    "shaucha",
    "yatra",
    "vivaha_bandha",
    "dhana_putra",
    "aksha",
    "videsh",
    "shastra",
    "nidra",
    "chinta",
    "mitra",
    "kalatra",
]

ESOTERIC_BINDUS: list[str] = [
    "bhrigu_bindu",
    "yogi_point",
    "avayogi_point",
    "mrityu_point",
    "trisphuta",
    "chatursphuta",
    "panchasphuta",
    "pranasphuta",
    "dehasphuta",
]

SAHAM_LABELS: dict[str, str] = {
    "punya":         "Punya",
    "vidya":         "Vidya",
    "yasas":         "Yasas",
    "vivah":         "Vivah",
    "karma":         "Karma",
    "bhagya":        "Bhagya",
    "putra":         "Putra",
    "aayur":         "Aayur",
    "mrityu":        "Mrityu",
    "roga":          "Roga",
    "sukha":         "Sukha",
    "dhan":          "Dhan",
    "raja":          "Raja",
    "bandhu":        "Bandhu",
    "shatru":        "Shatru",
    "labha":         "Labha",
    "vyaya":         "Vyaya",
    "matru":         "Matru",
    "pitru":         "Pitru",
    "bhratra":       "Bhratra",
    "jalapatana":    "Jalapatana",
    "paradesa":      "Paradesa",
    "vanik":         "Vanik",
    "kheta":         "Kheta",
    "pashu":         "Pashu",
    "shoola":        "Shoola",
    "bahu":          "Bahu",
    "kshetra":       "Kshetra",
    "siddhi":        "Siddhi",
    "shaucha":       "Shaucha",
    "yatra":         "Yatra",
    "vivaha_bandha": "Vivaha Bandha",
    "dhana_putra":   "Dhana Putra",
    "aksha":         "Aksha",
    "videsh":        "Videsh",
    "shastra":       "Shastra",
    "nidra":         "Nidra",
    "chinta":        "Chinta",
    "mitra":         "Mitra",
    "kalatra":       "Kalatra",
}

BINDU_LABELS: dict[str, str] = {
    "bhrigu_bindu":  "Bhrigu Bindu",
    "yogi_point":    "Yogi Point",
    "avayogi_point": "Avayogi Point",
    "mrityu_point":  "Mrityu Point",
    "trisphuta":     "Trisphuta",
    "chatursphuta":  "Chatursphuta",
    "panchasphuta":  "Panchasphuta",
    "pranasphuta":   "Pranasphuta",
    "dehasphuta":    "Dehasphuta",
}

# Standard Tajik Saham formulas (day birth; night variants swap Sun↔Moon for
# Moon-relative sahams where applicable)
SAHAM_FORMULAS: dict[str, str] = {
    "punya":         "Moon − Sun + Lagna (day) / Sun − Moon + Lagna (night)",
    "vidya":         "Mercury − Moon + Lagna (day) / Moon − Mercury + Lagna (night)",
    "yasas":         "Jupiter − Sun + Lagna (day) / Sun − Jupiter + Lagna (night)",
    "vivah":         "Venus − Saturn + Lagna (day) / Saturn − Venus + Lagna (night)",
    "karma":         "Mars − Mercury + Lagna (day) / Mercury − Mars + Lagna (night)",
    "bhagya":        "Jupiter − Sun + Lagna (day) / Sun − Jupiter + Lagna (night)",
    "putra":         "Jupiter − Moon + Lagna (day) / Moon − Jupiter + Lagna (night)",
    "aayur":         "Saturn − Moon + Lagna (day) / Moon − Saturn + Lagna (night)",
    "mrityu":        "8th Lord − Moon + Lagna (day) / Moon − 8th Lord + Lagna (night)",
    "roga":          "Mars − Saturn + Lagna (day) / Saturn − Mars + Lagna (night)",
    "sukha":         "Venus − Moon + Lagna (day) / Moon − Venus + Lagna (night)",
    "dhan":          "Jupiter − Sun + Lagna (day) / Sun − Jupiter + Lagna (night)",
    "raja":          "Sun − Saturn + Lagna (day) / Saturn − Sun + Lagna (night)",
    "bandhu":        "Moon − Mercury + Lagna (day) / Mercury − Moon + Lagna (night)",
    "shatru":        "Mars − Moon + Lagna (day) / Moon − Mars + Lagna (night)",
    "labha":         "Jupiter − Mercury + Lagna (day) / Mercury − Jupiter + Lagna (night)",
    "vyaya":         "Saturn − Jupiter + Lagna (day) / Jupiter − Saturn + Lagna (night)",
    "matru":         "Moon − Venus + Lagna (day) / Venus − Moon + Lagna (night)",
    "pitru":         "Sun − Saturn + Lagna (day) / Saturn − Sun + Lagna (night)",
    "bhratra":       "Mars − Jupiter + Lagna (day) / Jupiter − Mars + Lagna (night)",
    "jalapatana":    "Saturn − Moon + Lagna (day) / Moon − Saturn + Lagna (night)",
    "paradesa":      "Saturn − Mars + Lagna (day) / Mars − Saturn + Lagna (night)",
    "vanik":         "Mercury − Sun + Lagna (day) / Sun − Mercury + Lagna (night)",
    "kheta":         "Mars − Saturn + Lagna (day) / Saturn − Mars + Lagna (night)",
    "pashu":         "Venus − Moon + Lagna (day) / Moon − Venus + Lagna (night)",
    "shoola":        "Mars − Saturn + Lagna (day) / Saturn − Mars + Lagna (night)",
    "bahu":          "Mars − Moon + Lagna (day) / Moon − Mars + Lagna (night)",
    "kshetra":       "Venus − Sun + Lagna (day) / Sun − Venus + Lagna (night)",
    "siddhi":        "Jupiter − Mercury + Lagna (day) / Mercury − Jupiter + Lagna (night)",
    "shaucha":       "Moon − Saturn + Lagna (day) / Saturn − Moon + Lagna (night)",
    "yatra":         "Mercury − Sun + Lagna (day) / Sun − Mercury + Lagna (night)",
    "vivaha_bandha": "Venus − Saturn + Lagna (day) / Saturn − Venus + Lagna (night)",
    "dhana_putra":   "Jupiter − Venus + Lagna (day) / Venus − Jupiter + Lagna (night)",
    "aksha":         "Saturn − Mercury + Lagna (day) / Mercury − Saturn + Lagna (night)",
    "videsh":        "Saturn − Mars + Lagna (day) / Mars − Saturn + Lagna (night)",
    "shastra":       "Mars − Sun + Lagna (day) / Sun − Mars + Lagna (night)",
    "nidra":         "Moon − Saturn + Lagna (day) / Saturn − Moon + Lagna (night)",
    "chinta":        "Mercury − Moon + Lagna (day) / Moon − Mercury + Lagna (night)",
    "mitra":         "Jupiter − Venus + Lagna (day) / Venus − Jupiter + Lagna (night)",
    "kalatra":       "Venus − Jupiter + Lagna (day) / Jupiter − Venus + Lagna (night)",
}

BINDU_FORMULAS: dict[str, str] = {
    "bhrigu_bindu":  "Midpoint(Moon, Rahu)",
    "yogi_point":    "Sun + Moon + Yogi Nakshatra Lord offset",
    "avayogi_point": "Yogi Point + 186°40'",
    "mrityu_point":  "Moon + 8th cusp − Sun",
    "trisphuta":     "Moon + Mars + Lagna",
    "chatursphuta":  "Trisphuta + Sun",
    "panchasphuta":  "Chatursphuta + Jupiter",
    "pranasphuta":   "Trisphuta + Sun + Saturn",
    "dehasphuta":    "Moon + Lagna + 8th cusp",
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
    if nakshatra is None:
        return _NA
    return str(nakshatra)


def _fmt_pada(entry: dict) -> str:
    pada = entry.get("pada")
    if pada is None:
        return _NA
    return str(pada)


def _fmt_lord(entry: dict) -> str:
    lord = entry.get("lord")
    if lord is None:
        return _NA
    return str(lord)


def _fmt_formula(key: str, entry: dict) -> str:
    """Return formula from entry override or fall back to canonical table."""
    override = entry.get("formula") if entry else None
    if override:
        return str(override)
    return SAHAM_FORMULAS.get(key, _NA)


def _fmt_bindu_formula(key: str, entry: dict) -> str:
    override = entry.get("formula") if entry else None
    if override:
        return str(override)
    return BINDU_FORMULAS.get(key, _NA)


def _get_longitude(entry: dict) -> Any:
    """Return longitude, preferring 'longitude' key, then 'degree'."""
    if entry.get("longitude") is not None:
        return entry["longitude"]
    return entry.get("degree")


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_sahams_table(sahams_data: dict) -> str:
    """Render all Tajik Sahams as a markdown table."""
    lines: list[str] = [
        "### Tajik Sahams\n",
        "| Saham | Longitude | Sign | Nakshatra | Pada | Lord | Formula |",
        "|-------|-----------|------|-----------|------|------|---------|",
    ]

    for key in SAHAMS_CANONICAL_ORDER:
        label = SAHAM_LABELS.get(key, key.replace("_", " ").title())
        entry = sahams_data.get(key) or {}

        longitude = _fmt_degree(_get_longitude(entry))
        sign      = _fmt_sign(entry.get("sign"))
        nakshatra = _fmt_nakshatra(entry)
        pada      = _fmt_pada(entry)
        lord      = _fmt_lord(entry)
        formula   = _fmt_formula(key, entry)

        lines.append(
            f"| {label} | {longitude} | {sign} | {nakshatra}"
            f" | {pada} | {lord} | {formula} |"
        )

    lines.append("")
    lines.append(
        "**Formula source:** Tajika Neelakanthi / Brihat Parashara Hora Shastra"
        " (Saham computation rules)"
    )
    return "\n".join(lines) + "\n"


def _render_esoteric_bindus_table(bindus_data: dict) -> str:
    """Render esoteric bindus as a markdown table."""
    lines: list[str] = [
        "### Esoteric Bindus\n",
        "| Bindu | Longitude | Sign | Nakshatra | Lord | Formula |",
        "|-------|-----------|------|-----------|------|---------|",
    ]

    for key in ESOTERIC_BINDUS:
        label = BINDU_LABELS.get(key, key.replace("_", " ").title())
        entry = bindus_data.get(key) or {}

        longitude = _fmt_degree(_get_longitude(entry))
        sign      = _fmt_sign(entry.get("sign"))
        nakshatra = _fmt_nakshatra(entry)
        lord      = _fmt_lord(entry)
        formula   = _fmt_bindu_formula(key, entry)

        lines.append(
            f"| {label} | {longitude} | {sign} | {nakshatra}"
            f" | {lord} | {formula} |"
        )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_sahams_section(chart_output: dict) -> str:
    """
    Render the full Tajik Sahams + Esoteric Bindus section for FORENSIC.md.

    Covers:
    - 40 Tajik Sahams with formula, longitude, sign, nakshatra, pada, lord.
    - 9 esoteric bindus (Bhrigu Bindu through Dehasphuta) with formula.

    Returns a markdown string with no narration verbs.
    Gracefully degrades to N/A when data is absent.
    """
    sahams_data: dict  = chart_output.get("sahams") or {}
    bindus_data: dict  = chart_output.get("esoteric_bindus") or {}

    parts: list[str] = []

    # 1. Tajik Sahams table
    parts.append(_render_sahams_table(sahams_data))
    parts.append("\n")

    # 2. Esoteric bindus table
    parts.append(_render_esoteric_bindus_table(bindus_data))

    return "\n".join(parts)
