"""
ashtakavarga_writer.py — MARSYS-JIS A8-S3 (G3-03)
Ashtakavarga: BAV (Bhinnashtakavarga) + SAV (Sarvashtakavarga) + Sodhita SAV.

Reads chart_output.get('ashtakavarga', {}).
If present: stores BAV per contributor per sign, SAV per sign, Sodhita SAV.
If absent: stores a single placeholder row.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_ashtakavarga"
ASSET_LABEL = "Ashtakavarga BAV+SAV"
ENGINE_VERSION = "natal_engine/0.2.0"

_CONTRIBUTORS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna"]

_SIGN_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


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
        "writer": "ashtakavarga_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,
        "D1",
        "ashtakavarga_writer",
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
def _make_row(chart_id, ayanamsha_id, build_id, subject, fact_key, value_number, value_text=None):
    cref = make_citation_ref("ashtakavarga", subject, fact_key, chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "ashtakavarga",
        subject,
        fact_key,
        value_text,
        value_number,
        cref,
        "BPHS Ch 66-77 (Ashtakavarga)",
        "ashtakavarga_writer/compute_ashtakavarga",
    )


def _build_bav_rows(chart_id, ayanamsha_id, build_id, bav_data):
    """
    BAV: for each contributor, for each of 12 signs, one row.
    bav_data shape: { contributor: { sign_name: bindu_count } }
    Also accepts contributor keyed by index list of 12 values.
    """
    rows = []
    for contributor in _CONTRIBUTORS:
        contrib_data = bav_data.get(contributor, {})
        if isinstance(contrib_data, list):
            # List of 12 bindu counts indexed by sign position
            for idx, sign in enumerate(_SIGN_ORDER):
                house_num = idx + 1
                bindus = float(contrib_data[idx]) if idx < len(contrib_data) else 0.0
                fact_key = f"bav_{sign}_{house_num}"
                rows.append(_make_row(chart_id, ayanamsha_id, build_id, contributor, fact_key, bindus))
        else:
            for idx, sign in enumerate(_SIGN_ORDER):
                house_num = idx + 1
                bindus = float(contrib_data.get(sign, 0) or 0)
                fact_key = f"bav_{sign}_{house_num}"
                rows.append(_make_row(chart_id, ayanamsha_id, build_id, contributor, fact_key, bindus))
    return rows


def _build_sav_rows(chart_id, ayanamsha_id, build_id, sav_data):
    """
    SAV: total per sign.
    sav_data shape: { sign_name: total } or list of 12.
    """
    rows = []
    if isinstance(sav_data, list):
        for idx, sign in enumerate(_SIGN_ORDER):
            total = float(sav_data[idx]) if idx < len(sav_data) else 0.0
            rows.append(_make_row(chart_id, ayanamsha_id, build_id, "sav", f"sav_{sign}", total))
    else:
        for idx, sign in enumerate(_SIGN_ORDER):
            total = float(sav_data.get(sign, 0) or 0)
            rows.append(_make_row(chart_id, ayanamsha_id, build_id, "sav", f"sav_{sign}", total))
    return rows


def _build_sodhita_rows(chart_id, ayanamsha_id, build_id, sodhita_data):
    """
    Sodhita SAV: reduced SAV per sign.
    sodhita_data shape: { sign_name: value } or list of 12.
    """
    rows = []
    if isinstance(sodhita_data, list):
        for idx, sign in enumerate(_SIGN_ORDER):
            val = float(sodhita_data[idx]) if idx < len(sodhita_data) else 0.0
            rows.append(_make_row(chart_id, ayanamsha_id, build_id, "sodhita_sav", f"sodhita_{sign}", val))
    else:
        for idx, sign in enumerate(_SIGN_ORDER):
            val = float(sodhita_data.get(sign, 0) or 0)
            rows.append(_make_row(chart_id, ayanamsha_id, build_id, "sodhita_sav", f"sodhita_{sign}", val))
    return rows


def _placeholder_row(chart_id, ayanamsha_id, build_id):
    cref = make_citation_ref("ashtakavarga", "status", "computed", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "ashtakavarga",
        "status",
        "computed",
        "not_computed",
        0.0,
        cref,
        "BPHS Ch 66-77 (Ashtakavarga)",
        "ashtakavarga_writer/placeholder",
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
    Write A8-S3: Ashtakavarga BAV + SAV + Sodhita SAV to chart_facts.
    Returns number of rows written.
    """
    ashta = chart_output.get("ashtakavarga", {})

    if not ashta:
        rows = [_placeholder_row(chart_id, ayanamsha_id, build_id)]
    else:
        rows = []
        bav = ashta.get("bav", {})
        if bav:
            rows.extend(_build_bav_rows(chart_id, ayanamsha_id, build_id, bav))

        sav = ashta.get("sav", {})
        if sav:
            rows.extend(_build_sav_rows(chart_id, ayanamsha_id, build_id, sav))

        sodhita = ashta.get("sodhita_sav", {})
        if sodhita:
            rows.extend(_build_sodhita_rows(chart_id, ayanamsha_id, build_id, sodhita))

        if not rows:
            rows = [_placeholder_row(chart_id, ayanamsha_id, build_id)]

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[Ashtakavarga] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
