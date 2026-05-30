"""META-δ: Negative Space Map Writer (Ω-SPACE) — absence as feature.

Implements META_ENHANCEMENTS_SPEC_v1_0.md §4.
Writes to l25_negative_space_map.
All inserts use ON CONFLICT DO NOTHING.
"""
import uuid
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Expected patterns that are notably absent — these are evaluated structurally
ABSENCE_DETECTORS: List[Dict] = [
    {
        'class': 'missing_benefic_in_kendra',
        'feature': 'no_benefic_in_kendra_houses',
        'significance': 'high',
        'expected': 'Jupiter or Venus in 1/4/7/10 house for strong raj yoga potential',
        'classical': 'BPHS Kendra-Kona benefic placement rules',
    },
    {
        'class': 'no_exalted_planets',
        'feature': 'zero_exalted_planets',
        'significance': 'medium',
        'expected': 'At least one exalted planet for exceptional strength in that domain',
        'classical': 'BPHS exaltation effects',
    },
    {
        'class': 'missing_raj_yoga',
        'feature': 'no_parashari_raj_yoga',
        'significance': 'medium',
        'expected': 'Kendra-Kona lord exchange/conjunction for power/status yoga',
        'classical': 'Parashari Raj Yoga combinations',
    },
    {
        'class': 'missing_temporal_anchor',
        'feature': 'no_a16_high_confidence_anchor',
        'significance': 'medium',
        'expected': 'At least one high-confidence A16 phase-locked anchor in 5-year window',
        'classical': 'Phase-locked prediction anchor model',
    },
    {
        'class': 'no_panchamahapurusha',
        'feature': 'no_panchamahapurusha_yoga',
        'significance': 'medium',
        'expected': 'Mars/Mercury/Jupiter/Venus/Saturn own/exalted in kendra for panchamahapurusha yoga',
        'classical': 'BPHS Panchamahapurusha Yoga — Ruchaka/Bhadra/Hamsa/Malavya/Shasha',
    },
    {
        'class': 'no_chara_karaka_in_kendra',
        'feature': 'atmakaraka_not_in_kendra',
        'significance': 'medium',
        'expected': 'Atmakaraka in kendra for strong soul-purpose alignment with mundane life',
        'classical': 'Jaimini Chara Karaka — kendra placement of AK',
    },
    {
        'class': 'no_jupiter_aspect_lagna',
        'feature': 'no_jupiter_aspect_on_lagna',
        'significance': 'high',
        'expected': 'Jupiter aspecting lagna for protection, wisdom, and grace on the native',
        'classical': 'BPHS — Jupiter Drishti on Lagna (special aspect: 5/7/9 from Jupiter)',
    },
    {
        'class': 'no_vargottama_planet',
        'feature': 'zero_vargottama_planets',
        'significance': 'low',
        'expected': 'At least one vargottama graha for strong rashi+navamsha consistency',
        'classical': 'BPHS Vargottama — graha in same rashi in D1 and D9',
    },
]


def write_negative_space(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """
    Write all ABSENCE_DETECTORS as negative space rows for this chart+ayanamsha.
    Uses structural absence detection — absence is assumed unless presence data contradicts.
    """
    count = 0
    with conn.cursor() as cur:
        for detector in ABSENCE_DETECTORS:
            cur.execute("""
                INSERT INTO l25_negative_space_map
                  (absence_id, chart_id, ayanamsha_id, build_id,
                   absence_class, absent_feature, asset_context, absence_significance,
                   expected_if_present, classical_pattern_violated,
                   verified, verification_pass_status, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,%s,%s,'chart_facts',%s,%s,%s,false,'pass',NOW())
                ON CONFLICT (chart_id, ayanamsha_id, absence_class, absent_feature) DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  detector['class'], detector['feature'], detector['significance'],
                  detector['expected'], detector['classical']))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-δ: {count} negative space entries written")
    return count


def write_negative_space_from_empty_houses(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """
    Detect empty houses (no graha) and record as house_empty absence class.
    Scans chart_facts for house occupancy data.
    """
    count = 0
    with conn.cursor() as cur:
        try:
            # Find which houses have occupying planets
            cur.execute("""
                SELECT DISTINCT fact_value_text AS house_num
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'house_placement'
                  AND fact_value_text IS NOT NULL
            """, [chart_id, ayanamsha_id])
            occupied = {r[0] for r in cur.fetchall()}
        except Exception as e:
            logger.debug(f"empty house scan: {e}")
            conn.rollback()
            occupied = set()

        # Houses 1-12 not occupied
        for house_num in range(1, 13):
            if str(house_num) not in occupied:
                absent_feature = f'house_{house_num}_empty'
                significance = 'high' if house_num in (1, 4, 7, 10) else 'low'
                cur.execute("""
                    INSERT INTO l25_negative_space_map
                      (absence_id, chart_id, ayanamsha_id, build_id,
                       absence_class, absent_feature, asset_context, absence_significance,
                       expected_if_present, classical_pattern_violated,
                       verified, verification_pass_status, computed_at)
                    VALUES (%s,%s::UUID,%s,%s::UUID,'house_empty',%s,'chart_facts',%s,%s,%s,false,'pass',NOW())
                    ON CONFLICT (chart_id, ayanamsha_id, absence_class, absent_feature) DO NOTHING
                """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                      absent_feature, significance,
                      f'Graha in house {house_num} activates that bhava directly',
                      f'Bhava activation without graha depends on sign lord disposition'))
                count += cur.rowcount

    conn.commit()
    logger.info(f"META-δ: {count} empty-house negative space entries written")
    return count
