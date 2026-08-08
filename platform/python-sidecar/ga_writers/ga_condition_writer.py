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
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg.rows

from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS, PLANET_TO_SUBJECT
from pyjhora_adapter.version import ENGINE_VERSION

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
    "Rahu": "Taurus", "Ketu": "Scorpio",  # Parashari mainstream — L0 sealed 2026-06-24
}
_DEBILITATION: dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
    "Rahu": "Scorpio", "Ketu": "Taurus",  # Parashari mainstream — L0 sealed 2026-06-24
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

# ── Amendment 2 constants ─────────────────────────────────────────────────────

# Maps Title-case dignity values from chart_divisionals → lowercase canonical keys
# used by avastha_deeptaadi_from_dignity_and_state and DIGNITY_SCORES.
_DIVISIONAL_DIGNITY_NORMALIZE: dict[str, str] = {
    "Exalted":      "exalted",
    "Own":          "own",
    "Moolatrikona": "moolatrikona",
    "Friend":       "friend_sign",
    "Neutral":      "neutral_sign",
    "Enemy":        "enemy_sign",
    "Debilitated":  "debilitated",
}

# Avasthas that are intrinsically D1 concepts — no canonical per-varga method exists.
# Each tuple is (fact_category, reason_text stored in fact_value_text).
INTRINSICALLY_D1_AVASTHAS = [
    (
        "graha_avastha_jagradadi_per_varga",
        "floored: waking/dreaming state is a single D1 concept with no canonical varga extension (BPHS)",
    ),
    (
        "graha_avastha_sayanadi_per_varga",
        "floored: 12 sleeping-posture states are D1-only per Parashara; no canonical varga method exists",
    ),
    (
        "graha_avastha_lajjitadi_per_varga",
        "floored: ashamed/glad states depend on D1 conjunction/aspect context; not computable per-varga",
    ),
]


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



# Retrograde planets get a TIGHTER combustion orb than direct motion per
# classical authority (Saravali / Phaladeepika retrograde exception) —
# M-19: "Mercury 12°R, Venus 8°R". These values are exactly the SAME values
# already carried as each planet's own deep_orb_degrees in bg_combustion_orbs
# (Mercury deep=12, Venus deep=8) — the classical retrograde exception
# collapses the ordinary combustion threshold down to the direct-motion deep
# (atichara) threshold. No new schema/migration needed: this is read from the
# same bg_combustion_orbs row already loaded, just gated on is_retrograde.
# Only Mercury and Venus carry a documented retrograde exception; all other
# classical grahas use their direct-motion orb regardless of motion state.
_RETROGRADE_COMBUSTION_GRAHAS = ("Mercury", "Venus")


def check_combustion(
    graha: str, arc: float, orbs: dict, is_retrograde: bool = False,
) -> tuple[bool, bool]:
    """
    Determine whether a graha is combust or deeply combust.

    Args:
        graha:         Planet name
        arc:           Angular arc from Sun (degrees, 0–180)
        orbs:          Dict mapping graha → {'orb': float, 'deep': float}
                       Keys match bg_combustion_orbs columns.
        is_retrograde: Whether the graha is currently retrograde. Only
                       Mercury/Venus have a documented retrograde-orb
                       exception (M-19); see _RETROGRADE_COMBUSTION_GRAHAS.

    Returns:
        (is_combust, is_deeply_combust)
        Sun itself → (False, False) — the Sun cannot be combust by itself.
        Rahu/Ketu → (False, False) UNCONDITIONALLY (M-19): the nodes have no
        physical body/disc to be "obscured by sunlight", which is the
        astronomical basis of combustion (asta). bg_combustion_orbs still
        carries legacy Rahu/Ketu rows for other traditions/consumers, but
        this writer's condition-score combustion penalty never applies to
        them — a chart_facts row claiming node combustion is a fabricated
        computation (B.10), not a classically-grounded one.
    """
    if graha in ("Sun", "Rahu", "Ketu"):
        return False, False

    graha_orbs = orbs.get(graha)
    if graha_orbs is None:
        return False, False

    orb       = float(graha_orbs.get("orb", graha_orbs.get("orb_degrees", 0)))
    deep_orb  = float(graha_orbs.get("deep", graha_orbs.get("deep_orb_degrees", 0)))

    effective_orb = deep_orb if (is_retrograde and graha in _RETROGRADE_COMBUSTION_GRAHAS) else orb

    is_deeply = arc <= deep_orb
    is_combust_ = arc <= effective_orb
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
        "Mercury": {"vakra": 0, "anuvakra_hi": 0.1, "sama_hi": 2.0},  # sealed at L0 2026-06-24
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

