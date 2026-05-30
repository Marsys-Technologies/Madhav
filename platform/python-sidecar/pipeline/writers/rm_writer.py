"""
rm_writer.py — MARSYS-JIS A13 RM Remedial Map writer [G4-06]
Ranks grahas by weakness and stores remedy suggestions to chart_facts
with fact_category='rm_remedy'.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A13_rm"
ASSET_LABEL = "RM Resonance Map"
ENGINE_VERSION = "natal_engine/0.2.0"

_ALL_GRAHAS = [
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
]

# Classical remedy associations per graha (mantra, gemstone, charity)
_GRAHA_REMEDIES = {
    "sun":     ("Aditya Hridayam", "Ruby", "Wheat donation on Sunday"),
    "moon":    ("Chandra mantra 108x", "Pearl", "Rice donation on Monday"),
    "mars":    ("Mangal mantra 108x", "Red Coral", "Lentil donation on Tuesday"),
    "mercury": ("Budha mantra 108x", "Emerald", "Green gram donation on Wednesday"),
    "jupiter": ("Guru mantra 108x", "Yellow Sapphire", "Gram donation on Thursday"),
    "venus":   ("Shukra mantra 108x", "Diamond/White Sapphire", "Sugar donation on Friday"),
    "saturn":  ("Shani mantra 108x", "Blue Sapphire", "Sesame donation on Saturday"),
    "rahu":    ("Rahu mantra 108x", "Hessonite", "Donation on Saturday evening"),
    "ketu":    ("Ketu mantra 108x", "Cat's Eye", "Donate black sesame"),
}

_REMEDY_TYPES = ["mantra", "gemstone", "charity"]


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
        "writer": "rm_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,      # category (legacy col)
        "D1",               # divisional_chart
        "rm_writer",        # source_section
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
def _rank_grahas_by_weakness(shadbala_data: dict) -> list:
    """
    Return list of (graha, shadbala_ratio) sorted weakest first.
    If a graha is missing from shadbala_data, ratio defaults to 0.0.
    """
    REQUIRED = {
        "sun": 390.0, "moon": 360.0, "mars": 300.0, "mercury": 420.0,
        "jupiter": 390.0, "venus": 330.0, "saturn": 300.0,
        "rahu": 1.0, "ketu": 1.0,
    }
    rankings = []
    for graha in _ALL_GRAHAS:
        data = shadbala_data.get(graha, {}) if shadbala_data else {}
        total = float(data.get("total_shadbala", 0.0) or 0.0)
        req = REQUIRED.get(graha, 1.0)
        ratio = total / req if req > 0 else 0.0
        rankings.append((graha, ratio))
    return sorted(rankings, key=lambda x: x[1])  # weakest first


def _build_remedy_rows(chart_id, ayanamsha_id, build_id, graha, priority_rank) -> list:
    """Build 3 remedy rows (mantra, gemstone, charity) for a graha."""
    remedies = _GRAHA_REMEDIES.get(graha, ("unknown mantra", "unknown gemstone", "unknown charity"))
    remedy_descs = {
        "mantra": remedies[0],
        "gemstone": remedies[1],
        "charity": remedies[2],
    }
    rows = []
    for remedy_type in _REMEDY_TYPES:
        fact_key = f"remedy_{remedy_type}"
        cref = make_citation_ref("rm_remedy", graha, fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "rm_remedy",
            graha,
            fact_key,
            remedy_descs[remedy_type],
            float(priority_rank),
            cref,
            "RM classical remedy mapping",
            "rm_writer/build_remedy",
        ))
    return rows


def _build_placeholder_rows(chart_id, ayanamsha_id, build_id) -> list:
    """One placeholder row per graha when shadbala is absent."""
    rows = []
    for graha in _ALL_GRAHAS:
        fact_key = "status"
        cref = make_citation_ref("rm_remedy", graha, fact_key, chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "rm_remedy",
            graha,
            fact_key,
            "rm_not_computed",
            0.0,
            cref,
            "RM placeholder",
            "rm_writer/placeholder",
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
    Write RM remedy suggestions to chart_facts.
    Uses shadbala from chart_output or extra to rank grahas.
    Returns number of rows written.
    """
    if conn is None:
        return 0
    shadbala_data = chart_output.get("shadbala")
    if not shadbala_data and extra:
        shadbala_data = extra.get("shadbala")

    if not shadbala_data:
        rows = _build_placeholder_rows(chart_id, ayanamsha_id, build_id)
    else:
        ranked = _rank_grahas_by_weakness(shadbala_data)
        rows = []
        for priority_rank, (graha, _ratio) in enumerate(ranked, start=1):
            rows.extend(_build_remedy_rows(chart_id, ayanamsha_id, build_id, graha, priority_rank))

    if rows:
        _upsert_chart_facts(conn, rows)

    logger.info(
        "[RM] %s: %d rows written (chart=%s ayanamsha=%s build=%s)",
        ASSET_LABEL, len(rows), chart_id, ayanamsha_id, build_id,
    )
    return len(rows)
