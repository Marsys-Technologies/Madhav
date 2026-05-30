"""
vimsopaka_writer.py — MARSYS-JIS A8-S5 (G3-05)
Vimsopaka Bala + Avastha schemes.

Vimsopaka: per graha, 4 varga groups:
  saptavarga (7-varga), dashavarga (10-varga), shadvarga (6-varga),
  shodasavarga (16-varga).
  fact_category='vimsopaka'

Avasthas: per graha, per scheme:
  baladi, jagradadi, deeptadi, lajjitadi, shayanaadi.
  fact_category='avastha'

Citation: 'BPHS Ch 45-53 (avasthas)'
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_vimsopaka"
ASSET_LABEL = "Vimsopaka + Avastha"
ENGINE_VERSION = "natal_engine/0.2.0"

_ALL_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

_VARGA_GROUPS = ["saptavarga", "dashavarga", "shadvarga", "shodasavarga"]

_AVASTHA_SCHEMES = ["baladi", "jagradadi", "deeptadi", "lajjitadi", "shayanaadi"]


# ── Row helpers ───────────────────────────────────────────────────────────────

def make_fact_id(category, subject, key, chart_id, ayanamsha_id, build_id):
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_citation_ref(category, subject, key, chart_id, ayanamsha_id):
    return (
        f"{category}.{subject}.{key}"
        f"@chart={chart_id[:8]}"
        f":ay={ayanamsha_id}"
        f":eng={ENGINE_VERSION}"
    )


def _row(
    chart_id, ayanamsha_id, build_id,
    fact_category, fact_subject, fact_key,
    value_text, value_number,
    citation_ref, citation_human,
    source_calc,
):
    fact_id = make_fact_id(fact_category, fact_subject, fact_key, chart_id, ayanamsha_id, build_id)
    provenance = json.dumps({
        "writer": "vimsopaka_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,
        "D1",
        "vimsopaka_writer",
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",
        ENGINE_VERSION,
        datetime.now(timezone.utc).isoformat(),
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
  value_text = EXCLUDED.value_text,
  value_number = EXCLUDED.value_number,
  computed_at_iso = EXCLUDED.computed_at_iso
"""


def _upsert_chart_facts(conn, rows):
    from psycopg2.extras import execute_values
    with conn.cursor() as _cur:
        execute_values(_cur, _INSERT_SQL, rows)
# ── Vimsopaka computation ─────────────────────────────────────────────────────

def _build_vimsopaka_rows(chart_id, ayanamsha_id, build_id, vimsopaka_data):
    """
    vimsopaka_data shape:
    { graha: { saptavarga: score, dashavarga: score, shadvarga: score, shodasavarga: score } }
    """
    rows = []
    for graha in _ALL_GRAHAS:
        graha_data = vimsopaka_data.get(graha, {})
        for varga_group in _VARGA_GROUPS:
            score = float(graha_data.get(varga_group, 0.0) or 0.0)
            cref = make_citation_ref("vimsopaka", graha, varga_group, chart_id, ayanamsha_id)
            rows.append(_row(
                chart_id, ayanamsha_id, build_id,
                "vimsopaka",
                graha,
                varga_group,
                None, score,
                cref,
                "BPHS Ch 45-53 (avasthas)",
                "vimsopaka_writer/vimsopaka_score",
            ))
    return rows


# ── Avastha computation ───────────────────────────────────────────────────────

def _build_avastha_rows(chart_id, ayanamsha_id, build_id, avastha_data):
    """
    avastha_data shape:
    { graha: { baladi: 'bala', jagradadi: 'jagrad', deeptadi: 'deetha',
               lajjitadi: 'lajjita', shayanaadi: 'shayana' } }
    """
    rows = []
    for graha in _ALL_GRAHAS:
        graha_data = avastha_data.get(graha, {})
        for scheme in _AVASTHA_SCHEMES:
            avastha_name = str(graha_data.get(scheme, "") or "")
            cref = make_citation_ref("avastha", graha, scheme, chart_id, ayanamsha_id)
            rows.append(_row(
                chart_id, ayanamsha_id, build_id,
                "avastha",
                graha,
                scheme,
                avastha_name if avastha_name else None,
                None,
                cref,
                "BPHS Ch 45-53 (avasthas)",
                "vimsopaka_writer/avastha_scheme",
            ))
    return rows


def _vimsopaka_placeholder(chart_id, ayanamsha_id, build_id):
    cref = make_citation_ref("vimsopaka", "status", "computed", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "vimsopaka", "status", "computed",
        "not_computed", 0.0,
        cref, "BPHS Ch 45-53 (avasthas)",
        "vimsopaka_writer/placeholder",
    )


def _avastha_placeholder(chart_id, ayanamsha_id, build_id):
    cref = make_citation_ref("avastha", "status", "computed", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "avastha", "status", "computed",
        "not_computed", 0.0,
        cref, "BPHS Ch 45-53 (avasthas)",
        "vimsopaka_writer/avastha_placeholder",
    )


# ── Public entry point ────────────────────────────────────────────────────────

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write A8-S5: Vimsopaka Bala (4 varga groups) + Avastha (5 schemes) to chart_facts.
    Returns number of rows written.
    """
    vimsopaka_data = chart_output.get("vimsopaka", {})
    avastha_data = chart_output.get("avasthas", {})

    rows = []

    if vimsopaka_data:
        rows.extend(_build_vimsopaka_rows(chart_id, ayanamsha_id, build_id, vimsopaka_data))
    else:
        rows.append(_vimsopaka_placeholder(chart_id, ayanamsha_id, build_id))

    if avastha_data:
        rows.extend(_build_avastha_rows(chart_id, ayanamsha_id, build_id, avastha_data))
    else:
        rows.append(_avastha_placeholder(chart_id, ayanamsha_id, build_id))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[Vimsopaka] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
