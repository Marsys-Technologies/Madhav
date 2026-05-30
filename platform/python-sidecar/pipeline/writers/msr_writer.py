"""
msr_writer.py — MARSYS-JIS A10 MSR Signal Store writer [G4-02]
Writes MSR signals from chart_output to chart_facts with fact_category='msr_signal'.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A10_msr"
ASSET_LABEL = "MSR Signal Store"
ENGINE_VERSION = "natal_engine/0.2.0"


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
        "writer": "msr_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,      # category (legacy col)
        "D1",               # divisional_chart
        "msr_writer",       # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",           # verification_pass_status
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


def _build_signal_row(chart_id, ayanamsha_id, build_id, signal, index):
    """Build a single chart_facts row from an MSR signal dict."""
    fact_subject = signal.get("signal_type", "unknown")
    fact_key = signal.get("signal_id", f"sig_{index}")
    value_text = signal.get("configuration", "")
    value_number = float(signal.get("computed_salience", 0.0) or 0.0)
    citation_human = signal.get("primary_citation", "G12 library")

    cref = make_citation_ref("msr_signal", fact_subject, fact_key, chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "msr_signal",
        fact_subject,
        fact_key,
        value_text,
        value_number,
        cref,
        citation_human,
        "msr_writer/write_signal",
    )


def _build_placeholder_row(chart_id, ayanamsha_id, build_id):
    """Build a placeholder row when msr_signals are absent."""
    cref = make_citation_ref("msr_signal", "status", "status", chart_id, ayanamsha_id)
    return _row(
        chart_id, ayanamsha_id, build_id,
        "msr_signal",
        "status",
        "status",
        "msr_not_computed",
        0.0,
        cref,
        "G12 library",
        "msr_writer/placeholder",
    )


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write MSR signals from chart_output to chart_facts.
    Reads chart_output.get('msr_signals', []) — if absent, writes placeholder.
    Returns number of rows written.
    """
    signals = chart_output.get("msr_signals")

    if not signals:
        # No signals — write placeholder
        rows = [_build_placeholder_row(chart_id, ayanamsha_id, build_id)]
    else:
        rows = [
            _build_signal_row(chart_id, ayanamsha_id, build_id, sig, i)
            for i, sig in enumerate(signals)
        ]

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[MSR] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
