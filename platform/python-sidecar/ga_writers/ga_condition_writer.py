"""
ga_condition_writer.py — GA-CONDITION Planetary Condition Composite writer
==========================================================================
Asset: ga_condition — unified dignity/avastha/motion/combustion/friendship +
0–1 condition score per graha per ayanamsha.

Table: ga_condition_composite
Natural key: (chart_id, ayanamsha_id, graha)
Rows per chart: 9 grahas × 5 ayanamshas = 45

Idempotency: L1 pattern — DELETE (chart_id, ayanamsha_id) then INSERT.
FORENSIC guard: Sun in Capricorn must NOT be exalted/own/moolatrikona.

Classical sources:
    BPHS    = Brihat Parashara Hora Shastra
    JP      = Jataka Parijata
    PD      = Phala Deepika
    SS      = Surya Siddhanta / Saravali
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg.rows

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# All 9 classical Jyotish grahas (same order as ga_positions)
ALL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Sign lords (classical, keyed by sign name)
SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars",      "Taurus": "Venus",     "Gemini": "Mercury",
    "Cancer": "Moon",     "Leo": "Sun",           "Virgo": "Mercury",
    "Libra": "Venus",     "Scorpio": "Mars",      "Sagittarius": "Jupiter",
    "Capricorn": "Saturn","Aquarius": "Saturn",   "Pisces": "Jupiter",
}

# Dignity score map (0.0 – 1.0); used in condition_score formula
DIGNITY_SCORES: dict[str, float] = {
    "exalted":           1.0,
    "moolatrikona":      0.9,
    "own":               0.8,
    "great_friend_sign": 0.7,
    "friend_sign":       0.6,
    "neutral_sign":      0.5,
    "enemy_sign":        0.3,
    "great_enemy_sign":  0.2,
    "debilitated":       0.0,
}

# Deeptaadi → score mapping
_DEEPTAADI_SCORES: dict[str, float] = {
    "deepta":  1.0,
    "swastha": 0.85,
    "mudita":  0.70,
    "shanta":  0.60,
    "shakta":  0.50,
    "dina":    0.35,
    "peedit":  0.20,
    "khala":   0.10,
    "vikala":  0.00,
}

# Baladi → score mapping (yuva = peak age = highest strength)
_BALADI_SCORES: dict[str, float] = {
    "yuva":    1.0,
    "kumara":  0.75,
    "bala":    0.50,
    "vriddha": 0.25,
    "mrita":   0.00,
}

# Condition formula component weights (must sum to 1.0)
# Note: combustion component is a subtraction penalty, not an additive term.
# Max achievable score for a non-combust planet = 0.35 + 0.20 + 0.10 + 0.20 = 0.85
# (dignity_d1 + deeptaadi + baladi + varga; combustion penalty = 0 when not combust)
# A combust planet incurs a 0.15 penalty (floor ~0.70 for otherwise strong planets).
_FORMULA_WEIGHTS = {
    "dignity_d1":   0.35,
    "deeptaadi":    0.20,
    "baladi":       0.10,
    "combustion":   0.15,  # subtracted when combust
    "varga":        0.20,
}

# Exaltation / debilitation / own-sign / moolatrikona data (mirrors bg_dignity_reference)
# Used for pure helper functions that must work without a DB connection.
_EXALTATION: dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
    "Rahu": "Gemini", "Ketu": "Sagittarius",
}
_DEBILITATION: dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
    "Rahu": "Sagittarius", "Ketu": "Gemini",
}
_OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"], "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"], "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"], "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}
_MOOLATRIKONA: dict[str, str] = {
    "Sun": "Leo", "Moon": "Taurus", "Mars": "Aries",
    "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius",
}
# Moolatrikona degree ranges (from, to) within the sign
_MOOLATRIKONA_RANGE: dict[str, tuple[float, float]] = {
    "Sun": (0, 20), "Moon": (4, 30), "Mars": (0, 12),
    "Mercury": (16, 20), "Jupiter": (0, 10), "Venus": (0, 15), "Saturn": (0, 20),
}


# ── Pure helper functions (testable without DB) ───────────────────────────────

def dignity_d1_from_sign(
    graha: str,
    sign: str,
    degree_in_sign: float,
    dignity_ref: Optional[dict] = None,
) -> str:
    """
    Determine the dignity category of a graha in a given sign.

    Args:
        graha:          Planet name (e.g. 'Sun', 'Moon', …)
        sign:           Sign name (e.g. 'Capricorn')
        degree_in_sign: Degree within the sign (0–30)
        dignity_ref:    Optional pre-loaded dict from bg_dignity_reference.
                        When None, uses the module-level constants (same data).

    Returns:
        One of: 'exalted', 'moolatrikona', 'own', 'great_friend_sign',
                'friend_sign', 'neutral_sign', 'enemy_sign', 'great_enemy_sign',
                'debilitated'.

    Note: great_friend_sign / great_enemy_sign are derived at
    panchadha_maitri stage; this function returns only the sign-based category
    without tatkalika context. The function uses 'friend_sign'/'enemy_sign'
    for the naisargika-only assessment relative to the sign lord.
    """
    # Moolatrikona check (before exaltation) — when a planet's moolatrikona and exaltation
    # share the same sign (e.g. Mercury=Virgo), moolatrikona degree range takes precedence
    # over the generic sign-level exaltation check. Classical priority: MT range > exalt sign.
    mt_sign = _MOOLATRIKONA.get(graha) if dignity_ref is None else dignity_ref.get("moolatrikona_sign")
    mt_range = _MOOLATRIKONA_RANGE.get(graha)
    if mt_sign and sign == mt_sign and mt_range:
        mt_from, mt_to = mt_range
        if mt_from <= degree_in_sign < mt_to:
            return "moolatrikona"

    # Exaltation check
    exalt_sign = _EXALTATION.get(graha) if dignity_ref is None else dignity_ref.get("exaltation_sign")
    if sign == exalt_sign:
        return "exalted"

    # Debilitation check
    debi_sign = _DEBILITATION.get(graha) if dignity_ref is None else dignity_ref.get("debilitation_sign")
    if sign == debi_sign:
        return "debilitated"

    # Own sign check
    own = _OWN_SIGNS.get(graha, []) if dignity_ref is None else dignity_ref.get("own_signs", [])
    if sign in own:
        return "own"

    # Naisargika friendship with sign lord
    sign_lord = SIGN_LORDS.get(sign)
    if sign_lord is None or sign_lord == graha:
        return "neutral_sign"

    # Friend/enemy via naisargika table (module-level constants from ga_structural_writer)
    # We use a local minimal lookup here so the function is standalone.
    _NAISARGIKA: dict[str, dict[str, str]] = {
        "Sun":     {"Moon": "friend", "Mars": "friend", "Jupiter": "friend",
                    "Mercury": "neutral", "Venus": "enemy", "Saturn": "enemy",
                    "Rahu": "enemy", "Ketu": "neutral"},
        "Moon":    {"Sun": "friend", "Mercury": "friend", "Mars": "neutral",
                    "Jupiter": "neutral", "Venus": "neutral", "Saturn": "neutral",
                    "Rahu": "enemy", "Ketu": "neutral"},
        "Mars":    {"Sun": "friend", "Moon": "friend", "Jupiter": "friend",
                    "Venus": "neutral", "Saturn": "neutral", "Mercury": "enemy",
                    "Rahu": "neutral", "Ketu": "friend"},
        "Mercury": {"Sun": "friend", "Venus": "friend", "Mars": "neutral",
                    "Jupiter": "neutral", "Saturn": "neutral", "Moon": "enemy",
                    "Rahu": "friend", "Ketu": "neutral"},
        "Jupiter": {"Sun": "friend", "Moon": "friend", "Mars": "friend",
                    "Saturn": "neutral", "Mercury": "enemy", "Venus": "enemy",
                    "Rahu": "neutral", "Ketu": "neutral"},
        "Venus":   {"Mercury": "friend", "Saturn": "friend", "Mars": "neutral",
                    "Jupiter": "neutral", "Sun": "enemy", "Moon": "enemy",
                    "Rahu": "friend", "Ketu": "friend"},
        "Saturn":  {"Mercury": "friend", "Venus": "friend", "Jupiter": "neutral",
                    "Sun": "enemy", "Moon": "enemy", "Mars": "enemy",
                    "Rahu": "friend", "Ketu": "friend"},
        "Rahu":    {"Venus": "friend", "Saturn": "friend", "Mercury": "friend",
                    "Sun": "enemy", "Moon": "enemy", "Mars": "neutral",
                    "Jupiter": "neutral", "Ketu": "enemy"},
        "Ketu":    {"Mars": "friend", "Venus": "friend", "Saturn": "friend",
                    "Sun": "neutral", "Moon": "neutral", "Mercury": "neutral",
                    "Jupiter": "neutral", "Rahu": "enemy"},
    }

    graha_relations = _NAISARGIKA.get(graha, {})
    relation = graha_relations.get(sign_lord, "neutral")

    if relation == "friend":
        return "friend_sign"
    if relation == "enemy":
        return "enemy_sign"
    return "neutral_sign"


def avastha_baladi_from_degree(degree_in_sign: float) -> str:
    """
    Determine baladi avastha from degree within sign.
    0–6°=bala, 6–12°=kumara, 12–18°=yuva, 18–24°=vriddha, 24–30°=mrita.
    Boundary at exactly N° belongs to the next state (< N = prev state).
    """
    if degree_in_sign < 6:
        return "bala"
    if degree_in_sign < 12:
        return "kumara"
    if degree_in_sign < 18:
        return "yuva"
    if degree_in_sign < 24:
        return "vriddha"
    return "mrita"


def avastha_jagradadi_from_dignity(dignity_d1: str) -> str:
    """
    Derive jagradadi avastha from d1 dignity label.
    exalted/moolatrikona/own → jagrata
    friend_sign/great_friend_sign → svapna
    all others (neutral/enemy/debilitated) → sushupti
    """
    if dignity_d1 in ("exalted", "moolatrikona", "own"):
        return "jagrata"
    if dignity_d1 in ("friend_sign", "great_friend_sign"):
        return "svapna"
    return "sushupti"


def avastha_deeptaadi_from_dignity_and_state(
    dignity_d1: str,
    is_combust: bool,
    is_retrograde: bool,
) -> str:
    """
    Determine deeptaadi avastha (Phala Deepika priority ladder).

    Priority order (highest to lowest):
      deepta  → exalted or own sign
      swastha → friendly sign
      shanta  → neutral sign
      dina    → enemy sign
      peedit  → combust (overrides sign if planet is combust in non-own/exalt)
      khala   → debilitated
      vikala  → retrograde in enemy sign

    Note: mudita (good navamsa) and shakta (conjunct benefic) require chart-level
    data not available as pure inputs here; they are omitted from this simplified
    version and resolved to adjacent labels by the build function when needed.
    """
    # Combust overrides most sign-based labels (peedit wins over dina/shanta)
    if is_combust and dignity_d1 not in ("exalted", "moolatrikona", "own"):
        return "peedit"
    # Retrograde in enemy sign = vikala
    if is_retrograde and dignity_d1 in ("enemy_sign", "great_enemy_sign"):
        return "vikala"
    if dignity_d1 in ("exalted", "moolatrikona", "own"):
        return "deepta"
    if dignity_d1 in ("friend_sign", "great_friend_sign"):
        return "swastha"
    if dignity_d1 == "neutral_sign":
        return "shanta"
    if dignity_d1 in ("enemy_sign", "great_enemy_sign"):
        return "dina"
    if dignity_d1 == "debilitated":
        return "khala"
    return "shanta"  # fallback


def compute_combustion_arc(planet_longitude: float, sun_longitude: float) -> float:
    """
    Compute minimum arc between planet and Sun in degrees.
    Returns a value in [0, 180] range (short arc).

    Args:
        planet_longitude: Sidereal longitude of the planet (0–360)
        sun_longitude:    Sidereal longitude of the Sun (0–360)
    """
    raw_diff = abs(planet_longitude - sun_longitude)
    if raw_diff > 180.0:
        raw_diff = 360.0 - raw_diff
    return raw_diff


def check_combustion(graha: str, arc: float, orbs: dict) -> tuple[bool, bool]:
    """
    Determine whether a graha is combust or deeply combust.

    Args:
        graha: Planet name
        arc:   Angular arc from Sun (degrees, 0–180)
        orbs:  Dict mapping graha → {'orb': float, 'deep': float}
               Keys match bg_combustion_orbs columns.

    Returns:
        (is_combust, is_deeply_combust)
        Sun itself → (False, False).
        Rahu/Ketu: returns based on orbs table (tradition varies).
    """
    if graha == "Sun":
        return False, False

    graha_orbs = orbs.get(graha)
    if graha_orbs is None:
        return False, False

    orb       = float(graha_orbs.get("orb", graha_orbs.get("orb_degrees", 0)))
    deep_orb  = float(graha_orbs.get("deep", graha_orbs.get("deep_orb_degrees", 0)))

    is_deeply = arc <= deep_orb
    is_combust_ = arc <= orb
    return is_combust_, is_deeply


def compute_tatkalika_relation(planet_house: int, reference_planet_house: int) -> str:
    """
    Compute tatkalika (temporary) friendship based on house positions.

    Classical rule (BPHS Ch.27): A planet occupying the 2nd, 3rd, 4th, 10th,
    11th, or 12th house FROM the reference planet is a temporary friend.
    All others (1st = same sign, 5th–9th) are temporary enemies.

    Args:
        planet_house:           House number of the planet being evaluated
        reference_planet_house: House of the planet we're computing relation FROM

    Returns:
        'friend' or 'enemy'
    """
    offset = (planet_house - reference_planet_house) % 12
    # offset 0 = same house; 1 = 2nd from; etc.
    friend_offsets = {1, 2, 3, 9, 10, 11}   # 2nd, 3rd, 4th, 10th, 11th, 12th from reference
    return "friend" if offset in friend_offsets else "enemy"


def compute_panchadha_maitri(naisargika: str, tatkalika: str) -> str:
    """
    Combine naisargika (permanent) and tatkalika (temporary) friendship
    to derive the 5-fold (panchadha) maitri classification.

    5-fold result matrix (BPHS Ch.27):
        friend   + friend   → great_friend
        friend   + enemy    → neutral
        neutral  + friend   → friend
        neutral  + enemy    → enemy
        enemy    + friend   → neutral
        enemy    + enemy    → great_enemy

    Args:
        naisargika: 'friend', 'neutral', or 'enemy'
        tatkalika:  'friend' or 'enemy'

    Returns:
        'great_friend', 'friend', 'neutral', 'enemy', or 'great_enemy'
    """
    _MATRIX: dict[tuple[str, str], str] = {
        ("friend",  "friend"): "great_friend",
        ("friend",  "enemy"):  "neutral",
        ("neutral", "friend"): "friend",
        ("neutral", "enemy"):  "enemy",
        ("enemy",   "friend"): "neutral",
        ("enemy",   "enemy"):  "great_enemy",
    }
    return _MATRIX.get((naisargika, tatkalika), "neutral")


def compute_condition_score_v1(
    dignity_score: Optional[float],
    deeptaadi:     Optional[str],
    baladi:        Optional[str],
    is_combust:    bool,
    is_deeply_combust: bool,
    is_retrograde: bool,
    varga_score:   Optional[float],
) -> tuple[Optional[float], dict]:
    """
    Compute the unified condition score (version 1).

    Score is 0.0–1.0. Returns (None, {}) when required inputs are missing.

    Formula:
        raw = (dignity_weight × dignity_score)
            + (deeptaadi_weight × deeptaadi_score)
            + (baladi_weight × baladi_score)
            + (varga_weight × varga_score_or_fallback)
            − (combustion_penalty when combust)

    Combustion penalty: 0.15 for combust, 0.25 for deeply combust.
    Retrograde: ±0 (retrograde is not inherently positive or negative;
                    deeptaadi already encodes vikala for retrograde+enemy).

    Returns:
        (score: float | None, breakdown: dict)
    """
    breakdown: dict[str, Any] = {}

    # Require dignity_score at minimum
    if dignity_score is None:
        return None, breakdown

    # Deeptaadi component
    deeptaadi_score = _DEEPTAADI_SCORES.get(deeptaadi, 0.5) if deeptaadi else None
    if deeptaadi_score is None:
        return None, breakdown

    # Baladi component
    baladi_score = _BALADI_SCORES.get(baladi, 0.5) if baladi else None
    if baladi_score is None:
        return None, breakdown

    # Varga component — fall back to dignity_score when unavailable
    effective_varga = varga_score if varga_score is not None else dignity_score
    breakdown["varga_fallback_used"] = varga_score is None

    # Combustion penalty
    if is_deeply_combust:
        combustion_penalty = 0.25
    elif is_combust:
        combustion_penalty = 0.15
    else:
        combustion_penalty = 0.0

    w = _FORMULA_WEIGHTS
    raw = (
        w["dignity_d1"]  * dignity_score
        + w["deeptaadi"] * deeptaadi_score
        + w["baladi"]    * baladi_score
        + w["varga"]     * effective_varga
        - w["combustion"] * (combustion_penalty / 0.25 if combustion_penalty > 0 else 0)
    )

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(1.0, raw))

    breakdown.update({
        "dignity_d1_score":   round(dignity_score, 4),
        "deeptaadi_state":    deeptaadi,
        "deeptaadi_score":    round(deeptaadi_score, 4),
        "baladi_state":       baladi,
        "baladi_score":       round(baladi_score, 4),
        "varga_score":        round(effective_varga, 4),
        "combustion_penalty": round(combustion_penalty, 4),
        "is_retrograde":      is_retrograde,
        "raw_score":          round(raw, 6),
        "clamped_score":      round(score, 6),
        "formula_version":    "condition_formula_v1",
        "weights":            w,
    })

    return round(score, 6), breakdown


# ── Motion state helper ───────────────────────────────────────────────────────

def compute_motion_state(graha: str, speed: float) -> str:
    """
    Derive the motion_state label from the graha's daily speed.

    Uses module-level thresholds matching bg_motion_state_thresholds seed data.
    Returns one of: 'vakra', 'anuvakra', 'manda', 'sama', 'atichara'.
    """
    # Nodes are always retrograde
    if graha in ("Rahu", "Ketu"):
        return "vakra"
    # Sun never retrograde
    if graha == "Sun":
        if speed > 1.02:
            return "atichara"
        return "sama"
    # Moon
    if graha == "Moon":
        if speed > 15.0:
            return "atichara"
        return "sama"

    # Classical planets: Mars, Mercury, Jupiter, Venus, Saturn
    _THRESHOLDS: dict[str, dict[str, Any]] = {
        "Mars":    {"vakra": 0, "anuvakra_hi": 0.1, "manda_hi": 0.5, "sama_hi": 0.8},
        "Mercury": {"vakra": 0, "anuvakra_hi": 0.1, "sama_hi": 2.5},
        "Jupiter": {"vakra": 0, "anuvakra_hi": 0.05, "sama_hi": 0.15},
        "Venus":   {"vakra": 0, "anuvakra_hi": 0.05, "sama_hi": 1.3},
        "Saturn":  {"vakra": 0, "anuvakra_hi": 0.02, "sama_hi": 0.13},
    }

    t = _THRESHOLDS.get(graha, {})
    if not t:
        return "sama"

    if speed < t.get("vakra", 0):
        return "vakra"
    if speed < t.get("anuvakra_hi", 0):
        return "anuvakra"
    if "manda_hi" in t and speed < t["manda_hi"]:
        return "manda"
    if speed < t.get("sama_hi", 999):
        return "sama"
    return "atichara"


# ── DB helpers ────────────────────────────────────────────────────────────────

def _load_dignity_ref(conn: Any) -> dict[str, dict]:
    """Load bg_dignity_reference into a dict keyed by graha name."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, exaltation_sign, exaltation_degree,
                       debilitation_sign, debilitation_degree,
                       moolatrikona_sign, moolatrikona_from, moolatrikona_to,
                       own_signs
                FROM bg_dignity_reference
            """)
            return {
                row[0]: {
                    "exaltation_sign":     row[1],
                    "exaltation_degree":   float(row[2]) if row[2] is not None else None,
                    "debilitation_sign":   row[3],
                    "debilitation_degree": float(row[4]) if row[4] is not None else None,
                    "moolatrikona_sign":   row[5],
                    "moolatrikona_from":   float(row[6]) if row[6] is not None else None,
                    "moolatrikona_to":     float(row[7]) if row[7] is not None else None,
                    "own_signs":           list(row[8]) if row[8] else [],
                }
                for row in cur.fetchall()
            }
    except Exception as exc:
        logger.warning("[ga_condition_writer] bg_dignity_reference not available: %s", exc)
        return {}


def _load_combustion_orbs(conn: Any) -> dict[str, dict]:
    """Load bg_combustion_orbs into a dict keyed by graha name."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, orb_degrees, deep_orb_degrees
                FROM bg_combustion_orbs
            """)
            return {
                row[0]: {"orb": float(row[1]), "deep": float(row[2])}
                for row in cur.fetchall()
            }
    except Exception as exc:
        logger.warning("[ga_condition_writer] bg_combustion_orbs not available: %s", exc)
        # Fallback to hardcoded classical values
        return {
            "Moon":    {"orb": 12.0, "deep": 10.0},
            "Mars":    {"orb": 17.0, "deep": 15.0},
            "Mercury": {"orb": 14.0, "deep": 12.0},
            "Jupiter": {"orb": 11.0, "deep":  9.0},
            "Venus":   {"orb": 10.0, "deep":  8.0},
            "Saturn":  {"orb": 15.0, "deep": 12.0},
            "Rahu":    {"orb":  9.0, "deep":  7.0},
            "Ketu":    {"orb":  9.0, "deep":  7.0},
        }


def _load_naisargika_friendships(conn: Any) -> dict[str, dict[str, str]]:
    """Load bg_graha_naisargika_friendship into a nested dict."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, other_graha, relation
                FROM bg_graha_naisargika_friendship
            """)
            result: dict[str, dict[str, str]] = {}
            for graha, other, relation in cur.fetchall():
                if graha not in result:
                    result[graha] = {}
                result[graha][other] = relation
            return result
    except Exception as exc:
        logger.warning("[ga_condition_writer] bg_graha_naisargika_friendship not available: %s", exc)
        return {}


def _load_graha_positions(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """
    Load graha positions from chart_facts for a given chart + ayanamsha.

    Returns list of dicts with keys:
        graha, sign, degree_in_sign, longitude, speed, house, is_retrograde
    Uses a resilient column-discovery approach — tries preferred column names
    and falls back gracefully.
    """
    rows: dict[str, dict] = {}

    # Step 1: Get sign and degree_in_sign from graha_sign_attributes category
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT fact_subject, fact_key, fact_value_text, fact_value_num
                FROM chart_facts
                WHERE chart_id    = %s
                  AND ayanamsha_id = %s
                  AND fact_category IN ('graha_sign_attributes', 'graha_position')
                  AND fact_key IN ('sign', 'degree_in_sign', 'longitude_sidereal',
                                   'house_d1', 'retrograde_flag', 'speed_dps',
                                   'house', 'longitude')
            """, (chart_id, ayanamsha_id))

            for subject, key, val_text, val_num in cur.fetchall():
                # Map UPPER_SNAKE subjects back to planet names
                subject_to_graha = {
                    "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury",
                    "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
                    "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
                }
                graha = subject_to_graha.get(subject)
                if graha is None:
                    continue
                if graha not in rows:
                    rows[graha] = {"graha": graha}
                if key == "sign":
                    rows[graha]["sign"] = val_text
                elif key == "degree_in_sign":
                    rows[graha]["degree_in_sign"] = float(val_num) if val_num is not None else None
                elif key in ("longitude_sidereal", "longitude"):
                    rows[graha]["longitude"] = float(val_num) if val_num is not None else None
                elif key in ("house_d1", "house"):
                    rows[graha]["house"] = int(val_num) if val_num is not None else None
                elif key == "retrograde_flag":
                    rows[graha]["is_retrograde"] = (val_text == "retrograde") if val_text else False
                elif key == "speed_dps":
                    rows[graha]["speed"] = float(val_num) if val_num is not None else None

    except Exception as exc:
        logger.error("[ga_condition_writer] Error loading chart_facts positions: %s", exc)
        return []

    return list(rows.values())


