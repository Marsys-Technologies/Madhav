# Phase 3 Raw Data Capture
# L0 Brahmagyan Closure Pass — Phase 3 Enrichment Audit
# Date: 2026-06-17

---

## 1. reference_nakshatra — Schema (46 columns)

Columns: nakshatra_id, name_sa_iast, name_sa_devanagari, name_en, alt_names, start_longitude, end_longitude, span_degrees, rashis_spanned, degree_in_rashi_ranges, vimshottari_lord, presiding_deity, secondary_deities, ruling_planet, gana, nadi, yoni_en, yoni_sa, yoni_sex, varna, tatva, guna, pakshi, nakshatra_gender, muhurta_type, disha, favorable_acts, prohibited_acts, symbol, shakti, basis_above, basis_below, net_result, motivation, body_part, paramayus, naisargika_maturity_age, deity_domain, is_gandanta, is_mula_sangya, is_panchanka, is_abhijit, tradition_scope, classical_source, build_id, created_at

## 2. reference_nakshatra — All 28 rows (key columns)

| nakshatra_id | name_en           | gana     | nadi   | yoni_en  | yoni_sex | tatva   | body_part  | disha |
|-------------|-------------------|----------|--------|----------|----------|---------|------------|-------|
| 1           | Ashwini           | Deva     | Adi    | Horse    | M        | Agni    | head       | South |
| 2           | Bharani           | Manushya | Madhya | Elephant | M        | Jala    | head       | West  |
| 3           | Krittika          | Rakshasa | Antya  | Goat     | F        | Agni    | head       | North |
| 4           | Rohini            | Manushya | Adi    | Serpent  | M        | Jala    | forehead   | East  |
| 5           | Mrigasira         | Deva     | Madhya | Serpent  | F        | Agni    | eyes       | South |
| 6           | Ardra             | Manushya | Antya  | Dog      | F        | Vayu    | hair       | West  |
| 7           | Punarvasu         | Deva     | Adi    | Cat      | M        | Akasha  | nose       | North |
| 8           | Pushya            | Deva     | Madhya | Goat     | M        | Vayu    | face       | East  |
| 9           | Ashlesha          | Rakshasa | Antya  | Cat      | F        | Prithvi | nails      | South |
| 10          | Magha             | Rakshasa | Adi    | Rat      | M        | Agni    | lips       | East  |
| 11          | Purva Phalguni    | Manushya | Madhya | Rat      | F        | Jala    | right hand | West  |
| 12          | Uttara Phalguni   | Manushya | Antya  | Cow      | M        | Agni    | left hand  | East  |
| 13          | Hasta             | Deva     | Adi    | Buffalo  | F        | Jala    | fingers    | South |
| 14          | Chitra            | Rakshasa | Madhya | Tiger    | M        | Agni    | neck       | South |
| 15          | Swati             | Deva     | Antya  | Buffalo  | M        | Vayu    | chest      | North |
| 16          | Vishakha          | Rakshasa | Adi    | Tiger    | F        | Akasha  | arms       | East  |
| 17          | Anuradha          | Deva     | Madhya | Hare     | M        | Vayu    | stomach    | South |
| 18          | Jyeshtha          | Rakshasa | Antya  | Hare     | F        | Prithvi | tongue     | West  |
| 19          | Moola             | Rakshasa | Adi    | Dog      | M        | Agni    | feet       | South |
| 20          | Purva Ashadha     | Manushya | Madhya | Monkey   | F        | Jala    | back       | North |
| 21          | Uttara Ashadha    | Manushya | Antya  | Mongoose | M        | Agni    | thighs     | South |
| 22          | Shravana          | Deva     | Adi    | Monkey   | M        | Jala    | ears       | North |
| 23          | Dhanishtha        | Rakshasa | Madhya | Lion     | M        | Agni    | back       | East  |
| 24          | Shatabhisha       | Rakshasa | Antya  | Horse    | F        | Vayu    | chin       | South |
| 25          | Purva Bhadrapada  | Manushya | Adi    | Lion     | F        | Akasha  | sides      | West  |
| 26          | Uttara Bhadrapada | Manushya | Antya  | Cow      | F        | Vayu    | legs       | South |
| 27          | Revati            | Deva     | Madhya | Elephant | F        | Prithvi | feet       | North |
| 28          | Abhijit           | Deva     | NULL   | NULL     | NULL     | Agni    | NULL       | NULL  |

