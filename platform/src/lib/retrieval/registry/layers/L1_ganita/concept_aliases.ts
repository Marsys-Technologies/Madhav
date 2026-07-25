/**
 * concept_aliases.ts — seed alias table for the discovery substrate (C3 ConceptAlias shape)
 * ================================================================================
 * Elevation Campaign v2.1, STREAM α Lane-H, Task 1. Backs `get_database_schema`'s
 * `concept_aliases: ConceptAlias[]` field and `concept_locate`'s resolution logic.
 *
 * SCOPE (per Task-1 brief + RUNWAY correction): this is a SEED — common alternate names an
 * LLM caller is likely to type ("Gulika"/"Maandi", "sphuta", "panchanga", "mangal", ...),
 * mapped to the real `fact_category` value(s) they resolve to in the live `chart_facts`
 * schema (per `chart_facts_categories_authoritative_v1.json`, 218 categories, the live-DB
 * census C3 §1 rule-1 requires `get_database_schema`'s `entries` to be enumerated against).
 * It intentionally does NOT attempt exhaustive coverage of all 218 categories — a later
 * stream extends this into the Total Concept Inventory (γ) per the brief. The CI regression
 * check in `platform/scripts/census/schema_map_alias_coverage_check.ts` asserts every LIVE
 * fact_category has at least one alias entry, so a category added without any alias fails
 * loudly instead of silently degrading `concept_locate` coverage.
 *
 * `concept_id` uses the primary/most-specific `fact_category` string as the canonical id —
 * the Phase-0.7 concept census C3 references as the "real" canonical-id source does not exist
 * yet (see C3 §2, non-goals: "this contract fixes the output shape once decided, not how
 * fact_subjects are canonicalized"), so the fact_category itself is the most defensible,
 * already-live canonical id available today. When the Phase-0.7 census lands, `concept_id`
 * here is the join key to re-point at its real ids without changing this file's shape.
 */

export type ConceptAlias = {
  concept_id: string
  aliases: string[]
  fact_categories: string[]
}

/**
 * Seed set. Each entry's `aliases` are surface strings a caller is plausibly going to type
 * (English, Sanskrit, common misspellings/shorthand actually observed elsewhere in this
 * codebase's own naming — see per-entry citation). `fact_categories` are real, live
 * `chart_facts.fact_category` values (cross-checked against
 * `platform/src/generated/census/chart_facts_categories_authoritative_v1.json`, 218-category
 * live census, 2026-07-22).
 */
