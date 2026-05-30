"""
graha_aspects_writer.py — Per-graha next-exact-aspect lifetime computation.

Computes all dates 2026-2060 when transit grahas form exact aspects with
natal graha positions. Covers Parashari graha-drishti, classical 5-aspect
system, and Tajik aspects.

Native natal positions (Lahiri sidereal, pre-computed):
  Sun=314.5°, Moon=325.8°, Mars=198.3°, Mercury=298.7°, Jupiter=241.2°,
  Venus=292.1°, Saturn=207.4°, Rahu=89.4°, Ketu=269.4°

Algorithm:
  1. Define natal positions from FORENSIC_ASTROLOGICAL_DATA_v8_0 (Lahiri sidereal).
  2. For each (natal_graha, transit_graha, aspect_angle) triple:
     - Scan daily from start_date to end_date using swisseph
     - Detect when |transit_lon - (natal_lon + aspect_angle)| mod 360 ≤ 1.0°
     - Find local minimum orb within each crossing window (exact date)
  3. Insert with ON CONFLICT DO NOTHING (idempotent).

Aspect systems:
  - Parashari: graha-drishti angles per transit graha (7th for all;
    Mars+4th+8th; Jupiter+5th+9th; Saturn+3rd+10th; Rahu/Ketu+5th+9th)
  - Classical: {0°, 180°} for all 9×9 (critical aspects only for performance)
  - Tajik: {0°, 60°, 120°} with applying/separating flag

Stream C — A21 [BUILD-ORCH-STREAM-C-A21-S1]
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Optional

# ── Natal positions (Lahiri sidereal) from FORENSIC_ASTROLOGICAL_DATA_v8_0 ──

NATAL_POSITIONS: dict[str, float] = {
    "sun":     314.5,
    "moon":    325.8,
    "mars":    198.3,
    "mercury": 298.7,
    "jupiter": 241.2,
    "venus":   292.1,
    "saturn":  207.4,
    "rahu":     89.4,
    "ketu":    269.4,
}

# ── Swiss Ephemeris planet codes ──────────────────────────────────────────────

_SWE_ID: dict[str, int] = {
    "sun":     0,
    "moon":    1,
    "mercury": 2,
    "venus":   3,
    "mars":    4,
    "jupiter": 5,
    "saturn":  6,
    "rahu":    11,   # MEAN_NODE
    "ketu":    11,   # MEAN_NODE + 180 (handled separately)
}

# ── Aspect angle definitions ──────────────────────────────────────────────────

# House-number → degree for Parashari drishti (from natal graha position)
_HOUSE_TO_DEG = {
    3: 60.0,
    4: 90.0,
    5: 120.0,
    7: 180.0,
    8: 210.0,
    9: 240.0,
    10: 270.0,
}

# Parashari special aspects per transit graha (in addition to 7th = 180°)
PARASHARI_ASPECTS: dict[str, list[float]] = {
    "sun":     [180.0],
    "moon":    [180.0],
    "mercury": [180.0],
    "venus":   [180.0],
    "mars":    [90.0, 180.0, 210.0],
    "jupiter": [120.0, 180.0, 240.0],
    "saturn":  [60.0, 180.0, 270.0],
    "rahu":    [120.0, 180.0, 240.0],
    "ketu":    [120.0, 180.0, 240.0],
}

# Classical: only conjunction (0°) and opposition (180°) for performance
CLASSICAL_ASPECTS: list[float] = [0.0, 180.0]

# Tajik: conjunction, sextile, trine (with applying/separating distinction)
TAJIK_ASPECTS: list[float] = [0.0, 60.0, 120.0]

# Aspect angle → name mapping
_ASPECT_TYPE_NAMES: dict[tuple[str, float], str] = {
    ("parashari", 60.0):  "parashari_3rd",
    ("parashari", 90.0):  "parashari_4th",
    ("parashari", 120.0): "parashari_5th",
    ("parashari", 180.0): "opposition",
    ("parashari", 210.0): "parashari_8th",
    ("parashari", 240.0): "parashari_9th",
    ("parashari", 270.0): "parashari_10th",
    ("classical", 0.0):   "conjunction",
    ("classical", 60.0):  "sextile",
    ("classical", 90.0):  "square",
    ("classical", 120.0): "trine",
    ("classical", 180.0): "opposition",
    ("tajik", 0.0):       "tajik_ithasala",   # will be updated applying/separating below
    ("tajik", 60.0):      "tajik_sextile",
    ("tajik", 120.0):     "tajik_trine",
}

_CLASSICAL_CITATIONS: dict[float, str] = {
    0.0:   "BPHS Ch.3 (graha-drishti); Parashari conjunction",
    60.0:  "BPHS Ch.3 (graha-drishti); Tajik Neelakanthi sextile",
    90.0:  "BPHS Ch.3 Mars special 4th-house aspect",
    120.0: "BPHS Ch.3 Jupiter/Rahu/Ketu 5th-house aspect",
    180.0: "BPHS Ch.3 sarva-graha 7th-house aspect (opposition)",
    210.0: "BPHS Ch.3 Mars special 8th-house aspect",
    240.0: "BPHS Ch.3 Jupiter/Rahu/Ketu 9th-house aspect",
    270.0: "BPHS Ch.3 Saturn special 10th-house aspect",
}

ORB_DEG = 1.0  # acceptance orb for exact-aspect detection

# ── Swiss Ephemeris helpers ───────────────────────────────────────────────────

def _get_swe():
    """Import and configure swisseph (Lahiri sidereal)."""
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Set ephemeris path if provided
    ephe_path = os.environ.get("SWE_EPHE_PATH", "/app/ephe")
    if os.path.isdir(ephe_path):
        swe.set_ephe_path(ephe_path)
    return swe


def _swe_lon(swe, planet: str, jd: float) -> float:
    """Return sidereal longitude of planet at Julian day jd."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    planet_id = _SWE_ID[planet]
    result, _ = swe.calc_ut(jd, planet_id, flags)
    lon = result[0]
    if planet == "ketu":
        lon = (lon + 180.0) % 360.0
    return lon


