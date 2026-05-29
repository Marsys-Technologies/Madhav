"""
karakas_renderer.py — Chara Karakas + Natural Karakas + Karakamsa/Swamsa
+ Special Lagnas renderer for FORENSIC.md (F-06).

Covers:
  1. Chara Karakas (Jaimini 8-karaka scheme, ranked by longitude descending):
     AK, AmK, BK, MK, PK, GK, DK, SK
  2. Natural Karakas (fixed per classical — houses 1–12)
  3. Karakamsa (AK sign in D9) and Swamsa (D9 Lagna sign)
  4. Special Lagnas (10+): Hora, Ghati, Varnada, Sree, Pranapada, Indu,
     Bhava, Arudha, Shri, Bhrigu Bindu Lagna

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHARA_KARAKA_ORDER: list[str] = [
    "AK",   # Atmakaraka
    "AmK",  # Amatyakaraka
    "BK",   # Bhatrikaraka
    "MK",   # Matrikaraka
    "PK",   # Pitrikaraka
    "GK",   # Gnatikaraka
    "DK",   # Darakaraka
    "SK",   # Swakaraka (optional 8th; 7-karaka scheme omits)
]

CHARA_KARAKA_FULL_NAMES: dict[str, str] = {
    "AK":  "Atmakaraka",
    "AmK": "Amatyakaraka",
    "BK":  "Bhatrikaraka",
    "MK":  "Matrikaraka",
    "PK":  "Pitrikaraka",
    "GK":  "Gnatikaraka",
    "DK":  "Darakaraka",
    "SK":  "Swakaraka",
}

# Natural Karakas — classical fixed assignments (houses 1–12)
NATURAL_KARAKAS: dict[str, str] = {
    "1":  "Sun",
    "2":  "Jupiter",
    "3":  "Mars",
    "4":  "Moon",
    "5":  "Jupiter",
    "6":  "Mars/Saturn",
    "7":  "Venus",
    "8":  "Saturn",
    "9":  "Jupiter/Sun",
    "10": "Mercury/Saturn/Sun",
    "11": "Jupiter",
    "12": "Saturn",
}

SPECIAL_LAGNA_ORDER: list[str] = [
    "hora_lagna",
    "ghati_lagna",
    "varnada_lagna",
    "sree_lagna",
    "pranapada",
    "indu_lagna",
    "bhava_lagna",
    "arudha_lagna",
    "shri_lagna",
    "bhrigu_bindu_lagna",
]

SPECIAL_LAGNA_LABELS: dict[str, str] = {
    "hora_lagna":         "Hora Lagna",
    "ghati_lagna":        "Ghati Lagna",
    "varnada_lagna":      "Varnada Lagna",
    "sree_lagna":         "Sree Lagna",
    "pranapada":          "Pranapada",
    "indu_lagna":         "Indu Lagna",
    "bhava_lagna":        "Bhava Lagna",
    "arudha_lagna":       "Arudha Lagna (AL)",
    "shri_lagna":         "Shri Lagna",
    "bhrigu_bindu_lagna": "Bhrigu Bindu Lagna",
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


def _fmt_str(value: Any) -> str:
    if value is None:
        return _NA
    s = str(value).strip()
    return s if s else _NA


def _fmt_house(value: Any) -> str:
    if value is None:
        return _NA
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return _NA


def _get_longitude(entry: dict) -> Any:
    """Return longitude, preferring 'longitude' key, then 'degree'."""
    if entry.get("longitude") is not None:
        return entry["longitude"]
    return entry.get("degree")


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_chara_karakas_table(chara_karakas: dict) -> str:
    """Render Chara Karakas as a markdown table."""
    lines: list[str] = [
        "### Chara Karakas (Jaimini 8-Karaka Scheme)\n",
        "| Role | Name | Graha | Longitude | Sign |",
        "|------|------|-------|-----------|------|",
    ]

    for role in CHARA_KARAKA_ORDER:
        full_name = CHARA_KARAKA_FULL_NAMES.get(role, role)
        entry = chara_karakas.get(role) or {}

        graha     = _fmt_str(entry.get("graha"))
        longitude = _fmt_degree(_get_longitude(entry))
        sign      = _fmt_str(entry.get("sign"))

        lines.append(f"| {role} | {full_name} | {graha} | {longitude} | {sign} |")

    return "\n".join(lines) + "\n"


def _render_natural_karakas_table(natural_karakas: dict) -> str:
    """Render Natural Karakas (houses 1–12) as a markdown table.

    If chart_output provides a non-empty natural_karakas dict, that data
    is used.  Otherwise the canonical classical defaults are used.
    """
    source = natural_karakas if natural_karakas else NATURAL_KARAKAS

    lines: list[str] = [
        "### Natural Karakas\n",
        "| House | Natural Karaka |",
        "|-------|---------------|",
    ]

    for house_num in range(1, 13):
        key = str(house_num)
        karaka = source.get(key)
        if karaka is None:
            # Fall back to canonical default for this house
            karaka = NATURAL_KARAKAS.get(key, _NA)
        lines.append(f"| {house_num} | {_fmt_str(karaka)} |")

    return "\n".join(lines) + "\n"


def _render_karakamsa_swamsa_table(karakamsa: dict, swamsa: dict) -> str:
    """Render Karakamsa and Swamsa as a markdown table."""
    lines: list[str] = [
        "### Karakamsa and Swamsa\n",
        "| Point | Sign | Lord |",
        "|-------|------|------|",
    ]

    km_sign = _fmt_str(karakamsa.get("sign"))
    km_lord = _fmt_str(karakamsa.get("lord"))
    lines.append(f"| Karakamsa (AK in D9) | {km_sign} | {km_lord} |")

    sw_sign = _fmt_str(swamsa.get("sign"))
    sw_lord = _fmt_str(swamsa.get("lord"))
    lines.append(f"| Swamsa (D9 Lagna) | {sw_sign} | {sw_lord} |")

    return "\n".join(lines) + "\n"


def _render_special_lagnas_table(special_lagnas: dict) -> str:
    """Render Special Lagnas as a markdown table."""
    lines: list[str] = [
        "### Special Lagnas\n",
        "| Lagna | Longitude | Sign | House | Lord |",
        "|-------|-----------|------|-------|------|",
    ]

    for key in SPECIAL_LAGNA_ORDER:
        label = SPECIAL_LAGNA_LABELS.get(key, key.replace("_", " ").title())
        entry = special_lagnas.get(key) or {}

        longitude = _fmt_degree(_get_longitude(entry))
        sign      = _fmt_str(entry.get("sign"))
        house     = _fmt_house(entry.get("house"))
        lord      = _fmt_str(entry.get("lord"))

        lines.append(f"| {label} | {longitude} | {sign} | {house} | {lord} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_karakas_section(chart_output: dict) -> str:
    """
    Render the full Karakas + Special Lagnas section for FORENSIC.md.

    Covers:
    - Chara Karakas (Jaimini 8-karaka scheme): AK through SK
    - Natural Karakas for houses 1–12 (classical fixed assignments)
    - Karakamsa (AK in D9) and Swamsa (D9 Lagna)
    - Special Lagnas (10): Hora, Ghati, Varnada, Sree, Pranapada,
      Indu, Bhava, Arudha, Shri, Bhrigu Bindu Lagna

    Returns a markdown string with no narration verbs.
    Gracefully degrades to N/A when data is absent.
    """
    chara_karakas:  dict = chart_output.get("chara_karakas") or {}
    natural_karakas: dict = chart_output.get("natural_karakas") or {}
    karakamsa:      dict = chart_output.get("karakamsa") or {}
    swamsa:         dict = chart_output.get("swamsa") or {}
    special_lagnas: dict = chart_output.get("special_lagnas") or {}

    parts: list[str] = []

    # 1. Chara Karakas
    parts.append(_render_chara_karakas_table(chara_karakas))
    parts.append("\n")

    # 2. Natural Karakas
    parts.append(_render_natural_karakas_table(natural_karakas))
    parts.append("\n")

    # 3. Karakamsa + Swamsa
    parts.append(_render_karakamsa_swamsa_table(karakamsa, swamsa))
    parts.append("\n")

    # 4. Special Lagnas
    parts.append(_render_special_lagnas_table(special_lagnas))

    return "\n".join(parts)
