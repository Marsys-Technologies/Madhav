import type { SourceQueryAvailabilityRequirement } from './types'
import { stableFingerprint } from './stable'

export type SourceQueryParameterBinding =
  | 'global'
  | 'global_with_chart_fallback'
  | 'chart_and_active_build'
  | 'chart_with_active_build_context'
export type SourceQueryEmptySemantics = 'query_success_is_available'

/**
 * Registry-owned, read-only probe for a handler's actual source query.
 *
 * The generated knowledge snapshot carries only the requirement and the exact
 * contract fingerprint. SQL remains source-owned here so an untrusted snapshot
 * cannot inject a query into the overlay loader.
 */
export interface SourceQueryAvailabilityContract {
  readonly contract_id: string
  readonly descriptor_name: string
  readonly capability_uri: string
  readonly scope: 'chart' | 'global'
  readonly parameter_binding: SourceQueryParameterBinding
  readonly empty_semantics: SourceQueryEmptySemantics
  readonly sql: string
  readonly source_refs: readonly string[]
}

export interface DescriptorSourceQueryAvailabilityReview {
  readonly requirement: SourceQueryAvailabilityRequirement
}

export function sourceQueryAvailabilityContractFingerprint(
  contract: SourceQueryAvailabilityContract,
): string {
  return stableFingerprint(contract)
}

export function sourceQueryParameterBindingMatchesScope(
  scope: SourceQueryAvailabilityContract['scope'],
  parameterBinding: SourceQueryParameterBinding,
): boolean {
  return (scope === 'global' && (
    parameterBinding === 'global'
    || parameterBinding === 'global_with_chart_fallback'
  ))
    || (scope === 'chart' && (
      parameterBinding === 'chart_and_active_build'
      || parameterBinding === 'chart_with_active_build_context'
    ))
}

/*
 * Reviews are intentionally source-by-source. Do not infer membership from a
 * descriptor family or table name: a review is admitted only after the handler
 * relation, scope/parameter binding, and honest-empty behavior have all been read.
 */