**Gap identified**: Nakshatra 28 (Abhijit) is missing nadi, yoni_en, yoni_sex, body_part, disha.

## 3. reference_nakshatra_pada — Schema (18 columns)

Columns: pada_id, nakshatra_id, pada_number, absolute_pada, start_longitude, end_longitude, pada_navamsa_sign, pada_lord, pada_akshara, bija_sound, mantra_prefix, pada_deity_nuance, element_shading, dosha_shading, tradition_scope, classical_source, build_id, created_at
Row count: 108

## 4. reference_nakshatra_matrix — Schema (12 columns)

Columns: id, matrix_type, from_key, to_key, relation_value, guna_points, max_points, notes, tradition_scope, classical_source, build_id, created_at
Row count: 2721

## 5. bg_dignity_reference — 9 rows (all 9 grahas)

| graha   | exaltation_sign | exaltation_degree | debilitation_sign | debilitation_degree | moolatrikona_sign | moolatrikona_from | moolatrikona_to | own_signs            |
|---------|-----------------|-------------------|-------------------|---------------------|-------------------|-------------------|-----------------|----------------------|
| Sun     | Aries           | 10                | Libra             | 10                  | Leo               | 0                 | 20              | {Leo}                |
| Moon    | Taurus          | 3                 | Scorpio           | 3                   | Taurus            | 4                 | 30              | {Cancer}             |
| Mars    | Capricorn       | 28                | Cancer            | 28                  | Aries             | 0                 | 12              | {Aries,Scorpio}      |
| Mercury | Virgo           | 15                | Pisces            | 15                  | Virgo             | 16                | 20              | {Gemini,Virgo}       |
| Jupiter | Cancer          | 5                 | Capricorn         | 5                   | Sagittarius       | 0                 | 10              | {Sagittarius,Pisces} |
| Venus   | Pisces          | 27                | Virgo             | 27                  | Libra             | 0                 | 15              | {Taurus,Libra}       |
| Saturn  | Libra           | 20                | Aries             | 20                  | Aquarius          | 0                 | 20              | {Capricorn,Aquarius} |
| Rahu    | Gemini          | NULL              | Sagittarius       | NULL                | NULL              | NULL              | NULL            | {}                   |
| Ketu    | Sagittarius     | NULL              | Gemini            | NULL                | NULL              | NULL              | NULL            | {}                   |

## 6. bg_graha_naisargika_friendship — 72 rows (9 grahas × 8 others)

All 72 rows present covering Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. Rahu/Ketu follow Uttara Kalamrita (UK Ch.4).

## 7. bg_avastha_schemes — 35 rows, 5 schemes

Schemes: baladi (5 states), jagradadi (3 states), deeptaadi (9 states), lajjitaadi (6 states), sayanadi (12 states)

## 8. bg_combustion_orbs — 8 rows (Sun excluded, all planets)

| graha   | orb_degrees | deep_orb_degrees |
|---------|-------------|------------------|
| Moon    | 12          | 10               |
| Mars    | 17          | 15               |
| Mercury | 14          | 12               |
| Jupiter | 11          | 9                |
| Venus   | 10          | 8                |
| Saturn  | 15          | 12               |
| Rahu    | 9           | 7                |
| Ketu    | 9           | 7                |

## 9. bg_motion_state_thresholds — 27 rows

Covers: Sun (2), Moon (2), Mars (4), Mercury (4), Jupiter (4), Venus (4), Saturn (4), Rahu (1), Ketu (1). Comprehensive.

