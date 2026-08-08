"""
ga_medical_writer.py — GA Medical/Ayurvedic Indication writer
=============================================================
Asset: ga_medical — per-chart Ayurvedic Jyotish indication summary.
Table: ga_medical
Natural key: (chart_id, ayanamsha_id, graha)
Rows per chart: 9 grahas × 5 ayanamshas = 45

Algorithm:
  1. Load graha condition_scores from ga_condition_composite (already built by ga_condition).
  2. Load Ayurvedic mappings from bg_medical_mappings (L0 seed table).
  3. For each graha: derive indication_strength from condition_score:
       condition_score < 0.4  → 'strong'   (planet under stress → heightened indication)
       0.4 <= score <= 0.6    → 'moderate'
       condition_score > 0.6  → 'mild'      (planet strong → indication diminished)
     If condition_score is NULL: indication_strength = 'unknown'
  4. For Moon: also look up nakshatra_body_part from bg_nakshatra_medical.
  5. INSERT with indication_tier='jyotish_indication' and not_diagnosis=TRUE.

Idempotency: L1 pattern — DELETE WHERE (chart_id, ayanamsha_id) then INSERT.

FORENSIC guard (canonical chart 482012f1-710e-4a25-994a-93821f5871aa):
  Sun  = Capricorn (debilitated)  → condition_score expected low  → 'strong'
  Moon = Purva Bhadrapada         → nakshatra_body_part = 'left_side'
  Saturn = Libra (exalted)        → condition_score expected high → 'mild'

MEDICAL DISCLAIMER (NON-NEGOTIABLE):
  Every row carries indication_tier = 'jyotish_indication' AND not_diagnosis = TRUE.
  This writer produces Jyotish indicators ONLY — NOT medical diagnoses.
  The classical_citation on every row documents the Jyotish source text.
  No row in ga_medical should ever be interpreted as clinical medical advice.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg.rows

from brahmagyan.graha_vocabulary import to_title

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

ALL_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "krishnamurti",
    "true_chitra",
    "raman",
    "surya_siddhanta_classical",
]

# Citation attached to every ga_medical row — references BOTH source tables
MEDICAL_GA_CITATION = (
    "BPHS Ch.18 / Ashtanga Hridayam / Charaka Samhita "
    "— via bg_medical_mappings L0 reference (ga_medical indication)"
)


# ── indication_strength from condition_score ──────────────────────────────────

def indication_strength_from_score(condition_score: Optional[float]) -> str:
    """
    Derive Ayurvedic indication strength from the planetary condition_score.

    Rationale: a planet under stress (low condition_score) produces heightened
    disease indications for its associated organs/doshas, because the planetary
    energy is disturbed or afflicted. A strong, well-placed planet's Ayurvedic
    signatures are in equilibrium (mild indication only).

    condition_score < 0.4  → 'strong'    (stressed/afflicted → heightened)
    0.4 ≤ score ≤ 0.6     → 'moderate'
    condition_score > 0.6  → 'mild'      (well-placed → equilibrium)
    None                   → 'unknown'   (condition_score not available)

    Source logic: BPHS Ch.18 disease-causation framework — planets in debility
    or with enemies are chief causers of their associated ailments.
    """
    if condition_score is None:
        return "unknown"
    if condition_score < 0.4:
        return "strong"
    if condition_score <= 0.6:
        return "moderate"
    return "mild"


# ── DB helpers ────────────────────────────────────────────────────────────────

def _load_condition_scores(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> dict[str, Optional[float]]:
    """
    Load condition_score per graha from ga_condition_composite.

    Returns dict: {graha_name: condition_score_or_None}
    Falls back gracefully if ga_condition_composite is not yet populated.
    """
    result: dict[str, Optional[float]] = {g: None for g in ALL_GRAHAS}
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, condition_score
                FROM ga_condition_composite
                WHERE chart_id    = %s
                  AND ayanamsha_id = %s
            """, (chart_id, ayanamsha_id))
            for row in cur.fetchall():
                graha = row[0]
                score = row[1]
                if graha in result:
                    result[graha] = float(score) if score is not None else None
    except Exception as exc:
        logger.warning(
            "[ga_medical_writer] ga_condition_composite lookup failed for "
            "chart=%s aya=%s: %s", chart_id, ayanamsha_id, exc
        )
    return result