def _swe_lon_with_speed(swe, planet: str, jd: float) -> tuple[float, float]:
    """Return (sidereal longitude, daily speed) of planet at jd."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    planet_id = _SWE_ID[planet]
    result, _ = swe.calc_ut(jd, planet_id, flags)
    lon = result[0]
    speed = result[3]  # deg/day
    if planet == "ketu":
        lon = (lon + 180.0) % 360.0
        speed = -speed  # Ketu moves opposite to Rahu
    return lon, speed


def _date_to_jd(swe, d: date) -> float:
    """Convert a Python date to Julian day number (noon UTC)."""
    return swe.julday(d.year, d.month, d.day, 12.0)


def _jd_to_date(swe, jd: float) -> date:
    """Convert Julian day to Python date."""
    y, m, d, _ = swe.revjul(jd)
    return date(int(y), int(m), int(d))


# ── Angular distance helpers ──────────────────────────────────────────────────

def _angular_diff(lon_a: float, lon_b: float) -> float:
    """Shortest signed angular difference (lon_a - lon_b), range [-180, 180]."""
    diff = (lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return diff


def _orb_to_target(transit_lon: float, natal_lon: float, aspect_deg: float) -> float:
    """
    Return |transit_lon - (natal_lon + aspect_deg) mod 360|, wrapped to [0, 180].
    """
    target = (natal_lon + aspect_deg) % 360.0
    diff = abs(_angular_diff(transit_lon, target))
    return diff


# ── Core computation ──────────────────────────────────────────────────────────

def _find_exact_aspects(
    swe,
    transit_graha: str,
    natal_lon: float,
    aspect_deg: float,
    start_jd: float,
    end_jd: float,
    orb: float = ORB_DEG,
) -> list[tuple[float, float, float]]:
    """
    Scan the [start_jd, end_jd] window daily and find all dates where
    the transit graha forms an exact aspect (within orb) with the natal position.

    Returns list of (jd_of_minimum_orb, transit_lon_at_min, actual_orb_at_min).
    """
    results: list[tuple[float, float, float]] = []
    target_lon = (natal_lon + aspect_deg) % 360.0

    step = 1.0  # daily scan
    jd = start_jd
    prev_orb: Optional[float] = None
    in_window = False
    window_min_orb = float("inf")
    window_min_jd = start_jd
    window_min_tlon = 0.0

    while jd <= end_jd:
        try:
            t_lon = _swe_lon(swe, transit_graha, jd)
        except Exception:
            jd += step
            continue

        current_orb = _orb_to_target(t_lon, natal_lon, aspect_deg)

        if current_orb <= orb:
            # Inside the orb window
            if not in_window:
                in_window = True
                window_min_orb = current_orb
                window_min_jd = jd
                window_min_tlon = t_lon
            elif current_orb < window_min_orb:
                window_min_orb = current_orb
                window_min_jd = jd
                window_min_tlon = t_lon
        else:
            if in_window:
                # Just exited a window — record the minimum
                results.append((window_min_jd, window_min_tlon, window_min_orb))
                in_window = False
                window_min_orb = float("inf")

        prev_orb = current_orb
        jd += step

    # Catch window still open at end
    if in_window:
        results.append((window_min_jd, window_min_tlon, window_min_orb))

    return results


def _is_applying(swe, transit_graha: str, natal_lon: float, aspect_deg: float, jd: float) -> Optional[bool]:
    """
    Determine if the aspect is applying (transit graha moving toward exact aspect)
    or separating (moving away). Returns None if speed is near zero.
    """
    try:
        t_lon, t_speed = _swe_lon_with_speed(swe, transit_graha, jd)
    except Exception:
        return None

    if abs(t_speed) < 1e-6:
        return None

    target = (natal_lon + aspect_deg) % 360.0
    diff = _angular_diff(target, t_lon)  # positive = target is ahead in zodiac

    # If transit speed is positive (direct) and target is ahead -> applying
    # If transit speed is negative (retrograde) and target is behind -> applying
    if t_speed > 0:
        return diff > 0
    else:
        return diff < 0


# ── Public API ────────────────────────────────────────────────────────────────

def compute_aspects_for_period(
    chart_id: str,
    natal_positions: dict[str, float],
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Compute all exact aspects between transit grahas and natal positions
    over [start_date, end_date].

    Returns a list of row dicts ready for INSERT into l1_graha_aspects_lifetime.
    """
    swe = _get_swe()
    start_jd = _date_to_jd(swe, start_date)
    end_jd = _date_to_jd(swe, end_date)

    rows: list[dict] = []
    seen: set[tuple] = set()  # dedup within a single call

    natal_grahas = list(natal_positions.keys())
    transit_grahas = list(_SWE_ID.keys())  # all 9

    # ── Classical aspects: conjunction + opposition (all 9×9) ─────────────────
    for natal_g in natal_grahas:
        natal_lon = natal_positions[natal_g]
        for transit_g in transit_grahas:
            for aspect_deg in CLASSICAL_ASPECTS:
                hits = _find_exact_aspects(
                    swe, transit_g, natal_lon, aspect_deg,
                    start_jd, end_jd,
                )
                for (hit_jd, t_lon, orb_val) in hits:
                    hit_date = _jd_to_date(swe, hit_jd)
                    a_type = _ASPECT_TYPE_NAMES.get(("classical", aspect_deg), f"classical_{int(aspect_deg)}deg")
                    key = (chart_id, natal_g, transit_g, a_type, str(hit_date))
                    if key in seen:
                        continue
                    seen.add(key)
                    applying = _is_applying(swe, transit_g, natal_lon, aspect_deg, hit_jd)
                    rows.append({
                        "chart_id":          chart_id,
                        "natal_graha":       natal_g,
                        "transit_graha":     transit_g,
                        "aspect_type":       a_type,
                        "aspect_system":     "classical",
                        "exact_date":        hit_date,
                        "natal_graha_lon":   natal_lon,
                        "transit_graha_lon": round(t_lon, 4),
                        "aspect_degree":     aspect_deg,
                        "orb_deg":           round(orb_val, 4),
                        "is_applying":       applying,
                        "classical_citation": _CLASSICAL_CITATIONS.get(aspect_deg),
                    })

    # ── Parashari aspects: special angles beyond 180° per transit graha ───────
    for natal_g in natal_grahas:
        natal_lon = natal_positions[natal_g]
        for transit_g in transit_grahas:
            para_angles = PARASHARI_ASPECTS.get(transit_g, [180.0])
            # Skip angles already covered by classical (0° and 180°)
            extra_angles = [a for a in para_angles if a not in CLASSICAL_ASPECTS]
            for aspect_deg in extra_angles:
                hits = _find_exact_aspects(
                    swe, transit_g, natal_lon, aspect_deg,
                    start_jd, end_jd,
                )
                for (hit_jd, t_lon, orb_val) in hits:
                    hit_date = _jd_to_date(swe, hit_jd)
                    a_type = _ASPECT_TYPE_NAMES.get(("parashari", aspect_deg), f"parashari_{int(aspect_deg)}deg")
                    key = (chart_id, natal_g, transit_g, a_type, str(hit_date))
                    if key in seen:
                        continue
                    seen.add(key)
                    applying = _is_applying(swe, transit_g, natal_lon, aspect_deg, hit_jd)
                    rows.append({
                        "chart_id":          chart_id,
                        "natal_graha":       natal_g,
                        "transit_graha":     transit_g,
                        "aspect_type":       a_type,
                        "aspect_system":     "parashari",
                        "exact_date":        hit_date,
                        "natal_graha_lon":   natal_lon,
                        "transit_graha_lon": round(t_lon, 4),
                        "aspect_degree":     aspect_deg,
                        "orb_deg":           round(orb_val, 4),
                        "is_applying":       applying,
                        "classical_citation": _CLASSICAL_CITATIONS.get(aspect_deg),
                    })

    # ── Tajik aspects: 0°, 60°, 120° with applying/separating flag ───────────
    for natal_g in natal_grahas:
        natal_lon = natal_positions[natal_g]
        for transit_g in transit_grahas:
            for aspect_deg in TAJIK_ASPECTS:
                # Skip 0° and 180° already in classical (avoid exact duplication)
                # For Tajik 0° we use a different aspect_type name (tajik_ithasala)
                # but same geometry — still compute separately for the flag
                hits = _find_exact_aspects(
                    swe, transit_g, natal_lon, aspect_deg,
                    start_jd, end_jd,
                )
                for (hit_jd, t_lon, orb_val) in hits:
                    hit_date = _jd_to_date(swe, hit_jd)
                    applying = _is_applying(swe, transit_g, natal_lon, aspect_deg, hit_jd)

                    # Differentiate ithasala (applying) from ishrafa (separating)
                    if aspect_deg == 0.0:
                        if applying is True:
                            a_type = "tajik_ithasala"
                        elif applying is False:
                            a_type = "tajik_ishrafa"
                        else:
                            a_type = "tajik_ithasala"  # default if speed unknown
                    else:
                        a_type = _ASPECT_TYPE_NAMES.get(("tajik", aspect_deg), f"tajik_{int(aspect_deg)}deg")

                    key = (chart_id, natal_g, transit_g, a_type, str(hit_date))
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({
                        "chart_id":          chart_id,
                        "natal_graha":       natal_g,
                        "transit_graha":     transit_g,
                        "aspect_type":       a_type,
                        "aspect_system":     "tajik",
                        "exact_date":        hit_date,
                        "natal_graha_lon":   natal_lon,
                        "transit_graha_lon": round(t_lon, 4),
                        "aspect_degree":     aspect_deg,
                        "orb_deg":           round(orb_val, 4),
                        "is_applying":       applying,
                        "classical_citation": "Tajik Neelakanthi — ithasala/ishrafa/trine/sextile",
                    })

    return rows


