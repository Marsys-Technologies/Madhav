"""
supplementary_renderer.py — Supplementary section renderer (F-14).

Covers:
  1. KP Cuspal Sub-lords — 12 cusps × sub-lord + nakshatra lord + sub-sub-lord
  2. Tajik Varshphal — year-lord + hadda lord
  3. Midpoints — Sun/Moon, ASC/MC, outer planet midpoints
  4. Eclipse proximity — nearest solar + lunar eclipses to birth date
  5. Nadi-amsa — D150 rishi per body from G44 table
  6. Argala / Virodha Argala matrix — 12×12 sign matrix
  7. Astronomical data at birth — JD, GAST, LST, lat/lon
  8. No-narration linter pass on full supplementary section

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

# Standard midpoint pairs
MIDPOINT_PAIRS: list[tuple[str, str]] = [
    ("sun_moon",     "Sun/Moon"),
    ("asc_mc",       "ASC/MC"),
    ("sun_saturn",   "Sun/Saturn"),
    ("moon_jupiter", "Moon/Jupiter"),
    ("mercury_venus","Mercury/Venus"),
    ("mars_saturn",  "Mars/Saturn"),
    ("jupiter_saturn","Jupiter/Saturn"),
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


def _fmt_float(value: Any, precision: int = 1) -> str:
    if value is None:
        return _NA
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return _NA


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_kp_cuspal(kp_data: dict) -> str:
    """
    Render KP cuspal sub-lords table for 12 cusps.

    Data path: kp_data[cusp_str] = {sub_lord, nakshatra_lord, sub_sub_lord}
    """
    lines: list[str] = [
        "### KP Cuspal Sub-Lords (12 Cusps)\n",
        "| Cusp | Sub-Lord | Nakshatra Lord | Sub-Sub-Lord |",
        "|------|----------|----------------|--------------|",
    ]

    for cusp in range(1, 13):
        cdata: dict = (
            kp_data.get(str(cusp))
            or kp_data.get(cusp)
            or {}
        )
        sub_lord     = _safe(cdata.get("sub_lord"))
        nak_lord     = _safe(cdata.get("nakshatra_lord"))
        sub_sub_lord = _safe(cdata.get("sub_sub_lord"))
        lines.append(f"| {cusp} | {sub_lord} | {nak_lord} | {sub_sub_lord} |")

    return "\n".join(lines) + "\n"


def _render_tajik(tajik_data: dict) -> str:
    """
    Render Tajik Varshphal data.

    Data path: tajik_data = {year_lord, hadda_lord}
    """
    year_lord  = _safe(tajik_data.get("year_lord"))
    hadda_lord = _safe(tajik_data.get("hadda_lord"))

    lines: list[str] = [
        "### Tajik Varshphal\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| Year Lord | {year_lord} |",
        f"| Hadda Lord | {hadda_lord} |",
    ]

    return "\n".join(lines) + "\n"


def _render_midpoints(midpoints_data: dict) -> str:
    """
    Render midpoints table.

    Data path: midpoints_data[pair_key] = {longitude, sign}
    """
    lines: list[str] = [
        "### Midpoints\n",
        "| Pair | Longitude° | Sign |",
        "|------|------------|------|",
    ]

    for pair_key, pair_display in MIDPOINT_PAIRS:
        pdata: dict = midpoints_data.get(pair_key) or {}
        lon  = _fmt_float(pdata.get("longitude"), precision=2)
        sign = _safe(pdata.get("sign"))
        lines.append(f"| {pair_display} | {lon} | {sign} |")

    return "\n".join(lines) + "\n"


def _render_eclipses(eclipse_data: dict) -> str:
    """
    Render eclipse proximity table.

    Data path: eclipse_data = {
        nearest_solar: {date, type, eclipse_id},
        nearest_lunar: {date, type, eclipse_id}
    }
    """
    solar: dict = eclipse_data.get("nearest_solar") or {}
    lunar: dict = eclipse_data.get("nearest_lunar") or {}

    lines: list[str] = [
        "### Eclipse Proximity to Birth Date\n",
        "| Type | Eclipse ID | Date | Eclipse Type |",
        "|------|-----------|------|--------------|",
        f"| Nearest Solar | {_safe(solar.get('eclipse_id'))} | {_safe(solar.get('date'))} | {_safe(solar.get('type'))} |",
        f"| Nearest Lunar | {_safe(lunar.get('eclipse_id'))} | {_safe(lunar.get('date'))} | {_safe(lunar.get('type'))} |",
    ]

    return "\n".join(lines) + "\n"


def _render_nadi_amsa(nadi_data: dict) -> str:
    """
    Render Nadi-amsa (D150) rishi per body.

    Data path: nadi_data[graha] = {rishi, division}
    """
    lines: list[str] = [
        "### Nadi-Amsa (D150 Rishi — G44 Table)\n",
        "| Body | Rishi | Division |",
        "|------|-------|----------|",
    ]

    for graha in GRAHAS:
        gdata: dict = nadi_data.get(graha) or {}
        rishi    = _safe(gdata.get("rishi"))
        division = _safe(gdata.get("division"))
        lines.append(f"| {GRAHA_DISPLAY[graha]} | {rishi} | {division} |")

    return "\n".join(lines) + "\n"


def _render_argala(argala_data: dict) -> str:
    """
    Render Argala / Virodha Argala matrix (12×12 signs).

    Data path: argala_data[sign_from][sign_to] = "argala" | "virodha" | "—"
    """
    sign_abbrs = [s[:3].capitalize() for s in SIGNS]
    header = " | ".join(sign_abbrs)
    sep    = " | ".join(["---"] * 12)

    lines: list[str] = [
        "### Argala / Virodha Argala Matrix (12×12)\n",
        f"| From\\To | {header} |",
        f"|---------|{sep}|",
    ]

    for sign_from in SIGNS:
        row_data: dict = argala_data.get(sign_from) or {}
        cells: list[str] = []
        for sign_to in SIGNS:
            val = row_data.get(sign_to)
            if val is None or str(val).strip() == "":
                cells.append(_NA)
            elif str(val).strip().lower() == "argala":
                cells.append("A")
            elif str(val).strip().lower() in ("virodha", "virodha argala"):
                cells.append("V")
            else:
                cells.append(_safe(val, _NA))
        lines.append(f"| {SIGN_DISPLAY[sign_from]} | {' | '.join(cells)} |")

    lines.append("\n**Key:** A = Argala, V = Virodha Argala, — = none\n")
    return "\n".join(lines) + "\n"


def _render_astronomical(astro_data: dict) -> str:
    """
    Render astronomical data at birth.

    Data path: astro_data = {
        julian_day, sidereal_time_gast, local_sidereal_time,
        birth_place, lat, lon
    }
    """
    jd    = _fmt_float(astro_data.get("julian_day"), precision=4)
    gast  = _safe(astro_data.get("sidereal_time_gast"))
    lst   = _safe(astro_data.get("local_sidereal_time"))
    place = _safe(astro_data.get("birth_place"))
    lat   = _fmt_float(astro_data.get("lat"), precision=4)
    lon   = _fmt_float(astro_data.get("lon"), precision=4)

    lines: list[str] = [
        "### Astronomical Data at Birth\n",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Julian Day Number | {jd} |",
        f"| Sidereal Time (GAST) | {gast} |",
        f"| Local Sidereal Time | {lst} |",
        f"| Birth Place | {place} |",
        f"| Latitude | {lat}° |",
        f"| Longitude | {lon}° |",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_supplementary_section(chart_output: dict) -> str:
    """
    Render the full Supplementary section for FORENSIC.md (F-14).

    Covers:
    1. KP Cuspal Sub-lords (12 cusps)
    2. Tajik Varshphal (year-lord + hadda lord)
    3. Midpoints (7 pairs)
    4. Eclipse proximity (nearest solar + lunar)
    5. Nadi-amsa D150 rishi (9 grahas)
    6. Argala/Virodha Argala matrix (12×12)
    7. Astronomical data at birth

    Expected chart_output keys:
      "kp_cuspal"         — dict keyed by cusp str/int
      "tajik_varshphal"   — dict with year_lord + hadda_lord
      "midpoints"         — dict keyed by pair key
      "eclipse_proximity" — dict with nearest_solar + nearest_lunar
      "nadi_amsa"         — dict keyed by graha
      "argala"            — dict keyed by sign_from → sign_to → value
      "astronomical"      — dict with JD + sidereal times + lat/lon

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder cells when data is absent.
    """
    from pipeline.render.base_renderer import lint_narration

    kp_data:      dict = chart_output.get("kp_cuspal") or {}
    tajik_data:   dict = chart_output.get("tajik_varshphal") or {}
    midpts_data:  dict = chart_output.get("midpoints") or {}
    eclipse_data: dict = chart_output.get("eclipse_proximity") or {}
    nadi_data:    dict = chart_output.get("nadi_amsa") or {}
    argala_data:  dict = chart_output.get("argala") or {}
    astro_data:   dict = chart_output.get("astronomical") or {}

    parts: list[str] = []

    parts.append(_render_kp_cuspal(kp_data))
    parts.append("\n")
    parts.append(_render_tajik(tajik_data))
    parts.append("\n")
    parts.append(_render_midpoints(midpts_data))
    parts.append("\n")
    parts.append(_render_eclipses(eclipse_data))
    parts.append("\n")
    parts.append(_render_nadi_amsa(nadi_data))
    parts.append("\n")
    parts.append(_render_argala(argala_data))
    parts.append("\n")
    parts.append(_render_astronomical(astro_data))

    full_text = "\n".join(parts)

    # Final no-narration linter pass on complete supplementary section
    lint_narration(full_text, section="supplementary")

    return full_text
