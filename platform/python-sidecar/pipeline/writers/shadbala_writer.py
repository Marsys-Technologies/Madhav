"""
shadbala_writer.py — MARSYS-JIS A8-S2 (G3-02)
Shadbala: 6 sub-balas per graha stored as chart_facts rows.

If chart_output['shadbala'] is present, stores the 6 computed sub-balas
(sthana_bala, dig_bala, kala_bala, chesta_bala, naisargika_bala, drik_bala)
plus derived rows (total_shadbala, required_shadbala, shadbala_ratio).

If absent, uses NAISARGIKA_BALA constants for naisargika_bala only and
zeros elsewhere.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_shadbala"
ASSET_LABEL = "Shadbala 6 Sub-Balas"
ENGINE_VERSION = "pyjhora/1.0.0"

# ── Naisargika (natural) Bala constants — BPHS Ch 27 ─────────────────────────
NAISARGIKA_BALA = {
    "sun":     60.0,
    "moon":    51.43,
    "mars":    17.14,
    "mercury": 25.71,
    "jupiter": 34.29,
    "venus":   42.86,
    "saturn":  8.57,
    "rahu":    0.0,
    "ketu":    0.0,
}

# ── Required Shadbala (Rupas) — classical minima, BPHS Ch 28 ─────────────────
REQUIRED_SHADBALA = {
    "sun":     390.0,
    "moon":    360.0,
    "mars":    300.0,
    "mercury": 420.0,
    "jupiter": 390.0,
    "venus":   330.0,
    "saturn":  300.0,
    "rahu":    0.0,
    "ketu":    0.0,
}

_ALL_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


# ── Row helpers (mirror t1_structural_writer pattern) ─────────────────────────

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
        "writer": "shadbala_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,          # category (legacy col)
        "D1",                   # divisional_chart
        "shadbala_writer",      # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",               # verification_pass_status
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
def _make_row(chart_id, ayanamsha_id, build_id, graha, fact_key, value_number, value_text=None):
    cref = make_citation_ref("shadbala", graha, fact_key, chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "shadbala",
        graha,
        fact_key,
        value_text,
        value_number,
        cref,
        "BPHS Ch 27-28",
        "shadbala_writer/compute_shadbala",
    )


def _rows_for_graha(chart_id, ayanamsha_id, build_id, graha, bala_data):
    """
    Build all sub-bala rows for a single graha.
    bala_data is a dict with keys: sthana_bala, dig_bala, kala_bala,
    chesta_bala, drik_bala.  naisargika_bala comes from constants.
    """
    rows = []

    sthana   = float(bala_data.get("sthana_bala",  0) or 0)
    dig      = float(bala_data.get("dig_bala",     0) or 0)
    kala     = float(bala_data.get("kala_bala",    0) or 0)
    chesta   = float(bala_data.get("chesta_bala",  0) or 0)
    drik     = float(bala_data.get("drik_bala",    0) or 0)
    naisargika = NAISARGIKA_BALA.get(graha, 0.0)
    required   = REQUIRED_SHADBALA.get(graha, 0.0)
    total      = sthana + dig + kala + chesta + naisargika + drik
    ratio      = (total / required) if required > 0 else 0.0

    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "sthana_bala",      sthana))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "dig_bala",         dig))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "kala_bala",        kala))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "chesta_bala",      chesta))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "naisargika_bala",  naisargika))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "drik_bala",        drik))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "total_shadbala",   total))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "required_shadbala", required))
    rows.append(_make_row(chart_id, ayanamsha_id, build_id, graha, "shadbala_ratio",   round(ratio, 6)))

    return rows


def _build_rows(chart_id, ayanamsha_id, build_id, shadbala_data):
    rows = []
    for graha in _ALL_GRAHAS:
        bala = shadbala_data.get(graha, {}) if shadbala_data else {}
        rows.extend(_rows_for_graha(chart_id, ayanamsha_id, build_id, graha, bala))
    return rows


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
    Write A8-S2: Shadbala 6 sub-balas + derived rows to chart_facts.
    Returns the number of rows written.

    If chart_output['shadbala'] is absent, naisargika_bala uses constants
    and all other sub-balas default to 0.
    """
    shadbala_data = chart_output.get("shadbala", {})

    rows = _build_rows(chart_id, ayanamsha_id, build_id, shadbala_data)

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[Shadbala] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
