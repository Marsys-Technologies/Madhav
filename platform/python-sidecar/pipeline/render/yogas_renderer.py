"""
yogas_renderer.py — Yogas register + Doshas register renderer for FORENSIC.md (F-07).

Covers:
  1. Active Yogas table — sorted by tightness_score descending
  2. Near-Miss Yogas table — active=False but tightness_score > 0.5
  3. Summary count line (total evaluated, active, near-miss)
  4. Doshas Register table — all 15+ dosha types with severity + cancellations

Yoga categories represented:
  - Pancha Mahapurusha (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
  - Gajakesari
  - Raj Yogas (generic)
  - Dhan Yogas (generic)
  - Vipareeta Raja (3 types: Harsha, Sarala, Vimala)
  - Neechabhanga
  - Sunafa / Anapha / Durdhura
  - Kala Sarpa (12 variants)

Dosha names covered:
  Mangal (Manglik), Kaal Sarpa, Pitru, Matri, Naga, Sarpa,
  Guru Chandal, Grahan, Daridra, Shakata, Vish, Punarphoo,
  Angarak, Kemadrum, and additional standard types.

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NEAR_MISS_THRESHOLD: float = 0.5

# Canonical yoga category labels (used in documentation / summary only)
YOGA_CATEGORIES: list[str] = [
    "Pancha Mahapurusha",
    "Gajakesari",
    "Raj Yoga",
    "Dhan Yoga",
    "Vipareeta Raja Yoga",
    "Neechabhanga",
    "Sunafa / Anapha / Durdhura",
    "Kala Sarpa",
]

# Canonical dosha names expected in output
CANONICAL_DOSHA_NAMES: list[str] = [
    "Mangal Dosha",
    "Kaal Sarpa Dosha",
    "Pitru Dosha",
    "Matri Dosha",
    "Naga Dosha",
    "Sarpa Dosha",
    "Guru Chandal Dosha",
    "Grahan Dosha",
    "Daridra Dosha",
    "Shakata Dosha",
    "Vish Dosha",
    "Punarphoo Dosha",
    "Angarak Dosha",
    "Kemadrum Dosha",
]

SEVERITY_VALUES: frozenset[str] = frozenset({"mild", "moderate", "severe", "N/A"})

_NA = "N/A"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_str(value: Any) -> str:
    if value is None:
        return _NA
    s = str(value).strip()
    return s if s else _NA


def _fmt_float(value: Any, precision: int = 2) -> str:
    if value is None:
        return _NA
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return _NA


def _fmt_bool_yn(value: Any) -> str:
    """Return 'Yes' / 'No' for boolean; _NA for None."""
    if value is None:
        return _NA
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if str(value).lower() in ("true", "yes", "1"):
        return "Yes"
    if str(value).lower() in ("false", "no", "0"):
        return "No"
    return _NA


def _fmt_list(value: Any) -> str:
    """Join a list of strings with ', '; fall back to _NA."""
    if value is None:
        return _NA
    if isinstance(value, list):
        parts = [str(v).strip() for v in value if v is not None]
        return ", ".join(parts) if parts else _NA
    return _fmt_str(value)


def _fmt_severity(value: Any) -> str:
    if value is None:
        return _NA
    s = str(value).strip().lower()
    mapping = {
        "mild":     "Mild",
        "moderate": "Moderate",
        "severe":   "Severe",
        "n/a":      "N/A",
    }
    return mapping.get(s, _fmt_str(value).title())


# ---------------------------------------------------------------------------
# Sub-renderers
# ---------------------------------------------------------------------------

def _render_summary_line(yogas: list[dict]) -> str:
    """Render the count summary line for yogas."""
    total = len(yogas)
    active_count = sum(1 for y in yogas if y.get("active") is True)
    near_miss_count = sum(
        1 for y in yogas
        if y.get("active") is not True
        and float(y.get("tightness_score", 0) or 0) > NEAR_MISS_THRESHOLD
    )
    return (
        f"Total yoga predicates evaluated: {total} | "
        f"Active: {active_count} | "
        f"Near-miss (score > {NEAR_MISS_THRESHOLD}): {near_miss_count}"
    )


def _render_active_yogas_table(yogas: list[dict]) -> str:
    """Render the Active Yogas markdown table, sorted by tightness_score descending."""
    active = [y for y in yogas if y.get("active") is True]
    active_sorted = sorted(
        active,
        key=lambda y: float(y.get("tightness_score", 0) or 0),
        reverse=True,
    )

    lines: list[str] = [
        "### Active Yogas\n",
        "| Yoga | Constituent | Tightness | Citation |",
        "|------|-------------|-----------|----------|",
    ]

    if not active_sorted:
        lines.append("| — | — | — | — |")
    else:
        for y in active_sorted:
            name        = _fmt_str(y.get("name"))
            constituent = _fmt_list(y.get("constituent"))
            tightness   = _fmt_float(y.get("tightness_score"))
            citation    = _fmt_str(y.get("classical_citation"))
            lines.append(f"| {name} | {constituent} | {tightness} | {citation} |")

    return "\n".join(lines) + "\n"


def _render_near_miss_yogas_table(yogas: list[dict]) -> str:
    """Render Near-Miss Yogas (active=False, score > NEAR_MISS_THRESHOLD)."""
    near_miss = [
        y for y in yogas
        if y.get("active") is not True
        and float(y.get("tightness_score", 0) or 0) > NEAR_MISS_THRESHOLD
    ]
    near_miss_sorted = sorted(
        near_miss,
        key=lambda y: float(y.get("tightness_score", 0) or 0),
        reverse=True,
    )

    lines: list[str] = [
        "### Near-Miss Yogas (Score > 0.5, Not Active)\n",
        "| Yoga | Constituent | Tightness | Citation |",
        "|------|-------------|-----------|----------|",
    ]

    if not near_miss_sorted:
        lines.append("| — | — | — | — |")
    else:
        for y in near_miss_sorted:
            name        = _fmt_str(y.get("name"))
            constituent = _fmt_list(y.get("constituent"))
            tightness   = _fmt_float(y.get("tightness_score"))
            citation    = _fmt_str(y.get("classical_citation"))
            lines.append(f"| {name} | {constituent} | {tightness} | {citation} |")

    return "\n".join(lines) + "\n"


def _render_doshas_table(doshas: list[dict]) -> str:
    """Render the Doshas Register as a markdown table."""
    lines: list[str] = [
        "### Doshas Register\n",
        "| Dosha | Active | Constituent | Severity | Cancellations Applicable |",
        "|-------|--------|-------------|----------|--------------------------|",
    ]

    if not doshas:
        lines.append("| — | — | — | — | — |")
    else:
        for d in doshas:
            name          = _fmt_str(d.get("name"))
            active        = _fmt_bool_yn(d.get("active"))
            constituent   = _fmt_list(d.get("constituent"))
            severity      = _fmt_severity(d.get("severity"))
            cancellations = _fmt_list(d.get("cancellation_rules_applicable"))
            lines.append(
                f"| {name} | {active} | {constituent} | {severity} | {cancellations} |"
            )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_yogas_section(chart_output: dict) -> str:
    """
    Render the full Yogas + Doshas section for FORENSIC.md.

    Covers:
    - Summary count line: total evaluated | active | near-miss
    - Active Yogas table (sorted by tightness_score descending)
    - Near-Miss Yogas table (active=False but score > 0.5)
    - Doshas Register table

    Expected chart_output keys:
      "yogas"  — list of yoga dicts (name, active, constituent,
                  tightness_score, classical_citation)
      "doshas" — list of dosha dicts (name, active, constituent,
                  severity, cancellation_rules_applicable)

    Returns a markdown string with no narration verbs.
    Gracefully degrades to placeholder rows when data is absent.
    """
    yogas:  list[dict] = chart_output.get("yogas") or []
    doshas: list[dict] = chart_output.get("doshas") or []

    parts: list[str] = []

    # 1. Summary line
    parts.append(_render_summary_line(yogas))
    parts.append("\n")

    # 2. Active yogas table
    parts.append(_render_active_yogas_table(yogas))
    parts.append("\n")

    # 3. Near-miss yogas table
    parts.append(_render_near_miss_yogas_table(yogas))
    parts.append("\n")

    # 4. Doshas register
    parts.append(_render_doshas_table(doshas))

    return "\n".join(parts)
