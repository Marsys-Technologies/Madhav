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

FORENSIC guard (canonical chart 482012f1-710e-4a25-994a-93821f5871aa):
  Sun  = Capricorn (Saturn's sign — classical enemy_sign, NOT debilitation;
         Sun debilitates in Libra) → condition_score expected moderately low
         (measured 0.26) → 'strong'. Non-fatal: logged, not build-halting
         (F-E5 — the prior "debilitated" rationale was factually wrong, even
         though the threshold check it gated happened to still hold).
  Moon = Purva Bhadrapada         → nakshatra_body_part = 'left_side'
  Saturn = Libra (exalted)        → condition_score must not be in the LOW band (an exalted
         planet is not "under stress"); measured 0.68-0.70 across ayanamshas, i.e. the MID
         band ('moderate') under the ruled 0.4 / 0.7 table. The pre-I-28 guard demanded
         'mild' (score > 0.6); under 0.7 it would halt every canonical build.

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


def sun_forensic_guard_warning(sun_score: Optional[float]) -> Optional[str]:
    """F-E5: Sun's FORENSIC check for the canonical native, non-fatal.

    The prior version raised a build-halting AssertionError on this check
    with the stated ground "Sun debilitated in Capricorn" — Sun's actual
    debilitation sign is Libra; Capricorn (Saturn's sign) is merely Sun's
    classical enemy_sign, a weaker relationship. The check passed today only
    because enemy_sign's score (0.26) happens to also fall under the 0.4
    threshold a genuinely debilitated Sun (score 0.0) would produce — the
    assertion's own stated claim was never what the code actually measured
    (§N.8). Downgraded to a warning (§N.4 S7 precedent: an honest, correctly-
    reasoned signal beats a build-fatal one resting on a false premise).

    Returns a warning message when the expected 'strong' tier does not hold,
    or None when it does.
    """
    sun_strength = indication_strength_from_score(sun_score)
    if sun_strength == "strong":
        return None
    return (
        f"FORENSIC ADVISORY: Sun indication_strength={sun_strength!r} but expected "
        f"'strong' (Sun sits in Capricorn — Saturn's sign, Sun's classical enemy_sign, "
        f"NOT debilitation; Sun debilitates in Libra), score={sun_score!r}"
    )


def saturn_forensic_guard_violation(saturn_score: Optional[float]) -> Optional[str]:
    """FORENSIC check for the canonical native's Saturn (Libra, exalted). Build-halting.

    Returns a violation message, or None when the check holds.

    What the claim is: an EXALTED planet is not a planet "under stress", so its
    condition_score must not fall in the LOW band (score < 0.4 -> 'strong' indication), and the
    score must exist (a NULL score cannot support the claim either way).

    Why it is stated against the band table and not as `== 'mild'`: the pre-I-28 guard demanded
    'mild' because medical's private cut was `score > 0.6`. Under the ruled single table
    (0.4 / 0.7) the canonical Saturn scores 0.680-0.697 (MID band, 'moderate') on every
    ayanamsha, so an `== 'mild'` guard would halt EVERY canonical ga_medical build on a number
    the ruling moved, not on a regression in Saturn. The classical content (exalted => not
    stressed) is what the guard still enforces; 'mild' vs 'moderate' for Saturn is a band-edge
    question (0.7), not an exaltation question. Same reasoning as the ga_vastu Saturn gate
    removed by migration 924 (#2421).
    """
    band = score_band(saturn_score)
    if band is None:
        return (
            f"Saturn condition_score is NULL (cannot support 'exalted => not stressed'), "
            f"score={saturn_score!r}"
        )
    if band == BAND_LOW:
        return (
            f"Saturn indication_strength={indication_strength_from_score(saturn_score)!r} "
            f"(LOW band) but Saturn is exalted in Libra and must not be in the low band, "
            f"score={saturn_score!r}"
        )
    return None


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
      Sun=Capricorn → 'strong'; Moon=Purva Bhadrapada → left_side; Saturn=Libra → not LOW band.

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

    # FORENSIC guard for canonical chart. Saturn: assert-and-halt (the claim is
    # classically correct). Sun: non-fatal advisory only (F-E5) — see
    # sun_forensic_guard_warning's docstring for why.
    if chart_id == CANONICAL_CHART_ID and ayanamsha_id == "lahiri_chitrapaksha":
        sun_score = condition_scores.get("Sun")
        saturn_score = condition_scores.get("Saturn")
        moon_nak = positions.get("Moon", {}).get("nakshatra")
        logger.info(
            "[ga_medical_writer] FORENSIC chart=%s aya=%s — "
            "Sun condition_score=%s (expected<0.4→'strong'); "
            "Saturn condition_score=%s (expected not in the LOW band, i.e. >= 0.4); "
            "Moon nakshatra=%s (expected Purva Bhadrapada)",
            chart_id, ayanamsha_id, sun_score, saturn_score, moon_nak,
        )
        # F-E5: Sun in Capricorn is enemy_sign, not debilitation (Sun debilitates
        # in Libra) — non-fatal advisory, not a build-halting assertion.
        sun_warning = sun_forensic_guard_warning(sun_score)
        if sun_warning:
            logger.warning(
                "[ga_medical_writer] %s for chart_id=%s ayanamsha=%s",
                sun_warning, CANONICAL_CHART_ID, ayanamsha_id,
            )
        # Saturn = Libra (exalted) → condition_score must not be in the LOW band (an exalted
        # planet is not "under stress"); see saturn_forensic_guard_violation.
        saturn_violation = saturn_forensic_guard_violation(saturn_score)
        if saturn_violation:
            raise AssertionError(
                f"FORENSIC VIOLATION: {saturn_violation} "
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