## 10. bg_vastu_directions — 8 rows

All 8 directions present: N(Mercury), S(Mars), E(Sun), W(Saturn), NE(Jupiter), SE(Venus), NW(Moon), SW(Rahu)

## 11. bg_vastu_direction_remedials — 24 rows (3 per direction × 8 directions)

All directions have 3 remedials each (color, symbol, space/material).

## 12. bg_medical_mappings — 9 rows (all 9 grahas, no rashi-level)

Schema: id, graha, dosha (array), dhatu (array), organ_systems (array), body_part (array), disease_tendency (array), classical_citation
Note: Only graha-level mappings. No rashi or nakshatra-level medical mappings in this table.

## 13. bg_transit_rules — 41 rows before phase3 builds

Graha coverage before build:
- sun: 7 rules (3 fav + 4 unfav = actually 4+3)
- moon: 7 rules
- mars: 6 rules
- mercury: 5 rules
- jupiter: 7 rules
- saturn: 6 rules
- venus: 3 rules (ONLY 3 houses covered — houses 1,2,3)

**Gap: Venus transit rules missing for houses 4,5,6,7,8,9,10,11,12**

## 14. bg_prashna_lagna_methods — 5 rows

Methods: tajik_moment_lagna, kp_249, aarudha_based, chandra_lagna, swara_based. Complete classical set.

## 15. bg_prashna_tajik_yogas — 11 rows before phase3 builds

Present: ithasala, eesarpha, nakta, yamaya, manaau, kambula, gairi_kambula, dutthottha, rudda, khallasara, duhphali_kuttha

**Gap: Missing 5 of classical 16: ikbal, kuttha, dutthadhuta, tambira, durupha**

## 16. bg_prashna_significators — 12 rows

Question classes: marriage, career, litigation_legal, lost_object, health_illness, finance_wealth, travel_journey, property_land, children_progeny, death_longevity, spiritual_religious, enemy_conflict

## 17. bg_prashna_fructification_rules — 5 rows

Timing rules: degree_to_hours, degree_to_days, sign_to_months, sign_to_years, sign_quality_timing_matrix

## 18. bg_prashna_special_techniques — 3 rows

Techniques: nashta_jataka, tithi_nakshatra_yoga, omen_nimitta

## 19. bg_transit_engine — 9 rows (all 9 grahas)

All grahas covered with avg_daily_motion_deg, zodiac_period_days, sign_residence_days.

## 20. bg_nakshatra_medical — 27 rows

Covers nakshatras 1-27 with body_part per Ashtanga Hridayam / BPHS. Abhijit (28) absent.

## 21. brahma_remedy_corpus — 266 rows

Planet coverage: jupiter(31), ketu(19), mars(25), mercury(20), moon(41), rahu(34), saturn(29), sun(42), venus(25)

## 22. brahma_dosha_catalog — 50 rows

Schema: canonical_id, name_sa, name_en, category, formation_rule_jsonb, formation_text, effects_text, severity_grades, cancellation_conditions, classical_citations, source_chunk_ids, associated_remedies, school, created_at

## 23. brahma_yoga_catalog — 175 rows

Category breakdown: other(120), raja(31), dhana(12), pancha_mahapurusha(5), aristha(4), sannyasa(3)

## 24. brahma_ontology — 623 rows
## 25. brahma_dasha_systems — 18 rows
## 26. brahma_compendium_index — 9538 rows

## 27. bg_transit_vedha — does not exist (pre-phase3)

`SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bg_transit_vedha'` returned 0.

## 28. asset_registry bg_ assets — 22 assets

asset_id list: bg_ephemeris, bg_reference, bg_texts, bg_ontology, bg_text_index, bg_prashna_rules, bg_rules, bg_remedies, bg_concordance, bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index, bg_panchanga, bg_ephemeris_engine, bg_nakshatra, bg_vastu_directions, bg_transit_engine, bg_transit_rules, bg_medical_mappings, bg_nakshatra_medical, bg_dignity_reference
