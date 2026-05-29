"""
dosha_register_writer.py — MARSYS-JIS A8-S4 (G3-04, part 2)
Dosha Register: stores doshas with active flag, severity, and constituent planets.

Reads chart_output.get('doshas', []).
If absent, stores a single placeholder row.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A8_dosha_register"
ASSET_LABEL = "Dosha Register"
ENGINE_VERSION = "natal_engine/0.2.0"


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
        "writer": "dosha_register_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,
        "D1",
        "dosha_register_writer",
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
    execute_values(conn, _INSERT_SQL, rows)


def _dosha_subject(dosha_name: str) -> str:
    return dosha_name.lower().replace(" ", "_").replace("-", "_")


def _rows_for_dosha(chart_id, ayanamsha_id, build_id, dosha):
    """
    Build 4 rows per dosha: active, severity, tightness, constituent.
    dosha dict expected keys: name, active (bool), severity (str),
    tightness (float), constituents (list of str), classical_citation (str, opt).
    """
    rows = []
    dosha_name = dosha.get("name", "unknown")
    subject = _dosha_subject(dosha_name)
    is_active = dosha.get("active", False)
    severity = str(dosha.get("severity", "unknown") or "unknown")
    tightness = float(dosha.get("tightness", 0.0) or 0.0)
    constituents = dosha.get("constituents", dosha.get("constituent_planets", []))
    citation = dosha.get("classical_citation", "BPHS dosha chapter")

    # active row
    active_text = "yes" if is_active else "no"
    active_num = 1.0 if is_active else 0.0
    cref = make_citation_ref("dosha_register", subject, "active", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "dosha_register", subject, "active",
        active_text, active_num,
        cref, citation,
        "dosha_register_writer/dosha_active",
    ))

    # severity row
    severity_num_map = {"low": 1.0, "moderate": 2.0, "high": 3.0, "severe": 4.0}
    severity_num = severity_num_map.get(severity.lower(), 0.0)
    cref_s = make_citation_ref("dosha_register", subject, "severity", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "dosha_register", subject, "severity",
        severity, severity_num,
        cref_s, citation,
        "dosha_register_writer/dosha_severity",
    ))

    # tightness row
    cref_t = make_citation_ref("dosha_register", subject, "tightness", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "dosha_register", subject, "tightness",
        None, tightness,
        cref_t, citation,
        "dosha_register_writer/dosha_tightness",
    ))

    # constituent row
    constituent_text = ",".join(str(c) for c in constituents) if constituents else ""
    cref_c = make_citation_ref("dosha_register", subject, "constituent", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "dosha_register", subject, "constituent",
        constituent_text, float(len(constituents)),
        cref_c, citation,
        "dosha_register_writer/dosha_constituent",
    ))

    return rows


def _placeholder_row(chart_id, ayanamsha_id, build_id):
    cref = make_citation_ref("dosha_register", "status", "computed", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "dosha_register", "status", "computed",
        "not_computed", 0.0,
        cref, "BPHS dosha chapter",
        "dosha_register_writer/placeholder",
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
    Write A8-S4 (dosha register): dosha active/severity/tightness/constituent rows
    to chart_facts.  Returns number of rows written.
    """
    doshas = chart_output.get("doshas", [])

    if not doshas:
        rows = [_placeholder_row(chart_id, ayanamsha_id, build_id)]
    else:
        rows = []
        for dosha in doshas:
            rows.extend(_rows_for_dosha(chart_id, ayanamsha_id, build_id, dosha))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[DoshaRegister] %s: %d rows written from %d doshas (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), len(doshas) if doshas else 0,
        chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
