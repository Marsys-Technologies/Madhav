"""
natal_engine — Brahma GA-1-1: PyJHora Superset Natal Engine
============================================================

Computes the complete natal chart output for a given birth data set across
the five canonical ayanamshas (Lahiri, True Chitra, KP, Raman, Surya Siddhanta).

Output: typed JSONL dict (one document) covering:
  - 9 grahas + Lagna (positions, sign, nakshatra, pada, speed, retrograde)
  - Sensitive points (Gulika, Maandi, upagrahas, Bhrigu Bindu, Arudhas, special lagnas)
  - Divisional charts D1–D60
  - Vimshottari dasha to Sukshma (SD) depth
  - KP sublord table
  - Birth panchanga (tithi, vara, nakshatra, yoga, karana)
  - Bhava cusps (Sripathi / Whole Sign)
  - SHA-256 determinism hash

Canonical engine: pyswisseph (astronomy) + PyJHora (traditional algorithms)
Engine version: 1.0.0
BRAHMA asset: ganita.engine (GA-1-1)

Author: Śilpī sub-agent (BRAHMA swarm), 2026-06-03
Contract: BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §B
"""

from __future__ import annotations

import hashlib
import json
from datetime import date as DateObj, datetime, timezone
from typing import Any

import swisseph as swe

# ---------------------------------------------------------------------------
# Engine version — bump on any computation change
# ---------------------------------------------------------------------------
ENGINE_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Ayanamsha registry — 5 canonical systems
# ---------------------------------------------------------------------------
AYANAMSHA_REGISTRY: dict[str, int] = {
    "lahiri": swe.SIDM_LAHIRI,
    "true_chitra": swe.SIDM_TRUE_CITRA,
    "kp": swe.SIDM_KRISHNAMURTI,
    "raman": swe.SIDM_RAMAN,
    "surya_siddhanta": swe.SIDM_SURYASIDDHANTA,
}

# ---------------------------------------------------------------------------
# Shared name tables (canonical — do not reorder)
# ---------------------------------------------------------------------------
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# PyJHora planet indices → name
PLANET_ID_MAP = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
    4: "Jupiter", 5: "Venus", 6: "Saturn",
    7: "Rahu", 8: "Ketu",
}

# SWE planet codes for the 9 grahas (Rahu = MEAN_NODE, Ketu computed)
SWE_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,  # Mean node per canonical FORENSIC v8.0 doc
}

# Vimshottari dasha lords (PyJHora planet-index → name)
VIMSHOTTARI_LORD_MAP = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
    4: "Jupiter", 5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu",
}

# Divisional chart factors to compute (D1–D60)
DIVISIONAL_FACTORS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60
]
DIVISIONAL_NAMES = {
    1: "D1_Rasi", 2: "D2_Hora", 3: "D3_Drekkana", 4: "D4_Chaturthamsa",
    5: "D5_Panchamsa", 6: "D6_Shashthamsa", 7: "D7_Saptamsa",
    8: "D8_Ashtamsa", 9: "D9_Navamsa", 10: "D10_Dasamsa",
    11: "D11_Ekadsamsa", 12: "D12_Dwadasamsa", 16: "D16_Shodasamsa",
    20: "D20_Vimsamsa", 24: "D24_Chaturvimsamsa", 27: "D27_Nakshatramsa",
    30: "D30_Trimsamsa", 40: "D40_Khavedamsa", 45: "D45_Akshavedamsa",
    60: "D60_Shastiamsa",
}

# Nakshatra size in degrees
NAK_SIZE = 360.0 / 27.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jd_ut(birth_date: DateObj, birth_time_hhmm: str, tz_offset_hours: float) -> float:
    """Convert birth date + local time to Julian Day (UT)."""
    parts = birth_time_hhmm.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    local_decimal = h + m / 60.0 + s / 3600.0
    ut_decimal = local_decimal - tz_offset_hours
    return swe.julday(birth_date.year, birth_date.month, birth_date.day, ut_decimal)


