"""
vargas_renderer.py — Divisional charts (Vargas) renderer (F-12).

Covers:
  1. 30+ varga divisions: D1–D60 (Parashari) + D108, D150, D2700 (Nadi)
  2. Per varga: lagna sign+lord, then 9 grahas (sign+lord+dignity+vargottama)
  3. D9 and D10 always fully expanded
  4. D108 (Nadi): rishi column added
  5. D9 Two-Pass Verification subsection

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

# All varga divisions in order
PARASHARI_VARGAS: list[str] = [
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]

NADI_VARGAS: list[str] = ["D108", "D150", "D2700"]

ALL_VARGAS: list[str] = PARASHARI_VARGAS + NADI_VARGAS

# Vargas that receive the Nadi rishi column
NADI_RISHI_VARGAS: set[str] = {"D108", "D150", "D2700"}

# Varga descriptions (for table headings)
VARGA_DESC: dict[str, str] = {
    "D1":    "Rasi — natal chart",
    "D2":    "Hora — wealth",
    "D3":    "Drekkana — siblings",
    "D4":    "Chaturthamsha — property",
    "D5":    "Panchamsha — merit",
    "D6":    "Shashthamsha — health",
    "D7":    "Saptamsha — children",
    "D8":    "Ashtamsha — obstacles",
    "D9":    "Navamsha — spouse/dharma",
    "D10":   "Dasamsha — career",
    "D11":   "Ekadashamsha — gain",
    "D12":   "Dvadashamsha — parents",
    "D16":   "Shodashamsha — vehicles",
    "D20":   "Vimshamsha — spiritual",
    "D24":   "Chaturvimshamsha — learning",
    "D27":   "Bhamsha — strength",
    "D30":   "Trimshamsha — evil/misfortune",
    "D40":   "Khavedamsha — auspiciousness",
    "D45":   "Akshavedamsha — general",
    "D60":   "Shashtiamsha — karma",
    "D108":  "Nadi Ashtamamsha — Rishi",
    "D150":  "Nadi — Nadiamsha",
    "D2700": "Nadi Sookshma — ultra-fine",
}

_NA = "—"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe(value: Any, fallback: str = _NA) -> str:
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback


def _varg_flag(value: Any) -> str:
    """Render vargottama flag as ✓ / ✗ / —."""
    if value is None:
        return _NA
    if isinstance(value, bool):
        return "✓" if value else "✗"
    s = str(value).strip().lower()
    if s in ("true", "yes", "1"):
        return "✓"
    if s in ("false", "no", "0"):
        return "✗"
    return _NA


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_single_varga(varga_key: str, varga_data: dict, is_nadi: bool = False) -> str:
    """
    Render one varga table.

    varga_data keys:
      "lagna": {sign, lord}
      graha:   {sign, lord, dignity, vargottama[, rishi]}
    """
    desc = VARGA_DESC.get(varga_key, varga_key)

    if is_nadi:
        lines: list[str] = [
            f"#### {varga_key} — {desc}\n",
            "| Body | Sign | Lord | Dignity | Vargottama | Rishi |",
            "|------|------|------|---------|------------|-------|",
        ]
    else:
        lines = [
            f"#### {varga_key} — {desc}\n",
            "| Body | Sign | Lord | Dignity | Vargottama |",
            "|------|------|------|---------|------------|",
        ]

    # Lagna row
    lagna: dict = varga_data.get("lagna") or {}
    lagna_sign = _safe(lagna.get("sign"))
    lagna_lord = _safe(lagna.get("lord"))
    if is_nadi:
        lines.append(f"| Lagna | {lagna_sign} | {lagna_lord} | — | — | — |")
    else:
        lines.append(f"| Lagna | {lagna_sign} | {lagna_lord} | — | — |")

    # Graha rows
    for graha in GRAHAS:
        gdata: dict = varga_data.get(graha) or {}
        sign     = _safe(gdata.get("sign"))
        lord     = _safe(gdata.get("lord"))
        dignity  = _safe(gdata.get("dignity"))
        vargott  = _varg_flag(gdata.get("vargottama"))
        if is_nadi:
            rishi = _safe(gdata.get("rishi"))
            lines.append(
                f"| {GRAHA_DISPLAY[graha]} | {sign} | {lord} | {dignity} | {vargott} | {rishi} |"
            )
        else:
            lines.append(
                f"| {GRAHA_DISPLAY[graha]} | {sign} | {lord} | {dignity} | {vargott} |"
            )

    return "\n".join(lines) + "\n"


def _render_d9_verification(d9_verification: dict) -> str:
    """
    Render D9 two-pass verification subsection.

    d9_verification keys: match (bool), discrepancies (list of str)
    """
    match: bool = bool(d9_verification.get("match", False))
    discrepancies: list = d9_verification.get("discrepancies") or []

    status = "PASS — positions agree" if match else "FAIL — discrepancies found"

    lines: list[str] = [
        "## D9 Two-Pass Verification\n",
        f"**Status:** {status}\n",
        "| Field | Detail |",
        "|-------|--------|",
        f"| Match | {'✓' if match else '✗'} |",
        f"| Discrepancy count | {len(discrepancies)} |",
    ]

    if discrepancies:
        lines.append("\n**Discrepancies:**\n")
        for disc in discrepancies:
            lines.append(f"- {disc}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_vargas_section(chart_output: dict) -> str:
    """
    Render the full Vargas section for FORENSIC.md (F-12).

    Covers:
    1. All 23 varga tables (D1–D60 Parashari + D108/D150/D2700 Nadi)
    2. D9 and D10 always fully expanded
    3. D108 includes rishi column
    4. D9 Two-Pass Verification subsection

    Expected chart_output keys:
      "vargas"           — dict keyed by varga code (D1, D2 … D2700)
      "d9_verification"  — dict with match + discrepancies

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder cells when data is absent.
    """
    vargas_data: dict        = chart_output.get("vargas") or {}
    d9_verification: dict    = chart_output.get("d9_verification") or {}

    parts: list[str] = []

    # Parashari vargas
    parts.append("### Parashari Divisional Charts (D1–D60)\n\n")
    for varga_key in PARASHARI_VARGAS:
        vdata = vargas_data.get(varga_key) or {}
        parts.append(_render_single_varga(varga_key, vdata, is_nadi=False))
        parts.append("\n")

    # Nadi vargas (with rishi column)
    parts.append("### Nadi Divisional Charts (D108 / D150 / D2700)\n\n")
    for varga_key in NADI_VARGAS:
        vdata = vargas_data.get(varga_key) or {}
        parts.append(_render_single_varga(varga_key, vdata, is_nadi=True))
        parts.append("\n")

    # D9 two-pass verification
    parts.append(_render_d9_verification(d9_verification))

    return "\n".join(parts)
