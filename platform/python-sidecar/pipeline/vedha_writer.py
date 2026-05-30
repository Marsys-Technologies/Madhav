"""
vedha_writer.py — Extended Vedha obstruction reference data.

Covers 6 vedha systems:
  1. sarvatobhadra   — 28 SBC nakshatra vedha pairs (mirrors l1_sarvatobhadra_vedha)
  2. sapta_shalaka   — Tara-based 7-spoke obstruction relationships
  3. tajik_year_lord — Annual chart year-lord vedha to natal planets
  4. dasha_sub_lord  — Sub-period lord vedha obstructions per dasha system
  5. transit_chakra  — Transit graha vedha to natal nakshatra via Kota Chakra rings
  6. argala          — Planetary argala (intervention) and pratargala (counter-intervention)

Each tuple has 8 elements:
  (vedha_system, source_nakshatra, obstructing_element,
   obstruction_type, severity, cancellation_rule,
   classical_citation, notes)

Stream C — A18 [BUILD-ORCH-STREAM-C-A18-S1]
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# System 1: sarvatobhadra — SBC vedha pairs (28 bidirectional rows)
# Each of the 14 classical SBC vedha pairs generates 2 rows.
# ---------------------------------------------------------------------------

SBC_VEDHA_ROWS: list[tuple] = [
    ('sarvatobhadra', 'rohini',            'shravana',           'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'shravana',          'rohini',             'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'ardra',             'shatabhisha',        'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'shatabhisha',       'ardra',              'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'punarvasu',         'purva_bhadrapada',   'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'purva_bhadrapada',  'punarvasu',          'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'pushya',            'uttara_bhadrapada',  'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'uttara_bhadrapada', 'pushya',             'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'aslesha',           'revati',             'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'revati',            'aslesha',            'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'magha',             'ashwini',            'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'ashwini',           'magha',              'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'uttara_phalguni',   'bharani',            'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'bharani',           'uttara_phalguni',    'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'hasta',             'krittika',           'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'krittika',          'hasta',              'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'chitra',            'mrigashira',         'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'mrigashira',        'chitra',             'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'swati',             'purva_phalguni',     'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'purva_phalguni',    'swati',              'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'vishakha',          'uttara_ashadha',     'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'uttara_ashadha',    'vishakha',           'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'anuradha',          'purva_ashadha',      'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'purva_ashadha',     'anuradha',           'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'jyeshtha',          'abhijit',            'vedha', 'moderate',  None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'abhijit',           'jyeshtha',           'vedha', 'moderate',  None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'mula',              'dhanishtha',         'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
    ('sarvatobhadra', 'dhanishtha',        'mula',               'vedha', 'strong',    None, 'Sarvatobhadra Chakra', ''),
]

# ---------------------------------------------------------------------------
# System 2: sapta_shalaka — Tara-based 7-spoke vedha (18 rows)
# Shalaka 3 (Vipat=danger) and 7 (Naidhana=death) obstruct Shalaka 1 (Janma)
# and 2 (Sampat). Mutual same-group interactions produce cancellation rows.
# ---------------------------------------------------------------------------

SAPTA_SHALAKA_VEDHA: list[tuple] = [
    # Shalaka 3 (Vipat=danger) obstructs Shalaka 1 (Janma) nakshatras
    ('sapta_shalaka', 'ashwini',    'krittika',     'vedha', 'moderate',     None,
     'Tara Bala, Muhurta Chintamani', ''),
    ('sapta_shalaka', 'ashwini',    'anuradha',     'vedha', 'moderate',     None,
     'Tara Bala', ''),
    ('sapta_shalaka', 'ashwini',    'shatabhisha',  'vedha', 'moderate',     None,
     'Tara Bala', ''),
    ('sapta_shalaka', 'hasta',      'krittika',     'vedha', 'moderate',     None,
     'Tara Bala', ''),
    ('sapta_shalaka', 'hasta',      'anuradha',     'vedha', 'moderate',     None,
     'Tara Bala', ''),
    ('sapta_shalaka', 'shravana',   'krittika',     'vedha', 'moderate',     None,
     'Tara Bala', ''),
    ('sapta_shalaka', 'shravana',   'anuradha',     'vedha', 'moderate',     None,
     'Tara Bala', ''),
    # Shalaka 7 (Naidhana=death) obstructs all Janma+Sampat nakshatras
    ('sapta_shalaka', 'ashwini',    'chitra',       'vedha', 'strong',       None,
     'Tara Bala', 'Naidhana vedha'),
    ('sapta_shalaka', 'pushya',     'chitra',       'vedha', 'strong',       None,
     'Tara Bala', 'Naidhana vedha'),
    ('sapta_shalaka', 'shravana',   'chitra',       'vedha', 'strong',       None,
     'Tara Bala', 'Naidhana vedha'),
    ('sapta_shalaka', 'bharani',    'chitra',       'vedha', 'strong',       None,
     'Tara Bala', 'Naidhana vedha'),
    ('sapta_shalaka', 'dhanishtha', 'chitra',       'vedha', 'strong',       None,
     'Tara Bala', 'Naidhana vedha'),
    # Cancellations: when Shalaka 1 and 6 (Sadhana) interact, vedha is cancelled
    ('sapta_shalaka', 'ashwini',    'hasta',        'vedha', 'cancellation',
     'Shalaka 1 + Shalaka 6 (Sadhana) = vedha cancelled', 'Muhurta Chintamani', ''),
    ('sapta_shalaka', 'hasta',      'shravana',     'vedha', 'cancellation',
     'Same shalaka-group mutual support', 'Muhurta Chintamani', ''),
    ('sapta_shalaka', 'pushya',     'shravana',     'vedha', 'cancellation',
     'Janma nakshatra group mutual support', 'Muhurta Chintamani', ''),
    ('sapta_shalaka', 'bharani',    'dhanishtha',   'vedha', 'cancellation',
     'Sampat group mutual support', 'Muhurta Chintamani', ''),
    ('sapta_shalaka', 'mrigashira', 'punarvasu',    'vedha', 'cancellation',
     'Janma group overlap support', 'Muhurta Chintamani', ''),
    ('sapta_shalaka', 'vishakha',   'shatabhisha',  'vedha', 'cancellation',
     'Sampat cross-group support', 'Muhurta Chintamani', ''),
]

# ---------------------------------------------------------------------------
# Systems 3–6: Tajik year-lord, dasha sub-lord, transit chakra, argala
# (20 rows combined)
# ---------------------------------------------------------------------------

MULTI_SYSTEM_VEDHA: list[tuple] = [
    # --- System 3: tajik_year_lord ---
    # Year-lord in 6H/8H/12H from natal planet = vedha
    ('tajik_year_lord', 'natal_sun',     'year_lord_in_6H_from_sun',        'vedha', 'strong',   None,
     'Tajik Neelakanthi Ch 4', 'Year-lord in 6th from Sun natal position = obstruction to solar themes'),
    ('tajik_year_lord', 'natal_moon',    'year_lord_in_8H_from_moon',       'vedha', 'strong',   None,
     'TNK Ch 4', 'Year-lord in 8th from Moon = emotional/maternal obstruction'),
    ('tajik_year_lord', 'natal_mercury', 'year_lord_in_12H_from_mercury',   'vedha', 'moderate', None,
     'TNK Ch 4', '12H year-lord = hidden obstruction to intellect/commerce'),
    ('tajik_year_lord', 'natal_venus',   'year_lord_in_6H_from_venus',      'vedha', 'moderate', None,
     'TNK Ch 4', '6H year-lord from Venus = obstruction to relationships/pleasure'),
    ('tajik_year_lord', 'natal_mars',    'year_lord_in_8H_from_mars',       'vedha', 'strong',   None,
     'TNK Ch 4', '8H year-lord from Mars = accidents/surgery risk'),
    ('tajik_year_lord', 'natal_saturn',  'year_lord_in_12H_from_saturn',    'vedha', 'weak',     None,
     'TNK Ch 4', '12H from Saturn = isolation/loss of structure'),
    # --- System 4: dasha_sub_lord ---
    # Antardasha lord in enemy sign of main dasha lord = vedha
    ('dasha_sub_lord', 'vimshottari_MD', 'AD_lord_enemy_to_MD',             'vedha', 'strong',   None,
     'BPHS Ch 46 antardasha', 'Sub-period lord = natural enemy of main period lord'),
    ('dasha_sub_lord', 'vimshottari_MD', 'AD_lord_debilitated',             'vedha', 'moderate', None,
     'BPHS Ch 46', 'Sub-period lord debilitated in rasi'),
    ('dasha_sub_lord', 'jaimini_chara',  'sub_sign_8th_from_main',          'vedha', 'moderate', None,
     'Jaimini Sutra 1.4.3', '8th sub-sign from main Chara dasha sign'),
    ('dasha_sub_lord', 'jaimini_chara',  'sub_sign_6th_from_main',          'vedha', 'weak',     None,
     'Jaimini Sutra', '6th sub-sign from main Chara dasha sign'),
    # --- System 5: transit_chakra ---
    # Kota bahya-ring transits obstruct swami-ring natal positions
    ('transit_chakra', 'rohini',  'bahya_ring_transit', 'vedha', 'moderate', None,
     'Brihat Samhita Kota Chakra', 'Transit in outer Kota ring weakens inner-ring natal nakshatra'),
    ('transit_chakra', 'pushya',  'bahya_ring_transit', 'vedha', 'moderate', None,
     'Brihat Samhita Kota', ''),
    ('transit_chakra', 'hasta',   'bahya_ring_transit', 'vedha', 'moderate', None,
     'Brihat Samhita Kota', ''),
    ('transit_chakra', 'swati',   'bahya_ring_transit', 'vedha', 'moderate', None,
     'Brihat Samhita Kota', ''),
    ('transit_chakra', 'abhijit', 'bahya_ring_transit', 'vedha', 'weak',     None,
     'Brihat Samhita Kota', 'Abhijit in swami — partial transit protection'),
    # --- System 6: argala ---
    # Planets in 2H/4H/11H create argala; 3H/10H create pratargala
    ('argala', 'lagna', 'planet_in_2H',  'argala',     'strong',   None,
     'Jaimini Sutra 2.1.1', 'Planet in 2nd from reference = dhana argala'),
    ('argala', 'lagna', 'planet_in_4H',  'argala',     'moderate', None,
     'Jaimini Sutra 2.1.2', 'Planet in 4th from reference = sukha argala'),
    ('argala', 'lagna', 'planet_in_11H', 'argala',     'strong',   None,
     'Jaimini Sutra 2.1.3', 'Planet in 11th from reference = labha argala'),
    ('argala', 'lagna', 'planet_in_3H',  'pratargala', 'weak',
     'Planet in 3H cancels 11H argala', 'Jaimini Sutra 2.1.4', 'Pratargala to labha argala'),
    ('argala', 'lagna', 'planet_in_10H', 'pratargala', 'weak',
     'Planet in 10H cancels 4H sukha argala', 'Jaimini Sutra 2.1.5', 'Pratargala to sukha argala'),
]

# ---------------------------------------------------------------------------
# Combined export
# ---------------------------------------------------------------------------

VEDHA_ALL_ROWS: list[tuple] = SBC_VEDHA_ROWS + SAPTA_SHALAKA_VEDHA + MULTI_SYSTEM_VEDHA

_ALLOWED_SYSTEMS = frozenset({
    'sarvatobhadra', 'sapta_shalaka', 'tajik_year_lord',
    'dasha_sub_lord', 'transit_chakra', 'argala',
})
_ALLOWED_SEVERITIES = frozenset({'strong', 'moderate', 'weak', 'cancellation'})


# ---------------------------------------------------------------------------
# DB seed
# ---------------------------------------------------------------------------

_INSERT_SQL = """
INSERT INTO l1_vedha_extended
    (vedha_system, source_nakshatra, obstructing_element,
     obstruction_type, severity, cancellation_rule,
     classical_citation, notes)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (vedha_system, source_nakshatra, obstructing_element, obstruction_type)
DO NOTHING
"""


def seed_vedha_extended(conn) -> int:
    """Idempotently insert all vedha rows; returns the number of rows inserted."""
    inserted = 0
    with conn.cursor() as cur:
        for row in VEDHA_ALL_ROWS:
            cur.execute(_INSERT_SQL, row)
            inserted += cur.rowcount
    conn.commit()
    return inserted