def _rollback_to_savepoint(conn: Any, sp: str) -> None:
    """Best-effort ROLLBACK TO SAVEPOINT — used by the SAVEPOINT-guarded
    per-graha lookups below so a single failed/slow read (e.g. a chart_dashas
    lookup that hits statement_timeout under load) rolls back cleanly instead
    of leaving the shared substep transaction in Postgres's aborted state.
    Without this, the writer's swallow-without-rollback turned one slow query
    into InFailedSqlTransaction on every subsequent statement + the final
    DELETE — a failed L1 ga_condition that blocked the whole L2-L5 DAG
    (BA-P3 Abhinandan diagnostic, 2026-07-06)."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
    except Exception:
        pass


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


def _load_motion_thresholds(conn: Any) -> dict[str, dict]:
    """Load bg_motion_state_thresholds from L0. Returns {graha: {motion_state: (low, high, kind)}}."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT graha, motion_state, speed_threshold_low, speed_threshold_high, threshold_type
                FROM bg_motion_state_thresholds
            """)
            rows = cur.fetchall()
        result: dict[str, dict] = {}
        for graha, state, low, high, kind in rows:
            result.setdefault(graha, {})[state] = (
                float(low) if low is not None else None,
                float(high) if high is not None else None,
                kind or "above",
            )
        return result
    except Exception as exc:
        logger.warning("[ga_condition_writer] bg_motion_state_thresholds unavailable: %s", exc)
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
    sp = "sp_ga_cond_varga"
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(f"SAVEPOINT {sp}")
            # chart_divisionals.graha stores Title Case ("Sun", "Moon", ...) — pass graha directly.
            # Include both 'varga_position' (sign) and 'varga_dignity' (dignity, overall_dignity_score).
            cur.execute("""
                SELECT varga, fact_key, fact_value_text, fact_value_num
                FROM chart_divisionals
                WHERE chart_id       = %s
                  AND ayanamsha_id   = %s
                  AND graha          = %s
                  AND fact_category IN ('varga_position', 'varga_dignity')
                  AND fact_key       IN ('sign', 'dignity', 'overall_dignity_score')
            """, (chart_id, ayanamsha_id, graha))
            fetched = cur.fetchall()
            cur.execute(f"RELEASE SAVEPOINT {sp}")

            spread: dict[str, Any] = {}
            for varga, key, val_text, val_num in fetched:
                if varga not in spread:
                    spread[varga] = {}
                if key == "sign":
                    spread[varga]["sign"] = val_text
                elif key == "dignity":
                    spread[varga]["dignity"] = val_text
                elif key == "overall_dignity_score":
                    spread[varga]["score"] = float(val_num) if val_num is not None else None

            if not spread:
                return None

            return spread

    except Exception as exc:
        logger.warning("[ga_condition_writer] chart_divisionals varga spread failed for %s: %s", graha, exc)
        _rollback_to_savepoint(conn, sp)
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


# Condition-score thresholds gating peak vs weak dasha-trajectory classification.
# Mirrors ga_condition_composite migration comment: peak = "high-condition periods",
# weak = "low-condition periods" (see migrations/251_ga_condition_composite.sql).
_PEAK_CONDITION_THRESHOLD = 0.65
_WEAK_CONDITION_THRESHOLD = 0.35


def _load_dasha_periods(
    conn: Any,
    chart_id: str,
    graha: str,
    condition_score: Optional[float] = None,
    dignity_d1: Optional[str] = None,
) -> tuple[Optional[list], Optional[list]]:
    """
    Load mahadasha periods for this graha from chart_dashas.
    Returns (peak_periods, weak_periods) as JSON-serialisable lists.

    Peak = graha's own mahadasha, when the graha's unified condition_score
    (dignity + avastha + varga + combustion, see compute_condition_score_v1)
    is classically strong (>= _PEAK_CONDITION_THRESHOLD).
    Weak = the mirror-image case: condition_score is classically weak
    (<= _WEAK_CONDITION_THRESHOLD) — e.g. debilitated / enemy-sign dignity,
    deep combustion, or poor avastha dragging the composite score down.
    Periods in the neutral middle band are neither peak nor weak and both
    fields are None for that graha (this is a real "no signal" case, not a
    stub — see BA-Phase-2.5 fast-follow #2).
    """
    sp = "sp_ga_cond_dasha"
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(f"SAVEPOINT {sp}")
            # chart_dashas column is lord_graha (not graha_label). Served by the
            # partial index chart_dashas_condition_lookup_idx (chart_id,
            # lord_graha, start_iso) WHERE level_n=1 (migration 415) — a direct
            # ~27-row seek, not the ~20K-row heap scan that used to time out.
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
            cur.execute(f"RELEASE SAVEPOINT {sp}")
            if not rows:
                return None, None

            if condition_score is None:
                # No condition score available to classify — cannot say peak or weak.
                return None, None

            if condition_score >= _PEAK_CONDITION_THRESHOLD:
                reason = (
                    f"{graha} mahadasha period — dasha lord in classically strong "
                    f"condition (condition_score={condition_score:.4f}"
                    + (f", dignity_d1={dignity_d1}" if dignity_d1 else "")
                    + ")"
                )
                periods = [
                    {
                        "dasha_label": f"{row[2]} Mahadasha",
                        "system_id":   row[0],
                        "start_date":  row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                        "end_date":    row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                        "reason":      reason,
                    }
                    for row in rows
                ]
                return periods, None

            if condition_score <= _WEAK_CONDITION_THRESHOLD:
                reason = (
                    f"{graha} mahadasha period — dasha lord in classically weak "
                    f"condition (condition_score={condition_score:.4f}"
                    + (f", dignity_d1={dignity_d1}" if dignity_d1 else "")
                    + ")"
                )
                periods = [
                    {
                        "dasha_label": f"{row[2]} Mahadasha",
                        "system_id":   row[0],
                        "start_date":  row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                        "end_date":    row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                        "reason":      reason,
                    }
                    for row in rows
                ]
                return None, periods

            # Neutral band — condition is neither classically strong nor weak.
            return None, None

    except Exception as exc:
        logger.warning("[ga_condition_writer] chart_dashas lookup failed for %s: %s", graha, exc)
        _rollback_to_savepoint(conn, sp)
        return None, None


def _detect_graha_yuddha(position_map: dict[str, dict]) -> dict[str, tuple[str, Optional[str]]]:
    """
    Detect graha yuddha (planetary war) pairs.

    Classical rule: two classical planets (excluding Rahu/Ketu and Sun/Moon)
    within 1° of each other in the same sign → graha yuddha.

    Winner determination is FLOORED per the JL-027 native ruling
    (00_ARCHITECTURE/JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md, RULED
    2026-07-08): the previously-shipped "higher longitude wins" proxy here was
    the *mirror-image* of ga_structural_writer's now-removed "lower longitude
    wins" proxy — JL-027 §1 documents these as "two contradictory uncited
    rules, one silently clobbering the other". JL-027 explicitly forbids
    shipping either longitude proxy as a winner determination (§2/§4) and
    ratifies Option A (northern ecliptic latitude wins) as doctrine, but
    *implementation* of Option A is deferred to R5 pending a Swiss Ephemeris
    latitude L1 fact + derivation ledger (§5/§6). JL-027 §"governs" explicitly
    scopes this ruling to ga_structural_writer._build_graha_yuddha_rows
    "+ downstream graha_yuddha readers" — this function's yuddha_result
    annotation on ga_condition_composite is such a reader, so it floors
    identically: opponent pairing (yuddha_with) is reported, winner/loser
    is not.

    Returns dict: graha → (opponent_graha, None)   # result always None (floored)
    """
    classical = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    result: dict[str, tuple[str, Optional[str]]] = {}

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
                # JL-027 FLOOR: no ratified classical rule decides a winner from
                # longitude alone. Report the opponent only; result is None.
                result[g1] = (g2, None)
                result[g2] = (g1, None)

    return result


# ── Amendment 2: Per-varga avastha helpers ───────────────────────────────────

def _build_per_varga_avastha_rows(
    conn: Any,
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
) -> list[dict]:
    """
    Build chart_facts rows for the two varga-computable avasthas (Baladi, Deeptadi)
    plus floor rows for the three intrinsically-D1 avasthas.

    Sources:
      - Part A (Baladi):   avastha_baladi_from_degree applied to degree_in_sign per varga.
      - Part B (Deeptadi): avastha_deeptaadi_from_dignity_and_state applied to dignity per varga,
                           with is_combust=False, is_retrograde=False (combustion is D1-only).
      - Part C (floors):   One row per graha × INTRINSICALLY_D1_AVASTHAS, fact_key='D_ALL',
                           verification_pass_status='floored'.

    Queries chart_divisionals for degree_in_sign (fact_key='degree_in_sign') and
    dignity_status (fact_key='dignity_status') per (graha, varga), excluding Lagna.

    Returns list of dicts ready for chart_facts insertion.
    """
    rows: list[dict] = []

    # ── Query chart_divisionals for per-varga degree + dignity ────────────────
    # The GA6 atomic model stores one row per (chart_id, ayanamsha_id, varga, graha, fact_key).
    # We aggregate degree_in_sign + dignity_status per (graha, varga) in Python.
    try:
        cur = conn.execute(
            """
            SELECT graha, varga, fact_key, fact_value_text, fact_value_num
            FROM chart_divisionals
            WHERE chart_id      = %s
              AND ayanamsha_id  = %s
              AND graha IS NOT NULL
              AND graha != 'Lagna'
              AND fact_key IN ('degree_in_sign', 'dignity')
            """,
            (chart_id, ayanamsha_id),
        )
        divisional_raw = cur.fetchall()
    except Exception as exc:
        logger.warning(
            "[ga_condition_writer] per_varga_avastha: chart_divisionals query failed: %s", exc
        )
        divisional_raw = []

    # Aggregate into {(graha, varga): {"degree_in_sign": float, "dignity": str}}
    varga_data: dict[tuple[str, str], dict] = {}
    for row in divisional_raw:
        # Support both dict-like and tuple rows
        if hasattr(row, "get"):
            graha    = row.get("graha")
            varga    = row.get("varga")
            fkey     = row.get("fact_key")
            fval_txt = row.get("fact_value_text")
            fval_num = row.get("fact_value_num")
        else:
            graha, varga, fkey, fval_txt, fval_num = row
        if not graha or not varga or not fkey:
            continue
        key = (graha, varga)
        if key not in varga_data:
            varga_data[key] = {}
        if fkey == "degree_in_sign" and fval_num is not None:
            varga_data[key]["degree_in_sign"] = float(fval_num)
        elif fkey == "dignity" and fval_txt is not None:
            varga_data[key]["dignity"] = fval_txt

    # ── Part A + B: varga-computable avasthas ─────────────────────────────────
    for (graha, varga), data in varga_data.items():
        degree_in_sign = data.get("degree_in_sign")
        dignity_raw    = data.get("dignity")

        # Part A — Baladi avastha
        if degree_in_sign is not None:
            baladi_val = avastha_baladi_from_degree(degree_in_sign)
            rows.append({
                "fact_id":                 str(uuid.uuid4()),
                "chart_id":                chart_id,
                "ayanamsha_id":            ayanamsha_id,
                "build_id":                build_id,
                "fact_category":           "graha_avastha_baladi_per_varga",
                "fact_subject":            PLANET_TO_SUBJECT.get(graha, graha.upper()),
                "fact_key":                varga,
                "fact_value_text":         baladi_val,
                "fact_value_num":          None,
                "fact_value_jsonb":        None,
                "unit":                    None,
                "citation_ref":            f"graha_avastha_baladi_per_varga.{graha}.{varga}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}",
                "citation_human":          f"{graha.capitalize()} baladi avastha in {varga}: {baladi_val}",
                "source_calculation":      f"ga_condition_writer.avastha_baladi_from_degree_per_varga/{eng_ver}",
                "verification_pass_status":"computed_extension",
                "engine_version":          eng_ver,
                "computed_at":             computed_at,
            })

        # Part B — Deeptadi avastha
        if dignity_raw is not None:
            normalized_dignity = _DIVISIONAL_DIGNITY_NORMALIZE.get(dignity_raw, "neutral_sign")
            deeptaadi_val = avastha_deeptaadi_from_dignity_and_state(
                normalized_dignity, is_combust=False, is_retrograde=False
            )
            rows.append({
                "fact_id":                 str(uuid.uuid4()),
                "chart_id":                chart_id,
                "ayanamsha_id":            ayanamsha_id,
                "build_id":                build_id,
                "fact_category":           "graha_avastha_deeptaadi_per_varga",
                "fact_subject":            PLANET_TO_SUBJECT.get(graha, graha.upper()),
                "fact_key":                varga,
                "fact_value_text":         deeptaadi_val,
                "fact_value_num":          None,
                "fact_value_jsonb":        None,
                "unit":                    None,
                "citation_ref":            f"graha_avastha_deeptaadi_per_varga.{graha}.{varga}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}",
                "citation_human":          f"{graha.capitalize()} deeptaadi avastha in {varga}: {deeptaadi_val}",
                "source_calculation":      f"ga_condition_writer.deeptaadi_from_graha_dignity_per_varga/{eng_ver}",
                "verification_pass_status":"computed_extension",
                "engine_version":          eng_ver,
                "computed_at":             computed_at,
            })

    # ── Part C: Intrinsically-D1 floor rows ───────────────────────────────────
    for graha in ALL_GRAHAS:
        for floor_cat, reason in INTRINSICALLY_D1_AVASTHAS:
            rows.append({
                "fact_id":                 str(uuid.uuid4()),
                "chart_id":                chart_id,
                "ayanamsha_id":            ayanamsha_id,
                "build_id":                build_id,
                "fact_category":           floor_cat,
                "fact_subject":            PLANET_TO_SUBJECT.get(graha, graha.upper()),
                "fact_key":                "D_ALL",
                "fact_value_text":         reason,
                "fact_value_num":          None,
                "fact_value_jsonb":        None,
                "unit":                    None,
                "citation_ref":            f"{floor_cat}.{graha}.D_ALL@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}",
                "citation_human":          f"{graha.capitalize()} {floor_cat}: floored (intrinsically D1, no per-varga computation)",
                "source_calculation":      f"ga_condition_writer.intrinsically_d1_avastha_floor/{eng_ver}",
                "verification_pass_status":"floored",
                "engine_version":          eng_ver,
                "computed_at":             computed_at,
            })

    return rows


def _insert_per_varga_avastha_rows(conn: Any, rows: list[dict]) -> None:
    """Delete-then-insert per (chart_id, ayanamsha_id, fact_category) for per-varga avastha categories."""
    if not rows:
        return

    # ── Idempotent delete scoped to the categories we are about to write ──────
    cats = sorted({r["fact_category"] for r in rows})
    ayanamshas = sorted({r["ayanamsha_id"] for r in rows})
    chart_ids  = sorted({r["chart_id"] for r in rows})
    for cid in chart_ids:
        conn.execute(
            "DELETE FROM chart_facts WHERE chart_id = %s AND fact_category = ANY(%s) AND ayanamsha_id = ANY(%s)",
            [cid, cats, ayanamshas],
        )

    # ── Bulk INSERT ───────────────────────────────────────────────────────────
    cols = [
        "fact_id", "chart_id", "ayanamsha_id", "build_id",
        "fact_category", "fact_subject", "fact_key",
        "fact_value_text", "fact_value_num", "fact_value_jsonb",
        "unit", "citation_ref", "citation_human",
        "source_calculation", "verification_pass_status",
        "engine_version", "computed_at",
    ]
    placeholders = ", ".join(["%s"] * len(cols))
    col_str = ", ".join(cols)
    sql = f"INSERT INTO chart_facts ({col_str}) VALUES ({placeholders})"
    for row in rows:
        values = [row[c] for c in cols]
        conn.execute(sql, values)


# ── Amendment BA-P3A: D1 sayanadi + lajjitadi + yuddha chart_facts rows ──────

# Sayanadi avasthas — 12 states per 2.5° within sign (BPHS ch.28, Parashari).
# Signs divided into 12 equal 2.5° zones (30°/12 = 2.5°).
_SAYANADI_STATES: list[str] = [
    "shayana",    # 0-2.5°   sleeping — weakened state
    "upavishtha", # 2.5-5°   seated
    "netrapani",  # 5-7.5°   covering eyes
    "prakashana", # 7.5-10°  illuminated — visible
    "gamana",     # 10-12.5° moving
    "agama",      # 12.5-15° approaching
    "sabha",      # 15-17.5° in assembly — active
    "agamana",    # 17.5-20° arrived
    "naiveshya",  # 20-22.5° offering
    "kautuka",    # 22.5-25° curious
    "nishkapata", # 25-27.5° innocent/transparent
    "nidra",      # 27.5-30° deep sleep — debilitated
]


def _sayanadi_from_degree(degree_in_sign: float) -> str:
    """Sayanadi avastha from degree within sign (0–30). BPHS ch.28."""
    idx = min(int(degree_in_sign / 2.5), 11)
    return _SAYANADI_STATES[idx]


def _lajjitadi_from_context(
    graha: str,
    dignity_d1: str,
    house: Optional[int],
    is_combust: bool,
    position_map: dict,
) -> str:
    """
    Lajjitadi avastha — 6 states from Phaladeepika ch.13 + BPHS:
      Lajjita  — in 5th/9th with Rahu or Ketu
      Garvita  — in exaltation or moolatrikona sign
      Kshudhita— lord of sign is enemy
      Trishita — in enemy sign
      Mudita   — in friend sign (aspected or placed by friend)
      Kshobhita— with Sun (combust) + malefic aspect

    Falls back to 'neutral' when context is unavailable.
    """
    if dignity_d1 in ("exalted", "moolatrikona"):
        return "garvita"
    if is_combust:
        return "kshobhita"
    if dignity_d1 == "debilitated":
        return "trishita"
    if house in (5, 9):
        for shadow in ("Rahu", "Ketu"):
            shadow_pos = position_map.get(shadow)
            if shadow_pos and shadow_pos.get("house") == house:
                return "lajjita"
    if dignity_d1 in ("friend_sign", "great_friend_sign"):
        return "mudita"
    if dignity_d1 in ("enemy_sign", "great_enemy_sign"):
        return "kshudhita"
    return "neutral"


def _build_d1_avastha_rows(
    conn: Any,
    chart_id: str,
    build_id: Optional[str],
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
) -> list[dict]:
    """
    Build D1-level chart_facts rows for:
      - graha_avastha_sayanadi     (12-state degree-based, BPHS)
      - graha_avastha_lajjitadi    (6-state context-based, Phaladeepika)

    NOTE (JL-026, 2026-07-07): the `graha_yuddha` chart_facts category is NO
    LONGER emitted here — ga_structural is its sole authoritative writer
    (_build_graha_yuddha_rows, richer two_pass_verified output). This removes the
    third ga_structural↔ga_condition dual-write (the delete-scope clobber that the
    migration-416 edge papered over). `_detect_graha_yuddha` is retained ONLY to
    annotate ga_condition_composite rows (graha_yuddha_with/result columns) — an
    internal avastha-context input, not a chart_facts category.

    Sources: _load_graha_positions() (already computed for ayanamsha_id).
    These supplement the existing ga_condition_composite columns.
    """
    rows: list[dict] = []
    try:
        positions = _load_graha_positions(conn, chart_id, ayanamsha_id)
    except Exception as exc:
        logger.warning("[ga_condition_writer] d1_avastha: position load failed: %s", exc)
        return []

    position_map: dict[str, dict] = {}
    for p in positions:
        graha = p.get("graha") or p.get("fact_subject", "")
        position_map[graha] = p

    sun_pos = position_map.get("Sun")
    sun_longitude = sun_pos.get("longitude") if sun_pos else None
    # M-19: this was previously an empty dict that never resolved a graha's
    # orb, silently forcing is_combust=False for every graha's lajjitadi
    # avastha regardless of true combustion state. Load the real L0
    # bg_combustion_orbs table (same source ga_condition_composite uses).
    combustion_orbs: dict = _load_combustion_orbs(conn)

    for graha in ALL_GRAHAS:
        pos = position_map.get(graha)
        if pos is None:
            continue

        sign         = pos.get("sign")
        deg_in_sign  = pos.get("degree_in_sign")
        longitude    = pos.get("longitude")
        house        = pos.get("house")
        is_retrograde = bool(pos.get("is_retrograde", False))

        dignity_d1 = dignity_d1_from_sign(graha, sign, deg_in_sign or 0.0) if sign else "neutral_sign"

        # Combustion for lajjitadi
        is_combust = False
        if longitude is not None and sun_longitude is not None and graha != "Sun":
            arc = compute_combustion_arc(longitude, sun_longitude)
            is_combust, _ = check_combustion(graha, arc, combustion_orbs, is_retrograde=is_retrograde)

        # ── Sayanadi row ──────────────────────────────────────────────────────
        if deg_in_sign is not None:
            sayanadi_val = _sayanadi_from_degree(float(deg_in_sign))
            rows.append({
                "fact_id":                 str(uuid.uuid4()),
                "chart_id":                chart_id,
                "ayanamsha_id":            ayanamsha_id,
                "build_id":                build_id or "",
                "fact_category":           "graha_avastha_sayanadi",
                "fact_subject":            PLANET_TO_SUBJECT.get(graha, graha.upper()),
                "fact_key":                "D1",
                "fact_value_text":         sayanadi_val,
                "fact_value_num":          None,
                "fact_value_jsonb":        None,
                "unit":                    None,
                "citation_ref":            f"graha_avastha_sayanadi.{graha}.D1@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}",
                "citation_human":          f"{graha} sayanadi avastha (D1): {sayanadi_val} (deg_in_sign={deg_in_sign:.2f}). BPHS ch.28: 12-state 2.5°-division rule.",
                "source_calculation":      f"ga_condition_writer._sayanadi_from_degree/{eng_ver}",
                "verification_pass_status":"computed_extension",
                "engine_version":          eng_ver,
                "computed_at":             computed_at,
            })

        # ── Lajjitadi row ─────────────────────────────────────────────────────
        lajjitadi_val = _lajjitadi_from_context(
            graha, dignity_d1, house, is_combust, position_map
        )
        rows.append({
            "fact_id":                 str(uuid.uuid4()),
            "chart_id":                chart_id,
            "ayanamsha_id":            ayanamsha_id,
            "build_id":                build_id or "",
            "fact_category":           "graha_avastha_lajjitadi",
            "fact_subject":            PLANET_TO_SUBJECT.get(graha, graha.upper()),
            "fact_key":                "D1",
            "fact_value_text":         lajjitadi_val,
            "fact_value_num":          None,
            "fact_value_jsonb":        None,
            "unit":                    None,
            "citation_ref":            f"graha_avastha_lajjitadi.{graha}.D1@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}",
            "citation_human":          (
                f"{graha} lajjitadi avastha (D1): {lajjitadi_val}. "
                "Phaladeepika ch.13 / BPHS: 6-state context rule "
                "(exalted=garvita, combust=kshobhita, debilitated=trishita, "
                "5/9+shadow=lajjita, friend=mudita, enemy=kshudhita)."
            ),
            "source_calculation":      f"ga_condition_writer._lajjitadi_from_context/{eng_ver}",
            "verification_pass_status":"computed_extension",
            "engine_version":          eng_ver,
            "computed_at":             computed_at,
        })

        # ── Graha yuddha chart_facts row REMOVED (JL-026, 2026-07-07) ─────────
        # ga_structural is the sole authoritative writer of the `graha_yuddha`
        # fact_category (_build_graha_yuddha_rows). Emitting it here too was the
        # third ga_structural↔ga_condition dual-write: identical delete scope
        # (chart_id, 'graha_yuddha', ayanamsha_id) → parallel clobber/deadlock,
        # and ga_structural (running after ga_condition via the mig-416 edge)
        # deleted+re-inserted these rows every build, so this write never
        # survived. Single-writer now; the mig-416 edge is removed (migration 419).

    return rows


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
    dignity_ref       = _load_dignity_ref(conn)
    combustion_orbs   = _load_combustion_orbs(conn)
    naisargika_db     = _load_naisargika_friendships(conn)
    motion_thresholds = _load_motion_thresholds(conn)  # L0 authority; not yet threaded into _classify_motion_state

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
            is_combust, is_deeply_combust = check_combustion(
                graha, combustion_arc, combustion_orbs, is_retrograde=is_retrograde
            )

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
        peak_periods, weak_periods = _load_dasha_periods(
            conn, chart_id, graha,
            condition_score=condition_score_val,
            dignity_d1=dignity_d1,
        )

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
            inserted += max(0, cur.rowcount)

    logger.info(
        "[ga_condition_writer] Inserted %d rows for chart=%s ayanamsha=%s",
        inserted, chart_id, ayanamsha_id,
    )

    # ── Amendment 2: Per-varga avastha rows ─────────────────────────────────────
    per_varga_rows = _build_per_varga_avastha_rows(
        conn, chart_id, str(build_id) if build_id else None, ayanamsha_id, computed_at, ENGINE_VERSION
    )
    if per_varga_rows:
        _insert_per_varga_avastha_rows(conn, per_varga_rows)
        logger.info("[ga_condition_writer] per_varga_avastha_rows=%d", len(per_varga_rows))

    # ── Amendment BA-P3A: D1 sayanadi + lajjitadi + yuddha chart_facts rows ────
    d1_avastha_rows = _build_d1_avastha_rows(
        conn, chart_id, str(build_id) if build_id else None,
        ayanamsha_id, computed_at, ENGINE_VERSION
    )
    if d1_avastha_rows:
        _insert_per_varga_avastha_rows(conn, d1_avastha_rows)
        logger.info("[ga_condition_writer] d1_avastha_rows=%d", len(d1_avastha_rows))

    return inserted