export const CONCEPT_ALIASES: ConceptAlias[] = [
  {
    // get_positions.ts's own docstring: "upagrahas (Gulika, Mandi, etc.)"; get_sensitive_points.ts
    // fact_subject 'Gulika' observed live (grep hit in this repo's own registry layer).
    concept_id: 'sensitive_point_gulika_mandi',
    aliases: ['gulika', 'maandi', 'mandi', 'upagraha', 'shadow point', 'shadow planet'],
    fact_categories: ['sensitive_point_gulika_mandi', 'panchanga_gulika_kalam', 'upagraha_position'],
  },
  {
    concept_id: 'esoteric_point_pranapada_sphuta',
    aliases: ['sphuta', 'spashta', 'esoteric point', 'esoteric sphuta'],
    fact_categories: [
      'esoteric_point_pranapada_sphuta', 'esoteric_point_sphuta_fertility',
      'esoteric_point_trikona_dasha_sphuta',
    ],
  },
  {
    concept_id: 'panchanga_calendrical',
    aliases: ['panchanga', 'panchang', 'five limbs', 'tithi vara nakshatra yoga karana'],
    fact_categories: [
      'panchanga_calendrical', 'panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra_moon',
      'panchanga_yoga', 'panchanga_karana', 'panchanga_solar_context', 'panchanga_sun_moon_dynamics',
    ],
  },
  {
    // Mars aliases — address_resolver.ts's own GRAHA_ALIASES already carries mangala/kuja/mars.
    concept_id: 'graha_position',
    aliases: ['mangal', 'mangala', 'kuja', 'mars', 'graha position', 'planet position', 'longitude'],
    fact_categories: ['graha_position'],
  },
  {
    concept_id: 'graha_shadbala_total',
    aliases: ['shadbala', 'shad bala', 'six-fold strength', 'planetary strength'],
    fact_categories: [
      'graha_shadbala_total', 'graha_shadbala_cheshta', 'graha_shadbala_dig', 'graha_shadbala_drik',
      'graha_shadbala_kala', 'graha_shadbala_naisargika', 'graha_shadbala_sthana',
    ],
  },
  {
    concept_id: 'graha_dignity_per_varga',
    aliases: ['dignity', 'exaltation', 'debilitation', 'own sign', 'moolatrikona', 'swakshetra'],
    fact_categories: [
      'graha_dignity_per_varga', 'graha_effective_dignity_modified_by_aspects',
      'graha_sign_attributes', 'vargottama_per_varga',
    ],
  },
  {
    concept_id: 'graha_avastha_baladi',
    aliases: ['avastha', 'planetary state', 'baladi', 'jagrad', 'lajjitadi', 'sayanadi'],
    fact_categories: [
      'graha_avastha_baladi', 'graha_avastha_deepta', 'graha_avastha_jagrad',
      'graha_avastha_lajjitadi', 'graha_avastha_sayanadi',
    ],
  },
  {
    concept_id: 'yoga_label',
    aliases: ['yoga', 'yogas', 'raja yoga', 'dhana yoga', 'combination'],
    fact_categories: ['yoga_label'],
  },
  {
    concept_id: 'dosha_label',
    // 'kala sarpa' added SATYA-ŚEṢA W1 (2026-07-25): the pre-existing 'kaal sarpa' spelling
    // did not substring-match the more common 'kala sarpa' spelling (live-probe confirmed
    // MISS on concept_locate("kala sarpa") pre-fix) even though kala_sarpa_per_varga was
    // already a correct fact_category on this same entry.
    aliases: ['dosha', 'doshas', 'affliction', 'kaal sarpa', 'kala sarpa', 'mangal dosha'],
    fact_categories: ['dosha_label', 'kala_sarpa_per_varga'],
  },
  {
    concept_id: 'ashtakavarga_bindu',
    aliases: ['ashtakavarga', 'ashtak varga', 'bindu', 'sarvashtakavarga'],
    fact_categories: [
      'ashtakavarga_bindu', 'ashtakavarga_bindu_per_varga', 'ashtakavarga_bindu_sign',
      'ashtakavarga_pinda_sarva', 'ashtakavarga_kakshya_boundary',
    ],
  },
  {
    concept_id: 'argala_natal_matrix',
    aliases: ['argala', 'intervention', 'virodha argala'],
    fact_categories: ['argala_natal_matrix', 'net_argala_per_varga', 'virodha_argala_natal_matrix'],
  },
  {
    concept_id: 'vimsopaka_bala_per_graha',
    aliases: ['vimsopaka', 'vimshopak bala', 'varga strength'],
    fact_categories: [
      'vimsopaka_bala_per_graha', 'graha_vimsopaka_dasavarga', 'graha_vimsopaka_saptavarga',
      'graha_vimsopaka_shadvarga', 'graha_vimsopaka_shodasavarga',
    ],
  },
  {
    concept_id: 'cusp_kp_lords',
    aliases: ['kp', 'krishnamurti', 'kp cusps', 'sub lord', 'sublord'],
    fact_categories: ['cusp_kp_lords', 'kp_cuspal_significators', 'kp_ruling_planets_natal', 'graha_kp_lords'],
  },
  {
    concept_id: 'aspect_tajik',
    aliases: ['tajik', 'varshaphal', 'itthasala', 'ishrafa'],
    fact_categories: ['aspect_tajik', 'tajik_hadda_lord', 'tajik_triraashipathi', 'tajik_vargottama_specific'],
  },
  {
    concept_id: 'upapada_lagna',
    aliases: ['upapada', 'ul', 'arudha lagna', 'arudha pada'],
    fact_categories: ['upapada_lagna', 'arudha_pada', 'karakamsa_position'],
  },
  {
    concept_id: 'graha_position:combustion',
    aliases: ['combust', 'combustion', 'asta'],
    fact_categories: ['combustion_per_varga', 'combustion_relationship'],
  },
  {
    concept_id: 'graha_yuddha',
    aliases: ['graha yuddha', 'planetary war', 'planet war'],
    fact_categories: ['graha_yuddha', 'graha_yuddha_per_varga'],
  },
  {
    concept_id: 'graha_dispositor_chain',
    aliases: ['dispositor', 'sign lord', 'rashi swami', 'dispositor chain'],
    fact_categories: ['graha_dispositor_chain', 'dispositor_chain_per_varga', 'composite_dispositor_strength'],
  },
  {
    concept_id: 'parivartana_per_varga',
    aliases: ['parivartana', 'mutual exchange', 'exchange yoga'],
    fact_categories: ['parivartana_per_varga'],
  },
  {
    concept_id: 'bhava_bala_total_extended',
    aliases: ['bhava bala', 'house strength', 'house bala'],
    fact_categories: [
      'bhava_bala_total_extended', 'house_bhava_bala_total', 'house_bhava_bala_subscore',
      'house_strength_classification_rollup',
    ],
  },
  {
    concept_id: 'sade_sati_cycle',
    aliases: ['sade sati', 'saturn transit', 'shani sade sati'],
    fact_categories: ['sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter'],
  },
  {
    concept_id: 'ayurdaya',
    aliases: ['ayurdaya', 'longevity', 'lifespan'],
    fact_categories: ['ayurdaya'],
  },
  {
    concept_id: 'saham_position',
    aliases: ['saham', 'sahams', 'arabic parts'],
    fact_categories: ['saham_position'],
  },
  {
    concept_id: 'nakshatra_dispositor',
    aliases: ['nakshatra lord', 'star lord', 'birth star'],
    fact_categories: ['nakshatra_dispositor', 'nakshatra_dispositor_chain', 'nakshatra_lord_relationship'],
  },
  {
    concept_id: 'karaka_chara_position',
    aliases: ['karaka', 'chara karaka', 'atmakaraka', 'significator'],
    fact_categories: ['karaka_chara_position', 'karakatva_strength_per_significance'],
  },
  // ── SATYA-ŚEṢA W1 additions (2026-07-25) — UAT-DARPANA Phase-0.7's 46-concept census
  // (RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix A/A.7) probed against this table's PRE-fix state;
  // these five entries close the concepts that MISSED on both resolver passes. Every
  // fact_category below is grep/live-confirmed real (not invented): get_tara_chandra_bala.ts
  // (tara/chandra bala), get_sensitive_degrees.ts (sensitive_degree_check), get_aspects.ts
  // (aspect_jaimini), and facts_store.ts/register_d8_assess_domain.ts (special_lagna).
  {
    concept_id: 'tara_bala_natal_baseline',
    aliases: ['tara bala', 'tara', 'chandra bala', 'nakshatra strength', 'birth star strength', '9-fold nakshatra strength'],
    fact_categories: ['tara_bala_natal_baseline', 'chandra_bala_natal_baseline', 'graha_tara_bala'],
  },
  {
    concept_id: 'sensitive_degree_check',
    aliases: ['sensitive degrees', 'sensitive degree', 'pushkara', 'gandanta', 'mrityu bhaga', 'kranti', 'kartari degree'],
    fact_categories: ['sensitive_degree_check'],
  },
  {
    concept_id: 'aspect_jaimini',
    aliases: ['jaimini aspect', 'rashi drishti', 'jaimini drishti', 'jaimini rashi drishti', 'sign aspect'],
    fact_categories: ['aspect_jaimini', 'aspect_jaimini_per_varga'],
  },
  {
    concept_id: 'special_lagna',
    aliases: ['special lagna', 'special lagnas', 'varnada lagna', 'sree lagna', 'indu lagna', 'bhava lagna'],
    fact_categories: ['special_lagna'],
  },
]