def _load_varga_dignity_spread(
    conn: Any, chart_id: str, ayanamsha_id: str, graha: str
) -> Optional[dict]:
    """
    Load varga dignity spread from chart_divisionals for a single graha.
    Returns None when chart_divisionals is unavailable or has no data.
    """
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            # chart_divisionals.graha stores Title Case ("Sun", "Moon", ...) — pass graha directly.
            # Include both 'varga_position' (sign) and 'varga_dignity' (dignity_status, dignity_score).
            cur.execute("""
                SELECT varga, fact_key, fact_value_text, fact_value_num
                FROM chart_divisionals
                WHERE chart_id       = %s
                  AND ayanamsha_id   = %s
                  AND graha          = %s
                  AND fact_category IN ('varga_position', 'varga_dignity')
                  AND fact_key       IN ('sign', 'dignity_status', 'dignity_score')
            """, (chart_id, ayanamsha_id, graha))

            spread: dict[str, Any] = {}
            for varga, key, val_text, val_num in cur.fetchall():
                if varga not in spread:
                    spread[varga] = {}
                if key == "sign":
                    spread[varga]["sign"] = val_text
                elif key == "dignity_status":
                    spread[varga]["dignity"] = val_text
                elif key == "dignity_score":
                    spread[varga]["score"] = float(val_num) if val_num is not None else None

            if not spread:
                return None

            return spread

    except Exception as exc:
        logger.warning("[ga_condition_writer] chart_divisionals varga spread failed for %s: %s", graha, exc)
        return None