const CONTRACTS: readonly SourceQueryAvailabilityContract[] = [
  {
    contract_id: 'source-query:get-tara-chandra-bala:v1',
    descriptor_name: 'get_tara_chandra_bala',
    capability_uri: 'marsys://tool/L1/get_tara_chandra_bala',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY['tara_bala_natal_baseline', 'chandra_bala_natal_baseline']::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY['tara_bala_natal_baseline', 'chandra_bala_natal_baseline']::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_tara_chandra_bala.ts:53-84',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-condition-composite:v1',
    descriptor_name: 'get_condition_composite',
    capability_uri: 'marsys://tool/L1/get_condition_composite',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT graha, ayanamsha_id, dignity_d1, dignity_score_d1, varga_dignity_spread,
                   varga_dignity_composite, avastha_baladi, avastha_jagradadi, avastha_deeptaadi,
                   avastha_lajjitaadi, avastha_sayanadi, motion_state, speed_degrees_per_day,
                   is_retrograde, combustion_arc_from_sun, is_combust, is_deeply_combust,
                   naisargika_relation, tatkalika_relation, panchadha_relation, graha_yuddha_with,
                   graha_yuddha_result, condition_score, condition_formula_version,
                   condition_score_breakdown, peak_dasha_periods, weak_dasha_periods, computed_at
              FROM ga_condition_composite
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR graha = NULL::text)
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY graha, ayanamsha_id
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM ga_condition_composite
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR graha = NULL::text)
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts:75-107',
      'platform/migrations/251_ga_condition_composite.sql:1-73',
    ],
  },
  {
    contract_id: 'source-query:get-bhava-bala:v1',
    descriptor_name: 'get_bhava_bala',
    capability_uri: 'marsys://tool/L1/get_bhava_bala',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'bhava_bala_aspectual', 'bhava_bala_directional', 'bhava_bala_lord',
               'bhava_bala_occupant', 'bhava_bala_positional', 'bhava_bala_temporal',
               'bhava_bala_total_extended', 'house_bhava_bala_subscore',
               'house_bhava_bala_total', 'house_strength_classification_rollup'
             ]::text[])
             AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             AND (NULL::text IS NULL OR fact_key ILIKE NULL::text)
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_bhava_bala.ts:54-79',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-karakas:v1',
    descriptor_name: 'get_karakas',
    capability_uri: 'marsys://tool/L1/get_karakas',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'karaka_chara_position', 'karakamsa_position', 'swamsa_position', 'arudha_pada',
                 'bhava_arudha', 'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
                 'kp_cuspal_significators', 'kp_ruling_planets_natal', 'jaimini_tri_deva_role_per_graha'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'karaka_chara_position', 'karakamsa_position', 'swamsa_position', 'arudha_pada',
                 'bhava_arudha', 'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
                 'kp_cuspal_significators', 'kp_ruling_planets_natal', 'jaimini_tri_deva_role_per_graha'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts:103-123',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-dignity:v1',
    descriptor_name: 'get_dignity',
    capability_uri: 'marsys://tool/L1/get_dignity',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'graha_dignity_per_varga', 'graha_effective_dignity_modified_by_aspects',
                 'graha_sign_attributes', 'graha_vargottama_amplification_factor',
                 'vargottama_per_varga', 'graha_functional_class_per_ascendant'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR fact_key ILIKE NULL::text)
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'graha_dignity_per_varga', 'graha_effective_dignity_modified_by_aspects',
                 'graha_sign_attributes', 'graha_vargottama_amplification_factor',
                 'vargottama_per_varga', 'graha_functional_class_per_ascendant'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR fact_key ILIKE NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_dignity.ts:78-108',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-aspects:v1',
    descriptor_name: 'get_aspects',
    capability_uri: 'marsys://tool/L1/get_aspects',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'aspect_parashari_given', 'aspect_parashari_received', 'aspect_parashari_per_varga',
               'aspect_jaimini', 'aspect_jaimini_per_varga', 'aspect_matrix_summary', 'aspect_tajik',
               'conjunction_within_orb', 'conjunction_per_varga',
               'lord_aspects_lord_per_varga', 'lord_in_house_per_varga'
             ]::text[])
             AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_aspects.ts:55-91',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-ashtakavarga:v1',
    descriptor_name: 'get_ashtakavarga',
    capability_uri: 'marsys://tool/L1/get_ashtakavarga',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'ashtakavarga_bindu', 'ashtakavarga_anubindu', 'ashtakavarga_bindu_sign',
               'ashtakavarga_pinda_bhinna', 'ashtakavarga_pinda_sarva', 'ashtakavarga_pinda_sodhita',
               'ashtakavarga_pinda_raasi', 'ashtakavarga_trikona_shodhana',
               'ashtakavarga_ekadhipathya_shodhana', 'ashtakavarga_kakshya_boundary'
             ]::text[])
             AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_ashtakavarga.ts:88-124',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-avasthas:v1',
    descriptor_name: 'get_avasthas',
    capability_uri: 'marsys://tool/L1/get_avasthas',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'graha_avastha_baladi', 'graha_avastha_deepta', 'graha_avastha_jagrad',
                 'graha_avastha_lajjitadi', 'graha_avastha_lifetime_exposure_summary',
                 'graha_avastha_sayanadi'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'graha_avastha_baladi', 'graha_avastha_deepta', 'graha_avastha_jagrad',
                 'graha_avastha_lajjitadi', 'graha_avastha_lifetime_exposure_summary',
                 'graha_avastha_sayanadi'
               ]::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_avasthas.ts:71-100',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-argala:v1',
    descriptor_name: 'get_argala',
    capability_uri: 'marsys://tool/L1/get_argala',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, ayanamsha_id, fact_subject, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY['argala_natal_matrix', 'virodha_argala_natal_matrix']::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR fact_subject LIKE NULL::text || '%')
             ORDER BY ayanamsha_id, fact_subject, fact_key
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY['argala_natal_matrix', 'virodha_argala_natal_matrix']::text[])
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR fact_subject LIKE NULL::text || '%')
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_argala.ts:112-155',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-dispositors:v1',
    descriptor_name: 'get_dispositors',
    capability_uri: 'marsys://tool/L1/get_dispositors',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'graha_dispositor_chain', 'dispositor_chain_per_varga', 'composite_dispositor_strength',
               'parivartana_per_varga', 'kala_sarpa_per_varga'
             ]::text[])
             AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_dispositors.ts:20-79',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-eclipse-flags:v1',
    descriptor_name: 'get_eclipse_flags',
    capability_uri: 'marsys://tool/L1/get_eclipse_flags',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = 'eclipse_proximity_natal'
           ORDER BY ayanamsha_id, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_eclipse_flags.ts:38-62',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:query-yoga-catalog:v1',
    descriptor_name: 'query_yoga_catalog',
    capability_uri: 'marsys://tool/L0/query_yoga_catalog',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
          SELECT *
            FROM brahma_yoga_catalog
           WHERE name_en IS NOT NULL OR school IS NULL OR category IS NULL
           ORDER BY school, name_en
           LIMIT 0 OFFSET 0
        ), handler_count AS (
          SELECT COUNT(*)::text AS total
            FROM brahma_yoga_catalog
           WHERE name_en IS NOT NULL OR school IS NULL OR category IS NULL
        )
        SELECT handler_page.*, handler_count.total
          FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts:52-62',
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts:63-75',
    ],
  },
  {
    contract_id: 'source-query:query-dosha-catalog:v1',
    descriptor_name: 'query_dosha_catalog',
    capability_uri: 'marsys://tool/L0/query_dosha_catalog',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
          SELECT *
            FROM brahma_dosha_catalog
           WHERE 1=1
             AND (NULL::text IS NULL OR name_en ILIKE NULL::text
                  OR name_sa ILIKE NULL::text OR canonical_id ILIKE NULL::text)
             AND (NULL::text IS NULL OR severity_grades ? NULL::text)
             AND (NULL::text IS NULL OR category = NULL::text)
           ORDER BY category, name_en
           LIMIT 0 OFFSET 0
        ), handler_count AS (
          SELECT COUNT(*)::text AS total
            FROM brahma_dosha_catalog
           WHERE 1=1
             AND (NULL::text IS NULL OR name_en ILIKE NULL::text
                  OR name_sa ILIKE NULL::text OR canonical_id ILIKE NULL::text)
             AND (NULL::text IS NULL OR severity_grades ? NULL::text)
             AND (NULL::text IS NULL OR category = NULL::text)
        )
        SELECT handler_page.*, handler_count.total
          FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dosha_catalog.ts:42-99',
      'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:52-71',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_doshas.py:15-36',
      'platform/python-sidecar/brahmagyan/l0_doshas.py:1926-2047',
      'platform/supabase/migrations/622_nirmana_l0_doshas_integrity_contract.sql:1-84',
    ],
  },
  {
    contract_id: 'source-query:query-compendium-index:v1',
    descriptor_name: 'query_compendium_index',
    capability_uri: 'marsys://tool/L0/query_compendium_index',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
          SELECT index_id, text_id, chapter_num, chapter_title_en, chapter_title_sa, topic_id,
                 verse_start, verse_end, chunk_ids, summary_text, significance,
                 classical_significance_score
            FROM brahma_compendium_index
           WHERE 1=1
             AND (NULL::text IS NULL OR text_id = NULL::text)
             AND (NULL::integer IS NULL OR chapter_num = NULL::integer)
             AND (NULL::text IS NULL OR topic_id = NULL::text)
           ORDER BY text_id, chapter_num, verse_start
           LIMIT 0
        ), handler_count AS (
          SELECT COUNT(*)::int AS total
            FROM brahma_compendium_index
           WHERE 1=1
             AND (NULL::text IS NULL OR text_id = NULL::text)
             AND (NULL::integer IS NULL OR chapter_num = NULL::integer)
             AND (NULL::text IS NULL OR topic_id = NULL::text)
        )
        SELECT handler_page.*, handler_count.total
          FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_compendium_index.ts:58-107',
      'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:74-93',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_compendium_index.py:49-113',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_compendium_index.py:116-211',
      'platform/supabase/migrations/623_nirmana_l0_compendium_index_integrity_contract.sql:1-84',
    ],
  },
  {
    contract_id: 'source-query:list-entities:v1',
    descriptor_name: 'list_entities',
    capability_uri: 'marsys://tool/L0/list_entities',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
          SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms
            FROM brahma_ontology
           ORDER BY entity_class, canonical_name_en
           LIMIT 0 OFFSET 0
        ), handler_count AS (
          SELECT COUNT(*)::int AS total
            FROM brahma_ontology
        )
        SELECT handler_page.*, handler_count.total
          FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/list_entities.ts:136-160',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:17',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py:15-30',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:74-102',
    ],
  },
  {
    contract_id: 'source-query:resolve-entity:v1',
    descriptor_name: 'resolve_entity',
    capability_uri: 'marsys://tool/L0/resolve_entity',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa,
                 synonyms, description, source_citation
            FROM brahma_ontology
           WHERE NULL::text = ANY(synonyms)
              OR lower(canonical_name_en) = lower(NULL::text)
              OR lower(canonical_name_sa) = lower(NULL::text)
           ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts:45-92',
      'platform/migrations/ws2_l0_ontology.sql:15-37',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py:15-30',
      'platform/python-sidecar/brahmagyan/l0_ontology.py:1094-1173',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:74-102',
    ],
  },
  {
    contract_id: 'source-query:list-classical-texts:v1',
    descriptor_name: 'list_classical_texts',
    capability_uri: 'marsys://tool/L0/list_classical_texts',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT
          t.text_id,
          t.title_en,
          t.author,
          t.school,
          t.tradition,
          COUNT(c.chunk_id) AS chunk_count,
          s.source_url,
          t.license
        FROM classical_texts t
        LEFT JOIN classical_text_chunks c ON c.text_id = t.text_id
        LEFT JOIN classical_texts_source s ON s.text_id = t.text_id
        GROUP BY t.text_id, t.title_en, t.author, t.school, t.tradition, s.source_url, t.license
        ORDER BY t.text_id
        LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:2063-2075',
      'platform/src/lib/tools/classical_text_tools.ts:77-116',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:16',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py:39-59',
      'platform/supabase/migrations/610_nirmana_bg_texts_integrity_contract.sql:56-110',
    ],
  },
  {
    contract_id: 'source-query:read-chapter:v1',
    descriptor_name: 'read_chapter',
    capability_uri: 'marsys://tool/L0/read_chapter',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT chunk_id, verse_ref, content_en, content_sa
            FROM classical_text_chunks
           WHERE text_id = NULL::text
             AND chapter = NULL::integer
           ORDER BY verse_start, chunk_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1961-2026',
      'platform/src/lib/tools/classical_text_tools.ts:35-58',
      'platform/migrations/ws2_l0_texts.sql:42-65',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py:355-385',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py:660-683',
      'platform/supabase/migrations/609_nirmana_l0_digest_spec_revision.sql:25-27',
      'platform/supabase/migrations/610_nirmana_bg_texts_integrity_contract.sql:56-128',
    ],
  },
  {
    contract_id: 'source-query:query-avastha-schemes:v1',
    descriptor_name: 'query_avastha_schemes',
    capability_uri: 'marsys://tool/L0/query_avastha_schemes',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT scheme_name, state_name, state_order, determination_rule,
                 classical_citation, notes
            FROM bg_avastha_schemes
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(scheme_name) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR LOWER(state_name) = LOWER(NULL::text))
           ORDER BY scheme_name, state_order
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_avastha_schemes.ts:48-66',
      'platform/migrations/250_bg_dignity_reference.sql:239-256',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:474-499',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:184',
    ],
  },
  {
    contract_id: 'source-query:query-combustion-orbs:v1',
    descriptor_name: 'query_combustion_orbs',
    capability_uri: 'marsys://tool/L0/query_combustion_orbs',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT graha, orb_degrees, deep_orb_degrees, retrograde_note,
                 classical_citation
            FROM bg_combustion_orbs
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
           ORDER BY graha
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_combustion_orbs.ts:51-68',
      'platform/migrations/250_bg_dignity_reference.sql:484-497',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:501-516',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:187',
    ],
  },
  {
    contract_id: 'source-query:query-graha-naisargika-friendship:v1',
    descriptor_name: 'query_graha_naisargika_friendship',
    capability_uri: 'marsys://tool/L0/query_graha_naisargika_friendship',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT graha, other_graha, relation, classical_citation
            FROM bg_graha_naisargika_friendship
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR LOWER(other_graha) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR relation = NULL::text)
           ORDER BY graha, other_graha
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_naisargika_friendship.ts:51-69',
      'platform/migrations/250_bg_dignity_reference.sql:128-140',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:64-149',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:442-455',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:166-179',
    ],
  },
  {
    contract_id: 'source-query:query-motion-state-thresholds:v1',
    descriptor_name: 'query_motion_state_thresholds',
    capability_uri: 'marsys://tool/L0/query_motion_state_thresholds',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT graha, motion_state, speed_threshold_low, speed_threshold_high, threshold_type,
                 typical_speed_dps, classical_citation, notes
            FROM bg_motion_state_thresholds
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR LOWER(motion_state) = LOWER(NULL::text))
           ORDER BY graha, motion_state
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_motion_state_thresholds.ts:49-66',
      'platform/migrations/250_bg_dignity_reference.sql:406-423',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:274-323',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:475-499',
      'platform/supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql:184-186',
    ],
  },
  {
    contract_id: 'source-query:query-vastu-directions:v1',
    descriptor_name: 'query_vastu_directions',
    capability_uri: 'marsys://tool/L0/query_vastu_directions',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT direction, direction_deg, ruling_graha, secondary_graha, favorable_color, element,
                 classical_citation
            FROM bg_vastu_directions
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(direction) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR LOWER(ruling_graha) = LOWER(NULL::text))
           ORDER BY direction_deg
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vastu_directions.ts:49-68',
      'platform/migrations/284_bg_vastu_directions.sql:10-33',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_vastu_directions.py:22-40',
      'platform/supabase/migrations/612_nirmana_l0_vastu_medical_integrity_contract.sql:21-30',
    ],
  },
  {
    contract_id: 'source-query:query-vastu-direction-remedials:v1',
    descriptor_name: 'query_vastu_direction_remedials',
    capability_uri: 'marsys://tool/L0/query_vastu_direction_remedials',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT direction, remedy_type, remedy_description, classical_citation
            FROM bg_vastu_direction_remedials
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(direction) = LOWER(NULL::text))
             AND (NULL::text IS NULL OR LOWER(remedy_type) = LOWER(NULL::text))
           ORDER BY direction, remedy_type
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vastu_direction_remedials.ts:45-64',
      'platform/migrations/284_bg_vastu_directions.sql:37-89',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_vastu_directions.py:22-40',
      'platform/supabase/migrations/612_nirmana_l0_vastu_medical_integrity_contract.sql:31-38',
    ],
  },
  {
    contract_id: 'source-query:query-graha-dik:v1',
    descriptor_name: 'query_graha_dik',
    capability_uri: 'marsys://tool/L0/query_graha_dik',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT graha, peak_house, peak_direction, debility_house, paired_graha, school_note,
                 classical_citation
            FROM bg_graha_dik
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
           ORDER BY graha
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_dik.ts:53-57',
      'platform/migrations/304_bg_graha_dik.sql:22-32',
    ],
  },
  {
    contract_id: 'source-query:query-shashtiamsha-deities:v1',
    descriptor_name: 'query_shashtiamsha_deities',
    capability_uri: 'marsys://tool/L0/query_shashtiamsha_deities',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT amsa_number, quality, deity_name, classical_citation, rule_notes
            FROM bg_shashtiamsha_deities
           WHERE 1=1
             AND (NULL::integer IS NULL OR amsa_number = NULL::integer)
             AND (NULL::text IS NULL OR LOWER(quality) = LOWER(NULL::text))
           ORDER BY amsa_number
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_shashtiamsha_deities.ts:62-66',
      'platform/supabase/migrations/430_bg_shashtiamsha_deities.sql:34-42',
    ],
  },
  {
    contract_id: 'source-query:query-prashna-lagna-methods:v1',
    descriptor_name: 'query_prashna_lagna_methods',
    capability_uri: 'marsys://tool/L0/query_prashna_lagna_methods',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT method_id, method_name, method_name_sa, derivation_rule, derivation_rule_jsonb,
                 classical_citation, is_primary, tradition
            FROM bg_prashna_lagna_methods
           WHERE 1=1
             AND (NULL::text IS NULL OR method_id = NULL::text)
             AND (NULL::text IS NULL OR LOWER(tradition) = LOWER(NULL::text))
           ORDER BY method_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_lagna_methods.ts:55-63',
      'platform/migrations/261_bg_prashna_rules_schema.sql:6-16',
      'platform/python-sidecar/brahmagyan/l0_prashna.py:804-831',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:24',
      'platform/supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql:27-34',
    ],
  },
  {
    contract_id: 'source-query:query-prashna-tajik-yogas:v1',
    descriptor_name: 'query_prashna_tajik_yogas',
    capability_uri: 'marsys://tool/L0/query_prashna_tajik_yogas',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT yoga_id, yoga_name, yoga_name_sa, judgment_meaning, formation_rule,
                 formation_rule_jsonb, classical_citation, is_fructification_indicator
            FROM bg_prashna_tajik_yogas
           WHERE 1=1
             AND (NULL::text IS NULL OR yoga_id = NULL::text)
             AND (NULL::boolean IS NULL OR is_fructification_indicator = NULL::boolean)
           ORDER BY yoga_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_tajik_yogas.ts:56-64',
      'platform/migrations/261_bg_prashna_rules_schema.sql:19-29',
      'platform/python-sidecar/brahmagyan/l0_prashna.py:833-860',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:24',
      'platform/supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql:35-43',
    ],
  },
  {
    contract_id: 'source-query:query-prashna-significators:v1',
    descriptor_name: 'query_prashna_significators',
    capability_uri: 'marsys://tool/L0/query_prashna_significators',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT question_class, querent_house, querent_planet, quesited_house, quesited_planet,
                 significator_rule, classical_citation
            FROM bg_prashna_significators
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(question_class) = LOWER(NULL::text))
           ORDER BY question_class
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_significators.ts:51-56',
      'platform/migrations/261_bg_prashna_rules_schema.sql:32-42',
      'platform/python-sidecar/brahmagyan/l0_prashna.py:862-887',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:24',
      'platform/supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql:44-51',
    ],
  },
  {
    contract_id: 'source-query:query-prashna-fructification-rules:v1',
    descriptor_name: 'query_prashna_fructification_rules',
    capability_uri: 'marsys://tool/L0/query_prashna_fructification_rules',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT rule_id, time_unit, degree_conversion_rule, applicable_when, classical_citation
            FROM bg_prashna_fructification_rules
           WHERE 1=1
             AND (NULL::text IS NULL OR rule_id = NULL::text)
             AND (NULL::text IS NULL OR LOWER(time_unit) = LOWER(NULL::text))
           ORDER BY rule_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_fructification_rules.ts:55-59',
      'platform/migrations/261_bg_prashna_rules_schema.sql:45-52',
      'platform/python-sidecar/brahmagyan/l0_prashna.py:889-909',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:24',
      'platform/supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql:52-58',
    ],
  },
  {
    contract_id: 'source-query:query-prashna-special-techniques:v1',
    descriptor_name: 'query_prashna_special_techniques',
    capability_uri: 'marsys://tool/L0/query_prashna_special_techniques',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT technique_id, technique_name, technique_name_sa, application_rule, classical_citation
            FROM bg_prashna_special_techniques
           WHERE 1=1
             AND (NULL::text IS NULL OR technique_id = NULL::text)
           ORDER BY technique_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_special_techniques.ts:41-55',
      'platform/migrations/261_bg_prashna_rules_schema.sql:54-62',
      'platform/python-sidecar/brahmagyan/l0_prashna.py:911-931',
      'platform/supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql:24',
      'platform/supabase/migrations/616_nirmana_l0_prashna_integrity_contract.sql:59-65',
    ],
  },
  {
    contract_id: 'source-query:query-class-priors:v1',
    descriptor_name: 'query_class_priors',
    capability_uri: 'marsys://tool/L0/query_class_priors',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition,
                 class_prior, varga_weights, contested, citation, ratified_by
            FROM brahma_class_priors
           WHERE fact_kind <> 'lifetime_count_per_100y'
             AND (NULL::text IS NULL OR prior_version = NULL::text)
             AND (NULL::text IS NULL OR signal_type_class = NULL::text)
             AND (NULL::text IS NULL OR source_subsystem = NULL::text)
           ORDER BY prior_version, signal_type_class, source_subsystem
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_class_priors.ts:91-115',
      'platform/supabase/migrations/387_brahma_class_priors.sql:18-31',
      'platform/supabase/migrations/522_brahma_class_lifetime_counts.sql:67-100',
      'platform/python-sidecar/pipeline/orchestrator/writers/bg_class_priors.py:21-39',
      'platform/supabase/migrations/615_nirmana_l0_governance_integrity_contracts.sql:1-45',
    ],
  },
  {
    contract_id: 'source-query:query-muhurta-lattice:v1',
    descriptor_name: 'query_muhurta_lattice',
    capability_uri: 'marsys://tool/L0/query_muhurta_lattice',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT factor_family, factor_key, start_utc, end_utc, detail,
                 reference_lat, reference_lon, reference_tz_offset_minutes,
                 reference_location_key, ayanamsha_key, sampling_method,
                 source_citation, corpus_status
            FROM bg_muhurta_lattice
           WHERE start_utc < NULL::timestamp
             AND end_utc > NULL::timestamp
             AND (NULL::text IS NULL OR factor_family = NULL::text)
             AND (NULL::text IS NULL OR factor_key = NULL::text)
           ORDER BY start_utc, factor_family, factor_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_muhurta_lattice.ts:128-147',
      'platform/supabase/migrations/543_bg_muhurta_lattice.sql:57-85',
      'platform/supabase/migrations/530_bg_muhurta_lattice_panchangika_families.sql:77-93',
    ],
  },
  {
    contract_id: 'source-query:query-transit-moorti:v1',
    descriptor_name: 'query_transit_moorti',
    capability_uri: 'marsys://tool/L0/query_transit_moorti',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation, rule_notes
            FROM bg_transit_moorti
           WHERE 1=1
             AND (NULL::integer IS NULL OR nakshatra_offset = NULL::integer)
             AND (NULL::text IS NULL OR LOWER(moorti_name) = LOWER(NULL::text))
           ORDER BY nakshatra_offset
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_moorti.ts:59-73',
      'platform/supabase/migrations/401_bg_transit_moorti.sql:10-20',
    ],
  },
  {
    contract_id: 'source-query:query-transit-engine:v1',
    descriptor_name: 'query_transit_engine',
    capability_uri: 'marsys://tool/L0/query_transit_engine',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation
            FROM bg_transit_engine
           WHERE 1=1
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
           ORDER BY graha
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_engine.ts:58-75',
      'platform/migrations/266_bg_transit_tables.sql:21-32',
    ],
  },
  {
    contract_id: 'source-query:query-transit-av-gates:v1',
    descriptor_name: 'query_transit_av_gates',
    capability_uri: 'marsys://tool/L0/query_transit_av_gates',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT gate_kind, graha, house_from_moon, kakshya_lord, min_av_score, min_sav_score,
                 effect, classical_citation, rule_notes
            FROM bg_transit_av_gates
           WHERE 1=1
             AND (NULL::text IS NULL OR gate_kind = NULL::text)
             AND (NULL::text IS NULL OR LOWER(graha) = LOWER(NULL::text))
           ORDER BY gate_kind, graha, house_from_moon
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_av_gates.ts:67-85',
      'platform/supabase/migrations/397_bg_transit_av_gates.sql:10-38',
    ],
  },
  {
    contract_id: 'source-query:query-dasha-systems:v1',
    descriptor_name: 'query_dasha_systems',
    capability_uri: 'marsys://tool/L0/query_dasha_systems',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT canonical_id, name_sa, name_en, total_cycle_years, base_unit, sequence_jsonb,
                 computation_method, computation_pseudocode, conditions_for_use, school,
                 classical_citations
            FROM brahma_dasha_systems
           WHERE 1=1
             AND (NULL::text IS NULL OR canonical_id = NULL::text)
             AND (NULL::text IS NULL OR LOWER(school) = LOWER(NULL::text))
           ORDER BY canonical_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts:60-66',
      'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:30-49',
    ],
  },
  {
    contract_id: 'source-query:query-formula-constants:v1',
    descriptor_name: 'query_formula_constants',
    capability_uri: 'marsys://tool/L0/query_formula_constants',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT constant_id, value_jsonb, class, consumer_assets, citation_or_ratification,
                 calibratable, bounds, version
            FROM brahma_formula_constants
           WHERE 1=1
             AND (NULL::text IS NULL OR constant_id = NULL::text)
             AND (NULL::text IS NULL OR class = NULL::text)
           ORDER BY constant_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_formula_constants.ts:64-69',
      'platform/supabase/migrations/389_brahma_formula_constants.sql:9-27',
    ],
  },
  {
    contract_id: 'source-query:query-vichara-constants:v1',
    descriptor_name: 'query_vichara_constants',
    capability_uri: 'marsys://tool/L0/query_vichara_constants',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT constant_key, value_jsonb, citation, version, updated_at
            FROM brahma_vichara_constants
           WHERE 1=1
             AND (NULL::text IS NULL OR constant_key = NULL::text)
           ORDER BY constant_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vichara_constants.ts:55-59',
      'platform/migrations/435_ga_vichara.sql:83-89',
    ],
  },
  {
    contract_id: 'source-query:query-remedies-for-chart:v1',
    descriptor_name: 'query_remedies_for_chart',
    capability_uri: 'marsys://tool/L0/query_remedies_for_chart',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT remedy_id, planet, domain, category, deity,
                 prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
                 cost_tier, contraindications, source_canonical_id, source_citation,
                 classical_attestation_text
            FROM brahma_remedy_corpus
           WHERE planet ILIKE '%' || NULL::text || '%'
              OR domain ILIKE '%' || NULL::text || '%'
           ORDER BY confidence DESC NULLS LAST, cost_tier ASC
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1501-1517',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/081_l0fr_schema.sql:113-123',
    ],
  },
  {
    contract_id: 'source-query:query-remedies-by-planet:v1',
    descriptor_name: 'query_remedies_by_planet',
    capability_uri: 'marsys://tool/L0/query_remedies_by_planet',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT remedy_id, planet, domain, category, deity,
                 prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
                 cost_tier, contraindications, source_canonical_id, classical_attestation_text
            FROM brahma_remedy_corpus
           WHERE LOWER(planet) = LOWER(NULL::text)
           ORDER BY category, remedy_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1842-1849',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/081_l0fr_schema.sql:113-123',
    ],
  },
  {
    contract_id: 'source-query:read-remedy:v1',
    descriptor_name: 'read_remedy',
    capability_uri: 'marsys://tool/L0/read_remedy',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT id, remedy_id, planet, domain, remedy_type,
                 prescription_text, mantra_text, gemstone, charity_action,
                 day_of_week, color_associated, confidence,
                 source_canonical_id, source_citation, classical_ref, created_at,
                 category, deity, mantra_sanskrit, mantra_transliteration,
                 ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications,
                 classical_attestation_text, scaffold_status
            FROM brahma_remedy_corpus
           WHERE remedy_id = NULL::text
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1700-1710',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/081_l0fr_schema.sql:113-123',
      'platform/supabase/migrations/177_l0_phase_alpha_existing_table_schema.sql:17-20',
    ],
  },
  {
    contract_id: 'source-query:query-mantras:v1',
    descriptor_name: 'query_mantras',
    capability_uri: 'marsys://tool/L0/query_mantras',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT remedy_id, planet, deity,
                 mantra_sanskrit, mantra_transliteration, mantra_text,
                 prescription_text, timing_rules_jsonb,
                 source_canonical_id, classical_attestation_text, classical_ref
            FROM brahma_remedy_corpus
           WHERE (LOWER(remedy_type) = 'mantra' OR LOWER(category) = 'mantras')
             AND scaffold_status = 'live'
             AND (NULL::text IS NULL OR LOWER(planet) = LOWER(NULL::text))
           ORDER BY planet, remedy_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1921-1936',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/081_l0fr_schema.sql:113-123',
      'platform/supabase/migrations/177_l0_phase_alpha_existing_table_schema.sql:17-20',
    ],
  },
  {
    contract_id: 'source-query:query-tantric-remedies:v1',
    descriptor_name: 'query_tantric_remedies',
    capability_uri: 'marsys://tool/L0/query_tantric_remedies',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT remedy_id, planet, domain, deity,
                 prescription_text, mantra_sanskrit, mantra_transliteration,
                 ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications,
                 source_canonical_id, source_citation, classical_attestation_text
            FROM brahma_remedy_corpus
           WHERE (LOWER(remedy_type) = 'tantric' OR LOWER(category) = 'tantric')
             AND (NULL::text IS NULL OR deity ILIKE '%' || NULL::text || '%')
             AND (NULL::text IS NULL OR LOWER(planet) = LOWER(NULL::text))
           ORDER BY planet, remedy_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1763-1776',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/081_l0fr_schema.sql:113-123',
    ],
  },
  {
    contract_id: 'source-query:query-parihara-graph:v1',
    descriptor_name: 'query_parihara_graph',
    capability_uri: 'marsys://tool/L0/query_parihara_graph',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH parihara_rules_probe AS (
            SELECT dosha_canonical_id, dosha_name_en, dosha_category, cancellation_index,
                   cancellation_condition_text, net_standing, scope,
                   source_text_id, source_chapter, source_citation, extraction_context
              FROM bg_parihara_rules
             WHERE 1=1
               AND (NULL::text IS NULL OR dosha_canonical_id = NULL::text)
             ORDER BY dosha_canonical_id, cancellation_index
             LIMIT 0
          ), density_split_probe AS (
            SELECT
              COUNT(*) FILTER (
                WHERE cancellation_conditions IS NOT NULL
                  AND classical_citations IS NOT NULL
                  AND jsonb_typeof(classical_citations) = 'array'
                  AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(classical_citations) elem
                    WHERE elem->>'text_id' IS NOT NULL
                      AND elem->>'text_id' <> 'classical_tradition')
              ) AS real_cited,
              COUNT(*) FILTER (
                WHERE cancellation_conditions IS NOT NULL
                  AND NOT (
                    classical_citations IS NOT NULL
                    AND jsonb_typeof(classical_citations) = 'array'
                    AND EXISTS (
                      SELECT 1 FROM jsonb_array_elements(classical_citations) elem
                      WHERE elem->>'text_id' IS NOT NULL
                        AND elem->>'text_id' <> 'classical_tradition'))
              ) AS placeholder_only
              FROM brahma_dosha_catalog
             LIMIT 0
          ), activity_rules_probe AS (
            SELECT activity_class, factor_type, factor_id, quality_score, source_citation
              FROM bg_muhurta_activity_rules
             WHERE 1=1
               AND (NULL::text IS NULL OR activity_class = NULL::text)
             ORDER BY activity_class, factor_type, factor_id
             LIMIT 0
          ), factor_census_probe AS (
            SELECT factor_family, factor_name, disposition, citation_or_gap_note,
                   evidence_pointer, school_tag
              FROM bg_muhurta_factor_census
             WHERE 1=1
               AND (NULL::text IS NULL OR disposition = NULL::text)
             ORDER BY factor_family, factor_name
             LIMIT 0
          )
          SELECT 1 AS source_query_available
            FROM parihara_rules_probe
            CROSS JOIN density_split_probe
            CROSS JOIN activity_rules_probe
            CROSS JOIN factor_census_probe
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_parihara_graph.ts:125-227',
      'platform/supabase/migrations/485_bg_parihara_rules.sql:63-138',
      'platform/scripts/ci/migration_renumber_disclosed.json:30-36',
      'platform/supabase/migrations/524_bg_parihara_rules_muhurta_extraction_context.sql:52-65',
      'platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql:52-66',
    ],
  },
  {
    contract_id: 'source-query:query-falsifiers:v1',
    descriptor_name: 'query_falsifiers',
    capability_uri: 'marsys://tool/L4/query_falsifiers',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT pramana_id, anchor_id, evidence_type, evidence_strength_label,
                 falsifier_text, observable_criteria_jsonb, window_status,
                 lel_entry_id, linked_sodhana_id, source_citation
            FROM phala_pramana
           WHERE chart_id = $1::uuid
           ORDER BY array_position(ARRAY['open', 'pending', 'past_window']::text[], window_status) NULLS LAST, pramana_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts:241-250',
      'platform/src/lib/retrieval/registry/layers/L4_phala/salience_order.ts:43-64',
      'platform/supabase/migrations/338_phala_pramana.sql:23-67',
    ],
  },
  {
    contract_id: 'source-query:get-ayurdaya:v1',
    descriptor_name: 'get_ayurdaya',
    capability_uri: 'marsys://tool/L1/get_ayurdaya',
    scope: 'chart',
    parameter_binding: 'chart_and_active_build',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_subject, fact_key, fact_value_num, fact_value_text,
                   fact_value_jsonb, unit, ayanamsha_id, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND build_id = $2::uuid
               AND fact_category = 'ayurdaya'
             ORDER BY ayanamsha_id, fact_subject, fact_key
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND build_id = $2::uuid
               AND fact_category = 'ayurdaya'
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts:71-95',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts:112-130',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/python-sidecar/ga_writers/ga_ayurdaya_writer.py:270-310',
      'platform/python-sidecar/ga_writers/_idempotency.py:54-78',
    ],
  },
  {
    contract_id: 'source-query:get-sensitive-degrees:v1',
    descriptor_name: 'get_sensitive_degrees',
    capability_uri: 'marsys://tool/L1/get_sensitive_degrees',
    scope: 'chart',
    parameter_binding: 'chart_and_active_build',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_num, fact_value_text,
                   fact_value_jsonb, unit, ayanamsha_id, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND build_id = $2::uuid
               AND fact_category = ANY(ARRAY['sensitive_degree_check', 'sensitive_point_yogi']::text[])
             ORDER BY ayanamsha_id, fact_category, fact_subject, fact_key
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND build_id = $2::uuid
               AND fact_category = ANY(ARRAY['sensitive_degree_check', 'sensitive_point_yogi']::text[])
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_degrees.ts:97-120',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_degrees.ts:131-155',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/python-sidecar/ga_writers/ga_sensitive_writer.py:2895-2971',
      'platform/python-sidecar/ga_writers/_idempotency.py:54-78',
    ],
  },
  {
    contract_id: 'source-query:ganita-chart-facts-divisional:v1',
    // This is the MCP-only divisional section, not the broader chart_facts
    // query. Its handler reads chart_divisionals directly and intentionally
    // does not claim that the pivoted chart_facts relation is available.
    descriptor_name: 'ganita_chart_facts_get_divisional',
    capability_uri: 'mcp://tool/ganita_chart_facts_get',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT id
            FROM chart_divisionals
           WHERE chart_id = $1::uuid
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1298-1376',
      'platform-mcp/src/tools/register_p1_aliases.ts:1546-1581',
      'platform/migrations/002_ganita_divisionals.sql:31-59',
    ],
  },
  {
    contract_id: 'source-query:yoga-activation-by-dasha:v1',
    descriptor_name: 'yoga_activation_by_dasha_source',
    capability_uri: 'marsys://tool/L-TIMING/yoga_activation_by_dasha',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT m.signal_id
            FROM bodha_msr_signals m
            JOIN kala_activation ka ON ka.signal_id = m.signal_id
              AND ka.ayanamsha_id = m.ayanamsha_id
              AND ka.chart_id = m.chart_id
           WHERE m.chart_id = $1::uuid
             AND ka.chart_id = $1::uuid
             AND m.signal_type_class = 'yoga'
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:1906-1963',
      'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:2024-2039',
    ],
  },
  {
    contract_id: 'source-query:query-remedy-corpus:v1',
    descriptor_name: 'query_remedy_corpus',
    capability_uri: 'marsys://tool/L0/query_remedy_corpus',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT remedy_id, planet, remedy_type, category, deity, prescription_text, mantra_text,
                   source_canonical_id, source_citation, cost_tier, confidence
              FROM brahma_remedy_corpus
             WHERE 1=1
             ORDER BY planet, remedy_type
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::int AS total FROM brahma_remedy_corpus WHERE 1=1
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_remedy_corpus.ts:92-108',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
      'platform/supabase/migrations/608_nirmana_bg_remedies_integrity_contract.sql:38-78',
    ],
  },
  {
    contract_id: 'source-query:query-sky-calendar:v1',
    descriptor_name: 'query_sky_calendar',
    capability_uri: 'marsys://tool/L0/query_sky_calendar',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT event_type, primary_body, secondary_body, event_datetime_utc, sign, nakshatra,
                 longitude_deg, speed_dps, detail, ayanamsha_key, sampling_method, source_citation
            FROM bg_sky_calendar
           WHERE event_datetime_utc >= NULL::timestamptz
             AND event_datetime_utc < NULL::timestamptz
           ORDER BY event_datetime_utc, event_type, primary_body
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts:98-121',
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts:141-156',
      'platform/supabase/migrations/628_nirmana_l0_wave0_remaining_integrity_contracts.sql:29-62',
    ],
  },
  {
    contract_id: 'source-query:query-transit-vedha:v1',
    descriptor_name: 'query_transit_vedha',
    capability_uri: 'marsys://tool/L0/query_transit_vedha',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT primary_graha, primary_transit_house, vedha_graha, vedha_house, vedha_type,
                 classical_note, classical_citation
            FROM bg_transit_vedha
           WHERE 1=1
           ORDER BY primary_graha, primary_transit_house
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_vedha.ts:81-112',
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_vedha.ts:107-112',
    ],
  },
  {
    contract_id: 'source-query:get-kp-cusps:v1',
    descriptor_name: 'get_kp_cusps',
    capability_uri: 'marsys://tool/L1/get_kp_cusps',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_subject, fact_key,
                 fact_value_text, fact_value_num, fact_value_jsonb
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND ayanamsha_id = 'krishnamurti'
             AND fact_category = ANY(ARRAY[
               'cusp_kp_lords', 'kp_cuspal_significators', 'bhava_cusps',
               'kp_ruling_planets_natal'
             ]::text[])
           ORDER BY fact_category, fact_subject, fact_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts:122-141',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-nakshatra:v1',
    descriptor_name: 'get_nakshatra',
    capability_uri: 'marsys://tool/L1/get_nakshatra',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'graha_nakshatra_join', 'graha_pada_join', 'graha_kp_lords',
               'cusp_kp_lords', 'graha_gandanta', 'graha_degree_flags', 'nakshatra_dispositor',
               'nakshatra_exchange', 'nakshatra_conjunction', 'nakshatra_cogravity',
               'graha_tara_bala', 'nakshatra_statistics', 'nakshatra_cross_ayanamsha',
               'kp_house_significators', 'kp_planet_significations'
             ]::text[])
           ORDER BY fact_category, ayanamsha_id, fact_subject, fact_key
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_nakshatra.ts:76-115',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-sensitive-points:v1',
    descriptor_name: 'get_sensitive_points',
    capability_uri: 'marsys://tool/L1/get_sensitive_points',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, formula_id, formula_provenance_text,
                 verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'esoteric_point_avayogi', 'esoteric_point_bhrigu_bindu', 'esoteric_point_brahma',
               'esoteric_point_chatushphuta', 'esoteric_point_mrityu', 'esoteric_point_panchasphuta',
               'esoteric_point_pranapada_sphuta', 'esoteric_point_shiva',
               'esoteric_point_sphuta_fertility', 'esoteric_point_sri_yantra_position',
               'esoteric_point_trikona_dasha_sphuta', 'esoteric_point_trisphuta',
               'esoteric_point_vishnu', 'esoteric_point_yogi', 'esoteric_point_yogi_system',
               'bhrigu_nadi_point', 'lal_kitab_special_point', 'maharsi_specific_point', 'midpoint',
               'saham_position', 'saturn_derived_point', 'nakshatra_pada_sensitive'
             ]::text[])
           ORDER BY fact_category, ayanamsha_id, fact_key, formula_id
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_points.ts:90-124',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-sade-sati:v1',
    descriptor_name: 'get_sade_sati',
    capability_uri: 'marsys://tool/L1/get_sade_sati',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter',
               'sade_sati_modifier_overlay', 'sade_sati_cancellation_check',
               'sade_sati_concurrent_dasha_overlay', 'sade_sati_downstream_cross_reference',
               'sade_sati_saturn_retrograde_subset', 'janma_shani_period',
               'anumukha_shani_period', 'ardha_ashtama_shani_period', 'ashtama_shani_period',
               'dhaiya_period', 'vishakha_shani_period', 'kantaka_shani_period'
             ]::text[])
           ORDER BY fact_category, ayanamsha_id, fact_key, fact_subject, fact_id
           LIMIT 0 OFFSET 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_sade_sati.ts:77-118',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-tajik:v1',
    descriptor_name: 'get_tajik',
    capability_uri: 'marsys://tool/L1/get_tajik',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH chart_facts_probe AS (
            SELECT fact_id
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'tajik_hadda_lord', 'tajik_triraashipathi', 'tajik_vargottama_specific'
               ]::text[])
             LIMIT 0
          ), varsha_probe AS (
            SELECT chart_id
              FROM l1_tajik_varsha_year_lords
             WHERE chart_id = $1::uuid
             LIMIT 0
          ), birth_date_probe AS (
            SELECT id
              FROM charts
             WHERE id = $1::uuid
             LIMIT 0
          )
          SELECT 1
            FROM chart_facts_probe
            CROSS JOIN varsha_probe
            CROSS JOIN birth_date_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_tajik.ts:123-218',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-chart-header:v1',
    descriptor_name: 'get_chart_header',
    capability_uri: 'marsys://tool/L1/get_chart_header',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH name_probe AS (
            SELECT name
              FROM charts
             WHERE chart_id = $1::uuid OR id = $1::uuid
             LIMIT 0
          ), position_probe AS (
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND fact_category = 'graha_position'
               AND fact_subject IN ('LAGNA', 'MOON', 'SUN')
               AND fact_key IN ('sign', 'longitude_sidereal')
             LIMIT 0
          ), dasha_probe AS (
            SELECT lord_graha, level_n
              FROM chart_dashas
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND system_id = 'vimshottari'
               AND level_n IN (1, 2)
               AND start_date <= CURRENT_DATE
               AND end_date >= CURRENT_DATE
             ORDER BY level_n
             LIMIT 0
          )
          SELECT 1
            FROM name_probe
            CROSS JOIN position_probe
            CROSS JOIN dasha_probe`,
    source_refs: [
      'platform/src/lib/retrieval/chart_header.ts:72-94',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_chart_header.ts:54-55',
      'platform/supabase/migrations/0001_brahma_baseline.sql:1579-1607',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/supabase/migrations/206_ga3_supporting_tables.sql:36-68',
    ],
  },
  {
    contract_id: 'source-query:get-graha-yuddha:v1',
    descriptor_name: 'get_graha_yuddha',
    capability_uri: 'marsys://tool/L1/get_graha_yuddha',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH floor_facts_probe AS (
            SELECT fact_id, fact_subject, fact_key, ayanamsha_id, fact_value_jsonb
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = 'graha_yuddha'
             ORDER BY ayanamsha_id, fact_subject, fact_key
             LIMIT 0
          ), birth_date_probe AS (
            SELECT birth_date
              FROM charts
             WHERE id = $1::uuid
             LIMIT 0
          ), latitude_probe AS (
            SELECT e.body, e.latitude
              FROM charts c
              JOIN ephemeris_daily e ON e.date = c.birth_date
             WHERE c.id = $1::uuid
               AND e.ayanamsha_id = 'tropical'
             LIMIT 0
          )
          SELECT 1
            FROM floor_facts_probe
            CROSS JOIN birth_date_probe
            CROSS JOIN latitude_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_graha_yuddha.ts:165-218',
      'platform/supabase/migrations/0001_brahma_baseline.sql:1579-1607',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/migrations/ws2_l0_ephemeris.sql:18-45',
    ],
  },
  {
    contract_id: 'source-query:get-panchanga:v1',
    descriptor_name: 'get_panchanga',
    capability_uri: 'marsys://tool/L1/get_panchanga',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'panchanga_abhijit_muhurta', 'panchanga_agni_vasa', 'panchanga_brahma_muhurta',
                 'panchanga_calendrical', 'panchanga_choghadiya_birth', 'panchanga_disha_shul',
                 'panchanga_durmuhurta', 'panchanga_godhuli_muhurta', 'panchanga_gulika_kalam',
                 'panchanga_hora_birth', 'panchanga_karana', 'panchanga_krakaca',
                 'panchanga_madhyahna_sandhya', 'panchanga_nakshatra_moon', 'panchanga_nakshatra_shoonya_rashi',
                 'panchanga_nishita_kala', 'panchanga_panchaka_classification', 'panchanga_pratah_sandhya',
                 'panchanga_rahu_kalam', 'panchanga_sashtighati', 'panchanga_sayam_sandhya',
                 'panchanga_solar_context', 'panchanga_special_yoga_combinations', 'panchanga_sun_moon_dynamics',
                 'panchanga_tithi', 'panchanga_tithi_shoonya_rashi', 'panchanga_vara',
                 'panchanga_varjyam', 'panchanga_vijaya_muhurta', 'panchanga_visha_ghati',
                 'panchanga_yamaganda_kalam', 'panchanga_yamakantaka', 'panchanga_yoga'
               ]::text[])
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'panchanga_abhijit_muhurta', 'panchanga_agni_vasa', 'panchanga_brahma_muhurta',
                 'panchanga_calendrical', 'panchanga_choghadiya_birth', 'panchanga_disha_shul',
                 'panchanga_durmuhurta', 'panchanga_godhuli_muhurta', 'panchanga_gulika_kalam',
                 'panchanga_hora_birth', 'panchanga_karana', 'panchanga_krakaca',
                 'panchanga_madhyahna_sandhya', 'panchanga_nakshatra_moon', 'panchanga_nakshatra_shoonya_rashi',
                 'panchanga_nishita_kala', 'panchanga_panchaka_classification', 'panchanga_pratah_sandhya',
                 'panchanga_rahu_kalam', 'panchanga_sashtighati', 'panchanga_sayam_sandhya',
                 'panchanga_solar_context', 'panchanga_special_yoga_combinations', 'panchanga_sun_moon_dynamics',
                 'panchanga_tithi', 'panchanga_tithi_shoonya_rashi', 'panchanga_vara',
                 'panchanga_varjyam', 'panchanga_vijaya_muhurta', 'panchanga_visha_ghati',
                 'panchanga_yamaganda_kalam', 'panchanga_yamakantaka', 'panchanga_yoga'
               ]::text[])
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page
            CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_panchanga.ts:13-27',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_panchanga.ts:128-158',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-dasha-lord-capability:v1',
    descriptor_name: 'get_dasha_lord_capability',
    capability_uri: 'marsys://tool/L1/get_dasha_lord_capability',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH dasha_lords_probe AS (
            SELECT DISTINCT lord_graha
              FROM chart_dashas
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND system_id = 'vimshottari'
               AND level_n = 1
             LIMIT 0
          ), shadbala_probe AS (
            SELECT fact_id, fact_subject, fact_value_num AS rupa
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND fact_category = 'graha_shadbala_total'
               AND fact_key = 'rupa'
             LIMIT 0
          ), valence_probe AS (
            SELECT subject, value_jsonb, constituent_fact_ids
              FROM chart_vichara
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND varga = 'D1'
               AND vichara_family = 'valence_pass'
             LIMIT 0
          ), ratification_probe AS (
            SELECT subject, ratification_factor, domain
              FROM chart_vichara
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND vichara_family = 'varga_ratification'
               AND ratification_factor IS NOT NULL
             LIMIT 0
          )
          SELECT 1
            FROM dasha_lords_probe
            CROSS JOIN shadbala_probe
            CROSS JOIN valence_probe
            CROSS JOIN ratification_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts:166-209',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/supabase/migrations/206_ga3_supporting_tables.sql:36-68',
      'platform/migrations/435_ga_vichara.sql:44-83',
    ],
  },
  {
    contract_id: 'source-query:get-medical-indications:v1',
    descriptor_name: 'get_medical_indications',
    capability_uri: 'marsys://tool/L1/get_medical_indications',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT id, graha, ayanamsha_id, natal_sign, natal_nakshatra, indication_strength,
                   dosha_aggravated, organ_watch, body_part_watch, nakshatra_body_part,
                   indication_tier, not_diagnosis, classical_citation
              FROM ga_medical
             WHERE chart_id = $1::uuid
             ORDER BY graha, ayanamsha_id
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM ga_medical
             WHERE chart_id = $1::uuid
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page
            CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_medical_indications.ts:76-95',
      'platform/migrations/279_ga_medical.sql:21-55',
    ],
  },
  {
    contract_id: 'source-query:get-vastu-directions:v1',
    descriptor_name: 'get_vastu_directions',
    capability_uri: 'marsys://tool/L1/get_vastu_directions',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT m.id, m.graha, m.ayanamsha_id, m.direction, m.condition_score, m.dignity_d1,
                   m.direction_impact, m.indication_tier, m.classical_citation,
                   COALESCE(r.direction_remedies, '[]'::jsonb) AS direction_remedies
              FROM ga_vastu_planet_direction_map m
              LEFT JOIN LATERAL (
                SELECT jsonb_agg(
                         jsonb_build_object(
                           'remedy_type', remedy_type,
                           'remedy_description', remedy_description,
                           'classical_citation', classical_citation
                         ) ORDER BY remedy_type
                       ) AS direction_remedies
                  FROM bg_vastu_direction_remedials
                 WHERE direction = m.direction
              ) r ON true
             WHERE m.chart_id = $1::uuid
             ORDER BY m.graha, m.ayanamsha_id
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM ga_vastu_planet_direction_map m
             WHERE m.chart_id = $1::uuid
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page
            CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_vastu_directions.ts:91-117',
      'platform/migrations/284_bg_vastu_directions.sql:37-66',
      'platform/migrations/286_ga_vastu_planet_direction_map.sql:8-38',
    ],
  },
  {
    contract_id: 'source-query:get-transit-anchors:v1',
    descriptor_name: 'get_transit_anchors',
    capability_uri: 'marsys://tool/L1/get_transit_anchors',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH anchors_probe AS (
            SELECT id, chart_id, ayanamsha_id, graha,
                   natal_sign, natal_house_from_moon, natal_degree_absolute, computed_at
              FROM ga_transit_anchors
             WHERE chart_id = $1::uuid
             ORDER BY ayanamsha_id, graha
             LIMIT 0
          ), constituent_facts_probe AS (
            SELECT ayanamsha_id, fact_subject, fact_id
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY['graha_position', 'graha_sign_attributes']::text[])
               AND fact_key = ANY(ARRAY['sign', 'longitude_sidereal', 'nakshatra']::text[])
             LIMIT 0
          )
          SELECT 1
            FROM anchors_probe
            CROSS JOIN constituent_facts_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_transit_anchors.ts:67-109',
      'platform/migrations/267_ga_transit_anchors.sql:20-49',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:chart-snapshot:v1',
    descriptor_name: 'chart_snapshot',
    capability_uri: 'marsys://tool/L1/chart_snapshot',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT DISTINCT ON (varga, graha) varga, graha, sign, degree_in_sign, id
            FROM chart_divisionals
           WHERE chart_id = $1::uuid
             AND ayanamsha_id = 'lahiri_chitrapaksha'
             AND fact_category = 'varga_position'
             AND varga = ANY(ARRAY['D1']::text[])
             AND graha <> 'ALL'
           ORDER BY varga, graha
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_chart_snapshot.ts:205-215',
      'platform/migrations/002_ganita_divisionals.sql:31-65',
    ],
  },
  {
    contract_id: 'source-query:get-vichara:v1',
    descriptor_name: 'get_vichara',
    capability_uri: 'marsys://tool/L1/get_vichara',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT id, chart_id, ayanamsha_id, build_id, vichara_family, subject, domain, varga_id,
                   value_num, value_text, value_jsonb, constituent_fact_ids, formula_version,
                   source_citation, computed_at
              FROM chart_vichara
             WHERE chart_id = $1::uuid
             ORDER BY vichara_family, domain NULLS FIRST, subject, ayanamsha_id, varga_id NULLS FIRST, id
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM chart_vichara
             WHERE chart_id = $1::uuid
          ), family_counts_probe AS (
            SELECT vichara_family, COUNT(*)::text AS n
              FROM chart_vichara
             WHERE chart_id = $1::uuid
             GROUP BY vichara_family
             LIMIT 0
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page
            CROSS JOIN handler_count
            CROSS JOIN family_counts_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_vichara.ts:151-176',
      'platform/migrations/435_ga_vichara.sql:44-83',
    ],
  },
  {
    contract_id: 'source-query:get-structural:v1',
    descriptor_name: 'get_structural',
    capability_uri: 'marsys://tool/L1/get_structural',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'sambandha_grade', 'virupa_drishti', 'contradiction_pair', 'conjunction_special_point',
               'nakshatra_dispositor_chain', 'nakshatra_lord_relationship', 'nakshatra_co_tenancy',
               'graha_centrality', 'chart_cluster', 'chart_center_of_gravity', 'significator_path',
               'aspect_received_by_special_point', 'nway_config_per_varga', 'graha_yuddha_per_varga',
               'kendradhipati_dosha', 'bhava_significance_link', 'net_argala_per_varga', 'panchadha_maitri',
               'tara_bala'
             ]::text[])
           ORDER BY fact_category, ayanamsha_id, fact_subject, fact_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_structural_signals.ts:72-89',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_structural_signals.ts:151-171',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-yoga-dosha:v1',
    descriptor_name: 'get_yoga_dosha',
    capability_uri: 'marsys://tool/L1/get_yoga_dosha',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag'
               ]::text[])
               AND NOT (fact_category = 'dosha_label' AND (fact_value_jsonb->>'fire_reason') = 'requires_pass')
             ORDER BY fact_category, ayanamsha_id, fact_key
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = ANY(ARRAY[
                 'yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag'
               ]::text[])
          ), firings_probe AS (
            SELECT COUNT(*)::text AS total
              FROM ga_yoga_firings
             WHERE chart_id = $1::uuid
               AND fired = true
          ), kala_sarpa_probe AS (
            SELECT fact_id, ayanamsha_id, fact_value_jsonb, fact_value_text,
                   verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND fact_category = 'kala_sarpa_per_varga'
               AND fact_key = 'ks_detection'
             ORDER BY ayanamsha_id, (fact_value_jsonb->>'varga')
             LIMIT 0
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page
            CROSS JOIN firings_probe
            CROSS JOIN kala_sarpa_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts:5-6',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts:107-174',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts:206-218',
      'platform/migrations/240_ga_yoga.sql:4-48',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-ashtakavarga:v1',
    descriptor_name: 'get_ashtakavarga',
    capability_uri: 'marsys://tool/L1/get_ashtakavarga',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = ANY(ARRAY[
               'ashtakavarga_bindu', 'ashtakavarga_anubindu', 'ashtakavarga_bindu_sign',
               'ashtakavarga_pinda_bhinna', 'ashtakavarga_pinda_sarva', 'ashtakavarga_pinda_sodhita',
               'ashtakavarga_pinda_raasi', 'ashtakavarga_trikona_shodhana',
               'ashtakavarga_ekadhipathya_shodhana', 'ashtakavarga_kakshya_boundary',
               'ashtakavarga_bindu_per_varga', 'ashtakavarga_pinda_sarva_per_varga'
             ]::text[])
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_ashtakavarga.ts:27-42',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_ashtakavarga.ts:118-140',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-divisionals:v1',
    descriptor_name: 'get_divisionals',
    capability_uri: 'marsys://tool/L1/get_divisionals',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT * FROM chart_divisionals
             WHERE chart_id = $1::uuid
             ORDER BY varga, ayanamsha_id, graha, fact_category, fact_key
             LIMIT 0
          ), own_varga_lagna_probe AS (
            SELECT varga, ayanamsha_id, sign
              FROM chart_divisionals
             WHERE chart_id = $1::uuid
               AND graha = 'Lagna'
               AND formula_provenance_text = 'whole_sign'
             LIMIT 0
          )
          SELECT 1 FROM handler_page CROSS JOIN own_varga_lagna_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_divisionals.ts:80-101',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_divisionals.ts:112-120',
      'platform/migrations/002_ganita_divisionals.sql:31-65',
    ],
  },
  {
    contract_id: 'source-query:get-positions:v1',
    descriptor_name: 'get_positions',
    capability_uri: 'marsys://tool/L1/get_positions',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
            FROM chart_facts
           WHERE chart_id = $1::uuid
             AND fact_category = 'graha_position'
           ORDER BY ayanamsha_id,
                    CASE fact_category WHEN 'graha_position' THEN 0 WHEN 'upagraha_position' THEN 1
                                       WHEN 'aprakasha_position' THEN 2 ELSE 3 END,
                    fact_category, fact_key
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts:163-190',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts:218-228',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-yoga-firings:v1',
    descriptor_name: 'get_yoga_firings',
    capability_uri: 'marsys://tool/L1/get_yoga_firings',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT f.id, f.yoga_canonical_id, f.ayanamsha_id, f.fired, f.strength,
                   c.classical_citations AS catalog_classical_citations
              FROM ga_yoga_firings f
              LEFT JOIN brahma_yoga_catalog c ON c.canonical_id = f.yoga_canonical_id
             WHERE f.chart_id = $1::uuid
               AND f.fired = true
             ORDER BY f.strength DESC NULLS LAST, f.yoga_canonical_id, f.ayanamsha_id, f.id
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM ga_yoga_firings f
             WHERE f.chart_id = $1::uuid
               AND f.fired = true
          )
          SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_firings.ts:171-179',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_firings.ts:200-213',
      'platform/migrations/240_ga_yoga.sql:4-48',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-dashas:v1',
    descriptor_name: 'get_dashas',
    capability_uri: 'marsys://tool/L1/get_dashas',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH eligible_receipt AS (
            SELECT receipt.build_id::text AS build_id
              FROM asset_provenance_receipts receipt
              JOIN asset_freshness freshness
                ON freshness.asset_id = receipt.asset_id
               AND freshness.scope_key = receipt.scope_key
               AND freshness.partition_key = receipt.partition_key
               AND freshness.receipt_version = receipt.receipt_version
              JOIN build_runs receipt_run ON receipt_run.id = receipt.build_id
             WHERE receipt.asset_id = 'ga_dashas'
               AND receipt.chart_id = $1::uuid
               AND receipt.receipt_state = 'proven'
               AND receipt.output_digest_spec_sha256 = '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14'
               AND freshness.freshness_state = 'fresh'
               AND receipt_run.chart_id = $1::uuid
               AND receipt_run.state = 'completed'
             ORDER BY receipt.observed_at DESC
             LIMIT 1
          ), handler_page AS (
            SELECT d.dasha_row_id, d.system_id, d.ayanamsha_id, d.start_date, d.level_n, d.start_iso
              FROM chart_dashas d
              JOIN eligible_receipt eligible ON d.build_id = eligible.build_id::uuid
             WHERE d.chart_id = $1::uuid
               AND d.ayanamsha_id = 'lahiri_chitrapaksha'
               AND d.system_id = 'vimshottari'
             ORDER BY d.system_id, d.ayanamsha_id, d.start_date, d.level_n, d.start_iso, d.dasha_row_id
             LIMIT 0
          ), level_probe AS (
            SELECT MAX(level_n)::int AS max_level
              FROM chart_dashas
             WHERE chart_id = $1::uuid
             LIMIT 0
          )
          SELECT 1 FROM handler_page CROSS JOIN level_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:600-724',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:946-962',
      'platform/migrations/003_ganita_dashas.sql:1-80',
    ],
  },
  {
    contract_id: 'source-query:concept-locate:v1',
    descriptor_name: 'concept_locate',
    capability_uri: 'marsys://tool/L1/concept_locate',
    scope: 'global',
    parameter_binding: 'global_with_chart_fallback',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT DISTINCT fact_category
            FROM chart_facts
           WHERE chart_id = $1::uuid
           ORDER BY fact_category
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/concept_locate.ts:34-41',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/concept_locate.ts:89-116',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:chart-facts-query:v1',
    descriptor_name: 'chart_facts_query',
    capability_uri: 'marsys://tool/L1/chart_facts_query',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH fact_page_probe AS (
            SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_num,
                   fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
              FROM chart_facts
             WHERE chart_id = $1::uuid
               AND ayanamsha_id IN ('lahiri_chitrapaksha', 'INVARIANT')
             ORDER BY fact_category, fact_subject, fact_key
             LIMIT 0
          ), divisional_page_probe AS (
            SELECT id, chart_id, ayanamsha_id, varga, graha, sign, house, fact_category, fact_key
              FROM chart_divisionals
             WHERE chart_id = $1::uuid
               AND ayanamsha_id = 'lahiri_chitrapaksha'
             ORDER BY varga, graha, fact_category, fact_key
             LIMIT 0
          )
          SELECT 1 FROM fact_page_probe CROSS JOIN divisional_page_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:770-829',
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:972-1008',
      'platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1128-1189',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
      'platform/migrations/002_ganita_divisionals.sql:31-65',
    ],
  },
  {
    contract_id: 'source-query:get-database-schema:v1',
    descriptor_name: 'get_database_schema',
    capability_uri: 'marsys://tool/L1/get_database_schema',
    scope: 'global',
    parameter_binding: 'global_with_chart_fallback',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT fact_category, fact_subject,
                 array_agg(DISTINCT fact_key ORDER BY fact_key) AS fact_keys,
                 count(*)::text AS row_count,
                 (array_agg(fact_id ORDER BY fact_id))[1:3] AS sample_fact_ids
            FROM chart_facts
           WHERE chart_id = $1::uuid
           GROUP BY fact_category, fact_subject
           ORDER BY fact_category, fact_subject
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_database_schema.ts:79-105',
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_database_schema.ts:151-190',
      'platform/supabase/migrations/204_chart_facts.sql:10-29',
    ],
  },
  {
    contract_id: 'source-query:get-prashna-lagna:v1',
    descriptor_name: 'get_prashna_lagna',
    capability_uri: 'marsys://tool/L1/get_prashna_lagna',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT chart_id, ayanamsha_id, lagna_method, lagna_rashi, lagna_degree, kp_sub_lord,
                   is_primary, classical_citation
              FROM ga_prashna_lagna
             WHERE chart_id = $1::uuid
             ORDER BY ayanamsha_id, lagna_method
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM ga_prashna_lagna
             WHERE chart_id = $1::uuid
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L1_ganita/get_prashna_lagna.ts:70-95',
      'platform/migrations/289_ga_prashna_lagna.sql',
    ],
  },
  {
    contract_id: 'source-query:list-remedies-by-category:v1',
    descriptor_name: 'list_remedies_by_category',
    capability_uri: 'marsys://tool/L0/list_remedies_by_category',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT remedy_id, planet, domain, category, deity, prescription_text, mantra_text,
                 mantra_sanskrit, cost_tier, source_canonical_id, classical_attestation_text
            FROM brahma_remedy_corpus
           WHERE is_active = TRUE
             AND category = NULL::text
           ORDER BY planet, remedy_id
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieve/remedy_tools.ts:180-200',
      'platform/migrations/ws2_l0_remedy_corpus.sql:16-33',
    ],
  },
  {
    contract_id: 'source-query:asset-registry-all:v1',
    descriptor_name: 'asset_registry_all',
    capability_uri: 'marsys://resource/asset-registry/all',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT asset_id, layer, sanskrit_name, english_name, target_table, target_floor,
                 scope, is_active, asset_type, catalog_status, has_writer,
                 expected_volume_formula, count_sql, depends_on
            FROM asset_registry
           ORDER BY layer, asset_id
           LIMIT 0`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L0_brahmagyan/asset_registry_all.ts:145-162'],
  },
  {
    contract_id: 'source-query:asset-registry-l0:v1',
    descriptor_name: 'asset_registry_l0',
    capability_uri: 'marsys://resource/asset-registry/L0',
    scope: 'global',
    parameter_binding: 'global',
    empty_semantics: 'query_success_is_available',
    sql: `SELECT ar.asset_id, ar.layer, ar.sanskrit_name, ar.english_name, ar.target_table,
                 ar.target_floor, ar.scope, ar.is_active, ar.asset_type, ar.catalog_status,
                 ar.has_writer, ar.expected_volume_formula, ar.count_sql, ar.depends_on
            FROM asset_registry ar
           WHERE ar.layer = 'brahmagyan'
           ORDER BY ar.asset_id
           LIMIT 0`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L0_brahmagyan/asset_registry_l0.ts:103-120'],
  },
  {
    contract_id: 'source-query:query-pratijna:v1',
    descriptor_name: 'query_pratijna',
    capability_uri: 'marsys://tool/L2/query_pratijna',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT pratijna_id, ayanamsha_id, event_class_id, status, grade,
                   varga_confirmation, supporting_signal_ids, contradicting_signal_ids,
                   derivation, formula_version,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_pratijna
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR status = NULL::text)
               AND (NULL::text IS NULL OR event_class_id = NULL::text)
             ORDER BY event_class_id, ayanamsha_id
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM bodha_pratijna
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR status = NULL::text)
               AND (NULL::text IS NULL OR event_class_id = NULL::text)
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_pratijna.ts:155-177',
      'platform/migrations/665_bo_pratijna_integrity_check.sql:10-91',
    ],
  },
  {
    contract_id: 'source-query:query-cdlm-summary:v1',
    descriptor_name: 'query_cdlm_summary',
    capability_uri: 'marsys://tool/L2/query_cdlm_summary',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH chart_summary_page AS (
            SELECT summary_id, ayanamsha_id, snapshot_type, chart_typology_class,
                   total_chart_linkage, contradiction_density, dominant_3_domains_array,
                   weakest_3_domains_array, bridge_link_count, asymmetric_link_count,
                   house_to_domain_strength_jsonb, karaka_to_domain_strength_jsonb,
                   pattern_cluster_markers_jsonb, verification_pass_status, citation_ref, citation_human
              FROM bodha_cdlm_chart_summary
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY ayanamsha_id
             LIMIT 0
          ), domain_rollups_page AS (
            SELECT rollup_id, ayanamsha_id, snapshot_type, domain, total_inbound_linkage,
                   total_outbound_linkage, diagonal_density, signal_count_for_domain,
                   top_3_linked_domains_jsonb, contradiction_density,
                   pattern_markers_for_domain_array, verification_pass_status, citation_ref, citation_human
              FROM bodha_cdlm_domain_rollups
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR domain = NULL::text)
             ORDER BY ayanamsha_id, domain
             LIMIT 0
          ), pattern_clusters_page AS (
            SELECT pattern_id, ayanamsha_id, snapshot_type, pattern_marker_type,
                   involved_domains_array, cluster_strength_total, involved_cells_array,
                   involved_signals_array, contradicts_other_patterns_array, remedy_theme_jsonb,
                   classical_archetype_match, predicted_outcome_class, active_dasha_windows_jsonb,
                   verification_pass_status, citation_ref, citation_human
              FROM bodha_cdlm_pattern_clusters
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY cluster_strength_total DESC NULLS LAST
             LIMIT 0
          ), evolution_gradients_page AS (
            SELECT gradient_id, ayanamsha_id, dynamic_system_id, domain_row, domain_col,
                   evolution_class, gradient_score, trend_iso_window_array, peak_period_lord,
                   peak_period_iso, trough_period_iso, predicted_next_peak_iso,
                   verification_pass_status, citation_ref, citation_human
              FROM bodha_cdlm_evolution_gradients
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
             ORDER BY ayanamsha_id, domain_row, domain_col
             LIMIT 0
          )
          SELECT 1
            FROM chart_summary_page
            CROSS JOIN domain_rollups_page
            CROSS JOIN pattern_clusters_page
            CROSS JOIN evolution_gradients_page`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_cdlm_summary.ts:32-73',
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_cdlm_summary.ts:182-201',
      'platform/migrations/986_nirmana_l2_bo_cdlm_summary_output_digest_spec.sql:10-86',
    ],
  },
  {
    contract_id: 'source-query:query-cgm-motifs:v1',
    descriptor_name: 'query_cgm_motifs',
    capability_uri: 'marsys://tool/L2/query_cgm_motifs',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT motif_id, ayanamsha_id, snapshot_type, motif_name, motif_class,
                   involved_node_ids_array, involved_edge_ids_array, motif_strength,
                   classical_citation_id, verification_pass_status, citation_ref, citation_human
              FROM bodha_cgm_motifs
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR motif_class = NULL::text)
             ORDER BY motif_strength DESC NULLS LAST, motif_name
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM bodha_cgm_motifs
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR motif_class = NULL::text)
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_cgm_motifs.ts:67-84',
      'platform/migrations/1000_nirmana_l2_bo_cgm_motifs_output_digest_spec.sql:1-80',
    ],
  },
  {
    contract_id: 'source-query:query-cgm-paths:v1',
    descriptor_name: 'query_cgm_paths',
    capability_uri: 'marsys://tool/L2/query_cgm_paths',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT path_id, ayanamsha_id, snapshot_type, path_type, from_node_id, to_node_id,
                   path_node_ids_array, path_edge_ids_array, path_length, path_strength,
                   is_final_dispositor, convergence_count, path_label_human,
                   verification_pass_status, citation_ref, citation_human
              FROM bodha_cgm_paths
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR path_type = NULL::text)
             ORDER BY path_strength DESC NULLS LAST, path_length
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM bodha_cgm_paths
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR path_type = NULL::text)
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_cgm_paths.ts:66-83',
      'platform/migrations/982_nirmana_l2_bo_cgm_paths_output_digest_spec.sql:1-80',
    ],
  },
  {
    contract_id: 'source-query:query-question-lenses:v1',
    descriptor_name: 'query_question_lenses',
    capability_uri: 'marsys://tool/L2/query_question_lenses',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT lens_id, ayanamsha_id, question_type,
                   template_element_ids_jsonb, wildcard_element_ids_jsonb,
                   points_only_assertion, verification_pass_status,
                   lens_template_version, lens_formula_version, citation_ref,
                   COALESCE(
                     NULLIF(all_relevant_ranked_jsonb->>'total_count','')::int,
                     CASE WHEN jsonb_typeof(all_relevant_ranked_jsonb->'ranked_signals') = 'array'
                          THEN jsonb_array_length(all_relevant_ranked_jsonb->'ranked_signals') END,
                     CASE WHEN jsonb_typeof(all_relevant_ranked_jsonb) = 'array'
                          THEN jsonb_array_length(all_relevant_ranked_jsonb) END,
                     0
                   ) AS ranked_signal_count,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_question_lenses
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR question_type = NULL::text)
             ORDER BY question_type, ayanamsha_id
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total
              FROM bodha_question_lenses
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR question_type = NULL::text)
          )
          SELECT handler_page.*, handler_count.total
            FROM handler_page CROSS JOIN handler_count`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_question_lenses.ts:84-117',
      'platform/migrations/941_nirmana_l2_bo_drishti_output_digest_spec.sql:1-80',
    ],
  },
  {
    contract_id: 'source-query:query-rm-chart-summary:v1',
    descriptor_name: 'query_rm_chart_summary',
    capability_uri: 'marsys://tool/L2/query_rm_chart_summary',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT summary_id, ayanamsha_id, snapshot_type, top_3_resonance_targets_jsonb,
                   top_10_priority_prescriptions_jsonb, recommended_intensity_class,
                   recommended_remedy_phase_sequence_jsonb, total_active_dosha_count,
                   primary_dosha_class, cross_tradition_convergence_jsonb, remedy_chart_typology,
                   acharya_review_required_count, feasibility_assessment_jsonb,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_chart_summary
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR snapshot_type = NULL::text)
             ORDER BY computed_at DESC
             LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_chart_summary
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR snapshot_type = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_chart_summary.ts:62-88'],
  },
  {
    contract_id: 'source-query:query-rm-resonances:v1',
    descriptor_name: 'query_rm_resonances',
    capability_uri: 'marsys://tool/L2/query_rm_resonances',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT resonance_id, ayanamsha_id, graha, resonance_score, weakness_score,
                   contradiction_factor, domain_burden, motif_burden, is_yoga_karaka_flag,
                   is_chara_karaka_role, weakest_rank_in_chart, remedy_priority_class,
                   associated_doshas_array, associated_motifs_array, associated_cdlm_cells_array,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_resonances
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR graha = NULL::text)
             ORDER BY resonance_score DESC NULLS LAST, weakness_score DESC NULLS LAST
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_resonances
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR graha = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_resonances.ts:57-82'],
  },
  {
    contract_id: 'source-query:query-rm-prescriptions:v1',
    descriptor_name: 'query_rm_prescriptions',
    capability_uri: 'marsys://tool/L2/query_rm_prescriptions',
    scope: 'chart',
    parameter_binding: 'chart_with_active_build_context',
    empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT prescription_id, ayanamsha_id, target_graha, target_resonance_id,
                   tradition, sub_tradition, remedy_category, remedy_id_g27, remedy_label_human,
                   classical_strength_rating, classical_sources_jsonb, resonance_match_score,
                   feasibility_score, ritual_complexity_class, requires_acharya_review_flag,
                   acharya_review_reason_array, counter_indications_array, targets_motif_id,
                   targets_cell_id, targets_dosha_class, cross_tradition_corroboration_count,
                   phase_sequence_class, phase_duration_days, recommended_facing_direction,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_remedy_prescriptions
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR tradition = NULL::text)
               AND (NULL::text IS NULL OR remedy_category = NULL::text)
               AND (NULL::text IS NULL OR target_graha = NULL::text)
             ORDER BY resonance_match_score DESC NULLS LAST, classical_strength_rating DESC NULLS LAST
             LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_remedy_prescriptions
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR tradition = NULL::text)
               AND (NULL::text IS NULL OR remedy_category = NULL::text)
               AND (NULL::text IS NULL OR target_graha = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_prescriptions.ts:65-91'],
  },
  {
    contract_id: 'source-query:query-rm-dasha-windowed-prescriptions:v1',
    descriptor_name: 'query_rm_dasha_windowed_prescriptions',
    capability_uri: 'marsys://tool/L2/query_rm_dasha_windowed_prescriptions',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT window_prescription_id, ayanamsha_id, base_prescription_id, dasha_system,
                   dasha_level, dasha_lord, window_start_iso, window_end_iso,
                   window_intensity_multiplier, schedule_jsonb, phase_within_window,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_dasha_windowed_prescriptions
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR dasha_system = NULL::text)
               AND (NULL::text IS NULL OR dasha_lord = NULL::text)
             ORDER BY window_start_iso LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_dasha_windowed_prescriptions
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR dasha_system = NULL::text)
               AND (NULL::text IS NULL OR dasha_lord = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_dasha_windowed_prescriptions.ts:74-102'],
  },
  {
    contract_id: 'source-query:query-rm-dosha-remedy-bundles:v1',
    descriptor_name: 'query_rm_dosha_remedy_bundles',
    capability_uri: 'marsys://tool/L2/query_rm_dosha_remedy_bundles',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT bundle_id, ayanamsha_id, dosha_class, active_flag, intensity_score,
                   cancellation_count, prescription_ids_in_bundle_array, bundle_summary_jsonb,
                   classical_source_citation_id, active_dasha_windows_jsonb,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_dosha_remedy_bundles
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR dosha_class = NULL::text)
             ORDER BY intensity_score DESC NULLS LAST LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_dosha_remedy_bundles
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR dosha_class = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_dosha_remedy_bundles.ts:68-96'],
  },
  {
    contract_id: 'source-query:query-rm-pattern-remedies:v1',
    descriptor_name: 'query_rm_pattern_remedies',
    capability_uri: 'marsys://tool/L2/query_rm_pattern_remedies',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT pattern_remedy_id, ayanamsha_id, source_kind, source_id, remedy_theme,
                   prescription_ids_array, theme_strength, cross_tradition_unanimity_score,
                   verification_pass_status, citation_ref, citation_human,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_rm_pattern_remedies
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR source_kind = NULL::text)
             ORDER BY theme_strength DESC NULLS LAST LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_rm_pattern_remedies
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR source_kind = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_pattern_remedies.ts:59-81'],
  },
  {
    contract_id: 'source-query:query-discoveries:v1',
    descriptor_name: 'query_discoveries',
    capability_uri: 'marsys://tool/L2/query_discoveries',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT discovery_id, ayanamsha_id, discovery_class, discovery_subsystem,
                   non_obviousness_score, consequence_score, composite_discovery_rank,
                   novelty_class, corroboration_count, corroborating_methods_array,
                   affected_domains_array, surface_reading, depth_reading, surface_depth_delta,
                   hypothesis_text, why_an_acharya_misses_it, meaningfulness_basis,
                   constituent_refs_jsonb, cross_subsystem_refs_jsonb,
                   to_char(computed_at, 'YYYY-MM-DD') AS computed_date
              FROM bodha_discoveries
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR discovery_class = NULL::text)
             ORDER BY composite_discovery_rank ASC NULLS LAST, non_obviousness_score DESC NULLS LAST
             LIMIT 0 OFFSET 0
          ), family_page AS (
            SELECT discovery_class, discovery_subsystem, hypothesis_text, COUNT(*) AS member_count,
                   COUNT(DISTINCT ayanamsha_id) AS ayanamsha_count
              FROM bodha_discoveries
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR discovery_class = NULL::text)
             GROUP BY discovery_class, discovery_subsystem, hypothesis_text
             ORDER BY MIN(composite_discovery_rank) ASC NULLS LAST LIMIT 0 OFFSET 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM bodha_discoveries
             WHERE chart_id = $1::uuid AND (NULL::text IS NULL OR ayanamsha_id = NULL::text)
               AND (NULL::text IS NULL OR discovery_class = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L2_bodha/query_discoveries.ts:104-181'],
  },
  {
    contract_id: 'source-query:query-quality-scorecard:v1',
    descriptor_name: 'query_quality_scorecard',
    capability_uri: 'marsys://tool/L2/query_quality_scorecard',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH scorecard_probe AS (
            SELECT scorecard_id, chart_id, build_id, msr_signal_count, cdlm_cell_count,
                   cgm_node_count, cgm_edge_count, two_pass_verified_pct,
                   documented_approximation_pct, msr_citation_ref_coverage_pct,
                   trap1_authority_inversion_count, trap2_narration_leak_count,
                   unresolved_constituent_facts_count, scored_at
              FROM synthesis_quality_scorecard WHERE chart_id = $1::uuid
             ORDER BY scored_at DESC LIMIT 0
          ), defect001_probe AS (
            WITH refs AS (
              SELECT unnest(m.constituent_facts_array) AS fact_id
                FROM bodha_msr_signals m
               WHERE m.chart_id = $1::uuid AND m.constituent_facts_array IS NOT NULL
                 AND array_length(m.constituent_facts_array, 1) > 0
            ) SELECT count(*)::text AS total_refs,
                     count(*) FILTER (WHERE cf.fact_id IS NULL)::text AS orphan_refs
                FROM refs LEFT JOIN chart_facts cf ON cf.chart_id = $1::uuid AND cf.fact_id = refs.fact_id
          ) SELECT scorecard_probe.*, defect001_probe.total_refs, defect001_probe.orphan_refs
              FROM scorecard_probe CROSS JOIN defect001_probe`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L2_bodha/query_quality_scorecard.ts:78-97',
      'platform/src/lib/retrieval/provenance/freshness_notes.ts:73-107',
    ],
  },
  {
    contract_id: 'source-query:query-active-dashas:v1',
    descriptor_name: 'query_active_dashas',
    capability_uri: 'marsys://tool/L3/query_active_dashas',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH systems_present AS (
            SELECT DISTINCT system_id FROM chart_dashas
             WHERE chart_id = $1::uuid AND ayanamsha_id = 'lahiri_chitrapaksha'
             ORDER BY system_id LIMIT 0
          ), active_chain AS (
            SELECT system_id, level_n, lord_graha, lord_sign,
                   to_char(start_date, 'YYYY-MM-DD') AS start_date,
                   to_char(end_date, 'YYYY-MM-DD') AS end_date, start_iso, end_iso
              FROM chart_dashas
             WHERE chart_id = $1::uuid AND ayanamsha_id = 'lahiri_chitrapaksha'
               AND start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE AND level_n <= 3
             ORDER BY system_id, level_n LIMIT 0
          ) SELECT 1 FROM systems_present CROSS JOIN active_chain`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_active_dashas.ts:101-126'],
  },
  {
    contract_id: 'source-query:query-kala-paddhati-profile:v1',
    descriptor_name: 'query_kala_paddhati_profile',
    capability_uri: 'marsys://tool/L3/query_kala_paddhati_profile',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `SELECT factor_family, convention_id, school_tag, constraint_role,
                 convention_status, provenance, corpus_gap_ref,
                 native_confirmed, awaiting_native_confirmation, version,
                 confirmation_provenance, arbitration_role, precedence
            FROM kala_paddhati_profile
           WHERE chart_id = $1::uuid
             AND (NULL::text IS NULL OR factor_family = NULL::text)
             AND (NULL::text IS NULL OR version = NULL::text)
           ORDER BY version ASC, factor_family, convention_id
           LIMIT 0`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_kala_paddhati_profile.ts:121-143'],
  },
  {
    contract_id: 'source-query:query-life-arc:v1',
    descriptor_name: 'query_life_arc',
    capability_uri: 'marsys://tool/L3/query_life_arc',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH leveled AS (
            SELECT id, parva_index, dasha_planet, dominant_signal_class, start_year, end_year,
                   parva_quality, theme_keywords, high_convergence_count, avg_effective_score,
                   narrative, source_citation, computed_at,
                   CASE WHEN source_citation ~ ':AD=' THEN 'AD'
                        WHEN source_citation ~ ':PD=' THEN 'PD' ELSE 'MD' END AS parva_level
              FROM kala_jivana_parva WHERE chart_id = $1::uuid
          ), deduped AS (
            SELECT DISTINCT ON (start_year, end_year, dasha_planet, parva_level)
                   id, parva_index, dasha_planet, dominant_signal_class, start_year, end_year,
                   parva_quality, theme_keywords, high_convergence_count, avg_effective_score,
                   narrative, source_citation, computed_at
              FROM leveled
             ORDER BY start_year, end_year, dasha_planet, parva_level, parva_index DESC
          ) SELECT id, parva_index, dasha_planet, dominant_signal_class, start_year, end_year,
                   parva_quality, theme_keywords, high_convergence_count, avg_effective_score,
                   narrative, source_citation, computed_at
              FROM deduped ORDER BY parva_index LIMIT 0 OFFSET 0`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts:119-169'],
  },
  {
    contract_id: 'source-query:query-kota-chakra:v1',
    descriptor_name: 'query_kota_chakra',
    capability_uri: 'marsys://tool/L3/query_kota_chakra',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT graha, nakshatra_name, count_from_janma, kota_ring, is_natural_malefic,
                   posture, severity, to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end, start_truncated, end_truncated,
                   janma_nakshatra_fact_id, ring_table_citation, uncited_extension,
                   (window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE) AS is_current
              FROM kala_kota_chakra
             WHERE chart_id = $1::uuid
             ORDER BY graha, window_start LIMIT 0
          ), current_page AS (
            SELECT graha FROM kala_kota_chakra
             WHERE chart_id = $1::uuid AND window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE
             ORDER BY graha, window_start LIMIT 0
          ) SELECT 1 FROM handler_page CROSS JOIN current_page`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_kota_chakra.ts:86-115'],
  },
  {
    contract_id: 'source-query:query-moorti-nirnaya:v1',
    descriptor_name: 'query_moorti_nirnaya',
    capability_uri: 'marsys://tool/L3/query_moorti_nirnaya',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT graha, target_sign_idx, target_sign_name,
                   to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end,
                   start_truncated, end_truncated, moorti_computed,
                   moon_nakshatra_idx_at_ingress, moon_nakshatra_name_at_ingress,
                   janma_nakshatra_idx, janma_nakshatra_fact_id, nakshatra_offset,
                   moorti_name, quality_tier, phala_brief, moorti_classical_citation,
                   (window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE) AS is_current
              FROM kala_moorti_nirnaya WHERE chart_id = $1::uuid
             ORDER BY graha, window_start LIMIT 0
          ), current_page AS (
            SELECT graha FROM kala_moorti_nirnaya
             WHERE chart_id = $1::uuid AND window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE
             ORDER BY graha, window_start LIMIT 0
          ) SELECT 1 FROM handler_page CROSS JOIN current_page`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_moorti_nirnaya.ts:91-119'],
  },
  {
    contract_id: 'source-query:query-obstruction-periods:v1',
    descriptor_name: 'query_obstruction_periods',
    capability_uri: 'marsys://tool/L3/query_obstruction_periods',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT id, convergence_id, signal_id, obstruction_type, severity, severity_score,
                   override_score, obstruction_detail, source_citation
              FROM kala_obstruction
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR obstruction_type = NULL::text)
               AND (NULL::text IS NULL OR severity = NULL::text)
             ORDER BY severity_score DESC NULLS LAST LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_obstruction
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR obstruction_type = NULL::text)
               AND (NULL::text IS NULL OR severity = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_obstruction_periods.ts:74-94'],
  },
  {
    contract_id: 'source-query:query-vedha-gochara:v1',
    descriptor_name: 'query_vedha_gochara',
    capability_uri: 'marsys://tool/L3/query_vedha_gochara',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT vedha_kind, graha,
                   to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end,
                   start_truncated, end_truncated, janma_reference_fact_id,
                   classical_citation, uncited_extension, grid_basis, grid_school_tag, detail,
                   (window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE) AS is_current
              FROM kala_vedha_gochara
             WHERE chart_id = $1::uuid
             ORDER BY vedha_kind, graha, window_start LIMIT 0
          ), current_page AS (
            SELECT vedha_kind FROM kala_vedha_gochara
             WHERE chart_id = $1::uuid AND window_start <= CURRENT_DATE AND window_end >= CURRENT_DATE
             ORDER BY vedha_kind, graha, window_start LIMIT 0
          ) SELECT 1 FROM handler_page CROSS JOIN current_page`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts:111-152'],
  },
  {
    contract_id: 'source-query:query-sudarshana-varsha:v1',
    descriptor_name: 'query_sudarshana_varsha',
    capability_uri: 'marsys://tool/L3/query_sudarshana_varsha',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT varsha_year, to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end,
                   jl_active_sign_name, cl_active_sign_name, sl_active_sign_name,
                   tri_lagna_convergence, lagna_fact_id, moon_fact_id, sun_fact_id,
                   (window_start <= CURRENT_DATE AND window_end > CURRENT_DATE) AS is_current
              FROM kala_sudarshana_varsha
             WHERE chart_id = $1::uuid AND varsha_year >= 1 AND varsha_year <= 120
             ORDER BY varsha_year LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_sudarshana_varsha
             WHERE chart_id = $1::uuid AND varsha_year >= 1 AND varsha_year <= 120
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_sudarshana_varsha.ts:66-118'],
  },
  {
    contract_id: 'source-query:query-tithi-pravesha:v1',
    descriptor_name: 'query_tithi_pravesha',
    capability_uri: 'marsys://tool/L3/query_tithi_pravesha',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT pravesha_year,
                   to_char(window_start, 'YYYY-MM-DD"T"HH24:MI:SS') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD"T"HH24:MI:SS') AS window_end,
                   start_converged, end_converged, pravesha_lagna_sign_idx,
                   pravesha_lagna_sign_name, pravesha_lagna_degree, graha_positions_jsonb,
                   natal_moon_longitude_deg, moon_fact_id, ephemeris_audit_jsonb,
                   verification_pass_status, classical_source_citation,
                   (window_start <= CURRENT_TIMESTAMP AND window_end > CURRENT_TIMESTAMP) AS is_current
              FROM kala_tithi_pravesha
             WHERE chart_id = $1::uuid AND pravesha_year >= 1 AND pravesha_year <= 120
             ORDER BY pravesha_year LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_tithi_pravesha
             WHERE chart_id = $1::uuid AND pravesha_year >= 1 AND pravesha_year <= 120
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts:65-120'],
  },
  {
    contract_id: 'source-query:query-convergence-windows:v1',
    descriptor_name: 'query_convergence_windows',
    capability_uri: 'marsys://tool/L3/query_convergence_windows',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT convergence_id, signal_id,
                   to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end,
                   to_char(peak_date, 'YYYY-MM-DD') AS peak_date, mode, convergence_score,
                   orb_strength, rarity_years, confidence_score, confidence_label,
                   independent_current_count, is_off_dasha_discovery, horizon_tier, domain,
                   constituent_factors, source_citation
              FROM kala_convergence
             WHERE chart_id = $1::uuid
               AND (NULL::date IS NULL OR window_end >= NULL::date)
               AND (NULL::date IS NULL OR window_start <= NULL::date)
               AND (0::numeric <= 0 OR convergence_score >= 0::numeric)
               AND (NULL::text IS NULL OR domain = NULL::text)
             ORDER BY convergence_score DESC NULLS LAST LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_convergence
             WHERE chart_id = $1::uuid
               AND (NULL::date IS NULL OR window_end >= NULL::date)
               AND (NULL::date IS NULL OR window_start <= NULL::date)
               AND (0::numeric <= 0 OR convergence_score >= 0::numeric)
               AND (NULL::text IS NULL OR domain = NULL::text)
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts:82-176'],
  },
  {
    contract_id: 'source-query:query-activation-waveform:v1',
    descriptor_name: 'query_activation_waveform',
    capability_uri: 'marsys://tool/L3/query_activation_waveform',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH filtered AS (
            SELECT taranga_id, month, scope_kind, scope_id, activation, components, formula_version
              FROM kala_taranga
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR scope_kind = NULL::text)
               AND (NULL::text IS NULL OR scope_id = NULL::text)
               AND (NULL::date IS NULL OR month >= NULL::date)
               AND (NULL::date IS NULL OR month <= NULL::date)
          ), drill_page AS (
            SELECT * FROM filtered ORDER BY month LIMIT 0
          ), summary AS (
            SELECT MIN(month) AS first_month, MAX(month) AS last_month,
                   COUNT(DISTINCT scope_id)::int AS distinct_scopes,
                   COUNT(DISTINCT scope_kind)::int AS distinct_scope_kinds,
                   ROUND(AVG(activation)::numeric, 4) AS avg_activation,
                   ROUND(MAX(activation)::numeric, 4) AS max_activation
              FROM filtered
          ), peaks AS (
            SELECT month, scope_kind, scope_id, activation FROM filtered
             ORDER BY activation DESC NULLS LAST, month LIMIT 0
          ) SELECT 1 FROM drill_page CROSS JOIN summary CROSS JOIN peaks`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts:61-147'],
  },
  {
    contract_id: 'source-query:query-dasha-dossier:v1',
    descriptor_name: 'query_dasha_dossier',
    capability_uri: 'marsys://tool/L3/query_dasha_dossier',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT avadhi_id, system_id, level_n, lord_graha,
                   to_char(period_start, 'YYYY-MM-DD') AS period_start,
                   to_char(period_end, 'YYYY-MM-DD') AS period_end,
                   dossier, quality, citations, formula_version
              FROM kala_avadhi
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR system_id = NULL::text)
               AND (NULL::int IS NULL OR level_n = NULL::int)
               AND (NULL::text IS NULL OR lord_graha = NULL::text)
               AND (NULL::date IS NULL OR period_end >= NULL::date)
               AND (NULL::date IS NULL OR period_start <= NULL::date)
               AND (NULL::date IS NULL OR (period_start <= NULL::date AND period_end >= NULL::date))
             ORDER BY period_start, level_n LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_avadhi
             WHERE chart_id = $1::uuid
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts:60-119'],
  },
  {
    contract_id: 'source-query:query-projections:v1',
    descriptor_name: 'query_projections',
    capability_uri: 'marsys://tool/L3/query_projections',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH filtered AS (
            SELECT id, projection_rank, domain, probability_tier, effective_score, peak_date,
                   window_start, window_end, narrative, falsifiability, convergence_id, signal_id,
                   source_chain, outcome_recorded, outcome_notes, source_citation, computed_at
              FROM kala_bhavishya
             WHERE chart_id = $1::uuid
               AND (NULL::date IS NULL OR peak_date <= NULL::date)
               AND (NULL::text IS NULL OR probability_tier = NULL::text)
               AND (NULL::text IS NULL OR domain = NULL::text)
          ), handler_page AS (
            SELECT id, projection_rank, domain, probability_tier, effective_score,
                   to_char(peak_date, 'YYYY-MM-DD') AS peak_date,
                   to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end, narrative, falsifiability,
                   convergence_id, signal_id, source_chain, outcome_recorded, outcome_notes,
                   source_citation, computed_at
              FROM filtered ORDER BY probability_tier, projection_rank LIMIT 0
          ), families AS (
            SELECT window_start, window_end, domain, COUNT(*) AS member_count
              FROM filtered GROUP BY window_start, window_end, domain LIMIT 0
          ), source_classification AS (
            SELECT COUNT(*)::int AS total FROM kala_bhavishya WHERE chart_id = $1::uuid
          ), build_observation AS (
            SELECT br.id::text AS build_id, br.state AS build_state, bra.state AS asset_state
              FROM build_run_assets bra JOIN build_runs br ON br.id = bra.run_id
             WHERE br.chart_id = $1::uuid AND bra.asset_id = 'ka_bhavishya_lekha'
             ORDER BY COALESCE(bra.ended_at, br.ended_at, br.created_at) DESC LIMIT 0
          ) SELECT 1 FROM handler_page CROSS JOIN families CROSS JOIN source_classification CROSS JOIN build_observation`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts:74-137 | platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts:209-371'],
  },
  {
    contract_id: 'source-query:query-temporal-view:v1',
    descriptor_name: 'query_temporal_view',
    capability_uri: 'marsys://tool/L3/query_temporal_view',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT id, convergence_id, signal_id, effective_score, net_label,
                   to_char(peak_date, 'YYYY-MM-DD') AS peak_date,
                   to_char(window_start, 'YYYY-MM-DD') AS window_start,
                   to_char(window_end, 'YYYY-MM-DD') AS window_end,
                   obstruction_summary, narrative, source_citation
              FROM kala_darshana
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR net_label = NULL::text)
               AND (NULL::numeric IS NULL OR effective_score >= NULL::numeric)
               AND (NULL::date IS NULL OR window_end >= NULL::date)
               AND (NULL::date IS NULL OR window_start <= NULL::date)
               AND (NULL::date IS NULL OR (window_start <= NULL::date AND window_end >= NULL::date))
             ORDER BY effective_score DESC NULLS LAST, peak_date LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM kala_darshana WHERE chart_id = $1::uuid
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts:59-112'],
  },
  {
    contract_id: 'source-query:query-temporal-activation:v1',
    descriptor_name: 'query_temporal_activation',
    capability_uri: 'marsys://tool/L3/query_temporal_activation',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH activations AS (
            SELECT id, signal_id, ayanamsha_id, signature_class, activation_start, activation_end,
                   activation_peak_date, orb_strength, convergence_score,
                   dasha_activation_proximity_score, active_dasha_periods_jsonb,
                   activation_predicted_dates_jsonb, source_citation
              FROM kala_activation
             WHERE chart_id = $1::uuid AND ayanamsha_id = NULLIF(NULL::text, '')
             ORDER BY dasha_activation_proximity_score DESC NULLS LAST,
                      orb_strength DESC NULLS LAST, activation_start ASC, id ASC LIMIT 0
          ), activation_domains AS (
            SELECT ms.signal_id, ms.domains_affected_array FROM bodha_msr_signals ms
             WHERE ms.chart_id = $1::uuid LIMIT 0
          ), predicates AS (
            SELECT id, signal_id, ayanamsha_id, signature_class, dasha_eligibility_rule_jsonb,
                   transit_trigger_jsonb, strength_affliction_hook_jsonb,
                   derivation_ledger_jsonb, template_version
              FROM kala_activation_predicates
             WHERE chart_id = $1::uuid AND ayanamsha_id = NULLIF(NULL::text, '') LIMIT 0
          ), activation_empty_classification AS (
            SELECT COUNT(*)::int AS total, COUNT(activation_start)::int AS dated
              FROM kala_activation WHERE chart_id = $1::uuid
          ), forward_windows AS (
            SELECT id, signal_id, domain, probability_tier, effective_score, window_start,
                   window_end, peak_date, narrative, source_citation
              FROM kala_bhavishya WHERE chart_id = $1::uuid ORDER BY window_start LIMIT 0
          ), forward_source_classification AS (
            SELECT COUNT(*)::int AS total FROM kala_bhavishya WHERE chart_id = $1::uuid
          ), build_observation AS (
            SELECT br.id::text FROM build_run_assets bra JOIN build_runs br ON br.id = bra.run_id
             WHERE br.chart_id = $1::uuid AND bra.asset_id = 'ka_bhavishya_lekha' LIMIT 0
          ) SELECT 1 FROM activations CROSS JOIN activation_domains CROSS JOIN predicates
             CROSS JOIN activation_empty_classification CROSS JOIN forward_windows
             CROSS JOIN forward_source_classification CROSS JOIN build_observation`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:176-620'],
  },
  {
    contract_id: 'source-query:query-insights:v1',
    descriptor_name: 'query_insights',
    capability_uri: 'marsys://tool/L5/query_insights',
    scope: 'chart', parameter_binding: 'chart_with_active_build_context', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT insight_id, insight_type, domain, horizon, question_lens, statement,
                   rank_consequence, confidence_band, n_support, leakage_status, evidence_grade,
                   freshness_lel_version, last_calibrated_at, provenance_chain, is_negative_knowledge,
                   surface_formula_version, updated_at
              FROM mimamsa_insight_units
             WHERE chart_id = $1::uuid
               AND (NULL::text IS NULL OR insight_type = NULL::text)
               AND (NULL::text IS NULL OR domain = NULL::text)
               AND (0::numeric <= 0 OR rank_consequence >= 0::numeric)
               AND (true OR is_negative_knowledge = false)
             ORDER BY rank_consequence DESC NULLS LAST LIMIT 0
          ), filtered_count AS (
            SELECT COUNT(*)::text AS total FROM mimamsa_insight_units WHERE chart_id = $1::uuid
          ), chart_count AS (
            SELECT COUNT(*)::text AS total FROM mimamsa_insight_units WHERE chart_id = $1::uuid
          ), calibration_summary AS (
            SELECT COUNT(*)::int AS total_matches,
                   COUNT(*) FILTER (WHERE composite_verdict = 'CONFIRMED') AS confirmed,
                   COUNT(*) FILTER (WHERE composite_verdict = 'PARTIAL') AS partial,
                   COUNT(*) FILTER (WHERE composite_verdict = 'REFUTED') AS refuted,
                   COUNT(*) FILTER (WHERE composite_verdict = 'UNRESOLVED') AS unresolved,
                   AVG(composite_score)::numeric(4,3) AS mean_composite_score
              FROM mimamsa_calibration WHERE chart_id = $1::uuid
          ) SELECT 1 FROM handler_page CROSS JOIN filtered_count CROSS JOIN chart_count CROSS JOIN calibration_summary`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts:198-257'],
  },
  {
    contract_id: 'source-query:query-signal-families:v1',
    descriptor_name: 'query_signal_families',
    capability_uri: 'marsys://tool/L5/query_signal_families',
    scope: 'global', parameter_binding: 'global', empty_semantics: 'query_success_is_available',
    sql: `WITH handler_page AS (
            SELECT family_id, display_name, layman_name, family_class, evidence_tier,
                   soundness_basis, binding_kind, default_state, prior_weight,
                   calibration_status, citation_refs, binding_spec, apply_point, is_active, created_at
              FROM mimamsa_signal_families
             WHERE (NULL::text IS NULL OR display_name = NULL::text)
               AND (NULL::text IS NULL OR family_class = NULL::text)
               AND (true OR family_class <> 'negative_control')
             ORDER BY family_class, display_name LIMIT 0
          ), handler_count AS (
            SELECT COUNT(*)::text AS total FROM mimamsa_signal_families
          ) SELECT handler_page.*, handler_count.total FROM handler_page CROSS JOIN handler_count`,
    source_refs: ['platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_signal_families.ts:72-143'],
  },
]

