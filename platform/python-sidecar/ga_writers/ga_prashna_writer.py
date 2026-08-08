"""
ga_writers/ga_prashna_writer.py
Prashna (Horary) judgment computation for a prashna chart.

For each ayanamsha:
  1. Check if chart_id is in prashna_charts. If not → 0 rows (natal chart build).
  2. Read prashna_charts to get question_class and prashna_lagna_method.
  3. Read ga_positions for the prashna chart (planetary longitudes).
  4. Read bg_prashna_significators for the question_class to get natural significators.
  5. Determine which is faster (querent/quesited) and compute Ithasala/Eesarpha.
  6. Apply fructification timing rules.
  7. Store in ga_prashna_lagna and ga_prashna_judgment.

L1 idempotency: DELETE WHERE chart_id = %s AND ayanamsha_id = %s, then INSERT.
Never commits — caller owns the transaction.
"""
from __future__ import annotations
import logging
from typing import Optional, Any

from brahmagyan.graha_vocabulary import to_title

logger = logging.getLogger(__name__)

# Abbreviation-to-full-name map: chart_facts.fact_subject uses abbreviated tokens,
# but bg_prashna_significators stores full planet names.  Normalize at source so all
# downstream lookups (PLANET_DAILY_MOTION, PLANET_ORBS, querent_planet checks) work.
# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets). "ASC"/"ASCENDANT" are documented extra
# alternate Ascendant storage names the SSoT itself does not carry.
_ABBREV_TO_FULL: dict[str, str] = {
    code: to_title(code)
    for code in (
        "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN",
        "KET_MEAN", "LAGNA",
    )
}
_ABBREV_TO_FULL.update({
    # Alternate Ascendant storage names
    "ASC": "Lagna",
    "ASCENDANT": "Lagna",
})

# Canonical ayanamshas — MUST match ga_positions_writer.py CANONICAL_AYANAMSHAS exactly
CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

# Planet mean daily motion (degrees/day) — for determining faster/slower planet
PLANET_DAILY_MOTION = {
    "Moon":    13.17,
    "Mercury":  1.38,  # mean (can retrograde)
    "Venus":    1.20,  # mean
    "Sun":      0.985,
    "Mars":     0.524,
    "Jupiter":  0.083,
    "Saturn":   0.034,
    "Rahu":    -0.053,  # retrograde
    "Ketu":    -0.053,  # retrograde
}

# Tajik aspect orbs (degrees) per planet (half-sum rule)
PLANET_ORBS = {
    "Moon":    12.0,
    "Sun":      8.0,
    "Mercury":  7.0,
    "Venus":    7.0,
    "Mars":     8.0,
    "Jupiter":  9.0,
    "Saturn":   9.0,
    "Rahu":     4.0,
    "Ketu":     4.0,
}

TAJIK_ASPECT_DEGREES = [0, 60, 90, 120, 180]  # conjunction, sextile, square, trine, opposition


def _degrees_to_360(deg: float) -> float:
    return deg % 360.0


def _aspect_gap(lon_a: float, lon_b: float) -> tuple[float, float]:
    """Return (gap_to_nearest_aspect, aspect_degree) between two planetary longitudes.

    lon_a = faster planet longitude
    lon_b = slower planet longitude

    gap > 0: faster planet has NOT yet reached the aspect point (applying = Ithasala)
    gap < 0: faster planet has ALREADY passed the aspect point (separating = Eesarpha)
    """
    diff = _degrees_to_360(lon_b - lon_a)
    best_gap = 360.0
    best_aspect = 0.0
    for aspect in TAJIK_ASPECT_DEGREES:
        gap = diff - aspect
        # Normalize gap to -180..180
        while gap > 180:
            gap -= 360
        while gap < -180:
            gap += 360
        if abs(gap) < abs(best_gap):
            best_gap = gap
            best_aspect = float(aspect)
    return best_gap, best_aspect


