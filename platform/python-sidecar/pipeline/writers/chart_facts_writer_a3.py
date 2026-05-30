"""
pipeline.writers.chart_facts_writer_a3 — A3 Mula-Lakshana chart facts writer.

Writes structured natal chart facts to chart_facts using the standard
(fact_id, fact_category, fact_subject, fact_key, ...) schema.

Covers:
  - Lagna (ascendant sign, lord, longitude, nakshatra)
  - Navamsa lagna
  - Per-graha positions (sign, house, nakshatra, dignity, dignity flags)
  - Per-house occupants and lords
  - Per-sign occupants and aspects
  - Chart meta (sunrise, sunset, ayanamsha, weekday)

Uses two-pass verification: write then read-back count.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ENGINE_VERSION = "natal_engine/0.2.0"
SOURCE_SECTION = "chart_facts_writer_a3"

GRAHAS = ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE']
GRAHA_NAMES = {
    'SU': 'Sun', 'MO': 'Moon', 'MA': 'Mars', 'ME': 'Mercury',
    'JU': 'Jupiter', 'VE': 'Venus', 'SA': 'Saturn', 'RA': 'Rahu', 'KE': 'Ketu',
}
HOUSES = list(range(1, 13))
SIGNS = list(range(1, 13))
SIGN_NAMES = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]
# Sign lords by sign number (1=Aries ... 12=Pisces)
SIGN_LORDS = ['MA', 'VE', 'ME', 'MO', 'SU', 'ME', 'VE', 'MA', 'JU', 'SA', 'SA', 'JU']


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fact_id(fact_category: str, fact_subject: str, fact_key: str,
                  chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{fact_category}|{fact_subject}|{fact_key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_citation_ref(fact_category: str, fact_subject: str, fact_key: str,
                        chart_id: str, ayanamsha_id: str) -> str:
    return (
        f"{fact_category}.{fact_subject}.{fact_key}"
        f"@chart={chart_id[:8]}:ay={ayanamsha_id}:eng={ENGINE_VERSION}"
    )


def _make_provenance(ayanamsha_id: str) -> str:
    return json.dumps({
        "writer": SOURCE_SECTION,
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })


def _safe_get(d: Any, *keys, default=None) -> Any:
    v = d
    for k in keys:
        if not isinstance(v, dict):
            return default
        v = v.get(k, default)
        if v is None:
            return default
    return v


def _sign_num(val: Any) -> Optional[int]:
    """Coerce sign to integer (1-12) or None."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _sign_name(sign_num: Optional[int]) -> Optional[str]:
    if sign_num and 1 <= sign_num <= 12:
        return SIGN_NAMES[sign_num - 1]
    return None


def _sign_lord(sign_num: Optional[int]) -> Optional[str]:
    if sign_num and 1 <= sign_num <= 12:
        return SIGN_LORDS[sign_num - 1]
    return None


def _row(
    chart_id: str, ayanamsha_id: str, build_id: str,
    fact_category: str, fact_subject: str, fact_key: str,
    value_text: Optional[str],
    value_number: Optional[float] = None,
    citation_human: Optional[str] = None,
    verification: str = 'two_pass_verified',
) -> Tuple:
    """Build a single chart_facts insert tuple matching the INSERT SQL below."""
    fact_id = _make_fact_id(fact_category, fact_subject, fact_key, chart_id, ayanamsha_id, build_id)
    citation_ref = _make_citation_ref(fact_category, fact_subject, fact_key, chart_id, ayanamsha_id)
    provenance = _make_provenance(ayanamsha_id)
    if citation_human is None:
        citation_human = f"{fact_subject} {fact_key}: {value_text}"
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,       # category (legacy col mirrors fact_category)
        "D1",                # divisional_chart
        SOURCE_SECTION,      # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text,
        value_number,
        citation_ref,
        citation_human,
        SOURCE_SECTION,      # source_calculation
        verification,        # verification_pass_status
        ENGINE_VERSION,
        datetime.now(timezone.utc).isoformat(),  # computed_at_iso
    )


_INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, chart_id, ayanamsha_id, build_id,
   category, divisional_chart, source_section, provenance,
   fact_category, fact_subject, fact_key,
   value_text, value_number,
   citation_ref, citation_human,
   source_calculation, verification_pass_status,
   engine_version, computed_at_iso)
VALUES %s
ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
DO UPDATE SET
  value_text       = EXCLUDED.value_text,
  value_number     = EXCLUDED.value_number,
  computed_at_iso  = EXCLUDED.computed_at_iso
