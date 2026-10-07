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
       condition_score < 0.4        → 'strong'   (planet under stress → heightened indication)
       0.4 <= score < 0.7           → 'moderate'
       condition_score >= 0.7       → 'mild'     (planet strong → indication diminished)
     The cut points are the ONE band table in ga_writers/ga_condition_bands.py
     (I-28 / Q-L1-16(c); shared with ga_vastu) -- they are NOT defined in this file.
     If condition_score is NULL: indication_strength = 'unknown'
  4. For Moon: also look up nakshatra_body_part from bg_nakshatra_medical.
  5. INSERT with indication_tier='jyotish_indication' and not_diagnosis=TRUE.

Idempotency: L1 pattern — DELETE WHERE (chart_id, ayanamsha_id) then INSERT.

No chart-specific assertions (SS rulings 2026-10-02): this writer runs for every chart, so it asserts
nothing about one chart's values -- no build-halting Saturn guard, no Sun advisory, no Moon/Sun/Saturn
FORENSIC logging. What those checks protected is pinned as golden TESTS on fixtures read from the
canonical chart (tests/test_ga_medical_saturn_golden.py, tests/test_ga_medical_sun_golden.py), so a
change shows in CI, not as a production halt or a log line. (The seven FORENSIC anchors are positional
facts owned by L1; they are not asserted here.)

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

# ONE band table for condition_score, owned by ga_condition (I-28 / Q-L1-16(c)): the cut
# points (0.4 / 0.7) live there, not here. This writer only maps a band to ITS label.
# SCORE_BANDS is re-exported (not used for logic) so the "one table object" identity with
# ga_condition and ga_vastu is directly checkable.
from ga_writers.ga_condition_bands import (  # noqa: F401  (SCORE_BANDS: re-export)
    BAND_HIGH,
    BAND_LOW,
    BAND_MID,
    BAND_UNKNOWN,
    SCORE_BANDS,
    score_band,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

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

#: Band -> stored indication_strength label (medical polarity: a LOW condition_score is a
#: HEIGHTENED indication). The CUT POINTS are not here: they are `SCORE_BANDS` (ga_condition).
INDICATION_STRENGTH_BY_BAND: dict[str, str] = {
    BAND_LOW:  "strong",
    BAND_MID:  "moderate",
    BAND_HIGH: "mild",
}

#: NULL condition_score -> 'unknown' (unchanged stored value; the same label ga_vastu now stores).
INDICATION_STRENGTH_UNKNOWN: str = BAND_UNKNOWN

def indication_strength_from_score(condition_score: Optional[float]) -> str:
    """
    Derive Ayurvedic indication strength from the planetary condition_score.

    Rationale: a planet under stress (low condition_score) produces heightened
    disease indications for its associated organs/doshas, because the planetary
    energy is disturbed or afflicted. A strong, well-placed planet's Ayurvedic
    signatures are in equilibrium (mild indication only).

    The cut points are NOT defined here: they are the single band table in
    `ga_writers.ga_condition_bands` (score < 0.4 low; 0.4 <= score < 0.7 mid; score >= 0.7 high):

    low   (score < 0.4)         → 'strong'    (stressed/afflicted → heightened)
    mid   (0.4 <= score < 0.7)  → 'moderate'
    high  (score >= 0.7)        → 'mild'      (well-placed → equilibrium)
    NULL                        → 'unknown'   (condition_score not available)

    Source logic: BPHS Ch.18 disease-causation framework — planets in debility
    or with enemies are chief causers of their associated ailments. The numeric
    cut points are project conventions (`unsourced`), not classical.
    """
    band = score_band(condition_score)
    if band is None:
        return INDICATION_STRENGTH_UNKNOWN
    return INDICATION_STRENGTH_BY_BAND[band]


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


#: Spelling families of the three nakshatras the repo spells more than one way, folded (case-insensitive)
#: to the spelling of the L0 seed table this writer looks up (`bg_nakshatra_medical`, seeded from
#: `brahmagyan.l0_medical.NAKSHATRA_MEDICAL`): the L1 adapter (`pyjhora_adapter._names`) spells nakshatra 23
#: "Dhanishta" where the seed says "Dhanishtha", so a Moon in nakshatra 23 found no body part. The other
#: two families (`Moola` / `Mula`, `Mrigasira` / `Mrigashira`) are spelled the seed's way by the adapter
#: already; they are folded too so a caller handing in the bg_cohort spelling reaches the same row.
#: Every other nakshatra reaches the seed under the spelling it is already written with.
_NAKSHATRA_SEED_SPELLING: dict[str, str] = {
    "dhanishta": "Dhanishtha",
    "dhanishtha": "Dhanishtha",
    "moola": "Mula",
    "mula": "Mula",
    "mrigasira": "Mrigashira",
    "mrigashira": "Mrigashira",
}


def nakshatra_seed_name(nakshatra_name: str) -> str:
    """The `bg_nakshatra_medical.nakshatra_name` spelling for a nakshatra name as the L1 facts spell it.

    Applied at the LOOKUP only: the stored `natal_nakshatra` stays the L1 fact's own value (the writer
    forwards it, it does not re-spell it)."""
    squashed = " ".join(nakshatra_name.split())
    return _NAKSHATRA_SEED_SPELLING.get(squashed.casefold(), squashed)


def _load_nakshatra_body_part(conn: Any, nakshatra_name: str) -> Optional[str]:
    """
    Look up body_part for a nakshatra from bg_nakshatra_medical.

    FORENSIC: 'Purva Bhadrapada' → 'left_side' (native Moon nakshatra).
    The name is folded to the seed table's spelling first (`nakshatra_seed_name`): nakshatra 23 is
    'Dhanishta' in the L1 facts and 'Dhanishtha' in the seed.
    """
    if not nakshatra_name:
        return None
    nakshatra_name = nakshatra_seed_name(nakshatra_name)
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