def _compute_varga_composite(spread: Optional[dict]) -> Optional[float]:
    """Compute weighted average dignity score across available vargas."""
    if not spread:
        return None

    # Varga weights for composite (shodasavarga emphasis)
    _VARGA_WEIGHTS: dict[str, float] = {
        "D1": 3.5, "D9": 3.0, "D2": 0.5, "D3": 0.5, "D4": 0.5,
        "D7": 0.5, "D10": 1.5, "D12": 0.5, "D16": 0.5, "D20": 0.5,
        "D24": 0.5, "D27": 0.5, "D30": 0.5, "D40": 0.5, "D45": 0.5, "D60": 1.0,
    }

    total_w = 0.0
    total_s = 0.0
    for varga, data in spread.items():
        score = data.get("score")
        if score is None:
            # Derive score from dignity label if available
            dignity = data.get("dignity")
            if dignity:
                score = DIGNITY_SCORES.get(dignity)
        if score is not None:
            w = _VARGA_WEIGHTS.get(varga, 0.25)
            total_w += w
            total_s += w * float(score)

    if total_w == 0:
        return None
    return round(total_s / total_w, 6)


def _load_dasha_periods(
    conn: Any, chart_id: str, graha: str
) -> tuple[Optional[list], Optional[list]]:
    """
    Load mahadasha periods for this graha from chart_dashas.
    Returns (peak_periods, weak_periods) as JSON-serialisable lists.
    Peak = graha's own mahadasha; weak = based on condition context.
    """
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            # chart_dashas column is lord_graha (not graha_label)
            cur.execute("""
                SELECT system_id, level_n, lord_graha, start_iso, end_iso
                FROM chart_dashas
                WHERE chart_id   = %s
                  AND lord_graha = %s
                  AND level_n    = 1
                ORDER BY start_iso
                LIMIT 3
            """, (chart_id, graha))
            rows = cur.fetchall()
            if not rows:
                return None, None

            periods = [
                {
                    "dasha_label": f"{row[2]} Mahadasha",
                    "system_id":   row[0],
                    "start_date":  row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                    "end_date":    row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                    "reason":      f"{graha} mahadasha period",
                }
                for row in rows
            ]
            return periods, None   # weak periods require cross-reference with condition score

    except Exception as exc:
        logger.warning("[ga_condition_writer] chart_dashas lookup failed for %s: %s", graha, exc)
        return None, None


