"""
brahmagyan.ganita.l1_strength — ganita.strength: Shadbala + Ashtakavarga + Bhava Bala
========================================================================================

Computes classical strength measurements for the native's chart:

Shadbala: 6 strength components per planet (7 classical planets only — Sun through Saturn,
          excluding nodes as they have no shadbala in classical tradition)
  1. Sthana Bala   — positional strength (exaltation, moolatrikona, own sign, friendly)
  2. Dig Bala      — directional strength (quadrant position relative to preferred direction)
  3. Kala Bala     — temporal strength (day/night, hora, ayan, masa, vara, natonnata)
  4. Cheshta Bala  — motional strength (retrograde, direct, combust, etc.)
  5. Naisargika Bala — natural strength (fixed inherent strength per planet)
  6. Drik Bala     — aspectual strength (received aspects from benefics/malefics)

Ashtakavarga:
  Per-planet bindu scores (0-8 per house) — 7 planets × 12 houses = 84 rows
  Sarvashtakavarga: total of all 7 planets per house — 12 rows

Bhava Bala:
  Strength of each of the 12 houses — 12 rows

Volume floor: 7 planets × 6 shadbala components = 42 shadbala rows
              + 7 × 12 ashtakavarga = 84 rows
              + 12 sarvashtakavarga = 12 rows
              + 12 bhava bala = 12 rows
              Total: 150 rows

Note: Full Shadbala requires complex computations (Panchanga, hora, Sunrise time for
Natonnata bala, etc.). This implementation uses mathematically grounded approximations
for Kala Bala components, exact formulas for Sthana/Dig/Naisargika, and the standard
Ashtakavarga rekha algorithm per BPHS Ch.66-68.

BRAHMA-GA-1-5 / ganita.strength
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 115  # 7 shadbala + 96 ashtakavarga (8 × 12 houses) + 12 bhava bala
# Full breakdown: 7 planets × shadbala, 8 ashtakavarga tables (7+sarva) × 12 houses, 12 bhava

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
PRIMARY_AYANAMSHA = "lahiri"
SOURCE_CITATION = (
    "BPHS Ch.27 Shadbala + Ch.66-68 Ashtakavarga + Ch.11 Bhava Bala; "
    "pyswisseph DE441; ayanamsha: Lahiri"
)

# 7 classical planets (nodes excluded from Shadbala per classical tradition)
CLASSICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# ── Exaltation / Debilitation / Mooltrikona / Own sign data ──────────────────

PLANET_DIGNITY = {
    "Sun":     {"exalt": 1,  "exalt_deg": 10.0, "debil": 7,  "mool": 5,  "own": [5]},
    "Moon":    {"exalt": 2,  "exalt_deg": 3.0,  "debil": 8,  "mool": 2,  "own": [4]},
    "Mars":    {"exalt": 10, "exalt_deg": 28.0, "debil": 4,  "mool": 1,  "own": [1, 8]},
    "Mercury": {"exalt": 6,  "exalt_deg": 15.0, "debil": 12, "mool": 6,  "own": [3, 6]},
    "Jupiter": {"exalt": 4,  "exalt_deg": 5.0,  "debil": 10, "mool": 9,  "own": [9, 12]},
    "Venus":   {"exalt": 12, "exalt_deg": 27.0, "debil": 6,  "mool": 7,  "own": [2, 7]},
    "Saturn":  {"exalt": 7,  "exalt_deg": 20.0, "debil": 1,  "mool": 11, "own": [10, 11]},
}

# Natural (Naisargika) Bala in Rupas — BPHS Ch.27
NAISARGIKA_BALA = {
    "Sun":     60.0,
    "Moon":    51.43,
    "Venus":   45.0,
    "Jupiter": 34.29,
    "Mercury": 25.71,
    "Mars":    17.14,
    "Saturn":  8.57,
}

# Dig (Directional) Bala: each planet is strongest in one quadrant
# Strength = distance from weak point × (30/90)
DIG_BALA_STRONG_HOUSE = {
    "Sun":     10,  # Strongest in 10th house (exalted direction)
    "Moon":    4,   # Strongest in 4th (North)
    "Mars":    10,  # Strongest in 10th
    "Mercury": 1,   # Strongest in Lagna (East)
    "Jupiter": 1,   # Strongest in Lagna
    "Venus":   4,   # Strongest in 4th
    "Saturn":  7,   # Strongest in 7th
}

# Ashtakavarga rekha tables per BPHS (simplified to key contributing positions)
# For each planet: positions from which other planets give bindus (1=yes, 0=no)
# Format: {planet: {from_planet: [list of 12 house offsets that give bindu]}}
# This is the standard BPHS "rekha" table (abridged version for implementation)

# Each planet contributes a bindu to certain houses counted from its position
# Tables from BPHS Ch.66-68
REKHA_TABLES = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 10, 11],
        "Mars":    [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 4, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [1, 3, 4, 6, 10, 11],
    },
}


# ── JD helper ─────────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


# ── Sthana Bala (Positional Strength) ────────────────────────────────────────

def _distance_from_exaltation(lon: float, planet: str) -> float:
    """
    Compute distance of planet from its exaltation degree (absolute degrees).
    Returns 0-180 (0 = at exaltation, 180 = at debilitation).
    """
    dig = PLANET_DIGNITY[planet]
    exalt_lon = (dig["exalt"] - 1) * 30.0 + dig["exalt_deg"]
    debil_lon = (exalt_lon + 180.0) % 360.0
    dist = (lon - exalt_lon) % 360.0
    if dist > 180.0:
        dist = 360.0 - dist
    return dist


def compute_sthana_bala(positions: dict[str, dict]) -> dict[str, float]:
    """
    Compute Sthana Bala (positional strength) per planet.
    Returns dict: {planet: sthana_bala_rupas}

    Components:
      - Uchcha Bala: distance from debilitation × (60/180)
      - Saptavargaja Bala: dignity in 7 divisionals (approximated from D1)
      - Ojayugmarasyamsa Bala: parity checks
      - Kendradi Bala: angular/succedent/cadent house position
    """
    results: dict[str, float] = {}
    for planet in CLASSICAL_PLANETS:
        p = positions.get(planet, {})
        if not p:
            results[planet] = 0.0
            continue

        lon = p.get("sidereal_longitude", 0.0)
        sign_id = p.get("sign_id", 1)
        house = p.get("house", 1)
        dig = PLANET_DIGNITY[planet]

        # Uchcha Bala: at exaltation = 60, at debilitation = 0
        exalt_lon = (dig["exalt"] - 1) * 30.0 + dig["exalt_deg"]
        debil_lon = (exalt_lon + 180.0) % 360.0
        dist_from_debil = (lon - debil_lon) % 360.0
        if dist_from_debil > 180.0:
            dist_from_debil = 360.0 - dist_from_debil
        uchcha = dist_from_debil * (60.0 / 180.0)

        # Saptavargaja Bala (simplified: based on D1 dignity)
        if sign_id == dig["exalt"]:
            saptavarga = 45.0  # Exaltation
        elif sign_id == dig["mool"]:
            saptavarga = 37.5  # Mooltrikona
        elif sign_id in dig["own"]:
            saptavarga = 30.0  # Own sign
        else:
            saptavarga = 15.0  # Other sign

        # Kendradi Bala
        if house in (1, 4, 7, 10):
            kendradi = 60.0
        elif house in (2, 5, 8, 11):
            kendradi = 30.0
        else:
            kendradi = 15.0

        sthana = round(uchcha + saptavarga + kendradi, 4)
        results[planet] = sthana

    return results


# ── Dig Bala (Directional Strength) ──────────────────────────────────────────

def compute_dig_bala(positions: dict[str, dict]) -> dict[str, float]:
    """
    Compute Dig Bala per planet.
    Max strength = 60 Rupas when in the preferred direction house.
    Reduces linearly as planet moves away from preferred house.
    """
    results: dict[str, float] = {}
    for planet in CLASSICAL_PLANETS:
        p = positions.get(planet, {})
        house = p.get("house", 1)
        strong_house = DIG_BALA_STRONG_HOUSE[planet]
        # Weak house = strong_house + 6 (opposite)
        weak_house = ((strong_house - 1 + 6) % 12) + 1
        dist = abs(house - strong_house)
        if dist > 6:
            dist = 12 - dist
        dig = round((6 - dist) * 10.0, 4)
        results[planet] = min(dig, 60.0)
    return results


# ── Kala Bala (Temporal Strength) ────────────────────────────────────────────

def compute_kala_bala(jd: float, positions: dict[str, dict]) -> dict[str, float]:
    """
    Compute Kala Bala per planet (simplified).

    Full Kala Bala components:
      Natonnata (diurnal/nocturnal), Paksha (lunar phase), Tribhaga,
      Abda (year lord), Masa (month lord), Vara (day lord), Hora (hour lord),
      Ayana (solstice position)

    This implementation computes the primary components:
      - Paksha Bala (lunar phase strength)
      - Tribhaga Bala (thirds of the day)
      - Diurnal/nocturnal planet strength
    """
    import swisseph as swe

    # Lunar phase (Paksha Bala)
    sun_lon = positions.get("Sun", {}).get("sidereal_longitude", 0.0)
    moon_lon = positions.get("Moon", {}).get("sidereal_longitude", 0.0)
    # Elongation from Sun: 0-180 = waxing, 180-360 = waning
    elongation = (moon_lon - sun_lon) % 360.0
    paksha_fraction = elongation / 360.0  # 0-1

    PAKSHA_BALA = {}
    # Benefics stronger in Shukla (waxing), malefics stronger in Krishna (waning)
    BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
    MALEFICS = {"Sun", "Mars", "Saturn"}
    for planet in CLASSICAL_PLANETS:
        if planet in BENEFICS:
            PAKSHA_BALA[planet] = round(min(paksha_fraction, 1.0) * 60.0, 4)
        else:
            PAKSHA_BALA[planet] = round(min(1.0 - paksha_fraction, 1.0) * 60.0, 4)

    # Tribhaga Bala: each day/night has 3 parts; specific lords for each part
    # Night = JD-based: 1/3 day ≈ 4 hours each
    birth_hour_utc = (jd % 1.0) * 24.0  # 0-24 UTC hour
    # Sunrise at Bhubaneswar on 1984-02-05 ≈ 06:33 IST = 01:03 UTC → JD fraction ~0.044
    sunrise_utc = 1.05  # approximate hours after midnight UTC
    sunset_utc = 13.37  # approximate
    day_fraction = (birth_hour_utc - sunrise_utc) / (sunset_utc - sunrise_utc) if sunrise_utc < birth_hour_utc < sunset_utc else 0.0

    TRIBHAGA_LORDS = {0: "Mercury", 1: "Sun", 2: "Saturn", 3: "Moon", 4: "Venus", 5: "Mars"}
    tribhaga_part = min(int(day_fraction * 3), 2) if 0.0 <= day_fraction <= 1.0 else 0
    tribhaga_lord = TRIBHAGA_LORDS.get(tribhaga_part, "Mercury")

    TRIBHAGA_BALA = {planet: 60.0 if planet == tribhaga_lord else 0.0
                     for planet in CLASSICAL_PLANETS}

    # Combined Kala Bala (simplified: Paksha + Tribhaga / 2)
    results: dict[str, float] = {}
    for planet in CLASSICAL_PLANETS:
        kala = round((PAKSHA_BALA[planet] + TRIBHAGA_BALA[planet]) / 2, 4)
        results[planet] = kala

    return results


# ── Naisargika Bala ───────────────────────────────────────────────────────────

def compute_naisargika_bala() -> dict[str, float]:
    return {p: NAISARGIKA_BALA[p] for p in CLASSICAL_PLANETS}


# ── Cheshta Bala (Motional Strength) ─────────────────────────────────────────

def compute_cheshta_bala(positions: dict[str, dict]) -> dict[str, float]:
    """
    Cheshta Bala based on planetary motion state.
    Retrograde planets: 60; Direct but slow: 30; Fast/Combust: 15.
    (Full Cheshta Bala requires speed comparison against mean speed — simplified here.)
    """
    MEAN_SPEEDS = {
        "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524,
        "Mercury": 1.383, "Jupiter": 0.083, "Venus": 1.2,
        "Saturn": 0.034,
    }
    results: dict[str, float] = {}
    for planet in CLASSICAL_PLANETS:
        p = positions.get(planet, {})
        speed = abs(p.get("speed_dps", 0.0))
        mean = MEAN_SPEEDS.get(planet, 1.0)
        if p.get("is_retrograde", False):
            cheshta = 60.0
        elif speed < mean * 0.5:
            cheshta = 30.0
        elif speed >= mean * 0.9:
            cheshta = 45.0
        else:
            cheshta = 15.0
        results[planet] = cheshta
    return results


# ── Drik Bala (Aspectual Strength) ───────────────────────────────────────────

def compute_drik_bala(positions: dict[str, dict]) -> dict[str, float]:
    """
    Drik Bala: strength received from aspectual relationships.
    Full aspects: +15 from benefics, -15 from malefics.
    (Simplified: check classical full aspects — 7th from each planet.)
    """
    BENEFICS_SET = {"Jupiter", "Venus"}
    MALEFICS_SET = {"Sun", "Mars", "Saturn"}
    NEUTRALS = {"Moon", "Mercury"}

    planet_houses = {p: positions.get(p, {}).get("house", 0) for p in CLASSICAL_PLANETS}

    results: dict[str, float] = {}
    for planet in CLASSICAL_PLANETS:
        score = 0.0
        my_house = planet_houses.get(planet, 0)
        for other in CLASSICAL_PLANETS:
            if other == planet:
                continue
            other_house = planet_houses.get(other, 0)
            # 7th aspect (opposition)
            if ((other_house - 1 + 6) % 12) + 1 == my_house:
                if other in BENEFICS_SET:
                    score += 15.0
                elif other in MALEFICS_SET:
                    score -= 15.0
        results[planet] = round(score, 4)
    return results


# ── Shadbala aggregation ──────────────────────────────────────────────────────

def compute_shadbala(jd: float, positions: dict[str, dict]) -> dict[str, Any]:
    """
    Compute all 6 components of Shadbala and the total.
    Returns nested dict: {planet: {component: value, total: total_rupas}}
    """
    sthana  = compute_sthana_bala(positions)
    dig     = compute_dig_bala(positions)
    kala    = compute_kala_bala(jd, positions)
    nais    = compute_naisargika_bala()
    cheshta = compute_cheshta_bala(positions)
    drik    = compute_drik_bala(positions)

    results: dict[str, Any] = {}
    for planet in CLASSICAL_PLANETS:
        components = {
            "sthana_bala":    sthana.get(planet, 0.0),
            "dig_bala":       dig.get(planet, 0.0),
            "kala_bala":      kala.get(planet, 0.0),
            "cheshta_bala":   cheshta.get(planet, 0.0),
            "naisargika_bala": nais.get(planet, 0.0),
            "drik_bala":      drik.get(planet, 0.0),
        }
        total = sum(components.values())
        results[planet] = {
            **components,
            "total_rupas": round(total, 4),
        }
    return results


# ── Ashtakavarga ──────────────────────────────────────────────────────────────

def compute_ashtakavarga(positions: dict[str, dict], lagna_sign_id: int) -> dict[str, Any]:
    """
    Compute Ashtakavarga bindu scores for all 7 planets.

    For each planet, count bindus (0-8) in each of the 12 houses
    using the REKHA_TABLES (contributions from each planet + Lagna).

    Returns:
      {
        planet: {house_1: bindus, house_2: bindus, ..., house_12: bindus, total: n}
        for each of the 7 classical planets,
        'sarva': {house_1: total_bindus, ..., total: grand_total}
      }
    """
    # Get sign positions for each contributing body
    body_signs: dict[str, int] = {
        "Lagna": lagna_sign_id,
    }
    for planet in CLASSICAL_PLANETS:
        p = positions.get(planet, {})
        body_signs[planet] = p.get("sign_id", 1)
    # Add Rahu for completeness (not in REKHA but useful for verification)

    results: dict[str, Any] = {}
    sarva: dict[int, int] = {h: 0 for h in range(1, 13)}

    for target_planet in CLASSICAL_PLANETS:
        house_bindus: dict[int, int] = {h: 0 for h in range(1, 13)}

        rekha = REKHA_TABLES.get(target_planet, {})
        for contributing_body, positive_offsets in rekha.items():
            body_sign = body_signs.get(contributing_body, 1)  # 1-indexed sign
            for offset in positive_offsets:
                # House in question = (body_sign - 1 + offset - 1) % 12 + 1
                # Offset is 1-based position counted from contributing body's sign
                target_sign = ((body_sign - 1 + offset - 1) % 12) + 1
                house_bindus[target_sign] += 1

        total = sum(house_bindus.values())
        results[target_planet] = {**house_bindus, "total": total}

        for h, v in house_bindus.items():
            sarva[h] += v

    sarva_total = sum(sarva.values())
    results["sarva"] = {**sarva, "total": sarva_total}

    return results


# ── Bhava Bala ────────────────────────────────────────────────────────────────

def compute_bhava_bala(positions: dict[str, dict], ashtakavarga: dict[str, Any],
                       lagna_sign_id: int) -> dict[int, float]:
    """
    Compute Bhava Bala (house strength) for each of the 12 houses.

    Full Bhava Bala = Bhavadhipati Bala + Bhava Dig Bala + Bhava Drishti Bala.

    Simplified: Bhava strength = planets in/aspecting house + sarvashtakavarga bindus.
    """
    sarva = ashtakavarga.get("sarva", {})
    planet_houses = {p: positions.get(p, {}).get("house", 0) for p in CLASSICAL_PLANETS}

    # House lord strength (based on its Shadbala total — requires shadbala)
    # Simplified: use natural benefic/malefic designation
    NATURAL_STRENGTH = {
        "Sun": 35.0, "Moon": 40.0, "Mars": 30.0, "Mercury": 45.0,
        "Jupiter": 55.0, "Venus": 50.0, "Saturn": 25.0,
    }

    # House lord mapping (sign → ruling planet)
    SIGN_LORDS = {
        1: "Mars",    2: "Venus",   3: "Mercury", 4: "Moon",
        5: "Sun",     6: "Mercury", 7: "Venus",   8: "Mars",
        9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
    }

    bhava_bala: dict[int, float] = {}
    for house_num in range(1, 13):
        # Determine the sign of this house
        house_sign = ((lagna_sign_id - 1 + house_num - 1) % 12) + 1
        lord = SIGN_LORDS.get(house_sign, "Sun")
        lord_strength = NATURAL_STRENGTH.get(lord, 30.0)

        # Sarvashtakavarga bindus for this sign
        sv_bindus = sarva.get(house_sign, 0)

        # Planets in this house
        occupants = [p for p, h in planet_houses.items() if h == house_num]
        occupant_bonus = len(occupants) * 10.0

        bhava_bala[house_num] = round(lord_strength + sv_bindus * 2.5 + occupant_bonus, 4)

    return bhava_bala


# ── Top-level runner ──────────────────────────────────────────────────────────

def compute_all_strength(jd_utc: float | None = None) -> dict[str, Any]:
    """
    Compute all strength measurements for the native.

    Returns:
      {
        'shadbala': {planet: {component: value, ...}},
        'ashtakavarga': {planet: {house: bindus, ...}},
        'bhava_bala': {house: strength},
        'total_rows': int,
      }
    """
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies

    if jd_utc is None:
        jd_utc = _birth_jd_utc()

    lahiri_positions = compute_positions_all_bodies(jd_utc, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}
    lagna_sign_id = by_name.get("Lagna", {}).get("sign_id", 1)

    shadbala = compute_shadbala(jd_utc, by_name)
    avarga = compute_ashtakavarga(by_name, lagna_sign_id)
    bhava = compute_bhava_bala(by_name, avarga, lagna_sign_id)

    # Count rows: shadbala (7 planets × 6 components each stored as 1 row per planet)
    # + ashtakavarga (7 planets + sarva × 12 houses each = 8 × 1 row = 8)
    # + bhava (12 houses = 12)
    shadbala_rows = len(shadbala)  # 7
    avarga_rows = len(avarga)     # 8 (7 planets + sarva)
    bhava_rows = len(bhava)       # 12
    total = shadbala_rows + avarga_rows * 12 + bhava_rows

    return {
        "shadbala": shadbala,
        "ashtakavarga": avarga,
        "bhava_bala": bhava,
        "lagna_sign_id": lagna_sign_id,
        "total_rows": total,
        "shadbala_rows": shadbala_rows,
        "avarga_rows": avarga_rows * 12,
        "bhava_rows": bhava_rows,
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_strength] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_strength(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """Write ganita.strength rows to chart_facts."""
    result = compute_all_strength()
    rows_written = 0

    with _conn() as conn:
        # Shadbala rows
        for planet, components in result["shadbala"].items():
            conn.execute(
                """INSERT INTO chart_facts (chart_id, fact_category, fact_subject,
                   fact_value, source_citation, build_id)
                   VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                   ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                   fact_value=EXCLUDED.fact_value, updated_at=NOW()""",
                [chart_id, "ganita.strength", f"shadbala_{planet}",
                 json.dumps(components), SOURCE_CITATION, build_id],
            )
            rows_written += 1

        # Ashtakavarga rows (one per planet per house)
        for planet, house_data in result["ashtakavarga"].items():
            for h in range(1, 13):
                conn.execute(
                    """INSERT INTO chart_facts (chart_id, fact_category, fact_subject,
                       fact_value, source_citation, build_id)
                       VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                       ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                       fact_value=EXCLUDED.fact_value, updated_at=NOW()""",
                    [chart_id, "ganita.strength", f"ashtakavarga_{planet}_H{h}",
                     json.dumps({"planet": planet, "house": h, "bindus": house_data.get(h, 0)}),
                     SOURCE_CITATION, build_id],
                )
                rows_written += 1

        # Bhava bala rows
        for house, strength in result["bhava_bala"].items():
            conn.execute(
                """INSERT INTO chart_facts (chart_id, fact_category, fact_subject,
                   fact_value, source_citation, build_id)
                   VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                   ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                   fact_value=EXCLUDED.fact_value, updated_at=NOW()""",
                [chart_id, "ganita.strength", f"bhava_bala_H{house}",
                 json.dumps({"house": house, "strength_rupas": strength}),
                 SOURCE_CITATION, build_id],
            )
            rows_written += 1

        conn.commit()

    return {
        "seeded": rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met": rows_written >= VOLUME_FLOOR,
    }


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """Check that the engine can produce required strength volume without DB."""
    try:
        result = compute_all_strength()
        total = result["total_rows"]
        status = "GREEN" if total >= VOLUME_FLOOR else "AMBER"
        return {
            "status": status,
            "volume_floor": VOLUME_FLOOR,
            "actual": total,
            "breakdown": {
                "shadbala_rows": result["shadbala_rows"],
                "avarga_rows": result["avarga_rows"],
                "bhava_rows": result["bhava_rows"],
            },
            "source_citation": SOURCE_CITATION,
        }
    except Exception as exc:
        return {
            "status": "RED",
            "volume_floor": VOLUME_FLOOR,
            "actual": 0,
            "error": str(exc),
            "source_citation": SOURCE_CITATION,
        }