def _load_medical_mappings(conn: Any) -> dict[str, dict]:
    """
    Load bg_medical_mappings into a dict keyed by graha name.

    Falls back to empty dict if table not yet populated (safe — returns 'unknown').
    """
    result: dict[str, dict] = {}
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, dosha, dhatu, organ_systems, body_part,
                       disease_tendency, classical_citation
                FROM bg_medical_mappings
            """)
            for row in cur.fetchall():
                result[row[0]] = {
                    "dosha":             list(row[1]) if row[1] else [],
                    "dhatu":             list(row[2]) if row[2] else [],
                    "organ_systems":     list(row[3]) if row[3] else [],
                    "body_part":         list(row[4]) if row[4] else [],
                    "disease_tendency":  list(row[5]) if row[5] else [],
                    "classical_citation": row[6] or "",
                }
    except Exception as exc:
        logger.warning(
            "[ga_medical_writer] bg_medical_mappings lookup failed: %s", exc
        )
    return result


def _load_graha_positions(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> dict[str, dict]:
    """
    Load sign and nakshatra for each graha from chart_facts.

    Returns dict: {graha: {'sign': ..., 'nakshatra': ...}}
    """
    result: dict[str, dict] = {}
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT fact_subject, fact_key, fact_value_text
                FROM chart_facts
                WHERE chart_id     = %s
                  AND ayanamsha_id = %s
                  AND fact_category IN ('graha_sign_attributes', 'graha_position')
                  AND fact_key IN ('sign', 'nakshatra')
            """, (chart_id, ayanamsha_id))

            # Values sourced from the graha SSoT's to_title() helper
            # (brahmagyan/graha_vocabulary) rather than hardcoded literals —
            # ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of
            # the originally-enumerated retirement targets).
            _SUBJECT_MAP = {
                code: to_title(code)
                for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
            }
            for subject, key, val_text in cur.fetchall():
                graha = _SUBJECT_MAP.get(subject)
                if graha is None:
                    continue
                if graha not in result:
                    result[graha] = {}
                result[graha][key] = val_text
    except Exception as exc:
        logger.warning(
            "[ga_medical_writer] chart_facts lookup failed for "
            "chart=%s aya=%s: %s", chart_id, ayanamsha_id, exc
        )
    return result


