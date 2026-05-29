"""
strengths_renderer.py — Ashtakavarga, Shadbala, Bhava Bala, Ishta/Kashta renderer (F-10).

Covers:
  1. Bhinnashtakavarga (BAV) — 8 contributors × 12 signs = 96 bindu cells
  2. Sarvashtakavarga (SAV) — total bindus per sign (12 values)
  3. Trikona Sodhana (Trikona reduction)
  4. Ekadhipathya Sodhana (Ekadhipathya reduction)
  5. Sodhita SAV — final values after both reductions
  6. Kakshya contributions — 8 kakshyas per graha
  7. Shadbala — 6 sub-balas + total + required + ratio for 9 grahas
  8. Ishta/Kashta Phala — per graha
  9. Bhava Bala — 3 sub-balas + total for 12 houses

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

# BAV contributors: 7 grahas + Lagna (no Rahu/Ketu in classical BAV)
BAV_CONTRIBUTORS: list[str] = [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna",
]

BAV_CONTRIBUTOR_DISPLAY: dict[str, str] = {
    "sun":     "Sun",
    "moon":    "Moon",
    "mars":    "Mars",
    "mercury": "Mercury",
    "jupiter": "Jupiter",
    "venus":   "Venus",
    "saturn":  "Saturn",
    "lagna":   "Lagna",
}

SIGNS: list[str] = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

SIGN_DISPLAY: dict[str, str] = {
    "aries":       "Aries",
    "taurus":      "Taurus",
    "gemini":      "Gemini",
    "cancer":      "Cancer",
    "leo":         "Leo",
    "virgo":       "Virgo",
    "libra":       "Libra",
    "scorpio":     "Scorpio",
    "sagittarius": "Sagittarius",
    "capricorn":   "Capricorn",
    "aquarius":    "Aquarius",
    "pisces":      "Pisces",
}

SIGN_ABBR: dict[str, str] = {
    "aries":       "Ari",
    "taurus":      "Tau",
    "gemini":      "Gem",
    "cancer":      "Can",
    "leo":         "Leo",
    "virgo":       "Vir",
    "libra":       "Lib",
    "scorpio":     "Sco",
    "sagittarius": "Sag",
    "capricorn":   "Cap",
    "aquarius":    "Aqu",
    "pisces":      "Pis",
}

# 6 Shadbala sub-components (keys in data dict)
SHADBALA_COMPONENTS: list[tuple[str, str]] = [
    ("sthana_bala",     "Sthana"),
    ("dig_bala",        "Dig"),
    ("kala_bala",       "Kala"),
    ("chesta_bala",     "Chesta"),
    ("naisargika_bala", "Naisargika"),
    ("drik_bala",       "Drik"),
]

# Bhava Bala sub-components
BHAVA_COMPONENTS: list[tuple[str, str]] = [
    ("bhavadhipati_bala",  "Bhavadhipati"),
    ("bhava_drishti_bala", "Drishti"),
    ("bhava_dig_bala",     "Dig"),
]

_NA = "—"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_int(value: Any) -> str:
    if value is None:
        return _NA
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return _NA


def _fmt_float(value: Any, precision: int = 1) -> str:
    if value is None:
        return _NA
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return _NA


def _fmt_ratio(value: Any) -> str:
    """Format ratio to 2 decimal places."""
    if value is None:
        return _NA
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return _NA


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_bav(ashtakavarga: dict) -> str:
    """
    Render Bhinnashtakavarga table — 8 contributors × 12 signs.

    Data path: ashtakavarga["bav"][contributor][sign] = int (0-8)
    """
    bav: dict = ashtakavarga.get("bav") or {}

    sign_header = " | ".join(SIGN_DISPLAY[s] for s in SIGNS)
    sep_cols    = " | ".join(["-----"] * 12)

    lines: list[str] = [
        "### Bhinnashtakavarga (BAV — 8 Contributors × 12 Signs)\n",
        f"| Contributor | {sign_header} |",
        f"|-------------|{sep_cols}|",
    ]

    for contrib in BAV_CONTRIBUTORS:
        row_data: dict = bav.get(contrib) or {}
        cells = [_fmt_int(row_data.get(sign)) for sign in SIGNS]
        row = " | ".join(cells)
        lines.append(f"| {BAV_CONTRIBUTOR_DISPLAY[contrib]} | {row} |")

    return "\n".join(lines) + "\n"


def _render_sav(ashtakavarga: dict) -> str:
    """
    Render Sarvashtakavarga and Sodhita SAV rows.

    Data paths:
      ashtakavarga["sav"][sign]            = int
      ashtakavarga["trikona_reduced"][sign] = int
      ashtakavarga["ekadhipathya_reduced"][sign] = int
      ashtakavarga["sodhita_sav"][sign]    = int
    """
    sav: dict             = ashtakavarga.get("sav") or {}
    trikona: dict         = ashtakavarga.get("trikona_reduced") or {}
    ekadhipathya: dict    = ashtakavarga.get("ekadhipathya_reduced") or {}
    sodhita: dict         = ashtakavarga.get("sodhita_sav") or {}

    sign_header = " | ".join(SIGN_ABBR[s] for s in SIGNS)
    sep_cols    = " | ".join(["---"] * 12)

    lines: list[str] = [
        "### Sarvashtakavarga (SAV)\n",
        f"| Row | {sign_header} |",
        f"|-----|{sep_cols}|",
    ]

    def _row(label: str, data: dict) -> str:
        cells = [_fmt_int(data.get(sign)) for sign in SIGNS]
        return f"| {label} | {' | '.join(cells)} |"

    lines.append(_row("SAV", sav))
    lines.append(_row("Trikona Reduced", trikona))
    lines.append(_row("Ekadhipathya Reduced", ekadhipathya))
    lines.append(_row("Sodhita SAV", sodhita))

    return "\n".join(lines) + "\n"


def _render_kakshya(ashtakavarga: dict) -> str:
    """
    Render Kakshya contributions table.

    Data path: ashtakavarga["kakshya"][graha][kakshya_contributor] = int (0 or 1)
    Kakshya contributors: same 8 as BAV (sun, moon, mars, mercury, jupiter, venus, saturn, lagna)
    """
    kakshya: dict = ashtakavarga.get("kakshya") or {}

    contrib_header = " | ".join(BAV_CONTRIBUTOR_DISPLAY[c] for c in BAV_CONTRIBUTORS)
    sep_cols       = " | ".join(["---"] * len(BAV_CONTRIBUTORS))

    lines: list[str] = [
        "### Kakshya Contributions (8 Kakshyas per Graha)\n",
        f"| Graha | {contrib_header} | Total |",
        f"|-------|{sep_cols}|-------|",
    ]

    for graha in GRAHAS:
        graha_data: dict = kakshya.get(graha) or {}
        cells: list[str] = []
        total = 0
        for contrib in BAV_CONTRIBUTORS:
            val = graha_data.get(contrib)
            int_val = 0
            if val is not None:
                try:
                    int_val = int(val)
                except (TypeError, ValueError):
                    int_val = 0
            cells.append(str(int_val))
            total += int_val
        row = " | ".join(cells)
        lines.append(f"| {GRAHA_DISPLAY[graha]} | {row} | {total} |")

    return "\n".join(lines) + "\n"


def _render_shadbala(shadbala_data: dict) -> str:
    """
    Render Shadbala table — 6 sub-balas + total + required + ratio for 9 grahas.

    Data path: shadbala_data[graha] = {
        sthana_bala, dig_bala, kala_bala, chesta_bala, naisargika_bala, drik_bala,
        total, required, ratio
    }
    """
    comp_header = " | ".join(display for _, display in SHADBALA_COMPONENTS)
    sep_main    = " | ".join(["-------"] * len(SHADBALA_COMPONENTS))

    lines: list[str] = [
        "### Shadbala (6 Sub-Balas for 9 Grahas)\n",
        f"| Graha | {comp_header} | Total (R) | Required | Ratio |",
        f"|-------|{sep_main}|-----------|----------|-------|",
    ]

    for graha in GRAHAS:
        gdata: dict = shadbala_data.get(graha) or {}
        sub_cells = [
            _fmt_float(gdata.get(key))
            for key, _ in SHADBALA_COMPONENTS
        ]
        total    = _fmt_float(gdata.get("total"))
        required = _fmt_float(gdata.get("required"))
        ratio    = _fmt_ratio(gdata.get("ratio"))
        row = " | ".join(sub_cells)
        lines.append(
            f"| {GRAHA_DISPLAY[graha]} | {row} | {total} | {required} | {ratio} |"
        )

    return "\n".join(lines) + "\n"


def _render_ishta_kashta(shadbala_data: dict) -> str:
    """
    Render Ishta/Kashta Phala table — benefic/malefic potential per graha.

    Data path: shadbala_data[graha] = {ishta_phala, kashta_phala}
    """
    lines: list[str] = [
        "### Ishta/Kashta Phala\n",
        "| Graha | Ishta Phala | Kashta Phala |",
        "|-------|-------------|--------------|",
    ]

    for graha in GRAHAS:
        gdata: dict = shadbala_data.get(graha) or {}
        ishta  = _fmt_float(gdata.get("ishta_phala"))
        kashta = _fmt_float(gdata.get("kashta_phala"))
        lines.append(f"| {GRAHA_DISPLAY[graha]} | {ishta} | {kashta} |")

    return "\n".join(lines) + "\n"


def _render_bhava_bala(bhava_bala_data: dict) -> str:
    """
    Render Bhava Bala table — 3 sub-balas + total for 12 houses.

    Data path: bhava_bala_data[house_str] = {
        bhavadhipati_bala, bhava_drishti_bala, bhava_dig_bala, total
    }
    Keys may be int or str (1 or "1").
    """
    comp_header = " | ".join(display for _, display in BHAVA_COMPONENTS)
    sep_cols    = " | ".join(["----------"] * len(BHAVA_COMPONENTS))

    lines: list[str] = [
        "### Bhava Bala (3 Sub-Balas for 12 Houses)\n",
        f"| House | {comp_header} | Total |",
        f"|-------|{sep_cols}|-------|",
    ]

    for h in range(1, 13):
        hdata: dict = (
            bhava_bala_data.get(str(h))
            or bhava_bala_data.get(h)
            or {}
        )
        sub_cells = [
            _fmt_float(hdata.get(key))
            for key, _ in BHAVA_COMPONENTS
        ]
        total = _fmt_float(hdata.get("total"))
        row   = " | ".join(sub_cells)
        lines.append(f"| {h} | {row} | {total} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_strengths_section(chart_output: dict) -> str:
    """
    Render the full Strengths section for FORENSIC.md (F-10).

    Covers:
    1. Bhinnashtakavarga (BAV) — 8 contributors × 12 signs
    2. Sarvashtakavarga (SAV) + Trikona/Ekadhipathya reductions + Sodhita SAV
    3. Kakshya contributions (8 kakshyas per graha)
    4. Shadbala (6 sub-balas + total + required + ratio for 9 grahas)
    5. Ishta/Kashta Phala (per graha)
    6. Bhava Bala (3 sub-balas + total for 12 houses)

    Expected chart_output keys:
      "ashtakavarga" — dict with sub-keys: bav, sav, trikona_reduced,
                       ekadhipathya_reduced, sodhita_sav, kakshya
      "shadbala"     — dict keyed by graha name
      "bhava_bala"   — dict keyed by house number (str or int)

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder cells when data is absent.
    """
    ashtakavarga: dict  = chart_output.get("ashtakavarga") or {}
    shadbala_data: dict = chart_output.get("shadbala") or {}
    bhava_bala_data: dict = chart_output.get("bhava_bala") or {}

    parts: list[str] = []

    # 1. BAV table
    parts.append(_render_bav(ashtakavarga))
    parts.append("\n")

    # 2. SAV + reductions
    parts.append(_render_sav(ashtakavarga))
    parts.append("\n")

    # 3. Kakshya
    parts.append(_render_kakshya(ashtakavarga))
    parts.append("\n")

    # 4. Shadbala
    parts.append(_render_shadbala(shadbala_data))
    parts.append("\n")

    # 5. Ishta/Kashta Phala
    parts.append(_render_ishta_kashta(shadbala_data))
    parts.append("\n")

    # 6. Bhava Bala
    parts.append(_render_bhava_bala(bhava_bala_data))

    return "\n".join(parts)