const CONTRACT_BY_ID = new Map(CONTRACTS.map((contract) => [contract.contract_id, contract]))
const CONTRACT_BY_DESCRIPTOR = new Map(CONTRACTS.map((contract) => [contract.descriptor_name, contract]))

export function getSourceQueryAvailabilityContract(
  contractId: string,
): SourceQueryAvailabilityContract | undefined {
  return CONTRACT_BY_ID.get(contractId)
}

/**
 * Materialize a source-owned requirement for an explicit non-primary binding.
 * The contract's exact URI and fingerprint stay centralized with its SQL, so
 * an editorial alias cannot drift from the reviewed handler relation.
 */
export function sourceQueryAvailabilityRequirement(
  contractId: string,
): SourceQueryAvailabilityRequirement | undefined {
  const contract = getSourceQueryAvailabilityContract(contractId)
  if (!contract) return undefined
  return {
    kind: 'source_query',
    contract_id: contract.contract_id,
    capability_uri: contract.capability_uri,
    contract_sha256: sourceQueryAvailabilityContractFingerprint(contract),
    scope: contract.scope,
    source_ref: contract.source_refs.join(' | '),
  }
}

export function getDescriptorSourceQueryAvailabilityReview(
  descriptorName: string,
): DescriptorSourceQueryAvailabilityReview | undefined {
  const contract = CONTRACT_BY_DESCRIPTOR.get(descriptorName)
  if (!contract) return undefined
  return {
    requirement: {
      kind: 'source_query',
      contract_id: contract.contract_id,
      capability_uri: contract.capability_uri,
      contract_sha256: sourceQueryAvailabilityContractFingerprint(contract),
      scope: contract.scope,
      source_ref: contract.source_refs.join(' | '),
    },
  }
}

export function sourceQueryAvailabilityContractMatches(
  requirement: SourceQueryAvailabilityRequirement,
): boolean {
  const contract = getSourceQueryAvailabilityContract(requirement.contract_id)
  return Boolean(contract
    && requirement.contract_sha256 === sourceQueryAvailabilityContractFingerprint(contract)
    && requirement.capability_uri === contract.capability_uri
    && requirement.scope === contract.scope
    && requirement.source_ref === contract.source_refs.join(' | ')
    && sourceQueryParameterBindingMatchesScope(contract.scope, contract.parameter_binding))
}

export function getSourceQueryAvailabilityReviews(): readonly DescriptorSourceQueryAvailabilityReview[] {
  return CONTRACTS.map((contract) => getDescriptorSourceQueryAvailabilityReview(contract.descriptor_name)!)
}