def _detect_graha_yuddha(position_map: dict[str, dict]) -> dict[str, tuple[str, str]]:
    """
    Detect graha yuddha (planetary war) pairs.

    Classical rule: two classical planets (excluding Rahu/Ketu and Sun/Moon)
    within 1° of each other in the same sign → graha yuddha.
    Winner = planet with higher latitude; here approximated by higher
    ecliptic longitude (simplified — true determination requires latitude data).

    Returns dict: graha → (opponent_graha, 'winner'/'loser'/'none')
    """
    classical = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    result: dict[str, tuple[str, str]] = {}

    for i, g1 in enumerate(classical):
        for g2 in classical[i+1:]:
            d1 = position_map.get(g1)
            d2 = position_map.get(g2)
            if not d1 or not d2:
                continue
            l1 = d1.get("longitude")
            l2 = d2.get("longitude")
            if l1 is None or l2 is None:
                continue
            # Same sign check
            if d1.get("sign") != d2.get("sign"):
                continue
            # Arc within 1°
            arc = abs(l1 - l2)
            if arc > 180:
                arc = 360 - arc
            if arc <= 1.0:
                # Winner = higher longitude in direct motion (simplified)
                if l1 > l2:
                    result[g1] = (g2, "winner")
                    result[g2] = (g1, "loser")
                else:
                    result[g2] = (g1, "winner")
                    result[g1] = (g2, "loser")

    return result


