"""
yoga_register_writer.py — MARSYS-JIS A8-S4 (G3-04, part 1)
Yoga Register: stores active/inactive yogas with tightness and constituent planets.

Reads chart_output.get('yogas', []).
If absent, stores a single placeholder row.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_yoga_register"
ASSET_LABEL = "Yoga Register"
ENGINE_VERSION = "pyjhora/1.0.0"


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
        "writer": "yoga_register_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,
        "D1",
        "yoga_register_writer",
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
def _yoga_subject(yoga_name: str) -> str:
    return yoga_name.lower().replace(" ", "_").replace("-", "_")


def _rows_for_yoga(chart_id, ayanamsha_id, build_id, yoga):
    """
    Build 3 rows per yoga: active, tightness, constituent.
    yoga dict expected keys: name, active (bool), tightness (float),
    constituents (list of str), classical_citation (str, optional).
    """
    rows = []
    yoga_name = yoga.get("name", "unknown")
    subject = _yoga_subject(yoga_name)
    is_active = yoga.get("active", False)
    tightness = float(yoga.get("tightness", 0.0) or 0.0)
    constituents = yoga.get("constituents", yoga.get("constituent_planets", []))
    citation = yoga.get("classical_citation", "G12 library")

    # active row
    active_text = "yes" if is_active else "no"
    active_num = 1.0 if is_active else 0.0
    cref = make_citation_ref("yoga_register", subject, "active", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "yoga_register", subject, "active",
        active_text, active_num,
        cref, citation,
        "yoga_register_writer/yoga_active",
    ))

    # tightness row
    cref_t = make_citation_ref("yoga_register", subject, "tightness", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "yoga_register", subject, "tightness",
        None, tightness,
        cref_t, citation,
        "yoga_register_writer/yoga_tightness",
    ))

    # constituent row
    constituent_text = ",".join(str(c) for c in constituents) if constituents else ""
    cref_c = make_citation_ref("yoga_register", subject, "constituent", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "yoga_register", subject, "constituent",
        constituent_text, float(len(constituents)),
        cref_c, citation,
        "yoga_register_writer/yoga_constituent",
    ))

    return rows


def _placeholder_row(chart_id, ayanamsha_id, build_id):
    cref = make_citation_ref("yoga_register", "status", "computed", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "yoga_register", "status", "computed",
        "not_computed", 0.0,
        cref, "G12 library",
        "yoga_register_writer/placeholder",
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
    Write A8-S4 (yoga register): yoga active/tightness/constituent rows
    to chart_facts.  Returns number of rows written.
    """
    yogas = chart_output.get("yogas", [])

    if not yogas:
        rows = [_placeholder_row(chart_id, ayanamsha_id, build_id)]
    else:
        rows = []
        for yoga in yogas:
            rows.extend(_rows_for_yoga(chart_id, ayanamsha_id, build_id, yoga))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[YogaRegister] %s: %d rows written from %d yogas (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), len(yogas) if yogas else 0,
        chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