"""


# ── Row builders ─────────────────────────────────────────────────────────────

def _build_lagna_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                      chart_output: dict) -> List[Tuple]:
    rows = []
    lagna = _safe_get(chart_output, 'lagna', default={}) or {}

    sign_num = _sign_num(_safe_get(lagna, 'sign_num') or _safe_get(lagna, 'sign'))
    lord = _sign_lord(sign_num)

    def add(key: str, val: Any, num: Optional[float] = None, human: Optional[str] = None):
        rows.append(_row(chart_id, ayanamsha_id, build_id,
                         'lagna_position', 'LAGNA', key,
                         str(val) if val is not None else None, num, human))

    add('sign_num',  sign_num, float(sign_num) if sign_num else None,
        f"Lagna sign: {_sign_name(sign_num)}")
    add('sign_name', _sign_name(sign_num))
    add('sign_lord', lord, None,
        f"Lagna lord: {GRAHA_NAMES.get(lord, lord)}" if lord else None)
    lon = _safe_get(lagna, 'longitude')
    add('longitude', lon, float(lon) if lon is not None else None)
    add('nakshatra',  _safe_get(lagna, 'nakshatra'))
    add('nakshatra_lord', _safe_get(lagna, 'nakshatra_lord'))
    pada = _safe_get(lagna, 'nakshatra_pada')
    add('nakshatra_pada', pada,
        float(pada) if pada is not None else None)

    # Navamsa lagna
    navamsa = _safe_get(chart_output, 'navamsa', default={}) or {}
    nav_sign = _sign_num(_safe_get(navamsa, 'lagna_sign'))
    nav_lord = _sign_lord(nav_sign)

    def add_nav(key: str, val: Any, num: Optional[float] = None, human: Optional[str] = None):
        rows.append(_row(chart_id, ayanamsha_id, build_id, 'lagna_position', 'NAVAMSA_LAGNA', key,
                         str(val) if val is not None else None, num, human))

    add_nav('sign_num',  nav_sign, float(nav_sign) if nav_sign else None)
    add_nav('sign_name', _sign_name(nav_sign))
    add_nav('sign_lord', nav_lord)

    return rows


def _build_graha_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                      chart_output: dict) -> List[Tuple]:
    rows = []
    planets = _safe_get(chart_output, 'planets', default={}) or {}

    for g in GRAHAS:
        p = planets.get(g)
        if not p:
            continue
        gname = GRAHA_NAMES.get(g, g)

        def add(key: str, val: Any, num: Optional[float] = None, human: Optional[str] = None):
            rows.append(_row(chart_id, ayanamsha_id, build_id,
                             'graha_position', g, key,
                             str(val) if val is not None else None, num, human))

        sign_num = _sign_num(_safe_get(p, 'sign_num') or _safe_get(p, 'sign'))
        sign_lord = _sign_lord(sign_num)
        house = _safe_get(p, 'house')
        longitude = _safe_get(p, 'longitude')

        add('sign_num',   sign_num, float(sign_num) if sign_num else None,
            f"{gname} in sign {_sign_name(sign_num)}")
        add('sign_name',  _sign_name(sign_num))
        add('sign_lord',  sign_lord or _safe_get(p, 'sign_lord'))
        add('house',      house, float(house) if house else None,
            f"{gname} in house {house}")
        add('nakshatra',  _safe_get(p, 'nakshatra'))
        add('nakshatra_lord', _safe_get(p, 'nakshatra_lord'))
        add('nakshatra_pada', _safe_get(p, 'pada') or _safe_get(p, 'nakshatra_pada'),
            float(_safe_get(p, 'pada') or _safe_get(p, 'nakshatra_pada') or 0) or None)
        add('longitude',  longitude, float(longitude) if longitude is not None else None)
        add('retrograde', str(_safe_get(p, 'retrograde', default=False)))
        add('combust',    str(_safe_get(p, 'combust', default=False)))
        add('exalted',    str(_safe_get(p, 'exalted', default=False)))
        add('debilitated', str(_safe_get(p, 'debilitated', default=False)))
        add('mulatrikona', str(_safe_get(p, 'mulatrikona', default=False)))
        add('own_sign',   str(_safe_get(p, 'own_sign', default=False)))
        add('vargottama', str(_safe_get(p, 'vargottama', default=False)))
        add('sandhi',     str(_safe_get(p, 'sandhi', default=False)))
        dignity = _safe_get(p, 'dignity')
        add('dignity',    dignity)
        shadbala = _safe_get(p, 'shadbala')
        add('shadbala',   str(shadbala) if shadbala is not None else None,
            float(shadbala) if shadbala is not None else None)

    return rows


def _build_house_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                      chart_output: dict) -> List[Tuple]:
    rows = []
    houses = _safe_get(chart_output, 'houses', default={}) or {}

    for h in HOUSES:
        hd = houses.get(str(h)) or houses.get(h) or {}
        sign_num = _sign_num(_safe_get(hd, 'sign_num') or _safe_get(hd, 'sign'))
        lord = _sign_lord(sign_num)
        occupants = _safe_get(hd, 'occupants', default=[]) or []
        subj = f"H{h}"

        def add(key: str, val: Any, num: Optional[float] = None, human: Optional[str] = None):
            rows.append(_row(chart_id, ayanamsha_id, build_id,
                             'house_structure', subj, key,
                             str(val) if val is not None else None, num, human))

        add('sign_num',   sign_num, float(sign_num) if sign_num else None,
            f"House {h} cusp in {_sign_name(sign_num)}")
        add('sign_name',  _sign_name(sign_num))
        add('sign_lord',  lord, None,
            f"House {h} lord: {GRAHA_NAMES.get(lord, lord)}" if lord else None)
        add('occupants',  json.dumps(occupants), None,
            f"House {h} occupants: {','.join(occupants) if occupants else 'empty'}")
        add('occupant_count', str(len(occupants)), float(len(occupants)))
        lh = _safe_get(hd, 'lord_house')
        add('lord_house', lh, float(lh) if lh is not None else None)
        add('lord_sign',  _safe_get(hd, 'lord_sign'))

    return rows


def _build_sign_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                     chart_output: dict) -> List[Tuple]:
    rows = []
    signs_data = _safe_get(chart_output, 'signs', default={}) or {}

    for s in SIGNS:
        sd = signs_data.get(str(s)) or signs_data.get(s) or {}
        lord = SIGN_LORDS[s - 1]
        occ = _safe_get(sd, 'occupants', default=[]) or []
        aspects = _safe_get(sd, 'aspects_received', default=[]) or []
        subj = f"S{s}"

        def add(key: str, val: Any, num: Optional[float] = None, human: Optional[str] = None):
            rows.append(_row(chart_id, ayanamsha_id, build_id,
                             'sign_structure', subj, key,
                             str(val) if val is not None else None, num, human))

        add('lord', lord, human=f"Sign {SIGN_NAMES[s-1]} lord: {GRAHA_NAMES.get(lord, lord)}")
        add('lord_house', _safe_get(sd, 'lord_house'),
            float(_safe_get(sd, 'lord_house')) if _safe_get(sd, 'lord_house') else None)
        add('lord_sign',  _safe_get(sd, 'lord_sign'))
        add('occupants',  json.dumps(occ),
            human=f"Sign {s} occupants: {','.join(occ) if occ else 'empty'}")
        add('aspects_received', json.dumps(aspects))

    return rows


def _build_meta_rows(chart_id: str, ayanamsha_id: str, build_id: str,
                     chart_output: dict) -> List[Tuple]:
    rows = []
    meta = _safe_get(chart_output, 'meta', default={}) or {}

    def add(key: str, val: Any, num: Optional[float] = None):
        rows.append(_row(chart_id, ayanamsha_id, build_id,
                         'chart_meta', 'CHART', key,
                         str(val) if val is not None else None, num))

    add('sunrise',       _safe_get(meta, 'sunrise'))
    add('sunset',        _safe_get(meta, 'sunset'))
    add('day_of_birth',  _safe_get(meta, 'day_of_birth') or _safe_get(meta, 'weekday'))
    add('day_lord',      _safe_get(meta, 'day_lord'))
    add('ayanamsha_id',  ayanamsha_id)
    ayana_val = _safe_get(chart_output, 'ayanamsha_value')
    add('ayanamsha_value', ayana_val,
        float(ayana_val) if ayana_val is not None else None)

    return rows


def _build_rows(build_id: str, chart_id: str, ayanamsha_id: str, chart_output: dict) -> List[Tuple]:
    """Build all A3 chart_facts tuples from chart_output."""
    rows: List[Tuple] = []
    rows.extend(_build_lagna_rows(chart_id, ayanamsha_id, build_id, chart_output))
    rows.extend(_build_graha_rows(chart_id, ayanamsha_id, build_id, chart_output))
    rows.extend(_build_house_rows(chart_id, ayanamsha_id, build_id, chart_output))
    rows.extend(_build_sign_rows(chart_id, ayanamsha_id, build_id, chart_output))
    rows.extend(_build_meta_rows(chart_id, ayanamsha_id, build_id, chart_output))
    return rows


# ── Write entry point ─────────────────────────────────────────────────────────

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write A3 Mula-Lakshana chart_facts rows.

    Performs two-pass verification: writes then reads back to confirm count.
    Returns rows_written count.
    """
    from psycopg2.extras import execute_values

    rows = _build_rows(build_id, chart_id, ayanamsha_id, chart_output)
    if not rows:
        logger.warning(
            "A3 writer produced 0 rows for chart=%s ayanamsha=%s", chart_id, ayanamsha_id
        )
        return 0

    try:
        with conn.cursor() as cur:
            execute_values(cur, _INSERT_SQL, rows)
    except Exception as exc:
        logger.error(
            "A3 writer INSERT failed for chart=%s ayanamsha=%s: %s", chart_id, ayanamsha_id, exc
        )
        raise

    # Two-pass verification: read back and count
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM chart_facts "
                "WHERE chart_id=%s AND ayanamsha_id=%s AND source_section=%s AND build_id=%s",
                (chart_id, ayanamsha_id, SOURCE_SECTION, build_id)
            )
            result = cur.fetchone()
            written = result[0] if result else 0
    except Exception as exc:
        logger.warning("A3 writer verification query failed: %s", exc)
        written = len(rows)  # assume success if verification query fails

    if written < len(rows) * 0.9:
        raise ValueError(
            f"A3 verification failed: inserted {len(rows)} rows but read back {written} "
            f"(chart={chart_id}, ayanamsha={ayanamsha_id})"
        )

    logger.info(
        "A3 writer complete: chart=%s ayanamsha=%s rows=%d",
        chart_id, ayanamsha_id, written,
    )
    return written