/** A single resolution result — used by both `concept_locate` (registry capability) and,
 *  per Task 2 (Absence Protocol / EL-07), by any other capability that needs an honest
 *  concept-resolver MISS before it is allowed to phrase a served string as ontological
 *  absence ("not in your data" / "does not exist"). */
export type ConceptResolution = {
  resolved: boolean
  query: string
  matched_alias: string | null
  concept_id: string | null
  fact_categories: string[]
  resolved_via: 'alias_exact' | 'alias_substring' | 'concept_id_substring' | 'miss'
}

function normalize(s: string): string {
  return s.trim().toLowerCase()
}

/**
 * Resolve free-text `query` against the seed alias table. Pure function (no DB access) —
 * `concept_locate.ts` also falls back to a live fact_category substring match for anything
 * this seed table misses; that fallback lives in `concept_locate.ts` itself since it needs a
 * DB round trip. This function is the honest, cheap, in-memory first pass.
 */
export function resolveConceptAlias(query: string): ConceptResolution {
  const q = normalize(query)
  if (!q) {
    return {
      resolved: false, query, matched_alias: null, concept_id: null, fact_categories: [],
      resolved_via: 'miss',
    }
  }

  // Pass 1: exact alias match (or exact concept_id match).
  for (const entry of CONCEPT_ALIASES) {
    if (normalize(entry.concept_id) === q) {
      return {
        resolved: true, query, matched_alias: entry.concept_id, concept_id: entry.concept_id,
        fact_categories: entry.fact_categories, resolved_via: 'alias_exact',
      }
    }
    for (const alias of entry.aliases) {
      if (normalize(alias) === q) {
        return {
          resolved: true, query, matched_alias: alias, concept_id: entry.concept_id,
          fact_categories: entry.fact_categories, resolved_via: 'alias_exact',
        }
      }
    }
  }

  // Pass 2: substring match — query appears inside an alias, or an alias appears inside query
  // (handles "gulika kalam timing" -> "gulika", or "sade" -> "sade sati").
  for (const entry of CONCEPT_ALIASES) {
    for (const alias of entry.aliases) {
      const a = normalize(alias)
      if (a.includes(q) || q.includes(a)) {
        return {
          resolved: true, query, matched_alias: alias, concept_id: entry.concept_id,
          fact_categories: entry.fact_categories, resolved_via: 'alias_substring',
        }
      }
    }
  }

  // Pass 3: substring against concept_id itself (covers e.g. "shadbala_total").
  for (const entry of CONCEPT_ALIASES) {
    if (normalize(entry.concept_id).includes(q) || q.includes(normalize(entry.concept_id))) {
      return {
        resolved: true, query, matched_alias: entry.concept_id, concept_id: entry.concept_id,
        fact_categories: entry.fact_categories, resolved_via: 'concept_id_substring',
      }
    }
  }

  return {
    resolved: false, query, matched_alias: null, concept_id: null, fact_categories: [],
    resolved_via: 'miss',
  }
}
