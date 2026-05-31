"""
ucn_digest_writer.py — MARSYS-JIS A14 UCN Digest writer [G4-07]
Top-K summary stored to chart_facts with fact_category='ucn_digest'.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A14_ucn_digest"
ASSET_LABEL = "UCN Digest"
ENGINE_VERSION = "pyjhora/1.0.0"
TOP_K = 20

_ALL_GRAHAS = [
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
]

# Required Shadbala minima (BPHS Ch 28) for ratio computation
_REQUIRED_SHADBALA = {
    "sun": 390.0, "moon": 360.0, "mars": 300.0, "mercury": 420.0,
    "jupiter": 390.0, "venus": 330.0, "saturn": 300.0,
    "rahu": 1.0, "ketu": 1.0,
}


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
        "writer": "ucn_digest_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,          # category (legacy col)
        "D1",                   # divisional_chart
        "ucn_digest_writer",    # source_section
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
# ── Section builders ──────────────────────────────────────────────────────────

def _top_k_signal_rows(chart_id, ayanamsha_id, build_id, msr_signals: list, k: int = TOP_K) -> list:
    """Top-K MSR signals by computed_salience."""
    sorted_signals = sorted(
        msr_signals,
        key=lambda s: float(s.get("computed_salience", 0.0) or 0.0),
        reverse=True,
    )[:k]
    rows = []
    for rank, sig in enumerate(sorted_signals, start=1):
        sig_id = sig.get("signal_id", f"sig_{rank}")
        fact_key = f"top_signal_{rank:03d}"
        cref = make_citation_ref("ucn_digest", "top_signals", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "ucn_digest",
            "top_signals",
            fact_key,
            sig_id,
            float(sig.get("computed_salience", 0.0) or 0.0),
            cref,
            "UCN top-K MSR signals",
            "ucn_digest_writer/top_k_signals",
        ))
    return rows


def _shadbala_rank_rows(chart_id, ayanamsha_id, build_id, shadbala_data: dict) -> list:
    """Dominant (top 3) and weakest (bottom 3) grahas by shadbala ratio."""
    ratios = []
    for graha in _ALL_GRAHAS:
        data = shadbala_data.get(graha, {})
        total = float(data.get("total_shadbala", 0.0) or 0.0)
        req = _REQUIRED_SHADBALA.get(graha, 1.0)
        ratio = total / req if req > 0 else 0.0
        ratios.append((graha, ratio))
    ratios.sort(key=lambda x: x[1], reverse=True)  # strongest first

    rows = []
    for rank, (graha, ratio) in enumerate(ratios[:3], start=1):
        fact_key = f"dominant_{rank}"
        cref = make_citation_ref("ucn_digest", "dominant_grahas", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "ucn_digest",
            "dominant_grahas",
            fact_key,
            graha,
            round(ratio, 6),
            cref,
            "UCN dominant graha",
            "ucn_digest_writer/dominant_grahas",
        ))
    for rank, (graha, ratio) in enumerate(ratios[-3:], start=1):
        fact_key = f"weakest_{rank}"
        cref = make_citation_ref("ucn_digest", "weakest_grahas", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "ucn_digest",
            "weakest_grahas",
            fact_key,
            graha,
            round(ratio, 6),
            cref,
            "UCN weakest graha",
            "ucn_digest_writer/weakest_grahas",
        ))
    return rows


def _top_yoga_rows(chart_id, ayanamsha_id, build_id, yogas: list) -> list:
    """Top 5 active yogas by strength."""
    sorted_yogas = sorted(
        yogas,
        key=lambda y: float(y.get("strength", 0.0) or 0.0),
        reverse=True,
    )[:5]
    rows = []
    for rank, yoga in enumerate(sorted_yogas, start=1):
        yoga_name = yoga.get("yoga_name", f"yoga_{rank}")
        fact_key = f"top_yoga_{rank}"
        cref = make_citation_ref("ucn_digest", "top_yogas", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "ucn_digest",
            "top_yogas",
            fact_key,
            yoga_name,
            float(yoga.get("strength", 0.0) or 0.0),
            cref,
            "UCN top yoga",
            "ucn_digest_writer/top_yogas",
        ))
    return rows


def _dasha_context_rows(chart_id, ayanamsha_id, build_id, dashas: dict) -> list:
    """Current maha + antar dasha lords."""
    rows = []
    current_chain = dashas.get("vimshottari", {}).get("current_chain", [])
    for level, entry in enumerate(current_chain[:2]):
        lord = entry.get("lord", "unknown")
        level_name = "maha_dasha" if level == 0 else "antar_dasha"
        fact_key = f"current_{level_name}"
        cref = make_citation_ref("ucn_digest", "dasha_context", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "ucn_digest",
            "dasha_context",
            fact_key,
            lord,
            float(level),
            cref,
            "UCN current dasha chain",
            "ucn_digest_writer/dasha_context",
        ))
    return rows


def _system_convergence_row(chart_id, ayanamsha_id, build_id, convergence_count: int) -> list:
    """Number of ayanamshas that agree on the dominant graha."""
    fact_key = "ayanamsha_convergence_count"
    cref = make_citation_ref("ucn_digest", "system_convergence", fact_key, chart_id, ayanamsha_id)
    return [_row(
        chart_id, ayanamsha_id, build_id,
        "ucn_digest",
        "system_convergence",
        fact_key,
        f"{convergence_count} of 5 ayanamshas agree",
        float(convergence_count),
        cref,
        "UCN system convergence",
        "ucn_digest_writer/system_convergence",
    )]


def _placeholder_rows(chart_id, ayanamsha_id, build_id) -> list:
    """Minimal placeholder when chart_output has no usable data."""
    fact_key = "status"
    cref = make_citation_ref("ucn_digest", "status", fact_key, chart_id, ayanamsha_id)
    return [_row(
        chart_id, ayanamsha_id, build_id,
        "ucn_digest",
        "status",
        fact_key,
        "ucn_not_computed",
        0.0,
        cref,
        "UCN placeholder",
        "ucn_digest_writer/placeholder",
    )]


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Write UCN Digest to chart_facts.
    Computes top-K signals, dominant/weakest grahas, top yogas,
    dasha context, and system convergence.
    Returns number of rows written.
    """
    if conn is None:
        return 0
    msr_signals = chart_output.get("msr_signals") or []
    shadbala_data = chart_output.get("shadbala") or {}
    yogas = chart_output.get("yogas") or []
    dashas = chart_output.get("dashas") or {}
    convergence_count = int(chart_output.get("ayanamsha_convergence_count", 0) or 0)

    has_data = bool(msr_signals or shadbala_data or yogas or dashas)

    if not has_data:
        rows = _placeholder_rows(chart_id, ayanamsha_id, build_id)
    else:
        rows = []
        if msr_signals:
            rows.extend(_top_k_signal_rows(chart_id, ayanamsha_id, build_id, msr_signals))
        if shadbala_data:
            rows.extend(_shadbala_rank_rows(chart_id, ayanamsha_id, build_id, shadbala_data))
        if yogas:
            rows.extend(_top_yoga_rows(chart_id, ayanamsha_id, build_id, yogas))
        if dashas:
            rows.extend(_dasha_context_rows(chart_id, ayanamsha_id, build_id, dashas))
        rows.extend(_system_convergence_row(chart_id, ayanamsha_id, build_id, convergence_count))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[UCN] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
