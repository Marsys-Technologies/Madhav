"""
aspects_renderer.py — Aspect matrices renderer for FORENSIC.md (F-09).

Covers:
  1. Parashari Aspect Matrix (9 grahas × 12 houses) — aspect_type, strength, orb per cell
  2. Jaimini Rasi-Drishti Matrix (12 signs × 12 signs) — Yes/No + normal/special
  3. Tajik Aspects (5 types) — within-orb pairs with applying/separating
  4. Mutual Aspects table — which grahas mutually aspect each other
  5. Graha-to-Lagna Aspects — which grahas aspect the lagna

Parashari aspect rules:
  - All grahas:   7th house — Full strength
  - Mars:         4th, 8th  — Full strength (special)
  - Jupiter:      5th, 9th  — Full strength (special)
  - Saturn:       3rd, 10th — Three-quarter strength (special)
  - Rahu/Ketu:    5th, 9th  — Full strength (special, per classical tradition)

Jaimini Rasi-Drishti rules:
  - Fixed signs (Taurus, Leo, Scorpio, Aquarius):
      aspect all Moveable signs EXCEPT the adjacent one
  - Dual signs (Gemini, Virgo, Sagittarius, Pisces):
      aspect all Fixed signs
  - Moveable signs (Aries, Cancer, Libra, Capricorn):
      aspect all Dual signs EXCEPT the adjacent one

Tajik aspect types and orbs:
  - Trine (120°)        — major, 8° orb
  - Square (90°)        — major, 8° orb
  - Opposition (180°)   — major, 8° orb
  - Sextile (60°)       — major, 8° orb
  - Semi-sextile (30°)  — minor, 4° orb

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

SIGN_INDEX: dict[str, int] = {s: i for i, s in enumerate(SIGNS)}

MOVEABLE_SIGNS: frozenset[str] = frozenset({"aries", "cancer", "libra", "capricorn"})
FIXED_SIGNS:    frozenset[str] = frozenset({"taurus", "leo", "scorpio", "aquarius"})
DUAL_SIGNS:     frozenset[str] = frozenset({"gemini", "virgo", "sagittarius", "pisces"})

# Parashari special aspects by graha (in addition to universal 7th)
# Values: (house_offset, strength)
SPECIAL_ASPECTS: dict[str, list[tuple[int, str]]] = {
    "mars":    [(4, "full"), (8, "full")],
    "jupiter": [(5, "full"), (9, "full")],
    "saturn":  [(3, "three-quarter"), (10, "three-quarter")],
    "rahu":    [(5, "full"), (9, "full")],
    "ketu":    [(5, "full"), (9, "full")],
}

TAJIK_ASPECTS: list[dict] = [
    {"aspect_type": "trine",       "angle": 120.0, "orb_limit": 8.0, "minor": False},
    {"aspect_type": "square",      "angle":  90.0, "orb_limit": 8.0, "minor": False},
    {"aspect_type": "opposition",  "angle": 180.0, "orb_limit": 8.0, "minor": False},
    {"aspect_type": "sextile",     "angle":  60.0, "orb_limit": 8.0, "minor": False},
    {"aspect_type": "semi-sextile","angle":  30.0, "orb_limit": 4.0, "minor": True},
]

_NA = "—"
_DASH = "—"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_str(value: Any) -> str:
    if value is None:
        return _NA
    s = str(value).strip()
    return s if s else _NA


def _fmt_float(value: Any, precision: int = 1) -> str:
    if value is None:
        return _NA
    try:
        return f"{float(value):.{precision}f}°"
    except (TypeError, ValueError):
        return _NA


def _fmt_bool_yn(value: Any) -> str:
    if value is None:
        return _NA
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if str(value).lower() in ("true", "yes", "1"):
        return "Yes"
    if str(value).lower() in ("false", "no", "0"):
        return "No"
    return _NA


# ---------------------------------------------------------------------------
# Jaimini Rasi-Drishti computation (static rules — no chart data needed)
# ---------------------------------------------------------------------------

def _compute_jaimini_matrix() -> dict[str, dict[str, bool]]:
    """
    Compute the static Jaimini rasi-drishti matrix from sign-type rules.

    Returns dict[from_sign][to_sign] = bool.
    """
    matrix: dict[str, dict[str, bool]] = {}

    for from_sign in SIGNS:
        row: dict[str, bool] = {}

        if from_sign in MOVEABLE_SIGNS:
            # Moveable aspects all Dual signs except the adjacent one
            from_idx = SIGN_INDEX[from_sign]
            for to_sign in SIGNS:
                if to_sign in DUAL_SIGNS:
                    to_idx = SIGN_INDEX[to_sign]
                    adjacent = abs(from_idx - to_idx) in (1, 11)
                    row[to_sign] = not adjacent
                else:
                    row[to_sign] = False

        elif from_sign in FIXED_SIGNS:
            # Fixed aspects all Moveable signs except the adjacent one
            from_idx = SIGN_INDEX[from_sign]
            for to_sign in SIGNS:
                if to_sign in MOVEABLE_SIGNS:
                    to_idx = SIGN_INDEX[to_sign]
                    adjacent = abs(from_idx - to_idx) in (1, 11)
                    row[to_sign] = not adjacent
                else:
                    row[to_sign] = False

        else:
            # Dual aspects all Fixed signs
            for to_sign in SIGNS:
                row[to_sign] = to_sign in FIXED_SIGNS

        matrix[from_sign] = row

    return matrix


_JAIMINI_MATRIX: dict[str, dict[str, bool]] = _compute_jaimini_matrix()


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_parashari_matrix(aspects_data: dict) -> str:
    """
    Render the Parashari Aspect Matrix as a 9×12 markdown table.

    Data path: aspects_data["parashari"][graha][house_str]
      = {"aspect_type": str, "strength": str, "orb": float}

    Falls back to computed static aspect structure (house position relative)
    when chart data provides house occupancy for each graha.
    """
    parashari: dict = aspects_data.get("parashari") or {}

    header_cols = " | ".join(f"H{h}" for h in range(1, 13))
    sep_cols    = " | ".join(["----"] * 12)

    lines: list[str] = [
        "### Parashari Aspect Matrix\n",
        f"| Graha | {header_cols} |",
        f"|-------|{sep_cols}|",
    ]

    for graha in GRAHAS:
        graha_data: dict = parashari.get(graha) or {}
        cells: list[str] = []

        for h in range(1, 13):
            h_str = str(h)
            cell_data = graha_data.get(h_str) or graha_data.get(h)
            if cell_data:
                strength = _fmt_str(cell_data.get("strength"))
                orb_val  = cell_data.get("orb")
                if orb_val is not None:
                    try:
                        orb_str = f"{float(orb_val):.1f}°"
                    except (TypeError, ValueError):
                        orb_str = ""
                    cells.append(f"{strength.title()} ({orb_str})")
                else:
                    cells.append(strength.title())
            else:
                cells.append(_DASH)

        row = " | ".join(cells)
        cells_str = f"| {GRAHA_DISPLAY[graha]} | {row} |"
        lines.append(cells_str)

    return "\n".join(lines) + "\n"


def _render_jaimini_matrix(aspects_data: dict) -> str:
    """
    Render the Jaimini Rasi-Drishti Matrix as a 12×12 markdown table.

    Data path: aspects_data["jaimini_rasi_drishti"][from_sign][to_sign] = bool
    Falls back to statically computed matrix when data absent.
    """
    supplied: dict = aspects_data.get("jaimini_rasi_drishti") or {}
    # Merge supplied over static defaults
    matrix: dict[str, dict[str, bool]] = {}
    for s in SIGNS:
        static_row = _JAIMINI_MATRIX.get(s, {})
        supplied_row = supplied.get(s) or {}
        merged: dict[str, bool] = {}
        for t in SIGNS:
            if t in supplied_row:
                merged[t] = bool(supplied_row[t])
            else:
                merged[t] = static_row.get(t, False)
        matrix[s] = merged

    sign_header = " | ".join(SIGN_DISPLAY[s][:3] for s in SIGNS)
    sep_cols    = " | ".join(["---"] * 12)

    lines: list[str] = [
        "### Jaimini Rasi-Drishti Matrix\n",
        f"| Sign | {sign_header} |",
        f"|------|{sep_cols}|",
    ]

    for from_sign in SIGNS:
        row_data = matrix[from_sign]
        cells = []
        for to_sign in SIGNS:
            val = row_data.get(to_sign, False)
            cells.append("Yes" if val else _DASH)
        row = " | ".join(cells)
        lines.append(f"| {SIGN_DISPLAY[from_sign]} | {row} |")

    return "\n".join(lines) + "\n"


def _render_tajik_aspects(aspects_data: dict) -> str:
    """
    Render Tajik Aspects within orb as a markdown table.

    Data path: aspects_data["tajik"]
      = list of {body1, body2, aspect_type, orb, applying}
    """
    tajik_list: list[dict] = aspects_data.get("tajik") or []

    lines: list[str] = [
        "### Tajik Aspects (Within Orb)\n",
        "| Body 1 | Body 2 | Aspect | Orb | Applying |",
        "|--------|--------|--------|-----|----------|",
    ]

    if not tajik_list:
        lines.append(f"| {_DASH} | {_DASH} | {_DASH} | {_DASH} | {_DASH} |")
    else:
        for entry in tajik_list:
            body1       = _fmt_str(entry.get("body1"))
            body2       = _fmt_str(entry.get("body2"))
            aspect_type = _fmt_str(entry.get("aspect_type"))
            orb         = _fmt_float(entry.get("orb"))
            applying    = _fmt_bool_yn(entry.get("applying"))
            lines.append(
                f"| {body1.title()} | {body2.title()} "
                f"| {aspect_type.title()} | {orb} | {applying} |"
            )

    return "\n".join(lines) + "\n"


def _render_mutual_aspects(aspects_data: dict) -> str:
    """
    Render Mutual Aspects table.

    Data path: aspects_data["mutual"]
      = list of {body1, body2, aspect_type}
    """
    mutual_list: list[dict] = aspects_data.get("mutual") or []

    lines: list[str] = [
        "### Mutual Aspects\n",
        "| Body 1 | Body 2 | Type |",
        "|--------|--------|------|",
    ]

    if not mutual_list:
        lines.append(f"| {_DASH} | {_DASH} | {_DASH} |")
    else:
        for entry in mutual_list:
            body1       = _fmt_str(entry.get("body1"))
            body2       = _fmt_str(entry.get("body2"))
            aspect_type = _fmt_str(entry.get("aspect_type"))
            lines.append(
                f"| {body1.title()} | {body2.title()} | {aspect_type.title()} |"
            )

    return "\n".join(lines) + "\n"


def _render_lagna_aspects(aspects_data: dict) -> str:
    """
    Render Graha-to-Lagna Aspects table.

    Data path: aspects_data["lagna_aspects"]
      = list of {body, aspect_type, orb}
    """
    lagna_list: list[dict] = aspects_data.get("lagna_aspects") or []

    lines: list[str] = [
        "### Graha-to-Lagna Aspects\n",
        "| Graha | Aspect Type | Orb |",
        "|-------|-------------|-----|",
    ]

    if not lagna_list:
        lines.append(f"| {_DASH} | {_DASH} | {_DASH} |")
    else:
        for entry in lagna_list:
            body        = _fmt_str(entry.get("body"))
            aspect_type = _fmt_str(entry.get("aspect_type"))
            orb         = _fmt_float(entry.get("orb"))
            lines.append(
                f"| {body.title()} | {aspect_type.title()} | {orb} |"
            )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_aspects_section(chart_output: dict) -> str:
    """
    Render the full Aspects section for FORENSIC.md (F-09).

    Covers:
    1. Parashari Aspect Matrix (9 grahas × 12 houses)
    2. Jaimini Rasi-Drishti Matrix (12 signs × 12 signs)
    3. Tajik Aspects (within-orb pairs with applying/separating)
    4. Mutual Aspects (graha pairs that mutually aspect)
    5. Graha-to-Lagna Aspects

    Expected chart_output key: "aspects" (dict with sub-keys
    parashari, jaimini_rasi_drishti, tajik, mutual, lagna_aspects).

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder rows when data is absent.
    """
    aspects_data: dict = chart_output.get("aspects") or {}

    parts: list[str] = []

    # 1. Parashari matrix
    parts.append(_render_parashari_matrix(aspects_data))
    parts.append("\n")

    # 2. Jaimini rasi-drishti matrix
    parts.append(_render_jaimini_matrix(aspects_data))
    parts.append("\n")

    # 3. Tajik aspects
    parts.append(_render_tajik_aspects(aspects_data))
    parts.append("\n")

    # 4. Mutual aspects
    parts.append(_render_mutual_aspects(aspects_data))
    parts.append("\n")

    # 5. Graha-to-lagna aspects
    parts.append(_render_lagna_aspects(aspects_data))

    return "\n".join(parts)
