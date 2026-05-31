"""
cgm_writer.py — MARSYS-JIS A12 CGM Graph Nodes + Edges writer [G4-05]
Chart Graph Model: graha nodes + aspect edges stored to chart_facts.
  Nodes: fact_category='cgm_node'
  Edges: fact_category='cgm_edge'
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A12_cgm"
ASSET_LABEL = "CGM Graph Nodes + Edges"
ENGINE_VERSION = "pyjhora/1.0.0"

_ALL_GRAHAS = [
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
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
        "writer": "cgm_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,      # category (legacy col)
        "D1",               # divisional_chart
        "cgm_writer",       # source_section
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
    with conn.cursor() as _cur:
        execute_values(_cur, _INSERT_SQL, rows)
def _build_node_rows(chart_id, ayanamsha_id, build_id, planets: dict) -> list:
    """One cgm_node row per graha."""
    rows = []
    for graha in _ALL_GRAHAS:
        planet_data = planets.get(graha, {})
        graha_sign = planet_data.get("sign", "unknown")
        shadbala_rank = float(planet_data.get("shadbala_rank", 0.0) or 0.0)
        fact_key = graha
        cref = make_citation_ref("cgm_node", "graha", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "cgm_node",
            "graha",
            fact_key,
            graha_sign,
            shadbala_rank,
            cref,
            "CGM node — classical graha",
            "cgm_writer/build_node",
        ))
    return rows


def _build_edge_rows(chart_id, ayanamsha_id, build_id, aspects: list) -> list:
    """One cgm_edge row per aspect entry."""
    rows = []
    for aspect in aspects:
        g1 = aspect.get("graha1", "unknown")
        g2 = aspect.get("graha2", "unknown")
        aspect_strength = float(aspect.get("strength", 0.0) or 0.0)
        fact_key = f"{g1}_to_{g2}"
        cref = make_citation_ref("cgm_edge", "aspect_edge", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "cgm_edge",
            "aspect_edge",
            fact_key,
            aspect.get("aspect_type", "aspect"),
            aspect_strength,
            cref,
            "CGM edge — classical aspect",
            "cgm_writer/build_edge",
        ))
    return rows


def _build_placeholder_node_rows(chart_id, ayanamsha_id, build_id) -> list:
    """One placeholder row per graha when planets data is absent."""
    rows = []
    for graha in _ALL_GRAHAS:
        fact_key = graha
        cref = make_citation_ref("cgm_node", "graha", fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "cgm_node",
            "graha",
            fact_key,
            "cgm_not_computed",
            0.0,
            cref,
            "CGM node — placeholder",
            "cgm_writer/placeholder",
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
    Write CGM nodes (graha) and edges (aspects) to chart_facts.
    Returns total number of rows written.
    """
    if conn is None:
        return 0
    planets = chart_output.get("planets")
    aspects = chart_output.get("aspects", [])

    if planets:
        node_rows = _build_node_rows(chart_id, ayanamsha_id, build_id, planets)
    else:
        node_rows = _build_placeholder_node_rows(chart_id, ayanamsha_id, build_id)

    edge_rows = _build_edge_rows(chart_id, ayanamsha_id, build_id, aspects or [])

    all_rows = node_rows + edge_rows
    if all_rows:
        _upsert_chart_facts(conn, all_rows)

    logger.info(
        "[CGM] %s: %d node rows + %d edge rows = %d total (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(node_rows), len(edge_rows), len(all_rows),
        chart_id, ayanamsha_id, build_id,
    )
    return len(all_rows)