def compute_prashna_judgment(
    conn,
    chart_id: str,
    ayanamsha_id: str,
) -> Optional[dict[str, Any]]:
    """
    Compute the prashna judgment for a given chart_id and ayanamsha.
    Returns a dict with all fields for ga_prashna_lagna + ga_prashna_judgment.
    Returns None if no prashna chart exists for this chart_id.
    """
    cur = conn.cursor()

    # Step 1: Check prashna_charts
    cur.execute(
        "SELECT question_class, prashna_lagna_method, kp_number, querent_direction, active_nostril "
        "FROM prashna_charts WHERE chart_id = %s",
        (chart_id,)
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        return None  # Not a prashna chart — skip

    question_class, lagna_method, kp_number, querent_direction, active_nostril = row

    # Step 2: Get planetary positions from chart_facts (graha_position rows)
    cur.execute("""
        SELECT fact_subject,
               MAX(CASE WHEN fact_key = 'longitude_sidereal' THEN fact_value_num  END),
               MAX(CASE WHEN fact_key = 'retrograde_flag'    THEN fact_value_text END)
        FROM chart_facts
        WHERE chart_id      = %s
          AND ayanamsha_id  = %s
          AND fact_category = 'graha_position'
        GROUP BY fact_subject
    """, (chart_id, ayanamsha_id))
    positions = {
        _ABBREV_TO_FULL.get(r[0], r[0]): {"longitude": float(r[1]), "retrograde": (r[2] == "retrograde")}
        for r in cur.fetchall()
        if r[1] is not None
    }

    if not positions:
        # Prashna chart exists but chart_facts graha_position rows not yet built — build ordering issue
        logger.warning(
            "[ga_prashna_writer] chart_id=%s ayanamsha=%s: prashna chart exists "
            "but chart_facts has no graha_position rows — ensure ga_positions runs before ga_prashna",
            chart_id, ayanamsha_id,
        )
        cur.close()
        return None

    # Step 3: Get Lagna from positions (Ascendant is stored as 'Lagna' or 'Ascendant')
    lagna_data = positions.get("Lagna") or positions.get("Ascendant")
    lagna_lon = lagna_data["longitude"] if lagna_data else 0.0

    # Compute lagna sign (0-indexed: 0=Aries, 1=Taurus, ..., 11=Pisces)
    RASHI_NAMES = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    lagna_sign_idx = int(lagna_lon // 30) % 12
    lagna_rashi = RASHI_NAMES[lagna_sign_idx]
    lagna_degree_in_sign = lagna_lon % 30.0

    # Step 4: Get significators from bg_prashna_significators
    cur.execute(
        "SELECT querent_planet, quesited_planet FROM bg_prashna_significators "
        "WHERE question_class = %s",
        (question_class,)
    )
    sig_row = cur.fetchone()
    if not sig_row:
        cur.close()
        return None

    querent_planet_str, quesited_planet_str = sig_row
    # querent_planet is typically 'Moon'; quesited_planet may be 'Venus, Jupiter'
    querent_planet = querent_planet_str.strip().split(",")[0].strip() if querent_planet_str else "Moon"
    quesited_planet = quesited_planet_str.strip().split(",")[0].strip() if quesited_planet_str else None

    cur.close()

    if not quesited_planet or querent_planet not in positions or quesited_planet not in positions:
        return None  # Missing positions for significators

    querent_lon = positions[querent_planet]["longitude"]
    quesited_lon = positions[quesited_planet]["longitude"]

    # Step 5: Determine applying/separating (Ithasala vs Eesarpha)
    querent_speed = abs(PLANET_DAILY_MOTION.get(querent_planet, 1.0))
    quesited_speed = abs(PLANET_DAILY_MOTION.get(quesited_planet, 1.0))

    # Faster planet closes the gap in applying aspect
    if querent_speed >= quesited_speed:
        faster_lon = querent_lon
        slower_lon = quesited_lon
    else:
        faster_lon = quesited_lon
        slower_lon = querent_lon

    gap, aspect_deg = _aspect_gap(faster_lon, slower_lon)
    # gap > 0 means faster planet hasn't yet reached the aspect (applying = Ithasala)
    # gap < 0 means faster planet has passed the aspect (separating = Eesarpha)
    # Use mutual orb check
    mutual_orb = (PLANET_ORBS.get(querent_planet, 8.0) + PLANET_ORBS.get(quesited_planet, 8.0)) / 2.0
    in_orb = abs(gap) <= mutual_orb

    is_applying = (gap > 0) and in_orb
    is_separating = (gap < 0) and in_orb

    if is_applying:
        tajik_yoga = "ithasala"
        judgment_text = "YES"
    elif is_separating:
        tajik_yoga = "eesarpha"
        judgment_text = "NO"
    else:
        # Out of orb — no direct Ithasala/Eesarpha
        tajik_yoga = "no_direct_aspect"
        judgment_text = "UNCERTAIN"

    # Step 6: Fructification timing
    # Apply sign-quality matrix based on lagna rashi
    MOVABLE_SIGNS = {"Aries", "Cancer", "Libra", "Capricorn"}
    FIXED_SIGNS = {"Taurus", "Leo", "Scorpio", "Aquarius"}
    # Dual signs: Gemini, Virgo, Sagittarius, Pisces

    if lagna_rashi in MOVABLE_SIGNS:
        fructification_unit = "days"
        fruct_rule_id = "degree_to_days"
    elif lagna_rashi in FIXED_SIGNS:
        fructification_unit = "months"
        fruct_rule_id = "sign_to_months"
    else:
        # Dual signs
        fructification_unit = "days"
        fruct_rule_id = "degree_to_days"

    fructification_value = abs(gap)

    citation = "Tājika Nīlakaṇṭhī, Ch. 4–5 (Ithashāla + Phala adhyāya); Prashna Mārga Ch. 6–7"

    return {
        "lagna_method": lagna_method,
        "lagna_rashi": lagna_rashi,
        "lagna_degree_in_sign": lagna_degree_in_sign,
        "lagna_citation": "Tājika Nīlakaṇṭhī, Ch. 1 (Prashna Lagna Nirūpaṇa)",
        "question_class": question_class,
        "querent_significator": querent_planet,
        "quesited_significator": quesited_planet,
        "querent_longitude": querent_lon,
        "quesited_longitude": quesited_lon,
        "longitudinal_gap": abs(gap),
        "is_applying": is_applying,
        "tajik_yoga": tajik_yoga,
        "judgment_text": judgment_text,
        "fructification_value": fructification_value,
        "fructification_unit": fructification_unit,
        "fruct_rule_id": fruct_rule_id,
        "classical_citation": citation,
    }


def seed_prashna_judgment(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    *,
    dry_run: bool = False,
) -> int:
    """
    Seed ga_prashna_lagna + ga_prashna_judgment for one (chart_id, ayanamsha_id).
    L1 idempotency: DELETE WHERE chart_id = %s AND ayanamsha_id = %s, then INSERT.
    Returns rows inserted (0 if not a prashna chart).
    Never commits — caller owns the transaction.
    """
    if dry_run:
        return 0  # dry_run: no writes, no DB calls

    result = compute_prashna_judgment(conn, chart_id, ayanamsha_id)
    if result is None:
        return 0  # Not a prashna chart or missing positions

    cur = conn.cursor()

    # L1 idempotency: delete then insert
    cur.execute(
        "DELETE FROM ga_prashna_lagna WHERE chart_id = %s AND ayanamsha_id = %s",
        (chart_id, ayanamsha_id)
    )
    cur.execute(
        "DELETE FROM ga_prashna_judgment WHERE chart_id = %s AND ayanamsha_id = %s",
        (chart_id, ayanamsha_id)
    )

    # Insert Prashna-Lagna row
    cur.execute(
        """
        INSERT INTO ga_prashna_lagna
            (chart_id, ayanamsha_id, lagna_method, lagna_rashi, lagna_degree, is_primary, classical_citation)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            chart_id,
            ayanamsha_id,
            result["lagna_method"],
            result["lagna_rashi"],
            result["lagna_degree_in_sign"],
            True,  # primary method
            result["lagna_citation"],
        )
    )

    # Insert judgment row
    cur.execute(
        """
        INSERT INTO ga_prashna_judgment
            (chart_id, ayanamsha_id, question_class,
             querent_significator, quesited_significator,
             querent_longitude, quesited_longitude, longitudinal_gap,
             is_applying, tajik_yoga, judgment_text,
             fructification_value, fructification_unit, fructification_rule_id,
             lagna_rashi, classical_citation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            chart_id,
            ayanamsha_id,
            result["question_class"],
            result["querent_significator"],
            result["quesited_significator"],
            result["querent_longitude"],
            result["quesited_longitude"],
            result["longitudinal_gap"],
            result["is_applying"],
            result["tajik_yoga"],
            result["judgment_text"],
            result["fructification_value"],
            result["fructification_unit"],
            result["fruct_rule_id"],
            result["lagna_rashi"],
            result["classical_citation"],
        )
    )

    cur.close()
    rows = 2  # 1 lagna row + 1 judgment row per ayanamsha
    return rows