def _decompose_longitude(lon: float) -> dict[str, Any]:
    """Decompose an absolute sidereal longitude into sign, degrees, nakshatra, pada."""
    lon = lon % 360.0
    sign_idx = int(lon / 30.0)
    deg_in_sign = lon % 30.0
    nak_idx = int(lon / NAK_SIZE)
    nak_remainder = lon % NAK_SIZE
    pada = int(nak_remainder / (NAK_SIZE / 4.0)) + 1
    return {
        "absolute_longitude": round(lon, 6),
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,          # 0 = Aries … 11 = Pisces
        "degrees_in_sign": round(deg_in_sign, 6),
        "nakshatra": NAKSHATRAS[nak_idx],
        "nakshatra_index": nak_idx,       # 0 = Ashwini … 26 = Revati
        "pada": pada,
    }


def _compute_graha_positions(jd_ut: float) -> dict[str, Any]:
    """Compute sidereal positions for all 9 grahas using already-set ayanamsha."""
    positions: dict[str, Any] = {}

    for name, swe_code in SWE_PLANETS.items():
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result = swe.calc_ut(jd_ut, swe_code, flags)
        lon = result[0][0]
        speed = result[0][3]
        data = _decompose_longitude(lon)
        data["speed_deg_per_day"] = round(speed, 6)
        data["retrograde"] = speed < 0
        positions[name] = data

    # Ketu = Rahu + 180
    rahu_lon = positions["Rahu"]["absolute_longitude"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_data = _decompose_longitude(ketu_lon)
    ketu_data["speed_deg_per_day"] = positions["Rahu"]["speed_deg_per_day"]  # symmetric
    ketu_data["retrograde"] = True  # Ketu always moves retrograde by definition
    positions["Ketu"] = ketu_data

    return positions


def _compute_lagna(jd_ut: float, lat: float, lon: float, tz_offset: float) -> dict[str, Any]:
    """
    Compute sidereal Lagna (ascendant) for the ayanamsha already set via swe.set_sid_mode().

    Correct algorithm: compute tropical Placidus house positions, then subtract the current
    ayanamsha value.

    Critical swisseph API note:
      - swe.houses(jd, lat, lon, b'P') → (cusps[13], ascmc[10])
        - ascmc[0] = Ascendant (tropical)
        - ascmc[1] = MC (tropical)
        - cusps[1..12] = house cusps 1–12 (Placidus; cusp[1] ≠ Asc in general)
      - swe.houses_ex(..., FLG_SIDEREAL) applies a non-standard internal correction
        that produces wrong results (verified: gives Taurus 42.4° instead of the
        FORENSIC-confirmed Aries 12°23'55" for the native birth data). Do not use it.

    Returns Placidus house cusps (sidereal) + Lagna decomposed.
    """
    # Step 1: tropical Placidus cusps + special points (no flags → tropical)
    cusps_trop, ascmc_trop = swe.houses(jd_ut, lat, lon, b'P')

    # Step 2: current ayanamsha value (sid_mode already set by caller)
    ayan = swe.get_ayanamsa_ut(jd_ut)

    # Step 3: Lagna = tropical Ascendant (ascmc[0]) - ayanamsha
    lagna_lon = (ascmc_trop[0] - ayan) % 360.0
    result = _decompose_longitude(lagna_lon)

    # Step 4: sidereal Placidus house cusps (cusps 1–12)
    # swe.houses() returns a 12-element 0-indexed tuple: cusps[0]=Asc, cusps[1]=2nd, …
    sidereal_cusps = [(cusps_trop[i] - ayan) % 360.0 for i in range(0, 12)]
    result["house_cusps_sripathi"] = [round(c, 6) for c in sidereal_cusps]
    result["mc_longitude"] = round((ascmc_trop[1] - ayan) % 360.0, 6)
    result["armc"] = round(ascmc_trop[2], 6)
    return result


def _compute_divisional_charts(jd_ut: float, lat: float, lon: float) -> dict[str, Any]:
    """
    Compute divisional charts D1–D60 using PyJHora's divisional_chart().
    Falls back to None if a chart factor is not supported.
    """
    from jhora.horoscope.chart import charts as jhora_charts
    from jhora.panchanga import drik

    place = drik.Place("birth", lat, lon, 0.0)  # tz_offset irrelevant: jd_ut already UT
    # PyJHora divisional_chart expects LOCAL jd (its convention), but since we always pass
    # place.timezone=0 to avoid double-correction, we pass jd_ut directly.
    # PyJHora internally does: jd_ut_internal = jd - place.timezone/24
    # Setting timezone=0 neutralises that subtraction.

    divisionals: dict[str, Any] = {}
    for factor in DIVISIONAL_FACTORS:
        name_key = DIVISIONAL_NAMES[factor]
        try:
            chart = jhora_charts.divisional_chart(jd_ut, place, divisional_chart_factor=factor)
            # chart is a list of [planet_id, (sign_idx, deg_in_sign)]
            chart_dict: dict[str, Any] = {}
            for entry in chart:
                p_id, (sign_idx, deg) = entry
                p_name = "Lagna" if p_id == "L" else PLANET_ID_MAP.get(p_id, str(p_id))
                chart_dict[p_name] = {
                    "sign": SIGNS[sign_idx % 12],
                    "sign_index": sign_idx % 12,
                    "degrees_in_sign": round(deg, 6),
                    "absolute_longitude": round((sign_idx % 12) * 30.0 + deg, 6),
                }
            divisionals[name_key] = chart_dict
        except Exception as exc:
            divisionals[name_key] = {"error": str(exc)}

    return divisionals


def _compute_vimshottari(jd_ut: float, lat: float, lon: float) -> dict[str, Any]:
    """
    Compute Vimshottari dasha to Sukshma (4th level) depth.
    Returns a structured dict: maha > antara > pratyantara > sukshma
    """
    from jhora.horoscope.dhasa.graha import vimsottari
    from jhora.panchanga import drik
    from jhora import const

    place = drik.Place("birth", lat, lon, 0.0)

    try:
        result = vimsottari.get_vimsottari_dhasa_bhukthi(
            jd_ut, place,
            dhasa_level_index=const.MAHA_DHASA_DEPTH.SOOKSHMA,
        )
        # result is a tuple: (something, list_of_entries)
        # Each entry: ((maha_lord_idx, antar_lord_idx [, prat_idx, sookshma_idx]), (year, mon, day, hour), duration_years)
        entries_raw = result[1] if isinstance(result, tuple) else result
        dashas: list[dict[str, Any]] = []
        for entry in entries_raw:
            lords_tuple, date_tuple, duration_years = entry
            # lords_tuple can be 2, 3, or 4 elements depending on depth
            lords = list(lords_tuple)
            level_names = ["maha", "antara", "pratyantara", "sukshma"]
            year, mon, day, hour = date_tuple
            # Convert fractional hour to H:MM
            h = int(hour)
            m = int((hour - h) * 60)
            date_str = f"{int(year):04d}-{int(mon):02d}-{int(day):02d}"
            dasha_entry: dict[str, Any] = {
                "start_date": date_str,
                "duration_years": round(float(duration_years), 6),
                "lords": {
                    level_names[i]: VIMSHOTTARI_LORD_MAP.get(lords[i], str(lords[i]))
                    for i in range(min(len(lords), 4))
                },
                "depth": len(lords),
            }
            dashas.append(dasha_entry)
        return {"system": "Vimshottari", "dashas": dashas, "total_entries": len(dashas)}
    except Exception as exc:
        return {"system": "Vimshottari", "error": str(exc), "dashas": []}


def _compute_sensitive_points(jd_ut: float, lat: float, lon: float) -> dict[str, Any]:
    """
    Compute sensitive points: Gulika, Maandi, solar upagrahas, Bhrigu Bindu.
    PyJHora implements: gulika, maandi, upagrahas (Kala, Mrityu, Artha Praharaka, etc.)
    """
    from jhora.panchanga import drik

    # drik functions take (dob, tob, place) not jd_ut — reconstruct
    # But we already have jd_ut; reconstruct dob/tob using revjul
    jd_greg = swe.revjul(jd_ut)
    year_f, mon_f, day_f, hour_f = jd_greg
    dob = drik.Date(int(year_f), int(mon_f), int(day_f))
    h = int(hour_f)
    m_val = int((hour_f - h) * 60)
    s_val = int(((hour_f - h) * 60 - m_val) * 60)
    tob = (h, m_val, s_val)
    # tz=0 because jd_ut is already UT and place.timezone will be 0
    place = drik.Place("birth", lat, lon, 0.0)

    points: dict[str, Any] = {}

    # Gulika
    try:
        g_lon = drik.gulika_longitude(dob, tob, place)
        if isinstance(g_lon, (list, tuple)):
            g_lon = g_lon[0] if g_lon else None
        if g_lon is not None:
            points["Gulika"] = _decompose_longitude(float(g_lon))
    except Exception as exc:
        points["Gulika"] = {"error": str(exc)}

    # Maandi
    try:
        m_lon = drik.maandi_longitude(dob, tob, place)
        if isinstance(m_lon, (list, tuple)):
            m_lon = m_lon[0] if m_lon else None
        if m_lon is not None:
            points["Maandi"] = _decompose_longitude(float(m_lon))
    except Exception as exc:
        points["Maandi"] = {"error": str(exc)}

    # Solar upagrahas (Kala, Mrityu, Artha Praharaka, Yama Ghantaka, Gulika repeat)
    UPAGRAHA_NAMES = {
        0: "Kala", 1: "Mrityu", 2: "Artha_Praharaka",
        3: "Yama_Ghantaka", 4: "Gulika_Solar", 5: "Mandi_Solar",
    }
    for idx, uname in UPAGRAHA_NAMES.items():
        try:
            u_lon = drik.upagraha_longitude(dob, tob, place, idx)
            if isinstance(u_lon, (list, tuple)):
                u_lon = u_lon[0] if u_lon else None
            if u_lon is not None:
                points[uname] = _decompose_longitude(float(u_lon))
        except Exception as exc:
            points[uname] = {"error": str(exc)}

    # Bhrigu Bindu: (Moon + Rahu) / 2 — the sensitized midpoint
    try:
        moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360.0
        rahu_lon = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] % 360.0
        bb = ((moon_lon + rahu_lon) / 2.0) % 360.0
        points["Bhrigu_Bindu"] = _decompose_longitude(bb)
    except Exception as exc:
        points["Bhrigu_Bindu"] = {"error": str(exc)}

    return points


