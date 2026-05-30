"""
cdlm_writer.py — MARSYS-JIS A11 CDLM Cross-Domain Links writer [G4-04]
9×9 domain linkage matrix stored as chart_facts rows with fact_category='cdlm'.
"""
import hashlib
import json
import logging
import math
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A11_cdlm"
ASSET_LABEL = "CDLM Cross-Domain Links"
ENGINE_VERSION = "natal_engine/0.2.0"

DOMAINS = [
    "career",
    "relationships",
    "health",
    "wealth",
    "family",
    "learning",
    "spirituality",
    "longevity",
    "character",
]


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
        "writer": "cdlm_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,      # category (legacy col)
        "D1",               # divisional_chart
        "cdlm_writer",      # source_section
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


def _count_signals_per_domain(msr_signals: list) -> dict:
    """Count how many signals map to each domain."""
    counts = {d: 0 for d in DOMAINS}
    for sig in msr_signals:
        domain = sig.get("domain")
        if domain in counts:
            counts[domain] += 1
    return counts


def _shared_factor_count(domain_i: str, domain_j: str, msr_signals: list) -> int:
    """Count signals that reference both domain_i and domain_j."""
    count = 0
    for sig in msr_signals:
        domains = sig.get("domains", [])
        if isinstance(domains, list) and domain_i in domains and domain_j in domains:
            count += 1
    return count


def _link_strength(
    domain_i: str,
    domain_j: str,
    signal_counts: dict,
    msr_signals: list,
    use_placeholder: bool,
) -> tuple:
    """
    Returns (value_number, value_text) for the (domain_i, domain_j) cell.
    """
    if use_placeholder:
        return 0.5, "placeholder"

    shared = _shared_factor_count(domain_i, domain_j, msr_signals)
    n_i = signal_counts.get(domain_i, 0)
    n_j = signal_counts.get(domain_j, 0)
    denom = math.sqrt(max(1, n_i) * max(1, n_j))
    strength = shared / denom
    return round(strength, 6), f"{shared} shared factors"


def _build_rows(chart_id, ayanamsha_id, build_id, msr_signals, use_placeholder):
    """Build one row per (domain_i, domain_j) cell — 81 rows total."""
    signal_counts = _count_signals_per_domain(msr_signals) if msr_signals else {}
    rows = []
    for domain_i in DOMAINS:
        for domain_j in DOMAINS:
            value_number, value_text = _link_strength(
                domain_i, domain_j, signal_counts, msr_signals or [], use_placeholder
            )
            fact_key = f"link_{domain_j}"
            cref = make_citation_ref("cdlm", domain_i, fact_key, chart_id, ayanamsha_id)
            rows.append(_row(
                chart_id, ayanamsha_id, build_id,
                "cdlm",
                domain_i,
                fact_key,
                value_text,
                value_number,
                cref,
                "CDLM v4 cross-domain linkage",
                "cdlm_writer/compute_link_strength",
            ))
    return rows


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write CDLM 9×9 domain linkage matrix to chart_facts.
    Returns number of rows written (81 for a full matrix).
    """
    msr_signals = chart_output.get("msr_signals")
    use_placeholder = not msr_signals

    rows = _build_rows(chart_id, ayanamsha_id, build_id, msr_signals, use_placeholder)

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[CDLM] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
