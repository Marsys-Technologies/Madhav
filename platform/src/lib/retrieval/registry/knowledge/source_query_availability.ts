import type { SourceQueryAvailabilityRequirement } from './types'
import { stableFingerprint } from './stable'

export type SourceQueryParameterBinding =
  | 'global'
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
  return (scope === 'global' && parameterBinding === 'global')
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
            FROM bg_sky_events
           WHERE event_datetime_utc >= NULL::timestamptz
             AND event_datetime_utc < NULL::timestamptz
           ORDER BY event_datetime_utc, event_type, primary_body
           LIMIT 0`,
    source_refs: [
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts:98-121',
      'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_sky_calendar.ts:141-156',
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