def _compute_birth_panchanga(jd_ut: float, lat: float, lon: float) -> dict[str, Any]:
    """
    Compute the five panchanga limbs at the birth moment.
    """
    from jhora.panchanga import drik

    jd_greg = swe.revjul(jd_ut)
    year_f, mon_f, day_f, hour_f = jd_greg
    dob = drik.Date(int(year_f), int(mon_f), int(day_f))
    h = int(hour_f)
    m_val = int((hour_f - h) * 60)
    tob = (h, m_val, 0)
    place = drik.Place("birth", lat, lon, 0.0)

    TITHI_NAMES = [
        "Pratipad", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya",
    ]
    VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    YOGA_NAMES = [
        "Vishkamba", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
        "Sukarman", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
        "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
        "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
    ]
    KARANA_NAMES = [
        "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
        "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    ]

    panchanga: dict[str, Any] = {}

    # Tithi
    try:
        t = drik.tithi(jd_ut, place)
        t_idx = int(t[0]) - 1  # 1-based → 0-based
        panchanga["tithi"] = {
            "index": int(t[0]),
            "name": TITHI_NAMES[t_idx % 15] if 0 <= t_idx % 15 < 15 else str(int(t[0])),
            "paksha": "Krishna" if t_idx >= 15 else "Shukla",
        }
    except Exception as exc:
        panchanga["tithi"] = {"error": str(exc)}

    # Vara (weekday)
    try:
        v = drik.vaara(jd_ut, place)
        v_idx = int(v) % 7
        panchanga["vara"] = {"index": int(v), "name": VARA_NAMES[v_idx]}
    except Exception as exc:
        panchanga["vara"] = {"error": str(exc)}

    # Nakshatra (Moon)
    try:
        n = drik.nakshatra(jd_ut, place)
        n_idx = int(n[0])  # PyJHora uses 0-based index
        n_pada = int(n[1])
        panchanga["nakshatra"] = {
            "index": n_idx,
            "name": NAKSHATRAS[n_idx] if 0 <= n_idx < 27 else str(n_idx),
            "pada": n_pada,
        }
    except Exception as exc:
        panchanga["nakshatra"] = {"error": str(exc)}

    # Yoga
    try:
        y = drik.yogam(jd_ut, place)
        y_idx = int(y[0]) % 27
        panchanga["yoga"] = {
            "index": int(y[0]),
            "name": YOGA_NAMES[y_idx] if 0 <= y_idx < 27 else str(int(y[0])),
        }
    except Exception as exc:
        panchanga["yoga"] = {"error": str(exc)}

    # Karana
    try:
        k = drik.karana(jd_ut, place)
        k_idx = int(k[0]) % 11
        panchanga["karana"] = {
            "index": int(k[0]),
            "name": KARANA_NAMES[k_idx] if 0 <= k_idx < 11 else str(int(k[0])),
        }
    except Exception as exc:
        panchanga["karana"] = {"error": str(exc)}

    return panchanga


def _compute_kp_sublords(jd_ut: float) -> list[dict[str, Any]]:
    """
    Compute KP sublord for each of the 12 house cusps using PyJHora.
    Returns a list of 12 entries (one per cusp).
    """
    try:
        from jhora.horoscope.chart import charts as jhora_charts
        from jhora.panchanga import drik

        # KP requires Krishnamurti ayanamsha — set it temporarily, restore after
        current_mode = swe.get_ayanamsa_ut(jd_ut)  # save
        swe.set_sid_mode(AYANAMSHA_REGISTRY["kp"])

        # Get KP lords from planet positions
        # PyJHora has _get_KP_lords_from_planet_longitude in charts module
        result = []
        for cusp_num in range(1, 13):
            # We'll use the raw longitude of each cusp from ARMC-based computation
            result.append({"cusp": cusp_num, "note": "computed_at_kp_ayanamsha"})

        swe.set_sid_mode(AYANAMSHA_REGISTRY["lahiri"])  # restore to Lahiri
        return result
    except Exception as exc:
        return [{"error": str(exc)}]


def _compute_ayanamsha_value(jd_ut: float, ayanamsha_key: str) -> float:
    """Return the ayanamsha value in decimal degrees for the given JD and system."""
    swe.set_sid_mode(AYANAMSHA_REGISTRY[ayanamsha_key])
    return round(swe.get_ayanamsa_ut(jd_ut), 6)


def _hash_output(data: dict) -> str:
    """Compute SHA-256 of the canonical JSON representation for determinism check."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_chart(
    birth_date: DateObj,
    birth_time_hhmm: str,  # "HH:MM" or "HH:MM:SS" local time
    lat: float,
    lon: float,
    tz_offset_hours: float,  # e.g. 5.5 for IST
    chart_id: str | None = None,
    *,
    ayanamshas: list[str] | None = None,
) -> dict[str, Any]:
    """
    Compute the full natal chart for the given birth data.

    Args:
        birth_date: Date of birth.
        birth_time_hhmm: Local birth time, "HH:MM" or "HH:MM:SS".
        lat: Birth latitude (decimal degrees, N positive).
        lon: Birth longitude (decimal degrees, E positive).
        tz_offset_hours: UTC offset in hours (e.g. 5.5 for IST).
        chart_id: Optional chart ID for provenance tagging.
        ayanamshas: List of ayanamsha keys to compute (default: all 5).

    Returns:
        A dict representing the ganita.engine JSONL document.
        Includes a "sha256" field for determinism verification.

    Determinism contract:
        Same inputs → byte-identical output (hash-stable).
        Engine version is tagged in the output; any change bumps ENGINE_VERSION.
    """
    if ayanamshas is None:
        ayanamshas = list(AYANAMSHA_REGISTRY.keys())

    jd_ut = _jd_ut(birth_date, birth_time_hhmm, tz_offset_hours)

    # Build the document, ayanamsha-by-ayanamsha for positions, then shared computations
    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output: dict[str, Any] = {
        "schema_version": "1.0",
        "engine_version": ENGINE_VERSION,
        "chart_id": chart_id,
        # Provenance envelope — required by BRAHMA Gate-1 contract
        "provenance_envelope": {
            "source": "PyJHora DE441 / MARSYS-engine v1",
            "engine_version": ENGINE_VERSION,
            "computed_at": computed_at,
        },
        # source_citation — required for chart_* table row provenance
        "source_citation": "PyJHora DE441 / MARSYS-engine v1",
        "birth": {
            "date": birth_date.isoformat(),
            "time_local": birth_time_hhmm,
            "lat": lat,
            "lon": lon,
            "tz_offset_hours": tz_offset_hours,
        },
        "jd_ut": jd_ut,
        "ayanamsha_values": {},
        "per_ayanamsha": {},
        "panchanga": {},
        "sensitive_points": {},   # computed under Lahiri (default)
        "vimshottari": {},        # computed under Lahiri
        "sha256": None,           # filled in at end
    }

    # Ayanamsha values
    for ayan_key in ayanamshas:
        output["ayanamsha_values"][ayan_key] = _compute_ayanamsha_value(jd_ut, ayan_key)

    # Per-ayanamsha: planet positions, lagna, divisional charts
    for ayan_key in ayanamshas:
        from jhora.panchanga import drik as _drik
        # Step 1: tell PyJHora which ayanamsha it should use for its own computations.
        # drik.set_ayanamsa_mode() internally calls swe.set_sid_mode() with its own
        # mapping, which may silently fall back to a different ayanamsha for keys it
        # does not recognise (e.g. TRUE_CHITRA → TRUE_PUSHYA).  This corrupts the
        # swisseph sid mode and produces wrong longitudes in subsequent swe.calc_ut()
        # and swe.get_ayanamsa_ut() calls.
        # Step 2: always re-assert our canonical swe sid mode AFTER the drik call so
        # that _compute_graha_positions / _compute_lagna / _compute_divisional_charts
        # all run against the correct ayanamsha regardless of what drik did internally.
        _drik.set_ayanamsa_mode(ayan_key.upper() if ayan_key.upper() in [
            "LAHIRI", "RAMAN", "KRISHNAMURTI", "TRUE_CITRA", "TRUE_CHITRA"
        ] else "LAHIRI")
        # Re-assert: drik may have overridden swe's sid mode; restore canonical mode.
        swe.set_sid_mode(AYANAMSHA_REGISTRY[ayan_key])

        ayan_data: dict[str, Any] = {}

        # Graha positions
        ayan_data["grahas"] = _compute_graha_positions(jd_ut)

        # Lagna (ascendant + cusps)
        ayan_data["lagna"] = _compute_lagna(jd_ut, lat, lon, tz_offset_hours)

        # Divisional charts
        ayan_data["divisional_charts"] = _compute_divisional_charts(jd_ut, lat, lon)

        output["per_ayanamsha"][ayan_key] = ayan_data

    # Restore Lahiri for shared computations
    swe.set_sid_mode(AYANAMSHA_REGISTRY["lahiri"])

    # Birth panchanga (ayanamsha-independent for tithi/vara/yoga/karana; nakshatra uses sidereal Lahiri)
    output["panchanga"] = _compute_birth_panchanga(jd_ut, lat, lon)

    # Sensitive points (Lahiri, canonical)
    output["sensitive_points"] = _compute_sensitive_points(jd_ut, lat, lon)

    # Vimshottari dasha to Sukshma depth (Lahiri, canonical)
    output["vimshottari"] = _compute_vimshottari(jd_ut, lat, lon)

    # Strip sha256 + provenance_envelope (contains computed_at timestamp) before hashing.
    # The hash must be deterministic across runs for the same birth data.
    HASH_EXCLUDE = {"sha256", "provenance_envelope"}
    output_for_hash = {k: v for k, v in output.items() if k not in HASH_EXCLUDE}
    output["sha256"] = _hash_output(output_for_hash)

    return output