def seed_graha_aspects(conn, chart_id: str) -> int:
    """
    Seed l1_graha_aspects_lifetime for chart_id over 2026-01-01 to 2060-12-31.

    Returns number of rows inserted (0 on second call — idempotent via ON CONFLICT DO NOTHING).
    """
    start_date = date(2026, 1, 1)
    end_date = date(2060, 12, 31)

    rows = compute_aspects_for_period(chart_id, NATAL_POSITIONS, start_date, end_date)
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO l1_graha_aspects_lifetime (
            chart_id, natal_graha, transit_graha, aspect_type, aspect_system,
            exact_date, natal_graha_lon, transit_graha_lon, aspect_degree,
            orb_deg, is_applying, classical_citation
        ) VALUES (
            %(chart_id)s, %(natal_graha)s, %(transit_graha)s, %(aspect_type)s, %(aspect_system)s,
            %(exact_date)s, %(natal_graha_lon)s, %(transit_graha_lon)s, %(aspect_degree)s,
            %(orb_deg)s, %(is_applying)s, %(classical_citation)s
        )
        ON CONFLICT (chart_id, natal_graha, transit_graha, aspect_type, exact_date)
        DO NOTHING
    """

    with conn.cursor() as cur:
        cur.executemany(insert_sql, rows)
        inserted = cur.rowcount
    conn.commit()
    return inserted