# ── Main build function ───────────────────────────────────────────────────────

def build_ga_condition_substep(
    chart_id: str,
    build_id: Any,
    ayanamsha_id: str,
    conn: Any,
) -> int:
    """
    Build ga_condition_composite rows for one chart + ayanamsha.

    Steps:
      1. Load reference tables (dignity, combustion orbs, naisargika friendship)
      2. Load graha positions from chart_facts
      3. Load varga dignity spread from chart_divisionals (best-effort)
      4. Compute all condition fields for each graha
      5. Detect graha yuddha pairs
      6. FORENSIC assertion for canonical chart
      7. Delete-then-insert (idempotent replace)

    Returns:
        Number of rows inserted.
    """
    computed_at = datetime.now(timezone.utc).isoformat()

    # ── Load reference data ────────────────────────────────────────────────────
    dignity_ref     = _load_dignity_ref(conn)
    combustion_orbs = _load_combustion_orbs(conn)
    naisargika_db   = _load_naisargika_friendships(conn)

    # ── Load positions ─────────────────────────────────────────────────────────
    position_list = _load_graha_positions(conn, chart_id, ayanamsha_id)
    if not position_list:
        logger.warning(
            "[ga_condition_writer] No position rows for chart_id=%s ayanamsha=%s",
            chart_id, ayanamsha_id,
        )
        return 0

    # Index by graha name
    position_map: dict[str, dict] = {p["graha"]: p for p in position_list}

    # ── Get Sun longitude for combustion arc computation ───────────────────────
    sun_pos = position_map.get("Sun")
    sun_longitude = sun_pos.get("longitude") if sun_pos else None

    # ── Detect graha yuddha ────────────────────────────────────────────────────
    yuddha_map = _detect_graha_yuddha(position_map)

    # ── Build one row per graha ────────────────────────────────────────────────
    insert_rows: list[dict] = []
    forensic_rows: dict[str, dict] = {}   # graha → computed row for FORENSIC check

    for graha in ALL_GRAHAS:
        pos = position_map.get(graha)
        if pos is None:
            logger.debug("[ga_condition_writer] graha=%s not in positions for ay=%s", graha, ayanamsha_id)
            continue

        sign           = pos.get("sign")
        degree_in_sign = pos.get("degree_in_sign")
        longitude      = pos.get("longitude")
        speed          = pos.get("speed")
        house          = pos.get("house")
        is_retrograde  = bool(pos.get("is_retrograde", False))

        # ── Dignity D1 ────────────────────────────────────────────────────────
        dignity_d1: Optional[str] = None
        dignity_score_d1: Optional[float] = None
        if sign and degree_in_sign is not None:
            dref = dignity_ref.get(graha)
            dignity_d1 = dignity_d1_from_sign(graha, sign, degree_in_sign, dref)
            dignity_score_d1 = DIGNITY_SCORES.get(dignity_d1)

        # ── Combustion ────────────────────────────────────────────────────────
        combustion_arc: Optional[float] = None
        is_combust = False
        is_deeply_combust = False
        if longitude is not None and sun_longitude is not None and graha != "Sun":
            combustion_arc = compute_combustion_arc(longitude, sun_longitude)
            is_combust, is_deeply_combust = check_combustion(graha, combustion_arc, combustion_orbs)

        # ── Avasthas ─────────────────────────────────────────────────────────
        avastha_baladi: Optional[str] = None
        avastha_jagradadi: Optional[str] = None
        avastha_deeptaadi: Optional[str] = None
        if degree_in_sign is not None:
            avastha_baladi    = avastha_baladi_from_degree(degree_in_sign)
        if dignity_d1:
            avastha_jagradadi = avastha_jagradadi_from_dignity(dignity_d1)
            avastha_deeptaadi = avastha_deeptaadi_from_dignity_and_state(
                dignity_d1, is_combust, is_retrograde
            )

        # lajjitaadi and sayanadi require chart-level context; store None
        avastha_lajjitaadi: Optional[str] = None
        avastha_sayanadi:   Optional[str] = None

        # ── Motion state ──────────────────────────────────────────────────────
        motion_state: Optional[str] = None
        if speed is not None:
            motion_state = compute_motion_state(graha, speed)
        elif graha in ("Rahu", "Ketu"):
            motion_state = "vakra"

        # ── Naisargika friendship (graha → sign lord) ─────────────────────────
        naisargika_relation: Optional[str] = None
        sign_lord = SIGN_LORDS.get(sign or "") if sign else None
        if sign_lord and sign_lord != graha:
            # Use DB-loaded friendships if available, else derive from dignity
            if naisargika_db:
                naisargika_relation = naisargika_db.get(graha, {}).get(sign_lord, "neutral")
            else:
                # Fallback: derive from dignity
                if dignity_d1 in ("friend_sign", "great_friend_sign"):
                    naisargika_relation = "friend"
                elif dignity_d1 in ("enemy_sign", "great_enemy_sign"):
                    naisargika_relation = "enemy"
                elif dignity_d1 in ("exalted", "moolatrikona", "own"):
                    naisargika_relation = "friend"  # own = effectively friend of self
                else:
                    naisargika_relation = "neutral"
        elif sign_lord == graha:
            naisargika_relation = "friend"  # in own sign

        # ── Tatkalika + panchadha ──────────────────────────────────────────────
        tatkalika_relation: Optional[str] = None
        panchadha_relation: Optional[str] = None
        if house and sign_lord and sign_lord != graha:
            sign_lord_pos = position_map.get(sign_lord)
            if sign_lord_pos and sign_lord_pos.get("house"):
                tatkalika_relation = compute_tatkalika_relation(
                    sign_lord_pos["house"], house
                )
                if naisargika_relation:
                    panchadha_relation = compute_panchadha_maitri(
                        naisargika_relation, tatkalika_relation
                    )

        # ── Varga dignity spread ───────────────────────────────────────────────
        varga_spread     = _load_varga_dignity_spread(conn, chart_id, ayanamsha_id, graha)
        varga_composite  = _compute_varga_composite(varga_spread)

        # ── Graha yuddha ──────────────────────────────────────────────────────
        yuddha_data       = yuddha_map.get(graha)
        yuddha_with:   Optional[str] = yuddha_data[0] if yuddha_data else None
        yuddha_result: Optional[str] = yuddha_data[1] if yuddha_data else None

        # ── Condition score ───────────────────────────────────────────────────
        condition_score_val, breakdown = compute_condition_score_v1(
            dignity_score    = dignity_score_d1,
            deeptaadi        = avastha_deeptaadi,
            baladi           = avastha_baladi,
            is_combust       = is_combust,
            is_deeply_combust= is_deeply_combust,
            is_retrograde    = is_retrograde,
            varga_score      = varga_composite,
        )

        # ── Dasha trajectory ──────────────────────────────────────────────────
        peak_periods, weak_periods = _load_dasha_periods(conn, chart_id, graha)

        row = {
            "chart_id":                 chart_id,
            "build_id":                 str(build_id) if build_id else None,
            "ayanamsha_id":             ayanamsha_id,
            "graha":                    graha,
            "dignity_d1":               dignity_d1,
            "dignity_score_d1":         dignity_score_d1,
            "varga_dignity_spread":     json.dumps(varga_spread) if varga_spread else None,
            "varga_dignity_composite":  varga_composite,
            "avastha_baladi":           avastha_baladi,
            "avastha_jagradadi":        avastha_jagradadi,
            "avastha_deeptaadi":        avastha_deeptaadi,
            "avastha_lajjitaadi":       avastha_lajjitaadi,
            "avastha_sayanadi":         avastha_sayanadi,
            "motion_state":             motion_state,
            "speed_degrees_per_day":    speed,
            "is_retrograde":            is_retrograde,
            "combustion_arc_from_sun":  combustion_arc,
            "is_combust":               is_combust,
            "is_deeply_combust":        is_deeply_combust,
            "naisargika_relation":      naisargika_relation,
            "tatkalika_relation":       tatkalika_relation,
            "panchadha_relation":       panchadha_relation,
            "graha_yuddha_with":        yuddha_with,
            "graha_yuddha_result":      yuddha_result,
            "condition_score":          condition_score_val,
            "condition_formula_version":"condition_formula_v1",
            "condition_score_breakdown":json.dumps(breakdown) if breakdown else None,
            "peak_dasha_periods":       json.dumps(peak_periods) if peak_periods else None,
            "weak_dasha_periods":       json.dumps(weak_periods) if weak_periods else None,
            "computed_at":              computed_at,
        }
        insert_rows.append(row)
        forensic_rows[graha] = row

    if not insert_rows:
        return 0

    # ── FORENSIC assertions for canonical chart ────────────────────────────────
    if chart_id == CANONICAL_CHART_ID:
        sun_row = forensic_rows.get("Sun")
        if sun_row is not None:
            sun_dignity = sun_row.get("dignity_d1")
            assert sun_dignity not in ("exalted", "moolatrikona", "own"), (
                f"FORENSIC FAIL: Sun in Capricorn cannot be in dignity (exalted/moolatrikona/own), "
                f"got dignity_d1='{sun_dignity}'. "
                f"Sun's exaltation=Aries, own=Leo, moolatrikona=Leo. "
                f"Capricorn is owned by Saturn; Sun–Saturn are enemies."
            )
            logger.info(
                "[ga_condition_writer] FORENSIC PASS: Sun dignity_d1='%s' (correctly NOT exalted/own/moolatrikona) "
                "for ayanamsha=%s",
                sun_dignity, ayanamsha_id,
            )

        # FORENSIC: Saturn=Libra → exalted (BPHS Ch.3)
        saturn_rows = [r for r in insert_rows if r.get("graha") == "Saturn"]
        if saturn_rows:
            assert saturn_rows[0].get("dignity_d1") == "exalted", \
                f"FORENSIC FAIL: Saturn=Libra must be exalted, got {saturn_rows[0].get('dignity_d1')}"

    # ── Idempotent replace: DELETE then INSERT ─────────────────────────────────
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ga_condition_composite WHERE chart_id = %s AND ayanamsha_id = %s",
            (chart_id, ayanamsha_id),
        )
        deleted = getattr(cur, "rowcount", 0) or 0
        logger.debug(
            "[ga_condition_writer] Deleted %d prior rows for chart=%s ay=%s",
            deleted, chart_id, ayanamsha_id,
        )

    # ── INSERT ────────────────────────────────────────────────────────────────
    cols = [
        "chart_id", "build_id", "ayanamsha_id", "graha",
        "dignity_d1", "dignity_score_d1",
        "varga_dignity_spread", "varga_dignity_composite",
        "avastha_baladi", "avastha_jagradadi", "avastha_deeptaadi",
        "avastha_lajjitaadi", "avastha_sayanadi",
        "motion_state", "speed_degrees_per_day", "is_retrograde",
        "combustion_arc_from_sun", "is_combust", "is_deeply_combust",
        "naisargika_relation", "tatkalika_relation", "panchadha_relation",
        "graha_yuddha_with", "graha_yuddha_result",
        "condition_score", "condition_formula_version", "condition_score_breakdown",
        "peak_dasha_periods", "weak_dasha_periods",
        "computed_at",
    ]
    placeholders = ", ".join(["%s"] * len(cols))
    col_str = ", ".join(cols)
    sql = f"INSERT INTO ga_condition_composite ({col_str}) VALUES ({placeholders})"

    inserted = 0
    with conn.cursor() as cur:
        for row in insert_rows:
            values = [row[c] for c in cols]
            cur.execute(sql, values)
            inserted += 1

    logger.info(
        "[ga_condition_writer] Inserted %d rows for chart=%s ayanamsha=%s",
        inserted, chart_id, ayanamsha_id,
    )
    return inserted
