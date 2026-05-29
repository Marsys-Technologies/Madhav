"""
planets_renderer.py — Per-graha H2 section renderer for FORENSIC.md (F-02).

Produces deterministic, tabular output for all 23 chart bodies.
No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Canonical body order (23 bodies)
# ---------------------------------------------------------------------------

BODIES: list[str] = [
    # 9 classical grahas
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
    # True/Mean node variants
    "rahu_true", "ketu_true", "rahu_mean", "ketu_mean",
    # Liliths
    "mean_lilith", "true_lilith",
    # Outer planets / asteroids
    "ceres", "pallas", "juno", "vesta", "chiron",
    "uranus", "neptune", "pluto", "sedna", "eris",
]

BODY_DISPLAY_NAMES: dict[str, str] = {
    "sun": "Sun",
    "moon": "Moon",
    "mars": "Mars",
    "mercury": "Mercury",
    "jupiter": "Jupiter",
    "venus": "Venus",
    "saturn": "Saturn",
    "rahu": "Rahu (North Node)",
    "ketu": "Ketu (South Node)",
    "rahu_true": "Rahu True Node",
    "ketu_true": "Ketu True Node",
    "rahu_mean": "Rahu Mean Node",
    "ketu_mean": "Ketu Mean Node",
    "mean_lilith": "Mean Lilith",
    "true_lilith": "True Lilith",
    "ceres": "Ceres",
    "pallas": "Pallas",
    "juno": "Juno",
    "vesta": "Vesta",
    "chiron": "Chiron",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",
    "sedna": "Sedna",
    "eris": "Eris",
}

# Only classical grahas carry dignity
_CLASSICAL_GRAHAS: set[str] = {
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_longitude(body_data: dict) -> str:
    """Format ecliptic longitude as 'Sign DD°MM''."""
    sign = body_data.get("sign")
    degree = body_data.get("degree")
    if sign is None or degree is None:
        return "N/A"
    deg_int = int(float(degree))
    minutes = round((float(degree) - deg_int) * 60)
    return f"{sign} {deg_int}°{minutes:02d}'"


def _fmt_nakshatra(body_data: dict) -> str:
    """Format nakshatra + pada."""
    nakshatra = body_data.get("nakshatra")
    pada = body_data.get("pada")
    if nakshatra is None:
        return "N/A"
    if pada is None:
        return str(nakshatra)
    return f"{nakshatra} Pada {pada}"


def _fmt_float(value, decimals: int = 3, suffix: str = "°") -> str:
    """Format a float value with fixed decimals and an optional suffix."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_retrograde(body_data: dict) -> str:
    retro = body_data.get("retrograde")
    if retro is None:
        return "N/A"
    return "Yes" if retro else "No"


def _fmt_dignity(body_data: dict) -> str:
    dignity = body_data.get("dignity")
    if dignity is None:
        return "N/A"
    # Title-case for display
    return str(dignity).replace("_", " ").title()


def _fmt_house(body_data: dict) -> str:
    house = body_data.get("house")
    if house is None:
        return "N/A"
    return str(house)


def _fmt_varga_table(body_data: dict) -> str:
    """Build the Varga Positions markdown table."""
    varga_positions = body_data.get("varga_positions")
    if not varga_positions:
        return (
            "**Varga Positions**\n\n"
            "| Varga | Sign | Lord |\n"
            "|-------|------|------|\n"
            "| D1 (Rashi) | N/A | N/A |\n"
            "| D9 (Navamsa) | N/A | N/A |\n"
            "| D10 (Dasamsa) | N/A | N/A |\n"
        )

    rows = [
        ("D1 (Rashi)", "D1"),
        ("D9 (Navamsa)", "D9"),
        ("D10 (Dasamsa)", "D10"),
    ]
    lines = [
        "**Varga Positions**\n\n"
        "| Varga | Sign | Lord |\n"
        "|-------|------|------|"
    ]
    for label, key in rows:
        entry = varga_positions.get(key) or {}
        sign = entry.get("sign", "N/A")
        lord = entry.get("lord", "N/A")
        lines.append(f"| {label} | {sign} | {lord} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Per-body formatter
# ---------------------------------------------------------------------------

def _format_body(body_data: dict) -> str:
    """
    Format one chart body as a markdown H2 block with a data table
    and a Varga Positions sub-table.

    Returns a string that contains no narration verbs.
    """
    body_id = body_data.get("id", "unknown")
    display_name = BODY_DISPLAY_NAMES.get(body_id, body_id.replace("_", " ").title())
    is_classical = body_id in _CLASSICAL_GRAHAS

    longitude_str = _fmt_longitude(body_data)
    nakshatra_str = _fmt_nakshatra(body_data)
    latitude_str = _fmt_float(body_data.get("latitude"), suffix="°")
    speed_str = _fmt_float(body_data.get("speed"), suffix="°/day")
    retrograde_str = _fmt_retrograde(body_data)
    house_str = _fmt_house(body_data)
    helio_str = _fmt_float(body_data.get("heliocentric_longitude"), suffix="°")
    decl_str = _fmt_float(body_data.get("declination"), suffix="°")
    ra_str = _fmt_float(body_data.get("right_ascension"), suffix="°")

    # Build main data table rows
    rows = [
        ("Longitude", longitude_str),
        ("Nakshatra", nakshatra_str),
        ("Latitude", latitude_str),
        ("Speed", speed_str),
        ("Retrograde", retrograde_str),
    ]
    if is_classical:
        rows.append(("Dignity", _fmt_dignity(body_data)))
    rows += [
        ("House", house_str),
        ("Heliocentric Lon", helio_str),
        ("Declination", decl_str),
        ("Right Ascension", ra_str),
    ]

    table_lines = [
        "| Field | Value |",
        "|-------|-------|",
    ]
    for field, value in rows:
        table_lines.append(f"| {field} | {value} |")

    main_table = "\n".join(table_lines)
    varga_table = _fmt_varga_table(body_data)

    return (
        f"## {display_name} {{#{body_id}}}\n\n"
        f"{main_table}\n\n"
        f"{varga_table}\n"
    )


# ---------------------------------------------------------------------------
# Section renderer
# ---------------------------------------------------------------------------

def render_planets_section(chart_output: dict) -> str:
    """
    Render the full per-graha planetary section for FORENSIC.md.

    Iterates over all 23 canonical bodies in order. If a body is absent
    from chart_output['planets'], emits a stub block with N/A for all fields.

    Returns a markdown string. Guaranteed to contain no narration verbs.
    """
    planets_list: list[dict] = chart_output.get("planets") or []

    # Index planet list by body ID for O(1) lookup
    planets_by_id: dict[str, dict] = {}
    for p in planets_list:
        pid = p.get("id")
        if pid:
            planets_by_id[pid] = p

    parts: list[str] = []
    for body_id in BODIES:
        body_data = planets_by_id.get(body_id) or {"id": body_id}
        parts.append(_format_body(body_data))

    return "\n".join(parts)