def _load_nakshatra_body_part(conn: Any, nakshatra_name: str) -> Optional[str]:
    """
    Look up body_part for a nakshatra from bg_nakshatra_medical.

    FORENSIC: 'Purva Bhadrapada' → 'left_side' (native Moon nakshatra).
    """
    if not nakshatra_name:
        return None
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT body_part
                FROM bg_nakshatra_medical
                WHERE nakshatra_name = %s
            """, (nakshatra_name,))
            row = cur.fetchone()
            return row[0] if row else None
    except Exception as exc:
        logger.warning(
            "[ga_medical_writer] bg_nakshatra_medical lookup failed for "
            "nakshatra=%s: %s", nakshatra_name, exc
        )
    return None


# ── Core build function ───────────────────────────────────────────────────────

def build_ga_medical_substep(
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    conn: Any,
) -> int:
    """
    Build ga_medical rows for one (chart_id × ayanamsha_id) pair.

    Steps:
    1. DELETE existing rows for this (chart_id, ayanamsha_id) — L1 idempotency.
    2. Load condition_scores from ga_condition_composite.
    3. Load medical mappings from bg_medical_mappings.
    4. Load positions (sign, nakshatra) from chart_facts.
    5. For each of 9 grahas:
       - Derive indication_strength from condition_score.
       - For Moon: look up nakshatra_body_part from bg_nakshatra_medical.
    6. INSERT 9 rows with NOT NULL indication_tier + not_diagnosis enforcement.

    FORENSIC log (canonical chart):
      Sun=Capricorn → 'strong'; Moon=Purva Bhadrapada → left_side; Saturn=Libra → 'mild'.

    Returns: number of rows inserted.
    """
    now = datetime.now(timezone.utc)

    # Step 1: DELETE existing rows (L1 replace-not-accrete)
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ga_medical WHERE chart_id = %s AND ayanamsha_id = %s",
            (chart_id, ayanamsha_id),
        )
        deleted = cur.rowcount or 0
    if deleted:
        logger.debug(
            "[ga_medical_writer] deleted %d prior rows for chart=%s aya=%s",
            deleted, chart_id, ayanamsha_id,
        )

    # Step 2: Load inputs
    condition_scores = _load_condition_scores(conn, chart_id, ayanamsha_id)
    medical_mappings = _load_medical_mappings(conn)
    positions        = _load_graha_positions(conn, chart_id, ayanamsha_id)

    # FORENSIC guard for canonical chart — assert-and-halt, not log-only
    if chart_id == CANONICAL_CHART_ID and ayanamsha_id == "lahiri_chitrapaksha":
        sun_score = condition_scores.get("Sun")
        saturn_score = condition_scores.get("Saturn")
        moon_nak = positions.get("Moon", {}).get("nakshatra")
        logger.info(
            "[ga_medical_writer] FORENSIC chart=%s aya=%s — "
            "Sun condition_score=%s (expected<0.4→'strong'); "
            "Saturn condition_score=%s (expected>0.6→'mild'); "
            "Moon nakshatra=%s (expected Purva Bhadrapada)",
            chart_id, ayanamsha_id, sun_score, saturn_score, moon_nak,
        )
        # Sun = Capricorn (debilitated) → condition_score must be < 0.4 → 'strong'
        sun_strength = indication_strength_from_score(sun_score)
        if sun_strength != "strong":
            raise AssertionError(
                f"FORENSIC VIOLATION: Sun indication_strength={sun_strength!r} "
                f"but expected 'strong' (Sun debilitated in Capricorn, score={sun_score!r}) "
                f"for chart_id={CANONICAL_CHART_ID} ayanamsha={ayanamsha_id}"
            )
        # Saturn = Libra (exalted) → condition_score must be > 0.6 → 'mild'
        sat_strength = indication_strength_from_score(saturn_score)
        if sat_strength != "mild":
            raise AssertionError(
                f"FORENSIC VIOLATION: Saturn indication_strength={sat_strength!r} "
                f"but expected 'mild' (Saturn exalted in Libra, score={saturn_score!r}) "
                f"for chart_id={CANONICAL_CHART_ID} ayanamsha={ayanamsha_id}"
            )

    # Step 3–5: Build rows
    rows_to_insert = []
    for graha in ALL_GRAHAS:
        mapping = medical_mappings.get(graha, {})
        pos     = positions.get(graha, {})
        score   = condition_scores.get(graha)

        natal_sign      = pos.get("sign")
        natal_nakshatra = pos.get("nakshatra")

        indication_strength = indication_strength_from_score(score)

        # Moon nakshatra body-part lookup
        nakshatra_body_part: Optional[str] = None
        if graha == "Moon" and natal_nakshatra:
            nakshatra_body_part = _load_nakshatra_body_part(conn, natal_nakshatra)

        rows_to_insert.append({
            "chart_id":            chart_id,
            "ayanamsha_id":        ayanamsha_id,
            "graha":               graha,
            "natal_sign":          natal_sign,
            "natal_nakshatra":     natal_nakshatra,
            "indication_strength": indication_strength,
            "dosha_aggravated":    mapping.get("dosha", []) or [],
            "organ_watch":         mapping.get("organ_systems", []) or [],
            "body_part_watch":     mapping.get("body_part", []) or [],
            "nakshatra_body_part": nakshatra_body_part,
            "indication_tier":     "jyotish_indication",   # NON-NEGOTIABLE
            "not_diagnosis":       True,                   # NON-NEGOTIABLE
            "classical_citation":  mapping.get("classical_citation") or MEDICAL_GA_CITATION,
            "computed_at":         now,
        })

    # Step 6: INSERT
    insert_sql = """
        INSERT INTO ga_medical (
            chart_id, ayanamsha_id, graha,
            natal_sign, natal_nakshatra, indication_strength,
            dosha_aggravated, organ_watch, body_part_watch,
            nakshatra_body_part,
            indication_tier, not_diagnosis,
            classical_citation, computed_at
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s,
            %s, %s,
            %s, %s
        )
    """

    inserted = 0
    with conn.cursor() as cur:
        for row in rows_to_insert:
            cur.execute(insert_sql, (
                row["chart_id"],
                row["ayanamsha_id"],
                row["graha"],
                row["natal_sign"],
                row["natal_nakshatra"],
                row["indication_strength"],
                row["dosha_aggravated"],
                row["organ_watch"],
                row["body_part_watch"],
                row["nakshatra_body_part"],
                row["indication_tier"],
                row["not_diagnosis"],
                row["classical_citation"],
                row["computed_at"],
            ))
            inserted += 1

    logger.info(
        "[ga_medical_writer] chart=%s aya=%s — inserted %d rows",
        chart_id, ayanamsha_id, inserted,
    )
    return inserted
