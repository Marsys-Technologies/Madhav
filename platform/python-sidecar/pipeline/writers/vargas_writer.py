"""
vargas_writer.py — MARSYS-JIS A6 Varga Divisional Charts writer
A6-S1: 16 Parashari vargas (D1-D60)
A6-S2: 11 supplementary vargas (D5/D6/D8/D11/D14/D15/D21/D32/D33/D50/D54)
A6-S3: 3 Nadi vargas (D108/D150/D2700)

For each (graha, varga), writes to chart_facts:
- fact_category: "varga"
- divisional_chart: "D{N}" (e.g. "D9")
- fact_subject: graha name (e.g. "SUN")
- fact_key: "sign" | "sign_id" | "lord" | "vargottama" (D9 only)

Classical sources: BPHS Ch. 6–7; varga_formulas.py formula reference.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A6_vargas"
ASSET_LABEL = "Varga Divisional Charts"
ENGINE_VERSION = "natal_engine/0.2.0"

# ---------------------------------------------------------------------------
# Sign tables (1-indexed, Aries=1)
# ---------------------------------------------------------------------------

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = {
    "Aries": "Mars",       "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn",  "Pisces": "Jupiter",
}

# Element sets (0-indexed sign indices)
_FIRE  = {0, 4, 8}   # Aries, Leo, Sagittarius
_EARTH = {1, 5, 9}   # Taurus, Virgo, Capricorn
_AIR   = {2, 6, 10}  # Gemini, Libra, Aquarius
_WATER = {3, 7, 11}  # Cancer, Scorpio, Pisces

# Modality sets (0-indexed sign indices)
_MOVABLE = {0, 3, 6, 9}   # Aries, Cancer, Libra, Capricorn
_FIXED   = {1, 4, 7, 10}  # Taurus, Leo, Scorpio, Aquarius
_DUAL    = {2, 5, 8, 11}  # Gemini, Virgo, Sagittarius, Pisces

# D5 Panchamsa fixed sequences per parity (0-indexed sections → 0-indexed sign)
_D5_ODD  = [0, 10, 8, 2, 6]    # Aries, Aquarius, Sagittarius, Gemini, Libra
_D5_EVEN = [1, 5, 11, 9, 7]    # Taurus, Virgo, Pisces, Capricorn, Scorpio

# D30 Trimsamsa — unequal boundaries for odd signs
# (boundary_degrees_exclusive, result_sign_0indexed)
_D30_ODD = [
    (5,  0),   # Mars → Aries  (0-4.999°)
    (10, 10),  # Saturn → Aquarius  (5-9.999°)
    (18, 8),   # Jupiter → Sagittarius  (10-17.999°)
    (25, 2),   # Mercury → Gemini  (18-24.999°)
    (30, 6),   # Venus → Libra  (25-29.999°)
]
_D30_EVEN = [
    (5,  1),   # Venus → Taurus
    (12, 5),   # Mercury → Virgo
    (20, 11),  # Jupiter → Pisces
    (25, 9),   # Saturn → Capricorn
    (30, 7),   # Mars → Scorpio
]

# ---------------------------------------------------------------------------
# Varga lists per session scope
# ---------------------------------------------------------------------------

PARASHARI_VARGAS     = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
SUPPLEMENTARY_VARGAS = [5, 6, 8, 11, 14, 15, 21, 32, 33, 50, 54]
NADI_VARGAS          = [108, 150, 2700]

ALL_VARGAS = PARASHARI_VARGAS + SUPPLEMENTARY_VARGAS + NADI_VARGAS


# ---------------------------------------------------------------------------
# Helper: sign_name / sign_lord (1-indexed)
# ---------------------------------------------------------------------------

def sign_name(sign_id: int) -> str:
    """Return sign name from 1-indexed sign_id."""
    return SIGN_NAMES[(sign_id - 1) % 12]


def sign_lord(sign_id: int) -> str:
    """Return sign lord from 1-indexed sign_id."""
    return SIGN_LORDS[sign_name(sign_id)]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_varga_sign_id(natal_lon: float, divisor: int) -> int:
    """
    Compute varga sign_id (1-indexed, 1=Aries) from natal sidereal longitude
    and varga divisor.

    Uses classical Parashari rules per BPHS Ch. 6–7 and varga_formulas.py.

    Args:
        natal_lon: Sidereal longitude 0.0–359.999°
        divisor:   Varga D-number (1, 2, 3, …, 2700)

    Returns:
        sign_id: int 1–12 (1=Aries, 12=Pisces)
    """
    # 0-indexed natal sign (0=Aries … 11=Pisces)
    rasi_idx = int(natal_lon / 30.0) % 12
    degree_in_sign = natal_lon % 30.0

    # ------------------------------------------------------------------ D1
    if divisor == 1:
        return rasi_idx + 1

    # ------------------------------------------------------------------ D2 Hora
    if divisor == 2:
        # Odd signs (0-indexed even: 0,2,4,6,8,10): 0-15 → Leo(5), 15-30 → Cancer(4)
        # Even signs (0-indexed odd: 1,3,5,7,9,11): 0-15 → Cancer(4), 15-30 → Leo(5)
        if rasi_idx % 2 == 0:  # classical odd sign
            return 5 if degree_in_sign < 15.0 else 4
        else:                   # classical even sign
            return 4 if degree_in_sign < 15.0 else 5

    # ------------------------------------------------------------------ D3 Drekkana
    if divisor == 3:
        part = min(int(degree_in_sign / 10.0), 2)
        return (rasi_idx + part * 4) % 12 + 1

    # ------------------------------------------------------------------ D4 Chaturthamsa
    if divisor == 4:
        part = min(int(degree_in_sign / 7.5), 3)
        # Each modality has its own cardinal start sign (0-indexed)
        if rasi_idx in _MOVABLE:
            start = 0   # Aries
        elif rasi_idx in _FIXED:
            start = 1   # Taurus
        else:
            start = 2   # Gemini
        # The four parts step by 3 signs (cardinal/fixed/dual quarters)
        return (start + part * 3) % 12 + 1

    # ------------------------------------------------------------------ D5 Panchamsa
    if divisor == 5:
        part = min(int(degree_in_sign / 6.0), 4)
        seq = _D5_ODD if rasi_idx % 2 == 0 else _D5_EVEN
        return seq[part] + 1  # 0-indexed → 1-indexed

    # ------------------------------------------------------------------ D6 Shashtamsa
    if divisor == 6:
        part = min(int(degree_in_sign / 5.0), 5)
        start = 0 if rasi_idx % 2 == 0 else 6   # Aries or Libra
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D7 Saptamsa
    if divisor == 7:
        part = min(int(degree_in_sign / (30.0 / 7)), 6)
        # Odd signs (0-indexed even) → from Aries (0); even signs → from Libra (6)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D8 Ashtamsa
    if divisor == 8:
        part = min(int(degree_in_sign / 3.75), 7)
        # Element start: Fire→Aries(0), Earth→Cap(9), Air→Libra(6), Water→Cancer(3)
        if rasi_idx in _FIRE:
            start = 0
        elif rasi_idx in _EARTH:
            start = 9
        elif rasi_idx in _AIR:
            start = 6
        else:
            start = 3
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D9 Navamsa
    if divisor == 9:
        _nav_start = {
            0: 0, 4: 0, 8: 0,    # fire → Aries
            1: 9, 5: 9, 9: 9,    # earth → Capricorn
            2: 6, 6: 6, 10: 6,   # air → Libra
            3: 3, 7: 3, 11: 3,   # water → Cancer
        }
        part = min(int(degree_in_sign / (30.0 / 9)), 8)
        return (_nav_start[rasi_idx] + part) % 12 + 1

    # ------------------------------------------------------------------ D10 Dasamsa
    if divisor == 10:
        part = min(int(degree_in_sign / 3.0), 9)
        # 0-indexed even = classical odd → Aries start; 0-indexed odd → Capricorn(9)
        start = 0 if rasi_idx % 2 == 0 else 9
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D11 Rudramsa
    if divisor == 11:
        part = min(int(degree_in_sign / (30.0 / 11)), 10)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D12 Dvadasamsa
    if divisor == 12:
        part = min(int(degree_in_sign / 2.5), 11)
        return (rasi_idx + part) % 12 + 1

    # ------------------------------------------------------------------ D14 Chaturdamsa
    if divisor == 14:
        part = min(int(degree_in_sign / (30.0 / 14)), 13)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D15 Vimsamsa (15th)
    if divisor == 15:
        part = min(int(degree_in_sign / 2.0), 14)
        if rasi_idx in _MOVABLE:
            start = 0   # Aries
        elif rasi_idx in _FIXED:
            start = 8   # Sagittarius
        else:
            start = 4   # Leo
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D16 Shodasamsa
    if divisor == 16:
        part = min(int(degree_in_sign / (30.0 / 16)), 15)
        if rasi_idx in _MOVABLE:
            start = 0   # Aries
        elif rasi_idx in _FIXED:
            start = 4   # Leo
        else:
            start = 8   # Sagittarius
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D20 Vimsamsa (20th)
    if divisor == 20:
        part = min(int(degree_in_sign / 1.5), 19)
        if rasi_idx in _MOVABLE:
            start = 0   # Aries
        elif rasi_idx in _FIXED:
            start = 4   # Leo
        else:
            start = 8   # Sagittarius
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D21 Ekavimshamsa
    if divisor == 21:
        part = min(int(degree_in_sign / (30.0 / 21)), 20)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D24 Chaturvimsamsa (Siddhamsa)
    if divisor == 24:
        part = min(int(degree_in_sign / 1.25), 23)
        # Odd signs (0-indexed even) → Leo (4); even signs → Cancer (3)
        start = 4 if rasi_idx % 2 == 0 else 3
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D27 Nakshatramsa (Bhamsa)
    if divisor == 27:
        part = min(int(degree_in_sign / (30.0 / 27)), 26)
        if rasi_idx in _FIRE:
            start = 0   # Aries
        elif rasi_idx in _EARTH:
            start = 3   # Cancer
        elif rasi_idx in _AIR:
            start = 6   # Libra
        else:
            start = 9   # Capricorn
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D30 Trimsamsa
    if divisor == 30:
        boundaries = _D30_ODD if rasi_idx % 2 == 0 else _D30_EVEN
        for (limit, result_idx) in boundaries:
            if degree_in_sign < limit:
                return result_idx + 1
        # Fallback to last entry
        return boundaries[-1][1] + 1

    # ------------------------------------------------------------------ D32 Dvatrinshamsa
    if divisor == 32:
        part = min(int(degree_in_sign / (30.0 / 32)), 31)
        start = 0 if rasi_idx % 2 == 0 else 4   # Aries or Leo
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D33 Tritrimshamsa
    if divisor == 33:
        part = min(int(degree_in_sign / (30.0 / 33)), 32)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D40 Chatvarimsamsa
    if divisor == 40:
        part = min(int(degree_in_sign / 0.75), 39)
        start = 0 if rasi_idx % 2 == 0 else 6   # Aries or Libra
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D45 Akshavedamsa
    if divisor == 45:
        part = min(int(degree_in_sign / (30.0 / 45)), 44)
        if rasi_idx in _MOVABLE:
            start = 0   # Aries
        elif rasi_idx in _FIXED:
            start = 4   # Leo
        else:
            start = 8   # Sagittarius
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D50 Panchasat
    if divisor == 50:
        part = min(int(degree_in_sign / 0.6), 49)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D54 Chaturasubhamsa
    if divisor == 54:
        part = min(int(degree_in_sign / (30.0 / 54)), 53)
        if rasi_idx in _MOVABLE:
            start = 0
        elif rasi_idx in _FIXED:
            start = 4
        else:
            start = 8
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D60 Shashtiamsa
    if divisor == 60:
        part = min(int(degree_in_sign / 0.5), 59)
        start = 0 if rasi_idx % 2 == 0 else 6
        return (start + part) % 12 + 1

    # ------------------------------------------------------------------ D108 Ashtottaramsa (Nadi)
    if divisor == 108:
        part = min(int(degree_in_sign / (30.0 / 108)), 107)
        # Formula: (rasi_index * 9 + part) % 12
        return (rasi_idx * 9 + part) % 12 + 1

    # ------------------------------------------------------------------ D150 Rishi Nadi
    if divisor == 150:
        part = min(int(degree_in_sign / 0.2), 149)
        # Compound: start from navamsa position for this sign, then panchamsa offset
        _nav_start = {
            0: 0, 4: 0, 8: 0,
            1: 9, 5: 9, 9: 9,
            2: 6, 6: 6, 10: 6,
            3: 3, 7: 3, 11: 3,
        }
        nav_part = min(int(degree_in_sign / (30.0 / 9)), 8)
        nav_sign = (_nav_start[rasi_idx] + nav_part) % 12
        # Sub-divide each navamsa into 5 panchamsa parts
        panch_part = part % 5
        return (nav_sign * 5 + panch_part) % 12 + 1

    # ------------------------------------------------------------------ D2700 Sub-Rishi Nadi
    if divisor == 2700:
        part = min(int(degree_in_sign / (30.0 / 2700)), 2699)
        return part % 12 + 1

    # ------------------------------------------------------------------ Generic fallback
    # For any unrecognised divisor, use simple equal-division from natal sign
    part = min(int(degree_in_sign / (30.0 / divisor)), divisor - 1)
    return (rasi_idx + part) % 12 + 1


def is_vargottama(natal_lon: float) -> bool:
    """True when D1 sign == D9 sign (planet in same sign in rasi and navamsa)."""
    d1 = int(natal_lon / 30.0) % 12 + 1
    d9 = compute_varga_sign_id(natal_lon, 9)
    return d1 == d9


# ---------------------------------------------------------------------------
# fact_id helper
# ---------------------------------------------------------------------------

def _make_fact_id(
    category: str,
    divisional_chart: str,
    subject: str,
    key: str,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
) -> str:
    raw = f"{category}|{divisional_chart}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Public write()
# ---------------------------------------------------------------------------

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write varga (divisional chart) data to chart_facts.

    Covers all 30 vargas across A6-S1 (Parashari), A6-S2 (supplementary),
    A6-S3 (Nadi).  For each (graha, varga) emits fact rows:
        sign, sign_id, lord        — for every varga
        vargottama                 — for D9 only

    Returns:
        rows_written (int) — 0 if chart_output has no grahas (stub-safe)
    """
    grahas = chart_output.get("grahas", [])
    if not grahas:
        return 0

    rows = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for graha in grahas:
        planet_name = graha["name"].upper()
        natal_lon = float(graha["longitude_deg"])

        # Pre-computed varga positions from the engine (D1, D9, D10 typically)
        pre_computed: dict = graha.get("varga_position", {})

        for divisor in ALL_VARGAS:
            div_key = f"D{divisor}"

            # Use engine-pre-computed value if available; otherwise compute
            if div_key in pre_computed:
                pc = pre_computed[div_key]
                # Engine may give sign_index (0-indexed) or sign_id (1-indexed)
                raw_idx = pc.get("sign_index")
                if raw_idx is None:
                    raw_idx = pc.get("sign_id")
                if raw_idx is not None:
                    # Normalise: if 0, interpret as Pisces (12) — 0-indexed Aries would be 0
                    # We accept both 0-indexed and 1-indexed from engine:
                    # sign_index is typically 0-indexed; if it's 0 it might mean Aries(1)
                    # The safe approach: use our compute for verification parity unless
                    # explicitly 1-indexed.
                    # Convention: engine sign_index is 0-indexed (0=Aries); +1 → 1-indexed
                    sid = (int(raw_idx) % 12) + 1
                else:
                    sid = compute_varga_sign_id(natal_lon, divisor)
            else:
                sid = compute_varga_sign_id(natal_lon, divisor)

            varga_sign = sign_name(sid)
            varga_lord = sign_lord(sid)
            vargottama = is_vargottama(natal_lon) if divisor == 9 else False

            provenance = {
                "writer": "vargas_writer_a6",
                "engine_version": ENGINE_VERSION,
                "divisor": divisor,
                "pre_computed": div_key in pre_computed,
            }

            def _row(key: str, val_text: str, val_num) -> dict:  # noqa: E306
                return {
                    "fact_id": _make_fact_id(
                        "varga", div_key, planet_name, key,
                        chart_id, ayanamsha_id, build_id,
                    ),
                    "chart_id": chart_id,
                    "ayanamsha_id": ayanamsha_id,
                    "build_id": build_id,
                    "category": "varga",
                    "divisional_chart": div_key,
                    "source_section": "vargas_writer_a6",
                    "provenance": provenance,
                    "fact_category": "varga",
                    "fact_subject": planet_name,
                    "fact_key": key,
                    "value_text": val_text,
                    "value_number": val_num,
                    "citation_ref": (
                        f"varga.{div_key}.{planet_name}.{key}"
                        f"@chart={chart_id[:8]}:ay={ayanamsha_id}"
                    ),
                    "citation_human": (
                        f"{planet_name} {key}={val_text} in {div_key} ({ayanamsha_id})"
                    ),
                    "source_calculation": "vargas_writer_a6/compute_varga_sign_id",
                    "verification_pass_status": "single",
                    "engine_version": ENGINE_VERSION,
                    "computed_at_iso": now_iso,
                    "unit": "",
                }

            rows.append(_row("sign",    varga_sign,    None))
            rows.append(_row("sign_id", str(sid),      float(sid)))
            rows.append(_row("lord",    varga_lord,    None))

            if divisor == 9:
                rows.append(_row("vargottama", str(vargottama), float(vargottama)))

    if not rows:
        return 0

    # Batch insert — no-op when conn is None (test / dry-run mode)
    if conn is None:
        logger.info(
            "[DRY-RUN] %s: chart=%s ayanamsha=%s build=%s rows=%d",
            ASSET_LABEL, chart_id, ayanamsha_id, build_id, len(rows),
        )
        return len(rows)

    try:
        import psycopg2.extras  # type: ignore

        sql = """
            INSERT INTO chart_facts (
                fact_id, chart_id, ayanamsha_id, build_id,
                category, divisional_chart, source_section, provenance,
                fact_category, fact_subject, fact_key,
                value_text, value_number,
                citation_ref, citation_human,
                source_calculation, verification_pass_status,
                engine_version, computed_at_iso, unit
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """

        data = [
            (
                r["fact_id"],      r["chart_id"],   r["ayanamsha_id"], r["build_id"],
                r["category"],     r["divisional_chart"], r["source_section"],
                json.dumps(r["provenance"]),
                r["fact_category"], r["fact_subject"], r["fact_key"],
                r["value_text"],   r["value_number"],
                r["citation_ref"], r["citation_human"],
                r["source_calculation"], r["verification_pass_status"],
                r["engine_version"], r["computed_at_iso"], r["unit"],
            )
            for r in rows
        ]

        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, data, page_size=500)

        logger.info(
            "%s: chart=%s ayanamsha=%s build=%s rows_written=%d",
            ASSET_LABEL, chart_id, ayanamsha_id, build_id, len(rows),
        )
    except Exception:
        logger.exception(
            "vargas_writer: DB write failed chart=%s ayanamsha=%s",
            chart_id, ayanamsha_id,
        )
        raise

    return len(rows)
